class_name {{class_name}}
extends CharacterBody3D
## {{description}}

#region Signals
signal moved(velocity: Vector3)
signal jumped
signal landed
signal state_changed(new_state: String)
#endregion

#region Export Variables
@export_group("Movement Settings")
@export var walk_speed: float = 5.0
@export var run_speed: float = 10.0
@export var jump_velocity: float = 4.5
@export var acceleration: float = 10.0
@export var friction: float = 10.0

@export_group("Camera Settings")
@export var mouse_sensitivity: float = 0.002
@export var camera_height: float = 1.5
@export var camera_limit_up: float = 89.0
@export var camera_limit_down: float = -89.0

@export_group("Input Actions")
@export var input_left: StringName = "ui_left"
@export var input_right: StringName = "ui_right"
@export var input_forward: StringName = "ui_up"
@export var input_back: StringName = "ui_down"
@export var input_jump: StringName = "ui_accept"
@export var input_run: StringName = "ui_shift"
#endregion

#region Onready Variables
@onready var camera_pivot: Node3D = $CameraPivot
@onready var camera: Camera3D = $CameraPivot/Camera3D
#endregion

#region Private Variables
var _velocity: Vector3 = Vector3.ZERO
var _is_running: bool = false
var _is_grounded: bool = false
#endregion

func _ready():
	_setup_camera()
	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

func _setup_camera():
	if camera_pivot:
		camera_pivot.position.y = camera_height

func _unhandled_input(event: InputEvent):
	if event is InputEventMouseMotion:
		_rotate_camera(event.relative)

func _rotate_camera(relative: Vector2):
	if not camera_pivot:
		return
	
	# Horizontal rotation (yaw)
	rotate_y(-relative.x * mouse_sensitivity)
	
	# Vertical rotation (pitch)
	camera_pivot.rotate_x(-relative.y * mouse_sensitivity)
	camera_pivot.rotation.x = clamp(
		camera_pivot.rotation.x,
		deg_to_rad(camera_limit_down),
		deg_to_rad(camera_limit_up)
	)

func _physics_process(delta: float):
	_handle_input()
	_apply_movement(delta)
	_apply_gravity(delta)
	_apply_jump()
	
	move_and_slide()
	
	_check_landing()
	emit_signal("moved", velocity)

func _handle_input():
	_is_running = Input.is_action_pressed(input_run)

func _apply_movement(delta: float):
	var input_dir = Input.get_vector(input_left, input_right, input_forward, input_back)
	var direction = (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()
	
	var target_speed = _is_running if run_speed else walk_speed
	
	if direction:
		_velocity.x = lerp(_velocity.x, direction.x * target_speed, acceleration * delta)
		_velocity.z = lerp(_velocity.z, direction.z * target_speed, acceleration * delta)
	else:
		_velocity.x = lerp(_velocity.x, 0.0, friction * delta)
		_velocity.z = lerp(_velocity.z, 0.0, friction * delta)
	
	velocity.x = _velocity.x
	velocity.z = _velocity.z

func _apply_gravity(delta: float):
	if not is_on_floor():
		velocity += get_gravity() * delta

func _apply_jump():
	if Input.is_action_just_pressed(input_jump) and is_on_floor():
		velocity.y = jump_velocity
		emit_signal("jumped")

func _check_landing():
	var grounded = is_on_floor()
	if grounded and not _is_grounded:
		emit_signal("landed")
	_is_grounded = grounded

#region Public API
func teleport(position: Vector3):
	global_position = position
	velocity = Vector3.ZERO
	_velocity = Vector3.ZERO

func set_mouse_captured(captured: bool):
	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED if captured else Input.MOUSE_MODE_VISIBLE)

func get_movement_speed() -> float:
	return run_speed if _is_running else walk_speed

func is_moving() -> bool:
	return abs(velocity.x) > 0.1 or abs(velocity.z) > 0.1
#endregion
