// Read-only compatibility probe: real installed scheduling/capture/wait/detection code,
// simulated page transport and extraction. No Electron launch or network access.
// Usage: node tests/check_domi_runtime.cjs [Domi.app path]
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {performance} = require('node:perf_hooks');
const crypto = require('node:crypto');
const app = process.argv[2] && !process.argv[2].startsWith('--') ? process.argv[2] : '/Applications/Domi.app';
const resources = path.join(app, 'Contents/Resources');
const root = path.resolve(__dirname, '..');
const archive = fs.readFileSync(path.join(resources, 'app.asar'));
const header = JSON.parse(archive.subarray(16, 16 + archive.readUInt32LE(12)));
function asarFile(relative) {
  let entry = header;
  for (const component of relative.split('/')) entry = entry.files[component];
  const start = 8 + archive.readUInt32LE(4) + Number(entry.offset);
  return archive.subarray(start, start + entry.size).toString();
}
function loadModule(name, deps) {
  const context = vm.createContext({module: {exports: {}}, require: n => deps[n] || {},
    console, URL, Buffer, setTimeout, clearTimeout});
  const code = asarFile('public/electron/service/embeddedBrowser/' + name + '.js');
  vm.runInContext(code, context);
  return {exports: context.module.exports, context, hash: crypto.createHash('sha256').update(code).digest('hex')};
}
const hostModule = loadModule('browserHost', {crypto});
const runnerModule = loadModule('browserWorkflowRunner', {'./browserHost': hostModule.exports});
const {BrowserWorkflowRunner} = runnerModule.exports;
const {BrowserHost, failure} = hostModule.exports;
const pageDir = path.join(resources, 'browser-extensions/embedded-workflow');
const page = vm.createContext({console, URL, setTimeout, clearTimeout, setInterval, clearInterval,
  location: new URL('https://fixture.invalid/search'),
  document: {body: {innerText: ''}, title: 'local fixture', readyState: 'complete',
    visibilityState: 'visible', getElementsByTagName: () => []},
  window: {origin: 'https://fixture.invalid', addEventListener() {}, postMessage() {}},
  BrowserPageElements: {visible: () => true, enabled: () => true, describe: () => ({}),
    normalize: x => x, locate: () => [], snapshot: () => ({})}});
vm.runInContext(fs.readFileSync(path.join(pageDir, 'protocol.js'), 'utf8'), page);
const content = fs.readFileSync(path.join(pageDir, 'content.js'), 'utf8');
// Expose private functions in an in-memory copy only; production code is untouched.
vm.runInContext(content.replace(/\}\)\(\);\s*$/, `
  globalThis.probe = {executeWait, executeDetect, createContext, execution, executeStep, evaluateCondition};
})();`), page);
const fixture = JSON.parse(execFileSync('python3', ['-B', '-c', `
import sys,json
sys.path.insert(0, 'tests')
from workflow_helpers import build, load_builder
print(json.dumps(build(load_builder('versions/wts-v0-2'))))
`], {cwd: root, encoding: 'utf8'}));
const collectors = fixture.steps.filter(s => s.action === 'tabs.foreach');
function pageContext(input = {}) {
  return page.probe.createContext({deadline_at: new Date(Date.now() + 180000).toISOString(), input});
}
function setup() {
  const scope = {};
  const job = {context: {}, deadline: Date.now() + 180000, allowedDomains: fixture.allowed_domains};
  let nextId = 0;
  const tab = {__tabId: 'list', isDestroyed: () => false, webContents: {isDestroyed: () => false, getURL: () => 'https://fixture.invalid/search'}};
  const host = {
    capturePopup: BrowserHost.prototype.capturePopup,
    endPopupCapture: BrowserHost.prototype.endPopupCapture,
    scope: () => scope,
    assertActive: () => {if (job.cancelled) throw failure('TASK_CANCELLED', 'fixture cancelled');},
    open: async () => ({__tabId: 'detail-' + ++nextId, isDestroyed: () => false, webContents: {isDestroyed: () => false, getURL: () => 'https://fixture.invalid/detail'}}),
    navigate: async () => {}, close: () => {},
    requestHumanAction: (_, t) => {scope.pendingHumanAction = {tab_id: t.__tabId};},
    resumeHumanAction: () => {delete scope.pendingHumanAction; host.resumeCount++;},
    resumeCount: 0,
  };
  const runner = new BrowserWorkflowRunner(host, job, () => {});
  const state = {_runtime: {partial: false, reports: {}, page_failures: [], page_failures_truncated: 0}};
  return {host, job, runner, state, tab, scope};
}
function success(result = {}) {return {status: 'success', data: {result}, context: {variables: {}}, error: null};}
(async () => {
  const results = {runtime_hashes: {runner: runnerModule.hash, host: hostModule.hash,
    content: crypto.createHash('sha256').update(content).digest('hex')}, checks: [], blockers: []};
  const sample = setup();
  sample.runner._validateWorkflow(fixture);
  const opened = [];
  const waits = [];
  const operations = [];
  async function simulateProgram(program, context) {
    for (const step of program) {
      if (step.id.startsWith('pacing-index-')) {
        await page.probe.executeStep(step, context, step.id);
      } else if (step.id.startsWith('pacing-')) {
        if (step.op === 'flow.if') {
          const branch = page.probe.evaluateCondition(step.condition, context).matched ? step.then : step.else;
          await simulateProgram(branch, context);
        } else {
          const before = performance.now();
          await page.probe.executeWait(step, context);
          waits.push({id: step.id, planned_ms: step.until.ms, elapsed_ms: performance.now() - before});
        }
      } else if (['page.click', 'page.fill', 'page.press', 'page.extract', 'page.extract_list'].includes(step.op)) {
        operations.push({id: step.id, at: new Date().toISOString()});
      }
      // Existing load waits and conditional page restoration use an already-ready
      // mock page. No production DOM extraction or navigation is performed.
    }
  }
  const started = performance.now();
  page.probe.execution.cancelled = false;
  sample.host.page = async (tab, capability, input) => {
    if (tab === sample.tab) {
      // Page restoration/extraction are transport fixtures. Execute the actual
      // compiled wait with the installed executor, then simulate the final click.
      await simulateProgram(input.program, pageContext(input));
      opened.push({at_ms: performance.now() - started, at: new Date().toISOString()});
      assert.ok(sample.host.popupCapture, 'capture must survive the pre-open wait');
      const capture = sample.host.popupCapture;
      capture.resolve('https://fixture.invalid/detail/' + opened.length);
      sample.host.endPopupCapture();
      return success();
    }
    await simulateProgram(input.program, pageContext(input));
    return success({candidate_ref: 'synthetic-' + opened.length});
  };
  for (const [index, original] of collectors.entries()) {
    const step = structuredClone(original);
    step.items = Array.from({length: index === 0 ? 2 : 1}, (_, n) => ({row_index: n, search_page: 1}));
    await sample.runner._executeTabsForeach(sample.tab, step, fixture, sample.state);
  }
  const intervals = opened.map((x, n) => x.at_ms - (n ? opened[n - 1].at_ms : 0));
  assert.equal(opened.length, 3);
  {
    assert.equal(waits.length, 9);
    assert.equal(operations.length, 9);
    assert.equal(waits.reduce((sum, w) => sum + w.planned_ms, 0), 45000);
    for (const wait of waits) {
      assert.ok(wait.planned_ms >= 4000 && wait.planned_ms <= 6000);
      assert.ok(wait.elapsed_ms >= wait.planned_ms);
    }
    assert.ok(new Set(waits.map(w => w.planned_ms)).size > 1);
  }
  assert.equal(sample.state.details_primary.length, 2);
  assert.equal(sample.state.details_secondary.length, 1);
  results.checks.push({name: 'distributed_atomic_waits', opened, intervals_ms: intervals, waits, operations});

  const cancel = setup();
  let clicks = 0;
  page.probe.execution.cancelled = false;
  cancel.host.page = async (_, __, input) => {
    await simulateProgram(input.program, pageContext(input));
    clicks++;
    return success();
  };
  const timer = setTimeout(() => {cancel.job.cancelled = true; page.probe.execution.cancelled = true;}, 150);
  const cancelStart = performance.now();
  await assert.rejects(cancel.runner._executeTabsForeach(cancel.tab,
    {...collectors[0], items: [{}, {}]}, fixture, cancel.state), /fixture cancelled/);
  clearTimeout(timer);
  assert.equal(clicks, 0);
  results.checks.push({name: 'cancel_during_wait', clicks, elapsed_ms: performance.now() - cancelStart});
  page.probe.execution.cancelled = false;

  const verification = collectors[0].steps[0].program.find(s => s.op === 'page.detect').rules.find(r => r.id.endsWith('-verification'));
  page.document.body.innerText = '请完成验证';
  let human;
  try {await page.probe.executeDetect({rules: [verification]}, pageContext());}
  catch (error) {assert.equal(error.code, 'SECURITY_VERIFICATION_REQUIRED'); human = {
    status: 'human_required', data: error.details, context: {},
    error: {code: error.code, message: error.message, retryable: false}};}
  assert.ok(human);
  results.checks.push({name: 'captcha_detected', code: human.error.code});

  const held = setup();
  let detailExecutions = 0;
  held.host.page = async (_, capability) => {
    if (capability === 'page.status') return {data: {condition: {matched: false}}};
    detailExecutions++;
    return human;
  };
  const stopTimer = setTimeout(() => {held.job.cancelled = true;}, 150);
  await assert.rejects(held.runner._invokePage(held.tab, 'page.execute', {}), /fixture cancelled/);
  clearTimeout(stopTimer);
  assert.equal(detailExecutions, 1);
  assert.equal(held.host.resumeCount, 0);
  results.checks.push({name: 'captcha_present_waits_without_reexecute', detailExecutions});

  const cleared = setup();
  let executions = 0;
  cleared.host.page = async (_, capability) => capability === 'page.status'
    ? {data: {condition: {matched: true}}}
    : (++executions === 1 ? human : success());
  await cleared.runner._invokePage(cleared.tab, 'page.execute', {});
  if (cleared.host.resumeCount > 0) results.blockers.push({
    name: 'captcha_clear_auto_resumes', executions, resumes: cleared.host.resumeCount,
    explanation: 'No explicit user continue event was supplied; installed runner resumed anyway.'});
  const terminal = sample.runner._buildResult(fixture, sample.state, null,
    new Date().toISOString(), human);
  const terminalText = JSON.stringify(terminal);
  if (!terminalText.includes('synthetic-1')) results.blockers.push({
    name: 'completed_details_missing_from_terminal_result',
    completed_in_runtime_context: sample.state.details_primary.length + sample.state.details_secondary.length,
    explanation: 'Terminal human-required payload does not expose details already collected in the workflow context; resumable result retention is not satisfied at this boundary.'});
  results.budgets = {
    builder_default_minutes: (Date.parse(fixture.expires_at) - Date.parse(fixture.created_at)) / 60000,
    detail_wait_budget_ms: fixture.limits.max_tabs * 15000,
    popup_capture_ms: collectors[0].open.timeout_ms,
    host_max_workflow_ms: vm.runInContext('MAX_WORKFLOW_TIMEOUT_MS', runnerModule.context),
  };
  const detailBudget = results.budgets.detail_wait_budget_ms;
  assert.equal(detailBudget, 120000);
  assert.ok(results.budgets.builder_default_minutes * 60000 > detailBudget);
  results.status = results.blockers.length ? 'BLOCKED_RUNTIME' : 'PASS';
  console.log(JSON.stringify(results, null, 2));
  // A detected compatibility blocker is deliberately not a passing exit code.
  if (results.blockers.length) process.exitCode = 2;
})().catch(error => {console.error(error); process.exitCode = 1;});
