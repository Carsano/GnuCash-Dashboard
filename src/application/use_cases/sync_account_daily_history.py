"""Use case to materialize daily account valuation history into analytics."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import bindparam, text

from src.application.ports.database import DatabaseEnginePort
from src.domain.constants import DEFAULT_ASSET_TYPES, DEFAULT_LIABILITY_TYPES
from src.domain.policies.account_filters import is_valid_account_name
from src.domain.services.account_categorization import (
    categorize_account,
    categorize_balance_sheet_side,
)
from src.domain.services.fx import convert_balance
from src.infrastructure.logging.logger import get_app_logger
from src.utils.decimal_utils import coerce_decimal


TRACKED_ACCOUNT_TYPES = DEFAULT_ASSET_TYPES + DEFAULT_LIABILITY_TYPES

CREATE_ACCOUNTS_DAILY_HISTORY_SQL = """
CREATE TABLE IF NOT EXISTS accounts_daily_history (
    snapshot_date DATE NOT NULL,
    guid TEXT NOT NULL,
    name TEXT NOT NULL,
    account_type TEXT NOT NULL,
    parent_guid TEXT,
    commodity_guid TEXT,
    mnemonic TEXT,
    namespace TEXT,
    is_placeholder BOOLEAN DEFAULT FALSE,
    business_category TEXT NOT NULL,
    balance_sheet_category TEXT NOT NULL,
    balance_native NUMERIC NOT NULL,
    balance_converted NUMERIC,
    target_currency TEXT NOT NULL,
    PRIMARY KEY (snapshot_date, guid, target_currency)
)
"""

SELECT_HISTORY_ACCOUNTS_SQL = text(
    """
    SELECT a.guid,
           a.name,
           a.account_type,
           a.parent_guid,
           a.commodity_guid,
           c.mnemonic,
           c.namespace,
           COALESCE(a.is_placeholder, FALSE) AS is_placeholder
    FROM accounts a
    LEFT JOIN commodities c ON c.guid = a.commodity_guid
    WHERE a.account_type IN :account_types
    ORDER BY a.guid
    """
).bindparams(bindparam("account_types", expanding=True))

SELECT_DAILY_DELTAS_SQL = text(
    """
    SELECT s.account_guid AS guid,
           DATE(t.post_date) AS snapshot_date,
           SUM(
               CASE
                   WHEN c.namespace = 'CURRENCY'
                       THEN CAST(s.value_num AS NUMERIC) / NULLIF(s.value_denom, 0)
                   ELSE CAST(s.quantity_num AS NUMERIC) / NULLIF(s.quantity_denom, 0)
               END
           ) AS delta
    FROM splits s
    JOIN transactions t ON t.guid = s.tx_guid
    JOIN accounts a ON a.guid = s.account_guid
    JOIN commodities c ON c.guid = a.commodity_guid
    WHERE s.account_guid IN :account_guids
      AND t.post_date IS NOT NULL
    GROUP BY s.account_guid, DATE(t.post_date)
    ORDER BY DATE(t.post_date), s.account_guid
    """
).bindparams(bindparam("account_guids", expanding=True))

SELECT_MIN_MAX_DATES_SQL = text(
    """
    SELECT MIN(DATE(t.post_date)) AS min_date,
           MAX(DATE(t.post_date)) AS max_date
    FROM splits s
    JOIN transactions t ON t.guid = s.tx_guid
    WHERE s.account_guid IN :account_guids
      AND t.post_date IS NOT NULL
    """
).bindparams(bindparam("account_guids", expanding=True))

SELECT_PRICE_HISTORY_SQL = text(
    """
    SELECT commodity_guid,
           value_num,
           value_denom,
           DATE(date) AS price_date
    FROM prices
    WHERE currency_guid = :currency_guid
      AND DATE(date) <= :end_date
    ORDER BY DATE(date), commodity_guid
    """
)

INSERT_ACCOUNTS_DAILY_HISTORY_SQL = text(
    """
    INSERT INTO accounts_daily_history (
        snapshot_date,
        guid,
        name,
        account_type,
        parent_guid,
        commodity_guid,
        mnemonic,
        namespace,
        is_placeholder,
        business_category,
        balance_sheet_category,
        balance_native,
        balance_converted,
        target_currency
    )
    VALUES (
        :snapshot_date,
        :guid,
        :name,
        :account_type,
        :parent_guid,
        :commodity_guid,
        :mnemonic,
        :namespace,
        :is_placeholder,
        :business_category,
        :balance_sheet_category,
        :balance_native,
        :balance_converted,
        :target_currency
    )
    """
)


@dataclass(frozen=True)
class SyncAccountDailyHistoryResult:
    """Summary of a daily history materialization run."""

    account_count: int
    snapshot_count: int
    inserted_count: int
    target_currency: str


class SyncAccountDailyHistoryUseCase:
    """Materialize a daily valuation history for patrimony accounts."""

    def __init__(
        self,
        db_port: DatabaseEnginePort,
        logger=None,
    ) -> None:
        self._db_port = db_port
        self._logger = logger or get_app_logger()

    def run(
        self,
        *,
        target_currency: str = "EUR",
    ) -> SyncAccountDailyHistoryResult:
        """Build daily history rows in the analytics database."""
        engine = self._db_port.get_analytics_engine()
        with engine.connect() as conn:
            currency_guid = self._fetch_currency_guid(
                conn,
                currency=target_currency,
            )
            accounts = self._load_accounts(conn)

            if not accounts:
                with engine.begin() as write_conn:
                    write_conn.exec_driver_sql(CREATE_ACCOUNTS_DAILY_HISTORY_SQL)
                    self._truncate_table(
                        write_conn,
                        target_currency=target_currency,
                    )
                return SyncAccountDailyHistoryResult(
                    account_count=0,
                    snapshot_count=0,
                    inserted_count=0,
                    target_currency=target_currency,
                )

            account_guids = [account["guid"] for account in accounts]
            snapshot_dates = self._build_snapshot_dates(
                conn,
                account_guids=account_guids,
            )
            if not snapshot_dates:
                return SyncAccountDailyHistoryResult(
                    account_count=len(accounts),
                    snapshot_count=0,
                    inserted_count=0,
                    target_currency=target_currency,
                )

            daily_deltas = self._load_daily_deltas(
                conn,
                account_guids=account_guids,
            )
            price_history = self._load_price_history(
                conn,
                currency_guid=currency_guid,
                end_date=snapshot_dates[-1],
            )

        payload = self._build_history_rows(
            accounts=accounts,
            snapshot_dates=snapshot_dates,
            daily_deltas=daily_deltas,
            price_history=price_history,
            currency_guid=currency_guid,
            target_currency=target_currency,
        )

        with engine.begin() as conn:
            conn.exec_driver_sql(CREATE_ACCOUNTS_DAILY_HISTORY_SQL)
            self._ensure_column(
                conn,
                table_name="accounts_daily_history",
                column_name="balance_sheet_category",
                column_type="TEXT",
            )
            self._truncate_table(conn, target_currency=target_currency)
            if payload:
                conn.execute(INSERT_ACCOUNTS_DAILY_HISTORY_SQL, payload)

        self._logger.info(
            "Materialized "
            f"{len(payload)} rows into analytics.accounts_daily_history"
        )
        return SyncAccountDailyHistoryResult(
            account_count=len(accounts),
            snapshot_count=len(snapshot_dates),
            inserted_count=len(payload),
            target_currency=target_currency,
        )

    def _load_accounts(self, conn) -> list[dict[str, object]]:
        rows = conn.execute(
            SELECT_HISTORY_ACCOUNTS_SQL,
            {"account_types": list(TRACKED_ACCOUNT_TYPES)},
        ).all()
        accounts: list[dict[str, object]] = []
        for row in rows:
            if bool(row.is_placeholder):
                continue
            name = row.name or ""
            if not is_valid_account_name(name):
                continue
            accounts.append(
                {
                    "guid": row.guid,
                    "name": name,
                    "account_type": row.account_type,
                    "parent_guid": row.parent_guid,
                    "commodity_guid": row.commodity_guid,
                    "mnemonic": row.mnemonic,
                    "namespace": row.namespace,
                    "is_placeholder": False,
                    "business_category": categorize_account(
                        name=name,
                        account_type=row.account_type,
                    ),
                    "balance_sheet_category": categorize_balance_sheet_side(
                        row.account_type
                    ),
                }
            )
        return accounts

    @staticmethod
    def _fetch_currency_guid(conn, *, currency: str) -> str:
        result = conn.execute(
            text(
                """
                SELECT guid
                FROM commodities
                WHERE mnemonic = :currency
                  AND namespace = 'CURRENCY'
                LIMIT 1
                """
            ),
            {"currency": currency},
        ).first()
        if not result:
            raise RuntimeError(f"Missing currency in commodities: {currency}")
        return result.guid

    @staticmethod
    def _coerce_date(raw_value) -> date | None:
        if raw_value is None:
            return None
        if isinstance(raw_value, date):
            return raw_value
        return date.fromisoformat(str(raw_value))

    @classmethod
    def _build_snapshot_dates(
        cls,
        conn,
        *,
        account_guids: list[str],
    ) -> list[date]:
        row = conn.execute(
            SELECT_MIN_MAX_DATES_SQL,
            {"account_guids": list(account_guids)},
        ).first()
        min_date = cls._coerce_date(row.min_date) if row else None
        max_date = cls._coerce_date(row.max_date) if row else None
        if min_date is None or max_date is None:
            return []
        max_date = min(max_date, date.today())
        if min_date > max_date:
            return []

        current = min_date
        dates: list[date] = []
        while current <= max_date:
            dates.append(current)
            current += timedelta(days=1)
        return dates

    @classmethod
    def _load_daily_deltas(
        cls,
        conn,
        *,
        account_guids: list[str],
    ) -> dict[tuple[str, date], Decimal]:
        rows = conn.execute(
            SELECT_DAILY_DELTAS_SQL,
            {"account_guids": list(account_guids)},
        ).all()
        deltas: dict[tuple[str, date], Decimal] = {}
        for row in rows:
            snapshot_date = cls._coerce_date(row.snapshot_date)
            if snapshot_date is None:
                continue
            deltas[(row.guid, snapshot_date)] = coerce_decimal(row.delta)
        return deltas

    @classmethod
    def _load_price_history(
        cls,
        conn,
        *,
        currency_guid: str,
        end_date: date,
    ) -> list[dict[str, object]]:
        rows = conn.execute(
            SELECT_PRICE_HISTORY_SQL,
            {
                "currency_guid": currency_guid,
                "end_date": end_date,
            },
        ).all()
        return [
            {
                "commodity_guid": row.commodity_guid,
                "rate": (
                    coerce_decimal(row.value_num)
                    / coerce_decimal(row.value_denom)
                ),
                "price_date": cls._coerce_date(row.price_date),
            }
            for row in rows
            if coerce_decimal(row.value_denom) != 0
            and cls._coerce_date(row.price_date) is not None
        ]

    def _build_history_rows(
        self,
        *,
        accounts: list[dict[str, object]],
        snapshot_dates: list[date],
        daily_deltas: dict[tuple[str, date], Decimal],
        price_history: list[dict[str, object]],
        currency_guid: str,
        target_currency: str,
    ) -> list[dict[str, object]]:
        balances = defaultdict(lambda: Decimal("0"))
        current_rates: dict[str, Decimal] = {}
        price_index = 0
        payload: list[dict[str, object]] = []

        for snapshot_date in snapshot_dates:
            while (
                price_index < len(price_history)
                and price_history[price_index]["price_date"] <= snapshot_date
            ):
                current_rates[
                    str(price_history[price_index]["commodity_guid"])
                ] = price_history[price_index]["rate"]
                price_index += 1

            for account in accounts:
                guid = str(account["guid"])
                balances[guid] += daily_deltas.get(
                    (guid, snapshot_date),
                    Decimal("0"),
                )
                balance_native = balances[guid]
                converted = convert_balance(
                    balance_native,
                    str(account.get("commodity_guid") or ""),
                    str(account.get("mnemonic") or ""),
                    str(account.get("namespace") or ""),
                    currency_guid,
                    target_currency,
                    current_rates,
                    logger=self._logger,
                )
                payload.append(
                    {
                        "snapshot_date": snapshot_date,
                        "guid": guid,
                        "name": account["name"],
                        "account_type": account["account_type"],
                        "parent_guid": account["parent_guid"],
                        "commodity_guid": account["commodity_guid"],
                        "mnemonic": account["mnemonic"],
                        "namespace": account["namespace"],
                        "is_placeholder": account["is_placeholder"],
                        "business_category": account["business_category"],
                        "balance_sheet_category": account[
                            "balance_sheet_category"
                        ],
                        "balance_native": self._sql_numeric(balance_native),
                        "balance_converted": self._sql_numeric(converted),
                        "target_currency": target_currency,
                    }
                )
        return payload

    @staticmethod
    def _sql_numeric(value: Decimal | None) -> str | None:
        if value is None:
            return None
        return str(value)

    @staticmethod
    def _truncate_table(conn, *, target_currency: str) -> None:
        dialect = conn.engine.dialect.name
        if dialect == "sqlite":
            conn.execute(
                text(
                    """
                    DELETE FROM accounts_daily_history
                    WHERE target_currency = :target_currency
                    """
                ),
                {"target_currency": target_currency},
            )
            return
        conn.execute(
            text(
                """
                DELETE FROM accounts_daily_history
                WHERE target_currency = :target_currency
                """
            ),
            {"target_currency": target_currency},
        )

    @staticmethod
    def _ensure_column(
        conn,
        *,
        table_name: str,
        column_name: str,
        column_type: str,
    ) -> None:
        dialect = conn.engine.dialect.name
        if dialect == "sqlite":
            columns = {
                row[1]
                for row in conn.exec_driver_sql(
                    f"PRAGMA table_info({table_name})"
                ).all()
            }
            if column_name not in columns:
                conn.exec_driver_sql(
                    f"ALTER TABLE {table_name} "
                    f"ADD COLUMN {column_name} {column_type}"
                )
            return

        exists = conn.execute(
            text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = :table_name
                  AND column_name = :column_name
                LIMIT 1
                """
            ),
            {
                "table_name": table_name,
                "column_name": column_name,
            },
        ).first()
        if not exists:
            conn.exec_driver_sql(
                f"ALTER TABLE {table_name} "
                f"ADD COLUMN {column_name} {column_type}"
            )


__all__ = [
    "SyncAccountDailyHistoryUseCase",
    "SyncAccountDailyHistoryResult",
    "CREATE_ACCOUNTS_DAILY_HISTORY_SQL",
]
