"""Analytics-backed repository for GnuCash reporting data."""

from datetime import date

from sqlalchemy import text

from src.application.ports.database import DatabaseEnginePort
from src.application.ports.gnucash_repository import (
    AssetCategoryBalanceRow,
    GnuCashRepositoryPort,
    NetWorthBalanceRow,
    PriceRow,
)
from src.domain.models import AccountBalanceRow, CashflowRow
from src.utils.decimal_utils import coerce_decimal


class AnalyticsGnuCashRepository(GnuCashRepositoryPort):
    """Repository backed by the analytics database."""

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
            FROM commodities
            WHERE mnemonic = :currency AND namespace = 'CURRENCY'
            LIMIT 1
            """
        )
        engine = self._db_port.get_analytics_engine()
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
        query = self._build_asset_category_query(start_date, end_date)
        params = self._build_date_params(start_date, end_date)
        params["actif_root"] = actif_root_name
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

    def fetch_cashflow_rows(
        self,
        start_date: date | None,
        end_date: date | None,
        asset_root_name: str,
        currency_guid: str,
    ) -> list[CashflowRow]:
        query = self._build_cashflow_query(start_date, end_date)
        params = self._build_date_params(start_date, end_date)
        params["asset_root"] = asset_root_name
        params["currency_guid"] = currency_guid
        engine = self._db_port.get_analytics_engine()
        with engine.connect() as conn:
            rows = conn.execute(query, params).all()
        cashflow_rows = [
            CashflowRow(
                account_guid=row.account_guid,
                account_full_name=row.account_full_name,
                top_parent_name=row.top_parent_name,
                amount=coerce_decimal(row.amount),
            )
            for row in rows
        ]
        return list(cashflow_rows)

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

    @staticmethod
    def _build_cashflow_query(
        start_date: date | None,
        end_date: date | None,
    ):
        base_sql = """
        WITH RECURSIVE account_tree AS (
            SELECT guid,
                   parent_guid,
                   name,
                   NULL::TEXT AS full_name,
                   NULL::TEXT AS top_name
            FROM accounts
            WHERE parent_guid IS NULL
            UNION ALL
            SELECT a.guid,
                   a.parent_guid,
                   a.name,
                   CASE
                       WHEN at.full_name IS NULL THEN a.name
                       ELSE at.full_name || ':' || a.name
                   END AS full_name,
                   CASE
                       WHEN at.top_name IS NULL THEN a.name
                       ELSE at.top_name
                   END AS top_name
            FROM accounts a
            JOIN account_tree at ON a.parent_guid = at.guid
        ),
        asset_accounts AS (
            SELECT guid
            FROM account_tree
            WHERE top_name = :asset_root
        ),
        asset_transactions AS (
            SELECT DISTINCT s.tx_guid
            FROM splits s
            JOIN asset_accounts aa ON aa.guid = s.account_guid
            JOIN transactions t ON t.guid = s.tx_guid
            JOIN accounts a ON a.guid = s.account_guid
            JOIN commodities c ON c.guid = a.commodity_guid
            WHERE c.guid = :currency_guid
        """
        if start_date:
            base_sql += " AND t.post_date >= :start_date"
        if end_date:
            base_sql += " AND t.post_date <= :end_date"
        base_sql += """
        ),
        cashflow_splits AS (
            SELECT a.guid AS account_guid,
                   at.full_name AS account_full_name,
                   at.top_name AS top_parent_name,
                   CASE
                       WHEN c.namespace = 'CURRENCY'
                           THEN -CAST(s.value_num AS NUMERIC) / NULLIF(s.value_denom, 0)
                       ELSE -CAST(s.quantity_num AS NUMERIC) / NULLIF(s.quantity_denom, 0)
                    END AS signed_amount
            FROM splits s
            JOIN asset_transactions atx ON atx.tx_guid = s.tx_guid
            JOIN accounts a ON a.guid = s.account_guid
            JOIN account_tree at ON at.guid = a.guid
            JOIN commodities c ON c.guid = a.commodity_guid
            WHERE a.guid NOT IN (SELECT guid FROM asset_accounts)
              AND c.guid = :currency_guid
        ),
        cashflow_aggregates AS (
            SELECT account_guid,
                   account_full_name,
                   top_parent_name,
                   SUM(CASE
                           WHEN signed_amount > 0 THEN signed_amount
                           ELSE 0
                       END) AS incoming_amount,
                   SUM(CASE
                           WHEN signed_amount < 0 THEN signed_amount
                           ELSE 0
                       END) AS outgoing_amount
            FROM cashflow_splits
            GROUP BY account_guid, account_full_name, top_parent_name
        )
        SELECT account_guid,
               account_full_name,
               top_parent_name,
               incoming_amount AS amount
        FROM cashflow_aggregates
        WHERE incoming_amount <> 0
        UNION ALL
        SELECT account_guid,
               account_full_name,
               top_parent_name,
               outgoing_amount AS amount
        FROM cashflow_aggregates
        WHERE outgoing_amount <> 0
        ORDER BY account_full_name, account_guid, amount DESC
        """
        return text(base_sql)


__all__ = ["AnalyticsGnuCashRepository"]
