"""Use case to read analytics accounts for presentation layers."""

from dataclasses import dataclass
from typing import List

from sqlalchemy import text

from src.application.ports.database import DatabaseEnginePort
from src.application.use_cases.account_filters import is_valid_account_name


@dataclass(frozen=True)
class AccountDTO:
    """Serializable representation of an analytics account."""

    guid: str
    name: str
    account_type: str
    commodity_guid: str | None
    parent_guid: str | None


class GetAccountsUseCase:
    """Fetch accounts from the analytics database."""

    def __init__(self, db_port: DatabaseEnginePort) -> None:
        """Initialize the use case with its required dependencies."""
        self._db_port = db_port

    def execute(self) -> List[AccountDTO]:
        """Return every account currently stored in accounts_dim."""
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
            if is_valid_account_name(row.name)
        ]


__all__ = ["GetAccountsUseCase", "AccountDTO"]
