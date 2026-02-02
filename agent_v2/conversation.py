"""
Conversation Management for Agent V2

Handles conversation state, history, and step tracking for the
conversational curriculum mapping agent.
"""

import uuid
import json
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from pathlib import Path


class ConversationStep(Enum):
    """Steps in the curriculum mapping conversation flow."""

    # Initial state
    GREETING = "greeting"

    # Mode selection
    SELECT_MODE = "select_mode"

    # File upload steps
    UPLOAD_QUESTIONS = "upload_questions"
    UPLOAD_REFERENCE = "upload_reference"
    UPLOAD_MAPPED = "upload_mapped"

    # Dimension selection
    SELECT_DIMENSION = "select_dimension"
    SELECT_MULTIPLE_DIMENSIONS = "select_multiple_dimensions"

    # Processing steps
    CONFIRM_PROCESSING = "confirm_processing"
    PROCESSING = "processing"

    # Results steps
    SHOW_RESULTS = "show_results"
    REVIEW_RESULTS = "review_results"
    SELECT_MAPPINGS = "select_mappings"

    # Save/Export steps
    CONFIRM_SAVE = "confirm_save"
    SAVING = "saving"

    # Insights steps
    GENERATING_INSIGHTS = "generating_insights"
    SHOW_INSIGHTS = "show_insights"

    # Completion
    COMPLETED = "completed"

    # Error handling
    ERROR = "error"


@dataclass
class Message:
    """A single message in the conversation."""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UploadedFile:
    """Information about an uploaded file."""
    filename: str
    original_name: str
    file_type: str  # 'questions', 'reference', 'mapped'
    upload_time: str = field(default_factory=lambda: datetime.now().isoformat())
    row_count: int = 0
    columns: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MappingResult:
    """Result of a mapping operation."""
    question_num: str
    question_text: str
    mapped_value: str
    confidence: float
    justification: str
    dimension: str
    selected: bool = False
    original_mapping: Optional[str] = None  # For Mode B (rating existing)


@dataclass
class ConversationState:
    """Complete state of a conversation session."""

    # Session identification
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Current step in the conversation flow
    current_step: ConversationStep = ConversationStep.GREETING

    # Selected mode: 'A' (Map), 'B' (Rate), 'C' (Insights)
    mode: Optional[str] = None

    # Conversation history
    messages: List[Message] = field(default_factory=list)

    # Uploaded files
    files: Dict[str, UploadedFile] = field(default_factory=dict)

    # Selected dimensions for mapping
    selected_dimensions: List[str] = field(default_factory=list)
    current_dimension: Optional[str] = None

    # Mapping results (keyed by dimension)
    results: Dict[str, List[MappingResult]] = field(default_factory=dict)

    # Insights data
    insights: Dict[str, Any] = field(default_factory=dict)

    # Error tracking
    last_error: Optional[str] = None

    # Processing status
    is_processing: bool = False
    processing_progress: float = 0.0
    processing_message: str = ""

    # User preferences within session
    preferences: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> Message:
        """Add a message to the conversation history."""
        msg = Message(role=role, content=content, metadata=metadata or {})
        self.messages.append(msg)
        self.updated_at = datetime.now().isoformat()
        return msg

    def add_user_message(self, content: str, metadata: Dict[str, Any] = None) -> Message:
        """Add a user message."""
        return self.add_message('user', content, metadata)

    def add_assistant_message(self, content: str, metadata: Dict[str, Any] = None) -> Message:
        """Add an assistant message."""
        return self.add_message('assistant', content, metadata)

    def add_system_message(self, content: str, metadata: Dict[str, Any] = None) -> Message:
        """Add a system message."""
        return self.add_message('system', content, metadata)

    def set_step(self, step: ConversationStep):
        """Update the current conversation step."""
        self.current_step = step
        self.updated_at = datetime.now().isoformat()

    def set_mode(self, mode: str):
        """Set the operation mode."""
        if mode in ['A', 'B', 'C']:
            self.mode = mode
            self.updated_at = datetime.now().isoformat()

    def add_file(self, file_type: str, filename: str, original_name: str,
                 row_count: int = 0, columns: List[str] = None,
                 metadata: Dict[str, Any] = None) -> UploadedFile:
        """Register an uploaded file."""
        uploaded = UploadedFile(
            filename=filename,
            original_name=original_name,
            file_type=file_type,
            row_count=row_count,
            columns=columns or [],
            metadata=metadata or {}
        )
        self.files[file_type] = uploaded
        self.updated_at = datetime.now().isoformat()
        return uploaded

    def get_file(self, file_type: str) -> Optional[UploadedFile]:
        """Get an uploaded file by type."""
        return self.files.get(file_type)

    def has_file(self, file_type: str) -> bool:
        """Check if a file type has been uploaded."""
        return file_type in self.files

    def add_dimension(self, dimension: str):
        """Add a dimension to the selected list."""
        if dimension not in self.selected_dimensions:
            self.selected_dimensions.append(dimension)
            self.updated_at = datetime.now().isoformat()

    def set_dimensions(self, dimensions: List[str]):
        """Set the selected dimensions list."""
        self.selected_dimensions = dimensions
        self.updated_at = datetime.now().isoformat()

    def add_results(self, dimension: str, results: List[MappingResult]):
        """Store mapping results for a dimension."""
        self.results[dimension] = results
        self.updated_at = datetime.now().isoformat()

    def get_results(self, dimension: str) -> List[MappingResult]:
        """Get mapping results for a dimension."""
        return self.results.get(dimension, [])

    def get_selected_results(self, dimension: str) -> List[MappingResult]:
        """Get only the selected mapping results for a dimension."""
        return [r for r in self.results.get(dimension, []) if r.selected]

    def select_result(self, dimension: str, index: int, selected: bool = True):
        """Select or deselect a specific result."""
        if dimension in self.results and 0 <= index < len(self.results[dimension]):
            self.results[dimension][index].selected = selected
            self.updated_at = datetime.now().isoformat()

    def select_all_results(self, dimension: str, selected: bool = True):
        """Select or deselect all results for a dimension."""
        if dimension in self.results:
            for result in self.results[dimension]:
                result.selected = selected
            self.updated_at = datetime.now().isoformat()

    def select_high_confidence(self, dimension: str, threshold: float = 0.85):
        """Select only high-confidence results."""
        if dimension in self.results:
            for result in self.results[dimension]:
                result.selected = result.confidence >= threshold
            self.updated_at = datetime.now().isoformat()

    def set_processing(self, is_processing: bool, progress: float = 0.0, message: str = ""):
        """Update processing status."""
        self.is_processing = is_processing
        self.processing_progress = progress
        self.processing_message = message
        self.updated_at = datetime.now().isoformat()

    def set_error(self, error: str):
        """Set an error state."""
        self.last_error = error
        self.current_step = ConversationStep.ERROR
        self.updated_at = datetime.now().isoformat()

    def clear_error(self):
        """Clear any error state."""
        self.last_error = None
        self.updated_at = datetime.now().isoformat()

    def get_context_summary(self) -> str:
        """Get a summary of the current conversation context."""
        parts = [f"Session: {self.session_id[:8]}"]
        parts.append(f"Step: {self.current_step.value}")

        if self.mode:
            mode_names = {'A': 'Map Questions', 'B': 'Rate Mappings', 'C': 'Generate Insights'}
            parts.append(f"Mode: {mode_names.get(self.mode, self.mode)}")

        if self.files:
            parts.append(f"Files: {', '.join(self.files.keys())}")

        if self.selected_dimensions:
            parts.append(f"Dimensions: {', '.join(self.selected_dimensions)}")

        if self.results:
            total = sum(len(r) for r in self.results.values())
            selected = sum(len([x for x in r if x.selected]) for r in self.results.values())
            parts.append(f"Results: {selected}/{total} selected")

        return " | ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'current_step': self.current_step.value,
            'mode': self.mode,
            'messages': [asdict(m) for m in self.messages],
            'files': {k: asdict(v) for k, v in self.files.items()},
            'selected_dimensions': self.selected_dimensions,
            'current_dimension': self.current_dimension,
            'results': {k: [asdict(r) for r in v] for k, v in self.results.items()},
            'insights': self.insights,
            'last_error': self.last_error,
            'is_processing': self.is_processing,
            'processing_progress': self.processing_progress,
            'processing_message': self.processing_message,
            'preferences': self.preferences
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationState':
        """Create state from dictionary."""
        state = cls()
        state.session_id = data.get('session_id', state.session_id)
        state.created_at = data.get('created_at', state.created_at)
        state.updated_at = data.get('updated_at', state.updated_at)
        state.current_step = ConversationStep(data.get('current_step', 'greeting'))
        state.mode = data.get('mode')

        # Restore messages
        for msg_data in data.get('messages', []):
            state.messages.append(Message(**msg_data))

        # Restore files
        for file_type, file_data in data.get('files', {}).items():
            state.files[file_type] = UploadedFile(**file_data)

        state.selected_dimensions = data.get('selected_dimensions', [])
        state.current_dimension = data.get('current_dimension')

        # Restore results
        for dim, results_data in data.get('results', {}).items():
            state.results[dim] = [MappingResult(**r) for r in results_data]

        state.insights = data.get('insights', {})
        state.last_error = data.get('last_error')
        state.is_processing = data.get('is_processing', False)
        state.processing_progress = data.get('processing_progress', 0.0)
        state.processing_message = data.get('processing_message', '')
        state.preferences = data.get('preferences', {})

        return state

    def save(self, folder: str):
        """Save state to a JSON file."""
        path = Path(folder) / f"{self.session_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, folder: str, session_id: str) -> Optional['ConversationState']:
        """Load state from a JSON file."""
        path = Path(folder) / f"{session_id}.json"
        if path.exists():
            with open(path, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        return None


class SessionManager:
    """Manages multiple conversation sessions."""

    def __init__(self, session_folder: str = 'agent_v2/sessions'):
        self.session_folder = session_folder
        self._sessions: Dict[str, ConversationState] = {}
        Path(session_folder).mkdir(parents=True, exist_ok=True)

    def create_session(self) -> ConversationState:
        """Create a new conversation session."""
        state = ConversationState()
        self._sessions[state.session_id] = state
        return state

    def get_session(self, session_id: str) -> Optional[ConversationState]:
        """Get an existing session by ID."""
        if session_id in self._sessions:
            return self._sessions[session_id]
        # Try to load from disk
        state = ConversationState.load(self.session_folder, session_id)
        if state:
            self._sessions[session_id] = state
        return state

    def save_session(self, session_id: str):
        """Save a session to disk."""
        if session_id in self._sessions:
            self._sessions[session_id].save(self.session_folder)

    def delete_session(self, session_id: str):
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
        path = Path(self.session_folder) / f"{session_id}.json"
        if path.exists():
            path.unlink()

    def list_sessions(self) -> List[str]:
        """List all session IDs."""
        sessions = set(self._sessions.keys())
        for path in Path(self.session_folder).glob('*.json'):
            sessions.add(path.stem)
        return sorted(sessions)
