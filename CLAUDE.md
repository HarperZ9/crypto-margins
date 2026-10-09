# crypto-margins

Private research repo. It measures how much security the full, standardized
primitives have left: ML-KEM, ML-DSA, X25519, SLH-DSA, AES-256 and SHA-3, in
that order (largest open uncertainty first).

## Rules
- Full parameter sets only, taken from the standard (FIPS 203/204/205/197/202,
  RFC 7748). Never trust a vendored copy of parameters; assert against the
  standard.
- Every number lands in `results/` as a JSON receipt with the tool commit, tool
  version and timings. A number without a receipt is not a result.
- A result that beats a published bound is presumed to be our error until an
  independent recomputation agrees. A result that survives goes to the
  designers and NIST/CFRG before anything public.
- Our own code and dummy data only. No third-party live systems.

## Running
Sage lives in WSL Ubuntu-24.04 under micromamba:

    wsl -d Ubuntu-24.04 -- bash -lc "cd /mnt/c/dev/crypto-margins && ~/cm/bin/micromamba run -r ~/cm/mamba -n sage python src/mlkem_baseline.py"

Do not pipe the run through `tail` or `head`: the pipe hides the exit code.

`vendor/lattice-estimator` is a clone of github.com/malb/lattice-estimator; the
receipt records its commit.
