"""Use case to materialize business account categories into analytics."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import bindparam, text

from src.application.ports.database import DatabaseEnginePort
from src.domain.constants import DEFAULT_ASSET_TYPES, DEFAULT_LIABILITY_TYPES
from src.domain.policies.account_filters import is_valid_account_name
from src.domain.services.account_categorization import (
    categorize_account,
    categorize_balance_sheet_side,
)
from src.infrastructure.logging.logger import get_app_logger

TRACKED_ACCOUNT_TYPES = DEFAULT_ASSET_TYPES + DEFAULT_LIABILITY_TYPES


CREATE_ACCOUNTS_BUSINESS_SQL = """
CREATE TABLE IF NOT EXISTS accounts_business (
    guid TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    account_type TEXT NOT NULL,
    parent_guid TEXT,
    is_placeholder BOOLEAN DEFAULT FALSE,
    business_category TEXT NOT NULL,
    balance_sheet_category TEXT NOT NULL
)
"""

SELECT_ACCOUNTS_SQL = text(
    """
    SELECT guid,
           name,
           account_type,
           parent_guid,
           COALESCE(is_placeholder, FALSE) AS is_placeholder
    FROM accounts
    WHERE account_type IN :account_types
    """
).bindparams(bindparam("account_types", expanding=True))

INSERT_ACCOUNTS_BUSINESS_SQL = text(
    """
    INSERT INTO accounts_business (
        guid,
        name,
        account_type,
        parent_guid,
        is_placeholder,
        business_category,
        balance_sheet_category
    )
    VALUES (
        :guid,
        :name,
        :account_type,
        :parent_guid,
        :is_placeholder,
        :business_category,
        :balance_sheet_category
    )
    """
)


@dataclass(frozen=True)
class SyncAccountCategoriesResult:
    """Summary of the materialized account categories sync."""

    source_count: int
    inserted_count: int


class SyncAccountCategoriesUseCase:
    """Materialize Python account categories into analytics.accounts_business."""

    def __init__(
        self,
        db_port: DatabaseEnginePort,
        logger=None,
    ) -> None:
        self._db_port = db_port
        self._logger = logger or get_app_logger()

    def run(self) -> SyncAccountCategoriesResult:
        """Read imported accounts, categorize them, and refresh the table."""
        engine = self._db_port.get_analytics_engine()

        with engine.connect() as conn:
            rows = conn.execute(
                SELECT_ACCOUNTS_SQL,
                {"account_types": list(TRACKED_ACCOUNT_TYPES)},
            ).all()

        payload = [
            {
                "guid": row.guid,
                "name": row.name,
                "account_type": row.account_type,
                "parent_guid": row.parent_guid,
                "is_placeholder": bool(row.is_placeholder),
                "business_category": categorize_account(
                    name=row.name,
                    account_type=row.account_type,
                ),
                "balance_sheet_category": categorize_balance_sheet_side(
                    row.account_type
                ),
            }
            for row in rows
            if is_valid_account_name(row.name)
        ]

        with engine.begin() as conn:
            conn.exec_driver_sql(CREATE_ACCOUNTS_BUSINESS_SQL)
            self._ensure_column(
                conn,
                table_name="accounts_business",
                column_name="parent_guid",
                column_type="TEXT",
            )
            self._ensure_column(
                conn,
                table_name="accounts_business",
                column_name="balance_sheet_category",
                column_type="TEXT",
            )
            self._truncate_table(conn)
            if payload:
                conn.execute(INSERT_ACCOUNTS_BUSINESS_SQL, payload)

        self._logger.info(
            "Materialized "
            f"{len(payload)} accounts into analytics.accounts_business"
        )
        return SyncAccountCategoriesResult(
            source_count=len(rows),
            inserted_count=len(payload),
        )

    @staticmethod
    def _truncate_table(conn) -> None:
        dialect = conn.engine.dialect.name
        if dialect == "sqlite":
            conn.exec_driver_sql("DELETE FROM accounts_business")
            return
        conn.exec_driver_sql("TRUNCATE TABLE accounts_business")

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
    "SyncAccountCategoriesUseCase",
    "SyncAccountCategoriesResult",
    "CREATE_ACCOUNTS_BUSINESS_SQL",
    "SELECT_ACCOUNTS_SQL",
    "INSERT_ACCOUNTS_BUSINESS_SQL",
]
