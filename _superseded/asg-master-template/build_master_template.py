"""
ASG Master AutoCAD Template - generator
Saeed Al Siraj Glass & Aluminium Works L.L.C. | Al Siraj Group | UAE

Builds a BLANK master drawing (no product geometry) as DXF R2018 plus the
plot style table. DWG / DWT cannot be written by this toolchain - see README.

    python build_master_template.py
Requires: ezdxf >= 1.1
"""

from pathlib import Path

import ezdxf
from ezdxf import colors
from ezdxf.addons import acadctb
from ezdxf.enums import TextEntityAlignment

OUT = Path(__file__).parent / "output"
DXF_NAME = "ASG_Master_Template.dxf"
CTB_NAME = "ASG_Monochrome.ctb"

COMPANY = "SAEED AL SIRAJ GLASS & ALUMINIUM WORKS L.L.C."
GROUP = "AL SIRAJ GROUP"

# ---------------------------------------------------------------------------
# Linetypes (acadiso.lin values, mm)
# ---------------------------------------------------------------------------
LINETYPES = {
    "HIDDEN": ([9.525, 6.35, -3.175], "Hidden __ __ __ __"),
    "HIDDEN2": ([4.7625, 3.175, -1.5875], "Hidden (.5x) _ _ _ _"),
    "CENTER": ([50.8, 31.75, -6.35, 6.35, -6.35], "Center ____ _ ____ _"),
    "CENTER2": ([25.4, 15.875, -3.175, 3.175, -3.175], "Center (.5x) ___ _ ___"),
    "DASHED": ([19.05, 12.7, -6.35], "Dashed __ __ __"),
    "DASHED2": ([9.525, 6.35, -3.175], "Dashed (.5x) _ _ _"),
    "DASHDOT": ([25.4, 12.7, -6.35, 0.0, -6.35], "Dash dot __ . __ ."),
    "DASHDOT2": ([12.7, 6.35, -3.175, 0.0, -3.175], "Dash dot (.5x) _ . _ ."),
    "PHANTOM": ([63.5, 31.75, -6.35, 6.35, -6.35, 6.35, -6.35], "Phantom ____ _ _ ____"),
    "PHANTOM2": ([31.75, 15.875, -3.175, 3.175, -3.175, 3.175, -3.175], "Phantom (.5x) __ _ _ __"),
    "DOT": ([6.35, 0.0, -6.35], "Dot . . . ."),
}

# ---------------------------------------------------------------------------
# Layers: name, group, ACI, linetype, lineweight mm, plot, purpose
# Colour logic: 7 = primary geometry, 8 = secondary/hidden, 4 = glass,
# 3 = annotation, 1 = revision, 6 = non-plot, 250-254 = plotted grey.
# ---------------------------------------------------------------------------
LAYERS = [
    ("ASG-OBJECT", "General geometry", 7, "Continuous", 0.25, True, "General object geometry - default current layer"),
    ("ASG-OUTLINE", "General geometry", 7, "Continuous", 0.35, True, "Main overall outlines / visible edges in elevation"),
    ("ASG-PROFILE", "General geometry", 7, "Continuous", 0.30, True, "Aluminium profile outlines (frames, mullions, transoms, sashes)"),
    ("ASG-GLASS", "General geometry", 4, "Continuous", 0.18, True, "Glass / mirror panel edges"),
    ("ASG-METAL", "General geometry", 7, "Continuous", 0.30, True, "MS / SS members, plates, brackets"),
    ("ASG-HARDWARE", "General geometry", 8, "Continuous", 0.18, True, "Handles, hinges, locks, rollers, patch fittings"),
    ("ASG-FIXING", "General geometry", 8, "Continuous", 0.18, True, "Anchors, screws, bolts, fixing brackets"),
    ("ASG-CLADDING", "General geometry", 7, "Continuous", 0.25, True, "ACP / panel cladding and flashings"),
    ("ASG-INSULATION", "General geometry", 252, "Continuous", 0.13, True, "Insulation / thermal break outline and hatch (plots grey)"),
    ("ASG-HIDDEN", "Technical details", 8, "HIDDEN2", 0.18, True, "Concealed / hidden edges"),
    ("ASG-CENTER", "Technical details", 8, "CENTER2", 0.13, True, "Centrelines and axes of symmetry"),
    ("ASG-SECTION", "Technical details", 7, "Continuous", 0.35, True, "Cut-section outlines (heaviest object line)"),
    ("ASG-HATCH", "Technical details", 252, "Continuous", 0.09, True, "General section hatching (plots grey)"),
    ("ASG-GLAZING-BEAD", "Technical details", 7, "Continuous", 0.25, True, "Glazing beads and snap-in profiles"),
    ("ASG-SEALANT", "Technical details", 8, "Continuous", 0.13, True, "Silicone / weather seal, backer rod"),
    ("ASG-GASKET", "Technical details", 8, "Continuous", 0.13, True, "EPDM gaskets, brushes, setting blocks"),
    ("ASG-DRAINAGE", "Technical details", 8, "DASHED2", 0.18, True, "Drainage paths, weep holes, linear drains"),
    ("ASG-CONSTRUCTION", "Technical details", 6, "Continuous", 0.05, False, "Construction / setting-out lines - NO PLOT"),
    ("ASG-REFERENCE", "Technical details", 253, "Continuous", 0.13, True, "Architectural / structural background (plots light grey)"),
    ("ASG-DIMENSION", "Dimensions & annotation", 3, "Continuous", 0.13, True, "Dimensions"),
    ("ASG-TEXT", "Dimensions & annotation", 7, "Continuous", 0.18, True, "General text"),
    ("ASG-TEXT-NOTE", "Dimensions & annotation", 7, "Continuous", 0.18, True, "General / specification notes"),
    ("ASG-MULTILEADER", "Dimensions & annotation", 3, "Continuous", 0.13, True, "Multileader callouts"),
    ("ASG-TABLE", "Dimensions & annotation", 7, "Continuous", 0.18, True, "Schedules and tables"),
    ("ASG-LEVEL", "Dimensions & annotation", 3, "Continuous", 0.18, True, "Level markers (FFL, SSL, sill heights)"),
    ("ASG-REVISION", "Dimensions & annotation", 1, "Continuous", 0.25, True, "Revision clouds and delta tags"),
    ("ASG-DETAIL-MARK", "Dimensions & annotation", 3, "Continuous", 0.25, True, "Detail callout bubbles / boundaries"),
    ("ASG-SECTION-MARK", "Dimensions & annotation", 3, "Continuous", 0.25, True, "Section cut lines and markers"),
    ("ASG-GRID", "Dimensions & annotation", 8, "CENTER", 0.13, True, "Column grid / setting-out grid"),
    ("ASG-TITLEBLOCK", "Sheet & plotting", 7, "Continuous", 0.25, True, "Title block linework and attributes"),
    ("ASG-BORDER", "Sheet & plotting", 7, "Continuous", 0.50, True, "Sheet border frame"),
    ("ASG-VIEWPORT", "Sheet & plotting", 6, "Continuous", 0.00, False, "Viewport boundaries - NO PLOT"),
    ("ASG-NOPLOT", "Sheet & plotting", 6, "Continuous", 0.00, False, "Reference notes / markups never printed - NO PLOT"),
]
CURRENT_LAYER = "ASG-OBJECT"

# ---------------------------------------------------------------------------
# Text styles: name, ttf, bold, annotative, recommended paper height, use
# ---------------------------------------------------------------------------
TEXT_STYLES = [
    ("ASG-TEXT", "arial.ttf", False, True, 2.5, "General text and dimension text"),
    ("ASG-TEXT-NOTE", "arial.ttf", False, True, 2.5, "General notes / specifications"),
    ("ASG-TEXT-SMALL", "arial.ttf", False, True, 1.8, "Small technical annotation, profile codes"),
    ("ASG-TEXT-TITLE", "arialbd.ttf", True, False, 3.5, "Detail / view titles (5.0 for drawing title)"),
    ("ASG-TEXT-SHEET", "arialbd.ttf", True, False, 5.0, "Sheet headings, title block title / number"),
]
PAPER_HEIGHTS = [
    ("Small technical annotation", 1.8, "ASG-TEXT-SMALL", "Min. 1.8 mm - not below on A4"),
    ("Dimensions", 2.5, "ASG-TEXT (via dim style)", "2.0 acceptable on congested 1:1 details"),
    ("General notes", 2.5, "ASG-TEXT-NOTE", ""),
    ("Detail / view titles", 3.5, "ASG-TEXT-TITLE", "Underlined, scale text 2.5 below"),
    ("Drawing titles", 5.0, "ASG-TEXT-SHEET", "7.0 on A1 title block"),
    ("Sheet headings", 5.0, "ASG-TEXT-SHEET", "3.5 on A4"),
]

ANNO_SCALES = [1, 2, 5, 10, 20, 25, 50, 100]
FIXED_DIM_SCALES = [1, 2, 5, 10, 20, 50]

HATCH_STANDARD = [
    # material, pattern (acadiso.pat), scale @1:1 paper, angle, layer, note
    ("Glass (section)", "ANSI31", 0.5, 0, "ASG-HATCH", "Or no hatch + 2 parallel lines for thin glass"),
    ("Aluminium section", "SOLID", "-", "-", "ASG-HATCH", "Thin walls: solid fill reads best"),
    ("Steel / metal section", "ANSI32", 1.0, 0, "ASG-HATCH", "SS: ANSI31 @ 90 to distinguish"),
    ("Concrete", "AR-CONC", 0.05, 0, "ASG-REFERENCE", "Scale x drawing scale"),
    ("Masonry / blockwork", "ANSI31", 1.0, 0, "ASG-REFERENCE", "Alt: AR-B816 in elevation"),
    ("Insulation", "INSUL", 0.05, 0, "ASG-INSULATION", "Fit to insulation thickness"),
    ("Sealant", "SOLID", "-", "-", "ASG-SEALANT", "Small beads: solid fill"),
    ("Generic section fill", "ANSI37", 1.0, 0, "ASG-HATCH", ""),
]

ATTRIBUTE_STANDARD = [
    ("ITEM_CODE", "Item / product code", "e.g. ASG-W-01"),
    ("ITEM_NAME", "Item description", "e.g. SLIDING WINDOW"),
    ("SYSTEM_NAME", "System / series", "e.g. supplier series name"),
    ("MANUFACTURER", "Manufacturer / supplier", ""),
    ("MATERIAL", "Base material", "ALUMINIUM 6063-T6 / SS304 ..."),
    ("FINISH", "Finish", "POWDER COATED / ANODISED / HAIRLINE"),
    ("COLOUR", "Colour / RAL", "RAL 9016"),
    ("GLASS_SPEC", "Glass specification", "6mm CLEAR TEMPERED"),
    ("REVISION", "Block revision", "R0"),
]

# ---------------------------------------------------------------------------
# Sheets
# ---------------------------------------------------------------------------
SHEETS = [
    # layout name, width, height, paper (DWG To PDF.pc3), title block, tb width, vp scale
    ("A4-LANDSCAPE", 297.0, 210.0, "ISO_full_bleed_A4", "ASG-TB-A4", 10),
    ("A4-PORTRAIT", 210.0, 297.0, "ISO_full_bleed_A4", "ASG-TB-A4", 10),
    ("A3-LANDSCAPE", 420.0, 297.0, "ISO_full_bleed_A3", "ASG-TB-A3", 20),
    ("A3-PORTRAIT", 297.0, 420.0, "ISO_full_bleed_A3", "ASG-TB-A3", 20),
    ("A1-LANDSCAPE", 841.0, 594.0, "ISO_full_bleed_A1", "ASG-TB-A1", 50),
]
MARGIN_LEFT = 20.0  # filing margin
MARGIN = 10.0

# Title block geometry per sheet class (designed, not stretched)
TB_SPECS = {
    "ASG-TB-A4": dict(w=180.0, r=7.0, cap=1.8, val=2.5, title=3.5, num=3.5, comp=2.8),
    "ASG-TB-A3": dict(w=180.0, r=9.0, cap=2.0, val=2.5, title=5.0, num=3.5, comp=3.5),
    "ASG-TB-A1": dict(w=250.0, r=12.0, cap=2.5, val=3.5, title=7.0, num=5.0, comp=5.0),
}

TB_ATTRIBUTES = [
    ("PROJECT", "Project", "PROJECT NAME"),
    ("LOCATION", "Location", "LOCATION, UAE"),
    ("CLIENT", "Client", "CLIENT NAME"),
    ("CONSULTANT", "Consultant", "CONSULTANT NAME"),
    ("DWG_TITLE", "Drawing title - line 1", "DRAWING TITLE"),
    ("DWG_TITLE_2", "Drawing title - line 2", "-"),
    ("DWG_NO", "Drawing number", "AS-YYYY-NNN-DIS-TYP-001"),
    ("REV", "Revision", "R0"),
    ("DATE", "Date (DD.MM.YYYY)", "DD.MM.YYYY"),
    ("DRAWN_BY", "Drawn by", "-"),
    ("CHECKED_BY", "Checked by", "-"),
    ("APPROVED_BY", "Approved by", "-"),
    ("SCALE", "Scale", "AS SHOWN"),
    ("SHEET_NO", "Sheet number (__ OF __)", "01 OF 01"),
    ("DWG_STATUS", "Drawing status", "FOR APPROVAL"),
    ("REMARKS", "General remarks", "-"),
]

BYLAYER_RAW = colors.BY_LAYER_RAW_VALUE
TB_HEIGHTS = {}  # filled when title blocks are built


# ---------------------------------------------------------------------------
def annotative_xdata(entity):
    entity.set_xdata("AcadAnnotative", [
        (1000, "AnnotativeData"), (1002, "{"), (1070, 1), (1070, 1), (1002, "}"),
    ])


def build_document():
    doc = ezdxf.new("R2018", setup=False, units=4)
    doc.appids.add("AcadAnnotative")
    h = doc.header
    settings = {
        "$INSUNITS": 4, "$MEASUREMENT": 1, "$LUNITS": 2, "$LUPREC": 0,
        "$AUNITS": 0, "$AUPREC": 2, "$ANGBASE": 0.0, "$ANGDIR": 0,
        "$LIMMIN": (0.0, 0.0), "$LIMMAX": (100000.0, 70000.0), "$LIMCHECK": 0,
        "$LTSCALE": 1.0, "$PSLTSCALE": 1, "$CELTSCALE": 1.0,
        "$LWDISPLAY": 1, "$CELWEIGHT": -1, "$CECOLOR": 256,
        "$ORTHOMODE": 0,
        "$PDMODE": 0, "$PDSIZE": 0.0,
        "$DIMASSOC": 2, "$PLINEGEN": 1, "$FILLMODE": 1, "$MIRRTEXT": 0,
        "$TEXTSIZE": 2.5, "$PROXYGRAPHICS": 1, "$VISRETAIN": 1,
        "$PSVPSCALE": 0.0, "$TILEMODE": 1, "$UCSORG": (0, 0, 0),
        "$WORLDVIEW": 1, "$PSTYLEMODE": 1,  # colour-dependent (CTB)
    }
    for k, v in settings.items():
        h[k] = v

    for name, (pattern, desc) in LINETYPES.items():
        doc.linetypes.add(name, pattern=pattern, description=desc)

    for name, _g, aci, lt, lw, plot, desc in LAYERS:
        lay = doc.layers.add(name, color=aci, linetype=lt)
        lay.dxf.lineweight = int(round(lw * 100))
        lay.dxf.plot = int(plot)
        lay.description = desc
    doc.layers.get("0").description = "AutoCAD system layer - blocks only, do not draw"

    for name, ttf, bold, anno, _ph, _u in TEXT_STYLES:
        st = doc.styles.add(name, font=ttf)
        st.dxf.height = 0.0
        st.dxf.width = 1.0
        st.set_extended_font_data(family="Arial", italic=False, bold=bold)
        if anno:
            annotative_xdata(st)
    std = doc.styles.get("Standard")
    std.dxf.font = "arial.ttf"
    std.set_extended_font_data(family="Arial", italic=False, bold=False)

    add_dimstyles(doc)
    add_mleader_styles(doc)
    add_mline_styles(doc)
    for name, spec in TB_SPECS.items():
        add_title_block(doc, name, **spec)
    add_layouts(doc)

    h["$CLAYER"] = CURRENT_LAYER
    h["$TEXTSTYLE"] = "ASG-TEXT"
    h["$DIMSTYLE"] = "ASG-DIM-ANNOTATIVE"
    h["$CMLSTYLE"] = "ASG-MLINE-2"
    doc.set_modelspace_vport(height=10000, center=(5000, 3500))
    return doc


DIM_BASE = {
    "dimtxsty": "ASG-TEXT", "dimtxt": 2.5, "dimasz": 2.5, "dimblk": "",
    "dimexo": 1.5, "dimexe": 1.25, "dimdli": 7.0, "dimdle": 0.0, "dimgap": 1.0,
    "dimtad": 1, "dimjust": 0, "dimtih": 0, "dimtoh": 0, "dimtix": 0,
    "dimatfit": 3, "dimtmove": 1, "dimtofl": 1, "dimsoxd": 0,
    "dimlunit": 2, "dimdec": 0, "dimdsep": ord("."), "dimrnd": 0.0,
    "dimzin": 8,  # suppress trailing zeros
    "dimaunit": 0, "dimadec": 2, "dimazin": 2,
    "dimlfac": 1.0,  # measured geometry, never scaled
    "dimalt": 0, "dimaltf": 25.4, "dimaltd": 2,
    "dimtol": 0, "dimlim": 0, "dimtp": 0.0, "dimtm": 0.0, "dimtdec": 1, "dimtfac": 0.7,
    "dimclrd": 256, "dimclre": 256, "dimclrt": 256, "dimlwd": -2, "dimlwe": -2,
    "dimcen": 2.5, "dimupt": 0,
}


def add_dimstyles(doc):
    a = dict(DIM_BASE, dimscale=1.0)
    annotative_xdata(doc.dimstyles.add("ASG-DIM-ANNOTATIVE", dxfattribs=a))
    for s in FIXED_DIM_SCALES:
        doc.dimstyles.add(f"ASG-DIM-1-{s}", dxfattribs=dict(DIM_BASE, dimscale=float(s)))


MLEADER_SPECS = [
    # name, annotative, scale, arrow, char height, text style
    ("ASG-ML-ANNOTATIVE", True, 1.0, "", 2.5, "ASG-TEXT-NOTE"),
    ("ASG-ML-NOTE", False, 1.0, "", 2.5, "ASG-TEXT-NOTE"),
    ("ASG-ML-DETAIL", False, 1.0, "_DOT", 1.8, "ASG-TEXT-SMALL"),
]


def add_mleader_styles(doc):
    for name, anno, scale, arrow, ch, tstyle in MLEADER_SPECS:
        ml = doc.mleader_styles.new(name)
        d = ml.dxf
        d.content_type = 2  # MText
        d.leader_type = 1  # straight
        d.max_leader_segments_points = 2
        d.leader_line_color = BYLAYER_RAW
        d.leader_lineweight = -2
        d.arrow_head_size = 2.5 if not arrow else 1.5
        if arrow:
            d.arrow_head_handle = ezdxf.ARROWS.arrow_handle(doc.blocks, arrow)
        d.has_landing = 1
        d.has_dogleg = 1
        d.dogleg_length = 4.0
        d.landing_gap_size = 1.0
        d.text_style_handle = doc.styles.get(tstyle).dxf.handle
        d.text_color = BYLAYER_RAW
        d.char_height = ch
        d.has_text_frame = 0
        d.text_left_attachment_type = 1   # middle of top line
        d.text_right_attachment_type = 1
        d.text_angle_type = 1
        d.text_align_always_left = 0
        d.scale = scale
        d.is_annotative = int(anno)


def add_mline_styles(doc):
    m = doc.mline_styles.new("ASG-MLINE-2")
    m.dxf.description = "Two-line, offsets +/-0.5 - set MLINE scale = overall width"
    m.elements.append(0.5, 256, "BYLAYER")
    m.elements.append(-0.5, 256, "BYLAYER")
    m.dxf.flags = 16 | 256  # start + end square caps
    m = doc.mline_styles.new("ASG-MLINE-3")
    m.dxf.description = "Three-line with centreline - frames / panels with axis"
    m.elements.append(0.5, 256, "BYLAYER")
    m.elements.append(0.0, 256, "CENTER2")
    m.elements.append(-0.5, 256, "BYLAYER")
    m.dxf.flags = 16 | 256


# ---------------------------------------------------------------------------
def _text(space, s, x, y, h, style, layer, align=TextEntityAlignment.BOTTOM_LEFT):
    t = space.add_text(s, height=h, dxfattribs={"style": style, "layer": layer})
    t.set_placement((x, y), align=align)
    return t


def add_title_block(doc, name, w, r, cap, val, title, num, comp):
    """Bottom-right title block, base point = bottom-right corner."""
    blk = doc.blocks.new(name)
    L = "0"  # inserted on ASG-TITLEBLOCK; ByLayer inside block
    rows = []  # (height, cells) bottom -> top; cells: (fraction, caption, tag, height, style)
    rows.append((1.5 * r, [(0.60, "DRAWING No.", "DWG_NO", num, "ASG-TEXT-SHEET"),
                           (0.15, "REV", "REV", num, "ASG-TEXT-SHEET"),
                           (0.25, "SHEET No.", "SHEET_NO", val, "ASG-TEXT-NOTE")]))
    rows.append((r, [(1 / 3, "SCALE", "SCALE", val, "ASG-TEXT-NOTE"),
                     (1 / 3, "DATE", "DATE", val, "ASG-TEXT-NOTE"),
                     (1 / 3, "STATUS", "DWG_STATUS", val, "ASG-TEXT-NOTE")]))
    rows.append((r, [(1 / 3, "DRAWN BY", "DRAWN_BY", val, "ASG-TEXT-NOTE"),
                     (1 / 3, "CHECKED BY", "CHECKED_BY", val, "ASG-TEXT-NOTE"),
                     (1 / 3, "APPROVED BY", "APPROVED_BY", val, "ASG-TEXT-NOTE")]))
    rows.append(("TITLE", None))
    rows.append((r, [(1.0, "REMARKS", "REMARKS", val, "ASG-TEXT-NOTE")]))
    rows.append((r, [(0.5, "CLIENT", "CLIENT", val, "ASG-TEXT-NOTE"),
                     (0.5, "CONSULTANT", "CONSULTANT", val, "ASG-TEXT-NOTE")]))
    rows.append((r, [(0.5, "PROJECT", "PROJECT", val, "ASG-TEXT-NOTE"),
                     (0.5, "LOCATION", "LOCATION", val, "ASG-TEXT-NOTE")]))
    rows.append(("COMPANY", None))

    prompts = {t: p for t, p, _d in TB_ATTRIBUTES}
    defaults = {t: d for t, _p, d in TB_ATTRIBUTES}
    x0 = -w

    def att(tag, x, y, hh, style):
        a = blk.add_attdef(tag, insert=(x, y), text=defaults[tag],
                           dxfattribs={"height": hh, "style": style, "layer": L,
                                       "prompt": prompts[tag]})
        a.set_placement((x, y), align=TextEntityAlignment.BOTTOM_LEFT)

    pad = 0.12 * r
    y = 0.0
    for height, cells in rows:
        if height == "TITLE":
            hh = 2 * r
            _text(blk, "DRAWING TITLE", x0 + pad, y + hh - pad - cap, cap, "ASG-TEXT-SMALL", L)
            att("DWG_TITLE", x0 + pad, y + hh * 0.42, title, "ASG-TEXT-SHEET")
            att("DWG_TITLE_2", x0 + pad, y + pad, val, "ASG-TEXT-TITLE")
        elif height == "COMPANY":
            hh = 1.6 * r
            _text(blk, COMPANY, x0 + pad, y + hh * 0.52, comp, "ASG-TEXT-SHEET", L)
            _text(blk, GROUP + "  |  ALUMINIUM & GLASS DIVISION  |  UAE", x0 + pad, y + pad,
                  cap, "ASG-TEXT-SMALL", L)
        else:
            hh = height
            x = x0
            for frac, caption, tag, th, style in cells:
                cw = w * frac
                if x > x0:
                    blk.add_line((x, y), (x, y + hh), dxfattribs={"layer": L})
                _text(blk, caption, x + pad, y + hh - pad - cap, cap, "ASG-TEXT-SMALL", L)
                att(tag, x + pad, y + pad, min(th, hh - cap - 3 * pad), style)
                x += cw
        y += hh
        blk.add_line((x0, y), (0, y), dxfattribs={"layer": L})
    blk.add_lwpolyline([(x0, 0), (0, 0), (0, y), (x0, y)], close=True,
                       dxfattribs={"layer": L})
    TB_HEIGHTS[name] = y
    return y


def add_layouts(doc):
    for name, w, h, paper, tb, vp_scale in SHEETS:
        lay = doc.layouts.new(name)
        lay.page_setup(size=(w, h), margins=(0, 0, 0, 0), units="mm", scale=(1, 1),
                       name=paper, device="DWG To PDF.pc3")
        lay.dxf.current_style_sheet = CTB_NAME
        lay.use_plot_styles(True)
        lay.print_lineweights(True)
        lay.scale_lineweights(False)
        lay.plot_centered(True)
        lay.plot_viewport_borders(False)
        lay.show_plot_styles(False)
        lay.dxf.shade_plot_resolution_level = 3
        # border
        lay.add_lwpolyline([(MARGIN_LEFT, MARGIN), (w - MARGIN, MARGIN), (w - MARGIN, h - MARGIN),
                            (MARGIN_LEFT, h - MARGIN)], close=True,
                           dxfattribs={"layer": "ASG-BORDER"})
        ref = lay.add_blockref(tb, (w - MARGIN, MARGIN), dxfattribs={"layer": "ASG-TITLEBLOCK"})
        ref.add_auto_attribs({})
        # one locked viewport on the no-plot viewport layer, clear of title block
        tb_h = TB_HEIGHTS[tb]
        x1, y1 = MARGIN_LEFT + 5, MARGIN + tb_h + 5
        x2, y2 = w - MARGIN - 5, h - MARGIN - 5
        if w > h:  # landscape: viewport left of title block, full height
            x2 = w - MARGIN - TB_SPECS[tb]["w"] - 5
            y1 = MARGIN + 5
        vp = lay.add_viewport(center=((x1 + x2) / 2, (y1 + y2) / 2), size=(x2 - x1, y2 - y1),
                              view_center_point=((x2 - x1) * vp_scale / 2, (y2 - y1) * vp_scale / 2),
                              view_height=(y2 - y1) * vp_scale,
                              dxfattribs={"layer": "ASG-VIEWPORT"})
        vp.dxf.flags |= 16384  # display locked
    doc.layouts.delete("Layout1")


# ---------------------------------------------------------------------------
SCALE_TEMPLATE = """  0
SCALE
  5
{h}
102
{{ACAD_REACTORS
330
{owner}
102
}}
330
{owner}
100
AcDbScale
 70
0
300
{name}
140
1.0
141
{du}
290
{unit}
"""


def inject_annotation_scales(path: Path):
    """ezdxf has no SCALE object support: add the ACAD_SCALELIST entries as raw
    DXF tags (AcDbScale), with fresh handles above $HANDSEED."""
    doc = ezdxf.readfile(path)
    owner = doc.rootdict.get("ACAD_SCALELIST").dxf.handle
    seed = int(doc.header["$HANDSEED"], 16)
    lines = path.read_text().split("\n")
    objs, entries = [], []
    for i, s in enumerate(ANNO_SCALES):
        hnd = format(seed + i, "X")
        objs.append(SCALE_TEMPLATE.format(h=hnd, owner=owner, name=f"1:{s}", du=float(s),
                                          unit=1 if s == 1 else 0))
        entries += ["  3", f"A{i}", "350", hnd]
    new_seed = format(seed + len(ANNO_SCALES) + 1, "X")
    # find the dictionary with handle == owner and append entries after its 281 flag
    out = []
    i = 0
    in_dict = False
    done_entries = False
    done_objs = False
    in_objects = False
    while i < len(lines):
        ln = lines[i]
        out.append(ln)
        if ln.strip() == "$HANDSEED":
            out.append(lines[i + 1])
            out.append(new_seed)
            i += 3
            continue
        if ln.strip() == "OBJECTS" and lines[i - 1].strip() == "2":
            in_objects = True
        if ln.strip() == "5" and lines[i + 1].strip() == owner and lines[i - 1].strip() == "DICTIONARY":
            in_dict = True
        if in_dict and not done_entries and ln.strip() == "281":
            out.append(lines[i + 1])
            out += entries
            done_entries = True
            in_dict = False
            i += 2
            continue
        if in_objects and not done_objs and ln.strip() == "ENDSEC":
            out.pop()
            out.pop()  # remove "  0"
            out += "".join(objs).rstrip("\n").split("\n")
            out += ["  0", "ENDSEC"]
            done_objs = True
            in_objects = False
        i += 1
    assert done_entries and done_objs, "scale list injection failed"
    path.write_text("\n".join(out))


# ---------------------------------------------------------------------------
def _compress_ctb(stream, content: str):
    """Replacement for ezdxf's CTB writer: its pack("LLL") uses native 8-byte
    longs on 64-bit Linux/macOS, giving a header AutoCAD cannot read. CTB files
    use three little-endian 4-byte unsigned ints."""
    import struct
    import zlib
    body = zlib.compress(content.encode())
    stream.write(b"PIAFILEVERSION_2.0,CTBVER1,compress\r\npmzlibcodec")
    stream.write(struct.pack("<LLL", zlib.adler32(body), len(content), len(body)))
    stream.write(body)


acadctb._compress = _compress_ctb


def build_ctb(path: Path):
    ctb = acadctb.new_ctb()
    ctb.description = "ASG monochrome: all ACI plot black; 250-254 plot as grey; object lineweight"
    for aci in range(1, 256):
        st = ctb[aci]
        if 250 <= aci <= 254:
            g = {250: 51, 251: 91, 252: 132, 253: 173, 254: 214}[aci]
            st.color = (g, g, g)
        else:
            st.color = (0, 0, 0)
        st.set_lineweight(0.0)  # use object lineweight
        st.linetype = acadctb.OBJECT_LINETYPE
        st.screen = 100
        st.description = ""
    ctb.save(path)


def main():
    OUT.mkdir(exist_ok=True)
    doc = build_document()
    dxf_path = OUT / DXF_NAME
    doc.saveas(dxf_path)
    inject_annotation_scales(dxf_path)
    build_ctb(OUT / CTB_NAME)
    print("written", dxf_path)
    print("written", OUT / CTB_NAME)


if __name__ == "__main__":
    main()
