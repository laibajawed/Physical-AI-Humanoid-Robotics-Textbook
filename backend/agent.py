"""
OpenAI Agents SDK agent for Physical AI & Robotics book Q&A.

Uses Gemini 2.0 Flash via OpenAI-compatible endpoint for response generation.
Wraps existing retrieve.py functions with @function_tool decorator.
"""

import json
import os
from typing import Any, Dict, List, Optional
from uuid import UUID

from dotenv import load_dotenv
from openai import AsyncOpenAI

from agents import Agent, Runner, function_tool
from agents.run import RunConfig
from agents.model_settings import ModelSettings
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

from models.response import SourceCitation, SelectedTextCitation


# =============================================================================
# Constants
# =============================================================================

# Confidence thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.5
LOW_CONFIDENCE_THRESHOLD = 0.3

# Limits
MAX_RETRIEVAL_RESULTS = 10
DEFAULT_RETRIEVAL_RESULTS = 5
DEFAULT_SCORE_THRESHOLD = 0.5

# Gemini configuration
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_TIMEOUT = 120  # seconds


# =============================================================================
# Agent Instructions
# =============================================================================

BASE_INSTRUCTIONS = """You are a helpful assistant for the Physical AI & Robotics textbook.
You help users understand concepts from the book by answering questions accurately and citing sources.

Guidelines:
1. Always use the search_book_content tool to find relevant information before answering.
2. Base your answers ONLY on the retrieved content - do not use outside knowledge.
3. When citing sources, mention the section or chapter name.
4. If the retrieved content doesn't contain relevant information, say so honestly.
5. Be concise but thorough in your explanations.
6. If asked about topics outside the book's scope (like general knowledge questions), politely indicate this is a textbook assistant and suggest they ask robotics-related questions.

When answering:
- Reference specific passages from the retrieved content
- Explain concepts clearly for someone learning robotics
- If multiple sources are relevant, synthesize information from all of them
"""

SELECTED_TEXT_INSTRUCTIONS = """You are answering questions about the following selected text ONLY.
DO NOT use the search_book_content tool - it has been disabled for this request.
DO NOT reference information outside this selection.
Base your answer ENTIRELY on the provided text.

If the answer cannot be found in the selected text, respond with:
"This question cannot be answered from the selected text. The selection discusses [brief summary of what it does discuss]."

Selected text:
---
{selected_text}
---

Answer questions about this text clearly and concisely.
"""

OUT_OF_SCOPE_SUGGESTION = """

I'm an assistant for the Physical AI & Robotics textbook. I can help you with topics like:
- Robot motion planning and inverse kinematics
- ROS2 fundamentals and navigation
- Simulation with Gazebo and Unity
- NVIDIA Isaac SDK
- Vision-language-action systems
- Sensor fusion and control systems

Would you like to ask about any of these topics?"""


# =============================================================================
# Gemini Client Setup
# =============================================================================

_external_client: Optional[AsyncOpenAI] = None


def _get_gemini_client() -> AsyncOpenAI:
    """
    Get or create AsyncOpenAI client configured for Gemini.

    Returns:
        AsyncOpenAI client pointing to Gemini endpoint

    Raises:
        EnvironmentError: If GEMINI_API_KEY not set
    """
    global _external_client

    if _external_client is None:
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("Missing required environment variable: GEMINI_API_KEY")

        _external_client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            timeout=GEMINI_TIMEOUT,

        )

    return _external_client


# =============================================================================
# Retrieval Tool
# =============================================================================

@function_tool
async def search_book_content(
    query: str,
    limit: int = DEFAULT_RETRIEVAL_RESULTS,
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    source_url_prefix: Optional[str] = None,
    section: Optional[str] = None,
) -> str:
    """Search the Physical AI & Robotics book for relevant content.

    Use this tool to find information from the textbook before answering questions.
    Always search for relevant content before providing an answer.

    Args:
        query: Natural language search query describing what you're looking for
        limit: Maximum number of results to return (1-10, default 5)
        score_threshold: Minimum similarity score (0.0-1.0, default 0.5)
        source_url_prefix: Optional filter for URL prefix (e.g., "/docs/module1")
        section: Optional filter for specific section name (exact match)

    Returns:
        JSON string with retrieved passages and metadata
    """
    # Import here to avoid circular imports
    from retrieve import search

    # Clamp parameters to valid ranges
    limit = max(1, min(limit, MAX_RETRIEVAL_RESULTS))
    score_threshold = max(0.0, min(score_threshold, 1.0))

    try:
        response = await search(
            query_text=query,
            limit=limit,
            score_threshold=score_threshold,
            source_url_filter=source_url_prefix,
            section_filter=section,
        )

        results = []
        for r in response.results:
            results.append({
                "chunk_text": r.chunk_text,
                "source_url": r.source_url,
                "title": r.title,
                "section": r.section,
                "similarity_score": r.similarity_score,
                "chunk_position": r.chunk_position,
            })

        return json.dumps({
            "results": results,
            "total_results": response.total_results,
            "query_time_ms": response.query_time_ms,
            "message": f"Found {response.total_results} relevant passages" if results else "No relevant passages found",
        })

    except Exception as e:
        return json.dumps({
            "results": [],
            "total_results": 0,
            "error": str(e),
            "message": f"Search failed: {str(e)}",
        })


# =============================================================================
# Agent Builder
# =============================================================================

def build_agent(
    selected_text: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Agent:
    """
    Build an agent configured for the current request.

    Args:
        selected_text: If provided, agent answers only from this text
        conversation_history: Optional list of previous messages for context

    Returns:
        Configured Agent instance
    """
    client = _get_gemini_client()

    # Create model wrapper for Gemini via OpenAI-compatible endpoint
    model = OpenAIChatCompletionsModel(
        model=GEMINI_MODEL,
        openai_client=client,
    )

    # Build instructions based on mode
    if selected_text:
        instructions = BASE_INSTRUCTIONS + "\n\n" + SELECTED_TEXT_INSTRUCTIONS.format(
            selected_text=selected_text[:32000]  # Truncate if needed
        )
        tools = []  # No search tool in selected-text mode
    else:
        instructions = BASE_INSTRUCTIONS
        tools = [search_book_content]

    return Agent(
        name="BookAssistant",
        instructions=instructions,
        model=model,
        tools=tools,
    )


# =============================================================================
# Agent Execution
# =============================================================================

async def run_agent(
    query: str,
    selected_text: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    filters: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Execute agent with query and return structured result.

    Args:
        query: User's question
        selected_text: If provided, constrains answer to this text
        conversation_history: Optional conversation context
        filters: Optional metadata filters for retrieval

    Returns:
        Dict with keys: answer, tool_results, error
    """
    agent = build_agent(
        selected_text=selected_text,
        conversation_history=conversation_history,
    )

    # Build run config - disable tracing for privacy
    config = RunConfig(
        tracing_disabled=True,
    )

    try:
        # Run the agent
        result = await Runner.run(
            agent,
            input=query,
            run_config=config,
        )

        # Extract tool call results for citation validation
        tool_results = []
        if hasattr(result, "new_items"):
            for item in result.new_items:
                if hasattr(item, "raw_item") and hasattr(item.raw_item, "type"):
                    if item.raw_item.type == "function_call_output":
                        try:
                            parsed = json.loads(item.raw_item.output)
                            if "results" in parsed:
                                tool_results.extend(parsed["results"])
                        except (json.JSONDecodeError, AttributeError):
                            pass

        return {
            "answer": result.final_output,
            "tool_results": tool_results,
            "error": None,
        }

    except Exception as e:
        return {
            "answer": None,
            "tool_results": [],
            "error": str(e),
        }


# =============================================================================
# Citation Extraction and Validation
# =============================================================================

def extract_and_validate_citations(
    agent_output: str,
    tool_results: List[Dict[str, Any]],
) -> List[SourceCitation]:
    """
    Extract citations from tool results.

    Only includes citations that appear in tool results (no hallucination).
    Deduplicates by source_url + chunk_position.

    Args:
        agent_output: The agent's text response (used for validation)
        tool_results: List of retrieval results from tool calls

    Returns:
        List of validated SourceCitation objects
    """
    if not tool_results:
        return []

    citations = []
    seen = set()

    for result in tool_results:
        # Create deduplication key
        key = (result.get("source_url", ""), result.get("chunk_position", 0))
        if key in seen:
            continue
        seen.add(key)

        # Generate snippet (first 200 chars)
        chunk_text = result.get("chunk_text", "")
        snippet = chunk_text[:200].strip()
        if len(chunk_text) > 200:
            snippet += "..."

        citations.append(SourceCitation(
            source_url=result.get("source_url", ""),
            title=result.get("title", ""),
            section=result.get("section", ""),
            chunk_position=result.get("chunk_position", 0),
            similarity_score=result.get("similarity_score", 0.0),
            snippet=snippet[:200],  # Ensure max length
        ))

    return citations


def create_selected_text_citation(
    selected_text: str,
    relevance_note: str = "Answer derived from provided selection",
) -> SelectedTextCitation:
    """
    Create citation for selected-text mode response.

    Args:
        selected_text: The user's selected text
        relevance_note: Description of relevance

    Returns:
        SelectedTextCitation object
    """
    snippet = selected_text[:200].strip()
    if len(selected_text) > 200:
        snippet += "..."

    return SelectedTextCitation(
        source_type="selected_text",
        selection_length=len(selected_text),
        snippet=snippet[:200],
        relevance_note=relevance_note,
    )


def determine_confidence(tool_results: List[Dict[str, Any]]) -> tuple[bool, str]:
    """
    Determine confidence level and response mode from tool results.

    Args:
        tool_results: List of retrieval results

    Returns:
        Tuple of (low_confidence, mode)
        - low_confidence: True if scores between 0.3-0.5
        - mode: "full" | "no_results" | "low_confidence"
    """
    if not tool_results:
        return False, "no_results"

    max_score = max(r.get("similarity_score", 0) for r in tool_results)

    if max_score >= HIGH_CONFIDENCE_THRESHOLD:
        return False, "full"
    elif max_score >= LOW_CONFIDENCE_THRESHOLD:
        return True, "full"
    else:
        return True, "no_results"


# =============================================================================
# Fallback Responses
# =============================================================================

def get_fallback_answer(
    tool_results: List[Dict[str, Any]],
    error: Optional[str] = None,
) -> str:
    """
    Generate fallback answer when agent is unavailable.

    Args:
        tool_results: Retrieved content from Qdrant
        error: Optional error message

    Returns:
        Fallback answer text
    """
    if error:
        if tool_results:
            # Return retrieval results as-is
            sections = set()
            for r in tool_results[:3]:
                sections.add(r.get("section", "Unknown"))

            return (
                f"I found relevant content in the following sections: {', '.join(sections)}. "
                "However, I'm currently unable to generate a detailed response. "
                "Please check the sources below for the information you need."
            )
        else:
            return "I'm currently unable to search the textbook. Please try again in a moment."

    if not tool_results:
        return (
            "I couldn't find relevant information in the textbook to answer your question."
            + OUT_OF_SCOPE_SUGGESTION
        )

    return None  # No fallback needed


def get_out_of_scope_response() -> str:
    """
    Get response for out-of-scope questions.

    Returns:
        Polite decline with suggestions
    """
    return (
        "I couldn't find relevant information in the Physical AI & Robotics textbook "
        "to answer this question. This might be outside the scope of the textbook content."
        + OUT_OF_SCOPE_SUGGESTION
    )


# =============================================================================
# Streaming Agent Execution (T071)
# =============================================================================

async def run_agent_streamed(
    query: str,
    selected_text: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    filters: Optional[Dict[str, str]] = None,
):
    """
    Execute agent with streaming response using Runner.run_streamed().

    Yields events as they occur:
    - {"type": "delta", "content": "..."} for text chunks
    - {"type": "tool_call", "name": "...", "output": {...}} for tool calls
    - {"type": "sources", "data": [...]} for citations at the end
    - {"type": "done", "answer": "..."} when complete
    - {"type": "error", "message": "..."} on error

    Args:
        query: User's question
        selected_text: If provided, constrains answer to this text
        conversation_history: Optional conversation context
        filters: Optional metadata filters for retrieval

    Yields:
        Dict events for streaming
    """
    from openai.types.responses import ResponseTextDeltaEvent

    agent = build_agent(
        selected_text=selected_text,
        conversation_history=conversation_history,
    )

    config = RunConfig(
        tracing_disabled=True,
    )

    tool_results = []
    full_answer = ""

    try:
        result = Runner.run_streamed(
            agent,
            input=query,
            run_config=config,
        )

        async for event in result.stream_events():
            if event.type == "raw_response_event":
                if isinstance(event.data, ResponseTextDeltaEvent):
                    delta_text = event.data.delta
                    if delta_text:
                        full_answer += delta_text
                        yield {"type": "delta", "content": delta_text}

            elif event.type == "run_item_stream_event":
                if hasattr(event, "item"):
                    if event.item.type == "tool_call_output_item":
                        try:
                            parsed = json.loads(event.item.output)
                            if "results" in parsed:
                                tool_results.extend(parsed["results"])
                            yield {
                                "type": "tool_call",
                                "name": "search_book_content",
                                "output": parsed,
                            }
                        except (json.JSONDecodeError, AttributeError):
                            pass

        final_output = result.final_output if hasattr(result, "final_output") else full_answer

        if tool_results:
            citations = extract_and_validate_citations(final_output or "", tool_results)
            yield {
                "type": "sources",
                "data": [c.model_dump() for c in citations],
            }
        elif selected_text:
            citation = create_selected_text_citation(
                selected_text,
                "Answer derived from provided selection",
            )
            yield {
                "type": "sources",
                "data": [citation.model_dump()],
            }

        yield {
            "type": "done",
            "answer": final_output or full_answer,
            "tool_results": tool_results,
        }

    except Exception as e:
        yield {"type": "error", "message": str(e)}
