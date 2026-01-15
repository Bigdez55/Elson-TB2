"""
Wealth Management Model Loader

Downloads and loads the fine-tuned QDoRA model from GCS for wealth management
advisory services. Supports caching, lazy loading, and multiple deployment modes.

Model: elson-finance-trading-wealth-14b-q4
Location: gs://elson-33a95-elson-models/elson-finance-trading-wealth-14b-q4/

Architecture:
- Base Model: Qwen2.5-14B-Instruct
- Fine-tuning: DVoRA (training) → QDoRA (production, 4-bit quantized)
- Specialization: 70+ professional roles across wealth management domains
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ModelSource(Enum):
    """Model source locations."""
    GCS = "gcs"
    LOCAL = "local"
    HUGGINGFACE = "huggingface"


@dataclass
class ModelConfig:
    """Configuration for wealth management model."""
    model_name: str = "elson-finance-trading-wealth-14b-q4"
    base_model: str = "Qwen/Qwen2.5-14B-Instruct"  # Correct base model for 14B
    gcs_bucket: str = "elson-33a95-elson-models"
    gcs_path: str = "elson-finance-trading-wealth-14b-q4"
    local_cache_dir: str = "~/.cache/elson/wealth-models"
    quantization: str = "4bit"  # 4bit, 8bit, none
    device_map: str = "auto"
    torch_dtype: str = "bfloat16"  # bfloat16 for Qwen models
    max_memory: Optional[Dict[int, str]] = None


# Default GCS model location
DEFAULT_GCS_URI = "gs://elson-33a95-elson-models/elson-finance-trading-wealth-14b-q4"


class WealthModelLoader:
    """
    Loads the fine-tuned QDoRA wealth management model from GCS.

    Supports:
    - Lazy loading (model loaded on first use)
    - Local caching (download once, reuse)
    - Multiple quantization modes (4-bit, 8-bit, full)
    - Automatic device placement
    """

    def __init__(
        self,
        config: Optional[ModelConfig] = None,
        source: ModelSource = ModelSource.GCS
    ):
        self.config = config or ModelConfig()
        self.source = source
        self.model = None
        self.tokenizer = None
        self._loaded = False

        # Expand cache directory
        self.cache_dir = Path(os.path.expanduser(self.config.local_cache_dir))
        self.model_dir = self.cache_dir / self.config.model_name

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._loaded

    @property
    def gcs_uri(self) -> str:
        """Full GCS URI for the model."""
        return f"gs://{self.config.gcs_bucket}/{self.config.gcs_path}"

    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def _check_local_cache(self) -> bool:
        """Check if model is already cached locally."""
        required_files = [
            "adapter_config.json",
            "adapter_model.safetensors",
            "tokenizer.json"
        ]
        return all((self.model_dir / f).exists() for f in required_files)

    def download_from_gcs(self, force: bool = False) -> bool:
        """
        Download model from GCS to local cache.

        Args:
            force: Force re-download even if cached

        Returns:
            True if download successful
        """
        try:
            from google.cloud import storage
        except ImportError:
            logger.warning("google-cloud-storage not installed, trying gsutil")
            return self._download_with_gsutil(force)

        if not force and self._check_local_cache():
            logger.info(f"Model already cached at {self.model_dir}")
            return True

        self._ensure_cache_dir()

        try:
            client = storage.Client()
            bucket = client.bucket(self.config.gcs_bucket)

            # List all blobs in the model path
            blobs = bucket.list_blobs(prefix=self.config.gcs_path)

            downloaded = 0
            for blob in blobs:
                # Get relative path within the model directory
                relative_path = blob.name[len(self.config.gcs_path):].lstrip("/")
                if not relative_path:
                    continue

                local_path = self.model_dir / relative_path
                local_path.parent.mkdir(parents=True, exist_ok=True)

                logger.info(f"Downloading {blob.name} -> {local_path}")
                blob.download_to_filename(str(local_path))
                downloaded += 1

            logger.info(f"Downloaded {downloaded} files from GCS")
            return downloaded > 0

        except Exception as e:
            logger.error(f"GCS download failed: {e}")
            return self._download_with_gsutil(force)

    def _download_with_gsutil(self, force: bool = False) -> bool:
        """Fallback download using gsutil CLI."""
        import subprocess

        if not force and self._check_local_cache():
            logger.info(f"Model already cached at {self.model_dir}")
            return True

        self._ensure_cache_dir()

        try:
            cmd = [
                "gsutil", "-m", "cp", "-r",
                f"{self.gcs_uri}/*",
                str(self.model_dir)
            ]
            logger.info(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode == 0:
                logger.info("gsutil download successful")
                return True
            else:
                logger.error(f"gsutil failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("gsutil download timed out")
            return False
        except FileNotFoundError:
            logger.error("gsutil not found - install Google Cloud SDK")
            return False

    def _create_quantization_config(self):
        """Create BitsAndBytes quantization config."""
        try:
            import torch
            from transformers import BitsAndBytesConfig
        except ImportError:
            logger.error("transformers or torch not installed")
            return None

        if self.config.quantization == "4bit":
            return BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True
            )
        elif self.config.quantization == "8bit":
            return BitsAndBytesConfig(
                load_in_8bit=True
            )
        return None

    def load_model(self, force_download: bool = False):
        """
        Load the QDoRA model for inference.

        Args:
            force_download: Force re-download from GCS

        Returns:
            Tuple of (model, tokenizer)
        """
        if self._loaded:
            return self.model, self.tokenizer

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from peft import PeftModel
        except ImportError as e:
            raise ImportError(
                f"Required packages not installed: {e}. "
                "Install with: pip install torch transformers peft bitsandbytes"
            )

        # Download from GCS if needed
        if self.source == ModelSource.GCS:
            if not self.download_from_gcs(force=force_download):
                raise RuntimeError("Failed to download model from GCS")

        adapter_path = str(self.model_dir)

        logger.info(f"Loading base model: {self.config.base_model}")
        logger.info(f"Quantization: {self.config.quantization}")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            adapter_path,
            trust_remote_code=True
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load base model with quantization
        quant_config = self._create_quantization_config()

        torch_dtype = getattr(torch, self.config.torch_dtype, torch.float16)

        base_model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model,
            quantization_config=quant_config,
            device_map=self.config.device_map,
            torch_dtype=torch_dtype,
            trust_remote_code=True,
            max_memory=self.config.max_memory
        )

        # Load PEFT adapter
        logger.info(f"Loading QDoRA adapter from: {adapter_path}")
        self.model = PeftModel.from_pretrained(
            base_model,
            adapter_path,
            torch_dtype=torch_dtype
        )

        # Set to eval mode
        self.model.eval()
        self._loaded = True

        logger.info("Wealth management model loaded successfully")
        return self.model, self.tokenizer

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        do_sample: bool = True,
        **kwargs
    ) -> str:
        """
        Generate a response from the model.

        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            do_sample: Whether to use sampling

        Returns:
            Generated text response
        """
        import torch

        if not self._loaded:
            self.load_model()

        inputs = self.tokenizer(prompt, return_tensors="pt")

        # Move to same device as model
        device = next(self.model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                **kwargs
            )

        # Decode only new tokens
        response = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )

        return response.strip()

    def unload(self):
        """Unload model from memory."""
        import gc

        if self.model is not None:
            del self.model
            self.model = None

        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None

        self._loaded = False
        gc.collect()

        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

        logger.info("Model unloaded from memory")


def create_wealth_model_loader(
    quantization: str = "4bit",
    cache_dir: Optional[str] = None
) -> WealthModelLoader:
    """
    Factory function to create a wealth model loader.

    Args:
        quantization: Quantization mode (4bit, 8bit, none)
        cache_dir: Local cache directory

    Returns:
        Configured WealthModelLoader instance
    """
    config = ModelConfig(
        quantization=quantization,
        local_cache_dir=cache_dir or "~/.cache/elson/wealth-models"
    )
    return WealthModelLoader(config=config, source=ModelSource.GCS)


# Quick access functions
def load_wealth_model(quantization: str = "4bit"):
    """Load and return the wealth management model."""
    loader = create_wealth_model_loader(quantization=quantization)
    return loader.load_model()


def get_wealth_model_info() -> Dict[str, Any]:
    """Get information about the wealth management model."""
    return {
        "name": "ELSON Wealth Management QDoRA",
        "base_model": "Qwen/Qwen2.5-14B-Instruct",
        "adapter_type": "QDoRA (DVoRA-trained, 4-bit quantized)",
        "gcs_location": DEFAULT_GCS_URI,
        "trainable_params": "~0.15%",
        "adapter_size": "~500MB",
        "supported_quantization": ["4bit", "8bit", "none"],
        "recommended_vram": {
            "4bit": "~12GB",
            "8bit": "~18GB",
            "none": "~28GB"
        },
        "specialization": "70+ professional roles across wealth management domains"
    }
