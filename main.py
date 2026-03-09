#!/usr/bin/env python3
"""
Mrki - Main Application Entry Point
====================================

This is the main entry point for the Mrki platform. It initializes all modules,
sets up logging and configuration, starts the API server, and handles graceful
shutdown.

Usage:
    python main.py                    # Start with default config
    python main.py --config config.yaml
    python main.py --host 0.0.0.0 --port 8080
    python main.py --debug            # Enable debug mode

Environment Variables:
    MRKI_CONFIG_PATH: Path to configuration file
    MRKI_LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
    MRKI_DATABASE_URL: Database connection URL
    MRKI_REDIS_URL: Redis connection URL
    MRKI_SECRET_KEY: Secret key for security
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
import yaml
from pydantic import BaseModel, Field

# Configure structured logging before any other imports
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger("mrki.main")


# =============================================================================
# Configuration Models
# =============================================================================

class ServerConfig(BaseModel):
    """Server configuration."""
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    workers: int = 4
    timeout: int = 30
    max_body_size: str = "10MB"


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = "sqlite:///~/.config/mrki/mrki.db"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True


class SecurityConfig(BaseModel):
    """Security configuration."""
    secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600
    refresh_expiration: int = 604800
    api_key_header: str = "X-API-Key"


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "json"
    file: Optional[str] = None
    max_size: str = "10MB"
    max_files: int = 5


class ModuleConfig(BaseModel):
    """Module-specific configuration."""
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


class MrkiConfig(BaseModel):
    """Main Mrki configuration."""
    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    modules: Dict[str, ModuleConfig] = Field(default_factory=dict)


# =============================================================================
# Module Registry
# =============================================================================

class ModuleRegistry:
    """Registry for managing Mrki modules."""
    
    def __init__(self):
        self.modules: Dict[str, Any] = {}
        self.initialized: Dict[str, bool] = {}
        self._logger = structlog.get_logger("mrki.registry")
    
    def register(self, name: str, module: Any) -> None:
        """Register a module."""
        self.modules[name] = module
        self.initialized[name] = False
        self._logger.info("module_registered", name=name)
    
    def get(self, name: str) -> Optional[Any]:
        """Get a registered module."""
        return self.modules.get(name)
    
    async def initialize_all(self, config: MrkiConfig) -> None:
        """Initialize all registered modules."""
        self._logger.info("initializing_modules", count=len(self.modules))
        
        for name, module in self.modules.items():
            module_config = config.modules.get(name, ModuleConfig())
            
            if not module_config.enabled:
                self._logger.info("module_skipped", name=name, reason="disabled")
                continue
            
            try:
                if hasattr(module, 'initialize'):
                    await module.initialize(module_config.config)
                self.initialized[name] = True
                self._logger.info("module_initialized", name=name)
            except Exception as e:
                self._logger.error("module_init_failed", name=name, error=str(e))
                raise
    
    async def shutdown_all(self) -> None:
        """Shutdown all initialized modules."""
        self._logger.info("shutting_down_modules")
        
        for name, module in self.modules.items():
            if not self.initialized.get(name, False):
                continue
            
            try:
                if hasattr(module, 'shutdown'):
                    await module.shutdown()
                self.initialized[name] = False
                self._logger.info("module_shutdown", name=name)
            except Exception as e:
                self._logger.error("module_shutdown_failed", name=name, error=str(e))


# Global module registry
module_registry = ModuleRegistry()


# =============================================================================
# Module Imports and Registration
# =============================================================================

def import_and_register_modules() -> None:
    """Import and register all Mrki modules."""
    _logger = structlog.get_logger("mrki.modules")
    
    # Core Orchestrator
    try:
        from core.orchestrator import MrkiOrchestrator, OrchestratorConfig
        orchestrator = MrkiOrchestrator()
        module_registry.register("core", orchestrator)
        _logger.info("core_module_loaded")
    except ImportError as e:
        _logger.warning("core_module_not_available", error=str(e))
    
    # Visual Engine
    try:
        from visual_engine.analyzer import ImageAnalyzer, VideoAnalyzer
        from visual_engine.code_generator import CodeGenerator
        visual_engine = {
            "image_analyzer": ImageAnalyzer(),
            "video_analyzer": VideoAnalyzer(),
            "code_generator": CodeGenerator(),
        }
        module_registry.register("visual_engine", visual_engine)
        _logger.info("visual_engine_module_loaded")
    except ImportError as e:
        _logger.warning("visual_engine_module_not_available", error=str(e))
    
    # Development Environment
    try:
        from dev_env import (
            ProjectScaffolder,
            GitOps,
            CodeGenerator as DevCodeGenerator,
            DatabaseManager,
            APIBuilder,
            DockerManager,
            TestManager,
        )
        dev_env = {
            "scaffolder": ProjectScaffolder(),
            "git_ops": GitOps(),
            "code_generator": DevCodeGenerator(),
            "database": DatabaseManager(),
            "api_builder": APIBuilder(),
            "docker": DockerManager(),
            "testing": TestManager(),
        }
        module_registry.register("dev_env", dev_env)
        _logger.info("dev_env_module_loaded")
    except ImportError as e:
        _logger.warning("dev_env_module_not_available", error=str(e))
    
    # MoE (Mixture of Experts)
    try:
        from moe.router import create_router, RoutingConfig
        from moe.expert_manager import ExpertManager
        moe = {
            "router": create_router(input_dim=768, num_experts=64),
            "expert_manager": ExpertManager(),
        }
        module_registry.register("moe", moe)
        _logger.info("moe_module_loaded")
    except ImportError as e:
        _logger.warning("moe_module_not_available", error=str(e))
    
    # Game Development
    try:
        from gamedev.code_gen.generator import GameCodeGenerator
        gamedev = {
            "code_generator": GameCodeGenerator(),
        }
        module_registry.register("gamedev", gamedev)
        _logger.info("gamedev_module_loaded")
    except ImportError as e:
        _logger.warning("gamedev_module_not_available", error=str(e))
    
    # IDE Integration
    try:
        from ide_integration.file_watcher import FileWatcher
        ide_integration = {
            "file_watcher": FileWatcher(),
        }
        module_registry.register("ide_integration", ide_integration)
        _logger.info("ide_integration_module_loaded")
    except ImportError as e:
        _logger.warning("ide_integration_module_not_available", error=str(e))
    
    _logger.info("module_registration_complete", 
                registered=len(module_registry.modules))


# =============================================================================
# Configuration Loading
# =============================================================================

def load_config(config_path: Optional[str] = None) -> MrkiConfig:
    """Load configuration from file or environment."""
    # Check environment variable first
    if config_path is None:
        config_path = os.getenv("MRKI_CONFIG_PATH")
    
    config_data = {}
    
    if config_path and Path(config_path).exists():
        logger.info("loading_config", path=config_path)
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
    else:
        logger.info("using_default_config")
    
    # Override with environment variables
    if os.getenv("MRKI_LOG_LEVEL"):
        if "logging" not in config_data:
            config_data["logging"] = {}
        config_data["logging"]["level"] = os.getenv("MRKI_LOG_LEVEL")
    
    if os.getenv("MRKI_DATABASE_URL"):
        if "database" not in config_data:
            config_data["database"] = {}
        config_data["database"]["url"] = os.getenv("MRKI_DATABASE_URL")
    
    if os.getenv("MRKI_SECRET_KEY"):
        if "security" not in config_data:
            config_data["security"] = {}
        config_data["security"]["secret_key"] = os.getenv("MRKI_SECRET_KEY")
    
    return MrkiConfig(**config_data)


def setup_logging(config: LoggingConfig) -> None:
    """Setup logging configuration."""
    level = getattr(logging, config.level.upper(), logging.INFO)
    
    # Configure standard library logging
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # Configure structlog
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level),
    )
    
    logger.info("logging_configured", level=config.level, format=config.format)


# =============================================================================
# Signal Handling
# =============================================================================

_shutdown_event = asyncio.Event()


def setup_signal_handlers() -> None:
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(sig: int, frame: Any) -> None:
        logger.info("shutdown_signal_received", signal=sig)
        _shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("signal_handlers_configured")


# =============================================================================
# API Server Lifecycle
# =============================================================================

@asynccontextmanager
async def lifespan(app):
    """Lifespan context manager for FastAPI app."""
    # Startup
    logger.info("application_startup")
    
    # Load configuration
    config = app.state.config
    
    # Setup logging
    setup_logging(config.logging)
    
    # Import and register modules
    import_and_register_modules()
    
    # Initialize all modules
    await module_registry.initialize_all(config)
    
    logger.info("application_startup_complete")
    
    yield
    
    # Shutdown
    logger.info("application_shutdown")
    await module_registry.shutdown_all()
    logger.info("application_shutdown_complete")


def create_app(config: Optional[MrkiConfig] = None) -> Any:
    """Create and configure the FastAPI application."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    if config is None:
        config = load_config()

    app = FastAPI(
        title="Mrki API",
        description="Unified API for the Mrki platform",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Store config in app state
    app.state.config = config

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Import and include routers from sub-APIs
    try:
        from api.main import router as api_router
        app.include_router(api_router, prefix="/api/v1")
        logger.info("api_router_included")
    except ImportError as e:
        logger.warning("api_router_not_available", error=str(e))

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "modules": list(module_registry.modules.keys()),
        }

    # Serve frontend static files if the build exists
    frontend_dist = Path(__file__).parent / "frontend" / "dist"
    if frontend_dist.exists():
        # Serve static assets (JS, CSS, etc.)
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="static")

        # Serve index.html for all non-API routes (SPA catch-all)
        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            """Serve the frontend SPA for any non-API route."""
            file_path = frontend_dist / full_path
            if file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(str(frontend_dist / "index.html"))

        logger.info("frontend_serving_enabled", path=str(frontend_dist))
    else:
        # No frontend build - serve API info at root
        @app.get("/")
        async def root():
            """Root endpoint with API information."""
            return {
                "name": "Mrki API",
                "version": "1.0.0",
                "description": "Unified API for the Mrki platform",
                "documentation": "/docs",
                "health": "/health",
                "modules": list(module_registry.modules.keys()),
            }

        logger.info("frontend_not_found", path=str(frontend_dist))

    return app


# =============================================================================
# Main Entry Point
# =============================================================================

async def run_server(config: MrkiConfig) -> None:
    """Run the API server."""
    import uvicorn
    
    app = create_app(config)
    
    setup_signal_handlers()
    
    config_kwargs = {
        "host": config.server.host,
        "port": config.server.port,
        "log_level": config.logging.level.lower(),
    }
    
    if not config.server.debug:
        config_kwargs["workers"] = config.server.workers
    
    logger.info(
        "starting_server",
        host=config.server.host,
        port=config.server.port,
        debug=config.server.debug,
    )
    
    # Run server with graceful shutdown
    server = uvicorn.Server(uvicorn.Config(app, **config_kwargs))
    
    # Start server in background task
    server_task = asyncio.create_task(server.serve())
    
    # Wait for shutdown signal
    await _shutdown_event.wait()
    
    # Graceful shutdown
    logger.info("initiating_graceful_shutdown")
    server.should_exit = True
    await server_task
    
    logger.info("server_stopped")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Mrki - Workflow Automation Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py                    # Start with default config
    python main.py --config config.yaml
    python main.py --host 0.0.0.0 --port 8080
    python main.py --debug            # Enable debug mode
        """
    )
    
    parser.add_argument(
        "--config", "-c",
        help="Path to configuration file",
        default=None,
    )
    parser.add_argument(
        "--host", "-H",
        help="Host to bind to",
        default=None,
    )
    parser.add_argument(
        "--port", "-p",
        help="Port to listen on",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--debug", "-d",
        help="Enable debug mode",
        action="store_true",
    )
    parser.add_argument(
        "--log-level", "-l",
        help="Logging level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override with command line arguments
    if args.host:
        config.server.host = args.host
    if args.port:
        config.server.port = args.port
    if args.debug:
        config.server.debug = True
    if args.log_level:
        config.logging.level = args.log_level
    
    # Setup logging
    setup_logging(config.logging)
    
    # Print startup banner
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ███╗   ███╗██████╗ ██╗  ██╗██╗                            ║
║   ████╗ ████║██╔══██╗██║ ██╔╝██║                            ║
║   ██╔████╔██║██████╔╝█████╔╝ ██║                            ║
║   ██║╚██╔╝██║██╔══██╗██╔═██╗ ██║                            ║
║   ██║ ╚═╝ ██║██║  ██║██║  ██╗██║                            ║
║   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝                            ║
║                                                              ║
║   Workflow Automation Platform v1.0.0                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    logger.info("mrki_starting", version="1.0.0")
    
    try:
        # Run the server
        asyncio.run(run_server(config))
        return 0
    except KeyboardInterrupt:
        logger.info("interrupted_by_user")
        return 0
    except Exception as e:
        logger.error("fatal_error", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
