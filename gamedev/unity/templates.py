"""
Unity Project Templates
Pre-configured templates for common Unity game types.
"""

from .unity_adapter import UnityProjectConfig
from .csharp_generator import CSharpCodeGenerator, Field, Method, Property, AccessModifier
from typing import Dict, List, Any


class UnityTemplates:
    """Collection of Unity project templates."""
    
    @staticmethod
    def create_2d_platformer(name: str) -> Dict[str, Any]:
        """Create a 2D platformer project configuration."""
        config = UnityProjectConfig(
            name=name,
            template="2d",
            render_pipeline="builtin",
            packages=[
                "input_system",
                "cinemachine",
                "textmeshpro"
            ],
            platforms=["StandaloneWindows64", "Android", "WebGL"]
        )
        
        scripts = {
            "PlayerController2D": UnityTemplates._player_controller_2d(),
            "CameraFollow": UnityTemplates._camera_follow_2d(),
            "Platform": UnityTemplates._platform_script(),
            "Collectible": UnityTemplates._collectible_script(),
            "GameManager": UnityTemplates._game_manager(),
            "LevelManager": UnityTemplates._level_manager(),
            "EnemyPatrol": UnityTemplates._enemy_patrol_2d(),
            "HealthSystem": UnityTemplates._health_system()
        }
        
        return {
            "config": config,
            "scripts": scripts
        }
    
    @staticmethod
    def create_3d_fps(name: str) -> Dict[str, Any]:
        """Create a 3D FPS project configuration."""
        config = UnityProjectConfig(
            name=name,
            template="3d",
            render_pipeline="urp",
            packages=[
                "input_system",
                "cinemachine",
                "ai_navigation",
                "textmeshpro",
                "post_processing"
            ],
            platforms=["StandaloneWindows64", "StandaloneLinux64", "PS5", "XboxOne"]
        )
        
        scripts = {
            "FPSController": UnityTemplates._fps_controller(),
            "WeaponSystem": UnityTemplates._weapon_system(),
            "HealthSystem": UnityTemplates._health_system_3d(),
            "EnemyAI": UnityTemplates._enemy_ai_fps(),
            "GameManager": UnityTemplates._game_manager_fps(),
            "AmmoSystem": UnityTemplates._ammo_system(),
            "Damageable": UnityTemplates._damageable(),
            "PickUp": UnityTemplates._pickup_item()
        }
        
        return {
            "config": config,
            "scripts": scripts
        }
    
    @staticmethod
    def create_rpg(name: str) -> Dict[str, Any]:
        """Create an RPG project configuration."""
        config = UnityProjectConfig(
            name=name,
            template="3d",
            render_pipeline="urp",
            packages=[
                "input_system",
                "cinemachine",
                "ai_navigation",
                "textmeshpro",
                "timeline"
            ],
            platforms=["StandaloneWindows64", "StandaloneOSX", "StandaloneLinux64"]
        )
        
        scripts = {
            "PlayerMovement": UnityTemplates._rpg_player_movement(),
            "CharacterStats": UnityTemplates._character_stats(),
            "InventorySystem": UnityTemplates._inventory_system(),
            "QuestSystem": UnityTemplates._quest_system(),
            "DialogueSystem": UnityTemplates._dialogue_system(),
            "CombatSystem": UnityTemplates._combat_system(),
            "NPCController": UnityTemplates._npc_controller(),
            "SaveSystem": UnityTemplates._save_system()
        }
        
        return {
            "config": config,
            "scripts": scripts
        }
    
    @staticmethod
    def create_puzzle(name: str) -> Dict[str, Any]:
        """Create a puzzle game project configuration."""
        config = UnityProjectConfig(
            name=name,
            template="2d",
            render_pipeline="builtin",
            packages=[
                "input_system",
                "textmeshpro"
            ],
            platforms=["StandaloneWindows64", "Android", "iOS", "WebGL"]
        )
        
        scripts = {
            "GridManager": UnityTemplates._grid_manager(),
            "PuzzlePiece": UnityTemplates._puzzle_piece(),
            "GameBoard": UnityTemplates._game_board(),
            "LevelProgression": UnityTemplates._level_progression(),
            "ScoreManager": UnityTemplates._score_manager(),
            "HintSystem": UnityTemplates._hint_system(),
            "AudioManager": UnityTemplates._audio_manager()
        }
        
        return {
            "config": config,
            "scripts": scripts
        }
    
    @staticmethod
    def _player_controller_2d() -> str:
        """Generate 2D player controller."""
        gen = CSharpCodeGenerator()
        gen.set_class("PlayerController2D")
        gen.set_summary("2D platformer player controller")
        
        gen.add_field(Field(
            name="moveSpeed",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="5f",
            serialize_field=True,
            tooltip="Movement speed"
        ))
        
        gen.add_field(Field(
            name="jumpForce",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="12f",
            serialize_field=True,
            tooltip="Jump force"
        ))
        
        gen.add_field(Field(
            name="rb",
            type="Rigidbody2D",
            access=AccessModifier.PRIVATE
        ))
        
        gen.add_field(Field(
            name="groundCheck",
            type="Transform",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="groundLayer",
            type="LayerMask",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="facingRight",
            type="bool",
            access=AccessModifier.PRIVATE,
            default_value="true"
        ))
        
        gen.add_method(Method(
            name="Start",
            access=AccessModifier.PRIVATE,
            body=["rb = GetComponent<Rigidbody2D>();"]
        ))
        
        gen.add_method(Method(
            name="Update",
            access=AccessModifier.PRIVATE,
            body=[
                "HandleMovement();",
                "HandleJump();"
            ]
        ))
        
        gen.add_method(Method(
            name="HandleMovement",
            access=AccessModifier.PRIVATE,
            body=[
                "float moveInput = Input.GetAxisRaw(\"Horizontal\");",
                "rb.velocity = new Vector2(moveInput * moveSpeed, rb.velocity.y);",
                "",
                "if (moveInput > 0 && !facingRight)",
                "    Flip();",
                "else if (moveInput < 0 && facingRight)",
                "    Flip();"
            ]
        ))
        
        gen.add_method(Method(
            name="HandleJump",
            access=AccessModifier.PRIVATE,
            body=[
                "if (Input.GetButtonDown(\"Jump\") && IsGrounded())",
                "{",
                "    rb.velocity = new Vector2(rb.velocity.x, jumpForce);",
                "}"
            ]
        ))
        
        gen.add_method(Method(
            name="Flip",
            access=AccessModifier.PRIVATE,
            body=[
                "facingRight = !facingRight;",
                "Vector3 scale = transform.localScale;",
                "scale.x *= -1;",
                "transform.localScale = scale;"
            ]
        ))
        
        gen.add_method(Method(
            name="IsGrounded",
            access=AccessModifier.PRIVATE,
            return_type="bool",
            body=[
                "return Physics2D.OverlapCircle(groundCheck.position, 0.2f, groundLayer);"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _fps_controller() -> str:
        """Generate FPS controller."""
        gen = CSharpCodeGenerator()
        gen.set_class("FPSController")
        gen.set_summary("First-person shooter controller")
        
        gen.add_field(Field(
            name="moveSpeed",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="5f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="mouseSensitivity",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="100f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="jumpForce",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="10f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="gravity",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="-9.81f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="groundCheck",
            type="Transform",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="groundDistance",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="0.4f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="groundMask",
            type="LayerMask",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="controller",
            type="CharacterController",
            access=AccessModifier.PRIVATE
        ))
        
        gen.add_field(Field(
            name="cameraTransform",
            type="Transform",
            access=AccessModifier.PRIVATE
        ))
        
        gen.add_field(Field(
            name="velocity",
            type="Vector3",
            access=AccessModifier.PRIVATE
        ))
        
        gen.add_field(Field(
            name="isGrounded",
            type="bool",
            access=AccessModifier.PRIVATE
        ))
        
        gen.add_field(Field(
            name="xRotation",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="0f"
        ))
        
        gen.add_method(Method(
            name="Start",
            access=AccessModifier.PRIVATE,
            body=[
                "controller = GetComponent<CharacterController>();",
                "cameraTransform = Camera.main.transform;",
                "Cursor.lockState = CursorLockMode.Locked;"
            ]
        ))
        
        gen.add_method(Method(
            name="Update",
            access=AccessModifier.PRIVATE,
            body=[
                "HandleGroundCheck();",
                "HandleMovement();",
                "HandleLook();",
                "HandleJump();",
                "ApplyGravity();"
            ]
        ))
        
        gen.add_method(Method(
            name="HandleGroundCheck",
            access=AccessModifier.PRIVATE,
            body=[
                "isGrounded = Physics.CheckSphere(groundCheck.position, groundDistance, groundMask);",
                "if (isGrounded && velocity.y < 0)",
                "    velocity.y = -2f;"
            ]
        ))
        
        gen.add_method(Method(
            name="HandleMovement",
            access=AccessModifier.PRIVATE,
            body=[
                "float x = Input.GetAxis(\"Horizontal\");",
                "float z = Input.GetAxis(\"Vertical\");",
                "",
                "Vector3 move = transform.right * x + transform.forward * z;",
                "controller.Move(move * moveSpeed * Time.deltaTime);"
            ]
        ))
        
        gen.add_method(Method(
            name="HandleLook",
            access=AccessModifier.PRIVATE,
            body=[
                "float mouseX = Input.GetAxis(\"Mouse X\") * mouseSensitivity * Time.deltaTime;",
                "float mouseY = Input.GetAxis(\"Mouse Y\") * mouseSensitivity * Time.deltaTime;",
                "",
                "xRotation -= mouseY;",
                "xRotation = Mathf.Clamp(xRotation, -90f, 90f);",
                "",
                "cameraTransform.localRotation = Quaternion.Euler(xRotation, 0f, 0f);",
                "transform.Rotate(Vector3.up * mouseX);"
            ]
        ))
        
        gen.add_method(Method(
            name="HandleJump",
            access=AccessModifier.PRIVATE,
            body=[
                "if (Input.GetButtonDown(\"Jump\") && isGrounded)",
                "{",
                "    velocity.y = Mathf.Sqrt(jumpForce * -2f * gravity);",
                "}"
            ]
        ))
        
        gen.add_method(Method(
            name="ApplyGravity",
            access=AccessModifier.PRIVATE,
            body=[
                "velocity.y += gravity * Time.deltaTime;",
                "controller.Move(velocity * Time.deltaTime);"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _game_manager() -> str:
        """Generate game manager."""
        gen = CSharpCodeGenerator()
        gen.set_class("GameManager")
        gen.set_summary("Central game manager")
        
        gen.add_field(Field(
            name="_instance",
            type="GameManager",
            access=AccessModifier.PRIVATE,
            attributes=["[SerializeField]"]
        ))
        
        gen.add_field(Field(
            name="gameState",
            type="GameState",
            access=AccessModifier.PRIVATE,
            default_value="GameState.MainMenu"
        ))
        
        gen.add_field(Field(
            name="score",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="0"
        ))
        
        gen.add_property(Property(
            name="Instance",
            type="GameManager",
            getter=True,
            setter=False
        ))
        
        gen.add_property(Property(
            name="CurrentState",
            type="GameState",
            getter=True,
            setter=True
        ))
        
        gen.add_method(Method(
            name="Awake",
            access=AccessModifier.PRIVATE,
            body=[
                "if (_instance != null && _instance != this)",
                "{",
                '    Destroy(gameObject);',
                "    return;",
                "}",
                "",
                "_instance = this;",
                "DontDestroyOnLoad(gameObject);"
            ]
        ))
        
        gen.add_method(Method(
            name="ChangeState",
            access=AccessModifier.PUBLIC,
            parameters=[("GameState", "newState")],
            body=[
                "gameState = newState;",
                "OnStateChanged?.Invoke(newState);"
            ]
        ))
        
        gen.add_method(Method(
            name="AddScore",
            access=AccessModifier.PUBLIC,
            parameters=[("int", "points")],
            body=[
                "score += points;",
                "OnScoreChanged?.Invoke(score);"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _camera_follow_2d() -> str:
        """Generate 2D camera follow."""
        gen = CSharpCodeGenerator()
        gen.set_class("CameraFollow2D")
        gen.set_summary("Smooth 2D camera follow")
        
        gen.add_field(Field(
            name="target",
            type="Transform",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="smoothSpeed",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="0.125f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="offset",
            type="Vector3",
            access=AccessModifier.PRIVATE,
            default_value="new Vector3(0f, 0f, -10f)",
            serialize_field=True
        ))
        
        gen.add_method(Method(
            name="LateUpdate",
            access=AccessModifier.PRIVATE,
            body=[
                "if (target == null) return;",
                "",
                "Vector3 desiredPosition = target.position + offset;",
                "Vector3 smoothedPosition = Vector3.Lerp(transform.position, desiredPosition, smoothSpeed);",
                "transform.position = smoothedPosition;"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _health_system() -> str:
        """Generate health system."""
        gen = CSharpCodeGenerator()
        gen.set_class("HealthSystem")
        gen.set_summary("Health management system")
        
        gen.add_field(Field(
            name="maxHealth",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="100",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="currentHealth",
            type="int",
            access=AccessModifier.PRIVATE
        ))
        
        gen.add_property(Property(
            name="Health",
            type="int",
            getter=True,
            setter=False
        ))
        
        gen.add_property(Property(
            name="IsDead",
            type="bool",
            getter=True,
            setter=False
        ))
        
        gen.add_method(Method(
            name="Start",
            access=AccessModifier.PRIVATE,
            body=["currentHealth = maxHealth;"]
        ))
        
        gen.add_method(Method(
            name="TakeDamage",
            access=AccessModifier.PUBLIC,
            parameters=[("int", "damage")],
            body=[
                "currentHealth -= damage;",
                "currentHealth = Mathf.Clamp(currentHealth, 0, maxHealth);",
                "",
                "OnHealthChanged?.Invoke(currentHealth);",
                "",
                "if (currentHealth <= 0)",
                "    Die();"
            ]
        ))
        
        gen.add_method(Method(
            name="Heal",
            access=AccessModifier.PUBLIC,
            parameters=[("int", "amount")],
            body=[
                "currentHealth += amount;",
                "currentHealth = Mathf.Clamp(currentHealth, 0, maxHealth);",
                "OnHealthChanged?.Invoke(currentHealth);"
            ]
        ))
        
        gen.add_method(Method(
            name="Die",
            access=AccessModifier.PRIVATE,
            body=[
                "OnDeath?.Invoke();",
                "Destroy(gameObject);"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _enemy_patrol_2d() -> str:
        """Generate enemy patrol script."""
        gen = CSharpCodeGenerator()
        gen.set_class("EnemyPatrol2D")
        gen.set_summary("2D enemy patrol behavior")
        
        gen.add_field(Field(
            name="patrolPoints",
            type="Transform[]",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="moveSpeed",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="2f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="waitTime",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="1f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="currentPointIndex",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="0"
        ))
        
        gen.add_field(Field(
            name="waitTimer",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="0f"
        ))
        
        gen.add_field(Field(
            name="isWaiting",
            type="bool",
            access=AccessModifier.PRIVATE,
            default_value="false"
        ))
        
        gen.add_method(Method(
            name="Update",
            access=AccessModifier.PRIVATE,
            body=[
                "if (patrolPoints.Length == 0) return;",
                "",
                "if (isWaiting)",
                "{",
                "    waitTimer -= Time.deltaTime;",
                "    if (waitTimer <= 0)",
                "        isWaiting = false;",
                "    return;",
                "}",
                "",
                "Transform targetPoint = patrolPoints[currentPointIndex];",
                "transform.position = Vector2.MoveTowards(transform.position, targetPoint.position, moveSpeed * Time.deltaTime);",
                "",
                "if (Vector2.Distance(transform.position, targetPoint.position) < 0.1f)",
                "{",
                "    currentPointIndex = (currentPointIndex + 1) % patrolPoints.Length;",
                "    isWaiting = true;",
                "    waitTimer = waitTime;",
                "}"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _weapon_system() -> str:
        """Generate weapon system."""
        gen = CSharpCodeGenerator()
        gen.set_class("WeaponSystem")
        gen.set_summary("FPS weapon system")
        
        gen.add_field(Field(
            name="damage",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="25",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="range",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="100f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="fireRate",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="0.1f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="muzzleFlash",
            type="ParticleSystem",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="cameraTransform",
            type="Transform",
            access=AccessModifier.PRIVATE
        ))
        
        gen.add_field(Field(
            name="nextTimeToFire",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="0f"
        ))
        
        gen.add_method(Method(
            name="Start",
            access=AccessModifier.PRIVATE,
            body=["cameraTransform = Camera.main.transform;"]
        ))
        
        gen.add_method(Method(
            name="Update",
            access=AccessModifier.PRIVATE,
            body=[
                "if (Input.GetButton(\"Fire1\") && Time.time >= nextTimeToFire)",
                "{",
                "    nextTimeToFire = Time.time + fireRate;",
                "    Shoot();",
                "}"
            ]
        ))
        
        gen.add_method(Method(
            name="Shoot",
            access=AccessModifier.PRIVATE,
            body=[
                "muzzleFlash?.Play();",
                "",
                "RaycastHit hit;",
                "if (Physics.Raycast(cameraTransform.position, cameraTransform.forward, out hit, range))",
                "{",
                "    var damageable = hit.transform.GetComponent<IDamageable>();",
                "    damageable?.TakeDamage(damage);",
                "}"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _character_stats() -> str:
        """Generate RPG character stats."""
        gen = CSharpCodeGenerator()
        gen.set_class("CharacterStats")
        gen.set_summary("RPG character statistics")
        
        gen.add_field(Field(
            name="level",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="1",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="experience",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="0"
        ))
        
        gen.add_field(Field(
            name="strength",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="10",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="agility",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="10",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="intelligence",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="10",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="vitality",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="10",
            serialize_field=True
        ))
        
        gen.add_property(Property(
            name="MaxHealth",
            type="int",
            getter=True,
            setter=False
        ))
        
        gen.add_property(Property(
            name="AttackPower",
            type="int",
            getter=True,
            setter=False
        ))
        
        gen.add_method(Method(
            name="AddExperience",
            access=AccessModifier.PUBLIC,
            parameters=[("int", "amount")],
            body=[
                "experience += amount;",
                "CheckLevelUp();"
            ]
        ))
        
        gen.add_method(Method(
            name="CheckLevelUp",
            access=AccessModifier.PRIVATE,
            body=[
                "int expNeeded = GetExperienceForLevel(level + 1);",
                "if (experience >= expNeeded)",
                "{",
                "    experience -= expNeeded;",
                "    LevelUp();",
                "}"
            ]
        ))
        
        gen.add_method(Method(
            name="LevelUp",
            access=AccessModifier.PRIVATE,
            body=[
                "level++;",
                "OnLevelUp?.Invoke(level);"
            ]
        ))
        
        gen.add_method(Method(
            name="GetExperienceForLevel",
            access=AccessModifier.PRIVATE,
            return_type="int",
            parameters=[("int", "targetLevel")],
            body=[
                "return targetLevel * 100;"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _inventory_system() -> str:
        """Generate inventory system."""
        gen = CSharpCodeGenerator()
        gen.set_class("InventorySystem")
        gen.set_summary("Item inventory management")
        
        gen.add_field(Field(
            name="items",
            type="List<Item>",
            access=AccessModifier.PRIVATE,
            default_value="new List<Item>()"
        ))
        
        gen.add_field(Field(
            name="maxSlots",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="20",
            serialize_field=True
        ))
        
        gen.add_property(Property(
            name="ItemCount",
            type="int",
            getter=True,
            setter=False
        ))
        
        gen.add_property(Property(
            name="IsFull",
            type="bool",
            getter=True,
            setter=False
        ))
        
        gen.add_method(Method(
            name="AddItem",
            access=AccessModifier.PUBLIC,
            return_type="bool",
            parameters=[("Item", "item")],
            body=[
                "if (IsFull) return false;",
                "",
                "items.Add(item);",
                "OnItemAdded?.Invoke(item);",
                "return true;"
            ]
        ))
        
        gen.add_method(Method(
            name="RemoveItem",
            access=AccessModifier.PUBLIC,
            return_type="bool",
            parameters=[("Item", "item")],
            body=[
                "if (items.Remove(item))",
                "{",
                "    OnItemRemoved?.Invoke(item);",
                "    return true;",
                "}",
                "return false;"
            ]
        ))
        
        gen.add_method(Method(
            name="HasItem",
            access=AccessModifier.PUBLIC,
            return_type="bool",
            parameters=[("string", "itemId")],
            body=[
                "return items.Exists(i => i.Id == itemId);"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _grid_manager() -> str:
        """Generate grid manager for puzzle games."""
        gen = CSharpCodeGenerator()
        gen.set_class("GridManager")
        gen.set_summary("Grid-based puzzle game manager")
        
        gen.add_field(Field(
            name="gridWidth",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="8",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="gridHeight",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="8",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="cellSize",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="1f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="grid",
            type="GameObject[,]",
            access=AccessModifier.PRIVATE
        ))
        
        gen.add_field(Field(
            name="piecePrefabs",
            type="GameObject[]",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_method(Method(
            name="Start",
            access=AccessModifier.PRIVATE,
            body=[
                "grid = new GameObject[gridWidth, gridHeight];",
                "InitializeGrid();"
            ]
        ))
        
        gen.add_method(Method(
            name="InitializeGrid",
            access=AccessModifier.PRIVATE,
            body=[
                "for (int x = 0; x < gridWidth; x++)",
                "{",
                "    for (int y = 0; y < gridHeight; y++)",
                "    {",
                "        SpawnPiece(x, y);",
                "    }",
                "}"
            ]
        ))
        
        gen.add_method(Method(
            name="SpawnPiece",
            access=AccessModifier.PRIVATE,
            parameters=[("int", "x"), ("int", "y")],
            body=[
                "int randomIndex = Random.Range(0, piecePrefabs.Length);",
                "Vector3 position = new Vector3(x * cellSize, y * cellSize, 0);",
                "GameObject piece = Instantiate(piecePrefabs[randomIndex], position, Quaternion.identity);",
                "grid[x, y] = piece;"
            ]
        ))
        
        gen.add_method(Method(
            name="GetPieceAt",
            access=AccessModifier.PUBLIC,
            return_type="GameObject",
            parameters=[("int", "x"), ("int", "y")],
            body=[
                "if (x >= 0 && x < gridWidth && y >= 0 && y < gridHeight)",
                "    return grid[x, y];",
                "return null;"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _level_manager() -> str:
        """Generate level manager."""
        gen = CSharpCodeGenerator()
        gen.set_class("LevelManager")
        gen.set_summary("Level progression and management")
        
        gen.add_field(Field(
            name="scenes",
            type="string[]",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="currentLevelIndex",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="0"
        ))
        
        gen.add_property(Property(
            name="CurrentLevel",
            type="int",
            getter=True,
            setter=False
        ))
        
        gen.add_method(Method(
            name="LoadLevel",
            access=AccessModifier.PUBLIC,
            parameters=[("int", "levelIndex")],
            body=[
                "if (levelIndex >= 0 && levelIndex < scenes.Length)",
                "{",
                "    currentLevelIndex = levelIndex;",
                "    SceneManager.LoadScene(scenes[levelIndex]);",
                "}"
            ]
        ))
        
        gen.add_method(Method(
            name="LoadNextLevel",
            access=AccessModifier.PUBLIC,
            body=[
                "LoadLevel(currentLevelIndex + 1);"
            ]
        ))
        
        gen.add_method(Method(
            name="RestartLevel",
            access=AccessModifier.PUBLIC,
            body=[
                "LoadLevel(currentLevelIndex);"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _collectible_script() -> str:
        """Generate collectible item script."""
        gen = CSharpCodeGenerator()
        gen.set_class("Collectible")
        gen.set_summary("Collectible item behavior")
        
        gen.add_field(Field(
            name="value",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="10",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="collectEffect",
            type="GameObject",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="collectSound",
            type="AudioClip",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_method(Method(
            name="OnTriggerEnter2D",
            access=AccessModifier.PRIVATE,
            parameters=[("Collider2D", "other")],
            body=[
                'if (other.CompareTag("Player"))',
                "{",
                "    Collect(other.gameObject);",
                "}"
            ]
        ))
        
        gen.add_method(Method(
            name="Collect",
            access=AccessModifier.PRIVATE,
            parameters=[("GameObject", "player")],
            body=[
                "GameManager.Instance?.AddScore(value);",
                "",
                "if (collectEffect != null)",
                "    Instantiate(collectEffect, transform.position, Quaternion.identity);",
                "",
                "if (collectSound != null)",
                "    AudioSource.PlayClipAtPoint(collectSound, transform.position);",
                "",
                "Destroy(gameObject);"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _platform_script() -> str:
        """Generate platform behavior script."""
        gen = CSharpCodeGenerator()
        gen.set_class("Platform")
        gen.set_summary("Moving platform behavior")
        
        gen.add_field(Field(
            name="waypoints",
            type="Transform[]",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="moveSpeed",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="2f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="waitTime",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="0.5f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="currentWaypointIndex",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="0"
        ))
        
        gen.add_method(Method(
            name="Update",
            access=AccessModifier.PRIVATE,
            body=[
                "if (waypoints.Length == 0) return;",
                "",
                "Transform target = waypoints[currentWaypointIndex];",
                "transform.position = Vector3.MoveTowards(transform.position, target.position, moveSpeed * Time.deltaTime);",
                "",
                "if (Vector3.Distance(transform.position, target.position) < 0.01f)",
                "{",
                "    currentWaypointIndex = (currentWaypointIndex + 1) % waypoints.Length;",
                "}"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _enemy_ai_fps() -> str:
        """Generate FPS enemy AI."""
        gen = CSharpCodeGenerator()
        gen.set_class("EnemyAI")
        gen.set_summary("FPS enemy AI behavior")
        
        gen.add_field(Field(
            name="player",
            type="Transform",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="detectionRange",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="20f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="attackRange",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="10f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="moveSpeed",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="3f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="agent",
            type="UnityEngine.AI.NavMeshAgent",
            access=AccessModifier.PRIVATE
        ))
        
        gen.add_method(Method(
            name="Start",
            access=AccessModifier.PRIVATE,
            body=[
                "agent = GetComponent<UnityEngine.AI.NavMeshAgent>();",
                "player = GameObject.FindGameObjectWithTag(\"Player\").transform;"
            ]
        ))
        
        gen.add_method(Method(
            name="Update",
            access=AccessModifier.PRIVATE,
            body=[
                "float distanceToPlayer = Vector3.Distance(transform.position, player.position);",
                "",
                "if (distanceToPlayer <= detectionRange)",
                "{",
                "    if (distanceToPlayer > attackRange)",
                "    {",
                "        ChasePlayer();",
                "    }",
                "    else",
                "    {",
                "        AttackPlayer();",
                "    }",
                "}"
            ]
        ))
        
        gen.add_method(Method(
            name="ChasePlayer",
            access=AccessModifier.PRIVATE,
            body=[
                "agent.SetDestination(player.position);"
            ]
        ))
        
        gen.add_method(Method(
            name="AttackPlayer",
            access=AccessModifier.PRIVATE,
            body=[
                "agent.isStopped = true;",
                "// Implement attack logic here"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _rpg_player_movement() -> str:
        """Generate RPG player movement."""
        gen = CSharpCodeGenerator()
        gen.set_class("PlayerMovement")
        gen.set_summary("RPG-style player movement")
        
        gen.add_field(Field(
            name="moveSpeed",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="5f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="rotationSpeed",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="10f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="rb",
            type="Rigidbody",
            access=AccessModifier.PRIVATE
        ))
        
        gen.add_field(Field(
            name="cameraTransform",
            type="Transform",
            access=AccessModifier.PRIVATE
        ))
        
        gen.add_method(Method(
            name="Start",
            access=AccessModifier.PRIVATE,
            body=[
                "rb = GetComponent<Rigidbody>();",
                "cameraTransform = Camera.main.transform;"
            ]
        ))
        
        gen.add_method(Method(
            name="FixedUpdate",
            access=AccessModifier.PRIVATE,
            body=[
                "HandleMovement();"
            ]
        ))
        
        gen.add_method(Method(
            name="HandleMovement",
            access=AccessModifier.PRIVATE,
            body=[
                "float horizontal = Input.GetAxisRaw(\"Horizontal\");",
                "float vertical = Input.GetAxisRaw(\"Vertical\");",
                "",
                "Vector3 direction = new Vector3(horizontal, 0f, vertical).normalized;",
                "",
                "if (direction.magnitude >= 0.1f)",
                "{",
                "    float targetAngle = Mathf.Atan2(direction.x, direction.z) * Mathf.Rad2Deg + cameraTransform.eulerAngles.y;",
                "    float angle = Mathf.SmoothDampAngle(transform.eulerAngles.y, targetAngle, ref turnSmoothVelocity, 0.1f);",
                "    transform.rotation = Quaternion.Euler(0f, angle, 0f);",
                "",
                "    Vector3 moveDir = Quaternion.Euler(0f, targetAngle, 0f) * Vector3.forward;",
                "    rb.MovePosition(transform.position + moveDir * moveSpeed * Time.fixedDeltaTime);",
                "}"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _quest_system() -> str:
        """Generate quest system."""
        gen = CSharpCodeGenerator()
        gen.set_class("QuestSystem")
        gen.set_summary("Quest management system")
        
        gen.add_field(Field(
            name="activeQuests",
            type="List<Quest>",
            access=AccessModifier.PRIVATE,
            default_value="new List<Quest>()"
        ))
        
        gen.add_field(Field(
            name="completedQuests",
            type="List<Quest>",
            access=AccessModifier.PRIVATE,
            default_value="new List<Quest>()"
        ))
        
        gen.add_method(Method(
            name="AcceptQuest",
            access=AccessModifier.PUBLIC,
            parameters=[("Quest", "quest")],
            body=[
                "if (!activeQuests.Contains(quest))",
                "{",
                "    activeQuests.Add(quest);",
                "    OnQuestAccepted?.Invoke(quest);",
                "}"
            ]
        ))
        
        gen.add_method(Method(
            name="CompleteQuest",
            access=AccessModifier.PUBLIC,
            parameters=[("Quest", "quest")],
            body=[
                "if (activeQuests.Contains(quest))",
                "{",
                "    activeQuests.Remove(quest);",
                "    completedQuests.Add(quest);",
                "    OnQuestCompleted?.Invoke(quest);",
                "}"
            ]
        ))
        
        gen.add_method(Method(
            name="UpdateQuestProgress",
            access=AccessModifier.PUBLIC,
            parameters=[("string", "questId"), ("int", "progress")],
            body=[
                "Quest quest = activeQuests.Find(q => q.Id == questId);",
                "if (quest != null)",
                "{",
                "    quest.CurrentProgress += progress;",
                "    if (quest.IsComplete)",
                "        CompleteQuest(quest);",
                "}"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _dialogue_system() -> str:
        """Generate dialogue system."""
        gen = CSharpCodeGenerator()
        gen.set_class("DialogueSystem")
        gen.set_summary("NPC dialogue system")
        
        gen.add_field(Field(
            name="dialoguePanel",
            type="GameObject",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="dialogueText",
            type="TMPro.TextMeshProUGUI",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="nameText",
            type="TMPro.TextMeshProUGUI",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="typingSpeed",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="0.05f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="isTyping",
            type="bool",
            access=AccessModifier.PRIVATE,
            default_value="false"
        ))
        
        gen.add_method(Method(
            name="StartDialogue",
            access=AccessModifier.PUBLIC,
            parameters=[("Dialogue", "dialogue")],
            body=[
                "dialoguePanel.SetActive(true);",
                "nameText.text = dialogue.speakerName;",
                "StartCoroutine(TypeSentence(dialogue.sentences[0]));"
            ]
        ))
        
        gen.add_method(Method(
            name="EndDialogue",
            access=AccessModifier.PUBLIC,
            body=[
                "dialoguePanel.SetActive(false);",
                "OnDialogueEnd?.Invoke();"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _save_system() -> str:
        """Generate save system."""
        gen = CSharpCodeGenerator()
        gen.set_class("SaveSystem")
        gen.set_summary("Game save/load system")
        
        gen.add_field(Field(
            name="savePath",
            type="string",
            access=AccessModifier.PRIVATE
        ))
        
        gen.add_method(Method(
            name="Awake",
            access=AccessModifier.PRIVATE,
            body=[
                'savePath = Application.persistentDataPath + "/save.json";'
            ]
        ))
        
        gen.add_method(Method(
            name="SaveGame",
            access=AccessModifier.PUBLIC,
            body=[
                "SaveData data = new SaveData();",
                "data.playerPosition = FindObjectOfType<PlayerMovement>().transform.position;",
                "data.score = GameManager.Instance?.score ?? 0;",
                "",
                "string json = JsonUtility.ToJson(data);",
                "System.IO.File.WriteAllText(savePath, json);"
            ]
        ))
        
        gen.add_method(Method(
            name="LoadGame",
            access=AccessModifier.PUBLIC,
            body=[
                "if (System.IO.File.Exists(savePath))",
                "{",
                "    string json = System.IO.File.ReadAllText(savePath);",
                "    SaveData data = JsonUtility.FromJson<SaveData>(json);",
                "    // Apply loaded data",
                "}"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _audio_manager() -> str:
        """Generate audio manager."""
        gen = CSharpCodeGenerator()
        gen.set_class("AudioManager")
        gen.set_summary("Centralized audio management")
        
        gen.add_field(Field(
            name="soundEffects",
            type="Sound[]",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="musicSource",
            type="AudioSource",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="sfxSource",
            type="AudioSource",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_method(Method(
            name="PlaySound",
            access=AccessModifier.PUBLIC,
            parameters=[("string", "name")],
            body=[
                "Sound s = System.Array.Find(soundEffects, sound => sound.name == name);",
                "if (s != null)",
                "{",
                "    sfxSource.PlayOneShot(s.clip);",
                "}"
            ]
        ))
        
        gen.add_method(Method(
            name="PlayMusic",
            access=AccessModifier.PUBLIC,
            parameters=[("AudioClip", "music")],
            body=[
                "musicSource.clip = music;",
                "musicSource.Play();"
            ]
        ))
        
        gen.add_method(Method(
            name="SetMusicVolume",
            access=AccessModifier.PUBLIC,
            parameters=[("float", "volume")],
            body=[
                "musicSource.volume = volume;"
            ]
        ))
        
        gen.add_method(Method(
            name="SetSFXVolume",
            access=AccessModifier.PUBLIC,
            parameters=[("float", "volume")],
            body=[
                "sfxSource.volume = volume;"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _combat_system() -> str:
        """Generate combat system."""
        gen = CSharpCodeGenerator()
        gen.set_class("CombatSystem")
        gen.set_summary("RPG combat system")
        
        gen.add_field(Field(
            name="attackDamage",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="10",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="attackRange",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="2f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="attackCooldown",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="0.5f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="lastAttackTime",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="0f"
        ))
        
        gen.add_field(Field(
            name="attackPoint",
            type="Transform",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="enemyLayers",
            type="LayerMask",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_method(Method(
            name="Attack",
            access=AccessModifier.PUBLIC,
            body=[
                "if (Time.time - lastAttackTime < attackCooldown)",
                "    return;",
                "",
                "lastAttackTime = Time.time;",
                "",
                "Collider[] hitEnemies = Physics.OverlapSphere(attackPoint.position, attackRange, enemyLayers);",
                "",
                "foreach (Collider enemy in hitEnemies)",
                "{",
                "    enemy.GetComponent<HealthSystem>()?.TakeDamage(attackDamage);",
                "}",
                "",
                "OnAttack?.Invoke();"
            ]
        ))
        
        gen.add_method(Method(
            name="OnDrawGizmosSelected",
            access=AccessModifier.PRIVATE,
            body=[
                "if (attackPoint == null) return;",
                "Gizmos.color = Color.red;",
                "Gizmos.DrawWireSphere(attackPoint.position, attackRange);"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _npc_controller() -> str:
        """Generate NPC controller."""
        gen = CSharpCodeGenerator()
        gen.set_class("NPCController")
        gen.set_summary("NPC interaction controller")
        
        gen.add_field(Field(
            name="npcName",
            type="string",
            access=AccessModifier.PRIVATE,
            default_value='"NPC"',
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="dialogue",
            type="Dialogue",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="interactionRange",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="3f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="player",
            type="Transform",
            access=AccessModifier.PRIVATE
        ))
        
        gen.add_method(Method(
            name="Start",
            access=AccessModifier.PRIVATE,
            body=[
                'player = GameObject.FindGameObjectWithTag("Player").transform;'
            ]
        ))
        
        gen.add_method(Method(
            name="Update",
            access=AccessModifier.PRIVATE,
            body=[
                "float distance = Vector3.Distance(transform.position, player.position);",
                "",
                "if (distance <= interactionRange && Input.GetKeyDown(KeyCode.E))",
                "{",
                "    Interact();",
                "}"
            ]
        ))
        
        gen.add_method(Method(
            name="Interact",
            access=AccessModifier.PRIVATE,
            body=[
                "if (dialogue != null)",
                "{",
                "    DialogueSystem.Instance?.StartDialogue(dialogue);",
                "}",
                "OnInteract?.Invoke();"
            ]
        ))
        
        gen.add_method(Method(
            name="OnDrawGizmosSelected",
            access=AccessModifier.PRIVATE,
            body=[
                "Gizmos.color = Color.yellow;",
                "Gizmos.DrawWireSphere(transform.position, interactionRange);"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _health_system_3d() -> str:
        """Generate 3D health system."""
        return UnityTemplates._health_system()
    
    @staticmethod
    def _game_manager_fps() -> str:
        """Generate FPS game manager."""
        return UnityTemplates._game_manager()
    
    @staticmethod
    def _ammo_system() -> str:
        """Generate ammo system."""
        gen = CSharpCodeGenerator()
        gen.set_class("AmmoSystem")
        gen.set_summary("Weapon ammunition system")
        
        gen.add_field(Field(
            name="maxAmmo",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="30",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="currentAmmo",
            type="int",
            access=AccessModifier.PRIVATE
        ))
        
        gen.add_field(Field(
            name="totalAmmo",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="120",
            serialize_field=True
        ))
        
        gen.add_property(Property(
            name="CurrentAmmo",
            type="int",
            getter=True,
            setter=False
        ))
        
        gen.add_method(Method(
            name="Start",
            access=AccessModifier.PRIVATE,
            body=["currentAmmo = maxAmmo;"]
        ))
        
        gen.add_method(Method(
            name="UseAmmo",
            access=AccessModifier.PUBLIC,
            return_type="bool",
            body=[
                "if (currentAmmo > 0)",
                "{",
                "    currentAmmo--;",
                "    OnAmmoChanged?.Invoke(currentAmmo);",
                "    return true;",
                "}",
                "return false;"
            ]
        ))
        
        gen.add_method(Method(
            name="Reload",
            access=AccessModifier.PUBLIC,
            body=[
                "int ammoNeeded = maxAmmo - currentAmmo;",
                "int ammoToReload = Mathf.Min(ammoNeeded, totalAmmo);",
                "",
                "currentAmmo += ammoToReload;",
                "totalAmmo -= ammoToReload;",
                "",
                "OnReload?.Invoke();",
                "OnAmmoChanged?.Invoke(currentAmmo);"
            ]
        ))
        
        gen.add_method(Method(
            name="AddAmmo",
            access=AccessModifier.PUBLIC,
            parameters=[("int", "amount")],
            body=[
                "totalAmmo += amount;",
                "OnAmmoAdded?.Invoke(amount);"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _damageable() -> str:
        """Generate damageable interface implementation."""
        gen = CSharpCodeGenerator()
        gen.set_class("Damageable")
        gen.inherits_from("IDamageable")
        gen.set_summary("Damageable entity implementation")
        
        gen.add_field(Field(
            name="health",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="100",
            serialize_field=True
        ))
        
        gen.add_method(Method(
            name="TakeDamage",
            access=AccessModifier.PUBLIC,
            parameters=[("int", "damage")],
            body=[
                "health -= damage;",
                "OnDamageTaken?.Invoke(damage);",
                "",
                "if (health <= 0)",
                "    Die();"
            ]
        ))
        
        gen.add_method(Method(
            name="Die",
            access=AccessModifier.PRIVATE,
            body=[
                "OnDeath?.Invoke();",
                "Destroy(gameObject);"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _pickup_item() -> str:
        """Generate pickup item script."""
        gen = CSharpCodeGenerator()
        gen.set_class("PickupItem")
        gen.set_summary("Generic pickup item")
        
        gen.add_field(Field(
            name="itemType",
            type="PickupType",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="value",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="10",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="pickupEffect",
            type="ParticleSystem",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="pickupSound",
            type="AudioClip",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_method(Method(
            name="OnTriggerEnter",
            access=AccessModifier.PRIVATE,
            parameters=[("Collider", "other")],
            body=[
                'if (other.CompareTag("Player"))',
                "{",
                "    Pickup(other.gameObject);",
                "}"
            ]
        ))
        
        gen.add_method(Method(
            name="Pickup",
            access=AccessModifier.PRIVATE,
            parameters=[("GameObject", "player")],
            body=[
                "switch (itemType)",
                "{",
                "    case PickupType.Health:",
                "        player.GetComponent<HealthSystem>()?.Heal(value);",
                "        break;",
                "    case PickupType.Ammo:",
                "        player.GetComponent<AmmoSystem>()?.AddAmmo(value);",
                "        break;",
                "    case PickupType.Score:",
                "        GameManager.Instance?.AddScore(value);",
                "        break;",
                "}",
                "",
                "if (pickupEffect != null)",
                "    Instantiate(pickupEffect, transform.position, Quaternion.identity);",
                "",
                "if (pickupSound != null)",
                "    AudioSource.PlayClipAtPoint(pickupSound, transform.position);",
                "",
                "Destroy(gameObject);"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _puzzle_piece() -> str:
        """Generate puzzle piece script."""
        gen = CSharpCodeGenerator()
        gen.set_class("PuzzlePiece")
        gen.set_summary("Individual puzzle piece behavior")
        
        gen.add_field(Field(
            name="pieceType",
            type="PieceType",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="gridPosition",
            type="Vector2Int",
            access=AccessModifier.PRIVATE
        ))
        
        gen.add_field(Field(
            name="isSelected",
            type="bool",
            access=AccessModifier.PRIVATE,
            default_value="false"
        ))
        
        gen.add_method(Method(
            name="OnMouseDown",
            access=AccessModifier.PRIVATE,
            body=[
                "isSelected = true;",
                "OnPieceSelected?.Invoke(this);"
            ]
        ))
        
        gen.add_method(Method(
            name="MoveTo",
            access=AccessModifier.PUBLIC,
            parameters=[("Vector2Int", "newPosition")],
            body=[
                "gridPosition = newPosition;",
                "// Animate to new position",
                "StartCoroutine(MoveAnimation(newPosition));"
            ]
        ))
        
        gen.add_method(Method(
            name="Match",
            access=AccessModifier.PUBLIC,
            body=[
                "OnPieceMatched?.Invoke(this);",
                "Destroy(gameObject);"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _game_board() -> str:
        """Generate game board script."""
        gen = CSharpCodeGenerator()
        gen.set_class("GameBoard")
        gen.set_summary("Puzzle game board manager")
        
        gen.add_field(Field(
            name="gridManager",
            type="GridManager",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="selectedPiece",
            type="PuzzlePiece",
            access=AccessModifier.PRIVATE
        ))
        
        gen.add_method(Method(
            name="Start",
            access=AccessModifier.PRIVATE,
            body=[
                "PuzzlePiece.OnPieceSelected += OnPieceSelected;"
            ]
        ))
        
        gen.add_method(Method(
            name="OnPieceSelected",
            access=AccessModifier.PRIVATE,
            parameters=[("PuzzlePiece", "piece")],
            body=[
                "if (selectedPiece == null)",
                "{",
                "    selectedPiece = piece;",
                "}",
                "else",
                "{",
                "    TrySwapPieces(selectedPiece, piece);",
                "    selectedPiece = null;",
                "}"
            ]
        ))
        
        gen.add_method(Method(
            name="TrySwapPieces",
            access=AccessModifier.PRIVATE,
            parameters=[("PuzzlePiece", "piece1"), ("PuzzlePiece", "piece2")],
            body=[
                "// Check if pieces are adjacent",
                "if (AreAdjacent(piece1, piece2))",
                "{",
                "    SwapPieces(piece1, piece2);",
                "    if (!HasMatches())",
                "    {",
                "        SwapPieces(piece1, piece2); // Swap back if no matches",
                "    }",
                "}"
            ]
        ))
        
        gen.add_method(Method(
            name="AreAdjacent",
            access=AccessModifier.PRIVATE,
            return_type="bool",
            parameters=[("PuzzlePiece", "piece1"), ("PuzzlePiece", "piece2")],
            body=[
                "int dx = Mathf.Abs(piece1.GridPosition.x - piece2.GridPosition.x);",
                "int dy = Mathf.Abs(piece1.GridPosition.y - piece2.GridPosition.y);",
                "return (dx == 1 && dy == 0) || (dx == 0 && dy == 1);"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _level_progression() -> str:
        """Generate level progression script."""
        gen = CSharpCodeGenerator()
        gen.set_class("LevelProgression")
        gen.set_summary("Level progression and unlock system")
        
        gen.add_field(Field(
            name="levels",
            type="LevelData[]",
            access=AccessModifier.PRIVATE,
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="currentLevel",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="0"
        ))
        
        gen.add_method(Method(
            name="UnlockLevel",
            access=AccessModifier.PUBLIC,
            parameters=[("int", "levelIndex")],
            body=[
                "if (levelIndex >= 0 && levelIndex < levels.Length)",
                "{",
                "    levels[levelIndex].isUnlocked = true;",
                "    OnLevelUnlocked?.Invoke(levelIndex);",
                "}"
            ]
        ))
        
        gen.add_method(Method(
            name="CompleteLevel",
            access=AccessModifier.PUBLIC,
            parameters=[("int", "levelIndex")],
            body=[
                "if (levelIndex >= 0 && levelIndex < levels.Length)",
                "{",
                "    levels[levelIndex].isCompleted = true;",
                "    levels[levelIndex].stars = CalculateStars(levelIndex);",
                "    UnlockLevel(levelIndex + 1);",
                "    OnLevelCompleted?.Invoke(levelIndex);",
                "}"
            ]
        ))
        
        gen.add_method(Method(
            name="CalculateStars",
            access=AccessModifier.PRIVATE,
            return_type="int",
            parameters=[("int", "levelIndex")],
            body=[
                "// Calculate stars based on score/time",
                "return 3;"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _score_manager() -> str:
        """Generate score manager."""
        gen = CSharpCodeGenerator()
        gen.set_class("ScoreManager")
        gen.set_summary("Score tracking and management")
        
        gen.add_field(Field(
            name="currentScore",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="0"
        ))
        
        gen.add_field(Field(
            name="highScore",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="0"
        ))
        
        gen.add_field(Field(
            name="scoreMultiplier",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="1f"
        ))
        
        gen.add_property(Property(
            name="CurrentScore",
            type="int",
            getter=True,
            setter=False
        ))
        
        gen.add_property(Property(
            name="HighScore",
            type="int",
            getter=True,
            setter=False
        ))
        
        gen.add_method(Method(
            name="AddScore",
            access=AccessModifier.PUBLIC,
            parameters=[("int", "points")],
            body=[
                "int finalPoints = Mathf.RoundToInt(points * scoreMultiplier);",
                "currentScore += finalPoints;",
                "",
                "if (currentScore > highScore)",
                "{",
                "    highScore = currentScore;",
                "    OnNewHighScore?.Invoke(highScore);",
                "}",
                "",
                "OnScoreChanged?.Invoke(currentScore);"
            ]
        ))
        
        gen.add_method(Method(
            name="SetMultiplier",
            access=AccessModifier.PUBLIC,
            parameters=[("float", "multiplier")],
            body=[
                "scoreMultiplier = multiplier;"
            ]
        ))
        
        gen.add_method(Method(
            name="ResetScore",
            access=AccessModifier.PUBLIC,
            body=[
                "currentScore = 0;",
                "scoreMultiplier = 1f;",
                "OnScoreChanged?.Invoke(currentScore);"
            ]
        ))
        
        return gen.generate()
    
    @staticmethod
    def _hint_system() -> str:
        """Generate hint system."""
        gen = CSharpCodeGenerator()
        gen.set_class("HintSystem")
        gen.set_summary("Puzzle hint system")
        
        gen.add_field(Field(
            name="hintsAvailable",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="3",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="hintCooldown",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="30f",
            serialize_field=True
        ))
        
        gen.add_field(Field(
            name="lastHintTime",
            type="float",
            access=AccessModifier.PRIVATE,
            default_value="-999f"
        ))
        
        gen.add_property(Property(
            name="CanUseHint",
            type="bool",
            getter=True,
            setter=False
        ))
        
        gen.add_method(Method(
            name="UseHint",
            access=AccessModifier.PUBLIC,
            body=[
                "if (!CanUseHint) return;",
                "",
                "hintsAvailable--;",
                "lastHintTime = Time.time;",
                "",
                "// Show hint",
                "ShowHint();",
                "",
                "OnHintUsed?.Invoke(hintsAvailable);"
            ]
        ))
        
        gen.add_method(Method(
            name="ShowHint",
            access=AccessModifier.PRIVATE,
            body=[
                "// Implement hint display logic"
            ]
        ))
        
        gen.add_method(Method(
            name="AddHint",
            access=AccessModifier.PUBLIC,
            body=[
                "hintsAvailable++;",
                "OnHintAdded?.Invoke();"
            ]
        ))
        
        return gen.generate()
