"""
Conversation State Management

Tracks the entire conversation flow, files, results, and user decisions.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json


class ConversationStep(Enum):
    """Steps in the conversation flow"""
    GREETING = "greeting"
    MODE_SELECTION = "mode_selection"
    FILE_UPLOAD = "file_upload"
    FILE_VALIDATION = "file_validation"
    DIMENSION_SELECTION = "dimension_selection"
    PROCESSING = "processing"
    RESULTS = "results"
    OPTIONS = "options"
    REVIEW = "review"
    VISUALIZATION = "visualization"
    EXPORT = "export"
    ENHANCEMENT = "enhancement"
    COMPLETE = "complete"


@dataclass
class Message:
    """A single message in the conversation"""
    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    def to_api_format(self) -> dict:
        """Format for OpenAI API"""
        return {"role": self.role, "content": self.content}


@dataclass
class FileInfo:
    """Information about an uploaded file"""
    filename: str
    path: str
    file_type: str  # "question", "reference", "mapped"
    row_count: int = 0
    columns: List[str] = field(default_factory=list)
    validated: bool = False
    validation_message: str = ""


@dataclass
class ConversationState:
    """
    Maintains the full state of a conversation session.
    """
    # Session info
    session_id: str = ""
    started_at: datetime = field(default_factory=datetime.now)

    # Current position in flow
    step: ConversationStep = ConversationStep.GREETING

    # User selections
    mode: Optional[str] = None  # "map", "rate", "insights"
    dimension: Optional[str] = None

    # Files
    files: Dict[str, FileInfo] = field(default_factory=dict)

    # Results from processing
    results: Optional[Dict[str, Any]] = None
    recommendations: List[Dict] = field(default_factory=list)
    selected_indices: List[int] = field(default_factory=list)

    # Generated outputs
    charts: Dict[str, str] = field(default_factory=dict)
    export_file: Optional[str] = None
    library_id: Optional[str] = None

    # Conversation history
    messages: List[Message] = field(default_factory=list)
    tool_calls: List[Dict] = field(default_factory=list)

    # Flags
    awaiting_file_upload: bool = False
    awaiting_user_choice: bool = False
    current_options: List[str] = field(default_factory=list)

    def add_message(self, role: str, content: str, **metadata) -> None:
        """Add a message to history"""
        self.messages.append(Message(
            role=role,
            content=content,
            metadata=metadata
        ))

    def add_file(self, file_type: str, file_info: FileInfo) -> None:
        """Add an uploaded file"""
        self.files[file_type] = file_info

    def add_tool_call(self, tool_name: str, params: dict, result: Any) -> None:
        """Record a tool execution"""
        self.tool_calls.append({
            "tool": tool_name,
            "params": params,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

    def get_context_summary(self) -> str:
        """Get a summary of current state for LLM context"""
        files_summary = []
        for ftype, finfo in self.files.items():
            files_summary.append(f"  - {ftype}: {finfo.filename} ({finfo.row_count} rows)")

        return f"""
=== CONVERSATION STATE ===
Session: {self.session_id}
Step: {self.step.value}
Mode: {self.mode or 'Not selected'}
Dimension: {self.dimension or 'Not selected'}

Files Uploaded:
{chr(10).join(files_summary) if files_summary else '  None'}

Has Results: {bool(self.results)}
{f"Questions Mapped: {len(self.recommendations)}" if self.recommendations else ""}
{f"Selected: {len(self.selected_indices)}" if self.selected_indices else ""}
Charts Generated: {len(self.charts)}
Export Ready: {bool(self.export_file)}

Awaiting: {'File upload' if self.awaiting_file_upload else 'Choice' if self.awaiting_user_choice else 'User input'}
===========================
"""

    def get_messages_for_api(self, limit: int = 20) -> List[dict]:
        """Get recent messages formatted for OpenAI API"""
        recent = self.messages[-limit:] if len(self.messages) > limit else self.messages
        return [m.to_api_format() for m in recent if m.role in ("user", "assistant")]

    def set_step(self, step: ConversationStep) -> None:
        """Update the current step"""
        self.step = step

    def advance_step(self) -> None:
        """Move to the next logical step based on current state"""
        step_flow = {
            ConversationStep.GREETING: ConversationStep.MODE_SELECTION,
            ConversationStep.MODE_SELECTION: ConversationStep.FILE_UPLOAD,
            ConversationStep.FILE_UPLOAD: ConversationStep.FILE_VALIDATION,
            ConversationStep.FILE_VALIDATION: ConversationStep.DIMENSION_SELECTION,
            ConversationStep.DIMENSION_SELECTION: ConversationStep.PROCESSING,
            ConversationStep.PROCESSING: ConversationStep.RESULTS,
            ConversationStep.RESULTS: ConversationStep.OPTIONS,
            ConversationStep.OPTIONS: ConversationStep.ENHANCEMENT,
            ConversationStep.REVIEW: ConversationStep.OPTIONS,
            ConversationStep.VISUALIZATION: ConversationStep.OPTIONS,
            ConversationStep.EXPORT: ConversationStep.OPTIONS,
            ConversationStep.ENHANCEMENT: ConversationStep.COMPLETE,
        }
        if self.step in step_flow:
            self.step = step_flow[self.step]

    def reset(self) -> None:
        """Reset state for a new conversation"""
        self.step = ConversationStep.GREETING
        self.mode = None
        self.dimension = None
        self.files = {}
        self.results = None
        self.recommendations = []
        self.selected_indices = []
        self.charts = {}
        self.export_file = None
        self.library_id = None
        self.messages = []
        self.tool_calls = []
        self.awaiting_file_upload = False
        self.awaiting_user_choice = False
        self.current_options = []

    def to_dict(self) -> dict:
        """Serialize state to dictionary"""
        return {
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "step": self.step.value,
            "mode": self.mode,
            "dimension": self.dimension,
            "files": {k: v.__dict__ for k, v in self.files.items()},
            "has_results": bool(self.results),
            "recommendation_count": len(self.recommendations),
            "selected_count": len(self.selected_indices),
            "charts": self.charts,
            "export_file": self.export_file,
            "library_id": self.library_id,
            "message_count": len(self.messages)
        }
