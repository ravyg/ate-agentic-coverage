# Build the agentic-coverage dataset with Claude Code (one command, resumable)

This labels all **18,796 tasks** with an agentic-coverage score using **your own
Claude plan** inside Claude Code. **No API key. No pip install. No cost beyond your
Claude subscription.** Claude reads each chunk plus the labeling spec and writes one
CSV per chunk. It runs on **Sonnet**, spawns several chunks in parallel, and is fully
**resumable** — if you hit your usage limit and restart, it skips every chunk already
done and picks up where it left off.

## What you need
- This repo cloned locally.
- Claude Code installed and signed in (`claude`), on a plan with Sonnet.
- Python 3 (only for the two deterministic steps: making chunks + merging).

## Step 0 — one-time prep (only if `scripts/chunks/` is empty)
```bash
cd ate-agentic-coverage
python3 scripts/make_chunks.py     # -> scripts/chunks/chunk_000.json … + manifest.json
```
You should see `Tasks: 18796   chunks: 145 x 130/chunk`.

## Step 1 — run the labeling (this is the "one command": open Claude and paste)
From the repo root, start Claude Code:
```bash
cd ate-agentic-coverage
claude
```
Then paste this prompt verbatim:

---
You are labeling agentic coverage for the ATES dataset. Work entirely inside this repo.

1. Read `scripts/LABELING_SPEC_COVERAGE.md` in full. It is the ground truth for how to
   score. Every task gets ONE number `coverage` in [0.00, 1.00] and a short rationale.
2. Read `scripts/manifest.json`. Each entry has an `input` chunk and an `output` CSV.
3. A chunk is DONE when its `output` file already exists and is non-empty. **Skip every
   done chunk** — never relabel it. This is what makes the run resumable.
4. For each remaining chunk: read the input JSON, score every task per the spec, and
   write the output CSV with header exactly `task_id,occupation,task_text,coverage,rationale`.
   One row per input task, no tasks skipped, no duplicates. Preserve task_id, occupation,
   and task_text exactly. CSV-quote any field containing a comma.
5. Use the **Sonnet** model. Spawn subagents to work on up to **10 chunks in parallel**;
   as each finishes, start the next, until every chunk has an output CSV.
6. Do NOT invent penalty categories, tags, or extra columns. Do NOT look at or use any
   penalty flags — you are rating raw coverage only.
7. When all chunks have outputs, stop and tell me how many chunks and tasks you labeled.

Begin now. If you get interrupted or hit a limit, I will paste this again and you will
resume from the first chunk that has no output file.
---

If you run out of usage, just start `claude` again and paste the same prompt. It resumes.

## Step 2 — merge and validate (deterministic)
```bash
python3 scripts/merge_validate.py
```
This checks every coverage value is in [0,1], dedupes, confirms all 18,796 task_ids are
present, and writes the final dataset to `data/agentic_coverage.csv`. If anything is
missing it prints exactly which chunks still need labeling — re-run Step 1 to fill them,
then run this again. When it prints **`ALL TASKS LABELED ✔`** you are done.

## Step 3 — (optional) re-estimate the penalty weights on the full data
```bash
python3 -m pip install numpy
python3 code/estimate_weights.py
```

## Honesty rules (baked in)
- Coverage is rated directly and blind to the penalty scheme — never fit to it.
- Label every task the same way, using the spec's anchors. Two labelers should land
  within ~0.15.
- Report results however they come out.
