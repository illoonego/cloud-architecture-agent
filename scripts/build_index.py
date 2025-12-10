#!/usr/bin/env python3
"""
Build the RAG index by loading sample AWS documentation.

This script populates the Qdrant vector database with AWS service
documentation so the agent has knowledge to retrieve.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rag.indexing import Indexer



# Load all Markdown files from data/aws_docs/
RAW_DOCS_DIR = Path("data/aws_docs")

def read_markdown_files(directory: Path) -> list[str]:
    docs = []
    for file in directory.glob("*.md"):
        text = file.read_text(encoding="utf-8")
        docs.append(text)
    return docs

# Simple chunking: split each doc into ~800-character chunks
def chunk_text(text: str, chunk_size: int = 800) -> list[str]:
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 < chunk_size:
            current += para + "\n\n"
        else:
            if current:
                chunks.append(current.strip())
            current = para + "\n\n"
    if current:
        chunks.append(current.strip())
    return chunks



def main():
    print("Starting indexing process...")
    docs = read_markdown_files(RAW_DOCS_DIR)
    print(f"Loaded {len(docs)} raw documents.")

    # Chunk all docs
    all_chunks = []
    for doc in docs:
        chunks = chunk_text(doc)
        all_chunks.extend(chunks)
    print(f"Total chunks to index: {len(all_chunks)}")

    # Initialize indexer
    indexer = Indexer()

    # Index chunks
    indexer.index_documents(all_chunks)

    print(f"✅ Successfully indexed {len(all_chunks)} chunks!")
    print("\nYou can now query the agent with questions like:")
    print("  - What is AWS Lambda?")
    print("  - How does S3 ensure durability?")
    print("  - What is the difference between EC2 and Lambda?")


if __name__ == "__main__":
    main()
