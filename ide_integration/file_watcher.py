#!/usr/bin/env python3
"""
Mrki File Watcher - Monitor file system changes with hot reload
"""

import fnmatch
import json
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Any
from queue import Queue
from enum import Enum, auto

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("Warning: watchdog not installed. Using fallback polling watcher.")
    print("Install with: pip install watchdog")

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn


class FileChangeType(Enum):
    """Types of file changes"""
    CREATED = auto()
    MODIFIED = auto()
    DELETED = auto()
    MOVED = auto()


@dataclass
class FileChangeEvent:
    """File change event"""
    path: str
    change_type: FileChangeType
    timestamp: float = field(default_factory=time.time)
    is_directory: bool = False
    src_path: Optional[str] = None  # For move events


@dataclass
class WatchConfig:
    """Configuration for file watching"""
    include_patterns: List[str] = field(default_factory=lambda: ['**/*.py', '**/*.js', '**/*.ts'])
    exclude_patterns: List[str] = field(default_factory=lambda: [
        '**/__pycache__/**', '**/*.pyc', '**/node_modules/**',
        '**/.git/**', '**/.venv/**', '**/venv/**',
        '**/.mrki/cache/**', '**/.cursor/**'
    ])
    debounce_ms: int = 300
    recursive: bool = True
    follow_symlinks: bool = False


class FileWatcher:
    """
    File system watcher with hot reload support
    
    Features:
    - Pattern-based file filtering
    - Debounced change events
    - Hot reload callbacks
    - Multiple watch roots
    """
    
    def __init__(self, watch_path: str = ".", config: Optional[WatchConfig] = None):
        self.watch_path = Path(watch_path).resolve()
        self.config = config or WatchConfig()
        self.console = Console()
        
        self._observers: List[Any] = []
        self._handlers: List[Any] = []
        self._callbacks: List[Callable[[FileChangeEvent], None]] = []
        self._hot_reload_callbacks: Dict[str, List[Callable[[], None]]] = {}
        self._event_queue: Queue = Queue()
        self._debounce_timers: Dict[str, threading.Timer] = {}
        self._running = False
        self._lock = threading.Lock()
        
        # Statistics
        self._stats = {
            'events_received': 0,
            'events_processed': 0,
            'files_watched': 0,
            'last_event': None
        }
    
    def on_change(self, callback: Callable[[FileChangeEvent], None]) -> 'FileWatcher':
        """Register a callback for file changes"""
        self._callbacks.append(callback)
        return self
    
    def on_hot_reload(self, pattern: str, callback: Callable[[], None]) -> 'FileWatcher':
        """Register a hot reload callback for files matching pattern"""
        if pattern not in self._hot_reload_callbacks:
            self._hot_reload_callbacks[pattern] = []
        self._hot_reload_callbacks[pattern].append(callback)
        return self
    
    def start(self) -> 'FileWatcher':
        """Start watching files"""
        if self._running:
            return self
        
        self._running = True
        
        if WATCHDOG_AVAILABLE:
            self._start_watchdog()
        else:
            self._start_polling()
        
        # Start event processor
        self._processor_thread = threading.Thread(target=self._process_events)
        self._processor_thread.daemon = True
        self._processor_thread.start()
        
        self.console.print(f"[green]Started watching: {self.watch_path}[/green]")
        
        try:
            while self._running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()
        
        return self
    
    def stop(self) -> 'FileWatcher':
        """Stop watching files"""
        self._running = False
        
        # Stop observers
        for observer in self._observers:
            observer.stop()
        
        for observer in self._observers:
            observer.join()
        
        self._observers.clear()
        self.console.print("[yellow]Stopped watching[/yellow]")
        return self
    
    def _start_watchdog(self):
        """Start watchdog-based file watching"""
        handler = WatchdogHandler(self)
        
        observer = Observer()
        observer.schedule(
            handler,
            str(self.watch_path),
            recursive=self.config.recursive
        )
        observer.start()
        
        self._observers.append(observer)
        self._handlers.append(handler)
    
    def _start_polling(self):
        """Start polling-based file watching (fallback)"""
        self._polling_thread = threading.Thread(target=self._poll_files)
        self._polling_thread.daemon = True
        self._polling_thread.start()
    
    def _poll_files(self):
        """Poll files for changes"""
        file_states: Dict[str, float] = {}
        
        while self._running:
            current_files = set()
            
            for root, dirs, files in os.walk(self.watch_path):
                # Filter directories
                dirs[:] = [d for d in dirs if not self._should_exclude(
                    os.path.join(root, d)
                )]
                
                for filename in files:
                    filepath = os.path.join(root, filename)
                    
                    if self._should_exclude(filepath):
                        continue
                    
                    if not self._should_include(filepath):
                        continue
                    
                    current_files.add(filepath)
                    
                    try:
                        mtime = os.path.getmtime(filepath)
                        
                        if filepath not in file_states:
                            # New file
                            file_states[filepath] = mtime
                            self._queue_event(FileChangeEvent(
                                path=filepath,
                                change_type=FileChangeType.CREATED
                            ))
                        elif file_states[filepath] != mtime:
                            # Modified file
                            file_states[filepath] = mtime
                            self._queue_event(FileChangeEvent(
                                path=filepath,
                                change_type=FileChangeType.MODIFIED
                            ))
                    except OSError:
                        pass
            
            # Check for deleted files
            for filepath in list(file_states.keys()):
                if filepath not in current_files:
                    del file_states[filepath]
                    self._queue_event(FileChangeEvent(
                        path=filepath,
                        change_type=FileChangeType.DELETED
                    ))
            
            self._stats['files_watched'] = len(file_states)
            time.sleep(1)  # Poll interval
    
    def _queue_event(self, event: FileChangeEvent):
        """Queue a file change event"""
        self._event_queue.put(event)
        self._stats['events_received'] += 1
        self._stats['last_event'] = event
    
    def _process_events(self):
        """Process events from queue"""
        while self._running:
            try:
                event = self._event_queue.get(timeout=0.5)
                self._handle_event(event)
            except:
                continue
    
    def _handle_event(self, event: FileChangeEvent):
        """Handle a file change event with debouncing"""
        # Cancel existing timer for this file
        with self._lock:
            if event.path in self._debounce_timers:
                self._debounce_timers[event.path].cancel()
            
            # Create new timer
            timer = threading.Timer(
                self.config.debounce_ms / 1000.0,
                self._process_debounced_event,
                args=[event]
            )
            timer.start()
            self._debounce_timers[event.path] = timer
    
    def _process_debounced_event(self, event: FileChangeEvent):
        """Process a debounced event"""
        with self._lock:
            if event.path in self._debounce_timers:
                del self._debounce_timers[event.path]
        
        # Call registered callbacks
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                self.console.print(f"[red]Callback error: {e}[/red]")
        
        # Check for hot reload patterns
        for pattern, callbacks in self._hot_reload_callbacks.items():
            if fnmatch.fnmatch(event.path, pattern) or \
               fnmatch.fnmatch(os.path.basename(event.path), pattern):
                for callback in callbacks:
                    try:
                        callback()
                    except Exception as e:
                        self.console.print(f"[red]Hot reload error: {e}[/red]")
        
        self._stats['events_processed'] += 1
        
        # Log event
        change_icons = {
            FileChangeType.CREATED: '[green]+[/]',
            FileChangeType.MODIFIED: '[yellow]~[/]',
            FileChangeType.DELETED: '[red]-[/]',
            FileChangeType.MOVED: '[blue]→[/]'
        }
        
        icon = change_icons.get(event.change_type, '[dim]?[/]')
        rel_path = os.path.relpath(event.path, self.watch_path)
        self.console.print(f"{icon} {rel_path}")
    
    def _should_include(self, path: str) -> bool:
        """Check if path matches include patterns"""
        if not self.config.include_patterns:
            return True
        
        for pattern in self.config.include_patterns:
            if fnmatch.fnmatch(path, pattern) or \
               fnmatch.fnmatch(os.path.basename(path), pattern):
                return True
        
        return False
    
    def _should_exclude(self, path: str) -> bool:
        """Check if path matches exclude patterns"""
        for pattern in self.config.exclude_patterns:
            if fnmatch.fnmatch(path, pattern) or \
               fnmatch.fnmatch(os.path.basename(path), pattern):
                return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get watcher statistics"""
        return self._stats.copy()
    
    def show_stats(self):
        """Display watcher statistics"""
        table = Table(title="File Watcher Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Events Received", str(self._stats['events_received']))
        table.add_row("Events Processed", str(self._stats['events_processed']))
        table.add_row("Files Watched", str(self._stats['files_watched']))
        
        if self._stats['last_event']:
            last = self._stats['last_event']
            table.add_row("Last Event", f"{last.change_type.name}: {os.path.basename(last.path)}")
        
        self.console.print(table)


class WatchdogHandler(FileSystemEventHandler):
    """Watchdog event handler"""
    
    def __init__(self, watcher: FileWatcher):
        self.watcher = watcher
    
    def on_created(self, event: FileSystemEvent):
        if not self.watcher._should_exclude(event.src_path):
            self.watcher._queue_event(FileChangeEvent(
                path=event.src_path,
                change_type=FileChangeType.CREATED,
                is_directory=event.is_directory
            ))
    
    def on_modified(self, event: FileSystemEvent):
        if not self.watcher._should_exclude(event.src_path):
            self.watcher._queue_event(FileChangeEvent(
                path=event.src_path,
                change_type=FileChangeType.MODIFIED,
                is_directory=event.is_directory
            ))
    
    def on_deleted(self, event: FileSystemEvent):
        if not self.watcher._should_exclude(event.src_path):
            self.watcher._queue_event(FileChangeEvent(
                path=event.src_path,
                change_type=FileChangeType.DELETED,
                is_directory=event.is_directory
            ))
    
    def on_moved(self, event: FileSystemEvent):
        if not self.watcher._should_exclude(event.src_path):
            self.watcher._queue_event(FileChangeEvent(
                path=event.dest_path,
                change_type=FileChangeType.MOVED,
                is_directory=event.is_directory,
                src_path=event.src_path
            ))


class HotReloader:
    """Hot reload manager for development"""
    
    def __init__(self, watcher: FileWatcher):
        self.watcher = watcher
        self.modules: Dict[str, Any] = {}
        self.reload_hooks: List[Callable[[str], None]] = []
    
    def watch_module(self, module_name: str, module: Any):
        """Watch a module for changes"""
        self.modules[module_name] = module
        
        # Get module file path
        if hasattr(module, '__file__'):
            filepath = module.__file__
            pattern = os.path.basename(filepath)
            
            self.watcher.on_hot_reload(pattern, lambda: self._reload_module(module_name))
    
    def _reload_module(self, module_name: str):
        """Reload a module"""
        import importlib
        
        if module_name in self.modules:
            try:
                module = self.modules[module_name]
                importlib.reload(module)
                self.console.print(f"[green]Reloaded: {module_name}[/green]")
                
                # Call hooks
                for hook in self.reload_hooks:
                    hook(module_name)
            except Exception as e:
                self.console.print(f"[red]Failed to reload {module_name}: {e}[/red]")
    
    def on_reload(self, callback: Callable[[str], None]):
        """Register a callback for module reloads"""
        self.reload_hooks.append(callback)


def create_default_watcher(path: str = ".") -> FileWatcher:
    """Create a file watcher with default configuration"""
    config = WatchConfig(
        include_patterns=['**/*.py', '**/*.js', '**/*.ts', '**/*.rs', '**/*.go'],
        exclude_patterns=[
            '**/__pycache__/**',
            '**/*.pyc',
            '**/node_modules/**',
            '**/.git/**',
            '**/.venv/**',
            '**/venv/**',
            '**/.mrki/cache/**',
            '**/.cursor/**',
            '**/dist/**',
            '**/build/**',
            '**/*.egg-info/**'
        ],
        debounce_ms=300,
        recursive=True
    )
    
    return FileWatcher(path, config)


def demo():
    """Demo the file watcher"""
    console = Console()
    console.print(Panel("[bold]Mrki File Watcher Demo[/bold]", border_style="blue"))
    console.print()
    
    # Create watcher
    watcher = create_default_watcher(".")
    
    # Add callback
    def on_change(event: FileChangeEvent):
        console.print(f"[dim]Callback: {event.change_type.name} {os.path.basename(event.path)}[/dim]")
    
    watcher.on_change(on_change)
    
    # Add hot reload for Python files
    def reload_python():
        console.print("[yellow]Hot reload triggered for Python file[/yellow]")
    
    watcher.on_hot_reload("*.py", reload_python)
    
    console.print("[green]Watching current directory...[/green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")
    
    try:
        watcher.start()
    except KeyboardInterrupt:
        watcher.stop()
        console.print()
        watcher.show_stats()


if __name__ == "__main__":
    demo()
