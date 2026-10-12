"""Post effects (numpy, applied to the whole frame) and cairo light effects."""
import math
from functools import lru_cache

import numpy as np

from . import draw
from .color import rgba


@lru_cache(maxsize=4)
def _vignette_mask(w, h, strength):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (x - w / 2) / (w / 2)
    ny = (y - h / 2) / (h / 2)
    d = np.sqrt(nx * nx * 0.85 + ny * ny * 1.0)
    m = 1.0 - strength * np.clip((d - 0.55) / 0.85, 0, 1) ** 1.6
    return m[..., None].astype(np.float32)


def vignette(rgb, strength):
    if strength <= 0:
        return rgb
    h, w = rgb.shape[:2]
    return rgb * _vignette_mask(w, h, round(strength, 3))


@lru_cache(maxsize=2)
def _grain_bank(w, h, n=8):
    rs = np.random.RandomState(7)
    bank = []
    for _ in range(n):
        g = rs.normal(0, 1, (h, w)).astype(np.float32)
        # Soften to film-like grain clumps (2x2 box blur).
        g = (g + np.roll(g, 1, 0) + np.roll(g, 1, 1) + np.roll(np.roll(g, 1, 0), 1, 1)) / 2.0
        bank.append(g[..., None])
    return bank


def grain(rgb, amount, frame):
    """Luma-weighted film grain; strongest in mid-tones."""
    if amount <= 0:
        return rgb
    h, w = rgb.shape[:2]
    g = _grain_bank(w, h)[frame % 8]
    lum = rgb.mean(-1, keepdims=True)
    weight = 4.0 * lum * (1.0 - lum)
    return rgb + g * amount * (0.35 + 0.65 * weight)


def chromatic_split(rgb, px):
    """Shift R and B channels horizontally in opposite directions."""
    if abs(px) < 0.25:
        return rgb
    s = int(round(px))
    out = rgb.copy()
    out[..., 0] = np.roll(rgb[..., 0], s, axis=1)
    out[..., 2] = np.roll(rgb[..., 2], -s, axis=1)
    return out


def default_post(rgb, t, R):
    rgb = vignette(rgb, R.vignette)
    rgb = grain(rgb, R.grain, R.frame)
    return rgb


# --- cairo light effects (drawn inside scenes) -------------------------------

def light_leak(ctx, cx, cy, radius, color=(1.0, 0.78, 0.38), intensity=0.6, operator="screen"):
    """Soft warm light bloom (sun flare / light leak), screen-blended."""
    if intensity <= 0:
        return
    c = rgba(color)
    g = draw.radial_gradient(cx, cy, radius, [
        (0.0, (c[0], c[1], c[2], intensity)),
        (0.25, (c[0], c[1], c[2], intensity * 0.55)),
        (0.6, (c[0], c[1], c[2], intensity * 0.15)),
        (1.0, (c[0], c[1], c[2], 0.0)),
    ])
    ctx.save()
    ctx.set_operator(draw.OPERATORS[operator])
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()


def sun_rays(ctx, cx, cy, length, count=9, spread=70.0, angle=35.0, width=0.06,
             color=(1.0, 0.86, 0.55), intensity=0.25, phase=0.0):
    """Volumetric-looking god rays fanning from (cx, cy). angle = centre dir (deg)."""
    if intensity <= 0:
        return
    c = rgba(color)
    ctx.save()
    ctx.set_operator(draw.OPERATORS["screen"])
    for i in range(count):
        f = i / max(count - 1, 1)
        a = math.radians(angle - spread / 2 + spread * f + 3.0 * math.sin(phase + i * 1.7))
        w = width * (0.6 + 0.8 * ((i * 37) % 7) / 7.0)
        a0, a1 = a - w / 2, a + w / 2
        L = length * (0.7 + 0.3 * ((i * 53) % 5) / 5.0)
        g = draw.radial_gradient(cx, cy, L, [
            (0.0, (c[0], c[1], c[2], intensity)),
            (0.5, (c[0], c[1], c[2], intensity * 0.35)),
            (1.0, (c[0], c[1], c[2], 0.0)),
        ])
        ctx.new_path()
        ctx.move_to(cx, cy)
        ctx.line_to(cx + L * math.cos(a0), cy + L * math.sin(a0))
        ctx.line_to(cx + L * math.cos(a1), cy + L * math.sin(a1))
        ctx.close_path()
        ctx.set_source(g)
        ctx.fill()
    ctx.restore()


def particles(ctx, seed, count, t, area, color=(1, 1, 1), size=(1.5, 4.0), drift=(10.0, -25.0),
              alpha=0.6, twinkle=True):
    """Deterministic floating dust/pollen motes in a rect area=(x, y, w, h)."""
    rs = np.random.RandomState(seed)
    xs = rs.uniform(0, 1, count)
    ys = rs.uniform(0, 1, count)
    ss = rs.uniform(size[0], size[1], count)
    sp = rs.uniform(0.5, 1.5, count)
    ph = rs.uniform(0, 2 * math.pi, count)
    x0, y0, w, h = area
    c = rgba(color)
    for i in range(count):
        x = x0 + ((xs[i] * w + drift[0] * sp[i] * t) % w)
        y = y0 + ((ys[i] * h + drift[1] * sp[i] * t) % h)
        a = alpha * (0.5 + 0.5 * math.sin(t * 2.0 * sp[i] + ph[i])) if twinkle else alpha
        ctx.set_source_rgba(c[0], c[1], c[2], c[3] * a)
        draw.circle(ctx, x, y, ss[i])
        ctx.fill()


def camera_shake(t, amp=6.0, freq=9.0, seed=0.0):
    """Smooth pseudo-random (dx, dy, rot_deg) for handheld/impact shake."""
    dx = amp * (math.sin(t * freq * 1.0 + seed) * 0.6 + math.sin(t * freq * 2.3 + seed * 1.7) * 0.4)
    dy = amp * (math.sin(t * freq * 1.3 + seed * 0.7) * 0.6 + math.sin(t * freq * 2.9 + seed * 2.1) * 0.4)
    rot = amp * 0.04 * math.sin(t * freq * 0.9 + seed * 1.3)
    return dx, dy, rot
