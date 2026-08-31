#!/usr/bin/env python3
"""
Regenerate every number in validation/RESULTS.md.

    python3 validation/compute_validation.py

Inputs
------
data/agentic_coverage.csv        released dataset (18,796 LLM coverage labels)
validation/audit_scores_200.csv  DE-IDENTIFIED per-task human panel scores
                                 (annotator_1/2/3 columns, no names or emails)

The raw annotation export contains annotator names and emails and is NOT
released. `audit_scores_200.csv` is the de-identified derivative: annotator
columns are shuffled to a fixed pseudonymous order and carry no identity.
Regenerate it from the raw export with `--build` (maintainers only):

    python3 validation/compute_validation.py --build path/to/human_annotations_raw.json
"""
import argparse
import csv
import itertools
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
VAL = ROOT / "validation"
AUDIT = VAL / "audit_scores_200.csv"
SEED = 42


# ----------------------------------------------------------------------------
# de-identification (maintainers only)
# ----------------------------------------------------------------------------
def build_audit(raw_path):
    """Raw export -> de-identified per-task panel scores. Drops names/emails."""
    rows = json.load(open(raw_path))["rows"]
    key = {int(r["task_id"]): r for r in
           csv.DictReader(open(DATA / "validation_200_key.csv", newline=""))}

    # last-wins dedup per (email, task); form supports resume
    best = {}
    for r in rows:
        k = (r["annotator_email"], int(r["task_id"]))
        if k not in best or r["timestamp"] > best[k]["timestamp"]:
            best[k] = r

    # keep only annotators who completed the full 200-task set
    by_email = {}
    for (email, tid), r in best.items():
        by_email.setdefault(email, {})[tid] = float(r["coverage"])
    panel = sorted([e for e, d in by_email.items() if len(d) == 200])
    if len(panel) != 3:
        sys.exit(f"expected 3 complete annotators, found {len(panel)}")

    # fixed pseudonymous order so columns cannot be re-linked to people
    rng = np.random.default_rng(SEED)
    order = list(panel)
    rng.shuffle(order)

    tasks = sorted(key)
    with open(AUDIT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task_id", "stratum", "annotator_1", "annotator_2", "annotator_3"])
        for t in tasks:
            w.writerow([t, key[t]["stratum"]] + [by_email[e][t] for e in order])
    print(f"wrote {AUDIT} (de-identified, {len(tasks)} tasks)")


# ----------------------------------------------------------------------------
# metrics
# ----------------------------------------------------------------------------
def icc_2k(mat):
    """ICC(2,k): two-way random effects, absolute agreement, average of k raters."""
    n, k = mat.shape
    gm = mat.mean()
    ms_r = k * ((mat.mean(axis=1) - gm) ** 2).sum() / (n - 1)
    ms_c = n * ((mat.mean(axis=0) - gm) ** 2).sum() / (k - 1)
    resid = mat - mat.mean(axis=1, keepdims=True) - mat.mean(axis=0, keepdims=True) + gm
    ms_e = (resid ** 2).sum() / ((n - 1) * (k - 1))
    return float((ms_r - ms_e) / (ms_r + (ms_c - ms_e) / n))


def spearman(a, b):
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", metavar="RAW_JSON",
                    help="maintainers only: rebuild the de-identified audit file")
    args = ap.parse_args()
    if args.build:
        build_audit(args.build)
        return

    if not AUDIT.exists():
        sys.exit(f"missing {AUDIT}")

    llm = {}
    for r in csv.DictReader(open(DATA / "agentic_coverage.csv", newline="")):
        llm[int(r["task_id"])] = float(r["coverage"])

    rows = list(csv.DictReader(open(AUDIT, newline="")))
    tasks = [int(r["task_id"]) for r in rows]
    mat = np.array([[float(r[f"annotator_{i}"]) for i in (1, 2, 3)] for r in rows])
    human = mat.mean(axis=1)
    model = np.array([llm[t] for t in tasks])

    print("=" * 66)
    print("HUMAN VALIDATION OF THE AGENTIC COVERAGE DATASET")
    print("=" * 66)
    print(f"\nreleased dataset      : {len(llm):,} tasks")
    print(f"audit sample          : {len(tasks)} tasks x {mat.shape[1]} annotators "
          f"= {mat.size:,} ratings")

    print("\n--- headline: model vs human panel mean ---")
    r = float(np.corrcoef(model, human)[0, 1])
    rho = spearman(model, human)
    mae = float(np.abs(model - human).mean())
    rmse = float(np.sqrt(((model - human) ** 2).mean()))
    bias = float((model - human).mean())
    icc = icc_2k(mat)
    ceiling = float(np.sqrt(icc))
    print(f"  Pearson r                     : {r:.3f}")
    print(f"  Spearman rho                  : {rho:.3f}")
    print(f"  MAE                           : {mae:.3f}")
    print(f"  RMSE                          : {rmse:.3f}")
    print(f"  mean signed bias (model-human): {bias:+.3f}")
    print(f"  within +/-0.20                : {(np.abs(model-human)<=0.20).mean()*100:.1f}%")
    print(f"  within +/-0.25                : {(np.abs(model-human)<=0.25).mean()*100:.1f}%")

    print("\n--- inter-annotator reliability (the ceiling on any predictor) ---")
    print(f"  ICC(2,k) absolute agreement   : {icc:.3f}")
    print(f"  mean per-task SD              : {mat.std(axis=1, ddof=1).mean():.3f}")
    print(f"  reliability ceiling sqrt(ICC) : {ceiling:.3f}")
    print(f"  model Spearman / ceiling      : {rho/ceiling*100:.1f}% of attainable")
    for i, j in itertools.combinations(range(3), 2):
        print(f"  annotator_{i+1} vs annotator_{j+1}         : "
              f"r={np.corrcoef(mat[:,i],mat[:,j])[0,1]:.3f}  "
              f"mean|diff|={np.abs(mat[:,i]-mat[:,j]).mean():.3f}")

    print("\n--- leave-one-annotator-out (no single annotator drives it) ---")
    for d in range(3):
        keep = [i for i in range(3) if i != d]
        h = mat[:, keep].mean(axis=1)
        print(f"  without annotator_{d+1}          : r={np.corrcoef(model,h)[0,1]:.3f}  "
              f"MAE={np.abs(model-h).mean():.3f}")

    print("\n--- per-annotator vs model ---")
    for i in range(3):
        v = mat[:, i]
        print(f"  annotator_{i+1}: mean={v.mean():.3f} sd={v.std(ddof=1):.3f}  "
              f"r={np.corrcoef(v,model)[0,1]:.3f}  rho={spearman(v,model):.3f}")

    print("\n--- released dataset distribution ---")
    allc = np.array(list(llm.values()))
    print(f"  mean={allc.mean():.3f}  sd={allc.std(ddof=1):.3f}  "
          f"median={np.median(allc):.2f}  min={allc.min():.2f}  max={allc.max():.2f}")
    for lo, hi in [(0, .2), (.2, .4), (.4, .6), (.6, .8), (.8, 1.01)]:
        n = int(((allc >= lo) & (allc < hi)).sum())
        print(f"  [{lo:.1f},{hi:.1f}) {n:>6,}  {n/len(allc)*100:>5.1f}%")
    print("=" * 66)


if __name__ == "__main__":
    main()
