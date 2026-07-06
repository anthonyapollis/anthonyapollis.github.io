"""Simplify the SA district geojson: round coords to 2 dp, drop near-duplicate
consecutive points, drop tiny rings. Cuts 22MB -> well under 1MB while staying
visually accurate at country scale."""
import json
from pathlib import Path

OUT = Path(__file__).parent / "out"
geo = json.loads((OUT / "sa_provinces.geojson").read_text(encoding="utf-8"))

PREC = 2  # decimal degrees (~1.1 km)


def simplify_ring(ring):
    out = []
    last = None
    for pt in ring:
        p = [round(pt[0], PREC), round(pt[1], PREC)]
        if p != last:
            out.append(p)
            last = p
    # ring must have >=4 points and be closed
    if len(out) >= 4:
        if out[0] != out[-1]:
            out.append(out[0])
        return out
    return None


def simplify_geom(geom):
    t = geom["type"]
    if t == "Polygon":
        rings = [simplify_ring(r) for r in geom["coordinates"]]
        rings = [r for r in rings if r]
        return {"type": "Polygon", "coordinates": rings} if rings else None
    if t == "MultiPolygon":
        polys = []
        for poly in geom["coordinates"]:
            rings = [simplify_ring(r) for r in poly]
            rings = [r for r in rings if r]
            if rings:
                polys.append(rings)
        return {"type": "MultiPolygon", "coordinates": polys} if polys else None
    return geom


for feat in geo["features"]:
    g = simplify_geom(feat["geometry"])
    if g:
        feat["geometry"] = g
    # strip heavy unused props
    feat["properties"] = {"name": feat["properties"]["name"]}

small = json.dumps(geo, separators=(",", ":"))
(OUT / "sa_provinces_simple.geojson").write_text(small, encoding="utf-8")
print(f"Simplified geojson: {len(small)/1024:.0f} KB (was ~22 MB)")
