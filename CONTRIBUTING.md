# Contributing to Mrki

Thank you for your interest in contributing to Mrki! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code:

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Virtual environment tool (venv, conda, or pyenv)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/mrki.git
   cd mrki
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/mrki/mrki.git
   ```

## Development Environment

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev,test,docs]"

# Install pre-commit hooks
pre-commit install

# Verify setup
make test
```

### Project Structure

```
mrki/
├── src/
│   └── mrki/           # Main source code
├── tests/              # Test files
├── docs/               # Documentation
├── .github/            # GitHub workflows and templates
├── scripts/            # Utility scripts
├── Makefile            # Common tasks
├── pyproject.toml      # Project configuration
└── README.md           # Project readme
```

## How to Contribute

### Reporting Bugs

Before creating a bug report:

1. Check if the bug has already been reported
2. Update to the latest version to see if it's fixed
3. Collect information about the bug

When creating a bug report, include:

- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, Mrki version)
- Relevant logs or error messages

Use the [bug report template](https://github.com/mrki/mrki/issues/new?template=bug_report.yml).

### Suggesting Features

Feature requests are welcome! Please:

1. Check if the feature has already been suggested
2. Provide a clear use case
3. Explain why it would be useful

Use the [feature request template](https://github.com/mrki/mrki/issues/new?template=feature_request.yml).

### Contributing Code

1. **Find or create an issue** to discuss your changes
2. **Create a branch** for your feature/fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following our coding standards
4. **Write tests** for new functionality
5. **Update documentation** as needed
6. **Run tests** and ensure they pass
7. **Commit** with a clear message
8. **Push** to your fork
9. **Create a Pull Request**

## Coding Standards

### Python Style

We follow PEP 8 with some modifications:

- Line length: 100 characters
- Use type hints where appropriate
- Docstrings in Google style

```python
def example_function(param1: str, param2: int) -> dict:
    """Short description.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param2 is negative
    """
    if param2 < 0:
        raise ValueError("param2 must be non-negative")
    return {"result": param1 * param2}
```

### Code Formatting

We use automated tools to ensure consistency:

```bash
# Format code
make format

# Run linter
make lint

# Type checking
make typecheck
```

### Import Order

```python
# Standard library
import os
import sys
from typing import Dict, List

# Third-party
import fastapi
import sqlalchemy

# Local
from mrki.core import Workflow
from mrki.utils import helper
```

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run specific test
pytest tests/test_workflow.py::test_specific

# Run with verbose output
pytest -v
```

### Writing Tests

- Use pytest for all tests
- Name test files with `test_` prefix
- Name test functions with `test_` prefix
- Use fixtures for common setup
- Aim for high test coverage

```python
import pytest
from mrki.core import Workflow

@pytest.fixture
def sample_workflow():
    return Workflow(name="test", steps=[])

def test_workflow_creation(sample_workflow):
    assert sample_workflow.name == "test"
    assert len(sample_workflow.steps) == 0
```

### Test Categories

- **Unit tests**: Test individual components
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows

## Documentation

### Code Documentation

- All public functions must have docstrings
- Include type hints
- Provide usage examples for complex functions

### User Documentation

Documentation is in the `docs/` directory using MkDocs:

```bash
# Serve docs locally
mkdocs serve

# Build docs
mkdocs build
```

### Documentation Style

- Use clear, concise language
- Include code examples
- Keep headings hierarchical
- Use admonitions for important notes

## Pull Request Process

### Before Submitting

1. **Update your branch**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks**:
   ```bash
   make check  # Runs lint, typecheck, and test
   ```

3. **Update documentation** if needed

4. **Add changelog entry** if applicable

### PR Guidelines

- Use a clear, descriptive title
- Reference related issues
- Describe what changed and why
- Include screenshots for UI changes
- Ensure CI checks pass

### Review Process

1. Maintainers will review your PR
2. Address any requested changes
3. Once approved, a maintainer will merge

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- MAJOR: Incompatible API changes
- MINOR: New functionality (backward compatible)
- PATCH: Bug fixes (backward compatible)

### Creating a Release

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```
4. GitHub Actions will automatically:
   - Build and publish to PyPI
   - Create GitHub release
   - Build and push Docker images

## Questions?

- 💬 [Discussions](https://github.com/mrki/mrki/discussions)
- 🐛 [Issues](https://github.com/mrki/mrki/issues)
- 📧 [Email](mailto:dev@mrki.dev)

## Recognition

Contributors will be:

- Listed in the CONTRIBUTORS file
- Mentioned in release notes
- Added to the GitHub contributors graph

Thank you for contributing to Mrki!
