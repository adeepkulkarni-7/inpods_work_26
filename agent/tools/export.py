"""
Export Tool

Exports mapping results to Excel files.
"""

import os
from .base import BaseTool, ToolResult


class ExportTool(BaseTool):
    """Export mapping results to Excel"""

    name = "export_results"
    description = """Export mapping results to an Excel file for download.
    Creates a formatted spreadsheet with questions, mappings, confidence scores, and justifications."""

    parameters = {
        "type": "object",
        "properties": {
            "question_file": {
                "type": "string",
                "description": "Path to the original question file"
            },
            "recommendations": {
                "type": "array",
                "description": "List of mapping recommendations"
            },
            "selected_indices": {
                "type": "array",
                "description": "Indices of recommendations to include",
                "items": {"type": "integer"}
            },
            "dimension": {
                "type": "string",
                "description": "The curriculum dimension"
            }
        },
        "required": ["question_file", "recommendations", "selected_indices", "dimension"]
    }

    def __init__(self, config: dict):
        super().__init__(config)
        self._engine = None
        self.output_folder = config.get('output_folder', 'outputs')
        os.makedirs(self.output_folder, exist_ok=True)

    def _get_engine(self):
        """Lazy load the audit engine"""
        if self._engine is None:
            from integration import AuditEngine
            self._engine = AuditEngine(self.config)
        return self._engine

    async def execute(self, params: dict) -> ToolResult:
        """Export to Excel"""
        try:
            question_file = params['question_file']
            recommendations = params['recommendations']
            selected_indices = params['selected_indices']
            dimension = params['dimension']

            if not os.path.exists(question_file):
                return ToolResult(
                    success=False,
                    error=f"Question file not found: {question_file}"
                )

            if not recommendations:
                return ToolResult(
                    success=False,
                    error="No recommendations to export"
                )

            # If no selection, select all
            if not selected_indices:
                selected_indices = list(range(len(recommendations)))

            engine = self._get_engine()
            output_path = engine.apply_and_export(
                question_csv=question_file,
                recommendations=recommendations,
                selected_indices=selected_indices,
                dimension=dimension,
                output_folder=self.output_folder
            )

            filename = os.path.basename(output_path)

            return ToolResult(
                success=True,
                data={
                    'file_path': output_path,
                    'filename': filename,
                    'download_url': f'/api/download/{filename}'
                },
                message=f"Exported {len(selected_indices)} mappings to {filename}",
                metadata={
                    'total_exported': len(selected_indices),
                    'dimension': dimension,
                    'filename': filename
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
