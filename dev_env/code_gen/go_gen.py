#!/usr/bin/env python3
"""
Mrki Go Code Generator
Generates Go code with Gin framework and GORM
"""

from typing import Dict, List, Optional, Any, Union
from .generator import CodeGenerator, Class, Method, Field, Module, FieldType


class GoGenerator(CodeGenerator):
    """Go code generator"""
    
    def __init__(self, output_path: str = ".", framework: str = "gin"):
        super().__init__(output_path)
        self.framework = framework  # gin, echo, fiber
    
    def get_file_extension(self) -> str:
        return ".go"
    
    def _get_type_map(self) -> Dict[FieldType, str]:
        return {
            FieldType.STRING: "string",
            FieldType.INTEGER: "int64",
            FieldType.FLOAT: "float64",
            FieldType.BOOLEAN: "bool",
            FieldType.DATETIME: "time.Time",
            FieldType.DATE: "time.Time",
            FieldType.UUID: "uuid.UUID",
            FieldType.ARRAY: "[]interface{}",
            FieldType.OBJECT: "map[string]interface{}",
            FieldType.ANY: "interface{}",
        }
    
    def generate_class(self, class_def: Class) -> str:
        """Generate Go struct (class equivalent)"""
        lines = []
        
        # Package declaration
        lines.append(f"package {self._to_snake_case(class_def.name)}")
        lines.append("")
        
        # Imports
        imports = self._collect_imports(class_def.fields)
        if imports:
            lines.append("import (")
            for imp in imports:
                lines.append(f'\t"{imp}"')
            lines.append(")")
            lines.append("")
        
        # Struct comment
        if class_def.description:
            lines.append(f"// {class_def.name} {class_def.description}")
        
        # Struct definition
        lines.append(f"type {class_def.name} struct {{")
        
        for field in class_def.fields:
            json_tag = f' json:"{field.name}"'
            gorm_tag = ""
            
            if field.unique:
                gorm_tag = f' gorm:"uniqueIndex"'
            elif field.indexed:
                gorm_tag = f' gorm:"index"'
            
            go_type = self.map_type(field.type)
            if not field.required:
                go_type = f"*{go_type}"  # Pointer for optional
            
            if field.description:
                lines.append(f"\t// {field.description}")
            lines.append(f"\t{self._to_pascal_case(field.name)} {go_type}`{json_tag}{gorm_tag}`")
        
        lines.append("}")
        
        # Methods
        for method in class_def.methods:
            lines.append("")
            lines.append(self.generate_function(method))
        
        return "\n".join(lines)
    
    def generate_function(self, method: Method) -> str:
        """Generate Go function"""
        lines = []
        
        # Function comment
        if method.description:
            lines.append(f"// {method.name} {method.description}")
        
        # Function signature
        receiver = ""
        if not method.is_static:
            receiver = f"(s *{method.name.split('_')[0]}) "
        
        params_str = ", ".join([
            f"{p.name} {self.map_type(p.type)}" for p in method.params
        ])
        
        return_type = ""
        if method.return_type:
            return_type = f" {self.map_type(method.return_type)}"
        if method.is_async:
            return_type = f" (<-chan{return_type}, error)"
        
        lines.append(f"func {receiver}{method.name}({params_str}){return_type} {{")
        
        # Function body
        if method.body:
            lines.append(self._indent(method.body))
        else:
            lines.append("\t// TODO: Implement")
            if method.return_type:
                lines.append(f"\treturn {self._go_zero_value(method.return_type)}")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate_module(self, module: Module) -> str:
        """Generate complete Go module"""
        lines = []
        
        # Package declaration
        lines.append(f"package {self._to_snake_case(module.name)}")
        lines.append("")
        
        # Imports
        lines.append("import (")
        lines.append('\t"github.com/gin-gonic/gin"')
        lines.append('\t"gorm.io/gorm"')
        lines.append('\t"time"')
        lines.append(")")
        lines.append("")
        
        # Module comment
        lines.append(f"// {module.name} module")
        lines.append("")
        
        # Functions
        for func in module.functions:
            lines.append(self.generate_function(func))
            lines.append("")
        
        # Structs
        for cls in module.classes:
            lines.append(self.generate_class(cls))
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_model(self, name: str, fields: List[Field]) -> str:
        """Generate Go/GORM model"""
        lines = [
            f"package models",
            "",
            "import (",
            '\t"time"',
            '\t"github.com/google/uuid"',
            '\t"gorm.io/gorm"',
            ")",
            "",
            f"// {name} represents a {name.lower()} entity",
            f"type {name} struct {{",
            "\tID        uuid.UUID `gorm:\"type:uuid;primary_key;default:gen_random_uuid()\" json:\"id\"`",
            "\tCreatedAt time.Time `json:\"created_at\"`",
            "\tUpdatedAt time.Time `json:\"updated_at\"`",
            "\tDeletedAt gorm.DeletedAt `gorm:\"index\" json:\"-\"`",
        ]
        
        for field in fields:
            go_type = self.map_type(field.type)
            json_tag = f' json:"{field.name}"'
            
            gorm_tags = []
            if field.unique:
                gorm_tags.append("uniqueIndex")
            if field.indexed:
                gorm_tags.append("index")
            if not field.required:
                gorm_tags.append("null")
            
            gorm_tag = f' gorm:"{";".join(gorm_tags)}"' if gorm_tags else ""
            
            if field.description:
                lines.append(f"\t// {field.description}")
            lines.append(f"\t{self._to_pascal_case(field.name)} {go_type}`{json_tag}{gorm_tag}`")
        
        lines.append("}")
        lines.append("")
        
        # Table name method
        lines.append(f"// TableName specifies the table name for {name}")
        lines.append(f"func ({name}) TableName() string {{")
        lines.append(f'\treturn "{name.lower()}s"')
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate_api_endpoint(self, path: str, method: str,
                              params: List[Field], response_type: FieldType) -> str:
        """Generate Gin handler"""
        method_lower = method.lower()
        handler_name = f"{self._to_pascal_case(method_lower)}{self._path_to_handler_name(path)}"
        
        lines = [
            f"// {handler_name} handles {method.upper()} {path}",
            f"func {handler_name}(c *gin.Context) {{",
            "\t// Parse request",
        ]
        
        # Extract parameters
        for param in params:
            if param.name in path:
                lines.append(f"\t{param.name} := c.Param(\"{param.name}\")")
            elif param.type == FieldType.OBJECT:
                lines.append(f"\tvar req struct {{")
                for f in params:
                    lines.append(f"\t\t{self._to_pascal_case(f.name)} {self.map_type(f.type)} `json:\"{f.name}\"`")
                lines.append("\t}")
                lines.append("\tif err := c.ShouldBindJSON(&req); err != nil {")
                lines.append("\t\tc.JSON(400, gin.H{\"error\": err.Error()})")
                lines.append("\t\treturn")
                lines.append("\t}")
        
        lines.append("")
        lines.append("\t// TODO: Implement logic")
        lines.append("")
        lines.append("\tc.JSON(200, gin.H{")
        lines.append('\t\t"success": true,')
        lines.append('\t\t"data": nil,')
        lines.append("\t})")
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate_test(self, target: Union[Class, Method]) -> str:
        """Generate Go test"""
        lines = [
            f"package {self._to_snake_case(target.name) if isinstance(target, Class) else 'main'}",
            "",
            "import (",
            '\t"testing"',
            '\t"github.com/stretchr/testify/assert"',
            ")",
            "",
        ]
        
        if isinstance(target, Class):
            lines.append(f"func Test{target.name}(t *testing.T) {{")
            
            for method in target.methods:
                lines.append(f"\tt.Run(\"{method.name}\", func(t *testing.T) {{")
                lines.append("\t\t// Arrange")
                lines.append(f"\t\tinstance := New{target.name}()")
                lines.append("")
                lines.append("\t\t// Act")
                params = ", ".join([f'test_{p.name}' for p in method.params])
                lines.append(f"\t\tresult := instance.{method.name}({params})")
                lines.append("")
                lines.append("\t\t// Assert")
                lines.append("\t\tassert.NotNil(t, result)")
                lines.append("\t})")
            
            lines.append("}")
        
        elif isinstance(target, Method):
            lines.append(f"func Test{target.name}(t *testing.T) {{")
            lines.append("\t// Arrange")
            lines.append("")
            lines.append("\t// Act")
            params = ", ".join([f'test_{p.name}' for p in target.params])
            lines.append(f"\tresult := {target.name}({params})")
            lines.append("")
            lines.append("\t// Assert")
            lines.append("\tassert.NotNil(t, result)")
            lines.append("}")
        
        return "\n".join(lines)
    
    def _collect_imports(self, fields: List[Field]) -> List[str]:
        """Collect required imports"""
        imports = set()
        
        for field in fields:
            if field.type in (FieldType.DATETIME, FieldType.DATE):
                imports.add("time")
            elif field.type == FieldType.UUID:
                imports.add("github.com/google/uuid")
        
        return sorted(imports)
    
    def _to_snake_case(self, name: str) -> str:
        """Convert to snake_case"""
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append('_')
            result.append(char.lower())
        return ''.join(result)
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert to PascalCase"""
        parts = name.split('_')
        return ''.join(p.capitalize() for p in parts)
    
    def _go_zero_value(self, field_type: FieldType) -> str:
        """Get zero value for Go type"""
        zero_values = {
            FieldType.STRING: '""',
            FieldType.INTEGER: "0",
            FieldType.FLOAT: "0.0",
            FieldType.BOOLEAN: "false",
            FieldType.DATETIME: "time.Time{}",
            FieldType.DATE: "time.Time{}",
            FieldType.UUID: "uuid.Nil",
        }
        return zero_values.get(field_type, "nil")
    
    def _indent(self, code: str, level: int = 1) -> str:
        """Indent code"""
        indent = "\t" * level
        return "\n".join(indent + line if line.strip() else line for line in code.split("\n"))
    
    def _path_to_handler_name(self, path: str) -> str:
        """Convert path to handler name"""
        parts = path.strip("/").split("/")
        return "".join(self._to_pascal_case(p.replace(":", "")) for p in parts)
    
    # CRUD methods
    def _generate_create_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""func Create{model_name}(db *gorm.DB, input *{model_name}) (*{model_name}, error) {{
	if err := db.Create(input).Error; err != nil {{
		return nil, err
	}}
	return input, nil
}}"""
    
    def _generate_read_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""func Get{model_name}ByID(db *gorm.DB, id uuid.UUID) (*{model_name}, error) {{
	var result {model_name}
	if err := db.First(&result, "id = ?", id).Error; err != nil {{
		return nil, err
	}}
	return &result, nil
}}"""
    
    def _generate_update_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""func Update{model_name}(db *gorm.DB, id uuid.UUID, updates map[string]interface{{}}) (*{model_name}, error) {{
	var result {model_name}
	if err := db.Model(&result).Where("id = ?", id).Updates(updates).Error; err != nil {{
		return nil, err
	}}
	return &result, nil
}}"""
    
    def _generate_delete_method(self, model_name: str) -> str:
        return f"""func Delete{model_name}(db *gorm.DB, id uuid.UUID) error {{
	return db.Delete(&{model_name}{{}}, "id = ?", id).Error
}}"""
    
    def _generate_list_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""func List{model_name}s(db *gorm.DB, page, pageSize int) ([]{model_name}, int64, error) {{
	var results []{model_name}
	var total int64
	
	offset := (page - 1) * pageSize
	
	if err := db.Model(&{model_name}{{}}).Count(&total).Error; err != nil {{
		return nil, 0, err
	}}
	
	if err := db.Offset(offset).Limit(pageSize).Find(&results).Error; err != nil {{
		return nil, 0, err
	}}
	
	return results, total, nil
}}"""
