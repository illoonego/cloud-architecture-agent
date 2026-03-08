# src/api/auth.py
"""
API Key Authentication for FastAPI endpoints.

This module provides security for API endpoints by validating API keys
sent in the X-API-Key header. Keys are configured via environment variables.
"""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from src.config.settings import settings

# Define the API key header scheme
# This tells FastAPI to look for the "X-API-Key" header in requests
api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=True,  # Automatically return 403 if header is missing
    description="API key for authentication",
)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Validate the API key from the request header.

    Args:
        api_key: The API key from the X-API-Key header (auto-extracted by FastAPI)

    Returns:
        str: The validated API key

    Raises:
        HTTPException: 401 if the API key is invalid

    Usage:
        @app.post("/protected-endpoint")
        def my_endpoint(api_key: str = Depends(verify_api_key)):
            # This only runs if API key is valid
            ...
    """
    try:
        valid_keys = settings.api_keys_list
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    # Check if any keys are configured
    if not valid_keys:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "API keys not configured. Configure AWS Secrets Manager "
                "(AWS_SECRET_NAME/AWS_REGION)."
            ),
        )

    # Validate the provided key
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key
