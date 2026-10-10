"""
ASG CAD MASTER STANDARD - single source of truth + DXF builder.
Saeed Al Siraj Glass & Aluminium Works L.L.C. | Al Siraj Group | UAE

Every table in the documentation, the layer register and the QA checks is
read from the definitions in this module, so the standard, the files and the
tests cannot drift apart.

Builder: ezdxf (DXF R2018 / AC1032). Features ezdxf cannot write natively
(annotation scale list) are added as raw DXF tags and re-validated; features
it cannot write at all (table styles, named page setups) are created in
AutoCAD by ASG_Setup.lsp.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

import ezdxf
from ezdxf import colors
from ezdxf.addons import acadctb
from ezdxf.enums import TextEntityAlignment

STANDARD_REV = "R0"
COMPANY = "SAEED AL SIRAJ GLASS & ALUMINIUM WORKS L.L.C."
GROUP = "AL SIRAJ GROUP"
DIVISION = "ALUMINIUM, GLASS & FACADE DIVISION  |  UNITED ARAB EMIRATES"
CTB_NAME = "ASG_Monochrome.ctb"
PLOTTER = "DWG To PDF.pc3"

# ---------------------------------------------------------------------------
# 03 Units & drawing-resident variables  (var, value, purpose)
# ---------------------------------------------------------------------------
HEADER_VARS = [
    ("$INSUNITS", 4, "Insertion units = millimetres (no unit conversion on block insert)"),
    ("$MEASUREMENT", 1, "Metric - acadiso.lin / acadiso.pat used"),
    ("$LUNITS", 2, "Linear units = Decimal"),
    ("$LUPREC", 0, "Linear display precision 0 dp"),
    ("$AUNITS", 0, "Angular units = Decimal Degrees"),
    ("$AUPREC", 2, "Angle precision 0.00"),
    ("$ANGBASE", 0.0, "0 deg = East"),
    ("$ANGDIR", 0, "Counter-clockwise positive"),
    ("$LIMMIN", (0.0, 0.0), "Nominal limits origin"),
    ("$LIMMAX", (200000.0, 150000.0), "Nominal 200 x 150 m - never restrictive"),
    ("$LIMCHECK", 0, "Limits not enforced (large facade elevations)"),
    ("$LTSCALE", 1.0, "Global linetype scale 1 - dash lengths in paper mm"),
    ("$PSLTSCALE", 1, "Viewport scale controls linetype scale"),
    ("$CELTSCALE", 1.0, "Object linetype scale default"),
    ("$LWDISPLAY", 1, "Show lineweights on screen"),
    ("$CELWEIGHT", -1, "New objects lineweight ByLayer"),
    ("$CECOLOR", 256, "New objects colour ByLayer"),
    ("$ORTHOMODE", 0, "Ortho off - polar tracking preferred"),
    ("$DIMASSOC", 2, "Associative dimensions follow geometry"),
    ("$PLINEGEN", 1, "Continuous linetype pattern along polylines"),
    ("$FILLMODE", 1, "Fills displayed"),
    ("$MIRRTEXT", 0, "Text not mirrored"),
    ("$TEXTSIZE", 2.5, "Default text height"),
    ("$PSTYLEMODE", 1, "Colour-dependent plot styles (CTB)"),
    ("$WORLDVIEW", 1, "UCS follows WCS in views"),
    ("$UCSORG", (0.0, 0.0, 0.0), "UCS origin at WCS origin"),
    ("$UCSXDIR", (1.0, 0.0, 0.0), "UCS = World"),
    ("$UCSYDIR", (0.0, 1.0, 0.0), "UCS = World"),
    ("$VISRETAIN", 1, "Xref layer overrides retained"),
    ("$PROXYGRAPHICS", 1, "Proxy images saved for interoperability"),
]
CURRENT_LAYER = "ASG-OUTLINE-PRIMARY"
# set after styles exist
HEADER_STYLE_VARS = [
    ("$CLAYER", CURRENT_LAYER, "Default current layer (plottable geometry)"),
    ("$TEXTSTYLE", "ASG-TEXT-ANNO", "Default text style"),
    ("$DIMSTYLE", "ASG-DIM-ANNO", "Default dimension style"),
    ("$CMLSTYLE", "ASG-MLINE-2", "Default multiline style"),
]

# Machine / profile (NOT stored in DWG/DWT) - applied only by ASG-PROFILE on request
PROFILE_VARS = [
    ("OSMODE", "2223", "Endpoint, Midpoint, Centre, Node, Intersection, Perpendicular, Extension"),
    ("AUTOSNAP", "63", "Marker, magnet, tooltip, aperture box, polar + object snap tracking"),
    ("POLARANG", "45", "Polar increment"),
    ("DYNMODE / DYNPROMPT", "3 / 1", "Dynamic input"),
    ("SELECTIONCYCLING", "2", "Cycle overlapping objects with list"),
    ("GRIPS / GRIPSIZE", "1 / 5", "Grips on"),
    ("PICKBOX / APERTURE", "4 / 8", "Selection target sizes"),
    ("PICKFIRST / PICKADD", "1 / 2", "Noun-verb selection, Shift to remove"),
    ("MSLTSCALE", "1", "Model-space linetypes follow annotation scale"),
    ("ANNOAUTOSCALE", "0", "Do NOT auto-add scales to annotative objects"),
    ("ANNOALLVISIBLE", "0", "Show only annotation of the current scale"),
    ("SAVETIME / ISAVEBAK", "10 / 1", "Autosave 10 min, keep .bak"),
    ("LAYOUTREGENCTL", "2", "Fast layout switching"),
    ("HPLAYER / DIMLAYER", "ASG-HATCH / ASG-DIMENSION", "Auto-layer for hatch & dims (AutoCAD 2016+)"),
    ("REFPATHTYPE", "1", "Relative xref paths"),
    ("UCSFOLLOW / UCSVP", "0 / 1", "UCS stays World per viewport"),
]

# ---------------------------------------------------------------------------
# 04 Linetypes (acadiso values, mm)
# ---------------------------------------------------------------------------
LINETYPES = {
    "HIDDEN": ([9.525, 6.35, -3.175], "Hidden __ __ __"),
    "HIDDEN2": ([4.7625, 3.175, -1.5875], "Hidden (.5x) _ _ _"),
    "CENTER": ([50.8, 31.75, -6.35, 6.35, -6.35], "Center ____ _ ____"),
    "CENTER2": ([25.4, 15.875, -3.175, 3.175, -3.175], "Center (.5x) ___ _ ___"),
    "DASHED": ([19.05, 12.7, -6.35], "Dashed __ __"),
    "DASHED2": ([9.525, 6.35, -3.175], "Dashed (.5x) _ _"),
    "DASHDOT": ([25.4, 12.7, -6.35, 0.0, -6.35], "Dash dot __ . __"),
    "DASHDOT2": ([12.7, 6.35, -3.175, 0.0, -3.175], "Dash dot (.5x) _ . _"),
    "PHANTOM": ([63.5, 31.75, -6.35, 6.35, -6.35, 6.35, -6.35], "Phantom ___ _ _ ___"),
    "PHANTOM2": ([31.75, 15.875, -3.175, 3.175, -3.175, 3.175, -3.175], "Phantom (.5x) __ _ _ __"),
    "DOT": ([6.35, 0.0, -6.35], "Dot . . ."),
}

# ---------------------------------------------------------------------------
# 04 Layer dictionary
# code, name, group, ACI, linetype, lw mm, plot, description, recommended use
# Palette: 7 primary | 8 secondary | 4 glass | 3 annotation | 1 revision |
#          6 non-plot | 251-253 plotted grey (via CTB)
# ---------------------------------------------------------------------------
LAYERS = [
    ("G01", "ASG-OUTLINE-PRIMARY", "Geometry", 7, "Continuous", 0.35, True,
     "Primary visible outlines", "Overall frame / panel outlines in elevation and plan"),
    ("G02", "ASG-OUTLINE-SECONDARY", "Geometry", 8, "Continuous", 0.18, True,
     "Secondary visible lines", "Edges beyond, minor returns, internal lines"),
    ("G03", "ASG-ALUMINIUM-PROFILE", "Geometry", 7, "Continuous", 0.25, True,
     "Aluminium profiles", "Frames, mullions, transoms, sashes, beads (elevation and section)"),
    ("G04", "ASG-GLASS", "Geometry", 4, "Continuous", 0.18, True,
     "Glass and mirror", "Glass / mirror edges, DGU / laminate interlayer lines"),
    ("G05", "ASG-STAINLESS-STEEL", "Geometry", 7, "Continuous", 0.25, True,
     "Stainless steel", "SS fittings, spigots, channels, handrails, patch plates"),
    ("G06", "ASG-MILD-STEEL", "Geometry", 7, "Continuous", 0.30, True,
     "Mild steel", "MS brackets, sub-frames, support steel, base plates"),
    ("G07", "ASG-HARDWARE", "Geometry", 8, "Continuous", 0.18, True,
     "Hardware", "Hinges, handles, locks, rollers, closers, patch fittings"),
    ("G08", "ASG-FIXING", "Geometry", 8, "Continuous", 0.18, True,
     "Fixings", "Anchors, screws, bolts, rivets, fixing brackets"),
    ("G09", "ASG-GASKET", "Geometry", 8, "Continuous", 0.13, True,
     "Gaskets", "EPDM gaskets, brushes, setting / distance blocks"),
    ("G10", "ASG-SEALANT", "Geometry", 8, "Continuous", 0.13, True,
     "Sealants", "Structural / weather silicone, backer rod, tapes"),
    ("G11", "ASG-INSULATION", "Geometry", 252, "Continuous", 0.13, True,
     "Insulation", "Insulation and thermal breaks (plots grey)"),
    ("G12", "ASG-CLADDING", "Geometry", 7, "Continuous", 0.25, True,
     "Cladding", "ACP / solid panels, flashings, copings"),
    ("T01", "ASG-HIDDEN", "Technical", 8, "HIDDEN2", 0.18, True,
     "Hidden geometry", "Concealed edges, embedded parts"),
    ("T02", "ASG-CENTERLINE", "Technical", 8, "CENTER2", 0.13, True,
     "Centrelines", "Axes of symmetry, hole centres, module lines"),
    ("T03", "ASG-CUTTING-PLANE", "Technical", 7, "PHANTOM2", 0.35, True,
     "Cutting planes", "Section cut lines (markers go on ASG-SYMBOL)"),
    ("T04", "ASG-SECTION-CUT", "Technical", 7, "Continuous", 0.40, True,
     "Section cut outlines", "Outline of material cut by the section plane - heaviest geometry"),
    ("T05", "ASG-HATCH", "Technical", 252, "Continuous", 0.09, True,
     "Section hatching", "Pattern hatches in sections (plots grey)"),
    ("T06", "ASG-HATCH-FILL", "Technical", 251, "Continuous", 0.09, True,
     "Solid fills", "Solid fill of thin aluminium / steel walls (plots dark grey)"),
    ("T07", "ASG-SETOUT", "Technical", 8, "DASHDOT2", 0.13, True,
     "Setting-out geometry (plotted)", "Opening lines, setting-out lines that must print"),
    ("T08", "ASG-REFERENCE", "Technical", 253, "Continuous", 0.13, True,
     "Reference geometry", "Architectural / structural background, xrefs (plots light grey)"),
    ("T09", "ASG-CONSTRUCTION", "Technical", 6, "Continuous", 0.05, False,
     "Construction geometry (NOT plotted)", "Temporary helper lines only - never final geometry"),
    ("A01", "ASG-DIMENSION", "Annotation", 3, "Continuous", 0.13, True,
     "Dimensions", "All dimensions"),
    ("A02", "ASG-TEXT", "Annotation", 7, "Continuous", 0.18, True,
     "General text", "Labels, view titles"),
    ("A03", "ASG-TEXT-NOTE", "Annotation", 7, "Continuous", 0.18, True,
     "Notes", "General and specification notes"),
    ("A04", "ASG-MULTILEADER", "Annotation", 3, "Continuous", 0.13, True,
     "Multileaders", "Callouts and material labels"),
    ("A05", "ASG-TABLE", "Annotation", 7, "Continuous", 0.18, True,
     "Tables", "Schedules, registers, note tables"),
    ("A06", "ASG-LEVEL", "Annotation", 3, "Continuous", 0.18, True,
     "Levels", "FFL / SSL / sill / head level markers"),
    ("A07", "ASG-GRID", "Annotation", 8, "CENTER", 0.13, True,
     "Grids", "Structural / architectural grid lines and bubbles"),
    ("A08", "ASG-REVISION", "Annotation", 1, "Continuous", 0.25, True,
     "Revision clouds", "Revision clouds and delta tags"),
    ("A09", "ASG-SYMBOL", "Annotation", 3, "Continuous", 0.25, True,
     "Drafting symbols", "Section / detail / elevation marks, north arrow"),
    ("S01", "ASG-BORDER", "Sheet", 7, "Continuous", 0.50, True,
     "Sheet borders", "Border frame in layouts"),
    ("S02", "ASG-TITLEBLOCK", "Sheet", 7, "Continuous", 0.25, True,
     "Title blocks", "Title block insert and attributes"),
    ("S03", "ASG-VIEWPORT", "Sheet", 6, "Continuous", 0.00, False,
     "Viewports (NOT plotted)", "All layout viewports"),
    ("S04", "ASG-NOPLOT", "Sheet", 6, "Continuous", 0.00, False,
     "Non-plot objects", "Internal markups, reminders - never printed"),
]

LW_MATRIX = [
    (0.50, "Sheet border"),
    (0.40, "Section cut outline"),
    (0.35, "Primary outline, cutting plane"),
    (0.30, "Mild steel"),
    (0.25, "Aluminium, stainless, cladding, symbols, title block, revision"),
    (0.18, "Secondary lines, glass, hardware, fixings, hidden, text"),
    (0.13, "Dimensions, leaders, centrelines, seals, insulation, set-out, reference"),
    (0.09, "Hatches and fills"),
]

# ---------------------------------------------------------------------------
# 05 Text styles: name, ttf, bold, annotative, use
# ---------------------------------------------------------------------------
TEXT_STYLES = [
    ("ASG-TEXT-ANNO", "arial.ttf", False, True, "Model-space general text / dimension text"),
    ("ASG-TEXT-NOTE", "arial.ttf", False, True, "Model-space notes, material labels, leaders"),
    ("ASG-TEXT-SMALL", "arial.ttf", False, True, "Small detail notes, profile codes"),
    ("ASG-TEXT-TITLE", "arialbd.ttf", True, False, "Detail / view titles (paper space)"),
    ("ASG-TEXT-HEADING", "arialbd.ttf", True, False, "Drawing titles, section headings (paper space)"),
    ("ASG-TEXT-SHEET", "arial.ttf", False, False, "Title block fields, sheet text (paper space)"),
]
TEXT_HEIGHTS = [  # use, plotted mm, style
    ("General dimensions", 2.5, "ASG-TEXT-ANNO (via dim style)"),
    ("Technical notes", 2.5, "ASG-TEXT-NOTE"),
    ("Material labels", 2.5, "ASG-TEXT-NOTE (via ASG-ML-ANNO)"),
    ("Small detail notes", 1.8, "ASG-TEXT-SMALL"),
    ("Detail titles", 3.5, "ASG-TEXT-TITLE"),
    ("Drawing titles", 5.0, "ASG-TEXT-HEADING"),
    ("Sheet headings", 7.0, "ASG-TEXT-HEADING (A1); 5.0 on A3/A4"),
]

# ---------------------------------------------------------------------------
# 05 Dimension styles
# ---------------------------------------------------------------------------
DIM_BASE = {
    "dimtxsty": "ASG-TEXT-ANNO", "dimtxt": 2.5, "dimasz": 2.5, "dimblk": "",
    "dimexo": 1.5, "dimexe": 1.25, "dimdli": 7.0, "dimdle": 0.0, "dimgap": 1.0,
    "dimtad": 1, "dimjust": 0, "dimtih": 0, "dimtoh": 0, "dimtix": 0,
    "dimatfit": 3, "dimtmove": 1, "dimtofl": 1, "dimsoxd": 0,
    "dimlunit": 2, "dimdec": 0, "dimdsep": ord("."), "dimrnd": 0.0, "dimzin": 8,
    "dimaunit": 0, "dimadec": 2, "dimazin": 2, "dimlfac": 1.0,
    "dimalt": 0, "dimaltf": 25.4, "dimaltd": 2,
    "dimtol": 0, "dimlim": 0, "dimtp": 0.0, "dimtm": 0.0, "dimtdec": 1, "dimtfac": 0.7,
    "dimclrd": 256, "dimclre": 256, "dimclrt": 256, "dimlwd": -2, "dimlwe": -2,
    "dimcen": 2.5, "dimupt": 0, "dimscale": 1.0,
}
DIM_STYLES = [
    # name, annotative, overrides, use
    ("ASG-DIM-ANNO", True, {}, "Default linear / aligned dimensions in model space, any viewport scale"),
    ("ASG-DIM-FIXED", False, {}, "Non-annotative: paper-space (trans-spatial) dimensioning over viewports, or 1:1 sheets"),
    ("ASG-DIM-DETAIL", True, {"dimdec": 1, "dimzin": 0, "dimtdec": 1},
     "Fabrication details: 0.0 precision; tolerance switched on per dimension (symmetrical, 0.7 height)"),
    ("ASG-DIM-ANGULAR", True, {"dimadec": 2, "dimazin": 0},
     "Angular dimensions, decimal degrees 0.00"),
    ("ASG-DIM-RADIUS", True, {"dimcen": 0.0, "dimtmove": 0, "dimtofl": 1},
     "Radius dimensions (R prefix automatic), no centre mark"),
    ("ASG-DIM-DIAMETER", True, {"dimcen": 2.5, "dimtmove": 0, "dimtofl": 1},
     "Diameter dimensions (diameter symbol automatic), centre mark 2.5"),
]

# ---------------------------------------------------------------------------
# 05 Multileader styles
# ---------------------------------------------------------------------------
MLEADER_STYLES = [
    # name, annotative, arrow block ("" = closed filled), arrow size, text style, height, frame, use
    ("ASG-ML-ANNO", True, "", 2.5, "ASG-TEXT-NOTE", 2.5, False, "Default model-space callouts and material labels"),
    ("ASG-ML-NOTE", False, "", 2.5, "ASG-TEXT-NOTE", 2.5, False, "Paper-space notes pointing into viewports"),
    ("ASG-ML-DETAIL", True, "_DOT", 1.5, "ASG-TEXT-SMALL", 1.8, False, "Dense 1:1 / 1:2 fabrication details"),
    ("ASG-ML-REFERENCE", True, "_OPEN30", 2.5, "ASG-TEXT-NOTE", 2.5, True, "References to other drawings / details (framed text)"),
]

ANNO_SCALES = [1, 2, 5, 10, 20, 25, 50, 100]

# ---------------------------------------------------------------------------
# 07 Table styles (created in AutoCAD by ASG_Setup.lsp)
# name, title (h, align), header (h, align), data (h, align), title supp, header supp, use
# ---------------------------------------------------------------------------
TABLE_STYLES = [
    ("ASG-TABLE-STANDARD", (3.5, "MC"), (2.5, "MC"), (2.5, "ML"), False, False, "Standard technical tables"),
    ("ASG-TABLE-MATERIAL", (3.5, "MC"), (2.0, "MC"), (2.0, "ML"), False, False, "Material schedules"),
    ("ASG-TABLE-GLASS", (3.5, "MC"), (2.0, "MC"), (2.0, "ML"), False, False, "Glass schedules"),
    ("ASG-TABLE-HARDWARE", (3.5, "MC"), (2.0, "MC"), (2.0, "ML"), False, False, "Hardware schedules"),
    ("ASG-TABLE-REVISION", (3.5, "MC"), (2.0, "MC"), (2.0, "ML"), True, False, "Revision registers"),
    ("ASG-TABLE-REGISTER", (3.5, "MC"), (2.5, "MC"), (2.5, "ML"), False, False, "Drawing registers"),
    ("ASG-TABLE-NOTES", (3.5, "ML"), (2.5, "ML"), (2.5, "TL"), False, True, "General notes"),
]

# ---------------------------------------------------------------------------
# 08 Sheets
# ---------------------------------------------------------------------------
SHEETS = [
    # layout / page setup name, w, h, paper base, title block, default vp scale
    ("A4-LANDSCAPE", 297.0, 210.0, "ISO_full_bleed_A4", "ASG-TB-A4", 10),
    ("A4-PORTRAIT", 210.0, 297.0, "ISO_full_bleed_A4", "ASG-TB-A4", 10),
    ("A3-LANDSCAPE", 420.0, 297.0, "ISO_full_bleed_A3", "ASG-TB-A3", 20),
    ("A3-PORTRAIT", 297.0, 420.0, "ISO_full_bleed_A3", "ASG-TB-A3", 20),
    ("A1-LANDSCAPE", 841.0, 594.0, "ISO_full_bleed_A1", "ASG-TB-A1", 50),
]
MARGIN_LEFT, MARGIN = 20.0, 10.0
TB_SPECS = {  # designed per sheet class - never stretched
    "ASG-TB-A4": dict(w=180.0, r=7.0, cap=1.8, val=2.5, title=3.5, num=3.5, comp=2.8),
    "ASG-TB-A3": dict(w=180.0, r=9.0, cap=2.0, val=2.5, title=5.0, num=3.5, comp=3.5),
    "ASG-TB-A1": dict(w=250.0, r=12.0, cap=2.5, val=3.5, title=7.0, num=5.0, comp=5.0),
}
TB_ATTRIBUTES = [  # tag, prompt, default
    ("PROJECT", "Project", "PROJECT NAME"),
    ("LOCATION", "Location", "LOCATION, UAE"),
    ("CLIENT", "Client", "CLIENT"),
    ("CONSULTANT", "Consultant", "CONSULTANT"),
    ("DWG_TITLE", "Drawing title", "DRAWING TITLE"),
    ("DWG_TITLE_2", "Drawing title - second line (optional)", ""),
    ("DWG_NO", "Drawing number", "AS-YYYY-NNN-DIS-TYP-001"),
    ("REV", "Revision", "R0"),
    ("DATE", "Date (DD.MM.YYYY)", "DD.MM.YYYY"),
    ("DRAWN_BY", "Drawn by", "-"),
    ("CHECKED_BY", "Checked by", "-"),
    ("APPROVED_BY", "Approved by", "-"),
    ("SCALE", "Scale", "AS SHOWN"),
    ("SHEET_NO", "Sheet number", "01 OF 01"),
    ("DWG_STATUS", "Drawing status", "PRELIMINARY"),
]

HATCH_STANDARD = [  # material, pattern, scale @ paper, angle prop, layer, note
    ("Glass (section)", "ANSI31", "0.5", "0", "ASG-HATCH", "Thin glass: two lines, no hatch"),
    ("Aluminium (section)", "SOLID", "-", "-", "ASG-HATCH-FILL", "Plots dark grey"),
    ("Mild steel (section)", "ANSI32", "1.0", "0", "ASG-HATCH", "Lines read 45 deg"),
    ("Stainless steel (section)", "ANSI31", "0.75", "90", "ASG-HATCH", "Lines read 135 deg"),
    ("Concrete", "AR-CONC", "0.05", "0", "ASG-REFERENCE", ""),
    ("Masonry / blockwork", "ANSI31", "1.0", "0", "ASG-REFERENCE", "AR-B816 in elevation"),
    ("Insulation", "INSUL", "0.05", "0", "ASG-INSULATION", "Fit to thickness"),
    ("Sealant", "SOLID", "-", "-", "ASG-SEALANT", ""),
    ("Generic fill", "ANSI37", "1.0", "0", "ASG-HATCH", ""),
]
ATTRIBUTE_STANDARD = [
    ("ITEM_CODE", "Item / product code"), ("ITEM_NAME", "Item description"),
    ("SYSTEM_NAME", "System / series"), ("MANUFACTURER", "Manufacturer / supplier (verified only)"),
    ("MATERIAL", "Base material"), ("FINISH", "Finish"), ("COLOUR", "Colour / RAL"),
    ("GLASS_SPEC", "Glass specification"), ("REVISION", "Block revision"),
]

BYLAYER_RAW = colors.BY_LAYER_RAW_VALUE
BYBLOCK_RAW = colors.BY_BLOCK_RAW_VALUE
TB_HEIGHTS: dict[str, float] = {}


# ===========================================================================
# Builder
# ===========================================================================
def _anno(entity):
    entity.set_xdata("AcadAnnotative", [(1000, "AnnotativeData"), (1002, "{"),
                                        (1070, 1), (1070, 1), (1002, "}")])


def _text(space, s, x, y, h, style, layer="0", align=TextEntityAlignment.BOTTOM_LEFT):
    t = space.add_text(s, height=h, dxfattribs={"style": style, "layer": layer})
    t.set_placement((x, y), align=align)
    return t


def new_document(sheets=SHEETS):
    doc = ezdxf.new("R2018", setup=False, units=4)
    doc.appids.add("AcadAnnotative")
    for var, val, _p in HEADER_VARS:
        doc.header[var] = val
    for name, (pattern, desc) in LINETYPES.items():
        doc.linetypes.add(name, pattern=pattern, description=desc)
    for _c, name, _g, aci, lt, lw, plot, desc, _u in LAYERS:
        lay = doc.layers.add(name, color=aci, linetype=lt)
        lay.dxf.lineweight = int(round(lw * 100))
        lay.dxf.plot = int(plot)
        lay.description = desc
    doc.layers.get("0").description = "System layer - block definitions only"
    for name, ttf, bold, anno, _u in TEXT_STYLES:
        st = doc.styles.add(name, font=ttf)
        st.dxf.height = 0.0
        st.dxf.width = 1.0
        st.set_extended_font_data(family="Arial", italic=False, bold=bold)
        if anno:
            _anno(st)
    std = doc.styles.get("Standard")
    std.dxf.font = "arial.ttf"
    std.set_extended_font_data(family="Arial", italic=False, bold=False)
    for name, anno, over, _u in DIM_STYLES:
        ds = doc.dimstyles.add(name, dxfattribs=dict(DIM_BASE, **over))
        if anno:
            _anno(ds)
    _mleader_styles(doc)
    _mline_styles(doc)
    for name, spec in TB_SPECS.items():
        if any(s[4] == name for s in sheets):
            _title_block(doc, name, **spec)
    _layouts(doc, sheets)
    for var, val, _p in HEADER_VARS + HEADER_STYLE_VARS:  # re-apply: page setup resets limits
        doc.header[var] = val
    doc.layouts.get("Model").dxf.limmax = HEADER_VARS[9][1]  # $LIMMAX is synced from Model layout on save
    doc.layouts.get("Model").dxf.limmin = HEADER_VARS[8][1]
    doc.set_modelspace_vport(height=20000, center=(10000, 7000))
    return doc


def _mleader_styles(doc):
    for name, anno, arrow, asz, tstyle, ch, frame, _u in MLEADER_STYLES:
        ml = doc.mleader_styles.new(name)
        d = ml.dxf
        d.content_type = 2
        d.leader_type = 1
        d.max_leader_segments_points = 2
        d.leader_line_color = BYLAYER_RAW
        d.leader_lineweight = -2
        d.arrow_head_size = asz
        if arrow:
            d.arrow_head_handle = ezdxf.ARROWS.arrow_handle(doc.blocks, arrow)
        d.has_landing = 1
        d.has_dogleg = 1
        d.dogleg_length = 4.0
        d.landing_gap_size = 1.0
        d.text_style_handle = doc.styles.get(tstyle).dxf.handle
        d.text_color = BYLAYER_RAW
        d.char_height = ch
        d.has_text_frame = int(frame)
        d.text_left_attachment_type = 1
        d.text_right_attachment_type = 1
        d.text_angle_type = 1
        d.scale = 1.0
        d.is_annotative = int(anno)


def _mline_styles(doc):
    m = doc.mline_styles.new("ASG-MLINE-2")
    m.dxf.description = "Two lines +/-0.5; MLINE scale = overall width"
    m.elements.append(0.5, 256, "BYLAYER")
    m.elements.append(-0.5, 256, "BYLAYER")
    m.dxf.flags = 16 | 256
    m = doc.mline_styles.new("ASG-MLINE-3")
    m.dxf.description = "Two lines + CENTER2 axis"
    m.elements.append(0.5, 256, "BYLAYER")
    m.elements.append(0.0, 256, "CENTER2")
    m.elements.append(-0.5, 256, "BYLAYER")
    m.dxf.flags = 16 | 256


def _title_block(doc, name, w, r, cap, val, title, num, comp):
    """Bottom-right title block. Base point = bottom-right corner (sheet margin)."""
    blk = doc.blocks.new(name)
    prompts = {t: p for t, p, _d in TB_ATTRIBUTES}
    defaults = {t: d for t, _p, d in TB_ATTRIBUTES}
    x0, pad = -w, 0.12 * r
    rows = [
        (1.5 * r, [(0.60, "DRAWING No.", "DWG_NO", num, "ASG-TEXT-HEADING"),
                   (0.15, "REV", "REV", num, "ASG-TEXT-HEADING"),
                   (0.25, "SHEET No.", "SHEET_NO", val, "ASG-TEXT-SHEET")]),
        (r, [(1 / 3, "SCALE", "SCALE", val, "ASG-TEXT-SHEET"),
             (1 / 3, "DATE", "DATE", val, "ASG-TEXT-SHEET"),
             (1 / 3, "DRAWING STATUS", "DWG_STATUS", val, "ASG-TEXT-SHEET")]),
        (r, [(1 / 3, "DRAWN BY", "DRAWN_BY", val, "ASG-TEXT-SHEET"),
             (1 / 3, "CHECKED BY", "CHECKED_BY", val, "ASG-TEXT-SHEET"),
             (1 / 3, "APPROVED BY", "APPROVED_BY", val, "ASG-TEXT-SHEET")]),
        ("TITLE", None),
        (r, [(0.5, "CLIENT", "CLIENT", val, "ASG-TEXT-SHEET"),
             (0.5, "CONSULTANT", "CONSULTANT", val, "ASG-TEXT-SHEET")]),
        (r, [(0.5, "PROJECT", "PROJECT", val, "ASG-TEXT-SHEET"),
             (0.5, "LOCATION", "LOCATION", val, "ASG-TEXT-SHEET")]),
        ("COMPANY", None),
    ]

    def att(tag, x, y, hh, style):
        a = blk.add_attdef(tag, insert=(x, y), text=defaults[tag],
                           dxfattribs={"height": hh, "style": style, "layer": "0",
                                       "prompt": prompts[tag]})
        a.set_placement((x, y), align=TextEntityAlignment.BOTTOM_LEFT)

    y = 0.0
    for height, cells in rows:
        if height == "TITLE":
            hh = 2 * r
            _text(blk, "DRAWING TITLE", x0 + pad, y + hh - pad - cap, cap, "ASG-TEXT-SHEET")
            att("DWG_TITLE", x0 + pad, y + hh * 0.40, title, "ASG-TEXT-HEADING")
            att("DWG_TITLE_2", x0 + pad, y + pad, val, "ASG-TEXT-TITLE")
        elif height == "COMPANY":
            hh = 1.6 * r
            _text(blk, COMPANY, x0 + pad, y + hh * 0.50, comp, "ASG-TEXT-HEADING")
            _text(blk, f"{GROUP}  |  {DIVISION}", x0 + pad, y + pad, cap, "ASG-TEXT-SHEET")
        else:
            hh = height
            x = x0
            for frac, caption, tag, th, style in cells:
                if x > x0:
                    blk.add_line((x, y), (x, y + hh), dxfattribs={"layer": "0"})
                _text(blk, caption, x + pad, y + hh - pad - cap, cap, "ASG-TEXT-SHEET")
                att(tag, x + pad, y + pad, min(th, hh - cap - 3 * pad), style)
                x += w * frac
        y += hh
        blk.add_line((x0, y), (0, y), dxfattribs={"layer": "0"})
    blk.add_lwpolyline([(x0, 0), (0, 0), (0, y), (x0, y)], close=True,
                       dxfattribs={"layer": "0", "const_width": 0})
    TB_HEIGHTS[name] = y


def _layouts(doc, sheets):
    for name, w, h, paper, tb, vps in sheets:
        if name in doc.layouts:  # idempotent
            continue
        lay = doc.layouts.new(name)
        lay.page_setup(size=(w, h), margins=(0, 0, 0, 0), units="mm", scale=(1, 1),
                       name=paper, device=PLOTTER)
        lay.dxf.current_style_sheet = CTB_NAME
        lay.use_plot_styles(True)
        lay.print_lineweights(True)
        lay.scale_lineweights(False)
        lay.plot_centered(True)
        lay.plot_viewport_borders(False)
        lay.show_plot_styles(False)
        lay.dxf.shade_plot_resolution_level = 3
        lay.add_lwpolyline([(MARGIN_LEFT, MARGIN), (w - MARGIN, MARGIN), (w - MARGIN, h - MARGIN),
                            (MARGIN_LEFT, h - MARGIN)], close=True, dxfattribs={"layer": "ASG-BORDER"})
        lay.add_blockref(tb, (w - MARGIN, MARGIN), dxfattribs={"layer": "ASG-TITLEBLOCK"}
                         ).add_auto_attribs({})
        x1, y1 = MARGIN_LEFT + 5, MARGIN + TB_HEIGHTS[tb] + 5
        x2, y2 = w - MARGIN - 5, h - MARGIN - 5
        if w > h:
            x2, y1 = w - MARGIN - TB_SPECS[tb]["w"] - 5, MARGIN + 5
        vp = lay.add_viewport(center=((x1 + x2) / 2, (y1 + y2) / 2), size=(x2 - x1, y2 - y1),
                              view_center_point=((x2 - x1) * vps / 2, (y2 - y1) * vps / 2),
                              view_height=(y2 - y1) * vps, dxfattribs={"layer": "ASG-VIEWPORT"})
        vp.dxf.flags |= 16384
    if "Layout1" in doc.layouts and len(doc.layouts) > 2:
        doc.layouts.delete("Layout1")


# ---------------------------------------------------------------------------
# Annotation scale list - raw AcDbScale objects (ezdxf has no SCALE class)
# ---------------------------------------------------------------------------
_SCALE = ("  0\nSCALE\n  5\n{h}\n102\n{{ACAD_REACTORS\n330\n{o}\n102\n}}\n330\n{o}\n"
          "100\nAcDbScale\n 70\n0\n300\n{n}\n140\n1.0\n141\n{d}\n290\n{u}\n")


def inject_annotation_scales(path: Path):
    doc = ezdxf.readfile(path)
    owner = doc.rootdict.get("ACAD_SCALELIST").dxf.handle
    if len(doc.rootdict.get("ACAD_SCALELIST")):
        return  # idempotent
    seed = int(doc.header["$HANDSEED"], 16)
    objs, entries = [], []
    for i, s in enumerate(ANNO_SCALES):
        hnd = format(seed + i, "X")
        objs.append(_SCALE.format(h=hnd, o=owner, n=f"1:{s}", d=float(s), u=int(s == 1)))
        entries += ["  3", f"A{i}", "350", hnd]
    lines = path.read_text().split("\n")
    out, i, state = [], 0, {"dict": False, "entries": False, "objs": False, "inobj": False}
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if s == "$HANDSEED":
            out += [ln, lines[i + 1], format(seed + len(ANNO_SCALES) + 1, "X")]
            i += 3
            continue
        out.append(ln)
        if s == "OBJECTS" and lines[i - 1].strip() == "2":
            state["inobj"] = True
        if s == "5" and lines[i + 1].strip() == owner and lines[i - 1].strip() == "DICTIONARY":
            state["dict"] = True
        if state["dict"] and not state["entries"] and s == "281":
            out.append(lines[i + 1])
            out += entries
            state["entries"] = True
            i += 2
            continue
        if state["inobj"] and not state["objs"] and s == "ENDSEC":
            out.pop()
            out.pop()
            out += "".join(objs).rstrip("\n").split("\n")
            out += ["  0", "ENDSEC"]
            state["objs"] = True
            state["inobj"] = False
        i += 1
    if not (state["entries"] and state["objs"]):
        raise RuntimeError("annotation scale injection failed")
    path.write_text("\n".join(out))


def save_dxf(doc, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(path)
    inject_annotation_scales(path)


# ---------------------------------------------------------------------------
# CTB - ezdxf's writer packs the header with native longs (8 bytes on 64-bit
# Linux), which AutoCAD cannot read; write three little-endian uint32 instead.
# ---------------------------------------------------------------------------
def _compress_ctb(stream, content: str):
    body = zlib.compress(content.encode())
    stream.write(b"PIAFILEVERSION_2.0,CTBVER1,compress\r\npmzlibcodec")
    stream.write(struct.pack("<LLL", zlib.adler32(body), len(content), len(body)))
    stream.write(body)


acadctb._compress = _compress_ctb
CTB_GREYS = {250: 51, 251: 91, 252: 132, 253: 173, 254: 214}


def build_ctb(path: Path):
    ctb = acadctb.new_ctb()
    ctb.description = "ASG monochrome: ACI 1-249,255 black; 250-254 grey; object lineweight/linetype"
    for aci in range(1, 256):
        st = ctb[aci]
        g = CTB_GREYS.get(aci, 0)
        st.color = (g, g, g)
        st.set_lineweight(0.0)
        st.linetype = acadctb.OBJECT_LINETYPE
        st.screen = 100
        st.description = ""
    path.parent.mkdir(parents=True, exist_ok=True)
    ctb.save(path)
