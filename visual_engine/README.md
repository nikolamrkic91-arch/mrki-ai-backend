# Mrki Visual Engine

Visual-to-Code and Video-to-Code engine for automated UI generation.

## Features

- **Image/Video Analysis**: Extract UI elements, colors, typography from screenshots
- **Sketch-to-Code**: Convert hand-drawn sketches to structured code
- **Multi-Framework Support**: Generate React, Vue, Angular, Svelte code
- **Tailwind CSS**: First-class support for Tailwind CSS styling
- **Visual Debugging**: Compare screenshots and detect discrepancies
- **Design System Extraction**: Extract colors, typography, spacing from designs
- **Figma/Sketch Import**: Import from design tools (planned)

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Analyze an Image

```python
from visual_engine import ImageAnalyzer

analyzer = ImageAnalyzer()
result = analyzer.analyze_image("screenshot.png")

print(f"Found {len(result.elements)} elements")
print(f"Primary color: {result.colors.primary}")
print(f"Layout: {result.layout.value}")
```

### Generate Code

```python
from visual_engine import CodeGenerator, Framework, StyleSystem

generator = CodeGenerator()
code = generator.generate_from_analysis(
    result.to_dict(),
    framework=Framework.REACT,
    style_system=StyleSystem.TAILWIND,
    component_name="MyComponent"
)

print(code.template_code)
```

### Process a Sketch

```python
from visual_engine import SketchAnalyzer

sketch_analyzer = SketchAnalyzer()
analysis = sketch_analyzer.analyze("sketch.png")

print(f"Found {len(analysis.shapes)} shapes")
print(f"Detected style: {analysis.style.value}")
```

### Compare Screenshots

```python
from visual_engine import VisualDebugger

debugger = VisualDebugger()
report = debugger.debug_screenshot(
    expected_image="design.png",
    actual_image="screenshot.png"
)

print(f"Similarity: {report['summary']['similarity_score']:.2%}")
print(f"Issues: {report['summary']['total_discrepancies']}")
```

## API Server

Start the FastAPI server:

```bash
python api.py
```

Or with uvicorn:

```bash
uvicorn api:app --reload
```

### API Endpoints

- `POST /analyze/image` - Analyze an image
- `POST /analyze/sketch` - Analyze a sketch
- `POST /analyze/video` - Analyze a video
- `POST /generate/code` - Generate code from analysis
- `POST /generate/sketch-to-code` - Convert sketch to code
- `POST /compare/images` - Compare two images
- `POST /extract/design-system` - Extract design system
- `POST /debug/screenshot` - Debug screenshot

## Project Structure

```
visual_engine/
├── __init__.py           # Package initialization
├── analyzer.py           # Image/video analysis
├── sketch_processor.py   # Sketch recognition
├── code_generator.py     # Code generation
├── visual_debugger.py    # Screenshot comparison
├── design_extractor.py   # Design system extraction
├── api.py                # FastAPI endpoints
├── config.py             # Configuration
├── requirements.txt      # Dependencies
└── templates/            # Code templates
    ├── react/
    ├── vue/
    ├── angular/
    ├── svelte/
    └── shared/
```

## Supported Frameworks

- **React** (JSX/TSX)
- **Vue** (Single File Components)
- **Angular** (Components)
- **Svelte** (Svelte Components)

## Supported Style Systems

- **Tailwind CSS** (default)
- **CSS Modules**
- **Styled Components**
- **SCSS**
- **Plain CSS**

## Configuration

Set environment variables:

```bash
export MRKI_VISION_MODEL=default
export MRKI_DEFAULT_FRAMEWORK=react
export MRKI_DEFAULT_STYLE_SYSTEM=tailwind
export MRKI_API_HOST=0.0.0.0
export MRKI_API_PORT=8000
```

## License

MIT License
