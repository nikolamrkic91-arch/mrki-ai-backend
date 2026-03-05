"""
Mrki Core Architecture - Example Usage

This file demonstrates how to use the Mrki core architecture components
to build a multi-agent AI system.

Example Scenarios:
1. Basic task execution with parallel sub-agents
2. Complex task decomposition and execution
3. Cross-agent verification
4. State management across agents
5. Tool registration and batch execution

Author: Mrki Architecture Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from mrki.core import (
    # Orchestrator
    create_orchestrator,
    OrchestratorConfig,
    SubTask,
    AgentPriority,
    ExecutionMode,
    
    # Agent Pool
    create_agent_pool,
    AgentFactory,
    AgentConfig,
    ScalingPolicy,
    
    # Task Decomposer
    create_task_decomposer,
    DecompositionConfig,
    
    # Verifier
    create_verifier,
    VerificationConfig,
    
    # State Manager
    create_state_manager,
    StateConfig,
    StateLevel,
    
    # Tool Registry
    create_tool_registry,
    ToolRegistryConfig,
    ToolDefinition,
    ToolCategory,
    ToolType,
    ToolParameter,
    ToolOutput,
    create_function_tool,
    FunctionToolExecutor,
    BatchToolRequest,
)


# =============================================================================
# EXAMPLE 1: Basic Orchestrator Usage
# =============================================================================

async def example_basic_orchestrator():
    """
    Example: Basic task execution with the orchestrator.
    
    This demonstrates how to:
    - Create and initialize the orchestrator
    - Execute a simple task
    - Handle the result
    """
    print("=" * 60)
    print("Example 1: Basic Orchestrator Usage")
    print("=" * 60)
    
    # Create orchestrator with custom configuration
    config = OrchestratorConfig(
        max_concurrent_agents=50,
        max_parallel_tool_calls=1000,
        token_budget=256000,
        enable_verification=True,
        verification_sample_rate=0.3,
    )
    
    orchestrator = await create_orchestrator(config)
    
    try:
        # Execute a simple task
        task_description = "Research the latest developments in quantum computing"
        
        result = await orchestrator.execute_task(task_description)
        
        print(f"Task Status: {result.status.name}")
        print(f"Execution Time: {result.execution_time_ms:.2f}ms")
        print(f"Tokens Used: {result.tokens_used}")
        print(f"Output: {result.output}")
        
        if result.error:
            print(f"Error: {result.error}")
        
    finally:
        await orchestrator.shutdown()
    
    print()


# =============================================================================
# EXAMPLE 2: Complex Task Decomposition
# =============================================================================

async def example_task_decomposition():
    """
    Example: Complex task decomposition and execution.
    
    This demonstrates how to:
    - Decompose a complex task into subtasks
    - Execute subtasks in parallel
    - Aggregate results
    """
    print("=" * 60)
    print("Example 2: Complex Task Decomposition")
    print("=" * 60)
    
    # Create task decomposer
    decomposer = await create_task_decomposer(
        DecompositionConfig(
            max_subtasks=50,
            token_budget=256000,
            enable_pattern_matching=True,
        )
    )
    
    # Create a complex task
    complex_task = SubTask(
        name="comprehensive_research",
        description="""
        Conduct comprehensive research on renewable energy technologies:
        1. Analyze current solar panel efficiency trends
        2. Research wind turbine innovations
        3. Investigate battery storage solutions
        4. Compare costs across technologies
        5. Identify market leaders and emerging players
        6. Summarize findings with recommendations
        """,
        agent_type="researcher",
        priority=AgentPriority.HIGH,
        execution_mode=ExecutionMode.PARALLEL,
    )
    
    # Decompose the task
    subtasks = await decomposer.decompose(complex_task)
    
    print(f"Decomposed into {len(subtasks)} subtasks:")
    for i, subtask in enumerate(subtasks, 1):
        print(f"  {i}. {subtask.name}: {subtask.description[:50]}...")
        print(f"     Agent Type: {subtask.agent_type}")
        print(f"     Dependencies: {subtask.dependencies}")
        print()


# =============================================================================
# EXAMPLE 3: Agent Pool Management
# =============================================================================

async def example_agent_pool():
    """
    Example: Agent pool management and scaling.
    
    This demonstrates how to:
    - Create an agent factory
    - Register agent types
    - Scale agent instances dynamically
    """
    print("=" * 60)
    print("Example 3: Agent Pool Management")
    print("=" * 60)
    
    # Create agent factory
    factory = AgentFactory()
    
    # Define agent capabilities
    from mrki.core import AgentCapabilities
    
    researcher_capabilities = AgentCapabilities(
        agent_type="researcher",
        description="Gathers and synthesizes information",
        supported_tasks=["research", "search", "synthesis"],
        max_concurrent_tasks=5,
        average_tokens_per_task=4096,
        context_window_size=128000,
        specializations=["web_search", "document_analysis"],
        required_tools=["web_search", "summarizer"],
    )
    
    # Register agent type (would need actual constructor)
    # factory.register_agent_type(
    #     "researcher",
    #     ResearcherAgent,
    #     researcher_capabilities,
    # )
    
    # Create agent pool
    pool = await create_agent_pool(factory)
    
    # Register agent type configuration
    pool.register_agent_type(
        "researcher",
        AgentConfig(
            agent_type="researcher",
            capabilities=researcher_capabilities,
            min_instances=2,
            max_instances=20,
            scaling_policy=ScalingPolicy.DYNAMIC,
        )
    )
    
    # Scale agents
    await pool.scale_agents("researcher", 5)
    
    # Get pool status
    status = pool.get_pool_status()
    print(f"Pool Status: {status}")
    
    await pool.shutdown()
    print()


# =============================================================================
# EXAMPLE 4: Cross-Agent Verification
# =============================================================================

async def example_verification():
    """
    Example: Cross-agent verification.
    
    This demonstrates how to:
    - Create a verifier
    - Register verifier agents
    - Verify task results
    """
    print("=" * 60)
    print("Example 4: Cross-Agent Verification")
    print("=" * 60)
    
    # Create verifier
    verifier = await create_verifier(
        VerificationConfig(
            enable_verification=True,
            verification_sample_rate=0.5,
            min_confidence_threshold=0.75,
            max_verifiers=3,
        )
    )
    
    # Create a sample task and result
    sample_task = SubTask(
        name="fact_check",
        description="Verify that the Earth orbits the Sun",
        agent_type="researcher",
    )
    
    from mrki.core import TaskResult, TaskStatus
    
    sample_result = TaskResult(
        task_id=sample_task.task_id,
        status=TaskStatus.COMPLETED,
        output="The Earth orbits the Sun in an elliptical path.",
        tokens_used=150,
    )
    
    # Verify the result
    verification_report = await verifier.verify(sample_task, sample_result)
    
    print(f"Verification Score: {verification_report['score']:.2f}")
    print(f"Verified: {verification_report['verified']}")
    print(f"Confidence: {verification_report['confidence']}")
    print(f"Issues: {verification_report['issues']}")
    print()


# =============================================================================
# EXAMPLE 5: State Management
# =============================================================================

async def example_state_management():
    """
    Example: State management across agents.
    
    This demonstrates how to:
    - Create a state manager
    - Set and get state values
    - Build context windows
    """
    print("=" * 60)
    print("Example 5: State Management")
    print("=" * 60)
    
    # Create state manager
    state_mgr = await create_state_manager(
        StateConfig(
            token_budget=256000,
            enable_compression=True,
            enable_persistence=False,
        )
    )
    
    # Set global state
    await state_mgr.set(
        "system_config",
        {"version": "1.0.0", "environment": "production"},
        level=StateLevel.GLOBAL,
    )
    
    # Set session state
    await state_mgr.set(
        "user_preferences",
        {"theme": "dark", "language": "en"},
        level=StateLevel.SESSION,
        session_id="session_123",
    )
    
    # Set task state
    await state_mgr.set(
        "task_context",
        {"query": "quantum computing", "sources": ["arxiv", "nature"]},
        level=StateLevel.TASK,
        task_id="task_456",
    )
    
    # Get state values
    system_config = await state_mgr.get("system_config")
    print(f"System Config: {system_config}")
    
    user_prefs = await state_mgr.get(
        "user_preferences",
        level=StateLevel.SESSION,
        session_id="session_123",
    )
    print(f"User Preferences: {user_prefs}")
    
    # Build context window for agent
    context = await state_mgr.get_context_for_agent(
        agent_id="agent_789",
        task_id="task_456",
        session_id="session_123",
        max_tokens=64000,
    )
    print(f"Agent Context Keys: {list(context.keys())}")
    
    # Get state stats
    stats = state_mgr.get_stats()
    print(f"State Stats: {stats}")
    
    await state_mgr.shutdown()
    print()


# =============================================================================
# EXAMPLE 6: Tool Registry and Batch Execution
# =============================================================================

async def example_tool_registry():
    """
    Example: Tool registration and batch execution.
    
    This demonstrates how to:
    - Create a tool registry
    - Register tools
    - Execute tools individually and in batches
    """
    print("=" * 60)
    print("Example 6: Tool Registry and Batch Execution")
    print("=" * 60)
    
    # Create tool registry
    registry = await create_tool_registry(
        ToolRegistryConfig(
            max_concurrent_calls=1500,
            enable_batching=True,
            batch_size=100,
            enable_caching=True,
        )
    )
    
    # Define a simple tool function
    async def web_search(query: str, limit: int = 10) -> List[Dict[str, str]]:
        """Simulated web search tool."""
        await asyncio.sleep(0.1)  # Simulate network delay
        return [
            {"title": f"Result {i} for {query}", "url": f"https://example.com/{i}"}
            for i in range(limit)
        ]
    
    # Create tool definition from function
    search_tool_def = create_function_tool(
        web_search,
        tool_id="web_search",
        name="Web Search",
        description="Search the web for information",
        category=ToolCategory.WEB_SEARCH,
        tags={"search", "web", "information"},
    )
    
    # Create executor
    search_executor = FunctionToolExecutor(web_search)
    
    # Register tool
    await registry.register_tool(search_tool_def, search_executor)
    
    print(f"Registered tools: {[t.name for t in registry.list_tools()]}")
    
    # Execute single tool
    result = await registry.execute_tool(
        "web_search",
        {"query": "artificial intelligence", "limit": 5},
    )
    print(f"Single execution result: {result.success}, found {len(result.output or [])} results")
    
    # Execute batch of tools
    batch_request = BatchToolRequest(
        batch_id="batch_001",
        requests=[
            {"tool_id": "web_search", "params": {"query": "machine learning", "limit": 3}},
            {"tool_id": "web_search", "params": {"query": "deep learning", "limit": 3}},
            {"tool_id": "web_search", "params": {"query": "neural networks", "limit": 3}},
        ],
        parallel=True,
    )
    
    batch_result = await registry.execute_batch(batch_request)
    print(f"Batch execution: {batch_result.completed_count} completed, {batch_result.failed_count} failed")
    print(f"Total execution time: {batch_result.total_execution_time_ms:.2f}ms")
    
    # Get registry metrics
    metrics = registry.get_metrics()
    print(f"Registry Metrics: {metrics}")
    
    await registry.shutdown()
    print()


# =============================================================================
# EXAMPLE 7: Complete Integration
# =============================================================================

async def example_complete_integration():
    """
    Example: Complete integration of all components.
    
    This demonstrates how all components work together in a complete workflow.
    """
    print("=" * 60)
    print("Example 7: Complete Integration")
    print("=" * 60)
    
    # Initialize all components
    print("Initializing components...")
    
    # 1. Create state manager
    state_mgr = await create_state_manager()
    
    # 2. Create tool registry
    tool_registry = await create_tool_registry()
    
    # 3. Create agent factory and pool
    agent_factory = AgentFactory()
    agent_pool = await create_agent_pool(agent_factory)
    
    # 4. Create task decomposer
    task_decomposer = await create_task_decomposer()
    
    # 5. Create verifier
    verifier = await create_verifier()
    
    # 6. Create orchestrator
    orchestrator = await create_orchestrator(
        OrchestratorConfig(
            max_concurrent_agents=50,
            max_parallel_tool_calls=500,
        )
    )
    
    print("All components initialized!")
    
    # Store system state
    await state_mgr.set(
        "system_status",
        {"initialized": True, "components": 6},
        level=StateLevel.GLOBAL,
    )
    
    # Get system status
    status = await state_mgr.get("system_status")
    print(f"System Status: {status}")
    
    # Cleanup
    print("Shutting down components...")
    await orchestrator.shutdown()
    await agent_pool.shutdown()
    await tool_registry.shutdown()
    await state_mgr.shutdown()
    print("Shutdown complete!")
    print()


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Mrki Core Architecture - Example Usage")
    print("=" * 60 + "\n")
    
    # Run examples
    await example_task_decomposition()
    await example_verification()
    await example_state_management()
    await example_tool_registry()
    await example_agent_pool()
    await example_complete_integration()
    
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
