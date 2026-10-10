const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs'); const dir = process.argv[2];
const pdfs = {'ad-flyer-a4.svg': ['210mm','297mm'], 'card-front.svg': ['3.75in','2.25in'], 'card-back.svg': ['3.75in','2.25in']};
(async () => {
  const b = await chromium.launch();
  for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.svg'))) {
    const s = fs.readFileSync(dir+'/'+f,'utf8');
    const [w,h] = s.match(/viewBox="0 0 ([\d.]+) ([\d.]+)"/).slice(1).map(Number);
    const p = await b.newPage({ viewport:{width:Math.round(w),height:Math.round(h)} });
    const strip = s.replace(/width="[^"]*" height="[^"]*"/,'');
    await p.setContent(`<style>@page{margin:0}html,body{margin:0}body>svg{display:block;width:100vw;height:100vh}</style>`+strip);
    await p.screenshot({ path: dir+'/'+f.replace('.svg','.png') });
    if (pdfs[f]) await p.pdf({ path: dir+'/'+f.replace('.svg','.pdf'), width: pdfs[f][0], height: pdfs[f][1], printBackground: true, pageRanges: '1' });
    await p.close();
  }
  await b.close();
})();
