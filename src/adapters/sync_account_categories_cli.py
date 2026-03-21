"""CLI adapter to materialize business account categories into analytics."""

from src.application.use_cases.sync_account_categories import (
    SyncAccountCategoriesUseCase,
)
from src.infrastructure.container import build_database_adapter
from src.infrastructure.logging.logger import get_app_logger


def main() -> None:
    """Run the account business-category sync use case."""
    logger = get_app_logger()
    adapter = build_database_adapter()
    use_case = SyncAccountCategoriesUseCase(
        db_port=adapter,
        logger=logger,
    )
    result = use_case.run()
    print(
        "Synchronized account business categories into analytics. "
        f"source={result.source_count}, inserted={result.inserted_count}."
    )


if __name__ == "__main__":  # pragma: no cover
    main()
