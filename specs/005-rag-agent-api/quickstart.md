# Quickstart: RAG Agent API (Spec-3)

**Feature**: 005-rag-agent-api
**Date**: 2025-12-17

## Prerequisites

- Python 3.11+
- Existing Qdrant collection `rag_embedding` (from Spec-1 ingestion pipeline)
- API keys for Gemini, Cohere, and Qdrant Cloud
- Neon Postgres database (for session storage)

## 1. Environment Setup

### 1.1 Clone and Navigate

```bash
cd backend
```

### 1.2 Create Virtual Environment

```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS/Linux
python -m venv .venv
source .venv/bin/activate
```

### 1.3 Install Dependencies

```bash
pip install -e .
# Or with dev dependencies
pip install -e ".[dev]"
```

### 1.4 Configure Environment Variables

Create or update `.env` file:

```bash
# Required - Gemini API (for agent LLM)
GEMINI_API_KEY=your_gemini_api_key_here

# Required - Qdrant Cloud (for vector retrieval)
QDRANT_URL=https://your-cluster.us-east4-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_api_key_here

# Required - Cohere (for query embeddings)
COHERE_API_KEY=your_cohere_api_key_here

# Required - Neon Postgres (for session/history)
DATABASE_URL=postgresql://user:password@your-neon-host.neon.tech/neondb?sslmode=require

# Optional - Server configuration
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## 2. Database Setup

### 2.1 Create Tables

Run the migration script (or execute manually):

```sql
-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    session_id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active TIMESTAMPTZ DEFAULT NOW()
);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(session_id),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    sources JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp DESC);
```

## 3. Verify Setup

### 3.1 Check Qdrant Connection

```bash
python -c "
import asyncio
from retrieve import get_collection_stats

async def check():
    stats = await get_collection_stats()
    print(f'Qdrant connected: {stats.vector_count} vectors')
    print(f'Index status: {stats.index_status}')

asyncio.run(check())
"
```

Expected output:
```
Qdrant connected: 12 vectors
Index status: green
```

### 3.2 Check Gemini API

```bash
python -c "
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
import asyncio

load_dotenv()

async def check():
    client = AsyncOpenAI(
        api_key=os.getenv('GEMINI_API_KEY'),
        base_url='https://generativelanguage.googleapis.com/v1beta/openai/'
    )
    response = await client.chat.completions.create(
        model='gemini-2.0-flash',
        messages=[{'role': 'user', 'content': 'Say hello'}],
        max_tokens=10
    )
    print(f'Gemini connected: {response.choices[0].message.content}')

asyncio.run(check())
"
```

### 3.3 Check Postgres Connection

```bash
python -c "
import os
import asyncio
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def check():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    result = await conn.fetchval('SELECT version()')
    print(f'Postgres connected: {result[:50]}...')
    await conn.close()

asyncio.run(check())
"
```

## 4. Run the Server

### 4.1 Development Mode (with auto-reload)

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 4.2 Production Mode

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## 5. Test the API

### 5.1 Health Check

```bash
curl http://localhost:8000/health | jq
```

Expected:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-17T10:30:00Z",
  "services": {
    "qdrant": {"name": "qdrant", "status": "healthy", "latency_ms": 45.2},
    "postgres": {"name": "postgres", "status": "healthy", "latency_ms": 12.5}
  },
  "version": "0.1.0"
}
```

### 5.2 Basic Chat

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is inverse kinematics?"}' | jq
```

Expected:
```json
{
  "answer": "Inverse kinematics (IK) is the mathematical process...",
  "sources": [
    {
      "source_url": "https://...",
      "title": "Motion Planning",
      "section": "Inverse Kinematics",
      "chunk_position": 5,
      "similarity_score": 0.87,
      "snippet": "First 200 chars..."
    }
  ],
  "metadata": {
    "query_time_ms": 1234.5,
    "retrieval_count": 5,
    "mode": "full",
    "low_confidence": false,
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 5.3 Selected-Text Mode

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain this in simpler terms",
    "selected_text": "Inverse kinematics calculates joint angles from end-effector position."
  }' | jq
```

### 5.4 Streaming Response

```bash
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "What is inverse kinematics?"}' \
  --no-buffer
```

### 5.5 Get Conversation History

```bash
curl http://localhost:8000/history/550e8400-e29b-41d4-a716-446655440000 | jq
```

## 6. Run Tests

### 6.1 All Tests

```bash
pytest tests/ -v
```

### 6.2 Specific Test Files

```bash
# API smoke tests
pytest tests/test_api.py -v

# Agent tests
pytest tests/test_agent.py -v

# Integration tests
pytest tests/test_integration.py -v
```

### 6.3 With Coverage

```bash
pytest tests/ --cov=. --cov-report=html
```

## 7. Common Issues

### Issue: "GEMINI_API_KEY not set"

**Solution**: Ensure `.env` file exists and contains valid API key:
```bash
echo $GEMINI_API_KEY  # Should show your key
```

### Issue: "Connection refused to Qdrant"

**Solution**: Check Qdrant URL and API key in `.env`. Verify cluster is active in Qdrant Cloud console.

### Issue: "No vectors in collection"

**Solution**: Run the ingestion pipeline first (Spec-1):
```bash
python main.py
```

### Issue: "asyncpg connection refused"

**Solution**: Check DATABASE_URL format includes `?sslmode=require` for Neon.

### Issue: "Rate limit exceeded (429)"

**Solution**: Wait for retry-after period or reduce request frequency. Max 10 concurrent requests.

## 8. Development Workflow

```bash
# 1. Make changes to agent.py or app.py

# 2. Run tests
pytest tests/ -v

# 3. Check linting
ruff check .

# 4. Format code
ruff format .

# 5. Start server and test manually
uvicorn app:app --reload
```

## 9. API Documentation

With server running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
