"""Helpers for fetching runtime secrets from AWS Secrets Manager."""

from functools import lru_cache

import boto3


@lru_cache(maxsize=8)
def get_secret(secret_name: str, region_name: str) -> str:
    """Fetch and cache the SecretString for a given secret name/region."""
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    return response["SecretString"]
