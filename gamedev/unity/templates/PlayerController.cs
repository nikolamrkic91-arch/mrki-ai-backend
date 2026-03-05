using UnityEngine;

namespace {{namespace}}
{
    /// <summary>
    /// {{description}}
    /// </summary>
    public class {{class_name}} : MonoBehaviour
    {
        [Header("Movement Settings")]
        [SerializeField] private float moveSpeed = 5f;
        [SerializeField] private float rotationSpeed = 10f;
        [SerializeField] private bool usePhysics = false;

        [Header("Input Settings")]
        [SerializeField] private string horizontalAxis = "Horizontal";
        [SerializeField] private string verticalAxis = "Vertical";

        // Components
        private Rigidbody rb;
        private CharacterController characterController;

        // State
        private Vector3 moveDirection;
        private bool isMoving;

        private void Awake()
        {
            rb = GetComponent<Rigidbody>();
            characterController = GetComponent<CharacterController>();
        }

        private void Update()
        {
            HandleInput();
            
            if (!usePhysics)
            {
                MoveCharacter();
            }
        }

        private void FixedUpdate()
        {
            if (usePhysics && rb != null)
            {
                MovePhysics();
            }
        }

        private void HandleInput()
        {
            float horizontal = Input.GetAxis(horizontalAxis);
            float vertical = Input.GetAxis(verticalAxis);

            moveDirection = new Vector3(horizontal, 0f, vertical).normalized;
            isMoving = moveDirection.magnitude > 0.1f;
        }

        private void MoveCharacter()
        {
            if (!isMoving) return;

            Vector3 movement = moveDirection * moveSpeed * Time.deltaTime;
            
            if (characterController != null)
            {
                characterController.Move(movement);
            }
            else
            {
                transform.position += movement;
            }

            // Rotation
            Quaternion targetRotation = Quaternion.LookRotation(moveDirection);
            transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, rotationSpeed * Time.deltaTime);
        }

        private void MovePhysics()
        {
            if (!isMoving) return;

            Vector3 movement = moveDirection * moveSpeed;
            rb.velocity = new Vector3(movement.x, rb.velocity.y, movement.z);

            // Rotation
            Quaternion targetRotation = Quaternion.LookRotation(moveDirection);
            rb.MoveRotation(Quaternion.Slerp(rb.rotation, targetRotation, rotationSpeed * Time.fixedDeltaTime));
        }

        #region Public API

        public void SetMoveSpeed(float speed) => moveSpeed = speed;
        public float GetMoveSpeed() => moveSpeed;
        public bool IsMoving() => isMoving;
        public void Teleport(Vector3 position) => transform.position = position;

        #endregion
    }
}
