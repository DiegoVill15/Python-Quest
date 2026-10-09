const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class Element {
  constructor() { this.children = []; this.handlers = {}; this.hidden = false; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  addEventListener(event, handler) { this.handlers[event] = handler; }
  scrollIntoView() { this.scrolled = true; }
}
const elements = new Map();
const $ = (id) => {
  if (!elements.has(id)) elements.set(id, new Element());
  return elements.get(id);
};
const challenge = (id, canSubmit) => ({ id, can_submit: canSubmit, world_id: 'fundamentos',
  title: `Misión ${id}`, stage: 1, total_stages: 5, focus: 'entrada', story: 'Una misión.',
  objective: 'Lee un número.', input_format: 'Un entero.', output_format: 'El doble.',
  rules: [], examples: [{ input: '2\n', expected: '4\n' }], hint: 'Usa el dato de entrada.' });
const challenges = { active: challenge('active', true), archived: challenge('archived', false) };
const requests = [];
let code;
const sandbox = { $, active: null, worlds: [{ id: 'fundamentos', name: 'Aldea Inicial' }],
  el: (tag, cls, text) => Object.assign(new Element(), { textContent: text }),
  plainFeedback: (value) => value || '', setCode: (value) => { code = value; },
  localStorage: { getItem: () => 'print(4)' },
  api: async (path) => { requests.push(path); return challenges[path.split('/').pop()]; },
  notice: (message) => { throw new Error(message); } };
const source = fs.readFileSync('static/app.js', 'utf8');
const recentSource = `{${source.slice(source.indexOf('  const recent = $("recent");'), source.indexOf('  const trophies = $("trophies");'))}}`;
vm.createContext(sandbox);
vm.runInContext(source.slice(source.indexOf('function missionSection('), source.indexOf('function setCode(')), sandbox);
vm.runInContext(source.slice(source.indexOf('function showChallenge('), source.indexOf('async function refresh(')), sandbox);
vm.runInContext(source.slice(source.indexOf('async function openChallenge('), source.indexOf('async function resetWorld(')), sandbox);

(async () => {
  sandbox.data = { recent: [challenges.active, challenges.archived] };
  vm.runInContext(recentSource, sandbox);
  const [activeRow, archivedRow] = $('recent').children;
  assert.equal(activeRow.children[2].textContent, 'Continuar →');
  assert.equal(archivedRow.children[2].textContent, 'Ver archivo →');
  await archivedRow.handlers.click();
  assert.equal($('quest-title').textContent, 'Misión archived');
  assert.equal($('quest-badge').textContent, 'ARCHIVO');
  assert.equal($('quest-panel').hidden, false);
  assert.equal($('quest-panel').scrolled, true);
  assert.equal($('archive-note').hidden, false);
  assert.equal($('submit-button').disabled, true);
  assert.equal($('run-button').disabled, true);
  assert.equal($('examples').children[0].children.length, 5);
  await activeRow.handlers.click();
  assert.equal($('quest-title').textContent, 'Misión active');
  assert.equal($('archive-note').hidden, true);
  assert.equal($('submit-button').disabled, false);
  assert.equal(code, 'print(4)');
  assert.equal($('examples').children[0].children.length, 6);
  assert.deepEqual(requests, ['/api/challenges/archived', '/api/challenges/active']);
  sandbox.data = { recent: [] };
  vm.runInContext(recentSource, sandbox);
  assert.equal($('recent').children[0].textContent, 'Tu historia comienza con la primera misión.');
  console.log('OK: misiones recientes abren el archivo o recuperan el borrador activo.');
})().catch((error) => { console.error(error); process.exitCode = 1; });
