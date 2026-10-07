'use strict';
const test = require('node:test');
const assert = require('node:assert');
const { runTurn } = require('../src/core/agent');
const { createRouter } = require('../src/core/llm/router');
const { wrapTools, flushQueue } = require('../src/core/offline');
const { createJsonStore } = require('../src/core/store');
const { createDemoConnector } = require('../src/core/connectors/demo');
const { toAnthropicMessages } = require('../src/core/llm/anthropic');

// scripted fake provider
const fake = (name, replies) => ({ name, chat: async () => replies.shift() });

test('read tool runs, write tool needs confirmation', async () => {
  const tools = await createDemoConnector().loadTools();
  const provider = fake('p', [
    { content: '', toolCalls: [{ id: '1', name: 'list_inquiries', args: {} }] },
    { content: '', toolCalls: [{ id: '2', name: 'update_inquiry_status', args: { id: 'INQ-001', status: 'Quoted' } }] },
    { content: 'done', toolCalls: [] },
  ]);
  const router = createRouter({ online: provider, offline: null, mode: 'online' });
  let asked = 0;
  const out = await runTurn({ router, tools, history: [], userText: 'x', confirm: async () => { asked++; return false; } });
  assert.equal(out, 'done');
  assert.equal(asked, 1);
  assert.equal((await tools[0].run({ status: 'Quoted' })).length, 1); // INQ-001 unchanged because declined
});

test('auto mode falls back to offline when online is down', async () => {
  const online = { name: 'on', chat: async () => { throw new Error('net'); } };
  const offline = fake('off', [{ content: 'hi', toolCalls: [] }]);
  const router = createRouter({ online, offline, mode: 'auto', probe: async () => true });
  const r = await router.chat({ system: '', messages: [], tools: [] });
  assert.equal(r.provider, 'off');
});

test('offline cache serves reads; writes queue and flush', async () => {
  const store = createJsonStore(null);
  let up = true;
  const netErr = () => new Error('ECONNREFUSED');
  const raw = [
    { name: 'r', risk: 'read', run: async () => { if (!up) throw netErr(); return [1, 2]; } },
    { name: 'w', risk: 'write', run: async () => { if (!up) throw netErr(); return 'ok'; } },
  ];
  const tools = wrapTools(raw, store);
  assert.deepEqual(await tools[0].run({}), [1, 2]);
  up = false;
  const cached = await tools[0].run({});
  assert.equal(cached.offline, true);
  assert.deepEqual(cached.data, [1, 2]);
  assert.equal((await tools[1].run({ a: 1 })).queued, true);
  up = true;
  assert.deepEqual(await flushQueue(tools, store), { done: 1, remaining: 0 });
});

test('anthropic message conversion groups tool results', () => {
  const m = toAnthropicMessages([
    { role: 'user', content: 'q' },
    { role: 'assistant', content: '', toolCalls: [{ id: 'a', name: 't', args: {} }, { id: 'b', name: 't', args: {} }] },
    { role: 'tool', toolCallId: 'a', content: 'r1' },
    { role: 'tool', toolCallId: 'b', content: 'r2' },
  ]);
  assert.equal(m.length, 3);
  assert.equal(m[2].content.length, 2);
});
