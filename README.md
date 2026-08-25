# Agentic Coverage Dataset — Estimating the ATES Workflow-Coverage Penalties

Companion resource to the **ATES** (Agentic Task Exposure Score) framework and the
[O\*NET Task→Ability Mapping Dataset](https://doi.org/10.5281/zenodo.21989176).

This repo answers one question with data: **how much of each work task can an
autonomous AI agent complete on its own, end to end, with no human in the loop?**
That measurement lets us *estimate* the ATES workflow-coverage (COV) penalty
weights instead of asserting them.

> ⚠️ **Status: pilot / provisional.** The coverage labels here come from an
> LLM panel (4 independent blind raters, 100 tasks). Human validation using the
> included annotation form is the next step. Numbers will be updated when human
> labels land. Nothing here is fitted to any prior AI-exposure index.

---

## Why this exists

ATES discounts a task's automation exposure when completing it autonomously runs
into a barrier that raw capability cannot overcome:

| Penalty | Barrier | Judgment weight |
|--------|---------|:---:|
| P1 Interpersonal | needs human rapport / trust | ×0.75 |
| P2 Regulatory / fiduciary | needs legal authority / accountability | ×0.70 |
| P3 Physical | needs a body on site | ×0.60 |
| P4 Exception handling | needs novel human judgment | ×0.80 |

Those weights were expert judgment. A reviewer reasonably asked whether they are
arbitrary. This repo tests them: we measure agentic **coverage** per task with a
neutral instrument that never mentions the penalty scheme, then regress coverage
on which penalties each task triggers to recover the weights with confidence
intervals.

## Headline pilot result

Blind raters reproduce the **exact rank order** of the four penalties, and **no
judgment value is rejected** — each falls inside its 95% CI.

| Penalty | judgment | estimated (pilot) | 95% CI |
|---------|:---:|:---:|:---:|
| P1 Interpersonal | 0.75 | 0.77 | [0.39, 1.54] |
| P2 Regulatory | 0.70 | 0.52 | [0.25, 1.13] |
| P3 Physical | 0.60 | 0.26 | [0.11, 0.62] |
| P4 Exception | 0.80 | 0.71 | [0.33, 1.56] |

Raw coverage by group (ratio to the no-penalty control) tells the same story:
interpersonal 0.76, regulatory 0.65, physical 0.50, exception 0.89. Full write-up
in [`results/RESULTS.md`](results/RESULTS.md).

---

## What's here

```
INSTRUMENT.md              The neutral coverage question + calibration anchors
code/
  tag_penalties.py         Tag every task with P1-P4 (exact ATES keyword logic)
  build_pilot.py           Stratified sampling (seed 42)
  estimate_weights.py      Log-linear regression + bootstrap CIs
  RUN_FULL.md              How a collaborator scales this to all tasks
data/
  tasks_tagged.csv         All 18,796 tasks with penalty flags
  pilot_tasks.csv          The 100-task stratified pilot (with flags)
  rater_input.csv          Blinded input given to raters (no penalty columns)
results/
  ratings_rater{1..4}.csv  The LLM-panel coverage labels
  estimated_weights.csv    Estimated weights + CIs
  RESULTS.md               Method + results + limitations
crowdsource/
  Code.gs, Index.html      Google Apps Script annotation web app (coverage form)
  generate_index.py        Rebuild the form for any task set
  DEPLOY.md                5-minute deploy guide
```

## Reproduce in three commands

```bash
python3 -m pip install numpy
python3 code/tag_penalties.py       # or use the bundled data/tasks_tagged.csv
python3 code/estimate_weights.py    # prints the table above
```

## Method in one paragraph

Sample tasks that trip exactly one penalty category, plus a no-penalty control.
Independent raters, blind to the scheme, score each task 0–1 on *how much an
autonomous agent could complete alone* ([`INSTRUMENT.md`](INSTRUMENT.md)). Fit
`log(coverage) = log(base) + Σ_k trip_k · log(weight_k)`; `weight_k = exp(coef_k)`.
Controls identify the base; bootstrap over tasks gives CIs. See `RUN_FULL.md`.

## How this relates to CAP (why it is not double-counting)

CAP asks *is the AI able to do this kind of work?* (from the abilities a task
needs). COV asks *even if it is able, can an agent finish it alone, or must a
human stay in the loop?* These are different axes — except for **physical**,
where CAP already scores physical ability near zero, so P3 partially overlaps
CAP. This pilot measures coverage independently of CAP, so it can show whether P3
still carries signal after abilities are accounted for.

## License & citation

- Code and labels: **CC-BY-4.0** (see `LICENSE`). O\*NET task text is U.S. DoL public domain.
- If you use this, please cite the ATES paper and this dataset (see `CITATION.cff`).

## Contributing coverage labels

Want your name in the acknowledgements? Deploy the form in `crowdsource/`
(or ask us for the live link) and rate a batch of tasks. Two people rating the
same task is useful — it measures agreement.
