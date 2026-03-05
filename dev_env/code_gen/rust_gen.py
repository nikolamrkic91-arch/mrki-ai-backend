#!/usr/bin/env python3
"""
Mrki Rust Code Generator
Generates Rust code with Actix-web and SQLx
"""

from typing import Dict, List, Optional, Any, Union
from .generator import CodeGenerator, Class, Method, Field, Module, FieldType


class RustGenerator(CodeGenerator):
    """Rust code generator"""
    
    def __init__(self, output_path: str = ".", framework: str = "actix"):
        super().__init__(output_path)
        self.framework = framework  # actix, axum, rocket
    
    def get_file_extension(self) -> str:
        return ".rs"
    
    def _get_type_map(self) -> Dict[FieldType, str]:
        return {
            FieldType.STRING: "String",
            FieldType.INTEGER: "i64",
            FieldType.FLOAT: "f64",
            FieldType.BOOLEAN: "bool",
            FieldType.DATETIME: "chrono::DateTime<chrono::Utc>",
            FieldType.DATE: "chrono::NaiveDate",
            FieldType.UUID: "uuid::Uuid",
            FieldType.ARRAY: "Vec<T>",
            FieldType.OBJECT: "serde_json::Value",
            FieldType.ANY: "serde_json::Value",
        }
    
    def generate_class(self, class_def: Class) -> str:
        """Generate Rust struct (class equivalent)"""
        lines = []
        
        # Derives
        lines.append("#[derive(Debug, Clone, Serialize, Deserialize)]")
        
        # Struct comment
        if class_def.description:
            lines.append(f"/// {class_def.description}")
        
        # Struct definition
        lines.append(f"pub struct {class_def.name} {{")
        
        for field in class_def.fields:
            type_str = self.map_type(field.type)
            if not field.required:
                type_str = f"Option<{type_str}>"
            
            serde_attr = f'#[serde(rename = "{field.name}")]'
            if field.description:
                lines.append(f"    /// {field.description}")
            lines.append(f"    {serde_attr}")
            lines.append(f"    pub {self._to_snake_case(field.name)}: {type_str},")
        
        lines.append("}")
        
        # Impl block
        if class_def.methods:
            lines.append("")
            lines.append(f"impl {class_def.name} {{")
            
            for method in class_def.methods:
                lines.append("")
                lines.append(self._indent(self.generate_function(method)))
            
            lines.append("}")
        
        return "\n".join(lines)
    
    def generate_function(self, method: Method) -> str:
        """Generate Rust function/method"""
        lines = []
        
        # Function comment
        if method.description:
            lines.append(f"/// {method.description}")
        
        # Function signature
        async_prefix = "async " if method.is_async else ""
        
        params_str = ", ".join([
            f"{self._to_snake_case(p.name)}: {self.map_type(p.type)}"
            for p in method.params
        ])
        
        return_type = ""
        if method.return_type:
            ret = self.map_type(method.return_type)
            return_type = f" -> {ret}"
            if method.is_async:
                return_type = f" -> impl std::future::Future<Output = {ret}>"
        elif method.is_async:
            return_type = " -> impl std::future::Future<Output = ()>"
        
        pub_prefix = "pub " if not method.is_private else ""
        
        lines.append(f"{pub_prefix}{async_prefix}fn {self._to_snake_case(method.name)}({params_str}){return_type} {{")
        
        # Function body
        if method.body:
            lines.append(self._indent(method.body))
        else:
            lines.append("    // TODO: Implement")
            lines.append("    unimplemented!()")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate_module(self, module: Module) -> str:
        """Generate complete Rust module"""
        lines = []
        
        # Module declaration
        lines.append(f"pub mod {self._to_snake_case(module.name)};")
        lines.append("")
        
        # Imports
        lines.append("use actix_web::{web, HttpResponse, Responder};")
        lines.append("use serde::{Deserialize, Serialize};")
        lines.append("use sqlx::PgPool;")
        lines.append("")
        
        # Custom imports
        for imp in module.imports:
            lines.append(imp)
        
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
        """Generate Rust/SQLx model"""
        lines = [
            "use chrono::{DateTime, Utc};",
            "use serde::{Deserialize, Serialize};",
            "use sqlx::FromRow;",
            "use uuid::Uuid;",
            "",
            f"/// {name} database model",
            "#[derive(Debug, Clone, FromRow, Serialize, Deserialize)]",
            f"pub struct {name} {{",
            "    pub id: Uuid,",
            "    pub created_at: DateTime<Utc>,",
            "    pub updated_at: DateTime<Utc>,",
        ]
        
        for field in fields:
            type_str = self.map_type(field.type)
            if not field.required:
                type_str = f"Option<{type_str}>"
            
            if field.description:
                lines.append(f"    /// {field.description}")
            lines.append(f"    pub {self._to_snake_case(field.name)}: {type_str},")
        
        lines.append("}")
        lines.append("")
        
        # Create DTO
        lines.append(f"/// Create{name} request DTO")
        lines.append("#[derive(Debug, Clone, Deserialize)]")
        lines.append(f"pub struct Create{name} {{")
        for field in fields:
            if field.required:
                type_str = self.map_type(field.type)
                lines.append(f"    pub {self._to_snake_case(field.name)}: {type_str},")
        lines.append("}")
        lines.append("")
        
        # Update DTO
        lines.append(f"/// Update{name} request DTO")
        lines.append("#[derive(Debug, Clone, Deserialize, Default)]")
        lines.append(f"pub struct Update{name} {{")
        for field in fields:
            type_str = self.map_type(field.type)
            lines.append(f"    pub {self._to_snake_case(field.name)}: Option<{type_str}>,")
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate_api_endpoint(self, path: str, method: str,
                              params: List[Field], response_type: FieldType) -> str:
        """Generate Actix-web handler"""
        method_lower = method.lower()
        handler_name = f"{method_lower}_{self._path_to_handler_name(path)}"
        
        lines = [
            f"/// Handle {method.upper()} {path}",
            f"#[{method_lower}(\"{path}\")]",
            f"async fn {handler_name}(",
            "    pool: web::Data<PgPool>,",
        ]
        
        # Add parameters
        for param in params:
            if param.name in path:
                lines.append(f"    {self._to_snake_case(param.name)}: web::Path<{self.map_type(param.type)}>,")
            else:
                lines.append(f"    body: web::Json<serde_json::Value>,")
        
        lines.append(") -> impl Responder {")
        lines.append("    // TODO: Implement")
        lines.append('    HttpResponse::Ok().json(serde_json::json!({"success": true}))')
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate_test(self, target: Union[Class, Method]) -> str:
        """Generate Rust test"""
        lines = [
            "#[cfg(test)]",
            "mod tests {",
            '    use super::*;',
            "",
        ]
        
        if isinstance(target, Class):
            for method in target.methods:
                lines.append(f"    #[actix_rt::test]")
                lines.append(f"    async fn test_{self._to_snake_case(method.name)}() {{")
                lines.append("        // Arrange")
                lines.append(f"        let instance = {target.name}::default();")
                lines.append("")
                lines.append("        // Act")
                params = ", ".join([f'test_{self._to_snake_case(p.name)}' for p in method.params])
                lines.append(f"        let result = instance.{self._to_snake_case(method.name)}({params}).await;")
                lines.append("")
                lines.append("        // Assert")
                lines.append("        assert!(result.is_ok());")
                lines.append("    }")
                lines.append("")
        
        elif isinstance(target, Method):
            lines.append(f"    #[test]")
            lines.append(f"    fn test_{self._to_snake_case(target.name)}() {{")
            lines.append("        // Arrange")
            lines.append("")
            lines.append("        // Act")
            params = ", ".join([f'test_{self._to_snake_case(p.name)}' for p in target.params])
            lines.append(f"        let result = {self._to_snake_case(target.name)}({params});")
            lines.append("")
            lines.append("        // Assert")
            lines.append("        assert!(result.is_ok());")
            lines.append("    }")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _to_snake_case(self, name: str) -> str:
        """Convert to snake_case"""
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append('_')
            result.append(char.lower())
        return ''.join(result)
    
    def _indent(self, code: str, level: int = 1) -> str:
        """Indent code"""
        indent = "    " * level
        return "\n".join(indent + line if line.strip() else line for line in code.split("\n"))
    
    def _path_to_handler_name(self, path: str) -> str:
        """Convert path to handler name"""
        parts = path.strip("/").split("/")
        return "_".join(self._to_snake_case(p.replace(":", "")) for p in parts)
    
    # CRUD methods
    def _generate_create_method(self, model_name: str, fields: List[Field]) -> str:
        field_names = [self._to_snake_case(f.name) for f in fields if f.required]
        placeholders = ", ".join([f"${i+1}" for i in range(len(field_names))])
        
        return f"""pub async fn create_{self._to_snake_case(model_name)}(
    pool: &PgPool,
    input: &Create{model_name},
) -> Result<{model_name}, sqlx::Error> {{
    sqlx::query_as::<_, {model_name}>(
        r#"
        INSERT INTO {self._to_snake_case(model_name)}s ({', '.join(field_names)})
        VALUES ({placeholders})
        RETURNING *
        "#
    )
    .fetch_one(pool)
    .await
}}"""
    
    def _generate_read_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""pub async fn get_{self._to_snake_case(model_name)}_by_id(
    pool: &PgPool,
    id: uuid::Uuid,
) -> Result<Option<{model_name}>, sqlx::Error> {{
    sqlx::query_as::<_, {model_name}>(
        r#"
        SELECT * FROM {self._to_snake_case(model_name)}s
        WHERE id = $1
        "#
    )
    .bind(id)
    .fetch_optional(pool)
    .await
}}"""
    
    def _generate_update_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""pub async fn update_{self._to_snake_case(model_name)}(
    pool: &PgPool,
    id: uuid::Uuid,
    input: &Update{model_name},
) -> Result<Option<{model_name}>, sqlx::Error> {{
    sqlx::query_as::<_, {model_name}>(
        r#"
        UPDATE {self._to_snake_case(model_name)}s
        SET updated_at = NOW()
        WHERE id = $1
        RETURNING *
        "#
    )
    .bind(id)
    .fetch_optional(pool)
    .await
}}"""
    
    def _generate_delete_method(self, model_name: str) -> str:
        return f"""pub async fn delete_{self._to_snake_case(model_name)}(
    pool: &PgPool,
    id: uuid::Uuid,
) -> Result<bool, sqlx::Error> {{
    let result = sqlx::query(
        r#"
        DELETE FROM {self._to_snake_case(model_name)}s
        WHERE id = $1
        "#
    )
    .bind(id)
    .execute(pool)
    .await?;
    
    Ok(result.rows_affected() > 0)
}}"""
    
    def _generate_list_method(self, model_name: str, fields: List[Field]) -> str:
        return f"""pub async fn list_{self._to_snake_case(model_name)}s(
    pool: &PgPool,
    page: i64,
    page_size: i64,
) -> Result<(Vec<{model_name}>, i64), sqlx::Error> {{
    let offset = (page - 1) * page_size;
    
    let items = sqlx::query_as::<_, {model_name}>(
        r#"
        SELECT * FROM {self._to_snake_case(model_name)}s
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
        "#
    )
    .bind(page_size)
    .bind(offset)
    .fetch_all(pool)
    .await?;
    
    let total: i64 = sqlx::query_scalar(
        r#"
        SELECT COUNT(*) FROM {self._to_snake_case(model_name)}s
        "#
    )
    .fetch_one(pool)
    .await?;
    
    Ok((items, total))
}}"""
