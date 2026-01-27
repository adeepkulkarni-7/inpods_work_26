"""
Objectives Mapping Engine
Maps medical education questions to Learning Objectives (O1-O6) using Azure OpenAI
"""

from openai import AzureOpenAI
import pandas as pd
import json
from datetime import datetime
import os
import time


# Objectives Reference Data (O1-O6)
OBJECTIVES_REFERENCE = {
    'O1': 'Explain how different microorganisms cause human infection',
    'O2': 'Understand commensal, opportunistic and pathogenic organisms',
    'O3': 'Describe characteristics (morphology, resistance, virulence) of microorganisms',
    'O4': 'Explain host defense mechanisms against microorganisms',
    'O5': 'Describe laboratory diagnosis of human infections',
    'O6': 'Describe prophylaxis for infecting microorganisms'
}


class ObjectivesEngine:
    """Handles mapping questions to Learning Objectives (O1-O6)"""

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
        self.client = AzureOpenAI(
            api_key=self.config["api_key"],
            azure_endpoint=self.config["azure_endpoint"],
            api_version=self.config["api_version"]
        )

    def test_connection(self):
        """Test Azure OpenAI connection"""
        try:
            response = self.client.chat.completions.create(
                model=self.config["deployment"],
                messages=[{"role": "user", "content": "Respond with 'Connected'"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            print(f"[ERROR] Connection Failed: {e}")
            return False

    def _build_objectives_list(self):
        """Build formatted objectives list for prompts"""
        return "\n".join([
            f"- {obj_id}: {desc}"
            for obj_id, desc in OBJECTIVES_REFERENCE.items()
        ])

    # ========================================
    # TOOL 1: Map Unmapped Questions
    # ========================================

    def map_questions(self, question_csv, batch_size=5):
        """
        Tool 1: Map unmapped questions to objectives

        Args:
            question_csv (str): Path to question CSV
            batch_size (int): Questions per API call

        Returns:
            dict: {
                'recommendations': [...],
                'coverage': {...},
                'gaps': [...]
            }
        """
        questions_df = pd.read_csv(question_csv)

        # Prepare questions (skip stems)
        questions_list = []
        for idx, row in questions_df.iterrows():
            q_num = str(row.get('Question Number', f"Q{idx+1}"))
            q_text = row.get('Question Text', '')

            if '(Stem)' in q_num:
                continue
            if q_text and pd.notna(q_text):
                questions_list.append((q_num, q_text))

        recommendations = []
        coverage_counts = {obj: 0 for obj in OBJECTIVES_REFERENCE.keys()}

        # Process in batches
        total_batches = (len(questions_list) + batch_size - 1) // batch_size
        print(f"[MAP] Processing {len(questions_list)} questions in {total_batches} batches")

        for batch_idx in range(0, len(questions_list), batch_size):
            batch = questions_list[batch_idx:batch_idx + batch_size]
            current_batch = (batch_idx // batch_size) + 1
            print(f"  [...] Batch {current_batch}/{total_batches}")

            # Build batch prompt
            questions_block = "\n\n".join([
                f"[{q_num}]: {q_text}"
                for q_num, q_text in batch
            ])

            prompt = f"""You are a medical education curriculum mapping expert.

Map EACH question to the most appropriate Learning Objective.

QUESTIONS:
{questions_block}

AVAILABLE OBJECTIVES:
{self._build_objectives_list()}

Respond in JSON format:
{{
    "mappings": [
        {{
            "question_id": "...",
            "objective_id": "O1-O6",
            "confidence": 0.XX,
            "reason": "Brief one-line explanation"
        }}
    ]
}}

Rules:
- Map each question to exactly ONE objective (O1-O6)
- Confidence: 0.0-1.0 (how certain you are)
- Reason: Keep to one brief sentence
"""

            try:
                response = self.client.chat.completions.create(
                    model=self.config["deployment"],
                    messages=[
                        {"role": "system", "content": "You are a medical education expert. Respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1500,
                    response_format={"type": "json_object"}
                )

                content = response.choices[0].message.content.strip()
                batch_response = json.loads(content)
                mappings = batch_response.get('mappings', [])

                for i, mapping in enumerate(mappings):
                    if i < len(batch):
                        q_num, q_text = batch[i]
                        obj_id = mapping.get('objective_id', 'O1')

                        if obj_id in coverage_counts:
                            coverage_counts[obj_id] += 1

                        recommendations.append({
                            'question_num': q_num,
                            'question_text': q_text[:150] + '...' if len(q_text) > 150 else q_text,
                            'objective_id': obj_id,
                            'objective_desc': OBJECTIVES_REFERENCE.get(obj_id, ''),
                            'confidence': mapping.get('confidence', 0.0),
                            'reason': mapping.get('reason', '')
                        })

            except Exception as e:
                print(f"  [ERROR] Batch {current_batch} failed: {e}")

            time.sleep(1.0)

        # Identify gaps
        gaps = [obj for obj, count in coverage_counts.items() if count == 0]

        print(f"[OK] Mapped {len(recommendations)} questions")

        return {
            'recommendations': recommendations,
            'coverage': coverage_counts,
            'gaps': gaps,
            'total_questions': len(questions_df),
            'mapped_questions': len(recommendations)
        }

    # ========================================
    # TOOL 2: Rate Existing Mappings
    # ========================================

    def rate_mappings(self, mapped_file, batch_size=5):
        """
        Tool 2: Rate existing objective mappings

        Args:
            mapped_file (str): Path to file with existing mappings
            batch_size (int): Questions per API call

        Returns:
            dict: {
                'ratings': [...],
                'summary': {...},
                'recommendations': [...]
            }
        """
        # Load mapped file
        if mapped_file.endswith('.csv'):
            mapped_df = pd.read_csv(mapped_file)
        elif mapped_file.endswith('.ods'):
            mapped_df = pd.read_excel(mapped_file, engine='odf')
        else:
            mapped_df = pd.read_excel(mapped_file, engine='openpyxl')

        # Prepare questions with existing mappings
        questions_list = []
        for idx, row in mapped_df.iterrows():
            q_num = str(row.get('Question Number', f"Q{idx+1}"))

            if '(Stem)' in q_num:
                continue

            q_text = row.get('Question Text', '')
            if not q_text or pd.isna(q_text):
                continue

            # Get existing objective mapping
            existing_obj = row.get('mapped_objective', row.get('objective_id', row.get('Objective', '')))
            if pd.isna(existing_obj):
                existing_obj = ''

            questions_list.append((q_num, q_text, str(existing_obj).strip()))

        all_ratings = []

        # Process in batches
        total_batches = (len(questions_list) + batch_size - 1) // batch_size
        print(f"[RATE] Rating {len(questions_list)} mappings in {total_batches} batches")

        for batch_idx in range(0, len(questions_list), batch_size):
            batch = questions_list[batch_idx:batch_idx + batch_size]
            current_batch = (batch_idx // batch_size) + 1
            print(f"  [...] Batch {current_batch}/{total_batches}")

            questions_block = "\n\n".join([
                f"[{q_num}]\nQuestion: {q_text}\nCurrent Mapping: {existing}"
                for q_num, q_text, existing in batch
            ])

            prompt = f"""You are a medical education curriculum mapping expert.

TASK: Evaluate existing objective mappings. Rate each and suggest better if needed.

QUESTIONS WITH CURRENT MAPPINGS:
{questions_block}

AVAILABLE OBJECTIVES:
{self._build_objectives_list()}

Respond in JSON format:
{{
    "ratings": [
        {{
            "question_id": "...",
            "rating": "correct" | "partially_correct" | "incorrect",
            "agreement_score": 0.XX,
            "rating_reason": "Brief explanation",
            "suggested_objective": "O1-O6",
            "suggestion_confidence": 0.XX,
            "suggestion_reason": "Why this is better (if different)"
        }}
    ]
}}

Rules:
- rating: "correct" if mapping is accurate, "partially_correct" if somewhat related, "incorrect" if wrong
- agreement_score: 1.0 = perfect match, 0.0 = completely wrong
- If current is correct, suggested_objective should match current
"""

            try:
                response = self.client.chat.completions.create(
                    model=self.config["deployment"],
                    messages=[
                        {"role": "system", "content": "You are a medical education expert. Respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000,
                    response_format={"type": "json_object"}
                )

                content = response.choices[0].message.content.strip()
                batch_response = json.loads(content)
                ratings = batch_response.get('ratings', [])

                for i, rating in enumerate(ratings):
                    if i < len(batch):
                        q_num, q_text, existing = batch[i]

                        all_ratings.append({
                            'question_num': q_num,
                            'question_text': q_text[:150] + '...' if len(q_text) > 150 else q_text,
                            'current_objective': existing,
                            'rating': rating.get('rating', 'unknown'),
                            'agreement_score': rating.get('agreement_score', 0.0),
                            'rating_reason': rating.get('rating_reason', ''),
                            'suggested_objective': rating.get('suggested_objective', ''),
                            'suggested_desc': OBJECTIVES_REFERENCE.get(rating.get('suggested_objective', ''), ''),
                            'suggestion_confidence': rating.get('suggestion_confidence', 0.0),
                            'suggestion_reason': rating.get('suggestion_reason', '')
                        })

            except Exception as e:
                print(f"  [ERROR] Batch {current_batch} failed: {e}")

            time.sleep(1.0)

        # Generate summary
        correct = sum(1 for r in all_ratings if r['rating'] == 'correct')
        partial = sum(1 for r in all_ratings if r['rating'] == 'partially_correct')
        incorrect = sum(1 for r in all_ratings if r['rating'] == 'incorrect')
        avg_agreement = sum(r['agreement_score'] for r in all_ratings) / len(all_ratings) if all_ratings else 0

        summary = {
            'total_rated': len(all_ratings),
            'correct': correct,
            'partially_correct': partial,
            'incorrect': incorrect,
            'accuracy_rate': correct / len(all_ratings) if all_ratings else 0,
            'average_agreement': avg_agreement
        }

        # Extract recommendations (non-correct only)
        recommendations = [r for r in all_ratings if r['rating'] != 'correct']

        print(f"[OK] Rated {len(all_ratings)}: {correct} correct, {partial} partial, {incorrect} incorrect")

        return {
            'ratings': all_ratings,
            'summary': summary,
            'recommendations': recommendations
        }

    # ========================================
    # TOOL 3: Generate Insights Data
    # ========================================

    def get_insights_data(self, mapped_file):
        """
        Tool 3: Extract insights data for visualization

        Args:
            mapped_file (str): Path to mapped file

        Returns:
            dict: Data for visualization
        """
        # Load mapped file
        if mapped_file.endswith('.csv'):
            df = pd.read_csv(mapped_file)
        elif mapped_file.endswith('.ods'):
            df = pd.read_excel(mapped_file, engine='odf')
        else:
            df = pd.read_excel(mapped_file, engine='openpyxl')

        # Count coverage per objective
        coverage = {obj: 0 for obj in OBJECTIVES_REFERENCE.keys()}
        confidence_scores = []

        for idx, row in df.iterrows():
            q_num = str(row.get('Question Number', ''))
            if '(Stem)' in q_num:
                continue

            obj = row.get('objective_id', row.get('mapped_objective', row.get('Objective', '')))
            if pd.notna(obj) and str(obj).strip() in coverage:
                coverage[str(obj).strip()] += 1

            conf = row.get('confidence', row.get('confidence_score', 0.85))
            if pd.notna(conf):
                confidence_scores.append(float(conf))

        # Identify gaps
        gaps = [obj for obj, count in coverage.items() if count == 0]

        return {
            'coverage': coverage,
            'confidence_scores': confidence_scores,
            'gaps': gaps,
            'total_questions': len([1 for _, r in df.iterrows() if '(Stem)' not in str(r.get('Question Number', ''))]),
            'objectives_reference': OBJECTIVES_REFERENCE
        }

    # ========================================
    # Export Functions
    # ========================================

    def apply_and_export(self, question_csv, recommendations, selected_indices, output_folder):
        """
        Apply selected mappings and export to Excel

        Args:
            question_csv (str): Original question CSV
            recommendations (list): All recommendations
            selected_indices (list): Indices to apply
            output_folder (str): Output directory

        Returns:
            str: Path to output Excel file
        """
        df = pd.read_csv(question_csv)

        for idx in selected_indices:
            if idx < len(recommendations):
                rec = recommendations[idx]
                q_num = rec['question_num']

                mask = df['Question Number'].astype(str) == str(q_num)
                df.loc[mask, 'mapped_objective'] = rec.get('objective_id', '')
                df.loc[mask, 'objective_description'] = rec.get('objective_desc', rec.get('suggested_desc', ''))
                df.loc[mask, 'confidence_score'] = rec.get('confidence', rec.get('suggestion_confidence', 0.0))
                df.loc[mask, 'mapping_reason'] = rec.get('reason', rec.get('suggestion_reason', ''))

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"objectives_mapping_{timestamp}.xlsx"
        output_path = os.path.join(output_folder, output_filename)

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Objectives Mapping', index=False)

        return output_path
