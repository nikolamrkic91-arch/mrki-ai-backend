#!/usr/bin/env python3
"""
Mrki Test Manager
Generates and manages test files for various testing frameworks
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class TestType(Enum):
    """Types of tests"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    CONTRACT = "contract"
    PERFORMANCE = "performance"


class TestFramework(Enum):
    """Supported test frameworks"""
    JEST = "jest"
    VITEST = "vitest"
    MOCHA = "mocha"
    PYTEST = "pytest"
    UNITTEST = "unittest"
    GO_TEST = "go_test"
    RUST_TEST = "rust_test"
    JUNIT = "junit"
    XUNIT = "xunit"
    PLAYWRIGHT = "playwright"
    CYPRESS = "cypress"


@dataclass
class TestConfig:
    """Test configuration"""
    test_type: TestType
    framework: TestFramework
    coverage_threshold: float = 80.0
    parallel: bool = True
    timeout: int = 30000
    environment: Dict[str, str] = field(default_factory=dict)


class TestManager:
    """Test management class"""
    
    def __init__(self, output_path: str = "."):
        self.output_path = Path(output_path)
    
    def generate_test_files(self, project_path: Path, stack_type: str) -> List[str]:
        """Generate test files for a project"""
        created_files = []
        
        # Determine test frameworks based on stack
        if "django" in stack_type.lower():
            backend_framework = TestFramework.PYTEST
        elif "fastapi" in stack_type.lower():
            backend_framework = TestFramework.PYTEST
        elif "go" in stack_type.lower():
            backend_framework = TestFramework.GO_TEST
        elif "rust" in stack_type.lower():
            backend_framework = TestFramework.RUST_TEST
        elif "java" in stack_type.lower() or "spring" in stack_type.lower():
            backend_framework = TestFramework.JUNIT
        elif "dotnet" in stack_type.lower():
            backend_framework = TestFramework.XUNIT
        else:
            backend_framework = TestFramework.JEST
        
        frontend_framework = TestFramework.JEST
        e2e_framework = TestFramework.PLAYWRIGHT
        
        # Backend tests
        backend_tests = self._generate_backend_tests(project_path, backend_framework)
        created_files.extend(backend_tests)
        
        # Frontend tests
        frontend_tests = self._generate_frontend_tests(project_path, frontend_framework)
        created_files.extend(frontend_tests)
        
        # E2E tests
        e2e_tests = self._generate_e2e_tests(project_path, e2e_framework)
        created_files.extend(e2e_tests)
        
        # Test configuration
        config_files = self._generate_test_config(project_path, backend_framework, frontend_framework)
        created_files.extend(config_files)
        
        return created_files
    
    def _generate_backend_tests(self, project_path: Path, framework: TestFramework) -> List[str]:
        """Generate backend test files"""
        created_files = []
        
        if framework == TestFramework.PYTEST:
            tests_dir = project_path / "backend" / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            
            # __init__.py
            (tests_dir / "__init__.py").write_text("")
            
            # conftest.py
            conftest = tests_dir / "conftest.py"
            conftest.write_text(self._get_pytest_conftest())
            created_files.append(str(conftest))
            
            # test_api.py
            test_api = tests_dir / "test_api.py"
            test_api.write_text(self._get_pytest_api_tests())
            created_files.append(str(test_api))
            
            # test_models.py
            test_models = tests_dir / "test_models.py"
            test_models.write_text(self._get_pytest_model_tests())
            created_files.append(str(test_models))
        
        elif framework == TestFramework.JEST:
            tests_dir = project_path / "backend" / "__tests__"
            tests_dir.mkdir(parents=True, exist_ok=True)
            
            # api.test.js
            test_api = tests_dir / "api.test.js"
            test_api.write_text(self._get_jest_api_tests())
            created_files.append(str(test_api))
            
            # models.test.js
            test_models = tests_dir / "models.test.js"
            test_models.write_text(self._get_jest_model_tests())
            created_files.append(str(test_models))
        
        elif framework == TestFramework.GO_TEST:
            backend_dir = project_path / "backend"
            
            # handlers_test.go
            test_handlers = backend_dir / "handlers_test.go"
            test_handlers.write_text(self._get_go_handler_tests())
            created_files.append(str(test_handlers))
        
        elif framework == TestFramework.RUST_TEST:
            backend_dir = project_path / "backend" / "src"
            
            # Add tests to main.rs or create test files
            # Rust tests are typically inline
            pass
        
        return created_files
    
    def _generate_frontend_tests(self, project_path: Path, framework: TestFramework) -> List[str]:
        """Generate frontend test files"""
        created_files = []
        
        if framework == TestFramework.JEST:
            # src/__tests__/App.test.js
            tests_dir = project_path / "frontend" / "src" / "__tests__"
            tests_dir.mkdir(parents=True, exist_ok=True)
            
            test_app = tests_dir / "App.test.js"
            test_app.write_text(self._get_react_jest_tests())
            created_files.append(str(test_app))
            
            # SetupTests.js
            setup_tests = project_path / "frontend" / "src" / "setupTests.js"
            setup_tests.write_text(self._get_jest_setup())
            created_files.append(str(setup_tests))
        
        return created_files
    
    def _generate_e2e_tests(self, project_path: Path, framework: TestFramework) -> List[str]:
        """Generate E2E test files"""
        created_files = []
        
        if framework == TestFramework.PLAYWRIGHT:
            e2e_dir = project_path / "e2e"
            e2e_dir.mkdir(parents=True, exist_ok=True)
            
            # playwright.config.js
            config = e2e_dir / "playwright.config.js"
            config.write_text(self._get_playwright_config())
            created_files.append(str(config))
            
            # example.spec.js
            example = e2e_dir / "example.spec.js"
            example.write_text(self._get_playwright_tests())
            created_files.append(str(example))
        
        elif framework == TestFramework.CYPRESS:
            cypress_dir = project_path / "cypress"
            cypress_dir.mkdir(parents=True, exist_ok=True)
            
            # cypress.config.js
            config = project_path / "cypress.config.js"
            config.write_text(self._get_cypress_config())
            created_files.append(str(config))
            
            # e2e tests
            e2e_dir = cypress_dir / "e2e"
            e2e_dir.mkdir(parents=True, exist_ok=True)
            
            example = e2e_dir / "app.cy.js"
            example.write_text(self._get_cypress_tests())
            created_files.append(str(example))
        
        return created_files
    
    def _generate_test_config(self, project_path: Path, 
                              backend_framework: TestFramework,
                              frontend_framework: TestFramework) -> List[str]:
        """Generate test configuration files"""
        created_files = []
        
        # Backend jest config
        if backend_framework == TestFramework.JEST:
            config = project_path / "backend" / "jest.config.js"
            config.write_text(self._get_jest_config())
            created_files.append(str(config))
        
        # Frontend jest config
        if frontend_framework == TestFramework.JEST:
            config = project_path / "frontend" / "jest.config.js"
            config.write_text(self._get_jest_config_frontend())
            created_files.append(str(config))
        
        # Coverage config
        coverage_config = project_path / ".nycrc.json"
        coverage_config.write_text(self._get_nyc_config())
        created_files.append(str(coverage_config))
        
        return created_files
    
    # Test file templates
    def _get_pytest_conftest(self) -> str:
        return '''import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
'''
    
    def _get_pytest_api_tests(self) -> str:
        return '''import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_create_item(client: TestClient):
    """Test creating an item"""
    data = {"title": "Test Item", "description": "Test Description"}
    response = client.post("/api/items", json=data)
    assert response.status_code == 201
    assert response.json()["title"] == data["title"]


def test_get_items(client: TestClient):
    """Test getting all items"""
    response = client.get("/api/items")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_item(client: TestClient):
    """Test getting a single item"""
    # First create an item
    data = {"title": "Test Item"}
    create_response = client.post("/api/items", json=data)
    item_id = create_response.json()["id"]
    
    # Then get it
    response = client.get(f"/api/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["id"] == item_id


def test_update_item(client: TestClient):
    """Test updating an item"""
    # Create item
    data = {"title": "Original"}
    create_response = client.post("/api/items", json=data)
    item_id = create_response.json()["id"]
    
    # Update it
    update_data = {"title": "Updated"}
    response = client.put(f"/api/items/{item_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"


def test_delete_item(client: TestClient):
    """Test deleting an item"""
    # Create item
    data = {"title": "To Delete"}
    create_response = client.post("/api/items", json=data)
    item_id = create_response.json()["id"]
    
    # Delete it
    response = client.delete(f"/api/items/{item_id}")
    assert response.status_code == 204
    
    # Verify it's gone
    get_response = client.get(f"/api/items/{item_id}")
    assert get_response.status_code == 404
'''
    
    def _get_pytest_model_tests(self) -> str:
        return '''import pytest
from sqlalchemy.orm import Session
from app.models import User, Item


def test_create_user(db_session: Session):
    """Test creating a user"""
    user = User(email="test@example.com", name="Test User")
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
    assert user.email == "test@example.com"


def test_user_unique_email(db_session: Session):
    """Test that email must be unique"""
    user1 = User(email="unique@example.com", name="User 1")
    db_session.add(user1)
    db_session.commit()
    
    user2 = User(email="unique@example.com", name="User 2")
    db_session.add(user2)
    
    with pytest.raises(Exception):
        db_session.commit()


def test_create_item(db_session: Session):
    """Test creating an item"""
    user = User(email="item_test@example.com", name="Item Test")
    db_session.add(user)
    db_session.commit()
    
    item = Item(title="Test Item", description="Test", user_id=user.id)
    db_session.add(item)
    db_session.commit()
    
    assert item.id is not None
    assert item.user_id == user.id
'''
    
    def _get_jest_api_tests(self) -> str:
        return '''const request = require('supertest');
const app = require('../app');

describe('API Tests', () => {
  describe('GET /health', () => {
    it('should return health status', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);
      
      expect(response.body.status).toBe('OK');
    });
  });

  describe('POST /api/items', () => {
    it('should create a new item', async () => {
      const data = { title: 'Test Item', description: 'Test' };
      
      const response = await request(app)
        .post('/api/items')
        .send(data)
        .expect(201);
      
      expect(response.body.title).toBe(data.title);
      expect(response.body.id).toBeDefined();
    });

    it('should validate required fields', async () => {
      const response = await request(app)
        .post('/api/items')
        .send({})
        .expect(400);
      
      expect(response.body.error).toBeDefined();
    });
  });

  describe('GET /api/items', () => {
    it('should return list of items', async () => {
      const response = await request(app)
        .get('/api/items')
        .expect(200);
      
      expect(Array.isArray(response.body)).toBe(true);
    });
  });

  describe('GET /api/items/:id', () => {
    it('should return a single item', async () => {
      // Create item first
      const createRes = await request(app)
        .post('/api/items')
        .send({ title: 'Test' });
      
      const itemId = createRes.body.id;
      
      const response = await request(app)
        .get(`/api/items/${itemId}`)
        .expect(200);
      
      expect(response.body.id).toBe(itemId);
    });

    it('should return 404 for non-existent item', async () => {
      await request(app)
        .get('/api/items/999999')
        .expect(404);
    });
  });
});
'''
    
    def _get_jest_model_tests(self) -> str:
        return '''const { User, Item } = require('../models');

describe('Model Tests', () => {
  describe('User Model', () => {
    it('should create a user', async () => {
      const user = new User({
        email: 'test@example.com',
        name: 'Test User',
        password: 'password123'
      });
      
      await user.save();
      expect(user._id).toBeDefined();
      expect(user.email).toBe('test@example.com');
    });

    it('should require email', async () => {
      const user = new User({ name: 'Test' });
      
      await expect(user.save()).rejects.toThrow();
    });
  });

  describe('Item Model', () => {
    it('should create an item', async () => {
      const user = await User.create({
        email: 'item_test@example.com',
        name: 'Test',
        password: 'password'
      });

      const item = new Item({
        title: 'Test Item',
        description: 'Test',
        user: user._id
      });
      
      await item.save();
      expect(item._id).toBeDefined();
    });
  });
});
'''
    
    def _get_go_handler_tests(self) -> str:
        return '''package main

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func setupRouter() *gin.Engine {
	r := gin.Default()
	r.GET("/health", HealthCheck)
	r.GET("/api/items", GetItems)
	return r
}

func TestHealthCheck(t *testing.T) {
	router := setupRouter()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/health", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code)
	assert.Contains(t, w.Body.String(), "OK")
}

func TestGetItems(t *testing.T) {
	router := setupRouter()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/items", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code)
}
'''
    
    def _get_react_jest_tests(self) -> str:
        return '''import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import App from '../App';

describe('App Component', () => {
  it('renders without crashing', () => {
    render(<App />);
    expect(document.body.contains(document.body)).toBe(true);
  });

  it('renders navigation', () => {
    render(<App />);
    expect(screen.getByText(/home/i)).toBeInTheDocument();
  });
});

// Example component test
describe('Button Component', () => {
  const Button = ({ onClick, children }) => (
    <button onClick={onClick}>{children}</button>
  );

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByText(/click me/i));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
'''
    
    def _get_jest_setup(self) -> str:
        return '''// Jest setup file
import '@testing-library/jest-dom';

// Mock fetch globally
global.fetch = jest.fn();

// Setup environment variables
process.env.REACT_APP_API_URL = 'http://localhost:5000/api';

// Cleanup after each test
afterEach(() => {
  jest.clearAllMocks();
});
'''
    
    def _get_playwright_config(self) -> str:
        return '''// @ts-check
const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
  webServer: {
    command: 'npm run start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
'''
    
    def _get_playwright_tests(self) -> str:
        return '''const { test, expect } = require('@playwright/test');

test.describe('Application E2E Tests', () => {
  test('homepage has correct title', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/My App/i);
  });

  test('navigation works', async ({ page }) => {
    await page.goto('/');
    
    // Click on About link
    await page.click('text=About');
    await expect(page).toHaveURL(/.*about/);
  });

  test('form submission', async ({ page }) => {
    await page.goto('/contact');
    
    // Fill form
    await page.fill('[name="name"]', 'Test User');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="message"]', 'Test message');
    
    // Submit
    await page.click('button[type="submit"]');
    
    // Check for success message
    await expect(page.locator('.success-message')).toBeVisible();
  });

  test('API integration', async ({ page }) => {
    await page.goto('/items');
    
    // Wait for items to load
    await page.waitForSelector('.item');
    
    // Check items are displayed
    const items = await page.locator('.item').count();
    expect(items).toBeGreaterThan(0);
  });
});
'''
    
    def _get_cypress_config(self) -> str:
        return '''const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
  },
  component: {
    devServer: {
      framework: 'create-react-app',
      bundler: 'webpack',
    },
  },
})
'''
    
    def _get_cypress_tests(self) -> str:
        return '''describe('Application E2E Tests', () => {
  beforeEach(() => {
    cy.visit('/');
  });

  it('displays the homepage', () => {
    cy.contains('Welcome');
  });

  it('navigates to about page', () => {
    cy.contains('About').click();
    cy.url().should('include', '/about');
    cy.contains('About');
  });

  it('submits a form', () => {
    cy.visit('/contact');
    
    cy.get('[name="name"]').type('Test User');
    cy.get('[name="email"]').type('test@example.com');
    cy.get('[name="message"]').type('Test message');
    
    cy.get('button[type="submit"]').click();
    
    cy.get('.success-message').should('be.visible');
  });

  it('loads items from API', () => {
    cy.visit('/items');
    
    cy.intercept('GET', '/api/items').as('getItems');
    cy.wait('@getItems');
    
    cy.get('.item').should('have.length.at.least', 1);
  });
});
'''
    
    def _get_jest_config(self) -> str:
        return '''module.exports = {
  testEnvironment: 'node',
  coverageDirectory: 'coverage',
  collectCoverageFrom: [
    '**/*.js',
    '!**/node_modules/**',
    '!**/coverage/**',
    '!jest.config.js',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  testMatch: [
    '**/__tests__/**/*.test.js',
  ],
  setupFilesAfterEnv: ['<rootDir>/__tests__/setup.js'],
};
'''
    
    def _get_jest_config_frontend(self) -> str:
        return '''module.exports = {
  testEnvironment: 'jsdom',
  coverageDirectory: 'coverage',
  collectCoverageFrom: [
    'src/**/*.{js,jsx}',
    '!src/index.js',
    '!src/serviceWorker.js',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.js'],
  moduleNameMapping: {
    '\\.(css|less|scss)$': 'identity-obj-proxy',
  },
};
'''
    
    def _get_nyc_config(self) -> str:
        return '''{
  "all": true,
  "check-coverage": true,
  "reporter": ["text", "text-summary", "html", "lcov"],
  "include": ["src/**/*.js"],
  "exclude": [
    "**/*.test.js",
    "**/node_modules/**",
    "**/coverage/**"
  ],
  "branches": 80,
  "functions": 80,
  "lines": 80,
  "statements": 80
}
'''


if __name__ == "__main__":
    manager = TestManager()
    
    # Example usage
    test_files = manager.generate_test_files(Path("./test-project"), "mern")
    print(f"Generated {len(test_files)} test files")
