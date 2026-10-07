'use strict';
// Chat + tool loop. Read tools run immediately; write tools need explicit user confirmation.

const SYSTEM = `You are ASG Assistant for Saeed Al Siraj Glass & Aluminium Works (Al Siraj Group), UAE.
You help staff query company information and perform actions in the ASG system through tools.
Rules:
- Use tools to get real data; never invent figures, inquiry numbers or statuses.
- Before any change, state clearly what you will do; the user must confirm write actions.
- Be concise and professional. Reply in the language the user writes in (English, Urdu or Roman Urdu).`;

async function runTurn({ router, tools, history, userText, confirm, onEvent = () => {}, maxSteps = 8, system = SYSTEM }) {
  history.push({ role: 'user', content: userText });
  const toolDefs = tools.map(({ name, description, parameters }) => ({ name, description, parameters }));

  for (let step = 0; step < maxSteps; step++) {
    const reply = await router.chat({ system, messages: history, tools: toolDefs });
    onEvent({ type: 'provider', provider: reply.provider });
    history.push({ role: 'assistant', content: reply.content, toolCalls: reply.toolCalls });

    if (!reply.toolCalls.length) {
      onEvent({ type: 'final', text: reply.content });
      return reply.content;
    }
    for (const call of reply.toolCalls) {
      const tool = tools.find((t) => t.name === call.name);
      let result;
      if (!tool) {
        result = `Error: unknown tool ${call.name}`;
      } else {
        onEvent({ type: 'tool', name: call.name, args: call.args, risk: tool.risk });
        let allowed = true;
        if (tool.risk === 'write') allowed = await confirm({ name: call.name, args: call.args });
        if (!allowed) result = 'The user declined this action.';
        else {
          try { result = JSON.stringify(await tool.run(call.args)); }
          catch (err) { result = `Error: ${err.message}`; }
        }
      }
      history.push({ role: 'tool', toolCallId: call.id, content: result });
      onEvent({ type: 'tool_result', name: call.name, result });
    }
  }
  const text = 'Stopped: too many tool steps.';
  onEvent({ type: 'final', text });
  return text;
}

module.exports = { runTurn, SYSTEM };
