# AWS Cloud Architecture Agent

A production-grade GenAI agent backend for AWS cloud architecture reasoning, built with Python, FastAPI, and vLLM.

> **Note on AWS Documentation**: This project fetches AWS documentation from [docs.aws.amazon.com](https://docs.aws.amazon.com/) which is licensed under [CC-BY-SA-4.0](https://creativecommons.org/licenses/by-sa/4.0/). Documentation is not included in this repository; users must fetch it themselves using the provided script for educational and research purposes.

## Features

- **RAG-powered**: Retrieval-Augmented Generation using Qdrant vector database
- **Self-hosted LLM**: Uses vLLM for high-performance model serving
- **Modular architecture**: Clean separation of concerns (API, Agent, RAG, LLM)
- **Containerized**: Docker-ready for easy deployment
- **Production-ready**: Designed for AWS deployment with CI/CD

## Architecture

```
User → FastAPI → AgentRouter → {RAG + LLM} → Response
```

See [docs/architecture.md](docs/architecture.md) for detailed architecture diagrams.

## Prerequisites

- Python 3.10+
- Docker (optional, for containerization)
- AWS EC2 GPU instance (for vLLM deployment)

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/illoonego/cloud-architecture-agent.git
cd cloud-architecture-agent
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .

# Fetch AWS documentation for RAG
python scripts/fetch_docs.py
```

### 2. Configure Environment

Create a `.env` file:

```bash
# LLM Configuration
# Use Elastic IP (static) - won't change on EC2 stop/start
# Elastic IP setup: AWS Console → EC2 → Elastic IPs → Allocate → Associate with instance
VLLM_API_URL=http://<YOUR-ELASTIC-IP>:8000/v1
MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct

# RAG Configuration
QDRANT_URL=http://localhost:6333  # For local Qdrant in Docker
EMBEDDING_MODEL=all-MiniLM-L6-v2

# API Configuration
PROJECT_NAME=Cloud Architecture Agent
API_V1_STR=/api/v1
```

### 3. Build RAG Index

```bash
# Index AWS documentation into Qdrant
python scripts/build_index.py
```

### 4. Start Qdrant Vector Database

```bash
# Run Qdrant locally in Docker
docker run -d --name qdrant -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest
```

### 5. Run the API

```bash
source .venv/bin/activate
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8001
```

The API will be available at `http://localhost:8001`.

## API Endpoints

### Health Check
```bash
curl http://localhost:8001/health
```

### Query the Agent
```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I set up VPC peering in AWS?"}'
```

### Interactive Documentation
Visit `http://localhost:8001/docs` for Swagger UI.

## vLLM Deployment on AWS EC2

### Deploy vLLM on EC2 GPU Instance

**Prerequisites:**
- AWS EC2 g4dn.xlarge or g5.xlarge instance (with GPU)
- Ubuntu 24.04 Deep Learning AMI
- Docker with NVIDIA Container Toolkit installed
- HuggingFace token for Llama model access

**Deploy using official vLLM image:**
```bash
# SSH into EC2 instance (use Elastic IP for stable address)
ssh -i your-key.pem ubuntu@<YOUR-ELASTIC-IP>

# Run vLLM server
docker run -d --name vllm-server \
  --gpus all \
  -p 8000:8000 \
  -e HUGGING_FACE_HUB_TOKEN='your-hf-token' \
  -v /home/ubuntu/models:/root/.cache/huggingface \
  --restart unless-stopped \
  vllm/vllm-openai:v0.6.2 \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --dtype half \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.9
```

**Test deployment:**
```bash
curl http://<YOUR-ELASTIC-IP>:8000/health
```

### Cost Management

**Stop EC2 when not in use to save money:**
- g4dn.xlarge costs ~$0.526/hour ($378/month if running 24/7)
- Stopping the instance stops compute charges
- Storage charges continue (~$5-10/month)
- With Elastic IP allocated, the IP stays the same after restart
- Without Elastic IP, public IP changes on restart (requires `.env` update)

**To stop:** AWS Console → EC2 → Select instance → Instance state → Stop instance

### Production Deployment

See [docs/ec2-setup-walkthrough.md](docs/ec2-setup-walkthrough.md) for complete step-by-step guide including:
- EC2 instance launch and configuration
- Docker and GPU setup
- Security group configuration
- vLLM deployment and monitoring

## Project Structure

```
├── .github/
│   └── workflows/    # CI/CD pipelines (GitHub Actions)
├── data/             # AWS docs (gitignored - run scripts/fetch_docs.py)
├── docs/             # Project documentation
│   ├── api.md        # API reference
│   ├── architecture.md  # System architecture
│   ├── deployment.md    # Deployment guide
│   └── ec2-setup-walkthrough.md  # EC2 setup tutorial
├── infra/
│   ├── docker/       # Dockerfiles (API & vLLM)
│   └── aws/          # AWS infrastructure docs
├── scripts/          # Utility scripts
│   ├── build_index.py    # Build RAG index
│   ├── fetch_docs.py     # Fetch AWS docs
│   ├── run_eval.py       # Run evaluations
│   └── deploy_vllm.sh    # Deploy vLLM to EC2
├── src/
│   ├── api/          # FastAPI application
│   ├── agent/        # Agent orchestration (router + tools)
│   ├── llm/          # LLM client (vLLM integration)
│   ├── rag/          # RAG components (embeddings, indexing, retrieval)
│   ├── config/       # Configuration management
│   └── monitoring/   # Logging and metrics
├── tests/            # Unit and integration tests
├── .env.example      # Environment variables template
├── pyproject.toml    # Project dependencies and config
└── README.md         # This file
```

## Development

### Install Development Dependencies
```bash
# Install with dev tools (testing, linting, etc.)
pip install -e ".[dev]"
```

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
black src/
ruff check src/
```

## Deployment

### Local Development
1. Run Qdrant: `docker run -d --name qdrant -p 6333:6333 qdrant/qdrant:latest`
2. Set Elastic IP in `.env`: `VLLM_API_URL=http://<YOUR-ELASTIC-IP>:8000/v1`
3. Run FastAPI: `python -m uvicorn src.api.main:app --reload --port 8001`

**Note**: Use an [AWS Elastic IP](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html) for a stable address that won't change on EC2 stop/start (free while instance is running, ~$3.65/month when stopped).

### Production Deployment
See [docs/deployment.md](docs/deployment.md) for:
- CI/CD with GitHub Actions
- AWS ECS deployment (FastAPI)
- AWS EC2 GPU deployment (vLLM)
- Infrastructure as code setup

## Scripts

- **`scripts/fetch_docs.py`** - Web scraper to fetch AWS documentation from official AWS docs
- **`scripts/build_index.py`** - Build RAG vector index from fetched docs
- **`scripts/get_ec2_ip.sh`** - Helper to get current EC2 public IP (changes on restart)
- **`scripts/run_eval.py`** - Run agent evaluations
- **`scripts/deploy_vllm.sh`** - Deploy vLLM to EC2

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Install dev dependencies: `pip install -e ".[dev]"`
4. Make your changes
5. Run tests: `pytest tests/`
6. Run linting: `black src/ && ruff check src/`
7. Commit changes: `git commit -m 'Add amazing feature'`
8. Push to branch: `git push origin feature/amazing-feature`
9. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details
