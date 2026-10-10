const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 794, height: 1123 }, deviceScaleFactor: 2 });
  await p.goto('file://' + path.resolve('guide/guide.html')); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(500);
  await p.pdf({ path: 'guide/Studio-Designer-Guide-Urdu.pdf', format: 'A4', printBackground: true, preferCSSPageSize: true });
  const pages = await p.$$('.page');
  for (let i = 0; i < pages.length; i++) await pages[i].screenshot({ path: `guide/guide-page-${i + 1}.png` });
  const over = await p.evaluate(() => [...document.querySelectorAll('.page')].map((pg, i) => { const f = pg.querySelector('.foot').getBoundingClientRect().top; const last = [...pg.children].filter(c => !c.classList.contains('foot')).pop().getBoundingClientRect().bottom; return [i + 1, Math.round(f - last)]; }));
  console.log('gap above footer (px):', JSON.stringify(over));
  await b.close();
})();
