"""
Unreal Engine Adapter for Mrki
Handles Unreal project creation, management, and integration.
"""

import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class UnrealProjectConfig:
    """Configuration for Unreal project creation."""
    name: str
    version: str = "5.3"
    template: str = "blank"  # blank, firstperson, thirdperson, topdown, sidescroller
    quality: str = "maximum"  # scalable, maximum
    target_platforms: List[str] = field(default_factory=lambda: ["Windows", "Mac", "Linux"])
    plugins: List[str] = field(default_factory=list)
    starter_content: bool = True
    raytracing: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "template": self.template,
            "quality": self.quality,
            "target_platforms": self.target_platforms,
            "plugins": self.plugins,
            "starter_content": self.starter_content,
            "raytracing": self.raytracing
        }


class UnrealAdapter:
    """Adapter for Unreal Engine operations."""
    
    UNREAL_TEMPLATES = {
        "blank": "Blank",
        "firstperson": "FirstPerson",
        "thirdperson": "ThirdPerson",
        "topdown": "TopDown",
        "sidescroller": "SideScroller",
        "twinstick": "TwinStick",
        "puzzle": "Puzzle",
        "rpg": "RPG",
        "strategy": "Strategy"
    }
    
    COMMON_PLUGINS = {
        " Niagara": "Niagara",
        "chaos": "ChaosVehiclesPlugin",
        "water": "Water",
        "landmass": "Landmass",
        "control_rig": "ControlRig",
        "sequencer": "LevelSequenceEditor",
        "paper2d": "Paper2D",
        "online_subsystem": "OnlineSubsystem",
        "online_subsystem_steam": "OnlineSubsystemSteam",
        "gameplay_abilities": "GameplayAbilities",
        "enhanced_input": "EnhancedInput",
        "common_ui": "CommonUI",
        "modular_gameplay": "ModularGameplay"
    }
    
    def __init__(self, engine_path: Optional[str] = None):
        self.engine_path = engine_path or self._find_unreal_installation()
        self.projects_dir = Path.home() / "UnrealProjects"
        
    def _find_unreal_installation(self) -> Optional[str]:
        """Find Unreal Engine installation path."""
        if os.name == 'nt':  # Windows
            paths = [
                r"C:\Program Files\Epic Games\UE_5.3",
                r"C:\Program Files\Epic Games\UE_5.2",
                r"C:\Program Files\Epic Games\UE_5.1",
                r"C:\Program Files\Epic Games\UE_5.0",
            ]
        elif os.name == 'posix':
            if os.path.exists("/Users/Shared/Epic Games"):  # macOS
                paths = [
                    "/Users/Shared/Epic Games/UE_5.3",
                    "/Users/Shared/Epic Games/UE_5.2",
                ]
            else:  # Linux
                paths = [
                    "/opt/UnrealEngine",
                    "/usr/local/UnrealEngine"
                ]
        else:
            paths = []
            
        for path in paths:
            if os.path.exists(path):
                return path
        return None
    
    def create_project(self, config: UnrealProjectConfig, output_dir: Optional[str] = None) -> str:
        """Create a new Unreal project."""
        project_dir = Path(output_dir or self.projects_dir) / config.name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create project structure
        self._create_project_structure(project_dir, config)
        
        # Create .uproject file
        self._create_uproject(project_dir, config)
        
        # Create Config files
        self._create_config_files(project_dir, config)
        
        # Create Source structure for C++
        self._create_source_structure(project_dir, config)
        
        # Create Content folders
        self._create_content_structure(project_dir, config)
        
        return str(project_dir)
    
    def _create_project_structure(self, project_dir: Path, config: UnrealProjectConfig):
        """Create Unreal project folder structure."""
        folders = [
            "Config",
            "Config/Default",
            "Content",
            "Content/Blueprints",
            "Content/Blueprints/Actors",
            "Content/Blueprints/Components",
            "Content/Blueprints/GameModes",
            "Content/Blueprints/Player",
            "Content/Blueprints/AI",
            "Content/Blueprints/UI",
            "Content/Maps",
            "Content/Materials",
            "Content/Meshes",
            "Content/Textures",
            "Content/Audio",
            "Content/Animations",
            "Content/Particles",
            "Content/Data",
            "Plugins",
            "Source",
            f"Source/{config.name}",
            f"Source/{config.name}/Private",
            f"Source/{config.name}/Public",
            "Saved",
            "Intermediate",
            "Build"
        ]
        
        for folder in folders:
            (project_dir / folder).mkdir(parents=True, exist_ok=True)
    
    def _create_uproject(self, project_dir: Path, config: UnrealProjectConfig):
        """Create .uproject file."""
        uproject = {
            "FileVersion": 3,
            "EngineAssociation": config.version,
            "Category": "",
            "Description": "",
            "Modules": [
                {
                    "Name": config.name,
                    "Type": "Runtime",
                    "LoadingPhase": "Default"
                }
            ],
            "Plugins": [],
            "TargetPlatforms": config.target_platforms
        }
        
        # Add default plugins
        default_plugins = [
            {"Name": "ModelingToolsEditorMode", "Enabled": True},
            {"Name": "EnhancedInput", "Enabled": True}
        ]
        
        if config.starter_content:
            default_plugins.append({"Name": "StarterContent", "Enabled": True})
        
        for plugin in config.plugins:
            if plugin in self.COMMON_PLUGINS:
                default_plugins.append({
                    "Name": self.COMMON_PLUGINS[plugin],
                    "Enabled": True
                })
        
        uproject["Plugins"] = default_plugins
        
        uproject_path = project_dir / f"{config.name}.uproject"
        with open(uproject_path, 'w') as f:
            json.dump(uproject, f, indent=2)
    
    def _create_config_files(self, project_dir: Path, config: UnrealProjectConfig):
        """Create configuration files."""
        config_dir = project_dir / "Config"
        
        # DefaultEngine.ini
        engine_ini = f"""[/Script/Engine.Engine]
+ActiveGameNameRedirects=(OldGameName="TP_Blank",NewGameName="{config.name}")
+ActiveGameNameRedirects=(OldGameName="/Script/TP_Blank",NewGameName="/Script/{config.name}")
+ActiveClassRedirects=(OldClassName="TP_BlankGameModeBase",NewClassName="{config.name}GameMode")

[/Script/Engine.RendererSettings]
r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange=True
r.DefaultFeature.AutoExposure=False
r.DefaultFeature.MotionBlur=False
r.Shadow.Virtual.Enable=1
r.RayTracing={'true' if config.raytracing else 'false'}

[/Script/EngineSettings.GameMapsSettings]
EditorStartupMap=/Game/Maps/MainMenu.MainMenu
GameDefaultMap=/Game/Maps/MainMenu.MainMenu
TransitionMap=/Game/Maps/Transition.Transition
bUseSplitscreen=True
TwoPlayerSplitscreenLayout=Horizontal
ThreePlayerSplitscreenLayout=FavorTop
GlobalDefaultGameMode=/Game/Blueprints/GameModes/BP_{config.name}GameMode.BP_{config.name}GameMode_C
GlobalDefaultServerGameMode=None

[/Script/IOSRuntimeSettings.IOSRuntimeSettings]
MinimumiOSVersion=IOS_14

[/Script/AndroidRuntimeSettings.AndroidRuntimeSettings]
MinSDKVersion=28
TargetSDKVersion=30
bPackageDataInsideApk=True
"""
        
        with open(config_dir / "DefaultEngine.ini", 'w') as f:
            f.write(engine_ini)
        
        # DefaultGame.ini
        game_ini = f"""[/Script/Engine.GameSession]
MaxPlayers=16

[/Script/Engine.GameNetworkManager]
MaxIdleTime=0
DefaultMaxTimeMargin=0
TimeMarginSlack=1.35
DefaultMinTimeMargin=-1
MinTimeMarginSlack=1.1
"""
        
        with open(config_dir / "DefaultGame.ini", 'w') as f:
            f.write(game_ini)
        
        # DefaultInput.ini
        input_ini = """[/Script/Engine.InputSettings]
bAltEnterTogglesFullscreen=True
bF11TogglesFullscreen=True
bUseFixedBrakingDistancePaths=False
bUseFixedPathBrakingDistancePaths=False
bAlwaysShowTouchInterface=False
bShowConsoleOnFourFingerTap=True
bEnableGestureRecognizer=False
bUseAutocorrect=False
DefaultViewportMouseCaptureMode=CapturePermanently_IncludingInitialMouseDown
DefaultViewportMouseLockMode=LockOnCapture
FOVScale=0.011110
DoubleClickTime=0.200000
DefaultTouchInterface=/Engine/MobileResources/HUD/DefaultVirtualJoysticks.DefaultVirtualJoysticks
+ConsoleKeys=Tilde
"""
        
        with open(config_dir / "DefaultInput.ini", 'w') as f:
            f.write(input_ini)
    
    def _create_source_structure(self, project_dir: Path, config: UnrealProjectConfig):
        """Create C++ source files."""
        source_dir = project_dir / "Source" / config.name
        
        # Build.cs
        build_cs = f"""using UnrealBuildTool;

public class {config.name} : ModuleRules
{{
    public {config.name}(ReadOnlyTargetRules Target) : base(Target)
    {{
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[] {{
            "Core",
            "CoreUObject",
            "Engine",
            "InputCore",
            "EnhancedInput"
        }});

        PrivateDependencyModuleNames.AddRange(new string[] {{ }});
    }}
}}
"""
        
        with open(source_dir / f"{config.name}.Build.cs", 'w') as f:
            f.write(build_cs)
        
        # Target.cs
        target_cs = f"""using UnrealBuildTool;
using System.Collections.Generic;

public class {config.name}Target : TargetRules
{{
    public {config.name}Target(TargetInfo Target) : base(Target)
    {{
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V4;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_3;
        ExtraModuleNames.Add("{config.name}");
    }}
}}
"""
        
        with open(project_dir / "Source" / f"{config.name}.Target.cs", 'w') as f:
            f.write(target_cs)
        
        # Editor Target.cs
        editor_target_cs = f"""using UnrealBuildTool;
using System.Collections.Generic;

public class {config.name}EditorTarget : TargetRules
{{
    public {config.name}EditorTarget(TargetInfo Target) : base(Target)
    {{
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V4;
        IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_3;
        ExtraModuleNames.Add("{config.name}");
    }}
}}
"""
        
        with open(project_dir / "Source" / f"{config.name}Editor.Target.cs", 'w') as f:
            f.write(editor_target_cs)
        
        # GameMode header
        gamemode_h = f"""#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "{config.name}GameMode.generated.h"

UCLASS()
class {config.name.upper()}_API A{config.name}GameMode : public AGameModeBase
{{
    GENERATED_BODY()

public:
    A{config.name}GameMode();

    virtual void InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage) override;
    virtual void BeginPlay() override;
}};
"""
        
        with open(source_dir / "Public" / f"{config.name}GameMode.h", 'w') as f:
            f.write(gamemode_h)
        
        # GameMode cpp
        gamemode_cpp = f"""#include "{config.name}GameMode.h"

A{config.name}GameMode::A{config.name}GameMode()
{{
    // Set default pawn class
    // DefaultPawnClass = A{config.name}Character::StaticClass();
}}

void A{config.name}GameMode::InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage)
{{
    Super::InitGame(MapName, Options, ErrorMessage);
}}

void A{config.name}GameMode::BeginPlay()
{{
    Super::BeginPlay();
}}
"""
        
        with open(source_dir / "Private" / f"{config.name}GameMode.cpp", 'w') as f:
            f.write(gamemode_cpp)
    
    def _create_content_structure(self, project_dir: Path, config: UnrealProjectConfig):
        """Create content folder structure with placeholder files."""
        content_dir = project_dir / "Content"
        
        # Create placeholder files to track folders in git
        placeholder_content = "# Placeholder file for folder tracking\n"
        
        folders = [
            "Blueprints/Actors",
            "Blueprints/Components", 
            "Blueprints/GameModes",
            "Blueprints/Player",
            "Blueprints/AI",
            "Blueprints/UI",
            "Maps",
            "Materials",
            "Meshes",
            "Textures",
            "Audio",
            "Animations",
            "Particles",
            "Data"
        ]
        
        for folder in folders:
            placeholder = content_dir / folder / ".gitkeep"
            placeholder.parent.mkdir(parents=True, exist_ok=True)
            with open(placeholder, 'w') as f:
                f.write(placeholder_content)
    
    def add_plugin(self, project_path: str, plugin_name: str) -> bool:
        """Add a plugin to Unreal project."""
        uproject_path = Path(project_path)
        if uproject_path.is_dir():
            uproject_files = list(uproject_path.glob("*.uproject"))
            if not uproject_files:
                return False
            uproject_path = uproject_files[0]
        
        try:
            with open(uproject_path, 'r') as f:
                uproject = json.load(f)
            
            if plugin_name not in self.COMMON_PLUGINS:
                return False
            
            plugin_entry = {
                "Name": self.COMMON_PLUGINS[plugin_name],
                "Enabled": True
            }
            
            if "Plugins" not in uproject:
                uproject["Plugins"] = []
            
            # Check if already exists
            if not any(p.get("Name") == plugin_entry["Name"] for p in uproject["Plugins"]):
                uproject["Plugins"].append(plugin_entry)
            
            with open(uproject_path, 'w') as f:
                json.dump(uproject, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Failed to add plugin: {e}")
            return False
    
    def get_project_info(self, project_path: str) -> Dict[str, Any]:
        """Get Unreal project information."""
        info = {
            "path": project_path,
            "name": Path(project_path).name,
            "version": None,
            "plugins": [],
            "modules": [],
            "maps": []
        }
        
        # Read uproject
        uproject_files = list(Path(project_path).glob("*.uproject"))
        if uproject_files:
            with open(uproject_files[0], 'r') as f:
                uproject = json.load(f)
                info["version"] = uproject.get("EngineAssociation")
                info["plugins"] = [p.get("Name") for p in uproject.get("Plugins", [])]
                info["modules"] = [m.get("Name") for m in uproject.get("Modules", [])]
        
        # Find maps
        maps_path = Path(project_path) / "Content" / "Maps"
        if maps_path.exists():
            info["maps"] = [str(f) for f in maps_path.glob("*.umap")]
        
        return info
