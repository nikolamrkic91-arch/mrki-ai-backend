"""
Mrki Visual Engine
==================
Visual-to-Code and Video-to-Code engine for UI generation.

This package provides tools for:
- Image/video analysis using vision models
- Sketch-to-code conversion with edge detection
- Framework-specific code generation (React, Vue, Angular, Svelte)
- Visual debugging with screenshot comparison
- Design system extraction from images

Usage:
    from visual_engine import ImageAnalyzer, CodeGenerator
    
    analyzer = ImageAnalyzer()
    result = analyzer.analyze_image("screenshot.png")
    
    generator = CodeGenerator()
    code = generator.generate_from_analysis(result.to_dict())
"""

__version__ = "1.0.0"
__author__ = "Mrki Team"

# Import main classes for easy access
from .analyzer import (
    ImageAnalyzer,
    VideoAnalyzer,
    ElementDetector,
    ColorExtractor,
    LayoutAnalyzer,
    TextDetector,
    UIElement,
    UIElementType,
    BoundingBox,
    ColorInfo,
    AnalysisResult,
    LayoutType,
    encode_image_to_base64,
    decode_base64_to_image
)

from .sketch_processor import (
    SketchAnalyzer,
    SketchPreprocessor,
    EdgeDetector,
    ShapeRecognizer,
    WireframeConverter,
    SketchShape,
    SketchElement,
    SketchAnalysis,
    ShapeType,
    SketchStyle
)

from .code_generator import (
    CodeGenerator,
    ReactGenerator,
    VueGenerator,
    AngularGenerator,
    SvelteGenerator,
    StyleGenerator,
    GeneratedCode,
    ComponentSpec,
    Framework,
    StyleSystem
)

from .visual_debugger import (
    VisualDebugger,
    ImageComparator,
    ElementComparator,
    RegressionDetector,
    ComparisonResult,
    Discrepancy,
    ElementMatch,
    DiscrepancyType,
    Severity
)

from .design_extractor import (
    DesignExtractor,
    ColorExtractor as DesignColorExtractor,
    TypographyExtractor,
    SpacingExtractor,
    ComponentExtractor,
    FigmaImporter,
    SketchImporter,
    DesignSystem,
    ColorToken,
    TypographyToken,
    SpacingToken,
    ShadowToken,
    ComponentPattern
)

from .config import Config, config

# Define what gets imported with "from visual_engine import *"
__all__ = [
    # Version
    "__version__",
    
    # Analyzer
    "ImageAnalyzer",
    "VideoAnalyzer",
    "ElementDetector",
    "ColorExtractor",
    "LayoutAnalyzer",
    "TextDetector",
    "UIElement",
    "UIElementType",
    "BoundingBox",
    "ColorInfo",
    "AnalysisResult",
    "LayoutType",
    "encode_image_to_base64",
    "decode_base64_to_image",
    
    # Sketch Processor
    "SketchAnalyzer",
    "SketchPreprocessor",
    "EdgeDetector",
    "ShapeRecognizer",
    "WireframeConverter",
    "SketchShape",
    "SketchElement",
    "SketchAnalysis",
    "ShapeType",
    "SketchStyle",
    
    # Code Generator
    "CodeGenerator",
    "ReactGenerator",
    "VueGenerator",
    "AngularGenerator",
    "SvelteGenerator",
    "StyleGenerator",
    "GeneratedCode",
    "ComponentSpec",
    "Framework",
    "StyleSystem",
    
    # Visual Debugger
    "VisualDebugger",
    "ImageComparator",
    "ElementComparator",
    "RegressionDetector",
    "ComparisonResult",
    "Discrepancy",
    "ElementMatch",
    "DiscrepancyType",
    "Severity",
    
    # Design Extractor
    "DesignExtractor",
    "DesignColorExtractor",
    "TypographyExtractor",
    "SpacingExtractor",
    "ComponentExtractor",
    "FigmaImporter",
    "SketchImporter",
    "DesignSystem",
    "ColorToken",
    "TypographyToken",
    "SpacingToken",
    "ShadowToken",
    "ComponentPattern",
    
    # Config
    "Config",
    "config"
]
