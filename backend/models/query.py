"""
Query models for embedding retrieval module.

Contains dataclasses for test query definitions used in validation.
"""

from dataclasses import dataclass


@dataclass
class GoldenTestQuery:
    """
    Test query with expected results for validation.

    Used in the golden test set to validate retrieval quality.

    Attributes:
        query_text: Natural language query
        expected_url_patterns: URL patterns that should appear in results
        min_score: Minimum acceptable similarity score (default 0.6)
    """
    query_text: str
    expected_url_patterns: list[str]
    min_score: float = 0.6
