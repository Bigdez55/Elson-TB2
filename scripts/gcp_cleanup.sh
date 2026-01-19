#!/bin/bash
# Elson TB2 - GCP Cloud Shell Cleanup Script
#
# Cleans up disk space in Cloud Shell to prepare for training
# and deployment operations.
#
# Usage: ./scripts/gcp_cleanup.sh [--dry-run]

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo -e "${YELLOW}=== DRY RUN MODE - No changes will be made ===${NC}"
fi

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Elson TB2 - GCP Cloud Shell Cleanup${NC}"
echo -e "${GREEN}============================================${NC}"

# Function to format bytes
format_bytes() {
    numfmt --to=iec-i --suffix=B "$1" 2>/dev/null || echo "$1 bytes"
}

# Show current disk usage
echo -e "\n${BLUE}=== Current Disk Usage ===${NC}"
df -h /home 2>/dev/null || df -h .

echo -e "\n${BLUE}=== Largest Directories ===${NC}"
du -h --max-depth=2 ~/.local 2>/dev/null | sort -rh | head -15 || \
    du -sh ~/.local/* 2>/dev/null | sort -rh | head -15

echo -e "\n${BLUE}=== Cleanup Targets ===${NC}"

# Calculate potential savings
PIP_CACHE=$(du -sb ~/.local/share/pip/cache 2>/dev/null | cut -f1 || echo 0)
SITE_PACKAGES=$(du -sb ~/.local/lib/python*/site-packages 2>/dev/null | cut -f1 || echo 0)
NPM_CACHE=$(du -sb ~/.npm 2>/dev/null | cut -f1 || echo 0)
HUGGINGFACE_CACHE=$(du -sb ~/.cache/huggingface 2>/dev/null | cut -f1 || echo 0)
TORCH_CACHE=$(du -sb ~/.cache/torch 2>/dev/null | cut -f1 || echo 0)

echo "  - pip cache:           $(format_bytes $PIP_CACHE)"
echo "  - site-packages:       $(format_bytes $SITE_PACKAGES)"
echo "  - npm cache:           $(format_bytes $NPM_CACHE)"
echo "  - huggingface cache:   $(format_bytes $HUGGINGFACE_CACHE)"
echo "  - torch cache:         $(format_bytes $TORCH_CACHE)"

TOTAL=$((PIP_CACHE + NPM_CACHE + HUGGINGFACE_CACHE + TORCH_CACHE))
echo -e "\n  ${YELLOW}Potential savings (excluding site-packages): $(format_bytes $TOTAL)${NC}"

if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "\n${YELLOW}Dry run complete. Run without --dry-run to clean.${NC}"
    exit 0
fi

# Confirm before cleaning
echo -e "\n${YELLOW}This will clean caches and free disk space.${NC}"
read -p "Proceed with cleanup? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo -e "\n${GREEN}=== Cleaning ===${NC}"

# Clean pip cache
echo -e "\n${BLUE}Cleaning pip cache...${NC}"
rm -rf ~/.local/share/pip/cache/* 2>/dev/null || true
pip cache purge 2>/dev/null || true
echo "  Done."

# Clean npm cache
echo -e "\n${BLUE}Cleaning npm cache...${NC}"
rm -rf ~/.npm/_cacache 2>/dev/null || true
npm cache clean --force 2>/dev/null || true
echo "  Done."

# Clean HuggingFace cache (be careful - may need to redownload models)
echo -e "\n${BLUE}Cleaning HuggingFace cache...${NC}"
rm -rf ~/.cache/huggingface/hub/* 2>/dev/null || true
echo "  Done."

# Clean PyTorch cache
echo -e "\n${BLUE}Cleaning PyTorch cache...${NC}"
rm -rf ~/.cache/torch 2>/dev/null || true
echo "  Done."

# Clean __pycache__ directories
echo -e "\n${BLUE}Cleaning Python bytecode cache...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo "  Done."

# Clean temporary files
echo -e "\n${BLUE}Cleaning temporary files...${NC}"
rm -rf /tmp/pip-* 2>/dev/null || true
rm -rf ~/.local/tmp/* 2>/dev/null || true
echo "  Done."

# Show final disk usage
echo -e "\n${GREEN}=== Cleanup Complete ===${NC}"
echo -e "\n${BLUE}Final Disk Usage:${NC}"
df -h /home 2>/dev/null || df -h .

echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}  Additional Commands for More Space:${NC}"
echo -e "${GREEN}============================================${NC}"

echo -e "
${YELLOW}If you need more space, consider:${NC}

# Remove old Python environments:
rm -rf ~/.local/lib/python*/site-packages/*

# Remove entire .local directory (WARNING: reinstall needed):
rm -rf ~/.local

# Remove conda/miniconda if installed:
rm -rf ~/miniconda3 ~/anaconda3

# Check for large files:
find ~ -type f -size +100M 2>/dev/null | head -20

# Remove specific large packages:
pip uninstall torch torchvision torchaudio  # Reinstall as needed
"

echo -e "\n${GREEN}Done!${NC}"
