"""CLI adapter to compare SQLAlchemy and piecash backends."""

from datetime import date
import os

from src.application.use_cases.compare_backends import CompareBackendsUseCase
from src.infrastructure.container import build_database_adapter
from src.infrastructure.gnucash_repository import SqlAlchemyGnuCashRepository
from src.infrastructure.logging.logger import get_app_logger
from src.infrastructure.piecash_repository import PieCashGnuCashRepository
from src.infrastructure.settings import GnuCashSettings


def _parse_date(value: str | None, logger) -> date | None:
    """Parse an ISO date string into a date.

    Args:
        value: Date string in YYYY-MM-DD format.
        logger: Logger used for warnings.

    Returns:
        date | None: Parsed date or None when invalid.
    """
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        logger.warning(
            f"Invalid date '{value}'. Expected format YYYY-MM-DD."
        )
        return None


def main() -> None:
    """Run a sanity check comparing SQLAlchemy vs piecash outputs."""
    logger = get_app_logger()
    settings = GnuCashSettings.from_env()
    if settings.piecash_file is None:
        logger.warning(
            "PIECASH_FILE is required to compare SQLAlchemy and piecash."
        )
        return

    start_date = _parse_date(os.getenv("SANITY_START_DATE"), logger)
    end_date = _parse_date(os.getenv("SANITY_END_DATE"), logger)
    target_currency = os.getenv("SANITY_CURRENCY", "EUR")

    db_adapter = build_database_adapter()
    sql_repo = SqlAlchemyGnuCashRepository(db_adapter)
    try:
        piecash_repo = PieCashGnuCashRepository(
            settings.piecash_file,
            logger=logger,
        )
    except RuntimeError as exc:
        logger.error(str(exc))
        return

    use_case = CompareBackendsUseCase(
        left_repository=sql_repo,
        right_repository=piecash_repo,
        logger=logger,
    )
    result = use_case.execute(
        start_date=start_date,
        end_date=end_date,
        target_currency=target_currency,
        left_name="sqlalchemy",
        right_name="piecash",
    )

    print(
        "Backend comparison "
        f"(currency={target_currency}, start={start_date}, end={end_date})"
    )
    print(
        f"{result.left.name}: balances={result.left.balance_count}, "
        f"prices={result.left.price_count}, assets={result.left.asset_total}, "
        f"liabilities={result.left.liability_total}, "
        f"net_worth={result.left.net_worth}"
    )
    print(
        f"{result.right.name}: balances={result.right.balance_count}, "
        f"prices={result.right.price_count}, assets={result.right.asset_total}, "
        f"liabilities={result.right.liability_total}, "
        f"net_worth={result.right.net_worth}"
    )
    print(
        "Deltas (right - left): "
        f"balances={result.diff.balance_count_delta}, "
        f"prices={result.diff.price_count_delta}, "
        f"assets={result.diff.asset_delta}, "
        f"liabilities={result.diff.liability_delta}, "
        f"net_worth={result.diff.net_worth_delta}"
    )


if __name__ == "__main__":  # pragma: no cover
    main()
