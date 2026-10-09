"""Concrete primal uSVP on small ML-KEM-shaped LWE, compared with the estimator.

For each (eta, n): sample A, s, e with CBD(eta), q=3329; build the Kannan
embedding with m = d - n - 1 samples, where d is the estimator's chosen
dimension; run progressive BKZ 2.0 (one tour per block size) and record the
first block size at which the planted vector (e, s, 1) appears in the basis.

Usage: python src/usvp_concrete.py ETA N TRIALS MAX_BETA
Writes results/usvp_eta{ETA}_n{N}.json.
"""
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "vendor" / "lattice-estimator"))

from estimator import LWE, ND, RC  # noqa: E402
from estimator.lwe_parameters import LWEParameters  # noqa: E402
from fpylll import BKZ, GSO, IntegerMatrix, LLL  # noqa: E402
from fpylll.algorithms.bkz2 import BKZReduction  # noqa: E402
import numpy as np  # noqa: E402

Q = 3329


def cbd(rng, eta, size):
    a = rng.integers(0, 2, size=(size, eta)).sum(axis=1)
    b = rng.integers(0, 2, size=(size, eta)).sum(axis=1)
    return a - b


def embedding(A, b, m, n):
    d = m + n + 1
    B = IntegerMatrix(d, d)
    for i in range(m):
        B[i, i] = Q
    for j in range(n):
        for i in range(m):
            B[m + j, i] = int(-A[i, j]) % Q
        B[m + j, m + j] = 1
    for i in range(m):
        B[d - 1, i] = int(b[i])
    B[d - 1, d - 1] = 1
    return B


def found(B, target):
    neg = [-x for x in target]
    for r in range(min(B.nrows, 5)):
        row = list(B[r])
        if row == target or row == neg:
            return True
    return False


def trial(args):
    eta, n, m, seed, max_beta = args
    rng = np.random.default_rng(seed)
    A = rng.integers(0, Q, size=(m, n))
    s = cbd(rng, eta, n)
    e = cbd(rng, eta, m)
    b = (A @ s + e) % Q
    target = [int(x) for x in e] + [int(x) for x in s] + [1]
    B = embedding(A, b, m, n)
    t0 = time.time()
    LLL.reduction(B)
    if found(B, target):
        return {"seed": seed, "beta": 2, "seconds": round(time.time() - t0, 1)}
    M = GSO.Mat(B, float_type="dd" if B.nrows > 160 else "double")
    M.update_gso()
    bkz = BKZReduction(M)
    for beta in range(3, max_beta + 1):
        bkz(BKZ.EasyParam(beta, max_loops=1, flags=BKZ.AUTO_ABORT | BKZ.GH_BND))
        if found(B, target):
            return {"seed": seed, "beta": beta, "seconds": round(time.time() - t0, 1)}
    return {"seed": seed, "beta": None, "seconds": round(time.time() - t0, 1)}


def main():
    eta, n, trials, max_beta = (int(x) for x in sys.argv[1:5])
    params = LWEParameters(n=n, q=Q, Xs=ND.CenteredBinomial(eta), Xe=ND.CenteredBinomial(eta), m=n)
    pred = LWE.primal_usvp(params, red_cost_model=RC.ADPS16)
    d = int(pred["d"])
    m = d - n - 1
    with Pool(min(trials, 22)) as pool:
        runs = pool.map(trial, [(eta, n, m, 1000 * n + t, max_beta) for t in range(trials)])
    betas = [r["beta"] for r in runs if r["beta"] is not None]
    out = {
        "eta": eta, "n": n, "m": m, "d": d, "q": Q,
        "predicted_beta": int(pred["beta"]),
        "trials": trials, "max_beta": max_beta, "solved": len(betas),
        "median_beta": float(np.median(betas)) if betas else None,
        "runs": runs,
    }
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    path = ROOT / "results" / f"usvp_eta{eta}_n{n}_{stamp}.json"
    path.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != "runs"}), flush=True)


if __name__ == "__main__":
    main()
