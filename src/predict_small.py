"""Estimator predictions for small ML-KEM-shaped LWE (q=3329, CBD(eta) secret and error).

Prints the predicted uSVP block size and lattice dimension for each n, so the
experiment in usvp_concrete.py can be sized against something it can run.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vendor" / "lattice-estimator"))
from estimator import LWE, ND, RC  # noqa: E402
from estimator.lwe_parameters import LWEParameters  # noqa: E402

for eta in (2, 3):
    for n in range(40, 161, 10):
        p = LWEParameters(n=n, q=3329, Xs=ND.CenteredBinomial(eta), Xe=ND.CenteredBinomial(eta), m=n)
        c = LWE.primal_usvp(p, red_cost_model=RC.ADPS16)
        print(f"eta={eta} n={n} beta={int(c['beta'])} d={int(c['d'])}", flush=True)
