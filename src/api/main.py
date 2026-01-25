# src/api/main.py

from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from openai import APIConnectionError, APITimeoutError
from pydantic import BaseModel

from src.agent.router import AgentRouter
from src.api.auth import verify_api_key
from src.config.settings import settings

# Set up rate limiting
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app with rate limiting middleware
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Register rate limit exceeded handler
app.state.limiter = limiter

# Initialize the agent once (uses LLMClient + retriever singletons under the hood)
agent = AgentRouter()

class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    question: str
    answer: str

# Custom handler for rate limit exceeded
@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Try again in 60 seconds."},
    )

@app.get("/")
def root() -> dict:
    return {"message": "Welcome to the Cloud Architecture Agent API"}


@app.get("/health")
def health_check() -> dict:
    return {"status": "healthy", "project": settings.PROJECT_NAME}

@app.post("/query", response_model=QueryResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("5/minute")
def query_agent(request: Request, query_request: QueryRequest) -> QueryResponse:
    """
    Query the AI agent with a question about AWS architecture.
    
    Requires authentication via X-API-Key header.
    
    Raises:
        HTTPException 503: If LLM service is unavailable
        HTTPException 500: For other internal errors
    """
    try:
        response = agent.query(query_request.question)
        if not response or not response.strip():
            response = "No answer returned. Please try again later."
        return QueryResponse(question=query_request.question, answer=response)
    except (APITimeoutError, APIConnectionError) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM service unavailable: {type(e).__name__}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {type(e).__name__}"
        )
