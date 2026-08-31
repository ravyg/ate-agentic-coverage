# Human Validation of the COV Penalty Weights (n=200, 3 annotators)

**Date:** 2026-08-31
**Data:** `data/human_annotations_raw.json` (605 rows, pulled from the Apps Script
`?export=json` endpoint), joined to `data/validation_200_key.csv`.
**Script:** `code/estimate_weights_human.py` — method mirrored exactly from
`code/estimate_weights.py` (multiplicative model, OLS on log coverage, FLOOR=0.02,
N_BOOT=5000, SEED=42) so human and LLM-panel results are directly comparable.

> **Bottom line: this does not cleanly confirm the four judgment weights.**
> Three of four survive their confidence intervals. **P4 exception (0.80) is rejected**,
> and the rank order the pilot reproduced is **not** reproduced by humans. The result is
> still usable for the reviewer reply, but it cannot be presented as a clean vindication.

---

## 1. Data quality

| Annotator | Rows | Distinct tasks |
|---|---:|---:|
| Maulik | 200 | 200 |
| Shreeya Sharma | 200 | 200 |
| Saket Kumar | 200 | 200 |

All three panel annotators completed the full 200-task set. All coverage values are
valid and within [0,1], on a 0.05 grid.

**Exclusions.** A small number of form-development test entries were excluded from the
headline estimate; they account for the only duplicated (annotator, task) pair and the
single leftover numeric `comment` value (residue from the confidence field removed in
commit `0bd0986`). **Their effect is nil**: including them moves every weight by ≤0.001.
Deduplication is last-wins per annotator and task, matching the form's resume semantics.

Analysis set: **600 ratings, 200 tasks × 3 annotators.**

---

## 2. Inter-rater reliability — substantially worse than the LLM panel

| Metric | Human panel | LLM panel (pilot) |
|---|---:|---:|
| Mean per-task SD | **0.189** | ≈0.035 |
| ICC(2,k), absolute agreement | 0.782 | — |

Humans disagree roughly **5.4× more** than the LLM raters did. ICC(2,k)=0.782 is
acceptable for a 3-rater average, but the raw spread is large relative to the effects
being measured.

**The disagreement is not uniform — one annotator is an outlier:**

| Pair | Pearson r | mean abs. diff |
|---|---:|---:|
| Saket vs Shreeya | **0.877** | 0.115 |
| Maulik vs Saket | 0.536 | 0.268 |
| Maulik vs Shreeya | **0.403** | 0.324 |

Saket and Shreeya agree closely. Maulik diverges from both. Fitting each annotator
alone makes this concrete:

| Annotator | P1 | P2 | P3 | P4 |
|---|---:|---:|---:|---:|
| Maulik | **2.95** | **2.01** | 0.59 | 0.47 |
| Saket | 0.81 | 0.60 | 0.34 | 0.50 |
| Shreeya | 0.61 | 0.55 | 0.43 | 0.59 |

Maulik's solo P1 and P2 exceed 1.0, which under this model would mean the penalty
*increases* agentic coverage. This is an artifact of fitting category means on a
high-variance rater, not evidence of a misread instrument: his raw ratings correlate
positively with both the model (r=0.586) and the other annotators, and he simply uses
the extremes of the scale far more (SD 0.411 vs 0.281 and 0.320). All three annotators
are retained; excluding him moves the pooled headline by 0.007.

---

## 3. Mean coverage by stratum (pooled, 3 annotators)

| Stratum | n obs | mean | sd | ratio to control |
|---|---:|---:|---:|---:|
| control (no penalty) | 120 | 0.605 | 0.334 | 1.000 |
| P1 interpersonal | 120 | 0.549 | 0.272 | 0.908 |
| P2 regulatory | 120 | 0.505 | 0.325 | 0.836 |
| P3 physical | 120 | 0.417 | 0.391 | 0.689 |
| P4 exception | 120 | 0.414 | 0.354 | 0.685 |

---

## 4. Headline estimate

Base coverage (no-penalty task): **0.540**

| Penalty | judgment | **human** | 95% CI | judgment in CI? | LLM pilot | LLM in human CI? |
|---|---:|---:|:---:|:---:|---:|:---:|
| P1 interpersonal | 0.75 | 0.90 | [0.70, 1.16] | **yes** | 0.77 | yes |
| P2 regulatory | 0.70 | 0.74 | [0.54, 1.00] | **yes** | 0.52 | no (just outside) |
| P3 physical | 0.60 | 0.37 | [0.23, 0.60] | **yes** (at the bound) | 0.26 | yes |
| P4 exception | 0.80 | 0.52 | [0.35, 0.74] | **NO — rejected** | 0.71 | yes |

Note P3's judgment value 0.60 sits exactly at the upper CI bound — it survives, but only
just, and the point estimate (0.37) suggests physical barriers deserve a harsher discount
than the paper assigns. The pilot flagged this same direction.

### Rank order is not reproduced

- Paper's judgment order: physical < regulatory < interpersonal < exception
- **Human order: physical (0.37) < exception (0.52) < regulatory (0.74) < interpersonal (0.90)**

P4 exception moves from *least*-penalized in the paper to *second-most*-penalized in the
human data. On the raw ratio-to-control measure the flip is starker still: exception
(0.685) is the **most** penalized category, marginally below physical (0.689).

For fairness to the pilot: its "rank order reproduced exactly" claim refers to its raw
ratio table (Result 1), where it holds. Its own regression estimates (Result 2) already
put exception below interpersonal — i.e. the two methods in the pilot disagreed about
P4, and the human data now sides with the regression.

### The P4 rejection is robust

Leave-one-annotator-out, in every case:

| Dropped | P4 estimate | 95% CI | 0.80 verdict | rank |
|---|---:|:---:|---|---|
| without Maulik | 0.55 | [0.38, 0.76] | rejected | P3 < P4 < P2 < P1 |
| without Saket | 0.53 | [0.37, 0.74] | rejected | P3 < P4 < P2 < P1 |
| without Shreeya | 0.47 | [0.29, 0.78] | rejected | P3 < P4 < P2 < P1 |

No single annotator drives it — including the outlier.

---

## 5. Human vs LLM panel — implication for the full-corpus run

Three of four LLM-panel estimates fall inside the human CIs (P1, P3, P4); P2 (0.52) sits
just outside the human interval [0.54, 1.00]. Point estimates are in the same region and
the two panels agree that physical is the harshest discount.

This is **moderately reassuring** for the 145-chunk, 18,796-task corpus labelled by the
LLM panel — it is not evidence that the corpus run is invalid. But the LLM panel's very
low disagreement (SD 0.035 vs humans' 0.189) now reads as false precision rather than
reliability: LLM raters agreed with each other far more than humans do on the same
instrument, which is a known failure mode, not a quality signal.

---

## 6. Verdict on the Huntington-Klein critique

**Partially answered; do not overclaim.**

What can be said honestly:
- The weights are **not arbitrary**. They were measured against blind human ratings, and
  three of four judgment values fall within sampling error of the measured value.
- The *direction* of the discount is confirmed for interpersonal, regulatory, and
  physical barriers.

What must be conceded:
- **P4 exception (0.80) is not supported.** Human raters judge exception-handling tasks
  far less agent-coverable than the paper assumes (0.52 [0.35, 0.74]). The honest move is
  to revise the weight, not defend it.
- The rank order the pilot advertised does not survive human annotation.
- n=40 per category still leaves wide intervals; P1's CI includes 1.0, meaning we cannot
  rule out interpersonal barriers having no effect at all.

**Recommendation.** Lead the reply with the method (weights are now measured, blind,
against human annotation), report the P4 correction as a finding rather than burying it,
and note that exception-handling being *harder* for agents than assumed is a substantively
interesting result that strengthens rather than weakens the framework's premise. Resolve
the Maulik scale question before any number here goes into a manuscript.

---

## Open items

2. **Decide the P4 revision** — 0.52 point estimate, or re-run with more tasks in that stratum.
3. Consider enlarging n per category; current CIs cannot discriminate P1 from no effect.
4. `figures/penalty_validation.*` still shows pilot-only results and needs regenerating
   with the human estimates alongside.
