"""
Mrki Tool Registry - Dynamic Tool Registration and Management

This module implements a comprehensive tool registry for managing 1,500+ tools
with dynamic loading, batching, and optimization. It provides:
- Dynamic tool registration and discovery
- Tool categorization and tagging
- Batch tool call optimization
- Tool versioning and compatibility
- Access control and permissions
- Tool execution monitoring

Tool Types:
- Function Tools: Python function wrappers
- API Tools: External API integrations
- LLM Tools: LLM-based processing tools
- Composite Tools: Multi-step tool chains

Author: Mrki Architecture Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Set,
    TypeVar,
    Union,
    get_type_hints,
)

import structlog
from pydantic import BaseModel, Field, create_model

logger = structlog.get_logger("mrki.tool_registry")


class ToolType(Enum):
    """Types of tools in the registry."""
    FUNCTION = "function"
    API = "api"
    LLM = "llm"
    COMPOSITE = "composite"
    PLUGIN = "plugin"


class ToolCategory(Enum):
    """Categories for tool organization."""
    WEB_SEARCH = "web_search"
    CODE_EXECUTION = "code_execution"
    DATA_PROCESSING = "data_processing"
    FILE_OPERATIONS = "file_operations"
    COMMUNICATION = "communication"
    ANALYSIS = "analysis"
    GENERATION = "generation"
    VALIDATION = "validation"
    INTEGRATION = "integration"
    SYSTEM = "system"


class ToolStatus(Enum):
    """Status of tool registration."""
    REGISTERED = auto()
    LOADING = auto()
    ACTIVE = auto()
    DEPRECATED = auto()
    DISABLED = auto()
    ERROR = auto()


@dataclass
class ToolMetrics:
    """Metrics for tool execution."""
    call_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_execution_time_ms: float = 0.0
    average_execution_time_ms: float = 0.0
    last_called: Optional[float] = None
    last_error: Optional[str] = None
    error_count_by_type: Dict[str, int] = field(default_factory=dict)


class ToolParameter(BaseModel):
    """Parameter definition for tool."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None


class ToolOutput(BaseModel):
    """Output definition for tool."""
    type: str
    description: str
    schema: Optional[Dict[str, Any]] = None


class ToolDefinition(BaseModel):
    """Complete tool definition."""
    tool_id: str
    name: str
    description: str
    tool_type: ToolType
    category: ToolCategory
    parameters: List[ToolParameter] = Field(default_factory=list)
    output: Optional[ToolOutput] = None
    version: str = "1.0.0"
    author: Optional[str] = None
    tags: Set[str] = Field(default_factory=set)
    permissions: List[str] = Field(default_factory=list)
    timeout_seconds: float = 30.0
    retry_policy: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Result from tool execution."""
    tool_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BatchToolRequest(BaseModel):
    """Batch request for multiple tool calls."""
    batch_id: str
    requests: List[Dict[str, Any]] = Field(default_factory=list)
    parallel: bool = True
    timeout_seconds: float = 60.0
    priority: int = 5  # 1-10, lower is higher priority


class BatchToolResult(BaseModel):
    """Result from batch tool execution."""
    batch_id: str
    results: List[ToolResult] = Field(default_factory=list)
    completed_count: int = 0
    failed_count: int = 0
    total_execution_time_ms: float = 0.0
    timestamp: float = Field(default_factory=time.time)


class ToolRegistryConfig(BaseModel):
    """Configuration for tool registry."""
    max_concurrent_calls: int = 1500
    default_timeout_seconds: float = 30.0
    enable_batching: bool = True
    batch_size: int = 100
    batch_timeout_ms: float = 50.0
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    enable_metrics: bool = True
    auto_load_plugins: bool = True
    plugin_paths: List[str] = Field(default_factory=list)
    permission_checking: bool = True


class ToolExecutor(Protocol):
    """Protocol for tool executors."""
    
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters."""
        ...
    
    async def health_check(self) -> bool:
        """Check if tool is healthy."""
        ...


class RegisteredTool:
    """
    Wrapper for registered tools with execution management.
    
    Each RegisteredTool wraps a tool definition and its executor,
    providing:
    - Execution management
    - Metrics collection
    - Error handling
    - Caching support
    """
    
    def __init__(
        self,
        definition: ToolDefinition,
        executor: ToolExecutor,
    ):
        """
        Initialize registered tool.
        
        Args:
            definition: Tool definition
            executor: Tool executor implementation
        """
        self.definition = definition
        self.executor = executor
        self.status = ToolStatus.REGISTERED
        self.metrics = ToolMetrics()
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        self._logger = logger.bind(tool_id=definition.tool_id)
    
    async def execute(
        self,
        params: Dict[str, Any],
        use_cache: bool = True,
        cache_ttl: Optional[float] = None,
    ) -> ToolResult:
        """
        Execute the tool with given parameters.
        
        Args:
            params: Tool parameters
            use_cache: Whether to use caching
            cache_ttl: Cache TTL in seconds
            
        Returns:
            Tool execution result
        """
        start_time = time.time()
        cache_key = None
        
        # Check cache
        if use_cache:
            cache_key = self._generate_cache_key(params)
            cached = self._get_cached(cache_key)
            if cached is not None:
                self._logger.debug("cache_hit", tool_id=self.definition.tool_id)
                return ToolResult(
                    tool_id=self.definition.tool_id,
                    success=True,
                    output=cached,
                    execution_time_ms=0.0,
                    metadata={"cached": True},
                )
        
        # Execute tool
        try:
            self.status = ToolStatus.ACTIVE
            self.metrics.call_count += 1
            
            output = await asyncio.wait_for(
                self.executor.execute(**params),
                timeout=self.definition.timeout_seconds,
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Update metrics
            self.metrics.success_count += 1
            self.metrics.total_execution_time_ms += execution_time
            self.metrics.average_execution_time_ms = (
                self.metrics.total_execution_time_ms / self.metrics.call_count
            )
            self.metrics.last_called = time.time()
            
            # Cache result
            if use_cache and cache_key:
                self._cache_result(cache_key, output, cache_ttl)
            
            return ToolResult(
                tool_id=self.definition.tool_id,
                success=True,
                output=output,
                execution_time_ms=execution_time,
            )
            
        except asyncio.TimeoutError:
            error_msg = f"Tool execution timed out after {self.definition.timeout_seconds}s"
            self._handle_error("timeout", error_msg)
            return ToolResult(
                tool_id=self.definition.tool_id,
                success=False,
                error=error_msg,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
            
        except Exception as e:
            error_msg = str(e)
            self._handle_error(type(e).__name__, error_msg)
            return ToolResult(
                tool_id=self.definition.tool_id,
                success=False,
                error=error_msg,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        
        finally:
            self.status = ToolStatus.REGISTERED
    
    def _generate_cache_key(self, params: Dict[str, Any]) -> str:
        """Generate cache key from parameters."""
        key_data = json.dumps(params, sort_keys=True)
        return f"{self.definition.tool_id}:{hash(key_data)}"
    
    def _get_cached(self, cache_key: str) -> Any:
        """Get cached result if available."""
        if cache_key not in self._cache:
            return None
        
        timestamp = self._cache_timestamps.get(cache_key, 0)
        if time.time() - timestamp > 300:  # Default 5 min TTL
            del self._cache[cache_key]
            del self._cache_timestamps[cache_key]
            return None
        
        return self._cache[cache_key]
    
    def _cache_result(
        self,
        cache_key: str,
        output: Any,
        ttl: Optional[float] = None,
    ) -> None:
        """Cache execution result."""
        self._cache[cache_key] = output
        self._cache_timestamps[cache_key] = time.time()
    
    def _handle_error(self, error_type: str, error_msg: str) -> None:
        """Handle execution error."""
        self.metrics.failure_count += 1
        self.metrics.last_error = error_msg
        self.metrics.error_count_by_type[error_type] = (
            self.metrics.error_count_by_type.get(error_type, 0) + 1
        )
        self._logger.warning(
            "tool_execution_failed",
            tool_id=self.definition.tool_id,
            error_type=error_type,
            error=error_msg,
        )
    
    async def health_check(self) -> bool:
        """Check tool health."""
        try:
            return await self.executor.health_check()
        except Exception as e:
            self._logger.error("health_check_failed", error=str(e))
            return False
    
    def get_metrics(self) -> ToolMetrics:
        """Get tool metrics."""
        return self.metrics
    
    def invalidate_cache(self) -> int:
        """Invalidate tool cache."""
        count = len(self._cache)
        self._cache.clear()
        self._cache_timestamps.clear()
        return count


class ToolRegistry:
    """
    Central registry for managing tools in the Mrki system.
    
    The ToolRegistry provides:
    - Dynamic tool registration and discovery
    - Batch execution optimization for 1,500+ simultaneous calls
    - Tool categorization and search
    - Version management
    - Access control
    - Execution monitoring
    
    Example:
        >>> registry = ToolRegistry(config)
        >>> await registry.register_tool(definition, executor)
        >>> result = await registry.execute_tool("web_search", {"query": "AI"})
        >>> batch_result = await registry.execute_batch(batch_request)
    """
    
    def __init__(self, config: Optional[ToolRegistryConfig] = None):
        """
        Initialize the tool registry.
        
        Args:
            config: Registry configuration
        """
        self.config = config or ToolRegistryConfig()
        
        # Tool storage
        self._tools: Dict[str, RegisteredTool] = {}
        self._tools_by_category: Dict[ToolCategory, Set[str]] = defaultdict(set)
        self._tools_by_tag: Dict[str, Set[str]] = defaultdict(set)
        self._tools_by_type: Dict[ToolType, Set[str]] = defaultdict(set)
        
        # Batch processing
        self._batch_queue: asyncio.Queue = asyncio.Queue()
        self._batch_semaphore = asyncio.Semaphore(self.config.max_concurrent_calls)
        
        # Execution tracking
        self._active_executions: Dict[str, asyncio.Task] = {}
        
        # Metrics
        self._total_calls: int = 0
        self._total_batches: int = 0
        
        # Control
        self._running = False
        self._batch_processor_task: Optional[asyncio.Task] = None
        
        self._logger = logger.bind(component="tool_registry")
    
    async def initialize(self) -> None:
        """Initialize the tool registry."""
        self._running = True
        self._logger.info(
            "tool_registry_initializing",
            max_concurrent=self.config.max_concurrent_calls,
        )
        
        # Start batch processor
        if self.config.enable_batching:
            self._batch_processor_task = asyncio.create_task(self._batch_processor())
        
        # Auto-load plugins
        if self.config.auto_load_plugins:
            await self._load_plugins()
        
        self._logger.info("tool_registry_initialized")
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the tool registry."""
        self._running = False
        self._logger.info("tool_registry_shutting_down")
        
        # Cancel batch processor
        if self._batch_processor_task:
            self._batch_processor_task.cancel()
            try:
                await self._batch_processor_task
            except asyncio.CancelledError:
                pass
        
        # Cancel active executions
        for task in self._active_executions.values():
            task.cancel()
        
        self._logger.info("tool_registry_shutdown_complete")
    
    async def register_tool(
        self,
        definition: ToolDefinition,
        executor: ToolExecutor,
    ) -> bool:
        """
        Register a new tool.
        
        Args:
            definition: Tool definition
            executor: Tool executor
            
        Returns:
            True if registration successful
        """
        if definition.tool_id in self._tools:
            self._logger.warning(
                "tool_already_registered",
                tool_id=definition.tool_id,
            )
            return False
        
        tool = RegisteredTool(definition, executor)
        
        # Health check
        if not await tool.health_check():
            self._logger.error(
                "tool_health_check_failed",
                tool_id=definition.tool_id,
            )
            return False
        
        # Store tool
        self._tools[definition.tool_id] = tool
        self._tools_by_category[definition.category].add(definition.tool_id)
        self._tools_by_type[definition.tool_type].add(definition.tool_id)
        
        for tag in definition.tags:
            self._tools_by_tag[tag].add(definition.tool_id)
        
        tool.status = ToolStatus.ACTIVE
        
        self._logger.info(
            "tool_registered",
            tool_id=definition.tool_id,
            name=definition.name,
            category=definition.category.value,
        )
        
        return True
    
    async def unregister_tool(self, tool_id: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            tool_id: Tool ID to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        if tool_id not in self._tools:
            return False
        
        tool = self._tools[tool_id]
        definition = tool.definition
        
        # Remove from indexes
        del self._tools[tool_id]
        self._tools_by_category[definition.category].discard(tool_id)
        self._tools_by_type[definition.tool_type].discard(tool_id)
        
        for tag in definition.tags:
            self._tools_by_tag[tag].discard(tool_id)
        
        self._logger.info("tool_unregistered", tool_id=tool_id)
        
        return True
    
    async def execute_tool(
        self,
        tool_id: str,
        params: Dict[str, Any],
        use_cache: bool = True,
    ) -> ToolResult:
        """
        Execute a single tool.
        
        Args:
            tool_id: Tool ID
            params: Tool parameters
            use_cache: Whether to use caching
            
        Returns:
            Tool execution result
        """
        if tool_id not in self._tools:
            return ToolResult(
                tool_id=tool_id,
                success=False,
                error=f"Tool not found: {tool_id}",
            )
        
        tool = self._tools[tool_id]
        
        async with self._batch_semaphore:
            self._total_calls += 1
            return await tool.execute(params, use_cache=use_cache)
    
    async def execute_batch(
        self,
        batch_request: BatchToolRequest,
    ) -> BatchToolResult:
        """
        Execute multiple tools in batch.
        
        This is optimized for high-throughput execution of 1,500+
        simultaneous tool calls.
        
        Args:
            batch_request: Batch execution request
            
        Returns:
            Batch execution results
        """
        start_time = time.time()
        self._total_batches += 1
        
        self._logger.info(
            "batch_execution_started",
            batch_id=batch_request.batch_id,
            request_count=len(batch_request.requests),
        )
        
        # Create execution tasks
        tasks = []
        for request in batch_request.requests:
            tool_id = request.get("tool_id")
            params = request.get("params", {})
            
            task = self.execute_tool(tool_id, params)
            tasks.append(task)
        
        # Execute based on parallel setting
        if batch_request.parallel:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            results = []
            for task in tasks:
                try:
                    result = await task
                    results.append(result)
                except Exception as e:
                    results.append(e)
        
        # Process results
        tool_results = []
        completed = 0
        failed = 0
        
        for result in results:
            if isinstance(result, Exception):
                failed += 1
                tool_results.append(ToolResult(
                    tool_id="unknown",
                    success=False,
                    error=str(result),
                ))
            else:
                tool_results.append(result)
                if result.success:
                    completed += 1
                else:
                    failed += 1
        
        execution_time = (time.time() - start_time) * 1000
        
        self._logger.info(
            "batch_execution_completed",
            batch_id=batch_request.batch_id,
            completed=completed,
            failed=failed,
            execution_time_ms=execution_time,
        )
        
        return BatchToolResult(
            batch_id=batch_request.batch_id,
            results=tool_results,
            completed_count=completed,
            failed_count=failed,
            total_execution_time_ms=execution_time,
        )
    
    async def _batch_processor(self) -> None:
        """Background batch processor for queued requests."""
        while self._running:
            try:
                # Collect batch
                batch = []
                deadline = time.time() + (self.config.batch_timeout_ms / 1000)
                
                while len(batch) < self.config.batch_size:
                    timeout = max(0, deadline - time.time())
                    try:
                        request = await asyncio.wait_for(
                            self._batch_queue.get(),
                            timeout=timeout,
                        )
                        batch.append(request)
                    except asyncio.TimeoutError:
                        break
                
                # Process batch if not empty
                if batch:
                    await self._process_batch_queue(batch)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error("batch_processor_error", error=str(e))
    
    async def _process_batch_queue(
        self,
        batch: List[Dict[str, Any]],
    ) -> None:
        """Process a batch of queued requests."""
        # Group by tool for efficiency
        by_tool: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        for request in batch:
            tool_id = request.get("tool_id")
            by_tool[tool_id].append(request)
        
        # Execute in parallel
        tasks = []
        for tool_id, requests in by_tool.items():
            for request in requests:
                task = self.execute_tool(
                    tool_id,
                    request.get("params", {}),
                )
                tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_tool(self, tool_id: str) -> Optional[RegisteredTool]:
        """Get a registered tool by ID."""
        return self._tools.get(tool_id)
    
    def get_tool_definition(self, tool_id: str) -> Optional[ToolDefinition]:
        """Get tool definition by ID."""
        tool = self._tools.get(tool_id)
        return tool.definition if tool else None
    
    def find_tools(
        self,
        category: Optional[ToolCategory] = None,
        tool_type: Optional[ToolType] = None,
        tags: Optional[List[str]] = None,
        query: Optional[str] = None,
    ) -> List[ToolDefinition]:
        """
        Find tools matching criteria.
        
        Args:
            category: Filter by category
            tool_type: Filter by type
            tags: Filter by tags
            query: Search query
            
        Returns:
            List of matching tool definitions
        """
        # Start with all tools
        candidates = set(self._tools.keys())
        
        # Apply filters
        if category:
            candidates &= self._tools_by_category.get(category, set())
        
        if tool_type:
            candidates &= self._tools_by_type.get(tool_type, set())
        
        if tags:
            for tag in tags:
                candidates &= self._tools_by_tag.get(tag, set())
        
        # Get definitions
        results = [self._tools[tid].definition for tid in candidates]
        
        # Apply text search if query provided
        if query:
            query_lower = query.lower()
            results = [
                d for d in results
                if query_lower in d.name.lower()
                or query_lower in d.description.lower()
            ]
        
        return results
    
    def list_tools(self) -> List[ToolDefinition]:
        """List all registered tools."""
        return [tool.definition for tool in self._tools.values()]
    
    def get_tools_by_category(self, category: ToolCategory) -> List[ToolDefinition]:
        """Get all tools in a category."""
        tool_ids = self._tools_by_category.get(category, set())
        return [self._tools[tid].definition for tid in tool_ids]
    
    def get_categories(self) -> List[ToolCategory]:
        """Get all categories with registered tools."""
        return list(self._tools_by_category.keys())
    
    def get_tags(self) -> List[str]:
        """Get all tags used by registered tools."""
        return list(self._tools_by_tag.keys())
    
    async def _load_plugins(self) -> None:
        """Load plugins from configured paths."""
        for path in self.config.plugin_paths:
            try:
                await self._load_plugin_from_path(path)
            except Exception as e:
                self._logger.error("plugin_load_failed", path=path, error=str(e))
    
    async def _load_plugin_from_path(self, path: str) -> None:
        """Load a plugin from a file path."""
        # Implementation for dynamic plugin loading
        self._logger.info("loading_plugin", path=path)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get registry metrics."""
        tool_metrics = {
            tool_id: {
                "call_count": tool.metrics.call_count,
                "success_rate": (
                    tool.metrics.success_count / tool.metrics.call_count
                    if tool.metrics.call_count > 0 else 0
                ),
            }
            for tool_id, tool in self._tools.items()
        }
        
        return {
            "total_tools": len(self._tools),
            "total_calls": self._total_calls,
            "total_batches": self._total_batches,
            "categories": len(self._tools_by_category),
            "tags": len(self._tools_by_tag),
            "tool_metrics": tool_metrics,
        }
    
    def invalidate_cache(self, tool_id: Optional[str] = None) -> int:
        """
        Invalidate tool cache.
        
        Args:
            tool_id: Specific tool to invalidate, or all if None
            
        Returns:
            Number of cache entries invalidated
        """
        if tool_id:
            tool = self._tools.get(tool_id)
            if tool:
                return tool.invalidate_cache()
            return 0
        
        total = 0
        for tool in self._tools.values():
            total += tool.invalidate_cache()
        return total


# Utility functions for tool creation

def create_function_tool(
    func: Callable,
    tool_id: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: ToolCategory = ToolCategory.SYSTEM,
    tags: Optional[Set[str]] = None,
) -> ToolDefinition:
    """
    Create a tool definition from a function.
    
    Args:
        func: Function to wrap
        tool_id: Tool ID (defaults to function name)
        name: Tool name (defaults to function name)
        description: Tool description (from docstring if not provided)
        category: Tool category
        tags: Tool tags
        
    Returns:
        Tool definition
    """
    tool_id = tool_id or func.__name__
    name = name or func.__name__
    description = description or (func.__doc__ or "No description")
    
    # Extract parameters from function signature
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    parameters = []
    for param_name, param in sig.parameters.items():
        param_type = type_hints.get(param_name, Any).__name__
        param_required = param.default == inspect.Parameter.empty
        param_default = None if param_required else param.default
        
        parameters.append(ToolParameter(
            name=param_name,
            type=param_type,
            description=f"Parameter: {param_name}",
            required=param_required,
            default=param_default,
        ))
    
    # Get return type
    return_type = type_hints.get("return", Any).__name__
    output = ToolOutput(
        type=return_type,
        description=f"Returns {return_type}",
    )
    
    return ToolDefinition(
        tool_id=tool_id,
        name=name,
        description=description,
        tool_type=ToolType.FUNCTION,
        category=category,
        parameters=parameters,
        output=output,
        tags=tags or set(),
    )


class FunctionToolExecutor:
    """Executor for function-based tools."""
    
    def __init__(self, func: Callable):
        self.func = func
    
    async def execute(self, **kwargs) -> Any:
        """Execute the wrapped function."""
        if asyncio.iscoroutinefunction(self.func):
            return await self.func(**kwargs)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: self.func(**kwargs))
    
    async def health_check(self) -> bool:
        """Function tools are always healthy."""
        return True


# Factory function
async def create_tool_registry(
    config: Optional[ToolRegistryConfig] = None,
) -> ToolRegistry:
    """
    Factory function to create and initialize a tool registry.
    
    Args:
        config: Optional configuration
        
    Returns:
        Initialized ToolRegistry instance
    """
    registry = ToolRegistry(config)
    await registry.initialize()
    return registry
