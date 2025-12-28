"""
Embedding Pipeline for RAG-based Docusaurus Documentation Search

This module provides a complete pipeline to:
1. Discover and fetch documentation URLs from a deployed Docusaurus site
2. Extract and chunk text content with markdown-aware splitting
3. Generate embeddings using Cohere embed-english-v3.0 (1024 dimensions)
4. Store vectors in Qdrant Cloud collection 'rag_embedding' with full metadata
5. Support idempotent re-runs via deterministic IDs and content hashing
"""

import hashlib
import json
import os
import re
import time
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import cohere
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


# =============================================================================
# Environment Validation (T010)
# =============================================================================

def validate_environment() -> dict[str, str]:
    """
    Validate required environment variables are present.
    Fail-fast if any are missing.

    Returns:
        dict with validated environment variables

    Raises:
        EnvironmentError if any required variable is missing
    """
    required_vars = ['COHERE_API_KEY', 'QDRANT_URL', 'QDRANT_API_KEY']
    env_values = {}

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            raise EnvironmentError(f"Missing required environment variable: {var}")
        env_values[var] = value

    return env_values


# =============================================================================
# JSON Structured Logging (T011)
# =============================================================================

def log(entry: dict[str, Any]) -> None:
    """
    JSON structured logging helper.

    Each log entry is a JSON object with fields:
    - timestamp: ISO 8601 format with Z suffix
    - level: INFO, ERROR, WARNING, DEBUG
    - stage: init, discovery, process, report
    - message: Human-readable message
    - url: (optional) URL being processed
    - error: (optional) Error message

    Args:
        entry: Dictionary with log entry fields
    """
    entry["timestamp"] = datetime.utcnow().isoformat() + "Z"
    print(json.dumps(entry))


# =============================================================================
# Client Initialization (T012, T013)
# =============================================================================

def init_cohere_client(api_key: str) -> cohere.Client:
    """
    Initialize Cohere client with error handling.

    Args:
        api_key: Cohere API key

    Returns:
        Initialized Cohere client

    Raises:
        Exception if client initialization fails
    """
    try:
        client = cohere.Client(api_key)
        log({"level": "INFO", "stage": "init", "message": "Cohere client initialized"})
        return client
    except Exception as e:
        log({"level": "ERROR", "stage": "init", "message": f"Failed to initialize Cohere client: {e}"})
        raise


def init_qdrant_client(url: str, api_key: str) -> QdrantClient:
    """
    Initialize Qdrant client with error handling.

    Args:
        url: Qdrant Cloud cluster URL
        api_key: Qdrant API key

    Returns:
        Initialized Qdrant client

    Raises:
        Exception if client initialization fails
    """
    try:
        client = QdrantClient(url=url, api_key=api_key)
        log({"level": "INFO", "stage": "init", "message": "Qdrant client initialized"})
        return client
    except Exception as e:
        log({"level": "ERROR", "stage": "init", "message": f"Failed to initialize Qdrant client: {e}"})
        raise


# =============================================================================
# URL Discovery (T014)
# =============================================================================

def get_all_urls(base_url: str) -> list[str]:
    """
    Discover all documentation URLs from sitemap or fallback to hardcoded list.

    Args:
        base_url: Base URL of deployed Docusaurus site

    Returns:
        Deduplicated list of /docs/** URLs
    """
    base_url = base_url.rstrip('/')
    sitemap_url = f"{base_url}/sitemap.xml"

    # Try fetching sitemap.xml first
    try:
        response = httpx.get(sitemap_url, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml-xml')
            urls = []
            for loc in soup.find_all('loc'):
                url = loc.get_text(strip=True)
                # Filter to /docs/** paths only, exclude /search, /tags/*, /blog/*
                parsed = urlparse(url)
                if '/docs/' in parsed.path:
                    if not any(exclude in parsed.path for exclude in ['/search', '/tags/', '/blog/']):
                        # Rewrite URL to use the actual base_url host (sitemap may have wrong domain)
                        corrected_url = f"{base_url}{parsed.path}"
                        urls.append(corrected_url)

            if urls:
                # Deduplicate while preserving order
                seen = set()
                deduplicated = []
                for url in urls:
                    if url not in seen:
                        seen.add(url)
                        deduplicated.append(url)
                log({"level": "INFO", "stage": "discovery", "message": f"Found {len(deduplicated)} URLs from sitemap"})
                return deduplicated
    except Exception as e:
        log({"level": "WARNING", "stage": "discovery", "message": f"Sitemap fetch failed: {e}, using fallback"})

    # Fallback to hardcoded URLs
    fallback_urls = [
        f"{base_url}/docs/introduction/",
        f"{base_url}/docs/module1-ros2-fundamentals/chapter1-ros2-basics",
        f"{base_url}/docs/module1-ros2-fundamentals/chapter2-ros2-navigation",
        f"{base_url}/docs/module1-ros2-fundamentals/chapter3-ros2-manipulation",
        f"{base_url}/docs/module2-simulation-gazebo-unity/chapter4-gazebo-simulation",
        f"{base_url}/docs/module2-simulation-gazebo-unity/chapter5-unity-simulation",
        f"{base_url}/docs/module2-simulation-gazebo-unity/chapter6-sim-environments",
        f"{base_url}/docs/module3-advanced-robotics-nvidia-isaac/chapter7-isaac-sdk",
        f"{base_url}/docs/module3-advanced-robotics-nvidia-isaac/chapter8-isaac-manipulation",
        f"{base_url}/docs/module4-vla-systems/chapter9-vision-language",
        f"{base_url}/docs/module4-vla-systems/chapter10-action-systems",
        f"{base_url}/docs/resources/",
        f"{base_url}/docs/conclusion/",
    ]
    log({"level": "INFO", "stage": "discovery", "message": f"Using {len(fallback_urls)} fallback URLs"})
    return fallback_urls


# =============================================================================
# Section Extraction Helper (T029)
# =============================================================================

def extract_section_from_url(url: str) -> str:
    """
    Parse URL path to extract module/chapter info.

    E.g., "module1-ros2-fundamentals" from /docs/module1-ros2-fundamentals/chapter1-ros2-basics

    Args:
        url: Full documentation URL

    Returns:
        Section string extracted from URL path
    """
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split('/') if p and p != 'docs']

    if path_parts:
        # Return the first meaningful path segment (usually the module)
        return path_parts[0]
    return "general"


# =============================================================================
# Text Extraction (T015)
# =============================================================================

def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in extracted text."""
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    # But preserve paragraph breaks (double newlines)
    text = re.sub(r' {2,}', '\n\n', text)
    return text.strip()


def extract_text_from_url(url: str) -> tuple[str, str, str, str]:
    """
    Fetch HTML and extract clean text content from Docusaurus page.

    Args:
        url: Full URL of documentation page

    Returns:
        Tuple of (title, section, extracted_text, content_hash)

    Raises:
        ValueError if insufficient content extracted (< 100 chars)
        httpx.HTTPError if fetch fails
    """
    # Fetch HTML with 30s timeout
    response = httpx.get(url, timeout=30, follow_redirects=True)
    response.raise_for_status()

    # Parse with BeautifulSoup
    soup = BeautifulSoup(response.text, 'lxml')

    # Extract title from <title> or <h1>
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text(strip=True)
        # Clean up Docusaurus title format (often "Page Title | Site Name")
        if ' | ' in title:
            title = title.split(' | ')[0]
    else:
        h1_tag = soup.find('h1')
        title = h1_tag.get_text(strip=True) if h1_tag else "Untitled"

    # Extract section from URL path
    section = extract_section_from_url(url)

    # Extract main content using Docusaurus selectors (priority order)
    content_element = (
        soup.select_one('article.markdown') or
        soup.select_one('main[class*="docMainContainer"]') or
        soup.select_one('div[class*="theme-doc-markdown"]') or
        soup.find('main') or
        soup.find('article')
    )

    # Extract text, preserve structure
    if content_element:
        # Remove navigation, sidebar, footer elements
        for unwanted in content_element.select('nav, footer, .pagination-nav, .theme-doc-sidebar-container'):
            unwanted.decompose()
        text = content_element.get_text(separator='\n', strip=True)
    else:
        text = ""

    # Normalize whitespace
    text = normalize_whitespace(text)

    # Skip if < 100 characters
    if len(text) < 100:
        raise ValueError(f"Insufficient content: {len(text)} chars")

    # Compute content hash for idempotency (T021)
    content_hash = hashlib.sha256(text.encode()).hexdigest()

    return (title, section, text, content_hash)


# =============================================================================
# Text Chunking (T016)
# =============================================================================

def chunk_text(text: str, source_url: str) -> list[dict[str, Any]]:
    """
    Split text into overlapping chunks suitable for embedding.

    Args:
        text: Extracted document text
        source_url: URL for generating deterministic chunk IDs

    Returns:
        List of chunk dictionaries with id, text, position
    """
    # Target: 350 tokens (~1400 chars), Overlap: 60 tokens (~240 chars)
    CHUNK_SIZE = 1400
    CHUNK_OVERLAP = 240

    # Markdown-aware separators (priority order)
    SEPARATORS = ['\n## ', '\n### ', '\n#### ', '\n\n', '\n', ' ']

    chunks = []
    position = 0
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE

        # Find best split point using separators
        if end < len(text):
            best_split = end
            for sep in SEPARATORS:
                split_pos = text.rfind(sep, start, end)
                if split_pos > start:
                    best_split = split_pos + len(sep)
                    break
            end = best_split

        chunk_content = text[start:end].strip()

        if chunk_content:
            # Generate deterministic ID: SHA-256(source_url:position)[:32]
            chunk_id = hashlib.sha256(f"{source_url}:{position}".encode()).hexdigest()[:32]

            chunks.append({
                'id': chunk_id,
                'text': chunk_content,
                'position': position,
            })
            position += 1

        # Move start with overlap
        start = end - CHUNK_OVERLAP
        if start < 0:
            start = 0
        if start >= len(text):
            break
        # Prevent infinite loop
        if end >= len(text):
            break

    return chunks


# =============================================================================
# Embedding Generation (T017)
# =============================================================================

def embed(texts: list[str], cohere_client: cohere.Client) -> list[list[float]]:
    """
    Generate embeddings using Cohere API with batching.

    Args:
        texts: List of text strings to embed
        cohere_client: Initialized Cohere client

    Returns:
        List of 1024-dimension embedding vectors
    """
    BATCH_SIZE = 96  # Cohere max per call
    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]

        # Retry with exponential backoff
        for attempt in range(3):
            try:
                response = cohere_client.embed(
                    texts=batch,
                    model="embed-english-v3.0",
                    input_type="search_document"
                )
                all_embeddings.extend(response.embeddings)
                break
            except Exception as e:
                if attempt == 2:
                    raise
                wait_time = 2 ** attempt  # 1s, 2s, 4s backoff
                log({"level": "WARNING", "stage": "embed", "message": f"Retry {attempt + 1}/3 after {wait_time}s: {e}"})
                time.sleep(wait_time)

    return all_embeddings


# =============================================================================
# Qdrant Collection Management (T018)
# =============================================================================

def create_collection(qdrant_client: QdrantClient, collection_name: str = "rag_embedding") -> None:
    """
    Create Qdrant collection if it doesn't exist (idempotent).

    Args:
        qdrant_client: Initialized Qdrant client
        collection_name: Name of collection to create
    """
    # Check if collection exists
    collections = qdrant_client.get_collections().collections
    if any(c.name == collection_name for c in collections):
        log({"level": "INFO", "stage": "init", "message": f"Collection '{collection_name}' already exists"})
        return

    # Create with Cohere embed-english-v3.0 config
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=1024,  # embed-english-v3.0 dimensions
            distance=Distance.COSINE,
        ),
    )
    log({"level": "INFO", "stage": "init", "message": f"Collection '{collection_name}' created"})


# =============================================================================
# Vector Storage (T019)
# =============================================================================

def save_chunk_to_qdrant(
    qdrant_client: QdrantClient,
    chunks: list[dict[str, Any]],
    embeddings: list[list[float]],
    metadata: dict[str, str],
    collection_name: str = "rag_embedding"
) -> int:
    """
    Upsert vectors with metadata to Qdrant collection.

    Args:
        qdrant_client: Initialized Qdrant client
        chunks: List of chunk dicts with id, text, position
        embeddings: Corresponding embedding vectors
        metadata: Shared metadata (source_url, title, section, content_hash)
        collection_name: Target collection name

    Returns:
        Number of points upserted
    """
    points = []
    for chunk, embedding in zip(chunks, embeddings):
        point = PointStruct(
            id=chunk['id'],  # Deterministic 32-char hex ID
            vector=embedding,
            payload={
                "source_url": metadata['source_url'],
                "title": metadata['title'],
                "section": metadata['section'],
                "chunk_position": chunk['position'],
                "chunk_text": chunk['text'],
                "content_hash": metadata['content_hash'],
            }
        )
        points.append(point)

    # Upsert for idempotency (overwrites existing)
    qdrant_client.upsert(
        collection_name=collection_name,
        wait=True,
        points=points,
    )

    return len(points)


# =============================================================================
# Change Detection (T023)
# =============================================================================

def check_content_unchanged(
    qdrant_client: QdrantClient,
    source_url: str,
    content_hash: str,
    collection_name: str = "rag_embedding"
) -> bool:
    """
    Check if document content has changed since last ingestion.

    Args:
        qdrant_client: Initialized Qdrant client
        source_url: URL of the document
        content_hash: SHA-256 hash of current content
        collection_name: Collection to check

    Returns:
        True if content is unchanged (skip re-embedding), False otherwise
    """
    try:
        # Query for existing chunks with this source_url
        results = qdrant_client.scroll(
            collection_name=collection_name,
            scroll_filter={
                "must": [
                    {"key": "source_url", "match": {"value": source_url}}
                ]
            },
            limit=1,
            with_payload=True
        )

        points, _ = results
        if points and len(points) > 0:
            stored_hash = points[0].payload.get('content_hash', '')
            return stored_hash == content_hash
    except Exception:
        # If check fails, assume content changed
        pass

    return False


# =============================================================================
# Main Orchestration (T020)
# =============================================================================

def main() -> None:
    """
    Orchestrate pipeline execution with logging and reporting.
    """
    # Load environment variables
    load_dotenv()

    # Validate environment (fail-fast)
    env = validate_environment()

    # Stats tracking (T025)
    stats: dict[str, Any] = {
        "start_time": time.time(),
        "urls_processed": 0,
        "urls_skipped": 0,  # Unchanged content
        "urls_failed": 0,
        "chunks_created": 0,
        "embeddings_generated": 0,
        "vectors_stored": 0,
        "failed_urls": [],
    }

    BASE_URL = "https://hackathon-i-physical-ai-humanoid-ro-dun.vercel.app"

    # Initialize clients
    co = init_cohere_client(env['COHERE_API_KEY'])
    qdrant = init_qdrant_client(env['QDRANT_URL'], env['QDRANT_API_KEY'])

    # Create collection (idempotent)
    create_collection(qdrant)
    log({"level": "INFO", "stage": "init", "message": "Collection ready"})

    # Discover URLs
    urls = get_all_urls(BASE_URL)
    log({"level": "INFO", "stage": "discovery", "message": f"Found {len(urls)} URLs to process"})

    # Process each URL
    for url in urls:
        try:
            # Extract text (includes content_hash)
            title, section, text, content_hash = extract_text_from_url(url)

            # Check if content unchanged (T023)
            if check_content_unchanged(qdrant, url, content_hash):
                stats["urls_skipped"] += 1
                log({"level": "INFO", "stage": "process", "url": url, "message": "Skipped (unchanged)"})
                continue

            # Chunk text
            chunks = chunk_text(text, url)
            stats["chunks_created"] += len(chunks)

            # Generate embeddings
            chunk_texts = [c['text'] for c in chunks]
            embeddings = embed(chunk_texts, co)
            stats["embeddings_generated"] += len(embeddings)

            # Store in Qdrant
            metadata = {
                "source_url": url,
                "title": title,
                "section": section,
                "content_hash": content_hash
            }
            stored = save_chunk_to_qdrant(qdrant, chunks, embeddings, metadata)
            stats["vectors_stored"] += stored

            stats["urls_processed"] += 1
            log({
                "level": "INFO",
                "stage": "process",
                "url": url,
                "chunks": len(chunks),
                "title": title
            })

        except Exception as e:
            stats["urls_failed"] += 1
            stats["failed_urls"].append({"url": url, "error": str(e)})
            log({"level": "ERROR", "stage": "process", "url": url, "error": str(e)})

    # Report (T027)
    stats["end_time"] = time.time()
    stats["duration_seconds"] = round(stats["end_time"] - stats["start_time"], 2)

    print("\n" + "=" * 60)
    print("EXECUTION REPORT")
    print("=" * 60)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
