"""
Mrki State Manager - Shared State and Context Management

This module implements a comprehensive state management system for the Mrki
multi-agent architecture. It provides:
- Hierarchical state organization (global, session, task, agent levels)
- Efficient token budget management (256K context windows)
- State persistence and recovery
- Event-driven state updates
- Concurrent access control
- Context compression and summarization

State Hierarchy:
- Global State: System-wide configuration and shared resources
- Session State: User session data and preferences
- Task State: Task-specific data and intermediate results
- Agent State: Agent-specific memory and context

Author: Mrki Architecture Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import pickle
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Protocol,
    Set,
    TypeVar,
    Union,
)

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger("mrki.state_manager")


class StateLevel(Enum):
    """Hierarchy levels for state organization."""
    GLOBAL = "global"       # System-wide state
    SESSION = "session"     # Per-session state
    TASK = "task"           # Per-task state
    AGENT = "agent"         # Per-agent state
    EPHEMERAL = "ephemeral"  # Temporary state


class StatePersistence(Enum):
    """Persistence levels for state data."""
    TRANSIENT = auto()      # In-memory only
    SESSION_PERSISTED = auto()  # Persisted for session duration
    DURABLE = auto()        # Persisted across sessions
    ARCHIVED = auto()       # Long-term archival


class CompressionStrategy(Enum):
    """Strategies for context compression."""
    NONE = auto()
    SUMMARIZATION = auto()  # LLM-based summarization
    TRUNCATION = auto()     # Simple truncation
    SEMANTIC = auto()       # Semantic compression
    HIERARCHICAL = auto()   # Hierarchical summarization


T = TypeVar("T")


class StateEntry(BaseModel):
    """Single state entry with metadata."""
    key: str
    value: Any
    level: StateLevel
    persistence: StatePersistence
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    access_count: int = 0
    last_accessed: float = Field(default_factory=time.time)
    ttl_seconds: Optional[float] = None
    size_bytes: int = 0
    compressed: bool = False
    tags: Set[str] = Field(default_factory=set)
    
    class Config:
        arbitrary_types_allowed = True
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl_seconds is None:
            return False
        return time.time() - self.created_at > self.ttl_seconds
    
    def touch(self) -> None:
        """Update access metadata."""
        self.access_count += 1
        self.last_accessed = time.time()


class StateSnapshot(BaseModel):
    """Snapshot of state at a point in time."""
    snapshot_id: str
    timestamp: float
    level: StateLevel
    entries: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContextWindow(BaseModel):
    """Represents a context window with token management."""
    window_id: str
    max_tokens: int = 256000
    current_tokens: int = 0
    entries: List[StateEntry] = Field(default_factory=list)
    compression_strategy: CompressionStrategy = CompressionStrategy.SUMMARIZATION
    priority_entries: Set[str] = Field(default_factory=set)
    
    def available_tokens(self) -> int:
        """Get available token budget."""
        return self.max_tokens - self.current_tokens
    
    def can_fit(self, tokens: int) -> bool:
        """Check if tokens can fit in window."""
        return self.available_tokens() >= tokens
    
    def add_entry(self, entry: StateEntry, token_count: int) -> bool:
        """Add entry to window if space available."""
        if not self.can_fit(token_count):
            return False
        
        self.entries.append(entry)
        self.current_tokens += token_count
        return True


@dataclass
class StateMetrics:
    """Metrics for state management."""
    total_entries: int = 0
    total_size_bytes: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    compression_events: int = 0
    eviction_events: int = 0
    persistence_operations: int = 0


class StateConfig(BaseModel):
    """Configuration for state manager."""
    max_global_entries: int = 10000
    max_session_entries: int = 1000
    max_task_entries: int = 500
    max_agent_entries: int = 200
    default_ttl_seconds: Optional[float] = None
    enable_compression: bool = True
    compression_threshold_tokens: int = 200000
    persistence_enabled: bool = True
    persistence_backend: str = "redis"  # redis, disk, memory
    event_driven_updates: bool = True
    token_budget: int = 256000


class StateEvent:
    """Event for state changes."""
    def __init__(
        self,
        event_type: str,
        key: str,
        level: StateLevel,
        old_value: Any = None,
        new_value: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.event_type = event_type
        self.key = key
        self.level = level
        self.old_value = old_value
        self.new_value = new_value
        self.metadata = metadata or {}
        self.timestamp = time.time()


class StateListener(Protocol):
    """Protocol for state change listeners."""
    async def on_state_change(self, event: StateEvent) -> None:
        ...


class ContextCompressor:
    """
    Compresses context to fit within token budget.
    
    Implements multiple compression strategies:
    - Summarization: Use LLM to create condensed summaries
    - Truncation: Remove oldest/least important entries
    - Semantic: Compress based on semantic importance
    - Hierarchical: Multi-level summarization
    """
    
    def __init__(self, strategy: CompressionStrategy = CompressionStrategy.SUMMARIZATION):
        self.strategy = strategy
        self._logger = logger.bind(component="context_compressor")
    
    async def compress(
        self,
        entries: List[StateEntry],
        target_tokens: int,
        preserve_keys: Optional[Set[str]] = None,
    ) -> List[StateEntry]:
        """
        Compress entries to fit within target token budget.
        
        Args:
            entries: Entries to compress
            target_tokens: Target token count
            preserve_keys: Keys that must be preserved
            
        Returns:
            Compressed list of entries
        """
        preserve_keys = preserve_keys or set()
        
        if self.strategy == CompressionStrategy.NONE:
            return entries
        
        elif self.strategy == CompressionStrategy.TRUNCATION:
            return self._truncate(entries, target_tokens, preserve_keys)
        
        elif self.strategy == CompressionStrategy.SUMMARIZATION:
            return await self._summarize(entries, target_tokens, preserve_keys)
        
        elif self.strategy == CompressionStrategy.SEMANTIC:
            return await self._semantic_compress(entries, target_tokens, preserve_keys)
        
        elif self.strategy == CompressionStrategy.HIERARCHICAL:
            return await self._hierarchical_compress(entries, target_tokens, preserve_keys)
        
        return entries
    
    def _truncate(
        self,
        entries: List[StateEntry],
        target_tokens: int,
        preserve_keys: Set[str],
    ) -> List[StateEntry]:
        """Simple truncation strategy."""
        # Sort by importance (access count + recency)
        sorted_entries = sorted(
            entries,
            key=lambda e: (e.access_count, e.last_accessed),
            reverse=True,
        )
        
        result = []
        current_tokens = 0
        
        for entry in sorted_entries:
            if entry.key in preserve_keys:
                result.append(entry)
                current_tokens += entry.size_bytes // 4  # Rough token estimate
            elif current_tokens + (entry.size_bytes // 4) <= target_tokens:
                result.append(entry)
                current_tokens += entry.size_bytes // 4
        
        return result
    
    async def _summarize(
        self,
        entries: List[StateEntry],
        target_tokens: int,
        preserve_keys: Set[str],
    ) -> List[StateEntry]:
        """Summarization-based compression."""
        # Group entries by level and tags
        groups: Dict[str, List[StateEntry]] = {}
        for entry in entries:
            if entry.key in preserve_keys:
                continue
            tag_key = ",".join(sorted(entry.tags)) if entry.tags else "untagged"
            groups.setdefault(tag_key, []).append(entry)
        
        # Summarize each group
        summarized = []
        for group_entries in groups.values():
            if len(group_entries) > 3:
                # Create summary entry
                summary = StateEntry(
                    key=f"summary_{hash(group_entries[0].key)}",
                    value=f"Summarized {len(group_entries)} entries",
                    level=group_entries[0].level,
                    persistence=group_entries[0].persistence,
                    tags=group_entries[0].tags,
                )
                summarized.append(summary)
            else:
                summarized.extend(group_entries)
        
        # Add preserved entries
        for entry in entries:
            if entry.key in preserve_keys:
                summarized.append(entry)
        
        return summarized
    
    async def _semantic_compress(
        self,
        entries: List[StateEntry],
        target_tokens: int,
        preserve_keys: Set[str],
    ) -> List[StateEntry]:
        """Semantic compression based on content importance."""
        # Placeholder for semantic compression
        # Would use embeddings to determine importance
        return self._truncate(entries, target_tokens, preserve_keys)
    
    async def _hierarchical_compress(
        self,
        entries: List[StateEntry],
        target_tokens: int,
        preserve_keys: Set[str],
    ) -> List[StateEntry]:
        """Hierarchical multi-level compression."""
        # First pass: truncate to 150% of target
        first_pass = self._truncate(entries, int(target_tokens * 1.5), preserve_keys)
        
        # Second pass: summarize
        second_pass = await self._summarize(first_pass, int(target_tokens * 1.2), preserve_keys)
        
        # Final pass: truncate to target
        return self._truncate(second_pass, target_tokens, preserve_keys)


class StateManager:
    """
    Central state management system for Mrki multi-agent architecture.
    
    The StateManager provides hierarchical state organization with efficient
    token budget management. It supports:
    - Multi-level state (global, session, task, agent)
    - Context window management (256K tokens)
    - Automatic compression and eviction
    - Event-driven updates
    - Persistence and recovery
    
    Example:
        >>> state_mgr = StateManager(config)
        >>> await state_mgr.set("user_preference", value, level=StateLevel.SESSION)
        >>> value = await state_mgr.get("user_preference")
        >>> context = await state_mgr.build_context_window(task_id, max_tokens=128000)
    """
    
    def __init__(self, config: Optional[StateConfig] = None):
        """
        Initialize the state manager.
        
        Args:
            config: State management configuration
        """
        self.config = config or StateConfig()
        
        # State storage by level
        self._global_state: Dict[str, StateEntry] = {}
        self._session_states: Dict[str, Dict[str, StateEntry]] = {}
        self._task_states: Dict[str, Dict[str, StateEntry]] = {}
        self._agent_states: Dict[str, Dict[str, StateEntry]] = {}
        
        # Context windows
        self._context_windows: Dict[str, ContextWindow] = {}
        
        # Event listeners
        self._listeners: List[StateListener] = []
        self._event_queue: asyncio.Queue = asyncio.Queue()
        
        # Compression
        self._compressor = ContextCompressor(CompressionStrategy.SUMMARIZATION)
        
        # Metrics
        self._metrics = StateMetrics()
        
        # Locks
        self._locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._global_lock = asyncio.Lock()
        
        # Background tasks
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
        self._event_processor_task: Optional[asyncio.Task] = None
        
        self._logger = logger.bind(component="state_manager")
    
    async def initialize(self) -> None:
        """Initialize the state manager."""
        self._running = True
        self._logger.info("state_manager_initializing")
        
        # Start background tasks
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._event_processor_task = asyncio.create_task(self._event_processor())
        
        self._logger.info("state_manager_initialized")
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the state manager."""
        self._running = False
        self._logger.info("state_manager_shutting_down")
        
        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self._event_processor_task:
            self._event_processor_task.cancel()
            try:
                await self._event_processor_task
            except asyncio.CancelledError:
                pass
        
        # Persist durable state
        if self.config.persistence_enabled:
            await self._persist_all()
        
        self._logger.info("state_manager_shutdown_complete")
    
    async def set(
        self,
        key: str,
        value: Any,
        level: StateLevel = StateLevel.GLOBAL,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        persistence: Optional[StatePersistence] = None,
        ttl_seconds: Optional[float] = None,
        tags: Optional[Set[str]] = None,
    ) -> None:
        """
        Set a state value.
        
        Args:
            key: State key
            value: State value
            level: State hierarchy level
            session_id: Session ID for session-level state
            task_id: Task ID for task-level state
            agent_id: Agent ID for agent-level state
            persistence: Persistence level
            ttl_seconds: Time-to-live in seconds
            tags: Tags for categorization
        """
        # Calculate size
        try:
            size_bytes = len(pickle.dumps(value))
        except Exception:
            size_bytes = len(str(value))
        
        entry = StateEntry(
            key=key,
            value=value,
            level=level,
            persistence=persistence or StatePersistence.TRANSIENT,
            ttl_seconds=ttl_seconds or self.config.default_ttl_seconds,
            size_bytes=size_bytes,
            tags=tags or set(),
        )
        
        # Store based on level
        if level == StateLevel.GLOBAL:
            async with self._global_lock:
                old_value = self._global_state.get(key)
                self._global_state[key] = entry
                
                # Enforce limits
                if len(self._global_state) > self.config.max_global_entries:
                    await self._evict_oldest(self._global_state, self.config.max_global_entries)
        
        elif level == StateLevel.SESSION:
            if not session_id:
                raise ValueError("session_id required for SESSION level state")
            async with self._get_lock(f"session:{session_id}"):
                if session_id not in self._session_states:
                    self._session_states[session_id] = {}
                old_value = self._session_states[session_id].get(key)
                self._session_states[session_id][key] = entry
                
                if len(self._session_states[session_id]) > self.config.max_session_entries:
                    await self._evict_oldest(
                        self._session_states[session_id],
                        self.config.max_session_entries,
                    )
        
        elif level == StateLevel.TASK:
            if not task_id:
                raise ValueError("task_id required for TASK level state")
            async with self._get_lock(f"task:{task_id}"):
                if task_id not in self._task_states:
                    self._task_states[task_id] = {}
                old_value = self._task_states[task_id].get(key)
                self._task_states[task_id][key] = entry
                
                if len(self._task_states[task_id]) > self.config.max_task_entries:
                    await self._evict_oldest(
                        self._task_states[task_id],
                        self.config.max_task_entries,
                    )
        
        elif level == StateLevel.AGENT:
            if not agent_id:
                raise ValueError("agent_id required for AGENT level state")
            async with self._get_lock(f"agent:{agent_id}"):
                if agent_id not in self._agent_states:
                    self._agent_states[agent_id] = {}
                old_value = self._agent_states[agent_id].get(key)
                self._agent_states[agent_id][key] = entry
                
                if len(self._agent_states[agent_id]) > self.config.max_agent_entries:
                    await self._evict_oldest(
                        self._agent_states[agent_id],
                        self.config.max_agent_entries,
                    )
        
        # Emit event
        await self._emit_event(StateEvent(
            event_type="set",
            key=key,
            level=level,
            old_value=old_value.value if old_value else None,
            new_value=value,
        ))
        
        self._metrics.total_entries += 1
        self._metrics.total_size_bytes += size_bytes
    
    async def get(
        self,
        key: str,
        level: StateLevel = StateLevel.GLOBAL,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        default: Any = None,
    ) -> Any:
        """
        Get a state value.
        
        Args:
            key: State key
            level: State hierarchy level
            session_id: Session ID for session-level state
            task_id: Task ID for task-level state
            agent_id: Agent ID for agent-level state
            default: Default value if key not found
            
        Returns:
            State value or default
        """
        entry = await self._get_entry(key, level, session_id, task_id, agent_id)
        
        if entry is None:
            self._metrics.cache_misses += 1
            return default
        
        if entry.is_expired():
            await self.delete(key, level, session_id, task_id, agent_id)
            self._metrics.cache_misses += 1
            return default
        
        entry.touch()
        self._metrics.cache_hits += 1
        
        return entry.value
    
    async def _get_entry(
        self,
        key: str,
        level: StateLevel,
        session_id: Optional[str],
        task_id: Optional[str],
        agent_id: Optional[str],
    ) -> Optional[StateEntry]:
        """Get state entry without checking expiration."""
        if level == StateLevel.GLOBAL:
            return self._global_state.get(key)
        
        elif level == StateLevel.SESSION:
            if session_id and session_id in self._session_states:
                return self._session_states[session_id].get(key)
        
        elif level == StateLevel.TASK:
            if task_id and task_id in self._task_states:
                return self._task_states[task_id].get(key)
        
        elif level == StateLevel.AGENT:
            if agent_id and agent_id in self._agent_states:
                return self._agent_states[agent_id].get(key)
        
        return None
    
    async def delete(
        self,
        key: str,
        level: StateLevel = StateLevel.GLOBAL,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> bool:
        """
        Delete a state value.
        
        Args:
            key: State key
            level: State hierarchy level
            session_id: Session ID for session-level state
            task_id: Task ID for task-level state
            agent_id: Agent ID for agent-level state
            
        Returns:
            True if deleted, False if not found
        """
        old_value = None
        
        if level == StateLevel.GLOBAL:
            async with self._global_lock:
                if key in self._global_state:
                    old_value = self._global_state.pop(key)
        
        elif level == StateLevel.SESSION and session_id:
            async with self._get_lock(f"session:{session_id}"):
                if session_id in self._session_states and key in self._session_states[session_id]:
                    old_value = self._session_states[session_id].pop(key)
        
        elif level == StateLevel.TASK and task_id:
            async with self._get_lock(f"task:{task_id}"):
                if task_id in self._task_states and key in self._task_states[task_id]:
                    old_value = self._task_states[task_id].pop(key)
        
        elif level == StateLevel.AGENT and agent_id:
            async with self._get_lock(f"agent:{agent_id}"):
                if agent_id in self._agent_states and key in self._agent_states[agent_id]:
                    old_value = self._agent_states[agent_id].pop(key)
        
        if old_value:
            await self._emit_event(StateEvent(
                event_type="delete",
                key=key,
                level=level,
                old_value=old_value.value,
            ))
            return True
        
        return False
    
    async def build_context_window(
        self,
        window_id: str,
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        max_tokens: int = 256000,
        include_global: bool = True,
        priority_keys: Optional[Set[str]] = None,
    ) -> ContextWindow:
        """
        Build a context window for agent execution.
        
        Args:
            window_id: Unique window identifier
            task_id: Task ID to include task-level state
            agent_id: Agent ID to include agent-level state
            session_id: Session ID to include session-level state
            max_tokens: Maximum tokens for context
            include_global: Include global state
            priority_keys: Keys to prioritize in context
            
        Returns:
            ContextWindow with organized state
        """
        window = ContextWindow(
            window_id=window_id,
            max_tokens=max_tokens,
        )
        
        # Add priority keys first
        priority_keys = priority_keys or set()
        
        # Collect all entries
        all_entries: List[StateEntry] = []
        
        if include_global:
            all_entries.extend(self._global_state.values())
        
        if session_id and session_id in self._session_states:
            all_entries.extend(self._session_states[session_id].values())
        
        if task_id and task_id in self._task_states:
            all_entries.extend(self._task_states[task_id].values())
        
        if agent_id and agent_id in self._agent_states:
            all_entries.extend(self._agent_states[agent_id].values())
        
        # Sort by importance (priority keys first, then access patterns)
        def entry_priority(e: StateEntry) -> Tuple[int, int, float]:
            is_priority = 1 if e.key in priority_keys else 0
            return (is_priority, e.access_count, e.last_accessed)
        
        all_entries.sort(key=entry_priority, reverse=True)
        
        # Add entries until window is full
        for entry in all_entries:
            # Rough token estimate: 4 bytes per token
            token_estimate = entry.size_bytes // 4
            
            if not window.add_entry(entry, token_estimate):
                # Window full, need compression
                if self.config.enable_compression:
                    compressed = await self._compressor.compress(
                        window.entries,
                        max_tokens,
                        priority_keys,
                    )
                    window.entries = compressed
                    window.current_tokens = sum(e.size_bytes // 4 for e in compressed)
                break
        
        self._context_windows[window_id] = window
        
        return window
    
    async def get_context_for_agent(
        self,
        agent_id: str,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None,
        max_tokens: int = 128000,
    ) -> Dict[str, Any]:
        """
        Get context dictionary for agent execution.
        
        Args:
            agent_id: Agent ID
            task_id: Task ID
            session_id: Session ID
            max_tokens: Maximum tokens
            
        Returns:
            Context dictionary
        """
        window_id = f"ctx_{agent_id}_{task_id or 'none'}_{int(time.time())}"
        window = await self.build_context_window(
            window_id=window_id,
            task_id=task_id,
            agent_id=agent_id,
            session_id=session_id,
            max_tokens=max_tokens,
        )
        
        # Convert to dictionary
        context = {}
        for entry in window.entries:
            context[entry.key] = entry.value
        
        return context
    
    async def snapshot(
        self,
        level: StateLevel,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> StateSnapshot:
        """
        Create a snapshot of state at current level.
        
        Args:
            level: State level to snapshot
            session_id: Session ID for session level
            task_id: Task ID for task level
            agent_id: Agent ID for agent level
            
        Returns:
            StateSnapshot
        """
        entries: Dict[str, Any] = {}
        
        if level == StateLevel.GLOBAL:
            entries = {k: v.value for k, v in self._global_state.items()}
        
        elif level == StateLevel.SESSION and session_id:
            if session_id in self._session_states:
                entries = {k: v.value for k, v in self._session_states[session_id].items()}
        
        elif level == StateLevel.TASK and task_id:
            if task_id in self._task_states:
                entries = {k: v.value for k, v in self._task_states[task_id].items()}
        
        elif level == StateLevel.AGENT and agent_id:
            if agent_id in self._agent_states:
                entries = {k: v.value for k, v in self._agent_states[agent_id].items()}
        
        return StateSnapshot(
            snapshot_id=f"snap_{level.value}_{int(time.time())}",
            timestamp=time.time(),
            level=level,
            entries=entries,
        )
    
    async def restore(self, snapshot: StateSnapshot) -> None:
        """Restore state from snapshot."""
        for key, value in snapshot.entries.items():
            await self.set(key, value, level=snapshot.level)
    
    def add_listener(self, listener: StateListener) -> None:
        """Add a state change listener."""
        self._listeners.append(listener)
    
    def remove_listener(self, listener: StateListener) -> None:
        """Remove a state change listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    async def _emit_event(self, event: StateEvent) -> None:
        """Emit a state change event."""
        if self.config.event_driven_updates:
            await self._event_queue.put(event)
    
    async def _event_processor(self) -> None:
        """Process state change events."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                
                # Notify listeners
                for listener in self._listeners:
                    try:
                        await listener.on_state_change(event)
                    except Exception as e:
                        self._logger.error("listener_error", error=str(e))
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error("event_processor_error", error=str(e))
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup loop for expired entries."""
        while self._running:
            try:
                await asyncio.sleep(60)  # Run every minute
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error("cleanup_error", error=str(e))
    
    async def _cleanup_expired(self) -> None:
        """Remove expired state entries."""
        # Clean global state
        async with self._global_lock:
            expired = [k for k, v in self._global_state.items() if v.is_expired()]
            for k in expired:
                del self._global_state[k]
        
        # Clean session states
        for session_id, state in list(self._session_states.items()):
            async with self._get_lock(f"session:{session_id}"):
                expired = [k for k, v in state.items() if v.is_expired()]
                for k in expired:
                    del state[k]
        
        # Clean task states
        for task_id, state in list(self._task_states.items()):
            async with self._get_lock(f"task:{task_id}"):
                expired = [k for k, v in state.items() if v.is_expired()]
                for k in expired:
                    del state[k]
        
        # Clean agent states
        for agent_id, state in list(self._agent_states.items()):
            async with self._get_lock(f"agent:{agent_id}"):
                expired = [k for k, v in state.items() if v.is_expired()]
                for k in expired:
                    del state[k]
    
    async def _evict_oldest(
        self,
        state_dict: Dict[str, StateEntry],
        max_size: int,
    ) -> None:
        """Evict oldest entries to maintain size limit."""
        while len(state_dict) > max_size:
            # Find oldest entry by last access
            oldest_key = min(state_dict.keys(), key=lambda k: state_dict[k].last_accessed)
            del state_dict[oldest_key]
            self._metrics.eviction_events += 1
    
    def _get_lock(self, key: str) -> asyncio.Lock:
        """Get or create a lock for a key."""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]
    
    async def _persist_all(self) -> None:
        """Persist all durable state."""
        # Implementation depends on persistence backend
        pass
    
    def get_metrics(self) -> StateMetrics:
        """Get state management metrics."""
        return self._metrics
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive state statistics."""
        return {
            "global_entries": len(self._global_state),
            "session_count": len(self._session_states),
            "task_count": len(self._task_states),
            "agent_count": len(self._agent_states),
            "context_windows": len(self._context_windows),
            "metrics": {
                "total_entries": self._metrics.total_entries,
                "cache_hits": self._metrics.cache_hits,
                "cache_misses": self._metrics.cache_misses,
                "hit_rate": (
                    self._metrics.cache_hits / 
                    (self._metrics.cache_hits + self._metrics.cache_misses)
                    if (self._metrics.cache_hits + self._metrics.cache_misses) > 0 
                    else 0
                ),
            },
        }


# Factory function
async def create_state_manager(
    config: Optional[StateConfig] = None,
) -> StateManager:
    """
    Factory function to create and initialize a state manager.
    
    Args:
        config: Optional configuration
        
    Returns:
        Initialized StateManager instance
    """
    manager = StateManager(config)
    await manager.initialize()
    return manager
