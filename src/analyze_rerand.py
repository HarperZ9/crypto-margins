"""Compare a fixed secret's score spread across re-randomized lattices with the
across-secret spread on a single lattice, from rerandomize_check logs.

Usage: python src/analyze_rerand.py results/logs/rerand_s11.log [...]
"""
import json
import sys

import numpy as np

for path in sys.argv[1:]:
    rows = [json.loads(l) for l in open(path) if l.startswith('{"round"')]
    fx = np.array([r["fixed_ratio"] for r in rows])
    acr = np.array([r["across_q10_q50_q90"] for r in rows])
    q = np.quantile(fx, [0.1, 0.5, 0.9])
    print(f"{path}: rounds={len(fx)}")
    print(f"  fixed secret over lattices: mean={fx.mean():.3f} std={fx.std(ddof=1):.3f} "
          f"q10/q50/q90={q[0]:.2f}/{q[1]:.2f}/{q[2]:.2f} min={fx.min():.2f} max={fx.max():.2f}")
    m = np.median(acr, 0)
    print(f"  across secrets, per lattice (median of q10/q50/q90): {m[0]:.2f}/{m[1]:.2f}/{m[2]:.2f}")
    print(f"  across-secret spread implied std ~ {(m[2]-m[0])/2.563:.3f} (normal q10-q90 width)")
