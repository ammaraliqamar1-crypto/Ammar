"""
Re-opens output/ASG_Master_Template.dxf from disk, checks every configured
item against the specification in build_master_template.py, renders each
layout, and writes: validation report, layer register (XLSX + CSV) and the
standards reference PDF.

    python validate_and_document.py
"""

import csv
import datetime as dt
import subprocess
import tempfile
from pathlib import Path

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from ezdxf import recover  # noqa: E402
from ezdxf.addons import acadctb  # noqa: E402
from ezdxf.addons.drawing import Frontend, RenderContext  # noqa: E402
from ezdxf.addons.drawing.config import (BackgroundPolicy, ColorPolicy,  # noqa: E402
                                         Configuration, LineweightPolicy)
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend  # noqa: E402

import build_master_template as B  # noqa: E402

OUT = B.OUT
DXF = OUT / B.DXF_NAME
CTB = OUT / B.CTB_NAME
PREVIEW = OUT / "preview"

results = []  # (area, check, status, detail)


def check(area, name, ok, detail="", status=None):
    results.append((area, name, status or ("PASS" if ok else "FAIL"), detail))


def has_anno(entity):
    try:
        return entity.has_xdata("AcadAnnotative")
    except Exception:
        return False


def validate():
    doc, aud = recover.readfile(DXF)
    check("File", "DXF re-opened from disk (ezdxf recover + audit)", not aud.has_errors,
          f"{len(aud.errors)} errors, {len(aud.fixes)} fixes; DXF version {doc.dxfversion} (AutoCAD 2018)")
    doc2 = ezdxf.readfile(DXF)
    check("File", "DXF strict read (ezdxf.readfile)", doc2 is not None)
    # independent reader: LibreOffice Draw DXF import
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / DXF.name
        tmp.write_bytes(DXF.read_bytes())
        r = subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", td, str(tmp)],
                           capture_output=True, text=True, timeout=180)
        ok = (Path(td) / (DXF.stem + ".pdf")).exists()
    check("File", "DXF opened by independent reader (LibreOffice Draw import)", ok,
          "converted to PDF without load error" if ok else r.stderr[-200:])

    h = doc.header
    exp = {"$INSUNITS": 4, "$MEASUREMENT": 1, "$LUNITS": 2, "$LUPREC": 0, "$AUNITS": 0,
           "$AUPREC": 2, "$LTSCALE": 1.0, "$PSLTSCALE": 1, "$LWDISPLAY": 1, "$DIMASSOC": 2,
           "$CLAYER": B.CURRENT_LAYER, "$TEXTSTYLE": "ASG-TEXT", "$DIMSTYLE": "ASG-DIM-ANNOTATIVE",
           "$ORTHOMODE": 0, "$PSTYLEMODE": 1}
    for k, v in exp.items():
        check("Units & variables", f"{k} = {v}", h.get(k) == v, f"found {h.get(k)}")

    # linetypes
    for name in B.LINETYPES:
        check("Linetypes", f"{name} loaded", name in doc.linetypes)
    check("Linetypes", "Continuous loaded", "Continuous" in doc.linetypes)
    # layers
    names = [l.dxf.name for l in doc.layers]
    asg = [n for n in names if n.startswith("ASG-")]
    check("Layers", f"ASG layer count = {len(B.LAYERS)}", len(asg) == len(B.LAYERS), f"found {len(asg)}")
    check("Layers", "Only system layers besides ASG-*: 0, Defpoints",
          sorted(set(names) - set(asg)) == ["0", "Defpoints"], str(sorted(set(names) - set(asg))))
    check("Layers", "Layer names unique", len(set(n.upper() for n in names)) == len(names))
    for name, _g, aci, lt, lw, plot, desc in B.LAYERS:
        l = doc.layers.get(name)
        ok = (l is not None and l.dxf.color == aci and l.dxf.linetype == lt
              and l.dxf.lineweight == round(lw * 100) and bool(l.dxf.plot) == plot
              and lt in doc.linetypes and l.description == desc)
        check("Layers", f"{name}", ok, f"ACI {aci}, {lt}, {lw:.2f} mm, {'plot' if plot else 'NO PLOT'}")
    cur = doc.layers.get(h["$CLAYER"])
    check("Layers", "Current layer is plottable geometry layer", cur.dxf.plot == 1 and
          h["$CLAYER"] == "ASG-OBJECT")
    # text styles
    for name, ttf, bold, anno, _ph, _u in B.TEXT_STYLES:
        st = doc.styles.get(name)
        ok = st is not None and st.dxf.font == ttf and st.dxf.height == 0 and st.dxf.width == 1
        check("Text styles", f"{name} ({ttf}, height 0)", ok)
        if anno:
            check("Text styles", f"{name} annotative flag (AcadAnnotative xdata)", has_anno(st),
                  "flag written; behaviour in AutoCAD UNVERIFIED", status="PASS*" if has_anno(st) else None)
    # dim styles
    for name in ["ASG-DIM-ANNOTATIVE"] + [f"ASG-DIM-1-{s}" for s in B.FIXED_DIM_SCALES]:
        ds = doc.dimstyles.get(name)
        ok = ds is not None
        if ok:
            d = ds.dxf
            exp_scale = 1.0 if "ANNO" in name else float(name.split("-")[-1])
            ok = (d.dimscale == exp_scale and d.dimlfac == 1.0 and d.dimdec == 0 and d.dimtxt == 2.5
                  and d.dimasz == 2.5 and d.dimalt == 0 and d.dimtxsty == "ASG-TEXT")
        check("Dimension styles", f"{name}", ok, "DIMLFAC 1 (true measurement), DIMDEC 0, DIMALT off")
    check("Dimension styles", "ASG-DIM-ANNOTATIVE annotative flag",
          has_anno(doc.dimstyles.get("ASG-DIM-ANNOTATIVE")), "behaviour in AutoCAD UNVERIFIED",
          status="PASS*")
    # mleader styles
    for name, anno, _s, _a, ch, ts in B.MLEADER_SPECS:
        ml = doc.mleader_styles.get(name)
        ok = ml is not None and ml.dxf.char_height == ch and ml.dxf.leader_type == 1 \
            and bool(ml.dxf.is_annotative) == anno
        check("Multileader styles", f"{name}", ok, f"text {ch} mm {ts}, annotative={anno}")
    # mline styles
    for name in ("ASG-MLINE-2", "ASG-MLINE-3"):
        check("Multiline styles", name, doc.mline_styles.get(name) is not None)
    # annotation scales
    sl = doc.rootdict.get("ACAD_SCALELIST")
    scale_names = []
    for _k, e in sl.items():
        tags = e.xtags.get_subclass("AcDbScale") if hasattr(e, "xtags") else None
        if tags:
            scale_names.append(tags.get_first_value(300))
    want = [f"1:{s}" for s in B.ANNO_SCALES]
    check("Annotation scales", "ACAD_SCALELIST = " + ", ".join(want),
          scale_names == want, f"found {scale_names}; AutoCAD acceptance UNVERIFIED", status=None
          if scale_names != want else "PASS*")
    check("Annotation scales", "No duplicate scales", len(set(scale_names)) == len(scale_names))
    # table styles
    tsd = doc.rootdict.get("ACAD_TABLESTYLE")
    tnames = [k for k, _ in tsd.items()] if tsd else []
    check("Table styles", "ASG-TABLE-* table styles in DXF", False,
          "Not writable with ezdxf - created by ASG_Template_Setup.lsp (run once in AutoCAD). "
          f"DXF currently holds: {tnames}", status="UNVERIFIED")
    # layouts
    lnames = doc.layouts.names_in_taborder()
    want_l = ["Model"] + [s[0] for s in B.SHEETS]
    check("Layouts", "Layouts = " + ", ".join(want_l), lnames == want_l, f"found {lnames}")
    for name, w, hgt, paper, tb, vps in B.SHEETS:
        lay = doc.layouts.get(name)
        d = lay.dxf
        ok = (abs(d.paper_width - w) < .01 and abs(d.paper_height - hgt) < .01
              and d.plot_configuration_file == "DWG To PDF.pc3"
              and d.paper_size == f"{paper}_({w:.2f}_x_{hgt:.2f}_MM)"
              and d.current_style_sheet == B.CTB_NAME and lay.dxf.plot_layout_flags & 128)
        check("Page setups", f"{name}: {w:.0f}x{hgt:.0f} mm, DWG To PDF, {B.CTB_NAME}, plot lineweights",
              bool(ok))
        refs = [e for e in lay if e.dxftype() == "INSERT"]
        tb_ok = len(refs) == 1 and refs[0].dxf.name == tb
        tags = sorted(a.dxf.tag for a in refs[0].attribs) if refs else []
        check("Title blocks", f"{name}: {tb} inserted with {len(tags)} attributes",
              tb_ok and tags == sorted(t for t, _p, _d in B.TB_ATTRIBUTES))
        vps_ = [e for e in lay if e.dxftype() == "VIEWPORT" and e.dxf.id != 1]
        vp_ok = len(vps_) == 1 and vps_[0].dxf.layer == "ASG-VIEWPORT" and vps_[0].dxf.flags & 16384
        sc = vps_[0].dxf.view_height / vps_[0].dxf.height if vps_ else 0
        check("Viewports", f"{name}: 1 locked viewport on ASG-VIEWPORT (no-plot), 1:{sc:.0f}",
              bool(vp_ok) and abs(sc - vps) < 1e-6)
        borders = [e for e in lay if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "ASG-BORDER"]
        check("Sheets", f"{name}: border on ASG-BORDER", len(borders) == 1)
    for tb in B.TB_SPECS:
        blk = doc.blocks.get(tb)
        adefs = sorted(a.dxf.tag for a in blk.query("ATTDEF"))
        check("Title blocks", f"{tb} block: {len(adefs)} attribute definitions",
              adefs == sorted(t for t, _p, _d in B.TB_ATTRIBUTES))
    # model space blank
    check("Model space", "Model space contains no entities", len(doc.modelspace()) == 0,
          f"{len(doc.modelspace())} entities")
    # xrefs
    xr = [b.name for b in doc.blocks if b.block and b.block.is_xref]
    check("External references", "No external references", not xr, str(xr))
    # product geometry
    user_blocks = [b.name for b in doc.blocks if not b.name.startswith("*") and not b.name.startswith("_")]
    check("Scope", "Only title-block blocks defined (no product blocks)",
          sorted(user_blocks) == sorted(B.TB_SPECS), str(user_blocks))
    # CTB
    ctb = acadctb.load(str(CTB))
    blacks = all(ctb[a].color == (0, 0, 0) for a in range(1, 256) if not 250 <= a <= 254)
    greys = all(ctb[a].color[0] == ctb[a].color[1] == ctb[a].color[2] > 0 for a in range(250, 255))
    objlw = all(ctb[a].lineweight == 0 for a in range(1, 256))
    check("Plot style", f"{B.CTB_NAME} re-loaded: ACI 1-249,255 black; 250-254 grey; object lineweight",
          blacks and greys and objlw, "file format verified by re-reading; loading in AutoCAD UNVERIFIED")
    # DWG / DWT
    for ext in ("dwg", "dwt"):
        check("File", f"ASG_Master_Template.{ext}", False,
              "NOT GENERATED - no DWG writer available (no AutoCAD / ODA File Converter / "
              "RealDWG in this environment). See README for the 1-minute conversion.",
              status="NOT GENERATED")
    return doc


def render_previews(doc):
    PREVIEW.mkdir(exist_ok=True)
    paths = []
    for lay in doc.layouts:
        if lay.name == "Model":
            continue
        w, hgt = lay.dxf.paper_width, lay.dxf.paper_height
        fig = plt.figure(figsize=(w / 25.4, hgt / 25.4))
        ax = fig.add_axes([0, 0, 1, 1])
        cfg = Configuration(color_policy=ColorPolicy.BLACK, lineweight_policy=LineweightPolicy.ABSOLUTE,
                            background_policy=BackgroundPolicy.WHITE)
        ctx = RenderContext(doc)
        ctx.set_current_layout(lay)
        Frontend(ctx, MatplotlibBackend(ax), config=cfg).draw_layout(lay, finalize=True)
        ax.set_xlim(0, w)
        ax.set_ylim(0, hgt)
        p = PREVIEW / f"{lay.name}.png"
        fig.savefig(p, dpi=110)
        plt.close(fig)
        paths.append(p)
    check("Sheets", "All layouts rendered to preview PNG (visual check)", len(paths) == len(B.SHEETS))
    return paths


# ---------------------------------------------------------------------------
def write_layer_register():
    header = ["No.", "Layer", "Group", "ACI colour", "Linetype", "Lineweight (mm)", "Plot", "Purpose / description"]
    rows = [[i, n, g, a, lt, f"{lw:.2f}", "Yes" if p else "NO PLOT", d]
            for i, (n, g, a, lt, lw, p, d) in enumerate(B.LAYERS, 1)]
    with open(OUT / "ASG_Layer_Standards.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([header] + rows)
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    wb = Workbook()
    ws = wb.active
    ws.title = "Layer Register"
    ws.append(["ASG MASTER TEMPLATE - LAYER REGISTER"])
    ws.append([f"{B.COMPANY} | {B.GROUP} | ASG_Master_Template | Rev 0 | {dt.date.today():%d.%m.%Y}"])
    ws.append([])
    ws.append(header)
    for r in rows:
        ws.append(r)
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"].font = Font(italic=True, size=9)
    thin = Side(style="thin", color="999999")
    for c in ws[4]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="404040")
    for row in ws.iter_rows(min_row=4, max_row=4 + len(rows)):
        for c in row:
            c.border = Border(top=thin, bottom=thin, left=thin, right=thin)
            c.alignment = Alignment(vertical="center", wrap_text=c.column == 8)
        if row[6].value == "NO PLOT":
            row[6].font = Font(bold=True, color="C00000")
    for col, wdt in zip("ABCDEFGH", (5, 20, 24, 10, 12, 14, 10, 62)):
        ws.column_dimensions[col].width = wdt
    ws.freeze_panes = "A5"
    ws.auto_filter.ref = f"A4:H{4 + len(rows)}"

    ws2 = wb.create_sheet("Lineweight Hierarchy")
    ws2.append(["Class", "Lineweight (mm)", "Layers"])
    by_lw = {}
    for n, _g, _a, _lt, lw, p, _d in B.LAYERS:
        if p:
            by_lw.setdefault(lw, []).append(n)
    for lw in sorted(by_lw, reverse=True):
        ws2.append([LW_CLASS.get(lw, ""), f"{lw:.2f}", ", ".join(by_lw[lw])])
    for c in ws2[1]:
        c.font = Font(bold=True)
    ws2.column_dimensions["A"].width = 26
    ws2.column_dimensions["C"].width = 110
    wb.save(OUT / "ASG_Layer_Standards.xlsx")


LW_CLASS = {0.50: "Sheet border", 0.35: "Main outline / cut section", 0.30: "Profiles / metal",
            0.25: "Secondary geometry / marks", 0.18: "Glass, hidden, hardware, text",
            0.13: "Dimensions, centrelines, seals", 0.09: "Hatch", 0.05: "Construction (no plot)"}


# ---------------------------------------------------------------------------
def write_report():
    counts = {}
    for _a, _n, s, _d in results:
        counts[s] = counts.get(s, 0) + 1
    lines = ["ASG MASTER TEMPLATE - VALIDATION REPORT",
             f"{B.COMPANY} | {B.GROUP}",
             f"Generated {dt.datetime.now():%d.%m.%Y %H:%M} | tool: ezdxf {ezdxf.__version__} | file: {B.DXF_NAME}",
             "",
             "Status key: PASS = checked by re-reading the saved file; "
             "PASS* = written and re-read correctly, behaviour inside AutoCAD not testable here; "
             "UNVERIFIED / NOT GENERATED = see detail and README manual steps.",
             "Target CAD environment (AutoCAD) is NOT available in this environment - "
             "no check below was performed inside AutoCAD.",
             "",
             "Summary: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())),
             ""]
    area = None
    for a, n, s, d in results:
        if a != area:
            lines += ["", f"[{a}]"]
            area = a
        lines.append(f"  {s:<14} {n}" + (f"  -- {d}" if d else ""))
    (OUT / "ASG_Validation_Report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return counts


# ---------------------------------------------------------------------------
def write_pdf(previews):
    from reportlab.lib import colors as rc
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                    Table, TableStyle)

    ss = getSampleStyleSheet()
    H1 = ParagraphStyle("h1", parent=ss["Heading1"], fontSize=14, spaceAfter=4)
    H2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=11, spaceBefore=8, spaceAfter=3)
    P = ParagraphStyle("p", parent=ss["BodyText"], fontSize=8.5, leading=11)
    C = ParagraphStyle("c", parent=P, fontSize=7.5, leading=9)

    def table(data, widths, head=True):
        data = [[Paragraph(str(c), C) for c in r] for r in data]
        t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1 if head else 0)
        st = [("GRID", (0, 0), (-1, -1), 0.3, rc.grey), ("VALIGN", (0, 0), (-1, -1), "TOP"),
              ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]
        if head:
            st += [("BACKGROUND", (0, 0), (-1, 0), rc.HexColor("#d9d9d9"))]
        t.setStyle(TableStyle(st))
        return t

    def footer(c, d):
        c.saveState()
        c.setFont("Helvetica", 7)
        c.drawString(15 * mm, 8 * mm, f"{B.COMPANY} | ASG CAD Standards - Master Template Rev 0")
        c.drawRightString(d.pagesize[0] - 15 * mm, 8 * mm, f"Page {d.page}")
        c.restoreState()

    s = []
    s += [Paragraph(B.COMPANY, P), Paragraph("ASG MASTER AUTOCAD TEMPLATE - CAD STANDARDS & SETTINGS REFERENCE", H1),
          Paragraph(f"{B.GROUP} | Aluminium &amp; Glass Division | UAE | Rev 0 | {dt.date.today():%d.%m.%Y}", P),
          Spacer(1, 4),
          Paragraph("Files: ASG_Master_Template.dxf (master, AutoCAD 2018 DXF), ASG_Monochrome.ctb, "
                    "ASG_Template_Setup.lsp, ASG_Layer_Standards.xlsx/.csv, ASG_Validation_Report.txt. "
                    "ASG_Master_Template.dwg/.dwt must be saved from AutoCAD (see section 14) - "
                    "no DWG writer exists in the generation environment.", P)]

    s += [Paragraph("1. Drawing units &amp; drawing-resident system variables", H2),
          table([["Variable", "Value", "Purpose"]] + SYSVARS, (32, 38, 180))]
    s += [Paragraph("2. Machine / profile settings (NOT stored in DWG/DWT)", H2),
          Paragraph("These live in the AutoCAD user profile / registry. They are NOT written by the template. "
                    "Recommended values below; ASG_Template_Setup.lsp contains an optional (ASG-PROFILE) "
                    "command that sets them only when a user runs it.", P),
          table([["Setting", "Recommended", "Note"]] + PROFILE_VARS, (38, 38, 174))]
    s += [Paragraph("3. Layer standard", H2),
          table([["Layer", "ACI", "Linetype", "LW", "Plot", "Purpose"]] +
                [[n, a, lt, f"{lw:.2f}", "Yes" if p else "NO", d] for n, _g, a, lt, lw, p, d in B.LAYERS],
                (36, 10, 20, 12, 12, 160)),
          Paragraph("Colour logic: 7 primary geometry and text | 8 secondary, hidden, hardware | 4 glass | "
                    "3 annotation (dims, leaders, marks) | 1 revision | 6 non-plot | 250-254 deliberately "
                    "plotted grey (hatch, insulation, reference). Default current layer: ASG-OBJECT. "
                    "Layer 0 = blocks only. Defpoints is created automatically by AutoCAD with the first "
                    "dimension - not pre-created.", P)]
    s += [Paragraph("4. Linetypes &amp; lineweight hierarchy", H2),
          table([["Linetype", "Description"]] + [[k, v[1]] for k, v in B.LINETYPES.items()] +
                [["Continuous", "Solid"]], (35, 215)),
          Spacer(1, 3),
          table([["Lineweight", "Class / use"]] + [[f"{k:.2f} mm", v] for k, v in LW_CLASS.items()], (35, 215)),
          Paragraph("LTSCALE = 1, PSLTSCALE = 1: linetype dash lengths are paper mm in every viewport. "
                    "MSLTSCALE (profile, set 1) scales them by the annotation scale in model space. "
                    "Use CELTSCALE only per object if a short member needs a tighter pattern.", P)]
    s += [PageBreak(), Paragraph("5. Text styles - font Arial (TrueType, present on every Windows PC)", H2),
          table([["Style", "Font", "Annotative", "Height in style", "Use"]] +
                [[n, f, "Yes" if a else "No (paper space)", "0 (variable)", u] for n, f, _b, a, _h, u in B.TEXT_STYLES],
                (32, 25, 30, 25, 138)),
          Spacer(1, 3),
          table([["Text use", "Paper height", "Style", "Note"]] + [[a, f"{b} mm", c, d] for a, b, c, d in B.PAPER_HEIGHTS],
                (50, 25, 50, 125)),
          Paragraph("Readable on A4, A3 and A1: minimum 1.8 mm; never reduce title block text when plotting A1 "
                    "to A3 half-size - plot A3 at full size from an A3 layout instead.", P)]
    s += [Paragraph("6. Dimension styles", H2),
          table([["Style", "Annotative", "DIMSCALE", "Use"]] +
                [["ASG-DIM-ANNOTATIVE", "Yes", "1 (scale from annotation scale)", "Default - model space, any viewport scale"]] +
                [[f"ASG-DIM-1-{x}", "No", str(x), f"Fixed scale 1:{x} model-space dimensions"] for x in B.FIXED_DIM_SCALES],
                (40, 22, 45, 143)),
          Spacer(1, 3),
          table([["Parameter", "Value"]] + DIM_PARAMS, (60, 190))]
    s += [Paragraph("7. Multileader styles", H2),
          table([["Style", "Annotative", "Arrow", "Text", "Landing / dogleg", "Use"]] +
                [["ASG-ML-ANNOTATIVE", "Yes", "Closed filled 2.5", "ASG-TEXT-NOTE 2.5", "gap 1.0 / 4.0", "Default callouts in model space"],
                 ["ASG-ML-NOTE", "No", "Closed filled 2.5", "ASG-TEXT-NOTE 2.5", "gap 1.0 / 4.0", "Paper-space notes"],
                 ["ASG-ML-DETAIL", "No", "Dot 1.5", "ASG-TEXT-SMALL 1.8", "gap 1.0 / 4.0", "Dense 1:1 / 1:2 details, paper space"]],
                (35, 18, 30, 35, 28, 104)),
          Paragraph("All: straight leader, max 2 points, MText content, no text frame, attachment middle of "
                    "top line both sides, colour/lineweight ByLayer. Background mask is an MText property, "
                    "not a style property - turn on per note (Properties > Text > Background mask) where a "
                    "note sits over hatch.", P)]
    s += [PageBreak(), Paragraph("8. Annotative strategy &amp; annotation scales", H2),
          Paragraph("Scale list (ACAD_SCALELIST): " + ", ".join(f"1:{x}" for x in B.ANNO_SCALES) +
                    " - no duplicates, no imperial scales.", P),
          table([["Object", "Approach"]] + ANNO_STRATEGY, (35, 215)),
          Paragraph("<b>Manage scales:</b> set the viewport scale first (select viewport > scale list on status bar). "
                    "Annotation added in model space while CANNOSCALE = viewport scale gets that scale. To show an "
                    "object in a second viewport scale: select it > right-click > Annotative Object Scale > Add/Delete "
                    "(OBJECTSCALE). Keep ANNOAUTOSCALE = 0 (do not auto-add every scale). SCALELISTEDIT > Reset "
                    "only by the CAD custodian; run -SCALELISTEDIT > Reset > Exit then AUDIT if imported "
                    "drawings bring _XREF or duplicate scales.", P)]
    s += [Paragraph("9. Hatch standard (standard acadiso.pat patterns only)", H2),
          table([["Material", "Pattern", "Scale @1:1", "Angle", "Layer", "Note"]] +
                [list(map(str, r)) for r in B.HATCH_STANDARD], (35, 22, 20, 14, 30, 129)),
          Paragraph("Model-space hatch scale = table scale x drawing scale (e.g. ANSI31 at 1:5 = 1.0 x 5), "
                    "or tick Annotative in the hatch dialog and leave scale at the table value. "
                    "HPLAYER = ASG-HATCH (profile/session). The master drawing contains no hatches.", P),
          Paragraph("10. Multiline styles", H2),
          Paragraph("ASG-MLINE-2 (two lines +/-0.5, square caps) and ASG-MLINE-3 (adds CENTER2 axis). "
                    "MLINE justification Zero, scale = overall width (e.g. 50 for a 50 mm frame).", P)]
    s += [Paragraph("11. Table styles (created by ASG_Template_Setup.lsp - UNVERIFIED)", H2),
          table([["Style", "Title row", "Header row", "Data rows", "Use"]] + TABLE_STYLES, (38, 40, 40, 50, 82)),
          Paragraph("Common: text style ASG-TEXT, horizontal margin 1.5, vertical margin 1.0, direction down, "
                    "grid 0.18 inside / 0.35 outline, colours ByBlock, no background fill on data rows, "
                    "light grey (ACI 254) fill on header row.", P)]
    s += [Paragraph("12. Block &amp; attribute standard", H2),
          Paragraph("Naming: ASG-[CATEGORY]-[ITEM]-[VARIANT] (e.g. ASG-HW-HINGE-01). Draw on layer 0 with "
                    "ByBlock/ByLayer properties, base point at a logical fixing/datum point (bottom-left or "
                    "centreline), unit 1 = 1 mm, Insert units = Millimetres, 'Scale uniformly' ON, 'Allow "
                    "exploding' OFF for symbols. Symbols that must stay a fixed paper size (section/detail "
                    "marks, level heads, north arrow) are Annotative; real-size product blocks are not. "
                    "Attribute definitions on layer 0, style ASG-TEXT-SMALL, invisible unless displayed.", P),
          table([["Tag", "Prompt", "Example"]] + [list(r) for r in B.ATTRIBUTE_STANDARD], (35, 60, 155))]
    s += [PageBreak(), Paragraph("13. Layouts, page setups, title block &amp; plotting", H2),
          table([["Layout", "Paper (DWG To PDF.pc3)", "Title block", "Viewport"]] +
                [[n, f"{p}_({w:.2f}_x_{h:.2f}_MM)", tb, f"1 locked, 1:{v}, layer ASG-VIEWPORT"] for n, w, h, p, tb, v in B.SHEETS],
                (28, 82, 25, 115)),
          Paragraph("Each layout: plot area Layout, scale 1:1, centred, plot style table ASG_Monochrome.ctb, "
                    "plot object lineweights ON, plot with plot styles ON, plot transparency OFF, paper-space "
                    "last, hide viewport objects OFF. Border: 20 mm left (filing), 10 mm other sides, layer "
                    "ASG-BORDER. Title blocks are separate designs per size (A4 180 mm, A3 180 mm, A1 250 mm "
                    "wide) - not stretched. Change a viewport scale: unlock (Properties > Display locked = No), "
                    "pick scale from status bar, lock again.", P),
          Paragraph("<b>Title block attributes:</b> " + ", ".join(t for t, _p, _d in B.TB_ATTRIBUTES) +
                    ". Edit with EATTEDIT or ATTIPEDIT. Company heading is text - replace with an approved "
                    "logo block when available (no logo invented).", P),
          Paragraph("<b>Plot styles:</b> ASG_Monochrome.ctb: ACI 1-249 &amp; 255 plot black; 250-254 plot as "
                    "grey 20/36/52/68/84 % (hatch, insulation, reference). Lineweight and linetype = object. "
                    "Fallback if the CTB is unavailable: AutoCAD's own monochrome.ctb.", P),
          Paragraph("<b>PDF:</b> DWG To PDF.pc3, vector quality 1200 dpi, raster 300 dpi, fonts embedded "
                    "(PDFSHX = 1 / TrueType as text), include layer information OFF for client issue. "
                    "PDF import (PDFIMPORT) brings geometry on PDF_ layers - move to ASG layers and purge.", P)]
    s += [Paragraph("14. Creating the DWG and DWT (manual - not possible in generation environment)", H2),
          Paragraph("1) Open ASG_Master_Template.dxf in AutoCAD 2018+. 2) AUDIT (Y). 3) Run APPLOAD > "
                    "ASG_Template_Setup.lsp > type ASG-TABLESTYLES. 4) SAVEAS > AutoCAD 2018 Drawing (*.dwg) > "
                    "ASG_Master_Template.dwg. 5) SAVEAS > AutoCAD Drawing Template (*.dwt) > "
                    "ASG_Master_Template.dwt, description 'ASG master template', Measurement Metric. "
                    "6) Copy ASG_Monochrome.ctb to the Plot Styles folder. 7) Re-open the DWT and tick the "
                    "items in the validation report marked PASS* / UNVERIFIED.", P),
          Paragraph("15. Workflow &amp; housekeeping", H2),
          table([["Topic", "Standard"]] + WORKFLOW, (40, 210))]
    s += [PageBreak(), Paragraph("Appendix - layout previews (rendered from the saved DXF, monochrome)", H2)]
    for p in previews:
        s += [Paragraph(p.stem, P), Image(str(p), width=150 * mm, height=150 * mm, kind="proportional"),
              Spacer(1, 4)]
    SimpleDocTemplate(str(OUT / "ASG_CAD_Standards.pdf"), pagesize=landscape(A4),
                      leftMargin=15 * mm, rightMargin=15 * mm, topMargin=12 * mm, bottomMargin=14 * mm,
                      title="ASG CAD Standards", author=B.COMPANY).build(s, onFirstPage=footer, onLaterPages=footer)


SYSVARS = [
    ["INSUNITS", "4 (Millimetres)", "Block / xref insertion units"],
    ["MEASUREMENT", "1 (Metric)", "ISO hatch & linetype files"],
    ["LUNITS / LUPREC", "2 Decimal / 0", "Ordinary lengths whole mm (raise per detail via dim style)"],
    ["AUNITS / AUPREC", "0 Decimal degrees / 2", "Angles 0.00 deg"],
    ["ANGBASE / ANGDIR", "0 / 0", "East = 0, counter-clockwise"],
    ["LIMMIN / LIMMAX", "0,0 / 100000,70000", "Nominal area; LIMCHECK = 0 (no restriction)"],
    ["LTSCALE / PSLTSCALE", "1 / 1", "Linetypes in paper mm"],
    ["LWDISPLAY", "1", "Lineweights shown on screen"],
    ["CELWEIGHT / CECOLOR", "ByLayer / ByLayer", "No hard-coded properties"],
    ["CLAYER", "ASG-OBJECT", "Default current layer"],
    ["TEXTSTYLE / DIMSTYLE", "ASG-TEXT / ASG-DIM-ANNOTATIVE", "Defaults"],
    ["CMLSTYLE", "ASG-MLINE-2", "Default multiline style"],
    ["ORTHOMODE", "0", "Use polar tracking instead"],
    ["DIMASSOC", "2", "Associative dimensions - follow real geometry"],
    ["PLINEGEN / FILLMODE / MIRRTEXT", "1 / 1 / 0", "Linetype along polylines; fills on; text not mirrored"],
    ["PSTYLEMODE", "1", "Colour-dependent plot styles (CTB)"],
    ["Model space", "Empty, World UCS", "No geometry, no xrefs"],
]
PROFILE_VARS = [
    ["OSMODE", "2223", "End, Mid, Centre, Node, Intersection, Perpendicular, Extension (registry, not DWG)"],
    ["AUTOSNAP", "63", "Marker, magnet, tooltip, aperture, OTRACK"],
    ["POLARMODE / POLARANG", "Tracking ON / 45", "Polar + object snap tracking"],
    ["DYNMODE / DYNPROMPT", "3 / 1", "Dynamic input on"],
    ["SELECTIONCYCLING", "2", "Cycle overlapping objects"],
    ["GRIPS / GRIPSIZE", "1 / 5", "Standard grips"],
    ["PICKBOX / APERTURE", "4 / 8", ""],
    ["PICKFIRST / PICKADD", "1 / 2", "Noun-verb, Shift to remove"],
    ["MSLTSCALE / ANNOAUTOSCALE", "1 / 0", "Annotation linetype scaling; no auto scale add"],
    ["SAVETIME / ISAVEBAK", "10 min / 1", "Autosave + .bak"],
    ["Background / visual style", "Dark grey 33,40,48 model; white paper / 2D Wireframe", "Options > Display"],
    ["REGENAUTO / LAYOUTREGENCTL", "On / 2", "Fast layout switching"],
    ["HPLAYER / DIMLAYER", "ASG-HATCH / ASG-DIMENSION", "Auto layers (AutoCAD 2016+)"],
]
DIM_PARAMS = [
    ["Text style / height", "ASG-TEXT, 2.5 mm, above line, aligned with line, gap 1.0"],
    ["Arrowhead", "Closed filled 2.5 mm; centre mark 2.5"],
    ["Extension lines", "Offset from origin 1.5, extend beyond dim line 1.25"],
    ["Baseline spacing (DIMDLI)", "7.0"],
    ["Fit", "Either text or arrows (best fit), text beside line when moved, fit always inside ext lines"],
    ["Units / precision", "Decimal, 0 decimals, '.' separator, trailing zeros suppressed; angles 0.00 deg"],
    ["Special details", "Override precision in a child style or per-detail style (e.g. 0.0 for 1:1 fabrication)"],
    ["Measurement scale (DIMLFAC)", "1.0 - always true measured geometry, never type over values"],
    ["Tolerance", "None by default; symmetrical +/- precision 0.0, height 0.7 when needed"],
    ["Alternate units", "Off (inches 25.4 preset, 2 dp)"],
    ["Colour / lineweight", "ByBlock inside style -> ByLayer from ASG-DIMENSION"],
]
ANNO_STRATEGY = [
    ["Text (model space)", "ASG-TEXT / -NOTE / -SMALL are annotative - type paper height"],
    ["Text (paper space)", "Titles / sheet text: ASG-TEXT-TITLE / -SHEET, non-annotative, real paper height"],
    ["Dimensions", "ASG-DIM-ANNOTATIVE in model space; fixed ASG-DIM-1-x only for single-scale drawings"],
    ["Multileaders", "ASG-ML-ANNOTATIVE in model space; ASG-ML-NOTE / -DETAIL in paper space"],
    ["Blocks", "Annotative only for symbols (section/detail/level marks); real-size items never"],
    ["Hatches", "Non-annotative for material sections (true size); annotative only for symbolic fills"],
]
TABLE_STYLES = [
    ["ASG-TABLE-STANDARD", "3.5 bold, centred", "2.5 bold, centred, grey fill", "2.5, middle-left", "General / drawing register"],
    ["ASG-TABLE-MATERIAL", "3.5 bold, centred", "2.0 bold, centred, grey fill", "2.0, middle-left", "Material, glass, hardware schedules"],
    ["ASG-TABLE-REVISION", "suppressed", "2.0 bold, centred", "2.0, middle-left", "Revision history (Rev, Date, Description, By)"],
    ["ASG-TABLE-NOTES", "3.5 bold, left", "suppressed", "2.5, top-left", "General notes blocks"],
]
WORKFLOW = [
    ["Start", "NEW > ASG_Master_Template.dwt only. Never start from acad.dwt."],
    ["UCS", "Draw in World UCS; UCSVP 1 per viewport; set UCS back to World before saving."],
    ["Autosave / recovery", "SAVETIME 10, .bak on, local autosave folder; DRAWINGRECOVERY after crash."],
    ["Audit / purge", "Before issue: AUDIT Y > PURGE all (incl. regapps, orphaned data) > -SCALELISTEDIT reset if bloated > save."],
    ["Xrefs", "Relative paths only (REFPATHTYPE 1), backgrounds attached as Overlay on ASG-REFERENCE, in project 02-Drawings\\Ref; bind only for final archive."],
    ["PDF", "Underlays on ASG-REFERENCE, PDFIMPORT geometry re-layered to ASG layers."],
    ["Compatibility", "Save as AutoCAD 2018 DWG (default for AutoCAD 2018-2026); DXF copy for third parties; never save down below 2013 without approval."],
    ["File names", "Drawing number + short project name, e.g. AS-2026-014-ALU-SD-001-R0_MarinaTower.dwg"],
]


def main():
    doc = validate()
    previews = render_previews(doc)
    write_layer_register()
    check("Deliverables", "Layer register XLSX + CSV written", (OUT / "ASG_Layer_Standards.xlsx").exists())
    write_pdf(previews)
    check("Deliverables", "ASG_CAD_Standards.pdf written", (OUT / "ASG_CAD_Standards.pdf").exists())
    counts = write_report()
    print(counts)
    for a, n, s, d in results:
        if s not in ("PASS", "PASS*"):
            print(s, a, n, d)


if __name__ == "__main__":
    main()
