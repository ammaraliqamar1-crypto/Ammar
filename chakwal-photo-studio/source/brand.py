"""Chakwal Photo Studio - logo generator.
Builds the mark, outlines all lettering (English + Urdu) to SVG paths so files
print correctly anywhere without fonts installed."""
import math, os, sys
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- Brand colours -------------------------------------------------------
SURMA = "#26231F"   # deep charcoal
MALAI = "#F4EDE0"   # warm ivory
SONA = "#B08D57"    # muted gold
MEHNDI = "#6E2B2A"  # henna maroon (wedding accent)
BLACK, WHITE = "#000000", "#FFFFFF"


def fmt(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


class Font:
    def __init__(self, path):
        self.tt = TTFont(path)
        self.face = hb.Face(hb.Blob.from_file_path(path))
        self.hb = hb.Font(self.face)
        self.upem = self.face.upem
        self.gs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()

    def _shape(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {})
        return buf.glyph_infos, buf.glyph_positions

    def width(self, text, size, track=0.0):
        infos, pos = self._shape(text)
        return sum(p.x_advance for p in pos) * size / self.upem + track * size * (len(infos) - 1)

    def _draw(self, pen, text, size, x, y, track):
        infos, pos = self._shape(text)
        sc = size / self.upem
        cx = x
        for inf, p in zip(infos, pos):
            tp = TransformPen(pen, (sc, 0, 0, -sc, cx + p.x_offset * sc, y - p.y_offset * sc))
            self.gs[self.order[inf.codepoint]].draw(tp)
            cx += p.x_advance * sc + track * size

    def bounds(self, text, size, x=0, y=0, track=0.0):
        bp = BoundsPen(self.gs)
        self._draw(bp, text, size, x, y, track)
        return bp.bounds  # xmin, ymin(top in svg since flipped), xmax, ymax

    def path(self, text, size, x, y, track=0.0, anchor="start"):
        w = self.width(text, size, track)
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        pen = SVGPathPen(self.gs, ntos=fmt)
        self._draw(pen, text, size, x, y, track)
        return pen.getCommands()


F_DISPLAY = Font(os.path.join(HERE, "fonts/Marcellus.ttf"))
F_SUB = Font(os.path.join(HERE, "fonts/Jost500.ttf"))
F_URDU = Font(os.path.join(HERE, "fonts/Nastaliq600.ttf"))

NAME = "CHAKWAL"
SUB = "PHOTO STUDIO"
URDU = "چکوال فوٹو اسٹوڈیو"
URDU_NAME = "چکوال"
URDU_SUB = "فوٹو اسٹوڈیو"


# ---- The mark: "Darwaza" ---------------------------------------------------
# 200 x 200 grid. Focus-frame corners + doorway arch + Potohar ridge + sunrise.
_CLIP = [0]


def mark(line, sun, sw=7, x=0, y=0, s=1.0, ridge_sw=None):
    """The 'Darwaza camera': a camera whose top is the arched doorway of a
    Punjabi home, with the sun rising over the Potohar ridge inside the lens."""
    rs = ridge_sw or sw * 0.8
    _CLIP[0] += 1
    lens, sun_c = f"lens{_CLIP[0]}", f"sunrise{_CLIP[0]}"
    lr = 41 - sw / 2  # inner radius of the lens ring
    t = f' transform="translate({fmt(x)} {fmt(y)}) scale({s:g})"' if (x or y or s != 1) else ""
    return f"""<g{t} fill="none" stroke="{line}" stroke-linecap="round" stroke-linejoin="round">
  <clipPath id="{lens}"><circle cx="100" cy="116" r="{fmt(lr)}"/></clipPath>
  <clipPath id="{sun_c}"><polygon points="50 60 150 60 150 114 141 114 124 106 115 110 107 103 89 103 78 112 70 109 58 115 50 115"/></clipPath>
  <path stroke-width="{fmt(sw)}" d="M36 60H70V54A30 30 0 0 1 130 54V60H164A20 20 0 0 1 184 80V150A20 20 0 0 1 164 170H36A20 20 0 0 1 16 150V80A20 20 0 0 1 36 60Z"/>
  <path stroke-width="{fmt(sw)}" d="M30 60V51H52V60"/>
  <circle cx="161" cy="83" r="{fmt(max(3.5, sw * 0.62))}" fill="{line}" stroke="none"/>
  <circle cx="100" cy="116" r="41" stroke-width="{fmt(sw)}"/>
  <g clip-path="url(#{lens})">
    <g clip-path="url(#{sun_c})"><circle cx="98" cy="107" r="17" fill="{sun}" stroke="none"/></g>
    <path stroke-width="{fmt(rs)}" d="M52 123L70 116L78 119L90 109H106L115 116L124 112L148 122"/>
    <path stroke-width="{fmt(rs)}" d="M52 138C74 131 96 138 116 134C128 132 138 130 148 132"/>
  </g>
</g>"""


def svg(w, h, body, bg=None, defs=""):
    rect = f'<rect width="100%" height="100%" fill="{bg}"/>' if bg else ""
    d = f"<defs>{defs}</defs>" if defs else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fmt(w)} {fmt(h)}" '
            f'width="{fmt(w)}" height="{fmt(h)}">{d}{rect}{body}</svg>')


# ---- Lockup geometry --------------------------------------------------------
NAME_SIZE, NAME_TRACK = 96, 0.045
NAME_W = F_DISPLAY.width(NAME, NAME_SIZE, NAME_TRACK)
SUB_SIZE = 38
_sub_raw = F_SUB.width(SUB, SUB_SIZE)
SUB_TRACK = (NAME_W - _sub_raw) / (SUB_SIZE * (len(SUB) - 1))  # justify to CHAKWAL


def horizontal(line, sun, word, sub, rule, bg=None, urdu=False):
    x0 = 236
    body = mark(line, sun)
    body += f'<path fill="{word}" d="{F_DISPLAY.path(NAME, NAME_SIZE, x0, 116, NAME_TRACK)}"/>'
    body += f'<rect x="{fmt(x0)}" y="133" width="{fmt(NAME_W)}" height="2.5" fill="{rule}"/>'
    body += f'<path fill="{sub}" d="{F_SUB.path(SUB, SUB_SIZE, x0, 177, SUB_TRACK)}"/>'
    w = x0 + NAME_W + 16
    if urdu:
        dx = w + 26
        body += f'<rect x="{fmt(dx)}" y="40" width="2.5" height="120" fill="{rule}"/>'
        ux = dx + 40
        # stack the two Nastaliq lines by their real ink height so nothing leaves the 200-unit canvas
        n1, n2, gap, top, room = 74.0, 40.0, 6.0, 8.0, 184.0
        b1, b2 = F_URDU.bounds(URDU_NAME, n1, 0, 0), F_URDU.bounds(URDU_SUB, n2, 0, 0)
        k = min(1.0, room / ((b1[3] - b1[1]) + gap + (b2[3] - b2[1])))
        n1, n2 = n1 * k, n2 * k
        b1, b2 = F_URDU.bounds(URDU_NAME, n1, 0, 0), F_URDU.bounds(URDU_SUB, n2, 0, 0)
        y1 = top - b1[1]
        y2 = y1 + b1[3] + gap - b2[1]
        uw = max(F_URDU.width(URDU_NAME, n1), F_URDU.width(URDU_SUB, n2))
        body += f'<path fill="{word}" d="{F_URDU.path(URDU_NAME, n1, ux + uw / 2, y1, anchor="middle")}"/>'
        body += f'<path fill="{sub}" d="{F_URDU.path(URDU_SUB, n2, ux + uw / 2, y2, anchor="middle")}"/>'
        w = ux + uw + 16
    return svg(w, 200, body, bg)


def stacked(line, sun, word, sub, rule, bg=None, urdu=True):
    W = NAME_W + 40
    cx = W / 2
    body = mark(line, sun, x=cx - 100, y=0)
    nx = cx - NAME_W / 2
    body += f'<path fill="{word}" d="{F_DISPLAY.path(NAME, NAME_SIZE, nx, 300, NAME_TRACK)}"/>'
    body += f'<rect x="{fmt(nx)}" y="317" width="{fmt(NAME_W)}" height="2.5" fill="{rule}"/>'
    body += f'<path fill="{sub}" d="{F_SUB.path(SUB, SUB_SIZE, nx, 362, SUB_TRACK)}"/>'
    h = 380
    if urdu:
        body += f'<path fill="{word}" d="{F_URDU.path(URDU, 40, cx, 430, anchor="middle")}"/>'
        h = 470
    return svg(W, h, body, bg)


def icon(line, sun, bg, round_=False, size=512):
    s = size / 200 * 0.72
    off = (size - 200 * s) / 2
    shape = (f'<circle cx="{size/2}" cy="{size/2}" r="{size/2}" fill="{bg}"/>' if round_
             else f'<rect width="{size}" height="{size}" fill="{bg}"/>')
    return svg(size, size, shape + mark(line, sun, sw=9, x=off, y=off, s=s))


def watermark(color, opacity=1.0):
    # one-line mark + name, for photo corners
    body = f'<g opacity="{opacity}">' + mark(color, color, sw=9, s=0.6)
    tx = 140
    body += f'<path fill="{color}" d="{F_DISPLAY.path(NAME, 50, tx, 70, 0.06)}"/>'
    nw = F_DISPLAY.width(NAME, 50, 0.06)
    tr = (nw - F_SUB.width(SUB, 16)) / (16 * (len(SUB) - 1))
    body += f'<path fill="{color}" d="{F_SUB.path(SUB, 16, tx, 100, tr)}"/></g>'
    return svg(tx + nw + 6, 120, body)


FILES = {
    "logo-primary.svg": horizontal(SURMA, SONA, SURMA, SURMA, SONA),
    "logo-primary-on-dark.svg": horizontal(MALAI, SONA, MALAI, MALAI, SONA, bg=SURMA),
    "logo-bilingual-signboard.svg": horizontal(MALAI, SONA, MALAI, MALAI, SONA, bg=SURMA, urdu=True),
    "logo-stacked.svg": stacked(SURMA, SONA, SURMA, SURMA, SONA),
    "logo-stacked-on-dark.svg": stacked(MALAI, SONA, MALAI, MALAI, SONA, bg=SURMA),
    "logo-black.svg": horizontal(BLACK, BLACK, BLACK, BLACK, BLACK),
    "logo-white.svg": horizontal(WHITE, WHITE, WHITE, WHITE, WHITE, bg=BLACK),
    "mark-only.svg": svg(200, 200, mark(SURMA, SONA)),
    "icon-whatsapp-facebook.svg": icon(MALAI, SONA, SURMA),
    "watermark-white.svg": watermark(WHITE),
    "watermark-black.svg": watermark(BLACK),
}

if __name__ == "__main__":
    OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out")
    os.makedirs(OUT, exist_ok=True)
    for name, content in FILES.items():
        with open(os.path.join(OUT, name), "w") as f:
            f.write(content)
    print("SUB_TRACK", round(SUB_TRACK, 3), "NAME_W", round(NAME_W, 1))
    print("\n".join(sorted(FILES)))
