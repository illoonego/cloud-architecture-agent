"""Helpers for fetching runtime secrets from AWS Secrets Manager."""

from functools import lru_cache
from typing import cast

import boto3


@lru_cache(maxsize=8)
def get_secret(secret_name: str, region_name: str) -> str:
    """Fetch and cache the SecretString for a given secret name/region."""
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    secret = response.get("SecretString")
    if not isinstance(secret, str):
        raise ValueError(f"SecretString is missing or not a string for secret '{secret_name}'")
    return cast(str, secret)
