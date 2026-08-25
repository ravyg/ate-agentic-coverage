/**
 * ATES Agentic-Coverage Crowdsource Annotation — Backend
 * ------------------------------------------------------
 * Serves the coverage-rating form and writes every submission into a Google
 * Sheet. No external database. Runs entirely inside your Google account for free.
 *
 * This is the coverage counterpart to the task->ability annotation tool. Here
 * each annotator answers ONE neutral question per task: how much of the task
 * could an autonomous AI agent complete end to end, on its own (0-100%).
 * Annotators do NOT see the penalty categories, so they cannot reverse-engineer
 * the weights we are estimating.
 *
 * SETUP: This script must be CONTAINER-BOUND to a Google Sheet.
 *   Create a Google Sheet -> Extensions -> Apps Script -> paste this file
 *   (plus Index.html and IndexGrouped.html) -> Deploy -> Web app.
 * See DEPLOY.md for the full step-by-step.
 */

// Where to store answers.
//   - Container-bound deploy (script created via a Sheet): leave SHEET_ID = ''.
//   - Standalone deploy (clasp / standalone script): paste the target Sheet id
//     here. A standalone web app avoids the "Access Denied - Drive" wall that
//     consumer (@gmail) container-bound web apps hit for anonymous raters.
var SHEET_ID = '';

// Name of the tab where annotations are stored (auto-created on first submit).
var RESPONSE_SHEET = 'Responses';

/** The spreadsheet we read/write: bound sheet, or SHEET_ID if standalone. */
function getSpreadsheet_() {
  return SHEET_ID ? SpreadsheetApp.openById(SHEET_ID) : SpreadsheetApp.getActiveSpreadsheet();
}

// Column headers written to the Responses tab.
var HEADERS = [
  'timestamp', 'annotator', 'annotator_email', 'session_id',
  'task_id', 'occupation', 'task_text',
  'coverage',            // 0.00-1.00: fraction an autonomous agent can do alone
  'comment'
];

/**
 * Serves the HTML form.
 *   ...exec                     -> default one-task-at-a-time form (Index)
 *   ...exec?view=grouped        -> fast grouped-by-occupation form (IndexGrouped)
 *   ...exec?export=json         -> read-only JSON dump of all responses
 *   ...exec?start=1&end=50      -> hand out a task range (divide and conquer)
 */
function doGet(e) {
  // Read-only JSON export of all annotations (does not affect the form path).
  //   ...exec?export=json
  if (e && e.parameter && e.parameter.export === 'json') {
    var sh = getResponseSheet_();
    var last = sh.getLastRow();
    var values = (last > 1) ? sh.getRange(2, 1, last - 1, HEADERS.length).getValues() : [];
    var rows = values.map(function (r) {
      var o = {};
      for (var i = 0; i < HEADERS.length; i++) {
        o[HEADERS[i]] = (r[i] instanceof Date) ? r[i].toISOString() : r[i];
      }
      return o;
    });
    return ContentService
      .createTextOutput(JSON.stringify({ ok: true, count: rows.length, headers: HEADERS, rows: rows }))
      .setMimeType(ContentService.MimeType.JSON);
  }

  // Grouped-by-occupation fast interface, or the default single-task form.
  //   ...exec?view=grouped   (optionally &start=&end= exactly like the default)
  var templateName = (e && e.parameter && e.parameter.view === 'grouped') ? 'IndexGrouped' : 'Index';

  var t = HtmlService.createTemplateFromFile(templateName);
  t.startParam = (e && e.parameter && e.parameter.start) ? e.parameter.start : '';
  t.endParam   = (e && e.parameter && e.parameter.end)   ? e.parameter.end   : '';
  return t.evaluate()
    .setTitle('ATES Agentic-Coverage Annotation')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1.0')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/** Returns (creating if needed) the Responses sheet with a header row. */
function getResponseSheet_() {
  var ss = getSpreadsheet_();
  var sh = ss.getSheetByName(RESPONSE_SHEET);
  if (!sh) {
    sh = ss.insertSheet(RESPONSE_SHEET);
    sh.appendRow(HEADERS);
    sh.setFrozenRows(1);
    return sh;
  }
  // Self-heal: if the stored header row doesn't match the current HEADERS
  // (e.g. after we drop/rename a column), rewrite row 1 in place so a CSV
  // download and the JSON export always agree with the code schema. This
  // only touches the header row; it never deletes or moves response data.
  var width = Math.max(HEADERS.length, sh.getLastColumn());
  var current = sh.getRange(1, 1, 1, width).getValues()[0];
  var mismatch = current.length < HEADERS.length;
  for (var c = 0; c < HEADERS.length && !mismatch; c++) {
    if (String(current[c]) !== HEADERS[c]) mismatch = true;
  }
  // Also clear any stale trailing header cells beyond the new schema width.
  for (var d = HEADERS.length; d < current.length && !mismatch; d++) {
    if (String(current[d]) !== '') mismatch = true;
  }
  if (mismatch) {
    sh.getRange(1, 1, 1, width).clearContent();
    sh.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
    sh.setFrozenRows(1);
  }
  return sh;
}

/**
 * Called from the browser via google.script.run.
 * payload = {
 *   annotator: string, email: string, sessionId: string,
 *   rows: [[task_id, occupation, task_text, coverage, comment], ...]
 * }
 *
 * The grouped form submits MANY tasks (distinct task_ids) in one call; the
 * default form submits one. Both are handled: we upsert per DISTINCT
 * (session_id, task_id), so re-submitting any task replaces only that task's
 * prior row for this annotator, and different annotators keep separate rows
 * (which is what lets us measure inter-rater agreement).
 *
 * Returns { ok, written, replaced, totalResponses }.
 */
function submitAnnotation(payload) {
  var lock = LockService.getScriptLock();
  lock.waitLock(30000); // serialize writes so simultaneous submits don't collide
  try {
    var sh = getResponseSheet_();
    var ts = new Date();
    var sid = String(payload.sessionId || '');
    var prefix = [ts, payload.annotator || '', payload.email || '', sid];
    var out = (payload.rows || []).map(function (r) { return prefix.concat(r); });
    if (out.length === 0) return { ok: true, written: 0, replaced: 0, totalResponses: sh.getLastRow() - 1 };

    var SID_COL = 3, TASK_COL = 4; // 0-based positions of session_id and task_id

    // Set of task_ids in THIS submission, so we clean each one exactly once.
    var incomingIds = {};
    out.forEach(function (r) { incomingIds[String(r[TASK_COL])] = true; });

    // 1) Remove this annotator's PRIOR rows for ANY task in this batch, so a
    //    re-submit updates in place instead of duplicating.
    var replaced = 0;
    var last = sh.getLastRow();
    if (last > 1 && sid) {
      var data = sh.getRange(2, 1, last - 1, HEADERS.length).getValues();
      var rowsToDelete = [];
      for (var i = 0; i < data.length; i++) {
        if (String(data[i][SID_COL]) === sid && incomingIds[String(data[i][TASK_COL])]) {
          rowsToDelete.push(i + 2); // +2: skip header (row 1) and 0-based offset
        }
      }
      // Delete bottom-up so earlier row numbers stay valid as we remove.
      for (var j = rowsToDelete.length - 1; j >= 0; j--) {
        sh.deleteRow(rowsToDelete[j]);
        replaced++;
      }
    }

    // 2) Append the fresh rows.
    var startRow = sh.getLastRow() + 1;
    sh.getRange(startRow, 1, out.length, out[0].length).setValues(out);
    SpreadsheetApp.flush();
    return { ok: true, written: out.length, replaced: replaced, totalResponses: sh.getLastRow() - 1 };
  } catch (err) {
    return { ok: false, error: String(err) };
  } finally {
    lock.releaseLock();
  }
}

/** Lightweight stat call for the form's progress banner. */
function getGlobalCount() {
  var sh = getResponseSheet_();
  return Math.max(0, sh.getLastRow() - 1);
}

/**
 * Resume support: return THIS annotator's prior ratings so a refresh (or a
 * different device) picks up where they left off instead of starting over.
 * The client derives a stable session_id from the annotator's name+email, so
 * the same person maps to the same id across loads.
 *
 * Returns an object keyed by task_id: { "<task_id>": { coverage: 0-100 int,
 * comment: string }, ... }. Only rows for the given session_id are returned,
 * so an annotator never sees anyone else's answers. Note: the session_id is
 * derived, not secret, so this is a convenience/scoping mechanism, not auth.
 */
function getAnnotationsForSession(sessionId) {
  var sid = String(sessionId || '');
  if (!sid) return {};
  var sh = getResponseSheet_();
  var last = sh.getLastRow();
  if (last < 2) return {};
  var data = sh.getRange(2, 1, last - 1, HEADERS.length).getValues();
  var SID = 3, TASK = 4, COV = 7, CMT = 8; // 0-based column positions
  var out = {};
  for (var i = 0; i < data.length; i++) {
    if (String(data[i][SID]) === sid) {
      out[String(data[i][TASK])] = {
        coverage: Math.round(Number(data[i][COV]) * 100),
        comment: (data[i][CMT] == null) ? '' : String(data[i][CMT])
      };
    }
  }
  return out;
}
