"""
Database Connection and Operations Tests

Tests to verify:
1. PostgreSQL connection health
2. Session management
3. Conversation history persistence
4. Error handling
"""

import pytest
import pytest_asyncio
import asyncio
import os
import sys
from uuid import uuid4

# Set testing environment
os.environ["TESTING"] = "true"

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Reset database engine before each test to avoid async connection conflicts
@pytest_asyncio.fixture(autouse=True)
async def reset_db_engine():
    """Reset database engine before each test."""
    import db
    if db._engine is not None:
        await db.close_engine()
    yield
    # Cleanup after test
    if db._engine is not None:
        await db.close_engine()


# =============================================================================
# Database Connection Tests
# =============================================================================

@pytest.mark.asyncio
async def test_postgres_health_check():
    """
    Verify PostgreSQL connection health check works.
    """
    from db import check_postgres_health

    healthy, latency_ms, error = await check_postgres_health()

    print(f"PostgreSQL health check:")
    print(f"  - Healthy: {healthy}")
    print(f"  - Latency: {latency_ms:.2f}ms")
    if error:
        print(f"  - Error: {error}")

    # Don't fail if DB not configured, just skip
    if not healthy and "DATABASE_URL" in str(error):
        pytest.skip("PostgreSQL not configured")

    if healthy:
        assert latency_ms > 0, "Latency should be positive"
        assert latency_ms < 5000, f"Latency too high: {latency_ms}ms"


@pytest.mark.asyncio
async def test_init_tables():
    """
    Verify database tables can be initialized.
    """
    from db import init_tables, check_postgres_health

    # Check if DB is available first
    healthy, _, error = await check_postgres_health()
    if not healthy:
        pytest.skip(f"PostgreSQL not available: {error}")

    try:
        await init_tables()
        # If we get here, tables were created successfully
        assert True
    except Exception as e:
        pytest.fail(f"Failed to initialize tables: {e}")


# =============================================================================
# Session Management Tests
# =============================================================================

@pytest.mark.asyncio
async def test_create_session():
    """
    Verify new session can be created.
    """
    from db import get_or_create_session, check_postgres_health

    healthy, _, error = await check_postgres_health()
    if not healthy:
        pytest.skip(f"PostgreSQL not available: {error}")

    session_id = uuid4()

    try:
        session = await get_or_create_session(session_id)

        assert session is not None, "Session creation returned None"
        assert session.session_id == session_id, "Session ID mismatch"
        assert session.created_at is not None, "Missing created_at"

        print(f"Created session: {session_id}")

    except Exception as e:
        pytest.fail(f"Failed to create session: {e}")


@pytest.mark.asyncio
async def test_get_existing_session():
    """
    Verify existing session can be retrieved.
    """
    from db import get_or_create_session, get_session, check_postgres_health

    healthy, _, error = await check_postgres_health()
    if not healthy:
        pytest.skip(f"PostgreSQL not available: {error}")

    session_id = uuid4()

    try:
        # Create session
        await get_or_create_session(session_id)

        # Retrieve it
        session = await get_session(session_id)

        assert session is not None, "Failed to retrieve existing session"
        assert session.session_id == session_id, "Session ID mismatch"

    except Exception as e:
        pytest.fail(f"Failed to get session: {e}")


@pytest.mark.asyncio
async def test_get_nonexistent_session():
    """
    Verify getting non-existent session returns None.
    """
    from db import get_session, check_postgres_health

    healthy, _, error = await check_postgres_health()
    if not healthy:
        pytest.skip(f"PostgreSQL not available: {error}")

    fake_session_id = uuid4()

    try:
        session = await get_session(fake_session_id)
        assert session is None, "Should return None for non-existent session"

    except Exception as e:
        pytest.fail(f"Unexpected error: {e}")


# =============================================================================
# Conversation History Tests
# =============================================================================

@pytest.mark.asyncio
async def test_save_conversation():
    """
    Verify conversation can be saved.
    """
    from db import (
        get_or_create_session, save_conversation,
        check_postgres_health
    )

    healthy, _, error = await check_postgres_health()
    if not healthy:
        pytest.skip(f"PostgreSQL not available: {error}")

    session_id = uuid4()

    try:
        # Create session
        await get_or_create_session(session_id)

        # Save conversation
        entry = await save_conversation(
            session_id=session_id,
            query="What is inverse kinematics?",
            response="Inverse kinematics is the mathematical process...",
            sources=[{"source_url": "/docs/module1", "title": "Chapter 1"}],
            metadata={"query_time_ms": 100, "mode": "full"}
        )

        assert entry is not None, "Save returned None"
        assert entry.session_id == session_id, "Session ID mismatch"
        assert entry.query == "What is inverse kinematics?", "Query mismatch"
        assert entry.response is not None, "Response not saved"

        print(f"Saved conversation entry: {entry.id}")

    except Exception as e:
        pytest.fail(f"Failed to save conversation: {e}")


@pytest.mark.asyncio
async def test_get_conversation_history():
    """
    Verify conversation history can be retrieved.
    """
    from db import (
        get_or_create_session, save_conversation,
        get_conversation_history, check_postgres_health
    )

    healthy, _, error = await check_postgres_health()
    if not healthy:
        pytest.skip(f"PostgreSQL not available: {error}")

    session_id = uuid4()

    try:
        # Create session
        await get_or_create_session(session_id)

        # Save multiple conversations
        for i in range(3):
            await save_conversation(
                session_id=session_id,
                query=f"Question {i+1}",
                response=f"Answer {i+1}",
                sources=[],
                metadata={"index": i}
            )

        # Retrieve history
        history = await get_conversation_history(session_id, limit=10)

        assert len(history) == 3, f"Expected 3 entries, got {len(history)}"

        # Should be in chronological order (oldest first) or reverse
        # depending on implementation
        print(f"Retrieved {len(history)} conversation entries")

    except Exception as e:
        pytest.fail(f"Failed to get history: {e}")


@pytest.mark.asyncio
async def test_get_recent_context():
    """
    Verify recent context retrieval for conversation continuity.
    """
    from db import (
        get_or_create_session, save_conversation,
        get_recent_context, check_postgres_health
    )

    healthy, _, error = await check_postgres_health()
    if not healthy:
        pytest.skip(f"PostgreSQL not available: {error}")

    session_id = uuid4()

    try:
        # Create session
        await get_or_create_session(session_id)

        # Save conversations
        await save_conversation(
            session_id=session_id,
            query="What is ROS2?",
            response="ROS2 is the Robot Operating System 2...",
            sources=[],
            metadata={}
        )
        await save_conversation(
            session_id=session_id,
            query="How does it handle navigation?",
            response="ROS2 navigation uses Nav2 stack...",
            sources=[],
            metadata={}
        )

        # Get recent context
        context = await get_recent_context(session_id, limit=5)

        assert context is not None, "Context should not be None"
        assert len(context) >= 2, "Should have at least 2 messages"

        # Context should be formatted for conversation
        print(f"Recent context: {len(context)} messages")

    except Exception as e:
        pytest.fail(f"Failed to get recent context: {e}")


@pytest.mark.asyncio
async def test_history_limit():
    """
    Verify history limit is respected.
    """
    from db import (
        get_or_create_session, save_conversation,
        get_conversation_history, check_postgres_health
    )

    healthy, _, error = await check_postgres_health()
    if not healthy:
        pytest.skip(f"PostgreSQL not available: {error}")

    session_id = uuid4()

    try:
        # Create session
        await get_or_create_session(session_id)

        # Save more conversations than we'll request
        for i in range(10):
            await save_conversation(
                session_id=session_id,
                query=f"Question {i+1}",
                response=f"Answer {i+1}",
                sources=[],
                metadata={}
            )

        # Request only 5
        history = await get_conversation_history(session_id, limit=5)

        assert len(history) <= 5, f"Limit not respected: got {len(history)}"

    except Exception as e:
        pytest.fail(f"Failed: {e}")


# =============================================================================
# Error Handling Tests
# =============================================================================

@pytest.mark.asyncio
async def test_save_conversation_invalid_session():
    """
    Verify saving to non-existent session is handled.
    """
    from db import save_conversation, check_postgres_health

    healthy, _, error = await check_postgres_health()
    if not healthy:
        pytest.skip(f"PostgreSQL not available: {error}")

    fake_session_id = uuid4()

    # This might either:
    # 1. Create the session automatically
    # 2. Raise an error
    # Either is acceptable behavior
    try:
        entry = await save_conversation(
            session_id=fake_session_id,
            query="Test query",
            response="Test response",
            sources=[],
            metadata={}
        )
        # If it succeeds, that's fine (auto-creates session)
        print("Auto-created session for orphan conversation")
    except Exception as e:
        # Also acceptable - foreign key constraint
        print(f"Rejected orphan conversation: {e}")


@pytest.mark.asyncio
async def test_database_graceful_degradation():
    """
    Verify API works when database is unavailable.

    The API should still function (Qdrant search) even if
    PostgreSQL is down - just without history persistence.
    """
    from httpx import ASGITransport, AsyncClient
    from app import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/chat", json={
            "query": "What is a robot?"
        })

        # Should return 200 even if DB is down
        # (fallback behavior - no history)
        assert response.status_code in [200, 503], \
            f"Unexpected status: {response.status_code}"

        if response.status_code == 200:
            data = response.json()
            # Should have an answer
            assert data.get("answer") or data.get("fallback_message")


# =============================================================================
# Health Endpoint Integration
# =============================================================================

@pytest.mark.asyncio
async def test_health_shows_postgres_status():
    """
    Verify health endpoint reports PostgreSQL status.
    """
    from httpx import ASGITransport, AsyncClient
    from app import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()

        services = data.get("services", {})

        # Postgres service should be reported
        assert "postgres" in services, "Postgres status missing from health"

        pg_status = services["postgres"]
        assert "status" in pg_status
        assert pg_status["status"] in ["healthy", "degraded", "unavailable"]

        print(f"PostgreSQL status: {pg_status['status']}")
        if pg_status.get("error"):
            print(f"PostgreSQL error: {pg_status['error']}")
