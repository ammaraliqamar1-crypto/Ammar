'use strict';
// Picks online (Claude) or offline (Ollama) per request.
// mode: 'auto' | 'online' | 'offline'

async function isOnline(fetchImpl = fetch, url = 'https://api.anthropic.com') {
  try {
    await fetchImpl(url, { method: 'HEAD', signal: AbortSignal.timeout(2500) });
    return true; // any HTTP response means we have a route
  } catch { return false; }
}

function createRouter({ online, offline, mode = 'auto', probe = isOnline }) {
  return {
    async pick() {
      if (mode === 'offline') return offline;
      if (mode === 'online') return online;
      return (online && (await probe())) ? online : offline;
    },
    // Try preferred provider, fall back to the other on network failure.
    async chat(req) {
      const primary = await this.pick();
      const secondary = primary === online ? offline : online;
      try {
        return { provider: primary.name, ...(await primary.chat(req)) };
      } catch (err) {
        if (mode !== 'auto' || !secondary) throw err;
        return { provider: secondary.name, ...(await secondary.chat(req)) };
      }
    },
  };
}

module.exports = { createRouter, isOnline };
