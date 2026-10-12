"""The Deky Bike logo split into animatable parts.

Colors come from the gradient logo the client supplied (assets/images/logo.png,
white background); the clean transparency matte comes from the site's logo
(assets/site/logo.png). Both share the exact same geometry (1280x1024), so
we un-blend the client logo against white with the site matte and get a
crisp, transparent, full-color logo.

Parts (source pixel geometry, 1280x1024):
    diamond   - the pointed diamond outline behind the rider
    mountains - the mountain ridge + top bar
    rider     - cyclist + bike
    debris    - the small flying dirt chips
    wordmark  - black serif "DEKY BIKE" (also split per letter: letter0..letter7)
    bar       - lower horizontal bar
    pennant   - the green pennant (tagline removed and in-painted)
    tagline   - "Drive forward. Feel the power" (black)
"""
import os
from functools import lru_cache

import cairo
import numpy as np
from PIL import Image, ImageDraw

from .draw import array_to_surface

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
COLOR_PATH = os.path.join(ROOT, "assets", "images", "logo.png")
MATTE_PATH = os.path.join(ROOT, "assets", "site", "logo.png")

SRC_W, SRC_H = 1280, 1024
# Visible content bounds of the logo in source px.
CONTENT = (217, 128, 1063, 893)  # x0, y0, x1, y1
CONTENT_CX = (CONTENT[0] + CONTENT[2]) / 2
CONTENT_CY = (CONTENT[1] + CONTENT[3]) / 2
CONTENT_W = CONTENT[2] - CONTENT[0]
CONTENT_H = CONTENT[3] - CONTENT[1]

RIDER_POLY = [(728, 128), (760, 132), (790, 165), (770, 190), (752, 205), (772, 245),
              (800, 268), (826, 276), (828, 292), (814, 302), (766, 290), (785, 330),
              (790, 380), (770, 440), (745, 485), (705, 515), (655, 525), (630, 510),
              (612, 488), (590, 492), (560, 505), (505, 540), (470, 530), (452, 500),
              (458, 455), (488, 415), (530, 392), (565, 398), (570, 350), (570, 300),
              (588, 262), (612, 236), (606, 224), (620, 205), (655, 178), (700, 160),
              (708, 140)]

# Mountain ridge silhouette (top edge of the mountains), left to right.
RIDGE = [(217, 556), (268, 553), (330, 522), (352, 526), (380, 500), (395, 497),
         (425, 466), (452, 494), (500, 525), (515, 548), (545, 540), (568, 543),
         (600, 530), (640, 520), (700, 512), (765, 478), (788, 470), (808, 495),
         (830, 500), (860, 522), (875, 515), (915, 500), (965, 520), (1005, 553),
         (1062, 556)]

# Centre line of the diamond outline band (draw-on order: from the lower-left
# corner, up over the top behind the rider, down to the lower-right corner).
DIAMOND_PATH = [(381, 505), (336, 412), (607, 228), (690, 262), (772, 298),
                (944, 412), (865, 527)]
DIAMOND_BAND = 12.0  # stroke width of the band in source px
# The full implied kite the diamond band belongs to (its edges extended):
# apex hidden behind the rider, sides at the band corners, and the lower
# point far below the mountains, which echoes the pennant's point.
DIAMOND_KITE = [(636, 208), (944, 412), (587, 931), (336, 412)]

# Pennant outline (for masks/vector echoes).
PENNANT_POLY = [(315, 700), (965, 700), (922, 771), (792, 785), (640, 892),
                (488, 785), (358, 771)]

# Rows of the horizontal bands.
TOP_BAR_ROWS = (555, 573)
WORD_ROWS = (575, 682)
BAR_ROWS = (682, 701)
PENNANT_ROWS = (700, 895)

ANCHORS = {
    "rider_wheel_rear": (505, 465),
    "rider_wheel_front": (705, 420),
    "rider_center": (640, 330),
    "diamond_top": (690, 250),
    "wordmark_center": (640, 625),
    "pennant_center": (640, 760),
    "tagline_center": (640, 721),
}


def _poly_mask(poly, inside=True):
    im = Image.new("L", (SRC_W, SRC_H), 0)
    ImageDraw.Draw(im).polygon(poly, fill=255)
    m = np.asarray(im) > 127
    return m if inside else ~m


def _below_ridge_mask():
    poly = list(RIDGE) + [(1062, 575), (217, 575)]
    return _poly_mask(poly)


@lru_cache(maxsize=1)
def _base():
    col = np.asarray(Image.open(COLOR_PATH).convert("RGB")).astype(np.float32) / 255.0
    matte = np.asarray(Image.open(MATTE_PATH).convert("RGBA"))[..., 3].astype(np.float32) / 255.0
    a = matte[..., None]
    # Un-blend the white background: c = a*fg + (1-a)*1  =>  fg = (c - (1-a)) / a
    fg = np.where(a > 0.02, (col - (1.0 - a)) / np.maximum(a, 1e-3), col)
    fg = np.clip(fg, 0.0, 1.0)
    return fg, matte


def _small_components(mask, max_size=200):
    """Boolean mask of connected components smaller than max_size px."""
    from collections import deque
    H, W = mask.shape
    seen = np.zeros_like(mask, bool)
    out = np.zeros_like(mask, bool)
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys, xs):
        if seen[y0, x0]:
            continue
        q = deque([(y0, x0)])
        seen[y0, x0] = True
        comp = []
        while q:
            y, x = q.popleft()
            comp.append((y, x))
            if len(comp) > max_size:
                # Large component: finish marking without collecting.
                while q:
                    yy, xx = q.popleft()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        a, b = yy + dy, xx + dx
                        if 0 <= a < H and 0 <= b < W and mask[a, b] and not seen[a, b]:
                            seen[a, b] = True
                            q.append((a, b))
                comp = None
                break
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = y + dy, x + dx
                if 0 <= a < H and 0 <= b < W and mask[a, b] and not seen[a, b]:
                    seen[a, b] = True
                    q.append((a, b))
        if comp:
            for y, x in comp:
                out[y, x] = True
    return out


def _near_polyline(pts, dist):
    """Mask of pixels within `dist` source px of an open polyline."""
    H, W = SRC_H, SRC_W
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    best = np.full((H, W), np.inf, np.float32)
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy or 1.0
        t = np.clip(((xx - x0) * dx + (yy - y0) * dy) / L2, 0, 1)
        d = np.hypot(xx - (x0 + t * dx), yy - (y0 + t * dy))
        best = np.minimum(best, d)
    return best <= dist


def _dilate(m, r=1):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


@lru_cache(maxsize=1)
def part_masks():
    fg, matte = _base()
    H, W = matte.shape
    yy = np.arange(H)[:, None] * np.ones((1, W))
    solid = matte > 0.0
    rider = _poly_mask(RIDER_POLY)
    below = _below_ridge_mask()
    emblem_zone = yy < TOP_BAR_ROWS[1]
    debris = _small_components(solid & emblem_zone & (matte > 0.35) & ~rider, 200)
    debris = _dilate(debris, 1) & solid & ~rider
    masks = {}
    near_diamond = _near_polyline(DIAMOND_PATH, DIAMOND_BAND + 5.0)
    masks["rider"] = rider & solid
    masks["diamond"] = emblem_zone & near_diamond & ~rider & ~debris & solid & (yy < 540)
    masks["mountains"] = emblem_zone & ~masks["diamond"] & ~rider & ~debris & solid
    masks["debris"] = debris
    masks["wordmark"] = (yy >= WORD_ROWS[0]) & (yy < WORD_ROWS[1]) & solid
    masks["bar"] = (yy >= BAR_ROWS[0]) & (yy < BAR_ROWS[1]) & solid
    pen_zone = (yy >= BAR_ROWS[1]) & (yy < PENNANT_ROWS[1])
    lum = fg.mean(-1)
    tag = pen_zone & solid & (lum < 0.22) & (yy < 745)
    masks["tagline"] = _dilate(tag, 1) & pen_zone & solid & (lum < 0.45)
    masks["pennant"] = pen_zone & solid
    return masks


@lru_cache(maxsize=1)
def wordmark_letters():
    """Column spans of the 8 letters of DEKY BIKE (source px)."""
    fg, matte = _base()
    m = part_masks()["wordmark"]
    cols = m.any(0)
    spans, inside, x0 = [], False, 0
    for x in range(SRC_W):
        if cols[x] and not inside:
            inside, x0 = True, x
        elif not cols[x] and inside:
            inside = False
            spans.append((x0, x))
    if inside:
        spans.append((x0, SRC_W))
    # Merge fragments closer than 4px (serifs) to get whole letters.
    merged = []
    for s in spans:
        if merged and s[0] - merged[-1][1] < 4:
            merged[-1] = (merged[-1][0], s[1])
        else:
            merged.append(s)
    return merged


def _rgba_for(name):
    fg, matte = _base()
    masks = part_masks()
    if name.startswith("letter"):
        i = int(name[6:])
        x0, x1 = wordmark_letters()[i]
        m = masks["wordmark"].copy()
        m[:, :x0] = False
        m[:, x1:] = False
    elif name == "all":
        m = matte > 0
    else:
        m = masks[name]
    color = fg.copy()
    alpha = np.where(m, matte, 0.0)
    if name == "pennant":
        # In-paint the tagline: the pennant gradient is vertical, so use the
        # mean of non-text green pixels on each row.
        tag = masks["tagline"]
        rows = np.nonzero(tag.any(1))[0]
        lum = fg.mean(-1)
        for y in range(max(BAR_ROWS[1], rows.min() - 3), rows.max() + 4):
            row = masks["pennant"][y]
            clean = row & ~_dilate(tag, 2)[y] & (lum[y] > 0.35)
            if clean.any():
                color[y, row] = np.median(color[y, clean], axis=0)
        alpha = np.where(m, np.maximum(matte, tag.astype(np.float32)), 0.0)
    return color, alpha


@lru_cache(maxsize=64)
def _part_surface(name, bucket_w):
    color, alpha = _rgba_for(name)
    a = alpha[..., None]
    prem = color * a
    bgra = np.concatenate([prem[..., 2:3], prem[..., 1:2], prem[..., 0:1], a], -1)
    arr = (bgra * 255 + 0.5).astype(np.uint8)
    if bucket_w < SRC_W:
        bh = round(SRC_H * bucket_w / SRC_W)
        # Resample premultiplied data (correct for alpha edges).
        im = Image.fromarray(arr, "RGBA").resize((bucket_w, bh), Image.LANCZOS)
        arr = np.asarray(im)
    return array_to_surface(np.ascontiguousarray(arr))


def _bucket(px):
    import math
    return min(SRC_W, int(2 ** (math.ceil(math.log2(max(px, 16)) * 4) / 4)))


PARTS_ORDER = ["diamond", "mountains", "debris", "rider", "wordmark", "bar", "pennant", "tagline"]


def draw_part(ctx, R, name, cx, cy, width, alpha=1.0, dx=0.0, dy=0.0, scale=1.0,
              rot=0.0, pivot=None, sx=1.0, sy=1.0, color=None):
    """Draw one logo part with the whole logo's content box centred at
    (cx, cy) and `width` design px wide. Per-part transform: offset (dx, dy)
    in design px, scale/rot about `pivot` (source px; default: part anchor =
    logo content centre). color=(r, g, b[, a]) paints the part as a flat
    silhouette (e.g. white logo on dark footage)."""
    if alpha <= 0.0:
        return
    import math
    k = width / CONTENT_W  # design px per source px
    device_w = SRC_W * k * R.scale * max(scale, sx, sy, 1.0)
    bw = _bucket(device_w)
    surf = _part_surface(name, bw)
    px, py = pivot if pivot else (CONTENT_CX, CONTENT_CY)
    ctx.save()
    ctx.translate(cx + dx, cy + dy)
    ctx.scale(k, k)
    ctx.translate(px - CONTENT_CX, py - CONTENT_CY)
    if rot:
        ctx.rotate(math.radians(rot))
    if scale != 1.0 or sx != 1.0 or sy != 1.0:
        ctx.scale(max(scale * sx, 1e-4), max(scale * sy, 1e-4))
    ctx.translate(-px, -py)
    ctx.scale(SRC_W / bw, SRC_W / bw)
    if color is not None:
        c = tuple(color) + ((1.0,) if len(color) == 3 else ())
        ctx.set_source_rgba(c[0], c[1], c[2], c[3] * alpha)
        pat = cairo.SurfacePattern(surf)
        pat.set_filter(cairo.FILTER_GOOD)
        ctx.mask(pat)
    else:
        ctx.set_source_surface(surf, 0, 0)
        ctx.get_source().set_filter(cairo.FILTER_GOOD)
        ctx.paint_with_alpha(alpha) if alpha < 1.0 else ctx.paint()
    ctx.restore()


def draw_logo(ctx, R, cx, cy, width, alpha=1.0, per_part=None, parts=None, color=None):
    """Draw the full logo (or a subset of parts). per_part(name) -> dict of
    draw_part kwargs (dx, dy, scale, rot, pivot, alpha, sx, sy, color) or None
    to skip. Parts include letter0..letter7 (the wordmark letters) if listed."""
    names = parts or PARTS_ORDER
    if per_part is None and parts is None:
        draw_part(ctx, R, "all", cx, cy, width, alpha, color=color)
        return
    for name in names:
        kw = {} if per_part is None else per_part(name)
        if kw is None:
            continue
        kw = dict(kw)
        a = kw.pop("alpha", 1.0) * alpha
        if color is not None:
            kw.setdefault("color", color)
        draw_part(ctx, R, name, cx, cy, width, a, **kw)


def to_design(pt, cx, cy, width):
    """Map a logo source-pixel point to design space for a logo drawn at
    (cx, cy, width). Useful to align vector effects with the raster logo."""
    k = width / CONTENT_W
    return (cx + (pt[0] - CONTENT_CX) * k, cy + (pt[1] - CONTENT_CY) * k)


def path_in_design(points, cx, cy, width):
    return [to_design(p, cx, cy, width) for p in points]
