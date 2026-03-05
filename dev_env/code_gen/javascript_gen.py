#!/usr/bin/env python3
"""
Mrki JavaScript Code Generator
Generates JavaScript code for Node.js, Express, and general JS
"""

from typing import Dict, List, Optional, Any, Union
from .generator import CodeGenerator, Class, Method, Field, Module, FieldType


class JavaScriptGenerator(CodeGenerator):
    """JavaScript code generator"""
    
    def __init__(self, output_path: str = ".", framework: str = "express"):
        super().__init__(output_path)
        self.framework = framework  # express, fastify, vanilla
        self.use_es6 = True
    
    def get_file_extension(self) -> str:
        return ".js"
    
    def _get_type_map(self) -> Dict[FieldType, str]:
        return {
            FieldType.STRING: "string",
            FieldType.INTEGER: "number",
            FieldType.FLOAT: "number",
            FieldType.BOOLEAN: "boolean",
            FieldType.DATETIME: "Date",
            FieldType.DATE: "Date",
            FieldType.UUID: "string",
            FieldType.ARRAY: "Array",
            FieldType.OBJECT: "Object",
            FieldType.ANY: "any",
        }
    
    def generate_class(self, class_def: Class) -> str:
        """Generate JavaScript class"""
        lines = []
        
        # JSDoc
        if class_def.description:
            lines.append("/**")
            lines.append(f" * {class_def.description}")
            lines.append(" */")
        
        # Class definition
        extends_str = f" extends {class_def.extends}" if class_def.extends else ""
        lines.append(f"class {class_def.name}{extends_str} {{")
        
        # Constructor
        if class_def.fields:
            lines.append("  /**")
            lines.append("   * @param {Object} params")
            for field in class_def.fields:
                type_str = self.map_type(field.type)
                lines.append(f"   * @param {{{type_str}}} params.{field.name}")
            lines.append("   */")
            
            lines.append("  constructor(params = {}) {")
            if class_def.extends:
                lines.append("    super(params);")
            
            for field in class_def.fields:
                default = f" ?? {self._js_default(field.default)}" if field.default is not None else ""
                lines.append(f"    this.{field.name} = params.{field.name}{default};")
            
            lines.append("  }")
        
        # Methods
        for method in class_def.methods:
            lines.append("")
            lines.append(self._indent_method(self.generate_function(method)))
        
        lines.append("}")
        
        # Export
        lines.append("")
        lines.append(f"module.exports = {{ {class_def.name} }};")
        
        return "\n".join(lines)
    
    def generate_function(self, method: Method) -> str:
        """Generate JavaScript function"""
        lines = []
        
        # JSDoc
        if method.description:
            lines.append("/**")
            lines.append(f" * {method.description}")
            for param in method.params:
                type_str = self.map_type(param.type)
                lines.append(f" * @param {{{type_str}}} {param.name}")
            if method.return_type:
                return_str = self.map_type(method.return_type)
                lines.append(f" * @returns {{{return_str}}}")
            lines.append(" */")
        
        # Function definition
        async_prefix = "async " if method.is_async else ""
        static_prefix = "static " if method.is_static else ""
        private_prefix = "#" if method.is_private else ""
        
        params_str = ", ".join([p.name for p in method.params])
        
        lines.append(f"{static_prefix}{async_prefix}{private_prefix}{method.name}({params_str}) {{")
        
        # Function body
        if method.body:
            lines.append(self._indent(method.body))
        else:
            lines.append("  // TODO: Implement")
            lines.append("  throw new Error('Not implemented');")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate_module(self, module: Module) -> str:
        """Generate complete JavaScript module"""
        lines = []
        
        # Imports
        for imp in module.imports:
            lines.append(imp)
        
        if self.framework == "express":
            lines.append("const express = require('express');")
            lines.append("const router = express.Router();")
        elif self.framework == "mongoose":
            lines.append("const mongoose = require('mongoose');")
        
        lines.append("")
        
        # Module comment
        lines.append(f"/** {module.name} module */")
        lines.append("")
        
        # Functions
        for func in module.functions:
            lines.append(self.generate_function(func))
            lines.append("")
        
        # Classes
        for cls in module.classes:
            lines.append(self.generate_class(cls))
            lines.append("")
        
        # Exports
        if module.exports:
            exports_str = ", ".join(module.exports)
            lines.append(f"module.exports = {{ {exports_str} }};")
        elif self.framework == "express":
            lines.append("module.exports = router;")
        
        return "\n".join(lines)
    
    def generate_model(self, name: str, fields: List[Field]) -> str:
        """Generate JavaScript/Mongoose model"""
        if self.framework == "mongoose":
            return self._generate_mongoose_model(name, fields)
        elif self.framework == "sequelize":
            return self._generate_sequelize_model(name, fields)
        else:
            return self._generate_js_class_model(name, fields)
    
    def _generate_mongoose_model(self, name: str, fields: List[Field]) -> str:
        """Generate Mongoose schema and model"""
        lines = [
            "const mongoose = require('mongoose');",
            "",
            f"/** {name} Schema */",
            f"const {name}Schema = new mongoose.Schema({{",
        ]
        
        mongoose_types = {
            FieldType.STRING: "String",
            FieldType.INTEGER: "Number",
            FieldType.FLOAT: "Number",
            FieldType.BOOLEAN: "Boolean",
            FieldType.DATETIME: "Date",
            FieldType.DATE: "Date",
            FieldType.UUID: "String",
            FieldType.ARRAY: "[mongoose.Schema.Types.Mixed]",
            FieldType.OBJECT: "mongoose.Schema.Types.Mixed",
        }
        
        for field in fields:
            field_type = mongoose_types.get(field.type, "String")
            
            if not field.required:
                lines.append(f"  {field.name}: {{ type: {field_type} }},")
            else:
                lines.append(f"  {field.name}: {{ type: {field_type}, required: true }},")
        
        lines.append("  createdAt: { type: Date, default: Date.now },")
        lines.append("  updatedAt: { type: Date, default: Date.now },")
        
        lines.append("}, {")
        lines.append("  timestamps: true,")
        lines.append("});")
        lines.append("")
        
        # Indexes
        indexed_fields = [f.name for f in fields if f.indexed]
        if indexed_fields:
            for field_name in indexed_fields:
                lines.append(f"{name}Schema.index({{ {field_name}: 1 }});")
            lines.append("")
        
        lines.append(f"module.exports = mongoose.model('{name}', {name}Schema);")
        
        return "\n".join(lines)
    
    def _generate_sequelize_model(self, name: str, fields: List[Field]) -> str:
        """Generate Sequelize model"""
        lines = [
            "const { DataTypes } = require('sequelize');",
            "const sequelize = require('../config/database');",
            "",
            f"/** {name} Model */",
            f"const {name} = sequelize.define('{name}', {{",
        ]
        
        sequelize_types = {
            FieldType.STRING: "DataTypes.STRING",
            FieldType.INTEGER: "DataTypes.INTEGER",
            FieldType.FLOAT: "DataTypes.FLOAT",
            FieldType.BOOLEAN: "DataTypes.BOOLEAN",
            FieldType.DATETIME: "DataTypes.DATE",
            FieldType.DATE: "DataTypes.DATEONLY",
            FieldType.UUID: "DataTypes.UUID",
            FieldType.TEXT: "DataTypes.TEXT",
        }
        
        for field in fields:
            field_type = sequelize_types.get(field.type, "DataTypes.STRING")
            
            options = []
            if field.required:
                options.append("allowNull: false")
            else:
                options.append("allowNull: true")
            if field.unique:
                options.append("unique: true")
            
            options_str = ", ".join(options)
            lines.append(f"  {field.name}: {{ type: {field_type}, {options_str} }},")
        
        lines.append("}, {")
        lines.append(f"  tableName: '{name.toLowerCase()}s',")
        lines.append("  timestamps: true,")
        lines.append("});")
        lines.append("")
        lines.append(f"module.exports = {name};")
        
        return "\n".join(lines)
    
    def _generate_js_class_model(self, name: str, fields: List[Field]) -> str:
        """Generate plain JavaScript class model"""
        lines = [
            f"/** {name} Model */",
            f"class {name} {{",
            "  /**",
            "   * @param {Object} data",
            "   */",
            "  constructor(data = {}) {",
        ]
        
        for field in fields:
            default = f" ?? {self._js_default(field.default)}" if field.default is not None else ""
            lines.append(f"    this.{field.name} = data.{field.name}{default};")
        
        lines.append("  }")
        lines.append("")
        
        # toJSON method
        lines.append("  toJSON() {")
        lines.append("    return {")
        for field in fields:
            lines.append(f"      {field.name}: this.{field.name},")
        lines.append("    };")
        lines.append("  }")
        lines.append("")
        
        # validate method
        lines.append("  validate() {")
        lines.append("    const errors = [];")
        for field in fields:
            if field.required:
                lines.append(f"    if (!this.{field.name}) errors.push('{field.name} is required');")
        lines.append("    return errors;")
        lines.append("  }")
        
        lines.append("}")
        lines.append("")
        lines.append(f"module.exports = {{ {name} }};")
        
        return "\n".join(lines)
    
    def generate_api_endpoint(self, path: str, method: str,
                              params: List[Field], response_type: FieldType) -> str:
        """Generate Express route handler"""
        method_lower = method.lower()
        handler_name = f"{method_lower}{self._path_to_handler_name(path)}"
        
        lines = [
            f"/**",
            f" * {method.upper()} {path}",
            f" * @route {method.upper()} {path}",
            f" */",
            f"const {handler_name} = async (req, res, next) => {{",
            "  try {",
        ]
        
        # Extract parameters
        for param in params:
            if param.name in path:
                lines.append(f"    const {{ {param.name} }} = req.params;")
            else:
                lines.append(f"    const {{ {param.name} }} = req.body;")
        
        lines.append("")
        lines.append("    // TODO: Implement logic")
        lines.append("")
        lines.append("    res.json({ success: true, data: null });")
        lines.append("  } catch (error) {")
        lines.append("    next(error);")
        lines.append("  }")
        lines.append("};")
        lines.append("")
        lines.append(f"router.{method_lower}('{path}', {handler_name});")
        
        return "\n".join(lines)
    
    def generate_test(self, target: Union[Class, Method]) -> str:
        """Generate Jest test"""
        lines = [
            "const request = require('supertest');",
            "const app = require('../app');",
            "",
        ]
        
        if isinstance(target, Class):
            lines.append(f"const {{ {target.name} }} = require('../models/{target.name}');")
            lines.append("")
            lines.append(f"describe('{target.name}', () => {{")
            
            for method in target.methods:
                lines.append(f"  describe('{method.name}', () => {{")
                lines.append(f"    it('should {method.name} successfully', async () => {{")
                lines.append("      // Arrange")
                lines.append(f"      const instance = new {target.name}();")
                lines.append("")
                lines.append("      // Act")
                params = ", ".join([f"'test_{p.name}'" for p in method.params])
                lines.append(f"      const result = await instance.{method.name}({params});")
                lines.append("")
                lines.append("      // Assert")
                lines.append("      expect(result).toBeDefined();")
                lines.append("    });")
                lines.append("  });")
            
            lines.append("});")
        
        elif isinstance(target, Method):
            lines.append(f"describe('{target.name}', () => {{")
            lines.append(f"  it('should {target.name} successfully', async () => {{")
            lines.append("    // Arrange")
            lines.append("")
            lines.append("    // Act")
            params = ", ".join([f"'test_{p.name}'" for p in target.params])
            lines.append(f"    const result = await {target.name}({params});")
            lines.append("")
            lines.append("    // Assert")
            lines.append("    expect(result).toBeDefined();")
            lines.append("  });")
            lines.append("});")
        
        return "\n".join(lines)
    
    def _js_default(self, value: Any) -> str:
        """Convert Python default to JS default"""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, str):
            return f"'{value}'"
        return str(value)
    
    def _indent(self, code: str, level: int = 1) -> str:
        """Indent code"""
        indent = "  " * level
        return "\n".join(indent + line if line.strip() else line for line in code.split("\n"))
    
    def _indent_method(self, code: str) -> str:
        """Indent method for class"""
        lines = code.split("\n")
        result = []
        for line in lines:
            if line.strip():
                result.append("  " + line)
            else:
                result.append(line)
        return "\n".join(result)
    
    def _path_to_handler_name(self, path: str) -> str:
        """Convert path to handler name"""
        parts = path.strip("/").split("/")
        return "".join(p.capitalize() for p in parts if not p.startswith(":"))
    
    # CRUD methods
    def _generate_create_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""async function create{model_name}(data) {{
  try {{
    const {model_name.lower()} = new {model_name}(data);
    await {model_name.lower()}.save();
    return {model_name.lower()};
  }} catch (error) {{
    throw new Error(`Failed to create {model_name}: ${{error.message}}`);
  }}
}}"""
    
    def _generate_read_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""async function get{model_name}ById(id) {{
  try {{
    return await {model_name}.findById(id);
  }} catch (error) {{
    throw new Error(`Failed to get {model_name}: ${{error.message}}`);
  }}
}}"""
    
    def _generate_update_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""async function update{model_name}(id, data) {{
  try {{
    return await {model_name}.findByIdAndUpdate(id, data, {{ new: true }});
  }} catch (error) {{
    throw new Error(`Failed to update {model_name}: ${{error.message}}`);
  }}
}}"""
    
    def _generate_delete_method(self, model_name: str) -> str:
        return f"""async function delete{model_name}(id) {{
  try {{
    await {model_name}.findByIdAndDelete(id);
    return true;
  }} catch (error) {{
    throw new Error(`Failed to delete {model_name}: ${{error.message}}`);
  }}
}}"""
    
    def _generate_list_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""async function list{model_name}s(options = {{}}) {{
  const {{ page = 1, limit = 10 }} = options;
  try {{
    const skip = (page - 1) * limit;
    const [items, total] = await Promise.all([
      {model_name}.find().skip(skip).limit(limit),
      {model_name}.countDocuments()
    ]);
    return {{ items, total, page, pages: Math.ceil(total / limit) }};
  }} catch (error) {{
    throw new Error(`Failed to list {model_name}s: ${{error.message}}`);
  }}
}}"""
