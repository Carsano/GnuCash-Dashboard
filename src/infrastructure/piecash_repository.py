"""PieCash-backed repository for GnuCash reporting data."""

from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from src.application.ports.gnucash_repository import (
    AssetCategoryBalanceRow,
    GnuCashRepositoryPort,
    NetWorthBalanceRow,
    PriceRow,
)
from src.infrastructure.logging.logger import get_app_logger
from src.infrastructure.piecash_compat import load_piecash, open_piecash_book
from src.utils.decimal_utils import coerce_decimal


class PieCashGnuCashRepository(GnuCashRepositoryPort):
    """Repository for PieCash-based GnuCash access."""

    def __init__(self, book_path: Path | str, logger=None) -> None:
        """Initialize the repository.

        Args:
            book_path: Path or URI to the GnuCash book supported by piecash.
            logger: Optional logger compatible with logging.Logger-like API.
        """
        try:
            self._piecash = load_piecash()
        except ImportError as exc:
            raise RuntimeError(
                "piecash is not installed; install it to use the piecash backend"
            ) from exc
        self._book_path = book_path
        self._logger = logger or get_app_logger()

    @contextmanager
    def _open_book(self):
        book = open_piecash_book(
            self._piecash,
            self._book_path,
            readonly=True,
            open_if_lock=True,
            check_exists=False,
        )
        try:
            yield book
        finally:
            close_method = getattr(book, "close", None)
            if callable(close_method):
                close_method()

    @staticmethod
    def _normalize_account_type(raw_type) -> str:
        if raw_type is None:
            return ""
        if hasattr(raw_type, "name"):
            return str(raw_type.name).upper()
        return str(raw_type).upper()

    @staticmethod
    def _coerce_date(raw_value) -> date | None:
        if raw_value is None:
            return None
        if isinstance(raw_value, date) and not isinstance(raw_value, datetime):
            return raw_value
        if isinstance(raw_value, datetime):
            return raw_value.date()
        return None

    @staticmethod
    def _numeric_to_decimal(value) -> Decimal:
        if value is None:
            return Decimal("0")
        if hasattr(value, "num") and hasattr(value, "denom"):
            denom = coerce_decimal(value.denom)
            if denom == 0:
                return Decimal("0")
            return coerce_decimal(value.num) / denom
        if hasattr(value, "numerator") and hasattr(value, "denominator"):
            denom = coerce_decimal(value.denominator)
            if denom == 0:
                return Decimal("0")
            return coerce_decimal(value.numerator) / denom
        return coerce_decimal(value)

    def _split_amount(
        self,
        split,
        namespace: str | None,
    ) -> Decimal:
        namespace_value = (namespace or "").upper()
        if namespace_value == "CURRENCY":
            numeric = getattr(split, "value", None)
            if numeric is None:
                numeric = getattr(split, "value_num", None)
            return self._numeric_to_decimal(numeric)
        numeric = getattr(split, "quantity", None)
        if numeric is None:
            numeric = getattr(split, "quantity_num", None)
        if numeric is None:
            numeric = getattr(split, "value", None)
        return self._numeric_to_decimal(numeric)

    def _extract_price_values(self, price) -> tuple[Decimal, Decimal] | None:
        if hasattr(price, "value_num") and hasattr(price, "value_denom"):
            return (
                coerce_decimal(price.value_num),
                coerce_decimal(price.value_denom),
            )
        raw_value = getattr(price, "value", None)
        if raw_value is None:
            self._logger.warning(
                "Skipping price with missing value"
            )
            return None
        if hasattr(raw_value, "num") and hasattr(raw_value, "denom"):
            return (
                coerce_decimal(raw_value.num),
                coerce_decimal(raw_value.denom),
            )
        if hasattr(raw_value, "numerator") and hasattr(raw_value, "denominator"):
            return (
                coerce_decimal(raw_value.numerator),
                coerce_decimal(raw_value.denominator),
            )
        return (coerce_decimal(raw_value), Decimal("1"))

    def fetch_currency_guid(self, currency: str) -> str:
        """Return the GUID for a currency mnemonic.

        Args:
            currency: Currency mnemonic (e.g., EUR).

        Returns:
            str: GUID for the currency.
        """
        with self._open_book() as book:
            for commodity in book.commodities:
                if (
                    commodity.mnemonic == currency
                    and commodity.namespace == "CURRENCY"
                ):
                    return commodity.guid
        raise RuntimeError(f"Missing currency in commodities: {currency}")

    def fetch_net_worth_balances(
        self,
        start_date: date | None,
        end_date: date | None,
    ) -> list[NetWorthBalanceRow]:
        """Return balances needed for net worth aggregation.

        Args:
            start_date: Optional lower bound for transaction post dates.
            end_date: Optional upper bound for transaction post dates.

        Returns:
            list[NetWorthBalanceRow]: Balances for net worth aggregation.
        """
        balances: dict[tuple[str, str | None, str | None, str | None], Decimal] = {}
        with self._open_book() as book:
            for split in book.splits:
                transaction = getattr(split, "transaction", None)
                post_date = self._coerce_date(
                    getattr(transaction, "post_date", None)
                )
                if start_date and post_date and post_date < start_date:
                    continue
                if end_date and post_date and post_date > end_date:
                    continue
                account = split.account
                commodity = getattr(account, "commodity", None)
                namespace = (
                    commodity.namespace
                    if commodity is not None
                    else None
                )
                amount = self._split_amount(split, namespace)
                account_type = self._normalize_account_type(
                    getattr(account, "type", "")
                )
                commodity_guid = (
                    commodity.guid if commodity is not None else None
                )
                mnemonic = (
                    commodity.mnemonic if commodity is not None else None
                )
                key = (
                    account_type,
                    commodity_guid,
                    mnemonic,
                    namespace,
                )
                balances[key] = balances.get(key, Decimal("0")) + amount
        rows = [
            NetWorthBalanceRow(
                account_type=account_type,
                commodity_guid=commodity_guid,
                mnemonic=mnemonic,
                namespace=namespace,
                balance=balance,
            )
            for (
                account_type,
                commodity_guid,
                mnemonic,
                namespace,
            ), balance in balances.items()
        ]
        return sorted(
            rows,
            key=lambda row: (
                row.account_type,
                row.commodity_guid or "",
                row.mnemonic or "",
                row.namespace or "",
            ),
        )

    def fetch_asset_category_balances(
        self,
        start_date: date | None,
        end_date: date | None,
        actif_root_name: str,
    ) -> list[AssetCategoryBalanceRow]:
        """Return balances grouped by asset category.

        Args:
            start_date: Optional lower bound for transaction post dates.
            end_date: Optional upper bound for transaction post dates.
            actif_root_name: Root account name for asset categories.

        Returns:
            list[AssetCategoryBalanceRow]: Balances grouped by asset categories.
        """
        balances: dict[
            tuple[str, str | None, str | None, str | None, str | None, str | None],
            Decimal,
        ] = {}
        with self._open_book() as book:
            account_map = self._build_account_tree_map(
                book,
                actif_root_name,
            )
            if not account_map:
                return []
            for split in book.splits:
                account = split.account
                category_info = account_map.get(account.guid)
                if category_info is None:
                    continue
                transaction = getattr(split, "transaction", None)
                post_date = self._coerce_date(
                    getattr(transaction, "post_date", None)
                )
                if start_date and post_date and post_date < start_date:
                    continue
                if end_date and post_date and post_date > end_date:
                    continue
                commodity = getattr(account, "commodity", None)
                namespace = (
                    commodity.namespace
                    if commodity is not None
                    else None
                )
                amount = self._split_amount(split, namespace)
                account_type = self._normalize_account_type(
                    getattr(account, "type", "")
                )
                commodity_guid = (
                    commodity.guid if commodity is not None else None
                )
                mnemonic = (
                    commodity.mnemonic if commodity is not None else None
                )
                actif_category, actif_subcategory = category_info
                key = (
                    account_type,
                    commodity_guid,
                    mnemonic,
                    namespace,
                    actif_category,
                    actif_subcategory,
                )
                balances[key] = balances.get(key, Decimal("0")) + amount
        rows = [
            AssetCategoryBalanceRow(
                account_type=account_type,
                commodity_guid=commodity_guid,
                mnemonic=mnemonic,
                namespace=namespace,
                actif_category=actif_category,
                actif_subcategory=actif_subcategory,
                balance=balance,
            )
            for (
                account_type,
                commodity_guid,
                mnemonic,
                namespace,
                actif_category,
                actif_subcategory,
            ), balance in balances.items()
        ]
        return sorted(
            rows,
            key=lambda row: (
                row.actif_category or "",
                row.actif_subcategory or "",
                row.account_type,
                row.commodity_guid or "",
                row.mnemonic or "",
                row.namespace or "",
            ),
        )

    def fetch_latest_prices(
        self,
        currency_guid: str,
        end_date: date | None,
    ) -> list[PriceRow]:
        """Return the latest price rows per commodity.

        Args:
            currency_guid: GUID for the target currency.
            end_date: Optional upper bound for price dates.

        Returns:
            list[PriceRow]: Latest price rows per commodity.
        """
        rows: list[PriceRow] = []
        with self._open_book() as book:
            for price in book.prices:
                currency = getattr(price, "currency", None)
                if currency is None or currency.guid != currency_guid:
                    continue
                price_date = self._coerce_date(getattr(price, "date", None))
                if end_date and price_date and price_date > end_date:
                    continue
                commodity = getattr(price, "commodity", None)
                if commodity is None:
                    continue
                values = self._extract_price_values(price)
                if values is None:
                    continue
                value_num, value_denom = values
                rows.append(
                    PriceRow(
                        commodity_guid=commodity.guid,
                        value_num=value_num,
                        value_denom=value_denom,
                        date=price_date or date.min,
                    )
                )
        return sorted(
            rows,
            key=lambda row: (row.commodity_guid, row.date),
            reverse=True,
        )

    def _build_account_tree_map(
        self,
        book,
        actif_root_name: str,
    ) -> dict[str, tuple[str | None, str | None]]:
        root_account = None
        for account in book.accounts:
            if account.name == actif_root_name:
                root_account = account
                break
        if root_account is None:
            self._logger.warning(
                f"Missing root account named {actif_root_name}"
            )
            return {}
        mapping: dict[str, tuple[str | None, str | None]] = {}
        for account in book.accounts:
            if account.guid == root_account.guid:
                continue
            path = []
            current = account
            while current and current.guid != root_account.guid:
                path.append(current)
                current = getattr(current, "parent", None)
            if not current or current.guid != root_account.guid:
                continue
            path = list(reversed(path))
            if not path:
                continue
            top_child = path[0].name
            second_child = path[1].name if len(path) > 1 else None
            mapping[account.guid] = (top_child, second_child)
        return mapping


__all__ = ["PieCashGnuCashRepository"]
