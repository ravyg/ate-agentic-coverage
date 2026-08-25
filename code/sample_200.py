#!/usr/bin/env python3
"""
sample_200.py — build a balanced 200-task human-validation sample.

Design (mirrors the pilot, scaled up for a clean, defensible validation):
  - 40 tasks per single-barrier category (P1, P2, P3, P4), each tripping EXACTLY
    one category so each weight is cleanly identified.
  - 40 no-barrier controls (n_cats == 0) to anchor the baseline coverage.
  - Total = 200, balanced across the five strata.
  - Spread across occupations: at most MAX_PER_OCC tasks from one occupation per
    stratum (relaxed only if a stratum can't otherwise fill), so no single job
    dominates the estimate.
  - Excludes the 100 pilot tasks, so this is a fresh, independent sample.
  - Fixed seed 42 -> fully reproducible.

Outputs:
  data/validation_200.csv      BLIND (task_id, occupation, task_text) -> feeds the form
  data/validation_200_key.csv  our copy WITH stratum + flags -> for the analysis only
"""
import csv
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CATS = ["P1_interpersonal", "P2_regulatory", "P3_physical", "P4_exception"]
PER_CAT = 40
N_CONTROL = 40
MAX_PER_OCC = 2
SEED = 42


def pick_spread(pool, n, rng):
    """Sample n tasks, capping tasks per occupation at MAX_PER_OCC; relax if needed."""
    rng.shuffle(pool)
    for cap in (MAX_PER_OCC, MAX_PER_OCC + 2, 10**9):
        chosen, per_occ = [], defaultdict(int)
        for r in pool:
            if len(chosen) == n:
                break
            occ = r["occupation"]
            if per_occ[occ] < cap:
                chosen.append(r)
                per_occ[occ] += 1
        if len(chosen) == n:
            return chosen
    return chosen  # fewer than n available


def main():
    rows = list(csv.DictReader(open(DATA / "tasks_tagged.csv", newline="")))
    for r in rows:
        for c in CATS:
            r[c] = int(r[c])
        r["n_cats"] = int(r["n_cats"])

    pilot_ids = set()
    pilot_path = DATA / "pilot_tasks.csv"
    if pilot_path.exists():
        pilot_ids = {r["task_id"] for r in csv.DictReader(open(pilot_path, newline=""))}

    avail = [r for r in rows if r["task_id"] not in pilot_ids]
    rng = random.Random(SEED)
    sample = []

    for c in CATS:
        pool = [r for r in avail if r["n_cats"] == 1 and r[c] == 1]
        pick = pick_spread(pool, PER_CAT, rng)
        for r in pick:
            r["stratum"] = c
        sample += pick
        print(f"{c:18s} pool={len(pool):5d}  picked={len(pick):3d}  "
              f"occs={len({r['occupation'] for r in pick})}")

    pool = [r for r in avail if r["n_cats"] == 0]
    pick = pick_spread(pool, N_CONTROL, rng)
    for r in pick:
        r["stratum"] = "control_none"
    sample += pick
    print(f"{'control_none':18s} pool={len(pool):5d}  picked={len(pick):3d}  "
          f"occs={len({r['occupation'] for r in pick})}")

    # blind file for the form
    with open(DATA / "validation_200.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["task_id", "occupation", "task_text"],
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(sample)

    # keyed file for our analysis only (NOT hosted)
    with open(DATA / "validation_200_key.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["task_id", "occupation", "task_text",
                                          "stratum"] + CATS, extrasaction="ignore")
        w.writeheader()
        w.writerows(sample)

    print(f"\nTotal validation tasks: {len(sample)}")
    print(f"Distinct occupations   : {len({r['occupation'] for r in sample})}")
    print(f"Wrote {DATA/'validation_200.csv'} (blind) and validation_200_key.csv (keyed)")


if __name__ == "__main__":
    main()
