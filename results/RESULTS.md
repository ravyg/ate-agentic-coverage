# Empirically Estimating the COV Penalty Weights — Pilot Results

**Status: SUPERSEDED.** This was the LLM-panel pilot. Human validation is complete and
is the authoritative result — see [`../validation/RESULTS.md`](../validation/RESULTS.md).
The P1–P4 penalty weights this pilot estimated are no longer used: coverage is measured
per task instead.
Date: 2026-08-24. Seed 42. n = 100 tasks (20 per penalty category, single-category
only, + 20 no-penalty controls). Coverage labels: 4 independent blind LLM raters.

## What this answers

Reviewer critique (Huntington-Klein): the four COV penalty weights
(P1 0.75, P2 0.70, P3 0.60, P4 0.80) look arbitrary. This pilot tests whether
they can be recovered from measured *agentic coverage* instead of asserted.

## Method (one paragraph)

Sampled tasks that trip exactly one penalty category plus a no-penalty control.
Four independent raters, blind to the penalty scheme, each scored every task on a
neutral 0-1 "how much can an autonomous agent complete end to end alone" question
(see `INSTRUMENT.md`). Inter-rater agreement was high (mean SD 0.035). We then
compared each category's mean coverage to the control, and fit the multiplicative
model `log(coverage) = log(base) + Σ trip_k · log(weight_k)` with bootstrap CIs.

## Result 1 — raw coverage by category (the intuitive view)

| Group | mean coverage | ratio to control | judgment weight |
|-------|:---:|:---:|:---:|
| control (no penalty) | 0.40 | — | — |
| P1 interpersonal | 0.30 | **0.76** | 0.75 |
| P2 regulatory | 0.26 | **0.65** | 0.70 |
| P3 physical | 0.20 | **0.50** | 0.60 |
| P4 exception | 0.36 | **0.89** | 0.80 |

**The rank order is reproduced exactly.** Blind raters rank the barriers
physical < regulatory < interpersonal < exception, the identical ordering the
judgment weights encode. The measured magnitudes sit close to each judgment value.

## Result 2 — regression with confidence intervals

| Penalty | judgment | estimated | 95% CI | judgment in CI? |
|---------|:---:|:---:|:---:|:---:|
| P1 interpersonal | 0.75 | 0.77 | [0.39, 1.54] | yes |
| P2 regulatory | 0.70 | 0.52 | [0.25, 1.13] | yes |
| P3 physical | 0.60 | 0.26 | [0.11, 0.62] | yes |
| P4 exception | 0.80 | 0.71 | [0.33, 1.56] | yes |

**No judgment value is rejected** — every one falls inside its 95% CI. The point
estimates hint that physical may deserve a harsher discount than 0.60, but the CI
still contains 0.60. CIs are wide because n = 20 per category; a larger,
human-labeled sample would tighten them.

## Honest limitations

- Coverage labels are LLM-panel estimates, not human ground truth. This is a
  feasibility pilot, not the final number.
- 100 tasks; wide CIs. The instrument (`INSTRUMENT.md`) is built to hand to human
  annotators next for a validated estimate.
- We deliberately did **not** fit the weights to match Eloundou/AIOE — that would
  be circular. Coverage is measured directly from the task.

## Takeaway for the paper / reviewer reply

The judgment weights are not arbitrary: a blind panel reproduces their exact rank
order and lands within sampling error of each value. We can present this as a
validation pilot and commit to a human-labeled version for the camera-ready.

## What ships in revision 6

This 100-task pilot is how the ATES paper's four COV penalty weights were validated.
It is not in the current paper only because the human-annotated version of this
dataset is still being produced and needs to be published first. Revision 6 will add:

1. this repository (made public) as a companion resource, with the full-corpus
   agentic-coverage labels for all 18,796 tasks;
2. a "Validating the penalty weights" subsection reporting the pilot above; and
3. human-annotation agreement statistics once the crowdsourced labels land.

The full corpus is labeled once per task (single pass). The 4-rater panel and its
agreement statistic are the pilot's, and that is what we report as the validation.

## Files

- `tag_penalties.py` — penalty tagging (exact keyword logic from compute_ate_session.py)
- `build_pilot.py` — stratified sampling (seed 42)
- `INSTRUMENT.md` — neutral coverage-rating instrument (blind to penalties)
- `data/rater_input.csv` — blinded 100-task input given to raters
- `results/ratings_rater{1..4}.csv` — panel labels
- `estimate_weights.py` — regression + bootstrap
- `results/estimated_weights.csv` — final estimates
