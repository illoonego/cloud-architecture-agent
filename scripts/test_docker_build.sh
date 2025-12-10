#!/bin/bash
# Quick Docker Build Test Script
# Tests both Dockerfiles to ensure they build successfully

set -e  # Exit on error

echo "=========================================="
echo "Docker Build Test Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Project root: $PROJECT_ROOT"
echo ""

# ============================================
# Test 1: Build API Docker Image
# ============================================
echo -e "${YELLOW}[1/2] Building API Docker image...${NC}"
echo "File: infra/docker/Dockerfile.api"
echo ""

if docker build -f infra/docker/Dockerfile.api -t cloud-agent-api:test . ; then
    echo -e "${GREEN}✅ API Docker image built successfully${NC}"
    
    # Get image size
    IMAGE_SIZE=$(docker images cloud-agent-api:test --format "{{.Size}}")
    echo "Image size: $IMAGE_SIZE"
else
    echo -e "${RED}❌ API Docker build failed${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo ""

# ============================================
# Test 2: Build vLLM Docker Image (if GPU available)
# ============================================
echo -e "${YELLOW}[2/2] Building vLLM Docker image...${NC}"
echo "File: infra/docker/Dockerfile.vllm"
echo ""

# Check if NVIDIA Docker is available
if command -v nvidia-docker &> /dev/null || docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi &> /dev/null 2>&1; then
    echo "GPU support detected"
    
    if docker build -f infra/docker/Dockerfile.vllm -t cloud-agent-vllm:test infra/docker/ ; then
        echo -e "${GREEN}✅ vLLM Docker image built successfully${NC}"
        
        # Get image size
        IMAGE_SIZE=$(docker images cloud-agent-vllm:test --format "{{.Size}}")
        echo "Image size: $IMAGE_SIZE"
    else
        echo -e "${RED}❌ vLLM Docker build failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  GPU not available, skipping vLLM build${NC}"
    echo "To build vLLM image, you need:"
    echo "  - NVIDIA GPU"
    echo "  - nvidia-docker or Docker with --gpus support"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Docker Build Tests Complete!${NC}"
echo "=========================================="
echo ""

# Display built images
echo "Built images:"
docker images | grep cloud-agent

echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Test API container:"
echo "   docker run -p 8000:8000 -e QDRANT_URL=:memory: cloud-agent-api:test"
echo ""
echo "2. Test vLLM container (if built):"
echo "   docker run --gpus all -p 8001:8000 cloud-agent-vllm:test"
echo ""
echo "3. Test API health endpoint:"
echo "   curl http://localhost:8000/health"
