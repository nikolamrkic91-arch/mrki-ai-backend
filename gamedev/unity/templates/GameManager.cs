using UnityEngine;
using System;
using System.Collections.Generic;

namespace {{namespace}}
{
    /// <summary>
    /// {{description}}
    /// </summary>
    public class {{class_name}} : MonoBehaviour
    {
        public static {{class_name}} Instance { get; private set; }

        [Header("Game Settings")]
        [SerializeField] private bool dontDestroyOnLoad = true;
        [SerializeField] private bool pauseOnStart = false;

        // Events
        public event Action OnGameStart;
        public event Action OnGamePause;
        public event Action OnGameResume;
        public event Action OnGameEnd;

        // State
        public GameState CurrentState { get; private set; } = GameState.Menu;
        public float GameTime { get; private set; } = 0f;

        // Systems registry
        private Dictionary<Type, object> systems = new Dictionary<Type, object>();

        private void Awake()
        {
            InitializeSingleton();
        }

        private void Start()
        {
            if (pauseOnStart)
            {
                PauseGame();
            }
            else
            {
                StartGame();
            }
        }

        private void Update()
        {
            if (CurrentState == GameState.Playing)
            {
                GameTime += Time.deltaTime;
                UpdateSystems();
            }
        }

        private void InitializeSingleton()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }

            Instance = this;
            
            if (dontDestroyOnLoad)
            {
                DontDestroyOnLoad(gameObject);
            }
        }

        #region Game State Management

        public void StartGame()
        {
            CurrentState = GameState.Playing;
            Time.timeScale = 1f;
            OnGameStart?.Invoke();
        }

        public void PauseGame()
        {
            if (CurrentState != GameState.Playing) return;
            
            CurrentState = GameState.Paused;
            Time.timeScale = 0f;
            OnGamePause?.Invoke();
        }

        public void ResumeGame()
        {
            if (CurrentState != GameState.Paused) return;
            
            CurrentState = GameState.Playing;
            Time.timeScale = 1f;
            OnGameResume?.Invoke();
        }

        public void EndGame()
        {
            CurrentState = GameState.Ended;
            OnGameEnd?.Invoke();
        }

        public void TogglePause()
        {
            if (CurrentState == GameState.Playing)
                PauseGame();
            else if (CurrentState == GameState.Paused)
                ResumeGame();
        }

        #endregion

        #region System Registry

        public void RegisterSystem<T>(T system) where T : class
        {
            systems[typeof(T)] = system;
        }

        public T GetSystem<T>() where T : class
        {
            if (systems.TryGetValue(typeof(T), out object system))
            {
                return system as T;
            }
            return null;
        }

        public bool HasSystem<T>() where T : class
        {
            return systems.ContainsKey(typeof(T));
        }

        private void UpdateSystems()
        {
            foreach (var system in systems.Values)
            {
                if (system is IGameSystem gameSystem)
                {
                    gameSystem.OnUpdate();
                }
            }
        }

        #endregion

        #region Utility

        public void ResetGameTime() => GameTime = 0f;
        public void SetTimeScale(float scale) => Time.timeScale = scale;

        #endregion
    }

    public enum GameState
    {
        Menu,
        Playing,
        Paused,
        Ended
    }

    public interface IGameSystem
    {
        void OnUpdate();
    }
}
