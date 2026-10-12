"""S4 - 12.500 YouTube subscribers (4.26-7.00 s). See docs/STORYBOARD.md 4.4.

STUB written before the scene build so s05 can import the T4 handoff maths.
The scene builder replaces render() but MUST keep zoom_through, zero_center
and zero_counter_path exactly as defined here (s05 depends on them).
"""
from functools import lru_cache

from deky_reel import brand as B
from deky_reel.engine import ease, text

START, END, LAYER = 4.26, 7.00, 40

LN = {"lnum": True}
NUM_X, NUM_BASE, NUM_SIZE = 120.0, 700.0, 300.0
NUM_FONT = "display-black"


def zoom_through(t):
    """Z(t): anticipation pull-back, then the push through the last '0'."""
    if t < 6.62:
        return 1.0
    if t < 6.70:
        return 1.0 - 0.015 * ease.in_out_sine(ease.progress(t, 6.62, 0.08))
    return 0.985 + 43.015 * ease.in_expo(ease.progress(t, 6.70, 0.30))


@lru_cache(maxsize=4)
def _counter_contour(lang, value):
    """Inner contour (the counter) of the last '0' of the final numeral, as
    design-space commands at Z = 1, plus its bbox."""
    final = B.fmt_int(value, lang)
    lay = text.layout(NUM_FONT, NUM_SIZE, final, features=LN)
    g = [gl for gl in lay.glyphs if not gl.is_space][-1]
    cmds = lay.face.glyph_cmds(g.gid)
    contours, cur = [], []
    for c in cmds:
        if c[0] == "M" and cur:
            contours.append(cur)
            cur = []
        cur.append(c)
    if cur:
        contours.append(cur)

    def pts(contour):
        out = []
        for c in contour:
            out.extend(p for p in c[1:] if isinstance(p, tuple))
        return out

    def area(contour):
        ps = pts(contour)
        xs = [p[0] for p in ps]
        ys = [p[1] for p in ps]
        return (max(xs) - min(xs)) * (max(ys) - min(ys))

    inner = min(contours, key=area)
    s = lay.scale

    def m(p):
        return (NUM_X + g.x + p[0] * s, NUM_BASE - p[1] * s)

    mapped = []
    for c in inner:
        if c[0] == "Z":
            mapped.append(("Z",))
        else:
            mapped.append((c[0],) + tuple(m(p) for p in c[1:]))
    ps = [p for c in mapped for p in c[1:]]
    xs = [p[0] for p in ps]
    ys = [p[1] for p in ps]
    return tuple(mapped), (min(xs), min(ys), max(xs), max(ys))


def zero_center(R):
    """Centre of the bbox of the last '0' counter (design coords, Z = 1)."""
    _, (x0, y0, x1, y1) = _counter_contour(R.lang, R.stats["subscribers"])
    return ((x0 + x1) / 2.0, (y0 + y1) / 2.0)


def zero_counter_path(ctx, R):
    """Append the counter contour of the last '0' to the current path."""
    cmds, _ = _counter_contour(R.lang, R.stats["subscribers"])
    for c in cmds:
        if c[0] == "M":
            ctx.move_to(*c[1])
        elif c[0] == "L":
            ctx.line_to(*c[1])
        elif c[0] == "C":
            ctx.curve_to(c[1][0], c[1][1], c[2][0], c[2][1], c[3][0], c[3][1])
        elif c[0] == "Z":
            ctx.close_path()


def render(ctx, t, R):
    pass  # built by the s04 scene agent
