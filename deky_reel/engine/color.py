"""Color helpers. Colors are (r, g, b) or (r, g, b, a) tuples of floats 0..1."""
import colorsys


def hsl(h, s, l, a=1.0):
    """CSS-style hsl(h deg, s %, l %) -> rgba floats."""
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360.0, l / 100.0, s / 100.0)
    return (r, g, b, a)


def hex_(code, a=1.0):
    code = code.lstrip("#")
    if len(code) == 3:
        code = "".join(c * 2 for c in code)
    r, g, b = (int(code[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (r, g, b, a)


def to_hex(c):
    return "#" + "".join(f"{round(max(0, min(1, v)) * 255):02X}" for v in c[:3])


def with_alpha(c, a):
    return (c[0], c[1], c[2], (c[3] if len(c) > 3 else 1.0) * a)


def mix(c1, c2, t):
    c1 = tuple(c1) + ((1.0,) if len(c1) == 3 else ())
    c2 = tuple(c2) + ((1.0,) if len(c2) == 3 else ())
    return tuple(a + (b - a) * t for a, b in zip(c1, c2))


def lighten(c, amount):
    return mix(c, (1, 1, 1, c[3] if len(c) > 3 else 1.0), amount)


def darken(c, amount):
    return mix(c, (0, 0, 0, c[3] if len(c) > 3 else 1.0), amount)


def rgba(c):
    """Normalize to a 4-tuple."""
    return tuple(c) if len(c) == 4 else (c[0], c[1], c[2], 1.0)
