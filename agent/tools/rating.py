"""
Rating Tool

Rates existing curriculum mappings using the AuditEngine.
"""

import os
from .base import BaseTool, ToolResult


class RatingTool(BaseTool):
    """Rate existing question-to-curriculum mappings"""

    name = "rate_mappings"
    description = """Evaluate existing question-to-competency mappings and suggest improvements.
    Returns ratings (correct/partial/incorrect) with justifications and alternative suggestions."""

    parameters = {
        "type": "object",
        "properties": {
            "mapped_file": {
                "type": "string",
                "description": "Path to the file with existing mappings (CSV/Excel)"
            },
            "reference_file": {
                "type": "string",
                "description": "Path to the reference curriculum file (CSV/Excel)"
            },
            "dimension": {
                "type": "string",
                "enum": ["nmc_competency", "area_topics", "competency", "objective", "skill"],
                "description": "The curriculum dimension being rated"
            },
            "batch_size": {
                "type": "integer",
                "description": "Number of questions per API call (1-10)",
                "default": 5
            }
        },
        "required": ["mapped_file", "reference_file", "dimension"]
    }

    def __init__(self, config: dict):
        super().__init__(config)
        self._engine = None

    def _get_engine(self):
        """Lazy load the audit engine"""
        if self._engine is None:
            from integration import AuditEngine
            self._engine = AuditEngine(self.config)
        return self._engine

    async def execute(self, params: dict) -> ToolResult:
        """Execute the rating"""
        try:
            # Validate parameters
            is_valid, errors = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    success=False,
                    error=f"Invalid parameters: {', '.join(errors)}"
                )

            # Check files exist
            mapped_file = params['mapped_file']
            reference_file = params['reference_file']

            if not os.path.exists(mapped_file):
                return ToolResult(
                    success=False,
                    error=f"Mapped file not found: {mapped_file}"
                )

            if not os.path.exists(reference_file):
                return ToolResult(
                    success=False,
                    error=f"Reference file not found: {reference_file}"
                )

            # Run the rating
            engine = self._get_engine()
            batch_size = params.get('batch_size', 5)
            batch_size = max(1, min(10, batch_size))

            result = engine.rate_existing_mappings(
                mapped_file=mapped_file,
                reference_csv=reference_file,
                dimension=params['dimension'],
                batch_size=batch_size
            )

            # Extract summary
            summary = result.get('summary', {})
            ratings = result.get('ratings', [])
            recommendations = result.get('recommendations', [])

            metadata = {
                'total_rated': summary.get('total_rated', len(ratings)),
                'correct': summary.get('correct', 0),
                'partially_correct': summary.get('partially_correct', 0),
                'incorrect': summary.get('incorrect', 0),
                'accuracy_rate': round(summary.get('accuracy_rate', 0), 2),
                'average_agreement': round(summary.get('average_agreement_score', 0), 2),
                'needs_correction': len(recommendations)
            }

            return ToolResult(
                success=True,
                data=result,
                message=f"Rated {metadata['total_rated']} mappings: {metadata['correct']} correct, {metadata['partially_correct']} partial, {metadata['incorrect']} incorrect",
                metadata=metadata
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
