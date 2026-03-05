"""
Mrki Visual Engine - Code Generator
====================================
Framework-specific code generation from visual analysis.
Supports React, Vue, Angular, Svelte, and Tailwind CSS.
"""

import json
import re
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging
from jinja2 import Environment, FileSystemLoader, BaseLoader, DictLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Framework(Enum):
    """Supported frontend frameworks."""
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    SVELTE = "svelte"


class StyleSystem(Enum):
    """Supported styling systems."""
    TAILWIND = "tailwind"
    CSS_MODULES = "css_modules"
    STYLED_COMPONENTS = "styled_components"
    SCSS = "scss"
    PLAIN_CSS = "plain_css"


@dataclass
class GeneratedCode:
    """Generated code output."""
    framework: Framework
    style_system: StyleSystem
    component_name: str
    template_code: str
    style_code: str = ""
    script_code: str = ""
    test_code: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "framework": self.framework.value,
            "style_system": self.style_system.value,
            "component_name": self.component_name,
            "template_code": self.template_code,
            "style_code": self.style_code,
            "script_code": self.script_code,
            "test_code": self.test_code,
            "metadata": self.metadata
        }


@dataclass
class ComponentSpec:
    """Specification for a UI component."""
    name: str
    element_type: str
    props: List[Dict[str, Any]] = field(default_factory=list)
    styles: Dict[str, Any] = field(default_factory=dict)
    children: List['ComponentSpec'] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "element_type": self.element_type,
            "props": self.props,
            "styles": self.styles,
            "children": [c.to_dict() for c in self.children],
            "events": self.events
        }


class StyleGenerator:
    """Generate styles for different style systems."""
    
    TAILWIND_MAPPINGS = {
        # Layout
        "display_flex": "flex",
        "display_grid": "grid",
        "display_block": "block",
        "display_inline": "inline",
        "display_none": "hidden",
        
        # Flex direction
        "flex_direction_row": "flex-row",
        "flex_direction_column": "flex-col",
        
        # Justify content
        "justify_start": "justify-start",
        "justify_center": "justify-center",
        "justify_end": "justify-end",
        "justify_between": "justify-between",
        "justify_around": "justify-around",
        
        # Align items
        "align_start": "items-start",
        "align_center": "items-center",
        "align_end": "items-end",
        
        # Spacing (padding)
        "padding_0": "p-0",
        "padding_4": "p-1",
        "padding_8": "p-2",
        "padding_12": "p-3",
        "padding_16": "p-4",
        "padding_24": "p-6",
        "padding_32": "p-8",
        
        # Spacing (margin)
        "margin_0": "m-0",
        "margin_4": "m-1",
        "margin_8": "m-2",
        "margin_16": "m-4",
        "margin_24": "m-6",
        
        # Width
        "width_full": "w-full",
        "width_auto": "w-auto",
        "width_screen": "w-screen",
        
        # Height
        "height_full": "h-full",
        "height_auto": "h-auto",
        "height_screen": "h-screen",
        
        # Border radius
        "border_radius_0": "rounded-none",
        "border_radius_4": "rounded",
        "border_radius_8": "rounded-lg",
        "border_radius_16": "rounded-xl",
        "border_radius_full": "rounded-full",
        
        # Shadows
        "shadow_none": "shadow-none",
        "shadow_sm": "shadow-sm",
        "shadow_md": "shadow-md",
        "shadow_lg": "shadow-lg",
        "shadow_xl": "shadow-xl",
        
        # Typography
        "text_xs": "text-xs",
        "text_sm": "text-sm",
        "text_base": "text-base",
        "text_lg": "text-lg",
        "text_xl": "text-xl",
        "text_2xl": "text-2xl",
        "text_3xl": "text-3xl",
        "font_normal": "font-normal",
        "font_medium": "font-medium",
        "font_semibold": "font-semibold",
        "font_bold": "font-bold",
        
        # Colors (text)
        "text_primary": "text-gray-900",
        "text_secondary": "text-gray-600",
        "text_white": "text-white",
        
        # Colors (background)
        "bg_white": "bg-white",
        "bg_gray_100": "bg-gray-100",
        "bg_gray_200": "bg-gray-200",
        "bg_primary": "bg-blue-600",
        "bg_secondary": "bg-gray-600",
        
        # Position
        "position_relative": "relative",
        "position_absolute": "absolute",
        "position_fixed": "fixed",
        "position_sticky": "sticky",
    }
    
    def generate_tailwind(self, styles: Dict[str, Any]) -> str:
        """Generate Tailwind CSS classes from style dictionary."""
        classes = []
        
        # Layout
        if styles.get("display") == "flex":
            classes.append("flex")
            
            # Flex direction
            flex_dir = styles.get("flexDirection", "row")
            classes.append(f"flex-{flex_dir}" if flex_dir != "row" else "")
            
            # Justify content
            justify = styles.get("justifyContent", "flex-start")
            justify_map = {
                "flex-start": "justify-start",
                "center": "justify-center",
                "flex-end": "justify-end",
                "space-between": "justify-between",
                "space-around": "justify-around"
            }
            if justify in justify_map:
                classes.append(justify_map[justify])
            
            # Align items
            align = styles.get("alignItems", "stretch")
            align_map = {
                "flex-start": "items-start",
                "center": "items-center",
                "flex-end": "items-end",
                "stretch": "items-stretch"
            }
            if align in align_map:
                classes.append(align_map[align])
        
        elif styles.get("display") == "grid":
            classes.append("grid")
            
            # Grid columns
            cols = styles.get("gridTemplateColumns")
            if cols:
                if cols == "repeat(2, 1fr)":
                    classes.append("grid-cols-2")
                elif cols == "repeat(3, 1fr)":
                    classes.append("grid-cols-3")
                elif cols == "repeat(4, 1fr)":
                    classes.append("grid-cols-4")
        
        # Width
        width = styles.get("width")
        if width == "100%":
            classes.append("w-full")
        elif width == "auto":
            classes.append("w-auto")
        elif isinstance(width, (int, float)):
            classes.append(f"w-[{width}px]")
        
        # Height
        height = styles.get("height")
        if height == "100%":
            classes.append("h-full")
        elif height == "auto":
            classes.append("h-auto")
        elif isinstance(height, (int, float)):
            classes.append(f"h-[{height}px]")
        
        # Padding
        padding = styles.get("padding")
        if padding:
            if isinstance(padding, dict):
                if padding.get("top"):
                    classes.append(f"pt-[{padding['top']}px]")
                if padding.get("bottom"):
                    classes.append(f"pb-[{padding['bottom']}px]")
                if padding.get("left"):
                    classes.append(f"pl-[{padding['left']}px]")
                if padding.get("right"):
                    classes.append(f"pr-[{padding['right']}px]")
            elif isinstance(padding, (int, float)):
                classes.append(f"p-[{padding}px]")
        
        # Margin
        margin = styles.get("margin")
        if margin:
            if isinstance(margin, dict):
                if margin.get("top"):
                    classes.append(f"mt-[{margin['top']}px]")
                if margin.get("bottom"):
                    classes.append(f"mb-[{margin['bottom']}px]")
            elif isinstance(margin, (int, float)):
                classes.append(f"m-[{margin}px]")
        
        # Gap
        gap = styles.get("gap")
        if gap:
            classes.append(f"gap-[{gap}px]")
        
        # Background color
        bg = styles.get("backgroundColor")
        if bg:
            classes.append(f"bg-[{bg}]")
        
        # Text color
        color = styles.get("color")
        if color:
            classes.append(f"text-[{color}]")
        
        # Border radius
        radius = styles.get("borderRadius")
        if radius == "50%":
            classes.append("rounded-full")
        elif isinstance(radius, (int, float)):
            classes.append(f"rounded-[{radius}px]")
        
        # Border
        border = styles.get("border")
        if border:
            classes.append("border")
            border_color = styles.get("borderColor")
            if border_color:
                classes.append(f"border-[{border_color}]")
        
        # Shadow
        shadow = styles.get("boxShadow")
        if shadow:
            classes.append("shadow-md")
        
        # Typography
        font_size = styles.get("fontSize")
        if font_size:
            if isinstance(font_size, (int, float)):
                classes.append(f"text-[{font_size}px]")
            else:
                size_map = {
                    "12px": "text-xs",
                    "14px": "text-sm",
                    "16px": "text-base",
                    "18px": "text-lg",
                    "20px": "text-xl",
                    "24px": "text-2xl"
                }
                if font_size in size_map:
                    classes.append(size_map[font_size])
        
        font_weight = styles.get("fontWeight")
        if font_weight:
            weight_map = {
                "400": "font-normal",
                "500": "font-medium",
                "600": "font-semibold",
                "700": "font-bold"
            }
            if str(font_weight) in weight_map:
                classes.append(weight_map[str(font_weight)])
        
        # Position
        position = styles.get("position")
        if position:
            classes.append(position)
        
        # Filter out empty strings
        return " ".join([c for c in classes if c])
    
    def generate_css(self, styles: Dict[str, Any], selector: str = ".component") -> str:
        """Generate plain CSS from style dictionary."""
        css_lines = [f"{selector} {{"]
        
        for prop, value in styles.items():
            # Convert camelCase to kebab-case
            css_prop = re.sub(r'([A-Z])', r'-\1', prop).lower()
            css_lines.append(f"  {css_prop}: {value};")
        
        css_lines.append("}")
        
        return "\n".join(css_lines)
    
    def generate_scss(self, styles: Dict[str, Any], selector: str = ".component") -> str:
        """Generate SCSS from style dictionary."""
        return self.generate_css(styles, selector)


class ReactGenerator:
    """Generate React components."""
    
    def __init__(self, style_generator: StyleGenerator):
        self.style_generator = style_generator
    
    def generate(self, spec: ComponentSpec, 
                 style_system: StyleSystem = StyleSystem.TAILWIND) -> GeneratedCode:
        """Generate React component code."""
        
        # Generate imports
        imports = self._generate_imports(style_system)
        
        # Generate component body
        component_body = self._generate_component_body(spec, style_system)
        
        # Generate styles
        style_code = ""
        if style_system == StyleSystem.CSS_MODULES:
            style_code = self.style_generator.generate_css(spec.styles, ".container")
        elif style_system == StyleSystem.SCSS:
            style_code = self.style_generator.generate_scss(spec.styles, ".container")
        elif style_system == StyleSystem.STYLED_COMPONENTS:
            style_code = self._generate_styled_components(spec)
        
        # Generate prop types
        prop_types = self._generate_prop_types(spec)
        
        # Combine into full component
        template_code = f"""{imports}
{prop_types}
{style_code}

const {spec.name} = ({self._generate_props_destructure(spec)}) => {{
{self._generate_event_handlers(spec)}
  return (
{component_body}
  );
}};

export default {spec.name};
"""
        
        # Generate test code
        test_code = self._generate_test_code(spec)
        
        return GeneratedCode(
            framework=Framework.REACT,
            style_system=style_system,
            component_name=spec.name,
            template_code=template_code,
            style_code=style_code,
            test_code=test_code
        )
    
    def _generate_imports(self, style_system: StyleSystem) -> str:
        """Generate import statements."""
        imports = ["import React from 'react';"]
        
        if style_system == StyleSystem.CSS_MODULES:
            imports.append("import styles from './Component.module.css';")
        elif style_system == StyleSystem.STYLED_COMPONENTS:
            imports.append("import styled from 'styled-components';")
        elif style_system == StyleSystem.SCSS:
            imports.append("import './Component.scss';")
        
        return "\n".join(imports)
    
    def _generate_props_destructure(self, spec: ComponentSpec) -> str:
        """Generate props destructuring."""
        if not spec.props:
            return ""
        
        props_list = [p["name"] for p in spec.props]
        return "{ " + ", ".join(props_list) + " }"
    
    def _generate_prop_types(self, spec: ComponentSpec) -> str:
        """Generate TypeScript prop types."""
        if not spec.props:
            return ""
        
        prop_defs = []
        for prop in spec.props:
            prop_type = prop.get("type", "string")
            optional = "?" if prop.get("optional", True) else ""
            prop_defs.append(f"  {prop['name']}{optional}: {prop_type};")
        
        return f"""interface {spec.name}Props {{
{chr(10).join(prop_defs)}
}}
"""
    
    def _generate_event_handlers(self, spec: ComponentSpec) -> str:
        """Generate event handler functions."""
        handlers = []
        
        for event in spec.events:
            handler_name = f"handle{event.capitalize()}"
            handlers.append(f"""  const {handler_name} = () => {{
    // TODO: Implement {event} handler
  }};""")
        
        return "\n".join(handlers) if handlers else ""
    
    def _generate_component_body(self, spec: ComponentSpec, 
                                  style_system: StyleSystem) -> str:
        """Generate the JSX component body."""
        return self._generate_element_jsx(spec, 2, style_system)
    
    def _generate_element_jsx(self, spec: ComponentSpec, indent: int, 
                               style_system: StyleSystem) -> str:
        """Generate JSX for an element and its children."""
        indent_str = "  " * indent
        
        # Get Tailwind classes if using Tailwind
        class_attr = ""
        if style_system == StyleSystem.TAILWIND:
            classes = self.style_generator.generate_tailwind(spec.styles)
            if classes:
                class_attr = f' className="{classes}"'
        elif style_system == StyleSystem.CSS_MODULES:
            class_attr = ' className={styles.container}'
        
        # Generate event handlers
        event_attrs = ""
        for event in spec.events:
            handler_name = f"handle{event.capitalize()}"
            event_attrs += f" on{event.capitalize()}={{ {handler_name} }}"
        
        # Generate children
        children_jsx = ""
        if spec.children:
            children_jsx = "\n".join([
                self._generate_element_jsx(child, indent + 1, style_system)
                for child in spec.children
            ])
        
        # Determine element tag
        tag = self._get_element_tag(spec.element_type)
        
        # Generate JSX
        if children_jsx:
            return f"""{indent_str}<{tag}{class_attr}{event_attrs}>
{children_jsx}
{indent_str}</{tag}>"""
        else:
            # Self-closing or with content
            if spec.element_type in ["input", "img", "br", "hr"]:
                return f"{indent_str}<{tag}{class_attr}{event_attrs} />"
            else:
                content = spec.props.get("content", "") if isinstance(spec.props, dict) else ""
                return f"{indent_str}<{tag}{class_attr}{event_attrs}>{content}</{tag}>"
    
    def _get_element_tag(self, element_type: str) -> str:
        """Get HTML tag for element type."""
        tag_map = {
            "button": "button",
            "input": "input",
            "text": "span",
            "heading": "h2",
            "paragraph": "p",
            "image": "img",
            "container": "div",
            "card": "div",
            "list": "ul",
            "list_item": "li",
            "link": "a",
            "icon": "i",
            "nav": "nav",
            "header": "header",
            "footer": "footer",
            "sidebar": "aside",
            "main": "main",
            "section": "section"
        }
        return tag_map.get(element_type, "div")
    
    def _generate_styled_components(self, spec: ComponentSpec) -> str:
        """Generate styled-components code."""
        styles = []
        for prop, value in spec.styles.items():
            css_prop = re.sub(r'([A-Z])', r'-\1', prop).lower()
            styles.append(f"  {css_prop}: {value};")
        
        return f"""const Styled{spec.name} = styled.div`
{chr(10).join(styles)}
`;"""
    
    def _generate_test_code(self, spec: ComponentSpec) -> str:
        """Generate Jest test code."""
        return f"""import React from 'react';
import {{ render, screen }} from '@testing-library/react';
import {spec.name} from './{spec.name}';

describe('{spec.name}', () => {{
  it('renders correctly', () => {{
    render(<{spec.name} />);
    // Add your assertions here
  }});
}});"""


class VueGenerator:
    """Generate Vue components."""
    
    def __init__(self, style_generator: StyleGenerator):
        self.style_generator = style_generator
    
    def generate(self, spec: ComponentSpec,
                 style_system: StyleSystem = StyleSystem.TAILWIND) -> GeneratedCode:
        """Generate Vue component code."""
        
        # Generate template
        template = self._generate_template(spec, style_system)
        
        # Generate script
        script = self._generate_script(spec)
        
        # Generate styles
        style_code = ""
        if style_system == StyleSystem.TAILWIND:
            # Tailwind classes are in template
            pass
        else:
            style_code = self._generate_vue_styles(spec, style_system)
        
        # Combine
        template_code = f"""<template>
{template}
</template>

<script>
{script}
</script>

<style{' scoped' if style_system != StyleSystem.TAILWIND else ''}>
{style_code}
</style>
"""
        
        return GeneratedCode(
            framework=Framework.VUE,
            style_system=style_system,
            component_name=spec.name,
            template_code=template_code,
            style_code=style_code
        )
    
    def _generate_template(self, spec: ComponentSpec, 
                           style_system: StyleSystem) -> str:
        """Generate Vue template."""
        return self._generate_element_vue(spec, 1, style_system)
    
    def _generate_element_vue(self, spec: ComponentSpec, indent: int,
                               style_system: StyleSystem) -> str:
        """Generate Vue template element."""
        indent_str = "  " * indent
        
        # Get classes
        class_attr = ""
        if style_system == StyleSystem.TAILWIND:
            classes = self.style_generator.generate_tailwind(spec.styles)
            if classes:
                class_attr = f' class="{classes}"'
        
        # Generate event handlers
        event_attrs = ""
        for event in spec.events:
            vue_event = event.lower()
            event_attrs += f" @{vue_event}=\"handle{event.capitalize()}\""
        
        # Generate props bindings
        prop_attrs = ""
        for prop in spec.props:
            if prop.get("bind"):
                prop_attrs += f" :{prop['name']}=\"{prop['name']}\""
        
        # Determine tag
        tag = self._get_vue_tag(spec.element_type)
        
        # Generate children
        children_vue = ""
        if spec.children:
            children_vue = "\n".join([
                self._generate_element_vue(child, indent + 1, style_system)
                for child in spec.children
            ])
        
        if children_vue:
            return f"""{indent_str}<{tag}{class_attr}{event_attrs}{prop_attrs}>
{children_vue}
{indent_str}</{tag}>"""
        else:
            if spec.element_type in ["input", "img"]:
                return f"{indent_str}<{tag}{class_attr}{event_attrs}{prop_attrs} />"
            else:
                content = ""
                return f"{indent_str}<{tag}{class_attr}{event_attrs}{prop_attrs}>{content}</{tag}>"
    
    def _get_vue_tag(self, element_type: str) -> str:
        """Get Vue/HTML tag for element type."""
        return ReactGenerator(None)._get_element_tag(element_type)
    
    def _generate_script(self, spec: ComponentSpec) -> str:
        """Generate Vue script section."""
        props_def = ""
        if spec.props:
            props_list = [f"    '{p['name']}'" for p in spec.props]
            props_def = f"""  props: [
{chr(10).join(props_list)}
  ],"""
        
        methods_def = ""
        if spec.events:
            methods = []
            for event in spec.events:
                methods.append(f"""    handle{event.capitalize()}() {{
      // TODO: Implement {event} handler
    }},""")
            methods_def = f"""  methods: {{
{chr(10).join(methods)}
  }},"""
        
        return f"""export default {{
  name: '{spec.name}',{props_def}
{methods_def}
}};"""
    
    def _generate_vue_styles(self, spec: ComponentSpec, 
                              style_system: StyleSystem) -> str:
        """Generate Vue styles."""
        if style_system == StyleSystem.SCSS:
            return self.style_generator.generate_scss(spec.styles, ".container")
        else:
            return self.style_generator.generate_css(spec.styles, ".container")


class AngularGenerator:
    """Generate Angular components."""
    
    def __init__(self, style_generator: StyleGenerator):
        self.style_generator = style_generator
    
    def generate(self, spec: ComponentSpec,
                 style_system: StyleSystem = StyleSystem.TAILWIND) -> GeneratedCode:
        """Generate Angular component code."""
        
        # Generate template
        template = self._generate_template(spec, style_system)
        
        # Generate component class
        component_class = self._generate_component_class(spec)
        
        # Generate styles
        style_code = ""
        if style_system != StyleSystem.TAILWIND:
            style_code = self._generate_angular_styles(spec, style_system)
        
        # Combine
        template_code = f"""import {{ Component{', Input, Output, EventEmitter' if spec.props or spec.events else ''} }} from '@angular/core';

@Component({{
  selector: 'app-{spec.name.lower()}',
  template: `
{template}
  `,{f"""
  styles: [`
{style_code}
  `]""" if style_code else ""}
}})
{component_class}
"""
        
        return GeneratedCode(
            framework=Framework.ANGULAR,
            style_system=style_system,
            component_name=spec.name,
            template_code=template_code,
            style_code=style_code
        )
    
    def _generate_template(self, spec: ComponentSpec, 
                           style_system: StyleSystem) -> str:
        """Generate Angular template."""
        return self._generate_element_angular(spec, 2, style_system)
    
    def _generate_element_angular(self, spec: ComponentSpec, indent: int,
                                   style_system: StyleSystem) -> str:
        """Generate Angular template element."""
        indent_str = "  " * indent
        
        # Get classes
        class_attr = ""
        if style_system == StyleSystem.TAILWIND:
            classes = self.style_generator.generate_tailwind(spec.styles)
            if classes:
                class_attr = f' class="{classes}"'
        
        # Generate event handlers
        event_attrs = ""
        for event in spec.events:
            angular_event = event.lower()
            event_attrs += f" ({angular_event})=\"handle{event.capitalize()}()\""
        
        # Generate inputs
        input_attrs = ""
        for prop in spec.props:
            if prop.get("input"):
                input_attrs += f" [{prop['name']}]=\"{prop['name']}\""
        
        # Determine tag
        tag = self._get_angular_tag(spec.element_type)
        
        # Generate children
        children_ng = ""
        if spec.children:
            children_ng = "\n".join([
                self._generate_element_angular(child, indent + 1, style_system)
                for child in spec.children
            ])
        
        if children_ng:
            return f"""{indent_str}<{tag}{class_attr}{event_attrs}{input_attrs}>
{children_ng}
{indent_str}</{tag}>"""
        else:
            if spec.element_type in ["input", "img"]:
                return f"{indent_str}<{tag}{class_attr}{event_attrs}{input_attrs} />"
            else:
                return f"{indent_str}<{tag}{class_attr}{event_attrs}{input_attrs}></{tag}>"
    
    def _get_angular_tag(self, element_type: str) -> str:
        """Get Angular/HTML tag for element type."""
        return ReactGenerator(None)._get_element_tag(element_type)
    
    def _generate_component_class(self, spec: ComponentSpec) -> str:
        """Generate Angular component class."""
        inputs = []
        outputs = []
        methods = []
        
        for prop in spec.props:
            if prop.get("input"):
                inputs.append(f"  @Input() {prop['name']}: {prop.get('type', 'string')};")
        
        for event in spec.events:
            event_name = f"{event.lower()}Change"
            outputs.append(f"  @Output() {event_name} = new EventEmitter<void>();")
            methods.append(f"""  handle{event.capitalize()}() {{
    this.{event_name}.emit();
  }}""")
        
        inputs_str = "\n".join(inputs) if inputs else ""
        outputs_str = "\n".join(outputs) if outputs else ""
        methods_str = "\n\n".join(methods) if methods else ""
        
        return f"""export class {spec.name}Component {{
{inputs_str}
{outputs_str}
{methods_str}
}}"""
    
    def _generate_angular_styles(self, spec: ComponentSpec, 
                                  style_system: StyleSystem) -> str:
        """Generate Angular styles."""
        if style_system == StyleSystem.SCSS:
            return self.style_generator.generate_scss(spec.styles, ":host")
        else:
            return self.style_generator.generate_css(spec.styles, ":host")


class SvelteGenerator:
    """Generate Svelte components."""
    
    def __init__(self, style_generator: StyleGenerator):
        self.style_generator = style_generator
    
    def generate(self, spec: ComponentSpec,
                 style_system: StyleSystem = StyleSystem.TAILWIND) -> GeneratedCode:
        """Generate Svelte component code."""
        
        # Generate script
        script = self._generate_script(spec)
        
        # Generate template
        template = self._generate_template(spec, style_system)
        
        # Generate styles
        style_code = ""
        if style_system != StyleSystem.TAILWIND:
            style_code = self._generate_svelte_styles(spec, style_system)
        
        # Combine
        template_code = f"""<script>
{script}
</script>

{template}

<style>
{style_code}
</style>
"""
        
        return GeneratedCode(
            framework=Framework.SVELTE,
            style_system=style_system,
            component_name=spec.name,
            template_code=template_code,
            style_code=style_code
        )
    
    def _generate_script(self, spec: ComponentSpec) -> str:
        """Generate Svelte script section."""
        exports = []
        for prop in spec.props:
            exports.append(f"  export let {prop['name']}{' = ' + str(prop.get('default', "''")) if 'default' in prop else ''};")
        
        handlers = []
        for event in spec.events:
            handlers.append(f"""  function handle{event.capitalize()}() {{
    // TODO: Implement {event} handler
    dispatch('{event.lower()}', {{}});
  }}""")
        
        if spec.events:
            exports.insert(0, "  import {{ createEventDispatcher }} from 'svelte';")
            exports.insert(1, "  const dispatch = createEventDispatcher();")
        
        exports_str = "\n".join(exports) if exports else ""
        handlers_str = "\n\n".join(handlers) if handlers else ""
        
        return f"""{exports_str}
{handlers_str}"""
    
    def _generate_template(self, spec: ComponentSpec, 
                           style_system: StyleSystem) -> str:
        """Generate Svelte template."""
        return self._generate_element_svelte(spec, 0, style_system)
    
    def _generate_element_svelte(self, spec: ComponentSpec, indent: int,
                                  style_system: StyleSystem) -> str:
        """Generate Svelte template element."""
        indent_str =  "  " * indent
        
        # Get classes
        class_attr = ""
        if style_system == StyleSystem.TAILWIND:
            classes = self.style_generator.generate_tailwind(spec.styles)
            if classes:
                class_attr = f' class="{classes}"'
        
        # Generate event handlers
        event_attrs = ""
        for event in spec.events:
            svelte_event = event.lower()
            event_attrs += f" on:{svelte_event}=\"handle{event.capitalize()}\""
        
        # Determine tag
        tag = self._get_svelte_tag(spec.element_type)
        
        # Generate children
        children_svelte = ""
        if spec.children:
            children_svelte = "\n".join([
                self._generate_element_svelte(child, indent + 1, style_system)
                for child in spec.children
            ])
        
        if children_svelte:
            return f"""{indent_str}<{tag}{class_attr}{event_attrs}>
{children_svelte}
{indent_str}</{tag}>"""
        else:
            if spec.element_type in ["input", "img"]:
                return f"{indent_str}<{tag}{class_attr}{event_attrs} />"
            else:
                return f"{indent_str}<{tag}{class_attr}{event_attrs}></{tag}>"
    
    def _get_svelte_tag(self, element_type: str) -> str:
        """Get Svelte/HTML tag for element type."""
        return ReactGenerator(None)._get_element_tag(element_type)
    
    def _generate_svelte_styles(self, spec: ComponentSpec, 
                                 style_system: StyleSystem) -> str:
        """Generate Svelte styles."""
        return self.style_generator.generate_css(spec.styles, ".container")


class CodeGenerator:
    """Main code generator that orchestrates framework-specific generators."""
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize the code generator.
        
        Args:
            templates_dir: Directory containing code templates
        """
        self.style_generator = StyleGenerator()
        self.generators = {
            Framework.REACT: ReactGenerator(self.style_generator),
            Framework.VUE: VueGenerator(self.style_generator),
            Framework.ANGULAR: AngularGenerator(self.style_generator),
            Framework.SVELTE: SvelteGenerator(self.style_generator)
        }
        
        # Load templates if directory provided
        self.templates = {}
        if templates_dir:
            self._load_templates(templates_dir)
    
    def _load_templates(self, templates_dir: str):
        """Load code templates from directory."""
        templates_path = Path(templates_dir)
        
        for framework in Framework:
            framework_dir = templates_path / framework.value
            if framework_dir.exists():
                self.templates[framework] = {}
                for template_file in framework_dir.glob("*.template"):
                    with open(template_file, 'r') as f:
                        self.templates[framework][template_file.stem] = f.read()
    
    def generate(self, spec: ComponentSpec, 
                 framework: Framework = Framework.REACT,
                 style_system: StyleSystem = StyleSystem.TAILWIND) -> GeneratedCode:
        """
        Generate code for a component specification.
        
        Args:
            spec: Component specification
            framework: Target framework
            style_system: Styling system to use
            
        Returns:
            GeneratedCode object
        """
        generator = self.generators.get(framework)
        if not generator:
            raise ValueError(f"Unsupported framework: {framework}")
        
        return generator.generate(spec, style_system)
    
    def generate_from_analysis(self, analysis: Dict[str, Any],
                                framework: Framework = Framework.REACT,
                                style_system: StyleSystem = StyleSystem.TAILWIND,
                                component_name: str = "GeneratedComponent") -> GeneratedCode:
        """
        Generate code from visual analysis result.
        
        Args:
            analysis: Visual analysis result
            framework: Target framework
            style_system: Styling system to use
            component_name: Name for the generated component
            
        Returns:
            GeneratedCode object
        """
        # Convert analysis to component spec
        spec = self._analysis_to_spec(analysis, component_name)
        
        # Generate code
        return self.generate(spec, framework, style_system)
    
    def _analysis_to_spec(self, analysis: Dict[str, Any], 
                          component_name: str) -> ComponentSpec:
        """Convert visual analysis to component specification."""
        elements = analysis.get("elements", [])
        colors = analysis.get("colors", {})
        layout = analysis.get("layout", "flex_column")
        
        # Create root container
        root_styles = {
            "display": "flex",
            "flexDirection": "column" if layout == "flex_column" else "row",
            "width": "100%",
            "minHeight": "100vh",
            "backgroundColor": colors.get("background", "#ffffff")
        }
        
        children = []
        for i, elem in enumerate(elements):
            child_spec = self._element_to_spec(elem, f"child_{i}", colors)
            children.append(child_spec)
        
        return ComponentSpec(
            name=component_name,
            element_type="container",
            styles=root_styles,
            children=children
        )
    
    def _element_to_spec(self, element: Dict[str, Any], 
                         name: str, colors: Dict[str, str]) -> ComponentSpec:
        """Convert analysis element to component spec."""
        elem_type = element.get("type", "container")
        bbox = element.get("bbox", {})
        styles = element.get("styles", {})
        text = element.get("text", "")
        children = element.get("children", [])
        
        # Convert bbox to styles
        element_styles = {
            "width": f"{bbox.get('width', 100)}px" if bbox.get('width') else "auto",
            "height": f"{bbox.get('height', 50)}px" if bbox.get('height') else "auto",
        }
        
        # Merge with existing styles
        element_styles.update(styles)
        
        # Map element type
        type_map = {
            "button": "button",
            "input": "input",
            "text": "text",
            "image": "image",
            "container": "container",
            "card": "card",
            "navbar": "nav",
            "sidebar": "sidebar",
            "list": "list"
        }
        mapped_type = type_map.get(elem_type, "container")
        
        # Create child specs
        child_specs = []
        for i, child in enumerate(children):
            child_specs.append(self._element_to_spec(child, f"{name}_child_{i}", colors))
        
        # Create props
        props = []
        if text:
            props.append({"name": "content", "type": "string", "default": f"'{text}'"})
        
        return ComponentSpec(
            name=name,
            element_type=mapped_type,
            props=props,
            styles=element_styles,
            children=child_specs
        )
    
    def batch_generate(self, specs: List[ComponentSpec],
                       framework: Framework = Framework.REACT,
                       style_system: StyleSystem = StyleSystem.TAILWIND) -> List[GeneratedCode]:
        """Generate code for multiple components."""
        return [self.generate(spec, framework, style_system) for spec in specs]
    
    def save_generated_code(self, generated: GeneratedCode, 
                           output_dir: str) -> Dict[str, str]:
        """
        Save generated code to files.
        
        Args:
            generated: GeneratedCode object
            output_dir: Output directory
            
        Returns:
            Dictionary of file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        files = {}
        
        # Determine file extensions
        ext_map = {
            Framework.REACT: ".jsx",
            Framework.VUE: ".vue",
            Framework.ANGULAR: ".component.ts",
            Framework.SVELTE: ".svelte"
        }
        
        ext = ext_map.get(generated.framework, ".jsx")
        
        # Save main component file
        component_file = output_path / f"{generated.component_name}{ext}"
        with open(component_file, 'w') as f:
            f.write(generated.template_code)
        files['component'] = str(component_file)
        
        # Save style file if separate
        if generated.style_code and generated.style_system != StyleSystem.TAILWIND:
            if generated.framework == Framework.REACT:
                if generated.style_system == StyleSystem.CSS_MODULES:
                    style_file = output_path / f"{generated.component_name}.module.css"
                elif generated.style_system == StyleSystem.SCSS:
                    style_file = output_path / f"{generated.component_name}.scss"
                else:
                    style_file = output_path / f"{generated.component_name}.css"
                
                with open(style_file, 'w') as f:
                    f.write(generated.style_code)
                files['styles'] = str(style_file)
        
        # Save test file
        if generated.test_code:
            test_file = output_path / f"{generated.component_name}.test.js"
            with open(test_file, 'w') as f:
                f.write(generated.test_code)
            files['test'] = str(test_file)
        
        return files


# Export main classes
__all__ = [
    'CodeGenerator',
    'ReactGenerator',
    'VueGenerator',
    'AngularGenerator',
    'SvelteGenerator',
    'StyleGenerator',
    'GeneratedCode',
    'ComponentSpec',
    'Framework',
    'StyleSystem'
]
