"""
One-page drafting SOP (A4) for every draftsman - generated from
asg_standard.py so every layer / style name on it exists in the template.

    python build_sop.py        (also run by qa_validate.py)
Output: 05_CAD_Standards_Documentation/ASG_CAD_Quick_SOP.pdf
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle

import asg_standard as S

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "05_CAD_Standards_Documentation" / "ASG_CAD_Quick_SOP.pdf"
SOP_NO, SOP_REV = "ASG-SOP-CAD-001", "0"

_FONTS = "/usr/share/fonts/truetype"
pdfmetrics.registerFont(TTFont("Sans", f"{_FONTS}/liberation/LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Sans-Bold", f"{_FONTS}/liberation/LiberationSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Sym", f"{_FONTS}/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-Bold", italic="Sans", boldItalic="Sans-Bold")
BOX = '<font name="Sym">☐</font>'

DARK = colors.HexColor("#2b2b2b")
GRID = colors.HexColor("#9a9a9a")
SHADE = colors.HexColor("#ececec")

LAYER_GUIDE = [  # what you draw -> layer (all names verified against S.LAYERS)
    ("Frame / panel / opening outline (elevation, plan)", "ASG-OUTLINE-PRIMARY"),
    ("Edges beyond, minor lines", "ASG-OUTLINE-SECONDARY"),
    ("Aluminium profiles, beads", "ASG-ALUMINIUM-PROFILE"),
    ("Glass, mirror", "ASG-GLASS"),
    ("Mild steel / stainless steel", "ASG-MILD-STEEL / ASG-STAINLESS-STEEL"),
    ("Hardware / anchors, screws, brackets", "ASG-HARDWARE / ASG-FIXING"),
    ("Gaskets / silicone, backer rod", "ASG-GASKET / ASG-SEALANT"),
    ("Insulation, thermal break", "ASG-INSULATION"),
    ("ACP / panels, flashings", "ASG-CLADDING"),
    ("Outline of material cut in a section", "ASG-SECTION-CUT"),
    ("Hatch / solid fill in sections", "ASG-HATCH / ASG-HATCH-FILL"),
    ("Hidden edges / centrelines", "ASG-HIDDEN / ASG-CENTERLINE"),
    ("Section cut line / section & detail marks", "ASG-CUTTING-PLANE / ASG-SYMBOL"),
    ("Setting-out lines that must print", "ASG-SETOUT"),
    ("Architect / consultant background (xref)", "ASG-REFERENCE"),
    ("Helper lines - NOT printed", "ASG-CONSTRUCTION"),
    ("Notes / leaders / tables / levels / grids", "ASG-TEXT-NOTE / ASG-MULTILEADER / ASG-TABLE / ASG-LEVEL / ASG-GRID"),
    ("Revision cloud + delta", "ASG-REVISION"),
    ("Reminders for yourself - NOT printed", "ASG-NOPLOT"),
]


def _check_names():
    layers = {l[1] for l in S.LAYERS}
    for _what, names in LAYER_GUIDE:
        for n in names.split(" / "):
            assert n in layers, f"SOP names unknown layer {n}"


def build(font_size=7.6):
    _check_names()
    fs, ld = font_size, font_size * 1.22
    P = ParagraphStyle("p", fontName="Sans", fontSize=fs, leading=ld, spaceAfter=0.6)
    B = ParagraphStyle("b", parent=P, leftIndent=8, bulletIndent=0)
    H = ParagraphStyle("h", fontName="Sans-Bold", fontSize=fs + 1.2, leading=fs + 3, textColor=colors.white,
                       backColor=DARK, borderPadding=(1.6, 3, 1.6, 3), spaceBefore=5, spaceAfter=3.5)
    C = ParagraphStyle("c", parent=P, fontSize=fs - 0.6, leading=(fs - 0.6) * 1.18, spaceAfter=0)
    CB = ParagraphStyle("cb", parent=C, fontName="Sans-Bold")

    def h(t):
        return Paragraph(t, H)

    def steps(items):
        return [Paragraph(f"<b>{i}.</b> {t}", B, bulletText=None) for i, t in enumerate(items, 1)]

    def bullets(items, mark="•"):
        return [Paragraph(t, B, bulletText=mark) for t in items]

    def checks(items):
        return [Paragraph(f"{BOX} {t}", B) for t in items]

    def table(rows, widths, head=True):
        t = Table([[Paragraph(c, CB if (head and r == 0) else C) for c in row] for r, row in enumerate(rows)],
                  colWidths=[w * mm for w in widths], hAlign="LEFT")
        st = [("GRID", (0, 0), (-1, -1), 0.3, GRID), ("VALIGN", (0, 0), (-1, -1), "TOP"),
              ("TOPPADDING", (0, 0), (-1, -1), 0.8), ("BOTTOMPADDING", (0, 0), (-1, -1), 0.8),
              ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2)]
        if head:
            st.append(("BACKGROUND", (0, 0), (-1, 0), SHADE))
        t.setStyle(TableStyle(st))
        return t

    col_w = (A4[0] - 20 * mm - 6 * mm) / 2 / mm  # frame width in mm
    dims = {n: u for n, _a, _o, u in S.DIM_STYLES}
    vp_scales = ", ".join(f"1:{s}" for s in S.ANNO_SCALES)
    fmt = dict(S.NUMBERING)

    story = []
    # ---------------- column 1
    story += [h("1. EVERY NEW DRAWING - STEP BY STEP")]
    story += steps([
        "<b>NEW</b> &gt; <b>ASG_Master_Template.dwt</b>. Never start from acad.dwt or an old project file.",
        "Save at once with the correct name: <b>drawing number + rev + short project name</b>, "
        f"e.g. {fmt['Example'].split('file ')[-1]}",
        "Draw in the <b>Model</b> tab, <b>full size 1:1 in millimetres</b>. A 2400 mm opening is drawn 2400 long.",
        "Pick the correct <b>layer</b> before drawing (table 2). Never draw on layer 0.",
        "Open the sheet tab you need: " + ", ".join(s[0] for s in S.SHEETS) + ". Delete the tabs you do not use.",
        f"Unlock the viewport, set its scale from the list ({vp_scales}), <b>lock</b> it again.",
        "Double-click inside the viewport and add notes, dimensions and leaders with the ASG styles "
        "(table 3). Type the <b>paper height</b> (2.5) - AutoCAD sizes it for the viewport scale.",
        "Double-click the title block and fill every field. Never explode or move it.",
        "Plot: the page setup is ready (DWG To PDF, A-size paper, 1:1, " + S.CTB_NAME + "). Click Plot, "
        "then <b>open the PDF and check it</b>.",
    ])
    story += [h("2. WHAT GOES ON WHICH LAYER")]
    story += [table([["What you draw", "Layer"]] + [list(r) for r in LAYER_GUIDE], (col_w * 0.48, col_w * 0.52))]
    story += [Paragraph("Colours on screen show the job of the line; on paper everything prints black "
                        "(hatch, insulation and background print grey). Line thickness comes from the layer - "
                        "never change colour, linetype or lineweight of an object (keep <b>ByLayer</b>).", P)]
    story += [h("3. WHICH STYLE TO USE")]
    story += [table([
        ["Item", "Style", "Use"],
        ["Dimension", "ASG-DIM-ANNO", "Normal dims - whole mm (1200)"],
        ["Dimension", "ASG-DIM-DETAIL", "Fabrication details - 0.0 (50.0)"],
        ["Dimension", "ASG-DIM-ANGULAR / -RADIUS / -DIAMETER", "30.00 deg / R40 / Ø80"],
        ["Dimension", "ASG-DIM-FIXED", "Only when dimensioning in the layout tab"],
        ["Leader", "ASG-ML-ANNO / -DETAIL / -REFERENCE", "Normal / dense detail / 'see drawing ...'"],
        ["Note text", "ASG-TEXT-NOTE 2.5  (small: ASG-TEXT-SMALL 1.8)", "Model tab"],
        ["Titles", "ASG-TEXT-TITLE 3.5 / ASG-TEXT-HEADING 5.0", "Layout tab"],
        ["Tables", "ASG-TABLE-STANDARD, -MATERIAL, -GLASS, -HARDWARE, -REVISION, -REGISTER, -NOTES", "Layout tab"],
    ], (col_w * 0.18, col_w * 0.45, col_w * 0.37))]
    assert {"ASG-DIM-ANNO", "ASG-DIM-DETAIL", "ASG-DIM-FIXED"} <= set(dims)

    # ---------------- column 2
    story += [h("4. GOLDEN RULES")]
    story += bullets([
        "Only the template, only ASG layers and ASG styles. Never use the 'Standard' styles.",
        "<b>Never type over a dimension value.</b> If the number is wrong, the drawing is wrong - fix the lines.",
        "Viewports always <b>locked</b>. Unlock only to change the scale.",
        "Title block: never explode, scale or move it.",
        "No new layers or styles on your own - ask the CAD in-charge.",
        "Consultant / architect drawings: attach as xref (Overlay, relative path) on ASG-REFERENCE.",
        "Profile codes, glass make-ups, hardware: only from approved supplier catalogues - never guess.",
    ])
    story += [h("5. BEFORE YOU ISSUE - CHECKLIST")]
    story += checks([
        "All title block fields filled; drawing number in the company format; REV correct.",
        "Every changed area has a revision cloud + delta, and the REV / revision list is updated.",
        "Nothing on layer 0; no object with its own colour / linetype / lineweight.",
        "Viewport scales correct, locked, and written in the SCALE field.",
        "Text and dimensions readable; nothing overlapping; no overridden dimension values.",
        "Helper lines only on ASG-CONSTRUCTION / ASG-NOPLOT (they do not print).",
        "<b>AUDIT</b> (Y) and <b>PURGE</b> (all) done, file saved.",
        "PDF opened and checked: right paper size, lines thick/thin as expected, nothing cut off.",
    ])
    story += [h("6. PROBLEM - QUICK FIX")]
    story += [table([
        ["Problem", "Fix"],
        ["All lines print equally thin", f"{S.CTB_NAME} missing in Plot Styles folder - tell CAD in-charge "
                                         "(meanwhile use monochrome.ctb)"],
        ["Text / arrows huge or tiny", "Wrong style or scale: use ASG-*-ANNO styles and set the viewport scale first"],
        ["Note missing in one viewport", "Select it > right-click > Annotative Object Scale > Add that scale"],
        ["Viewport drawing moved / zoomed", "Viewport was unlocked: unlock, set scale again, lock"],
        ["Helper lines appear on the PDF", "Move them to ASG-CONSTRUCTION or ASG-NOPLOT"],
        ["Title block damaged", "Copy a clean one from a new drawing made from the template"],
    ], (col_w * 0.36, col_w * 0.64))]
    story += [h("7. DRAWING NUMBER")]
    story += [Paragraph(f"<b>{fmt['Format'].split('  +')[0]}</b> + REV R0, R1, R2 ...<br/>"
                        f"DIS: {fmt['DIS']}<br/>TYP: {fmt['TYP']}<br/>"
                        f"Status: {', '.join(S.DRAWING_STATUS_CODES)}", P)]
    story += [h("8. ONE-TIME SETUP (CAD IN-CHARGE ONLY)")]
    story += steps([
        f"Copy <b>{S.CTB_NAME}</b> to the Plot Styles folder; open it: every colour = 'Use object lineweight'.",
        "OPEN ASG_Master_Template.dxf &gt; AUDIT &gt; APPLOAD ASG_Setup.lsp &gt; type <b>ASG-SETUP</b>.",
        "Last line must read <b>0 FAIL</b> (log: ASG_QA_Log.txt). ASG-QA checks the <b>template</b> only - "
        "it is not a check for project drawings.",
        "SAVEAS .dwg, then SAVEAS .dwt; put DWT + CTB on the shared drive; set QNEW on every PC.",
    ])
    story += [Spacer(1, 2),
              Paragraph(f"Full rules: <b>ASG_CAD_Standards.pdf</b> (Standard {S.STANDARD_REV}). "
                        "Questions / changes: CAD in-charge ______________________", P)]

    def page(c, doc):
        w, hgt = A4
        c.saveState()
        c.setFillColor(DARK)
        c.rect(10 * mm, hgt - 27 * mm, w - 20 * mm, 17 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Sans-Bold", 12.5)
        c.drawString(13 * mm, hgt - 16.5 * mm, "ASG CAD DRAFTING SOP - HOW TO USE THE MASTER TEMPLATE")
        c.setFont("Sans", 7.6)
        c.drawString(13 * mm, hgt - 21.5 * mm, f"{S.COMPANY}  |  {S.GROUP}  |  Aluminium, Glass & Facade Division")
        c.drawString(13 * mm, hgt - 25.2 * mm, "Applies to: every estimator / draftsman producing AutoCAD drawings")
        c.setFont("Sans-Bold", 7.6)
        for i, t in enumerate((f"Doc No. {SOP_NO}", f"SOP Rev {SOP_REV}  |  Standard {S.STANDARD_REV}",
                               f"Date {S.STANDARD_DATE}")):
            c.drawRightString(w - 13 * mm, hgt - (16.5 + 4.2 * i) * mm, t)
        c.setFillColor(colors.black)
        c.setFont("Sans", 6.6)
        c.drawString(10 * mm, 6.5 * mm, "Prepared by: ________________     Reviewed by: ________________     "
                                       "Approved by: ________________")
        c.drawRightString(w - 10 * mm, 6.5 * mm, "Controlled document - print and keep at your workstation")
        c.restoreState()

    top = A4[1] - 29 * mm
    fw = (A4[0] - 20 * mm - 6 * mm) / 2
    frames = [Frame(10 * mm, 10 * mm, fw, top - 10 * mm, id="c1", leftPadding=0, rightPadding=0,
                    topPadding=0, bottomPadding=0),
              Frame(10 * mm + fw + 6 * mm, 10 * mm, fw, top - 10 * mm, id="c2", leftPadding=0,
                    rightPadding=0, topPadding=0, bottomPadding=0)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(str(OUT), pagesize=A4, title="ASG CAD Drafting SOP", author=S.COMPANY,
                          leftMargin=10 * mm, rightMargin=10 * mm, topMargin=29 * mm, bottomMargin=10 * mm)
    doc.addPageTemplates([PageTemplate(id="p", frames=frames, onPage=page)])
    # column break before section 4
    from reportlab.platypus import FrameBreak
    i = next(k for k, f in enumerate(story)
             if isinstance(f, Paragraph) and f.style is H and f.getPlainText().startswith("4."))
    story.insert(i, FrameBreak())
    doc.build(story)
    return doc.page


def build_one_page():
    """Largest font size (9.0 -> 6.6 pt) at which the SOP fits on one A4 page."""
    size = 9.0
    while size >= 6.6:
        pages = build(size)
        if pages == 1:
            return size
        size = round(size - 0.1, 2)
    raise RuntimeError("SOP does not fit on one page")


if __name__ == "__main__":
    print("SOP font size", build_one_page(), "->", OUT)
