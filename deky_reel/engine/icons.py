"""Lucide icons (the same icon set the deky.bike site uses via lucide-react),
parsed from the original SVGs and drawn as cairo vector strokes.

    icons.draw(ctx, "youtube", cx, cy, size=96, color=..., progress=1.0)

progress < 1 draws the icon on (trim path), which is how icons "write"
themselves in. fill=... additionally fills closed shapes.
"""
import math
import os
import re
import xml.etree.ElementTree as ET
from functools import lru_cache

from . import draw as _d
from .color import rgba

ICON_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "icons"))

_NUM = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
_CMD = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]")


def _tokens(d):
    pos = 0
    out = []
    while pos < len(d):
        ch = d[pos]
        if _CMD.match(ch):
            out.append(ch)
            pos += 1
        elif ch in " ,\n\t":
            pos += 1
        else:
            m = _NUM.match(d, pos)
            if not m:
                pos += 1
                continue
            out.append(float(m.group()))
            pos = m.end()
    return out


def _arc_to_beziers(x1, y1, rx, ry, phi, fa, fs, x2, y2):
    """SVG elliptical arc -> list of cubic bezier control tuples."""
    if rx == 0 or ry == 0:
        return [((x1, y1), (x2, y2), (x2, y2))]
    phi = math.radians(phi)
    cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p = cp * dx + sp * dy
    y1p = -sp * dx + cp * dy
    rx, ry = abs(rx), abs(ry)
    lam = (x1p ** 2) / (rx ** 2) + (y1p ** 2) / (ry ** 2)
    if lam > 1:
        s = math.sqrt(lam)
        rx, ry = rx * s, ry * s
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    coef = math.sqrt(max(num / den, 0)) if den else 0
    if fa == fs:
        coef = -coef
    cxp = coef * rx * y1p / ry
    cyp = -coef * ry * x1p / rx
    cx = cp * cxp - sp * cyp + (x1 + x2) / 2
    cy = sp * cxp + cp * cyp + (y1 + y2) / 2

    def ang(ux, uy, vx, vy):
        a = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        return a

    th1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dth = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not fs and dth > 0:
        dth -= 2 * math.pi
    elif fs and dth < 0:
        dth += 2 * math.pi
    segs = max(1, int(math.ceil(abs(dth) / (math.pi / 2))))
    delta = dth / segs
    t = 4 / 3 * math.tan(delta / 4)
    out = []
    a = th1
    for _ in range(segs):
        c1, s1 = math.cos(a), math.sin(a)
        c2, s2 = math.cos(a + delta), math.sin(a + delta)
        p1 = (c1 - t * s1, s1 + t * c1)
        p2 = (c2 + t * s2, s2 - t * c2)
        p3 = (c2, s2)

        def tf(p):
            x, y = p[0] * rx, p[1] * ry
            return (cp * x - sp * y + cx, sp * x + cp * y + cy)
        out.append((tf(p1), tf(p2), tf(p3)))
        a += delta
    return out


def _path_cmds(d):
    """Parse SVG path data into absolute ('M'|'L'|'C'|'Z', pts...) commands."""
    toks = _tokens(d)
    cmds = []
    i = 0
    cur = (0.0, 0.0)
    start = (0.0, 0.0)
    last_c2 = None
    last_q = None
    cmd = None
    while i < len(toks):
        if isinstance(toks[i], str):
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                cmds.append(("Z",))
                cur = start
                last_c2 = last_q = None
                continue
        rel = cmd.islower()
        c = cmd.upper()

        def num():
            nonlocal i
            v = toks[i]
            i += 1
            return v

        if c == "M":
            x, y = num(), num()
            if rel:
                x, y = cur[0] + x, cur[1] + y
            cmds.append(("M", (x, y)))
            cur = start = (x, y)
            cmd = "l" if rel else "L"
            last_c2 = last_q = None
        elif c == "L":
            x, y = num(), num()
            if rel:
                x, y = cur[0] + x, cur[1] + y
            cmds.append(("L", (x, y)))
            cur = (x, y)
            last_c2 = last_q = None
        elif c == "H":
            x = num()
            x = cur[0] + x if rel else x
            cmds.append(("L", (x, cur[1])))
            cur = (x, cur[1])
            last_c2 = last_q = None
        elif c == "V":
            y = num()
            y = cur[1] + y if rel else y
            cmds.append(("L", (cur[0], y)))
            cur = (cur[0], y)
            last_c2 = last_q = None
        elif c == "C":
            p = [num() for _ in range(6)]
            if rel:
                p = [p[k] + cur[k % 2] for k in range(6)]
            cmds.append(("C", (p[0], p[1]), (p[2], p[3]), (p[4], p[5])))
            last_c2 = (p[2], p[3])
            cur = (p[4], p[5])
            last_q = None
        elif c == "S":
            p = [num() for _ in range(4)]
            if rel:
                p = [p[k] + cur[k % 2] for k in range(4)]
            c1 = (2 * cur[0] - last_c2[0], 2 * cur[1] - last_c2[1]) if last_c2 else cur
            cmds.append(("C", c1, (p[0], p[1]), (p[2], p[3])))
            last_c2 = (p[0], p[1])
            cur = (p[2], p[3])
            last_q = None
        elif c in "QT":
            if c == "Q":
                p = [num() for _ in range(4)]
                if rel:
                    p = [p[k] + cur[k % 2] for k in range(4)]
                q = (p[0], p[1])
                end = (p[2], p[3])
            else:
                p = [num() for _ in range(2)]
                if rel:
                    p = [p[k] + cur[k % 2] for k in range(2)]
                q = (2 * cur[0] - last_q[0], 2 * cur[1] - last_q[1]) if last_q else cur
                end = (p[0], p[1])
            c1 = (cur[0] + 2 / 3 * (q[0] - cur[0]), cur[1] + 2 / 3 * (q[1] - cur[1]))
            c2 = (end[0] + 2 / 3 * (q[0] - end[0]), end[1] + 2 / 3 * (q[1] - end[1]))
            cmds.append(("C", c1, c2, end))
            last_q = q
            cur = end
            last_c2 = None
        elif c == "A":
            rx, ry, phi, fa, fs, x, y = (num() for _ in range(7))
            if rel:
                x, y = cur[0] + x, cur[1] + y
            for c1, c2, p3 in _arc_to_beziers(cur[0], cur[1], rx, ry, phi, int(fa), int(fs), x, y):
                cmds.append(("C", c1, c2, p3))
            cur = (x, y)
            last_c2 = last_q = None
        else:
            i += 1
    return cmds


def _circle_cmds(cx, cy, r):
    k = 0.5522847498 * r
    return [("M", (cx + r, cy)),
            ("C", (cx + r, cy + k), (cx + k, cy + r), (cx, cy + r)),
            ("C", (cx - k, cy + r), (cx - r, cy + k), (cx - r, cy)),
            ("C", (cx - r, cy - k), (cx - k, cy - r), (cx, cy - r)),
            ("C", (cx + k, cy - r), (cx + r, cy - k), (cx + r, cy)),
            ("Z",)]


def _ellipse_cmds(cx, cy, rx, ry):
    kx, ky = 0.5522847498 * rx, 0.5522847498 * ry
    return [("M", (cx + rx, cy)),
            ("C", (cx + rx, cy + ky), (cx + kx, cy + ry), (cx, cy + ry)),
            ("C", (cx - kx, cy + ry), (cx - rx, cy + ky), (cx - rx, cy)),
            ("C", (cx - rx, cy - ky), (cx - kx, cy - ry), (cx, cy - ry)),
            ("C", (cx + kx, cy - ry), (cx + rx, cy - ky), (cx + rx, cy)),
            ("Z",)]


def _rect_cmds(x, y, w, h, rx, ry):
    if not rx and not ry:
        return [("M", (x, y)), ("L", (x + w, y)), ("L", (x + w, y + h)), ("L", (x, y + h)), ("Z",)]
    rx = rx or ry
    ry = ry or rx
    k = 0.5522847498
    return [("M", (x + rx, y)), ("L", (x + w - rx, y)),
            ("C", (x + w - rx + k * rx, y), (x + w, y + ry - k * ry), (x + w, y + ry)),
            ("L", (x + w, y + h - ry)),
            ("C", (x + w, y + h - ry + k * ry), (x + w - rx + k * rx, y + h), (x + w - rx, y + h)),
            ("L", (x + rx, y + h)),
            ("C", (x + rx - k * rx, y + h), (x, y + h - ry + k * ry), (x, y + h - ry)),
            ("L", (x, y + ry)),
            ("C", (x, y + ry - k * ry), (x + rx - k * rx, y), (x + rx, y)),
            ("Z",)]


@lru_cache(maxsize=128)
def load(name):
    """List of sub-shapes, each a list of absolute commands in the 24x24 grid."""
    path = os.path.join(ICON_DIR, f"{name}.svg")
    root = ET.parse(path).getroot()
    shapes = []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        a = el.attrib
        f = lambda k, d=0.0: float(a.get(k, d))
        if tag == "path":
            shapes.append(_path_cmds(a["d"]))
        elif tag == "circle":
            shapes.append(_circle_cmds(f("cx"), f("cy"), f("r")))
        elif tag == "ellipse":
            shapes.append(_ellipse_cmds(f("cx"), f("cy"), f("rx"), f("ry")))
        elif tag == "rect":
            shapes.append(_rect_cmds(f("x"), f("y"), f("width"), f("height"), f("rx"), f("ry")))
        elif tag == "line":
            shapes.append([("M", (f("x1"), f("y1"))), ("L", (f("x2"), f("y2")))])
        elif tag in ("polyline", "polygon"):
            nums = [float(v) for v in _NUM.findall(a["points"])]
            pts = list(zip(nums[0::2], nums[1::2]))
            cmds = [("M", pts[0])] + [("L", p) for p in pts[1:]]
            if tag == "polygon":
                cmds.append(("Z",))
            shapes.append(cmds)
    return shapes


def _emit(ctx, cmds):
    for c in cmds:
        if c[0] == "M":
            ctx.move_to(*c[1])
        elif c[0] == "L":
            ctx.line_to(*c[1])
        elif c[0] == "C":
            ctx.curve_to(c[1][0], c[1][1], c[2][0], c[2][1], c[3][0], c[3][1])
        elif c[0] == "Z":
            ctx.close_path()


def path(ctx, name, cx, cy, size):
    """Append the icon outline (24-grid scaled to `size`) to the current path."""
    s = size / 24.0
    ctx.save()
    ctx.translate(cx - 12 * s, cy - 12 * s)
    ctx.scale(s, s)
    for cmds in load(name):
        _emit(ctx, cmds)
    ctx.restore()


def draw(ctx, name, cx, cy, size=48.0, color=(1, 1, 1, 1), stroke_width=2.0,
         progress=1.0, fill=None, rot=0.0, scale=1.0):
    """Draw a Lucide icon centred at (cx, cy). stroke_width is in the 24-grid
    (Lucide default 2). progress animates a draw-on across all strokes."""
    if progress <= 0 or scale <= 0:
        return
    s = size / 24.0 * scale
    ctx.save()
    ctx.translate(cx, cy)
    if rot:
        ctx.rotate(math.radians(rot))
    ctx.translate(-12 * s, -12 * s)
    ctx.scale(s, s)
    shapes = load(name)
    if fill is not None:
        ctx.new_path()
        for cmds in shapes:
            if cmds and cmds[-1][0] == "Z":
                _emit(ctx, cmds)
        ctx.set_source_rgba(*rgba(fill))
        ctx.fill()
    ctx.new_path()
    if progress >= 1.0:
        for cmds in shapes:
            _emit(ctx, cmds)
    else:
        for cmds in shapes:
            fp = _d.FlatPath.from_fn(ctx, lambda c, cm=cmds: _emit(c, cm), tolerance=0.02)
            fp.emit(ctx, 0.0, progress)
    _d.stroke(ctx, color, stroke_width)
    ctx.restore()


def youtube_badge(ctx, cx, cy, width, bg=(1.0, 0.0, 0.0, 1.0), fg=(1, 1, 1, 1), alpha=1.0):
    """Solid YouTube-style play badge (filled rounded rect + triangle)."""
    h = width * 0.70
    r = h * 0.28
    ctx.save()
    ctx.new_path()
    _d.rounded_rect(ctx, cx - width / 2, cy - h / 2, width, h, r)
    b = rgba(bg)
    ctx.set_source_rgba(b[0], b[1], b[2], b[3] * alpha)
    ctx.fill()
    tri = h * 0.42
    ctx.move_to(cx - tri * 0.38, cy - tri / 2)
    ctx.line_to(cx + tri * 0.55, cy)
    ctx.line_to(cx - tri * 0.38, cy + tri / 2)
    ctx.close_path()
    f = rgba(fg)
    ctx.set_source_rgba(f[0], f[1], f[2], f[3] * alpha)
    ctx.fill()
    ctx.restore()
