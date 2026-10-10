const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path');
const mark = async (p, items) => p.evaluate(items => {
  document.querySelectorAll('.gmark').forEach(e => e.remove());
  for (const [sel, n, pos] of items) {
    const el = typeof sel === 'string' ? document.querySelector(sel) : null; if (!el) continue;
    const r = el.getBoundingClientRect();
    const box = document.createElement('div'); box.className = 'gmark';
    Object.assign(box.style, { position: 'fixed', left: r.left - 4 + 'px', top: r.top - 4 + 'px', width: r.width + 8 + 'px', height: r.height + 8 + 'px', border: '3px solid #C0392B', borderRadius: '10px', zIndex: 99, pointerEvents: 'none' });
    const b = document.createElement('div'); b.className = 'gmark'; b.textContent = n;
    const L = Math.max(4, Math.min(innerWidth - 40, pos === 'below' ? r.left + r.width / 2 - 17 : pos === 'left' ? r.left - 26 : r.right - 22)), T = pos === 'below' ? r.bottom + 8 : pos === 'left' ? r.top + r.height / 2 - 17 : r.top - 14;
    Object.assign(b.style, { position: 'fixed', left: L + 'px', top: Math.max(4, T) + 'px', width: '34px', height: '34px', borderRadius: '50%', background: '#C0392B', color: '#fff', font: '700 18px Arial', display: 'grid', placeItems: 'center', zIndex: 100, boxShadow: '0 2px 6px rgba(0,0,0,.4)' });
    document.body.append(box, b);
  }
}, items);
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1400, height: 900 }, deviceScaleFactor: 1.5 });
  const p = await ctx.newPage();
  await p.goto('file://' + path.resolve('appout/studio-designer.html')); await p.waitForTimeout(1500);
  // overview
  await mark(p, [['.rail', '1', 'left'], ['#stage svg', '2'], ['.panel', '3'], ['.bar .actions', '4']]);
  await p.screenshot({ path: 'guide/shots/overview.png' });
  // add photo
  await mark(p, [['.slot .btn.primary', '1'], ['#stage svg [data-slot]', '2']]);
  await p.screenshot({ path: 'guide/shots/add-photo.png', clip: { x: 250, y: 60, width: 1150, height: 840 } });
  const [fc] = await Promise.all([p.waitForEvent('filechooser'), p.click('text=Add photo')]);
  await fc.setFiles('guide/sample.jpg'); await p.waitForTimeout(700);
  await mark(p, [['#stage svg [data-slot]', '1'], ['.slot input[type=range]', '2'], ['.slot .btn:not(.primary)', '3']]);
  await p.screenshot({ path: 'guide/shots/adjust-photo.png', clip: { x: 250, y: 60, width: 1150, height: 840 } });
  // text on album
  await p.click('text=Wedding album'); await p.waitForTimeout(400);
  await mark(p, [['.fields', '1'], ['#stage svg', '2', 'left']]);
  await p.screenshot({ path: 'guide/shots/text.png', clip: { x: 250, y: 60, width: 1150, height: 840 } });
  // export
  await mark(p, [['.grid2 .btn:nth-child(1)', '1'], ['.grid2 .btn:nth-child(2)', '2'], ['.grid2 .btn:nth-child(3)', '3'], ['.grid2 .btn:nth-child(4)', '4']]);
  const ex = await p.locator('.sec:has(.grid2)').boundingBox();
  await p.screenshot({ path: 'guide/shots/export.png', clip: { x: ex.x - 30, y: ex.y - 30, width: ex.width + 60, height: ex.height + 60 } });
  await mark(p, [['#btnOpen', '1', 'below'], ['#btnSave', '2', 'below'], ['#btnAll', '3', 'below']]);
  await p.screenshot({ path: 'guide/shots/project.png', clip: { x: 880, y: 0, width: 520, height: 112 } });
  await b.close();
})();
