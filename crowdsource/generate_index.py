#!/usr/bin/env python3
"""
Generate Index.html for the agentic-coverage annotation web app.

Embeds a blinded task list (task_id, occupation, task_text ONLY -- no penalty
columns, so annotators cannot reverse-engineer the weights) into a self-contained
HTML form. Paste the output into the Apps Script editor as an `Index` HTML file.

Usage:
  python3 generate_index.py                    # uses ../data/rater_input.csv (100-task pilot)
  python3 generate_index.py --tasks FILE.csv   # any CSV with task_id,occupation,task_text
  python3 generate_index.py --full             # uses ../data/tasks_tagged.csv (all 18,796)
"""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = ROOT / "data" / "rater_input.csv"
FULL = ROOT / "data" / "tasks_tagged.csv"
OUT = Path(__file__).resolve().parent / "Index.html"

TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<base target="_top">
<meta charset="utf-8">
<style>
  body { font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
         max-width: 760px; margin: 0 auto; padding: 20px; color: #1a1a1a; }
  h1 { font-size: 20px; } h2 { font-size: 16px; color: #444; }
  .card { border: 1px solid #ddd; border-radius: 10px; padding: 18px; margin: 14px 0;
          box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
  .task { font-size: 17px; line-height: 1.5; margin: 6px 0 14px; }
  .occ { color: #666; font-size: 13px; text-transform: uppercase; letter-spacing: .04em; }
  .q { font-weight: 600; margin: 16px 0 6px; }
  .scale { display:flex; justify-content:space-between; font-size:12px; color:#777; }
  input[type=range] { width: 100%; }
  .val { font-size: 28px; font-weight: 700; text-align:center; color:#0b5; margin: 4px 0; }
  .conf label { margin-right: 12px; font-size: 14px; }
  textarea { width: 100%; min-height: 44px; margin-top: 6px; }
  .nav { display:flex; justify-content:space-between; margin-top: 18px; }
  button { padding: 10px 18px; border-radius: 8px; border: 1px solid #0b5; background:#0b5;
           color:#fff; font-size:15px; cursor:pointer; }
  button.secondary { background:#fff; color:#0b5; }
  .banner { background:#eef7f0; border:1px solid #cde8d5; border-radius:8px; padding:10px 14px;
            font-size:14px; margin-bottom:14px; }
  .prog { font-size:13px; color:#666; }
  .ident input { padding:6px; font-size:14px; margin-right:8px; }
</style>
</head>
<body>
  <h1>Can an AI agent do this task on its own?</h1>
  <div class="banner">
    For each work task, tell us <b>how much of it a capable autonomous AI agent (2026)
    could complete end to end, on its own, with no human stepping in</b> to act, be
    physically present, decide, or take responsibility. The agent can browse, write,
    reason, and use tools, but has <b>no physical body</b> and no legal authority of
    its own. Judge only what it can finish <b>unaided</b>. About 15 minutes.
  </div>

  <div class="card ident">
    <div class="q">Your name and email (so we can credit you)</div>
    <input id="annotator" placeholder="Name">
    <input id="email" placeholder="Email (optional)">
  </div>

  <div class="prog" id="prog"></div>
  <div id="stage"></div>

  <script>
    var TASKS = __TASKS_JSON__;
    var startParam = "<?= startParam ?>", endParam = "<?= endParam ?>";
    var s = parseInt(startParam, 10), e = parseInt(endParam, 10);
    if (!isNaN(s) || !isNaN(e)) {
      var a = isNaN(s) ? 1 : s, b = isNaN(e) ? TASKS.length : e;
      TASKS = TASKS.slice(a - 1, b);
    }
    var sessionId = 'sess-' + Math.random().toString(36).slice(2) + '-' + (new Date()).getTime();
    var i = 0, answers = {};

    function anchor(v) {
      if (v >= 90) return "agent can do essentially all of it alone";
      if (v >= 65) return "agent does most; a human finishes a little";
      if (v >= 35) return "roughly half needs a human to act / be present / decide";
      if (v >= 10) return "agent helps but a human must do most of it";
      return "agent cannot meaningfully do it alone";
    }

    function render() {
      var t = TASKS[i];
      var prev = answers[t.task_id] || { coverage: 50, confidence: 3, comment: "" };
      document.getElementById('prog').textContent =
        'Task ' + (i + 1) + ' of ' + TASKS.length +
        '  ( you have saved ' + Object.keys(answers).length + ' )';
      document.getElementById('stage').innerHTML =
        '<div class="card">' +
          '<div class="occ">' + esc(t.occupation) + '</div>' +
          '<div class="task">' + esc(t.task_text) + '</div>' +
          '<div class="q">How much could an autonomous AI agent complete on its own?</div>' +
          '<div class="val"><span id="cv">' + prev.coverage + '</span>%</div>' +
          '<input type="range" min="0" max="100" step="5" id="cov" value="' + prev.coverage + '">' +
          '<div class="scale"><span>0% none</span><span id="anch">' + anchor(prev.coverage) + '</span><span>100% all</span></div>' +
          '<div class="q">How confident are you?</div>' +
          '<div class="conf" id="conf">' + confRadios(prev.confidence) + '</div>' +
          '<div class="q">Comment (optional)</div>' +
          '<textarea id="comment" placeholder="e.g. needs a human signature / on-site presence">' + esc(prev.comment) + '</textarea>' +
          '<div class="nav">' +
            '<button class="secondary" onclick="back()"' + (i === 0 ? ' disabled' : '') + '>Back</button>' +
            '<button onclick="saveNext()">' + (i === TASKS.length - 1 ? 'Save &amp; finish' : 'Save &amp; next') + '</button>' +
          '</div>' +
        '</div>';
      var cov = document.getElementById('cov');
      cov.oninput = function () {
        document.getElementById('cv').textContent = cov.value;
        document.getElementById('anch').textContent = anchor(parseInt(cov.value, 10));
      };
    }

    function confRadios(sel) {
      var out = '';
      for (var c = 1; c <= 5; c++) {
        out += '<label><input type="radio" name="confidence" value="' + c + '"' +
               (c === sel ? ' checked' : '') + '>' + c + '</label>';
      }
      return out + ' <span style="font-size:12px;color:#999">(1 low - 5 high)</span>';
    }

    function esc(x) { var d = document.createElement('div'); d.textContent = x == null ? '' : x; return d.innerHTML; }

    function collect() {
      var t = TASKS[i];
      var conf = document.querySelector('input[name=confidence]:checked');
      answers[t.task_id] = {
        coverage: parseInt(document.getElementById('cov').value, 10),
        confidence: conf ? parseInt(conf.value, 10) : 3,
        comment: document.getElementById('comment').value || ""
      };
      return t;
    }

    function saveNext() {
      var t = collect();
      var a = answers[t.task_id];
      var name = document.getElementById('annotator').value || 'anonymous';
      var email = document.getElementById('email').value || '';
      google.script.run
        .withSuccessHandler(function () {})
        .withFailureHandler(function (err) { alert('Save failed: ' + err); })
        .submitAnnotation({
          annotator: name, email: email, sessionId: sessionId,
          rows: [[t.task_id, t.occupation, t.task_text,
                  (a.coverage / 100).toFixed(2), a.confidence, a.comment]]
        });
      if (i < TASKS.length - 1) { i++; render(); }
      else {
        document.getElementById('stage').innerHTML =
          '<div class="card"><h2>Thank you!</h2><p>You saved ' +
          Object.keys(answers).length + ' ratings. You can close this tab, or go ' +
          '<button class="secondary" onclick="i=0;render()">back to the start</button> to review.</p></div>';
        document.getElementById('prog').textContent = '';
      }
    }

    function back() { collect(); if (i > 0) { i--; render(); } }

    render();
  </script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", type=Path, default=None)
    ap.add_argument("--full", action="store_true")
    args = ap.parse_args()

    src = args.tasks or (FULL if args.full else DEFAULT)
    rows = list(csv.DictReader(open(src, newline="")))
    tasks = [{"task_id": r["task_id"],
              "occupation": r.get("occupation", ""),
              "task_text": r["task_text"]} for r in rows]

    html = TEMPLATE.replace("__TASKS_JSON__", json.dumps(tasks, ensure_ascii=False))
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT} with {len(tasks)} tasks (source: {src.name}).")
    print("Paste this into the Apps Script editor as an HTML file named 'Index'.")


if __name__ == "__main__":
    main()
