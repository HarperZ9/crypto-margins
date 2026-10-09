"""Concrete dual-hybrid distinguisher on small ML-KEM-shaped LWE.

Question: do the score statistics the dual-hybrid cost model assumes hold on
real sieved dual vectors? The model treats wrong-guess scores as independent
N(0, N/2) and the correct-guess score as mean sum(eps_i), where
eps_i = exp(-2 pi^2 sigma^2 |w_i|^2 / q^2). Ducas-Pulles (2023) argued the
independence assumption fails in some regimes.

Setup: b = A s + e mod q, s, e ~ CBD(2) (sigma^2 = 1), q = 3329. Guess the
first k secret coordinates; build the dual lattice
    L = {(x, y) : y = A_r^T x mod q}  of dimension m + (n - k),
sieve it with g6k, and score every guess c in {-2..2}^k:
    S(c) = sum_i cos(2 pi (<x_i, b> - <A_g^T x_i, c>) / q).
A control run replaces b with uniform noise.

Usage (g6k venv): python src/dual_hybrid_check.py M NR K TRIALS THREADS
Writes results/dual_m{M}_nr{NR}_k{K}.json.
"""
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
from fpylll import BKZ, IntegerMatrix, LLL
from g6k import Siever, SieverParams
from g6k.siever import SaturationError

Q = 3329
ROOT = Path(__file__).resolve().parent.parent


def cbd2(rng, size):
    return rng.integers(0, 2, (size, 2)).sum(1) - rng.integers(0, 2, (size, 2)).sum(1)


def dual_basis(A_r, m, nr):
    d = m + nr
    B = IntegerMatrix(d, d)
    for i in range(m):
        B[i, i] = 1
        for j in range(nr):
            B[i, m + j] = int(A_r[i, j]) % Q
    for j in range(nr):
        B[m + j, m + j] = Q
    return B


def sieve_vectors(B, threads):
    LLL.reduction(B)
    # No strategies file in the source-built fpylll; plain BKZ-20 needs none.
    BKZ.reduction(B, BKZ.Param(20, max_loops=4))
    g6k = Siever(B, SieverParams(threads=threads))
    g6k.initialize_local(0, 0, B.nrows)
    saturated = True
    try:
        g6k()
    except SaturationError:
        # The database is still valid lattice vectors; predictions use their
        # actual norms, so an unsaturated database does not bias the check.
        saturated = False
    W = np.array([g6k.M.B.multiply_left(x) for x in g6k.itervalues()], dtype=np.int64)
    return W, saturated


def scores(W, m, b, A_g, cands):
    X = W[:, :m]
    u = (X @ b) % Q                     # <x_i, b>
    G = (X @ A_g) % Q                   # A_g^T x_i, shape N x k
    out = np.empty(len(cands))
    step = 64
    for s in range(0, len(cands), step):
        C = cands[s:s + step]
        ph = (u[:, None] - G @ C.T) % Q
        out[s:s + step] = np.cos(2 * np.pi * ph / Q).sum(0)
    return out


def iid_max_quantiles(N, C, rng, reps=2000):
    sims = rng.normal(0, np.sqrt(N / 2), size=(reps, C)).max(1)
    return {"median": float(np.median(sims)), "p95": float(np.quantile(sims, 0.95))}


def trial(m, nr, k, seed, threads):
    rng = np.random.default_rng(seed)
    n = nr + k
    A = rng.integers(0, Q, (m, n))
    s, e = cbd2(rng, n), cbd2(rng, m)
    b = (A @ s + e) % Q
    A_g, A_r = A[:, :k], A[:, k:]
    t0 = time.time()
    W, saturated = sieve_vectors(dual_basis(A_r, m, nr), threads)
    t_sieve = time.time() - t0
    W = W[(W != 0).any(1)]
    norms2 = (W.astype(float) ** 2).sum(1)
    eps = np.exp(-2 * np.pi ** 2 * norms2 / Q ** 2)
    # Exact for CBD(2): E[cos(2 pi <w,z>/q)] = prod_j cos(pi w_j / q)^4.
    with np.errstate(divide="ignore"):
        eps_cbd = np.exp(4 * np.log(np.abs(np.cos(np.pi * W / Q))).sum(1))
    cands = np.array(list(itertools.product(range(-2, 3), repeat=k)), dtype=np.int64)
    true_idx = int(np.where((cands == s[:k]).all(1))[0][0])
    sc = scores(W, m, b, A_g, cands)
    wrong = np.delete(sc, true_idx)
    ctrl = scores(W, m, rng.integers(0, Q, m), A_g, cands)
    N = len(W)
    # The database depends only on A_r, so score many fresh secrets against it:
    # S(t) = sum_i cos(2 pi <w_i, t> / q) for t = (e, s_r) ~ CBD(2).
    T = 400
    S = np.empty(T)
    for j in range(T):
        t = cbd2(rng, W.shape[1])
        S[j] = np.cos(2 * np.pi * ((W @ t) % Q) / Q).sum()
    ratio = S / eps_cbd.sum()
    return {
        "fresh_targets": T,
        "fresh_ratio_mean": float(ratio.mean()),
        "fresh_ratio_sem": float(ratio.std() / np.sqrt(T)),
        "fresh_ratio_quantiles": {q: float(np.quantile(ratio, float(q)))
                                  for q in ("0.1", "0.25", "0.5", "0.75", "0.9")},
        # Fraction of fresh secrets whose correct score would lose to the
        # best wrong guess observed in this trial (the attack fails on them).
        "fresh_fail_frac": float((S <= wrong.max()).mean()),
        "pred_fail_frac_iid": float(
            (rng.normal(eps_cbd.sum(), np.sqrt(N / 2), 20000) <= wrong.max()).mean()),
        "seed": seed, "N": N, "saturated": saturated, "sieve_seconds": round(t_sieve, 1),
        "mean_norm": float(np.sqrt(norms2).mean()),
        "pred_correct_mean": float(eps.sum()),
        "pred_correct_mean_cbd": float(eps_cbd.sum()),
        "correct_score": float(sc[true_idx]),
        "correct_rank": int((sc > sc[true_idx]).sum()),
        "wrong_std": float(wrong.std()), "pred_wrong_std": float(np.sqrt(N / 2)),
        "wrong_max": float(wrong.max()),
        "control_max": float(ctrl.max()), "control_std": float(ctrl.std()),
        "iid_max": iid_max_quantiles(N, len(cands) - 1, rng),
    }


def main():
    m, nr, k, trials, threads = (int(x) for x in sys.argv[1:6])
    runs = []
    for t in range(trials):
        r = trial(m, nr, k, 7919 * (m * 100 + nr) + t, threads)
        runs.append(r)
        print(json.dumps(r), flush=True)
    out = {"m": m, "nr": nr, "k": k, "q": Q, "dim": m + nr, "runs": runs}
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    path = ROOT / "results" / f"dual_m{m}_nr{nr}_k{k}_{stamp}.json"
    path.write_text(json.dumps(out, indent=2))
    print("wrote", path, flush=True)


if __name__ == "__main__":
    main()
