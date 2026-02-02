"""
Visualization Engine for Curriculum Mapping Insights
Generates static charts (PNG) for stakeholder reporting

V2.3: Clean infographic-style visualizations
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle
import seaborn as sns
import numpy as np
import pandas as pd

import os
from datetime import datetime
from collections import Counter


class VisualizationEngine:
    """Generates insight charts from mapping data"""

    def __init__(self, output_folder='outputs/insights'):
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)

        # Set seaborn theme
        sns.set_theme(style="whitegrid", context="notebook", font_scale=1.1)
        self.palette = sns.color_palette("husl", 12)

        # Brand colors
        self.colors = {
            'primary': '#0077b6',
            'success': '#10b981',
            'warning': '#f59e0b',
            'danger': '#ef4444',
            'info': '#6366f1',
            'dark': '#1e293b',
            'light': '#f8fafc',
            'muted': '#94a3b8'
        }

        # Dimension-specific colors
        self.dimension_colors = {
            'competency': '#0077b6',
            'objective': '#2a9d8f',
            'skill': '#e9c46a',
            'blooms': '#9b5de5',
            'complexity': '#f72585',
            'area_topics': '#4361ee',
            'nmc_competency': '#fb8500'
        }

    def _save_chart(self, fig, prefix):
        """Helper to save a chart and return the filepath"""
        filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_folder, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close()
        return filepath

    # ==================== INFOGRAPHIC CHART 1: Executive Summary ====================
    def generate_executive_summary(self, total_questions, coverage_data, confidence_scores,
                                   gaps_count, dimensions_mapped=None):
        """
        Clean executive summary card with key metrics
        """
        fig, ax = plt.subplots(figsize=(14, 6))
        ax.set_xlim(0, 14)
        ax.set_ylim(0, 6)
        ax.axis('off')

        # Background
        fig.patch.set_facecolor('#f8fafc')

        # Title bar
        ax.add_patch(FancyBboxPatch((0.2, 5.2), 13.6, 0.6, boxstyle="round,pad=0.02",
                                     facecolor=self.colors['dark'], edgecolor='none'))
        ax.text(7, 5.5, 'CURRICULUM MAPPING SUMMARY', ha='center', va='center',
                fontsize=16, fontweight='bold', color='white')

        # === Metric Cards ===
        card_y = 3.2
        card_height = 1.8
        card_width = 3.0

        # Card 1: Total Questions
        self._draw_metric_card(ax, 0.5, card_y, card_width, card_height,
                              str(total_questions), 'Questions Mapped', self.colors['primary'])

        # Card 2: Topics Covered
        topics_covered = len([k for k, v in coverage_data.items() if v > 0])
        total_topics = len(coverage_data)
        self._draw_metric_card(ax, 3.8, card_y, card_width, card_height,
                              f"{topics_covered}/{total_topics}", 'Topics Covered', self.colors['info'])

        # Card 3: Avg Confidence
        avg_conf = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        conf_color = self.colors['success'] if avg_conf >= 0.85 else (self.colors['warning'] if avg_conf >= 0.7 else self.colors['danger'])
        self._draw_metric_card(ax, 7.1, card_y, card_width, card_height,
                              f"{avg_conf:.0%}", 'Avg Confidence', conf_color)

        # Card 4: Gaps
        gap_color = self.colors['success'] if gaps_count == 0 else (self.colors['warning'] if gaps_count <= 2 else self.colors['danger'])
        self._draw_metric_card(ax, 10.4, card_y, card_width, card_height,
                              str(gaps_count), 'Curriculum Gaps', gap_color)

        # === Confidence Breakdown Bar ===
        if confidence_scores:
            high = sum(1 for c in confidence_scores if c >= 0.85)
            med = sum(1 for c in confidence_scores if 0.7 <= c < 0.85)
            low = sum(1 for c in confidence_scores if c < 0.7)
            total = len(confidence_scores)

            bar_y = 1.2
            bar_height = 0.5
            bar_width = 12.6

            ax.text(0.5, bar_y + 0.9, 'Confidence Distribution', fontsize=11, fontweight='bold', color=self.colors['dark'])

            # Stacked bar
            x_start = 0.5
            if high > 0:
                w = (high / total) * bar_width
                ax.add_patch(FancyBboxPatch((x_start, bar_y), w, bar_height,
                            boxstyle="round,pad=0.02", facecolor=self.colors['success'], edgecolor='none'))
                if w > 1:
                    ax.text(x_start + w/2, bar_y + bar_height/2, f'{high} High',
                           ha='center', va='center', fontsize=9, color='white', fontweight='bold')
                x_start += w

            if med > 0:
                w = (med / total) * bar_width
                ax.add_patch(FancyBboxPatch((x_start, bar_y), w, bar_height,
                            boxstyle="round,pad=0.02", facecolor=self.colors['warning'], edgecolor='none'))
                if w > 1:
                    ax.text(x_start + w/2, bar_y + bar_height/2, f'{med} Med',
                           ha='center', va='center', fontsize=9, color='white', fontweight='bold')
                x_start += w

            if low > 0:
                w = (low / total) * bar_width
                ax.add_patch(FancyBboxPatch((x_start, bar_y), w, bar_height,
                            boxstyle="round,pad=0.02", facecolor=self.colors['danger'], edgecolor='none'))
                if w > 1:
                    ax.text(x_start + w/2, bar_y + bar_height/2, f'{low} Low',
                           ha='center', va='center', fontsize=9, color='white', fontweight='bold')

        # Footer
        ax.text(7, 0.3, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
               ha='center', va='center', fontsize=9, color=self.colors['muted'])

        return self._save_chart(fig, 'executive_summary')

    def _draw_metric_card(self, ax, x, y, width, height, value, label, color):
        """Helper to draw a metric card"""
        ax.add_patch(FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.05",
                                     facecolor='white', edgecolor=color, linewidth=2))
        ax.text(x + width/2, y + height*0.65, value, ha='center', va='center',
                fontsize=24, fontweight='bold', color=color)
        ax.text(x + width/2, y + height*0.25, label, ha='center', va='center',
                fontsize=10, color=self.colors['muted'])

    # ==================== INFOGRAPHIC CHART 2: Coverage Heatmap ====================
    def generate_coverage_heatmap(self, coverage_data, title="Topic Coverage Intensity"):
        """
        Heatmap-style visualization of coverage across all topics
        """
        if not coverage_data:
            return None

        # Sort by count descending
        sorted_items = sorted(coverage_data.items(), key=lambda x: -x[1])
        codes = [item[0] for item in sorted_items]
        counts = [item[1] for item in sorted_items]
        max_count = max(counts) if counts else 1

        # Create figure
        n_items = len(codes)
        fig_height = max(4, n_items * 0.4 + 1)
        fig, ax = plt.subplots(figsize=(10, fig_height))

        # Create horizontal bars with gradient based on intensity
        y_positions = range(len(codes))

        # Normalize counts for color intensity
        norm_counts = [c / max_count for c in counts]
        colors = [plt.cm.Blues(0.3 + 0.7 * nc) for nc in norm_counts]

        bars = ax.barh(y_positions, counts, color=colors, edgecolor='white', height=0.7)

        # Add value labels
        for i, (bar, count) in enumerate(zip(bars, counts)):
            # Label inside or outside based on bar width
            if count > max_count * 0.3:
                ax.text(count - max_count*0.02, i, str(count), ha='right', va='center',
                       fontsize=10, fontweight='bold', color='white')
            else:
                ax.text(count + max_count*0.02, i, str(count), ha='left', va='center',
                       fontsize=10, fontweight='bold', color=self.colors['dark'])

        ax.set_yticks(y_positions)
        ax.set_yticklabels(codes, fontsize=10)
        ax.set_xlabel('Number of Questions', fontsize=11)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15, color=self.colors['dark'])
        ax.invert_yaxis()

        # Clean up
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.tick_params(left=False)

        plt.tight_layout()
        return self._save_chart(fig, 'coverage_heatmap')

    # ==================== INFOGRAPHIC CHART 3: Confidence Gauge ====================
    def generate_confidence_gauge(self, confidence_scores, title="Overall Mapping Confidence"):
        """
        Clean gauge/meter showing overall confidence level
        """
        if not confidence_scores:
            return None

        avg_conf = sum(confidence_scores) / len(confidence_scores)

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-0.2, 1.2)
        ax.axis('off')
        fig.patch.set_facecolor('white')

        # Draw gauge arc background
        theta = np.linspace(np.pi, 0, 100)
        r = 1

        # Background arc (gray)
        x_bg = r * np.cos(theta)
        y_bg = r * np.sin(theta)
        ax.plot(x_bg, y_bg, color='#e2e8f0', linewidth=25, solid_capstyle='round')

        # Colored sections
        # Red section (0-70%)
        theta_red = np.linspace(np.pi, np.pi * 0.65, 30)
        ax.plot(r * np.cos(theta_red), r * np.sin(theta_red),
               color=self.colors['danger'], linewidth=22, solid_capstyle='butt')

        # Yellow section (70-85%)
        theta_yellow = np.linspace(np.pi * 0.65, np.pi * 0.425, 15)
        ax.plot(r * np.cos(theta_yellow), r * np.sin(theta_yellow),
               color=self.colors['warning'], linewidth=22, solid_capstyle='butt')

        # Green section (85-100%)
        theta_green = np.linspace(np.pi * 0.425, 0, 30)
        ax.plot(r * np.cos(theta_green), r * np.sin(theta_green),
               color=self.colors['success'], linewidth=22, solid_capstyle='butt')

        # Needle
        needle_angle = np.pi * (1 - avg_conf)
        needle_x = 0.7 * np.cos(needle_angle)
        needle_y = 0.7 * np.sin(needle_angle)
        ax.annotate('', xy=(needle_x, needle_y), xytext=(0, 0),
                   arrowprops=dict(arrowstyle='->', color=self.colors['dark'], lw=3))

        # Center circle
        circle = Circle((0, 0), 0.1, color=self.colors['dark'], zorder=10)
        ax.add_patch(circle)

        # Value display
        conf_color = self.colors['success'] if avg_conf >= 0.85 else (self.colors['warning'] if avg_conf >= 0.7 else self.colors['danger'])
        ax.text(0, -0.15, f'{avg_conf:.0%}', ha='center', va='top',
               fontsize=32, fontweight='bold', color=conf_color)

        # Labels
        ax.text(-1.2, -0.05, '0%', ha='center', fontsize=10, color=self.colors['muted'])
        ax.text(1.2, -0.05, '100%', ha='center', fontsize=10, color=self.colors['muted'])
        ax.text(0, 1.1, title, ha='center', fontsize=14, fontweight='bold', color=self.colors['dark'])

        # Legend
        ax.text(-0.9, 0.6, 'Low', fontsize=9, color=self.colors['danger'])
        ax.text(0, 0.85, 'Med', fontsize=9, color=self.colors['warning'])
        ax.text(0.8, 0.6, 'High', fontsize=9, color=self.colors['success'])

        return self._save_chart(fig, 'confidence_gauge')

    # ==================== INFOGRAPHIC CHART 4: Gap Alert Panel ====================
    def generate_gap_analysis(self, coverage_data, reference_topics, title="Coverage Analysis"):
        """
        Clean visual showing gaps and coverage status
        """
        if not reference_topics:
            return None

        # Categorize topics
        gaps = []
        low_coverage = []
        good_coverage = []

        for topic in reference_topics:
            count = coverage_data.get(topic, 0)
            if count == 0:
                gaps.append(topic)
            elif count <= 2:
                low_coverage.append((topic, count))
            else:
                good_coverage.append((topic, count))

        # Sort by count
        low_coverage.sort(key=lambda x: x[1])
        good_coverage.sort(key=lambda x: -x[1])

        # Create figure
        fig, axes = plt.subplots(1, 3, figsize=(14, 5))
        fig.suptitle(title, fontsize=16, fontweight='bold', y=1.02, color=self.colors['dark'])

        # Panel 1: Gaps (Red)
        ax1 = axes[0]
        ax1.set_xlim(0, 10)
        ax1.set_ylim(0, max(6, len(gaps) + 2))
        ax1.axis('off')

        ax1.add_patch(FancyBboxPatch((0.5, 0.5), 9, max(5, len(gaps) + 1.5),
                     boxstyle="round,pad=0.05", facecolor='#fef2f2', edgecolor=self.colors['danger'], linewidth=2))
        ax1.text(5, max(5, len(gaps) + 1.5) - 0.3, f"GAPS ({len(gaps)})", ha='center', va='top',
                fontsize=12, fontweight='bold', color=self.colors['danger'])

        for i, gap in enumerate(gaps[:10]):  # Limit to 10
            ax1.text(5, max(5, len(gaps) + 1.5) - 1.2 - i*0.5, f"• {gap}", ha='center', va='top',
                    fontsize=10, color=self.colors['dark'])
        if len(gaps) == 0:
            ax1.text(5, 3, "No gaps!", ha='center', va='center', fontsize=11,
                    color=self.colors['success'], fontweight='bold')

        # Panel 2: Low Coverage (Yellow)
        ax2 = axes[1]
        ax2.set_xlim(0, 10)
        ax2.set_ylim(0, max(6, len(low_coverage) + 2))
        ax2.axis('off')

        ax2.add_patch(FancyBboxPatch((0.5, 0.5), 9, max(5, len(low_coverage) + 1.5),
                     boxstyle="round,pad=0.05", facecolor='#fffbeb', edgecolor=self.colors['warning'], linewidth=2))
        ax2.text(5, max(5, len(low_coverage) + 1.5) - 0.3, f"LOW COVERAGE ({len(low_coverage)})",
                ha='center', va='top', fontsize=12, fontweight='bold', color=self.colors['warning'])

        for i, (topic, count) in enumerate(low_coverage[:10]):
            ax2.text(5, max(5, len(low_coverage) + 1.5) - 1.2 - i*0.5, f"• {topic} ({count})",
                    ha='center', va='top', fontsize=10, color=self.colors['dark'])
        if len(low_coverage) == 0:
            ax2.text(5, 3, "All topics have\ngood coverage!", ha='center', va='center',
                    fontsize=11, color=self.colors['success'], fontweight='bold')

        # Panel 3: Good Coverage (Green)
        ax3 = axes[2]
        ax3.set_xlim(0, 10)
        ax3.set_ylim(0, max(6, min(len(good_coverage), 10) + 2))
        ax3.axis('off')

        ax3.add_patch(FancyBboxPatch((0.5, 0.5), 9, max(5, min(len(good_coverage), 10) + 1.5),
                     boxstyle="round,pad=0.05", facecolor='#f0fdf4', edgecolor=self.colors['success'], linewidth=2))
        ax3.text(5, max(5, min(len(good_coverage), 10) + 1.5) - 0.3, f"GOOD COVERAGE ({len(good_coverage)})",
                ha='center', va='top', fontsize=12, fontweight='bold', color=self.colors['success'])

        for i, (topic, count) in enumerate(good_coverage[:10]):
            ax3.text(5, max(5, min(len(good_coverage), 10) + 1.5) - 1.2 - i*0.5, f"• {topic} ({count})",
                    ha='center', va='top', fontsize=10, color=self.colors['dark'])

        plt.tight_layout()
        return self._save_chart(fig, 'gap_analysis')

    # ==================== Coverage Table (Data Only) ====================
    def generate_coverage_table(self, coverage_data, reference_data, total_questions):
        """
        Generate coverage table data: Code → Definition → Mapped Questions → %
        """
        table_data = []

        # Handle different reference_data formats
        if isinstance(reference_data, dict):
            all_codes = set(reference_data.keys()) | set(coverage_data.keys())
        else:
            all_codes = set(coverage_data.keys())
            reference_data = {code: '' for code in all_codes}

        for code in sorted(all_codes):
            count = coverage_data.get(code, 0)
            definition = reference_data.get(code, '')

            # Handle nested dict
            if isinstance(definition, dict):
                definition = definition.get('description', str(definition))

            percentage = round((count / total_questions * 100), 1) if total_questions > 0 else 0

            table_data.append({
                'code': code,
                'definition': str(definition)[:200] if definition else '',
                'count': count,
                'percentage': percentage
            })

        # Sort by count descending
        table_data.sort(key=lambda x: (-x['count'], x['code']))
        return table_data

    # ==================== Main Entry Point ====================
    def generate_all_insights(self, mapping_data, reference_topics, reference_definitions=None):
        """
        Generate all insight charts from mapping data

        Returns clean infographic-style visualizations
        """
        coverage = mapping_data.get('coverage', {})
        recommendations = mapping_data.get('recommendations', [])
        confidence_scores = [r.get('confidence', 0) for r in recommendations]
        total_questions = len(recommendations)

        # Calculate gaps
        gaps_count = len([t for t in reference_topics if coverage.get(t, 0) == 0])

        charts = {}

        # 1. Executive Summary (main infographic)
        charts['executive_summary'] = self.generate_executive_summary(
            total_questions, coverage, confidence_scores, gaps_count
        )

        # 2. Coverage Heatmap
        charts['coverage_heatmap'] = self.generate_coverage_heatmap(coverage)

        # 3. Confidence Gauge
        charts['confidence_gauge'] = self.generate_confidence_gauge(confidence_scores)

        # 4. Gap Analysis Panel
        charts['gap_analysis'] = self.generate_gap_analysis(coverage, reference_topics)

        # Coverage Table Data (for HTML display)
        ref_defs = reference_definitions or mapping_data.get('reference_definitions', {})
        if not ref_defs:
            ref_defs = {topic: '' for topic in reference_topics}
        charts['coverage_table'] = self.generate_coverage_table(coverage, ref_defs, total_questions)

        return charts

    # ==================== V2.4: Per-Dimension Entry Point ====================
    def generate_all_insights_v2(self, mapping_data, dimensions, reference_by_dimension):
        """
        Generate insight charts with per-dimension separation

        Args:
            mapping_data: {coverage, coverage_by_dimension, recommendations}
            dimensions: list of dimension names to analyze
            reference_by_dimension: {dim: {topics: [], definitions: {}}}

        Returns charts dict with:
            - executive_summary (global)
            - confidence_gauge (global)
            - coverage_heatmap_{dim} (per dimension)
            - gap_analysis_{dim} (per dimension)
            - coverage_tables (per dimension)
        """
        coverage = mapping_data.get('coverage', {})
        coverage_by_dimension = mapping_data.get('coverage_by_dimension', {})
        recommendations = mapping_data.get('recommendations', [])
        confidence_scores = [r.get('confidence', 0) for r in recommendations]
        total_questions = len(recommendations)

        # Calculate total gaps across all dimensions
        total_gaps = 0
        for dim in dimensions:
            ref_topics = reference_by_dimension.get(dim, {}).get('topics', [])
            dim_coverage = coverage_by_dimension.get(dim, {})
            total_gaps += len([t for t in ref_topics if dim_coverage.get(t, 0) == 0])

        charts = {}

        # 1. Executive Summary (global - uses combined coverage)
        charts['executive_summary'] = self.generate_executive_summary(
            total_questions, coverage, confidence_scores, total_gaps, dimensions
        )

        # 2. Confidence Gauge (global)
        charts['confidence_gauge'] = self.generate_confidence_gauge(confidence_scores)

        # 3. Per-dimension charts
        coverage_tables = {}

        for dim in dimensions:
            dim_coverage = coverage_by_dimension.get(dim, {})
            ref_data = reference_by_dimension.get(dim, {})
            ref_topics = ref_data.get('topics', list(dim_coverage.keys()))
            ref_defs = ref_data.get('definitions', {})

            if not dim_coverage:
                continue

            # Dimension label for chart titles
            dim_label = self._format_dimension_label(dim)

            # Coverage heatmap for this dimension
            charts[f'coverage_heatmap_{dim}'] = self.generate_coverage_heatmap(
                dim_coverage,
                title=f"{dim_label} Coverage"
            )

            # Gap analysis for this dimension
            charts[f'gap_analysis_{dim}'] = self.generate_gap_analysis(
                dim_coverage,
                ref_topics,
                title=f"{dim_label} Gap Analysis"
            )

            # Coverage table for this dimension
            coverage_tables[dim] = self.generate_coverage_table(
                dim_coverage, ref_defs, total_questions
            )

        charts['coverage_tables'] = coverage_tables

        return charts

    def _format_dimension_label(self, dim):
        """Format dimension name for display"""
        labels = {
            'competency': 'Competency',
            'objective': 'Objective',
            'skill': 'Skill',
            'nmc_competency': 'NMC Competency',
            'area_topics': 'Topic Areas',
            'blooms': 'Blooms Level',
            'complexity': 'Complexity'
        }
        return labels.get(dim, dim.replace('_', ' ').title())


# For backward compatibility - keep old method names mapping to new ones
VisualizationEngine.generate_topic_bar_chart = lambda self, *args, **kwargs: self.generate_coverage_heatmap(*args, **kwargs)
VisualizationEngine.generate_summary_dashboard = lambda self, coverage, conf, ref, **kwargs: self.generate_executive_summary(
    len(conf) if conf else 0, coverage, conf, len([t for t in ref if coverage.get(t, 0) == 0])
)
