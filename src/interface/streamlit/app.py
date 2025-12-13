"""Streamlit dashboard entry point."""

from collections.abc import Sequence

import streamlit as st

from src.application.use_cases.get_accounts import (
    AccountDTO,
    GetAccountsUseCase
)
from src.infrastructure.db import SqlAlchemyDatabaseEngineAdapter


@st.cache_data(show_spinner=False)
def _load_accounts() -> Sequence[AccountDTO]:
    """Fetch accounts using the analytics database."""
    adapter = SqlAlchemyDatabaseEngineAdapter()
    use_case = GetAccountsUseCase(db_port=adapter)
    return use_case.execute()


def main() -> None:
    """Render the Streamlit app."""
    st.set_page_config(page_title="GnuCash Dashboard", layout="wide")
    st.title("GnuCash Accounts Overview")

    accounts = _load_accounts()
    st.caption(f"{len(accounts)} accounts synced from analytics.accounts_dim")

    if not accounts:
        st.warning("No accounts found. Run the sync first.")
        return

    data = [
        {
            "GUID": acc.guid,
            "Name": acc.name,
            "Type": acc.account_type,
            "Commodity": acc.commodity_guid,
            "Parent": acc.parent_guid,
        }
        for acc in accounts
    ]

    st.dataframe(data, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
