#!/bin/bash
# Elson TB2 - vLLM Deployment with DoRA Adapter Support
#
# Deploys the Elson Financial AI model with DoRA/QDoRA adapters
# NOTE: LoRA adapters are deprecated. Use DoRA or QDoRA only.
#
# Usage:
#   ./scripts/deploy-vllm-dora.sh [mode] [adapter]
#
# Modes:
#   l4          - L4 GPU (24GB) - Recommended for production
#   2xt4        - 2x T4 GPUs with tensor parallelism
#   quantized   - T4 GPU with AWQ 4-bit quantization
#   spot        - L4 GPU on Spot VM (65% cheaper)
#
# Adapters:
#   dora        - DoRA adapter (H100 trained, loss: 0.14) - PRODUCTION
#   qdora       - QDoRA quantized model - PRODUCTION (cost-efficient)
#   none        - Base model only

set -e

PROJECT_ID="elson-33a95"
BASE_MODEL_BUCKET="gs://elson-33a95-elson-models/elson-finance-trading-14b-final/final"
DORA_ADAPTER="gs://elson-33a95-elson-models/wealth-dora-elson14b-h100"
QDORA_MODEL="gs://elson-33a95-elson-models/elson-finance-trading-wealth-14b-q4"
VM_NAME="elson-vllm-server"

# NOTE: LoRA adapters deprecated - not included

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  Elson TB2 - vLLM Deployment with DoRA${NC}"
    echo -e "${GREEN}============================================${NC}"
}

print_usage() {
    echo "Usage: $0 [mode] [adapter]"
    echo ""
    echo "Modes:"
    echo "  l4          L4 GPU (24GB) - Recommended"
    echo "  2xt4        2x T4 GPUs with tensor parallelism"
    echo "  quantized   T4 GPU with AWQ 4-bit quantization"
    echo "  spot        L4 GPU on Spot VM (65% cheaper)"
    echo ""
    echo "Adapters (DoRA/QDoRA only - LoRA deprecated):"
    echo "  dora        DoRA adapter (H100 trained, best quality) - PRODUCTION"
    echo "  qdora       QDoRA quantized model - PRODUCTION (cost-efficient)"
    echo "  none        Base model only"
    echo ""
    echo "Examples:"
    echo "  $0 l4 dora           # L4 with DoRA adapter (recommended)"
    echo "  $0 spot qdora        # Spot L4 with QDoRA (cost-effective)"
    echo "  $0 2xt4 none         # 2x T4 with base model"
}

check_quota() {
    echo -e "\n${BLUE}Checking GPU quota...${NC}"

    local gpu_type=$1
    local quota_name=""
    local region=""

    case $gpu_type in
        "l4")
            quota_name="NVIDIA_L4_GPUS"
            region="us-central1"
            ;;
        "t4")
            quota_name="NVIDIA_T4_GPUS"
            region="europe-west4"
            ;;
    esac

    # Check quota (may not have permissions)
    local quota=$(gcloud compute regions describe $region \
        --format="value(quotas[name='$quota_name'].limit)" 2>/dev/null || echo "unknown")

    if [[ "$quota" == "0" || "$quota" == "unknown" ]]; then
        echo -e "${YELLOW}Warning: GPU quota may be insufficient.${NC}"
        echo -e "Request quota at: https://console.cloud.google.com/iam-admin/quotas?project=$PROJECT_ID"
        echo ""
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo -e "${GREEN}GPU quota available: $quota${NC}"
    fi
}

# Parse arguments
MODE=${1:-"l4"}
ADAPTER=${2:-"dora"}

print_header

# Validate arguments
case $MODE in
    "l4"|"2xt4"|"quantized"|"spot")
        ;;
    "--help"|"-h")
        print_usage
        exit 0
        ;;
    *)
        echo -e "${RED}Error: Unknown mode '$MODE'${NC}"
        print_usage
        exit 1
        ;;
esac

case $ADAPTER in
    "dora"|"qdora"|"none")
        ;;
    "lora-v1"|"lora-v2")
        echo -e "${RED}Error: LoRA adapters are DEPRECATED. Use 'dora' or 'qdora' instead.${NC}"
        print_usage
        exit 1
        ;;
    *)
        echo -e "${RED}Error: Unknown adapter '$ADAPTER'${NC}"
        print_usage
        exit 1
        ;;
esac

echo -e "\n${BLUE}Configuration:${NC}"
echo "  Mode:    $MODE"
echo "  Adapter: $ADAPTER"

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 > /dev/null 2>&1; then
    echo -e "${RED}Error: Not authenticated. Run 'gcloud auth login' first.${NC}"
    exit 1
fi

gcloud config set project $PROJECT_ID

# Set deployment parameters based on mode
case $MODE in
    "l4")
        ZONE="us-central1-a"
        MACHINE_TYPE="g2-standard-8"
        ACCELERATOR="type=nvidia-l4,count=1"
        IMAGE_FAMILY="pytorch-latest-gpu"
        VLLM_ARGS="--dtype half --max-model-len 4096"
        PREEMPTIBLE=""
        check_quota "l4"
        ;;
    "spot")
        ZONE="us-central1-a"
        MACHINE_TYPE="g2-standard-8"
        ACCELERATOR="type=nvidia-l4,count=1"
        IMAGE_FAMILY="pytorch-latest-gpu"
        VLLM_ARGS="--dtype half --max-model-len 4096"
        PREEMPTIBLE="--provisioning-model=SPOT --instance-termination-action=STOP"
        check_quota "l4"
        ;;
    "2xt4")
        ZONE="europe-west4-a"
        MACHINE_TYPE="n1-standard-16"
        ACCELERATOR="type=nvidia-tesla-t4,count=2"
        IMAGE_FAMILY="pytorch-2-7-cu128-ubuntu-2204-nvidia-570"
        VLLM_ARGS="--tensor-parallel-size 2 --dtype half --max-model-len 4096"
        PREEMPTIBLE=""
        check_quota "t4"
        ;;
    "quantized")
        ZONE="europe-west4-a"
        MACHINE_TYPE="n1-standard-8"
        ACCELERATOR="type=nvidia-tesla-t4,count=1"
        IMAGE_FAMILY="pytorch-2-7-cu128-ubuntu-2204-nvidia-570"
        VLLM_ARGS="--quantization awq --dtype half --max-model-len 2048"
        PREEMPTIBLE=""
        check_quota "t4"
        ;;
esac

# Set adapter configuration
ADAPTER_BUCKET=""
ADAPTER_FLAG=""
MODEL_PATH="/workspace/elson-model"

case $ADAPTER in
    "dora")
        ADAPTER_BUCKET=$DORA_ADAPTER
        ADAPTER_FLAG="--enable-lora --lora-modules elson-dora=/workspace/adapter"
        ;;
    "qdora")
        # QDoRA is a merged quantized model, not an adapter
        BASE_MODEL_BUCKET=$QDORA_MODEL
        ADAPTER_FLAG=""
        ;;
    "none")
        ADAPTER_FLAG=""
        ;;
    # LoRA adapters deprecated - handled in validation above
esac

echo -e "\n${YELLOW}Deployment Configuration:${NC}"
echo "  Zone:          $ZONE"
echo "  Machine:       $MACHINE_TYPE"
echo "  GPU:           $ACCELERATOR"
echo "  vLLM Args:     $VLLM_ARGS $ADAPTER_FLAG"
if [[ -n "$PREEMPTIBLE" ]]; then
    echo -e "  ${GREEN}Spot VM:        Yes (65% cheaper)${NC}"
fi

# Check if VM exists
if gcloud compute instances describe $VM_NAME --zone=$ZONE > /dev/null 2>&1; then
    echo -e "\n${YELLOW}VM $VM_NAME already exists in $ZONE.${NC}"
    read -p "Delete and recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Deleting existing VM..."
        gcloud compute instances delete $VM_NAME --zone=$ZONE --quiet
    else
        echo "Aborting."
        exit 1
    fi
fi

# Create startup script
echo -e "\n${BLUE}Creating startup script...${NC}"

STARTUP_SCRIPT=$(cat <<SCRIPT
#!/bin/bash
set -e
exec > /var/log/vllm-deploy.log 2>&1
echo "=== ELSON VLLM DEPLOYMENT ===" && date

# System info
nvidia-smi
python3 --version

# Upgrade pip
python3 -m pip install --upgrade pip

# Install vLLM with LoRA support
echo "=== Installing vLLM ===" && date
pip install vllm peft bitsandbytes accelerate

# Download base model
echo "=== Downloading base model ===" && date
mkdir -p $MODEL_PATH
gsutil -m cp -r $BASE_MODEL_BUCKET/* $MODEL_PATH/
echo "Base model download complete" && date
SCRIPT
)

# Add adapter download if needed
if [[ -n "$ADAPTER_BUCKET" ]]; then
    STARTUP_SCRIPT+="
# Download adapter
echo \"=== Downloading adapter ==\" && date
mkdir -p /workspace/adapter
gsutil -m cp -r $ADAPTER_BUCKET/* /workspace/adapter/
echo \"Adapter download complete\" && date
"
fi

# Add vLLM server start
STARTUP_SCRIPT+="
# Start vLLM server
echo \"=== Starting vLLM server ==\" && date
python3 -m vllm.entrypoints.openai.api_server \\
  --model $MODEL_PATH \\
  --host 0.0.0.0 \\
  --port 8000 \\
  $VLLM_ARGS \\
  $ADAPTER_FLAG \\
  --trust-remote-code
"

# Create the VM
echo -e "\n${GREEN}Creating VM: $VM_NAME in $ZONE${NC}"

gcloud compute instances create $VM_NAME \
  --zone=$ZONE \
  --machine-type=$MACHINE_TYPE \
  --accelerator=$ACCELERATOR \
  --image-family=$IMAGE_FAMILY \
  --image-project=deeplearning-platform-release \
  --boot-disk-size=200GB \
  --boot-disk-type=pd-ssd \
  --maintenance-policy=TERMINATE \
  --scopes=cloud-platform \
  --tags=http-server,https-server \
  $PREEMPTIBLE \
  --metadata=startup-script="$STARTUP_SCRIPT"

# Wait for external IP
sleep 10
EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE \
    --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

# Create firewall rule if needed
if ! gcloud compute firewall-rules describe allow-vllm --quiet 2>/dev/null; then
    echo -e "\n${BLUE}Creating firewall rule for port 8000...${NC}"
    gcloud compute firewall-rules create allow-vllm \
        --direction=INGRESS \
        --priority=1000 \
        --network=default \
        --action=ALLOW \
        --rules=tcp:8000 \
        --source-ranges=0.0.0.0/0 \
        --target-tags=http-server
fi

# Print summary
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Deployment Started Successfully!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "VM Name:       ${YELLOW}$VM_NAME${NC}"
echo -e "Zone:          ${YELLOW}$ZONE${NC}"
echo -e "External IP:   ${YELLOW}$EXTERNAL_IP${NC}"
echo -e "Adapter:       ${YELLOW}$ADAPTER${NC}"
echo ""
echo -e "${BLUE}Monitor deployment:${NC}"
echo "  gcloud compute ssh $VM_NAME --zone=$ZONE --command=\"tail -f /var/log/vllm-deploy.log\""
echo ""
echo -e "${BLUE}Test API (wait 10-15 min for model download):${NC}"
echo "  curl http://$EXTERNAL_IP:8000/v1/models"
echo ""
echo "  curl http://$EXTERNAL_IP:8000/v1/chat/completions \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{"
echo "      \"model\": \"elson-finance-trading-14b\","
echo "      \"messages\": [{\"role\": \"user\", \"content\": \"What is a 401k?\"}],"
echo "      \"max_tokens\": 256"
echo "    }'"
echo ""
echo -e "${BLUE}Stop VM to save costs:${NC}"
echo "  gcloud compute instances stop $VM_NAME --zone=$ZONE"
echo ""
echo -e "${BLUE}Delete VM when done:${NC}"
echo "  gcloud compute instances delete $VM_NAME --zone=$ZONE"
echo ""

# Cost estimate
case $MODE in
    "l4")
        echo -e "${YELLOW}Estimated Cost: ~\$0.70/hour (~\$504/month always-on)${NC}"
        ;;
    "spot")
        echo -e "${YELLOW}Estimated Cost: ~\$0.25/hour (~\$180/month always-on) - SPOT VM${NC}"
        ;;
    "2xt4")
        echo -e "${YELLOW}Estimated Cost: ~\$1.50/hour (~\$1,080/month always-on)${NC}"
        ;;
    "quantized")
        echo -e "${YELLOW}Estimated Cost: ~\$0.50/hour (~\$360/month always-on)${NC}"
        ;;
esac

echo ""
echo -e "${GREEN}Done!${NC}"
