#!/bin/bash
# Elson TB2 - H100 Curriculum Training Pipeline
#
# This script runs the 3-PHASE CURRICULUM TRAINING on H100:
#   Phase A: Domain Blocks (35% easy, 35% medium, 25% hard, 5% extreme)
#   Phase B: Mixed Curriculum (20% easy, 40% medium, 30% hard, 10% extreme)
#   Phase C: Stress Epoch (10% easy, 25% medium, 35% hard, 30% extreme)
#
# Usage:
#   ./scripts/train-curriculum-h100.sh [--dry-run] [--phase A|B|C|all]
#
# Prerequisites:
#   - H100 VM running (elson-h100-spot)
#   - Domain buckets built: backend/training_data/domain_buckets/
#   - Curriculum manifests generated: python scripts/curriculum_sampler.py --phase all
#
# Cost: ~$2-3 total (~45-60 min on H100 Spot at $2.50/hr)

set -e

# Configuration
PROJECT_ID="elson-33a95"
GCS_BUCKET="gs://elson-33a95-elson-models"
BASE_MODEL="$GCS_BUCKET/elson-finance-trading-14b-final"
CURRICULUM_DIR="backend/training_data/curriculum_runs"
DORA_OUTPUT="wealth-dora-elson14b-h100-v3-curriculum"
QDORA_OUTPUT="elson-finance-trading-wealth-14b-q4-v3-curriculum"

# Training hyperparameters (optimized for H100 80GB)
DORA_RANK=128
DORA_ALPHA=256
BATCH_SIZE=16
GRAD_ACCUM=4
EPOCHS_PER_PHASE=2
MAX_LENGTH=2048
LEARNING_RATE="2e-4"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PHASE_TO_RUN="${2:-all}"

print_header() {
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  Elson TB2 - Curriculum Training Pipeline${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo -e "${BLUE}Model:${NC} Elson-Finance-Trading-14B"
    echo -e "${BLUE}Method:${NC} 3-Phase Curriculum Training"
    echo -e "${BLUE}GPU:${NC} NVIDIA H100 80GB HBM3"
    echo ""
    echo -e "${BLUE}Phase A:${NC} Domain Blocks (35% easy, 35% medium, 25% hard, 5% extreme)"
    echo -e "${BLUE}Phase B:${NC} Mixed Curriculum (20% easy, 40% medium, 30% hard, 10% extreme)"
    echo -e "${BLUE}Phase C:${NC} Stress Epoch (10% easy, 25% medium, 35% hard, 30% extreme)"
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

check_curriculum_data() {
    echo -e "\n${BLUE}Checking curriculum training data...${NC}"

    # Check if domain buckets exist
    if [[ ! -d "backend/training_data/domain_buckets" ]]; then
        echo -e "${RED}Error: Domain buckets not found at backend/training_data/domain_buckets${NC}"
        echo "Run: python scripts/domain_bucket_builder.py"
        exit 1
    fi

    # Check bucket count
    BUCKET_COUNT=$(find backend/training_data/domain_buckets -name "*.jsonl" | wc -l)
    echo -e "${GREEN}Domain buckets found: $BUCKET_COUNT files${NC}"

    # Check if curriculum manifests exist
    if [[ ! -d "$CURRICULUM_DIR" ]]; then
        echo -e "${YELLOW}Warning: Curriculum runs directory not found. Generating manifests...${NC}"
        python3 scripts/curriculum_sampler.py --phase all --target-records 15000
    fi

    # List available manifests
    echo -e "\n${BLUE}Available curriculum manifests:${NC}"
    ls -la "$CURRICULUM_DIR"/*.jsonl 2>/dev/null | tail -10 || echo "No manifests found"

    # Get latest merged files for each phase
    PHASE_A_FILE=$(ls -t "$CURRICULUM_DIR"/merged_phaseA_*.jsonl 2>/dev/null | head -1)
    PHASE_B_FILE=$(ls -t "$CURRICULUM_DIR"/merged_phaseB_*.jsonl 2>/dev/null | head -1)
    PHASE_C_FILE=$(ls -t "$CURRICULUM_DIR"/merged_phaseC_*.jsonl 2>/dev/null | head -1)

    if [[ -z "$PHASE_A_FILE" ]] || [[ -z "$PHASE_B_FILE" ]] || [[ -z "$PHASE_C_FILE" ]]; then
        echo -e "${YELLOW}Missing phase files. Generating fresh manifests...${NC}"
        python3 scripts/curriculum_sampler.py --phase all --target-records 15000
        PHASE_A_FILE=$(ls -t "$CURRICULUM_DIR"/merged_phaseA_*.jsonl 2>/dev/null | head -1)
        PHASE_B_FILE=$(ls -t "$CURRICULUM_DIR"/merged_phaseB_*.jsonl 2>/dev/null | head -1)
        PHASE_C_FILE=$(ls -t "$CURRICULUM_DIR"/merged_phaseC_*.jsonl 2>/dev/null | head -1)
    fi

    echo -e "\n${GREEN}Using training files:${NC}"
    echo "  Phase A: $PHASE_A_FILE"
    echo "  Phase B: $PHASE_B_FILE"
    echo "  Phase C: $PHASE_C_FILE"

    # Count records in each phase
    PHASE_A_COUNT=$(wc -l < "$PHASE_A_FILE" 2>/dev/null || echo "0")
    PHASE_B_COUNT=$(wc -l < "$PHASE_B_FILE" 2>/dev/null || echo "0")
    PHASE_C_COUNT=$(wc -l < "$PHASE_C_FILE" 2>/dev/null || echo "0")

    echo -e "\n${GREEN}Training data counts:${NC}"
    echo "  Phase A: $PHASE_A_COUNT examples"
    echo "  Phase B: $PHASE_B_COUNT examples"
    echo "  Phase C: $PHASE_C_COUNT examples"
    echo "  Total: $((PHASE_A_COUNT + PHASE_B_COUNT + PHASE_C_COUNT)) examples"

    export PHASE_A_FILE PHASE_B_FILE PHASE_C_FILE
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

train_phase() {
    local PHASE=$1
    local TRAINING_FILE=$2
    local TIER_DESC=$3

    echo -e "\n${GREEN}============================================${NC}"
    echo -e "${GREEN}  Phase $PHASE: $TIER_DESC${NC}"
    echo -e "${GREEN}============================================${NC}"

    python3 << TRAINING_SCRIPT
import os
import json
import torch
from datetime import datetime
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, TaskType, PeftModel
from trl import SFTTrainer
from datasets import Dataset

# Configuration
PHASE = "$PHASE"
TRAINING_FILE = "$TRAINING_FILE"
DORA_RANK = int(os.environ.get('DORA_RANK', 128))
DORA_ALPHA = int(os.environ.get('DORA_ALPHA', 256))
BATCH_SIZE = int(os.environ.get('BATCH_SIZE', 16))
GRAD_ACCUM = int(os.environ.get('GRAD_ACCUM', 4))
EPOCHS = int(os.environ.get('EPOCHS_PER_PHASE', 2))
MAX_LENGTH = int(os.environ.get('MAX_LENGTH', 2048))
LEARNING_RATE = float(os.environ.get('LEARNING_RATE', 2e-4))
DORA_OUTPUT = os.environ.get('DORA_OUTPUT', 'wealth-dora-elson14b-h100-v3-curriculum')
OUTPUT_DIR = f"/workspace/{DORA_OUTPUT}/phase_{PHASE}"

print(f"\n{'='*50}")
print(f"Phase {PHASE} Training Configuration")
print(f"{'='*50}")
print(f"Training File: {TRAINING_FILE}")
print(f"Rank (r): {DORA_RANK}")
print(f"Alpha: {DORA_ALPHA}")
print(f"Batch Size: {BATCH_SIZE}")
print(f"Epochs: {EPOCHS}")
print(f"Output: {OUTPUT_DIR}")
print(f"{'='*50}\n")

# Load training data from JSONL
print("Loading training data...")
training_data = []
with open(TRAINING_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            training_data.append(json.loads(line))
print(f"Loaded {len(training_data)} training pairs")

# Format for training
def format_example(example):
    instruction = example.get('instruction', example.get('question', ''))
    input_text = example.get('input', '')
    output = example.get('output', example.get('answer', ''))

    if input_text:
        return {"text": f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n{output}"}
    else:
        return {"text": f"### Instruction:\n{instruction}\n\n### Response:\n{output}"}

dataset = Dataset.from_list([format_example(ex) for ex in training_data])
print(f"Dataset prepared: {len(dataset)} examples")

# Load tokenizer
print("\nLoading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained("/workspace/base_model", trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

# Check if we should continue from previous phase
PREV_PHASE = {"B": "A", "C": "B"}.get(PHASE)
if PREV_PHASE and os.path.exists(f"/workspace/{DORA_OUTPUT}/phase_{PREV_PHASE}"):
    print(f"Loading model from Phase {PREV_PHASE}...")
    base_model = AutoModelForCausalLM.from_pretrained(
        "/workspace/base_model",
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(
        base_model,
        f"/workspace/{DORA_OUTPUT}/phase_{PREV_PHASE}",
        is_trainable=True
    )
    print(f"Continuing from Phase {PREV_PHASE} checkpoint")
else:
    # Load fresh base model
    print("Loading base model (this may take a few minutes)...")
    model = AutoModelForCausalLM.from_pretrained(
        "/workspace/base_model",
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )

    # Configure DoRA
    print("\nConfiguring DoRA adapter...")
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=DORA_RANK,
        lora_alpha=DORA_ALPHA,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        use_dora=True,
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
    bf16=True,
    gradient_checkpointing=True,
    optim="adamw_torch_fused",
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
    packing=True,
)

# Train
print(f"\n{'='*50}")
print(f"Starting Phase {PHASE} training...")
print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*50}\n")

train_result = trainer.train()

print(f"\n{'='*50}")
print(f"Phase {PHASE} training complete!")
print(f"Final loss: {train_result.training_loss:.4f}")
print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*50}\n")

# Save
print(f"Saving Phase {PHASE} checkpoint...")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

# Save metadata
metadata = {
    "phase": PHASE,
    "model": "Elson-Finance-Trading-14B",
    "method": "Curriculum DoRA",
    "rank": DORA_RANK,
    "alpha": DORA_ALPHA,
    "epochs": EPOCHS,
    "batch_size": BATCH_SIZE * GRAD_ACCUM,
    "training_pairs": len(training_data),
    "final_loss": train_result.training_loss,
    "timestamp": datetime.now().isoformat(),
}
with open(f"{OUTPUT_DIR}/training_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print(f"Phase {PHASE} checkpoint saved to {OUTPUT_DIR}")
TRAINING_SCRIPT
}

run_curriculum_training() {
    echo -e "\n${GREEN}============================================${NC}"
    echo -e "${GREEN}  Starting 3-Phase Curriculum Training${NC}"
    echo -e "${GREEN}============================================${NC}"

    # Phase A: Domain Blocks
    if [[ "$PHASE_TO_RUN" == "all" ]] || [[ "$PHASE_TO_RUN" == "A" ]]; then
        train_phase "A" "$PHASE_A_FILE" "Domain Blocks (35% easy, 35% medium, 25% hard, 5% extreme)"
    fi

    # Phase B: Mixed Curriculum
    if [[ "$PHASE_TO_RUN" == "all" ]] || [[ "$PHASE_TO_RUN" == "B" ]]; then
        train_phase "B" "$PHASE_B_FILE" "Mixed Curriculum (20% easy, 40% medium, 30% hard, 10% extreme)"
    fi

    # Phase C: Stress Epoch
    if [[ "$PHASE_TO_RUN" == "all" ]] || [[ "$PHASE_TO_RUN" == "C" ]]; then
        train_phase "C" "$PHASE_C_FILE" "Stress Epoch (10% easy, 25% medium, 35% hard, 30% extreme)"
    fi

    # Copy final phase to main output directory
    echo -e "\n${BLUE}Copying final checkpoint...${NC}"
    cp -r "/workspace/$DORA_OUTPUT/phase_C/"* "/workspace/$DORA_OUTPUT/" 2>/dev/null || \
    cp -r "/workspace/$DORA_OUTPUT/phase_B/"* "/workspace/$DORA_OUTPUT/" 2>/dev/null || \
    cp -r "/workspace/$DORA_OUTPUT/phase_A/"* "/workspace/$DORA_OUTPUT/" 2>/dev/null

    echo -e "${GREEN}Curriculum training complete!${NC}"
}

upload_to_gcs() {
    echo -e "\n${GREEN}============================================${NC}"
    echo -e "${GREEN}  Uploading to GCS${NC}"
    echo -e "${GREEN}============================================${NC}"

    echo -e "${BLUE}Uploading DoRA adapter...${NC}"
    gsutil -m cp -r /workspace/$DORA_OUTPUT $GCS_BUCKET/
    echo -e "${GREEN}DoRA uploaded to $GCS_BUCKET/$DORA_OUTPUT${NC}"

    echo -e "\n${BLUE}Verifying upload...${NC}"
    gsutil ls -l "$GCS_BUCKET/$DORA_OUTPUT/"
}

print_summary() {
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  Curriculum Training Complete!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo -e "${BLUE}Model created:${NC}"
    echo "  DoRA (Curriculum): $GCS_BUCKET/$DORA_OUTPUT"
    echo ""
    echo -e "${BLUE}Training phases completed:${NC}"
    echo "  Phase A: Domain Blocks"
    echo "  Phase B: Mixed Curriculum"
    echo "  Phase C: Stress Epoch"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Stop H100 VM to save costs:"
    echo "     gcloud compute instances stop elson-h100-spot --zone=us-central1-a"
    echo ""
    echo "  2. Deploy on L4 for inference:"
    echo "     ./scripts/deploy-vllm-dora.sh l4 dora"
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
    check_curriculum_data
    echo -e "\n${GREEN}Dry run complete. Ready for curriculum training.${NC}"
    exit 0
fi

# Export environment variables
export DORA_RANK DORA_ALPHA BATCH_SIZE GRAD_ACCUM EPOCHS_PER_PHASE MAX_LENGTH LEARNING_RATE
export DORA_OUTPUT QDORA_OUTPUT

check_gpu
check_curriculum_data
install_dependencies
download_base_model
run_curriculum_training
upload_to_gcs
print_summary

echo -e "${GREEN}Done!${NC}"
