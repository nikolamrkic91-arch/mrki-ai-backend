"""
Tween Systems
Smooth interpolation and animation utilities.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class EaseType(Enum):
    """Easing function types."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    ELASTIC_IN = "elastic_in"
    ELASTIC_OUT = "elastic_out"
    ELASTIC_IN_OUT = "elastic_in_out"
    BOUNCE_IN = "bounce_in"
    BOUNCE_OUT = "bounce_out"
    BOUNCE_IN_OUT = "bounce_in_out"
    BACK_IN = "back_in"
    BACK_OUT = "back_out"
    BACK_IN_OUT = "back_in_out"


class LoopType(Enum):
    """Tween loop types."""
    NONE = "none"
    RESTART = "restart"
    YOYO = "yoyo"
    INCREMENTAL = "incremental"


@dataclass
class TweenConfig:
    """Tween configuration."""
    duration: float = 1.0
    ease_type: EaseType = EaseType.LINEAR
    loop_type: LoopType = LoopType.NONE
    loops: int = 0
    delay: float = 0.0
    use_unscaled_time: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "duration": self.duration,
            "ease_type": self.ease_type.value,
            "loop_type": self.loop_type.value,
            "loops": self.loops,
            "delay": self.delay,
            "use_unscaled_time": self.use_unscaled_time
        }


class TweenSystem:
    """Tween system utilities."""
    
    @staticmethod
    def generate_unity_tween_manager() -> str:
        """Generate Unity tween manager using DOTween-style API."""
        return '''using UnityEngine;
using System;
using System.Collections;
using System.Collections.Generic;

public enum TweenEase
{
    Linear,
    EaseInQuad, EaseOutQuad, EaseInOutQuad,
    EaseInCubic, EaseOutCubic, EaseInOutCubic,
    EaseInElastic, EaseOutElastic, EaseInOutElastic,
    EaseInBounce, EaseOutBounce, EaseInOutBounce,
    EaseInBack, EaseOutBack, EaseInOutBack
}

public enum TweenLoop
{
    None, Restart, Yoyo, Incremental
}

public class TweenManager : MonoBehaviour
{
    private static TweenManager instance;
    private List<Tween> activeTweens = new List<Tween>();
    
    public static TweenManager Instance
    {
        get
        {
            if (instance == null)
            {
                var go = new GameObject("TweenManager");
                instance = go.AddComponent<TweenManager>();
                DontDestroyOnLoad(go);
            }
            return instance;
        }
    }
    
    private void Update()
    {
        float deltaTime = Time.deltaTime;
        
        for (int i = activeTweens.Count - 1; i >= 0; i--)
        {
            if (!activeTweens[i].Update(deltaTime))
            {
                activeTweens.RemoveAt(i);
            }
        }
    }
    
    public Tween TweenPosition(Transform target, Vector3 endValue, float duration)
    {
        var tween = new Tween(target, endValue, duration, TweenType.Position);
        activeTweens.Add(tween);
        return tween;
    }
    
    public Tween TweenScale(Transform target, Vector3 endValue, float duration)
    {
        var tween = new Tween(target, endValue, duration, TweenType.Scale);
        activeTweens.Add(tween);
        return tween;
    }
    
    public Tween TweenRotation(Transform target, Vector3 endValue, float duration)
    {
        var tween = new Tween(target, endValue, duration, TweenType.Rotation);
        activeTweens.Add(tween);
        return tween;
    }
    
    public Tween TweenAlpha(CanvasGroup target, float endValue, float duration)
    {
        var tween = new Tween(target, endValue, duration, TweenType.Alpha);
        activeTweens.Add(tween);
        return tween;
    }
}

public enum TweenType { Position, Scale, Rotation, Alpha }

public class Tween
{
    private Transform transformTarget;
    private CanvasGroup canvasGroupTarget;
    private Vector3 startVectorValue;
    private Vector3 endVectorValue;
    private float startFloatValue;
    private float endFloatValue;
    private float duration;
    private float elapsed;
    private TweenType type;
    private TweenEase ease = TweenEase.Linear;
    private TweenLoop loop = TweenLoop.None;
    private int loops = 0;
    private int currentLoop = 0;
    private float delay = 0;
    private float delayElapsed = 0;
    private bool useUnscaledTime = false;
    
    private Action onComplete;
    private Action onUpdate;
    private Action onStart;
    
    public Tween(Transform target, Vector3 endValue, float duration, TweenType type)
    {
        this.transformTarget = target;
        this.endVectorValue = endValue;
        this.duration = duration;
        this.type = type;
        
        switch (type)
        {
            case TweenType.Position: startVectorValue = target.position; break;
            case TweenType.Scale: startVectorValue = target.localScale; break;
            case TweenType.Rotation: startVectorValue = target.eulerAngles; break;
        }
    }
    
    public Tween(CanvasGroup target, float endValue, float duration, TweenType type)
    {
        this.canvasGroupTarget = target;
        this.endFloatValue = endValue;
        this.duration = duration;
        this.type = type;
        this.startFloatValue = target.alpha;
    }
    
    public Tween SetEase(TweenEase easeType)
    {
        ease = easeType;
        return this;
    }
    
    public Tween SetLoop(TweenLoop loopType, int loopCount = -1)
    {
        loop = loopType;
        loops = loopCount;
        return this;
    }
    
    public Tween SetDelay(float delayTime)
    {
        delay = delayTime;
        return this;
    }
    
    public Tween OnComplete(Action callback)
    {
        onComplete = callback;
        return this;
    }
    
    public Tween OnUpdate(Action callback)
    {
        onUpdate = callback;
        return this;
    }
    
    public Tween OnStart(Action callback)
    {
        onStart = callback;
        return this;
    }
    
    public bool Update(float deltaTime)
    {
        if (delayElapsed < delay)
        {
            delayElapsed += deltaTime;
            return true;
        }
        
        if (elapsed == 0 && onStart != null)
            onStart.Invoke();
        
        elapsed += deltaTime;
        float t = Mathf.Clamp01(elapsed / duration);
        float easedT = ApplyEase(t, ease);
        
        ApplyValue(easedT);
        
        onUpdate?.Invoke();
        
        if (t >= 1f)
        {
            if (loop != TweenLoop.None && (loops < 0 || currentLoop < loops))
            {
                currentLoop++;
                elapsed = 0;
                
                if (loop == TweenLoop.Yoyo)
                {
                    var temp = startVectorValue;
                    startVectorValue = endVectorValue;
                    endVectorValue = temp;
                }
                else if (loop == TweenLoop.Incremental)
                {
                    startVectorValue = endVectorValue;
                    endVectorValue += (endVectorValue - startVectorValue);
                }
                
                return true;
            }
            
            onComplete?.Invoke();
            return false;
        }
        
        return true;
    }
    
    private void ApplyValue(float t)
    {
        if (transformTarget != null)
        {
            Vector3 value = Vector3.LerpUnclamped(startVectorValue, endVectorValue, t);
            
            switch (type)
            {
                case TweenType.Position: transformTarget.position = value; break;
                case TweenType.Scale: transformTarget.localScale = value; break;
                case TweenType.Rotation: transformTarget.eulerAngles = value; break;
            }
        }
        else if (canvasGroupTarget != null)
        {
            canvasGroupTarget.alpha = Mathf.LerpUnclamped(startFloatValue, endFloatValue, t);
        }
    }
    
    private float ApplyEase(float t, TweenEase easeType)
    {
        switch (easeType)
        {
            case TweenEase.Linear: return t;
            case TweenEase.EaseInQuad: return t * t;
            case TweenEase.EaseOutQuad: return 1 - (1 - t) * (1 - t);
            case TweenEase.EaseInOutQuad: return t < 0.5f ? 2 * t * t : 1 - Mathf.Pow(-2 * t + 2, 2) / 2;
            case TweenEase.EaseInCubic: return t * t * t;
            case TweenEase.EaseOutCubic: return 1 - Mathf.Pow(1 - t, 3);
            case TweenEase.EaseInElastic: return ElasticEaseIn(t);
            case TweenEase.EaseOutElastic: return ElasticEaseOut(t);
            case TweenEase.EaseInBounce: return BounceEaseIn(t);
            case TweenEase.EaseOutBounce: return BounceEaseOut(t);
            case TweenEase.EaseInBack: return BackEaseIn(t);
            case TweenEase.EaseOutBack: return BackEaseOut(t);
            default: return t;
        }
    }
    
    private float ElasticEaseIn(float t) => Mathf.Sin(13 * Mathf.PI / 2 * t) * Mathf.Pow(2, 10 * (t - 1));
    private float ElasticEaseOut(float t) => Mathf.Sin(-13 * Mathf.PI / 2 * (t + 1)) * Mathf.Pow(2, -10 * t) + 1;
    private float BounceEaseIn(float t) => 1 - BounceEaseOut(1 - t);
    private float BounceEaseOut(float t)
    {
        if (t < 1 / 2.75f) return 7.5625f * t * t;
        if (t < 2 / 2.75f) return 7.5625f * (t -= 1.5f / 2.75f) * t + 0.75f;
        if (t < 2.5 / 2.75f) return 7.5625f * (t -= 2.25f / 2.75f) * t + 0.9375f;
        return 7.5625f * (t -= 2.625f / 2.75f) * t + 0.984375f;
    }
    private float BackEaseIn(float t) => t * t * (2.70158f * t - 1.70158f);
    private float BackEaseOut(float t) => 1 - BackEaseIn(1 - t);
}
'''
    
    @staticmethod
    def generate_godot_tween_manager() -> str:
        """Generate Godot tween manager."""
        return '''extends Node

## Tween Manager - Wrapper around Godot's built-in Tween

var tweens: Dictionary = {}

func create_tween(target: Node, name: String = "") -> Tween:
    var tween = create_tween()
    
    if name.is_empty():
        name = str(tweens.size())
    
    tweens[name] = tween
    
    tween.finished.connect(func(): _on_tween_finished(name))
    
    return tween

func tween_property(target: Node, property: String, final_val, duration: float, 
                   ease_type: int = Tween.EASE_IN_OUT, trans_type: int = Tween.TRANS_LINEAR) -> Tween:
    var tween = create_tween()
    tween.set_ease(ease_type)
    tween.set_trans(trans_type)
    tween.tween_property(target, property, final_val, duration)
    return tween

func tween_position(target: Node3D, end_position: Vector3, duration: float,
                   ease_type: int = Tween.EASE_IN_OUT, trans_type: int = Tween.TRANS_LINEAR) -> Tween:
    return tween_property(target, "position", end_position, duration, ease_type, trans_type)

func tween_scale(target: Node3D, end_scale: Vector3, duration: float,
                ease_type: int = Tween.EASE_IN_OUT, trans_type: int = Tween.TRANS_LINEAR) -> Tween:
    return tween_property(target, "scale", end_scale, duration, ease_type, trans_type)

func tween_rotation(target: Node3D, end_rotation: Vector3, duration: float,
                   ease_type: int = Tween.EASE_IN_OUT, trans_type: int = Tween.TRANS_LINEAR) -> Tween:
    return tween_property(target, "rotation", end_rotation, duration, ease_type, trans_type)

func tween_modulate(target: CanvasItem, end_color: Color, duration: float,
                   ease_type: int = Tween.EASE_IN_OUT, trans_type: int = Tween.TRANS_LINEAR) -> Tween:
    return tween_property(target, "modulate", end_color, duration, ease_type, trans_type)

func kill_tween(name: String):
    if tweens.has(name):
        var tween = tweens[name]
        if is_instance_valid(tween):
            tween.kill()
        tweens.erase(name)

func kill_all_tweens():
    for name in tweens.keys():
        kill_tween(name)
    tweens.clear()

func _on_tween_finished(name: String):
    tweens.erase(name)

# Common tween presets
func fade_in(target: CanvasItem, duration: float = 0.3) -> Tween:
    target.modulate.a = 0
    return tween_modulate(target, Color(1, 1, 1, 1), duration, Tween.EASE_OUT, Tween.TRANS_QUAD)

func fade_out(target: CanvasItem, duration: float = 0.3) -> Tween:
    return tween_modulate(target, Color(1, 1, 1, 0), duration, Tween.EASE_IN, Tween.TRANS_QUAD)

func scale_bounce(target: Node3D, original_scale: Vector3, intensity: float = 1.2, duration: float = 0.3) -> Tween:
    var tween = create_tween()
    tween.set_ease(Tween.EASE_OUT)
    tween.set_trans(Tween.TRANS_BACK)
    tween.tween_property(target, "scale", original_scale * intensity, duration * 0.5)
    tween.tween_property(target, "scale", original_scale, duration * 0.5)
    return tween

func shake(target: Node3D, intensity: float = 0.1, duration: float = 0.5) -> Tween:
    var tween = create_tween()
    var original_pos = target.position
    
    for i in range(10):
        var offset = Vector3(
            randf_range(-intensity, intensity),
            randf_range(-intensity, intensity),
            0
        )
        tween.tween_property(target, "position", original_pos + offset, duration / 10)
    
    tween.tween_property(target, "position", original_pos, duration / 10)
    return tween
'''
    
    @staticmethod
    def generate_easing_functions_unity() -> str:
        """Generate standalone easing functions for Unity."""
        return '''using UnityEngine;

public static class EasingFunctions
{
    public static float Linear(float t) => t;
    
    public static float EaseInQuad(float t) => t * t;
    public static float EaseOutQuad(float t) => 1 - (1 - t) * (1 - t);
    public static float EaseInOutQuad(float t) => t < 0.5f ? 2 * t * t : 1 - Mathf.Pow(-2 * t + 2, 2) / 2;
    
    public static float EaseInCubic(float t) => t * t * t;
    public static float EaseOutCubic(float t) => 1 - Mathf.Pow(1 - t, 3);
    public static float EaseInOutCubic(float t) => t < 0.5f ? 4 * t * t * t : 1 - Mathf.Pow(-2 * t + 2, 3) / 2;
    
    public static float EaseInQuart(float t) => t * t * t * t;
    public static float EaseOutQuart(float t) => 1 - Mathf.Pow(1 - t, 4);
    public static float EaseInOutQuart(float t) => t < 0.5f ? 8 * t * t * t * t : 1 - Mathf.Pow(-2 * t + 2, 4) / 2;
    
    public static float EaseInSine(float t) => 1 - Mathf.Cos(t * Mathf.PI / 2);
    public static float EaseOutSine(float t) => Mathf.Sin(t * Mathf.PI / 2);
    public static float EaseInOutSine(float t) => -(Mathf.Cos(Mathf.PI * t) - 1) / 2;
    
    public static float EaseInExpo(float t) => t == 0 ? 0 : Mathf.Pow(2, 10 * (t - 1));
    public static float EaseOutExpo(float t) => t == 1 ? 1 : 1 - Mathf.Pow(2, -10 * t);
    public static float EaseInOutExpo(float t)
    {
        if (t == 0) return 0;
        if (t == 1) return 1;
        return t < 0.5f ? Mathf.Pow(2, 20 * t - 10) / 2 : (2 - Mathf.Pow(2, -20 * t + 10)) / 2;
    }
    
    public static float EaseInCirc(float t) => 1 - Mathf.Sqrt(1 - Mathf.Pow(t, 2));
    public static float EaseOutCirc(float t) => Mathf.Sqrt(1 - Mathf.Pow(t - 1, 2));
    public static float EaseInOutCirc(float t)
    {
        return t < 0.5f 
            ? (1 - Mathf.Sqrt(1 - Mathf.Pow(2 * t, 2))) / 2 
            : (Mathf.Sqrt(1 - Mathf.Pow(-2 * t + 2, 2)) + 1) / 2;
    }
    
    public static float EaseInBack(float t)
    {
        const float c1 = 1.70158f;
        const float c3 = c1 + 1;
        return c3 * t * t * t - c1 * t * t;
    }
    
    public static float EaseOutBack(float t)
    {
        const float c1 = 1.70158f;
        const float c3 = c1 + 1;
        return 1 + c3 * Mathf.Pow(t - 1, 3) + c1 * Mathf.Pow(t - 1, 2);
    }
    
    public static float EaseInOutBack(float t)
    {
        const float c1 = 1.70158f;
        const float c2 = c1 * 1.525f;
        return t < 0.5f
            ? (Mathf.Pow(2 * t, 2) * ((c2 + 1) * 2 * t - c2)) / 2
            : (Mathf.Pow(2 * t - 2, 2) * ((c2 + 1) * (t * 2 - 2) + c2) + 2) / 2;
    }
    
    public static float EaseInElastic(float t)
    {
        const float c4 = (2 * Mathf.PI) / 3;
        if (t == 0) return 0;
        if (t == 1) return 1;
        return -Mathf.Pow(2, 10 * t - 10) * Mathf.Sin((t * 10 - 10.75f) * c4);
    }
    
    public static float EaseOutElastic(float t)
    {
        const float c4 = (2 * Mathf.PI) / 3;
        if (t == 0) return 0;
        if (t == 1) return 1;
        return Mathf.Pow(2, -10 * t) * Mathf.Sin((t * 10 - 0.75f) * c4) + 1;
    }
    
    public static float EaseInOutElastic(float t)
    {
        const float c5 = (2 * Mathf.PI) / 4.5f;
        if (t == 0) return 0;
        if (t == 1) return 1;
        return t < 0.5f
            ? -(Mathf.Pow(2, 20 * t - 10) * Mathf.Sin((20 * t - 11.125f) * c5)) / 2
            : (Mathf.Pow(2, -20 * t + 10) * Mathf.Sin((20 * t - 11.125f) * c5)) / 2 + 1;
    }
    
    public static float EaseInBounce(float t) => 1 - EaseOutBounce(1 - t);
    
    public static float EaseOutBounce(float t)
    {
        const float n1 = 7.5625f;
        const float d1 = 2.75f;
        
        if (t < 1 / d1)
            return n1 * t * t;
        else if (t < 2 / d1)
            return n1 * (t -= 1.5f / d1) * t + 0.75f;
        else if (t < 2.5 / d1)
            return n1 * (t -= 2.25f / d1) * t + 0.9375f;
        else
            return n1 * (t -= 2.625f / d1) * t + 0.984375f;
    }
    
    public static float EaseInOutBounce(float t)
    {
        return t < 0.5f
            ? (1 - EaseOutBounce(1 - 2 * t)) / 2
            : (1 + EaseOutBounce(2 * t - 1)) / 2;
    }
}
'''
