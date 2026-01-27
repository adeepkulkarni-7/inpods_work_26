# AI Prompts Reference

This document contains all the prompts used by the Curriculum Mapping Audit System for Azure OpenAI operations.

## Supported Dimensions

| Dimension | ID Format | Count | Description |
|-----------|-----------|-------|-------------|
| Area Topics | Topic names | Variable | NMC/OER curriculum topics |
| Competency | C1-C6 | 6 | Learning competencies |
| Objective | O1-O6 | 6 | Learning objectives |
| Skill | S1-S5 | 5 | Practical skills |
| **NMC Competency** | MI1.1-MI3.5 | 15 | National Medical Council competencies |

---

## System Message

Used in ALL LLM calls across all tools:

```
You are a medical education curriculum mapping expert. Always respond with valid JSON.
```

---

## Tool 1: Map Unmapped Questions

### Single Question Mapping - Area Topics

```
You are a curriculum mapping expert for medical education.

Map the following question to the most appropriate Topic Area and Subtopic from the NMC/OER curriculum.

QUESTION:
{question_text}

AVAILABLE TOPIC AREAS AND SUBTOPICS:
{topics_list}

Respond in JSON format:
{
    "mapped_topic": "...",
    "mapped_subtopic": "...",
    "confidence_score": 0.XX,
    "justification": "Detailed reasoning for this mapping..."
}

Rules:
- confidence_score must be between 0.0 and 1.0
- Choose the MOST specific and relevant topic/subtopic
- Provide clear justification based on question content
```

---

### Single Question Mapping - Competency/Objective/Skill

```
You are a curriculum mapping expert for medical education.

Map the following question to the most appropriate {dimension_name} from the curriculum framework.

QUESTION:
{question_text}

AVAILABLE {DIMENSION_NAME}S:
{ids_list}

Respond in JSON format:
{
    "mapped_id": "...",
    "confidence_score": 0.XX,
    "justification": "Detailed reasoning for this mapping..."
}

Rules:
- confidence_score must be between 0.0 and 1.0
- Choose the MOST relevant {dimension_name}
- Provide clear justification based on question content
```

**Variables:**
- `{dimension_name}` = "Competency", "Objective", or "Skill"
- `{DIMENSION_NAME}` = uppercase version for headers

---

### Batch Mapping (5 questions per call) - Area Topics

```
You are a curriculum mapping expert for medical education.

Map EACH of the following questions to the most appropriate Topic Area and Subtopic from the NMC/OER curriculum.

QUESTIONS:
{questions_block}

AVAILABLE TOPIC AREAS AND SUBTOPICS:
{topics_list}

Respond in JSON format with an array of mappings:
{
    "mappings": [
        {
            "question_id": "Q1",
            "mapped_topic": "...",
            "mapped_subtopic": "...",
            "confidence_score": 0.XX,
            "justification": "Brief reasoning..."
        },
        ...
    ]
}

Rules:
- Include a mapping for EACH question in the same order
- confidence_score must be between 0.0 and 1.0
- Choose the MOST specific and relevant topic/subtopic for each
- Keep justifications concise (1-2 sentences)
```

**Questions Block Format:**
```
[Q1]: {question_text_1}

[Q2]: {question_text_2}

[Q3]: {question_text_3}
...
```

---

### Batch Mapping - Competency/Objective/Skill

```
You are a curriculum mapping expert for medical education.

Map EACH of the following questions to the most appropriate {dimension_name} from the curriculum framework.

QUESTIONS:
{questions_block}

AVAILABLE {DIMENSION_NAME}S:
{ids_list}

Respond in JSON format with an array of mappings:
{
    "mappings": [
        {
            "question_id": "Q1",
            "mapped_id": "...",
            "confidence_score": 0.XX,
            "justification": "Brief reasoning..."
        },
        ...
    ]
}

Rules:
- Include a mapping for EACH question in the same order
- confidence_score must be between 0.0 and 1.0
- Choose the MOST relevant {dimension_name} for each
- Keep justifications concise (1-2 sentences)
```

---

## Tool 2: Rate Existing Mappings

### Rating Prompt - Area Topics

```
You are a curriculum mapping expert for medical education.

TASK: Evaluate EXISTING mappings for multiple questions. Rate each and suggest better mappings if needed.

QUESTIONS WITH CURRENT MAPPINGS:
{questions_block}

AVAILABLE TOPIC AREAS AND SUBTOPICS:
{topics_list}

Respond in JSON format:
{
    "ratings": [
        {
            "question_id": "...",
            "rating": "correct" | "partially_correct" | "incorrect",
            "agreement_score": 0.XX,
            "rating_justification": "Brief reason...",
            "suggested_topic": "...",
            "suggested_subtopic": "...",
            "suggestion_confidence": 0.XX,
            "suggestion_justification": "Brief reason if different..."
        },
        ...
    ]
}

Rules:
- Include a rating for EACH question
- agreement_score: 1.0 = perfect, 0.0 = wrong
- Keep justifications concise (1-2 sentences)
```

**Questions Block Format for Rating:**
```
[Q1]
Question: {question_text}
Current Mapping: {topic} / {subtopic}

[Q2]
Question: {question_text}
Current Mapping: {topic} / {subtopic}
...
```

---

### Rating Prompt - Competency/Objective/Skill

```
You are a curriculum mapping expert for medical education.

TASK: Evaluate EXISTING {dimension_name} mappings. Rate each and suggest better if needed.

QUESTIONS WITH CURRENT MAPPINGS:
{questions_block}

AVAILABLE {DIMENSION_NAME}S:
{ids_list}

Respond in JSON format:
{
    "ratings": [
        {
            "question_id": "...",
            "rating": "correct" | "partially_correct" | "incorrect",
            "agreement_score": 0.XX,
            "rating_justification": "Brief reason...",
            "suggested_id": "...",
            "suggestion_confidence": 0.XX,
            "suggestion_justification": "Brief reason if different..."
        },
        ...
    ]
}
```

**Questions Block Format for Rating:**
```
[Q1]
Question: {question_text}
Current Mapping: {id}

[Q2]
Question: {question_text}
Current Mapping: {id}
...
```

---

## Tool 3: Generate Insights

Tool 3 does not use LLM calls. It generates visualizations from the mapping data using matplotlib.

---

## LLM Configuration Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Temperature | 0.3 | Low temperature for consistent, deterministic outputs |
| Max Tokens (single) | 500 | For single question mapping |
| Max Tokens (batch) | 2000 | For batch mapping (5 questions) |
| Max Tokens (rating) | 2500 | For batch rating |
| Response Format | `{"type": "json_object"}` | Forces JSON response |

---

## Rating Scale Reference

| Rating | Agreement Score | Meaning |
|--------|-----------------|---------|
| correct | 0.85 - 1.0 | Mapping is accurate |
| partially_correct | 0.5 - 0.84 | Mapping is close but not ideal |
| incorrect | 0.0 - 0.49 | Mapping is wrong |

---

## Confidence Score Guidelines

| Score Range | Label | Color Code |
|-------------|-------|------------|
| 0.85 - 1.0 | High | Green (#00d4aa) |
| 0.70 - 0.84 | Medium | Orange (#ffa600) |
| 0.0 - 0.69 | Low | Red (#ff6b6b) |

---

## Source Files

- `backend_v2/audit_engine.py` - Main audit engine with all prompts
- `objectives/backend/objectives_engine.py` - Objectives-specific engine
