"""
Database operations for RAG Agent API.

Provides async operations for Neon Postgres session and conversation storage.
Uses SQLAlchemy 2.0 async with asyncpg driver.
"""

import json
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import asyncio

from models.session import ConversationRecord, HistoryEntry, Session


# =============================================================================
# Database Configuration
# =============================================================================

# Module-level engine (lazy initialized)
_engine: Optional[AsyncEngine] = None
_async_session_factory: Optional[sessionmaker] = None


def _get_database_url() -> str:
    """
    Get database URL from environment, converting to asyncpg format.

    Returns:
        Async-compatible database URL

    Raises:
        EnvironmentError: If DATABASE_URL not set
    """
    from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

    load_dotenv()
    url = os.getenv("DATABASE_URL")
    if not url:
        raise EnvironmentError("Missing required environment variable: DATABASE_URL")

    # Convert postgresql:// to postgresql+asyncpg://
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    # Parse URL to handle query parameters properly
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    # Remove parameters not supported by asyncpg
    unsupported_params = ["sslmode", "channel_binding", "options"]
    for param in unsupported_params:
        params.pop(param, None)

    # Add SSL requirement for Neon (asyncpg style)
    params["ssl"] = ["require"]

    # Rebuild URL with cleaned parameters
    new_query = urlencode(params, doseq=True)
    new_parsed = parsed._replace(query=new_query)
    url = urlunparse(new_parsed)

    return url


async def get_engine(use_null_pool: bool = False) -> AsyncEngine:
    """
    Get or create async SQLAlchemy engine.

    Args:
        use_null_pool: If True, use NullPool (for testing to avoid connection issues)

    Returns:
        AsyncEngine instance
    """
    global _engine

    if _engine is None:
        url = _get_database_url()

        # Use NullPool for testing environments to avoid async connection conflicts
        if use_null_pool or os.getenv("TESTING", "").lower() == "true":
            _engine = create_async_engine(
                url,
                echo=False,
                poolclass=NullPool,  # No connection pooling - each request gets fresh connection
            )
        else:
            _engine = create_async_engine(
                url,
                echo=False,  # Set to True for SQL debugging
                pool_size=5,
                max_overflow=10,
                pool_timeout=5,  # 5 second timeout per spec
                pool_recycle=300,  # Recycle connections every 5 minutes
                pool_pre_ping=True,  # Verify connections before use
            )

    return _engine


async def get_session_factory() -> sessionmaker:
    """
    Get or create async session factory.

    Returns:
        Async session factory
    """
    global _async_session_factory

    if _async_session_factory is None:
        engine = await get_engine()
        _async_session_factory = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    return _async_session_factory


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.

    Usage:
        async with get_db_session() as session:
            await session.execute(...)

    Yields:
        AsyncSession instance
    """
    factory = await get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# =============================================================================
# Table Initialization
# =============================================================================

async def init_tables() -> None:
    """
    Create required tables if they don't exist.

    Creates:
    - sessions: Tracks user sessions
    - conversations: Stores chat history
    """
    engine = await get_engine()

    async with engine.begin() as conn:
        # Create sessions table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id UUID PRIMARY KEY,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                last_active TIMESTAMPTZ DEFAULT NOW()
            )
        """))

        # Create conversations table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                sources JSONB DEFAULT '[]',
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))

        # Create indexes
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_conversations_session
            ON conversations(session_id)
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_conversations_timestamp
            ON conversations(timestamp DESC)
        """))


# =============================================================================
# Session Operations
# =============================================================================

async def create_session(session_id: UUID) -> Session:
    """
    Create a new session.

    Args:
        session_id: UUID for the new session

    Returns:
        Created Session object
    """
    async with get_db_session() as db:
        now = datetime.utcnow()
        await db.execute(
            text("""
                INSERT INTO sessions (session_id, created_at, last_active)
                VALUES (:session_id, :created_at, :last_active)
            """),
            {
                "session_id": str(session_id),
                "created_at": now,
                "last_active": now,
            },
        )

    return Session(
        session_id=session_id,
        created_at=now,
        last_active=now,
    )


async def get_session(session_id: UUID) -> Optional[Session]:
    """
    Retrieve a session by ID.

    Args:
        session_id: UUID of the session

    Returns:
        Session object if found, None otherwise
    """
    async with get_db_session() as db:
        result = await db.execute(
            text("""
                SELECT session_id, created_at, last_active
                FROM sessions
                WHERE session_id = :session_id
            """),
            {"session_id": str(session_id)},
        )
        row = result.fetchone()

        if row:
            return Session(
                session_id=UUID(str(row[0])),
                created_at=row[1],
                last_active=row[2],
            )

    return None


async def update_session_activity(session_id: UUID) -> bool:
    """
    Update session's last_active timestamp.

    Args:
        session_id: UUID of the session

    Returns:
        True if session was updated, False if not found
    """
    async with get_db_session() as db:
        result = await db.execute(
            text("""
                UPDATE sessions
                SET last_active = NOW()
                WHERE session_id = :session_id
            """),
            {"session_id": str(session_id)},
        )
        return result.rowcount > 0


async def get_or_create_session(session_id: UUID) -> Session:
    """
    Get existing session or create new one.

    Args:
        session_id: UUID of the session

    Returns:
        Session object (existing or newly created)
    """
    session = await get_session(session_id)
    if session:
        await update_session_activity(session_id)
        return session
    return await create_session(session_id)


# =============================================================================
# Conversation Operations
# =============================================================================

async def save_conversation(
    session_id: UUID,
    query: str,
    response: str,
    sources: List[Dict[str, Any]],
    metadata: Dict[str, Any],
) -> ConversationRecord:
    """
    Store a conversation exchange.

    Args:
        session_id: UUID of the session
        query: User's question
        response: Agent's answer
        sources: List of citation dictionaries
        metadata: Response metadata dictionary

    Returns:
        Created ConversationRecord object
    """
    async with get_db_session() as db:
        now = datetime.utcnow()
        result = await db.execute(
            text("""
                INSERT INTO conversations (session_id, timestamp, query, response, sources, metadata)
                VALUES (:session_id, :timestamp, :query, :response, :sources, :metadata)
                RETURNING id
            """),
            {
                "session_id": str(session_id),
                "timestamp": now,
                "query": query,
                "response": response,
                "sources": json.dumps(sources),
                "metadata": json.dumps(metadata),
            },
        )
        row = result.fetchone()
        record_id = row[0] if row else None

    return ConversationRecord(
        id=record_id,
        session_id=session_id,
        timestamp=now,
        query=query,
        response=response,
        sources=sources,
        metadata=metadata,
    )


async def get_conversation_history(
    session_id: UUID,
    limit: int = 50,
) -> List[HistoryEntry]:
    """
    Retrieve conversation history for a session.

    Args:
        session_id: UUID of the session
        limit: Maximum entries to return (default 50)

    Returns:
        List of HistoryEntry objects, oldest first
    """
    async with get_db_session() as db:
        result = await db.execute(
            text("""
                SELECT timestamp, query, response, sources
                FROM conversations
                WHERE session_id = :session_id
                ORDER BY timestamp ASC
                LIMIT :limit
            """),
            {
                "session_id": str(session_id),
                "limit": limit,
            },
        )
        rows = result.fetchall()

    entries = []
    for row in rows:
        sources = row[3] if isinstance(row[3], list) else json.loads(row[3] or "[]")
        entries.append(
            HistoryEntry(
                timestamp=row[0],
                query=row[1],
                response=row[2],
                sources=sources,
            )
        )

    return entries


async def get_recent_context(
    session_id: UUID,
    limit: int = 5,
) -> List[Dict[str, str]]:
    """
    Get recent conversation exchanges for context.

    Args:
        session_id: UUID of the session
        limit: Number of recent exchanges to retrieve

    Returns:
        List of dicts with 'role' and 'content' for agent context
    """
    async with get_db_session() as db:
        result = await db.execute(
            text("""
                SELECT query, response
                FROM conversations
                WHERE session_id = :session_id
                ORDER BY timestamp DESC
                LIMIT :limit
            """),
            {
                "session_id": str(session_id),
                "limit": limit,
            },
        )
        rows = result.fetchall()

    # Reverse to get chronological order
    context = []
    for row in reversed(rows):
        context.append({"role": "user", "content": row[0]})
        context.append({"role": "assistant", "content": row[1]})

    return context


# =============================================================================
# Health Check
# =============================================================================

async def check_postgres_health() -> tuple[bool, Optional[float], Optional[str]]:
    """
    Check Postgres connectivity for health endpoint.

    Returns:
        Tuple of (is_healthy, latency_ms, error_message)
    """
    import time

    start = time.perf_counter()
    try:
        async with get_db_session() as db:
            result = await db.execute(text("SELECT 1"))
            result.fetchone()
        latency = (time.perf_counter() - start) * 1000
        return True, latency, None
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return False, latency, str(e)


# =============================================================================
# Cleanup
# =============================================================================

async def close_engine() -> None:
    """Close database engine and connection pool."""
    global _engine, _async_session_factory

    if _engine:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
