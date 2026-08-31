# O*NET Agentic Coverage Dataset

A task-level estimate, for **all 18,796 O\*NET work tasks** — the full O\*NET task
corpus, economy-wide — of **how much of each task a current autonomous AI agent
could complete end to end, with no human in the loop.**

This dataset supports task-level research on AI exposure and human-AI task
allocation: which tasks an agent can already finish alone, which need a human for
part of the work, and which still require a human throughout.

> Built as a companion resource to the **ATES** (Agentic Task Exposure Score)
> framework and the [O\*NET Task→Ability Mapping Dataset](https://doi.org/10.5281/zenodo.21989176)
> — coverage is the axis those datasets don't measure on their own: not *can* an
> agent do this kind of work, but *how much of this specific task* can it finish
> unaided.

**Get it:** [🤗 Hugging Face](https://huggingface.co/datasets/ravishgupta/ate-agentic-coverage) · [GitHub source](https://github.com/ravyg/ate-agentic-coverage) · [Zenodo (archival DOI)](https://doi.org/10.5281/zenodo.22202518)

Load it programmatically from Hugging Face:

```python
from datasets import load_dataset

ds = load_dataset("ravishgupta/ate-agentic-coverage")
```

> ⭐ **Find this useful?** Please **clone it and give the repo a star** — it takes one
> click, helps others discover the dataset, and lets us gauge interest to keep it
> maintained and expanded. If you use it in your work, a [citation](#citation) is the
> best thanks of all. 🙏

> ### ✅ Status: labels released · human validation **complete**
> The full agentic-coverage dataset (**18,796 tasks — economy-wide, the entire O\*NET
> task corpus**) is **available today**. Labels were produced by a large language
> model (**Claude Sonnet**) against a single neutral instrument
> ([`scripts/LABELING_SPEC_COVERAGE.md`](scripts/LABELING_SPEC_COVERAGE.md)), applied
> in one consistent pass across all 145 chunks. **Independent human validation is
> complete:** three annotators each scored all 200 tasks of the audit sample.
> Against the pooled human panel, the model reaches **Spearman ρ = 0.884**, and stays
> between 0.87 and 0.88 for every subset of annotators — no single rater drives it.
> Ranking is reliable. **Absolute levels
> are conservative:** the model scores tasks **0.147 lower** than the human panel on
> average (model mean 0.353 vs. human mean 0.498) — a known calibration gap, not a
> ranking problem. Full breakdown, method, and scope in [`validation/`](validation/).

---

## What's here

| File | Description |
|------|-------------|
| `data/agentic_coverage.csv` | **Main dataset** — 18,796 rows, one per O\*NET task |
| `scripts/LABELING_SPEC_COVERAGE.md` | The neutral labeling spec used for every task |
| `scripts/` | The resumable, one-command full-corpus generation pipeline (chunk → label → merge) |
| `validation/` | Human validation results (Spearman ρ, ICC, bias) + the reproduction script |
| `crowdsource/` | The web form used to collect human validation labels |
| `docs/METHODOLOGY.md` | How the dataset was built and validated |
| `docs/SCHEMA.md` | Column-by-column schema |
| `code/`, `results/` | The earlier 100-task pilot that motivated this full-corpus release |

---

## Main dataset schema

`data/agentic_coverage.csv` — one row per O\*NET task:

| Column | Type | Description |
|--------|------|-------------|
| `task_id` | int | O\*NET task identifier |
| `occupation` | string | O\*NET occupation title the task belongs to |
| `task_text` | string | Full O\*NET task statement |
| `coverage` | float [0, 1] | How much of the task an autonomous AI agent could complete end to end, unaided |
| `rationale` | string | Short free-text justification for the score |

Full column notes: [`docs/SCHEMA.md`](docs/SCHEMA.md).

## Coverage distribution

18,796 tasks · mean **0.353** · sd 0.329 · median 0.30.

| Coverage band | Tasks | Share |
|---|---:|---:|
| [0.0, 0.2) | 8,206 | 43.7% |
| [0.2, 0.4) | 2,786 | 14.8% |
| [0.4, 0.6) | 2,221 | 11.8% |
| [0.6, 0.8) | 2,052 | 10.9% |
| [0.8, 1.0] | 3,531 | 18.8% |

Most tasks cluster at the low end — a majority still need meaningful human
involvement — with a smaller, distinct cluster of tasks an agent can already
handle almost entirely alone.

---

## How it was built (short version)

1. **LLM pass** — every one of the 18,796 O\*NET tasks was scored 0–1 for agentic
   coverage by a large language model (**Claude Sonnet**) against a single neutral
   instrument ([`scripts/LABELING_SPEC_COVERAGE.md`](scripts/LABELING_SPEC_COVERAGE.md))
   that never mentions the ATES penalty scheme, so labels aren't circular with the
   model they were built to inform. Tasks were split into 145 blind chunks of 130
   tasks each and labeled in one consistent pass, then merged and validated
   (`scripts/merge_validate.py`).
2. **Human validation** *(complete)* — a 200-task stratified sample (seed 42, 40 per
   penalty category plus 40 no-penalty controls, spanning 180 occupations) was
   independently scored by **three annotators**, each rating all 200 tasks on the
   same blind instrument.
3. **Agreement** — model-vs-human Spearman ρ = 0.884 (stable at 0.87–0.88 across
   annotator subsets); inter-annotator ICC(2,k) = 0.782. Mean absolute error 0.171;
   the model runs 0.147 low on average (known, documented calibration gap). A known
   instrument limitation — one annotator read the 0–1 scale as closer to a yes/no —
   is documented in full in [`validation/RESULTS.md`](validation/RESULTS.md).

Full protocol: [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md).

---

## Source & license

- **Source taxonomy:** [O\*NET 30.2](https://www.onetcenter.org/database.html)
  (U.S. Department of Labor, public domain).
- **This dataset:** licensed **CC-BY-4.0** — free to use with attribution.

## Citation

If you use this dataset, please cite the accompanying paper. Copy-paste in your
preferred style:

**APA**
```
Gupta, R., & Kumar, S. (2026). Agentic AI and Occupational Displacement: A Multi-Regional Task Exposure Analysis of Emerging Labor Market Disruption. arXiv preprint arXiv:2604.00186.
```

**MLA**
```
Gupta, Ravish, and Saket Kumar. "Agentic AI and Occupational Displacement: A Multi-Regional Task Exposure Analysis of Emerging Labor Market Disruption." arXiv preprint arXiv:2604.00186 (2026).
```

**Chicago**
```
Gupta, Ravish, and Saket Kumar. "Agentic AI and Occupational Displacement: A Multi-Regional Task Exposure Analysis of Emerging Labor Market Disruption." arXiv preprint arXiv:2604.00186 (2026).
```

**Harvard**
```
Gupta, R. and Kumar, S., 2026. Agentic AI and Occupational Displacement: A Multi-Regional Task Exposure Analysis of Emerging Labor Market Disruption. arXiv preprint arXiv:2604.00186.
```

**Vancouver**
```
Gupta R, Kumar S. Agentic AI and Occupational Displacement: A Multi-Regional Task Exposure Analysis of Emerging Labor Market Disruption. arXiv preprint arXiv:2604.00186. 2026 Mar 31.
```

**BibTeX**
```bibtex
@article{gupta2026agentic,
  title   = {Agentic AI and Occupational Displacement: A Multi-Regional Task Exposure Analysis of Emerging Labor Market Disruption},
  author  = {Gupta, Ravish and Kumar, Saket},
  journal = {arXiv preprint arXiv:2604.00186},
  year    = {2026}
}
```

### Citing the dataset

The dataset is archived on Zenodo with a DOI (concept DOI, always resolves to the
latest version):

**DOI:** [10.5281/zenodo.22202518](https://doi.org/10.5281/zenodo.22202518)

```bibtex
@misc{gupta2026agenticcoverage,
  author    = {Gupta, Ravish and Kumar, Saket and Dang, Maulik},
  title     = {{O*NET} Agentic Coverage Dataset},
  year      = {2026},
  publisher = {Zenodo},
  version   = {1.0.0},
  doi       = {10.5281/zenodo.22202518},
  url       = {https://doi.org/10.5281/zenodo.22202518}
}
```

See also `CITATION.cff`.

## Acknowledgements

**Special thanks to our annotators — Saket Kumar ([@saki007ster](https://github.com/saki007ster)), Maulik Dang ([@floppymilo](https://github.com/floppymilo)), and
Shreeya Sharma —**
whose independent human review of the 200-task validation sample made the quality
assessment of this dataset possible. Their careful judgments on agentic coverage
are the backbone of its reliability.

### 🙋 Want your name here? Become an annotator

This dataset gets better with more human eyes — and we credit every contributor.
If you'd like to help validate agentic-coverage labels (it takes ~15 minutes, no
special background needed) **your name will be listed in the Acknowledgements of
this dataset and its accompanying paper.**

It's a simple, citable way to contribute to open research on AI and the future of
work — something concrete to point to on your CV, LinkedIn, or Google Scholar.

👉 **Interested? Reach out:** [ravishgupta.me/#contact](https://ravishgupta.me/index.html#contact)

Tell us roughly how many tasks you'd like to annotate and we'll send you a link.
Every verified contributor is acknowledged by name (or kept anonymous on request).

## Related

- **Hugging Face:** [ravishgupta/ate-agentic-coverage](https://huggingface.co/datasets/ravishgupta/ate-agentic-coverage) — load with `datasets.load_dataset(...)`.
- **Zenodo:** [10.5281/zenodo.22202518](https://doi.org/10.5281/zenodo.22202518) — archival record + citation DOI.
- **Paper:** Gupta & Kumar (2026), *Agentic AI and Occupational Displacement*, arXiv:2604.00186.
- **O\*NET Task→Ability Mapping Dataset:** [ate-task-ability-dataset](https://github.com/ravyg/ate-task-ability-dataset) — the companion dataset this one builds on.
- **ATES framework** — the model this dataset was built for *(link on paper release)*.

---

⭐ **If this dataset helped your work, please [star the repo](https://github.com/ravyg/ate-agentic-coverage) and cite the paper.** It's the simplest way to support open research and keep this dataset growing. Thank you!
