# Deployment Guide

This guide covers deploying the Cloud Architecture Agent to AWS using the automated CI/CD pipeline.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [AWS Infrastructure Setup](#aws-infrastructure-setup)
3. [GitHub Secrets Configuration](#github-secrets-configuration)
4. [Deployment Workflow](#deployment-workflow)
5. [Manual Deployment Steps](#manual-deployment-steps)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools
- AWS CLI v2
- Docker Desktop
- Git
- GitHub account with Actions enabled

### AWS Resources Needed
- ECR repositories (2): API and vLLM images
- ECS Cluster with Fargate
- EC2 GPU instance (g4dn.xlarge or g5.xlarge) for vLLM
- VPC with public/private subnets
- Application Load Balancer (optional)
- IAM roles and policies

### AWS Account Quotas
- GPU instance quota (g5.xlarge) - request increase if needed
- ECR storage limit
- ECS service limits

---

## AWS Infrastructure Setup

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

- [ ] Set up CloudWatch alarms for critical metrics
- [ ] Configure Auto Scaling policies
- [ ] Add authentication (API keys, OAuth)
- [ ] Implement request rate limiting
- [ ] Set up Qdrant server mode (persistent storage)
- [ ] Add Terraform/CDK for infrastructure as code
