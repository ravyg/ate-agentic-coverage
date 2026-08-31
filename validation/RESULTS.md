# Human Validation of the Agentic Coverage Dataset

## Result (headline)

The agentic-coverage labels were produced by a large language model (**Claude Sonnet**)
against the labeling spec in [`scripts/LABELING_SPEC_COVERAGE.md`](../scripts/LABELING_SPEC_COVERAGE.md).
To validate them, **three independent annotators** each scored **all 200 tasks** of the
audit sample on the same neutral 0–1 instrument. Against the pooled human panel, the
model labels reach **Spearman ρ = 0.884**. The result is stable: ρ stays between 0.87
and 0.88 across every subset of annotators, so no single rater drives it.

| Metric | Value |
|--------|-------|
| Independent annotators | 3 |
| Tasks scored (each annotator) | 200 |
| Human ratings collected (total) | 600 |
| **Spearman ρ (model vs. human panel)** | **0.884** |
| Pearson r (model vs. human panel) | 0.849 |
| Inter-annotator reliability, ICC(2,k) | 0.782 |
| Reliability ceiling, √ICC (see caveat below) | 0.885 |
| Mean absolute error | 0.171 |
| Within ±0.20 of the human mean | 67.0% |
| Mean signed bias (model − human) | **−0.147** |

## What the number means (and its scope)

- **ρ = 0.884 is a *ranking* claim.** The model reliably orders tasks from
  least- to most- agent-coverable. This is what downstream exposure modeling depends on,
  and it is the sense in which the labels are validated.
- **Do not read the ceiling as a score to be beaten.** Three humans scoring the same task
  differ by 0.189 on average, which in principle caps how well any predictor can match
  their mean at √0.782 ≈ 0.885. We previously framed the model as reaching "99.9% of
  attainable". **That framing is withdrawn**: the ceiling is not stable enough to support
  it. Computed on the two annotators who agree most closely (ICC 0.918), the ceiling rises
  to 0.958 and the model reaches 91% of it; two other two-rater subsets give values above
  100%, which is not meaningful. The defensible claim is the raw ρ ≈ 0.88, which barely
  moves across subsets.
- **Known calibration gap (absolute level):** the model scores tasks **0.147 lower** than
  the human panel on average (model mean 0.353, human mean 0.498). Ranking is excellent;
  absolute values are systematically conservative. **Users needing calibrated absolute
  coverage should apply a linear correction fitted on the audit sample; users needing
  relative ordering can use the labels as released.** This is the direct analogue of the
  coverage-gap caveat documented for the task→ability dataset.
- **No single annotator drives the result.** Leave-one-out gives r = 0.777–0.842 (headline
  0.849), and ρ stays in 0.87–0.88 for every subset.
- **Known instrument limitation.** The 0–1 scale was read as a proportion by two annotators
  and closer to a yes/no by the third: on tasks the other two scored 0–20%, that annotator
  answered exactly 0 in 91% of cases, and scored 55% of physical tasks at 0. The direction
  of their judgments agrees with the others (r = +0.49; inverting it gives −0.49, so this is
  not a reversed scale), but the magnitudes are near-binary. All three are retained — the
  panel is reported as collected — and a future round should make the instrument state
  explicitly that a fraction, not a yes/no verdict, is being asked for.

## Method (brief)

- **Instrument:** a blind web form ([`INSTRUMENT.md`](../INSTRUMENT.md)). Annotators saw only
  the occupation and task text, and answered one question — how much of the task an
  autonomous agent could complete alone, on a 0–1 scale. **Annotators were never shown the
  model's label, the penalty categories, or any other annotator's entries.**
- **Sample:** 200 tasks drawn with seed 42 from the 18,796-task corpus, stratified as 40
  per barrier category (interpersonal, regulatory, physical, exception) plus 40 no-barrier
  controls, spanning 180 distinct occupations.
- **Independence:** each annotator worked alone through their own form; individual
  responses were compiled only afterward from the shared response sheet.
- **Reproducibility:** [`compute_validation.py`](compute_validation.py) regenerates every
  number in this file:

  ```bash
  python3 validation/compute_validation.py
  ```

- **Deduplication:** the form supports resume, so where a task was submitted more than once
  by the same annotator the latest response is used. A small number of form-development
  test rows were excluded; including them moves every metric by ≤0.001.

## Data availability

Consistent with the task→ability dataset, **the human annotations are not released.** The
raw export carries annotator names and emails, and the de-identified per-task panel file is
withheld as well. What is released is the **dataset itself** (`data/agentic_coverage.csv`),
the **metrics above**, and the **code that computes them**. Maintainers can regenerate the
de-identified input from the raw export with:

```bash
python3 validation/compute_validation.py --build <raw_export.json>
```

## Scope note

The headline figures are the pooled result of the three annotators (**Maulik Dang**
([@floppymilo](https://github.com/floppymilo)), **Saket Kumar** ([@saki007ster](https://github.com/saki007ster)), **Shreeya Sharma**), who each independently scored the full 200-task set. A
prior 100-task pilot using a four-rater LLM panel is reported separately in
[`../results/RESULTS.md`](../results/RESULTS.md); that pilot's inter-rater spread (SD ≈ 0.035)
is far tighter than the human panel's (0.189), which is a caution about treating LLM-panel
agreement as evidence of reliability rather than of shared bias.

## Acknowledgments

We thank **Saket Kumar** ([@saki007ster](https://github.com/saki007ster)), **Maulik Dang** ([@floppymilo](https://github.com/floppymilo)), and **Shreeya Sharma** for
their independent expert annotation of the validation sample.
