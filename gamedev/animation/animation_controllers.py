"""
Animation Controllers and State Machines
Animation state management for different game engines.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class AnimationType(Enum):
    """Animation types."""
    IDLE = "idle"
    WALK = "walk"
    RUN = "run"
    JUMP = "jump"
    FALL = "fall"
    ATTACK = "attack"
    HIT = "hit"
    DEATH = "death"
    INTERACT = "interact"
    CUSTOM = "custom"


class BlendTreeType(Enum):
    """Animation blend tree types."""
    BLEND_1D = "1d"
    BLEND_2D = "2d"
    BLEND_DIRECT = "direct"


@dataclass
class AnimationState:
    """Represents an animation state."""
    name: str
    animation_clip: str
    speed: float = 1.0
    loop: bool = True
    transitions: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "animation_clip": self.animation_clip,
            "speed": self.speed,
            "loop": self.loop,
            "transitions": self.transitions
        }


@dataclass
class AnimationTransition:
    """Represents an animation transition."""
    from_state: str
    to_state: str
    condition: str
    duration: float = 0.25
    has_exit_time: bool = False
    exit_time: float = 0.75
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_state": self.from_state,
            "to_state": self.to_state,
            "condition": self.condition,
            "duration": self.duration,
            "has_exit_time": self.has_exit_time,
            "exit_time": self.exit_time
        }


class AnimationStateMachine:
    """Animation state machine generator."""
    
    def __init__(self):
        self.states: List[AnimationState] = []
        self.transitions: List[AnimationTransition] = []
        self.default_state: str = ""
        self.parameters: Dict[str, str] = {}
    
    def add_state(self, state: AnimationState):
        """Add an animation state."""
        self.states.append(state)
        if not self.default_state:
            self.default_state = state.name
        return self
    
    def add_transition(self, transition: AnimationTransition):
        """Add an animation transition."""
        self.transitions.append(transition)
        return self
    
    def add_parameter(self, name: str, param_type: str):
        """Add an animation parameter."""
        self.parameters[name] = param_type
        return self
    
    def set_default_state(self, state_name: str):
        """Set the default state."""
        self.default_state = state_name
        return self
    
    def generate_unity_animator_controller(self) -> str:
        """Generate Unity Animator Controller configuration."""
        lines = []
        
        lines.append("using UnityEngine;")
        lines.append("")
        lines.append("public static class AnimatorParameters")
        lines.append("{")
        for param_name, param_type in self.parameters.items():
            lines.append(f'    public static readonly int {param_name} = Animator.StringToHash("{param_name}");')
        lines.append("}")
        lines.append("")
        
        lines.append("public class AnimationStateController : MonoBehaviour")
        lines.append("{")
        lines.append("    private Animator animator;")
        lines.append("")
        lines.append("    private void Awake()")
        lines.append("    {")
        lines.append("        animator = GetComponent<Animator>();")
        lines.append("    }")
        lines.append("")
        
        # Generate parameter setters
        for param_name, param_type in self.parameters.items():
            if param_type == "bool":
                lines.append(f"    public void Set{param_name}(bool value)")
                lines.append("    {")
                lines.append(f"        animator.SetBool(AnimatorParameters.{param_name}, value);")
                lines.append("    }")
                lines.append("")
            elif param_type == "float":
                lines.append(f"    public void Set{param_name}(float value)")
                lines.append("    {")
                lines.append(f"        animator.SetFloat(AnimatorParameters.{param_name}, value);")
                lines.append("    }")
                lines.append("")
            elif param_type == "int":
                lines.append(f"    public void Set{param_name}(int value)")
                lines.append("    {")
                lines.append(f"        animator.SetInteger(AnimatorParameters.{param_name}, value);")
                lines.append("    }")
                lines.append("")
            elif param_type == "trigger":
                lines.append(f"    public void Set{param_name}()")
                lines.append("    {")
                lines.append(f"        animator.SetTrigger(AnimatorParameters.{param_name});")
                lines.append("    }")
                lines.append("")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate_godot_animation_tree(self) -> str:
        """Generate Godot AnimationTree configuration."""
        lines = []
        
        lines.append("extends AnimationTree")
        lines.append("")
        lines.append("## Animation State Machine Controller")
        lines.append("")
        
        # Generate parameter exports
        for param_name, param_type in self.parameters.items():
            if param_type == "bool":
                lines.append(f"@export var {param_name}: bool = false")
            elif param_type == "float":
                lines.append(f"@export var {param_name}: float = 0.0")
            elif param_type == "int":
                lines.append(f"@export var {param_name}: int = 0")
        
        lines.append("")
        lines.append("@onready var state_machine: AnimationNodeStateMachinePlayback = get(\"parameters/playback\")")
        lines.append("")
        lines.append("func _ready():")
        lines.append("    active = true")
        lines.append("")
        
        # Generate state transition functions
        for state in self.states:
            lines.append(f"func travel_to_{state.name.lower()}():")
            lines.append(f'    state_machine.travel("{state.name}")')
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def create_platformer_state_machine() -> "AnimationStateMachine":
        """Create a platformer animation state machine."""
        asm = AnimationStateMachine()
        
        # Add parameters
        asm.add_parameter("IsGrounded", "bool")
        asm.add_parameter("Speed", "float")
        asm.add_parameter("IsAttacking", "bool")
        asm.add_parameter("IsHit", "trigger")
        
        # Add states
        asm.add_state(AnimationState("Idle", "Idle", speed=1.0, loop=True))
        asm.add_state(AnimationState("Walk", "Walk", speed=1.0, loop=True))
        asm.add_state(AnimationState("Run", "Run", speed=1.0, loop=True))
        asm.add_state(AnimationState("Jump", "Jump", speed=1.0, loop=False))
        asm.add_state(AnimationState("Fall", "Fall", speed=1.0, loop=True))
        asm.add_state(AnimationState("Attack", "Attack", speed=1.5, loop=False))
        asm.add_state(AnimationState("Hit", "Hit", speed=1.0, loop=False))
        
        # Add transitions
        asm.add_transition(AnimationTransition("Idle", "Walk", "Speed > 0.1"))
        asm.add_transition(AnimationTransition("Walk", "Idle", "Speed < 0.1"))
        asm.add_transition(AnimationTransition("Walk", "Run", "Speed > 5.0"))
        asm.add_transition(AnimationTransition("Run", "Walk", "Speed < 5.0"))
        asm.add_transition(AnimationTransition("Any", "Jump", "!IsGrounded"))
        asm.add_transition(AnimationTransition("Jump", "Fall", "!IsGrounded"))
        asm.add_transition(AnimationTransition("Fall", "Idle", "IsGrounded"))
        asm.add_transition(AnimationTransition("Any", "Attack", "IsAttacking"))
        asm.add_transition(AnimationTransition("Attack", "Idle", "!IsAttacking"))
        
        return asm
    
    @staticmethod
    def create_fps_state_machine() -> "AnimationStateMachine":
        """Create an FPS animation state machine."""
        asm = AnimationStateMachine()
        
        # Add parameters
        asm.add_parameter("Speed", "float")
        asm.add_parameter("IsAiming", "bool")
        asm.add_parameter("IsFiring", "bool")
        asm.add_parameter("IsReloading", "bool")
        
        # Add states
        asm.add_state(AnimationState("Idle", "Idle", speed=1.0, loop=True))
        asm.add_state(AnimationState("Walk", "Walk", speed=1.0, loop=True))
        asm.add_state(AnimationState("Run", "Run", speed=1.0, loop=True))
        asm.add_state(AnimationState("Aim", "Aim", speed=1.0, loop=True))
        asm.add_state(AnimationState("Fire", "Fire", speed=1.0, loop=False))
        asm.add_state(AnimationState("Reload", "Reload", speed=1.0, loop=False))
        
        # Add transitions
        asm.add_transition(AnimationTransition("Idle", "Walk", "Speed > 0.1"))
        asm.add_transition(AnimationTransition("Walk", "Idle", "Speed < 0.1"))
        asm.add_transition(AnimationTransition("Walk", "Run", "Speed > 5.0"))
        asm.add_transition(AnimationTransition("Run", "Walk", "Speed < 5.0"))
        asm.add_transition(AnimationTransition("Idle", "Aim", "IsAiming"))
        asm.add_transition(AnimationTransition("Aim", "Idle", "!IsAiming"))
        asm.add_transition(AnimationTransition("Any", "Fire", "IsFiring"))
        asm.add_transition(AnimationTransition("Fire", "Idle", "!IsFiring"))
        asm.add_transition(AnimationTransition("Any", "Reload", "IsReloading"))
        asm.add_transition(AnimationTransition("Reload", "Idle", "!IsReloading"))
        
        return asm


class AnimationController:
    """Animation controller utilities."""
    
    @staticmethod
    def generate_unity_animation_events() -> str:
        """Generate Unity animation event handler."""
        return '''using UnityEngine;
using System;

public class AnimationEventHandler : MonoBehaviour
{
    public event Action<string> OnAnimationEvent;
    public event Action OnAnimationComplete;
    
    [Header("Events")]
    public event Action OnFootstep;
    public event Action OnAttackStart;
    public event Action OnAttackEnd;
    public event Action OnHitFrame;
    
    // Called from Animation Events
    public void TriggerEvent(string eventName)
    {
        OnAnimationEvent?.Invoke(eventName);
        
        switch (eventName)
        {
            case "Footstep":
                OnFootstep?.Invoke();
                break;
            case "AttackStart":
                OnAttackStart?.Invoke();
                break;
            case "AttackEnd":
                OnAttackEnd?.Invoke();
                break;
            case "HitFrame":
                OnHitFrame?.Invoke();
                break;
        }
    }
    
    public void AnimationComplete()
    {
        OnAnimationComplete?.Invoke();
    }
}
'''
    
    @staticmethod
    def generate_godot_animation_events() -> str:
        """Generate Godot animation event handler."""
        return '''extends Node

## Animation Event Handler

signal animation_event(event_name: String)
signal animation_complete
signal footstep
signal attack_start
signal attack_end
signal hit_frame

func trigger_event(event_name: String):
    animation_event.emit(event_name)
    
    match event_name:
        "Footstep":
            footstep.emit()
        "AttackStart":
            attack_start.emit()
        "AttackEnd":
            attack_end.emit()
        "HitFrame":
            hit_frame.emit()

func animation_complete():
    animation_complete.emit()
'''
    
    @staticmethod
    def generate_unity_blend_tree_controller() -> str:
        """Generate Unity blend tree controller."""
        return '''using UnityEngine;

public class BlendTreeController : MonoBehaviour
{
    private Animator animator;
    
    [Header("Blend Parameters")]
    [SerializeField] private string blendXParameter = "BlendX";
    [SerializeField] private string blendYParameter = "BlendY";
    
    private void Awake()
    {
        animator = GetComponent<Animator>();
    }
    
    public void SetBlendValues(float x, float y)
    {
        animator.SetFloat(blendXParameter, x);
        animator.SetFloat(blendYParameter, y);
    }
    
    public void SetBlendFromDirection(Vector2 direction)
    {
        animator.SetFloat(blendXParameter, direction.x);
        animator.SetFloat(blendYParameter, direction.y);
    }
    
    public void SetBlendFromVelocity(Vector3 velocity, float maxSpeed)
    {
        float normalizedSpeed = velocity.magnitude / maxSpeed;
        Vector3 normalizedVelocity = velocity.normalized * normalizedSpeed;
        
        animator.SetFloat(blendXParameter, normalizedVelocity.x);
        animator.SetFloat(blendYParameter, normalizedVelocity.z);
    }
}
'''
    
    @staticmethod
    def generate_godot_blend_tree_controller() -> str:
        """Generate Godot blend tree controller."""
        return '''extends AnimationTree

## Blend Tree Controller

@export var blend_x_parameter: String = "blend_position"
@export var blend_y_parameter: String = "blend_position"

@onready var playback: AnimationNodeStateMachinePlayback = get("parameters/playback")

func set_blend_values(x: float, y: float):
    set("parameters/" + blend_x_parameter + "/blend_position", Vector2(x, y))

func set_blend_from_direction(direction: Vector2):
    set("parameters/" + blend_x_parameter + "/blend_position", direction)

func set_blend_from_velocity(velocity: Vector2, max_speed: float):
    var normalized_speed = velocity.length() / max_speed
    var normalized_velocity = velocity.normalized() * normalized_speed
    set("parameters/" + blend_x_parameter + "/blend_position", normalized_velocity)
'''
