# EC2 GPU Setup Guide - Step by Step

**✅ DEPLOYMENT COMPLETE** - This is a reference guide. For the actual production deployment details, see [DEPLOYMENT_COMPLETE.md](DEPLOYMENT_COMPLETE.md).

**Current Production Setup:**
- Instance Type: g4dn.xlarge (T4 GPU)
- AMI: Deep Learning OSS Nvidia Driver GPU AMI (Ubuntu 24.04)
- Deployment: Docker with vllm/vllm-openai:v0.6.2
- Model: meta-llama/Llama-3.1-8B-Instruct

---

## Part 1: Launch EC2 GPU Instance

### Step 1: Go to EC2 Dashboard
1. Log into AWS Console
2. Navigate to **EC2** service
3. Click **Launch Instance**

### Step 2: Configure Instance

**Name and Tags:**
- Name: `vllm-inference-server`

**Application and OS Images (AMI):**
- Click **Browse more AMIs**
- Search for: `Deep Learning OSS Nvidia Driver GPU AMI`
- Select: **Deep Learning OSS Nvidia Driver GPU AMI (Ubuntu 22.04)**
  - This comes pre-installed with NVIDIA drivers and CUDA toolkit

**Instance Type:**
- **Production:** `g4dn.xlarge` (1x NVIDIA T4, 4 vCPUs, 16 GB RAM) - ~$0.526/hour ✅ Currently deployed
- **Alternative:** `g5.xlarge` (1x NVIDIA A10G GPU, 4 vCPUs, 16 GB RAM) - ~$1.00/hour

**Key Pair (login):**
- If you don't have one:
  - Click **Create new key pair**
  - Name: `vllm-key`
  - Type: RSA
  - Format: `.pem` (for Mac/Linux) or `.ppk` (for Windows with PuTTY)
  - Click **Create key pair** (downloads automatically)
  - **IMPORTANT:** Save this file securely - you can't download it again!

**Network Settings:**
- Click **Edit**
- VPC: Default VPC (or select your VPC)
- Subnet: No preference
- Auto-assign public IP: **Enable**
- Firewall (Security Groups): **Create security group**
  - Security group name: `vllm-server-sg`
  - Description: `Security group for vLLM inference server`
  
  **Add Rules:**
  1. SSH (already added):
     - Type: SSH
     - Port: 22
     - Source: **My IP** (restricts SSH to your current IP)
  
  2. Add Rule - vLLM API:
     - Click **Add security group rule**
     - Type: Custom TCP
     - Port: 8000
     - Source: **My IP** (for testing) or **Custom** with your API server's IP/VPC CIDR
  
  3. (Optional) Add Rule - HTTPS:
     - Type: HTTPS
     - Port: 443
     - Source: My IP

**Configure Storage:**
- Size: **100 GB** (minimum recommended)
- Volume Type: `gp3` (faster and more cost-effective)
- Delete on Termination: ✓ (checked)

**Advanced Details (Optional but Recommended):**
- Scroll down to **User data** (optional - we'll do this manually)

### Step 3: Review and Launch
- Review your configuration
- Click **Launch Instance**
- Wait for instance state to show **Running** (takes 2-3 minutes)

---

## Part 2: Connect to Your EC2 Instance

### Step 1: Get Instance Details
1. In EC2 Dashboard, click on your instance ID
2. Copy the **Public IPv4 address** (e.g., `54.123.45.67`)

### Step 2: Set Key Permissions (Mac/Linux)
```bash
# Navigate to where you downloaded the key
cd ~/Downloads

# Set correct permissions (required by SSH)
chmod 400 vllm-key.pem

# Optional: Move to a safe location
mkdir -p ~/.ssh/aws-keys
mv vllm-key.pem ~/.ssh/aws-keys/
```

### Step 3: Connect via SSH
```bash
# Replace with your actual public IP
ssh -i ~/.ssh/aws-keys/vllm-key.pem ubuntu@54.123.45.67
```

First time connecting, you'll see:
```
The authenticity of host '54.123.45.67 (54.123.45.67)' can't be established.
Are you sure you want to continue connecting (yes/no/[fingerprint])? 
```
Type: **yes**

You should now see:
```
ubuntu@ip-172-31-x-x:~$
```

✅ **You're connected!**

---

## Part 3: Verify GPU and Environment

### Step 1: Check GPU
```bash
nvidia-smi
```

You should see output showing your NVIDIA A10G GPU:
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.xx.xx    Driver Version: 535.xx.xx    CUDA Version: 12.2     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
|   0  NVIDIA A10G           On | 00000000:00:1E.0 Off |                    0 |
+-------------------------------+----------------------+----------------------+
```

### Step 2: Check Python
```bash
python3 --version
# Should show Python 3.10 or 3.11
```

### Step 3: Check CUDA
```bash
nvcc --version
# Should show CUDA 12.x
```

---

## Part 4: Install Docker and NVIDIA Container Toolkit

### Step 1: Install Docker
```bash
# Update package index
sudo apt-get update

# Install prerequisites
sudo apt-get install -y ca-certificates curl gnupg

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to docker group (avoid using sudo)
sudo usermod -aG docker ubuntu

# Apply group changes
newgrp docker

# Verify Docker installation
docker --version
```

### Step 2: Install NVIDIA Container Toolkit
```bash
# Configure the repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Update and install
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker to use NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker

# Restart Docker
sudo systemctl restart docker

# Test GPU with Docker
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

If you see the GPU info, you're ready! ✅

---

## Part 5: Build and Run vLLM Docker Container

### Option A: Build Locally on EC2 (Recommended)

```bash
# Install git
sudo apt-get install -y git

# Clone your repository (or create Dockerfile manually)
git clone https://github.com/YOUR_USERNAME/cloud-architecture-agent.git
cd cloud-architecture-agent

# Build the vLLM image
docker build -f infra/docker/Dockerfile.vllm -t vllm-server infra/docker/

# Run the container
docker run -d \
  --name vllm-server \
  --gpus all \
  -p 8000:8000 \
  --restart unless-stopped \
  vllm-server
```

### Option B: Create Dockerfile Manually (if not using git)

```bash
# Create a directory
mkdir -p ~/vllm-docker
cd ~/vllm-docker

# Create the Dockerfile
cat > Dockerfile.vllm << 'EOF'
# Multi-stage build to reduce final image size
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3.10 \
        python3-pip \
        curl \
        ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3.10 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

RUN pip install --upgrade pip setuptools wheel

FROM base AS builder

RUN pip install --no-cache-dir \
    torch==2.1.0 \
    --index-url https://download.pytorch.org/whl/cu121

RUN pip install --no-cache-dir vllm==0.2.7

FROM base AS runtime

COPY --from=builder /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app
RUN mkdir -p /models

ENV VLLM_WORKER_MULTIPROC_METHOD=spawn \
    CUDA_VISIBLE_DEVICES=0

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

CMD ["python", "-m", "vllm.entrypoints.openai.api_server", \
     "--model", "meta-llama/Meta-Llama-3-8B-Instruct", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--dtype", "half", \
     "--max-model-len", "4096"]
EOF

# Build the image
docker build -f Dockerfile.vllm -t vllm-server .

# Run the container
docker run -d \
  --name vllm-server \
  --gpus all \
  -p 8000:8000 \
  --restart unless-stopped \
  vllm-server
```

---

## Part 6: Monitor and Test

### Check Container Status
```bash
# View running containers
docker ps

# View logs (model download will take 5-10 minutes first time)
docker logs -f vllm-server
```

You'll see:
```
INFO:     Downloading model meta-llama/Meta-Llama-3-8B-Instruct...
INFO:     Loading model weights...
INFO:     Model loaded successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Test the vLLM API

**From within EC2:**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test models endpoint
curl http://localhost:8000/v1/models

# Test completion (simple test)
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Meta-Llama-3-8B-Instruct",
    "prompt": "What is AWS Lambda?",
    "max_tokens": 100
  }'
```

**From your local machine:**
```bash
# Replace with your EC2 public IP
curl http://54.123.45.67:8000/health
```

---

## Part 7: Install AWS CLI and SSM Agent (For CI/CD)

### Install AWS CLI
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
sudo apt-get install -y unzip
unzip awscliv2.zip
sudo ./aws/install
aws --version
```

### Install SSM Agent (for remote deployment)
```bash
sudo snap install amazon-ssm-agent --classic
sudo systemctl enable snap.amazon-ssm-agent.amazon-ssm-agent.service
sudo systemctl start snap.amazon-ssm-agent.amazon-ssm-agent.service
```

### Configure IAM Role for EC2
1. Go to IAM Console → Roles → Create Role
2. Select: AWS Service → EC2
3. Add permissions: `AmazonSSMManagedInstanceCore`, `AmazonEC2ContainerRegistryReadOnly`
4. Name: `EC2-vLLM-Server-Role`
5. Go back to EC2 → Select your instance → Actions → Security → Modify IAM role
6. Attach: `EC2-vLLM-Server-Role`

---

## Part 8: Keep Instance Running and Manage Costs

### Option 1: Keep Running 24/7
- Costs: ~$720/month (g5.xlarge)
- Best for: Production use

### Option 2: Stop When Not Needed
```bash
# From your local machine
aws ec2 stop-instances --instance-ids i-YOUR-INSTANCE-ID

# Start again when needed
aws ec2 start-instances --instance-ids i-YOUR-INSTANCE-ID
```

**Note:** Public IP changes each time you stop/start. Use Elastic IP for fixed IP.

### Option 3: Schedule with Lambda
- Use AWS Lambda to start/stop on schedule
- Example: Run only during business hours

---

## Troubleshooting

**Container won't start:**
```bash
docker logs vllm-server  # Check for errors
docker ps -a              # See all containers
```

**Out of memory:**
- Use smaller model or reduce `--max-model-len`

**Can't access from outside:**
- Check Security Group allows port 8000
- Verify public IP is correct

**GPU not detected:**
```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

---

## Next Steps

1. ✅ vLLM server is running on EC2
2. Update your API's `.env` with EC2's public IP:
   ```
   VLLM_API_URL=http://54.123.45.67:8000/v1
   ```
3. Test your FastAPI with real vLLM backend
4. Set up CI/CD pipeline to auto-deploy updates

---

## Quick Reference Commands

```bash
# SSH to EC2
ssh -i ~/.ssh/aws-keys/vllm-key.pem ubuntu@YOUR_EC2_IP

# Check vLLM logs
docker logs -f vllm-server

# Restart vLLM
docker restart vllm-server

# Stop vLLM
docker stop vllm-server

# Update vLLM (pull new image and restart)
docker pull YOUR_ECR_REPO/vllm:latest
docker stop vllm-server
docker rm vllm-server
docker run -d --name vllm-server --gpus all -p 8000:8000 --restart unless-stopped YOUR_ECR_REPO/vllm:latest
```
