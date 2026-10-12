"""S1 - Logo splash (0.00-1.00 s).

The Deky Bike logo assembles itself from its own parts on the site's cream
paper: the site's 64x4 heading underline grows into the logo bar, mountains
rise out of the bar, the diamond outline is drawn by two yellow "rider dots"
that meet behind the rider, the rider jumps in and lands (dust + micro shake),
the DEKY BIKE letters rise, the lower bar snaps open and the pennant slides
down (the site's slide-down), then a light sweep glints across it.
"""
import math

from deky_reel import brand as B
from deky_reel.engine import draw, ease, logo
from deky_reel.engine.color import mix, with_alpha

START, END, LAYER = 0.0, 1.0, 10

CX, CY, LOGO_W = 960.0, 548.0, 740.0
K = LOGO_W / logo.CONTENT_W           # design px per logo source px


def P(pt):
    return logo.to_design(pt, CX, CY, LOGO_W)


BAR_TOP = P((0, 555))[1]
BAR_BOT = P((0, 574))[1]
BAR_X0 = P((217, 0))[0]
BAR_X1 = P((1063, 0))[0]
WORD_TOP = P((0, 575))[1]
WORD_BOT = P((0, 682))[1]
LBAR_BOT = P((0, 701))[1]
REAR_CONTACT = (505, 535)              # rear wheel ground contact (source px)
FRONT_CONTACT = (690, 520)

# Diamond draw-on: the band's centre line, split at the hidden apex so two
# strokes start at the lower corners and meet behind the rider.
_D = logo.DIAMOND_PATH
LEFT_LEG = [P(p) for p in (_D[0], _D[1], _D[2], _D[3])]
RIGHT_LEG = [P(p) for p in (_D[6], _D[5], _D[4], _D[3])]
_FP_L = draw.FlatPath.from_points(LEFT_LEG)
_FP_R = draw.FlatPath.from_points(RIGHT_LEG)

# Procedural dirt flecks burst from the wheels at landing.
FLECKS = [
    # (contact, vx, vy, size, spin, colour mix)
    (REAR_CONTACT, -420, -520, 10, 9.0, 0.2),
    (REAR_CONTACT, -300, -640, 7, -7.0, 0.6),
    (REAR_CONTACT, -540, -380, 8, 5.0, 0.9),
    (REAR_CONTACT, -180, -560, 6, 11.0, 0.4),
    (REAR_CONTACT, -360, -300, 9, -6.0, 0.1),
    (FRONT_CONTACT, -120, -460, 7, 8.0, 0.7),
    (FRONT_CONTACT, 160, -420, 6, -10.0, 0.3),
    (FRONT_CONTACT, -260, -520, 8, 6.0, 0.8),
]
LAND = 0.42


def logo_parts_state(t):
    """Per-part transforms for the assembly at time t. Exposed so a later
    scene can reuse the assembled logo exactly."""
    st = {}
    # Mountains rise from behind the bar.
    p = ease.progress(t, 0.04, 0.28)
    st["mountains_dy"] = (1 - ease.out_back(p, 1.9)) * 80.0
    st["mountains_a"] = ease.out_quad(ease.progress(t, 0.04, 0.08))
    # Diamond draw-on.
    st["diamond_p"] = ease.in_out_cubic(ease.progress(t, 0.06, 0.30))
    # Rider jump: quadratic bezier offset path, spring rotation, scale.
    p = ease.progress(t, 0.12, LAND - 0.12)
    u = ease.out_cubic(p)
    p0, p1, p2 = (-330.0, 210.0), (-120.0, -190.0), (0.0, 0.0)
    bx = (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0]
    by = (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]
    st["rider_dx"], st["rider_dy"] = bx, by
    sp = ease.spring(ease.progress(t, 0.12, 0.50), damping=0.38, freq=2.2)
    st["rider_rot"] = -22.0 * (1 - sp)
    st["rider_scale"] = 0.80 + 0.20 * ease.out_cubic(p)
    st["rider_a"] = ease.progress(t, 0.12, 0.06)
    # Letters rise, staggered.
    st["letters"] = [ease.out_expo(ease.progress(t, 0.20 + i * 0.025, 0.24)) for i in range(8)]
    # Lower bar snaps open from the centre, pennant slides down.
    st["lbar"] = ease.out_expo(ease.progress(t, 0.26, 0.12))
    st["pennant"] = ease.out_cubic(ease.progress(t, 0.30, 0.22))
    st["tagline"] = ease.out_cubic(ease.progress(t, 0.38, 0.22))
    # Upper bar grows from the site underline.
    st["bar_grow"] = ease.out_expo(ease.progress(t, 0.0, 0.20))
    st["bar_raster"] = ease.progress(t, 0.12, 0.10)
    return st


def draw_background(ctx, t):
    draw.paint(ctx, B.BACKGROUND)
    glow = draw.radial_gradient(960, 540, 760, [
        (0.0, with_alpha(B.WARM_CREAM, 0.75)),
        (0.55, with_alpha(B.WARM_CREAM, 0.25)),
        (1.0, with_alpha(B.WARM_CREAM, 0.0)),
    ])
    draw.paint(ctx, glow)


def draw_logo_assembly(ctx, R, t, st=None):
    st = st or logo_parts_state(t)

    # 1. Upper bar: the site's 64x4 underline (x1.5) grows into the logo bar,
    #    then hands over to the raster bar.
    g = st["bar_grow"]
    bar_cy = (BAR_TOP + BAR_BOT) / 2
    full_w = BAR_X1 - BAR_X0
    w = 96 + (full_w - 96) * g
    h = 6 + (BAR_BOT - BAR_TOP - 6) * g
    vec_a = 1.0 - st["bar_raster"]
    if vec_a > 0:
        ctx.new_path()
        draw.pill(ctx, 960 - w / 2, bar_cy - h / 2, w, h) if g < 0.98 else \
            ctx.rectangle(960 - w / 2, bar_cy - h / 2, w, h)
        draw.fill(ctx, with_alpha(B.PRIMARY, vec_a))
    if st["bar_raster"] > 0:
        with draw.clipped(ctx, lambda c: c.rectangle(0, BAR_TOP - 0.5, 1920, BAR_BOT - BAR_TOP + 1)):
            logo.draw_part(ctx, R, "mountains", CX, CY, LOGO_W, alpha=st["bar_raster"])

    # 2. Diamond outline drawn on through a thick trim-stroke mask.
    dp = st["diamond_p"]
    if dp > 0:
        def mask(c):
            c.new_path()
            _FP_L.emit(c, 0, dp)
            _FP_R.emit(c, 0, dp)
            draw.stroke(c, (0, 0, 0, 1), logo.DIAMOND_BAND * K + 26, cap="round")
        with draw.masked(ctx, mask):
            logo.draw_part(ctx, R, "diamond", CX, CY, LOGO_W)

    # 3. Mountains rise out of the bar (clipped above it).
    if st["mountains_a"] > 0:
        with draw.clipped(ctx, lambda c: c.rectangle(0, 0, 1920, BAR_TOP + 0.5)):
            logo.draw_part(ctx, R, "mountains", CX, CY, LOGO_W, alpha=st["mountains_a"],
                           dy=st["mountains_dy"])

    # 4. Debris chips pop at landing.
    pd = ease.progress(t, LAND - 0.02, 0.16)
    if pd > 0:
        logo.draw_part(ctx, R, "debris", CX, CY, LOGO_W, alpha=min(1, pd * 2),
                       scale=ease.out_back(pd, 2.2), pivot=REAR_CONTACT)

    # 5. Rider + bike.
    if st["rider_a"] > 0:
        logo.draw_part(ctx, R, "rider", CX, CY, LOGO_W, alpha=st["rider_a"],
                       dx=st["rider_dx"], dy=st["rider_dy"], rot=st["rider_rot"],
                       scale=st["rider_scale"], pivot=REAR_CONTACT)

    # 6. Wordmark letters rise inside the band.
    with draw.clipped(ctx, lambda c: c.rectangle(0, WORD_TOP, 1920, WORD_BOT - WORD_TOP)):
        for i, p in enumerate(st["letters"]):
            if p > 0:
                logo.draw_part(ctx, R, f"letter{i}", CX, CY, LOGO_W, dy=(1 - p) * 95)

    # 7. Lower bar opens from the centre.
    if st["lbar"] > 0:
        logo.draw_part(ctx, R, "bar", CX, CY, LOGO_W, sx=max(st["lbar"], 1e-3), pivot=(640, 692))

    # 8. Pennant slides down from behind the lower bar (site slide-down).
    pp = st["pennant"]
    if pp > 0:
        with draw.clipped(ctx, lambda c: c.rectangle(0, LBAR_BOT - 1, 1920, 1080)):
            logo.draw_part(ctx, R, "pennant", CX, CY, LOGO_W, dy=-(1 - pp) * 175)
            if st["tagline"] > 0:
                logo.draw_part(ctx, R, "tagline", CX, CY, LOGO_W, dy=-(1 - pp) * 175 + (1 - st["tagline"]) * 10,
                               alpha=st["tagline"])


def draw_rider_dots(ctx, R, t):
    """Yellow rider dots riding the diamond trim heads (the ride-line motif)."""
    dp = ease.in_out_cubic(ease.progress(t, 0.06, 0.30))
    a = ease.progress(t, 0.0, 0.04) * (1 - ease.progress(t, 0.33, 0.07))
    if a <= 0 or dp <= 0:
        return
    for fp in (_FP_L, _FP_R):
        x, y, _ = fp.point_at(dp)

        def dot(c, x=x, y=y):
            draw.circle(c, x, y, 13)
            draw.fill(c, with_alpha(B.ACCENT, 0.9 * a))
        draw.blurred(ctx, R, 10, dot, operator="screen", bbox=(x - 13, y - 13, 26, 26))
        draw.circle(ctx, x, y, 7)
        draw.fill(ctx, with_alpha(B.ACCENT, a))
        ctx.new_path()
        draw.circle(ctx, x, y, 7)
        draw.stroke(ctx, with_alpha(B.FOREGROUND, a), 2.5)


def draw_flecks(ctx, t):
    tt = t - LAND
    if tt <= 0 or tt > 0.32:
        return
    a = 1 - ease.progress(tt, 0.12, 0.2)
    for (src, vx, vy, s, spin, m) in FLECKS:
        x0, y0 = P(src)
        x = x0 + vx * tt * 0.9
        y = y0 + vy * tt + 0.5 * 2200 * tt * tt
        col = mix(B.LOGO_LIME, B.LOGO_GREEN, m)
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(spin * tt * 3)
        draw.polygon(ctx, [(0, -s), (s * 0.9, s * 0.6), (-s * 0.8, s * 0.5)])
        draw.fill(ctx, with_alpha(col, a))
        ctx.restore()


def draw_light_sweep(ctx, R, t):
    p = ease.in_out_sine(ease.progress(t, 0.52, 0.24))
    if p <= 0 or p >= 1:
        return
    x = 480 + (1460 - 480) * p

    def mask(c):
        logo.draw_logo(c, R, CX, CY, LOGO_W)

    with draw.masked(ctx, mask):
        ctx.save()
        ctx.translate(x, 540)
        ctx.rotate(math.radians(25))
        g = draw.linear_gradient(-70, 0, 70, 0, [
            (0.0, with_alpha(B.WARM_CREAM, 0.0)),
            (0.5, with_alpha((1, 1, 0.92), 0.55)),
            (1.0, with_alpha(B.WARM_CREAM, 0.0)),
        ])
        ctx.rectangle(-70, -900, 140, 1800)
        ctx.set_source(g)
        ctx.fill()
        ctx.restore()


def camera_state(t):
    zoom = 1.0 + 0.02 * ease.progress(t, 0.0, 0.82)
    # Landing micro shake (2 px, decays over 0.12 s).
    sh = 0.0
    if LAND <= t < LAND + 0.12:
        d = 1 - (t - LAND) / 0.12
        sh = 2.5 * d * math.sin((t - LAND) * 90)
    return zoom, sh


def render(ctx, t, R):
    draw_background(ctx, t)
    zoom, sh = camera_state(t)
    with draw.camera(ctx, 960, 540 - sh, zoom):
        draw_logo_assembly(ctx, R, t)
        draw_flecks(ctx, t)
        draw_rider_dots(ctx, R, t)
        draw_light_sweep(ctx, R, t)
