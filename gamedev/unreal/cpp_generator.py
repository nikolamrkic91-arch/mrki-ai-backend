"""
C++ Code Generator for Unreal Engine
Generates C++ code for Unreal Engine game development.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class UClassType(Enum):
    """Unreal class types."""
    ACTOR = "AActor"
    PAWN = "APawn"
    CHARACTER = "ACharacter"
    PLAYER_CONTROLLER = "APlayerController"
    GAME_MODE = "AGameModeBase"
    GAME_STATE = "AGameStateBase"
    PLAYER_STATE = "APlayerState"
    HUD = "AHUD"
    ACTOR_COMPONENT = "UActorComponent"
    SCENE_COMPONENT = "USceneComponent"
    OBJECT = "UObject"


class UPropertySpec(Enum):
    """Unreal property specifiers."""
    EDIT_ANYWHERE = "EditAnywhere"
    EDIT_DEFAULTS_ONLY = "EditDefaultsOnly"
    EDIT_INSTANCE_ONLY = "EditInstanceOnly"
    BLUEPRINT_READ_WRITE = "BlueprintReadWrite"
    BLUEPRINT_READ_ONLY = "BlueprintReadOnly"
    VISIBLE_ANYWHERE = "VisibleAnywhere"
    VISIBLE_DEFAULTS_ONLY = "VisibleDefaultsOnly"
    VISIBLE_INSTANCE_ONLY = "VisibleInstanceOnly"
    REPLICATED = "Replicated"
    REPLICATED_USING = "ReplicatedUsing"
    SAVE_GAME = "SaveGame"
    CATEGORY = "Category"
    META = "meta"


@dataclass
class UProperty:
    """Represents a UPROPERTY."""
    name: str
    type: str
    specifiers: List[str] = field(default_factory=list)
    category: Optional[str] = None
    default_value: Optional[str] = None
    tooltip: Optional[str] = None
    
    def generate_header(self) -> str:
        lines = []
        
        # Build specifier string
        spec_list = self.specifiers.copy()
        if self.category:
            spec_list.append(f'Category="{self.category}"')
        if self.tooltip:
            spec_list.append(f'meta=(Tooltip="{self.tooltip}")')
        
        specifier_str = ", ".join(spec_list) if spec_list else ""
        
        lines.append(f"    UPROPERTY({specifier_str})")
        
        if self.default_value:
            lines.append(f"    {self.type} {self.name} = {self.default_value};")
        else:
            lines.append(f"    {self.type} {self.name};")
        
        return "\n".join(lines)


@dataclass
class UFunction:
    """Represents a UFUNCTION."""
    name: str
    return_type: str = "void"
    parameters: List[tuple] = field(default_factory=list)
    specifiers: List[str] = field(default_factory=list)
    body: List[str] = field(default_factory=list)
    is_virtual: bool = False
    is_override: bool = False
    is_ufunction: bool = True
    documentation: Optional[str] = None
    
    def generate_header(self) -> str:
        lines = []
        
        if self.documentation:
            lines.append(f"    /** {self.documentation} */")
        
        if self.is_ufunction and self.specifiers:
            lines.append(f"    UFUNCTION({', '.join(self.specifiers)})")
        
        # Function signature
        modifiers = []
        if self.is_virtual:
            modifiers.append("virtual")
        if self.is_override:
            modifiers.append("override")
        
        modifier_str = " ".join(modifiers)
        
        params = ", ".join([f"{p[0]} {p[1]}" for p in self.parameters]) if self.parameters else ""
        
        if modifier_str:
            lines.append(f"    {modifier_str} {self.return_type} {self.name}({params});")
        else:
            lines.append(f"    {self.return_type} {self.name}({params});")
        
        return "\n".join(lines)
    
    def generate_cpp(self, class_name: str) -> str:
        """Generate C++ implementation."""
        lines = []
        
        params = ", ".join([f"{p[0]} {p[1]}" for p in self.parameters]) if self.parameters else ""
        lines.append(f"{self.return_type} A{class_name}::{self.name}({params})")
        lines.append("{")
        
        if self.body:
            for line in self.body:
                lines.append(f"    {line}")
        elif self.return_type != "void":
            lines.append(f"    return {self.return_type}();")
        
        lines.append("}")
        
        return "\n".join(lines)


class CppCodeGenerator:
    """Generator for Unreal Engine C++ code."""
    
    def __init__(self):
        self.class_name: str = ""
        self.parent_class: str = "AActor"
        self.includes: List[str] = []
        self.properties: List[UProperty] = []
        self.functions: List[UFunction] = []
        self.generated_body: str = "GENERATED_BODY()"
        self.api_macro: str = ""
        self.documentation: Optional[str] = None
        
    def set_class(self, name: str, parent: UClassType = UClassType.ACTOR):
        """Set the class name and parent."""
        self.class_name = name
        self.parent_class = parent.value
        return self
    
    def set_api_macro(self, macro: str):
        """Set the API macro for module export."""
        self.api_macro = macro
        return self
    
    def add_include(self, header: str):
        """Add an include statement."""
        if header not in self.includes:
            self.includes.append(header)
        return self
    
    def add_property(self, prop: UProperty):
        """Add a property to the class."""
        self.properties.append(prop)
        return self
    
    def add_function(self, func: UFunction):
        """Add a function to the class."""
        self.functions.append(func)
        return self
    
    def set_documentation(self, doc: str):
        """Set class documentation."""
        self.documentation = doc
        return self
    
    def generate_header(self) -> str:
        """Generate the header (.h) file."""
        lines = []
        
        # Header guard
        guard = f"{self.class_name.upper()}_H"
        lines.append(f"#pragma once")
        lines.append("")
        
        # Includes
        default_includes = [
            "CoreMinimal.h",
            f"GameFramework/{self.parent_class.replace('A', '').replace('U', '')}.h"
        ]
        
        for inc in default_includes:
            lines.append(f'#include "{inc}"')
        
        for inc in self.includes:
            if inc not in default_includes:
                lines.append(f'#include "{inc}"')
        
        lines.append(f'#include "{self.class_name}.generated.h"')
        lines.append("")
        
        # Class documentation
        if self.documentation:
            lines.append(f"/** {self.documentation} */")
        
        # Class declaration
        api = f" {self.api_macro}" if self.api_macro else ""
        lines.append(f"UCLASS()")
        lines.append(f"class{api} A{self.class_name} : public {self.parent_class}")
        lines.append("{")
        lines.append(f"    {self.generated_body}")
        lines.append("")
        
        # Properties
        if self.properties:
            lines.append("public:")
            for prop in self.properties:
                lines.append(prop.generate_header())
                lines.append("")
        
        # Functions
        if self.functions:
            lines.append("protected:")
            for func in self.functions:
                lines.append(func.generate_header())
                lines.append("")
        
        lines.append("};")
        
        return "\n".join(lines)
    
    def generate_cpp(self) -> str:
        """Generate the implementation (.cpp) file."""
        lines = []
        
        # Include header
        lines.append(f'#include "{self.class_name}.h"')
        lines.append("")
        
        # Generate function implementations
        for func in self.functions:
            lines.append(func.generate_cpp(self.class_name))
            lines.append("")
        
        return "\n".join(lines)
    
    # Preset generators for common Unreal patterns
    
    def generate_character(self, class_name: str) -> Dict[str, str]:
        """Generate a character class."""
        self.set_class(class_name, UClassType.CHARACTER)
        self.set_documentation(f"Player character for {class_name}")
        
        self.add_include("GameFramework/CharacterMovementComponent.h")
        self.add_include("GameFramework/SpringArmComponent.h")
        self.add_include("Camera/CameraComponent.h")
        
        # Camera boom
        self.add_property(UProperty(
            name="CameraBoom",
            type="USpringArmComponent*",
            specifiers=["VisibleAnywhere", "BlueprintReadOnly"],
            category="Camera"
        ))
        
        # Follow camera
        self.add_property(UProperty(
            name="FollowCamera",
            type="UCameraComponent*",
            specifiers=["VisibleAnywhere", "BlueprintReadOnly"],
            category="Camera"
        ))
        
        # Movement speed
        self.add_property(UProperty(
            name="BaseTurnRate",
            type="float",
            specifiers=["EditAnywhere", "BlueprintReadOnly"],
            category="Input",
            default_value="45.f"
        ))
        
        self.add_property(UProperty(
            name="BaseLookUpRate",
            type="float",
            specifiers=["EditAnywhere", "BlueprintReadOnly"],
            category="Input",
            default_value="45.f"
        ))
        
        # Constructor
        self.add_function(UFunction(
            name=class_name,
            specifiers=[],
            is_ufunction=False,
            is_virtual=False,
            body=[
                "// Set size for collision capsule",
                "GetCapsuleComponent()->InitCapsuleSize(42.f, 96.0f);",
                "",
                "// Don't rotate when the controller rotates.",
                "bUseControllerRotationPitch = false;",
                "bUseControllerRotationYaw = false;",
                "bUseControllerRotationRoll = false;",
                "",
                "// Configure character movement",
                "GetCharacterMovement()->bOrientRotationToMovement = true;",
                "GetCharacterMovement()->RotationRate = FRotator(0.0f, 500.0f, 0.0f);",
                "",
                "// Create CameraBoom",
                "CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT(\"CameraBoom\"));",
                "CameraBoom->SetupAttachment(RootComponent);",
                "CameraBoom->TargetArmLength = 300.0f;",
                "CameraBoom->bUsePawnControlRotation = true;",
                "",
                "// Create FollowCamera",
                "FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT(\"FollowCamera\"));",
                "FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);",
                "FollowCamera->bUsePawnControlRotation = false;"
            ]
        ))
        
        # SetupPlayerInputComponent
        self.add_function(UFunction(
            name="SetupPlayerInputComponent",
            parameters=[("UInputComponent*", "PlayerInputComponent")],
            specifiers=["virtual", "override"],
            body=[
                "Super::SetupPlayerInputComponent(PlayerInputComponent);",
                "",
                "// Bind movement events",
                "PlayerInputComponent->BindAxis(\"MoveForward\", this, &A{0}::MoveForward);".format(class_name),
                "PlayerInputComponent->BindAxis(\"MoveRight\", this, &A{0}::MoveRight);".format(class_name), 
                "",
                "// Bind look events",
                "PlayerInputComponent->BindAxis(\"Turn\", this, &APawn::AddControllerYawInput);",
                "PlayerInputComponent->BindAxis(\"LookUp\", this, &APawn::AddControllerPitchInput);"
            ]
        ))
        
        # MoveForward
        self.add_function(UFunction(
            name="MoveForward",
            parameters=[("float", "Value")],
            body=[
                "if ((Controller != nullptr) && (Value != 0.0f))",
                "{",
                "    const FRotator Rotation = Controller->GetControlRotation();",
                "    const FRotator YawRotation(0, Rotation.Yaw, 0);",
                "    const FVector Direction = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X);",
                "    AddMovementInput(Direction, Value);",
                "}"
            ]
        ))
        
        # MoveRight
        self.add_function(UFunction(
            name="MoveRight",
            parameters=[("float", "Value")],
            body=[
                "if ((Controller != nullptr) && (Value != 0.0f))",
                "{",
                "    const FRotator Rotation = Controller->GetControlRotation();",
                "    const FRotator YawRotation(0, Rotation.Yaw, 0);",
                "    const FVector Direction = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::Y);",
                "    AddMovementInput(Direction, Value);",
                "}"
            ]
        ))
        
        return {
            "header": self.generate_header(),
            "cpp": self.generate_cpp()
        }
    
    def generate_player_controller(self, class_name: str) -> Dict[str, str]:
        """Generate a player controller class."""
        self.set_class(class_name, UClassType.PLAYER_CONTROLLER)
        self.set_documentation(f"Player controller for {class_name}")
        
        self.add_include("EnhancedInputComponent.h")
        self.add_include("EnhancedInputSubsystems.h")
        
        # Input mapping context
        self.add_property(UProperty(
            name="DefaultMappingContext",
            type="UInputMappingContext*",
            specifiers=["EditAnywhere", "BlueprintReadOnly"],
            category="Input"
        ))
        
        # Jump action
        self.add_property(UProperty(
            name="JumpAction",
            type="UInputAction*",
            specifiers=["EditAnywhere", "BlueprintReadOnly"],
            category="Input"
        ))
        
        # Move action
        self.add_property(UProperty(
            name="MoveAction",
            type="UInputAction*",
            specifiers=["EditAnywhere", "BlueprintReadOnly"],
            category="Input"
        ))
        
        # Look action
        self.add_property(UProperty(
            name="LookAction",
            type="UInputAction*",
            specifiers=["EditAnywhere", "BlueprintReadOnly"],
            category="Input"
        ))
        
        # BeginPlay
        self.add_function(UFunction(
            name="BeginPlay",
            is_virtual=True,
            is_override=True,
            specifiers=["virtual", "override"],
            body=[
                "Super::BeginPlay();",
                "",
                "// Add Input Mapping Context",
                "if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(GetLocalPlayer()))",
                "{",
                "    Subsystem->AddMappingContext(DefaultMappingContext, 0);",
                "}"
            ]
        ))
        
        return {
            "header": self.generate_header(),
            "cpp": self.generate_cpp()
        }
    
    def generate_game_mode(self, class_name: str) -> Dict[str, str]:
        """Generate a game mode class."""
        self.set_class(class_name, UClassType.GAME_MODE)
        self.set_documentation(f"Game mode for {class_name}")
        
        # Constructor
        self.add_function(UFunction(
            name=class_name,
            specifiers=[],
            is_ufunction=False,
            body=[
                "// Set default pawn class",
                "// DefaultPawnClass = A{0}Character::StaticClass();".format(class_name.replace("GameMode", "")),
                "",
                "// Set default player controller",
                "// PlayerControllerClass = A{0}PlayerController::StaticClass();".format(class_name.replace("GameMode", ""))
            ]
        ))
        
        # InitGame
        self.add_function(UFunction(
            name="InitGame",
            parameters=[("const FString&", "MapName"), ("const FString&", "Options"), ("FString&", "ErrorMessage")],
            is_virtual=True,
            is_override=True,
            specifiers=["virtual", "override"],
            body=[
                "Super::InitGame(MapName, Options, ErrorMessage);"
            ]
        ))
        
        return {
            "header": self.generate_header(),
            "cpp": self.generate_cpp()
        }
    
    def generate_actor_component(self, class_name: str) -> Dict[str, str]:
        """Generate an actor component class."""
        self.set_class(class_name, UClassType.ACTOR_COMPONENT)
        self.set_documentation(f"Actor component for {class_name}")
        
        # Constructor
        self.add_function(UFunction(
            name=class_name,
            specifiers=[],
            is_ufunction=False,
            body=[
                "// Set this component to be initialized when the game starts",
                "PrimaryComponentTick.bCanEverTick = true;"
            ]
        ))
        
        # BeginPlay
        self.add_function(UFunction(
            name="BeginPlay",
            is_virtual=True,
            is_override=True,
            specifiers=["virtual", "override"],
            body=[
                "Super::BeginPlay();"
            ]
        ))
        
        # TickComponent
        self.add_function(UFunction(
            name="TickComponent",
            parameters=[("float", "DeltaTime"), ("ELevelTick", "TickType"), ("FActorComponentTickFunction*", "ThisTickFunction")],
            is_virtual=True,
            is_override=True,
            specifiers=["virtual", "override"],
            body=[
                "Super::TickComponent(DeltaTime, TickType, ThisTickFunction);"
            ]
        ))
        
        return {
            "header": self.generate_header(),
            "cpp": self.generate_cpp()
        }
    
    def generate_health_component(self, class_name: str = "Health") -> Dict[str, str]:
        """Generate a health component."""
        self.set_class(f"{class_name}Component", UClassType.ACTOR_COMPONENT)
        self.set_documentation(f"Health component for managing health")
        
        # Max health
        self.add_property(UProperty(
            name="MaxHealth",
            type="float",
            specifiers=["EditDefaultsOnly", "BlueprintReadOnly"],
            category="Health",
            default_value="100.f"
        ))
        
        # Current health
        self.add_property(UProperty(
            name="CurrentHealth",
            type="float",
            specifiers=["VisibleAnywhere", "BlueprintReadOnly", "ReplicatedUsing=OnRep_CurrentHealth"],
            category="Health"
        ))
        
        # Constructor
        self.add_function(UFunction(
            name=f"{class_name}Component",
            specifiers=[],
            is_ufunction=False,
            body=[
                "PrimaryComponentTick.bCanEverTick = false;",
                "SetIsReplicatedByDefault(true);"
            ]
        ))
        
        # BeginPlay
        self.add_function(UFunction(
            name="BeginPlay",
            is_virtual=True,
            is_override=True,
            specifiers=["virtual", "override"],
            body=[
                "Super::BeginPlay();",
                "CurrentHealth = MaxHealth;"
            ]
        ))
        
        # TakeDamage
        self.add_function(UFunction(
            name="TakeDamage",
            parameters=[("float", "DamageAmount")],
            specifiers=["BlueprintCallable"],
            body=[
                "if (DamageAmount <= 0.f)",
                "    return;",
                "",
                "CurrentHealth = FMath::Clamp(CurrentHealth - DamageAmount, 0.f, MaxHealth);",
                "OnHealthChanged.Broadcast(CurrentHealth, MaxHealth);",
                "",
                "if (CurrentHealth <= 0.f)",
                "{",
                "    OnDeath.Broadcast();",
                "}"
            ]
        ))
        
        # Heal
        self.add_function(UFunction(
            name="Heal",
            parameters=[("float", "HealAmount")],
            specifiers=["BlueprintCallable"],
            body=[
                "if (HealAmount <= 0.f)",
                "    return;",
                "",
                "CurrentHealth = FMath::Clamp(CurrentHealth + HealAmount, 0.f, MaxHealth);",
                "OnHealthChanged.Broadcast(CurrentHealth, MaxHealth);"
            ]
        ))
        
        # OnRep_CurrentHealth
        self.add_function(UFunction(
            name="OnRep_CurrentHealth",
            specifiers=[],
            body=[
                "OnHealthChanged.Broadcast(CurrentHealth, MaxHealth);"
            ]
        ))
        
        return {
            "header": self.generate_header(),
            "cpp": self.generate_cpp()
        }
    
    def generate_weapon_component(self, class_name: str = "Weapon") -> Dict[str, str]:
        """Generate a weapon component."""
        self.set_class(f"{class_name}Component", UClassType.ACTOR_COMPONENT)
        self.set_documentation(f"Weapon component for handling weapon functionality")
        
        # Damage
        self.add_property(UProperty(
            name="Damage",
            type="float",
            specifiers=["EditDefaultsOnly", "BlueprintReadOnly"],
            category="Weapon",
            default_value="25.f"
        ))
        
        # Fire rate
        self.add_property(UProperty(
            name="FireRate",
            type="float",
            specifiers=["EditDefaultsOnly", "BlueprintReadOnly"],
            category="Weapon",
            default_value="0.1f"
        ))
        
        # Range
        self.add_property(UProperty(
            name="Range",
            type="float",
            specifiers=["EditDefaultsOnly", "BlueprintReadOnly"],
            category="Weapon",
            default_value="10000.f"
        ))
        
        # Muzzle location
        self.add_property(UProperty(
            name="MuzzleLocation",
            type="FVector",
            specifiers=["EditDefaultsOnly", "BlueprintReadOnly"],
            category="Weapon"
        ))
        
        # Constructor
        self.add_function(UFunction(
            name=f"{class_name}Component",
            specifiers=[],
            is_ufunction=False,
            body=[
                "PrimaryComponentTick.bCanEverTick = false;"
            ]
        ))
        
        # Fire
        self.add_function(UFunction(
            name="Fire",
            specifiers=["BlueprintCallable"],
            body=[
                "AActor* Owner = GetOwner();",
                "if (!Owner)",
                "    return;",
                "",
                "FVector Start = Owner->GetActorLocation() + MuzzleLocation;",
                "FVector End = Start + Owner->GetActorForwardVector() * Range;",
                "",
                "FHitResult HitResult;",
                "FCollisionQueryParams QueryParams;",
                "QueryParams.AddIgnoredActor(Owner);",
                "",
                "if (GetWorld()->LineTraceSingleByChannel(HitResult, Start, End, ECC_Visibility, QueryParams))",
                "{",
                "    if (AActor* HitActor = HitResult.GetActor())",
                "    {",
                "        UGameplayStatics::ApplyDamage(HitActor, Damage, Owner->GetInstigatorController(), Owner, UDamageType::StaticClass());",
                "    }",
                "}",
                "",
                "OnFire.Broadcast();"
            ]
        ))
        
        return {
            "header": self.generate_header(),
            "cpp": self.generate_cpp()
        }
    
    def generate_interactable_interface(self, class_name: str = "Interactable") -> Dict[str, str]:
        """Generate an interactable interface."""
        lines = []
        
        lines.append("#pragma once")
        lines.append("")
        lines.append("#include \"CoreMinimal.h\"")
        lines.append("#include \"UObject/Interface.h\"")
        lines.append(f'#include "{class_name}Interface.generated.h"')
        lines.append("")
        lines.append("UINTERFACE(MinimalAPI)")
        lines.append(f"class U{class_name}Interface : public UInterface")
        lines.append("{")
        lines.append("    GENERATED_BODY()")
        lines.append("};")
        lines.append("")
        lines.append(f"class I{class_name}Interface")
        lines.append("{")
        lines.append("    GENERATED_BODY()")
        lines.append("")
        lines.append("public:")
        lines.append(f"    /** Called when the player interacts with this object */")
        lines.append(f"    UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category=\"Interaction\")")
        lines.append(f"    void OnInteract(AActor* InteractingActor);")
        lines.append("")
        lines.append(f"    /** Returns true if this object can be interacted with */")
        lines.append(f"    UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category=\"Interaction\")")
        lines.append(f"    bool CanInteract(AActor* InteractingActor) const;")
        lines.append("")
        lines.append(f"    /** Returns the interaction prompt text */")
        lines.append(f"    UFUNCTION(BlueprintCallable, BlueprintNativeEvent, Category=\"Interaction\")")
        lines.append(f"    FText GetInteractionPrompt() const;")
        lines.append("};")
        
        return {
            "header": "\n".join(lines),
            "cpp": ""
        }
