# Deky Bike: 15 s showreel, final build spec

**Status:** final, approved for parallel build. The spine is the editorial board ("The Numbers Issue"). Grafted onto it are cinematic's depth, light, occlusion and copy-driven camera, and dataviz's earned subscriber, live sum and line-driven counters. Every weakness the judges raised has been fixed: the plain page slide is gone, the hero has been decluttered, the routes montage has been cut, each stat holds for at least 1.2 s, the four counters work differently, and photo scenes have real depth.

**Canvas:** 1920x1080 design space at 30 fps (450 frames), previewed at 854x480. All coordinates below are design px. All times are **global seconds**. `END` is exclusive.

**Engine:** `docs/ENGINE.md`. Every name used below exists in the engine (`draw`, `ease`, `fx`, `icons`, `images`, `logo`, `text`, `transitions`, `ui`, `site_mock`).

---

## 0. Conventions (read first)

* `p(t, a, d)` means `ease.progress(t, a, d)`, and an easing name `E(...)` means `ease.<name>(...)`.
* "Fade-in-up" always means `ui.fade_in_up(t, start, duration, distance)`, which uses the site's Tailwind ease-out.
* "Masked rise" means a per-glyph rise inside a clip rect running from `baseline - 1.05*lay.ascent` to `baseline + 0.30*size`. Each glyph `i` gets `e = out_expo(p(t, T + i*stagger, dur))`, `dy = (1-e)*rise`, and optionally `rot = (1-e)*deg` with `pivot="baseline"`. Spaces are skipped.
* `LN = {"lnum": True}`. **Every Playfair numeral uses `features=LN`.** Playfair's default figures are old-style, and Playfair has **no `tnum`**, so `text.tabular()` does not make it tabular. See §2.7.
* Numbers always come from `R.stats[...]` and are formatted with `B.fmt_int(v, R.lang)` or `B.fmt_decimal(v, R.lang)`. Never hard-code "12.500". Layouts are anchored left or right, so English and real values reflow.
* Copy comes from `R.t(key)` when the key exists in `brand.COPY`. Otherwise it comes from a **scene-local** `COPY = {"sr": ..., "en": ...}` dict.
* **Do not edit** `brand.py`, the engine, `render.py` or other scenes. The only exception is s01, which gets the exit described in §4.1. Cross-scene values are passed only by importing what this spec names: s02 imports from s01, and s05 imports from s04.
* Deterministic rendering: no unseeded randomness. Particles use fixed seeds. Motion blur is the compositor's 6 sub-frames.
* The compositor already paints cream, vignette and grain. **Do not add your own vignette or grain.**

---

## 1. Concept and connecting motif

**"One line, one ride."** The reel plays as a 15-second editorial issue about the Deky Bike YouTube channel. It has huge Playfair numerals, site-faithful cream pages, and natural sunlit photography with real depth.

A single element, **THE LINE**, motivates every cut. THE LINE is the site's 64x4 section-heading underline, drawn at 96x6. Its path through the film:

1. It opens the logo (s01) and becomes the logo's bar.
2. It flies up to become the sunset **horizon**, and opens like an aperture whose lower lip is the logo's **mountain ridge** (T1).
3. The title rises from behind that real horizon. The full stop of "Kreni." flies into the sun and the flare burns into the hosts' page (T2).
4. The logo ridge rises again and carries the gorge in (T3), where the line is the **YouTube progress bar**.
5. We fly through the counter of the last "0" (T4) onto the **rule of an addition sum**. The rule zips off and returns as the **hem of the site's slide-down page** (T5).
6. There it becomes the **browser loading bar** and the **growth line** that drives the visit counter.
7. A click on "Rezerviši" opens an iris onto real riders (T6). The line traces the **real mountain ridge**, and its arc length counts the clients while the number rises from **behind** that ridge.
8. The landscape collapses into the logo's diamond (T7). The line redraws the diamond band, the rider who leapt out in second one lands home, and the line ends as the **underline of deky.bike**.

Every stat is counted differently, and each count is driven by something visible on screen:

| Stat | Counting mechanism |
|---|---|
| Subscribers | An odometer that a "Pretplati se" click carries from 12.499 to 12.500 |
| Followers | A live sum, `IG(t) + FB(t)`, computed every frame |
| Visits | Driven by the growth line's drawn length |
| Clients | Driven by the length of the ridge traced so far |

---

## 2. Global

### 2.1 Palette (site tokens, `brand.py`)

| Token | Hex | Use |
|---|---|---|
| `B.BACKGROUND` | #FFFDEB | Cream pages (s01, s03, s06, s08) |
| `B.FOREGROUND` | #1B3221 | Text on cream and sky; s05 page; hero overlay at α 0.50 |
| `B.PRIMARY` | #2F6A40 | THE LINE on cream, buttons, underline bars, '&', '.' in deky.bike |
| `B.SECONDARY` | #81B780 | Sage. Social icons and labels on the dark s05 page; ripple |
| `B.ACCENT` | #F7C859 | Warm yellow. **Only on dark or photo grounds**, plus small fills (stars, the "+1" chip) |
| `B.CARD` | #FDFCF7 | Cards; s05 numerals |
| `B.MUTED` | #F3F1E2 | Browser chrome; "Pretplaćeno" pill |
| `B.MUTED_FG` | #57755F | Secondary text on cream |
| `B.BORDER` | #E4E2CD | 2 px card borders, browser dots |
| `B.WARM_CREAM` | #FFF8C2 | Glows on cream |
| `B.WARM_SAND` | #E8E4C9 | Far ridge plane (s03, s08) |
| `B.HERO_OVERLAY` | #122116 | Legibility gradients over photos |
| `B.LOGO_GREEN` | #4D9C26 | Logo top-bar colour (s01 exit) |
| `B.YOUTUBE_RED` | #FF0000 | **Single exception:** only the YouTube play badge in s04, so the platform reads instantly. Nowhere else. |
| Burn white | #FFF4D6 `(1.0, 0.957, 0.839)` | T2 flare peak, capped at α 0.92 and never pure white |

Contrast rules:
* Yellow is never used for text or thin lines on cream.
* White text over photos needs a `HERO_OVERLAY` gradient or the site's 50 % `FOREGROUND` overlay.
* Dark `FOREGROUND` type is used on bright skies (s07).

### 2.2 Type scale (font key, size in design px, tracking)

| Role | Font key | Size | Tracking | Notes |
|---|---|---|---|---|
| Hero title | `display` (Playfair 700) | 140 | 0 | Site style: white Playfair 700 |
| Headline names | `display-black` | 150 | 0 | |
| Ampersand | `display-bold-italic` | 150 | 0 | `PRIMARY` |
| Stat numerals | `display-black` + `LN` | 260–300 | 0 | 12.500 at 300, 24.800 at 260, 58.000 at 280, 1.250 at 280 |
| Stat labels | `display-bold-italic` | 64–96 | 0 | |
| URL | `display-black` | 170 | 0 | |
| Kicker | `body-bold` | 34 | 4.76 (0.14 em) | Uppercase |
| UI labels, pills | `body-semibold` | 32–44 | 0 | |
| Secondary numbers | `body-black` | 120 | 0 | Source Sans digits are natively tabular |
| Rating | `body-bold` | 40 | 0 | |
| Browser title | `display` | 64 | 0 | |
| Tagline | `display-bold-italic` | 48 | 0 | |

Size rules:
* **Minimum text size anywhere is 32 px**, except the s05 card name and kickers, which are 34. That is well above the 28 px floor.
* No Playfair 400 is used. Italics are 48 px or larger.
* Strokes are at least 4 px. Motif lines are 6–9 px. Card borders are 2 px.

### 2.3 Easing vocabulary (engine names)

| Intent | Engine | Used for |
|---|---|---|
| Glyph and column rises | `ease.out_expo` | Masked rises, odometer column entry, bar growth |
| Silky UI settle | `ease.snappy` | Optional for UI pops |
| The site's own motion | `ease.site_ease_out` via `ui.fade_in_up` | Kickers, chips, card, tagline |
| Camera moves and wipes | `ease.camera` | T3 ridge rise |
| Shape morphs and flights | `ease.in_out_expo` | s01 bar flight, avatar flight, iris |
| Aperture | `ease.in_out_quart` | T1, T5 page drop |
| Zoom-through | `ease.in_expo` | T4 |
| Launches and exits | `ease.in_cubic`, `ease.in_quad` | Rider launch, period flight, fades out |
| Pops | `ease.out_back(t, s)` | s = 1.7 by default; s = 2.0 for drops and '+'; s = 1.8 for stars |
| Springs | `ease.spring(p, damping, freq)` over a stated duration | "bouncy" = (0.40, 2.0); "pop" = (0.45, 2.2); "firm" = (0.50, 2.0); "card" = (0.50, 2.5) |
| Bumps | `ease.pulse(t, start, dur)` | 0→1→0 sine; landing bumps, press, cursor squash |
| Glide | `ease.in_out_cubic`, `ease.in_out_sine` | Line trims, cursor paths, trails |

### 2.4 Global FX policy

* **Motion blur:** compositor default (6 sub-frames, 180° shutter). Nothing else. Particles are seeded and everything is a pure function of `t`.
* **Grain and vignette:** compositor only.
* **Light, used with restraint:**
  * s02 has one sun leak with one surge on "Upali."
  * The T2 burn (in s03) is the only white-out, capped at #FFF4D6 α 0.92.
  * s04 has a top-right sky leak at 0.22.
  * s07 has a top-left leak at 0.12.
  * The s07 head-dot burst is one small leak.
  * There are **no** leaks on the s05 or s06 pages, and no anamorphic streaks.
* **Depth (no 3D):**

  | Scene | Depth device |
  |---|---|
  | s02 | Title occluded by the real horizon (far plane); riders as the mid plane; dust particles at 1.4x parallax (near); the rider leaping at the lens (nearest) |
  | s03 | Warm-sand far ridge plane, portrait drop shadow, two-speed parallax |
  | s04 | Near particles at 1.4x, the zoom-through |
  | s05 | Three planes (card, text, bokeh) at three drift speeds, plus a rotated card with a heavy shadow |
  | s06 | Card shadows, a photo inside the browser, parallax |
  | s07 | Numeral occluded by the real ridge, near pollen |
  | s08 | Far ridge plane, kite mask |

* **Grade:** natural only. Use `dict(images.NATURAL, **overrides)` with exposure within ±0.12, contrast ≤ 1.06, saturation 0.94–1.04 and warmth ≤ 0.05. No LUTs.
* **Camera shake** happens only on impacts, as `fx.camera_shake(t, amp, freq=40)` with amp decaying linearly to 0 over 0.12 s:

  | Time | Event | Amplitude |
  |---|---|---|
  | 0.42 | Rider lands (s01, built) | 2.5 px |
  | 2.14 | Period pop | 1.5 px |
  | 5.40 | +1 lands | 2 px |
  | 7.67 | Sum lands | 2 px |
  | 9.70 | Visits land | 1.5 px |
  | 11.56 | Clients land | 2 px |
  | 13.46 | Rider lands home | 1.5 px |

* **Chromatic split:** not used. It is not available per scene.
* **Performance:** at most 3 offscreen blurs per frame, always passing `bbox=` to `draw.blurred` / `draw.glow`. Cache FlatPaths and polygons at module level.
* **Final hold:** 14.40–15.00 is completely static (no camera drift). Only the compositor grain moves.

### 2.5 Scene table

The scenes tile 0.00–15.00 with no uncovered frame.

| Key | Module | Title | START | END | LAYER | Overlaps |
|---|---|---|---|---|---|---|
| s01 | `s01_logo_splash` | Logo splash (built) + exit to horizon | 0.00 | 1.36 | 10 | s02 0.88–1.36 |
| s02 | `s02_hero_horizon` | "Sedi. Upali. Kreni." at sunset | 0.88 | 3.04 | 20 | s01 0.88–1.36 · s03 2.80–3.04 |
| s03 | `s03_hosts_channel` | Dejan & Slađana, family YouTube channel | 2.80 | 4.70 | 30 | s02 2.80–3.04 · s04 4.26–4.70 |
| s04 | `s04_subscribers` | 12.500 subscribers (earned +1) | 4.26 | 7.00 | 40 | s03 4.26–4.70 · s05 6.70–7.00 |
| s05 | `s05_followers` | 16.300 + 8.500 = 24.800 | 6.70 | 9.32 | 50 | s04 6.70–7.00 · s06 8.98–9.32 |
| s06 | `s06_site_visits` | 58.000 visits on deky.bike | 8.98 | 11.16 | 60 | s05 8.98–9.32 · s07 10.74–11.16 |
| s07 | `s07_clients` | 1.250 clients, 4,9/5 | 10.74 | 13.40 | 70 | s06 10.74–11.16 · s08 12.80–13.40 |
| s08 | `s08_outro` | End card: logo, deky.bike, Pretplati se | 12.80 | 15.00 | 80 | s07 12.80–13.40 |

### 2.6 Master beat sheet, read windows, hit points

```
0.00 ─ s01 logo builds ─ 0.52 complete ─ 0.52-0.76 sweep ─ 0.88 EXIT
0.88 rider launches at lens (s02) · bar flies to horizon (s01) → 1.04 horizon y=365
1.04-1.34 aperture opens (top line up, logo-ridge lip down)
1.22 / 1.46 / 1.70 "Sedi." / "Upali." / "Kreni." rise from behind the horizon
1.50 "Upali." sun surge · 2.14 full stop pops · 2.62-2.84 full stop flies into the sun
2.80-3.00 flare burns to #FFF4D6 · 3.00-3.32 recedes onto the hosts page
3.04 kicker · 3.12/3.24 "Dejan" / "& Slađana" · 3.48 underline
4.20 text exits · 4.26-4.68 logo ridge rises with the gorge · portrait → avatar
4.56-5.16 odometer to 12.499 · 5.20 CLICK "Pretplati se" · 5.40 = 12.500
6.62 anticipation · 6.70-7.00 through the zero
6.92 Instagram · 7.06 Facebook · 7.14 rule · 7.20 sum drops · 7.67 = 24.800 · 7.95 label
8.80 rule extends · 8.90 rule zips up · 8.98-9.30 cream page drops with its hem
9.24-9.70 growth line drives 58.000 · 10.30 cursor · 10.70 CLICK "Rezerviši"
10.74-11.16 iris onto riders · 10.96-11.56 ridge trace drives 1.250 (rises behind ridge)
11.24 rating chip · 11.46 label
12.80-13.20 landscape collapses into the logo diamond · 12.98 line redraws the band
13.16-13.46 rider lands home · 13.36 deky.bike · 13.74 Pretplati se · 13.92 tagline
14.40-15.00 static hold
```

**Stat read windows.** Each final value must be fully legible and static for at least 1.2 s.

| Stat | Final value lands | First occlusion | Hold |
|---|---|---|---|
| 12.500 | 5.40 | 6.70 (zoom-through; 6.62–6.70 is only −1.5 % scale) | **1.30 s** |
| 24.800 | 7.67 | 9.14 (page hem reaches cap top y 636) | **1.47 s** |
| 58.000 | 9.70 | 10.92 (iris edge touches the numeral) | **1.22 s** |
| 1.250 | 11.56 | 12.80 (exit fade starts) | **1.24 s** |

**Text read windows (at least 0.8 s each):**

| Text | Legible from–to |
|---|---|
| Sedi. | 1.40–2.84 |
| Upali. | 1.65–2.84 |
| Kreni. | 1.90–2.84 |
| Kicker (s03) | 3.15–4.20 |
| Names | 3.32–4.20 |
| "pretplatnika" | 5.0–6.7 |
| "Deky Bike" card | 4.8–6.7 |
| Instagram / Facebook rows | 7.1–9.1 |
| "pratilaca na mrežama" | 8.1–9.1 |
| "poseta sajtu" | 9.3–10.9 |
| Rating chip | 11.45–12.8 |
| Label (s07) | 11.6–12.8 |
| deky.bike | 13.9–15.0 |
| Pretplati se | 14.0–15.0 |
| Tagline | 14.1–15.0 |

**New-element density:** no more than 3 new reading elements in any 1 s window. Each scene's schedule below respects this.

**Hit points (for a future music bed):** 0.42, 0.88, 1.04, 1.22, 1.50, 2.14, 2.84, 3.12, 4.26, 5.20, 5.40, 6.70, 7.67, 8.90, 9.70, 10.70, 11.56, 12.80, 13.46, 14.40.

### 2.7 Shared algorithms

Each scene implements these locally, copying the reference code.

**(a) Cell-grid numerals.** These are jitter-free Playfair counters. They are used by s04, s05 (total), s06 and s07.

```python
LN = {"lnum": True}
DIG, SEP = 0.70, 0.30          # tabular cell widths in em while counting

def grid(final_str, font, size, relax):
    """Cell x-offsets/advances for final_str. relax 0 = tabular cells,
    1 = the real proportional HarfBuzz advances of final_str."""
    lay = text.layout(font, size, final_str, features=LN)
    tab = [(DIG if ch.isdigit() else SEP) * size for ch in final_str]
    prop = [g.advance for g in lay.glyphs]          # 1 glyph per char here
    adv = [a + (b - a) * relax for a, b in zip(tab, prop)]
    xs, x = [], 0.0
    for a in adv:
        xs.append(x); x += a
    return xs, adv, x                                # x = total width

def shown_chars(value, final_str, lang):
    """Current value written into final_str's columns. Leading-zero
    columns -> None (hidden); a separator shows only if a digit left of
    it is visible."""
    digits = [i for i, ch in enumerate(final_str) if ch.isdigit()]
    s = str(int(round(value))).rjust(len(digits), "0")[-len(digits):]
    out = list(final_str)
    first = next((k for k, d in enumerate(s) if d != "0"), len(s) - 1)
    for k, i in enumerate(digits):
        out[i] = s[k] if k >= first else None
    for i, ch in enumerate(final_str):
        if not ch.isdigit():
            out[i] = ch if any(out[j] is not None for j in digits if j < i) else None
    return out
```

Drawing rules:
* Draw each visible char centred in its cell: `gl = text.layout(font, size, ch, features=LN)` at `x0 + xs[i] + adv[i]/2 - gl.width/2`.
* Alignment: left means `x0 = anchor`; right means `x0 = anchor - total`.
* While counting, `relax = 0`. At landing, ease `relax` 0→1 over 0.20 s with `in_out_cubic`. The number visibly tightens into its true kerning, which is the "settle" detail.
* Per-cell transforms (rise, drop) are indexed by cell `i`, from left to right.

**(b) Odometer (s04 only).** The column for digit `k` (units are k=0) has a continuous position:

```
p_k(v) = (floor(v / 10^k) + clamp((v mod 10^k) - (10^k - 1), 0, 1)) mod 10
```

* This carry-correct rule means a column turns only while every lower column rolls from 9 to 0.
* Draw digit `floor(p_k)` at `dy = -frac * pitch` and digit `floor(p_k)+1` (mod 10) at `dy = (1-frac) * pitch`, with `pitch = 1.0 em`. Clip to the numeral window.
* Leading columns (where `v < 10^k`) draw digit 0 as invisible.
* **Spin strip:** when a column turns faster than 90 cells/s (more than 3 cells per frame), draw it through `draw.blurred(ctx, R, 0.10*size, fn, alpha=0.85, bbox=cell_rect)` so it reads as a spinning strip, not flicker. Use at most 3 strip columns at once.

**(c) Photo plates.**
* Always use `images.draw_image(...)`.
* For coordinate maths, use `tx, ty, s = images.cover_transform(iw, ih, x, y, w, h, zoom, focus)`; then `design = (tx + sx*s, ty + sy*s)`.
* Masks or lines that are locked to a photo are built from **source-px** polylines and mapped each frame with that transform.

**(d) THE LINE.**
* Styles:
  * On cream: `PRIMARY`, 6 px, round caps.
  * On photo or dark grounds: `ACCENT`, 6–8 px.
  * Head dot ("rider dot"): radius 10–11, glow via `draw.blurred` with `bbox`.
* Trims use `draw.FlatPath` plus `fp.emit(ctx, a, b)` or `ui.trail(...)`.

### 2.8 Copy (sr primary, en alternative)

| Scene | sr | en | Source |
|---|---|---|---|
| s02 | Sedi. Upali. Kreni. | Sit. Start. Ride. | `R.t("hero.title")` (site H1) |
| s03 | PORODIČNI YOUTUBE KANAL · ČAČAK | FAMILY YOUTUBE CHANNEL · ČAČAK | local |
| s03 | Dejan / & Slađana | Dejan / & Slađana | local (site: "Dejan i Slađana") |
| s04 | pretplatnika | subscribers | `R.t("stats.subscribers")` |
| s04 | Deky Bike | Deky Bike | `R.t("channel.name")` |
| s04 | Pretplati se → Pretplaćeno | Subscribe → Subscribed | `R.t("channel.subscribe")` / `R.t("channel.subscribed")` |
| s04 | +1 | +1 | local |
| s05 | Instagram · Facebook | Instagram · Facebook | `R.t("stats.instagram")` / `R.t("stats.facebook")` |
| s05 | pratilaca na mrežama | social media followers | local |
| s05 | Deky Bike (post card) | Deky Bike | `R.t("channel.name")` |
| s06 | deky.bike | deky.bike | `R.t("channel.url")` |
| s06 | Sedi. Upali. Kreni. · Rezerviši | Sit. Start. Ride. · Book Now | `R.t("hero.title")`, `R.t("nav.reserve")` |
| s06 | poseta sajtu | site visits | `R.t("stats.visits")` |
| s07 | zadovoljnih / klijenata | happy / clients | `R.t("stats.clients").split(" ", 1)` |
| s07 | 4,9 / 5 | 4.9 / 5 | `B.fmt_decimal(R.stats["rating"], R.lang) + " / 5"` |
| s08 | deky.bike | deky.bike | `R.t("channel.url")` |
| s08 | Pretplati se | Subscribe | `R.t("channel.subscribe")` |
| s08 | Istražite više. Manje okrećite pedale. | Explore more. Pedal less. | local, the site repo's `footer.tagline` (sr.ts/en.ts) |

`brand.py` has a different footer wording. Use the repo copy above and keep it local.

---

## 3. Transition contract

### 3.1 Rules

1. **The later scene (higher LAYER) draws the transition.** It masks itself in or draws its own entry overlay. The earlier scene keeps drawing normally until its END. It may animate its *own* content's exit (fade, sink, zoom) as specified, but it never draws the next scene.
2. **An element that persists across a cut is owned by exactly one scene during the overlap.** That ownership is listed below. Ownership switches at a single instant `t_h`: the old owner draws it for `t < t_h`, and the new owner draws it for `t >= t_h`, in the *identical* state at `t_h`.
3. **Shared maths is imported, never re-derived.**
   * s02 imports `CX, CY, LOGO_W, REAR_CONTACT` from s01.
   * s05 imports `zoom_through`, `zero_center` and `zero_counter_path` from s04.
   * Every other handoff is fully defined by the numbers below.

### 3.2 Handoffs

| # | Window | Earlier scene draws | Later scene draws | Carried element (owner switch `t_h`) and exact handoff state |
|---|---|---|---|---|
| T1 s01→s02 | 0.88–1.36 | s01: cream bg; logo minus rider and minus top bar, sinking and fading 0.88–1.08; **vector bar** flying to the horizon 0.88–1.04 | s02: **rider launch** 0.88–1.16 (topmost); aperture 1.04–1.34 with two `PRIMARY` 6 px lines | **Rider** (`t_h` = 0.88): S1 rest pose, i.e. inside `draw.camera(ctx, 960, 540, 1.02)`, `logo.draw_part(ctx, R, "rider", 960, 548, 740, pivot=(505, 535))` with dx = dy = 0, scale 1, rot 0, alpha 1. **Bar** (`t_h` = 1.04): screen rect x −40..1960, y 362..368 (6 px tall, centre y **365**), colour `PRIMARY`. At 1.04 s02 draws both aperture lines coincident at y 365. |
| T2 s02→s03 | 2.80–3.04 | s02: hero; the full stop flies into the sun 2.62–2.84 and is not drawn from 2.84 | s03: flare burn 2.80–3.00 (overlay only), then an opaque page plus a receding overlay 3.00–3.32 | **Sun point (1567, 320)**: s02's sun at the end of its move. s03 centres the burn there. At 3.00 the frame is the s02 hero under #FFF4D6 α 0.92. s03's page appears beneath its own overlay at exactly 3.00. |
| T3 s03→s04 | 4.26–4.70 | s03: page; text exits 4.20–4.40; portrait for t < 4.26 | s04: gorge inside the rising logo-ridge mask 4.26–4.68; **portrait → avatar** flight 4.26–4.72 | **Portrait circle** (`t_h` = 4.26): centre (1330, 540), r 300, hosts.jpg drawn in the rect (cx−r, cy−r, 2r, 2r) with `zoom=1.333, focus=(0.644, 0.50)`, grade `dict(NATURAL, exposure=-0.12, contrast=1.06, saturation=1.0)`, circle clip, ring 6 px `PRIMARY` at radius r+3. |
| T4 s04→s05 | 6.70–7.00 | s04: everything inside the zoom camera `Z(t)` about `C` | s05: itself, masked to the zero's counter contour under the same `Z(t)` | `C = zero_center(R)` ≈ (968.6, 593.8) sr / (967.4, 593.8) en. `Z(t)` = s04's `zoom_through(t)`. The mask is the inner contour of the last '0' of the s04 numeral (x 120, baseline 700, 300 px). |
| T5 s05→s06 | 8.80–9.32 | s05: the rule extends 8.80–8.92 and zips off the top 8.90–9.02; all of s05 sinks +60 px 8.98–9.32 | s06: the cream page drops 8.98–9.30 with an `ACCENT` 6 px hem on its bottom edge | **Rule** owned by s05 until it leaves the frame (y < 0 at 9.02). **Hem** owned by s06. There is no carried numeral; 24.800 stays on s05. |
| T6 s06→s07 | 10.74–11.16 | s06: cursor clicks at 10.70 and stays | s07: circle iris at the click point (600, 528), r 0→1440, with an 8 px `ACCENT` ring on the edge | **Click point (600, 528)** is the cursor tip at 10.62–10.74. |
| T7 s07→s08 | 12.80–13.40 | s07: zooms 1→1.10 about (509.2, 485.1); UI fades out 12.80–12.96 | s08: cream outside the logo **kite** (S 11→1, rot 18°→0) 12.80–13.20; band stroke 12.98–13.40; inside-kite dissolve 13.14–13.38 | Kite, outro logo placement (cx 520, cy 500, w 640): (517.0, 271.2), (750.0, 425.5), (479.9, 818.1), (290.0, 425.5). Pivot (509.2, 485.1). |

---

## 4. Scenes

### 4.1 s01: `s01_logo_splash` (BUILT; modify exit only). START 0.00, END **1.36**, LAYER 10

**Purpose:** the brand splash, unchanged from 0.00 to 0.88. It sets up THE LINE: the underline becomes the bar.

**Keep as is:** everything for `t < 0.88` (assembly to about 0.62, light sweep 0.52–0.76, camera zoom 1.0→1.02 by 0.82, held at 1.02 afterwards).

**Changes:**
1. Set `START, END, LAYER = 0.0, 1.36, 10`. Add `EXIT = 0.88` and `HORIZON_Y = 365.0`.
2. **Rider:** do not draw the rider for `t >= 0.88`. s02 owns it from 0.88 in the identical rest pose. Debris, flecks, dots and sweep are already finished and stay as they are.
3. **Logo exit (0.88–1.08):**
   * For `t >= 0.88`, draw the assembled logo inside the same `draw.camera(ctx, 960, 540, 1.02)`, **without** the rider and **without** step 1 (top bar, vector or raster).
   * Parts: diamond (full, no mask), mountains (clipped `y < BAR_TOP`), debris, `letter0..7`, lower bar, pennant, tagline.
   * Exit transform, with `e = in_quad(p(t, 0.88, 0.20))`: group alpha `1 - e`, scale `1 - 0.04*e` about (960, 596), `dy = +30*e`.
   * Optional blur: the whole group via `draw.blurred(ctx, R, 6*e, fn, bbox=(570, 190, 780, 720))` when `e > 0.02`.
   * Nothing is drawn from 1.08.
4. **Vector bar flight (0.88 ≤ t < 1.04):** drawn in screen space, outside the camera.
   * `q = in_out_expo(p(t, 0.88, 0.16))`.
   * The rect lerps from (582.6, 587.9, w 754.8, h 16.9) to (−40, 362, w 2000, h 6). This is the camera-transformed raster bar at 0.88, so the swap is invisible.
   * Colour `mix(B.LOGO_GREEN, B.PRIMARY, q)`.
   * Corner radius `h/2`.
   * Not drawn for `t >= 1.04`.
5. Background (cream plus warm glow) keeps drawing to 1.36. It is the "outside" of the opening aperture.
6. Add `RIDER_CAM = (960.0, 540.0, 1.02)` at module level for s02.

### 4.2 s02: `s02_hero_horizon`. START 0.88, END 3.04, LAYER 20

**Purpose:** the site's hero line, staged cinematically. The bar is the horizon, and the words rise from behind it. Copy drives the camera:
* "Sedi." (sit): the camera settles.
* "Upali." (start): the sun surges.
* "Kreni." (go): its full stop launches into the sun.

**Imports:** `from deky_reel.scenes import s01_logo_splash as S1`.

**Asset:** `assets/site/hero-home.jpg` (1920x1080).
* `images.draw_image(ctx, R, path, 0, 0, 1920, 1080, zoom=z, focus=(0.0, 0.0), grade=dict(images.NATURAL, exposure=0.06))`.
* With `focus (0, 0)`, `tx = ty = 0` and `s = z`, so source→design is `(x*z, y*z)`.
* `z(t) = ease.keyframes(t, [(1.04, 1.14), (1.72, 1.08, ease.out_cubic), (3.04, 1.065, ease.linear)])`. The settle ends as "Sedi." lands.
* **Sun:** `(1470*z, 300*z)`, which is (1675.8, 342) at 1.04 and (1567, 320) at 2.84.

**Horizon polyline, source px** (measured): (0,280) (60,277) (120,292) (180,293) (240,298) (300,299) (360,300) (420,304) (480,306) (540,310) (600,312) (660,314) (720,316) (780,319) (840,320) (900,325) (960,328) (1020,330) (1080,331) (1140,328) (1200,327) (1260,327) (1320,330) (1440,334) (1560,333) (1620,328) (1680,328) (1740,327) (1800,326) (1860,328) (1920,328).

**SKY polygon (design):** `[(-20,-20), (1940,-20)] + [(x*z, y*z) for x, y in reversed(H)] + [(-20, 280*z)]`. The horizon at the title's left end is ≥ 312 at every z used. Title baseline 285 leaves ≥ 27 px clearance, and the 'p' descender clears by ≥ 14 px.

**Layer stack** (bottom→top), with `t >= 1.04` unless noted:
1. Photo.
2. Site hero overlay: `fill_rect(0, 0, 1920, 1080, with_alpha(B.FOREGROUND, 0.50))`.
3. Sun light: `fx.light_leak(ctx, sx, sy, 440, (1.0, 0.84, 0.52), I(t))`. `I = keyframes [(1.04,0), (1.40,0.45,out_cubic), (1.50,0.36), (1.75,0.75,out_cubic), (2.30,0.40,in_out_sine), (2.84,0.60,in_quad), (3.04,0.60)]`. Sun rays: `fx.sun_rays(ctx, sx, sy, 980, count=7, spread=46, angle=196, width=0.05, color=(1.0,0.86,0.55), intensity=0.15*ease.pulse(t,1.50,0.80), phase=0.8*t)`.
4. Title shadow, clipped to SKY: `draw.blurred(ctx, R, 16, fn, alpha=0.45, bbox=(130,150,1220,210))`, where `fn` draws the title in `FOREGROUND` with dy +6 using the same per-glyph state.
5. **Title**, clipped to SKY (`draw.clipped(ctx, sky_fn)`): `lay = text.layout("display", 140, R.t("hero.title"))`, x 150, baseline 285, `B.WHITE`.
6. Dust (near plate), inside `draw.camera(ctx, 960, 540, 1 + 1.4*(z - 1.065))`: `fx.particles(ctx, 21, 16, t, (0, 380, 1920, 700), (1.0, 0.80, 0.50), (2.0, 5.0), (16, -8), 0.45)`.
7. Full-stop flight and trail (2.62–2.84).
8. Aperture lines (1.04–1.34).
9. Rider launch (0.88–1.16), topmost.

Layers 1–6 are drawn inside the aperture mask while `t < 1.34`. Layers 1–7 get the 2.14 shake.

**Beats:**
* **0.88–1.16, rider leap at the lens:**
  * Inside `draw.camera(ctx, *S1.RIDER_CAM[:2], S1.RIDER_CAM[2])`, set `u = in_cubic(p(t, 0.88, 0.28))`.
  * `logo.draw_part(ctx, R, "rider", S1.CX, S1.CY, S1.LOGO_W, alpha=1 - p(t, 1.06, 0.10), dx=560*u, dy=-360*u, scale=1+1.5*u, rot=-14*u, pivot=S1.REAR_CONTACT)`.
  * At 0.88 this is identical to s01's rest pose. The rider swells toward the lens and exits upper right over the opening hero.
* **1.04–1.34, aperture:**
  * `q = in_out_quart(p(t, 1.04, 0.30))`. Top line `yA = 365 - 375*q`. Lip baseline `yB = 365 + 875*q`. Ridge amplitude `a = 150*min(1, 3*q)`.
  * Lip `edge(x) = yB + dy_u(x)*a`, with `prof = transitions.ridge_profile(2000, 1.0, x0=-40)` giving `(x, dy_u)` and `dy_u ∈ [-1, 0]`.
  * Mask polygon: (−40, yA) → (1960, yA) → (1960, edge_last) → edge points right→left → (−40, edge_first).
  * Stroke `y=yA` and the edge polyline: 6 px `PRIMARY`, round joins.
  * From 1.34: no mask and no lines.
* **Words (masked rise from behind the horizon; the SKY clip does the occlusion):**
  * Word w starts at `T = [1.22, 1.46, 1.70][w]`.
  * Glyph j within the word: `e = out_expo(p(t, T + 0.025*j, 0.40))`, `dy = (1-e)*150`, `rot = (1-e)*6` (`pivot="baseline"`).
  * The last glyph of word 2, '.', is **excluded** here.
* **1.50, "Upali." surge:** the leak and rays keyframes above.
* **2.14–2.44, full stop pop:**
  * `scale = ease.spring(p(t, 2.14, 0.30), 0.40, 2.0)`, pivot at the glyph centre, `WHITE`.
  * Shake 1.5 px from 2.14 to 2.26.
  * Full stop centre: `P0 = (150 + g.x + g.advance/2, 285 - r0)`, with `r0 = 0.5 * glyph-ink width` from the glyph path extents. That is about (1291, 271) with r0 ≈ 14.
* **2.40–2.52:** the full stop's colour goes `WHITE`→`ACCENT`.
* **2.56–2.62, anticipation squash:** sx 1→1.18, sy 1→0.80 (`in_out_sine`), anchored at the dot's bottom.
* **2.62–2.84, flight into the sun:**
  * Replace the glyph with a vector circle.
  * `u = in_cubic(p(t, 2.62, 0.22))`.
  * Position = quadratic Bézier from P0 via (1430, 150) to `sun(t)`.
  * r 14→22, `ACCENT` fill, glow `draw.blurred(r=12, alpha 0.8, screen, bbox around dot)`.
  * Trail: sample the Bézier from `max(0, u - 0.40)` to `u` in 15 segments, 6 px `ACCENT`, alpha ramping 0→1 toward the head.
  * Not drawn for `t >= 2.84`.

**Copy:** `R.t("hero.title")` (sr "Sedi. Upali. Kreni." / en "Sit. Start. Ride."; en word widths are smaller and left-anchored, so no change is needed).

**Entry:** T1. **Exit:** T2. s03 draws the burn over s02 from 2.80; s02 keeps rendering until 3.04.

### 4.3 s03: `s03_hosts_channel`. START 2.80, END 4.70, LAYER 30

**Purpose:** who makes the channel. A portrait of Dejan and Slađana, "family YouTube channel · Čačak", and their names in big Playfair. There are exactly three reading elements.

**Assets:** `assets/site/hosts.jpg` (1600x1200), crop params as in §3.2 T3. Both faces sit inside the circle: Dejan near source (870, 540) and Slađana near (1210, 690).

**2.80–3.00, entry burn (overlay only):**
* `e = in_quad(p(t, 2.80, 0.20))`.
* `fx.light_leak(ctx, 1567, 320, 300 + 2300*e, (1.0, 0.957, 0.839), 0.35 + 0.65*e)`.
* `draw.paint(ctx, (1.0, 0.957, 0.839, 1), alpha=0.92*e)`.

**t ≥ 3.00:** the page (layers 1–8 below), then the overlay `draw.paint(#FFF4D6, alpha=0.92*(1 - out_cubic(p(t, 3.00, 0.32))))` on top.

**Layer stack:**
1. `B.BACKGROUND` plus a radial glow of `WARM_CREAM` α 0.6 at (1340, 540), r 760.
2. **Far ridge plane:**
   * `prof = transitions.ridge_profile(2000, 120, x0=-40 + d)`, with `d = -16*p(t, 3.0, 1.7)`.
   * Polygon: `[(x, 1010 + dy) for x, dy in prof] + [(1960, 1090), (-40, 1090)]`.
   * Fill `WARM_SAND` α 0.55.
3. Portrait shadow: `draw.soft_shadow(ctx, R, circle(cx, cy+0, r), blur=30, dy=16, color=with_alpha(FOREGROUND, 0.18))`.
4. **Portrait:**
   * Centre `cx = 1340 - 10*clamp((t - 3.00)/1.26)`, cy 540. This reaches (1330, 540) at 4.26.
   * `r = 300*(1.06 - 0.06*out_cubic(p(t, 3.00, 0.40)))`.
   * hosts.jpg is clipped to the circle (`draw.clipped`), using the T3 crop.
5. **Ring:** circle at radius r+3.
   * Colour `mix(ACCENT, PRIMARY, k)`, width `10 - 4*k`, with `k = in_out_cubic(p(t, 3.00, 0.50))`.
   * Glow: `draw.glow(radius 14, alpha 0.6*(1-k), bbox = circle box + 20)`.
6. **Kicker**, faded in with `ui.fade_in_up(t, 3.04, 0.45, 30)`:
   * `icons.draw(ctx, "youtube", 164, 318, 48, PRIMARY, 2.0)`.
   * `text.layout("body-bold", 34, KICKER, tracking=4.76)` at x 204, baseline 330, `PRIMARY` (sr width 695, en 667).
7. **Names:**
   * Line 1: "Dejan", `display-black` 150, `FOREGROUND`, x 140, baseline 500. Masked rise starting 3.12, stagger 0.025, 0.45 s, rise 165, rot 8.
   * Line 2:
     * "&" in `display-bold-italic` 150 `PRIMARY` at x 140, baseline 670. Pop: `scale = spring(p(t, 3.24, 0.40), 0.45, 2.2)`, rot `-20*(1 - out_expo(...))`.
     * "Slađana" in `display-black` 150 `FOREGROUND` at x 289.4 (= 140 + 129.4 + 20), baseline 670. Masked rise starting 3.28.
     * Line 2 right edge is 853, clear of the portrait's left edge at 1030.
8. **Underline (THE LINE):** `ui.underline_bar(ctx, 140, 706, out_expo(p(t, 3.48, 0.25)), PRIMARY, 64, 4, 1.5, align="left")`. That is 96x6 at x 140.

**Parallax:** text layers 6–8 shift by `x -4*clamp((t-3.0)/1.7)`. The portrait shift is in its centre formula.

**Exit (4.20–4.40):**
* Kicker, line 1, line 2 and the bar: alpha 1→0 and dy 0→−40, `in_cubic`, 0.20 s each, starting 4.20 / 4.23 / 4.26 / 4.29.
* The portrait and its ring and shadow are **not drawn for t ≥ 4.26**. s04 owns them.
* The page (layers 1–2) stays until 4.70 and is covered by s04's ridge.

**Copy:** `KICKER` sr "PORODIČNI YOUTUBE KANAL · ČAČAK" / en "FAMILY YOUTUBE CHANNEL · ČAČAK". Names are identical in both languages.

### 4.4 s04: `s04_subscribers`. START 4.26, END 7.00, LAYER 40

**Purpose:** stat 01. The channel's video (the gorge) plays. The odometer runs to 12.499, then the viewer's click on "Pretplati se" earns the last subscriber and the columns carry to **12.500**.

**Exports (required by s05):**

```python
def zoom_through(t):            # Z(t)
    if t < 6.62: return 1.0
    if t < 6.70: return 1.0 - 0.015 * ease.in_out_sine(ease.progress(t, 6.62, 0.08))
    return 0.985 + 43.015 * ease.in_expo(ease.progress(t, 6.70, 0.30))
def zero_center(R):             # centre of bbox of the inner contour of the last '0'
def zero_counter_path(ctx, R):  # appends that inner contour, design coords at Z = 1
```

* Numeral layout for these: `text.layout("display-black", 300, F, features=LN)`, x 120, baseline 700, with `F = B.fmt_int(R.stats["subscribers"], R.lang)`.
* Last glyph: split `lay.face.glyph_cmds(g.gid)` at `"M"` commands. The contour with the smaller fill extents is the counter.
* Map points with `(120 + g.x + px*lay.scale, 700 - py*lay.scale)`.
* sr result: bbox (936.3, 488.8)–(1000.8, 698.8), centre (968.6, 593.8).
* `Z ≥ 31` covers the frame, which happens at t ≥ 6.984.

**Asset:** `assets/site/gallery-4.jpg` (800x600, gorge).
* `draw_image(..., zoom=zp, focus=(0.55, 0.42), grade=dict(NATURAL, warmth=0.05, saturation=0.98))`.
* `zp = 1.0 + 0.06*p(t, 4.26, 2.74)` (linear).
* Visible source y ≈ 27–477. The river vanishing point is near design (1236, 391).

**Layer stack:** the whole stack is inside `draw.camera(ctx, C.x, C.y, Z(t), screen_x=C.x, screen_y=C.y)` for t ≥ 6.62. Layers 1–10 are also inside the ridge mask while t < 4.68.
1. Photo.
2. `fx.light_leak(ctx, 1700, 30, 720, (1.0, 0.89, 0.63), 0.22)`.
3. Legibility gradients:
   * Horizontal, x 0→1250, `HERO_OVERLAY` α 0.78 at 0, 0.55 at 0.56, 0 at 1.
   * Bottom, y 820→1080, α 0→0.55.
4. Near particles inside `draw.camera(ctx, 960, 540, 1 + 1.4*(zp - 1))`: `fx.particles(ctx, 44, 14, t, (0, 0, 1920, 1080), (1.0, 0.96, 0.85), (2, 4.5), (8, -18), 0.35)`.
5. **YouTube progress bar (THE LINE):**
   * Visible from 4.70, alpha `p(t, 4.70, 0.2)`.
   * Track `(0, 1040, 1920, 8)` `WHITE` α 0.30.
   * Fill `(0, 1040, 1920*f, 8)` `ACCENT`, `f = 0.08 + 0.56*p(t, 4.70, 2.30)`.
   * Head dot (1920f, 1044), r 10, `ACCENT`, with glow.
6. **Numeral**, `WHITE`, odometer (§2.7b) on the cell grid (§2.7a), left-anchored at x 120, baseline 700, 300 px. Window clip y 460–736.
   * Soft shadow: `draw.blurred(ctx, R, 22, numeral in FOREGROUND dy 8, alpha 0.35, bbox=(100, 440, 1200, 320))`.
7. **Label row:**
   * `icons.youtube_badge(ctx, 172, 816, 96, bg=B.YOUTUBE_RED, fg=B.WHITE)`, scaled by `out_back(p(t, 4.80, 0.30), 1.7)` about (172, 816).
   * Label `R.t("stats.subscribers")` in `display-bold-italic` 96 `ACCENT`, x 244, baseline 850. Masked rise starting 4.86, stagger 0.02, 0.45 s, rise 110. sr width 548, en 495.
8. **Channel card:**
   * `ui.card(ctx, R, 1060, 812, 740, 150, fill=CARD, border=BORDER, radius=24, shadow=0.18)`.
   * Entry 4.50–4.80: alpha `site_ease_out(p)`, scale 0.96→1 about (1430, 887).
   * Avatar slot (1140, 887), r 52, ring 4 px `WHITE`.
   * Name `R.t("channel.name")` in `display` 48 `FOREGROUND`, x 1216, baseline 904 (ends 1439).
   * Pill: right edge anchored at x 1776, cy 887, `ui.pill_button(..., font="body-semibold", size=34, icon="youtube")`. Width = label + 32.3 + 13.6 + 88: 300.5 for "Pretplati se" and 311.0 for "Pretplaćeno". So `cx = 1776 - w/2`.
9. "+1" chip.
10. Cursor.
11. Avatar in flight (4.26–4.72), topmost. From 4.72 it is drawn as part of the card.
12. Ridge edge stroke (4.26–4.68).

**Beats:**
* **4.26–4.68, T3 ridge rise:**
  * `pr = ease.camera(p(t, 4.26, 0.42))`. Draw layers 1–10 inside `draw.masked(ctx, lambda c: transitions.ridge_wipe(c, pr, "up", 170))`.
  * Edge stroke: `base = 1097 - 1284*pr`.
  * Points `(x, base + dy + 170)` for `prof = [(-40, d0)] + transitions.ridge_profile(1920, 170) + [(1960, dN)]`.
  * 6 px `PRIMARY` (the logo's mountain outline).
* **4.26–4.72, portrait → avatar:**
  * `a = in_out_expo(p(t, 4.26, 0.46))`. Centre lerps (1330, 540)→(1140, 887). r lerps 300→52.
  * Same crop params (the rect is the circle's box). Ring width 6→4, colour `PRIMARY`→`WHITE`.
* **4.50:** the card appears.
* **4.56–5.16, odometer to 12.499:**
  * `v = (S-1)*out_quart(p(t, 4.56, 0.60))`, where `S = R.stats["subscribers"]`.
  * Column c (left→right, separator included) enters with `dy += (1 - out_expo(p(t, 4.56 + 0.04*c, 0.45)))*300`.
* **4.80 / 4.86:** badge pop / label rise.
* **4.94–5.18, cursor in:**
  * `icons.draw(ctx, "mouse-pointer-2", tip_x + 20.8, tip_y + 20.8, 64, FOREGROUND, 1.6, fill=WHITE)`. The tip offset is −20.8 at 64 px.
  * The tip follows a quadratic Bézier (1980, 1150) → (1820, 960) → (1640, 900), `in_out_cubic`.
* **5.20, CLICK:**
  * Cursor scale `1 - 0.15*pulse(t, 5.20, 0.14)` about the tip.
  * Pill `press = pulse(t, 5.20, 0.14)`.
  * Ripple: `SECONDARY` 4 px circle at the pill centre, r 0→120, α 0.9→0, 5.20–5.60, `out_cubic`.
* **5.22–5.44, pill becomes Subscribed:**
  * bg `PRIMARY`→`MUTED` with a 2 px `BORDER` stroke; fg `WHITE`→`FOREGROUND`.
  * Label roll, clipped to the pill: the old label and youtube icon go dy 0→−24 with α→0; "Pretplaćeno" and a `check` icon in `PRIMARY` come dy +24→0 with α 0→1. `out_cubic`, 0.22 s.
  * Width: `lerp(w_old, w_new, spring(p(t, 5.22, 0.35), 0.5, 2.0))`, right-anchored.
* **5.22–5.40, carry +1:**
  * `v = (S-1) + out_cubic(p(t, 5.22, 0.18))`. The hundreds, tens and units columns roll together (4→5, 9→0, 9→0).
  * "+1" chip: pill 76x52 `ACCENT` with "+1" in `body-black` 34 `FOREGROUND`. It moves from (1625, 850) to (1625, 760) with `out_cubic` over 5.22–5.62. Scale 0.6→1 with `out_back` over the first 0.12 s. Alpha falls to 0 over 5.45–5.62.
* **5.40, landing:**
  * Changed columns get `dy += 12*pulse(t, 5.40, 0.22)`.
  * Shake 2 px over 5.40–5.52.
  * `relax = in_out_cubic(p(t, 5.42, 0.20))`. The grid tightens from 1134.6 px to 951 px wide.
* **5.46–5.76:** cursor exits: tip += (40, 40)·`in_cubic`, alpha→0.
* **5.40–6.62:** hold. 12.500 is fully legible. The progress bar keeps playing.
* **6.62–7.00:** T4 zoom-through. `Z(t)` is applied to the whole stack.

**Copy:** "pretplatnika" / "subscribers"; "Deky Bike"; "Pretplati se"→"Pretplaćeno" / "Subscribe"→"Subscribed"; "+1".

### 4.5 s05: `s05_followers`. START 6.70, END 9.32, LAYER 50

**Purpose:** stat 02 as an editorial addition. Instagram 16.300 + Facebook 8.500, both counting, and below the drawn rule the total is **literally their live sum**, landing on **24.800**. The dark forest page is the contrast beat.

**Imports:** `from deky_reel.scenes.s04_subscribers import zoom_through, zero_center, zero_counter_path`.

**Entry mask (t < 7.00):**
* Draw everything inside `draw.masked(ctx, m)`, where `m(c)` sets `with draw.camera(c, C.x, C.y, zoom_through(t), screen_x=C.x, screen_y=C.y): zero_counter_path(c, R)` and fills.
* Content alpha inside the mask: `p(t, 6.70, 0.10)`.
* Own entry camera for the whole scene: `draw.camera(ctx, C.x, C.y, 1.25 - 0.25*out_cubic(p(t, 6.70, 0.50)), screen_x=C.x, screen_y=C.y)`. It is active for t < 7.20 and is the identity afterwards. `C = zero_center(R)`.

**Asset:** `assets/site/slika1.jpg` (1200x1600 portrait: two Deky e-bikes in front of a mural in Čačak).
* `draw_image(..., 170, 250, 500, 600, radius=14, zoom=1.06 - 0.06*p(t, 6.70, 2.62), focus=(0.5, 0.62), grade=dict(NATURAL, contrast=1.03))`.
* The hosts crop for the avatar is as in T3.

**Planes and drift**, with `u = p(t, 6.70, 2.62)` (linear):
* Card plane dx = −18u.
* Text plane dx = −8u.
* Bokeh plane dx = −30u.
* Exit sink: every plane gets `dy += 60*in_cubic(p(t, 8.98, 0.34))`.

**Layer stack:**
1. Paint `FOREGROUND`, plus `radial_gradient(1240, 520, 980, [(0, with_alpha(PRIMARY, 0.55)), (1, with_alpha(PRIMARY, 0))])`.
2. **Post card.** Rotated about (420, 540) by `rot = -6 + 3.5*spring(p(t, 6.75, 0.60), 0.5, 2.5)` (ending at −2.5°), with `dy = 20*(1 - out_cubic(p(t, 6.75, 0.50)))`. Coordinates are unrotated:
   * `ui.card(ctx, R, 150, 140, 540, 800, fill=CARD, border=BORDER, radius=24, shadow=0.35)`.
   * Avatar: hosts circle at (210, 198), r 30, ring 3 px `PRIMARY`.
   * "Deky Bike" in `body-bold` 34 `FOREGROUND`, x 256, baseline 210.
   * Photo rect (170, 250, 500, 600), r 14.
   * `heart` icon at (202, 892), 48 px, `FOREGROUND`, 2.0. `message-circle` icon at (266, 892), 48 px.
3. **Bokeh (near plane).** Soft discs drawn as radial gradients, colour α→0 at r, no blur. Each drifts y −20 px/s from 6.70. Positions (x, y, r, colour, α):
   * (760, 180, 18, WARM_CREAM, 0.16)
   * (1830, 120, 12, ACCENT, 0.14)
   * (1540, 990, 22, WARM_CREAM, 0.12)
   * (720, 1010, 14, ACCENT, 0.18)
   * (90, 90, 26, WARM_CREAM, 0.10)
   * (1110, 470, 10, ACCENT, 0.12)
   * (40, 760, 20, WARM_CREAM, 0.12)
   * (1880, 640, 16, ACCENT, 0.12)
   * (600, 600, 12, WARM_CREAM, 0.10)
4. **Text plane** (right column, x 860–1780):
   * **IG row (6.92):**
     * Icon `instagram` at (898, 270), 60 px, `SECONDARY`, 2.0. Scale `out_back(p(t, 6.92, 0.30))`.
     * "Instagram" in `body-semibold` 44 `SECONDARY`, x 948, baseline 285, `fade_in_up(t, 6.92, 0.40, 24)`.
     * Value `IG = round(R.stats["instagram"]*out_quart(p(t, 6.92, 0.54)))`, formatted. `body-black` 120 `CARD`, right-aligned at x 1780, baseline 300. Alpha fades in over 0.2 s.
   * **FB row (7.06):**
     * Icon `facebook` at (898, 440).
     * "Facebook" at x 948, baseline 455.
     * "+" in `display` 110 `ACCENT`, centred x 1430, `valign="cap-center"` at y 430. Pop 7.12: scale `out_back(p, 2.0)` and rot 90→0 over 0.30 s.
     * Value `FB = round(R.stats["facebook"]*out_quart(p(t, 7.06, 0.46)))`, right-aligned at 1780, baseline 470.
   * **Rule (THE LINE), 7.14–7.34:** trimmed (860, 543)→(1780, 543), 6 px `ACCENT`, round caps, `in_out_cubic`.
   * **Total (7.20):**
     * Value `IG + FB` every frame. **Never** a separate tween.
     * Cell grid (§2.7a) of `F = fmt_int(R.stats["followers"])`, right-anchored at 1780, baseline 820, `display-black` 260 + LN, `CARD`.
     * Clipped to y ≥ 549 (it emerges from under the rule).
     * Cell c drops: `dy = -(1 - out_back(p(t, 7.20 + 0.03*c, 0.32), 2.0))*220`.
     * Values are final at 7.52. The drop completes at 7.67.
     * `relax = in_out_cubic(p(t, 7.67, 0.20))`.
     * Landing 7.67: shake 2 px, plus scale pulse `1 + 0.03*pulse(t, 7.67, 0.24)` about (1780, 820).
     * Heart pop on the card: heart filled `PRIMARY`, scale `1 + 0.35*pulse(t, 7.67, 0.30)`, plus six `ACCENT` sparks (r 5) radiating 0→34 px with α 1→0 over 0.30 s.
   * **Label (7.95):** `display-bold-italic` 64 `ACCENT`, right-aligned at 1780, baseline 930. Masked rise, stagger 0.015, 0.45 s. sr width 643, en 634.
5. **T5 rule exit** (the s05 rule, drawn last):
   * 8.80–8.92: x0 860→−10 and x1 1780→1930, `in_out_expo`.
   * 8.90–9.02: y 543→−20, `in_expo`.
   * Not drawn once y < −10.

**Copy:** "Instagram", "Facebook", "+", label sr "pratilaca na mrežama" / en "social media followers", card "Deky Bike".

### 4.6 s06: `s06_site_visits`. START 8.98, END 11.16, LAYER 60

**Purpose:** stat 03. The real deky.bike in a browser card (a callback to the hero). **58.000** is driven by the growth line's drawn length. A cursor books a ride.

**Page drop (T5):** `pdy = -1080*(1 - in_out_quart(p(t, 8.98, 0.32)))`. All page layers 1–4 are translated by `(drift, pdy)`.

**Assets:** `assets/site/hero-home.jpg` inside the browser viewport.

**Layer stack:**
1. `B.BACKGROUND` (full frame, translated) plus a radial glow of `WARM_CREAM` α 0.5 at (960, 540), r 900.
2. **Browser** (drift `-10*p(t, 9.30, 1.86)`):
   * `ui.card(ctx, R, 120, 130, 920, 560, fill=CARD, border=BORDER, radius=24, shadow=0.16)`.
   * Clip to the card's rounded rect:
     * Chrome: `fill_rect(120, 130, 920, 76, MUTED)`. Hairline `(120, 204, 920, 2)` `BORDER`.
     * Dots: r 8 at (160, 168), (188, 168), (216, 168), `BORDER`.
     * Address pill: rounded rect (252, 146, 460, 44), r 22, fill `CARD`, 2 px `BORDER` stroke.
     * `icons.draw("globe", 278, 168, 26, PRIMARY)`.
     * `R.t("channel.url")` in `body-semibold` 32 `FOREGROUND`, x 300, `valign="cap-center"` at y 168.
     * Loading bar (THE LINE): `(120, 206, 920*L, 6)` `PRIMARY`, `L = in_out_cubic(p(t, 9.24, 0.36))`, alpha `1 - p(t, 9.62, 0.13)`.
     * Viewport (120, 206, 920, 484): `draw_image(hero-home, 120, 206, 920, 484, zoom=1.06 - 0.04*p(t, 8.98, 2.18), focus=(0.5, 0.45))`.
     * Overlay `FOREGROUND` α 0.5.
     * Title `text.layout("display", 64, R.t("hero.title"))`, `WHITE`, centred x 580, baseline 410.
     * Pill: `ui.pill_button(ctx, 580, 520 - 4*hov, R.t("nav.reserve"), bg=mix(PRIMARY, WHITE, 0.08*hov), fg=WHITE, font="body-semibold", size=34, icon="phone", press=press, shadow_R=R)`. Size 265x73.
3. **Right column** (drift `-4*p(t, 9.30, 1.86)`):
   * **Label:** `R.t("stats.visits")` in `display-bold-italic` 96 `PRIMARY`, x 1120, baseline 250. It is static on the page.
   * **Growth line:**
     * `GL = [(1120,640), (1230,606), (1340,618), (1450,556), (1560,544), (1670,484), (1790,404)]`.
     * `fp = draw.FlatPath.from_fn(ctx, lambda c: draw.smooth_polyline(c, GL, 0.5))`, cached at first use.
     * `f = in_out_cubic(p(t, 9.24, 0.46))`.
     * `ui.trail(ctx, fp, 0, f, PRIMARY, width=8, head=True, head_color=PRIMARY, head_r=10, glow_R=R)`.
     * Area under the trimmed line, down to y 660: linear gradient y 404→660, `PRIMARY` α 0.16→0.
   * **Numeral:**
     * `V = round(R.stats["visits"]*f)`. It is **driven by the line**.
     * Cell grid right-anchored at x 1800, baseline 960, `display-black` 280 + LN, `FOREGROUND`. Tabular left edge 736; proportional 828.
     * `relax = in_out_cubic(p(t, 9.70, 0.20))`.
     * Landing 9.70: scale `1 + 0.03*pulse(t, 9.70, 0.24)` about (1800, 960); head-dot radius `10 + 6*pulse(t, 9.70, 0.24)`; shake 1.5 px.
4. **Hem:** `fill_rect(0, 1074 + pdy, 1920, 6, ACCENT)` with alpha `1 - p(t, 9.30, 0.15)`.
5. **Cursor** (screen space, not translated):
   * Tip path 10.30–10.62: quadratic Bézier (1240, 1130) → (900, 800) → **(600, 528)**, `in_out_cubic`. Draw as in s04.
   * `hov = in_out_sine(p(t, 10.56, 0.10))`.
   * **Click at 10.70:**
     * `press = pulse(t, 10.70, 0.14)`, and the cursor scales `1 - 0.15*press`.
     * Ripple: 6 px `ACCENT` ring at (600, 528), r 0→80, α 1→0 over 10.70–10.98, `out_cubic`.
   * The cursor remains and is covered by the iris.

**Schedule check:** the page arrives at 9.30 with the browser and label. The numeral and line run 9.24–9.70. The cursor at 10.30 is an actor, not text.

**Copy:** "deky.bike"; "Sedi. Upali. Kreni." / "Sit. Start. Ride."; "Rezerviši" / "Book Now"; "poseta sajtu" / "site visits".

### 4.7 s07: `s07_clients`. START 10.74, END 13.40, LAYER 70

**Purpose:** stat 04 over real riders, who are the clients. **1.250** rises from *behind* the real mountain ridge (an occlusion matte), and its value is driven by the yellow line tracing that ridge. A **4,9 / 5** chip completes the beat.

**Entry (T6, t < 11.16):**
* Draw everything inside `draw.masked` of a circle at (600, 528) with `r = 1440*in_out_expo(p(t, 10.74, 0.42))`.
* Then stroke that circle: 8 px `ACCENT`, `alpha = 1 - ease.smoothstep(0.7, 1.0, p(t, 10.74, 0.42))`.

**Asset:** `assets/site/gallery-1.jpg` (800x600). The "Z20 7014" watermark is at source y ≥ 562 and is **never visible**: with top-anchoring, visible source y ≤ 450.
* `zg = keyframes [(10.74, 1.12), (11.24, 1.00, out_cubic), (13.40, 1.04, linear)]`.
* `draw_image(..., zoom=zg, focus=(0.5, 0.0), grade=dict(NATURAL, saturation=0.94, warmth=0.02, contrast=1.03))`.
* `(tx, ty, s) = images.cover_transform(800, 600, 0, 0, 1920, 1080, zg, (0.5, 0.0))`.

**Skyline, source px** (measured): (0,71) (20,78) (40,87) (60,100) (80,107) (100,118) (120,120) (140,131) (160,149) (180,147) (200,156) (220,153) (240,163) (260,172) (280,180) (300,182) (320,181) (340,181) (360,182) (380,181) (400,196) (420,192) (440,181) (460,176) (480,165) (500,169) (520,156) (540,157) (560,160) (580,162) (600,157) (620,158) (640,152) (660,150) (680,142) (700,139) (720,140) (740,145) (760,146) (780,142) (800,144).
* **SKY polygon:** `[(-20,-20), (1940,-20), (1940, ty+144*s)] + mapped skyline reversed + [(-20, ty+71*s)]`.
* **Clearance:** the highest skyline under the numeral span (x 480–1348) is design y 367 at z 1.0 and 387 at z 1.04. Under the label (x 1380–1761) it is 334 at z 1.0. The numeral baseline (350) and label baselines (220, 300) clear it by ≥ 17 px.

**Exit camera (12.80–13.40):** everything inside `draw.camera(ctx, 509.2, 485.1, 1 + 0.10*in_cubic(p(t, 12.80, 0.60)), screen_x=509.2, screen_y=485.1)`.

**Layer stack:**
1. **Plate:**
   * Photo.
   * Mist: linear gradient y 0→470, `BACKGROUND` α 0.28→0.
   * `fx.light_leak(ctx, 180, 40, 620, (1.0, 0.95, 0.80), 0.12)`.
2. **Numeral**, clipped to SKY (this is the occlusion):
   * `V = round(R.stats["clients"]*f)`.
   * Cell grid left-anchored at x 480, baseline 350, `display-black` 280 + LN, `FOREGROUND`.
   * Cell c rises `dy = (1 - out_expo(p(t, 10.96 + 0.03*c, 0.48)))*320`, from behind the ridge. At dy 320 the cap top (y 472) starts below the valley skyline (about y 480 at zg 1.02), so the digits emerge rather than pop.
   * `relax = in_out_cubic(p(t, 11.56, 0.20))`. The tabular right edge is 1348; proportional is 1176.
   * Landing 11.56: shake 2 px.
3. **Ridge trace (THE LINE):**
   * Build the FlatPath once from source points lifted 3 px: `(x, y-3)`.
   * Draw inside `draw.transform(ctx, tx, ty, scale=s)` with widths divided by s.
   * `f = in_out_sine(p(t, 10.96, 0.60))`.
   * Draw order: under-stroke `FOREGROUND` α 0.30, 12 px, offset +2/s in y (no blur); then body `ACCENT` 8 px round; then head dot r 11 `ACCENT` with a 2.5 px `FOREGROUND` ring and glow.
   * At 11.56 a burst at the head (the right edge): `fx.light_leak(head, 140*pulse(t, 11.56, 0.40), ACCENT, 0.5)`.
4. **Pollen (near):** `fx.particles(ctx, 77, 12, t, (0, 380, 1920, 700), (1.0, 0.98, 0.88), (2, 4), (12, -16), 0.40)`.
5. **Rating chip:**
   * `fade_in_up(t, 11.24, 0.45, 24)`.
   * Pill (480, 56, 421, 72), `FOREGROUND` α 0.88.
   * Stars: `draw.star(ctx, 520 + 50*i, 92, 22, 9.5)` for i in 0..4, fill `ACCENT`. Pop `out_back(p(t, 11.32 + 0.06*i, 0.28), 1.8)`.
   * Star 5 is filled only up to `x ≤ 720 - 22 + 0.9*44`, with a 2.5 px `ACCENT` outline. That makes 4,9 out of 5.
   * Rating text `body-bold` 40 `WHITE` at x 760, `valign="cap-center"` at y 92.
6. **Label:**
   * `display-bold-italic` 72 `FOREGROUND`, x 1380.
   * Line 1 "zadovoljnih" at baseline 220: masked rise starting 11.46.
   * Line 2 "klijenata" at baseline 300: masked rise starting 11.56.
   * Stagger 0.02, 0.45 s.
7. **Exit:** chip, numeral and label use `ui.fade_out_down(t, 12.80, 0.16, 16)`. The photo, line and particles stay and are carried by the exit camera and the kite.

**Copy:** "zadovoljnih" / "klijenata", en "happy" / "clients"; "4,9 / 5" / "4.9 / 5".

### 4.8 s08: `s08_outro`. START 12.80, END 15.00, LAYER 80

**Purpose:** the bookend. The landscape collapses into the logo's diamond, THE LINE redraws the band, and the rider who leapt out at 0.88 lands home. Then deky.bike (underlined), the YouTube **Pretplati se** CTA, the site's footer line, and a **static hold from 14.40 to 15.00**.

**Logo placement:**
* `LX, LY, LW = 520, 500, 640` (k = 0.7565). Content box x 200–840, y 211–789.
* Top-bar rows y 533.7–548.0.
* Wordmark rows y 548.8–629.7.
* Lower-bar bottom y 644.1.
* Rear contact (417.9, 518.5).
* `DPATH = logo.path_in_design(logo.DIAMOND_PATH, 520, 500, 640)` = (324.1,495.8) (290.0,425.5) (495.0,286.3) (557.8,312.0) (619.9,339.2) (750.0,425.5) (690.2,512.5). Band 9.1 px.

**Kite (T7):**
* `K = [(517.0,271.2), (750.0,425.5), (479.9,818.1), (290.0,425.5)]`, pivot `P = (509.2, 485.1)`.
* `e = in_out_cubic(p(t, 12.80, 0.40))`, `S = 11**(1-e)`, `rot = 18*(1-e)`°.
* `kite_t` = K scaled by S and rotated by rot about P. At S 11 / 18° it covers the whole frame (verified ≥ 9).

**Composition:**
* **(A)** `with draw.masked(ctx, kite_t, invert=True): page(ctx, t)`.
* **(B)** Inside the kite, 13.14–13.38: `with draw.masked(ctx, kite_t): page(ctx, t)` through a vertical alpha mask.
  * The front is `y_w = 830 - 570*in_out_cubic(p(t, 13.14, 0.24))`.
  * Alpha is 1 below `y_w + 60` and 0 above `y_w - 60` (linear gradient mask). This dissolves the riders bottom→top.
* **(C)** For t ≥ 13.38, draw `page(ctx, t)` unmasked.
* The band stroke (beat 2) is drawn **on top** of A/B/C.

**`page()` layer stack:**
1. `BACKGROUND` plus a radial glow of `WARM_CREAM` α 0.6 at (520, 500), r 560.
2. **Far ridge plane:** `WARM_SAND` α 0.5, `ridge_profile(2000, 120, x0=-40 - 12*p(t, 12.80, 1.60))` on baseline y 1040, down to 1090. Static from 14.40.
3. Logo parts (beats).
4. Text (beats).
5. Light sweep (beats).

**Beats:**
1. **12.80–13.20:** the kite closes. s07 is visible only inside it.
2. **12.98–13.40, the line redraws the diamond:**
   * Trim along `DPATH` from 0 to `in_out_cubic(p(t, 12.98, 0.28))`, 9.1 px `ACCENT`, round, with `draw.glow(radius 10, bbox=(270, 260, 500, 280))`.
   * Stroke alpha `1 - p(t, 13.24, 0.16)`. The raster `diamond` part has alpha `p(t, 13.20, 0.20)`.
3. **13.14–13.42, mountains:**
   * Clipped to y < 533.7: `dy = (1 - out_back(p(t, 13.14, 0.28), 1.6))*60`, alpha `out_quad(p(t, 13.14, 0.08))`.
   * Top bar: the `mountains` part clipped to rows 533.7–548.0, with `sx = out_expo(p(t, 13.14, 0.20))`, pivot (640, 564).
4. **13.16–13.46, rider lands home** (bookend of the leap):
   * `w = out_cubic(p(t, 13.16, 0.30))`. Offset is a quadratic Bézier (−420, −300) → (−160, −360) → (0, 0) at `w`.
   * `scale = 1.5 - 0.5*w`. `rot = -12*(1 - spring(p(t, 13.16, 0.45), 0.40, 2.2))`. Alpha `p(t, 13.16, 0.06)`. Pivot (505, 535).
   * 13.44: `debris` pops (scale `out_back(p(t, 13.44, 0.16), 2.2)`, same pivot).
   * 13.46: five flecks from (417.9, 518.5), reusing s01's FLECKS velocities ×0.865 with gravity 1903. Shake 1.5 px over 13.46–13.58.
5. **13.24–13.52, letters:** clipped to rows 548.8–629.7. `letter_i` has `dy = (1 - out_expo(p(t, 13.24 + 0.025*i, 0.24)))*82`.
6. **13.30–13.56, lower bar and pennant:**
   * `bar` sx `out_expo(p(t, 13.30, 0.12))`, pivot (640, 692).
   * `pennant` clipped to y ≥ 643.1, `dy = -(1 - out_cubic(p(t, 13.34, 0.22)))*151`.
   * `tagline` alpha `out_cubic(p(t, 13.42, 0.20))`.
7. **13.36, URL:**
   * `text.layout("display-black", 170, R.t("channel.url"))`, x 920, baseline 430, `FOREGROUND`. Glyph 4 ('.') is `PRIMARY`.
   * Masked rise, stagger 0.03, 0.45 s, rise 180. Done by 14.05. Width 767.
8. **13.70–13.98, link underline (THE LINE ends here):** rect (920, 458, 767*`in_out_cubic(p(t, 13.70, 0.28))`, 6), `PRIMARY`, round.
9. **13.74, CTA:**
   * `ui.pill_button(ctx, 920 + w/2, 568, R.t("channel.subscribe"), PRIMARY, WHITE, "body-semibold", 42, icon="youtube", alpha=p(t, 13.74, 0.10), scale=0.7 + 0.3*spring(p(t, 13.74, 0.40), 0.5, 2.0), shadow_R=R)`.
   * `w = layout_width + 39.9 + 16.8 + 88`: 350.5 sr, 323.5 en. Height 90.
10. **13.92, tagline:** `display-bold-italic` 48 `PRIMARY`, x 920, baseline 700, `ui.fade_in_up(t, 13.92, 0.48, 30)`. sr width 791, en 541. Ends at 14.40.
11. **14.02–14.30, light sweep:**
    * Same as s01: a 140 px band at 25°, peak `(1, 1, 0.92)` α 0.55, x 200→840, `in_out_sine`.
    * Masked by `logo.draw_logo(c, R, 520, 500, 640)`.
12. **14.40–15.00, hold:** every animation above is complete. Nothing moves, and the frame works as a thumbnail and loop point.

**Copy:** "deky.bike"; "Pretplati se" / "Subscribe"; "Istražite više. Manje okrećite pedale." / "Explore more. Pedal less."

---

## 5. Signature moments

1. **0.00–1.34, "Everything starts with a line."**
   * The site's underline grows into the logo.
   * The logo's bar flies up to become the sunset horizon and opens like an aperture whose lower lip is the logo's own ridge.
   * Meanwhile the logo's rider leaps at the lens, over the opening landscape.
2. **1.22–3.32, "Sedi. Upali. Kreni."**
   * The site's H1 rises from **behind the real horizon**: the far plane, occluded by the land.
   * "Upali." ignites the sun.
   * The full stop of "Kreni." flies into the sun and the flare burns softly into the cream page, where Dejan and Slađana's portrait settles.
3. **4.94–7.00, the earned subscriber and the zero.**
   * The odometer waits on 12.499. A click on "Pretplati se" carries three columns to **12.500**.
   * A pull-back, then the camera flies through the counter of the last zero into the next page.
4. **6.92–9.30, the sum and the blind.**
   * 16.300 + 8.500 count live.
   * The total, which is their actual per-frame sum, drops out from under the drawn yellow rule onto 24.800.
   * The rule zips off and returns as the hem of the site's slide-down page.
5. **9.24–13.46, line → click → ridge → diamond.**
   * The growth line drives 58.000.
   * A "Rezerviši" click opens an iris onto real riders.
   * 1.250 rises from behind the real mountain ridge as the line traces it.
   * The landscape collapses into the logo's diamond, the line redraws the band, and the rider lands home.

---

## 6. QA checklist

**Timing and contract**
- [ ] Scene windows exactly match §2.5. Every frame 0–449 has at least one active scene: `python -m deky_reel.render --sheet 30` shows no blank cream frame except s01's own frame 0.
- [ ] Handoff stills match with no pop: `--stills 0.88,1.04,1.34,2.84,3.00,4.26,4.72,6.70,7.00,8.98,9.32,10.74,11.16,12.80,13.40`. Rider pose at 0.88, bar rect at 1.04, portrait at 4.26 and zero contour at 6.70 are identical on both sides.
- [ ] No scene draws another scene's carried element outside its ownership window (§3.2).
- [ ] The read windows in §2.6 are met: 12.500 ≥ 1.30 s, 24.800 ≥ 1.47 s, 58.000 ≥ 1.22 s, 1.250 ≥ 1.24 s, and every short line ≥ 0.8 s.
- [ ] No more than 3 new reading elements in any 1 s window.
- [ ] 14.40–15.00 is pixel-static apart from grain (diff the stills at 14.45 and 14.95 with `--grain 0`).

**Numbers**
- [ ] All values come from `R.stats` and are formatted with `B.fmt_int` / `B.fmt_decimal`. sr shows 12.500 · 24.800 · 58.000 · 1.250 · 4,9. en shows 12,500 · 24,800 · 58,000 · 1,250 · 4.9.
- [ ] Every Playfair numeral uses `features={"lnum": True}`. No old-style figures appear anywhere.
- [ ] Counters do not jitter: tabular cells while counting, relaxing over 0.20 s after landing. Right-aligned totals (s05, s06) keep their right edge fixed.
- [ ] The s05 total equals IG(t) + FB(t) on every frame. Check a few mid-count frames.
- [ ] s06 V equals visits × line fraction. s07 V equals clients × traced ridge fraction.
- [ ] s04 shows 12.499 for ≤ 0.10 s before the click (5.16–5.22) and carries correctly: the hundreds, tens and units columns roll together.

**Legibility and brand**
- [ ] No text is under 32 px (34 for kickers and card names). The preview at 854x480 reads at 100 %.
- [ ] Yellow is never used for text or thin lines on cream. White text is always over an overlay or gradient.
- [ ] Diacritics render in both fonts: Č Ć Š Ž Đ đ ć (Slađana, Čačak, Pretplaćeno, mrežama, Rezerviši, Istražite, okrećite).
- [ ] The en render (`--lang en`) fits: no text crosses its column or the portrait or card, and pills spring to their real widths.
- [ ] `YOUTUBE_RED` appears only in the s04 badge.
- [ ] Photos look natural. No visible grade shift. The gallery-1 watermark is never in frame (visible source y ≤ 450).

**Depth and craft**
- [ ] s02 title glyphs are occluded by the horizon while rising, then clear it by ≥ 13 px at rest.
- [ ] s07 numeral cells are occluded by the ridge while rising, then clear it by ≥ 13 px at rest.
- [ ] Particles and bokeh move at different speeds from their plates: 1.4x parallax in s02 and s04; three drift planes in s05.
- [ ] Every Ken Burns move is continuous. No photo edge or EXTEND_PAD smear is ever visible.
- [ ] Shake happens only at the impacts listed in §2.4.

**Performance and determinism**
- [ ] No more than 3 offscreen blurs per frame, all with `bbox`. Average ≤ 0.2 s per 480p frame (`--range a:b` timing per scene).
- [ ] No unseeded randomness. Two renders of the same frame are byte-identical.
- [ ] Each module renders standalone: `python -m deky_reel.render --only sNN --stills <mid-scene t>`. s05 standalone needs s04 importable.

---

## Appendix A: measured geometry

| Item | Measurement |
|---|---|
| s01 logo | CX 960, CY 548, W 740 (k 0.8747); content box x 590–1330, y 213–883; screen bar at 0.88 (camera 1.02) x 582.6–1337.4, y 587.9–604.8 |
| Hero (s02) | Horizon at screen x 960 for z 1.14 is y 365 (= HORIZON_Y). Sun (1470z, 300z). Title `display` 140: sr width 1160 (x 150–1310), en 967; cap 99; descent 35; '.' glyph x 1122.4 (adv 37.8) relative to the origin. |
| s03 | Kicker sr 695 / en 667 at 34 px, tracking 4.76. "Dejan" 418, "Slađana" 564, "&" 129 at 150 px. |
| s04 | "12.500" at 300 px LN: width 951, cap 212; tabular width 1134.6; last '0' at x 746.1, adv 204.9; counter bbox (relative to x 120, baseline 700) (936.3, 488.8)–(1000.8, 698.8). "pretplatnika" 548, "subscribers" 495 at 96 px. "Deky Bike" 48 px = 223. |
| s05 | "16.300" 362 and "8.500" 298 at Source Sans Black 120. "24.800" at 260 LN = 879 (cap 184). Label sr 643 / en 634 at 64 px. |
| s06 | "58.000" at 280 LN = 972 (cap 198); tabular 1064. "poseta sajtu" 518 / "site visits" 401 at 96 px. Hero title at 64 = 530. |
| s07 | "1.250" at 280 LN = 696; tabular 868. "zadovoljnih" 381, "klijenata" 289 at 72 px. Rating text 105 at 40 px. |
| s08 | "deky.bike" at 170 = 767 (cap 120). "Pretplati se" 206 / "Subscribe" 179 at 42 px. Tagline at 48: sr 791 / en 541. |
| Playfair 900 LN digit advances (em) | 0 .683 · 1 .412 · 2 .566 · 3 .575 · 4 .560 · 5 .544 · 6 .638 · 7 .525 · 8 .608 · 9 .638 · '.' .282 |
