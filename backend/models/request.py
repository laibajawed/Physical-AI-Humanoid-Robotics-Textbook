"""
Request models for RAG Agent API.

Contains Pydantic models for API request validation.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class MetadataFilter(BaseModel):
    """Optional filters for retrieval."""

    source_url_prefix: Optional[str] = Field(
        None,
        description="Filter results to URLs starting with this prefix",
        examples=["/docs/module1"],
    )
    section: Optional[str] = Field(
        None,
        description="Filter results to specific section name (exact match)",
        examples=["Inverse Kinematics"],
    )


class ChatRequest(BaseModel):
    """Input payload for /chat and /chat/stream endpoints."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=32000,
        description="Natural language question about the book",
        examples=["What is inverse kinematics?"],
    )
    selected_text: Optional[str] = Field(
        None,
        max_length=64000,
        description="If provided, answer is grounded only in this text (no Qdrant search)",
    )
    session_id: Optional[UUID] = Field(
        None,
        description="Session ID for conversation history. Generated if not provided.",
    )
    filters: Optional[MetadataFilter] = Field(
        None,
        description="Optional filters for retrieval",
    )

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        """Validate query is not empty or whitespace only."""
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()

    @field_validator("selected_text")
    @classmethod
    def selected_text_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate selected_text is not just whitespace if provided."""
        if v is not None and not v.strip():
            raise ValueError("Selected text cannot be empty or whitespace only")
        return v.strip() if v else None
