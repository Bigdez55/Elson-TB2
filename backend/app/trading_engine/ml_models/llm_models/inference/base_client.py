"""
Elson Financial AI - Base Inference Client

Abstract interface for LLM inference backends.
All inference clients (Ollama, vLLM, Vertex AI) implement this interface.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional


class InferenceBackend(Enum):
    """Supported inference backends for Elson Financial AI."""

    OLLAMA = "ollama"  # Local development
    VLLM = "vllm"  # Production (self-hosted)
    VERTEX_AI = "vertex"  # GCP native (future)


@dataclass
class InferenceResponse:
    """
    Standardized response from Elson Financial AI inference.

    Attributes:
        text: The generated text response
        model: Model identifier used for inference
        tokens_used: Total tokens consumed (prompt + completion)
        latency_ms: Time taken for inference in milliseconds
        confidence: Optional confidence score (0-1) extracted from response
        reasoning: Optional chain-of-thought reasoning
        raw_response: Original response from backend for debugging
    """

    text: str
    model: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    raw_response: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "text": self.text,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


@dataclass
class GenerationConfig:
    """
    Configuration for text generation.

    Attributes:
        temperature: Controls randomness (0=deterministic, 1=creative)
        max_tokens: Maximum tokens to generate
        top_p: Nucleus sampling threshold
        top_k: Top-k sampling (0=disabled)
        stop_sequences: Strings that stop generation
        presence_penalty: Penalty for token presence
        frequency_penalty: Penalty for token frequency
    """

    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    top_k: int = 0
    stop_sequences: List[str] = field(default_factory=list)
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0


class BaseInferenceClient(ABC):
    """
    Abstract base class for Elson Financial AI inference clients.

    Implementations must provide:
    - generate(): Single response generation
    - generate_stream(): Streaming response generation
    - embed(): Text embedding (for RAG applications)
    - health_check(): Backend health verification
    """

    def __init__(
        self, model_name: str, backend: InferenceBackend, timeout_seconds: float = 60.0
    ):
        """
        Initialize inference client.

        Args:
            model_name: Name of the Elson Financial AI model to use
            backend: Inference backend type
            timeout_seconds: Request timeout
        """
        self.model_name = model_name
        self.backend = backend
        self.timeout_seconds = timeout_seconds
        self._request_count = 0
        self._total_tokens = 0
        self._total_latency_ms = 0.0

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
        system_prompt: Optional[str] = None,
    ) -> InferenceResponse:
        """
        Generate a single response from the model.

        Args:
            prompt: User prompt/query
            config: Generation configuration
            system_prompt: Optional system prompt override

        Returns:
            InferenceResponse with generated text and metadata
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Generate streaming response from the model.

        Args:
            prompt: User prompt/query
            config: Generation configuration
            system_prompt: Optional system prompt override

        Yields:
            Text chunks as they are generated
        """
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the inference backend is healthy.

        Returns:
            True if backend is responding, False otherwise
        """
        pass

    def get_stats(self) -> Dict[str, Any]:
        """
        Get client usage statistics.

        Returns:
            Dictionary with request count, total tokens, average latency
        """
        avg_latency = (
            self._total_latency_ms / self._request_count
            if self._request_count > 0
            else 0.0
        )
        return {
            "model": self.model_name,
            "backend": self.backend.value,
            "request_count": self._request_count,
            "total_tokens": self._total_tokens,
            "average_latency_ms": avg_latency,
        }

    def _track_request(self, response: InferenceResponse) -> None:
        """Track request statistics."""
        self._request_count += 1
        self._total_tokens += response.tokens_used
        self._total_latency_ms += response.latency_ms


class InferenceClientFactory:
    """
    Factory for creating inference clients based on configuration.

    Usage:
        client = InferenceClientFactory.create(
            backend="vllm",
            model_name="elson-finance-trading",
            endpoint="http://localhost:8000"
        )
    """

    @staticmethod
    def create(
        backend: str, model_name: str = "elson-finance-trading", **kwargs
    ) -> BaseInferenceClient:
        """
        Create an inference client for the specified backend.

        Args:
            backend: Backend type ("ollama", "vllm", "vertex")
            model_name: Elson Financial AI model name
            **kwargs: Backend-specific configuration

        Returns:
            Configured inference client

        Raises:
            ValueError: If backend is not supported
        """
        from .ollama_client import OllamaInferenceClient
        from .vllm_client import VLLMInferenceClient

        backend_enum = InferenceBackend(backend.lower())

        if backend_enum == InferenceBackend.OLLAMA:
            return OllamaInferenceClient(
                model_name=model_name,
                base_url=kwargs.get("endpoint", "http://localhost:11434"),
                timeout_seconds=kwargs.get("timeout", 60.0),
            )
        elif backend_enum == InferenceBackend.VLLM:
            return VLLMInferenceClient(
                model_name=model_name,
                base_url=kwargs.get("endpoint", "http://localhost:8000"),
                api_key=kwargs.get("api_key"),
                timeout_seconds=kwargs.get("timeout", 60.0),
            )
        elif backend_enum == InferenceBackend.VERTEX_AI:
            raise NotImplementedError("Vertex AI client coming soon")
        else:
            raise ValueError(f"Unsupported backend: {backend}")
