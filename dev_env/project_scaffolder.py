#!/usr/bin/env python3
"""
Mrki Project Scaffolder
Initializes new projects with various technology stacks
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class StackType(Enum):
    MERN = "mern"  # MongoDB, Express, React, Node
    PERN = "pern"  # PostgreSQL, Express, React, Node
    DJANGO_REACT = "django-react"
    FASTAPI_VUE = "fastapi-vue"
    GO_REACT = "go-react"
    NEXTJS_FULLSTACK = "nextjs-fullstack"
    RUST_REACT = "rust-react"
    JAVA_SPRING_ANGULAR = "java-spring-angular"
    DOTNET_REACT = "dotnet-react"


@dataclass
class ProjectConfig:
    name: str
    stack: StackType
    description: str = ""
    author: str = ""
    version: str = "1.0.0"
    features: List[str] = None
    database: Optional[str] = None
    auth: bool = False
    docker: bool = True
    ci_cd: bool = True
    testing: bool = True
    
    def __post_init__(self):
        if self.features is None:
            self.features = []


class ProjectScaffolder:
    """Main class for scaffolding new projects"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.templates_path = Path(__file__).parent / "templates"
        
    def scaffold(self, config: ProjectConfig) -> Dict[str, Any]:
        """Create a new project with the specified configuration"""
        project_path = self.base_path / config.name
        
        if project_path.exists():
            raise FileExistsError(f"Project {config.name} already exists")
        
        project_path.mkdir(parents=True)
        
        results = {
            "project_path": str(project_path),
            "created_files": [],
            "stack": config.stack.value,
            "features": []
        }
        
        # Scaffold based on stack type
        scaffold_methods = {
            StackType.MERN: self._scaffold_mern,
            StackType.PERN: self._scaffold_pern,
            StackType.DJANGO_REACT: self._scaffold_django_react,
            StackType.FASTAPI_VUE: self._scaffold_fastapi_vue,
            StackType.GO_REACT: self._scaffold_go_react,
            StackType.NEXTJS_FULLSTACK: self._scaffold_nextjs,
            StackType.RUST_REACT: self._scaffold_rust_react,
            StackType.JAVA_SPRING_ANGULAR: self._scaffold_java_spring,
            StackType.DOTNET_REACT: self._scaffold_dotnet_react,
        }
        
        scaffold_method = scaffold_methods.get(config.stack)
        if scaffold_method:
            scaffold_method(project_path, config, results)
        
        # Add common files
        self._add_common_files(project_path, config, results)
        
        # Add Docker if requested
        if config.docker:
            self._add_docker(project_path, config, results)
        
        # Add CI/CD if requested
        if config.ci_cd:
            self._add_ci_cd(project_path, config, results)
        
        # Add testing if requested
        if config.testing:
            self._add_testing(project_path, config, results)
        
        return results
    
    def _scaffold_mern(self, path: Path, config: ProjectConfig, results: Dict):
        """Scaffold MERN stack project"""
        # Backend
        backend = path / "backend"
        backend.mkdir()
        
        # Express server
        server_js = backend / "server.js"
        server_js.write_text(self._get_mern_server_template(config))
        results["created_files"].append(str(server_js))
        
        # Package.json
        package_json = backend / "package.json"
        package_json.write_text(json.dumps(self._get_mern_package_json(config), indent=2))
        results["created_files"].append(str(package_json))
        
        # Models
        models = backend / "models"
        models.mkdir()
        (models / "index.js").write_text(self._get_mongoose_models_template())
        
        # Routes
        routes = backend / "routes"
        routes.mkdir()
        (routes / "api.js").write_text(self._get_express_routes_template())
        
        # Middleware
        middleware = backend / "middleware"
        middleware.mkdir()
        (middleware / "auth.js").write_text(self._get_auth_middleware_template())
        
        # Frontend
        frontend = path / "frontend"
        frontend.mkdir()
        
        # React setup
        (frontend / "package.json").write_text(json.dumps(self._get_react_package_json(config), indent=2))
        
        # Public
        public = frontend / "public"
        public.mkdir()
        (public / "index.html").write_text(self._get_react_html_template(config))
        
        # Src
        src = frontend / "src"
        src.mkdir()
        (src / "App.js").write_text(self._get_react_app_template())
        (src / "index.js").write_text(self._get_react_index_template())
        
        components = src / "components"
        components.mkdir()
        (components / "Navbar.js").write_text(self._get_react_navbar_template())
        
        results["features"].append("MERN stack initialized")
    
    def _scaffold_pern(self, path: Path, config: ProjectConfig, results: Dict):
        """Scaffold PERN stack project"""
        # Similar to MERN but with PostgreSQL
        self._scaffold_mern(path, config, results)
        
        # Add PostgreSQL specific files
        backend = path / "backend"
        (backend / "config").mkdir()
        (backend / "config" / "database.js").write_text(self._get_postgres_config_template())
        
        migrations = backend / "migrations"
        migrations.mkdir()
        (migrations / "001_initial.sql").write_text(self._get_initial_migration())
        
        results["features"].append("PostgreSQL configuration added")
    
    def _scaffold_django_react(self, path: Path, config: ProjectConfig, results: Dict):
        """Scaffold Django + React project"""
        # Backend - Django
        backend = path / "backend"
        backend.mkdir()
        
        # Django project structure
        (backend / "manage.py").write_text(self._get_django_manage_template(config))
        
        project_dir = backend / config.name
        project_dir.mkdir()
        (project_dir / "__init__.py").write_text("")
        (project_dir / "settings.py").write_text(self._get_django_settings_template(config))
        (project_dir / "urls.py").write_text(self._get_django_urls_template())
        (project_dir / "wsgi.py").write_text(self._get_django_wsgi_template(config))
        (project_dir / "asgi.py").write_text(self._get_django_asgi_template(config))
        
        # Django apps
        apps = backend / "apps"
        apps.mkdir()
        
        api_app = apps / "api"
        api_app.mkdir()
        (api_app / "__init__.py").write_text("")
        (api_app / "models.py").write_text(self._get_django_models_template())
        (api_app / "views.py").write_text(self._get_django_views_template())
        (api_app / "serializers.py").write_text(self._get_django_serializers_template())
        (api_app / "urls.py").write_text(self._get_django_app_urls_template())
        
        # Requirements
        (backend / "requirements.txt").write_text(self._get_django_requirements())
        
        # Frontend - React (same as MERN)
        self._create_react_frontend(path, config, results)
        
        results["features"].append("Django + React stack initialized")
    
    def _scaffold_fastapi_vue(self, path: Path, config: ProjectConfig, results: Dict):
        """Scaffold FastAPI + Vue project"""
        # Backend - FastAPI
        backend = path / "backend"
        backend.mkdir()
        
        (backend / "main.py").write_text(self._get_fastapi_main_template(config))
        (backend / "models.py").write_text(self._get_fastapi_models_template())
        (backend / "schemas.py").write_text(self._get_fastapi_schemas_template())
        (backend / "crud.py").write_text(self._get_fastapi_crud_template())
        (backend / "database.py").write_text(self._get_fastapi_database_template())
        (backend / "requirements.txt").write_text(self._get_fastapi_requirements())
        
        # Frontend - Vue
        frontend = path / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text(json.dumps(self._get_vue_package_json(config), indent=2))
        
        public = frontend / "public"
        public.mkdir()
        (public / "index.html").write_text(self._get_vue_html_template(config))
        
        src = frontend / "src"
        src.mkdir()
        (src / "main.js").write_text(self._get_vue_main_template())
        (src / "App.vue").write_text(self._get_vue_app_template())
        
        components = src / "components"
        components.mkdir()
        (components / "HelloWorld.vue").write_text(self._get_vue_hello_template())
        
        results["features"].append("FastAPI + Vue stack initialized")
    
    def _scaffold_go_react(self, path: Path, config: ProjectConfig, results: Dict):
        """Scaffold Go + React project"""
        # Backend - Go
        backend = path / "backend"
        backend.mkdir()
        
        (backend / "go.mod").write_text(self._get_go_mod_template(config))
        (backend / "main.go").write_text(self._get_go_main_template(config))
        
        internal = backend / "internal"
        internal.mkdir()
        
        handlers = internal / "handlers"
        handlers.mkdir()
        (handlers / "handlers.go").write_text(self._get_go_handlers_template())
        
        models = internal / "models"
        models.mkdir()
        (models / "models.go").write_text(self._get_go_models_template())
        
        db = internal / "db"
        db.mkdir()
        (db / "db.go").write_text(self._get_go_db_template())
        
        # Frontend - React
        self._create_react_frontend(path, config, results)
        
        results["features"].append("Go + React stack initialized")
    
    def _scaffold_nextjs(self, path: Path, config: ProjectConfig, results: Dict):
        """Scaffold Next.js full-stack project"""
        (path / "package.json").write_text(json.dumps(self._get_nextjs_package_json(config), indent=2))
        
        public_dir = path / "public"
        public_dir.mkdir()
        
        src = path / "src"
        src.mkdir()
        
        app_dir = src / "app"
        app_dir.mkdir()
        (app_dir / "layout.js").write_text(self._get_nextjs_layout_template())
        (app_dir / "page.js").write_text(self._get_nextjs_page_template())
        (app_dir / "globals.css").write_text(self._get_nextjs_css_template())
        
        api_dir = app_dir / "api"
        api_dir.mkdir()
        (api_dir / "route.js").write_text(self._get_nextjs_api_template())
        
        components = src / "components"
        components.mkdir()
        (components / "Header.js").write_text(self._get_nextjs_header_template())
        
        lib = src / "lib"
        lib.mkdir()
        (lib / "db.js").write_text(self._get_nextjs_db_template())
        
        results["features"].append("Next.js full-stack initialized")
    
    def _scaffold_rust_react(self, path: Path, config: ProjectConfig, results: Dict):
        """Scaffold Rust + React project"""
        # Backend - Rust/Actix
        backend = path / "backend"
        backend.mkdir()
        
        (backend / "Cargo.toml").write_text(self._get_cargo_toml_template(config))
        
        src_dir = backend / "src"
        src_dir.mkdir()
        (src_dir / "main.rs").write_text(self._get_rust_main_template())
        (src_dir / "routes.rs").write_text(self._get_rust_routes_template())
        (src_dir / "models.rs").write_text(self._get_rust_models_template())
        (src_dir / "db.rs").write_text(self._get_rust_db_template())
        
        # Frontend - React
        self._create_react_frontend(path, config, results)
        
        results["features"].append("Rust + React stack initialized")
    
    def _scaffold_java_spring(self, path: Path, config: ProjectConfig, results: Dict):
        """Scaffold Java Spring + Angular project"""
        # Backend - Spring Boot
        backend = path / "backend"
        backend.mkdir()
        
        (backend / "pom.xml").write_text(self._get_pom_xml_template(config))
        
        src_main = backend / "src" / "main" / "java" / "com" / "example" / config.name
        src_main.mkdir(parents=True)
        
        (src_main / "Application.java").write_text(self._get_java_main_template(config))
        
        controller = src_main / "controller"
        controller.mkdir()
        (controller / "ApiController.java").write_text(self._get_java_controller_template())
        
        model = src_main / "model"
        model.mkdir()
        (model / "Entity.java").write_text(self._get_java_entity_template())
        
        repository = src_main / "repository"
        repository.mkdir()
        (repository / "Repository.java").write_text(self._get_java_repository_template())
        
        service = src_main / "service"
        service.mkdir()
        (service / "Service.java").write_text(self._get_java_service_template())
        
        # Frontend - Angular
        frontend = path / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text(json.dumps(self._get_angular_package_json(config), indent=2))
        (frontend / "angular.json").write_text(self._get_angular_json_template(config))
        
        results["features"].append("Java Spring + Angular stack initialized")
    
    def _scaffold_dotnet_react(self, path: Path, config: ProjectConfig, results: Dict):
        """Scaffold .NET + React project"""
        # Backend - .NET
        backend = path / "backend"
        backend.mkdir()
        
        (backend / f"{config.name}.csproj").write_text(self._get_csproj_template(config))
        (backend / "Program.cs").write_text(self._get_program_cs_template(config))
        
        controllers = backend / "Controllers"
        controllers.mkdir()
        (controllers / "ApiController.cs").write_text(self._get_dotnet_controller_template())
        
        models = backend / "Models"
        models.mkdir()
        (models / "Entity.cs").write_text(self._get_dotnet_model_template())
        
        data = backend / "Data"
        data.mkdir()
        (data / "AppDbContext.cs").write_text(self._get_dotnet_dbcontext_template(config))
        
        # Frontend - React
        self._create_react_frontend(path, config, results)
        
        results["features"].append(".NET + React stack initialized")
    
    def _create_react_frontend(self, path: Path, config: ProjectConfig, results: Dict):
        """Helper to create React frontend"""
        frontend = path / "frontend"
        frontend.mkdir(exist_ok=True)
        
        (frontend / "package.json").write_text(json.dumps(self._get_react_package_json(config), indent=2))
        
        public = frontend / "public"
        public.mkdir(exist_ok=True)
        (public / "index.html").write_text(self._get_react_html_template(config))
        
        src = frontend / "src"
        src.mkdir(exist_ok=True)
        (src / "App.js").write_text(self._get_react_app_template())
        (src / "index.js").write_text(self._get_react_index_template())
    
    def _add_common_files(self, path: Path, config: ProjectConfig, results: Dict):
        """Add common project files"""
        # README
        readme = path / "README.md"
        readme.write_text(self._get_readme_template(config))
        results["created_files"].append(str(readme))
        
        # .gitignore
        gitignore = path / ".gitignore"
        gitignore.write_text(self._get_gitignore_template(config))
        results["created_files"].append(str(gitignore))
        
        # .env.example
        env_example = path / ".env.example"
        env_example.write_text(self._get_env_example_template(config))
        results["created_files"].append(str(env_example))
        
        # LICENSE
        license_file = path / "LICENSE"
        license_file.write_text(self._get_license_template())
        results["created_files"].append(str(license_file))
    
    def _add_docker(self, path: Path, config: ProjectConfig, results: Dict):
        """Add Docker configuration"""
        from .docker import DockerManager
        docker_manager = DockerManager()
        docker_files = docker_manager.generate_docker_files(path, config.stack.value)
        results["created_files"].extend(docker_files)
        results["features"].append("Docker configuration added")
    
    def _add_ci_cd(self, path: Path, config: ProjectConfig, results: Dict):
        """Add CI/CD configuration"""
        github_dir = path / ".github" / "workflows"
        github_dir.mkdir(parents=True)
        
        # CI workflow
        ci_file = github_dir / "ci.yml"
        ci_file.write_text(self._get_ci_workflow_template(config))
        results["created_files"].append(str(ci_file))
        
        # CD workflow
        cd_file = github_dir / "cd.yml"
        cd_file.write_text(self._get_cd_workflow_template(config))
        results["created_files"].append(str(cd_file))
        
        results["features"].append("CI/CD pipelines added")
    
    def _add_testing(self, path: Path, config: ProjectConfig, results: Dict):
        """Add testing configuration"""
        from .testing import TestManager
        test_manager = TestManager()
        test_files = test_manager.generate_test_files(path, config.stack.value)
        results["created_files"].extend(test_files)
        results["features"].append("Testing framework added")
    
    # Template methods - MERN
    def _get_mern_server_template(self, config: ProjectConfig) -> str:
        return f'''const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const dotenv = require('dotenv');

const app = express();
dotenv.config();

// Middleware
app.use(cors());
app.use(express.json());

// Database connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/{config.name}')
  .then(() => console.log('MongoDB connected'))
  .catch(err => console.error('MongoDB connection error:', err));

// Routes
app.use('/api', require('./routes/api'));

// Health check
app.get('/health', (req, res) => {{
  res.json({{ status: 'OK', timestamp: new Date().toISOString() }});
}});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${{PORT}}`));
'''
    
    def _get_mern_package_json(self, config: ProjectConfig) -> dict:
        return {
            "name": f"{config.name}-backend",
            "version": config.version,
            "description": config.description,
            "main": "server.js",
            "scripts": {
                "start": "node server.js",
                "dev": "nodemon server.js",
                "test": "jest"
            },
            "dependencies": {
                "express": "^4.18.2",
                "mongoose": "^8.0.0",
                "cors": "^2.8.5",
                "dotenv": "^16.3.1",
                "bcryptjs": "^2.4.3",
                "jsonwebtoken": "^9.0.2"
            },
            "devDependencies": {
                "nodemon": "^3.0.1",
                "jest": "^29.7.0"
            }
        }
    
    def _get_mongoose_models_template(self) -> str:
        return '''const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
  name: { type: String, required: true },
  createdAt: { type: Date, default: Date.now }
});

const itemSchema = new mongoose.Schema({
  title: { type: String, required: true },
  description: String,
  user: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  createdAt: { type: Date, default: Date.now }
});

module.exports = {
  User: mongoose.model('User', userSchema),
  Item: mongoose.model('Item', itemSchema)
};
'''
    
    def _get_express_routes_template(self) -> str:
        return '''const express = require('express');
const router = express.Router();
const { User, Item } = require('../models');
const auth = require('../middleware/auth');

// Get all items
router.get('/items', async (req, res) => {
  try {
    const items = await Item.find().populate('user', 'name email');
    res.json(items);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Create item
router.post('/items', auth, async (req, res) => {
  try {
    const item = new Item({ ...req.body, user: req.userId });
    await item.save();
    res.status(201).json(item);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Get user profile
router.get('/profile', auth, async (req, res) => {
  try {
    const user = await User.findById(req.userId).select('-password');
    res.json(user);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
'''
    
    def _get_auth_middleware_template(self) -> str:
        return '''const jwt = require('jsonwebtoken');

module.exports = (req, res, next) => {
  const token = req.header('Authorization')?.replace('Bearer ', '');
  
  if (!token) {
    return res.status(401).json({ error: 'No token, authorization denied' });
  }
  
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'secret');
    req.userId = decoded.userId;
    next();
  } catch (error) {
    res.status(401).json({ error: 'Token is invalid' });
  }
};
'''
    
    def _get_react_package_json(self, config: ProjectConfig) -> dict:
        return {
            "name": f"{config.name}-frontend",
            "version": config.version,
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.20.0",
                "axios": "^1.6.0",
                "@tanstack/react-query": "^5.8.0"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            },
            "devDependencies": {
                "react-scripts": "5.0.1"
            },
            "browserslist": {
                "production": [">0.2%", "not dead", "not op_mini all"],
                "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
            }
        }
    
    def _get_react_html_template(self, config: ProjectConfig) -> str:
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{config.name}</title>
</head>
<body>
  <div id="root"></div>
</body>
</html>
'''
    
    def _get_react_app_template(self) -> str:
        return '''import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Navbar from './components/Navbar';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="App">
          <Navbar />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

function Home() {
  return <div className="p-4"><h1>Welcome</h1></div>;
}

function About() {
  return <div className="p-4"><h1>About</h1></div>;
}

export default App;
'''
    
    def _get_react_index_template(self) -> str:
        return '''import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
'''
    
    def _get_react_navbar_template(self) -> str:
        return '''import React from 'react';
import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="navbar">
      <Link to="/">Home</Link>
      <Link to="/about">About</Link>
    </nav>
  );
}

export default Navbar;
'''
    
    # PostgreSQL templates
    def _get_postgres_config_template(self) -> str:
        return '''const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'myapp',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'password',
});

module.exports = pool;
'''
    
    def _get_initial_migration(self) -> str:
        return '''-- Initial migration
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS items (
  id SERIAL PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  user_id INTEGER REFERENCES users(id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''
    
    # Django templates
    def _get_django_manage_template(self, config: ProjectConfig) -> str:
        return f'''#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{config.name}.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
'''
    
    def _get_django_settings_template(self, config: ProjectConfig) -> str:
        return f'''import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-me')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'apps.api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = '{config.name}.urls'

TEMPLATES = [
    {{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {{
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        }},
    }},
]

WSGI_APPLICATION = '{config.name}.wsgi.application'

DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', '{config.name}'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }}
}}

AUTH_PASSWORD_VALIDATORS = [
    {{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'}},
    {{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'}},
    {{'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'}},
    {{'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

REST_FRAMEWORK = {{
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}}
'''
    
    def _get_django_urls_template(self) -> str:
        return '''from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.api.urls')),
]
'''
    
    def _get_django_wsgi_template(self, config: ProjectConfig) -> str:
        return f'''import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{config.name}.settings')

application = get_wsgi_application()
'''
    
    def _get_django_asgi_template(self, config: ProjectConfig) -> str:
        return f'''import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{config.name}.settings')

application = get_asgi_application()
'''
    
    def _get_django_models_template(self) -> str:
        return '''from django.db import models
from django.contrib.auth.models import User


class Item(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='items')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
'''
    
    def _get_django_views_template(self) -> str:
        return '''from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Item
from .serializers import ItemSerializer, UserSerializer


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


@api_view(['GET'])
def health_check(request):
    return Response({'status': 'OK', 'timestamp': __import__('datetime').datetime.now()})
'''
    
    def _get_django_serializers_template(self) -> str:
        return '''from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Item


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class ItemSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Item
        fields = ['id', 'title', 'description', 'user', 'created_at', 'updated_at']
'''
    
    def _get_django_app_urls_template(self) -> str:
        return '''from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ItemViewSet, UserViewSet, health_check

router = DefaultRouter()
router.register(r'items', ItemViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('health/', health_check),
]
'''
    
    def _get_django_requirements(self) -> str:
        return '''Django>=4.2.0,<5.0
djangorestframework>=3.14.0
django-cors-headers>=4.3.0
psycopg2-binary>=2.9.9
python-dotenv>=1.0.0
gunicorn>=21.2.0
'''
    
    # FastAPI templates
    def _get_fastapi_main_template(self, config: ProjectConfig) -> str:
        return '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import engine, Base
from .routers import items, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown


app = FastAPI(
    title="''' + config.name + '''",
    description="''' + config.description + '''",
    version="''' + config.version + '''",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(items.router, prefix="/api/items", tags=["items"])
app.include_router(users.router, prefix="/api/users", tags=["users"])


@app.get("/health")
async def health_check():
    return {"status": "OK", "timestamp": __import__('datetime').datetime.now().isoformat()}
'''
    
    def _get_fastapi_models_template(self) -> str:
        return '''from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    items = relationship("Item", back_populates="owner")


class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    owner = relationship("User", back_populates="items")
'''
    
    def _get_fastapi_schemas_template(self) -> str:
        return '''from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    created_at: datetime
    items: List[Item] = []

    class Config:
        from_attributes = True
'''
    
    def _get_fastapi_crud_template(self) -> str:
        return '''from sqlalchemy.orm import Session
from . import models, schemas


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = models.User(email=user.email, hashed_password=fake_hashed_password, full_name=user.full_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()


def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
'''
    
    def _get_fastapi_database_template(self) -> str:
        return '''from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost/myapp"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''
    
    def _get_fastapi_requirements(self) -> str:
        return '''fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.9
pydantic>=2.5.0
python-dotenv>=1.0.0
pytest>=7.4.0
httpx>=0.25.0
'''
    
    # Vue templates
    def _get_vue_package_json(self, config: ProjectConfig) -> dict:
        return {
            "name": f"{config.name}-frontend",
            "version": config.version,
            "private": True,
            "scripts": {
                "serve": "vue-cli-service serve",
                "build": "vue-cli-service build",
                "test:unit": "vue-cli-service test:unit",
                "lint": "vue-cli-service lint"
            },
            "dependencies": {
                "vue": "^3.3.8",
                "vue-router": "^4.2.5",
                "pinia": "^2.1.7",
                "axios": "^1.6.0"
            },
            "devDependencies": {
                "@vue/cli-plugin-eslint": "~5.0.0",
                "@vue/cli-plugin-router": "~5.0.0",
                "@vue/cli-plugin-unit-jest": "~5.0.0",
                "@vue/cli-service": "~5.0.0",
                "@vue/test-utils": "^2.4.0"
            }
        }
    
    def _get_vue_html_template(self, config: ProjectConfig) -> str:
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{config.name}</title>
</head>
<body>
  <div id="app"></div>
</body>
</html>
'''
    
    def _get_vue_main_template(self) -> str:
        return '''import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
'''
    
    def _get_vue_app_template(self) -> str:
        return '''<template>
  <div id="app">
    <nav>
      <router-link to="/">Home</router-link> |
      <router-link to="/about">About</router-link>
    </nav>
    <router-view />
  </div>
</template>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  text-align: center;
  color: #2c3e50;
}

nav {
  padding: 30px;
}

nav a {
  font-weight: bold;
  color: #2c3e50;
  margin: 0 10px;
}

nav a.router-link-exact-active {
  color: #42b983;
}
</style>
'''
    
    def _get_vue_hello_template(self) -> str:
        return '''<template>
  <div class="hello">
    <h1>{{ msg }}</h1>
    <p>Welcome to your Vue.js app</p>
  </div>
</template>

<script>
export default {
  name: 'HelloWorld',
  props: {
    msg: String
  }
}
</script>
'''
    
    # Go templates
    def _get_go_mod_template(self, config: ProjectConfig) -> str:
        return f'''module github.com/example/{config.name}

go 1.21

require (
	github.com/gin-gonic/gin v1.9.1
	github.com/lib/pq v1.10.9
	github.com/joho/godotenv v1.5.1
	gorm.io/driver/postgres v1.5.4
	gorm.io/gorm v1.25.5
)
'''
    
    def _get_go_main_template(self, config: ProjectConfig) -> str:
        return f'''package main

import (
	"log"
	"os"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"github.com/example/{config.name}/internal/db"
	"github.com/example/{config.name}/internal/handlers"
)

func main() {{
	godotenv.Load()

	database := db.Init()
	defer db.Close()

	r := gin.Default()

	// CORS
	r.Use(func(c *gin.Context) {{
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		if c.Request.Method == "OPTIONS" {{
			c.AbortWithStatus(204)
			return
		}}
		c.Next()
	}})

	// Routes
	api := r.Group("/api")
	{{
		api.GET("/items", handlers.GetItems)
		api.POST("/items", handlers.CreateItem)
		api.GET("/items/:id", handlers.GetItem)
		api.PUT("/items/:id", handlers.UpdateItem)
		api.DELETE("/items/:id", handlers.DeleteItem)
	}}

	r.GET("/health", handlers.HealthCheck)

	port := os.Getenv("PORT")
	if port == "" {{
		port = "8080"
	}}

	log.Printf("Server starting on port %s", port)
	if err := r.Run(":" + port); err != nil {{
		log.Fatal(err)
	}}
}}
'''
    
    def _get_go_handlers_template(self) -> str:
        return '''package handlers

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/example/myapp/internal/db"
	"github.com/example/myapp/internal/models"
)

func GetItems(c *gin.Context) {
	var items []models.Item
	db.DB.Find(&items)
	c.JSON(http.StatusOK, items)
}

func CreateItem(c *gin.Context) {
	var item models.Item
	if err := c.ShouldBindJSON(&item); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	db.DB.Create(&item)
	c.JSON(http.StatusCreated, item)
}

func GetItem(c *gin.Context) {
	id, _ := strconv.Atoi(c.Param("id"))
	var item models.Item
	if err := db.DB.First(&item, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Item not found"})
		return
	}
	c.JSON(http.StatusOK, item)
}

func UpdateItem(c *gin.Context) {
	id, _ := strconv.Atoi(c.Param("id"))
	var item models.Item
	if err := db.DB.First(&item, id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Item not found"})
		return
	}
	if err := c.ShouldBindJSON(&item); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	db.DB.Save(&item)
	c.JSON(http.StatusOK, item)
}

func DeleteItem(c *gin.Context) {
	id, _ := strconv.Atoi(c.Param("id"))
	db.DB.Delete(&models.Item{}, id)
	c.JSON(http.StatusOK, gin.H{"message": "Item deleted"})
}

func HealthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "OK"})
}
'''
    
    def _get_go_models_template(self) -> str:
        return '''package models

import (
	"time"
	"gorm.io/gorm"
)

type User struct {
	ID        uint           `gorm:"primarykey" json:"id"`
	CreatedAt time.Time      `json:"created_at"`
	UpdatedAt time.Time      `json:"updated_at"`
	DeletedAt gorm.DeletedAt `gorm:"index" json:"-"`
	Email     string         `gorm:"uniqueIndex" json:"email"`
	Password  string         `json:"-"`
	Name      string         `json:"name"`
	Items     []Item         `json:"items,omitempty"`
}

type Item struct {
	ID          uint           `gorm:"primarykey" json:"id"`
	CreatedAt   time.Time      `json:"created_at"`
	UpdatedAt   time.Time      `json:"updated_at"`
	DeletedAt   gorm.DeletedAt `gorm:"index" json:"-"`
	Title       string         `json:"title"`
	Description string         `json:"description"`
	UserID      uint           `json:"user_id"`
}
'''
    
    def _get_go_db_template(self) -> str:
        return '''package db

import (
	"log"
	"os"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"github.com/example/myapp/internal/models"
)

var DB *gorm.DB

func Init() *gorm.DB {
	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		dsn = "host=localhost user=postgres password=password dbname=myapp port=5432 sslmode=disable"
	}

	var err error
	DB, err = gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}

	// Auto migrate
	DB.AutoMigrate(&models.User{}, &models.Item{})

	return DB
}

func Close() {
	sqlDB, _ := DB.DB()
	sqlDB.Close()
}
'''
    
    # Next.js templates
    def _get_nextjs_package_json(self, config: ProjectConfig) -> dict:
        return {
            "name": config.name,
            "version": config.version,
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint",
                "test": "jest"
            },
            "dependencies": {
                "next": "14.0.0",
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "@prisma/client": "^5.6.0"
            },
            "devDependencies": {
                "@types/node": "^20.0.0",
                "@types/react": "^18.2.0",
                "eslint": "^8.0.0",
                "eslint-config-next": "14.0.0",
                "jest": "^29.7.0",
                "prisma": "^5.6.0",
                "typescript": "^5.3.0"
            }
        }
    
    def _get_nextjs_layout_template(self) -> str:
        return '''export const metadata = {
  title: 'My App',
  description: 'A Next.js application',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
'''
    
    def _get_nextjs_page_template(self) -> str:
        return '''export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold mb-4">Welcome to Next.js</h1>
        <p className="text-lg">Get started by editing src/app/page.js</p>
      </div>
    </main>
  )
}
'''
    
    def _get_nextjs_css_template(self) -> str:
        return '''@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --foreground-rgb: 0, 0, 0;
  --background-start-rgb: 214, 219, 220;
  --background-end-rgb: 255, 255, 255;
}

body {
  color: rgb(var(--foreground-rgb));
  background: linear-gradient(
      to bottom,
      transparent,
      rgb(var(--background-end-rgb))
    )
    rgb(var(--background-start-rgb));
}
'''
    
    def _get_nextjs_api_template(self) -> str:
        return '''export async function GET() {
  return Response.json({ message: 'Hello from API' })
}

export async function POST(request) {
  const body = await request.json()
  return Response.json({ received: body })
}
'''
    
    def _get_nextjs_header_template(self) -> str:
        return '''export default function Header() {
  return (
    <header className="bg-blue-600 text-white p-4">
      <nav className="container mx-auto flex justify-between items-center">
        <h1 className="text-xl font-bold">My App</h1>
        <ul className="flex gap-4">
          <li><a href="/" className="hover:underline">Home</a></li>
          <li><a href="/about" className="hover:underline">About</a></li>
        </ul>
      </nav>
    </header>
  )
}
'''
    
    def _get_nextjs_db_template(self) -> str:
        return '''import { PrismaClient } from '@prisma/client'

const globalForPrisma = globalThis

export const prisma = globalForPrisma.prisma ?? new PrismaClient()

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma
'''
    
    # Rust templates
    def _get_cargo_toml_template(self, config: ProjectConfig) -> str:
        return f'''[package]
name = "{config.name}"
version = "{config.version}"
edition = "2021"

[dependencies]
actix-web = "4.4"
actix-cors = "0.6"
serde = {{ version = "1.0", features = ["derive"] }}
serde_json = "1.0"
tokio = {{ version = "1.34", features = ["full"] }}
sqlx = {{ version = "0.7", features = ["runtime-tokio-native-tls", "postgres"] }}
dotenvy = "0.15"
chrono = {{ version = "0.4", features = ["serde"] }}
uuid = {{ version = "1.6", features = ["serde", "v4"] }}

[dev-dependencies]
actix-rt = "2.9"
'''
    
    def _get_rust_main_template(self) -> str:
        return '''mod routes;
mod models;
mod db;

use actix_web::{web, App, HttpServer};
use actix_cors::Cors;
use dotenvy::dotenv;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    dotenv().ok();
    
    let db_pool = db::create_pool().await.expect("Failed to create pool");
    
    HttpServer::new(move || {
        let cors = Cors::default()
            .allow_any_origin()
            .allow_any_method()
            .allow_any_header();
        
        App::new()
            .wrap(cors)
            .app_data(web::Data::new(db_pool.clone()))
            .configure(routes::config)
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}
'''
    
    def _get_rust_routes_template(self) -> str:
        return '''use actix_web::{web, HttpResponse, Responder};
use crate::db::DbPool;

pub fn config(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/api")
            .route("/items", web::get().to(get_items))
            .route("/items", web::post().to(create_item))
            .route("/health", web::get().to(health_check))
    );
}

async fn get_items(pool: web::Data<DbPool>) -> impl Responder {
    HttpResponse::Ok().json(vec![
        serde_json::json!({"id": 1, "title": "Item 1"}),
        serde_json::json!({"id": 2, "title": "Item 2"}),
    ])
}

async fn create_item(pool: web::Data<DbPool>, item: web::Json<crate::models::Item>) -> impl Responder {
    HttpResponse::Created().json(item.into_inner())
}

async fn health_check() -> impl Responder {
    HttpResponse::Ok().json(serde_json::json!({"status": "OK"}))
}
'''
    
    def _get_rust_models_template(self) -> str:
        return '''use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize)]
pub struct User {
    pub id: Uuid,
    pub email: String,
    pub name: String,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Item {
    pub id: Uuid,
    pub title: String,
    pub description: Option<String>,
    pub user_id: Uuid,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
pub struct CreateItemRequest {
    pub title: String,
    pub description: Option<String>,
}
'''
    
    def _get_rust_db_template(self) -> str:
        return '''use sqlx::postgres::PgPoolOptions;
use sqlx::PgPool;
use std::env;

pub type DbPool = PgPool;

pub async fn create_pool() -> Result<DbPool, sqlx::Error> {
    let database_url = env::var("DATABASE_URL")
        .unwrap_or_else(|_| "postgres://postgres:password@localhost/myapp".to_string());
    
    PgPoolOptions::new()
        .max_connections(5)
        .connect(&database_url)
        .await
}
'''
    
    # Java templates
    def _get_pom_xml_template(self, config: ProjectConfig) -> str:
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>
    
    <groupId>com.example</groupId>
    <artifactId>{config.name}</artifactId>
    <version>{config.version}</version>
    <name>{config.name}</name>
    <description>{config.description}</description>
    
    <properties>
        <java.version>17</java.version>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
'''
    
    def _get_java_main_template(self, config: ProjectConfig) -> str:
        return f'''package com.example.{config.name};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Application {{
    public static void main(String[] args) {{
        SpringApplication.run(Application.class, args);
    }}
}}
'''
    
    def _get_java_controller_template(self) -> str:
        return '''package com.example.myapp.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import java.util.List;

@RestController
@RequestMapping("/api")
public class ApiController {
    
    @GetMapping("/items")
    public ResponseEntity<List<String>> getItems() {
        return ResponseEntity.ok(List.of("Item 1", "Item 2", "Item 3"));
    }
    
    @GetMapping("/health")
    public ResponseEntity<String> healthCheck() {
        return ResponseEntity.ok("OK");
    }
}
'''
    
    def _get_java_entity_template(self) -> str:
        return '''package com.example.myapp.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "items")
public class Entity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    private String title;
    private String description;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
    
    // Getters and setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    
    public LocalDateTime getCreatedAt() { return createdAt; }
}
'''
    
    def _get_java_repository_template(self) -> str:
        return '''package com.example.myapp.repository;

import com.example.myapp.model.Entity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface Repository extends JpaRepository<Entity, Long> {
}
'''
    
    def _get_java_service_template(self) -> str:
        return '''package com.example.myapp.service;

import com.example.myapp.model.Entity;
import com.example.myapp.repository.Repository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class Service {
    
    @Autowired
    private Repository repository;
    
    public List<Entity> findAll() {
        return repository.findAll();
    }
    
    public Entity save(Entity entity) {
        return repository.save(entity);
    }
}
'''
    
    def _get_angular_package_json(self, config: ProjectConfig) -> dict:
        return {
            "name": f"{config.name}-frontend",
            "version": config.version,
            "scripts": {
                "ng": "ng",
                "start": "ng serve",
                "build": "ng build",
                "watch": "ng build --watch --configuration development",
                "test": "ng test"
            },
            "dependencies": {
                "@angular/animations": "^17.0.0",
                "@angular/common": "^17.0.0",
                "@angular/compiler": "^17.0.0",
                "@angular/core": "^17.0.0",
                "@angular/forms": "^17.0.0",
                "@angular/platform-browser": "^17.0.0",
                "@angular/platform-browser-dynamic": "^17.0.0",
                "@angular/router": "^17.0.0",
                "rxjs": "~7.8.0",
                "tslib": "^2.3.0",
                "zone.js": "~0.14.0"
            },
            "devDependencies": {
                "@angular-devkit/build-angular": "^17.0.0",
                "@angular/cli": "^17.0.0",
                "@angular/compiler-cli": "^17.0.0",
                "typescript": "~5.2.0"
            }
        }
    
    def _get_angular_json_template(self, config: ProjectConfig) -> str:
        return '''{
  "$schema": "./node_modules/@angular/cli/lib/config/schema.json",
  "version": 1,
  "newProjectRoot": "projects",
  "projects": {
    "''' + config.name + '''": {
      "projectType": "application",
      "schematics": {},
      "root": "",
      "sourceRoot": "src",
      "prefix": "app",
      "architect": {
        "build": {
          "builder": "@angular-devkit/build-angular:browser",
          "options": {
            "outputPath": "dist/''' + config.name + '''",
            "index": "src/index.html",
            "main": "src/main.ts",
            "polyfills": ["zone.js"],
            "tsConfig": "tsconfig.app.json",
            "assets": ["src/favicon.ico", "src/assets"],
            "styles": ["src/styles.css"],
            "scripts": []
          }
        },
        "serve": {
          "builder": "@angular-devkit/build-angular:dev-server",
          "options": {
            "port": 4200
          }
        }
      }
    }
  }
}
'''
    
    # .NET templates
    def _get_csproj_template(self, config: ProjectConfig) -> str:
        return f'''<Project Sdk="Microsoft.NET.Sdk.Web">

  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.AspNetCore.OpenApi" Version="8.0.0" />
    <PackageReference Include="Microsoft.EntityFrameworkCore.SqlServer" Version="8.0.0" />
    <PackageReference Include="Microsoft.EntityFrameworkCore.Tools" Version="8.0.0" />
    <PackageReference Include="Npgsql.EntityFrameworkCore.PostgreSQL" Version="8.0.0" />
    <PackageReference Include="Swashbuckle.AspNetCore" Version="6.5.0" />
  </ItemGroup>

</Project>
'''
    
    def _get_program_cs_template(self, config: ProjectConfig) -> str:
        return f'''using Microsoft.EntityFrameworkCore;
using {config.name}.Data;

var builder = WebApplication.CreateBuilder(args);

// Add services
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Add DbContext
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));

// Add CORS
builder.Services.AddCors(options =>
{{
    options.AddPolicy("AllowAll", policy =>
    {{
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    }});
}});

var app = builder.Build();

// Configure middleware
if (app.Environment.IsDevelopment())
{{
    app.UseSwagger();
    app.UseSwaggerUI();
}}

app.UseHttpsRedirection();
app.UseCors("AllowAll");
app.UseAuthorization();
app.MapControllers();

app.Run();
'''
    
    def _get_dotnet_controller_template(self) -> str:
        return '''using Microsoft.AspNetCore.Mvc;

namespace MyApp.Controllers;

[ApiController]
[Route("api/[controller]")]
public class ItemsController : ControllerBase
{
    [HttpGet]
    public IActionResult GetItems()
    {
        return Ok(new[] { "Item 1", "Item 2", "Item 3" });
    }

    [HttpGet("health")]
    public IActionResult HealthCheck()
    {
        return Ok(new { status = "OK", timestamp = DateTime.UtcNow });
    }
}
'''
    
    def _get_dotnet_model_template(self) -> str:
        return '''namespace MyApp.Models;

public class Entity
{
    public int Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
'''
    
    def _get_dotnet_dbcontext_template(self, config: ProjectConfig) -> str:
        return f'''using Microsoft.EntityFrameworkCore;
using {config.name}.Models;

namespace {config.name}.Data;

public class AppDbContext : DbContext
{{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) {{ }}

    public DbSet<Entity> Entities => Set<Entity>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {{
        base.OnModelCreating(modelBuilder);
    }}
}}
'''
    
    # Common templates
    def _get_readme_template(self, config: ProjectConfig) -> str:
        return f'''# {config.name}

{config.description}

## Stack

- **Frontend**: {config.stack.value.split('-')[1] if '-' in config.stack.value else 'React'}
- **Backend**: {config.stack.value.split('-')[0] if '-' in config.stack.value else 'Node.js'}
- **Database**: {config.database or 'PostgreSQL'}

## Getting Started

### Prerequisites

- Node.js (v18+)
- Docker (optional)
- {config.database or 'PostgreSQL'}

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd {config.name}
```

2. Install dependencies
```bash
# Backend
cd backend
npm install  # or pip install -r requirements.txt, go mod download, etc.

# Frontend
cd ../frontend
npm install
```

3. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start the development servers
```bash
# Backend
cd backend
npm run dev

# Frontend (new terminal)
cd frontend
npm start
```

## Docker

```bash
docker-compose up -d
```

## Testing

```bash
npm test
```

## License

MIT
'''
    
    def _get_gitignore_template(self, config: ProjectConfig) -> str:
        return '''# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/
target/
Cargo.lock

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Testing
coverage/
.nyc_output/

# Database
*.sqlite
*.db

# Misc
.cache/
temp/
tmp/
'''
    
    def _get_env_example_template(self, config: ProjectConfig) -> str:
        return f'''# Application
NODE_ENV=development
PORT=5000

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME={config.name}
DB_USER=postgres
DB_PASSWORD=password

# MongoDB (if using MERN)
MONGODB_URI=mongodb://localhost:27017/{config.name}

# JWT
JWT_SECRET=your-secret-key-here
JWT_EXPIRE=7d

# Frontend
REACT_APP_API_URL=http://localhost:5000/api
'''
    
    def _get_license_template(self) -> str:
        return '''MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
    
    def _get_ci_workflow_template(self, config: ProjectConfig) -> str:
        return '''name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies (Backend)
      run: |
        cd backend
        npm ci
    
    - name: Install dependencies (Frontend)
      run: |
        cd frontend
        npm ci
    
    - name: Run linter
      run: |
        cd backend && npm run lint || true
        cd ../frontend && npm run lint || true
    
    - name: Run tests
      run: |
        cd backend && npm test || true
        cd ../frontend && npm test -- --watchAll=false || true
    
    - name: Build
      run: |
        cd frontend && npm run build
'''
    
    def _get_cd_workflow_template(self, config: ProjectConfig) -> str:
        return '''name: CD

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Build Docker images
      run: docker-compose build
    
    - name: Push to registry
      run: |
        echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
        docker-compose push
    
    - name: Deploy to production
      run: |
        # Add your deployment commands here
        echo "Deploying to production..."
'''


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Mrki Project Scaffolder")
    parser.add_argument("name", help="Project name")
    parser.add_argument("--stack", choices=[s.value for s in StackType], default="mern", help="Technology stack")
    parser.add_argument("--description", default="", help="Project description")
    parser.add_argument("--author", default="", help="Project author")
    
    args = parser.parse_args()
    
    config = ProjectConfig(
        name=args.name,
        stack=StackType(args.stack),
        description=args.description,
        author=args.author
    )
    
    scaffolder = ProjectScaffolder()
    result = scaffolder.scaffold(config)
    
    print(f"Project created at: {result['project_path']}")
    print(f"Stack: {result['stack']}")
    print(f"Features: {', '.join(result['features'])}")
    print(f"Files created: {len(result['created_files'])}")
