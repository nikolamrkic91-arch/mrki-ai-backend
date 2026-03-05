"""
Godot Engine Adapter for Mrki
Handles Godot project creation, management, and integration.
"""

import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class GodotProjectConfig:
    """Configuration for Godot project creation."""
    name: str
    version: str = "4.2"
    renderer: str = "forward_plus"  # forward_plus, mobile, compatibility
    features: List[str] = field(default_factory=list)
    autoloads: Dict[str, str] = field(default_factory=dict)
    input_actions: Dict[str, Dict] = field(default_factory=dict)
    layers: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "renderer": self.renderer,
            "features": self.features,
            "autoloads": self.autoloads,
            "input_actions": self.input_actions,
            "layers": self.layers
        }


class GodotAdapter:
    """Adapter for Godot Engine operations."""
    
    RENDERERS = {
        "forward_plus": "forward_plus",
        "mobile": "mobile",
        "compatibility": "gl_compatibility"
    }
    
    COMMON_FEATURES = [
        "2d",
        "3d",
        "physics",
        "navigation",
        "multiplayer",
        "audio",
        "animation"
    ]
    
    DEFAULT_INPUT_ACTIONS = {
        "ui_accept": {
            "deadzone": 0.5,
            "events": [
                {"type": "key", "keycode": 4194309},  # Enter
                {"type": "key", "keycode": 32},       # Space
            ]
        },
        "ui_select": {
            "deadzone": 0.5,
            "events": [
                {"type": "key", "keycode": 32}  # Space
            ]
        },
        "ui_cancel": {
            "deadzone": 0.5,
            "events": [
                {"type": "key", "keycode": 4194305}  # Escape
            ]
        },
        "move_left": {
            "deadzone": 0.5,
            "events": [
                {"type": "key", "keycode": 65},   # A
                {"type": "key", "keycode": 4194319}  # Left
            ]
        },
        "move_right": {
            "deadzone": 0.5,
            "events": [
                {"type": "key", "keycode": 68},   # D
                {"type": "key", "keycode": 4194321}  # Right
            ]
        },
        "move_up": {
            "deadzone": 0.5,
            "events": [
                {"type": "key", "keycode": 87},   # W
                {"type": "key", "keycode": 4194320}  # Up
            ]
        },
        "move_down": {
            "deadzone": 0.5,
            "events": [
                {"type": "key", "keycode": 83},   # S
                {"type": "key", "keycode": 4194322}  # Down
            ]
        },
        "jump": {
            "deadzone": 0.5,
            "events": [
                {"type": "key", "keycode": 32}  # Space
            ]
        },
        "attack": {
            "deadzone": 0.5,
            "events": [
                {"type": "mouse_button", "button_index": 1}
            ]
        },
        "interact": {
            "deadzone": 0.5,
            "events": [
                {"type": "key", "keycode": 69}  # E
            ]
        }
    }
    
    def __init__(self, godot_path: Optional[str] = None):
        self.godot_path = godot_path or self._find_godot_installation()
        self.projects_dir = Path.home() / "GodotProjects"
        
    def _find_godot_installation(self) -> Optional[str]:
        """Find Godot installation path."""
        if os.name == 'nt':  # Windows
            paths = [
                r"C:\Program Files\Godot\Godot.exe",
                r"C:\Program Files (x86)\Godot\Godot.exe",
            ]
        elif os.name == 'posix':
            if os.path.exists("/Applications/Godot.app"):  # macOS
                paths = ["/Applications/Godot.app/Contents/MacOS/Godot"]
            else:  # Linux
                paths = [
                    "/usr/bin/godot",
                    "/usr/local/bin/godot",
                    "/opt/godot/godot"
                ]
        else:
            paths = []
            
        for path in paths:
            if os.path.exists(path):
                return path
        return None
    
    def create_project(self, config: GodotProjectConfig, output_dir: Optional[str] = None) -> str:
        """Create a new Godot project."""
        project_dir = Path(output_dir or self.projects_dir) / config.name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create project structure
        self._create_project_structure(project_dir, config)
        
        # Create project.godot file
        self._create_project_godot(project_dir, config)
        
        return str(project_dir)
    
    def _create_project_structure(self, project_dir: Path, config: GodotProjectConfig):
        """Create Godot project folder structure."""
        folders = [
            "scenes",
            "scenes/levels",
            "scenes/ui",
            "scripts",
            "scripts/player",
            "scripts/enemies",
            "scripts/ui",
            "scripts/managers",
            "scripts/utils",
            "assets",
            "assets/sprites",
            "assets/models",
            "assets/audio",
            "assets/fonts",
            "assets/tilesets",
            "resources",
            "autoload",
            "shaders"
        ]
        
        for folder in folders:
            (project_dir / folder).mkdir(parents=True, exist_ok=True)
    
    def _create_project_godot(self, project_dir: Path, config: GodotProjectConfig):
        """Create project.godot file."""
        project_config = {
            ";": "*** AUTO GENERATED BY MRKI ***",
            "application": {
                "config/name": config.name,
                "config/description": f"Generated by Mrki Game Development Module",
                "config/version": "1.0.0",
                "run/main_scene": "res://scenes/main_menu.tscn",
                "config/features": PackedStringArray(config.version, config.renderer),
                "boot_splash/bg_color": Color(0, 0, 0, 1)
            },
            "autoload": config.autoloads,
            "display": {
                "window/size/viewport_width": 1920,
                "window/size/viewport_height": 1080,
                "window/size/mode": 0,
                "window/stretch/mode": "canvas_items",
                "window/stretch/aspect": "expand"
            },
            "input": {},
            "layer_names": {
                "3d_physics": {},
                "2d_physics": {}
            },
            "rendering": {
                "renderer/rendering_method": self.RENDERERS.get(config.renderer, "forward_plus"),
                "textures/canvas_textures/default_texture_filter": 0,
                "textures/canvas_textures/default_texture_repeat": 0
            }
        }
        
        # Add input actions
        input_actions = self.DEFAULT_INPUT_ACTIONS.copy()
        input_actions.update(config.input_actions)
        project_config["input"] = input_actions
        
        # Add layers
        for layer_name, layer_number in config.layers.items():
            project_config["layer_names"]["3d_physics"][f"layer_{layer_number}"] = layer_name
        
        # Write as Godot config format
        config_lines = self._dict_to_godot_config(project_config)
        
        with open(project_dir / "project.godot", 'w') as f:
            f.write(config_lines)
    
    def _dict_to_godot_config(self, data: Dict, section: str = "") -> str:
        """Convert dictionary to Godot config format."""
        lines = []
        
        for key, value in data.items():
            if key == ";":
                lines.append(f"; {value}")
                continue
                
            full_key = f"{section}/{key}" if section else key
            
            if isinstance(value, dict):
                if section:
                    lines.extend(self._dict_to_godot_config(value, full_key).split('\n'))
                else:
                    lines.append(f"[{key}]")
                    lines.extend(self._dict_to_godot_config(value, "").split('\n'))
                    lines.append("")
            elif isinstance(value, list):
                if all(isinstance(v, dict) for v in value):
                    for item in value:
                        item_str = json.dumps(item).replace('"', '\\"')
                        lines.append(f'{full_key}="{item_str}"')
                else:
                    list_str = ", ".join(f'"{v}"' if isinstance(v, str) else str(v) for v in value)
                    lines.append(f'{full_key}=PackedStringArray({list_str})')
            elif isinstance(value, str):
                lines.append(f'{full_key}="{value}"')
            elif isinstance(value, bool):
                lines.append(f'{full_key}={"true" if value else "false"}')
            elif isinstance(value, (int, float)):
                lines.append(f'{full_key}={value}')
            elif hasattr(value, 'r'):
                # Color
                lines.append(f'{full_key}=Color({value.r}, {value.g}, {value.b}, {value.a})')
        
        return '\n'.join(lines)
    
    def add_autoload(self, project_path: str, name: str, script_path: str) -> bool:
        """Add an autoload (singleton) to the project."""
        project_godot = Path(project_path) / "project.godot"
        
        try:
            with open(project_godot, 'r') as f:
                content = f.read()
            
            # Check if autoload section exists
            if "[autoload]" not in content:
                content += "\n[autoload]\n"
            
            # Add autoload entry
            autoload_line = f'{name}="*res://{script_path}"\n'
            
            if f"{name}=\"" not in content:
                content = content.replace("[autoload]\n", f"[autoload]\n{autoload_line}")
            
            with open(project_godot, 'w') as f:
                f.write(content)
            
            return True
        except Exception as e:
            print(f"Failed to add autoload: {e}")
            return False
    
    def add_input_action(self, project_path: str, action_name: str, 
                         events: List[Dict], deadzone: float = 0.5) -> bool:
        """Add an input action to the project."""
        project_godot = Path(project_path) / "project.godot"
        
        try:
            with open(project_godot, 'r') as f:
                content = f.read()
            
            # Check if input section exists
            if "[input]" not in content:
                content += "\n[input]\n"
            
            # Add input action
            action_config = f'{action_name}={{"deadzone": {deadzone}, "events": {json.dumps(events)}}}\n'
            
            if f"{action_name}={{" not in content:
                content = content.replace("[input]\n", f"[input]\n{action_config}")
            
            with open(project_godot, 'w') as f:
                f.write(content)
            
            return True
        except Exception as e:
            print(f"Failed to add input action: {e}")
            return False
    
    def get_project_info(self, project_path: str) -> Dict[str, Any]:
        """Get Godot project information."""
        info = {
            "path": project_path,
            "name": Path(project_path).name,
            "version": None,
            "main_scene": None,
            "autoloads": {},
            "scenes": []
        }
        
        # Read project.godot
        project_godot = Path(project_path) / "project.godot"
        if project_godot.exists():
            with open(project_godot, 'r') as f:
                content = f.read()
                
                # Parse basic info
                for line in content.split('\n'):
                    if 'config/name=' in line:
                        info["name"] = line.split('=')[1].strip().strip('"')
                    elif 'config/features=' in line:
                        features = line.split('=')[1].strip()
                        info["version"] = features.split(',')[0].strip('"[]')
                    elif 'run/main_scene=' in line:
                        info["main_scene"] = line.split('=')[1].strip().strip('"')
        
        # Find scenes
        scenes_path = Path(project_path) / "scenes"
        if scenes_path.exists():
            info["scenes"] = [str(f) for f in scenes_path.rglob("*.tscn")]
        
        return info
    
    def export_project(self, project_path: str, export_preset: str, 
                       output_path: str) -> bool:
        """Export Godot project for a specific platform."""
        if not self.godot_path:
            raise RuntimeError("Godot installation not found")
        
        cmd = [
            self.godot_path,
            "--headless",
            "--path", project_path,
            "--export-release", export_preset,
            output_path
        ]
        
        try:
            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            return result.returncode == 0
        except Exception as e:
            print(f"Export error: {e}")
            return False


# Helper class for Color
class Color:
    def __init__(self, r: float, g: float, b: float, a: float = 1.0):
        self.r = r
        self.g = g
        self.b = b
        self.a = a
    
    def __repr__(self):
        return f"Color({self.r}, {self.g}, {self.b}, {self.a})"


# Helper class for PackedStringArray
class PackedStringArray(list):
    def __init__(self, *args):
        super().__init__(args)
