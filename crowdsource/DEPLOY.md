# Deploy the agentic-coverage annotation form (Google, free, no database)

This turns the coverage-rating instrument into a shareable web form. People open
a Google link, rate tasks, and every answer lands in a **Google Sheet** you own.
No server, no database, no cost. It's a **Google Apps Script Web App** bound to a
Sheet. It mirrors the task->ability annotation tool, but asks a single neutral
question per task: *how much can an autonomous AI agent complete on its own?*

**Files in this folder:**
- `Code.gs` — the backend (serves the forms, writes answers to the Sheet, JSON export)
- `Index.html` — one-task-at-a-time form, tasks embedded (generated)
- `IndexGrouped.html` — fast grouped-by-occupation form, batch-saved (generated)
- `generate_index.py` — regenerates the forms (pilot set, a custom set, or all 18,796)

**Two interfaces, one Sheet.** Both forms are blind (raters never see the penalty
categories) and both write to the same `Responses` tab:
- Default `/exec` serves `Index.html` — one task per screen, careful pace.
- `/exec?view=grouped` serves `IndexGrouped.html` — every task for an occupation on
  one page with a compact slider each, saved a group at a time. Faster for bulk runs.

---

## One-time setup (~5 minutes)

### 1. Create the Sheet + script
1. Go to <https://sheets.google.com> → **Blank spreadsheet**.
2. Rename it e.g. `ATES Coverage Annotations`.
3. **Extensions → Apps Script**. A script editor opens.

### 2. Paste the code
1. Delete the sample `function myFunction() {}` in `Code.gs` and paste the entire
   contents of **`Code.gs`** from this folder.
2. Click **＋** next to "Files" → **HTML** → name it exactly `Index`. Delete its
   default contents and paste the entire contents of **`Index.html`**.
3. Repeat: **＋** → **HTML** → name it exactly `IndexGrouped` → paste **`IndexGrouped.html`**.
   (Skip this file only if you don't want the grouped view.)
4. **Save** (Ctrl/Cmd-S).

### 3. Deploy as a Web App
1. **Deploy → New deployment**.
2. Gear ⚙ → **Web app**.
3. Set: **Execute as: Me**; **Who has access: Anyone**.
4. **Deploy** → **Authorize access** → your account → *Advanced → Go to project → Allow*.
5. Copy the **Web app URL** (ends in `/exec`). That's your shareable link.

Open it once to test. Submissions appear on a new **`Responses`** tab.

---

## Divide and conquer

Hand different people different task ranges with `?start=` and `?end=`:

| Person | Link |
|--------|------|
| You | `…/exec?start=1&end=25` |
| Colleague A | `…/exec?start=26&end=50` |
| Colleague B | `…/exec?start=51&end=75` |
| Colleague C | `…/exec?start=76&end=100` |

No params = the whole set. Add `&view=grouped` to any link to hand out the fast
grouped form instead (e.g. `…/exec?start=26&end=50&view=grouped`). Overlaps are
welcome: two people rating the same task is exactly what lets us measure
inter-rater agreement (Cohen's κ / ICC), just as we did for the task→ability dataset.

---

## Regenerating the task list

```bash
# pilot set (100 tasks, default) -> Index.html only
python3 generate_index.py

# also emit the grouped form
python3 generate_index.py --grouped

# every penalty-relevant task + controls, or the full corpus
python3 generate_index.py --full --grouped              # all 18,796 tasks, both forms
python3 generate_index.py --tasks mine.csv --grouped    # any CSV: task_id,occupation,task_text
python3 generate_index.py --only grouped --tasks x.csv  # only the grouped form
```

After editing a form, redeploy: **Deploy → Manage deployments → ✏️ Edit →
Version: New version → Deploy**. The `/exec` URL stays the same.

---

## Getting the data back out

The `Responses` tab **is** your dataset — one row per (annotator, task):

```
timestamp · annotator · annotator_email · session_id ·
task_id · occupation · task_text · coverage · confidence · comment
```

`coverage` is 0.00–1.00. **File → Download → CSV**, drop it into
`results/` as `human_ratings.csv`, and re-run
`python3 code/estimate_weights.py` (point it at the human file) to get the
human-validated weights + CIs and the agreement statistic.

**Or pull it without the Sheet UI:** open `…/exec?export=json` for a read-only
JSON dump of every response (`{ ok, count, headers, rows }`) — handy for scripting
`curl …/exec?export=json` straight into the analysis.

---

## Quotas
Apps Script free tier: ~20,000 form loads/day — far more than a
friends-and-colleagues drive needs. Resets daily if you ever hit it.
