"""Use case to compute net worth from the GnuCash database."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable

from sqlalchemy import text

from src.application.ports.database import DatabaseEnginePort
from src.infrastructure.logging.logger import get_app_logger


DEFAULT_ASSET_TYPES = (
    "ASSET",
    "BANK",
    "CASH",
    "STOCK",
    "MUTUAL",
    "RECEIVABLE",
)
DEFAULT_LIABILITY_TYPES = (
    "LIABILITY",
    "CREDIT",
    "PAYABLE",
)


@dataclass(frozen=True)
class NetWorthSummary:
    """Summary of net worth figures.

    Attributes:
        asset_total: Sum of asset balances.
        liability_total: Sum of liability balances.
        net_worth: Assets minus liabilities.
    """

    asset_total: Decimal
    liability_total: Decimal
    net_worth: Decimal
    currency_code: str


class GetNetWorthSummaryUseCase:
    """Compute net worth from the GnuCash database."""

    def __init__(
        self,
        db_port: DatabaseEnginePort,
        logger=None,
        asset_types: Iterable[str] | None = None,
        liability_types: Iterable[str] | None = None,
    ) -> None:
        """Initialize the use case.

        Args:
            db_port: Port providing access to the GnuCash engine.
            logger: Optional logger compatible with logging.Logger-like API.
            asset_types: Optional iterable of account types treated as assets.
            liability_types: Optional iterable treated as liabilities.
        """
        self._db_port = db_port
        self._logger = logger or get_app_logger()
        self._asset_types = tuple(asset_types or DEFAULT_ASSET_TYPES)
        self._liability_types = tuple(
            liability_types or DEFAULT_LIABILITY_TYPES
        )

    def execute(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        target_currency: str = "EUR",
    ) -> NetWorthSummary:
        """Return the net worth summary.

        Args:
            start_date: Optional lower bound for transaction post dates.
            end_date: Optional upper bound for transaction post dates.

        Returns:
            NetWorthSummary: Computed asset, liability, and net worth totals.
        """
        engine = self._db_port.get_gnucash_engine()
        with engine.connect() as conn:
            currency_guid = self._fetch_currency_guid(conn, target_currency)
            balances = conn.execute(
                self._build_query(start_date, end_date),
                self._build_params(start_date, end_date),
            ).all()
            prices = self._fetch_latest_prices(
                conn,
                currency_guid,
                end_date,
            )

        asset_total = Decimal("0")
        liability_total = Decimal("0")

        for row in balances:
            account_type = row.account_type
            if account_type not in self._asset_types and account_type not in self._liability_types:
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
            if account_type in self._asset_types:
                asset_total += converted
            else:
                liability_total += abs(converted)

        net_worth = asset_total - liability_total

        self._logger.info(
            f"Net worth computed: assets={asset_total}, "
            f"liabilities={liability_total}, currency={target_currency}"
        )

        return NetWorthSummary(
            asset_total=asset_total,
            liability_total=liability_total,
            net_worth=net_worth,
            currency_code=target_currency,
        )

    @staticmethod
    def _coerce_decimal(value) -> Decimal:
        """Normalize numeric values to Decimal.

        Args:
            value: Raw numeric value from SQL.

        Returns:
            Decimal: Normalized numeric value.
        """
        if value is None:
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    @staticmethod
    def _build_query(
        start_date: date | None,
        end_date: date | None,
    ):
        base_sql = """
        SELECT a.account_type AS account_type,
               a.commodity_guid AS commodity_guid,
               c.mnemonic AS mnemonic,
               c.namespace AS namespace,
               SUM(
                   CASE
                       WHEN c.namespace = 'CURRENCY'
                           THEN CAST(s.value_num AS NUMERIC) / NULLIF(s.value_denom, 0)
                       ELSE CAST(s.quantity_num AS NUMERIC) / NULLIF(s.quantity_denom, 0)
                   END
               ) AS balance
        FROM accounts a
        JOIN commodities c ON c.guid = a.commodity_guid
        JOIN splits s ON s.account_guid = a.guid
        JOIN transactions t ON t.guid = s.tx_guid
        WHERE 1=1
        """
        if start_date:
            base_sql += " AND t.post_date >= :start_date"
        if end_date:
            base_sql += " AND t.post_date <= :end_date"
        base_sql += " GROUP BY a.account_type, a.commodity_guid, c.mnemonic, c.namespace"
        return text(base_sql)

    @staticmethod
    def _build_params(
        start_date: date | None,
        end_date: date | None,
    ) -> dict[str, date]:
        params: dict[str, date] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return params

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
            query = text(
                query.text + " AND date <= :end_date"
            )
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
                    f"Skipping FX rate with zero denominator "
                    f"for {row.commodity_guid}"
                )
                continue
            rates[row.commodity_guid] = (
                self._coerce_decimal(row.value_num) / denom
                )
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
            self._logger.warning(
                "Skipping account with missing commodity info"
                )
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


__all__ = ["GetNetWorthSummaryUseCase", "NetWorthSummary"]
