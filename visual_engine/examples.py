"""
Mrki Visual Engine - Examples
==============================
Example usage of the visual engine components.
"""

import os
from pathlib import Path

# Import visual engine components
from analyzer import ImageAnalyzer, VideoAnalyzer
from sketch_processor import SketchAnalyzer, WireframeConverter
from code_generator import CodeGenerator, Framework, StyleSystem
from visual_debugger import VisualDebugger, ImageComparator
from design_extractor import DesignExtractor


def example_image_analysis():
    """Example: Analyze an image and extract UI elements."""
    print("=" * 60)
    print("Example: Image Analysis")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = ImageAnalyzer()
    
    # Analyze image (replace with your image path)
    image_path = "path/to/your/screenshot.png"
    
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        print("Skipping example - please provide a valid image path")
        return
    
    result = analyzer.analyze_image(image_path)
    
    # Print results
    print(f"\nAnalysis Results:")
    print(f"  Dimensions: {result.dimensions}")
    print(f"  Layout Type: {result.layout.value}")
    print(f"  Elements Found: {len(result.elements)}")
    
    print(f"\nColors:")
    print(f"  Primary: {result.colors.primary}")
    print(f"  Secondary: {result.colors.secondary}")
    print(f"  Background: {result.colors.background}")
    print(f"  Text: {result.colors.text}")
    
    print(f"\nTypography:")
    print(f"  Font Sizes: {result.typography.get('sizes', [])}")
    print(f"  Line Heights: {result.typography.get('line_heights', [])}")
    
    print(f"\nTop-level Elements:")
    for i, elem in enumerate(result.elements[:5]):
        print(f"  {i+1}. {elem.type.value} at ({elem.bbox.x}, {elem.bbox.y})")
        if elem.children:
            print(f"      Children: {len(elem.children)}")


def example_sketch_analysis():
    """Example: Analyze a hand-drawn sketch."""
    print("\n" + "=" * 60)
    print("Example: Sketch Analysis")
    print("=" * 60)
    
    # Initialize sketch analyzer
    analyzer = SketchAnalyzer()
    
    # Analyze sketch (replace with your sketch path)
    sketch_path = "path/to/your/sketch.png"
    
    if not os.path.exists(sketch_path):
        print(f"Sketch not found: {sketch_path}")
        print("Skipping example - please provide a valid sketch path")
        return
    
    result = analyzer.analyze(sketch_path)
    
    # Print results
    print(f"\nSketch Analysis Results:")
    print(f"  Style: {result.style.value}")
    print(f"  Dimensions: {result.dimensions}")
    print(f"  Shapes Found: {len(result.shapes)}")
    print(f"  Elements Found: {len(result.elements)}")
    print(f"  Connections: {len(result.connections)}")
    
    print(f"\nDetected Shapes:")
    for i, shape in enumerate(result.shapes[:10]):
        print(f"  {i+1}. {shape.shape_type.value} (confidence: {shape.confidence:.2f})")
    
    print(f"\nUI Elements:")
    for i, elem in enumerate(result.elements[:5]):
        print(f"  {i+1}. {elem.element_type} - {elem.label}")
        print(f"      Position: ({elem.bbox[0]}, {elem.bbox[1]})")
        print(f"      Size: {elem.bbox[2]}x{elem.bbox[3]}")


def example_code_generation():
    """Example: Generate code from analysis."""
    print("\n" + "=" * 60)
    print("Example: Code Generation")
    print("=" * 60)
    
    # Initialize code generator
    generator = CodeGenerator()
    
    # Create a sample analysis result
    sample_analysis = {
        "elements": [
            {
                "id": "elem_1",
                "type": "button",
                "bbox": {"x": 100, "y": 100, "width": 120, "height": 40},
                "text": "Click Me",
                "styles": {
                    "backgroundColor": "#3b82f6",
                    "color": "#ffffff",
                    "borderRadius": "8px",
                    "padding": "10px 20px"
                }
            },
            {
                "id": "elem_2",
                "type": "input",
                "bbox": {"x": 100, "y": 160, "width": 300, "height": 40},
                "styles": {
                    "border": "1px solid #d1d5db",
                    "borderRadius": "4px",
                    "padding": "8px 12px"
                }
            }
        ],
        "colors": {
            "primary": "#3b82f6",
            "secondary": "#6b7280",
            "background": "#ffffff",
            "text": "#111827"
        },
        "layout": "flex_column",
        "typography": {
            "sizes": [14, 16, 18],
            "line_heights": [1.5]
        }
    }
    
    # Generate code for different frameworks
    frameworks = [
        (Framework.REACT, "React"),
        (Framework.VUE, "Vue"),
        (Framework.ANGULAR, "Angular"),
        (Framework.SVELTE, "Svelte")
    ]
    
    for framework, name in frameworks:
        print(f"\n{name} Code:")
        print("-" * 40)
        
        result = generator.generate_from_analysis(
            sample_analysis,
            framework=framework,
            style_system=StyleSystem.TAILWIND,
            component_name="SampleComponent"
        )
        
        # Print first 500 characters of template code
        code_preview = result.template_code[:500]
        print(code_preview)
        if len(result.template_code) > 500:
            print("... (truncated)")


def example_visual_debugging():
    """Example: Compare images and detect discrepancies."""
    print("\n" + "=" * 60)
    print("Example: Visual Debugging")
    print("=" * 60)
    
    # Initialize debugger
    debugger = VisualDebugger()
    
    # Compare images (replace with your image paths)
    expected_path = "path/to/expected.png"
    actual_path = "path/to/actual.png"
    
    if not os.path.exists(expected_path) or not os.path.exists(actual_path):
        print("Images not found")
        print("Skipping example - please provide valid image paths")
        return
    
    report = debugger.debug_screenshot(expected_path, actual_path)
    
    # Print results
    summary = report["summary"]
    print(f"\nComparison Results:")
    print(f"  Similarity Score: {summary['similarity_score']:.2%}")
    print(f"  Pixel Difference: {summary['pixel_diff_percentage']:.2f}%")
    print(f"  Total Discrepancies: {summary['total_discrepancies']}")
    print(f"  Critical Issues: {summary['critical_issues']}")
    print(f"  High Issues: {summary['high_issues']}")
    print(f"  Passed: {summary['passed']}")
    
    if report["discrepancies"]:
        print(f"\nDiscrepancies:")
        for i, disc in enumerate(report["discrepancies"][:5]):
            print(f"  {i+1}. [{disc['severity']}] {disc['type']}")
            print(f"      {disc['message']}")
            if disc.get('suggestion'):
                print(f"      Suggestion: {disc['suggestion']}")


def example_design_extraction():
    """Example: Extract design system from image."""
    print("\n" + "=" * 60)
    print("Example: Design System Extraction")
    print("=" * 60)
    
    # Initialize design extractor
    extractor = DesignExtractor()
    
    # Extract from image (replace with your image path)
    image_path = "path/to/design.png"
    
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        print("Skipping example - please provide a valid image path")
        return
    
    design_system = extractor.extract_from_image(image_path, "My Design System")
    
    # Print results
    print(f"\nDesign System: {design_system.name}")
    
    print(f"\nColors ({len(design_system.colors)}):")
    for color in design_system.colors[:10]:
        print(f"  {color.name}: {color.hex_value} (RGB{color.rgb})")
    
    print(f"\nTypography ({len(design_system.typography)}):")
    for typo in design_system.typography[:5]:
        print(f"  {typo.name}: {typo.font_size}px, weight {typo.font_weight}")
    
    print(f"\nSpacing ({len(design_system.spacing)}):")
    for space in design_system.spacing[:5]:
        print(f"  {space.name}: {space.value}px")
    
    print(f"\nBorder Radius: {design_system.border_radius}")
    
    print(f"\nBreakpoints:")
    for name, value in design_system.breakpoints.items():
        print(f"  {name}: {value}px")
    
    # Show CSS variables
    print(f"\nCSS Variables Preview:")
    css_lines = design_system.to_css_variables().split('\n')[:15]
    for line in css_lines:
        print(f"  {line}")


def example_video_analysis():
    """Example: Analyze a video for UI behaviors."""
    print("\n" + "=" * 60)
    print("Example: Video Analysis")
    print("=" * 60)
    
    # Initialize video analyzer
    analyzer = VideoAnalyzer(frame_interval=30)
    
    # Analyze video (replace with your video path)
    video_path = "path/to/video.mp4"
    
    if not os.path.exists(video_path):
        print(f"Video not found: {video_path}")
        print("Skipping example - please provide a valid video path")
        return
    
    result = analyzer.analyze_video(video_path)
    
    # Print results
    video_info = result["video_info"]
    print(f"\nVideo Information:")
    print(f"  FPS: {video_info['fps']}")
    print(f"  Total Frames: {video_info['total_frames']}")
    print(f"  Duration: {video_info['duration']:.2f}s")
    print(f"  Frames Analyzed: {video_info['frames_analyzed']}")
    
    print(f"\nDetected Behaviors ({len(result['behaviors'])}):")
    for i, behavior in enumerate(result["behaviors"][:10]):
        print(f"  {i+1}. {behavior['type']} at {behavior['timestamp']:.2f}s")
        if behavior.get('elements'):
            print(f"      Elements: {len(behavior['elements'])}")


def example_wireframe_conversion():
    """Example: Convert sketch to wireframe."""
    print("\n" + "=" * 60)
    print("Example: Wireframe Conversion")
    print("=" * 60)
    
    # Initialize wireframe converter
    converter = WireframeConverter()
    
    # Convert sketch (replace with your sketch path)
    sketch_path = "path/to/sketch.png"
    
    if not os.path.exists(sketch_path):
        print(f"Sketch not found: {sketch_path}")
        print("Skipping example - please provide a valid sketch path")
        return
    
    # Convert to wireframe
    wireframe = converter.convert_to_wireframe(sketch_path)
    
    print(f"\nWireframe generated!")
    print(f"  Shape: {wireframe.shape}")
    
    # Save wireframe
    output_path = "output_wireframe.png"
    from PIL import Image
    Image.fromarray(wireframe).save(output_path)
    print(f"  Saved to: {output_path}")


def run_all_examples():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Mrki Visual Engine - Examples")
    print("=" * 60)
    
    example_image_analysis()
    example_sketch_analysis()
    example_code_generation()
    example_visual_debugging()
    example_design_extraction()
    example_video_analysis()
    example_wireframe_conversion()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_examples()
