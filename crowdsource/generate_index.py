#!/usr/bin/env python3
"""
Generate the agentic-coverage annotation web app forms.

Embeds a blinded task list (task_id, occupation, task_text ONLY -- no penalty
columns, so annotators cannot reverse-engineer the weights) into a self-contained
HTML form. Paste the output into the Apps Script editor as an HTML file.

The visual design mirrors the task->ability annotation tool: a dark sticky
header + footbar, card-based tasks, teal occupation headers, a progress bar and
pager, and a "gate" onboarding card that collects name/email ONCE. Here each
task asks a single neutral question -- how much of it a capable autonomous AI
agent could complete on its own (0-100%). Annotators never see the penalty
categories.

Two interfaces (both blind, both write to the same Google Sheet via Code.gs):
  Index.html         one task at a time, coverage slider + optional note  (?exec)
  IndexGrouped.html  all tasks for an occupation on one page, batch-save (?view=grouped)

Usage:
  python3 generate_index.py                    # Index.html from the default set
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


# ---------------------------------------------------------------------------
# Shared stylesheet -- adapted from the task->ability annotation tool so both
# datasets share one visual language. Injected into each template via __CSS__.
# ---------------------------------------------------------------------------
CSS = """<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #f0f2f5; color: #1a1a2e; padding-bottom: 76px; font-size: 14px; }

  .header { background: #1a1a2e; color: white; padding: 10px 18px; display: flex; align-items: center;
            justify-content: space-between; position: sticky; top: 0; z-index: 300;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3); flex-wrap: wrap; gap: 8px; }
  .header h1 { font-size: 14px; font-weight: 600; }
  .header .who { font-size: 12px; color: #a0aec0; }

  .layout { max-width: 900px; margin: 0 auto; padding: 14px 12px; }
  .container { min-width: 0; }

  /* onboarding gate */
  .gate { background: white; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);
          padding: 32px; max-width: 520px; margin: 56px auto; }
  .gate h2 { font-size: 20px; margin-bottom: 8px; color: #1a1a2e; text-align: center; }
  .gate .lede { color: #718096; font-size: 14px; line-height: 1.6; margin-bottom: 18px; text-align: center; }
  .gate input { width: 100%; padding: 12px 14px; border: 1.5px solid #e2e8f0; border-radius: 10px;
                font-size: 15px; margin-bottom: 12px; }
  .gate input:focus { outline: none; border-color: #4c51bf; }
  .gate button { width: 100%; padding: 13px; background: #4c51bf; color: white; border: none;
                 border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; }
  .gate button:hover { background: #434190; }
  .gate .credit-note { background: linear-gradient(135deg,#fffaf0,#feebc8); border: 1.5px solid #f6ad55;
                       border-radius: 10px; padding: 13px 15px; margin-bottom: 16px; font-size: 13px;
                       color: #7b341e; line-height: 1.6; }
  .gate .id-hint { font-size: 12.5px; color: #4a5568; margin: -4px 0 12px; min-height: 15px; }
  .gate .rubric { background: #f8fafc; border-radius: 10px; padding: 14px 16px; margin-top: 18px;
                  font-size: 13px; color: #4a5568; line-height: 1.7; }
  .gate .rubric b { color: #2d3748; }

  /* progress + pager */
  .topbar { background: white; border-radius: 12px; padding: 10px 16px; margin-bottom: 12px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08); position: sticky; top: 44px; z-index: 250; }
  .topbar .row1 { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
  .gprog { font-size: 13px; color: #4a5568; } .gprog b { color: #2d3748; }
  .progress-wrap { flex: 1; min-width: 120px; max-width: 320px; height: 8px; background: #edf2f7;
                   border-radius: 4px; overflow: hidden; }
  .progress-fill { height: 100%; width: 0; background: linear-gradient(90deg,#48bb78,#38a169);
                   border-radius: 4px; transition: width .3s; }
  .pager { display: flex; align-items: center; gap: 8px; }
  .pgbtn { padding: 6px 12px; border: 1.5px solid #cbd5e0; background: white; color: #2d3748;
           border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 600; }
  .pgbtn:hover { border-color: #4c51bf; color: #4c51bf; }
  .pgbtn:disabled { opacity: .4; cursor: not-allowed; }
  .pgpos { font-size: 12px; color: #718096; min-width: 150px; text-align: center; }

  .note { background: #ebf4ff; border: 1.5px solid #90cdf4; border-radius: 10px; padding: 9px 14px;
          margin-bottom: 12px; font-size: 12.5px; color: #2c5282; line-height: 1.55; }
  .note b { color: #2a4365; }

  /* occupation header */
  .occ-head { background: linear-gradient(135deg,#e0f2f1,#c8e6e3); border-radius: 12px; padding: 11px 18px;
              margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;
              flex-wrap: wrap; gap: 8px; }
  .occ-head .occ-name { font-size: 17px; font-weight: 700; color: #00695c; }
  .occ-head .occ-sub { font-size: 12px; color: #00897b; font-weight: 600; }

  /* task card */
  .task { background: white; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.07);
          margin-bottom: 12px; overflow: hidden; border-left: 3px solid transparent; }
  .task.complete { border-left-color: #48bb78; }
  .task.incomplete { border-left-color: #ed8936; }
  .task-top { padding: 11px 16px 9px; border-bottom: 1px solid #f0f0f0; }
  .task-meta { display: flex; gap: 6px; align-items: center; margin-bottom: 6px; flex-wrap: wrap; }
  .badge { padding: 2px 9px; border-radius: 12px; font-size: 10.5px; font-weight: 600; }
  .badge-id { background: #e8eaf6; color: #3949ab; font-family: monospace; }
  .badge-saved { background: #c6f6d5; color: #22543d; }
  .badge-todo { background: #feebc8; color: #9c4221; }
  .task-text { font-size: 14px; line-height: 1.5; color: #1a202c; }

  /* coverage control */
  .covbox { padding: 12px 16px 14px; }
  .covq { font-size: 11px; font-weight: 700; color: #718096; text-transform: uppercase;
          letter-spacing: .5px; margin-bottom: 8px; }
  .covline { display: flex; align-items: center; gap: 14px; }
  .covline input[type=range] { flex: 1; height: 6px; -webkit-appearance: none; appearance: none;
        background: #e2e8f0; border-radius: 4px; accent-color: #38a169; }
  .covline input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; appearance: none;
        width: 22px; height: 22px; border-radius: 50%; background: #38a169; cursor: pointer;
        border: 3px solid white; box-shadow: 0 1px 4px rgba(0,0,0,0.25); }
  .covline input[type=range]::-moz-range-thumb { width: 20px; height: 20px; border-radius: 50%;
        background: #38a169; cursor: pointer; border: 3px solid white; }
  .cov-val { min-width: 66px; text-align: right; font-size: 22px; font-weight: 800; color: #2d3748; }
  .anch { font-size: 12px; color: #718096; margin-top: 8px; min-height: 16px; }
  .cmt { width: 100%; margin-top: 10px; padding: 7px 11px; border: 1.5px solid #e2e8f0; border-radius: 8px;
         font-size: 12.5px; font-family: inherit; }
  .cmt:focus { outline: none; border-color: #4c51bf; }

  /* occupation submit row */
  .occ-submit-row { display: flex; align-items: center; gap: 12px; margin: 4px 0 10px; flex-wrap: wrap; }
  .occ-submit { padding: 9px 22px; background: #00796b; color: white; border: none; border-radius: 10px;
                cursor: pointer; font-size: 14px; font-weight: 700; }
  .occ-submit:hover { background: #00695c; }
  .occ-submit:disabled { opacity: .5; cursor: wait; }
  .occ-submit.primary { background: #4c51bf; } .occ-submit.primary:hover { background: #434190; }
  .status { font-size: 12.5px; font-weight: 600; }
  .status.ok { color: #2f855a; } .status.err { color: #c53030; } .status.saving { color: #718096; }

  /* sticky footbar */
  .footbar { position: fixed; bottom: 0; left: 0; right: 0; background: #1a1a2e; color: white;
             padding: 9px 18px; display: flex; align-items: center; justify-content: space-between;
             gap: 12px; z-index: 300; box-shadow: 0 -2px 10px rgba(0,0,0,0.3); flex-wrap: wrap; }
  .footbar .fstat { font-size: 12.5px; color: #cbd5e0; } .footbar .fstat b { color: white; }
  .submitallbtn { padding: 9px 20px; background: #48bb78; color: white; border: none; border-radius: 9px;
                  cursor: pointer; font-size: 14px; font-weight: 700; }
  .submitallbtn:hover { background: #38a169; }
  .submitallbtn:disabled { opacity: .55; cursor: wait; }

  /* results */
  .results { background: white; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.08);
             padding: 22px 24px; }
  .results h2 { font-size: 20px; margin-bottom: 8px; color: #1a1a2e; }
  .results p { color: #4a5568; line-height: 1.6; margin-bottom: 14px; }
  .results .dlabel { font-size: 11px; font-weight: 700; color: #718096; text-transform: uppercase;
                     letter-spacing: .5px; margin: 14px 0 8px; }
  .bar-row { display: flex; align-items: center; gap: 8px; margin: 3px 0; font-size: 13px; }
  .bar-row .blab { width: 66px; color: #718096; }
  .bar-row .bfill { display: inline-block; height: 14px; background: #38a169; border-radius: 3px; min-width: 2px; }
  .rtable { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 6px; }
  .rtable th { text-align: left; color: #718096; border-bottom: 1px solid #e2e8f0; padding: 6px 8px; font-weight: 600; }
  .rtable td { border-bottom: 1px solid #f4f6f8; padding: 6px 8px; }
  .rtable .occ { display: block; font-size: 10.5px; text-transform: uppercase; letter-spacing: .04em; color: #a0aec0; }
  .rtable .cov { font-weight: 700; color: #2f855a; white-space: nowrap; }

  /* toast */
  .toast { position: fixed; left: 50%; bottom: 66px; transform: translateX(-50%) translateY(8px);
           background: #1a1a2e; color: white; padding: 9px 16px; border-radius: 10px; font-size: 13px;
           font-weight: 600; box-shadow: 0 6px 24px rgba(0,0,0,0.35); opacity: 0; pointer-events: none;
           z-index: 600; transition: opacity .15s, transform .15s; }
  .toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }

  @media (max-width: 640px) {
    .layout { padding: 12px 8px; }
    .cov-val { font-size: 19px; min-width: 56px; }
  }
</style>"""


# Shared JS helpers injected into both templates via __HELPERS__.
HELPERS = """
    function anchor(v) {
      if (v >= 90) return "does essentially all of it alone";
      if (v >= 65) return "does most; a human finishes a little";
      if (v >= 35) return "about half needs a human to act / be present / decide";
      if (v >= 10) return "helps but a human must do most of it";
      return "cannot meaningfully do it alone";
    }
    function esc(x) { var d = document.createElement('div'); d.textContent = x == null ? '' : x; return d.innerHTML; }
    function escAttr(x) { return String(x == null ? '' : x).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;'); }
    function toast(msg) {
      var el = document.getElementById('toast'); el.textContent = msg; el.classList.add('show');
      clearTimeout(el._t); el._t = setTimeout(function(){ el.classList.remove('show'); }, 1600);
    }
    function refreshGlobal() {
      google.script.run.withSuccessHandler(function (total) {
        var g = document.getElementById('globalStat'); if (g) g.innerHTML = '<b>' + total + '</b> ratings collected so far';
      }).getGlobalCount();
    }
    // Stable session id derived from EMAIL only (name is for credit, not matching),
    // so a refresh / different device / a typo in the name still maps to the same
    // person and resumes (and re-rating upserts, not dupes). If no email is given
    // we fall back to the name so anonymous raters still get a stable-ish id.
    function sidFor(email, name) {
      var raw = String(email || '').toLowerCase().trim();
      if (!raw) raw = 'name:' + String(name || 'anon').toLowerCase().replace(/\\s+/g, ' ').trim();
      var h = 5381; for (var j = 0; j < raw.length; j++) { h = ((h << 5) + h + raw.charCodeAt(j)) >>> 0; }
      var slug = raw.replace(/[^a-z0-9]+/g, '').slice(0, 12);
      return 'sess-' + h.toString(36) + '-' + (slug || 'anon');
    }
    // Remember identity in this browser so the gate is prefilled after a refresh.
    function saveIdent() { try { localStorage.setItem('ate_cov_ident', JSON.stringify({ n: annName, e: annEmail })); } catch (e) {} }
    function prefillGate() {
      try {
        var d = JSON.parse(localStorage.getItem('ate_cov_ident') || '{}');
        if (d.e) document.getElementById('g-email').value = d.e;
        if (d.n) document.getElementById('g-name').value = d.n;
        if (d.e) lookupIdentity();
      } catch (e) {}
    }
    // Email is the key. When one is entered, ask the Sheet if we already know this
    // person; if so, prefill their name. If not, nudge them to add one for credit.
    function lookupIdentity() {
      var em = (document.getElementById('g-email').value || '').trim();
      var hint = document.getElementById('id-hint');
      if (!em) { if (hint) hint.textContent = ''; return; }
      google.script.run
        .withSuccessHandler(function (name) {
          var nm = document.getElementById('g-name');
          if (name) {
            if (!nm.value.trim()) nm.value = name;
            if (hint) hint.textContent = '✓ Welcome back — resuming as ' + (nm.value.trim() || name) + '.';
          } else if (hint) {
            hint.textContent = 'New here? Add your name so we can credit you.';
          }
        })
        .withFailureHandler(function () {})
        .getIdentityForEmail(em);
    }
"""


# ---------------------------------------------------------------------------
# GROUPED form: all tasks for an occupation on one page, batch-saved.
# ---------------------------------------------------------------------------
GROUPED_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<base target="_top">
<meta charset="utf-8">
__CSS__
</head>
<body>

<div id="gate" class="gate">
  <h2>Can an AI agent do these tasks on its own?</h2>
  <div class="lede">Help validate an AI-exposure research dataset. You'll review real work
    tasks one occupation at a time and judge how much an autonomous AI agent could do unaided.</div>
  <div class="credit-note">
    &#127942; <b>Get credited.</b> This dataset is public and its human validation is
    <b>in progress</b>. Credit in the <b>Acknowledgements</b> is added <b>only when you
    complete all 180 occupations (200 tasks)</b>. Partial runs still help the research,
    but only a full run earns a credit. Your email saves your progress so you can stop
    and resume anytime.
  </div>
  <input id="g-email" type="email" placeholder="Email (saves your progress)" onblur="lookupIdentity()" onchange="lookupIdentity()">
  <input id="g-name" type="text" placeholder="Your name (for the Acknowledgements)">
  <div class="id-hint" id="id-hint"></div>
  <button onclick="enterTool()">Start annotating &#8594;</button>
  <div class="rubric">
    <b>For each task, set one slider:</b> how much of it a capable autonomous AI agent (2026)
    could complete end to end, <b>on its own</b>, with no human stepping in to act, be physically
    present, decide, or take responsibility. The agent can browse, write, reason, and use tools,
    but has <b>no physical body</b> and no legal authority of its own. Judge only what it can
    finish <b>unaided</b>. That's it &#8212; read, slide, next.
  </div>
</div>

<div id="app" style="display:none">
  <div class="header">
    <h1>Agentic-Coverage Annotation &#183; by occupation</h1>
    <span class="who" id="who"></span>
  </div>
  <div class="layout"><div class="container">
    <div class="topbar">
      <div class="row1">
        <span class="gprog" id="gprog"></span>
        <div class="progress-wrap"><div class="progress-fill" id="pfill"></div></div>
        <div class="pager">
          <button class="pgbtn" id="prevBtn" onclick="prevGroup()">&#8592; Prev</button>
          <span class="pgpos" id="pgpos"></span>
          <button class="pgbtn" id="nextBtn" onclick="nextGroup()">Next &#8594;</button>
        </div>
      </div>
    </div>
    <div class="note">Move each slider to how much an autonomous AI agent could do <b>unaided</b>,
      then <b>Save this occupation</b>. A short note is optional. Your name/email were captured once
      and apply to everything you rate.</div>
    <div id="stage"></div>
  </div></div>

  <div class="footbar">
    <span class="fstat" id="fstat"></span>
    <span class="fstat" id="globalStat"></span>
    <button class="submitallbtn" id="finishBtn" onclick="finish()">Finish &amp; see results</button>
  </div>
</div>
<div class="toast" id="toast"></div>

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

    var sessionId = '';  // set from identity in enterTool() so refresh resumes
    var g = 0, answers = {}, savedTasks = {}, annName = 'anonymous', annEmail = '';

__HELPERS__

    function enterTool() {
      annEmail = (document.getElementById('g-email').value || '').trim();
      annName = (document.getElementById('g-name').value || '').trim() || 'anonymous';
      sessionId = sidFor(annEmail, annName);
      saveIdent();
      document.getElementById('gate').style.display = 'none';
      document.getElementById('app').style.display = '';
      document.getElementById('who').textContent = annName + (annEmail ? ' (' + annEmail + ')' : '');
      refreshGlobal();
      // Resume: pull this annotator's prior ratings, restore them, and jump to
      // the first task they haven't rated yet (or straight to results if done).
      var runner = google.script.run
        .withSuccessHandler(function (prior) {
          prior = prior || {};
          var ids = Object.keys(prior), n = ids.length;
          ids.forEach(function (id) {
            answers[id] = { coverage: prior[id].coverage, comment: prior[id].comment };
            savedTasks[id] = true;
          });
          // Count only tasks that belong to THIS handout (start/end slice).
          var done = 0;
          TASKS.forEach(function (t) { if (savedTasks[t.task_id]) done++; });
          if (done) toast('Welcome back, ' + annName + ' — ' + done + ' of ' + TASKS.length + ' already done, resuming');
          if (TASKS.length > 0 && done >= TASKS.length) { showResults(); return; }
          jumpToFirstUnrated();
          render();
        })
        .withFailureHandler(function () { render(); });
      // Resume is keyed on EMAIL (the identity), so prior ratings come back even
      // if they were saved under an older session-id scheme. No email -> fall
      // back to the (name-derived) session id.
      if (annEmail) runner.getAnnotationsForEmail(annEmail);
      else runner.getAnnotationsForSession(sessionId);
    }

    function updateProgress() {
      var saved = Object.keys(savedTasks).length, total = TASKS.length;
      document.getElementById('pfill').style.width = (total ? (saved / total * 100) : 0) + '%';
      document.getElementById('gprog').innerHTML = '<b>' + saved + '</b> / ' + total + ' tasks saved';
      document.getElementById('fstat').innerHTML = '<b>' + saved + '</b> of ' + total + ' tasks saved';
    }

    function render() {
      var grp = GROUPS[g];
      document.getElementById('pgpos').textContent = 'Occupation ' + (g + 1) + ' of ' + GROUPS.length;
      var html = '<div class="occ-head"><span class="occ-name">' + esc(grp.occupation) + '</span>' +
                 '<span class="occ-sub">' + grp.tasks.length + ' task' + (grp.tasks.length === 1 ? '' : 's') + '</span></div>';
      grp.tasks.forEach(function (t) {
        var prev = answers[t.task_id] || { coverage: 50, comment: "" };
        var done = !!savedTasks[t.task_id];
        html +=
          '<div class="task ' + (done ? 'complete' : 'incomplete') + '" id="task_' + t.task_id + '">' +
            '<div class="task-top">' +
              '<div class="task-meta">' +
                '<span class="badge badge-id">#' + esc(t.task_id) + '</span>' +
                '<span class="badge ' + (done ? 'badge-saved">saved' : 'badge-todo">to rate') + '</span>' +
              '</div>' +
              '<div class="task-text">' + esc(t.task_text) + '</div>' +
            '</div>' +
            '<div class="covbox">' +
              '<div class="covq">How much could an autonomous AI agent complete on its own?</div>' +
              '<div class="covline">' +
                '<input type="range" min="0" max="100" step="5" id="cov_' + t.task_id + '" value="' + prev.coverage + '">' +
                '<span class="cov-val"><span id="cv_' + t.task_id + '">' + prev.coverage + '</span>%</span>' +
              '</div>' +
              '<div class="anch" id="an_' + t.task_id + '">' + anchor(prev.coverage) + '</div>' +
              '<input class="cmt" id="cm_' + t.task_id + '" placeholder="optional note (e.g. needs a human signature / on-site presence)" value="' + escAttr(prev.comment) + '">' +
            '</div>' +
          '</div>';
      });
      html += '<div class="occ-submit-row">' +
              '<button class="occ-submit" id="saveBtn" onclick="saveGroup()">Save this occupation (' + grp.tasks.length + ' tasks)</button>' +
              '<span class="status" id="saveStatus"></span></div>';
      document.getElementById('stage').innerHTML = html;

      grp.tasks.forEach(function (t) {
        var cov = document.getElementById('cov_' + t.task_id);
        cov.oninput = function () {
          document.getElementById('cv_' + t.task_id).textContent = cov.value;
          document.getElementById('an_' + t.task_id).textContent = anchor(parseInt(cov.value, 10));
        };
      });
      document.getElementById('prevBtn').disabled = (g === 0);
      document.getElementById('nextBtn').disabled = (g === GROUPS.length - 1);
      updateProgress();
    }

    function collectGroup() {
      var grp = GROUPS[g], rows = [];
      grp.tasks.forEach(function (t) {
        var cov = parseInt(document.getElementById('cov_' + t.task_id).value, 10);
        var comment = document.getElementById('cm_' + t.task_id).value || "";
        answers[t.task_id] = { coverage: cov, comment: comment };
        rows.push([t.task_id, t.occupation, t.task_text, (cov / 100).toFixed(2), comment]);
      });
      return rows;
    }

    function saveGroup() {
      var rows = collectGroup();
      var btn = document.getElementById('saveBtn'), st = document.getElementById('saveStatus');
      btn.disabled = true; st.className = 'status saving'; st.textContent = 'Saving...';
      google.script.run
        .withSuccessHandler(function () {
          rows.forEach(function (r) { savedTasks[r[0]] = true; });
          btn.disabled = false; st.className = 'status ok'; st.textContent = 'Saved';
          toast('Saved ' + rows.length + ' task' + (rows.length === 1 ? '' : 's'));
          render(); refreshGlobal();
        })
        .withFailureHandler(function (err) {
          btn.disabled = false; st.className = 'status err'; st.textContent = 'Save failed'; alert('Save failed: ' + err);
        })
        .submitAnnotation({ annotator: annName, email: annEmail, sessionId: sessionId, rows: rows });
    }

    function jumpToFirstUnrated() {
      for (var k = 0; k < GROUPS.length; k++) {
        for (var j = 0; j < GROUPS[k].tasks.length; j++) {
          if (!savedTasks[GROUPS[k].tasks[j].task_id]) { g = k; return; }
        }
      }
      g = 0;
    }

    function nextGroup() { collectGroup(); if (g < GROUPS.length - 1) { g++; render(); } }
    function prevGroup() { collectGroup(); if (g > 0) { g--; render(); } }

    function taskById(id) {
      for (var k = 0; k < TASKS.length; k++) { if (String(TASKS[k].task_id) === String(id)) return TASKS[k]; }
      return { occupation: "", task_text: "" };
    }

    function finish() {
      var rows = collectGroup();
      var btn = document.getElementById('finishBtn');
      btn.disabled = true; btn.textContent = 'Saving...';
      google.script.run
        .withSuccessHandler(function () { rows.forEach(function (r) { savedTasks[r[0]] = true; }); showResults(); })
        .withFailureHandler(function (err) { btn.disabled = false; btn.textContent = 'Finish & see results'; alert('Save failed: ' + err); })
        .submitAnnotation({ annotator: annName, email: annEmail, sessionId: sessionId, rows: rows });
    }

    function showResults() {
      var ids = Object.keys(answers);
      var n = ids.length, sum = 0, buckets = [0, 0, 0, 0, 0];
      ids.forEach(function (id) { var c = answers[id].coverage; sum += c; buckets[Math.min(4, Math.floor(c / 20))]++; });
      var mean = n ? Math.round(sum / n) : 0;
      var labels = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'];
      var maxb = Math.max.apply(null, buckets) || 1;

      var html = '<div class="results"><h2>Thank you, ' + esc(annName) + '!</h2>' +
        '<p>You rated <b>' + n + '</b> task' + (n === 1 ? '' : 's') +
        '. Your average coverage was <b>' + mean + '%</b> (how much you judged an autonomous AI agent could do unaided).</p>' +
        '<div class="dlabel">Distribution of your ratings</div>';
      for (var b = 0; b < 5; b++) {
        var w = Math.round(buckets[b] / maxb * 100);
        html += '<div class="bar-row"><span class="blab">' + labels[b] + '</span>' +
          '<span class="bfill" style="width:' + w + '%"></span><span style="color:#718096">' + buckets[b] + '</span></div>';
      }
      html += '<div class="dlabel">Your answers</div><table class="rtable">' +
        '<tr><th>Task</th><th>Coverage</th></tr>';
      ids.forEach(function (id) {
        var t = taskById(id), a = answers[id];
        html += '<tr><td><span class="occ">' + esc(t.occupation) + '</span>' + esc(t.task_text) + '</td>' +
          '<td class="cov">' + a.coverage + '%</td></tr>';
      });
      html += '</table><div class="occ-submit-row" style="margin-top:16px">' +
        '<button class="occ-submit primary" onclick="g=0;render()">Review / edit answers</button></div></div>';

      document.getElementById('stage').innerHTML = html;
      document.querySelector('.topbar').style.display = 'none';
      document.querySelector('.note').style.display = 'none';
      document.getElementById('finishBtn').style.display = 'none';
      refreshGlobal();
    }

    prefillGate();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# SINGLE form: one task per screen, careful pace.
# ---------------------------------------------------------------------------
TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<base target="_top">
<meta charset="utf-8">
__CSS__
</head>
<body>

<div id="gate" class="gate">
  <h2>Can an AI agent do this task on its own?</h2>
  <div class="lede">Help validate an AI-exposure research dataset. You'll review real work
    tasks one at a time and judge how much an autonomous AI agent could do unaided.</div>
  <div class="credit-note">
    &#127942; <b>Get credited.</b> This dataset is public and its human validation is
    <b>in progress</b>. Credit in the <b>Acknowledgements</b> is added <b>only when you
    complete all 180 occupations (200 tasks)</b>. Partial runs still help the research,
    but only a full run earns a credit. Your email saves your progress so you can stop
    and resume anytime.
  </div>
  <input id="g-email" type="email" placeholder="Email (saves your progress)" onblur="lookupIdentity()" onchange="lookupIdentity()">
  <input id="g-name" type="text" placeholder="Your name (for the Acknowledgements)">
  <div class="id-hint" id="id-hint"></div>
  <button onclick="enterTool()">Start annotating &#8594;</button>
  <div class="rubric">
    <b>For each task, set one slider:</b> how much of it a capable autonomous AI agent (2026)
    could complete end to end, <b>on its own</b>, with no human stepping in to act, be physically
    present, decide, or take responsibility. The agent can browse, write, reason, and use tools,
    but has <b>no physical body</b> and no legal authority of its own. Judge only what it can
    finish <b>unaided</b>.
  </div>
</div>

<div id="app" style="display:none">
  <div class="header">
    <h1>Agentic-Coverage Annotation</h1>
    <span class="who" id="who"></span>
  </div>
  <div class="layout"><div class="container">
    <div class="topbar">
      <div class="row1">
        <span class="gprog" id="gprog"></span>
        <div class="progress-wrap"><div class="progress-fill" id="pfill"></div></div>
        <div class="pager">
          <button class="pgbtn" id="prevBtn" onclick="back()">&#8592; Back</button>
          <span class="pgpos" id="pgpos"></span>
        </div>
      </div>
    </div>
    <div id="stage"></div>
  </div></div>

  <div class="footbar">
    <span class="fstat" id="fstat"></span>
    <span class="fstat" id="globalStat"></span>
  </div>
</div>
<div class="toast" id="toast"></div>

<script>
    var TASKS = __TASKS_JSON__;
    var startParam = "<?= startParam ?>", endParam = "<?= endParam ?>";
    var s = parseInt(startParam, 10), e = parseInt(endParam, 10);
    if (!isNaN(s) || !isNaN(e)) {
      var a = isNaN(s) ? 1 : s, b = isNaN(e) ? TASKS.length : e;
      TASKS = TASKS.slice(a - 1, b);
    }
    var sessionId = '';  // set from identity in enterTool() so refresh resumes
    var i = 0, answers = {}, savedTasks = {}, annName = 'anonymous', annEmail = '';

__HELPERS__

    function enterTool() {
      annEmail = (document.getElementById('g-email').value || '').trim();
      annName = (document.getElementById('g-name').value || '').trim() || 'anonymous';
      sessionId = sidFor(annEmail, annName);
      saveIdent();
      document.getElementById('gate').style.display = 'none';
      document.getElementById('app').style.display = '';
      document.getElementById('who').textContent = annName + (annEmail ? ' (' + annEmail + ')' : '');
      refreshGlobal();
      // Resume: pull this annotator's prior ratings, restore them, and jump to
      // the first task they haven't rated yet (or straight to results if done).
      var runner = google.script.run
        .withSuccessHandler(function (prior) {
          prior = prior || {};
          var ids = Object.keys(prior), n = ids.length;
          ids.forEach(function (id) {
            answers[id] = { coverage: prior[id].coverage, comment: prior[id].comment };
            savedTasks[id] = true;
          });
          // Count only tasks that belong to THIS handout (start/end slice).
          var done = 0;
          TASKS.forEach(function (t) { if (savedTasks[t.task_id]) done++; });
          if (done) toast('Welcome back, ' + annName + ' — ' + done + ' of ' + TASKS.length + ' already done, resuming');
          if (TASKS.length > 0 && done >= TASKS.length) { showResults(); return; }
          jumpToFirstUnrated();
          render();
        })
        .withFailureHandler(function () { render(); });
      // Resume is keyed on EMAIL (the identity), so prior ratings come back even
      // if they were saved under an older session-id scheme. No email -> fall
      // back to the (name-derived) session id.
      if (annEmail) runner.getAnnotationsForEmail(annEmail);
      else runner.getAnnotationsForSession(sessionId);
    }

    function updateProgress() {
      var saved = Object.keys(savedTasks).length, total = TASKS.length;
      document.getElementById('pfill').style.width = (total ? (saved / total * 100) : 0) + '%';
      document.getElementById('gprog').innerHTML = '<b>' + saved + '</b> / ' + total + ' saved';
      document.getElementById('fstat').innerHTML = '<b>' + saved + '</b> of ' + total + ' saved';
      document.getElementById('pgpos').textContent = 'Task ' + (i + 1) + ' of ' + TASKS.length;
    }

    function render() {
      var t = TASKS[i];
      var prev = answers[t.task_id] || { coverage: 50, comment: "" };
      var done = !!savedTasks[t.task_id];
      var html =
        '<div class="occ-head"><span class="occ-name">' + esc(t.occupation) + '</span></div>' +
        '<div class="task ' + (done ? 'complete' : 'incomplete') + '">' +
          '<div class="task-top">' +
            '<div class="task-meta">' +
              '<span class="badge badge-id">#' + esc(t.task_id) + '</span>' +
              '<span class="badge ' + (done ? 'badge-saved">saved' : 'badge-todo">to rate') + '</span>' +
            '</div>' +
            '<div class="task-text">' + esc(t.task_text) + '</div>' +
          '</div>' +
          '<div class="covbox">' +
            '<div class="covq">How much could an autonomous AI agent complete on its own?</div>' +
            '<div class="covline">' +
              '<input type="range" min="0" max="100" step="5" id="cov" value="' + prev.coverage + '">' +
              '<span class="cov-val"><span id="cv">' + prev.coverage + '</span>%</span>' +
            '</div>' +
            '<div class="anch" id="anch">' + anchor(prev.coverage) + '</div>' +
            '<input class="cmt" id="comment" placeholder="optional note (e.g. needs a human signature / on-site presence)" value="' + escAttr(prev.comment) + '">' +
          '</div>' +
        '</div>' +
        '<div class="occ-submit-row">' +
          '<button class="occ-submit" id="saveBtn" onclick="saveNext()">' +
            (i === TASKS.length - 1 ? 'Save &amp; finish' : 'Save &amp; next &#8594;') + '</button>' +
          '<span class="status" id="saveStatus"></span></div>';
      document.getElementById('stage').innerHTML = html;
      var cov = document.getElementById('cov');
      cov.oninput = function () {
        document.getElementById('cv').textContent = cov.value;
        document.getElementById('anch').textContent = anchor(parseInt(cov.value, 10));
      };
      document.getElementById('prevBtn').disabled = (i === 0);
      updateProgress();
    }

    function collect() {
      var t = TASKS[i];
      answers[t.task_id] = {
        coverage: parseInt(document.getElementById('cov').value, 10),
        comment: document.getElementById('comment').value || ""
      };
      return t;
    }

    function saveNext() {
      var t = collect(), a = answers[t.task_id];
      var btn = document.getElementById('saveBtn'), st = document.getElementById('saveStatus');
      btn.disabled = true; st.className = 'status saving'; st.textContent = 'Saving...';
      google.script.run
        .withSuccessHandler(function () {
          savedTasks[t.task_id] = true; toast('Saved');
          if (i < TASKS.length - 1) { i++; render(); } else { showResults(); }
        })
        .withFailureHandler(function (err) {
          btn.disabled = false; st.className = 'status err'; st.textContent = 'Save failed'; alert('Save failed: ' + err);
        })
        .submitAnnotation({
          annotator: annName, email: annEmail, sessionId: sessionId,
          rows: [[t.task_id, t.occupation, t.task_text, (a.coverage / 100).toFixed(2), a.comment]]
        });
    }

    function jumpToFirstUnrated() {
      for (var k = 0; k < TASKS.length; k++) { if (!savedTasks[TASKS[k].task_id]) { i = k; return; } }
      i = 0;
    }

    function back() { collect(); if (i > 0) { i--; render(); } }

    function taskById(id) {
      for (var k = 0; k < TASKS.length; k++) { if (String(TASKS[k].task_id) === String(id)) return TASKS[k]; }
      return { occupation: "", task_text: "" };
    }

    function showResults() {
      var ids = Object.keys(answers);
      var n = ids.length, sum = 0, buckets = [0, 0, 0, 0, 0];
      ids.forEach(function (id) { var c = answers[id].coverage; sum += c; buckets[Math.min(4, Math.floor(c / 20))]++; });
      var mean = n ? Math.round(sum / n) : 0;
      var labels = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'];
      var maxb = Math.max.apply(null, buckets) || 1;

      var html = '<div class="results"><h2>Thank you, ' + esc(annName) + '!</h2>' +
        '<p>You rated <b>' + n + '</b> task' + (n === 1 ? '' : 's') +
        '. Your average coverage was <b>' + mean + '%</b> (how much you judged an autonomous AI agent could do unaided).</p>' +
        '<div class="dlabel">Distribution of your ratings</div>';
      for (var b = 0; b < 5; b++) {
        var w = Math.round(buckets[b] / maxb * 100);
        html += '<div class="bar-row"><span class="blab">' + labels[b] + '</span>' +
          '<span class="bfill" style="width:' + w + '%"></span><span style="color:#718096">' + buckets[b] + '</span></div>';
      }
      html += '<div class="dlabel">Your answers</div><table class="rtable">' +
        '<tr><th>Task</th><th>Coverage</th></tr>';
      ids.forEach(function (id) {
        var t = taskById(id), a = answers[id];
        html += '<tr><td><span class="occ">' + esc(t.occupation) + '</span>' + esc(t.task_text) + '</td>' +
          '<td class="cov">' + a.coverage + '%</td></tr>';
      });
      html += '</table><div class="occ-submit-row" style="margin-top:16px">' +
        '<button class="occ-submit primary" onclick="i=0;render()">Review / edit answers</button></div></div>';

      document.getElementById('stage').innerHTML = html;
      document.querySelector('.topbar').style.display = 'none';
      refreshGlobal();
    }

    prefillGate();
</script>
</body>
</html>
"""


# Inject the shared stylesheet + helpers into both templates.
for _name in ("TEMPLATE", "GROUPED_TEMPLATE"):
    globals()[_name] = globals()[_name].replace("__CSS__", CSS).replace("__HELPERS__", HELPERS)


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
