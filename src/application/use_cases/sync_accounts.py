"""Use case for synchronizing GnuCash accounts into the analytics mirror.

This module defines a simple ETL-style use case that:

* reads accounts from the configured source adapter;
* ensures the canonical analytics accounts table exists;
* truncates the mirror and reloads its content from the source.
"""

from dataclasses import dataclass

from src.application.ports.accounts_sync import (
    AccountsDestinationPort,
    AccountsSourcePort,
)
from src.infrastructure.logging.logger import get_app_logger


@dataclass(frozen=True)
class SyncAccountsResult:
    """Result of a sync_accounts run.

    Attributes:
        source_count: Number of accounts read from the GnuCash database.
        inserted_count: Number of accounts inserted into the analytics table.
    """

    source_count: int
    inserted_count: int


class SyncAccountsUseCase:
    """Synchronize GnuCash accounts into the analytics mirror.

    The use case depends on ports to remain decoupled from concrete
    database drivers or storage configuration details.
    """

    def __init__(
        self,
        source_port: AccountsSourcePort,
        destination_port: AccountsDestinationPort,
        logger=None,
    ) -> None:
        """Initialize the use case.

        Args:
            source_port: Port providing access to source accounts.
            destination_port: Port responsible for analytics writes.
            logger: Optional logger compatible with logging.Logger-like API.
        """
        self._source_port = source_port
        self._destination_port = destination_port
        self._logger = logger or get_app_logger()

    def run(self) -> SyncAccountsResult:
        """Execute the synchronization job.

        The method creates the analytics table if needed, truncates it, and
        reloads all accounts from the GnuCash source database.

        Returns:
            SyncAccountsResult: Summary of how many rows were processed.
        """
        source_accounts = self._source_port.fetch_accounts()
        self._logger.info(
            f"Fetched {len(source_accounts)} accounts from source"
        )
        self._destination_port.prepare_destination()
        inserted_count = self._destination_port.refresh_accounts(
            sorted(source_accounts, key=lambda row: row.guid)
        )
        self._logger.info(
            f"Inserted {inserted_count} accounts into analytics.accounts"
        )

        return SyncAccountsResult(
            source_count=len(source_accounts),
            inserted_count=inserted_count,
        )


__all__ = ["SyncAccountsUseCase", "SyncAccountsResult"]
