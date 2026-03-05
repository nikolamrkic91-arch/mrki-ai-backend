"""
Mrki Game Code Generation Module
Provides 2D/3D game code generation for multiple engines.
"""

from .game_code_generator import GameCodeGenerator, CodeTemplate
from .pattern_library import PatternLibrary

__all__ = [
    'GameCodeGenerator',
    'CodeTemplate',
    'PatternLibrary'
]

__version__ = '1.0.0'
