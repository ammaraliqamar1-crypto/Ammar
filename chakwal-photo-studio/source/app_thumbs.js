const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const T = JSON.parse(fs.readFileSync('build/templates.json', 'utf8'));
const dir = 'build/thumbs'; fs.mkdirSync(dir, { recursive: true });
const font = (n, f) => `@font-face{font-family:"${n}";src:url(file://${path.resolve('fonts', f)})}`;
const css = font('CPS Display','Marcellus.ttf') + font('CPS Sans','Jost500.ttf') + font('CPS Urdu','Nastaliq600.ttf');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 200, height: 200 } });
  for (const t of T) {
    const k = 120 / Math.max(t.w, t.h), w = Math.round(t.w * k), h = Math.round(t.h * k);
    await p.setViewportSize({ width: 120, height: 120 });
    fs.writeFileSync('build/_t.html', `<style>${css}html,body{margin:0;background:#E9E1D2}svg{position:absolute;left:${(120-w)/2}px;top:${(120-h)/2}px;width:${w}px;height:${h}px}</style>` + t.svg.replace('<svg ', `<svg viewBox="0 0 ${t.w} ${t.h}" `));
    await p.goto('file://' + path.resolve('build/_t.html'));
    await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: `${dir}/${t.id}.jpg`, type: 'jpeg', quality: 80 });
  }
  await b.close();
})();
