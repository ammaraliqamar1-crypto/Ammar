"""Chakwal Photo Studio - advertisement and business card artwork.

Usage: python3 ad.py OUT_DIR [--photo path/to/wedding.jpg]
Without --photo the arch window shows the brand's Potohar illustration.
All lettering is outlined, so the files print exactly as designed."""
import base64, mimetypes, os, sys
from brand import (mark, horizontal, svg, fmt, F_DISPLAY, F_SUB, F_URDU,
                   SURMA, MALAI, SONA, NAME, SUB, URDU)

# ---- Studio details --------------------------------------------------------
CONTACT_NAME = "Zaigham Ali"
PHONES = ["0316-5549338", "0336-9145512"]
ADDRESS = "Minhas Book Palace, Pindi Road, Chakwal"
ADDRESS_UR = "منہاس بک پیلس، پنڈی روڈ، چکوال"
SERVICES = [  # (English, Urdu, is_new)
    ("Wedding Photography & Movies", "شادی کی فوٹوگرافی اور مووی", False),
    ("Drone Coverage", "ڈرون کوریج", False),
    ("Lighting & Stage Decoration", "لائٹنگ اور اسٹیج ڈیکوریشن", False),
    ("Sound System", "ساؤنڈ سسٹم", False),
    ("Album Designing & Mixing", "البم ڈیزائننگ اور مکسنگ", False),
    ("All Size Photo Prints, Frames & Crystals", "ہر سائز کے فوٹو پرنٹ، فریم اور کرسٹل", True),
    ("Studio Portraits & Passport Photos", "اسٹوڈیو پورٹریٹ اور پاسپورٹ فوٹو", False),
]
HEADLINE_UR = "آپ کی خوشیوں کے لمحے، ہمیشہ کے لیے"
HEADLINE_EN = "MOMENTS OF YOUR HAPPINESS, KEPT FOREVER"
STAFF_EN = "Professional Male & Female Staff Available"
STAFF_UR = "مرد اور خواتین اسٹاف دستیاب"

INK2 = "#CFC6B6"  # softer ivory for secondary text on charcoal


LIVE = False  # True: emit live <text> (editable in the Studio Designer app) instead of outlines
FAMILY = {id(F_DISPLAY): "CPS Display", id(F_SUB): "CPS Sans", id(F_URDU): "CPS Urdu"}


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def t(font, s, size, x, y, fill, track=0.0, anchor="start", max_w=None):
    """Outlined text (or live text when LIVE); shrinks to max_w if given."""
    base = size
    if max_w:
        w = font.width(s, size, track)
        if w > max_w:
            size *= max_w / w
    if LIVE:
        fam = FAMILY[id(font)]
        ls = f' letter-spacing="{track * size:.2f}"' if track else ""
        mw = f' data-maxw="{fmt(max_w)}" data-base="{base:.2f}" data-track="{track}"' if max_w else ""
        rtl = font is F_URDU
        if rtl:  # in RTL, SVG "start" is the right edge
            anchor = {"start": "end", "end": "start"}.get(anchor, anchor)
        d = ' direction="rtl"' if rtl else ""
        return (f'<text x="{fmt(x)}" y="{fmt(y)}" font-family="{fam}" font-size="{size:.2f}" fill="{fill}" '
                f'text-anchor="{anchor}"{d}{ls}{mw} data-edit="1" xml:space="preserve">{_esc(s)}</text>')
    return f'<path fill="{fill}" d="{font.path(s, size, x, y, track, anchor)}"/>'


def fit_size(font, items, size, max_w, track=0.0):
    w = max(font.width(s, size, track) for s in items)
    return size * min(1.0, max_w / w)


def inner(svgstr):
    """Strip outer <svg> wrapper, return (viewbox_w, viewbox_h, body)."""
    vb = svgstr.split('viewBox="0 0 ')[1].split('"')[0].split()
    body = svgstr[svgstr.index(">") + 1: svgstr.rindex("</svg>")]
    return float(vb[0]), float(vb[1]), body


def place(svgstr, x, y, w):
    vw, vh, body = inner(svgstr)
    s = w / vw
    return f'<g transform="translate({fmt(x)} {fmt(y)}) scale({s:.4f})">{body}</g>', vh * s


SCENE = """<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3E4A66"/><stop offset=".55" stop-color="#D58A5A"/><stop offset="1" stop-color="#F2C98B"/></linearGradient>
<radialGradient id="sunglow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#FFF1C9"/><stop offset=".35" stop-color="#FBD38D" stop-opacity=".9"/><stop offset="1" stop-color="#FBD38D" stop-opacity="0"/></radialGradient>
<rect width="600" height="400" fill="url(#sky)"/><circle cx="300" cy="236" r="120" fill="url(#sunglow)"/><circle cx="300" cy="236" r="30" fill="#FFF0C8"/>
<path d="M0 250L60 226L110 236L170 204H240L290 230L350 214L420 238L470 222L530 240L600 228V400H0Z" fill="#8C5A48"/>
<path d="M0 286C90 266 170 284 260 276C350 268 430 262 600 270V400H0Z" fill="#5E3D36"/>
<path d="M0 330C120 314 260 330 380 318C470 310 540 316 600 312V400H0Z" fill="#3B2A27"/>
<g fill="#2A1E1C"><circle cx="270" cy="300" r="7"/><path d="M261 340Q270 306 279 340Z"/><circle cx="288" cy="304" r="6"/><path d="M280 340Q288 310 296 340Z"/><circle cx="305" cy="314" r="4.5"/><path d="M299 340Q305 318 311 340Z"/></g>"""


def arch_window(x, y, w, h, photo, uid):
    """The Darwaza arch used as a photo window, with gold focus corners."""
    r = w / 2
    d = f"M{fmt(x)} {fmt(y + h)}V{fmt(y + r)}A{fmt(r)} {fmt(r)} 0 0 1 {fmt(x + w)} {fmt(y + r)}V{fmt(y + h)}Z"
    if photo:
        fill = (f'<image href="{photo}" x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" '
                f'preserveAspectRatio="xMidYMid slice"/>')
    else:
        fill = (f'<svg x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" viewBox="150 0 300 400" '
                f'preserveAspectRatio="xMidYMid slice">{SCENE}</svg>')
    g = 26  # gap from arch to focus corners
    L = min(w, h) * 0.16
    x0, y0, x1, y1 = x - g, y - g, x + w + g, y + h + g
    corners = (f"M{fmt(x0)} {fmt(y0 + L)}V{fmt(y0)}H{fmt(x0 + L)}M{fmt(x1 - L)} {fmt(y0)}H{fmt(x1)}V{fmt(y0 + L)}"
               f"M{fmt(x1)} {fmt(y1 - L)}V{fmt(y1)}H{fmt(x1 - L)}M{fmt(x0 + L)} {fmt(y1)}H{fmt(x0)}V{fmt(y1 - L)}")
    return (f'<clipPath id="arch{uid}"><path d="{d}"/></clipPath>'
            f'<g clip-path="url(#arch{uid})" data-slot="photo" data-box="{fmt(x)} {fmt(y)} {fmt(w)} {fmt(h)}">'
            f'<g class="slot-default">{fill}</g></g>'
            f'<path d="{d}" fill="none" stroke="{MALAI}" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="{corners}" fill="none" stroke="{SONA}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')


def bullet(x, y, new=False):
    s = 7
    return f'<path d="M{fmt(x)} {fmt(y - s)}L{fmt(x + s)} {fmt(y)}L{fmt(x)} {fmt(y + s)}L{fmt(x - s)} {fmt(y)}Z" fill="{SONA}"/>'


def new_tag(x, y):
    w = F_SUB.width("NEW", 15, 0.2) + 20
    return (f'<rect x="{fmt(x)}" y="{fmt(y - 17)}" width="{fmt(w)}" height="24" rx="12" fill="{SONA}"/>'
            + t(F_SUB, "NEW", 15, x + 10, y, SURMA, 0.2)), w


def frame(W, H):
    return (f'<rect width="{W}" height="{H}" fill="{SURMA}"/>'
            f'<rect x="28" y="28" width="{W - 56}" height="{H - 56}" fill="none" stroke="{SONA}" stroke-width="2"/>'
            f'<rect x="38" y="38" width="{W - 76}" height="{H - 76}" fill="none" stroke="{SONA}" stroke-opacity=".35" stroke-width="1"/>')


def services_block(x, y, col_w, row_h, items, en_size=26, ur_size=21):
    out = ""
    en_size = fit_size(F_SUB, [e for e, _, n in SERVICES], en_size, col_w - 30 - 70)
    for i, (en, ur, new) in enumerate(items):
        yy = y + i * row_h
        out += bullet(x + 7, yy - en_size * 0.35)
        out += t(F_SUB, en, en_size, x + 30, yy, MALAI, 0.01)
        if new:
            tag, _ = new_tag(x + 30 + F_SUB.width(en, en_size, 0.01) + 12, yy - 2)
            out += tag
        out += t(F_URDU, ur, ur_size, x + 30, yy + ur_size * 1.75, INK2, max_w=col_w - 30)
    return out


def contact_block(cx, y, W):
    out = t(F_SUB, "CONTACT", 18, cx, y, SONA, 0.4, "middle")
    out += t(F_DISPLAY, CONTACT_NAME, 40, cx, y + 54, MALAI, 0.02, "middle")
    out += t(F_SUB, "   ·   ".join(PHONES), 46, cx, y + 118, MALAI, 0.03, "middle", max_w=W - 160)
    out += f'<rect x="{fmt(cx - 200)}" y="{fmt(y + 146)}" width="400" height="1.5" fill="{SONA}" opacity=".6"/>'
    out += t(F_SUB, ADDRESS, 25, cx, y + 190, INK2, 0.02, "middle", max_w=W - 160)
    out += t(F_URDU, ADDRESS_UR, 23, cx, y + 238, INK2, anchor="middle")
    return out


def staff_band(cx, y, W):
    w = W - 180
    out = f'<rect x="{fmt(cx - w / 2)}" y="{fmt(y)}" width="{fmt(w)}" height="84" rx="42" fill="none" stroke="{SONA}" stroke-width="2.5"/>'
    out += t(F_SUB, STAFF_EN, 26, cx, y + 36, MALAI, 0.02, "middle", max_w=w - 60)
    out += t(F_URDU, STAFF_UR, 20, cx, y + 70, SONA, anchor="middle")
    return out


def headline(cx, y, W):
    out = t(F_URDU, HEADLINE_UR, 44, cx, y, MALAI, anchor="middle", max_w=W - 160)
    out += t(F_SUB, HEADLINE_EN, 19, cx, y + 58, SONA, 0.28, "middle", max_w=W - 160)
    return out


LOGO = horizontal(MALAI, SONA, MALAI, MALAI, SONA)


def ad_post(photo=None):
    """1080 x 1350 - Facebook / Instagram / WhatsApp feed."""
    W, H = 1080, 1350
    cx = W / 2
    body = frame(W, H)
    lg, lh = place(LOGO, cx - 260, 76, 520)
    body += lg
    body += headline(cx, 76 + lh + 66, W)
    top = 76 + lh + 150
    body += arch_window(W - 96 - 290, top + 30, 290, 440, photo, "p")
    body += services_block(84, top + 34, 560, 75, SERVICES, 25, 18)
    body += staff_band(cx, top + 572, W)
    body += contact_block(cx, top + 706, W)
    return svg(W, H, body)


def ad_tall(H, photo=None, uid="t"):
    """1080 wide, tall formats: WhatsApp status (1920) and A4 flyer (1527)."""
    W = 1080
    cx = W / 2
    extra = H - 1527  # spare height distributed over the arch and gaps
    body = frame(W, H)
    lg, lh = place(LOGO, cx - 280, 70 + extra * .08, 560)
    body += lg
    y = 70 + extra * .08 + lh + 70 + extra * .04
    body += headline(cx, y, W)
    y += 100 + extra * .04
    aw, ah = 330 + extra * .3, 270 + extra * .6
    body += arch_window(cx - aw / 2, y + 26, aw, ah, photo, uid)
    y += ah + 100 + extra * .05
    half = (len(SERVICES) + 1) // 2
    body += services_block(90, y, 440, 70, SERVICES[:half], 22, 17)
    body += services_block(560, y, 440, 70, SERVICES[half:], 22, 17)
    y += half * 70 + extra * .04
    body += staff_band(cx, y, W)
    y += 84 + 62 + extra * .04
    body += contact_block(cx, y, W)
    return svg(W, H, body)


# ---- Business card: 3.5 x 2 in + 0.125 in bleed, 300 units per inch --------
BLEED = 37.5
CW, CH = 1050 + 2 * BLEED, 600 + 2 * BLEED


def card_front():
    body = f'<rect width="{fmt(CW)}" height="{fmt(CH)}" fill="{SURMA}"/>'
    lg, lh = place(LOGO, CW / 2 - 330, CH / 2 - 0, 660)
    vw, vh, _ = inner(LOGO)
    lg, lh = place(LOGO, CW / 2 - 330, CH / 2 - (vh * 660 / vw) / 2, 660)
    return svg(CW, CH, body + lg)


def card_back():
    x0, y0 = BLEED + 70, BLEED + 66
    body = f'<rect width="{fmt(CW)}" height="{fmt(CH)}" fill="{MALAI}"/>'
    body += t(F_DISPLAY, CONTACT_NAME, 54, x0, y0 + 46, SURMA, 0.02)
    body += t(F_SUB, "PHOTOGRAPHER & VIDEOGRAPHER", 17, x0, y0 + 86, SONA, 0.24)
    mk, _ = place(svg(200, 200, mark(SURMA, SONA)), CW - BLEED - 70 - 120, y0 - 6, 120)
    body += mk
    y = y0 + 168
    for p in PHONES:
        body += t(F_SUB, p, 36, x0, y, SURMA, 0.03)
        y += 50
    body += t(F_SUB, ADDRESS, 21, x0, y + 10, SURMA, 0.01)
    body += t(F_URDU, ADDRESS_UR, 19, x0, y + 50, "#5E574D")
    # services strip
    sy = CH - BLEED - 62
    body += f'<rect x="{fmt(x0)}" y="{fmt(sy - 34)}" width="{fmt(CW - 2 * x0)}" height="1.5" fill="{SONA}"/>'
    body += t(F_SUB, "WEDDINGS · MOVIES · DRONE · ALL SIZE PRINTS, FRAMES & CRYSTALS", 15.5, x0, sy, SURMA, 0.12,
              max_w=CW - 2 * x0)
    return svg(CW, CH, body)


if __name__ == "__main__":
    out = sys.argv[1]
    photo = None
    if "--photo" in sys.argv:
        p = sys.argv[sys.argv.index("--photo") + 1]
        mime = mimetypes.guess_type(p)[0] or "image/jpeg"
        photo = f"data:{mime};base64," + base64.b64encode(open(p, "rb").read()).decode()
    os.makedirs(out, exist_ok=True)
    files = {
        "ad-post-1080x1350.svg": ad_post(photo),
        "ad-status-1080x1920.svg": ad_tall(1920, photo, "s"),
        "ad-flyer-a4.svg": ad_tall(1527, photo, "a"),
        "card-front.svg": card_front(),
        "card-back.svg": card_back(),
    }
    for k, v in files.items():
        open(os.path.join(out, k), "w").write(v)
    print("\n".join(files))
