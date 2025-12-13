"""Simple CLI to validate database connections.

This adapter is meant for local operations: it instantiates the concrete
database adapter from the infrastructure layer and runs a basic health
check against both GnuCash and analytics databases.
"""

from src.infrastructure.db import SqlAlchemyDatabaseEngineAdapter


def main() -> None:
    """Run basic connectivity checks against configured databases."""
    adapter = SqlAlchemyDatabaseEngineAdapter()

    gnucash_engine = adapter.get_gnucash_engine()
    analytics_engine = adapter.get_analytics_engine()

    print("GnuCash DB:", gnucash_engine.url)
    print("Analytics DB:", analytics_engine.url)

    with gnucash_engine.connect() as conn:
        conn.exec_driver_sql("SELECT 1")
    with analytics_engine.connect() as conn:
        conn.exec_driver_sql("SELECT 1")

    print("Both connections are working.")


if __name__ == "__main__":
    main()
