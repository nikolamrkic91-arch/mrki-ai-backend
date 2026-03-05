#!/usr/bin/env python3
"""
Mrki Game Development API
FastAPI endpoints for game code generation.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

from code_gen.generator import (
    GameCodeGenerator,
    EngineType,
    TemplateType,
    GenerationResult
)

# Initialize FastAPI app
app = FastAPI(
    title="Mrki Game Development API",
    description="API for generating game code across Unity, Unreal Engine, and Godot",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Enums for API
class EngineEnum(str, Enum):
    UNITY = "unity"
    UNREAL = "unreal"
    GODOT = "godot"


class TemplateEnum(str, Enum):
    PLAYER_CONTROLLER = "player_controller"
    GAME_MANAGER = "game_manager"
    STATE_MACHINE = "state_machine"
    ACTOR_BASE = "actor_base"
    CHARACTER_BASE = "character_base"


# Request/Response Models
class GenerateRequest(BaseModel):
    engine: EngineEnum = Field(..., description="Target game engine")
    template: TemplateEnum = Field(..., description="Template type to use")
    class_name: str = Field(..., min_length=1, description="Name of the generated class")
    namespace: str = Field(default="MyGame", description="Namespace/module name")
    description: str = Field(default="", description="Class description")
    extra_vars: Optional[Dict[str, Any]] = Field(default=None, description="Additional template variables")


class GenerateResponse(BaseModel):
    success: bool
    code: str
    file_path: Optional[str] = None
    error: Optional[str] = None


class TemplateInfo(BaseModel):
    name: str
    description: str
    available_engines: List[str]


class EngineInfo(BaseModel):
    name: str
    templates: List[str]


# Initialize generator
generator = GameCodeGenerator()


# API Endpoints
@app.get("/")
async def root():
    """API root - health check"""
    return {
        "name": "Mrki Game Development API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/engines", response_model=Dict[str, List[str]])
async def list_engines():
    """List all supported game engines and their templates"""
    return {
        "unity": ["player_controller", "game_manager", "state_machine"],
        "unreal": ["actor_base", "character_base"],
        "godot": ["player_controller", "game_manager", "state_machine"]
    }


@app.get("/templates/{engine}", response_model=List[str])
async def list_templates(engine: EngineEnum):
    """List available templates for a specific engine"""
    templates = {
        EngineEnum.UNITY: ["player_controller", "game_manager", "state_machine"],
        EngineEnum.UNREAL: ["actor_base", "character_base"],
        EngineEnum.GODOT: ["player_controller", "game_manager", "state_machine"]
    }
    return templates.get(engine, [])


@app.post("/generate", response_model=GenerateResponse)
async def generate_code(request: GenerateRequest):
    """
    Generate game code from a template.
    
    Example request:
    ```json
    {
        "engine": "unity",
        "template": "player_controller",
        "class_name": "HeroController",
        "namespace": "AdventureGame",
        "description": "Main hero controller"
    }
    ```
    """
    try:
        # Map enums to internal types
        engine_map = {
            EngineEnum.UNITY: EngineType.UNITY,
            EngineEnum.UNREAL: EngineType.UNREAL,
            EngineEnum.GODOT: EngineType.GODOT
        }
        
        template_map = {
            TemplateEnum.PLAYER_CONTROLLER: TemplateType.PLAYER_CONTROLLER,
            TemplateEnum.GAME_MANAGER: TemplateType.GAME_MANAGER,
            TemplateEnum.STATE_MACHINE: TemplateType.STATE_MACHINE,
            TemplateEnum.ACTOR_BASE: TemplateType.ACTOR_BASE,
            TemplateEnum.CHARACTER_BASE: TemplateType.CHARACTER_BASE
        }
        
        # Generate code
        result = generator.generate(
            engine=engine_map[request.engine],
            template=template_map[request.template],
            class_name=request.class_name,
            namespace=request.namespace,
            description=request.description,
            extra_vars=request.extra_vars
        )
        
        return GenerateResponse(
            success=result.success,
            code=result.code,
            file_path=result.file_path,
            error=result.error
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/player-controller", response_model=GenerateResponse)
async def generate_player_controller(
    engine: EngineEnum,
    class_name: str,
    namespace: str = "MyGame",
    description: str = ""
):
    """Quick endpoint to generate a player controller"""
    engine_map = {
        EngineEnum.UNITY: EngineType.UNITY,
        EngineEnum.UNREAL: EngineType.UNREAL,
        EngineEnum.GODOT: EngineType.GODOT
    }
    
    result = generator.generate_player_controller(
        engine=engine_map[engine],
        class_name=class_name,
        namespace=namespace,
        description=description
    )
    
    return GenerateResponse(
        success=result.success,
        code=result.code,
        file_path=result.file_path,
        error=result.error
    )


@app.post("/generate/game-manager", response_model=GenerateResponse)
async def generate_game_manager(
    engine: EngineEnum,
    class_name: str,
    namespace: str = "MyGame",
    description: str = ""
):
    """Quick endpoint to generate a game manager"""
    engine_map = {
        EngineEnum.UNITY: EngineType.UNITY,
        EngineEnum.UNREAL: EngineType.UNREAL,
        EngineEnum.GODOT: EngineType.GODOT
    }
    
    result = generator.generate_game_manager(
        engine=engine_map[engine],
        class_name=class_name,
        namespace=namespace,
        description=description
    )
    
    return GenerateResponse(
        success=result.success,
        code=result.code,
        file_path=result.file_path,
        error=result.error
    )


@app.post("/batch-generate", response_model=List[GenerateResponse])
async def batch_generate(requests: List[GenerateRequest]):
    """Generate multiple code files in one request"""
    results = []
    
    engine_map = {
        EngineEnum.UNITY: EngineType.UNITY,
        EngineEnum.UNREAL: EngineType.UNREAL,
        EngineEnum.GODOT: EngineType.GODOT
    }
    
    template_map = {
        TemplateEnum.PLAYER_CONTROLLER: TemplateType.PLAYER_CONTROLLER,
        TemplateEnum.GAME_MANAGER: TemplateType.GAME_MANAGER,
        TemplateEnum.STATE_MACHINE: TemplateType.STATE_MACHINE,
        TemplateEnum.ACTOR_BASE: TemplateType.ACTOR_BASE,
        TemplateEnum.CHARACTER_BASE: TemplateType.CHARACTER_BASE
    }
    
    for req in requests:
        try:
            result = generator.generate(
                engine=engine_map[req.engine],
                template=template_map[req.template],
                class_name=req.class_name,
                namespace=req.namespace,
                description=req.description,
                extra_vars=req.extra_vars
            )
            
            results.append(GenerateResponse(
                success=result.success,
                code=result.code,
                file_path=result.file_path,
                error=result.error
            ))
        except Exception as e:
            results.append(GenerateResponse(
                success=False,
                code="",
                error=str(e)
            ))
    
    return results


# Template preview endpoint
@app.get("/preview/{engine}/{template}")
async def preview_template(engine: EngineEnum, template: TemplateEnum):
    """Preview a template with default values"""
    engine_map = {
        EngineEnum.UNITY: EngineType.UNITY,
        EngineEnum.UNREAL: EngineType.UNREAL,
        EngineEnum.GODOT: EngineType.GODOT
    }
    
    template_map = {
        TemplateEnum.PLAYER_CONTROLLER: TemplateType.PLAYER_CONTROLLER,
        TemplateEnum.GAME_MANAGER: TemplateType.GAME_MANAGER,
        TemplateEnum.STATE_MACHINE: TemplateType.STATE_MACHINE,
        TemplateEnum.ACTOR_BASE: TemplateType.ACTOR_BASE,
        TemplateEnum.CHARACTER_BASE: TemplateType.CHARACTER_BASE
    }
    
    result = generator.generate(
        engine=engine_map[engine],
        template=template_map[template],
        class_name="ExampleClass",
        namespace="MyGame",
        description="Example generated class"
    )
    
    if result.success:
        return {
            "template": template.value,
            "engine": engine.value,
            "preview": result.code
        }
    else:
        raise HTTPException(status_code=500, detail=result.error)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
