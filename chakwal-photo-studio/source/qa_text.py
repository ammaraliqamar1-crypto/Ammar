"""Ink-accurate text QA: every text line inside its canvas and no two lines' ink overlapping."""
import itertools, sys
import ad, kit
from brand import SURMA, MALAI, SONA, MEHNDI

REC = []
_orig = ad.t


def rec_t(font, s, size, x, y, fill, track=0.0, anchor="start", max_w=None):
    sz = size
    if max_w:
        w = font.width(s, size, track)
        if w > max_w:
            sz = size * max_w / w
    w = font.width(s, sz, track)
    x0 = x - (w / 2 if anchor == "middle" else w if anchor == "end" else 0)
    b = font.bounds(s, sz, x0, y, track)
    if b:
        REC.append((s, b))
    return _orig(font, s, size, x, y, fill, track, anchor, max_w)


ad.t = rec_t
kit.t = rec_t

designs = {}
def run(name, fn, W, H):
    REC.clear(); fn(); designs[name] = (list(REC), W, H)

for p in kit.POSTS:
    run("post-" + p["key"], lambda p=p: kit.service_post(p), 1080, 1350)
run("facebook-cover", kit.fb_cover, 1640, 624)
run("ad-post", ad.ad_post, 1080, 1350)
run("ad-status", lambda: ad.ad_tall(1920), 1080, 1920)
run("ad-flyer", lambda: ad.ad_tall(1527), 1080, 1527)
for name, kind, title, ur, date in kit.ALBUMS:
    run(name, lambda k=kind, a=title, u=ur, d=date: kit.album(k, a, u, d), 1200, 1200)
run("card-back", ad.card_back, ad.CW, ad.CH)
run("badge", lambda: kit.badge(SURMA, MALAI, SONA, MALAI), 1000, 1000)
run("signboard", kit.signboard, 2400, 600)
run("order-slip", kit.order_slip, 592, 840)

bad = 0
for name, (recs, W, H) in designs.items():
    for s, (x0, y0, x1, y1) in recs:
        if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
            bad += 1; print(f"✗ {name}: outside canvas '{s[:30]}' {x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f}")
    for (sa, a), (sb, b) in itertools.combinations(recs, 2):
        ix = min(a[2], b[2]) - max(a[0], b[0]); iy = min(a[3], b[3]) - max(a[1], b[1])
        if ix > 1 and iy > 1:
            bad += 1; print(f"✗ {name}: ink overlap {iy:.1f}px '{sa[:26]}' × '{sb[:26]}'")
print(f"text QA: {sum(len(r) for r, _, _ in designs.values())} lines in {len(designs)} designs, {bad} issue(s)")
sys.exit(1 if bad else 0)
