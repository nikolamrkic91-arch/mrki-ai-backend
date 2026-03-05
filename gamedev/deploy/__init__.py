"""
Mrki Deployment Module
Provides cross-platform deployment configurations for game development.
"""

from .deployment_configs import DeploymentManager, PlatformConfig
from .build_scripts import BuildScriptGenerator

__all__ = [
    'DeploymentManager',
    'PlatformConfig',
    'BuildScriptGenerator'
]

__version__ = '1.0.0'
