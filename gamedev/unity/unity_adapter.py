"""
Unity Engine Adapter for Mrki
Handles Unity project creation, management, and integration.
"""

import os
import json
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class UnityProjectConfig:
    """Configuration for Unity project creation."""
    name: str
    version: str = "2022.3.0f1"  # LTS version
    template: str = "3d"
    render_pipeline: str = "builtin"  # builtin, urp, hdrp
    scripting_backend: str = "mono"  # mono, il2cpp
    api_compatibility: str = "netstandard2.1"
    packages: List[str] = field(default_factory=list)
    platforms: List[str] = field(default_factory=lambda: ["StandaloneWindows64"])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "template": self.template,
            "render_pipeline": self.render_pipeline,
            "scripting_backend": self.scripting_backend,
            "api_compatibility": self.api_compatibility,
            "packages": self.packages,
            "platforms": self.platforms
        }


class UnityAdapter:
    """Adapter for Unity Engine operations."""
    
    UNITY_TEMPLATES = {
        "2d": "com.unity.template.2d",
        "3d": "com.unity.template.3d",
        "3d-extra": "com.unity.template.3d-extra",
        "urp-2d": "com.unity.template.universal-2d",
        "urp-3d": "com.unity.template.universal",
        "hdrp": "com.unity.template.hdrp-blank"
    }
    
    RENDER_PIPELINES = {
        "builtin": None,
        "urp": "com.unity.render-pipelines.universal",
        "hdrp": "com.unity.render-pipelines.high-definition"
    }
    
    COMMON_PACKAGES = {
        "input_system": "com.unity.inputsystem",
        "cinemachine": "com.unity.cinemachine",
        "ai_navigation": "com.unity.ai.navigation",
        "textmeshpro": "com.unity.textmeshpro",
        "timeline": "com.unity.timeline",
        "post_processing": "com.unity.postprocessing",
        "visual_scripting": "com.unity.visualscripting",
        "shader_graph": "com.unity.shadergraph",
        "vfx_graph": "com.unity.visualeffectgraph",
        "addressables": "com.unity.addressables",
        "entities": "com.unity.entities"
    }
    
    def __init__(self, unity_path: Optional[str] = None):
        self.unity_path = unity_path or self._find_unity_installation()
        self.projects_dir = Path.home() / "UnityProjects"
        
    def _find_unity_installation(self) -> Optional[str]:
        """Find Unity installation path."""
        # Platform-specific paths
        if os.name == 'nt':  # Windows
            paths = [
                r"C:\Program Files\Unity\Hub\Editor",
                r"C:\Program Files\Unity",
            ]
        elif os.name == 'posix':
            if os.path.exists("/Applications/Unity/Unity.app"):  # macOS
                paths = ["/Applications/Unity/Unity.app/Contents/MacOS"]
            else:  # Linux
                paths = ["/opt/Unity", "/usr/local/Unity"]
        else:
            paths = []
            
        for path in paths:
            if os.path.exists(path):
                return path
        return None
    
    def create_project(self, config: UnityProjectConfig, output_dir: Optional[str] = None) -> str:
        """Create a new Unity project."""
        project_dir = Path(output_dir or self.projects_dir) / config.name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create project structure
        self._create_project_structure(project_dir, config)
        
        # Create manifest.json
        self._create_manifest(project_dir, config)
        
        # Create ProjectSettings
        self._create_project_settings(project_dir, config)
        
        return str(project_dir)
    
    def _create_project_structure(self, project_dir: Path, config: UnityProjectConfig):
        """Create Unity project folder structure."""
        folders = [
            "Assets/Scripts",
            "Assets/Scripts/Controllers",
            "Assets/Scripts/Managers",
            "Assets/Scripts/Models",
            "Assets/Scripts/Utils",
            "Assets/Prefabs",
            "Assets/Scenes",
            "Assets/Resources",
            "Assets/Animations",
            "Assets/Audio",
            "Assets/Materials",
            "Assets/Textures",
            "Assets/Models",
            "Assets/Plugins",
            "Assets/Editor",
            "Packages",
            "ProjectSettings"
        ]
        
        for folder in folders:
            (project_dir / folder).mkdir(parents=True, exist_ok=True)
    
    def _create_manifest(self, project_dir: Path, config: UnityProjectConfig):
        """Create Packages/manifest.json."""
        manifest = {
            "dependencies": {
                "com.unity.collab-proxy": "2.0.0",
                "com.unity.feature.development": "1.0.0",
                "com.unity.ide.rider": "3.0.21",
                "com.unity.ide.visualstudio": "2.0.18",
                "com.unity.ide.vscode": "1.2.5",
                "com.unity.modules.ai": "1.0.0",
                "com.unity.modules.androidjni": "1.0.0",
                "com.unity.modules.animation": "1.0.0",
                "com.unity.modules.assetbundle": "1.0.0",
                "com.unity.modules.audio": "1.0.0",
                "com.unity.modules.cloth": "1.0.0",
                "com.unity.modules.director": "1.0.0",
                "com.unity.modules.imageconversion": "1.0.0",
                "com.unity.modules.imgui": "1.0.0",
                "com.unity.modules.jsonserialize": "1.0.0",
                "com.unity.modules.particlesystem": "1.0.0",
                "com.unity.modules.physics": "1.0.0",
                "com.unity.modules.physics2d": "1.0.0",
                "com.unity.modules.screencapture": "1.0.0",
                "com.unity.modules.terrain": "1.0.0",
                "com.unity.modules.terrainphysics": "1.0.0",
                "com.unity.modules.tilemap": "1.0.0",
                "com.unity.modules.ui": "1.0.0",
                "com.unity.modules.uielements": "1.0.0",
                "com.unity.modules.umbra": "1.0.0",
                "com.unity.modules.unityanalytics": "1.0.0",
                "com.unity.modules.unitywebrequest": "1.0.0",
                "com.unity.modules.unitywebrequestassetbundle": "1.0.0",
                "com.unity.modules.unitywebrequestaudio": "1.0.0",
                "com.unity.modules.unitywebrequesttexture": "1.0.0",
                "com.unity.modules.unitywebrequestwww": "1.0.0",
                "com.unity.modules.vehicles": "1.0.0",
                "com.unity.modules.video": "1.0.0",
                "com.unity.modules.vr": "1.0.0",
                "com.unity.modules.wind": "1.0.0",
                "com.unity.modules.xr": "1.0.0",
                "com.unity.test-framework": "1.1.33",
                "com.unity.textmeshpro": "3.0.6",
                "com.unity.timeline": "1.7.4",
                "com.unity.ugui": "1.0.0",
                "com.unity.visualscripting": "1.8.0"
            }
        }
        
        # Add render pipeline
        if config.render_pipeline == "urp":
            manifest["dependencies"]["com.unity.render-pipelines.universal"] = "14.0.8"
        elif config.render_pipeline == "hdrp":
            manifest["dependencies"]["com.unity.render-pipelines.high-definition"] = "14.0.8"
        
        # Add additional packages
        for package in config.packages:
            if package in self.COMMON_PACKAGES:
                pkg_name = self.COMMON_PACKAGES[package]
                manifest["dependencies"][pkg_name] = "latest"
        
        manifest_path = project_dir / "Packages" / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
    
    def _create_project_settings(self, project_dir: Path, config: UnityProjectConfig):
        """Create ProjectSettings files."""
        # ProjectVersion.txt
        version_path = project_dir / "ProjectSettings" / "ProjectVersion.txt"
        with open(version_path, 'w') as f:
            f.write(f"m_EditorVersion: {config.version}\n")
            f.write(f"m_EditorVersionWithRevision: {config.version} (unknown)\n")
        
        # ProjectSettings.asset
        project_settings = {
            "PlayerSettings": {
                "scriptingBackend": {
                    "Standalone": config.scripting_backend
                },
                "apiCompatibilityLevel": config.api_compatibility
            }
        }
        
        settings_path = project_dir / "ProjectSettings" / "ProjectSettings.asset"
        with open(settings_path, 'w') as f:
            json.dump(project_settings, f, indent=2)
    
    def build_project(self, project_path: str, target_platform: str, 
                      output_path: Optional[str] = None) -> bool:
        """Build Unity project for target platform."""
        if not self.unity_path:
            raise RuntimeError("Unity installation not found")
        
        build_methods = {
            "StandaloneWindows64": "Windows64",
            "StandaloneWindows": "Windows32",
            "StandaloneOSX": "MacOS",
            "StandaloneLinux64": "Linux64",
            "Android": "Android",
            "iOS": "iOS",
            "WebGL": "WebGL",
            "PS5": "PS5",
            "XboxOne": "XboxOne",
            "Switch": "Switch"
        }
        
        if target_platform not in build_methods:
            raise ValueError(f"Unsupported platform: {target_platform}")
        
        output = output_path or f"{project_path}/Builds/{target_platform}"
        
        # Build command
        cmd = [
            self.unity_path,
            "-batchmode",
            "-nographics",
            "-quit",
            "-projectPath", project_path,
            "-buildTarget", target_platform,
            "-executeMethod", f"BuildScript.Build{build_methods[target_platform]}",
            "-logFile", f"{project_path}/build.log"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
        except Exception as e:
            print(f"Build error: {e}")
            return False
    
    def add_package(self, project_path: str, package_name: str, 
                    version: str = "latest") -> bool:
        """Add a package to Unity project."""
        manifest_path = Path(project_path) / "Packages" / "manifest.json"
        
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            manifest["dependencies"][package_name] = version
            
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Failed to add package: {e}")
            return False
    
    def get_project_info(self, project_path: str) -> Dict[str, Any]:
        """Get Unity project information."""
        info = {
            "path": project_path,
            "name": Path(project_path).name,
            "version": None,
            "packages": [],
            "scenes": []
        }
        
        # Read version
        version_path = Path(project_path) / "ProjectSettings" / "ProjectVersion.txt"
        if version_path.exists():
            with open(version_path, 'r') as f:
                for line in f:
                    if "m_EditorVersion:" in line:
                        info["version"] = line.split(":")[1].strip()
        
        # Read packages
        manifest_path = Path(project_path) / "Packages" / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                info["packages"] = list(manifest.get("dependencies", {}).keys())
        
        # Find scenes
        scenes_path = Path(project_path) / "Assets" / "Scenes"
        if scenes_path.exists():
            info["scenes"] = [str(f) for f in scenes_path.glob("*.unity")]
        
        return info
