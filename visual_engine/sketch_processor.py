"""
Mrki Visual Engine - Sketch Processor
======================================
Hand-drawn sketch recognition using edge detection and shape recognition.
Converts sketches to structured UI elements for code generation.
"""

import cv2
import numpy as np
from PIL import Image, ImageFilter
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import logging
from scipy.spatial.distance import cdist
from sklearn.cluster import DBSCAN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ShapeType(Enum):
    """Types of shapes that can be recognized in sketches."""
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    LINE = "line"
    ARROW = "arrow"
    TEXT_BOX = "text_box"
    BUTTON = "button"
    INPUT_FIELD = "input_field"
    CHECKBOX = "checkbox"
    RADIO_BUTTON = "radio_button"
    DROPDOWN = "dropdown"
    IMAGE_PLACEHOLDER = "image_placeholder"
    CONTAINER = "container"
    UNKNOWN = "unknown"


class SketchStyle(Enum):
    """Style of the sketch."""
    WIREFRAME = "wireframe"
    LOW_FIDELITY = "low_fidelity"
    HIGH_FIDELITY = "high_fidelity"
    HAND_DRAWN = "hand_drawn"


@dataclass
class SketchShape:
    """Recognized shape from a sketch."""
    id: str
    shape_type: ShapeType
    points: List[Tuple[int, int]]
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def center(self) -> Tuple[int, int]:
        x, y, w, h = self.bbox
        return (x + w // 2, y + h // 2)
    
    @property
    def area(self) -> int:
        _, _, w, h = self.bbox
        return w * h
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "shape_type": self.shape_type.value,
            "points": self.points,
            "bbox": self.bbox,
            "confidence": self.confidence,
            "metadata": self.metadata
        }


@dataclass
class SketchElement:
    """UI element derived from sketch shapes."""
    id: str
    element_type: str
    shapes: List[SketchShape]
    bbox: Tuple[int, int, int, int]
    label: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    children: List['SketchElement'] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "element_type": self.element_type,
            "shapes": [s.to_dict() for s in self.shapes],
            "bbox": self.bbox,
            "label": self.label,
            "properties": self.properties,
            "children": [c.to_dict() for c in self.children]
        }


@dataclass
class SketchAnalysis:
    """Complete analysis of a sketch."""
    shapes: List[SketchShape]
    elements: List[SketchElement]
    connections: List[Tuple[str, str]]  # Connections between elements
    style: SketchStyle
    dimensions: Tuple[int, int]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "shapes": [s.to_dict() for s in self.shapes],
            "elements": [e.to_dict() for e in self.elements],
            "connections": self.connections,
            "style": self.style.value,
            "dimensions": self.dimensions
        }


class SketchPreprocessor:
    """Preprocess sketch images for better recognition."""
    
    def __init__(self):
        self.min_line_thickness = 2
        self.max_line_thickness = 10
        
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess sketch image.
        
        Args:
            image: Input image (BGR or RGB)
            
        Returns:
            Preprocessed binary image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()
        
        # Remove noise
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Adaptive thresholding for binarization
        binary = cv2.adaptiveThreshold(
            enhanced, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 
            11, 2
        )
        
        # Clean up small noise
        kernel = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Close gaps in lines
        closed = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        return closed
    
    def remove_background(self, image: np.ndarray) -> np.ndarray:
        """Remove background from sketch image."""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()
        
        # Detect background color (most common color)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        bg_color = np.argmax(hist)
        
        # Create mask for foreground
        _, mask = cv2.threshold(gray, bg_color + 10, 255, cv2.THRESH_BINARY_INV)
        
        # Apply mask
        result = cv2.bitwise_and(gray, gray, mask=mask)
        
        return result
    
    def straighten_lines(self, image: np.ndarray, angle_threshold: float = 5.0) -> np.ndarray:
        """Straighten nearly-horizontal and nearly-vertical lines."""
        # Detect lines using Hough transform
        lines = cv2.HoughLinesP(image, 1, np.pi/180, 50, minLineLength=30, maxLineGap=10)
        
        if lines is None:
            return image
        
        result = np.zeros_like(image)
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            # Calculate angle
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            
            # Straighten if close to horizontal or vertical
            if abs(angle) < angle_threshold or abs(angle - 180) < angle_threshold:
                # Horizontal line
                y_avg = (y1 + y2) // 2
                cv2.line(result, (x1, y_avg), (x2, y_avg), 255, 2)
            elif abs(angle - 90) < angle_threshold or abs(angle + 90) < angle_threshold:
                # Vertical line
                x_avg = (x1 + x2) // 2
                cv2.line(result, (x_avg, y1), (x_avg, y2), 255, 2)
            else:
                # Keep original line
                cv2.line(result, (x1, y1), (x2, y2), 255, 2)
        
        return result


class EdgeDetector:
    """Detect edges in sketch images."""
    
    def __init__(self):
        self.canny_low = 50
        self.canny_high = 150
        
    def detect_edges(self, image: np.ndarray) -> np.ndarray:
        """Detect edges using Canny edge detector."""
        # Ensure grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Canny edge detection
        edges = cv2.Canny(blurred, self.canny_low, self.canny_high)
        
        return edges
    
    def detect_contours(self, image: np.ndarray) -> List[np.ndarray]:
        """Detect contours from edge image."""
        contours, hierarchy = cv2.findContours(
            image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        return contours
    
    def detect_lines(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect straight lines using Hough transform."""
        lines = cv2.HoughLinesP(
            image, 1, np.pi/180, 
            threshold=50, 
            minLineLength=30, 
            maxLineGap=10
        )
        
        if lines is None:
            return []
        
        return [(line[0][0], line[0][1], line[0][2], line[0][3]) for line in lines]


class ShapeRecognizer:
    """Recognize shapes from contours and edges."""
    
    def __init__(self):
        self.rectangle_threshold = 0.1  # Aspect ratio tolerance
        self.circle_threshold = 0.15    # Circularity tolerance
        
    def recognize_shapes(self, contours: List[np.ndarray], 
                         lines: List[Tuple[int, int, int, int]]) -> List[SketchShape]:
        """Recognize shapes from contours and lines."""
        shapes = []
        shape_id = 0
        
        # Process contours
        for contour in contours:
            shape = self._recognize_contour(contour, f"shape_{shape_id}")
            if shape:
                shapes.append(shape)
                shape_id += 1
        
        # Process lines for arrows and connectors
        arrow_shapes = self._recognize_arrows(lines)
        shapes.extend(arrow_shapes)
        
        return shapes
    
    def _recognize_contour(self, contour: np.ndarray, shape_id: str) -> Optional[SketchShape]:
        """Recognize a single contour."""
        # Approximate polygon
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Get bounding box
        x, y, w, h = cv2.boundingRect(contour)
        
        # Filter small contours
        if w < 10 or h < 10:
            return None
        
        # Calculate area and perimeter
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        if perimeter == 0:
            return None
        
        # Circularity check
        circularity = 4 * np.pi * area / (perimeter ** 2)
        
        # Get convex hull
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        
        # Solidity check
        solidity = area / hull_area if hull_area > 0 else 0
        
        # Extract points
        points = [(int(p[0][0]), int(p[0][1])) for p in approx]
        
        # Determine shape type
        shape_type = ShapeType.UNKNOWN
        confidence = 0.5
        
        if len(approx) == 4:
            # Could be rectangle
            aspect_ratio = float(w) / h if h > 0 else 0
            if 0.5 < aspect_ratio < 2.0:
                shape_type = ShapeType.RECTANGLE
                confidence = 0.85
                
                # Check if it's a specific UI element
                if aspect_ratio > 3:
                    shape_type = ShapeType.INPUT_FIELD
                elif aspect_ratio > 1.5 and w < 150:
                    shape_type = ShapeType.BUTTON
        
        elif circularity > 0.8:
            shape_type = ShapeType.CIRCLE
            confidence = 0.90
            
            # Check size for radio button or checkbox
            if w < 30 and h < 30:
                shape_type = ShapeType.RADIO_BUTTON
        
        elif len(approx) > 4 and solidity > 0.9:
            # Likely a container or complex shape
            shape_type = ShapeType.CONTAINER
            confidence = 0.70
        
        return SketchShape(
            id=shape_id,
            shape_type=shape_type,
            points=points,
            bbox=(x, y, w, h),
            confidence=confidence,
            metadata={
                "circularity": circularity,
                "solidity": solidity,
                "num_points": len(approx)
            }
        )
    
    def _recognize_arrows(self, lines: List[Tuple[int, int, int, int]]) -> List[SketchShape]:
        """Recognize arrow shapes from lines."""
        arrows = []
        
        # Group nearby lines
        if len(lines) < 2:
            return arrows
        
        # Convert to numpy array for clustering
        line_array = np.array(lines)
        centers = np.array([
            [(x1 + x2) / 2, (y1 + y2) / 2] 
            for x1, y1, x2, y2 in lines
        ])
        
        # Cluster lines by proximity
        if len(centers) > 1:
            clustering = DBSCAN(eps=30, min_samples=2).fit(centers)
            
            for cluster_id in set(clustering.labels_):
                if cluster_id == -1:
                    continue
                
                cluster_mask = clustering.labels_ == cluster_id
                cluster_lines = line_array[cluster_mask]
                
                # Check if lines form an arrow pattern
                if len(cluster_lines) >= 2:
                    # Find the main line (longest)
                    lengths = [np.sqrt((x2-x1)**2 + (y2-y1)**2) for x1, y1, x2, y2 in cluster_lines]
                    main_idx = np.argmax(lengths)
                    main_line = cluster_lines[main_idx]
                    
                    # Check for arrowhead pattern
                    x1, y1, x2, y2 = main_line
                    
                    # Bounding box for arrow
                    min_x = min(x1, x2) - 10
                    min_y = min(y1, y2) - 10
                    max_x = max(x1, x2) + 10
                    max_y = max(y1, y2) + 10
                    
                    arrows.append(SketchShape(
                        id=f"arrow_{len(arrows)}",
                        shape_type=ShapeType.ARROW,
                        points=[(x1, y1), (x2, y2)],
                        bbox=(min_x, min_y, max_x - min_x, max_y - min_y),
                        confidence=0.75,
                        metadata={"direction": "right" if x2 > x1 else "left"}
                    ))
        
        return arrows


class SketchAnalyzer:
    """Main class for analyzing sketches and converting to UI elements."""
    
    def __init__(self):
        self.preprocessor = SketchPreprocessor()
        self.edge_detector = EdgeDetector()
        self.shape_recognizer = ShapeRecognizer()
        
    def analyze(self, image_path: Union[str, Path, np.ndarray]) -> SketchAnalysis:
        """
        Analyze a sketch image and extract UI elements.
        
        Args:
            image_path: Path to sketch image or numpy array
            
        Returns:
            SketchAnalysis with recognized shapes and elements
        """
        # Load image
        if isinstance(image_path, (str, Path)):
            image = cv2.imread(str(image_path))
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image = image_path
        
        height, width = image.shape[:2]
        logger.info(f"Analyzing sketch: {width}x{height}")
        
        # Preprocess
        preprocessed = self.preprocessor.preprocess(image)
        
        # Detect edges
        edges = self.edge_detector.detect_edges(preprocessed)
        
        # Detect contours
        contours = self.edge_detector.detect_contours(edges)
        
        # Detect lines
        lines = self.edge_detector.detect_lines(edges)
        
        # Recognize shapes
        shapes = self.shape_recognizer.recognize_shapes(contours, lines)
        
        # Group shapes into UI elements
        elements = self._group_into_elements(shapes)
        
        # Detect connections between elements
        connections = self._detect_connections(elements)
        
        # Detect sketch style
        style = self._detect_style(image, shapes)
        
        return SketchAnalysis(
            shapes=shapes,
            elements=elements,
            connections=connections,
            style=style,
            dimensions=(width, height)
        )
    
    def _group_into_elements(self, shapes: List[SketchShape]) -> List[SketchElement]:
        """Group shapes into UI elements."""
        elements = []
        element_id = 0
        
        # Sort shapes by position (top to bottom, left to right)
        sorted_shapes = sorted(shapes, key=lambda s: (s.bbox[1], s.bbox[0]))
        
        used_shapes = set()
        
        for i, shape in enumerate(sorted_shapes):
            if shape.id in used_shapes:
                continue
            
            # Find related shapes (overlapping or nearby)
            related_shapes = [shape]
            used_shapes.add(shape.id)
            
            for other in sorted_shapes[i+1:]:
                if other.id in used_shapes:
                    continue
                
                # Check if shapes are related
                if self._shapes_are_related(shape, other):
                    related_shapes.append(other)
                    used_shapes.add(other.id)
            
            # Create element from related shapes
            element = self._create_element(related_shapes, f"element_{element_id}")
            if element:
                elements.append(element)
                element_id += 1
        
        # Build hierarchy
        elements = self._build_hierarchy(elements)
        
        return elements
    
    def _shapes_are_related(self, shape1: SketchShape, shape2: SketchShape, 
                           threshold: int = 20) -> bool:
        """Check if two shapes are related (part of same element)."""
        x1, y1, w1, h1 = shape1.bbox
        x2, y2, w2, h2 = shape2.bbox
        
        # Check overlap
        if (x1 < x2 + w2 + threshold and x1 + w1 + threshold > x2 and
            y1 < y2 + h2 + threshold and y1 + h1 + threshold > y2):
            return True
        
        # Check if one contains the other
        if (x1 <= x2 and y1 <= y2 and x1 + w1 >= x2 + w2 and y1 + h1 >= y2 + h2):
            return True
        
        if (x2 <= x1 and y2 <= y1 and x2 + w2 >= x1 + w1 and y2 + h2 >= y1 + h1):
            return True
        
        return False
    
    def _create_element(self, shapes: List[SketchShape], element_id: str) -> Optional[SketchElement]:
        """Create a UI element from shapes."""
        if not shapes:
            return None
        
        # Determine element type from shapes
        shape_types = [s.shape_type for s in shapes]
        
        element_type = "container"
        label = ""
        properties = {}
        
        if ShapeType.BUTTON in shape_types:
            element_type = "button"
            label = "Button"
        elif ShapeType.INPUT_FIELD in shape_types:
            element_type = "input"
            label = "Input"
        elif ShapeType.CHECKBOX in shape_types:
            element_type = "checkbox"
            label = "Checkbox"
        elif ShapeType.RADIO_BUTTON in shape_types:
            element_type = "radio"
            label = "Radio"
        elif ShapeType.IMAGE_PLACEHOLDER in shape_types:
            element_type = "image"
            label = "Image"
        elif ShapeType.TEXT_BOX in shape_types:
            element_type = "text"
            label = "Text"
        
        # Calculate combined bounding box
        min_x = min(s.bbox[0] for s in shapes)
        min_y = min(s.bbox[1] for s in shapes)
        max_x = max(s.bbox[0] + s.bbox[2] for s in shapes)
        max_y = max(s.bbox[1] + s.bbox[3] for s in shapes)
        
        bbox = (min_x, min_y, max_x - min_x, max_y - min_y)
        
        return SketchElement(
            id=element_id,
            element_type=element_type,
            shapes=shapes,
            bbox=bbox,
            label=label,
            properties=properties
        )
    
    def _build_hierarchy(self, elements: List[SketchElement]) -> List[SketchElement]:
        """Build parent-child hierarchy from elements."""
        # Sort by area (largest first)
        sorted_elements = sorted(elements, key=lambda e: e.bbox[2] * e.bbox[3], reverse=True)
        
        root_elements = []
        
        for element in sorted_elements:
            placed = False
            x1, y1, w1, h1 = element.bbox
            
            for potential_parent in sorted_elements:
                if potential_parent == element:
                    continue
                
                x2, y2, w2, h2 = potential_parent.bbox
                
                # Check if element is inside potential parent
                if (x2 <= x1 and y2 <= y1 and 
                    x2 + w2 >= x1 + w1 and y2 + h2 >= y1 + h1):
                    potential_parent.children.append(element)
                    placed = True
                    break
            
            if not placed:
                root_elements.append(element)
        
        return root_elements
    
    def _detect_connections(self, elements: List[SketchElement]) -> List[Tuple[str, str]]:
        """Detect connections between elements (e.g., arrows)."""
        connections = []
        
        # Find arrow shapes
        arrows = []
        for elem in elements:
            for shape in elem.shapes:
                if shape.shape_type == ShapeType.ARROW:
                    arrows.append((shape, elem))
        
        # Match arrows to elements
        for arrow_shape, arrow_elem in arrows:
            arrow_center = arrow_shape.center
            
            # Find closest elements to arrow start and end
            closest_start = None
            closest_end = None
            min_start_dist = float('inf')
            min_end_dist = float('inf')
            
            for elem in elements:
                if elem == arrow_elem:
                    continue
                
                elem_center = (elem.bbox[0] + elem.bbox[2] // 2, 
                              elem.bbox[1] + elem.bbox[3] // 2)
                
                dist = np.sqrt((arrow_center[0] - elem_center[0])**2 + 
                              (arrow_center[1] - elem_center[1])**2)
                
                if arrow_shape.metadata.get("direction") == "right":
                    if elem_center[0] < arrow_center[0] and dist < min_start_dist:
                        min_start_dist = dist
                        closest_start = elem
                    elif elem_center[0] > arrow_center[0] and dist < min_end_dist:
                        min_end_dist = dist
                        closest_end = elem
                else:
                    if elem_center[0] > arrow_center[0] and dist < min_start_dist:
                        min_start_dist = dist
                        closest_start = elem
                    elif elem_center[0] < arrow_center[0] and dist < min_end_dist:
                        min_end_dist = dist
                        closest_end = elem
            
            if closest_start and closest_end:
                connections.append((closest_start.id, closest_end.id))
        
        return connections
    
    def _detect_style(self, image: np.ndarray, shapes: List[SketchShape]) -> SketchStyle:
        """Detect the style of the sketch."""
        # Check for color
        if len(image.shape) == 3:
            # Check if image has significant color variation
            std = np.std(image, axis=(0, 1))
            if np.mean(std) > 30:
                return SketchStyle.HIGH_FIDELITY
        
        # Check line quality
        if shapes:
            avg_confidence = np.mean([s.confidence for s in shapes])
            if avg_confidence > 0.8:
                return SketchStyle.WIREFRAME
            elif avg_confidence > 0.6:
                return SketchStyle.LOW_FIDELITY
        
        return SketchStyle.HAND_DRAWN


class WireframeConverter:
    """Convert sketches to wireframe representations."""
    
    def __init__(self):
        self.analyzer = SketchAnalyzer()
        
    def convert_to_wireframe(self, image_path: Union[str, Path, np.ndarray]) -> np.ndarray:
        """
        Convert a sketch to a clean wireframe.
        
        Args:
            image_path: Path to sketch image or numpy array
            
        Returns:
            Wireframe image as numpy array
        """
        # Analyze sketch
        analysis = self.analyzer.analyze(image_path)
        
        # Create blank canvas
        width, height = analysis.dimensions
        wireframe = np.ones((height, width, 3), dtype=np.uint8) * 255
        
        # Draw elements
        for element in analysis.elements:
            self._draw_element(wireframe, element)
        
        # Draw connections
        for conn in analysis.connections:
            self._draw_connection(wireframe, conn, analysis.elements)
        
        return wireframe
    
    def _draw_element(self, canvas: np.ndarray, element: SketchElement):
        """Draw an element on the wireframe canvas."""
        x, y, w, h = element.bbox
        
        # Draw based on element type
        if element.element_type == "button":
            cv2.rectangle(canvas, (x, y), (x + w, y + h), (0, 0, 0), 2)
            cv2.putText(canvas, element.label, (x + 10, y + h // 2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        elif element.element_type == "input":
            cv2.rectangle(canvas, (x, y), (x + w, y + h), (128, 128, 128), 1)
            cv2.putText(canvas, "Input...", (x + 5, y + h // 2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (128, 128, 128), 1)
        
        elif element.element_type == "image":
            cv2.rectangle(canvas, (x, y), (x + w, y + h), (0, 0, 0), 1)
            # Draw X pattern
            cv2.line(canvas, (x, y), (x + w, y + h), (200, 200, 200), 1)
            cv2.line(canvas, (x + w, y), (x, y + h), (200, 200, 200), 1)
        
        elif element.element_type == "text":
            cv2.putText(canvas, "Text content", (x, y + h // 2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        else:
            cv2.rectangle(canvas, (x, y), (x + w, y + h), (0, 0, 0), 1)
        
        # Draw children
        for child in element.children:
            self._draw_element(canvas, child)
    
    def _draw_connection(self, canvas: np.ndarray, connection: Tuple[str, str], 
                        elements: List[SketchElement]):
        """Draw a connection between elements."""
        # Find elements by ID
        elem1 = next((e for e in elements if e.id == connection[0]), None)
        elem2 = next((e for e in elements if e.id == connection[1]), None)
        
        if elem1 and elem2:
            x1 = elem1.bbox[0] + elem1.bbox[2] // 2
            y1 = elem1.bbox[1] + elem1.bbox[3] // 2
            x2 = elem2.bbox[0] + elem2.bbox[2] // 2
            y2 = elem2.bbox[1] + elem2.bbox[3] // 2
            
            cv2.arrowedLine(canvas, (x1, y1), (x2, y2), (0, 0, 255), 2)


# Export main classes
__all__ = [
    'SketchAnalyzer',
    'SketchPreprocessor',
    'EdgeDetector',
    'ShapeRecognizer',
    'WireframeConverter',
    'SketchShape',
    'SketchElement',
    'SketchAnalysis',
    'ShapeType',
    'SketchStyle'
]
