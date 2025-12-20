"""Use case to compute asset category breakdown in a target currency."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable

from sqlalchemy import text

from src.application.ports.database import DatabaseEnginePort
from src.application.use_cases.get_net_worth_summary import DEFAULT_ASSET_TYPES
from src.infrastructure.logging.logger import get_app_logger


@dataclass(frozen=True)
class AssetCategoryAmount:
    """Amount aggregated for a given asset category."""

    category: str
    amount: Decimal
    parent_category: str | None = None
    parent_category: str | None = None


@dataclass(frozen=True)
class AssetCategoryBreakdown:
    """Breakdown of asset amounts by category."""

    currency_code: str
    categories: list[AssetCategoryAmount]


class GetAssetCategoryBreakdownUseCase:
    """Compute asset category breakdown from the GnuCash database."""

    def __init__(
        self,
        db_port: DatabaseEnginePort,
        logger=None,
        asset_types: Iterable[str] | None = None,
        actif_root_name: str = "Actif",
    ) -> None:
        """Initialize the use case.

        Args:
            db_port: Port providing access to the GnuCash engine.
            logger: Optional logger compatible with logging.Logger-like API.
            asset_types: Optional iterable of account types treated as assets.
            actif_root_name: Name of the root account containing asset buckets.
        """
        self._db_port = db_port
        self._logger = logger or get_app_logger()
        self._asset_types = tuple(asset_types or DEFAULT_ASSET_TYPES)
        self._actif_root_name = actif_root_name

    def execute(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        target_currency: str = "EUR",
        level: int = 1,
    ) -> AssetCategoryBreakdown:
        """Return the asset breakdown in the target currency.

        Args:
            start_date: Optional lower bound for transaction post dates.
            end_date: Optional upper bound for transaction post dates.
            target_currency: Currency code to convert into.
            level: Depth level under the Actif root (1 or 2).

        Returns:
            AssetCategoryBreakdown: Aggregated asset totals by category.
        """
        engine = self._db_port.get_gnucash_engine()
        with engine.connect() as conn:
            currency_guid = self._fetch_currency_guid(conn, target_currency)
            rows = conn.execute(
                self._build_query(start_date, end_date),
                self._build_params(start_date, end_date),
            ).all()
            prices = self._fetch_latest_prices(
                conn,
                currency_guid,
                end_date,
            )

        totals: dict[tuple[str | None, str], Decimal] = {}
        for row in rows:
            account_type = row.account_type
            if account_type not in self._asset_types:
                continue
            category = self._resolve_category(row, level)
            parent_category = (
                row.actif_category
                if level == 2
                else None
            )
            if not category:
                continue
            balance = self._coerce_decimal(row.balance)
            converted = self._convert_balance(
                balance,
                row.commodity_guid,
                row.mnemonic,
                row.namespace,
                currency_guid,
                target_currency,
                prices,
            )
            if converted is None:
                continue
            key = (parent_category, category)
            totals[key] = totals.get(key, Decimal("0")) + converted

        categories = [
            AssetCategoryAmount(
                category=category,
                amount=amount,
                parent_category=parent_category,
            )
            for (parent_category, category), amount in sorted(totals.items())
        ]

        return AssetCategoryBreakdown(
            currency_code=target_currency,
            categories=categories,
        )

    @staticmethod
    def _build_query(
        start_date: date | None,
        end_date: date | None,
    ):
        base_sql = """
        WITH RECURSIVE account_tree AS (
            SELECT child.guid AS guid,
                   child.parent_guid AS parent_guid,
                   child.name AS top_child_name,
                   NULL::TEXT AS second_child_name
            FROM accounts root
            JOIN accounts child ON child.parent_guid = root.guid
            WHERE root.name = :actif_root
            UNION ALL
            SELECT a.guid,
                   a.parent_guid,
                   at.top_child_name,
                   CASE
                       WHEN at.second_child_name IS NULL THEN a.name
                       ELSE at.second_child_name
                   END AS second_child_name
            FROM account_tree at
            JOIN accounts a ON a.parent_guid = at.guid
        )
        SELECT a.account_type AS account_type,
               a.commodity_guid AS commodity_guid,
               c.mnemonic AS mnemonic,
               c.namespace AS namespace,
               at.top_child_name AS actif_category,
               at.second_child_name AS actif_subcategory,
               SUM(
                   CASE
                       WHEN c.namespace = 'CURRENCY'
                           THEN CAST(s.value_num AS NUMERIC) / NULLIF(s.value_denom, 0)
                       ELSE CAST(s.quantity_num AS NUMERIC) / NULLIF(s.quantity_denom, 0)
                   END
               ) AS balance
        FROM accounts a
        JOIN account_tree at ON at.guid = a.guid
        JOIN commodities c ON c.guid = a.commodity_guid
        JOIN splits s ON s.account_guid = a.guid
        JOIN transactions t ON t.guid = s.tx_guid
        WHERE at.top_child_name IS NOT NULL
        """
        if start_date:
            base_sql += " AND t.post_date >= :start_date"
        if end_date:
            base_sql += " AND t.post_date <= :end_date"
        base_sql += (
            " GROUP BY a.account_type, a.commodity_guid, c.mnemonic, "
            "c.namespace, at.top_child_name, at.second_child_name"
        )
        return text(base_sql)

    def _build_params(
        self,
        start_date: date | None,
        end_date: date | None,
    ) -> dict[str, date | str]:
        params: dict[str, date | str] = {}
        params["actif_root"] = self._actif_root_name
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return params

    @staticmethod
    def _coerce_decimal(value) -> Decimal:
        if value is None:
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    def _fetch_currency_guid(self, conn, currency: str) -> str:
        query = text(
            """
            SELECT guid
            FROM commodities
            WHERE mnemonic = :currency AND namespace = 'CURRENCY'
            LIMIT 1
            """
        )
        result = conn.execute(query, {"currency": currency}).first()
        if not result:
            raise RuntimeError(f"Missing currency in commodities: {currency}")
        return result.guid

    def _fetch_latest_prices(
        self,
        conn,
        currency_guid: str,
        end_date: date | None,
    ) -> dict[str, Decimal]:
        query = text(
            """
            SELECT commodity_guid, value_num, value_denom, date
            FROM prices
            WHERE currency_guid = :currency_guid
            """
        )
        params = {"currency_guid": currency_guid}
        if end_date:
            query = text(query.text + " AND date <= :end_date")
            params["end_date"] = end_date
        query = text(query.text + " ORDER BY commodity_guid, date DESC")
        rows = conn.execute(query, params).all()

        rates: dict[str, Decimal] = {}
        for row in rows:
            if row.commodity_guid in rates:
                continue
            denom = self._coerce_decimal(row.value_denom)
            if denom == 0:
                self._logger.warning(
                    f"Skipping FX rate with zero denominator for {row.commodity_guid}"
                )
                continue
            rates[row.commodity_guid] = self._coerce_decimal(row.value_num) / denom
        return rates

    def _convert_balance(
        self,
        balance: Decimal,
        commodity_guid: str,
        mnemonic: str,
        namespace: str,
        target_guid: str,
        target_currency: str,
        prices: dict[str, Decimal],
    ) -> Decimal | None:
        if not commodity_guid or not mnemonic:
            self._logger.warning("Skipping account with missing commodity info")
            return None
        if namespace.upper() == "TEMPLATE" or mnemonic.lower() == "template":
            return None
        if namespace == "CURRENCY" and (
            commodity_guid == target_guid or mnemonic == target_currency
        ):
            return balance
        rate = prices.get(commodity_guid)
        if rate is None:
            self._logger.warning(
                f"Missing FX rate for {mnemonic} to {target_currency}"
            )
            return None
        return balance * rate

    @staticmethod
    def _resolve_category(row, level: int) -> str | None:
        if level == 1:
            return row.actif_category
        if level == 2:
            return row.actif_subcategory
        return row.actif_category

__all__ = [
    "GetAssetCategoryBreakdownUseCase",
    "AssetCategoryBreakdown",
    "AssetCategoryAmount",
]
