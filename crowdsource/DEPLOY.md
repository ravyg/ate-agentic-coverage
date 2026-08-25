# Deploy the agentic-coverage annotation form (Google, free, no database)

This turns the coverage-rating instrument into a shareable web form. People open
a Google link, rate tasks, and every answer lands in a **Google Sheet** you own.
No server, no database, no cost. It's a **Google Apps Script Web App** bound to a
Sheet. It mirrors the task->ability annotation tool, but asks a single neutral
question per task: *how much can an autonomous AI agent complete on its own?*

**Files in this folder:**
- `Code.gs` — the backend (serves the form, writes answers to the Sheet)
- `Index.html` — the form UI, with the pilot tasks embedded (generated)
- `generate_index.py` — regenerates `Index.html` (pilot set, a custom set, or all 18,796)

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
3. **Save** (Ctrl/Cmd-S).

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

No params = the whole set. Overlaps are welcome: two people rating the same task
is exactly what lets us measure inter-rater agreement (Cohen's κ / ICC), just as
we did for the task→ability dataset.

---

## Regenerating the task list

```bash
# pilot set (100 tasks, default)
python3 generate_index.py

# every penalty-relevant task + controls, or the full corpus
python3 generate_index.py --full            # all 18,796 tasks
python3 generate_index.py --tasks mine.csv  # any CSV: task_id,occupation,task_text
```

After editing `Index.html`, redeploy: **Deploy → Manage deployments → ✏️ Edit →
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

---

## Quotas
Apps Script free tier: ~20,000 form loads/day — far more than a
friends-and-colleagues drive needs. Resets daily if you ever hit it.
