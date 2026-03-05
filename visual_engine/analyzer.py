"""
Mrki Visual Engine - Image/Video Analyzer
============================================
Screenshot/UI mockup analysis using vision models (GPT-4V, Claude Vision)
Supports image analysis, video frame extraction, and UI component detection.
"""

import cv2
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import base64
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UIElementType(Enum):
    """Types of UI elements that can be detected."""
    BUTTON = "button"
    INPUT = "input"
    TEXT = "text"
    IMAGE = "image"
    CONTAINER = "container"
    NAVBAR = "navbar"
    SIDEBAR = "sidebar"
    CARD = "card"
    MODAL = "modal"
    LIST = "list"
    ICON = "icon"
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SLIDER = "slider"
    UNKNOWN = "unknown"


class LayoutType(Enum):
    """Layout pattern types."""
    FLEX_ROW = "flex_row"
    FLEX_COLUMN = "flex_column"
    GRID = "grid"
    ABSOLUTE = "absolute"
    STACK = "stack"


@dataclass
class BoundingBox:
    """Bounding box for detected elements."""
    x: int
    y: int
    width: int
    height: int
    
    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def area(self) -> int:
        return self.width * self.height
    
    def to_dict(self) -> Dict[str, int]:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}
    
    def contains(self, other: 'BoundingBox') -> bool:
        """Check if this box contains another box."""
        return (self.x <= other.x and 
                self.y <= other.y and 
                self.x + self.width >= other.x + other.width and 
                self.y + self.height >= other.y + other.height)


@dataclass
class ColorInfo:
    """Color information for UI elements."""
    primary: str = ""
    secondary: str = ""
    background: str = ""
    text: str = ""
    accent: str = ""
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "background": self.background,
            "text": self.text,
            "accent": self.accent
        }


@dataclass
class UIElement:
    """Detected UI element with all properties."""
    id: str
    type: UIElementType
    bbox: BoundingBox
    text: str = ""
    confidence: float = 0.0
    styles: Dict[str, Any] = field(default_factory=dict)
    children: List['UIElement'] = field(default_factory=list)
    parent: Optional['UIElement'] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "bbox": self.bbox.to_dict(),
            "text": self.text,
            "confidence": self.confidence,
            "styles": self.styles,
            "children": [c.to_dict() for c in self.children]
        }


@dataclass
class AnalysisResult:
    """Complete analysis result for an image or video frame."""
    elements: List[UIElement]
    layout: LayoutType
    colors: ColorInfo
    typography: Dict[str, Any]
    dimensions: Tuple[int, int]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "elements": [e.to_dict() for e in self.elements],
            "layout": self.layout.value,
            "colors": self.colors.to_dict(),
            "typography": self.typography,
            "dimensions": self.dimensions,
            "metadata": self.metadata
        }


class ImageAnalyzer:
    """Main image analysis class using computer vision and ML models."""
    
    def __init__(self, vision_model: Optional[str] = None):
        """
        Initialize the image analyzer.
        
        Args:
            vision_model: Name of the vision model to use (gpt4v, claude, etc.)
        """
        self.vision_model = vision_model or "default"
        self.element_detector = ElementDetector()
        self.color_extractor = ColorExtractor()
        self.layout_analyzer = LayoutAnalyzer()
        self.text_detector = TextDetector()
        
    def analyze_image(self, image_path: Union[str, Path, np.ndarray]) -> AnalysisResult:
        """
        Analyze a single image and extract UI elements.
        
        Args:
            image_path: Path to image or numpy array
            
        Returns:
            AnalysisResult with all detected elements and metadata
        """
        # Load image
        if isinstance(image_path, (str, Path)):
            image = cv2.imread(str(image_path))
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image = image_path
            
        height, width = image.shape[:2]
        logger.info(f"Analyzing image: {width}x{height}")
        
        # Detect UI elements
        elements = self.element_detector.detect(image)
        
        # Extract colors
        colors = self.color_extractor.extract(image)
        
        # Analyze layout
        layout = self.layout_analyzer.analyze(elements, (width, height))
        
        # Detect text
        typography = self.text_detector.detect(image, elements)
        
        # Build hierarchy
        root_elements = self._build_hierarchy(elements)
        
        return AnalysisResult(
            elements=root_elements,
            layout=layout,
            colors=colors,
            typography=typography,
            dimensions=(width, height)
        )
    
    def analyze_batch(self, image_paths: List[Union[str, Path]]) -> List[AnalysisResult]:
        """Analyze multiple images in parallel."""
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(self.analyze_image, image_paths))
        return results
    
    def _build_hierarchy(self, elements: List[UIElement]) -> List[UIElement]:
        """Build parent-child hierarchy from flat element list."""
        # Sort by area (largest first)
        sorted_elements = sorted(elements, key=lambda e: e.bbox.area, reverse=True)
        
        root_elements = []
        
        for element in sorted_elements:
            placed = False
            for potential_parent in sorted_elements:
                if potential_parent != element and potential_parent.bbox.contains(element.bbox):
                    element.parent = potential_parent
                    potential_parent.children.append(element)
                    placed = True
                    break
            if not placed:
                root_elements.append(element)
                
        return root_elements


class ElementDetector:
    """Detect UI elements in images using computer vision."""
    
    def __init__(self):
        self.min_element_size = 20
        self.confidence_threshold = 0.5
        
    def detect(self, image: np.ndarray) -> List[UIElement]:
        """Detect all UI elements in the image."""
        elements = []
        element_id = 0
        
        # Detect buttons
        buttons = self._detect_buttons(image)
        for bbox in buttons:
            elements.append(UIElement(
                id=f"elem_{element_id}",
                type=UIElementType.BUTTON,
                bbox=bbox,
                confidence=0.85
            ))
            element_id += 1
        
        # Detect input fields
        inputs = self._detect_inputs(image)
        for bbox in inputs:
            elements.append(UIElement(
                id=f"elem_{element_id}",
                type=UIElementType.INPUT,
                bbox=bbox,
                confidence=0.80
            ))
            element_id += 1
        
        # Detect text regions
        texts = self._detect_text_regions(image)
        for bbox, text in texts:
            elements.append(UIElement(
                id=f"elem_{element_id}",
                type=UIElementType.TEXT,
                bbox=bbox,
                text=text,
                confidence=0.75
            ))
            element_id += 1
        
        # Detect images
        images = self._detect_images(image)
        for bbox in images:
            elements.append(UIElement(
                id=f"elem_{element_id}",
                type=UIElementType.IMAGE,
                bbox=bbox,
                confidence=0.70
            ))
            element_id += 1
        
        # Detect containers
        containers = self._detect_containers(image)
        for bbox in containers:
            elements.append(UIElement(
                id=f"elem_{element_id}",
                type=UIElementType.CONTAINER,
                bbox=bbox,
                confidence=0.65
            ))
            element_id += 1
        
        return elements
    
    def _detect_buttons(self, image: np.ndarray) -> List[BoundingBox]:
        """Detect button elements using shape and color analysis."""
        buttons = []
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by size
            if w < self.min_element_size or h < self.min_element_size:
                continue
            
            # Check aspect ratio (buttons are typically wider than tall)
            aspect_ratio = w / h if h > 0 else 0
            if 1.5 < aspect_ratio < 6 and h < 80:
                # Check for rounded corners or rectangular shape
                approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
                if len(approx) >= 4:
                    buttons.append(BoundingBox(x, y, w, h))
        
        return buttons
    
    def _detect_inputs(self, image: np.ndarray) -> List[BoundingBox]:
        """Detect input field elements."""
        inputs = []
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Look for rectangular regions with borders
        edges = cv2.Canny(gray, 30, 100)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Input fields are typically wide and short
            if w > 100 and 30 < h < 60:
                aspect_ratio = w / h if h > 0 else 0
                if aspect_ratio > 4:
                    inputs.append(BoundingBox(x, y, w, h))
        
        return inputs
    
    def _detect_text_regions(self, image: np.ndarray) -> List[Tuple[BoundingBox, str]]:
        """Detect text regions using OCR."""
        texts = []
        
        try:
            import pytesseract
            
            # Get text data with bounding boxes
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            for i, text in enumerate(data['text']):
                if int(data['conf'][i]) > 30:  # Confidence threshold
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    
                    if w > 10 and h > 10 and text.strip():
                        texts.append((BoundingBox(x, y, w, h), text))
        except ImportError:
            logger.warning("pytesseract not installed, skipping text detection")
        
        return texts
    
    def _detect_images(self, image: np.ndarray) -> List[BoundingBox]:
        """Detect image elements."""
        images = []
        
        # Look for regions with high color variance (typical of images)
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Use Laplacian to detect texture
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        # Find regions with significant texture
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter for image-like sizes
            if w > 50 and h > 50:
                roi = gray[y:y+h, x:x+w]
                if roi.size > 0:
                    roi_variance = cv2.Laplacian(roi, cv2.CV_64F).var()
                    if roi_variance > variance * 0.5:
                        images.append(BoundingBox(x, y, w, h))
        
        return images
    
    def _detect_containers(self, image: np.ndarray) -> List[BoundingBox]:
        """Detect container/div elements."""
        containers = []
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Look for large rectangular regions
        edges = cv2.Canny(gray, 30, 100)
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Containers are typically large
            if w > 200 and h > 100:
                containers.append(BoundingBox(x, y, w, h))
        
        return containers


class ColorExtractor:
    """Extract color palette from images."""
    
    def extract(self, image: np.ndarray) -> ColorInfo:
        """Extract dominant colors from the image."""
        # Reshape image for k-means
        pixels = image.reshape(-1, 3)
        pixels = np.float32(pixels)
        
        # K-means clustering to find dominant colors
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(pixels, 5, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Convert to hex colors
        colors = []
        for center in centers:
            r, g, b = int(center[0]), int(center[1]), int(center[2])
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            colors.append(hex_color)
        
        # Sort by frequency
        counts = np.bincount(labels.flatten())
        sorted_indices = np.argsort(counts)[::-1]
        sorted_colors = [colors[i] for i in sorted_indices]
        
        return ColorInfo(
            primary=sorted_colors[0] if len(sorted_colors) > 0 else "#000000",
            secondary=sorted_colors[1] if len(sorted_colors) > 1 else "#ffffff",
            background=sorted_colors[-1] if len(sorted_colors) > 0 else "#ffffff",
            text=sorted_colors[0] if len(sorted_colors) > 0 else "#000000",
            accent=sorted_colors[2] if len(sorted_colors) > 2 else sorted_colors[0]
        )


class LayoutAnalyzer:
    """Analyze layout patterns in UI designs."""
    
    def analyze(self, elements: List[UIElement], dimensions: Tuple[int, int]) -> LayoutType:
        """Determine the dominant layout pattern."""
        if not elements:
            return LayoutType.FLEX_COLUMN
        
        # Count horizontal vs vertical alignments
        horizontal_alignments = 0
        vertical_alignments = 0
        
        for i, elem1 in enumerate(elements):
            for elem2 in elements[i+1:]:
                # Check horizontal alignment
                if abs(elem1.bbox.y - elem2.bbox.y) < 20:
                    horizontal_alignments += 1
                # Check vertical alignment
                if abs(elem1.bbox.x - elem2.bbox.x) < 20:
                    vertical_alignments += 1
        
        # Determine layout type
        if horizontal_alignments > vertical_alignments * 1.5:
            return LayoutType.FLEX_ROW
        elif vertical_alignments > horizontal_alignments * 1.5:
            return LayoutType.FLEX_COLUMN
        elif len(elements) > 6:
            return LayoutType.GRID
        else:
            return LayoutType.FLEX_COLUMN


class TextDetector:
    """Detect and analyze text in images."""
    
    def detect(self, image: np.ndarray, elements: List[UIElement]) -> Dict[str, Any]:
        """Detect text properties and typography."""
        typography = {
            "fonts": [],
            "sizes": [],
            "weights": [],
            "line_heights": []
        }
        
        # Extract text elements
        text_elements = [e for e in elements if e.type == UIElementType.TEXT]
        
        if text_elements:
            # Estimate font sizes from bounding boxes
            sizes = [e.bbox.height for e in text_elements]
            typography["sizes"] = list(set(sizes))
            typography["sizes"].sort()
            
            # Estimate line heights
            if len(text_elements) > 1:
                sorted_by_y = sorted(text_elements, key=lambda e: e.bbox.y)
                line_heights = []
                for i in range(len(sorted_by_y) - 1):
                    gap = sorted_by_y[i+1].bbox.y - (sorted_by_y[i].bbox.y + sorted_by_y[i].bbox.height)
                    if gap > 0:
                        line_heights.append(gap)
                if line_heights:
                    typography["line_heights"] = list(set(line_heights))
        
        return typography


class VideoAnalyzer:
    """Analyze video files for UI behavior extraction."""
    
    def __init__(self, frame_interval: int = 30):
        """
        Initialize video analyzer.
        
        Args:
            frame_interval: Extract every Nth frame
        """
        self.frame_interval = frame_interval
        self.image_analyzer = ImageAnalyzer()
        
    def analyze_video(self, video_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Analyze a video file and extract UI behaviors.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with frame analysis and behavior detection
        """
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        logger.info(f"Video: {total_frames} frames, {fps} fps, {duration:.2f}s")
        
        frame_results = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process every Nth frame
            if frame_count % self.frame_interval == 0:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Analyze frame
                result = self.image_analyzer.analyze_image(frame_rgb)
                
                frame_results.append({
                    "frame_number": frame_count,
                    "timestamp": frame_count / fps if fps > 0 else 0,
                    "analysis": result.to_dict()
                })
            
            frame_count += 1
        
        cap.release()
        
        # Detect behaviors from frame sequence
        behaviors = self._detect_behaviors(frame_results)
        
        return {
            "video_info": {
                "fps": fps,
                "total_frames": total_frames,
                "duration": duration,
                "frames_analyzed": len(frame_results)
            },
            "frames": frame_results,
            "behaviors": behaviors
        }
    
    def _detect_behaviors(self, frame_results: List[Dict]) -> List[Dict[str, Any]]:
        """Detect UI behaviors from frame sequence."""
        behaviors = []
        
        if len(frame_results) < 2:
            return behaviors
        
        # Detect element appearances/disappearances
        prev_elements = set()
        
        for i, frame in enumerate(frame_results):
            current_elements = set()
            for elem in frame["analysis"]["elements"]:
                elem_key = f"{elem['type']}_{elem['bbox']['x']}_{elem['bbox']['y']}"
                current_elements.add(elem_key)
            
            # Detect new elements
            new_elements = current_elements - prev_elements
            if new_elements and i > 0:
                behaviors.append({
                    "type": "element_appear",
                    "timestamp": frame["timestamp"],
                    "elements": list(new_elements)
                })
            
            # Detect removed elements
            removed_elements = prev_elements - current_elements
            if removed_elements and i > 0:
                behaviors.append({
                    "type": "element_disappear",
                    "timestamp": frame["timestamp"],
                    "elements": list(removed_elements)
                })
            
            prev_elements = current_elements
        
        return behaviors
    
    def extract_keyframes(self, video_path: Union[str, Path], num_keyframes: int = 5) -> List[np.ndarray]:
        """Extract key representative frames from video."""
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_indices = np.linspace(0, total_frames - 1, num_keyframes, dtype=int)
        
        keyframes = []
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                keyframes.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        cap.release()
        return keyframes


def encode_image_to_base64(image_path: Union[str, Path]) -> str:
    """Encode an image file to base64 string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def decode_base64_to_image(base64_string: str) -> np.ndarray:
    """Decode base64 string to numpy image array."""
    image_data = base64.b64decode(base64_string)
    nparr = np.frombuffer(image_data, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)


# Export main classes
__all__ = [
    'ImageAnalyzer',
    'VideoAnalyzer',
    'ElementDetector',
    'ColorExtractor',
    'LayoutAnalyzer',
    'TextDetector',
    'UIElement',
    'UIElementType',
    'BoundingBox',
    'ColorInfo',
    'AnalysisResult',
    'LayoutType',
    'encode_image_to_base64',
    'decode_base64_to_image'
]
