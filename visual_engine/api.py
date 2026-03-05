"""
Mrki Visual Engine - FastAPI API
=================================
REST API endpoints for visual processing.
"""

import os
import io
import base64
import tempfile
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

import numpy as np
from PIL import Image
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
import uvicorn

# Import visual engine modules
from analyzer import ImageAnalyzer, VideoAnalyzer, AnalysisResult
from sketch_processor import SketchAnalyzer, WireframeConverter
from code_generator import CodeGenerator, Framework, StyleSystem, ComponentSpec
from visual_debugger import VisualDebugger, ImageComparator, RegressionDetector
from design_extractor import DesignExtractor, FigmaImporter, SketchImporter


# Initialize FastAPI app
app = FastAPI(
    title="Mrki Visual Engine API",
    description="Visual-to-Code and Video-to-Code engine for UI generation",
    version="1.0.0"
)

# Initialize processors
image_analyzer = ImageAnalyzer()
video_analyzer = VideoAnalyzer()
sketch_analyzer = SketchAnalyzer()
code_generator = CodeGenerator()
visual_debugger = VisualDebugger()
design_extractor = DesignExtractor()


# ============== Pydantic Models ==============

class AnalyzeImageRequest(BaseModel):
    """Request model for image analysis."""
    vision_model: Optional[str] = "default"
    extract_elements: bool = True
    extract_colors: bool = True
    extract_typography: bool = True


class AnalyzeImageResponse(BaseModel):
    """Response model for image analysis."""
    success: bool
    elements: List[Dict[str, Any]]
    colors: Dict[str, str]
    layout: str
    typography: Dict[str, Any]
    dimensions: List[int]
    processing_time: float


class GenerateCodeRequest(BaseModel):
    """Request model for code generation."""
    analysis: Dict[str, Any]
    framework: str = "react"
    style_system: str = "tailwind"
    component_name: str = "GeneratedComponent"


class GenerateCodeResponse(BaseModel):
    """Response model for code generation."""
    success: bool
    framework: str
    style_system: str
    component_name: str
    template_code: str
    style_code: str
    test_code: str


class SketchToCodeRequest(BaseModel):
    """Request model for sketch to code conversion."""
    framework: str = "react"
    style_system: str = "tailwind"
    straighten_lines: bool = True
    enhance_contrast: bool = True


class CompareImagesRequest(BaseModel):
    """Request model for image comparison."""
    similarity_threshold: float = 0.95
    mask_regions: Optional[List[List[int]]] = None


class CompareImagesResponse(BaseModel):
    """Response model for image comparison."""
    success: bool
    similarity_score: float
    pixel_diff_percentage: float
    discrepancies: List[Dict[str, Any]]
    has_issues: bool


class ExtractDesignSystemRequest(BaseModel):
    """Request model for design system extraction."""
    name: str = "Extracted Design System"
    num_colors: int = 10


class ExtractDesignSystemResponse(BaseModel):
    """Response model for design system extraction."""
    success: bool
    design_system: Dict[str, Any]
    tailwind_config: Dict[str, Any]
    css_variables: str


class VideoAnalysisRequest(BaseModel):
    """Request model for video analysis."""
    frame_interval: int = 30
    extract_keyframes: bool = True
    num_keyframes: int = 5


class VideoAnalysisResponse(BaseModel):
    """Response model for video analysis."""
    success: bool
    video_info: Dict[str, Any]
    frames_analyzed: int
    behaviors: List[Dict[str, Any]]
    keyframes: Optional[List[str]] = None  # Base64 encoded


# ============== Helper Functions ==============

def decode_base64_image(base64_string: str) -> np.ndarray:
    """Decode base64 string to numpy array."""
    image_data = base64.b64decode(base64_string)
    image = Image.open(io.BytesIO(image_data))
    return np.array(image)


def encode_image_to_base64(image: np.ndarray) -> str:
    """Encode numpy array to base64 string."""
    pil_image = Image.fromarray(image)
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def save_upload_file(upload_file: UploadFile) -> str:
    """Save uploaded file to temporary location."""
    suffix = Path(upload_file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(upload_file.file.read())
        return tmp.name


# ============== API Endpoints ==============

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Mrki Visual Engine API",
        "version": "1.0.0",
        "endpoints": [
            "/analyze/image",
            "/analyze/sketch",
            "/analyze/video",
            "/generate/code",
            "/generate/sketch-to-code",
            "/compare/images",
            "/extract/design-system",
            "/debug/screenshot"
        ]
    }


@app.post("/analyze/image", response_model=AnalyzeImageResponse)
async def analyze_image(
    file: UploadFile = File(...),
    vision_model: Optional[str] = Form("default"),
    extract_elements: bool = Form(True),
    extract_colors: bool = Form(True),
    extract_typography: bool = Form(True)
):
    """
    Analyze an image and extract UI elements, colors, and typography.
    
    - **file**: Image file to analyze
    - **vision_model**: Vision model to use (default, gpt4v, claude)
    - **extract_elements**: Whether to extract UI elements
    - **extract_colors**: Whether to extract color palette
    - **extract_typography**: Whether to extract typography
    """
    try:
        start_time = datetime.now()
        
        # Save uploaded file
        temp_path = save_upload_file(file)
        
        # Analyze image
        result = image_analyzer.analyze_image(temp_path)
        
        # Clean up
        os.unlink(temp_path)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return AnalyzeImageResponse(
            success=True,
            elements=[e.to_dict() for e in result.elements],
            colors=result.colors.to_dict(),
            layout=result.layout.value,
            typography=result.typography,
            dimensions=list(result.dimensions),
            processing_time=processing_time
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/sketch")
async def analyze_sketch(
    file: UploadFile = File(...),
    straighten_lines: bool = Form(True),
    enhance_contrast: bool = Form(True)
):
    """
    Analyze a hand-drawn sketch and convert to structured elements.
    
    - **file**: Sketch image file
    - **straighten_lines**: Whether to straighten nearly-straight lines
    - **enhance_contrast**: Whether to enhance contrast before analysis
    """
    try:
        # Save uploaded file
        temp_path = save_upload_file(file)
        
        # Analyze sketch
        result = sketch_analyzer.analyze(temp_path)
        
        # Clean up
        os.unlink(temp_path)
        
        return {
            "success": True,
            "shapes": [s.to_dict() for s in result.shapes],
            "elements": [e.to_dict() for e in result.elements],
            "connections": result.connections,
            "style": result.style.value,
            "dimensions": result.dimensions
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/video", response_model=VideoAnalysisResponse)
async def analyze_video(
    file: UploadFile = File(...),
    frame_interval: int = Form(30),
    extract_keyframes: bool = Form(True),
    num_keyframes: int = Form(5)
):
    """
    Analyze a video and extract UI behaviors.
    
    - **file**: Video file to analyze
    - **frame_interval**: Extract every Nth frame
    - **extract_keyframes**: Whether to extract keyframes
    - **num_keyframes**: Number of keyframes to extract
    """
    try:
        # Save uploaded file
        temp_path = save_upload_file(file)
        
        # Analyze video
        video_analyzer = VideoAnalyzer(frame_interval=frame_interval)
        result = video_analyzer.analyze_video(temp_path)
        
        # Extract keyframes if requested
        keyframes = None
        if extract_keyframes:
            keyframe_images = video_analyzer.extract_keyframes(temp_path, num_keyframes)
            keyframes = [encode_image_to_base64(kf) for kf in keyframe_images]
        
        # Clean up
        os.unlink(temp_path)
        
        return VideoAnalysisResponse(
            success=True,
            video_info=result["video_info"],
            frames_analyzed=result["video_info"]["frames_analyzed"],
            behaviors=result["behaviors"],
            keyframes=keyframes
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/code", response_model=GenerateCodeResponse)
async def generate_code(request: GenerateCodeRequest):
    """
    Generate code from visual analysis.
    
    - **analysis**: Visual analysis result
    - **framework**: Target framework (react, vue, angular, svelte)
    - **style_system**: Styling system (tailwind, css_modules, styled_components, scss)
    - **component_name**: Name for the generated component
    """
    try:
        # Map framework string to enum
        framework_map = {
            "react": Framework.REACT,
            "vue": Framework.VUE,
            "angular": Framework.ANGULAR,
            "svelte": Framework.SVELTE
        }
        framework = framework_map.get(request.framework.lower(), Framework.REACT)
        
        # Map style system string to enum
        style_map = {
            "tailwind": StyleSystem.TAILWIND,
            "css_modules": StyleSystem.CSS_MODULES,
            "styled_components": StyleSystem.STYLED_COMPONENTS,
            "scss": StyleSystem.SCSS,
            "plain_css": StyleSystem.PLAIN_CSS
        }
        style_system = style_map.get(request.style_system.lower(), StyleSystem.TAILWIND)
        
        # Generate code
        result = code_generator.generate_from_analysis(
            request.analysis,
            framework=framework,
            style_system=style_system,
            component_name=request.component_name
        )
        
        return GenerateCodeResponse(
            success=True,
            framework=result.framework.value,
            style_system=result.style_system.value,
            component_name=result.component_name,
            template_code=result.template_code,
            style_code=result.style_code,
            test_code=result.test_code
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/sketch-to-code")
async def sketch_to_code(
    file: UploadFile = File(...),
    framework: str = Form("react"),
    style_system: str = Form("tailwind")
):
    """
    Convert a sketch directly to code.
    
    - **file**: Sketch image file
    - **framework**: Target framework
    - **style_system**: Styling system
    """
    try:
        # Save uploaded file
        temp_path = save_upload_file(file)
        
        # Analyze sketch
        sketch_result = sketch_analyzer.analyze(temp_path)
        
        # Convert to analysis format
        analysis = {
            "elements": [e.to_dict() for e in sketch_result.elements],
            "colors": {"primary": "#3b82f6", "background": "#ffffff"},
            "layout": sketch_result.style.value,
            "typography": {}
        }
        
        # Generate code
        framework_map = {
            "react": Framework.REACT,
            "vue": Framework.VUE,
            "angular": Framework.ANGULAR,
            "svelte": Framework.SVELTE
        }
        style_map = {
            "tailwind": StyleSystem.TAILWIND,
            "css_modules": StyleSystem.CSS_MODULES,
            "scss": StyleSystem.SCSS
        }
        
        result = code_generator.generate_from_analysis(
            analysis,
            framework=framework_map.get(framework, Framework.REACT),
            style_system=style_map.get(style_system, StyleSystem.TAILWIND),
            component_name="SketchComponent"
        )
        
        # Clean up
        os.unlink(temp_path)
        
        return {
            "success": True,
            "sketch_analysis": sketch_result.to_dict(),
            "generated_code": {
                "framework": result.framework.value,
                "template_code": result.template_code,
                "style_code": result.style_code
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compare/images", response_model=CompareImagesResponse)
async def compare_images(
    expected: UploadFile = File(..., description="Expected/reference image"),
    actual: UploadFile = File(..., description="Actual/rendered image"),
    similarity_threshold: float = Form(0.95),
    mask_regions: Optional[str] = Form(None)
):
    """
    Compare two images and detect visual discrepancies.
    
    - **expected**: Expected/reference image
    - **actual**: Actual/rendered image
    - **similarity_threshold**: Threshold for similarity (0-1)
    - **mask_regions**: JSON array of regions to ignore [[x, y, w, h], ...]
    """
    try:
        # Save uploaded files
        expected_path = save_upload_file(expected)
        actual_path = save_upload_file(actual)
        
        # Parse mask regions
        mask = None
        if mask_regions:
            import json
            mask = json.loads(mask_regions)
        
        # Compare images
        comparator = ImageComparator(similarity_threshold=similarity_threshold)
        result = comparator.compare(expected_path, actual_path, mask)
        
        # Clean up
        os.unlink(expected_path)
        os.unlink(actual_path)
        
        return CompareImagesResponse(
            success=True,
            similarity_score=result.similarity_score,
            pixel_diff_percentage=result.pixel_diff_percentage,
            discrepancies=[d.to_dict() for d in result.discrepancies],
            has_issues=result.has_issues
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract/design-system", response_model=ExtractDesignSystemResponse)
async def extract_design_system(
    file: UploadFile = File(...),
    name: str = Form("Extracted Design System"),
    num_colors: int = Form(10)
):
    """
    Extract a design system from an image.
    
    - **file**: Image file to analyze
    - **name**: Name for the design system
    - **num_colors**: Number of colors to extract
    """
    try:
        # Save uploaded file
        temp_path = save_upload_file(file)
        
        # Extract design system
        design_system = design_extractor.extract_from_image(temp_path, name)
        
        # Clean up
        os.unlink(temp_path)
        
        return ExtractDesignSystemResponse(
            success=True,
            design_system=design_system.to_dict(),
            tailwind_config=design_system.to_tailwind_config(),
            css_variables=design_system.to_css_variables()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/debug/screenshot")
async def debug_screenshot(
    expected_design: UploadFile = File(...),
    actual_screenshot: UploadFile = File(...),
    expected_elements: Optional[str] = Form(None),
    actual_elements: Optional[str] = Form(None)
):
    """
    Debug a screenshot against expected design.
    
    - **expected_design**: Expected design image
    - **actual_screenshot**: Actual rendered screenshot
    - **expected_elements**: JSON array of expected UI elements
    - **actual_elements**: JSON array of actual UI elements
    """
    try:
        # Save uploaded files
        expected_path = save_upload_file(expected_design)
        actual_path = save_upload_file(actual_screenshot)
        
        # Parse elements if provided
        exp_elems = None
        act_elems = None
        if expected_elements:
            import json
            exp_elems = json.loads(expected_elements)
        if actual_elements:
            import json
            act_elems = json.loads(actual_elements)
        
        # Debug screenshot
        report = visual_debugger.debug_screenshot(
            expected_path, 
            actual_path,
            exp_elems,
            act_elems
        )
        
        # Clean up
        os.unlink(expected_path)
        os.unlink(actual_path)
        
        return report
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/convert/wireframe")
async def convert_to_wireframe(
    file: UploadFile = File(...)
):
    """
    Convert a sketch to a clean wireframe.
    
    - **file**: Sketch image file
    """
    try:
        # Save uploaded file
        temp_path = save_upload_file(file)
        
        # Convert to wireframe
        converter = WireframeConverter()
        wireframe = converter.convert_to_wireframe(temp_path)
        
        # Encode result
        wireframe_b64 = encode_image_to_base64(wireframe)
        
        # Clean up
        os.unlink(temp_path)
        
        return {
            "success": True,
            "wireframe": wireframe_b64
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# ============== Main ==============

def main():
    """Run the API server."""
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
