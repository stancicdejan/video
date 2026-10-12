"""A faithful vector rendition of the deky.bike home page (from the site's
React source: Header.tsx, HeroSection.tsx, Index.tsx) plus a browser window,
for "the real site" moments in the reel.

The page is laid out in CSS px for a 1440 px wide desktop viewport and scaled
into any rect, so it can be shown full-frame or as a small card.

    site_mock.draw_browser(ctx, R, x, y, w, h, content=lambda c, cx, cy, cw, ch:
        site_mock.draw_page(c, R, cx, cy, cw, ch, scroll=..., t=t, load_start=...))
"""
from .. import brand as B
from . import draw, ease, icons, images, text, ui
from .color import with_alpha

VIEWPORT_W = 1440.0
VIEWPORT_H = 810.0
HERO_H = 0.85 * VIEWPORT_H          # h-[85vh]
HEADER_H = 80.0                     # h-20
CONTAINER_W = 1152.0                # max-w-6xl
QUICK_H = 64.0                      # py-5 + text-base


def _container_x():
    return (VIEWPORT_W - CONTAINER_W) / 2 + 32.0  # lg:px-8


def page_height():
    return HERO_H + QUICK_H + 760.0


def draw_header(ctx, R, sticky=False, alpha=1.0, lang=None):
    """Header bar (heroMode). sticky=True gives the muted/95 bar with border."""
    lang = lang or R.lang
    x0 = _container_x()
    x1 = VIEWPORT_W - x0
    with draw.group(ctx, alpha):
        if sticky:
            draw.soft_shadow(ctx, R, lambda c: c.rectangle(0, 0, VIEWPORT_W, HEADER_H),
                             blur=6, dy=1, color=(0, 0, 0, 0.08))
            draw.fill_rect(ctx, 0, 0, VIEWPORT_W, HEADER_H, with_alpha(B.MUTED, 0.95))
            draw.fill_rect(ctx, 0, HEADER_H - 1, VIEWPORT_W, 1, B.BORDER)
        fg = B.FOREGROUND if sticky else B.PRIMARY_FG
        # Logo: h-16 image of the full logo canvas (1280x1024) -> 80x64 px.
        images.draw_image_at(ctx, R, "assets/site/logo.png", x0 + 40, HEADER_H / 2, 80)
        # Nav, right aligned: links, language switcher, CTA pill.
        labels = {"sr": ["Početna", "O nama", "Galerija", "Kontakt"],
                  "en": ["Home", "About", "Gallery", "Contact"]}[lang]
        cta = R.t("nav.reserve")
        cta_lay = text.layout("body-semibold", 14, cta)
        cta_w = 20 + 16 + 8 + cta_lay.width + 20
        cta_h = 40.0
        cx = x1 - cta_w
        cy = HEADER_H / 2
        ctx.new_path()
        draw.pill(ctx, cx, cy - cta_h / 2, cta_w, cta_h)
        draw.fill(ctx, B.PRIMARY)
        icons.draw(ctx, "phone", cx + 20 + 8, cy, 16, B.PRIMARY_FG)
        cta_lay.draw(ctx, cx + 20 + 16 + 8, cy, B.PRIMARY_FG, valign="x-center")
        # Language switcher: [flag] SR v
        lx = cx - 32 - 64
        _flag(ctx, lx + 12, cy, 18, 12, lang)
        text.layout("body-semibold", 14, "SR" if lang == "sr" else "EN").draw(
            ctx, lx + 26, cy, fg, valign="cap-center")
        icons.draw(ctx, "chevron-right", lx + 56, cy, 13, fg, rot=90)
        nx = lx - 32
        for i, lab in enumerate(reversed(labels)):
            lay = text.layout("body-semibold", 14, lab.upper(), tracking=0.35)
            nx -= lay.width
            lay.draw(ctx, nx, cy, fg, valign="cap-center")
            if i == len(labels) - 1:  # active page: border-b-2 border-primary
                draw.fill_rect(ctx, nx, cy + 12, lay.width, 2, B.PRIMARY)
            nx -= 32


def _flag(ctx, cx, cy, w, h, lang):
    x, y = cx - w / 2, cy - h / 2
    if lang == "sr":
        cols = [(0.78, 0.14, 0.22, 1), (0.05, 0.25, 0.53, 1), (1, 1, 1, 1)]
    else:
        cols = [(0.0, 0.14, 0.49, 1), (1, 1, 1, 1), (0.78, 0.06, 0.18, 1)]
    for i, c in enumerate(cols):
        draw.fill_rect(ctx, x, y + i * h / 3, w, h / 3 + 0.3, c)


def draw_hero(ctx, R, t=None, load_start=None, image="assets/site/hero-home.jpg",
              zoom=1.0, focus=(0.5, 0.5)):
    """Hero section: full-bleed photo, foreground/50 overlay, centred title,
    subtitle and CTA with the site's staggered fade-in-up on load."""
    images.draw_image(ctx, R, image, 0, 0, VIEWPORT_W, HERO_H, zoom=zoom, focus=focus)
    draw.fill_rect(ctx, 0, 0, VIEWPORT_W, HERO_H, with_alpha(B.FOREGROUND, 0.5))

    def fiu(delay):
        if t is None or load_start is None:
            return 1.0, 0.0
        return ui.fade_in_up(t, load_start + delay)

    title = R.t("hero.title")
    title_lay = text.layout("display", 72, title)
    sub_lines = text.wrap("body", 20, R.t("hero.subtitle") + (
        " Iznajmljivanje električnih bicikala širom Čačka." if R.lang == "sr"
        else " E-bike rental across Čačak."), 672)
    cta = R.t("nav.reserve")
    cta_lay = text.layout("body-semibold", 18, cta)
    cta_h = 18 * 1.55 + 32
    # Vertical stack: h1 (line-height 1) mb-6, p (lh 1.75) mb-8, CTA.
    stack_h = 72 + 24 + len(sub_lines) * 28 + 32 + cta_h
    top = (HERO_H - stack_h) / 2
    a, dy = fiu(0.0)
    if a > 0:
        title_lay.draw(ctx, VIEWPORT_W / 2, top + 72 * 0.86 + dy, with_alpha(B.PRIMARY_FG, a), align="center")
    a, dy = fiu(0.2)
    if a > 0:
        for i, line in enumerate(sub_lines):
            text.layout("body", 20, line).draw(ctx, VIEWPORT_W / 2, top + 72 + 24 + 20 + i * 28 + dy,
                                               with_alpha(B.PRIMARY_FG, 0.9 * a), align="center")
    a, dy = fiu(0.4)
    if a > 0:
        cy = top + 72 + 24 + len(sub_lines) * 28 + 32 + cta_h / 2 + dy
        w = 32 + 20 + 8 + cta_lay.width + 32
        with draw.group(ctx, a):
            draw.soft_shadow(ctx, R, lambda c: draw.pill(c, VIEWPORT_W / 2 - w / 2, cy - cta_h / 2, w, cta_h),
                             blur=10, dy=6, color=(0, 0, 0, 0.25))
            ctx.new_path()
            draw.pill(ctx, VIEWPORT_W / 2 - w / 2, cy - cta_h / 2, w, cta_h)
            draw.fill(ctx, B.PRIMARY)
            icons.draw(ctx, "phone", VIEWPORT_W / 2 - w / 2 + 32 + 10, cy, 20, B.PRIMARY_FG)
            cta_lay.draw(ctx, VIEWPORT_W / 2 - w / 2 + 32 + 28, cy, B.PRIMARY_FG, valign="x-center")
    return top


def draw_sections(ctx, R, y0):
    """Quick-info bar + 'Zašto baš Deky Bike?' section with the three cards."""
    items = [R.t("quick.locations"), R.t("quick.booking"), R.t("quick.experience")]
    ui.quick_info_bar(ctx, y0, QUICK_H, items, B.SECONDARY, B.PRIMARY_FG, size=16,
                      tracking=0.4, w=VIEWPORT_W)
    y = y0 + QUICK_H
    draw.fill_rect(ctx, 0, y, VIEWPORT_W, 760, B.BACKGROUND)
    y += 96
    title = "Zašto baš Deky Bike?" if R.lang == "sr" else "Why Deky Bike?"
    text.layout("display", 48, title).draw(ctx, VIEWPORT_W / 2, y + 40, B.FOREGROUND, align="center")
    sub = ("Iznajmite električni bicikl i otkrijte lepotu regiona na sopstvenim uslovima."
           if R.lang == "sr" else
           "Rent an e-bike and discover the beauty of the region on your own terms.")
    text.layout("body", 18, sub).draw(ctx, VIEWPORT_W / 2, y + 88, B.MUTED_FG, align="center")
    ctx.new_path()
    draw.pill(ctx, VIEWPORT_W / 2 - 32, y + 112, 64, 4)
    draw.fill(ctx, B.PRIMARY)
    cards = {"sr": [("Avanti 500Wh", "Premium električni bicikli"), ("Radius 50–100km", "Baterija za ceo dan"),
                    ("Dostava na lokaciju", "Transport uključen")],
             "en": [("Avanti 500Wh", "Premium e-bikes"), ("Range 50–100km", "A full day of battery"),
                    ("Delivery included", "Transport included")]}[R.lang]
    cw, gap = (CONTAINER_W - 64 - 2 * 32) / 3, 32
    cy = y + 180
    for i, (ttl, desc) in enumerate(cards):
        x = _container_x() + i * (cw + gap)
        ui.card(ctx, R, x, cy, cw, 230, fill=B.CARD, border=B.BORDER, radius=16, shadow=0.06)
        draw.circle(ctx, x + cw / 2, cy + 32 + 32, 32)
        draw.fill(ctx, with_alpha(B.PRIMARY, 0.1))
        icons.draw(ctx, ["bike", "battery", "truck"][i], x + cw / 2, cy + 64, 32, B.PRIMARY)
        text.layout("display", 20, ttl).draw(ctx, x + cw / 2, cy + 140, B.FOREGROUND, align="center")
        text.layout("body", 16, desc).draw(ctx, x + cw / 2, cy + 172, B.MUTED_FG, align="center")


def draw_page(ctx, R, x, y, w, h, scroll=0.0, t=None, load_start=None, hero_zoom=1.0,
              sticky=None, header_alpha=1.0):
    """Draw the home page into rect (x, y, w, h). scroll in CSS px.
    The header becomes sticky once scroll passes the hero (as on the site)."""
    k = w / VIEWPORT_W
    ctx.save()
    ctx.new_path()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    ctx.translate(x, y)
    ctx.scale(k, k)
    draw.fill_rect(ctx, 0, 0, VIEWPORT_W, h / k, B.BACKGROUND)
    ctx.save()
    ctx.translate(0, -scroll)
    draw_hero(ctx, R, t, load_start, zoom=hero_zoom)
    draw_sections(ctx, R, HERO_H)
    ctx.restore()
    if sticky is None:
        sticky = scroll > HERO_H - 80
    if not sticky:
        ctx.save()
        ctx.translate(0, -scroll)
        draw_header(ctx, R, sticky=False, alpha=header_alpha)
        ctx.restore()
    else:
        # slide-down 0.3s ease-out on becoming sticky (approximated by scroll).
        p = ease.out_cubic(ease.clamp((scroll - (HERO_H - 80)) / 60.0))
        ctx.save()
        ctx.translate(0, -(1 - p) * HEADER_H)
        draw_header(ctx, R, sticky=True, alpha=header_alpha)
        ctx.restore()
    ctx.restore()


def draw_browser(ctx, R, x, y, w, h, content=None, url="deky.bike", radius=18.0,
                 chrome_h=56.0, shadow=0.28, alpha=1.0, dark=False):
    """Minimal browser window: rounded frame, traffic lights, address pill.
    content(ctx, cx, cy, cw, ch) draws the page into the viewport rect."""
    if alpha <= 0:
        return
    with draw.group(ctx, alpha):
        if shadow > 0:
            draw.soft_shadow(ctx, R, lambda c: draw.rounded_rect(c, x, y, w, h, radius),
                             blur=40, dy=24, color=(0.04, 0.10, 0.06, shadow))
        ctx.new_path()
        draw.rounded_rect(ctx, x, y, w, h, radius)
        draw.fill(ctx, B.DARK_CARD if dark else B.CARD)
        # chrome
        bar = B.DARK_MUTED if dark else B.MUTED
        ctx.save()
        ctx.new_path()
        draw.rounded_rect(ctx, x, y, w, h, radius)
        ctx.clip()
        draw.fill_rect(ctx, x, y, w, chrome_h, bar)
        draw.fill_rect(ctx, x, y + chrome_h - 1, w, 1, B.BORDER if not dark else B.DARK_MUTED)
        if content:
            ctx.save()
            ctx.new_path()
            ctx.rectangle(x, y + chrome_h, w, h - chrome_h)
            ctx.clip()
            content(ctx, x, y + chrome_h, w, h - chrome_h)
            ctx.restore()
        ctx.restore()
        dot_r = chrome_h * 0.11
        for i, c in enumerate([(1.0, 0.37, 0.34), (1.0, 0.74, 0.18), (0.16, 0.79, 0.25)]):
            draw.circle(ctx, x + chrome_h * 0.5 + i * dot_r * 3.4, y + chrome_h / 2, dot_r)
            draw.fill(ctx, c)
        pw = min(w * 0.42, 560)
        ph = chrome_h * 0.6
        px = x + (w - pw) / 2
        py = y + (chrome_h - ph) / 2
        ctx.new_path()
        draw.pill(ctx, px, py, pw, ph)
        draw.fill(ctx, B.BACKGROUND if not dark else B.DARK_BG)
        fs = ph * 0.5
        lay = text.layout("body-semibold", fs, url)
        icon_s = fs * 0.95
        total = icon_s + fs * 0.4 + lay.width
        sx = px + (pw - total) / 2
        _lock(ctx, sx + icon_s / 2, py + ph / 2, icon_s, B.MUTED_FG)
        lay.draw(ctx, sx + icon_s + fs * 0.4, py + ph / 2, B.FOREGROUND if not dark else B.PRIMARY_FG,
                 valign="x-center")
        # frame border
        ctx.new_path()
        draw.rounded_rect(ctx, x, y, w, h, radius)
        draw.stroke(ctx, with_alpha(B.BORDER, 0.9), 1.5)


def _lock(ctx, cx, cy, s, color):
    bw, bh = s * 0.72, s * 0.5
    ctx.new_path()
    draw.rounded_rect(ctx, cx - bw / 2, cy - bh / 2 + s * 0.12, bw, bh, s * 0.1)
    draw.fill(ctx, color)
    ctx.new_path()
    ctx.arc(cx, cy - s * 0.1, s * 0.22, 3.14159, 0)
    draw.stroke(ctx, color, s * 0.1, cap="butt")
