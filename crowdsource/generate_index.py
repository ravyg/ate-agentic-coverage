#!/usr/bin/env python3
"""
Generate the agentic-coverage annotation web app forms.

Embeds a blinded task list (task_id, occupation, task_text ONLY -- no penalty
columns, so annotators cannot reverse-engineer the weights) into a self-contained
HTML form. Paste the output into the Apps Script editor as an HTML file.

Two interfaces (both blind, both write to the same Google Sheet via Code.gs):
  Index.html         one task at a time, slider + confidence + comment  (?exec)
  IndexGrouped.html  all tasks for an occupation on one page, batch-save (?view=grouped)

Usage:
  python3 generate_index.py                    # Index.html from the 100-task pilot
  python3 generate_index.py --tasks FILE.csv   # any CSV with task_id,occupation,task_text
  python3 generate_index.py --full             # all 18,796 tasks
  python3 generate_index.py --grouped          # also emit IndexGrouped.html
  python3 generate_index.py --only grouped     # emit ONLY IndexGrouped.html
"""
import argparse
import csv
import json
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = ROOT / "data" / "rater_input.csv"
FULL = ROOT / "data" / "tasks_tagged.csv"
OUT = Path(__file__).resolve().parent / "Index.html"
OUT_GROUPED = Path(__file__).resolve().parent / "IndexGrouped.html"

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
      else { showResults(); }
    }

    function back() { collect(); if (i > 0) { i--; render(); } }

    function taskById(id) {
      for (var k = 0; k < TASKS.length; k++) { if (String(TASKS[k].task_id) === String(id)) return TASKS[k]; }
      return { occupation: "", task_text: "" };
    }

    // Final screen: show the annotator a summary of THEIR OWN ratings.
    function showResults() {
      var ids = Object.keys(answers);
      var n = ids.length, sum = 0, buckets = [0, 0, 0, 0, 0];
      ids.forEach(function (id) { var c = answers[id].coverage; sum += c; buckets[Math.min(4, Math.floor(c / 20))]++; });
      var mean = n ? Math.round(sum / n) : 0;
      var labels = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'];
      var maxb = Math.max.apply(null, buckets) || 1;

      var html = '<div class="card"><h2>Thank you! Here are your ratings.</h2>' +
        '<p>You rated <b>' + n + '</b> task' + (n === 1 ? '' : 's') +
        '. Your average coverage was <b>' + mean + '%</b> ' +
        '(how much you judged an autonomous AI agent could do unaided).</p>' +
        '<div class="q">Distribution of your ratings</div>';
      for (var b = 0; b < 5; b++) {
        var w = Math.round(buckets[b] / maxb * 100);
        html += '<div style="display:flex;align-items:center;gap:8px;margin:3px 0;font-size:13px;">' +
          '<span style="width:64px;color:#777">' + labels[b] + '</span>' +
          '<span style="display:inline-block;height:14px;width:' + w + '%;background:#0b5;border-radius:3px;min-width:2px;"></span>' +
          '<span style="color:#555">' + buckets[b] + '</span></div>';
      }

      html += '<div class="q" style="margin-top:14px">Your answers</div>' +
        '<table style="width:100%;border-collapse:collapse;font-size:13px;">' +
        '<tr style="text-align:left;color:#777;border-bottom:1px solid #ddd;">' +
        '<th style="padding:4px 6px;">Task</th><th style="padding:4px 6px;">Coverage</th><th style="padding:4px 6px;">Conf.</th></tr>';
      ids.forEach(function (id) {
        var t = taskById(id), a = answers[id];
        html += '<tr style="border-bottom:1px solid #f0f0f0;">' +
          '<td style="padding:4px 6px;"><span class="occ" style="display:block">' + esc(t.occupation) + '</span>' + esc(t.task_text) + '</td>' +
          '<td style="padding:4px 6px;font-weight:700;color:#0b5;white-space:nowrap;">' + a.coverage + '%</td>' +
          '<td style="padding:4px 6px;">' + a.confidence + '</td></tr>';
      });
      html += '</table>' +
        '<div class="nav"><button class="secondary" onclick="i=0;render()">Review / edit answers</button>' +
        '<span class="prog" id="globalStat"></span></div></div>';

      document.getElementById('stage').innerHTML = html;
      document.getElementById('prog').textContent = '';
      google.script.run.withSuccessHandler(function (total) {
        document.getElementById('globalStat').textContent = total + ' ratings collected so far (all annotators)';
      }).getGlobalCount();
    }

    render();
  </script>
</body>
</html>
"""


GROUPED_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<base target="_top">
<meta charset="utf-8">
<style>
  body { font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
         max-width: 820px; margin: 0 auto; padding: 20px; color: #1a1a1a; }
  h1 { font-size: 20px; } h2 { font-size: 16px; color: #444; margin: 4px 0; }
  .banner { background:#eef7f0; border:1px solid #cde8d5; border-radius:8px; padding:10px 14px;
            font-size:14px; margin-bottom:14px; }
  .ident input { padding:6px; font-size:14px; margin-right:8px; }
  .group { border:1px solid #ddd; border-radius:10px; padding:16px; margin:16px 0;
           box-shadow:0 1px 3px rgba(0,0,0,0.05); }
  .occ { color:#0b5; font-size:13px; text-transform:uppercase; letter-spacing:.04em;
         font-weight:700; margin-bottom:10px; }
  .row { border-top:1px solid #eee; padding:12px 0; }
  .task { font-size:15px; line-height:1.45; margin-bottom:8px; }
  .ctl { display:flex; align-items:center; gap:12px; }
  .ctl input[type=range] { flex:1; }
  .val { font-size:18px; font-weight:700; color:#0b5; width:52px; text-align:right; }
  .anch { font-size:12px; color:#777; margin-top:4px; }
  .conf { font-size:13px; margin-top:6px; color:#555; }
  .conf label { margin-right:10px; }
  .q { font-weight:600; margin:6px 0; }
  textarea { width:100%; min-height:36px; margin-top:6px; font-size:13px; }
  .nav { display:flex; justify-content:space-between; align-items:center; margin-top:14px; }
  button { padding:10px 18px; border-radius:8px; border:1px solid #0b5; background:#0b5;
           color:#fff; font-size:15px; cursor:pointer; }
  button.secondary { background:#fff; color:#0b5; }
  .prog { font-size:13px; color:#666; }
  .saved { color:#0b5; font-size:13px; }
</style>
</head>
<body>
  <h1>Can an AI agent do these tasks on its own?</h1>
  <div class="banner">
    For each work task, set <b>how much of it a capable autonomous AI agent (2026)
    could complete end to end, on its own, with no human stepping in</b> to act, be
    physically present, decide, or take responsibility. The agent can browse, write,
    reason, and use tools, but has <b>no physical body</b> and no legal authority of
    its own. Judge only what it can finish <b>unaided</b>. Tasks are grouped by
    occupation so you can move fast; save each group when done.
  </div>

  <div class="group ident">
    <div class="q">Your name and email (so we can credit you)</div>
    <input id="annotator" placeholder="Name">
    <input id="email" placeholder="Email (optional)">
  </div>

  <div class="prog" id="prog"></div>
  <div id="stage"></div>
  <div class="nav">
    <button class="secondary" id="prevBtn" onclick="prevGroup()">Previous occupation</button>
    <span>
      <button class="secondary" id="finishBtn" onclick="finish()">Finish &amp; see results</button>
      <button id="nextBtn" onclick="nextGroup()">Next occupation</button>
    </span>
  </div>

  <script>
    var TASKS = __TASKS_JSON__;
    var startParam = "<?= startParam ?>", endParam = "<?= endParam ?>";
    var s = parseInt(startParam, 10), e = parseInt(endParam, 10);
    if (!isNaN(s) || !isNaN(e)) {
      var a = isNaN(s) ? 1 : s, b = isNaN(e) ? TASKS.length : e;
      TASKS = TASKS.slice(a - 1, b);
    }

    // Group tasks by occupation, preserving first-seen order.
    var GROUPS = [], byOcc = {};
    TASKS.forEach(function (t) {
      if (!byOcc[t.occupation]) { byOcc[t.occupation] = { occupation: t.occupation, tasks: [] }; GROUPS.push(byOcc[t.occupation]); }
      byOcc[t.occupation].tasks.push(t);
    });

    var sessionId = 'sess-' + Math.random().toString(36).slice(2) + '-' + (new Date()).getTime();
    var g = 0, answers = {}, savedTasks = {};

    function anchor(v) {
      if (v >= 90) return "does essentially all of it alone";
      if (v >= 65) return "does most; a human finishes a little";
      if (v >= 35) return "about half needs a human to act / be present / decide";
      if (v >= 10) return "helps but a human must do most of it";
      return "cannot meaningfully do it alone";
    }
    function esc(x) { var d = document.createElement('div'); d.textContent = x == null ? '' : x; return d.innerHTML; }

    function confRadios(id, sel) {
      var out = '';
      for (var c = 1; c <= 5; c++) {
        out += '<label><input type="radio" name="conf_' + id + '" value="' + c + '"' +
               (c === sel ? ' checked' : '') + '>' + c + '</label>';
      }
      return out + ' <span style="color:#999">(1 low - 5 high)</span>';
    }

    function render() {
      var grp = GROUPS[g];
      document.getElementById('prog').textContent =
        'Occupation ' + (g + 1) + ' of ' + GROUPS.length +
        '  ( ' + Object.keys(savedTasks).length + ' of ' + TASKS.length + ' tasks saved )';
      var html = '<div class="group"><div class="occ">' + esc(grp.occupation) + '</div>';
      grp.tasks.forEach(function (t) {
        var prev = answers[t.task_id] || { coverage: 50, confidence: 3, comment: "" };
        html +=
          '<div class="row">' +
            '<div class="task">' + esc(t.task_text) + (savedTasks[t.task_id] ? ' <span class="saved">saved</span>' : '') + '</div>' +
            '<div class="ctl">' +
              '<input type="range" min="0" max="100" step="5" id="cov_' + t.task_id + '" value="' + prev.coverage + '">' +
              '<span class="val"><span id="cv_' + t.task_id + '">' + prev.coverage + '</span>%</span>' +
            '</div>' +
            '<div class="anch" id="an_' + t.task_id + '">' + anchor(prev.coverage) + '</div>' +
            '<div class="conf">confidence: ' + confRadios(t.task_id, prev.confidence) + '</div>' +
            '<textarea id="cm_' + t.task_id + '" placeholder="comment (optional): e.g. needs a human signature / on-site presence">' + esc(prev.comment) + '</textarea>' +
          '</div>';
      });
      html += '<div class="nav"><span></span>' +
              '<button onclick="saveGroup()">Save this occupation (' + grp.tasks.length + ' tasks)</button></div>' +
              '</div>';
      document.getElementById('stage').innerHTML = html;

      grp.tasks.forEach(function (t) {
        var cov = document.getElementById('cov_' + t.task_id);
        cov.oninput = function () {
          document.getElementById('cv_' + t.task_id).textContent = cov.value;
          document.getElementById('an_' + t.task_id).textContent = anchor(parseInt(cov.value, 10));
        };
      });
      document.getElementById('prevBtn').style.display = '';
      document.getElementById('nextBtn').style.display = '';
      document.getElementById('finishBtn').style.display = '';
      document.getElementById('prevBtn').disabled = (g === 0);
      document.getElementById('nextBtn').disabled = (g === GROUPS.length - 1);
    }

    function collectGroup() {
      var grp = GROUPS[g], rows = [];
      grp.tasks.forEach(function (t) {
        var cov = parseInt(document.getElementById('cov_' + t.task_id).value, 10);
        var confEl = document.querySelector('input[name=conf_' + t.task_id + ']:checked');
        var conf = confEl ? parseInt(confEl.value, 10) : 3;
        var comment = document.getElementById('cm_' + t.task_id).value || "";
        answers[t.task_id] = { coverage: cov, confidence: conf, comment: comment };
        rows.push([t.task_id, t.occupation, t.task_text, (cov / 100).toFixed(2), conf, comment]);
      });
      return rows;
    }

    function saveGroup() {
      var rows = collectGroup();
      var name = document.getElementById('annotator').value || 'anonymous';
      var email = document.getElementById('email').value || '';
      google.script.run
        .withSuccessHandler(function () {
          rows.forEach(function (r) { savedTasks[r[0]] = true; });
          render();
        })
        .withFailureHandler(function (err) { alert('Save failed: ' + err); })
        .submitAnnotation({ annotator: name, email: email, sessionId: sessionId, rows: rows });
    }

    function nextGroup() { collectGroup(); if (g < GROUPS.length - 1) { g++; render(); } }
    function prevGroup() { collectGroup(); if (g > 0) { g--; render(); } }

    function taskById(id) {
      for (var k = 0; k < TASKS.length; k++) { if (String(TASKS[k].task_id) === String(id)) return TASKS[k]; }
      return { occupation: "", task_text: "" };
    }

    // Save whatever is on screen, then show the annotator a summary of THEIR ratings.
    function finish() {
      var rows = collectGroup();
      var name = document.getElementById('annotator').value || 'anonymous';
      var email = document.getElementById('email').value || '';
      google.script.run
        .withSuccessHandler(function () { rows.forEach(function (r) { savedTasks[r[0]] = true; }); showResults(); })
        .withFailureHandler(function (err) { alert('Save failed: ' + err); })
        .submitAnnotation({ annotator: name, email: email, sessionId: sessionId, rows: rows });
    }

    function showResults() {
      var ids = Object.keys(answers);
      var n = ids.length, sum = 0, buckets = [0, 0, 0, 0, 0];
      ids.forEach(function (id) { var c = answers[id].coverage; sum += c; buckets[Math.min(4, Math.floor(c / 20))]++; });
      var mean = n ? Math.round(sum / n) : 0;
      var labels = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'];
      var maxb = Math.max.apply(null, buckets) || 1;

      var html = '<div class="group"><h2>Thank you! Here are your ratings.</h2>' +
        '<p>You rated <b>' + n + '</b> task' + (n === 1 ? '' : 's') +
        '. Your average coverage was <b>' + mean + '%</b> ' +
        '(how much you judged an autonomous AI agent could do unaided).</p>' +
        '<div class="q">Distribution of your ratings</div>';
      for (var b = 0; b < 5; b++) {
        var w = Math.round(buckets[b] / maxb * 100);
        html += '<div style="display:flex;align-items:center;gap:8px;margin:3px 0;font-size:13px;">' +
          '<span style="width:64px;color:#777">' + labels[b] + '</span>' +
          '<span style="display:inline-block;height:14px;width:' + w + '%;background:#0b5;border-radius:3px;min-width:2px;"></span>' +
          '<span style="color:#555">' + buckets[b] + '</span></div>';
      }

      html += '<div class="q" style="margin-top:14px">Your answers</div>' +
        '<table style="width:100%;border-collapse:collapse;font-size:13px;">' +
        '<tr style="text-align:left;color:#777;border-bottom:1px solid #ddd;">' +
        '<th style="padding:4px 6px;">Task</th><th style="padding:4px 6px;">Coverage</th><th style="padding:4px 6px;">Conf.</th></tr>';
      ids.forEach(function (id) {
        var t = taskById(id), a = answers[id];
        html += '<tr style="border-bottom:1px solid #f0f0f0;">' +
          '<td style="padding:4px 6px;"><span class="occ" style="display:block">' + esc(t.occupation) + '</span>' + esc(t.task_text) + '</td>' +
          '<td style="padding:4px 6px;font-weight:700;color:#0b5;white-space:nowrap;">' + a.coverage + '%</td>' +
          '<td style="padding:4px 6px;">' + a.confidence + '</td></tr>';
      });
      html += '</table>' +
        '<div class="nav"><button class="secondary" onclick="g=0;render()">Review / edit answers</button>' +
        '<span class="prog" id="globalStat"></span></div></div>';

      document.getElementById('stage').innerHTML = html;
      document.getElementById('prog').textContent = '';
      document.getElementById('prevBtn').style.display = 'none';
      document.getElementById('nextBtn').style.display = 'none';
      document.getElementById('finishBtn').style.display = 'none';
      google.script.run.withSuccessHandler(function (total) {
        document.getElementById('globalStat').textContent = total + ' ratings collected so far (all annotators)';
      }).getGlobalCount();
    }

    render();
  </script>
</body>
</html>
"""


def load_tasks(src):
    rows = list(csv.DictReader(open(src, newline="")))
    return [{"task_id": r["task_id"],
             "occupation": r.get("occupation", ""),
             "task_text": r["task_text"]} for r in rows]


def write_form(template, out, tasks, src, name):
    html = template.replace("__TASKS_JSON__", json.dumps(tasks, ensure_ascii=False))
    out.write_text(html, encoding="utf-8")
    n_occ = len(OrderedDict((t["occupation"], None) for t in tasks))
    print(f"Wrote {out} with {len(tasks)} tasks across {n_occ} occupations (source: {src.name}).")
    print(f"Paste this into the Apps Script editor as an HTML file named '{name}'.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", type=Path, default=None)
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--grouped", action="store_true",
                    help="also emit IndexGrouped.html")
    ap.add_argument("--only", choices=["index", "grouped"], default=None,
                    help="emit only one form")
    args = ap.parse_args()

    src = args.tasks or (FULL if args.full else DEFAULT)
    tasks = load_tasks(src)

    if args.only != "grouped":
        write_form(TEMPLATE, OUT, tasks, src, "Index")
    if args.grouped or args.only == "grouped":
        write_form(GROUPED_TEMPLATE, OUT_GROUPED, tasks, src, "IndexGrouped")


if __name__ == "__main__":
    main()
