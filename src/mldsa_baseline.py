"""Baseline security estimates for the full ML-DSA parameter sets (FIPS 204).

Key recovery: t = A s1 + s2 with A in R_q^{k x l}, s1, s2 uniform in [-eta, eta].
As LWE: secret dimension 256*l, 256*k samples, q = 8380417.
Forgery: the estimator's bundled Dilithium MSIS sets (weak and strong
unforgeability), recorded as-is; their length bounds are not yet re-derived
from FIPS 204.

Run: python src/mldsa_baseline.py   (conda env `sage`)
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "vendor" / "lattice-estimator"
sys.path.insert(0, str(VENDOR))

from estimator import LWE, ND, RC, SIS, schemes  # noqa: E402
from estimator.lwe_parameters import LWEParameters  # noqa: E402
from sage.all import log, oo, version  # noqa: E402

Q, N = 8380417, 256
# FIPS 204, Table 1: (k, l, eta, claimed category)
FIPS204 = {
    "ML-DSA-44": (4, 4, 2, 2),
    "ML-DSA-65": (6, 5, 4, 3),
    "ML-DSA-87": (8, 7, 2, 5),
}
MSIS = {
    "ML-DSA-44": (schemes.Dilithium2_MSIS_WkUnf, schemes.Dilithium2_MSIS_StrUnf),
    "ML-DSA-65": (schemes.Dilithium3_MSIS_WkUnf, schemes.Dilithium3_MSIS_StrUnf),
    "ML-DSA-87": (schemes.Dilithium5_MSIS_WkUnf, schemes.Dilithium5_MSIS_StrUnf),
}


def summarize(results):
    out = {}
    for attack, cost in results.items():
        rop = cost.get("rop", oo)
        out[attack] = {"log2_rop": None if rop == oo else round(float(log(rop, 2)), 2),
                       "beta": int(cost["beta"]) if "beta" in cost else None}
    return out


def main():
    commit = subprocess.run(["git", "-C", str(VENDOR), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=True).stdout.strip()
    receipt = {"started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "estimator_commit": commit, "sage_version": version(), "params": {}}
    for name, (k, l, eta, cat) in FIPS204.items():
        p = LWEParameters(n=N * l, q=Q, Xs=ND.Uniform(-eta, eta), Xe=ND.Uniform(-eta, eta),
                          m=N * k, tag=name)
        entry = {"lwe": str(p), "claimed_category": cat, "key_recovery": {}, "forgery": {}}
        for model, rc in (("MATZOV", RC.MATZOV), ("ADPS16_classical", RC.ADPS16)):
            entry["key_recovery"][model] = summarize(LWE.estimate(p, red_cost_model=rc, jobs=8))
            print(name, "key recovery", model, "done", flush=True)
        for label, sp in zip(("weak_unf", "strong_unf"), MSIS[name]):
            for model, rc in (("MATZOV", RC.MATZOV), ("ADPS16_classical", RC.ADPS16)):
                entry["forgery"][f"{label}_{model}"] = summarize(
                    SIS.estimate(sp, red_cost_model=rc, jobs=8))
            print(name, "forgery", label, "done", flush=True)
        receipt["params"][name] = entry
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = ROOT / "results" / f"mldsa_baseline_{stamp}.json"
    out.write_text(json.dumps(receipt, indent=2))
    print("wrote", out)


if __name__ == "__main__":
    main()
