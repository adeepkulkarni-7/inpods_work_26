"""
Curriculum Mapping AI Agent V2

A conversational AI agent for curriculum mapping with full dimension support.
Supports: NMC Competency, Area Topics, Competency, Objective, Skill, Blooms, Complexity

Usage:
    python run_agent_v2.py          # Web interface on port 5003
    python run_agent_v2.py cli      # CLI interface
"""

__version__ = "2.0.0"

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
