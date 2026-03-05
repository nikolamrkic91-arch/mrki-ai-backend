"""
Mrki AI Module
Provides NPC AI and procedural generation systems for game development.
"""

from .npc_ai import NPCAI, BehaviorTree, StateMachineAI
from .procedural_generation import ProceduralGenerator, DungeonGenerator, TerrainGenerator

__all__ = [
    'NPCAI',
    'BehaviorTree',
    'StateMachineAI',
    'ProceduralGenerator',
    'DungeonGenerator',
    'TerrainGenerator'
]

__version__ = '1.0.0'
