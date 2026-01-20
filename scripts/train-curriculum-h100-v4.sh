#!/usr/bin/env bash
# =============================================================================
# Elson TB2 - H100 Curriculum Training Pipeline v4
# =============================================================================
#
# CRITICAL FIXES IN V4:
#   1. Phase A: packing=False to restore optimizer steps
#   2. Warmup is step-based, not ratio-based
#   3. Scheduler is constant_with_warmup for Phase A, cosine for B/C
#   4. Diagnostic logging prints counts and expected steps every phase
#   5. Guards against warmup_steps > total_steps
#
# Usage:
#   ./scripts/train-curriculum-h100-v4.sh [--dry-run] [--phase A|B|C|all]
#
# Prerequisites:
#   - H100 VM running (elson-h100-spot)
#   - Domain buckets built: backend/training_data/domain_buckets/
#   - Curriculum manifests generated: python scripts/curriculum_sampler.py --phase all
#
# Cost: ~$2-4 total (~60-90 min on H100 Spot at $2.50/hr)
# =============================================================================

set -euo pipefail

# Configuration
PROJECT_ID="elson-33a95"
GCS_BUCKET="gs://elson-33a95-elson-models"
BASE_MODEL="$GCS_BUCKET/elson-finance-trading-14b-final"
CURRICULUM_DIR="backend/training_data/curriculum_runs"
DORA_OUTPUT="wealth-dora-elson14b-h100-v4-curriculum"
DATA_DIR="backend/training_data"

# =============================================================================
# V4 HYPERPARAMETERS - FIXED FOR PROPER LEARNING
# =============================================================================

# DoRA Configuration
DORA_RANK=128
DORA_ALPHA=256

# Batch Configuration (unchanged - effective batch 64)
BATCH_SIZE=4
GRAD_ACCUM=16

# Context Length
MAX_LENGTH=2048

# PHASE A: Domain Blocks - NO PACKING, more epochs, step-based warmup
PHASE_A_EPOCHS=8
PHASE_A_LR="1e-4"
PHASE_A_WARMUP_STEPS=20
PHASE_A_SCHEDULER="constant_with_warmup"
PHASE_A_PACKING="false"

# PHASE B: Mixed Curriculum - packing OK, cosine schedule
PHASE_B_EPOCHS=3
PHASE_B_LR="5e-5"
PHASE_B_WARMUP_STEPS=60
PHASE_B_SCHEDULER="cosine"
PHASE_B_PACKING="true"

# PHASE C: Stress Epoch - packing OK, lower LR
PHASE_C_EPOCHS=2
PHASE_C_LR="2e-5"
PHASE_C_WARMUP_STEPS=30
PHASE_C_SCHEDULER="cosine"
PHASE_C_PACKING="true"

# Minimum steps guard (refuse to run if below this)
MIN_STEPS_PHASE_A=50
MIN_STEPS_PHASE_B=100
MIN_STEPS_PHASE_C=50

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Parse arguments
DRY_RUN=false
PHASE_TO_RUN="all"

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --phase)
            PHASE_TO_RUN="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

print_header() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║     Elson TB2 - Curriculum Training Pipeline v4               ║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║  CRITICAL FIXES IN V4:                                        ║${NC}"
    echo -e "${GREEN}║  • Phase A: packing=False (restores optimizer steps)          ║${NC}"
    echo -e "${GREEN}║  • Step-based warmup (not ratio-based)                        ║${NC}"
    echo -e "${GREEN}║  • Diagnostic logging with step count verification            ║${NC}"
    echo -e "${GREEN}║  • Guards against broken LR schedules                         ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Model:${NC} Elson-Finance-Trading-14B"
    echo -e "${BLUE}Method:${NC} 3-Phase Curriculum Training (v4 - Fixed)"
    echo -e "${BLUE}GPU:${NC} NVIDIA H100 80GB HBM3"
    echo ""
    echo -e "${CYAN}Phase A:${NC} Domain Blocks | packing=${PHASE_A_PACKING} | ${PHASE_A_EPOCHS} epochs | lr=${PHASE_A_LR}"
    echo -e "${CYAN}Phase B:${NC} Mixed Curriculum | packing=${PHASE_B_PACKING} | ${PHASE_B_EPOCHS} epochs | lr=${PHASE_B_LR}"
    echo -e "${CYAN}Phase C:${NC} Stress Epoch | packing=${PHASE_C_PACKING} | ${PHASE_C_EPOCHS} epochs | lr=${PHASE_C_LR}"
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

    # Get latest merged files for each phase
    PHASE_A_FILE=$(ls -t "$CURRICULUM_DIR"/merged_phaseA_*.jsonl 2>/dev/null | head -1 || echo "")
    PHASE_B_FILE=$(ls -t "$CURRICULUM_DIR"/merged_phaseB_*.jsonl 2>/dev/null | head -1 || echo "")
    PHASE_C_FILE=$(ls -t "$CURRICULUM_DIR"/merged_phaseC_*.jsonl 2>/dev/null | head -1 || echo "")

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
    export PHASE_A_COUNT PHASE_B_COUNT PHASE_C_COUNT
}

install_dependencies() {
    echo -e "\n${BLUE}Installing dependencies...${NC}"
    pip install --quiet --upgrade pip
    pip install --quiet torch transformers peft bitsandbytes accelerate
    pip install --quiet datasets trl wandb
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

run_training() {
    echo -e "\n${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Starting v4 Curriculum Training Pipeline${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"

    # Create output directory
    mkdir -p "/workspace/$DORA_OUTPUT"

    # Run the Python training module
    python3 -m backend.scripts.train_curriculum_h100_v4 \
        --base_model "/workspace/base_model" \
        --output_dir "/workspace/$DORA_OUTPUT" \
        --data_dir "$(pwd)/$CURRICULUM_DIR" \
        --phase_a_file "$PHASE_A_FILE" \
        --phase_b_file "$PHASE_B_FILE" \
        --phase_c_file "$PHASE_C_FILE" \
        --rank "$DORA_RANK" \
        --alpha "$DORA_ALPHA" \
        --batch_size "$BATCH_SIZE" \
        --grad_accum "$GRAD_ACCUM" \
        --max_length "$MAX_LENGTH" \
        --phase_a_epochs "$PHASE_A_EPOCHS" \
        --phase_b_epochs "$PHASE_B_EPOCHS" \
        --phase_c_epochs "$PHASE_C_EPOCHS" \
        --lr_a "$PHASE_A_LR" \
        --lr_b "$PHASE_B_LR" \
        --lr_c "$PHASE_C_LR" \
        --warmup_steps_a "$PHASE_A_WARMUP_STEPS" \
        --warmup_steps_b "$PHASE_B_WARMUP_STEPS" \
        --warmup_steps_c "$PHASE_C_WARMUP_STEPS" \
        --scheduler_a "$PHASE_A_SCHEDULER" \
        --scheduler_b "$PHASE_B_SCHEDULER" \
        --scheduler_c "$PHASE_C_SCHEDULER" \
        --packing_a "$PHASE_A_PACKING" \
        --packing_b "$PHASE_B_PACKING" \
        --packing_c "$PHASE_C_PACKING" \
        --min_steps_a "$MIN_STEPS_PHASE_A" \
        --min_steps_b "$MIN_STEPS_PHASE_B" \
        --min_steps_c "$MIN_STEPS_PHASE_C" \
        --phases "$PHASE_TO_RUN" \
        --log_every 1

    echo -e "${GREEN}Curriculum training complete!${NC}"
}

upload_to_gcs() {
    echo -e "\n${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Uploading to GCS${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"

    echo -e "${BLUE}Uploading DoRA adapter...${NC}"
    gsutil -m cp -r "/workspace/$DORA_OUTPUT" "$GCS_BUCKET/"
    echo -e "${GREEN}DoRA uploaded to $GCS_BUCKET/$DORA_OUTPUT${NC}"

    echo -e "\n${BLUE}Verifying upload...${NC}"
    gsutil ls -l "$GCS_BUCKET/$DORA_OUTPUT/"
}

print_summary() {
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Curriculum Training v4 Complete!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}Model created:${NC}"
    echo "  DoRA (Curriculum v4): $GCS_BUCKET/$DORA_OUTPUT"
    echo ""
    echo -e "${BLUE}Key v4 improvements applied:${NC}"
    echo "  • Phase A: packing=False (proper optimizer steps)"
    echo "  • Step-based warmup (not ratio-based)"
    echo "  • Per-phase learning rates (1e-4 → 5e-5 → 2e-5)"
    echo "  • Diagnostic logging verified step counts"
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

# =============================================================================
# MAIN EXECUTION
# =============================================================================

print_header

if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}DRY RUN - No actual training will occur${NC}"
    check_gpu
    check_curriculum_data
    echo ""
    echo -e "${CYAN}Would run training with these parameters:${NC}"
    echo "  Phase A: ${PHASE_A_COUNT} examples, ${PHASE_A_EPOCHS} epochs, packing=${PHASE_A_PACKING}"
    echo "  Phase B: ${PHASE_B_COUNT} examples, ${PHASE_B_EPOCHS} epochs, packing=${PHASE_B_PACKING}"
    echo "  Phase C: ${PHASE_C_COUNT} examples, ${PHASE_C_EPOCHS} epochs, packing=${PHASE_C_PACKING}"
    echo ""
    echo -e "${GREEN}Dry run complete. Ready for curriculum training.${NC}"
    exit 0
fi

check_gpu
check_curriculum_data
install_dependencies
download_base_model
run_training
upload_to_gcs
print_summary

echo -e "${GREEN}Done!${NC}"
