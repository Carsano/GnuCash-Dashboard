"""Use case to build selectable asset accounts for cashflow dashboards."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from src.application.ports.accounts_tree_repository import AccountsTreeRepositoryPort
from src.application.use_cases.get_accounts_tree import GetAccountsTreeUseCase
from src.domain.models.accounts import AccountDTO


@dataclass(frozen=True, slots=True)
class CashflowAssetAccountOption:
    """Selectable asset account option for the cashflow UI."""

    guid: str
    display_name: str


@dataclass(frozen=True, slots=True)
class CashflowAssetSelection:
    """Computed selection model for cashflow asset accounts."""

    asset_root_name: str
    options: tuple[CashflowAssetAccountOption, ...]
    default_selected_guids: tuple[str, ...]

    @property
    def display_name_by_guid(self) -> dict[str, str]:
        """Return a guid -> display name mapping."""
        return {option.guid: option.display_name for option in self.options}

    @property
    def candidate_guids(self) -> tuple[str, ...]:
        """Return candidate GUIDs in deterministic order."""
        return tuple(option.guid for option in self.options)


def _build_account_full_names(accounts: Sequence[AccountDTO]) -> dict[str, str]:
    accounts_by_guid = {account.guid: account for account in accounts}
    full_name_by_guid: dict[str, str] = {}

    for account in accounts:
        parts: list[str] = []
        cursor: AccountDTO | None = account
        seen: set[str] = set()
        while cursor is not None and cursor.guid not in seen:
            seen.add(cursor.guid)
            parts.append(cursor.name)
            cursor = (
                accounts_by_guid.get(cursor.parent_guid)
                if cursor.parent_guid
                else None
            )
        full_name_by_guid[account.guid] = ":".join(reversed(parts))
    return full_name_by_guid


def build_cashflow_asset_selection(
    accounts: Sequence[AccountDTO],
    *,
    asset_root_name: str,
) -> CashflowAssetSelection:
    """Build cashflow asset account selection options.

    Args:
        accounts: Flat account list containing parent relationships.
        asset_root_name: Root account name identifying assets ("Actif").

    Returns:
        CashflowAssetSelection: Options + default selection.
    """
    accounts_by_guid = {account.guid: account for account in accounts}
    full_name_by_guid = _build_account_full_names(accounts)
    root_guids = {
        account.guid for account in accounts if account.name == asset_root_name
    }

    def is_descendant_of_asset_root(account: AccountDTO) -> bool:
        cursor = account
        seen: set[str] = set()
        while cursor.guid not in seen:
            seen.add(cursor.guid)
            if cursor.guid in root_guids:
                return True
            if not cursor.parent_guid:
                return False
            parent = accounts_by_guid.get(cursor.parent_guid)
            if parent is None:
                return False
            cursor = parent
        return False

    options: list[CashflowAssetAccountOption] = []
    for account in accounts:
        if account.guid in root_guids:
            continue
        if not is_descendant_of_asset_root(account):
            continue
        parts = full_name_by_guid.get(account.guid, account.name).split(":")
        if asset_root_name in parts:
            idx = parts.index(asset_root_name)
            display_name = ":".join(parts[idx:])
        else:
            display_name = full_name_by_guid.get(account.guid, account.name)
        options.append(
            CashflowAssetAccountOption(
                guid=account.guid,
                display_name=display_name,
            )
        )

    options.sort(key=lambda opt: (opt.display_name, opt.guid))

    excluded_prefixes = (
        f"{asset_root_name}:Créances",
        f"{asset_root_name}:Investissements",
    )
    default_selected_guids: list[str] = []
    for option in options:
        if any(
            option.display_name == excluded_prefix
            or option.display_name.startswith(f"{excluded_prefix}:")
            for excluded_prefix in excluded_prefixes
        ):
            continue
        default_selected_guids.append(option.guid)

    return CashflowAssetSelection(
        asset_root_name=asset_root_name,
        options=tuple(options),
        default_selected_guids=tuple(default_selected_guids),
    )


class GetCashflowAssetSelectionUseCase:
    """Fetch accounts tree and build cashflow asset selection options."""

    def __init__(self, repository: AccountsTreeRepositoryPort) -> None:
        """Initialize the use case with its required dependencies."""
        self._repository = repository

    def execute(self, *, asset_root_name: str = "Actif") -> CashflowAssetSelection:
        """Return selectable asset accounts and default selection.

        Args:
            asset_root_name: Root account name identifying assets ("Actif").

        Returns:
            CashflowAssetSelection: Options + default selection.
        """
        accounts = GetAccountsTreeUseCase(repository=self._repository).execute()
        return build_cashflow_asset_selection(
            accounts,
            asset_root_name=asset_root_name,
        )


__all__ = [
    "CashflowAssetAccountOption",
    "CashflowAssetSelection",
    "GetCashflowAssetSelectionUseCase",
    "build_cashflow_asset_selection",
]
