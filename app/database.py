"""
 ============================================================================
 Database Connection Management
 ============================================================================
 Description: Async PostgreSQL connection pool using asyncpg
 Provides connection utilities for PostGIS spatial queries
 ============================================================================
"""

import asyncpg
from typing import Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """
    Async PostgreSQL connection pool manager.
    Handles connection lifecycle and provides query execution methods.
    """
    
    pool: Optional[asyncpg.Pool] = None
    
    @classmethod
    async def create_pool(cls) -> asyncpg.Pool:
        """
        Create and initialize the connection pool.
        
        Returns:
            asyncpg.Pool: Connection pool instance
        """
        if cls.pool is None:
            try:
                cls.pool = await asyncpg.create_pool(
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    database=settings.DB_NAME,
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD,
                    min_size=5,
                    max_size=20,
                    command_timeout=60
                )
                logger.info("Database connection pool created successfully")
            except Exception as e:
                logger.error(f"Failed to create database pool: {e}")
                raise
        return cls.pool
    
    @classmethod
    async def close_pool(cls):
        """Close the connection pool."""
        if cls.pool:
            await cls.pool.close()
            cls.pool = None
            logger.info("Database connection pool closed")
    
    @classmethod
    async def get_connection(cls) -> asyncpg.Connection:
        """
        Get a connection from the pool.
        
        Returns:
            asyncpg.Connection: Database connection
        """
        if cls.pool is None:
            await cls.create_pool()
        return cls.pool.acquire()
    
    @classmethod
    async def execute_query(cls, query: str, *args) -> list:
        """
        Execute a query and return results.
        
        Args:
            query: SQL query string
            *args: Query parameters
            
        Returns:
            List of query results
        """
        conn = await cls.get_connection()
        try:
            result = await conn.fetch(query, *args)
            return result
        finally:
            await cls.pool.release(conn)
    
    @classmethod
    async def execute_command(cls, command: str, *args) -> str:
        """
        Execute a command (INSERT, UPDATE, DELETE) and return status.
        
        Args:
            command: SQL command string
            *args: Command parameters
            
        Returns:
            Command status message
        """
        conn = await cls.get_connection()
        try:
            result = await conn.execute(command, *args)
            return result
        finally:
            await cls.pool.release(conn)


# Dependency for FastAPI routes
async def get_db():
    """
    Dependency injection for database access.
    Yields a connection from the pool.
    """
    pool = await Database.create_pool()
    async with pool.acquire() as connection:
        yield connection
