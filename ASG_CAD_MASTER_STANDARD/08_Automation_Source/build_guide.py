"""
00_START_HERE.pdf - two-page picture guide (English + Roman Urdu).
Page 1: install in 2 minutes (CAD in-charge / team member).
Page 2: every new drawing in 6 steps, on an annotated preview of the A3 sheet.

Called by qa_validate.py (needs the rendered A3 preview); positions of the
callouts are read from the real title block in the master DXF.
"""

from pathlib import Path

import ezdxf
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

import asg_standard as S

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "00_START_HERE.pdf"

_F = "/usr/share/fonts/truetype/liberation/"
for name, f in (("G", "LiberationSans-Regular.ttf"), ("G-B", "LiberationSans-Bold.ttf"),
                ("G-I", "LiberationSans-Italic.ttf"), ("Mono", "LiberationMono-Regular.ttf")):
    pdfmetrics.registerFont(TTFont(name, _F + f))
pdfmetrics.registerFont(TTFont("Sym", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFontFamily("G", normal="G", bold="G-B", italic="G-I", boldItalic="G-B")

INK = colors.HexColor("#222222")
ACCENT = colors.HexColor("#1f5f8b")
SOFT = colors.HexColor("#eef3f7")
GREY = colors.HexColor("#5f6b75")
OK = colors.HexColor("#2e7d4f")
OK_SOFT = colors.HexColor("#e9f5ee")
W, H = landscape(A4)

EN = ParagraphStyle("en", fontName="G-B", fontSize=10.5, leading=13.2, textColor=INK)
UR = ParagraphStyle("ur", fontName="G-I", fontSize=9, leading=11.4, textColor=GREY)
SM = ParagraphStyle("sm", fontName="G", fontSize=8.6, leading=11, textColor=INK)
SMB = ParagraphStyle("smb", parent=SM, fontName="G-B")


def para(c, text, style, x, y_top, width):
    """Draw a paragraph with its top at y_top; return its height."""
    p = Paragraph(text, style)
    _w, h = p.wrap(width, 1000)
    p.drawOn(c, x, y_top - h)
    return h


def header(c, title, sub):
    c.setFillColor(INK)
    c.rect(0, H - 24 * mm, W, 24 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("G-B", 19)
    c.drawString(14 * mm, H - 13 * mm, title)
    c.setFont("G", 10)
    c.drawString(14 * mm, H - 19.5 * mm, sub)
    c.setFont("G-B", 8.5)
    c.drawRightString(W - 14 * mm, H - 13 * mm, S.COMPANY)
    c.setFont("G", 8)
    c.drawRightString(W - 14 * mm, H - 19.5 * mm, f"CAD Standard {S.STANDARD_REV}  |  {S.STANDARD_DATE}")


def footer(c, text):
    c.setFillColor(GREY)
    c.setFont("G", 7.5)
    c.drawString(14 * mm, 7 * mm, text)
    c.drawRightString(W - 14 * mm, 7 * mm, f"Page {c.getPageNumber()} of 2")


def badge(c, x, y, n, r=4.6 * mm, fill=ACCENT):
    c.setFillColor(fill)
    c.circle(x, y, r, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("G-B", 12 if r > 3.5 * mm else 9)
    c.drawCentredString(x, y - (4.2 if r > 3.5 * mm else 3.1), str(n))


def chip(c, x, y, text):
    c.setFont("Mono", 8.2)
    tw = c.stringWidth(text, "Mono", 8.2)
    c.setFillColor(SOFT)
    c.setStrokeColor(colors.HexColor("#b9c9d6"))
    c.roundRect(x, y - 1.6 * mm, tw + 4 * mm, 5.2 * mm, 1.2 * mm, stroke=1, fill=1)
    c.setFillColor(ACCENT)
    c.drawString(x + 2 * mm, y, text)
    return tw + 4 * mm


def keycap(c, x, y, keys):
    for i, k in enumerate(keys):
        c.setFont("G-B", 8.5)
        tw = c.stringWidth(k, "G-B", 8.5)
        c.setFillColor(colors.white)
        c.setStrokeColor(INK)
        c.roundRect(x, y - 1.7 * mm, tw + 4 * mm, 5.6 * mm, 1.2 * mm, stroke=1, fill=1)
        c.setFillColor(INK)
        c.drawString(x + 2 * mm, y, k)
        x += tw + 4 * mm
        if i < len(keys) - 1:
            c.setFont("G-B", 9)
            c.drawString(x + 1 * mm, y, "+")
            x += 4.5 * mm
    return x


def step_card(c, x, y_top, w, n, en, ur, chips=(), h_min=17 * mm):
    inner = w - 16 * mm
    h = 3.5 * mm + Paragraph(en, EN).wrap(inner, 1000)[1] + 1.2 * mm + Paragraph(ur, UR).wrap(inner, 1000)[1]
    h += (7 * mm if chips else 0) + 3.5 * mm
    h = max(h, h_min)
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.HexColor("#c9d3db"))
    c.roundRect(x, y_top - h, w, h, 2.2 * mm, stroke=1, fill=1)
    badge(c, x + 7.5 * mm, y_top - 8 * mm, n)
    yy = y_top - 3.5 * mm
    yy -= para(c, en, EN, x + 14 * mm, yy, inner)
    yy -= 1.2 * mm
    yy -= para(c, ur, UR, x + 14 * mm, yy, inner)
    if chips:
        cx = x + 14 * mm
        for t in chips:
            cx += chip(c, cx, yy - 5 * mm, t) + 2 * mm
    return h


def result_card(c, x, y_top, w, en, ur):
    inner = w - 10 * mm
    h = 4 * mm + Paragraph(en, SMB).wrap(inner, 1000)[1] + 1 * mm + Paragraph(ur, UR).wrap(inner, 1000)[1] + 3.5 * mm
    c.setFillColor(OK_SOFT)
    c.setStrokeColor(OK)
    c.roundRect(x, y_top - h, w, h, 2.2 * mm, stroke=1, fill=1)
    c.setFillColor(OK)
    c.setFont("Sym", 13)
    c.drawString(x + 3.2 * mm, y_top - 7.8 * mm, "✓")
    yy = y_top - 4 * mm
    yy -= para(c, en, SMB, x + 9 * mm, yy, inner)
    yy -= 1 * mm
    para(c, ur, UR, x + 9 * mm, yy, inner)
    return h


def column(c, x, y_top, w, tag, title, sub, steps, result):
    c.setFillColor(ACCENT)
    c.roundRect(x, y_top - 9.5 * mm, 9.5 * mm, 9.5 * mm, 1.5 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("G-B", 14)
    c.drawCentredString(x + 4.75 * mm, y_top - 7 * mm, tag)
    c.setFillColor(INK)
    c.setFont("G-B", 13)
    c.drawString(x + 12.5 * mm, y_top - 5 * mm, title)
    c.setFillColor(GREY)
    c.setFont("G-I", 9)
    c.drawString(x + 12.5 * mm, y_top - 9.3 * mm, sub)
    y = y_top - 13 * mm
    for i, (en, ur, chips) in enumerate(steps, 1):
        y -= step_card(c, x, y, w, i, en, ur, chips) + 3 * mm
    result_card(c, x, y, w, *result)


def page_install(c):
    header(c, "ASG CAD TEMPLATE  -  START HERE",
           "Install once in 2 minutes   |   Sirf ek dafa install karein - 2 minute")
    col_w = (W - 28 * mm - 10 * mm) / 2
    top = H - 31 * mm
    column(c, 14 * mm, top, col_w, "A", "CAD IN-CHARGE  -  ONCE", "Sirf CAD in-charge, sirf ek dafa", [
        ("Extract the zip: right-click &gt; <b>Extract All</b>.",
         "Zip ko pehle extract karein. Zip ke andar se file na kholein.", ()),
        ("Double-click the template - it opens in AutoCAD.",
         "Is file par double-click karein - AutoCAD mein khul jayegi.",
         ("01_Master_Template\\ASG_Master_Template.dxf",)),
        ("Drag the installer from the same folder into the AutoCAD window. "
         "If AutoCAD asks, click <b>Load Once</b>.",
         "Isi folder se yeh file AutoCAD ke andar drag karein. Sawal aaye to 'Load Once' dabayein.",
         ("ASG_Install.lsp",)),
    ], ("A window says ASG INSTALL COMPLETE: print setting installed, template saved, Ctrl+N uses it, "
        "and the folder 09_Team_Kit is ready for your team.",
        "Popup mein 'ASG INSTALL COMPLETE' aayega. Bas - template tayyar, aur team ke liye 09_Team_Kit "
        "folder bhi tayyar."))
    column(c, 14 * mm + col_w + 10 * mm, top, col_w, "B", "EACH TEAM MEMBER  -  ONCE PER PC",
           "Har team member, apne PC par ek dafa", [
               ("Copy the folder <b>09_Team_Kit</b> to your PC (or open it on the shared drive).",
                "09_Team_Kit folder apne PC par copy karein (ya shared drive se kholein).", ()),
               ("Open AutoCAD and drag the installer from the kit into the window. "
                "Click <b>Load Once</b> if asked.",
                "AutoCAD kholein aur kit se yeh file andar drag karein. 'Load Once' dabayein.",
                ("ASG_Install.lsp",)),
               ("When asked, select the template from the kit folder.",
                "Jab file maange, kit folder se template chunein.",
                ("ASG_Master_Template.dwt",)),
           ], ("ASG INSTALL COMPLETE. Press Ctrl+N - every new drawing starts from the company template.",
               "Ctrl+N dabayein - har nayi drawing company template se shuru hogi."))
    # help band
    y = 22 * mm
    c.setFillColor(SOFT)
    c.roundRect(14 * mm, y - 9 * mm, W - 28 * mm, 15 * mm, 2 * mm, stroke=0, fill=1)
    para(c, "<b>If a step says NOT DONE</b>, the window tells you exactly what to do by hand. "
            "Still stuck? Send <b>ASG_QA_Log.txt</b> (next to the template) or a screenshot of the "
            "command line (F2) to the CAD in-charge.", SM, 18 * mm, y + 4.6 * mm, W - 36 * mm)
    para(c, "Koi step 'NOT DONE' dikhaye to popup mein likha hai haath se kya karna hai. Phir bhi masla ho to "
            "ASG_QA_Log.txt ya F2 ka screenshot CAD in-charge ko bhejein.", UR, 18 * mm, y - 2.2 * mm, W - 36 * mm)
    footer(c, "ASG CAD Master Standard - 00_START_HERE.pdf")


def page_daily(c, preview_png, master_dxf):
    header(c, "EVERY NEW DRAWING  -  6 STEPS",
           "Har nayi drawing - 6 aasaan steps   |   Rules: ASG_CAD_Quick_SOP.pdf")
    # annotated A3 preview
    img_w = 170 * mm
    img_h = img_w * 297 / 420
    ix, iy = 12 * mm, H - 31 * mm - img_h
    c.setStrokeColor(colors.HexColor("#c9d3db"))
    c.rect(ix - 1, iy - 1, img_w + 2, img_h + 2, stroke=1, fill=0)
    c.drawImage(str(preview_png), ix, iy, img_w, img_h)
    k = img_w / (420 * mm)

    def at(xmm, ymm):
        return ix + xmm * mm * k, iy + ymm * mm * k

    doc = ezdxf.readfile(master_dxf)
    sheet = next(s for s in S.SHEETS if s[0] == "A3-LANDSCAPE")
    _n, sw, sh, _p, tb, _v = sheet
    base = (sw - S.MARGIN, S.MARGIN)
    pos = {a.dxf.tag: a.dxf.insert for a in doc.blocks.get(tb).query("ATTDEF")}
    vx1, vy1, vx2, vy2 = S.viewport_rect(sheet[0], sw, sh, tb)
    marks = {
        2: ((vx1 + vx2) / 2, (vy1 + vy2) / 2),
        3: (vx1 + 4, vy1 + 4),
        4: (base[0] + pos["PROJECT"].x + 40, base[1] + pos["PROJECT"].y + 2),
        5: (base[0] + pos["REV1_DESC"].x + 20, base[1] + pos["REV1_DESC"].y + 1),
    }
    for n, (xm, ym) in marks.items():
        badge(c, *at(xm, ym), n, r=3.6 * mm, fill=colors.HexColor("#c0392b"))
    c.setFillColor(GREY)
    c.setFont("G-I", 8)
    c.drawString(ix, iy - 5 * mm, "A3-LANDSCAPE sheet as it comes from the template (title strip on the right).")

    # steps
    sx, sw_ = ix + img_w + 9 * mm, W - (ix + img_w + 9 * mm) - 12 * mm
    y = H - 31 * mm
    steps = [
        (1, "New drawing", "Every drawing starts from the template.",
         "Har drawing template se shuru karein.", ["Ctrl", "N"]),
        (2, "Draw 1:1 in mm on ASG layers", "Model tab, real size. Pick the layer first (SOP table 2).",
         "Model tab mein asal size mein draw karein; pehle sahi layer chunein.", None),
        (3, "Sheet: scale + lock", "Open a sheet tab, click the viewport edge, choose the scale "
         "(bottom right), then click the lock.",
         "Sheet tab kholein, viewport ka scale chunein aur lock (taala) laga dein.", None),
        (4, "Fill the title strip", "Double-click the title strip: project, title, drawing number, "
         "date, names, status.",
         "Title strip par double-click karke saari details bharein.", None),
        (5, "Revisions", "Every change: next row in the revision table + a cloud on ASG-REVISION.",
         "Har tabdeeli par revision table ki agli row bharein aur cloud lagayein.", None),
        (6, "Print to PDF and check it", "Everything is preset. Open the PDF and check before you send it.",
         "Sab settings tayyar hain. PDF khol kar check karein, phir bhejein.", ["Ctrl", "P"]),
    ]
    for n, title, en, ur, keys in steps:
        badge(c, sx + 4.6 * mm, y - 4.6 * mm, n, fill=colors.HexColor("#c0392b") if n in marks else ACCENT)
        c.setFillColor(INK)
        c.setFont("G-B", 11)
        c.drawString(sx + 12 * mm, y - 6 * mm, title)
        if keys:
            keycap(c, sx + 12 * mm + c.stringWidth(title, "G-B", 11) + 3 * mm, y - 6 * mm, keys)
        yy = y - 9 * mm
        yy -= para(c, en, SM, sx + 12 * mm, yy, sw_ - 12 * mm)
        yy -= para(c, ur, UR, sx + 12 * mm, yy - 0.6 * mm, sw_ - 12 * mm) + 0.6 * mm
        y = yy - 1.8 * mm
    band_top = 29 * mm
    assert y >= band_top + 1 * mm, f"guide page 2: steps overlap the rules band ({y / mm:.1f} mm)"
    en = ("<b>Golden rules:</b> never draw on layer 0 &nbsp;|&nbsp; never type over a dimension value "
          "&nbsp;|&nbsp; keep viewports locked &nbsp;|&nbsp; never explode or move the title strip &nbsp;|&nbsp; "
          "objects stay ByLayer &nbsp;|&nbsp; no new layers or styles without the CAD in-charge.")
    ur = ("Layer 0 par kuch na banayein - dimension ka number haath se na badlein - viewport hamesha lock "
          "rakhein - title strip ko explode na karein - nayi layer/style sirf CAD in-charge se pooch kar.")
    tw = W - 32 * mm
    hb = 2.5 * mm + Paragraph(en, SM).wrap(tw, 1000)[1] + 1.2 * mm + Paragraph(ur, UR).wrap(tw, 1000)[1] + 2.5 * mm
    assert band_top - hb >= 11 * mm, "guide page 2: rules band runs into the footer"
    c.setFillColor(SOFT)
    c.roundRect(12 * mm, band_top - hb, W - 24 * mm, hb, 2 * mm, stroke=0, fill=1)
    yy = band_top - 2.5 * mm
    yy -= para(c, en, SM, 16 * mm, yy, tw) + 1.2 * mm
    para(c, ur, UR, 16 * mm, yy, tw)
    footer(c, "ASG CAD Master Standard - 00_START_HERE.pdf")


def build(preview_png, master_dxf):
    c = canvas.Canvas(str(OUT), pagesize=landscape(A4))
    c.setTitle("ASG CAD Template - Start Here")
    c.setAuthor(S.COMPANY)
    page_install(c)
    c.showPage()
    page_daily(c, preview_png, master_dxf)
    c.showPage()
    c.save()
    return OUT
