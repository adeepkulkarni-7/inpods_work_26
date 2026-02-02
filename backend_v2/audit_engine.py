"""
Core Audit Engine V2
Dimension-agnostic curriculum mapping using Azure OpenAI

V2 Changes:
- Full question text preserved (no truncation)
- Cleaner tool-ready function interfaces
- Better structured outputs for agent integration
"""

from openai import AzureOpenAI
import pandas as pd
import json
from datetime import datetime
import os
import uuid


class AuditEngine:
    """
    Handles curriculum mapping audit across multiple dimensions.

    Designed as a tool provider for future AI agent integration.
    Each public method follows a clear input/output contract.
    """

    def __init__(self, config):
        """
        Initialize with Azure OpenAI config.

        Tool: initialize_audit_engine
        Inputs:
            config (dict): {
                'api_key': str,
                'azure_endpoint': str,
                'api_version': str,
                'deployment': str
            }
        Outputs:
            Initialized AuditEngine instance
        """
        self.config = config
        self.client = None
        self._initialize_client()

    def _get_full_question_text(self, row):
        """
        Get full question text including MCQ options if present.
        Combines question text with options A, B, C, D for MCQ questions.
        """
        question_text = row.get('Question Text', '')
        if pd.isna(question_text):
            question_text = ''
        question_text = str(question_text).strip()

        # Check for MCQ options and append them
        options = []
        for opt_label in ['option a', 'option b', 'option c', 'option d', 'Option A', 'Option B', 'Option C', 'Option D', 'A', 'B', 'C', 'D']:
            opt_value = row.get(opt_label, None)
            if opt_value is not None and pd.notna(opt_value) and str(opt_value).strip():
                # Normalize option label
                label = opt_label.upper().replace('OPTION ', '').strip()
                if len(label) == 1:
                    options.append(f"{label}. {str(opt_value).strip()}")

        if options:
            question_text = question_text + "\n" + "\n".join(options)

        return question_text

    def _initialize_client(self):
        """Initialize Azure OpenAI client"""
        try:
            self.client = AzureOpenAI(
                api_key=self.config["api_key"],
                azure_endpoint=self.config["azure_endpoint"],
                api_version=self.config["api_version"]
            )
        except Exception as e:
            print(f"Failed to initialize Azure OpenAI client: {e}")
            raise

    def test_connection(self):
        """
        Test Azure OpenAI connection.

        Tool: test_azure_connection
        Inputs: None
        Outputs: bool - True if connected, False otherwise
        """
        try:
            response = self.client.chat.completions.create(
                model=self.config["deployment"],
                messages=[{"role": "user", "content": "Respond with 'Connected'"}],
                max_tokens=5
            )
            status = response.choices[0].message.content.strip()
            print(f"[OK] Connection Status: {status}")
            return True
        except Exception as e:
            print(f"[ERROR] Connection Failed: {e}")
            return False

    def _load_reference_data(self, reference_csv, dimension):
        """
        Load reference definitions based on dimension.

        Tool: load_reference_data
        Inputs:
            reference_csv (str): Path to reference CSV or Excel file
            dimension (str): 'area_topics', 'competency', 'objective', 'skill', 'nmc_competency'
        Outputs:
            dict: Reference definitions keyed by topic/code
        """
        # Handle both CSV and Excel files
        if reference_csv.endswith('.csv'):
            df = pd.read_csv(reference_csv)
        elif reference_csv.endswith('.xlsx') or reference_csv.endswith('.xls'):
            df = pd.read_excel(reference_csv, engine='openpyxl')
        else:
            # Try CSV first, then Excel
            try:
                df = pd.read_csv(reference_csv)
            except:
                df = pd.read_excel(reference_csv, engine='openpyxl')

        if dimension == 'area_topics':
            reference = {}
            for _, row in df.iterrows():
                topic = row.get('Topic Area (CBME)', row.get('Topic Area', ''))
                subtopics = row.get('Subtopics Covered', '')
                if pd.notna(topic):
                    reference[topic] = subtopics
            return reference

        else:
            reference = {}
            for _, row in df.iterrows():
                id_val = None
                type_val = None
                desc_val = None

                if 'ID' in df.columns or 'Code' in df.columns:
                    id_val = row.get('ID', row.get('Code'))
                    type_val = row.get('Type', row.get('Category', ''))  # Support both Type and Category columns
                    desc_val = row.get('Description', row.get('Definition', ''))
                else:
                    for i, val in enumerate(row):
                        if pd.notna(val) and isinstance(val, str):
                            val_str = str(val).strip()
                            if len(val_str) == 2 and val_str[0] in ['C', 'O', 'S'] and val_str[1].isdigit():
                                id_val = val_str
                                if i + 1 < len(row):
                                    type_val = row.iloc[i + 1]
                                if i + 2 < len(row):
                                    desc_val = row.iloc[i + 2]
                                break

                if pd.notna(id_val) and isinstance(id_val, str):
                    id_str = str(id_val).strip()
                    if dimension == 'competency' and id_str.startswith('C'):
                        reference[id_str] = {'type': type_val, 'description': desc_val}
                    elif dimension == 'objective' and id_str.startswith('O'):
                        reference[id_str] = {'type': type_val, 'description': desc_val}
                    elif dimension == 'skill' and id_str.startswith('S'):
                        reference[id_str] = {'type': type_val, 'description': desc_val}
                    elif dimension == 'nmc_competency' and id_str.startswith('MI'):
                        reference[id_str] = {'type': type_val, 'description': desc_val}
                    elif dimension == 'blooms' and id_str.startswith('KL'):
                        reference[id_str] = {'type': type_val, 'description': desc_val}
                    elif dimension == 'complexity' and id_str in ['Easy', 'Medium', 'Hard']:
                        reference[id_str] = {'type': type_val, 'description': desc_val}

            return reference

    def _load_reference_data_multi(self, reference_csv, dimensions):
        """
        V2.1: Load reference definitions for multiple dimensions.

        Tool: load_reference_data_multi
        Inputs:
            reference_csv (str): Path to reference CSV or Excel file
            dimensions (list): List of dimension strings
        Outputs:
            dict: {dimension: {code: definition, ...}, ...}
        """
        all_reference = {}
        for dim in dimensions:
            all_reference[dim] = self._load_reference_data(reference_csv, dim)
        return all_reference

    def _build_multi_dimension_batch_prompt(self, questions_batch, reference_data_multi, dimensions):
        """
        V2.1: Build prompt for mapping to multiple dimensions at once.

        Args:
            questions_batch: List of (q_num, q_text) tuples
            reference_data_multi: Dict of {dimension: {code: data, ...}, ...}
            dimensions: List of dimension names to map
        Returns:
            str: Prompt text for LLM
        """
        questions_block = "\n\n".join([
            f"[{q_num}]: {q_text}"
            for q_num, q_text in questions_batch
        ])

        # Build reference sections for each dimension
        dimension_sections = []
        dimension_names = {
            'competency': 'Competency',
            'objective': 'Objective',
            'skill': 'Skill',
            'nmc_competency': 'NMC Competency',
            'area_topics': 'Topic Area',
            'blooms': 'Blooms Level',
            'complexity': 'Complexity Level'
        }

        for dim in dimensions:
            dim_data = reference_data_multi.get(dim, {})
            dim_name = dimension_names.get(dim, dim)

            if dim == 'area_topics':
                items = "\n".join([f"- {k}: {v}" for k, v in dim_data.items()])
            else:
                items = "\n".join([
                    f"- {k}: {v.get('description', '') if isinstance(v, dict) else v}"
                    for k, v in dim_data.items()
                ])
            dimension_sections.append(f"**{dim_name.upper()} ({dim})**:\n{items}")

        # Build JSON response template
        json_fields = []
        for dim in dimensions:
            if dim == 'area_topics':
                json_fields.append(f'            "{dim}_topic": "...",\n            "{dim}_subtopic": "...",\n            "{dim}_confidence": 0.XX')
            else:
                json_fields.append(f'            "{dim}": {{"code": "...", "confidence": 0.XX}}')

        json_template = ",\n".join(json_fields)

        prompt = f"""You are a curriculum mapping expert for medical education.

Map EACH question to the most appropriate code from EACH of the following dimensions:

{chr(10).join(dimension_sections)}

QUESTIONS:
{questions_block}

Respond in JSON format with an array of mappings:
{{
    "mappings": [
        {{
            "question_id": "Q1",
{json_template},
            "justification": "Brief reasoning for all mappings..."
        }},
        ...
    ]
}}

Rules:
- Include a mapping for EACH question in the same order
- For each dimension, choose the MOST relevant code
- confidence values must be between 0.0 and 1.0
- Keep justifications concise (1-2 sentences covering key dimensions)
"""
        return prompt

    def _build_mapping_prompt(self, question_text, reference_data, dimension):
        """Build prompt for single question LLM mapping"""
        if dimension == 'area_topics':
            topics_list = "\n".join([
                f"- {topic}: {subtopics}"
                for topic, subtopics in reference_data.items()
            ])

            prompt = f"""You are a curriculum mapping expert for medical education.

Map the following question to the most appropriate Topic Area and Subtopic from the NMC/OER curriculum.

QUESTION:
{question_text}

AVAILABLE TOPIC AREAS AND SUBTOPICS:
{topics_list}

Respond in JSON format:
{{
    "mapped_topic": "...",
    "mapped_subtopic": "...",
    "confidence_score": 0.XX,
    "justification": "Detailed reasoning for this mapping..."
}}

Rules:
- confidence_score must be between 0.0 and 1.0
- Choose the MOST specific and relevant topic/subtopic
- Provide clear justification based on question content
"""

        else:
            ids_list = "\n".join([
                f"- {id_key}: {data['description']}"
                for id_key, data in reference_data.items()
            ])

            dimension_name = {
                'competency': 'Competency',
                'objective': 'Objective',
                'skill': 'Skill',
                'nmc_competency': 'NMC Competency',
                'blooms': 'Blooms Level',
                'complexity': 'Complexity Level'
            }[dimension]

            prompt = f"""You are a curriculum mapping expert for medical education.

Map the following question to the most appropriate {dimension_name} from the curriculum framework.

QUESTION:
{question_text}

AVAILABLE {dimension_name.upper()}S:
{ids_list}

Respond in JSON format:
{{
    "mapped_id": "...",
    "confidence_score": 0.XX,
    "justification": "Detailed reasoning for this mapping..."
}}

Rules:
- confidence_score must be between 0.0 and 1.0
- Choose the MOST relevant {dimension_name}
- Provide clear justification based on question content
"""

        return prompt

    def _build_batch_prompt(self, questions_batch, reference_data, dimension):
        """Build prompt for batch of questions (token-efficient)"""
        questions_block = "\n\n".join([
            f"[{q_num}]: {q_text}"
            for q_num, q_text in questions_batch
        ])

        if dimension == 'area_topics':
            topics_list = "\n".join([
                f"- {topic}: {subtopics}"
                for topic, subtopics in reference_data.items()
            ])

            prompt = f"""You are a curriculum mapping expert for medical education.

Map EACH of the following questions to the most appropriate Topic Area and Subtopic from the NMC/OER curriculum.

QUESTIONS:
{questions_block}

AVAILABLE TOPIC AREAS AND SUBTOPICS:
{topics_list}

Respond in JSON format with an array of mappings:
{{
    "mappings": [
        {{
            "question_id": "Q1",
            "mapped_topic": "...",
            "mapped_subtopic": "...",
            "confidence_score": 0.XX,
            "justification": "Brief reasoning..."
        }},
        ...
    ]
}}

Rules:
- Include a mapping for EACH question in the same order
- confidence_score must be between 0.0 and 1.0
- Choose the MOST specific and relevant topic/subtopic for each
- Keep justifications concise (1-2 sentences)
"""
        else:
            ids_list = "\n".join([
                f"- {id_key}: {data['description']}"
                for id_key, data in reference_data.items()
            ])

            dimension_name = {
                'competency': 'Competency',
                'objective': 'Objective',
                'skill': 'Skill',
                'nmc_competency': 'NMC Competency',
                'blooms': 'Blooms Level',
                'complexity': 'Complexity Level'
            }[dimension]

            prompt = f"""You are a curriculum mapping expert for medical education.

Map EACH of the following questions to the most appropriate {dimension_name} from the curriculum framework.

QUESTIONS:
{questions_block}

AVAILABLE {dimension_name.upper()}S:
{ids_list}

Respond in JSON format with an array of mappings:
{{
    "mappings": [
        {{
            "question_id": "Q1",
            "mapped_id": "...",
            "confidence_score": 0.XX,
            "justification": "Brief reasoning..."
        }},
        ...
    ]
}}

Rules:
- Include a mapping for EACH question in the same order
- confidence_score must be between 0.0 and 1.0
- Choose the MOST relevant {dimension_name} for each
- Keep justifications concise (1-2 sentences)
"""

        return prompt

    def _call_llm(self, prompt, max_tokens=500):
        """
        Call Azure OpenAI with prompt.

        Tool: call_llm
        Inputs:
            prompt (str): The prompt text
            max_tokens (int): Maximum response tokens
        Outputs:
            tuple: (Parsed JSON response or None, token_usage dict)
        """
        try:
            response = self.client.chat.completions.create(
                model=self.config["deployment"],
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical education curriculum mapping expert. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content.strip()

            # Extract token usage
            token_usage = {
                'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                'total_tokens': response.usage.total_tokens if response.usage else 0
            }

            return json.loads(content), token_usage

        except Exception as e:
            print(f"LLM call failed: {e}")
            return None, {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}

    def run_audit(self, question_csv, reference_csv, dimension):
        """
        Run mapping audit (single question mode).

        Tool: run_mapping_audit
        Inputs:
            question_csv (str): Path to question CSV
            reference_csv (str): Path to reference CSV
            dimension (str): 'area_topics', 'competency', 'objective', 'skill'
        Outputs:
            dict: {
                'recommendations': list of mapping recommendations (full question text),
                'coverage': dict of topic/code counts,
                'gaps': list of topics/codes with no coverage,
                'dimension': str,
                'total_questions': int,
                'mapped_questions': int,
                'token_usage': dict with prompt_tokens, completion_tokens, total_tokens
            }
        """
        import time

        questions_df = pd.read_csv(question_csv)
        reference_data = self._load_reference_data(reference_csv, dimension)

        recommendations = []
        coverage_counts = {}

        # Track total token usage
        total_token_usage = {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'api_calls': 0
        }

        for idx, row in questions_df.iterrows():
            question_num = row.get('Question Number', f"Q{idx+1}")
            question_text = self._get_full_question_text(row)

            # Skip stem questions
            if '(Stem)' in str(question_num):
                continue

            if not question_text.strip():
                continue

            prompt = self._build_mapping_prompt(question_text, reference_data, dimension)
            llm_response, token_usage = self._call_llm(prompt)

            # Accumulate token usage
            total_token_usage['prompt_tokens'] += token_usage['prompt_tokens']
            total_token_usage['completion_tokens'] += token_usage['completion_tokens']
            total_token_usage['total_tokens'] += token_usage['total_tokens']
            total_token_usage['api_calls'] += 1

            if llm_response:
                if dimension == 'area_topics':
                    mapped_topic = llm_response.get('mapped_topic', '')
                    mapped_subtopic = llm_response.get('mapped_subtopic', '')
                    mapping_display = f"{mapped_topic} / {mapped_subtopic}"

                    coverage_counts[mapped_topic] = coverage_counts.get(mapped_topic, 0) + 1

                    recommendations.append({
                        'question_num': str(question_num),
                        'question_text': str(question_text),  # V2: Full text, no truncation
                        'current_mapping': None,
                        'recommended_mapping': mapping_display,
                        'mapped_topic': mapped_topic,
                        'mapped_subtopic': mapped_subtopic,
                        'confidence': llm_response.get('confidence_score', 0.0),
                        'justification': llm_response.get('justification', '')
                    })

                else:
                    mapped_id = llm_response.get('mapped_id', '')
                    coverage_counts[mapped_id] = coverage_counts.get(mapped_id, 0) + 1

                    recommendations.append({
                        'question_num': str(question_num),
                        'question_text': str(question_text),  # V2: Full text, no truncation
                        'current_mapping': None,
                        'recommended_mapping': mapped_id,
                        'mapped_id': mapped_id,
                        'confidence': llm_response.get('confidence_score', 0.0),
                        'justification': llm_response.get('justification', '')
                    })

            time.sleep(0.5)

        gaps = [key for key in reference_data.keys() if key not in coverage_counts]

        # Convert reference_data to a serializable format with definitions
        reference_definitions = {}
        for key, value in reference_data.items():
            if isinstance(value, dict):
                reference_definitions[key] = value.get('description', str(value))
            else:
                reference_definitions[key] = str(value) if value else ''

        print(f"[TOKEN] Total: {total_token_usage['total_tokens']} (Prompt: {total_token_usage['prompt_tokens']}, Completion: {total_token_usage['completion_tokens']}, API Calls: {total_token_usage['api_calls']})")

        return {
            'recommendations': recommendations,
            'coverage': coverage_counts,
            'gaps': gaps,
            'dimension': dimension,
            'total_questions': len(questions_df),
            'mapped_questions': len(recommendations),
            'reference_definitions': reference_definitions,
            'token_usage': total_token_usage
        }

    def run_audit_batched(self, question_csv, reference_csv, dimension, batch_size=5):
        """
        Run mapping audit with batching (60-70% token savings).

        Tool: run_mapping_audit_batched
        Inputs:
            question_csv (str): Path to question CSV
            reference_csv (str): Path to reference CSV
            dimension (str): 'area_topics', 'competency', 'objective', 'skill'
            batch_size (int): Questions per API call (1-10, default 5)
        Outputs:
            dict: Same as run_audit() plus batch_mode, batch_size, and token_usage fields
        """
        import time

        questions_df = pd.read_csv(question_csv)
        reference_data = self._load_reference_data(reference_csv, dimension)

        recommendations = []
        coverage_counts = {}

        # Track total token usage
        total_token_usage = {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'api_calls': 0
        }

        # Prepare questions list (skip stem questions)
        questions_list = []
        for idx, row in questions_df.iterrows():
            question_num = row.get('Question Number', f"Q{idx+1}")
            question_text = self._get_full_question_text(row)
            if '(Stem)' in str(question_num):
                continue
            if question_text.strip():
                questions_list.append((str(question_num), question_text))

        total_batches = (len(questions_list) + batch_size - 1) // batch_size
        print(f"[BATCH] Processing {len(questions_list)} questions in {total_batches} batches (batch_size={batch_size})")

        for batch_idx in range(0, len(questions_list), batch_size):
            batch = questions_list[batch_idx:batch_idx + batch_size]
            current_batch_num = (batch_idx // batch_size) + 1
            print(f"  [...] Processing batch {current_batch_num}/{total_batches}...")

            prompt = self._build_batch_prompt(batch, reference_data, dimension)

            try:
                response = self.client.chat.completions.create(
                    model=self.config["deployment"],
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a medical education curriculum mapping expert. Always respond with valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=2000,
                    response_format={"type": "json_object"}
                )

                # Track token usage for this batch
                if response.usage:
                    total_token_usage['prompt_tokens'] += response.usage.prompt_tokens
                    total_token_usage['completion_tokens'] += response.usage.completion_tokens
                    total_token_usage['total_tokens'] += response.usage.total_tokens
                total_token_usage['api_calls'] += 1

                content = response.choices[0].message.content.strip()
                batch_response = json.loads(content)
                mappings = batch_response.get('mappings', [])

                for i, mapping in enumerate(mappings):
                    if i < len(batch):
                        q_num, q_text = batch[i]

                        if dimension == 'area_topics':
                            mapped_topic = mapping.get('mapped_topic', '')
                            mapped_subtopic = mapping.get('mapped_subtopic', '')
                            mapping_display = f"{mapped_topic} / {mapped_subtopic}"

                            coverage_counts[mapped_topic] = coverage_counts.get(mapped_topic, 0) + 1

                            recommendations.append({
                                'question_num': q_num,
                                'question_text': q_text,  # V2: Full text
                                'current_mapping': None,
                                'recommended_mapping': mapping_display,
                                'mapped_topic': mapped_topic,
                                'mapped_subtopic': mapped_subtopic,
                                'confidence': mapping.get('confidence_score', 0.0),
                                'justification': mapping.get('justification', '')
                            })
                        else:
                            mapped_id = mapping.get('mapped_id', '')
                            coverage_counts[mapped_id] = coverage_counts.get(mapped_id, 0) + 1

                            recommendations.append({
                                'question_num': q_num,
                                'question_text': q_text,  # V2: Full text
                                'current_mapping': None,
                                'recommended_mapping': mapped_id,
                                'mapped_id': mapped_id,
                                'confidence': mapping.get('confidence_score', 0.0),
                                'justification': mapping.get('justification', '')
                            })

            except Exception as e:
                print(f"  [ERROR] Batch {current_batch_num} failed: {e}")
                # Fallback: process this batch one by one
                for q_num, q_text in batch:
                    prompt = self._build_mapping_prompt(q_text, reference_data, dimension)
                    llm_response, token_usage = self._call_llm(prompt)
                    # Track fallback token usage
                    total_token_usage['prompt_tokens'] += token_usage['prompt_tokens']
                    total_token_usage['completion_tokens'] += token_usage['completion_tokens']
                    total_token_usage['total_tokens'] += token_usage['total_tokens']
                    total_token_usage['api_calls'] += 1

                    if llm_response:
                        if dimension == 'area_topics':
                            mapped_topic = llm_response.get('mapped_topic', '')
                            mapped_subtopic = llm_response.get('mapped_subtopic', '')
                            mapping_display = f"{mapped_topic} / {mapped_subtopic}"
                            coverage_counts[mapped_topic] = coverage_counts.get(mapped_topic, 0) + 1
                            recommendations.append({
                                'question_num': q_num,
                                'question_text': q_text,
                                'current_mapping': None,
                                'recommended_mapping': mapping_display,
                                'mapped_topic': mapped_topic,
                                'mapped_subtopic': mapped_subtopic,
                                'confidence': llm_response.get('confidence_score', 0.0),
                                'justification': llm_response.get('justification', '')
                            })
                        else:
                            mapped_id = llm_response.get('mapped_id', '')
                            coverage_counts[mapped_id] = coverage_counts.get(mapped_id, 0) + 1
                            recommendations.append({
                                'question_num': q_num,
                                'question_text': q_text,
                                'current_mapping': None,
                                'recommended_mapping': mapped_id,
                                'mapped_id': mapped_id,
                                'confidence': llm_response.get('confidence_score', 0.0),
                                'justification': llm_response.get('justification', '')
                            })
                    time.sleep(0.5)

            time.sleep(1.0)

        gaps = [key for key in reference_data.keys() if key not in coverage_counts]

        print(f"[OK] Completed: {len(recommendations)} questions mapped")
        print(f"[TOKEN] Total: {total_token_usage['total_tokens']} (Prompt: {total_token_usage['prompt_tokens']}, Completion: {total_token_usage['completion_tokens']}, API Calls: {total_token_usage['api_calls']})")

        # Convert reference_data to a serializable format with definitions
        reference_definitions = {}
        for key, value in reference_data.items():
            if isinstance(value, dict):
                reference_definitions[key] = value.get('description', str(value))
            else:
                reference_definitions[key] = str(value) if value else ''

        return {
            'recommendations': recommendations,
            'coverage': coverage_counts,
            'gaps': gaps,
            'dimension': dimension,
            'total_questions': len(questions_df),
            'mapped_questions': len(recommendations),
            'batch_mode': True,
            'batch_size': batch_size,
            'reference_definitions': reference_definitions,
            'token_usage': total_token_usage
        }

    def run_audit_batched_multi(self, question_csv, reference_csv, dimensions, batch_size=5):
        """
        V2.1: Run mapping audit with multiple dimensions in a single API call per batch.

        Tool: run_mapping_audit_batched_multi
        Inputs:
            question_csv (str): Path to question CSV
            reference_csv (str): Path to reference CSV
            dimensions (list): List of dimension strings to map
            batch_size (int): Questions per API call (1-10, default 5)
        Outputs:
            dict: {
                'recommendations': list with multi-dimension mappings,
                'coverage': dict of code counts per dimension,
                'gaps': dict of gaps per dimension,
                'dimensions': list of dimensions used,
                'total_questions': int,
                'mapped_questions': int,
                'batch_mode': True,
                'batch_size': int,
                'reference_definitions': dict per dimension,
                'token_usage': dict
            }
        """
        import time

        questions_df = pd.read_csv(question_csv)

        # Load reference data for all dimensions
        reference_data_multi = self._load_reference_data_multi(reference_csv, dimensions)

        recommendations = []
        coverage_counts = {dim: {} for dim in dimensions}  # Per-dimension coverage

        # Track total token usage
        total_token_usage = {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'api_calls': 0
        }

        # Prepare questions list (skip stem questions)
        questions_list = []
        for idx, row in questions_df.iterrows():
            question_num = row.get('Question Number', f"Q{idx+1}")
            question_text = self._get_full_question_text(row)
            if '(Stem)' in str(question_num):
                continue
            if question_text.strip():
                questions_list.append((str(question_num), question_text))

        total_batches = (len(questions_list) + batch_size - 1) // batch_size
        dim_names = ', '.join(dimensions)
        print(f"[BATCH-MULTI] Processing {len(questions_list)} questions in {total_batches} batches")
        print(f"[BATCH-MULTI] Mapping to {len(dimensions)} dimensions: {dim_names}")

        for batch_idx in range(0, len(questions_list), batch_size):
            batch = questions_list[batch_idx:batch_idx + batch_size]
            current_batch_num = (batch_idx // batch_size) + 1
            print(f"  [...] Processing batch {current_batch_num}/{total_batches}...")

            prompt = self._build_multi_dimension_batch_prompt(batch, reference_data_multi, dimensions)

            # Calculate max tokens based on number of dimensions
            max_tokens = 2000 + (len(dimensions) * 500)  # More tokens for more dimensions

            try:
                response = self.client.chat.completions.create(
                    model=self.config["deployment"],
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a medical education curriculum mapping expert. Always respond with valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"}
                )

                # Track token usage for this batch
                if response.usage:
                    total_token_usage['prompt_tokens'] += response.usage.prompt_tokens
                    total_token_usage['completion_tokens'] += response.usage.completion_tokens
                    total_token_usage['total_tokens'] += response.usage.total_tokens
                total_token_usage['api_calls'] += 1

                content = response.choices[0].message.content.strip()
                batch_response = json.loads(content)
                mappings = batch_response.get('mappings', [])

                for i, mapping in enumerate(mappings):
                    if i < len(batch):
                        q_num, q_text = batch[i]

                        rec = {
                            'question_num': q_num,
                            'question_text': q_text,
                            'current_mapping': None,
                            'justification': mapping.get('justification', '')
                        }

                        # Extract mappings for each dimension
                        confidences = []
                        display_parts = []

                        for dim in dimensions:
                            if dim == 'area_topics':
                                topic = mapping.get(f'{dim}_topic', mapping.get('area_topics', {}).get('topic', ''))
                                subtopic = mapping.get(f'{dim}_subtopic', mapping.get('area_topics', {}).get('subtopic', ''))
                                conf = mapping.get(f'{dim}_confidence', mapping.get('area_topics', {}).get('confidence', 0.85))
                                rec[f'mapped_{dim}_topic'] = topic
                                rec[f'mapped_{dim}_subtopic'] = subtopic
                                rec['mapped_topic'] = topic
                                rec['mapped_subtopic'] = subtopic
                                if topic:
                                    coverage_counts[dim][topic] = coverage_counts[dim].get(topic, 0) + 1
                                    display_parts.append(topic)
                                confidences.append(float(conf) if conf else 0.85)
                            else:
                                dim_data = mapping.get(dim, {})
                                if isinstance(dim_data, dict):
                                    code = dim_data.get('code', '')
                                    conf = dim_data.get('confidence', 0.85)
                                else:
                                    code = str(dim_data) if dim_data else ''
                                    conf = 0.85
                                rec[f'mapped_{dim}'] = code
                                if code:
                                    coverage_counts[dim][code] = coverage_counts[dim].get(code, 0) + 1
                                    display_parts.append(code)
                                confidences.append(float(conf) if conf else 0.85)

                        # Calculate average confidence
                        rec['confidence'] = sum(confidences) / len(confidences) if confidences else 0.85
                        rec['recommended_mapping'] = ' | '.join(display_parts)

                        recommendations.append(rec)

            except Exception as e:
                print(f"  [ERROR] Batch {current_batch_num} failed: {e}")
                # Fallback: process questions individually with first dimension only
                for q_num, q_text in batch:
                    first_dim = dimensions[0]
                    prompt = self._build_mapping_prompt(q_text, reference_data_multi.get(first_dim, {}), first_dim)
                    llm_response, token_usage = self._call_llm(prompt)
                    total_token_usage['prompt_tokens'] += token_usage['prompt_tokens']
                    total_token_usage['completion_tokens'] += token_usage['completion_tokens']
                    total_token_usage['total_tokens'] += token_usage['total_tokens']
                    total_token_usage['api_calls'] += 1

                    if llm_response:
                        rec = {
                            'question_num': q_num,
                            'question_text': q_text,
                            'current_mapping': None,
                            'confidence': llm_response.get('confidence_score', 0.85),
                            'justification': llm_response.get('justification', '')
                        }
                        if first_dim == 'area_topics':
                            topic = llm_response.get('mapped_topic', '')
                            rec['mapped_topic'] = topic
                            rec['mapped_subtopic'] = llm_response.get('mapped_subtopic', '')
                            rec['recommended_mapping'] = topic
                            if topic:
                                coverage_counts[first_dim][topic] = coverage_counts[first_dim].get(topic, 0) + 1
                        else:
                            code = llm_response.get('mapped_id', '')
                            rec[f'mapped_{first_dim}'] = code
                            rec['recommended_mapping'] = code
                            if code:
                                coverage_counts[first_dim][code] = coverage_counts[first_dim].get(code, 0) + 1
                        recommendations.append(rec)
                    time.sleep(0.5)

            time.sleep(1.0)

        # Calculate gaps per dimension
        gaps = {}
        for dim in dimensions:
            dim_ref = reference_data_multi.get(dim, {})
            dim_coverage = coverage_counts.get(dim, {})
            gaps[dim] = [key for key in dim_ref.keys() if key not in dim_coverage]

        print(f"[OK] Completed: {len(recommendations)} questions mapped to {len(dimensions)} dimensions")
        print(f"[TOKEN] Total: {total_token_usage['total_tokens']} (Prompt: {total_token_usage['prompt_tokens']}, Completion: {total_token_usage['completion_tokens']}, API Calls: {total_token_usage['api_calls']})")

        # Build reference definitions for all dimensions
        reference_definitions = {}
        for dim in dimensions:
            for key, value in reference_data_multi.get(dim, {}).items():
                if isinstance(value, dict):
                    reference_definitions[key] = value.get('description', str(value))
                else:
                    reference_definitions[key] = str(value) if value else ''

        return {
            'recommendations': recommendations,
            'coverage': coverage_counts,
            'gaps': gaps,
            'dimensions': dimensions,
            'dimension': dimensions[0] if dimensions else None,  # Backward compat
            'total_questions': len(questions_df),
            'mapped_questions': len(recommendations),
            'batch_mode': True,
            'batch_size': batch_size,
            'reference_definitions': reference_definitions,
            'token_usage': total_token_usage
        }

    def apply_and_export(self, question_csv, recommendations, selected_indices, dimension, output_folder, dimensions=None):
        """
        Apply selected recommendations and export to Excel.

        Tool: apply_mappings_and_export
        Inputs:
            question_csv (str): Path to original question file (CSV, Excel, or ODS)
            recommendations (list): List of all recommendations
            selected_indices (list): Indices of accepted recommendations
            dimension (str): Dimension type (for backward compatibility)
            output_folder (str): Where to save output
            dimensions (list): V2.1 - Optional list of dimensions for multi-mapping
        Outputs:
            str: Path to output Excel file
        """
        # V2: Handle CSV, Excel, and ODS files
        if question_csv.endswith('.csv'):
            questions_df = pd.read_csv(question_csv)
        elif question_csv.endswith('.ods'):
            questions_df = pd.read_excel(question_csv, engine='odf')
        else:
            questions_df = pd.read_excel(question_csv, engine='openpyxl')

        for idx in selected_indices:
            if idx < len(recommendations):
                rec = recommendations[idx]
                question_num = rec['question_num']

                mask = questions_df['Question Number'].astype(str) == str(question_num)

                # V2.1: Handle multi-dimension mappings
                # Extract all mapped_* fields from the recommendation (except mapped_id which needs special handling)
                for key, value in rec.items():
                    if key.startswith('mapped_') and key != 'mapped_id' and value:
                        questions_df.loc[mask, key] = value

                # Handle mapped_id - convert to proper dimension column name
                if 'mapped_id' in rec and rec['mapped_id']:
                    # For single-dimension mapping, save to proper column name
                    if dimension and dimension != 'area_topics':
                        questions_df.loc[mask, f'mapped_{dimension}'] = rec['mapped_id']
                    elif not dimension and dimensions:
                        # Use first dimension from dimensions array
                        first_dim = dimensions[0] if dimensions else 'competency'
                        if first_dim != 'area_topics':
                            questions_df.loc[mask, f'mapped_{first_dim}'] = rec['mapped_id']

                # Backward compatibility for area_topics
                if dimension == 'area_topics' and 'mapped_topic' not in rec:
                    questions_df.loc[mask, 'mapped_topic'] = rec.get('mapped_topic', '')
                    questions_df.loc[mask, 'mapped_subtopic'] = rec.get('mapped_subtopic', '')

                questions_df.loc[mask, 'confidence_score'] = rec.get('confidence', 0.0)
                questions_df.loc[mask, 'justification'] = rec.get('justification', '')

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # V2.1: Include all dimensions in filename if multi-mapping
        if dimensions and len(dimensions) > 1:
            dim_suffix = '_'.join(dimensions[:3])  # Limit filename length
            if len(dimensions) > 3:
                dim_suffix += f'_plus{len(dimensions)-3}'
            output_filename = f"audit_output_multi_{dim_suffix}_{timestamp}.xlsx"
        else:
            output_filename = f"audit_output_{dimension}_{timestamp}.xlsx"

        output_path = os.path.join(output_folder, output_filename)

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            questions_df.to_excel(writer, sheet_name='Audit Results', index=False)

        return output_path

    def _build_batch_rating_prompt(self, questions_batch, reference_data, dimension):
        """Build prompt for rating a batch of existing mappings"""
        if dimension == 'area_topics':
            topics_list = "\n".join([
                f"- {topic}: {subtopics}"
                for topic, subtopics in reference_data.items()
            ])

            questions_block = "\n\n".join([
                f"[{q_num}]\nQuestion: {q_text}\nCurrent Mapping: {mapping.get('topic', 'Unknown')} / {mapping.get('subtopic', 'Unknown')}"
                for q_num, q_text, mapping in questions_batch
            ])

            prompt = f"""You are a curriculum mapping expert for medical education.

TASK: Evaluate EXISTING mappings for multiple questions. Rate each and suggest better mappings if needed.

QUESTIONS WITH CURRENT MAPPINGS:
{questions_block}

AVAILABLE TOPIC AREAS AND SUBTOPICS:
{topics_list}

Respond in JSON format:
{{
    "ratings": [
        {{
            "question_id": "...",
            "rating": "correct" | "partially_correct" | "incorrect",
            "agreement_score": 0.XX,
            "rating_justification": "Brief reason...",
            "suggested_topic": "...",
            "suggested_subtopic": "...",
            "suggestion_confidence": 0.XX,
            "suggestion_justification": "Brief reason if different..."
        }},
        ...
    ]
}}

Rules:
- Include a rating for EACH question
- agreement_score: 1.0 = perfect, 0.0 = wrong
- Keep justifications concise (1-2 sentences)
"""
        else:
            ids_list = "\n".join([
                f"- {id_key}: {data['description']}"
                for id_key, data in reference_data.items()
            ])

            dimension_name = {
                'competency': 'Competency',
                'objective': 'Objective',
                'skill': 'Skill',
                'nmc_competency': 'NMC Competency',
                'blooms': 'Blooms Level',
                'complexity': 'Complexity Level'
            }[dimension]

            questions_block = "\n\n".join([
                f"[{q_num}]\nQuestion: {q_text}\nCurrent Mapping: {mapping.get('id', 'Unknown')}"
                for q_num, q_text, mapping in questions_batch
            ])

            prompt = f"""You are a curriculum mapping expert for medical education.

TASK: Evaluate EXISTING {dimension_name} mappings. Rate each and suggest better if needed.

QUESTIONS WITH CURRENT MAPPINGS:
{questions_block}

AVAILABLE {dimension_name.upper()}S:
{ids_list}

Respond in JSON format:
{{
    "ratings": [
        {{
            "question_id": "...",
            "rating": "correct" | "partially_correct" | "incorrect",
            "agreement_score": 0.XX,
            "rating_justification": "Brief reason...",
            "suggested_id": "...",
            "suggestion_confidence": 0.XX,
            "suggestion_justification": "Brief reason if different..."
        }},
        ...
    ]
}}
"""

        return prompt

    def rate_existing_mappings(self, mapped_file, reference_csv, dimension, batch_size=5):
        """
        Rate existing mappings and suggest alternatives where needed.

        Tool: rate_existing_mappings
        Inputs:
            mapped_file (str): Path to file with existing mappings
            reference_csv (str): Path to reference CSV
            dimension (str): 'area_topics', 'competency', 'objective', 'skill'
            batch_size (int): Questions per API call
        Outputs:
            dict: {
                'ratings': list of all rating results,
                'summary': {correct, partially_correct, incorrect counts},
                'recommendations': list of non-correct mappings with suggestions,
                'dimension': str,
                'total_questions': int,
                'token_usage': dict with prompt_tokens, completion_tokens, total_tokens
            }
        """
        import time

        if mapped_file.endswith('.csv'):
            mapped_df = pd.read_csv(mapped_file)
        else:
            try:
                mapped_df = pd.read_excel(mapped_file, engine='openpyxl')
            except:
                mapped_df = pd.read_excel(mapped_file, engine='odf')

        reference_data = self._load_reference_data(reference_csv, dimension)

        # Track total token usage
        total_token_usage = {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'api_calls': 0
        }

        questions_list = []
        for idx, row in mapped_df.iterrows():
            q_num = str(row.get('Question Number', f"Q{idx+1}"))

            if '(Stem)' in q_num:
                continue

            q_text = row.get('Question Text', '')
            if not q_text or pd.isna(q_text):
                continue

            if dimension == 'area_topics':
                existing_mapping = {
                    'topic': row.get('mapped_topic', ''),
                    'subtopic': row.get('mapped_subtopic', '')
                }
            else:
                existing_mapping = {
                    'id': row.get(f'mapped_{dimension}', row.get('mapped_id', ''))
                }

            questions_list.append((q_num, str(q_text), existing_mapping))

        total_batches = (len(questions_list) + batch_size - 1) // batch_size
        print(f"[RATE] Rating {len(questions_list)} existing mappings in {total_batches} batches")

        all_ratings = []

        for batch_idx in range(0, len(questions_list), batch_size):
            batch = questions_list[batch_idx:batch_idx + batch_size]
            current_batch_num = (batch_idx // batch_size) + 1
            print(f"  [...] Processing batch {current_batch_num}/{total_batches}...")

            prompt = self._build_batch_rating_prompt(batch, reference_data, dimension)

            try:
                response = self.client.chat.completions.create(
                    model=self.config["deployment"],
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a medical education curriculum mapping expert. Always respond with valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=2500,
                    response_format={"type": "json_object"}
                )

                # Track token usage for this batch
                if response.usage:
                    total_token_usage['prompt_tokens'] += response.usage.prompt_tokens
                    total_token_usage['completion_tokens'] += response.usage.completion_tokens
                    total_token_usage['total_tokens'] += response.usage.total_tokens
                total_token_usage['api_calls'] += 1

                content = response.choices[0].message.content.strip()
                batch_response = json.loads(content)
                ratings = batch_response.get('ratings', [])

                for i, rating in enumerate(ratings):
                    if i < len(batch):
                        q_num, q_text, existing = batch[i]

                        rating_result = {
                            'question_num': q_num,
                            'question_text': q_text,  # V2: Full text
                            'existing_mapping': existing,
                            'rating': rating.get('rating', 'unknown'),
                            'agreement_score': rating.get('agreement_score', 0.0),
                            'rating_justification': rating.get('rating_justification', '')
                        }

                        if dimension == 'area_topics':
                            rating_result['suggested_topic'] = rating.get('suggested_topic', '')
                            rating_result['suggested_subtopic'] = rating.get('suggested_subtopic', '')
                            rating_result['suggested_mapping'] = f"{rating.get('suggested_topic', '')} / {rating.get('suggested_subtopic', '')}"
                        else:
                            rating_result['suggested_id'] = rating.get('suggested_id', '')
                            rating_result['suggested_mapping'] = rating.get('suggested_id', '')

                        rating_result['suggestion_confidence'] = rating.get('suggestion_confidence', 0.0)
                        rating_result['suggestion_justification'] = rating.get('suggestion_justification', '')

                        all_ratings.append(rating_result)

            except Exception as e:
                print(f"  [ERROR] Batch {current_batch_num} failed: {e}")

            time.sleep(1.0)

        correct_count = sum(1 for r in all_ratings if r['rating'] == 'correct')
        partial_count = sum(1 for r in all_ratings if r['rating'] == 'partially_correct')
        incorrect_count = sum(1 for r in all_ratings if r['rating'] == 'incorrect')
        avg_agreement = sum(r['agreement_score'] for r in all_ratings) / len(all_ratings) if all_ratings else 0

        summary = {
            'total_rated': len(all_ratings),
            'correct': correct_count,
            'partially_correct': partial_count,
            'incorrect': incorrect_count,
            'accuracy_rate': correct_count / len(all_ratings) if all_ratings else 0,
            'average_agreement_score': avg_agreement
        }

        recommendations = [
            {
                'question_num': r['question_num'],
                'question_text': r['question_text'],
                'current_mapping': r['existing_mapping'],
                'recommended_mapping': r['suggested_mapping'],
                'mapped_topic': r.get('suggested_topic', ''),
                'mapped_subtopic': r.get('suggested_subtopic', ''),
                'mapped_id': r.get('suggested_id', ''),
                'confidence': r['suggestion_confidence'],
                'justification': r['suggestion_justification'],
                'rating': r['rating'],
                'agreement_score': r['agreement_score']
            }
            for r in all_ratings if r['rating'] != 'correct'
        ]

        print(f"[OK] Rating complete: {correct_count} correct, {partial_count} partial, {incorrect_count} incorrect")
        print(f"[TOKEN] Total: {total_token_usage['total_tokens']} (Prompt: {total_token_usage['prompt_tokens']}, Completion: {total_token_usage['completion_tokens']}, API Calls: {total_token_usage['api_calls']})")

        # Convert reference_data to a serializable format with definitions
        reference_definitions = {}
        for key, value in reference_data.items():
            if isinstance(value, dict):
                reference_definitions[key] = value.get('description', str(value))
            else:
                reference_definitions[key] = str(value) if value else ''

        return {
            'ratings': all_ratings,
            'summary': summary,
            'recommendations': recommendations,
            'dimension': dimension,
            'total_questions': len(all_ratings),
            'token_usage': total_token_usage,
            'reference_definitions': reference_definitions
        }

    def _build_multi_dimension_rating_prompt(self, questions_batch, reference_data_multi, dimensions):
        """
        V2.1: Build prompt for rating multiple dimensions at once.

        Args:
            questions_batch: List of (q_num, q_text, existing_mappings_dict) tuples
            reference_data_multi: Dict of {dimension: {code: data, ...}, ...}
            dimensions: List of dimension names to rate
        Returns:
            str: Prompt text for LLM
        """
        dimension_names = {
            'competency': 'Competency',
            'objective': 'Objective',
            'skill': 'Skill',
            'nmc_competency': 'NMC Competency',
            'area_topics': 'Topic Area',
            'blooms': 'Blooms Level',
            'complexity': 'Complexity Level'
        }

        # Build reference sections for each dimension
        dimension_sections = []
        for dim in dimensions:
            dim_data = reference_data_multi.get(dim, {})
            dim_name = dimension_names.get(dim, dim)

            if dim == 'area_topics':
                items = "\n".join([f"- {k}: {v}" for k, v in dim_data.items()])
            else:
                items = "\n".join([
                    f"- {k}: {v.get('description', '') if isinstance(v, dict) else v}"
                    for k, v in dim_data.items()
                ])
            dimension_sections.append(f"**{dim_name.upper()} ({dim})**:\n{items}")

        # Build questions block with current mappings per dimension
        questions_lines = []
        for q_num, q_text, existing in questions_batch:
            mapping_lines = []
            for dim in dimensions:
                if dim == 'area_topics':
                    current = existing.get('area_topics_topic', existing.get('mapped_topic', 'Unknown'))
                else:
                    current = existing.get(f'mapped_{dim}', existing.get(dim, 'Unknown'))
                mapping_lines.append(f"  {dimension_names.get(dim, dim)}: {current}")
            questions_lines.append(f"[{q_num}]\nQuestion: {q_text}\nCurrent Mappings:\n" + "\n".join(mapping_lines))

        questions_block = "\n\n".join(questions_lines)

        # Build JSON response template
        dim_rating_fields = []
        for dim in dimensions:
            dim_rating_fields.append(f'''            "{dim}": {{
                "current": "...",
                "rating": "correct" | "partially_correct" | "incorrect",
                "suggested": "...",
                "confidence": 0.XX
            }}''')

        json_template = ",\n".join(dim_rating_fields)

        prompt = f"""You are a curriculum mapping expert for medical education.

TASK: Evaluate EXISTING mappings across multiple dimensions. Rate each dimension's mapping and suggest better alternatives if needed.

REFERENCE DATA:
{chr(10).join(dimension_sections)}

QUESTIONS WITH CURRENT MAPPINGS:
{questions_block}

Respond in JSON format:
{{
    "ratings": [
        {{
            "question_id": "Q1",
{json_template},
            "overall_rating": "correct" | "partially_correct" | "incorrect",
            "justification": "Brief reason covering key issues..."
        }},
        ...
    ]
}}

Rules:
- Include a rating for EACH question in the same order
- Rate EACH dimension separately: "correct", "partially_correct", or "incorrect"
- For incorrect mappings, provide a suggested alternative code
- confidence values must be between 0.0 and 1.0
- overall_rating should reflect the worst dimension rating
- Keep justifications concise (1-2 sentences)
"""
        return prompt

    def rate_existing_mappings_multi(self, mapped_file, reference_csv, dimensions, batch_size=5):
        """
        V2.1: Rate existing mappings across multiple dimensions.

        Tool: rate_existing_mappings_multi
        Inputs:
            mapped_file (str): Path to file with existing mappings
            reference_csv (str): Path to reference CSV
            dimensions (list): List of dimensions to rate
            batch_size (int): Questions per API call
        Outputs:
            dict: {
                'ratings': list of all rating results with per-dimension ratings,
                'summary': {correct, partially_correct, incorrect counts per dimension},
                'recommendations': list of questions needing corrections,
                'dimensions': list,
                'total_questions': int,
                'token_usage': dict
            }
        """
        import time

        if mapped_file.endswith('.csv'):
            mapped_df = pd.read_csv(mapped_file)
        else:
            try:
                mapped_df = pd.read_excel(mapped_file, engine='openpyxl')
            except:
                mapped_df = pd.read_excel(mapped_file, engine='odf')

        # Load reference data for all dimensions
        reference_data_multi = self._load_reference_data_multi(reference_csv, dimensions)

        # Track total token usage
        total_token_usage = {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'api_calls': 0
        }

        # Build questions list with existing mappings per dimension
        questions_list = []
        for idx, row in mapped_df.iterrows():
            q_num = str(row.get('Question Number', f"Q{idx+1}"))

            if '(Stem)' in q_num:
                continue

            q_text = row.get('Question Text', '')
            if not q_text or pd.isna(q_text):
                continue

            # Extract existing mappings for each dimension
            existing_mappings = {}
            for dim in dimensions:
                if dim == 'area_topics':
                    existing_mappings['mapped_topic'] = row.get('mapped_topic', '')
                    existing_mappings['mapped_subtopic'] = row.get('mapped_subtopic', '')
                else:
                    existing_mappings[f'mapped_{dim}'] = row.get(f'mapped_{dim}', row.get('mapped_id', ''))

            questions_list.append((q_num, str(q_text), existing_mappings))

        total_batches = (len(questions_list) + batch_size - 1) // batch_size
        dim_names = ', '.join(dimensions)
        print(f"[RATE-MULTI] Rating {len(questions_list)} mappings across {len(dimensions)} dimensions: {dim_names}")

        all_ratings = []

        for batch_idx in range(0, len(questions_list), batch_size):
            batch = questions_list[batch_idx:batch_idx + batch_size]
            current_batch_num = (batch_idx // batch_size) + 1
            print(f"  [...] Processing batch {current_batch_num}/{total_batches}...")

            prompt = self._build_multi_dimension_rating_prompt(batch, reference_data_multi, dimensions)

            # More tokens needed for multi-dimension response
            max_tokens = 2500 + (len(dimensions) * 300)

            try:
                response = self.client.chat.completions.create(
                    model=self.config["deployment"],
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a medical education curriculum mapping expert. Always respond with valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"}
                )

                if response.usage:
                    total_token_usage['prompt_tokens'] += response.usage.prompt_tokens
                    total_token_usage['completion_tokens'] += response.usage.completion_tokens
                    total_token_usage['total_tokens'] += response.usage.total_tokens
                total_token_usage['api_calls'] += 1

                content = response.choices[0].message.content.strip()
                batch_response = json.loads(content)
                ratings = batch_response.get('ratings', [])

                for i, rating in enumerate(ratings):
                    if i < len(batch):
                        q_num, q_text, existing = batch[i]

                        rating_result = {
                            'question_num': q_num,
                            'question_text': q_text,
                            'existing_mappings': existing,
                            'overall_rating': rating.get('overall_rating', 'unknown'),
                            'justification': rating.get('justification', ''),
                            'dimension_ratings': {}
                        }

                        # Extract per-dimension ratings
                        for dim in dimensions:
                            dim_rating = rating.get(dim, {})
                            if isinstance(dim_rating, dict):
                                rating_result['dimension_ratings'][dim] = {
                                    'current': dim_rating.get('current', existing.get(f'mapped_{dim}', '')),
                                    'rating': dim_rating.get('rating', 'unknown'),
                                    'suggested': dim_rating.get('suggested', ''),
                                    'confidence': dim_rating.get('confidence', 0.0)
                                }
                                # Also store flat for compatibility
                                if dim_rating.get('suggested'):
                                    rating_result[f'suggested_{dim}'] = dim_rating.get('suggested')
                                    rating_result[f'mapped_{dim}'] = dim_rating.get('suggested')

                        all_ratings.append(rating_result)

            except Exception as e:
                print(f"  [ERROR] Batch {current_batch_num} failed: {e}")

            time.sleep(1.0)

        # Calculate summary per dimension
        summary = {
            'total_rated': len(all_ratings),
            'per_dimension': {}
        }

        overall_correct = 0
        overall_partial = 0
        overall_incorrect = 0

        for dim in dimensions:
            correct = sum(1 for r in all_ratings if r['dimension_ratings'].get(dim, {}).get('rating') == 'correct')
            partial = sum(1 for r in all_ratings if r['dimension_ratings'].get(dim, {}).get('rating') == 'partially_correct')
            incorrect = sum(1 for r in all_ratings if r['dimension_ratings'].get(dim, {}).get('rating') == 'incorrect')
            summary['per_dimension'][dim] = {
                'correct': correct,
                'partially_correct': partial,
                'incorrect': incorrect
            }

        overall_correct = sum(1 for r in all_ratings if r['overall_rating'] == 'correct')
        overall_partial = sum(1 for r in all_ratings if r['overall_rating'] == 'partially_correct')
        overall_incorrect = sum(1 for r in all_ratings if r['overall_rating'] == 'incorrect')

        summary['correct'] = overall_correct
        summary['partially_correct'] = overall_partial
        summary['incorrect'] = overall_incorrect
        summary['accuracy_rate'] = overall_correct / len(all_ratings) if all_ratings else 0

        # Build recommendations (questions needing corrections in any dimension)
        recommendations = []
        for r in all_ratings:
            if r['overall_rating'] != 'correct':
                rec = {
                    'question_num': r['question_num'],
                    'question_text': r['question_text'],
                    'current_mapping': r['existing_mappings'],
                    'rating': r['overall_rating'],
                    'justification': r['justification'],
                    'dimension_ratings': r['dimension_ratings']
                }
                # Build recommended_mapping display
                suggested_parts = []
                for dim in dimensions:
                    dim_data = r['dimension_ratings'].get(dim, {})
                    if dim_data.get('rating') != 'correct' and dim_data.get('suggested'):
                        suggested_parts.append(dim_data['suggested'])
                        rec[f'mapped_{dim}'] = dim_data['suggested']
                    else:
                        # Keep existing if correct
                        existing_val = r['existing_mappings'].get(f'mapped_{dim}', '')
                        if existing_val:
                            suggested_parts.append(existing_val)
                            rec[f'mapped_{dim}'] = existing_val

                rec['recommended_mapping'] = ' | '.join(suggested_parts) if suggested_parts else ''
                rec['confidence'] = sum(
                    r['dimension_ratings'].get(dim, {}).get('confidence', 0)
                    for dim in dimensions
                ) / len(dimensions) if dimensions else 0

                recommendations.append(rec)

        print(f"[OK] Multi-dimension rating complete: {overall_correct} correct, {overall_partial} partial, {overall_incorrect} incorrect")
        print(f"[TOKEN] Total: {total_token_usage['total_tokens']}")

        # Build reference definitions for all dimensions
        reference_definitions = {}
        for dim in dimensions:
            for key, value in reference_data_multi.get(dim, {}).items():
                if isinstance(value, dict):
                    reference_definitions[key] = value.get('description', str(value))
                else:
                    reference_definitions[key] = str(value) if value else ''

        return {
            'ratings': all_ratings,
            'summary': summary,
            'recommendations': recommendations,
            'dimensions': dimensions,
            'dimension': dimensions[0] if dimensions else None,
            'total_questions': len(all_ratings),
            'token_usage': total_token_usage,
            'reference_definitions': reference_definitions
        }


# ============================================
# Library Manager - V2 Addition
# ============================================

class LibraryManager:
    """
    Manages persistent storage of mapping sets.

    Designed as a tool provider for future AI agent integration.
    """

    def __init__(self, library_folder):
        """
        Initialize library manager.

        Tool: initialize_library
        Inputs:
            library_folder (str): Path to library storage folder
        """
        self.library_folder = library_folder
        os.makedirs(library_folder, exist_ok=True)

    def save_mapping(self, name, recommendations, dimension, mode, source_file=''):
        """
        Save a mapping set to the library.

        Tool: save_mapping_to_library
        Inputs:
            name (str): Name for the mapping set
            recommendations (list): List of mapping recommendations
            dimension (str): Mapping dimension used
            mode (str): 'A' or 'B'
            source_file (str): Original source filename
        Outputs:
            dict: {id, name, created_at, question_count}
        """
        mapping_id = str(uuid.uuid4())[:8]

        library_data = {
            'id': mapping_id,
            'name': name,
            'created_at': datetime.now().isoformat(),
            'dimension': dimension,
            'mode': mode,
            'source_file': source_file,
            'question_count': len(recommendations),
            'recommendations': recommendations
        }

        filepath = os.path.join(self.library_folder, f'{mapping_id}.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(library_data, f, indent=2, ensure_ascii=False)

        return {
            'id': mapping_id,
            'name': name,
            'created_at': library_data['created_at'],
            'question_count': len(recommendations)
        }

    def list_mappings(self):
        """
        List all saved mapping sets.

        Tool: list_saved_mappings
        Inputs: None
        Outputs:
            list: Array of mapping summaries
        """
        mappings = []

        for filename in os.listdir(self.library_folder):
            if filename.endswith('.json'):
                filepath = os.path.join(self.library_folder, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        mappings.append({
                            'id': data.get('id'),
                            'name': data.get('name'),
                            'created_at': data.get('created_at'),
                            'question_count': data.get('question_count', 0),
                            'dimension': data.get('dimension'),
                            'mode': data.get('mode', 'A')
                        })
                except:
                    continue

        mappings.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return mappings

    def get_mapping(self, mapping_id):
        """
        Get a specific mapping set.

        Tool: get_library_mapping
        Inputs:
            mapping_id (str): The mapping ID
        Outputs:
            dict: Full mapping data or None if not found
        """
        filepath = os.path.join(self.library_folder, f'{mapping_id}.json')

        if not os.path.exists(filepath):
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def delete_mapping(self, mapping_id):
        """
        Delete a mapping set.

        Tool: delete_library_mapping
        Inputs:
            mapping_id (str): The mapping ID
        Outputs:
            bool: True if deleted, False if not found
        """
        filepath = os.path.join(self.library_folder, f'{mapping_id}.json')

        if not os.path.exists(filepath):
            return False

        os.remove(filepath)
        return True

    def export_to_excel(self, mapping_id, output_folder):
        """
        Export a mapping set to Excel.

        Tool: export_mapping_to_excel
        Inputs:
            mapping_id (str): The mapping ID
            output_folder (str): Where to save the Excel file
        Outputs:
            str: Path to exported file or None if not found
        """
        data = self.get_mapping(mapping_id)
        if not data:
            return None

        recommendations = data.get('recommendations', [])

        rows = []
        for rec in recommendations:
            rows.append({
                'Question Number': rec.get('question_num', ''),
                'Question Text': rec.get('question_text', ''),
                'Mapped Topic': rec.get('mapped_topic', rec.get('recommended_mapping', '')),
                'Mapped Subtopic': rec.get('mapped_subtopic', ''),
                'Confidence': rec.get('confidence', 0),
                'Justification': rec.get('justification', '')
            })

        df = pd.DataFrame(rows)

        safe_name = "".join(c for c in data.get('name', 'export') if c.isalnum() or c in (' ', '-', '_')).strip()
        output_filename = f"{safe_name}_{mapping_id}.xlsx"
        output_path = os.path.join(output_folder, output_filename)

        df.to_excel(output_path, index=False, engine='openpyxl')

        return output_path
