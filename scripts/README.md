# scripts/ — full-corpus coverage generation pipeline

This is the resumable, one-command pipeline for labeling **all 18,796 tasks** with an
agentic-coverage score. It mirrors the task->ability dataset's generation pipeline
exactly, so if you've run that one, this is the same shape: chunk → label → merge.

```
scripts/
  make_chunks.py             Split data/tasks_tagged.csv into blind chunks
  LABELING_SPEC_COVERAGE.md  Ground truth: how to score one task (blind to penalties)
  RUN_WITH_CLAUDE.md         The paste-into-Claude prompt (Sonnet, parallel, resumable)
  merge_validate.py          Merge partial CSVs → data/agentic_coverage.csv + validate
  chunks/                    chunk_000.json … chunk_144.json  (generated; blind fields only)
  manifest.json              One entry per chunk (input, output, status)  (generated)
  partial_output/            chunk_000.csv …  (written as labeling proceeds)
```

## The flow

1. **`make_chunks.py`** — deterministic. Dedupes tasks, strips to the three blind fields
   (`task_id, occupation, task_text`), writes 145 chunks of 130 tasks + `manifest.json`.
   No penalty flags ever enter a chunk, so the labeler cannot reverse-engineer the scheme.

2. **`RUN_WITH_CLAUDE.md`** — the only step that needs a model. Runs inside Claude Code on
   the collaborator's own plan (Sonnet, no API key). A chunk is "done" when its output CSV
   exists, so the run is **resumable**: hit a usage limit, restart, and it skips finished
   chunks. Up to 10 chunks label in parallel.

3. **`merge_validate.py`** — deterministic. Validates coverage ∈ [0,1], dedupes, confirms
   all task_ids are present, writes `data/agentic_coverage.csv`, and if anything is missing
   tells you exactly which chunks to re-run. Prints `ALL TASKS LABELED ✔` when complete.

## Output schema

`data/agentic_coverage.csv`, one row per task:

```
task_id,occupation,task_text,coverage,rationale
```

`coverage` is 0.00–1.00 (how much an autonomous agent could complete alone, end to end).
`rationale` is a one-clause reason.

## Resumability contract (why restarts are safe)

- Chunk boundaries are fixed by `make_chunks.py` (stable order, seed-free dedupe), so the
  same task always lands in the same chunk.
- The labeler writes one output CSV per chunk and treats an existing output as done.
- `merge_validate.py` reconciles against `manifest.json`, so a partial run never silently
  loses or double-counts tasks.

## Relationship to the pilot in `code/`

`code/` holds the 100-task **pilot** that estimated the weights (blind LLM panel +
regression). `scripts/` scales the same neutral instrument to the **full corpus** to
produce the released dataset and to re-estimate the weights on all tasks. Same question,
same blinding, bigger N.
