#!/bin/bash
# Elson TB2 - H100 DoRA Training + QDoRA Quantization Pipeline
#
# This script runs the complete training pipeline on H100:
#   1. Train DoRA with 950 Q&A pairs
#   2. Quantize to QDoRA (4-bit AWQ)
#   3. Upload both models to GCS
#
# Usage:
#   ./scripts/train-and-quantize-h100.sh [--dry-run]
#
# Prerequisites:
#   - H100 VM running (elson-h100-spot)
#   - Training data at: backend/training_data/consolidated_training_data.json
#   - Base model downloaded or accessible
#
# Cost: ~$1-2 total (~15-20 min on H100 Spot at $2.50/hr)

set -e

# Configuration
PROJECT_ID="elson-33a95"
GCS_BUCKET="gs://elson-33a95-elson-models"
BASE_MODEL="$GCS_BUCKET/elson-finance-trading-14b-final"
TRAINING_DATA="backend/training_data/consolidated_training_data.json"
DORA_OUTPUT="wealth-dora-elson14b-h100-v2"
QDORA_OUTPUT="elson-finance-trading-wealth-14b-q4-v2"

# Training hyperparameters (optimized for H100 80GB)
DORA_RANK=128          # Increased from 64 for better expressiveness
DORA_ALPHA=256         # 2x rank
BATCH_SIZE=16          # H100 can handle larger batches
GRAD_ACCUM=4           # Effective batch size: 64
EPOCHS=5               # More epochs for better convergence
MAX_LENGTH=2048        # Context length
LEARNING_RATE="2e-4"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  Elson TB2 - H100 Training Pipeline${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo -e "${BLUE}Model:${NC} Elson-Finance-Trading-14B"
    echo -e "${BLUE}Method:${NC} DoRA (r=$DORA_RANK, α=$DORA_ALPHA) → QDoRA (4-bit)"
    echo -e "${BLUE}Data:${NC} 950 Q&A pairs"
    echo -e "${BLUE}GPU:${NC} NVIDIA H100 80GB HBM3"
    echo ""
}

check_gpu() {
    echo -e "${BLUE}Checking GPU...${NC}"
    if ! nvidia-smi &> /dev/null; then
        echo -e "${RED}Error: No GPU detected. Are you on the H100 VM?${NC}"
        echo "Start VM: gcloud compute instances start elson-h100-spot --zone=us-central1-a"
        exit 1
    fi

    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
    GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader | head -1)
    echo -e "${GREEN}GPU: $GPU_NAME ($GPU_MEM)${NC}"

    if [[ ! "$GPU_NAME" =~ "H100" ]]; then
        echo -e "${YELLOW}Warning: Expected H100, got $GPU_NAME${NC}"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

check_training_data() {
    echo -e "\n${BLUE}Checking training data...${NC}"

    if [[ ! -f "$TRAINING_DATA" ]]; then
        echo -e "${RED}Error: Training data not found at $TRAINING_DATA${NC}"
        echo "Run: git pull origin main"
        exit 1
    fi

    PAIR_COUNT=$(python3 -c "import json; print(len(json.load(open('$TRAINING_DATA'))))" 2>/dev/null || echo "0")
    echo -e "${GREEN}Training pairs: $PAIR_COUNT${NC}"

    if [[ "$PAIR_COUNT" -lt 500 ]]; then
        echo -e "${YELLOW}Warning: Expected 950+ pairs, got $PAIR_COUNT${NC}"
    fi
}

install_dependencies() {
    echo -e "\n${BLUE}Installing dependencies...${NC}"
    pip install --quiet --upgrade pip
    pip install --quiet torch transformers peft bitsandbytes accelerate
    pip install --quiet datasets trl wandb
    pip install --quiet auto-awq  # For quantization
    echo -e "${GREEN}Dependencies installed${NC}"
}

download_base_model() {
    echo -e "\n${BLUE}Downloading base model from GCS...${NC}"

    if [[ -d "/workspace/base_model" ]] && [[ -f "/workspace/base_model/config.json" ]]; then
        echo -e "${GREEN}Base model already exists at /workspace/base_model${NC}"
        return
    fi

    mkdir -p /workspace/base_model
    gsutil -m cp -r "$BASE_MODEL/final/*" /workspace/base_model/
    echo -e "${GREEN}Base model downloaded (27.52GB)${NC}"
}

train_dora() {
    echo -e "\n${GREEN}============================================${NC}"
    echo -e "${GREEN}  Stage 1: DoRA Training${NC}"
    echo -e "${GREEN}============================================${NC}"

    mkdir -p /workspace/$DORA_OUTPUT

    python3 << 'TRAINING_SCRIPT'
import os
import json
import torch
from datetime import datetime
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer
from datasets import Dataset

# Configuration from environment
DORA_RANK = int(os.environ.get('DORA_RANK', 128))
DORA_ALPHA = int(os.environ.get('DORA_ALPHA', 256))
BATCH_SIZE = int(os.environ.get('BATCH_SIZE', 16))
GRAD_ACCUM = int(os.environ.get('GRAD_ACCUM', 4))
EPOCHS = int(os.environ.get('EPOCHS', 5))
MAX_LENGTH = int(os.environ.get('MAX_LENGTH', 2048))
LEARNING_RATE = float(os.environ.get('LEARNING_RATE', 2e-4))
OUTPUT_DIR = f"/workspace/{os.environ.get('DORA_OUTPUT', 'wealth-dora-elson14b-h100-v2')}"

print(f"\n{'='*50}")
print(f"DoRA Training Configuration")
print(f"{'='*50}")
print(f"Rank (r): {DORA_RANK}")
print(f"Alpha: {DORA_ALPHA}")
print(f"Batch Size: {BATCH_SIZE}")
print(f"Gradient Accumulation: {GRAD_ACCUM}")
print(f"Effective Batch Size: {BATCH_SIZE * GRAD_ACCUM}")
print(f"Epochs: {EPOCHS}")
print(f"Learning Rate: {LEARNING_RATE}")
print(f"Max Length: {MAX_LENGTH}")
print(f"Output: {OUTPUT_DIR}")
print(f"{'='*50}\n")

# Load training data
print("Loading training data...")
with open(os.environ.get('TRAINING_DATA', 'backend/training_data/consolidated_training_data.json')) as f:
    training_data = json.load(f)
print(f"Loaded {len(training_data)} training pairs")

# Format for training
def format_example(example):
    return {
        "text": f"### Question:\n{example['question']}\n\n### Answer:\n{example['answer']}"
    }

dataset = Dataset.from_list([format_example(ex) for ex in training_data])
print(f"Dataset prepared: {len(dataset)} examples")

# Load tokenizer
print("\nLoading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained("/workspace/base_model", trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

# Load model with bfloat16 (H100 native precision)
print("Loading base model (this may take a few minutes)...")
model = AutoModelForCausalLM.from_pretrained(
    "/workspace/base_model",
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True,
)
print(f"Model loaded on {model.device}")

# Configure DoRA (LoRA with use_dora=True)
print("\nConfiguring DoRA adapter...")
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=DORA_RANK,
    lora_alpha=DORA_ALPHA,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    use_dora=True,  # Enable DoRA
    bias="none",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Training arguments
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRAD_ACCUM,
    learning_rate=LEARNING_RATE,
    weight_decay=0.01,
    warmup_ratio=0.03,
    lr_scheduler_type="cosine",
    logging_steps=10,
    save_steps=100,
    save_total_limit=2,
    bf16=True,  # H100 native
    gradient_checkpointing=True,
    optim="adamw_torch_fused",  # Fast optimizer for H100
    report_to="none",
    max_grad_norm=0.3,
)

# Initialize trainer
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
    max_seq_length=MAX_LENGTH,
    dataset_text_field="text",
    packing=True,  # Pack short sequences for efficiency
)

# Train
print(f"\n{'='*50}")
print("Starting DoRA training...")
print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*50}\n")

train_result = trainer.train()

print(f"\n{'='*50}")
print("Training complete!")
print(f"Final loss: {train_result.training_loss:.4f}")
print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*50}\n")

# Save the adapter
print("Saving DoRA adapter...")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

# Save training metadata
metadata = {
    "model": "Elson-Finance-Trading-14B",
    "method": "DoRA",
    "rank": DORA_RANK,
    "alpha": DORA_ALPHA,
    "epochs": EPOCHS,
    "batch_size": BATCH_SIZE * GRAD_ACCUM,
    "learning_rate": LEARNING_RATE,
    "training_pairs": len(training_data),
    "final_loss": train_result.training_loss,
    "trained_on": "H100 80GB",
    "timestamp": datetime.now().isoformat(),
}
with open(f"{OUTPUT_DIR}/training_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print(f"DoRA adapter saved to {OUTPUT_DIR}")
TRAINING_SCRIPT
}

quantize_to_qdora() {
    echo -e "\n${GREEN}============================================${NC}"
    echo -e "${GREEN}  Stage 2: QDoRA Quantization (4-bit AWQ)${NC}"
    echo -e "${GREEN}============================================${NC}"

    mkdir -p /workspace/$QDORA_OUTPUT

    python3 << 'QUANTIZE_SCRIPT'
import os
import json
import torch
from datetime import datetime
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from awq import AutoAWQForCausalLM

DORA_OUTPUT = os.environ.get('DORA_OUTPUT', 'wealth-dora-elson14b-h100-v2')
QDORA_OUTPUT = os.environ.get('QDORA_OUTPUT', 'elson-finance-trading-wealth-14b-q4-v2')

print(f"\n{'='*50}")
print("QDoRA Quantization (4-bit AWQ)")
print(f"{'='*50}")
print(f"Input: /workspace/{DORA_OUTPUT}")
print(f"Output: /workspace/{QDORA_OUTPUT}")
print(f"{'='*50}\n")

# Load base model + DoRA adapter
print("Loading base model with DoRA adapter...")
base_model = AutoModelForCausalLM.from_pretrained(
    "/workspace/base_model",
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True,
)
model = PeftModel.from_pretrained(base_model, f"/workspace/{DORA_OUTPUT}")

# Merge adapter into base model
print("Merging DoRA adapter into base model...")
model = model.merge_and_unload()

# Save merged model temporarily
print("Saving merged model...")
merged_path = "/workspace/merged_temp"
model.save_pretrained(merged_path)

tokenizer = AutoTokenizer.from_pretrained(f"/workspace/{DORA_OUTPUT}")
tokenizer.save_pretrained(merged_path)

# Quantize with AWQ
print("\nQuantizing to 4-bit AWQ...")
quant_config = {
    "zero_point": True,
    "q_group_size": 128,
    "w_bit": 4,
    "version": "GEMM"
}

awq_model = AutoAWQForCausalLM.from_pretrained(merged_path, trust_remote_code=True)
awq_model.quantize(tokenizer, quant_config=quant_config)

# Save quantized model
print(f"Saving quantized model to /workspace/{QDORA_OUTPUT}...")
awq_model.save_quantized(f"/workspace/{QDORA_OUTPUT}")
tokenizer.save_pretrained(f"/workspace/{QDORA_OUTPUT}")

# Save quantization metadata
metadata = {
    "model": "Elson-Finance-Trading-14B + DoRA",
    "quantization": "AWQ 4-bit",
    "q_group_size": 128,
    "source_adapter": DORA_OUTPUT,
    "timestamp": datetime.now().isoformat(),
}
with open(f"/workspace/{QDORA_OUTPUT}/quantization_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

# Cleanup
import shutil
shutil.rmtree(merged_path)

print(f"\n{'='*50}")
print("Quantization complete!")
print(f"QDoRA model saved to /workspace/{QDORA_OUTPUT}")
print(f"{'='*50}\n")
QUANTIZE_SCRIPT
}

upload_to_gcs() {
    echo -e "\n${GREEN}============================================${NC}"
    echo -e "${GREEN}  Stage 3: Upload to GCS${NC}"
    echo -e "${GREEN}============================================${NC}"

    echo -e "${BLUE}Uploading DoRA adapter...${NC}"
    gsutil -m cp -r /workspace/$DORA_OUTPUT $GCS_BUCKET/
    echo -e "${GREEN}DoRA uploaded to $GCS_BUCKET/$DORA_OUTPUT${NC}"

    echo -e "\n${BLUE}Uploading QDoRA model...${NC}"
    gsutil -m cp -r /workspace/$QDORA_OUTPUT $GCS_BUCKET/
    echo -e "${GREEN}QDoRA uploaded to $GCS_BUCKET/$QDORA_OUTPUT${NC}"

    echo -e "\n${BLUE}Verifying uploads...${NC}"
    gsutil ls -l "$GCS_BUCKET/$DORA_OUTPUT/"
    gsutil ls -l "$GCS_BUCKET/$QDORA_OUTPUT/"
}

print_summary() {
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  Training Pipeline Complete!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo -e "${BLUE}Models created:${NC}"
    echo "  1. DoRA:  $GCS_BUCKET/$DORA_OUTPUT"
    echo "  2. QDoRA: $GCS_BUCKET/$QDORA_OUTPUT"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Stop H100 VM to save costs:"
    echo "     gcloud compute instances stop elson-h100-spot --zone=us-central1-a"
    echo ""
    echo "  2. Deploy QDoRA on L4 for inference:"
    echo "     ./scripts/deploy-vllm-dora.sh l4 qdora"
    echo ""
    echo "  3. Run evaluation benchmark:"
    echo "     python scripts/run_evaluation_benchmark.py --api-url http://EXTERNAL_IP:8000"
    echo ""
}

# Main execution
print_header

if [[ "$1" == "--dry-run" ]]; then
    echo -e "${YELLOW}DRY RUN - No actual training will occur${NC}"
    check_gpu
    check_training_data
    echo -e "\n${GREEN}Dry run complete. Ready for training.${NC}"
    exit 0
fi

# Export environment variables for Python scripts
export DORA_RANK DORA_ALPHA BATCH_SIZE GRAD_ACCUM EPOCHS MAX_LENGTH LEARNING_RATE
export DORA_OUTPUT QDORA_OUTPUT TRAINING_DATA

check_gpu
check_training_data
install_dependencies
download_base_model
train_dora
quantize_to_qdora
upload_to_gcs
print_summary

echo -e "${GREEN}Done!${NC}"
