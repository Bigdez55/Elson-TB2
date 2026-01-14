"""
Elson Financial AI - vLLM Inference Client

Production inference using vLLM with OpenAI-compatible API.
Optimized for high-throughput, low-latency model serving.

Deployment:
    1. Deploy vLLM container with Elson model
    2. Configure endpoint URL and API key
    3. Enable auto-scaling based on request queue
"""

import time
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp

from .base_client import (
    BaseInferenceClient,
    GenerationConfig,
    InferenceBackend,
    InferenceResponse,
)


class VLLMInferenceClient(BaseInferenceClient):
    """
    vLLM inference client for production deployment of Elson Financial AI.

    Features:
    - OpenAI-compatible API for easy migration
    - High throughput with continuous batching
    - PagedAttention for efficient memory usage
    - Auto-scaling support on GCP Cloud Run / GKE

    Usage:
        client = VLLMInferenceClient(
            model_name="elson-finance-trading",
            base_url="http://elson-llm-inference:8000",
            api_key="your-api-key"
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
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout_seconds: float = 60.0
    ):
        """
        Initialize vLLM client.

        Args:
            model_name: Name of the model in vLLM
            base_url: vLLM API base URL
            api_key: Optional API key for authentication
            timeout_seconds: Request timeout
        """
        super().__init__(
            model_name=model_name,
            backend=InferenceBackend.VLLM,
            timeout_seconds=timeout_seconds
        )
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with auth headers."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
        return self._session

    async def close(self) -> None:
        """Close the client session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
        system_prompt: Optional[str] = None
    ) -> InferenceResponse:
        """
        Generate a single response from vLLM using OpenAI-compatible API.

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

        # OpenAI-compatible chat completions format
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            "presence_penalty": config.presence_penalty,
            "frequency_penalty": config.frequency_penalty,
            "stream": False
        }

        if config.stop_sequences:
            payload["stop"] = config.stop_sequences

        session = await self._get_session()

        try:
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()

                latency_ms = (time.time() - start_time) * 1000

                # Extract response from OpenAI format
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})
                text = message.get("content", "")

                usage = data.get("usage", {})
                tokens_used = (
                    usage.get("prompt_tokens", 0) +
                    usage.get("completion_tokens", 0)
                )

                response = InferenceResponse(
                    text=text,
                    model=self.model_name,
                    tokens_used=tokens_used,
                    latency_ms=latency_ms,
                    confidence=self._extract_confidence(text),
                    reasoning=self._extract_reasoning(text),
                    raw_response=data
                )

                self._track_request(response)
                return response

        except aiohttp.ClientError as e:
            raise ConnectionError(f"vLLM connection failed: {e}")

    async def generate_stream(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
        system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Generate streaming response from vLLM using SSE.

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
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            "stream": True
        }

        session = await self._get_session()

        async with session.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload
        ) as resp:
            resp.raise_for_status()
            async for line in resp.content:
                if line:
                    line_str = line.decode("utf-8").strip()
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]
                        if data_str == "[DONE]":
                            break
                        import json
                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            continue

    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding vector using vLLM embeddings endpoint.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        session = await self._get_session()

        payload = {
            "model": self.model_name,
            "input": text
        }

        async with session.post(
            f"{self.base_url}/v1/embeddings",
            json=payload
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            embeddings = data.get("data", [{}])
            if embeddings:
                return embeddings[0].get("embedding", [])
            return []

    async def health_check(self) -> bool:
        """
        Check if vLLM is running and model is loaded.

        Returns:
            True if healthy, False otherwise
        """
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/v1/models") as resp:
                if resp.status != 200:
                    return False
                data = await resp.json()
                models = [m.get("id") for m in data.get("data", [])]
                return self.model_name in models or any(
                    self.model_name in str(m) for m in models
                )
        except Exception:
            return False

    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.

        Returns:
            Model metadata including parameters, context length, etc.
        """
        session = await self._get_session()

        async with session.get(f"{self.base_url}/v1/models") as resp:
            resp.raise_for_status()
            data = await resp.json()
            for model in data.get("data", []):
                if self.model_name in str(model.get("id", "")):
                    return model
            return {}

    def _extract_confidence(self, text: str) -> Optional[float]:
        """Extract confidence score from response text."""
        import re
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
        markers = ["reasoning:", "analysis:", "rationale:", "because:"]
        text_lower = text.lower()
        for marker in markers:
            if marker in text_lower:
                idx = text_lower.index(marker)
                end_idx = min(idx + 500, len(text))
                for end_marker in ["\n\n", "recommendation:", "signal:"]:
                    if end_marker in text_lower[idx:end_idx]:
                        end_idx = idx + text_lower[idx:end_idx].index(end_marker)
                        break
                return text[idx:end_idx].strip()
        return None
