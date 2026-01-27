"""
Base Tool Class

All agent tools inherit from this base class.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


@dataclass
class ToolResult:
    """Result from a tool execution"""
    success: bool
    data: Any = None
    message: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "message": self.message,
            "error": self.error,
            "metadata": self.metadata
        }


class BaseTool(ABC):
    """
    Base class for all agent tools.

    Each tool has:
    - name: Unique identifier
    - description: What the tool does
    - parameters: JSON schema for input parameters
    - execute(): The actual implementation
    """

    name: str = "base_tool"
    description: str = "Base tool description"
    parameters: dict = {
        "type": "object",
        "properties": {},
        "required": []
    }

    def __init__(self, config: dict):
        """Initialize tool with configuration"""
        self.config = config

    @abstractmethod
    async def execute(self, params: dict) -> ToolResult:
        """
        Execute the tool with given parameters.

        Args:
            params: Dictionary of parameters matching the schema

        Returns:
            ToolResult with success status and data/error
        """
        raise NotImplementedError

    def get_definition(self) -> dict:
        """Get OpenAI function definition format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    def validate_params(self, params: dict) -> tuple:
        """
        Validate parameters against schema.

        Returns:
            (is_valid: bool, errors: list)
        """
        errors = []
        required = self.parameters.get("required", [])
        properties = self.parameters.get("properties", {})

        for req in required:
            if req not in params:
                errors.append(f"Missing required parameter: {req}")

        for key, value in params.items():
            if key in properties:
                prop_type = properties[key].get("type")
                if prop_type == "string" and not isinstance(value, str):
                    errors.append(f"Parameter {key} must be a string")
                elif prop_type == "integer" and not isinstance(value, int):
                    errors.append(f"Parameter {key} must be an integer")
                elif prop_type == "array" and not isinstance(value, list):
                    errors.append(f"Parameter {key} must be an array")

        return len(errors) == 0, errors
