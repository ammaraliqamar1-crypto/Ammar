'use strict';
// Online provider. Neutral message format -> Anthropic Messages API.
// Neutral: {role:'user'|'assistant'|'tool', content, toolCalls?:[{id,name,args}], toolCallId?}

function toAnthropicMessages(messages) {
  const out = [];
  for (const m of messages) {
    if (m.role === 'user') {
      out.push({ role: 'user', content: m.content });
    } else if (m.role === 'assistant') {
      const blocks = [];
      if (m.content) blocks.push({ type: 'text', text: m.content });
      for (const c of m.toolCalls || []) {
        blocks.push({ type: 'tool_use', id: c.id, name: c.name, input: c.args || {} });
      }
      out.push({ role: 'assistant', content: blocks });
    } else if (m.role === 'tool') {
      const block = { type: 'tool_result', tool_use_id: m.toolCallId, content: String(m.content) };
      const last = out[out.length - 1];
      if (last && last.role === 'user' && Array.isArray(last.content)) last.content.push(block);
      else out.push({ role: 'user', content: [block] });
    }
  }
  return out;
}

function createAnthropic({ apiKey, model, fetchImpl = fetch, baseUrl = 'https://api.anthropic.com' }) {
  return {
    name: 'anthropic',
    async chat({ system, messages, tools, signal }) {
      if (!apiKey) throw new Error('Anthropic API key is not set');
      const body = {
        model,
        max_tokens: 4096,
        system,
        messages: toAnthropicMessages(messages),
      };
      if (tools && tools.length) {
        body.tools = tools.map((t) => ({
          name: t.name,
          description: t.description,
          input_schema: t.parameters || { type: 'object', properties: {} },
        }));
      }
      const res = await fetchImpl(`${baseUrl}/v1/messages`, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
        },
        body: JSON.stringify(body),
        signal,
      });
      if (!res.ok) throw new Error(`Anthropic ${res.status}: ${await res.text()}`);
      const data = await res.json();
      let content = '';
      const toolCalls = [];
      for (const b of data.content || []) {
        if (b.type === 'text') content += b.text;
        else if (b.type === 'tool_use') toolCalls.push({ id: b.id, name: b.name, args: b.input });
      }
      return { content, toolCalls };
    },
  };
}

module.exports = { createAnthropic, toAnthropicMessages };
