"""
Procedural Generation Systems
Dungeon generation, terrain generation, and other procedural content.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import math


class TileType(Enum):
    """Dungeon tile types."""
    EMPTY = 0
    FLOOR = 1
    WALL = 2
    DOOR = 3
    START = 4
    EXIT = 5
    TREASURE = 6
    ENEMY = 7
    TRAP = 8


@dataclass
class Room:
    """Represents a dungeon room."""
    x: int
    y: int
    width: int
    height: int
    
    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def intersects(self, other: "Room") -> bool:
        return (self.x <= other.x + other.width and
                self.x + self.width >= other.x and
                self.y <= other.y + other.height and
                self.y + self.height >= other.y)


@dataclass
class DungeonConfig:
    """Dungeon generation configuration."""
    width: int = 50
    height: int = 50
    min_room_size: int = 4
    max_room_size: int = 10
    max_rooms: int = 15
    corridor_width: int = 1
    enemy_spawn_chance: float = 0.1
    treasure_spawn_chance: float = 0.05
    trap_spawn_chance: float = 0.03
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "min_room_size": self.min_room_size,
            "max_room_size": self.max_room_size,
            "max_rooms": self.max_rooms,
            "corridor_width": self.corridor_width,
            "enemy_spawn_chance": self.enemy_spawn_chance,
            "treasure_spawn_chance": self.treasure_spawn_chance,
            "trap_spawn_chance": self.trap_spawn_chance
        }


class DungeonGenerator:
    """Procedural dungeon generator."""
    
    def __init__(self, config: DungeonConfig = None):
        self.config = config or DungeonConfig()
        self.grid: List[List[TileType]] = []
        self.rooms: List[Room] = []
    
    def generate(self) -> List[List[TileType]]:
        """Generate a dungeon."""
        # Initialize grid with empty tiles
        self.grid = [[TileType.EMPTY for _ in range(self.config.width)] 
                     for _ in range(self.config.height)]
        self.rooms = []
        
        # Generate rooms
        for _ in range(self.config.max_rooms):
            room = self._create_random_room()
            
            # Check if room intersects with existing rooms
            intersects = any(room.intersects(r) for r in self.rooms)
            
            if not intersects:
                self._carve_room(room)
                self.rooms.append(room)
        
        # Connect rooms with corridors
        for i in range(len(self.rooms) - 1):
            self._create_corridor(self.rooms[i], self.rooms[i + 1])
        
        # Place start and exit
        if self.rooms:
            start_room = self.rooms[0]
            exit_room = self.rooms[-1]
            
            self.grid[start_room.center[1]][start_room.center[0]] = TileType.START
            self.grid[exit_room.center[1]][exit_room.center[0]] = TileType.EXIT
        
        # Spawn enemies, treasures, and traps
        self._spawn_entities()
        
        return self.grid
    
    def _create_random_room(self) -> Room:
        """Create a random room."""
        width = random.randint(self.config.min_room_size, self.config.max_room_size)
        height = random.randint(self.config.min_room_size, self.config.max_room_size)
        
        x = random.randint(1, self.config.width - width - 1)
        y = random.randint(1, self.config.height - height - 1)
        
        return Room(x, y, width, height)
    
    def _carve_room(self, room: Room):
        """Carve a room into the grid."""
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if (y == room.y or y == room.y + room.height - 1 or
                    x == room.x or x == room.x + room.width - 1):
                    self.grid[y][x] = TileType.WALL
                else:
                    self.grid[y][x] = TileType.FLOOR
    
    def _create_corridor(self, room1: Room, room2: Room):
        """Create a corridor between two rooms."""
        center1 = room1.center
        center2 = room2.center
        
        # Randomly choose horizontal or vertical first
        if random.random() < 0.5:
            # Horizontal then vertical
            self._create_h_corridor(center1[0], center2[0], center1[1])
            self._create_v_corridor(center1[1], center2[1], center2[0])
        else:
            # Vertical then horizontal
            self._create_v_corridor(center1[1], center2[1], center1[0])
            self._create_h_corridor(center1[0], center2[0], center2[1])
    
    def _create_h_corridor(self, x1: int, x2: int, y: int):
        """Create a horizontal corridor."""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if self.grid[y][x] == TileType.EMPTY:
                self.grid[y][x] = TileType.FLOOR
                # Add walls above and below
                if y > 0 and self.grid[y - 1][x] == TileType.EMPTY:
                    self.grid[y - 1][x] = TileType.WALL
                if y < self.config.height - 1 and self.grid[y + 1][x] == TileType.EMPTY:
                    self.grid[y + 1][x] = TileType.WALL
    
    def _create_v_corridor(self, y1: int, y2: int, x: int):
        """Create a vertical corridor."""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if self.grid[y][x] == TileType.EMPTY:
                self.grid[y][x] = TileType.FLOOR
                # Add walls left and right
                if x > 0 and self.grid[y][x - 1] == TileType.EMPTY:
                    self.grid[y][x - 1] = TileType.WALL
                if x < self.config.width - 1 and self.grid[y][x + 1] == TileType.EMPTY:
                    self.grid[y][x + 1] = TileType.WALL
    
    def _spawn_entities(self):
        """Spawn enemies, treasures, and traps."""
        for room in self.rooms[1:-1]:  # Skip start and exit rooms
            for y in range(room.y + 1, room.y + room.height - 1):
                for x in range(room.x + 1, room.x + room.width - 1):
                    if self.grid[y][x] == TileType.FLOOR:
                        rand = random.random()
                        if rand < self.config.enemy_spawn_chance:
                            self.grid[y][x] = TileType.ENEMY
                        elif rand < self.config.enemy_spawn_chance + self.config.treasure_spawn_chance:
                            self.grid[y][x] = TileType.TREASURE
                        elif rand < (self.config.enemy_spawn_chance + 
                                    self.config.treasure_spawn_chance + 
                                    self.config.trap_spawn_chance):
                            self.grid[y][x] = TileType.TRAP
    
    def to_string(self) -> str:
        """Convert dungeon to string representation."""
        symbols = {
            TileType.EMPTY: ' ',
            TileType.FLOOR: '.',
            TileType.WALL: '#',
            TileType.DOOR: '+',
            TileType.START: 'S',
            TileType.EXIT: 'E',
            TileType.TREASURE: '$',
            TileType.ENEMY: 'X',
            TileType.TRAP: '^'
        }
        
        lines = []
        for row in self.grid:
            line = ''.join(symbols[tile] for tile in row)
            lines.append(line)
        
        return '\n'.join(lines)
    
    def export_to_json(self) -> Dict[str, Any]:
        """Export dungeon to JSON format."""
        return {
            "width": self.config.width,
            "height": self.config.height,
            "rooms": [{"x": r.x, "y": r.y, "width": r.width, "height": r.height} for r in self.rooms],
            "grid": [[tile.value for tile in row] for row in self.grid]
        }


@dataclass
class TerrainConfig:
    """Terrain generation configuration."""
    width: int = 100
    height: int = 100
    scale: float = 20.0
    octaves: int = 4
    persistence: float = 0.5
    lacunarity: float = 2.0
    seed: int = 0
    offset: Tuple[float, float] = (0, 0)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "scale": self.scale,
            "octaves": self.octaves,
            "persistence": self.persistence,
            "lacunarity": self.lacunarity,
            "seed": self.seed,
            "offset": self.offset
        }


class TerrainGenerator:
    """Procedural terrain generator using Perlin noise."""
    
    def __init__(self, config: TerrainConfig = None):
        self.config = config or TerrainConfig()
        self.height_map: List[List[float]] = []
    
    def generate(self) -> List[List[float]]:
        """Generate a height map."""
        self.height_map = [[0.0 for _ in range(self.config.width)] 
                          for _ in range(self.config.height)]
        
        # Generate Perlin noise
        for y in range(self.config.height):
            for x in range(self.config.width):
                self.height_map[y][x] = self._perlin_noise(x, y)
        
        return self.height_map
    
    def _perlin_noise(self, x: int, y: int) -> float:
        """Generate Perlin noise value."""
        amplitude = 1.0
        frequency = 1.0
        noise_height = 0.0
        
        for i in range(self.config.octaves):
            float_x = (x - self.config.width / 2) / self.config.scale * frequency + self.config.offset[0]
            float_y = (y - self.config.height / 2) / self.config.scale * frequency + self.config.offset[1]
            
            # Simple pseudo-random noise (simplified Perlin)
            noise_height += self._noise(float_x, float_y) * amplitude
            
            amplitude *= self.config.persistence
            frequency *= self.config.lacunarity
        
        # Normalize to 0-1 range
        return (noise_height + 1) / 2
    
    def _noise(self, x: float, y: float) -> float:
        """Simple noise function."""
        # Simple pseudo-random noise based on coordinates
        n = int(x * 374761393 + y * 668265263 + self.config.seed)
        n = (n << 13) ^ n
        n = n * (n * n * 15731 + 789221) + 1376312589
        return 1.0 - (n & 0x7fffffff) / 1073741824.0
    
    def get_biome_map(self, water_level: float = 0.3, 
                      grass_level: float = 0.6,
                      mountain_level: float = 0.8) -> List[List[str]]:
        """Convert height map to biome map."""
        biome_map = []
        
        for row in self.height_map:
            biome_row = []
            for height in row:
                if height < water_level:
                    biome_row.append("water")
                elif height < grass_level:
                    biome_row.append("grass")
                elif height < mountain_level:
                    biome_row.append("forest")
                else:
                    biome_row.append("mountain")
            biome_map.append(biome_row)
        
        return biome_map
    
    def export_to_json(self) -> Dict[str, Any]:
        """Export terrain to JSON format."""
        return {
            "config": self.config.to_dict(),
            "height_map": self.height_map
        }


class ProceduralGenerator:
    """Main procedural generation utility class."""
    
    @staticmethod
    def generate_random_name(syllables: int = 2) -> str:
        """Generate a random fantasy name."""
        consonants = "bcdfghjklmnpqrstvwxyz"
        vowels = "aeiou"
        
        name = ""
        for _ in range(syllables):
            name += random.choice(consonants).upper()
            name += random.choice(vowels)
            name += random.choice(consonants)
        
        return name
    
    @staticmethod
    def generate_loot_table(items: List[Dict[str, Any]], 
                           rarity_weights: Dict[str, float] = None) -> Dict[str, Any]:
        """Generate a loot table with weighted drops."""
        if rarity_weights is None:
            rarity_weights = {
                "common": 0.6,
                "uncommon": 0.25,
                "rare": 0.1,
                "epic": 0.04,
                "legendary": 0.01
            }
        
        loot_table = {}
        for item in items:
            rarity = item.get("rarity", "common")
            weight = rarity_weights.get(rarity, 0.1)
            loot_table[item["name"]] = {
                "weight": weight,
                "min_quantity": item.get("min_quantity", 1),
                "max_quantity": item.get("max_quantity", 1)
            }
        
        return loot_table
    
    @staticmethod
    def generate_quest(level: int = 1) -> Dict[str, Any]:
        """Generate a random quest."""
        quest_types = ["kill", "collect", "deliver", "escort", "explore"]
        quest_type = random.choice(quest_types)
        
        quest = {
            "type": quest_type,
            "level": level,
            "title": "",
            "description": "",
            "rewards": {
                "experience": level * 100,
                "gold": level * 50 + random.randint(0, 50)
            }
        }
        
        if quest_type == "kill":
            target_count = random.randint(3, 10)
            quest["title"] = f"Slay {target_count} Enemies"
            quest["description"] = f"Defeat {target_count} enemies in the nearby area."
            quest["objective"] = {"type": "kill", "count": target_count, "current": 0}
        
        elif quest_type == "collect":
            item_count = random.randint(3, 8)
            quest["title"] = f"Gather {item_count} Items"
            quest["description"] = f"Collect {item_count} items from the surrounding area."
            quest["objective"] = {"type": "collect", "count": item_count, "current": 0}
        
        elif quest_type == "deliver":
            quest["title"] = "Deliver Package"
            quest["description"] = "Deliver the package to the specified location."
            quest["objective"] = {"type": "deliver", "delivered": False}
        
        elif quest_type == "escort":
            quest["title"] = "Escort Mission"
            quest["description"] = "Escort the NPC safely to their destination."
            quest["objective"] = {"type": "escort", "escorted": False}
        
        elif quest_type == "explore":
            quest["title"] = "Explore Area"
            quest["description"] = "Explore the marked area on your map."
            quest["objective"] = {"type": "explore", "explored": False}
        
        return quest
    
    @staticmethod
    def generate_npc_dialogue(npc_type: str = "villager") -> List[Dict[str, str]]:
        """Generate NPC dialogue."""
        greetings = {
            "villager": ["Hello there!", "Greetings, traveler!", "Welcome to our village!"],
            "merchant": ["Looking to buy something?", "I have the finest goods!", "Welcome to my shop!"],
            "guard": ["Halt! State your business.", "Move along.", "Keep the peace."],
            "quest_giver": ["I have a task for you.", "Adventurer, I need your help!", "There's something you could do for me."]
        }
        
        farewells = {
            "villager": ["Safe travels!", "Come back soon!", "Goodbye!"],
            "merchant": ["Come again!", "Pleasure doing business!", "Farewell!"],
            "guard": ["Move along.", "Stay out of trouble.", "Dismissed."],
            "quest_giver": ["Return when you're done.", "I'll be waiting.", "Good luck!"]
        }
        
        greeting = random.choice(greetings.get(npc_type, greetings["villager"]))
        farewell = random.choice(farewells.get(npc_type, farewells["villager"]))
        
        return [
            {"speaker": npc_type, "text": greeting},
            {"speaker": "player", "text": "Hello."},
            {"speaker": npc_type, "text": farewell}
        ]
