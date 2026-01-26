# AWS Cloud Architecture Agent 🤖☁️

> A production-grade GenAI agent for AWS cloud architecture questions, demonstrating RAG, LLM deployment, API security, and cloud infrastructure skills.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Project Highlights

**What This Demonstrates:**
- ✅ **Production API Development**: FastAPI with authentication, rate limiting, and proper error handling
- ✅ **RAG Implementation**: Vector search with Qdrant and sentence transformers
- ✅ **LLM Deployment**: Self-hosted vLLM on AWS EC2 GPU instance
- ✅ **Cloud Infrastructure**: AWS EC2, Elastic IPs, security best practices
- ✅ **Software Engineering**: Clean architecture, type hints, error handling, testing

**Tech Stack:** Python, FastAPI, vLLM, Qdrant, Docker, AWS EC2, Llama 3.1

---

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP Request
       ↓
┌──────────────────────────────────────┐
│  FastAPI Application (Port 8001)     │
│  ├─ API Key Authentication           │
│  ├─ Rate Limiting (5 req/min)        │
│  └─ HTTP Error Handling (401/429/503)│
└──────┬──────────────────┬────────────┘
       │                  │
       │ Search           │ Generate
       ↓                  ↓
┌──────────────┐   ┌─────────────────┐
│   Qdrant     │   │  vLLM (EC2 GPU) │
│  Vector DB   │   │  Llama-3.1-8B   │
│  (RAG)       │   │  Port 8000      │
└──────────────┘   └─────────────────┘
```

**Data Flow:**
1. **User Query** → API validates auth & rate limits
2. **RAG Search** → Find relevant AWS docs in Qdrant
3. **LLM Generation** → vLLM generates answer with context
4. **Response** → Structured JSON with answer + sources

See [docs/architecture.md](docs/architecture.md) for detailed design decisions.

---

## 🚀 Demo

> **Note for Reviewers:** GPU instance is stopped to minimize costs (~$12/day). 
> Available for live demo during interview with 30-minute notice.

### 📹 Video Walkthrough
*[TODO: Add 2-3 minute Loom video showing:]*
- API authentication in action
- Sample query/response
- Swagger UI demonstration
- Architecture explanation

### 📸 Screenshots

**Swagger UI with Authentication:**

![Swagger UI](docs/images/swagger-ui.png)

*Interactive API documentation with 🔒 authentication locks on protected endpoints*

**Example Query:**
```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"question": "How do I set up VPC peering?"}'
```

**Response:**
```json
{
  "question": "How do I set up VPC peering?",
  "answer": "VPC peering allows you to connect two VPCs privately...",
  "sources": ["vpc-peering.md"]
}
```

---

## 🔐 Security Features

| Feature | Implementation | Status |
|---------|----------------|--------|
| **API Authentication** | API key validation (X-API-Key header) | ✅ Implemented |
| **Rate Limiting** | 5 requests/min per IP (slowapi) | ✅ Implemented |
| **HTTP Error Codes** | 401, 429, 503, 500 with clear messages | ✅ Implemented |
| **Elastic IP** | Static IP for EC2 (no IP changes on restart) | ✅ Implemented |
| **Input Validation** | Pydantic models with type checking | ✅ Implemented |
| **Error Logging** | Structured logging for debugging | ✅ Implemented |

**Future Enhancements:**
- 🔄 AWS Secrets Manager for credential storage
- 🔄 Security groups (IP whitelisting for port 8000)
- 🔄 CloudWatch monitoring and alerts
- 🔄 Auto-scaling for production workloads

---

## 🛠️ Technical Implementation

### Key Design Decisions

**1. Why vLLM over OpenAI API?**
- ✅ Full control over model and data (no external dependencies)
- ✅ Cost-effective for high volume (~$0.526/hour vs per-token pricing)
- ✅ Low latency (no network calls to external API)
- ✅ Demonstrates cloud deployment skills

**2. Why RAG over Fine-tuning?**
- ✅ Always up-to-date (can refresh docs without retraining)
- ✅ Transparent sourcing (shows which docs were used)
- ✅ Lower compute cost (no training required)
- ✅ Easier to maintain and update

**3. Architecture Choices**
- **FastAPI**: Modern, async, auto-generated docs, type safety
- **Qdrant**: Fast vector search, easy Docker deployment
- **Sentence Transformers**: Lightweight embeddings, runs locally
- **Docker**: Consistent environments, easy deployment

### Code Quality Highlights

```python
# Clean error handling with proper HTTP codes
@app.post("/query", dependencies=[Depends(verify_api_key)])
@limiter.limit("5/minute")
async def query_agent(request: Request, query_request: QueryRequest):
    try:
        response = agent.query(query_request.question)
        return QueryResponse(question=query_request.question, answer=response)
    except (APITimeoutError, APIConnectionError) as e:
        raise HTTPException(503, f"LLM service unavailable: {type(e).__name__}")
    except Exception as e:
        # Smart error detection: service errors vs bugs
        error_name = type(e).__name__
        if "ResponseHandling" in error_name or "Qdrant" in error_name:
            raise HTTPException(503, f"Search service unavailable: {error_name}")
        else:
            raise HTTPException(500, f"Internal server error: {error_name}")
```

**Notable Features:**
- Type hints throughout (`def search(query: str) -> list[str]`)
- Singleton pattern for expensive resources (LLM client, embeddings)
- Error propagation from service layer to API layer
- Structured logging for debugging

---

## 📦 Quick Start

### Prerequisites
- Python 3.10+
- Docker (for Qdrant)
- AWS account (for EC2 GPU deployment)

### 1. Local Development Setup

```bash
# Clone and install
git clone https://github.com/illoonego/cloud-architecture-agent.git
cd cloud-architecture-agent
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Fetch AWS documentation
python scripts/fetch_docs.py

# Start Qdrant
docker run -d --name qdrant -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest

# Build vector index
python scripts/build_index.py

# Generate API keys
openssl rand -hex 32  # Copy to .env

# Create .env (see .env.example)
# Add VLLM_API_URL and API_KEYS

# Run API
python -m uvicorn src.api.main:app --reload --port 8001
```

### 2. Test the API

```bash
# Health check (no auth required)
curl http://localhost:8001/health

# Query with API key
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-generated-key" \
  -d '{"question": "What is a VPC?"}'

# Interactive docs
open http://localhost:8001/docs
```

---

## 🌩️ AWS Deployment

### EC2 GPU Setup (vLLM)

```bash
# 1. Launch g4dn.xlarge instance (Ubuntu 24.04 Deep Learning AMI)
# 2. Allocate Elastic IP and associate with instance
# 3. SSH into instance
ssh -i your-key.pem ubuntu@YOUR-ELASTIC-IP

# 4. Deploy vLLM
docker run -d --name vllm-server \
  --gpus all \
  -p 8000:8000 \
  -e HUGGING_FACE_HUB_TOKEN='your-token' \
  vllm/vllm-openai:v0.6.2 \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --dtype half \
  --max-model-len 4096
```

**Cost Management:**
- Instance cost: ~$0.526/hour ($378/month if running 24/7)
- **Strategy**: Stop EC2 when not in use (storage ~$5-10/month only)
- Elastic IP: Free while running, $3.65/month when stopped

See [docs/ec2-setup-walkthrough.md](docs/ec2-setup-walkthrough.md) for complete guide.

---

## 📂 Project Structure

```
cloud-architecture-agent/
├── src/
│   ├── api/           # FastAPI application + auth
│   ├── agent/         # Agent orchestration logic
│   ├── llm/           # vLLM client
│   ├── rag/           # Vector search (embeddings, indexing, retrieval)
│   └── config/        # Settings management
├── tests/             # Unit and integration tests
├── scripts/           # Utility scripts (fetch docs, build index)
├── docs/              # Additional documentation
│   ├── architecture.md       # Detailed system design
│   ├── ec2-setup-walkthrough.md  # Step-by-step EC2 guide
│   └── deployment.md         # Production deployment guide
├── infra/docker/      # Dockerfiles
├── .env.example       # Environment template
└── pyproject.toml     # Dependencies
```

---

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Test with coverage
pytest --cov=src tests/

# Specific test file
pytest tests/test_agent.py -v
```

**Test Coverage:**
- Unit tests for RAG retrieval
- Integration tests for agent pipeline
- API endpoint tests with auth

---

## 📊 API Documentation

### Endpoints

| Endpoint | Method | Auth | Rate Limit | Description |
|----------|--------|------|------------|-------------|
| `/` | GET | ❌ | None | Welcome message |
| `/health` | GET | ❌ | None | Health check |
| `/query` | POST | ✅ | 5/min | Ask AWS architecture question |
| `/docs` | GET | ❌ | None | Swagger UI |

### Error Codes

| Code | Meaning | Cause |
|------|---------|-------|
| 200 | Success | Query processed successfully |
| 401 | Unauthorized | Missing or invalid API key |
| 422 | Validation Error | Invalid request body |
| 429 | Rate Limit | Exceeded 5 requests/minute |
| 503 | Service Unavailable | LLM or Qdrant offline |
| 500 | Internal Error | Unexpected server error |

---

## 🎓 Learning Outcomes

**Skills Demonstrated:**
- Backend API development with Python/FastAPI
- Vector search and RAG implementation
- LLM deployment and inference optimization
- AWS cloud infrastructure (EC2, Elastic IPs)
- API security (authentication, rate limiting)
- Error handling and logging
- Docker containerization
- Git workflow and documentation

---

## 📝 Environment Variables

```bash
# .env file
VLLM_API_URL=http://YOUR-ELASTIC-IP:8000/v1
MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
QDRANT_URL=http://localhost:6333
EMBEDDING_MODEL=all-MiniLM-L6-v2
PROJECT_NAME=Cloud Architecture Agent
API_V1_STR=/api/v1
API_KEYS=key1,key2,key3  # Generate with: openssl rand -hex 32
```

See [.env.example](.env.example) for complete template.

---

## 🤝 For Recruiters

**This project demonstrates:**
- ✅ Full-stack backend development skills
- ✅ Cloud architecture and deployment
- ✅ Security best practices
- ✅ Clean, maintainable code
- ✅ Production-ready error handling
- ✅ Documentation and communication

**Live Demo:** Available during interview with 30-minute notice to start EC2 instance.

**Contact:** [Your LinkedIn] | [Your Email]

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🔗 Additional Resources

- [AWS Documentation](https://docs.aws.amazon.com/) (source of RAG data, CC-BY-SA-4.0)
- [vLLM Documentation](https://docs.vllm.ai/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)

---

**⭐ If you find this project interesting, please star it on GitHub!**
