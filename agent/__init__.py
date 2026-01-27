"""
Curriculum Mapping AI Agent

An autonomous conversational agent that guides users through
curriculum mapping workflows using natural language.

Usage:
    # CLI Mode
    python -m agent.cli

    # Web Mode
    python -m agent.web

    # Or import directly
    from agent import AgentOrchestrator
    agent = AgentOrchestrator(config)
    response = await agent.process_message("Help me map my questions")
"""

__version__ = "1.0.0"

from .orchestrator import AgentOrchestrator
from .conversation import ConversationState, ConversationStep
from .config import AgentConfig, get_agent_config

__all__ = [
    'AgentOrchestrator',
    'ConversationState',
    'ConversationStep',
    'AgentConfig',
    'get_agent_config'
]
