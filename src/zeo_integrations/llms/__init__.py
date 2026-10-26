"""
LLM integration for zeo_core.

This module provides a lightweight integration with Large Language Models (LLMs),
offering a standardized interface for making chat completions across different
LLM providers.
"""

from zeo_core.integrations.core.protocols import IntegrationProtocol

from zeo_integrations.llms.clients import (
    LLMClient,
    MockLLMClient,
)
from zeo_integrations.llms.clients.anthropic import AnthropicClient
from zeo_integrations.llms.clients.ollama import OllamaClient
from zeo_integrations.llms.clients.openai import OpenAIClient
from zeo_integrations.llms.config import LLMConfig, LLMConfigProvider
from zeo_integrations.llms.execution import llm_chat_target
from zeo_integrations.llms.fallback import FallbackConfig, FallbackLLMClient
from zeo_integrations.llms.models import (
    ChatMessage,
    FunctionCall,
    LLMOptions,
    RoleType,
    ToolCall,
)
from zeo_integrations.llms.protocols import (
    LLMProviderProtocol,
    OneAttemptLLMProviderProtocol,
)
from zeo_integrations.llms.registry import (
    get_llm_client,
    register_llm_client,
)

__all__ = [
    # Main client classes
    "LLMClient",
    "OpenAIClient",
    "llm_chat_target",
    "AnthropicClient",
    "OllamaClient",
    "MockLLMClient",
    "FallbackLLMClient",
    # Configuration
    "LLMConfig",
    "LLMConfigProvider",
    "FallbackConfig",
    # Models
    "ChatMessage",
    "FunctionCall",
    "LLMOptions",
    "ToolCall",
    "RoleType",
    # Protocols
    "LLMProviderProtocol",
    "OneAttemptLLMProviderProtocol",
    # Registry
    "get_llm_client",
    "register_llm_client",
    # Factory function for integration discovery
    "create_integration",
    # Module
    "get_mock_llm",
]


def create_integration() -> IntegrationProtocol:
    """
    Create and return an LLM integration instance.

    This function is used as an entry point for automatic integration discovery.

    Returns:
        IntegrationProtocol: Configured LLM integration
    """
    from zeo_integrations.llms.service import LLMIntegration

    return LLMIntegration()


def get_mock_llm(script: list[str] | None = None) -> MockLLMClient:
    """
    Create a mock LLM client with a predefined script of responses.

    This is a convenience function for testing and educational purposes.

    Args:
        script: List of responses the mock LLM should return in sequence.

    Returns:
        MockLLMClient: A mock LLM client.
    """
    return MockLLMClient(script=script)
