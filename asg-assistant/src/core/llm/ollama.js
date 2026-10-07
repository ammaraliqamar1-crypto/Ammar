'use strict';
// Offline provider: local Ollama server (default http://127.0.0.1:11434).

function toOllamaMessages(system, messages) {
  const out = [{ role: 'system', content: system }];
  for (const m of messages) {
    if (m.role === 'user') out.push({ role: 'user', content: m.content });
    else if (m.role === 'assistant') {
      const msg = { role: 'assistant', content: m.content || '' };
      if (m.toolCalls && m.toolCalls.length) {
        msg.tool_calls = m.toolCalls.map((c) => ({ function: { name: c.name, arguments: c.args || {} } }));
      }
      out.push(msg);
    } else if (m.role === 'tool') out.push({ role: 'tool', content: String(m.content) });
  }
  return out;
}

function createOllama({ model, baseUrl = 'http://127.0.0.1:11434', fetchImpl = fetch }) {
  return {
    name: 'ollama',
    async chat({ system, messages, tools, signal }) {
      const body = { model, stream: false, messages: toOllamaMessages(system, messages) };
      if (tools && tools.length) {
        body.tools = tools.map((t) => ({
          type: 'function',
          function: { name: t.name, description: t.description, parameters: t.parameters || { type: 'object', properties: {} } },
        }));
      }
      const res = await fetchImpl(`${baseUrl}/api/chat`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(body),
        signal,
      });
      if (!res.ok) throw new Error(`Ollama ${res.status}: ${await res.text()}`);
      const data = await res.json();
      const msg = data.message || {};
      const toolCalls = (msg.tool_calls || []).map((c, i) => ({
        id: `ollama_${Date.now()}_${i}`,
        name: c.function.name,
        args: c.function.arguments || {},
      }));
      return { content: msg.content || '', toolCalls };
    },
    async isUp() {
      try {
        const r = await fetchImpl(`${baseUrl}/api/tags`, { signal: AbortSignal.timeout(2000) });
        return r.ok;
      } catch { return false; }
    },
  };
}

module.exports = { createOllama, toOllamaMessages };
