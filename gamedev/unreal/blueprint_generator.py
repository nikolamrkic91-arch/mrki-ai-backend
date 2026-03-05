"""
Blueprint Generator for Unreal Engine
Generates Blueprint asset definitions and node graphs.
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class BlueprintType(Enum):
    """Blueprint class types."""
    ACTOR = "Actor"
    PAWN = "Pawn"
    CHARACTER = "Character"
    PLAYER_CONTROLLER = "PlayerController"
    GAME_MODE = "GameMode"
    GAME_STATE = "GameState"
    PLAYER_STATE = "PlayerState"
    HUD = "HUD"
    ACTOR_COMPONENT = "ActorComponent"
    SCENE_COMPONENT = "SceneComponent"
    OBJECT = "Object"
    ENUM = "Enum"
    STRUCT = "Struct"
    INTERFACE = "Interface"
    LIBRARY = "BlueprintFunctionLibrary"


class PinType(Enum):
    """Blueprint pin types."""
    EXEC = "exec"
    BOOLEAN = "bool"
    INTEGER = "int"
    FLOAT = "float"
    STRING = "string"
    TEXT = "text"
    NAME = "name"
    VECTOR = "vector"
    ROTATOR = "rotator"
    TRANSFORM = "transform"
    OBJECT = "object"
    CLASS = "class"
    STRUCT = "struct"
    ENUM = "enum"
    ARRAY = "array"
    MAP = "map"
    SET = "set"


@dataclass
class BlueprintPin:
    """Represents a Blueprint node pin."""
    name: str
    pin_type: PinType
    direction: str = "input"  # input, output
    default_value: Optional[Any] = None
    connected_to: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.pin_type.value,
            "direction": self.direction,
            "default_value": self.default_value,
            "connected_to": self.connected_to
        }


@dataclass
class BlueprintNode:
    """Represents a Blueprint graph node."""
    node_id: str
    node_type: str
    function_name: Optional[str] = None
    pins: List[BlueprintPin] = field(default_factory=list)
    position_x: float = 0
    position_y: float = 0
    comment: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.node_id,
            "type": self.node_type,
            "function_name": self.function_name,
            "pins": [p.to_dict() for p in self.pins],
            "position": {"x": self.position_x, "y": self.position_y},
            "comment": self.comment
        }


@dataclass
class BlueprintVariable:
    """Represents a Blueprint variable."""
    name: str
    var_type: str
    default_value: Optional[Any] = None
    is_instance_editable: bool = True
    is_replicated: bool = False
    tooltip: Optional[str] = None
    category: str = "Default"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.var_type,
            "default_value": self.default_value,
            "instance_editable": self.is_instance_editable,
            "replicated": self.is_replicated,
            "tooltip": self.tooltip,
            "category": self.category
        }


@dataclass
class BlueprintFunction:
    """Represents a Blueprint function."""
    name: str
    inputs: List[BlueprintPin] = field(default_factory=list)
    outputs: List[BlueprintPin] = field(default_factory=list)
    nodes: List[BlueprintNode] = field(default_factory=list)
    is_pure: bool = False
    is_const: bool = False
    access: str = "public"  # public, protected, private
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "inputs": [p.to_dict() for p in self.inputs],
            "outputs": [p.to_dict() for p in self.outputs],
            "nodes": [n.to_dict() for n in self.nodes],
            "is_pure": self.is_pure,
            "is_const": self.is_const,
            "access": self.access
        }


class BlueprintGenerator:
    """Generator for Unreal Engine Blueprints."""
    
    def __init__(self):
        self.blueprint_name: str = ""
        self.blueprint_type: BlueprintType = BlueprintType.ACTOR
        self.parent_class: str = ""
        self.variables: List[BlueprintVariable] = []
        self.functions: List[BlueprintFunction] = []
        self.event_graph: List[BlueprintNode] = []
        self.components: List[Dict[str, Any]] = []
        
    def set_blueprint(self, name: str, bp_type: BlueprintType = BlueprintType.ACTOR):
        """Set the Blueprint name and type."""
        self.blueprint_name = name
        self.blueprint_type = bp_type
        self.parent_class = bp_type.value
        return self
    
    def set_parent_class(self, parent: str):
        """Set the parent class."""
        self.parent_class = parent
        return self
    
    def add_variable(self, var: BlueprintVariable):
        """Add a variable to the Blueprint."""
        self.variables.append(var)
        return self
    
    def add_function(self, func: BlueprintFunction):
        """Add a function to the Blueprint."""
        self.functions.append(func)
        return self
    
    def add_event_graph_node(self, node: BlueprintNode):
        """Add a node to the event graph."""
        self.event_graph.append(node)
        return self
    
    def add_component(self, name: str, component_type: str, properties: Dict[str, Any] = None):
        """Add a component to the Blueprint."""
        self.components.append({
            "name": name,
            "type": component_type,
            "properties": properties or {}
        })
        return self
    
    def generate_json(self) -> str:
        """Generate Blueprint as JSON."""
        blueprint = {
            "name": self.blueprint_name,
            "type": self.blueprint_type.value,
            "parent_class": self.parent_class,
            "variables": [v.to_dict() for v in self.variables],
            "functions": [f.to_dict() for f in self.functions],
            "event_graph": [n.to_dict() for n in self.event_graph],
            "components": self.components
        }
        
        return json.dumps(blueprint, indent=2)
    
    def generate_markdown_documentation(self) -> str:
        """Generate Markdown documentation for the Blueprint."""
        lines = []
        
        lines.append(f"# {self.blueprint_name}")
        lines.append("")
        lines.append(f"**Type:** {self.blueprint_type.value}")
        lines.append(f"**Parent:** {self.parent_class}")
        lines.append("")
        
        # Components
        if self.components:
            lines.append("## Components")
            lines.append("")
            for comp in self.components:
                lines.append(f"- **{comp['name']}**: {comp['type']}")
            lines.append("")
        
        # Variables
        if self.variables:
            lines.append("## Variables")
            lines.append("")
            lines.append("| Name | Type | Category | Editable | Replicated |")
            lines.append("|------|------|----------|----------|------------|")
            for var in self.variables:
                editable = "Yes" if var.is_instance_editable else "No"
                replicated = "Yes" if var.is_replicated else "No"
                lines.append(f"| {var.name} | {var.var_type} | {var.category} | {editable} | {replicated} |")
            lines.append("")
        
        # Functions
        if self.functions:
            lines.append("## Functions")
            lines.append("")
            for func in self.functions:
                lines.append(f"### {func.name}")
                lines.append("")
                
                if func.inputs:
                    lines.append("**Inputs:**")
                    for inp in func.inputs:
                        lines.append(f"- {inp.name}: {inp.pin_type.value}")
                    lines.append("")
                
                if func.outputs:
                    lines.append("**Outputs:**")
                    for out in func.outputs:
                        lines.append(f"- {out.name}: {out.pin_type.value}")
                    lines.append("")
                
                lines.append(f"**Access:** {func.access}")
                lines.append(f"**Pure:** {'Yes' if func.is_pure else 'No'}")
                lines.append("")
        
        return "\n".join(lines)
    
    # Preset Blueprint generators
    
    def generate_fps_character(self, name: str = "BP_FPSCharacter") -> Dict[str, str]:
        """Generate FPS character Blueprint."""
        self.set_blueprint(name, BlueprintType.CHARACTER)
        
        # Add components
        self.add_component("Camera", "CameraComponent", {
            "relative_location": {"x": 0, "y": 0, "z": 64},
            "use_pawn_control_rotation": True
        })
        
        self.add_component("GunMesh", "SkeletalMeshComponent", {
            "attach_to": "Camera",
            "relative_location": {"x": 30, "y": 14, "z": -12}
        })
        
        # Add variables
        self.add_variable(BlueprintVariable(
            name="MaxHealth",
            var_type="float",
            default_value=100.0,
            category="Health",
            tooltip="Maximum health"
        ))
        
        self.add_variable(BlueprintVariable(
            name="CurrentHealth",
            var_type="float",
            default_value=100.0,
            category="Health",
            tooltip="Current health"
        ))
        
        self.add_variable(BlueprintVariable(
            name="WalkSpeed",
            var_type="float",
            default_value=600.0,
            category="Movement",
            tooltip="Walking speed"
        ))
        
        self.add_variable(BlueprintVariable(
            name="SprintSpeed",
            var_type="float",
            default_value=1000.0,
            category="Movement",
            tooltip="Sprinting speed"
        ))
        
        # Add functions
        fire_func = BlueprintFunction(
            name="Fire",
            access="public"
        )
        
        fire_func.nodes.append(BlueprintNode(
            node_id="begin",
            node_type="FunctionEntry",
            position_x=0,
            position_y=0
        ))
        
        fire_func.nodes.append(BlueprintNode(
            node_id="line_trace",
            node_type="LineTraceByChannel",
            position_x=200,
            position_y=0,
            pins=[
                BlueprintPin("Start", PinType.VECTOR, "input"),
                BlueprintPin("End", PinType.VECTOR, "input"),
                BlueprintPin("OutHit", PinType.STRUCT, "output")
            ]
        ))
        
        self.add_function(fire_func)
        
        return {
            "json": self.generate_json(),
            "documentation": self.generate_markdown_documentation()
        }
    
    def generate_game_mode(self, name: str = "BP_GameMode") -> Dict[str, str]:
        """Generate Game Mode Blueprint."""
        self.set_blueprint(name, BlueprintType.GAME_MODE)
        
        # Add variables
        self.add_variable(BlueprintVariable(
            name="MatchDuration",
            var_type="float",
            default_value=300.0,
            category="Game Rules",
            tooltip="Match duration in seconds"
        ))
        
        self.add_variable(BlueprintVariable(
            name="MaxPlayers",
            var_type="int",
            default_value=16,
            category="Game Rules",
            tooltip="Maximum number of players"
        ))
        
        self.add_variable(BlueprintVariable(
            name="ScoreToWin",
            var_type="int",
            default_value=50,
            category="Game Rules",
            tooltip="Score required to win"
        ))
        
        # Add functions
        start_match_func = BlueprintFunction(
            name="StartMatch",
            access="public"
        )
        
        start_match_func.nodes.append(BlueprintNode(
            node_id="begin",
            node_type="FunctionEntry",
            position_x=0,
            position_y=0
        ))
        
        self.add_function(start_match_func)
        
        return {
            "json": self.generate_json(),
            "documentation": self.generate_markdown_documentation()
        }
    
    def generate_interactable_object(self, name: str = "BP_Interactable") -> Dict[str, str]:
        """Generate interactable object Blueprint."""
        self.set_blueprint(name, BlueprintType.ACTOR)
        
        # Add components
        self.add_component("Mesh", "StaticMeshComponent")
        
        self.add_component("InteractionWidget", "WidgetComponent", {
            "widget_class": "WBP_InteractionPrompt",
            "relative_location": {"x": 0, "y": 0, "z": 100},
            "visibility": False
        })
        
        # Add variables
        self.add_variable(BlueprintVariable(
            name="InteractionPrompt",
            var_type="text",
            default_value="Press E to Interact",
            category="Interaction",
            tooltip="Text shown when player can interact"
        ))
        
        self.add_variable(BlueprintVariable(
            name="CanInteract",
            var_type="bool",
            default_value=True,
            category="Interaction",
            tooltip="Whether this object can be interacted with"
        ))
        
        # Add functions
        interact_func = BlueprintFunction(
            name="OnInteract",
            inputs=[BlueprintPin("InteractingActor", PinType.OBJECT, "input")],
            access="public"
        )
        
        interact_func.nodes.append(BlueprintNode(
            node_id="begin",
            node_type="FunctionEntry",
            position_x=0,
            position_y=0
        ))
        
        self.add_function(interact_func)
        
        return {
            "json": self.generate_json(),
            "documentation": self.generate_markdown_documentation()
        }
    
    def generate_health_pickup(self, name: str = "BP_HealthPickup") -> Dict[str, str]:
        """Generate health pickup Blueprint."""
        self.set_blueprint(name, BlueprintType.ACTOR)
        
        # Add components
        self.add_component("Mesh", "StaticMeshComponent")
        
        self.add_component("Collision", "SphereComponent", {
            "sphere_radius": 50.0,
            "collision_profile": "OverlapAllDynamic"
        })
        
        # Add variables
        self.add_variable(BlueprintVariable(
            name="HealAmount",
            var_type="float",
            default_value=25.0,
            category="Pickup",
            tooltip="Amount of health to restore"
        ))
        
        self.add_variable(BlueprintVariable(
            name="PickupSound",
            var_type="sound",
            category="Pickup",
            tooltip="Sound played on pickup"
        ))
        
        self.add_variable(BlueprintVariable(
            name="PickupEffect",
            var_type="particle_system",
            category="Pickup",
            tooltip="Particle effect on pickup"
        ))
        
        return {
            "json": self.generate_json(),
            "documentation": self.generate_markdown_documentation()
        }
    
    def generate_door(self, name: str = "BP_Door") -> Dict[str, str]:
        """Generate interactive door Blueprint."""
        self.set_blueprint(name, BlueprintType.ACTOR)
        
        # Add components
        self.add_component("DoorFrame", "StaticMeshComponent")
        
        self.add_component("DoorMesh", "StaticMeshComponent", {
            "attach_to": "DoorFrame"
        })
        
        self.add_component("InteractionZone", "BoxComponent", {
            "relative_location": {"x": 0, "y": 100, "z": 0},
            "box_extent": {"x": 100, "y": 100, "z": 100}
        })
        
        # Add variables
        self.add_variable(BlueprintVariable(
            name="IsOpen",
            var_type="bool",
            default_value=False,
            category="Door State",
            tooltip="Whether the door is currently open"
        ))
        
        self.add_variable(BlueprintVariable(
            name="IsLocked",
            var_type="bool",
            default_value=False,
            category="Door State",
            tooltip="Whether the door is locked"
        ))
        
        self.add_variable(BlueprintVariable(
            name="OpenAngle",
            var_type="float",
            default_value=90.0,
            category="Door Settings",
            tooltip="Angle to rotate when opening"
        ))
        
        self.add_variable(BlueprintVariable(
            name="OpenSpeed",
            var_type="float",
            default_value=2.0,
            category="Door Settings",
            tooltip="Speed of door opening animation"
        ))
        
        # Add functions
        toggle_func = BlueprintFunction(
            name="ToggleDoor",
            access="public"
        )
        
        toggle_func.nodes.append(BlueprintNode(
            node_id="begin",
            node_type="FunctionEntry",
            position_x=0,
            position_y=0
        ))
        
        self.add_function(toggle_func)
        
        return {
            "json": self.generate_json(),
            "documentation": self.generate_markdown_documentation()
        }
    
    def generate_enemy_ai(self, name: str = "BP_EnemyAI") -> Dict[str, str]:
        """Generate enemy AI Blueprint."""
        self.set_blueprint(name, BlueprintType.CHARACTER)
        
        # Add AI components
        self.add_component("AIController", "AIController")
        
        # Add variables
        self.add_variable(BlueprintVariable(
            name="Health",
            var_type="float",
            default_value=100.0,
            category="Stats",
            tooltip="Enemy health"
        ))
        
        self.add_variable(BlueprintVariable(
            name="Damage",
            var_type="float",
            default_value=10.0,
            category="Stats",
            tooltip="Damage dealt per attack"
        ))
        
        self.add_variable(BlueprintVariable(
            name="DetectionRange",
            var_type="float",
            default_value=1000.0,
            category="AI",
            tooltip="Range to detect player"
        ))
        
        self.add_variable(BlueprintVariable(
            name="AttackRange",
            var_type="float",
            default_value=150.0,
            category="AI",
            tooltip="Range to attack player"
        ))
        
        self.add_variable(BlueprintVariable(
            name="MoveSpeed",
            var_type="float",
            default_value=300.0,
            category="AI",
            tooltip="Movement speed"
        ))
        
        return {
            "json": self.generate_json(),
            "documentation": self.generate_markdown_documentation()
        }
    
    def generate_inventory_component(self, name: str = "BP_InventoryComponent") -> Dict[str, str]:
        """Generate inventory component Blueprint."""
        self.set_blueprint(name, BlueprintType.ACTOR_COMPONENT)
        
        # Add variables
        self.add_variable(BlueprintVariable(
            name="MaxSlots",
            var_type="int",
            default_value=20,
            category="Inventory",
            tooltip="Maximum inventory slots"
        ))
        
        self.add_variable(BlueprintVariable(
            name="Items",
            var_type="array",
            default_value=[],
            category="Inventory",
            tooltip="Current items in inventory"
        ))
        
        # Add functions
        add_item_func = BlueprintFunction(
            name="AddItem",
            inputs=[BlueprintPin("Item", PinType.OBJECT, "input")],
            outputs=[BlueprintPin("Success", PinType.BOOLEAN, "output")],
            access="public"
        )
        
        add_item_func.nodes.append(BlueprintNode(
            node_id="begin",
            node_type="FunctionEntry",
            position_x=0,
            position_y=0
        ))
        
        self.add_function(add_item_func)
        
        remove_item_func = BlueprintFunction(
            name="RemoveItem",
            inputs=[BlueprintPin("Item", PinType.OBJECT, "input")],
            outputs=[BlueprintPin("Success", PinType.BOOLEAN, "output")],
            access="public"
        )
        
        self.add_function(remove_item_func)
        
        return {
            "json": self.generate_json(),
            "documentation": self.generate_markdown_documentation()
        }
