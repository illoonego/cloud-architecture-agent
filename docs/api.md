# API Documentation

## Base URL
```
http://localhost:8001
```

## Endpoints

### 1. Root
**GET** `/`

Returns a welcome message.

**Response:**
```json
{
  "message": "Welcome to the Cloud Architecture Agent API"
}
```

---

### 2. Health Check
**GET** `/health`

Returns the health status of the API.

**Response:**
```json
{
  "status": "healthy",
  "project": "Cloud Architecture Agent"
}
```

---

### 3. Query Agent
**POST** `/query`

Query the AI agent with a question about AWS cloud architecture.

**Request Body:**
```json
{
  "question": "What is AWS Lambda?"
}
```

**Response:**
```json
{
  "question": "What is AWS Lambda?",
  "answer": "AWS Lambda is a serverless compute service..."
}
```

**Example with curl:**
```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is AWS Lambda?"}'
```

**Example with Python:**
```python
import requests

response = requests.post(
    "http://localhost:8001/query",
    json={"question": "What is AWS Lambda?"}
)
print(response.json())
```

---

## Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `http://localhost:8001/docs`
- **ReDoc**: `http://localhost:8001/redoc`

---

## Request/Response Models

### QueryRequest
```python
class QueryRequest(BaseModel):
    question: str
```

### QueryResponse
```python
class QueryResponse(BaseModel):
    question: str
    answer: str
```

---

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Successful request
- `422 Unprocessable Entity`: Invalid request body
- `500 Internal Server Error`: Server error

**Example Error Response:**
```json
{
  "detail": [
    {
      "loc": ["body", "question"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Configuration

The API behavior can be configured via environment variables (`.env` file):

```bash
# LLM Configuration
VLLM_API_URL=http://YOUR_EC2_PUBLIC_IP:8000/v1
MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct

# RAG Configuration
QDRANT_URL=http://localhost:6333
EMBEDDING_MODEL=all-MiniLM-L6-v2
RAG_TOP_K=3

# API Configuration
PROJECT_NAME=Cloud Architecture Agent
API_V1_STR=/api/v1
```

---

## Rate Limiting

Currently, no rate limiting is implemented. For production deployment, consider adding rate limiting middleware.

---

## Authentication

Currently, no authentication is required. For production deployment, implement:
- API keys
- OAuth 2.0
- JWT tokens
