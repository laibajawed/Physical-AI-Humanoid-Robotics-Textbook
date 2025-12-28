# Research: RAG Agent API (Spec-3)

**Feature**: 005-rag-agent-api
**Date**: 2025-12-17
**Status**: Complete

## 1. OpenAI Agents SDK Integration with Gemini

### Decision
Use `OpenAIChatCompletionsModel` with custom `AsyncOpenAI` client pointing to Gemini's OpenAI-compatible endpoint.

### Rationale
- Gemini provides OpenAI-compatible endpoint at `https://generativelanguage.googleapis.com/v1beta/openai/`
- This allows using OpenAI Agents SDK with Gemini models without code changes
- Pattern validated in `.specify/memory/openai-knowledge.md`
- Lower cost than OpenAI with comparable performance for RAG tasks

### Implementation Pattern
```python
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, RunConfig, function_tool
from openai import AsyncOpenAI

external_client = AsyncOpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

config = RunConfig(
    model=model,
    model_provider=external_client,
    tracing_disabled=True  # Privacy
)
```

### Alternatives Considered
1. **LitellmModel wrapper** - More abstraction but adds dependency
2. **Direct Gemini SDK** - Would require custom agent implementation
3. **OpenAI GPT-4o** - Higher cost, similar performance

---

## 2. Streaming vs Non-Streaming Decision

### Decision
Implement **both** endpoints:
- `POST /chat` - Non-streaming (default, simpler integration)
- `POST /chat/stream` - SSE streaming (better UX for long responses)

### Rationale
- Non-streaming is simpler for testing and integration
- Streaming improves perceived latency for long responses
- FastAPI supports both patterns well with `StreamingResponse`

### Implementation Pattern (Non-Streaming)
```python
result = await Runner.run(agent, input=query, run_config=config)
return ChatResponse(answer=result.final_output, sources=...)
```

### Implementation Pattern (Streaming)
```python
from fastapi.responses import StreamingResponse
from openai.types.responses import ResponseTextDeltaEvent

async def stream_response():
    result = Runner.run_streamed(agent, input=query, run_config=config)
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            yield f"data: {json.dumps({'delta': event.data.delta})}\n\n"
    yield f"data: {json.dumps({'done': True, 'sources': sources})}\n\n"

return StreamingResponse(stream_response(), media_type="text/event-stream")
```

### Alternatives Considered
1. **WebSocket** - More complex, not needed for request-response pattern
2. **Streaming only** - Would complicate simple integrations

---

## 3. Tool Interface (search_book_content)

### Decision
Define a `@function_tool` decorated async function that wraps existing `retrieve.search()`.

### Rationale
- Reuses existing, tested retrieval implementation
- OpenAI Agents SDK expects tools to return strings (JSON serialized)
- Docstring becomes tool description for the LLM

### Implementation Pattern
```python
@function_tool
async def search_book_content(
    query: str,
    limit: int = 5,
    score_threshold: float = 0.5
) -> str:
    """Search the Physical AI & Robotics book for relevant content.

    Args:
        query: Natural language search query
        limit: Maximum results to return (1-10)
        score_threshold: Minimum similarity score (0.0-1.0)

    Returns:
        JSON string with retrieved chunks and metadata
    """
    from retrieve import search
    response = await search(
        query_text=query,
        limit=min(limit, 10),
        score_threshold=score_threshold
    )
    return json.dumps({
        "results": [
            {
                "chunk_text": r.chunk_text,
                "source_url": r.source_url,
                "title": r.title,
                "section": r.section,
                "similarity_score": r.similarity_score,
                "chunk_position": r.chunk_position
            }
            for r in response.results
        ],
        "total_results": response.total_results,
        "message": f"Found {response.total_results} relevant passages"
    })
```

### Input Schema (for LLM)
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Natural language search query |
| limit | integer | No | Max results (1-10, default 5) |
| score_threshold | float | No | Min similarity (0-1, default 0.5) |

### Output Schema
```json
{
  "results": [
    {
      "chunk_text": "string",
      "source_url": "string",
      "title": "string",
      "section": "string",
      "similarity_score": 0.85,
      "chunk_position": 1
    }
  ],
  "total_results": 5,
  "message": "Found 5 relevant passages"
}
```

---

## 4. Citation Payload Shape

### Decision
Structured citation format with snippet preview and all source metadata.

### Rationale
- Frontend needs structured data for rendering citation chips/links
- Snippet allows hover preview without full chunk text
- Similarity score enables confidence indicators

### Schema
```json
{
  "source_url": "https://book.example.com/docs/module1/chapter3",
  "title": "Motion Planning Fundamentals",
  "section": "Inverse Kinematics",
  "chunk_position": 5,
  "similarity_score": 0.87,
  "snippet": "First 200 characters of chunk_text for preview..."
}
```

### Selected-Text Citation Schema
```json
{
  "source_type": "selected_text",
  "selection_length": 1500,
  "snippet": "First 200 characters of user's selected text...",
  "relevance_note": "Answer derived from provided selection"
}
```

---

## 5. Selected-Text-Only Enforcement Strategy

### Decision
Use **dynamic agent instructions** to enforce selected-text mode.

### Rationale
- Agent instructions can be modified per-request
- Simpler than creating two separate agents
- Explicitly tells LLM not to use search tool when selection is provided

### Implementation Pattern
```python
BASE_INSTRUCTIONS = """You are a helpful assistant for the Physical AI & Robotics textbook.
Always cite sources when answering questions.
If you cannot find relevant information, say so honestly."""

SELECTED_TEXT_INSTRUCTIONS = """You are answering questions about the following selected text ONLY.
DO NOT use the search_book_content tool.
DO NOT reference information outside this selection.
If the answer is not in the selection, respond with "This question cannot be answered from the selected text."

Selected text:
---
{selected_text}
---
"""

def build_agent(selected_text: str | None = None) -> Agent:
    if selected_text:
        instructions = BASE_INSTRUCTIONS + "\n\n" + SELECTED_TEXT_INSTRUCTIONS.format(
            selected_text=selected_text
        )
        tools = []  # No search tool in selected-text mode
    else:
        instructions = BASE_INSTRUCTIONS
        tools = [search_book_content]

    return Agent(
        name="BookAssistant",
        instructions=instructions,
        model=model,
        tools=tools
    )
```

### Alternatives Considered
1. **Two separate agents** - More duplication, harder to maintain
2. **Guardrail function** - More complex, not needed for this use case
3. **Post-processing filter** - Would not prevent tool calls

---

## 6. Error/Fallback Behavior

### Decision
Implement graceful degradation with explicit fallback modes.

### Scenarios and Responses

| Scenario | Response |
|----------|----------|
| Empty query | 400 Bad Request: `{"error_code": "EMPTY_QUERY", "message": "Query cannot be empty"}` |
| Qdrant unavailable | 503 Service Unavailable with retry-after header, 3 retries with exponential backoff |
| Gemini unavailable | Return retrieval results only: `{"answer": null, "fallback_message": "AI summarization unavailable", "sources": [...]}` |
| No relevant results | Agent responds: "I couldn't find relevant information in the book to answer this question" |
| Low-confidence results | Include results with `low_confidence: true` flag in metadata (scores 0.3-0.5) |
| Rate limit exceeded | 429 Too Many Requests with retry-after header |

### Implementation Pattern (Gemini Fallback)
```python
try:
    result = await Runner.run(agent, input=query, run_config=config)
    return ChatResponse(answer=result.final_output, sources=sources)
except Exception as e:
    if is_gemini_error(e):
        # Graceful degradation - return search results only
        search_results = await search(query)
        return ChatResponse(
            answer=None,
            fallback_message="AI summarization unavailable",
            sources=format_citations(search_results),
            metadata={"mode": "retrieval_only"}
        )
    raise
```

---

## 7. Logging/Tracing Plan

### Decision
JSON structured logging with request correlation via request_id (UUID v4).

### Rationale
- JSON logs enable easy parsing by log aggregators
- Request ID enables tracing across service calls
- Matches existing pattern in retrieve.py

### Log Entry Schema
```json
{
  "timestamp": "2025-12-17T10:30:00.000Z",
  "level": "INFO",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "chat|retrieval|agent|response",
  "message": "Human-readable description",
  "latency_ms": 1234.56,
  "query_length": 150,
  "result_count": 5,
  "error": null
}
```

### Key Log Points
1. Request received (INFO)
2. Retrieval started/completed (DEBUG/INFO)
3. Agent execution started/completed (DEBUG/INFO)
4. Response sent (INFO)
5. Errors (ERROR with stack trace)

### Tracing Disabled
Per spec FR-004, `tracing_disabled=True` in RunConfig to avoid sending data to OpenAI servers.

---

## 8. "No Hallucinated Citations" Rule

### Decision
Citations are extracted from tool call results only, never generated by the agent.

### Implementation Strategy
1. Agent generates text answer with inline references
2. Parse agent output to extract any source references
3. Validate references exist in tool call results
4. Only include validated citations in response

### Pattern
```python
def extract_and_validate_citations(
    agent_output: str,
    tool_results: list[dict]
) -> list[SourceCitation]:
    """
    Extract citations from agent output and validate against tool results.
    Only return citations that match actual retrieved chunks.
    """
    valid_sources = {r["source_url"] for r in tool_results}
    citations = []

    for result in tool_results:
        if result["source_url"] in agent_output or result["title"] in agent_output:
            citations.append(SourceCitation(
                source_url=result["source_url"],
                title=result["title"],
                section=result["section"],
                chunk_position=result["chunk_position"],
                similarity_score=result["similarity_score"],
                snippet=result["chunk_text"][:200]
            ))

    return citations
```

---

## 9. Handle Empty/Low-Confidence Retrieval

### Decision
Use tiered response strategy based on retrieval quality.

### Thresholds
- **High confidence**: score >= 0.5 (default)
- **Low confidence**: 0.3 <= score < 0.5
- **No confidence**: score < 0.3 (excluded)

### Response Patterns

**No results (empty retrieval)**:
```json
{
  "answer": "I couldn't find relevant information in the book to answer this question. Could you try rephrasing or asking about a different robotics topic?",
  "sources": [],
  "metadata": {
    "mode": "no_results",
    "retrieval_count": 0
  }
}
```

**Low-confidence results only**:
```json
{
  "answer": "Based on limited relevant content I found...",
  "sources": [...],
  "metadata": {
    "mode": "low_confidence",
    "low_confidence": true,
    "retrieval_count": 3
  }
}
```

---

## 10. Testing Strategy

### API Smoke Tests

| Test | Endpoint | Expected |
|------|----------|----------|
| Basic chat | POST /chat | 200 with answer and sources |
| Selected-text mode | POST /chat (with selected_text) | 200, no Qdrant queries |
| Empty query | POST /chat | 400 EMPTY_QUERY error |
| Health check | GET /health | 200 with Qdrant status |
| Streaming | POST /chat/stream | SSE events |
| Rate limit | 11+ concurrent | 429 on 11th request |

### Deterministic Test Prompts

```python
TEST_CASES = [
    {
        "query": "What is inverse kinematics?",
        "expected_sources_contain": ["module1", "robotics"],
        "min_sources": 1
    },
    {
        "query": "Explain sensor fusion",
        "expected_sources_contain": ["module4", "vla"],
        "min_sources": 1
    },
    {
        "query": "What is the capital of France?",
        "expected_behavior": "out_of_scope_response"
    }
]
```

### Qdrant Connectivity Check
```python
async def test_qdrant_connectivity():
    stats = await get_collection_stats()
    assert stats.vector_count > 0
    assert stats.index_status == "green"
```

---

## Dependencies Summary

### New Dependencies (add to pyproject.toml)
```toml
[project]
dependencies = [
    # Existing
    "beautifulsoup4>=4.14.3",
    "cohere>=5.20.0",
    "httpx>=0.28.1",
    "lxml>=6.0.2",
    "python-dotenv>=1.2.1",
    "qdrant-client>=1.16.2",
    # New for Spec-3
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "openai-agents>=0.2.0",
    "openai>=1.60.0",  # AsyncOpenAI
    "sqlalchemy>=2.0.36",
    "asyncpg>=0.30.0",
    "pydantic>=2.10.0",
]
```

### Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| GEMINI_API_KEY | Yes | Gemini API key for agent LLM |
| QDRANT_URL | Yes | Qdrant Cloud cluster URL |
| QDRANT_API_KEY | Yes | Qdrant API key |
| COHERE_API_KEY | Yes | Cohere API key for embeddings |
| DATABASE_URL | Yes | Neon Postgres connection string |
