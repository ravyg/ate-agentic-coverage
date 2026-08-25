# Running the full estimation (for a collaborator)

This reproduces the pilot and scales it to the full task corpus. Everything is
plain Python + numpy. No API keys are needed for the deterministic steps; the
coverage-labeling step needs either the crowdsource form (humans) or an LLM panel.

## 0. Requirements
```bash
python3 -m pip install numpy
```

## 1. Tag every task with its penalty categories (deterministic)
Uses the exact keyword logic from the ATES code (`compute_ate_session.py`).
```bash
python3 code/tag_penalties.py
# -> data/tasks_tagged.csv  (all 18,796 tasks, columns P1..P4, n_cats)
```
It reads the O*NET task→ability mapping if present
(`~/workplace/ate-task-ability-dataset/data/task_ability_mapping.csv`,
Zenodo 10.5281/zenodo.21989176); otherwise it falls back to the bundled
`data/tasks_tagged.csv`.

## 2. Build the sample to label
```bash
python3 code/build_pilot.py          # 100-task stratified pilot (seed 42)
```
For a larger, tighter estimate, edit `PER_CAT` / `N_CONTROL` in `build_pilot.py`
(e.g. 80 per category + 80 controls = 400 tasks), or label every
penalty-triggering task plus a control sample.

## 3. Collect coverage labels (the one step that needs people or a model)
Two interchangeable options; both are blind to the penalty scheme.

**A. Humans (authoritative).** Deploy `crowdsource/` (see its DEPLOY.md),
share the link, download the `Responses` tab, save it as
`results/human_ratings.csv` with columns `task_id,coverage` (coverage 0–1).

**B. LLM panel (fast, provisional).** Give several independent raters the
neutral `INSTRUMENT.md` + `data/rater_input.csv` and have each write
`results/ratings_raterN.csv` (columns `task_id,coverage,reason`). The pilot in
this repo used 4 raters this way.

## 4. Estimate the weights
```bash
python3 code/estimate_weights.py
# -> results/estimated_weights.csv
# prints judgment vs estimated weight + bootstrap 95% CI per penalty
```
`estimate_weights.py` pools every `results/ratings_rater*.csv`. To use human
labels, either name the file `ratings_rater_human.csv` or edit the glob.

## What you get
For each penalty (P1–P4): the estimated multiplicative weight, a bootstrap 95%
CI, and whether the paper's judgment value (0.75 / 0.70 / 0.60 / 0.80) falls
inside it. Plus the base (no-penalty) coverage and mean inter-rater spread.

## Honesty rules baked in
- Coverage is measured directly and independently of CAP; do **not** fit weights
  to Eloundou/AIOE (circular).
- LLM-panel labels are provisional until human labels replace them.
- Report the result whichever way it comes out, including if a weight shifts.
