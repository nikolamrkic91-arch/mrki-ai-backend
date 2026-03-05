class_name {{class_name}}
extends Node
## {{description}}

#region Singleton
static var instance: {{class_name}} = null

func _enter_tree():
	if instance == null:
		instance = self
	else:
		queue_free()
		return
	
	if {{dont_destroy_on_load}}:
		process_mode = Node.PROCESS_MODE_ALWAYS
#endregion

#region Signals
signal game_started
signal game_paused
signal game_resumed
signal game_ended
signal state_changed(new_state: GameState)
signal score_updated(new_score: int)
#endregion

#region Enums
enum GameState {
	MENU,
	PLAYING,
	PAUSED,
	ENDED
}
#endregion

#region Export Variables
@export_group("Settings")
@export var auto_start: bool = false
@export var pause_on_focus_loss: bool = true

@export_group("Score")
@export var starting_score: int = 0
#endregion

#region Public Variables
var current_state: GameState = GameState.MENU
var game_time: float = 0.0
var score: int = 0:
	set(value):
		score = value
		emit_signal("score_updated", score)
#endregion

#region Private Variables
var _systems: Dictionary = {}
var _is_initialized: bool = false
#endregion

func _ready():
	if auto_start:
		start_game()
	_is_initialized = true

func _process(delta: float):
	if current_state == GameState.PLAYING:
		game_time += delta
		_update_systems(delta)

func _notification(what: int):
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT and pause_on_focus_loss:
		pause_game()

#region State Management
func start_game():
	if current_state == GameState.PLAYING:
		return
	
	current_state = GameState.PLAYING
	get_tree().paused = false
	game_time = 0.0
	score = starting_score
	emit_signal("game_started")
	emit_signal("state_changed", current_state)

func pause_game():
	if current_state != GameState.PLAYING:
		return
	
	current_state = GameState.PAUSED
	get_tree().paused = true
	emit_signal("game_paused")
	emit_signal("state_changed", current_state)

func resume_game():
	if current_state != GameState.PAUSED:
		return
	
	current_state = GameState.PLAYING
	get_tree().paused = false
	emit_signal("game_resumed")
	emit_signal("state_changed", current_state)

func end_game():
	current_state = GameState.ENDED
	emit_signal("game_ended")
	emit_signal("state_changed", current_state)

func toggle_pause():
	match current_state:
		GameState.PLAYING:
			pause_game()
		GameState.PAUSED:
			resume_game()
#endregion

#region System Registry
func register_system(system_name: String, system: Node):
	_systems[system_name] = system

func get_system(system_name: String) -> Node:
	return _systems.get(system_name)

func has_system(system_name: String) -> bool:
	return _systems.has(system_name)

func unregister_system(system_name: String):
	_systems.erase(system_name)

func _update_systems(delta: float):
	for system in _systems.values():
		if system.has_method("on_update"):
			system.on_update(delta)
#endregion

#region Score Management
func add_score(points: int):
	score += points

func reset_score():
	score = starting_score

func set_score(value: int):
	score = value
#endregion

#region Utility
func reset_game_time():
	game_time = 0.0

func get_formatted_time() -> String:
	var minutes = int(game_time) / 60
	var seconds = int(game_time) % 60
	return "%02d:%02d" % [minutes, seconds]

func is_playing() -> bool:
	return current_state == GameState.PLAYING

func load_scene(scene_path: String):
	get_tree().change_scene_to_file(scene_path)
#endregion
