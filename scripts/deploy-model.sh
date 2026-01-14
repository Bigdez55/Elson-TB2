#!/bin/bash
# Elson Financial AI - Model Deployment Script
# Usage: ./deploy-model.sh [l4|2xt4|quantized]

set -e

PROJECT_ID="elson-33a95"
MODEL_BUCKET="gs://elson-33a95-elson-models/elson-finance-trading-14b-final/final"
VM_NAME="elson-vllm-server"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Elson Financial AI Model Deployment ===${NC}"

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 > /dev/null 2>&1; then
    echo -e "${RED}Error: Not authenticated. Run 'gcloud auth login' first.${NC}"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# Get deployment mode
MODE=${1:-"l4"}

case $MODE in
    "l4")
        echo -e "${YELLOW}Deploying with L4 GPU (24GB VRAM)${NC}"
        ZONE="us-central1-a"
        MACHINE_TYPE="g2-standard-8"
        ACCELERATOR="type=nvidia-l4,count=1"
        IMAGE_FAMILY="pytorch-latest-gpu"
        VLLM_ARGS="--dtype half --max-model-len 4096"
        ;;
    "2xt4")
        echo -e "${YELLOW}Deploying with 2x T4 GPUs (32GB total VRAM)${NC}"
        ZONE="europe-west4-a"
        MACHINE_TYPE="n1-standard-16"
        ACCELERATOR="type=nvidia-tesla-t4,count=2"
        IMAGE_FAMILY="pytorch-2-7-cu128-ubuntu-2204-nvidia-570"
        VLLM_ARGS="--tensor-parallel-size 2 --dtype half --max-model-len 4096"
        ;;
    "quantized")
        echo -e "${YELLOW}Deploying with 1x T4 GPU + 4-bit quantization${NC}"
        ZONE="europe-west4-a"
        MACHINE_TYPE="n1-standard-8"
        ACCELERATOR="type=nvidia-tesla-t4,count=1"
        IMAGE_FAMILY="pytorch-2-7-cu128-ubuntu-2204-nvidia-570"
        VLLM_ARGS="--quantization awq --dtype half --max-model-len 2048"
        ;;
    *)
        echo -e "${RED}Unknown mode: $MODE${NC}"
        echo "Usage: $0 [l4|2xt4|quantized]"
        exit 1
        ;;
esac

# Check if VM already exists
if gcloud compute instances describe $VM_NAME --zone=$ZONE > /dev/null 2>&1; then
    echo -e "${YELLOW}VM $VM_NAME already exists. Delete it first.${NC}"
    read -p "Delete existing VM? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gcloud compute instances delete $VM_NAME --zone=$ZONE --quiet
    else
        exit 1
    fi
fi

# Create startup script
STARTUP_SCRIPT=$(cat <<'SCRIPT'
#!/bin/bash
set -e
exec > /var/log/vllm-deploy.log 2>&1
echo "=== VLLM DEPLOYMENT ===" && date

# Upgrade pip
python3 -m pip install --upgrade pip

# Install vLLM
pip install vllm

# Download model from GCS
echo "=== Downloading model ===" && date
mkdir -p /workspace/elson-model
gsutil -m cp -r MODEL_BUCKET/* /workspace/elson-model/
echo "Download complete" && date

# Start vLLM server
echo "=== Starting vLLM server ===" && date
python3 -m vllm.entrypoints.openai.api_server \
  --model /workspace/elson-model \
  --host 0.0.0.0 \
  --port 8000 \
  VLLM_ARGS \
  --trust-remote-code
SCRIPT
)

# Replace placeholders
STARTUP_SCRIPT=${STARTUP_SCRIPT//MODEL_BUCKET/$MODEL_BUCKET}
STARTUP_SCRIPT=${STARTUP_SCRIPT//VLLM_ARGS/$VLLM_ARGS}

# Create VM
echo -e "${GREEN}Creating VM: $VM_NAME in $ZONE${NC}"
gcloud compute instances create $VM_NAME \
  --zone=$ZONE \
  --machine-type=$MACHINE_TYPE \
  --accelerator=$ACCELERATOR \
  --image-family=$IMAGE_FAMILY \
  --image-project=deeplearning-platform-release \
  --boot-disk-size=100GB \
  --boot-disk-type=pd-ssd \
  --maintenance-policy=TERMINATE \
  --scopes=cloud-platform \
  --tags=http-server \
  --metadata=startup-script="$STARTUP_SCRIPT"

# Get external IP
sleep 5
EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

echo ""
echo -e "${GREEN}=== Deployment Started ===${NC}"
echo -e "VM Name: ${YELLOW}$VM_NAME${NC}"
echo -e "Zone: ${YELLOW}$ZONE${NC}"
echo -e "External IP: ${YELLOW}$EXTERNAL_IP${NC}"
echo ""
echo -e "Monitor deployment:"
echo -e "  gcloud compute ssh $VM_NAME --zone=$ZONE --command=\"tail -f /var/log/vllm-deploy.log\""
echo ""
echo -e "Test API (once ready):"
echo -e "  curl http://$EXTERNAL_IP:8000/v1/models"
echo ""
echo -e "Stop VM to save costs:"
echo -e "  gcloud compute instances stop $VM_NAME --zone=$ZONE"
