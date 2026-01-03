"""Application use cases package."""

from .sync_accounts import SyncAccountsUseCase, SyncAccountsResult
from .get_accounts import GetAccountsUseCase
from .get_account_balances import GetAccountBalancesUseCase
from .get_cashflow import GetCashflowUseCase
from .get_net_worth_summary import GetNetWorthSummaryUseCase
from .get_asset_category_breakdown import GetAssetCategoryBreakdownUseCase
from .compare_backends import CompareBackendsUseCase, BackendComparison
from .sync_gnucash_analytics import (
    SyncGnuCashAnalyticsUseCase,
    SyncGnuCashAnalyticsResult,
)
from src.domain.models.accounts import AccountDTO
from src.domain.models.accounts import AccountBalanceDTO
from src.domain.models.finance import (
    AssetCategoryAmount,
    AssetCategoryBreakdown,
    CashflowSummary,
    CashflowView,
    NetWorthSummary,
)

__all__ = [
    "SyncAccountsUseCase",
    "SyncAccountsResult",
    "GetAccountsUseCase",
    "AccountDTO",
    "GetAccountBalancesUseCase",
    "AccountBalanceDTO",
    "GetCashflowUseCase",
    "GetNetWorthSummaryUseCase",
    "NetWorthSummary",
    "GetAssetCategoryBreakdownUseCase",
    "AssetCategoryBreakdown",
    "AssetCategoryAmount",
    "CashflowSummary",
    "CashflowView",
    "CompareBackendsUseCase",
    "BackendComparison",
    "SyncGnuCashAnalyticsUseCase",
    "SyncGnuCashAnalyticsResult",
]
