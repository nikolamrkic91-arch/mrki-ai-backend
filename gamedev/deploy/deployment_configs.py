"""
Deployment Configurations
Cross-platform deployment settings for different game engines.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json


class Platform(Enum):
    """Supported deployment platforms."""
    WINDOWS = "windows"
    MAC = "mac"
    LINUX = "linux"
    ANDROID = "android"
    IOS = "ios"
    WEBGL = "webgl"
    CONSOLE_PS5 = "ps5"
    CONSOLE_XBOX = "xbox"
    CONSOLE_SWITCH = "switch"


class BuildType(Enum):
    """Build types."""
    DEBUG = "debug"
    DEVELOPMENT = "development"
    RELEASE = "release"


@dataclass
class PlatformConfig:
    """Platform-specific configuration."""
    platform: Platform
    enabled: bool = True
    build_type: BuildType = BuildType.DEVELOPMENT
    output_path: str = ""
    additional_settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform.value,
            "enabled": self.enabled,
            "build_type": self.build_type.value,
            "output_path": self.output_path,
            "additional_settings": self.additional_settings
        }


class DeploymentManager:
    """Manages deployment configurations for multiple platforms."""
    
    def __init__(self):
        self.platforms: Dict[Platform, PlatformConfig] = {}
        self._initialize_default_platforms()
    
    def _initialize_default_platforms(self):
        """Initialize default platform configurations."""
        # Windows
        self.platforms[Platform.WINDOWS] = PlatformConfig(
            platform=Platform.WINDOWS,
            output_path="Builds/Windows",
            additional_settings={
                "architecture": "x64",
                "scripting_backend": "il2cpp"
            }
        )
        
        # Mac
        self.platforms[Platform.MAC] = PlatformConfig(
            platform=Platform.MAC,
            output_path="Builds/Mac",
            additional_settings={
                "architecture": "x64",
                "target_osx_version": "10.14"
            }
        )
        
        # Linux
        self.platforms[Platform.LINUX] = PlatformConfig(
            platform=Platform.LINUX,
            output_path="Builds/Linux",
            additional_settings={
                "architecture": "x64"
            }
        )
        
        # Android
        self.platforms[Platform.ANDROID] = PlatformConfig(
            platform=Platform.ANDROID,
            enabled=False,
            output_path="Builds/Android",
            additional_settings={
                "min_sdk_version": 28,
                "target_sdk_version": 33,
                "architecture": "arm64"
            }
        )
        
        # iOS
        self.platforms[Platform.IOS] = PlatformConfig(
            platform=Platform.IOS,
            enabled=False,
            output_path="Builds/iOS",
            additional_settings={
                "target_version": "14.0"
            }
        )
        
        # WebGL
        self.platforms[Platform.WEBGL] = PlatformConfig(
            platform=Platform.WEBGL,
            enabled=False,
            output_path="Builds/WebGL",
            additional_settings={
                "compression_format": "gzip",
                "template": "default"
            }
        )
    
    def get_config(self, platform: Platform) -> Optional[PlatformConfig]:
        """Get configuration for a platform."""
        return self.platforms.get(platform)
    
    def set_config(self, config: PlatformConfig):
        """Set configuration for a platform."""
        self.platforms[config.platform] = config
    
    def enable_platform(self, platform: Platform):
        """Enable a platform for building."""
        if platform in self.platforms:
            self.platforms[platform].enabled = True
    
    def disable_platform(self, platform: Platform):
        """Disable a platform for building."""
        if platform in self.platforms:
            self.platforms[platform].enabled = False
    
    def get_enabled_platforms(self) -> List[PlatformConfig]:
        """Get all enabled platform configurations."""
        return [config for config in self.platforms.values() if config.enabled]
    
    def export_to_json(self, filepath: str):
        """Export configurations to JSON."""
        data = {
            "platforms": [config.to_dict() for config in self.platforms.values()]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def import_from_json(self, filepath: str):
        """Import configurations from JSON."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        for platform_data in data.get("platforms", []):
            platform = Platform(platform_data["platform"])
            config = PlatformConfig(
                platform=platform,
                enabled=platform_data["enabled"],
                build_type=BuildType(platform_data["build_type"]),
                output_path=platform_data["output_path"],
                additional_settings=platform_data.get("additional_settings", {})
            )
            self.set_config(config)
    
    # Unity-specific configurations
    
    @staticmethod
    def generate_unity_build_script() -> str:
        """Generate Unity build script."""
        return '''using UnityEditor;
using UnityEngine;
using System.Collections.Generic;
using System.Linq;

public static class BuildScript
{
    private static readonly Dictionary<BuildTarget, string> TargetNames = new Dictionary<BuildTarget, string>
    {
        { BuildTarget.StandaloneWindows64, "Windows64" },
        { BuildTarget.StandaloneOSX, "Mac" },
        { BuildTarget.StandaloneLinux64, "Linux64" },
        { BuildTarget.Android, "Android" },
        { BuildTarget.iOS, "iOS" },
        { BuildTarget.WebGL, "WebGL" }
    };

    [MenuItem("Build/Build All Platforms")]
    public static void BuildAllPlatforms()
    {
        BuildWindows64();
        BuildMac();
        BuildLinux64();
    }

    [MenuItem("Build/Build Windows")]
    public static void BuildWindows64()
    {
        Build(BuildTarget.StandaloneWindows64, "Windows64");
    }

    [MenuItem("Build/Build Mac")]
    public static void BuildMac()
    {
        Build(BuildTarget.StandaloneOSX, "Mac");
    }

    [MenuItem("Build/Build Linux")]
    public static void BuildLinux64()
    {
        Build(BuildTarget.StandaloneLinux64, "Linux64");
    }

    [MenuItem("Build/Build Android")]
    public static void BuildAndroid()
    {
        Build(BuildTarget.Android, "Android");
    }

    [MenuItem("Build/Build iOS")]
    public static void BuildiOS()
    {
        Build(BuildTarget.iOS, "iOS");
    }

    [MenuItem("Build/Build WebGL")]
    public static void BuildWebGL()
    {
        Build(BuildTarget.WebGL, "WebGL");
    }

    private static void Build(BuildTarget target, string folderName)
    {
        string[] scenes = EditorBuildSettings.scenes
            .Where(s => s.enabled)
            .Select(s => s.path)
            .ToArray();

        string buildPath = $"Builds/{folderName}";

        BuildPlayerOptions buildOptions = new BuildPlayerOptions
        {
            scenes = scenes,
            locationPathName = buildPath,
            target = target,
            options = BuildOptions.None
        };

        BuildPipeline.BuildPlayer(buildOptions);
        
        Debug.Log($"Build completed for {target}");
    }
}
'''
    
    @staticmethod
    def generate_unity_cloud_build_config() -> Dict[str, Any]:
        """Generate Unity Cloud Build configuration."""
        return {
            "projectName": "MyGame",
            "buildTargets": [
                {
                    "name": "Windows-64",
                    "platform": "standalonewindows64",
                    "enabled": True,
                    "buildSubFolder": "windows"
                },
                {
                    "name": "Mac-Universal",
                    "platform": "standaloneosxuniversal",
                    "enabled": True,
                    "buildSubFolder": "mac"
                },
                {
                    "name": "Linux-64",
                    "platform": "standalonelinux64",
                    "enabled": True,
                    "buildSubFolder": "linux"
                },
                {
                    "name": "Android",
                    "platform": "android",
                    "enabled": False,
                    "buildSubFolder": "android"
                },
                {
                    "name": "iOS",
                    "platform": "ios",
                    "enabled": False,
                    "buildSubFolder": "ios"
                },
                {
                    "name": "WebGL",
                    "platform": "webgl",
                    "enabled": False,
                    "buildSubFolder": "webgl"
                }
            ]
        }
    
    # Unreal-specific configurations
    
    @staticmethod
    def generate_unreal_build_script() -> str:
        """Generate Unreal build script."""
        return '''using UnrealBuildTool;
using System.Collections.Generic;

public class BuildScript : ModuleRules
{
    public BuildScript(ReadOnlyTargetRules Target) : base(Target)
    {
        // Build configuration
    }
}

// Build command examples:
// Windows: "C:\\Program Files\\Epic Games\\UE_5.3\\Engine\\Build\\BatchFiles\\RunUAT.bat" BuildCookRun -project="Path\\To\\Project.uproject" -platform=Win64 -clientconfig=Development -cook -build -stage -pak -archive -archivedirectory="Path\\To\\Output"
// Mac: "/Users/Shared/Epic Games/UE_5.3/Engine/Build/BatchFiles/RunUAT.sh" BuildCookRun -project="Path/To/Project.uproject" -platform=Mac -clientconfig=Development -cook -build -stage -pak -archive -archivedirectory="Path/To/Output"
// Linux: "/opt/UnrealEngine/Engine/Build/BatchFiles/RunUAT.sh" BuildCookRun -project="Path/To/Project.uproject" -platform=Linux -clientconfig=Development -cook -build -stage -pak -archive -archivedirectory="Path/To/Output"
// Android: "Path/To/RunUAT" BuildCookRun -project="Path/To/Project.uproject" -platform=Android -clientconfig=Development -cook -build -stage -pak -archive -archivedirectory="Path/To/Output"
// iOS: "Path/To/RunUAT" BuildCookRun -project="Path/To/Project.uproject" -platform=IOS -clientconfig=Development -cook -build -stage -pak -archive -archivedirectory="Path/To/Output"
'''
    
    # Godot-specific configurations
    
    @staticmethod
    def generate_godot_export_presets() -> Dict[str, Any]:
        """Generate Godot export presets."""
        return {
            "preset.0.name": "Windows Desktop",
            "preset.0.platform": "Windows Desktop",
            "preset.0.runnable": True,
            "preset.0.export_filter": "all_resources",
            "preset.0.export_path": "Builds/Windows/MyGame.exe",
            "preset.0.encryption_include_filters": "",
            "preset.0.encryption_exclude_filters": "",
            "preset.0.encrypt_pck": False,
            "preset.0.encrypt_directory": False,
            "preset.0.script_export_mode": 2,
            
            "preset.1.name": "macOS",
            "preset.1.platform": "macOS",
            "preset.1.runnable": False,
            "preset.1.export_filter": "all_resources",
            "preset.1.export_path": "Builds/Mac/MyGame.zip",
            
            "preset.2.name": "Linux/X11",
            "preset.2.platform": "Linux/X11",
            "preset.2.runnable": False,
            "preset.2.export_filter": "all_resources",
            "preset.2.export_path": "Builds/Linux/MyGame.x86_64",
            
            "preset.3.name": "Android",
            "preset.3.platform": "Android",
            "preset.3.runnable": False,
            "preset.3.export_filter": "all_resources",
            "preset.3.export_path": "Builds/Android/MyGame.apk",
            
            "preset.4.name": "iOS",
            "preset.4.platform": "iOS",
            "preset.4.runnable": False,
            "preset.4.export_filter": "all_resources",
            "preset.4.export_path": "Builds/iOS/MyGame.ipa",
            
            "preset.5.name": "Web",
            "preset.5.platform": "Web",
            "preset.5.runnable": False,
            "preset.5.export_filter": "all_resources",
            "preset.5.export_path": "Builds/Web/index.html"
        }
    
    @staticmethod
    def generate_godot_export_script() -> str:
        """Generate Godot export script."""
        return '''#!/bin/bash

# Godot Export Script
# Usage: ./export_game.sh [platform]

GODOT_PATH="/usr/bin/godot"
PROJECT_PATH="$(pwd)"
BUILD_PATH="$PROJECT_PATH/Builds"

# Create build directory
mkdir -p "$BUILD_PATH"

# Export function
export_platform() {
    local platform=$1
    local preset=$2
    local output=$3
    
    echo "Exporting for $platform..."
    $GODOT_PATH --headless --path "$PROJECT_PATH" --export-release "$preset" "$BUILD_PATH/$output"
    
    if [ $? -eq 0 ]; then
        echo "✓ $platform export successful"
    else
        echo "✗ $platform export failed"
    fi
}

# Export based on argument
case "$1" in
    "windows")
        export_platform "Windows" "Windows Desktop" "Windows/MyGame.exe"
        ;;
    "mac")
        export_platform "macOS" "macOS" "Mac/MyGame.zip"
        ;;
    "linux")
        export_platform "Linux" "Linux/X11" "Linux/MyGame.x86_64"
        ;;
    "android")
        export_platform "Android" "Android" "Android/MyGame.apk"
        ;;
    "ios")
        export_platform "iOS" "iOS" "iOS/MyGame.ipa"
        ;;
    "web")
        export_platform "Web" "Web" "Web/index.html"
        ;;
    "all"|"")
        export_platform "Windows" "Windows Desktop" "Windows/MyGame.exe"
        export_platform "macOS" "macOS" "Mac/MyGame.zip"
        export_platform "Linux" "Linux/X11" "Linux/MyGame.x86_64"
        ;;
    *)
        echo "Unknown platform: $1"
        echo "Usage: $0 [windows|mac|linux|android|ios|web|all]"
        exit 1
        ;;
esac

echo "Export complete!"
'''
    
    # CI/CD configurations
    
    @staticmethod
    def generate_github_actions_workflow(engine: str = "unity") -> str:
        """Generate GitHub Actions workflow for game builds."""
        if engine == "unity":
            return '''name: Build Game

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Cache Library
      uses: actions/cache@v3
      with:
        path: Library
        key: Library-${{ hashFiles('Assets/**', 'Packages/**', 'ProjectSettings/**') }}
    
    - name: Build Windows
      uses: game-ci/unity-builder@v3
      env:
        UNITY_LICENSE: ${{ secrets.UNITY_LICENSE }}
        UNITY_EMAIL: ${{ secrets.UNITY_EMAIL }}
        UNITY_PASSWORD: ${{ secrets.UNITY_PASSWORD }}
      with:
        targetPlatform: StandaloneWindows64
        buildName: MyGame-Windows
    
    - name: Upload Build
      uses: actions/upload-artifact@v3
      with:
        name: Build-Windows
        path: build/StandaloneWindows64

  build-mac:
    runs-on: macos-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Cache Library
      uses: actions/cache@v3
      with:
        path: Library
        key: Library-${{ hashFiles('Assets/**', 'Packages/**', 'ProjectSettings/**') }}
    
    - name: Build macOS
      uses: game-ci/unity-builder@v3
      env:
        UNITY_LICENSE: ${{ secrets.UNITY_LICENSE }}
        UNITY_EMAIL: ${{ secrets.UNITY_EMAIL }}
        UNITY_PASSWORD: ${{ secrets.UNITY_PASSWORD }}
      with:
        targetPlatform: StandaloneOSX
        buildName: MyGame-Mac
    
    - name: Upload Build
      uses: actions/upload-artifact@v3
      with:
        name: Build-Mac
        path: build/StandaloneOSX

  build-linux:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Cache Library
      uses: actions/cache@v3
      with:
        path: Library
        key: Library-${{ hashFiles('Assets/**', 'Packages/**', 'ProjectSettings/**') }}
    
    - name: Build Linux
      uses: game-ci/unity-builder@v3
      env:
        UNITY_LICENSE: ${{ secrets.UNITY_LICENSE }}
        UNITY_EMAIL: ${{ secrets.UNITY_EMAIL }}
        UNITY_PASSWORD: ${{ secrets.UNITY_PASSWORD }}
      with:
        targetPlatform: StandaloneLinux64
        buildName: MyGame-Linux
    
    - name: Upload Build
      uses: actions/upload-artifact@v3
      with:
        name: Build-Linux
        path: build/StandaloneLinux64
'''
        elif engine == "godot":
            return '''name: Build Game

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-windows:
    runs-on: ubuntu-latest
    container:
      image: barichello/godot-ci:4.2
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup
      run: |
        mkdir -v -p ~/.local/share/godot/export_templates/
        mv /root/.local/share/godot/export_templates/* ~/.local/share/godot/export_templates/
    
    - name: Build Windows
      run: |
        mkdir -p build/windows
        godot --headless --verbose --export-release "Windows Desktop" build/windows/MyGame.exe
    
    - name: Upload Build
      uses: actions/upload-artifact@v3
      with:
        name: Build-Windows
        path: build/windows

  build-linux:
    runs-on: ubuntu-latest
    container:
      image: barichello/godot-ci:4.2
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup
      run: |
        mkdir -v -p ~/.local/share/godot/export_templates/
        mv /root/.local/share/godot/export_templates/* ~/.local/share/godot/export_templates/
    
    - name: Build Linux
      run: |
        mkdir -p build/linux
        godot --headless --verbose --export-release "Linux/X11" build/linux/MyGame.x86_64
    
    - name: Upload Build
      uses: actions/upload-artifact@v3
      with:
        name: Build-Linux
        path: build/linux

  build-web:
    runs-on: ubuntu-latest
    container:
      image: barichello/godot-ci:4.2
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup
      run: |
        mkdir -v -p ~/.local/share/godot/export_templates/
        mv /root/.local/share/godot/export_templates/* ~/.local/share/godot/export_templates/
    
    - name: Build Web
      run: |
        mkdir -p build/web
        godot --headless --verbose --export-release "Web" build/web/index.html
    
    - name: Upload Build
      uses: actions/upload-artifact@v3
      with:
        name: Build-Web
        path: build/web
'''
        else:
            return "# CI/CD workflow not available for this engine"
