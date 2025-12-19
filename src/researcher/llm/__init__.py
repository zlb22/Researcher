"""LLM clients for the Researcher system.

This module provides abstractions and implementations for different LLM providers:
- LLMClient: Abstract base class
- Message, ToolCall, LLMResponse: Data models
- AnthropicClient: Anthropic Claude implementation
- OpenAIClient: OpenAI GPT implementation
"""

from researcher.llm.anthropic_client import AnthropicClient
from researcher.llm.base import (
    FunctionCall,
    LLMClient,
    LLMResponse,
    Message,
    ToolCall,
)
from researcher.llm.openai_client import OpenAIClient

__all__ = [
    "LLMClient",
    "Message",
    "ToolCall",
    "FunctionCall",
    "LLMResponse",
    "AnthropicClient",
    "OpenAIClient",
]
