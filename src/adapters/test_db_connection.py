"""Simple CLI to validate database connections.

This adapter is meant for local operations: it instantiates the concrete
database adapter from the infrastructure layer and runs a basic health
check against both GnuCash and analytics databases.
"""

from src.infrastructure.db import SqlAlchemyDatabaseEngineAdapter
from src.infrastructure.logging.logger import get_app_logger


def main() -> None:
    """Run basic connectivity checks against configured databases."""
    adapter = SqlAlchemyDatabaseEngineAdapter()
    logger = get_app_logger()

    gnucash_engine = adapter.get_gnucash_engine()
    analytics_engine = adapter.get_analytics_engine()

    logger.info(f"GnuCash DB: {gnucash_engine.url}")
    logger.info(f"Analytics DB: {analytics_engine.url}")

    with gnucash_engine.connect() as conn:
        conn.exec_driver_sql("SELECT 1")
    with analytics_engine.connect() as conn:
        conn.exec_driver_sql("SELECT 1")

    logger.info("Both connections are working.")


if __name__ == "__main__":
    main()
