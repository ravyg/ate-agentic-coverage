# Human Validation of the Agentic Coverage Dataset

## Result (headline)

The agentic-coverage labels were produced by a large language model (**Claude Sonnet**)
against the labeling spec in [`scripts/LABELING_SPEC_COVERAGE.md`](../scripts/LABELING_SPEC_COVERAGE.md).
To validate them, **three independent annotators** each scored **all 200 tasks** of the
audit sample on the same neutral 0–1 instrument. Against the pooled human panel, the
model labels reach **Spearman ρ = 0.884** — against a reliability ceiling of **0.885**
set by how much the three annotators agree with each other. The model therefore
recovers **99.9% of the attainable rank agreement**: it orders tasks by agentic
coverage about as well as it is possible to do, given human disagreement.

| Metric | Value |
|--------|-------|
| Independent annotators | 3 |
| Tasks scored (each annotator) | 200 |
| Human ratings collected (total) | 600 |
| **Spearman ρ (model vs. human panel)** | **0.884** |
| Pearson r (model vs. human panel) | 0.849 |
| Inter-annotator reliability, ICC(2,k) | 0.782 |
| Reliability ceiling, √ICC | 0.885 |
| **Share of attainable agreement reached** | **99.9%** |
| Mean absolute error | 0.171 |
| Within ±0.20 of the human mean | 67.0% |
| Mean signed bias (model − human) | **−0.147** |

## What the number means (and its scope)

- **ρ = 0.884 is a *ranking* claim.** The model reliably orders tasks from
  least- to most- agent-coverable. This is what downstream exposure modeling depends on,
  and it is the sense in which the labels are validated.
- **The ceiling matters more than the raw number.** Three humans scoring the same task
  differ by 0.189 on average, which caps how well *any* predictor can match their mean at
  √0.782 ≈ 0.885. The model sits at 0.884. Reporting ρ without the ceiling would understate
  the result; reporting the ceiling without the bias below would overstate it.
- **Known calibration gap (absolute level):** the model scores tasks **0.147 lower** than
  the human panel on average (model mean 0.353, human mean 0.498). Ranking is excellent;
  absolute values are systematically conservative. **Users needing calibrated absolute
  coverage should apply a linear correction fitted on the audit sample; users needing
  relative ordering can use the labels as released.** This is the direct analogue of the
  coverage-gap caveat documented for the task→ability dataset.
- **No single annotator drives the result.** Leave-one-out gives r = 0.777–0.842 (headline
  0.849). Pairwise annotator agreement is uneven (r = 0.403 to 0.877), and one annotator
  used the extremes of the scale considerably more than the other two (SD 0.411 vs. 0.281
  and 0.320). Their ratings are retained: the divergence is dispersion, not inversion, and
  excluding them changes the headline by 0.007.

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
