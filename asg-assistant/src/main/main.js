'use strict';
const { app, BrowserWindow, ipcMain, safeStorage } = require('electron');
const path = require('path');
const { createJsonStore } = require('../core/store');
const { createAnthropic } = require('../core/llm/anthropic');
const { createOllama } = require('../core/llm/ollama');
const { createRouter, isOnline } = require('../core/llm/router');
const { createRestConnector } = require('../core/connectors/rest');
const { createDemoConnector } = require('../core/connectors/demo');
const { wrapTools, flushQueue } = require('../core/offline');
const { runTurn } = require('../core/agent');

const DEFAULTS = {
  mode: 'auto',
  anthropicModel: 'claude-sonnet-5-5',
  ollamaModel: 'llama3.1',
  ollamaUrl: 'http://127.0.0.1:11434',
  asgUrl: '',
  asgToken: '',
};

let win, settings, cache, history = [], tools = [], pendingConfirms = new Map();

const enc = (s) => (s && safeStorage.isEncryptionAvailable() ? safeStorage.encryptString(s).toString('base64') : s || '');
const dec = (s) => {
  if (!s) return '';
  try { return safeStorage.isEncryptionAvailable() ? safeStorage.decryptString(Buffer.from(s, 'base64')) : s; } catch { return ''; }
};
const cfg = () => ({ ...DEFAULTS, ...(settings.get('cfg') || {}) });
const secret = (k) => dec(settings.get(`secret.${k}`));

async function loadTools() {
  const c = cfg();
  const connector = c.asgUrl
    ? createRestConnector({ baseUrl: c.asgUrl, token: secret('asgToken') })
    : createDemoConnector();
  let raw;
  try {
    raw = await connector.loadTools();
    cache.set('tools.manifest', raw.map(({ name, description, parameters, risk }) => ({ name, description, parameters, risk })));
  } catch {
    // Offline at startup: rebuild tool stubs from the cached manifest; wrapTools serves cache / queues writes.
    const m = cache.get('tools.manifest') || [];
    raw = m.map((t) => ({ ...t, run: async () => { throw new Error('ASG server unreachable'); } }));
  }
  tools = wrapTools(raw, cache);
  return tools;
}

function buildRouter() {
  const c = cfg();
  const key = secret('anthropicKey');
  return createRouter({
    mode: c.mode,
    online: key ? createAnthropic({ apiKey: key, model: c.anthropicModel }) : null,
    offline: createOllama({ model: c.ollamaModel, baseUrl: c.ollamaUrl }),
  });
}

function send(ch, payload) { if (win && !win.isDestroyed()) win.webContents.send(ch, payload); }

app.whenReady().then(async () => {
  const dir = app.getPath('userData');
  settings = createJsonStore(path.join(dir, 'settings.json'));
  cache = createJsonStore(path.join(dir, 'cache.json'));
  await loadTools();

  win = new BrowserWindow({
    width: 1100, height: 760, title: 'ASG Assistant',
    webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, nodeIntegration: false, sandbox: true },
  });
  win.removeMenu();
  win.loadFile(path.join(__dirname, '../renderer/index.html'));

  // Replay queued offline actions whenever the server comes back.
  setInterval(async () => {
    if ((cache.get('queue') || []).length && (await isOnline(fetch, cfg().asgUrl || 'https://api.anthropic.com'))) {
      const r = await flushQueue(tools, cache);
      if (r.done) send('status', { text: `Synced ${r.done} queued action(s)` });
    }
  }, 30000);
});

ipcMain.handle('settings:get', () => ({
  ...cfg(), asgToken: '', hasAnthropicKey: !!secret('anthropicKey'), hasAsgToken: !!secret('asgToken'),
}));

ipcMain.handle('settings:set', async (_e, s) => {
  const { anthropicKey, asgToken, ...rest } = s;
  settings.set('cfg', { ...cfg(), ...rest });
  if (anthropicKey) settings.set('secret.anthropicKey', enc(anthropicKey));
  if (asgToken) settings.set('secret.asgToken', enc(asgToken));
  await loadTools();
  return true;
});

ipcMain.handle('chat:send', async (_e, text) => {
  try {
    await runTurn({
      router: buildRouter(), tools, history, userText: text,
      onEvent: (ev) => send('chat:event', ev),
      confirm: ({ name, args }) => new Promise((resolve) => {
        const id = `${Date.now()}-${Math.random()}`;
        pendingConfirms.set(id, resolve);
        send('chat:confirm', { id, name, args });
      }),
    });
  } catch (err) {
    send('chat:event', { type: 'error', text: err.message });
  }
});

ipcMain.handle('chat:confirm', (_e, { id, ok }) => {
  const r = pendingConfirms.get(id);
  if (r) { pendingConfirms.delete(id); r(!!ok); }
});

ipcMain.handle('chat:clear', () => { history = []; });
ipcMain.handle('status:get', async () => ({
  tools: tools.length, queued: (cache.get('queue') || []).length, online: await isOnline(),
}));

app.on('window-all-closed', () => app.quit());
