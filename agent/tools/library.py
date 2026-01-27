"""
Library Tool

Saves and manages mapping sets in the library.
"""

import os
from .base import BaseTool, ToolResult


class LibraryTool(BaseTool):
    """Save mappings to the library"""

    name = "save_to_library"
    description = """Save mapping results to the library for future reference.
    Creates a named entry that can be loaded, exported, or deleted later."""

    parameters = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name for the saved mapping set"
            },
            "recommendations": {
                "type": "array",
                "description": "List of mapping recommendations to save"
            },
            "dimension": {
                "type": "string",
                "description": "The curriculum dimension"
            },
            "mode": {
                "type": "string",
                "description": "Mode: A (map), B (rate), or C (insights)",
                "default": "A"
            },
            "source_file": {
                "type": "string",
                "description": "Original source filename",
                "default": ""
            }
        },
        "required": ["name", "recommendations", "dimension"]
    }

    def __init__(self, config: dict):
        super().__init__(config)
        self._library = None
        self.library_folder = config.get('library_folder', 'outputs/library')
        os.makedirs(self.library_folder, exist_ok=True)

    def _get_library(self):
        """Lazy load the library manager"""
        if self._library is None:
            from integration import LibraryManager
            self._library = LibraryManager(self.library_folder)
        return self._library

    async def execute(self, params: dict) -> ToolResult:
        """Save to library"""
        try:
            name = params['name']
            recommendations = params['recommendations']
            dimension = params['dimension']
            mode = params.get('mode', 'A')
            source_file = params.get('source_file', '')

            if not recommendations:
                return ToolResult(
                    success=False,
                    error="No recommendations to save"
                )

            library = self._get_library()
            result = library.save_mapping(
                name=name,
                recommendations=recommendations,
                dimension=dimension,
                mode=mode,
                source_file=source_file
            )

            return ToolResult(
                success=True,
                data=result,
                message=f"Saved '{name}' to library with {len(recommendations)} mappings",
                metadata={
                    'library_id': result['id'],
                    'name': result['name'],
                    'question_count': len(recommendations),
                    'dimension': dimension
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )


class ListLibraryTool(BaseTool):
    """List saved mappings in the library"""

    name = "list_library"
    description = "List all saved mapping sets in the library."

    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    def __init__(self, config: dict):
        super().__init__(config)
        self._library = None
        self.library_folder = config.get('library_folder', 'outputs/library')

    def _get_library(self):
        if self._library is None:
            from integration import LibraryManager
            self._library = LibraryManager(self.library_folder)
        return self._library

    async def execute(self, params: dict) -> ToolResult:
        try:
            library = self._get_library()
            mappings = library.list_mappings()

            return ToolResult(
                success=True,
                data=mappings,
                message=f"Found {len(mappings)} saved mappings in library",
                metadata={'count': len(mappings)}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
