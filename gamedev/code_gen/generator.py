#!/usr/bin/env python3
"""
Mrki Game Code Generator
Generates game code from templates for Unity, Unreal Engine, and Godot.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class EngineType(Enum):
    UNITY = "unity"
    UNREAL = "unreal"
    GODOT = "godot"


class TemplateType(Enum):
    PLAYER_CONTROLLER = "player_controller"
    GAME_MANAGER = "game_manager"
    STATE_MACHINE = "state_machine"
    ACTOR_BASE = "actor_base"
    CHARACTER_BASE = "character_base"


@dataclass
class GenerationResult:
    """Result of code generation"""
    success: bool
    code: str
    file_path: Optional[str]
    error: Optional[str] = None


class GameCodeGenerator:
    """Main code generator for game development"""
    
    def __init__(self, templates_dir: Optional[str] = None):
        if templates_dir is None:
            self.templates_dir = Path(__file__).parent.parent
        else:
            self.templates_dir = Path(templates_dir)
    
    def _get_template_path(self, engine: EngineType, template: TemplateType) -> Path:
        """Get the path to a template file"""
        template_map = {
            (EngineType.UNITY, TemplateType.PLAYER_CONTROLLER): "unity/templates/PlayerController.cs",
            (EngineType.UNITY, TemplateType.GAME_MANAGER): "unity/templates/GameManager.cs",
            (EngineType.UNITY, TemplateType.STATE_MACHINE): "unity/templates/StateMachine.cs",
            (EngineType.UNREAL, TemplateType.ACTOR_BASE): "unreal/templates/ActorBase.h",
            (EngineType.UNREAL, TemplateType.CHARACTER_BASE): "unreal/templates/CharacterBase.h",
            (EngineType.GODOT, TemplateType.PLAYER_CONTROLLER): "godot/templates/player_controller.gd",
            (EngineType.GODOT, TemplateType.GAME_MANAGER): "godot/templates/game_manager.gd",
            (EngineType.GODOT, TemplateType.STATE_MACHINE): "godot/templates/state_machine.gd",
        }
        
        key = (engine, template)
        if key not in template_map:
            raise ValueError(f"Template {template.value} not available for {engine.value}")
        
        return self.templates_dir / template_map[key]
    
    def _load_template(self, template_path: Path) -> str:
        """Load template content from file"""
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        return template_path.read_text(encoding='utf-8')
    
    def _process_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Replace template variables with actual values"""
        result = template
        for key, value in variables.items():
            pattern = r'\{\{\s*' + re.escape(key) + r'\s*\}\}'
            result = re.sub(pattern, str(value), result)
        return result
    
    def generate(
        self,
        engine: EngineType,
        template: TemplateType,
        class_name: str,
        namespace: str = "MyGame",
        description: str = "",
        output_path: Optional[str] = None,
        extra_vars: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """
        Generate code from a template.
        
        Args:
            engine: Target game engine
            template: Type of template to use
            class_name: Name of the generated class
            namespace: Namespace/module name
            description: Class description
            output_path: Where to save the file (optional)
            extra_vars: Additional template variables
        
        Returns:
            GenerationResult with the generated code
        """
        try:
            # Load template
            template_path = self._get_template_path(engine, template)
            template_content = self._load_template(template_path)
            
            # Prepare variables
            variables = {
                "class_name": class_name,
                "namespace": namespace,
                "description": description or f"{class_name} generated class",
            }
            
            # Engine-specific variables
            if engine == EngineType.UNREAL:
                variables["api_macro"] = f"{namespace.upper()}_API"
            elif engine == EngineType.GODOT:
                variables["dont_destroy_on_load"] = "true"
            
            # Add extra variables
            if extra_vars:
                variables.update(extra_vars)
            
            # Process template
            generated_code = self._process_template(template_content, variables)
            
            # Save to file if path provided
            file_path = None
            if output_path:
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(generated_code, encoding='utf-8')
                file_path = str(output_file)
            
            return GenerationResult(
                success=True,
                code=generated_code,
                file_path=file_path
            )
            
        except Exception as e:
            return GenerationResult(
                success=False,
                code="",
                file_path=None,
                error=str(e)
            )
    
    def generate_player_controller(
        self,
        engine: EngineType,
        class_name: str,
        **kwargs
    ) -> GenerationResult:
        """Generate a player controller class"""
        return self.generate(
            engine=engine,
            template=TemplateType.PLAYER_CONTROLLER,
            class_name=class_name,
            **kwargs
        )
    
    def generate_game_manager(
        self,
        engine: EngineType,
        class_name: str,
        **kwargs
    ) -> GenerationResult:
        """Generate a game manager class"""
        return self.generate(
            engine=engine,
            template=TemplateType.GAME_MANAGER,
            class_name=class_name,
            **kwargs
        )
    
    def generate_state_machine(
        self,
        engine: EngineType,
        class_name: str,
        **kwargs
    ) -> GenerationResult:
        """Generate a state machine class"""
        return self.generate(
            engine=engine,
            template=TemplateType.STATE_MACHINE,
            class_name=class_name,
            **kwargs
        )
    
    def list_templates(self) -> Dict[str, List[str]]:
        """List all available templates"""
        return {
            "unity": ["player_controller", "game_manager", "state_machine"],
            "unreal": ["actor_base", "character_base"],
            "godot": ["player_controller", "game_manager", "state_machine"]
        }
    
    def batch_generate(
        self,
        configs: List[Dict[str, Any]]
    ) -> List[GenerationResult]:
        """Generate multiple files at once"""
        results = []
        for config in configs:
            result = self.generate(**config)
            results.append(result)
        return results


# Convenience functions for quick generation
def generate_unity_controller(
    class_name: str,
    namespace: str = "MyGame",
    output_path: Optional[str] = None
) -> GenerationResult:
    """Quick generate Unity player controller"""
    gen = GameCodeGenerator()
    return gen.generate_player_controller(
        engine=EngineType.UNITY,
        class_name=class_name,
        namespace=namespace,
        output_path=output_path
    )


def generate_unreal_character(
    class_name: str,
    api_macro: str = "MYGAME",
    output_path: Optional[str] = None
) -> GenerationResult:
    """Quick generate Unreal character"""
    gen = GameCodeGenerator()
    return gen.generate(
        engine=EngineType.UNREAL,
        template=TemplateType.CHARACTER_BASE,
        class_name=class_name,
        namespace=api_macro,
        output_path=output_path
    )


def generate_godot_controller(
    class_name: str,
    output_path: Optional[str] = None
) -> GenerationResult:
    """Quick generate Godot player controller"""
    gen = GameCodeGenerator()
    return gen.generate_player_controller(
        engine=EngineType.GODOT,
        class_name=class_name,
        output_path=output_path
    )


if __name__ == "__main__":
    # Example usage
    gen = GameCodeGenerator()
    
    # Generate Unity PlayerController
    result = gen.generate_player_controller(
        engine=EngineType.UNITY,
        class_name="HeroController",
        namespace="AdventureGame",
        output_path="./output/HeroController.cs"
    )
    
    if result.success:
        print(f"Generated: {result.file_path}")
    else:
        print(f"Error: {result.error}")
