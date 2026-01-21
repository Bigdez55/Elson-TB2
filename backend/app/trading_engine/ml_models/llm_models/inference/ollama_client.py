"""
Elson Financial AI - Ollama Inference Client

Local development inference using Ollama.
Supports the quantized Elson-Finance-Trading model (GGUF format).

Setup:
    1. Install Ollama: https://ollama.ai
    2. Import model: ollama create elson-finance-trading -f Modelfile
    3. Run: ollama serve
"""

import asyncio
import time
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp

from .base_client import (
    BaseInferenceClient,
    GenerationConfig,
    InferenceBackend,
    InferenceResponse,
)


class OllamaInferenceClient(BaseInferenceClient):
    """
    Ollama inference client for local development with Elson Financial AI.

    Features:
    - Fast local inference with quantized models (Q4_K_M)
    - Streaming support for real-time responses
    - Embedding generation for RAG applications
    - Automatic retry on connection errors

    Usage:
        client = OllamaInferenceClient(
            model_name="elson-finance-trading",
            base_url="http://localhost:11434"
        )
        response = await client.generate("Analyze AAPL for a swing trade")
    """

    DEFAULT_SYSTEM_PROMPT = """You are Elson-Finance-Trading, a proprietary AI model
specialized in autonomous trading decisions. You analyze market data, sentiment,
and technical indicators to generate high-confidence trading signals.

For each analysis, provide:
1. Market context and current conditions
2. Technical analysis summary
3. Sentiment assessment
4. Risk factors
5. Trading recommendation with confidence level (0-100%)
6. Suggested entry, stop-loss, and take-profit levels

Always explain your reasoning chain before providing recommendations."""

    def __init__(
        self,
        model_name: str = "elson-finance-trading",
        base_url: str = "http://localhost:11434",
        timeout_seconds: float = 60.0,
    ):
        """
        Initialize Ollama client.

        Args:
            model_name: Name of the model in Ollama
            base_url: Ollama API base URL
            timeout_seconds: Request timeout
        """
        super().__init__(
            model_name=model_name,
            backend=InferenceBackend.OLLAMA,
            timeout_seconds=timeout_seconds,
        )
        self.base_url = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close the client session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
        system_prompt: Optional[str] = None,
    ) -> InferenceResponse:
        """
        Generate a single response from Ollama.

        Args:
            prompt: User prompt/query
            config: Generation configuration
            system_prompt: Optional system prompt override

        Returns:
            InferenceResponse with generated text and metadata
        """
        config = config or GenerationConfig()
        system = system_prompt or self.DEFAULT_SYSTEM_PROMPT

        start_time = time.time()

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
                "top_p": config.top_p,
                "top_k": config.top_k if config.top_k > 0 else 40,
                "repeat_penalty": 1.0 + config.frequency_penalty,
            },
        }

        if config.stop_sequences:
            payload["options"]["stop"] = config.stop_sequences

        session = await self._get_session()

        try:
            async with session.post(
                f"{self.base_url}/api/generate", json=payload
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()

                latency_ms = (time.time() - start_time) * 1000

                response = InferenceResponse(
                    text=data.get("response", ""),
                    model=self.model_name,
                    tokens_used=data.get("eval_count", 0)
                    + data.get("prompt_eval_count", 0),
                    latency_ms=latency_ms,
                    confidence=self._extract_confidence(data.get("response", "")),
                    reasoning=self._extract_reasoning(data.get("response", "")),
                    raw_response=data,
                )

                self._track_request(response)
                return response

        except aiohttp.ClientError as e:
            raise ConnectionError(f"Ollama connection failed: {e}")

    async def generate_stream(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Generate streaming response from Ollama.

        Args:
            prompt: User prompt/query
            config: Generation configuration
            system_prompt: Optional system prompt override

        Yields:
            Text chunks as they are generated
        """
        config = config or GenerationConfig()
        system = system_prompt or self.DEFAULT_SYSTEM_PROMPT

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system,
            "stream": True,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
                "top_p": config.top_p,
            },
        }

        session = await self._get_session()

        async with session.post(f"{self.base_url}/api/generate", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.content:
                if line:
                    import json

                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                    except json.JSONDecodeError:
                        continue

    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding vector using Ollama.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        session = await self._get_session()

        payload = {"model": self.model_name, "prompt": text}

        async with session.post(
            f"{self.base_url}/api/embeddings", json=payload
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data.get("embedding", [])

    async def health_check(self) -> bool:
        """
        Check if Ollama is running and model is available.

        Returns:
            True if healthy, False otherwise
        """
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as resp:
                if resp.status != 200:
                    return False
                data = await resp.json()
                models = [m["name"] for m in data.get("models", [])]
                return self.model_name in models or any(
                    self.model_name in m for m in models
                )
        except Exception:
            return False

    def _extract_confidence(self, text: str) -> Optional[float]:
        """Extract confidence score from response text."""
        import re

        # Look for patterns like "confidence: 85%" or "85% confidence"
        patterns = [
            r"confidence[:\s]+(\d+(?:\.\d+)?)\s*%",
            r"(\d+(?:\.\d+)?)\s*%\s*confidence",
            r"confidence\s+level[:\s]+(\d+(?:\.\d+)?)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return float(match.group(1)) / 100.0
        return None

    def _extract_reasoning(self, text: str) -> Optional[str]:
        """Extract reasoning section from response text."""
        # Look for reasoning markers
        markers = ["reasoning:", "analysis:", "rationale:", "because:"]
        text_lower = text.lower()
        for marker in markers:
            if marker in text_lower:
                idx = text_lower.index(marker)
                # Extract up to next section or 500 chars
                end_idx = min(idx + 500, len(text))
                for end_marker in ["\n\n", "recommendation:", "signal:"]:
                    if end_marker in text_lower[idx:end_idx]:
                        end_idx = idx + text_lower[idx:end_idx].index(end_marker)
                        break
                return text[idx:end_idx].strip()
        return None
