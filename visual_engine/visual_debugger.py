"""
Mrki Visual Engine - Visual Debugger
======================================
Screenshot comparison and discrepancy detection.
Compare rendered output with expected designs.
"""

import cv2
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import logging
from scipy.spatial.distance import cosine
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import mean_squared_error

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscrepancyType(Enum):
    """Types of visual discrepancies."""
    COLOR_MISMATCH = "color_mismatch"
    POSITION_MISMATCH = "position_mismatch"
    SIZE_MISMATCH = "size_mismatch"
    MISSING_ELEMENT = "missing_element"
    EXTRA_ELEMENT = "extra_element"
    TEXT_MISMATCH = "text_mismatch"
    FONT_MISMATCH = "font_mismatch"
    SPACING_MISMATCH = "spacing_mismatch"
    ALIGNMENT_MISMATCH = "alignment_mismatch"
    VISUAL_REGRESSION = "visual_regression"


class Severity(Enum):
    """Severity levels for discrepancies."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Discrepancy:
    """A detected visual discrepancy."""
    type: DiscrepancyType
    severity: Severity
    message: str
    location: Optional[Tuple[int, int, int, int]] = None  # x, y, w, h
    expected_value: Any = None
    actual_value: Any = None
    confidence: float = 1.0
    suggestion: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "message": self.message,
            "location": self.location,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "confidence": self.confidence,
            "suggestion": self.suggestion
        }


@dataclass
class ComparisonResult:
    """Result of comparing two images."""
    similarity_score: float
    pixel_diff_percentage: float
    discrepancies: List[Discrepancy]
    diff_image: Optional[np.ndarray] = None
    annotated_image: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "similarity_score": self.similarity_score,
            "pixel_diff_percentage": self.pixel_diff_percentage,
            "discrepancies": [d.to_dict() for d in self.discrepancies],
            "metadata": self.metadata
        }
    
    @property
    def has_issues(self) -> bool:
        """Check if comparison found any issues."""
        return len(self.discrepancies) > 0 or self.similarity_score < 0.95
    
    @property
    def critical_issues(self) -> List[Discrepancy]:
        """Get critical severity discrepancies."""
        return [d for d in self.discrepancies if d.severity == Severity.CRITICAL]
    
    @property
    def high_issues(self) -> List[Discrepancy]:
        """Get high severity discrepancies."""
        return [d for d in self.discrepancies if d.severity == Severity.HIGH]


@dataclass
class ElementMatch:
    """Match between expected and actual elements."""
    expected_element: Dict[str, Any]
    actual_element: Optional[Dict[str, Any]]
    match_score: float
    discrepancies: List[Discrepancy]


class ImageComparator:
    """Compare images and detect differences."""
    
    def __init__(self, similarity_threshold: float = 0.95):
        """
        Initialize image comparator.
        
        Args:
            similarity_threshold: Threshold for considering images similar
        """
        self.similarity_threshold = similarity_threshold
        
    def compare(self, expected: Union[str, Path, np.ndarray],
                actual: Union[str, Path, np.ndarray],
                mask_regions: Optional[List[Tuple[int, int, int, int]]] = None) -> ComparisonResult:
        """
        Compare two images and detect differences.
        
        Args:
            expected: Expected/reference image
            actual: Actual/rendered image
            mask_regions: Regions to ignore in comparison
            
        Returns:
            ComparisonResult with discrepancies
        """
        # Load images
        expected_img = self._load_image(expected)
        actual_img = self._load_image(actual)
        
        # Ensure same size
        if expected_img.shape != actual_img.shape:
            logger.warning("Images have different sizes, resizing actual to match expected")
            actual_img = cv2.resize(actual_img, (expected_img.shape[1], expected_img.shape[0]))
        
        # Apply mask if provided
        if mask_regions:
            expected_img = self._apply_mask(expected_img, mask_regions)
            actual_img = self._apply_mask(actual_img, mask_regions)
        
        # Calculate similarity metrics
        similarity_score = self._calculate_ssim(expected_img, actual_img)
        pixel_diff = self._calculate_pixel_difference(expected_img, actual_img)
        
        # Generate diff image
        diff_image = self._generate_diff_image(expected_img, actual_img)
        
        # Detect discrepancies
        discrepancies = []
        
        if similarity_score < self.similarity_threshold:
            discrepancies.extend(self._detect_color_discrepancies(expected_img, actual_img))
            discrepancies.extend(self._detect_layout_discrepancies(expected_img, actual_img))
        
        # Create annotated image
        annotated = self._create_annotated_image(actual_img, discrepancies)
        
        return ComparisonResult(
            similarity_score=similarity_score,
            pixel_diff_percentage=pixel_diff,
            discrepancies=discrepancies,
            diff_image=diff_image,
            annotated_image=annotated,
            metadata={
                "expected_shape": expected_img.shape,
                "actual_shape": actual_img.shape,
                "threshold": self.similarity_threshold
            }
        )
    
    def _load_image(self, image: Union[str, Path, np.ndarray]) -> np.ndarray:
        """Load image from path or return numpy array."""
        if isinstance(image, (str, Path)):
            img = cv2.imread(str(image))
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return image
    
    def _apply_mask(self, image: np.ndarray, 
                    regions: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """Apply mask to ignore certain regions."""
        masked = image.copy()
        for x, y, w, h in regions:
            masked[y:y+h, x:x+w] = [128, 128, 128]  # Gray out masked regions
        return masked
    
    def _calculate_ssim(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Calculate Structural Similarity Index."""
        gray1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY)
        
        score, _ = ssim(gray1, gray2, full=True)
        return score
    
    def _calculate_pixel_difference(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Calculate percentage of different pixels."""
        diff = cv2.absdiff(img1, img2)
        diff_pixels = np.count_nonzero(diff)
        total_pixels = img1.shape[0] * img1.shape[1] * img1.shape[2]
        return (diff_pixels / total_pixels) * 100
    
    def _calculate_mse(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Calculate Mean Squared Error."""
        gray1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY)
        return mean_squared_error(gray1, gray2)
    
    def _generate_diff_image(self, img1: np.ndarray, img2: np.ndarray) -> np.ndarray:
        """Generate visual diff image."""
        diff = cv2.absdiff(img1, img2)
        
        # Enhance differences
        diff_enhanced = cv2.convertScaleAbs(diff, alpha=2.0, beta=0)
        
        return diff_enhanced
    
    def _detect_color_discrepancies(self, expected: np.ndarray, 
                                     actual: np.ndarray) -> List[Discrepancy]:
        """Detect color discrepancies between images."""
        discrepancies = []
        
        # Calculate color histograms
        expected_hist = self._calculate_color_histogram(expected)
        actual_hist = self._calculate_color_histogram(actual)
        
        # Compare histograms
        correlation = cv2.compareHist(expected_hist, actual_hist, cv2.HISTCMP_CORREL)
        
        if correlation < 0.9:
            # Extract dominant colors
            expected_colors = self._extract_dominant_colors(expected)
            actual_colors = self._extract_dominant_colors(actual)
            
            # Find color differences
            for i, (exp_color, act_color) in enumerate(zip(expected_colors, actual_colors)):
                color_diff = np.linalg.norm(np.array(exp_color) - np.array(act_color))
                
                if color_diff > 30:  # Significant color difference
                    discrepancies.append(Discrepancy(
                        type=DiscrepancyType.COLOR_MISMATCH,
                        severity=Severity.HIGH if color_diff > 50 else Severity.MEDIUM,
                        message=f"Color mismatch detected in dominant color {i+1}",
                        expected_value=f"RGB{exp_color}",
                        actual_value=f"RGB{act_color}",
                        confidence=min(color_diff / 100, 1.0),
                        suggestion=f"Update color to match design: RGB{exp_color}"
                    ))
        
        return discrepancies
    
    def _calculate_color_histogram(self, image: np.ndarray) -> np.ndarray:
        """Calculate color histogram for image."""
        hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        return hist
    
    def _extract_dominant_colors(self, image: np.ndarray, n_colors: int = 5) -> List[Tuple[int, int, int]]:
        """Extract dominant colors using k-means."""
        pixels = image.reshape(-1, 3)
        pixels = np.float32(pixels)
        
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(pixels, n_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        colors = [(int(c[0]), int(c[1]), int(c[2])) for c in centers]
        return colors
    
    def _detect_layout_discrepancies(self, expected: np.ndarray, 
                                      actual: np.ndarray) -> List[Discrepancy]:
        """Detect layout discrepancies."""
        discrepancies = []
        
        # Detect edges in both images
        expected_edges = self._detect_edges(expected)
        actual_edges = self._detect_edges(actual)
        
        # Compare edge positions
        edge_diff = cv2.absdiff(expected_edges, actual_edges)
        
        # Find contours in edge difference
        contours, _ = cv2.findContours(edge_diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 100:  # Significant difference
                x, y, w, h = cv2.boundingRect(contour)
                
                discrepancies.append(Discrepancy(
                    type=DiscrepancyType.POSITION_MISMATCH,
                    severity=Severity.MEDIUM if area < 500 else Severity.HIGH,
                    message=f"Layout discrepancy detected at position ({x}, {y})",
                    location=(x, y, w, h),
                    confidence=min(area / 1000, 1.0),
                    suggestion="Review element positioning and alignment"
                ))
        
        return discrepancies
    
    def _detect_edges(self, image: np.ndarray) -> np.ndarray:
        """Detect edges in image."""
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        return edges
    
    def _create_annotated_image(self, image: np.ndarray, 
                                 discrepancies: List[Discrepancy]) -> np.ndarray:
        """Create image with discrepancy annotations."""
        annotated = image.copy()
        
        for disc in discrepancies:
            if disc.location:
                x, y, w, h = disc.location
                
                # Color based on severity
                color_map = {
                    Severity.CRITICAL: (255, 0, 0),
                    Severity.HIGH: (255, 100, 0),
                    Severity.MEDIUM: (255, 200, 0),
                    Severity.LOW: (0, 255, 0),
                    Severity.INFO: (0, 200, 255)
                }
                color = color_map.get(disc.severity, (128, 128, 128))
                
                # Draw rectangle
                cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
                
                # Add label
                label = f"{disc.type.value}: {disc.severity.value}"
                cv2.putText(annotated, label, (x, y - 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        return annotated


class ElementComparator:
    """Compare UI elements between expected and actual."""
    
    def __init__(self, position_tolerance: int = 5, size_tolerance: float = 0.1):
        """
        Initialize element comparator.
        
        Args:
            position_tolerance: Pixel tolerance for position matching
            size_tolerance: Percentage tolerance for size matching
        """
        self.position_tolerance = position_tolerance
        self.size_tolerance = size_tolerance
    
    def compare_elements(self, expected_elements: List[Dict[str, Any]],
                         actual_elements: List[Dict[str, Any]]) -> List[ElementMatch]:
        """
        Compare expected and actual UI elements.
        
        Args:
            expected_elements: Expected UI elements
            actual_elements: Actual UI elements
            
        Returns:
            List of element matches with discrepancies
        """
        matches = []
        matched_actual = set()
        
        for expected in expected_elements:
            # Find best matching actual element
            best_match = None
            best_score = 0
            
            for i, actual in enumerate(actual_elements):
                if i in matched_actual:
                    continue
                
                score = self._calculate_element_match_score(expected, actual)
                
                if score > best_score and score > 0.5:
                    best_score = score
                    best_match = (i, actual)
            
            if best_match:
                matched_actual.add(best_match[0])
                discrepancies = self._find_element_discrepancies(expected, best_match[1])
                
                matches.append(ElementMatch(
                    expected_element=expected,
                    actual_element=best_match[1],
                    match_score=best_score,
                    discrepancies=discrepancies
                ))
            else:
                # No match found - missing element
                matches.append(ElementMatch(
                    expected_element=expected,
                    actual_element=None,
                    match_score=0,
                    discrepancies=[Discrepancy(
                        type=DiscrepancyType.MISSING_ELEMENT,
                        severity=Severity.CRITICAL,
                        message=f"Missing element: {expected.get('type', 'unknown')}",
                        expected_value=expected,
                        suggestion="Add missing element to implementation"
                    )]
                ))
        
        # Check for extra elements
        for i, actual in enumerate(actual_elements):
            if i not in matched_actual:
                matches.append(ElementMatch(
                    expected_element=None,
                    actual_element=actual,
                    match_score=0,
                    discrepancies=[Discrepancy(
                        type=DiscrepancyType.EXTRA_ELEMENT,
                        severity=Severity.LOW,
                        message=f"Extra element found: {actual.get('type', 'unknown')}",
                        actual_value=actual,
                        suggestion="Remove extra element or update design"
                    )]
                ))
        
        return matches
    
    def _calculate_element_match_score(self, expected: Dict[str, Any],
                                        actual: Dict[str, Any]) -> float:
        """Calculate match score between two elements."""
        scores = []
        
        # Type match
        if expected.get("type") == actual.get("type"):
            scores.append(1.0)
        else:
            scores.append(0.3)
        
        # Position match
        expected_bbox = expected.get("bbox", {})
        actual_bbox = actual.get("bbox", {})
        
        if expected_bbox and actual_bbox:
            exp_center = (expected_bbox.get("x", 0) + expected_bbox.get("width", 0) / 2,
                         expected_bbox.get("y", 0) + expected_bbox.get("height", 0) / 2)
            act_center = (actual_bbox.get("x", 0) + actual_bbox.get("width", 0) / 2,
                         actual_bbox.get("y", 0) + actual_bbox.get("height", 0) / 2)
            
            distance = np.sqrt((exp_center[0] - act_center[0])**2 + 
                             (exp_center[1] - act_center[1])**2)
            
            if distance <= self.position_tolerance:
                scores.append(1.0)
            else:
                scores.append(max(0, 1 - distance / 100))
        
        # Size match
        if expected_bbox and actual_bbox:
            exp_w = expected_bbox.get("width", 0)
            exp_h = expected_bbox.get("height", 0)
            act_w = actual_bbox.get("width", 0)
            act_h = actual_bbox.get("height", 0)
            
            if exp_w > 0 and exp_h > 0:
                w_ratio = min(act_w, exp_w) / max(act_w, exp_w)
                h_ratio = min(act_h, exp_h) / max(act_h, exp_h)
                scores.append((w_ratio + h_ratio) / 2)
        
        # Text match
        if expected.get("text") and actual.get("text"):
            if expected["text"] == actual["text"]:
                scores.append(1.0)
            else:
                scores.append(0.5)
        
        return np.mean(scores) if scores else 0
    
    def _find_element_discrepancies(self, expected: Dict[str, Any],
                                     actual: Dict[str, Any]) -> List[Discrepancy]:
        """Find discrepancies between matched elements."""
        discrepancies = []
        
        expected_bbox = expected.get("bbox", {})
        actual_bbox = actual.get("bbox", {})
        
        # Position discrepancy
        if expected_bbox and actual_bbox:
            exp_x = expected_bbox.get("x", 0)
            exp_y = expected_bbox.get("y", 0)
            act_x = actual_bbox.get("x", 0)
            act_y = actual_bbox.get("y", 0)
            
            x_diff = abs(exp_x - act_x)
            y_diff = abs(exp_y - act_y)
            
            if x_diff > self.position_tolerance or y_diff > self.position_tolerance:
                discrepancies.append(Discrepancy(
                    type=DiscrepancyType.POSITION_MISMATCH,
                    severity=Severity.MEDIUM if max(x_diff, y_diff) < 20 else Severity.HIGH,
                    message=f"Element position differs by ({x_diff}, {y_diff}) pixels",
                    expected_value=f"({exp_x}, {exp_y})",
                    actual_value=f"({act_x}, {act_y})",
                    location=(act_x, act_y, actual_bbox.get("width", 0), actual_bbox.get("height", 0)),
                    suggestion=f"Adjust position to match design: ({exp_x}, {exp_y})"
                ))
        
        # Size discrepancy
        if expected_bbox and actual_bbox:
            exp_w = expected_bbox.get("width", 0)
            exp_h = expected_bbox.get("height", 0)
            act_w = actual_bbox.get("width", 0)
            act_h = actual_bbox.get("height", 0)
            
            w_diff_pct = abs(exp_w - act_w) / exp_w if exp_w > 0 else 0
            h_diff_pct = abs(exp_h - act_h) / exp_h if exp_h > 0 else 0
            
            if w_diff_pct > self.size_tolerance or h_diff_pct > self.size_tolerance:
                discrepancies.append(Discrepancy(
                    type=DiscrepancyType.SIZE_MISMATCH,
                    severity=Severity.MEDIUM if max(w_diff_pct, h_diff_pct) < 0.2 else Severity.HIGH,
                    message=f"Element size differs from expected",
                    expected_value=f"{exp_w}x{exp_h}",
                    actual_value=f"{act_w}x{act_h}",
                    location=(act_x, act_y, act_w, act_h),
                    suggestion=f"Adjust size to match design: {exp_w}x{exp_h}"
                ))
        
        # Text discrepancy
        exp_text = expected.get("text", "")
        act_text = actual.get("text", "")
        
        if exp_text and exp_text != act_text:
            discrepancies.append(Discrepancy(
                type=DiscrepancyType.TEXT_MISMATCH,
                severity=Severity.HIGH,
                message="Element text does not match",
                expected_value=exp_text,
                actual_value=act_text,
                suggestion=f"Update text to: '{exp_text}'"
            ))
        
        # Style discrepancies
        exp_styles = expected.get("styles", {})
        act_styles = actual.get("styles", {})
        
        for style_prop, exp_value in exp_styles.items():
            act_value = act_styles.get(style_prop)
            if act_value != exp_value:
                discrepancies.append(Discrepancy(
                    type=DiscrepancyType.COLOR_MISMATCH if "color" in style_prop else DiscrepancyType.VISUAL_REGRESSION,
                    severity=Severity.MEDIUM,
                    message=f"Style property '{style_prop}' differs",
                    expected_value=exp_value,
                    actual_value=act_value,
                    suggestion=f"Update {style_prop} to: {exp_value}"
                ))
        
        return discrepancies


class VisualDebugger:
    """Main visual debugging class."""
    
    def __init__(self, similarity_threshold: float = 0.95):
        """
        Initialize visual debugger.
        
        Args:
            similarity_threshold: Threshold for image similarity
        """
        self.image_comparator = ImageComparator(similarity_threshold)
        self.element_comparator = ElementComparator()
        
    def debug_screenshot(self, expected_image: Union[str, Path, np.ndarray],
                         actual_image: Union[str, Path, np.ndarray],
                         expected_elements: Optional[List[Dict]] = None,
                         actual_elements: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Debug a screenshot against expected design.
        
        Args:
            expected_image: Expected design image
            actual_image: Actual rendered screenshot
            expected_elements: Expected UI elements (optional)
            actual_elements: Actual UI elements (optional)
            
        Returns:
            Debug report with discrepancies
        """
        # Compare images
        image_comparison = self.image_comparator.compare(expected_image, actual_image)
        
        # Compare elements if provided
        element_comparison = None
        if expected_elements and actual_elements:
            element_comparison = self.element_comparator.compare_elements(
                expected_elements, actual_elements
            )
        
        # Generate report
        report = {
            "summary": {
                "similarity_score": image_comparison.similarity_score,
                "pixel_diff_percentage": image_comparison.pixel_diff_percentage,
                "total_discrepancies": len(image_comparison.discrepancies),
                "critical_issues": len(image_comparison.critical_issues),
                "high_issues": len(image_comparison.high_issues),
                "passed": not image_comparison.has_issues
            },
            "image_comparison": image_comparison.to_dict(),
            "element_comparison": None
        }
        
        if element_comparison:
            report["element_comparison"] = {
                "total_matches": len(element_comparison),
                "matched_elements": sum(1 for m in element_comparison if m.match_score > 0.8),
                "missing_elements": sum(1 for m in element_comparison if m.actual_element is None),
                "extra_elements": sum(1 for m in element_comparison if m.expected_element is None),
                "matches": [{
                    "expected": m.expected_element,
                    "actual": m.actual_element,
                    "score": m.match_score,
                    "discrepancies": [d.to_dict() for d in m.discrepancies]
                } for m in element_comparison]
            }
        
        return report
    
    def generate_diff_report(self, comparison_result: ComparisonResult,
                            output_path: Optional[str] = None) -> str:
        """
        Generate HTML diff report.
        
        Args:
            comparison_result: Comparison result
            output_path: Path to save HTML report
            
        Returns:
            HTML report string
        """
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Visual Diff Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 8px; }}
        .metric {{ display: inline-block; margin: 10px 20px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .discrepancy {{ 
            border: 1px solid #ddd; 
            margin: 10px 0; 
            padding: 15px; 
            border-radius: 5px;
        }}
        .critical {{ border-left: 4px solid #ff0000; }}
        .high {{ border-left: 4px solid #ff6600; }}
        .medium {{ border-left: 4px solid #ffcc00; }}
        .low {{ border-left: 4px solid #00cc00; }}
        .images {{ display: flex; gap: 20px; margin: 20px 0; }}
        .image-container {{ text-align: center; }}
        .image-container img {{ max-width: 400px; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Visual Diff Report</h1>
        <div class="metric">
            <div class="metric-value {'passed' if comparison_result.similarity_score >= 0.95 else 'failed'}">
                {comparison_result.similarity_score:.2%}
            </div>
            <div>Similarity Score</div>
        </div>
        <div class="metric">
            <div class="metric-value">{comparison_result.pixel_diff_percentage:.2f}%</div>
            <div>Pixel Difference</div>
        </div>
        <div class="metric">
            <div class="metric-value {'passed' if not comparison_result.has_issues else 'failed'}">
                {'PASS' if not comparison_result.has_issues else 'FAIL'}
            </div>
            <div>Status</div>
        </div>
    </div>
    
    <h2>Discrepancies ({len(comparison_result.discrepancies)})</h2>
"""
        
        for disc in comparison_result.discrepancies:
            severity_class = disc.severity.value
            html += f"""
    <div class="discrepancy {severity_class}">
        <h3>{disc.type.value.replace('_', ' ').title()}</h3>
        <p><strong>Severity:</strong> {disc.severity.value}</p>
        <p><strong>Message:</strong> {disc.message}</p>
        {f'<p><strong>Expected:</strong> {disc.expected_value}</p>' if disc.expected_value else ''}
        {f'<p><strong>Actual:</strong> {disc.actual_value}</p>' if disc.actual_value else ''}
        {f'<p><strong>Suggestion:</strong> {disc.suggestion}</p>' if disc.suggestion else ''}
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(html)
        
        return html
    
    def save_comparison_images(self, comparison_result: ComparisonResult,
                               output_dir: str, prefix: str = "comparison"):
        """
        Save comparison images to directory.
        
        Args:
            comparison_result: Comparison result
            output_dir: Output directory
            prefix: File prefix
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if comparison_result.diff_image is not None:
            diff_path = output_path / f"{prefix}_diff.png"
            cv2.imwrite(str(diff_path), 
                       cv2.cvtColor(comparison_result.diff_image, cv2.COLOR_RGB2BGR))
            logger.info(f"Saved diff image to {diff_path}")
        
        if comparison_result.annotated_image is not None:
            annotated_path = output_path / f"{prefix}_annotated.png"
            cv2.imwrite(str(annotated_path),
                       cv2.cvtColor(comparison_result.annotated_image, cv2.COLOR_RGB2BGR))
            logger.info(f"Saved annotated image to {annotated_path}")


class RegressionDetector:
    """Detect visual regressions over time."""
    
    def __init__(self, baseline_dir: str):
        """
        Initialize regression detector.
        
        Args:
            baseline_dir: Directory containing baseline screenshots
        """
        self.baseline_dir = Path(baseline_dir)
        self.comparator = ImageComparator()
        
    def check_regression(self, test_name: str, 
                         current_screenshot: Union[str, Path, np.ndarray]) -> ComparisonResult:
        """
        Check for regression against baseline.
        
        Args:
            test_name: Name of the test/baseline
            current_screenshot: Current screenshot
            
        Returns:
            ComparisonResult
        """
        baseline_path = self.baseline_dir / f"{test_name}.png"
        
        if not baseline_path.exists():
            logger.warning(f"No baseline found for {test_name}, saving current as baseline")
            self._save_baseline(test_name, current_screenshot)
            return ComparisonResult(
                similarity_score=1.0,
                pixel_diff_percentage=0,
                discrepancies=[],
                metadata={"status": "new_baseline"}
            )
        
        return self.comparator.compare(baseline_path, current_screenshot)
    
    def _save_baseline(self, test_name: str, 
                       screenshot: Union[str, Path, np.ndarray]):
        """Save new baseline screenshot."""
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        
        if isinstance(screenshot, (str, Path)):
            img = cv2.imread(str(screenshot))
        else:
            img = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        
        baseline_path = self.baseline_dir / f"{test_name}.png"
        cv2.imwrite(str(baseline_path), img)
        logger.info(f"Saved baseline to {baseline_path}")
    
    def update_baseline(self, test_name: str, 
                        new_screenshot: Union[str, Path, np.ndarray]):
        """Update baseline screenshot."""
        self._save_baseline(test_name, new_screenshot)


# Export main classes
__all__ = [
    'VisualDebugger',
    'ImageComparator',
    'ElementComparator',
    'RegressionDetector',
    'ComparisonResult',
    'Discrepancy',
    'ElementMatch',
    'DiscrepancyType',
    'Severity'
]
