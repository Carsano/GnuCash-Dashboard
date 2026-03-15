from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine, text

from src.application.ports.database import DatabaseEnginePort
from src.infrastructure.budget_repository import SqlAlchemyBudgetRepository
from src.domain.models.budget import BudgetInapplicableReason


def test_sqlalchemy_budget_repository_fetches_budgets_from_gnucash_engine() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE budgets (
                    guid TEXT NOT NULL,
                    name TEXT NOT NULL,
                    num_periods INTEGER NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                "INSERT INTO budgets (guid, name, num_periods) VALUES (:g, :n, :p)"
            ),
            [
                {"g": "b1", "n": "Household", "p": 12},
                {"g": "b2", "n": "Household", "p": 6},
            ],
        )

    class _FakeDbPort(DatabaseEnginePort):
        def get_gnucash_engine(self):
            return engine

        def get_analytics_engine(self):
            return engine

    repo = SqlAlchemyBudgetRepository(db_port=_FakeDbPort())
    budgets = repo.fetch_budgets()
    assert {(b.guid, b.name, b.num_periods) for b in budgets} == {
        ("b1", "Household", 12),
        ("b2", "Household", 6),
    }


def test_sqlalchemy_budget_repository_fetch_budget_applicability_out_of_range_and_no_targets_and_applicable() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE budgets (
                    guid TEXT NOT NULL,
                    name TEXT NOT NULL,
                    num_periods INTEGER NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE recurrences (
                    obj_guid TEXT NOT NULL,
                    recurrence_period_type TEXT NOT NULL,
                    recurrence_mult INTEGER NOT NULL,
                    recurrence_period_start TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE accounts (
                    guid TEXT NOT NULL,
                    account_type TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE budget_amounts (
                    budget_guid TEXT NOT NULL,
                    account_guid TEXT NOT NULL,
                    period_num INTEGER NOT NULL,
                    amount_num INTEGER NOT NULL,
                    amount_denom INTEGER NOT NULL
                )
                """
            )
        )

        conn.execute(
            text(
                "INSERT INTO budgets (guid, name, num_periods) VALUES (:g, :n, :p)"
            ),
            [{"g": "b1", "n": "Household", "p": 2}],
        )
        conn.execute(
            text(
                """
                INSERT INTO recurrences (
                    obj_guid, recurrence_period_type, recurrence_mult, recurrence_period_start
                ) VALUES (:g, :t, :m, :s)
                """
            ),
            [{"g": "b1", "t": "month", "m": 1, "s": "2026-01-01 00:00:00"}],
        )
        conn.execute(
            text(
                "INSERT INTO accounts (guid, account_type) VALUES (:g, :t)"
            ),
            [{"g": "a1", "t": "EXPENSE"}, {"g": "a2", "t": "ASSET"}],
        )
        conn.execute(
            text(
                """
                INSERT INTO budget_amounts (
                    budget_guid, account_guid, period_num, amount_num, amount_denom
                ) VALUES (:b, :a, :p, :n, :d)
                """
            ),
            [
                {
                    "b": "b1",
                    "a": "a1",
                    "p": 0,
                    "n": 100,
                    "d": 100,
                }
            ],
        )

    class _FakeDbPort(DatabaseEnginePort):
        def get_gnucash_engine(self):
            return engine

        def get_analytics_engine(self):
            return engine

    repo = SqlAlchemyBudgetRepository(db_port=_FakeDbPort())

    out_of_range = repo.fetch_budget_applicability(
        budget_guid="b1",
        month_start=date(2026, 3, 1),
    )
    assert out_of_range.applicable is False
    assert out_of_range.reason == BudgetInapplicableReason.OUT_OF_RANGE

    no_targets = repo.fetch_budget_applicability(
        budget_guid="b1",
        month_start=date(2026, 2, 1),
    )
    assert no_targets.applicable is False
    assert no_targets.reason == BudgetInapplicableReason.NO_TARGETS

    applicable = repo.fetch_budget_applicability(
        budget_guid="b1",
        month_start=date(2026, 1, 1),
    )
    assert applicable.applicable is True
    assert applicable.reason is None


def test_sqlalchemy_budget_repository_fetch_monthly_budget_targets_filters_expense_and_keeps_zero() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE budgets (
                    guid TEXT NOT NULL,
                    name TEXT NOT NULL,
                    num_periods INTEGER NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE recurrences (
                    obj_guid TEXT NOT NULL,
                    recurrence_period_type TEXT NOT NULL,
                    recurrence_mult INTEGER NOT NULL,
                    recurrence_period_start TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE accounts (
                    guid TEXT NOT NULL,
                    account_type TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE budget_amounts (
                    budget_guid TEXT NOT NULL,
                    account_guid TEXT NOT NULL,
                    period_num INTEGER NOT NULL,
                    amount_num INTEGER NOT NULL,
                    amount_denom INTEGER NOT NULL
                )
                """
            )
        )

        conn.execute(
            text(
                "INSERT INTO budgets (guid, name, num_periods) VALUES (:g, :n, :p)"
            ),
            [{"g": "b1", "n": "Household", "p": 12}],
        )
        conn.execute(
            text(
                """
                INSERT INTO recurrences (
                    obj_guid, recurrence_period_type, recurrence_mult, recurrence_period_start
                ) VALUES (:g, :t, :m, :s)
                """
            ),
            [{"g": "b1", "t": "month", "m": 1, "s": "2026-01-01"}],
        )
        conn.execute(
            text(
                "INSERT INTO accounts (guid, account_type) VALUES (:g, :t)"
            ),
            [
                {"g": "a-exp-2", "t": "EXPENSE"},
                {"g": "a-exp-1", "t": "EXPENSE"},
                {"g": "a-asset-1", "t": "ASSET"},
            ],
        )
        conn.execute(
            text(
                """
                INSERT INTO budget_amounts (
                    budget_guid, account_guid, period_num, amount_num, amount_denom
                ) VALUES (:b, :a, :p, :n, :d)
                """
            ),
            [
                {"b": "b1", "a": "a-exp-2", "p": 1, "n": 0, "d": 100},
                {"b": "b1", "a": "a-exp-1", "p": 1, "n": -2500, "d": 100},
                {"b": "b1", "a": "a-asset-1", "p": 1, "n": 999, "d": 100},
                {"b": "b1", "a": "a-exp-1", "p": 0, "n": 1200, "d": 100},
            ],
        )

    class _FakeDbPort(DatabaseEnginePort):
        def get_gnucash_engine(self):
            return engine

        def get_analytics_engine(self):
            return engine

    repo = SqlAlchemyBudgetRepository(db_port=_FakeDbPort())
    results = repo.fetch_monthly_budget_targets(
        budget_guid="b1",
        month_start=date(2026, 2, 15),
    )

    assert [(row.account_guid, row.amount) for row in results] == [
        ("a-exp-1", -25),
        ("a-exp-2", 0),
    ]


def test_sqlalchemy_budget_repository_fetch_monthly_budget_targets_returns_empty_when_out_of_range() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE budgets (
                    guid TEXT NOT NULL,
                    name TEXT NOT NULL,
                    num_periods INTEGER NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE recurrences (
                    obj_guid TEXT NOT NULL,
                    recurrence_period_type TEXT NOT NULL,
                    recurrence_mult INTEGER NOT NULL,
                    recurrence_period_start TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE accounts (
                    guid TEXT NOT NULL,
                    account_type TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE budget_amounts (
                    budget_guid TEXT NOT NULL,
                    account_guid TEXT NOT NULL,
                    period_num INTEGER NOT NULL,
                    amount_num INTEGER NOT NULL,
                    amount_denom INTEGER NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                "INSERT INTO budgets (guid, name, num_periods) VALUES (:g, :n, :p)"
            ),
            [{"g": "b1", "n": "Short", "p": 1}],
        )
        conn.execute(
            text(
                """
                INSERT INTO recurrences (
                    obj_guid, recurrence_period_type, recurrence_mult, recurrence_period_start
                ) VALUES (:g, :t, :m, :s)
                """
            ),
            [{"g": "b1", "t": "month", "m": 1, "s": "2026-01-01"}],
        )

    class _FakeDbPort(DatabaseEnginePort):
        def get_gnucash_engine(self):
            return engine

        def get_analytics_engine(self):
            return engine

    repo = SqlAlchemyBudgetRepository(db_port=_FakeDbPort())
    results = repo.fetch_monthly_budget_targets(
        budget_guid="b1",
        month_start=date(2026, 2, 1),
    )
    assert results == []


def test_sqlalchemy_budget_repository_fetch_monthly_budget_targets_uses_earliest_monthly_recurrence() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE budgets (
                    guid TEXT NOT NULL,
                    name TEXT NOT NULL,
                    num_periods INTEGER NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE recurrences (
                    obj_guid TEXT NOT NULL,
                    recurrence_period_type TEXT NOT NULL,
                    recurrence_mult INTEGER NOT NULL,
                    recurrence_period_start TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE accounts (
                    guid TEXT NOT NULL,
                    account_type TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE budget_amounts (
                    budget_guid TEXT NOT NULL,
                    account_guid TEXT NOT NULL,
                    period_num INTEGER NOT NULL,
                    amount_num INTEGER NOT NULL,
                    amount_denom INTEGER NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                "INSERT INTO budgets (guid, name, num_periods) VALUES (:g, :n, :p)"
            ),
            [{"g": "b1", "n": "Household", "p": 24}],
        )
        conn.execute(
            text(
                """
                INSERT INTO recurrences (
                    obj_guid, recurrence_period_type, recurrence_mult, recurrence_period_start
                ) VALUES (:g, :t, :m, :s)
                """
            ),
            [
                {"g": "b1", "t": "month", "m": 1, "s": "2026-03-01"},
                {"g": "b1", "t": "month", "m": 1, "s": "2026-01-01"},
            ],
        )
        conn.execute(
            text(
                "INSERT INTO accounts (guid, account_type) VALUES (:g, :t)"
            ),
            [{"g": "a-exp-1", "t": "EXPENSE"}],
        )
        conn.execute(
            text(
                """
                INSERT INTO budget_amounts (
                    budget_guid, account_guid, period_num, amount_num, amount_denom
                ) VALUES (:b, :a, :p, :n, :d)
                """
            ),
            [
                {"b": "b1", "a": "a-exp-1", "p": 0, "n": 1000, "d": 100},
                {"b": "b1", "a": "a-exp-1", "p": 2, "n": 2000, "d": 100},
            ],
        )

    class _FakeDbPort(DatabaseEnginePort):
        def get_gnucash_engine(self):
            return engine

        def get_analytics_engine(self):
            return engine

    repo = SqlAlchemyBudgetRepository(db_port=_FakeDbPort())
    results = repo.fetch_monthly_budget_targets(
        budget_guid="b1",
        month_start=date(2026, 3, 1),
    )
    assert [(row.account_guid, row.amount) for row in results] == [
        ("a-exp-1", 20),
    ]


def test_sqlalchemy_budget_repository_fetch_monthly_budget_targets_raises_on_zero_denominator() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE budgets (
                    guid TEXT NOT NULL,
                    name TEXT NOT NULL,
                    num_periods INTEGER NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE recurrences (
                    obj_guid TEXT NOT NULL,
                    recurrence_period_type TEXT NOT NULL,
                    recurrence_mult INTEGER NOT NULL,
                    recurrence_period_start TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE accounts (
                    guid TEXT NOT NULL,
                    account_type TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE budget_amounts (
                    budget_guid TEXT NOT NULL,
                    account_guid TEXT NOT NULL,
                    period_num INTEGER NOT NULL,
                    amount_num INTEGER NOT NULL,
                    amount_denom INTEGER NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                "INSERT INTO budgets (guid, name, num_periods) VALUES (:g, :n, :p)"
            ),
            [{"g": "b1", "n": "Household", "p": 12}],
        )
        conn.execute(
            text(
                """
                INSERT INTO recurrences (
                    obj_guid, recurrence_period_type, recurrence_mult, recurrence_period_start
                ) VALUES (:g, :t, :m, :s)
                """
            ),
            [{"g": "b1", "t": "month", "m": 1, "s": "2026-01-01"}],
        )
        conn.execute(
            text(
                "INSERT INTO accounts (guid, account_type) VALUES (:g, :t)"
            ),
            [{"g": "a-exp-1", "t": "EXPENSE"}],
        )
        conn.execute(
            text(
                """
                INSERT INTO budget_amounts (
                    budget_guid, account_guid, period_num, amount_num, amount_denom
                ) VALUES (:b, :a, :p, :n, :d)
                """
            ),
            [{"b": "b1", "a": "a-exp-1", "p": 0, "n": 1000, "d": 0}],
        )

    class _FakeDbPort(DatabaseEnginePort):
        def get_gnucash_engine(self):
            return engine

        def get_analytics_engine(self):
            return engine

    repo = SqlAlchemyBudgetRepository(db_port=_FakeDbPort())
    try:
        repo.fetch_monthly_budget_targets(
            budget_guid="b1",
            month_start=date(2026, 1, 1),
        )
        assert False, "Expected ValueError when amount_denom=0"
    except ValueError as exc:
        assert "amount_denom=0" in str(exc)


def test_sqlalchemy_budget_repository_fetch_monthly_actuals_by_account_filters_month_expense_and_normalizes_sign() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE accounts (
                    guid TEXT NOT NULL,
                    account_type TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE transactions (
                    guid TEXT NOT NULL,
                    post_date DATE NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE splits (
                    guid TEXT NOT NULL,
                    account_guid TEXT NOT NULL,
                    tx_guid TEXT NOT NULL,
                    value_num NUMERIC NOT NULL,
                    value_denom NUMERIC NOT NULL
                )
                """
            )
        )

        conn.execute(
            text("INSERT INTO accounts (guid, account_type) VALUES (:g, :t)"),
            [
                {"g": "a-exp-2", "t": "EXPENSE"},
                {"g": "a-exp-1", "t": "EXPENSE"},
                {"g": "a-asset-1", "t": "ASSET"},
            ],
        )
        conn.execute(
            text("INSERT INTO transactions (guid, post_date) VALUES (:g, :d)"),
            [
                {"g": "tx-in-1", "d": "2026-02-01"},
                {"g": "tx-in-2", "d": "2026-02-10"},
                {"g": "tx-out", "d": "2026-03-01"},
            ],
        )
        conn.execute(
            text(
                """
                INSERT INTO splits (
                    guid, account_guid, tx_guid, value_num, value_denom
                ) VALUES (:g, :a, :t, :n, :d)
                """
            ),
            [
                # expense entries in-range, negative convention
                {
                    "g": "s1",
                    "a": "a-exp-1",
                    "t": "tx-in-1",
                    "n": -5000,
                    "d": 100,
                },
                {
                    "g": "s2",
                    "a": "a-exp-2",
                    "t": "tx-in-2",
                    "n": -700,
                    "d": 100,
                },
                # out-of-range should be excluded
                {
                    "g": "s3",
                    "a": "a-exp-1",
                    "t": "tx-out",
                    "n": -1000,
                    "d": 100,
                },
                # non-expense should be excluded
                {
                    "g": "s4",
                    "a": "a-asset-1",
                    "t": "tx-in-1",
                    "n": -2000,
                    "d": 100,
                },
            ],
        )

    class _FakeDbPort(DatabaseEnginePort):
        def get_gnucash_engine(self):
            return engine

        def get_analytics_engine(self):
            return engine

    repo = SqlAlchemyBudgetRepository(db_port=_FakeDbPort())
    results = repo.fetch_monthly_actuals_by_account(month_start=date(2026, 2, 21))

    assert [(row.account_guid, row.amount) for row in results] == [
        ("a-exp-1", Decimal("50")),
        ("a-exp-2", Decimal("7")),
    ]


def test_sqlalchemy_budget_repository_fetch_monthly_actuals_by_account_returns_empty_without_rows() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE accounts (
                    guid TEXT NOT NULL,
                    account_type TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE transactions (
                    guid TEXT NOT NULL,
                    post_date DATE NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE splits (
                    guid TEXT NOT NULL,
                    account_guid TEXT NOT NULL,
                    tx_guid TEXT NOT NULL,
                    value_num NUMERIC NOT NULL,
                    value_denom NUMERIC NOT NULL
                )
                """
            )
        )

    class _FakeDbPort(DatabaseEnginePort):
        def get_gnucash_engine(self):
            return engine

        def get_analytics_engine(self):
            return engine

    repo = SqlAlchemyBudgetRepository(db_port=_FakeDbPort())
    results = repo.fetch_monthly_actuals_by_account(month_start=date(2026, 2, 1))
    assert results == []


def test_sqlalchemy_budget_repository_fetch_monthly_actuals_by_account_reads_from_analytics_engine() -> None:
    gnucash_engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    analytics_engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

    with gnucash_engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE accounts (
                    guid TEXT NOT NULL,
                    account_type TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE transactions (
                    guid TEXT NOT NULL,
                    post_date DATE NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE splits (
                    guid TEXT NOT NULL,
                    account_guid TEXT NOT NULL,
                    tx_guid TEXT NOT NULL,
                    value_num NUMERIC NOT NULL,
                    value_denom NUMERIC NOT NULL
                )
                """
            )
        )

    with analytics_engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE accounts (
                    guid TEXT NOT NULL,
                    account_type TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE transactions (
                    guid TEXT NOT NULL,
                    post_date DATE NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE splits (
                    guid TEXT NOT NULL,
                    account_guid TEXT NOT NULL,
                    tx_guid TEXT NOT NULL,
                    value_num NUMERIC NOT NULL,
                    value_denom NUMERIC NOT NULL
                )
                """
            )
        )
        conn.execute(
            text("INSERT INTO accounts (guid, account_type) VALUES (:g, :t)"),
            [{"g": "a-exp-1", "t": "EXPENSE"}],
        )
        conn.execute(
            text("INSERT INTO transactions (guid, post_date) VALUES (:g, :d)"),
            [{"g": "tx-1", "d": "2026-02-05"}],
        )
        conn.execute(
            text(
                """
                INSERT INTO splits (
                    guid, account_guid, tx_guid, value_num, value_denom
                ) VALUES (:g, :a, :t, :n, :d)
                """
            ),
            [{"g": "s1", "a": "a-exp-1", "t": "tx-1", "n": -3300, "d": 100}],
        )

    class _FakeDbPort(DatabaseEnginePort):
        def get_gnucash_engine(self):
            return gnucash_engine

        def get_analytics_engine(self):
            return analytics_engine

    repo = SqlAlchemyBudgetRepository(db_port=_FakeDbPort())
    results = repo.fetch_monthly_actuals_by_account(month_start=date(2026, 2, 1))
    assert [(row.account_guid, row.amount) for row in results] == [
        ("a-exp-1", Decimal("33")),
    ]


def test_sqlalchemy_budget_repository_fetch_monthly_actuals_by_account_raises_on_zero_denominator() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE accounts (
                    guid TEXT NOT NULL,
                    account_type TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE transactions (
                    guid TEXT NOT NULL,
                    post_date DATE NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE splits (
                    guid TEXT NOT NULL,
                    account_guid TEXT NOT NULL,
                    tx_guid TEXT NOT NULL,
                    value_num NUMERIC NOT NULL,
                    value_denom NUMERIC NOT NULL
                )
                """
            )
        )
        conn.execute(
            text("INSERT INTO accounts (guid, account_type) VALUES (:g, :t)"),
            [{"g": "a-exp-1", "t": "EXPENSE"}],
        )
        conn.execute(
            text("INSERT INTO transactions (guid, post_date) VALUES (:g, :d)"),
            [{"g": "tx-1", "d": "2026-02-05"}],
        )
        conn.execute(
            text(
                """
                INSERT INTO splits (
                    guid, account_guid, tx_guid, value_num, value_denom
                ) VALUES (:g, :a, :t, :n, :d)
                """
            ),
            [{"g": "s1", "a": "a-exp-1", "t": "tx-1", "n": -3300, "d": 0}],
        )

    class _FakeDbPort(DatabaseEnginePort):
        def get_gnucash_engine(self):
            return engine

        def get_analytics_engine(self):
            return engine

    repo = SqlAlchemyBudgetRepository(db_port=_FakeDbPort())
    try:
        repo.fetch_monthly_actuals_by_account(month_start=date(2026, 2, 1))
        assert False, "Expected ValueError when value_denom=0"
    except ValueError as exc:
        assert "value_denom=0" in str(exc)
