"""Dependency providers for HTTP API endpoints."""

from __future__ import annotations

import os

from src.adapters.interface.http_api.data_version import DataVersionStore
from src.application.use_cases.get_account_balances import GetAccountBalancesUseCase
from src.application.use_cases.get_accounts import GetAccountsUseCase
from src.application.use_cases.get_accounts_tree import GetAccountsTreeUseCase
from src.application.use_cases.get_asset_category_breakdown import (
    GetAssetCategoryBreakdownUseCase,
)
from src.application.use_cases.get_cashflow import GetCashflowUseCase
from src.application.use_cases.get_cashflow_asset_selection import (
    GetCashflowAssetSelectionUseCase,
)
from src.application.use_cases.get_budget_applicability import (
    GetBudgetApplicabilityUseCase,
)
from src.application.use_cases.get_budget_month_view import (
    GetBudgetMonthViewUseCase,
)
from src.application.use_cases.get_budgets import GetBudgetsUseCase
from src.application.use_cases.get_net_worth_summary import GetNetWorthSummaryUseCase
from src.application.use_cases.sync_gnucash_analytics import SyncGnuCashAnalyticsUseCase
from src.infrastructure.container import (
    build_accounts_repository,
    build_accounts_tree_repository,
    build_analytics_repository,
    build_budget_repository,
    build_database_adapter,
)
from src.infrastructure.settings import GnuCashSettings


def get_data_version_store() -> DataVersionStore:
    """Return app-level data version store.

    This dependency is overridden at app wiring time.
    """
    return DataVersionStore()


def get_read_mode() -> str:
    """Return effective analytics read mode."""
    return os.getenv("ANALYTICS_READ_MODE", "tables").strip().lower()


def get_backend() -> str:
    """Return configured backend identifier."""
    return GnuCashSettings.from_env().backend


def get_sync_use_case() -> SyncGnuCashAnalyticsUseCase:
    """Build sync use case."""
    return SyncGnuCashAnalyticsUseCase(db_port=build_database_adapter())


def get_accounts_use_case() -> GetAccountsUseCase:
    """Build accounts use case."""
    return GetAccountsUseCase(repository=build_accounts_repository())


def get_accounts_tree_use_case() -> GetAccountsTreeUseCase:
    """Build accounts tree use case."""
    return GetAccountsTreeUseCase(repository=build_accounts_tree_repository())


def get_net_worth_use_case() -> GetNetWorthSummaryUseCase:
    """Build net worth use case."""
    return GetNetWorthSummaryUseCase(
        gnucash_repository=build_analytics_repository()
    )


def get_account_balances_use_case() -> GetAccountBalancesUseCase:
    """Build account balances use case."""
    return GetAccountBalancesUseCase(gnucash_repository=build_analytics_repository())


def get_asset_category_breakdown_use_case() -> GetAssetCategoryBreakdownUseCase:
    """Build asset category breakdown use case."""
    return GetAssetCategoryBreakdownUseCase(
        gnucash_repository=build_analytics_repository()
    )


def get_cashflow_asset_selection_use_case() -> GetCashflowAssetSelectionUseCase:
    """Build cashflow asset selection use case."""
    return GetCashflowAssetSelectionUseCase(
        repository=build_accounts_tree_repository()
    )


def get_cashflow_use_case() -> GetCashflowUseCase:
    """Build cashflow use case."""
    return GetCashflowUseCase(gnucash_repository=build_analytics_repository())


def get_budgets_use_case() -> GetBudgetsUseCase:
    """Build budgets use case."""
    return GetBudgetsUseCase(repository=build_budget_repository())


def get_budget_applicability_use_case() -> GetBudgetApplicabilityUseCase:
    """Build budget applicability use case."""
    return GetBudgetApplicabilityUseCase(repository=build_budget_repository())


def get_budget_month_view_use_case() -> GetBudgetMonthViewUseCase:
    """Build budget month view use case."""
    return GetBudgetMonthViewUseCase(repository=build_budget_repository())
