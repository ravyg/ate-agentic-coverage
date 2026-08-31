# Methodology

How the agentic-coverage dataset was constructed and validated.

## 1. Source data

- **O\*NET 30.2** (U.S. Department of Labor): the full task statement corpus,
  18,796 tasks spanning all SOC major groups, with occupation titles.
- This dataset labels **coverage**, not ability requirements — it is a
  companion to, not a replacement for, the
  [O\*NET Task→Ability Mapping Dataset](https://github.com/ravyg/ate-task-ability-dataset),
  which maps each task to the O\*NET abilities it requires. Coverage answers a
  different question: even where an agent has the relevant ability, how much of
  the task can it complete *alone*, end to end?

## 2. Labeling instrument

Every task was scored against one deliberately **neutral** instrument
([`../scripts/LABELING_SPEC_COVERAGE.md`](../scripts/LABELING_SPEC_COVERAGE.md),
mirrored for the earlier pilot in [`../INSTRUMENT.md`](../INSTRUMENT.md)):

> Consider a capable autonomous software AI agent in 2026. It can browse, write,
> call APIs and tools, reason, and generate text, images, audio, and code. It has
> no physical body and no legal or professional authority of its own. What
> fraction of this task could the agent carry out end to end, on its own, with no
> human stepping in to act, be physically present, decide, or take
> responsibility?

The instrument never mentions the ATES workflow-coverage penalty categories
(interpersonal, regulatory, physical, exception) or any prior exposure index, so
labels are not circular with the model they were built to inform. A fixed set of
calibration anchors (e.g. "physically install equipment on site" → 0.00; "draft a
routine status email from notes" → 0.95) keeps scoring consistent across the
corpus without ever revealing a category scheme to the labeler.

## 3. Labeling pass

Labels were produced by a large language model (**Claude Sonnet**), prompted with
the task text, its occupation, and the labeling spec above, in **one consistent
pass across the entire corpus** — the same method was applied to every task, with
no per-group or per-chunk variation.

The pipeline in [`../scripts/`](../scripts/) makes the pass reproducible and
resumable:

1. **`make_chunks.py`** — deterministic. Splits the 18,796 tasks into 145 blind
   chunks of 130 tasks, carrying only `task_id, occupation, task_text` (no
   penalty flags or other signal that could leak the downstream use of the
   labels).
2. **Labeling** ([`../scripts/RUN_WITH_CLAUDE.md`](../scripts/RUN_WITH_CLAUDE.md))
   — each chunk is labeled by Claude Sonnet against the spec above. A chunk is
   "done" once its output CSV exists, so a labeling run can be interrupted (e.g.
   by a usage limit) and resumed without re-labeling finished chunks or losing
   track of what's left.
3. **`merge_validate.py`** — deterministic. Validates `coverage ∈ [0, 1]`,
   dedupes, reconciles against the chunk manifest, and merges everything into
   [`../data/agentic_coverage.csv`](../data/agentic_coverage.csv). It reports
   exactly which chunks are missing if the run is incomplete, and prints
   `ALL TASKS LABELED ✔` once every task has a score.

## 4. Validation

### Sample

A **200-task stratified sample** (seed 42) was drawn: 40 tasks per ATES penalty
category (interpersonal, regulatory, physical, exception) plus 40 no-penalty
controls, spanning 180 distinct occupations.

### Human re-annotation

**Three independent annotators** each scored the full 200-task sample using the
same blind instrument as the model, via a purpose-built web form
([`../crowdsource/`](../crowdsource/)). Annotators saw only the occupation and
task text — never the model's label, the penalty categories, or each other's
entries.

### Agreement metrics

Model-vs-human agreement and inter-annotator reliability are reported as
Spearman's ρ, Pearson's r, ICC(2,k), MAE, and mean signed bias. **Full numbers,
their scope, and their interpretation live in
[`../validation/RESULTS.md`](../validation/RESULTS.md) — see that file rather
than this one for the results themselves; this document only describes how they
were produced.** The computation is reproducible end to end:

```bash
python3 validation/compute_validation.py
```

## 5. Known limitations

- Coverage reflects a single consistent model's judgment, not an ensemble or
  majority vote, though it is validated against an independent human panel.
- Absolute coverage values run conservative relative to human judgment (see
  `validation/RESULTS.md` for the documented calibration gap and a suggested
  correction); relative ordering (ranking) is not affected.
- The instrument asks about *unaided* completion; it does not model
  human-in-the-loop or human-AI collaborative workflows, which is a distinct
  (and generally higher) coverage question.
- Coverage is scored against 2026-era agent capability; it is a snapshot, not a
  forecast, and is expected to shift as agent capability changes.
- Coverage is the U.S. O\*NET taxonomy; cross-country transfer is untested here.
