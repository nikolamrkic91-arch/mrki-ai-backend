"""
Collision Systems
Collision detection and response configurations.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class CollisionShape(Enum):
    """Collision shape types."""
    BOX = "box"
    SPHERE = "sphere"
    CAPSULE = "capsule"
    CYLINDER = "cylinder"
    MESH = "mesh"
    CONVEX_MESH = "convex_mesh"
    TERRAIN = "terrain"


class CollisionLayer(Enum):
    """Common collision layers."""
    DEFAULT = 0
    PLAYER = 1
    ENEMY = 2
    GROUND = 3
    WALL = 4
    TRIGGER = 5
    COLLECTIBLE = 6
    PROJECTILE = 7
    VEHICLE = 8
    WATER = 9
    INTERACTABLE = 10


@dataclass
class CollisionConfig:
    """Collision configuration."""
    shape: CollisionShape
    is_trigger: bool = False
    layer: int = 0
    mask: int = 0xFFFFFFFF
    material: Dict[str, float] = field(default_factory=dict)
    offset: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0, "z": 0})
    size: Dict[str, float] = field(default_factory=lambda: {"x": 1, "y": 1, "z": 1})
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "shape": self.shape.value,
            "is_trigger": self.is_trigger,
            "layer": self.layer,
            "mask": self.mask,
            "material": self.material,
            "offset": self.offset,
            "size": self.size
        }


class CollisionSystem:
    """Collision system utilities and templates."""
    
    # Unity Layer Definitions
    UNITY_LAYERS = {
        "Default": 0,
        "TransparentFX": 1,
        "Ignore Raycast": 2,
        "Water": 4,
        "UI": 5,
        "Player": 6,
        "Enemy": 7,
        "Ground": 8,
        "Wall": 9,
        "Trigger": 10,
        "Collectible": 11,
        "Projectile": 12,
        "Vehicle": 13,
        "Interactable": 14
    }
    
    # Godot Layer Definitions
    GODOT_LAYERS = {
        "player": 1,
        "enemy": 2,
        "ground": 3,
        "wall": 4,
        "collectible": 5,
        "projectile": 6,
        "interactable": 7,
        "trigger": 8
    }
    
    @staticmethod
    def generate_unity_collision_matrix() -> Dict[str, List[str]]:
        """Generate Unity collision matrix configuration."""
        return {
            "Player": ["Default", "Ground", "Wall", "Enemy", "Collectible", "Interactable"],
            "Enemy": ["Default", "Ground", "Wall", "Player", "Projectile"],
            "Projectile": ["Default", "Ground", "Wall", "Enemy"],
            "Collectible": ["Player"],
            "Ground": ["Default", "Player", "Enemy", "Projectile"],
            "Wall": ["Default", "Player", "Enemy", "Projectile"],
            "Interactable": ["Player"],
            "Trigger": []
        }
    
    @staticmethod
    def generate_unity_collision_handler(is_3d: bool = True) -> str:
        """Generate Unity collision handler script."""
        if is_3d:
            return '''using UnityEngine;
using System;

public class CollisionHandler : MonoBehaviour
{
    [Header("Collision Events")]
    public event Action<Collision> OnCollisionEnterEvent;
    public event Action<Collision> OnCollisionStayEvent;
    public event Action<Collision> OnCollisionExitEvent;
    
    [Header("Trigger Events")]
    public event Action<Collider> OnTriggerEnterEvent;
    public event Action<Collider> OnTriggerStayEvent;
    public event Action<Collider> OnTriggerExitEvent;
    
    [Header("Settings")]
    [SerializeField] private LayerMask collisionLayers = ~0;
    [SerializeField] private bool logCollisions = false;
    
    private void OnCollisionEnter(Collision collision)
    {
        if (!IsValidLayer(collision.gameObject.layer)) return;
        
        if (logCollisions)
            Debug.Log($"Collision Enter: {collision.gameObject.name}");
        
        OnCollisionEnterEvent?.Invoke(collision);
    }
    
    private void OnCollisionStay(Collision collision)
    {
        if (!IsValidLayer(collision.gameObject.layer)) return;
        OnCollisionStayEvent?.Invoke(collision);
    }
    
    private void OnCollisionExit(Collision collision)
    {
        if (!IsValidLayer(collision.gameObject.layer)) return;
        OnCollisionExitEvent?.Invoke(collision);
    }
    
    private void OnTriggerEnter(Collider other)
    {
        if (!IsValidLayer(other.gameObject.layer)) return;
        
        if (logCollisions)
            Debug.Log($"Trigger Enter: {other.gameObject.name}");
        
        OnTriggerEnterEvent?.Invoke(other);
    }
    
    private void OnTriggerStay(Collider other)
    {
        if (!IsValidLayer(other.gameObject.layer)) return;
        OnTriggerStayEvent?.Invoke(other);
    }
    
    private void OnTriggerExit(Collider other)
    {
        if (!IsValidLayer(other.gameObject.layer)) return;
        OnTriggerExitEvent?.Invoke(other);
    }
    
    private bool IsValidLayer(int layer)
    {
        return (collisionLayers.value & (1 << layer)) != 0;
    }
}
'''
        else:
            return '''using UnityEngine;
using System;

public class CollisionHandler2D : MonoBehaviour
{
    [Header("Collision Events")]
    public event Action<Collision2D> OnCollisionEnterEvent;
    public event Action<Collision2D> OnCollisionStayEvent;
    public event Action<Collision2D> OnCollisionExitEvent;
    
    [Header("Trigger Events")]
    public event Action<Collider2D> OnTriggerEnterEvent;
    public event Action<Collider2D> OnTriggerStayEvent;
    public event Action<Collider2D> OnTriggerExitEvent;
    
    [Header("Settings")]
    [SerializeField] private LayerMask collisionLayers = ~0;
    [SerializeField] private bool logCollisions = false;
    
    private void OnCollisionEnter2D(Collision2D collision)
    {
        if (!IsValidLayer(collision.gameObject.layer)) return;
        
        if (logCollisions)
            Debug.Log($"Collision Enter: {collision.gameObject.name}");
        
        OnCollisionEnterEvent?.Invoke(collision);
    }
    
    private void OnCollisionStay2D(Collision2D collision)
    {
        if (!IsValidLayer(collision.gameObject.layer)) return;
        OnCollisionStayEvent?.Invoke(collision);
    }
    
    private void OnCollisionExit2D(Collision2D collision)
    {
        if (!IsValidLayer(collision.gameObject.layer)) return;
        OnCollisionExitEvent?.Invoke(collision);
    }
    
    private void OnTriggerEnter2D(Collider2D other)
    {
        if (!IsValidLayer(other.gameObject.layer)) return;
        
        if (logCollisions)
            Debug.Log($"Trigger Enter: {other.gameObject.name}");
        
        OnTriggerEnterEvent?.Invoke(other);
    }
    
    private void OnTriggerStay2D(Collider2D other)
    {
        if (!IsValidLayer(other.gameObject.layer)) return;
        OnTriggerStayEvent?.Invoke(other);
    }
    
    private void OnTriggerExit2D(Collider2D other)
    {
        if (!IsValidLayer(other.gameObject.layer)) return;
        OnTriggerExitEvent?.Invoke(other);
    }
    
    private bool IsValidLayer(int layer)
    {
        return (collisionLayers.value & (1 << layer)) != 0;
    }
}
'''
    
    @staticmethod
    def generate_godot_collision_handler(is_3d: bool = True) -> str:
        """Generate Godot collision handler script."""
        if is_3d:
            return '''extends CharacterBody3D

## Collision Handler for 3D

signal collision_entered(body: Node)
signal collision_exited(body: Node)
signal trigger_entered(body: Node)
signal trigger_exited(body: Node)

@export var collision_layers: int = 1
@export var collision_mask: int = 1
@export var log_collisions: bool = false

func _ready():
    # Set collision layers and mask
    collision_layer = collision_layers
    collision_mask = collision_mask

func _on_body_entered(body: Node) -> void:
    if log_collisions:
        print("Body entered: ", body.name)
    collision_entered.emit(body)

func _on_body_exited(body: Node) -> void:
    collision_exited.emit(body)

func _on_area_entered(area: Area3D) -> void:
    if log_collisions:
        print("Area entered: ", area.name)
    trigger_entered.emit(area)

func _on_area_exited(area: Area3D) -> void:
    trigger_exited.emit(area)
'''
        else:
            return '''extends CharacterBody2D

## Collision Handler for 2D

signal collision_entered(body: Node2D)
signal collision_exited(body: Node2D)
signal trigger_entered(body: Node2D)
signal trigger_exited(body: Node2D)

@export var collision_layers: int = 1
@export var collision_mask: int = 1
@export var log_collisions: bool = false

func _ready():
    # Set collision layers and mask
    collision_layer = collision_layers
    collision_mask = collision_mask

func _on_body_entered(body: Node2D) -> void:
    if log_collisions:
        print("Body entered: ", body.name)
    collision_entered.emit(body)

func _on_body_exited(body: Node2D) -> void:
    collision_exited.emit(body)

func _on_area_entered(area: Area2D) -> void:
    if log_collisions:
        print("Area entered: ", area.name)
    trigger_entered.emit(area)

func _on_area_exited(area: Area2D) -> void:
    trigger_exited.emit(area)
'''
    
    @staticmethod
    def generate_unreal_collision_handler() -> str:
        """Generate Unreal collision handler."""
        return '''#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CollisionHandlerComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnCollisionDelegate, UPrimitiveComponent*, OverlappedComponent);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnHitDelegate, UPrimitiveComponent*, HitComponent, const FHitResult&, Hit);

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class MYGAME_API UCollisionHandlerComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UCollisionHandlerComponent();

    UPROPERTY(BlueprintAssignable, Category = "Collision")
    FOnCollisionDelegate OnCollisionEnter;

    UPROPERTY(BlueprintAssignable, Category = "Collision")
    FOnCollisionDelegate OnCollisionExit;

    UPROPERTY(BlueprintAssignable, Category = "Collision")
    FOnHitDelegate OnHit;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Collision")
    TArray<TEnumAsByte<ECollisionChannel>> CollisionChannels;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Collision")
    bool bLogCollisions;

protected:
    virtual void BeginPlay() override;

    UFUNCTION()
    void OnOverlapBegin(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, 
                        UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, 
                        bool bFromSweep, const FHitResult& SweepResult);

    UFUNCTION()
    void OnOverlapEnd(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
                      UPrimitiveComponent* OtherComp, int32 OtherBodyIndex);

    UFUNCTION()
    void OnHitEvent(UPrimitiveComponent* HitComponent, AActor* OtherActor,
                    UPrimitiveComponent* OtherComp, FVector NormalImpulse, 
                    const FHitResult& Hit);
};
'''
    
    @staticmethod
    def generate_raycast_unity(is_3d: bool = True) -> str:
        """Generate Unity raycast utility."""
        if is_3d:
            return '''using UnityEngine;

public static class RaycastHelper
{
    public static RaycastHit? RaycastFromCamera(Camera camera, float maxDistance = 100f, LayerMask layerMask = default)
    {
        Ray ray = new Ray(camera.transform.position, camera.transform.forward);
        
        if (Physics.Raycast(ray, out RaycastHit hit, maxDistance, layerMask))
        {
            return hit;
        }
        
        return null;
    }
    
    public static RaycastHit? RaycastFromScreenPoint(Vector2 screenPoint, Camera camera, float maxDistance = 100f, LayerMask layerMask = default)
    {
        Ray ray = camera.ScreenPointToRay(screenPoint);
        
        if (Physics.Raycast(ray, out RaycastHit hit, maxDistance, layerMask))
        {
            return hit;
        }
        
        return null;
    }
    
    public static RaycastHit[] RaycastAll(Vector3 origin, Vector3 direction, float maxDistance = 100f, LayerMask layerMask = default)
    {
        return Physics.RaycastAll(origin, direction, maxDistance, layerMask);
    }
    
    public static void DrawDebugRay(Vector3 origin, Vector3 direction, float distance, Color color, float duration = 0f)
    {
        Debug.DrawRay(origin, direction * distance, color, duration);
    }
}
'''
        else:
            return '''using UnityEngine;

public static class RaycastHelper2D
{
    public static RaycastHit2D? Raycast(Vector2 origin, Vector2 direction, float distance = 100f, LayerMask layerMask = default)
    {
        RaycastHit2D hit = Physics2D.Raycast(origin, direction, distance, layerMask);
        
        if (hit.collider != null)
        {
            return hit;
        }
        
        return null;
    }
    
    public static RaycastHit2D[] RaycastAll(Vector2 origin, Vector2 direction, float distance = 100f, LayerMask layerMask = default)
    {
        return Physics2D.RaycastAll(origin, direction, distance, layerMask);
    }
    
    public static void DrawDebugRay(Vector2 origin, Vector2 direction, float distance, Color color, float duration = 0f)
    {
        Debug.DrawRay(origin, direction * distance, color, duration);
    }
}
'''
    
    @staticmethod
    def generate_raycast_godot(is_3d: bool = True) -> str:
        """Generate Godot raycast utility."""
        if is_3d:
            return '''extends Node3D

## Raycast Helper for 3D

@export var max_distance: float = 100.0
@export var collision_mask: int = 1

func raycast_from_camera(camera: Camera3D) -> Dictionary:
    var from = camera.global_position
    var to = from + camera.global_transform.basis.z * max_distance
    
    var space_state = get_world_3d().direct_space_state
    var query = PhysicsRayQueryParameters3D.new()
    query.from = from
    query.to = to
    query.collision_mask = collision_mask
    
    return space_state.intersect_ray(query)

func raycast_from_screen_point(screen_point: Vector2, camera: Camera3D) -> Dictionary:
    var from = camera.project_ray_origin(screen_point)
    var to = from + camera.project_ray_normal(screen_point) * max_distance
    
    var space_state = get_world_3d().direct_space_state
    var query = PhysicsRayQueryParameters3D.new()
    query.from = from
    query.to = to
    query.collision_mask = collision_mask
    
    return space_state.intersect_ray(query)

func raycast_all(origin: Vector3, direction: Vector3) -> Array:
    var to = origin + direction * max_distance
    
    var space_state = get_world_3d().direct_space_state
    var query = PhysicsRayQueryParameters3D.new()
    query.from = origin
    query.to = to
    query.collision_mask = collision_mask
    
    return space_state.intersect_shape(query)
'''
        else:
            return '''extends Node2D

## Raycast Helper for 2D

@export var max_distance: float = 100.0
@export var collision_mask: int = 1

func raycast(origin: Vector2, direction: Vector2) -> Dictionary:
    var space_state = get_world_2d().direct_space_state
    var query = PhysicsRayQueryParameters2D.new()
    query.from = origin
    query.to = origin + direction * max_distance
    query.collision_mask = collision_mask
    
    return space_state.intersect_ray(query)

func raycast_all(origin: Vector2, direction: Vector2) -> Array:
    var space_state = get_world_2d().direct_space_state
    var query = PhysicsRayQueryParameters2D.new()
    query.from = origin
    query.to = origin + direction * max_distance
    query.collision_mask = collision_mask
    
    return space_state.intersect_shape(query)
'''
