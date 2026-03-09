#!/usr/bin/env python3
"""
Mrki API - Unified FastAPI Application
======================================

This module combines all sub-APIs from different Mrki modules into a single
unified FastAPI application with proper routing, middleware, and error handling.

Sub-APIs included:
- Core: Agent orchestration endpoints
- Visual Engine: Visual-to-code processing
- Dev Environment: Full-stack development tools
- MoE: Mixture-of-Experts routing
- Game Development: Game code generation
"""

from __future__ import annotations

import os
import time
import traceback
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import structlog

from api.middleware import (
    AuthMiddleware,
    RateLimitMiddleware,
    create_access_token,
    hash_password,
    verify_password,
    verify_token,
    TokenResponse,
)

logger = structlog.get_logger("mrki.api")

# Create main router
router = APIRouter(prefix="/api/v1")


# =============================================================================
# Common Models
# =============================================================================

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: float
    version: str
    uptime: float
    modules: List[str]


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)


class APIInfo(BaseModel):
    """API information model."""
    name: str
    version: str
    description: str
    endpoints: List[Dict[str, str]]


# =============================================================================
# Request/Response Middleware
# =============================================================================

class RequestTimingMiddleware:
    """Middleware to track request timing."""
    
    async def __call__(self, request: Request, call_next: Callable) -> Any:
        start_time = time.time()
        
        # Log request
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else None,
        )
        
        response = await call_next(request)
        
        # Log response
        duration = time.time() - start_time
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )
        
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        return response


# =============================================================================
# Error Handlers
# =============================================================================

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(
        "http_exception",
        path=request.url.path,
        status_code=exc.status_code,
        detail=exc.detail,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            code=f"HTTP_{exc.status_code}",
        ).dict(),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        traceback=traceback.format_exc(),
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if False else None,  # Set to True for debug mode
            code="INTERNAL_ERROR",
        ).dict(),
    )


# =============================================================================
# Core API Routes
# =============================================================================

core_router = APIRouter(prefix="/core", tags=["Core"])


@core_router.get("/health")
async def core_health():
    """Core module health check."""
    try:
        from core.orchestrator import MrkiOrchestrator
        return {
            "status": "healthy",
            "module": "core",
            "orchestrator": "available",
        }
    except ImportError:
        return {
            "status": "unavailable",
            "module": "core",
            "reason": "module_not_installed",
        }


@core_router.post("/execute")
async def core_execute_task(request: Dict[str, Any]):
    """Execute a task through the orchestrator."""
    try:
        from core.orchestrator import MrkiOrchestrator, SubTask
        
        orchestrator = MrkiOrchestrator()
        await orchestrator.initialize()
        
        task = SubTask(
            name=request.get("name", "api_task"),
            description=request.get("description", ""),
            agent_type=request.get("agent_type", "default"),
            input_data=request.get("input", {}),
        )
        
        result = await orchestrator.execute_task(task)
        
        return {
            "success": result.status.value == "COMPLETED",
            "task_id": result.task_id,
            "status": result.status.value,
            "output": result.output,
            "execution_time_ms": result.execution_time_ms,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@core_router.get("/metrics")
async def core_metrics():
    """Get orchestrator metrics."""
    try:
        from core.orchestrator import MrkiOrchestrator
        
        orchestrator = MrkiOrchestrator()
        return {
            "module": "core",
            "max_concurrent_agents": orchestrator.config.max_concurrent_agents,
            "max_parallel_tool_calls": orchestrator.config.max_parallel_tool_calls,
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Core module not available")


# =============================================================================
# Visual Engine API Routes
# =============================================================================

visual_router = APIRouter(prefix="/visual", tags=["Visual Engine"])


@visual_router.get("/health")
async def visual_health():
    """Visual engine health check."""
    try:
        from visual_engine.analyzer import ImageAnalyzer
        return {
            "status": "healthy",
            "module": "visual_engine",
            "analyzer": "available",
        }
    except ImportError:
        return {
            "status": "unavailable",
            "module": "visual_engine",
            "reason": "module_not_installed",
        }


@visual_router.post("/analyze/image")
async def visual_analyze_image(request: Dict[str, Any]):
    """Analyze an image and extract UI elements."""
    try:
        from visual_engine.analyzer import ImageAnalyzer
        
        analyzer = ImageAnalyzer()
        # Implementation would process base64 image data
        return {
            "success": True,
            "module": "visual_engine",
            "message": "Image analysis endpoint - implement with actual image processing",
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Visual engine not available")


@visual_router.post("/generate/code")
async def visual_generate_code(request: Dict[str, Any]):
    """Generate code from visual analysis."""
    try:
        from visual_engine.code_generator import CodeGenerator, Framework, StyleSystem
        
        generator = CodeGenerator()
        
        # Map framework string to enum
        framework_map = {
            "react": Framework.REACT,
            "vue": Framework.VUE,
            "angular": Framework.ANGULAR,
            "svelte": Framework.SVELTE,
        }
        
        style_map = {
            "tailwind": StyleSystem.TAILWIND,
            "css_modules": StyleSystem.CSS_MODULES,
            "styled_components": StyleSystem.STYLED_COMPONENTS,
            "scss": StyleSystem.SCSS,
        }
        
        framework = framework_map.get(
            request.get("framework", "react").lower(),
            Framework.REACT
        )
        style_system = style_map.get(
            request.get("style_system", "tailwind").lower(),
            StyleSystem.TAILWIND
        )
        
        result = generator.generate_from_analysis(
            analysis=request.get("analysis", {}),
            framework=framework,
            style_system=style_system,
            component_name=request.get("component_name", "GeneratedComponent"),
        )
        
        return {
            "success": True,
            "framework": result.framework.value,
            "component_name": result.component_name,
            "template_code": result.template_code,
            "style_code": result.style_code,
            "test_code": result.test_code,
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Visual engine not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Dev Environment API Routes
# =============================================================================

dev_env_router = APIRouter(prefix="/dev", tags=["Development Environment"])


@dev_env_router.get("/health")
async def dev_env_health():
    """Dev environment health check."""
    try:
        from dev_env import ProjectScaffolder
        return {
            "status": "healthy",
            "module": "dev_env",
            "scaffolder": "available",
        }
    except ImportError:
        return {
            "status": "unavailable",
            "module": "dev_env",
            "reason": "module_not_installed",
        }


@dev_env_router.post("/scaffold")
async def dev_scaffold_project(request: Dict[str, Any]):
    """Scaffold a new project."""
    try:
        from dev_env.project_scaffolder import ProjectScaffolder
        
        scaffolder = ProjectScaffolder()
        
        project_type = request.get("project_type", "web")
        project_name = request.get("project_name", "my-project")
        output_dir = request.get("output_dir", "./")
        
        result = scaffolder.scaffold(
            project_type=project_type,
            project_name=project_name,
            output_dir=output_dir,
            options=request.get("options", {}),
        )
        
        return {
            "success": True,
            "project_name": project_name,
            "project_type": project_type,
            "output_path": result.get("path"),
            "files_created": result.get("files", []),
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Dev environment not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@dev_env_router.post("/generate/api")
async def dev_generate_api(request: Dict[str, Any]):
    """Generate API endpoints."""
    try:
        from dev_env.api_builder import APIBuilder
        
        builder = APIBuilder()
        
        result = builder.generate_api(
            name=request.get("name", "API"),
            endpoints=request.get("endpoints", []),
            framework=request.get("framework", "fastapi"),
            output_dir=request.get("output_dir", "./api"),
        )
        
        return {
            "success": True,
            "api_name": request.get("name"),
            "files_generated": result.get("files", []),
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Dev environment not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MoE API Routes
# =============================================================================

moe_router = APIRouter(prefix="/moe", tags=["Mixture of Experts"])


@moe_router.get("/health")
async def moe_health():
    """MoE module health check."""
    try:
        from moe.router import create_router
        return {
            "status": "healthy",
            "module": "moe",
            "router": "available",
        }
    except ImportError:
        return {
            "status": "unavailable",
            "module": "moe",
            "reason": "module_not_installed",
        }


@moe_router.get("/experts")
async def moe_list_experts():
    """List available experts."""
    try:
        from moe.expert_manager import ExpertManager
        
        manager = ExpertManager()
        experts = manager.list_experts()
        
        return {
            "success": True,
            "experts": experts,
            "count": len(experts),
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="MoE module not available")


@moe_router.post("/route")
async def moe_route(request: Dict[str, Any]):
    """Route input to appropriate experts."""
    try:
        import torch
        from moe.router import create_router
        
        router = create_router(
            input_dim=request.get("input_dim", 768),
            num_experts=request.get("num_experts", 64),
        )
        
        # Create dummy input for demonstration
        batch_size = request.get("batch_size", 1)
        seq_len = request.get("seq_len", 128)
        input_dim = request.get("input_dim", 768)
        
        inputs = torch.randn(batch_size, seq_len, input_dim)
        decision = router.route(inputs, training=False)
        
        return {
            "success": True,
            "expert_indices": decision.expert_indices,
            "routing_time_ms": decision.routing_time_ms,
            "capacity_usage": decision.capacity_usage,
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="MoE module not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@moe_router.get("/statistics")
async def moe_statistics():
    """Get MoE routing statistics."""
    try:
        from moe.router import create_router
        
        router = create_router(input_dim=768, num_experts=64)
        stats = router.get_expert_statistics()
        
        return {
            "success": True,
            "statistics": stats,
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="MoE module not available")


# =============================================================================
# Game Development API Routes
# =============================================================================

gamedev_router = APIRouter(prefix="/gamedev", tags=["Game Development"])


@gamedev_router.get("/health")
async def gamedev_health():
    """Game development module health check."""
    try:
        from gamedev.code_gen.generator import GameCodeGenerator
        return {
            "status": "healthy",
            "module": "gamedev",
            "generator": "available",
        }
    except ImportError:
        return {
            "status": "unavailable",
            "module": "gamedev",
            "reason": "module_not_installed",
        }


@gamedev_router.get("/engines")
async def gamedev_list_engines():
    """List supported game engines."""
    return {
        "success": True,
        "engines": [
            {"name": "unity", "language": "C#", "templates": ["player_controller", "game_manager", "state_machine"]},
            {"name": "unreal", "language": "C++", "templates": ["actor_base", "character_base"]},
            {"name": "godot", "language": "GDScript", "templates": ["player_controller", "game_manager", "state_machine"]},
        ],
    }


@gamedev_router.post("/generate")
async def gamedev_generate(request: Dict[str, Any]):
    """Generate game code."""
    try:
        from gamedev.code_gen.generator import (
            GameCodeGenerator,
            EngineType,
            TemplateType,
        )
        
        generator = GameCodeGenerator()
        
        # Map engine string to enum
        engine_map = {
            "unity": EngineType.UNITY,
            "unreal": EngineType.UNREAL,
            "godot": EngineType.GODOT,
        }
        
        # Map template string to enum
        template_map = {
            "player_controller": TemplateType.PLAYER_CONTROLLER,
            "game_manager": TemplateType.GAME_MANAGER,
            "state_machine": TemplateType.STATE_MACHINE,
            "actor_base": TemplateType.ACTOR_BASE,
            "character_base": TemplateType.CHARACTER_BASE,
        }
        
        engine = engine_map.get(request.get("engine", "unity").lower())
        template = template_map.get(request.get("template", "player_controller").lower())
        
        if not engine or not template:
            raise HTTPException(status_code=400, detail="Invalid engine or template")
        
        result = generator.generate(
            engine=engine,
            template=template,
            class_name=request.get("class_name", "MyClass"),
            namespace=request.get("namespace", "MyGame"),
            description=request.get("description", ""),
            extra_vars=request.get("extra_vars"),
        )
        
        return {
            "success": result.success,
            "code": result.code,
            "file_path": result.file_path,
            "error": result.error,
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Game development module not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Auth API Routes
# =============================================================================

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# Simple in-memory user store (replace with database in production)
_users_store: Dict[str, Dict[str, str]] = {}


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "user"


@auth_router.post("/register")
async def auth_register(request: RegisterRequest):
    """Register a new user."""
    if request.username in _users_store:
        raise HTTPException(status_code=400, detail="Username already exists")

    _users_store[request.username] = {
        "password_hash": hash_password(request.password),
        "role": request.role,
    }

    return {"success": True, "message": f"User '{request.username}' registered"}


@auth_router.post("/login", response_model=TokenResponse)
async def auth_login(request: LoginRequest):
    """Login and receive a JWT token."""
    user = _users_store.get(request.username)
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(subject=request.username, role=user["role"])
    return TokenResponse(
        access_token=token,
        expires_in=int(os.getenv("MRKI_JWT_EXPIRATION", "3600")),
    )


@auth_router.get("/me")
async def auth_me(request: Request):
    """Get current user info."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"user": user}


# =============================================================================
# Main Router Assembly
# =============================================================================

# Include all sub-routers
router.include_router(auth_router)
router.include_router(core_router)
router.include_router(visual_router)
router.include_router(dev_env_router)
router.include_router(moe_router)
router.include_router(gamedev_router)


# =============================================================================
# Main API Endpoints
# =============================================================================

@router.get("/", response_model=APIInfo)
async def api_info():
    """Get API information."""
    return APIInfo(
        name="Mrki API",
        version="1.0.0",
        description="Unified API for the Mrki platform",
        endpoints=[
            {"path": "/core", "description": "Agent orchestration"},
            {"path": "/visual", "description": "Visual-to-code processing"},
            {"path": "/dev", "description": "Development environment"},
            {"path": "/moe", "description": "Mixture-of-Experts routing"},
            {"path": "/gamedev", "description": "Game development"},
        ],
    )


@router.get("/health", response_model=HealthResponse)
async def api_health(request: Request):
    """Get API health status."""
    start_time = request.app.state.start_time if hasattr(request.app.state, 'start_time') else time.time()
    uptime = time.time() - start_time
    
    # Check module availability
    modules = []
    
    try:
        from core.orchestrator import MrkiOrchestrator
        modules.append("core")
    except ImportError:
        pass
    
    try:
        from visual_engine.analyzer import ImageAnalyzer
        modules.append("visual_engine")
    except ImportError:
        pass
    
    try:
        from dev_env import ProjectScaffolder
        modules.append("dev_env")
    except ImportError:
        pass
    
    try:
        from moe.router import create_router
        modules.append("moe")
    except ImportError:
        pass
    
    try:
        from gamedev.code_gen.generator import GameCodeGenerator
        modules.append("gamedev")
    except ImportError:
        pass
    
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        version="1.0.0",
        uptime=uptime,
        modules=modules,
    )


# =============================================================================
# Application Factory
# =============================================================================

def create_unified_app() -> FastAPI:
    """Create the unified FastAPI application."""
    app = FastAPI(
        title="Mrki Unified API",
        description="Combined API for all Mrki modules",
        version="1.0.0",
    )

    # Add middleware (order matters - last added runs first)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("MRKI_CORS_ORIGINS", "*").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting
    rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    rate_limiter = RateLimitMiddleware(rate_limit_requests, rate_limit_window)
    app.middleware("http")(rate_limiter)

    # Authentication
    auth_middleware = AuthMiddleware()
    app.middleware("http")(auth_middleware)

    # Add exception handlers
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Include main router
    app.include_router(router)

    # Store start time
    app.state.start_time = time.time()

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": "Mrki Unified API",
            "version": "1.0.0",
            "documentation": "/docs",
            "health": "/api/v1/health",
        }

    return app


# =============================================================================
# Standalone Server
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    app = create_unified_app()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
