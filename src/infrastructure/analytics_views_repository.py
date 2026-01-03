"""Analytics-backed repository using precomputed views."""

from datetime import date

from sqlalchemy import text

from src.application.ports.analytics_repository import AnalyticsRepositoryPort
from src.application.ports.database import DatabaseEnginePort
from src.domain.models import (
    AccountBalanceRow,
    AssetCategoryBalanceRow,
    NetWorthBalanceRow,
    PriceRow,
)
from src.utils.decimal_utils import coerce_decimal


class AnalyticsViewsRepository(AnalyticsRepositoryPort):
    """Repository that reads analytics views for dashboard computations."""

    def __init__(self, db_port: DatabaseEnginePort) -> None:
        """Initialize the repository.

        Args:
            db_port: Port providing access to the analytics engine.
        """
        self._db_port = db_port

    def fetch_currency_guid(self, currency: str) -> str:
        query = text(
            """
            SELECT guid
            FROM vw_currency_lookup
            WHERE mnemonic = :currency AND namespace = 'CURRENCY'
            LIMIT 1
            """
        )
        engine = self._db_port.get_analytics_engine()
        with engine.connect() as conn:
            result = conn.execute(query, {"currency": currency}).first()
        if not result:
            raise RuntimeError(f"Missing currency in vw_currency_lookup: {currency}")
        return result.guid

    def fetch_net_worth_balances(
        self,
        start_date: date | None,
        end_date: date | None,
    ) -> list[NetWorthBalanceRow]:
        query = text(
            """
            SELECT account_type,
                   commodity_guid,
                   mnemonic,
                   namespace,
                   balance
            FROM vw_net_worth_balances
            WHERE 1=1
            """
        )
        params = self._build_date_params(start_date, end_date)
        if start_date:
            query = text(query.text + " AND post_date >= :start_date")
        if end_date:
            query = text(query.text + " AND post_date <= :end_date")
        engine = self._db_port.get_analytics_engine()
        with engine.connect() as conn:
            rows = conn.execute(query, params).all()
        balances = [
            NetWorthBalanceRow(
                account_type=row.account_type,
                commodity_guid=row.commodity_guid,
                mnemonic=row.mnemonic,
                namespace=row.namespace,
                balance=coerce_decimal(row.balance),
            )
            for row in rows
        ]
        return sorted(
            balances,
            key=lambda row: (
                row.account_type,
                row.commodity_guid or "",
                row.mnemonic or "",
                row.namespace or "",
            ),
        )

    def fetch_asset_category_balances(
        self,
        start_date: date | None,
        end_date: date | None,
        actif_root_name: str,
    ) -> list[AssetCategoryBalanceRow]:
        query = text(
            """
            SELECT account_type,
                   commodity_guid,
                   mnemonic,
                   namespace,
                   actif_category,
                   actif_subcategory,
                   balance
            FROM vw_asset_category_balances
            WHERE actif_root_name = :actif_root
            """
        )
        params = self._build_date_params(start_date, end_date)
        params["actif_root"] = actif_root_name
        if start_date:
            query = text(query.text + " AND post_date >= :start_date")
        if end_date:
            query = text(query.text + " AND post_date <= :end_date")
        engine = self._db_port.get_analytics_engine()
        with engine.connect() as conn:
            rows = conn.execute(query, params).all()
        balances = [
            AssetCategoryBalanceRow(
                account_type=row.account_type,
                commodity_guid=row.commodity_guid,
                mnemonic=row.mnemonic,
                namespace=row.namespace,
                actif_category=row.actif_category,
                actif_subcategory=row.actif_subcategory,
                balance=coerce_decimal(row.balance),
            )
            for row in rows
        ]
        return sorted(
            balances,
            key=lambda row: (
                row.actif_category or "",
                row.actif_subcategory or "",
                row.account_type,
                row.commodity_guid or "",
                row.mnemonic or "",
                row.namespace or "",
            ),
        )

    def fetch_account_balances(
        self,
        end_date: date | None,
    ) -> list[AccountBalanceRow]:
        query = self._build_account_balances_query(end_date)
        params = self._build_date_params(None, end_date)
        engine = self._db_port.get_analytics_engine()
        with engine.connect() as conn:
            rows = conn.execute(query, params).all()
        balances = [
            AccountBalanceRow(
                guid=row.guid,
                name=row.name,
                account_type=row.account_type,
                commodity_guid=row.commodity_guid,
                parent_guid=row.parent_guid,
                mnemonic=row.mnemonic,
                namespace=row.namespace,
                balance=coerce_decimal(row.balance),
            )
            for row in rows
        ]
        return sorted(
            balances,
            key=lambda row: (row.name.lower(), row.guid),
        )

    def fetch_latest_prices(
        self,
        currency_guid: str,
        end_date: date | None,
    ) -> list[PriceRow]:
        query = text(
            """
            SELECT commodity_guid, value_num, value_denom, date
            FROM vw_latest_prices
            WHERE currency_guid = :currency_guid
            """
        )
        params = {"currency_guid": currency_guid}
        if end_date:
            query = text(query.text + " AND date <= :end_date")
            params["end_date"] = end_date
        query = text(query.text + " ORDER BY commodity_guid, date DESC")
        engine = self._db_port.get_analytics_engine()
        with engine.connect() as conn:
            rows = conn.execute(query, params).all()
        prices = [
            PriceRow(
                commodity_guid=row.commodity_guid,
                value_num=coerce_decimal(row.value_num),
                value_denom=coerce_decimal(row.value_denom),
                date=row.date,
            )
            for row in rows
        ]
        return sorted(
            prices,
            key=lambda row: (row.commodity_guid, row.date),
            reverse=True,
        )

    @staticmethod
    def _build_date_params(
        start_date: date | None,
        end_date: date | None,
    ) -> dict[str, date]:
        params: dict[str, date] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return params

    @staticmethod
    def _build_account_balances_query(end_date: date | None):
        base_sql = """
        SELECT a.guid AS guid,
               a.name AS name,
               a.account_type AS account_type,
               a.parent_guid AS parent_guid,
               a.commodity_guid AS commodity_guid,
               c.mnemonic AS mnemonic,
               c.namespace AS namespace,
               COALESCE(
                   SUM(
                       CASE
                           WHEN s.value_num IS NULL THEN 0
                           WHEN c.namespace = 'CURRENCY'
                               THEN CAST(s.value_num AS NUMERIC) / NULLIF(s.value_denom, 0)
                           ELSE CAST(s.quantity_num AS NUMERIC) / NULLIF(s.quantity_denom, 0)
                       END
                   ),
                   0
               ) AS balance
        FROM accounts a
        JOIN commodities c ON c.guid = a.commodity_guid
        LEFT JOIN splits s ON s.account_guid = a.guid
        LEFT JOIN transactions t ON t.guid = s.tx_guid
        WHERE 1=1
        """
        if end_date:
            base_sql += " AND (t.post_date <= :end_date OR t.post_date IS NULL)"
        base_sql += (
            " GROUP BY a.guid, a.name, a.account_type, a.parent_guid, "
            "a.commodity_guid, c.mnemonic, c.namespace"
        )
        return text(base_sql)


__all__ = ["AnalyticsViewsRepository"]
