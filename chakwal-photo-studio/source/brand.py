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
    rs = ridge_sw or sw * 0.82
    _CLIP[0] += 1
    cid = f"sunrise{_CLIP[0]}"
    t = f' transform="translate({fmt(x)} {fmt(y)}) scale({s:g})"' if (x or y or s != 1) else ""
    return f"""<g{t} fill="none" stroke="{line}" stroke-linecap="round" stroke-linejoin="round">
  <clipPath id="{cid}"><polygon points="40 40 160 40 160 120 144 120 129 112 118 116 108 108 94 108 81 120 71 116 40 136"/></clipPath>
  <path stroke-width="{fmt(sw)}" d="M16 50V16H50M150 16H184V50M184 150V184H150M50 184H16V150"/>
  <path stroke-width="{fmt(sw)}" d="M56 162V98A44 44 0 0 1 144 98V162Z"/>
  <path stroke-width="{fmt(rs)}" d="M56 133L71 123L81 127L94 115H108L118 123L129 119L144 127"/>
  <path stroke-width="{fmt(rs)}" d="M56 149C75 141 93 147 110 144C123 142 133 139 144 141"/>
  <circle cx="101" cy="107" r="19.5" fill="{sun}" stroke="none" clip-path="url(#{cid})"/>
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
        uw1 = F_URDU.width(URDU_NAME, 74)
        uw2 = F_URDU.width(URDU_SUB, 40)
        uw = max(uw1, uw2)
        body += f'<path fill="{word}" d="{F_URDU.path(URDU_NAME, 74, ux + uw / 2, 108, anchor="middle")}"/>'
        body += f'<path fill="{sub}" d="{F_URDU.path(URDU_SUB, 40, ux + uw / 2, 166, anchor="middle")}"/>'
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
