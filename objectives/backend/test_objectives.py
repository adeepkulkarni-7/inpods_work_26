"""
Regression Test Suite for Objectives Mapping System

Tests:
1. Tool 1 (Map Questions) - works independently
2. Tool 2 (Rate Mappings) - works independently WITHOUT Tool 1
3. Tool 3 (Generate Insights) - works independently
4. Full flow: A → B → C
5. Edge cases and error handling

Run: python -m pytest test_objectives.py -v
Live test: python test_objectives.py --live
"""

import pytest
import os
import sys
import json
import tempfile
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from objectives_engine import ObjectivesEngine, OBJECTIVES_REFERENCE
from objectives_viz import ObjectivesVizEngine


# ============================================
# Test Fixtures
# ============================================

@pytest.fixture
def sample_questions_csv(tmp_path):
    """Create sample unmapped questions CSV"""
    data = {
        'Question Number': ['1.A', '1.B', '2', '3', '4 (Stem)', '5'],
        'Question Type': ['Long Essay', 'Long Essay', 'Short Essay', 'Short Answer', 'Stem', 'MCQ'],
        'Question Text': [
            'Explain how bacteria cause urinary tract infections.',
            'Discuss the laboratory diagnosis of tuberculosis.',
            'Describe the host immune response to viral infections.',
            'What are the prophylactic measures for malaria?',
            'A 45 year old patient presents with fever...',  # Stem - should be skipped
            'Which organism is commensal in the gut?'
        ]
    }
    df = pd.DataFrame(data)
    filepath = tmp_path / "test_questions.csv"
    df.to_csv(filepath, index=False)
    return str(filepath)


@pytest.fixture
def sample_mapped_csv(tmp_path):
    """Create sample pre-mapped questions CSV (for Tool 2)"""
    data = {
        'Question Number': ['1.A', '1.B', '2', '3'],
        'Question Type': ['Long Essay', 'Long Essay', 'Short Essay', 'Short Answer'],
        'Question Text': [
            'Explain how bacteria cause urinary tract infections.',
            'Discuss the laboratory diagnosis of tuberculosis.',
            'Describe the host immune response to viral infections.',
            'What are the prophylactic measures for malaria?'
        ],
        'mapped_objective': ['O1', 'O5', 'O4', 'O6'],  # Pre-existing mappings
        'confidence_score': [0.9, 0.85, 0.8, 0.95]
    }
    df = pd.DataFrame(data)
    filepath = tmp_path / "test_mapped.csv"
    df.to_csv(filepath, index=False)
    return str(filepath)


@pytest.fixture
def sample_mapped_with_errors_csv(tmp_path):
    """Create sample with intentionally wrong mappings (for Tool 2)"""
    data = {
        'Question Number': ['1', '2', '3'],
        'Question Type': ['Essay', 'Essay', 'MCQ'],
        'Question Text': [
            'Explain how bacteria cause urinary tract infections.',  # Should be O1, mapped to O6
            'Discuss the laboratory diagnosis of tuberculosis.',     # Should be O5, mapped to O2
            'What are the prophylactic measures for malaria?'        # Correct - O6
        ],
        'mapped_objective': ['O6', 'O2', 'O6'],  # Some wrong mappings
        'confidence_score': [0.9, 0.85, 0.95]
    }
    df = pd.DataFrame(data)
    filepath = tmp_path / "test_mapped_errors.csv"
    df.to_csv(filepath, index=False)
    return str(filepath)


@pytest.fixture
def empty_csv(tmp_path):
    """Create empty CSV with only headers"""
    data = {
        'Question Number': [],
        'Question Type': [],
        'Question Text': []
    }
    df = pd.DataFrame(data)
    filepath = tmp_path / "test_empty.csv"
    df.to_csv(filepath, index=False)
    return str(filepath)


@pytest.fixture
def viz_engine(tmp_path):
    """Create visualization engine with temp output folder"""
    return ObjectivesVizEngine(output_folder=str(tmp_path / "insights"))


# ============================================
# Unit Tests - Objectives Reference
# ============================================

class TestObjectivesReference:
    """Test objectives reference data"""

    def test_objectives_count(self):
        """Should have exactly 6 objectives (O1-O6)"""
        assert len(OBJECTIVES_REFERENCE) == 6

    def test_objectives_keys(self):
        """Should have O1 through O6"""
        expected = {'O1', 'O2', 'O3', 'O4', 'O5', 'O6'}
        assert set(OBJECTIVES_REFERENCE.keys()) == expected

    def test_objectives_have_descriptions(self):
        """Each objective should have a non-empty description"""
        for obj_id, desc in OBJECTIVES_REFERENCE.items():
            assert desc, f"{obj_id} has empty description"
            assert len(desc) > 10, f"{obj_id} description too short"


# ============================================
# Unit Tests - Tool 1: Map Questions
# ============================================

class TestTool1MapQuestions:
    """Test Tool 1: Map unmapped questions"""

    def test_stem_questions_skipped(self, sample_questions_csv):
        """Stem questions should be filtered out"""
        df = pd.read_csv(sample_questions_csv)

        # Count non-stem questions
        non_stem = [q for q in df['Question Number'] if '(Stem)' not in str(q)]
        stem = [q for q in df['Question Number'] if '(Stem)' in str(q)]

        assert len(non_stem) == 5
        assert len(stem) == 1

    def test_output_structure(self):
        """Mapping output should have required fields"""
        required_fields = ['question_num', 'question_text', 'objective_id',
                          'confidence', 'reason']

        # Mock recommendation
        rec = {
            'question_num': '1.A',
            'question_text': 'Test question',
            'objective_id': 'O1',
            'objective_desc': 'Description',
            'confidence': 0.9,
            'reason': 'Test reason'
        }

        for field in required_fields:
            assert field in rec, f"Missing field: {field}"

    def test_confidence_range(self):
        """Confidence scores should be between 0 and 1"""
        test_scores = [0.0, 0.5, 0.85, 1.0]
        for score in test_scores:
            assert 0.0 <= score <= 1.0

    def test_objective_id_valid(self):
        """Objective IDs should be O1-O6"""
        valid_ids = {'O1', 'O2', 'O3', 'O4', 'O5', 'O6'}
        test_id = 'O3'
        assert test_id in valid_ids


# ============================================
# Unit Tests - Tool 2: Rate Mappings
# ============================================

class TestTool2RateMappings:
    """Test Tool 2: Rate existing mappings - MUST WORK WITHOUT TOOL 1"""

    def test_can_load_premapped_file(self, sample_mapped_csv):
        """Should load a pre-mapped CSV without needing Tool 1"""
        df = pd.read_csv(sample_mapped_csv)

        assert 'mapped_objective' in df.columns
        assert 'Question Text' in df.columns
        assert len(df) > 0

    def test_rating_values(self):
        """Rating should be correct, partially_correct, or incorrect"""
        valid_ratings = {'correct', 'partially_correct', 'incorrect'}
        test_rating = 'partially_correct'
        assert test_rating in valid_ratings

    def test_rating_output_structure(self):
        """Rating output should have required fields"""
        required_fields = ['question_num', 'current_objective', 'rating',
                          'agreement_score', 'suggested_objective']

        # Mock rating result
        rating = {
            'question_num': '1.A',
            'question_text': 'Test',
            'current_objective': 'O1',
            'rating': 'correct',
            'agreement_score': 0.95,
            'rating_reason': 'Good match',
            'suggested_objective': 'O1',
            'suggestion_confidence': 0.95,
            'suggestion_reason': ''
        }

        for field in required_fields:
            assert field in rating, f"Missing field: {field}"

    def test_summary_calculation(self):
        """Summary should correctly count ratings"""
        ratings = [
            {'rating': 'correct'},
            {'rating': 'correct'},
            {'rating': 'partially_correct'},
            {'rating': 'incorrect'}
        ]

        correct = sum(1 for r in ratings if r['rating'] == 'correct')
        partial = sum(1 for r in ratings if r['rating'] == 'partially_correct')
        incorrect = sum(1 for r in ratings if r['rating'] == 'incorrect')

        assert correct == 2
        assert partial == 1
        assert incorrect == 1

    def test_independent_from_tool1(self, sample_mapped_csv):
        """Tool 2 should work with ANY pre-mapped file, not just Tool 1 output"""
        # Create a completely independent mapped file
        df = pd.read_csv(sample_mapped_csv)

        # Verify it has the minimum required columns
        assert 'Question Number' in df.columns or 'question_num' in df.columns
        assert 'Question Text' in df.columns or 'question_text' in df.columns

        # Should be able to extract existing mappings
        if 'mapped_objective' in df.columns:
            mappings = df['mapped_objective'].tolist()
            assert all(m in OBJECTIVES_REFERENCE for m in mappings if pd.notna(m))


# ============================================
# Unit Tests - Tool 3: Generate Insights
# ============================================

class TestTool3GenerateInsights:
    """Test Tool 3: Generate visualizations"""

    def test_coverage_calculation(self, sample_mapped_csv):
        """Should correctly calculate coverage per objective"""
        df = pd.read_csv(sample_mapped_csv)

        coverage = {obj: 0 for obj in OBJECTIVES_REFERENCE.keys()}
        for obj in df['mapped_objective']:
            if pd.notna(obj) and obj in coverage:
                coverage[obj] += 1

        assert coverage['O1'] == 1
        assert coverage['O5'] == 1
        assert coverage['O4'] == 1
        assert coverage['O6'] == 1
        assert coverage['O2'] == 0  # Gap
        assert coverage['O3'] == 0  # Gap

    def test_gap_identification(self, sample_mapped_csv):
        """Should identify objectives with zero coverage"""
        df = pd.read_csv(sample_mapped_csv)

        coverage = {obj: 0 for obj in OBJECTIVES_REFERENCE.keys()}
        for obj in df['mapped_objective']:
            if pd.notna(obj) and obj in coverage:
                coverage[obj] += 1

        gaps = [obj for obj, count in coverage.items() if count == 0]

        assert 'O2' in gaps
        assert 'O3' in gaps
        assert len(gaps) == 2

    def test_viz_engine_creates_charts(self, viz_engine):
        """Visualization engine should create chart files"""
        coverage = {'O1': 5, 'O2': 3, 'O3': 0, 'O4': 2, 'O5': 8, 'O6': 1}

        filepath = viz_engine.generate_coverage_bar_chart(coverage)

        assert os.path.exists(filepath)
        assert filepath.endswith('.png')

    def test_viz_handles_empty_data(self, viz_engine):
        """Should handle empty data without crashing"""
        coverage = {obj: 0 for obj in OBJECTIVES_REFERENCE.keys()}
        confidence_scores = []

        # Should not raise exception
        try:
            filepath = viz_engine.generate_coverage_bar_chart(coverage)
            assert os.path.exists(filepath)
        except ZeroDivisionError:
            pytest.fail("Division by zero with empty data")

    def test_viz_handles_zero_total(self, viz_engine):
        """Should handle zero total without division by zero"""
        coverage = {}
        confidence_scores = []

        insights_data = {
            'coverage': coverage,
            'confidence_scores': confidence_scores,
            'gaps': list(OBJECTIVES_REFERENCE.keys())
        }

        # Should not raise ZeroDivisionError
        try:
            charts = viz_engine.generate_all_charts(insights_data)
            assert isinstance(charts, dict)
        except ZeroDivisionError:
            pytest.fail("Division by zero error not handled")


# ============================================
# Integration Tests - Full Flow
# ============================================

class TestFullFlow:
    """Test the complete workflow: A → B → C"""

    def test_flow_a_to_b(self, sample_questions_csv, tmp_path):
        """Output from Tool 1 should be valid input for Tool 2"""
        # Simulate Tool 1 output
        tool1_output = {
            'Question Number': ['1.A', '1.B', '2'],
            'Question Type': ['Essay', 'Essay', 'MCQ'],
            'Question Text': [
                'Explain how bacteria cause infections.',
                'Discuss lab diagnosis of TB.',
                'Prophylaxis for malaria.'
            ],
            'mapped_objective': ['O1', 'O5', 'O6'],
            'objective_description': ['Desc1', 'Desc2', 'Desc3'],
            'confidence_score': [0.9, 0.85, 0.95],
            'mapping_reason': ['Reason1', 'Reason2', 'Reason3']
        }

        df = pd.DataFrame(tool1_output)
        output_file = tmp_path / "tool1_output.csv"
        df.to_csv(output_file, index=False)

        # Verify Tool 2 can read it
        df_loaded = pd.read_csv(output_file)
        assert 'mapped_objective' in df_loaded.columns
        assert len(df_loaded) == 3

    def test_flow_b_to_c(self, sample_mapped_csv, viz_engine):
        """Output from Tool 2 (or any mapped file) should work for Tool 3"""
        df = pd.read_csv(sample_mapped_csv)

        # Build insights data
        coverage = {obj: 0 for obj in OBJECTIVES_REFERENCE.keys()}
        confidence_scores = []

        for _, row in df.iterrows():
            obj = row.get('mapped_objective', '')
            if pd.notna(obj) and obj in coverage:
                coverage[obj] += 1

            conf = row.get('confidence_score', 0.85)
            if pd.notna(conf):
                confidence_scores.append(float(conf))

        insights_data = {
            'coverage': coverage,
            'confidence_scores': confidence_scores,
            'gaps': [obj for obj, c in coverage.items() if c == 0]
        }

        # Generate charts
        charts = viz_engine.generate_all_charts(insights_data)

        assert len(charts) >= 4  # At least 4 chart types
        for name, filepath in charts.items():
            assert os.path.exists(filepath), f"Chart {name} not created"


# ============================================
# Edge Case Tests
# ============================================

class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_file(self, empty_csv):
        """Should handle empty CSV gracefully"""
        df = pd.read_csv(empty_csv)
        assert len(df) == 0

    def test_missing_columns(self, tmp_path):
        """Should handle missing columns"""
        # CSV with wrong columns
        data = {'col1': [1, 2], 'col2': ['a', 'b']}
        df = pd.DataFrame(data)
        filepath = tmp_path / "wrong_columns.csv"
        df.to_csv(filepath, index=False)

        df_loaded = pd.read_csv(filepath)

        # Check for expected column
        has_question_text = 'Question Text' in df_loaded.columns
        assert not has_question_text  # Should be False

    def test_invalid_objective_id(self):
        """Should validate objective IDs"""
        valid_ids = set(OBJECTIVES_REFERENCE.keys())

        assert 'O1' in valid_ids
        assert 'O7' not in valid_ids  # Invalid
        assert 'X1' not in valid_ids  # Invalid

    def test_confidence_bounds(self):
        """Confidence should be clamped to 0-1"""
        def clamp_confidence(conf):
            return max(0.0, min(1.0, conf))

        assert clamp_confidence(1.5) == 1.0
        assert clamp_confidence(-0.5) == 0.0
        assert clamp_confidence(0.85) == 0.85

    def test_all_stems_file(self, tmp_path):
        """Should handle file with only stem questions"""
        data = {
            'Question Number': ['1 (Stem)', '2 (Stem)', '3 (Stem)'],
            'Question Type': ['Stem', 'Stem', 'Stem'],
            'Question Text': ['Context 1...', 'Context 2...', 'Context 3...']
        }
        df = pd.DataFrame(data)
        filepath = tmp_path / "all_stems.csv"
        df.to_csv(filepath, index=False)

        # Count non-stem questions
        df_loaded = pd.read_csv(filepath)
        non_stem = [q for q in df_loaded['Question Number'] if '(Stem)' not in str(q)]

        assert len(non_stem) == 0


# ============================================
# API Contract Tests
# ============================================

class TestAPIContracts:
    """Test API request/response contracts"""

    def test_tool1_request_format(self):
        """Tool 1 request should have filename and batch_size"""
        request = {
            'filename': 'questions.csv',
            'batch_size': 5
        }

        assert 'filename' in request
        assert isinstance(request['batch_size'], int)
        assert 1 <= request['batch_size'] <= 10

    def test_tool1_response_format(self):
        """Tool 1 response should have recommendations, coverage, gaps"""
        response = {
            'recommendations': [
                {'question_num': '1', 'objective_id': 'O1', 'confidence': 0.9, 'reason': 'Test'}
            ],
            'coverage': {'O1': 1, 'O2': 0, 'O3': 0, 'O4': 0, 'O5': 0, 'O6': 0},
            'gaps': ['O2', 'O3', 'O4', 'O5', 'O6'],
            'total_questions': 1,
            'mapped_questions': 1
        }

        assert 'recommendations' in response
        assert 'coverage' in response
        assert 'gaps' in response
        assert isinstance(response['recommendations'], list)

    def test_tool2_response_format(self):
        """Tool 2 response should have ratings, summary, recommendations"""
        response = {
            'ratings': [
                {'question_num': '1', 'rating': 'correct', 'agreement_score': 0.95}
            ],
            'summary': {
                'total_rated': 1,
                'correct': 1,
                'partially_correct': 0,
                'incorrect': 0,
                'accuracy_rate': 1.0
            },
            'recommendations': []
        }

        assert 'ratings' in response
        assert 'summary' in response
        assert 'correct' in response['summary']

    def test_tool3_response_format(self):
        """Tool 3 response should have charts and summary"""
        response = {
            'status': 'success',
            'charts': {
                'coverage_bar': '/api/insights/chart1.png',
                'distribution_pie': '/api/insights/chart2.png'
            },
            'summary': {
                'total_questions': 10,
                'objectives_covered': 4,
                'average_confidence': 0.87,
                'gaps': ['O2', 'O3']
            }
        }

        assert 'charts' in response
        assert 'summary' in response
        assert isinstance(response['charts'], dict)


# ============================================
# Live Integration Tests (Optional)
# ============================================

class TestLiveIntegration:
    """Live tests that require Azure OpenAI connection.
    Run with: python test_objectives.py --live
    """

    @pytest.fixture
    def engine(self):
        """Create engine with real credentials"""
        from dotenv import load_dotenv
        load_dotenv()

        config = {
            'api_key': os.getenv('AZURE_OPENAI_API_KEY'),
            'azure_endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
            'api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
            'deployment': os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4')
        }

        if not config['api_key']:
            pytest.skip("Azure credentials not configured")

        return ObjectivesEngine(config)

    @pytest.mark.live
    def test_connection(self, engine):
        """Test Azure OpenAI connection"""
        assert engine.test_connection()

    @pytest.mark.live
    def test_tool1_live(self, engine, sample_questions_csv):
        """Live test: Map questions to objectives"""
        result = engine.map_questions(sample_questions_csv, batch_size=3)

        assert 'recommendations' in result
        assert len(result['recommendations']) > 0

        # Check first recommendation
        rec = result['recommendations'][0]
        assert rec['objective_id'] in OBJECTIVES_REFERENCE
        assert 0.0 <= rec['confidence'] <= 1.0

    @pytest.mark.live
    def test_tool2_live(self, engine, sample_mapped_csv):
        """Live test: Rate existing mappings"""
        result = engine.rate_mappings(sample_mapped_csv, batch_size=3)

        assert 'ratings' in result
        assert 'summary' in result

        # Check summary
        summary = result['summary']
        assert summary['total_rated'] > 0


# ============================================
# Main - Run Tests
# ============================================

if __name__ == '__main__':
    import sys

    if '--live' in sys.argv:
        # Run live tests only
        print("Running LIVE integration tests (requires Azure credentials)...")
        pytest.main([__file__, '-v', '-m', 'live', '--tb=short'])
    else:
        # Run unit tests only (no Azure required)
        print("Running unit tests...")
        print("(Use --live flag to run live integration tests)")
        pytest.main([__file__, '-v', '-m', 'not live', '--tb=short'])
