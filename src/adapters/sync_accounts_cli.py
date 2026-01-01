"""CLI adapter to synchronize GnuCash accounts into the analytics database.

This module wires the SyncAccountsUseCase to the concrete infrastructure
adapters and provides a simple command-line entry point for running the
sync job.
"""

from src.application.use_cases.sync_accounts import SyncAccountsUseCase
from src.infrastructure.accounts_sync import (
    SqlAlchemyAccountsDestination,
    SqlAlchemyAccountsSource,
)
from src.infrastructure.db import SqlAlchemyDatabaseEngineAdapter
from src.infrastructure.logging.logger import get_app_logger


def main() -> None:
    """Run the accounts synchronization use case."""
    logger = get_app_logger()
    db_adapter = SqlAlchemyDatabaseEngineAdapter()
    source = SqlAlchemyAccountsSource(db_adapter)
    destination = SqlAlchemyAccountsDestination(db_adapter)
    use_case = SyncAccountsUseCase(
        source_port=source,
        destination_port=destination,
        logger=logger,
    )

    result = use_case.run()

    print(
        f"Synchronized {result.inserted_count} accounts "
        f"into the analytics database."
    )


if __name__ == "__main__":  # pragma: no cover
    main()
