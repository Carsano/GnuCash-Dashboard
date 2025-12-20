"""Use case to compute net worth from the GnuCash database."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable

from sqlalchemy import text

from src.application.ports.database import DatabaseEnginePort
from src.infrastructure.logging.logger import get_app_logger


DEFAULT_ASSET_TYPES = (
    "ASSET",
    "BANK",
    "CASH",
    "STOCK",
    "MUTUAL",
    "RECEIVABLE",
)
DEFAULT_LIABILITY_TYPES = (
    "LIABILITY",
    "CREDIT",
    "PAYABLE",
)


@dataclass(frozen=True)
class NetWorthSummary:
    """Summary of net worth figures.

    Attributes:
        asset_total: Sum of asset balances.
        liability_total: Sum of liability balances.
        net_worth: Assets minus liabilities.
    """

    asset_total: Decimal
    liability_total: Decimal
    net_worth: Decimal


class GetNetWorthSummaryUseCase:
    """Compute net worth from the GnuCash database."""

    def __init__(
        self,
        db_port: DatabaseEnginePort,
        logger=None,
        asset_types: Iterable[str] | None = None,
        liability_types: Iterable[str] | None = None,
    ) -> None:
        """Initialize the use case.

        Args:
            db_port: Port providing access to the GnuCash engine.
            logger: Optional logger compatible with logging.Logger-like API.
            asset_types: Optional iterable of account types treated as assets.
            liability_types: Optional iterable treated as liabilities.
        """
        self._db_port = db_port
        self._logger = logger or get_app_logger()
        self._asset_types = tuple(asset_types or DEFAULT_ASSET_TYPES)
        self._liability_types = tuple(
            liability_types or DEFAULT_LIABILITY_TYPES
        )

    def execute(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> NetWorthSummary:
        """Return the net worth summary.

        Args:
            start_date: Optional lower bound for transaction post dates.
            end_date: Optional upper bound for transaction post dates.

        Returns:
            NetWorthSummary: Computed asset, liability, and net worth totals.
        """
        query = self._build_query(start_date, end_date)

        engine = self._db_port.get_gnucash_engine()
        with engine.connect() as conn:
            rows = conn.execute(query, self._build_params(start_date, end_date)).all()

        totals = {
            row.account_type: self._coerce_decimal(row.balance) for row in rows
        }

        asset_total = sum(
            (
                totals.get(account_type, Decimal("0"))
                for account_type in self._asset_types
            ),
            Decimal("0"),
        )
        liability_total = sum(
            (
                abs(totals.get(account_type, Decimal("0")))
                for account_type in self._liability_types
            ),
            Decimal("0"),
        )
        net_worth = asset_total - liability_total

        self._logger.info(
            f"Net worth computed: assets={asset_total}, "
            f"liabilities={liability_total}"
        )

        return NetWorthSummary(
            asset_total=asset_total,
            liability_total=liability_total,
            net_worth=net_worth,
        )

    @staticmethod
    def _coerce_decimal(value) -> Decimal:
        """Normalize numeric values to Decimal.

        Args:
            value: Raw numeric value from SQL.

        Returns:
            Decimal: Normalized numeric value.
        """
        if value is None:
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    @staticmethod
    def _build_query(
        start_date: date | None,
        end_date: date | None,
    ):
        base_sql = """
        SELECT a.account_type AS account_type,
               SUM(CAST(s.value_num AS NUMERIC) / NULLIF(s.value_denom, 0))
               AS balance
        FROM accounts a
        JOIN splits s ON s.account_guid = a.guid
        JOIN transactions t ON t.guid = s.tx_guid
        WHERE 1=1
        """
        if start_date:
            base_sql += " AND t.post_date >= :start_date"
        if end_date:
            base_sql += " AND t.post_date <= :end_date"
        base_sql += " GROUP BY a.account_type"
        return text(base_sql)

    @staticmethod
    def _build_params(
        start_date: date | None,
        end_date: date | None,
    ) -> dict[str, date]:
        params: dict[str, date] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return params


__all__ = ["GetNetWorthSummaryUseCase", "NetWorthSummary"]
