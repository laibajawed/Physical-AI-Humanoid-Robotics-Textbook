# specify.md – Integrated RAG Chatbot for Physical AI & Humanoid Robotics Docusaurus Textbook

Target audience  
Students, educators, and researchers using the Physical AI & Humanoid Robotics textbook who need instant, context-aware answers about ROS 2, URDF, Python-ROS bridging, humanoid systems, and related course content.

Focus  
Semantic search and retrieval-augmented generation system that provides accurate, source-cited answers from textbook content with support for full-document and user-selected text queries.

Success criteria  
- Chatbot accurately answers questions using textbook content with 90%+ relevance score  
- Supports both general book queries and context-specific queries from user-highlighted text  
- Response time under 3 seconds for typical queries (95th percentile)  
- Successfully ingests and embeds all Docusaurus markdown content (chapters, lessons, code examples)  
- Implements secure API authentication and rate limiting  
- Stores conversation history per user session in Neon Postgres  
- Vector similarity search retrieves top 3–5 relevant chunks before generation  
- Responses include source citations (chapter/lesson references) from retrieved content  

Constraints  
- Tech stack: OpenAI Agents SDK (with Gemini API via OpenAI-compatible endpoint), FastAPI, Qdrant Cloud Free Tier, Neon Serverless Postgres  
- Project structure: Follow backend/ architecture with the exact files:  
  main.py, embeddings.py, vector_store.py, db.py, routes.py, chat.py, ingest.py, source.py  
- API key management: Store GEMINI_API_KEY in .env file, never commit to version control  
- Embedding model: Gemini text embedding model (via Gemini API) or text-embedding-3-small equivalent  
- Database schema: User sessions, conversation history, and metadata in Neon Postgres; vector embeddings and payloads in Qdrant  
- Free tier limits: Qdrant Cloud Free (1 GB storage), Neon Serverless Postgres Free tier  

Technical implementation requirements  
- Async FastAPI application with endpoints: /embed, /query, /chat, /ingest (plus /health and /feedback)  
- Implement chunking strategy for markdown content: 500–1000 tokens per chunk with 150–200 token overlap; preserve headings and code blocks  
- Use OpenAI Agents SDK Runner with AsyncOpenAI client pointing to Gemini OpenAI-compatible endpoint (https://generativelanguage.googleapis.com/v1beta/openai/)  
- Vector store operations in Qdrant:  
  - Initialize collection with correct dimension (Gemini embedding size = 768 or 1536 depending on model)  
  - Upsert points with metadata payload (chapter, lesson, slug, heading, code_block flag)  
  - Similarity search with metadata filtering and score threshold  
- CORS configuration allowing only the Docusaurus domain(s)  
- Environment variables (required):  
 - Error handling and structured logging (JSON logs in production)  
- Input validation using Pydantic models for every API request (QueryRequest, IngestRequest, etc.)  
- Session management: create anonymous session ID client-side, store conversation history in Postgres table conversations  

This document is the authoritative, single source of truth for the entire project implementation.

Analyze & get the context from @OpenAIAgents_SampleCode.md , @chatkit_Knowledge.md Based on the specifications,SampleCode, and chatkit knowledge, create a best and optimized /sp.specify