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

                if 'ID' in df.columns:
                    id_val = row.get('ID')
                    type_val = row.get('Type', row.get('Category', ''))  # Support both Type and Category columns
                    desc_val = row.get('Description')
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

            return reference

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
                'nmc_competency': 'NMC Competency'
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
                'nmc_competency': 'NMC Competency'
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
            dict: Parsed JSON response or None on error
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
            return json.loads(content)

        except Exception as e:
            print(f"LLM call failed: {e}")
            return None

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
                'mapped_questions': int
            }
        """
        import time

        questions_df = pd.read_csv(question_csv)
        reference_data = self._load_reference_data(reference_csv, dimension)

        recommendations = []
        coverage_counts = {}

        for idx, row in questions_df.iterrows():
            question_num = row.get('Question Number', f"Q{idx+1}")
            question_text = row.get('Question Text', '')

            # Skip stem questions
            if '(Stem)' in str(question_num):
                continue

            if not question_text or pd.isna(question_text):
                continue

            prompt = self._build_mapping_prompt(question_text, reference_data, dimension)
            llm_response = self._call_llm(prompt)

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

        return {
            'recommendations': recommendations,
            'coverage': coverage_counts,
            'gaps': gaps,
            'dimension': dimension,
            'total_questions': len(questions_df),
            'mapped_questions': len(recommendations)
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
            dict: Same as run_audit() plus batch_mode and batch_size fields
        """
        import time

        questions_df = pd.read_csv(question_csv)
        reference_data = self._load_reference_data(reference_csv, dimension)

        recommendations = []
        coverage_counts = {}

        # Prepare questions list (skip stem questions)
        questions_list = []
        for idx, row in questions_df.iterrows():
            question_num = row.get('Question Number', f"Q{idx+1}")
            question_text = row.get('Question Text', '')
            if '(Stem)' in str(question_num):
                continue
            if question_text and pd.notna(question_text):
                questions_list.append((str(question_num), str(question_text)))

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
                    llm_response = self._call_llm(prompt)
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

        return {
            'recommendations': recommendations,
            'coverage': coverage_counts,
            'gaps': gaps,
            'dimension': dimension,
            'total_questions': len(questions_df),
            'mapped_questions': len(recommendations),
            'batch_mode': True,
            'batch_size': batch_size
        }

    def apply_and_export(self, question_csv, recommendations, selected_indices, dimension, output_folder):
        """
        Apply selected recommendations and export to Excel.

        Tool: apply_mappings_and_export
        Inputs:
            question_csv (str): Path to original question file (CSV, Excel, or ODS)
            recommendations (list): List of all recommendations
            selected_indices (list): Indices of accepted recommendations
            dimension (str): Dimension type
            output_folder (str): Where to save output
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

                if dimension == 'area_topics':
                    questions_df.loc[mask, 'mapped_topic'] = rec.get('mapped_topic', '')
                    questions_df.loc[mask, 'mapped_subtopic'] = rec.get('mapped_subtopic', '')
                else:
                    questions_df.loc[mask, f'mapped_{dimension}'] = rec.get('mapped_id', '')

                questions_df.loc[mask, 'confidence_score'] = rec.get('confidence', 0.0)
                questions_df.loc[mask, 'justification'] = rec.get('justification', '')

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
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
                'nmc_competency': 'NMC Competency'
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
                'total_questions': int
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

        return {
            'ratings': all_ratings,
            'summary': summary,
            'recommendations': recommendations,
            'dimension': dimension,
            'total_questions': len(all_ratings)
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
