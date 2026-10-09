"""Baseline security estimates for the full ML-KEM parameter sets (FIPS 203).

Run with the Python of the conda-forge sage environment:  python src/mlkem_baseline.py
Writes results/mlkem_baseline.json with the estimator commit, Sage version and
every attack cost, so each later claim can be checked against this receipt.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "vendor" / "lattice-estimator"
sys.path.insert(0, str(VENDOR))

from estimator import LWE, ND, RC, schemes  # noqa: E402
from estimator.lwe_parameters import LWEParameters  # noqa: E402
from estimator.reduction import ADPS16  # noqa: E402
from sage.all import log, oo, version  # noqa: E402

N, Q = 256, 3329
# FIPS 203, Table 2. Key recovery attacks the public key t = A s + e, where
# s and e are both sampled with eta1, and m = k*n samples are available.
FIPS203 = {
    "ML-KEM-512": {"k": 2, "eta1": 3, "vendor": schemes.Kyber512, "claimed_level": 1},
    "ML-KEM-768": {"k": 3, "eta1": 2, "vendor": schemes.Kyber768, "claimed_level": 3},
    "ML-KEM-1024": {"k": 4, "eta1": 2, "vendor": schemes.Kyber1024, "claimed_level": 5},
}

COST_MODELS = {
    "MATZOV": RC.MATZOV,          # estimator default, gate-count style
    "ADPS16_classical": RC.ADPS16,  # core-SVP, the model in the Kyber spec
    "ADPS16_quantum": ADPS16(mode="quantum"),
}


def fips_params(name, spec):
    n = spec["k"] * N
    return LWEParameters(n=n, q=Q, Xs=ND.CenteredBinomial(spec["eta1"]),
                         Xe=ND.CenteredBinomial(spec["eta1"]), m=n, tag=name)


def check_vendor(ours, theirs):
    fields = ("n", "q", "m", "Xs", "Xe")
    diffs = {f: (str(getattr(ours, f)), str(getattr(theirs, f)))
             for f in fields if getattr(ours, f) != getattr(theirs, f)}
    if diffs:
        raise SystemExit(f"vendor parameters disagree with FIPS 203: {diffs}")


def summarize(results):
    out = {}
    for attack, cost in results.items():
        rop = cost.get("rop", oo)
        out[attack] = {
            "log2_rop": None if rop == oo else round(float(log(rop, 2)), 2),
            "beta": int(cost["beta"]) if "beta" in cost else None,
            "raw": str(cost),
        }
    return out


def git_head(path):
    return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()


def main():
    receipt = {
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "estimator_commit": git_head(VENDOR),
        "sage_version": version(),
        "params": {},
    }
    for name, spec in FIPS203.items():
        params = fips_params(name, spec)
        check_vendor(params, spec["vendor"])
        receipt["params"][name] = {"lwe": str(params),
                                   "claimed_nist_level": spec["claimed_level"],
                                   "models": {}}
        for model, rc in COST_MODELS.items():
            t0 = time.time()
            res = LWE.estimate(params, red_cost_model=rc, jobs=8)
            receipt["params"][name]["models"][model] = {
                "seconds": round(time.time() - t0, 1),
                "attacks": summarize(res),
            }
            print(name, model, "done", flush=True)
    out = ROOT / "results" / "mlkem_baseline.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
