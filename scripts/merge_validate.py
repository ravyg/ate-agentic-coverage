#!/usr/bin/env python3
"""
merge_validate.py — merge all per-chunk coverage CSVs into the final dataset.

Mirrors the task->ability pipeline's merge_validate.py. Reads manifest.json for the
expected task_ids, globs partial_output/chunk_*.csv, validates every row, dedupes,
and writes ../data/agentic_coverage.csv. Reports any tasks still unlabeled so the
run can be resumed by re-labeling only the missing chunks.

Usage:  python3 merge_validate.py
"""
import csv
import glob
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MANIFEST = HERE / "manifest.json"
OUT_DIR = HERE / "partial_output"
FINAL = ROOT / "data" / "agentic_coverage.csv"

FIELDS = ["task_id", "occupation", "task_text", "coverage", "rationale"]


def expected_ids():
    ids = set()
    for entry in json.loads(MANIFEST.read_text()):
        chunk = json.loads((HERE / entry["input"]).read_text())
        for t in chunk:
            ids.add(t["task_id"])
    return ids


def main():
    want = expected_ids()
    rows, seen, errors = {}, set(), []

    for path in sorted(glob.glob(str(OUT_DIR / "chunk_*.csv"))):
        with open(path, newline="") as f:
            for i, r in enumerate(csv.DictReader(f), start=2):
                tid = (r.get("task_id") or "").strip()
                if not tid:
                    errors.append(f"{Path(path).name}:{i} blank task_id")
                    continue
                try:
                    cov = float(r["coverage"])
                except (KeyError, ValueError):
                    errors.append(f"{Path(path).name}:{i} bad coverage {r.get('coverage')!r}")
                    continue
                if not (0.0 <= cov <= 1.0):
                    errors.append(f"{Path(path).name}:{i} coverage out of range: {cov}")
                    continue
                if tid in seen:
                    continue  # first write wins; duplicates ignored
                seen.add(tid)
                rows[tid] = {
                    "task_id": tid,
                    "occupation": r.get("occupation", ""),
                    "task_text": r.get("task_text", ""),
                    "coverage": f"{cov:.2f}",
                    "rationale": (r.get("rationale") or "").strip(),
                }

    FINAL.parent.mkdir(parents=True, exist_ok=True)
    with open(FINAL, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for tid in sorted(rows):
            w.writerow(rows[tid])

    missing = want - seen
    extra = seen - want

    print(f"Expected tasks : {len(want)}")
    print(f"Labeled tasks  : {len(seen)}")
    print(f"Wrote          : {FINAL}  ({len(rows)} rows)")
    if extra:
        print(f"WARNING: {len(extra)} labeled task_ids not in manifest (ignored count): "
              f"{list(sorted(extra))[:5]}...")
    if errors:
        print(f"\n{len(errors)} row error(s) (first 20):")
        for e in errors[:20]:
            print("  -", e)
    if missing:
        # map missing ids back to the chunks that still need labeling
        need_chunks = set()
        for entry in json.loads(MANIFEST.read_text()):
            chunk = json.loads((HERE / entry["input"]).read_text())
            if any(t["task_id"] in missing for t in chunk):
                need_chunks.add(entry["output"])
        print(f"\nUNLABELED: {len(missing)} task(s) still need coverage.")
        print(f"Re-label these {len(need_chunks)} chunk output(s):")
        for c in sorted(need_chunks):
            print("  -", c)
    else:
        print("\nALL TASKS LABELED ✔")


if __name__ == "__main__":
    main()
