"""SQLAlchemy-backed repository for GnuCash budgets."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import text

from src.application.ports.budget_repository import (
    BudgetsUnsupportedBackendError,
)
from src.application.ports.budget_repository import BudgetRepositoryPort
from src.application.ports.database import DatabaseEnginePort
from src.domain.models.budget import (
    AccountMonthlyActualDTO,
    BudgetApplicabilityDTO,
    BudgetAccountMonthlyTargetDTO,
    BudgetDTO,
    BudgetInapplicableReason,
)


def _months_between(*, start: date, end: date) -> int:
    """Return whole-month distance between two dates (end - start)."""

    return (end.year - start.year) * 12 + (end.month - start.month)


def _coerce_to_month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def _next_month_start(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def _parse_recurrence_period_start(raw_value: object) -> date:
    if isinstance(raw_value, datetime):
        return _coerce_to_month_start(raw_value.date())
    if isinstance(raw_value, date):
        return _coerce_to_month_start(raw_value)
    as_str = str(raw_value)
    if len(as_str) >= 10:
        return _coerce_to_month_start(date.fromisoformat(as_str[:10]))
    return _coerce_to_month_start(date.fromisoformat(as_str))


class SqlAlchemyBudgetRepository(BudgetRepositoryPort):
    """Repository backed by SQLAlchemy for GnuCash budgets."""

    def __init__(self, db_port: DatabaseEnginePort) -> None:
        self._db_port = db_port

    def fetch_budgets(self) -> list[BudgetDTO]:
        query = text(
            """
            SELECT guid, name, num_periods
            FROM budgets
            """
        )
        gnucash_engine = self._db_port.get_gnucash_engine()
        with gnucash_engine.connect() as conn:
            rows = conn.execute(query).all()
        return [
            BudgetDTO(
                guid=row.guid,
                name=row.name,
                num_periods=row.num_periods,
            )
            for row in rows
        ]

    def fetch_monthly_budget_targets(
        self,
        *,
        budget_guid: str,
        month_start: date,
    ) -> list[BudgetAccountMonthlyTargetDTO]:
        normalized_month_start = _coerce_to_month_start(month_start)
        meta_query = text(
            """
            SELECT guid, num_periods
            FROM budgets
            WHERE guid = :budget_guid
            """
        )
        recurrence_query = text(
            """
            SELECT recurrence_period_start
            FROM recurrences
            WHERE obj_guid = :budget_guid
              AND recurrence_period_type = 'month'
              AND recurrence_mult = 1
            ORDER BY recurrence_period_start ASC
            LIMIT 1
            """
        )
        targets_query = text(
            """
            SELECT
                ba.account_guid,
                ba.amount_num,
                ba.amount_denom
            FROM budget_amounts ba
            JOIN accounts a ON a.guid = ba.account_guid
            WHERE ba.budget_guid = :budget_guid
              AND ba.period_num = :period_num
              AND a.account_type = 'EXPENSE'
            ORDER BY ba.account_guid
            """
        )

        gnucash_engine = self._db_port.get_gnucash_engine()
        with gnucash_engine.connect() as conn:
            budget_row = conn.execute(
                meta_query,
                {"budget_guid": budget_guid},
            ).first()
            if budget_row is None:
                return []

            recurrence_row = conn.execute(
                recurrence_query,
                {"budget_guid": budget_guid},
            ).first()
            if recurrence_row is None:
                return []

            recurrence_start = _parse_recurrence_period_start(
                recurrence_row.recurrence_period_start
            )
            period_num = _months_between(
                start=recurrence_start,
                end=normalized_month_start,
            )
            if period_num < 0 or period_num >= int(budget_row.num_periods):
                return []

            rows = conn.execute(
                targets_query,
                {"budget_guid": budget_guid, "period_num": period_num},
            ).all()

        totals_by_account: dict[str, Decimal] = {}
        for row in rows:
            denominator = Decimal(row.amount_denom)
            if denominator == Decimal("0"):
                raise ValueError(
                    "Invalid budget_amounts row with amount_denom=0 "
                    f"for budget_guid={budget_guid}, "
                    f"account_guid={row.account_guid}, period_num={period_num}."
                )
            amount = Decimal(row.amount_num) / denominator
            account_guid = str(row.account_guid)
            totals_by_account[account_guid] = (
                totals_by_account.get(account_guid, Decimal("0")) + amount
            )

        return [
            BudgetAccountMonthlyTargetDTO(
                account_guid=account_guid,
                amount=totals_by_account[account_guid],
            )
            for account_guid in sorted(totals_by_account.keys())
        ]

    def fetch_monthly_actuals_by_account(
        self,
        *,
        month_start: date,
    ) -> list[AccountMonthlyActualDTO]:
        normalized_month_start = _coerce_to_month_start(month_start)
        next_month_start = _next_month_start(normalized_month_start)
        actuals_query = text(
            """
            SELECT
                s.account_guid,
                s.value_num,
                s.value_denom
            FROM splits s
            JOIN transactions t ON t.guid = s.tx_guid
            JOIN accounts a ON a.guid = s.account_guid
            WHERE a.account_type = 'EXPENSE'
              AND t.post_date >= :month_start
              AND t.post_date < :next_month_start
            ORDER BY s.account_guid, s.guid
            """
        )
        analytics_engine = self._db_port.get_analytics_engine()
        with analytics_engine.connect() as conn:
            rows = conn.execute(
                actuals_query,
                {
                    "month_start": normalized_month_start,
                    "next_month_start": next_month_start,
                },
            ).all()

        totals_by_account: dict[str, Decimal] = {}
        for row in rows:
            denominator = Decimal(row.value_denom)
            if denominator == Decimal("0"):
                raise ValueError(
                    "Invalid splits row with value_denom=0 "
                    f"for account_guid={row.account_guid}."
                )
            amount = Decimal(row.value_num) / denominator
            account_guid = str(row.account_guid)
            totals_by_account[account_guid] = (
                totals_by_account.get(account_guid, Decimal("0")) + amount
            )

        return [
            AccountMonthlyActualDTO(
                account_guid=account_guid,
                # Actual spend is exposed as positive magnitude for UI semantics.
                amount=abs(totals_by_account[account_guid]),
            )
            for account_guid in sorted(totals_by_account.keys())
        ]

    def fetch_budget_applicability(
        self,
        *,
        budget_guid: str,
        month_start: date,
    ) -> BudgetApplicabilityDTO:
        """Return whether the budget has applicable expense targets for the month."""

        normalized_month_start = _coerce_to_month_start(month_start)
        meta_query = text(
            """
            SELECT guid, num_periods
            FROM budgets
            WHERE guid = :budget_guid
            """
        )
        recurrence_query = text(
            """
            SELECT recurrence_period_start
            FROM recurrences
            WHERE obj_guid = :budget_guid
              AND recurrence_period_type = 'month'
              AND recurrence_mult = 1
            """
        )
        gnucash_engine = self._db_port.get_gnucash_engine()
        with gnucash_engine.connect() as conn:
            budget_row = conn.execute(
                meta_query,
                {"budget_guid": budget_guid},
            ).first()
            if budget_row is None:
                return BudgetApplicabilityDTO(
                    applicable=False,
                    reason=BudgetInapplicableReason.DATA_UNAVAILABLE,
                )

            recurrence_row = conn.execute(
                recurrence_query,
                {"budget_guid": budget_guid},
            ).first()
            if recurrence_row is None:
                return BudgetApplicabilityDTO(
                    applicable=False,
                    reason=BudgetInapplicableReason.DATA_UNAVAILABLE,
                )

            recurrence_start = _parse_recurrence_period_start(
                recurrence_row.recurrence_period_start
            )

            period_num = _months_between(
                start=recurrence_start,
                end=normalized_month_start,
            )
            if period_num < 0 or period_num >= int(budget_row.num_periods):
                return BudgetApplicabilityDTO(
                    applicable=False,
                    reason=BudgetInapplicableReason.OUT_OF_RANGE,
                )

            targets_count_query = text(
                """
                SELECT COUNT(*) AS cnt
                FROM budget_amounts ba
                JOIN accounts a ON a.guid = ba.account_guid
                WHERE ba.budget_guid = :budget_guid
                  AND ba.period_num = :period_num
                  AND a.account_type = 'EXPENSE'
                """
            )
            count_row = conn.execute(
                targets_count_query,
                {"budget_guid": budget_guid, "period_num": period_num},
            ).first()
            cnt = int(count_row.cnt) if count_row is not None else 0
            if cnt <= 0:
                return BudgetApplicabilityDTO(
                    applicable=False,
                    reason=BudgetInapplicableReason.NO_TARGETS,
                )

        return BudgetApplicabilityDTO(applicable=True, reason=None)


class UnsupportedBudgetRepository(BudgetRepositoryPort):
    """Repository that explains unsupported budget backends."""

    def __init__(self, *, backend: str) -> None:
        self._backend = backend

    def fetch_budgets(self) -> list[BudgetDTO]:
        raise BudgetsUnsupportedBackendError(backend=self._backend)

    def fetch_monthly_budget_targets(
        self,
        *,
        budget_guid: str,
        month_start: date,
    ) -> list[BudgetAccountMonthlyTargetDTO]:
        _ = budget_guid, month_start
        raise RuntimeError(
            "Budget targets are not available for the configured backend "
            f"(GNUCASH_BACKEND={self._backend})."
        )

    def fetch_monthly_actuals_by_account(
        self,
        *,
        month_start: date,
    ) -> list[AccountMonthlyActualDTO]:
        _ = month_start
        raise RuntimeError(
            "Budget actuals are not available for the configured backend "
            f"(GNUCASH_BACKEND={self._backend})."
        )

    def fetch_budget_applicability(
        self,
        *,
        budget_guid: str,
        month_start: date,
    ) -> BudgetApplicabilityDTO:
        _ = budget_guid, month_start
        raise BudgetsUnsupportedBackendError(backend=self._backend)


__all__ = [
    "SqlAlchemyBudgetRepository",
    "UnsupportedBudgetRepository",
]
