class_name {{class_name}}
extends Node
## {{description}}

#region Signals
signal state_changed(from_state: String, to_state: String)
signal state_entered(state_name: String)
signal state_exited(state_name: String)
#endregion

#region Public Variables
var current_state: String = ""
var previous_state: String = ""
var is_active: bool = true
#endregion

#region Private Variables
var _states: Dictionary = {}
var _transitions: Dictionary = {}
#endregion

func _ready():
	pass

func _process(delta: float):
	if is_active and current_state != "":
		_call_state_method("update", delta)

func _physics_process(delta: float):
	if is_active and current_state != "":
		_call_state_method("physics_update", delta)

#region State Management
func add_state(state_name: String, state_data: Dictionary = {}):
	_states[state_name] = {
		"data": state_data,
		"enter": state_data.get("enter"),
		"exit": state_data.get("exit"),
		"update": state_data.get("update"),
		"physics_update": state_data.get("physics_update")
	}

func remove_state(state_name: String):
	_states.erase(state_name)
	_transitions.erase(state_name)

func change_state(new_state: String, args: Dictionary = {}):
	if not _states.has(new_state):
		push_error("State '" + new_state + "' does not exist!")
		return
	
	if new_state == current_state:
		return
	
	# Exit current state
	if current_state != "":
		_call_state_method("exit")
		emit_signal("state_exited", current_state)
	
	previous_state = current_state
	current_state = new_state
	
	# Enter new state
	emit_signal("state_changed", previous_state, current_state)
	emit_signal("state_entered", current_state)
	_call_state_method("enter", args)

func return_to_previous():
	if previous_state != "":
		change_state(previous_state)

func get_state_data(state_name: String = "") -> Dictionary:
	var state = current_state if state_name == "" else state_name
	if _states.has(state):
		return _states[state]["data"]
	return {}

func set_state_data(key: String, value, state_name: String = ""):
	var state = current_state if state_name == "" else state_name
	if _states.has(state):
		_states[state]["data"][key] = value
#endregion

#region Transitions
func add_transition(from_state: String, to_state: String, condition: Callable):
	if not _transitions.has(from_state):
		_transitions[from_state] = []
	_transitions[from_state].append({
		"to": to_state,
		"condition": condition
	})

func check_transitions():
	if not _transitions.has(current_state):
		return
	
	for transition in _transitions[current_state]:
		if transition.condition.call():
			change_state(transition.to)
			return
#endregion

#region Private Methods
func _call_state_method(method_name: String, arg = null):
	if current_state == "" or not _states.has(current_state):
		return
	
	var method = _states[current_state].get(method_name)
	if method and method is Callable:
		if arg != null:
			method.call(arg)
		else:
			method.call()
#endregion

#region Utility
func has_state(state_name: String) -> bool:
	return _states.has(state_name)

func get_states() -> Array:
	return _states.keys()

func clear():
	_states.clear()
	_transitions.clear()
	current_state = ""
	previous_state = ""
#endregion
