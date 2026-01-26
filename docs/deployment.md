# Deployment Guide

This guide covers deploying the Cloud Architecture Agent to AWS.

## Table of Contents
1. [Current Production Architecture](#current-production-architecture)
2. [Prerequisites](#prerequisites)
3. [Local Development Setup](#local-development-setup)
4. [AWS EC2 vLLM Setup](#aws-ec2-vllm-setup)
5. [Security Configuration](#security-configuration)
6. [Future: ECS/Fargate Deployment](#future-ecsfargate-deployment)
7. [Troubleshooting](#troubleshooting)

---

## Current Production Architecture

**Actual Deployed Setup:**

```
┌──────────────────┐
│  Local Machine   │
│                  │
│  ┌────────────┐  │
│  │  FastAPI   │  │  ← Runs locally with uvicorn
│  │  API       │  │  ← Port 8001
│  │            │  │  ← API keys + rate limiting
│  └─────┬──────┘  │
│        │         │
└────────┼─────────┘
         │
         │ HTTP requests to vLLM
         │
         ▼
┌──────────────────────────┐
│   AWS EC2 (g4dn.xlarge)  │
│   54.86.51.139 (Elastic) │
│                          │
│   ┌────────────────┐     │
│   │  vLLM Server   │     │
│   │  (Docker)      │     │
│   │  Port 8000     │     │
│   │  Llama-3.1-8B  │     │
│   └────────────────┘     │
└──────────────────────────┘
```

**Why This Architecture:**
- API runs locally: Easy development, no ECS costs
- vLLM on EC2: GPU required, stopped when not in use (~$0.526/hour)
- Elastic IP: Fixed IP address (54.86.51.139) for consistent access
- Portfolio project: Cost-optimized, EC2 stopped most of the time

**Cost:** ~$12/day when running, $0 when stopped

---

## Prerequisites

### Required Tools
- Python 3.10+
- Docker Desktop (for EC2 vLLM)
- AWS CLI v2
- Git

### AWS Resources (Current Setup)
- ✅ EC2 GPU instance: g4dn.xlarge with T4 GPU
- ✅ Elastic IP: 54.86.51.139
- ✅ Security Group: Allows port 22 (SSH) and 8000 (vLLM)
- ✅ IAM Role: EC2 with SSM and ECR read permissions

### AWS Resources (Future ECS Deployment)
- ECR repositories for API and vLLM images
- ECS Cluster with Fargate
- VPC with public/private subnets
- Application Load Balancer
- Additional IAM roles and policies

---

## Local Development Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/cloud-architecture-agent.git
cd cloud-architecture-agent
```

### Step 2: Create Environment File

Create `.env` file:

```bash
# LLM Configuration
VLLM_API_URL=http://54.86.51.139:8000/v1  # Elastic IP
VLLM_MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct

# RAG Configuration
QDRANT_URL=:memory:  # In-memory mode
EMBEDDING_MODEL=all-MiniLM-L6-v2
QUERY_TOP_K=5

# Security
API_KEYS=key1,key2,key3  # Generate with: openssl rand -hex 32

# Server
HOST=0.0.0.0
PORT=8001
```

### Step 3: Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -e .
```

### Step 4: Build Qdrant Index

```bash
python scripts/build_index.py
```

### Step 5: Run API Server

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload
```

**Test:**
```bash
# Health check
curl http://localhost:8001/health

# Test query (replace with your API key)
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"question": "What is AWS Lambda?"}'
```

---

## AWS EC2 vLLM Setup

See [ec2-setup-walkthrough.md](ec2-setup-walkthrough.md) for complete EC2 GPU instance setup.

**Quick Reference:**

```bash
# SSH to EC2
ssh -i ~/.ssh/aws-keys/vllm-key.pem ubuntu@54.86.51.139

# Check vLLM status
docker ps
docker logs -f vllm-server

# Restart vLLM
docker restart vllm-server
```

**Start/Stop EC2 (Cost Management):**

```bash
# Stop when not needed
aws ec2 stop-instances --instance-ids i-YOUR-INSTANCE-ID

# Start when needed
aws ec2 start-instances --instance-ids i-YOUR-INSTANCE-ID

# Get status
aws ec2 describe-instances --instance-ids i-YOUR-INSTANCE-ID \
  --query 'Reservations[0].Instances[0].State.Name'
```

---

## Security Configuration

### API Key Management

**Generate API Keys:**
```bash
# Generate 3 secure keys
openssl rand -hex 32
openssl rand -hex 32
openssl rand -hex 32
```

**Store in `.env`:**
```bash
API_KEYS=key1,key2,key3
```

**⚠️ Security Notes:**
- Never commit `.env` to Git (already in `.gitignore`)
- Share keys securely (1Password, encrypted channels)
- Rotate keys periodically
- For production: Use AWS Secrets Manager

### Rate Limiting

**Current Configuration:**
- 5 requests per minute per IP address
- Implemented with slowapi
- Returns 429 when exceeded

**Code Location:** `src/api/main.py`

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("5/minute")
@app.post("/query")
async def query_endpoint(...):
    # Rate limited endpoint
```

### EC2 Security Group

**Current Rules:**
- Port 22 (SSH): Your IP only
- Port 8000 (vLLM): Your IP only (for testing)

**For Production:**
```bash
# Add your API server's IP to security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-YOUR-SG-ID \
  --protocol tcp \
  --port 8000 \
  --cidr YOUR_API_SERVER_IP/32
```

**Note:** Current setup doesn't restrict port 8000 since EC2 is stopped most of the time. For 24/7 production, restrict to API server IP only.

### Elastic IP Benefits

✅ **Fixed address**: 54.86.51.139 doesn't change when EC2 stops/starts  
✅ **No .env updates**: API always connects to same IP  
✅ **Cost**: Free when attached to running instance, $0.005/hour when detached  

---

## Future: ECS/Fargate Deployment

**Note:** This section describes a future production architecture. Current setup runs API locally.

### Step 1: Create ECR Repositories

```bash
# Login to AWS
aws configure

# Create ECR repository for API
aws ecr create-repository \
  --repository-name cloud-architecture-agent-api \
  --region us-east-1

# Create ECR repository for vLLM
aws ecr create-repository \
  --repository-name cloud-architecture-agent-vllm \
  --region us-east-1
```

### Step 2: Create ECS Cluster

```bash
aws ecs create-cluster \
  --cluster-name cloud-architecture-cluster \
  --region us-east-1
```

### Step 3: Launch EC2 GPU Instance for vLLM

Follow the guide in `infra/aws/ec2-gpu-setup.md`:

1. Launch g4dn.xlarge or g5.xlarge instance
2. Use Deep Learning AMI (Ubuntu 22.04 or 24.04)
3. Configure Security Group (ports 22, 8000)
4. Install Docker and NVIDIA Container Toolkit
5. Install AWS Systems Manager Agent (for automated deployment)

### Step 4: Create ECS Task Definition

Create a file `task-definition.json`:

```json
{
  "family": "cloud-architecture-api-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "api-container",
      "image": "<ECR_REGISTRY>/cloud-architecture-agent-api:latest",
      "portMappings": [
        {
          "containerPort": 8001,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "VLLM_API_URL",
          "value": "http://<EC2_PRIVATE_IP>:8000/v1"
        },
        {
          "name": "QDRANT_URL",
          "value": ":memory:"
        },
        {
          "name": "EMBEDDING_MODEL",
          "value": "all-MiniLM-L6-v2"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/cloud-architecture-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8001/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

Register the task definition:

```bash
aws ecs register-task-definition \
  --cli-input-json file://task-definition.json
```

### Step 5: Create ECS Service

```bash
aws ecs create-service \
  --cluster cloud-architecture-cluster \
  --service-name cloud-architecture-api-service \
  --task-definition cloud-architecture-api-task \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

---

## GitHub Secrets Configuration

Add the following secrets to your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

### Required Secrets

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `AWS_ACCESS_KEY_ID` | AWS access key | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `EC2_VLLM_INSTANCE_ID` | EC2 instance ID for vLLM | `i-0123456789abcdef0` |
| `API_ENDPOINT_URL` | ECS service URL | `http://api-lb-xxx.us-east-1.elb.amazonaws.com` |

### Optional Secrets
- `SLACK_WEBHOOK_URL` - For deployment notifications
- `DATADOG_API_KEY` - For monitoring integration

---

## Deployment Workflow

### Automated Deployment (Recommended)

The CI/CD pipeline automatically triggers on:

1. **Push to `main` branch** → Full deployment to production
2. **Create tag `v*.*.*`** → Versioned release deployment
3. **Manual trigger** → Deploy to staging/production

**Workflow Steps:**

```
┌─────────────────┐
│ Push to main    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Run CI Tests    │  ← Linting, unit tests, security scan
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Build Docker    │  ← Build API + vLLM images
│ Images          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Push to ECR     │  ← Upload images to AWS ECR
└────────┬────────┘
         │
         ├─────────────────┬──────────────────┐
         ▼                 ▼                  ▼
┌────────────────┐  ┌──────────────┐  ┌──────────────┐
│ Deploy to ECS  │  │ Deploy to EC2│  │ Run Smoke    │
│ (API)          │  │ (vLLM)       │  │ Tests        │
└────────────────┘  └──────────────┘  └──────────────┘
```

### Manual Deployment

If you need to deploy manually:

```bash
# 1. Build Docker images locally
docker build -f infra/docker/Dockerfile.api -t api:local .
docker build -f infra/docker/Dockerfile.vllm -t vllm:local infra/docker/

# 2. Tag images
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ECR_REGISTRY>
docker tag api:local <ECR_REGISTRY>/cloud-architecture-agent-api:manual
docker tag vllm:local <ECR_REGISTRY>/cloud-architecture-agent-vllm:manual

# 3. Push to ECR
docker push <ECR_REGISTRY>/cloud-architecture-agent-api:manual
docker push <ECR_REGISTRY>/cloud-architecture-agent-vllm:manual

# 4. Update ECS service
aws ecs update-service \
  --cluster cloud-architecture-cluster \
  --service cloud-architecture-api-service \
  --force-new-deployment
```

---

## Monitoring and Logging

### CloudWatch Logs

View API logs:
```bash
aws logs tail /ecs/cloud-architecture-api --follow
```

### Health Checks

- **API**: `http://<ECS_SERVICE_URL>/health`
- **vLLM**: `http://<EC2_PUBLIC_IP>:8000/health`

### Metrics

Monitor in CloudWatch:
- ECS CPU/Memory utilization
- API request latency
- EC2 GPU utilization

---

## Troubleshooting

### Common Issues

**Issue**: Docker image too large (>15GB)
- **Solution**: Use optimized Dockerfile.vllm (now uses multi-stage builds)

**Issue**: ECS task fails to start
- **Solution**: Check CloudWatch logs, verify environment variables

**Issue**: Cannot connect to vLLM server
- **Solution**: Verify EC2 security group allows port 8000, check EC2 instance status

**Issue**: GitHub Actions failing
- **Solution**: Verify all secrets are set correctly, check AWS permissions

### Rollback Procedure

```bash
# List previous task definitions
aws ecs list-task-definitions --family-prefix cloud-architecture-api-task

# Update service to previous version
aws ecs update-service \
  --cluster cloud-architecture-cluster \
  --service cloud-architecture-api-service \
  --task-definition cloud-architecture-api-task:X
```

---

## Cost Optimization

- Use ECS Fargate Spot for non-production
- Stop EC2 GPU instance when not in use
- Set up Auto Scaling for ECS service
- Use ECR lifecycle policies to remove old images

---

## Security Best Practices

1. **IAM**: Use least-privilege IAM roles
2. **Secrets**: Never commit AWS credentials to Git
3. **VPC**: Deploy in private subnets with NAT Gateway
4. **ALB**: Use HTTPS with ACM certificates
5. **Security Groups**: Restrict inbound traffic to known IPs

---

## Next Steps

### Completed ✅
- [x] API key authentication (3 keys generated)
- [x] Rate limiting (5 req/min per IP)
- [x] Elastic IP for vLLM (54.86.51.139)
- [x] EC2 GPU instance with Docker vLLM
- [x] Local API development setup
- [x] Proper HTTP error codes (401, 422, 429, 503, 500)

### Future Enhancements 🔄
- [ ] Move API to ECS Fargate (containerized deployment)
- [ ] AWS Secrets Manager for API keys
- [ ] CloudWatch alarms for GPU/API metrics
- [ ] Qdrant server mode (persistent storage)
- [ ] HTTPS with SSL certificates
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Terraform/CDK for infrastructure as code
- [ ] Per-key rate limiting
- [ ] API key rotation automation
