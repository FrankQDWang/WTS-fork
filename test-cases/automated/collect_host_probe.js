// Exercise generated conditions and identity lookup in the installed Domi interpreter.
const fs = require('fs');
const vm = require('vm');
const assert = require('assert/strict');
const path = require('path');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const root = process.argv[2];
const sandbox = {console, setTimeout, clearTimeout, URL, structuredClone, crypto: require("crypto").webcrypto};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(root, 'protocol.js'), 'utf8'), sandbox);
vm.runInContext(fs.readFileSync(path.join(root, 'elements.js'), 'utf8'), sandbox);
let source = fs.readFileSync(path.join(root, 'content.js'), 'utf8');
source = source.slice(0, source.indexOf('  window.addEventListener("message"')) +
  'globalThis.probe = {createContext, executeProgram, resolveTemplate};})();';
// Disable only the Electron checkpoint transport; execute the real DSL interpreter.
source = source.replace('await bridgeInput({kind:"checkpoint"}, context, completing);', '');
vm.runInContext(source, sandbox);
const {createContext, executeProgram, resolveTemplate} = sandbox.probe;
function context(values, item = {}) {
  return createContext({input: {variables: values, scope: {item},
    limits: {max_loop_iterations: 30}}, deadline_at: '2100-01-01T00:00:00Z'});
}
(async () => {
  // Mutate one observation at a time: only the identical state may skip restoration.
  for (const [field, value] of [['same', null], ['query', 'other'], ['page', '2'],
                                ['filters', ['3天内活跃']], ['url', 'https://h.liepin.com/other']]) {
    const state = structuredClone(input.snapshot);
    if (field !== 'same') state[field] = value;
    const c = context({search: {list_state: state}});
    const step = {...input.gate,
      then: [{id: 'reuse', op: 'data.set', path: 'outcome', value: 'reuse'}],
      else: [{id: 'restore', op: 'data.set', path: 'outcome', value: 'restore'}]};
    await executeProgram([step], c);
    assert.equal(c.values.outcome, field === 'same' ? 'reuse' : 'restore');
  }
  for (const rows of [[], [{candidate_ref: 'liepin:other0001', row_index: 0}],
    [{candidate_ref: 'liepin:wanted001', row_index: 7}],
    [{candidate_ref: 'liepin:wanted001', row_index: 2}, {candidate_ref: 'liepin:wanted001', row_index: 7}]]) {
    const c = context({collect: {live_cards: rows}}, {candidate_ref: 'liepin:wanted001', row_index: 0});
    let failed = false;
    try { await executeProgram(input.identity, c); } catch (e) {
      assert.equal(e.code, 'WAIT_TIMEOUT', e.stack); failed = true;
    }
    assert.equal(failed, rows.filter(r => r.candidate_ref === 'liepin:wanted001').length !== 1);
    if (!failed) assert.equal(resolveTemplate(input.target, c).within.index, 7);
  }
  console.log('Domi interpreter: 5 page-state cases + 4 candidate-identity cases passed');
})().catch(e => {console.error(e);process.exitCode = 1;});
