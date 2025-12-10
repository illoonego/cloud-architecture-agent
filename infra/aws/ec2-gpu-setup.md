# AWS EC2 GPU Setup for vLLM

**✅ DEPLOYMENT COMPLETE** - See [docs/DEPLOYMENT_COMPLETE.md](../../docs/DEPLOYMENT_COMPLETE.md) for current production setup.

This guide provides general instructions for setting up vLLM on AWS EC2. For the actual deployed configuration, refer to the deployment summary.

---

## Current Production Deployment

- **Instance Type:** g4dn.xlarge (NVIDIA T4, 16GB VRAM)
- **AMI:** Deep Learning OSS Nvidia Driver GPU AMI (Ubuntu 24.04)
- **vLLM Image:** vllm/vllm-openai:v0.6.2 (official Docker image)
- **Model:** meta-llama/Llama-3.1-8B-Instruct
- **Deployment Method:** Docker container (not systemd service)

---

## Prerequisites

- AWS account with EC2 access
- AWS CLI configured
- SSH key pair created

## Step 1: Launch EC2 GPU Instance

### Current Production Setup
- **Instance Type:** g4dn.xlarge (1x NVIDIA T4 GPU, 4 vCPUs, 16 GB RAM) - ~$0.526/hour
- **AMI:** Deep Learning OSS Nvidia Driver GPU AMI (Ubuntu 24.04)
- **Storage:** 100 GB gp3

### Recommended Instance Types
- **g4dn.xlarge** (1x NVIDIA T4, 4 vCPUs, 16 GB RAM) - ~$0.526/hour - ✅ Used in production
- **g5.xlarge** (1x NVIDIA A10G GPU, 4 vCPUs, 16 GB RAM) - ~$1.00/hour
- **g5.2xlarge** (1x NVIDIA A10G GPU, 8 vCPUs, 32 GB RAM) - ~$1.21/hour

### Launch via AWS Console

1. Go to EC2 Dashboard → Launch Instance
2. **Name**: `vllm-server`
3. **AMI**: Deep Learning AMI GPU PyTorch 2.0 (Ubuntu 20.04)
4. **Instance type**: `g5.xlarge`
5. **Key pair**: Select your SSH key
6. **Security Group**: 
   - Allow SSH (port 22) from your IP
   - Allow Custom TCP (port 8000) from your IP or VPC
7. **Storage**: 100 GB gp3
8. Launch instance

## Step 2: Connect to Instance

```bash
ssh -i your-key.pem ubuntu@<instance-public-ip>
```

## Step 3: Install Docker & NVIDIA Container Toolkit

### Current Production Method (Recommended)

The Deep Learning AMI comes with Docker pre-installed. Just install NVIDIA Container Toolkit:

```bash
# Update system
sudo apt update

# Verify GPU
nvidia-smi

# Configure NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Verify Docker can access GPU
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

## Step 4: Deploy vLLM with Docker

### Production Deployment (Recommended)

Use the official vLLM Docker image:

```bash
docker run -d --name vllm-server \
  --gpus all \
  -p 8000:8000 \
  -e HUGGING_FACE_HUB_TOKEN='your-hf-token-here' \
  -v /home/ubuntu/models:/root/.cache/huggingface \
  --restart unless-stopped \
  vllm/vllm-openai:v0.6.2 \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --dtype half \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.9
```

**Parameters explained:**
- `--gpus all` - Use all available GPUs
- `-p 8000:8000` - Expose port 8000
- `-e HUGGING_FACE_HUB_TOKEN` - For downloading gated models (Llama)
- `-v /home/ubuntu/models` - Cache models to avoid re-downloading
- `--restart unless-stopped` - Auto-restart on EC2 reboot
- `--dtype half` - Use FP16 for 50% memory savings
- `--max-model-len 4096` - Maximum sequence length
- `--gpu-memory-utilization 0.9` - Use 90% of GPU memory

### Alternative: Custom Dockerfile (Not Recommended)

**Note:** We attempted custom Dockerfile builds but encountered issues with multiprocessing and dependencies. The official image is more reliable.

See `infra/docker/Dockerfile.vllm` for reference (not used in production).

## Step 5: Verify Deployment

```bash
# Check container is running
docker ps | grep vllm-server

# View logs
docker logs -f vllm-server

# Wait for model to load (2-3 minutes)
# Look for: "Capturing the model for CUDA graphs..."

# Test health endpoint
curl http://localhost:8000/health

# Test inference
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
  }'
```

## Step 6: Update Agent Configuration

Update your `.env` file on your local machine:

```bash
# Get EC2 public IP from AWS Console
VLLM_API_URL=http://<ec2-public-ip>:8000/v1
MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
QDRANT_URL=http://localhost:6333
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

**⚠️ Important:** The public IP changes every time you stop/start the EC2 instance. You'll need to update this value each time.

**For production:** Use an Elastic IP (static IP that doesn't change) to avoid this issue.

## Security Best Practices

1. **Use VPC**: Place EC2 in a private subnet, use VPN or bastion host
2. **Security Groups**: Restrict port 8000 to your application's IP only
3. **HTTPS**: Use nginx reverse proxy with SSL certificate
4. **API Key**: Add authentication layer (vLLM doesn't have built-in auth)

## Cost Optimization

### Stop/Start Instance to Save Money

**Current costs (g4dn.xlarge):**
- **Running:** ~$0.526/hour ($378/month if 24/7)
- **Stopped:** ~$0.10/GB/month for storage only (~$5-10/month)

**To stop instance (AWS Console):**
1. EC2 Dashboard → Instances
2. Select your instance
3. Instance State → Stop instance
4. Confirm

**What happens:**
- ✅ Compute charges stop immediately
- ✅ Docker container and model files preserved
- ✅ Can restart anytime
- ⚠️ Public IP will change on restart

**To restart:**
1. Instance State → Start instance
2. Wait 2-3 minutes
3. Get new public IP
4. Update `.env` file with new IP
5. vLLM auto-starts (due to `--restart unless-stopped`)

### Other Options
- **Spot Instances**: Save up to 70% (risk of interruption) - Not recommended for production
- **Elastic IP**: Static IP that doesn't change ($0.005/hour when instance running)
- **Reserved Instances**: Commit to 1-3 years for 30-60% discount
- **Auto-shutdown**: Use CloudWatch + Lambda to stop instance when idle

## Monitoring

### Check Container Status
```bash
# View running containers
docker ps

# View logs in real-time
docker logs -f vllm-server

# Check container resource usage
docker stats vllm-server
```

### Check GPU Usage
```bash
# Real-time GPU monitoring
watch -n 1 nvidia-smi

# Expected during inference:
# - GPU Utilization: 80-100%
# - Memory Usage: ~15GB / 16GB
# - Temperature: 60-85°C
```

### Performance Metrics
```bash
# Test inference latency
time curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'
```

**Expected performance on g4dn.xlarge (T4 GPU):**
- Model load time: 2-3 minutes
- First inference: 1-2 seconds (cold start)
- Subsequent inference: <1 second for 50 tokens

## Troubleshooting

### Container Won't Start
```bash
# Check all containers (including stopped)
docker ps -a

# View error logs
docker logs vllm-server

# Common issues:
# 1. GPU not accessible → Verify nvidia-smi works
# 2. Out of disk space → Run docker system prune -a -f
# 3. Port 8000 in use → Change port mapping: -p 8001:8000
```

### Out of Memory (OOM)
**Symptoms:** Container crashes, GPU OOM errors in logs

**Solutions:**
```bash
# Option 1: Lower GPU memory utilization
--gpu-memory-utilization 0.8  # Instead of 0.9

# Option 2: Reduce max sequence length
--max-model-len 2048  # Instead of 4096

# Option 3: Use smaller model
--model meta-llama/Llama-3.2-3B-Instruct  # 3B model instead of 8B
```

### Slow Inference
**Debug steps:**
```bash
# 1. Check GPU utilization
nvidia-smi
# Should show 80-100% during inference

# 2. Check disk I/O (if model not cached)
iostat -x 1

# 3. Check network latency (if calling from remote)
ping <ec2-public-ip>
```

**Solutions:**
- Ensure model is cached (first run downloads, subsequent runs are faster)
- Use g5 instances (A10G GPU) for better performance
- Enable tensor parallelism for multi-GPU: `--tensor-parallel-size 2`

### Connection Refused (from FastAPI)
**Symptoms:** FastAPI can't connect to vLLM endpoint

**Debug:**
```bash
# 1. Test from EC2 itself
curl http://localhost:8000/health

# 2. Test from your Mac
curl http://<ec2-public-ip>:8000/health

# 3. Check Security Group allows port 8000
# AWS Console → EC2 → Security Groups → Check inbound rules
```

**Common causes:**
- EC2 instance stopped → Start it
- Security Group doesn't allow port 8000 → Add inbound rule
- Wrong IP in `.env` file → Update with current public IP
- vLLM container not running → `docker start vllm-server`

### Model Download Fails
**Symptoms:** Container exits, logs show "Repo not found" or permission errors

**Solutions:**
```bash
# 1. Verify HuggingFace token has access to Llama models
# Go to: https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct
# Click "Agree and access repository"

# 2. Test token
docker run --rm -e HUGGING_FACE_HUB_TOKEN='your-token' \
  vllm/vllm-openai:v0.6.2 \
  huggingface-cli whoami

# 3. Manually download model first
docker run --rm -v /home/ubuntu/models:/root/.cache/huggingface \
  -e HUGGING_FACE_HUB_TOKEN='your-token' \
  vllm/vllm-openai:v0.6.2 \
  huggingface-cli download meta-llama/Llama-3.1-8B-Instruct
```

### Instance Type Not Available
**Error:** "Your requested instance type is not supported in your requested Availability Zone"

**Solutions:**
- Try different Availability Zone in same region
- Try different instance type (g5.xlarge instead of g4dn.xlarge)
- Request quota increase if you hit service limits

---

## Quick Reference

### Production Deployment Command
```bash
docker run -d --name vllm-server \
  --gpus all -p 8000:8000 \
  -e HUGGING_FACE_HUB_TOKEN='your-hf-token' \
  -v /home/ubuntu/models:/root/.cache/huggingface \
  --restart unless-stopped \
  vllm/vllm-openai:v0.6.2 \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --dtype half \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.9
```

### Useful Commands
```bash
# Container management
docker ps                        # List running containers
docker logs -f vllm-server      # View logs
docker stop vllm-server         # Stop container
docker start vllm-server        # Start container
docker restart vllm-server      # Restart container
docker rm -f vllm-server        # Remove container

# GPU monitoring
nvidia-smi                      # Current GPU status
watch -n 1 nvidia-smi          # Real-time monitoring

# Testing
curl http://localhost:8000/health                    # Health check
curl http://localhost:8000/v1/models                # List models
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"meta-llama/Llama-3.1-8B-Instruct","messages":[{"role":"user","content":"Hi"}],"max_tokens":10}'

# Cleanup
docker system prune -a -f       # Free up disk space (removes unused images/containers)
```

### File Locations
- **Model cache:** `/home/ubuntu/models/`
- **Docker logs:** `docker logs vllm-server`
- **Container config:** View with `docker inspect vllm-server`
- **SSH key:** `~/.ssh/aws-keys/vllm-ec2-key.pem` (local)

### Environment Variables (.env on Mac)
```bash
VLLM_API_URL=http://<EC2-PUBLIC-IP>:8000/v1
MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
QDRANT_URL=http://localhost:6333
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

---

## Additional Resources

- **Complete Deployment Guide:** [docs/DEPLOYMENT_COMPLETE.md](../../docs/DEPLOYMENT_COMPLETE.md)
- **vLLM Documentation:** https://docs.vllm.ai/
- **AWS EC2 Pricing:** https://aws.amazon.com/ec2/pricing/on-demand/
- **Llama Model Card:** https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct
