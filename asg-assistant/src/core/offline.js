'use strict';
// Offline resilience for ASG tools.
//  - read tools: cache last good result; when the server is unreachable serve the cached copy (flagged).
//  - write tools: when the server is unreachable, queue and replay later via flushQueue().

const { createJsonStore } = require('./store');

function isNetworkError(err) {
  return !err.httpStatus; // HTTP errors carry httpStatus; everything else is connectivity/timeout
}

function wrapTools(tools, store) {
  return tools.map((t) => ({
    ...t,
    async run(args) {
      const key = `${t.name}:${JSON.stringify(args || {})}`;
      try {
        const result = await t.run(args);
        if (t.risk === 'read') store.set(`cache.${key}`, { at: new Date().toISOString(), result });
        return result;
      } catch (err) {
        if (!isNetworkError(err)) throw err;
        if (t.risk === 'read') {
          const hit = store.get(`cache.${key}`);
          if (hit) return { offline: true, cachedAt: hit.at, data: hit.result };
          throw new Error('ASG server unreachable and no cached data for this request');
        }
        const q = store.get('queue') || [];
        q.push({ tool: t.name, args, queuedAt: new Date().toISOString() });
        store.set('queue', q);
        return { queued: true, message: 'ASG server unreachable. Action queued and will run when it is back.' };
      }
    },
  }));
}

async function flushQueue(tools, store) {
  const q = store.get('queue') || [];
  const remaining = [];
  let done = 0;
  for (const item of q) {
    const tool = tools.find((t) => t.name === item.tool);
    try {
      await tool.run(item.args);
      done++;
    } catch (err) {
      if (isNetworkError(err)) remaining.push(item);
      // HTTP/logic errors are dropped from the queue to avoid infinite retry
    }
  }
  store.set('queue', remaining);
  return { done, remaining: remaining.length };
}

module.exports = { wrapTools, flushQueue, isNetworkError, createJsonStore };
