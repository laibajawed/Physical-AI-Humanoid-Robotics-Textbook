# Feature Specification: Embedding Pipeline Setup

**Feature Branch**: `003-embedding-pipeline`
**Created**: 2025-12-15
**Status**: Draft
**Input**: User description: "Extract text from deployed Docusaurus URLs, generate embeddings using Cohere, and store them in Qdrant for RAG-based retrieval."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Initial Document Ingestion (Priority: P1)

As a developer building a RAG backend, I want to run the embedding pipeline against the deployed Docusaurus book so that all book content becomes searchable via vector similarity.

**Why this priority**: This is the core functionality - without initial ingestion, no RAG retrieval is possible. This delivers the fundamental value of making book content queryable.

**Independent Test**: Can be fully tested by running the pipeline once against the live book URLs and verifying vectors appear in Qdrant with correct metadata.

**Acceptance Scenarios**:

1. **Given** the Docusaurus book is deployed and accessible, **When** the pipeline runs for the first time, **Then** all discoverable document URLs are fetched, processed, and stored as vectors in Qdrant.
2. **Given** a book with 13 chapters across 4 modules, **When** the pipeline completes, **Then** each chapter produces multiple chunks with embeddings stored in Qdrant.
3. **Given** a document URL returns valid HTML, **When** text extraction runs, **Then** only meaningful content is extracted (no navigation, headers, footers, or boilerplate).

---

### User Story 2 - Idempotent Re-runs (Priority: P1)

As a developer, I want to re-run the pipeline without creating duplicate vectors so that I can safely update embeddings when book content changes.

**Why this priority**: Idempotency is critical for operational reliability - without it, re-runs corrupt the vector store with duplicates, breaking retrieval quality.

**Independent Test**: Can be tested by running the pipeline twice consecutively and verifying the vector count remains stable (no duplicates created).

**Acceptance Scenarios**:

1. **Given** the pipeline has already run successfully, **When** I run it again with no content changes, **Then** no new vectors are created and existing vectors are unchanged.
2. **Given** a document's content has changed since the last run, **When** the pipeline re-runs, **Then** the old vectors for that document are replaced with new ones.
3. **Given** a new chapter is added to the book, **When** the pipeline re-runs, **Then** only the new chapter is processed and added (existing vectors untouched).

---

### User Story 3 - Pipeline Execution Report (Priority: P2)

As a developer, I want to see a summary report after pipeline execution so that I can verify the ingestion completed successfully and troubleshoot any issues.

**Why this priority**: Observability is essential for debugging and operational confidence, but the pipeline can function without it.

**Independent Test**: Can be tested by running the pipeline and verifying a structured report is produced with expected metrics.

**Acceptance Scenarios**:

1. **Given** the pipeline completes successfully, **When** execution finishes, **Then** a report shows: URLs processed, chunks created, embeddings generated, vectors stored, and total duration.
2. **Given** some URLs fail to fetch, **When** execution finishes, **Then** the report lists failed URLs with error reasons.
3. **Given** the pipeline runs with no errors, **When** I review the report, **Then** I can see per-document statistics (chunks per doc, average chunk size).

---

### User Story 4 - Source Metadata Preservation (Priority: P2)

As a developer building RAG retrieval, I want each vector to include source metadata so that I can attribute answers to specific book sections.

**Why this priority**: Metadata enables citation and context in RAG responses, improving user trust and answer quality.

**Independent Test**: Can be tested by querying Qdrant for any vector and verifying it contains expected metadata fields.

**Acceptance Scenarios**:

1. **Given** a chunk is created from a document, **When** stored in Qdrant, **Then** the vector payload includes: source URL, document title, chapter/section info, and chunk position.
2. **Given** a user queries the RAG system, **When** results are returned, **Then** each result can be traced back to its original book location via metadata.

---

### Edge Cases

- What happens when a URL returns a 404 or is temporarily unavailable?
  - Pipeline logs the error, skips the URL, and continues processing other URLs. Failed URLs are listed in the execution report.

- How does the system handle extremely long documents?
  - Documents are chunked regardless of length. Chunking ensures no single piece exceeds embedding model limits.

- What happens when the Cohere API rate limit is hit?
  - Pipeline implements exponential backoff and retries (3 attempts with 1s, 2s, 4s delays). If retries are exhausted, the batch fails gracefully with error logged.

- What happens when Qdrant Cloud is temporarily unavailable?
  - Pipeline retries with backoff. If Qdrant remains unavailable, pipeline fails with clear error message indicating the external dependency issue.

- How does the system handle documents with no extractable text content?
  - Empty or navigation-only pages (< 100 characters extracted) are detected and skipped. A warning is logged but pipeline continues.

- What happens when duplicate URLs are discovered?
  - Duplicate URLs are deduplicated before processing. Only unique URLs are fetched.

- What happens if chunk content is identical across documents?
  - Each chunk gets a unique ID based on source URL and position, so identical content from different sources remains distinct.

- What happens when embedding generation fails for a specific chunk?
  - The chunk is logged as failed, skipped, and the pipeline continues. Failed chunks appear in the report.

- What happens if Qdrant Cloud cluster is suspended due to inactivity?
  - Pipeline fails with clear error; user must reactivate cluster in Qdrant Cloud dashboard. Note: Free tier clusters suspend after 1 week of inactivity and are deleted after 4 weeks.

## Requirements *(mandatory)*

### Functional Requirements

**URL Discovery & Fetching**

- **FR-001**: System MUST discover documentation URLs using sitemap.xml as primary source, with hardcoded fallback list of 13 known URLs if sitemap unavailable
- **FR-002**: System MUST fetch HTML content from each discovered URL with 30-second timeout per request
- **FR-003**: System MUST handle HTTP errors gracefully (4xx, 5xx) without stopping the entire pipeline
- **FR-004**: System MUST skip non-documentation pages by filtering to `/docs/**` paths only, excluding `/search`, `/tags/*`, `/blog/*`
- **FR-005**: System MUST deduplicate URLs before processing
- **FR-006**: System MUST limit concurrent connections to maximum 5 requests to avoid rate limiting

**Text Extraction & Cleaning**

- **FR-007**: System MUST extract main content from HTML using Docusaurus-specific selectors: `article.markdown`, `main[class*="docMainContainer"]`, `div[class*="theme-doc-markdown"]`, falling back to `<main>` or `<article>`
- **FR-008**: System MUST preserve document structure indicators (headings, sections) in extracted text
- **FR-009**: System MUST normalize whitespace and remove HTML artifacts
- **FR-010**: System MUST extract document title and section hierarchy from HTML structure
- **FR-011**: System MUST include code blocks with their surrounding explanatory text (preserve formatting, do not split mid-block)
- **FR-012**: System MUST skip documents with less than 100 characters of extractable text

**Chunking**

- **FR-013**: System MUST split extracted text into chunks of 300-400 tokens (target 350 tokens, ~1400 characters)
- **FR-014**: System MUST use 50-80 token overlap (target 60 tokens, ~240 characters) between chunks
- **FR-015**: System MUST use markdown-aware separators for splitting: `\n## `, `\n### `, `\n#### `, `\n\n`, `\n`, ` `
- **FR-016**: System MUST keep code blocks intact within chunks (do not split on code fences)
- **FR-017**: System MUST track chunk position (index) within source document
- **FR-018**: System MUST generate deterministic chunk IDs using SHA-256 hash of (source_url + chunk_position)

**Embedding Generation**

- **FR-019**: System MUST generate embeddings using Cohere `embed-english-v3.0` model (1024 dimensions)
- **FR-020**: System MUST use `input_type="search_document"` for indexing embeddings
- **FR-021**: System MUST batch embedding requests with maximum 96 texts per API call
- **FR-022**: System MUST handle Cohere API rate limits (100 calls/min on trial) with exponential backoff (3 retries: 1s, 2s, 4s)
- **FR-023**: System MUST retry failed embedding requests up to 3 times before marking as failed
- **FR-024**: System MUST validate embedding dimensions are 1024 before storage

**Qdrant Collection Configuration**

- **FR-025**: System MUST connect to Qdrant Cloud free tier using API key authentication
- **FR-026**: System MUST create collection named `rag_embedding` if it does not exist
- **FR-027**: System MUST configure collection with vector size of 1024 dimensions (matching Cohere embed-english-v3.0)
- **FR-028**: System MUST configure collection with Cosine distance metric
- **FR-029**: System MUST configure HNSW index with m=16, ef_construct=100 for optimal recall/speed tradeoff
- **FR-030**: System MUST handle cluster suspension errors with clear messaging about reactivation

**Vector Storage**

- **FR-031**: System MUST store vectors in Qdrant `rag_embedding` collection with associated metadata
- **FR-032**: System MUST include in vector payload: `source_url` (string), `title` (string), `section` (string), `chunk_position` (int), `chunk_text` (string), `content_hash` (string)
- **FR-033**: System MUST use deterministic vector IDs (first 32 chars of SHA-256 hash) enabling idempotent upserts
- **FR-034**: System MUST use upsert operations to overwrite existing vectors with same ID

**Idempotency & Re-runs**

- **FR-035**: System MUST support re-running without creating duplicate vectors (via deterministic IDs + upsert)
- **FR-036**: System MUST detect content changes by comparing SHA-256 hash of extracted text against stored `content_hash` in vector payload
- **FR-037**: System MUST skip embedding generation for documents with unchanged content hash (early exit optimization)
- **FR-038**: System MUST re-embed all chunks for a document if its content hash has changed (document-level change detection)

**Reporting**

- **FR-039**: System MUST produce an execution report with processing statistics
- **FR-040**: System MUST log errors and warnings for failed operations
- **FR-041**: System MUST report: total URLs processed, documents skipped (unchanged), chunks created, embeddings generated, vectors stored, failed operations, and total duration

### Key Entities

- **Document**: A single page from the Docusaurus book; attributes include URL, title, section hierarchy, raw HTML, extracted text, and content_hash (SHA-256)
- **Chunk**: A segment of extracted text suitable for embedding; attributes include content, position index, parent document reference, and deterministic ID
- **Embedding**: A vector representation of a chunk; attributes include 1024-dimensional vector values and associated chunk reference
- **Vector Record**: The stored representation in Qdrant `rag_embedding` collection; attributes include vector ID, embedding values, and metadata payload (source_url, title, section, chunk_position, chunk_text, content_hash)
- **Pipeline Run**: A single execution of the pipeline; attributes include start time, end time, status, and statistics (URLs processed, chunks created, etc.)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 13 known documentation URLs are successfully fetched with HTTP 200; discovery completes in under 30 seconds
- **SC-002**: 100% of documents with >100 characters of extracted text produce at least one chunk with valid 1024-dimension embedding
- **SC-003**: Pipeline completes full book ingestion (13+ docs) in under 10 minutes wall-clock time
- **SC-004**: Re-running the pipeline on unchanged content produces zero embedding API calls (idempotency via content hash verified)
- **SC-005**: Re-running the pipeline on changed content updates only that document's vectors; unchanged documents are skipped
- **SC-006**: 100% of stored vectors contain complete metadata: source_url (valid URL), title (non-empty), section (string), chunk_position (int >= 0), chunk_text (string), content_hash (64-char hex)
- **SC-007**: Pipeline execution report values match Qdrant collection state within 1% margin
- **SC-008**: Failed URL fetches (max 10% of total) do not prevent processing of remaining URLs
- **SC-009**: Cohere API rate limits (429 responses) are handled automatically via retry/backoff without manual intervention
- **SC-010**: Vector search in Qdrant `rag_embedding` collection returns relevant results (top-3 results contain expected source URLs with similarity > 0.7) for sample queries

## Constraints

### Input Constraints
- **IC-001**: Source URLs must be from deployed Docusaurus site (Vercel or custom domain)
- **IC-002**: Maximum 5 concurrent HTTP connections to source site
- **IC-003**: Request timeout of 30 seconds per URL fetch
- **IC-004**: Only `text/html` content type processed; skip assets/media
- **IC-005**: URL pattern: include only `/docs/**` paths
- **IC-006**: Maximum 100 URLs per pipeline run (safety limit)

### Processing Constraints
- **PC-001**: Cohere model: `embed-english-v3.0` (1024 dimensions)
- **PC-002**: Cohere input_type: `search_document` for indexing, `search_query` for retrieval
- **PC-003**: Cohere batch size: maximum 96 texts per API call
- **PC-004**: Chunk size: 300-400 tokens (target 350), markdown-aware splitting
- **PC-005**: Chunk overlap: 50-80 tokens (target 60, ~17% of chunk size)
- **PC-006**: Minimum extractable text: 100 characters (skip empty pages)
- **PC-007**: Maximum raw HTML size: 500KB per document

### Output Constraints
- **OC-001**: Vector dimensions: 1024 (matching embed-english-v3.0)
- **OC-002**: Distance metric: Cosine similarity
- **OC-003**: Point ID: First 32 characters of SHA-256 hash from (source_url + chunk_position)
- **OC-004**: Required payload fields: `source_url`, `title`, `section`, `chunk_position`, `chunk_text`, `content_hash`
- **OC-005**: Collection name: `rag_embedding`

### Operational Constraints
- **OpC-001**: Qdrant deployment: Qdrant Cloud free tier (1GB RAM, 4GB disk)
- **OpC-002**: Retry policy: 3 attempts with exponential backoff (1s, 2s, 4s base delays)
- **OpC-003**: Stage timeouts: Fetch=30s, Extract=5s, Chunk=2s, Embed=60s/batch, Upsert=30s/batch
- **OpC-004**: Error budget: Pipeline continues if <= 10% of URLs fail; aborts if > 10% fail
- **OpC-005**: Cohere API: Handle 429 responses using Retry-After header or exponential backoff
- **OpC-006**: Credentials: Cohere API key and Qdrant Cloud URL/API key from environment variables
- **OpC-007**: Inactivity awareness: Qdrant Cloud free tier suspends after 1 week, deletes after 4 weeks of inactivity

## Clarifications

### Session 2025-12-15

**Q1: Environment Variables for Credentials**
- **Question**: Which environment variables should be required for external service credentials?
- **Answer**: Three required variables with fail-fast validation:
  - `COHERE_API_KEY ` - Cohere API key for embedding generation
  - `QDRANT_URL ` - Qdrant Cloud cluster URL
  - `QDRANT_API_KEY` - Qdrant Cloud API key
- **Rationale**: Explicit variable names improve documentation and debugging. Fail-fast validation prevents silent failures mid-pipeline.


  **Q2: Structured Logging Format**
  - **Question**: Which logging approach should the pipeline use for operational debugging?
  - **Answer**: JSON structured logs - each log entry is a JSON object with fields: `timestamp`, `level`, `stage`, `message`, `url` (optional), `error` (optional).
  - **Rationale**: JSON format enables both human debugging (via jq or grep) and future integration with log aggregation tools without code changes.


## Assumptions

- The Docusaurus book is deployed and publicly accessible at a known base URL
- Docusaurus site has sitemap.xml available, or the 13 known documentation URLs are valid
- Cohere API trial key is available with sufficient quota (1,000 calls/month, ~96,000 embeddings)
- Qdrant Cloud free tier account is created and cluster is active
- Book content is primarily English text with some code blocks
- Standard Docusaurus HTML structure is used (content in main article area with expected CSS selectors)
- Document URLs follow Docusaurus routing patterns (`/docs/**`)
- Code blocks in the robotics book are accompanied by explanatory prose that provides semantic context

## Not Building (Out of Scope)

- Real-time content synchronization (webhook-based updates)
- Authentication/authorization for protected content
- Multi-language embedding support (English-only with embed-english-v3.0)
- Custom embedding model fine-tuning
- RAG query interface (retrieval API) - separate feature
- Frontend/UI for pipeline management
- Incremental/streaming ingestion during book editing
- Support for non-Docusaurus documentation sites
- Automatic sitemap generation (assumes sitemap exists or uses hardcoded URL list)
- Image/diagram embedding (text-only embeddings)
- Cross-reference/link graph storage (flat vector store)
- Version history of embeddings (upsert overwrites)
- Multi-tenant collection support (single collection for single book)
- Chunk-level change detection (document-level is sufficient for this scale)
