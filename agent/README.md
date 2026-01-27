# Curriculum Mapping AI Agent

An autonomous conversational AI agent that guides users through curriculum mapping workflows using natural language.

## Quick Start

### Web Interface (Recommended)

```bash
# From project root
python run_agent.py

# Or specify port
python run_agent.py --port 5002
```

Open http://localhost:5002 in your browser.

### CLI Interface

```bash
python run_agent.py cli
```

## Features

- **Natural Conversation**: Chat naturally to map questions to curriculum
- **Guided Workflow**: Step-by-step guidance through the process
- **File Upload**: Drag & drop or select files in web UI
- **Three Modes**:
  - **Map Questions**: Map unmapped exam questions to competencies
  - **Rate Mappings**: Evaluate existing mappings
  - **Generate Insights**: Create visual charts
- **Smart Recommendations**: Auto-detects dimension, selects high-confidence mappings
- **Visual Results**: Charts displayed inline in chat
- **Export Options**: Download Excel files directly

## Architecture

```
agent/
├── __init__.py           # Package exports
├── __main__.py           # Entry point (python -m agent)
├── config.py             # Configuration
├── conversation.py       # State management
├── orchestrator.py       # Main AI logic
├── prompts.py            # System prompts
├── tools/                # Agent tools
│   ├── mapping.py        # Question mapping
│   ├── rating.py         # Rating existing mappings
│   ├── insights.py       # Chart generation
│   ├── export.py         # Excel export
│   ├── library.py        # Library management
│   └── file_handler.py   # File operations
├── web.py                # Flask web server
├── cli.py                # Terminal interface
└── templates/
    └── chat.html         # Web UI
```

## How It Works

### Conversation Flow

```
1. GREETING
   "Hello! What would you like to do?"
   [Map Questions] [Rate Mappings] [Generate Insights]

2. MODE SELECTION
   User picks a mode

3. FILE UPLOAD
   Agent asks for required files
   User uploads via drag & drop or file picker

4. DIMENSION SELECTION
   Agent recommends a dimension based on files
   User confirms or changes

5. PROCESSING
   Agent runs mapping/rating/insights
   Shows progress

6. RESULTS
   Agent displays summary with stats
   Shows coverage, gaps, confidence

7. OPTIONS
   - Generate charts
   - Review details
   - Export to Excel
   - Save to library
   - Start over

8. ITERATION
   User can refine, export, visualize
   Loop until done
```

### Agent Tools

The agent can use these tools:

| Tool | Description |
|------|-------------|
| `map_questions` | Map questions to curriculum using AI |
| `rate_mappings` | Evaluate existing mappings |
| `generate_insights` | Create visualization charts |
| `export_results` | Export to Excel |
| `save_to_library` | Save to library |
| `get_file_info` | Validate uploaded files |

## Configuration

Uses the same `.env` file as the main project:

```env
# Required
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4

# Agent-specific (optional)
AGENT_PORT=5002
AGENT_DEBUG=false
AGENT_TEMPERATURE=0.7
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Chat UI |
| `/api/chat` | POST | Send message |
| `/api/upload` | POST | Upload file |
| `/api/download/<file>` | GET | Download file |
| `/api/insights/<file>` | GET | Get chart image |
| `/api/reset` | POST | Reset session |
| `/api/state` | GET | Get current state |

### Chat API

```bash
curl -X POST http://localhost:5002/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "Help me map my questions"}'
```

Response:
```json
{
    "success": true,
    "message": "Hello! I'd be happy to help...",
    "options": ["Map Questions", "Rate Mappings", "Generate Insights"],
    "input_type": "choice"
}
```

## Extending the Agent

### Adding a New Tool

1. Create tool in `tools/`:

```python
from .base import BaseTool, ToolResult

class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something useful"
    parameters = {
        "type": "object",
        "properties": {
            "param1": {"type": "string"}
        },
        "required": ["param1"]
    }

    async def execute(self, params: dict) -> ToolResult:
        # Implementation
        return ToolResult(success=True, data=result)
```

2. Register in `orchestrator.py`:

```python
from .tools import MyTool

self.tools['my_tool'] = MyTool(tool_config)
```

### Customizing Prompts

Edit `prompts.py` to change:
- System prompt
- Greeting message
- Mode descriptions
- Processing messages
- Error messages

## Troubleshooting

**Agent won't start**
- Check `.env` file has Azure credentials
- Ensure `integration` package is available

**File upload fails**
- Check file is CSV/Excel format
- File size under 16MB

**Processing hangs**
- Check Azure OpenAI quota
- Reduce batch size

**Charts not showing**
- Ensure matplotlib is installed
- Check `outputs/insights/` folder permissions

## Dependencies

```
openai>=1.0.0       # Azure OpenAI
flask>=3.0.0        # Web server
flask-cors>=4.0.0   # CORS support
pandas>=1.5.0       # Data processing
matplotlib>=3.5.0   # Charts
rich>=13.0.0        # CLI formatting (optional)
```

Install with:
```bash
pip install -r requirements.txt
```
