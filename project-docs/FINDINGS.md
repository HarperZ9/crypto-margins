# Findings

Dated entries. Each names its receipt files, what it shows, and what it does
not prove. Toolchain: SageMath 10.9 + lattice-estimator 53da598 (conda env
`sage`); g6k c71e084 + fpylll 0.6.4 built from source (venv `g6kenv`).

## 2026-10-08 F1. ML-KEM baseline reproduces the published estimates

Receipt: `results/mlkem_baseline.json`. Parameters from FIPS 203 Table 2,
asserted equal to the estimator's Kyber512/768/1024.

Primal uSVP, core-SVP: 2^118.6 / 2^182.2 / 2^255.2 classical, 2^107.6 /
2^165.4 / 2^231.6 quantum, beta 406 / 624 / 874. Kyber round-3 spec figures
(from memory, moderate): 118 / 182 / 256 and 107 / 165 / 232, beta 406 / 623
/ 873. Best attack under MATZOV: dual-hybrid, 2^139.7 / 2^196.4 / 2^262.3.

Does not prove: that the estimator's cost models are right; only that our
toolchain and parameter encoding reproduce the published analysis.

## 2026-10-08 F2. Concrete primal uSVP needs slightly larger beta than predicted

Receipts: `results/usvp_eta*_n*.json`. Progressive BKZ 2.0, one tour per
block size, auto-abort on; 10 trials per point, all solved.

| eta | n | d | predicted beta | median beta |
|---|---|---|---|---|
| 2 | 130 | 260 | 44 | 53.0 |
| 3 | 130 | 259 | 53 | 55.5 |
| 2 | 140 | 274 | 55 | 59.5 |

Direction: harder for the attacker than predicted, gap narrowing away from the
estimator's beta floor of 40. Likely cause: one tour per block size leaves the
basis less reduced than the model's "BKZ-beta reduced" assumption.

Does not prove: anything about full ML-KEM. Small dimensions only; the harness
reduction strategy is weaker than the model assumes.

## 2026-10-09 F5. ML-DSA baseline reproduces the published key-recovery estimates

Receipt: `results/mldsa_baseline_20261009T231103Z.json`. Key recovery from
FIPS 204 Table 1 as LWE (secret dim 256*l, 256*k samples, q = 8380417,
uniform [-eta, eta]). Forgery uses the estimator's bundled Dilithium MSIS
sets as-is; their length bounds are not yet re-derived from FIPS 204.

Core-SVP (ADPS16), classical:

| set | primal uSVP (beta) | dual-hybrid | MSIS weak / strong unf. | spec MLWE (memory, moderate) |
|---|---|---|---|---|
| ML-DSA-44 | 2^123.8 (424) | 2^122.6 | 2^123.5 / 2^121.8 | 123 |
| ML-DSA-65 | 2^182.2 (624) | 2^184.9 | 2^186.3 / 2^175.8 | 182 |
| ML-DSA-87 | 2^252.0 (863) | 2^245.1 | 2^265.4 / 2^253.5 | 252 |

Best key recovery under MATZOV: 2^148.0 / 2^203.8 / 2^267.0.

Note: for ML-DSA-87 the dual-hybrid estimate sits 7 bits below primal, and
under MATZOV a few bits below the commonly cited category-5 gate threshold of
about 2^272 (moderate). It rests on the dual-hybrid model whose fixed-secret
score behavior F3/F4 measured; the same pattern as the ML-KEM-512 debate.
Identical numbers for ML-DSA-65 and ML-KEM-768 (2^182.21, beta 624) are not a
bug: core-SVP cost depends only on beta.

Does not prove: that the MSIS bounds are right for FIPS 204, or anything
beyond reproduction of the published analysis.

## 2026-10-09 F4. Re-randomizing the lattice only partly re-draws a fixed secret's score; no cost gain

Receipts: `results/logs/rerand_s11.log` (15 rounds), `rerand_s12.log` (20
rounds); runs stopped by a session restart, completed rounds kept.
`src/analyze_rerand.py` summarizes them. Shape m=25, nr=45, k=4; each round a
fresh 25-sample subset from a 400-sample pool, same secret.

| secret | rounds | fixed-secret mean ratio | std across lattices | across-secret std (per lattice) |
|---|---|---|---|---|
| 11 | 15 | 1.196 (SE 0.069) | 0.268 | about 0.49 |
| 12 | 20 | 0.964 (SE 0.086) | 0.386 | about 0.47 |

Reading: part of the across-secret spread is a persistent property of the
secret (secret 11 sits about 2.8 SE above 1), consistent with the target-norm
confounder Ducas-Pulles identify; s_r is fixed across rounds while the error
subset changes. The rest re-draws with each lattice.

Cost (inferred, not measured): running at half the threshold signal saves
about 4x in sieved vectors (threshold grows as sqrt(N)) but needs a ratio of
2 or more per attempt, about 0.5 to 1% likely at the measured spread, so about
100+ attempts. Net loss. The F3 open question closes as a null.

Does not prove: anything at cryptographic size; two secrets, one shape.

## 2026-10-09 F3. Dual-hybrid scores: mean matches the model, fixed-secret spread does not

Receipts: `results/dual_m*_nr*_k4*.json`. Small ML-KEM-shaped LWE (q = 3329,
CBD(2)), k = 4 guessed coordinates (625 candidates), g6k sieve of the dual
lattice, 400 fresh secrets scored per sieved database.

1. Wrong-guess scores match the independence model: measured std within about
   5% of sqrt(N/2) at every shape (e.g. 199 / 194, 274 / 278, 418 / 399).
2. Correct-guess score, averaged over secrets, matches sum(eps) with the exact
   CBD characteristic function: mean ratio 0.98 to 1.10, each within about 2
   standard errors of 1.
3. For a fixed lattice, the correct-guess score varies across secrets far more
   than the model's sqrt(N/2): 10th to 90th percentile of the ratio is
   0.46 to 1.8 (m=25, nr=45) and about -0.3 to 2.5 (m=25, nr=50). The model
   implies a relative spread of about 2 to 6%.
4. Consequence near threshold (m=25, nr=50, signal about half the best wrong
   score): measured failure 0.87 / 0.74 / 0.81 against the iid model's
   0.96 / 0.85 / 0.88. Well above threshold, failures appear where the model
   predicts none (0.005, 0.003 at m=25, nr=45).

Interpretation (inferred): the fixed-secret score is wide and right-skewed,
consistent with the score depending on the secret's position relative to the
primal lattice (the Ducas-Pulles 2023 picture). It cuts both ways: success
above threshold is slightly less certain than modeled; success below threshold
is more likely than modeled.

Open question this raises: if re-randomizing the lattice (fresh sample subset,
different guessed coordinates) re-draws a fixed secret's score from the same
wide distribution, an attacker could run below the modeled threshold and
repeat. Whether that lowers total cost depends on how cost falls with signal;
at the measured gain (success probability up by a factor of 1.1 to 3) the
effect is at most a few bits before accounting for repetition cost, and may be
zero after it. Not yet measured.

Does not prove: any reduction in ML-KEM security. Dimensions 70 to 80, k = 4,
3 lattices per shape, unsaturated sieve databases.

Literature check (2026-10-09, web search, not yet read in full): items 1 and 3
are known. Ducas-Pulles (Crypto 2023, ePrint 2023/1850) report that the
independence heuristic badly underestimates the correct-guess variance; their
"Accurate Score Prediction for Dual-Sieve Attacks" fixes the target norm as the
confounder; ePrint 2026/1048 gives a covariance-based analysis; ePrint
2026/2166 gives a provable correctness analysis of the MATZOV FFT dual attack
on ML-KEM. F3 is a reproduction, not a new result. The re-randomization
question below was not found addressed in this search; that absence is not
evidence it is open.
