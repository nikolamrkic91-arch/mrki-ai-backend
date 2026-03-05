"""
NPC AI Systems
Behavior trees, state machines, and AI utilities for NPCs.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import random


class AIState(Enum):
    """Common AI states."""
    IDLE = "idle"
    PATROL = "patrol"
    CHASE = "chase"
    ATTACK = "attack"
    FLEE = "flee"
    DEAD = "dead"
    STUNNED = "stunned"


class NodeStatus(Enum):
    """Behavior tree node status."""
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"


@dataclass
class AIConfig:
    """AI configuration."""
    detection_range: float = 10.0
    attack_range: float = 2.0
    flee_health_threshold: float = 0.2
    patrol_wait_time: float = 2.0
    move_speed: float = 3.0
    chase_speed: float = 5.0
    rotation_speed: float = 5.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "detection_range": self.detection_range,
            "attack_range": self.attack_range,
            "flee_health_threshold": self.flee_health_threshold,
            "patrol_wait_time": self.patrol_wait_time,
            "move_speed": self.move_speed,
            "chase_speed": self.chase_speed,
            "rotation_speed": self.rotation_speed
        }


class BehaviorTreeNode:
    """Base class for behavior tree nodes."""
    
    def __init__(self, name: str):
        self.name = name
        self.status = NodeStatus.FAILURE
    
    def tick(self, context: Dict[str, Any]) -> NodeStatus:
        """Execute the node."""
        raise NotImplementedError
    
    def reset(self):
        """Reset the node state."""
        self.status = NodeStatus.FAILURE


class SequenceNode(BehaviorTreeNode):
    """Sequence node - executes children in order until one fails."""
    
    def __init__(self, name: str, children: List[BehaviorTreeNode] = None):
        super().__init__(name)
        self.children = children or []
        self.current_index = 0
    
    def tick(self, context: Dict[str, Any]) -> NodeStatus:
        while self.current_index < len(self.children):
            status = self.children[self.current_index].tick(context)
            
            if status == NodeStatus.FAILURE:
                self.reset()
                return NodeStatus.FAILURE
            elif status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
            
            self.current_index += 1
        
        self.reset()
        return NodeStatus.SUCCESS
    
    def reset(self):
        super().reset()
        self.current_index = 0
        for child in self.children:
            child.reset()


class SelectorNode(BehaviorTreeNode):
    """Selector node - executes children until one succeeds."""
    
    def __init__(self, name: str, children: List[BehaviorTreeNode] = None):
        super().__init__(name)
        self.children = children or []
        self.current_index = 0
    
    def tick(self, context: Dict[str, Any]) -> NodeStatus:
        while self.current_index < len(self.children):
            status = self.children[self.current_index].tick(context)
            
            if status == NodeStatus.SUCCESS:
                self.reset()
                return NodeStatus.SUCCESS
            elif status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
            
            self.current_index += 1
        
        self.reset()
        return NodeStatus.FAILURE
    
    def reset(self):
        super().reset()
        self.current_index = 0
        for child in self.children:
            child.reset()


class ActionNode(BehaviorTreeNode):
    """Action node - executes an action."""
    
    def __init__(self, name: str, action: Callable[[Dict[str, Any]], NodeStatus]):
        super().__init__(name)
        self.action = action
    
    def tick(self, context: Dict[str, Any]) -> NodeStatus:
        return self.action(context)


class ConditionNode(BehaviorTreeNode):
    """Condition node - checks a condition."""
    
    def __init__(self, name: str, condition: Callable[[Dict[str, Any]], bool]):
        super().__init__(name)
        self.condition = condition
    
    def tick(self, context: Dict[str, Any]) -> NodeStatus:
        return NodeStatus.SUCCESS if self.condition(context) else NodeStatus.FAILURE


class InverterNode(BehaviorTreeNode):
    """Inverter node - inverts the result of its child."""
    
    def __init__(self, name: str, child: BehaviorTreeNode):
        super().__init__(name)
        self.child = child
    
    def tick(self, context: Dict[str, Any]) -> NodeStatus:
        status = self.child.tick(context)
        
        if status == NodeStatus.SUCCESS:
            return NodeStatus.FAILURE
        elif status == NodeStatus.FAILURE:
            return NodeStatus.SUCCESS
        return NodeStatus.RUNNING


class BehaviorTree:
    """Behavior tree for NPC AI."""
    
    def __init__(self, root: BehaviorTreeNode):
        self.root = root
    
    def tick(self, context: Dict[str, Any]) -> NodeStatus:
        """Tick the behavior tree."""
        return self.root.tick(context)
    
    def reset(self):
        """Reset the behavior tree."""
        self.root.reset()
    
    @staticmethod
    def create_enemy_behavior_tree() -> "BehaviorTree":
        """Create a standard enemy behavior tree."""
        # Root selector
        root = SelectorNode("Root")
        
        # Combat branch (high priority)
        combat_sequence = SequenceNode("Combat")
        combat_sequence.children.append(ConditionNode("Can See Player", lambda ctx: ctx.get("can_see_player", False)))
        combat_sequence.children.append(ConditionNode("In Attack Range", lambda ctx: ctx.get("distance_to_player", 999) <= ctx.get("attack_range", 2)))
        combat_sequence.children.append(ActionNode("Attack", lambda ctx: NodeStatus.SUCCESS))
        
        # Chase branch
        chase_sequence = SequenceNode("Chase")
        chase_sequence.children.append(ConditionNode("Can See Player", lambda ctx: ctx.get("can_see_player", False)))
        chase_sequence.children.append(ActionNode("Chase Player", lambda ctx: NodeStatus.SUCCESS))
        
        # Patrol branch
        patrol_action = ActionNode("Patrol", lambda ctx: NodeStatus.SUCCESS)
        
        root.children = [combat_sequence, chase_sequence, patrol_action]
        
        return BehaviorTree(root)
    
    @staticmethod
    def create_guard_behavior_tree() -> "BehaviorTree":
        """Create a guard behavior tree."""
        root = SelectorNode("Root")
        
        # Alert branch
        alert_sequence = SequenceNode("Alert")
        alert_sequence.children.append(ConditionNode("Heard Noise", lambda ctx: ctx.get("heard_noise", False)))
        alert_sequence.children.append(ActionNode("Investigate", lambda ctx: NodeStatus.SUCCESS))
        
        # Combat branch
        combat_sequence = SequenceNode("Combat")
        combat_sequence.children.append(ConditionNode("Can See Player", lambda ctx: ctx.get("can_see_player", False)))
        combat_sequence.children.append(ActionNode("Attack", lambda ctx: NodeStatus.SUCCESS))
        
        # Patrol branch
        patrol_action = ActionNode("Patrol", lambda ctx: NodeStatus.SUCCESS)
        
        root.children = [alert_sequence, combat_sequence, patrol_action]
        
        return BehaviorTree(root)


class StateMachineAI:
    """State machine based AI."""
    
    def __init__(self, initial_state: str = "idle"):
        self.states: Dict[str, Dict[str, Any]] = {}
        self.transitions: Dict[str, List[Dict[str, Any]]] = {}
        self.current_state = initial_state
        self.previous_state = ""
        self.context: Dict[str, Any] = {}
    
    def add_state(self, name: str, on_enter: Callable = None, 
                  on_update: Callable = None, on_exit: Callable = None):
        """Add a state to the state machine."""
        self.states[name] = {
            "on_enter": on_enter,
            "on_update": on_update,
            "on_exit": on_exit
        }
        self.transitions[name] = []
    
    def add_transition(self, from_state: str, to_state: str, condition: Callable):
        """Add a transition between states."""
        if from_state not in self.transitions:
            self.transitions[from_state] = []
        
        self.transitions[from_state].append({
            "to_state": to_state,
            "condition": condition
        })
    
    def change_state(self, new_state: str):
        """Change to a new state."""
        if new_state not in self.states:
            return
        
        # Exit current state
        if self.current_state in self.states:
            exit_func = self.states[self.current_state].get("on_exit")
            if exit_func:
                exit_func(self.context)
        
        self.previous_state = self.current_state
        self.current_state = new_state
        
        # Enter new state
        enter_func = self.states[self.current_state].get("on_enter")
        if enter_func:
            enter_func(self.context)
    
    def update(self):
        """Update the state machine."""
        # Check transitions
        if self.current_state in self.transitions:
            for transition in self.transitions[self.current_state]:
                if transition["condition"](self.context):
                    self.change_state(transition["to_state"])
                    return
        
        # Update current state
        update_func = self.states[self.current_state].get("on_update")
        if update_func:
            update_func(self.context)
    
    @staticmethod
    def create_enemy_state_machine() -> "StateMachineAI":
        """Create a standard enemy state machine."""
        sm = StateMachineAI("idle")
        
        # Add states
        sm.add_state("idle")
        sm.add_state("patrol")
        sm.add_state("chase")
        sm.add_state("attack")
        sm.add_state("flee")
        
        # Add transitions
        sm.add_transition("idle", "patrol", lambda ctx: ctx.get("patrol_timer", 0) > 3)
        sm.add_transition("patrol", "idle", lambda ctx: ctx.get("reached_waypoint", False))
        sm.add_transition("idle", "chase", lambda ctx: ctx.get("can_see_player", False))
        sm.add_transition("patrol", "chase", lambda ctx: ctx.get("can_see_player", False))
        sm.add_transition("chase", "attack", lambda ctx: ctx.get("distance_to_player", 999) <= ctx.get("attack_range", 2))
        sm.add_transition("attack", "chase", lambda ctx: ctx.get("distance_to_player", 0) > ctx.get("attack_range", 2))
        sm.add_transition("chase", "idle", lambda ctx: not ctx.get("can_see_player", False))
        sm.add_transition("attack", "flee", lambda ctx: ctx.get("health_percent", 1) < 0.2)
        
        return sm


class NPCAI:
    """NPC AI utilities and generators."""
    
    @staticmethod
    def generate_unity_ai_controller() -> str:
        """Generate Unity AI controller script."""
        return '''using UnityEngine;
using UnityEngine.AI;
using System.Collections.Generic;

public enum AIState { Idle, Patrol, Chase, Attack, Flee }

public class AIController : MonoBehaviour
{
    [Header("AI Settings")]
    [SerializeField] private float detectionRange = 10f;
    [SerializeField] private float attackRange = 2f;
    [SerializeField] private float moveSpeed = 3f;
    [SerializeField] private float chaseSpeed = 5f;
    [SerializeField] private float fleeHealthThreshold = 0.2f;
    
    [Header("Patrol")]
    [SerializeField] private List<Transform> patrolPoints;
    [SerializeField] private float patrolWaitTime = 2f;
    
    private NavMeshAgent agent;
    private Transform player;
    private AIState currentState = AIState.Idle;
    private int currentPatrolIndex = 0;
    private float patrolTimer = 0f;
    private HealthSystem healthSystem;
    
    private void Awake()
    {
        agent = GetComponent<NavMeshAgent>();
        healthSystem = GetComponent<HealthSystem>();
    }
    
    private void Start()
    {
        player = GameObject.FindGameObjectWithTag("Player")?.transform;
        agent.speed = moveSpeed;
    }
    
    private void Update()
    {
        if (player == null) return;
        
        UpdateState();
        ExecuteState();
    }
    
    private void UpdateState()
    {
        float distanceToPlayer = Vector3.Distance(transform.position, player.position);
        float healthPercent = healthSystem != null ? healthSystem.CurrentHealth / healthSystem.MaxHealth : 1f;
        
        switch (currentState)
        {
            case AIState.Idle:
                if (distanceToPlayer <= detectionRange)
                    ChangeState(AIState.Chase);
                else if (patrolPoints.Count > 0 && patrolTimer > patrolWaitTime)
                    ChangeState(AIState.Patrol);
                break;
                
            case AIState.Patrol:
                if (distanceToPlayer <= detectionRange)
                    ChangeState(AIState.Chase);
                break;
                
            case AIState.Chase:
                if (distanceToPlayer <= attackRange)
                    ChangeState(AIState.Attack);
                else if (distanceToPlayer > detectionRange)
                    ChangeState(AIState.Idle);
                else if (healthPercent < fleeHealthThreshold)
                    ChangeState(AIState.Flee);
                break;
                
            case AIState.Attack:
                if (distanceToPlayer > attackRange)
                    ChangeState(AIState.Chase);
                else if (healthPercent < fleeHealthThreshold)
                    ChangeState(AIState.Flee);
                break;
                
            case AIState.Flee:
                if (healthPercent > fleeHealthThreshold * 2)
                    ChangeState(AIState.Chase);
                break;
        }
        
        patrolTimer += Time.deltaTime;
    }
    
    private void ExecuteState()
    {
        switch (currentState)
        {
            case AIState.Idle:
                agent.isStopped = true;
                break;
                
            case AIState.Patrol:
                agent.isStopped = false;
                agent.speed = moveSpeed;
                Patrol();
                break;
                
            case AIState.Chase:
                agent.isStopped = false;
                agent.speed = chaseSpeed;
                agent.SetDestination(player.position);
                break;
                
            case AIState.Attack:
                agent.isStopped = true;
                Attack();
                break;
                
            case AIState.Flee:
                agent.isStopped = false;
                agent.speed = chaseSpeed;
                Flee();
                break;
        }
    }
    
    private void Patrol()
    {
        if (patrolPoints.Count == 0) return;
        
        Transform targetPoint = patrolPoints[currentPatrolIndex];
        agent.SetDestination(targetPoint.position);
        
        if (Vector3.Distance(transform.position, targetPoint.position) < 0.5f)
        {
            currentPatrolIndex = (currentPatrolIndex + 1) % patrolPoints.Count;
            patrolTimer = 0f;
            ChangeState(AIState.Idle);
        }
    }
    
    private void Attack()
    {
        // Implement attack logic
        Debug.Log("Attacking player!");
    }
    
    private void Flee()
    {
        Vector3 fleeDirection = transform.position - player.position;
        Vector3 fleePosition = transform.position + fleeDirection.normalized * detectionRange;
        agent.SetDestination(fleePosition);
    }
    
    private void ChangeState(AIState newState)
    {
        currentState = newState;
        patrolTimer = 0f;
    }
    
    private void OnDrawGizmosSelected()
    {
        Gizmos.color = Color.yellow;
        Gizmos.DrawWireSphere(transform.position, detectionRange);
        
        Gizmos.color = Color.red;
        Gizmos.DrawWireSphere(transform.position, attackRange);
    }
}
'''
    
    @staticmethod
    def generate_godot_ai_controller() -> str:
        """Generate Godot AI controller script."""
        return '''extends CharacterBody2D

## AI Controller for NPCs

enum AIState { IDLE, PATROL, CHASE, ATTACK, FLEE }

@export var detection_range: float = 200.0
@export var attack_range: float = 50.0
@export var move_speed: float = 100.0
@export var chase_speed: float = 150.0
@export var flee_health_threshold: float = 0.2

@export var patrol_points: Array[Vector2] = []
@export var patrol_wait_time: float = 2.0

var current_state: AIState = AIState.IDLE
var current_patrol_index: int = 0
var patrol_timer: float = 0.0

@onready var player: Node2D = get_tree().get_first_node_in_group("player")
@onready var health_component: Node = $HealthComponent

func _physics_process(delta: float) -> void:
    if not player:
        return
    
    update_state(delta)
    execute_state(delta)

func update_state(delta: float) -> void:
    var distance_to_player = global_position.distance_to(player.global_position)
    var health_percent = 1.0
    if health_component:
        health_percent = health_component.current_health / health_component.max_health
    
    match current_state:
        AIState.IDLE:
            if distance_to_player <= detection_range:
                change_state(AIState.CHASE)
            elif not patrol_points.is_empty() and patrol_timer > patrol_wait_time:
                change_state(AIState.PATROL)
        
        AIState.PATROL:
            if distance_to_player <= detection_range:
                change_state(AIState.CHASE)
        
        AIState.CHASE:
            if distance_to_player <= attack_range:
                change_state(AIState.ATTACK)
            elif distance_to_player > detection_range:
                change_state(AIState.IDLE)
            elif health_percent < flee_health_threshold:
                change_state(AIState.FLEE)
        
        AIState.ATTACK:
            if distance_to_player > attack_range:
                change_state(AIState.CHASE)
            elif health_percent < flee_health_threshold:
                change_state(AIState.FLEE)
        
        AIState.FLEE:
            if health_percent > flee_health_threshold * 2:
                change_state(AIState.CHASE)
    
    patrol_timer += delta

func execute_state(delta: float) -> void:
    match current_state:
        AIState.IDLE:
            velocity = Vector2.ZERO
        
        AIState.PATROL:
            patrol(delta)
        
        AIState.CHASE:
            chase(delta)
        
        AIState.ATTACK:
            attack(delta)
        
        AIState.FLEE:
            flee(delta)
    
    move_and_slide()

func patrol(delta: float) -> void:
    if patrol_points.is_empty():
        return
    
    var target_point = patrol_points[current_patrol_index]
    var direction = global_position.direction_to(target_point)
    velocity = direction * move_speed
    
    if global_position.distance_to(target_point) < 10:
        current_patrol_index = (current_patrol_index + 1) % patrol_points.size()
        patrol_timer = 0.0
        change_state(AIState.IDLE)

func chase(delta: float) -> void:
    var direction = global_position.direction_to(player.global_position)
    velocity = direction * chase_speed

func attack(delta: float) -> void:
    velocity = Vector2.ZERO
    # Implement attack logic
    print("Attacking player!")

func flee(delta: float) -> void:
    var flee_direction = global_position.direction_to(player.global_position) * -1
    velocity = flee_direction * chase_speed

func change_state(new_state: AIState) -> void:
    current_state = new_state
    patrol_timer = 0.0
'''
