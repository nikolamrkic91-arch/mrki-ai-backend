"""
Mrki Agent Pool - Agent Lifecycle Management System

This module implements comprehensive agent lifecycle management including:
- Dynamic agent creation, scaling, and destruction
- Health monitoring and self-healing
- Load balancing across agent clusters
- Resource allocation and token budget management
- Agent specialization and capability tracking

Architecture:
- AgentPool: Central manager for all agent instances
- AgentInstance: Individual agent wrapper with lifecycle state
- AgentFactory: Creates agents based on type specifications
- HealthMonitor: Continuous health checks and recovery

Author: Mrki Architecture Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import time
import uuid
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
)

import structlog
from pydantic import BaseModel, Field

from .orchestrator import (
    AgentCapabilities,
    AgentPriority,
    AgentWorker,
    SubTask,
    TaskResult,
    TaskStatus,
)

logger = structlog.get_logger("mrki.agent_pool")


class AgentState(Enum):
    """Lifecycle states for agent instances."""
    INITIALIZING = auto()   # Agent is being created
    IDLE = auto()           # Agent ready for work
    BUSY = auto()           # Agent executing task
    PAUSED = auto()         # Agent temporarily paused
    UNHEALTHY = auto()      # Agent failed health check
    RECOVERING = auto()     # Agent attempting recovery
    SHUTTING_DOWN = auto()  # Agent is being destroyed
    TERMINATED = auto()     # Agent destroyed


class ScalingPolicy(Enum):
    """Auto-scaling policies for agent pools."""
    STATIC = auto()         # Fixed number of agents
    DYNAMIC = auto()        # Scale based on queue depth
    PREDICTIVE = auto()     # Scale based on predicted load
    ADAPTIVE = auto()       # Machine learning-based scaling


@dataclass
class ResourceAllocation:
    """Resource allocation for an agent instance."""
    max_tokens: int = 128000
    current_tokens: int = 0
    max_concurrent_tasks: int = 5
    active_tasks: int = 0
    memory_mb: int = 512
    cpu_cores: float = 1.0


class AgentMetrics(BaseModel):
    """Metrics for an individual agent instance."""
    agent_id: str
    agent_type: str
    state: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time_ms: float = 0.0
    total_tokens_used: int = 0
    average_task_time_ms: float = 0.0
    current_load: float = 0.0
    last_health_check: float = 0.0
    health_check_failures: int = 0
    created_at: float = Field(default_factory=time.time)
    last_activity: float = Field(default_factory=time.time)


class PoolMetrics(BaseModel):
    """Aggregate metrics for the entire agent pool."""
    total_agents: int = 0
    idle_agents: int = 0
    busy_agents: int = 0
    unhealthy_agents: int = 0
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0
    average_load: float = 0.0
    queue_depth: int = 0
    scale_up_events: int = 0
    scale_down_events: int = 0
    timestamp: float = Field(default_factory=time.time)


class AgentConfig(BaseModel):
    """Configuration for agent instances."""
    agent_type: str
    capabilities: AgentCapabilities
    min_instances: int = 1
    max_instances: int = 50
    scaling_policy: ScalingPolicy = ScalingPolicy.DYNAMIC
    scale_up_threshold: float = 0.7  # Queue depth ratio to scale up
    scale_down_threshold: float = 0.2
    health_check_interval_seconds: float = 30.0
    idle_timeout_seconds: float = 300.0
    max_health_failures: int = 3
    recovery_attempts: int = 3


class AgentInstance:
    """
    Wrapper for individual agent instances with lifecycle management.
    
    Each AgentInstance wraps an actual agent worker and manages its
    state, health, and task execution. It provides:
    - State machine for lifecycle management
    - Health monitoring and self-healing
    - Resource tracking and limits
    - Metrics collection
    
    Example:
        >>> agent = AgentInstance(agent_worker, config)
        >>> await agent.initialize()
        >>> result = await agent.execute_task(subtask, context)
    """
    
    def __init__(
        self,
        worker: AgentWorker,
        config: AgentConfig,
    ):
        """
        Initialize agent instance.
        
        Args:
            worker: The underlying agent worker
            config: Configuration for this agent type
        """
        self.worker = worker
        self.config = config
        self.agent_id = worker.agent_id
        self.agent_type = worker.agent_type
        self.state = AgentState.INITIALIZING
        self.resources = ResourceAllocation(
            max_tokens=worker.capabilities.context_window_size,
            max_concurrent_tasks=worker.capabilities.max_concurrent_tasks,
        )
        self.metrics = AgentMetrics(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            state=self.state.name,
        )
        self._current_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        self._health_check_task: Optional[asyncio.Task] = None
        self._logger = logger.bind(agent_id=self.agent_id, agent_type=self.agent_type)
    
    async def initialize(self) -> bool:
        """
        Initialize the agent instance.
        
        Returns:
            True if initialization successful
        """
        try:
            self._logger.info("agent_initializing")
            
            # Perform health check
            if not await self.worker.health_check():
                self.state = AgentState.UNHEALTHY
                return False
            
            self.state = AgentState.IDLE
            self.metrics.state = self.state.name
            
            # Start health monitoring
            self._health_check_task = asyncio.create_task(self._health_monitor())
            
            self._logger.info("agent_initialized")
            return True
            
        except Exception as e:
            self._logger.error("agent_initialization_failed", error=str(e))
            self.state = AgentState.UNHEALTHY
            return False
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the agent instance."""
        self._logger.info("agent_shutting_down")
        self.state = AgentState.SHUTTING_DOWN
        
        # Cancel health check
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Wait for current tasks to complete
        if self._current_tasks:
            await asyncio.gather(*self._current_tasks.values(), return_exceptions=True)
        
        self.state = AgentState.TERMINATED
        self._logger.info("agent_terminated")
    
    async def execute_task(
        self,
        subtask: SubTask,
        context: Dict[str, Any],
    ) -> TaskResult:
        """
        Execute a task on this agent.
        
        Args:
            subtask: The subtask to execute
            context: Execution context
            
        Returns:
            TaskResult from execution
        """
        async with self._lock:
            if self.state not in (AgentState.IDLE, AgentState.BUSY):
                return TaskResult(
                    task_id=subtask.task_id,
                    status=TaskStatus.FAILED,
                    error=f"Agent not available (state: {self.state.name})",
                )
            
            # Check resource limits
            if self.resources.active_tasks >= self.resources.max_concurrent_tasks:
                return TaskResult(
                    task_id=subtask.task_id,
                    status=TaskStatus.FAILED,
                    error="Agent at maximum concurrent tasks",
                )
            
            # Update state
            self.state = AgentState.BUSY
            self.resources.active_tasks += 1
            self.metrics.current_load = self.resources.active_tasks / self.resources.max_concurrent_tasks
        
        start_time = time.time()
        
        try:
            # Execute task
            result = await self.worker.execute(subtask, context)
            
            # Update metrics
            execution_time = (time.time() - start_time) * 1000
            self.metrics.tasks_completed += 1
            self.metrics.total_execution_time_ms += execution_time
            self.metrics.total_tokens_used += result.tokens_used
            self.metrics.average_task_time_ms = (
                self.metrics.total_execution_time_ms / self.metrics.tasks_completed
            )
            
            if result.status == TaskStatus.FAILED:
                self.metrics.tasks_failed += 1
            
            return result
            
        except Exception as e:
            self.metrics.tasks_failed += 1
            return TaskResult(
                task_id=subtask.task_id,
                agent_id=self.agent_id,
                status=TaskStatus.FAILED,
                error=str(e),
            )
        
        finally:
            async with self._lock:
                self.resources.active_tasks -= 1
                self.metrics.current_load = self.resources.active_tasks / self.resources.max_concurrent_tasks
                self.metrics.last_activity = time.time()
                
                # Return to idle if no more tasks
                if self.resources.active_tasks == 0:
                    self.state = AgentState.IDLE
                
                self.metrics.state = self.state.name
    
    async def health_check(self) -> bool:
        """Perform health check on agent."""
        try:
            healthy = await self.worker.health_check()
            self.metrics.last_health_check = time.time()
            
            if not healthy:
                self.metrics.health_check_failures += 1
                if self.metrics.health_check_failures >= self.config.max_health_failures:
                    self.state = AgentState.UNHEALTHY
            else:
                self.metrics.health_check_failures = 0
            
            return healthy
            
        except Exception as e:
            self._logger.error("health_check_failed", error=str(e))
            self.metrics.health_check_failures += 1
            return False
    
    async def _health_monitor(self) -> None:
        """Background health monitoring loop."""
        while self.state not in (AgentState.SHUTTING_DOWN, AgentState.TERMINATED):
            try:
                await asyncio.sleep(self.config.health_check_interval_seconds)
                
                if self.state == AgentState.UNHEALTHY:
                    await self._attempt_recovery()
                else:
                    await self.health_check()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error("health_monitor_error", error=str(e))
    
    async def _attempt_recovery(self) -> bool:
        """Attempt to recover an unhealthy agent."""
        self._logger.info("attempting_recovery")
        self.state = AgentState.RECOVERING
        
        for attempt in range(self.config.recovery_attempts):
            try:
                if await self.worker.health_check():
                    self.state = AgentState.IDLE
                    self.metrics.health_check_failures = 0
                    self._logger.info("recovery_successful", attempt=attempt + 1)
                    return True
            except Exception as e:
                self._logger.warning("recovery_attempt_failed", attempt=attempt + 1, error=str(e))
            
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        self._logger.error("recovery_failed")
        return False
    
    def get_load(self) -> float:
        """Get current load factor (0.0 - 1.0)."""
        return self.metrics.current_load
    
    def is_available(self) -> bool:
        """Check if agent is available for new tasks."""
        return (
            self.state in (AgentState.IDLE, AgentState.BUSY)
            and self.resources.active_tasks < self.resources.max_concurrent_tasks
        )


class AgentFactory:
    """
    Factory for creating agent instances based on type specifications.
    
    The factory maintains a registry of agent constructors and creates
    instances on demand. It supports:
    - Dynamic agent type registration
    - Constructor dependency injection
    - Agent capability validation
    """
    
    def __init__(self):
        self._constructors: Dict[str, Callable[..., AgentWorker]] = {}
        self._capabilities: Dict[str, AgentCapabilities] = {}
        self._logger = logger.bind(component="agent_factory")
    
    def register_agent_type(
        self,
        agent_type: str,
        constructor: Callable[..., AgentWorker],
        capabilities: AgentCapabilities,
    ) -> None:
        """
        Register an agent type with its constructor.
        
        Args:
            agent_type: Unique identifier for agent type
            constructor: Callable that creates agent instances
            capabilities: Capabilities of this agent type
        """
        self._constructors[agent_type] = constructor
        self._capabilities[agent_type] = capabilities
        self._logger.info(
            "agent_type_registered",
            agent_type=agent_type,
            capabilities=capabilities.supported_tasks,
        )
    
    def unregister_agent_type(self, agent_type: str) -> None:
        """Unregister an agent type."""
        if agent_type in self._constructors:
            del self._constructors[agent_type]
            del self._capabilities[agent_type]
            self._logger.info("agent_type_unregistered", agent_type=agent_type)
    
    async def create_agent(
        self,
        agent_type: str,
        **kwargs,
    ) -> Optional[AgentInstance]:
        """
        Create an agent instance of the specified type.
        
        Args:
            agent_type: Type of agent to create
            **kwargs: Additional arguments for constructor
            
        Returns:
            AgentInstance or None if creation failed
        """
        if agent_type not in self._constructors:
            self._logger.error("unknown_agent_type", agent_type=agent_type)
            return None
        
        try:
            # Create worker
            worker = self._constructors[agent_type](**kwargs)
            
            # Create config
            config = AgentConfig(
                agent_type=agent_type,
                capabilities=self._capabilities[agent_type],
            )
            
            # Create instance
            instance = AgentInstance(worker, config)
            
            # Initialize
            if await instance.initialize():
                return instance
            else:
                self._logger.error("agent_initialization_failed", agent_type=agent_type)
                return None
                
        except Exception as e:
            self._logger.error("agent_creation_failed", agent_type=agent_type, error=str(e))
            return None
    
    def get_capabilities(self, agent_type: str) -> Optional[AgentCapabilities]:
        """Get capabilities for an agent type."""
        return self._capabilities.get(agent_type)
    
    def list_agent_types(self) -> List[str]:
        """List all registered agent types."""
        return list(self._constructors.keys())


class AgentPool:
    """
    Central manager for all agent instances in the system.
    
    The AgentPool manages the lifecycle of 50+ agent instances including:
    - Dynamic scaling based on demand
    - Load balancing across agents
    - Health monitoring and recovery
    - Resource allocation and limits
    - Queue management for pending tasks
    
    Scaling Strategies:
    - STATIC: Fixed pool size
    - DYNAMIC: Scale based on queue depth
    - PREDICTIVE: Use historical patterns
    - ADAPTIVE: ML-based prediction
    
    Example:
        >>> pool = AgentPool(factory)
        >>> await pool.initialize()
        >>> agent = await pool.acquire_agent("code_generator")
        >>> result = await agent.execute_task(subtask, context)
        >>> await pool.release_agent(agent)
    """
    
    def __init__(
        self,
        factory: AgentFactory,
        default_config: Optional[AgentConfig] = None,
    ):
        """
        Initialize the agent pool.
        
        Args:
            factory: Agent factory for creating instances
            default_config: Default configuration for agent types
        """
        self.factory = factory
        self.default_config = default_config or AgentConfig(
            agent_type="default",
            capabilities=AgentCapabilities(
                agent_type="default",
                description="Default agent",
                supported_tasks=["*"],
            ),
        )
        
        # Agent storage by type
        self._agents: Dict[str, List[AgentInstance]] = defaultdict(list)
        self._all_agents: Dict[str, AgentInstance] = {}
        
        # Task queues by agent type
        self._queues: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        
        # Configuration by agent type
        self._configs: Dict[str, AgentConfig] = {}
        
        # Metrics
        self._metrics = PoolMetrics()
        self._metrics_history: List[PoolMetrics] = []
        
        # Scaling control
        self._scaling_lock = asyncio.Lock()
        self._last_scale_up: Dict[str, float] = defaultdict(float)
        self._last_scale_down: Dict[str, float] = defaultdict(float)
        
        # Control
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._logger = logger.bind(component="agent_pool")
    
    async def initialize(self) -> None:
        """Initialize the agent pool and start monitoring."""
        self._running = True
        self._logger.info("agent_pool_initializing")
        
        # Start monitoring loop
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
        self._logger.info("agent_pool_initialized")
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the agent pool."""
        self._logger.info("agent_pool_shutting_down")
        self._running = False
        
        # Stop monitor
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown all agents
        shutdown_tasks = [
            agent.shutdown() for agent in self._all_agents.values()
        ]
        await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        
        self._logger.info("agent_pool_shutdown_complete")
    
    def register_agent_type(
        self,
        agent_type: str,
        config: Optional[AgentConfig] = None,
    ) -> None:
        """
        Register an agent type with its configuration.
        
        Args:
            agent_type: Type identifier
            config: Configuration for this type
        """
        if config is None:
            capabilities = self.factory.get_capabilities(agent_type)
            if capabilities:
                config = AgentConfig(agent_type=agent_type, capabilities=capabilities)
            else:
                config = self.default_config
        
        self._configs[agent_type] = config
        self._logger.info(
            "agent_type_configured",
            agent_type=agent_type,
            min_instances=config.min_instances,
            max_instances=config.max_instances,
        )
    
    async def scale_agents(self, agent_type: str, target_count: int) -> bool:
        """
        Scale agent instances to target count.
        
        Args:
            agent_type: Type of agent to scale
            target_count: Desired number of instances
            
        Returns:
            True if scaling successful
        """
        async with self._scaling_lock:
            config = self._configs.get(agent_type)
            if not config:
                self._logger.error("agent_type_not_configured", agent_type=agent_type)
                return False
            
            current_count = len(self._agents.get(agent_type, []))
            
            # Scale up
            if target_count > current_count:
                to_create = min(target_count - current_count, config.max_instances - current_count)
                
                for _ in range(to_create):
                    agent = await self.factory.create_agent(agent_type)
                    if agent:
                        self._agents[agent_type].append(agent)
                        self._all_agents[agent.agent_id] = agent
                
                self._metrics.scale_up_events += 1
                self._logger.info(
                    "agents_scaled_up",
                    agent_type=agent_type,
                    created=to_create,
                    total=len(self._agents[agent_type]),
                )
            
            # Scale down
            elif target_count < current_count:
                to_remove = current_count - max(target_count, config.min_instances)
                agents = self._agents.get(agent_type, [])
                
                # Remove idle agents first
                removable = [a for a in agents if a.state == AgentState.IDLE]
                
                for agent in removable[:to_remove]:
                    await agent.shutdown()
                    agents.remove(agent)
                    del self._all_agents[agent.agent_id]
                
                self._metrics.scale_down_events += 1
                self._logger.info(
                    "agents_scaled_down",
                    agent_type=agent_type,
                    removed=len(removable[:to_remove]),
                    total=len(agents),
                )
            
            return True
    
    async def acquire_agent(
        self,
        agent_type: str,
        timeout: Optional[float] = None,
    ) -> Optional[AgentInstance]:
        """
        Acquire an available agent of the specified type.
        
        Args:
            agent_type: Type of agent needed
            timeout: Maximum wait time
            
        Returns:
            Available agent or None
        """
        start_time = time.time()
        
        while timeout is None or (time.time() - start_time) < timeout:
            # Find available agent
            agents = self._agents.get(agent_type, [])
            available = [a for a in agents if a.is_available()]
            
            if available:
                # Sort by load and return least loaded
                available.sort(key=lambda a: a.get_load())
                return available[0]
            
            # Try to scale up if needed
            config = self._configs.get(agent_type)
            if config and len(agents) < config.max_instances:
                await self.scale_agents(agent_type, len(agents) + 1)
            
            await asyncio.sleep(0.1)
        
        return None
    
    async def release_agent(self, agent: AgentInstance) -> None:
        """
        Release an agent back to the pool.
        
        Args:
            agent: Agent to release
        """
        # Agent is automatically available when task completes
        pass
    
    async def execute_on_agent(
        self,
        agent_type: str,
        subtask: SubTask,
        context: Dict[str, Any],
    ) -> TaskResult:
        """
        Execute a task on an agent of the specified type.
        
        Args:
            agent_type: Type of agent needed
            subtask: Task to execute
            context: Execution context
            
        Returns:
            TaskResult from execution
        """
        agent = await self.acquire_agent(agent_type)
        
        if not agent:
            return TaskResult(
                task_id=subtask.task_id,
                status=TaskStatus.FAILED,
                error=f"No available agent of type: {agent_type}",
            )
        
        try:
            return await agent.execute_task(subtask, context)
        finally:
            await self.release_agent(agent)
    
    async def _monitor_loop(self) -> None:
        """Background monitoring and scaling loop."""
        while self._running:
            try:
                await asyncio.sleep(5)
                
                # Update metrics
                await self._update_metrics()
                
                # Auto-scale based on policy
                await self._auto_scale()
                
                # Cleanup idle agents
                await self._cleanup_idle()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error("monitor_loop_error", error=str(e))
    
    async def _update_metrics(self) -> None:
        """Update pool metrics."""
        total_agents = len(self._all_agents)
        idle_agents = sum(
            1 for a in self._all_agents.values() if a.state == AgentState.IDLE
        )
        busy_agents = sum(
            1 for a in self._all_agents.values() if a.state == AgentState.BUSY
        )
        unhealthy_agents = sum(
            1 for a in self._all_agents.values() 
            if a.state in (AgentState.UNHEALTHY, AgentState.RECOVERING)
        )
        
        total_tasks = sum(
            a.metrics.tasks_completed for a in self._all_agents.values()
        )
        failed_tasks = sum(
            a.metrics.tasks_failed for a in self._all_agents.values()
        )
        
        avg_load = (
            sum(a.get_load() for a in self._all_agents.values()) / total_agents
            if total_agents > 0 else 0.0
        )
        
        self._metrics = PoolMetrics(
            total_agents=total_agents,
            idle_agents=idle_agents,
            busy_agents=busy_agents,
            unhealthy_agents=unhealthy_agents,
            total_tasks_completed=total_tasks,
            total_tasks_failed=failed_tasks,
            average_load=avg_load,
            queue_depth=sum(q.qsize() for q in self._queues.values()),
            scale_up_events=self._metrics.scale_up_events,
            scale_down_events=self._metrics.scale_down_events,
        )
        
        self._metrics_history.append(self._metrics)
        
        # Trim history
        if len(self._metrics_history) > 1000:
            self._metrics_history = self._metrics_history[-500:]
    
    async def _auto_scale(self) -> None:
        """Auto-scale agents based on configured policy."""
        for agent_type, config in self._configs.items():
            agents = self._agents.get(agent_type, [])
            current_count = len(agents)
            queue_depth = self._queues[agent_type].qsize()
            
            if config.scaling_policy == ScalingPolicy.STATIC:
                continue  # No auto-scaling
            
            elif config.scaling_policy == ScalingPolicy.DYNAMIC:
                # Scale based on queue depth and agent availability
                available = sum(1 for a in agents if a.is_available())
                load_ratio = 1.0 - (available / max(current_count, 1))
                
                if load_ratio > config.scale_up_threshold and current_count < config.max_instances:
                    if time.time() - self._last_scale_up[agent_type] > 30:
                        await self.scale_agents(agent_type, current_count + 1)
                        self._last_scale_up[agent_type] = time.time()
                
                elif load_ratio < config.scale_down_threshold and current_count > config.min_instances:
                    if time.time() - self._last_scale_down[agent_type] > 60:
                        await self.scale_agents(agent_type, current_count - 1)
                        self._last_scale_down[agent_type] = time.time()
    
    async def _cleanup_idle(self) -> None:
        """Remove idle agents that have exceeded timeout."""
        current_time = time.time()
        
        for agent_type, agents in self._agents.items():
            config = self._configs.get(agent_type)
            if not config:
                continue
            
            to_remove = []
            for agent in agents:
                if (
                    agent.state == AgentState.IDLE
                    and current_time - agent.metrics.last_activity > config.idle_timeout_seconds
                    and len(agents) > config.min_instances
                ):
                    to_remove.append(agent)
            
            for agent in to_remove:
                await agent.shutdown()
                agents.remove(agent)
                del self._all_agents[agent.agent_id]
    
    def get_metrics(self) -> PoolMetrics:
        """Get current pool metrics."""
        return self._metrics
    
    def get_agent_metrics(self, agent_id: Optional[str] = None) -> Union[AgentMetrics, List[AgentMetrics]]:
        """Get metrics for specific agent or all agents."""
        if agent_id:
            agent = self._all_agents.get(agent_id)
            return agent.metrics if agent else None
        return [a.metrics for a in self._all_agents.values()]
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get comprehensive pool status."""
        return {
            "metrics": self._metrics.dict(),
            "agent_types": {
                agent_type: {
                    "count": len(agents),
                    "states": {
                        state.name: sum(1 for a in agents if a.state == state)
                        for state in AgentState
                    },
                }
                for agent_type, agents in self._agents.items()
            },
        }


# Factory function
async def create_agent_pool(
    factory: AgentFactory,
    default_config: Optional[AgentConfig] = None,
) -> AgentPool:
    """
    Factory function to create and initialize an agent pool.
    
    Args:
        factory: Agent factory
        default_config: Optional default configuration
        
    Returns:
        Initialized AgentPool instance
    """
    pool = AgentPool(factory, default_config)
    await pool.initialize()
    return pool
