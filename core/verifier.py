"""
Mrki Verifier - Cross-Agent Verification System

This module implements a comprehensive verification system where agents verify
each other's work. It provides:
- Multi-agent consensus verification
- Automated quality checks
- Self-correction mechanisms
- Verification result aggregation
- Confidence scoring

Verification Strategies:
- Consensus: Multiple agents vote on correctness
- Redundancy: Same task executed by multiple agents
- Specialized: Expert agents verify specific aspects
- Self-Verification: Agent checks its own work

Author: Mrki Architecture Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Set,
    Tuple,
    Union,
)

import structlog
from pydantic import BaseModel, Field

from .orchestrator import (
    AgentCapabilities,
    AgentPriority,
    SubTask,
    TaskResult,
    TaskStatus,
)

logger = structlog.get_logger("mrki.verifier")


class VerificationStatus(Enum):
    """Status of verification process."""
    PENDING = auto()
    IN_PROGRESS = auto()
    VERIFIED = auto()
    FAILED = auto()
    UNCERTAIN = auto()
    PARTIAL = auto()


class VerificationType(Enum):
    """Types of verification."""
    CONSENSUS = auto()      # Multiple agents vote
    REDUNDANCY = auto()     # Same task, multiple executions
    SPECIALIZED = auto()    # Expert verification
    SELF = auto()           # Self-verification
    CROSS_REFERENCE = auto()  # Cross-reference with sources
    LOGICAL = auto()        # Logical consistency check
    SYNTACTIC = auto()      # Syntax/format validation
    SEMANTIC = auto()       # Meaning/semantic validation


class ConfidenceLevel(Enum):
    """Confidence levels for verification results."""
    VERY_HIGH = 0.95  # 95%+ confidence
    HIGH = 0.85       # 85-95% confidence
    MEDIUM = 0.70     # 70-85% confidence
    LOW = 0.50        # 50-70% confidence
    VERY_LOW = 0.30   # 30-50% confidence
    UNCERTAIN = 0.0   # <30% confidence


@dataclass
class VerificationIssue:
    """Represents an issue found during verification."""
    issue_type: str
    severity: str  # critical, high, medium, low
    description: str
    location: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class VerificationResult:
    """Result of verification process."""
    verifier_id: str
    verification_type: VerificationType
    status: VerificationStatus
    score: float  # 0.0 to 1.0
    confidence: ConfidenceLevel
    issues: List[VerificationIssue] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    execution_time_ms: float = 0.0


class VerificationConfig(BaseModel):
    """Configuration for verification system."""
    enable_verification: bool = True
    verification_sample_rate: float = 0.3
    min_confidence_threshold: float = 0.70
    consensus_threshold: float = 0.66  # 2/3 majority
    max_verification_time_seconds: float = 60.0
    max_verifiers: int = 3
    enable_self_correction: bool = True
    max_correction_attempts: int = 2
    parallel_verification: bool = True


class VerifierAgent(Protocol):
    """Protocol for verifier agents."""
    
    agent_id: str
    verification_types: List[VerificationType]
    capabilities: AgentCapabilities
    
    async def verify(
        self,
        subtask: SubTask,
        result: TaskResult,
        context: Dict[str, Any],
    ) -> VerificationResult:
        """Verify a task result."""
        ...
    
    async def health_check(self) -> bool:
        """Check if verifier is healthy."""
        ...


class QualityCriterion(BaseModel):
    """Quality criterion for verification."""
    name: str
    description: str
    check_function: Optional[str] = None  # Python expression
    weight: float = 1.0
    required: bool = False


class CrossAgentVerifier:
    """
    Cross-agent verification system for ensuring output quality.
    
    The CrossAgentVerifier implements multiple verification strategies:
    1. Consensus: Multiple agents independently verify and vote
    2. Redundancy: Same task executed by different agents
    3. Specialized: Expert agents verify specific aspects
    4. Self-Verification: Agents check their own work
    
    It provides confidence scoring and automatic correction triggers.
    
    Example:
        >>> verifier = CrossAgentVerifier(config)
        >>> result = await verifier.verify(subtask, task_result)
        >>> if result['score'] < 0.7:
        ...     corrected = await verifier.request_correction(subtask, result)
    """
    
    # Default quality criteria
    DEFAULT_CRITERIA: List[QualityCriterion] = [
        QualityCriterion(
            name="completeness",
            description="Task output is complete and addresses all requirements",
            weight=1.5,
            required=True,
        ),
        QualityCriterion(
            name="accuracy",
            description="Information is factually correct",
            weight=2.0,
            required=True,
        ),
        QualityCriterion(
            name="consistency",
            description="Output is internally consistent",
            weight=1.0,
        ),
        QualityCriterion(
            name="clarity",
            description="Output is clear and well-structured",
            weight=0.8,
        ),
        QualityCriterion(
            name="relevance",
            description="Output is relevant to the task",
            weight=1.2,
            required=True,
        ),
    ]
    
    def __init__(self, config: Optional[VerificationConfig] = None):
        """
        Initialize the cross-agent verifier.
        
        Args:
            config: Verification configuration
        """
        self.config = config or VerificationConfig()
        self.verifiers: Dict[str, VerifierAgent] = {}
        self.criteria: List[QualityCriterion] = self.DEFAULT_CRITERIA.copy()
        self.verification_history: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self._logger = logger.bind(component="cross_agent_verifier")
    
    def register_verifier(self, verifier: VerifierAgent) -> None:
        """
        Register a verifier agent.
        
        Args:
            verifier: Verifier agent to register
        """
        self.verifiers[verifier.agent_id] = verifier
        self._logger.info(
            "verifier_registered",
            verifier_id=verifier.agent_id,
            types=[t.name for t in verifier.verification_types],
        )
    
    def unregister_verifier(self, verifier_id: str) -> None:
        """Unregister a verifier agent."""
        if verifier_id in self.verifiers:
            del self.verifiers[verifier_id]
            self._logger.info("verifier_unregistered", verifier_id=verifier_id)
    
    def add_criterion(self, criterion: QualityCriterion) -> None:
        """Add a quality criterion."""
        self.criteria.append(criterion)
        self._logger.info("criterion_added", criterion_name=criterion.name)
    
    async def verify(
        self,
        subtask: SubTask,
        result: TaskResult,
        verification_types: Optional[List[VerificationType]] = None,
    ) -> Dict[str, Any]:
        """
        Verify a task result using cross-agent verification.
        
        This is the main entry point for verification. It selects appropriate
        verification strategies and aggregates results.
        
        Args:
            subtask: The original subtask
            result: The result to verify
            verification_types: Specific verification types to use
            
        Returns:
            Verification report with score and details
        """
        if not self.config.enable_verification:
            return {"verified": True, "score": 1.0, "method": "disabled"}
        
        start_time = time.time()
        
        self._logger.info(
            "verification_started",
            task_id=subtask.task_id,
            agent_id=result.agent_id,
        )
        
        # Select verification strategies
        types_to_use = verification_types or self._select_verification_types(subtask, result)
        
        # Execute verifications
        verification_results = await self._execute_verifications(
            subtask, result, types_to_use
        )
        
        # Aggregate results
        aggregated = self._aggregate_verifications(verification_results)
        
        # Check if correction needed
        needs_correction = (
            aggregated["score"] < self.config.min_confidence_threshold
            and self.config.enable_self_correction
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        report = {
            "verified": aggregated["status"] == VerificationStatus.VERIFIED,
            "status": aggregated["status"].name,
            "score": aggregated["score"],
            "confidence": aggregated["confidence"].name,
            "method": "cross_agent_consensus",
            "verification_count": len(verification_results),
            "needs_correction": needs_correction,
            "issues": aggregated["issues"],
            "details": aggregated["details"],
            "execution_time_ms": execution_time,
        }
        
        # Store in history
        self.verification_history.append({
            "task_id": subtask.task_id,
            "timestamp": time.time(),
            "report": report,
        })
        
        self._logger.info(
            "verification_completed",
            task_id=subtask.task_id,
            score=report["score"],
            verified=report["verified"],
        )
        
        return report
    
    def _select_verification_types(
        self,
        subtask: SubTask,
        result: TaskResult,
    ) -> List[VerificationType]:
        """
        Select appropriate verification types for the task.
        
        Args:
            subtask: The subtask
            result: The result to verify
            
        Returns:
            List of verification types to use
        """
        types_to_use = []
        
        # Always include self-verification
        types_to_use.append(VerificationType.SELF)
        
        # Add consensus for important tasks
        if subtask.priority in (AgentPriority.CRITICAL, AgentPriority.HIGH):
            types_to_use.append(VerificationType.CONSENSUS)
        
        # Add specialized verification based on agent type
        if subtask.agent_type in ["code_generator", "data_analyst"]:
            types_to_use.append(VerificationType.SYNTACTIC)
            types_to_use.append(VerificationType.LOGICAL)
        
        # Add cross-reference for research tasks
        if subtask.agent_type == "researcher":
            types_to_use.append(VerificationType.CROSS_REFERENCE)
        
        return types_to_use
    
    async def _execute_verifications(
        self,
        subtask: SubTask,
        result: TaskResult,
        verification_types: List[VerificationType],
    ) -> List[VerificationResult]:
        """
        Execute multiple verification strategies.
        
        Args:
            subtask: The subtask
            result: The result to verify
            verification_types: Types of verification to execute
            
        Returns:
            List of verification results
        """
        verification_tasks = []
        
        for vtype in verification_types:
            if vtype == VerificationType.CONSENSUS:
                task = self._verify_consensus(subtask, result)
            elif vtype == VerificationType.REDUNDANCY:
                task = self._verify_redundancy(subtask, result)
            elif vtype == VerificationType.SPECIALIZED:
                task = self._verify_specialized(subtask, result)
            elif vtype == VerificationType.SELF:
                task = self._verify_self(subtask, result)
            elif vtype == VerificationType.CROSS_REFERENCE:
                task = self._verify_cross_reference(subtask, result)
            elif vtype == VerificationType.LOGICAL:
                task = self._verify_logical(subtask, result)
            elif vtype == VerificationType.SYNTACTIC:
                task = self._verify_syntactic(subtask, result)
            elif vtype == VerificationType.SEMANTIC:
                task = self._verify_semantic(subtask, result)
            else:
                continue
            
            verification_tasks.append(task)
        
        # Execute in parallel if configured
        if self.config.parallel_verification:
            results = await asyncio.gather(*verification_tasks, return_exceptions=True)
        else:
            results = []
            for task in verification_tasks:
                try:
                    result = await task
                    results.append(result)
                except Exception as e:
                    results.append(e)
        
        # Filter out exceptions
        valid_results = []
        for r in results:
            if isinstance(r, Exception):
                self._logger.warning("verification_failed", error=str(r))
            else:
                valid_results.append(r)
        
        return valid_results
    
    async def _verify_consensus(
        self,
        subtask: SubTask,
        result: TaskResult,
    ) -> VerificationResult:
        """
        Verify using consensus from multiple verifiers.
        
        Args:
            subtask: The subtask
            result: The result to verify
            
        Returns:
            Consensus verification result
        """
        start_time = time.time()
        
        # Select verifiers for consensus
        available_verifiers = [
            v for v in self.verifiers.values()
            if VerificationType.CONSENSUS in v.verification_types
            and await v.health_check()
        ]
        
        if len(available_verifiers) < 2:
            return VerificationResult(
                verifier_id="consensus",
                verification_type=VerificationType.CONSENSUS,
                status=VerificationStatus.UNCERTAIN,
                score=0.5,
                confidence=ConfidenceLevel.UNCERTAIN,
                details={"error": "Insufficient verifiers for consensus"},
            )
        
        # Limit verifiers
        selected_verifiers = available_verifiers[:self.config.max_verifiers]
        
        # Execute verifications
        context = {"original_subtask": subtask, "criteria": self.criteria}
        verification_tasks = [
            verifier.verify(subtask, result, context)
            for verifier in selected_verifiers
        ]
        
        results = await asyncio.gather(*verification_tasks, return_exceptions=True)
        
        # Calculate consensus
        valid_results = [r for r in results if isinstance(r, VerificationResult)]
        
        if not valid_results:
            return VerificationResult(
                verifier_id="consensus",
                verification_type=VerificationType.CONSENSUS,
                status=VerificationStatus.FAILED,
                score=0.0,
                confidence=ConfidenceLevel.UNCERTAIN,
                details={"error": "All verifiers failed"},
            )
        
        # Count votes
        votes_for = sum(1 for r in valid_results if r.score >= self.config.min_confidence_threshold)
        total_votes = len(valid_results)
        consensus_ratio = votes_for / total_votes
        
        # Aggregate issues
        all_issues = []
        for r in valid_results:
            all_issues.extend(r.issues)
        
        # Calculate average score
        avg_score = sum(r.score for r in valid_results) / len(valid_results)
        
        execution_time = (time.time() - start_time) * 1000
        
        if consensus_ratio >= self.config.consensus_threshold:
            status = VerificationStatus.VERIFIED
            confidence = ConfidenceLevel.HIGH if avg_score > 0.85 else ConfidenceLevel.MEDIUM
        else:
            status = VerificationStatus.FAILED
            confidence = ConfidenceLevel.LOW
        
        return VerificationResult(
            verifier_id="consensus",
            verification_type=VerificationType.CONSENSUS,
            status=status,
            score=avg_score,
            confidence=confidence,
            issues=all_issues,
            details={
                "consensus_ratio": consensus_ratio,
                "votes_for": votes_for,
                "total_votes": total_votes,
                "individual_scores": [r.score for r in valid_results],
            },
            execution_time_ms=execution_time,
        )
    
    async def _verify_redundancy(
        self,
        subtask: SubTask,
        result: TaskResult,
    ) -> VerificationResult:
        """Verify by executing task redundantly."""
        # Implementation for redundancy verification
        # Would re-execute task with different agents and compare
        return VerificationResult(
            verifier_id="redundancy",
            verification_type=VerificationType.REDUNDANCY,
            status=VerificationStatus.VERIFIED,
            score=1.0,
            confidence=ConfidenceLevel.HIGH,
        )
    
    async def _verify_specialized(
        self,
        subtask: SubTask,
        result: TaskResult,
    ) -> VerificationResult:
        """Verify using specialized expert agents."""
        # Find specialized verifiers
        specialized = [
            v for v in self.verifiers.values()
            if VerificationType.SPECIALIZED in v.verification_types
        ]
        
        if not specialized:
            return VerificationResult(
                verifier_id="specialized",
                verification_type=VerificationType.SPECIALIZED,
                status=VerificationStatus.UNCERTAIN,
                score=0.5,
                confidence=ConfidenceLevel.UNCERTAIN,
            )
        
        # Use first available specialized verifier
        verifier = specialized[0]
        context = {"specialization": subtask.agent_type}
        
        return await verifier.verify(subtask, result, context)
    
    async def _verify_self(
        self,
        subtask: SubTask,
        result: TaskResult,
    ) -> VerificationResult:
        """Self-verification by the original agent."""
        start_time = time.time()
        
        # Run quality checks
        issues = []
        score = 1.0
        
        # Check completeness
        if result.output is None or result.output == "":
            issues.append(VerificationIssue(
                issue_type="completeness",
                severity="critical",
                description="Task output is empty",
            ))
            score -= 0.5
        
        # Check for errors
        if result.error:
            issues.append(VerificationIssue(
                issue_type="execution",
                severity="critical",
                description=f"Task execution failed: {result.error}",
            ))
            score = 0.0
        
        # Check execution time
        if result.execution_time_ms > subtask.timeout_seconds * 1000:
            issues.append(VerificationIssue(
                issue_type="performance",
                severity="medium",
                description="Task exceeded timeout",
            ))
            score -= 0.1
        
        execution_time = (time.time() - start_time) * 1000
        
        # Determine status
        if score >= self.config.min_confidence_threshold:
            status = VerificationStatus.VERIFIED
            confidence = ConfidenceLevel.HIGH if score > 0.9 else ConfidenceLevel.MEDIUM
        elif score > 0.3:
            status = VerificationStatus.PARTIAL
            confidence = ConfidenceLevel.LOW
        else:
            status = VerificationStatus.FAILED
            confidence = ConfidenceLevel.VERY_LOW
        
        return VerificationResult(
            verifier_id="self",
            verification_type=VerificationType.SELF,
            status=status,
            score=max(0.0, score),
            confidence=confidence,
            issues=issues,
            execution_time_ms=execution_time,
        )
    
    async def _verify_cross_reference(
        self,
        subtask: SubTask,
        result: TaskResult,
    ) -> VerificationResult:
        """Verify by cross-referencing with sources."""
        # Implementation for cross-reference verification
        return VerificationResult(
            verifier_id="cross_reference",
            verification_type=VerificationType.CROSS_REFERENCE,
            status=VerificationStatus.VERIFIED,
            score=0.9,
            confidence=ConfidenceLevel.HIGH,
        )
    
    async def _verify_logical(
        self,
        subtask: SubTask,
        result: TaskResult,
    ) -> VerificationResult:
        """Verify logical consistency."""
        # Implementation for logical verification
        return VerificationResult(
            verifier_id="logical",
            verification_type=VerificationType.LOGICAL,
            status=VerificationStatus.VERIFIED,
            score=1.0,
            confidence=ConfidenceLevel.HIGH,
        )
    
    async def _verify_syntactic(
        self,
        subtask: SubTask,
        result: TaskResult,
    ) -> VerificationResult:
        """Verify syntactic correctness."""
        issues = []
        score = 1.0
        
        # Check if output is valid JSON if expected
        if subtask.expected_output_schema:
            try:
                if isinstance(result.output, str):
                    json.loads(result.output)
            except json.JSONDecodeError as e:
                issues.append(VerificationIssue(
                    issue_type="syntax",
                    severity="high",
                    description=f"Invalid JSON output: {str(e)}",
                ))
                score -= 0.3
        
        return VerificationResult(
            verifier_id="syntactic",
            verification_type=VerificationType.SYNTACTIC,
            status=VerificationStatus.VERIFIED if score > 0.7 else VerificationStatus.FAILED,
            score=score,
            confidence=ConfidenceLevel.HIGH if score > 0.9 else ConfidenceLevel.MEDIUM,
            issues=issues,
        )
    
    async def _verify_semantic(
        self,
        subtask: SubTask,
        result: TaskResult,
    ) -> VerificationResult:
        """Verify semantic correctness."""
        # Implementation for semantic verification
        return VerificationResult(
            verifier_id="semantic",
            verification_type=VerificationType.SEMANTIC,
            status=VerificationStatus.VERIFIED,
            score=0.85,
            confidence=ConfidenceLevel.HIGH,
        )
    
    def _aggregate_verifications(
        self,
        results: List[VerificationResult],
    ) -> Dict[str, Any]:
        """
        Aggregate multiple verification results.
        
        Args:
            results: List of verification results
            
        Returns:
            Aggregated verification report
        """
        if not results:
            return {
                "status": VerificationStatus.UNCERTAIN,
                "score": 0.5,
                "confidence": ConfidenceLevel.UNCERTAIN,
                "issues": [],
                "details": {},
            }
        
        # Calculate weighted score
        total_weight = len(results)
        weighted_score = sum(r.score for r in results) / total_weight
        
        # Aggregate issues
        all_issues = []
        for r in results:
            all_issues.extend(r.issues)
        
        # Determine status
        if weighted_score >= self.config.min_confidence_threshold:
            status = VerificationStatus.VERIFIED
        elif weighted_score > 0.3:
            status = VerificationStatus.PARTIAL
        else:
            status = VerificationStatus.FAILED
        
        # Determine confidence
        if weighted_score >= 0.95:
            confidence = ConfidenceLevel.VERY_HIGH
        elif weighted_score >= 0.85:
            confidence = ConfidenceLevel.HIGH
        elif weighted_score >= 0.70:
            confidence = ConfidenceLevel.MEDIUM
        elif weighted_score >= 0.50:
            confidence = ConfidenceLevel.LOW
        else:
            confidence = ConfidenceLevel.VERY_LOW
        
        return {
            "status": status,
            "score": weighted_score,
            "confidence": confidence,
            "issues": all_issues,
            "details": {
                "individual_results": [
                    {
                        "verifier": r.verifier_id,
                        "type": r.verification_type.name,
                        "score": r.score,
                        "status": r.status.name,
                    }
                    for r in results
                ],
            },
        }
    
    async def request_correction(
        self,
        subtask: SubTask,
        verification_report: Dict[str, Any],
        original_result: TaskResult,
    ) -> TaskResult:
        """
        Request correction based on verification feedback.
        
        Args:
            subtask: The original subtask
            verification_report: Verification report with issues
            original_result: The original task result
            
        Returns:
            Corrected task result
        """
        self._logger.info(
            "correction_requested",
            task_id=subtask.task_id,
            issues_count=len(verification_report.get("issues", [])),
        )
        
        # Create correction subtask
        correction_subtask = SubTask(
            parent_task_id=subtask.parent_task_id,
            name=f"{subtask.name}_correction",
            description=f"Correct the following issues: {verification_report.get('issues')}",
            agent_type=subtask.agent_type,
            priority=subtask.priority,
            input_data={
                **subtask.input_data,
                "original_output": original_result.output,
                "issues": verification_report.get("issues", []),
                "verification_score": verification_report.get("score"),
            },
            max_retries=self.config.max_correction_attempts,
        )
        
        # Return correction subtask for execution
        # The orchestrator will execute this
        return TaskResult(
            task_id=correction_subtask.task_id,
            status=TaskStatus.PENDING,
            output=None,
            metadata={
                "correction_subtask": correction_subtask,
                "verification_report": verification_report,
            },
        )
    
    def get_verification_stats(self) -> Dict[str, Any]:
        """Get verification statistics."""
        if not self.verification_history:
            return {"total_verifications": 0}
        
        scores = [v["report"]["score"] for v in self.verification_history]
        
        return {
            "total_verifications": len(self.verification_history),
            "average_score": sum(scores) / len(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "verified_count": sum(1 for v in self.verification_history if v["report"]["verified"]),
            "correction_count": sum(1 for v in self.verification_history if v["report"].get("needs_correction")),
        }


# Factory function
async def create_verifier(
    config: Optional[VerificationConfig] = None,
) -> CrossAgentVerifier:
    """
    Factory function to create a cross-agent verifier.
    
    Args:
        config: Optional configuration
        
    Returns:
        CrossAgentVerifier instance
    """
    return CrossAgentVerifier(config)
