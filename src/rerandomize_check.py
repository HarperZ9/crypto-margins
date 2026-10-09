"""Does re-randomizing the lattice re-draw a fixed secret's dual score?

One secret s and a pool of M_POOL samples b = A s + e. Each round picks a fresh
random subset of m samples, sieves the dual lattice of A_r on that subset, and
records the correct-guess score ratio S / sum(eps_cbd) for the true target
t = (e_subset, s_r). The same database also scores 200 fresh secrets, giving
the across-secret spread for comparison.

Usage (g6k venv): python src/rerandomize_check.py M NR K ROUNDS THREADS SEED
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dual_hybrid_check import Q, cbd2, dual_basis, sieve_vectors  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
M_POOL = 400


def eps_cbd(W):
    with np.errstate(divide="ignore"):
        return np.exp(4 * np.log(np.abs(np.cos(np.pi * W / Q))).sum(1))


def ratio(W, t, eps_sum):
    return float(np.cos(2 * np.pi * ((W @ t) % Q) / Q).sum() / eps_sum)


def main():
    m, nr, k, rounds, threads, seed = (int(x) for x in sys.argv[1:7])
    rng = np.random.default_rng(seed)
    n = nr + k
    A = rng.integers(0, Q, (M_POOL, n))
    s, e = cbd2(rng, n), cbd2(rng, M_POOL)
    fixed, across = [], []
    for r in range(rounds):
        idx = rng.choice(M_POOL, m, replace=False)
        W, _ = sieve_vectors(dual_basis(A[idx, k:], m, nr), threads)
        W = W[(W != 0).any(1)]
        es = eps_cbd(W).sum()
        fixed.append(ratio(W, np.concatenate([e[idx], s[k:]]), es))
        others = [ratio(W, cbd2(rng, m + nr), es) for _ in range(200)]
        across.append([float(np.quantile(others, q)) for q in (0.1, 0.5, 0.9)])
        print(json.dumps({"round": r, "N": len(W), "fixed_ratio": fixed[-1],
                          "across_q10_q50_q90": across[-1]}), flush=True)
    fx = np.array(fixed)
    summary = {
        "m": m, "nr": nr, "k": k, "rounds": rounds, "seed": seed,
        "fixed_secret_ratios": fixed,
        "fixed_q10_q50_q90": [float(np.quantile(fx, q)) for q in (0.1, 0.5, 0.9)],
        "fixed_mean": float(fx.mean()), "fixed_std": float(fx.std()),
        "across_secret_median_q10_q50_q90": np.median(np.array(across), 0).tolist(),
    }
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    path = ROOT / "results" / f"rerand_m{m}_nr{nr}_k{k}_s{seed}_{stamp}.json"
    path.write_text(json.dumps(summary, indent=2))
    print(json.dumps({k_: v for k_, v in summary.items() if k_ != "fixed_secret_ratios"}), flush=True)


if __name__ == "__main__":
    main()
