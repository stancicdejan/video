"""Scene registry. Every module named sNN_*.py in this package is a scene
(see deky_reel.engine.core for the scene contract)."""
import importlib
import os
import pkgutil


def load_scenes():
    pkg_dir = os.path.dirname(__file__)
    mods = []
    for info in sorted(pkgutil.iter_modules([pkg_dir]), key=lambda m: m.name):
        if info.name[:1] == "s" and info.name[1:3].isdigit():
            mods.append(importlib.import_module(f"{__name__}.{info.name}"))
    return mods
