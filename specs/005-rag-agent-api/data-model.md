# Data Model: RAG Agent API (Spec-3)

**Feature**: 005-rag-agent-api
**Date**: 2025-12-17
**Status**: Complete

## Entity Relationship Diagram

```
┌─────────────────┐       ┌──────────────────┐
│   ChatRequest   │──────▶│   ChatResponse   │
└─────────────────┘       └──────────────────┘
        │                         │
        │                         ▼
        │                 ┌──────────────────┐
        │                 │  SourceCitation  │
        │                 └──────────────────┘
        │
        ▼
┌─────────────────┐       ┌──────────────────┐
│     Session     │◀─────▶│ConversationRecord│
└─────────────────┘       └──────────────────┘
```

---

## 1. Request Models

### ChatRequest

**Purpose**: Input payload for `/chat` and `/chat/stream` endpoints.

**File**: `backend/models/request.py`

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from uuid import UUID
import uuid

class MetadataFilter(BaseModel):
    """Optional filters for retrieval."""
    source_url_prefix: Optional[str] = Field(
        None,
        description="Filter results to URLs starting with this prefix",
        example="/docs/module1"
    )
    section: Optional[str] = Field(
        None,
        description="Filter results to specific section name (exact match)",
        example="Inverse Kinematics"
    )


class ChatRequest(BaseModel):
    """Input for chat endpoint."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=32000,
        description="Natural language question about the book",
        example="What is inverse kinematics?"
    )
    selected_text: Optional[str] = Field(
        None,
        max_length=64000,
        description="If provided, answer is grounded only in this text"
    )
    session_id: Optional[UUID] = Field(
        None,
        description="Session ID for conversation history. Generated if not provided."
    )
    filters: Optional[MetadataFilter] = Field(
        None,
        description="Optional filters for retrieval"
    )

    @field_validator('query')
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Query cannot be empty or whitespace only')
        return v.strip()
```

**Validation Rules**:
| Field | Rule | Error |
|-------|------|-------|
| query | Non-empty, non-whitespace, max 32000 chars | EMPTY_QUERY / QUERY_TOO_LONG |
| selected_text | Max 64000 chars (~16k tokens) | SELECTION_TOO_LONG |
| session_id | Valid UUID v4 if provided | INVALID_SESSION_ID |

---

## 2. Response Models

### ChatResponse

**Purpose**: Output payload for `/chat` endpoint.

**File**: `backend/models/response.py` (extend existing)

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class SourceCitation(BaseModel):
    """Citation from Qdrant retrieval."""
    source_url: str = Field(
        ...,
        description="Full URL to the book section"
    )
    title: str = Field(
        ...,
        description="Document/chapter title"
    )
    section: str = Field(
        ...,
        description="Section or heading name"
    )
    chunk_position: int = Field(
        ...,
        ge=0,
        description="Position of chunk within document"
    )
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Cosine similarity score"
    )
    snippet: str = Field(
        ...,
        max_length=200,
        description="First 200 chars of chunk_text for preview"
    )


class SelectedTextCitation(BaseModel):
    """Citation for selected-text mode responses."""
    source_type: str = Field(
        default="selected_text",
        description="Always 'selected_text' for this type"
    )
    selection_length: int = Field(
        ...,
        ge=0,
        description="Character count of provided selection"
    )
    snippet: str = Field(
        ...,
        max_length=200,
        description="First 200 chars of selection for preview"
    )
    relevance_note: str = Field(
        ...,
        description="How the selection relates to the answer"
    )


class ResponseMetadata(BaseModel):
    """Metadata about the response."""
    query_time_ms: float = Field(
        ...,
        ge=0,
        description="Total processing time in milliseconds"
    )
    retrieval_count: int = Field(
        ...,
        ge=0,
        description="Number of chunks retrieved from Qdrant"
    )
    mode: str = Field(
        ...,
        description="Response mode: 'full' | 'selected_text' | 'retrieval_only' | 'no_results'"
    )
    low_confidence: bool = Field(
        default=False,
        description="True if best results had scores 0.3-0.5"
    )
    request_id: UUID = Field(
        ...,
        description="UUID v4 for request tracing"
    )


class ChatResponse(BaseModel):
    """Complete response to chat request."""
    answer: Optional[str] = Field(
        None,
        description="AI-generated answer. Null if Gemini unavailable."
    )
    fallback_message: Optional[str] = Field(
        None,
        description="Message when answer is null (graceful degradation)"
    )
    sources: List[SourceCitation | SelectedTextCitation] = Field(
        default_factory=list,
        description="Citations for the answer"
    )
    metadata: ResponseMetadata = Field(
        ...,
        description="Response metadata including timing and mode"
    )
    session_id: UUID = Field(
        ...,
        description="Session ID (provided or newly generated)"
    )
```

---

### ErrorResponse

**Purpose**: Structured error response for all API errors.

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID


class ErrorResponse(BaseModel):
    """Structured error response."""
    error_code: str = Field(
        ...,
        description="Machine-readable error code",
        example="EMPTY_QUERY"
    )
    message: str = Field(
        ...,
        description="Human-readable error description",
        example="Query cannot be empty"
    )
    request_id: UUID = Field(
        ...,
        description="UUID v4 for request tracing"
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error context"
    )


# Error Code Constants
class ErrorCodes:
    EMPTY_QUERY = "EMPTY_QUERY"
    QUERY_TOO_LONG = "QUERY_TOO_LONG"
    SELECTION_TOO_LONG = "SELECTION_TOO_LONG"
    INVALID_SESSION_ID = "INVALID_SESSION_ID"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    QDRANT_UNAVAILABLE = "QDRANT_UNAVAILABLE"
    GEMINI_UNAVAILABLE = "GEMINI_UNAVAILABLE"
```

---

### HealthResponse

**Purpose**: Output for `/health` endpoint.

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ServiceStatus(BaseModel):
    """Status of a dependent service."""
    name: str
    status: str = Field(description="'healthy' | 'degraded' | 'unavailable'")
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(
        ...,
        description="Overall status: 'healthy' | 'degraded' | 'unavailable'"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp"
    )
    services: dict[str, ServiceStatus] = Field(
        default_factory=dict,
        description="Status of dependent services"
    )
    version: str = Field(
        default="0.1.0",
        description="API version"
    )
```

---

## 3. Session & Conversation Models

### Session

**Purpose**: Track user sessions for conversation history.

**Table**: `sessions`

```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class Session(BaseModel):
    """User session tracking."""
    session_id: UUID = Field(
        ...,
        description="Primary key - UUID v4"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Session creation timestamp"
    )
    last_active: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last activity timestamp"
    )
```

**SQL Schema**:
```sql
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active TIMESTAMPTZ DEFAULT NOW()
);
```

---

### ConversationRecord

**Purpose**: Store individual chat exchanges for history.

**Table**: `conversations`

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class ConversationRecord(BaseModel):
    """Stored chat exchange."""
    id: Optional[int] = Field(
        None,
        description="Auto-increment primary key"
    )
    session_id: UUID = Field(
        ...,
        description="Foreign key to sessions table"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the exchange occurred"
    )
    query: str = Field(
        ...,
        description="User's question"
    )
    response: str = Field(
        ...,
        description="Agent's answer"
    )
    sources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Citations as JSON"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Response metadata as JSON"
    )
```

**SQL Schema**:
```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(session_id),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    sources JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conversations_session ON conversations(session_id);
CREATE INDEX idx_conversations_timestamp ON conversations(timestamp DESC);
```

---

### ConversationHistoryResponse

**Purpose**: Output for `/history/{session_id}` endpoint.

```python
from pydantic import BaseModel, Field
from typing import List
from uuid import UUID


class HistoryEntry(BaseModel):
    """Single conversation turn."""
    timestamp: datetime
    query: str
    response: str
    sources: List[SourceCitation]


class ConversationHistoryResponse(BaseModel):
    """Conversation history for a session."""
    session_id: UUID
    entries: List[HistoryEntry] = Field(
        default_factory=list,
        description="Conversation history, oldest first"
    )
    total_entries: int = Field(
        ...,
        ge=0,
        description="Total number of entries"
    )
```

---

## 4. Internal Models (Agent Communication)

### RetrievalToolResult

**Purpose**: Structured result from `search_book_content` tool.

```python
from dataclasses import dataclass
from typing import List


@dataclass
class ChunkResult:
    """Single retrieved chunk."""
    chunk_text: str
    source_url: str
    title: str
    section: str
    similarity_score: float
    chunk_position: int


@dataclass
class RetrievalToolResult:
    """Tool output for agent."""
    results: List[ChunkResult]
    total_results: int
    message: str
```

**JSON Serialization** (returned to agent):
```json
{
    "results": [
        {
            "chunk_text": "...",
            "source_url": "https://...",
            "title": "...",
            "section": "...",
            "similarity_score": 0.85,
            "chunk_position": 1
        }
    ],
    "total_results": 5,
    "message": "Found 5 relevant passages"
}
```

---

## 5. State Transitions

### Request Processing States

```
┌─────────────┐
│  RECEIVED   │ Request validated, request_id assigned
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ RETRIEVING  │ Qdrant search in progress
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  GENERATING │ Agent processing query
└──────┬──────┘
       │
       ├────────────────┐
       ▼                ▼
┌─────────────┐  ┌─────────────┐
│  COMPLETED  │  │   FAILED    │
└─────────────┘  └─────────────┘
```

### Session States

```
New Request (no session_id)      Existing Session
        │                              │
        ▼                              ▼
┌──────────────┐              ┌──────────────┐
│    CREATE    │              │    UPDATE    │
│   SESSION    │              │  last_active │
└──────────────┘              └──────────────┘
        │                              │
        └──────────────┬───────────────┘
                       ▼
              ┌──────────────┐
              │    STORE     │
              │ CONVERSATION │
              └──────────────┘
```

---

## 6. Validation Summary

### Input Validation Matrix

| Model | Field | Validation | HTTP Code |
|-------|-------|------------|-----------|
| ChatRequest | query | non-empty, max 32000 | 400 |
| ChatRequest | selected_text | max 64000 | 400 |
| ChatRequest | session_id | valid UUID v4 | 400 |
| MetadataFilter | source_url_prefix | valid URL prefix | 400 |

### Output Constraints

| Model | Field | Constraint |
|-------|-------|------------|
| SourceCitation | snippet | max 200 chars |
| SourceCitation | similarity_score | 0.0-1.0 |
| ResponseMetadata | mode | enum: full, selected_text, retrieval_only, no_results |
| ChatResponse | session_id | always present (provided or generated) |

---

## 7. File Organization

```
backend/models/
├── __init__.py          # Export all models
├── query.py             # Existing - GoldenTestQuery
├── response.py          # Existing + new chat response models
├── request.py           # NEW - ChatRequest, MetadataFilter
├── session.py           # NEW - Session, ConversationRecord
└── health.py            # NEW - HealthResponse, ServiceStatus
```
