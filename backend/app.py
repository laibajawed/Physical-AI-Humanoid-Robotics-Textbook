"""
FastAPI application for RAG Agent API.

Provides REST API endpoints for Physical AI & Robotics textbook Q&A.
"""

import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from models import (
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
    ErrorCodes,
    ErrorResponse,
    HealthResponse,
    ResponseMetadata,
    ServiceStatus,
    SelectedTextCitation,
    SourceCitation,
)
from agent import (
    run_agent_streamed,
    run_agent,
    extract_and_validate_citations,
    create_selected_text_citation,
    determine_confidence,
    get_fallback_answer,
)
from db import (
    init_tables,
    get_or_create_session,
    get_session,
    save_conversation,
    get_conversation_history,
    get_recent_context,
    check_postgres_health,
    close_engine,
)
from retrieve import get_collection_stats
from auth import verify_jwt_token


# =============================================================================
# Configuration
# =============================================================================

load_dotenv()

# CORS origins
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

# Rate limiting
MAX_CONCURRENT_REQUESTS = 10
RETRY_AFTER_SECONDS = 30

# Version
API_VERSION = "0.1.0"


# =============================================================================
# Rate Limiting
# =============================================================================

_current_requests = 0
_rate_lock = asyncio.Lock()


async def acquire_request_slot() -> bool:
    """
    Attempt to acquire a request slot for rate limiting.

    Returns:
        True if slot acquired, False if rate limited
    """
    global _current_requests
    async with _rate_lock:
        if _current_requests >= MAX_CONCURRENT_REQUESTS:
            return False
        _current_requests += 1
        return True


async def release_request_slot() -> None:
    """Release a request slot."""
    global _current_requests
    async with _rate_lock:
        _current_requests = max(0, _current_requests - 1)


# =============================================================================
# JSON Structured Logging
# =============================================================================

def log_request(
    level: str,
    stage: str,
    message: str,
    request_id: Optional[UUID] = None,
    latency_ms: Optional[float] = None,
    error: Optional[str] = None,
    **extra: Any,
) -> None:
    """
    JSON structured logging for API requests.

    Args:
        level: Log level (INFO, WARNING, ERROR)
        stage: Processing stage
        message: Human-readable message
        request_id: Request UUID for tracing
        latency_ms: Request latency in milliseconds
        error: Error message if applicable
        **extra: Additional fields
    """
    entry: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": level,
        "stage": stage,
        "message": message,
    }
    if request_id:
        entry["request_id"] = str(request_id)
    if latency_ms is not None:
        entry["latency_ms"] = round(latency_ms, 2)
    if error:
        entry["error"] = error
    entry.update(extra)

    print(json.dumps(entry))


# =============================================================================
# Lifespan (Startup/Shutdown)
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    log_request("INFO", "startup", "Initializing RAG Agent API")
    try:
        await init_tables()
        log_request("INFO", "startup", "Database tables initialized")
    except Exception as e:
        log_request("WARNING", "startup", f"Database init failed (will retry on demand): {e}")

    yield

    # Shutdown
    log_request("INFO", "shutdown", "Shutting down RAG Agent API")
    await close_engine()


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="RAG Agent API",
    description="FastAPI backend for Physical AI & Robotics textbook Q&A",
    version=API_VERSION,
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Request ID Middleware
# =============================================================================

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Add request ID to each request for tracing."""
    request_id = uuid4()
    request.state.request_id = request_id

    start_time = time.perf_counter()
    response = await call_next(request)
    latency_ms = (time.perf_counter() - start_time) * 1000

    # Add request ID to response headers
    response.headers["X-Request-ID"] = str(request_id)

    # Log request completion
    log_request(
        "INFO",
        "request",
        f"{request.method} {request.url.path}",
        request_id=request_id,
        latency_ms=latency_ms,
        status_code=response.status_code,
    )

    return response


# =============================================================================
# Exception Handlers
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with structured error response."""
    request_id = getattr(request.state, "request_id", uuid4())

    # Map status codes to error codes
    error_code_map = {
        400: ErrorCodes.EMPTY_QUERY,
        429: ErrorCodes.RATE_LIMITED,
        503: ErrorCodes.SERVICE_UNAVAILABLE,
        500: ErrorCodes.INTERNAL_ERROR,
    }
    error_code = error_code_map.get(exc.status_code, ErrorCodes.INTERNAL_ERROR)

    # Check for specific error codes in detail
    if isinstance(exc.detail, dict) and "error_code" in exc.detail:
        error_code = exc.detail["error_code"]
        message = exc.detail.get("message", str(exc.detail))
        details = exc.detail.get("details")
    else:
        message = str(exc.detail)
        details = None

    error_response = ErrorResponse(
        error_code=error_code,
        message=message,
        request_id=request_id,
        details=details,
    )

    headers = {}
    if exc.status_code in (429, 503):
        headers["Retry-After"] = str(RETRY_AFTER_SECONDS)

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json"),
        headers=headers,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    request_id = getattr(request.state, "request_id", uuid4())

    log_request(
        "ERROR",
        "exception",
        f"Unhandled exception: {type(exc).__name__}",
        request_id=request_id,
        error=str(exc),
    )

    error_response = ErrorResponse(
        error_code=ErrorCodes.INTERNAL_ERROR,
        message="An unexpected error occurred",
        request_id=request_id,
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(mode="json"),
    )


# =============================================================================
# Health Endpoint
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """
    Check service health.

    Returns status of dependent services (Qdrant, Postgres).
    """
    services: Dict[str, ServiceStatus] = {}
    overall_status = "healthy"

    # Check Qdrant
    qdrant_start = time.perf_counter()
    try:
        stats = await get_collection_stats()
        qdrant_latency = (time.perf_counter() - qdrant_start) * 1000
        services["qdrant"] = ServiceStatus(
            name="qdrant",
            status="healthy",
            latency_ms=qdrant_latency,
        )
    except Exception as e:
        qdrant_latency = (time.perf_counter() - qdrant_start) * 1000
        services["qdrant"] = ServiceStatus(
            name="qdrant",
            status="unavailable",
            latency_ms=qdrant_latency,
            error=str(e),
        )
        overall_status = "degraded"

    # Check Postgres
    pg_healthy, pg_latency, pg_error = await check_postgres_health()
    if pg_healthy:
        services["postgres"] = ServiceStatus(
            name="postgres",
            status="healthy",
            latency_ms=pg_latency,
        )
    else:
        services["postgres"] = ServiceStatus(
            name="postgres",
            status="unavailable",
            latency_ms=pg_latency,
            error=pg_error,
        )
        overall_status = "degraded"

    # If both are unavailable, overall is unavailable
    if all(s.status == "unavailable" for s in services.values()):
        overall_status = "unavailable"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        services=services,
        version=API_VERSION,
    )


# =============================================================================
# Chat Endpoint
# =============================================================================

@app.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(
    request: Request, 
    chat_request: ChatRequest,
    current_user: dict = Depends(verify_jwt_token),
) -> ChatResponse:
    """
    Ask a question about the Physical AI & Robotics textbook.

    Returns an AI-generated answer with source citations.

    Modes:
    - Default: Searches full book content via Qdrant
    - Selected-text: If `selected_text` is provided, answers are grounded only in that text
    """
    request_id = getattr(request.state, "request_id", uuid4())
    start_time = time.perf_counter()

    # Rate limiting
    if not await acquire_request_slot():
        raise HTTPException(
            status_code=429,
            detail={
                "error_code": ErrorCodes.RATE_LIMITED,
                "message": "Too many concurrent requests. Please try again later.",
            },
        )

    try:
        # Validate request
        query = chat_request.query
        selected_text = chat_request.selected_text
        session_id = chat_request.session_id or uuid4()
        filters = chat_request.filters

        # Validate query not empty (additional check)
        if not query or not query.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": ErrorCodes.EMPTY_QUERY,
                    "message": "Query cannot be empty",
                },
            )

        # Validate query length
        if len(query) > 32000:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": ErrorCodes.QUERY_TOO_LONG,
                    "message": f"Query exceeds maximum length of 32000 characters (got {len(query)})",
                },
            )

        # Validate selected_text length
        if selected_text and len(selected_text) > 64000:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": ErrorCodes.SELECTION_TOO_LONG,
                    "message": f"Selected text exceeds maximum length of 64000 characters (got {len(selected_text)})",
                },
            )

        log_request(
            "INFO",
            "chat",
            "Processing chat request",
            request_id=request_id,
            query_length=len(query),
            mode="selected_text" if selected_text else "full",
        )

        # Get or create session
        try:
            session = await get_or_create_session(session_id)
        except Exception as e:
            log_request("WARNING", "chat", f"Session operation failed: {e}", request_id=request_id)
            # Continue without session persistence
            session = None

        # Get conversation history for context
        conversation_history = None
        if session and not selected_text:
            try:
                conversation_history = await get_recent_context(session_id, limit=5)
            except Exception:
                pass  # Continue without history

        # Build filter dict
        filter_dict = None
        if filters:
            filter_dict = {}
            if filters.source_url_prefix:
                filter_dict["source_url_prefix"] = filters.source_url_prefix
            if filters.section:
                filter_dict["section"] = filters.section

        # Run agent
        agent_result = await run_agent(
            query=query,
            selected_text=selected_text,
            conversation_history=conversation_history,
            filters=filter_dict,
        )

        # Process results
        answer = agent_result.get("answer")
        tool_results = agent_result.get("tool_results", [])
        error = agent_result.get("error")

        # Determine mode and confidence
        if selected_text:
            mode = "selected_text"
            low_confidence = False
            retrieval_count = 0
            sources = [create_selected_text_citation(
                selected_text,
                "Answer derived from provided selection",
            )]
        else:
            low_confidence, mode = determine_confidence(tool_results)
            retrieval_count = len(tool_results)
            sources = extract_and_validate_citations(answer or "", tool_results)

        # Handle fallback
        fallback_message = None
        if error:
            fallback_message = get_fallback_answer(tool_results, error)
            # Preserve selected_text mode even on error
            if not selected_text:
                mode = "retrieval_only" if tool_results else "no_results"

        # Calculate timing
        query_time_ms = (time.perf_counter() - start_time) * 1000

        # Build metadata
        metadata = ResponseMetadata(
            query_time_ms=query_time_ms,
            retrieval_count=retrieval_count,
            mode=mode,
            low_confidence=low_confidence,
            request_id=request_id,
        )

        # Build response
        response = ChatResponse(
            answer=answer,
            fallback_message=fallback_message,
            sources=sources,
            metadata=metadata,
            session_id=session_id,
        )

        # Save conversation to history
        if session and answer:
            try:
                await save_conversation(
                    session_id=session_id,
                    query=query,
                    response=answer,
                    sources=[s.model_dump() for s in sources],
                    metadata=metadata.model_dump(mode="json"),
                )
            except Exception as e:
                log_request(
                    "WARNING",
                    "chat",
                    f"Failed to save conversation: {e}",
                    request_id=request_id,
                )

        log_request(
            "INFO",
            "chat",
            "Chat request completed",
            request_id=request_id,
            latency_ms=query_time_ms,
            mode=mode,
            retrieval_count=retrieval_count,
        )

        return response

    finally:
        await release_request_slot()


# =============================================================================
# Streaming Chat Endpoint (SSE)
# =============================================================================

@app.post("/chat/stream", tags=["chat"])
async def chat_stream(
    request: Request, 
    chat_request: ChatRequest,
    current_user: dict = Depends(verify_jwt_token),
):
    """
    Stream answer generation via Server-Sent Events.

    Event types:
    - delta: Partial answer text
    - sources: Citation data (sent at end)
    - done: Stream complete
    - error: Error occurred
    """
    request_id = getattr(request.state, "request_id", uuid4())

    # Rate limiting
    if not await acquire_request_slot():
        raise HTTPException(
            status_code=429,
            detail={
                "error_code": ErrorCodes.RATE_LIMITED,
                "message": "Too many concurrent requests. Please try again later.",
            },
        )

    async def generate_stream():
        try:
            # Use Runner.run_streamed() for true streaming (T071)
            query = chat_request.query
            selected_text = chat_request.selected_text
            session_id = chat_request.session_id or uuid4()

            start_time = time.perf_counter()

            # Stream events from agent using run_agent_streamed
            async for event in run_agent_streamed(
                query=query,
                selected_text=selected_text,
            ):
                event_type = event.get("type")

                if event_type == "delta":
                    delta_data = json.dumps({"delta": event.get("content", "")})
                    yield f"data: {delta_data}\n\n"

                elif event_type == "sources":
                    query_time_ms = (time.perf_counter() - start_time) * 1000
                    mode = "selected_text" if selected_text else "full"
                    sources_data = json.dumps({
                        "sources": event.get("data", []),
                        "metadata": {
                            "query_time_ms": query_time_ms,
                            "mode": mode,
                            "session_id": str(session_id)
                        }
                    })
                    yield f"data: {sources_data}\n\n"

                elif event_type == "done":
                    yield f"data: {json.dumps({'done': True})}\n\n"

                elif event_type == "error":
                    error_data = json.dumps({"error": event.get("message", "Unknown error")})
                    yield f"data: {error_data}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            await release_request_slot()

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Request-ID": str(request_id),
        },
    )


# =============================================================================
# History Endpoint
# =============================================================================

@app.get("/history/{session_id}", response_model=ConversationHistoryResponse, tags=["history"])
async def get_history(
    request: Request,
    session_id: UUID,
    limit: int = 50,
    current_user: dict = Depends(verify_jwt_token),
) -> ConversationHistoryResponse:
    """
    Get conversation history for a session.

    Args:
        session_id: UUID of the session
        limit: Maximum entries to return (1-100, default 50)
    """
    request_id = getattr(request.state, "request_id", uuid4())

    # Validate limit
    limit = max(1, min(limit, 100))

    # Check if session exists
    session = await get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCodes.SESSION_NOT_FOUND,
                "message": f"Session {session_id} not found",
            },
        )

    # Get history
    entries = await get_conversation_history(session_id, limit=limit)

    return ConversationHistoryResponse(
        session_id=session_id,
        entries=entries,
        total_entries=len(entries),
    )


# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/", tags=["health"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "RAG Agent API",
        "version": API_VERSION,
        "description": "Physical AI & Robotics textbook Q&A API",
        "endpoints": {
            "chat": "POST /chat",
            "stream": "POST /chat/stream",
            "health": "GET /health",
            "history": "GET /history/{session_id}",
            "docs": "GET /docs",
        },
    }


# =============================================================================
# Run with Uvicorn
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=True,
    )
