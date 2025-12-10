#!/bin/bash

# =============================================================================
# vLLM Deployment Script for AWS EC2
# =============================================================================
# This script automates the deployment of vLLM on your EC2 instance
#
# Usage (from Mac terminal):
#   ./scripts/deploy_vllm.sh [build|start|stop|restart|logs|test|status]
#
# =============================================================================

set -e  # Exit on error

# Configuration
# ⚠️ IMPORTANT: Update these values for your environment
EC2_IP="${EC2_IP:-YOUR_EC2_PUBLIC_IP}"
EC2_USER="ubuntu"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/aws-keys/vllm-ec2-key.pem}"
CONTAINER_NAME="vllm-server"
IMAGE_NAME="vllm-server"
HF_TOKEN="${HUGGING_FACE_HUB_TOKEN:-YOUR_HF_TOKEN_HERE}"
MODEL="meta-llama/Llama-3.1-8B-Instruct"
DOCKERFILE="infra/docker/Dockerfile.vllm"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

ssh_exec() {
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_IP" "$1"
}

# Command functions
build() {
    log_info "Building vLLM Docker image on EC2..."
    
    # Copy Dockerfile to EC2
    log_info "Copying Dockerfile to EC2..."
    scp -i "$SSH_KEY" "$DOCKERFILE" "$EC2_USER@$EC2_IP:~/Dockerfile.vllm"
    
    # Build image on EC2
    log_info "Building Docker image (this may take 5-10 minutes)..."
    ssh_exec "docker build -f ~/Dockerfile.vllm -t $IMAGE_NAME ."
    
    log_info "✅ Build complete!"
}

start() {
    log_info "Starting vLLM container on EC2..."
    
    # Check if container already exists
    if ssh_exec "docker ps -a | grep -q $CONTAINER_NAME"; then
        log_warn "Container $CONTAINER_NAME already exists. Stopping and removing..."
        ssh_exec "docker stop $CONTAINER_NAME || true"
        ssh_exec "docker rm $CONTAINER_NAME || true"
    fi
    
    # Start container
    log_info "Starting container with Llama-3.1-8B-Instruct..."
    ssh_exec "docker run -d \
        --name $CONTAINER_NAME \
        --gpus all \
        -p 8000:8000 \
        -e HUGGING_FACE_HUB_TOKEN='$HF_TOKEN' \
        -e MODEL='$MODEL' \
        -v /home/ubuntu/models:/models \
        --restart unless-stopped \
        $IMAGE_NAME"
    
    log_info "✅ Container started!"
    log_info "Model loading in progress (this takes 2-3 minutes on first run)..."
    log_info "Monitor logs with: $0 logs"
}

stop() {
    log_info "Stopping vLLM container..."
    ssh_exec "docker stop $CONTAINER_NAME || true"
    log_info "✅ Container stopped!"
}

restart() {
    log_info "Restarting vLLM container..."
    stop
    sleep 2
    start
}

logs() {
    log_info "Showing container logs (Ctrl+C to exit)..."
    ssh -i "$SSH_KEY" "$EC2_USER@$EC2_IP" "docker logs -f $CONTAINER_NAME"
}

status() {
    log_info "Checking vLLM container status..."
    
    # Container status
    echo ""
    echo "=== Container Status ==="
    ssh_exec "docker ps -a | grep $CONTAINER_NAME || echo 'Container not found'"
    
    # GPU status
    echo ""
    echo "=== GPU Status ==="
    ssh_exec "nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv"
    
    # API health
    echo ""
    echo "=== API Health Check ==="
    HEALTH=$(curl -s http://$EC2_IP:8000/health 2>/dev/null || echo "API not accessible")
    echo "$HEALTH"
    
    # Model info
    echo ""
    echo "=== Available Models ==="
    MODELS=$(curl -s http://$EC2_IP:8000/v1/models 2>/dev/null || echo "API not accessible")
    echo "$MODELS"
}

test() {
    log_info "Testing vLLM inference API..."
    
    # Test 1: Health check
    echo ""
    echo "=== Test 1: Health Check ==="
    curl -s http://$EC2_IP:8000/health | jq '.' || log_error "Health check failed"
    
    # Test 2: List models
    echo ""
    echo "=== Test 2: List Models ==="
    curl -s http://$EC2_IP:8000/v1/models | jq '.data[0].id' || log_error "Model list failed"
    
    # Test 3: Chat completion
    echo ""
    echo "=== Test 3: Chat Completion ==="
    curl -s http://$EC2_IP:8000/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"$MODEL\",
            \"messages\": [
                {\"role\": \"system\", \"content\": \"You are a helpful AWS Cloud Architect assistant.\"},
                {\"role\": \"user\", \"content\": \"What is Amazon EC2 in one sentence?\"}
            ],
            \"max_tokens\": 50,
            \"temperature\": 0.7
        }" | jq '.choices[0].message.content' || log_error "Chat completion failed"
    
    echo ""
    log_info "✅ All tests completed!"
}

deploy() {
    log_info "Starting full deployment pipeline..."
    build
    start
    
    log_info "Waiting 30 seconds for model to load..."
    sleep 30
    
    status
    
    log_info "Deployment complete!"
    log_info "API is available at: http://$EC2_IP:8000"
    log_info "Run '$0 test' to verify inference"
}

usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  deploy     - Full deployment (build + start)"
    echo "  build      - Build Docker image on EC2"
    echo "  start      - Start vLLM container"
    echo "  stop       - Stop vLLM container"
    echo "  restart    - Restart vLLM container"
    echo "  logs       - Show container logs (follow mode)"
    echo "  status     - Show container, GPU, and API status"
    echo "  test       - Run API tests"
    echo ""
    echo "Examples:"
    echo "  $0 deploy       # Full deployment"
    echo "  $0 logs         # Monitor logs"
    echo "  $0 test         # Test API endpoints"
}

# Main
case "${1:-}" in
    deploy)
        deploy
        ;;
    build)
        build
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    test)
        test
        ;;
    *)
        usage
        exit 1
        ;;
esac
