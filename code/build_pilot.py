#!/usr/bin/env python3
"""
Build a stratified pilot sample for coverage labeling.

Strategy: sample tasks that trip EXACTLY ONE penalty category (clean
identification of each weight), plus a no-penalty control group. Fixed
seed 42 to match the audit-sample convention.

Output: pilot_tasks.csv (task_id, occupation, task_text, stratum, P1-P4)
Coverage is NOT assigned here; it is measured by the labeling instrument.
"""
import csv
import random
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"   # repo root / data
CATS = ["P1_interpersonal", "P2_regulatory", "P3_physical", "P4_exception"]
PER_CAT = 20          # single-category tasks per penalty
N_CONTROL = 20        # no-penalty controls
SEED = 42


def main():
    rows = list(csv.DictReader(open(DATA / "tasks_tagged.csv", newline="")))
    for r in rows:
        for c in CATS:
            r[c] = int(r[c])
        r["n_cats"] = int(r["n_cats"])

    rng = random.Random(SEED)
    pilot = []

    # exactly-one-category strata
    for c in CATS:
        pool = [r for r in rows if r["n_cats"] == 1 and r[c] == 1]
        pick = rng.sample(pool, min(PER_CAT, len(pool)))
        for r in pick:
            r["stratum"] = c
        pilot += pick
        print(f"{c:18s} pool={len(pool):5d}  sampled={len(pick)}")

    # no-penalty control
    pool = [r for r in rows if r["n_cats"] == 0]
    pick = rng.sample(pool, N_CONTROL)
    for r in pick:
        r["stratum"] = "control_none"
    pilot += pick
    print(f"{'control_none':18s} pool={len(pool):5d}  sampled={len(pick)}")

    fields = ["task_id", "occupation", "task_text", "stratum"] + CATS
    with open(DATA / "pilot_tasks.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(pilot)
    print(f"\nTotal pilot tasks: {len(pilot)}")
    print(f"Wrote {DATA/'pilot_tasks.csv'}")


if __name__ == "__main__":
    main()
