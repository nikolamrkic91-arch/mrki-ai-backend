"""
Mrki Animation System Module
Provides animation controllers and state machines for game development.
"""

from .animation_controllers import AnimationController, AnimationStateMachine
from .tween_systems import TweenSystem, TweenConfig

__all__ = [
    'AnimationController',
    'AnimationStateMachine',
    'TweenSystem',
    'TweenConfig'
]

__version__ = '1.0.0'
