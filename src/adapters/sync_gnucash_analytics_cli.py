"""CLI adapter to mirror GnuCash tables into analytics storage."""

from src.application.use_cases.sync_gnucash_analytics import (
    SyncGnuCashAnalyticsUseCase,
)
from src.infrastructure.container import build_database_adapter
from src.infrastructure.logging.logger import get_app_logger


def main() -> None:
    """Run the GnuCash analytics sync use case."""
    logger = get_app_logger()
    adapter = build_database_adapter()
    use_case = SyncGnuCashAnalyticsUseCase(
        db_port=adapter,
        logger=logger,
    )
    result = use_case.run()
    print(
        "Synchronized GnuCash tables into analytics. "
        f"accounts={result.accounts_count}, "
        f"commodities={result.commodities_count}, "
        f"splits={result.splits_count}, "
        f"transactions={result.transactions_count}, "
        f"prices={result.prices_count}."
    )


if __name__ == "__main__":  # pragma: no cover
    main()
