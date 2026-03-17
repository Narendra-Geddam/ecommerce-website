"""
Database Connection Pool for Microservices

Provides thread-safe connection pooling using psycopg2.
Each service should create its own pool instance.
"""
import os
import threading
from contextlib import contextmanager
from typing import Optional
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor


class DatabasePool:
    """Thread-safe database connection pool manager"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, database_url: str = None, min_connections: int = 2, max_connections: int = 10):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, database_url: str = None, min_connections: int = 2, max_connections: int = 10):
        if self._initialized:
            return

        self.database_url = database_url or os.environ.get('DATABASE_URL')
        if not self.database_url:
            raise RuntimeError('DATABASE_URL environment variable is required')
        self.min_connections = min_connections
        self.max_connections = max_connections
        self._pool: Optional[pool.ThreadedConnectionPool] = None
        self._pool_lock = threading.Lock()
        self._initialized = True

    def initialize(self):
        """Initialize the connection pool"""
        if self._pool is None:
            with self._pool_lock:
                if self._pool is None:
                    self._pool = pool.ThreadedConnectionPool(
                        minconn=self.min_connections,
                        maxconn=self.max_connections,
                        dsn=self.database_url
                    )
        return self._pool

    def get_connection(self):
        """Get a connection from the pool"""
        if self._pool is None:
            self.initialize()
        return self._pool.getconn()

    def return_connection(self, conn):
        """Return a connection to the pool"""
        if self._pool is not None:
            self._pool.putconn(conn)

    def close_all(self):
        """Close all connections in the pool"""
        if self._pool is not None:
            self._pool.closeall()

    @contextmanager
    def connection(self, cursor_factory=RealDictCursor, autocommit=True):
        """Context manager for database connections"""
        conn = None
        try:
            conn = self.get_connection()
            conn.autocommit = autocommit
            cursor = conn.cursor(cursor_factory=cursor_factory)
            yield cursor
        finally:
            if conn is not None:
                if not autocommit:
                    conn.commit()
                self.return_connection(conn)


# Global pool instance
_pool_instance: Optional[DatabasePool] = None
_pool_lock = threading.Lock()


def get_connection_pool(database_url: str = None, min_connections: int = 2, max_connections: int = 10) -> DatabasePool:
    """Get or create the global connection pool"""
    global _pool_instance
    if _pool_instance is None:
        with _pool_lock:
            if _pool_instance is None:
                _pool_instance = DatabasePool(
                    database_url=database_url,
                    min_connections=min_connections,
                    max_connections=max_connections
                )
                _pool_instance.initialize()
    return _pool_instance


@contextmanager
def get_db_connection(cursor_factory=RealDictCursor, autocommit=True):
    """Get a database connection from the pool as a context manager"""
    pool = get_connection_pool()
    with pool.connection(cursor_factory=cursor_factory, autocommit=autocommit) as cursor:
        yield cursor
