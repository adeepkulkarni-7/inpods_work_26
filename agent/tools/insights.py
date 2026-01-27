"""
Insights Tool

Generates visual charts from mapping data.
"""

import os
import pandas as pd
from .base import BaseTool, ToolResult


class InsightsTool(BaseTool):
    """Generate visual insights from mapping data"""

    name = "generate_insights"
    description = """Create visual charts from curriculum mapping data.
    Generates bar charts, pie charts, confidence histograms, gap analysis, and summary dashboards."""

    parameters = {
        "type": "object",
        "properties": {
            "mapped_file": {
                "type": "string",
                "description": "Path to the file with mappings (CSV/Excel)"
            },
            "reference_file": {
                "type": "string",
                "description": "Path to the reference curriculum file (optional)"
            }
        },
        "required": ["mapped_file"]
    }

    def __init__(self, config: dict):
        super().__init__(config)
        self._viz_engine = None
        self.insights_folder = config.get('insights_folder', 'outputs/insights')
        os.makedirs(self.insights_folder, exist_ok=True)

    def _get_viz_engine(self):
        """Lazy load the visualization engine"""
        if self._viz_engine is None:
            from integration import VisualizationEngine
            self._viz_engine = VisualizationEngine(output_folder=self.insights_folder)
        return self._viz_engine

    async def execute(self, params: dict) -> ToolResult:
        """Generate insights"""
        try:
            mapped_file = params['mapped_file']

            if not os.path.exists(mapped_file):
                return ToolResult(
                    success=False,
                    error=f"Mapped file not found: {mapped_file}"
                )

            # Load mapped data
            if mapped_file.endswith('.csv'):
                mapped_df = pd.read_csv(mapped_file)
            elif mapped_file.endswith('.ods'):
                mapped_df = pd.read_excel(mapped_file, engine='odf')
            else:
                mapped_df = pd.read_excel(mapped_file, engine='openpyxl')

            # Build mapping data structure
            coverage = {}
            recommendations = []

            for idx, row in mapped_df.iterrows():
                topic = None
                for col in ['mapped_topic', 'mapped_objective', 'objective_id', 'Objective',
                            'mapped_competency', 'competency_id', 'mapped_skill', 'skill_id',
                            'mapped_nmc_competency', 'nmc_competency_id', 'mapped_id']:
                    if col in mapped_df.columns and pd.notna(row.get(col)) and row.get(col):
                        topic = str(row.get(col)).strip()
                        break

                if topic:
                    coverage[topic] = coverage.get(topic, 0) + 1

                confidence = row.get('confidence_score', 0.85)
                if pd.isna(confidence):
                    confidence = 0.85

                recommendations.append({
                    'confidence': float(confidence),
                    'question_num': row.get('Question Number', f'Q{idx+1}')
                })

            mapping_data = {
                'coverage': coverage,
                'recommendations': recommendations
            }

            # Get reference topics
            reference_topics = list(coverage.keys())
            reference_file = params.get('reference_file')
            if reference_file and os.path.exists(reference_file):
                if reference_file.endswith('.csv'):
                    ref_df = pd.read_csv(reference_file)
                else:
                    ref_df = pd.read_excel(reference_file)
                if 'Topic Area (CBME)' in ref_df.columns:
                    reference_topics = ref_df['Topic Area (CBME)'].dropna().tolist()
                elif 'Topic Area' in ref_df.columns:
                    reference_topics = ref_df['Topic Area'].dropna().tolist()

            # Generate charts
            viz_engine = self._get_viz_engine()
            charts = viz_engine.generate_all_insights(mapping_data, reference_topics)

            # Calculate summary stats
            avg_confidence = sum(r['confidence'] for r in recommendations) / len(recommendations) if recommendations else 0
            high_conf = sum(1 for r in recommendations if r['confidence'] >= 0.85)

            metadata = {
                'total_questions': len(recommendations),
                'topics_covered': len(coverage),
                'average_confidence': round(avg_confidence, 2),
                'high_confidence_count': high_conf,
                'charts_generated': len(charts)
            }

            return ToolResult(
                success=True,
                data={
                    'charts': charts,
                    'coverage': coverage,
                    'summary': metadata
                },
                message=f"Generated {len(charts)} visualization charts",
                metadata=metadata
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
