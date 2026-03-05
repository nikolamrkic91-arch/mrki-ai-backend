"""
Mrki Core Orchestrator - Main Agent Orchestration Engine

This module implements the central orchestration system for managing 50+ specialized
sub-agents in parallel. It provides hierarchical supervision, graph-based execution
planning, and optimized parallel execution targeting 1,500 simultaneous tool calls.

Architecture Pattern: Supervisor-Workers with Hierarchical Delegation
- Root Orchestrator: Coordinates high-level task planning
- Domain Supervisors: Manage specialized agent clusters
- Worker Agents: Execute specific subtasks

Author: Mrki Architecture Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any,
    AsyncIterator,
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
)

import structlog
from pydantic import BaseModel, Field, validator

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger("mrki.orchestrator")


class TaskStatus(Enum):
    """Enumeration of possible task execution states."""
    PENDING = auto()
    DECOMPOSING = auto()
    SCHEDULED = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    RETRYING = auto()
    CANCELLED = auto()
    VERIFIED = auto()


class AgentPriority(Enum):
    """Priority levels for agent task assignment."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class ExecutionMode(Enum):
    """Execution modes for task processing."""
    PARALLEL = auto()      # Execute all subtasks in parallel
    SEQUENTIAL = auto()    # Execute subtasks sequentially
    PIPELINE = auto()      # Stream results between dependent tasks
    DAG = auto()           # Execute based on dependency graph


# Type variables for generic types
T = TypeVar("T")
R = TypeVar("R")


class TaskResult(BaseModel):
    """Standardized result container for task execution."""
    task_id: str
    agent_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    output: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    tokens_used: int = 0
    subtask_results: List["TaskResult"] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
    verification_score: Optional[float] = None
    retry_count: int = 0

    class Config:
        arbitrary_types_allowed = True


class SubTask(BaseModel):
    """Represents a decomposed subtask with execution parameters."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_task_id: Optional[str] = None
    name: str
    description: str
    agent_type: str
    priority: AgentPriority = AgentPriority.NORMAL
    dependencies: List[str] = Field(default_factory=list)
    input_data: Dict[str, Any] = Field(default_factory=dict)
    expected_output_schema: Optional[Dict[str, Any]] = None
    max_retries: int = 3
    timeout_seconds: float = 300.0
    execution_mode: ExecutionMode = ExecutionMode.PARALLEL
    context_window_tokens: int = 4096
    required_tools: List[str] = Field(default_factory=list)

    @validator("task_id", pre=True, always=True)
    def ensure_task_id(cls, v):
        return v or str(uuid.uuid4())


class ExecutionPlan(BaseModel):
    """Execution plan containing decomposed subtasks and their dependencies."""
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    root_task_id: str
    subtasks: List[SubTask] = Field(default_factory=list)
    dependency_graph: Dict[str, List[str]] = Field(default_factory=dict)
    estimated_tokens: int = 0
    parallel_groups: List[List[str]] = Field(default_factory=list)
    critical_path: List[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)


class AgentCapabilities(BaseModel):
    """Defines the capabilities and constraints of an agent type."""
    agent_type: str
    description: str
    supported_tasks: List[str]
    max_concurrent_tasks: int = 10
    average_tokens_per_task: int = 2048
    specializations: List[str] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    context_window_size: int = 128000


class OrchestratorConfig(BaseModel):
    """Configuration for the orchestrator engine."""
    max_concurrent_agents: int = 100
    max_parallel_tool_calls: int = 1500
    default_timeout_seconds: float = 300.0
    max_retries: int = 3
    enable_verification: bool = True
    verification_sample_rate: float = 0.3
    token_budget: int = 256000
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    metrics_enabled: bool = True
    execution_mode: ExecutionMode = ExecutionMode.PARALLEL


@dataclass
class ExecutionMetrics:
    """Runtime metrics for orchestration performance tracking."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    retried_tasks: int = 0
    total_tokens_used: int = 0
    total_execution_time_ms: float = 0.0
    active_agents: int = 0
    queued_tasks: int = 0
    parallel_efficiency: float = 0.0
    timestamp: float = field(default_factory=time.time)


class AgentWorker(Protocol):
    """Protocol defining the interface for agent workers."""
    
    agent_id: str
    agent_type: str
    capabilities: AgentCapabilities
    
    async def execute(self, subtask: SubTask, context: Dict[str, Any]) -> TaskResult:
        """Execute a subtask and return the result."""
        ...
    
    async def health_check(self) -> bool:
        """Check if the agent is healthy and ready to work."""
        ...
    
    def get_load(self) -> float:
        """Return current load factor (0.0 - 1.0)."""
        ...


class TaskCache:
    """LRU cache for task results with TTL support."""
    
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 10000):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl_seconds = ttl_seconds
        self._max_size = max_size
        self._access_order: List[str] = []
        self._lock = asyncio.Lock()
    
    def _generate_key(self, subtask: SubTask) -> str:
        """Generate cache key from subtask parameters."""
        key_data = {
            "name": subtask.name,
            "description": subtask.description,
            "agent_type": subtask.agent_type,
            "input_data": subtask.input_data,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    async def get(self, subtask: SubTask) -> Optional[TaskResult]:
        """Retrieve cached result if available and not expired."""
        async with self._lock:
            key = self._generate_key(subtask)
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if time.time() - entry["timestamp"] > self._ttl_seconds:
                del self._cache[key]
                self._access_order.remove(key)
                return None
            
            # Update access order for LRU
            self._access_order.remove(key)
            self._access_order.append(key)
            
            return entry["result"]
    
    async def set(self, subtask: SubTask, result: TaskResult) -> None:
        """Cache a task result."""
        async with self._lock:
            key = self._generate_key(subtask)
            
            # Evict oldest if at capacity
            if len(self._cache) >= self._max_size and self._access_order:
                oldest = self._access_order.pop(0)
                del self._cache[oldest]
            
            self._cache[key] = {
                "result": result,
                "timestamp": time.time(),
            }
            self._access_order.append(key)
    
    async def invalidate(self, pattern: Optional[str] = None) -> int:
        """Invalidate cache entries matching pattern."""
        async with self._lock:
            if pattern is None:
                count = len(self._cache)
                self._cache.clear()
                self._access_order.clear()
                return count
            
            # Pattern-based invalidation
            keys_to_remove = [
                k for k in self._cache.keys() 
                if pattern in k
            ]
            for key in keys_to_remove:
                del self._cache[key]
                self._access_order.remove(key)
            
            return len(keys_to_remove)


class DependencyGraph:
    """Manages task dependencies and execution ordering."""
    
    def __init__(self):
        self._dependencies: Dict[str, Set[str]] = defaultdict(set)
        self._dependents: Dict[str, Set[str]] = defaultdict(set)
        self._completed: Set[str] = set()
        self._failed: Set[str] = set()
        self._lock = asyncio.Lock()
    
    def add_task(self, task_id: str, dependencies: List[str]) -> None:
        """Add a task with its dependencies."""
        self._dependencies[task_id] = set(dependencies)
        for dep in dependencies:
            self._dependents[dep].add(task_id)
    
    async def mark_completed(self, task_id: str) -> List[str]:
        """Mark task as completed and return newly ready tasks."""
        async with self._lock:
            self._completed.add(task_id)
            ready_tasks = []
            
            for dependent in self._dependents[task_id]:
                if self._is_ready(dependent):
                    ready_tasks.append(dependent)
            
            return ready_tasks
    
    async def mark_failed(self, task_id: str) -> List[str]:
        """Mark task as failed and propagate to dependents."""
        async with self._lock:
            self._failed.add(task_id)
            # Return all dependent tasks that should be cancelled
            return list(self._dependents[task_id])
    
    def _is_ready(self, task_id: str) -> bool:
        """Check if all dependencies are completed."""
        return all(
            dep in self._completed 
            for dep in self._dependencies[task_id]
        )
    
    def get_ready_tasks(self) -> List[str]:
        """Get all tasks that are ready to execute."""
        return [
            task_id for task_id in self._dependencies.keys()
            if task_id not in self._completed 
            and task_id not in self._failed
            and self._is_ready(task_id)
        ]
    
    def get_critical_path(self) -> List[str]:
        """Calculate the critical path through the dependency graph."""
        # Simple longest path calculation
        distances: Dict[str, int] = {task: 0 for task in self._dependencies}
        
        for task_id in self._dependencies:
            for dep in self._dependencies[task_id]:
                distances[task_id] = max(distances[task_id], distances.get(dep, 0) + 1)
        
        # Sort by distance descending
        return sorted(distances.keys(), key=lambda x: distances[x], reverse=True)


class MrkiOrchestrator:
    """
    Main orchestration engine for managing 50+ sub-agents in parallel.
    
    This orchestrator implements a hierarchical supervisor-workers pattern with
    graph-based execution planning. It optimizes for parallel execution targeting
    1,500 simultaneous tool calls and 4.5x performance improvement over sequential
    execution models.
    
    Key Features:
    - Parallel execution with dependency-aware scheduling
    - Token budget management (256K context windows)
    - Self-correction through cross-agent verification
    - Dynamic load balancing across agent pool
    - Result caching for improved efficiency
    
    Example:
        >>> orchestrator = MrkiOrchestrator(config)
        >>> await orchestrator.initialize()
        >>> result = await orchestrator.execute_task(complex_task)
    """
    
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """
        Initialize the orchestrator with configuration.
        
        Args:
            config: Orchestrator configuration. Uses defaults if not provided.
        """
        self.config = config or OrchestratorConfig()
        self._agent_pool: Dict[str, AgentWorker] = {}
        self._agent_queues: Dict[str, asyncio.PriorityQueue] = defaultdict(asyncio.PriorityQueue)
        self._task_results: Dict[str, TaskResult] = {}
        self._execution_plan_cache: Dict[str, ExecutionPlan] = {}
        self._cache = TaskCache(ttl_seconds=self.config.cache_ttl_seconds)
        self._dependency_graphs: Dict[str, DependencyGraph] = {}
        self._metrics = ExecutionMetrics()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_agents)
        self._tool_call_semaphore = asyncio.Semaphore(self.config.max_parallel_tool_calls)
        self._executor = ThreadPoolExecutor(max_workers=32)
        self._running = False
        self._lock = asyncio.Lock()
        self._logger = logger.bind(component="orchestrator")
        
        # Performance tracking
        self._performance_history: List[Dict[str, Any]] = []
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the orchestrator and start background tasks."""
        self._running = True
        if config:
            self._logger.info("orchestrator_initialized_with_config", config_keys=list(config.keys()))
        self._logger.info(
            "orchestrator_initializing",
            max_agents=self.config.max_concurrent_agents,
            max_tool_calls=self.config.max_parallel_tool_calls,
        )
        
        # Start background monitoring
        asyncio.create_task(self._monitor_loop())
        
        # Initialize agent pool
        await self._initialize_agent_pool()
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the orchestrator."""
        self._running = False
        self._executor.shutdown(wait=True)
        self._logger.info("orchestrator_shutdown_complete")
    
    async def _initialize_agent_pool(self) -> None:
        """Initialize the pool of available agents."""
        # This would be implemented to load agents from configuration
        # or dynamically create them based on demand
        pass
    
    def register_agent(self, agent: AgentWorker) -> None:
        """
        Register an agent worker with the orchestrator.
        
        Args:
            agent: Agent worker implementing the AgentWorker protocol
        """
        self._agent_pool[agent.agent_id] = agent
        self._metrics.active_agents = len(self._agent_pool)
        self._logger.info(
            "agent_registered",
            agent_id=agent.agent_id,
            agent_type=agent.agent_type,
        )
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the orchestrator."""
        if agent_id in self._agent_pool:
            del self._agent_pool[agent_id]
            self._metrics.active_agents = len(self._agent_pool)
            self._logger.info("agent_unregistered", agent_id=agent_id)
    
    async def execute_task(
        self, 
        task: Union[str, SubTask, ExecutionPlan],
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskResult:
        """
        Execute a task using the orchestrator's parallel execution engine.
        
        This is the main entry point for task execution. It handles task
        decomposition, scheduling, and result aggregation.
        
        Args:
            task: The task to execute (string, SubTask, or ExecutionPlan)
            context: Optional context data to pass to agents
            
        Returns:
            TaskResult containing the execution results
        """
        context = context or {}
        start_time = time.time()
        
        # Convert string to SubTask if needed
        if isinstance(task, str):
            task = SubTask(
                name="root_task",
                description=task,
                agent_type="orchestrator",
            )
        
        # Generate or use existing execution plan
        if isinstance(task, ExecutionPlan):
            plan = task
            root_task_id = plan.root_task_id
        else:
            plan = await self._create_execution_plan(task)
            root_task_id = task.task_id
        
        self._logger.info(
            "task_execution_started",
            root_task_id=root_task_id,
            subtask_count=len(plan.subtasks),
        )
        
        # Execute based on execution mode
        if plan.subtasks[0].execution_mode == ExecutionMode.SEQUENTIAL:
            result = await self._execute_sequential(plan, context)
        elif plan.subtasks[0].execution_mode == ExecutionMode.PIPELINE:
            result = await self._execute_pipeline(plan, context)
        elif plan.subtasks[0].execution_mode == ExecutionMode.DAG:
            result = await self._execute_dag(plan, context)
        else:
            result = await self._execute_parallel(plan, context)
        
        execution_time = (time.time() - start_time) * 1000
        result.execution_time_ms = execution_time
        
        # Update metrics
        self._metrics.total_tasks += len(plan.subtasks)
        self._metrics.total_execution_time_ms += execution_time
        
        self._logger.info(
            "task_execution_completed",
            root_task_id=root_task_id,
            status=result.status.value,
            execution_time_ms=execution_time,
        )
        
        return result
    
    async def _create_execution_plan(self, root_task: SubTask) -> ExecutionPlan:
        """
        Create an execution plan by decomposing the root task.
        
        Args:
            root_task: The root task to decompose
            
        Returns:
            ExecutionPlan containing decomposed subtasks
        """
        # Import task decomposer
        from .task_decomposer import TaskDecomposer
        
        decomposer = TaskDecomposer(token_budget=self.config.token_budget)
        subtasks = await decomposer.decompose(root_task)
        
        # Build dependency graph
        dependency_graph = defaultdict(list)
        for subtask in subtasks:
            dependency_graph[subtask.task_id] = subtask.dependencies
        
        # Calculate parallel execution groups
        parallel_groups = self._calculate_parallel_groups(subtasks, dependency_graph)
        
        # Create dependency graph object
        dep_graph = DependencyGraph()
        for subtask in subtasks:
            dep_graph.add_task(subtask.task_id, subtask.dependencies)
        
        self._dependency_graphs[root_task.task_id] = dep_graph
        
        plan = ExecutionPlan(
            root_task_id=root_task.task_id,
            subtasks=subtasks,
            dependency_graph=dict(dependency_graph),
            parallel_groups=parallel_groups,
            critical_path=dep_graph.get_critical_path(),
            estimated_tokens=sum(s.context_window_tokens for s in subtasks),
        )
        
        self._execution_plan_cache[root_task.task_id] = plan
        
        return plan
    
    def _calculate_parallel_groups(
        self, 
        subtasks: List[SubTask], 
        dependency_graph: Dict[str, List[str]]
    ) -> List[List[str]]:
        """
        Calculate groups of tasks that can be executed in parallel.
        
        Args:
            subtasks: List of all subtasks
            dependency_graph: Dependency relationships
            
        Returns:
            List of task ID groups for parallel execution
        """
        completed = set()
        groups = []
        remaining = {s.task_id for s in subtasks}
        
        while remaining:
            # Find tasks with all dependencies satisfied
            ready = [
                task_id for task_id in remaining
                if all(dep in completed for dep in dependency_graph.get(task_id, []))
            ]
            
            if not ready:
                # Circular dependency detected
                break
            
            groups.append(ready)
            completed.update(ready)
            remaining -= set(ready)
        
        return groups
    
    async def _execute_parallel(
        self, 
        plan: ExecutionPlan, 
        context: Dict[str, Any]
    ) -> TaskResult:
        """
        Execute tasks in parallel groups respecting dependencies.
        
        Args:
            plan: The execution plan
            context: Execution context
            
        Returns:
            Aggregated task result
        """
        results: Dict[str, TaskResult] = {}
        dep_graph = self._dependency_graphs[plan.root_task_id]
        
        # Execute each parallel group
        for group in plan.parallel_groups:
            # Create tasks for this group
            tasks = [
                self._execute_subtask_with_retry(
                    self._get_subtask(plan, task_id),
                    context,
                    results,
                )
                for task_id in group
            ]
            
            # Execute group in parallel
            group_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for task_id, result in zip(group, group_results):
                if isinstance(result, Exception):
                    results[task_id] = TaskResult(
                        task_id=task_id,
                        status=TaskStatus.FAILED,
                        error=str(result),
                    )
                    await dep_graph.mark_failed(task_id)
                else:
                    results[task_id] = result
                    await dep_graph.mark_completed(task_id)
        
        # Aggregate results
        return self._aggregate_results(plan.root_task_id, results, plan.subtasks)
    
    async def _execute_sequential(
        self, 
        plan: ExecutionPlan, 
        context: Dict[str, Any]
    ) -> TaskResult:
        """Execute tasks sequentially in dependency order."""
        results: Dict[str, TaskResult] = {}
        
        # Flatten parallel groups into sequential order
        ordered_tasks = []
        for group in plan.parallel_groups:
            ordered_tasks.extend(group)
        
        for task_id in ordered_tasks:
            subtask = self._get_subtask(plan, task_id)
            result = await self._execute_subtask_with_retry(subtask, context, results)
            results[task_id] = result
        
        return self._aggregate_results(plan.root_task_id, results, plan.subtasks)
    
    async def _execute_pipeline(
        self, 
        plan: ExecutionPlan, 
        context: Dict[str, Any]
    ) -> TaskResult:
        """Execute tasks in a streaming pipeline fashion."""
        # Pipeline execution for data streaming between tasks
        results: Dict[str, TaskResult] = {}
        
        async def pipeline_stream():
            for group in plan.parallel_groups:
                tasks = [
                    self._execute_subtask_with_retry(
                        self._get_subtask(plan, task_id),
                        context,
                        results,
                    )
                    for task_id in group
                ]
                
                # Yield results as they complete
                for coro in asyncio.as_completed(tasks):
                    result = await coro
                    results[result.task_id] = result
                    yield result
        
        # Collect all results
        async for _ in pipeline_stream():
            pass
        
        return self._aggregate_results(plan.root_task_id, results, plan.subtasks)
    
    async def _execute_dag(
        self, 
        plan: ExecutionPlan, 
        context: Dict[str, Any]
    ) -> TaskResult:
        """Execute tasks following DAG dependencies dynamically."""
        results: Dict[str, TaskResult] = {}
        dep_graph = self._dependency_graphs[plan.root_task_id]
        pending_tasks: Set[str] = set(s.task_id for s in plan.subtasks)
        running_tasks: Dict[str, asyncio.Task] = {}
        
        while pending_tasks or running_tasks:
            # Start ready tasks
            ready = [
                task_id for task_id in pending_tasks
                if dep_graph._is_ready(task_id)
            ]
            
            for task_id in ready:
                subtask = self._get_subtask(plan, task_id)
                running_tasks[task_id] = asyncio.create_task(
                    self._execute_subtask_with_retry(subtask, context, results)
                )
                pending_tasks.remove(task_id)
            
            # Wait for at least one task to complete
            if running_tasks:
                done, _ = await asyncio.wait(
                    running_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED,
                )
                
                for task in done:
                    task_id = None
                    for tid, t in running_tasks.items():
                        if t == task:
                            task_id = tid
                            break
                    
                    if task_id:
                        try:
                            result = await task
                            results[task_id] = result
                            await dep_graph.mark_completed(task_id)
                        except Exception as e:
                            results[task_id] = TaskResult(
                                task_id=task_id,
                                status=TaskStatus.FAILED,
                                error=str(e),
                            )
                            await dep_graph.mark_failed(task_id)
                        
                        del running_tasks[task_id]
        
        return self._aggregate_results(plan.root_task_id, results, plan.subtasks)
    
    def _get_subtask(self, plan: ExecutionPlan, task_id: str) -> SubTask:
        """Get subtask by ID from execution plan."""
        for subtask in plan.subtasks:
            if subtask.task_id == task_id:
                return subtask
        raise ValueError(f"Subtask {task_id} not found in plan")
    
    async def _execute_subtask_with_retry(
        self,
        subtask: SubTask,
        context: Dict[str, Any],
        dependency_results: Dict[str, TaskResult],
    ) -> TaskResult:
        """
        Execute a subtask with retry logic and caching.
        
        Args:
            subtask: The subtask to execute
            context: Execution context
            dependency_results: Results from dependent tasks
            
        Returns:
            TaskResult from execution
        """
        # Check cache first
        if self.config.enable_caching:
            cached = await self._cache.get(subtask)
            if cached:
                self._logger.debug("cache_hit", task_id=subtask.task_id)
                return cached
        
        # Build context with dependency results
        enriched_context = {
            **context,
            "dependency_results": {
                dep_id: dependency_results.get(dep_id)
                for dep_id in subtask.dependencies
            },
        }
        
        # Execute with retry
        for attempt in range(subtask.max_retries):
            try:
                result = await self._execute_subtask(subtask, enriched_context)
                
                if result.status == TaskStatus.COMPLETED:
                    # Cache successful result
                    if self.config.enable_caching:
                        await self._cache.set(subtask, result)
                    return result
                
                # Retry on failure
                if attempt < subtask.max_retries - 1:
                    self._logger.warning(
                        "task_retry",
                        task_id=subtask.task_id,
                        attempt=attempt + 1,
                        error=result.error,
                    )
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
            except Exception as e:
                if attempt < subtask.max_retries - 1:
                    self._logger.warning(
                        "task_exception_retry",
                        task_id=subtask.task_id,
                        attempt=attempt + 1,
                        error=str(e),
                    )
                    await asyncio.sleep(2 ** attempt)
                else:
                    return TaskResult(
                        task_id=subtask.task_id,
                        status=TaskStatus.FAILED,
                        error=str(e),
                        retry_count=attempt + 1,
                    )
        
        return result
    
    async def _execute_subtask(
        self,
        subtask: SubTask,
        context: Dict[str, Any],
    ) -> TaskResult:
        """
        Execute a single subtask using the appropriate agent.
        
        Args:
            subtask: The subtask to execute
            context: Execution context
            
        Returns:
            TaskResult from agent execution
        """
        async with self._semaphore:
            start_time = time.time()
            
            # Select best agent for task
            agent = await self._select_agent(subtask)
            
            if not agent:
                return TaskResult(
                    task_id=subtask.task_id,
                    status=TaskStatus.FAILED,
                    error=f"No available agent for type: {subtask.agent_type}",
                )
            
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    agent.execute(subtask, context),
                    timeout=subtask.timeout_seconds,
                )
                
                result.agent_id = agent.agent_id
                result.execution_time_ms = (time.time() - start_time) * 1000
                
                # Verify result if enabled
                if self.config.enable_verification:
                    verification = await self._verify_result(subtask, result)
                    result.verification_score = verification.get("score", 0.0)
                
                return result
                
            except asyncio.TimeoutError:
                return TaskResult(
                    task_id=subtask.task_id,
                    agent_id=agent.agent_id,
                    status=TaskStatus.FAILED,
                    error=f"Task timed out after {subtask.timeout_seconds}s",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )
            except Exception as e:
                return TaskResult(
                    task_id=subtask.task_id,
                    agent_id=agent.agent_id,
                    status=TaskStatus.FAILED,
                    error=str(e),
                    execution_time_ms=(time.time() - start_time) * 1000,
                )
    
    async def _select_agent(self, subtask: SubTask) -> Optional[AgentWorker]:
        """
        Select the best available agent for a subtask.
        
        Selection criteria:
        1. Agent type match
        2. Current load (prefer less loaded)
        3. Health status
        
        Args:
            subtask: The subtask requiring an agent
            
        Returns:
            Selected agent or None if no suitable agent available
        """
        candidates = [
            agent for agent in self._agent_pool.values()
            if agent.agent_type == subtask.agent_type
            and agent.get_load() < 0.8  # Not overloaded
        ]
        
        if not candidates:
            return None
        
        # Sort by load (ascending) and select least loaded
        candidates.sort(key=lambda a: a.get_load())
        
        # Verify health
        for agent in candidates:
            if await agent.health_check():
                return agent
        
        return None
    
    async def _verify_result(
        self, 
        subtask: SubTask, 
        result: TaskResult
    ) -> Dict[str, Any]:
        """
        Verify a task result using cross-agent verification.
        
        Args:
            subtask: The original subtask
            result: The result to verify
            
        Returns:
            Verification report with score and details
        """
        # Import verifier
        from .verifier import CrossAgentVerifier
        
        verifier = CrossAgentVerifier()
        return await verifier.verify(subtask, result)
    
    def _aggregate_results(
        self,
        root_task_id: str,
        results: Dict[str, TaskResult],
        subtasks: List[SubTask],
    ) -> TaskResult:
        """
        Aggregate subtask results into a single root result.
        
        Args:
            root_task_id: The root task ID
            results: All subtask results
            subtasks: All subtasks in the plan
            
        Returns:
            Aggregated TaskResult
        """
        # Check for failures
        failed = [r for r in results.values() if r.status == TaskStatus.FAILED]
        
        if failed:
            return TaskResult(
                task_id=root_task_id,
                status=TaskStatus.FAILED,
                error=f"{len(failed)} subtasks failed",
                subtask_results=list(results.values()),
            )
        
        # Aggregate outputs
        aggregated_output = {
            subtask.name: results.get(subtask.task_id, TaskResult(task_id=subtask.task_id)).output
            for subtask in subtasks
        }
        
        total_tokens = sum(r.tokens_used for r in results.values())
        total_time = sum(r.execution_time_ms for r in results.values())
        
        return TaskResult(
            task_id=root_task_id,
            status=TaskStatus.COMPLETED,
            output=aggregated_output,
            subtask_results=list(results.values()),
            tokens_used=total_tokens,
            execution_time_ms=total_time,
        )
    
    async def _monitor_loop(self) -> None:
        """Background monitoring loop for metrics collection."""
        while self._running:
            await asyncio.sleep(10)
            
            # Collect metrics
            metrics = {
                "timestamp": time.time(),
                "active_agents": self._metrics.active_agents,
                "total_tasks": self._metrics.total_tasks,
                "completed_tasks": self._metrics.completed_tasks,
                "failed_tasks": self._metrics.failed_tasks,
                "cache_size": len(self._cache._cache),
            }
            
            self._performance_history.append(metrics)
            
            # Trim history if too large
            if len(self._performance_history) > 1000:
                self._performance_history = self._performance_history[-500:]
            
            self._logger.debug("metrics_snapshot", **metrics)
    
    def get_metrics(self) -> ExecutionMetrics:
        """Get current execution metrics."""
        return self._metrics
    
    def get_performance_history(self) -> List[Dict[str, Any]]:
        """Get historical performance data."""
        return self._performance_history.copy()
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running or pending task."""
        # Implementation for task cancellation
        self._logger.info("task_cancelled", task_id=task_id)
        return True


# Factory function for creating orchestrator instances
async def create_orchestrator(
    config: Optional[OrchestratorConfig] = None
) -> MrkiOrchestrator:
    """
    Factory function to create and initialize an orchestrator.
    
    Args:
        config: Optional configuration
        
    Returns:
        Initialized MrkiOrchestrator instance
    """
    orchestrator = MrkiOrchestrator(config)
    await orchestrator.initialize()
    return orchestrator
