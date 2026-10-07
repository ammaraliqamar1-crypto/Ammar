'use strict';
const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('asg', {
  getSettings: () => ipcRenderer.invoke('settings:get'),
  setSettings: (s) => ipcRenderer.invoke('settings:set', s),
  send: (t) => ipcRenderer.invoke('chat:send', t),
  confirm: (id, ok) => ipcRenderer.invoke('chat:confirm', { id, ok }),
  clear: () => ipcRenderer.invoke('chat:clear'),
  status: () => ipcRenderer.invoke('status:get'),
  onEvent: (cb) => ipcRenderer.on('chat:event', (_e, p) => cb(p)),
  onConfirm: (cb) => ipcRenderer.on('chat:confirm', (_e, p) => cb(p)),
  onStatus: (cb) => ipcRenderer.on('status', (_e, p) => cb(p)),
});
