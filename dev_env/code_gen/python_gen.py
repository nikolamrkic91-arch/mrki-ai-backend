#!/usr/bin/env python3
"""
Mrki Python Code Generator
Generates Python code including FastAPI, Django, and general Python
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from .generator import CodeGenerator, Class, Method, Field, Module, FieldType


class PythonGenerator(CodeGenerator):
    """Python code generator"""
    
    def __init__(self, output_path: str = ".", framework: str = "fastapi"):
        super().__init__(output_path)
        self.framework = framework  # fastapi, django, flask, vanilla
    
    def get_file_extension(self) -> str:
        return ".py"
    
    def _get_type_map(self) -> Dict[FieldType, str]:
        return {
            FieldType.STRING: "str",
            FieldType.INTEGER: "int",
            FieldType.FLOAT: "float",
            FieldType.BOOLEAN: "bool",
            FieldType.DATETIME: "datetime",
            FieldType.DATE: "date",
            FieldType.UUID: "UUID",
            FieldType.ARRAY: "List",
            FieldType.OBJECT: "Dict[str, Any]",
            FieldType.ANY: "Any",
        }
    
    def generate_class(self, class_def: Class) -> str:
        """Generate Python class"""
        lines = []
        
        # Docstring
        if class_def.description:
            lines.append(f'"""{class_def.description}"""')
        
        # Class definition
        inheritance = f"({class_def.extends})" if class_def.extends else ""
        abstract = "@abstractmethod\n" if class_def.is_abstract else ""
        lines.append(f"{abstract}class {class_def.name}{inheritance}:")
        
        # __init__ method
        init_params = ["self"] + [self._field_to_param(f) for f in class_def.fields]
        lines.append(f"    def __init__({', '.join(init_params)}):")
        
        for field in class_def.fields:
            default = f" = {field.default}" if field.default is not None else ""
            lines.append(f"        self.{field.name} = {field.name}{default}")
        
        # Other methods
        for method in class_def.methods:
            lines.append("")
            lines.append(self._indent(self.generate_function(method)))
        
        return "\n".join(lines)
    
    def generate_function(self, method: Method) -> str:
        """Generate Python function/method"""
        lines = []
        
        # Docstring
        if method.description:
            lines.append(f'"""{method.description}"""')
        
        # Function definition
        async_prefix = "async " if method.is_async else ""
        static_prefix = "@staticmethod\n" if method.is_static else ""
        private_prefix = "_" if method.is_private else ""
        
        params = ["self"] if not method.is_static else []
        params.extend([self._field_to_param(p) for p in method.params])
        
        return_type = f" -> {self.map_type(method.return_type)}" if method.return_type else ""
        
        lines.append(f"{static_prefix}{async_prefix}def {private_prefix}{method.name}({', '.join(params)}){return_type}:")
        
        # Function body
        if method.body:
            lines.append(self._indent(method.body))
        else:
            lines.append("    pass")
        
        return "\n".join(lines)
    
    def generate_module(self, module: Module) -> str:
        """Generate complete Python module"""
        lines = []
        
        # Imports
        lines.append("from typing import List, Dict, Optional, Any")
        lines.append("from datetime import datetime, date")
        lines.append("from uuid import UUID")
        
        if self.framework == "fastapi":
            lines.append("from fastapi import FastAPI, HTTPException, Depends")
            lines.append("from pydantic import BaseModel")
            lines.append("from sqlalchemy import Column, Integer, String, DateTime, ForeignKey")
        elif self.framework == "django":
            lines.append("from django.db import models")
            lines.append("from rest_framework import serializers, viewsets")
        elif self.framework == "flask":
            lines.append("from flask import Flask, request, jsonify")
        
        # Module docstring
        lines.append(f'\n"""{module.name} module"""\n')
        
        # Custom imports
        for imp in module.imports:
            lines.append(imp)
        
        # Functions
        for func in module.functions:
            lines.append("")
            lines.append(self.generate_function(func))
        
        # Classes
        for cls in module.classes:
            lines.append("")
            lines.append(self.generate_class(cls))
        
        # Exports
        if module.exports:
            lines.append(f"\n__all__ = {module.exports}")
        
        return "\n".join(lines)
    
    def generate_model(self, name: str, fields: List[Field]) -> str:
        """Generate Python data model"""
        if self.framework == "fastapi":
            return self._generate_pydantic_model(name, fields)
        elif self.framework == "django":
            return self._generate_django_model(name, fields)
        elif self.framework == "sqlalchemy":
            return self._generate_sqlalchemy_model(name, fields)
        else:
            return self._generate_dataclass_model(name, fields)
    
    def _generate_pydantic_model(self, name: str, fields: List[Field]) -> str:
        """Generate Pydantic model for FastAPI"""
        lines = [
            f"class {name}(BaseModel):",
            f'    """{name} model"""',
            ""
        ]
        
        for field in fields:
            type_str = self.map_type(field.type)
            if not field.required:
                type_str = f"Optional[{type_str}]"
            
            default_str = f" = {field.default}" if field.default is not None else ""
            if not field.required and field.default is None:
                default_str = " = None"
            
            desc = f'  # {field.description}' if field.description else ""
            lines.append(f"    {field.name}: {type_str}{default_str}{desc}")
        
        lines.append("")
        lines.append("    class Config:")
        lines.append("        from_attributes = True")
        
        return "\n".join(lines)
    
    def _generate_django_model(self, name: str, fields: List[Field]) -> str:
        """Generate Django ORM model"""
        lines = [
            f"class {name}(models.Model):",
            f'    """{name} model"""',
            ""
        ]
        
        django_field_map = {
            FieldType.STRING: "CharField(max_length=255)",
            FieldType.INTEGER: "IntegerField()",
            FieldType.FLOAT: "FloatField()",
            FieldType.BOOLEAN: "BooleanField(default=False)",
            FieldType.DATETIME: "DateTimeField(auto_now_add=True)",
            FieldType.DATE: "DateField()",
            FieldType.UUID: "UUIDField(default=uuid.uuid4)",
            FieldType.TEXT: "TextField()",
        }
        
        for field in fields:
            field_type = django_field_map.get(field.type, "CharField(max_length=255)")
            
            if not field.required:
                field_type = field_type.replace(")", "", 1) + ", null=True, blank=True)"
            
            if field.unique:
                field_type = field_type.replace(")", "", 1) + ", unique=True)"
            
            lines.append(f"    {field.name} = models.{field_type}")
        
        lines.append("")
        lines.append("    class Meta:")
        lines.append(f"        db_table = '{name.lower()}s'")
        lines.append("        ordering = ['-created_at']")
        
        lines.append("")
        lines.append("    def __str__(self):")
        first_field = fields[0].name if fields else "id"
        lines.append(f"        return str(self.{first_field})")
        
        return "\n".join(lines)
    
    def _generate_sqlalchemy_model(self, name: str, fields: List[Field]) -> str:
        """Generate SQLAlchemy model"""
        lines = [
            f"class {name}(Base):",
            f'    """{name} model"""',
            f'    __tablename__ = "{name.lower()}s"',
            "",
            "    id = Column(Integer, primary_key=True, index=True)",
        ]
        
        for field in fields:
            type_str = self._get_sqlalchemy_type(field.type)
            params = ["index=True"] if field.indexed else []
            
            if field.unique:
                params.append("unique=True")
            if not field.required:
                params.append("nullable=True")
            
            param_str = ", " + ", ".join(params) if params else ""
            lines.append(f"    {field.name} = Column({type_str}{param_str})")
        
        lines.append("    created_at = Column(DateTime(timezone=True), server_default=func.now())")
        
        return "\n".join(lines)
    
    def _generate_dataclass_model(self, name: str, fields: List[Field]) -> str:
        """Generate Python dataclass"""
        lines = [
            "from dataclasses import dataclass, field",
            "",
            "@dataclass",
            f"class {name}:",
            f'    """{name} data class"""',
            ""
        ]
        
        for field in fields:
            type_str = self.map_type(field.type)
            default_str = ""
            
            if not field.required:
                type_str = f"Optional[{type_str}]"
                default_str = " = None"
            elif field.default is not None:
                default_str = f" = {field.default}"
            
            lines.append(f"    {field.name}: {type_str}{default_str}")
        
        return "\n".join(lines)
    
    def generate_api_endpoint(self, path: str, method: str,
                              params: List[Field], response_type: FieldType) -> str:
        """Generate FastAPI endpoint"""
        method_lower = method.lower()
        
        lines = [
            f"@{self.framework}.route('{path}', methods=['{method.upper()}'])",
            f"async def {method_lower}_{path.replace('/', '_').strip('_')}(",
]
        
        # Add parameters
        for param in params:
            type_str = self.map_type(param.type)
            if not param.required:
                type_str = f"Optional[{type_str}] = None"
            lines.append(f"    {param.name}: {type_str},")
        
        lines.append(f") -> {self.map_type(response_type)}:")
        lines.append(f'    """Handle {method.upper()} {path}"""')
        lines.append("    # TODO: Implement endpoint logic")
        lines.append("    pass")
        
        return "\n".join(lines)
    
    def generate_test(self, target: Union[Class, Method]) -> str:
        """Generate pytest test"""
        lines = [
            "import pytest",
            "from unittest.mock import Mock, patch",
            "",
        ]
        
        if isinstance(target, Class):
            lines.append(f"from . import {target.name}")
            lines.append("")
            lines.append(f"class Test{target.name}:")
            lines.append(f'    """Tests for {target.name}"""')
            lines.append("")
            
            for method in target.methods:
                lines.append(f"    def test_{method.name}(self):")
                lines.append(f'        """Test {method.name} method"""')
                lines.append("        # Arrange")
                lines.append(f"        instance = {target.name}()")
                lines.append("")
                lines.append("        # Act")
                lines.append(f"        result = instance.{method.name}()")
                lines.append("")
                lines.append("        # Assert")
                lines.append("        assert result is not None")
                lines.append("")
        
        elif isinstance(target, Method):
            lines.append(f"def test_{target.name}():")
            lines.append(f'    """Test {target.name} function"""')
            lines.append("    # Arrange")
            lines.append("")
            lines.append("    # Act")
            lines.append(f"    result = {target.name}()")
            lines.append("")
            lines.append("    # Assert")
            lines.append("    assert result is not None")
        
        return "\n".join(lines)
    
    def _field_to_param(self, field: Field) -> str:
        """Convert field to function parameter"""
        type_str = self.map_type(field.type)
        if not field.required:
            type_str = f"Optional[{type_str}]"
        
        default_str = ""
        if field.default is not None:
            default_str = f" = {field.default}"
        elif not field.required:
            default_str = " = None"
        
        return f"{field.name}: {type_str}{default_str}"
    
    def _get_sqlalchemy_type(self, field_type: FieldType) -> str:
        """Get SQLAlchemy column type"""
        type_map = {
            FieldType.STRING: "String",
            FieldType.INTEGER: "Integer",
            FieldType.FLOAT: "Float",
            FieldType.BOOLEAN: "Boolean",
            FieldType.DATETIME: "DateTime(timezone=True)",
            FieldType.DATE: "Date",
            FieldType.UUID: "UUID",
            FieldType.TEXT: "Text",
        }
        return type_map.get(field_type, "String")
    
    def _indent(self, code: str, level: int = 1) -> str:
        """Indent code"""
        indent = "    " * level
        return "\n".join(indent + line if line.strip() else line for line in code.split("\n"))
    
    # CRUD methods
    def _generate_create_method(self, model_name: str, fields: List[Field]) -> str:
        lines = [
            f"async def create_{model_name.lower()}(",
            f"    db: Session,",
            f"    obj_in: {model_name}Create",
            f") -> {model_name}:",
            f'    """Create new {model_name}"""',
            f"    db_obj = {model_name}(**obj_in.dict())",
            "    db.add(db_obj)",
            "    await db.commit()",
            "    await db.refresh(db_obj)",
            "    return db_obj",
        ]
        return "\n".join(lines)
    
    def _generate_read_method(self, model_name: str, fields: List[Field]) -> str:
        lines = [
            f"async def get_{model_name.lower()}(",
            f"    db: Session,",
            f"    {model_name.lower()}_id: int",
            f") -> Optional[{model_name}]:",
            f'    """Get {model_name} by ID"""',
            f"    return db.query({model_name}).filter({model_name}.id == {model_name.lower()}_id).first()",
        ]
        return "\n".join(lines)
    
    def _generate_update_method(self, model_name: str, fields: List[Field]) -> str:
        lines = [
            f"async def update_{model_name.lower()}(",
            f"    db: Session,",
            f"    db_obj: {model_name},",
            f"    obj_in: {model_name}Update",
            f") -> {model_name}:",
            f'    """Update {model_name}"""',
            "    update_data = obj_in.dict(exclude_unset=True)",
            "    for field, value in update_data.items():",
            "        setattr(db_obj, field, value)",
            "    db.add(db_obj)",
            "    await db.commit()",
            "    await db.refresh(db_obj)",
            "    return db_obj",
        ]
        return "\n".join(lines)
    
    def _generate_delete_method(self, model_name: str) -> str:
        lines = [
            f"async def delete_{model_name.lower()}(",
            f"    db: Session,",
            f"    {model_name.lower()}_id: int",
            f") -> bool:",
            f'    """Delete {model_name}"""',
            f"    obj = await get_{model_name.lower()}(db, {model_name.lower()}_id)",
            "    if obj:",
            "        await db.delete(obj)",
            "        await db.commit()",
            "        return True",
            "    return False",
        ]
        return "\n".join(lines)
    
    def _generate_list_method(self, model_name: str, fields: List[Field]) -> str:
        lines = [
            f"async def list_{model_name.lower()}s(",
            f"    db: Session,",
            f"    skip: int = 0,",
            f"    limit: int = 100,",
            f") -> List[{model_name}]:",
            f'    """List {model_name}s with pagination"""',
            f"    return db.query({model_name}).offset(skip).limit(limit).all()",
        ]
        return "\n".join(lines)
