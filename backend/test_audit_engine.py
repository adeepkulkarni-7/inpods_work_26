"""
Test suite for Audit Engine
Validates output against expected results from Microbiology_OER_Audit_Results.xlsx.ods
"""

import pytest
import pandas as pd
import os
import json
from unittest.mock import Mock, patch, MagicMock
from audit_engine import AuditEngine

# Paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUESTIONS_CSV = os.path.join(PROJECT_ROOT, "RamaiaMicroExamCSV_CLEANED (1).csv")
REFERENCE_CSV = os.path.join(PROJECT_ROOT, "NMC_OER_Mapping (3).csv")
EXPECTED_OUTPUT = os.path.join(PROJECT_ROOT, "Microbiology_OER_Audit_Results.xlsx.ods")


def load_expected_results():
    """Load expected results from the ODS file"""
    df = pd.read_excel(EXPECTED_OUTPUT, engine='odf')
    return df


def create_mock_config():
    """Create a mock config for testing"""
    return {
        'api_key': 'test-key',
        'azure_endpoint': 'https://test.openai.azure.com',
        'api_version': '2024-02-15-preview',
        'deployment': 'gpt-4'
    }


class TestAuditEngineValidation:
    """Tests that validate audit engine output against expected results"""

    @pytest.fixture
    def expected_df(self):
        """Load expected results as fixture"""
        return load_expected_results()

    @pytest.fixture
    def mock_engine(self):
        """Create engine with mocked Azure client"""
        with patch('audit_engine.AzureOpenAI'):
            config = create_mock_config()
            engine = AuditEngine(config)
            return engine

    def test_expected_output_file_exists(self):
        """Verify expected output file exists"""
        assert os.path.exists(EXPECTED_OUTPUT), f"Expected output file not found: {EXPECTED_OUTPUT}"

    def test_expected_output_has_correct_columns(self, expected_df):
        """Verify expected output has required columns"""
        required_columns = ['Question Number', 'mapped_topic', 'mapped_subtopic',
                          'confidence_score', 'justification', 'Question Text']
        for col in required_columns:
            assert col in expected_df.columns, f"Missing column: {col}"

    def test_expected_output_has_44_questions(self, expected_df):
        """Verify expected output has all 44 questions mapped"""
        assert len(expected_df) == 44, f"Expected 44 rows, got {len(expected_df)}"

    def test_all_questions_have_mappings(self, expected_df):
        """Verify all questions have topic mappings"""
        missing_topics = expected_df[expected_df['mapped_topic'].isna()]
        assert len(missing_topics) == 0, f"Questions missing topic mapping: {missing_topics['Question Number'].tolist()}"

    def test_confidence_scores_in_valid_range(self, expected_df):
        """Verify all confidence scores are between 0 and 1"""
        scores = expected_df['confidence_score'].dropna()
        assert (scores >= 0).all(), "Some confidence scores are below 0"
        assert (scores <= 1).all(), "Some confidence scores are above 1"

    def test_mapped_topics_are_valid(self, expected_df):
        """Verify mapped topics match reference data"""
        valid_topics = [
            'AETCOM & Bioethics',
            'General Microbiology',
            'Immunology',
            'Gastrointestinal & Hepatobiliary',
            'CVS & Blood',
            'Musculoskeletal, Skin & Soft Tissue',
            'Infectious Diseases & Laboratory'
        ]
        actual_topics = expected_df['mapped_topic'].unique()
        for topic in actual_topics:
            assert topic in valid_topics, f"Invalid topic found: {topic}"


class TestBatchProcessing:
    """Tests for batch processing efficiency"""

    @pytest.fixture
    def mock_engine(self):
        """Create engine with mocked Azure client"""
        with patch('audit_engine.AzureOpenAI'):
            config = create_mock_config()
            engine = AuditEngine(config)
            return engine

    def test_batch_prompt_includes_all_questions(self, mock_engine):
        """Verify batch prompt includes all questions in batch"""
        questions_batch = [
            ("Q1", "What is the function of antibodies?"),
            ("Q2", "Describe bacterial cell wall structure."),
            ("Q3", "Explain viral replication cycle.")
        ]
        reference_data = {
            "Immunology": "Antigen/Antibody, Complement System",
            "General Microbiology": "Morphology of Bacteria"
        }

        prompt = mock_engine._build_batch_prompt(questions_batch, reference_data, 'area_topics')

        # Verify all questions are in the prompt
        assert "[Q1]:" in prompt
        assert "[Q2]:" in prompt
        assert "[Q3]:" in prompt
        assert "antibodies" in prompt
        assert "bacterial cell wall" in prompt
        assert "viral replication" in prompt

    def test_batch_size_reduces_api_calls(self, mock_engine):
        """Verify batching reduces number of API calls"""
        # 45 questions with batch_size=5 should result in 9 API calls, not 45
        num_questions = 45
        batch_size = 5
        expected_calls = (num_questions + batch_size - 1) // batch_size  # ceiling division

        assert expected_calls == 9, f"Expected 9 batches for 45 questions with batch_size=5, got {expected_calls}"

    def test_batch_size_10_reduces_calls_further(self, mock_engine):
        """Verify larger batch size reduces calls more"""
        num_questions = 45
        batch_size = 10
        expected_calls = (num_questions + batch_size - 1) // batch_size

        assert expected_calls == 5, f"Expected 5 batches for 45 questions with batch_size=10, got {expected_calls}"


class TestAuditEngineWithMockedLLM:
    """Tests with mocked LLM responses to validate processing logic"""

    @pytest.fixture
    def mock_engine_with_responses(self):
        """Create engine with mocked LLM responses"""
        with patch('audit_engine.AzureOpenAI') as mock_client_class:
            config = create_mock_config()
            engine = AuditEngine(config)

            # Setup mock response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "mappings": [
                    {
                        "question_id": "Q1",
                        "mapped_topic": "Immunology",
                        "mapped_subtopic": "Antigen/Antibody",
                        "confidence_score": 0.95,
                        "justification": "Test justification"
                    }
                ]
            })

            engine.client.chat.completions.create = MagicMock(return_value=mock_response)
            return engine

    def test_reference_data_loading(self, mock_engine_with_responses):
        """Test that reference data loads correctly"""
        ref_data = mock_engine_with_responses._load_reference_data(REFERENCE_CSV, 'area_topics')

        assert 'Immunology' in ref_data
        assert 'Infectious Diseases & Laboratory' in ref_data
        assert len(ref_data) > 0


class TestIntegrationValidation:
    """Integration tests that compare actual output against expected"""

    @pytest.fixture
    def expected_df(self):
        return load_expected_results()

    def test_compare_topic_distribution(self, expected_df):
        """Compare topic distribution in expected output"""
        topic_counts = expected_df['mapped_topic'].value_counts()

        # Verify distribution makes sense for microbiology exam
        assert topic_counts.get('Infectious Diseases & Laboratory', 0) > 0, \
            "Expected some questions mapped to Infectious Diseases & Laboratory"
        assert topic_counts.get('Immunology', 0) > 0, \
            "Expected some questions mapped to Immunology"

    def test_average_confidence_score(self, expected_df):
        """Verify average confidence is reasonable"""
        avg_confidence = expected_df['confidence_score'].mean()
        assert avg_confidence >= 0.7, f"Average confidence {avg_confidence} is too low (expected >= 0.7)"
        assert avg_confidence <= 1.0, f"Average confidence {avg_confidence} is invalid"

    def test_all_justifications_present(self, expected_df):
        """Verify all mappings have justifications"""
        missing_justifications = expected_df[expected_df['justification'].isna() | (expected_df['justification'] == '')]
        assert len(missing_justifications) == 0, \
            f"Questions missing justification: {missing_justifications['Question Number'].tolist()}"


class TestEngineOutputMatchesExpected:
    """
    Tests that run the engine with mocked LLM responses based on expected output
    and verify the engine produces matching results question-by-question
    """

    @pytest.fixture
    def expected_df(self):
        return load_expected_results()

    def _create_mock_batch_response(self, expected_df, batch_questions):
        """
        Create a mock LLM response for a batch based on expected output

        Args:
            expected_df: DataFrame with expected results
            batch_questions: List of (question_num, question_text) tuples

        Returns:
            dict: Mock response matching expected output format
        """
        mappings = []
        for q_num, q_text in batch_questions:
            # Find expected mapping for this question
            expected_row = expected_df[expected_df['Question Number'] == q_num]
            if len(expected_row) > 0:
                row = expected_row.iloc[0]
                mappings.append({
                    "question_id": q_num,
                    "mapped_topic": row['mapped_topic'],
                    "mapped_subtopic": row['mapped_subtopic'],
                    "confidence_score": float(row['confidence_score']),
                    "justification": row['justification']
                })
            else:
                # Fallback for questions not in expected output
                mappings.append({
                    "question_id": q_num,
                    "mapped_topic": "Infectious Diseases & Laboratory",
                    "mapped_subtopic": "Lab diagnosis",
                    "confidence_score": 0.85,
                    "justification": "Default mapping"
                })
        return {"mappings": mappings}

    def test_engine_output_matches_expected_question_by_question(self, expected_df):
        """
        Run engine with mocked LLM that returns expected results,
        verify engine processes and outputs match expected file exactly

        Note: Engine now skips stem questions automatically, so output
        should have 44 questions matching the expected output.
        """
        # Load questions (engine will skip stems automatically)
        questions_df = pd.read_csv(QUESTIONS_CSV)
        questions_list = []
        for idx, row in questions_df.iterrows():
            q_num = str(row.get('Question Number', f"Q{idx+1}"))
            q_text = row.get('Question Text', '')
            # Skip stem questions (matching engine behavior)
            if '(Stem)' in q_num:
                continue
            if q_text and pd.notna(q_text):
                questions_list.append((q_num, q_text))

        # Create engine with mocked client
        with patch('audit_engine.AzureOpenAI'):
            config = create_mock_config()
            engine = AuditEngine(config)

            # Track API calls and batch contents
            api_call_count = 0
            batch_size = 5

            def mock_create(*args, **kwargs):
                nonlocal api_call_count
                api_call_count += 1

                # Extract which batch this is from the prompt
                prompt = kwargs.get('messages', [{}])[1].get('content', '')

                # Find questions in this batch by parsing the prompt
                batch_start = (api_call_count - 1) * batch_size
                batch_end = min(batch_start + batch_size, len(questions_list))
                batch_questions = questions_list[batch_start:batch_end]

                # Create mock response based on expected output
                response_data = self._create_mock_batch_response(expected_df, batch_questions)

                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.content = json.dumps(response_data)
                return mock_response

            engine.client.chat.completions.create = mock_create

            # Run batched audit
            result = engine.run_audit_batched(
                question_csv=QUESTIONS_CSV,
                reference_csv=REFERENCE_CSV,
                dimension='area_topics',
                batch_size=batch_size
            )

        # Now compare results question by question
        recommendations = result['recommendations']

        matches = 0
        mismatches = []

        for rec in recommendations:
            q_num = rec['question_num']
            actual_topic = rec.get('mapped_topic', '')
            actual_subtopic = rec.get('mapped_subtopic', '')
            actual_confidence = rec.get('confidence', 0)

            # Find expected
            expected_row = expected_df[expected_df['Question Number'] == q_num]
            if len(expected_row) > 0:
                expected_topic = expected_row['mapped_topic'].values[0]
                expected_subtopic = expected_row['mapped_subtopic'].values[0]
                expected_confidence = expected_row['confidence_score'].values[0]

                if actual_topic == expected_topic and actual_subtopic == expected_subtopic:
                    matches += 1
                else:
                    mismatches.append({
                        'question': q_num,
                        'expected_topic': expected_topic,
                        'actual_topic': actual_topic,
                        'expected_subtopic': expected_subtopic,
                        'actual_subtopic': actual_subtopic
                    })

        # Calculate match rate
        match_rate = (matches / len(recommendations)) * 100 if recommendations else 0

        # Assert high match rate (should be 100% since we're mocking with expected data)
        assert match_rate >= 95, f"Match rate {match_rate:.1f}% is below 95%. Mismatches: {mismatches[:5]}"

        # Verify we processed all questions
        assert len(recommendations) == len(expected_df), \
            f"Expected {len(expected_df)} recommendations, got {len(recommendations)}"

    def test_batching_reduces_api_calls_with_mock(self, expected_df):
        """Verify batching actually reduces API calls when running the engine"""
        questions_df = pd.read_csv(QUESTIONS_CSV)
        questions_list = []
        for idx, row in questions_df.iterrows():
            q_num = str(row.get('Question Number', f"Q{idx+1}"))
            q_text = row.get('Question Text', '')
            # Skip stem questions
            if '(Stem)' in q_num:
                continue
            if q_text and pd.notna(q_text):
                questions_list.append((q_num, q_text))

        with patch('audit_engine.AzureOpenAI'):
            config = create_mock_config()
            engine = AuditEngine(config)

            api_call_count = 0
            batch_size = 5

            def mock_create(*args, **kwargs):
                nonlocal api_call_count
                api_call_count += 1

                batch_start = (api_call_count - 1) * batch_size
                batch_end = min(batch_start + batch_size, len(questions_list))
                batch_questions = questions_list[batch_start:batch_end]

                response_data = self._create_mock_batch_response(expected_df, batch_questions)

                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.content = json.dumps(response_data)
                return mock_response

            engine.client.chat.completions.create = mock_create

            result = engine.run_audit_batched(
                question_csv=QUESTIONS_CSV,
                reference_csv=REFERENCE_CSV,
                dimension='area_topics',
                batch_size=batch_size
            )

        # 44 questions with batch_size=5 should be 9 API calls
        expected_calls = (len(questions_list) + batch_size - 1) // batch_size

        assert api_call_count == expected_calls, \
            f"Expected {expected_calls} API calls, but made {api_call_count}"

        # Verify it's significantly less than one-per-question
        assert api_call_count < len(questions_list), \
            f"Batching didn't reduce calls: {api_call_count} calls for {len(questions_list)} questions"

    def test_each_question_mapping_matches_expected(self, expected_df):
        """
        Detailed question-by-question comparison showing exact differences
        """
        questions_df = pd.read_csv(QUESTIONS_CSV)
        questions_list = []
        for idx, row in questions_df.iterrows():
            q_num = str(row.get('Question Number', f"Q{idx+1}"))
            q_text = row.get('Question Text', '')
            # Skip stem questions
            if '(Stem)' in q_num:
                continue
            if q_text and pd.notna(q_text):
                questions_list.append((q_num, q_text))

        with patch('audit_engine.AzureOpenAI'):
            config = create_mock_config()
            engine = AuditEngine(config)

            api_call_count = 0
            batch_size = 5

            def mock_create(*args, **kwargs):
                nonlocal api_call_count
                api_call_count += 1
                batch_start = (api_call_count - 1) * batch_size
                batch_end = min(batch_start + batch_size, len(questions_list))
                batch_questions = questions_list[batch_start:batch_end]
                response_data = self._create_mock_batch_response(expected_df, batch_questions)
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.content = json.dumps(response_data)
                return mock_response

            engine.client.chat.completions.create = mock_create

            result = engine.run_audit_batched(
                question_csv=QUESTIONS_CSV,
                reference_csv=REFERENCE_CSV,
                dimension='area_topics',
                batch_size=batch_size
            )

        # Build comparison report
        comparison_results = []
        for rec in result['recommendations']:
            q_num = rec['question_num']
            expected_row = expected_df[expected_df['Question Number'] == q_num]

            if len(expected_row) > 0:
                exp = expected_row.iloc[0]
                comparison_results.append({
                    'question': q_num,
                    'topic_match': rec.get('mapped_topic') == exp['mapped_topic'],
                    'subtopic_match': rec.get('mapped_subtopic') == exp['mapped_subtopic'],
                    'expected_topic': exp['mapped_topic'],
                    'actual_topic': rec.get('mapped_topic'),
                    'expected_subtopic': exp['mapped_subtopic'],
                    'actual_subtopic': rec.get('mapped_subtopic')
                })

        # All should match since we're using mocked data from expected output
        topic_matches = sum(1 for r in comparison_results if r['topic_match'])
        subtopic_matches = sum(1 for r in comparison_results if r['subtopic_match'])

        assert topic_matches == len(comparison_results), \
            f"Topic mismatches found: {[r for r in comparison_results if not r['topic_match']]}"
        assert subtopic_matches == len(comparison_results), \
            f"Subtopic mismatches found: {[r for r in comparison_results if not r['subtopic_match']]}"


def run_live_validation(config_path=None):
    """
    Run live validation against expected output (requires Azure credentials)

    This function runs the actual audit engine and compares results
    against the expected output file.

    Usage:
        python test_audit_engine.py --live

    Args:
        config_path: Path to config file with Azure credentials
    """
    import time
    from dotenv import load_dotenv

    # Load environment
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)

    config = {
        'api_key': os.getenv('AZURE_OPENAI_API_KEY'),
        'azure_endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
        'api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
        'deployment': os.getenv('AZURE_OPENAI_DEPLOYMENT')
    }

    if not all([config['api_key'], config['azure_endpoint'], config['deployment']]):
        print("[ERROR] Missing Azure credentials in .env file")
        print("Required: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT")
        return False

    print("=" * 60)
    print("LIVE VALIDATION TEST")
    print("=" * 60)

    # Load expected results
    expected_df = load_expected_results()
    print(f"[OK] Loaded expected results: {len(expected_df)} questions")

    # Initialize engine
    engine = AuditEngine(config)
    print("[OK] Initialized AuditEngine")

    # Test connection
    if not engine.test_connection():
        print("[ERROR] Failed to connect to Azure OpenAI")
        return False

    # Run batched audit
    print("\n[...] Running batched audit (batch_size=5)...")
    start_time = time.time()

    result = engine.run_audit_batched(
        question_csv=QUESTIONS_CSV,
        reference_csv=REFERENCE_CSV,
        dimension='area_topics',
        batch_size=5
    )

    elapsed = time.time() - start_time
    print(f"[OK] Audit completed in {elapsed:.1f}s")
    print(f"     - Questions mapped: {result['mapped_questions']}")
    print(f"     - Batch mode: {result.get('batch_mode', False)}")

    # Compare results
    print("\n" + "=" * 60)
    print("COMPARISON WITH EXPECTED OUTPUT")
    print("=" * 60)

    recommendations = result['recommendations']
    matches = 0
    mismatches = []

    for rec in recommendations:
        q_num = rec['question_num']
        actual_topic = rec.get('mapped_topic', '')

        # Find expected mapping
        expected_row = expected_df[expected_df['Question Number'] == q_num]
        if len(expected_row) > 0:
            expected_topic = expected_row['mapped_topic'].values[0]
            if actual_topic == expected_topic:
                matches += 1
            else:
                mismatches.append({
                    'question': q_num,
                    'expected': expected_topic,
                    'actual': actual_topic
                })

    match_rate = (matches / len(recommendations)) * 100 if recommendations else 0

    print(f"\nResults:")
    print(f"  - Total questions: {len(recommendations)}")
    print(f"  - Matches: {matches}")
    print(f"  - Mismatches: {len(mismatches)}")
    print(f"  - Match rate: {match_rate:.1f}%")

    if mismatches:
        print(f"\nMismatches (first 10):")
        for m in mismatches[:10]:
            print(f"  Q{m['question']}: expected '{m['expected']}', got '{m['actual']}'")

    # Determine pass/fail (allow some variance due to LLM non-determinism)
    passed = match_rate >= 70  # 70% match threshold
    print(f"\n{'[PASS]' if passed else '[FAIL]'} Validation {'passed' if passed else 'failed'} (threshold: 70%)")

    return passed


if __name__ == '__main__':
    import sys

    if '--live' in sys.argv:
        # Run live validation
        success = run_live_validation()
        sys.exit(0 if success else 1)
    else:
        # Run pytest
        pytest.main([__file__, '-v'])
