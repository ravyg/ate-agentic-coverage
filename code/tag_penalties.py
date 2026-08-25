#!/usr/bin/env python3
"""
Tag unique O*NET tasks with the four COV penalty categories (P1-P4)
using the exact keyword logic from calibration/compute_ate_session.py.

Purpose: build the sample for empirically ESTIMATING the penalty weights
(instead of asserting them). Output is a per-task table of P1-P4 trip
indicators plus a stratified pilot sample with a no-penalty control group.

This script does NOT assign coverage values. Coverage is measured
separately (LLM panel / human annotators) with a neutral instrument.
"""
import csv
import sys
from pathlib import Path

# Source task list. Default: the O*NET task->ability mapping (Zenodo 10.5281/zenodo.21989176).
# Any CSV with columns task_id, occupation, task_text works. Falls back to the
# bundled tasks_tagged.csv (which already contains all 18,796 task texts) if absent.
_ROOT = Path(__file__).resolve().parent.parent
DATASET = Path.home() / "workplace/ate-task-ability-dataset/data/task_ability_mapping.csv"
if not DATASET.exists():
    DATASET = _ROOT / "data" / "tasks_tagged.csv"
OUT_DIR = _ROOT / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Exact keyword logic copied from compute_ate_session.py (COV_PENALTIES) ---
COV_PENALTIES = {
    "P1_interpersonal": ["negotiate", "counsel", "mediate", "comfort", "de-escalate",
                         "patient interaction", "rapport", "empathy", "console",
                         "persuade", "motivate", "mentor", "coach", "interview"],
    "P2_regulatory":    ["fiduciary", "regulatory compliance", "certify", "notarize",
                         "prescribe", "diagnose", "sworn", "testimony", "liability",
                         "licensure", "binding agreement", "legal authority"],
    "P3_physical":      ["physically", "lift", "operate machinery", "on-site",
                         "field work", "manual", "hands-on", "physical exam",
                         "drive", "transport", "carry", "assemble", "repair",
                         "install", "construct", "clean", "inspect physically"],
    "P4_exception":     ["emergency", "crisis", "escalate", "override",
                         "judgment call", "novel situation", "unpredictable",
                         "improvise", "triage", "life-threatening"],
}
CATS = list(COV_PENALTIES.keys())


def trips(task_text):
    """Return dict cat -> 0/1 using the same substring match as compute_cov."""
    low = task_text.lower()
    return {c: int(any(k.lower() in low for k in kws))
            for c, kws in COV_PENALTIES.items()}


def main():
    # Dedupe to unique tasks (mapping has one row per task-ability pair)
    tasks = {}
    with open(DATASET, newline="") as f:
        for row in csv.DictReader(f):
            tid = row["task_id"]
            if tid not in tasks:
                tasks[tid] = {"task_id": tid,
                              "occupation": row["occupation"],
                              "task_text": row["task_text"]}
    for t in tasks.values():
        t.update(trips(t["task_text"]))
        t["n_cats"] = sum(t[c] for c in CATS)

    rows = list(tasks.values())
    print(f"Unique tasks: {len(rows)}")
    print("Per-category trip counts (task fires that penalty at least once):")
    for c in CATS:
        n = sum(r[c] for r in rows)
        print(f"  {c:18s} {n:6d}  ({100*n/len(rows):.1f}%)")
    none = sum(1 for r in rows if r["n_cats"] == 0)
    multi = sum(1 for r in rows if r["n_cats"] >= 2)
    print(f"  {'no penalty':18s} {none:6d}  ({100*none/len(rows):.1f}%)")
    print(f"  {'>=2 penalties':18s} {multi:6d}  ({100*multi/len(rows):.1f}%)")

    # Full tagged table
    fields = ["task_id", "occupation", "task_text"] + CATS + ["n_cats"]
    with open(OUT_DIR / "tasks_tagged.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {OUT_DIR/'tasks_tagged.csv'}")


if __name__ == "__main__":
    main()
