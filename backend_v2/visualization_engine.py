"""
Visualization Engine for Curriculum Mapping Insights
Generates static charts (PNG) for stakeholder reporting

V2: Same as V1 - no changes needed
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use

import os
from datetime import datetime
from collections import Counter


class VisualizationEngine:
    """Generates insight charts from mapping data"""

    def __init__(self, output_folder='outputs/insights'):
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)

        # Set style
        plt.style.use('seaborn-v0_8-whitegrid')
        self.colors = ['#00a8cc', '#00d4aa', '#ffa600', '#ff6b6b', '#845ec2', '#4b8bbe', '#f9c74f']

    def generate_topic_bar_chart(self, coverage_data, title="Questions per Topic Area"):
        """
        Generate bar chart showing question count per topic area

        Args:
            coverage_data (dict): {topic: count, ...}
            title (str): Chart title

        Returns:
            str: Path to saved PNG file
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        topics = list(coverage_data.keys())
        counts = list(coverage_data.values())

        # Sort by count descending
        sorted_pairs = sorted(zip(counts, topics), reverse=True)
        counts, topics = zip(*sorted_pairs) if sorted_pairs else ([], [])

        bars = ax.barh(topics, counts, color=self.colors[:len(topics)])

        # Add value labels
        for bar, count in zip(bars, counts):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                    str(count), va='center', fontsize=10, fontweight='bold')

        ax.set_xlabel('Number of Questions', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.invert_yaxis()

        plt.tight_layout()

        filename = f"topic_bar_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_folder, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()

        return filepath

    def generate_percentage_pie_chart(self, coverage_data, title="Topic Distribution (%)"):
        """
        Generate pie/donut chart showing percentage distribution

        Args:
            coverage_data (dict): {topic: count, ...}
            title (str): Chart title

        Returns:
            str: Path to saved PNG file
        """
        fig, ax = plt.subplots(figsize=(10, 8))

        topics = list(coverage_data.keys())
        counts = list(coverage_data.values())
        total = sum(counts) if counts else 1  # Avoid division by zero

        # Create labels with percentages
        labels = [f"{t}\n({c}, {c/total*100:.1f}%)" for t, c in zip(topics, counts)]

        # Donut chart
        wedges, texts = ax.pie(counts, labels=None, colors=self.colors[:len(topics)],
                               wedgeprops=dict(width=0.6), startangle=90)

        # Add legend
        ax.legend(wedges, labels, title="Topic Areas", loc="center left",
                  bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)

        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        # Center text
        ax.text(0, 0, f'Total\n{total}', ha='center', va='center', fontsize=16, fontweight='bold')

        plt.tight_layout()

        filename = f"topic_pie_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_folder, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()

        return filepath

    def generate_confidence_histogram(self, confidence_scores, title="Confidence Score Distribution"):
        """
        Generate histogram of confidence scores

        Args:
            confidence_scores (list): List of confidence values (0.0-1.0)
            title (str): Chart title

        Returns:
            str: Path to saved PNG file
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        # Define bins
        bins = [0, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0]
        bin_labels = ['<50%', '50-60%', '60-70%', '70-80%', '80-85%', '85-90%', '90-95%', '95-100%']

        # Create histogram
        counts, edges, patches = ax.hist(confidence_scores, bins=bins, edgecolor='white', linewidth=1.2)

        # Color code: red (<70%), yellow (70-85%), green (>85%)
        for i, patch in enumerate(patches):
            if edges[i] < 0.7:
                patch.set_facecolor('#ff6b6b')
            elif edges[i] < 0.85:
                patch.set_facecolor('#ffa600')
            else:
                patch.set_facecolor('#00d4aa')

        # Add count labels on bars
        for count, patch in zip(counts, patches):
            if count > 0:
                ax.text(patch.get_x() + patch.get_width()/2, patch.get_height() + 0.5,
                        int(count), ha='center', va='bottom', fontsize=10, fontweight='bold')

        ax.set_xlabel('Confidence Score', fontsize=12)
        ax.set_ylabel('Number of Questions', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#ff6b6b', label='Low (<70%)'),
            Patch(facecolor='#ffa600', label='Medium (70-85%)'),
            Patch(facecolor='#00d4aa', label='High (>85%)')
        ]
        ax.legend(handles=legend_elements, loc='upper left')

        # Stats annotation
        avg_conf = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        high_conf = sum(1 for c in confidence_scores if c >= 0.85)
        stats_text = f"Avg: {avg_conf:.1%} | High Confidence: {high_conf}/{len(confidence_scores)}"
        ax.text(0.98, 0.98, stats_text, transform=ax.transAxes, ha='right', va='top',
                fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()

        filename = f"confidence_histogram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_folder, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()

        return filepath

    def generate_gap_analysis_chart(self, coverage_data, reference_topics, title="Curriculum Coverage & Gaps"):
        """
        Generate chart highlighting topics with zero or low coverage

        Args:
            coverage_data (dict): {topic: count, ...}
            reference_topics (list): All possible topics from reference
            title (str): Chart title

        Returns:
            str: Path to saved PNG file
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        # Ensure all reference topics are included
        all_topics = {}
        for topic in reference_topics:
            all_topics[topic] = coverage_data.get(topic, 0)

        topics = list(all_topics.keys())
        counts = list(all_topics.values())

        # Sort by count
        sorted_pairs = sorted(zip(counts, topics))
        counts, topics = zip(*sorted_pairs) if sorted_pairs else ([], [])

        # Color based on coverage
        colors = []
        for count in counts:
            if count == 0:
                colors.append('#ff6b6b')  # Red - gap
            elif count <= 2:
                colors.append('#ffa600')  # Yellow - low coverage
            else:
                colors.append('#00d4aa')  # Green - good coverage

        bars = ax.barh(topics, counts, color=colors)

        # Add value labels
        for bar, count in zip(bars, counts):
            label = str(count) if count > 0 else 'GAP'
            color = 'white' if count == 0 else 'black'
            ax.text(max(bar.get_width(), 0.5), bar.get_y() + bar.get_height()/2,
                    label, va='center', fontsize=10, fontweight='bold', color=color)

        ax.set_xlabel('Number of Questions', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        # Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#ff6b6b', label='Gap (0 questions)'),
            Patch(facecolor='#ffa600', label='Low (1-2 questions)'),
            Patch(facecolor='#00d4aa', label='Good (3+ questions)')
        ]
        ax.legend(handles=legend_elements, loc='lower right')

        plt.tight_layout()

        filename = f"gap_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_folder, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()

        return filepath

    def generate_summary_dashboard(self, coverage_data, confidence_scores, reference_topics,
                                   title="Curriculum Mapping Summary"):
        """
        Generate a combined dashboard with multiple charts

        Args:
            coverage_data (dict): {topic: count, ...}
            confidence_scores (list): List of confidence values
            reference_topics (list): All possible topics
            title (str): Dashboard title

        Returns:
            str: Path to saved PNG file
        """
        fig = plt.figure(figsize=(16, 12))

        # Title
        fig.suptitle(title, fontsize=18, fontweight='bold', y=0.98)

        # 2x2 grid
        ax1 = fig.add_subplot(2, 2, 1)  # Bar chart
        ax2 = fig.add_subplot(2, 2, 2)  # Pie chart
        ax3 = fig.add_subplot(2, 2, 3)  # Confidence histogram
        ax4 = fig.add_subplot(2, 2, 4)  # Summary stats

        # 1. Bar chart
        topics = list(coverage_data.keys())
        counts = list(coverage_data.values())
        sorted_pairs = sorted(zip(counts, topics), reverse=True)
        if sorted_pairs:
            counts, topics = zip(*sorted_pairs)
            ax1.barh(topics, counts, color=self.colors[:len(topics)])
            ax1.set_xlabel('Questions')
            ax1.set_title('Questions per Topic', fontweight='bold')
            ax1.invert_yaxis()

        # 2. Pie chart
        if coverage_data:
            ax2.pie(list(coverage_data.values()), labels=list(coverage_data.keys()),
                    colors=self.colors[:len(coverage_data)], autopct='%1.1f%%', startangle=90)
            ax2.set_title('Topic Distribution', fontweight='bold')

        # 3. Confidence histogram
        if confidence_scores:
            bins = [0, 0.7, 0.85, 1.0]
            colors_hist = ['#ff6b6b', '#ffa600', '#00d4aa']
            ax3.hist(confidence_scores, bins=bins, color=self.colors[0], edgecolor='white')
            ax3.set_xlabel('Confidence Score')
            ax3.set_ylabel('Count')
            ax3.set_title('Confidence Distribution', fontweight='bold')

        # 4. Summary stats
        ax4.axis('off')
        total_questions = sum(coverage_data.values()) if coverage_data else 0
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        high_conf = sum(1 for c in confidence_scores if c >= 0.85)
        gaps = [t for t in reference_topics if coverage_data.get(t, 0) == 0]
        high_conf_pct = (high_conf / total_questions * 100) if total_questions > 0 else 0

        stats_text = f"""
        SUMMARY STATISTICS
        ─────────────────────────────
        Total Questions Mapped: {total_questions}
        Topics Covered: {len([t for t in coverage_data if coverage_data[t] > 0])} / {len(reference_topics)}

        Average Confidence: {avg_confidence:.1%}
        High Confidence (≥85%): {high_conf} ({high_conf_pct:.1f}%)

        Curriculum Gaps: {len(gaps)}
        {', '.join(gaps) if gaps else 'None'}
        """

        ax4.text(0.1, 0.9, stats_text, transform=ax4.transAxes, fontsize=12,
                 verticalalignment='top', fontfamily='monospace',
                 bbox=dict(boxstyle='round', facecolor='#f0f0f0', alpha=0.8))

        plt.tight_layout(rect=[0, 0, 1, 0.96])

        filename = f"summary_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_folder, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()

        return filepath

    def generate_coverage_table(self, coverage_data, reference_data, total_questions):
        """
        Generate coverage table data: Code → Definition → Mapped Questions → %

        Args:
            coverage_data (dict): {code: count, ...}
            reference_data (dict or list): Reference definitions
            total_questions (int): Total number of questions mapped

        Returns:
            list: [{code, definition, count, percentage}, ...]
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

            # Handle nested dict (for area_topics which may have subtopics)
            if isinstance(definition, dict):
                definition = definition.get('description', str(definition))

            percentage = round((count / total_questions * 100), 1) if total_questions > 0 else 0

            table_data.append({
                'code': code,
                'definition': str(definition)[:200] if definition else '',  # Truncate long definitions
                'count': count,
                'percentage': percentage
            })

        # Sort by count descending, gaps at the end
        table_data.sort(key=lambda x: (-x['count'], x['code']))

        return table_data

    def generate_all_insights(self, mapping_data, reference_topics, reference_definitions=None):
        """
        Generate all insight charts from mapping data

        Args:
            mapping_data (dict): Result from audit engine containing:
                - recommendations: list of mapping recommendations
                - coverage: dict of topic counts
            reference_topics (list): All possible topics from reference
            reference_definitions (dict): Optional - {code: definition, ...}

        Returns:
            dict: {chart_name: filepath, ..., coverage_table: [...]}
        """
        coverage = mapping_data.get('coverage', {})
        recommendations = mapping_data.get('recommendations', [])
        confidence_scores = [r.get('confidence', 0) for r in recommendations]
        total_questions = len(recommendations)

        charts = {}

        # Generate individual charts
        charts['topic_bar_chart'] = self.generate_topic_bar_chart(coverage)
        charts['topic_pie_chart'] = self.generate_percentage_pie_chart(coverage)
        charts['confidence_histogram'] = self.generate_confidence_histogram(confidence_scores)
        charts['gap_analysis'] = self.generate_gap_analysis_chart(coverage, reference_topics)
        charts['summary_dashboard'] = self.generate_summary_dashboard(
            coverage, confidence_scores, reference_topics
        )

        # Generate coverage table data
        ref_defs = reference_definitions or mapping_data.get('reference_definitions', {})
        if not ref_defs:
            # Create simple reference dict from topics list
            ref_defs = {topic: '' for topic in reference_topics}

        charts['coverage_table'] = self.generate_coverage_table(coverage, ref_defs, total_questions)

        return charts
