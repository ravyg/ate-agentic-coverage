#!/usr/bin/env python3
"""
make_chunks.py — split the full task corpus into blind chunks for coverage labeling.

Mirrors the task->ability pipeline: writes chunks/chunk_NNN.json (a JSON array of
tasks) plus manifest.json listing every chunk. Chunks contain ONLY
task_id, occupation, task_text — no penalty flags — so annotators/Claude cannot
reverse-engineer the penalty weights we later estimate from these labels.

Idempotent: a chunk is "done" when its output CSV exists under partial_output/.

Usage:  python3 make_chunks.py            # default 130 tasks/chunk (matches ability pipeline)
        python3 make_chunks.py --size 100
"""
import argparse
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "data" / "tasks_tagged.csv"     # all 18,796 tasks (blind fields only used)
CHUNK_DIR = HERE / "chunks"
OUT_DIR = HERE / "partial_output"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=130, help="tasks per chunk")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(SRC, newline="")))
    # dedupe by task_id, keep only blind fields, stable order
    seen, tasks = set(), []
    for r in rows:
        tid = r["task_id"]
        if tid in seen:
            continue
        seen.add(tid)
        tasks.append({"task_id": tid,
                      "occupation": r["occupation"],
                      "task_text": r["task_text"]})

    CHUNK_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = []
    n = args.size
    for ci in range((len(tasks) + n - 1) // n):
        chunk = tasks[ci * n:(ci + 1) * n]
        name = f"chunk_{ci:03d}"
        (CHUNK_DIR / f"{name}.json").write_text(
            json.dumps(chunk, ensure_ascii=False, indent=1), encoding="utf-8")
        manifest.append({
            "chunk": ci,
            "n_tasks": len(chunk),
            "input": f"chunks/{name}.json",
            "output": f"partial_output/{name}.csv",
            "status": "todo",
        })

    (HERE / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Tasks: {len(tasks)}   chunks: {len(manifest)} x {n}/chunk")
    print(f"Wrote {CHUNK_DIR}/chunk_*.json and manifest.json")
    print(f"Output dir ready: {OUT_DIR} (empty until labeling runs)")


if __name__ == "__main__":
    main()
