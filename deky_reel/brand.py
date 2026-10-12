"""Deky Bike brand system, pulled from the deky.bike site source
(stancicdejan/deky-electric-ride: src/index.css, tailwind.config.ts,
src/i18n/sr.ts + en.ts, src/components/*).

Colors are the site's exact HSL tokens. Copy is the site's own wording
wherever it exists. STATS are placeholders until real channel numbers are in.
"""
from .engine.color import hsl, to_hex

# --- design tokens (src/index.css :root) -------------------------------------
BACKGROUND = hsl(53, 100, 96)         # cream page background
FOREGROUND = hsl(137, 30, 15)         # deep forest text
CARD = hsl(53, 60, 98)
PRIMARY = hsl(137, 39, 30)            # teal / forest green (buttons, bars)
PRIMARY_FG = hsl(0, 0, 100)
SECONDARY = hsl(119, 28, 61)          # sage (quick-info bar, footer)
ACCENT = hsl(42, 91, 66)              # warm yellow
ACCENT_FG = hsl(137, 39, 15)
MUTED = hsl(53, 40, 92)
MUTED_FG = hsl(137, 15, 40)
BORDER = hsl(53, 30, 85)
WARM_CREAM = hsl(53, 100, 88)
WARM_SAND = hsl(53, 40, 85)
HERO_OVERLAY = hsl(137, 30, 10)
# Dark theme tokens (.dark) - handy for night/dark scenes.
DARK_BG = hsl(137, 30, 8)
DARK_CARD = hsl(137, 25, 12)
DARK_MUTED = hsl(137, 20, 18)

# Logo gradient (sampled from the supplied logo).
LOGO_LIME = (178 / 255, 234 / 255, 80 / 255, 1.0)
LOGO_GREEN = (77 / 255, 156 / 255, 38 / 255, 1.0)

WHITE = (1.0, 1.0, 1.0, 1.0)
YOUTUBE_RED = (1.0, 0.0, 0.0, 1.0)

RADIUS = 8.0          # --radius: 0.5rem (lg). Cards use rounded-2xl = 16px.
RADIUS_CARD = 24.0    # rounded-2xl scaled up for a 1920 canvas
RADIUS_PILL = 999.0

FONT_DISPLAY = "display"          # Playfair Display 700
FONT_BODY = "body"                # Source Sans 3 400

# --- copy (site wording; sr is primary, en alternative) ----------------------
COPY = {
    "hero": {
        "title": {"sr": "Sedi. Upali. Kreni.", "en": "Sit. Start. Ride."},
        "subtitle": {
            "sr": "Vaša avantura počinje ovde — bez napora, bez granica.",
            "en": "Your adventure starts here — effortless and limitless.",
        },
    },
    "nav": {"reserve": {"sr": "Rezerviši", "en": "Book Now"}},
    "quick": {
        "locations": {"sr": "Više lokacija", "en": "Multiple Locations"},
        "booking": {"sr": "Jednostavna rezervacija", "en": "Easy Booking"},
        "experience": {"sr": "Nezaboravno iskustvo", "en": "Unforgettable Experience"},
    },
    "footer": {
        "tagline": {
            "sr": "Iznajmljivanje e-bicikala u Čačku. Istraži više. Pedaliraj manje.",
            "en": "E-bike rental in Čačak. Explore more. Pedal less.",
        },
    },
    "hosts": {
        "motto": {"sr": "Pronađite svoj put. Uživajte u vožnji.",
                  "en": "Find your path. Enjoy the journey."},
    },
    "logo_tagline": {"sr": "Drive forward. Feel the power", "en": "Drive forward. Feel the power"},
    "channel": {
        "name": {"sr": "Deky Bike", "en": "Deky Bike"},
        "kicker": {"sr": "YouTube kanal", "en": "YouTube channel"},
        "subscribe": {"sr": "Pretplati se", "en": "Subscribe"},
        "subscribed": {"sr": "Pretplaćeno", "en": "Subscribed"},
        "url": {"sr": "deky.bike", "en": "deky.bike"},
        "handle": {"sr": "@dekybike", "en": "@dekybike"},
        "place": {"sr": "Čačak, Srbija", "en": "Čačak, Serbia"},
    },
    "stats": {
        "subscribers": {"sr": "pretplatnika", "en": "subscribers"},
        "followers": {"sr": "pratilaca", "en": "followers"},
        "visits": {"sr": "poseta sajtu", "en": "site visits"},
        "clients": {"sr": "zadovoljnih klijenata", "en": "happy clients"},
        "rating": {"sr": "prosečna ocena", "en": "average rating"},
        "instagram": {"sr": "Instagram", "en": "Instagram"},
        "facebook": {"sr": "Facebook", "en": "Facebook"},
    },
    "routes": {
        "gorge": {"sr": "Ovčarsko-kablarska klisura", "en": "Ovčar-Kablar Gorge"},
        "morava": {"sr": "Obala Zapadne Morave", "en": "West Morava riverside"},
        "jelica": {"sr": "Planina Jelica", "en": "Jelica Mountain"},
        "monasteries": {"sr": "Manastiri", "en": "Monasteries"},
        "city": {"sr": "Gradska tura: Srce Čačka", "en": "City tour: Heart of Čačak"},
    },
}

# --- channel statistics (PLACEHOLDERS - replace with real numbers) -----------
STATS = {
    "subscribers": 12500,
    "followers": 24800,
    "instagram": 16300,
    "facebook": 8500,
    "visits": 58000,
    "clients": 1250,
    "rating": 4.9,
}


def fmt_int(n, lang="sr"):
    """12500 -> '12.500' (sr) / '12,500' (en)."""
    s = f"{int(round(n)):,}"
    return s.replace(",", ".") if lang == "sr" else s


def fmt_compact(n, lang="sr", decimals=1):
    """12500 -> '12,5K' (sr) / '12.5K' (en)."""
    if n >= 1_000_000:
        v, suf = n / 1_000_000, "M"
    elif n >= 1000:
        v, suf = n / 1000, "K"
    else:
        return fmt_int(n, lang)
    s = f"{v:.{decimals}f}".rstrip("0").rstrip(".")
    if lang == "sr":
        s = s.replace(".", ",")
    return s + suf


def fmt_decimal(x, lang="sr", decimals=1):
    s = f"{x:.{decimals}f}"
    return s.replace(".", ",") if lang == "sr" else s


def palette_report():
    names = ["BACKGROUND", "FOREGROUND", "PRIMARY", "SECONDARY", "ACCENT", "MUTED",
             "MUTED_FG", "BORDER", "WARM_CREAM", "WARM_SAND", "HERO_OVERLAY", "DARK_BG"]
    g = globals()
    return {n: to_hex(g[n]) for n in names}
