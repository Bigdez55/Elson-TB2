"""
Elson Financial AI - Inference Clients

Provides unified interface for LLM inference across different backends:
- OllamaInferenceClient: Local development with Ollama
- VLLMInferenceClient: Production deployment with vLLM
- VertexAIInferenceClient: GCP native deployment (future)
"""

from .base_client import BaseInferenceClient, InferenceResponse
from .ollama_client import OllamaInferenceClient
from .vllm_client import VLLMInferenceClient

__all__ = [
    "BaseInferenceClient",
    "InferenceResponse",
    "OllamaInferenceClient",
    "VLLMInferenceClient",
]
