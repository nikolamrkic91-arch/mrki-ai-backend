using System;
using System.Collections.Generic;

namespace {{namespace}}
{
    /// <summary>
    /// Generic state machine for game entities
    /// </summary>
    public class StateMachine<T> where T : Enum
    {
        private Dictionary<T, State<T>> states = new Dictionary<T, State<T>>();
        private State<T> currentState;
        private T currentStateType;

        public T CurrentState => currentStateType;
        public bool IsInState(T state) => EqualityComparer<T>.Default.Equals(currentStateType, state);

        public void AddState(T stateType, State<T> state)
        {
            states[stateType] = state;
            state.StateMachine = this;
        }

        public void ChangeState(T newStateType)
        {
            if (!states.ContainsKey(newStateType))
            {
                UnityEngine.Debug.LogError($"State {newStateType} not found!");
                return;
            }

            currentState?.Exit();
            currentStateType = newStateType;
            currentState = states[newStateType];
            currentState.Enter();
        }

        public void Update()
        {
            currentState?.Update();
        }

        public void FixedUpdate()
        {
            currentState?.FixedUpdate();
        }
    }

    public abstract class State<T> where T : Enum
    {
        public StateMachine<T> StateMachine { get; set; }
        
        public abstract void Enter();
        public abstract void Update();
        public abstract void FixedUpdate();
        public abstract void Exit();
    }
}
