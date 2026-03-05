#!/usr/bin/env python3
"""
Mrki TypeScript Code Generator
Generates TypeScript code for Node.js, NestJS, and frontend applications
"""

from typing import Dict, List, Optional, Any, Union
from .generator import CodeGenerator, Class, Method, Field, Module, FieldType


class TypeScriptGenerator(CodeGenerator):
    """TypeScript code generator"""
    
    def __init__(self, output_path: str = ".", framework: str = "nestjs"):
        super().__init__(output_path)
        self.framework = framework  # nestjs, express, react, vanilla
    
    def get_file_extension(self) -> str:
        return ".ts"
    
    def _get_type_map(self) -> Dict[FieldType, str]:
        return {
            FieldType.STRING: "string",
            FieldType.INTEGER: "number",
            FieldType.FLOAT: "number",
            FieldType.BOOLEAN: "boolean",
            FieldType.DATETIME: "Date",
            FieldType.DATE: "Date",
            FieldType.UUID: "string",
            FieldType.ARRAY: "Array<T>",
            FieldType.OBJECT: "Record<string, any>",
            FieldType.ANY: "any",
        }
    
    def generate_class(self, class_def: Class) -> str:
        """Generate TypeScript class"""
        lines = []
        
        # Imports for decorators
        if self.framework == "nestjs":
            lines.append("import { Injectable } from '@nestjs/common';")
            lines.append("")
        
        # JSDoc
        if class_def.description:
            lines.append("/**")
            lines.append(f" * {class_def.description}")
            lines.append(" */")
        
        # Decorators
        if self.framework == "nestjs" and not class_def.is_abstract:
            lines.append("@Injectable()")
        
        # Class definition
        abstract = "abstract " if class_def.is_abstract else ""
        extends_str = f" extends {class_def.extends}" if class_def.extends else ""
        implements_str = ""
        if class_def.implements:
            implements_str = f" implements {', '.join(class_def.implements)}"
        
        lines.append(f"export {abstract}class {class_def.name}{extends_str}{implements_str} {{")
        
        # Properties
        for field in class_def.fields:
            type_str = self.map_type(field.type)
            if not field.required:
                type_str += " | undefined"
            
            optional = "?" if not field.required else ""
            default = f" = {self._ts_default(field.default)}" if field.default is not None else ""
            
            if field.description:
                lines.append(f"  /** {field.description} */")
            lines.append(f"  {field.access_modifier or 'private'}{field.name}{optional}: {type_str}{default};")
        
        # Constructor
        if class_def.fields or class_def.extends:
            lines.append("")
            lines.append("  constructor(")
            
            ctor_params = []
            for field in class_def.fields:
                type_str = self.map_type(field.type)
                if not field.required:
                    type_str += " | undefined"
                optional = "?" if not field.required else ""
                ctor_params.append(f"    {field.access_modifier or 'private'}readonly {field.name}{optional}: {type_str}")
            
            lines.append(",\n".join(ctor_params))
            lines.append("  ) {")
            
            if class_def.extends:
                lines.append("    super();")
            
            lines.append("  }")
        
        # Methods
        for method in class_def.methods:
            lines.append("")
            lines.append(self._indent_method(self.generate_function(method)))
        
        lines.append("}")
        lines.append("")
        lines.append(f"export default {class_def.name};")
        
        return "\n".join(lines)
    
    def generate_function(self, method: Method) -> str:
        """Generate TypeScript function/method"""
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
        private_prefix = "private " if method.is_private else ""
        
        params_str = ", ".join([
            f"{p.name}{'?' if not p.required else ''}: {self.map_type(p.type)}"
            for p in method.params
        ])
        
        return_type = f": {self.map_type(method.return_type)}" if method.return_type else ": void"
        if method.is_async and method.return_type:
            return_type = f": Promise<{self.map_type(method.return_type)}>"
        elif method.is_async:
            return_type = ": Promise<void>"
        
        lines.append(f"{static_prefix}{private_prefix}{async_prefix}{method.name}({params_str}){return_type} {{")
        
        # Function body
        if method.body:
            lines.append(self._indent(method.body))
        else:
            lines.append("  // TODO: Implement")
            lines.append("  throw new Error('Not implemented');")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate_module(self, module: Module) -> str:
        """Generate complete TypeScript module"""
        lines = []
        
        # Framework-specific imports
        if self.framework == "nestjs":
            lines.append("import { Module } from '@nestjs/common';")
        elif self.framework == "express":
            lines.append("import express, { Request, Response, NextFunction } from 'express';")
        
        # Standard imports
        for imp in module.imports:
            lines.append(imp)
        
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
        
        # NestJS module decorator
        if self.framework == "nestjs" and module.classes:
            providers = [c.name for c in module.classes]
            lines.append(f"""@Module({{
  providers: [{', '.join(providers)}],
  exports: [{', '.join(providers)}],
}})
export class {module.name}Module {{}}
""")
        
        return "\n".join(lines)
    
    def generate_model(self, name: str, fields: List[Field]) -> str:
        """Generate TypeScript interface/type"""
        if self.framework == "nestjs":
            return self._generate_nestjs_dto(name, fields)
        elif self.framework == "typeorm":
            return self._generate_typeorm_entity(name, fields)
        else:
            return self._generate_ts_interface(name, fields)
    
    def _generate_nestjs_dto(self, name: str, fields: List[Field]) -> str:
        """Generate NestJS DTO with class-validator"""
        lines = [
            "import { IsString, IsNumber, IsBoolean, IsOptional, IsDate, ValidateNested } from 'class-validator';",
            "import { Type } from 'class-transformer';",
            "",
            f"export class {name} {{",
        ]
        
        for field in fields:
            decorator = self._get_validator_decorator(field)
            if decorator:
                lines.append(f"  {decorator}")
            
            optional = "?" if not field.required else ""
            type_str = self.map_type(field.type)
            lines.append(f"  {field.name}{optional}: {type_str};")
            lines.append("")
        
        lines.append("}")
        lines.append("")
        
        # Create DTO
        lines.append(f"export class Create{name}Dto {{")
        for field in fields:
            if field.required:
                decorator = self._get_validator_decorator(field)
                if decorator:
                    lines.append(f"  {decorator}")
                type_str = self.map_type(field.type)
                lines.append(f"  {field.name}: {type_str};")
                lines.append("")
        lines.append("}")
        lines.append("")
        
        # Update DTO
        lines.append(f"export class Update{name}Dto {{")
        for field in fields:
            lines.append(f"  @IsOptional()")
            decorator = self._get_validator_decorator(field)
            if decorator:
                lines.append(f"  {decorator}")
            type_str = self.map_type(field.type)
            lines.append(f"  {field.name}?: {type_str};")
            lines.append("")
        lines.append("}")
        
        return "\n".join(lines)
    
    def _generate_typeorm_entity(self, name: str, fields: List[Field]) -> str:
        """Generate TypeORM entity"""
        lines = [
            "import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn } from 'typeorm';",
            "",
            f"@Entity('{name.lower()}s')",
            f"export class {name} {{",
            "  @PrimaryGeneratedColumn()",
            "  id!: number;",
            "",
        ]
        
        for field in fields:
            column_options = []
            if field.unique:
                column_options.append("unique: true")
            if not field.required:
                column_options.append("nullable: true")
            
            options_str = f"({{ {', '.join(column_options)} }})" if column_options else "()"
            type_str = self._get_typeorm_type(field.type)
            
            lines.append(f"  @Column{type_str}{options_str}")
            optional = "?" if not field.required else ""
            ts_type = self.map_type(field.type)
            lines.append(f"  {field.name}{optional}: {ts_type};")
            lines.append("")
        
        lines.append("  @CreateDateColumn()")
        lines.append("  createdAt!: Date;")
        lines.append("")
        lines.append("  @UpdateDateColumn()")
        lines.append("  updatedAt!: Date;")
        lines.append("}")
        
        return "\n".join(lines)
    
    def _generate_ts_interface(self, name: str, fields: List[Field]) -> str:
        """Generate TypeScript interface"""
        lines = [
            f"export interface {name} {{",
        ]
        
        for field in fields:
            optional = "?" if not field.required else ""
            type_str = self.map_type(field.type)
            
            if field.description:
                lines.append(f"  /** {field.description} */")
            lines.append(f"  {field.name}{optional}: {type_str};")
        
        lines.append("}")
        lines.append("")
        
        # Create type
        create_fields = [f for f in fields if f.required]
        if create_fields:
            lines.append(f"export type Create{name} = Omit<{name}, 'id' | 'createdAt' | 'updatedAt'>;")
        
        lines.append(f"export type Update{name} = Partial<Create{name}>;")
        
        return "\n".join(lines)
    
    def generate_api_endpoint(self, path: str, method: str,
                              params: List[Field], response_type: FieldType) -> str:
        """Generate NestJS controller endpoint"""
        method_decorator = method.capitalize()
        handler_name = f"{method.lower()}{self._path_to_handler_name(path)}"
        
        lines = [
            f"  @{method_decorator}('{path}')",
        ]
        
        # Add parameter decorators
        for param in params:
            if param.name in path:
                lines.append(f"  async {handler_name}(@Param('{param.name}') {param.name}: {self.map_type(param.type)})")
            else:
                lines.append(f"  async {handler_name}(@Body() body: any)")
        
        if not params:
            lines.append(f"  async {handler_name}()")
        
        return_type = self.map_type(response_type)
        lines[-1] += f": Promise<{return_type}> " + "{"
        lines.append("    // TODO: Implement")
        lines.append("    throw new Error('Not implemented');")
        lines.append("  }")
        
        return "\n".join(lines)
    
    def generate_test(self, target: Union[Class, Method]) -> str:
        """Generate Jest test"""
        lines = [
            "import { Test, TestingModule } from '@nestjs/testing';",
            "import request from 'supertest';",
            "",
        ]
        
        if isinstance(target, Class):
            lines.append(f"import {{ {target.name} }} from './{target.name}';")
            lines.append("")
            lines.append(f"describe('{target.name}', () => {{")
            lines.append("  let service: {};".format(target.name))
            lines.append("")
            lines.append("  beforeEach(async () => {")
            lines.append("    const module: TestingModule = await Test.createTestingModule({")
            lines.append(f"      providers: [{target.name}],")
            lines.append("    }).compile();")
            lines.append("")
            lines.append(f"    service = module.get<{target.name}>({target.name});")
            lines.append("  });")
            lines.append("")
            
            for method in target.methods:
                lines.append(f"  describe('{method.name}', () => {{")
                lines.append(f"    it('should {method.name} successfully', async () => {{")
                lines.append("      // Arrange")
                lines.append("")
                lines.append("      // Act")
                params = ", ".join([f"'test_{p.name}'" for p in method.params])
                lines.append(f"      const result = await service.{method.name}({params});")
                lines.append("")
                lines.append("      // Assert")
                lines.append("      expect(result).toBeDefined();")
                lines.append("    });")
                lines.append("  });")
            
            lines.append("});")
        
        return "\n".join(lines)
    
    def _get_validator_decorator(self, field: Field) -> str:
        """Get class-validator decorator for field"""
        decorators = {
            FieldType.STRING: "@IsString()",
            FieldType.INTEGER: "@IsNumber()",
            FieldType.FLOAT: "@IsNumber()",
            FieldType.BOOLEAN: "@IsBoolean()",
            FieldType.DATETIME: "@IsDate()",
            FieldType.DATE: "@IsDate()",
        }
        return decorators.get(field.type, "")
    
    def _get_typeorm_type(self, field_type: FieldType) -> str:
        """Get TypeORM column type"""
        type_map = {
            FieldType.STRING: ": 'varchar'",
            FieldType.INTEGER: ": 'int'",
            FieldType.FLOAT: ": 'float'",
            FieldType.BOOLEAN: ": 'boolean'",
            FieldType.DATETIME: "",
            FieldType.DATE: ": 'date'",
            FieldType.TEXT: ": 'text'",
        }
        return type_map.get(field_type, "")
    
    def _ts_default(self, value: Any) -> str:
        """Convert Python default to TS default"""
        if value is None:
            return "undefined"
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
        return f"""async create(data: Create{model_name}Dto): Promise<{model_name}> {{
  const entity = this.repository.create(data);
  return await this.repository.save(entity);
}}"""
    
    def _generate_read_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""async findById(id: number): Promise<{model_name} | null> {{
  return await this.repository.findOne({{ where: {{ id }} }});
}}"""
    
    def _generate_update_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""async update(id: number, data: Update{model_name}Dto): Promise<{model_name}> {{
  await this.repository.update(id, data);
  return await this.findById(id);
}}"""
    
    def _generate_delete_method(self, model_name: str) -> str:
        return f"""async delete(id: number): Promise<boolean> {{
  const result = await this.repository.delete(id);
  return result.affected > 0;
}}"""
    
    def _generate_list_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""async findAll(options: {{ page?: number; limit?: number }} = {{}}): Promise<{{ items: {model_name}[]; total: number }}> {{
  const {{ page = 1, limit = 10 }} = options;
  const [items, total] = await this.repository.findAndCount({{
    skip: (page - 1) * limit,
    take: limit,
  }});
  return {{ items, total }};
}}"""
