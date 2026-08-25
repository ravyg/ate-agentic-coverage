# Agentic-Coverage Labeling Spec

This is the ground truth for **how** to label. Every chunk is labeled the same way,
so new rows are consistent. The task is deliberately **neutral**: you rate one number
per task and never see or infer any penalty categories.

## The single question

For each work task, decide:

> Consider a capable autonomous software AI agent in 2026. It can browse, write, call
> APIs and tools, reason, and generate text, images, audio, and code. It has **no
> physical body** and **no legal or professional authority of its own**.
>
> What fraction of this task could the agent carry out **end to end, on its own, with
> no human stepping in** to act, be physically present, decide, or take responsibility?

Output a single number **coverage** in **[0.00, 1.00]**, rounded to 2 decimals.

- **1.00** = the agent can fully complete the task by itself.
- **~0.50** = about half; the rest needs a human to act, be present, decide, or be accountable.
- **0.00** = the agent cannot meaningfully complete any of it alone.

Judge only autonomous, unaided completion. Do **not** credit "the agent could help a
human do it." If a human must be in the loop to act, be present, or be accountable,
that portion is **not** covered.

## Calibration anchors (not from the corpus)

| Task | coverage | why |
|------|:---:|------|
| Draft a routine status email from notes | 0.95 | fully doable unaided |
| Summarize a policy document and flag risks | 0.90 | text in, text out |
| Reconcile invoices in accounting software | 0.85 | automatable, minor human confirm |
| Schedule a meeting across calendars | 0.80 | mostly automatable |
| Analyze survey data and write up findings | 0.85 | analysis + writing |
| Interview a client to gather requirements | 0.45 | agent can draft/ask but a human relationship carries it |
| Negotiate contract terms with a vendor | 0.35 | needs human trust/authority to close |
| Counsel a grieving family member | 0.10 | needs human presence and trust |
| Diagnose and prescribe medication | 0.10 | needs licensed human authority |
| Physically install equipment on site | 0.00 | requires a body on site |
| Sign and certify a legal filing under oath | 0.05 | requires human legal authority |

## Rules

1. Rate the task as written. If it bundles several sub-actions, weigh them by how much
   of the whole an agent could finish alone.
2. Physical / on-site / manual work scores low (no body). Work needing legal authority,
   licensure, sworn responsibility, or fiduciary duty scores low (no authority). Work
   needing live human rapport, negotiation, or emotional trust scores in the middle.
   Pure information work (read, analyze, write, compute, code) scores high.
3. Be decisive and consistent. Use the anchors. Two labelers should land within ~0.15.
4. Do **not** invent categories, tags, or extra columns. One number per task.

## Output schema (one row per task)

Write a CSV with header exactly:

```
task_id,occupation,task_text,coverage,rationale
```

- `coverage` — float in [0.00, 1.00], 2 decimals.
- `rationale` — one short clause (e.g. "needs on-site presence", "pure text analysis").
- Preserve `task_id`, `occupation`, `task_text` exactly from the input chunk.
- CSV-quote any field containing a comma. One row per input task — no duplicates, none skipped.
