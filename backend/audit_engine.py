"""
Core Audit Engine
Dimension-agnostic curriculum mapping using Azure OpenAI
"""

from openai import AzureOpenAI
import pandas as pd
import json
from datetime import datetime
import os


class AuditEngine:
    """Handles curriculum mapping audit across multiple dimensions"""
    
    def __init__(self, config):
        """
        Initialize with Azure OpenAI config
        
        Args:
            config (dict): {
                'api_key': str,
                'azure_endpoint': str,
                'api_version': str,
                'deployment': str
            }
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
        """Test Azure OpenAI connection"""
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
        Load reference definitions based on dimension
        
        Args:
            reference_csv (str): Path to reference CSV
            dimension (str): 'area_topics', 'competency', 'objective', 'skill'
        
        Returns:
            dict: Reference definitions
        """
        df = pd.read_csv(reference_csv)
        
        if dimension == 'area_topics':
            # Format: Topic Area, Subtopics Covered
            reference = {}
            for _, row in df.iterrows():
                topic = row.get('Topic Area (CBME)', row.get('Topic Area', ''))
                subtopics = row.get('Subtopics Covered', '')
                if pd.notna(topic):
                    reference[topic] = subtopics
            return reference
        
        else:
            # Format: ID, Type, Description (for C*, O*, S*)
            # Handle various CSV formats where columns may be in different positions
            reference = {}

            for _, row in df.iterrows():
                id_val = None
                type_val = None
                desc_val = None

                # Try standard column names first
                if 'ID' in df.columns:
                    id_val = row.get('ID')
                    type_val = row.get('Type')
                    desc_val = row.get('Description')
                else:
                    # Search all columns for ID pattern (C1, O1, S1, etc.)
                    for i, val in enumerate(row):
                        if pd.notna(val) and isinstance(val, str):
                            val_str = str(val).strip()
                            # Check if this looks like an ID (C1-C9, O1-O9, S1-S9)
                            if len(val_str) == 2 and val_str[0] in ['C', 'O', 'S'] and val_str[1].isdigit():
                                id_val = val_str
                                # Type is next column, Description is the one after
                                if i + 1 < len(row):
                                    type_val = row.iloc[i + 1]
                                if i + 2 < len(row):
                                    desc_val = row.iloc[i + 2]
                                break

                if pd.notna(id_val) and isinstance(id_val, str):
                    id_str = str(id_val).strip()
                    if dimension == 'competency' and id_str.startswith('C'):
                        reference[id_str] = {
                            'type': type_val,
                            'description': desc_val
                        }
                    elif dimension == 'objective' and id_str.startswith('O'):
                        reference[id_str] = {
                            'type': type_val,
                            'description': desc_val
                        }
                    elif dimension == 'skill' and id_str.startswith('S'):
                        reference[id_str] = {
                            'type': type_val,
                            'description': desc_val
                        }

            return reference
    
    def _build_mapping_prompt(self, question_text, reference_data, dimension):
        """
        Build prompt for LLM mapping
        
        Args:
            question_text (str): The question to map
            reference_data (dict): Reference definitions
            dimension (str): Dimension type
        
        Returns:
            str: Formatted prompt
        """
        if dimension == 'area_topics':
            # Build topic/subtopic mapping prompt
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
            # Build C*/O*/S* mapping prompt
            ids_list = "\n".join([
                f"- {id_key}: {data['description']}"
                for id_key, data in reference_data.items()
            ])
            
            dimension_name = {
                'competency': 'Competency',
                'objective': 'Objective',
                'skill': 'Skill'
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
        """
        Build prompt for batch of questions (token-efficient)

        Args:
            questions_batch (list): List of (question_num, question_text) tuples
            reference_data (dict): Reference definitions
            dimension (str): Dimension type

        Returns:
            str: Formatted prompt for batch processing
        """
        # Build questions block
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
                'skill': 'Skill'
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

    def _call_llm(self, prompt):
        """
        Call Azure OpenAI with prompt
        
        Args:
            prompt (str): The prompt
        
        Returns:
            dict: Parsed JSON response
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
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            return json.loads(content)
        
        except Exception as e:
            print(f"LLM call failed: {e}")
            return None
    
    def run_audit(self, question_csv, reference_csv, dimension):
        """
        Run mapping audit
        
        Args:
            question_csv (str): Path to question CSV
            reference_csv (str): Path to reference CSV
            dimension (str): 'area_topics', 'competency', 'objective', 'skill'
        
        Returns:
            dict: {
                'recommendations': [...],
                'coverage': {...},
                'gaps': [...]
            }
        """
        # Load data
        questions_df = pd.read_csv(question_csv)
        reference_data = self._load_reference_data(reference_csv, dimension)
        
        recommendations = []
        coverage_counts = {}
        
        # Process each question
        for idx, row in questions_df.iterrows():
            question_num = row.get('Question Number', f"Q{idx+1}")
            question_text = row.get('Question Text', '')

            # Skip stem questions (context-setting, no mapping needed)
            if '(Stem)' in str(question_num):
                continue

            if not question_text or pd.isna(question_text):
                continue
            
            # Build prompt and call LLM
            prompt = self._build_mapping_prompt(question_text, reference_data, dimension)
            llm_response = self._call_llm(prompt)
            
            if llm_response:
                if dimension == 'area_topics':
                    mapped_topic = llm_response.get('mapped_topic', '')
                    mapped_subtopic = llm_response.get('mapped_subtopic', '')
                    mapping_display = f"{mapped_topic} / {mapped_subtopic}"
                    
                    # Track coverage
                    if mapped_topic in coverage_counts:
                        coverage_counts[mapped_topic] += 1
                    else:
                        coverage_counts[mapped_topic] = 1
                    
                    recommendations.append({
                        'question_num': str(question_num),
                        'question_text': question_text[:100] + '...' if len(question_text) > 100 else question_text,
                        'current_mapping': None,  # Could extract from existing columns if present
                        'recommended_mapping': mapping_display,
                        'mapped_topic': mapped_topic,
                        'mapped_subtopic': mapped_subtopic,
                        'confidence': llm_response.get('confidence_score', 0.0),
                        'justification': llm_response.get('justification', '')
                    })
                
                else:
                    mapped_id = llm_response.get('mapped_id', '')
                    
                    # Track coverage
                    if mapped_id in coverage_counts:
                        coverage_counts[mapped_id] += 1
                    else:
                        coverage_counts[mapped_id] = 1
                    
                    recommendations.append({
                        'question_num': str(question_num),
                        'question_text': question_text[:100] + '...' if len(question_text) > 100 else question_text,
                        'current_mapping': None,
                        'recommended_mapping': mapped_id,
                        'mapped_id': mapped_id,
                        'confidence': llm_response.get('confidence_score', 0.0),
                        'justification': llm_response.get('justification', '')
                    })
            
            # Rate limiting - small delay
            import time
            time.sleep(0.5)
        
        # Identify gaps (reference items with 0 coverage)
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
        Run mapping audit with batching (60-70% token savings)

        Args:
            question_csv (str): Path to question CSV
            reference_csv (str): Path to reference CSV
            dimension (str): 'area_topics', 'competency', 'objective', 'skill'
            batch_size (int): Number of questions per API call (default: 5)

        Returns:
            dict: Same structure as run_audit()
        """
        import time

        # Load data
        questions_df = pd.read_csv(question_csv)
        reference_data = self._load_reference_data(reference_csv, dimension)

        recommendations = []
        coverage_counts = {}

        # Prepare questions list (skip stem questions)
        questions_list = []
        for idx, row in questions_df.iterrows():
            question_num = row.get('Question Number', f"Q{idx+1}")
            question_text = row.get('Question Text', '')
            # Skip stem questions (context-setting, no mapping needed)
            if '(Stem)' in str(question_num):
                continue
            if question_text and pd.notna(question_text):
                questions_list.append((str(question_num), question_text))

        # Process in batches
        total_batches = (len(questions_list) + batch_size - 1) // batch_size
        print(f"[BATCH] Processing {len(questions_list)} questions in {total_batches} batches (batch_size={batch_size})")

        for batch_idx in range(0, len(questions_list), batch_size):
            batch = questions_list[batch_idx:batch_idx + batch_size]
            current_batch_num = (batch_idx // batch_size) + 1
            print(f"  [...] Processing batch {current_batch_num}/{total_batches}...")

            # Build batch prompt and call LLM
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
                    max_tokens=2000,  # Larger for batch responses
                    response_format={"type": "json_object"}
                )

                content = response.choices[0].message.content.strip()
                batch_response = json.loads(content)
                mappings = batch_response.get('mappings', [])

                # Process each mapping in the batch
                for i, mapping in enumerate(mappings):
                    if i < len(batch):
                        q_num, q_text = batch[i]

                        if dimension == 'area_topics':
                            mapped_topic = mapping.get('mapped_topic', '')
                            mapped_subtopic = mapping.get('mapped_subtopic', '')
                            mapping_display = f"{mapped_topic} / {mapped_subtopic}"

                            # Track coverage
                            if mapped_topic in coverage_counts:
                                coverage_counts[mapped_topic] += 1
                            else:
                                coverage_counts[mapped_topic] = 1

                            recommendations.append({
                                'question_num': q_num,
                                'question_text': q_text[:100] + '...' if len(q_text) > 100 else q_text,
                                'current_mapping': None,
                                'recommended_mapping': mapping_display,
                                'mapped_topic': mapped_topic,
                                'mapped_subtopic': mapped_subtopic,
                                'confidence': mapping.get('confidence_score', 0.0),
                                'justification': mapping.get('justification', '')
                            })
                        else:
                            mapped_id = mapping.get('mapped_id', '')

                            # Track coverage
                            if mapped_id in coverage_counts:
                                coverage_counts[mapped_id] += 1
                            else:
                                coverage_counts[mapped_id] = 1

                            recommendations.append({
                                'question_num': q_num,
                                'question_text': q_text[:100] + '...' if len(q_text) > 100 else q_text,
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
                            if mapped_topic in coverage_counts:
                                coverage_counts[mapped_topic] += 1
                            else:
                                coverage_counts[mapped_topic] = 1
                            recommendations.append({
                                'question_num': q_num,
                                'question_text': q_text[:100] + '...' if len(q_text) > 100 else q_text,
                                'current_mapping': None,
                                'recommended_mapping': mapping_display,
                                'mapped_topic': mapped_topic,
                                'mapped_subtopic': mapped_subtopic,
                                'confidence': llm_response.get('confidence_score', 0.0),
                                'justification': llm_response.get('justification', '')
                            })
                        else:
                            mapped_id = llm_response.get('mapped_id', '')
                            if mapped_id in coverage_counts:
                                coverage_counts[mapped_id] += 1
                            else:
                                coverage_counts[mapped_id] = 1
                            recommendations.append({
                                'question_num': q_num,
                                'question_text': q_text[:100] + '...' if len(q_text) > 100 else q_text,
                                'current_mapping': None,
                                'recommended_mapping': mapped_id,
                                'mapped_id': mapped_id,
                                'confidence': llm_response.get('confidence_score', 0.0),
                                'justification': llm_response.get('justification', '')
                            })
                    time.sleep(0.5)

            # Rate limiting between batches
            time.sleep(1.0)

        # Identify gaps
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
        Apply selected recommendations and export to Excel
        
        Args:
            question_csv (str): Original question CSV
            recommendations (list): List of all recommendations
            selected_indices (list): Indices of accepted recommendations
            dimension (str): Dimension type
            output_folder (str): Where to save output
        
        Returns:
            str: Path to output Excel file
        """
        # Load original questions
        questions_df = pd.read_csv(question_csv)
        
        # Apply selected mappings
        for idx in selected_indices:
            if idx < len(recommendations):
                rec = recommendations[idx]
                question_num = rec['question_num']
                
                # Find matching row in dataframe
                mask = questions_df['Question Number'].astype(str) == str(question_num)
                
                if dimension == 'area_topics':
                    questions_df.loc[mask, 'mapped_topic'] = rec.get('mapped_topic', '')
                    questions_df.loc[mask, 'mapped_subtopic'] = rec.get('mapped_subtopic', '')
                else:
                    questions_df.loc[mask, f'mapped_{dimension}'] = rec.get('mapped_id', '')
                
                questions_df.loc[mask, 'confidence_score'] = rec.get('confidence', 0.0)
                questions_df.loc[mask, 'justification'] = rec.get('justification', '')
        
        # Generate output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"audit_output_{dimension}_{timestamp}.xlsx"
        output_path = os.path.join(output_folder, output_filename)
        
        # Export to Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            questions_df.to_excel(writer, sheet_name='Audit Results', index=False)

        return output_path

    def _build_rating_prompt(self, question_text, existing_mapping, reference_data, dimension):
        """
        Build prompt for rating an existing mapping

        Args:
            question_text (str): The question text
            existing_mapping (dict): Current mapping {topic, subtopic} or {id}
            reference_data (dict): Reference definitions
            dimension (str): Dimension type

        Returns:
            str: Formatted prompt
        """
        if dimension == 'area_topics':
            topics_list = "\n".join([
                f"- {topic}: {subtopics}"
                for topic, subtopics in reference_data.items()
            ])

            current_topic = existing_mapping.get('topic', 'Unknown')
            current_subtopic = existing_mapping.get('subtopic', 'Unknown')

            prompt = f"""You are a curriculum mapping expert for medical education.

TASK: Evaluate an EXISTING mapping and rate its accuracy. If incorrect, suggest a better mapping.

QUESTION:
{question_text}

CURRENT MAPPING:
- Topic: {current_topic}
- Subtopic: {current_subtopic}

AVAILABLE TOPIC AREAS AND SUBTOPICS:
{topics_list}

Respond in JSON format:
{{
    "rating": "correct" | "partially_correct" | "incorrect",
    "agreement_score": 0.XX,
    "rating_justification": "Why you agree or disagree with the current mapping...",
    "suggested_topic": "...",
    "suggested_subtopic": "...",
    "suggestion_confidence": 0.XX,
    "suggestion_justification": "Why this mapping is better (if different)..."
}}

Rules:
- agreement_score: 1.0 = perfect match, 0.0 = completely wrong
- If current mapping is correct, suggested_topic/subtopic should match current
- If incorrect, provide the better mapping with justification
- Be specific about why a mapping is right or wrong
"""
        else:
            ids_list = "\n".join([
                f"- {id_key}: {data['description']}"
                for id_key, data in reference_data.items()
            ])

            dimension_name = {
                'competency': 'Competency',
                'objective': 'Objective',
                'skill': 'Skill'
            }[dimension]

            current_id = existing_mapping.get('id', 'Unknown')

            prompt = f"""You are a curriculum mapping expert for medical education.

TASK: Evaluate an EXISTING {dimension_name} mapping and rate its accuracy.

QUESTION:
{question_text}

CURRENT MAPPING: {current_id}

AVAILABLE {dimension_name.upper()}S:
{ids_list}

Respond in JSON format:
{{
    "rating": "correct" | "partially_correct" | "incorrect",
    "agreement_score": 0.XX,
    "rating_justification": "Why you agree or disagree...",
    "suggested_id": "...",
    "suggestion_confidence": 0.XX,
    "suggestion_justification": "Why this is better (if different)..."
}}
"""

        return prompt

    def _build_batch_rating_prompt(self, questions_batch, reference_data, dimension):
        """
        Build prompt for rating a batch of existing mappings

        Args:
            questions_batch (list): List of (q_num, q_text, existing_mapping) tuples
            reference_data (dict): Reference definitions
            dimension (str): Dimension type

        Returns:
            str: Formatted prompt
        """
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
                'skill': 'Skill'
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
        Rate existing mappings and suggest alternatives where needed

        Args:
            mapped_file (str): Path to file with existing mappings (CSV/Excel)
            reference_csv (str): Path to reference CSV
            dimension (str): 'area_topics', 'competency', 'objective', 'skill'
            batch_size (int): Questions per API call

        Returns:
            dict: {
                'ratings': [...],
                'summary': {...},
                'recommendations': [...]  # Only for incorrect/partially_correct
            }
        """
        import time

        # Load mapped data
        if mapped_file.endswith('.csv'):
            mapped_df = pd.read_csv(mapped_file)
        else:
            # Try Excel formats
            try:
                mapped_df = pd.read_excel(mapped_file, engine='openpyxl')
            except:
                mapped_df = pd.read_excel(mapped_file, engine='odf')

        reference_data = self._load_reference_data(reference_csv, dimension)

        # Prepare questions with existing mappings
        questions_list = []
        for idx, row in mapped_df.iterrows():
            q_num = str(row.get('Question Number', f"Q{idx+1}"))

            # Skip stems
            if '(Stem)' in q_num:
                continue

            q_text = row.get('Question Text', '')
            if not q_text or pd.isna(q_text):
                continue

            # Extract existing mapping
            if dimension == 'area_topics':
                existing_mapping = {
                    'topic': row.get('mapped_topic', ''),
                    'subtopic': row.get('mapped_subtopic', '')
                }
            else:
                existing_mapping = {
                    'id': row.get(f'mapped_{dimension}', row.get('mapped_id', ''))
                }

            questions_list.append((q_num, q_text, existing_mapping))

        # Process in batches
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
                            'question_text': q_text[:100] + '...' if len(q_text) > 100 else q_text,
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

        # Generate summary
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

        # Extract recommendations (only for non-correct mappings)
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
