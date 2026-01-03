"""Use case to compare GnuCash repository backends."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from src.application.ports.gnucash_repository import GnuCashRepositoryPort
from src.domain.models import (
    AssetCategoryBalanceRow,
    NetWorthBalanceRow,
    PriceRow,
)
from src.application.use_cases.get_net_worth_summary import (
    GetNetWorthSummaryUseCase,
)
from src.infrastructure.logging.logger import get_app_logger


@dataclass(frozen=True)
class BackendSnapshot:
    """Snapshot of totals and counts for a backend."""

    name: str
    balance_count: int
    price_count: int
    asset_total: Decimal
    liability_total: Decimal
    net_worth: Decimal
    currency_code: str


@dataclass(frozen=True)
class BackendDiff:
    """Difference between two backend snapshots."""

    balance_count_delta: int
    price_count_delta: int
    asset_delta: Decimal
    liability_delta: Decimal
    net_worth_delta: Decimal


@dataclass(frozen=True)
class BackendComparison:
    """Comparison result for two backends."""

    left: BackendSnapshot
    right: BackendSnapshot
    diff: BackendDiff


class _CountingRepository:
    """Wrapper around a repository to capture counts."""

    def __init__(self, repository: GnuCashRepositoryPort) -> None:
        self._repository = repository
        self.balance_count = 0
        self.price_count = 0

    def fetch_currency_guid(self, currency: str) -> str:
        return self._repository.fetch_currency_guid(currency)

    def fetch_net_worth_balances(
        self,
        start_date: date | None,
        end_date: date | None,
    ) -> list[NetWorthBalanceRow]:
        balances = self._repository.fetch_net_worth_balances(
            start_date,
            end_date,
        )
        self.balance_count = len(balances)
        return balances

    def fetch_asset_category_balances(
        self,
        start_date: date | None,
        end_date: date | None,
        actif_root_name: str,
    ) -> list[AssetCategoryBalanceRow]:
        return self._repository.fetch_asset_category_balances(
            start_date,
            end_date,
            actif_root_name,
        )

    def fetch_latest_prices(
        self,
        currency_guid: str,
        end_date: date | None,
    ) -> list[PriceRow]:
        prices = self._repository.fetch_latest_prices(
            currency_guid,
            end_date,
        )
        self.price_count = len(prices)
        return prices


class CompareBackendsUseCase:
    """Compare key metrics between two repository backends."""

    def __init__(
        self,
        left_repository: GnuCashRepositoryPort,
        right_repository: GnuCashRepositoryPort,
        logger=None,
    ) -> None:
        """Initialize the use case.

        Args:
            left_repository: Repository used as baseline for comparison.
            right_repository: Repository used for comparison.
            logger: Optional logger compatible with logging.Logger-like API.
        """
        self._left_repository = left_repository
        self._right_repository = right_repository
        self._logger = logger or get_app_logger()

    def execute(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        target_currency: str = "EUR",
        left_name: str = "sqlalchemy",
        right_name: str = "piecash",
    ) -> BackendComparison:
        """Return a comparison between the two backends.

        Args:
            start_date: Optional lower bound for transaction post dates.
            end_date: Optional upper bound for transaction post dates.
            target_currency: Currency code to convert into.
            left_name: Label for the baseline backend.
            right_name: Label for the compared backend.

        Returns:
            BackendComparison: Aggregated comparison data.
        """
        left_snapshot = self._build_snapshot(
            self._left_repository,
            left_name,
            start_date,
            end_date,
            target_currency,
        )
        right_snapshot = self._build_snapshot(
            self._right_repository,
            right_name,
            start_date,
            end_date,
            target_currency,
        )

        diff = BackendDiff(
            balance_count_delta=(
                right_snapshot.balance_count - left_snapshot.balance_count
            ),
            price_count_delta=(
                right_snapshot.price_count - left_snapshot.price_count
            ),
            asset_delta=right_snapshot.asset_total - left_snapshot.asset_total,
            liability_delta=(
                right_snapshot.liability_total - left_snapshot.liability_total
            ),
            net_worth_delta=(
                right_snapshot.net_worth - left_snapshot.net_worth
            ),
        )
        return BackendComparison(
            left=left_snapshot,
            right=right_snapshot,
            diff=diff,
        )

    def _build_snapshot(
        self,
        repository: GnuCashRepositoryPort,
        name: str,
        start_date: date | None,
        end_date: date | None,
        target_currency: str,
    ) -> BackendSnapshot:
        counting_repo = _CountingRepository(repository)
        summary = GetNetWorthSummaryUseCase(
            gnucash_repository=counting_repo,
            logger=self._logger,
        ).execute(
            start_date=start_date,
            end_date=end_date,
            target_currency=target_currency,
        )
        return BackendSnapshot(
            name=name,
            balance_count=counting_repo.balance_count,
            price_count=counting_repo.price_count,
            asset_total=summary.asset_total,
            liability_total=summary.liability_total,
            net_worth=summary.net_worth,
            currency_code=summary.currency_code,
        )


__all__ = [
    "BackendSnapshot",
    "BackendDiff",
    "BackendComparison",
    "CompareBackendsUseCase",
]
