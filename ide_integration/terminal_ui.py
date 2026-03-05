#!/usr/bin/env python3
"""
Mrki Terminal UI - Rich terminal interface components
"""

import asyncio
import json
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any, Tuple
from enum import Enum

from rich.align import Align
from rich.box import DOUBLE, ROUNDED, HEAVY
from rich.console import Console, RenderableType
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

# Try to import textual for TUI mode
try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical
    from textual.reactive import reactive
    from textual.widgets import (
        Button, DataTable, Footer, Header, Input, Label, 
        ListView, ListItem, Static, TabbedContent, Tabs, TextLog, Tree as TextualTree
    )
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False


@dataclass
class Message:
    """Chat message"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class CompletionItem:
    """Code completion item"""
    text: str
    confidence: float
    language: str
    source: str = 'mrki'


class Theme:
    """Color theme for terminal UI"""
    PRIMARY = "bright_cyan"
    SECONDARY = "bright_blue"
    SUCCESS = "bright_green"
    WARNING = "bright_yellow"
    ERROR = "bright_red"
    INFO = "bright_white"
    MUTED = "dim"
    BORDER = "blue"
    
    HEADER = f"[{PRIMARY}]"
    SUCCESS_TAG = f"[{SUCCESS}]"
    ERROR_TAG = f"[{ERROR}]"
    WARNING_TAG = f"[{WARNING}]"


class MrkiTerminalUI:
    """Rich terminal UI for Mrki"""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.theme = Theme()
        self.messages: List[Message] = []
        self.running = False
        
    def print_header(self, title: str):
        """Print a styled header"""
        self.console.print()
        self.console.print(Panel(
            Align.center(Text(title, style=f"bold {self.theme.PRIMARY}")),
            box=DOUBLE,
            border_style=self.theme.PRIMARY
        ))
        self.console.print()
    
    def print_success(self, message: str):
        """Print success message"""
        self.console.print(f"{self.theme.SUCCESS_TAG}✓[/] {message}")
    
    def print_error(self, message: str):
        """Print error message"""
        self.console.print(f"{self.theme.ERROR_TAG}✗[/] {message}")
    
    def print_warning(self, message: str):
        """Print warning message"""
        self.console.print(f"{self.theme.WARNING_TAG}⚠[/] {message}")
    
    def print_info(self, message: str):
        """Print info message"""
        self.console.print(f"{self.theme.INFO_TAG}ℹ[/] {message}")
    
    def show_code(self, code: str, language: str = "python", title: Optional[str] = None):
        """Display code with syntax highlighting"""
        syntax = Syntax(
            code, 
            language, 
            theme="monokai",
            line_numbers=True,
            word_wrap=True
        )
        
        panel = Panel(
            syntax,
            title=title or f"{language.upper()} Code",
            border_style=self.theme.SECONDARY,
            box=ROUNDED
        )
        self.console.print(panel)
    
    def show_diff(self, original: str, modified: str, language: str = "python"):
        """Show diff between two code blocks"""
        from difflib import unified_diff
        
        diff = list(unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile='original',
            tofile='modified'
        ))
        
        if diff:
            diff_text = ''.join(diff)
            syntax = Syntax(diff_text, "diff", theme="monokai")
            self.console.print(Panel(
                syntax,
                title="Changes",
                border_style=self.theme.WARNING
            ))
        else:
            self.console.print("[dim]No changes[/dim]")
    
    def show_completions(self, completions: List[CompletionItem]):
        """Display code completions"""
        table = Table(title="Code Completions", show_header=True)
        table.add_column("#", style="dim", width=3)
        table.add_column("Completion", style=self.theme.PRIMARY)
        table.add_column("Confidence", width=12)
        table.add_column("Source", style="dim")
        
        for i, comp in enumerate(completions[:10], 1):
            conf_color = (
                self.theme.SUCCESS if comp.confidence > 0.8 
                else self.theme.WARNING if comp.confidence > 0.5 
                else self.theme.ERROR
            )
            
            # Truncate long completions
            text = comp.text[:50] + "..." if len(comp.text) > 50 else comp.text
            
            table.add_row(
                str(i),
                text,
                f"[{conf_color}]{comp.confidence:.0%}[/]",
                comp.source
            )
        
        self.console.print(table)
    
    def show_file_tree(self, path: str = ".", max_depth: int = 3):
        """Display file tree"""
        root = Path(path)
        if not root.exists():
            self.print_error(f"Path not found: {path}")
            return
        
        tree = Tree(f"[bold]{root.name}[/]")
        self._build_tree(root, tree, 0, max_depth)
        
        self.console.print(Panel(
            tree,
            title="Project Structure",
            border_style=self.theme.SECONDARY
        ))
    
    def _build_tree(self, path: Path, tree: Tree, depth: int, max_depth: int):
        """Recursively build file tree"""
        if depth >= max_depth:
            return
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
            for item in items[:20]:  # Limit items per level
                if item.name.startswith('.') and item.name not in ['.mrki', '.gitignore']:
                    continue
                
                if item.is_dir():
                    branch = tree.add(f"[bold blue]{item.name}/[/]")
                    self._build_tree(item, branch, depth + 1, max_depth)
                else:
                    icon = self._get_file_icon(item.suffix)
                    tree.add(f"{icon} {item.name}")
        except PermissionError:
            pass
    
    def _get_file_icon(self, suffix: str) -> str:
        """Get icon for file type"""
        icons = {
            '.py': '🐍',
            '.js': '📜',
            '.ts': '🔷',
            '.rs': '🦀',
            '.go': '🐹',
            '.java': '☕',
            '.cpp': '⚙️',
            '.c': '⚙️',
            '.h': '📋',
            '.md': '📝',
            '.json': '📋',
            '.yml': '⚙️',
            '.yaml': '⚙️',
            '.toml': '⚙️',
            '.txt': '📄',
        }
        return icons.get(suffix, '📄')
    
    def show_progress(self, description: str) -> Progress:
        """Create and return a progress bar"""
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        )
        return progress
    
    def start_chat(self):
        """Start interactive chat session"""
        self.print_header("Mrki Chat")
        self.console.print("[dim]Type 'exit' or 'quit' to end the session[/dim]\n")
        
        # Welcome message
        self._print_message(Message(
            role='assistant',
            content='Hello! I\'m Mrki, your AI coding assistant. How can I help you today?'
        ))
        
        self.running = True
        while self.running:
            try:
                user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    self.running = False
                    break
                
                # Add user message
                user_msg = Message(role='user', content=user_input)
                self.messages.append(user_msg)
                self._print_message(user_msg)
                
                # Get AI response
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console
                ) as progress:
                    progress.add_task("Mrki is thinking...", total=None)
                    response = self._get_ai_response(user_input)
                
                # Add and print AI message
                ai_msg = Message(role='assistant', content=response)
                self.messages.append(ai_msg)
                self._print_message(ai_msg)
                
            except KeyboardInterrupt:
                self.running = False
                break
        
        self.console.print("\n[dim]Chat ended. Goodbye![/dim]")
    
    def _print_message(self, message: Message):
        """Print a chat message"""
        if message.role == 'user':
            self.console.print(f"\n[bold cyan]You:[/bold cyan] {message.content}")
        elif message.role == 'assistant':
            # Format AI response with code blocks
            content = self._format_ai_response(message.content)
            self.console.print(f"\n[bold green]Mrki:[/bold green] {content}")
        else:
            self.console.print(f"\n[dim]{message.content}[/dim]")
    
    def _format_ai_response(self, content: str) -> str:
        """Format AI response with proper styling"""
        import re
        
        # Format code blocks
        def format_code_block(match):
            lang = match.group(1) or 'text'
            code = match.group(2)
            return f"\n[dim]```{lang}[/dim]\n{code}\n[dim]```[/dim]"
        
        content = re.sub(r'```(\w+)?\n(.*?)```', format_code_block, content, flags=re.DOTALL)
        
        # Format inline code
        content = re.sub(r'`([^`]+)`', r'[yellow]\1[/]', content)
        
        return content
    
    def _get_ai_response(self, message: str) -> str:
        """Get AI response - in real implementation, this would call the API"""
        # Placeholder responses for demo
        responses = [
            "I can help you with that! Here's an example:\n\n```python\ndef example():\n    return 'Hello, World!'\n```",
            "That's a great question. Let me explain:\n\nThe code you're looking at uses a common pattern for handling async operations. The `async` keyword defines a coroutine function, and `await` is used to wait for the result.",
            "I can generate tests for that function. Would you like me to proceed?",
            "Here's a refactored version that might be cleaner:\n\n```python\n# Refactored code\nresult = [x for x in items if x.is_valid()]\n```",
        ]
        import random
        time.sleep(1)  # Simulate API call
        return random.choice(responses)
    
    def show_dashboard(self):
        """Show interactive dashboard"""
        if TEXTUAL_AVAILABLE:
            app = MrkiDashboardApp()
            app.run()
        else:
            self._show_simple_dashboard()
    
    def _show_simple_dashboard(self):
        """Show simple dashboard without textual"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="sidebar", size=30),
            Layout(name="content")
        )
        
        # Header
        layout["header"].update(Panel(
            Align.center("[bold]Mrki Dashboard[/bold]"),
            style=self.theme.PRIMARY
        ))
        
        # Sidebar
        sidebar = Table(show_header=False, box=None)
        sidebar.add_column(style=self.theme.PRIMARY)
        sidebar.add_row("📊 Status")
        sidebar.add_row("💬 Chat")
        sidebar.add_row("📝 Completions")
        sidebar.add_row("⚙️ Settings")
        layout["sidebar"].update(Panel(sidebar, title="Menu"))
        
        # Content
        content = Table(title="Recent Activity")
        content.add_column("Time", style="dim")
        content.add_column("Action")
        content.add_column("Status")
        content.add_row("10:30", "Code completion", "[green]Success[/]")
        content.add_row("10:25", "Chat message", "[green]Success[/]")
        content.add_row("10:20", "File analysis", "[green]Success[/]")
        layout["content"].update(content)
        
        # Footer
        layout["footer"].update(Panel(
            "[dim]Press Ctrl+C to exit[/dim]",
            style=self.theme.MUTED
        ))
        
        with Live(layout, screen=True, console=self.console) as live:
            try:
                while True:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                pass


if TEXTUAL_AVAILABLE:
    class MrkiDashboardApp(App):
        """Textual-based dashboard app"""
        
        CSS = """
        Screen { align: center middle; }
        
        #sidebar {
            width: 25;
            background: $surface-darken-1;
            border-right: solid $primary;
        }
        
        #content {
            background: $surface;
        }
        
        .menu-item {
            padding: 1;
            text-align: center;
        }
        
        .menu-item:hover {
            background: $primary-darken-2;
        }
        """
        
        BINDINGS = [
            ("q", "quit", "Quit"),
            ("c", "chat", "Chat"),
            ("s", "status", "Status"),
        ]
        
        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            
            with Horizontal():
                with Vertical(id="sidebar"):
                    yield Button("📊 Status", id="btn-status")
                    yield Button("💬 Chat", id="btn-chat")
                    yield Button("📝 Completions", id="btn-completions")
                    yield Button("⚙️ Settings", id="btn-settings")
                
                with Vertical(id="content"):
                    yield Static("Welcome to Mrki Dashboard", id="main-content")
            
            yield Footer()
        
        def on_button_pressed(self, event: Button.Pressed) -> None:
            """Handle button presses"""
            button_id = event.button.id
            content = self.query_one("#main-content", Static)
            
            if button_id == "btn-status":
                content.update("Status: All systems operational\n\nServer: Running\nLSP: Connected\nModels: Loaded")
            elif button_id == "btn-chat":
                content.update("Chat interface would appear here...")
            elif button_id == "btn-completions":
                content.update("Recent completions:\n\n1. def process_data(data):\n2. async def fetch():\n3. class DataHandler:")
            elif button_id == "btn-settings":
                content.update("Settings:\n\nTheme: Dark\nAuto-complete: On\nInline hints: On")
        
        def action_chat(self):
            """Open chat"""
            self.on_button_pressed(type('Event', (), {'button': type('Btn', (), {'id': 'btn-chat'})})())
        
        def action_status(self):
            """Show status"""
            self.on_button_pressed(type('Event', (), {'button': type('Btn', (), {'id': 'btn-status'})})())


def demo():
    """Demo the terminal UI"""
    ui = MrkiTerminalUI()
    
    ui.print_header("Mrki Terminal UI Demo")
    
    ui.print_success("Successfully connected to Mrki server")
    ui.print_info("Server version: 1.0.0")
    ui.print_warning("Low memory mode enabled")
    
    ui.console.print()
    ui.show_code("""
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Example usage
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")
""", language="python", title="Example Code")
    
    ui.console.print()
    
    completions = [
        CompletionItem("def process_data(data):\n    result = []", 0.95, "python"),
        CompletionItem("async def fetch_data(url):", 0.87, "python"),
        CompletionItem("class DataProcessor:", 0.72, "python"),
        CompletionItem("for item in items:", 0.65, "python"),
    ]
    ui.show_completions(completions)
    
    ui.console.print()
    ui.show_file_tree(".", max_depth=2)


if __name__ == "__main__":
    demo()
