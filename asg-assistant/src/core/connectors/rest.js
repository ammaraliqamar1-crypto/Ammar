'use strict';
// Generic connector for the ASG server. The ASG system exposes:
//   GET  {base}/assistant/manifest  -> { name, tools: [{name, description, parameters, risk, method, path}] }
// and each tool is invoked with its declared method/path (see docs/ASG-PLUGIN-API.md).

function createRestConnector({ baseUrl, token, fetchImpl = fetch, timeoutMs = 8000 }) {
  const base = baseUrl.replace(/\/+$/, '');
  const headers = { 'content-type': 'application/json' };
  if (token) headers.authorization = `Bearer ${token}`;

  async function call(method, path, args) {
    let url = base + path;
    const init = { method, headers, signal: AbortSignal.timeout(timeoutMs) };
    if (method === 'GET' || method === 'DELETE') {
      const qs = new URLSearchParams();
      for (const [k, v] of Object.entries(args || {})) if (v != null) qs.set(k, String(v));
      if ([...qs].length) url += (url.includes('?') ? '&' : '?') + qs;
    } else {
      init.body = JSON.stringify(args || {});
    }
    const res = await fetchImpl(url, init);
    if (!res.ok) {
      const err = new Error(`ASG ${res.status}: ${await res.text()}`);
      err.httpStatus = res.status; // server answered: not a connectivity failure
      throw err;
    }
    const text = await res.text();
    try { return JSON.parse(text); } catch { return text; }
  }

  return {
    id: 'asg-rest',
    async loadTools() {
      const manifest = await call('GET', '/assistant/manifest');
      return (manifest.tools || []).map((t) => ({
        name: t.name,
        description: t.description,
        parameters: t.parameters,
        risk: t.risk === 'write' ? 'write' : 'read',
        run: (args) => call((t.method || 'GET').toUpperCase(), t.path, args),
      }));
    },
    async ping() {
      try { await call('GET', '/assistant/manifest'); return true; } catch { return false; }
    },
  };
}

module.exports = { createRestConnector };
