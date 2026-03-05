"""
Game Code Generator
Unified code generation for 2D/3D games across multiple engines.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json


class EngineType(Enum):
    """Supported game engines."""
    UNITY = "unity"
    UNREAL = "unreal"
    GODOT = "godot"


class GameDimension(Enum):
    """Game dimension type."""
    DIM_2D = "2d"
    DIM_3D = "3d"


class GameGenre(Enum):
    """Game genres."""
    PLATFORMER = "platformer"
    FPS = "fps"
    RPG = "rpg"
    PUZZLE = "puzzle"
    STRATEGY = "strategy"
    RACING = "racing"
    FIGHTING = "fighting"
    HORROR = "horror"
    SIMULATION = "simulation"
    SPORTS = "sports"


@dataclass
class CodeTemplate:
    """Code template for game components."""
    name: str
    engine: EngineType
    dimension: GameDimension
    genre: GameGenre
    description: str
    files: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "engine": self.engine.value,
            "dimension": self.dimension.value,
            "genre": self.genre.value,
            "description": self.description,
            "files": self.files,
            "dependencies": self.dependencies,
            "parameters": self.parameters
        }


class GameCodeGenerator:
    """Unified game code generator for multiple engines."""
    
    def __init__(self):
        self.templates: Dict[str, CodeTemplate] = {}
        self._register_default_templates()
    
    def _register_default_templates(self):
        """Register default code templates."""
        # Unity 2D Platformer templates
        self._register_unity_2d_platformer()
        
        # Unity 3D FPS templates
        self._register_unity_3d_fps()
        
        # Unity RPG templates
        self._register_unity_rpg()
        
        # Unreal FPS templates
        self._register_unreal_fps()
        
        # Godot 2D Platformer templates
        self._register_godot_2d_platformer()
        
        # Godot 3D FPS templates
        self._register_godot_3d_fps()
    
    def register_template(self, template: CodeTemplate):
        """Register a code template."""
        key = f"{template.engine.value}_{template.dimension.value}_{template.genre.value}_{template.name}"
        self.templates[key] = template
    
    def get_template(self, engine: EngineType, dimension: GameDimension, 
                     genre: GameGenre, name: str) -> Optional[CodeTemplate]:
        """Get a code template by criteria."""
        key = f"{engine.value}_{dimension.value}_{genre.value}_{name}"
        return self.templates.get(key)
    
    def get_templates_by_engine(self, engine: EngineType) -> List[CodeTemplate]:
        """Get all templates for an engine."""
        return [t for t in self.templates.values() if t.engine == engine]
    
    def get_templates_by_genre(self, genre: GameGenre) -> List[CodeTemplate]:
        """Get all templates for a genre."""
        return [t for t in self.templates.values() if t.genre == genre]
    
    def generate_component(self, engine: EngineType, dimension: GameDimension,
                          genre: GameGenre, component_type: str,
                          parameters: Dict[str, Any] = None) -> Dict[str, str]:
        """Generate a game component."""
        template = self.get_template(engine, dimension, genre, component_type)
        
        if not template:
            raise ValueError(f"Template not found: {engine.value} {dimension.value} {genre.value} {component_type}")
        
        # Apply parameters
        params = template.parameters.copy()
        if parameters:
            params.update(parameters)
        
        # Generate files with parameter substitution
        generated_files = {}
        for filename, content in template.files.items():
            generated_files[filename] = self._apply_parameters(content, params)
        
        return generated_files
    
    def _apply_parameters(self, content: str, parameters: Dict[str, Any]) -> str:
        """Apply parameters to template content."""
        result = content
        for key, value in parameters.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    def _register_unity_2d_platformer(self):
        """Register Unity 2D platformer templates."""
        # Player Controller
        player_controller = CodeTemplate(
            name="player_controller",
            engine=EngineType.UNITY,
            dimension=GameDimension.DIM_2D,
            genre=GameGenre.PLATFORMER,
            description="2D platformer player controller",
            files={
                "PlayerController.cs": '''using UnityEngine;

public class PlayerController : MonoBehaviour
{
    [SerializeField] private float moveSpeed = {{moveSpeed}}f;
    [SerializeField] private float jumpForce = {{jumpForce}}f;
    [SerializeField] private LayerMask groundLayer;
    
    private Rigidbody2D rb;
    private bool isGrounded;
    private float horizontalInput;
    
    private void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
    }
    
    private void Update()
    {
        horizontalInput = Input.GetAxisRaw("Horizontal");
        
        if (Input.GetButtonDown("Jump") && isGrounded)
        {
            Jump();
        }
    }
    
    private void FixedUpdate()
    {
        Move();
        CheckGrounded();
    }
    
    private void Move()
    {
        rb.velocity = new Vector2(horizontalInput * moveSpeed, rb.velocity.y);
    }
    
    private void Jump()
    {
        rb.velocity = new Vector2(rb.velocity.x, jumpForce);
    }
    
    private void CheckGrounded()
    {
        RaycastHit2D hit = Physics2D.Raycast(transform.position, Vector2.down, 0.1f, groundLayer);
        isGrounded = hit.collider != null;
    }
}
'''
            },
            parameters={
                "moveSpeed": 5.0,
                "jumpForce": 10.0
            }
        )
        self.register_template(player_controller)
        
        # Camera Follow
        camera_follow = CodeTemplate(
            name="camera_follow",
            engine=EngineType.UNITY,
            dimension=GameDimension.DIM_2D,
            genre=GameGenre.PLATFORMER,
            description="2D camera that follows the player",
            files={
                "CameraFollow.cs": '''using UnityEngine;

public class CameraFollow : MonoBehaviour
{
    [SerializeField] private Transform target;
    [SerializeField] private float smoothSpeed = {{smoothSpeed}}f;
    [SerializeField] private Vector3 offset = new Vector3(0f, 0f, -10f);
    
    private void LateUpdate()
    {
        if (target == null) return;
        
        Vector3 desiredPosition = target.position + offset;
        Vector3 smoothedPosition = Vector3.Lerp(transform.position, desiredPosition, smoothSpeed);
        transform.position = smoothedPosition;
    }
}
'''
            },
            parameters={
                "smoothSpeed": 0.125
            }
        )
        self.register_template(camera_follow)
    
    def _register_unity_3d_fps(self):
        """Register Unity 3D FPS templates."""
        # FPS Controller
        fps_controller = CodeTemplate(
            name="fps_controller",
            engine=EngineType.UNITY,
            dimension=GameDimension.DIM_3D,
            genre=GameGenre.FPS,
            description="First-person shooter controller",
            files={
                "FPSController.cs": '''using UnityEngine;

[RequireComponent(typeof(CharacterController))]
public class FPSController : MonoBehaviour
{
    [Header("Movement")]
    [SerializeField] private float walkSpeed = {{walkSpeed}}f;
    [SerializeField] private float sprintSpeed = {{sprintSpeed}}f;
    [SerializeField] private float jumpForce = {{jumpForce}}f;
    [SerializeField] private float gravity = -9.81f;
    
    [Header("Look")]
    [SerializeField] private float mouseSensitivity = {{mouseSensitivity}}f;
    [SerializeField] private float lookXLimit = 80f;
    
    private CharacterController controller;
    private Camera playerCamera;
    private Vector3 velocity;
    private float rotationX = 0f;
    private bool canMove = true;
    
    private void Start()
    {
        controller = GetComponent<CharacterController>();
        playerCamera = GetComponentInChildren<Camera>();
        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;
    }
    
    private void Update()
    {
        HandleLook();
        HandleMovement();
        ApplyGravity();
    }
    
    private void HandleLook()
    {
        if (!canMove) return;
        
        rotationX += -Input.GetAxis("Mouse Y") * mouseSensitivity;
        rotationX = Mathf.Clamp(rotationX, -lookXLimit, lookXLimit);
        playerCamera.transform.localRotation = Quaternion.Euler(rotationX, 0, 0);
        
        transform.rotation *= Quaternion.Euler(0, Input.GetAxis("Mouse X") * mouseSensitivity, 0);
    }
    
    private void HandleMovement()
    {
        if (!canMove) return;
        
        float speed = Input.GetKey(KeyCode.LeftShift) ? sprintSpeed : walkSpeed;
        
        Vector3 forward = transform.TransformDirection(Vector3.forward);
        Vector3 right = transform.TransformDirection(Vector3.right);
        
        float curSpeedX = speed * Input.GetAxis("Vertical");
        float curSpeedY = speed * Input.GetAxis("Horizontal");
        
        Vector3 moveDirection = (forward * curSpeedX) + (right * curSpeedY);
        
        if (controller.isGrounded && Input.GetButton("Jump"))
        {
            velocity.y = jumpForce;
        }
        
        controller.Move(moveDirection * Time.deltaTime);
    }
    
    private void ApplyGravity()
    {
        if (controller.isGrounded && velocity.y < 0)
        {
            velocity.y = -2f;
        }
        
        velocity.y += gravity * Time.deltaTime;
        controller.Move(velocity * Time.deltaTime);
    }
}
'''
            },
            parameters={
                "walkSpeed": 5.0,
                "sprintSpeed": 10.0,
                "jumpForce": 8.0,
                "mouseSensitivity": 2.0
            }
        )
        self.register_template(fps_controller)
    
    def _register_unity_rpg(self):
        """Register Unity RPG templates."""
        # Character Stats
        character_stats = CodeTemplate(
            name="character_stats",
            engine=EngineType.UNITY,
            dimension=GameDimension.DIM_3D,
            genre=GameGenre.RPG,
            description="RPG character statistics system",
            files={
                "CharacterStats.cs": '''using UnityEngine;

public class CharacterStats : MonoBehaviour
{
    [Header("Base Stats")]
    [SerializeField] private int level = 1;
    [SerializeField] private int strength = {{baseStrength}};
    [SerializeField] private int agility = {{baseAgility}};
    [SerializeField] private int intelligence = {{baseIntelligence}};
    [SerializeField] private int vitality = {{baseVitality}};
    
    [Header("Derived Stats")]
    public int MaxHealth => vitality * 10;
    public int AttackPower => strength * 2;
    public int Defense => vitality;
    public float AttackSpeed => 1f + (agility * 0.05f);
    public float MoveSpeed => 5f + (agility * 0.1f);
    
    public int CurrentHealth { get; private set; }
    public int CurrentMana { get; private set; }
    
    public int Experience { get; private set; }
    public int ExperienceToNextLevel => level * 100;
    
    private void Start()
    {
        CurrentHealth = MaxHealth;
        CurrentMana = MaxMana;
    }
    
    public int MaxMana => intelligence * 10;
    
    public void TakeDamage(int damage)
    {
        int actualDamage = Mathf.Max(1, damage - Defense);
        CurrentHealth = Mathf.Max(0, CurrentHealth - actualDamage);
        
        if (CurrentHealth <= 0)
        {
            Die();
        }
    }
    
    public void Heal(int amount)
    {
        CurrentHealth = Mathf.Min(MaxHealth, CurrentHealth + amount);
    }
    
    public void AddExperience(int amount)
    {
        Experience += amount;
        
        while (Experience >= ExperienceToNextLevel)
        {
            Experience -= ExperienceToNextLevel;
            LevelUp();
        }
    }
    
    private void LevelUp()
    {
        level++;
        strength += 2;
        agility += 1;
        intelligence += 1;
        vitality += 2;
        
        CurrentHealth = MaxHealth;
        CurrentMana = MaxMana;
        
        Debug.Log($"Level Up! Now level {level}");
    }
    
    private void Die()
    {
        Debug.Log($"{gameObject.name} has died!");
    }
}
'''
            },
            parameters={
                "baseStrength": 10,
                "baseAgility": 10,
                "baseIntelligence": 10,
                "baseVitality": 10
            }
        )
        self.register_template(character_stats)
    
    def _register_unreal_fps(self):
        """Register Unreal FPS templates."""
        # FPS Character Header
        fps_character_h = CodeTemplate(
            name="fps_character_h",
            engine=EngineType.UNREAL,
            dimension=GameDimension.DIM_3D,
            genre=GameGenre.FPS,
            description="FPS character header file",
            files={
                "FPSCharacter.h": '''#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "FPSCharacter.generated.h"

UCLASS()
class {{project_name}}_API AFPSCharacter : public ACharacter
{
    GENERATED_BODY()

public:
    AFPSCharacter();

protected:
    virtual void BeginPlay() override;

public:
    virtual void Tick(float DeltaTime) override;
    virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

    /** Camera component */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = Camera)
    class UCameraComponent* FirstPersonCamera;

    /** Gun mesh component */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = Mesh)
    class USkeletalMeshComponent* GunMesh;

    /** Muzzle location */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = Mesh)
    class USceneComponent* MuzzleLocation;

    /** Movement speed */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = Movement)
    float WalkSpeed;

    /** Sprint speed */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = Movement)
    float SprintSpeed;

protected:
    /** Move forward/backward */
    void MoveForward(float Value);

    /** Move right/left */
    void MoveRight(float Value);

    /** Fire weapon */
    void Fire();

    /** Start sprinting */
    void StartSprint();

    /** Stop sprinting */
    void StopSprint();
};
'''
            },
            parameters={
                "project_name": "MyGame"
            }
        )
        self.register_template(fps_character_h)
    
    def _register_godot_2d_platformer(self):
        """Register Godot 2D platformer templates."""
        # Player Controller
        player_controller = CodeTemplate(
            name="player_controller",
            engine=EngineType.GODOT,
            dimension=GameDimension.DIM_2D,
            genre=GameGenre.PLATFORMER,
            description="2D platformer player controller",
            files={
                "player.gd": '''extends CharacterBody2D

## 2D Platformer Player Controller

@export var speed: float = {{speed}}
@export var jump_velocity: float = {{jump_velocity}}
@export var gravity_scale: float = 1.0

@onready var animated_sprite: AnimatedSprite2D = $AnimatedSprite2D

signal jumped
signal landed

func _physics_process(delta: float) -> void:
    # Apply gravity
    if not is_on_floor():
        velocity.y += ProjectSettings.get_setting("physics/2d/default_gravity") * gravity_scale * delta
    
    # Handle jump
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = jump_velocity
        jumped.emit()
    
    # Get input direction
    var direction := Input.get_axis("move_left", "move_right")
    
    # Handle movement
    if direction:
        velocity.x = direction * speed
        animated_sprite.flip_h = direction < 0
        animated_sprite.play("run")
    else:
        velocity.x = move_toward(velocity.x, 0, speed)
        animated_sprite.play("idle")
    
    if not is_on_floor():
        animated_sprite.play("jump")
    
    move_and_slide()
'''
            },
            parameters={
                "speed": 300.0,
                "jump_velocity": -400.0
            }
        )
        self.register_template(player_controller)
    
    def _register_godot_3d_fps(self):
        """Register Godot 3D FPS templates."""
        # FPS Controller
        fps_controller = CodeTemplate(
            name="fps_controller",
            engine=EngineType.GODOT,
            dimension=GameDimension.DIM_3D,
            genre=GameGenre.FPS,
            description="First-person shooter controller",
            files={
                "fps_player.gd": '''extends CharacterBody3D

## First-Person Shooter Controller

@export var speed: float = {{speed}}
@export var jump_velocity: float = {{jump_velocity}}
@export var mouse_sensitivity: float = {{mouse_sensitivity}}

@onready var camera: Camera3D = $Camera3D

func _ready() -> void:
    Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseMotion:
        rotate_y(-event.relative.x * mouse_sensitivity)
        camera.rotate_x(-event.relative.y * mouse_sensitivity)
        camera.rotation.x = clamp(camera.rotation.x, -PI/2, PI/2)

func _physics_process(delta: float) -> void:
    # Apply gravity
    if not is_on_floor():
        velocity.y -= ProjectSettings.get_setting("physics/3d/default_gravity") * delta
    
    # Handle jump
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = jump_velocity
    
    # Get input direction
    var input_dir := Input.get_vector("move_left", "move_right", "move_up", "move_down")
    var direction := (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
    
    # Handle movement
    if direction:
        velocity.x = direction.x * speed
        velocity.z = direction.z * speed
    else:
        velocity.x = move_toward(velocity.x, 0, speed)
        velocity.z = move_toward(velocity.z, 0, speed)
    
    move_and_slide()
'''
            },
            parameters={
                "speed": 5.0,
                "jump_velocity": 4.5,
                "mouse_sensitivity": 0.003
            }
        )
        self.register_template(fps_controller)
    
    def export_templates(self, filepath: str):
        """Export all templates to a JSON file."""
        data = {
            "templates": [t.to_dict() for t in self.templates.values()]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def import_templates(self, filepath: str):
        """Import templates from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        for template_data in data.get("templates", []):
            template = CodeTemplate(
                name=template_data["name"],
                engine=EngineType(template_data["engine"]),
                dimension=GameDimension(template_data["dimension"]),
                genre=GameGenre(template_data["genre"]),
                description=template_data["description"],
                files=template_data.get("files", {}),
                dependencies=template_data.get("dependencies", []),
                parameters=template_data.get("parameters", {})
            )
            self.register_template(template)
