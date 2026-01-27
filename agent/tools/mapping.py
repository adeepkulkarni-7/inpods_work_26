"""
Mapping Tool

Maps exam questions to curriculum competencies using the AuditEngine.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from .base import BaseTool, ToolResult


class MappingTool(BaseTool):
    """Map questions to curriculum competencies"""

    name = "map_questions"
    description = """Map exam questions to curriculum competencies using AI analysis.
    Returns recommendations with confidence scores, coverage statistics, and gaps."""

    parameters = {
        "type": "object",
        "properties": {
            "question_file": {
                "type": "string",
                "description": "Path to the question bank file (CSV/Excel)"
            },
            "reference_file": {
                "type": "string",
                "description": "Path to the reference curriculum file (CSV/Excel)"
            },
            "dimension": {
                "type": "string",
                "enum": ["nmc_competency", "area_topics", "competency", "objective", "skill"],
                "description": "The curriculum dimension to map to"
            },
            "batch_size": {
                "type": "integer",
                "description": "Number of questions per API call (1-10)",
                "default": 5
            }
        },
        "required": ["question_file", "reference_file", "dimension"]
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
        """Execute the mapping"""
        try:
            # Validate parameters
            is_valid, errors = self.validate_params(params)
            if not is_valid:
                return ToolResult(
                    success=False,
                    error=f"Invalid parameters: {', '.join(errors)}"
                )

            # Check files exist
            question_file = params['question_file']
            reference_file = params['reference_file']

            if not os.path.exists(question_file):
                return ToolResult(
                    success=False,
                    error=f"Question file not found: {question_file}"
                )

            if not os.path.exists(reference_file):
                return ToolResult(
                    success=False,
                    error=f"Reference file not found: {reference_file}"
                )

            # Run the mapping
            engine = self._get_engine()
            batch_size = params.get('batch_size', 5)
            batch_size = max(1, min(10, batch_size))

            result = engine.run_audit_batched(
                question_csv=question_file,
                reference_csv=reference_file,
                dimension=params['dimension'],
                batch_size=batch_size
            )

            # Build summary
            total_mapped = result.get('mapped_questions', 0)
            coverage = result.get('coverage', {})
            gaps = result.get('gaps', [])
            recommendations = result.get('recommendations', [])

            # Calculate confidence stats
            confidences = [r.get('confidence', 0) for r in recommendations]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            high_conf = sum(1 for c in confidences if c >= 0.85)
            med_conf = sum(1 for c in confidences if 0.7 <= c < 0.85)
            low_conf = sum(1 for c in confidences if c < 0.7)

            summary = {
                'total_questions': result.get('total_questions', 0),
                'mapped_questions': total_mapped,
                'dimension': params['dimension'],
                'topics_covered': len(coverage),
                'gaps_found': len(gaps),
                'average_confidence': round(avg_confidence, 2),
                'high_confidence_count': high_conf,
                'medium_confidence_count': med_conf,
                'low_confidence_count': low_conf
            }

            return ToolResult(
                success=True,
                data=result,
                message=f"Successfully mapped {total_mapped} questions to {params['dimension']}",
                metadata=summary
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
