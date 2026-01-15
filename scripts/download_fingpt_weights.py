#!/usr/bin/env python3
"""
FinGPT LoRA Weights Downloader

Downloads pre-trained FinGPT LoRA adapter weights from HuggingFace
for financial sentiment analysis.

Usage:
    python scripts/download_fingpt_weights.py
    python scripts/download_fingpt_weights.py --model sentiment
    python scripts/download_fingpt_weights.py --model forecaster --quantize 4bit
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FinGPT Model Registry
FINGPT_MODELS = {
    "sentiment": {
        "base_model": "meta-llama/Llama-2-7b-hf",
        "lora_weights": "FinGPT/fingpt-sentiment_llama2-7b_lora",
        "description": "Financial sentiment analysis (positive/negative/neutral)",
        "recommended_quantization": "8bit",
        "memory_8bit": "~8GB",
        "memory_4bit": "~5GB",
    },
    "sentiment-13b": {
        "base_model": "meta-llama/Llama-2-13b-hf",
        "lora_weights": "FinGPT/fingpt-sentiment_llama2-13b_lora",
        "description": "Financial sentiment analysis (larger, more accurate)",
        "recommended_quantization": "4bit",
        "memory_8bit": "~14GB",
        "memory_4bit": "~8GB",
    },
    "forecaster": {
        "base_model": "meta-llama/Llama-2-7b-hf",
        "lora_weights": "FinGPT/fingpt-forecaster_dowjones_llama2-7b_lora",
        "description": "Stock movement forecasting based on news",
        "recommended_quantization": "8bit",
        "memory_8bit": "~8GB",
        "memory_4bit": "~5GB",
    },
    "headline": {
        "base_model": "meta-llama/Llama-2-7b-hf",
        "lora_weights": "FinGPT/fingpt-headline_llama2-7b_lora",
        "description": "Financial headline classification",
        "recommended_quantization": "8bit",
        "memory_8bit": "~8GB",
        "memory_4bit": "~5GB",
    },
}

# Alternative smaller models (no Llama license required)
FINGPT_ALTERNATIVE_MODELS = {
    "sentiment-bloom": {
        "base_model": "bigscience/bloom-7b1",
        "lora_weights": "FinGPT/fingpt-sentiment_bloom-7b1_lora",
        "description": "Financial sentiment (BLOOM base, no license needed)",
        "recommended_quantization": "8bit",
        "memory_8bit": "~8GB",
        "memory_4bit": "~5GB",
    },
    "sentiment-falcon": {
        "base_model": "tiiuae/falcon-7b",
        "lora_weights": "FinGPT/fingpt-sentiment_falcon-7b_lora",
        "description": "Financial sentiment (Falcon base, Apache 2.0)",
        "recommended_quantization": "8bit",
        "memory_8bit": "~8GB",
        "memory_4bit": "~5GB",
    },
}


def check_dependencies():
    """Check if required dependencies are installed."""
    missing = []

    try:
        import torch
        logger.info(f"PyTorch version: {torch.__version__}")
        if torch.cuda.is_available():
            logger.info(f"CUDA available: {torch.cuda.get_device_name(0)}")
            logger.info(f"CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
        else:
            logger.warning("CUDA not available - will use CPU (slow)")
    except ImportError:
        missing.append("torch")

    try:
        import transformers
        logger.info(f"Transformers version: {transformers.__version__}")
    except ImportError:
        missing.append("transformers")

    try:
        from peft import PeftModel
        logger.info("PEFT library available")
    except ImportError:
        missing.append("peft")

    try:
        import bitsandbytes
        logger.info("BitsAndBytes available for quantization")
    except ImportError:
        missing.append("bitsandbytes")

    if missing:
        logger.error(f"Missing dependencies: {missing}")
        logger.error("Install with: pip install " + " ".join(missing))
        return False

    return True


def download_model(model_name: str, cache_dir: str = None, quantization: str = "8bit"):
    """
    Download FinGPT LoRA weights and base model.

    Args:
        model_name: Name of the model from FINGPT_MODELS
        cache_dir: Directory to cache model weights
        quantization: Quantization mode ('8bit', '4bit', or 'none')
    """
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    from peft import PeftModel
    import torch

    # Check if model exists
    all_models = {**FINGPT_MODELS, **FINGPT_ALTERNATIVE_MODELS}
    if model_name not in all_models:
        logger.error(f"Unknown model: {model_name}")
        logger.info(f"Available models: {list(all_models.keys())}")
        return False

    model_config = all_models[model_name]
    base_model_name = model_config["base_model"]
    lora_weights = model_config["lora_weights"]

    logger.info(f"Downloading FinGPT model: {model_name}")
    logger.info(f"  Base model: {base_model_name}")
    logger.info(f"  LoRA weights: {lora_weights}")
    logger.info(f"  Quantization: {quantization}")

    # Set up cache directory
    if cache_dir is None:
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")

    os.makedirs(cache_dir, exist_ok=True)

    try:
        # Configure quantization
        quantization_config = None
        if quantization == "4bit":
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True
            )
            logger.info("Using 4-bit quantization (NF4)")
        elif quantization == "8bit":
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=True
            )
            logger.info("Using 8-bit quantization")
        else:
            logger.info("No quantization - full precision")

        # Download tokenizer
        logger.info("Downloading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            base_model_name,
            cache_dir=cache_dir,
            trust_remote_code=True
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        logger.info("Tokenizer downloaded successfully")

        # Download base model
        logger.info("Downloading base model (this may take a while)...")
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            quantization_config=quantization_config,
            device_map="auto",
            cache_dir=cache_dir,
            trust_remote_code=True,
            torch_dtype=torch.float16
        )
        logger.info("Base model downloaded successfully")

        # Download LoRA weights
        logger.info("Downloading FinGPT LoRA adapter weights...")
        model = PeftModel.from_pretrained(
            base_model,
            lora_weights,
            torch_dtype=torch.float16
        )
        logger.info("LoRA weights downloaded successfully")

        # Verify model works
        logger.info("Verifying model with test inference...")
        test_prompt = "Instruction: What is the sentiment of this news? Please choose an answer from {negative/neutral/positive}.\nInput: Apple reports record Q4 revenue.\nAnswer: "

        inputs = tokenizer(test_prompt, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=10,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id
            )

        response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        logger.info(f"Test inference result: '{response.strip()}'")

        logger.info(f"\n{'='*60}")
        logger.info(f"FinGPT model '{model_name}' downloaded successfully!")
        logger.info(f"{'='*60}")

        return True

    except Exception as e:
        logger.error(f"Error downloading model: {str(e)}")
        return False


def list_models():
    """List all available FinGPT models."""
    print("\n" + "="*70)
    print("Available FinGPT Models")
    print("="*70)

    print("\n--- Llama-2 Based Models (require Meta license) ---\n")
    for name, config in FINGPT_MODELS.items():
        print(f"  {name}:")
        print(f"    Description: {config['description']}")
        print(f"    Base Model: {config['base_model']}")
        print(f"    LoRA Weights: {config['lora_weights']}")
        print(f"    Memory (8-bit): {config['memory_8bit']}")
        print(f"    Memory (4-bit): {config['memory_4bit']}")
        print()

    print("\n--- Alternative Models (no special license required) ---\n")
    for name, config in FINGPT_ALTERNATIVE_MODELS.items():
        print(f"  {name}:")
        print(f"    Description: {config['description']}")
        print(f"    Base Model: {config['base_model']}")
        print(f"    LoRA Weights: {config['lora_weights']}")
        print(f"    Memory (8-bit): {config['memory_8bit']}")
        print(f"    Memory (4-bit): {config['memory_4bit']}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Download FinGPT LoRA weights for financial sentiment analysis"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="sentiment",
        help="Model to download (default: sentiment)"
    )
    parser.add_argument(
        "--quantize", "-q",
        type=str,
        choices=["8bit", "4bit", "none"],
        default="8bit",
        help="Quantization mode (default: 8bit)"
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default=None,
        help="Directory to cache model weights"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available models"
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check dependencies only"
    )

    args = parser.parse_args()

    if args.list:
        list_models()
        return

    if args.check_deps:
        if check_dependencies():
            logger.info("All dependencies are installed!")
        return

    # Check dependencies first
    if not check_dependencies():
        logger.error("Please install missing dependencies first")
        sys.exit(1)

    # Download the model
    success = download_model(
        model_name=args.model,
        cache_dir=args.cache_dir,
        quantization=args.quantize
    )

    if success:
        print("\n" + "="*60)
        print("Next Steps:")
        print("="*60)
        print("""
1. Use the FinGPT sentiment analyzer in your code:

   from app.trading_engine.ml_models.ai_model_engine import FinGPTSentimentAnalyzer

   analyzer = FinGPTSentimentAnalyzer(load_in_8bit=True)
   results = analyzer.analyze_financial_text([
       "Apple reports record Q4 revenue beating expectations",
       "Tesla faces regulatory scrutiny over autopilot claims"
   ])
   print(results)

2. Run the benchmark to compare with DistilBERT:

   python scripts/benchmark_sentiment.py
""")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
