#!/usr/bin/env python3
"""
Elson Financial AI - Model Merge via Vertex AI

Submits a custom training job to Vertex AI with GPU to run the model merge.
Uses your existing GCP project and integrates with Cloud Build.

Usage:
    python scripts/run_model_merge_vertex.py

Requirements:
    pip install google-cloud-aiplatform

Copyright (c) 2024 Elson Wealth. All rights reserved.
"""

import os
import sys
from datetime import datetime

# Try to import google cloud, provide helpful error if missing
try:
    from google.cloud import aiplatform
except ImportError:
    print("Installing google-cloud-aiplatform...")
    os.system(f"{sys.executable} -m pip install google-cloud-aiplatform")
    from google.cloud import aiplatform


def create_model_merge_job():
    """Submit a Vertex AI custom training job to merge the model."""

    # Configuration
    PROJECT_ID = os.environ.get("GCP_PROJECT_ID", os.environ.get("PROJECT_ID"))
    REGION = os.environ.get("GCP_REGION", "us-west1")
    HF_TOKEN = os.environ.get("HF_TOKEN")
    BUCKET_NAME = f"{PROJECT_ID}-elson-models"

    if not PROJECT_ID:
        print("Error: Set GCP_PROJECT_ID or PROJECT_ID environment variable")
        sys.exit(1)

    if not HF_TOKEN:
        print("Error: Set HF_TOKEN environment variable")
        sys.exit(1)

    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║           ELSON FINANCIAL AI - MODEL MERGE (VERTEX AI)            ║
╠═══════════════════════════════════════════════════════════════════╣
║  Project: {PROJECT_ID:<52} ║
║  Region:  {REGION:<52} ║
║  Output:  gs://{BUCKET_NAME}/elson-finance-trading-14b-final  ║
╚═══════════════════════════════════════════════════════════════════╝
""")

    # Initialize Vertex AI
    aiplatform.init(project=PROJECT_ID, location=REGION)

    # The training script that runs on Vertex AI
    TRAINING_SCRIPT = '''
#!/bin/bash
set -e

echo "=== Elson Financial AI Model Merge ==="
echo "Started at: $(date)"

# Install dependencies
pip install -q mergekit transformers safetensors accelerate huggingface_hub sentencepiece

# Login to HuggingFace
python -c "from huggingface_hub import login; login(token='$HF_TOKEN')"

# Create workspace
mkdir -p /workspace/checkpoints /workspace/configs
cd /workspace

# Stage 1: SLERP
echo "=== STAGE 1: SLERP ==="
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
mergekit-yaml configs/stage1.yaml ./checkpoints/elson-reason-math-14b --cuda --low-cpu-memory

# Stage 2: TIES
echo "=== STAGE 2: TIES ==="
cat > configs/stage2.yaml << 'EOF'
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
mergekit-yaml configs/stage2.yaml ./checkpoints/elson-finance-trading-14b --cuda --low-cpu-memory

# Stage 3: DARE
echo "=== STAGE 3: DARE ==="
cat > configs/stage3.yaml << 'EOF'
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
mergekit-yaml configs/stage3.yaml ./checkpoints/elson-finance-trading-14b-final --cuda --low-cpu-memory

# Upload to GCS
echo "=== Uploading to GCS ==="
gsutil -m cp -r ./checkpoints/elson-finance-trading-14b-final gs://$BUCKET_NAME/

echo "=== COMPLETE ==="
echo "Model at: gs://$BUCKET_NAME/elson-finance-trading-14b-final"
'''

    # Create and submit the custom job
    job = aiplatform.CustomJob(
        display_name=f"elson-model-merge-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        worker_pool_specs=[
            {
                "machine_spec": {
                    "machine_type": "n1-standard-8",
                    "accelerator_type": "NVIDIA_TESLA_A100",
                    "accelerator_count": 1,
                },
                "replica_count": 1,
                "disk_spec": {
                    "boot_disk_type": "pd-ssd",
                    "boot_disk_size_gb": 500,
                },
                "container_spec": {
                    "image_uri": "pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime",
                    "command": ["bash", "-c", TRAINING_SCRIPT],
                    "env": [
                        {"name": "HF_TOKEN", "value": HF_TOKEN},
                        {"name": "BUCKET_NAME", "value": BUCKET_NAME},
                    ],
                },
            }
        ],
    )

    print("Submitting Vertex AI training job...")
    print("This will take 2-3 hours. You can monitor at:")
    print(f"  https://console.cloud.google.com/vertex-ai/training/custom-jobs?project={PROJECT_ID}")

    # Submit the job
    job.run(
        sync=False,  # Don't wait for completion
        service_account=f"vertex-ai@{PROJECT_ID}.iam.gserviceaccount.com",
    )

    print(f"\nJob submitted: {job.display_name}")
    print(f"Job ID: {job.resource_name}")
    print("\nWhen complete, your model will be at:")
    print(f"  gs://{BUCKET_NAME}/elson-finance-trading-14b-final")


if __name__ == "__main__":
    create_model_merge_job()
