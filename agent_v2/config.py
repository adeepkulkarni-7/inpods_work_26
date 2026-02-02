"""
Agent V2 Configuration

Configuration management for the Curriculum Mapping AI Agent.
Supports Azure OpenAI settings, dimension definitions, and conversation parameters.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class DimensionConfig:
    """Configuration for a single mapping dimension."""
    name: str
    code_prefix: str
    description: str
    examples: List[str] = field(default_factory=list)
    requires_reference: bool = True


# All supported mapping dimensions
DIMENSIONS: Dict[str, DimensionConfig] = {
    'area_topics': DimensionConfig(
        name='Area Topics',
        code_prefix='Topic',
        description='NMC/OER curriculum topic areas (Topic / Subtopic format)',
        examples=['Bacteriology / Gram Positive Cocci', 'Virology / DNA Viruses', 'Immunology / Innate Immunity'],
        requires_reference=True
    ),
    'competency': DimensionConfig(
        name='Competency',
        code_prefix='C',
        description='Core competency codes (C1-C6)',
        examples=['C1', 'C2', 'C3', 'C4', 'C5', 'C6'],
        requires_reference=True
    ),
    'objective': DimensionConfig(
        name='Objective',
        code_prefix='O',
        description='Learning objective codes (O1-O6)',
        examples=['O1', 'O2', 'O3', 'O4', 'O5', 'O6'],
        requires_reference=True
    ),
    'skill': DimensionConfig(
        name='Skill',
        code_prefix='S',
        description='Clinical skill codes (S1-S5)',
        examples=['S1', 'S2', 'S3', 'S4', 'S5'],
        requires_reference=True
    ),
    'nmc_competency': DimensionConfig(
        name='NMC Competency',
        code_prefix='MI',
        description='National Medical Council 15 competencies (MI1.1-MI3.5)',
        examples=['MI1.1', 'MI1.2', 'MI2.1', 'MI2.2', 'MI3.1', 'MI3.2', 'MI3.3', 'MI3.4', 'MI3.5'],
        requires_reference=True
    ),
    'blooms': DimensionConfig(
        name='Blooms Taxonomy',
        code_prefix='KL',
        description="Bloom's taxonomy knowledge levels (KL1-KL6)",
        examples=['KL1 (Remember)', 'KL2 (Understand)', 'KL3 (Apply)', 'KL4 (Analyze)', 'KL5 (Evaluate)', 'KL6 (Create)'],
        requires_reference=False
    ),
    'complexity': DimensionConfig(
        name='Complexity',
        code_prefix='',
        description='Question difficulty classification (Easy/Medium/Hard)',
        examples=['Easy', 'Medium', 'Hard'],
        requires_reference=False
    )
}

# Blooms taxonomy levels (built-in, no reference file needed)
BLOOMS_LEVELS = {
    'KL1': {'name': 'Remember', 'description': 'Recall facts and basic concepts'},
    'KL2': {'name': 'Understand', 'description': 'Explain ideas or concepts'},
    'KL3': {'name': 'Apply', 'description': 'Use information in new situations'},
    'KL4': {'name': 'Analyze', 'description': 'Draw connections among ideas'},
    'KL5': {'name': 'Evaluate', 'description': 'Justify a stand or decision'},
    'KL6': {'name': 'Create', 'description': 'Produce new or original work'}
}

# Complexity levels (built-in, no reference file needed)
COMPLEXITY_LEVELS = {
    'Easy': {'description': 'Basic recall or straightforward application'},
    'Medium': {'description': 'Requires analysis or integration of concepts'},
    'Hard': {'description': 'Complex reasoning, synthesis, or evaluation'}
}


@dataclass
class AgentConfig:
    """Main configuration for the Curriculum Mapping AI Agent."""

    # Azure OpenAI settings
    azure_api_key: str = field(default_factory=lambda: os.getenv('AZURE_OPENAI_API_KEY', ''))
    azure_endpoint: str = field(default_factory=lambda: os.getenv('AZURE_OPENAI_ENDPOINT', ''))
    azure_api_version: str = field(default_factory=lambda: os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'))
    azure_deployment: str = field(default_factory=lambda: os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4'))

    # Agent behavior settings
    agent_name: str = "Curriculum Mapping Agent"
    agent_version: str = "2.0.0"
    max_conversation_turns: int = 50
    max_questions_per_batch: int = 5
    default_confidence_threshold: float = 0.70

    # Server settings
    host: str = '0.0.0.0'
    port: int = 5003
    debug: bool = True

    # Folder paths
    upload_folder: str = 'agent_v2/uploads'
    output_folder: str = 'agent_v2/outputs'
    session_folder: str = 'agent_v2/sessions'

    # Backend API settings (connects to existing backend_v2)
    backend_url: str = 'http://localhost:5001'
    use_backend_api: bool = True

    # Conversation settings
    welcome_message: str = """Hello! I'm your Curriculum Mapping Assistant.

I can help you with:
• **Map Questions** - Map exam questions to curriculum topics/competencies
• **Review Mappings** - Analyze and improve existing mappings
• **Generate Insights** - Create visual reports from your data

What would you like to do today?"""

    # Available dimensions
    dimensions: Dict[str, DimensionConfig] = field(default_factory=lambda: DIMENSIONS.copy())

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Create folders if they don't exist
        for folder in [self.upload_folder, self.output_folder, self.session_folder]:
            os.makedirs(folder, exist_ok=True)

    def validate(self) -> tuple[bool, str]:
        """Validate that required configuration is present."""
        if not self.azure_api_key:
            return False, "AZURE_OPENAI_API_KEY not set"
        if not self.azure_endpoint:
            return False, "AZURE_OPENAI_ENDPOINT not set"
        return True, "Configuration valid"

    def get_azure_config(self) -> dict:
        """Get Azure OpenAI configuration as dictionary."""
        return {
            'api_key': self.azure_api_key,
            'azure_endpoint': self.azure_endpoint,
            'api_version': self.azure_api_version,
            'deployment': self.azure_deployment
        }

    def get_dimension(self, dimension_key: str) -> Optional[DimensionConfig]:
        """Get configuration for a specific dimension."""
        return self.dimensions.get(dimension_key)

    def list_dimensions(self) -> List[str]:
        """List all available dimension keys."""
        return list(self.dimensions.keys())

    def get_dimension_display_names(self) -> Dict[str, str]:
        """Get mapping of dimension keys to display names."""
        return {key: dim.name for key, dim in self.dimensions.items()}


# Singleton config instance
_config_instance: Optional[AgentConfig] = None


def get_agent_config() -> AgentConfig:
    """Get the singleton agent configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = AgentConfig()
    return _config_instance


def reset_config():
    """Reset the configuration instance (useful for testing)."""
    global _config_instance
    _config_instance = None
