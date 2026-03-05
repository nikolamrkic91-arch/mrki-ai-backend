#!/usr/bin/env python3
"""
Mrki C# Code Generator
Generates C# code with .NET and Entity Framework Core
"""

from typing import Dict, List, Optional, Any, Union
from .generator import CodeGenerator, Class, Method, Field, Module, FieldType


class CSharpGenerator(CodeGenerator):
    """C# code generator"""
    
    def __init__(self, output_path: str = ".", framework: str = "dotnet"):
        super().__init__(output_path)
        self.framework = framework  # dotnet, aspnet
        self.namespace = "MyApp"
    
    def get_file_extension(self) -> str:
        return ".cs"
    
    def _get_type_map(self) -> Dict[FieldType, str]:
        return {
            FieldType.STRING: "string",
            FieldType.INTEGER: "long",
            FieldType.FLOAT: "double",
            FieldType.BOOLEAN: "bool",
            FieldType.DATETIME: "DateTime",
            FieldType.DATE: "DateOnly",
            FieldType.UUID: "Guid",
            FieldType.ARRAY: "List<object>",
            FieldType.OBJECT: "Dictionary<string, object>",
            FieldType.ANY: "object",
        }
    
    def generate_class(self, class_def: Class) -> str:
        """Generate C# class"""
        lines = []
        
        # Using statements
        usings = self._collect_usings(class_def)
        for u in sorted(usings):
            lines.append(f"using {u};")
        lines.append("")
        
        # Namespace
        lines.append(f"namespace {self.namespace}")
        lines.append("{")
        
        # Class comment
        if class_def.description:
            lines.append(f"    /// <summary>")
            lines.append(f"    /// {class_def.description}")
            lines.append(f"    /// </summary>")
        
        # Attributes
        if self.framework == "aspnet":
            if "Controller" in class_def.name:
                lines.append("    [ApiController]")
                lines.append('    [Route("api/[controller]")]')
            elif "Service" in class_def.name:
                lines.append("    [Service]")
        
        # Class definition
        access = "public "
        abstract = "abstract " if class_def.is_abstract else ""
        sealed = "sealed " if not class_def.is_abstract and not class_def.extends else ""
        static = "static " if class_def.is_static else ""
        
        extends_str = f" : {class_def.extends}" if class_def.extends else ""
        implements_str = ""
        if class_def.implements:
            separator = ", " if class_def.extends else " : "
            implements_str = f"{separator}{', '.join(class_def.implements)}"
        
        lines.append(f"    {access}{abstract}{sealed}{static}class {class_def.name}{extends_str}{implements_str}")
        lines.append("    {")
        
        # Properties
        for field in class_def.fields:
            if field.description:
                lines.append(f"        /// <summary>")
                lines.append(f"        /// {field.description}")
                lines.append(f"        /// </summary>")
            
            # Attributes
            if self.framework == "aspnet":
                if field.name == "Id":
                    lines.append("        [Key]")
                    lines.append("        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]")
                if field.required:
                    lines.append("        [Required]")
                if field.unique:
                    lines.append("        [StringLength(255)]")
                if field.description:
                    lines.append(f'        [Display(Name = "{field.description}")]')
            
            access_mod = "public "
            type_str = self.map_type(field.type)
            if not field.required and field.type not in (FieldType.OBJECT, FieldType.ARRAY):
                type_str += "?"
            
            getter = "get;"
            setter = " set;" if not field.readonly else ""
            
            lines.append(f"        {access_mod}{type_str} {self._to_pascal_case(field.name)} {{{getter}{setter}}}")
        
        # Constructor
        if class_def.fields and not class_def.is_static:
            lines.append("")
            lines.append(f"        public {class_def.name}()")
            lines.append("        {")
            lines.append("        }")
            
            # Parameterized constructor
            lines.append("")
            params = ", ".join([
                f"{self.map_type(f.type)} {self._to_camel_case(f.name)}" for f in class_def.fields
            ])
            lines.append(f"        public {class_def.name}({params})")
            lines.append("        {")
            for field in class_def.fields:
                pascal_name = self._to_pascal_case(field.name)
                camel_name = self._to_camel_case(field.name)
                lines.append(f"            {pascal_name} = {camel_name};")
            lines.append("        }")
        
        # Methods
        for method in class_def.methods:
            lines.append("")
            lines.append(self._indent_method(self.generate_function(method)))
        
        lines.append("    }")
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate_function(self, method: Method) -> str:
        """Generate C# method"""
        lines = []
        
        # Method comment
        if method.description:
            lines.append(f"        /// <summary>")
            lines.append(f"        /// {method.description}")
            lines.append(f"        /// </summary>")
            for param in method.params:
                lines.append(f"        /// <param name=\"{param.name}\">{param.description or ''}</param>")
            if method.return_type:
                lines.append(f"        /// <returns>{self.map_type(method.return_type)}</returns>")
            lines.append(f"        /// </summary>")
        
        # Attributes
        if self.framework == "aspnet":
            http_methods = {
                "get": "HttpGet",
                "post": "HttpPost",
                "put": "HttpPut",
                "delete": "HttpDelete",
                "patch": "HttpPatch",
            }
            if method.name.lower() in http_methods:
                lines.append(f"        [{http_methods[method.name.lower()]}]")
        
        # Method signature
        access = "public "
        static = "static " if method.is_static else ""
        async_prefix = "async " if method.is_async else ""
        
        return_type = "void"
        if method.return_type:
            return_type = self.map_type(method.return_type)
        if method.is_async:
            return_type = f"Task<{return_type}>"
        
        params_str = ", ".join([
            f"{self.map_type(p.type)} {self._to_camel_case(p.name)}" for p in method.params
        ])
        
        lines.append(f"        {access}{static}{async_prefix}{return_type} {method.name}({params_str})")
        lines.append("        {")
        
        # Method body
        if method.body:
            lines.append(self._indent(method.body))
        else:
            lines.append("            // TODO: Implement")
            if method.return_type:
                lines.append(f"            return {self._csharp_zero_value(method.return_type)};")
            elif method.is_async:
                lines.append("            return Task.CompletedTask;")
        
        lines.append("        }")
        
        return "\n".join(lines)
    
    def generate_module(self, module: Module) -> str:
        """Generate complete C# module"""
        lines = []
        
        # Using statements
        for imp in module.imports:
            lines.append(f"using {imp};")
        
        if self.framework == "aspnet":
            lines.append("using Microsoft.AspNetCore.Mvc;")
            lines.append("using Microsoft.EntityFrameworkCore;")
        
        lines.append("")
        
        # Namespace
        lines.append(f"namespace {self.namespace}.{module.name}")
        lines.append("{")
        
        # Module comment
        lines.append(f"    /// <summary>{module.name} module</summary>")
        lines.append("")
        
        # Functions
        for func in module.functions:
            lines.append(self.generate_function(func))
            lines.append("")
        
        # Classes
        for cls in module.classes:
            lines.append(self.generate_class(cls))
            lines.append("")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate_model(self, name: str, fields: List[Field]) -> str:
        """Generate C# Entity Framework model"""
        lines = [
            "using System;",
            "using System.ComponentModel.DataAnnotations;",
            "using System.ComponentModel.DataAnnotations.Schema;",
            "",
            f"namespace {self.namespace}.Models",
            "{",
            f"    /// <summary>{name} entity</summary>",
            f"    [Table(\"{name}s\")]",
            f"    public class {name}",
            "    {",
            "        [Key]",
            "        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]",
            "        public long Id { get; set; }",
            "",
            "        [Required]",
            "        public DateTime CreatedAt { get; set; }",
            "",
            "        public DateTime? UpdatedAt { get; set; }",
            "",
        ]
        
        for field in fields:
            type_str = self.map_type(field.type)
            if not field.required:
                type_str += "?"
            
            if field.description:
                lines.append(f"        /// <summary>{field.description}</summary>")
            
            if field.required:
                lines.append("        [Required]")
            if field.unique:
                lines.append("        [StringLength(255)]")
            
            pascal_name = self._to_pascal_case(field.name)
            lines.append(f"        public {type_str} {pascal_name} {{ get; set; }}")
            lines.append("")
        
        lines.append("    }")
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate_api_endpoint(self, path: str, method: str,
                              params: List[Field], response_type: FieldType) -> str:
        """Generate ASP.NET controller action"""
        method_lower = method.lower()
        action_name = f"{method.capitalize()}{self._path_to_action_name(path)}"
        
        lines = [
            f"        [Http{method.capitalize()}(\"{path}\")]",
            f"        public async Task<ActionResult<{self.map_type(response_type)}>> {action_name}(",
        ]
        
        # Add parameters
        for param in params:
            if param.name in path:
                lines.append(f"            [FromRoute] {self.map_type(param.type)} {self._to_camel_case(param.name)},")
            else:
                lines.append(f"            [FromBody] {self.map_type(param.type)} {self._to_camel_case(param.name)},")
        
        if lines[-1].endswith(","):
            lines[-1] = lines[-1][:-1]
        
        lines.append("        )")
        lines.append("        {")
        lines.append("            // TODO: Implement")
        lines.append("            return Ok();")
        lines.append("        }")
        
        return "\n".join(lines)
    
    def generate_test(self, target: Union[Class, Method]) -> str:
        """Generate xUnit test"""
        lines = [
            "using Xunit;",
            "using Moq;",
            "using System.Threading.Tasks;",
            "",
        ]
        
        if isinstance(target, Class):
            lines.append(f"using {self.namespace}.Models;")
            lines.append("")
            lines.append(f"namespace {self.namespace}.Tests")
            lines.append("{")
            lines.append(f"    public class {target.name}Tests")
            lines.append("    {")
            lines.append(f"        private readonly {target.name} _{self._to_camel_case(target.name)};")
            lines.append("")
            lines.append("        public {}Tests()".format(target.name))
            lines.append("        {")
            lines.append(f"            _{self._to_camel_case(target.name)} = new {target.name}();")
            lines.append("        }")
            lines.append("")
            
            for method in target.methods:
                lines.append("        [Fact]")
                lines.append(f"        public async Task {method.name}_ShouldReturnResult()")
                lines.append("        {")
                lines.append("            // Arrange")
                lines.append("")
                lines.append("            // Act")
                params = ", ".join([f'test_{self._to_camel_case(p.name)}' for p in method.params])
                lines.append(f"            var result = await _{self._to_camel_case(target.name)}.{method.name}({params});")
                lines.append("")
                lines.append("            // Assert")
                lines.append("            Assert.NotNull(result);")
                lines.append("        }")
                lines.append("")
            
            lines.append("    }")
            lines.append("}")
        
        return "\n".join(lines)
    
    def _collect_usings(self, class_def: Class) -> List[str]:
        """Collect required using statements"""
        usings = set()
        
        if self.framework == "aspnet":
            usings.add("Microsoft.AspNetCore.Mvc")
            usings.add("Microsoft.EntityFrameworkCore")
            usings.add("System.ComponentModel.DataAnnotations")
            usings.add("System.ComponentModel.DataAnnotations.Schema")
        
        for field in class_def.fields:
            if field.type == FieldType.DATETIME:
                usings.add("System")
            elif field.type == FieldType.UUID:
                usings.add("System")
            elif field.type == FieldType.ARRAY:
                usings.add("System.Collections.Generic")
            elif field.type == FieldType.OBJECT:
                usings.add("System.Collections.Generic")
        
        return list(usings)
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert to PascalCase"""
        parts = name.split('_')
        return ''.join(p.capitalize() for p in parts)
    
    def _to_camel_case(self, name: str) -> str:
        """Convert to camelCase"""
        pascal = self._to_pascal_case(name)
        return pascal[0].lower() + pascal[1:]
    
    def _csharp_zero_value(self, field_type: FieldType) -> str:
        """Get zero value for C# type"""
        zero_values = {
            FieldType.STRING: '""',
            FieldType.INTEGER: "0",
            FieldType.FLOAT: "0.0",
            FieldType.BOOLEAN: "false",
        }
        return zero_values.get(field_type, "null")
    
    def _indent(self, code: str, level: int = 1) -> str:
        """Indent code"""
        indent = "            " * level
        return "\n".join(indent + line if line.strip() else line for line in code.split("\n"))
    
    def _indent_method(self, code: str) -> str:
        """Indent method for class"""
        lines = code.split("\n")
        result = []
        for line in lines:
            if line.strip():
                result.append("        " + line)
            else:
                result.append(line)
        return "\n".join(result)
    
    def _path_to_action_name(self, path: str) -> str:
        """Convert path to action name"""
        parts = path.strip("/").split("/")
        return "".join(self._to_pascal_case(p.replace(":", "").replace("-", "_")) for p in parts)
    
    # CRUD methods
    def _generate_create_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""public async Task<{model_name}> CreateAsync(Create{model_name}Dto dto)
{{
    var entity = new {model_name}
    {{
        CreatedAt = DateTime.UtcNow,
        // TODO: Map other fields
    }};
    
    _context.{model_name}s.Add(entity);
    await _context.SaveChangesAsync();
    return entity;
}}"""
    
    def _generate_read_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""public async Task<{model_name}?> GetByIdAsync(long id)
{{
    return await _context.{model_name}s.FindAsync(id);
}}"""
    
    def _generate_update_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""public async Task<{model_name}?> UpdateAsync(long id, Update{model_name}Dto dto)
{{
    var entity = await _context.{model_name}s.FindAsync(id);
    if (entity == null) return null;
    
    // TODO: Map fields
    entity.UpdatedAt = DateTime.UtcNow;
    
    await _context.SaveChangesAsync();
    return entity;
}}"""
    
    def _generate_delete_method(self, model_name: str) -> str:
        return f"""public async Task<bool> DeleteAsync(long id)
{{
    var entity = await _context.{model_name}s.FindAsync(id);
    if (entity == null) return false;
    
    _context.{model_name}s.Remove(entity);
    await _context.SaveChangesAsync();
    return true;
}}"""
    
    def _generate_list_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""public async Task<(List<{model_name}> Items, int Total)> ListAsync(int page = 1, int pageSize = 10)
{{
    var query = _context.{model_name}s.AsQueryable();
    
    var total = await query.CountAsync();
    var items = await query
        .Skip((page - 1) * pageSize)
        .Take(pageSize)
        .ToListAsync();
    
    return (items, total);
}}"""
