# AI Agent for Curriculum Mapping - Implementation Plan

## Overview

Create an autonomous AI Agent that guides users through the entire curriculum mapping workflow via natural conversation. The agent will handle file uploads, present options, run mappings, generate visualizations, and iterate based on user feedback.

---

## Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AI AGENT APP                                 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Conversation UI                           │   │
│  │   (Web Chat / CLI / API)                                    │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                       │
│  ┌──────────────────────────▼──────────────────────────────────┐   │
│  │                    Agent Orchestrator                        │   │
│  │   - Conversation State Management                           │   │
│  │   - Intent Recognition                                      │   │
│  │   - Tool Selection & Execution                              │   │
│  │   - Response Generation                                     │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                       │
│  ┌──────────────┬───────────┼───────────┬──────────────────────┐   │
│  │              │           │           │                      │   │
│  ▼              ▼           ▼           ▼                      │   │
│ ┌────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌───────────┐ │   │
│ │ Upload │ │ Mapping │ │ Rating  │ │ Insights │ │ Export    │ │   │
│ │ Tool   │ │ Tool    │ │ Tool    │ │ Tool     │ │ Tool      │ │   │
│ └────────┘ └─────────┘ └─────────┘ └──────────┘ └───────────┘ │   │
│                             │                                       │
│                    ┌────────┴────────┐                             │
│                    │  Integration    │                             │
│                    │  Package        │                             │
│                    │  (Engine/Viz)   │                             │
│                    └────────┬────────┘                             │
│                             │                                       │
│                    ┌────────┴────────┐                             │
│                    │  Azure OpenAI   │                             │
│                    │  (GPT-4)        │                             │
│                    └─────────────────┘                             │
└─────────────────────────────────────────────────────────────────────┘
```

### Folder Structure

```
agent/
├── __init__.py
├── main.py                    # Entry point
├── config.py                  # Agent configuration
├── orchestrator.py            # Main agent logic
├── conversation.py            # Conversation state management
├── tools/
│   ├── __init__.py
│   ├── base.py               # Base tool class
│   ├── upload_tool.py        # File upload handling
│   ├── mapping_tool.py       # Question mapping
│   ├── rating_tool.py        # Rating existing mappings
│   ├── insights_tool.py      # Visualization generation
│   └── export_tool.py        # Export to Excel
├── prompts/
│   ├── __init__.py
│   ├── system.py             # System prompts
│   ├── tools.py              # Tool descriptions
│   └── responses.py          # Response templates
├── ui/
│   ├── __init__.py
│   ├── cli.py                # Command-line interface
│   ├── web.py                # Web chat interface (Flask/FastAPI)
│   └── templates/
│       └── chat.html         # Chat UI template
├── tests/
│   ├── test_orchestrator.py
│   └── test_tools.py
└── README.md
```

---

## Conversation Flow

### Main Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        START                                      │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  GREETING & INTRODUCTION                                          │
│  "Hello! I'm your Curriculum Mapping Assistant. I can help you:  │
│   • Map exam questions to curriculum competencies                 │
│   • Rate existing mappings for accuracy                          │
│   • Generate visual insights from your mappings                  │
│                                                                   │
│  What would you like to do today?"                               │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  MODE SELECTION                                                   │
│  User chooses: [Map Questions] [Rate Mappings] [Generate Insights]│
└────────────────────────┬─────────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
     ┌─────────┐   ┌─────────┐   ┌─────────┐
     │ Mode A  │   │ Mode B  │   │ Mode C  │
     │ Map     │   │ Rate    │   │ Insights│
     └────┬────┘   └────┬────┘   └────┬────┘
          │              │              │
          ▼              ▼              ▼
┌──────────────────────────────────────────────────────────────────┐
│  FILE UPLOAD REQUEST                                              │
│  "Please upload your files. You can drag & drop or click to      │
│   select. I need:"                                                │
│   • Mode A: Question file + Reference curriculum                  │
│   • Mode B: Pre-mapped file + Reference curriculum               │
│   • Mode C: Mapped file (with existing mappings)                 │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  FILE VALIDATION & PREVIEW                                        │
│  "Great! I received your files:                                   │
│   • questions.csv - 50 questions found                           │
│   • curriculum.csv - 15 competencies loaded                      │
│                                                                   │
│   Here's a preview of your data..."                              │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  DIMENSION SELECTION                                              │
│  "Which curriculum dimension should I map to?                     │
│                                                                   │
│   1. NMC Competency (MI1.1 - MI15.x)                            │
│   2. Area Topics (Topic / Subtopic)                              │
│   3. Competency (C1-C9)                                          │
│   4. Objective (O1-O9)                                           │
│   5. Skill (S1-S5)                                               │
│                                                                   │
│   Based on your reference file, I recommend: NMC Competency"     │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  PROCESSING                                                       │
│  "Starting the mapping process...                                 │
│                                                                   │
│   ⏳ Processing batch 1/10...                                    │
│   ⏳ Processing batch 2/10...                                    │
│   ...                                                            │
│   ✓ Completed! 50 questions mapped."                             │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  RESULTS SUMMARY                                                  │
│  "Here's what I found:                                           │
│                                                                   │
│   📊 Coverage Summary:                                           │
│   • MI1.1: 8 questions (16%)                                     │
│   • MI2.3: 5 questions (10%)                                     │
│   • ...                                                          │
│                                                                   │
│   ⚠️ Gaps Identified: MI4.2, MI5.1 (0 questions)                │
│                                                                   │
│   📈 Confidence: 87% average (42 high, 6 medium, 2 low)"         │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  OPTIONS MENU                                                     │
│  "What would you like to do next?                                │
│                                                                   │
│   1. 📊 Generate visual charts and dashboard                     │
│   2. 📝 Review individual mappings                               │
│   3. ✏️  Refine low-confidence mappings                          │
│   4. 💾 Export results to Excel                                  │
│   5. 🔄 Re-run with different dimension                          │
│   6. ✅ Save to library and finish"                              │
└────────────────────────┬─────────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
   ┌────────────┐ ┌────────────┐ ┌────────────┐
   │ Visualize  │ │  Review    │ │  Export    │
   │ Charts     │ │  Details   │ │  Download  │
   └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
         │              │              │
         └──────────────┼──────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│  ENHANCEMENT LOOP                                                 │
│  "Would you like to make any adjustments?                        │
│                                                                   │
│   • Change any mappings manually                                 │
│   • Focus on specific topics                                     │
│   • Re-analyze low-confidence items                              │
│   • Generate additional charts                                   │
│                                                                   │
│   Or type 'done' to finish."                                     │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  COMPLETION                                                       │
│  "All done! Here's your final output:                            │
│                                                                   │
│   📁 audit_output_nmc_competency_20260127.xlsx                   │
│   📊 summary_dashboard.png                                       │
│   📈 confidence_histogram.png                                    │
│                                                                   │
│   Your mapping has been saved to the library.                    │
│   Would you like to start a new mapping?"                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Agent Components

### 1. Orchestrator

The main brain that:
- Manages conversation state
- Decides which tool to use
- Generates natural responses
- Handles user intent

```python
class AgentOrchestrator:
    def __init__(self, config):
        self.llm = AzureOpenAI(...)
        self.tools = self._load_tools()
        self.conversation = ConversationState()

    async def process_message(self, user_message: str) -> AgentResponse:
        # 1. Understand intent
        intent = await self._analyze_intent(user_message)

        # 2. Update conversation state
        self.conversation.update(user_message, intent)

        # 3. Select and execute tool if needed
        if intent.requires_tool:
            tool_result = await self._execute_tool(intent.tool, intent.params)
            self.conversation.add_tool_result(tool_result)

        # 4. Generate response
        response = await self._generate_response()

        return response
```

### 2. Conversation State

Tracks the entire conversation flow:

```python
@dataclass
class ConversationState:
    mode: str = None                    # 'map', 'rate', 'insights'
    step: str = 'greeting'              # Current step
    files: dict = None                  # Uploaded files
    dimension: str = None               # Selected dimension
    results: dict = None                # Mapping results
    selected_indices: list = None       # User selections
    messages: list = field(default_factory=list)
    tool_results: list = field(default_factory=list)

    def get_context(self) -> str:
        """Get context for LLM"""
        return f"""
        Current Mode: {self.mode}
        Current Step: {self.step}
        Files Uploaded: {bool(self.files)}
        Dimension: {self.dimension}
        Has Results: {bool(self.results)}
        """
```

### 3. Tools

Each tool is a discrete capability:

```python
class BaseTool:
    name: str
    description: str

    async def execute(self, params: dict) -> ToolResult:
        raise NotImplementedError

class MappingTool(BaseTool):
    name = "map_questions"
    description = "Map exam questions to curriculum competencies"

    async def execute(self, params: dict) -> ToolResult:
        engine = AuditEngine(self.config)
        result = engine.run_audit_batched(
            question_csv=params['question_file'],
            reference_csv=params['reference_file'],
            dimension=params['dimension'],
            batch_size=params.get('batch_size', 5)
        )
        return ToolResult(success=True, data=result)
```

### 4. Prompts

System prompts guide the agent:

```python
SYSTEM_PROMPT = """
You are a helpful Curriculum Mapping Assistant. Your role is to guide users
through the process of mapping exam questions to curriculum competencies.

You have access to these tools:
{tool_descriptions}

Current conversation state:
{conversation_state}

Guidelines:
- Be friendly and professional
- Explain technical concepts simply
- Always confirm before taking actions
- Provide clear summaries of results
- Offer relevant next steps
- Ask clarifying questions when needed
"""
```

---

## User Interface Options

### Option A: Web Chat Interface

```
┌──────────────────────────────────────────────────────────────┐
│  🎓 Curriculum Mapping Assistant                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 🤖 Hello! I'm your Curriculum Mapping Assistant.      │ │
│  │    What would you like to do today?                   │ │
│  │                                                        │ │
│  │    [Map Questions] [Rate Mappings] [Generate Insights]│ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 👤 I want to map my exam questions                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 🤖 Great! Please upload your files:                   │ │
│  │                                                        │ │
│  │    📎 Question Bank:  [Choose File] questions.csv ✓   │ │
│  │    📎 Reference:      [Choose File] curriculum.csv ✓  │ │
│  │                                                        │ │
│  │    [Continue]                                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Type a message...                              [Send]       │
└──────────────────────────────────────────────────────────────┘
```

### Option B: CLI Interface

```
╔══════════════════════════════════════════════════════════════╗
║          🎓 CURRICULUM MAPPING ASSISTANT                     ║
╚══════════════════════════════════════════════════════════════╝

🤖 Hello! I'm your Curriculum Mapping Assistant.
   What would you like to do today?

   [1] Map exam questions to curriculum
   [2] Rate existing mappings
   [3] Generate visual insights

> 1

🤖 Great! Let's map your questions. Please provide the file paths:

   Question file path: > ./questions.csv
   ✓ Found 50 questions

   Reference file path: > ./curriculum.csv
   ✓ Found 15 competencies

🤖 Which dimension should I map to?

   [1] NMC Competency (MI1.1 - MI15.x) ← Recommended
   [2] Area Topics
   [3] Competency (C1-C9)

> 1

🤖 Starting mapping process...

   ⏳ Processing batch 1/10...
   ⏳ Processing batch 2/10...
   ✓ Complete! 50 questions mapped.

🤖 Results Summary:
   ┌─────────────────────────────────────┐
   │ Coverage      │ Questions │ %       │
   ├─────────────────────────────────────┤
   │ MI1.1         │ 8         │ 16%     │
   │ MI2.3         │ 5         │ 10%     │
   │ ...           │           │         │
   ├─────────────────────────────────────┤
   │ Gaps: MI4.2, MI5.1                  │
   │ Avg Confidence: 87%                 │
   └─────────────────────────────────────┘

🤖 What would you like to do next?

   [1] Generate charts
   [2] Review mappings
   [3] Export to Excel
   [4] Start over

> _
```

---

## Implementation Details

### Key Classes

#### AgentOrchestrator

```python
# agent/orchestrator.py

from openai import AzureOpenAI
from typing import Optional, List
from dataclasses import dataclass
import json

from .conversation import ConversationState
from .tools import ToolRegistry
from .prompts import SYSTEM_PROMPT, TOOL_DESCRIPTIONS

@dataclass
class AgentResponse:
    message: str
    options: Optional[List[str]] = None
    files: Optional[List[str]] = None
    charts: Optional[List[str]] = None
    requires_input: bool = False
    input_type: str = "text"  # "text", "file", "choice"

class AgentOrchestrator:
    def __init__(self, config: dict):
        self.client = AzureOpenAI(
            api_key=config['api_key'],
            azure_endpoint=config['azure_endpoint'],
            api_version=config.get('api_version', '2024-02-15-preview')
        )
        self.deployment = config.get('deployment', 'gpt-4')
        self.tools = ToolRegistry(config)
        self.state = ConversationState()

    async def process_message(
        self,
        user_message: str,
        files: Optional[List[str]] = None
    ) -> AgentResponse:
        """Process user message and generate response."""

        # Add user message to history
        self.state.add_message("user", user_message)

        # Handle file uploads if provided
        if files:
            await self._handle_file_upload(files)

        # Build context for LLM
        context = self._build_context()

        # Call LLM for decision making
        response = await self._call_llm(context, user_message)

        # Parse LLM response for tool calls
        if response.tool_calls:
            for tool_call in response.tool_calls:
                result = await self.tools.execute(
                    tool_call.name,
                    json.loads(tool_call.arguments)
                )
                self.state.add_tool_result(tool_call.name, result)

        # Generate final response
        agent_response = await self._generate_response()

        # Add to history
        self.state.add_message("assistant", agent_response.message)

        return agent_response

    def _build_context(self) -> str:
        """Build context string for LLM."""
        return SYSTEM_PROMPT.format(
            tool_descriptions=TOOL_DESCRIPTIONS,
            conversation_state=self.state.get_summary(),
            message_history=self.state.get_recent_messages(10)
        )

    async def _call_llm(self, context: str, user_message: str):
        """Call Azure OpenAI with tools."""
        messages = [
            {"role": "system", "content": context},
            *self.state.get_messages_for_api(),
            {"role": "user", "content": user_message}
        ]

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            tools=self.tools.get_tool_definitions(),
            tool_choice="auto",
            temperature=0.7
        )

        return response.choices[0].message
```

#### ConversationState

```python
# agent/conversation.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class ConversationStep(Enum):
    GREETING = "greeting"
    MODE_SELECTION = "mode_selection"
    FILE_UPLOAD = "file_upload"
    DIMENSION_SELECTION = "dimension_selection"
    PROCESSING = "processing"
    RESULTS = "results"
    OPTIONS = "options"
    ENHANCEMENT = "enhancement"
    COMPLETE = "complete"

@dataclass
class Message:
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConversationState:
    step: ConversationStep = ConversationStep.GREETING
    mode: Optional[str] = None  # "map", "rate", "insights"
    files: Dict[str, str] = field(default_factory=dict)
    dimension: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    selected_indices: List[int] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)

    def add_message(self, role: str, content: str, **metadata):
        self.messages.append(Message(role, content, metadata=metadata))

    def add_tool_result(self, tool_name: str, result: Any):
        self.tool_results.append({
            "tool": tool_name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

    def get_summary(self) -> str:
        return f"""
        Step: {self.step.value}
        Mode: {self.mode or 'Not selected'}
        Files: {list(self.files.keys()) if self.files else 'None'}
        Dimension: {self.dimension or 'Not selected'}
        Has Results: {bool(self.results)}
        Messages: {len(self.messages)}
        """

    def get_messages_for_api(self) -> List[Dict]:
        return [
            {"role": m.role, "content": m.content}
            for m in self.messages[-20:]  # Last 20 messages
        ]

    def advance_step(self):
        """Move to next logical step."""
        step_order = list(ConversationStep)
        current_idx = step_order.index(self.step)
        if current_idx < len(step_order) - 1:
            self.step = step_order[current_idx + 1]
```

#### Tools

```python
# agent/tools/mapping_tool.py

from .base import BaseTool, ToolResult
from integration import AuditEngine

class MappingTool(BaseTool):
    name = "map_questions"
    description = """
    Map exam questions to curriculum competencies using AI.

    Parameters:
    - question_file: Path to the question CSV/Excel file
    - reference_file: Path to the reference curriculum file
    - dimension: Mapping dimension (nmc_competency, area_topics, etc.)
    - batch_size: Questions per API call (default: 5)
    """

    parameters = {
        "type": "object",
        "properties": {
            "question_file": {"type": "string"},
            "reference_file": {"type": "string"},
            "dimension": {
                "type": "string",
                "enum": ["nmc_competency", "area_topics", "competency", "objective", "skill"]
            },
            "batch_size": {"type": "integer", "default": 5}
        },
        "required": ["question_file", "reference_file", "dimension"]
    }

    def __init__(self, config: dict):
        self.engine = AuditEngine(config)

    async def execute(self, params: dict) -> ToolResult:
        try:
            result = self.engine.run_audit_batched(
                question_csv=params['question_file'],
                reference_csv=params['reference_file'],
                dimension=params['dimension'],
                batch_size=params.get('batch_size', 5)
            )

            return ToolResult(
                success=True,
                data=result,
                message=f"Mapped {result['mapped_questions']} questions"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
```

#### Web Interface

```python
# agent/ui/web.py

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import asyncio

from ..orchestrator import AgentOrchestrator
from ..config import get_config

app = Flask(__name__)
CORS(app)

# Initialize orchestrator
config = get_config()
orchestrator = AgentOrchestrator(config)

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    files = data.get('files', [])

    # Process message
    loop = asyncio.new_event_loop()
    response = loop.run_until_complete(
        orchestrator.process_message(message, files)
    )

    return jsonify({
        'message': response.message,
        'options': response.options,
        'files': response.files,
        'charts': response.charts,
        'requires_input': response.requires_input,
        'input_type': response.input_type
    })

@app.route('/api/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files')
    saved_files = []

    for file in files:
        # Save file
        path = f"uploads/{file.filename}"
        file.save(path)
        saved_files.append(path)

    return jsonify({
        'status': 'success',
        'files': saved_files
    })

@app.route('/api/reset', methods=['POST'])
def reset():
    global orchestrator
    orchestrator = AgentOrchestrator(config)
    return jsonify({'status': 'reset'})

if __name__ == '__main__':
    app.run(port=5002, debug=True)
```

---

## Prompts

### System Prompt

```python
# agent/prompts/system.py

SYSTEM_PROMPT = """
You are a helpful Curriculum Mapping Assistant for medical education.
Your role is to guide educators through the process of mapping exam
questions to curriculum competencies.

## Your Capabilities
{tool_descriptions}

## Current State
{conversation_state}

## Guidelines
1. Be friendly, professional, and helpful
2. Explain technical concepts in simple terms
3. Always confirm before executing actions
4. Provide clear summaries of results
5. Suggest relevant next steps
6. Ask clarifying questions when needed

## Response Format
- Use markdown for formatting
- Include relevant emojis for visual clarity
- Present options as numbered lists
- Show progress during processing
- Summarize results in tables when helpful

## Error Handling
- If something goes wrong, explain simply
- Offer alternatives or retry options
- Never expose technical error details

Recent Messages:
{message_history}
"""
```

### Tool Descriptions

```python
# agent/prompts/tools.py

TOOL_DESCRIPTIONS = """
1. **map_questions**: Map exam questions to curriculum competencies
   - Input: Question file, Reference file, Dimension
   - Output: Recommendations with confidence scores

2. **rate_mappings**: Evaluate existing question-to-competency mappings
   - Input: Mapped file, Reference file, Dimension
   - Output: Ratings (correct/partial/incorrect) with suggestions

3. **generate_insights**: Create visual charts from mapping data
   - Input: Mapped file
   - Output: Bar chart, pie chart, histogram, gap analysis, dashboard

4. **export_results**: Export mappings to Excel file
   - Input: Results, Selected indices, Dimension
   - Output: Downloadable Excel file

5. **save_to_library**: Save mapping set for future reference
   - Input: Name, Results, Dimension
   - Output: Library ID

6. **upload_file**: Handle file uploads from user
   - Input: File data
   - Output: File path, validation results
"""
```

---

## Example Conversations

### Example 1: Basic Mapping Flow

```
User: Hi, I need help mapping my exam questions

Agent: Hello! 👋 I'd be happy to help you map your exam questions to
       curriculum competencies.

       To get started, I'll need two files from you:
       1. 📄 Your question bank (CSV or Excel)
       2. 📚 Your reference curriculum (CSV or Excel)

       You can drag & drop files here or click to upload.

User: [Uploads questions.csv and curriculum.csv]

Agent: Great! I've received your files:

       📄 **questions.csv**
       • 50 questions found
       • Columns: Question Number, Question Text

       📚 **curriculum.csv**
       • 15 NMC competencies found
       • Format: MI1.1 - MI15.x

       Which mapping dimension would you like to use?

       1. **NMC Competency** (MI1.1 - MI15.x) ← Recommended based on your file
       2. Area Topics
       3. Competency (C1-C9)
       4. Objective (O1-O9)

User: 1

Agent: Perfect! I'll map your questions to NMC Competencies.

       ⏳ Starting mapping process...

       Processing batch 1/10... ✓
       Processing batch 2/10... ✓
       ...
       Processing batch 10/10... ✓

       ✅ **Mapping Complete!**

       | Metric | Value |
       |--------|-------|
       | Total Questions | 50 |
       | Successfully Mapped | 50 |
       | Average Confidence | 87% |
       | High Confidence (≥85%) | 42 |

       **Coverage by Competency:**
       | Competency | Questions | % |
       |------------|-----------|---|
       | MI1.1 | 8 | 16% |
       | MI2.3 | 5 | 10% |
       | MI3.1 | 7 | 14% |
       | ... | | |

       ⚠️ **Gaps Identified:** MI4.2, MI5.1 have no questions

       What would you like to do next?
       1. 📊 Generate visual charts
       2. 📝 Review individual mappings
       3. 💾 Export to Excel
       4. 🔄 Adjust settings and re-run

User: 1

Agent: Generating visualizations...

       ✅ Charts ready!

       [Shows 4 charts inline:]
       - Topic Bar Chart
       - Coverage Pie Chart
       - Confidence Histogram
       - Gap Analysis

       Would you like to:
       1. Download all charts as ZIP
       2. Export everything to Excel
       3. Make adjustments
       4. Save to library and finish

User: 2

Agent: Exporting to Excel...

       ✅ **Export Complete!**

       📁 [Download: audit_output_nmc_competency_20260127.xlsx]

       The file includes:
       • All 50 questions with mappings
       • Confidence scores and justifications
       • Summary statistics sheet

       Would you like to save this to your library for future reference?

User: Yes, name it "Microbiology Final Exam 2026"

Agent: ✅ Saved to library as "Microbiology Final Exam 2026"
       ID: abc12345

       Is there anything else you'd like me to help with?
       - Start a new mapping
       - Rate an existing mapping
       - Generate more insights
```

---

## Technical Requirements

### Dependencies

```
# agent/requirements.txt
openai>=1.0.0
flask>=3.0.0
flask-cors>=4.0.0
python-dotenv>=1.0.0
rich>=13.0.0          # CLI formatting
prompt_toolkit>=3.0.0  # CLI input
aiofiles>=23.0.0      # Async file handling
```

### Configuration

```env
# Same Azure OpenAI config as integration package
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4

# Agent-specific
AGENT_PORT=5002
AGENT_DEBUG=true
AGENT_MAX_HISTORY=50
```

---

## Implementation Steps

### Phase 1: Core Agent (Day 1-2)
1. [ ] Create `agent/` folder structure
2. [ ] Implement `AgentOrchestrator`
3. [ ] Implement `ConversationState`
4. [ ] Create base `Tool` class
5. [ ] Implement core tools (mapping, rating, insights)
6. [ ] Write system prompts

### Phase 2: CLI Interface (Day 2-3)
1. [ ] Implement CLI with `rich` for formatting
2. [ ] Add file upload handling
3. [ ] Add progress indicators
4. [ ] Test full conversation flow

### Phase 3: Web Interface (Day 3-4)
1. [ ] Create Flask web server
2. [ ] Build chat UI template
3. [ ] Add file upload component
4. [ ] Add chart display
5. [ ] Add download functionality

### Phase 4: Polish & Testing (Day 4-5)
1. [ ] Error handling
2. [ ] Edge cases
3. [ ] Unit tests
4. [ ] Integration tests
5. [ ] Documentation

---

## Questions to Clarify

1. **Interface Preference**: Web chat, CLI, or both?
2. **Deployment**: Same server as integration API or separate?
3. **State Persistence**: Keep conversation history across sessions?
4. **Multi-user**: Support concurrent users?
5. **Customization**: Allow custom prompts/responses?

---

## Summary

This AI Agent will provide:

- 🤖 **Natural conversation** for curriculum mapping
- 📁 **Guided file uploads** with validation
- 🎯 **Smart recommendations** for dimension selection
- 📊 **Automatic visualizations** on request
- 🔄 **Iterative refinement** based on feedback
- 💾 **Seamless export** to Excel

The agent uses the same integration package under the hood, but wraps it in a conversational interface that makes the process intuitive and user-friendly.