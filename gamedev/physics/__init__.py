"""
Mrki Physics System Module
Provides physics templates and configurations for game development.
"""

from .physics_templates import PhysicsTemplates, PhysicsConfig
from .collision_systems import CollisionSystem, CollisionConfig

__all__ = [
    'PhysicsTemplates',
    'PhysicsConfig',
    'CollisionSystem',
    'CollisionConfig'
]

__version__ = '1.0.0'
