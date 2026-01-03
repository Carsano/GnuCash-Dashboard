"""SQLAlchemy-backed repository for analytics mirrored account hierarchy."""

from sqlalchemy import text

from src.application.ports.accounts_tree_repository import (
    AccountsTreeRepositoryPort,
)
from src.application.ports.database import DatabaseEnginePort
from src.domain.models.accounts import AccountDTO


class SqlAlchemyAccountsTreeRepository(AccountsTreeRepositoryPort):
    """Repository backed by SQLAlchemy for analytics.accounts."""

    def __init__(self, db_port: DatabaseEnginePort) -> None:
        """Initialize the repository.

        Args:
            db_port: Port providing access to the analytics engine.
        """
        self._db_port = db_port

    def fetch_accounts_tree(self) -> list[AccountDTO]:
        """Return accounts from the mirrored GnuCash table."""
        query = text(
            """
            SELECT guid, name, account_type, commodity_guid, parent_guid
            FROM accounts
            ORDER BY name
            """
        )
        engine = self._db_port.get_analytics_engine()
        with engine.connect() as conn:
            rows = conn.execute(query).all()
        return [
            AccountDTO(
                guid=row.guid,
                name=row.name,
                account_type=row.account_type,
                commodity_guid=row.commodity_guid,
                parent_guid=row.parent_guid,
            )
            for row in rows
        ]


__all__ = ["SqlAlchemyAccountsTreeRepository"]

