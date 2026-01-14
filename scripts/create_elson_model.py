#!/usr/bin/env python3
"""
Elson Financial AI - Model Creation Script (Python Version)

Alternative to the bash script for those who prefer Python.
Can be run locally or in a Jupyter notebook.

Usage:
    python scripts/create_elson_model.py --hf-token YOUR_TOKEN

Or in Python:
    from scripts.create_elson_model import ElsonModelCreator
    creator = ElsonModelCreator(hf_token="your_token")
    creator.run_full_pipeline()

Copyright (c) 2024 Elson Wealth. All rights reserved.
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ElsonModelCreator:
    """
    Creates the proprietary Elson-Finance-Trading-14B model.

    This class orchestrates the 3-stage merge pipeline:
    1. SLERP: DeepSeek-R1 + Qwen2.5-Math → reasoning+math foundation
    2. TIES: + FinGPT + FinLLaMA → financial domain injection
    3. DARE: Prune noise, sharpen focus → production model
    """

    # Base models to merge
    BASE_MODELS = {
        "reasoning": "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
        "math": "Qwen/Qwen2.5-Math-14B-Instruct",
        "sentiment": "FinGPT/fingpt-mt_llama2-13b_lora",
        "trading": "FinGPT/FinLLaMA",
    }

    def __init__(
        self,
        hf_token: Optional[str] = None,
        output_dir: str = "./checkpoints",
        use_gpu: bool = True
    ):
        """
        Initialize model creator.

        Args:
            hf_token: HuggingFace token for model downloads
            output_dir: Directory for model checkpoints
            use_gpu: Whether to use GPU acceleration
        """
        self.hf_token = hf_token or os.environ.get("HF_TOKEN")
        self.output_dir = Path(output_dir)
        self.use_gpu = use_gpu

        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not self.hf_token:
            raise ValueError(
                "HuggingFace token required. Set HF_TOKEN env var or pass hf_token param.\n"
                "Get your token from: https://huggingface.co/settings/tokens"
            )

    def check_dependencies(self) -> bool:
        """Check if required packages are installed."""
        required = ["mergekit", "torch", "transformers", "safetensors"]
        missing = []

        for pkg in required:
            try:
                __import__(pkg.replace("-", "_"))
            except ImportError:
                missing.append(pkg)

        if missing:
            logger.warning(f"Missing packages: {missing}")
            logger.info("Installing missing packages...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-q"
            ] + missing, check=True)

        return True

    def login_huggingface(self) -> None:
        """Login to HuggingFace Hub."""
        from huggingface_hub import login
        login(token=self.hf_token)
        logger.info("Logged into HuggingFace Hub")

    def run_stage1_slerp(self) -> Path:
        """
        Stage 1: SLERP merge of DeepSeek-R1 + Qwen2.5-Math.
        Creates reasoning + mathematical foundation.
        """
        logger.info("=" * 60)
        logger.info("STAGE 1: SLERP (Reasoning + Math Foundation)")
        logger.info("=" * 60)

        output_path = self.output_dir / "elson-reason-math-14b"

        if output_path.exists():
            logger.info(f"Stage 1 checkpoint exists: {output_path}")
            return output_path

        # Create config
        config = f"""
slices:
  - sources:
      - model: {self.BASE_MODELS['reasoning']}
        layer_range: [0, 48]
      - model: {self.BASE_MODELS['math']}
        layer_range: [0, 48]
merge_method: slerp
base_model: {self.BASE_MODELS['reasoning']}
parameters:
  t:
    - filter: self_attn
      value: [0, 0.3, 0.5, 0.7, 1]
    - filter: mlp
      value: 0.4
    - value: 0.5
dtype: bfloat16
"""

        config_path = self.output_dir / "stage1_config.yaml"
        config_path.write_text(config)

        # Run merge
        cmd = [
            "mergekit-yaml",
            str(config_path),
            str(output_path),
            "--low-cpu-memory"
        ]
        if self.use_gpu:
            cmd.append("--cuda")

        logger.info(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

        logger.info(f"Stage 1 complete: {output_path}")
        return output_path

    def run_stage2_ties(self, stage1_path: Path) -> Path:
        """
        Stage 2: TIES merge to add financial domain knowledge.
        Adds FinGPT sentiment and FinLLaMA trading capabilities.
        """
        logger.info("=" * 60)
        logger.info("STAGE 2: TIES (Financial Domain Injection)")
        logger.info("=" * 60)

        output_path = self.output_dir / "elson-finance-trading-14b"

        if output_path.exists():
            logger.info(f"Stage 2 checkpoint exists: {output_path}")
            return output_path

        # Create config
        config = f"""
models:
  - model: {stage1_path}
    parameters:
      density: 1.0
      weight: 0.6
  - model: {self.BASE_MODELS['sentiment']}
    parameters:
      density: 0.5
      weight: 0.25
  - model: {self.BASE_MODELS['trading']}
    parameters:
      density: 0.5
      weight: 0.15
merge_method: ties
base_model: {stage1_path}
parameters:
  normalize: true
dtype: bfloat16
"""

        config_path = self.output_dir / "stage2_config.yaml"
        config_path.write_text(config)

        # Run merge
        cmd = [
            "mergekit-yaml",
            str(config_path),
            str(output_path),
            "--low-cpu-memory"
        ]
        if self.use_gpu:
            cmd.append("--cuda")

        logger.info(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

        logger.info(f"Stage 2 complete: {output_path}")
        return output_path

    def run_stage3_dare(self, stage2_path: Path) -> Path:
        """
        Stage 3: DARE refinement to prune noise and sharpen focus.
        Creates the final production model.
        """
        logger.info("=" * 60)
        logger.info("STAGE 3: DARE (Refinement)")
        logger.info("=" * 60)

        output_path = self.output_dir / "elson-finance-trading-14b-final"

        if output_path.exists():
            logger.info(f"Stage 3 checkpoint exists: {output_path}")
            return output_path

        # Create config
        config = f"""
models:
  - model: {stage2_path}
    parameters:
      weight: 1.0
merge_method: dare_ties
base_model: {stage2_path}
parameters:
  dare_pruning_rate: 0.2
  normalize: true
  rescale: true
dtype: bfloat16
"""

        config_path = self.output_dir / "stage3_config.yaml"
        config_path.write_text(config)

        # Run merge
        cmd = [
            "mergekit-yaml",
            str(config_path),
            str(output_path),
            "--low-cpu-memory"
        ]
        if self.use_gpu:
            cmd.append("--cuda")

        logger.info(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

        logger.info(f"Stage 3 complete: {output_path}")
        return output_path

    def run_full_pipeline(self) -> Path:
        """
        Run the complete 3-stage merge pipeline.

        Returns:
            Path to the final model
        """
        logger.info("╔" + "═" * 58 + "╗")
        logger.info("║" + " ELSON FINANCIAL AI - MODEL CREATION PIPELINE ".center(58) + "║")
        logger.info("╚" + "═" * 58 + "╝")

        # Check dependencies
        self.check_dependencies()

        # Login to HuggingFace
        self.login_huggingface()

        # Run pipeline
        stage1_output = self.run_stage1_slerp()
        stage2_output = self.run_stage2_ties(stage1_output)
        final_output = self.run_stage3_dare(stage2_output)

        logger.info("")
        logger.info("╔" + "═" * 58 + "╗")
        logger.info("║" + " MODEL CREATION COMPLETE ".center(58) + "║")
        logger.info("╠" + "═" * 58 + "╣")
        logger.info("║" + f" Final model: {final_output}".ljust(58) + "║")
        logger.info("║" + " ".ljust(58) + "║")
        logger.info("║" + " This model is 100% owned by Elson Wealth.".ljust(58) + "║")
        logger.info("╚" + "═" * 58 + "╝")

        return final_output

    def convert_to_gguf(self, model_path: Path, quantization: str = "Q4_K_M") -> Path:
        """
        Convert model to GGUF format for Ollama.

        Args:
            model_path: Path to the model
            quantization: Quantization type (Q4_K_M, Q5_K_M, Q8_0, etc.)

        Returns:
            Path to GGUF file
        """
        output_path = model_path.parent / f"{model_path.name}-{quantization}.gguf"

        logger.info(f"Converting to GGUF ({quantization})...")

        # This requires llama.cpp's convert script
        # For now, just log instructions
        logger.info(f"""
To convert to GGUF for Ollama:

1. Clone llama.cpp:
   git clone https://github.com/ggerganov/llama.cpp

2. Convert to GGUF:
   python llama.cpp/convert.py {model_path} --outfile {output_path} --outtype {quantization.lower()}

3. Create Ollama Modelfile:
   echo 'FROM {output_path}' > Modelfile
   echo 'PARAMETER temperature 0.7' >> Modelfile
   echo 'SYSTEM "You are Elson-Finance-Trading..."' >> Modelfile

4. Import to Ollama:
   ollama create elson-finance-trading -f Modelfile
""")

        return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Create Elson Financial AI proprietary model"
    )
    parser.add_argument(
        "--hf-token",
        type=str,
        help="HuggingFace token (or set HF_TOKEN env var)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./checkpoints",
        help="Output directory for model checkpoints"
    )
    parser.add_argument(
        "--no-gpu",
        action="store_true",
        help="Disable GPU acceleration (slower but works on CPU)"
    )
    parser.add_argument(
        "--stage",
        type=int,
        choices=[1, 2, 3],
        help="Run only a specific stage (for resuming)"
    )

    args = parser.parse_args()

    creator = ElsonModelCreator(
        hf_token=args.hf_token,
        output_dir=args.output_dir,
        use_gpu=not args.no_gpu
    )

    if args.stage:
        # Run specific stage
        if args.stage == 1:
            creator.run_stage1_slerp()
        elif args.stage == 2:
            stage1 = Path(args.output_dir) / "elson-reason-math-14b"
            creator.run_stage2_ties(stage1)
        elif args.stage == 3:
            stage2 = Path(args.output_dir) / "elson-finance-trading-14b"
            creator.run_stage3_dare(stage2)
    else:
        # Run full pipeline
        creator.run_full_pipeline()


if __name__ == "__main__":
    main()
