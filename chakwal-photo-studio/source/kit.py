"""Chakwal Photo Studio - complete brand kit.

Builds: round DP badge, service illustrations, social posts, highlight covers,
Facebook cover, album covers, signboard flex and order slip.

Usage: python3 kit.py OUT_DIR
Real photos: put wedding.jpg, baby.jpg, family.jpg, passport.jpg, prints.jpg,
drone.jpg in source/photos/ (next to this file) and run again - each post then
shows the studio's own photo in the arch window instead of the illustration."""
import base64, math, mimetypes, os, sys
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from brand import (mark, horizontal, stacked, svg, fmt, F_DISPLAY, F_SUB, F_URDU,
                   SURMA, MALAI, SONA, MEHNDI, BLACK, WHITE, NAME, SUB, URDU)
from ad import (t, place, inner, frame, PHONES, CONTACT_NAME, ADDRESS, ADDRESS_UR, SCENE)

HERE = os.path.dirname(os.path.abspath(__file__))
SURMA2 = "#322D27"   # raised charcoal panel
MALAI2 = "#EAE0CE"   # shaded ivory panel


# ---------------------------------------------------------------------------
# Service illustrations - 200 x 200, one stroke weight, gold accent.
# `bg` is the colour behind the drawing, used to let front shapes overlap.
# ---------------------------------------------------------------------------
def _g(line, sw, inner_):
    return (f'<g fill="none" stroke="{line}" stroke-width="{sw}" stroke-linecap="round" '
            f'stroke-linejoin="round">{inner_}</g>')


def ill_wedding(line, gold, bg, sw=5):
    return _g(line, sw, f"""
<path d="M30 176C32 140 46 122 76 120C100 119 110 130 114 146"/>
<path d="M76 120V176"/>
<circle cx="76" cy="132" r="2.6" fill="{gold}" stroke="none"/><circle cx="76" cy="146" r="2.6" fill="{gold}" stroke="none"/><circle cx="76" cy="160" r="2.6" fill="{gold}" stroke="none"/>
<circle cx="76" cy="98" r="16"/>
<path d="M57 93C55 72 66 61 77 61C89 61 99 71 96 93C88 88 66 88 57 93Z" fill="{bg}"/>
<path d="M60 83C70 77 86 77 95 83M64 72C72 68 84 68 92 72"/>
<path d="M82 63C86 52 95 45 106 43M84 66C92 58 102 56 111 58" stroke="{gold}"/>
<path d="M100 176C98 146 104 126 116 116C120 88 130 78 138 78C154 78 160 92 160 110C162 136 170 156 176 176Z" fill="{bg}"/>
<circle cx="136" cy="106" r="14"/>
<path d="M116 116C120 96 128 88 138 88C150 88 156 98 156 112" stroke="{gold}" stroke-dasharray="0.1 9"/>
<circle cx="134" cy="94" r="3.2" fill="{gold}" stroke="none"/>
<path d="M120 150C132 146 148 148 164 156" stroke="{gold}"/>""")


def ill_baby(line, gold, bg, sw=5):
    return _g(line, sw, f"""
<path d="M56 176C52 136 70 114 100 114C130 114 148 136 144 176Z"/>
<path d="M62 150C84 140 112 156 140 142"/>
<path d="M58 168C84 160 116 172 142 164" stroke="{gold}"/>
<circle cx="100" cy="86" r="30" fill="{bg}"/>
<path d="M86 86Q91 91 96 86M104 86Q109 91 114 86"/>
<path d="M95 99Q100 103 105 99"/>
<path d="M100 56C94 50 100 42 106 47"/>
<path d="M150 46L153 56L163 59L153 62L150 72L147 62L137 59L147 56Z" fill="{gold}" stroke="none"/>
<path d="M44 74L46 80L52 82L46 84L44 90L42 84L36 82L42 80Z" fill="{gold}" stroke="none"/>""")


def ill_family(line, gold, bg, sw=5):
    return _g(line, sw, f"""
<path d="M28 176C28 134 42 116 64 116C86 116 98 132 98 160"/>
<circle cx="64" cy="88" r="17"/>
<path d="M102 160C102 132 114 116 136 116C158 116 172 134 172 176"/>
<path d="M114 96C114 70 158 70 158 96C160 108 164 116 170 122"/>
<circle cx="136" cy="92" r="15"/>
<path d="M76 176C76 152 86 142 100 142C114 142 124 152 124 176Z" fill="{bg}"/>
<circle cx="100" cy="122" r="12" fill="{bg}" stroke="{gold}"/>""")


def ill_passport(line, gold, bg, sw=5):
    return _g(line, sw, f"""
<rect x="58" y="40" width="84" height="112" rx="4"/>
<circle cx="100" cy="82" r="17"/>
<path d="M72 152C72 124 84 112 100 112C116 112 128 124 128 152"/>
<path d="M44 52V40H56M144 40H156V52M156 140V152H144M56 152H44V140" stroke="{gold}"/>
<path d="M66 172H134" />
<path d="M84 186H116" stroke="{gold}"/>""")


def ill_prints(line, gold, bg, sw=5):
    return _g(line, sw, f"""
<rect x="30" y="34" width="96" height="120" rx="3"/>
<rect x="44" y="48" width="68" height="92"/>
<path d="M44 120L60 108L70 114L82 102L96 112L112 104"/>
<circle cx="78" cy="80" r="9" fill="{gold}" stroke="none"/>
<path d="M112 108H156V174H112Z" fill="{bg}"/>
<path d="M112 108L128 94H172L156 108M156 108L172 94V160L156 174"/>
<path d="M134 152C122 144 120 132 128 128C132 126 134 130 134 132C134 130 136 126 140 128C148 132 146 144 134 152Z" fill="{gold}" stroke="none"/>""")


def ill_drone(line, gold, bg, sw=5):
    return _g(line, sw, f"""
<path d="M78 92H122L114 112H86Z"/>
<path d="M78 98L46 86M122 98L154 86"/>
<path d="M46 86V76M154 86V76"/>
<path d="M24 72H68M132 72H176"/>
<path d="M88 112L82 124M112 112L118 124"/>
<circle cx="100" cy="124" r="8" fill="{gold}" stroke="none"/>
<path d="M60 150C80 140 120 140 140 150" stroke="{gold}" stroke-dasharray="0.1 10"/>
<path d="M44 172C76 160 124 160 156 172"/>""")


ILLUSTRATIONS = {
    "wedding": ill_wedding, "baby": ill_baby, "family": ill_family,
    "passport": ill_passport, "prints": ill_prints, "drone": ill_drone,
}


# ---------------------------------------------------------------------------
# Text on a circle (for the round badge)
# ---------------------------------------------------------------------------
def arc_text(font, text, size, cx, cy, R, fill, track=0.0, top=True):
    infos, pos = font._shape(text)
    sc = size / font.upem
    advs = [p.x_advance * sc + track * size for p in pos]
    total = sum(advs) - track * size
    pen = SVGPathPen(font.gs, ntos=fmt)
    s = 0.0
    for inf, p, a in zip(infos, pos, advs):
        gw = p.x_advance * sc
        mid = s + gw / 2 - total / 2
        if top:
            th = -math.pi / 2 + mid / R
            rot = th + math.pi / 2
        else:
            th = math.pi / 2 - mid / R
            rot = th - math.pi / 2
        c, si = math.cos(rot), math.sin(rot)
        px, py = cx + R * math.cos(th), cy + R * math.sin(th)
        half = gw / 2
        tp = TransformPen(pen, (c * sc, si * sc, si * sc, -c * sc, px - c * half, py - si * half))
        font.gs[font.order[inf.codepoint]].draw(tp)
        s += a
    return f'<path fill="{fill}" d="{pen.getCommands()}"/>'


def badge(bg, line, gold, word, size=1000):
    """Round logo for DPs, stickers and stamps."""
    c = size / 2
    out = f'<circle cx="{c}" cy="{c}" r="{c}" fill="{bg}"/>' if bg else ""
    out += f'<circle cx="{c}" cy="{c}" r="{c - 34}" fill="none" stroke="{gold}" stroke-width="6"/>'
    out += f'<circle cx="{c}" cy="{c}" r="{c - 148}" fill="none" stroke="{gold}" stroke-width="3"/>'
    out += arc_text(F_DISPLAY, NAME, 92, c, c, c - 122, word, 0.16, top=True)
    out += arc_text(F_SUB, "PHOTO  STUDIO", 44, c, c, c - 76, word, 0.42, top=False)
    for ang in (180, 0):
        x = c + (c - 91) * math.cos(math.radians(ang))
        out += (f'<path d="M{fmt(x)} {fmt(c - 11)}L{fmt(x + 11)} {fmt(c)}L{fmt(x)} {fmt(c + 11)}'
                f'L{fmt(x - 11)} {fmt(c)}Z" fill="{gold}"/>')
    ms = 2.15
    out += mark(line, gold, sw=7.5, x=c - 100 * ms, y=c - 100 * ms - 56, s=ms)
    out += t(F_URDU, URDU, 40, c, c + 262, word, anchor="middle")
    return svg(size, size, out)


def dp_icon(bg, line, gold, size=1000):
    c = size / 2
    s = size / 200 * 0.62
    return svg(size, size, f'<circle cx="{c}" cy="{c}" r="{c}" fill="{bg}"/>'
               f'<circle cx="{c}" cy="{c}" r="{c - 30}" fill="none" stroke="{gold}" stroke-width="5"/>'
               + mark(line, gold, sw=9, x=c - 100 * s, y=c - 100 * s, s=s))


# ---------------------------------------------------------------------------
# Photo slot: arch window holding a real photo or an illustration
# ---------------------------------------------------------------------------
def photo_uri(key):
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = os.path.join(HERE, "photos", f"{key}.{ext}")
        if os.path.exists(p):
            mime = mimetypes.guess_type(p)[0] or "image/jpeg"
            return f"data:{mime};base64," + base64.b64encode(open(p, "rb").read()).decode()
    return None


_UID = [0]


def arch_slot(x, y, w, h, key, panel, line, gold, corners=True):
    _UID[0] += 1
    uid = f"slot{_UID[0]}"
    r = w / 2
    d = f"M{fmt(x)} {fmt(y + h)}V{fmt(y + r)}A{fmt(r)} {fmt(r)} 0 0 1 {fmt(x + w)} {fmt(y + r)}V{fmt(y + h)}Z"
    photo = photo_uri(key) if key else None
    if photo:
        fill = (f'<image href="{photo}" x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" '
                f'preserveAspectRatio="xMidYMid slice"/>')
    elif key in ILLUSTRATIONS:
        iw = min(w, h) * 0.78
        fill = (f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" fill="{panel}"/>'
                f'<g transform="translate({fmt(x + (w - iw) / 2)} {fmt(y + h - iw - h * 0.08)}) scale({iw / 200:.4f})">'
                f'{ILLUSTRATIONS[key](line, gold, panel, sw=5)}</g>')
    else:
        fill = (f'<svg x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" viewBox="150 0 300 400" '
                f'preserveAspectRatio="xMidYMid slice">{SCENE}</svg>')
    out = (f'<clipPath id="{uid}"><path d="{d}"/></clipPath><g clip-path="url(#{uid})">{fill}</g>'
           f'<path d="{d}" fill="none" stroke="{line}" stroke-width="5" stroke-linejoin="round"/>')
    if corners:
        g, L = 24, min(w, h) * 0.15
        x0, y0, x1, y1 = x - g, y - g, x + w + g, y + h + g
        out += (f'<path d="M{fmt(x0)} {fmt(y0 + L)}V{fmt(y0)}H{fmt(x0 + L)}M{fmt(x1 - L)} {fmt(y0)}H{fmt(x1)}V{fmt(y0 + L)}'
                f'M{fmt(x1)} {fmt(y1 - L)}V{fmt(y1)}H{fmt(x1 - L)}M{fmt(x0 + L)} {fmt(y1)}H{fmt(x0)}V{fmt(y1 - L)}" '
                f'fill="none" stroke="{gold}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>')
    return out


# ---------------------------------------------------------------------------
# Social media service posts (1080 x 1350)
# ---------------------------------------------------------------------------
THEMES = {
    "dark": dict(bg=SURMA, panel=SURMA2, line=MALAI, gold=SONA, text=MALAI, soft="#CFC6B6"),
    "light": dict(bg=MALAI, panel=MALAI2, line=SURMA, gold=SONA, text=SURMA, soft="#5E574D"),
    "mehndi": dict(bg=MEHNDI, panel="#5E2423", line=MALAI, gold="#D9B77C", text=MALAI, soft="#E6CFC2"),
}

POSTS = [
    dict(key="wedding", theme="mehndi", ur=["آپ کی شادی،", "ہماری ذمہ داری"], en="WEDDING PHOTOGRAPHY & MOVIES",
         points=["Barat · Walima · Mehndi · Nikah", "HD movie, drone, lighting & stage", "Male & female staff available"]),
    dict(key="baby", theme="light", ur=["ننھی مسکراہٹیں،", "ہمیشہ کے لیے"], en="NEWBORN & BABY PHOTOSHOOT",
         points=["Newborn, birthday & aqiqa shoots", "Safe, gentle studio setup", "Female staff on request"]),
    dict(key="family", theme="dark", ur=["پورا خاندان،", "ایک تصویر میں"], en="FAMILY PORTRAITS",
         points=["Studio & home family portraits", "Three generations, one frame", "Large prints for your wall"]),
    dict(key="passport", theme="light", ur=["پاسپورٹ اور آئی ڈی فوٹو", "منٹوں میں تیار"], en="PASSPORT & ID PHOTOS",
         points=["Passport, CNIC, visa & admission", "Correct size & background", "Ready while you wait"]),
    dict(key="prints", theme="dark", ur=["ہر سائز کے فوٹو پرنٹ،", "فریم اور کرسٹل"], en="PRINTS, FRAMES & CRYSTALS",
         points=["All size photo prints", "Wall frames & table frames", "3D crystal photo gifts"]),
    dict(key="drone", theme="dark", ur=["اوپر سے دیکھیں", "اپنی خوشیاں"], en="DRONE COVERAGE & HD MOVIES",
         points=["Aerial video & photos", "Cinematic wedding highlights", "Album designing & mixing"]),
]


def cta(cx, y, W, th):
    out = f'<rect x="{fmt(cx - (W - 160) / 2)}" y="{fmt(y)}" width="{fmt(W - 160)}" height="1.5" fill="{th["gold"]}" opacity=".7"/>'
    out += t(F_URDU, "آج ہی تشریف لائیں", 38, cx, y + 70, th["text"], anchor="middle")
    out += t(F_SUB, "VISIT US TODAY  ·  BOOK YOUR DATE", 19, cx, y + 114, th["gold"], 0.3, "middle")
    out += t(F_SUB, "   ·   ".join(PHONES), 46, cx, y + 182, th["text"], 0.03, "middle")
    out += t(F_SUB, ADDRESS, 24, cx, y + 226, th["soft"], 0.02, "middle")
    return out


def logo_for(th):
    return horizontal(th["line"], th["gold"], th["text"], th["text"], th["gold"])


def service_post(p):
    th = THEMES[p["theme"]]
    W, H = 1080, 1350
    cx = W / 2
    body = (f'<rect width="{W}" height="{H}" fill="{th["bg"]}"/>'
            f'<rect x="28" y="28" width="{W - 56}" height="{H - 56}" fill="none" stroke="{th["gold"]}" stroke-width="2"/>')
    lg, lh = place(logo_for(th), cx - 230, 72, 460)
    body += lg
    body += arch_slot(104, 270, 430, 620, p["key"], th["panel"], th["line"], th["gold"])
    x = 600
    body += t(F_SUB, p["en"], 19, x, 360, th["gold"], 0.2, max_w=W - x - 76)
    yy = 452
    for ln in p["ur"]:
        body += t(F_URDU, ln, 46, W - 76, yy, th["text"], anchor="end", max_w=W - x - 76)
        yy += 94
    yy += 20
    for pt in p["points"]:
        body += (f'<path d="M{x + 7} {yy - 17}L{x + 14} {yy - 10}L{x + 7} {yy - 3}L{x} {yy - 10}Z" fill="{th["gold"]}"/>')
        body += t(F_SUB, pt, 25, x + 28, yy, th["text"], 0.01, max_w=W - x - 104)
        yy += 58
    body += cta(cx, 990, W, th)
    return svg(W, H, body)


def highlight(key, label):
    """1080 x 1080 story-highlight cover; works inside the round crop."""
    S = 1080
    c = S / 2
    body = f'<rect width="{S}" height="{S}" fill="{SURMA}"/>'
    body += f'<circle cx="{c}" cy="{c}" r="430" fill="none" stroke="{SONA}" stroke-width="5"/>'
    if key == "logo":
        s = 2.3
        body += mark(MALAI, SONA, sw=8, x=c - 100 * s, y=c - 100 * s - 40, s=s)
    else:
        s = 2.2
        body += f'<g transform="translate({fmt(c - 100 * s)} {fmt(c - 100 * s - 50)}) scale({s})">{ILLUSTRATIONS[key](MALAI, SONA, SURMA, sw=6)}</g>'
    body += t(F_SUB, label, 54, c, c + 300, MALAI, 0.22, "middle")
    return svg(S, S, body)


HIGHLIGHTS = [("wedding", "WEDDINGS"), ("baby", "BABIES"), ("family", "FAMILY"),
              ("passport", "PASSPORT"), ("prints", "FRAMES"), ("drone", "DRONE"), ("logo", "STUDIO")]


def fb_cover():
    W, H = 1640, 624
    body = f'<rect width="{W}" height="{H}" fill="{SURMA}"/>'
    body += f'<rect x="20" y="20" width="{W - 40}" height="{H - 40}" fill="none" stroke="{SONA}" stroke-width="2"/>'
    lg, lh = place(horizontal(MALAI, SONA, MALAI, MALAI, SONA), 180, 92, 560)
    body += lg
    body += t(F_URDU, "آپ کی خوشیوں کے لمحے، ہمیشہ کے لیے", 40, 460, 330, MALAI, anchor="middle")
    body += t(F_SUB, "WEDDINGS · BABIES · FAMILY · PRINTS, FRAMES & CRYSTALS", 17, 460, 388, SONA, 0.2, "middle")
    body += t(F_SUB, "   ·   ".join(PHONES), 34, 460, 456, MALAI, 0.03, "middle")
    body += t(F_SUB, ADDRESS, 19, 460, 498, "#CFC6B6", 0.02, "middle")
    for i, k in enumerate(["baby", "wedding", "family"]):
        w, h = (230, 380) if k == "wedding" else (200, 320)
        x = 880 + i * 250 + (0 if k != "wedding" else -15)
        y = (H - h) / 2 + (0 if k == "wedding" else 30)
        body += arch_slot(x, y, w, h, k, SURMA2, MALAI, SONA, corners=(k == "wedding"))
    return svg(W, H, body)


# ---------------------------------------------------------------------------
# Album covers - 12 x 12 in (1200 units = 12 in at 100/in)
# ---------------------------------------------------------------------------
FOIL = ('<linearGradient id="{id}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="1200" y2="1200">'
        '<stop offset="0" stop-color="#E3C58C"/><stop offset=".45" stop-color="#B08D57"/>'
        '<stop offset=".7" stop-color="#F0D9A8"/><stop offset="1" stop-color="#9C7A45"/></linearGradient>')


def album(kind, title, sub_ur, date):
    S = 1200
    c = S / 2
    if kind == "wedding":
        bg, ink, ill = MEHNDI, "url(#foilW)", "wedding"
        defs = FOIL.format(id="foilW")
    elif kind == "baby":
        bg, ink, ill = MALAI, "url(#foilB)", "baby"
        defs = FOIL.format(id="foilB").replace("#E3C58C", "#A88450").replace("#F0D9A8", "#B8925A").replace("#B08D57", "#7E5F33").replace("#9C7A45", "#6E5230")
    else:
        bg, ink, ill = SURMA, "url(#foilF)", "family"
        defs = FOIL.format(id="foilF")
    body = f'<rect width="{S}" height="{S}" fill="{bg}"/>'
    body += f'<rect x="60" y="60" width="{S - 120}" height="{S - 120}" fill="none" stroke="{ink}" stroke-width="3"/>'
    body += f'<rect x="76" y="76" width="{S - 152}" height="{S - 152}" fill="none" stroke="{ink}" stroke-width="1.2"/>'
    s = 1.55
    body += (f'<g transform="translate({fmt(c - 100 * s)} 190) scale({s})">'
             f'<path d="M30 200V90A70 70 0 0 1 170 90V200" fill="none" stroke="{ink}" stroke-width="3.2"/>'
             f'<g transform="translate(40 52) scale(.6)">{ILLUSTRATIONS[ill](ink, ink, bg, sw=5.5)}</g></g>')
    body += t(F_DISPLAY, title, 74, c, 640, ink, 0.03, "middle", max_w=900)
    body += t(F_URDU, sub_ur, 44, c, 730, ink, anchor="middle")
    body += t(F_SUB, date, 24, c, 800, ink, 0.4, "middle")
    nw = F_DISPLAY.width("CHAKWAL PHOTO STUDIO", 26, 0.14)
    body += t(F_DISPLAY, "CHAKWAL PHOTO STUDIO", 26, c, 1050, ink, 0.14, "middle")
    body += mark(ink, ink, sw=7, x=c - 30, y=960, s=0.3)
    return svg(S, S, body, defs=defs)


ALBUMS = [
    ("album-wedding", "wedding", "Ayesha & Bilal", "شادی مبارک", "12 · 12 · 2026"),
    ("album-baby", "baby", "Our Little Blessing", "ننھی خوشیاں", "MUHAMMAD HASSAN · 2026"),
    ("album-family", "family", "Our Family", "ہمارا خاندان", "THE AWAN FAMILY · 2026"),
]


# ---------------------------------------------------------------------------
# Signboard flex - 12 ft x 3 ft (2400 x 600 units, 200 units per ft)
# ---------------------------------------------------------------------------
def signboard():
    W, H = 2400, 600
    body = f'<rect width="{W}" height="{H}" fill="{SURMA}"/>'
    body += f'<rect x="24" y="24" width="{W - 48}" height="{H - 48}" fill="none" stroke="{SONA}" stroke-width="6"/>'
    lg, lh = place(horizontal(MALAI, SONA, MALAI, MALAI, SONA, urdu=True), 110, 70, 1500)
    body += lg
    x = 1720
    body += f'<rect x="{x - 40}" y="90" width="3" height="{H - 180}" fill="{SONA}"/>'
    body += t(F_SUB, "CALL", 26, x, 150, SONA, 0.3)
    for i, p in enumerate(PHONES):
        body += t(F_SUB, p, 62, x, 240 + i * 82, MALAI, 0.02, max_w=W - x - 70)
    body += t(F_SUB, "MINHAS BOOK PALACE", 26, x, 430, "#CFC6B6", 0.2)
    body += t(F_SUB, "PINDI ROAD, CHAKWAL", 26, x, 470, "#CFC6B6", 0.2)
    strip = "WEDDING PHOTOGRAPHY & MOVIES  ·  DRONE  ·  BABY & FAMILY SHOOTS  ·  ALL SIZE PRINTS, FRAMES & CRYSTALS"
    body += f'<rect x="110" y="{H - 132}" width="1500" height="2" fill="{SONA}"/>'
    body += t(F_SUB, strip, 25, 110, H - 82, MALAI, 0.14, max_w=1500)
    return svg(W, H, body)


# ---------------------------------------------------------------------------
# Order slip / receipt - A5 portrait (148 x 210 mm at 4 units/mm)
# ---------------------------------------------------------------------------
def order_slip():
    W, H = 592, 840
    ink, soft = SURMA, "#8A8174"
    body = f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>'
    lg, lh = place(horizontal(SURMA, SONA, SURMA, SURMA, SONA), 40, 36, 300)
    body += lg
    body += t(F_SUB, "ORDER SLIP / RECEIPT", 13, W - 40, 62, SONA, 0.2, "end")
    body += t(F_SUB, "No. ________", 15, W - 40, 92, ink, 0.02, "end")
    body += t(F_SUB, "Date ________", 15, W - 40, 118, ink, 0.02, "end")
    body += f'<rect x="40" y="{fmt(36 + lh + 18)}" width="{W - 80}" height="2" fill="{SONA}"/>'
    rows = [("Customer name", "نام"), ("Phone", "فون"), ("Event / Service", "تقریب / سروس"),
            ("Event date", "تاریخ تقریب"), ("Venue", "مقام")]
    y = 36 + lh + 70
    for en, ur in rows:
        body += t(F_SUB, en, 14, 40, y, ink, 0.02)
        body += t(F_URDU, ur, 14, W - 40, y + 2, soft, anchor="end")
        body += f'<rect x="170" y="{y + 4}" width="{W - 320}" height="1" fill="{soft}"/>'
        y += 40
    # table
    y += 10
    cols = [40, 300, 400, 470, W - 40]
    heads = ["Item / size", "Qty", "Rate", "Amount"]
    body += f'<rect x="40" y="{y}" width="{W - 80}" height="30" fill="{MALAI}"/>'
    for i, hd in enumerate(heads):
        body += t(F_SUB, hd, 12.5, cols[i] + 8, y + 20, ink, 0.06)
    for r in range(6):
        yy = y + 30 + (r + 1) * 30
        body += f'<rect x="40" y="{yy}" width="{W - 80}" height="1" fill="#D9D1C3"/>'
    for cx_ in cols:
        body += f'<rect x="{cx_}" y="{y}" width="1" height="{30 + 6 * 30}" fill="#D9D1C3"/>'
    y += 30 + 6 * 30 + 36
    for lab in ["Total", "Advance", "Balance"]:
        body += t(F_SUB, lab, 14, 380, y, ink, 0.02, "end")
        body += f'<rect x="392" y="{y + 4}" width="{W - 432}" height="1" fill="{soft}"/>'
        y += 34
    body += t(F_SUB, "Delivery date ____________", 14, 40, y - 102, ink, 0.02)
    body += t(F_SUB, "Signature ______________", 14, 40, y - 34, ink, 0.02)
    body += f'<rect x="40" y="{H - 92}" width="{W - 80}" height="1" fill="{SONA}"/>'
    body += t(F_SUB, "Please bring this slip when collecting your order.", 12.5, W / 2, H - 66, soft, 0.02, "middle")
    body += t(F_SUB, f"{ADDRESS}  ·  {'  /  '.join(PHONES)}", 12.5, W / 2, H - 44, ink, 0.02, "middle", max_w=W - 80)
    return svg(W, H, body)


def build(out):
    files = {}
    files["dp/dp-badge-dark.svg"] = badge(SURMA, MALAI, SONA, MALAI)
    files["dp/dp-badge-light.svg"] = badge(MALAI, SURMA, SONA, SURMA)
    files["dp/dp-badge-mehndi.svg"] = badge(MEHNDI, MALAI, "#D9B77C", MALAI)
    files["dp/stamp-badge-black.svg"] = badge(None, BLACK, BLACK, BLACK)
    files["dp/dp-icon-circle.svg"] = dp_icon(SURMA, MALAI, SONA)
    for k, fn in ILLUSTRATIONS.items():
        files[f"illustrations/{k}-dark.svg"] = svg(200, 200, f'<rect width="200" height="200" fill="{SURMA}"/>' + fn(MALAI, SONA, SURMA))
        files[f"illustrations/{k}-light.svg"] = svg(200, 200, fn(SURMA, SONA, WHITE))
    for i, p in enumerate(POSTS, 1):
        files[f"social/post-{i}-{p['key']}.svg"] = service_post(p)
    for k, lab in HIGHLIGHTS:
        files[f"social/highlight-{lab.lower()}.svg"] = highlight(k, lab)
    files["social/facebook-cover-1640x624.svg"] = fb_cover()
    for name, kind, title, ur, date in ALBUMS:
        files[f"album-covers/{name}.svg"] = album(kind, title, ur, date)
    files["signboard/signboard-flex-12x3ft.svg"] = signboard()
    files["stationery/order-slip-a5.svg"] = order_slip()
    for k, v in files.items():
        p = os.path.join(out, k)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(v)
    return files


if __name__ == "__main__":
    print("\n".join(build(sys.argv[1])))
