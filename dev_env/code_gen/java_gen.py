#!/usr/bin/env python3
"""
Mrki Java Code Generator
Generates Java code with Spring Boot and JPA
"""

from typing import Dict, List, Optional, Any, Union
from .generator import CodeGenerator, Class, Method, Field, Module, FieldType


class JavaGenerator(CodeGenerator):
    """Java code generator"""
    
    def __init__(self, output_path: str = ".", framework: str = "spring"):
        super().__init__(output_path)
        self.framework = framework  # spring, jakarta, vanilla
        self.package = "com.example"
    
    def get_file_extension(self) -> str:
        return ".java"
    
    def _get_type_map(self) -> Dict[FieldType, str]:
        return {
            FieldType.STRING: "String",
            FieldType.INTEGER: "Long",
            FieldType.FLOAT: "Double",
            FieldType.BOOLEAN: "Boolean",
            FieldType.DATETIME: "LocalDateTime",
            FieldType.DATE: "LocalDate",
            FieldType.UUID: "UUID",
            FieldType.ARRAY: "List<Object>",
            FieldType.OBJECT: "Map<String, Object>",
            FieldType.ANY: "Object",
        }
    
    def generate_class(self, class_def: Class) -> str:
        """Generate Java class"""
        lines = []
        
        # Package declaration
        lines.append(f"package {self.package};")
        lines.append("")
        
        # Imports
        imports = self._collect_imports(class_def)
        for imp in sorted(imports):
            lines.append(f"import {imp};")
        lines.append("")
        
        # Class comment
        if class_def.description:
            lines.append("/**")
            lines.append(f" * {class_def.description}")
            lines.append(" */")
        
        # Annotations
        if self.framework == "spring":
            if "Controller" in class_def.name or "controller" in class_def.name.lower():
                lines.append("@RestController")
                lines.append("@RequestMapping(\"/api\")")
            elif "Service" in class_def.name or "service" in class_def.name.lower():
                lines.append("@Service")
            elif "Repository" in class_def.name or "repository" in class_def.name.lower():
                lines.append("@Repository")
        
        # Class definition
        access = "public "
        abstract = "abstract " if class_def.is_abstract else ""
        extends_str = f" extends {class_def.extends}" if class_def.extends else ""
        implements_str = ""
        if class_def.implements:
            implements_str = f" implements {', '.join(class_def.implements)}"
        
        lines.append(f"{access}{abstract}class {class_def.name}{extends_str}{implements_str} {{")
        
        # Fields
        for field in class_def.fields:
            if field.description:
                lines.append(f"    /** {field.description} */")
            
            # Annotations
            if self.framework == "spring":
                if field.name == "id":
                    lines.append("    @Id")
                    lines.append("    @GeneratedValue(strategy = GenerationType.IDENTITY)")
                if field.unique:
                    lines.append("    @Column(unique = true)")
                elif not field.required:
                    lines.append("    @Column(nullable = true)")
            
            access_mod = "private "
            type_str = self.map_type(field.type)
            if not field.required and field.type not in (FieldType.OBJECT, FieldType.ARRAY):
                type_str = f"Optional<{type_str}>"
            
            lines.append(f"    {access_mod}{type_str} {field.name};")
        
        # Constructor
        if class_def.fields:
            lines.append("")
            lines.append(f"    public {class_def.name}() {{}}")
            
            # All-args constructor
            lines.append("")
            params = ", ".join([
                f"{self.map_type(f.type)} {f.name}" for f in class_def.fields
            ])
            lines.append(f"    public {class_def.name}({params}) {{")
            for field in class_def.fields:
                lines.append(f"        this.{field.name} = {field.name};")
            lines.append("    }")
        
        # Getters and Setters
        for field in class_def.fields:
            type_str = self.map_type(field.type)
            pascal_name = self._to_pascal_case(field.name)
            
            lines.append("")
            lines.append(f"    public {type_str} get{pascal_name}() {{")
            lines.append(f"        return this.{field.name};")
            lines.append("    }")
            lines.append("")
            lines.append(f"    public void set{pascal_name}({type_str} {field.name}) {{")
            lines.append(f"        this.{field.name} = {field.name};")
            lines.append("    }")
        
        # Methods
        for method in class_def.methods:
            lines.append("")
            lines.append(self._indent_method(self.generate_function(method)))
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate_function(self, method: Method) -> str:
        """Generate Java method"""
        lines = []
        
        # Method comment
        if method.description:
            lines.append("/**")
            lines.append(f" * {method.description}")
            for param in method.params:
                lines.append(f" * @param {param.name} {param.description or ''}")
            if method.return_type:
                lines.append(f" * @return {self.map_type(method.return_type)}")
            lines.append(" */")
        
        # Annotations
        if self.framework == "spring":
            if method.is_async:
                lines.append("    @Async")
            if method.name.startswith("get"):
                lines.append("    @GetMapping")
            elif method.name.startswith("post"):
                lines.append("    @PostMapping")
            elif method.name.startswith("put"):
                lines.append("    @PutMapping")
            elif method.name.startswith("delete"):
                lines.append("    @DeleteMapping")
        
        # Method signature
        access = "public "
        static = "static " if method.is_static else ""
        
        return_type = "void"
        if method.return_type:
            return_type = self.map_type(method.return_type)
        
        params_str = ", ".join([
            f"{self.map_type(p.type)} {p.name}" for p in method.params
        ])
        
        lines.append(f"{access}{static}{return_type} {method.name}({params_str}) {{")
        
        # Method body
        if method.body:
            lines.append(self._indent(method.body))
        else:
            lines.append("        // TODO: Implement")
            if method.return_type:
                lines.append(f"        return {self._java_zero_value(method.return_type)};")
        
        lines.append("    }")
        
        return "\n".join(lines)
    
    def generate_module(self, module: Module) -> str:
        """Generate complete Java module"""
        lines = []
        
        # Package declaration
        lines.append(f"package {self.package}.{self._to_snake_case(module.name)};")
        lines.append("")
        
        # Imports
        for imp in module.imports:
            lines.append(f"import {imp};")
        
        if self.framework == "spring":
            lines.append("import org.springframework.web.bind.annotation.*;")
            lines.append("import org.springframework.stereotype.*;")
            lines.append("import org.springframework.data.jpa.repository.*;")
        
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
        
        return "\n".join(lines)
    
    def generate_model(self, name: str, fields: List[Field]) -> str:
        """Generate Java/JPA entity"""
        lines = [
            f"package {self.package}.model;",
            "",
            "import jakarta.persistence.*;",
            "import java.time.LocalDateTime;",
            "import java.util.UUID;",
            "",
            f"/** {name} entity */",
            "@Entity",
            f"@Table(name = \"{name.lower()}s\")",
            f"public class {name} {{",
            "",
            "    @Id",
            "    @GeneratedValue(strategy = GenerationType.IDENTITY)",
            "    private Long id;",
            "",
            "    @Column(name = \"created_at\", nullable = false, updatable = false)",
            "    private LocalDateTime createdAt;",
            "",
            "    @Column(name = \"updated_at\")",
            "    private LocalDateTime updatedAt;",
            "",
        ]
        
        for field in fields:
            annotations = []
            if field.unique:
                annotations.append("    @Column(unique = true)")
            elif not field.required:
                annotations.append("    @Column(nullable = true)")
            else:
                annotations.append("    @Column(nullable = false)")
            
            type_str = self.map_type(field.type)
            
            if field.description:
                lines.append(f"    /** {field.description} */")
            for ann in annotations:
                lines.append(ann)
            lines.append(f"    private {type_str} {field.name};")
            lines.append("")
        
        # PrePersist and PreUpdate
        lines.append("    @PrePersist")
        lines.append("    protected void onCreate() {")
        lines.append("        createdAt = LocalDateTime.now();")
        lines.append("        updatedAt = LocalDateTime.now();")
        lines.append("    }")
        lines.append("")
        lines.append("    @PreUpdate")
        lines.append("    protected void onUpdate() {")
        lines.append("        updatedAt = LocalDateTime.now();")
        lines.append("    }")
        lines.append("")
        
        # Getters and Setters
        for field in [Field("id", FieldType.INTEGER)] + fields:
            type_str = self.map_type(field.type)
            pascal_name = self._to_pascal_case(field.name)
            
            lines.append(f"    public {type_str} get{pascal_name}() {{")
            lines.append(f"        return this.{field.name};")
            lines.append("    }")
            lines.append("")
            lines.append(f"    public void set{pascal_name}({type_str} {field.name}) {{")
            lines.append(f"        this.{field.name} = {field.name};")
            lines.append("    }")
            lines.append("")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate_api_endpoint(self, path: str, method: str,
                              params: List[Field], response_type: FieldType) -> str:
        """Generate Spring controller endpoint"""
        method_upper = method.upper()
        handler_name = f"{method.lower()}{self._path_to_handler_name(path)}"
        
        lines = [
            f"    @RequestMapping(value = \"{path}\", method = RequestMethod.{method_upper})",
            f"    public ResponseEntity<{self.map_type(response_type)}> {handler_name}(",
        ]
        
        # Add parameters
        for param in params:
            if param.name in path:
                lines.append(f"            @PathVariable {self.map_type(param.type)} {param.name},")
            else:
                lines.append(f"            @RequestBody {self.map_type(param.type)} {param.name},")
        
        if lines[-1].endswith(","):
            lines[-1] = lines[-1][:-1]
        
        lines.append("    ) {")
        lines.append("        // TODO: Implement")
        lines.append(f"        return ResponseEntity.ok({self._java_zero_value(response_type)});")
        lines.append("    }")
        
        return "\n".join(lines)
    
    def generate_test(self, target: Union[Class, Method]) -> str:
        """Generate JUnit test"""
        lines = [
            f"package {self.package};",
            "",
            "import org.junit.jupiter.api.Test;",
            "import org.junit.jupiter.api.BeforeEach;",
            "import static org.junit.jupiter.api.Assertions.*;",
            "",
        ]
        
        if isinstance(target, Class):
            lines.append(f"import {self.package}.model.{target.name};")
            lines.append("")
            lines.append(f"class {target.name}Test {{")
            lines.append("")
            lines.append(f"    private {target.name} {self._to_camel_case(target.name)};")
            lines.append("")
            lines.append("    @BeforeEach")
            lines.append("    void setUp() {")
            lines.append(f"        {self._to_camel_case(target.name)} = new {target.name}();")
            lines.append("    }")
            lines.append("")
            
            for method in target.methods:
                lines.append("    @Test")
                lines.append(f"    void test{self._to_pascal_case(method.name)}() {{")
                lines.append("        // Arrange")
                lines.append("")
                lines.append("        // Act")
                params = ", ".join([f'test_{p.name}' for p in method.params])
                lines.append(f"        var result = {self._to_camel_case(target.name)}.{method.name}({params});")
                lines.append("")
                lines.append("        // Assert")
                lines.append("        assertNotNull(result);")
                lines.append("    }")
                lines.append("")
            
            lines.append("}")
        
        return "\n".join(lines)
    
    def _collect_imports(self, class_def: Class) -> List[str]:
        """Collect required imports"""
        imports = set()
        
        if self.framework == "spring":
            imports.add("org.springframework.web.bind.annotation.*")
            imports.add("org.springframework.http.ResponseEntity")
        
        for field in class_def.fields:
            if field.type == FieldType.DATETIME:
                imports.add("java.time.LocalDateTime")
            elif field.type == FieldType.DATE:
                imports.add("java.time.LocalDate")
            elif field.type == FieldType.UUID:
                imports.add("java.util.UUID")
            elif field.type == FieldType.ARRAY:
                imports.add("java.util.List")
            elif field.type == FieldType.OBJECT:
                imports.add("java.util.Map")
        
        return list(imports)
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert to PascalCase"""
        parts = name.split('_')
        return ''.join(p.capitalize() for p in parts)
    
    def _to_camel_case(self, name: str) -> str:
        """Convert to camelCase"""
        pascal = self._to_pascal_case(name)
        return pascal[0].lower() + pascal[1:]
    
    def _to_snake_case(self, name: str) -> str:
        """Convert to snake_case"""
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append('_')
            result.append(char.lower())
        return ''.join(result)
    
    def _java_zero_value(self, field_type: FieldType) -> str:
        """Get zero value for Java type"""
        zero_values = {
            FieldType.STRING: '""',
            FieldType.INTEGER: "0L",
            FieldType.FLOAT: "0.0",
            FieldType.BOOLEAN: "false",
        }
        return zero_values.get(field_type, "null")
    
    def _indent(self, code: str, level: int = 1) -> str:
        """Indent code"""
        indent = "    " * level
        return "\n".join(indent + line if line.strip() else line for line in code.split("\n"))
    
    def _indent_method(self, code: str) -> str:
        """Indent method for class"""
        lines = code.split("\n")
        result = []
        for line in lines:
            if line.strip():
                result.append("    " + line)
            else:
                result.append(line)
        return "\n".join(result)
    
    def _path_to_handler_name(self, path: str) -> str:
        """Convert path to handler name"""
        parts = path.strip("/").split("/")
        return "".join(self._to_pascal_case(p.replace(":", "")) for p in parts)
    
    # CRUD methods
    def _generate_create_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""public {model_name} create{model_name}(Create{model_name}Dto dto) {{
    {model_name} entity = new {model_name}();
    // TODO: Map fields
    return repository.save(entity);
}}"""
    
    def _generate_read_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""public Optional<{model_name}> get{model_name}ById(Long id) {{
    return repository.findById(id);
}}"""
    
    def _generate_update_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""public {model_name} update{model_name}(Long id, Update{model_name}Dto dto) {{
    {model_name} entity = repository.findById(id)
        .orElseThrow(() -> new EntityNotFoundException("{model_name} not found"));
    // TODO: Map fields
    return repository.save(entity);
}}"""
    
    def _generate_delete_method(self, model_name: str) -> str:
        return f"""public void delete{model_name}(Long id) {{
    repository.deleteById(id);
}}"""
    
    def _generate_list_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""public Page<{model_name}> list{model_name}s(Pageable pageable) {{
    return repository.findAll(pageable);
}}"""
