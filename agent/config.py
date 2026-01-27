"""
Agent Configuration
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv


@dataclass
class AgentConfig:
    """Configuration for the AI Agent"""

    # Azure OpenAI (same as integration package)
    api_key: str = ""
    azure_endpoint: str = ""
    api_version: str = "2024-02-15-preview"
    deployment: str = "gpt-4"

    # Agent settings
    agent_name: str = "Curriculum Mapping Assistant"
    max_history: int = 50
    temperature: float = 0.7

    # Server settings
    host: str = "0.0.0.0"
    port: int = 5002
    debug: bool = False

    # Storage (reuse from integration)
    upload_folder: str = "uploads"
    output_folder: str = "outputs"
    insights_folder: str = "outputs/insights"
    library_folder: str = "outputs/library"

    # Supported dimensions
    dimensions: List[str] = field(default_factory=lambda: [
        "nmc_competency",
        "area_topics",
        "competency",
        "objective",
        "skill"
    ])

    def get_azure_config(self) -> dict:
        """Get config dict for AuditEngine"""
        return {
            'api_key': self.api_key,
            'azure_endpoint': self.azure_endpoint,
            'api_version': self.api_version,
            'deployment': self.deployment
        }

    def validate(self) -> tuple:
        """Validate configuration"""
        errors = []
        if not self.api_key:
            errors.append("AZURE_OPENAI_API_KEY is required")
        if not self.azure_endpoint:
            errors.append("AZURE_OPENAI_ENDPOINT is required")
        return len(errors) == 0, errors


def get_agent_config(env_file: str = None) -> AgentConfig:
    """Load agent configuration from environment"""
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    return AgentConfig(
        api_key=os.getenv('AZURE_OPENAI_API_KEY', ''),
        azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT', ''),
        api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
        deployment=os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4'),
        agent_name=os.getenv('AGENT_NAME', 'Curriculum Mapping Assistant'),
        max_history=int(os.getenv('AGENT_MAX_HISTORY', '50')),
        temperature=float(os.getenv('AGENT_TEMPERATURE', '0.7')),
        host=os.getenv('AGENT_HOST', '0.0.0.0'),
        port=int(os.getenv('AGENT_PORT', '5002')),
        debug=os.getenv('AGENT_DEBUG', 'false').lower() == 'true',
        upload_folder=os.getenv('UPLOAD_FOLDER', 'uploads'),
        output_folder=os.getenv('OUTPUT_FOLDER', 'outputs'),
        insights_folder=os.getenv('INSIGHTS_FOLDER', 'outputs/insights'),
        library_folder=os.getenv('LIBRARY_FOLDER', 'outputs/library')
    )
