"""
Session and conversation history models for RAG Agent API.

Contains Pydantic models for session tracking and conversation history.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from uuid import UUID


class Session(BaseModel):
    """User session tracking."""

    session_id: UUID = Field(
        ...,
        description="Primary key - UUID v4",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Session creation timestamp",
    )
    last_active: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last activity timestamp",
    )


class ConversationRecord(BaseModel):
    """Stored chat exchange."""

    id: Optional[int] = Field(
        None,
        description="Auto-increment primary key",
    )
    session_id: UUID = Field(
        ...,
        description="Foreign key to sessions table",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the exchange occurred",
    )
    query: str = Field(
        ...,
        description="User's question",
    )
    response: str = Field(
        ...,
        description="Agent's answer",
    )
    sources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Citations as JSON",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Response metadata as JSON",
    )


class HistoryEntry(BaseModel):
    """Single conversation turn for history response."""

    timestamp: datetime = Field(..., description="When the exchange occurred")
    query: str = Field(..., description="User's question")
    response: str = Field(..., description="Agent's answer")
    sources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Citations for the answer",
    )


class ConversationHistoryResponse(BaseModel):
    """Conversation history for /history/{session_id} endpoint."""

    session_id: UUID = Field(..., description="Session UUID")
    entries: List[HistoryEntry] = Field(
        default_factory=list,
        description="Conversation history, oldest first",
    )
    total_entries: int = Field(
        ...,
        ge=0,
        description="Total number of entries",
    )
