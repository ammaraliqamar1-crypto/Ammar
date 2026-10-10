"""
ASG CAD MASTER STANDARD - single source of truth + DXF builder.
Saeed Al Siraj Glass & Aluminium Works L.L.C. | Al Siraj Group | UAE

Every table in the documentation, the layer register, the AutoLISP setup/QA
file and the Python QA is generated from the definitions in this module, so
the standard, the files and the tests cannot drift apart.

Builder: ezdxf (DXF R2018 / AC1032).
  * written natively by ezdxf ........ units, layers, linetypes, text / dim /
                                        multileader / multiline styles, blocks,
                                        layouts, page settings, viewports
  * written as raw DXF tags .......... annotation scale list (AcDbScale) -
                                        re-read and checked by qa_validate.py
  * not writable by any DXF library .. table styles, named page setups and a
    used here                          few drawing variables -> created inside
                                        AutoCAD by ASG_Setup.lsp (ASG-SETUP)
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

import ezdxf
from ezdxf import colors
from ezdxf.addons import acadctb
from ezdxf.enums import TextEntityAlignment

STANDARD_REV = "R1"
STANDARD_DATE = "10.10.2026"
COMPANY = "SAEED AL SIRAJ GLASS & ALUMINIUM WORKS L.L.C."
GROUP = "AL SIRAJ GROUP"
DIVISION = "ALUMINIUM, GLASS & FACADE DIVISION  |  UNITED ARAB EMIRATES"
CTB_NAME = "ASG_Monochrome.ctb"
PLOTTER = "DWG To PDF.pc3"

# ---------------------------------------------------------------------------
# 03 Units - drawing-resident variables written into the DXF
# (var, value, purpose)
# ---------------------------------------------------------------------------
HEADER_VARS = [
    ("$INSUNITS", 4, "Insertion units = millimetres (no unit conversion on block insert)"),
    ("$MEASUREMENT", 1, "Metric - acadiso.lin / acadiso.pat"),
    ("$LUNITS", 2, "Linear units = Decimal"),
    ("$LUPREC", 0, "Linear display precision 0 dp"),
    ("$AUNITS", 0, "Angular units = Decimal Degrees"),
    ("$AUPREC", 2, "Angle display precision 0.00"),
    ("$ANGBASE", 0.0, "0 deg = East"),
    ("$ANGDIR", 0, "Counter-clockwise positive"),
    ("$LIMMIN", (0.0, 0.0), "Nominal limits origin"),
    ("$LIMMAX", (200000.0, 150000.0), "Nominal 200 x 150 m - never restrictive"),
    ("$LIMCHECK", 0, "Limits not enforced (large facade elevations)"),
    ("$LTSCALE", 1.0, "Global linetype scale 1 - dash lengths in paper mm"),
    ("$PSLTSCALE", 1, "Viewport scale controls paper-space linetype scaling"),
    ("$CELTSCALE", 1.0, "New-object linetype scale 1"),
    ("$LWDISPLAY", 1, "Lineweights displayed on screen"),
    ("$CELWEIGHT", -1, "New objects: lineweight ByLayer"),
    ("$CECOLOR", 256, "New objects: colour ByLayer"),
    ("$DIMASSOC", 2, "Associative dimensions follow geometry"),
    ("$PLINEGEN", 1, "Continuous linetype pattern along polylines"),
    ("$FILLMODE", 1, "Fills displayed"),
    ("$MIRRTEXT", 0, "Text not mirrored"),
    ("$TEXTSIZE", 2.5, "Default text height (paper mm for annotative styles)"),
    ("$PSTYLEMODE", 1, "Colour-dependent plot styles (CTB)"),
    ("$WORLDVIEW", 1, "UCS follows WCS in views"),
    ("$UCSORG", (0.0, 0.0, 0.0), "UCS origin = WCS origin"),
    ("$UCSXDIR", (1.0, 0.0, 0.0), "UCS = World"),
    ("$UCSYDIR", (0.0, 1.0, 0.0), "UCS = World"),
    ("$VISRETAIN", 1, "Xref layer overrides retained"),
    ("$PROXYGRAPHICS", 1, "Proxy images saved (interoperability)"),
]
CURRENT_LAYER = "ASG-OUTLINE-PRIMARY"
HEADER_STYLE_VARS = [  # applied after the styles exist
    ("$CLAYER", CURRENT_LAYER, "Default current layer (plottable geometry)"),
    ("$TEXTSTYLE", "ASG-TEXT-ANNO", "Default text style"),
    ("$DIMSTYLE", "ASG-DIM-ANNO", "Default dimension style (header dim vars synchronised - no overrides)"),
    ("$CMLSTYLE", "ASG-MLINE-2", "Default multiline style"),
]

# Drawing-resident variables that no DXF library can write: set inside AutoCAD
# by ASG-SETUP (saved with the DWG/DWT). (var, value, purpose)
SETUP_DRAWING_VARS = [
    ("CANNOSCALE", "1:1", "Current annotation scale in model space"),
    ("MSLTSCALE", 1, "Model-space linetypes follow the annotation scale"),
    ("ANNOALLVISIBLE", 0, "Show only annotation that supports the current scale (no visual duplicates)"),
    ("CMLEADERSTYLE", "ASG-ML-ANNO", "Default multileader style"),
    ("CTABLESTYLE", "ASG-TABLE-STANDARD", "Default table style"),
    ("HPLAYER", "ASG-HATCH", "New hatches go to ASG-HATCH automatically"),
    ("DIMLAYER", "ASG-DIMENSION", "New dimensions go to ASG-DIMENSION automatically"),
    ("UCSFOLLOW", 0, "View does not rotate with UCS changes"),
]

# Machine / user-profile variables - stored in the registry, NOT in any DWG/DWT.
# Applied only by the opt-in command ASG-PROFILE.  (var, value, purpose)
PROFILE_VARS = [
    ("OSMODE", 2223, "Endpoint, Midpoint, Centre, Node, Intersection, Perpendicular, Extension"),
    ("AUTOSNAP", 63, "Marker, magnet, tooltip, aperture, polar + object snap tracking"),
    ("POLARANG", 45.0, "Polar tracking increment 45 deg"),
    ("ORTHOMODE", 0, "Ortho off - polar tracking preferred"),
    ("DYNMODE", 3, "Dynamic input: pointer + dimension input"),
    ("DYNPROMPT", 1, "Prompts near cursor"),
    ("SELECTIONCYCLING", 2, "Cycle overlapping objects with list"),
    ("GRIPS", 1, "Grips on"),
    ("GRIPSIZE", 5, "Grip size"),
    ("PICKBOX", 4, "Selection target size"),
    ("APERTURE", 8, "Object snap target size"),
    ("PICKFIRST", 1, "Noun-verb selection"),
    ("PICKADD", 2, "Shift removes from selection"),
    ("ANNOAUTOSCALE", 0, "Do NOT auto-add scales to annotative objects"),
    ("SAVETIME", 10, "Autosave every 10 min"),
    ("ISAVEBAK", 1, "Keep .bak on save"),
    ("LAYOUTREGENCTL", 2, "Fast layout switching"),
    ("REFPATHTYPE", 1, "Relative xref paths"),
]

# ---------------------------------------------------------------------------
# 04 Linetypes (acadiso.lin values, mm)
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
# 04 Lineweight matrix - ISO 128 series (ratio ~1.4) + 0.09 for hatching only
# ---------------------------------------------------------------------------
LW_MATRIX = [
    (0.50, "Extra heavy", "Section cut outlines, sheet border"),
    (0.35, "Heavy", "Primary visible outlines, cutting planes"),
    (0.25, "Medium", "Aluminium, steel, cladding, symbols, revisions, title block"),
    (0.18, "Light", "Secondary lines, glass, hardware, fixings, hidden lines, text, tables"),
    (0.13, "Fine", "Dimensions, leaders, centrelines, grids, seals, insulation, set-out, reference"),
    (0.09, "Hatch", "Hatch patterns and fills only (also plotted grey)"),
]
ISO_128_SERIES = (0.13, 0.18, 0.25, 0.35, 0.50, 0.70, 1.00)

# ---------------------------------------------------------------------------
# 04 Layer dictionary
# code, name, group, ACI, linetype, lw mm, plot, description, recommended use
# Palette: 7 primary | 8 secondary | 4 glass | 3 annotation | 1 revision |
#          6 non-plot | 251-253 plotted grey (via CTB)
# ---------------------------------------------------------------------------
LAYERS = [
    ("G01", "ASG-OUTLINE-PRIMARY", "Geometry", 7, "Continuous", 0.35, True,
     "Primary visible outlines", "Overall frame / panel / opening outlines in elevation and plan"),
    ("G02", "ASG-OUTLINE-SECONDARY", "Geometry", 8, "Continuous", 0.18, True,
     "Secondary visible lines", "Edges beyond, minor returns, internal lines"),
    ("G03", "ASG-ALUMINIUM-PROFILE", "Geometry", 7, "Continuous", 0.25, True,
     "Aluminium profiles", "Frames, mullions, transoms, sashes, beads (elevation and section)"),
    ("G04", "ASG-GLASS", "Geometry", 4, "Continuous", 0.18, True,
     "Glass and mirror", "Glass / mirror edges, DGU and laminate ply lines"),
    ("G05", "ASG-STAINLESS-STEEL", "Geometry", 7, "Continuous", 0.25, True,
     "Stainless steel", "SS fittings, spigots, channels, handrails, patch plates"),
    ("G06", "ASG-MILD-STEEL", "Geometry", 7, "Continuous", 0.25, True,
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
     "Cutting planes", "Section cut lines (section markers go on ASG-SYMBOL)"),
    ("T04", "ASG-SECTION-CUT", "Technical", 7, "Continuous", 0.50, True,
     "Section cut outlines", "Outline of material cut by the section plane - heaviest geometry"),
    ("T05", "ASG-HATCH", "Technical", 252, "Continuous", 0.09, True,
     "Section hatching", "Pattern hatches in sections (plots grey)"),
    ("T06", "ASG-HATCH-FILL", "Technical", 251, "Continuous", 0.09, True,
     "Solid fills", "Solid fill of thin aluminium / steel walls (plots dark grey)"),
    ("T07", "ASG-SETOUT", "Technical", 8, "DASHDOT2", 0.13, True,
     "Setting-out geometry (plotted)", "Opening lines, setting-out lines that must print"),
    ("T08", "ASG-REFERENCE", "Technical", 253, "Continuous", 0.13, True,
     "Reference geometry", "Architectural / structural background, xrefs (plots light grey)"),
    ("T09", "ASG-CONSTRUCTION", "Technical", 6, "Continuous", 0.00, False,
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
    ("A06", "ASG-LEVEL", "Annotation", 3, "Continuous", 0.13, True,
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
     "Non-plot objects", "Internal markups and reminders - never printed"),
]

COLOUR_LOGIC = [
    ("7", "Primary geometry, metals, text, sheet", "Black"),
    ("8", "Secondary geometry, hardware, seals, hidden, centrelines, grids", "Black (lighter weights)"),
    ("4", "Glass and mirror", "Black"),
    ("3", "Annotation: dimensions, leaders, levels, symbols", "Black"),
    ("1", "Revisions", "Black"),
    ("6", "Non-plot: construction, viewport, no-plot", "Not plotted (layer plot flag off)"),
    ("251", "Solid fills (aluminium / steel walls in section)", "Grey RGB 91 (about 64 % dark)"),
    ("252", "Hatch patterns, insulation", "Grey RGB 132 (about 48 % dark)"),
    ("253", "Reference background / xrefs", "Grey RGB 173 (about 32 % dark)"),
]

# ---------------------------------------------------------------------------
# 05 Text styles: name, ttf, bold, annotative, use  (ISO 3098 height series)
# ---------------------------------------------------------------------------
TEXT_STYLES = [
    ("ASG-TEXT-ANNO", "arial.ttf", False, True, "Model-space general text and dimension text"),
    ("ASG-TEXT-NOTE", "arial.ttf", False, True, "Model-space notes, material labels, leaders"),
    ("ASG-TEXT-SMALL", "arial.ttf", False, True, "Small detail notes, profile codes"),
    ("ASG-TEXT-TITLE", "arialbd.ttf", True, False, "Detail / view titles (paper space)"),
    ("ASG-TEXT-HEADING", "arialbd.ttf", True, False, "Drawing titles, sheet headings (paper space)"),
    ("ASG-TEXT-SHEET", "arial.ttf", False, False, "Title block fields, tables, sheet text (paper space)"),
]
TEXT_HEIGHTS = [  # use, plotted mm, style
    ("General dimensions", 2.5, "ASG-TEXT-ANNO (via dimension style)"),
    ("Technical notes", 2.5, "ASG-TEXT-NOTE"),
    ("Material labels", 2.5, "ASG-TEXT-NOTE (via ASG-ML-ANNO)"),
    ("Small detail notes", 1.8, "ASG-TEXT-SMALL"),
    ("Detail titles", 3.5, "ASG-TEXT-TITLE"),
    ("Drawing titles", 5.0, "ASG-TEXT-HEADING"),
    ("Sheet headings", 7.0, "ASG-TEXT-HEADING (A1); 5.0 on A3 / A4"),
]
ISO_3098_HEIGHTS = (1.8, 2.5, 3.5, 5.0, 7.0, 10.0, 14.0, 20.0)

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
    ("ASG-DIM-FIXED", False, {},
     "Non-annotative: dimensions placed in paper space over viewports (true size), or 1:1 sheets"),
    ("ASG-DIM-DETAIL", True, {"dimdec": 1, "dimzin": 0},
     "Fabrication details 0.0; symmetrical tolerance switched on per dimension (height 0.7)"),
    ("ASG-DIM-ANGULAR", True, {"dimazin": 0}, "Angular dimensions, decimal degrees 0.00"),
    ("ASG-DIM-RADIUS", True, {"dimcen": 0.0, "dimtmove": 0}, "Radius dimensions (R prefix automatic), no centre mark"),
    ("ASG-DIM-DIAMETER", True, {"dimcen": 2.5, "dimtmove": 0}, "Diameter dimensions (diameter sign automatic), centre mark 2.5"),
]
DIM_HEADER_EXCLUDE = {"dimblk"}  # $DIMBLK "" already = closed filled

# ---------------------------------------------------------------------------
# 05 Multileader styles
# name, annotative, arrow block ("" = closed filled), arrow size, text style,
# text height, text frame, use
# ---------------------------------------------------------------------------
MLEADER_STYLES = [
    ("ASG-ML-ANNO", True, "", 2.5, "ASG-TEXT-NOTE", 2.5, False, "Default model-space callouts and material labels"),
    ("ASG-ML-NOTE", False, "", 2.5, "ASG-TEXT-SHEET", 2.5, False, "Paper-space notes pointing into viewports"),
    ("ASG-ML-DETAIL", True, "_DOT", 1.5, "ASG-TEXT-SMALL", 1.8, False, "Dense 1:1 / 1:2 fabrication details"),
    ("ASG-ML-REFERENCE", True, "_OPEN30", 2.5, "ASG-TEXT-NOTE", 2.5, True, "References to other drawings / details (framed text)"),
]

ANNO_SCALES = [1, 2, 5, 10, 20, 25, 50, 100]

# ---------------------------------------------------------------------------
# 07 Table styles (created in AutoCAD by ASG-SETUP)
# name, title (h, align), header (h, align), data (h, align), title suppressed,
# header suppressed, use.   align: TL top-left, ML middle-left, MC middle-centre
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
TABLE_ALIGN_CODE = {"TL": 1, "ML": 4, "MC": 5}  # AcCellAlignment

# ---------------------------------------------------------------------------
# 08 Sheets (ISO 216 sizes)
# layout name, width, height, DWG To PDF media base name, title block, default vp scale
# ---------------------------------------------------------------------------
SHEETS = [
    ("A4-LANDSCAPE", 297.0, 210.0, "ISO_full_bleed_A4", "ASG-TB-A4-L", 10),
    ("A4-PORTRAIT", 210.0, 297.0, "ISO_full_bleed_A4", "ASG-TB-A4-P", 10),
    ("A3-LANDSCAPE", 420.0, 297.0, "ISO_full_bleed_A3", "ASG-TB-A3-L", 20),
    ("A3-PORTRAIT", 297.0, 420.0, "ISO_full_bleed_A3", "ASG-TB-A3-P", 20),
    ("A1-LANDSCAPE", 841.0, 594.0, "ISO_full_bleed_A1", "ASG-TB-A1-L", 50),
]
ISO_216 = {(210.0, 297.0), (297.0, 420.0), (594.0, 841.0)}
MARGIN_LEFT, MARGIN = 20.0, 10.0  # ISO 5457 practice: 20 mm filing margin, 10 mm others


def media_name(base: str, w: float, h: float) -> str:
    return f"{base}_({w:.2f}_x_{h:.2f}_MM)"


# Title blocks - designed per sheet, never stretched.
#   strip  = full-height title strip on the right of landscape sheets
#   bottom = full-width title block at the foot of portrait sheets
# r: info row height, rr: revision row height, cap: caption text, val: value
# text, title / num: drawing title / number text, comp: company name, note: notes
TB_SPECS = {
    "ASG-TB-A4-L": dict(kind="strip", w=70.0, h=190.0, r=6.8, rr=4.5, cap=1.8, val=2.5, title=3.5,
                        num=3.5, comp=2.5, note=1.8, stamp_min=24.0),
    "ASG-TB-A3-L": dict(kind="strip", w=98.0, h=277.0, r=8.5, rr=5.5, cap=1.8, val=2.5, title=5.0,
                        num=5.0, comp=3.5, note=1.8, stamp_min=40.0),
    "ASG-TB-A1-L": dict(kind="strip", w=160.0, h=574.0, r=13.0, rr=8.0, cap=2.5, val=3.5, title=7.0,
                        num=7.0, comp=5.0, note=2.5, stamp_min=80.0),
    "ASG-TB-A4-P": dict(kind="bottom", w=180.0, r=7.0, rr=4.4, cap=1.8, val=2.5, title=3.5,
                        num=3.5, comp=2.5, note=1.8, stamp_min=20.0),
    "ASG-TB-A3-P": dict(kind="bottom", w=267.0, r=8.5, rr=5.2, cap=1.8, val=2.5, title=5.0,
                        num=5.0, comp=3.5, note=1.8, stamp_min=26.0),
}
REV_ROWS = 5
TB_ATTRIBUTES = [  # tag, prompt, default, design sample (longest value the field must hold)
    ("PROJECT", "Project", "PROJECT NAME", "MARINA TOWER - PODIUM FACADE"),
    ("LOCATION", "Location", "LOCATION, UAE", "DUBAI MARINA, DUBAI, UAE"),
    ("CLIENT", "Client", "CLIENT", "ABC REAL ESTATE DEVELOPMENT"),
    ("CONSULTANT", "Consultant", "CONSULTANT", "XYZ ENGINEERING CONSULTANTS"),
    ("DWG_TITLE", "Drawing title", "DRAWING TITLE", "CURTAIN WALL ELEVATION"),
    ("DWG_TITLE_2", "Drawing title - second line (optional)", "", "GRID A-D, LEVEL 01 TO 05"),
    ("DWG_NO", "Drawing number", "AS-YYYY-NNN-DIS-TYP-001", "AS-2026-014-ALU-SD-001"),
    ("REV", "Current revision", "R0", "R12"),
    ("SHEET_NO", "Sheet number", "01 OF 01", "12 OF 12"),
    ("SCALE", "Scale", "AS SHOWN", "1:20, 1:5"),
    ("DATE", "Date (DD.MM.YYYY)", "DD.MM.YYYY", "28.10.2026"),
    ("DWG_STATUS", "Drawing status", "PRELIMINARY", "FOR CONSTRUCTION"),
    ("DRAWN_BY", "Drawn by", "-", "A. A. QAMAR"),
    ("CHECKED_BY", "Checked by", "-", "A. A. QAMAR"),
    ("APPROVED_BY", "Approved by", "-", "A. A. QAMAR"),
] + [
    att for n in range(1, REV_ROWS + 1) for att in (
        (f"REV{n}_NO", f"Revision row {n} - revision", "R0" if n == 1 else "", "R12"),
        (f"REV{n}_DATE", f"Revision row {n} - date", "DD.MM.YYYY" if n == 1 else "", "28.10.2026"),
        (f"REV{n}_DESC", f"Revision row {n} - description", "FIRST ISSUE" if n == 1 else "",
         "ISSUED FOR APPROVAL"),
        (f"REV{n}_BY", f"Revision row {n} - by", "-" if n == 1 else "", "AAQ"),
    )
]
TB_NOTES = [
    "ALL DIMENSIONS ARE IN MILLIMETRES UNLESS NOTED OTHERWISE.",
    "DO NOT SCALE THIS DRAWING - USE FIGURED DIMENSIONS ONLY.",
    "VERIFY ALL DIMENSIONS ON SITE BEFORE FABRICATION.",
    "READ WITH ARCHITECTURAL, STRUCTURAL DRAWINGS AND SPECIFICATIONS.",
]
TB_COPYRIGHT = ("\u00a9 SAEED AL SIRAJ GLASS & ALUMINIUM WORKS L.L.C. - CONFIDENTIAL. "
                "NOT TO BE COPIED OR USED WITHOUT WRITTEN PERMISSION.")
DRAWING_STATUS_CODES = ["PRELIMINARY", "FOR APPROVAL", "APPROVED", "FOR CONSTRUCTION",
                        "FOR FABRICATION", "AS-BUILT", "SUPERSEDED"]
NUMBERING = [
    ("Format", "AS-[YYYY]-[NNN]-[DIS]-[TYP]-[SSS]  +  revision R0, R1, R2 ... in the REV field"),
    ("Example", "AS-2026-014-ALU-SD-001, REV R0  ->  file AS-2026-014-ALU-SD-001-R0_MarinaTower.dwg"),
    ("YYYY-NNN", "Al Siraj project code (year + project serial)"),
    ("DIS", "ALU aluminium | GLZ glazing | MS mild steel | SS stainless steel | MISC other metal works"),
    ("TYP", "GA general arrangement | EL elevation | SD shop drawing | SEC section | DT detail"),
    ("SSS", "Sheet serial 001, 002 ..."),
]

# ---------------------------------------------------------------------------
# Hatch standard - pattern names verified against acadiso.pat definitions
# material, pattern, AutoCAD angle property, scale rule, layer, note
# Module values (acadiso, scale 1): ANSI31/37 spacing 3.175 mm, ANSI32 pair
# spacing 9.525 mm, INSUL band 9.525 mm, AR-* real-size (mm).
# ---------------------------------------------------------------------------
HATCH_STANDARD = [
    ("Glass (section)", "ANSI31", "0", "0.5 x drawing scale (1.6 mm on paper)", "ASG-HATCH",
     "Thin monolithic glass may be left unhatched"),
    ("Aluminium (section)", "SOLID", "-", "-", "ASG-HATCH-FILL", "Plots dark grey"),
    ("Mild steel (section)", "ANSI32", "0", "1.0 x drawing scale", "ASG-HATCH", "Lines read 45 deg"),
    ("Stainless steel (section)", "ANSI31", "90", "0.75 x drawing scale", "ASG-HATCH", "Lines read 135 deg"),
    ("Thermal break / polyamide", "ANSI37", "0", "0.5 x drawing scale", "ASG-INSULATION", "Cross-hatch"),
    ("Insulation board / batt", "INSUL", "0", "insulation thickness / 9.525 (real size)", "ASG-INSULATION",
     "Pattern band fits the thickness"),
    ("Concrete", "AR-CONC", "0", "real size: 1.0 up to 1:10, 2.0 at 1:20-1:25, 5.0 at 1:50-1:100", "ASG-REFERENCE", ""),
    ("Masonry / blockwork (section)", "ANSI31", "0", "1.0 x drawing scale", "ASG-REFERENCE", "Plots light grey"),
    ("Blockwork (elevation)", "AR-B816", "0", "real size 0.984 (= 200 x 400 block)", "ASG-REFERENCE", ""),
    ("Sealant bead", "SOLID", "-", "-", "ASG-SEALANT", "Plots black"),
    ("Generic / unspecified section", "ANSI31", "0", "1.0 x drawing scale", "ASG-HATCH", "Use only until material is confirmed"),
]

ATTRIBUTE_STANDARD = [
    ("ITEM_CODE", "Item / product code"), ("ITEM_NAME", "Item description"),
    ("SYSTEM_NAME", "System / series"), ("MANUFACTURER", "Manufacturer / supplier (verified data only)"),
    ("MATERIAL", "Base material"), ("FINISH", "Finish"), ("COLOUR", "Colour / RAL"),
    ("GLASS_SPEC", "Glass specification"), ("REVISION", "Block revision"),
]

BYLAYER_RAW = colors.BY_LAYER_RAW_VALUE


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


def header_value(var):
    return next(v for k, v, _p in HEADER_VARS if k == var)


def dim_values(name):
    over = next(o for n, _a, o, _u in DIM_STYLES if n == name)
    return dict(DIM_BASE, **over)


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
    # "Standard" cannot be removed from a drawing - make it harmless if picked
    doc.dimstyles.get("Standard").dxf.update(dim_values("ASG-DIM-FIXED"))
    _mleader_styles(doc)
    _mline_styles(doc)
    for name, spec in TB_SPECS.items():
        if any(s[4] == name for s in sheets):
            _title_block(doc, name, **spec)
    _layouts(doc, sheets)
    # page_setup() resets limits -> re-apply all header values last
    for var, val, _p in HEADER_VARS + HEADER_STYLE_VARS:
        doc.header[var] = val
    _sync_header_dimvars(doc, "ASG-DIM-ANNO")
    msp_layout = doc.layouts.get("Model")
    msp_layout.dxf.limmin = header_value("$LIMMIN")  # $LIM* are synced from the Model layout on save
    msp_layout.dxf.limmax = header_value("$LIMMAX")
    doc.set_modelspace_vport(height=20000, center=(10000, 7000))
    return doc


def _sync_header_dimvars(doc, style):
    """Current dimension variables in the header must equal the current style,
    otherwise AutoCAD shows the style with '<style overrides>'."""
    for k, v in dim_values(style).items():
        if k in DIM_HEADER_EXCLUDE:
            continue
        doc.header["$" + k.upper()] = v


def _mleader_styles(doc):
    def setup(ml, anno, arrow, asz, tstyle, ch, frame):
        d = ml.dxf
        d.content_type = 2  # MText
        d.leader_type = 1  # straight
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
        d.text_left_attachment_type = 1  # middle of top line
        d.text_right_attachment_type = 1
        d.text_angle_type = 1  # horizontal
        d.scale = 1.0
        d.is_annotative = int(anno)

    for name, anno, arrow, asz, tstyle, ch, frame, _u in MLEADER_STYLES:
        setup(doc.mleader_styles.new(name), anno, arrow, asz, tstyle, ch, frame)
    setup(doc.mleader_styles.get("Standard"), False, "", 2.5, "ASG-TEXT-SHEET", 2.5, False)


def _mline_styles(doc):
    m = doc.mline_styles.new("ASG-MLINE-2")
    m.dxf.description = "Two lines +/-0.5; MLINE scale = overall width"
    m.elements.append(0.5, 256, "BYLAYER")
    m.elements.append(-0.5, 256, "BYLAYER")
    m.dxf.flags = 16 | 256  # square start / end caps
    m = doc.mline_styles.new("ASG-MLINE-3")
    m.dxf.description = "Two lines + CENTER2 axis"
    m.elements.append(0.5, 256, "BYLAYER")
    m.elements.append(0.0, 256, "CENTER2")
    m.elements.append(-0.5, 256, "BYLAYER")
    m.dxf.flags = 16 | 256


# ---------------------------------------------------------------------------
# Text measurement (Liberation Sans = Arial metrics). AutoCAD TrueType text
# height is the capital height (Arial cap height = 0.716 em).
# ---------------------------------------------------------------------------
_FONT_FILES = {False: "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
               True: "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"}
_BOLD_STYLES = {n for n, _f, bold, *_r in TEXT_STYLES if bold}
_FONT_CACHE = {}


def text_width(s, h, style):
    from PIL import ImageFont
    bold = style in _BOLD_STYLES
    if bold not in _FONT_CACHE:
        _FONT_CACHE[bold] = ImageFont.truetype(_FONT_FILES[bold], 1000)
    return _FONT_CACHE[bold].getlength(s) / 1000.0 * h / 0.716


def wrap(text, h, style, width, indent=""):
    """Greedy word wrap by measured width; continuation lines get `indent`."""
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip() if cur else w_
        if text_width((indent if lines else "") + trial, h, style) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w_
    lines.append(cur)
    return [lines[0]] + [indent + ln for ln in lines[1:]]


TB_HEIGHTS: dict[str, float] = {}
TB_FIT: dict[str, list] = {}  # name -> [(label, text, height, style, available width)]
_ATT = {t: (p, d, smp) for t, p, d, smp in TB_ATTRIBUTES}
FIT_SPARE = 1.0  # mm kept free at the end of every title-block text line


class _TB:
    """Title-block drawing helper: geometry on layer 0 / ByLayer (takes the
    ASG-TITLEBLOCK layer when inserted); attributes added in TB_ATTRIBUTES order."""

    def __init__(self, doc, name, spec):
        self.blk = doc.blocks.new(name)
        br = self.blk.block_record
        br.dxf.units = 4      # millimetres
        br.dxf.explode = 0    # not explodable - keeps attributes intact
        br.dxf.scale = 1      # uniform scaling only
        self.name, self.s = name, spec
        self.pad = max(0.8, 0.12 * spec["r"])
        self.atts = {}
        TB_FIT[name] = []

    def line(self, p1, p2):
        self.blk.add_line(p1, p2, dxfattribs={"layer": "0"})

    def rect(self, x, y, w, h):
        self.blk.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], close=True,
                                dxfattribs={"layer": "0"})

    def text(self, s, x, y, h, style, avail, label=None, align=TextEntityAlignment.BOTTOM_LEFT):
        if s:
            _text(self.blk, s, x, y, h, style)
            TB_FIT[self.name].append((label or s[:24], s, h, style, avail))

    def att(self, tag, x, y, h, style, avail):
        self.atts[tag] = (x, y, h, style)
        TB_FIT[self.name].append((tag, _ATT[tag][2], h, style, avail))

    def cell(self, x, y, w, h, caption, tag, vh, vstyle="ASG-TEXT-SHEET"):
        """Caption top-left, value bottom-left."""
        s, p = self.s, self.pad
        assert s["cap"] + vh + 3 * p <= h + 1e-9, f"{self.name}: cell {caption} too low"
        self.text(caption, x + p, y + h - p - s["cap"], s["cap"], "ASG-TEXT-SHEET", w - 2 * p)
        self.att(tag, x + p, y + p, vh, vstyle, w - 2 * p)

    def row(self, x, y, w, h, cells):
        """cells: [(fraction, caption, tag, value height, value style)]"""
        cx = x
        for i, (frac, caption, tag, vh, vstyle) in enumerate(cells):
            cw = w * frac
            if i:
                self.line((cx, y), (cx, y + h))
            self.cell(cx, y, cw, h, caption, tag, vh, vstyle)
            cx += cw
        return h

    # ------------------------------------------------------------ sections
    def company_lines(self, w):
        s = self.s
        if text_width(COMPANY, s["comp"], "ASG-TEXT-HEADING") <= w - 2 * self.pad - FIT_SPARE:
            names = [COMPANY]
        else:
            names = ["SAEED AL SIRAJ GLASS &", "ALUMINIUM WORKS L.L.C."]
        sub = wrap(f"{GROUP} - ALUMINIUM, GLASS & FACADE DIVISION - UAE", s["cap"], "ASG-TEXT-SHEET",
                   w - 2 * self.pad - FIT_SPARE)
        return names, sub

    def company_height(self, w):
        s = self.s
        names, sub = self.company_lines(w)
        return 2.6 * self.pad + len(names) * s["comp"] * 1.45 + 0.6 * s["comp"] + len(sub) * s["cap"] * 1.55

    def company(self, x, y, w, h):
        s, p = self.s, self.pad
        names, sub = self.company_lines(w)
        ty = y + h - 1.6 * p - s["comp"]
        for n in names:
            self.text(n, x + p, ty, s["comp"], "ASG-TEXT-HEADING", w - 2 * p)
            ty -= s["comp"] * 1.45
        ty -= 0.6 * s["comp"] - s["comp"] * 1.45 + s["cap"] * 1.55
        for ln in sub:
            self.text(ln, x + p, ty, s["cap"], "ASG-TEXT-SHEET", w - 2 * p)
            ty -= s["cap"] * 1.55

    def stamp(self, x, y, w, h, key_plan=False):
        """Approval stamp box; tall strips also get a KEY PLAN box above it."""
        s, p = self.s, self.pad
        assert h >= s["stamp_min"] - 1e-9, f"{self.name}: stamp box {h:.1f} < {s['stamp_min']}"
        if key_plan and h >= 2 * s["stamp_min"]:
            hs = max(s["stamp_min"], 0.5 * h)
            self.line((x, y + hs), (x + w, y + hs))
            self.text("KEY PLAN", x + p, y + h - p - s["cap"], s["cap"], "ASG-TEXT-SHEET", w - 2 * p)
            h = hs
        self.text("APPROVAL STAMP", x + p, y + h - p - s["cap"], s["cap"], "ASG-TEXT-SHEET", w - 2 * p)

    def note_lines(self, w):
        s = self.s
        out = []
        for i, n in enumerate(TB_NOTES, 1):
            out += wrap(f"{i}. {n}", s["note"], "ASG-TEXT-SHEET", w - 2 * self.pad - FIT_SPARE, indent="    ")
        cr = wrap(TB_COPYRIGHT, s["note"], "ASG-TEXT-SHEET", w - 2 * self.pad - FIT_SPARE)
        return out, cr

    def notes_height(self, w):
        s = self.s
        out, cr = self.note_lines(w)
        return 2 * self.pad + s["cap"] * 1.9 + (len(out) + len(cr)) * s["note"] * 1.55 + s["note"] * 0.8

    def notes(self, x, y, w, h):
        s, p = self.s, self.pad
        out, cr = self.note_lines(w)
        self.text("GENERAL NOTES", x + p, y + h - p - s["cap"], s["cap"], "ASG-TEXT-SHEET", w - 2 * p)
        ty = y + h - p - s["cap"] * 1.9 - s["note"]
        for ln in out:
            self.text(ln, x + p, ty, s["note"], "ASG-TEXT-SHEET", w - 2 * p, label="note")
            ty -= s["note"] * 1.55
        ty -= s["note"] * 0.8
        for ln in cr:
            self.text(ln, x + p, ty, s["note"], "ASG-TEXT-SHEET", w - 2 * p, label="copyright")
            ty -= s["note"] * 1.55

    REV_COLS = [(0.13, "REV", "NO"), (0.25, "DATE", "DATE"), (0.46, "DESCRIPTION", "DESC"), (0.16, "BY", "BY")]

    def revisions_height(self):
        return (REV_ROWS + 1) * self.s["rr"]

    def revisions(self, x, y, w, h=None):
        """Header row on top, rows 1..REV_ROWS below it (row 1 = first issue).
        `h` stretches the rows to fill a band exactly."""
        s, p = self.s, self.pad
        rr = (h or self.revisions_height()) / (REV_ROWS + 1)
        top = y + rr * (REV_ROWS + 1)
        th = min(s["cap"], rr - 2 * p * 0.8)
        cx = x
        for i, (frac, caption, _k) in enumerate(self.REV_COLS):
            cw = w * frac
            if i:
                self.line((cx, y), (cx, top))
            self.text(caption, cx + p, top - rr + (rr - th) / 2, th, "ASG-TEXT-SHEET", cw - 2 * p)
            for n in range(1, REV_ROWS + 1):
                ry = top - (n + 1) * rr
                self.att(f"REV{n}_{_k}", cx + p, ry + (rr - th) / 2, th, "ASG-TEXT-SHEET", cw - 2 * p)
            cx += cw
        for n in range(1, REV_ROWS + 1):
            self.line((x, top - n * rr), (x + w, top - n * rr))

    def title(self, x, y, w, h):
        s, p = self.s, self.pad
        assert s["cap"] + s["title"] + s["val"] + 5 * p <= h + 1e-9, f"{self.name}: title row too low"
        self.text("DRAWING TITLE", x + p, y + h - p - s["cap"], s["cap"], "ASG-TEXT-SHEET", w - 2 * p)
        self.att("DWG_TITLE", x + p, y + p + s["val"] + 1.5 * p, s["title"], "ASG-TEXT-HEADING", w - 2 * p)
        self.att("DWG_TITLE_2", x + p, y + p, s["val"], "ASG-TEXT-TITLE", w - 2 * p)

    def finish(self, width, height):
        self.rect(-width, 0, width, height)
        for tag, _p, _d, _smp in TB_ATTRIBUTES:  # prompt order = this order
            x, y, h, style = self.atts[tag]
            a = self.blk.add_attdef(tag, insert=(x, y), text=_ATT[tag][1],
                                    dxfattribs={"height": h, "style": style, "layer": "0",
                                                "prompt": _ATT[tag][0], "lock_position": 1})
            a.set_placement((x, y), align=TextEntityAlignment.BOTTOM_LEFT)
        TB_HEIGHTS[self.name] = height


def _title_block(doc, name, **spec):
    """Base point = bottom-right corner of the border."""
    tb = _TB(doc, name, spec)
    s, W, r = spec, spec["w"], spec["r"]
    x0 = -W
    num_row = 1.6 * r
    if s["kind"] == "strip":
        H = s["h"]
        y = 0.0
        y += tb.row(x0, y, W, num_row, [(1.0, "DRAWING No.", "DWG_NO", s["num"], "ASG-TEXT-HEADING")])
        tb.line((x0, y), (0, y))
        # bottom-up: REV|SHEET, SCALE|DATE, STATUS, APPROVED, DRAWN|CHECKED
        for cells in ([(0.35, "REV", "REV", s["val"], "ASG-TEXT-HEADING"), (0.65, "SHEET No.", "SHEET_NO", s["val"], "ASG-TEXT-SHEET")],
                      [(0.5, "SCALE", "SCALE", s["val"], "ASG-TEXT-SHEET"), (0.5, "DATE", "DATE", s["val"], "ASG-TEXT-SHEET")],
                      [(1.0, "DRAWING STATUS", "DWG_STATUS", s["val"], "ASG-TEXT-SHEET")],
                      [(1.0, "APPROVED BY", "APPROVED_BY", s["val"], "ASG-TEXT-SHEET")],
                      [(0.5, "DRAWN BY", "DRAWN_BY", s["val"], "ASG-TEXT-SHEET"), (0.5, "CHECKED BY", "CHECKED_BY", s["val"], "ASG-TEXT-SHEET")]):
            y += tb.row(x0, y, W, r, cells)
            tb.line((x0, y), (0, y))
        th = s["cap"] + s["title"] + s["val"] + 6 * tb.pad
        tb.title(x0, y, W, th)
        y += th
        tb.line((x0, y), (0, y))
        for cap_, tag in (("CONSULTANT", "CONSULTANT"), ("CLIENT", "CLIENT"), ("LOCATION", "LOCATION"),
                          ("PROJECT", "PROJECT")):
            y += tb.row(x0, y, W, r, [(1.0, cap_, tag, s["val"], "ASG-TEXT-SHEET")])
            tb.line((x0, y), (0, y))
        tb.revisions(x0, y, W)
        y += tb.revisions_height()
        tb.line((x0, y), (0, y))
        nh = tb.notes_height(W)
        tb.notes(x0, y, W, nh)
        y += nh
        tb.line((x0, y), (0, y))
        ch = tb.company_height(W)
        tb.stamp(x0, y, W, H - y - ch, key_plan=True)
        tb.line((x0, H - ch), (0, H - ch))
        tb.company(x0, H - ch, W, ch)
        tb.finish(W, H)
    else:  # bottom block for portrait sheets
        y = 0.0
        y += tb.row(x0, y, W, num_row, [(0.55, "DRAWING No.", "DWG_NO", s["num"], "ASG-TEXT-HEADING"),
                                        (0.15, "REV", "REV", s["num"], "ASG-TEXT-HEADING"),
                                        (0.30, "SHEET No.", "SHEET_NO", s["val"], "ASG-TEXT-SHEET")])
        tb.line((x0, y), (0, y))
        for cells in ([(1 / 3, "SCALE", "SCALE", s["val"], "ASG-TEXT-SHEET"), (1 / 3, "DATE", "DATE", s["val"], "ASG-TEXT-SHEET"),
                       (1 / 3, "DRAWING STATUS", "DWG_STATUS", s["val"], "ASG-TEXT-SHEET")],
                      [(1 / 3, "DRAWN BY", "DRAWN_BY", s["val"], "ASG-TEXT-SHEET"), (1 / 3, "CHECKED BY", "CHECKED_BY", s["val"], "ASG-TEXT-SHEET"),
                       (1 / 3, "APPROVED BY", "APPROVED_BY", s["val"], "ASG-TEXT-SHEET")]):
            y += tb.row(x0, y, W, r, cells)
            tb.line((x0, y), (0, y))
        th = s["cap"] + s["title"] + s["val"] + 6 * tb.pad
        tb.title(x0, y, W, th)
        y += th
        tb.line((x0, y), (0, y))
        for cells in ([(0.5, "CLIENT", "CLIENT", s["val"], "ASG-TEXT-SHEET"), (0.5, "CONSULTANT", "CONSULTANT", s["val"], "ASG-TEXT-SHEET")],
                      [(0.5, "PROJECT", "PROJECT", s["val"], "ASG-TEXT-SHEET"), (0.5, "LOCATION", "LOCATION", s["val"], "ASG-TEXT-SHEET")]):
            y += tb.row(x0, y, W, r, cells)
            tb.line((x0, y), (0, y))
        wn, wr = 0.45 * W, 0.55 * W
        bh = max(tb.notes_height(wn), tb.revisions_height())
        tb.notes(x0, y, wn, bh)
        tb.revisions(x0 + wn, y, wr, bh)
        tb.line((x0 + wn, y), (x0 + wn, y + bh))
        y += bh
        tb.line((x0, y), (0, y))
        wc = 0.55 * W
        ch = max(tb.company_height(wc), s["stamp_min"])
        tb.company(x0, y, wc, ch)
        tb.line((x0 + wc, y), (x0 + wc, y + ch))
        tb.stamp(x0 + wc, y, W - wc, ch)
        y += ch
        tb.finish(W, y)


def title_block_height(name):
    if name not in TB_HEIGHTS:
        tmp = ezdxf.new("R2018", setup=False, units=4)
        for st, ttf, *_ in TEXT_STYLES:
            tmp.styles.add(st, font=ttf)
        _title_block(tmp, name, **TB_SPECS[name])
    return TB_HEIGHTS[name]


def viewport_rect(name, w, h, tb):
    """Default viewport: inside the border with 5 mm clearance, never over the
    title block (left of a strip, above a bottom block)."""
    spec = TB_SPECS[tb]
    x1, y1, x2, y2 = MARGIN_LEFT + 5, MARGIN + 5, w - MARGIN - 5, h - MARGIN - 5
    if spec["kind"] == "strip":
        x2 = w - MARGIN - spec["w"] - 5
    else:
        y1 = MARGIN + title_block_height(tb) + 5
    return x1, y1, x2, y2


def _layouts(doc, sheets):
    for name, w, h, paper, tb, vps in sheets:
        if name in doc.layouts:  # idempotent
            continue
        lay = doc.layouts.new(name)
        # scale MUST be a tuple: an int selects an AutoCAD standard scale index
        lay.page_setup(size=(w, h), margins=(0, 0, 0, 0), units="mm", offset=(0, 0),
                       rotation=0, scale=(1, 1), name=paper, device=PLOTTER)
        lay.dxf.current_style_sheet = CTB_NAME
        lay.use_plot_styles(True)
        lay.print_lineweights(True)
        lay.scale_lineweights(False)
        lay.plot_centered(False)  # not available for plot area "Layout"; offset 0,0 on full-bleed media
        lay.plot_viewport_borders(False)
        lay.show_plot_styles(False)
        lay.plot_hidden(False)
        lay.dxf.shade_plot_resolution_level = 3  # Presentation
        lay.add_lwpolyline([(MARGIN_LEFT, MARGIN), (w - MARGIN, MARGIN), (w - MARGIN, h - MARGIN),
                            (MARGIN_LEFT, h - MARGIN)], close=True, dxfattribs={"layer": "ASG-BORDER"})
        lay.add_blockref(tb, (w - MARGIN, MARGIN), dxfattribs={"layer": "ASG-TITLEBLOCK"}
                         ).add_auto_attribs({})
        x1, y1, x2, y2 = viewport_rect(name, w, h, tb)
        vp = lay.add_viewport(center=((x1 + x2) / 2, (y1 + y2) / 2), size=(x2 - x1, y2 - y1),
                              view_center_point=((x2 - x1) * vps / 2, (y2 - y1) * vps / 2),
                              view_height=(y2 - y1) * vps, dxfattribs={"layer": "ASG-VIEWPORT"})
        vp.dxf.flags |= 16384  # display locked
    if "Layout1" in doc.layouts and len(doc.layouts) > 2:
        doc.layouts.delete("Layout1")


# ---------------------------------------------------------------------------
# Annotation scale list - raw AcDbScale objects (ezdxf has no SCALE class)
# ---------------------------------------------------------------------------
_SCALE = ("  0\nSCALE\n  5\n{h}\n102\n{{ACAD_REACTORS\n330\n{o}\n102\n}}\n330\n{o}\n"
          "100\nAcDbScale\n 70\n0\n300\n{n}\n140\n1.0\n141\n{d}\n290\n{u}\n")


def inject_annotation_scales(path: Path):
    doc = ezdxf.readfile(path)
    sl = doc.rootdict.get("ACAD_SCALELIST")
    if len(sl):
        return  # idempotent: list already present
    owner = sl.dxf.handle
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
# CTB.  ezdxf's writer packs the 3 header fields with native C longs, which are
# 8 bytes on 64-bit Linux/macOS -> AutoCAD cannot read the file. CTB files use
# three little-endian uint32 (60-byte header, as ezdxf's own reader expects).
# ---------------------------------------------------------------------------
def _compress_ctb(stream, content: str):
    body = zlib.compress(content.encode())
    stream.write(b"PIAFILEVERSION_2.0,CTBVER1,compress\r\npmzlibcodec")
    stream.write(struct.pack("<LLL", zlib.adler32(body), len(content), len(body)))
    stream.write(body)


acadctb._compress = _compress_ctb
CTB_GREY_ACI = (250, 251, 252, 253, 254)  # plot in their own (grey) colour


def build_ctb(path: Path):
    """All colours plot black except ACI 250-254, which keep their own grey
    ('Use object color', the same encoding as AutoCAD's acad.ctb). Lineweight
    and linetype always 'Use object ...'."""
    ctb = acadctb.new_ctb()
    ctb.description = "ASG monochrome: ACI 1-249,255 black; 250-254 object grey; object lineweight & linetype"
    for aci in range(1, 256):
        st = ctb[aci]
        if aci in CTB_GREY_ACI:
            st.set_object_color()
        else:
            st.color = (0, 0, 0)
        st.set_lineweight(0.0)  # index 0 = use object lineweight
        st.linetype = acadctb.OBJECT_LINETYPE
        st.screen = 100
        st.description = ""
    path.parent.mkdir(parents=True, exist_ok=True)
    ctb.save(path)
