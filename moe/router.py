"""
Mrki MoE Router - Mixture-of-Experts Routing Mechanism

Implements intelligent routing for 50+ specialized sub-agents using:
- Learned routing with load balancing
- Top-k expert selection
- Capacity factor management
- Expert affinity tracking
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
import numpy as np
from collections import defaultdict
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Available routing strategies."""
    TOP_K = "top_k"
    EXPERT_CHOICE = "expert_choice"
    CAPACITY_BASED = "capacity_based"
    LEARNED = "learned"
    HYBRID = "hybrid"


@dataclass
class RoutingConfig:
    """Configuration for MoE routing."""
    num_experts: int = 64
    top_k: int = 2
    capacity_factor: float = 1.25
    min_capacity: int = 4
    noise_std: float = 1.0
    aux_loss_coef: float = 0.01
    z_loss_coef: float = 0.001
    router_dtype: torch.dtype = torch.float32
    load_balance_importance: float = 0.1
    expert_affinity_decay: float = 0.95
    max_concurrent_experts: int = 8
    routing_strategy: RoutingStrategy = RoutingStrategy.TOP_K


@dataclass
class RoutingDecision:
    """Result of a routing decision."""
    expert_indices: List[int]
    weights: torch.Tensor
    load_balance_loss: torch.Tensor
    router_z_loss: torch.Tensor
    capacity_usage: Dict[int, float]
    routing_time_ms: float


class ExpertAffinityTracker:
    """Tracks affinity between input patterns and experts."""
    
    def __init__(self, num_experts: int, embedding_dim: int, decay: float = 0.95):
        self.num_experts = num_experts
        self.embedding_dim = embedding_dim
        self.decay = decay
        self.expert_centroids = torch.randn(num_experts, embedding_dim)
        self.expert_usage_counts = torch.zeros(num_experts)
        self.pattern_history = defaultdict(list)
        
    def update(self, embeddings: torch.Tensor, expert_indices: List[int]):
        """Update expert centroids based on routing decisions."""
        for emb, exp_idx in zip(embeddings, expert_indices):
            self.expert_centroids[exp_idx] = (
                self.decay * self.expert_centroids[exp_idx] + 
                (1 - self.decay) * emb.cpu()
            )
            self.expert_usage_counts[exp_idx] += 1
            
    def get_affinity_scores(self, embeddings: torch.Tensor) -> torch.Tensor:
        """Compute affinity scores for given embeddings."""
        embeddings_norm = F.normalize(embeddings, dim=-1)
        centroids_norm = F.normalize(self.expert_centroids.to(embeddings.device), dim=-1)
        return torch.matmul(embeddings_norm, centroids_norm.T)


class LoadBalancer:
    """Manages load balancing across expert instances."""
    
    def __init__(self, num_experts: int, capacity_factor: float = 1.25):
        self.num_experts = num_experts
        self.capacity_factor = capacity_factor
        self.expert_loads = torch.zeros(num_experts)
        self.expert_capacities = torch.ones(num_experts)
        self.request_queue = asyncio.Queue()
        self.lock = asyncio.Lock()
        
    async def update_load(self, expert_idx: int, load_delta: float):
        """Update load for a specific expert."""
        async with self.lock:
            self.expert_loads[expert_idx] = max(
                0, self.expert_loads[expert_idx] + load_delta
            )
            
    def get_available_experts(self, k: int = 5) -> List[int]:
        """Get k least loaded experts."""
        load_ratios = self.expert_loads / (self.expert_capacities + 1e-8)
        _, indices = torch.topk(load_ratios, k=k, largest=False)
        return indices.tolist()
    
    def compute_balance_loss(self, router_probs: torch.Tensor) -> torch.Tensor:
        """Compute load balancing auxiliary loss."""
        # Fraction of routing weight per expert
        router_prob_per_expert = router_probs.mean(dim=0)
        
        # Fraction of tokens routed to each expert
        num_tokens = router_probs.shape[0]
        tokens_per_expert = (router_probs > 0).float().sum(dim=0) / num_tokens
        
        # Balance loss: encourage uniform distribution
        balance_loss = self.num_experts * torch.sum(
            router_prob_per_expert * tokens_per_expert
        )
        return balance_loss


class RouterGate(nn.Module):
    """Learned gating mechanism for expert selection."""
    
    def __init__(self, input_dim: int, num_experts: int, config: RoutingConfig):
        super().__init__()
        self.input_dim = input_dim
        self.num_experts = num_experts
        self.config = config
        
        # Router network
        self.router = nn.Sequential(
            nn.Linear(input_dim, input_dim // 2),
            nn.LayerNorm(input_dim // 2),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(input_dim // 2, num_experts)
        )
        
        # Expert embedding for learned routing
        self.expert_embeddings = nn.Parameter(
            torch.randn(num_experts, input_dim // 2)
        )
        
        self._init_weights()
        
    def _init_weights(self):
        """Initialize router weights."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
                    
    def forward(
        self, 
        x: torch.Tensor,
        training: bool = True,
        affinity_scores: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Route inputs to experts.
        
        Args:
            x: Input tensor [batch_size, seq_len, input_dim]
            training: Whether in training mode
            affinity_scores: Optional affinity scores from tracker
            
        Returns:
            expert_indices: Selected expert indices [batch_size, seq_len, top_k]
            expert_weights: Routing weights [batch_size, seq_len, top_k]
            router_logits: Raw router logits [batch_size, seq_len, num_experts]
        """
        original_shape = x.shape
        x_flat = x.view(-1, self.input_dim)
        
        # Compute router logits
        router_logits = self.router(x_flat)
        
        # Add affinity bias if available
        if affinity_scores is not None:
            affinity_flat = affinity_scores.view(-1, self.num_experts)
            router_logits = router_logits + self.config.load_balance_importance * affinity_flat
        
        # Add noise during training for exploration
        if training:
            noise = torch.randn_like(router_logits) * self.config.noise_std
            router_logits = router_logits + noise
        
        # Compute routing weights
        router_probs = F.softmax(router_logits, dim=-1)
        
        # Select top-k experts
        expert_weights, expert_indices = torch.topk(
            router_probs, self.config.top_k, dim=-1
        )
        
        # Normalize weights
        expert_weights = expert_weights / (expert_weights.sum(dim=-1, keepdim=True) + 1e-9)
        
        # Reshape to original batch dimensions
        expert_indices = expert_indices.view(*original_shape[:-1], self.config.top_k)
        expert_weights = expert_weights.view(*original_shape[:-1], self.config.top_k)
        
        return expert_indices, expert_weights, router_logits


class MoERouter:
    """
    Main MoE Router implementing multiple routing strategies.
    
    Supports 50+ specialized sub-agents with intelligent load balancing.
    """
    
    def __init__(
        self,
        input_dim: int,
        config: Optional[RoutingConfig] = None,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.config = config or RoutingConfig()
        self.input_dim = input_dim
        self.device = device
        
        # Initialize router gate
        self.router_gate = RouterGate(
            input_dim, 
            self.config.num_experts, 
            self.config
        ).to(device)
        
        # Initialize load balancer
        self.load_balancer = LoadBalancer(
            self.config.num_experts,
            self.config.capacity_factor
        )
        
        # Initialize affinity tracker
        self.affinity_tracker = ExpertAffinityTracker(
            self.config.num_experts,
            input_dim,
            self.config.expert_affinity_decay
        )
        
        # Expert registry (populated externally)
        self.expert_registry: Dict[int, Any] = {}
        
        # Metrics tracking
        self.routing_history = []
        self.expert_usage_counts = defaultdict(int)
        self.total_routings = 0
        
        # Thread pool for parallel expert execution
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_experts)
        
        logger.info(f"Initialized MoE Router with {self.config.num_experts} experts")
        
    def register_expert(self, expert_id: int, expert_instance: Any):
        """Register an expert with the router."""
        self.expert_registry[expert_id] = expert_instance
        logger.info(f"Registered expert {expert_id}")
        
    def unregister_expert(self, expert_id: int):
        """Unregister an expert from the router."""
        if expert_id in self.expert_registry:
            del self.expert_registry[expert_id]
            logger.info(f"Unregistered expert {expert_id}")
            
    def compute_aux_losses(
        self,
        router_logits: torch.Tensor,
        expert_indices: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Compute auxiliary losses for training."""
        router_probs = F.softmax(router_logits, dim=-1)
        
        # Load balance loss
        balance_loss = self.load_balancer.compute_balance_loss(router_probs)
        
        # Router z-loss (encourage sparsity)
        log_z = torch.logsumexp(router_logits, dim=-1)
        z_loss = torch.mean(log_z ** 2)
        
        return balance_loss, z_loss
    
    def route(
        self,
        inputs: torch.Tensor,
        training: bool = True,
        return_metadata: bool = False
    ) -> RoutingDecision:
        """
        Route inputs to appropriate experts.
        
        Args:
            inputs: Input tensor [batch_size, seq_len, input_dim]
            training: Whether in training mode
            return_metadata: Whether to return additional metadata
            
        Returns:
            RoutingDecision with expert indices, weights, and losses
        """
        start_time = time.time()
        
        # Get affinity scores
        inputs_flat = inputs.view(-1, self.input_dim)
        affinity_scores = self.affinity_tracker.get_affinity_scores(inputs_flat)
        affinity_scores = affinity_scores.to(self.device)
        
        # Route through gate
        expert_indices, expert_weights, router_logits = self.router_gate(
            inputs, training, affinity_scores
        )
        
        # Compute auxiliary losses
        balance_loss, z_loss = self.compute_aux_losses(router_logits, expert_indices)
        
        # Update affinity tracker
        if training:
            self.affinity_tracker.update(
                inputs_flat.cpu(),
                expert_indices.view(-1).cpu().tolist()
            )
        
        # Track usage
        for idx in expert_indices.view(-1).cpu().tolist():
            self.expert_usage_counts[idx] += 1
        self.total_routings += 1
        
        # Compute capacity usage
        capacity_usage = {}
        for i in range(self.config.num_experts):
            usage = self.expert_usage_counts[i] / max(1, self.total_routings)
            capacity_usage[i] = usage
        
        routing_time = (time.time() - start_time) * 1000
        
        decision = RoutingDecision(
            expert_indices=expert_indices.cpu().tolist(),
            weights=expert_weights,
            load_balance_loss=balance_loss,
            router_z_loss=z_loss,
            capacity_usage=capacity_usage,
            routing_time_ms=routing_time
        )
        
        if return_metadata:
            decision.metadata = {
                "router_logits": router_logits,
                "affinity_scores": affinity_scores,
                "router_probs": F.softmax(router_logits, dim=-1)
            }
        
        return decision
    
    async def execute_experts_async(
        self,
        inputs: torch.Tensor,
        decision: RoutingDecision,
        expert_fn: Callable[[torch.Tensor, int], torch.Tensor]
    ) -> List[torch.Tensor]:
        """
        Execute selected experts asynchronously.
        
        Args:
            inputs: Input tensor
            decision: Routing decision
            expert_fn: Function to execute expert (inputs, expert_id) -> outputs
            
        Returns:
            List of expert outputs
        """
        expert_indices = decision.expert_indices
        batch_size = inputs.shape[0]
        
        # Group inputs by expert
        expert_inputs = defaultdict(list)
        expert_positions = defaultdict(list)
        
        for b in range(batch_size):
            for k, exp_idx in enumerate(expert_indices[b]):
                expert_inputs[exp_idx].append(inputs[b])
                expert_positions[exp_idx].append((b, k))
        
        # Execute experts in parallel
        async def execute_expert(exp_idx: int, exp_inputs: List[torch.Tensor]):
            await self.load_balancer.update_load(exp_idx, len(exp_inputs))
            stacked = torch.stack(exp_inputs)
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                expert_fn,
                stacked,
                exp_idx
            )
            await self.load_balancer.update_load(exp_idx, -len(exp_inputs))
            return exp_idx, result
        
        tasks = [
            execute_expert(exp_idx, exp_inputs)
            for exp_idx, exp_inputs in expert_inputs.items()
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Reconstruct output
        outputs = [None] * (batch_size * self.config.top_k)
        for exp_idx, result in results:
            for pos, (b, k) in zip(result, expert_positions[exp_idx]):
                outputs[b * self.config.top_k + k] = pos
        
        return outputs
    
    def combine_expert_outputs(
        self,
        expert_outputs: List[torch.Tensor],
        weights: torch.Tensor
    ) -> torch.Tensor:
        """
        Combine expert outputs using routing weights.
        
        Args:
            expert_outputs: List of expert output tensors
            weights: Routing weights
            
        Returns:
            Combined output tensor
        """
        stacked = torch.stack(expert_outputs, dim=-1)  # [..., num_experts]
        weights = weights.unsqueeze(-2)  # [..., 1, num_experts]
        combined = torch.sum(stacked * weights, dim=-1)
        return combined
    
    def get_expert_statistics(self) -> Dict[str, Any]:
        """Get statistics about expert usage."""
        usage_values = list(self.expert_usage_counts.values())
        
        return {
            "total_routings": self.total_routings,
            "expert_usage": dict(self.expert_usage_counts),
            "usage_entropy": self._compute_usage_entropy(),
            "most_used_experts": sorted(
                self.expert_usage_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "least_used_experts": sorted(
                self.expert_usage_counts.items(),
                key=lambda x: x[1]
            )[:10],
            "load_distribution": {
                "mean": np.mean(usage_values) if usage_values else 0,
                "std": np.std(usage_values) if usage_values else 0,
                "min": min(usage_values) if usage_values else 0,
                "max": max(usage_values) if usage_values else 0,
            }
        }
    
    def _compute_usage_entropy(self) -> float:
        """Compute entropy of expert usage distribution."""
        if self.total_routings == 0:
            return 0.0
        
        probs = torch.tensor([
            count / self.total_routings 
            for count in self.expert_usage_counts.values()
        ])
        probs = probs[probs > 0]
        entropy = -torch.sum(probs * torch.log(probs + 1e-10)).item()
        return entropy
    
    def save_state(self, path: str):
        """Save router state to disk."""
        state = {
            "router_gate": self.router_gate.state_dict(),
            "expert_centroids": self.affinity_tracker.expert_centroids,
            "expert_usage_counts": self.expert_usage_counts,
            "total_routings": self.total_routings,
            "config": self.config
        }
        torch.save(state, path)
        logger.info(f"Saved router state to {path}")
        
    def load_state(self, path: str):
        """Load router state from disk."""
        state = torch.load(path, map_location=self.device)
        self.router_gate.load_state_dict(state["router_gate"])
        self.affinity_tracker.expert_centroids = state["expert_centroids"]
        self.expert_usage_counts = defaultdict(int, state["expert_usage_counts"])
        self.total_routings = state["total_routings"]
        logger.info(f"Loaded router state from {path}")


class HierarchicalRouter:
    """
    Hierarchical routing for scaling to 100+ experts.
    
    Uses a two-level routing scheme:
    1. First level: Route to expert clusters
    2. Second level: Route to specific expert within cluster
    """
    
    def __init__(
        self,
        input_dim: int,
        num_clusters: int = 8,
        experts_per_cluster: int = 8,
        config: Optional[RoutingConfig] = None,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.num_clusters = num_clusters
        self.experts_per_cluster = experts_per_cluster
        self.total_experts = num_clusters * experts_per_cluster
        self.device = device
        
        # Cluster-level router
        self.cluster_router = MoERouter(
            input_dim,
            RoutingConfig(
                num_experts=num_clusters,
                top_k=1,
                **{k: v for k, v in (config or RoutingConfig()).__dict__.items() 
                   if k not in ['num_experts', 'top_k']}
            ),
            device
        )
        
        # Expert-level routers per cluster
        self.expert_routers = nn.ModuleList([
            MoERouter(
                input_dim,
                RoutingConfig(
                    num_experts=experts_per_cluster,
                    top_k=2,
                    **{k: v for k, v in (config or RoutingConfig()).__dict__.items() 
                       if k not in ['num_experts', 'top_k']}
                ),
                device
            )
            for _ in range(num_clusters)
        ])
        
    def route(
        self,
        inputs: torch.Tensor,
        training: bool = True
    ) -> Tuple[RoutingDecision, List[RoutingDecision]]:
        """
        Hierarchical routing through clusters then experts.
        
        Returns:
            Tuple of (cluster decision, list of expert decisions)
        """
        # Route to clusters
        cluster_decision = self.cluster_router.route(inputs, training)
        
        # Route to experts within each selected cluster
        expert_decisions = []
        batch_size = inputs.shape[0]
        
        for b in range(batch_size):
            cluster_idx = cluster_decision.expert_indices[b][0]
            expert_decision = self.expert_routers[cluster_idx].route(
                inputs[b:b+1], training
            )
            expert_decisions.append(expert_decision)
        
        return cluster_decision, expert_decisions
    
    def get_global_expert_index(self, cluster_idx: int, expert_idx: int) -> int:
        """Convert cluster-local expert index to global index."""
        return cluster_idx * self.experts_per_cluster + expert_idx


# Factory function for creating routers
def create_router(
    input_dim: int,
    num_experts: int = 64,
    routing_strategy: str = "top_k",
    hierarchical: bool = False,
    **kwargs
) -> MoERouter:
    """
    Factory function to create MoE router.
    
    Args:
        input_dim: Input dimension
        num_experts: Number of experts
        routing_strategy: Routing strategy name
        hierarchical: Whether to use hierarchical routing
        **kwargs: Additional config parameters
        
    Returns:
        Configured MoE router
    """
    config = RoutingConfig(
        num_experts=num_experts,
        routing_strategy=RoutingStrategy(routing_strategy),
        **{k: v for k, v in kwargs.items() if k in RoutingConfig.__dataclass_fields__}
    )
    
    if hierarchical and num_experts > 32:
        num_clusters = int(np.sqrt(num_experts))
        experts_per_cluster = num_experts // num_clusters
        return HierarchicalRouter(
            input_dim,
            num_clusters=num_clusters,
            experts_per_cluster=experts_per_cluster,
            config=config
        )
    
    return MoERouter(input_dim, config)


if __name__ == "__main__":
    # Test the router
    router = create_router(
        input_dim=768,
        num_experts=64,
        top_k=2,
        routing_strategy="top_k"
    )
    
    # Test routing
    test_input = torch.randn(4, 128, 768)
    decision = router.route(test_input, training=True)
    
    print(f"Routing completed in {decision.routing_time_ms:.2f}ms")
    print(f"Selected experts shape: {len(decision.expert_indices)}")
    print(f"Expert weights shape: {decision.weights.shape}")
    print(f"Load balance loss: {decision.load_balance_loss.item():.4f}")
    print(f"Router Z loss: {decision.router_z_loss.item():.4f}")
    
    # Print statistics
    stats = router.get_expert_statistics()
    print(f"\nExpert Statistics:")
    print(f"Total routings: {stats['total_routings']}")
    print(f"Usage entropy: {stats['usage_entropy']:.4f}")
