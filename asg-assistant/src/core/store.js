'use strict';
const fs = require('fs');
const path = require('path');

// Tiny JSON file store. Keys are flat strings; values any JSON. Pass file=null for in-memory.
function createJsonStore(file) {
  let data = {};
  if (file) {
    try { data = JSON.parse(fs.readFileSync(file, 'utf8')); } catch { data = {}; }
  }
  const persist = () => {
    if (!file) return;
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, JSON.stringify(data));
  };
  return {
    get: (k) => data[k],
    set: (k, v) => { data[k] = v; persist(); },
    all: () => data,
  };
}
module.exports = { createJsonStore };
