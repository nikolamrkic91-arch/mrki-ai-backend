"""
Physics System Templates
Physics configurations and templates for different game types.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class PhysicsEngine(Enum):
    """Supported physics engines."""
    UNITY_PHYSICS = "unity_physics"
    UNITY_PHYSICS2D = "unity_physics2d"
    UNREAL_CHAOS = "unreal_chaos"
    UNREAL_CHAOS2D = "unreal_chaos2d"
    GODOT_PHYSICS = "godot_physics"
    GODOT_PHYSICS2D = "godot_physics2d"


class PhysicsPreset(Enum):
    """Physics presets for different game types."""
    ARCADE = "arcade"
    REALISTIC = "realistic"
    PLATFORMER = "platformer"
    SPACE = "space"
    UNDERWATER = "underwater"
    LOW_GRAVITY = "low_gravity"


@dataclass
class PhysicsConfig:
    """Physics configuration for a game."""
    engine: PhysicsEngine
    preset: PhysicsPreset
    gravity: float = -9.81
    time_scale: float = 1.0
    fixed_timestep: float = 0.02
    max_substeps: int = 3
    solver_iterations: int = 6
    sleep_threshold: float = 0.005
    default_material: Dict[str, float] = field(default_factory=dict)
    layers: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine": self.engine.value,
            "preset": self.preset.value,
            "gravity": self.gravity,
            "time_scale": self.time_scale,
            "fixed_timestep": self.fixed_timestep,
            "max_substeps": self.max_substeps,
            "solver_iterations": self.solver_iterations,
            "sleep_threshold": self.sleep_threshold,
            "default_material": self.default_material,
            "layers": self.layers
        }


class PhysicsTemplates:
    """Collection of physics system templates."""
    
    # Unity Physics2D Presets
    UNITY_2D_PRESETS = {
        PhysicsPreset.ARCADE: {
            "gravity": -15.0,
            "default_material": {
                "friction": 0.0,
                "bounciness": 0.0
            }
        },
        PhysicsPreset.PLATFORMER: {
            "gravity": -25.0,
            "default_material": {
                "friction": 0.4,
                "bounciness": 0.0
            }
        },
        PhysicsPreset.REALISTIC: {
            "gravity": -9.81,
            "default_material": {
                "friction": 0.5,
                "bounciness": 0.1
            }
        },
        PhysicsPreset.SPACE: {
            "gravity": 0.0,
            "default_material": {
                "friction": 0.0,
                "bounciness": 0.5
            }
        },
        PhysicsPreset.LOW_GRAVITY: {
            "gravity": -3.0,
            "default_material": {
                "friction": 0.3,
                "bounciness": 0.2
            }
        }
    }
    
    # Unity Physics3D Presets
    UNITY_3D_PRESETS = {
        PhysicsPreset.ARCADE: {
            "gravity": -15.0,
            "default_material": {
                "dynamic_friction": 0.0,
                "static_friction": 0.0,
                "bounciness": 0.0
            }
        },
        PhysicsPreset.PLATFORMER: {
            "gravity": -20.0,
            "default_material": {
                "dynamic_friction": 0.6,
                "static_friction": 0.6,
                "bounciness": 0.0
            }
        },
        PhysicsPreset.REALISTIC: {
            "gravity": -9.81,
            "default_material": {
                "dynamic_friction": 0.5,
                "static_friction": 0.5,
                "bounciness": 0.1
            }
        },
        PhysicsPreset.SPACE: {
            "gravity": 0.0,
            "default_material": {
                "dynamic_friction": 0.0,
                "static_friction": 0.0,
                "bounciness": 0.5
            }
        },
        PhysicsPreset.UNDERWATER: {
            "gravity": -2.0,
            "default_material": {
                "dynamic_friction": 0.8,
                "static_friction": 0.8,
                "bounciness": 0.0
            }
        }
    }
    
    # Godot Physics2D Presets
    GODOT_2D_PRESETS = {
        PhysicsPreset.ARCADE: {
            "gravity": Vector2(0, 1500),
            "default_linear_damp": 0.0,
            "default_angular_damp": 0.0
        },
        PhysicsPreset.PLATFORMER: {
            "gravity": Vector2(0, 2500),
            "default_linear_damp": 0.1,
            "default_angular_damp": 0.1
        },
        PhysicsPreset.REALISTIC: {
            "gravity": Vector2(0, 980),
            "default_linear_damp": 0.0,
            "default_angular_damp": 0.0
        },
        PhysicsPreset.SPACE: {
            "gravity": Vector2(0, 0),
            "default_linear_damp": 0.0,
            "default_angular_damp": 0.0
        }
    }
    
    # Godot Physics3D Presets
    GODOT_3D_PRESETS = {
        PhysicsPreset.ARCADE: {
            "gravity": Vector3(0, -15, 0),
            "default_linear_damp": 0.0,
            "default_angular_damp": 0.0
        },
        PhysicsPreset.PLATFORMER: {
            "gravity": Vector3(0, -25, 0),
            "default_linear_damp": 0.1,
            "default_angular_damp": 0.1
        },
        PhysicsPreset.REALISTIC: {
            "gravity": Vector3(0, -9.81, 0),
            "default_linear_damp": 0.0,
            "default_angular_damp": 0.0
        },
        PhysicsPreset.SPACE: {
            "gravity": Vector3(0, 0, 0),
            "default_linear_damp": 0.0,
            "default_angular_damp": 0.0
        }
    }
    
    @staticmethod
    def get_unity_2d_config(preset: PhysicsPreset = PhysicsPreset.PLATFORMER) -> Dict[str, Any]:
        """Get Unity 2D physics configuration."""
        config = PhysicsTemplates.UNITY_2D_PRESETS.get(preset, PhysicsTemplates.UNITY_2D_PRESETS[PhysicsPreset.PLATFORMER])
        
        return {
            "gravity": config["gravity"],
            "default_contact_offset": 0.01,
            "sleep_threshold": 0.005,
            "queries_hit_triggers": False,
            "queries_start_in_colliders": False,
            "callbacks_on_disable": True,
            "reuse_collision_callbacks": False,
            "auto_sync_transforms": False,
            "default_material": config["default_material"],
            "velocity_iterations": 8,
            "position_iterations": 3
        }
    
    @staticmethod
    def get_unity_3d_config(preset: PhysicsPreset = PhysicsPreset.REALISTIC) -> Dict[str, Any]:
        """Get Unity 3D physics configuration."""
        config = PhysicsTemplates.UNITY_3D_PRESETS.get(preset, PhysicsTemplates.UNITY_3D_PRESETS[PhysicsPreset.REALISTIC])
        
        return {
            "gravity": Vector3(0, config["gravity"], 0),
            "default_contact_offset": 0.001,
            "sleep_threshold": 0.005,
            "queries_hit_triggers": False,
            "queries_hit_backfaces": False,
            "bounce_threshold": 2.0,
            "default_max_angular_speed": 7.0,
            "default_max_depentration_velocity": 10.0,
            "default_solver_iterations": 6,
            "default_solver_velocity_iterations": 1,
            "default_material": config["default_material"],
            "auto_simulation": True,
            "auto_sync_transforms": False,
            "reuse_collision_callbacks": False,
            "interpolate_poses": True,
            "enable_enhanced_internal_edge_removals": False
        }
    
    @staticmethod
    def get_godot_2d_config(preset: PhysicsPreset = PhysicsPreset.PLATFORMER) -> Dict[str, Any]:
        """Get Godot 2D physics configuration."""
        config = PhysicsTemplates.GODOT_2D_PRESETS.get(preset, PhysicsTemplates.GODOT_2D_PRESETS[PhysicsPreset.PLATFORMER])
        
        return {
            "physics_engine": "DEFAULT",
            "gravity": config["gravity"],
            "default_linear_damp": config["default_linear_damp"],
            "default_angular_damp": config["default_angular_damp"],
            "default_gravity_vector": Vector2(0, 1),
            "sleep_threshold_linear": 2.0,
            "sleep_threshold_angular": 8.0 / 180.0 * 3.14159,  # 8 degrees in radians
            "time_before_sleep": 0.5,
            "solver": {"solver_iterations": 8, "solver_contact_max_allowed_penetration": 0.3}
        }
    
    @staticmethod
    def get_godot_3d_config(preset: PhysicsPreset = PhysicsPreset.REALISTIC) -> Dict[str, Any]:
        """Get Godot 3D physics configuration."""
        config = PhysicsTemplates.GODOT_3D_PRESETS.get(preset, PhysicsTemplates.GODOT_3D_PRESETS[PhysicsPreset.REALISTIC])
        
        return {
            "physics_engine": "DEFAULT",
            "gravity": config["gravity"],
            "default_linear_damp": config["default_linear_damp"],
            "default_angular_damp": config["default_angular_damp"],
            "default_gravity_vector": Vector3(0, -1, 0),
            "sleep_threshold_linear": 0.1,
            "sleep_threshold_angular": 8.0 / 180.0 * 3.14159,
            "time_before_sleep": 0.5,
            "solver": {"solver_iterations": 8, "solver_contact_max_allowed_penetration": 0.01}
        }
    
    @staticmethod
    def generate_unity_physics2d_manager(preset: PhysicsPreset = PhysicsPreset.PLATFORMER) -> str:
        """Generate Unity 2D physics manager script."""
        config = PhysicsTemplates.get_unity_2d_config(preset)
        
        return f'''using UnityEngine;

public class Physics2DManager : MonoBehaviour
{{
    [Header("Gravity Settings")]
    [SerializeField] private Vector2 gravity = new Vector2(0f, {config["gravity"]}f);
    
    [Header("Simulation Settings")]
    [SerializeField] private int velocityIterations = 8;
    [SerializeField] private int positionIterations = 3;
    [SerializeField] private float sleepThreshold = {config["sleep_threshold"]}f;
    
    [Header("Material Settings")]
    [SerializeField] private PhysicsMaterial2D defaultMaterial;
    
    private void Awake()
    {{
        ApplySettings();
    }}
    
    private void ApplySettings()
    {{
        Physics2D.gravity = gravity;
        Physics2D.velocityIterations = velocityIterations;
        Physics2D.positionIterations = positionIterations;
        Physics2D.sleepThreshold = sleepThreshold;
        
        if (defaultMaterial != null)
        {{
            defaultMaterial.friction = {config["default_material"]["friction"]}f;
            defaultMaterial.bounciness = {config["default_material"]["bounciness"]}f;
        }}
    }}
    
    public void SetGravity(Vector2 newGravity)
    {{
        gravity = newGravity;
        Physics2D.gravity = gravity;
    }}
    
    public void SetTimeScale(float scale)
    {{
        Time.timeScale = scale;
    }}
}}
'''
    
    @staticmethod
    def generate_unity_physics3d_manager(preset: PhysicsPreset = PhysicsPreset.REALISTIC) -> str:
        """Generate Unity 3D physics manager script."""
        config = PhysicsTemplates.get_unity_3d_config(preset)
        
        return f'''using UnityEngine;

public class Physics3DManager : MonoBehaviour
{{
    [Header("Gravity Settings")]
    [SerializeField] private Vector3 gravity = new Vector3(0f, {config["gravity"].y}f, 0f);
    
    [Header("Simulation Settings")]
    [SerializeField] private int solverIterations = 6;
    [SerializeField] private int solverVelocityIterations = 1;
    [SerializeField] private float sleepThreshold = {config["sleep_threshold"]}f;
    [SerializeField] private float defaultContactOffset = {config["default_contact_offset"]}f;
    
    [Header("Material Settings")]
    [SerializeField] private PhysicMaterial defaultMaterial;
    
    private void Awake()
    {{
        ApplySettings();
    }}
    
    private void ApplySettings()
    {{
        Physics.gravity = gravity;
        Physics.defaultSolverIterations = solverIterations;
        Physics.defaultSolverVelocityIterations = solverVelocityIterations;
        Physics.sleepThreshold = sleepThreshold;
        Physics.defaultContactOffset = defaultContactOffset;
        
        if (defaultMaterial != null)
        {{
            defaultMaterial.dynamicFriction = {config["default_material"]["dynamic_friction"]}f;
            defaultMaterial.staticFriction = {config["default_material"]["static_friction"]}f;
            defaultMaterial.bounciness = {config["default_material"]["bounciness"]}f;
        }}
    }}
    
    public void SetGravity(Vector3 newGravity)
    {{
        gravity = newGravity;
        Physics.gravity = gravity;
    }}
    
    public void SetTimeScale(float scale)
    {{
        Time.timeScale = scale;
    }}
}}
'''
    
    @staticmethod
    def generate_godot_physics2d_manager(preset: PhysicsPreset = PhysicsPreset.PLATFORMER) -> str:
        """Generate Godot 2D physics manager script."""
        config = PhysicsTemplates.get_godot_2d_config(preset)
        
        return f'''extends Node

## 2D Physics Manager

@export var gravity: Vector2 = Vector2(0, {config["gravity"].y})
@export var default_linear_damp: float = {config["default_linear_damp"]}
@export var default_angular_damp: float = {config["default_angular_damp"]}
@export var sleep_threshold_linear: float = {config["sleep_threshold_linear"]}
@export var sleep_threshold_angular: float = {config["sleep_threshold_angular"]}

func _ready():
    apply_settings()

func apply_settings():
    ProjectSettings.set_setting("physics/2d/default_gravity", gravity)
    ProjectSettings.set_setting("physics/2d/default_linear_damp", default_linear_damp)
    ProjectSettings.set_setting("physics/2d/default_angular_damp", default_angular_damp)
    ProjectSettings.set_setting("physics/2d/sleep_threshold_linear", sleep_threshold_linear)
    ProjectSettings.set_setting("physics/2d/sleep_threshold_angular", sleep_threshold_angular)

func set_gravity(new_gravity: Vector2):
    gravity = new_gravity
    ProjectSettings.set_setting("physics/2d/default_gravity", gravity)

func set_time_scale(scale: float):
    Engine.time_scale = scale
'''
    
    @staticmethod
    def generate_godot_physics3d_manager(preset: PhysicsPreset = PhysicsPreset.REALISTIC) -> str:
        """Generate Godot 3D physics manager script."""
        config = PhysicsTemplates.get_godot_3d_config(preset)
        
        return f'''extends Node

## 3D Physics Manager

@export var gravity: Vector3 = Vector3(0, {config["gravity"].y}, 0)
@export var default_linear_damp: float = {config["default_linear_damp"]}
@export var default_angular_damp: float = {config["default_angular_damp"]}
@export var sleep_threshold_linear: float = {config["sleep_threshold_linear"]}
@export var sleep_threshold_angular: float = {config["sleep_threshold_angular"]}

func _ready():
    apply_settings()

func apply_settings():
    ProjectSettings.set_setting("physics/3d/default_gravity", gravity)
    ProjectSettings.set_setting("physics/3d/default_linear_damp", default_linear_damp)
    ProjectSettings.set_setting("physics/3d/default_angular_damp", default_angular_damp)
    ProjectSettings.set_setting("physics/3d/sleep_threshold_linear", sleep_threshold_linear)
    ProjectSettings.set_setting("physics/3d/sleep_threshold_angular", sleep_threshold_angular)

func set_gravity(new_gravity: Vector3):
    gravity = new_gravity
    ProjectSettings.set_setting("physics/3d/default_gravity", gravity)

func set_time_scale(scale: float):
    Engine.time_scale = scale
'''


# Helper class for Vector2
class Vector2:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __repr__(self):
        return f"Vector2({self.x}, {self.y})"


# Helper class for Vector3
class Vector3:
    def __init__(self, x: float, y: float, z: float = 0):
        self.x = x
        self.y = y
        self.z = z
    
    def __repr__(self):
        return f"Vector3({self.x}, {self.y}, {self.z})"
