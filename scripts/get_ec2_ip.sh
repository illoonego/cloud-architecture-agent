#!/bin/bash
#
# scripts/get_ec2_ip.sh
#
# Helper script to get the current public IP of your vLLM EC2 instance
# Usage: ./scripts/get_ec2_ip.sh [instance-id]
#

set -e

# Default instance ID (update this or pass as argument)
INSTANCE_ID="${1:-i-YOUR-INSTANCE-ID}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI not found. Please install it first."
    echo "Install: pip install awscli or brew install awscli"
    exit 1
fi

# Get the current public IP
echo "Fetching public IP for instance: $INSTANCE_ID..."
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text 2>/dev/null)

if [ "$PUBLIC_IP" == "None" ] || [ -z "$PUBLIC_IP" ]; then
    echo "Error: Could not get IP address. Is the instance running?"
    echo ""
    echo "Checking instance state..."
    STATE=$(aws ec2 describe-instances \
        --instance-ids "$INSTANCE_ID" \
        --query 'Reservations[0].Instances[0].State.Name' \
        --output text 2>/dev/null || echo "unknown")
    echo "Instance state: $STATE"
    
    if [ "$STATE" == "stopped" ]; then
        echo ""
        echo "Start the instance with:"
        echo "  aws ec2 start-instances --instance-ids $INSTANCE_ID"
    fi
    exit 1
fi

echo ""
echo "✓ Instance is running"
echo "Public IP: $PUBLIC_IP"
echo ""
echo "Update your .env file with:"
echo "  VLLM_API_URL=http://$PUBLIC_IP:8000/v1"
echo ""
echo "Or run:"
echo "  echo \"VLLM_API_URL=http://$PUBLIC_IP:8000/v1\" >> .env"
