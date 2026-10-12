"""Mask-shape builders for motivated transitions.

Each function appends a closed path to the current path, so it can be used
directly as a `draw.masked(ctx, lambda c: ...)` mask, a clip, or filled.
"""
import math

from . import draw, logo


def ridge_profile(width=1920.0, amplitude=140.0, x0=0.0, seed_shift=0.0):
    """The logo's mountain ridge, stretched across `width`, as (x, dy) points
    where dy <= 0 is the height above the baseline (dy in [-amplitude, 0])."""
    xs = [p[0] for p in logo.RIDGE]
    ys = [p[1] for p in logo.RIDGE]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    pts = []
    for x, y in zip(xs, ys):
        u = (x - xmin) / (xmax - xmin)
        h = (ymax - y) / (ymax - ymin)
        pts.append((x0 + u * width + seed_shift, -h * amplitude))
    return pts


def ridge_wipe(ctx, progress, direction="up", amplitude=160.0, width=1920.0, height=1080.0,
               overshoot=None):
    """Mountain-silhouette wipe. progress 0 -> nothing covered, 1 -> full frame.

    direction "up": the ridge rises from the bottom edge and covers the frame.
    direction "down": the ridge descends from the top (mirrored peaks).
    The covered region is the area 'inside' the mountains.
    """
    amp = amplitude
    travel = height + amp * 1.2
    base = height + amp * 0.1 - progress * travel  # baseline y of the ridge front
    prof = ridge_profile(width, amp)
    # Extend the profile beyond the frame edges.
    prof = [(-40.0, prof[0][1])] + prof + [(width + 40.0, prof[-1][1])]
    ctx.new_sub_path()
    if direction == "up":
        ctx.move_to(-40, height + 10)
        for x, dy in prof:
            ctx.line_to(x, base + dy + amp)
        ctx.line_to(width + 40, height + 10)
    else:
        top = height - base
        ctx.move_to(-40, -10)
        for x, dy in prof:
            ctx.line_to(x, top - dy - amp)
        ctx.line_to(width + 40, -10)
    ctx.close_path()


def iris(ctx, cx, cy, progress, max_r=None, width=1920.0, height=1080.0):
    """Circle that grows from (cx, cy) to cover the frame at progress 1."""
    if max_r is None:
        max_r = max(math.hypot(cx - x, cy - y) for x in (0, width) for y in (0, height))
    draw.circle(ctx, cx, cy, max(progress, 0.0) * max_r)


def diamond(ctx, cx, cy, size, rot=0.0):
    """The logo's kite-shaped diamond (DIAMOND_KITE) centred on its widest
    point at (cx, cy); size = width in design px."""
    pts = logo.DIAMOND_KITE
    xs = [p[0] for p in pts]
    mx = (min(xs) + max(xs)) / 2
    my = pts[1][1]  # y of the side corners (widest line)
    k = size / (max(xs) - min(xs))
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    out = []
    for x, y in pts:
        dx, dy = (x - mx) * k, (y - my) * k
        out.append((cx + dx * c - dy * s, cy + dx * s + dy * c))
    draw.polygon(ctx, out)


def diamond_iris(ctx, cx, cy, progress, width=1920.0, height=1080.0):
    """Diamond-shaped iris that grows to cover the frame."""
    size = max(progress, 0.0) * max(width, height) * 2.6
    diamond(ctx, cx, cy, size)


def diagonal_wipe(ctx, progress, angle=-18.0, width=1920.0, height=1080.0, feather=0.0):
    """A straight edge sweeping left->right at `angle` degrees from vertical."""
    span = width + height * abs(math.tan(math.radians(angle))) + 200
    x = -100 - height * abs(math.tan(math.radians(angle))) + progress * span
    off = math.tan(math.radians(angle)) * height
    draw.polygon(ctx, [(-200, -10), (x, -10), (x + off, height + 10), (-200, height + 10)])


def bars(ctx, progress, count=5, width=1920.0, height=1080.0, stagger=0.12, vertical=True,
         ease_fn=None):
    """Staggered bar wipe (venetian blinds that slide in)."""
    from . import ease as E
    fn = ease_fn or E.in_out_cubic
    n = count
    for i in range(n):
        p = fn(E.clamp((progress - i * stagger) / max(1 - (n - 1) * stagger, 1e-3)))
        if vertical:
            bw = width / n
            draw_h = height * p
            ctx.rectangle(i * bw - 0.5, height - draw_h, bw + 1, draw_h)
        else:
            bh = height / n
            ctx.rectangle(0, i * bh - 0.5, width * p, bh + 1)
