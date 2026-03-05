# Mrki Game Development Module

Cross-platform game code generation for Unity, Unreal Engine, and Godot.

## Structure

```
gamedev/
├── unity/templates/          # Unity C# templates
│   ├── PlayerController.cs
│   ├── GameManager.cs
│   └── StateMachine.cs
├── unreal/templates/         # Unreal C++ templates
│   ├── ActorBase.h/.cpp
│   └── CharacterBase.h/.cpp
├── godot/templates/          # Godot GDScript templates
│   ├── player_controller.gd
│   ├── game_manager.gd
│   └── state_machine.gd
├── code_gen/
│   └── generator.py          # Core code generator
└── api.py                    # FastAPI endpoints
```

## Quick Start

### 1. Generate Code via Python

```python
from code_gen.generator import GameCodeGenerator, EngineType, TemplateType

gen = GameCodeGenerator()

# Generate Unity PlayerController
result = gen.generate_player_controller(
    engine=EngineType.UNITY,
    class_name="HeroController",
    namespace="AdventureGame",
    output_path="./HeroController.cs"
)

print(result.code)
```

### 2. Generate Code via API

Start the server:
```bash
python api.py
```

Generate code:
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "engine": "unity",
    "template": "player_controller",
    "class_name": "HeroController",
    "namespace": "AdventureGame"
  }'
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/engines` | GET | List supported engines |
| `/templates/{engine}` | GET | List templates for engine |
| `/generate` | POST | Generate code from template |
| `/generate/player-controller` | POST | Quick player controller |
| `/generate/game-manager` | POST | Quick game manager |
| `/batch-generate` | POST | Generate multiple files |
| `/preview/{engine}/{template}` | GET | Preview template |

## Supported Engines

### Unity (C#)
- **PlayerController** - Character movement with physics/kinematic options
- **GameManager** - Singleton game state manager with events
- **StateMachine** - Generic state machine for entities

### Unreal Engine (C++)
- **ActorBase** - Base actor class with activation system
- **CharacterBase** - Third-person character with Enhanced Input

### Godot (GDScript)
- **PlayerController** - 3D character controller with camera
- **GameManager** - Singleton with state management
- **StateMachine** - Flexible state machine

## Template Variables

All templates support these variables:
- `{{class_name}}` - Class name
- `{{namespace}}` - Namespace/module
- `{{description}}` - Class description

Engine-specific:
- Unreal: `{{api_macro}}` - API export macro
- Godot: `{{dont_destroy_on_load}}` - Persist flag

## Examples

### Unity GameManager
```python
gen.generate_game_manager(
    engine=EngineType.UNITY,
    class_name="AdventureManager",
    namespace="AdventureGame",
    description="Manages game state and systems"
)
```

### Unreal Character
```python
gen.generate(
    engine=EngineType.UNREAL,
    template=TemplateType.CHARACTER_BASE,
    class_name="HeroCharacter",
    namespace="MYGAME",
    extra_vars={"api_macro": "MYGAME_API"}
)
```

### Godot State Machine
```python
gen.generate_state_machine(
    engine=EngineType.GODOT,
    class_name="EnemyAI",
    namespace="",
    description="Enemy AI state machine"
)
```

## Extending

Add custom templates to `unity/templates/`, `unreal/templates/`, or `godot/templates/`.

Register in `generator.py`:
```python
template_map = {
    (EngineType.UNITY, TemplateType.YOUR_TEMPLATE): "unity/templates/YourTemplate.cs",
}
```

## License

MIT - Part of the Mrki platform
