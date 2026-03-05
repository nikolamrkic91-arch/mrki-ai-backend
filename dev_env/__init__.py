"""
Mrki - Full-Stack Development Environment
A comprehensive toolkit for building modern full-stack applications
"""

__version__ = "1.0.0"
__author__ = "Mrki Dev Team"

from .project_scaffolder import ProjectScaffolder
from .git_ops import GitOps
from .code_gen import CodeGenerator
from .database import DatabaseManager
from .api_builder import APIBuilder
from .docker import DockerManager
from .testing import TestManager

__all__ = [
    "ProjectScaffolder",
    "GitOps", 
    "CodeGenerator",
    "DatabaseManager",
    "APIBuilder",
    "DockerManager",
    "TestManager",
]
