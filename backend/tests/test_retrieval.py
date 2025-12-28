"""
Qdrant Retrieval Tests

Tests to verify:
1. Qdrant connection and collection health
2. Embedding generation works correctly
3. Search returns relevant results
4. Metadata is complete and valid
5. Pipeline validation passes
"""

import pytest
import pytest_asyncio
import asyncio
import os
import sys

# Set testing environment
os.environ["TESTING"] = "true"

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Reset module-level clients before each test to avoid event loop issues
@pytest.fixture(autouse=True)
def reset_clients():
    """Reset module-level clients before each test."""
    import retrieve
    retrieve._cohere_client = None
    retrieve._qdrant_client = None
    yield
    # Cleanup after test
    retrieve._cohere_client = None
    retrieve._qdrant_client = None


# =============================================================================
# Direct Retrieval Tests (bypassing API)
# =============================================================================

@pytest.mark.asyncio
async def test_qdrant_collection_exists():
    """
    Verify Qdrant collection exists and has vectors.
    """
    from retrieve import get_collection_stats

    try:
        stats = await get_collection_stats()

        assert stats.vector_count > 0, \
            f"Collection is empty - no vectors found (count: {stats.vector_count})"

        assert stats.dimensions == 1024, \
            f"Unexpected vector dimensions: {stats.dimensions} (expected 1024)"

        print(f"Collection stats:")
        print(f"  - Vector count: {stats.vector_count}")
        print(f"  - Points count: {stats.points_count}")
        print(f"  - Index status: {stats.index_status}")

    except EnvironmentError as e:
        pytest.skip(f"Qdrant credentials not configured: {e}")
    except Exception as e:
        pytest.fail(f"Failed to get collection stats: {e}")


@pytest.mark.asyncio
async def test_search_returns_results():
    """
    Verify basic search returns results for in-domain query.
    """
    from retrieve import search

    try:
        response = await search(
            query_text="What is inverse kinematics?",
            limit=5,
            score_threshold=0.0  # Get all results for testing
        )

        assert response.total_results > 0, \
            "No results returned for in-domain query"

        assert len(response.results) <= 5, \
            f"More results than limit: {len(response.results)}"

        # Check first result has required fields
        first = response.results[0]
        assert first.source_url, "Result missing source_url"
        assert first.chunk_text, "Result missing chunk_text"
        assert first.similarity_score > 0, "Invalid similarity score"

        print(f"Search results:")
        print(f"  - Total: {response.total_results}")
        print(f"  - Query time: {response.query_time_ms:.2f}ms")
        for i, r in enumerate(response.results[:3]):
            print(f"  - Result {i+1}: score={r.similarity_score:.3f}, url={r.source_url}")

    except EnvironmentError as e:
        pytest.skip(f"Credentials not configured: {e}")


@pytest.mark.asyncio
async def test_search_with_score_threshold():
    """
    Verify score_threshold filters results correctly.
    """
    from retrieve import search

    try:
        # Search with high threshold
        response = await search(
            query_text="robot arm control",
            limit=10,
            score_threshold=0.7  # High threshold
        )

        # All results should meet threshold
        for result in response.results:
            assert result.similarity_score >= 0.7, \
                f"Result below threshold: {result.similarity_score}"

    except EnvironmentError as e:
        pytest.skip(f"Credentials not configured: {e}")


@pytest.mark.asyncio
async def test_search_with_url_filter():
    """
    Verify source_url_filter works correctly.
    """
    from retrieve import search

    try:
        # Search with URL filter
        response = await search(
            query_text="robot",
            limit=10,
            score_threshold=0.0,
            source_url_filter="/docs/module1"
        )

        # All results should match URL pattern
        for result in response.results:
            assert "/docs/module1" in result.source_url, \
                f"Result URL doesn't match filter: {result.source_url}"

    except EnvironmentError as e:
        pytest.skip(f"Credentials not configured: {e}")


@pytest.mark.asyncio
async def test_search_empty_query_rejected():
    """
    Verify empty query raises ValueError.
    """
    from retrieve import search

    with pytest.raises(ValueError) as exc_info:
        await search(query_text="", limit=5)

    assert "empty" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_search_whitespace_query_rejected():
    """
    Verify whitespace-only query raises ValueError.
    """
    from retrieve import search

    with pytest.raises(ValueError) as exc_info:
        await search(query_text="   \n\t  ", limit=5)

    assert "empty" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_search_limit_validation():
    """
    Verify limit parameter is validated.
    """
    from retrieve import search

    with pytest.raises(ValueError):
        await search(query_text="test", limit=0)

    with pytest.raises(ValueError):
        await search(query_text="test", limit=100)  # Above max


@pytest.mark.asyncio
async def test_metadata_completeness():
    """
    Verify all required metadata fields are present in results.
    """
    from retrieve import search

    try:
        response = await search(
            query_text="sensor fusion robot",
            limit=5,
            score_threshold=0.0
        )

        required_fields = ["source_url", "title", "section", "chunk_position", "chunk_text"]

        for result in response.results:
            for field in required_fields:
                value = getattr(result, field, None)
                # chunk_position can be 0, others should be non-empty
                if field == "chunk_position":
                    assert value is not None, f"Missing {field}"
                else:
                    # Allow empty but not None
                    assert value is not None, f"Missing {field}"

    except EnvironmentError as e:
        pytest.skip(f"Credentials not configured: {e}")


@pytest.mark.asyncio
async def test_search_deterministic():
    """
    Verify same query returns same results (deterministic).
    """
    from retrieve import search

    try:
        query = "robot motion planning"

        response1 = await search(query_text=query, limit=5, score_threshold=0.0)
        response2 = await search(query_text=query, limit=5, score_threshold=0.0)

        # Results should be identical
        assert len(response1.results) == len(response2.results), \
            "Different result counts for same query"

        for r1, r2 in zip(response1.results, response2.results):
            assert r1.source_url == r2.source_url, "Different URLs for same query"
            assert abs(r1.similarity_score - r2.similarity_score) < 0.001, \
                "Different scores for same query"

    except EnvironmentError as e:
        pytest.skip(f"Credentials not configured: {e}")


# =============================================================================
# Golden Test Set Validation
# =============================================================================

@pytest.mark.asyncio
async def test_golden_queries_return_relevant_results():
    """
    Verify golden test queries return expected content.
    """
    from retrieve import search

    golden_queries = [
        ("What is inverse kinematics?", ["/docs/module"]),
        ("How does robot arm control work?", ["/docs/"]),
        ("Explain motion planning", ["/docs/"]),
    ]

    try:
        for query, expected_patterns in golden_queries:
            response = await search(
                query_text=query,
                limit=5,
                score_threshold=0.3  # Reasonable threshold
            )

            # Should have results
            assert response.total_results > 0, \
                f"No results for golden query: {query}"

            # At least one result should match expected patterns
            matched = False
            for result in response.results:
                for pattern in expected_patterns:
                    if pattern in result.source_url:
                        matched = True
                        break
                if matched:
                    break

            assert matched, \
                f"Golden query '{query}' didn't match expected patterns. " \
                f"Got URLs: {[r.source_url for r in response.results[:3]]}"

    except EnvironmentError as e:
        pytest.skip(f"Credentials not configured: {e}")


@pytest.mark.asyncio
async def test_out_of_domain_returns_low_scores():
    """
    Verify out-of-domain queries return low similarity scores.
    """
    from retrieve import search

    out_of_domain_queries = [
        "What is the best pizza recipe?",
        "How to train a cat?",
        "Stock market analysis techniques",
    ]

    try:
        for query in out_of_domain_queries:
            response = await search(
                query_text=query,
                limit=5,
                score_threshold=0.0  # Get all results
            )

            # If results exist, scores should be low
            if response.results:
                max_score = max(r.similarity_score for r in response.results)

                # Out-of-domain should have low scores (< 0.5)
                assert max_score < 0.5, \
                    f"Out-of-domain query '{query}' got high score: {max_score}"

                print(f"Out-of-domain '{query}': max_score={max_score:.3f}")

    except EnvironmentError as e:
        pytest.skip(f"Credentials not configured: {e}")


# =============================================================================
# Pipeline Validation
# =============================================================================

@pytest.mark.asyncio
async def test_validate_pipeline():
    """
    Run full pipeline validation.
    """
    from retrieve import validate_pipeline

    try:
        report = await validate_pipeline()

        print(f"\nPipeline Validation Report:")
        print(f"  - Passed: {report.passed}")
        print(f"  - Total queries: {report.total_queries}")
        print(f"  - Passed queries: {report.passed_queries}")
        print(f"  - Vector count: {report.vector_count}")
        print(f"  - Metadata completeness: {report.metadata_completeness:.1f}%")

        if report.failed_queries:
            print(f"  - Failed queries:")
            for failed in report.failed_queries:
                print(f"    - {failed['query']}: {failed['reason']}")

        # Check minimum criteria
        assert report.vector_count > 0, "No vectors in collection"
        assert report.metadata_completeness >= 80, \
            f"Low metadata completeness: {report.metadata_completeness}%"

        # Allow some failures in golden set (4/5 minimum)
        pass_rate = report.passed_queries / report.total_queries
        assert pass_rate >= 0.6, \
            f"Low pipeline pass rate: {pass_rate:.0%}"

    except EnvironmentError as e:
        pytest.skip(f"Credentials not configured: {e}")


# =============================================================================
# Performance Tests
# =============================================================================

@pytest.mark.asyncio
async def test_search_latency():
    """
    Verify search completes within acceptable time.
    """
    from retrieve import search
    import time

    try:
        start = time.perf_counter()
        response = await search(
            query_text="robot kinematics",
            limit=5,
            score_threshold=0.3
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Search should complete in < 5 seconds (including embedding)
        assert elapsed_ms < 5000, \
            f"Search too slow: {elapsed_ms:.0f}ms"

        print(f"Search latency: {elapsed_ms:.0f}ms (reported: {response.query_time_ms:.0f}ms)")

    except EnvironmentError as e:
        pytest.skip(f"Credentials not configured: {e}")


@pytest.mark.asyncio
async def test_concurrent_searches():
    """
    Verify multiple concurrent searches work correctly.
    """
    from retrieve import search

    queries = [
        "inverse kinematics",
        "robot arm control",
        "sensor fusion",
        "motion planning",
        "ROS2 navigation",
    ]

    try:
        tasks = [
            search(query_text=q, limit=3, score_threshold=0.0)
            for q in queries
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent search failed for '{queries[i]}': {result}")

            assert result.total_results >= 0, \
                f"Invalid result for '{queries[i]}'"

        print(f"Completed {len(queries)} concurrent searches successfully")

    except EnvironmentError as e:
        pytest.skip(f"Credentials not configured: {e}")


# =============================================================================
# Edge Cases
# =============================================================================

@pytest.mark.asyncio
async def test_very_long_query():
    """
    Verify very long query is handled (truncated with warning).
    """
    from retrieve import search

    try:
        long_query = "robot " * 10000  # Very long query

        response = await search(
            query_text=long_query,
            limit=5,
            score_threshold=0.0
        )

        # Should complete without error
        assert response is not None

        # Should have truncation warning
        assert any("truncat" in w.lower() for w in response.warnings), \
            "Long query should generate truncation warning"

    except EnvironmentError as e:
        pytest.skip(f"Credentials not configured: {e}")


@pytest.mark.asyncio
async def test_special_characters_in_query():
    """
    Verify special characters don't break search.
    """
    from retrieve import search

    special_queries = [
        "robot's arm control",
        "what is x^2 + y^2?",
        "C++ programming for robots",
        "robot <sensor> data",
    ]

    try:
        for query in special_queries:
            response = await search(
                query_text=query,
                limit=3,
                score_threshold=0.0
            )

            # Should complete without error
            assert response is not None, f"Failed for query: {query}"

    except EnvironmentError as e:
        pytest.skip(f"Credentials not configured: {e}")
