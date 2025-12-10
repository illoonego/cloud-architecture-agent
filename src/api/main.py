# src/api/main.py

from fastapi import FastAPI
from pydantic import BaseModel

from src.agent.router import AgentRouter
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


@app.post("/query", response_model=QueryResponse)
def query_agent(request: QueryRequest) -> QueryResponse:
    """
    Query the AI agent with a question about AWS architecture.
    """
    response = agent.query(request.question)
    if not response or not response.strip():
        response = "No answer returned. Please try again later."
    return QueryResponse(question=request.question, answer=response)
