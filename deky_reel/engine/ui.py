"""Motion versions of the deky.bike site components and its motion language.

The site animates with `fade-in-up` (opacity 0->1, translateY 30px->0,
0.7 s ease-out, 0.2 s stagger) and `slide-down`. Those are reproduced here,
along with the pill CTA, rounded-2xl cards, the section heading underline bar,
the sage quick-info bar, and number counters.
"""
from . import draw, ease, icons, text
from .color import rgba, with_alpha


def fade_in_up(t, start, duration=0.7, distance=30.0, ease_fn=ease.site_ease_out):
    """Site's fade-in-up: returns (alpha, dy)."""
    p = ease_fn(ease.progress(t, start, duration))
    return p, (1.0 - p) * distance


def fade_out_down(t, start, duration=0.4, distance=20.0, ease_fn=ease.in_cubic):
    p = ease_fn(ease.progress(t, start, duration))
    return 1.0 - p, p * distance


def underline_bar(ctx, cx, y, progress, color, width=64.0, height=4.0, scale=1.6, align="center"):
    """Section heading underline (h-1 w-16 rounded-full bg-primary), growing
    from its centre (or left). scale enlarges it for a 1920 canvas."""
    if progress <= 0:
        return
    w = width * scale * progress
    h = height * scale
    x = cx - w / 2 if align == "center" else cx
    ctx.new_path()
    draw.pill(ctx, x, y, max(w, h), h)
    draw.fill(ctx, with_alpha(color, min(1.0, progress * 3)))


def pill_button(ctx, cx, cy, label, bg, fg, font="body-semibold", size=34.0,
                icon=None, pad_x=44.0, height=None, alpha=1.0, scale=1.0, press=0.0,
                shadow_R=None):
    """Rounded-full CTA like the site's 'Rezerviši' button. press: 0..1 click
    squash. Returns the button rect (x, y, w, h) in design px."""
    lay = text.layout(font, size, label)
    icon_sz = size * 0.95 if icon else 0.0
    gap = size * 0.4 if icon else 0.0
    h = height or size * 2.15
    w = lay.width + icon_sz + gap + 2 * pad_x
    s = scale * (1.0 - 0.06 * press)
    x, y = cx - w / 2, cy - h / 2
    if alpha <= 0 or s <= 0:
        return (x, y, w, h)
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(s, s)
    ctx.translate(-cx, -cy)
    with draw.group(ctx, alpha):
        if shadow_R is not None:
            draw.soft_shadow(ctx, shadow_R, lambda c: draw.pill(c, x, y, w, h), blur=22,
                             dy=10, color=(0, 0, 0, 0.22))
        ctx.new_path()
        draw.pill(ctx, x, y, w, h)
        draw.fill(ctx, bg)
        tx = x + pad_x
        if icon:
            icons.draw(ctx, icon, tx + icon_sz / 2, cy, icon_sz, fg, stroke_width=2.2)
            tx += icon_sz + gap
        lay.draw(ctx, tx, cy, fg, valign="x-center")
    ctx.restore()
    return (x, y, w, h)


def card(ctx, R, x, y, w, h, fill=(1, 1, 1, 1), border=None, radius=24.0, shadow=0.12,
         alpha=1.0):
    """rounded-2xl card with 1px border and soft shadow (site style)."""
    if alpha <= 0:
        return
    with draw.group(ctx, alpha):
        if shadow > 0:
            draw.soft_shadow(ctx, R, lambda c: draw.rounded_rect(c, x, y, w, h, radius),
                             blur=28, dy=14, color=(0.05, 0.12, 0.07, shadow))
        ctx.new_path()
        draw.rounded_rect(ctx, x, y, w, h, radius)
        draw.fill(ctx, fill, preserve=border is not None)
        if border is not None:
            draw.stroke(ctx, border, 2.0)


def quick_info_bar(ctx, y, h, items, bg, fg, progress=1.0, font="body-semibold",
                   size=30.0, tracking=3.0, x=0.0, w=1920.0):
    """Sage bar with uppercase, tracked items separated by bullets."""
    if progress <= 0:
        return
    ctx.save()
    ctx.new_path()
    ctx.rectangle(x, y, w * progress, h)
    ctx.clip()
    draw.fill_rect(ctx, x, y, w, h, bg)
    labels = [text.layout(font, size, s.upper(), tracking=tracking) for s in items]
    bullet = text.layout(font, size, "•")
    gap = 48.0
    total = sum(l.width for l in labels) + (len(labels) - 1) * (2 * gap + bullet.width)
    cx = x + (w - total) / 2
    cy = y + h / 2
    f = rgba(fg)
    for i, l in enumerate(labels):
        l.draw(ctx, cx, cy, (f[0], f[1], f[2], 0.92), valign="cap-center")
        cx += l.width
        if i < len(labels) - 1:
            cx += gap
            bullet.draw(ctx, cx, cy, (f[0], f[1], f[2], 0.45), valign="x-center")
            cx += bullet.width + gap
    ctx.restore()


def counter_value(t, start, duration, target, ease_fn=ease.out_expo):
    """Eased count-up value (float) from 0 to target."""
    return target * ease.get(ease_fn)(ease.progress(t, start, duration))


def rolling_digits(ctx, t, start, duration, digits_text, x, y, font, size, color,
                   align="left", stagger=0.06, ease_fn=ease.out_expo, travel=None):
    """Odometer-style counter: each digit rolls vertically through 0-9 to its
    final value (masked to the line). Non-digits (separators) fade in.

    digits_text is the final formatted string, e.g. '12.500'.
    """
    lay = text.layout(font, size, digits_text, features=text.tabular())
    ox, oy = lay.origin(x, y, align)
    digit_layouts = {d: text.layout(font, size, d, features=text.tabular()) for d in "0123456789"}
    line_h = lay.cap_height * 1.6
    c = rgba(color)
    ctx.save()
    ctx.new_path()
    ctx.rectangle(ox - size, oy - lay.cap_height * 1.3, lay.width + 2 * size, lay.cap_height * 1.6)
    ctx.clip()
    n_digits = sum(ch.isdigit() for ch in digits_text)
    di = 0
    for g in lay.glyphs:
        ch = g.char
        if ch.isdigit():
            k = di
            di += 1
            p = ease.get(ease_fn)(ease.progress(t, start + (n_digits - 1 - k) * stagger * 0.5 + k * stagger * 0.5, duration))
            final = int(ch)
            spins = 1 + (n_digits - k) % 3  # leading digits spin more
            pos = p * (spins * 10 + final)  # how many digits have rolled by
            base = int(pos)
            frac = pos - base
            for j in (0, 1):
                d = (base + j) % 10
                dy = (j - frac) * line_h
                dl = digit_layouts[str(d)]
                a = 1.0 - min(abs(j - frac), 1.0) * 0.6
                dl.draw(ctx, ox + g.x + (g.advance - dl.width) / 2, oy + g.y + dy,
                        (c[0], c[1], c[2], c[3] * a))
        elif not g.is_space:
            p = ease.progress(t, start + duration * 0.35, 0.3)
            gl = text.layout(font, size, ch, features=text.tabular())
            gl.draw(ctx, ox + g.x, oy + g.y + (1 - p) * 10, (c[0], c[1], c[2], c[3] * p))
    ctx.restore()
    return lay


def word_reveal(ctx, t, start, lay, x, y, color, align="left", valign="baseline",
                stagger=0.12, duration=0.7, distance=None, ease_fn=ease.snappy,
                mask=True, rot=0.0):
    """Masked word-by-word slide-up reveal (each word rises from behind a line)."""
    distance = lay.size * 1.05 if distance is None else distance
    ox, oy = lay.origin(x, y, align, valign)
    c = rgba(color)

    def pg(g, n):
        p = ease.get(ease_fn)(ease.progress(t, start + max(g.word, 0) * stagger, duration))
        return dict(dy=(1 - p) * distance, alpha=1.0 if mask else p,
                    rot=(1 - p) * rot, pivot="baseline")

    if mask:
        ctx.save()
        ctx.new_path()
        ctx.rectangle(ox - lay.size, oy - lay.ascent * 1.05, lay.width + 2 * lay.size,
                      lay.ascent * 1.05 + lay.descent * 1.15)
        ctx.clip()
        lay.draw(ctx, ox, oy, c, per_glyph=pg)
        ctx.restore()
    else:
        lay.draw(ctx, ox, oy, c, per_glyph=pg)


def char_cascade(ctx, t, start, lay, x, y, color, align="left", valign="baseline",
                 stagger=0.025, duration=0.6, distance=40.0, ease_fn=ease.out_back,
                 scale_from=0.6, rot_from=0.0, fade=True):
    """Per-character pop-in (scale + rise + optional rotation)."""
    c = rgba(color)

    def pg(g, n):
        p = ease.progress(t, start + g.index * stagger, duration)
        e = ease.get(ease_fn)(p)
        return dict(dy=(1 - e) * distance, scale=scale_from + (1 - scale_from) * e,
                    rot=(1 - e) * rot_from, alpha=ease.out_quad(p * 1.6) if fade else 1.0)

    lay.draw(ctx, x, y, c, align=align, valign=valign, per_glyph=pg)


def trail(ctx, fp, start, end, color, width=8.0, head=True, head_color=None, head_r=None,
          glow_R=None, glow_radius=14.0):
    """The 'ride line' motif: a stroked trim of FlatPath fp from start to end
    (fractions) with an optional glowing head dot at `end`.
    Returns the head position (x, y, angle)."""
    if end <= start:
        return fp.point_at(end)
    ctx.new_path()
    fp.emit(ctx, start, end)
    draw.stroke(ctx, color, width)
    hx, hy, ang = fp.point_at(end)
    if head:
        r = head_r if head_r is not None else width * 1.25
        hc = head_color if head_color is not None else color
        if glow_R is not None:
            draw.blurred(ctx, glow_R, glow_radius, lambda c: (draw.circle(c, hx, hy, r * 1.8),
                                                              draw.fill(c, with_alpha(hc, 0.85))),
                         operator="screen", bbox=(hx - r * 1.8, hy - r * 1.8, r * 3.6, r * 3.6))
        draw.circle(ctx, hx, hy, r)
        draw.fill(ctx, hc)
    return hx, hy, ang
