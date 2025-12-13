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

    print("GnuCash DB:", gnucash_engine.url)

    with gnucash_engine.connect() as conn:
        conn.exec_driver_sql("SELECT 1")

    print("GNUCash connection is working.")


if __name__ == "__main__":
    main()
