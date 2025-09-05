"""
Database management for the Japanese Learning Telegram Bot.

This module handles database initialization, connection management,
and provides the base for all database operations using SQLAlchemy.
"""

import logging
from pathlib import Path
from typing import Optional, Any
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool


logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, database_url: str):
        """Initialize the database manager.

        Args:
            database_url: Database connection string
        """
        self.database_url = database_url
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    async def init_database(self) -> None:
        """Initialize the database connection and create tables."""
        logger.info(f"Initializing database connection to: {self._safe_url}")

        # Configure engine based on database type
        if self.database_url.startswith("sqlite"):
            # SQLite configuration
            engine_kwargs = {
                "echo": False,
                "poolclass": StaticPool,
                "connect_args": {
                    "check_same_thread": False,
                },
            }

            # Ensure directory exists for SQLite database
            if "///" in self.database_url:  # File-based SQLite
                db_path = self.database_url.split("///")[-1]
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        else:
            # PostgreSQL configuration
            engine_kwargs = {
                "echo": False,
                "pool_size": 5,
                "max_overflow": 10,
            }

        # Create async engine
        self.engine = create_async_engine(self.database_url, **engine_kwargs)

        # Create session factory
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create all tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database initialization completed successfully")

    @asynccontextmanager
    async def get_session(self):
        """Get an async database session with automatic cleanup.

        Yields:
            AsyncSession: Database session
        """
        if not self.session_factory:
            raise RuntimeError("Database not initialized. Call init_database() first.")

        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self) -> None:
        """Close the database connection."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")

    @property
    def _safe_url(self) -> str:
        """Get a safe version of the database URL for logging (without credentials)."""
        if self.database_url.startswith("sqlite"):
            return self.database_url

        # For other databases, hide credentials
        parts = self.database_url.split("@")
        if len(parts) > 1:
            scheme_and_creds = parts[0].split("//")
            if len(scheme_and_creds) > 1:
                scheme = scheme_and_creds[0]
                return f"{scheme}//***:***@{parts[1]}"

        return "***hidden***"

    async def health_check(self) -> bool:
        """Check if the database connection is healthy.

        Returns:
            bool: True if database is accessible, False otherwise
        """
        try:
            if not self.engine:
                return False

            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

            return True

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def execute_raw_query(self, query: str, params: Optional[dict] = None) -> Any:
        """Execute a raw SQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Query result
        """
        async with self.get_session() as session:
            result = await session.execute(text(query), params or {})
            return result


# Global database manager instance
db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance.

    Returns:
        DatabaseManager: The database manager instance

    Raises:
        RuntimeError: If database manager is not initialized
    """
    if db_manager is None:
        raise RuntimeError("Database manager not initialized")
    return db_manager


async def init_database_cli():
    """CLI command to initialize the database."""
    import sys
    import asyncio
    from app.core.config import Config

    config = Config()

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        manager = DatabaseManager(config.DATABASE_URL)
        await manager.init_database()
        logger.info("✅ Database initialized successfully!")

        # Test connection
        if await manager.health_check():
            logger.info("✅ Database health check passed!")
        else:
            logger.error("❌ Database health check failed!")
            sys.exit(1)

        await manager.close()

    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Allow running as a module: python -m app.core.database init
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "init":
        asyncio.run(init_database_cli())
    else:
        print("Usage: python -m app.core.database init")
