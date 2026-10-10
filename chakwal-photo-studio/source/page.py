"""Builds the brand presentation page from the outlined logo artwork."""
import math, re, sys
from brand import (mark, horizontal, stacked, icon, watermark, svg, fmt,
                   SURMA, MALAI, SONA, MEHNDI, BLACK, WHITE, F_DISPLAY, F_SUB, NAME, SUB)

OUT = sys.argv[1]


def inline(s, cls=""):
    s = re.sub(r'^<svg([^>]*?) width="[^"]*" height="[^"]*"', r'<svg\1', s, count=1)
    return s.replace("<svg ", f'<svg class="{cls}" role="img" aria-label="Chakwal Photo Studio logo" ', 1)


FOIL = ('<linearGradient id="{id}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="200" y2="200">'
        '<stop offset="0" stop-color="#E3C58C"/><stop offset=".45" stop-color="#B08D57"/>'
        '<stop offset=".7" stop-color="#F0D9A8"/><stop offset="1" stop-color="#9C7A45"/></linearGradient>')

# ---- Concept sketches -------------------------------------------------------
concept_a = svg(200, 200, f"""<g fill="none" stroke="{SURMA}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round">
<path d="M36 172V100A64 64 0 0 1 164 100V172"/><path d="M60 172V106A40 40 0 0 1 140 106V172"/>
<path d="M84 172V114A16 16 0 0 1 116 114V172" stroke="{SONA}"/><path d="M24 172H176"/></g>""")

# aperture: hexagon opening + blade edges
pts = [(100 + 46 * math.cos(math.radians(a - 90)), 100 + 46 * math.sin(math.radians(a - 90))) for a in range(0, 360, 60)]
blades = ""
for i in range(6):
    (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % 6]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    # extend from vertex i backwards until the circle r=78
    b = ux * (x1 - 100) + uy * (y1 - 100)
    c = (x1 - 100) ** 2 + (y1 - 100) ** 2 - 78 ** 2
    t = -b - math.sqrt(b * b - c)
    blades += f"M{fmt(x1)} {fmt(y1)}L{fmt(x1 + ux * t)} {fmt(y1 + uy * t)}"
hexp = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in pts)
concept_b = svg(200, 200, f"""<defs><clipPath id="hexclip"><polygon points="{hexp}"/></clipPath></defs>
<g fill="none" stroke="{SURMA}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
<circle cx="100" cy="100" r="84"/><path d="{blades}" stroke-width="4"/><polygon points="{hexp}"/>
<g clip-path="url(#hexclip)"><circle cx="100" cy="98" r="13" fill="{SONA}" stroke="none"/>
<path d="M50 124L72 112L84 117L96 106H108L120 115L150 110"/></g></g>""")

concept_c = f"""<svg viewBox="0 0 200 200" role="img" aria-label="Concept C seal"><defs><path id="ring" d="M100 100m-70 0a70 70 0 1 1 140 0a70 70 0 1 1 -140 0"/></defs>
<circle cx="100" cy="100" r="92" fill="none" stroke="{SURMA}" stroke-width="3"/>
<circle cx="100" cy="100" r="54" fill="none" stroke="{SONA}" stroke-width="2"/>
<text font-family="Jost, sans-serif" font-weight="500" font-size="13.5" letter-spacing="4.2" fill="{SURMA}"><textPath href="#ring">CHAKWAL • PHOTO STUDIO • PINDI ROAD •</textPath></text>
<text x="100" y="118" text-anchor="middle" font-family="Marcellus, serif" font-size="52" fill="{SURMA}">C<tspan font-size="30" dy="-4" fill="{SONA}">P</tspan><tspan font-size="30" dy="0">S</tspan></text></svg>"""

# ---- Final artwork ---------------------------------------------------------
primary = horizontal(SURMA, SONA, SURMA, SURMA, SONA)
primary_dark = horizontal(MALAI, SONA, MALAI, MALAI, SONA)
sign = horizontal(MALAI, SONA, MALAI, MALAI, SONA, urdu=True)
stack = stacked(SURMA, SONA, SURMA, SURMA, SONA)
stack_dark = stacked(MALAI, SONA, MALAI, MALAI, SONA)
mono_black = horizontal(BLACK, BLACK, BLACK, BLACK, BLACK)
mono_white = horizontal(WHITE, WHITE, WHITE, WHITE, WHITE)
mk = svg(200, 200, mark(SURMA, SONA))
mk_dark = svg(200, 200, mark(MALAI, SONA))
mk_black = svg(200, 200, mark(BLACK, BLACK, sw=9))
mk_white = svg(200, 200, mark(WHITE, WHITE, sw=9))
app_icon = icon(MALAI, SONA, SURMA, round_=True)
wm_white = watermark(WHITE)
wm_black = watermark(BLACK)
foil_mark = svg(200, 200, mark("url(#foilA)", "url(#foilA)", sw=6), defs=FOIL.format(id="foilA"))
FOOT = "CHAKWAL PHOTO STUDIO"
nw = F_DISPLAY.width(FOOT, 40, 0.12)
foil_word = svg(nw + 4, 50, f'<path fill="url(#foilB)" d="{F_DISPLAY.path(FOOT, 40, 2, 34, 0.12)}"/>',
                defs=FOIL.format(id="foilB").replace('x2="200" y2="200"', f'x2="{fmt(nw)}" y2="50"'))

# Illustrated sample "photograph": Potohar evening
scene = """<svg viewBox="0 0 600 400" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3E4A66"/><stop offset=".55" stop-color="#D58A5A"/><stop offset="1" stop-color="#F2C98B"/></linearGradient>
<radialGradient id="sunglow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#FFF1C9"/><stop offset=".35" stop-color="#FBD38D" stop-opacity=".9"/><stop offset="1" stop-color="#FBD38D" stop-opacity="0"/></radialGradient></defs>
<rect width="600" height="400" fill="url(#sky)"/><circle cx="330" cy="236" r="120" fill="url(#sunglow)"/><circle cx="330" cy="236" r="30" fill="#FFF0C8"/>
<path d="M0 250L60 226L110 236L170 204H240L290 230L350 214L420 238L470 222L530 240L600 228V400H0Z" fill="#8C5A48"/>
<path d="M0 286C90 266 170 284 260 276C350 268 430 262 600 270V400H0Z" fill="#5E3D36"/>
<path d="M0 330C120 314 260 330 380 318C470 310 540 316 600 312V400H0Z" fill="#3B2A27"/>
<g fill="#2A1E1C"><circle cx="190" cy="300" r="7"/><path d="M181 340Q190 306 199 340Z"/><circle cx="208" cy="304" r="6"/><path d="M200 340Q208 310 216 340Z"/><circle cx="225" cy="314" r="4.5"/><path d="M219 340Q225 318 231 340Z"/></g></svg>"""

TOKENS = {
    "PRIMARY": inline(primary, "art"), "PRIMARY_DARK": inline(primary_dark, "art"),
    "SIGN": inline(sign, "art"), "STACK": inline(stack, "art"), "STACK_DARK": inline(stack_dark, "art"),
    "MONO_BLACK": inline(mono_black, "art"), "MONO_WHITE": inline(mono_white, "art"),
    "MARK": inline(mk, "art"), "MARK_DARK": inline(mk_dark, "art"),
    "MARK_BLACK": inline(mk_black, "art"), "MARK_WHITE": inline(mk_white, "art"),
    "APP_ICON": inline(app_icon, "art"), "WM_WHITE": inline(wm_white, "art"), "WM_BLACK": inline(wm_black, "art"),
    "FOIL_MARK": inline(foil_mark, "art"), "FOIL_WORD": inline(foil_word, "art"),
    "CONCEPT_A": inline(concept_a, "art"), "CONCEPT_B": inline(concept_b, "art"), "CONCEPT_C": concept_c.replace("<svg ", '<svg class="art" ', 1),
    "SCENE": scene,
}

html = open("template.html").read()
for k, v in TOKENS.items():
    html = html.replace("{{" + k + "}}", v)
left = re.findall(r"\{\{[A-Z_]+\}\}", html)
assert not left, left
open(OUT, "w").write(html)
print("wrote", OUT, len(html) // 1024, "KB")
