"""
scripts/fetch_docs.py

Fetch selected AWS documentation pages and save their main content
into Markdown files under data/aws_docs/.

Usage:
    python scripts/fetch_docs.py
"""

from __future__ import annotations

import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# --------- Config --------- #

SAVE_DIR = Path("data/aws_docs")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# List of (filename, url) pairs.
# You can add/remove entries as you like.
DOCS_TO_FETCH: list[dict[str, str]] = [
    # VPC & Networking
    {
        "filename": "vpc-what-is-amazon-vpc.md",
        "url": "https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html",
    },
    {
        "filename": "vpc-subnets.md",
        "url": "https://docs.aws.amazon.com/vpc/latest/userguide/configure-subnets.html",
    },
    {
        "filename": "vpc-route-tables.md",
        "url": "https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html",
    },
    {
        "filename": "vpc-internet-gateway.md",
        "url": "https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html",
    },
    {
        "filename": "vpc-nat-gateway.md",
        "url": "https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html",
    },
    {
        "filename": "vpc-security-groups.md",
        "url": "https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html",
    },
    {
        "filename": "vpc-network-acls.md",
        "url": "https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html",
    },
    {
        "filename": "vpc-peering.md",
        "url": "https://docs.aws.amazon.com/vpc/latest/peering/what-is-vpc-peering.html",
    },
    {
        "filename": "transit-gateway.md",
        "url": "https://docs.aws.amazon.com/vpc/latest/tgw/what-is-transit-gateway.html",
    },
    # Load Balancing / Auto Scaling
    {
        "filename": "elb-introduction.md",
        "url": "https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/introduction.html",
    },
    {
        "filename": "alb-introduction.md",
        "url": "https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html",
    },
    {
        "filename": "ec2-auto-scaling.md",
        "url": "https://docs.aws.amazon.com/autoscaling/ec2/userguide/what-is-amazon-ec2-auto-scaling.html",
    },
    # Compute
    {
        "filename": "ec2-concepts.md",
        "url": "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html",
    },
    {
        "filename": "ecs-welcome.md",
        "url": "https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html",
    },
    {
        "filename": "containers-on-aws.md",
        "url": "https://docs.aws.amazon.com/whitepapers/latest/container-services-on-aws/",
    },
    # Serverless
    {
        "filename": "lambda-welcome.md",
        "url": "https://docs.aws.amazon.com/lambda/latest/dg/welcome.html",
    },
    {
        "filename": "apigateway-welcome.md",
        "url": "https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html",
    },
    # Storage & Databases
    {
        "filename": "s3-welcome.md",
        "url": "https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html",
    },
    {
        "filename": "rds-welcome.md",
        "url": "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html",
    },
    {
        "filename": "dynamodb-introduction.md",
        "url": "https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html",
    },
    # Security / IAM
    {
        "filename": "iam-introduction.md",
        "url": "https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html",
    },
    {
        "filename": "iam-best-practices.md",
        "url": "https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html",
    },
    # Well-Architected
    {
        "filename": "well-architected-framework-welcome.md",
        "url": "https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html",
    },
    {
        "filename": "well-architected-reliability-pillar.md",
        "url": "https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html",
    },
    {
        "filename": "well-architected-security-pillar.md",
        "url": "https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html",
    },
]


# --------- Helpers --------- #

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AWS-Cloud-Architecture-Agent/1.0)"}


def fetch_html(url: str) -> str:
    """
    Fetch raw HTML from a URL with basic error handling.
    """
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def extract_main_text(html: str) -> str:
    """
    Extract the main documentation content from an AWS docs page.

    We primarily look for the .awsdocs-content container, and fall back
    to <main> or <body> if needed.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Try AWS docs main container
    main = soup.find("div", {"class": "awsdocs-content"})
    if main is None:
        # Fallbacks
        main = soup.find("main") or soup.find("body")

    if main is None:
        # As a last resort, return everything
        main = soup

    # Get the page title for context
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "AWS Documentation"

    # Extract visible text with newlines between blocks
    text = main.get_text(separator="\n")

    # Normalize whitespace: strip and collapse multiple blank lines
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]  # drop empty lines
    cleaned_text = "\n\n".join(lines)

    # Make it Markdown-like: heading with title + body text
    md = f"# {title}\n\n{cleaned_text}\n"
    return md


def save_markdown(filename: str, content: str) -> None:
    """
    Save given content into SAVE_DIR / filename.
    """
    path = SAVE_DIR / filename
    path.write_text(content, encoding="utf-8")
    print(f"  -> Saved to {path}")


# --------- Main --------- #


def main() -> None:
    print(f"[fetch_docs] Output directory: {SAVE_DIR.resolve()}")
    for doc in DOCS_TO_FETCH:
        filename = doc["filename"]
        url = doc["url"]

        print(f"[fetch_docs] Fetching: {url}")
        try:
            html = fetch_html(url)
            md_content = extract_main_text(html)
            save_markdown(filename, md_content)
        except Exception as e:
            print(f"  !! Failed to fetch {url}: {e}")

        # Be polite: small delay between requests
        time.sleep(1.0)

    print("[fetch_docs] Done.")


if __name__ == "__main__":
    main()
