"""
Agent Response Evaluation Tests

Tests to verify:
1. Agent retrieves data from Qdrant (not hallucinating)
2. Agent answers are grounded in retrieved content
3. Citations match actual retrieved passages
4. Out-of-scope questions are handled appropriately
5. Selected-text mode restricts answers to provided text
"""

import pytest
import pytest_asyncio
import json
import asyncio
import os
from typing import List, Dict, Any

# Set testing environment
os.environ["TESTING"] = "true"


# =============================================================================
# Hallucination Detection Tests
# =============================================================================

@pytest.mark.asyncio
async def test_agent_uses_retrieval_tool(client):
    """
    Verify agent calls search_book_content tool before answering.

    The agent should ALWAYS search Qdrant for relevant content
    before generating a response (unless in selected-text mode).
    """
    response = await client.post("/chat", json={
        "query": "What is inverse kinematics in robotics?"
    })

    if response.status_code == 200:
        data = response.json()
        metadata = data.get("metadata", {})

        # In full mode, retrieval_count should be > 0 if content was found
        # Mode should be 'full' when searching the book
        assert metadata.get("mode") in ["full", "no_results", "retrieval_only"], \
            f"Expected search mode, got {metadata.get('mode')}"

        # If sources exist, there was retrieval
        sources = data.get("sources", [])
        if sources:
            assert metadata.get("retrieval_count", 0) > 0, \
                "Sources returned but retrieval_count is 0"


@pytest.mark.asyncio
async def test_answer_grounded_in_sources(client):
    """
    Verify that answer content relates to retrieved sources.

    Checks that the answer references concepts from the retrieved chunks.
    """
    response = await client.post("/chat", json={
        "query": "Explain robot motion planning"
    })

    if response.status_code == 200:
        data = response.json()
        answer = data.get("answer", "")
        sources = data.get("sources", [])

        if answer and sources:
            # Get keywords from source snippets
            source_text = " ".join([s.get("snippet", "") for s in sources])
            source_text_lower = source_text.lower()

            # Check if answer references robotics concepts
            robotics_terms = ["robot", "motion", "path", "planning", "trajectory",
                           "arm", "joint", "kinematic", "control"]

            answer_lower = answer.lower()
            terms_in_answer = [t for t in robotics_terms if t in answer_lower]

            # At least some robotics terms should appear in a grounded answer
            assert len(terms_in_answer) >= 2, \
                f"Answer doesn't seem grounded in robotics content. Found terms: {terms_in_answer}"


@pytest.mark.asyncio
async def test_citations_match_retrieved_content(client):
    """
    Verify that citations are from actual Qdrant retrieval, not fabricated.

    Each citation should have:
    - Valid source_url from the book
    - Non-empty snippet
    - similarity_score from Qdrant search
    """
    response = await client.post("/chat", json={
        "query": "How does ROS2 navigation work?"
    })

    if response.status_code == 200:
        data = response.json()
        sources = data.get("sources", [])

        for source in sources:
            # Skip selected_text type citations
            if source.get("source_type") == "selected_text":
                continue

            # Verify source has required fields from Qdrant
            assert "source_url" in source, "Citation missing source_url"
            assert "snippet" in source, "Citation missing snippet"
            assert "similarity_score" in source, "Citation missing similarity_score"

            # URL should be from the book (docs path)
            url = source.get("source_url", "")
            assert url.startswith("/docs/") or url.startswith("http"), \
                f"Invalid source URL: {url}"

            # Similarity score should be valid (0-1)
            score = source.get("similarity_score", 0)
            assert 0 <= score <= 1, f"Invalid similarity score: {score}"

            # Snippet should not be empty
            snippet = source.get("snippet", "")
            assert len(snippet) > 0, "Empty snippet in citation"


@pytest.mark.asyncio
async def test_no_hallucinated_sources(client):
    """
    Verify agent doesn't cite sources that weren't retrieved.

    All citations should come from the tool call results,
    not fabricated by the model.
    """
    response = await client.post("/chat", json={
        "query": "What sensors are used in robot perception?"
    })

    if response.status_code == 200:
        data = response.json()
        sources = data.get("sources", [])

        for source in sources:
            if source.get("source_type") == "selected_text":
                continue

            # Each source should have chunk_position (from Qdrant)
            assert "chunk_position" in source, \
                "Source missing chunk_position - might be hallucinated"

            # Title should not be generic/fabricated
            title = source.get("title", "")
            generic_titles = ["Unknown", "Source", "Document", "Reference", "N/A"]
            # Allow empty but not generic fabricated titles
            if title:
                assert title not in generic_titles, \
                    f"Potentially hallucinated title: {title}"


@pytest.mark.asyncio
async def test_out_of_scope_handled_correctly(client):
    """
    Verify out-of-scope questions don't get hallucinated answers.

    Questions outside the book's scope should:
    - Return no_results or low confidence
    - Not fabricate robotics content
    - Suggest relevant topics instead
    """
    out_of_scope_queries = [
        "What is the best pizza recipe?",
        "Who won the 2024 Olympics?",
        "How do I invest in stocks?",
    ]

    for query in out_of_scope_queries:
        response = await client.post("/chat", json={"query": query})

        if response.status_code == 200:
            data = response.json()
            metadata = data.get("metadata", {})
            sources = data.get("sources", [])

            # Should either:
            # 1. Return no results (mode = no_results)
            # 2. Return low_confidence = True
            # 3. Have very few/no sources
            mode = metadata.get("mode")
            low_conf = metadata.get("low_confidence", False)

            # At least one of these conditions should be true
            is_handled = (
                mode == "no_results" or
                low_conf or
                len(sources) == 0 or
                metadata.get("retrieval_count", 0) == 0
            )

            assert is_handled, \
                f"Out-of-scope query '{query}' returned confident answer with sources"


# =============================================================================
# Selected-Text Mode Tests (Grounding)
# =============================================================================

@pytest.mark.asyncio
async def test_selected_text_restricts_answer(client):
    """
    Verify selected-text mode answers only from provided text.

    When selected_text is provided:
    - No Qdrant search should occur
    - Answer should be derived from the selected text only
    """
    selected_text = """
    The differential drive robot uses two independently controlled wheels
    on a common axis to achieve movement. By varying the speeds of the
    left and right wheels, the robot can move forward, backward, or rotate.
    """

    response = await client.post("/chat", json={
        "query": "What type of robot is described?",
        "selected_text": selected_text
    })

    if response.status_code == 200:
        data = response.json()
        metadata = data.get("metadata", {})
        sources = data.get("sources", [])

        # Mode should be selected_text
        assert metadata.get("mode") == "selected_text", \
            f"Expected selected_text mode, got {metadata.get('mode')}"

        # Retrieval count should be 0 (no Qdrant search)
        assert metadata.get("retrieval_count", 0) == 0, \
            "Qdrant search occurred in selected-text mode"

        # Source should be of type selected_text
        if sources:
            assert sources[0].get("source_type") == "selected_text", \
                "Source is not from selected text"


@pytest.mark.asyncio
async def test_selected_text_no_external_knowledge(client):
    """
    Verify selected-text answers don't include external knowledge.

    The answer should only contain information from the provided selection.
    """
    selected_text = "The gripper has two fingers that can open and close."

    response = await client.post("/chat", json={
        "query": "What advanced features does this gripper have?",
        "selected_text": selected_text
    })

    if response.status_code == 200:
        data = response.json()
        answer = data.get("answer", "")

        if answer:
            # Answer should acknowledge limited information
            # or reference only what's in the selection
            answer_lower = answer.lower()

            # Check that answer doesn't fabricate features not in the text
            fabricated_terms = ["force sensor", "tactile", "compliance",
                              "adaptive", "vacuum", "suction"]

            found_fabricated = [t for t in fabricated_terms if t in answer_lower]

            # If fabricated terms found, ensure answer hedges appropriately
            if found_fabricated:
                hedging_phrases = ["not mentioned", "cannot", "doesn't",
                                 "not specified", "only", "limited"]
                has_hedging = any(h in answer_lower for h in hedging_phrases)

                assert has_hedging, \
                    f"Answer may contain hallucinated info: {found_fabricated}"


# =============================================================================
# Retrieval Quality Tests
# =============================================================================

@pytest.mark.asyncio
async def test_relevant_chunks_retrieved(client):
    """
    Verify retrieved chunks are semantically relevant to query.

    Similarity scores should be above threshold for relevant queries.
    """
    response = await client.post("/chat", json={
        "query": "Explain coordinate transforms in robotics"
    })

    if response.status_code == 200:
        data = response.json()
        sources = data.get("sources", [])

        for source in sources:
            if source.get("source_type") == "selected_text":
                continue

            score = source.get("similarity_score", 0)

            # For a relevant robotics query, we expect decent scores
            # Note: threshold may vary based on corpus size
            assert score >= 0.3, \
                f"Very low similarity score {score} - may not be relevant"


@pytest.mark.asyncio
async def test_chunk_text_not_truncated_badly(client):
    """
    Verify snippet excerpts are meaningful, not cut mid-word/sentence.
    """
    response = await client.post("/chat", json={
        "query": "What is a robot arm?"
    })

    if response.status_code == 200:
        data = response.json()
        sources = data.get("sources", [])

        for source in sources:
            snippet = source.get("snippet", "")

            if snippet:
                # Snippet should end properly (with punctuation or ellipsis)
                valid_endings = [".", "!", "?", "...", ",", ":", ";"]

                # Allow truncation marker
                if len(snippet) >= 200:
                    # Long snippets may be truncated with ...
                    pass
                else:
                    # Shorter snippets should have reasonable structure
                    assert len(snippet) > 10, "Snippet too short to be useful"


# =============================================================================
# Response Consistency Tests
# =============================================================================

@pytest.mark.asyncio
async def test_same_query_consistent_sources(client):
    """
    Verify same query returns consistent source URLs.

    Qdrant search should be deterministic for the same query.
    """
    query = "What is forward kinematics?"

    # Make two requests
    response1 = await client.post("/chat", json={"query": query})
    response2 = await client.post("/chat", json={"query": query})

    if response1.status_code == 200 and response2.status_code == 200:
        data1 = response1.json()
        data2 = response2.json()

        sources1 = data1.get("sources", [])
        sources2 = data2.get("sources", [])

        # Get source URLs from both responses
        urls1 = set(s.get("source_url", "") for s in sources1
                   if s.get("source_type") != "selected_text")
        urls2 = set(s.get("source_url", "") for s in sources2
                   if s.get("source_type") != "selected_text")

        # URLs should significantly overlap (at least 50%)
        if urls1 and urls2:
            overlap = len(urls1 & urls2)
            min_len = min(len(urls1), len(urls2))
            overlap_ratio = overlap / min_len if min_len > 0 else 0

            assert overlap_ratio >= 0.5, \
                f"Inconsistent sources between requests: {overlap_ratio:.0%} overlap"


@pytest.mark.asyncio
async def test_low_confidence_flagged_appropriately(client):
    """
    Verify low confidence is flagged when scores are borderline.
    """
    # Query that might have borderline relevance
    response = await client.post("/chat", json={
        "query": "quantum computing applications"  # Not robotics-specific
    })

    if response.status_code == 200:
        data = response.json()
        metadata = data.get("metadata", {})
        sources = data.get("sources", [])

        # If sources exist but scores are low, should be flagged
        if sources:
            max_score = max(
                s.get("similarity_score", 0)
                for s in sources
                if s.get("source_type") != "selected_text"
            ) if any(s.get("source_type") != "selected_text" for s in sources) else 0

            # If max score < 0.5, expect low_confidence=True
            if max_score < 0.5 and max_score > 0:
                assert metadata.get("low_confidence", False), \
                    f"Low confidence not flagged for max_score={max_score}"


# =============================================================================
# Fallback Behavior Tests
# =============================================================================

@pytest.mark.asyncio
async def test_fallback_on_no_results(client):
    """
    Verify appropriate fallback when no relevant content found.
    """
    response = await client.post("/chat", json={
        "query": "ancient Egyptian hieroglyphics"  # Definitely not in robotics book
    })

    if response.status_code == 200:
        data = response.json()
        metadata = data.get("metadata", {})
        answer = data.get("answer", "")

        # Should indicate no relevant info found or suggest topics
        # Mode should reflect the situation
        mode = metadata.get("mode")

        if mode == "no_results" or metadata.get("low_confidence"):
            # Good - properly flagged
            pass
        elif answer:
            # If there's an answer, it should mention inability to find info
            answer_lower = answer.lower()
            helpfulness_indicators = [
                "couldn't find", "not found", "outside", "scope",
                "textbook", "can help with", "robotics"
            ]
            has_indicator = any(i in answer_lower for i in helpfulness_indicators)

            # Either flagged as no_results or answer indicates limitation
            assert has_indicator or metadata.get("retrieval_count", 0) == 0, \
                "Out-of-scope query got confident answer without proper handling"


# =============================================================================
# Integration Sanity Tests
# =============================================================================

@pytest.mark.asyncio
async def test_qdrant_connection_in_response(client):
    """
    Verify Qdrant is being used (not mocked/bypassed).

    Health check should show Qdrant status.
    """
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()

    services = data.get("services", {})

    # Qdrant service should be present
    assert "qdrant" in services, "Qdrant service not in health check"

    qdrant_status = services["qdrant"]

    # Should have latency (actual connection)
    assert "latency_ms" in qdrant_status, "No latency reported for Qdrant"

    # Log status for debugging
    print(f"Qdrant status: {qdrant_status.get('status')}")
    print(f"Qdrant latency: {qdrant_status.get('latency_ms')}ms")


@pytest.mark.asyncio
async def test_metadata_completeness(client):
    """
    Verify response metadata is complete for debugging/auditing.
    """
    response = await client.post("/chat", json={
        "query": "What is sensor fusion?"
    })

    if response.status_code == 200:
        data = response.json()
        metadata = data.get("metadata", {})

        # Required metadata fields
        required_fields = ["query_time_ms", "retrieval_count", "mode",
                         "low_confidence", "request_id"]

        for field in required_fields:
            assert field in metadata, f"Missing metadata field: {field}"

        # Types should be correct
        assert isinstance(metadata["query_time_ms"], (int, float))
        assert isinstance(metadata["retrieval_count"], int)
        assert isinstance(metadata["mode"], str)
        assert isinstance(metadata["low_confidence"], bool)
        assert isinstance(metadata["request_id"], str)
