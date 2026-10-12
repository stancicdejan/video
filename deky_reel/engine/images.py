"""Still-image layers: loading, gentle natural grading, resolution-aware
caching, cover-fit Ken Burns drawing, and pre-blurred variants."""
import math
import os

import cairo
import numpy as np
from PIL import Image, ImageFilter

from .draw import array_to_surface, rounded_rect

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))

_SRC = {}
_CACHE = {}

# A light, natural grade: a touch of warmth and density, no stylized looks.
NATURAL = dict(exposure=0.0, contrast=1.04, saturation=1.04, warmth=0.03, lift=0.0, gamma=1.0)


def resolve(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def _source(path):
    im = _SRC.get(path)
    if im is None:
        im = Image.open(resolve(path))
        im = im.convert("RGBA")
        _SRC[path] = im
    return im


def size(path):
    return _source(path).size


def _grade(arr, g):
    """arr: float32 RGB 0..1. Applies a gentle grade."""
    if not g:
        return arr
    out = arr
    exp = g.get("exposure", 0.0)
    if exp:
        out = out * (2.0 ** exp)
    gamma = g.get("gamma", 1.0)
    if gamma != 1.0:
        out = np.clip(out, 0, None) ** (1.0 / gamma)
    con = g.get("contrast", 1.0)
    if con != 1.0:
        out = (out - 0.5) * con + 0.5
    sat = g.get("saturation", 1.0)
    if sat != 1.0:
        lum = (out[..., 0:1] * 0.2126 + out[..., 1:2] * 0.7152 + out[..., 2:3] * 0.0722)
        out = lum + (out - lum) * sat
    warm = g.get("warmth", 0.0)
    if warm:
        out = out + np.array([warm, warm * 0.35, -warm], np.float32)
    tint = g.get("tint", 0.0)  # + green / - magenta
    if tint:
        out = out + np.array([-tint * 0.5, tint, -tint * 0.5], np.float32)
    lift = g.get("lift", 0.0)
    if lift:
        lc = np.array(g.get("lift_color", (0.10, 0.18, 0.12)), np.float32)
        out = out + (1.0 - np.clip(out, 0, 1)) * lc * lift
    return np.clip(out, 0.0, 1.0)


def _grade_key(g):
    return tuple(sorted((k, tuple(v) if isinstance(v, (list, tuple)) else v) for k, v in (g or {}).items()))


def _bucket(px):
    return int(2 ** (math.ceil(math.log2(max(px, 8)) * 4) / 4))


def get_surface(path, device_w, grade=None, blur=0.0):
    """Cached cairo surface of the image resampled to ~device_w px wide.

    blur is in device px of the cached surface. Returns (surface, w, h).
    """
    src = _source(path)
    bw = min(_bucket(device_w), src.width)
    bkey = round(blur * 2) / 2
    key = (path, bw, _grade_key(grade), bkey)
    hit = _CACHE.get(key)
    if hit is not None:
        return hit
    bh = max(1, round(src.height * bw / src.width))
    im = src if bw == src.width else src.resize((bw, bh), Image.LANCZOS)
    arr = np.asarray(im).astype(np.float32) / 255.0
    rgb, a = arr[..., :3], arr[..., 3:4]
    rgb = _grade(rgb, grade)
    if bkey > 0:
        tmp = Image.fromarray((np.concatenate([rgb, a], -1) * 255 + 0.5).astype(np.uint8), "RGBA")
        tmp = tmp.filter(ImageFilter.GaussianBlur(bkey))
        arr2 = np.asarray(tmp).astype(np.float32) / 255.0
        rgb, a = arr2[..., :3], arr2[..., 3:4]
    prem = rgb * a
    bgra = np.concatenate([prem[..., 2:3], prem[..., 1:2], prem[..., 0:1], a], -1)
    surf = array_to_surface((bgra * 255 + 0.5).astype(np.uint8))
    hit = (surf, bw, bh)
    _CACHE[key] = hit
    return hit


def cover_transform(iw, ih, x, y, w, h, zoom=1.0, focus=(0.5, 0.5), pan=(0.0, 0.0), clamp=True):
    """Return (tx, ty, s): top-left and scale that cover rect with the image."""
    s = max(w / iw, h / ih) * zoom
    cx, cy = x + w / 2, y + h / 2
    tx = cx - focus[0] * iw * s
    ty = cy - focus[1] * ih * s
    if clamp:
        tx = min(max(tx, x + w - iw * s), x)
        ty = min(max(ty, y + h - ih * s), y)
    return tx + pan[0], ty + pan[1], s


def draw_image(ctx, R, path, x=0.0, y=0.0, w=1920.0, h=1080.0, zoom=1.0,
               focus=(0.5, 0.5), pan=(0.0, 0.0), rot=0.0, alpha=1.0, grade=NATURAL,
               blur=0.0, radius=0.0, clip=True, clamp=True, fit="cover"):
    """Draw an image into a rect with Ken Burns controls.

    zoom >= 1 pushes in; focus is the image point (0..1) kept at rect centre;
    pan offsets in design px; rot rotates about the rect centre (deg);
    blur is in design px; radius rounds the clip rect.
    """
    if alpha <= 0.0:
        return
    iw, ih = size(path)
    if fit == "contain":
        s = min(w / iw, h / ih) * zoom
        tx = x + (w - iw * s) / 2 + pan[0]
        ty = y + (h - ih * s) / 2 + pan[1]
    else:
        tx, ty, s = cover_transform(iw, ih, x, y, w, h, zoom, focus, pan, clamp)
    device_w = iw * s * R.scale
    surf, bw, bh = get_surface(path, device_w, grade, blur * R.scale * (min(device_w, iw) / max(device_w, 1)) if blur else 0.0)
    k = iw * s / bw
    ctx.save()
    if clip:
        ctx.new_path()
        if radius > 0:
            rounded_rect(ctx, x, y, w, h, radius)
        else:
            ctx.rectangle(x, y, w, h)
        ctx.clip()
    if rot:
        ctx.translate(x + w / 2, y + h / 2)
        ctx.rotate(math.radians(rot))
        ctx.translate(-(x + w / 2), -(y + h / 2))
    ctx.translate(tx, ty)
    ctx.scale(k, k)
    ctx.set_source_surface(surf, 0, 0)
    pat = ctx.get_source()
    pat.set_filter(cairo.FILTER_GOOD)
    pat.set_extend(cairo.EXTEND_PAD)
    if alpha < 1.0:
        ctx.paint_with_alpha(alpha)
    else:
        ctx.paint()
    ctx.restore()


def draw_image_at(ctx, R, path, cx, cy, width, rot=0.0, alpha=1.0, grade=None, blur=0.0):
    """Draw a whole image (e.g. a cut-out PNG) centred at (cx, cy), given width."""
    iw, ih = size(path)
    s = width / iw
    h = ih * s
    device_w = width * R.scale
    surf, bw, bh = get_surface(path, device_w, grade, blur * R.scale if blur else 0.0)
    k = width / bw
    ctx.save()
    ctx.translate(cx, cy)
    if rot:
        ctx.rotate(math.radians(rot))
    ctx.translate(-width / 2, -h / 2)
    ctx.scale(k, k)
    ctx.set_source_surface(surf, 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint_with_alpha(alpha) if alpha < 1.0 else ctx.paint()
    ctx.restore()
