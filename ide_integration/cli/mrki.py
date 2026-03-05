#!/usr/bin/env python3
"""
Mrki CLI - Command Line Interface for Mrki AI Development Assistant
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from terminal_ui import MrkiTerminalUI
from file_watcher import FileWatcher

console = Console()


class MrkiCLI:
    """Main CLI application for Mrki"""
    
    def __init__(self):
        self.config = self._load_config()
        self.terminal_ui = MrkiTerminalUI()
        self.file_watcher: Optional[FileWatcher] = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config file"""
        config_path = Path.home() / '.mrki' / 'config.json'
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            'server': {
                'host': 'localhost',
                'port': 8765
            },
            'completion': {
                'enabled': True,
                'inline': True
            },
            'ui': {
                'theme': 'dark',
                'animations': True
            }
        }
    
    def _save_config(self):
        """Save configuration to file"""
        config_path = Path.home() / '.mrki'
        config_path.mkdir(parents=True, exist_ok=True)
        with open(config_path / 'config.json', 'w') as f:
            json.dump(self.config, f, indent=2)


class Commands:
    """CLI commands implementation"""
    
    def __init__(self, cli: MrkiCLI):
        self.cli = cli
        self.console = Console()
    
    def status(self):
        """Show Mrki status"""
        table = Table(title="Mrki Status", show_header=True)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="dim")
        
        # Check server status
        try:
            import urllib.request
            req = urllib.request.Request(
                f"http://{self.cli.config['server']['host']}:{self.cli.config['server']['port']}/health"
            )
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status == 200:
                    table.add_row("Server", "[green]Running[/green]", 
                                f"{self.cli.config['server']['host']}:{self.cli.config['server']['port']}")
                else:
                    table.add_row("Server", "[yellow]Warning[/yellow]", f"Status: {response.status}")
        except Exception as e:
            table.add_row("Server", "[red]Stopped[/red]", str(e))
        
        # Config status
        table.add_row("Completion", 
                     "[green]Enabled[/green]" if self.cli.config['completion']['enabled'] else "[red]Disabled[/red]",
                     "Inline: " + ("Yes" if self.cli.config['completion']['inline'] else "No"))
        
        table.add_row("Config", "[green]Loaded[/green]", str(Path.home() / '.mrki' / 'config.json'))
        
        self.console.print(table)
    
    def complete(self, file: Optional[str] = None, line: Optional[int] = None, 
                 column: Optional[int] = None):
        """Get code completions"""
        if file:
            path = Path(file)
            if not path.exists():
                self.console.print(f"[red]File not found: {file}[/red]")
                return
            
            content = path.read_text()
            language = path.suffix.lstrip('.')
        else:
            # Read from stdin
            self.console.print("[dim]Enter code (Ctrl+D when done):[/dim]")
            content = sys.stdin.read()
            language = "python"
        
        # Get completions from server
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Getting completions...", total=None)
            
            try:
                import urllib.request
                req = urllib.request.Request(
                    f"http://{self.cli.config['server']['host']}:{self.cli.config['server']['port']}/complete",
                    data=json.dumps({
                        'text': content,
                        'position': {'line': line or 0, 'character': column or 0},
                        'language': language
                    }).encode(),
                    headers={'Content-Type': 'application/json'}
                )
                
                with urllib.request.urlopen(req, timeout=30) as response:
                    data = json.loads(response.read())
                    progress.update(task, completed=True)
                    
                    if data.get('items'):
                        self.console.print("\n[bold green]Completions:[/bold green]")
                        for i, item in enumerate(data['items'][:5], 1):
                            confidence = item.get('confidence', 0)
                            color = 'green' if confidence > 0.8 else 'yellow' if confidence > 0.5 else 'red'
                            self.console.print(f"{i}. [{color}]{item['insertText'][:50]}...[/] (confidence: {confidence:.2f})")
                    else:
                        self.console.print("[yellow]No completions available[/yellow]")
                        
            except Exception as e:
                progress.update(task, completed=True)
                self.console.print(f"[red]Error: {e}[/red]")
    
    def chat(self, message: Optional[str] = None):
        """Start interactive chat with Mrki"""
        self.cli.terminal_ui.start_chat()
    
    def explain(self, file: Optional[str] = None):
        """Explain code"""
        if file:
            path = Path(file)
            if path.exists():
                code = path.read_text()
            else:
                self.console.print(f"[red]File not found: {file}[/red]")
                return
        else:
            self.console.print("[dim]Enter code to explain (Ctrl+D when done):[/dim]")
            code = sys.stdin.read()
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            progress.add_task("Analyzing code...", total=None)
            
            try:
                import urllib.request
                req = urllib.request.Request(
                    f"http://{self.cli.config['server']['host']}:{self.cli.config['server']['port']}/explain",
                    data=json.dumps({'code': code}).encode(),
                    headers={'Content-Type': 'application/json'}
                )
                
                with urllib.request.urlopen(req, timeout=30) as response:
                    data = json.loads(response.read())
                    explanation = data.get('explanation', 'No explanation available')
                    
                    self.console.print(Panel(
                        explanation,
                        title="Code Explanation",
                        border_style="blue"
                    ))
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
    
    def test(self, file: str, output: Optional[str] = None):
        """Generate tests for code"""
        path = Path(file)
        if not path.exists():
            self.console.print(f"[red]File not found: {file}[/red]")
            return
        
        code = path.read_text()
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            progress.add_task("Generating tests...", total=None)
            
            try:
                import urllib.request
                req = urllib.request.Request(
                    f"http://{self.cli.config['server']['host']}:{self.cli.config['server']['port']}/generate-tests",
                    data=json.dumps({'code': code, 'language': path.suffix.lstrip('.')}).encode(),
                    headers={'Content-Type': 'application/json'}
                )
                
                with urllib.request.urlopen(req, timeout=30) as response:
                    data = json.loads(response.read())
                    tests = data.get('tests', '')
                    
                    if output:
                        Path(output).write_text(tests)
                        self.console.print(f"[green]Tests written to: {output}[/green]")
                    else:
                        syntax = Syntax(tests, path.suffix.lstrip('.'), theme="monokai")
                        self.console.print(Panel(syntax, title="Generated Tests", border_style="green"))
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
    
    def refactor(self, file: str, instruction: str):
        """Refactor code"""
        path = Path(file)
        if not path.exists():
            self.console.print(f"[red]File not found: {file}[/red]")
            return
        
        code = path.read_text()
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            progress.add_task("Refactoring...", total=None)
            
            try:
                import urllib.request
                req = urllib.request.Request(
                    f"http://{self.cli.config['server']['host']}:{self.cli.config['server']['port']}/refactor",
                    data=json.dumps({'code': code, 'instruction': instruction}).encode(),
                    headers={'Content-Type': 'application/json'}
                )
                
                with urllib.request.urlopen(req, timeout=30) as response:
                    data = json.loads(response.read())
                    refactored = data.get('code', '')
                    
                    # Show diff
                    self.console.print(Panel(
                        Syntax(refactored, path.suffix.lstrip('.'), theme="monokai"),
                        title="Refactored Code",
                        border_style="yellow"
                    ))
                    
                    if Confirm.ask("Apply changes?"):
                        path.write_text(refactored)
                        self.console.print("[green]Changes applied![/green]")
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
    
    def watch(self, path: str = "."):
        """Watch files for changes"""
        self.console.print(f"[green]Watching {path} for changes...[/green]")
        self.console.print("[dim]Press Ctrl+C to stop[/dim]\n")
        
        self.cli.file_watcher = FileWatcher(path)
        
        try:
            self.cli.file_watcher.start()
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Stopped watching[/yellow]")
    
    def config(self, key: Optional[str] = None, value: Optional[str] = None):
        """Manage configuration"""
        if key is None:
            # Show all config
            table = Table(title="Mrki Configuration")
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="green")
            
            def flatten_dict(d: dict, prefix: str = ""):
                for k, v in d.items():
                    full_key = f"{prefix}.{k}" if prefix else k
                    if isinstance(v, dict):
                        flatten_dict(v, full_key)
                    else:
                        table.add_row(full_key, str(v))
            
            flatten_dict(self.cli.config)
            self.console.print(table)
        elif value is None:
            # Get specific key
            keys = key.split('.')
            val = self.cli.config
            for k in keys:
                val = val.get(k, {})
            self.console.print(f"{key} = {val}")
        else:
            # Set key
            keys = key.split('.')
            config = self.cli.config
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Try to parse as JSON
            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                parsed_value = value
            
            config[keys[-1]] = parsed_value
            self.cli._save_config()
            self.console.print(f"[green]Set {key} = {parsed_value}[/green]")
    
    def init(self):
        """Initialize Mrki in current project"""
        if Path('.mrki').exists():
            self.console.print("[yellow]Mrki is already initialized in this project[/yellow]")
            return
        
        Path('.mrki').mkdir()
        
        # Create default config
        project_config = {
            'name': Path.cwd().name,
            'language': self._detect_language(),
            'include': ['**/*.py', '**/*.js', '**/*.ts'],
            'exclude': ['**/node_modules', '**/__pycache__', '**/.git']
        }
        
        with open('.mrki/config.json', 'w') as f:
            json.dump(project_config, f, indent=2)
        
        self.console.print("[green]Mrki initialized![/green]")
        self.console.print(f"Project: {project_config['name']}")
        self.console.print(f"Language: {project_config['language']}")
    
    def _detect_language(self) -> str:
        """Detect primary language of project"""
        if any(Path('.').glob('*.py')):
            return 'python'
        elif any(Path('.').glob('package.json')):
            return 'javascript'
        elif any(Path('.').glob('Cargo.toml')):
            return 'rust'
        elif any(Path('.').glob('go.mod')):
            return 'go'
        return 'unknown'


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        prog='mrki',
        description='Mrki - AI-Powered Development Assistant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mrki status              Show Mrki status
  mrki complete file.py    Get completions for file
  mrki chat                Start interactive chat
  mrki explain file.py     Explain code
  mrki test file.py        Generate tests
  mrki watch               Watch files for changes
  mrki init                Initialize Mrki in project
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Status command
    subparsers.add_parser('status', help='Show Mrki status')
    
    # Complete command
    complete_parser = subparsers.add_parser('complete', help='Get code completions')
    complete_parser.add_argument('file', nargs='?', help='File to complete')
    complete_parser.add_argument('--line', '-l', type=int, help='Line number')
    complete_parser.add_argument('--column', '-c', type=int, help='Column number')
    
    # Chat command
    chat_parser = subparsers.add_parser('chat', help='Start interactive chat')
    chat_parser.add_argument('message', nargs='?', help='Initial message')
    
    # Explain command
    explain_parser = subparsers.add_parser('explain', help='Explain code')
    explain_parser.add_argument('file', nargs='?', help='File to explain')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Generate tests')
    test_parser.add_argument('file', help='File to generate tests for')
    test_parser.add_argument('-o', '--output', help='Output file for tests')
    
    # Refactor command
    refactor_parser = subparsers.add_parser('refactor', help='Refactor code')
    refactor_parser.add_argument('file', help='File to refactor')
    refactor_parser.add_argument('instruction', help='Refactoring instruction')
    
    # Watch command
    watch_parser = subparsers.add_parser('watch', help='Watch files for changes')
    watch_parser.add_argument('path', nargs='?', default='.', help='Path to watch')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_parser.add_argument('key', nargs='?', help='Configuration key')
    config_parser.add_argument('value', nargs='?', help='Configuration value')
    
    # Init command
    subparsers.add_parser('init', help='Initialize Mrki in project')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = MrkiCLI()
    commands = Commands(cli)
    
    # Execute command
    if args.command == 'status':
        commands.status()
    elif args.command == 'complete':
        commands.complete(args.file, args.line, args.column)
    elif args.command == 'chat':
        commands.chat(args.message)
    elif args.command == 'explain':
        commands.explain(args.file)
    elif args.command == 'test':
        commands.test(args.file, args.output)
    elif args.command == 'refactor':
        commands.refactor(args.file, args.instruction)
    elif args.command == 'watch':
        commands.watch(args.path)
    elif args.command == 'config':
        commands.config(args.key, args.value)
    elif args.command == 'init':
        commands.init()


if __name__ == '__main__':
    main()
