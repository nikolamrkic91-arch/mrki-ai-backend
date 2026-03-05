"""
Mrki API Package
================

This package contains the unified API for the Mrki platform.

Usage:
    from api.main import create_unified_app, router
    
    app = create_unified_app()
    
    # Or use the router directly
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
"""

from api.main import (
    create_unified_app,
    router,
    core_router,
    visual_router,
    dev_env_router,
    moe_router,
    gamedev_router,
    HealthResponse,
    ErrorResponse,
    APIInfo,
)

__all__ = [
    "create_unified_app",
    "router",
    "core_router",
    "visual_router",
    "dev_env_router",
    "moe_router",
    "gamedev_router",
    "HealthResponse",
    "ErrorResponse",
    "APIInfo",
]
