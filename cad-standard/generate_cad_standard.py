"""
Al Siraj Group - CAD Shop Drawing Standard generator (ASG-STD-CAD-001 Rev 0)

Builds, from the written standard:
  output/AlSiraj_ShopDrawing_Template.dxf      -> open in AutoCAD, Save As .dwt
  output/AS-2026-000-ALU-SD-001-R0_Sample-W01.dxf  -> worked example sheet + legend
  output/AlSiraj_ShopDrawing.ctb                -> plot style table (all colours plot black)

Run:  python generate_cad_standard.py
Requires: ezdxf >= 1.1
"""

from pathlib import Path

import ezdxf
from ezdxf import colors
from ezdxf.addons import acadctb
from ezdxf.enums import TextEntityAlignment
from ezdxf.math import Vec2
from ezdxf.render import mleader

OUT = Path(__file__).parent / "output"

COMPANY = "SAEED AL SIRAJ GLASS & ALUMINIUM WORKS L.L.C."
DIVISION = "AL SIRAJ GROUP - ALUMINIUM & GLASS DIVISION"
CTB_NAME = "AlSiraj_ShopDrawing.ctb"

# --------------------------------------------------------------------------
# Section 3 - Layer standard: name, ACI colour, lineweight (mm, None=Default),
# linetype, plot, description
# --------------------------------------------------------------------------
LAYERS = [
    ("A-TITLEBLOCK", 7, 0.30, "Continuous", True, "Sheet border, title block, company logo"),
    ("A-GRID", 9, 0.13, "CENTER2", True, "Column grid / setting-out axis lines"),
    ("A-TEXT-TITLE", 7, 0.35, "Continuous", True, "Drawing title & sheet heading text"),
    ("A-TEXT-NOTES", 7, 0.18, "Continuous", True, "General notes & specification notes"),
    ("A-DIM", 1, 0.13, "Continuous", True, "Dimension lines, extension lines & dimension text"),
    ("A-LEADER", 1, 0.13, "Continuous", True, "Leaders & multileader callouts"),
    ("A-HIDDEN", 8, 0.13, "HIDDEN2", True, "Concealed / hidden edges"),
    ("A-CENTER", 8, 0.13, "CENTER2", True, "Centrelines of symmetrical members"),
    ("A-CONST", 9, 0.00, "Continuous", False, "Construction / reference geometry - NON-PLOT"),
    ("A-VPORT", 9, 0.00, "Continuous", False, "Paperspace viewport boundary - NON-PLOT"),
    ("A-REVCLOUD", 1, 0.30, "Continuous", True, "Revision clouds & delta revision tags"),
    ("ALU-OUTLINE", 5, 0.30, "Continuous", True, "Aluminium profile outlines - frame / mullion / transom / sash"),
    ("ALU-HATCH", 5, 0.13, "Continuous", True, "Aluminium section fill / hatch"),
    ("ALU-HARDWARE", 140, 0.18, "Continuous", True, "Hinges, handles, locks, rollers, cleats, brackets"),
    ("ALU-LABEL", 5, 0.13, "Continuous", True, "Aluminium profile code / reference tag"),
    ("GLZ-OUTLINE", 4, 0.25, "Continuous", True, "Glass panel outline"),
    ("GLZ-HATCH", 4, 0.09, "Continuous", True, "Glass section hatch"),
    ("GLZ-LABEL", 4, 0.13, "Continuous", True, "Glass type / thickness / DGU make-up callout"),
    ("MS-STRUCT", 3, 0.40, "Continuous", True, "Mild steel structural members"),
    # Std lists ANSI32 / ANSI31 / ANSI37 here - those are hatch patterns, not
    # linetypes, so the layer linetype is Continuous and the pattern is applied
    # by the HATCH object (Section 9).
    ("MS-HATCH", 3, 0.13, "Continuous", True, "Mild steel section hatch (ANSI32 @ 45)"),
    ("MS-WELD", 30, 0.18, "Continuous", True, "Weld symbols - mild steel"),
    ("SS-STRUCT", 6, 0.40, "Continuous", True, "Stainless steel structural / fabrication members"),
    ("SS-HATCH", 6, 0.13, "Continuous", True, "Stainless steel section hatch (ANSI31 @ 135)"),
    ("SS-WELD", 30, 0.18, "Continuous", True, "Weld symbols - stainless steel"),
    ("MISC-SEALANT", 2, 0.13, "Continuous", True, "Sealant / weather-seal / gasket line"),
    ("MISC-INSULATION", 2, 0.09, "Continuous", True, "Insulation / thermal break hatch (ANSI37)"),
    ("MISC-ANCHOR", 9, 0.18, "Continuous", True, "Anchors, fixing brackets, fasteners"),
    ("MISC-MIRROR", 4, 0.25, "Continuous", True, "Mirror panels"),
    ("MISC-HANDRAIL", 6, 0.30, "Continuous", True, "Handrail / balustrade posts & rails"),
    ("MISC-DRAIN", 5, 0.25, "Continuous", True, "Linear drain / channel"),
    ("XREF", 9, None, "Continuous", True, "External reference - architectural background"),
]

# Section 6 - text styles: name, ttf, bold, plotted height
TEXT_STYLES = [
    ("STD-TITLE", "arialbd.ttf", True, 5.0),
    ("STD-SUBTITLE", "arial.ttf", False, 3.5),
    ("STD-NOTES", "arial.ttf", False, 2.5),
    ("STD-DIM", "arial.ttf", False, 2.5),
    ("STD-LABEL", "arial.ttf", False, 2.0),
]
H_TITLE, H_SUB, H_NOTES, H_DIM, H_LABEL = 5.0, 3.5, 2.5, 2.5, 2.0

# Section 2.2 scales. Dim/MLeader styles are created per scale (DIMSCALE
# method of Section 7). Precision: 0.0 for detail scales, 0 for GA/elevation.
SCALES = [1, 2, 5, 10, 20, 50, 100]


def style_suffix(scale: int) -> str:
    return "" if scale == 1 else f"-1-{scale}"


# Section 9 - hatch by material: pattern, scale, visual line angle, layer.
# ANSI31/32/37 are already drawn at 45 deg, so the HATCH angle property is
# (visual angle - 45): MS lines read 45 deg, SS lines read 135 deg on paper.
HATCH = {
    "ALU": ("SOLID", 1.0, 0, "ALU-HATCH"),
    "GLASS": ("ANSI31", 0.5, 45, "GLZ-HATCH"),
    "MS": ("ANSI32", 1.0, 45, "MS-HATCH"),
    "SS": ("ANSI31", 0.75, 135, "SS-HATCH"),
    "INSUL": ("ANSI37", 1.0, 45, "MISC-INSULATION"),
}

BYLAYER_RAW = colors.BY_LAYER_RAW_VALUE


# --------------------------------------------------------------------------
# Document setup
# --------------------------------------------------------------------------
def new_document() -> ezdxf.document.Drawing:
    doc = ezdxf.new("R2018", setup=False, units=4)  # 4 = millimetres
    hdr = doc.header
    hdr["$MEASUREMENT"] = 1
    hdr["$LUNITS"] = 2  # decimal
    hdr["$LUPREC"] = 2
    hdr["$AUNITS"] = 0
    hdr["$AUPREC"] = 0
    hdr["$LWDISPLAY"] = 1
    hdr["$LTSCALE"] = 1.0
    hdr["$PSLTSCALE"] = 1
    hdr["$CELTSCALE"] = 1.0
    # Endpoint 1 + Midpoint 2 + Centre 4 + Intersection 32 + Perpendicular 128
    hdr["$OSMODE"] = 1 + 2 + 4 + 32 + 128
    hdr["$PDMODE"] = 34
    hdr["$PDSIZE"] = 2.5
    hdr["$CELWEIGHT"] = -1  # ByLayer
    hdr["$PLINEGEN"] = 1
    hdr["$FILLMODE"] = 1
    hdr["$MIRRTEXT"] = 0
    hdr["$TEXTSIZE"] = H_NOTES

    add_linetypes(doc)
    add_layers(doc)
    add_text_styles(doc)
    add_dim_styles(doc)
    add_mleader_styles(doc)
    add_title_block_block(doc)
    add_symbol_blocks(doc)
    doc.header["$CLAYER"] = "A-CONST"
    doc.header["$TEXTSTYLE"] = "STD-NOTES"
    doc.header["$DIMSTYLE"] = "AlSiraj-Dim"
    return doc


def add_linetypes(doc):
    # acadiso.lin values (mm)
    lts = {
        "CENTER": ([50.8, 31.75, -6.35, 6.35, -6.35], "Center ____ _ ____ _ ____"),
        "CENTER2": ([25.4, 15.875, -3.175, 3.175, -3.175], "Center (.5x) ___ _ ___ _ ___"),
        "HIDDEN": ([9.525, 6.35, -3.175], "Hidden __ __ __ __"),
        "HIDDEN2": ([4.7625, 3.175, -1.5875], "Hidden (.5x) _ _ _ _ _ _"),
        "DASHED": ([19.05, 12.7, -6.35], "Dashed __ __ __ __"),
        "PHANTOM2": ([31.75, 15.875, -3.175, 3.175, -3.175, 3.175, -3.175],
                     "Phantom (.5x) ___ _ _ ___ _ _"),
    }
    for name, (pattern, desc) in lts.items():
        doc.linetypes.add(name, pattern=pattern, description=desc)


def add_layers(doc):
    for name, aci, lw, lt, plot, desc in LAYERS:
        layer = doc.layers.add(name, color=aci, linetype=lt)
        layer.dxf.lineweight = -3 if lw is None else int(round(lw * 100))
        layer.dxf.plot = 1 if plot else 0
        layer.description = desc
    zero = doc.layers.get("0")
    zero.description = "RESERVED - do not draw entities on Layer 0"


def add_text_styles(doc):
    for name, ttf, bold, _h in TEXT_STYLES:
        st = doc.styles.add(name, font=ttf)
        st.dxf.height = 0.0
        st.dxf.width = 1.0
        st.set_extended_font_data(family="Arial", italic=False, bold=bold)
    std = doc.styles.get("Standard")
    std.dxf.font = "arial.ttf"
    std.set_extended_font_data(family="Arial", italic=False, bold=False)


def add_dim_styles(doc):
    base = {
        "dimtxsty": "STD-DIM",
        "dimtxt": H_DIM,
        "dimasz": 2.5,
        "dimblk": "",  # closed filled
        "dimexo": 1.5,
        "dimexe": 1.25,
        "dimgap": 1.0,
        "dimtad": 1,  # above
        "dimtih": 0,  # aligned with dim line
        "dimtoh": 0,
        "dimjust": 0,
        "dimlunit": 2,  # decimal
        "dimdsep": ord("."),
        "dimzin": 0,  # no zero suppression
        "dimclrd": 256,  # ByLayer
        "dimclre": 256,
        "dimclrt": 256,
        "dimlwd": -1,
        "dimlwe": -1,
        "dimdli": 7.0,
        "dimtofl": 1,
        "dimatfit": 3,
        "dimtmove": 0,
        "dimlfac": 1.0,
        "dimtol": 0,
        "dimlim": 0,
    }
    for s in SCALES:
        attrs = dict(base)
        attrs["dimscale"] = float(s)
        attrs["dimdec"] = 1 if s <= 10 else 0
        doc.dimstyles.add(f"AlSiraj-Dim{style_suffix(s)}", dxfattribs=attrs)
    # Fabrication / connection details - symmetrical +/- tolerance
    for s in (1, 2):
        attrs = dict(base)
        attrs.update(dimscale=float(s), dimdec=1, dimtol=1, dimtp=0.5,
                     dimtm=0.5, dimtdec=1, dimtfac=0.7)
        doc.dimstyles.add(f"AlSiraj-Dim-TOL{style_suffix(s)}", dxfattribs=attrs)


def add_mleader_styles(doc):
    txt_handle = doc.styles.get("STD-LABEL").dxf.handle
    for s in SCALES:
        ml = doc.mleader_styles.new(f"AlSiraj-MLeader{style_suffix(s)}")
        d = ml.dxf
        d.content_type = 2  # MText
        d.leader_type = 1  # straight
        d.max_leader_segments_points = 2
        d.leader_line_color = BYLAYER_RAW
        d.leader_lineweight = -1
        d.arrow_head_size = 2.5
        d.has_landing = 1
        d.has_dogleg = 1
        d.landing_gap_size = 2.0
        d.dogleg_length = 6.0
        d.text_style_handle = txt_handle
        d.text_color = BYLAYER_RAW
        d.char_height = H_LABEL
        d.text_left_attachment_type = 1  # middle of top line
        d.text_right_attachment_type = 1
        d.text_angle_type = 1
        d.scale = float(s)
        d.is_annotative = 0


# --------------------------------------------------------------------------
# Title block (Section 10.1) - block with attributes, 180 x 111 mm
# --------------------------------------------------------------------------
TB_W = 180.0
TB_H = 111.0


def _rect(space, x1, y1, x2, y2, layer):
    space.add_lwpolyline([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], close=True,
                         dxfattribs={"layer": layer})


def _text(space, s, x, y, h, style, layer, align=TextEntityAlignment.BOTTOM_LEFT):
    t = space.add_text(s, height=h, dxfattribs={"style": style, "layer": layer})
    t.set_placement((x, y), align=align)
    return t


def add_title_block_block(doc):
    blk = doc.blocks.new("ASG-TITLEBLOCK", base_point=(TB_W, 0))
    L, LT, LN = "A-TITLEBLOCK", "A-TEXT-TITLE", "A-TEXT-NOTES"
    W = TB_W
    _rect(blk, 0, 0, W, TB_H, L)

    def hline(y, x1=0, x2=W):
        blk.add_line((x1, y), (x2, y), dxfattribs={"layer": L})

    def vline(x, y1, y2):
        blk.add_line((x, y1), (x, y2), dxfattribs={"layer": L})

    def cap(s, x, y):
        _text(blk, s, x + 1.5, y - 1.5 - H_LABEL, H_LABEL * 0.9, "STD-LABEL", LN)

    def att(tag, prompt, default, x, y, h, style, layer=LN):
        a = blk.add_attdef(tag, insert=(x, y), text=default,
                           dxfattribs={"height": h, "style": style, "layer": layer,
                                       "prompt": prompt})
        a.set_placement((x, y), align=TextEntityAlignment.BOTTOM_LEFT)

    # Row A 0-14: drawing number | rev
    hline(14)
    vline(140, 0, 14)
    cap("DRAWING No.", 0, 14)
    att("DWG_NO", "Drawing number", "AS-2026-000-ALU-SD-001-R0", 2, 2.5, H_SUB, "STD-TITLE", LT)
    cap("REV", 140, 14)
    att("REV", "Current revision", "R0", 152, 2.0, H_TITLE, "STD-TITLE", LT)

    # Row B 14-24: scale | date | sheet | size
    hline(24)
    for x in (45, 90, 135):
        vline(x, 14, 24)
    for x, c, tag, prm, dft in (
        (0, "SCALE", "SCALE", "Scale(s)", "AS SHOWN"),
        (45, "DATE", "DATE", "Issue date", "DD.MM.YYYY"),
        (90, "SHEET", "SHEET", "Sheet __ of __", "01 OF 01"),
        (135, "SHEET SIZE", "SIZE", "Sheet size", "A3"),
    ):
        cap(c, x, 24)
        att(tag, prm, dft, x + 2, 15.5, H_NOTES, "STD-NOTES")

    # Row C 24-34: drawn | checked | approved
    hline(34)
    for x in (60, 120):
        vline(x, 24, 34)
    for x, c, tag, prm in (
        (0, "DRAWN BY", "DRAWN", "Drawn by"),
        (60, "CHECKED BY", "CHECKED", "Checked by"),
        (120, "APPROVED BY", "APPROVED", "Approved by"),
    ):
        cap(c, x, 34)
        att(tag, prm, "---", x + 2, 25.5, H_NOTES, "STD-NOTES")

    # Row D 34-52: drawing title (2 lines)
    hline(52)
    cap("DRAWING TITLE", 0, 52)
    att("TITLE1", "Drawing title - line 1", "DRAWING TITLE", 2, 41.5, H_TITLE, "STD-TITLE", LT)
    att("TITLE2", "Drawing title - line 2", "ELEVATION / SECTION / DETAIL", 2, 36.0, H_SUB,
        "STD-SUBTITLE", LT)

    # Row E 52-68: project / client
    hline(60)
    hline(68)
    vline(24, 52, 68)
    _text(blk, "PROJECT", 1.5, 63, H_LABEL, "STD-LABEL", LN)
    _text(blk, "CLIENT", 1.5, 55, H_LABEL, "STD-LABEL", LN)
    att("PROJECT", "Project name", "PROJECT NAME", 26, 62.5, H_NOTES, "STD-NOTES")
    att("CLIENT", "Client / main contractor", "CLIENT NAME", 26, 54.5, H_NOTES, "STD-NOTES")

    # Row F 68-86: company + logo
    hline(86)
    vline(32, 68, 86)
    blk.add_lwpolyline([(3, 70), (29, 70), (29, 84), (3, 84)], close=True,
                       dxfattribs={"layer": L})
    _text(blk, "ASG", 16, 77, H_TITLE, "STD-TITLE", LT, TextEntityAlignment.MIDDLE_CENTER)
    _text(blk, "LOGO", 16, 72, H_LABEL * 0.9, "STD-LABEL", LN, TextEntityAlignment.MIDDLE_CENTER)
    _text(blk, COMPANY, 34, 79.5, 3.2, "STD-TITLE", LT)
    _text(blk, DIVISION, 34, 74.5, H_NOTES, "STD-NOTES", LN)
    att("CONTACT", "Company contact line", "UNITED ARAB EMIRATES", 34, 70.5, H_LABEL, "STD-LABEL")

    # Revision table 86-111: header row + 4 rows (latest on top)
    cols = [(0, 15, "REV"), (15, 40, "DATE"), (40, 160, "DESCRIPTION"), (160, W, "BY")]
    hline(91)
    for x in (15, 40, 160):
        vline(x, 86, TB_H)
    for x1, x2, c in cols:
        _text(blk, c, (x1 + x2) / 2, 88.5, H_LABEL, "STD-LABEL", LN, TextEntityAlignment.MIDDLE_CENTER)
    for i in range(4):
        y = 91 + i * 5
        if i:
            hline(y)
        n = i + 1
        for (x1, _x2, _c), key, prm in zip(cols, ("REV", "DATE", "DESC", "BY"),
                                            ("Rev", "Date", "Description", "By")):
            att(f"R{n}_{key}", f"Revision row {n} - {prm}", "", x1 + 1.5, y + 1.5,
                H_LABEL, "STD-LABEL")


def add_symbol_blocks(doc):
    # Section mark: circle 10 mm with letter attribute (paper size, insert x scale)
    blk = doc.blocks.new("ASG-SECTION-MARK")
    blk.add_circle((0, 0), 5.0, dxfattribs={"layer": "0"})
    a = blk.add_attdef("SEC", insert=(0, 0), text="A",
                       dxfattribs={"height": H_SUB, "style": "STD-TITLE", "layer": "0",
                                   "prompt": "Section letter"})
    a.set_placement((0, 0), align=TextEntityAlignment.MIDDLE_CENTER)
    blk.add_solid([(-2.5, -5.5), (2.5, -5.5), (0, -9.0)], dxfattribs={"layer": "0"})

    # Revision delta tag (Section 10.3)
    blk = doc.blocks.new("ASG-REV-DELTA")
    blk.add_lwpolyline([(-4, -2.3), (4, -2.3), (0, 4.6)], close=True, dxfattribs={"layer": "0"})
    a = blk.add_attdef("REV", insert=(0, 0), text="1",
                       dxfattribs={"height": H_LABEL, "style": "STD-LABEL", "layer": "0",
                                   "prompt": "Revision number"})
    a.set_placement((0, 0), align=TextEntityAlignment.MIDDLE_CENTER)

    # Sealant / gasket symbol (Section 9 - symbol block, not a hatch); 10x10 unit
    blk = doc.blocks.new("ASG-SEALANT")
    blk.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=True,
                       dxfattribs={"layer": "0"})
    blk.add_arc((5, 10), 5, 180, 360, dxfattribs={"layer": "0"})

    # Window / door mark tag
    blk = doc.blocks.new("ASG-ITEM-TAG")
    blk.add_ellipse((0, 0), major_axis=(8, 0), ratio=0.55, dxfattribs={"layer": "0"})
    a = blk.add_attdef("MARK", insert=(0, 0), text="W-01",
                       dxfattribs={"height": H_NOTES, "style": "STD-TITLE", "layer": "0",
                                   "prompt": "Item mark"})
    a.set_placement((0, 0), align=TextEntityAlignment.MIDDLE_CENTER)


# --------------------------------------------------------------------------
# Sheets / layouts (Sections 2.1, 10, 12)
# --------------------------------------------------------------------------
SHEETS = {
    "A1": (841.0, 594.0, "ISO_full_bleed_A1_(841.00_x_594.00_MM)"),
    "A3": (420.0, 297.0, "ISO_full_bleed_A3_(420.00_x_297.00_MM)"),
}
M_LEFT, M_OTHER = 20.0, 10.0  # binding margin left, 10 mm elsewhere

STANDARD_NOTES = [
    "ALL DIMENSIONS ARE IN MILLIMETRES UNLESS NOTED OTHERWISE.",
    "DO NOT SCALE FROM THIS DRAWING - USE FIGURED DIMENSIONS ONLY.",
    "ALL OPENING SIZES / LEVELS TO BE VERIFIED AT SITE BEFORE FABRICATION.",
    "READ THIS DRAWING WITH THE ARCHITECTURAL / STRUCTURAL DRAWINGS AND SPECIFICATION.",
]


def setup_layout(doc, name, size_key):
    w, h, paper = SHEETS[size_key]
    lay = doc.layouts.new(name)
    lay.page_setup(size=(w, h), margins=(0, 0, 0, 0), units="mm", scale=1,
                   name=paper, device="DWG To PDF.pc3")
    lay.dxf.current_style_sheet = CTB_NAME
    lay.use_plot_styles(True)
    lay.print_lineweights(True)
    lay.scale_lineweights(False)
    lay.plot_centered(True)
    lay.show_plot_styles(False)
    lay.dxf.shade_plot_resolution_level = 3  # Presentation
    return lay


def draw_sheet(lay, size_key, attribs, notes):
    w, h, _ = SHEETS[size_key]
    _rect(lay, M_LEFT, M_OTHER, w - M_OTHER, h - M_OTHER, "A-TITLEBLOCK")
    tb = lay.add_blockref("ASG-TITLEBLOCK", (w - M_OTHER, M_OTHER),
                          dxfattribs={"layer": "A-TITLEBLOCK"})
    vals = {"SIZE": size_key}
    vals.update(attribs)
    tb.add_auto_attribs(vals)
    # General notes column above title block
    x = w - M_OTHER - TB_W
    top = h - M_OTHER
    lay.add_line((x, M_OTHER + TB_H), (x, top), dxfattribs={"layer": "A-TITLEBLOCK"})
    _text(lay, "GENERAL NOTES", x + 3, top - 8, H_SUB, "STD-TITLE", "A-TEXT-TITLE")
    body = "\\P".join(f"{i}. {n}" for i, n in enumerate(notes, 1))
    mt = lay.add_mtext(body, dxfattribs={"style": "STD-NOTES", "layer": "A-TEXT-NOTES",
                                         "char_height": H_NOTES, "width": TB_W - 8})
    mt.set_location((x + 3, top - 12), attachment_point=1)
    mt.dxf.line_spacing_factor = 1.3
    return x  # left edge of the right-hand column


def add_viewport(lay, x1, y1, x2, y2, model_center, scale):
    w, h = x2 - x1, y2 - y1
    vp = lay.add_viewport(center=((x1 + x2) / 2, (y1 + y2) / 2), size=(w, h),
                          view_center_point=model_center, view_height=h * scale,
                          dxfattribs={"layer": "A-VPORT"})
    vp.dxf.flags |= 16384  # display locked
    return vp


def view_title(lay, x, y, title, scale):
    t = _text(lay, title, x, y, H_SUB, "STD-TITLE", "A-TEXT-TITLE")
    t.dxf.text = f"%%U{title}"
    _text(lay, f"SCALE 1:{scale}", x, y - 5, H_NOTES, "STD-NOTES", "A-TEXT-NOTES")


# --------------------------------------------------------------------------
# Drafting helpers used by the sample drawing
# --------------------------------------------------------------------------
def poly(msp, pts, layer, close=True, ltype=None):
    attrs = {"layer": layer}
    if ltype:
        attrs["linetype"] = ltype
    return msp.add_lwpolyline(pts, close=close, dxfattribs=attrs)


def box(msp, x1, y1, x2, y2, layer):
    return poly(msp, [(x1, y1), (x2, y1), (x2, y2), (x1, y2)], layer)


def rect_pts(x1, y1, x2, y2):
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]


def hatch(msp, material, paths, drawing_scale):
    """Hatch per Section 9; model-space pattern scale = table scale x drawing scale."""
    pattern, sc, ang, layer = HATCH[material]
    hh = msp.add_hatch(dxfattribs={"layer": layer})
    if pattern == "SOLID":
        hh.set_solid_fill(color=256)
    else:
        hh.set_pattern_fill(pattern, scale=sc * drawing_scale, angle=ang - 45, color=256)
    for i, p in enumerate(paths):
        hh.paths.add_polyline_path(p, is_closed=True, flags=1 if i == 0 else 16)
    return hh


def hollow_section(msp, x1, y1, x2, y2, t, scale):
    """Aluminium hollow profile: outline + SOLID cut-section fill."""
    outer = rect_pts(x1, y1, x2, y2)
    inner = rect_pts(x1 + t, y1 + t, x2 - t, y2 - t)
    hatch(msp, "ALU", [outer, inner], scale)
    poly(msp, outer, "ALU-OUTLINE")
    poly(msp, inner, "ALU-OUTLINE")


def solid_plate(msp, x1, y1, x2, y2, scale, material="ALU", outline="ALU-OUTLINE"):
    pts = rect_pts(x1, y1, x2, y2)
    hatch(msp, material, [pts], scale)
    poly(msp, pts, outline)


def dim_lin(msp, p1, p2, base, scale, angle=0, style=None):
    d = msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=angle,
                           dimstyle=style or f"AlSiraj-Dim{style_suffix(scale)}",
                           dxfattribs={"layer": "A-DIM"})
    d.render()


def callout(msp, text, target, text_pos, scale, layer="A-LEADER", side=None):
    """AlSiraj-MLeader callout: straight, 2 points (arrow + landing)."""
    ml = msp.add_multileader_mtext(f"AlSiraj-MLeader{style_suffix(scale)}",
                                   dxfattribs={"layer": layer})
    ml.multileader.dxf.scale = 1.0
    ml.context.set_scale(1.0)
    if side is None:
        side = (mleader.ConnectionSide.left if text_pos[0] >= target[0]
                else mleader.ConnectionSide.right)
    align = mleader.TextAlignment.left if side == mleader.ConnectionSide.left else mleader.TextAlignment.right
    ml.set_content(text, char_height=H_LABEL, alignment=align, style="STD-LABEL")
    ml.add_leader_line(side, [Vec2(target)])
    ml.set_overall_scaling(scale)
    ml.build(insert=Vec2(text_pos))
    return ml


def break_line(msp, p1, p2, layer, size):
    """Zig-zag break symbol between p1 and p2."""
    a, b = Vec2(p1), Vec2(p2)
    m = a.lerp(b, 0.5)
    d = (b - a).normalize()
    n = d.orthogonal()
    pts = [a, m - d * size * 0.5, m + n * size - d * size * 0.15,
           m - n * size + d * size * 0.15, m + d * size * 0.5, b]
    poly(msp, pts, layer, close=False)


# --------------------------------------------------------------------------
# Sample: W-01 two-panel sliding window - elevation 1:20 + jamb section 1:2
# --------------------------------------------------------------------------
W01_W, W01_H = 2400, 2100
SEC_ORIGIN = Vec2(4000, 300)  # section A-A drawn here in model space


def draw_elevation(msp):
    s = 20
    W, H = W01_W, W01_H
    f, sf = 50, 70  # frame & sash face widths
    mid = W / 2
    lap = 25  # half interlock
    # outer frame
    box(msp, 0, 0, W, H, "ALU-OUTLINE")
    box(msp, f, f, W - f, H - f, "ALU-OUTLINE")
    # right sash (outer track - in front)
    rx1, rx2 = mid - lap, W - f
    box(msp, rx1, f, rx2, H - f, "ALU-OUTLINE")
    box(msp, rx1 + sf, f + sf, rx2 - sf, H - f - sf, "ALU-OUTLINE")
    # left sash (inner track) - meeting stile concealed behind right sash
    lx1, lx2 = f, mid + lap
    poly(msp, [(rx1, f), (lx1, f), (lx1, H - f), (rx1, H - f)], "ALU-OUTLINE", close=False)
    msp.add_line((lx2, f), (lx2, H - f), dxfattribs={"layer": "A-HIDDEN"})
    msp.add_line((rx1, f), (lx2, f), dxfattribs={"layer": "A-HIDDEN"})
    msp.add_line((rx1, H - f), (lx2, H - f), dxfattribs={"layer": "A-HIDDEN"})
    poly(msp, [(rx1, f + sf), (lx1 + sf, f + sf), (lx1 + sf, H - f - sf), (rx1, H - f - sf)],
         "ALU-OUTLINE", close=False)
    # glass outlines + reflection marks
    for gx1, gx2 in ((lx1 + sf, rx1), (rx1 + sf, rx2 - sf)):
        box(msp, gx1 + 10, f + sf + 10, gx2 - 10, H - f - sf - 10, "GLZ-OUTLINE")
        cx, cy = (gx1 + gx2) / 2, H / 2
        for off in (0, 120):
            msp.add_line((cx - 300 + off, cy - 150), (cx - 100 + off, cy + 150),
                         dxfattribs={"layer": "GLZ-HATCH"})
    # handles
    for hx in (lx1 + sf / 2, rx1 + sf / 2):
        box(msp, hx - 10, H / 2 - 90, hx + 10, H / 2 + 90, "ALU-HARDWARE")
    # sliding arrows
    for x1, x2 in ((mid - 450, mid - 150), (mid + 450, mid + 150)):
        y = H / 2 - 450
        msp.add_line((x1, y), (x2, y), dxfattribs={"layer": "ALU-LABEL"})
        dirn = 1 if x2 > x1 else -1
        msp.add_solid([(x2, y), (x2 - dirn * 80, y + 30), (x2 - dirn * 80, y - 30)],
                      dxfattribs={"layer": "ALU-LABEL"})
    # setting-out centreline
    msp.add_line((mid, -100), (mid, H + 100), dxfattribs={"layer": "A-CENTER"})
    # section cut A-A through left jamb (arrows = viewing direction)
    y = 1450
    msp.add_line((-100, y), (350, y), dxfattribs={"layer": "A-CENTER"})
    for x in (-200, 450):
        msp.add_blockref("ASG-SECTION-MARK", (x, y),
                         dxfattribs={"layer": "A-LEADER", "xscale": s, "yscale": s}
                         ).add_auto_attribs({"SEC": "A"})
    # item tag
    msp.add_blockref("ASG-ITEM-TAG", (mid, H + 350),
                     dxfattribs={"layer": "A-TEXT-NOTES", "xscale": s, "yscale": s}
                     ).add_auto_attribs({"MARK": "W-01"})
    # dimensions (1:20, whole mm)
    dim_lin(msp, (0, 0), (W, 0), (0, -300), s)
    dim_lin(msp, (0, 0), (mid, 0), (0, -150), s)
    dim_lin(msp, (mid, 0), (W, 0), (0, -150), s)
    dim_lin(msp, (W, 0), (W, H), (W + 200, 0), s, angle=90)
    # callouts
    tx = W + 450
    callout(msp, "ALU. SLIDING FRAME\\PPC RAL 9016", (W - 25, H - 300), (tx, H - 150), s,
            "ALU-LABEL")
    callout(msp, "6mm CLEAR\\PTEMPERED GLASS", (W * 0.8, H * 0.72), (tx, H * 0.6), s,
            "GLZ-LABEL")
    callout(msp, "SLIDING HANDLE\\PWITH LOCK", (rx1 + sf / 2, H / 2 + 60), (tx, H * 0.35), s,
            "ALU-LABEL")


def draw_section(msp):
    s = 5
    o = SEC_ORIGIN
    P = lambda x, y: (o.x + x, o.y + y)  # noqa: E731

    def R(x1, y1, x2, y2):
        return rect_pts(o.x + x1, o.y + y1, o.x + x2, o.y + y2)

    # wall / reveal (architectural background)
    poly(msp, [P(-160, -20), P(0, -20), P(0, 220), P(-160, 220)], "XREF", close=False)
    break_line(msp, P(-160, -20), P(-160, 220), "XREF", 10)
    # exterior / interior labels
    _text(msp, "EXTERIOR", *P(170, -40), H_SUB * s, "STD-SUBTITLE", "A-TEXT-NOTES")
    _text(msp, "INTERIOR", *P(170, 230), H_SUB * s, "STD-SUBTITLE", "A-TEXT-NOTES")

    # outer frame jamb: hollow base + 3 fins forming two sash channels
    hollow_section(msp, o.x + 10, o.y + 50, o.x + 40, o.y + 150, 2.0, s)
    for y1 in (50, 99, 148):
        solid_plate(msp, o.x + 40, o.y + y1, o.x + 60, o.y + y1 + 2, s)
    # sash stile in inner channel
    hollow_section(msp, o.x + 45, o.y + 104, o.x + 130, o.y + 145, 1.6, s)
    # glazing legs + glass
    solid_plate(msp, o.x + 130, o.y + 113, o.x + 148, o.y + 114.6, s)
    solid_plate(msp, o.x + 130, o.y + 134.4, o.x + 148, o.y + 136, s)
    g1, g2 = 121.5, 127.5
    gl = R(132, g1, 330, g2)
    hatch(msp, "GLASS", [gl], s)
    poly(msp, gl[:2] + gl[2:], "GLZ-OUTLINE")
    break_line(msp, P(330, g1 - 10), P(330, g2 + 10), "GLZ-OUTLINE", 6)
    # EPDM glazing gaskets
    for y1, y2 in ((114.6, g1), (g2, 134.4)):
        box(msp, o.x + 134, o.y + y1, o.x + 146, o.y + y2, "MISC-SEALANT")
    # perimeter: insulation in gap, sealant + backer rod both faces
    hatch(msp, "INSUL", [R(0, 70, 10, 132)], s)
    box(msp, o.x + 0, o.y + 70, o.x + 10, o.y + 132, "MISC-INSULATION")
    for y1, y2, rod_y in ((50, 58, 63), (142, 150, 137)):
        poly(msp, R(0, y1, 10, y2), "MISC-SEALANT")
        msp.add_circle(P(5, rod_y), 5, dxfattribs={"layer": "MISC-SEALANT"})
    # SS anchor screw through frame into wall
    poly(msp, R(-75, 98, 26, 102), "MISC-ANCHOR")
    poly(msp, [P(26, 95), P(30, 95), P(30, 105), P(26, 105)], "MISC-ANCHOR")
    box(msp, o.x - 80, o.y + 95, o.x - 10, o.y + 105, "A-HIDDEN")
    msp.add_line(P(-90, 100), P(45, 100), dxfattribs={"layer": "A-CENTER"})

    # dimensions (1:5, one decimal)
    dim_lin(msp, P(10, 50), P(60, 50), P(0, 15), s)
    dim_lin(msp, P(60, 50), P(130, 50), P(0, 15), s)
    dim_lin(msp, P(10, 50), P(10, 150), P(-200, 0), s, angle=90)

    # callouts - right group (profiles / glass), left group (perimeter)
    tx = o.x + 380
    callout(msp, "ALU. SLIDING FRAME JAMB\\P(AS PER SYSTEM CATALOGUE)",
            P(25, 51), (tx, o.y + 10), s, "ALU-LABEL")
    callout(msp, "6mm CLEAR TEMPERED GLASS", P(280, g1), (tx, o.y + 80), s, "GLZ-LABEL")
    callout(msp, "EPDM GLAZING GASKET", P(140, g2 + 3), (tx, o.y + 160), s)
    callout(msp, "ALU. SLIDING SASH STILE", P(90, 145), (tx, o.y + 210), s, "ALU-LABEL")
    left = mleader.ConnectionSide.left
    callout(msp, "SILICONE SEAL ON BACKER ROD", P(5, 54), (o.x - 150, o.y - 50), s, side=left)
    callout(msp, "PU FOAM INSULATION", P(5, 125), (o.x - 150, o.y + 250), s, side=left)
    callout(msp, "SS A2 ANCHOR 6x80 + NYLON PLUG\\P@ 500 c/c MAX.", P(-60, 102),
            (o.x - 150, o.y + 300), s, side=left)


def draw_legend(doc):
    """A3 quick-reference legend sheet (paper space, 1:1)."""
    lay = setup_layout(doc, "STD-LEGEND", "A3")
    draw_sheet(lay, "A3", {
        "DWG_NO": "ASG-STD-CAD-001-LEGEND", "REV": "R0",
        "TITLE1": "CAD STANDARD LEGEND", "TITLE2": "LAYERS - HATCHES - TEXT - LINEWEIGHTS",
        "PROJECT": "ASG-STD-CAD-001 QUICK REFERENCE", "CLIENT": "INTERNAL",
        "SCALE": "1:1", "DATE": "10.10.2026", "SHEET": "01 OF 01",
        "DRAWN": "ESTIMATION", "CHECKED": "---", "APPROVED": "---",
        "R1_REV": "R0", "R1_DATE": "10.10.2026", "R1_DESC": "INITIAL ISSUE", "R1_BY": "ASG",
    }, STANDARD_NOTES + ["ALL LAYERS PLOT BLACK VIA AlSiraj_ShopDrawing.ctb; WEIGHT = LAYER LINEWEIGHT."])

    # Layer table
    x0, y = 25, 280
    _text(lay, "%%ULAYER STANDARD", x0, y, H_SUB, "STD-TITLE", "A-TEXT-TITLE")
    y -= 7
    for c, xo in (("LAYER", 0), ("ACI", 34), ("LW", 44), ("SAMPLE", 54)):
        _text(lay, c, x0 + xo, y, H_LABEL, "STD-LABEL", "A-TEXT-NOTES")
    rows = [("0", 7, None, "Continuous", True, "")] + LAYERS
    per_col = 16
    for i, (name, aci, lw, lt, plot, _d) in enumerate(rows[1:]):
        col, r = divmod(i, per_col)
        x = x0 + col * 72
        yy = y - 5.5 - r * 5.2
        if col and r == 0:
            pass
        _text(lay, name, x, yy, H_LABEL, "STD-LABEL", "A-TEXT-NOTES")
        _text(lay, str(aci), x + 34, yy, H_LABEL, "STD-LABEL", "A-TEXT-NOTES")
        _text(lay, "DEF" if lw is None else f"{lw:.2f}", x + 42, yy, H_LABEL, "STD-LABEL", "A-TEXT-NOTES")
        lay.add_line((x + 52, yy + 1), (x + 68, yy + 1), dxfattribs={"layer": name})
    for col in (1,):
        _text(lay, "LAYER", x0 + col * 72, y, H_LABEL, "STD-LABEL", "A-TEXT-NOTES")
        _text(lay, "ACI", x0 + col * 72 + 34, y, H_LABEL, "STD-LABEL", "A-TEXT-NOTES")
        _text(lay, "LW", x0 + col * 72 + 44, y, H_LABEL, "STD-LABEL", "A-TEXT-NOTES")
        _text(lay, "SAMPLE", x0 + col * 72 + 54, y, H_LABEL, "STD-LABEL", "A-TEXT-NOTES")

    # Hatch legend
    y = 170
    _text(lay, "%%UHATCH BY MATERIAL (SECTION 9)", x0, y, H_SUB, "STD-TITLE", "A-TEXT-TITLE")
    items = [("ALU", "ALUMINIUM - SOLID"), ("GLASS", "GLASS - ANSI31 0.5 @45"),
             ("MS", "MILD STEEL - ANSI32 1.0 @45"), ("SS", "STAINLESS - ANSI31 0.75 @135"),
             ("INSUL", "INSULATION - ANSI37 1.0 @45")]
    for i, (key, label) in enumerate(items):
        x = x0 + i * 40
        pts = rect_pts(x, y - 30, x + 30, y - 8)
        hatch(lay, key, [pts], 1)
        outline = {"ALU": "ALU-OUTLINE", "GLASS": "GLZ-OUTLINE", "MS": "MS-STRUCT",
                   "SS": "SS-STRUCT", "INSUL": "MISC-INSULATION"}[key]
        poly(lay, pts, outline)
        mt = lay.add_mtext(label.replace(" - ", "\\P"),
                           dxfattribs={"style": "STD-LABEL", "layer": "A-TEXT-NOTES",
                                       "char_height": H_LABEL, "width": 36})
        mt.set_location((x, y - 33), attachment_point=1)
    lay.add_blockref("ASG-SEALANT", (x0 + 200, y - 30),
                     dxfattribs={"layer": "MISC-SEALANT", "xscale": 2.2, "yscale": 2.2})
    _text(lay, "SEALANT (SYMBOL BLOCK)", x0 + 200, y - 37, H_LABEL, "STD-LABEL", "A-TEXT-NOTES")

    # Text styles
    y = 112
    _text(lay, "%%UTEXT STYLES (SECTION 6) - ARIAL", x0, y, H_SUB, "STD-TITLE", "A-TEXT-TITLE")
    yy = y - 9
    for name, _f, _b, h in TEXT_STYLES:
        _text(lay, f"{name}  {h:.1f} mm  - ABC abc 123", x0, yy, h, name, "A-TEXT-NOTES")
        yy -= h + 4

    # Dimension + leader sample
    y = 58
    _text(lay, "%%UDIMENSION / MULTILEADER", x0, y, H_SUB, "STD-TITLE", "A-TEXT-TITLE")
    box(lay, x0, 22, x0 + 60, 40, "ALU-OUTLINE")
    dim_lin(lay, (x0, 40), (x0 + 60, 40), (0, 48), 1)
    dim_lin(lay, (x0 + 60, 22), (x0 + 60, 40), (x0 + 70, 0), 1, angle=90)
    callout(lay, "AlSiraj-MLeader\\PSTD-LABEL 2.0", (x0 + 30, 31), (x0 + 95, 45), 1)
    lay.add_blockref("ASG-REV-DELTA", (x0 + 150, 30), dxfattribs={"layer": "A-REVCLOUD"}
                     ).add_auto_attribs({"REV": "1"})
    _text(lay, "REVISION DELTA", x0 + 145, 22, H_LABEL, "STD-LABEL", "A-TEXT-NOTES")


# --------------------------------------------------------------------------
# Build files
# --------------------------------------------------------------------------
def build_template():
    doc = new_document()
    a3 = setup_layout(doc, "AlSiraj-A3-Plot", "A3")
    a1 = setup_layout(doc, "AlSiraj-A1-Plot", "A1")
    doc.layouts.delete("Layout1")
    blank = {"DWG_NO": "AS-YYYY-NNN-DIS-TYP-001-R0", "REV": "R0",
             "TITLE1": "DRAWING TITLE", "TITLE2": "ELEVATION / SECTION / DETAIL",
             "PROJECT": "PROJECT NAME", "CLIENT": "CLIENT NAME",
             "SCALE": "AS SHOWN", "DATE": "DD.MM.YYYY", "SHEET": "01 OF 01",
             "DRAWN": "---", "CHECKED": "---", "APPROVED": "---",
             "R1_REV": "R0", "R1_DATE": "DD.MM.YYYY", "R1_DESC": "FIRST ISSUE FOR APPROVAL",
             "R1_BY": "---"}
    notes = STANDARD_NOTES + ["(ADD PROJECT-SPECIFIC NOTES)"]
    xr = draw_sheet(a3, "A3", blank, notes)
    add_viewport(a3, M_LEFT + 5, M_OTHER + 5, xr - 5, 297 - M_OTHER - 5, (1000, 1000), 10)
    xr = draw_sheet(a1, "A1", dict(blank, SIZE="A1"), notes)
    add_viewport(a1, M_LEFT + 5, M_OTHER + 5, xr - 5, 594 - M_OTHER - 5, (10000, 6000), 50)
    doc.set_modelspace_vport(height=3000, center=(1500, 1000))
    path = OUT / "AlSiraj_ShopDrawing_Template.dxf"
    doc.saveas(path)
    return path


def build_sample():
    doc = new_document()
    msp = doc.modelspace()
    draw_elevation(msp)
    draw_section(msp)
    lay = setup_layout(doc, "SD-001", "A3")
    doc.layouts.delete("Layout1")
    xr = draw_sheet(lay, "A3", {
        "DWG_NO": "AS-2026-000-ALU-SD-001-R0", "REV": "R0",
        "TITLE1": "SLIDING WINDOW W-01", "TITLE2": "ELEVATION & JAMB SECTION A-A",
        "PROJECT": "SAMPLE PROJECT - TYPICAL VILLA", "CLIENT": "SAMPLE CLIENT",
        "SCALE": "1:20, 1:5", "DATE": "10.10.2026", "SHEET": "01 OF 01",
        "DRAWN": "A. A. QAMAR", "CHECKED": "---", "APPROVED": "---",
        "R1_REV": "R0", "R1_DATE": "10.10.2026", "R1_DESC": "FIRST ISSUE FOR APPROVAL",
        "R1_BY": "AAQ",
    }, STANDARD_NOTES + [
        "ALUMINIUM: 6063-T6 EXTRUSIONS, POWDER COATED (COLOUR AS APPROVED SAMPLE).",
        "GLASS: 6mm CLEAR FULLY TEMPERED, EDGES POLISHED.",
        "FIXINGS: STAINLESS STEEL GRADE A2 (SS304) UNLESS NOTED.",
        "PERIMETER: PU FOAM + SILICONE WEATHER SEAL ON BACKER ROD, BOTH FACES.",
        "PROFILE GEOMETRY IS INDICATIVE - REFER SYSTEM SUPPLIER CATALOGUE.",
    ])
    # elevation viewport 1:20 (top-left), section viewport 1:2 (bottom-left)
    add_viewport(lay, 25, 117, xr - 5, 282, (1520, 1000), 20)
    view_title(lay, 30, 124, "ELEVATION - W-01 (VIEWED FROM OUTSIDE)", 20)
    add_viewport(lay, 25, 15, xr - 5, 112, (SEC_ORIGIN.x + 190, SEC_ORIGIN.y + 70), 5)
    view_title(lay, 30, 21, "SECTION A-A - TYPICAL JAMB", 5)
    lay.add_line((M_LEFT, 114.5), (xr, 114.5), dxfattribs={"layer": "A-TITLEBLOCK"})
    draw_legend(doc)
    doc.set_modelspace_vport(height=3500, center=(2500, 1000))
    path = OUT / "AS-2026-000-ALU-SD-001-R0_Sample-W01.dxf"
    doc.saveas(path)
    return path


def build_ctb():
    ctb = acadctb.new_ctb()
    ctb.description = "Al Siraj Group - all colours plot black, object lineweight"
    for aci in range(1, 256):
        st = ctb[aci]
        st.color = (0, 0, 0)
        st.set_lineweight(0.0)  # 0.0 = use object lineweight
        st.linetype = acadctb.OBJECT_LINETYPE
        st.screen = 100
        st.description = ""
    path = OUT / CTB_NAME
    ctb.save(path)
    return path


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for p in (build_template(), build_sample(), build_ctb()):
        print("written", p)
