"""Easing curves, interpolation and keyframe helpers.

All easing functions map a progress value in [0, 1] to an eased value.
Values outside [0, 1] are clamped first, so callers can pass raw progress.
"""
import math


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_pt(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def progress(t, start, duration):
    """Linear 0..1 progress of time t through [start, start + duration]."""
    if duration <= 0:
        return 1.0 if t >= start else 0.0
    return clamp((t - start) / duration)


def remap(v, a0, a1, b0=0.0, b1=1.0, clamp_out=True):
    if a1 == a0:
        return b1 if v >= a1 else b0
    p = (v - a0) / (a1 - a0)
    if clamp_out:
        p = clamp(p)
    return b0 + (b1 - b0) * p


# --- classic Penner curves -------------------------------------------------

def linear(t):
    return clamp(t)


def in_sine(t):
    t = clamp(t)
    return 1 - math.cos(t * math.pi / 2)


def out_sine(t):
    t = clamp(t)
    return math.sin(t * math.pi / 2)


def in_out_sine(t):
    t = clamp(t)
    return -(math.cos(math.pi * t) - 1) / 2


def in_quad(t):
    t = clamp(t)
    return t * t


def out_quad(t):
    t = clamp(t)
    return 1 - (1 - t) ** 2


def in_out_quad(t):
    t = clamp(t)
    return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2


def in_cubic(t):
    t = clamp(t)
    return t ** 3


def out_cubic(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def in_out_cubic(t):
    t = clamp(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def in_quart(t):
    t = clamp(t)
    return t ** 4


def out_quart(t):
    t = clamp(t)
    return 1 - (1 - t) ** 4


def in_out_quart(t):
    t = clamp(t)
    return 8 * t ** 4 if t < 0.5 else 1 - (-2 * t + 2) ** 4 / 2


def in_quint(t):
    t = clamp(t)
    return t ** 5


def out_quint(t):
    t = clamp(t)
    return 1 - (1 - t) ** 5


def in_out_quint(t):
    t = clamp(t)
    return 16 * t ** 5 if t < 0.5 else 1 - (-2 * t + 2) ** 5 / 2


def in_expo(t):
    t = clamp(t)
    return 0.0 if t == 0 else 2 ** (10 * t - 10)


def out_expo(t):
    t = clamp(t)
    return 1.0 if t == 1 else 1 - 2 ** (-10 * t)


def in_out_expo(t):
    t = clamp(t)
    if t == 0 or t == 1:
        return t
    return 2 ** (20 * t - 10) / 2 if t < 0.5 else (2 - 2 ** (-20 * t + 10)) / 2


def in_circ(t):
    t = clamp(t)
    return 1 - math.sqrt(1 - t * t)


def out_circ(t):
    t = clamp(t)
    return math.sqrt(1 - (t - 1) ** 2)


def in_out_circ(t):
    t = clamp(t)
    if t < 0.5:
        return (1 - math.sqrt(1 - (2 * t) ** 2)) / 2
    return (math.sqrt(1 - (-2 * t + 2) ** 2) + 1) / 2


def in_back(t, s=1.70158):
    t = clamp(t)
    return (s + 1) * t ** 3 - s * t * t


def out_back(t, s=1.70158):
    t = clamp(t)
    return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2


def in_out_back(t, s=1.70158):
    t = clamp(t)
    c = s * 1.525
    if t < 0.5:
        return ((2 * t) ** 2 * ((c + 1) * 2 * t - c)) / 2
    return ((2 * t - 2) ** 2 * ((c + 1) * (t * 2 - 2) + c) + 2) / 2


def out_elastic(t):
    t = clamp(t)
    if t == 0 or t == 1:
        return t
    c4 = (2 * math.pi) / 3
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * c4) + 1


def out_bounce(t):
    t = clamp(t)
    n1, d1 = 7.5625, 2.75
    if t < 1 / d1:
        return n1 * t * t
    if t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    if t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    t -= 2.625 / d1
    return n1 * t * t + 0.984375


def spring(t, damping=0.42, freq=4.2):
    """Damped spring settling at 1 with natural overshoot.

    damping: 0..1 (lower = bouncier). freq: oscillations over the duration.
    """
    t = clamp(t)
    if t >= 1:
        return 1.0
    w = 2 * math.pi * freq
    zeta = clamp(damping, 0.01, 0.99)
    wd = w * math.sqrt(1 - zeta * zeta)
    decay = math.exp(-zeta * w * t)
    v = 1 - decay * (math.cos(wd * t) + (zeta * w / wd) * math.sin(wd * t))
    # Force an exact landing at t=1 without a visible jump.
    tail = smoothstep(0.85, 1.0, t)
    return lerp(v, 1.0, tail)


def smoothstep(e0, e1, x):
    x = clamp((x - e0) / (e1 - e0)) if e1 != e0 else (1.0 if x >= e1 else 0.0)
    return x * x * (3 - 2 * x)


def bezier(x1, y1, x2, y2):
    """CSS-style cubic-bezier easing factory, e.g. bezier(.16, 1, .3, 1)."""
    def sample(a1, a2, u):
        return 3 * a1 * u * (1 - u) ** 2 + 3 * a2 * u * u * (1 - u) + u ** 3

    def fn(t):
        t = clamp(t)
        lo, hi = 0.0, 1.0
        u = t
        for _ in range(28):
            x = sample(x1, x2, u)
            if abs(x - t) < 1e-5:
                break
            if x < t:
                lo = u
            else:
                hi = u
            u = (lo + hi) / 2
        return sample(y1, y2, u)
    return fn


# The site's Tailwind "ease-out" (cubic-bezier(0, 0, 0.2, 1)).
site_ease_out = bezier(0.0, 0.0, 0.2, 1.0)
# A punchy "motion designer" ease: fast attack, long silky settle.
snappy = bezier(0.16, 1.0, 0.3, 1.0)
# Smooth anticipation-free in-out for camera moves.
camera = bezier(0.65, 0.0, 0.35, 1.0)

EASINGS = {
    name: fn for name, fn in globals().items()
    if callable(fn) and (name.startswith(("in_", "out_")) or name in ("linear",))
}
EASINGS.update(spring=spring, site_ease_out=site_ease_out, snappy=snappy, camera=camera)


def get(name_or_fn):
    if callable(name_or_fn):
        return name_or_fn
    return EASINGS[name_or_fn]


def anim(t, start, duration, a=0.0, b=1.0, ease=out_cubic):
    """Animate a value from a to b over [start, start + duration]."""
    return lerp(a, b, get(ease)(progress(t, start, duration)))


def keyframes(t, frames, default_ease=in_out_cubic):
    """Piecewise interpolation.

    frames: list of (time, value) or (time, value, ease) sorted by time. The
    ease on a keyframe shapes the segment that ENDS at that keyframe. Values
    can be numbers or tuples of numbers.
    """
    if not frames:
        raise ValueError("no keyframes")
    if t <= frames[0][0]:
        return frames[0][1]
    for i in range(1, len(frames)):
        t1 = frames[i][0]
        if t <= t1:
            t0, v0 = frames[i - 1][0], frames[i - 1][1]
            v1 = frames[i][1]
            ease = get(frames[i][2]) if len(frames[i]) > 2 else default_ease
            p = ease((t - t0) / (t1 - t0) if t1 > t0 else 1.0)
            if isinstance(v0, (tuple, list)):
                return tuple(lerp(a, b, p) for a, b in zip(v0, v1))
            return lerp(v0, v1, p)
    return frames[-1][1]


def stagger(t, start, index, step, duration, ease=out_cubic):
    """Eased 0..1 progress for the index-th item of a staggered sequence."""
    return get(ease)(progress(t, start + index * step, duration))


def pulse(t, start, duration):
    """0 -> 1 -> 0 bump (sine) over the window, 0 elsewhere."""
    p = progress(t, start, duration)
    if p <= 0 or p >= 1:
        return 0.0
    return math.sin(math.pi * p)


def window(t, t_in, t_out, fade_in=0.2, fade_out=0.2, ease_in=out_cubic, ease_out=in_cubic):
    """Opacity envelope: fades in at t_in, holds, fades out ending at t_out."""
    a = get(ease_in)(progress(t, t_in, fade_in))
    b = 1 - get(ease_out)(progress(t, t_out - fade_out, fade_out))
    return min(a, b)
