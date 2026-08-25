# Agentic Coverage Rating Instrument

Purpose: measure, for a single work task, how much of it a current autonomous
AI agent could complete **end to end on its own**, so that the ATES coverage
penalty weights can be estimated from data rather than asserted.

This instrument is deliberately neutral. It does **not** mention penalty
categories, barrier types, or the ATES model. Raters see only the task text and
answer one question. This prevents raters from reverse-engineering the weights
we are trying to estimate.

## The question

> Consider a capable autonomous software AI agent in 2026 (it can browse, write,
> call APIs and tools, reason, and generate text, images, audio, and code, but
> has **no physical body** and no legal or professional authority of its own).
>
> For the task below, what fraction of it could this agent carry out **end to
> end, on its own, with no human stepping in** to act, decide, be present, or
> take responsibility?
>
> Answer with a single number **coverage** in [0.00, 1.00]:
> - **1.00** = the agent can fully complete the task by itself.
> - **0.50** = the agent can do about half; the rest needs a human to act,
>   be physically present, decide, or take responsibility.
> - **0.00** = the agent cannot meaningfully complete any of it alone.
>
> Judge only autonomous, unaided completion. Do not credit "the agent could
> help a human do it." If a human must be in the loop to act, be present, or be
> accountable, that portion is **not** covered.

## Anchors (calibration examples, not from the sample)

| Task | coverage | why |
|------|----------|-----|
| Draft a routine status email from notes | 0.95 | fully doable unaided |
| Summarize a policy document and flag risks | 0.90 | text in, text out |
| Schedule a meeting across calendars | 0.80 | mostly automatable, may need a human confirm |
| Counsel a grieving family member | 0.10 | needs human trust and presence |
| Physically install equipment on site | 0.00 | requires a body on site |
| Sign and certify a legal filing under oath | 0.05 | requires human legal authority |

## Output

For each task_id, return: `task_id, coverage, one_line_reason`.
Return the whole set as CSV. Do not add commentary outside the CSV.
