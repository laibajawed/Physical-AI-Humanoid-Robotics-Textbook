"""
Pytest configuration and fixtures for RAG Agent API tests.
"""

import os
import sys
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Set testing environment BEFORE importing app
os.environ["TESTING"] = "true"

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


# Configure pytest-asyncio to use function-scoped event loops
@pytest.fixture(scope="function")
def anyio_backend():
    """Use asyncio backend for async tests."""
    return "asyncio"


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create async HTTP client for testing API endpoints.

    Yields:
        AsyncClient configured for ASGI testing
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=60.0) as ac:
        yield ac


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ["TESTING"] = "true"
    yield
    # Cleanup
    os.environ.pop("TESTING", None)


@pytest.fixture
def sample_chat_request():
    """Sample chat request payload."""
    return {
        "query": "What is inverse kinematics?",
    }


@pytest.fixture
def sample_selected_text_request():
    """Sample chat request with selected text."""
    return {
        "query": "Explain this in simpler terms",
        "selected_text": "Inverse kinematics (IK) is the mathematical process of calculating the joint angles needed to position an end effector at a desired location and orientation.",
    }


@pytest.fixture
def sample_out_of_scope_request():
    """Sample out-of-scope question."""
    return {
        "query": "What is the capital of France?",
    }


@pytest.fixture
def invalid_session_id():
    """Invalid session ID for testing."""
    return "not-a-valid-uuid"


@pytest.fixture
def valid_session_id():
    """Valid session ID for testing."""
    return "550e8400-e29b-41d4-a716-446655440000"
