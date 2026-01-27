"""
Agent Orchestrator

The main brain of the AI Agent. Handles:
- Message processing
- Tool selection and execution
- Response generation
- Conversation flow management
"""

import json
import uuid
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from openai import AzureOpenAI

from .config import AgentConfig
from .conversation import ConversationState, ConversationStep, FileInfo
from .prompts import (
    SYSTEM_PROMPT, TOOL_DESCRIPTIONS, GREETING_MESSAGE,
    MODE_DESCRIPTIONS, DIMENSION_DESCRIPTIONS,
    OPTIONS_AFTER_MAPPING, OPTIONS_AFTER_RATING,
    PROCESSING_MESSAGES, ERROR_MESSAGES
)
from .tools import (
    MappingTool, RatingTool, InsightsTool,
    ExportTool, LibraryTool, FileHandlerTool
)


@dataclass
class AgentResponse:
    """Response from the agent"""
    message: str
    options: Optional[List[str]] = None
    files: Optional[List[str]] = None
    charts: Optional[Dict[str, str]] = None
    download_url: Optional[str] = None
    requires_input: bool = True
    input_type: str = "text"  # "text", "file", "choice"
    state: Optional[Dict] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentOrchestrator:
    """
    Main orchestrator for the AI Agent.

    Usage:
        config = get_agent_config()
        agent = AgentOrchestrator(config)

        response = await agent.process_message("Help me map questions")
        print(response.message)
    """

    def __init__(self, config: AgentConfig):
        self.config = config

        # Initialize OpenAI client
        self.client = AzureOpenAI(
            api_key=config.api_key,
            azure_endpoint=config.azure_endpoint,
            api_version=config.api_version
        )
        self.deployment = config.deployment

        # Initialize conversation state
        self.state = ConversationState(
            session_id=str(uuid.uuid4())[:8]
        )

        # Initialize tools
        tool_config = config.get_azure_config()
        tool_config['upload_folder'] = config.upload_folder
        tool_config['output_folder'] = config.output_folder
        tool_config['insights_folder'] = config.insights_folder
        tool_config['library_folder'] = config.library_folder

        self.tools = {
            'map_questions': MappingTool(tool_config),
            'rate_mappings': RatingTool(tool_config),
            'generate_insights': InsightsTool(tool_config),
            'export_results': ExportTool(tool_config),
            'save_to_library': LibraryTool(tool_config),
            'get_file_info': FileHandlerTool(tool_config)
        }

    async def process_message(
        self,
        user_message: str,
        files: Optional[List[Dict]] = None
    ) -> AgentResponse:
        """
        Process a user message and generate a response.

        Args:
            user_message: The user's input text
            files: Optional list of uploaded files [{filename, path}]

        Returns:
            AgentResponse with message and any additional data
        """
        # Add user message to history
        self.state.add_message("user", user_message)

        # Handle file uploads
        if files:
            await self._handle_file_uploads(files)

        # Process based on current step
        response = await self._process_by_step(user_message)

        # Add assistant response to history
        self.state.add_message("assistant", response.message)

        # Add state info
        response.state = self.state.to_dict()

        return response

    async def _handle_file_uploads(self, files: List[Dict]) -> None:
        """Process uploaded files"""
        for file_info in files:
            filename = file_info.get('filename', '')
            path = file_info.get('path', '')
            file_type = file_info.get('type', 'question')

            # Get file info using tool
            result = await self.tools['get_file_info'].execute({
                'file_path': path,
                'file_type': file_type
            })

            if result.success:
                info = FileInfo(
                    filename=filename,
                    path=path,
                    file_type=file_type,
                    row_count=result.data.get('row_count', 0),
                    columns=result.data.get('columns', []),
                    validated=result.data.get('valid', False),
                    validation_message=', '.join(result.data.get('validation_errors', []))
                )
                self.state.add_file(file_type, info)

                # Auto-detect dimension from reference file
                if file_type == 'reference' and result.data.get('detected_dimension'):
                    self.state.dimension = result.data['detected_dimension']

    async def _process_by_step(self, user_message: str) -> AgentResponse:
        """Process message based on current conversation step"""

        step = self.state.step

        if step == ConversationStep.GREETING:
            return await self._handle_greeting(user_message)

        elif step == ConversationStep.MODE_SELECTION:
            return await self._handle_mode_selection(user_message)

        elif step == ConversationStep.FILE_UPLOAD:
            return await self._handle_file_upload_step(user_message)

        elif step == ConversationStep.FILE_VALIDATION:
            return await self._handle_file_validation(user_message)

        elif step == ConversationStep.DIMENSION_SELECTION:
            return await self._handle_dimension_selection(user_message)

        elif step == ConversationStep.PROCESSING:
            return await self._handle_processing(user_message)

        elif step == ConversationStep.RESULTS:
            return await self._handle_results(user_message)

        elif step == ConversationStep.OPTIONS:
            return await self._handle_options(user_message)

        elif step == ConversationStep.VISUALIZATION:
            return await self._handle_visualization(user_message)

        elif step == ConversationStep.EXPORT:
            return await self._handle_export(user_message)

        elif step == ConversationStep.ENHANCEMENT:
            return await self._handle_enhancement(user_message)

        else:
            # Use LLM for general conversation
            return await self._handle_general(user_message)

    async def _handle_greeting(self, user_message: str) -> AgentResponse:
        """Handle initial greeting"""
        self.state.set_step(ConversationStep.MODE_SELECTION)

        return AgentResponse(
            message=GREETING_MESSAGE,
            options=["Map Questions", "Rate Mappings", "Generate Insights"],
            input_type="choice"
        )

    async def _handle_mode_selection(self, user_message: str) -> AgentResponse:
        """Handle mode selection"""
        msg_lower = user_message.lower()

        if any(w in msg_lower for w in ['map', '1', 'first', 'questions']):
            self.state.mode = 'map'
            mode_info = MODE_DESCRIPTIONS['map']
        elif any(w in msg_lower for w in ['rate', '2', 'second', 'evaluate', 'existing']):
            self.state.mode = 'rate'
            mode_info = MODE_DESCRIPTIONS['rate']
        elif any(w in msg_lower for w in ['insight', '3', 'third', 'chart', 'visual']):
            self.state.mode = 'insights'
            mode_info = MODE_DESCRIPTIONS['insights']
        else:
            return AgentResponse(
                message="I didn't quite catch that. Please choose one of the options:\n\n1. **Map Questions** - Map your exam questions to curriculum\n2. **Rate Mappings** - Evaluate existing mappings\n3. **Generate Insights** - Create visual charts",
                options=["Map Questions", "Rate Mappings", "Generate Insights"],
                input_type="choice"
            )

        self.state.set_step(ConversationStep.FILE_UPLOAD)
        self.state.awaiting_file_upload = True

        files_needed = "\n".join([f"• {f}" for f in mode_info['files_needed']])

        return AgentResponse(
            message=f"**{mode_info['emoji']} {mode_info['name']}**\n\n{mode_info['description']}\n\nPlease upload the following files:\n{files_needed}",
            input_type="file",
            metadata={'files_needed': mode_info['files_needed']}
        )

    async def _handle_file_upload_step(self, user_message: str) -> AgentResponse:
        """Handle file upload step"""
        # Check if we have the required files
        mode = self.state.mode
        has_question = 'question' in self.state.files
        has_reference = 'reference' in self.state.files
        has_mapped = 'mapped' in self.state.files

        if mode == 'map' and has_question and has_reference:
            self.state.awaiting_file_upload = False
            self.state.set_step(ConversationStep.FILE_VALIDATION)
            return await self._handle_file_validation(user_message)

        elif mode == 'rate' and has_mapped and has_reference:
            self.state.awaiting_file_upload = False
            self.state.set_step(ConversationStep.FILE_VALIDATION)
            return await self._handle_file_validation(user_message)

        elif mode == 'insights' and has_mapped:
            self.state.awaiting_file_upload = False
            self.state.set_step(ConversationStep.FILE_VALIDATION)
            return await self._handle_file_validation(user_message)

        # Still waiting for files
        missing = []
        if mode == 'map':
            if not has_question:
                missing.append("Question bank file")
            if not has_reference:
                missing.append("Reference curriculum file")
        elif mode == 'rate':
            if not has_mapped:
                missing.append("Pre-mapped questions file")
            if not has_reference:
                missing.append("Reference curriculum file")
        elif mode == 'insights':
            if not has_mapped:
                missing.append("Mapped questions file")

        return AgentResponse(
            message=f"I still need the following files:\n" + "\n".join([f"• {f}" for f in missing]) + "\n\nPlease upload them to continue.",
            input_type="file"
        )

    async def _handle_file_validation(self, user_message: str) -> AgentResponse:
        """Validate uploaded files and show summary"""
        summaries = []

        for file_type, file_info in self.state.files.items():
            status = "✓" if file_info.validated else "⚠️"
            summaries.append(f"{status} **{file_info.filename}**\n   {file_info.row_count} rows, {len(file_info.columns)} columns")
            if not file_info.validated:
                summaries.append(f"   ⚠️ {file_info.validation_message}")

        summary_text = "\n".join(summaries)

        self.state.set_step(ConversationStep.DIMENSION_SELECTION)

        # Build dimension options
        dim_options = []
        recommended = self.state.dimension or 'nmc_competency'

        for dim_id, dim_info in DIMENSION_DESCRIPTIONS.items():
            rec_marker = " ← Recommended" if dim_id == recommended else ""
            dim_options.append(f"{dim_info['name']} ({dim_info['format']}){rec_marker}")

        return AgentResponse(
            message=f"**Files Received:**\n\n{summary_text}\n\n**Which curriculum dimension should I use?**",
            options=dim_options,
            input_type="choice"
        )

    async def _handle_dimension_selection(self, user_message: str) -> AgentResponse:
        """Handle dimension selection"""
        msg_lower = user_message.lower()

        # Detect dimension from message
        if 'nmc' in msg_lower or 'mi1' in msg_lower or '1' == msg_lower.strip():
            self.state.dimension = 'nmc_competency'
        elif 'topic' in msg_lower or 'area' in msg_lower or '2' == msg_lower.strip():
            self.state.dimension = 'area_topics'
        elif 'competenc' in msg_lower or 'c1' in msg_lower or '3' == msg_lower.strip():
            self.state.dimension = 'competency'
        elif 'objective' in msg_lower or 'o1' in msg_lower or '4' == msg_lower.strip():
            self.state.dimension = 'objective'
        elif 'skill' in msg_lower or 's1' in msg_lower or '5' == msg_lower.strip():
            self.state.dimension = 'skill'
        else:
            # Use default or previously detected
            if not self.state.dimension:
                self.state.dimension = 'nmc_competency'

        self.state.set_step(ConversationStep.PROCESSING)
        return await self._handle_processing(user_message)

    async def _handle_processing(self, user_message: str) -> AgentResponse:
        """Execute the main processing task"""
        mode = self.state.mode
        dimension = self.state.dimension

        dim_name = DIMENSION_DESCRIPTIONS.get(dimension, {}).get('name', dimension)

        if mode == 'map':
            # Run mapping
            question_file = self.state.files['question'].path
            reference_file = self.state.files['reference'].path

            result = await self.tools['map_questions'].execute({
                'question_file': question_file,
                'reference_file': reference_file,
                'dimension': dimension,
                'batch_size': 5
            })

            if not result.success:
                return AgentResponse(
                    message=f"❌ {result.error}\n\nWould you like to try again?",
                    options=["Try Again", "Change Files", "Start Over"]
                )

            # Store results
            self.state.results = result.data
            self.state.recommendations = result.data.get('recommendations', [])

            # Auto-select high confidence
            self.state.selected_indices = [
                i for i, r in enumerate(self.state.recommendations)
                if r.get('confidence', 0) >= 0.85
            ]

            self.state.set_step(ConversationStep.RESULTS)
            return await self._format_mapping_results(result)

        elif mode == 'rate':
            # Run rating
            mapped_file = self.state.files['mapped'].path
            reference_file = self.state.files['reference'].path

            result = await self.tools['rate_mappings'].execute({
                'mapped_file': mapped_file,
                'reference_file': reference_file,
                'dimension': dimension,
                'batch_size': 5
            })

            if not result.success:
                return AgentResponse(
                    message=f"❌ {result.error}\n\nWould you like to try again?",
                    options=["Try Again", "Change Files", "Start Over"]
                )

            self.state.results = result.data
            self.state.recommendations = result.data.get('recommendations', [])
            self.state.set_step(ConversationStep.RESULTS)

            return await self._format_rating_results(result)

        elif mode == 'insights':
            # Generate insights
            mapped_file = self.state.files['mapped'].path
            reference_file = self.state.files.get('reference', {})
            ref_path = reference_file.path if hasattr(reference_file, 'path') else None

            result = await self.tools['generate_insights'].execute({
                'mapped_file': mapped_file,
                'reference_file': ref_path
            })

            if not result.success:
                return AgentResponse(
                    message=f"❌ {result.error}",
                    options=["Try Again", "Start Over"]
                )

            self.state.charts = result.data.get('charts', {})
            self.state.set_step(ConversationStep.OPTIONS)

            return await self._format_insights_results(result)

        return AgentResponse(message="Processing...")

    async def _format_mapping_results(self, result) -> AgentResponse:
        """Format mapping results into a nice message"""
        meta = result.metadata
        coverage = self.state.results.get('coverage', {})
        gaps = self.state.results.get('gaps', [])

        # Coverage table
        coverage_lines = []
        for topic, count in sorted(coverage.items(), key=lambda x: -x[1])[:10]:
            coverage_lines.append(f"| {topic} | {count} |")

        coverage_table = "| Topic | Questions |\n|-------|----------|\n" + "\n".join(coverage_lines)
        if len(coverage) > 10:
            coverage_table += f"\n| ... | ({len(coverage) - 10} more) |"

        # Gaps
        gaps_text = ", ".join(gaps[:5]) if gaps else "None found"
        if len(gaps) > 5:
            gaps_text += f" (+{len(gaps) - 5} more)"

        message = f"""✅ **Mapping Complete!**

**Summary:**
| Metric | Value |
|--------|-------|
| Total Questions | {meta['total_questions']} |
| Mapped | {meta['mapped_questions']} |
| Average Confidence | {meta['average_confidence']:.0%} |
| High Confidence (≥85%) | {meta['high_confidence_count']} |
| Medium (70-85%) | {meta['medium_confidence_count']} |
| Low (<70%) | {meta['low_confidence_count']} |

**Coverage by {DIMENSION_DESCRIPTIONS.get(self.state.dimension, {}).get('name', 'Topic')}:**
{coverage_table}

**Gaps (no questions):** {gaps_text}

{OPTIONS_AFTER_MAPPING}"""

        self.state.set_step(ConversationStep.OPTIONS)

        return AgentResponse(
            message=message,
            options=["Generate Charts", "Review Mappings", "Export to Excel", "Save to Library", "Start Over"],
            metadata=meta
        )

    async def _format_rating_results(self, result) -> AgentResponse:
        """Format rating results"""
        meta = result.metadata
        summary = self.state.results.get('summary', {})

        message = f"""✅ **Rating Complete!**

**Summary:**
| Rating | Count |
|--------|-------|
| ✓ Correct | {summary.get('correct', 0)} |
| ~ Partially Correct | {summary.get('partially_correct', 0)} |
| ✗ Incorrect | {summary.get('incorrect', 0)} |

**Accuracy Rate:** {summary.get('accuracy_rate', 0):.0%}
**Average Agreement:** {summary.get('average_agreement_score', 0):.0%}
**Need Correction:** {meta.get('needs_correction', 0)}

{OPTIONS_AFTER_RATING}"""

        self.state.set_step(ConversationStep.OPTIONS)

        return AgentResponse(
            message=message,
            options=["Generate Charts", "Review Ratings", "Apply Corrections", "Export to Excel", "Save to Library"],
            metadata=meta
        )

    async def _format_insights_results(self, result) -> AgentResponse:
        """Format insights results"""
        charts = result.data.get('charts', {})
        summary = result.data.get('summary', {})

        chart_list = "\n".join([f"• {name.replace('_', ' ').title()}" for name in charts.keys()])

        message = f"""✅ **Charts Generated!**

**Available Charts:**
{chart_list}

**Summary:**
| Metric | Value |
|--------|-------|
| Total Questions | {summary.get('total_questions', 0)} |
| Topics Covered | {summary.get('topics_covered', 0)} |
| Avg Confidence | {summary.get('average_confidence', 0):.0%} |

Would you like to:
1. **Download Charts** - Get all charts as images
2. **Export to Excel** - Include charts in spreadsheet
3. **Start Over** - Begin a new session"""

        return AgentResponse(
            message=message,
            charts=charts,
            options=["Download Charts", "Export to Excel", "Start Over"]
        )

    async def _handle_results(self, user_message: str) -> AgentResponse:
        """Handle results display - redirect to options"""
        self.state.set_step(ConversationStep.OPTIONS)
        return await self._handle_options(user_message)

    async def _handle_options(self, user_message: str) -> AgentResponse:
        """Handle post-processing options"""
        msg_lower = user_message.lower()

        if any(w in msg_lower for w in ['chart', 'visual', 'graph', '1']):
            return await self._handle_visualization(user_message)

        elif any(w in msg_lower for w in ['review', 'detail', 'see', '2']):
            return await self._format_detailed_review()

        elif any(w in msg_lower for w in ['export', 'excel', 'download', '3', '4']):
            return await self._handle_export(user_message)

        elif any(w in msg_lower for w in ['save', 'library', '5']):
            return await self._handle_save_to_library(user_message)

        elif any(w in msg_lower for w in ['start over', 'reset', 'new', '6']):
            self.state.reset()
            return await self._handle_greeting("")

        elif any(w in msg_lower for w in ['done', 'finish', 'exit', 'bye']):
            return AgentResponse(
                message="Thank you for using the Curriculum Mapping Assistant! Your work has been saved. Feel free to come back anytime. 👋",
                requires_input=False
            )

        else:
            # Let LLM handle
            return await self._handle_general(user_message)

    async def _handle_visualization(self, user_message: str) -> AgentResponse:
        """Generate and return visualizations"""
        if self.state.charts:
            return AgentResponse(
                message="Here are your charts:",
                charts=self.state.charts,
                options=["Export to Excel", "Save to Library", "Start Over"]
            )

        # Need to generate charts
        if self.state.mode == 'insights':
            mapped_file = self.state.files.get('mapped', {})
            file_path = mapped_file.path if hasattr(mapped_file, 'path') else None
        else:
            # Export current results first, then generate insights
            # For now, use the question file with applied mappings
            file_path = self.state.files.get('question', self.state.files.get('mapped', {}))
            file_path = file_path.path if hasattr(file_path, 'path') else None

        if not file_path:
            return AgentResponse(
                message="I need mapping data to generate charts. Let's run a mapping first.",
                options=["Start Mapping", "Start Over"]
            )

        result = await self.tools['generate_insights'].execute({
            'mapped_file': file_path
        })

        if result.success:
            self.state.charts = result.data.get('charts', {})
            return AgentResponse(
                message="✅ Charts generated!",
                charts=self.state.charts,
                options=["Export to Excel", "Save to Library", "Start Over"]
            )
        else:
            return AgentResponse(
                message=f"❌ Failed to generate charts: {result.error}",
                options=["Try Again", "Start Over"]
            )

    async def _handle_export(self, user_message: str) -> AgentResponse:
        """Export results to Excel"""
        if not self.state.recommendations:
            return AgentResponse(
                message="No results to export. Please run a mapping first.",
                options=["Start Mapping", "Start Over"]
            )

        question_file = self.state.files.get('question', self.state.files.get('mapped', {}))
        file_path = question_file.path if hasattr(question_file, 'path') else None

        if not file_path:
            return AgentResponse(
                message="Source file not found. Please try again.",
                options=["Start Over"]
            )

        # If no selection, use all
        selected = self.state.selected_indices or list(range(len(self.state.recommendations)))

        result = await self.tools['export_results'].execute({
            'question_file': file_path,
            'recommendations': self.state.recommendations,
            'selected_indices': selected,
            'dimension': self.state.dimension
        })

        if result.success:
            self.state.export_file = result.data.get('filename')
            return AgentResponse(
                message=f"✅ **Export Ready!**\n\n📁 **{result.data.get('filename')}**\n\nExported {result.metadata.get('total_exported', 0)} mappings.",
                download_url=result.data.get('download_url'),
                options=["Save to Library", "Generate Charts", "Start Over"]
            )
        else:
            return AgentResponse(
                message=f"❌ Export failed: {result.error}",
                options=["Try Again", "Start Over"]
            )

    async def _handle_save_to_library(self, user_message: str) -> AgentResponse:
        """Save to library"""
        if not self.state.recommendations:
            return AgentResponse(
                message="No results to save. Please run a mapping first.",
                options=["Start Mapping", "Start Over"]
            )

        # Extract name from message or generate default
        name = user_message.strip()
        if len(name) < 3 or any(w in name.lower() for w in ['save', 'library', 'yes']):
            from datetime import datetime
            name = f"Mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        source_file = self.state.files.get('question', self.state.files.get('mapped', {}))
        source_name = source_file.filename if hasattr(source_file, 'filename') else ''

        result = await self.tools['save_to_library'].execute({
            'name': name,
            'recommendations': self.state.recommendations,
            'dimension': self.state.dimension,
            'mode': self.state.mode.upper() if self.state.mode else 'A',
            'source_file': source_name
        })

        if result.success:
            self.state.library_id = result.data.get('id')
            return AgentResponse(
                message=f"✅ **Saved to Library!**\n\n📚 **{result.data.get('name')}**\nID: `{result.data.get('id')}`\n\nYou can load this anytime from your library.",
                options=["Export to Excel", "Generate Charts", "Start Over", "Done"]
            )
        else:
            return AgentResponse(
                message=f"❌ Save failed: {result.error}",
                options=["Try Again", "Start Over"]
            )

    async def _format_detailed_review(self) -> AgentResponse:
        """Show detailed review of mappings"""
        if not self.state.recommendations:
            return AgentResponse(
                message="No mappings to review.",
                options=["Start Mapping", "Start Over"]
            )

        # Show first 10
        recs = self.state.recommendations[:10]
        lines = []

        for i, rec in enumerate(recs):
            conf = rec.get('confidence', 0)
            conf_emoji = "🟢" if conf >= 0.85 else "🟡" if conf >= 0.7 else "🔴"
            q_text = rec.get('question_text', '')[:100]
            if len(rec.get('question_text', '')) > 100:
                q_text += "..."

            lines.append(f"""**{rec.get('question_num', f'Q{i+1}')}** {conf_emoji} {conf:.0%}
> {q_text}
→ **{rec.get('recommended_mapping', 'N/A')}**
""")

        remaining = len(self.state.recommendations) - 10
        if remaining > 0:
            lines.append(f"\n*...and {remaining} more mappings*")

        message = "**Detailed Mappings:**\n\n" + "\n".join(lines)

        return AgentResponse(
            message=message,
            options=["Export All", "Generate Charts", "Save to Library", "Start Over"]
        )

    async def _handle_enhancement(self, user_message: str) -> AgentResponse:
        """Handle enhancement/refinement requests"""
        return await self._handle_options(user_message)

    async def _handle_general(self, user_message: str) -> AgentResponse:
        """Handle general conversation using LLM"""
        # Build context
        context = SYSTEM_PROMPT.format(
            tool_descriptions=TOOL_DESCRIPTIONS,
            conversation_state=self.state.get_context_summary()
        )

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": context},
                    *self.state.get_messages_for_api(),
                    {"role": "user", "content": user_message}
                ],
                temperature=self.config.temperature,
                max_tokens=1000
            )

            message = response.choices[0].message.content

            return AgentResponse(
                message=message,
                options=self.state.current_options if self.state.current_options else None
            )

        except Exception as e:
            return AgentResponse(
                message=f"I encountered an issue: {str(e)}\n\nLet's try something else.",
                options=["Start Over", "Help"]
            )

    def reset(self) -> None:
        """Reset the agent state"""
        self.state.reset()
        self.state.session_id = str(uuid.uuid4())[:8]
