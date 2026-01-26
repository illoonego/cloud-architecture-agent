# Architecture

## Top-Level Architecture

```text
                    TOP-LEVEL ARCHITECTURE

               ┌────────────────────────────┐
               │        Client / User       │
               │  (CLI, curl, UI, Postman)  │
               └──────────────┬─────────────┘
                              │  HTTPS
                              ▼
                ┌───────────────────────────┐
                │  Agent API (FastAPI)      │
                │  - /query, /health        │
                │  - runs on AWS (ECS/EC2)  │
                └──────────────┬────────────┘
                       uses    │
        ┌──────────────────────┼─────────────────────────┐
        │                      │                         │
        ▼                      ▼                         ▼
┌───────────────┐      ┌────────────────┐        ┌─────────────────────┐
│  RAG Layer    │      │ Tools / Logic  │        │    LLM Service      │
│  - retriever  │      │ - Terraform    │        │  (vLLM on AWS EC2)  │
│  - embeddings │      │ - error expl.  │        │  - Llama-3.1-8B     │
└──────┬────────┘      │ - arch helper  │        │  - OpenAI-style API │
       │               └────────────────┘        └─────────┬───────────┘
       │                                         HTTP      │
       ▼                                                   │
┌──────────────┐                                           │
│  Vector DB   │  (Chroma/Qdrant or similar)               │
└──────────────┘                                           │
                                                           │
                            ┌──────────────────────────────┘
                            ▼
            ┌───────────────────────────────────────────┐
            │    AWS & MLOps Infrastructure             │
            │    - ECS/EC2 for Agent API container      │
            │    - EC2 GPU instance for vLLM            │
            │    - S3 for docs (optional)               │
            │    - CloudWatch logs & metrics            │
            │    - GitHub Actions CI/CD (build & deploy)│
            └───────────────────────────────────────────┘
```

## Component Breakdown

### 1. Agent API (The Brain)
- **Technology**: Python, FastAPI.
- **Role**: The central orchestrator. It receives user queries, coordinates with the RAG layer and Tools, and sends the final prompt to the LLM.
- **Deployment**: Docker container running on AWS ECS (Elastic Container Service) or EC2.

### 2. LLM Service (The Intelligence)
- **Technology**: vLLM (High-throughput LLM serving).
- **Model**: Llama-3.1-8B-Instruct or similar open-source models.
- **Role**: Generates the actual text responses. It is "stateless" and doesn't know about your private data unless you provide it in the prompt.
- **Deployment**: AWS EC2 instance with GPU support (e.g., g4dn.xlarge with T4 GPU).

### 3. RAG Layer (The Memory)
- **Technology**: Qdrant, ChromaDB, or FAISS.
- **Role**: Stores "embeddings" (mathematical representations) of your documents (AWS whitepapers, architecture guides). It retrieves the most relevant info to help the LLM answer accurately.

### 4. Tools / Logic
- **Role**: Specific Python functions the agent can call.
- **Examples**:
    - `terraform_plan_analyzer`: Reads a Terraform file and explains it.
    - `cost_estimator`: Calculates estimated AWS costs.

## Implementation Details

### Project Structure
```
src/
├── api/          # FastAPI application
│   └── main.py   # API endpoints (/query, /health)
├── agent/        # Agent orchestration
│   ├── router.py # Main agent logic (RAG → LLM → Response)
│   └── tools.py  # Agent tools (search_documentation)
├── llm/          # LLM client
│   └── client.py # vLLM OpenAI-compatible client
├── rag/          # RAG components
│   ├── embeddings.py  # Text-to-vector conversion
│   ├── indexing.py    # Document ingestion
│   └── retriever.py   # Vector search
└── config/       # Configuration
    └── settings.py    # Centralized settings
```

### Data Flow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Agent
    participant RAG
    participant LLM

    User->>API: POST /query {"question": "..."}
    API->>Agent: query(user_input)
    Agent->>RAG: search_documentation(query)
    RAG-->>Agent: [context chunks]
    Agent->>LLM: generate(prompt + context)
    LLM-->>Agent: response
    Agent-->>API: response
    API-->>User: {"answer": "..."}
```

### Key Design Patterns

1. **Singleton Pattern**: `get_embedding_service()` and `get_retriever()` use `@lru_cache` to ensure single instances.

2. **Dependency Injection**: Components accept optional dependencies for testability:
   ```python
   def __init__(self, client: QdrantClient | None = None):
       self.client = client or QdrantClient(...)
   ```

3. **Configuration Management**: All settings centralized in `settings.py` with `.env` support.

4. **Error Handling**: Graceful degradation when services are unavailable.

### Technology Stack

- **API Framework**: FastAPI (async, OpenAPI docs)
- **LLM Server**: vLLM (high-throughput inference)
- **Vector DB**: Qdrant (in-memory or server mode)
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
- **Containerization**: Docker
- **Deployment**: AWS ECS/EC2
- **CI/CD**: GitHub Actions (planned)
---

## Security Architecture

### Authentication Flow

```text
┌────────────┐
│   Client   │
└─────┬──────┘
      │ POST /query
      │ X-API-Key: abc123...
      ▼
┌─────────────────────────┐
│  API Key Validation     │
│  (src/api/auth.py)      │
└─────┬──────────┬────────┘
      │          │
   Valid?     Invalid?
      │          │
      ▼          ▼
┌──────────┐  ┌──────────┐
│ Process  │  │ Return   │
│ Request  │  │ 401      │
└──────────┘  └──────────┘
```

### Security Layers

#### Layer 1: API Key Authentication
- **Implementation**: FastAPI Security dependency (`verify_api_key`)
- **Storage**: `.env` file (comma-separated keys)
- **Validation**: Header-based (`X-API-Key`)
- **Error Handling**: Returns 401 with clear error messages

**Code Location**: `src/api/auth.py`

```python
@app.post("/query", dependencies=[Depends(verify_api_key)])
async def query_endpoint(...):
    # Only reachable with valid API key
```

#### Layer 2: Rate Limiting
- **Implementation**: slowapi (Flask-Limiter for FastAPI)
- **Strategy**: IP-based limiting
- **Limits**: 5 requests per minute per IP
- **Error Handling**: Returns 429 with retry guidance

**Code Location**: `src/api/main.py`

```python
@limiter.limit("5/minute")
@app.post("/query", ...)
async def query_endpoint(...):
    # Rate limited to 5 req/min
```

#### Layer 3: Input Validation
- **Implementation**: Pydantic models
- **Validation**: Type checking, required fields
- **Error Handling**: Returns 422 with validation details

**Code Location**: Request/Response models in `src/api/main.py`

#### Layer 4: Error Handling
- **Implementation**: Exception propagation with HTTP status mapping
- **Strategy**: Service errors (503) vs. bugs (500)
- **Logging**: Structured logging for debugging

**Error Code Mapping**:
- `401` → Authentication failures
- `422` → Validation errors
- `429` → Rate limit exceeded
- `503` → External service failures (LLM, Qdrant)
- `500` → Internal errors (bugs)

**Code Location**: Exception handlers in `src/api/main.py`

### Security Best Practices Implemented

✅ **Secrets Management**: API keys in `.env` (gitignored)  
✅ **Least Privilege**: Only `/query` requires authentication  
✅ **Rate Limiting**: Prevents abuse and DoS attacks  
✅ **Error Messages**: Clear but not leaking sensitive info  
✅ **Input Validation**: Pydantic prevents injection attacks  
✅ **Logging**: Errors logged for debugging, not exposed to clients  

### Future Security Enhancements

🔄 **AWS Secrets Manager**: Move API keys from `.env` to AWS Secrets Manager  
🔄 **Security Groups**: Restrict vLLM port 8000 to API server only  
🔄 **TLS/HTTPS**: Enable HTTPS with SSL certificates  
🔄 **Per-Key Rate Limits**: Different limits for different API keys  
🔄 **API Key Rotation**: Automated key expiration and rotation  
🔄 **Audit Logging**: Track all API access for compliance  

---