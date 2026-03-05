"""
Mrki Expert Registry - Expert Registration and Discovery

Implements a comprehensive registry system for:
- Expert registration with capabilities
- Service discovery and health checking
- Load balancing across expert instances
- Capability-based routing
- Expert metadata management
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Set, Any, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from collections import defaultdict
from pathlib import Path
import threading
import hashlib
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExpertStatus(Enum):
    """Status of an expert instance."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    STARTING = "starting"
    STOPPING = "stopping"


class CapabilityType(Enum):
    """Types of expert capabilities."""
    CODE = "code"
    REASONING = "reasoning"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    CONVERSATION = "conversation"
    MATH = "math"
    SCIENCE = "science"
    LEGAL = "legal"
    MEDICAL = "medical"
    FINANCE = "finance"
    TECHNICAL = "technical"


@dataclass
class ExpertCapability:
    """Represents an expert capability."""
    name: str
    type: CapabilityType
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    latency_ms: float = 0.0
    
    def matches(self, query: str) -> bool:
        """Check if capability matches a query."""
        query_lower = query.lower()
        return (
            query_lower in self.name.lower() or
            query_lower in self.description.lower() or
            query_lower in self.type.value.lower()
        )


@dataclass
class ExpertEndpoint:
    """Represents an expert service endpoint."""
    host: str
    port: int
    protocol: str = "http"
    path: str = "/"
    weight: int = 1
    
    @property
    def url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}{self.path}"


@dataclass
class ExpertInstance:
    """Represents a running expert instance."""
    instance_id: str
    expert_id: str
    expert_name: str
    version: str
    endpoint: ExpertEndpoint
    capabilities: List[ExpertCapability]
    status: ExpertStatus = ExpertStatus.STARTING
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Runtime metrics
    registered_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    request_count: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0
    current_load: float = 0.0
    max_capacity: float = 100.0
    
    # Health check
    health_check_path: str = "/health"
    health_check_interval: float = 30.0
    
    def is_healthy(self) -> bool:
        """Check if instance is healthy."""
        return self.status == ExpertStatus.HEALTHY
    
    def is_available(self) -> bool:
        """Check if instance is available for requests."""
        return self.status in [ExpertStatus.HEALTHY, ExpertStatus.DEGRADED]
    
    def get_load_ratio(self) -> float:
        """Get current load ratio."""
        return self.current_load / self.max_capacity if self.max_capacity > 0 else 1.0
    
    def update_heartbeat(self):
        """Update last heartbeat timestamp."""
        self.last_heartbeat = time.time()
    
    def record_request(self, latency_ms: float, error: bool = False):
        """Record a request completion."""
        self.request_count += 1
        if error:
            self.error_count += 1
        
        # Update average latency
        self.avg_latency_ms = (
            (self.avg_latency_ms * (self.request_count - 1) + latency_ms)
            / self.request_count
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "instance_id": self.instance_id,
            "expert_id": self.expert_id,
            "expert_name": self.expert_name,
            "version": self.version,
            "endpoint": {
                "host": self.endpoint.host,
                "port": self.endpoint.port,
                "protocol": self.endpoint.protocol,
                "url": self.endpoint.url
            },
            "capabilities": [
                {
                    "name": c.name,
                    "type": c.type.value,
                    "description": c.description,
                    "confidence": c.confidence
                }
                for c in self.capabilities
            ],
            "status": self.status.value,
            "registered_at": self.registered_at,
            "last_heartbeat": self.last_heartbeat,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "avg_latency_ms": self.avg_latency_ms,
            "current_load": self.current_load,
            "max_capacity": self.max_capacity,
        }


@dataclass
class ExpertDefinition:
    """Static definition of an expert type."""
    expert_id: str
    name: str
    description: str
    version: str
    model_id: str
    capabilities: List[ExpertCapability]
    parameters: Dict[str, Any] = field(default_factory=dict)
    requirements: Dict[str, Any] = field(default_factory=dict)
    scaling_config: Dict[str, Any] = field(default_factory=dict)
    
    def get_capability_hash(self) -> str:
        """Get hash of capabilities for comparison."""
        cap_str = json.dumps([
            {"name": c.name, "type": c.type.value}
            for c in self.capabilities
        ], sort_keys=True)
        return hashlib.sha256(cap_str.encode()).hexdigest()[:16]


class LoadBalancer:
    """
    Load balancer for distributing requests across expert instances.
    
    Supports multiple strategies:
    - Round-robin
    - Least connections
    - Weighted response time
    - Consistent hashing
    """
    
    def __init__(self, strategy: str = "least_connections"):
        self.strategy = strategy
        self._instances: List[ExpertInstance] = []
        self._round_robin_index = 0
        self._lock = threading.Lock()
        
    def add_instance(self, instance: ExpertInstance):
        """Add an instance to the balancer."""
        with self._lock:
            if instance not in self._instances:
                self._instances.append(instance)
    
    def remove_instance(self, instance_id: str) -> bool:
        """Remove an instance from the balancer."""
        with self._lock:
            for i, inst in enumerate(self._instances):
                if inst.instance_id == instance_id:
                    self._instances.pop(i)
                    return True
            return False
    
    def get_instance(self, context: Optional[str] = None) -> Optional[ExpertInstance]:
        """Get next instance based on strategy."""
        with self._lock:
            available = [i for i in self._instances if i.is_available()]
            
            if not available:
                return None
            
            if self.strategy == "round_robin":
                instance = available[self._round_robin_index % len(available)]
                self._round_robin_index += 1
                return instance
            
            elif self.strategy == "least_connections":
                return min(available, key=lambda i: i.current_load)
            
            elif self.strategy == "weighted_response_time":
                # Weight by inverse of latency and load
                def score(i: ExpertInstance) -> float:
                    latency_weight = 1.0 / (i.avg_latency_ms + 1)
                    load_weight = 1.0 - i.get_load_ratio()
                    return latency_weight * load_weight * i.endpoint.weight
                
                return max(available, key=score)
            
            elif self.strategy == "consistent_hashing":
                if context:
                    # Hash context to select instance
                    hash_val = int(hashlib.md5(context.encode()).hexdigest(), 16)
                    return available[hash_val % len(available)]
                else:
                    return available[0]
            
            else:
                return available[0]
    
    def get_all_instances(self) -> List[ExpertInstance]:
        """Get all registered instances."""
        with self._lock:
            return list(self._instances)
    
    def get_healthy_instances(self) -> List[ExpertInstance]:
        """Get all healthy instances."""
        with self._lock:
            return [i for i in self._instances if i.is_healthy()]


class ExpertRegistry:
    """
    Central registry for expert discovery and management.
    
    Features:
    - Expert registration and deregistration
    - Capability-based discovery
    - Health monitoring
    - Load balancing
    - Statistics tracking
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or Path.home() / ".mrki" / "expert_registry.json"
        self.storage_path = Path(self.storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Storage
        self._definitions: Dict[str, ExpertDefinition] = {}
        self._instances: Dict[str, ExpertInstance] = {}
        self._capability_index: Dict[str, Set[str]] = defaultdict(set)
        self._type_index: Dict[CapabilityType, Set[str]] = defaultdict(set)
        self._load_balancers: Dict[str, LoadBalancer] = {}
        
        # Health checking
        self._health_check_interval = 30.0
        self._health_check_task: Optional[asyncio.Task] = None
        self._stop_health_check = asyncio.Event()
        
        # Callbacks
        self._status_callbacks: List[Callable[[ExpertInstance, ExpertStatus], None]] = []
        
        # Lock
        self._lock = threading.RLock()
        
        # Load persisted data
        self._load()
        
        logger.info("ExpertRegistry initialized")
    
    def register_definition(self, definition: ExpertDefinition) -> bool:
        """
        Register an expert definition.
        
        Args:
            definition: Expert definition
            
        Returns:
            True if registered successfully
        """
        with self._lock:
            self._definitions[definition.expert_id] = definition
            
            # Index capabilities
            for cap in definition.capabilities:
                self._capability_index[cap.name].add(definition.expert_id)
                self._type_index[cap.type].add(definition.expert_id)
            
            # Create load balancer
            if definition.expert_id not in self._load_balancers:
                self._load_balancers[definition.expert_id] = LoadBalancer()
            
        self._save()
        logger.info(f"Registered expert definition: {definition.expert_id}")
        return True
    
    def unregister_definition(self, expert_id: str) -> bool:
        """Unregister an expert definition."""
        with self._lock:
            if expert_id not in self._definitions:
                return False
            
            definition = self._definitions.pop(expert_id)
            
            # Remove from indexes
            for cap in definition.capabilities:
                self._capability_index[cap.name].discard(expert_id)
                self._type_index[cap.type].discard(expert_id)
            
            # Remove load balancer
            self._load_balancers.pop(expert_id, None)
        
        self._save()
        logger.info(f"Unregistered expert definition: {expert_id}")
        return True
    
    def register_instance(self, instance: ExpertInstance) -> bool:
        """
        Register an expert instance.
        
        Args:
            instance: Expert instance
            
        Returns:
            True if registered successfully
        """
        with self._lock:
            # Check if definition exists
            if instance.expert_id not in self._definitions:
                logger.warning(f"Expert definition {instance.expert_id} not found")
                return False
            
            self._instances[instance.instance_id] = instance
            
            # Add to load balancer
            if instance.expert_id in self._load_balancers:
                self._load_balancers[instance.expert_id].add_instance(instance)
        
        logger.info(f"Registered instance: {instance.instance_id} for {instance.expert_id}")
        return True
    
    def unregister_instance(self, instance_id: str) -> bool:
        """Unregister an expert instance."""
        with self._lock:
            if instance_id not in self._instances:
                return False
            
            instance = self._instances.pop(instance_id)
            
            # Remove from load balancer
            if instance.expert_id in self._load_balancers:
                self._load_balancers[instance.expert_id].remove_instance(instance_id)
        
        logger.info(f"Unregistered instance: {instance_id}")
        return True
    
    def discover_by_capability(
        self,
        capability: str,
        capability_type: Optional[CapabilityType] = None
    ) -> List[ExpertDefinition]:
        """
        Discover experts by capability.
        
        Args:
            capability: Capability name or query
            capability_type: Optional capability type filter
            
        Returns:
            List of matching expert definitions
        """
        with self._lock:
            results = set()
            
            # Search by name
            for cap_name, expert_ids in self._capability_index.items():
                if capability.lower() in cap_name.lower():
                    results.update(expert_ids)
            
            # Filter by type
            if capability_type:
                type_experts = self._type_index.get(capability_type, set())
                results = results.intersection(type_experts)
            
            return [self._definitions[eid] for eid in results if eid in self._definitions]
    
    def discover_by_query(self, query: str) -> List[ExpertDefinition]:
        """
        Discover experts by natural language query.
        
        Args:
            query: Natural language query
            
        Returns:
            List of matching expert definitions
        """
        with self._lock:
            results = []
            query_lower = query.lower()
            
            for definition in self._definitions.values():
                # Check name and description
                if (query_lower in definition.name.lower() or
                    query_lower in definition.description.lower()):
                    results.append(definition)
                    continue
                
                # Check capabilities
                for cap in definition.capabilities:
                    if cap.matches(query):
                        results.append(definition)
                        break
            
            return results
    
    def get_instance(
        self,
        expert_id: str,
        context: Optional[str] = None
    ) -> Optional[ExpertInstance]:
        """
        Get an instance for an expert with load balancing.
        
        Args:
            expert_id: Expert ID
            context: Optional context for consistent routing
            
        Returns:
            Selected expert instance
        """
        with self._lock:
            balancer = self._load_balancers.get(expert_id)
            if not balancer:
                return None
            
            return balancer.get_instance(context)
    
    def get_all_instances(self, expert_id: Optional[str] = None) -> List[ExpertInstance]:
        """Get all instances, optionally filtered by expert_id."""
        with self._lock:
            if expert_id:
                return [
                    inst for inst in self._instances.values()
                    if inst.expert_id == expert_id
                ]
            return list(self._instances.values())
    
    def get_healthy_instances(self, expert_id: str) -> List[ExpertInstance]:
        """Get all healthy instances for an expert."""
        with self._lock:
            balancer = self._load_balancers.get(expert_id)
            if not balancer:
                return []
            return balancer.get_healthy_instances()
    
    def update_instance_status(
        self,
        instance_id: str,
        status: ExpertStatus
    ) -> bool:
        """Update instance status."""
        with self._lock:
            if instance_id not in self._instances:
                return False
            
            instance = self._instances[instance_id]
            old_status = instance.status
            instance.status = status
            
            # Notify callbacks
            for callback in self._status_callbacks:
                try:
                    callback(instance, old_status)
                except Exception as e:
                    logger.error(f"Status callback error: {e}")
        
        return True
    
    def record_heartbeat(self, instance_id: str) -> bool:
        """Record a heartbeat from an instance."""
        with self._lock:
            if instance_id not in self._instances:
                return False
            
            self._instances[instance_id].update_heartbeat()
        
        return True
    
    def record_request(
        self,
        instance_id: str,
        latency_ms: float,
        error: bool = False
    ) -> bool:
        """Record a request completion."""
        with self._lock:
            if instance_id not in self._instances:
                return False
            
            self._instances[instance_id].record_request(latency_ms, error)
        
        return True
    
    def register_status_callback(
        self,
        callback: Callable[[ExpertInstance, ExpertStatus], None]
    ):
        """Register a callback for status changes."""
        self._status_callbacks.append(callback)
    
    async def start_health_checks(self):
        """Start periodic health checks."""
        if self._health_check_task is not None:
            return
        
        self._stop_health_check.clear()
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Health checks started")
    
    async def stop_health_checks(self):
        """Stop health checks."""
        if self._health_check_task:
            self._stop_health_check.set()
            await self._health_check_task
            self._health_check_task = None
            logger.info("Health checks stopped")
    
    async def _health_check_loop(self):
        """Health check loop."""
        while not self._stop_health_check.is_set():
            await self._check_all_instances()
            try:
                await asyncio.wait_for(
                    self._stop_health_check.wait(),
                    timeout=self._health_check_interval
                )
            except asyncio.TimeoutError:
                pass
    
    async def _check_all_instances(self):
        """Check health of all instances."""
        for instance in list(self._instances.values()):
            try:
                await self._check_instance_health(instance)
            except Exception as e:
                logger.error(f"Health check failed for {instance.instance_id}: {e}")
    
    async def _check_instance_health(self, instance: ExpertInstance):
        """Check health of a single instance."""
        # Check heartbeat age
        heartbeat_age = time.time() - instance.last_heartbeat
        
        if heartbeat_age > instance.health_check_interval * 3:
            # Missed heartbeats
            if instance.status != ExpertStatus.UNHEALTHY:
                self.update_instance_status(instance.instance_id, ExpertStatus.UNHEALTHY)
            return
        
        # Check error rate
        if instance.request_count > 10:
            error_rate = instance.error_count / instance.request_count
            if error_rate > 0.5 and instance.status == ExpertStatus.HEALTHY:
                self.update_instance_status(instance.instance_id, ExpertStatus.DEGRADED)
            elif error_rate < 0.1 and instance.status == ExpertStatus.DEGRADED:
                self.update_instance_status(instance.instance_id, ExpertStatus.HEALTHY)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        with self._lock:
            total_instances = len(self._instances)
            healthy_instances = sum(
                1 for i in self._instances.values() if i.is_healthy()
            )
            available_instances = sum(
                1 for i in self._instances.values() if i.is_available()
            )
            
            return {
                "definitions": len(self._definitions),
                "instances": {
                    "total": total_instances,
                    "healthy": healthy_instances,
                    "available": available_instances,
                    "unhealthy": total_instances - healthy_instances
                },
                "capabilities": len(self._capability_index),
                "by_type": {
                    t.value: len(experts)
                    for t, experts in self._type_index.items()
                },
                "total_requests": sum(
                    i.request_count for i in self._instances.values()
                ),
                "total_errors": sum(
                    i.error_count for i in self._instances.values()
                ),
            }
    
    def _save(self):
        """Persist registry to disk."""
        data = {
            "definitions": {
                eid: {
                    "expert_id": d.expert_id,
                    "name": d.name,
                    "description": d.description,
                    "version": d.version,
                    "model_id": d.model_id,
                    "capabilities": [
                        {
                            "name": c.name,
                            "type": c.type.value,
                            "description": c.description,
                            "confidence": c.confidence
                        }
                        for c in d.capabilities
                    ],
                    "parameters": d.parameters,
                    "requirements": d.requirements
                }
                for eid, d in self._definitions.items()
            }
        }
        
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load(self):
        """Load registry from disk."""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            for eid, d in data.get("definitions", {}).items():
                definition = ExpertDefinition(
                    expert_id=d["expert_id"],
                    name=d["name"],
                    description=d.get("description", ""),
                    version=d.get("version", "1.0"),
                    model_id=d.get("model_id", ""),
                    capabilities=[
                        ExpertCapability(
                            name=c["name"],
                            type=CapabilityType(c["type"]),
                            description=c.get("description", ""),
                            confidence=c.get("confidence", 1.0)
                        )
                        for c in d.get("capabilities", [])
                    ],
                    parameters=d.get("parameters", {}),
                    requirements=d.get("requirements", {})
                )
                self._definitions[eid] = definition
                
                # Index capabilities
                for cap in definition.capabilities:
                    self._capability_index[cap.name].add(eid)
                    self._type_index[cap.type].add(eid)
                
                # Create load balancer
                self._load_balancers[eid] = LoadBalancer()
            
            logger.info(f"Loaded {len(self._definitions)} expert definitions")
        
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")


# Factory functions
def create_expert_registry(storage_path: Optional[str] = None) -> ExpertRegistry:
    """Factory function to create an ExpertRegistry."""
    return ExpertRegistry(storage_path)


def create_expert_definition(
    expert_id: str,
    name: str,
    capabilities: List[Tuple[str, CapabilityType]],
    model_id: str,
    description: str = "",
    version: str = "1.0"
) -> ExpertDefinition:
    """Helper to create an expert definition."""
    return ExpertDefinition(
        expert_id=expert_id,
        name=name,
        description=description,
        version=version,
        model_id=model_id,
        capabilities=[
            ExpertCapability(name=n, type=t)
            for n, t in capabilities
        ]
    )


def create_expert_instance(
    expert_id: str,
    expert_name: str,
    host: str,
    port: int,
    capabilities: List[ExpertCapability],
    version: str = "1.0"
) -> ExpertInstance:
    """Helper to create an expert instance."""
    return ExpertInstance(
        instance_id=str(uuid.uuid4()),
        expert_id=expert_id,
        expert_name=expert_name,
        version=version,
        endpoint=ExpertEndpoint(host=host, port=port),
        capabilities=capabilities
    )


if __name__ == "__main__":
    # Test expert registry
    registry = create_expert_registry()
    
    # Create expert definition
    definition = create_expert_definition(
        expert_id="code-expert-v1",
        name="Code Expert",
        description="Expert for code generation and analysis",
        model_id="codellama/CodeLlama-7b-Instruct-hf",
        capabilities=[
            ("code_generation", CapabilityType.CODE),
            ("code_review", CapabilityType.CODE),
            ("debugging", CapabilityType.TECHNICAL),
        ]
    )
    
    registry.register_definition(definition)
    
    # Create instance
    instance = create_expert_instance(
        expert_id="code-expert-v1",
        expert_name="Code Expert",
        host="localhost",
        port=8080,
        capabilities=definition.capabilities
    )
    
    registry.register_instance(instance)
    
    # Discover
    print("\nDiscovering code experts:")
    results = registry.discover_by_capability("code", CapabilityType.CODE)
    for r in results:
        print(f"  - {r.name}: {r.description}")
    
    # Statistics
    print(f"\nRegistry Statistics:")
    print(json.dumps(registry.get_statistics(), indent=2))
