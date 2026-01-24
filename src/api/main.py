# src/api/main.py

from fastapi import Depends, FastAPI, HTTPException, status
from openai import APIConnectionError, APITimeoutError
from pydantic import BaseModel

from src.agent.router import AgentRouter
from src.api.auth import verify_api_key
from src.config.settings import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Initialize the agent once (uses LLMClient + retriever singletons under the hood)
agent = AgentRouter()


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    question: str
    answer: str


@app.get("/")
def root() -> dict:
    return {"message": "Welcome to the Cloud Architecture Agent API"}


@app.get("/health")
def health_check() -> dict:
    return {"status": "healthy", "project": settings.PROJECT_NAME}


@app.post("/query", response_model=QueryResponse, dependencies=[Depends(verify_api_key)])
def query_agent(request: QueryRequest) -> QueryResponse:
    """
    Query the AI agent with a question about AWS architecture.
    
    Requires authentication via X-API-Key header.
    
    Raises:
        HTTPException 503: If LLM service is unavailable
        HTTPException 500: For other internal errors
    """
    try:
        response = agent.query(request.question)
        if not response or not response.strip():
            response = "No answer returned. Please try again later."
        return QueryResponse(question=request.question, answer=response)
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
