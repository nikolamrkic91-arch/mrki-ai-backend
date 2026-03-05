"""
Mrki Unity Integration Module
Provides Unity engine integration, C# code generation, and project management.
"""

from .unity_adapter import UnityAdapter, UnityProjectConfig
from .csharp_generator import CSharpCodeGenerator
from .templates import UnityTemplates

__all__ = [
    'UnityAdapter',
    'UnityProjectConfig',
    'CSharpCodeGenerator',
    'UnityTemplates'
]

__version__ = '1.0.0'
