"""Render the Deky Bike showreel.

    python -m deky_reel.render                       # 480p preview -> out/
    python -m deky_reel.render --quality full        # 1920x1080 master
    python -m deky_reel.render --stills 0.5,3.2      # PNG stills for review
    python -m deky_reel.render --sheet 24            # contact sheet of 24 frames
    python -m deky_reel.render --range 3:6           # render only 3 s..6 s
    python -m deky_reel.render --only s03 --stills 4 # one scene in isolation

Frames are rendered in parallel worker processes and piped, in order, as raw
RGB into ffmpeg (H.264, yuv420p, faststart).
"""
import argparse
import multiprocessing as mp
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

from . import brand
from .engine import fx, text
from .engine.core import Compositor, RenderContext
from .scenes import load_scenes

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

_COMP = None


def build(opts):
    R = RenderContext(quality=opts["quality"], fps=opts["fps"], lang=opts["lang"],
                      motion_blur=opts["mblur"], grain=opts["grain"],
                      vignette=opts["vignette"], copy=brand.COPY, stats=brand.STATS)
    post = fx.default_post if opts["post"] else None
    scenes = load_scenes()
    if opts.get("only"):
        keep = [k.strip() for k in opts["only"].split(",")]
        scenes = [s for s in scenes if any(s.__name__.rsplit(".", 1)[-1].startswith(k) for k in keep)]
    return Compositor(scenes, R, background=brand.BACKGROUND, post=post)


def _init(opts):
    global _COMP
    _COMP = build(opts)


def _render(index):
    return index, _COMP.render_frame(index).tobytes()


def options(a):
    return dict(quality=a.quality, fps=a.fps, lang=a.lang, mblur=a.mblur, grain=a.grain,
                vignette=a.vignette, post=not a.no_post, only=a.only)


def render_video(a):
    opts = options(a)
    comp = build(opts)
    R = comp.R
    f0, f1 = 0, R.frames
    if a.range:
        s0, s1 = (float(v) for v in a.range.split(":"))
        f0, f1 = int(round(s0 * R.fps)), min(R.frames, int(round(s1 * R.fps)))
    out = a.out or os.path.join(ROOT, "out", f"deky_bike_showreel_{a.quality}_{a.lang}.mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{R.px_w}x{R.px_h}", "-r", str(R.fps), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", str(a.crf), "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-movflags", "+faststart",
           "-metadata", "title=Deky Bike - motion showreel", out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    n = f1 - f0
    workers = max(1, a.workers)
    if workers == 1:
        _init(opts)
        it = (_render(i) for i in range(f0, f1))
        pool = None
    else:
        pool = mp.get_context("fork").Pool(workers, initializer=_init, initargs=(opts,))
        it = pool.imap(_render, range(f0, f1), chunksize=2)
    done = 0
    for idx, buf in it:
        ff.stdin.write(buf)
        done += 1
        if done % 30 == 0 or done == n:
            el = time.time() - t0
            sys.stderr.write(f"\r  frame {done}/{n}  {el:5.1f}s  ({done / max(el, 1e-6):.1f} fps)")
            sys.stderr.flush()
    sys.stderr.write("\n")
    if pool:
        pool.close()
        pool.join()
    ff.stdin.close()
    ff.wait()
    if ff.returncode != 0:
        raise SystemExit("ffmpeg failed")
    print(out)
    return out


def render_stills(a):
    opts = options(a)
    comp = build(opts)
    R = comp.R
    out_dir = a.out or os.path.join(ROOT, "out", "stills")
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for s in a.stills.split(","):
        t = float(s)
        idx = min(R.frames - 1, int(round(t * R.fps)))
        img = comp.render_frame(idx)
        p = os.path.join(out_dir, f"still_{t:05.2f}s_{a.quality}_{a.lang}.png")
        Image.fromarray(img).save(p)
        paths.append(p)
        print(p)
    return paths


def render_sheet(a):
    """Grid of evenly spaced frames with timestamps (for reviews)."""
    opts = options(a)
    comp = build(opts)
    R = comp.R
    n = a.sheet
    if a.range:
        s0, s1 = (float(v) for v in a.range.split(":"))
    else:
        s0, s1 = 0.0, R.duration
    times = [s0 + (s1 - s0) * (i + 0.5) / n for i in range(n)]
    cols = 4 if n > 6 else n
    rows = (n + cols - 1) // cols
    tw, th = R.px_w // 2, R.px_h // 2
    sheet = Image.new("RGB", (cols * tw, rows * (th + 22)), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    for i, t in enumerate(times):
        idx = min(R.frames - 1, int(round(t * R.fps)))
        im = Image.fromarray(comp.render_frame(idx)).resize((tw, th), Image.LANCZOS)
        x, y = (i % cols) * tw, (i // cols) * (th + 22)
        sheet.paste(im, (x, y))
        d.text((x + 6, y + th + 4), f"t={idx / R.fps:5.2f}s  f{idx}", fill=(230, 230, 230))
    out = a.out or os.path.join(ROOT, "out", f"sheet_{a.lang}.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    print(out)
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--quality", default="preview", choices=["preview", "720p", "full"])
    p.add_argument("--lang", default="sr", choices=["sr", "en"])
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--mblur", type=int, default=6, help="motion-blur sub-frames (1 = off)")
    p.add_argument("--grain", type=float, default=0.022)
    p.add_argument("--vignette", type=float, default=0.22)
    p.add_argument("--no-post", action="store_true")
    p.add_argument("--crf", type=int, default=18)
    p.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2)))
    p.add_argument("--range", help="seconds a:b")
    p.add_argument("--stills", help="comma separated times (s) to export as PNG")
    p.add_argument("--sheet", type=int, help="contact sheet with N frames")
    p.add_argument("--only", help="comma separated scene module prefixes, e.g. s02,s03")
    p.add_argument("--out")
    a = p.parse_args(argv)
    if a.stills:
        render_stills(a)
    elif a.sheet:
        render_sheet(a)
    else:
        render_video(a)


if __name__ == "__main__":
    main()
