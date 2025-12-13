"""Database ports for the GnuCash dashboard.

This module defines the application-layer protocols for accessing database
engines. Infrastructure implementations are expected to provide concrete
adapters that satisfy these ports.
"""

from typing import Protocol

from sqlalchemy.engine import Engine


class DatabaseEnginePort(Protocol):
    """Port exposing database engines for GnuCash and analytics.

    Application use cases can depend on this protocol instead of concrete
    database drivers or configuration details.
    """

    def get_gnucash_engine(self) -> Engine:
        """Get the engine for the GnuCash database.

        Returns:
            Engine: SQLAlchemy engine connected to the GnuCash backend.
        """

    def get_analytics_engine(self) -> Engine:
        """Get the engine for the analytics database.

        Returns:
            Engine: SQLAlchemy engine connected to the analytics layer.
        """


__all__ = ["DatabaseEnginePort"]
