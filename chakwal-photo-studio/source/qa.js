// QA: (1) nothing painted outside the canvas in any SVG deliverable,
//     (2) in live-text templates, no text outside canvas and no two text lines overlapping.
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const walk = d => fs.readdirSync(d).flatMap(f => { const p = path.join(d, f); return fs.statSync(p).isDirectory() ? walk(p) : [p]; });
const font = (n, f) => `@font-face{font-family:"${n}";src:url(file://${path.resolve('fonts', f)})}`;
const css = font('CPS Display', 'Marcellus.ttf') + font('CPS Sans', 'Jost500.ttf') + font('CPS Urdu', 'Nastaliq600.ttf');
const probe = () => {
  const svg = document.querySelector('svg');
  const [, , W, H] = svg.getAttribute('viewBox').split(/\s+/).map(Number);
  const root = svg.getScreenCTM().inverse();
  const box = el => { const b = el.getBBox(), m = root.multiply(el.getScreenCTM());
    const pts = [[b.x, b.y], [b.x + b.width, b.y], [b.x, b.y + b.height], [b.x + b.width, b.y + b.height]].map(([x, y]) => [m.a * x + m.c * y + m.e, m.b * x + m.d * y + m.f]);
    const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
    return { x0: Math.min(...xs), y0: Math.min(...ys), x1: Math.max(...xs), y1: Math.max(...ys) }; };
  const out = [], texts = [];
  for (const el of svg.querySelectorAll('path,text,circle,rect,polygon,line,image,ellipse')) {
    if (el.closest('clipPath,defs,linearGradient,radialGradient')) continue;
    if (el.parentElement.closest('[clip-path]') && !el.hasAttribute('clip-path')) continue;
    if (el.closest('svg') !== svg) continue;
    const b = box(el), tol = 0.5;
    if (b.x1 - b.x0 < 0.01 && b.y1 - b.y0 < 0.01) continue;
    if (b.x0 < -tol || b.y0 < -tol || b.x1 > W + tol || b.y1 > H + tol)
      out.push(`outside canvas: <${el.tagName}> ${(el.textContent || '').slice(0, 30)} [${b.x0.toFixed(1)},${b.y0.toFixed(1)} → ${b.x1.toFixed(1)},${b.y1.toFixed(1)}] in ${W}×${H}`);
    if (el.tagName === 'text') texts.push([el.textContent, b]);
  }
  // text-to-text overlap is checked ink-accurately in qa_text.py
  return out;
};
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1200, height: 1200 } });
  let issues = 0, checked = 0;
  const run = async (label, svgText) => {
    fs.writeFileSync('build/_qa.html', `<style>${css}body{margin:0}svg{width:1000px;height:auto}</style>` + svgText.replace(/ width="[^"]*" height="[^"]*"/, ''));
    await p.goto('file://' + path.resolve('build/_qa.html')); await p.evaluate(() => document.fonts.ready);
    const r = await p.evaluate(probe); checked++;
    if (r.length) { issues += r.length; console.log('✗', label); r.slice(0, 8).forEach(x => console.log('   ', x)); }
  };
  for (const f of walk(process.argv[2] || 'stage').filter(f => f.endsWith('.svg'))) await run(f, fs.readFileSync(f, 'utf8'));
  for (const t of JSON.parse(fs.readFileSync('build/templates.json', 'utf8'))) await run('app:' + t.id, t.svg.replace('<svg ', `<svg viewBox="0 0 ${t.w} ${t.h}" `));
  console.log(`checked ${checked} designs, ${issues} issue(s)`);
  await b.close();
})();
