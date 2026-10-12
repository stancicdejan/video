"""Vector typography: HarfBuzz shaping + glyph outlines drawn as cairo paths.

Every glyph is a real vector path, so text can be animated per glyph
(position, scale, rotation, opacity, color), used as a clip/mask, or stroked.

Coordinates are in design space (1920x1080). Font sizes are CSS-like px.
"""
import math
import os
from dataclasses import dataclass, field

import uharfbuzz as hb
from fontTools.ttLib import TTFont

from .color import rgba

FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "fonts")

FONT_FILES = {
    "display": "PlayfairDisplay_700Bold.ttf",
    "display-regular": "PlayfairDisplay_400Regular.ttf",
    "display-black": "PlayfairDisplay_900Black.ttf",
    "display-italic": "PlayfairDisplay_400Regular_Italic.ttf",
    "display-bold-italic": "PlayfairDisplay_700Bold_Italic.ttf",
    "body": "SourceSans3_400Regular.ttf",
    "body-light": "SourceSans3_300Light.ttf",
    "body-semibold": "SourceSans3_600SemiBold.ttf",
    "body-bold": "SourceSans3_700Bold.ttf",
    "body-black": "SourceSans3_900Black.ttf",
}


class _PathRecorder:
    """fontTools-style pen that records outline commands (font units, y-up)."""

    def __init__(self):
        self.cmds = []
        self._cur = (0.0, 0.0)

    def moveTo(self, p):
        self.cmds.append(("M", p))
        self._cur = p

    def lineTo(self, p):
        self.cmds.append(("L", p))
        self._cur = p

    def curveTo(self, *pts):
        # Cubic segments (possibly a poly-bezier); cairo wants exact cubics.
        if len(pts) == 3:
            self.cmds.append(("C", pts[0], pts[1], pts[2]))
            self._cur = pts[2]
        else:
            # Decompose a super-bezier into consecutive cubics.
            for i in range(0, len(pts) - 2, 3):
                self.cmds.append(("C", pts[i], pts[i + 1], pts[i + 2]))
                self._cur = pts[i + 2]

    def qCurveTo(self, *pts):
        # TrueType quadratic spline with implied on-curve points.
        if pts[-1] is None:
            pts = pts[:-1]
        cur = self._cur
        offs, end = pts[:-1], pts[-1]
        for i, c in enumerate(offs):
            if i < len(offs) - 1:
                nxt = offs[i + 1]
                on = ((c[0] + nxt[0]) / 2, (c[1] + nxt[1]) / 2)
            else:
                on = end
            c1 = (cur[0] + 2 / 3 * (c[0] - cur[0]), cur[1] + 2 / 3 * (c[1] - cur[1]))
            c2 = (on[0] + 2 / 3 * (c[0] - on[0]), on[1] + 2 / 3 * (c[1] - on[1]))
            self.cmds.append(("C", c1, c2, on))
            cur = on
        if not offs:
            self.cmds.append(("L", end))
            cur = end
        self._cur = cur

    def closePath(self):
        self.cmds.append(("Z",))

    def endPath(self):
        pass


class FontFace:
    def __init__(self, path):
        self.path = path
        blob = hb.Blob.from_file_path(path)
        self.face = hb.Face(blob)
        self.font = hb.Font(self.face)
        self.upem = self.face.upem
        ext = self.font.get_font_extents("ltr")
        self.ascender = ext.ascender
        self.descender = ext.descender  # negative
        tt = TTFont(path, lazy=True)
        os2 = tt["OS/2"]
        self.cap_height = getattr(os2, "sCapHeight", 0) or self.ascender * 0.7
        self.x_height = getattr(os2, "sxHeight", 0) or self.cap_height * 0.7
        tt.close()
        self._glyphs = {}

    def glyph_cmds(self, gid):
        cmds = self._glyphs.get(gid)
        if cmds is None:
            rec = _PathRecorder()
            self.font.draw_glyph_with_pen(gid, rec)
            cmds = rec.cmds
            self._glyphs[gid] = cmds
        return cmds

    def shape(self, text, features=None):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.font, buf, features or {"kern": True, "liga": True})
        return list(zip(buf.glyph_infos, buf.glyph_positions))


_FACES = {}


def face(key):
    f = _FACES.get(key)
    if f is None:
        fname = FONT_FILES.get(key, key)
        path = fname if os.path.isabs(fname) else os.path.join(FONT_DIR, fname)
        f = FontFace(os.path.normpath(path))
        _FACES[key] = f
    return f


@dataclass
class Glyph:
    gid: int
    x: float          # pen x of glyph origin, relative to layout start (px)
    y: float          # baseline offset (px, y-down)
    advance: float    # px
    char: str
    index: int        # glyph index in the layout
    char_index: int   # cluster (character) index into the text
    word: int         # word index (whitespace separated)
    is_space: bool = False


@dataclass
class TextLayout:
    font_key: str
    size: float
    text: str
    tracking: float = 0.0
    features: dict = None
    glyphs: list = field(default_factory=list)
    width: float = 0.0

    def __post_init__(self):
        self.face = face(self.font_key)
        self.scale = self.size / self.face.upem
        feats = {"kern": True, "liga": True}
        if self.features:
            feats.update(self.features)
        shaped = self.face.shape(self.text, feats)
        x = 0.0
        word = 0
        prev_space = False
        n = len(shaped)
        for i, (info, pos) in enumerate(shaped):
            ch = self.text[info.cluster] if info.cluster < len(self.text) else ""
            is_space = ch.isspace()
            if is_space and not prev_space and i > 0:
                word += 1
            elif not is_space and prev_space:
                pass
            adv = pos.x_advance * self.scale
            g = Glyph(
                gid=info.codepoint,
                x=x + pos.x_offset * self.scale,
                y=-pos.y_offset * self.scale,
                advance=adv,
                char=ch,
                index=i,
                char_index=info.cluster,
                word=word,
                is_space=is_space,
            )
            self.glyphs.append(g)
            x += adv + (self.tracking if i < n - 1 else 0.0)
            prev_space = is_space
        # Re-number words so they are contiguous and spaces belong to no word.
        w = -1
        prev_space = True
        for g in self.glyphs:
            if not g.is_space and prev_space:
                w += 1
            g.word = w if not g.is_space else -1
            prev_space = g.is_space
        self.word_count = w + 1
        self.width = x

    # --- metrics -------------------------------------------------------
    @property
    def ascent(self):
        return self.face.ascender * self.scale

    @property
    def descent(self):
        return -self.face.descender * self.scale

    @property
    def cap_height(self):
        return self.face.cap_height * self.scale

    @property
    def x_height(self):
        return self.face.x_height * self.scale

    @property
    def visible_glyphs(self):
        return [g for g in self.glyphs if not g.is_space]

    def word_spans(self):
        """List of (x0, x1) per word, relative to layout start."""
        spans = {}
        for g in self.glyphs:
            if g.word < 0:
                continue
            x0, x1 = spans.get(g.word, (g.x, g.x + g.advance))
            spans[g.word] = (min(x0, g.x), max(x1, g.x + g.advance))
        return [spans[k] for k in sorted(spans)]

    def origin(self, x, y, align="left", valign="baseline"):
        """Return the baseline-left origin for an anchor point."""
        if align == "center":
            x -= self.width / 2
        elif align == "right":
            x -= self.width
        if valign == "cap-center":
            y += self.cap_height / 2
        elif valign == "x-center":
            y += self.x_height / 2
        elif valign == "top":
            y += self.cap_height
        elif valign == "bottom":
            y -= self.descent
        elif valign == "middle":
            y += (self.ascent - self.descent) / 2
        return x, y

    def bbox(self, x, y, align="left", valign="baseline"):
        ox, oy = self.origin(x, y, align, valign)
        return (ox, oy - self.cap_height, self.width, self.cap_height)

    # --- drawing -------------------------------------------------------
    def _emit(self, ctx, g):
        s = self.scale
        for c in self.face.glyph_cmds(g.gid):
            op = c[0]
            if op == "M":
                ctx.move_to(c[1][0] * s, -c[1][1] * s)
            elif op == "L":
                ctx.line_to(c[1][0] * s, -c[1][1] * s)
            elif op == "C":
                ctx.curve_to(c[1][0] * s, -c[1][1] * s, c[2][0] * s, -c[2][1] * s,
                             c[3][0] * s, -c[3][1] * s)
            elif op == "Z":
                ctx.close_path()

    def path(self, ctx, x, y, align="left", valign="baseline", per_glyph=None):
        """Append glyph outlines to the current path (for clip/mask/stroke)."""
        ox, oy = self.origin(x, y, align, valign)
        n = len(self.glyphs)
        for g in self.glyphs:
            if g.is_space:
                continue
            tf = per_glyph(g, n) if per_glyph else None
            if tf is not None and tf.get("alpha", 1.0) <= 0.0:
                continue
            ctx.save()
            self._apply(ctx, ox, oy, g, tf)
            self._emit(ctx, g)
            ctx.restore()

    def _apply(self, ctx, ox, oy, g, tf):
        ctx.translate(ox + g.x, oy + g.y)
        if not tf:
            return
        dx, dy = tf.get("dx", 0.0), tf.get("dy", 0.0)
        sx = tf.get("sx", tf.get("scale", 1.0))
        sy = tf.get("sy", tf.get("scale", 1.0))
        rot = tf.get("rot", 0.0)
        # Pivot: glyph centre on the cap-height middle (or baseline if asked).
        px = g.advance / 2
        py = -self.cap_height / 2 if tf.get("pivot", "center") == "center" else 0.0
        ctx.translate(dx + px, dy + py)
        if rot:
            ctx.rotate(math.radians(rot))
        if sx != 1.0 or sy != 1.0:
            ctx.scale(max(sx, 1e-4), max(sy, 1e-4))
        ctx.translate(-px, -py)

    def draw(self, ctx, x, y, color=(1, 1, 1, 1), align="left", valign="baseline",
             per_glyph=None, stroke=None, stroke_width=0.0):
        """Fill the text. per_glyph(glyph, n) -> dict(dx, dy, sx, sy, scale,
        rot (deg), alpha, color, pivot) or None."""
        ox, oy = self.origin(x, y, align, valign)
        base = rgba(color)
        n = len(self.glyphs)
        if per_glyph is None:
            ctx.save()
            ctx.translate(ox, oy)
            ctx.new_path()
            for g in self.glyphs:
                if g.is_space:
                    continue
                ctx.save()
                ctx.translate(g.x, g.y)
                self._emit(ctx, g)
                ctx.restore()
            self._paint(ctx, base, stroke, stroke_width)
            ctx.restore()
            return
        for g in self.glyphs:
            if g.is_space:
                continue
            tf = per_glyph(g, n) or {}
            a = tf.get("alpha", 1.0)
            if a <= 0.001:
                continue
            col = rgba(tf.get("color", base))
            col = (col[0], col[1], col[2], col[3] * a)
            ctx.save()
            self._apply(ctx, ox, oy, g, tf)
            ctx.new_path()
            self._emit(ctx, g)
            self._paint(ctx, col, stroke, stroke_width)
            ctx.restore()

    @staticmethod
    def _paint(ctx, col, stroke, stroke_width):
        if stroke is not None and stroke_width > 0:
            ctx.set_source_rgba(*col)
            ctx.fill_preserve()
            ctx.set_source_rgba(*rgba(stroke))
            ctx.set_line_width(stroke_width)
            ctx.set_line_join(1)
            ctx.stroke()
        elif col[3] > 0:
            ctx.set_source_rgba(*col)
            ctx.fill()
        else:
            ctx.new_path()


_LAYOUT_CACHE = {}


def layout(font_key, size, text, tracking=0.0, features=None):
    """Cached TextLayout constructor."""
    key = (font_key, round(size, 3), text, round(tracking, 3),
           tuple(sorted((features or {}).items())))
    lay = _LAYOUT_CACHE.get(key)
    if lay is None:
        lay = TextLayout(font_key, size, text, tracking, features)
        _LAYOUT_CACHE[key] = lay
    return lay


def fit_size(font_key, text, max_width, size, min_size=10.0, tracking=0.0, features=None):
    """Largest size <= size so the text fits max_width."""
    lay = layout(font_key, size, text, tracking, features)
    if lay.width <= max_width:
        return size
    return max(min_size, size * max_width / max(lay.width, 1e-3))


def tabular(features=None):
    """Feature set for jitter-free counters (tabular lining figures)."""
    f = {"tnum": True, "lnum": True, "kern": True}
    if features:
        f.update(features)
    return f


def wrap(font_key, size, string, max_width, tracking=0.0, features=None):
    """Greedy word wrap -> list of line strings that fit max_width."""
    words = string.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if not cur or layout(font_key, size, trial, tracking, features).width <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines
