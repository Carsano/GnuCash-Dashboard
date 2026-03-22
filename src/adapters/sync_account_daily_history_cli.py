"""CLI adapter to materialize daily account valuation history."""

from src.application.use_cases.sync_account_daily_history import (
    SyncAccountDailyHistoryUseCase,
)
from src.infrastructure.container import build_database_adapter
from src.infrastructure.logging.logger import get_app_logger


def main() -> None:
    """Run the daily account history sync use case."""
    logger = get_app_logger()
    adapter = build_database_adapter()
    use_case = SyncAccountDailyHistoryUseCase(
        db_port=adapter,
        logger=logger,
    )
    result = use_case.run()
    print(
        "Synchronized account daily history into analytics. "
        f"accounts={result.account_count}, "
        f"snapshots={result.snapshot_count}, "
        f"inserted={result.inserted_count}, "
        f"currency={result.target_currency}."
    )


if __name__ == "__main__":  # pragma: no cover
    main()
