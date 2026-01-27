"""
Objectives Visualization Engine
Generates charts for Learning Objectives (O1-O6) mapping insights
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

import os
from datetime import datetime


# Objectives Reference
OBJECTIVES_REFERENCE = {
    'O1': 'Explain how microorganisms cause infection',
    'O2': 'Commensal, opportunistic & pathogenic organisms',
    'O3': 'Characteristics (morphology, resistance, virulence)',
    'O4': 'Host defense mechanisms',
    'O5': 'Laboratory diagnosis',
    'O6': 'Prophylaxis for infections'
}


class ObjectivesVizEngine:
    """Generates visualization charts for Objectives mapping"""

    def __init__(self, output_folder='outputs/insights'):
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)

        plt.style.use('seaborn-v0_8-whitegrid')
        self.colors = {
            'O1': '#00a8cc',
            'O2': '#00d4aa',
            'O3': '#ffa600',
            'O4': '#ff6b6b',
            'O5': '#845ec2',
            'O6': '#4b8bbe'
        }

    def generate_coverage_bar_chart(self, coverage_data):
        """
        Bar chart showing questions per objective

        Args:
            coverage_data (dict): {O1: count, O2: count, ...}

        Returns:
            str: Path to saved PNG
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        objectives = list(OBJECTIVES_REFERENCE.keys())
        counts = [coverage_data.get(obj, 0) for obj in objectives]
        labels = [f"{obj}\n{OBJECTIVES_REFERENCE[obj][:30]}..." for obj in objectives]
        colors = [self.colors[obj] for obj in objectives]

        bars = ax.bar(labels, counts, color=colors, edgecolor='white', linewidth=2)

        # Add count labels
        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    str(count), ha='center', va='bottom', fontsize=14, fontweight='bold')

        ax.set_ylabel('Number of Questions', fontsize=12)
        ax.set_title('Questions per Learning Objective', fontsize=16, fontweight='bold', pad=20)
        ax.set_ylim(0, max(counts) * 1.2 if counts else 10)

        plt.xticks(rotation=0, fontsize=10)
        plt.tight_layout()

        filename = f"objectives_coverage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_folder, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()

        return filepath

    def generate_distribution_pie(self, coverage_data):
        """
        Pie chart showing objective distribution

        Args:
            coverage_data (dict): {O1: count, ...}

        Returns:
            str: Path to saved PNG
        """
        fig, ax = plt.subplots(figsize=(10, 8))

        objectives = [obj for obj in OBJECTIVES_REFERENCE.keys() if coverage_data.get(obj, 0) > 0]
        counts = [coverage_data[obj] for obj in objectives]
        colors = [self.colors[obj] for obj in objectives]
        total = sum(counts)

        # Donut chart
        wedges, texts, autotexts = ax.pie(
            counts,
            colors=colors,
            autopct=lambda pct: f'{pct:.1f}%' if pct > 5 else '',
            pctdistance=0.75,
            wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2),
            startangle=90
        )

        # Legend
        legend_labels = [f"{obj}: {OBJECTIVES_REFERENCE[obj][:35]}... ({coverage_data.get(obj, 0)})"
                         for obj in objectives]
        ax.legend(wedges, legend_labels, title="Learning Objectives",
                  loc="center left", bbox_to_anchor=(1, 0.5), fontsize=9)

        ax.set_title('Objective Distribution', fontsize=16, fontweight='bold', pad=20)

        # Center text
        ax.text(0, 0, f'{total}\nQuestions', ha='center', va='center',
                fontsize=18, fontweight='bold')

        plt.tight_layout()

        filename = f"objectives_distribution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_folder, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()

        return filepath

    def generate_confidence_chart(self, confidence_scores):
        """
        Histogram of confidence scores

        Args:
            confidence_scores (list): List of confidence values 0.0-1.0

        Returns:
            str: Path to saved PNG
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        if not confidence_scores:
            confidence_scores = [0.85]

        bins = [0, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0]
        counts, edges, patches = ax.hist(confidence_scores, bins=bins,
                                          edgecolor='white', linewidth=1.5)

        # Color code by confidence level
        for i, patch in enumerate(patches):
            if edges[i] < 0.7:
                patch.set_facecolor('#ff6b6b')  # Low - Red
            elif edges[i] < 0.85:
                patch.set_facecolor('#ffa600')  # Medium - Orange
            else:
                patch.set_facecolor('#00d4aa')  # High - Green

        # Add count labels
        for count, patch in zip(counts, patches):
            if count > 0:
                ax.text(patch.get_x() + patch.get_width()/2, patch.get_height() + 0.3,
                        int(count), ha='center', va='bottom', fontsize=11, fontweight='bold')

        ax.set_xlabel('Confidence Score', fontsize=12)
        ax.set_ylabel('Number of Mappings', fontsize=12)
        ax.set_title('Mapping Confidence Distribution', fontsize=16, fontweight='bold', pad=20)

        # Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#ff6b6b', label='Low (<70%)'),
            Patch(facecolor='#ffa600', label='Medium (70-85%)'),
            Patch(facecolor='#00d4aa', label='High (>85%)')
        ]
        ax.legend(handles=legend_elements, loc='upper left')

        # Stats
        avg = sum(confidence_scores) / len(confidence_scores)
        high = sum(1 for c in confidence_scores if c >= 0.85)
        stats = f"Avg: {avg:.1%} | High Confidence: {high}/{len(confidence_scores)}"
        ax.text(0.98, 0.98, stats, transform=ax.transAxes, ha='right', va='top',
                fontsize=10, bbox=dict(boxstyle='round', facecolor='#f0f0f0', alpha=0.8))

        plt.tight_layout()

        filename = f"objectives_confidence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_folder, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()

        return filepath

    def generate_gap_analysis(self, coverage_data):
        """
        Gap analysis chart showing coverage vs gaps

        Args:
            coverage_data (dict): {O1: count, ...}

        Returns:
            str: Path to saved PNG
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        objectives = list(OBJECTIVES_REFERENCE.keys())
        counts = [coverage_data.get(obj, 0) for obj in objectives]
        labels = [f"{obj}" for obj in objectives]

        # Color by coverage level
        colors = []
        for count in counts:
            if count == 0:
                colors.append('#ff6b6b')  # Gap - Red
            elif count <= 3:
                colors.append('#ffa600')  # Low - Orange
            else:
                colors.append('#00d4aa')  # Good - Green

        bars = ax.barh(labels, counts, color=colors, edgecolor='white', linewidth=2)

        # Add labels and descriptions
        for i, (bar, count, obj) in enumerate(zip(bars, counts, objectives)):
            # Count or GAP label
            label = str(count) if count > 0 else 'GAP'
            color = 'black' if count > 0 else 'white'
            x_pos = max(bar.get_width(), 0.5) if count > 0 else 0.5
            ax.text(x_pos + 0.3, bar.get_y() + bar.get_height()/2,
                    label, va='center', fontsize=11, fontweight='bold', color=color)

            # Description on right
            ax.text(max(counts) + 2, bar.get_y() + bar.get_height()/2,
                    OBJECTIVES_REFERENCE[obj][:40] + '...',
                    va='center', fontsize=9, color='#666666')

        ax.set_xlabel('Number of Questions', fontsize=12)
        ax.set_title('Curriculum Coverage & Gap Analysis', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlim(0, max(counts) + 15 if counts else 15)

        # Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#ff6b6b', label='Gap (0 questions)'),
            Patch(facecolor='#ffa600', label='Low (1-3 questions)'),
            Patch(facecolor='#00d4aa', label='Good (4+ questions)')
        ]
        ax.legend(handles=legend_elements, loc='lower right')

        plt.tight_layout()

        filename = f"objectives_gaps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_folder, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()

        return filepath

    def generate_summary_dashboard(self, coverage_data, confidence_scores):
        """
        Combined dashboard with all key metrics

        Args:
            coverage_data (dict): {O1: count, ...}
            confidence_scores (list): Confidence values

        Returns:
            str: Path to saved PNG
        """
        fig = plt.figure(figsize=(16, 10))
        fig.suptitle('Objectives Mapping Summary Dashboard', fontsize=20, fontweight='bold', y=0.98)

        # 2x2 grid
        ax1 = fig.add_subplot(2, 2, 1)  # Bar chart
        ax2 = fig.add_subplot(2, 2, 2)  # Pie chart
        ax3 = fig.add_subplot(2, 2, 3)  # Confidence
        ax4 = fig.add_subplot(2, 2, 4)  # Summary stats

        # 1. Bar chart
        objectives = list(OBJECTIVES_REFERENCE.keys())
        counts = [coverage_data.get(obj, 0) for obj in objectives]
        colors = [self.colors[obj] for obj in objectives]

        ax1.bar(objectives, counts, color=colors, edgecolor='white')
        ax1.set_ylabel('Questions')
        ax1.set_title('Questions per Objective', fontweight='bold')
        for i, (obj, count) in enumerate(zip(objectives, counts)):
            ax1.text(i, count + 0.2, str(count), ha='center', fontweight='bold')

        # 2. Pie chart
        non_zero = [(obj, count) for obj, count in zip(objectives, counts) if count > 0]
        if non_zero:
            pie_labels, pie_counts = zip(*non_zero)
            pie_colors = [self.colors[obj] for obj in pie_labels]
            ax2.pie(pie_counts, labels=pie_labels, colors=pie_colors,
                    autopct='%1.0f%%', startangle=90)
            ax2.set_title('Distribution', fontweight='bold')

        # 3. Confidence histogram
        if confidence_scores:
            ax3.hist(confidence_scores, bins=[0, 0.7, 0.85, 1.0],
                     color='#00a8cc', edgecolor='white')
            ax3.set_xlabel('Confidence')
            ax3.set_ylabel('Count')
            ax3.set_title('Confidence Levels', fontweight='bold')

        # 4. Summary stats
        ax4.axis('off')
        total = sum(counts) if counts else 0
        avg_conf = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        high_conf = sum(1 for c in confidence_scores if c >= 0.85) if confidence_scores else 0
        gaps = [obj for obj in objectives if coverage_data.get(obj, 0) == 0]
        covered = len([obj for obj in objectives if coverage_data.get(obj, 0) > 0])
        high_conf_pct = (high_conf / total * 100) if total > 0 else 0

        stats_text = f"""
    SUMMARY STATISTICS
    {'='*40}

    Total Questions Mapped:  {total}
    Objectives Covered:      {covered} / 6

    Average Confidence:      {avg_conf:.1%}
    High Confidence (>85%):  {high_conf} ({high_conf_pct:.0f}% of total)

    Curriculum Gaps:         {len(gaps)}
    {', '.join(gaps) if gaps else 'None - Full coverage!'}
        """

        ax4.text(0.1, 0.9, stats_text, transform=ax4.transAxes, fontsize=11,
                 verticalalignment='top', fontfamily='monospace',
                 bbox=dict(boxstyle='round', facecolor='#f8f9fa', edgecolor='#dee2e6'))

        plt.tight_layout(rect=[0, 0, 1, 0.95])

        filename = f"objectives_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_folder, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()

        return filepath

    def generate_all_charts(self, insights_data):
        """
        Generate all insight charts

        Args:
            insights_data (dict): From ObjectivesEngine.get_insights_data()

        Returns:
            dict: {chart_name: filepath, ...}
        """
        coverage = insights_data.get('coverage', {})
        confidence = insights_data.get('confidence_scores', [])

        charts = {
            'coverage_bar': self.generate_coverage_bar_chart(coverage),
            'distribution_pie': self.generate_distribution_pie(coverage),
            'confidence_histogram': self.generate_confidence_chart(confidence),
            'gap_analysis': self.generate_gap_analysis(coverage),
            'summary_dashboard': self.generate_summary_dashboard(coverage, confidence)
        }

        return charts
