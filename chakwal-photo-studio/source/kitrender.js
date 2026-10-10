const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const root = process.argv[2];
const pdfs = { 'album-covers': ['12in','12in'], 'signboard': ['144in','36in'], 'stationery': ['148mm','210mm'] };
const scale = { 'album-covers': 2.5, 'illustrations': 4, 'dp': 1, 'signboard': 2, 'stationery': 3 };
function walk(d) { return fs.readdirSync(d).flatMap(f => { const p = path.join(d,f); return fs.statSync(p).isDirectory() ? walk(p) : [p]; }); }
(async () => {
  const b = await chromium.launch();
  for (const f of walk(root).filter(f => f.endsWith('.svg'))) {
    const dir = path.basename(path.dirname(f));
    const s = fs.readFileSync(f,'utf8');
    const [w,h] = s.match(/viewBox="0 0 ([\d.]+) ([\d.]+)"/).slice(1).map(Number);
    const ds = scale[dir] || 1;
    const p = await b.newPage({ viewport:{width:Math.round(w),height:Math.round(h)}, deviceScaleFactor: ds });
    await p.setContent(`<style>@page{margin:0}html,body{margin:0;background:transparent}body>svg{display:block;width:100vw;height:100vh}</style>`+s.replace(/width="[^"]*" height="[^"]*"/,''));
    await p.screenshot({ path: f.replace('.svg','.png'), omitBackground: true });
    if (pdfs[dir]) await p.pdf({ path: f.replace('.svg','.pdf'), width: pdfs[dir][0], height: pdfs[dir][1], printBackground: true, pageRanges: '1' });
    await p.close();
  }
  await b.close();
})();
