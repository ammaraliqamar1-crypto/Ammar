const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs'); const dir = process.argv[2];
const jobs = [['logo-primary.svg',2400],['logo-primary-on-dark.svg',2400],['logo-bilingual-signboard.svg',3000],['logo-stacked.svg',1600],['icon-whatsapp-facebook.svg',1024],['watermark-white.svg',1200],['watermark-black.svg',1200],['mark-only.svg',1024]];
(async () => {
  const b = await chromium.launch();
  for (const [f,w] of jobs) {
    const s = fs.readFileSync(dir+'/'+f,'utf8');
    const [vw,vh] = s.match(/viewBox="0 0 ([\d.]+) ([\d.]+)"/).slice(1).map(Number);
    const h = Math.round(w*vh/vw);
    const p = await b.newPage({ viewport:{width:w,height:h} });
    await p.setContent(`<style>html,body{margin:0;background:transparent}svg{display:block;width:${w}px;height:${h}px}</style>`+s.replace(/width="[^"]*" height="[^"]*"/,''));
    await p.screenshot({ path: dir+'/'+f.replace('.svg','.png'), omitBackground:true });
    await p.close();
  }
  await b.close();
})();
