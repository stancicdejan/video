"""Cairo drawing primitives: shapes, gradients, groups/masks, trim paths,
offscreen layers with blur, and soft shadows.

All coordinates are in design space (1920x1080). The root context is scaled
by the render quality, so the same scene code renders at any resolution.
"""
import math
from contextlib import contextmanager

import cairo
import numpy as np
from PIL import Image, ImageFilter

from .color import rgba

DESIGN_W = 1920
DESIGN_H = 1080

OPERATORS = {
    "over": cairo.OPERATOR_OVER,
    "add": cairo.OPERATOR_ADD,
    "screen": cairo.OPERATOR_SCREEN,
    "multiply": cairo.OPERATOR_MULTIPLY,
    "overlay": cairo.OPERATOR_OVERLAY,
    "soft_light": cairo.OPERATOR_SOFT_LIGHT,
    "color_dodge": cairo.OPERATOR_COLOR_DODGE,
    "lighten": cairo.OPERATOR_LIGHTEN,
    "darken": cairo.OPERATOR_DARKEN,
    "dest_in": cairo.OPERATOR_DEST_IN,
    "dest_out": cairo.OPERATOR_DEST_OUT,
    "source": cairo.OPERATOR_SOURCE,
    "clear": cairo.OPERATOR_CLEAR,
}


# --- surfaces ---------------------------------------------------------------

def new_surface(px_w, px_h):
    return cairo.ImageSurface(cairo.FORMAT_ARGB32, px_w, px_h)


def design_context(surface, scale):
    ctx = cairo.Context(surface)
    ctx.scale(scale, scale)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    return ctx


def surface_to_array(surface):
    """ARGB32 premultiplied surface -> HxWx4 uint8 view (B, G, R, A)."""
    surface.flush()
    w, h = surface.get_width(), surface.get_height()
    stride = surface.get_stride()
    buf = np.ndarray((h, stride // 4, 4), np.uint8, buffer=surface.get_data())
    return buf[:, :w, :]


def array_to_surface(arr):
    """HxWx4 uint8 premultiplied BGRA -> ImageSurface (copies)."""
    h, w = arr.shape[:2]
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    dst = surface_to_array(surf)
    dst[...] = arr
    surf.mark_dirty()
    return surf


def blur_array(arr, radius_px):
    """Gaussian blur of a premultiplied BGRA array (radius in device px)."""
    if radius_px <= 0.3:
        return arr
    im = Image.fromarray(np.ascontiguousarray(arr), "RGBA")
    im = im.filter(ImageFilter.GaussianBlur(radius_px))
    return np.asarray(im)


# --- state helpers -----------------------------------------------------------

@contextmanager
def saved(ctx):
    ctx.save()
    try:
        yield ctx
    finally:
        ctx.restore()


@contextmanager
def transform(ctx, x=0.0, y=0.0, scale=1.0, rot=0.0, pivot=None, sx=None, sy=None):
    """Translate to (x, y), then rotate (deg) / scale about pivot (relative)."""
    ctx.save()
    try:
        ctx.translate(x, y)
        if pivot:
            ctx.translate(pivot[0], pivot[1])
        if rot:
            ctx.rotate(math.radians(rot))
        sx_ = scale if sx is None else sx * scale
        sy_ = scale if sy is None else sy * scale
        if sx_ != 1.0 or sy_ != 1.0:
            ctx.scale(max(sx_, 1e-5), max(sy_, 1e-5))
        if pivot:
            ctx.translate(-pivot[0], -pivot[1])
        yield ctx
    finally:
        ctx.restore()


@contextmanager
def group(ctx, alpha=1.0, operator="over"):
    """Render children into an isolated group, then composite with alpha."""
    ctx.push_group()
    try:
        yield ctx
    finally:
        pat = ctx.pop_group()
        if alpha > 0.0:
            ctx.save()
            ctx.set_operator(OPERATORS[operator])
            ctx.set_source(pat)
            ctx.paint_with_alpha(min(alpha, 1.0))
            ctx.restore()


@contextmanager
def masked(ctx, mask_fn, alpha=1.0, invert=False):
    """Render children, then keep them only where mask_fn(ctx) paints (alpha).
    mask_fn may either paint (fill/stroke/paint with any alpha) or simply
    append a path, which is then filled. invert=True keeps the outside."""
    ctx.push_group()
    try:
        yield ctx
    finally:
        content = ctx.pop_group()
        ctx.push_group_with_content(cairo.CONTENT_ALPHA)
        if invert:
            ctx.set_source_rgba(0, 0, 0, 1)
            ctx.paint()
            ctx.set_operator(cairo.OPERATOR_CLEAR)
        ctx.set_source_rgba(0, 0, 0, 1)
        ctx.new_path()
        mask_fn(ctx)
        # mask_fn may paint itself, or just append a path: fill what is left.
        ctx.set_source_rgba(0, 0, 0, 1)
        ctx.fill()
        mask = ctx.pop_group()
        ctx.save()
        ctx.set_source(content)
        if alpha < 1.0:
            ctx.push_group()
            ctx.set_source(content)
            ctx.mask(mask)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(alpha)
        else:
            ctx.mask(mask)
        ctx.restore()


@contextmanager
def clipped(ctx, path_fn):
    """Clip children to the path appended by path_fn(ctx)."""
    ctx.save()
    ctx.new_path()
    path_fn(ctx)
    ctx.clip()
    try:
        yield ctx
    finally:
        ctx.restore()


class Offscreen:
    """A full-frame offscreen layer in device pixels with the design scale.

    Use for effects cairo cannot do natively (blur, glow):
        with offscreen(ctx, R) as off:
            draw(off.ctx)
            off.blur(12)          # design px
        off.paint(ctx, alpha)
    """

    def __init__(self, R):
        self.R = R
        self.surface = new_surface(R.px_w, R.px_h)
        self.ctx = design_context(self.surface, R.scale)

    def blur(self, radius):
        arr = surface_to_array(self.surface)
        blurred = blur_array(arr.copy(), radius * self.R.scale)
        arr[...] = blurred
        self.surface.mark_dirty()
        return self

    def paint(self, ctx, alpha=1.0, operator="over"):
        ctx.save()
        ctx.identity_matrix()
        ctx.set_operator(OPERATORS[operator])
        ctx.set_source_surface(self.surface, 0, 0)
        ctx.paint_with_alpha(min(max(alpha, 0.0), 1.0))
        ctx.restore()

    def as_pattern(self):
        pat = cairo.SurfacePattern(self.surface)
        m = cairo.Matrix()
        m.scale(self.R.scale, self.R.scale)  # design -> device
        pat.set_matrix(m)
        return pat


def offscreen(R):
    return Offscreen(R)


def blurred(ctx, R, radius, draw_fn, alpha=1.0, operator="over"):
    """Draw draw_fn(ctx) into a layer, gaussian-blur it, composite it."""
    off = Offscreen(R)
    draw_fn(off.ctx)
    off.blur(radius)
    off.paint(ctx, alpha, operator)


def glow(ctx, R, radius, draw_fn, alpha=1.0, crisp=True):
    """Additive bloom: blurred copy screened under (and optionally over) a crisp draw."""
    blurred(ctx, R, radius, draw_fn, alpha, "screen")
    if crisp:
        draw_fn(ctx)


def soft_shadow(ctx, R, path_fn, blur=24.0, dx=0.0, dy=12.0, color=(0, 0, 0, 0.18)):
    """Blurred drop shadow for an arbitrary shape (path_fn appends a path)."""
    def draw(c):
        c.translate(dx, dy)
        c.new_path()
        path_fn(c)
        c.set_source_rgba(*rgba(color))
        c.fill()
    blurred(ctx, R, blur, draw)


# --- path builders ------------------------------------------------------------

def rounded_rect(ctx, x, y, w, h, r):
    r = max(0.0, min(r, w / 2, h / 2))
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def pill(ctx, x, y, w, h):
    rounded_rect(ctx, x, y, w, h, h / 2)


def circle(ctx, cx, cy, r):
    ctx.new_sub_path()
    ctx.arc(cx, cy, max(r, 0.0), 0, 2 * math.pi)
    ctx.close_path()


def polygon(ctx, pts, close=True):
    if not pts:
        return
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if close:
        ctx.close_path()


def smooth_polyline(ctx, pts, tension=0.5):
    """Catmull-Rom spline through points (open), as cubic beziers."""
    if len(pts) < 2:
        return
    ctx.move_to(*pts[0])
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) * tension / 3, p1[1] + (p2[1] - p0[1]) * tension / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * tension / 3, p2[1] - (p3[1] - p1[1]) * tension / 3)
        ctx.curve_to(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])


def star(ctx, cx, cy, r_out, r_in=None, points=5, rot=-90.0):
    r_in = r_out * 0.45 if r_in is None else r_in
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 180.0 / points)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    polygon(ctx, pts)


def arc_path(ctx, cx, cy, r, a0_deg, a1_deg):
    ctx.new_sub_path()
    a0, a1 = math.radians(a0_deg), math.radians(a1_deg)
    if a1 >= a0:
        ctx.arc(cx, cy, r, a0, a1)
    else:
        ctx.arc_negative(cx, cy, r, a0, a1)


# --- fills & strokes ------------------------------------------------------------

def fill(ctx, color, preserve=False):
    ctx.set_source_rgba(*rgba(color))
    ctx.fill_preserve() if preserve else ctx.fill()


def stroke(ctx, color, width, cap="round", join="round", preserve=False, dash=None):
    ctx.set_source_rgba(*rgba(color))
    ctx.set_line_width(width)
    ctx.set_line_cap({"butt": cairo.LINE_CAP_BUTT, "round": cairo.LINE_CAP_ROUND,
                      "square": cairo.LINE_CAP_SQUARE}[cap])
    ctx.set_line_join({"miter": cairo.LINE_JOIN_MITER, "round": cairo.LINE_JOIN_ROUND,
                       "bevel": cairo.LINE_JOIN_BEVEL}[join])
    ctx.set_dash(dash or [])
    ctx.stroke_preserve() if preserve else ctx.stroke()
    ctx.set_dash([])


def linear_gradient(x0, y0, x1, y1, stops):
    """stops: list of (offset, color)."""
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for off, c in stops:
        g.add_color_stop_rgba(off, *rgba(c))
    return g


def radial_gradient(cx, cy, r, stops, cx0=None, cy0=None, r0=0.0):
    g = cairo.RadialGradient(cx if cx0 is None else cx0, cy if cy0 is None else cy0, r0, cx, cy, r)
    for off, c in stops:
        g.add_color_stop_rgba(off, *rgba(c))
    return g


def paint(ctx, color_or_pattern, alpha=1.0, operator="over"):
    ctx.save()
    ctx.set_operator(OPERATORS[operator])
    if isinstance(color_or_pattern, cairo.Pattern):
        ctx.set_source(color_or_pattern)
    else:
        ctx.set_source_rgba(*rgba(color_or_pattern))
    ctx.paint_with_alpha(alpha) if alpha < 1.0 else ctx.paint()
    ctx.restore()


def fill_rect(ctx, x, y, w, h, color_or_pattern, operator="over"):
    ctx.save()
    ctx.set_operator(OPERATORS[operator])
    ctx.rectangle(x, y, w, h)
    if isinstance(color_or_pattern, cairo.Pattern):
        ctx.set_source(color_or_pattern)
    else:
        ctx.set_source_rgba(*rgba(color_or_pattern))
    ctx.fill()
    ctx.restore()


# --- trim paths (animated draw-on) ---------------------------------------------

class FlatPath:
    """Flattened polyline representation of a cairo path, in user space.

    Build once per frame (or cache when the geometry is static):
        fp = FlatPath.from_fn(ctx, lambda c: smooth_polyline(c, pts))
        fp.emit(ctx, 0.0, p)        # appends the trimmed sub-path
        x, y, ang = fp.point_at(p)  # head position for a leading dot
    """

    def __init__(self, subpaths):
        self.subpaths = subpaths  # list of list[(x, y)]
        self.seg = []
        total = 0.0
        for sp in subpaths:
            lens = [0.0]
            for i in range(1, len(sp)):
                total_i = math.hypot(sp[i][0] - sp[i - 1][0], sp[i][1] - sp[i - 1][1])
                lens.append(lens[-1] + total_i)
            self.seg.append(lens)
            total += lens[-1]
        self.length = total

    @classmethod
    def from_fn(cls, ctx, path_fn, tolerance=0.25):
        ctx.save()
        ctx.new_path()
        old_tol = ctx.get_tolerance()
        ctx.set_tolerance(tolerance)
        path_fn(ctx)
        flat = ctx.copy_path_flat()
        ctx.set_tolerance(old_tol)
        ctx.new_path()
        ctx.restore()
        subpaths, cur, start = [], None, None
        for kind, pts in flat:
            if kind == cairo.PATH_MOVE_TO:
                if cur and len(cur) > 1:
                    subpaths.append(cur)
                cur = [pts]
                start = pts
            elif kind == cairo.PATH_LINE_TO:
                if cur is None:
                    cur = [pts]
                else:
                    cur.append(pts)
            elif kind == cairo.PATH_CLOSE_PATH:
                if cur and start:
                    cur.append(start)
                    subpaths.append(cur)
                cur = None
        if cur and len(cur) > 1:
            subpaths.append(cur)
        return cls(subpaths)

    @classmethod
    def from_points(cls, pts):
        return cls([list(pts)])

    def emit(self, ctx, start=0.0, end=1.0):
        """Append the portion between fractions start..end of total length."""
        if self.length <= 0 or end <= start:
            return
        a, b = start * self.length, end * self.length
        acc = 0.0
        for sp, lens in zip(self.subpaths, self.seg):
            L = lens[-1]
            lo, hi = max(a - acc, 0.0), min(b - acc, L)
            if hi > lo:
                started = False
                for i in range(1, len(sp)):
                    s0, s1 = lens[i - 1], lens[i]
                    if s1 < lo:
                        continue
                    if s0 > hi:
                        break
                    seg_len = s1 - s0 if s1 > s0 else 1e-9
                    t0 = max((lo - s0) / seg_len, 0.0)
                    t1 = min((hi - s0) / seg_len, 1.0)
                    p0 = (sp[i - 1][0] + (sp[i][0] - sp[i - 1][0]) * t0,
                          sp[i - 1][1] + (sp[i][1] - sp[i - 1][1]) * t0)
                    p1 = (sp[i - 1][0] + (sp[i][0] - sp[i - 1][0]) * t1,
                          sp[i - 1][1] + (sp[i][1] - sp[i - 1][1]) * t1)
                    if not started:
                        ctx.move_to(*p0)
                        started = True
                    ctx.line_to(*p1)
            acc += L

    def point_at(self, frac):
        """(x, y, angle_rad) at a fraction of total length."""
        if not self.subpaths:
            return (0.0, 0.0, 0.0)
        d = max(0.0, min(frac, 1.0)) * self.length
        acc = 0.0
        for sp, lens in zip(self.subpaths, self.seg):
            L = lens[-1]
            if d <= acc + L or sp is self.subpaths[-1]:
                local = min(d - acc, L)
                for i in range(1, len(sp)):
                    if lens[i] >= local:
                        seg_len = lens[i] - lens[i - 1] or 1e-9
                        t = (local - lens[i - 1]) / seg_len
                        x = sp[i - 1][0] + (sp[i][0] - sp[i - 1][0]) * t
                        y = sp[i - 1][1] + (sp[i][1] - sp[i - 1][1]) * t
                        ang = math.atan2(sp[i][1] - sp[i - 1][1], sp[i][0] - sp[i - 1][0])
                        return (x, y, ang)
                last = sp[-1]
                prev = sp[-2] if len(sp) > 1 else sp[-1]
                return (last[0], last[1], math.atan2(last[1] - prev[1], last[0] - prev[0]))
            acc += L
        last = self.subpaths[-1][-1]
        return (last[0], last[1], 0.0)


def trim_stroke(ctx, path_fn, start, end, color, width, cap="round", join="round"):
    """Stroke only [start, end] (fractions) of the path appended by path_fn."""
    fp = FlatPath.from_fn(ctx, path_fn)
    ctx.new_path()
    fp.emit(ctx, start, end)
    stroke(ctx, color, width, cap, join)
    return fp


@contextmanager
def camera(ctx, look_x=960.0, look_y=540.0, zoom=1.0, rot=0.0, screen_x=960.0, screen_y=540.0):
    """Virtual 2D camera: the design-space point (look_x, look_y) appears at
    (screen_x, screen_y) on screen, magnified by zoom and rotated by rot (deg).
    Push-ins, whip pans and 'fly through a glyph' moves are animations of
    look/zoom."""
    ctx.save()
    try:
        ctx.translate(screen_x, screen_y)
        if rot:
            ctx.rotate(math.radians(rot))
        ctx.scale(max(zoom, 1e-5), max(zoom, 1e-5))
        ctx.translate(-look_x, -look_y)
        yield ctx
    finally:
        ctx.restore()
