"""
Mrki Visual Engine - Configuration
===================================
Configuration settings for the visual engine.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AnalyzerConfig:
    """Configuration for image/video analyzer."""
    vision_model: str = "default"
    min_element_size: int = 20
    confidence_threshold: float = 0.5
    edge_detection_low: int = 50
    edge_detection_high: int = 150
    
    
@dataclass
class SketchConfig:
    """Configuration for sketch processor."""
    min_line_thickness: int = 2
    max_line_thickness: int = 10
    rectangle_threshold: float = 0.1
    circle_threshold: float = 0.15
    position_tolerance: int = 5
    size_tolerance: float = 0.1


@dataclass
class CodeGenConfig:
    """Configuration for code generator."""
    default_framework: str = "react"
    default_style_system: str = "tailwind"
    templates_dir: Optional[str] = None
    indent_size: int = 2
    use_semantic_names: bool = True


@dataclass
class DebuggerConfig:
    """Configuration for visual debugger."""
    similarity_threshold: float = 0.95
    pixel_diff_threshold: float = 1.0
    position_tolerance: int = 5
    size_tolerance: float = 0.1
    color_tolerance: int = 30


@dataclass
class DesignConfig:
    """Configuration for design extractor."""
    num_colors: int = 10
    min_color_frequency: float = 0.01
    base_spacing_unit: int = 4
    font_size_tolerance: int = 2


@dataclass
class APIConfig:
    """Configuration for API server."""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    log_level: str = "info"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: list = field(default_factory=lambda: [
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp",
        ".mp4", ".avi", ".mov", ".mkv"
    ])


class Config:
    """Main configuration class."""
    
    def __init__(self):
        self.analyzer = AnalyzerConfig()
        self.sketch = SketchConfig()
        self.codegen = CodeGenConfig()
        self.debugger = DebuggerConfig()
        self.design = DesignConfig()
        self.api = APIConfig()
        
        # Load from environment variables
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Analyzer config
        self.analyzer.vision_model = os.getenv("MRKI_VISION_MODEL", self.analyzer.vision_model)
        
        # CodeGen config
        self.codegen.default_framework = os.getenv("MRKI_DEFAULT_FRAMEWORK", self.codegen.default_framework)
        self.codegen.default_style_system = os.getenv("MRKI_DEFAULT_STYLE_SYSTEM", self.codegen.default_style_system)
        
        # API config
        self.api.host = os.getenv("MRKI_API_HOST", self.api.host)
        self.api.port = int(os.getenv("MRKI_API_PORT", self.api.port))
        self.api.log_level = os.getenv("MRKI_LOG_LEVEL", self.api.log_level)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "analyzer": self.analyzer.__dict__,
            "sketch": self.sketch.__dict__,
            "codegen": self.codegen.__dict__,
            "debugger": self.debugger.__dict__,
            "design": self.design.__dict__,
            "api": self.api.__dict__
        }


# Global config instance
config = Config()
