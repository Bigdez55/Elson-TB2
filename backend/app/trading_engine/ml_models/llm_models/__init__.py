"""
Elson Financial AI - LLM Models Module

This module contains the proprietary Elson Financial AI infrastructure:
- Inference clients for local (Ollama) and production (vLLM) deployments
- ElsonFinanceEnsemble for combining LLM with existing ML models
- Prompt templates for trading decisions

The Elson-Finance-Trading-14B model is a proprietary merged model
created using SLERP, TIES, and DARE techniques from:
- DeepSeek-R1-Distill-Qwen-14B (reasoning)
- Qwen2.5-Math-14B-Instruct (quantitative)
- FinGPT (financial domain)
- FinLLaMA (trading strategies)

Copyright (c) 2024 Elson Wealth. All rights reserved.
"""

from .elson_finance_ensemble import ElsonFinanceEnsemble
from .inference.base_client import BaseInferenceClient, InferenceResponse
from .inference.ollama_client import OllamaInferenceClient
from .inference.vllm_client import VLLMInferenceClient
from .prompts.trading_prompts import TradingPromptBuilder

__all__ = [
    "BaseInferenceClient",
    "InferenceResponse",
    "OllamaInferenceClient",
    "VLLMInferenceClient",
    "ElsonFinanceEnsemble",
    "TradingPromptBuilder",
]
