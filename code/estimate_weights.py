#!/usr/bin/env python3
"""
Estimate the four COV penalty weights from measured agentic coverage.

Model (multiplicative, matching compute_cov in the ATES code):
    coverage_i = base * prod_k  weight_k ** trip_ik
=>  log(coverage_i) = log(base) + sum_k trip_ik * log(weight_k)

We fit an OLS on log(coverage) with a constant + 4 penalty indicators.
weight_k = exp(coef_k); base = exp(intercept). No-penalty control tasks
identify the base. Bootstrap over tasks gives percentile CIs.

Coverage labels come from the LLM panel (results/ratings_rater*.csv),
averaged per task. CLEARLY PROVISIONAL: LLM-panel estimates, pending
human validation. Compares estimated weights to the paper's judgment
values (0.75 / 0.70 / 0.60 / 0.80).
"""
import csv
import glob
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent.parent   # repo root
DATA = HERE / "data"
RES = HERE / "results"
CATS = ["P1_interpersonal", "P2_regulatory", "P3_physical", "P4_exception"]
JUDGMENT = {"P1_interpersonal": 0.75, "P2_regulatory": 0.70,
            "P3_physical": 0.60, "P4_exception": 0.80}
FLOOR = 0.02          # coverage floor so log is defined
N_BOOT = 5000
SEED = 42


def load_pilot():
    rows = list(csv.DictReader(open(DATA / "pilot_tasks.csv", newline="")))
    for r in rows:
        for c in CATS:
            r[c] = int(r[c])
    return {r["task_id"]: r for r in rows}


def load_ratings():
    """Return {task_id: [coverage,...]} pooled across all rater files."""
    pooled = {}
    files = sorted(glob.glob(str(RES / "ratings_rater*.csv")))
    if not files:
        raise SystemExit("No rater files yet in results/. Run the panel first.")
    for fp in files:
        for r in csv.DictReader(open(fp, newline="")):
            try:
                cov = float(r["coverage"])
            except (ValueError, KeyError):
                continue
            pooled.setdefault(r["task_id"], []).append(cov)
    print(f"Loaded {len(files)} rater files.")
    return pooled


def fit(X, y):
    """OLS: y = X beta. Returns beta. X includes intercept column."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def main():
    pilot = load_pilot()
    ratings = load_ratings()

    ids, y, rows = [], [], []
    spreads = []
    for tid, covs in ratings.items():
        if tid not in pilot:
            continue
        m = float(np.mean(covs))
        spreads.append(float(np.std(covs)))
        ids.append(tid)
        y.append(np.log(max(m, FLOOR)))
        rows.append([pilot[tid][c] for c in CATS])
    y = np.array(y)
    Xp = np.array(rows, dtype=float)
    X = np.column_stack([np.ones(len(y)), Xp])   # intercept + 4 cats
    print(f"Tasks used: {len(y)}   mean inter-rater SD: {np.mean(spreads):.3f}")

    beta = fit(X, y)
    base = np.exp(beta[0])
    weights = {c: float(np.exp(beta[i + 1])) for i, c in enumerate(CATS)}

    # Bootstrap CIs over tasks
    rng = np.random.default_rng(SEED)
    boot = {c: [] for c in CATS}
    n = len(y)
    for _ in range(N_BOOT):
        idx = rng.integers(0, n, n)
        try:
            b = fit(X[idx], y[idx])
        except np.linalg.LinAlgError:
            continue
        for i, c in enumerate(CATS):
            boot[c].append(np.exp(b[i + 1]))

    print(f"\nBase coverage (no-penalty task): {base:.3f}\n")
    print(f"{'Penalty':18s} {'judgment':>9s} {'estimated':>10s} {'95% CI':>18s}  {'agree?':>6s}")
    out = []
    for c in CATS:
        lo, hi = np.percentile(boot[c], [2.5, 97.5])
        est = weights[c]
        agree = "yes" if lo <= JUDGMENT[c] <= hi else "no"
        print(f"{c:18s} {JUDGMENT[c]:9.2f} {est:10.2f} "
              f"[{lo:5.2f}, {hi:5.2f}]  {agree:>6s}")
        out.append({"penalty": c, "judgment": JUDGMENT[c],
                    "estimated": round(est, 3),
                    "ci_lo": round(float(lo), 3), "ci_hi": round(float(hi), 3),
                    "judgment_in_ci": agree})

    with open(RES / "estimated_weights.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print(f"\nWrote {RES/'estimated_weights.csv'}")
    print("\nNOTE: coverage labels are LLM-panel estimates (provisional), "
          "not human ground truth.")


if __name__ == "__main__":
    main()
