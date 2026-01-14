#!/bin/bash
# Elson Financial AI - VM Startup Script for Model Merge
# This script runs automatically when the VM boots
#
# Copyright (c) 2024 Elson Wealth. All rights reserved.

set -e

# Configuration - these will be passed via metadata
HF_TOKEN="${HF_TOKEN:-}"
BUCKET_NAME="${BUCKET_NAME:-elson-33a95-elson-models}"
PROJECT_ID="${PROJECT_ID:-elson-33a95}"

# Log file
LOG_FILE="/var/log/elson-model-merge.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║           ELSON FINANCIAL AI - MODEL MERGE STARTUP                ║"
echo "║                                                                   ║"
echo "║  Creating proprietary Elson-Finance-Trading-14B                  ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Started at: $(date)"
echo "Project: $PROJECT_ID"
echo "Bucket: $BUCKET_NAME"
echo ""

# Get HF_TOKEN from instance metadata if not set
if [ -z "$HF_TOKEN" ]; then
    echo "Fetching HF_TOKEN from instance metadata..."
    HF_TOKEN=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/hf-token" -H "Metadata-Flavor: Google" 2>/dev/null || echo "")
fi

if [ -z "$HF_TOKEN" ]; then
    echo "ERROR: HF_TOKEN not found. Set it via metadata or environment variable."
    exit 1
fi

echo "HF_TOKEN found (${#HF_TOKEN} chars)"

# Wait for GPU to be ready
echo ""
echo "=== Checking GPU ==="
nvidia-smi || { echo "GPU not ready, waiting..."; sleep 30; nvidia-smi; }

# Install dependencies
echo ""
echo "=== Installing dependencies ==="
pip install --quiet mergekit transformers safetensors accelerate huggingface_hub sentencepiece protobuf

# Login to HuggingFace
echo ""
echo "=== Authenticating with HuggingFace ==="
python3 -c "from huggingface_hub import login; login(token='$HF_TOKEN')"

# Create workspace
echo ""
echo "=== Setting up workspace ==="
mkdir -p /workspace/checkpoints /workspace/configs
cd /workspace

# ============================================
# STAGE 1: SLERP - Reasoning + Math Foundation
# ============================================
echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║  STAGE 1: SLERP MERGE                                             ║"
echo "║  Combining: DeepSeek-R1-Distill-Qwen-14B + Qwen2.5-Math-14B      ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"

cat > configs/stage1.yaml << 'EOF'
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

echo "Starting Stage 1 merge at: $(date)"
mergekit-yaml configs/stage1.yaml ./checkpoints/elson-reason-math-14b --cuda --low-cpu-memory
echo "Stage 1 complete at: $(date)"
echo "Output: ./checkpoints/elson-reason-math-14b"

# ============================================
# STAGE 2: DARE-TIES - Prune and Refine
# ============================================
echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║  STAGE 2: DARE-TIES REFINEMENT                                    ║"
echo "║  Pruning redundant weights, normalizing, rescaling               ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"

cat > configs/stage2.yaml << 'EOF'
models:
  - model: ./checkpoints/elson-reason-math-14b
    parameters:
      density: 1.0
      weight: 1.0
merge_method: dare_ties
base_model: ./checkpoints/elson-reason-math-14b
parameters:
  dare_pruning_rate: 0.15
  normalize: true
  rescale: true
dtype: bfloat16
EOF

echo "Starting Stage 2 merge at: $(date)"
mergekit-yaml configs/stage2.yaml ./checkpoints/elson-finance-trading-14b-final --cuda --low-cpu-memory
echo "Stage 2 complete at: $(date)"
echo "Output: ./checkpoints/elson-finance-trading-14b-final"

# ============================================
# Upload to GCS
# ============================================
echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║  UPLOADING TO GOOGLE CLOUD STORAGE                                ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"

# Create bucket if not exists
gsutil mb -l us-west1 gs://${BUCKET_NAME}/ 2>/dev/null || true

# Upload the final model
echo "Uploading model to gs://${BUCKET_NAME}/elson-finance-trading-14b-final/"
gsutil -m cp -r ./checkpoints/elson-finance-trading-14b-final gs://${BUCKET_NAME}/

# Upload logs
gsutil cp $LOG_FILE gs://${BUCKET_NAME}/logs/model-merge-$(date +%Y%m%d-%H%M%S).log

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                    MODEL MERGE COMPLETE                           ║"
echo "╠═══════════════════════════════════════════════════════════════════╣"
echo "║  Your proprietary Elson-Finance-Trading-14B model is ready!      ║"
echo "║                                                                   ║"
echo "║  Location: gs://${BUCKET_NAME}/elson-finance-trading-14b-final   ║"
echo "║                                                                   ║"
echo "║  Next steps:                                                      ║"
echo "║  1. Deploy with vLLM or Ollama                                   ║"
echo "║  2. Fine-tune on proprietary trading data                        ║"
echo "║  3. Integrate with trading engine                                ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Completed at: $(date)"

# Auto-shutdown to save costs
echo ""
echo "=== Auto-shutting down VM to save costs ==="
echo "Model is safely stored in GCS."
sleep 10
sudo shutdown -h now
