# Validation

Human validation of the agentic-coverage dataset.

## Headline result

Three independent annotators each scored **all 200 tasks** of the audit sample on
the same neutral 0–1 instrument. Against the pooled human panel, the model labels
reach **Spearman ρ = 0.884** — **99.9% of the attainable rank agreement**, set by a
reliability ceiling of **0.885** (how well the three annotators agree with each
other). Ranking is excellent; **absolute levels run 0.147 low on average** (model
mean 0.353 vs. human mean 0.498) — a known, documented calibration gap, not a
ranking problem. See **[`RESULTS.md`](RESULTS.md)** for the full breakdown, method,
and scope.

| Metric | Value |
|--------|-------|
| Independent annotators | 3 |
| Tasks scored (each annotator) | 200 |
| Spearman ρ (model vs. human panel) | **0.884** |
| Reliability ceiling, √ICC | 0.885 |
| Share of attainable agreement reached | **99.9%** |
| Mean signed bias (model − human) | **−0.147** |

## Reproducibility & raw data

The raw human annotations and the reproduction script live with the experiment
code. **Raw exports contain annotator names/emails (PII) and are withheld;** the
de-identified per-task panel file used to compute the numbers above is also not
released. What's released is the **dataset itself**
(`data/agentic_coverage.csv`), the **metrics in `RESULTS.md`**, and the **code
that computes them**:

```bash
python3 validation/compute_validation.py
```

A prior 100-task pilot using a four-rater LLM panel (not human validation) is
reported separately in [`../results/RESULTS.md`](../results/RESULTS.md).
