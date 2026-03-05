"""
Mrki Visual Engine - Tests
===========================
Unit tests for visual engine components.
"""

import unittest
import numpy as np
from pathlib import Path

# Import components to test
from analyzer import ImageAnalyzer, VideoAnalyzer, BoundingBox, UIElement, UIElementType
from sketch_processor import SketchAnalyzer, SketchShape, ShapeType
from code_generator import CodeGenerator, Framework, StyleSystem, ComponentSpec
from visual_debugger import VisualDebugger, ImageComparator, DiscrepancyType
from design_extractor import DesignExtractor, ColorToken, DesignSystem


class TestBoundingBox(unittest.TestCase):
    """Test BoundingBox class."""
    
    def test_center_calculation(self):
        bbox = BoundingBox(x=10, y=20, width=100, height=50)
        self.assertEqual(bbox.center, (60, 45))
    
    def test_area_calculation(self):
        bbox = BoundingBox(x=0, y=0, width=100, height=50)
        self.assertEqual(bbox.area, 5000)
    
    def test_contains(self):
        outer = BoundingBox(x=0, y=0, width=100, height=100)
        inner = BoundingBox(x=10, y=10, width=50, height=50)
        self.assertTrue(outer.contains(inner))
        self.assertFalse(inner.contains(outer))


class TestUIElement(unittest.TestCase):
    """Test UIElement class."""
    
    def test_element_creation(self):
        bbox = BoundingBox(x=10, y=20, width=100, height=50)
        element = UIElement(
            id="test_1",
            type=UIElementType.BUTTON,
            bbox=bbox,
            text="Click Me",
            confidence=0.95
        )
        
        self.assertEqual(element.id, "test_1")
        self.assertEqual(element.type, UIElementType.BUTTON)
        self.assertEqual(element.text, "Click Me")
        self.assertEqual(element.confidence, 0.95)
    
    def test_element_to_dict(self):
        bbox = BoundingBox(x=0, y=0, width=100, height=50)
        element = UIElement(
            id="test_1",
            type=UIElementType.BUTTON,
            bbox=bbox
        )
        
        d = element.to_dict()
        self.assertEqual(d["id"], "test_1")
        self.assertEqual(d["type"], "button")
        self.assertIn("bbox", d)


class TestColorToken(unittest.TestCase):
    """Test ColorToken class."""
    
    def test_color_creation(self):
        color = ColorToken(
            name="primary",
            hex_value="#3b82f6",
            rgb=(59, 130, 246)
        )
        
        self.assertEqual(color.name, "primary")
        self.assertEqual(color.hex_value, "#3b82f6")
        self.assertEqual(color.rgb, (59, 130, 246))
    
    def test_hsl_conversion(self):
        color = ColorToken(
            name="red",
            hex_value="#ff0000",
            rgb=(255, 0, 0)
        )
        
        hsl = color.hsl
        self.assertAlmostEqual(hsl[0], 0, delta=1)  # Hue should be 0 (red)
        self.assertAlmostEqual(hsl[1], 100, delta=1)  # Saturation should be 100%


class TestDesignSystem(unittest.TestCase):
    """Test DesignSystem class."""
    
    def test_design_system_creation(self):
        colors = [
            ColorToken(name="primary", hex_value="#3b82f6", rgb=(59, 130, 246)),
            ColorToken(name="secondary", hex_value="#6b7280", rgb=(107, 114, 128))
        ]
        
        design = DesignSystem(
            name="Test Design",
            colors=colors,
            typography=[],
            spacing=[],
            shadows=[],
            components=[]
        )
        
        self.assertEqual(design.name, "Test Design")
        self.assertEqual(len(design.colors), 2)
    
    def test_to_tailwind_config(self):
        colors = [
            ColorToken(name="primary", hex_value="#3b82f6", rgb=(59, 130, 246))
        ]
        
        design = DesignSystem(
            name="Test",
            colors=colors,
            typography=[],
            spacing=[],
            shadows=[],
            components=[]
        )
        
        config = design.to_tailwind_config()
        self.assertIn("theme", config)
        self.assertIn("extend", config["theme"])
        self.assertIn("colors", config["theme"]["extend"])
        self.assertEqual(config["theme"]["extend"]["colors"]["primary"], "#3b82f6")


class TestComponentSpec(unittest.TestCase):
    """Test ComponentSpec class."""
    
    def test_spec_creation(self):
        spec = ComponentSpec(
            name="Button",
            element_type="button",
            props=[{"name": "variant", "type": "string"}],
            styles={"backgroundColor": "#3b82f6"}
        )
        
        self.assertEqual(spec.name, "Button")
        self.assertEqual(spec.element_type, "button")
        self.assertEqual(len(spec.props), 1)


class TestStyleGenerator(unittest.TestCase):
    """Test StyleGenerator class."""
    
    def test_tailwind_generation(self):
        from code_generator import StyleGenerator
        
        generator = StyleGenerator()
        styles = {
            "display": "flex",
            "flexDirection": "column",
            "padding": 16,
            "backgroundColor": "#3b82f6"
        }
        
        classes = generator.generate_tailwind(styles)
        self.assertIn("flex", classes)
        self.assertIn("flex-col", classes)


class TestImageComparator(unittest.TestCase):
    """Test ImageComparator class."""
    
    def test_identical_images(self):
        comparator = ImageComparator()
        
        # Create two identical images
        img1 = np.ones((100, 100, 3), dtype=np.uint8) * 128
        img2 = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        result = comparator.compare(img1, img2)
        
        self.assertAlmostEqual(result.similarity_score, 1.0, delta=0.01)
        self.assertEqual(result.pixel_diff_percentage, 0.0)
        self.assertFalse(result.has_issues)
    
    def test_different_images(self):
        comparator = ImageComparator()
        
        # Create two different images
        img1 = np.ones((100, 100, 3), dtype=np.uint8) * 0
        img2 = np.ones((100, 100, 3), dtype=np.uint8) * 255
        
        result = comparator.compare(img1, img2)
        
        self.assertLess(result.similarity_score, 0.5)
        self.assertTrue(result.has_issues)


class TestSketchShape(unittest.TestCase):
    """Test SketchShape class."""
    
    def test_shape_creation(self):
        shape = SketchShape(
            id="shape_1",
            shape_type=ShapeType.RECTANGLE,
            points=[(0, 0), (100, 0), (100, 50), (0, 50)],
            bbox=(0, 0, 100, 50),
            confidence=0.9
        )
        
        self.assertEqual(shape.id, "shape_1")
        self.assertEqual(shape.shape_type, ShapeType.RECTANGLE)
        self.assertEqual(shape.confidence, 0.9)


class TestCodeGeneration(unittest.TestCase):
    """Test code generation."""
    
    def test_react_generation(self):
        from code_generator import ReactGenerator, StyleGenerator
        
        style_gen = StyleGenerator()
        generator = ReactGenerator(style_gen)
        
        spec = ComponentSpec(
            name="TestButton",
            element_type="button",
            props=[{"name": "children", "type": "ReactNode"}],
            styles={"backgroundColor": "#3b82f6"}
        )
        
        result = generator.generate(spec, StyleSystem.TAILWIND)
        
        self.assertEqual(result.framework.value, "react")
        self.assertIn("TestButton", result.template_code)
        self.assertIn("import React", result.template_code)


class TestEnums(unittest.TestCase):
    """Test enum classes."""
    
    def test_ui_element_types(self):
        self.assertEqual(UIElementType.BUTTON.value, "button")
        self.assertEqual(UIElementType.INPUT.value, "input")
        self.assertEqual(UIElementType.TEXT.value, "text")
    
    def test_shape_types(self):
        self.assertEqual(ShapeType.RECTANGLE.value, "rectangle")
        self.assertEqual(ShapeType.CIRCLE.value, "circle")
    
    def test_frameworks(self):
        self.assertEqual(Framework.REACT.value, "react")
        self.assertEqual(Framework.VUE.value, "vue")
        self.assertEqual(Framework.ANGULAR.value, "angular")
        self.assertEqual(Framework.SVELTE.value, "svelte")


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBoundingBox))
    suite.addTests(loader.loadTestsFromTestCase(TestUIElement))
    suite.addTests(loader.loadTestsFromTestCase(TestColorToken))
    suite.addTests(loader.loadTestsFromTestCase(TestDesignSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestComponentSpec))
    suite.addTests(loader.loadTestsFromTestCase(TestStyleGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestImageComparator))
    suite.addTests(loader.loadTestsFromTestCase(TestSketchShape))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestEnums))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
