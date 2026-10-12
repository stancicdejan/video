"""Render context and the frame compositor.

A scene is a module exposing:
    START: float        global start time (s), inclusive
    END: float          global end time (s), exclusive
    LAYER: int          z-order (higher draws on top); default 0
    def render(ctx, t, R): draw the scene at global time t (design space)

The compositor clears the frame to the brand background, renders every scene
whose [START, END) window contains t (sorted by LAYER, then START), then
applies global post FX in numpy.
"""
from dataclasses import dataclass, field

import numpy as np

from . import draw

QUALITY = {
    # name: (px_w, px_h)
    "preview": (854, 480),
    "720p": (1280, 720),
    "full": (1920, 1080),
}


@dataclass
class RenderContext:
    quality: str = "preview"
    fps: int = 30
    duration: float = 15.0
    lang: str = "sr"
    motion_blur: int = 1          # sub-frames per frame (1 = off)
    shutter: float = 0.5          # fraction of a frame interval the shutter is open
    grain: float = 0.022
    vignette: float = 0.22
    copy: dict = field(default_factory=dict)
    stats: dict = field(default_factory=dict)
    frame: int = 0                # current frame index (set by renderer)
    debug: bool = False

    def __post_init__(self):
        self.px_w, self.px_h = QUALITY[self.quality]
        self.scale = self.px_h / draw.DESIGN_H
        self.W, self.H = draw.DESIGN_W, draw.DESIGN_H
        self.frames = int(round(self.duration * self.fps))

    def t(self, key):
        """Localized copy lookup: R.t('hero.title')."""
        node = self.copy
        for part in key.split("."):
            node = node[part]
        if isinstance(node, dict):
            return node.get(self.lang, node.get("sr"))
        return node

    @property
    def dt(self):
        return 1.0 / self.fps


class Compositor:
    def __init__(self, scenes, R, background=(1, 1, 1, 1), post=None):
        self.scenes = sorted(scenes, key=lambda s: (getattr(s, "LAYER", 0), s.START))
        self.R = R
        self.background = background
        self.post = post  # callable(rgb_float_array, t, R) -> array

    def active(self, t):
        return [s for s in self.scenes if s.START <= t < s.END]

    def render_raw(self, t):
        """Render all scenes at time t -> float32 HxWx3 RGB array (0..1)."""
        R = self.R
        surf = draw.new_surface(R.px_w, R.px_h)
        ctx = draw.design_context(surf, R.scale)
        draw.paint(ctx, self.background)
        for scene in self.active(t):
            ctx.save()
            scene.render(ctx, t, R)
            ctx.restore()
        arr = draw.surface_to_array(surf)
        rgb = arr[..., [2, 1, 0]].astype(np.float32) / 255.0
        return rgb

    def render_frame(self, index):
        R = self.R
        R.frame = index
        t0 = index / R.fps
        n = max(1, R.motion_blur)
        if n == 1:
            acc = self.render_raw(t0)
        else:
            acc = None
            span = R.shutter / R.fps
            for k in range(n):
                # Centred shutter: samples spread around the frame time.
                tk = t0 + (k / (n - 1) - 0.5) * span if n > 1 else t0
                tk = min(max(tk, 0.0), R.duration - 1e-6)
                img = self.render_raw(tk)
                acc = img if acc is None else acc + img
            acc /= n
        if self.post:
            acc = self.post(acc, t0, R)
        return (np.clip(acc, 0, 1) * 255 + 0.5).astype(np.uint8)
