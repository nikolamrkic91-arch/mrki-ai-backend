#!/usr/bin/env python3
"""
Mrki Base Code Generator
Abstract base class for all language-specific generators
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class FieldType(Enum):
    """Common field types across languages"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"
    UUID = "uuid"
    ARRAY = "array"
    OBJECT = "object"
    ANY = "any"


@dataclass
class Field:
    """Field definition for code generation"""
    name: str
    type: FieldType
    required: bool = True
    default: Any = None
    description: str = ""
    nullable: bool = False
    unique: bool = False
    indexed: bool = False


@dataclass
class Method:
    """Method definition for code generation"""
    name: str
    params: List[Field]
    return_type: Optional[FieldType]
    body: str = ""
    description: str = ""
    is_async: bool = False
    is_static: bool = False
    is_private: bool = False


@dataclass
class Class:
    """Class definition for code generation"""
    name: str
    fields: List[Field]
    methods: List[Method]
    description: str = ""
    extends: Optional[str] = None
    implements: List[str] = None
    is_abstract: bool = False
    
    def __post_init__(self):
        if self.implements is None:
            self.implements = []


@dataclass
class Module:
    """Module/Package definition"""
    name: str
    classes: List[Class]
    functions: List[Method]
    imports: List[str] = None
    exports: List[str] = None
    
    def __post_init__(self):
        if self.imports is None:
            self.imports = []
        if self.exports is None:
            self.exports = []


class CodeGenerator(ABC):
    """Abstract base class for code generators"""
    
    def __init__(self, output_path: str = "."):
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def generate_class(self, class_def: Class) -> str:
        """Generate class code"""
        pass
    
    @abstractmethod
    def generate_function(self, method: Method) -> str:
        """Generate function/method code"""
        pass
    
    @abstractmethod
    def generate_module(self, module: Module) -> str:
        """Generate complete module code"""
        pass
    
    @abstractmethod
    def generate_model(self, name: str, fields: List[Field]) -> str:
        """Generate data model (ORM/ODM)"""
        pass
    
    @abstractmethod
    def generate_api_endpoint(self, path: str, method: str, 
                              params: List[Field], response_type: FieldType) -> str:
        """Generate API endpoint handler"""
        pass
    
    @abstractmethod
    def generate_test(self, target: Union[Class, Method]) -> str:
        """Generate test code"""
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """Get file extension for this language"""
        pass
    
    def write_file(self, filename: str, content: str) -> Path:
        """Write generated code to file"""
        filepath = self.output_path / filename
        filepath.write_text(content)
        return filepath
    
    def map_type(self, field_type: FieldType, context: str = "default") -> str:
        """Map common type to language-specific type"""
        type_maps = self._get_type_map()
        return type_maps.get(field_type, "any")
    
    @abstractmethod
    def _get_type_map(self) -> Dict[FieldType, str]:
        """Get type mapping for this language"""
        pass
    
    def generate_crud(self, model_name: str, fields: List[Field]) -> Dict[str, str]:
        """Generate full CRUD operations for a model"""
        return {
            "model": self.generate_model(model_name, fields),
            "create": self._generate_create_method(model_name, fields),
            "read": self._generate_read_method(model_name, fields),
            "update": self._generate_update_method(model_name, fields),
            "delete": self._generate_delete_method(model_name),
            "list": self._generate_list_method(model_name, fields),
        }
    
    @abstractmethod
    def _generate_create_method(self, model_name: str, fields: List[Field]) -> str:
        pass
    
    @abstractmethod
    def _generate_read_method(self, model_name: str, fields: List[Field]) -> str:
        pass
    
    @abstractmethod
    def _generate_update_method(self, model_name: str, fields: List[Field]) -> str:
        pass
    
    @abstractmethod
    def _generate_delete_method(self, model_name: str) -> str:
        pass
    
    @abstractmethod
    def _generate_list_method(self, model_name: str, fields: List[Field]) -> str:
        pass
