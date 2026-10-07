'use strict';
const $ = (id) => document.getElementById(id);
const log = $('log');
let busy = false;

function add(cls, text) {
  const d = document.createElement('div');
  d.className = `msg ${cls}`;
  d.textContent = text;
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
  return d;
}

async function refreshStatus() {
  const s = await window.asg.status();
  $('badge').textContent = s.online ? 'Online' : 'Offline';
  $('info').textContent = `${s.tools} ASG tools` + (s.queued ? ` · ${s.queued} queued` : '');
}

$('form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = $('input').value.trim();
  if (!text || busy) return;
  $('input').value = '';
  add('user', text);
  busy = true;
  const wait = add('tool', 'Thinking…');
  await window.asg.send(text);
  wait.remove();
  busy = false;
  refreshStatus();
});
$('input').addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); $('form').requestSubmit(); }
});

window.asg.onEvent((ev) => {
  if (ev.type === 'tool') add('tool', `▶ ${ev.name}(${JSON.stringify(ev.args)})`);
  else if (ev.type === 'tool_result') add('tool', `◀ ${ev.result.slice(0, 300)}`);
  else if (ev.type === 'final') add('bot', ev.text);
  else if (ev.type === 'error') add('error', ev.text);
});
window.asg.onStatus((s) => add('tool', s.text));

let pending = null;
window.asg.onConfirm((c) => {
  pending = c.id;
  $('confirmText').textContent = `Approve action "${c.name}" with ${JSON.stringify(c.args)}?`;
  $('confirm').hidden = false;
});
for (const [id, ok] of [['yes', true], ['no', false]]) {
  $(id).onclick = () => { $('confirm').hidden = true; window.asg.confirm(pending, ok); };
}

$('clear').onclick = () => { window.asg.clear(); log.textContent = ''; };

const fields = ['mode', 'anthropicModel', 'ollamaUrl', 'ollamaModel', 'asgUrl'];
$('openSettings').onclick = async () => {
  const s = await window.asg.getSettings();
  for (const f of fields) $(f).value = s[f] || '';
  $('settings').showModal();
};
$('closeSettings').onclick = () => $('settings').close();
$('save').onclick = async () => {
  const s = {};
  for (const f of fields) s[f] = $(f).value.trim();
  if ($('anthropicKey').value) s.anthropicKey = $('anthropicKey').value;
  if ($('asgToken').value) s.asgToken = $('asgToken').value;
  await window.asg.setSettings(s);
  $('anthropicKey').value = $('asgToken').value = '';
  $('settings').close();
  refreshStatus();
};

refreshStatus();
setInterval(refreshStatus, 15000);
