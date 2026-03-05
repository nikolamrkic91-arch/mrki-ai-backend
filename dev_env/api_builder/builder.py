#!/usr/bin/env python3
"""
Mrki API Builder
Builds API endpoints and generates server/client code
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum


class HTTPMethod(Enum):
    GET = "get"
    POST = "post"
    PUT = "put"
    PATCH = "patch"
    DELETE = "delete"
    HEAD = "head"
    OPTIONS = "options"


class ParameterLocation(Enum):
    QUERY = "query"
    PATH = "path"
    HEADER = "header"
    COOKIE = "cookie"
    BODY = "body"


@dataclass
class Parameter:
    """API parameter definition"""
    name: str
    location: ParameterLocation
    type: str
    required: bool = False
    description: str = ""
    default: Any = None
    example: Any = None
    enum: List[str] = field(default_factory=list)


@dataclass
class Response:
    """API response definition"""
    status_code: int
    description: str
    content_type: str = "application/json"
    schema: Optional[Dict[str, Any]] = None
    example: Any = None


@dataclass
class Endpoint:
    """API endpoint definition"""
    path: str
    method: HTTPMethod
    summary: str = ""
    description: str = ""
    operation_id: str = ""
    tags: List[str] = field(default_factory=list)
    parameters: List[Parameter] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: List[Response] = field(default_factory=list)
    security: List[Dict[str, List[str]]] = field(default_factory=list)
    deprecated: bool = False
    
    def __post_init__(self):
        if not self.operation_id:
            self.operation_id = f"{self.method.value}_{self.path.replace('/', '_').replace('{', '').replace('}', '')}"


@dataclass
class APISpec:
    """Complete API specification"""
    title: str
    version: str
    description: str = ""
    servers: List[Dict[str, str]] = field(default_factory=list)
    endpoints: List[Endpoint] = field(default_factory=list)
    components: Dict[str, Any] = field(default_factory=dict)
    security_schemes: Dict[str, Any] = field(default_factory=dict)


class APIBuilder:
    """Main API builder class"""
    
    def __init__(self, output_path: str = "."):
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.spec = APISpec(
            title="API",
            version="1.0.0",
            servers=[{"url": "http://localhost:3000", "description": "Local server"}],
        )
    
    def set_info(self, title: str, version: str, description: str = "") -> "APIBuilder":
        """Set API information"""
        self.spec.title = title
        self.spec.version = version
        self.spec.description = description
        return self
    
    def add_server(self, url: str, description: str = "") -> "APIBuilder":
        """Add server URL"""
        self.spec.servers.append({"url": url, "description": description})
        return self
    
    def add_endpoint(self, endpoint: Endpoint) -> "APIBuilder":
        """Add an endpoint"""
        self.spec.endpoints.append(endpoint)
        return self
    
    def add_security_scheme(self, name: str, scheme_type: str, 
                            scheme: str = "bearer", bearer_format: str = "JWT") -> "APIBuilder":
        """Add security scheme"""
        self.spec.security_schemes[name] = {
            "type": scheme_type,
            "scheme": scheme,
            "bearerFormat": bearer_format,
        }
        return self
    
    def add_component_schema(self, name: str, schema: Dict[str, Any]) -> "APIBuilder":
        """Add component schema"""
        if "schemas" not in self.spec.components:
            self.spec.components["schemas"] = {}
        self.spec.components["schemas"][name] = schema
        return self
    
    def generate_openapi(self) -> Dict[str, Any]:
        """Generate OpenAPI 3.0 specification"""
        spec = {
            "openapi": "3.0.3",
            "info": {
                "title": self.spec.title,
                "version": self.spec.version,
                "description": self.spec.description,
            },
            "servers": self.spec.servers,
            "paths": self._build_paths(),
            "components": self.spec.components,
        }
        
        if self.spec.security_schemes:
            spec["components"]["securitySchemes"] = self.spec.security_schemes
        
        return spec
    
    def _build_paths(self) -> Dict[str, Any]:
        """Build paths section of OpenAPI spec"""
        paths = {}
        
        for endpoint in self.spec.endpoints:
            if endpoint.path not in paths:
                paths[endpoint.path] = {}
            
            path_item = {
                "summary": endpoint.summary,
                "description": endpoint.description,
                "operationId": endpoint.operation_id,
                "tags": endpoint.tags,
            }
            
            # Parameters
            if endpoint.parameters:
                path_item["parameters"] = [
                    {
                        "name": p.name,
                        "in": p.location.value,
                        "required": p.required,
                        "description": p.description,
                        "schema": {"type": p.type},
                    }
                    for p in endpoint.parameters
                ]
            
            # Request body
            if endpoint.request_body:
                path_item["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": endpoint.request_body,
                        }
                    }
                }
            
            # Responses
            path_item["responses"] = {}
            for response in endpoint.responses:
                response_spec = {
                    "description": response.description,
                }
                if response.schema:
                    response_spec["content"] = {
                        response.content_type: {
                            "schema": response.schema,
                        }
                    }
                path_item["responses"][str(response.status_code)] = response_spec
            
            # Security
            if endpoint.security:
                path_item["security"] = endpoint.security
            
            if endpoint.deprecated:
                path_item["deprecated"] = True
            
            paths[endpoint.path][endpoint.method.value] = path_item
        
        return paths
    
    def save_openapi(self, filename: str = "openapi.json") -> Path:
        """Save OpenAPI spec to file"""
        spec = self.generate_openapi()
        filepath = self.output_path / filename
        filepath.write_text(json.dumps(spec, indent=2))
        return filepath
    
    def generate_postman_collection(self) -> Dict[str, Any]:
        """Generate Postman collection"""
        collection = {
            "info": {
                "name": self.spec.title,
                "description": self.spec.description,
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": [],
        }
        
        # Group by tags
        tag_groups = {}
        for endpoint in self.spec.endpoints:
            tag = endpoint.tags[0] if endpoint.tags else "Default"
            if tag not in tag_groups:
                tag_groups[tag] = []
            tag_groups[tag].append(endpoint)
        
        for tag, endpoints in tag_groups.items():
            folder = {
                "name": tag,
                "item": [],
            }
            
            for endpoint in endpoints:
                request = {
                    "name": endpoint.summary or endpoint.operation_id,
                    "request": {
                        "method": endpoint.method.value.upper(),
                        "header": [],
                        "url": {
                            "raw": f"{{{{base_url}}}}{endpoint.path}",
                            "host": ["{{base_url}}"],
                            "path": endpoint.path.strip("/").split("/"),
                        },
                    },
                }
                
                # Add query parameters
                query_params = [p for p in endpoint.parameters if p.location == ParameterLocation.QUERY]
                if query_params:
                    request["request"]["url"]["query"] = [
                        {"key": p.name, "value": p.example or ""} for p in query_params
                    ]
                
                # Add body
                if endpoint.request_body:
                    request["request"]["body"] = {
                        "mode": "raw",
                        "raw": json.dumps(endpoint.request_body.get("example", {}), indent=2),
                        "options": {
                            "raw": {"language": "json"}
                        }
                    }
                
                folder["item"].append(request)
            
            collection["item"].append(folder)
        
        # Add variables
        collection["variable"] = [
            {"key": "base_url", "value": self.spec.servers[0]["url"] if self.spec.servers else "http://localhost:3000"},
        ]
        
        return collection
    
    def save_postman_collection(self, filename: str = "postman_collection.json") -> Path:
        """Save Postman collection to file"""
        collection = self.generate_postman_collection()
        filepath = self.output_path / filename
        filepath.write_text(json.dumps(collection, indent=2))
        return filepath
    
    def generate_client_sdk(self, language: str, output_dir: str) -> Path:
        """Generate client SDK for specified language"""
        generators = {
            "typescript": self._generate_typescript_sdk,
            "javascript": self._generate_javascript_sdk,
            "python": self._generate_python_sdk,
            "go": self._generate_go_sdk,
        }
        
        generator = generators.get(language)
        if not generator:
            raise ValueError(f"Unsupported language: {language}")
        
        return generator(output_dir)
    
    def _generate_typescript_sdk(self, output_dir: str) -> Path:
        """Generate TypeScript client SDK"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        lines = [
            "import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';",
            "",
            f"// {self.spec.title} Client SDK",
            f"// Version: {self.spec.version}",
            "",
            f"export class {self.spec.title.replace(' ', '')}Client {{",
            "  private client: AxiosInstance;",
            "",
            "  constructor(baseURL: string) {",
            "    this.client = axios.create({ baseURL });",
            "  }",
            "",
        ]
        
        for endpoint in self.spec.endpoints:
            method_name = endpoint.operation_id
            params = [f"{p.name}: {self._ts_type(p.type)}" for p in endpoint.parameters]
            
            lines.append(f"  async {method_name}({', '.join(params)}): Promise<any> {{")
            lines.append(f"    const response = await this.client.{endpoint.method.value}('{endpoint.path}');")
            lines.append("    return response.data;")
            lines.append("  }")
            lines.append("")
        
        lines.append("}")
        lines.append("")
        lines.append("export default {}Client;".format(self.spec.title.replace(' ', '')))
        
        filepath = output_path / "client.ts"
        filepath.write_text("\n".join(lines))
        return filepath
    
    def _generate_javascript_sdk(self, output_dir: str) -> Path:
        """Generate JavaScript client SDK"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        lines = [
            "const axios = require('axios');",
            "",
            f"// {self.spec.title} Client SDK",
            f"// Version: {self.spec.version}",
            "",
            f"class {self.spec.title.replace(' ', '')}Client {{",
            "  constructor(baseURL) {",
            "    this.client = axios.create({ baseURL });",
            "  }",
            "",
        ]
        
        for endpoint in self.spec.endpoints:
            method_name = endpoint.operation_id
            params = [p.name for p in endpoint.parameters]
            
            lines.append(f"  async {method_name}({', '.join(params)}) {{")
            lines.append(f"    const response = await this.client.{endpoint.method.value}('{endpoint.path}');")
            lines.append("    return response.data;")
            lines.append("  }")
            lines.append("")
        
        lines.append("}")
        lines.append("")
        lines.append("module.exports = {}Client;".format(self.spec.title.replace(' ', '')))
        
        filepath = output_path / "client.js"
        filepath.write_text("\n".join(lines))
        return filepath
    
    def _generate_python_sdk(self, output_dir: str) -> Path:
        """Generate Python client SDK"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        lines = [
            "import requests",
            "from typing import Optional, Dict, Any",
            "",
            f'"""{self.spec.title} Client SDK',
            f'Version: {self.spec.version}',
            '"""',
            "",
            f"class {self.spec.title.replace(' ', '')}Client:",
            '    """API Client"""',
            "",
            "    def __init__(self, base_url: str):",
            "        self.base_url = base_url",
            "        self.session = requests.Session()",
            "",
        ]
        
        for endpoint in self.spec.endpoints:
            method_name = endpoint.operation_id
            params = [f"{p.name}: {self._py_type(p.type)}" for p in endpoint.parameters]
            params_str = ", ".join(["self"] + params)
            
            lines.append(f"    def {method_name}({params_str}) -> Dict[str, Any]:")
            lines.append(f'        """{endpoint.summary or method_name}"""')
            lines.append(f"        response = self.session.{endpoint.method.value}(f'{{self.base_url}}{endpoint.path}')")
            lines.append("        response.raise_for_status()")
            lines.append("        return response.json()")
            lines.append("")
        
        filepath = output_path / "client.py"
        filepath.write_text("\n".join(lines))
        return filepath
    
    def _generate_go_sdk(self, output_dir: str) -> Path:
        """Generate Go client SDK"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        package_name = self.spec.title.lower().replace(" ", "")
        
        lines = [
            f"package {package_name}",
            "",
            "import (",
            '    "net/http"',
            '    "encoding/json"',
            '    "fmt"',
            ")",
            "",
            f"// {self.spec.title} Client",\n            f"type Client struct {{",
            "    baseURL string",
            "    httpClient *http.Client",
            "}",
            "",
            "// NewClient creates a new API client",
            "func NewClient(baseURL string) *Client {",
            "    return &Client{",
            "        baseURL: baseURL,",
            "        httpClient: &http.Client{},",
            "    }",
            "}",
            "",
        ]
        
        for endpoint in self.spec.endpoints:
            method_name = self._to_pascal_case(endpoint.operation_id)
            
            lines.append(f"// {method_name} makes a {endpoint.method.value.upper()} request")
            lines.append(f"func (c *Client) {method_name}() (map[string]interface{{}}, error) {{")
            lines.append(f"    url := fmt.Sprintf(\"%s{endpoint.path}\", c.baseURL)")
            lines.append(f"    req, err := http.NewRequest(\"{endpoint.method.value.upper()}\", url, nil)")
            lines.append("    if err != nil {")
            lines.append("        return nil, err")
            lines.append("    }")
            lines.append("")
            lines.append("    resp, err := c.httpClient.Do(req)")
            lines.append("    if err != nil {")
            lines.append("        return nil, err")
            lines.append("    }")
            lines.append("    defer resp.Body.Close()")
            lines.append("")
            lines.append("    var result map[string]interface{}")
            lines.append("    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {")
            lines.append("        return nil, err")
            lines.append("    }")
            lines.append("    return result, nil")
            lines.append("}")
            lines.append("")
        
        filepath = output_path / "client.go"
        filepath.write_text("\n".join(lines))
        return filepath
    
    def _ts_type(self, api_type: str) -> str:
        """Convert API type to TypeScript type"""
        type_map = {
            "string": "string",
            "integer": "number",
            "number": "number",
            "boolean": "boolean",
            "array": "any[]",
            "object": "Record<string, any>",
        }
        return type_map.get(api_type, "any")
    
    def _py_type(self, api_type: str) -> str:
        """Convert API type to Python type"""
        type_map = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "array": "list",
            "object": "dict",
        }
        return type_map.get(api_type, "Any")
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert to PascalCase"""
        parts = name.replace("_", " ").replace("-", " ").split()
        return "".join(p.capitalize() for p in parts)


# Convenience functions for common API patterns
def create_crud_endpoints(resource_name: str, base_path: str = "") -> List[Endpoint]:
    """Create standard CRUD endpoints for a resource"""
    path = f"{base_path}/{resource_name.lower()}s"
    
    return [
        Endpoint(
            path=path,
            method=HTTPMethod.GET,
            summary=f"List all {resource_name}s",
            operation_id=f"list{resource_name}s",
            tags=[resource_name],
            parameters=[
                Parameter("page", ParameterLocation.QUERY, "integer", False, "Page number", 1),
                Parameter("limit", ParameterLocation.QUERY, "integer", False, "Items per page", 10),
            ],
            responses=[
                Response(200, "List of items", schema={"type": "array"}),
            ],
        ),
        Endpoint(
            path=path,
            method=HTTPMethod.POST,
            summary=f"Create a new {resource_name}",
            operation_id=f"create{resource_name}",
            tags=[resource_name],
            request_body={"$ref": f"#/components/schemas/Create{resource_name}"},
            responses=[
                Response(201, "Created item", schema={"$ref": f"#/components/schemas/{resource_name}"}),
                Response(400, "Invalid input"),
            ],
        ),
        Endpoint(
            path=f"{path}/{{id}}",
            method=HTTPMethod.GET,
            summary=f"Get a {resource_name} by ID",
            operation_id=f"get{resource_name}",
            tags=[resource_name],
            parameters=[
                Parameter("id", ParameterLocation.PATH, "string", True, f"{resource_name} ID"),
            ],
            responses=[
                Response(200, "Item found", schema={"$ref": f"#/components/schemas/{resource_name}"}),
                Response(404, "Item not found"),
            ],
        ),
        Endpoint(
            path=f"{path}/{{id}}",
            method=HTTPMethod.PUT,
            summary=f"Update a {resource_name}",
            operation_id=f"update{resource_name}",
            tags=[resource_name],
            parameters=[
                Parameter("id", ParameterLocation.PATH, "string", True, f"{resource_name} ID"),
            ],
            request_body={"$ref": f"#/components/schemas/Update{resource_name}"},
            responses=[
                Response(200, "Updated item", schema={"$ref": f"#/components/schemas/{resource_name}"}),
                Response(404, "Item not found"),
            ],
        ),
        Endpoint(
            path=f"{path}/{{id}}",
            method=HTTPMethod.DELETE,
            summary=f"Delete a {resource_name}",
            operation_id=f"delete{resource_name}",
            tags=[resource_name],
            parameters=[
                Parameter("id", ParameterLocation.PATH, "string", True, f"{resource_name} ID"),
            ],
            responses=[
                Response(204, "Item deleted"),
                Response(404, "Item not found"),
            ],
        ),
    ]


if __name__ == "__main__":
    # Example usage
    builder = APIBuilder()
    
    builder.set_info(
        title="My API",
        version="1.0.0",
        description="A sample API built with Mrki"
    )
    
    # Add CRUD endpoints
    for endpoint in create_crud_endpoints("User"):
        builder.add_endpoint(endpoint)
    
    # Add component schemas
    builder.add_component_schema("User", {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "email": {"type": "string"},
            "name": {"type": "string"},
        },
        "required": ["id", "email"],
    })
    
    # Save OpenAPI spec
    builder.save_openapi()
    
    # Save Postman collection
    builder.save_postman_collection()
    
    print("API spec generated successfully!")
