"""
Game Design Pattern Library
Common game design patterns and their implementations.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class DesignPattern:
    """Represents a game design pattern."""
    name: str
    category: str
    description: str
    problem: str
    solution: str
    implementation: Dict[str, str] = field(default_factory=dict)
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    related_patterns: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "problem": self.problem,
            "solution": self.solution,
            "implementation": self.implementation,
            "pros": self.pros,
            "cons": self.cons,
            "related_patterns": self.related_patterns
        }


class PatternLibrary:
    """Library of game design patterns."""
    
    def __init__(self):
        self.patterns: Dict[str, DesignPattern] = {}
        self._register_default_patterns()
    
    def _register_default_patterns(self):
        """Register default design patterns."""
        self._register_creational_patterns()
        self._register_structural_patterns()
        self._register_behavioral_patterns()
        self._register_gameplay_patterns()
        self._register_architectural_patterns()
    
    def register_pattern(self, pattern: DesignPattern):
        """Register a design pattern."""
        self.patterns[pattern.name] = pattern
    
    def get_pattern(self, name: str) -> Optional[DesignPattern]:
        """Get a pattern by name."""
        return self.patterns.get(name)
    
    def get_patterns_by_category(self, category: str) -> List[DesignPattern]:
        """Get all patterns in a category."""
        return [p for p in self.patterns.values() if p.category == category]
    
    def search_patterns(self, query: str) -> List[DesignPattern]:
        """Search patterns by query."""
        results = []
        query_lower = query.lower()
        
        for pattern in self.patterns.values():
            if (query_lower in pattern.name.lower() or
                query_lower in pattern.description.lower() or
                query_lower in pattern.category.lower()):
                results.append(pattern)
        
        return results
    
    def _register_creational_patterns(self):
        """Register creational design patterns."""
        # Singleton
        singleton = DesignPattern(
            name="Singleton",
            category="Creational",
            description="Ensures a class has only one instance and provides global access to it.",
            problem="You need exactly one instance of a class and need global access to it.",
            solution="Make the class itself responsible for keeping track of its sole instance.",
            implementation={
                "unity": '''public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }
    
    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }
}''',
                "godot": '''extends Node

class_name GameManager

static var instance: GameManager = null

func _ready():
    if instance == null:
        instance = self
    else:
        queue_free()''',
                "unreal": '''UCLASS()
class MYGAME_API UGameManager : public UObject
{
    GENERATED_BODY()
    
public:
    static UGameManager* GetInstance();
    
private:
    static UGameManager* Instance;
};'''
            },
            pros=[
                "Controlled access to sole instance",
                "Reduced namespace pollution",
                "Permits refinement of operations"
            ],
            cons=[
                "Violates Single Responsibility Principle",
                "Can mask bad design",
                "Requires special treatment in multithreaded environments"
            ],
            related_patterns=["Factory Method", "Abstract Factory"]
        )
        self.register_pattern(singleton)
        
        # Object Pool
        object_pool = DesignPattern(
            name="Object Pool",
            category="Creational",
            description="Manages a pool of reusable objects to improve performance.",
            problem="Creating and destroying objects frequently causes performance issues.",
            solution="Maintain a pool of initialized objects ready for use.",
            implementation={
                "unity": '''public class ObjectPool<T> where T : MonoBehaviour
{
    private Queue<T> pool = new Queue<T>();
    private T prefab;
    
    public ObjectPool(T prefab, int initialSize)
    {
        this.prefab = prefab;
        for (int i = 0; i < initialSize; i++)
        {
            T obj = Object.Instantiate(prefab);
            obj.gameObject.SetActive(false);
            pool.Enqueue(obj);
        }
    }
    
    public T Get()
    {
        if (pool.Count > 0)
        {
            T obj = pool.Dequeue();
            obj.gameObject.SetActive(true);
            return obj;
        }
        return Object.Instantiate(prefab);
    }
    
    public void Return(T obj)
    {
        obj.gameObject.SetActive(false);
        pool.Enqueue(obj);
    }
}''',
                "godot": '''class_name ObjectPool

var pool: Array = []
var scene: PackedScene
var parent: Node

func _init(p_scene: PackedScene, p_parent: Node, initial_size: int):
    scene = p_scene
    parent = p_parent
    for i in range(initial_size):
        var obj = scene.instantiate()
        obj.visible = false
        parent.add_child(obj)
        pool.append(obj)

func get_object() -> Node:
    if pool.size() > 0:
        var obj = pool.pop_back()
        obj.visible = true
        return obj
    return scene.instantiate()

func return_object(obj: Node):
    obj.visible = false
    pool.append(obj)'''
            },
            pros=[
                "Improves performance",
                "Reduces garbage collection pressure",
                "Predictable memory usage"
            ],
            cons=[
                "Increased memory usage",
                "More complex code",
                "Objects may need reset"
            ],
            related_patterns=["Factory Method", "Flyweight"]
        )
        self.register_pattern(object_pool)
    
    def _register_structural_patterns(self):
        """Register structural design patterns."""
        # Component Pattern
        component = DesignPattern(
            name="Component",
            category="Structural",
            description="Composes objects into tree structures to represent part-whole hierarchies.",
            problem="You want to treat individual objects and compositions uniformly.",
            solution="Define a component interface that both simple and complex objects implement.",
            implementation={
                "unity": '''// Unity uses this pattern natively with MonoBehaviour
public class HealthComponent : MonoBehaviour
{
    [SerializeField] private float maxHealth = 100f;
    public float CurrentHealth { get; private set; }
    
    public void TakeDamage(float damage)
    {
        CurrentHealth -= damage;
        if (CurrentHealth <= 0) Die();
    }
}

public class MovementComponent : MonoBehaviour
{
    [SerializeField] private float speed = 5f;
    
    public void Move(Vector3 direction)
    {
        transform.position += direction * speed * Time.deltaTime;
    }
}''',
                "godot": '''# Godot uses this pattern natively with nodes
class_name HealthComponent
extends Node

@export var max_health: float = 100.0
var current_health: float

func _ready():
    current_health = max_health

func take_damage(damage: float):
    current_health -= damage
    if current_health <= 0:
        die()'''
            },
            pros=[
                "Flexible object composition",
                "Easy to add/remove functionality",
                "Promotes code reuse"
            ],
            cons=[
                "Can lead to many small classes",
                "System design becomes more complex"
            ],
            related_patterns=["Decorator", "Strategy"]
        )
        self.register_pattern(component)
        
        # Observer Pattern
        observer = DesignPattern(
            name="Observer",
            category="Structural",
            description="Defines a subscription mechanism to notify multiple objects about events.",
            problem="You need to notify multiple objects when another object changes.",
            solution="Define a one-to-many dependency between objects.",
            implementation={
                "unity": '''public class HealthSystem : MonoBehaviour
{
    public event Action<float> OnHealthChanged;
    public event Action OnDeath;
    
    [SerializeField] private float maxHealth = 100f;
    private float currentHealth;
    
    public void TakeDamage(float damage)
    {
        currentHealth -= damage;
        OnHealthChanged?.Invoke(currentHealth);
        
        if (currentHealth <= 0)
            OnDeath?.Invoke();
    }
}

public class HealthUI : MonoBehaviour
{
    [SerializeField] private HealthSystem healthSystem;
    [SerializeField] private Slider healthSlider;
    
    private void OnEnable()
    {
        healthSystem.OnHealthChanged += UpdateHealthBar;
    }
    
    private void OnDisable()
    {
        healthSystem.OnHealthChanged -= UpdateHealthBar;
    }
    
    private void UpdateHealthBar(float health)
    {
        healthSlider.value = health;
    }
}''',
                "godot": '''class_name HealthSystem
extends Node

signal health_changed(current: float)
signal died

@export var max_health: float = 100.0
var current_health: float

func take_damage(damage: float):
    current_health -= damage
    health_changed.emit(current_health)
    if current_health <= 0:
        died.emit()

# In UI script:
func _ready():
    health_system.health_changed.connect(_on_health_changed)

func _on_health_changed(current: float):
    health_bar.value = current'''
            },
            pros=[
                "Loose coupling between objects",
                "Support for broadcast communication",
                "Easy to add/remove observers"
            ],
            cons=[
                "Can cause memory leaks if not unsubscribed",
                "Unexpected updates can be hard to debug"
            ],
            related_patterns=["Mediator", "Singleton"]
        )
        self.register_pattern(observer)
    
    def _register_behavioral_patterns(self):
        """Register behavioral design patterns."""
        # State Pattern
        state = DesignPattern(
            name="State",
            category="Behavioral",
            description="Allows an object to alter its behavior when its internal state changes.",
            problem="An object's behavior depends on its state, and it must change behavior at runtime.",
            solution="Define states as separate classes and delegate state-specific behavior.",
            implementation={
                "unity": '''public interface IPlayerState
{
    void Enter(PlayerController player);
    void Update(PlayerController player);
    void Exit(PlayerController player);
}

public class IdleState : IPlayerState
{
    public void Enter(PlayerController player) { }
    
    public void Update(PlayerController player)
    {
        if (Input.GetAxisRaw("Horizontal") != 0)
            player.ChangeState(new RunState());
        if (Input.GetButtonDown("Jump"))
            player.ChangeState(new JumpState());
    }
    
    public void Exit(PlayerController player) { }
}

public class PlayerController : MonoBehaviour
{
    private IPlayerState currentState;
    
    private void Start()
    {
        ChangeState(new IdleState());
    }
    
    private void Update()
    {
        currentState?.Update(this);
    }
    
    public void ChangeState(IPlayerState newState)
    {
        currentState?.Exit(this);
        currentState = newState;
        currentState.Enter(this);
    }
}''',
                "godot": '''class_name PlayerState
extends RefCounted

func enter(player: PlayerController):
    pass

func update(player: PlayerController, delta: float):
    pass

func exit(player: PlayerController):
    pass

class_name IdleState
extends PlayerState

func update(player: PlayerController, delta: float):
    if Input.get_axis("move_left", "move_right") != 0:
        player.change_state(RunState.new())
    if Input.is_action_just_pressed("jump"):
        player.change_state(JumpState.new())'''
            },
            pros=[
                "Organizes state-specific behavior",
                "Eliminates large conditional statements",
                "Makes state transitions explicit"
            ],
            cons=[
                "Can result in many state classes",
                "State changes may not be obvious"
            ],
            related_patterns=["Strategy", "Flyweight"]
        )
        self.register_pattern(state)
        
        # Command Pattern
        command = DesignPattern(
            name="Command",
            category="Behavioral",
            description="Encapsulates a request as an object, allowing parameterization and queuing.",
            problem="You need to parameterize objects with operations, queue requests, or support undo.",
            solution="Turn the request into a stand-alone object.",
            implementation={
                "unity": '''public interface ICommand
{
    void Execute();
    void Undo();
}

public class MoveCommand : ICommand
{
    private Transform transform;
    private Vector3 movement;
    private Vector3 previousPosition;
    
    public MoveCommand(Transform transform, Vector3 movement)
    {
        this.transform = transform;
        this.movement = movement;
    }
    
    public void Execute()
    {
        previousPosition = transform.position;
        transform.position += movement;
    }
    
    public void Undo()
    {
        transform.position = previousPosition;
    }
}

public class CommandInvoker
{
    private Stack<ICommand> commandHistory = new Stack<ICommand>();
    
    public void ExecuteCommand(ICommand command)
    {
        command.Execute();
        commandHistory.Push(command);
    }
    
    public void Undo()
    {
        if (commandHistory.Count > 0)
        {
            commandHistory.Pop().Undo();
        }
    }
}'''
            },
            pros=[
                "Decouples invoker from receiver",
                "Supports undo/redo",
                "Allows command composition"
            ],
            cons=[
                "Can result in many command classes",
                "May increase memory usage"
            ],
            related_patterns=["Memento", "Prototype"]
        )
        self.register_pattern(command)
    
    def _register_gameplay_patterns(self):
        """Register gameplay-specific patterns."""
        # Game Loop
        game_loop = DesignPattern(
            name="Game Loop",
            category="Gameplay",
            description="Central loop that drives game progression and updates.",
            problem="You need a consistent way to update game state and render frames.",
            solution="Use a main loop that processes input, updates game state, and renders output.",
            implementation={
                "unity": '''// Unity handles this automatically
public class GameManager : MonoBehaviour
{
    private void Update()
    {
        // Called every frame - use for input and non-physics updates
        ProcessInput();
    }
    
    private void FixedUpdate()
    {
        // Called at fixed intervals - use for physics
        UpdatePhysics();
    }
    
    private void LateUpdate()
    {
        // Called after all Updates - use for camera follow
        UpdateCamera();
    }
}''',
                "godot": '''extends Node

func _process(delta: float):
    # Called every frame
    process_input()
    update_game_state(delta)

func _physics_process(delta: float):
    # Called at fixed rate for physics
    update_physics(delta)''',
                "unreal": '''void AMyGameMode::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    
    // Custom game loop logic
    ProcessInput(DeltaTime);
    UpdateGameState(DeltaTime);
}'''
            },
            pros=[
                "Consistent update timing",
                "Separation of concerns",
                "Easy to profile and optimize"
            ],
            cons=[
                "Frame rate dependency",
                "Complexity with variable time steps"
            ],
            related_patterns=["Update Method", "Double Buffering"]
        )
        self.register_pattern(game_loop)
        
        # Entity Component System (ECS)
        ecs = DesignPattern(
            name="Entity Component System",
            category="Gameplay",
            description="Architectural pattern that separates data (components) from behavior (systems).",
            problem="Traditional OOP inheritance hierarchies become too complex.",
            solution="Use composition: Entities are IDs, Components are data, Systems process entities.",
            implementation={
                "unity": '''// Unity DOTS/ECS
public struct Health : IComponentData
{
    public float Current;
    public float Max;
}

public struct Position : IComponentData
{
    public float3 Value;
}

public partial struct HealthSystem : ISystem
{
    public void OnUpdate(ref SystemState state)
    {
        foreach (var health in 
            SystemAPI.Query<RefRW<Health>>())
        {
            if (health.ValueRW.Current <= 0)
            {
                // Handle death
            }
        }
    }
}''',
                "godot": '''# Godot doesn't have native ECS, but you can implement it
class_name ECSWorld
extends Node

var entities: Dictionary = {}
var systems: Array[ECSSystem] = []

func _process(delta: float):
    for system in systems:
        system.update(delta, entities)

class Entity:
    var id: int
    var components: Dictionary = {}
    
    func add_component(component: ECSComponent):
        components[component.get_class()] = component
    
    func get_component(component_type: String) -> ECSComponent:
        return components.get(component_type)'''
            },
            pros=[
                "High performance with data-oriented design",
                "Cache-friendly memory layout",
                "Easy to parallelize"
            ],
            cons=[
                "Steep learning curve",
                "Different way of thinking",
                "Less intuitive for some developers"
            ],
            related_patterns=["Component", "Data Locality"]
        )
        self.register_pattern(ecs)
    
    def _register_architectural_patterns(self):
        """Register architectural patterns."""
        # Service Locator
        service_locator = DesignPattern(
            name="Service Locator",
            category="Architectural",
            description="Central registry that provides access to services throughout the application.",
            problem="You need global access to services without tight coupling.",
            solution="Create a registry that maps service interfaces to concrete implementations.",
            implementation={
                "unity": '''public class ServiceLocator : MonoBehaviour
{
    private static Dictionary<Type, object> services = new Dictionary<Type, object>();
    
    public static void Register<T>(T service) where T : class
    {
        services[typeof(T)] = service;
    }
    
    public static T Get<T>() where T : class
    {
        if (services.TryGetValue(typeof(T), out object service))
        {
            return service as T;
        }
        return null;
    }
    
    public static void Unregister<T>() where T : class
    {
        services.Remove(typeof(T));
    }
}

// Usage:
ServiceLocator.Register<IAudioManager>(new AudioManager());
var audio = ServiceLocator.Get<IAudioManager>();'''
            },
            pros=[
                "Decouples service consumers from providers",
                "Easy to swap implementations",
                "Centralized service management"
            ],
            cons=[
                "Can hide dependencies",
                "Runtime errors if service not registered",
                "Global state issues"
            ],
            related_patterns=["Singleton", "Dependency Injection"]
        )
        self.register_pattern(service_locator)
        
        # Event Bus
        event_bus = DesignPattern(
            name="Event Bus",
            category="Architectural",
            description="Central channel for publishing and subscribing to events.",
            problem="You need decoupled communication between many game systems.",
            solution="Use a central event dispatcher that systems can publish to and subscribe from.",
            implementation={
                "unity": '''public class EventBus : MonoBehaviour
{
    public static EventBus Instance { get; private set; }
    
    private Dictionary<Type, Delegate> events = new Dictionary<Type, Delegate>();
    
    private void Awake()
    {
        Instance = this;
    }
    
    public void Subscribe<T>(Action<T> handler) where T : GameEvent
    {
        if (!events.ContainsKey(typeof(T)))
            events[typeof(T)] = null;
        
        events[typeof(T)] = (Action<T>)events[typeof(T)] + handler;
    }
    
    public void Unsubscribe<T>(Action<T> handler) where T : GameEvent
    {
        if (events.ContainsKey(typeof(T)))
            events[typeof(T)] = (Action<T>)events[typeof(T)] - handler;
    }
    
    public void Publish<T>(T eventData) where T : GameEvent
    {
        if (events.ContainsKey(typeof(T)))
            ((Action<T>)events[typeof(T)])?.Invoke(eventData);
    }
}

public abstract class GameEvent { }

public class PlayerDamagedEvent : GameEvent
{
    public float DamageAmount;
    public GameObject Attacker;
}'''
            },
            pros=[
                "Highly decoupled systems",
                "Easy to add new event types",
                "Centralized event handling"
            ],
            cons=[
                "Can be hard to debug",
                "Potential for memory leaks",
                "Event ordering issues"
            ],
            related_patterns=["Observer", "Mediator"]
        )
        self.register_pattern(event_bus)
    
    def export_patterns(self, filepath: str):
        """Export all patterns to a JSON file."""
        import json
        data = {
            "patterns": [p.to_dict() for p in self.patterns.values()]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_all_categories(self) -> List[str]:
        """Get all pattern categories."""
        categories = set()
        for pattern in self.patterns.values():
            categories.add(pattern.category)
        return sorted(list(categories))
