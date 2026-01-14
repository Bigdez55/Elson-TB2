#!/bin/bash
#
# Elson Financial AI - Model Creation Script
#
# This script creates the proprietary Elson-Finance-Trading-14B model
# by merging DeepSeek-R1, Qwen2.5-Math, FinGPT, and FinLLaMA.
#
# Prerequisites:
#   - GCP account with billing enabled
#   - HuggingFace account with token
#   - gcloud CLI installed and authenticated
#
# Usage:
#   ./scripts/create_elson_model.sh
#
# Cost: ~$15-20 (Spot VM for ~3 hours)
# Time: ~3-4 hours total
#
# Copyright (c) 2024 Elson Wealth. All rights reserved.
#

set -e  # Exit on error

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project)}"
ZONE="us-central1-a"
VM_NAME="elson-model-merger"
BUCKET_NAME="elson-model-weights-${PROJECT_ID}"
HF_TOKEN="${HF_TOKEN:-}"  # Set this or will prompt

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║           ELSON FINANCIAL AI - MODEL CREATION SCRIPT              ║"
echo "║                                                                   ║"
echo "║  This will create YOUR proprietary Elson-Finance-Trading-14B     ║"
echo "║  model by merging leading open-source financial AI models.       ║"
echo "║                                                                   ║"
echo "║  Estimated cost: \$15-20                                          ║"
echo "║  Estimated time: 3-4 hours                                        ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not installed${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No GCP project set${NC}"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${GREEN}✓ GCP Project: $PROJECT_ID${NC}"

# Prompt for HuggingFace token if not set
if [ -z "$HF_TOKEN" ]; then
    echo ""
    echo -e "${YELLOW}HuggingFace token required for model downloads.${NC}"
    echo "Get your token from: https://huggingface.co/settings/tokens"
    read -sp "Enter HuggingFace token: " HF_TOKEN
    echo ""
fi

# Step 1: Create GCS bucket for model storage
echo ""
echo -e "${YELLOW}Step 1/6: Creating GCS bucket...${NC}"

if gsutil ls -b gs://${BUCKET_NAME} &> /dev/null; then
    echo -e "${GREEN}✓ Bucket already exists: gs://${BUCKET_NAME}${NC}"
else
    gsutil mb -l us-central1 gs://${BUCKET_NAME}
    echo -e "${GREEN}✓ Created bucket: gs://${BUCKET_NAME}${NC}"
fi

# Step 2: Create GPU VM (Spot instance for cost savings)
echo ""
echo -e "${YELLOW}Step 2/6: Creating GPU VM (this may take a few minutes)...${NC}"

# Check if VM already exists
if gcloud compute instances describe $VM_NAME --zone=$ZONE &> /dev/null; then
    echo -e "${GREEN}✓ VM already exists, starting if stopped...${NC}"
    gcloud compute instances start $VM_NAME --zone=$ZONE || true
else
    echo "Creating A100 Spot VM..."
    gcloud compute instances create $VM_NAME \
        --zone=$ZONE \
        --machine-type=a2-highgpu-1g \
        --accelerator=type=nvidia-tesla-a100,count=1 \
        --image-family=pytorch-latest-gpu \
        --image-project=deeplearning-platform-release \
        --boot-disk-size=500GB \
        --boot-disk-type=pd-ssd \
        --maintenance-policy=TERMINATE \
        --provisioning-model=SPOT \
        --instance-termination-action=STOP \
        --metadata="install-nvidia-driver=True" \
        --scopes=cloud-platform

    echo "Waiting for VM to be ready..."
    sleep 60
fi

echo -e "${GREEN}✓ VM ready: $VM_NAME${NC}"

# Step 3: Upload merge configs and run script to VM
echo ""
echo -e "${YELLOW}Step 3/6: Uploading configurations to VM...${NC}"

# Create the merge script to run on VM
cat > /tmp/run_merge.sh << 'MERGE_SCRIPT'
#!/bin/bash
set -e

echo "=== Elson Financial AI Model Merge ==="
echo "Started at: $(date)"

# Install dependencies
echo "Installing dependencies..."
pip install -q mergekit torch transformers safetensors accelerate bitsandbytes
pip install -q huggingface_hub sentencepiece protobuf

# Login to HuggingFace
echo "Logging into HuggingFace..."
huggingface-cli login --token $HF_TOKEN

# Create directories
mkdir -p /workspace/checkpoints
mkdir -p /workspace/configs
cd /workspace

# Download merge configs
echo "Creating merge configurations..."

# Stage 1: SLERP config
cat > configs/stage1_reasoning.yaml << 'EOF'
slices:
  - sources:
      - model: deepseek-ai/DeepSeek-R1-Distill-Qwen-14B
        layer_range: [0, 48]
      - model: Qwen/Qwen2.5-Math-14B-Instruct
        layer_range: [0, 48]
merge_method: slerp
base_model: deepseek-ai/DeepSeek-R1-Distill-Qwen-14B
parameters:
  t:
    - filter: self_attn
      value: [0, 0.3, 0.5, 0.7, 1]
    - filter: mlp
      value: 0.4
    - value: 0.5
dtype: bfloat16
EOF

# Stage 2: TIES config
cat > configs/stage2_financial.yaml << 'EOF'
models:
  - model: ./checkpoints/elson-reason-math-14b
    parameters:
      density: 1.0
      weight: 0.6
  - model: FinGPT/fingpt-mt_llama2-13b_lora
    parameters:
      density: 0.5
      weight: 0.25
  - model: FinGPT/FinLLaMA
    parameters:
      density: 0.5
      weight: 0.15
merge_method: ties
base_model: ./checkpoints/elson-reason-math-14b
parameters:
  normalize: true
dtype: bfloat16
EOF

# Stage 3: DARE config
cat > configs/stage3_dare.yaml << 'EOF'
models:
  - model: ./checkpoints/elson-finance-trading-14b
    parameters:
      weight: 1.0
merge_method: dare_ties
base_model: ./checkpoints/elson-finance-trading-14b
parameters:
  dare_pruning_rate: 0.2
  normalize: true
  rescale: true
dtype: bfloat16
EOF

echo ""
echo "=== STAGE 1: SLERP (Reasoning + Math) ==="
echo "Merging DeepSeek-R1 + Qwen2.5-Math..."
echo "This will take ~45 minutes..."
mergekit-yaml configs/stage1_reasoning.yaml ./checkpoints/elson-reason-math-14b --cuda --low-cpu-memory

echo ""
echo "=== STAGE 2: TIES (Financial Domain) ==="
echo "Adding FinGPT + FinLLaMA..."
echo "This will take ~60 minutes..."
mergekit-yaml configs/stage2_financial.yaml ./checkpoints/elson-finance-trading-14b --cuda --low-cpu-memory

echo ""
echo "=== STAGE 3: DARE (Refinement) ==="
echo "Pruning noise, sharpening focus..."
echo "This will take ~30 minutes..."
mergekit-yaml configs/stage3_dare.yaml ./checkpoints/elson-finance-trading-14b-final --cuda --low-cpu-memory

echo ""
echo "=== UPLOAD TO GCS ==="
echo "Uploading final model to Cloud Storage..."
gsutil -m cp -r ./checkpoints/elson-finance-trading-14b-final gs://$BUCKET_NAME/

echo ""
echo "=== COMPLETE ==="
echo "Finished at: $(date)"
echo ""
echo "Your proprietary model is ready at:"
echo "  gs://$BUCKET_NAME/elson-finance-trading-14b-final"
echo ""
echo "Next steps:"
echo "  1. Convert to GGUF for Ollama (local testing)"
echo "  2. Deploy to Cloud Run with vLLM (production)"
echo "  3. Fine-tune with LoRA on your proprietary data"
MERGE_SCRIPT

# Copy script to VM
gcloud compute scp /tmp/run_merge.sh $VM_NAME:/tmp/run_merge.sh --zone=$ZONE

echo -e "${GREEN}✓ Configuration uploaded${NC}"

# Step 4: Run the merge on VM
echo ""
echo -e "${YELLOW}Step 4/6: Running model merge on VM...${NC}"
echo -e "${YELLOW}This will take approximately 2-3 hours.${NC}"
echo ""

gcloud compute ssh $VM_NAME --zone=$ZONE --command="
    export HF_TOKEN='$HF_TOKEN'
    export BUCKET_NAME='$BUCKET_NAME'
    chmod +x /tmp/run_merge.sh
    /tmp/run_merge.sh
"

# Step 5: Verify upload
echo ""
echo -e "${YELLOW}Step 5/6: Verifying model upload...${NC}"

if gsutil ls gs://${BUCKET_NAME}/elson-finance-trading-14b-final/ &> /dev/null; then
    echo -e "${GREEN}✓ Model successfully uploaded to GCS${NC}"

    # Get model size
    SIZE=$(gsutil du -s gs://${BUCKET_NAME}/elson-finance-trading-14b-final/ | awk '{print $1}')
    SIZE_GB=$((SIZE / 1024 / 1024 / 1024))
    echo -e "${GREEN}✓ Model size: ~${SIZE_GB}GB${NC}"
else
    echo -e "${RED}Error: Model not found in GCS${NC}"
    exit 1
fi

# Step 6: Stop VM to save costs
echo ""
echo -e "${YELLOW}Step 6/6: Stopping VM to save costs...${NC}"

gcloud compute instances stop $VM_NAME --zone=$ZONE

echo -e "${GREEN}✓ VM stopped${NC}"

# Summary
echo ""
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                     MODEL CREATION COMPLETE                       ║"
echo "╠═══════════════════════════════════════════════════════════════════╣"
echo "║                                                                   ║"
echo "║  Your proprietary Elson-Finance-Trading-14B is ready!            ║"
echo "║                                                                   ║"
echo "║  Location: gs://${BUCKET_NAME}/elson-finance-trading-14b-final   ║"
echo "║                                                                   ║"
echo "║  This model is 100% owned by Elson Wealth.                       ║"
echo "║                                                                   ║"
echo "║  Next Steps:                                                      ║"
echo "║    1. Test locally: Convert to GGUF, run with Ollama             ║"
echo "║    2. Deploy: Cloud Run with GPU + vLLM                          ║"
echo "║    3. Fine-tune: Train LoRA adapter on your backtest data        ║"
echo "║                                                                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo "To delete the VM (when you're done with all merging):"
echo "  gcloud compute instances delete $VM_NAME --zone=$ZONE"
echo ""
echo "To convert model for local testing with Ollama:"
echo "  See: docs/ELSON_MODEL_MERGING_STRATEGY.md"
