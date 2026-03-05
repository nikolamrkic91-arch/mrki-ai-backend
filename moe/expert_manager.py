"""
Mrki Expert Manager - Expert Lifecycle Management

Manages the complete lifecycle of expert models including:
- Expert initialization and registration
- Dynamic loading and unloading
- Memory management and caching
- Health monitoring and recovery
- Scaling and replication
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import OrderedDict
import asyncio
import time
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor
import logging
import json
from pathlib import Path
import weakref

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExpertState(Enum):
    """Possible states of an expert."""
    UNINITIALIZED = auto()
    INITIALIZING = auto()
    LOADING = auto()
    READY = auto()
    BUSY = auto()
    UNLOADING = auto()
    ERROR = auto()
    OFFLINE = auto()


class ExpertPriority(Enum):
    """Priority levels for expert memory management."""
    CRITICAL = 0  # Never unload
    HIGH = 1      # Prefer to keep loaded
    NORMAL = 2    # Standard priority
    LOW = 3       # Can be unloaded frequently
    BACKGROUND = 4  # Unload when not in use


@dataclass
class ExpertConfig:
    """Configuration for an expert."""
    expert_id: str
    name: str
    description: str = ""
    model_path: Optional[str] = None
    model_type: str = "transformer"
    parameters: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    priority: ExpertPriority = ExpertPriority.NORMAL
    max_batch_size: int = 32
    max_concurrent_requests: int = 4
    timeout_seconds: float = 30.0
    memory_limit_mb: int = 4096
    warmup_iterations: int = 3
    device: str = "cuda"


@dataclass
class ExpertMetrics:
    """Runtime metrics for an expert."""
    total_requests: int = 0
    total_tokens_processed: int = 0
    total_latency_ms: float = 0.0
    errors: int = 0
    last_used: float = 0.0
    load_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    gpu_memory_usage_mb: float = 0.0
    avg_latency_ms: float = 0.0
    throughput_tps: float = 0.0
    cache_hit_rate: float = 0.0


@dataclass
class ExpertInstance:
    """Represents a loaded expert instance."""
    config: ExpertConfig
    model: Optional[nn.Module] = None
    state: ExpertState = ExpertState.UNINITIALIZED
    metrics: ExpertMetrics = field(default_factory=ExpertMetrics)
    created_at: float = field(default_factory=time.time)
    loaded_at: Optional[float] = None
    version: int = 1
    replicas: List[Any] = field(default_factory=list)
    lock: threading.RLock = field(default_factory=threading.RLock)
    _ref_count: int = 0

    def acquire(self):
        """Acquire reference to this expert."""
        with self.lock:
            self._ref_count += 1
            self.metrics.last_used = time.time()

    def release(self):
        """Release reference to this expert."""
        with self.lock:
            self._ref_count = max(0, self._ref_count - 1)

    @property
    def is_idle(self) -> bool:
        """Check if expert is idle (no active references)."""
        return self._ref_count == 0

    @property
    def idle_time(self) -> float:
        """Get time since last use."""
        return time.time() - self.metrics.last_used


class LRUCache(OrderedDict):
    """LRU cache for expert models."""
    
    def __init__(self, capacity: int):
        super().__init__()
        self.capacity = capacity
        self._lock = threading.RLock()
        
    def get(self, key):
        with self._lock:
            if key not in self:
                return None
            self.move_to_end(key)
            return self[key]
    
    def put(self, key, value):
        with self._lock:
            if key in self:
                self.move_to_end(key)
            self[key] = value
            if len(self) > self.capacity:
                self.popitem(last=False)
    
    def remove(self, key):
        with self._lock:
            if key in self:
                del self[key]


class MemoryMonitor:
    """Monitors system memory and GPU memory."""
    
    def __init__(self, warning_threshold: float = 0.85, critical_threshold: float = 0.95):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        self.callbacks: List[Callable[[str, float], None]] = []
        
    def start_monitoring(self, interval_seconds: float = 5.0):
        """Start memory monitoring in background."""
        def monitor():
            while not self._stop_event.is_set():
                self._check_memory()
                time.sleep(interval_seconds)
        
        self._monitor_thread = threading.Thread(target=monitor, daemon=True)
        self._monitor_thread.start()
        logger.info("Memory monitoring started")
        
    def stop_monitoring(self):
        """Stop memory monitoring."""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join()
            
    def _check_memory(self):
        """Check memory usage and trigger callbacks."""
        # System RAM
        ram_percent = psutil.virtual_memory().percent / 100
        
        if ram_percent > self.critical_threshold:
            self._notify("ram_critical", ram_percent)
        elif ram_percent > self.warning_threshold:
            self._notify("ram_warning", ram_percent)
        
        # GPU memory
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                gpu_memory = torch.cuda.memory_allocated(i)
                gpu_total = torch.cuda.get_device_properties(i).total_memory
                gpu_percent = gpu_memory / gpu_total
                
                if gpu_percent > self.critical_threshold:
                    self._notify(f"gpu_{i}_critical", gpu_percent)
                elif gpu_percent > self.warning_threshold:
                    self._notify(f"gpu_{i}_warning", gpu_percent)
                    
    def _notify(self, event: str, value: float):
        """Notify all registered callbacks."""
        for callback in self.callbacks:
            try:
                callback(event, value)
            except Exception as e:
                logger.error(f"Memory callback error: {e}")
                
    def register_callback(self, callback: Callable[[str, float], None]):
        """Register a memory event callback."""
        self.callbacks.append(callback)


class ExpertManager:
    """
    Manages expert lifecycle including loading, unloading, and monitoring.
    
    Features:
    - Dynamic expert loading based on demand
    - LRU cache for active experts
    - Memory-aware unloading
    - Health monitoring and auto-recovery
    - Expert replication for high-load scenarios
    """
    
    def __init__(
        self,
        max_cached_experts: int = 16,
        max_memory_mb: int = 32768,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.max_cached_experts = max_cached_experts
        self.max_memory_mb = max_memory_mb
        self.device = device
        
        # Expert storage
        self._experts: Dict[str, ExpertInstance] = {}
        self._expert_cache = LRUCache(max_cached_experts)
        
        # Model loader function (injected)
        self._model_loader: Optional[Callable[[ExpertConfig], nn.Module]] = None
        
        # Memory monitor
        self._memory_monitor = MemoryMonitor()
        self._memory_monitor.register_callback(self._on_memory_pressure)
        self._memory_monitor.start_monitoring()
        
        # Thread pool for async operations
        self._executor = ThreadPoolExecutor(max_workers=8)
        
        # Async lock
        self._lock = asyncio.Lock()
        
        # Metrics
        self._total_loads = 0
        self._total_unloads = 0
        self._load_errors = 0
        
        logger.info(f"ExpertManager initialized (max_cache={max_cached_experts})")
        
    def set_model_loader(self, loader: Callable[[ExpertConfig], nn.Module]):
        """Set the model loader function."""
        self._model_loader = loader
        
    def register_expert(self, config: ExpertConfig) -> ExpertInstance:
        """Register a new expert configuration."""
        if config.expert_id in self._experts:
            logger.warning(f"Expert {config.expert_id} already registered, updating config")
            
        expert = ExpertInstance(config=config)
        self._experts[config.expert_id] = expert
        logger.info(f"Registered expert: {config.expert_id} ({config.name})")
        return expert
    
    def unregister_expert(self, expert_id: str) -> bool:
        """Unregister an expert and unload if loaded."""
        if expert_id not in self._experts:
            return False
            
        expert = self._experts[expert_id]
        
        # Unload if loaded
        if expert.state in [ExpertState.READY, ExpertState.BUSY]:
            self.unload_expert(expert_id)
            
        del self._experts[expert_id]
        self._expert_cache.remove(expert_id)
        logger.info(f"Unregistered expert: {expert_id}")
        return True
    
    def get_expert(self, expert_id: str) -> Optional[ExpertInstance]:
        """Get expert instance (may not be loaded)."""
        return self._experts.get(expert_id)
    
    def list_experts(self, state: Optional[ExpertState] = None) -> List[ExpertInstance]:
        """List all registered experts, optionally filtered by state."""
        experts = list(self._experts.values())
        if state:
            experts = [e for e in experts if e.state == state]
        return experts
    
    def load_expert(
        self, 
        expert_id: str,
        force_reload: bool = False
    ) -> ExpertInstance:
        """
        Load an expert into memory.
        
        Args:
            expert_id: Expert identifier
            force_reload: Whether to reload even if already loaded
            
        Returns:
            Loaded expert instance
        """
        if expert_id not in self._experts:
            raise ValueError(f"Expert {expert_id} not registered")
            
        expert = self._experts[expert_id]
        
        # Check if already loaded
        if expert.state == ExpertState.READY and not force_reload:
            logger.debug(f"Expert {expert_id} already loaded")
            return expert
            
        # Check cache
        cached = self._expert_cache.get(expert_id)
        if cached and not force_reload:
            logger.debug(f"Expert {expert_id} found in cache")
            return cached
        
        # Load the model
        start_time = time.time()
        expert.state = ExpertState.LOADING
        
        try:
            if self._model_loader is None:
                raise RuntimeError("Model loader not set")
                
            # Check memory before loading
            self._ensure_memory_available(expert.config.memory_limit_mb)
            
            # Load model
            expert.model = self._model_loader(expert.config)
            expert.model.to(self.device)
            expert.model.eval()
            
            # Warmup
            self._warmup_expert(expert)
            
            # Update state
            expert.state = ExpertState.READY
            expert.loaded_at = time.time()
            expert.metrics.load_time_ms = (time.time() - start_time) * 1000
            
            # Update cache
            self._expert_cache.put(expert_id, expert)
            
            self._total_loads += 1
            logger.info(
                f"Loaded expert {expert_id} in {expert.metrics.load_time_ms:.2f}ms"
            )
            
        except Exception as e:
            expert.state = ExpertState.ERROR
            self._load_errors += 1
            logger.error(f"Failed to load expert {expert_id}: {e}")
            raise
            
        return expert
    
    async def load_expert_async(self, expert_id: str) -> ExpertInstance:
        """Asynchronously load an expert."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self.load_expert, expert_id)
    
    def unload_expert(self, expert_id: str) -> bool:
        """Unload an expert from memory."""
        if expert_id not in self._experts:
            return False
            
        expert = self._experts[expert_id]
        
        with expert.lock:
            if expert.state not in [ExpertState.READY, ExpertState.ERROR]:
                return False
                
            if not expert.is_idle:
                logger.warning(f"Expert {expert_id} has active references, delaying unload")
                return False
                
            expert.state = ExpertState.UNLOADING
            
            try:
                # Clear model
                if expert.model is not None:
                    del expert.model
                    expert.model = None
                    
                # Clear cache
                self._expert_cache.remove(expert_id)
                
                # Force garbage collection
                import gc
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    
                expert.state = ExpertState.UNINITIALIZED
                self._total_unloads += 1
                logger.info(f"Unloaded expert {expert_id}")
                return True
                
            except Exception as e:
                expert.state = ExpertState.ERROR
                logger.error(f"Error unloading expert {expert_id}: {e}")
                return False
    
    def _warmup_expert(self, expert: ExpertInstance):
        """Warmup expert with dummy inputs."""
        if expert.model is None:
            return
            
        try:
            dummy_input = torch.randn(
                1, 
                expert.config.parameters.get("seq_len", 128),
                expert.config.parameters.get("hidden_dim", 768),
                device=self.device
            )
            
            with torch.no_grad():
                for _ in range(expert.config.warmup_iterations):
                    _ = expert.model(dummy_input)
                    
            if torch.cuda.is_available():
                torch.cuda.synchronize()
                
        except Exception as e:
            logger.warning(f"Warmup failed for expert {expert.config.expert_id}: {e}")
    
    def _ensure_memory_available(self, required_mb: int):
        """Ensure enough memory is available by unloading low-priority experts."""
        # Check current memory
        available_mb = psutil.virtual_memory().available / (1024 * 1024)
        
        if available_mb >= required_mb:
            return
            
        # Need to free memory
        to_free = required_mb - available_mb + 1024  # Extra 1GB buffer
        freed = 0
        
        # Sort experts by priority and idle time
        candidates = [
            e for e in self._experts.values()
            if e.state == ExpertState.READY 
            and e.is_idle
            and e.config.priority != ExpertPriority.CRITICAL
        ]
        
        candidates.sort(key=lambda e: (
            e.config.priority.value,
            -e.idle_time  # Longer idle time = higher priority for unloading
        ))
        
        for expert in candidates:
            if freed >= to_free:
                break
                
            expert_memory = expert.metrics.memory_usage_mb
            self.unload_expert(expert.config.expert_id)
            freed += expert_memory
            
        if freed < to_free:
            logger.warning(f"Could only free {freed}MB, need {to_free}MB")
    
    def _on_memory_pressure(self, event: str, value: float):
        """Handle memory pressure events."""
        logger.warning(f"Memory pressure: {event} = {value:.2%}")
        
        if "critical" in event:
            # Aggressive unloading
            self._unload_low_priority_experts(aggressive=True)
        elif "warning" in event:
            # Gentle unloading
            self._unload_low_priority_experts(aggressive=False)
    
    def _unload_low_priority_experts(self, aggressive: bool = False):
        """Unload low-priority experts to free memory."""
        candidates = [
            e for e in self._experts.values()
            if e.state == ExpertState.READY 
            and e.is_idle
            and e.config.priority in (
                [ExpertPriority.LOW, ExpertPriority.BACKGROUND] 
                if not aggressive 
                else [ExpertPriority.NORMAL, ExpertPriority.LOW, ExpertPriority.BACKGROUND]
            )
        ]
        
        # Sort by idle time (unload longest idle first)
        candidates.sort(key=lambda e: e.idle_time, reverse=True)
        
        to_unload = len(candidates) // 2 if aggressive else len(candidates) // 4
        
        for expert in candidates[:to_unload]:
            self.unload_expert(expert.config.expert_id)
    
    def get_or_load_expert(self, expert_id: str) -> ExpertInstance:
        """Get expert, loading if necessary."""
        expert = self.get_expert(expert_id)
        if expert is None:
            raise ValueError(f"Expert {expert_id} not registered")
            
        if expert.state != ExpertState.READY:
            expert = self.load_expert(expert_id)
            
        return expert
    
    def create_expert_replica(self, expert_id: str) -> Optional[ExpertInstance]:
        """Create a replica of an expert for load balancing."""
        expert = self.get_expert(expert_id)
        if expert is None or expert.state != ExpertState.READY:
            return None
            
        # Create replica config
        replica_config = ExpertConfig(
            expert_id=f"{expert_id}_replica_{len(expert.replicas)}",
            name=f"{expert.config.name} (replica)",
            model_path=expert.config.model_path,
            model_type=expert.config.model_type,
            parameters=expert.config.parameters,
            capabilities=expert.config.capabilities,
            priority=expert.config.priority,
            device=expert.config.device
        )
        
        # Register and load replica
        replica = self.register_expert(replica_config)
        self.load_expert(replica_config.expert_id)
        
        expert.replicas.append(replica)
        logger.info(f"Created replica for expert {expert_id}")
        
        return replica
    
    def get_expert_metrics(self, expert_id: str) -> Optional[ExpertMetrics]:
        """Get metrics for a specific expert."""
        expert = self.get_expert(expert_id)
        return expert.metrics if expert else None
    
    def update_expert_metrics(
        self, 
        expert_id: str, 
        latency_ms: float, 
        tokens: int = 0,
        error: bool = False
    ):
        """Update expert metrics after request."""
        expert = self.get_expert(expert_id)
        if expert is None:
            return
            
        expert.metrics.total_requests += 1
        expert.metrics.total_tokens_processed += tokens
        expert.metrics.total_latency_ms += latency_ms
        expert.metrics.last_used = time.time()
        
        if error:
            expert.metrics.errors += 1
            
        # Update averages
        if expert.metrics.total_requests > 0:
            expert.metrics.avg_latency_ms = (
                expert.metrics.total_latency_ms / expert.metrics.total_requests
            )
    
    def get_all_metrics(self) -> Dict[str, ExpertMetrics]:
        """Get metrics for all experts."""
        return {
            eid: expert.metrics 
            for eid, expert in self._experts.items()
        }
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """Get manager-level statistics."""
        return {
            "total_experts": len(self._experts),
            "loaded_experts": len([e for e in self._experts.values() if e.state == ExpertState.READY]),
            "cached_experts": len(self._expert_cache),
            "total_loads": self._total_loads,
            "total_unloads": self._total_unloads,
            "load_errors": self._load_errors,
            "memory_usage": {
                "system_percent": psutil.virtual_memory().percent,
                "available_mb": psutil.virtual_memory().available / (1024 * 1024)
            },
            "gpu_memory": self._get_gpu_memory_info() if torch.cuda.is_available() else None
        }
    
    def _get_gpu_memory_info(self) -> Dict[str, Any]:
        """Get GPU memory information."""
        info = {}
        for i in range(torch.cuda.device_count()):
            allocated = torch.cuda.memory_allocated(i) / (1024 ** 2)
            reserved = torch.cuda.memory_reserved(i) / (1024 ** 2)
            total = torch.cuda.get_device_properties(i).total_memory / (1024 ** 2)
            info[f"gpu_{i}"] = {
                "allocated_mb": allocated,
                "reserved_mb": reserved,
                "total_mb": total,
                "free_mb": total - allocated
            }
        return info
    
    def save_expert_configs(self, path: str):
        """Save all expert configurations to file."""
        configs = {
            eid: {
                "expert_id": e.config.expert_id,
                "name": e.config.name,
                "description": e.config.description,
                "model_path": e.config.model_path,
                "model_type": e.config.model_type,
                "parameters": e.config.parameters,
                "capabilities": e.config.capabilities,
                "priority": e.config.priority.name,
                "max_batch_size": e.config.max_batch_size,
                "timeout_seconds": e.config.timeout_seconds,
                "memory_limit_mb": e.config.memory_limit_mb
            }
            for eid, e in self._experts.items()
        }
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(configs, f, indent=2)
            
        logger.info(f"Saved expert configs to {path}")
    
    def load_expert_configs(self, path: str):
        """Load expert configurations from file."""
        with open(path, 'r') as f:
            configs = json.load(f)
            
        for eid, config_dict in configs.items():
            config = ExpertConfig(
                expert_id=config_dict["expert_id"],
                name=config_dict["name"],
                description=config_dict.get("description", ""),
                model_path=config_dict.get("model_path"),
                model_type=config_dict.get("model_type", "transformer"),
                parameters=config_dict.get("parameters", {}),
                capabilities=config_dict.get("capabilities", []),
                priority=ExpertPriority[config_dict.get("priority", "NORMAL")],
                max_batch_size=config_dict.get("max_batch_size", 32),
                timeout_seconds=config_dict.get("timeout_seconds", 30.0),
                memory_limit_mb=config_dict.get("memory_limit_mb", 4096)
            )
            self.register_expert(config)
            
        logger.info(f"Loaded expert configs from {path}")
    
    def shutdown(self):
        """Shutdown the expert manager and cleanup resources."""
        logger.info("Shutting down ExpertManager...")
        
        # Stop memory monitor
        self._memory_monitor.stop_monitoring()
        
        # Unload all experts
        for expert_id in list(self._experts.keys()):
            self.unload_expert(expert_id)
        
        # Shutdown executor
        self._executor.shutdown(wait=True)
        
        logger.info("ExpertManager shutdown complete")


# Convenience functions
def create_expert_manager(
    max_cached_experts: int = 16,
    max_memory_mb: int = 32768,
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
) -> ExpertManager:
    """Factory function to create an ExpertManager."""
    return ExpertManager(max_cached_experts, max_memory_mb, device)


if __name__ == "__main__":
    # Test expert manager
    manager = create_expert_manager(max_cached_experts=4)
    
    # Register a test expert
    config = ExpertConfig(
        expert_id="test_expert",
        name="Test Expert",
        description="A test expert for demonstration",
        model_type="dummy",
        capabilities=["test"],
        priority=ExpertPriority.NORMAL
    )
    
    expert = manager.register_expert(config)
    print(f"Registered expert: {expert.config.name}")
    
    # Print stats
    stats = manager.get_manager_stats()
    print(f"\nManager Stats:")
    print(f"Total experts: {stats['total_experts']}")
    print(f"Loaded experts: {stats['loaded_experts']}")
