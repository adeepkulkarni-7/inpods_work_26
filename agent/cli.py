"""
CLI Interface for the AI Agent

A terminal-based interface for the curriculum mapping agent.
"""

import os
import sys
import asyncio
from typing import Optional

# Try to import rich for better formatting
try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Note: Install 'rich' for better formatting: pip install rich")

from .config import get_agent_config
from .orchestrator import AgentOrchestrator


class CLIAgent:
    """Command-line interface for the AI Agent"""

    def __init__(self):
        self.config = get_agent_config()
        self.agent = None

        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None

    def print(self, text: str, style: str = None):
        """Print text with optional styling"""
        if self.console:
            self.console.print(text, style=style)
        else:
            print(text)

    def print_markdown(self, text: str):
        """Print markdown formatted text"""
        if self.console:
            self.console.print(Markdown(text))
        else:
            print(text)

    def print_panel(self, text: str, title: str = None, style: str = "green"):
        """Print text in a panel"""
        if self.console:
            self.console.print(Panel(text, title=title, border_style=style))
        else:
            if title:
                print(f"\n=== {title} ===")
            print(text)
            print("=" * 40)

    def get_input(self, prompt: str = "> ") -> str:
        """Get user input"""
        if RICH_AVAILABLE:
            return Prompt.ask(prompt)
        else:
            return input(prompt)

    def show_options(self, options: list) -> Optional[str]:
        """Display options and get selection"""
        if not options:
            return None

        self.print("\nOptions:", style="bold cyan")
        for i, opt in enumerate(options, 1):
            self.print(f"  [{i}] {opt}")

        choice = self.get_input("\nSelect an option (number or text)")

        # Handle numeric selection
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass

        return choice

    def upload_files(self, file_types: list = None) -> list:
        """Handle file upload"""
        self.print("\n📁 File Upload", style="bold cyan")

        if file_types:
            self.print(f"   Needed: {', '.join(file_types)}")

        files = []

        while True:
            path = self.get_input("Enter file path (or 'done' to continue)")

            if path.lower() in ['done', 'd', '']:
                if files:
                    break
                else:
                    self.print("Please upload at least one file.", style="yellow")
                    continue

            # Expand user path
            path = os.path.expanduser(path)

            if not os.path.exists(path):
                self.print(f"File not found: {path}", style="red")
                continue

            # Determine file type
            filename = os.path.basename(path)
            file_type = 'question'

            if any(w in filename.lower() for w in ['curriculum', 'reference', 'nmc']):
                file_type = 'reference'
            elif any(w in filename.lower() for w in ['mapped', 'output', 'audit']):
                file_type = 'mapped'

            # Copy to uploads folder
            import shutil
            dest = os.path.join(self.config.upload_folder, filename)
            shutil.copy(path, dest)

            files.append({
                'filename': filename,
                'path': dest,
                'type': file_type
            })

            self.print(f"✓ Added: {filename} ({file_type})", style="green")

        return files

    async def run(self):
        """Run the CLI agent"""
        # Show header
        self.print_panel(
            "🎓 Curriculum Mapping AI Assistant\n\n"
            "I'll help you map exam questions to curriculum competencies.\n"
            "Type 'quit' to exit, 'reset' to start over.",
            title="Welcome",
            style="cyan"
        )

        # Validate config
        is_valid, errors = self.config.validate()
        if not is_valid:
            self.print(f"Configuration Error: {', '.join(errors)}", style="red")
            self.print("\nPlease check your .env file and ensure Azure OpenAI credentials are set.")
            return

        # Initialize agent
        self.print("\n⏳ Initializing agent...", style="dim")

        try:
            self.agent = AgentOrchestrator(self.config)
            self.print("✓ Agent ready!\n", style="green")
        except Exception as e:
            self.print(f"Failed to initialize agent: {e}", style="red")
            return

        # Get initial greeting
        response = await self.agent.process_message("")
        self.print_markdown(response.message)

        if response.options:
            self.show_options(response.options)

        # Main loop
        while True:
            try:
                # Get user input
                user_input = self.get_input("\n💬 You")

                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    self.print("\nGoodbye! 👋", style="cyan")
                    break

                if user_input.lower() in ['reset', 'restart']:
                    self.agent.reset()
                    response = await self.agent.process_message("")
                    self.print_markdown(response.message)
                    continue

                if user_input.lower() == 'help':
                    self.print_panel(
                        "Commands:\n"
                        "  quit    - Exit the program\n"
                        "  reset   - Start a new session\n"
                        "  help    - Show this help\n"
                        "  upload  - Upload files manually\n\n"
                        "You can also just type naturally!",
                        title="Help"
                    )
                    continue

                # Check if we need file upload
                files = []
                if response.input_type == 'file' or user_input.lower() == 'upload':
                    files = self.upload_files()

                # Process message
                if RICH_AVAILABLE:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=self.console
                    ) as progress:
                        task = progress.add_task("Thinking...", total=None)
                        response = await self.agent.process_message(user_input, files)
                else:
                    print("Processing...")
                    response = await self.agent.process_message(user_input, files)

                # Display response
                self.print("\n🤖 Assistant:", style="bold cyan")
                self.print_markdown(response.message)

                # Show charts info
                if response.charts:
                    self.print("\n📊 Charts generated:", style="bold")
                    for name, path in response.charts.items():
                        self.print(f"   • {name}: {path}")

                # Show download link
                if response.download_url:
                    self.print(f"\n📥 Download: {response.download_url}", style="green")

                # Show options
                if response.options:
                    selected = self.show_options(response.options)
                    if selected:
                        # Auto-send the selected option
                        user_input = selected
                        response = await self.agent.process_message(user_input)
                        self.print("\n🤖 Assistant:", style="bold cyan")
                        self.print_markdown(response.message)

            except KeyboardInterrupt:
                self.print("\n\nInterrupted. Type 'quit' to exit.", style="yellow")
            except Exception as e:
                self.print(f"\nError: {e}", style="red")


def main():
    """Entry point for CLI"""
    cli = CLIAgent()
    asyncio.run(cli.run())


if __name__ == '__main__':
    main()
