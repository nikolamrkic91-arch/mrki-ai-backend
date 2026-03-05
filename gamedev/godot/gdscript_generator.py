"""
GDScript Generator for Godot Engine
Generates GDScript code for Godot game development.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class GDScriptType(Enum):
    """GDScript node types."""
    NODE = "Node"
    NODE2D = "Node2D"
    NODE3D = "Node3D"
    CHARACTER_BODY2D = "CharacterBody2D"
    CHARACTER_BODY3D = "CharacterBody3D"
    RIGID_BODY2D = "RigidBody2D"
    RIGID_BODY3D = "RigidBody3D"
    STATIC_BODY2D = "StaticBody2D"
    STATIC_BODY3D = "StaticBody3D"
    AREA2D = "Area2D"
    AREA3D = "Area3D"
    ANIMATED_SPRITE2D = "AnimatedSprite2D"
    SPRITE2D = "Sprite2D"
    SPRITE3D = "Sprite3D"
    CAMERA2D = "Camera2D"
    CAMERA3D = "Camera3D"
    CONTROL = "Control"
    BUTTON = "Button"
    LABEL = "Label"
    RICH_TEXT_LABEL = "RichTextLabel"
    PROGRESS_BAR = "ProgressBar"
    TIMER = "Timer"
    AUDIO_STREAM_PLAYER = "AudioStreamPlayer"
    ANIMATION_PLAYER = "AnimationPlayer"
    PARTICLES2D = "GPUParticles2D"
    TILE_MAP = "TileMap"
    NAVIGATION_AGENT2D = "NavigationAgent2D"
    NAVIGATION_AGENT3D = "NavigationAgent3D"


class ExportType(Enum):
    """GDScript export types."""
    INT = "int"
    FLOAT = "float"
    STRING = "String"
    BOOL = "bool"
    VECTOR2 = "Vector2"
    VECTOR3 = "Vector3"
    COLOR = "Color"
    ARRAY = "Array"
    DICTIONARY = "Dictionary"
    NODE_PATH = "NodePath"
    RESOURCE = "Resource"
    TEXTURE = "Texture"
    AUDIO_STREAM = "AudioStream"
    PACKED_SCENE = "PackedScene"


@dataclass
class GDScriptVariable:
    """Represents a GDScript variable."""
    name: str
    var_type: Optional[str] = None
    default_value: Optional[str] = None
    is_export: bool = False
    export_type: Optional[ExportType] = None
    is_onready: bool = False
    is_const: bool = False
    is_static: bool = False
    documentation: Optional[str] = None
    
    def generate(self) -> str:
        lines = []
        
        if self.documentation:
            lines.append(f"## {self.documentation}")
        
        if self.is_export and self.export_type:
            if self.default_value:
                lines.append(f"@export var {self.name}: {self.export_type.value} = {self.default_value}")
            else:
                lines.append(f"@export var {self.name}: {self.export_type.value}")
        elif self.is_onready:
            lines.append(f"@onready var {self.name}: {self.var_type or 'Node'}")
        elif self.is_const:
            lines.append(f"const {self.name}: {self.var_type or 'Variant'} = {self.default_value}")
        elif self.is_static:
            lines.append(f"static var {self.name}: {self.var_type or 'Variant'}")
        elif self.var_type:
            if self.default_value:
                lines.append(f"var {self.name}: {self.var_type} = {self.default_value}")
            else:
                lines.append(f"var {self.name}: {self.var_type}")
        else:
            if self.default_value:
                lines.append(f"var {self.name} = {self.default_value}")
            else:
                lines.append(f"var {self.name}")
        
        return "\n".join(lines)


@dataclass
class GDScriptFunction:
    """Represents a GDScript function."""
    name: str
    parameters: List[tuple] = field(default_factory=list)
    return_type: Optional[str] = None
    is_static: bool = False
    is_virtual: bool = False
    body: List[str] = field(default_factory=list)
    documentation: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    
    def generate(self) -> str:
        lines = []
        
        # Decorators
        for decorator in self.decorators:
            lines.append(f"@{decorator}")
        
        if self.documentation:
            lines.append(f"## {self.documentation}")
        
        # Function signature
        static_keyword = "static " if self.is_static else ""
        params = ", ".join([f"{p[0]}: {p[1]}" if len(p) > 1 else p[0] for p in self.parameters])
        
        if self.return_type:
            lines.append(f"{static_keyword}func {self.name}({params}) -> {self.return_type}:")
        else:
            lines.append(f"{static_keyword}func {self.name}({params}):")
        
        # Function body
        if self.body:
            for line in self.body:
                lines.append(f"    {line}")
        else:
            lines.append("    pass")
        
        return "\n".join(lines)


@dataclass
class GDScriptSignal:
    """Represents a GDScript signal."""
    name: str
    parameters: List[tuple] = field(default_factory=list)
    documentation: Optional[str] = None
    
    def generate(self) -> str:
        lines = []
        
        if self.documentation:
            lines.append(f"## {self.documentation}")
        
        if self.parameters:
            params = ", ".join([f"{p[0]}: {p[1]}" for p in self.parameters])
            lines.append(f"signal {self.name}({params})")
        else:
            lines.append(f"signal {self.name}")
        
        return "\n".join(lines)


class GDScriptGenerator:
    """Generator for GDScript code."""
    
    def __init__(self):
        self.class_name: str = ""
        self.extends: str = "Node"
        self.class_documentation: Optional[str] = None
        self.icon: Optional[str] = None
        self.variables: List[GDScriptVariable] = []
        self.signals: List[GDScriptSignal] = []
        self.functions: List[GDScriptFunction] = []
        self.enums: Dict[str, List[str]] = {}
        self.constants: Dict[str, str] = {}
        
    def set_class(self, name: str, extends: GDScriptType = GDScriptType.NODE):
        """Set the class name and extends."""
        self.class_name = name
        self.extends = extends.value
        return self
    
    def set_icon(self, icon_path: str):
        """Set the class icon."""
        self.icon = icon_path
        return self
    
    def set_documentation(self, doc: str):
        """Set class documentation."""
        self.class_documentation = doc
        return self
    
    def add_variable(self, var: GDScriptVariable):
        """Add a variable to the script."""
        self.variables.append(var)
        return self
    
    def add_signal(self, signal: GDScriptSignal):
        """Add a signal to the script."""
        self.signals.append(signal)
        return self
    
    def add_function(self, func: GDScriptFunction):
        """Add a function to the script."""
        self.functions.append(func)
        return self
    
    def add_enum(self, name: str, values: List[str]):
        """Add an enum to the script."""
        self.enums[name] = values
        return self
    
    def add_constant(self, name: str, value: str):
        """Add a constant to the script."""
        self.constants[name] = value
        return self
    
    def generate(self) -> str:
        """Generate the complete GDScript."""
        lines = []
        
        # Class documentation
        if self.class_documentation:
            lines.append(f"## {self.class_documentation}")
        
        # Icon
        if self.icon:
            lines.append(f"@icon(\"{self.icon}\")")
        
        # Extends
        lines.append(f"extends {self.extends}")
        lines.append("")
        
        # Enums
        if self.enums:
            for enum_name, values in self.enums.items():
                lines.append(f"enum {enum_name} {{")
                for i, value in enumerate(values):
                    if i < len(values) - 1:
                        lines.append(f"    {value},")
                    else:
                        lines.append(f"    {value}")
                lines.append("}")
            lines.append("")
        
        # Constants
        if self.constants:
            for name, value in self.constants.items():
                lines.append(f"const {name} = {value}")
            lines.append("")
        
        # Signals
        if self.signals:
            for signal in self.signals:
                lines.append(signal.generate())
            lines.append("")
        
        # Variables
        if self.variables:
            for var in self.variables:
                lines.append(var.generate())
            lines.append("")
        
        # Functions
        if self.functions:
            for func in self.functions:
                lines.append(func.generate())
                lines.append("")
        
        return "\n".join(lines)
    
    # Preset generators for common Godot patterns
    
    def generate_player_controller_2d(self, class_name: str = "PlayerController") -> str:
        """Generate 2D player controller."""
        self.set_class(class_name, GDScriptType.CHARACTER_BODY2D)
        self.set_documentation("2D Player controller with movement and jumping")
        
        # Export variables
        self.add_variable(GDScriptVariable(
            name="speed",
            is_export=True,
            export_type=ExportType.FLOAT,
            default_value="300.0",
            documentation="Movement speed"
        ))
        
        self.add_variable(GDScriptVariable(
            name="jump_velocity",
            is_export=True,
            export_type=ExportType.FLOAT,
            default_value="-400.0",
            documentation="Jump velocity (negative is up)"
        ))
        
        self.add_variable(GDScriptVariable(
            name="gravity_scale",
            is_export=True,
            export_type=ExportType.FLOAT,
            default_value="1.0",
            documentation="Gravity scale multiplier"
        ))
        
        # Onready variables
        self.add_variable(GDScriptVariable(
            name="animated_sprite",
            is_onready=True,
            var_type="AnimatedSprite2D"
        ))
        
        # Signals
        self.add_signal(GDScriptSignal(
            name="jumped",
            documentation="Emitted when player jumps"
        ))
        
        self.add_signal(GDScriptSignal(
            name="landed",
            documentation="Emitted when player lands"
        ))
        
        # _ready function
        self.add_function(GDScriptFunction(
            name="_ready",
            body=[
                "animated_sprite = $AnimatedSprite2D"
            ]
        ))
        
        # _physics_process function
        self.add_function(GDScriptFunction(
            name="_physics_process",
            parameters=[("delta", "float")],
            body=[
                "# Apply gravity",
                "if not is_on_floor():",
                "    velocity.y += ProjectSettings.get_setting(\"physics/2d/default_gravity\") * gravity_scale * delta",
                "",
                "# Handle jump",
                "if Input.is_action_just_pressed(\"jump\") and is_on_floor():",
                "    velocity.y = jump_velocity",
                "    jumped.emit()",
                "",
                "# Get input direction",
                "var direction = Input.get_axis(\"move_left\", \"move_right\")",
                "",
                "# Handle movement",
                "if direction:",
                "    velocity.x = direction * speed",
                "    animated_sprite.flip_h = direction < 0",
                "    animated_sprite.play(\"run\")",
                "else:",
                "    velocity.x = move_toward(velocity.x, 0, speed)",
                "    animated_sprite.play(\"idle\")",
                "",
                "if not is_on_floor():",
                "    animated_sprite.play(\"jump\")",
                "",
                "move_and_slide()"
            ]
        ))
        
        return self.generate()
    
    def generate_player_controller_3d(self, class_name: str = "PlayerController") -> str:
        """Generate 3D player controller."""
        self.set_class(class_name, GDScriptType.CHARACTER_BODY3D)
        self.set_documentation("3D Player controller with FPS-style movement")
        
        # Export variables
        self.add_variable(GDScriptVariable(
            name="speed",
            is_export=True,
            export_type=ExportType.FLOAT,
            default_value="5.0",
            documentation="Movement speed"
        ))
        
        self.add_variable(GDScriptVariable(
            name="jump_velocity",
            is_export=True,
            export_type=ExportType.FLOAT,
            default_value="4.5",
            documentation="Jump velocity"
        ))
        
        self.add_variable(GDScriptVariable(
            name="mouse_sensitivity",
            is_export=True,
            export_type=ExportType.FLOAT,
            default_value="0.003",
            documentation="Mouse look sensitivity"
        ))
        
        # Onready variables
        self.add_variable(GDScriptVariable(
            name="camera",
            is_onready=True,
            var_type="Camera3D"
        ))
        
        # _ready function
        self.add_function(GDScriptFunction(
            name="_ready",
            body=[
                "camera = $Camera3D",
                "Input.mouse_mode = Input.MOUSE_MODE_CAPTURED"
            ]
        ))
        
        # _unhandled_input function
        self.add_function(GDScriptFunction(
            name="_unhandled_input",
            parameters=[("event", "InputEvent")],
            body=[
                "if event is InputEventMouseMotion:",
                "    rotate_y(-event.relative.x * mouse_sensitivity)",
                "    camera.rotate_x(-event.relative.y * mouse_sensitivity)",
                "    camera.rotation.x = clamp(camera.rotation.x, -PI/2, PI/2)"
            ]
        ))
        
        # _physics_process function
        self.add_function(GDScriptFunction(
            name="_physics_process",
            parameters=[("delta", "float")],
            body=[
                "# Apply gravity",
                "if not is_on_floor():",
                "    velocity.y -= ProjectSettings.get_setting(\"physics/3d/default_gravity\") * delta",
                "",
                "# Handle jump",
                "if Input.is_action_just_pressed(\"jump\") and is_on_floor():",
                "    velocity.y = jump_velocity",
                "",
                "# Get input direction",
                "var input_dir = Input.get_vector(\"move_left\", \"move_right\", \"move_up\", \"move_down\")",
                "var direction = (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()",
                "",
                "# Handle movement",
                "if direction:",
                "    velocity.x = direction.x * speed",
                "    velocity.z = direction.z * speed",
                "else:",
                "    velocity.x = move_toward(velocity.x, 0, speed)",
                "    velocity.z = move_toward(velocity.z, 0, speed)",
                "",
                "move_and_slide()"
            ]
        ))
        
        return self.generate()
    
    def generate_game_manager(self, class_name: str = "GameManager") -> str:
        """Generate game manager singleton."""
        self.set_class(class_name, GDScriptType.NODE)
        self.set_documentation("Game manager singleton for global game state")
        
        # Enum
        self.add_enum("GameState", ["MAIN_MENU", "PLAYING", "PAUSED", "GAME_OVER"])
        
        # Variables
        self.add_variable(GDScriptVariable(
            name="current_state",
            var_type="GameState",
            default_value="GameState.MAIN_MENU"
        ))
        
        self.add_variable(GDScriptVariable(
            name="score",
            var_type="int",
            default_value="0"
        ))
        
        self.add_variable(GDScriptVariable(
            name="high_score",
            var_type="int",
            default_value="0"
        ))
        
        # Signals
        self.add_signal(GDScriptSignal(
            name="state_changed",
            parameters=[("new_state", "GameState")],
            documentation="Emitted when game state changes"
        ))
        
        self.add_signal(GDScriptSignal(
            name="score_changed",
            parameters=[("new_score", "int")],
            documentation="Emitted when score changes"
        ))
        
        # Functions
        self.add_function(GDScriptFunction(
            name="change_state",
            parameters=[("new_state", "GameState")],
            body=[
                "current_state = new_state",
                "state_changed.emit(new_state)"
            ]
        ))
        
        self.add_function(GDScriptFunction(
            name="add_score",
            parameters=[("points", "int")],
            body=[
                "score += points",
                "if score > high_score:",
                "    high_score = score",
                "score_changed.emit(score)"
            ]
        ))
        
        self.add_function(GDScriptFunction(
            name="reset_game",
            body=[
                "score = 0",
                "current_state = GameState.MAIN_MENU",
                "score_changed.emit(score)"
            ]
        ))
        
        return self.generate()
    
    def generate_health_component(self, class_name: str = "HealthComponent") -> str:
        """Generate health component."""
        self.set_class(class_name, GDScriptType.NODE)
        self.set_documentation("Health component for managing entity health")
        
        # Export variables
        self.add_variable(GDScriptVariable(
            name="max_health",
            is_export=True,
            export_type=ExportType.FLOAT,
            default_value="100.0",
            documentation="Maximum health"
        ))
        
        # Variables
        self.add_variable(GDScriptVariable(
            name="current_health",
            var_type="float"
        ))
        
        # Signals
        self.add_signal(GDScriptSignal(
            name="health_changed",
            parameters=[("current", "float"), ("maximum", "float")],
            documentation="Emitted when health changes"
        ))
        
        self.add_signal(GDScriptSignal(
            name="died",
            documentation="Emitted when health reaches zero"
        ))
        
        # _ready function
        self.add_function(GDScriptFunction(
            name="_ready",
            body=[
                "current_health = max_health"
            ]
        ))
        
        # take_damage function
        self.add_function(GDScriptFunction(
            name="take_damage",
            parameters=[("amount", "float")],
            body=[
                "if amount <= 0:",
                "    return",
                "",
                "current_health -= amount",
                "current_health = clamp(current_health, 0, max_health)",
                "health_changed.emit(current_health, max_health)",
                "",
                "if current_health <= 0:",
                "    died.emit()"
            ]
        ))
        
        # heal function
        self.add_function(GDScriptFunction(
            name="heal",
            parameters=[("amount", "float")],
            body=[
                "if amount <= 0:",
                "    return",
                "",
                "current_health += amount",
                "current_health = clamp(current_health, 0, max_health)",
                "health_changed.emit(current_health, max_health)"
            ]
        ))
        
        # is_alive function
        self.add_function(GDScriptFunction(
            name="is_alive",
            return_type="bool",
            body=[
                "return current_health > 0"
            ]
        ))
        
        return self.generate()
    
    def generate_enemy_ai(self, class_name: str = "EnemyAI") -> str:
        """Generate enemy AI controller."""
        self.set_class(class_name, GDScriptType.CHARACTER_BODY2D)
        self.set_documentation("Basic enemy AI with patrol and chase behavior")
        
        # Export variables
        self.add_variable(GDScriptVariable(
            name="patrol_points",
            is_export=True,
            export_type=ExportType.ARRAY,
            default_value="[]",
            documentation="Array of patrol point positions"
        ))
        
        self.add_variable(GDScriptVariable(
            name="patrol_speed",
            is_export=True,
            export_type=ExportType.FLOAT,
            default_value="100.0",
            documentation="Speed when patrolling"
        ))
        
        self.add_variable(GDScriptVariable(
            name="chase_speed",
            is_export=True,
            export_type=ExportType.FLOAT,
            default_value="200.0",
            documentation="Speed when chasing player"
        ))
        
        self.add_variable(GDScriptVariable(
            name="detection_range",
            is_export=True,
            export_type=ExportType.FLOAT,
            default_value="200.0",
            documentation="Range to detect player"
        ))
        
        # Variables
        self.add_variable(GDScriptVariable(
            name="current_patrol_index",
            var_type="int",
            default_value="0"
        ))
        
        self.add_variable(GDScriptVariable(
            name="player",
            var_type="Node2D"
        ))
        
        self.add_variable(GDScriptVariable(
            name="state",
            var_type="String",
            default_value='"patrol"'
        ))
        
        # _ready function
        self.add_function(GDScriptFunction(
            name="_ready",
            body=[
                'player = get_tree().get_first_node_in_group("player")'
            ]
        ))
        
        # _physics_process function
        self.add_function(GDScriptFunction(
            name="_physics_process",
            parameters=[("delta", "float")],
            body=[
                "if player:",
                "    var distance_to_player = global_position.distance_to(player.global_position)",
                "    if distance_to_player <= detection_range:",
                "        state = \"chase\"",
                "    else:",
                "        state = \"patrol\"",
                "",
                "match state:",
                '    "patrol":',
                "        _patrol(delta)",
                '    "chase":',
                "        _chase(delta)",
                "",
                "move_and_slide()"
            ]
        ))
        
        # _patrol function
        self.add_function(GDScriptFunction(
            name="_patrol",
            parameters=[("delta", "float")],
            body=[
                "if patrol_points.is_empty():",
                "    return",
                "",
                "var target = patrol_points[current_patrol_index]",
                "var direction = global_position.direction_to(target)",
                "velocity = direction * patrol_speed",
                "",
                "if global_position.distance_to(target) < 10:",
                "    current_patrol_index = (current_patrol_index + 1) % patrol_points.size()"
            ]
        ))
        
        # _chase function
        self.add_function(GDScriptFunction(
            name="_chase",
            parameters=[("delta", "float")],
            body=[
                "if not player:",
                "    return",
                "",
                "var direction = global_position.direction_to(player.global_position)",
                "velocity = direction * chase_speed"
            ]
        ))
        
        return self.generate()
    
    def generate_collectible(self, class_name: str = "Collectible") -> str:
        """Generate collectible item."""
        self.set_class(class_name, GDScriptType.AREA2D)
        self.set_documentation("Collectible item that can be picked up by player")
        
        # Export variables
        self.add_variable(GDScriptVariable(
            name="value",
            is_export=True,
            export_type=ExportType.INT,
            default_value="10",
            documentation="Score value of this collectible"
        ))
        
        self.add_variable(GDScriptVariable(
            name="pickup_sound",
            is_export=True,
            export_type=ExportType.AUDIO_STREAM,
            documentation="Sound played on pickup"
        ))
        
        # Signals
        self.add_signal(GDScriptSignal(
            name="collected",
            parameters=[("value", "int")],
            documentation="Emitted when collected"
        ))
        
        # _on_body_entered function
        self.add_function(GDScriptFunction(
            name="_on_body_entered",
            parameters=[("body", "Node2D")],
            body=[
                'if body.is_in_group("player"):',
                "    _collect()"
            ]
        ))
        
        # _collect function
        self.add_function(GDScriptFunction(
            name="_collect",
            body=[
                "if pickup_sound:",
                "    AudioManager.play_sfx(pickup_sound)",
                "",
                "GameManager.add_score(value)",
                "collected.emit(value)",
                "queue_free()"
            ]
        ))
        
        return self.generate()
    
    def generate_ui_manager(self, class_name: str = "UIManager") -> str:
        """Generate UI manager."""
        self.set_class(class_name, GDScriptType.CONTROL)
        self.set_documentation("UI manager for handling game UI")
        
        # Onready variables
        self.add_variable(GDScriptVariable(
            name="score_label",
            is_onready=True,
            var_type="Label"
        ))
        
        self.add_variable(GDScriptVariable(
            name="health_bar",
            is_onready=True,
            var_type="ProgressBar"
        ))
        
        self.add_variable(GDScriptVariable(
            name="pause_menu",
            is_onready=True,
            var_type="Control"
        ))
        
        # _ready function
        self.add_function(GDScriptFunction(
            name="_ready",
            body=[
                "score_label = $ScoreLabel",
                "health_bar = $HealthBar",
                "pause_menu = $PauseMenu",
                "pause_menu.hide()",
                "",
                "GameManager.score_changed.connect(_on_score_changed)",
                "get_tree().paused = false"
            ]
        ))
        
        # _process function
        self.add_function(GDScriptFunction(
            name="_process",
            parameters=[("_delta", "float")],
            body=[
                "if Input.is_action_just_pressed(\"ui_cancel\"):",
                "    _toggle_pause()"
            ]
        ))
        
        # _toggle_pause function
        self.add_function(GDScriptFunction(
            name="_toggle_pause",
            body=[
                "get_tree().paused = not get_tree().paused",
                "pause_menu.visible = get_tree().paused",
                "",
                "if get_tree().paused:",
                "    Input.mouse_mode = Input.MOUSE_MODE_VISIBLE",
                "else:",
                "    Input.mouse_mode = Input.MOUSE_MODE_CAPTURED"
            ]
        ))
        
        # _on_score_changed function
        self.add_function(GDScriptFunction(
            name="_on_score_changed",
            parameters=[("new_score", "int")],
            body=[
                'score_label.text = "Score: %d" % new_score'
            ]
        ))
        
        # update_health_bar function
        self.add_function(GDScriptFunction(
            name="update_health_bar",
            parameters=[("current", "float"), ("maximum", "float")],
            body=[
                "health_bar.max_value = maximum",
                "health_bar.value = current"
            ]
        ))
        
        return self.generate()
