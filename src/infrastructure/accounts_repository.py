"""SQLAlchemy-backed repository for analytics accounts."""

from sqlalchemy import text

from src.application.ports.accounts_repository import AccountsRepositoryPort
from src.application.ports.database import DatabaseEnginePort
from src.domain.models.accounts import AccountDTO


class SqlAlchemyAccountsRepository(AccountsRepositoryPort):
    """Repository backed by SQLAlchemy for analytics accounts."""

    def __init__(self, db_port: DatabaseEnginePort) -> None:
        """Initialize the repository.

        Args:
            db_port: Port providing access to the analytics engine.
        """
        self._db_port = db_port

    def fetch_accounts(self) -> list[AccountDTO]:
        """Return analytics accounts from the database."""
        query = text(
            """
            SELECT guid, name, account_type, commodity_guid, parent_guid
            FROM accounts_dim
            ORDER BY name
            """
        )
        analytics_engine = self._db_port.get_analytics_engine()
        with analytics_engine.connect() as conn:
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


__all__ = ["SqlAlchemyAccountsRepository"]
