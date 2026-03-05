"""
C# Code Generator for Unity
Generates C# scripts for Unity game development.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class ScriptType(Enum):
    MONOBEHAVIOUR = "MonoBehaviour"
    SCRIPTABLE_OBJECT = "ScriptableObject"
    EDITOR = "Editor"
    STATIC = "Static"
    INTERFACE = "Interface"
    ABSTRACT = "Abstract"


class AccessModifier(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    INTERNAL = "internal"
    PROTECTED_INTERNAL = "protected internal"


@dataclass
class Field:
    """Represents a C# field."""
    name: str
    type: str
    access: AccessModifier = AccessModifier.PRIVATE
    default_value: Optional[str] = None
    attributes: List[str] = field(default_factory=list)
    serialize_field: bool = False
    tooltip: Optional[str] = None
    
    def generate(self) -> str:
        lines = []
        
        # Add attributes
        if self.serialize_field:
            lines.append("        [SerializeField]")
        if self.tooltip:
            lines.append(f'        [Tooltip("{self.tooltip}")]')
        for attr in self.attributes:
            lines.append(f"        [{attr}]")
        
        # Field declaration
        default = f" = {self.default_value};" if self.default_value else ";"
        lines.append(f"        {self.access.value} {self.type} {self.name}{default}")
        
        return "\n".join(lines)


@dataclass
class Method:
    """Represents a C# method."""
    name: str
    return_type: str = "void"
    parameters: List[tuple] = field(default_factory=list)
    access: AccessModifier = AccessModifier.PRIVATE
    is_virtual: bool = False
    is_override: bool = False
    is_static: bool = False
    body: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    
    def generate(self) -> str:
        lines = []
        
        # XML documentation
        if self.summary:
            lines.append("        /// <summary>")
            lines.append(f"        /// {self.summary}")
            lines.append("        /// </summary>")
        
        # Attributes
        for attr in self.attributes:
            lines.append(f"        [{attr}]")
        
        # Method signature
        modifiers = []
        if self.is_static:
            modifiers.append("static")
        if self.is_override:
            modifiers.append("override")
        elif self.is_virtual:
            modifiers.append("virtual")
        
        modifier_str = " ".join(modifiers)
        if modifier_str:
            signature = f"        {self.access.value} {modifier_str} {self.return_type} {self.name}"
        else:
            signature = f"        {self.access.value} {self.return_type} {self.name}"
        
        # Parameters
        if self.parameters:
            params = ", ".join([f"{p[0]} {p[1]}" for p in self.parameters])
            signature += f"({params})"
        else:
            signature += "()"
        
        lines.append(signature)
        lines.append("        {")
        
        # Method body
        if self.body:
            for line in self.body:
                lines.append(f"            {line}")
        else:
            if self.return_type != "void":
                lines.append(f"            return default({self.return_type});")
        
        lines.append("        }")
        
        return "\n".join(lines)


@dataclass
class Property:
    """Represents a C# property."""
    name: str
    type: str
    access: AccessModifier = AccessModifier.PUBLIC
    getter: bool = True
    setter: bool = True
    getter_access: Optional[AccessModifier] = None
    setter_access: Optional[AccessModifier] = None
    backing_field: Optional[str] = None
    
    def generate(self) -> str:
        lines = []
        
        if self.backing_field:
            lines.append(f"        private {self.type} {self.backing_field};")
        
        getter = "get;" if self.getter else ""
        setter = " set;" if self.setter else ""
        
        if self.getter_access:
            getter = f"{self.getter_access.value} get;"
        if self.setter_access:
            setter = f" {self.setter_access.value} set;"
        
        lines.append(f"        {self.access.value} {self.type} {self.name} {{ {getter}{setter} }}")
        
        return "\n".join(lines)


class CSharpCodeGenerator:
    """Generator for C# Unity scripts."""
    
    def __init__(self):
        self.using_statements: List[str] = []
        self.namespace: Optional[str] = None
        self.class_name: str = ""
        self.script_type: ScriptType = ScriptType.MONOBEHAVIOUR
        self.inheritance: List[str] = []
        self.fields: List[Field] = []
        self.properties: List[Property] = []
        self.methods: List[Method] = []
        self.attributes: List[str] = []
        self.summary: Optional[str] = None
        self.regions: Dict[str, List[str]] = {}
        
    def set_namespace(self, namespace: str):
        """Set the namespace for the script."""
        self.namespace = namespace
        return self
    
    def add_using(self, namespace: str):
        """Add a using statement."""
        if namespace not in self.using_statements:
            self.using_statements.append(namespace)
        return self
    
    def set_class(self, name: str, script_type: ScriptType = ScriptType.MONOBEHAVIOUR):
        """Set the class name and type."""
        self.class_name = name
        self.script_type = script_type
        return self
    
    def inherits_from(self, base_class: str):
        """Add base class inheritance."""
        self.inheritance.append(base_class)
        return self
    
    def add_field(self, field: Field):
        """Add a field to the class."""
        self.fields.append(field)
        return self
    
    def add_property(self, prop: Property):
        """Add a property to the class."""
        self.properties.append(prop)
        return self
    
    def add_method(self, method: Method):
        """Add a method to the class."""
        self.methods.append(method)
        return self
    
    def add_attribute(self, attribute: str):
        """Add a class-level attribute."""
        self.attributes.append(attribute)
        return self
    
    def set_summary(self, summary: str):
        """Set the class XML documentation summary."""
        self.summary = summary
        return self
    
    def generate(self) -> str:
        """Generate the complete C# script."""
        lines = []
        
        # Using statements
        default_usings = [
            "UnityEngine",
            "System.Collections",
            "System.Collections.Generic"
        ]
        
        for u in default_usings:
            if u not in self.using_statements:
                lines.append(f"using {u};")
        
        for u in self.using_statements:
            if u not in default_usings:
                lines.append(f"using {u};")
        
        lines.append("")
        
        # Namespace
        if self.namespace:
            lines.append(f"namespace {self.namespace}")
            lines.append("{")
            indent = "    "
        else:
            indent = ""
        
        # Class documentation
        if self.summary:
            lines.append(f"{indent}/// <summary>")
            lines.append(f"{indent}/// {self.summary}")
            lines.append(f"{indent}/// </summary>")
        
        # Class attributes
        for attr in self.attributes:
            lines.append(f"{indent}[{attr}]")
        
        # Class declaration
        base_class = self.script_type.value
        if self.inheritance:
            base_class = ", ".join([base_class] + self.inheritance)
        
        lines.append(f"{indent}public class {self.class_name} : {base_class}")
        lines.append(f"{indent}{{")
        
        # Fields
        if self.fields:
            lines.append(f"{indent}    #region Fields")
            lines.append("")
            for field in self.fields:
                lines.append(field.generate())
                lines.append("")
            lines.append(f"{indent}    #endregion")
            lines.append("")
        
        # Properties
        if self.properties:
            lines.append(f"{indent}    #region Properties")
            lines.append("")
            for prop in self.properties:
                lines.append(prop.generate())
                lines.append("")
            lines.append(f"{indent}    #endregion")
            lines.append("")
        
        # Unity Lifecycle Methods
        lifecycle_methods = [m for m in self.methods if m.name in [
            "Awake", "Start", "OnEnable", "OnDisable", "OnDestroy",
            "Update", "FixedUpdate", "LateUpdate"
        ]]
        
        if lifecycle_methods:
            lines.append(f"{indent}    #region Unity Lifecycle")
            lines.append("")
            for method in lifecycle_methods:
                lines.append(method.generate())
                lines.append("")
            lines.append(f"{indent}    #endregion")
            lines.append("")
        
        # Other methods
        other_methods = [m for m in self.methods if m.name not in [
            "Awake", "Start", "OnEnable", "OnDisable", "OnDestroy",
            "Update", "FixedUpdate", "LateUpdate"
        ]]
        
        if other_methods:
            lines.append(f"{indent}    #region Public Methods")
            lines.append("")
            for method in other_methods:
                if method.access == AccessModifier.PUBLIC:
                    lines.append(method.generate())
                    lines.append("")
            lines.append(f"{indent}    #endregion")
            lines.append("")
            
            lines.append(f"{indent}    #region Private Methods")
            lines.append("")
            for method in other_methods:
                if method.access != AccessModifier.PUBLIC:
                    lines.append(method.generate())
                    lines.append("")
            lines.append(f"{indent}    #endregion")
            lines.append("")
        
        lines.append(f"{indent}}}")
        
        if self.namespace:
            lines.append("}")
        
        return "\n".join(lines)
    
    # Preset generators for common Unity patterns
    
    def generate_singleton(self, class_name: str) -> str:
        """Generate a singleton MonoBehaviour."""
        self.set_class(class_name)
        self.set_summary(f"Singleton pattern implementation for {class_name}")
        
        self.add_property(Property(
            name="Instance",
            type=class_name,
            getter=True,
            setter=False
        ))
        
        self.add_field(Field(
            name="_instance",
            type=class_name,
            access=AccessModifier.PRIVATE,
            attributes=["[SerializeField]"]
        ))
        
        self.add_method(Method(
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
        
        return self.generate()
    
    def generate_game_manager(self) -> str:
        """Generate a GameManager singleton."""
        self.set_class("GameManager")
        self.set_summary("Central game manager for global game state")
        
        self.add_field(Field(
            name="_instance",
            type="GameManager",
            access=AccessModifier.PRIVATE,
            attributes=["[SerializeField]"]
        ))
        
        self.add_field(Field(
            name="gameState",
            type="GameState",
            access=AccessModifier.PRIVATE,
            default_value="GameState.MainMenu",
            tooltip="Current game state"
        ))
        
        self.add_field(Field(
            name="score",
            type="int",
            access=AccessModifier.PRIVATE,
            default_value="0",
            tooltip="Player score"
        ))
        
        self.add_property(Property(
            name="Instance",
            type="GameManager",
            getter=True,
            setter=False
        ))
        
        self.add_property(Property(
            name="CurrentState",
            type="GameState",
            getter=True,
            setter=True
        ))
        
        self.add_method(Method(
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
        
        self.add_method(Method(
            name="ChangeState",
            access=AccessModifier.PUBLIC,
            parameters=[("GameState", "newState")],
            summary="Change the current game state",
            body=[
                "gameState = newState;",
                "OnStateChanged?.Invoke(newState);"
            ]
        ))
        
        self.add_method(Method(
            name="AddScore",
            access=AccessModifier.PUBLIC,
            parameters=[("int", "points")],
            summary="Add points to the score",
            body=[
                "score += points;",
                "OnScoreChanged?.Invoke(score);"
            ]
        ))
        
        return self.generate()
    
    def generate_player_controller(self, is_3d: bool = True) -> str:
        """Generate a player controller."""
        self.set_class("PlayerController")
        self.set_summary("Player character controller")
        
        if is_3d:
            self.add_field(Field(
                name="moveSpeed",
                type="float",
                access=AccessModifier.PRIVATE,
                default_value="5f",
                serialize_field=True,
                tooltip="Player movement speed"
            ))
            
            self.add_field(Field(
                name="rotationSpeed",
                type="float",
                access=AccessModifier.PRIVATE,
                default_value="10f",
                serialize_field=True,
                tooltip="Player rotation speed"
            ))
            
            self.add_field(Field(
                name="jumpForce",
                type="float",
                access=AccessModifier.PRIVATE,
                default_value="10f",
                serialize_field=True,
                tooltip="Jump force"
            ))
            
            self.add_field(Field(
                name="groundCheck",
                type="Transform",
                access=AccessModifier.PRIVATE,
                serialize_field=True,
                tooltip="Ground check transform"
            ))
            
            self.add_field(Field(
                name="groundLayer",
                type="LayerMask",
                access=AccessModifier.PRIVATE,
                serialize_field=True,
                tooltip="Ground layer mask"
            ))
            
            self.add_field(Field(
                name="controller",
                type="CharacterController",
                access=AccessModifier.PRIVATE
            ))
            
            self.add_field(Field(
                name="velocity",
                type="Vector3",
                access=AccessModifier.PRIVATE
            ))
            
            self.add_field(Field(
                name="isGrounded",
                type="bool",
                access=AccessModifier.PRIVATE
            ))
            
            self.add_method(Method(
                name="Start",
                access=AccessModifier.PRIVATE,
                body=["controller = GetComponent<CharacterController>();"]
            ))
            
            self.add_method(Method(
                name="Update",
                access=AccessModifier.PRIVATE,
                body=[
                    "isGrounded = Physics.CheckSphere(groundCheck.position, 0.3f, groundLayer);",
                    "",
                    "if (isGrounded && velocity.y < 0)",
                    "{",
                    "    velocity.y = -2f;",
                    "}",
                    "",
                    "float horizontal = Input.GetAxis(\"Horizontal\");",
                    "float vertical = Input.GetAxis(\"Vertical\");",
                    "",
                    "Vector3 direction = transform.right * horizontal + transform.forward * vertical;",
                    "controller.Move(direction * moveSpeed * Time.deltaTime);",
                    "",
                    "if (Input.GetButtonDown(\"Jump\") && isGrounded)",
                    "{",
                    "    velocity.y = Mathf.Sqrt(jumpForce * -2f * Physics.gravity.y);",
                    "}",
                    "",
                    "velocity.y += Physics.gravity.y * Time.deltaTime;",
                    "controller.Move(velocity * Time.deltaTime);"
                ]
            ))
        else:
            # 2D controller
            self.add_field(Field(
                name="moveSpeed",
                type="float",
                access=AccessModifier.PRIVATE,
                default_value="5f",
                serialize_field=True
            ))
            
            self.add_field(Field(
                name="jumpForce",
                type="float",
                access=AccessModifier.PRIVATE,
                default_value="10f",
                serialize_field=True
            ))
            
            self.add_field(Field(
                name="rb",
                type="Rigidbody2D",
                access=AccessModifier.PRIVATE
            ))
            
            self.add_field(Field(
                name="groundCheck",
                type="Transform",
                access=AccessModifier.PRIVATE,
                serialize_field=True
            ))
            
            self.add_field(Field(
                name="groundLayer",
                type="LayerMask",
                access=AccessModifier.PRIVATE,
                serialize_field=True
            ))
            
            self.add_method(Method(
                name="Start",
                access=AccessModifier.PRIVATE,
                body=["rb = GetComponent<Rigidbody2D>();"]
            ))
            
            self.add_method(Method(
                name="Update",
                access=AccessModifier.PRIVATE,
                body=[
                    "float horizontal = Input.GetAxis(\"Horizontal\");",
                    "rb.velocity = new Vector2(horizontal * moveSpeed, rb.velocity.y);",
                    "",
                    "if (Input.GetButtonDown(\"Jump\") && IsGrounded())",
                    "{",
                    "    rb.velocity = new Vector2(rb.velocity.x, jumpForce);",
                    "}"
                ]
            ))
            
            self.add_method(Method(
                name="IsGrounded",
                access=AccessModifier.PRIVATE,
                return_type="bool",
                body=[
                    "return Physics2D.OverlapCircle(groundCheck.position, 0.2f, groundLayer);"
                ]
            ))
        
        return self.generate()
    
    def generate_state_machine(self, class_name: str, states: List[str]) -> str:
        """Generate a state machine."""
        self.set_class(class_name)
        self.set_summary(f"State machine for {class_name}")
        
        self.add_field(Field(
            name="currentState",
            type=f"I{class_name}State",
            access=AccessModifier.PRIVATE
        ))
        
        self.add_field(Field(
            name="states",
            type=f"Dictionary<string, I{class_name}State>",
            access=AccessModifier.PRIVATE,
            default_value="new Dictionary<string, I{class_name}State>()"
        ))
        
        self.add_method(Method(
            name="ChangeState",
            access=AccessModifier.PUBLIC,
            parameters=[("string", "stateName")],
            body=[
                "if (states.ContainsKey(stateName))",
                "{",
                "    currentState?.Exit();",
                "    currentState = states[stateName];",
                "    currentState.Enter();",
                "}"
            ]
        ))
        
        self.add_method(Method(
            name="Update",
            access=AccessModifier.PRIVATE,
            body=["currentState?.Update();"]
        ))
        
        return self.generate()
