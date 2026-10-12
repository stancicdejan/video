# Deky Reel engine: API reference

A small frame-by-frame 2D motion engine, written for this showreel instead of
Remotion/After Effects: **pycairo** (vector drawing), **HarfBuzz** (shaped,
kerned typography as real glyph paths), **numpy** (post FX), **ffmpeg**
(encoding). Every frame is a pure function of time.

## Coordinate system and scenes

* Design space is **1920x1080** at any output quality. The root context is
  pre-scaled, so scene code always uses 1920x1080 coordinates and sizes.
  `--quality preview` renders 854x480, `full` renders 1920x1080.
* Time `t` is **global seconds** (0.0 to 15.0). 30 fps, 450 frames.
* A scene is a module `deky_reel/scenes/sNN_name.py` exposing
  `START`, `END` (global seconds, END exclusive), `LAYER` (z-order; higher is on
  top) and `render(ctx, t, R)`. All scenes whose window contains `t` are drawn
  each frame, lowest `LAYER` first. Overlapping windows = transitions.
* `R` (RenderContext): `R.scale` (device px per design px), `R.px_w/px_h`,
  `R.fps`, `R.lang` (`"sr"`/`"en"`), `R.t("hero.title")` localized copy from
  `deky_reel/brand.py:COPY`, `R.stats` (numbers), `R.frame`.
* The compositor clears every frame to `brand.BACKGROUND` (cream) and applies
  vignette + film grain after all scenes. Motion blur = sub-frame accumulation
  (`--mblur 6`, the default), so **render must be deterministic in t** (no randomness that
  is not seeded by constants).

## Modules

```python
from deky_reel import brand as B
from deky_reel.engine import draw, ease, fx, icons, images, logo, text, ui
from deky_reel.engine.color import hsl, hex_, with_alpha, mix, lighten, darken
```

### brand (site design tokens, copy, stats)
Colors (rgba tuples) from the site's `index.css`: `BACKGROUND` cream #FFFCEB,
`FOREGROUND` deep forest #1B3222, `PRIMARY` #2F6A40, `SECONDARY` sage #84B783,
`ACCENT` warm yellow #F7C85A, `MUTED`, `MUTED_FG`, `BORDER`, `CARD`,
`WARM_CREAM`, `WARM_SAND`, `HERO_OVERLAY`, `DARK_BG`, `DARK_CARD`,
`LOGO_LIME`, `LOGO_GREEN`, `WHITE`, `YOUTUBE_RED`. Radii: `RADIUS_CARD` 24.
Number formatting: `B.fmt_int(12500, R.lang)` -> `12.500` / `12,500`;
`B.fmt_compact(12500, R.lang)` -> `12,5K` / `12.5K`; `B.fmt_decimal(4.9, R.lang)`.
Stats: `R.stats["subscribers"|"followers"|"instagram"|"facebook"|"visits"|"clients"|"rating"]`.

### ease
`clamp, lerp, progress(t, start, dur) -> 0..1`, `remap(v, a0, a1, b0, b1)`.
Curves (take 0..1, clamp): `linear, in_/out_/in_out_ sine|quad|cubic|quart|quint|expo|circ|back`,
`out_elastic, out_bounce, spring(t, damping=.42, freq=4.2), smoothstep(e0,e1,x)`,
`bezier(x1,y1,x2,y2)` factory, presets `site_ease_out` (Tailwind ease-out),
`snappy` (cubic-bezier(.16,1,.3,1)), `camera` (cubic-bezier(.65,0,.35,1)).
`ease.get("out_expo")` resolves names.
Helpers: `anim(t, start, dur, a, b, ease)`, `keyframes(t, [(t0, v0), (t1, v1, ease), ...])`
(values may be tuples), `stagger(t, start, i, step, dur, ease)`,
`pulse(t, start, dur)` (0->1->0), `window(t, t_in, t_out, fade_in, fade_out)`.

### draw (cairo helpers; ctx is a cairo.Context in design space)
* Context managers: `saved(ctx)`, `transform(ctx, x, y, scale, rot, pivot, sx, sy)`,
  `group(ctx, alpha, operator)` (isolated layer + opacity/blend),
  `masked(ctx, mask_fn, alpha, invert)` (keep content where `mask_fn(ctx)` paints),
  `clipped(ctx, path_fn)`.
* Operators: `over add screen multiply overlay soft_light color_dodge lighten darken dest_in dest_out`.
* Offscreen/blur: `off = draw.offscreen(R, match=ctx, region=None)` draws with ctx's current
  transform (camera, page scale); `off.blur(radius)` (radius in ctx user units);
  `off.paint(ctx, alpha, operator)`. Shortcuts: `blurred(ctx, R, radius, draw_fn, alpha, operator, bbox=(x, y, w, h))`,
  `glow(ctx, R, radius, draw_fn, alpha, bbox=...)`, `soft_shadow(ctx, R, path_fn, blur, dx, dy, color)`.
  `off.motion_blur(length, axis=0|1)` = directional streak blur (user units).
  Always pass `bbox` (user units) to `blurred`/`glow` when the effect is local: only that area
  (padded by 3x radius) is processed, which is many times faster than a full-frame blur.
  soft_shadow computes its own bbox. All of them respect the current transform.
* Paths: `rounded_rect(ctx,x,y,w,h,r)`, `pill`, `circle(ctx,cx,cy,r)`, `polygon(ctx, pts)`,
  `smooth_polyline(ctx, pts, tension)` (Catmull-Rom), `star`, `arc_path`.
* Paint: `fill(ctx, color)`, `stroke(ctx, color, width, cap, join, dash)`,
  `paint(ctx, color_or_pattern, alpha, operator)`, `fill_rect(ctx,x,y,w,h,color_or_pattern)`,
  `linear_gradient(x0,y0,x1,y1, [(off, color), ...])`, `radial_gradient(cx,cy,r, stops)`.
* Trim paths (draw-on): `fp = draw.FlatPath.from_fn(ctx, path_fn)` or `FlatPath.from_points(pts)`;
  `ctx.new_path(); fp.emit(ctx, start_frac, end_frac); draw.stroke(...)`;
  `fp.point_at(frac) -> (x, y, angle_rad)`; `fp.length`. Shortcut:
  `trim_stroke(ctx, path_fn, start, end, color, width)`.

### text (HarfBuzz-shaped vector type)
Font keys: `display` (Playfair Display 700), `display-regular` (400), `display-black` (900),
`display-italic`, `display-bold-italic`, `body` (Source Sans 3 400), `body-light` (300),
`body-semibold` (600), `body-bold` (700), `body-black` (900).
* `lay = text.layout(font_key, size_px, string, tracking=px, features=None)` (cached).
  Metrics: `lay.width, lay.ascent, lay.descent, lay.cap_height, lay.x_height, lay.glyphs, lay.word_count, lay.word_spans()`.
  Each glyph: `.x, .advance, .char, .index, .word, .is_space`.
* `lay.draw(ctx, x, y, color, align="left|center|right", valign="baseline|cap-center|x-center|top|bottom|middle", per_glyph=fn, stroke=None, stroke_width=0)`.
  `per_glyph(g, n) -> dict(dx, dy, scale|sx|sy, rot (deg), alpha, color, pivot="center|baseline")`.
* `lay.path(ctx, x, y, align, valign, per_glyph)` appends outlines (use as clip/mask, text-as-window).
* `lay.origin(...)`, `lay.bbox(...)`. `text.fit_size(font, s, max_w, size)`.
  `text.tabular()` features for counters (tabular lining figures).

### images (natural photography)
`images.draw_image(ctx, R, path, x=0, y=0, w=1920, h=1080, zoom=1.0, focus=(fx, fy), pan=(dx, dy), rot=0, alpha=1, grade=images.NATURAL, blur=0, radius=0, clip=True, fit="cover"|"contain")`
cover-fits a photo into a rect. Ken Burns = animate `zoom` (>=1), `focus`
(image point 0..1 kept at rect centre; clamped so no edges show) and `pan`.
`blur` is design px (pre-blurred, cached; animate between a few values).
`grade` dict keys: exposure (stops), contrast, saturation, warmth, tint, lift, gamma.
Default `NATURAL` is a light warm grade; keep photos natural.
`images.draw_image_at(ctx, R, path, cx, cy, width, rot, alpha)` draws a whole image.

### logo (the Deky Bike logo, split into parts)
`logo.draw_logo(ctx, R, cx, cy, width, alpha=1, per_part=None, parts=None, color=None)`:
(cx, cy) is the centre of the logo's visible content box, `width` its width in design px
(content aspect is 846x765, so height = width * 0.904).
Parts (back to front): `diamond, mountains, debris, rider, wordmark, bar, pennant, tagline`,
plus per-letter `letter0..letter7` for D,E,K,Y,B,I,K,E (use instead of `wordmark`).
`per_part(name) -> dict(dx, dy, scale, rot, pivot=(src_x, src_y), alpha, sx, sy, color)` or None to skip.
`color=(1,1,1)` renders a flat silhouette (white logo on footage).
`logo.draw_part(ctx, R, name, cx, cy, width, alpha, dx, dy, scale, rot, pivot, sx, sy, color)`.
Geometry for vector effects aligned with the raster logo (source px, map with
`logo.to_design(pt, cx, cy, width)` / `logo.path_in_design(pts, cx, cy, width)`):
`DIAMOND_PATH` (centre line of the diamond band, draw-on order), `DIAMOND_BAND` (12 px), `DIAMOND_KITE` (the full kite shape the band implies, used by `transitions.diamond`),
`RIDGE` (mountain silhouette polyline), `RIDER_POLY`, `PENNANT_POLY`, `ANCHORS`.
Tip: reveal the raster diamond by masking it with a thick trim stroke along `DIAMOND_PATH`.

### icons (Lucide, same set as the site)
`icons.draw(ctx, name, cx, cy, size, color, stroke_width=2.0 (24-grid), progress=1.0, fill=None, rot, scale)`;
`progress < 1` draws the icon on. Names: youtube instagram facebook globe users
star map-pin bike phone mouse-pointer-click mouse-pointer-2 eye trending-up heart
play map mountain battery truck mail clock arrow-right thumbs-up bell bell-ring
user-plus map-pinned route smile award badge-check sparkles chart-line
chart-no-axes-column calendar navigation check circle-play monitor smartphone
laptop sun leaf trees zap gauge chevron-right share-2 message-circle.
`icons.path(ctx, name, cx, cy, size)` appends outlines.
`icons.youtube_badge(ctx, cx, cy, width, bg, fg, alpha)` solid play badge.

### ui (site components + motion language)
* `ui.fade_in_up(t, start, duration=.7, distance=30)` -> (alpha, dy): the site's animation.
* `ui.fade_out_down(t, start, duration, distance)`.
* `ui.underline_bar(ctx, cx, y, progress, color, width=64, height=4, scale=1.6, align)`: section heading bar.
* `ui.pill_button(ctx, cx, cy, label, bg, fg, font, size=34, icon="phone", alpha, scale, press, shadow_R=R)` -> rect.
* `ui.card(ctx, R, x, y, w, h, fill, border, radius=24, shadow=.12, alpha)`: rounded-2xl card.
* `ui.quick_info_bar(ctx, y, h, items, bg, fg, progress)`: sage uppercase bar.
* `ui.counter_value(t, start, dur, target, ease)`; `ui.rolling_digits(ctx, t, start, dur, "12.500", x, y, font, size, color, align)` odometer counter.
* `ui.odometer(ctx, t, value_fn, target, x, y, font, size, color, lang=R.lang, align, valign, settle=0, R=R)`:
  carry-correct mechanical counter (columns roll only on real carries, tight digit window,
  physically sized vertical motion streaks on fast columns when `R` is passed, tabular layout of
  the final formatted number, leading zeros hidden). `value_fn(t)` returns the current value, e.g.
  `lambda t: ui.counter_value(t, 3.0, 1.2, 12500, ease.out_expo)`. Prefer this over `rolling_digits`.
* `ui.word_reveal(ctx, t, start, lay, x, y, color, align, valign, stagger, duration, distance, ease, mask)` masked word slide-up.
* `ui.char_cascade(ctx, t, start, lay, x, y, color, ...)` per-character pop-in.

### fx
`fx.light_leak(ctx, cx, cy, radius, color, intensity, operator="screen")`,
`fx.sun_rays(ctx, cx, cy, length, count, spread, angle, width, color, intensity, phase)`,
`fx.particles(ctx, seed, count, t, area=(x,y,w,h), color, size, drift, alpha)`,
`fx.camera_shake(t, amp, freq, seed) -> (dx, dy, rot)`. Frame post FX
(vignette, grain, `chromatic_split`) run automatically / on numpy arrays.

## Rendering

```
python -m deky_reel.render                      # 854x480 preview, motion blur 6
python -m deky_reel.render --stills 0.5,3.2     # PNGs in out/stills
python -m deky_reel.render --sheet 16 --range 3:6 --out out/sheet.png
python -m deky_reel.render --quality full --lang en
```

## Performance budget
~0.1-0.2 s per 480p frame. Avoid more than ~3 full-frame offscreen blurs per
frame; cache static geometry at module level (FlatPath of constant shapes,
layouts are cached automatically).

### transitions (mask shapes; append a closed path)
`ridge_wipe(ctx, progress, direction="up"|"down", amplitude=160)` (the logo's
mountain ridge as a wipe edge), `iris(ctx, cx, cy, progress)`,
`diamond(ctx, cx, cy, size, rot)` / `diamond_iris(ctx, cx, cy, progress)` (logo diamond),
`diagonal_wipe(ctx, progress, angle)`, `bars(ctx, progress, count, stagger, vertical)`,
`ridge_profile(width, amplitude)` -> points. Use with
`with draw.masked(ctx, lambda c: transitions.ridge_wipe(c, p)): draw_next_scene()`.

### site_mock (the real deky.bike home page, vector-rebuilt from the site source)
`site_mock.draw_browser(ctx, R, x, y, w, h, content=fn, url="deky.bike", radius=18, chrome_h=56, shadow=.28, alpha=1, dark=False)`
draws a browser window; `content(ctx, cx, cy, cw, ch)` fills the viewport.
`site_mock.draw_page(ctx, R, x, y, w, h, scroll=0, t=None, load_start=None, hero_zoom=1, sticky=None)`
draws the home page (transparent header with logo, nav, SR switcher and the
'Rezerviši' pill; hero photo with 50% forest overlay, 'Sedi. Upali. Kreni.',
subtitle and CTA with the site's staggered fade-in-up starting at `load_start`;
sage quick-info bar; 'Zašto baš Deky Bike?' heading, underline and 3 cards).
`scroll` is in CSS px of a 1440x810 viewport; the header turns sticky
(muted bar, slide-down) after the hero, like the site. Building blocks:
`draw_header`, `draw_hero`, `draw_sections`; constants `VIEWPORT_W/H`, `HERO_H`, `HEADER_H`.
`text.wrap(font, size, string, max_width)` -> lines.
`draw.camera(ctx, look_x, look_y, zoom, rot, screen_x=960, screen_y=540)`: virtual camera context
(push-ins, whip pans, flying through a glyph). `ui.trail(ctx, fp, start, end, color, width, head=True, head_color, head_r, glow_R=R)`:
the ride-line motif (trimmed stroke + glowing head dot), returns the head (x, y, angle).
