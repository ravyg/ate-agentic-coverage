#!/usr/bin/env python3
"""
Estimate the four COV penalty weights from HUMAN agentic-coverage annotations.

Companion to estimate_weights.py, which used the LLM panel and is explicitly
marked provisional ("pending human validation"). This is that validation.

Method is mirrored EXACTLY from estimate_weights.py so the two are comparable:
    coverage_i = base * prod_k weight_k ** trip_ik
=>  log(coverage_i) = log(base) + sum_k trip_ik * log(weight_k)
OLS on log(coverage) with constant + 4 penalty indicators; weight_k =
exp(coef_k); base = exp(intercept); FLOOR=0.02; percentile bootstrap over
tasks, N_BOOT=5000, SEED=42.

Input: data/human_annotations_raw.json  (pulled from the Apps Script
       ?export=json endpoint; see memory conventions G5)
       data/validation_200_key.csv      (unblinded strata)
"""
import csv
import os
import json
import itertools
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "data"
RES = HERE / "results"
CATS = ["P1_interpersonal", "P2_regulatory", "P3_physical", "P4_exception"]
JUDGMENT = {"P1_interpersonal": 0.75, "P2_regulatory": 0.70,
            "P3_physical": 0.60, "P4_exception": 0.80}
# LLM-panel pilot results, for the human-vs-LLM comparison.
PILOT = {"P1_interpersonal": (0.77, 0.39, 1.54),
         "P2_regulatory":    (0.52, 0.25, 1.13),
         "P3_physical":      (0.26, 0.11, 0.62),
         "P4_exception":     (0.71, 0.33, 1.56)}
FLOOR = 0.02
N_BOOT = 5000
SEED = 42
# Owner test rows from form development — excluded from the headline estimate,
# reported as a sensitivity line. See data-quality section of the writeup.
OWNER_EMAIL = os.environ.get("ATE_OWNER_EMAIL", "")  # set locally; never hard-code PII


def load_key():
    rows = list(csv.DictReader(open(DATA / "validation_200_key.csv", newline="")))
    for r in rows:
        for c in CATS:
            r[c] = int(r[c])
    return {int(r["task_id"]): r for r in rows}


def load_annotations():
    d = json.load(open(DATA / "human_annotations_raw.json"))
    return d["rows"]


def fit(X, y):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def dedup(rows):
    """Keep the LAST response per (email, task) — the form supports resume,
    so a later row supersedes an earlier one."""
    best = {}
    for r in rows:
        k = (r["annotator_email"], int(r["task_id"]))
        prev = best.get(k)
        if prev is None or r["timestamp"] > prev["timestamp"]:
            best[k] = r
    return list(best.values())


def build(rows, key):
    """rows -> (task_ids, per-task mean coverage, X design matrix, spreads)."""
    per_task = {}
    for r in rows:
        tid = int(r["task_id"])
        if tid not in key:
            continue
        per_task.setdefault(tid, []).append(float(r["coverage"]))
    ids, y, design, spreads = [], [], [], []
    for tid, covs in sorted(per_task.items()):
        m = float(np.mean(covs))
        ids.append(tid)
        y.append(np.log(max(m, FLOOR)))
        design.append([key[tid][c] for c in CATS])
        if len(covs) > 1:
            spreads.append(float(np.std(covs, ddof=1)))
    y = np.array(y)
    X = np.column_stack([np.ones(len(y)), np.array(design, dtype=float)])
    return ids, y, X, spreads


def estimate(y, X, label):
    beta = fit(X, y)
    base = float(np.exp(beta[0]))
    weights = {c: float(np.exp(beta[i + 1])) for i, c in enumerate(CATS)}
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
            boot[c].append(float(np.exp(b[i + 1])))
    cis = {c: tuple(np.percentile(boot[c], [2.5, 97.5])) for c in CATS}
    return base, weights, cis, label


def icc_2k(mat):
    """ICC(2,k) — two-way random effects, absolute agreement, average of k
    raters. mat: n_targets x k_raters."""
    n, k = mat.shape
    gm = mat.mean()
    ms_r = k * ((mat.mean(axis=1) - gm) ** 2).sum() / (n - 1)          # between targets
    ms_c = n * ((mat.mean(axis=0) - gm) ** 2).sum() / (k - 1)          # between raters
    resid = mat - mat.mean(axis=1, keepdims=True) - mat.mean(axis=0, keepdims=True) + gm
    ms_e = (resid ** 2).sum() / ((n - 1) * (k - 1))
    return float((ms_r - ms_e) / (ms_r + (ms_c - ms_e) / n))


def main():
    key = load_key()
    raw = load_annotations()
    print(f"raw rows: {len(raw)}   key tasks: {len(key)}")

    # ---------- data quality ----------
    by_email = {}
    for r in raw:
        by_email.setdefault(r["annotator_email"], []).append(r)
    print("\n=== completeness ===")
    for e, rs in sorted(by_email.items(), key=lambda kv: -len(kv[1])):
        name = rs[0]["annotator"]
        print(f"  {name:<18} {e:<30} {len(rs):>4} rows, "
              f"{len({int(x['task_id']) for x in rs}):>3} distinct tasks")

    deduped = dedup(raw)
    print(f"\ndedup (last-wins per email+task): {len(raw)} -> {len(deduped)} rows")

    main_rows = [r for r in deduped if r["annotator_email"] != OWNER_EMAIL]
    print(f"excluding owner test rows ({OWNER_EMAIL}): -> {len(main_rows)} rows")

    panel = sorted({r["annotator_email"] for r in main_rows})
    print(f"panel: {len(panel)} annotators")

    # ---------- inter-rater reliability ----------
    cov = {}
    for r in main_rows:
        cov.setdefault(int(r["task_id"]), {})[r["annotator_email"]] = float(r["coverage"])
    complete = sorted([t for t, d in cov.items() if len(d) == len(panel)])
    mat = np.array([[cov[t][e] for e in panel] for t in complete])
    print(f"\n=== inter-rater reliability (n={len(complete)} tasks x {len(panel)} raters) ===")
    print(f"  ICC(2,k) absolute agreement : {icc_2k(mat):.3f}")
    print(f"  mean per-task SD            : {mat.std(axis=1, ddof=1).mean():.3f}")
    print("  pairwise Pearson r / mean|diff|:")
    for i, j in itertools.combinations(range(len(panel)), 2):
        r_ = float(np.corrcoef(mat[:, i], mat[:, j])[0, 1])
        md = float(np.abs(mat[:, i] - mat[:, j]).mean())
        print(f"    {panel[i].split('@')[0]:<16} vs {panel[j].split('@')[0]:<16} "
              f"r={r_:.3f}  mean|diff|={md:.3f}")

    # ---------- group means ----------
    print("\n=== mean coverage by stratum (pooled humans) ===")
    strata = {}
    for i, t in enumerate(complete):
        strata.setdefault(key[t]["stratum"], []).extend(mat[i].tolist())
    ctrl_key = next((s for s in strata if s.startswith("control")), None)
    ctrl = float(np.mean(strata[ctrl_key])) if ctrl_key else float("nan")
    print(f"  {'stratum':<20} {'n_obs':>6} {'mean':>7} {'sd':>7} {'ratio/ctrl':>11}")
    for s in sorted(strata):
        v = np.array(strata[s])
        ratio = v.mean() / ctrl if ctrl == ctrl else float("nan")
        print(f"  {s:<20} {len(v):>6} {v.mean():>7.3f} {v.std(ddof=1):>7.3f} {ratio:>11.3f}")

    # ---------- headline estimate ----------
    ids, y, X, spreads = build(main_rows, key)
    base, weights, cis, _ = estimate(y, X, "human")
    print(f"\n=== HEADLINE: human panel (tasks={len(y)}, base={base:.3f}) ===")
    print(f"{'penalty':<18} {'judgment':>9} {'human':>7} {'95% CI':>16} "
          f"{'in CI?':>7} {'LLM pilot':>10} {'LLM CI':>16}")
    out = []
    for c in CATS:
        lo, hi = cis[c]
        ok = "YES" if lo <= JUDGMENT[c] <= hi else "no"
        pe, plo, phi = PILOT[c]
        print(f"{c:<18} {JUDGMENT[c]:>9.2f} {weights[c]:>7.2f} "
              f"[{lo:>5.2f},{hi:>6.2f}] {ok:>7} {pe:>10.2f} [{plo:>5.2f},{phi:>6.2f}]")
        out.append({"penalty": c, "judgment": JUDGMENT[c],
                    "human_estimate": round(weights[c], 3),
                    "ci_lo": round(lo, 3), "ci_hi": round(hi, 3),
                    "judgment_in_ci": ok, "llm_pilot": pe,
                    "llm_ci_lo": plo, "llm_ci_hi": phi,
                    "llm_in_human_ci": "YES" if lo <= pe <= hi else "no"})

    order = sorted(CATS, key=lambda c: weights[c])
    expected = ["P3_physical", "P2_regulatory", "P1_interpersonal", "P4_exception"]
    print(f"\nrank order (low->high): {' < '.join(order)}")
    print(f"expected             : {' < '.join(expected)}")
    print(f"rank order reproduced: {'YES' if order == expected else 'NO'}")

    # ---------- sensitivity: include owner rows ----------
    ids2, y2, X2, _ = build(deduped, key)
    _, w2, ci2, _ = estimate(y2, X2, "with-owner")
    print("\n=== sensitivity: including owner test rows ===")
    for c in CATS:
        print(f"  {c:<18} {w2[c]:.3f}  (headline {weights[c]:.3f}, "
              f"delta {w2[c]-weights[c]:+.3f})")

    # ---------- per-annotator and leave-one-out ----------
    # Inter-rater disagreement is high, so check no single annotator drives the
    # result (and in particular whether P4's rejection is robust).
    print("\n=== per-annotator estimates (each rater alone) ===")
    print(f"  {'annotator':<16} " + " ".join(f"{c.split('_')[0]:>7}" for c in CATS))
    for e in panel:
        rs = [r for r in main_rows if r["annotator_email"] == e]
        idsi, yi, Xi, _ = build(rs, key)
        bi = fit(Xi, yi)
        wi = [float(np.exp(bi[i + 1])) for i in range(len(CATS))]
        print(f"  {e.split('@')[0]:<16} " + " ".join(f"{v:>7.2f}" for v in wi))

    print("\n=== leave-one-annotator-out (does P4's rejection survive?) ===")
    for drop in panel:
        rs = [r for r in main_rows if r["annotator_email"] != drop]
        idsl, yl, Xl, _ = build(rs, key)
        _, wl, cil, _ = estimate(yl, Xl, "loo")
        p4lo, p4hi = cil["P4_exception"]
        verdict = "0.80 IN CI" if p4lo <= 0.80 <= p4hi else "0.80 rejected"
        order_l = sorted(CATS, key=lambda c: wl[c])
        print(f"  without {drop.split('@')[0]:<16} "
              f"P4={wl['P4_exception']:.2f} [{p4lo:.2f},{p4hi:.2f}] -> {verdict}")
        print(f"      rank: {' < '.join(x.split('_')[0] for x in order_l)}")

    RES.mkdir(exist_ok=True)
    with open(RES / "estimated_weights_human.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

    with open(DATA / "human_annotations_tidy.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task_id", "occupation", "stratum", "annotator_email", "coverage"])
        for r in sorted(main_rows, key=lambda x: (int(x["task_id"]), x["annotator_email"])):
            t = int(r["task_id"])
            w.writerow([t, r["occupation"], key[t]["stratum"],
                        r["annotator_email"], r["coverage"]])
    print(f"\nwrote {RES/'estimated_weights_human.csv'} and {DATA/'human_annotations_tidy.csv'}")


if __name__ == "__main__":
    main()
