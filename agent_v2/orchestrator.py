"""
Agent Orchestrator for Curriculum Mapping Agent V2

The orchestrator manages the conversation flow, coordinates with the backend API,
and handles the AI-powered curriculum mapping operations.
"""

import json
import requests
from typing import Dict, List, Optional, Any, Tuple
from openai import AzureOpenAI

from .config import AgentConfig, get_agent_config, BLOOMS_LEVELS, COMPLEXITY_LEVELS
from .conversation import (
    ConversationState, ConversationStep, SessionManager,
    Message, MappingResult, UploadedFile
)


class AgentOrchestrator:
    """
    Main orchestrator for the Curriculum Mapping AI Agent.

    Handles:
    - Conversation flow management
    - User intent detection
    - Backend API communication
    - AI-powered responses and mapping
    """

    def __init__(self, config: AgentConfig = None):
        """Initialize the orchestrator with configuration."""
        self.config = config or get_agent_config()
        self.session_manager = SessionManager(self.config.session_folder)

        # Initialize Azure OpenAI client
        self.ai_client = None
        if self.config.azure_api_key and self.config.azure_endpoint:
            self.ai_client = AzureOpenAI(
                api_key=self.config.azure_api_key,
                api_version=self.config.azure_api_version,
                azure_endpoint=self.config.azure_endpoint
            )

    def create_session(self) -> ConversationState:
        """Create a new conversation session."""
        state = self.session_manager.create_session()
        state.add_assistant_message(self.config.welcome_message)
        return state

    def get_session(self, session_id: str) -> Optional[ConversationState]:
        """Get an existing session."""
        return self.session_manager.get_session(session_id)

    def process_message(self, session_id: str, user_message: str,
                        files: Dict[str, Any] = None) -> Tuple[str, ConversationState]:
        """
        Process a user message and return the agent's response.

        Args:
            session_id: The session identifier
            user_message: The user's message text
            files: Optional dict of uploaded files

        Returns:
            Tuple of (response_text, updated_state)
        """
        state = self.get_session(session_id)
        if not state:
            state = self.create_session()

        # Add user message to history
        state.add_user_message(user_message)

        # Detect intent and route to appropriate handler
        response = self._route_message(state, user_message, files)

        # Add response to history
        state.add_assistant_message(response)

        # Save session
        self.session_manager.save_session(session_id)

        return response, state

    def _route_message(self, state: ConversationState, message: str,
                       files: Dict[str, Any] = None) -> str:
        """Route the message to the appropriate handler based on current step."""
        message_lower = message.lower().strip()

        # Handle file uploads first
        if files:
            return self._handle_file_upload(state, files)

        # Global commands that work in any step
        if message_lower in ['help', '?', 'what can you do']:
            return self._get_help_message()

        if message_lower in ['restart', 'start over', 'reset']:
            return self._handle_restart(state)

        if message_lower in ['status', 'where am i']:
            return self._get_status_message(state)

        # Route based on current step
        step = state.current_step

        if step == ConversationStep.GREETING:
            return self._handle_greeting(state, message)

        elif step == ConversationStep.SELECT_MODE:
            return self._handle_mode_selection(state, message)

        elif step in [ConversationStep.UPLOAD_QUESTIONS, ConversationStep.UPLOAD_REFERENCE,
                      ConversationStep.UPLOAD_MAPPED]:
            return self._handle_waiting_for_upload(state, message)

        elif step == ConversationStep.SELECT_DIMENSION:
            return self._handle_dimension_selection(state, message)

        elif step == ConversationStep.SELECT_MULTIPLE_DIMENSIONS:
            return self._handle_multiple_dimension_selection(state, message)

        elif step == ConversationStep.CONFIRM_PROCESSING:
            return self._handle_confirm_processing(state, message)

        elif step == ConversationStep.SHOW_RESULTS:
            return self._handle_results_interaction(state, message)

        elif step == ConversationStep.REVIEW_RESULTS:
            return self._handle_review_results(state, message)

        elif step == ConversationStep.CONFIRM_SAVE:
            return self._handle_confirm_save(state, message)

        elif step == ConversationStep.SHOW_INSIGHTS:
            return self._handle_insights_interaction(state, message)

        elif step == ConversationStep.COMPLETED:
            return self._handle_completed(state, message)

        elif step == ConversationStep.ERROR:
            return self._handle_error_recovery(state, message)

        # Fallback - use AI to understand intent
        return self._handle_with_ai(state, message)

    def _handle_greeting(self, state: ConversationState, message: str) -> str:
        """Handle initial greeting and mode selection."""
        message_lower = message.lower()

        # Detect mode from message
        if any(w in message_lower for w in ['map', 'mapping', 'unmapped', 'mode a', 'a']):
            state.set_mode('A')
            state.set_step(ConversationStep.UPLOAD_QUESTIONS)
            return """Great! Let's map your questions to the curriculum.

**Mode A: Map Unmapped Questions**

Please upload your files:
1. **Question file** - Excel/CSV with your exam questions
2. **Reference file** - Excel/CSV with curriculum topics/competencies

You can upload both files, or one at a time."""

        elif any(w in message_lower for w in ['rate', 'review', 'improve', 'analyze', 'mode b', 'b']):
            state.set_mode('B')
            state.set_step(ConversationStep.UPLOAD_MAPPED)
            return """Let's review and improve your existing mappings.

**Mode B: Rate & Improve Mappings**

Please upload:
1. **Mapped file** - Excel/CSV with questions that already have mappings
2. **Reference file** - Excel/CSV with curriculum topics (for validation)

You can upload both files, or one at a time."""

        elif any(w in message_lower for w in ['insight', 'visual', 'chart', 'report', 'mode c', 'c']):
            state.set_mode('C')
            state.set_step(ConversationStep.UPLOAD_MAPPED)
            return """Let's generate insights from your mapping data.

**Mode C: Generate Insights**

Please upload your **mapped file** - an Excel/CSV with questions that have been mapped to curriculum topics.

Optionally, upload a **reference file** to identify coverage gaps."""

        # If no clear mode detected, show options
        state.set_step(ConversationStep.SELECT_MODE)
        return """I can help you with three different tasks:

**A. Map Unmapped Questions**
   Map exam questions to curriculum topics/competencies

**B. Rate & Improve Mappings**
   Review existing mappings and suggest corrections

**C. Generate Insights**
   Create visual reports from your mapping data

Which would you like to do? (Enter A, B, or C)"""

    def _handle_mode_selection(self, state: ConversationState, message: str) -> str:
        """Handle mode selection."""
        message_upper = message.upper().strip()

        if message_upper in ['A', 'MODE A', '1', 'MAP']:
            state.set_mode('A')
            state.set_step(ConversationStep.UPLOAD_QUESTIONS)
            return """**Mode A: Map Unmapped Questions** selected.

Please upload your files:
1. **Question file** - Excel/CSV with your exam questions
2. **Reference file** - Excel/CSV with curriculum topics/competencies"""

        elif message_upper in ['B', 'MODE B', '2', 'RATE', 'REVIEW']:
            state.set_mode('B')
            state.set_step(ConversationStep.UPLOAD_MAPPED)
            return """**Mode B: Rate & Improve Mappings** selected.

Please upload:
1. **Mapped file** - Excel/CSV with existing mappings
2. **Reference file** - Excel/CSV with curriculum topics"""

        elif message_upper in ['C', 'MODE C', '3', 'INSIGHTS', 'CHARTS']:
            state.set_mode('C')
            state.set_step(ConversationStep.UPLOAD_MAPPED)
            return """**Mode C: Generate Insights** selected.

Please upload your **mapped file** with existing curriculum mappings."""

        return """Please select a mode:
- **A** - Map unmapped questions
- **B** - Rate & improve mappings
- **C** - Generate insights"""

    def _handle_waiting_for_upload(self, state: ConversationState, message: str) -> str:
        """Handle state when waiting for file upload."""
        message_lower = message.lower()

        if 'skip' in message_lower and state.current_step == ConversationStep.UPLOAD_REFERENCE:
            # Allow skipping reference for built-in dimensions
            return self._prompt_dimension_selection(state)

        return """I'm waiting for your file upload. Please:

1. Click the upload button to select your file(s)
2. Or drag and drop your Excel/CSV files here

Supported formats: .xlsx, .xls, .csv, .ods"""

    def _handle_file_upload(self, state: ConversationState, files: Dict[str, Any]) -> str:
        """Process uploaded files."""
        responses = []

        for file_type, file_info in files.items():
            # Register the file
            state.add_file(
                file_type=file_type,
                filename=file_info.get('filename'),
                original_name=file_info.get('original_name'),
                row_count=file_info.get('row_count', 0),
                columns=file_info.get('columns', []),
                metadata=file_info.get('metadata', {})
            )

            responses.append(f"✓ **{file_info.get('original_name')}** uploaded ({file_info.get('row_count', 0)} rows)")

        # Determine next step based on what's uploaded and current mode
        mode = state.mode

        if mode == 'A':
            if state.has_file('questions') and state.has_file('reference'):
                state.set_step(ConversationStep.SELECT_DIMENSION)
                responses.append("\nBoth files received! " + self._prompt_dimension_selection(state, include_header=False))
            elif state.has_file('questions'):
                state.set_step(ConversationStep.UPLOAD_REFERENCE)
                responses.append("\nNow please upload your **reference file** with curriculum topics.")
            elif state.has_file('reference'):
                state.set_step(ConversationStep.UPLOAD_QUESTIONS)
                responses.append("\nNow please upload your **question file**.")

        elif mode == 'B':
            if state.has_file('mapped') and state.has_file('reference'):
                state.set_step(ConversationStep.SELECT_DIMENSION)
                responses.append("\nBoth files received! " + self._prompt_dimension_selection(state, include_header=False))
            elif state.has_file('mapped'):
                state.set_step(ConversationStep.UPLOAD_REFERENCE)
                responses.append("\nNow please upload your **reference file** for validation.")

        elif mode == 'C':
            if state.has_file('mapped'):
                state.set_step(ConversationStep.CONFIRM_PROCESSING)
                responses.append("\nReady to generate insights! Type **'generate'** to proceed.")

        return '\n'.join(responses)

    def _prompt_dimension_selection(self, state: ConversationState, include_header: bool = True) -> str:
        """Generate the dimension selection prompt."""
        dimensions = self.config.get_dimension_display_names()

        lines = []
        if include_header:
            lines.append("**Select Mapping Dimension(s)**\n")

        lines.append("Which dimension would you like to map to?\n")

        for i, (key, name) in enumerate(dimensions.items(), 1):
            dim = self.config.get_dimension(key)
            ref_note = "" if dim.requires_reference else " (no reference needed)"
            lines.append(f"{i}. **{name}**{ref_note}")

        lines.append("\nEnter a number, name, or 'all' for multiple dimensions:")
        state.set_step(ConversationStep.SELECT_DIMENSION)

        return '\n'.join(lines)

    def _handle_dimension_selection(self, state: ConversationState, message: str) -> str:
        """Handle dimension selection."""
        message_lower = message.lower().strip()
        dimensions = self.config.list_dimensions()
        display_names = self.config.get_dimension_display_names()

        # Check for 'all' or 'multiple'
        if message_lower in ['all', 'multiple', 'multi']:
            state.set_step(ConversationStep.SELECT_MULTIPLE_DIMENSIONS)
            return """Select multiple dimensions by entering numbers separated by commas.
Example: 1, 3, 5

""" + self._prompt_dimension_selection(state, include_header=False)

        # Try to match by number
        try:
            num = int(message_lower)
            if 1 <= num <= len(dimensions):
                selected = dimensions[num - 1]
                state.set_dimensions([selected])
                state.current_dimension = selected
                return self._confirm_processing(state, selected)
        except ValueError:
            pass

        # Try to match by name or key
        for key in dimensions:
            if key == message_lower or display_names[key].lower() == message_lower:
                state.set_dimensions([key])
                state.current_dimension = key
                return self._confirm_processing(state, key)

        # Partial match
        for key in dimensions:
            if message_lower in key or message_lower in display_names[key].lower():
                state.set_dimensions([key])
                state.current_dimension = key
                return self._confirm_processing(state, key)

        return "I didn't recognize that dimension. " + self._prompt_dimension_selection(state)

    def _handle_multiple_dimension_selection(self, state: ConversationState, message: str) -> str:
        """Handle multiple dimension selection."""
        dimensions = self.config.list_dimensions()

        # Parse comma-separated numbers
        try:
            numbers = [int(n.strip()) for n in message.split(',')]
            selected = []
            for num in numbers:
                if 1 <= num <= len(dimensions):
                    selected.append(dimensions[num - 1])

            if selected:
                state.set_dimensions(selected)
                state.current_dimension = selected[0]
                names = [self.config.get_dimension(d).name for d in selected]
                return self._confirm_processing(state, ', '.join(names))
        except ValueError:
            pass

        return "Please enter dimension numbers separated by commas (e.g., 1, 3, 5)"

    def _confirm_processing(self, state: ConversationState, dimension_name: str) -> str:
        """Confirm before starting processing."""
        state.set_step(ConversationStep.CONFIRM_PROCESSING)

        mode_desc = {
            'A': 'map questions to curriculum',
            'B': 'rate and improve existing mappings',
            'C': 'generate insights'
        }.get(state.mode, 'process')

        file_info = []
        if state.has_file('questions'):
            f = state.get_file('questions')
            file_info.append(f"• Questions: {f.original_name} ({f.row_count} rows)")
        if state.has_file('mapped'):
            f = state.get_file('mapped')
            file_info.append(f"• Mapped file: {f.original_name} ({f.row_count} rows)")
        if state.has_file('reference'):
            f = state.get_file('reference')
            file_info.append(f"• Reference: {f.original_name}")

        return f"""**Ready to {mode_desc}**

**Dimension:** {dimension_name}
**Files:**
{chr(10).join(file_info)}

Type **'start'** or **'go'** to begin processing, or **'change'** to modify settings."""

    def _handle_confirm_processing(self, state: ConversationState, message: str) -> str:
        """Handle confirmation before processing."""
        message_lower = message.lower().strip()

        if message_lower in ['start', 'go', 'yes', 'proceed', 'run', 'begin', 'ok', 'generate']:
            return self._start_processing(state)

        elif message_lower in ['change', 'modify', 'back', 'edit']:
            state.set_step(ConversationStep.SELECT_DIMENSION)
            return self._prompt_dimension_selection(state)

        elif message_lower in ['cancel', 'stop', 'no']:
            return self._handle_restart(state)

        return "Type **'start'** to begin processing, **'change'** to modify settings, or **'cancel'** to start over."

    def _start_processing(self, state: ConversationState) -> str:
        """Start the mapping/rating/insights process."""
        state.set_processing(True, 0.0, "Starting...")

        mode = state.mode

        try:
            if mode == 'A':
                return self._process_mode_a(state)
            elif mode == 'B':
                return self._process_mode_b(state)
            elif mode == 'C':
                return self._process_mode_c(state)
        except Exception as e:
            state.set_error(str(e))
            return f"An error occurred: {str(e)}\n\nType **'retry'** to try again or **'restart'** to start over."

    def _process_mode_a(self, state: ConversationState) -> str:
        """Process Mode A: Map unmapped questions."""
        dimension = state.current_dimension

        if self.config.use_backend_api:
            # Use existing backend API
            try:
                response = requests.post(
                    f"{self.config.backend_url}/api/run-audit-efficient",
                    json={
                        'question_file': state.get_file('questions').filename,
                        'reference_file': state.get_file('reference').filename,
                        'dimension': dimension,
                        'batch_size': self.config.max_questions_per_batch
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    return self._format_mapping_results(state, result, dimension)
                else:
                    raise Exception(f"Backend error: {response.text}")

            except requests.exceptions.ConnectionError:
                return self._process_with_ai(state, dimension)
        else:
            return self._process_with_ai(state, dimension)

    def _process_mode_b(self, state: ConversationState) -> str:
        """Process Mode B: Rate existing mappings."""
        dimension = state.current_dimension

        if self.config.use_backend_api:
            try:
                response = requests.post(
                    f"{self.config.backend_url}/api/rate-mappings",
                    json={
                        'mapped_file': state.get_file('mapped').filename,
                        'reference_file': state.get_file('reference').filename,
                        'dimension': dimension,
                        'batch_size': self.config.max_questions_per_batch
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    return self._format_rating_results(state, result, dimension)
                else:
                    raise Exception(f"Backend error: {response.text}")

            except requests.exceptions.ConnectionError:
                return "Backend service not available. Please ensure the backend is running on port 5001."
        else:
            return "Direct processing not implemented. Please use backend API."

    def _process_mode_c(self, state: ConversationState) -> str:
        """Process Mode C: Generate insights."""
        if self.config.use_backend_api:
            try:
                payload = {'mapped_file': state.get_file('mapped').filename}
                if state.has_file('reference'):
                    payload['reference_file'] = state.get_file('reference').filename

                response = requests.post(
                    f"{self.config.backend_url}/api/generate-insights",
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    return self._format_insights_results(state, result)
                else:
                    raise Exception(f"Backend error: {response.text}")

            except requests.exceptions.ConnectionError:
                return "Backend service not available. Please ensure the backend is running on port 5001."
        else:
            return "Direct processing not implemented. Please use backend API."

    def _process_with_ai(self, state: ConversationState, dimension: str) -> str:
        """Process mapping using direct AI call (fallback when backend unavailable)."""
        if not self.ai_client:
            return "AI client not configured. Please check Azure OpenAI credentials."

        # This is a simplified version - full implementation would read files and process
        return "Direct AI processing is available. Backend API recommended for full functionality."

    def _format_mapping_results(self, state: ConversationState, result: Dict, dimension: str) -> str:
        """Format mapping results for display."""
        state.set_processing(False)
        state.set_step(ConversationStep.SHOW_RESULTS)

        recommendations = result.get('recommendations', [])

        # Store results
        mapping_results = []
        for rec in recommendations:
            mapping_results.append(MappingResult(
                question_num=str(rec.get('question_num', '')),
                question_text=rec.get('question_text', '')[:200],
                mapped_value=rec.get('mapped_topic', rec.get('mapped_value', '')),
                confidence=rec.get('confidence', 0.0),
                justification=rec.get('justification', ''),
                dimension=dimension,
                selected=rec.get('confidence', 0) >= self.config.default_confidence_threshold
            ))

        state.add_results(dimension, mapping_results)

        # Format response
        dim_name = self.config.get_dimension(dimension).name
        high_conf = sum(1 for r in mapping_results if r.confidence >= 0.85)
        med_conf = sum(1 for r in mapping_results if 0.70 <= r.confidence < 0.85)
        low_conf = sum(1 for r in mapping_results if r.confidence < 0.70)

        lines = [
            f"**Mapping Complete!** ({dim_name})",
            "",
            f"**Results:** {len(mapping_results)} questions mapped",
            f"• High confidence (85%+): {high_conf}",
            f"• Medium confidence (70-84%): {med_conf}",
            f"• Low confidence (<70%): {low_conf}",
            "",
            "**Actions:**",
            "• Type **'show'** to view results",
            "• Type **'select all'** or **'select high'** to select mappings",
            "• Type **'save'** to save and download results"
        ]

        return '\n'.join(lines)

    def _format_rating_results(self, state: ConversationState, result: Dict, dimension: str) -> str:
        """Format rating results for display."""
        state.set_processing(False)
        state.set_step(ConversationStep.SHOW_RESULTS)

        # Similar to mapping results but includes rating info
        summary = result.get('summary', {})

        lines = [
            "**Rating Complete!**",
            "",
            f"**Summary:**",
            f"• Correct mappings: {summary.get('correct', 0)}",
            f"• Partially correct: {summary.get('partial', 0)}",
            f"• Needs correction: {summary.get('incorrect', 0)}",
            "",
            "**Actions:**",
            "• Type **'show'** to view detailed results",
            "• Type **'apply'** to apply suggested corrections",
            "• Type **'save'** to save results"
        ]

        return '\n'.join(lines)

    def _format_insights_results(self, state: ConversationState, result: Dict) -> str:
        """Format insights results for display."""
        state.set_processing(False)
        state.set_step(ConversationStep.SHOW_INSIGHTS)

        state.insights = result

        charts = result.get('charts', {})
        summary = result.get('summary', {})

        lines = [
            "**Insights Generated!**",
            "",
            f"**Summary:**",
            f"• Total questions: {summary.get('total_questions', 0)}",
            f"• Topics covered: {summary.get('topics_covered', 0)}",
            f"• Average confidence: {summary.get('average_confidence', 0):.1%}",
            "",
            f"**Charts Generated:** {len(charts)}",
        ]

        for chart_name in charts.keys():
            lines.append(f"• {chart_name.replace('_', ' ').title()}")

        lines.extend([
            "",
            "**Actions:**",
            "• Type **'view [chart_name]'** to see a specific chart",
            "• Type **'download'** to get all charts",
            "• Type **'done'** when finished"
        ])

        return '\n'.join(lines)

    def _handle_results_interaction(self, state: ConversationState, message: str) -> str:
        """Handle interaction with results."""
        message_lower = message.lower().strip()
        dimension = state.current_dimension

        if message_lower in ['show', 'view', 'list', 'results']:
            return self._show_results(state, dimension)

        elif message_lower in ['select all', 'all']:
            state.select_all_results(dimension, True)
            count = len(state.get_selected_results(dimension))
            return f"Selected all {count} mappings."

        elif message_lower in ['select none', 'none', 'clear', 'deselect']:
            state.select_all_results(dimension, False)
            return "Cleared all selections."

        elif message_lower in ['select high', 'high confidence', 'high']:
            state.select_high_confidence(dimension, 0.85)
            count = len(state.get_selected_results(dimension))
            return f"Selected {count} high-confidence (85%+) mappings."

        elif message_lower in ['save', 'download', 'export', 'apply']:
            state.set_step(ConversationStep.CONFIRM_SAVE)
            count = len(state.get_selected_results(dimension))
            return f"""**Save & Download**

You have {count} mappings selected.

Please enter a name for this mapping set, or type **'save'** to use the default name."""

        elif message_lower == 'done':
            return self._handle_completed(state, message)

        return """Available commands:
• **show** - View mapping results
• **select all** / **select none** - Select/deselect all
• **select high** - Select high-confidence mappings only
• **save** - Save and download results
• **done** - Finish this session"""

    def _show_results(self, state: ConversationState, dimension: str, limit: int = 10) -> str:
        """Show mapping results."""
        results = state.get_results(dimension)
        if not results:
            return "No results available."

        lines = [f"**Mapping Results** (showing {min(limit, len(results))} of {len(results)})", ""]

        for i, r in enumerate(results[:limit]):
            status = "✓" if r.selected else "○"
            conf_pct = f"{r.confidence:.0%}"
            lines.append(f"{status} **Q{r.question_num}** → {r.mapped_value} ({conf_pct})")
            if r.question_text:
                lines.append(f"   _{r.question_text[:80]}..._" if len(r.question_text) > 80 else f"   _{r.question_text}_")

        if len(results) > limit:
            lines.append(f"\n...and {len(results) - limit} more. Type **'show all'** to see all.")

        selected = len(state.get_selected_results(dimension))
        lines.append(f"\n**Selected:** {selected} of {len(results)}")

        return '\n'.join(lines)

    def _handle_confirm_save(self, state: ConversationState, message: str) -> str:
        """Handle save confirmation."""
        message_lower = message.lower().strip()

        if message_lower in ['save', 'yes', 'ok', 'confirm']:
            name = f"Mapping_{state.session_id[:8]}"
        elif message_lower in ['cancel', 'no', 'back']:
            state.set_step(ConversationStep.SHOW_RESULTS)
            return "Save cancelled. Returning to results."
        else:
            name = message.strip()

        # Perform save via backend
        if self.config.use_backend_api:
            try:
                dimension = state.current_dimension
                results = state.get_results(dimension)
                selected_indices = [i for i, r in enumerate(results) if r.selected]

                # Convert results to recommendations format
                recommendations = []
                for r in results:
                    recommendations.append({
                        'question_num': r.question_num,
                        'question_text': r.question_text,
                        'mapped_topic': r.mapped_value,
                        'confidence': r.confidence,
                        'justification': r.justification
                    })

                response = requests.post(
                    f"{self.config.backend_url}/api/apply-and-save",
                    json={
                        'question_file': state.get_file('questions').filename if state.has_file('questions') else state.get_file('mapped').filename,
                        'recommendations': recommendations,
                        'selected_indices': selected_indices,
                        'dimension': dimension,
                        'name': name
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    state.set_step(ConversationStep.COMPLETED)
                    return f"""**Saved Successfully!**

• Library ID: {result.get('library_id', 'N/A')}
• Name: {result.get('library_name', name)}
• Download: {result.get('download_url', 'N/A')}

Type **'new'** to start a new mapping session or **'exit'** to finish."""

            except requests.exceptions.ConnectionError:
                return "Backend service not available. Please ensure the backend is running."

        return "Save completed. Type **'new'** to start a new session."

    def _handle_insights_interaction(self, state: ConversationState, message: str) -> str:
        """Handle interaction with insights."""
        message_lower = message.lower().strip()

        if message_lower in ['download', 'export', 'get']:
            charts = state.insights.get('charts', {})
            if charts:
                lines = ["**Chart Downloads:**", ""]
                for name, url in charts.items():
                    lines.append(f"• [{name}]({url})")
                return '\n'.join(lines)
            return "No charts available for download."

        elif message_lower in ['done', 'finish', 'exit']:
            return self._handle_completed(state, message)

        elif message_lower.startswith('view '):
            chart_name = message_lower.replace('view ', '').strip()
            charts = state.insights.get('charts', {})
            for name, url in charts.items():
                if chart_name in name.lower():
                    return f"**{name}**\n\nView at: {url}"
            return f"Chart '{chart_name}' not found."

        return """Available commands:
• **view [chart_name]** - View a specific chart
• **download** - Get download links for all charts
• **done** - Finish this session"""

    def _handle_completed(self, state: ConversationState, message: str) -> str:
        """Handle completed state."""
        message_lower = message.lower().strip()

        if message_lower in ['new', 'again', 'restart', 'start']:
            return self._handle_restart(state)

        elif message_lower in ['exit', 'quit', 'bye', 'done']:
            state.set_step(ConversationStep.COMPLETED)
            return """Thank you for using the Curriculum Mapping Agent!

Your session has been saved. You can resume it later using your session ID:
**{state.session_id}**

Goodbye!"""

        return """Session complete! What would you like to do?
• **new** - Start a new mapping session
• **exit** - End this session"""

    def _handle_restart(self, state: ConversationState) -> str:
        """Reset the session for a new task."""
        # Keep session ID but reset state
        state.mode = None
        state.current_step = ConversationStep.GREETING
        state.files.clear()
        state.selected_dimensions.clear()
        state.current_dimension = None
        state.results.clear()
        state.insights.clear()
        state.clear_error()

        return self.config.welcome_message

    def _handle_error_recovery(self, state: ConversationState, message: str) -> str:
        """Handle recovery from error state."""
        message_lower = message.lower().strip()

        if message_lower in ['retry', 'try again']:
            state.clear_error()
            state.set_step(ConversationStep.CONFIRM_PROCESSING)
            return "Let's try again. Type **'start'** to begin processing."

        elif message_lower in ['restart', 'start over']:
            return self._handle_restart(state)

        error = state.last_error or "Unknown error"
        return f"""An error occurred: {error}

• Type **'retry'** to try again
• Type **'restart'** to start over"""

    def _handle_with_ai(self, state: ConversationState, message: str) -> str:
        """Use AI to understand and respond to unstructured messages."""
        if not self.ai_client:
            return "I'm not sure what you mean. Type **'help'** for available commands."

        try:
            # Create context-aware prompt
            context = state.get_context_summary()
            system_prompt = f"""You are a helpful curriculum mapping assistant.
Current context: {context}
Help the user with their curriculum mapping task. Be concise and helpful."""

            response = self.ai_client.chat.completions.create(
                model=self.config.azure_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=500,
                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"I'm not sure what you mean. Type **'help'** for available commands."

    def _get_help_message(self) -> str:
        """Return help message."""
        return """**Curriculum Mapping Agent - Help**

**Modes:**
• **A** - Map unmapped questions to curriculum
• **B** - Rate and improve existing mappings
• **C** - Generate visual insights from mappings

**Commands:**
• **help** - Show this help message
• **status** - Show current session status
• **restart** - Start a new session

**During Results:**
• **show** - View mapping results
• **select all/none/high** - Select mappings
• **save** - Save and download results

**Dimensions Supported:**
• Area Topics, Competency, Objective, Skill
• NMC Competency, Blooms Taxonomy, Complexity

Need more help? Just ask!"""

    def _get_status_message(self, state: ConversationState) -> str:
        """Return current status."""
        return f"""**Current Status**

{state.get_context_summary()}

Type **'help'** for available commands."""
