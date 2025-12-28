"""
API smoke tests for RAG Agent API.

Tests cover:
- Health check endpoint
- Basic chat functionality
- Selected-text mode
- Error handling
- Response schema validation
"""

import pytest
from uuid import uuid4


# =============================================================================
# Health Endpoint Tests (User Story 5)
# =============================================================================

@pytest.mark.asyncio
async def test_health_endpoint_returns_200(client):
    """T051: Smoke test - GET /health returns status with Qdrant info."""
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded", "unavailable"]
    assert "timestamp" in data
    assert "version" in data
    assert "services" in data


@pytest.mark.asyncio
async def test_health_endpoint_has_service_status(client):
    """Health endpoint returns service status details."""
    response = await client.get("/health")
    data = response.json()

    # Should have at least qdrant service status
    services = data.get("services", {})
    if "qdrant" in services:
        qdrant = services["qdrant"]
        assert "name" in qdrant
        assert "status" in qdrant
        assert qdrant["status"] in ["healthy", "degraded", "unavailable"]


# =============================================================================
# Root Endpoint Test
# =============================================================================

@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Root endpoint returns API information."""
    response = await client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "endpoints" in data


# =============================================================================
# Chat Endpoint Tests (User Story 1)
# =============================================================================

@pytest.mark.asyncio
async def test_chat_basic_question(client, sample_chat_request):
    """T024: Smoke test - POST /chat basic question returns answer with sources."""
    response = await client.post("/chat", json=sample_chat_request)

    # Should return 200 (or timeout if services unavailable)
    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        # Required fields
        assert "metadata" in data
        assert "session_id" in data

        # Metadata fields
        metadata = data["metadata"]
        assert "query_time_ms" in metadata
        assert "retrieval_count" in metadata
        assert "mode" in metadata
        assert "request_id" in metadata


@pytest.mark.asyncio
async def test_chat_returns_session_id(client, sample_chat_request):
    """Chat returns session_id (generated if not provided)."""
    response = await client.post("/chat", json=sample_chat_request)

    if response.status_code == 200:
        data = response.json()
        assert "session_id" in data
        # Should be a valid UUID string
        assert len(data["session_id"]) == 36


@pytest.mark.asyncio
async def test_chat_with_session_id(client, sample_chat_request, valid_session_id):
    """Chat with provided session_id returns same session_id."""
    request = {**sample_chat_request, "session_id": valid_session_id}
    response = await client.post("/chat", json=request)

    if response.status_code == 200:
        data = response.json()
        assert data["session_id"] == valid_session_id


@pytest.mark.asyncio
async def test_chat_citation_structure(client, sample_chat_request):
    """T025: Citation structure matches SourceCitation schema."""
    response = await client.post("/chat", json=sample_chat_request)

    if response.status_code == 200:
        data = response.json()
        sources = data.get("sources", [])

        for source in sources:
            # SourceCitation required fields
            if source.get("source_type") != "selected_text":
                assert "source_url" in source
                assert "title" in source
                assert "section" in source
                assert "chunk_position" in source
                assert "similarity_score" in source
                assert "snippet" in source


# =============================================================================
# Selected-Text Mode Tests (User Story 2)
# =============================================================================

@pytest.mark.asyncio
async def test_chat_selected_text_mode(client, sample_selected_text_request):
    """T032: Smoke test - POST /chat with selected_text returns answer."""
    response = await client.post("/chat", json=sample_selected_text_request)

    if response.status_code == 200:
        data = response.json()
        metadata = data.get("metadata", {})
        # Mode should be selected_text
        assert metadata.get("mode") == "selected_text"
        # Should not have Qdrant retrieval count (or 0)
        assert metadata.get("retrieval_count", 0) == 0


@pytest.mark.asyncio
async def test_chat_selected_text_citation_type(client, sample_selected_text_request):
    """T033: Selected_text mode citation has source_type='selected_text'."""
    response = await client.post("/chat", json=sample_selected_text_request)

    if response.status_code == 200:
        data = response.json()
        sources = data.get("sources", [])

        # Should have at least one source
        if sources:
            # First source should be selected_text type
            assert sources[0].get("source_type") == "selected_text"
            assert "selection_length" in sources[0]
            assert "snippet" in sources[0]


# =============================================================================
# Citation Tests (User Story 3)
# =============================================================================

@pytest.mark.asyncio
async def test_snippet_max_length(client, sample_chat_request):
    """T039: Snippet field is max 200 chars."""
    response = await client.post("/chat", json=sample_chat_request)

    if response.status_code == 200:
        data = response.json()
        sources = data.get("sources", [])

        for source in sources:
            snippet = source.get("snippet", "")
            assert len(snippet) <= 203  # 200 + "..." ellipsis


# =============================================================================
# Error Handling Tests
# =============================================================================

@pytest.mark.asyncio
async def test_empty_query_returns_400(client):
    """T022: Empty query returns 400 EMPTY_QUERY error."""
    response = await client.post("/chat", json={"query": "   "})
    assert response.status_code == 400 or response.status_code == 422  # Validation error

    data = response.json()
    # Should have error information
    if "error_code" in data:
        assert data["error_code"] == "EMPTY_QUERY"


@pytest.mark.asyncio
async def test_missing_query_returns_422(client):
    """Missing query field returns 422."""
    response = await client.post("/chat", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_error_response_has_request_id(client):
    """T069: All errors return structured ErrorResponse with request_id."""
    response = await client.post("/chat", json={})
    assert response.status_code == 422

    # Check X-Request-ID header
    assert "x-request-id" in response.headers


@pytest.mark.asyncio
async def test_query_too_long(client):
    """T023: Query too long returns 400 or 422 error."""
    # Query with 33000 characters (exceeds 32000 limit)
    long_query = "a" * 33000
    response = await client.post("/chat", json={"query": long_query})

    # Should be rejected for length (422 from Pydantic validation, 400 from app validation)
    assert response.status_code in [400, 422]

    data = response.json()
    # Either our custom error code or Pydantic's validation error
    if "error_code" in data:
        assert data["error_code"] == "QUERY_TOO_LONG"
    elif "detail" in data:
        # Pydantic validation error format
        assert any("max_length" in str(err).lower() or "32000" in str(err) for err in data["detail"])


# =============================================================================
# Session/History Tests (User Story 6)
# =============================================================================

@pytest.mark.asyncio
async def test_chat_without_session_id_returns_new_session(client, sample_chat_request):
    """T059: Chat without session_id returns new session_id."""
    response = await client.post("/chat", json=sample_chat_request)

    if response.status_code == 200:
        data = response.json()
        assert "session_id" in data
        # UUID format check
        session_id = data["session_id"]
        assert len(session_id) == 36
        assert session_id.count("-") == 4


@pytest.mark.asyncio
async def test_invalid_session_id_format(client, sample_chat_request):
    """T061: Invalid session_id format returns 400 error."""
    request = {**sample_chat_request, "session_id": "not-a-uuid"}
    response = await client.post("/chat", json=request)

    # Should reject invalid UUID
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_history_endpoint_not_found(client):
    """History for non-existent session returns 404."""
    fake_session = str(uuid4())
    response = await client.get(f"/history/{fake_session}")

    assert response.status_code == 404
    data = response.json()
    if "error_code" in data:
        assert data["error_code"] == "SESSION_NOT_FOUND"


@pytest.mark.asyncio
async def test_history_invalid_session_id(client):
    """History with invalid session_id returns 422."""
    response = await client.get("/history/invalid-uuid")
    assert response.status_code == 422


# =============================================================================
# Response Schema Validation Tests
# =============================================================================

@pytest.mark.asyncio
async def test_chat_response_schema(client, sample_chat_request):
    """Validate ChatResponse schema structure."""
    response = await client.post("/chat", json=sample_chat_request)

    if response.status_code == 200:
        data = response.json()

        # Required fields per schema
        assert "metadata" in data
        assert "session_id" in data

        # Metadata schema
        metadata = data["metadata"]
        assert isinstance(metadata.get("query_time_ms"), (int, float))
        assert isinstance(metadata.get("retrieval_count"), int)
        assert metadata.get("mode") in ["full", "selected_text", "retrieval_only", "no_results"]
        assert isinstance(metadata.get("low_confidence"), bool)
        assert "request_id" in metadata

        # Sources should be a list
        assert isinstance(data.get("sources", []), list)


@pytest.mark.asyncio
async def test_health_response_schema(client):
    """Validate HealthResponse schema structure."""
    response = await client.get("/health")
    data = response.json()

    # Required fields per schema
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data

    # Services should be a dict
    assert isinstance(data.get("services", {}), dict)


# =============================================================================
# Out-of-Scope Tests (User Story 4)
# =============================================================================

@pytest.mark.asyncio
async def test_out_of_scope_question(client, sample_out_of_scope_request):
    """T044: Out-of-scope question returns appropriate response."""
    response = await client.post("/chat", json=sample_out_of_scope_request)

    if response.status_code == 200:
        data = response.json()
        # Should have an answer (even if it says it can't answer)
        # Mode might be no_results or full with low confidence
        metadata = data.get("metadata", {})
        # The response should handle gracefully
        assert metadata.get("mode") in ["full", "no_results", "retrieval_only"]


# =============================================================================
# Rate Limiting Tests (if applicable)
# =============================================================================

@pytest.mark.asyncio
async def test_concurrent_requests_accepted(client, sample_chat_request):
    """Multiple concurrent requests should be accepted (up to limit)."""
    import asyncio

    # Send 3 concurrent requests (below limit)
    tasks = [
        client.post("/chat", json=sample_chat_request)
        for _ in range(3)
    ]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    # All should complete (200 or 503)
    for resp in responses:
        if not isinstance(resp, Exception):
            assert resp.status_code in [200, 429, 503]


# =============================================================================
# Streaming Tests (Phase 10)
# =============================================================================

@pytest.mark.asyncio
async def test_chat_stream_returns_sse_events(client, sample_chat_request):
    """T073: POST /chat/stream returns SSE events."""
    async with client.stream(
        "POST",
        "/chat/stream",
        json=sample_chat_request,
    ) as response:
        # Should return 200 with SSE content type
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        # Should have X-Request-ID header
        assert "x-request-id" in response.headers

        events_received = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                import json
                event_data = json.loads(line[6:])  # Remove "data: " prefix
                events_received.append(event_data)

                # Check for done event to break
                if "done" in event_data:
                    break

        # Should receive at least one event (either delta, sources, or done)
        assert len(events_received) > 0

        # Last event should be done
        if events_received:
            last_event = events_received[-1]
            assert "done" in last_event or "error" in last_event or "sources" in last_event


@pytest.mark.asyncio
async def test_chat_stream_delta_events(client, sample_chat_request):
    """Streaming returns delta events for partial text."""
    async with client.stream(
        "POST",
        "/chat/stream",
        json=sample_chat_request,
    ) as response:
        if response.status_code == 200:
            delta_events = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    import json
                    try:
                        event_data = json.loads(line[6:])
                        if "delta" in event_data:
                            delta_events.append(event_data)
                        if "done" in event_data:
                            break
                    except json.JSONDecodeError:
                        pass

            # Delta events should have content field
            for event in delta_events:
                assert "delta" in event
                assert isinstance(event["delta"], str)


@pytest.mark.asyncio
async def test_chat_stream_sources_event(client, sample_chat_request):
    """Streaming sends sources event at end."""
    async with client.stream(
        "POST",
        "/chat/stream",
        json=sample_chat_request,
    ) as response:
        if response.status_code == 200:
            sources_event = None
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    import json
                    try:
                        event_data = json.loads(line[6:])
                        if "sources" in event_data:
                            sources_event = event_data
                        if "done" in event_data:
                            break
                    except json.JSONDecodeError:
                        pass

            # Sources event should have sources array if found
            if sources_event:
                assert isinstance(sources_event["sources"], list)
                assert "metadata" in sources_event


@pytest.mark.asyncio
async def test_chat_stream_selected_text_mode(client, sample_selected_text_request):
    """Streaming works with selected_text mode."""
    async with client.stream(
        "POST",
        "/chat/stream",
        json=sample_selected_text_request,
    ) as response:
        assert response.status_code == 200

        events = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                import json
                try:
                    event_data = json.loads(line[6:])
                    events.append(event_data)
                    if "done" in event_data:
                        break
                except json.JSONDecodeError:
                    pass

        # Should receive events
        assert len(events) > 0
