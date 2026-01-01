"""SQLAlchemy-backed repository for GnuCash reporting data."""

from datetime import date
from decimal import Decimal

from sqlalchemy import text

from src.application.ports.database import DatabaseEnginePort
from src.application.ports.gnucash_repository import (
    AssetCategoryBalanceRow,
    GnuCashRepositoryPort,
    NetWorthBalanceRow,
    PriceRow,
)


class SqlAlchemyGnuCashRepository(GnuCashRepositoryPort):
    """Repository backed by SQLAlchemy for GnuCash reporting queries."""

    def __init__(self, db_port: DatabaseEnginePort) -> None:
        """Initialize the repository.

        Args:
            db_port: Port providing access to the GnuCash engine.
        """
        self._db_port = db_port

    def fetch_currency_guid(self, currency: str) -> str:
        query = text(
            """
            SELECT guid
            FROM commodities
            WHERE mnemonic = :currency AND namespace = 'CURRENCY'
            LIMIT 1
            """
        )
        engine = self._db_port.get_gnucash_engine()
        with engine.connect() as conn:
            result = conn.execute(query, {"currency": currency}).first()
        if not result:
            raise RuntimeError(f"Missing currency in commodities: {currency}")
        return result.guid

    def fetch_net_worth_balances(
        self,
        start_date: date | None,
        end_date: date | None,
    ) -> list[NetWorthBalanceRow]:
        query = self._build_net_worth_query(start_date, end_date)
        params = self._build_date_params(start_date, end_date)
        engine = self._db_port.get_gnucash_engine()
        with engine.connect() as conn:
            rows = conn.execute(query, params).all()
        return [
            NetWorthBalanceRow(
                account_type=row.account_type,
                commodity_guid=row.commodity_guid,
                mnemonic=row.mnemonic,
                namespace=row.namespace,
                balance=self._coerce_decimal(row.balance),
            )
            for row in rows
        ]

    def fetch_asset_category_balances(
        self,
        start_date: date | None,
        end_date: date | None,
        actif_root_name: str,
    ) -> list[AssetCategoryBalanceRow]:
        query = self._build_asset_category_query(start_date, end_date)
        params = self._build_date_params(start_date, end_date)
        params["actif_root"] = actif_root_name
        engine = self._db_port.get_gnucash_engine()
        with engine.connect() as conn:
            rows = conn.execute(query, params).all()
        return [
            AssetCategoryBalanceRow(
                account_type=row.account_type,
                commodity_guid=row.commodity_guid,
                mnemonic=row.mnemonic,
                namespace=row.namespace,
                actif_category=row.actif_category,
                actif_subcategory=row.actif_subcategory,
                balance=self._coerce_decimal(row.balance),
            )
            for row in rows
        ]

    def fetch_latest_prices(
        self,
        currency_guid: str,
        end_date: date | None,
    ) -> list[PriceRow]:
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
        engine = self._db_port.get_gnucash_engine()
        with engine.connect() as conn:
            rows = conn.execute(query, params).all()
        return [
            PriceRow(
                commodity_guid=row.commodity_guid,
                value_num=self._coerce_decimal(row.value_num),
                value_denom=self._coerce_decimal(row.value_denom),
                date=row.date,
            )
            for row in rows
        ]

    @staticmethod
    def _coerce_decimal(value) -> Decimal:
        if value is None:
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

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
    def _build_net_worth_query(
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
        base_sql += (
            " GROUP BY a.account_type, a.commodity_guid, c.mnemonic, c.namespace"
        )
        return text(base_sql)

    @staticmethod
    def _build_asset_category_query(
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


__all__ = ["SqlAlchemyGnuCashRepository"]
