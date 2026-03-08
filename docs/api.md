# API Documentation

## Base URL
```
http://localhost:8001
```

## Authentication

🔐 **All `/query` requests require authentication via API key.**

### How to Authenticate

Include your API key in the `X-API-Key` header:

```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"question": "What is AWS Lambda?"}'
```

### Getting Your API Key

API keys are configured in the `.env` file. Generate secure keys with:

```bash
openssl rand -hex 32
```

See the main README for setup instructions.

---

## Rate Limiting

⏱️ **Rate limit: 5 requests per minute per IP address**

When you exceed the rate limit, you'll receive a `429` error:

```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

---

## Endpoints

### 1. Root
**GET** `/`

**Authentication:** ❌ Not required

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

**Authentication:** ❌ Not required

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

**Authentication:** ✅ Required (X-API-Key header)  
**Rate Limit:** 5 requests/minute per IP

Query the AI agent with a question about AWS cloud architecture.

**Request Headers:**
```
Content-Type: application/json
X-API-Key: your-api-key-here
```

**Request Body:**
```json
{
  "question": "What is AWS Lambda?"
}
```

**Success Response (200):**
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
  -H "X-API-Key: your-api-key-here" \
  -d '{"question": "What is AWS Lambda?"}'
```

**Example with Python:**
```python
import requests

response = requests.post(
    "http://localhost:8001/query",
    headers={
        "Content-Type": "application/json",
        "X-API-Key": "your-api-key-here"
    },
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

### HTTP Status Codes

The API returns the following HTTP status codes:

| Code | Meaning | When It Happens |
|------|---------|-----------------|
| `200` | Success | Query processed successfully |
| `401` | Unauthorized | Missing or invalid API key |
| `422` | Validation Error | Invalid request body (missing `question` field) |
| `429` | Rate Limit Exceeded | More than 5 requests per minute |
| `503` | Service Unavailable | LLM or RAG service is down |
| `500` | Internal Server Error | Unexpected server error |

### Error Response Examples

**401 Unauthorized (No API Key):**
```json
{
  "detail": "Not authenticated"
}
```

**401 Unauthorized (Invalid API Key):**
```json
{
  "detail": "Invalid or expired API key"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "question"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

**429 Rate Limit Exceeded:**
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

**503 Service Unavailable (LLM Down):**
```json
{
  "detail": "LLM service unavailable: APITimeoutError"
}
```

**503 Service Unavailable (RAG Down):**
```json
{
  "detail": "Search service unavailable: ResponseHandlingException"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error: UnexpectedException"
}
```

---

## Configuration

The API behavior can be configured via environment variables (`.env` file):

```bash
# LLM Configuration
VLLM_API_URL=http://YOUR_ELASTIC_IP:8000/v1
MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct

# RAG Configuration
QDRANT_URL=http://localhost:6333
EMBEDDING_MODEL=all-MiniLM-L6-v2
RAG_TOP_K=3

# API Configuration
PROJECT_NAME=Cloud Architecture Agent
API_V1_STR=/api/v1

# Authentication (AWS Secrets Manager)
AWS_SECRET_NAME=cloud-architecture-agent/prod
AWS_REGION=us-east-1
```

---

## Security Features

### ✅ Implemented

- **API Key Authentication**: Required for all `/query` requests
- **Rate Limiting**: 5 requests per minute per IP address
- **Proper Error Codes**: Clear error messages with appropriate HTTP status codes
- **Input Validation**: Pydantic models validate all request data

### 🔄 Future Enhancements

- IP whitelisting via security groups
- OAuth 2.0 / JWT tokens
- Per-key rate limiting (different limits per user)
- API key rotation mechanism
