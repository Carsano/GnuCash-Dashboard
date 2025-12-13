"""Database infrastructure for the GnuCash dashboard.

This module exposes concrete helpers to create and reuse SQLAlchemy engines
connected to the GnuCash and analytics databases. It belongs to the
infrastructure layer because it deals with external systems (PostgreSQL).
"""

import os
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

from application.ports.database import DatabaseEnginePort


def _get_env_var(name: str) -> str:
    """Read an environment variable or raise a descriptive error.

    Args:
        name: Name of the environment variable to read.

    Returns:
        str: The raw value of the environment variable.

    Raises:
        RuntimeError: If the environment variable is missing or empty.
    """
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def _create_engine(db_url: str) -> Engine:
    """Create a configured SQLAlchemy engine for a PostgreSQL database.

    Args:
        db_url: Fully qualified database URL (including driver and credentials)

    Returns:
        Engine: A SQLAlchemy engine instance with a small connection pool and
        health checks enabled.
    """
    return create_engine(
        db_url,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
        future=True,
    )


_gnucash_engine: Optional[Engine] = None
_analytics_engine: Optional[Engine] = None


def get_gnucash_engine() -> Engine:
    """Get a singleton SQLAlchemy engine for the GnuCash database.

    Returns:
        Engine: Lazily initialized engine connected to the GnuCash backend.
    """
    global _gnucash_engine
    if _gnucash_engine is None:
        db_url = _get_env_var("GNUCASH_DB_URL")
        _gnucash_engine = _create_engine(db_url)
    return _gnucash_engine


def get_analytics_engine() -> Engine:
    """Get a singleton SQLAlchemy engine for the analytics database or schema.

    Returns:
        Engine: Lazily initialized engine connected to the analytics layer.
    """
    global _analytics_engine
    if _analytics_engine is None:
        db_url = _get_env_var("ANALYTICS_DB_URL")
        _analytics_engine = _create_engine(db_url)
    return _analytics_engine


class SqlAlchemyDatabaseEngineAdapter(DatabaseEnginePort):
    """DatabaseEnginePort implementation backed by SQLAlchemy engines.

    The adapter hides configuration details (environment variables, pooling)
    behind the port so application use cases can depend only on the protocol.
    """

    def get_gnucash_engine(self) -> Engine:
        """Get the engine for the GnuCash database.

        Returns:
            Engine: SQLAlchemy engine connected to GnuCash.
        """
        return get_gnucash_engine()

    def get_analytics_engine(self) -> Engine:
        """Get the engine for the analytics database.

        Returns:
            Engine: SQLAlchemy engine connected to the analytics layer.
        """
        return get_analytics_engine()


__all__ = [
    "get_gnucash_engine",
    "get_analytics_engine",
    "SqlAlchemyDatabaseEngineAdapter",
]
