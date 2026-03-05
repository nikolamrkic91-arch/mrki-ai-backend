"""
Mrki Core Architecture - Multi-Agent AI System

This package provides the core architecture for Mrki, a personal AI assistant
capable of managing 50+ specialized sub-agents in parallel.

Key Components:
- Orchestrator: Central task coordination and parallel execution
- AgentPool: Agent lifecycle management and scaling
- TaskDecomposer: Complex task breakdown and planning
- CrossAgentVerifier: Self-correction through verification
- StateManager: Shared state and context management
- ToolRegistry: Dynamic tool registration and batch execution

Example:
    >>> from mrki.core import create_orchestrator, OrchestratorConfig
    >>> config = OrchestratorConfig(max_concurrent_agents=100)
    >>> orchestrator = await create_orchestrator(config)
    >>> result = await orchestrator.execute_task("Research quantum computing")

Author: Mrki Architecture Team
Version: 1.0.0
License: MIT
"""

from __future__ import annotations

# Orchestrator exports
from .orchestrator import (
    AgentCapabilities,
    AgentPriority,
    AgentWorker,
    DependencyGraph,
    ExecutionMetrics,
    ExecutionMode,
    ExecutionPlan,
    MrkiOrchestrator,
    OrchestratorConfig,
    SubTask,
    TaskCache,
    TaskResult,
    TaskStatus,
    create_orchestrator,
)

# Agent Pool exports
from .agent_pool import (
    AgentConfig,
    AgentFactory,
    AgentInstance,
    AgentMetrics,
    AgentPool,
    AgentState,
    PoolMetrics,
    ResourceAllocation,
    ScalingPolicy,
    create_agent_pool,
)

# Task Decomposer exports
from .task_decomposer import (
    DecompositionConfig,
    DecompositionMetrics,
    DecompositionRule,
    DecompositionStrategy,
    TaskCategory,
    TaskComplexity,
    TaskDecomposer,
    TaskPattern,
    create_task_decomposer,
)

# Verifier exports
from .verifier import (
    ConfidenceLevel,
    CrossAgentVerifier,
    QualityCriterion,
    VerificationConfig,
    VerificationIssue,
    VerificationResult,
    VerificationStatus,
    VerificationType,
    VerifierAgent,
    create_verifier,
)

# State Manager exports
from .state_manager import (
    CompressionStrategy,
    ContextCompressor,
    ContextWindow,
    StateConfig,
    StateEntry,
    StateEvent,
    StateLevel,
    StateListener,
    StateManager,
    StateMetrics,
    StatePersistence,
    StateSnapshot,
    create_state_manager,
)

# Tool Registry exports
from .tool_registry import (
    BatchToolRequest,
    BatchToolResult,
    FunctionToolExecutor,
    RegisteredTool,
    ToolCategory,
    ToolDefinition,
    ToolExecutor,
    ToolMetrics,
    ToolOutput,
    ToolParameter,
    ToolRegistry,
    ToolRegistryConfig,
    ToolResult,
    ToolStatus,
    ToolType,
    create_function_tool,
    create_tool_registry,
)

__version__ = "1.0.0"
__author__ = "Mrki Architecture Team"

__all__ = [
    # Orchestrator
    "MrkiOrchestrator",
    "OrchestratorConfig",
    "ExecutionPlan",
    "SubTask",
    "TaskResult",
    "TaskStatus",
    "AgentWorker",
    "AgentCapabilities",
    "AgentPriority",
    "ExecutionMode",
    "ExecutionMetrics",
    "DependencyGraph",
    "TaskCache",
    "create_orchestrator",
    
    # Agent Pool
    "AgentPool",
    "AgentFactory",
    "AgentInstance",
    "AgentConfig",
    "AgentState",
    "AgentMetrics",
    "PoolMetrics",
    "ResourceAllocation",
    "ScalingPolicy",
    "create_agent_pool",
    
    # Task Decomposer
    "TaskDecomposer",
    "DecompositionConfig",
    "DecompositionStrategy",
    "TaskComplexity",
    "TaskCategory",
    "TaskPattern",
    "DecompositionRule",
    "DecompositionMetrics",
    "create_task_decomposer",
    
    # Verifier
    "CrossAgentVerifier",
    "VerificationConfig",
    "VerificationResult",
    "VerificationStatus",
    "VerificationType",
    "ConfidenceLevel",
    "VerificationIssue",
    "QualityCriterion",
    "VerifierAgent",
    "create_verifier",
    
    # State Manager
    "StateManager",
    "StateConfig",
    "StateEntry",
    "StateLevel",
    "StatePersistence",
    "StateSnapshot",
    "StateEvent",
    "StateListener",
    "StateMetrics",
    "ContextWindow",
    "ContextCompressor",
    "CompressionStrategy",
    "create_state_manager",
    
    # Tool Registry
    "ToolRegistry",
    "ToolRegistryConfig",
    "ToolDefinition",
    "ToolParameter",
    "ToolOutput",
    "ToolResult",
    "ToolType",
    "ToolCategory",
    "ToolStatus",
    "ToolMetrics",
    "ToolExecutor",
    "RegisteredTool",
    "BatchToolRequest",
    "BatchToolResult",
    "FunctionToolExecutor",
    "create_tool_registry",
    "create_function_tool",
]
