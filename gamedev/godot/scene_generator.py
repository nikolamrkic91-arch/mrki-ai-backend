"""
Godot Scene Generator
Generates Godot scene files (.tscn).
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class NodeType(Enum):
    """Godot node types."""
    NODE = "Node"
    NODE2D = "Node2D"
    NODE3D = "Node3D"
    CONTROL = "Control"
    CHARACTER_BODY2D = "CharacterBody2D"
    CHARACTER_BODY3D = "CharacterBody3D"
    RIGID_BODY2D = "RigidBody2D"
    RIGID_BODY3D = "RigidBody3D"
    STATIC_BODY2D = "StaticBody2D"
    STATIC_BODY3D = "StaticBody3D"
    AREA2D = "Area2D"
    AREA3D = "Area3D"
    SPRITE2D = "Sprite2D"
    SPRITE3D = "Sprite3D"
    ANIMATED_SPRITE2D = "AnimatedSprite2D"
    ANIMATED_SPRITE3D = "AnimatedSprite3D"
    CAMERA2D = "Camera2D"
    CAMERA3D = "Camera3D"
    COLLISION_SHAPE2D = "CollisionShape2D"
    COLLISION_SHAPE3D = "CollisionShape3D"
    COLLISION_POLYGON2D = "CollisionPolygon2D"
    LABEL = "Label"
    BUTTON = "Button"
    TEXTURE_RECT = "TextureRect"
    PROGRESS_BAR = "ProgressBar"
    TIMER = "Timer"
    AUDIO_STREAM_PLAYER = "AudioStreamPlayer"
    AUDIO_STREAM_PLAYER2D = "AudioStreamPlayer2D"
    AUDIO_STREAM_PLAYER3D = "AudioStreamPlayer3D"
    ANIMATION_PLAYER = "AnimationPlayer"
    TILE_MAP = "TileMap"
    PATH2D = "Path2D"
    PATH_FOLLOW2D = "PathFollow2D"
    RAY_CAST2D = "RayCast2D"
    RAY_CAST3D = "RayCast3D"
    LIGHT2D = "PointLight2D"
    DIRECTIONAL_LIGHT2D = "DirectionalLight2D"
    OMNI_LIGHT3D = "OmniLight3D"
    DIRECTIONAL_LIGHT3D = "DirectionalLight3D"
    SPOT_LIGHT3D = "SpotLight3D"
    ENVIRONMENT = "WorldEnvironment"


@dataclass
class NodeProperty:
    """Represents a node property."""
    name: str
    value: Any
    
    def to_tscn(self) -> str:
        if isinstance(self.value, str):
            return f'{self.name} = "{self.value}"'
        elif isinstance(self.value, bool):
            return f'{self.name} = {"true" if self.value else "false"}'
        elif isinstance(self.value, (int, float)):
            return f'{self.name} = {self.value}'
        elif isinstance(self.value, (list, tuple)):
            values = ", ".join(str(v) for v in self.value)
            return f'{self.name} = Vector2({values})' if len(self.value) == 2 else f'{self.name} = Vector3({values})'
        else:
            return f'{self.name} = {self.value}'


@dataclass
class SceneNode:
    """Represents a node in a Godot scene."""
    name: str
    node_type: NodeType
    parent: str = "."
    index: int = 0
    properties: List[NodeProperty] = field(default_factory=list)
    script_path: Optional[str] = None
    groups: List[str] = field(default_factory=list)
    
    def to_tscn(self) -> str:
        lines = []
        
        # Node header
        if self.parent == ".":
            lines.append(f'[node name="{self.name}" type="{self.node_type.value}"]')
        else:
            lines.append(f'[node name="{self.name}" type="{self.node_type.value}" parent="{self.parent}"]')
        
        # Script
        if self.script_path:
            lines.append(f'script = ExtResource("{self.script_path}")')
        
        # Properties
        for prop in self.properties:
            lines.append(prop.to_tscn())
        
        # Groups
        for group in self.groups:
            lines.append(f'groups = ["{group}"]')
        
        return "\n".join(lines)


@dataclass
class ExtResource:
    """Represents an external resource reference."""
    resource_id: str
    resource_type: str
    path: str
    
    def to_tscn(self) -> str:
        return f'[ext_resource type="{self.resource_type}" path="{self.path}" id="{self.resource_id}"]'


@dataclass
class SubResource:
    """Represents a sub-resource definition."""
    resource_id: str
    resource_type: str
    properties: List[NodeProperty] = field(default_factory=list)
    
    def to_tscn(self) -> str:
        lines = [f'[sub_resource type="{self.resource_type}" id="{self.resource_id}"]']
        for prop in self.properties:
            lines.append(prop.to_tscn())
        return "\n".join(lines)


class SceneGenerator:
    """Generator for Godot scene files."""
    
    def __init__(self):
        self.scene_name: str = ""
        self.load_steps: int = 2
        self.ext_resources: List[ExtResource] = []
        self.sub_resources: List[SubResource] = []
        self.nodes: List[SceneNode] = []
        self.connections: List[str] = []
        
    def set_scene_name(self, name: str):
        """Set the scene name."""
        self.scene_name = name
        return self
    
    def add_ext_resource(self, resource: ExtResource):
        """Add an external resource."""
        self.ext_resources.append(resource)
        return self
    
    def add_sub_resource(self, resource: SubResource):
        """Add a sub-resource."""
        self.sub_resources.append(resource)
        return self
    
    def add_node(self, node: SceneNode):
        """Add a node to the scene."""
        self.nodes.append(node)
        return self
    
    def add_connection(self, signal_name: str, from_node: str, to_method: str):
        """Add a signal connection."""
        self.connections.append(f'[connection signal="{signal_name}" from="{from_node}" to="{from_node}" method="{to_method}"]')
        return self
    
    def generate(self) -> str:
        """Generate the complete .tscn file."""
        lines = []
        
        # Header
        lines.append("[gd_scene load_steps=2 format=3 uid=\"uid://" + self._generate_uid() + "\"]")
        lines.append("")
        
        # External resources
        for resource in self.ext_resources:
            lines.append(resource.to_tscn())
        
        if self.ext_resources:
            lines.append("")
        
        # Sub-resources
        for resource in self.sub_resources:
            lines.append(resource.to_tscn())
            lines.append("")
        
        # Nodes
        for node in self.nodes:
            lines.append(node.to_tscn())
            lines.append("")
        
        # Connections
        for connection in self.connections:
            lines.append(connection)
        
        return "\n".join(lines)
    
    def _generate_uid(self) -> str:
        """Generate a unique identifier."""
        import random
        import string
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=13))
    
    # Preset scene generators
    
    def generate_player_scene_2d(self, script_path: str = "player.gd") -> str:
        """Generate a 2D player scene."""
        self.set_scene_name("Player")
        
        # Add script resource
        self.add_ext_resource(ExtResource(
            resource_id="1_abc123",
            resource_type="Script",
            path=f"res://scripts/{script_path}"
        ))
        
        # Add collision shape sub-resource
        self.add_sub_resource(SubResource(
            resource_id="CircleShape2D_abc",
            resource_type="CircleShape2D",
            properties=[NodeProperty("radius", 20)]
        ))
        
        # Root node (CharacterBody2D)
        self.add_node(SceneNode(
            name="Player",
            node_type=NodeType.CHARACTER_BODY2D,
            parent=".",
            script_path="1_abc123",
            groups=["player"]
        ))
        
        # AnimatedSprite2D
        self.add_node(SceneNode(
            name="AnimatedSprite2D",
            node_type=NodeType.ANIMATED_SPRITE2D,
            parent=".",
            properties=[
                NodeProperty("position", [0, -16])
            ]
        ))
        
        # CollisionShape2D
        self.add_node(SceneNode(
            name="CollisionShape2D",
            node_type=NodeType.COLLISION_SHAPE2D,
            parent=".",
            properties=[
                NodeProperty("shape", "SubResource(\"CircleShape2D_abc\")")
            ]
        ))
        
        # Camera2D
        self.add_node(SceneNode(
            name="Camera2D",
            node_type=NodeType.CAMERA2D,
            parent=".",
            properties=[
                NodeProperty("zoom", [2, 2]),
                NodeProperty("position_smoothing_enabled", True)
            ]
        ))
        
        return self.generate()
    
    def generate_enemy_scene_2d(self, script_path: str = "enemy.gd") -> str:
        """Generate a 2D enemy scene."""
        self.set_scene_name("Enemy")
        
        # Add script resource
        self.add_ext_resource(ExtResource(
            resource_id="1_def456",
            resource_type="Script",
            path=f"res://scripts/{script_path}"
        ))
        
        # Add collision shape sub-resource
        self.add_sub_resource(SubResource(
            resource_id="RectangleShape2D_def",
            resource_type="RectangleShape2D",
            properties=[
                NodeProperty("size", [32, 48])
            ]
        ))
        
        # Root node (CharacterBody2D)
        self.add_node(SceneNode(
            name="Enemy",
            node_type=NodeType.CHARACTER_BODY2D,
            parent=".",
            script_path="1_def456",
            groups=["enemy"]
        ))
        
        # Sprite2D
        self.add_node(SceneNode(
            name="Sprite2D",
            node_type=NodeType.SPRITE2D,
            parent=".",
            properties=[
                NodeProperty("position", [0, -24])
            ]
        ))
        
        # CollisionShape2D
        self.add_node(SceneNode(
            name="CollisionShape2D",
            node_type=NodeType.COLLISION_SHAPE2D,
            parent=".",
            properties=[
                NodeProperty("position", [0, -24]),
                NodeProperty("shape", "SubResource(\"RectangleShape2D_def\")")
            ]
        ))
        
        return self.generate()
    
    def generate_collectible_scene(self, script_path: str = "collectible.gd") -> str:
        """Generate a collectible item scene."""
        self.set_scene_name("Collectible")
        
        # Add script resource
        self.add_ext_resource(ExtResource(
            resource_id="1_ghi789",
            resource_type="Script",
            path=f"res://scripts/{script_path}"
        ))
        
        # Add collision shape sub-resource
        self.add_sub_resource(SubResource(
            resource_id="CircleShape2D_ghi",
            resource_type="CircleShape2D",
            properties=[NodeProperty("radius", 16)]
        ))
        
        # Root node (Area2D)
        self.add_node(SceneNode(
            name="Collectible",
            node_type=NodeType.AREA2D,
            parent=".",
            script_path="1_ghi789",
            groups=["collectible"]
        ))
        
        # Sprite2D
        self.add_node(SceneNode(
            name="Sprite2D",
            node_type=NodeType.SPRITE2D,
            parent=".",
            properties=[
                NodeProperty("scale", [0.5, 0.5])
            ]
        ))
        
        # CollisionShape2D
        self.add_node(SceneNode(
            name="CollisionShape2D",
            node_type=NodeType.COLLISION_SHAPE2D,
            parent=".",
            properties=[
                NodeProperty("shape", "SubResource(\"CircleShape2D_ghi\")")
            ]
        ))
        
        # AnimationPlayer
        self.add_node(SceneNode(
            name="AnimationPlayer",
            node_type=NodeType.ANIMATION_PLAYER,
            parent="."
        ))
        
        # Add connection
        self.add_connection("body_entered", ".", "_on_body_entered")
        
        return self.generate()
    
    def generate_level_scene(self) -> str:
        """Generate a basic level scene."""
        self.set_scene_name("Level")
        
        # Root node (Node2D)
        self.add_node(SceneNode(
            name="Level",
            node_type=NodeType.NODE2D,
            parent="."
        ))
        
        # Background
        self.add_node(SceneNode(
            name="Background",
            node_type=NodeType.NODE2D,
            parent="."
        ))
        
        # TileMap
        self.add_node(SceneNode(
            name="TileMap",
            node_type=NodeType.TILE_MAP,
            parent=".",
            properties=[
                NodeProperty("format", 2)
            ]
        ))
        
        # Entities
        self.add_node(SceneNode(
            name="Entities",
            node_type=NodeType.NODE2D,
            parent="."
        ))
        
        # Player spawn point
        self.add_node(SceneNode(
            name="PlayerSpawn",
            node_type=NodeType.MARKER2D,
            parent="Entities"
        ))
        
        # Enemies container
        self.add_node(SceneNode(
            name="Enemies",
            node_type=NodeType.NODE2D,
            parent="Entities"
        ))
        
        # Collectibles container
        self.add_node(SceneNode(
            name="Collectibles",
            node_type=NodeType.NODE2D,
            parent="Entities"
        ))
        
        # Environment
        self.add_node(SceneNode(
            name="Environment",
            node_type=NodeType.NODE2D,
            parent="."
        ))
        
        return self.generate()
    
    def generate_ui_scene(self) -> str:
        """Generate a UI scene."""
        self.set_scene_name("UI")
        
        # Add script resource
        self.add_ext_resource(ExtResource(
            resource_id="1_jkl012",
            resource_type="Script",
            path="res://scripts/ui_manager.gd"
        ))
        
        # Root node (CanvasLayer)
        self.add_node(SceneNode(
            name="UI",
            node_type=NodeType.NODE,
            parent=".",
            script_path="1_jkl012"
        ))
        
        # HUD
        self.add_node(SceneNode(
            name="HUD",
            node_type=NodeType.CONTROL,
            parent=".",
            properties=[
                NodeProperty("layout_mode", 3),
                NodeProperty("anchors_preset", 15),
                NodeProperty("anchor_right", 1.0),
                NodeProperty("anchor_bottom", 1.0),
                NodeProperty("grow_horizontal", 2),
                NodeProperty("grow_vertical", 2)
            ]
        ))
        
        # Score Label
        self.add_node(SceneNode(
            name="ScoreLabel",
            node_type=NodeType.LABEL,
            parent="HUD",
            properties=[
                NodeProperty("layout_mode", 0),
                NodeProperty("offset_left", 20),
                NodeProperty("offset_top", 20),
                NodeProperty("text", "Score: 0")
            ]
        ))
        
        # Health Bar
        self.add_node(SceneNode(
            name="HealthBar",
            node_type=NodeType.PROGRESS_BAR,
            parent="HUD",
            properties=[
                NodeProperty("layout_mode", 0),
                NodeProperty("offset_left", 20),
                NodeProperty("offset_top", 50),
                NodeProperty("offset_right", 220),
                NodeProperty("offset_bottom", 70),
                NodeProperty("max_value", 100.0),
                NodeProperty("value", 100.0)
            ]
        ))
        
        # Pause Menu
        self.add_node(SceneNode(
            name="PauseMenu",
            node_type=NodeType.CONTROL,
            parent=".",
            properties=[
                NodeProperty("visible", False),
                NodeProperty("layout_mode", 3),
                NodeProperty("anchors_preset", 15),
                NodeProperty("anchor_right", 1.0),
                NodeProperty("anchor_bottom", 1.0),
                NodeProperty("grow_horizontal", 2),
                NodeProperty("grow_vertical", 2)
            ]
        ))
        
        # Pause Menu Background
        self.add_node(SceneNode(
            name="Background",
            node_type=NodeType.COLOR_RECT,
            parent="PauseMenu",
            properties=[
                NodeProperty("layout_mode", 1),
                NodeProperty("anchors_preset", 15),
                NodeProperty("anchor_right", 1.0),
                NodeProperty("anchor_bottom", 1.0),
                NodeProperty("grow_horizontal", 2),
                NodeProperty("grow_vertical", 2),
                NodeProperty("color", [0, 0, 0, 0.5])
            ]
        ))
        
        # Resume Button
        self.add_node(SceneNode(
            name="ResumeButton",
            node_type=NodeType.BUTTON,
            parent="PauseMenu",
            properties=[
                NodeProperty("layout_mode", 1),
                NodeProperty("anchors_preset", 8),
                NodeProperty("anchor_left", 0.5),
                NodeProperty("anchor_top", 0.5),
                NodeProperty("anchor_right", 0.5),
                NodeProperty("anchor_bottom", 0.5),
                NodeProperty("offset_left", -100),
                NodeProperty("offset_top", -60),
                NodeProperty("offset_right", 100),
                NodeProperty("offset_bottom", -20),
                NodeProperty("grow_horizontal", 2),
                NodeProperty("grow_vertical", 2),
                NodeProperty("text", "Resume")
            ]
        ))
        
        # Quit Button
        self.add_node(SceneNode(
            name="QuitButton",
            node_type=NodeType.BUTTON,
            parent="PauseMenu",
            properties=[
                NodeProperty("layout_mode", 1),
                NodeProperty("anchors_preset", 8),
                NodeProperty("anchor_left", 0.5),
                NodeProperty("anchor_top", 0.5),
                NodeProperty("anchor_right", 0.5),
                NodeProperty("anchor_bottom", 0.5),
                NodeProperty("offset_left", -100),
                NodeProperty("offset_top", 20),
                NodeProperty("offset_right", 100),
                NodeProperty("offset_bottom", 60),
                NodeProperty("grow_horizontal", 2),
                NodeProperty("grow_vertical", 2),
                NodeProperty("text", "Quit")
            ]
        ))
        
        return self.generate()
    
    def generate_main_menu_scene(self) -> str:
        """Generate a main menu scene."""
        self.set_scene_name("MainMenu")
        
        # Root node (Control)
        self.add_node(SceneNode(
            name="MainMenu",
            node_type=NodeType.CONTROL,
            parent=".",
            properties=[
                NodeProperty("layout_mode", 3),
                NodeProperty("anchors_preset", 15),
                NodeProperty("anchor_right", 1.0),
                NodeProperty("anchor_bottom", 1.0),
                NodeProperty("grow_horizontal", 2),
                NodeProperty("grow_vertical", 2)
            ]
        ))
        
        # Background
        self.add_node(SceneNode(
            name="Background",
            node_type=NodeType.COLOR_RECT,
            parent=".",
            properties=[
                NodeProperty("layout_mode", 1),
                NodeProperty("anchors_preset", 15),
                NodeProperty("anchor_right", 1.0),
                NodeProperty("anchor_bottom", 1.0),
                NodeProperty("grow_horizontal", 2),
                NodeProperty("grow_vertical", 2),
                NodeProperty("color", [0.1, 0.1, 0.2, 1.0])
            ]
        ))
        
        # Title Label
        self.add_node(SceneNode(
            name="TitleLabel",
            node_type=NodeType.LABEL,
            parent=".",
            properties=[
                NodeProperty("layout_mode", 1),
                NodeProperty("anchors_preset", 5),
                NodeProperty("anchor_left", 0.5),
                NodeProperty("anchor_right", 0.5),
                NodeProperty("offset_left", -200),
                NodeProperty("offset_top", 100),
                NodeProperty("offset_right", 200),
                NodeProperty("offset_bottom", 150),
                NodeProperty("grow_horizontal", 2),
                NodeProperty("text", "GAME TITLE"),
                NodeProperty("horizontal_alignment", 1)
            ]
        ))
        
        # Start Button
        self.add_node(SceneNode(
            name="StartButton",
            node_type=NodeType.BUTTON,
            parent=".",
            properties=[
                NodeProperty("layout_mode", 1),
                NodeProperty("anchors_preset", 8),
                NodeProperty("anchor_left", 0.5),
                NodeProperty("anchor_top", 0.5),
                NodeProperty("anchor_right", 0.5),
                NodeProperty("anchor_bottom", 0.5),
                NodeProperty("offset_left", -100),
                NodeProperty("offset_top", -40),
                NodeProperty("offset_right", 100),
                NodeProperty("offset_bottom", 0),
                NodeProperty("grow_horizontal", 2),
                NodeProperty("grow_vertical", 2),
                NodeProperty("text", "Start Game")
            ]
        ))
        
        # Options Button
        self.add_node(SceneNode(
            name="OptionsButton",
            node_type=NodeType.BUTTON,
            parent=".",
            properties=[
                NodeProperty("layout_mode", 1),
                NodeProperty("anchors_preset", 8),
                NodeProperty("anchor_left", 0.5),
                NodeProperty("anchor_top", 0.5),
                NodeProperty("anchor_right", 0.5),
                NodeProperty("anchor_bottom", 0.5),
                NodeProperty("offset_left", -100),
                NodeProperty("offset_top", 20),
                NodeProperty("offset_right", 100),
                NodeProperty("offset_bottom", 60),
                NodeProperty("grow_horizontal", 2),
                NodeProperty("grow_vertical", 2),
                NodeProperty("text", "Options")
            ]
        ))
        
        # Quit Button
        self.add_node(SceneNode(
            name="QuitButton",
            node_type=NodeType.BUTTON,
            parent=".",
            properties=[
                NodeProperty("layout_mode", 1),
                NodeProperty("anchors_preset", 8),
                NodeProperty("anchor_left", 0.5),
                NodeProperty("anchor_top", 0.5),
                NodeProperty("anchor_right", 0.5),
                NodeProperty("anchor_bottom", 0.5),
                NodeProperty("offset_left", -100),
                NodeProperty("offset_top", 80),
                NodeProperty("offset_right", 100),
                NodeProperty("offset_bottom", 120),
                NodeProperty("grow_horizontal", 2),
                NodeProperty("grow_vertical", 2),
                NodeProperty("text", "Quit")
            ]
        ))
        
        return self.generate()
