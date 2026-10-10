#!/bin/bash
# Rebuild every Chakwal Photo Studio deliverable into ./stage
set -euo pipefail
cd "$(dirname "$0")"
rm -rf stage kitout adout appout build/thumbs
mkdir -p stage
python3 brand.py stage/logo >/dev/null && node png.js stage/logo
python3 ad.py adout >/dev/null && node render.js adout
mkdir -p stage/ads stage/cards && cp adout/ad-* stage/ads/ && cp adout/card-* stage/cards/
python3 kit.py kitout >/dev/null && node kitrender.js kitout
cp -r kitout/dp kitout/illustrations kitout/social kitout/album-covers kitout/signboard kitout/stationery stage/
python3 studio_app.py templates && node app_thumbs.js && python3 studio_app.py html appout
python3 -c "from brand import horizontal, MALAI, SONA; open('guide/logo-dark.svg','w').write(horizontal(MALAI,SONA,MALAI,MALAI,SONA))"
node guideshots.js && node guidepdf.js
python3 page.py chakwal-photo-studio.html
echo BUILD-OK
