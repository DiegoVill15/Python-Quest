// Ejecutar: node tests/test_ai_models.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class Element {
  constructor() { this.value = ''; this.children = []; this.handlers = {}; this.hidden = false; }
  addEventListener(event, handler) { this.handlers[event] = handler; }
  replaceChildren(...children) { this.children = children; this.value = children[0]?.value || ''; }
  append(child) { this.children.push(child); }
  showModal() { this.open = true; }
}
const elements = new Map();
const $ = (id) => {
  if (!elements.has(id)) elements.set(id, new Element());
  return elements.get(id);
};
const pending = [];
const sandbox = { $, el: (tag, cls, text) => Object.assign(new Element(), { textContent: text }),
  api: (path) => new Promise((resolve, reject) => pending.push({ path, resolve, reject })) };
const source = fs.readFileSync('static/app.js', 'utf8');
vm.createContext(sandbox);
vm.runInContext(source.slice(source.indexOf('$("ai-open").addEventListener'), source.indexOf('$("ai-provider").addEventListener')), sandbox);
const options = () => $('ai-model').children.map((option) => option.value);
const tick = () => new Promise(setImmediate);

(async () => {
  vm.runInContext('renderAi({connections:[{id:"codex",label:"Codex"},{id:"claude",label:"Claude"}],selection:{id:"codex",model:"saved"}})', sandbox);
  assert.equal(pending.length, 0); // No consulta mientras la ventana está cerrada.
  $('ai-open').handlers.click();
  assert.equal(pending.length, 1);
  assert.equal($('ai-model').disabled, true);
  pending.shift().resolve({ models: ['saved', 'other'] });
  await tick();
  assert.equal($('ai-model').value, 'saved');
  assert.deepEqual(options(), ['saved', 'other', '']);
  $('ai-model').value = 'other';
  $('ai-model').handlers.change();
  assert.deepEqual(options(), ['saved', 'other', '']); // Elegir nunca filtra la lista.
  assert.equal($('ai-model-manual').hidden, true);
  $('ai-model').value = '';
  $('ai-model').handlers.change();
  assert.equal($('ai-model-manual').hidden, false);

  $('ai-connection').value = 'claude';
  $('ai-connection').handlers.change();
  const stale = pending.shift();
  assert.match(stale.path, /claude\/models$/);
  $('ai-connection').value = 'codex';
  $('ai-connection').handlers.change();
  pending.shift().resolve({ models: ['saved', 'fresh'] });
  await tick();
  stale.reject(new Error('Respuesta antigua'));
  await tick();
  assert.deepEqual(options(), ['saved', 'fresh', '']);
  assert.equal($('ai-model').disabled, false);
  assert.doesNotMatch($('ai-help').textContent, /antigua/);

  $('ai-connection').value = 'claude';
  $('ai-connection').handlers.change();
  pending.shift().resolve({ models: [] });
  await tick();
  assert.deepEqual(options(), ['']);
  assert.equal($('ai-model-manual').hidden, false);
  $('ai-connection').handlers.change();
  pending.shift().reject(new Error('Sesión no disponible'));
  await tick();
  assert.equal($('ai-save').disabled, false);
  assert.equal($('ai-model-manual').hidden, false);
  assert.match($('ai-help').textContent, /Sesión no disponible/);
  console.log('OK: carga automática, lista persistente, entrada manual y respuestas fuera de orden.');
})().catch((error) => { console.error(error); process.exitCode = 1; });
