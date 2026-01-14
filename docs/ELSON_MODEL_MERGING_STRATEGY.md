# Elson Financial AI - Model Merging Strategy

## Overview

This document describes the creation of **Elson Financial AI**, a proprietary family of large language models owned 100% by Elson Wealth. These models are created by merging leading open-source financial AI models using advanced techniques.

## Ownership & Intellectual Property

The merged model weights are **Elson Wealth's intellectual property**:

- **Not dependent on external AI providers** - No OpenAI, Anthropic, or other API fees
- **Unique combination** - The specific merge recipe creates something that doesn't exist elsewhere
- **Commercially licensable** - Can be licensed to others if desired
- **Self-hosted** - Runs on YOUR infrastructure, YOUR data stays private

All source models have MIT or Apache 2.0 licenses that explicitly permit derivative works for commercial use.

## Model Family

| Model | Purpose | Status |
|-------|---------|--------|
| **Elson-Finance-Trading-14B** | Autonomous trading decisions | In Development |
| **Elson-Finance-Planning** | Wealth management | Future |
| **Elson-Finance-Insurance** | Insurance analysis | Future |
| **Elson-Finance-Tax** | Tax document processing | Future |

## Source Models

### Elson-Finance-Trading-14B

| Model | Purpose | Size | License |
|-------|---------|------|---------|
| DeepSeek-R1-Distill-Qwen-14B | Chain-of-thought reasoning | 14B | MIT |
| Qwen2.5-Math-14B-Instruct | Mathematical/quantitative precision | 14B | Apache 2.0 |
| FinGPT-v3 | Financial sentiment & domain knowledge | 7B | Apache 2.0 |
| FinLLaMA | Trading strategy reasoning | 7B | Apache 2.0 |

## Merging Techniques

### SLERP (Spherical Linear Interpolation)
- Used for Stage 1: Blending exactly 2 models
- Treats weights as points on a high-dimensional sphere
- Preserves unique characteristics of both models

### TIES-Merging
- Used for Stage 2: Merging 3+ models
- **T**rim redundant parameters
- **I**nfer (Elect) dominant sign
- **E**liminate conflicts
- **S**cale and merge

### DARE (Drop And REscale)
- Used for Stage 3: Refinement
- Randomly prunes small weight changes
- Rescales remaining weights
- Reduces noise, sharpens model focus

## Merge Pipeline

```
Stage 1: SLERP
┌────────────────────────────┐     ┌────────────────────────────┐
│ DeepSeek-R1-Distill-14B    │ + │ Qwen2.5-Math-14B-Instruct   │
│ (Reasoning)                │     │ (Quantitative)             │
└────────────────────────────┘     └────────────────────────────┘
                    │
                    ▼
        ┌──────────────────────┐
        │ elson-reason-math-14b │
        │ (Intermediate)        │
        └──────────────────────┘
                    │
Stage 2: TIES      │
                    ▼
        ┌──────────────────────┐
        │ + FinGPT-v3          │
        │ + FinLLaMA           │
        └──────────────────────┘
                    │
                    ▼
        ┌──────────────────────────┐
        │ elson-finance-trading-14b │
        │ (Intermediate)            │
        └──────────────────────────┘
                    │
Stage 3: DARE      │
                    ▼
        ┌────────────────────────────────┐
        │ elson-finance-trading-14b-final │
        │ (Production Model)              │
        └────────────────────────────────┘
```

## Hardware Requirements

### Merging (One-time)
- **GCP VM:** a2-highgpu-1g (A100 40GB)
- **Cost:** ~$15-25 (Spot: ~$10-15)
- **Time:** 2-3 hours total

### Development (Local)
- **Tool:** Ollama with GGUF quantized model
- **RAM:** 16GB+ (32GB recommended)
- **GPU:** Optional for CPU inference

### Production
- **GCP Cloud Run with GPU** or **GKE with vLLM**
- **GPU:** NVIDIA L4 or A100
- **Cost:** ~$0.50/hour (scales to zero)

## Configuration Files

### Stage 1: SLERP (`mergekit_configs/stage1_reasoning.yaml`)
```yaml
merge_method: slerp
base_model: deepseek-ai/DeepSeek-R1-Distill-Qwen-14B
parameters:
  t:
    - filter: self_attn
      value: [0, 0.3, 0.5, 0.7, 1]
    - filter: mlp
      value: 0.4
    - value: 0.5
```

### Stage 2: TIES (`mergekit_configs/stage2_financial.yaml`)
```yaml
merge_method: ties
models:
  - model: ./checkpoints/elson-reason-math-14b
    density: 1.0
    weight: 0.6
  - model: FinGPT/fingpt-mt_llama2-13b_lora
    density: 0.5
    weight: 0.25
  - model: FinGPT/FinLLaMA
    density: 0.5
    weight: 0.15
```

### Stage 3: DARE (`mergekit_configs/stage3_dare.yaml`)
```yaml
merge_method: dare_ties
parameters:
  dare_pruning_rate: 0.2
  normalize: true
  rescale: true
```

## Running the Merge

```bash
# SSH into GCP VM
gcloud compute ssh elson-model-merger --zone=us-central1-a

# Install dependencies
pip install mergekit torch transformers safetensors accelerate

# Run Stage 1
mergekit-yaml mergekit_configs/stage1_reasoning.yaml \
    ./checkpoints/elson-reason-math-14b --cuda

# Run Stage 2
mergekit-yaml mergekit_configs/stage2_financial.yaml \
    ./checkpoints/elson-finance-trading-14b --cuda

# Run Stage 3
mergekit-yaml mergekit_configs/stage3_dare.yaml \
    ./checkpoints/elson-finance-trading-14b-final --cuda

# Upload to GCS
gsutil -m cp -r ./checkpoints/elson-finance-trading-14b-final \
    gs://elson-model-weights/
```

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ElsonFinanceEnsemble                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Elson LLM   │  │ Hybrid ML   │  │ Sentiment   │             │
│  │ (40%)       │  │ (35%)       │  │ (25%)       │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                     │
│         └────────────────┼────────────────┘                     │
│                          │                                      │
│                          ▼                                      │
│              ┌───────────────────────┐                          │
│              │  Weighted Combination  │                          │
│              └───────────┬───────────┘                          │
│                          │                                      │
│                          ▼                                      │
│              ┌───────────────────────┐                          │
│              │   TradingDecision     │                          │
│              │   - action            │                          │
│              │   - confidence        │                          │
│              │   - entry/stop/target │                          │
│              │   - reasoning         │                          │
│              └───────────────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Files Created

```
backend/app/trading_engine/ml_models/llm_models/
├── __init__.py
├── elson_finance_ensemble.py      # Main ensemble class
├── inference/
│   ├── __init__.py
│   ├── base_client.py             # Abstract interface
│   ├── ollama_client.py           # Local development
│   └── vllm_client.py             # Production
└── prompts/
    ├── __init__.py
    └── trading_prompts.py         # Prompt templates

mergekit_configs/
├── stage1_reasoning.yaml          # SLERP config
├── stage2_financial.yaml          # TIES config
└── stage3_dare.yaml               # DARE config
```

## Usage Example

```python
from backend.app.trading_engine.ml_models.llm_models import (
    ElsonFinanceEnsemble,
    OllamaInferenceClient,
    VLLMInferenceClient,
)

# Local development
client = OllamaInferenceClient(model_name="elson-finance-trading")

# Production
client = VLLMInferenceClient(
    model_name="elson-finance-trading",
    base_url="http://elson-llm-inference:8000"
)

# Create ensemble
ensemble = ElsonFinanceEnsemble(llm_client=client)

# Generate trading decision
decision = await ensemble.generate_trading_decision(
    symbol="AAPL",
    market_data=market_df,
    news=headlines
)

print(f"Action: {decision.action.value}")
print(f"Confidence: {decision.confidence:.1%}")
print(f"Reasoning: {decision.reasoning}")
```

## Evaluation Benchmarks

| Metric | Target | Method |
|--------|--------|--------|
| Signal Accuracy | >= 65% | 2-year backtest |
| Latency (P99) | < 2s | Load test |
| Sharpe Ratio | > 1.5 | 30-day paper trade |
| Drawdown Prediction | >= 75% | Historical comparison |

## Future Enhancements

1. **Proprietary Fine-Tuning** - LoRA training on Elson trading data
2. **Model Soup** - Average multiple fine-tuned variants
3. **Continuous Learning** - Re-merge with newer base models
4. **Additional Models** - Planning, Insurance, Tax variants

## References

- [mergekit Documentation](https://github.com/cg123/mergekit)
- [TIES-Merging Paper](https://arxiv.org/abs/2306.01708)
- [DARE Paper](https://arxiv.org/abs/2311.03099)
- [DeepSeek-R1](https://github.com/deepseek-ai/DeepSeek-R1)
- [FinGPT](https://github.com/AI4Finance-Foundation/FinGPT)
