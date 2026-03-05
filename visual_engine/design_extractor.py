"""
Mrki Visual Engine - Design Extractor
======================================
Extract design systems from images, Figma files, and Sketch files.
Extracts colors, typography, components, and spacing systems.
"""

import cv2
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import logging
from collections import Counter
import colorsys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ColorToken:
    """A color token in the design system."""
    name: str
    hex_value: str
    rgb: Tuple[int, int, int]
    usage_count: int = 0
    contexts: List[str] = field(default_factory=list)
    
    @property
    def hsl(self) -> Tuple[float, float, float]:
        """Convert RGB to HSL."""
        r, g, b = self.rgb[0] / 255.0, self.rgb[1] / 255.0, self.rgb[2] / 255.0
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        return (h * 360, s * 100, l * 100)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "hex": self.hex_value,
            "rgb": self.rgb,
            "hsl": self.hsl,
            "usage_count": self.usage_count,
            "contexts": self.contexts
        }


@dataclass
class TypographyToken:
    """A typography token in the design system."""
    name: str
    font_family: str
    font_size: int
    font_weight: int
    line_height: float
    letter_spacing: Optional[float] = None
    usage_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "font_family": self.font_family,
            "font_size": f"{self.font_size}px",
            "font_weight": self.font_weight,
            "line_height": self.line_height,
            "letter_spacing": self.letter_spacing,
            "usage_count": self.usage_count
        }


@dataclass
class SpacingToken:
    """A spacing token in the design system."""
    name: str
    value: int
    unit: str = "px"
    usage_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "usage_count": self.usage_count
        }


@dataclass
class ShadowToken:
    """A shadow token in the design system."""
    name: str
    x_offset: int
    y_offset: int
    blur_radius: int
    spread_radius: int
    color: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": f"{self.x_offset}px {self.y_offset}px {self.blur_radius}px {self.spread_radius}px {self.color}"
        }


@dataclass
class ComponentPattern:
    """A reusable component pattern."""
    name: str
    element_type: str
    styles: Dict[str, Any]
    variants: List[Dict[str, Any]] = field(default_factory=list)
    usage_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "element_type": self.element_type,
            "styles": self.styles,
            "variants": self.variants,
            "usage_count": self.usage_count
        }


@dataclass
class DesignSystem:
    """Complete extracted design system."""
    name: str
    colors: List[ColorToken]
    typography: List[TypographyToken]
    spacing: List[SpacingToken]
    shadows: List[ShadowToken]
    components: List[ComponentPattern]
    border_radius: List[int] = field(default_factory=list)
    breakpoints: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "colors": [c.to_dict() for c in self.colors],
            "typography": [t.to_dict() for t in self.typography],
            "spacing": [s.to_dict() for s in self.spacing],
            "shadows": [s.to_dict() for s in self.shadows],
            "components": [c.to_dict() for c in self.components],
            "border_radius": self.border_radius,
            "breakpoints": self.breakpoints,
            "metadata": self.metadata
        }
    
    def to_tailwind_config(self) -> Dict[str, Any]:
        """Convert design system to Tailwind CSS config format."""
        return {
            "theme": {
                "extend": {
                    "colors": {c.name: c.hex_value for c in self.colors},
                    "fontFamily": {t.name: [t.font_family] for t in self.typography},
                    "fontSize": {t.name: f"{t.font_size}px" for t in self.typography},
                    "spacing": {s.name: f"{s.value}px" for s in self.spacing},
                    "borderRadius": {f"radius-{r}": f"{r}px" for r in self.border_radius},
                    "boxShadow": {s.name: s.to_dict()["value"] for s in self.shadows}
                }
            }
        }
    
    def to_css_variables(self) -> str:
        """Convert design system to CSS variables."""
        lines = [":root {"]
        
        # Colors
        for color in self.colors:
            lines.append(f"  --color-{color.name}: {color.hex_value};")
        
        # Typography
        for typo in self.typography:
            lines.append(f"  --font-{typo.name}: '{typo.font_family}';")
            lines.append(f"  --text-{typo.name}: {typo.font_size}px;")
        
        # Spacing
        for space in self.spacing:
            lines.append(f"  --space-{space.name}: {space.value}px;")
        
        # Shadows
        for shadow in self.shadows:
            lines.append(f"  --shadow-{shadow.name}: {shadow.to_dict()['value']};")
        
        lines.append("}")
        
        return "\n".join(lines)


class ColorExtractor:
    """Extract color palette from images."""
    
    def __init__(self, num_colors: int = 10, min_frequency: float = 0.01):
        """
        Initialize color extractor.
        
        Args:
            num_colors: Number of dominant colors to extract
            min_frequency: Minimum frequency for a color to be included
        """
        self.num_colors = num_colors
        self.min_frequency = min_frequency
    
    def extract(self, image: np.ndarray) -> List[ColorToken]:
        """
        Extract color palette from image.
        
        Args:
            image: Input image
            
        Returns:
            List of ColorToken objects
        """
        # Reshape for k-means
        pixels = image.reshape(-1, 3)
        pixels = np.float32(pixels)
        
        # K-means clustering
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(pixels, self.num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Count color frequencies
        counts = Counter(labels.flatten())
        total_pixels = len(labels)
        
        colors = []
        for i, center in enumerate(centers):
            frequency = counts[i] / total_pixels
            
            if frequency >= self.min_frequency:
                r, g, b = int(center[0]), int(center[1]), int(center[2])
                hex_value = f"#{r:02x}{g:02x}{b:02x}"
                
                # Determine color name based on usage
                name = self._name_color(r, g, b, frequency)
                
                colors.append(ColorToken(
                    name=name,
                    hex_value=hex_value,
                    rgb=(r, g, b),
                    usage_count=counts[i]
                ))
        
        # Sort by usage
        colors.sort(key=lambda c: c.usage_count, reverse=True)
        
        return colors
    
    def _name_color(self, r: int, g: int, b: int, frequency: float) -> str:
        """Generate a semantic name for a color."""
        # Convert to HSL for better naming
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        
        # Determine if it's grayscale
        if s < 0.1:
            if l < 0.1:
                return "black"
            elif l > 0.9:
                return "white"
            elif l < 0.3:
                return "gray-900"
            elif l < 0.5:
                return "gray-700"
            elif l < 0.7:
                return "gray-500"
            else:
                return "gray-300"
        
        # Determine hue
        hue_names = [
            (15, "red"), (45, "orange"), (75, "yellow"),
            (150, "green"), (195, "cyan"), (255, "blue"),
            (285, "purple"), (330, "pink"), (360, "red")
        ]
        
        hue_name = "neutral"
        for max_hue, name in hue_names:
            if h * 360 <= max_hue:
                hue_name = name
                break
        
        # Determine lightness variant
        if l < 0.3:
            return f"{hue_name}-900"
        elif l < 0.5:
            return f"{hue_name}-700"
        elif l < 0.7:
            return f"{hue_name}-500"
        else:
            return f"{hue_name}-300"
    
    def extract_contextual_colors(self, image: np.ndarray, 
                                   elements: List[Dict[str, Any]]) -> List[ColorToken]:
        """Extract colors with context information from elements."""
        colors = self.extract(image)
        
        # Analyze element contexts
        for color in colors:
            for element in elements:
                elem_color = element.get("styles", {}).get("backgroundColor", "")
                if elem_color and self._colors_similar(color.hex_value, elem_color):
                    color.contexts.append(element.get("type", "unknown"))
        
        return colors
    
    def _colors_similar(self, hex1: str, hex2: str, threshold: int = 30) -> bool:
        """Check if two hex colors are similar."""
        rgb1 = tuple(int(hex1[i:i+2], 16) for i in (1, 3, 5))
        rgb2 = tuple(int(hex2[i:i+2], 16) for i in (1, 3, 5))
        
        distance = np.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))
        return distance < threshold


class TypographyExtractor:
    """Extract typography system from images."""
    
    def __init__(self):
        self.font_size_tolerance = 2
        self.common_font_sizes = [12, 14, 16, 18, 20, 24, 28, 32, 36, 40, 48, 56, 64]
        self.common_font_weights = [400, 500, 600, 700]
    
    def extract(self, image: np.ndarray, 
                text_regions: List[Dict[str, Any]]) -> List[TypographyToken]:
        """
        Extract typography system from text regions.
        
        Args:
            image: Input image
            text_regions: Detected text regions with bounding boxes
            
        Returns:
            List of TypographyToken objects
        """
        typography = []
        
        # Group text by size
        size_groups = {}
        for region in text_regions:
            height = region.get("bbox", {}).get("height", 16)
            font_size = self._estimate_font_size(height)
            
            if font_size not in size_groups:
                size_groups[font_size] = []
            size_groups[font_size].append(region)
        
        # Create tokens for each size group
        for font_size, regions in size_groups.items():
            # Estimate font weight from thickness
            avg_weight = self._estimate_font_weight(image, regions)
            
            # Generate name
            name = self._name_typography(font_size, avg_weight)
            
            typography.append(TypographyToken(
                name=name,
                font_family="system-ui, -apple-system, sans-serif",
                font_size=font_size,
                font_weight=avg_weight,
                line_height=self._estimate_line_height(font_size),
                usage_count=len(regions)
            ))
        
        # Sort by font size
        typography.sort(key=lambda t: t.font_size)
        
        return typography
    
    def _estimate_font_size(self, height: int) -> int:
        """Estimate font size from text height."""
        # Find closest common font size
        closest = min(self.common_font_sizes, key=lambda x: abs(x - height))
        return closest
    
    def _estimate_font_weight(self, image: np.ndarray, 
                               regions: List[Dict[str, Any]]) -> int:
        """Estimate font weight from text thickness."""
        # Default to regular
        return 400
    
    def _estimate_line_height(self, font_size: int) -> float:
        """Estimate line height from font size."""
        # Common line height is 1.2-1.6 times font size
        return round(1.5 * font_size / font_size, 2)
    
    def _name_typography(self, font_size: int, weight: int) -> str:
        """Generate semantic name for typography."""
        if font_size >= 48:
            return "display"
        elif font_size >= 32:
            return "h1"
        elif font_size >= 28:
            return "h2"
        elif font_size >= 24:
            return "h3"
        elif font_size >= 20:
            return "h4"
        elif font_size >= 18:
            return "h5"
        elif font_size >= 16:
            return "body"
        elif font_size >= 14:
            return "body-small"
        else:
            return "caption"


class SpacingExtractor:
    """Extract spacing system from images."""
    
    def __init__(self, base_unit: int = 4):
        """
        Initialize spacing extractor.
        
        Args:
            base_unit: Base spacing unit (typically 4 or 8)
        """
        self.base_unit = base_unit
        self.spacing_scale = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96]
    
    def extract(self, elements: List[Dict[str, Any]]) -> List[SpacingToken]:
        """
        Extract spacing system from element layout.
        
        Args:
            elements: UI elements with positions
            
        Returns:
            List of SpacingToken objects
        """
        spacings = []
        
        # Calculate gaps between elements
        gaps = self._calculate_gaps(elements)
        
        # Group gaps by size
        gap_groups = {}
        for gap in gaps:
            # Round to nearest base unit
            rounded_gap = round(gap / self.base_unit) * self.base_unit
            
            if rounded_gap not in gap_groups:
                gap_groups[rounded_gap] = 0
            gap_groups[rounded_gap] += 1
        
        # Create tokens for common gaps
        for gap_size, count in sorted(gap_groups.items()):
            if gap_size > 0 and count >= 2:  # At least 2 occurrences
                name = self._name_spacing(gap_size)
                spacings.append(SpacingToken(
                    name=name,
                    value=gap_size,
                    usage_count=count
                ))
        
        # Sort by value
        spacings.sort(key=lambda s: s.value)
        
        return spacings
    
    def _calculate_gaps(self, elements: List[Dict[str, Any]]) -> List[int]:
        """Calculate gaps between elements."""
        gaps = []
        
        # Sort elements by position
        sorted_elements = sorted(elements, key=lambda e: (e.get("bbox", {}).get("y", 0), 
                                                          e.get("bbox", {}).get("x", 0)))
        
        for i, elem1 in enumerate(sorted_elements):
            bbox1 = elem1.get("bbox", {})
            x1, y1, w1, h1 = bbox1.get("x", 0), bbox1.get("y", 0), bbox1.get("width", 0), bbox1.get("height", 0)
            
            for elem2 in sorted_elements[i+1:]:
                bbox2 = elem2.get("bbox", {})
                x2, y2 = bbox2.get("x", 0), bbox2.get("y", 0)
                
                # Horizontal gap
                if abs(y1 - y2) < 10:  # Same row
                    gap = x2 - (x1 + w1)
                    if gap > 0:
                        gaps.append(gap)
                
                # Vertical gap
                if abs(x1 - x2) < 10:  # Same column
                    gap = y2 - (y1 + h1)
                    if gap > 0:
                        gaps.append(gap)
        
        return gaps
    
    def _name_spacing(self, value: int) -> str:
        """Generate semantic name for spacing."""
        scale_names = {
            0: "0",
            4: "1",
            8: "2",
            12: "3",
            16: "4",
            20: "5",
            24: "6",
            32: "8",
            40: "10",
            48: "12",
            64: "16",
            80: "20",
            96: "24"
        }
        
        return scale_names.get(value, f"custom-{value}")


class ComponentExtractor:
    """Extract reusable component patterns from images."""
    
    def __init__(self, similarity_threshold: float = 0.8):
        """
        Initialize component extractor.
        
        Args:
            similarity_threshold: Threshold for considering elements similar
        """
        self.similarity_threshold = similarity_threshold
    
    def extract(self, elements: List[Dict[str, Any]]) -> List[ComponentPattern]:
        """
        Extract component patterns from elements.
        
        Args:
            elements: UI elements
            
        Returns:
            List of ComponentPattern objects
        """
        patterns = []
        grouped = self._group_similar_elements(elements)
        
        for group_name, group_elements in grouped.items():
            if len(group_elements) >= 2:  # At least 2 similar elements
                # Create base pattern
                base_element = group_elements[0]
                
                # Find variants
                variants = []
                for elem in group_elements[1:]:
                    variant = self._extract_variant_diff(base_element, elem)
                    if variant:
                        variants.append(variant)
                
                patterns.append(ComponentPattern(
                    name=group_name,
                    element_type=base_element.get("type", "div"),
                    styles=base_element.get("styles", {}),
                    variants=variants,
                    usage_count=len(group_elements)
                ))
        
        return patterns
    
    def _group_similar_elements(self, elements: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """Group similar elements together."""
        groups = {}
        
        for element in elements:
            elem_type = element.get("type", "unknown")
            styles = element.get("styles", {})
            
            # Create signature from type and key styles
            key_styles = {k: v for k, v in styles.items() 
                         if k in ["backgroundColor", "borderRadius", "padding", "fontSize"]}
            
            signature = f"{elem_type}_{json.dumps(key_styles, sort_keys=True)}"
            
            if signature not in groups:
                groups[signature] = []
            groups[signature].append(element)
        
        # Rename groups with semantic names
        named_groups = {}
        type_counts = {}
        
        for signature, group in groups.items():
            elem_type = group[0].get("type", "unknown")
            
            if elem_type not in type_counts:
                type_counts[elem_type] = 0
            type_counts[elem_type] += 1
            
            name = f"{elem_type}-{type_counts[elem_type]}"
            named_groups[name] = group
        
        return named_groups
    
    def _extract_variant_diff(self, base: Dict[str, Any], 
                               variant: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract differences between base and variant."""
        base_styles = base.get("styles", {})
        variant_styles = variant.get("styles", {})
        
        diff = {}
        for key, value in variant_styles.items():
            if base_styles.get(key) != value:
                diff[key] = value
        
        return diff if diff else None


class DesignExtractor:
    """Main design extraction class."""
    
    def __init__(self):
        self.color_extractor = ColorExtractor()
        self.typography_extractor = TypographyExtractor()
        self.spacing_extractor = SpacingExtractor()
        self.component_extractor = ComponentExtractor()
    
    def extract_from_image(self, image_path: Union[str, Path, np.ndarray],
                           name: str = "Extracted Design System") -> DesignSystem:
        """
        Extract design system from an image.
        
        Args:
            image_path: Path to image or numpy array
            name: Name for the design system
            
        Returns:
            DesignSystem object
        """
        # Load image
        if isinstance(image_path, (str, Path)):
            image = cv2.imread(str(image_path))
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image = image_path
        
        logger.info(f"Extracting design system from image: {image.shape}")
        
        # Extract colors
        colors = self.color_extractor.extract(image)
        logger.info(f"Extracted {len(colors)} colors")
        
        # Extract typography (requires text detection)
        typography = []  # Would need text detection
        
        # Extract spacing (requires element detection)
        spacing = []  # Would need element detection
        
        # Extract components
        components = []  # Would need element detection
        
        # Common border radius values
        border_radius = [0, 4, 8, 12, 16, 24, 32]
        
        # Standard breakpoints
        breakpoints = {
            "sm": 640,
            "md": 768,
            "lg": 1024,
            "xl": 1280,
            "2xl": 1536
        }
        
        return DesignSystem(
            name=name,
            colors=colors,
            typography=typography,
            spacing=spacing,
            shadows=[],
            components=components,
            border_radius=border_radius,
            breakpoints=breakpoints,
            metadata={
                "source": "image",
                "dimensions": image.shape[:2]
            }
        )
    
    def extract_from_analysis(self, analysis: Dict[str, Any],
                               name: str = "Extracted Design System") -> DesignSystem:
        """
        Extract design system from visual analysis result.
        
        Args:
            analysis: Visual analysis result
            name: Name for the design system
            
        Returns:
            DesignSystem object
        """
        elements = analysis.get("elements", [])
        colors_data = analysis.get("colors", {})
        typography_data = analysis.get("typography", {})
        
        # Extract colors from analysis
        colors = []
        for color_name, hex_value in colors_data.items():
            rgb = tuple(int(hex_value[i:i+2], 16) for i in (1, 3, 5))
            colors.append(ColorToken(
                name=color_name,
                hex_value=hex_value,
                rgb=rgb
            ))
        
        # Extract typography
        typography = []
        for size in typography_data.get("sizes", []):
            typography.append(TypographyToken(
                name=f"text-{size}",
                font_family="system-ui",
                font_size=size,
                font_weight=400,
                line_height=1.5
            ))
        
        # Extract spacing from element positions
        spacing = self.spacing_extractor.extract(elements)
        
        # Extract components
        components = self.component_extractor.extract(elements)
        
        return DesignSystem(
            name=name,
            colors=colors,
            typography=typography,
            spacing=spacing,
            shadows=[],
            components=components
        )
    
    def save_design_system(self, design_system: DesignSystem, 
                          output_dir: str):
        """
        Save design system to files.
        
        Args:
            design_system: DesignSystem object
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save as JSON
        json_path = output_path / "design-system.json"
        with open(json_path, 'w') as f:
            json.dump(design_system.to_dict(), f, indent=2)
        logger.info(f"Saved design system JSON to {json_path}")
        
        # Save as CSS variables
        css_path = output_path / "design-system.css"
        with open(css_path, 'w') as f:
            f.write(design_system.to_css_variables())
        logger.info(f"Saved design system CSS to {css_path}")
        
        # Save Tailwind config
        tailwind_path = output_path / "tailwind.config.js"
        with open(tailwind_path, 'w') as f:
            f.write(f"module.exports = {json.dumps(design_system.to_tailwind_config(), indent=2)}")
        logger.info(f"Saved Tailwind config to {tailwind_path}")


class FigmaImporter:
    """Import design systems from Figma files."""
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize Figma importer.
        
        Args:
            api_token: Figma API token
        """
        self.api_token = api_token
    
    def import_from_file(self, file_path: Union[str, Path]) -> DesignSystem:
        """
        Import design system from Figma file.
        
        Args:
            file_path: Path to Figma file
            
        Returns:
            DesignSystem object
        """
        # Note: This is a placeholder for Figma file parsing
        # Actual implementation would require Figma's REST API or file format parsing
        logger.info("Figma import not yet implemented - requires API integration")
        
        return DesignSystem(
            name="Figma Import",
            colors=[],
            typography=[],
            spacing=[],
            shadows=[],
            components=[],
            metadata={"source": "figma", "file": str(file_path)}
        )
    
    def import_from_url(self, file_url: str) -> DesignSystem:
        """Import design system from Figma URL."""
        logger.info("Figma URL import not yet implemented - requires API integration")
        return DesignSystem(
            name="Figma Import",
            colors=[],
            typography=[],
            spacing=[],
            shadows=[],
            components=[],
            metadata={"source": "figma", "url": file_url}
        )


class SketchImporter:
    """Import design systems from Sketch files."""
    
    def import_from_file(self, file_path: Union[str, Path]) -> DesignSystem:
        """
        Import design system from Sketch file.
        
        Args:
            file_path: Path to Sketch file
            
        Returns:
            DesignSystem object
        """
        # Note: This is a placeholder for Sketch file parsing
        # Actual implementation would require Sketch file format parsing
        logger.info("Sketch import not yet implemented - requires file format parser")
        
        return DesignSystem(
            name="Sketch Import",
            colors=[],
            typography=[],
            spacing=[],
            shadows=[],
            components=[],
            metadata={"source": "sketch", "file": str(file_path)}
        )


# Export main classes
__all__ = [
    'DesignExtractor',
    'ColorExtractor',
    'TypographyExtractor',
    'SpacingExtractor',
    'ComponentExtractor',
    'FigmaImporter',
    'SketchImporter',
    'DesignSystem',
    'ColorToken',
    'TypographyToken',
    'SpacingToken',
    'ShadowToken',
    'ComponentPattern'
]
