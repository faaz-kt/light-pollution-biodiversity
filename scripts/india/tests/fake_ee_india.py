"""Fake Earth Engine for the smoke tests: the value of a layer at each pixel CENTRE of the requested grid."""
import numpy as np
import truth_india as truth

def fake_fetch(layer, grid):
    w, h = grid["dimensions"]["width"], grid["dimensions"]["height"]
    t = grid["affineTransform"]
    lon = t["translateX"] + (np.arange(w) + 0.5) * t["scaleX"]
    lat = t["translateY"] + (np.arange(h) + 0.5) * t["scaleY"]
    LON, LAT = np.meshgrid(lon, lat)            # row 0 = north
    if layer == "viirs":
        return np.stack([truth.radiance(LAT, LON, y) for y in range(2015, 2026)])
    f = {"built": lambda a, b: truth.built(a, b, 2020), "built2015": lambda a, b: truth.built(a, b, 2015),
         "built2025": lambda a, b: truth.built(a, b, 2025), "tree": truth.tree, "crop": truth.crop,
         "water": truth.water, "elevation_m": truth.elevation, "pop": truth.pop}
    if layer in f:
        return f[layer](LAT, LON)[None]
    if layer.startswith("no2_"):
        return truth.no2(LAT, LON, int(layer[4:]))[None]
    raise ValueError(layer)

import os
_max = int(os.environ.get("FAKE_EE_MAX_CELLS", "0"))
_real_fake_fetch = fake_fetch
def fake_fetch(layer, grid):                     # optionally pretend big tiles time out
    h, w = grid["dimensions"]["height"], grid["dimensions"]["width"]
    if _max and h * w > _max:
        raise RuntimeError("Computation timed out.")
    return _real_fake_fetch(layer, grid)
