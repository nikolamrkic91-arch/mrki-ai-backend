"""
Mrki Task Decomposer - Complex Task Breakdown System

This module implements intelligent task decomposition for complex multi-step tasks.
It breaks down high-level tasks into executable subtasks while:
- Respecting token budget constraints (256K context windows)
- Optimizing for parallel execution
- Identifying dependencies between subtasks
- Balancing granularity for efficient execution

Decomposition Strategies:
- Hierarchical: Tree-like breakdown with increasing detail
- Sequential: Linear dependency chain
- Parallel: Independent subtasks for maximum concurrency
- Hybrid: Combination based on task characteristics

Author: Mrki Architecture Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

import structlog
from pydantic import BaseModel, Field, validator

from .orchestrator import (
    AgentCapabilities,
    AgentPriority,
    ExecutionMode,
    SubTask,
)

logger = structlog.get_logger("mrki.task_decomposer")


class DecompositionStrategy(Enum):
    """Strategies for task decomposition."""
    HIERARCHICAL = auto()   # Tree-like breakdown
    SEQUENTIAL = auto()     # Linear dependencies
    PARALLEL = auto()       # Maximum parallelism
    HYBRID = auto()         # Adaptive strategy
    RECURSIVE = auto()      # Recursive subdivision


class TaskComplexity(Enum):
    """Complexity levels for tasks."""
    SIMPLE = 1      # Single subtask
    MODERATE = 2    # 2-5 subtasks
    COMPLEX = 3     # 5-15 subtasks
    VERY_COMPLEX = 4  # 15-50 subtasks
    EXTREME = 5     # 50+ subtasks


class TaskCategory(Enum):
    """Categories for task classification."""
    RESEARCH = "research"
    CODE_GENERATION = "code_generation"
    DATA_ANALYSIS = "data_analysis"
    WRITING = "writing"
    PLANNING = "planning"
    DECISION = "decision"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    INTEGRATION = "integration"
    VERIFICATION = "verification"


@dataclass
class DecompositionMetrics:
    """Metrics for decomposition process."""
    input_tokens: int = 0
    output_tokens: int = 0
    decomposition_time_ms: float = 0.0
    subtasks_created: int = 0
    dependencies_identified: int = 0
    parallel_groups: int = 0
    estimated_total_tokens: int = 0


class TaskPattern(BaseModel):
    """Pattern for recognizing and decomposing task types."""
    name: str
    category: TaskCategory
    keywords: List[str]
    agent_type: str
    decomposition_template: List[Dict[str, Any]]
    estimated_complexity: TaskComplexity
    typical_subtask_count: int
    required_tools: List[str] = Field(default_factory=list)


class DecompositionRule(BaseModel):
    """Rule for decomposing tasks based on patterns."""
    pattern: TaskPattern
    condition: str  # Python expression for matching
    priority: int = 1
    max_depth: int = 3


class DecompositionConfig(BaseModel):
    """Configuration for task decomposition."""
    token_budget: int = 256000
    max_subtasks: int = 100
    min_subtask_tokens: int = 512
    max_subtask_tokens: int = 32000
    default_timeout_seconds: float = 300.0
    enable_pattern_matching: bool = True
    enable_dependency_analysis: bool = True
    parallel_threshold: int = 5  # Min subtasks to use parallel mode
    complexity_analysis_depth: int = 3


class TaskDecomposer:
    """
    Intelligent task decomposition system for complex multi-step tasks.
    
    The TaskDecomposer analyzes complex tasks and breaks them down into
    manageable subtasks optimized for parallel execution. It supports
    multiple decomposition strategies and adapts based on task characteristics.
    
    Key Features:
    - Pattern-based task recognition
    - Dependency graph construction
    - Token budget management
    - Parallel group optimization
    - Adaptive granularity
    
    Example:
        >>> decomposer = TaskDecomposer(token_budget=256000)
        >>> subtasks = await decomposer.decompose(root_task)
        >>> print(f"Created {len(subtasks)} subtasks")
    """
    
    # Predefined task patterns for common scenarios
    DEFAULT_PATTERNS: List[TaskPattern] = [
        TaskPattern(
            name="research_query",
            category=TaskCategory.RESEARCH,
            keywords=["research", "find", "search", "investigate", "explore"],
            agent_type="researcher",
            decomposition_template=[
                {"name": "query_analysis", "description": "Analyze and refine search query"},
                {"name": "information_gathering", "description": "Gather relevant information from sources"},
                {"name": "synthesis", "description": "Synthesize findings into coherent response"},
                {"name": "verification", "description": "Verify accuracy of information"},
            ],
            estimated_complexity=TaskComplexity.MODERATE,
            typical_subtask_count=4,
            required_tools=["web_search", "document_retrieval"],
        ),
        TaskPattern(
            name="code_generation",
            category=TaskCategory.CODE_GENERATION,
            keywords=["code", "implement", "write", "function", "class", "program"],
            agent_type="code_generator",
            decomposition_template=[
                {"name": "requirements_analysis", "description": "Analyze requirements and constraints"},
                {"name": "design", "description": "Design solution architecture"},
                {"name": "implementation", "description": "Implement the solution"},
                {"name": "testing", "description": "Write and run tests"},
                {"name": "documentation", "description": "Generate documentation"},
            ],
            estimated_complexity=TaskComplexity.COMPLEX,
            typical_subtask_count=5,
            required_tools=["code_executor", "syntax_checker", "test_runner"],
        ),
        TaskPattern(
            name="data_analysis",
            category=TaskCategory.DATA_ANALYSIS,
            keywords=["analyze", "data", "statistics", "metrics", "report"],
            agent_type="data_analyst",
            decomposition_template=[
                {"name": "data_loading", "description": "Load and validate data"},
                {"name": "exploration", "description": "Explore data characteristics"},
                {"name": "analysis", "description": "Perform statistical analysis"},
                {"name": "visualization", "description": "Create visualizations"},
                {"name": "interpretation", "description": "Interpret results"},
            ],
            estimated_complexity=TaskComplexity.COMPLEX,
            typical_subtask_count=5,
            required_tools=["data_loader", "analysis_engine", "visualization"],
        ),
        TaskPattern(
            name="writing_task",
            category=TaskCategory.WRITING,
            keywords=["write", "draft", "compose", "create content", "article"],
            agent_type="writer",
            decomposition_template=[
                {"name": "outline", "description": "Create content outline"},
                {"name": "research", "description": "Gather supporting information"},
                {"name": "drafting", "description": "Write initial draft"},
                {"name": "editing", "description": "Edit and refine content"},
                {"name": "review", "description": "Final review and polish"},
            ],
            estimated_complexity=TaskComplexity.MODERATE,
            typical_subtask_count=5,
            required_tools=["grammar_checker", "plagiarism_detector"],
        ),
        TaskPattern(
            name="planning_task",
            category=TaskCategory.PLANNING,
            keywords=["plan", "schedule", "organize", "coordinate", "strategy"],
            agent_type="planner",
            decomposition_template=[
                {"name": "goal_clarification", "description": "Clarify objectives and constraints"},
                {"name": "resource_assessment", "description": "Assess available resources"},
                {"name": "timeline_creation", "description": "Create timeline and milestones"},
                {"name": "risk_analysis", "description": "Identify and mitigate risks"},
                {"name": "execution_plan", "description": "Create detailed execution plan"},
            ],
            estimated_complexity=TaskComplexity.COMPLEX,
            typical_subtask_count=5,
            required_tools=["calendar", "resource_allocator"],
        ),
        TaskPattern(
            name="integration_task",
            category=TaskCategory.INTEGRATION,
            keywords=["integrate", "combine", "merge", "synthesize", "unify"],
            agent_type="integrator",
            decomposition_template=[
                {"name": "component_analysis", "description": "Analyze components to integrate"},
                {"name": "interface_design", "description": "Design integration interfaces"},
                {"name": "implementation", "description": "Implement integration logic"},
                {"name": "testing", "description": "Test integrated system"},
                {"name": "validation", "description": "Validate end-to-end functionality"},
            ],
            estimated_complexity=TaskComplexity.COMPLEX,
            typical_subtask_count=5,
            required_tools=["integration_tester", "validator"],
        ),
    ]
    
    def __init__(self, config: Optional[DecompositionConfig] = None):
        """
        Initialize the task decomposer.
        
        Args:
            config: Decomposition configuration
        """
        self.config = config or DecompositionConfig()
        self.patterns: List[TaskPattern] = self.DEFAULT_PATTERNS.copy()
        self.rules: List[DecompositionRule] = []
        self._initialize_rules()
        self._logger = logger.bind(component="task_decomposer")
    
    def _initialize_rules(self) -> None:
        """Initialize decomposition rules from patterns."""
        for pattern in self.patterns:
            # Create keyword matching condition
            keywords_pattern = "|".join(pattern.keywords)
            condition = f"re.search(r'{keywords_pattern}', task.description, re.IGNORECASE)"
            
            rule = DecompositionRule(
                pattern=pattern,
                condition=condition,
                priority=1,
            )
            self.rules.append(rule)
        
        # Sort rules by priority
        self.rules.sort(key=lambda r: r.priority)
    
    def register_pattern(self, pattern: TaskPattern) -> None:
        """
        Register a new task pattern.
        
        Args:
            pattern: Task pattern to register
        """
        self.patterns.append(pattern)
        
        keywords_pattern = "|".join(pattern.keywords)
        condition = f"re.search(r'{keywords_pattern}', task.description, re.IGNORECASE)"
        
        rule = DecompositionRule(
            pattern=pattern,
            condition=condition,
            priority=1,
        )
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority)
        
        self._logger.info("pattern_registered", pattern_name=pattern.name)
    
    async def decompose(self, task: SubTask) -> List[SubTask]:
        """
        Decompose a task into executable subtasks.
        
        This is the main entry point for task decomposition. It analyzes
        the task, selects the appropriate strategy, and generates subtasks.
        
        Args:
            task: The task to decompose
            
        Returns:
            List of decomposed subtasks
        """
        self._logger.info(
            "decomposition_started",
            task_id=task.task_id,
            task_name=task.name,
        )
        
        # Analyze task complexity
        complexity = self._analyze_complexity(task)
        
        # If simple task, return as-is
        if complexity == TaskComplexity.SIMPLE:
            self._logger.info("task_simple_no_decomposition", task_id=task.task_id)
            return [task]
        
        # Match pattern if enabled
        matched_pattern = None
        if self.config.enable_pattern_matching:
            matched_pattern = self._match_pattern(task)
        
        # Select decomposition strategy
        strategy = self._select_strategy(task, complexity, matched_pattern)
        
        # Decompose based on strategy
        if strategy == DecompositionStrategy.HIERARCHICAL:
            subtasks = await self._decompose_hierarchical(task, matched_pattern)
        elif strategy == DecompositionStrategy.SEQUENTIAL:
            subtasks = await self._decompose_sequential(task, matched_pattern)
        elif strategy == DecompositionStrategy.PARALLEL:
            subtasks = await self._decompose_parallel(task, matched_pattern)
        elif strategy == DecompositionStrategy.HYBRID:
            subtasks = await self._decompose_hybrid(task, matched_pattern)
        else:
            subtasks = await self._decompose_recursive(task, matched_pattern)
        
        # Analyze and add dependencies
        if self.config.enable_dependency_analysis:
            subtasks = self._analyze_dependencies(subtasks)
        
        # Optimize token allocation
        subtasks = self._optimize_tokens(subtasks)
        
        # Validate decomposition
        subtasks = self._validate_decomposition(subtasks)
        
        self._logger.info(
            "decomposition_completed",
            task_id=task.task_id,
            subtask_count=len(subtasks),
            strategy=strategy.name,
        )
        
        return subtasks
    
    def _analyze_complexity(self, task: SubTask) -> TaskComplexity:
        """
        Analyze task complexity based on description and requirements.
        
        Args:
            task: Task to analyze
            
        Returns:
            TaskComplexity level
        """
        description = task.description.lower()
        
        # Count complexity indicators
        indicators = {
            "and": description.count(" and "),
            "then": description.count(" then "),
            "after": description.count(" after "),
            "before": description.count(" before "),
            "steps": description.count("step"),
            "phases": description.count("phase"),
        }
        
        complexity_score = sum(indicators.values())
        
        # Check for explicit complexity markers
        if any(word in description for word in ["simple", "basic", "quick"]):
            return TaskComplexity.SIMPLE
        
        if complexity_score <= 2:
            return TaskComplexity.SIMPLE
        elif complexity_score <= 5:
            return TaskComplexity.MODERATE
        elif complexity_score <= 15:
            return TaskComplexity.COMPLEX
        elif complexity_score <= 30:
            return TaskComplexity.VERY_COMPLEX
        else:
            return TaskComplexity.EXTREME
    
    def _match_pattern(self, task: SubTask) -> Optional[TaskPattern]:
        """
        Match task against registered patterns.
        
        Args:
            task: Task to match
            
        Returns:
            Matched pattern or None
        """
        description = task.description.lower()
        
        for rule in self.rules:
            try:
                if eval(rule.condition, {"re": re, "task": task}):
                    return rule.pattern
            except Exception:
                continue
        
        return None
    
    def _select_strategy(
        self,
        task: SubTask,
        complexity: TaskComplexity,
        pattern: Optional[TaskPattern],
    ) -> DecompositionStrategy:
        """
        Select decomposition strategy based on task characteristics.
        
        Args:
            task: Task to decompose
            complexity: Analyzed complexity
            pattern: Matched pattern if any
            
        Returns:
            Selected decomposition strategy
        """
        # Use pattern's strategy if available
        if pattern:
            if pattern.estimated_complexity == TaskComplexity.SIMPLE:
                return DecompositionStrategy.SEQUENTIAL
            elif pattern.estimated_complexity == TaskComplexity.MODERATE:
                return DecompositionStrategy.HIERARCHICAL
            else:
                return DecompositionStrategy.HYBRID
        
        # Select based on complexity
        if complexity == TaskComplexity.SIMPLE:
            return DecompositionStrategy.SEQUENTIAL
        elif complexity == TaskComplexity.MODERATE:
            return DecompositionStrategy.HIERARCHICAL
        elif complexity == TaskComplexity.COMPLEX:
            return DecompositionStrategy.HYBRID
        else:
            return DecompositionStrategy.RECURSIVE
    
    async def _decompose_hierarchical(
        self,
        task: SubTask,
        pattern: Optional[TaskPattern],
    ) -> List[SubTask]:
        """
        Decompose task using hierarchical (tree) structure.
        
        Args:
            task: Task to decompose
            pattern: Matched pattern
            
        Returns:
            List of subtasks
        """
        subtasks = []
        
        if pattern:
            # Use pattern template
            for i, template in enumerate(pattern.decomposition_template):
                subtask = SubTask(
                    parent_task_id=task.task_id,
                    name=f"{task.name}_{template['name']}",
                    description=template["description"],
                    agent_type=pattern.agent_type,
                    priority=task.priority,
                    input_data=task.input_data,
                    required_tools=pattern.required_tools,
                    execution_mode=ExecutionMode.SEQUENTIAL if i > 0 else ExecutionMode.PARALLEL,
                )
                subtasks.append(subtask)
        else:
            # Generic hierarchical decomposition
            subtasks = await self._generic_hierarchical_decomposition(task)
        
        return subtasks
    
    async def _decompose_sequential(
        self,
        task: SubTask,
        pattern: Optional[TaskPattern],
    ) -> List[SubTask]:
        """
        Decompose task into sequential chain.
        
        Args:
            task: Task to decompose
            pattern: Matched pattern
            
        Returns:
            List of subtasks with linear dependencies
        """
        subtasks = await self._decompose_hierarchical(task, pattern)
        
        # Add sequential dependencies
        for i in range(1, len(subtasks)):
            subtasks[i].dependencies = [subtasks[i-1].task_id]
            subtasks[i].execution_mode = ExecutionMode.SEQUENTIAL
        
        return subtasks
    
    async def _decompose_parallel(
        self,
        task: SubTask,
        pattern: Optional[TaskPattern],
    ) -> List[SubTask]:
        """
        Decompose task into parallel subtasks.
        
        Args:
            task: Task to decompose
            pattern: Matched pattern
            
        Returns:
            List of independent subtasks
        """
        subtasks = await self._decompose_hierarchical(task, pattern)
        
        # Ensure no dependencies for parallel execution
        for subtask in subtasks:
            subtask.dependencies = []
            subtask.execution_mode = ExecutionMode.PARALLEL
        
        return subtasks
    
    async def _decompose_hybrid(
        self,
        task: SubTask,
        pattern: Optional[TaskPattern],
    ) -> List[SubTask]:
        """
        Decompose task using hybrid approach.
        
        Combines hierarchical structure with parallel groups where possible.
        
        Args:
            task: Task to decompose
            pattern: Matched pattern
            
        Returns:
            List of subtasks with optimized dependencies
        """
        subtasks = await self._decompose_hierarchical(task, pattern)
        
        # Group subtasks that can run in parallel
        # This is a simplified version - real implementation would be smarter
        parallel_groups = self._identify_parallel_groups(subtasks)
        
        # Update execution modes
        for group in parallel_groups:
            if len(group) > 1:
                for subtask in group:
                    subtask.execution_mode = ExecutionMode.PARALLEL
        
        return subtasks
    
    async def _decompose_recursive(
        self,
        task: SubTask,
        pattern: Optional[TaskPattern],
        depth: int = 0,
    ) -> List[SubTask]:
        """
        Recursively decompose task until granularity threshold.
        
        Args:
            task: Task to decompose
            pattern: Matched pattern
            depth: Current recursion depth
            
        Returns:
            List of subtasks
        """
        if depth >= self.config.complexity_analysis_depth:
            return [task]
        
        subtasks = await self._decompose_hierarchical(task, pattern)
        
        # Recursively decompose complex subtasks
        final_subtasks = []
        for subtask in subtasks:
            complexity = self._analyze_complexity(subtask)
            if complexity.value > TaskComplexity.MODERATE.value:
                nested = await self._decompose_recursive(subtask, None, depth + 1)
                final_subtasks.extend(nested)
            else:
                final_subtasks.append(subtask)
        
        return final_subtasks
    
    async def _generic_hierarchical_decomposition(self, task: SubTask) -> List[SubTask]:
        """
        Generic hierarchical decomposition when no pattern matches.
        
        Args:
            task: Task to decompose
            
        Returns:
            List of subtasks
        """
        # Break down by sentences or logical sections
        description = task.description
        
        # Simple sentence-based decomposition
        sentences = [s.strip() for s in re.split(r'[.!?]+', description) if s.strip()]
        
        subtasks = []
        for i, sentence in enumerate(sentences[:self.config.max_subtasks]):
            subtask = SubTask(
                parent_task_id=task.task_id,
                name=f"{task.name}_part_{i+1}",
                description=sentence,
                agent_type=task.agent_type,
                priority=task.priority,
                input_data=task.input_data,
            )
            subtasks.append(subtask)
        
        return subtasks
    
    def _identify_parallel_groups(self, subtasks: List[SubTask]) -> List[List[SubTask]]:
        """
        Identify groups of subtasks that can execute in parallel.
        
        Args:
            subtasks: All subtasks
            
        Returns:
            Groups of parallelizable subtasks
        """
        # Simple grouping - real implementation would use dependency analysis
        if len(subtasks) < self.config.parallel_threshold:
            return [subtasks]
        
        # Group by 3-5 subtasks
        groups = []
        group_size = max(3, len(subtasks) // 3)
        
        for i in range(0, len(subtasks), group_size):
            groups.append(subtasks[i:i+group_size])
        
        return groups
    
    def _analyze_dependencies(self, subtasks: List[SubTask]) -> List[SubTask]:
        """
        Analyze and add dependencies between subtasks.
        
        Args:
            subtasks: Subtasks to analyze
            
        Returns:
            Subtasks with dependencies
        """
        # Simple dependency detection based on keywords
        for i, subtask in enumerate(subtasks):
            description = subtask.description.lower()
            
            # Check for references to previous steps
            for j in range(i):
                prev_subtask = subtasks[j]
                if any(kw in description for kw in ["previous", "above", "before", "prior"]):
                    if prev_subtask.task_id not in subtask.dependencies:
                        subtask.dependencies.append(prev_subtask.task_id)
                
                # Check for output references
                if prev_subtask.name.lower() in description:
                    if prev_subtask.task_id not in subtask.dependencies:
                        subtask.dependencies.append(prev_subtask.task_id)
        
        return subtasks
    
    def _optimize_tokens(self, subtasks: List[SubTask]) -> List[SubTask]:
        """
        Optimize token allocation across subtasks.
        
        Args:
            subtasks: Subtasks to optimize
            
        Returns:
            Subtasks with optimized token budgets
        """
        total_budget = self.config.token_budget
        num_subtasks = len(subtasks)
        
        if num_subtasks == 0:
            return subtasks
        
        # Calculate per-subtask budget
        base_budget = total_budget // num_subtasks
        
        # Ensure within bounds
        base_budget = max(
            self.config.min_subtask_tokens,
            min(base_budget, self.config.max_subtask_tokens),
        )
        
        for subtask in subtasks:
            subtask.context_window_tokens = base_budget
        
        return subtasks
    
    def _validate_decomposition(self, subtasks: List[SubTask]) -> List[SubTask]:
        """
        Validate and fix decomposition issues.
        
        Args:
            subtasks: Subtasks to validate
            
        Returns:
            Validated subtasks
        """
        # Ensure no circular dependencies
        task_ids = {s.task_id for s in subtasks}
        
        for subtask in subtasks:
            # Remove dependencies to non-existent tasks
            subtask.dependencies = [
                dep for dep in subtask.dependencies if dep in task_ids
            ]
            
            # Remove self-dependencies
            if subtask.task_id in subtask.dependencies:
                subtask.dependencies.remove(subtask.task_id)
        
        # Limit total subtasks
        if len(subtasks) > self.config.max_subtasks:
            self._logger.warning(
                "too_many_subtasks_truncated",
                original_count=len(subtasks),
                max_allowed=self.config.max_subtasks,
            )
            subtasks = subtasks[:self.config.max_subtasks]
        
        return subtasks
    
    def estimate_complexity(self, description: str) -> TaskComplexity:
        """
        Estimate task complexity from description.
        
        Args:
            description: Task description
            
        Returns:
            Estimated complexity
        """
        task = SubTask(
            name="estimate",
            description=description,
            agent_type="estimator",
        )
        return self._analyze_complexity(task)


# Factory function
async def create_task_decomposer(
    config: Optional[DecompositionConfig] = None,
) -> TaskDecomposer:
    """
    Factory function to create a task decomposer.
    
    Args:
        config: Optional configuration
        
    Returns:
        TaskDecomposer instance
    """
    return TaskDecomposer(config)
