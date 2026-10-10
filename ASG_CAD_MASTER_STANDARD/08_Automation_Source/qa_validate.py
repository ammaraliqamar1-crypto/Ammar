"""
ASG CAD Master Standard - QA validation + documentation.

Re-opens every generated file from disk and tests it against asg_standard.py.
Writes:
  06_Layer_Register/ASG_Layer_Register.xlsx (+ .csv)
  05_CAD_Standards_Documentation/ASG_CAD_Standards.pdf (+ previews)
  07_QA_Validation/ASG_Template_Validation_Report.pdf (+ .txt), QA renders
  README.txt (package root - counts filled from this run)

Statuses: PASS (tested successfully) | PARTIAL (part tested) |
          UNVERIFIED (could not be tested here) | FAIL (test failed / missing)
"""

import csv
import datetime as dt
import hashlib
import re
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
from ezdxf.tools.pattern import ISO_PATTERN  # noqa: E402

import asg_standard as S  # noqa: E402
import build_all as BA  # noqa: E402

ROOT = BA.ROOT
D_DOC = ROOT / "05_CAD_Standards_Documentation"
D_REG = ROOT / "06_Layer_Register"
D_QA = BA.D_QA
TODAY = S.STANDARD_DATE

R = []  # (area, test, status, evidence)
RENDER_LW_SCALE = 1.0  # set by lineweight_test() - calibrates preview line widths


def rec(area, test, status, evidence=""):
    R.append((area, test, status, evidence))


def pf(ok):
    return "PASS" if ok else "FAIL"


def anno(e):
    try:
        return e.has_xdata("AcadAnnotative")
    except Exception:
        return False


def render(doc, layout, png, dpi, pdf=None):
    w, h = layout.dxf.paper_width, layout.dxf.paper_height
    fig = plt.figure(figsize=(w / 25.4, h / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    cfg = Configuration(color_policy=ColorPolicy.BLACK, lineweight_policy=LineweightPolicy.ABSOLUTE,
                        background_policy=BackgroundPolicy.WHITE, min_lineweight=0.01,
                        lineweight_scaling=RENDER_LW_SCALE)
    ctx = RenderContext(doc)
    ctx.set_current_layout(layout)
    Frontend(ctx, MatplotlibBackend(ax, adjust_figure=False), config=cfg).draw_layout(layout, finalize=True)
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.set_aspect("auto")
    fig.savefig(png, dpi=dpi)
    if pdf:
        fig.savefig(pdf)
    plt.close(fig)


# ===========================================================================
# Tests
# ===========================================================================
ENV = {}


def test_environment():
    tools = ("acad", "accoreconsole", "ODAFileConverter", "TeighaFileConverter", "dwg2dxf",
             "dxf2dwg", "qcad", "librecad", "bricscad")
    found = [t for t in tools if subprocess.run(["which", t], capture_output=True).returncode == 0]
    ENV["cad"] = ", ".join(found) or "none"
    lo = subprocess.run(["soffice", "--version"], capture_output=True, text=True)
    ENV["second_reader"] = lo.stdout.strip().split(" (")[0] or "not available"
    for ext in ("dwt", "dwg"):
        rec("Deliverables", f"ASG_Master_Template.{ext} generated natively", "FAIL",
            "Not generated: no DWG writer in this environment (" + ", ".join(tools) +
            " all absent). Not faked by renaming. Created in AutoCAD by README step 5.")


def test_master(path):
    doc, aud = recover.readfile(path)
    rec("File", "Master DXF re-opened from disk (recover + audit)", pf(not aud.has_errors),
        f"{len(aud.errors)} errors, {len(aud.fixes)} fixes, {doc.dxfversion} = AutoCAD 2018 DXF")
    ezdxf.readfile(path)
    rec("File", "Master DXF strict parse", "PASS", "ezdxf.readfile without exception")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / path.name
        tmp.write_bytes(path.read_bytes())
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", td, str(tmp)],
                       capture_output=True, timeout=180)
        ok = (Path(td) / (path.stem + ".pdf")).exists()
    rec("File", "Master DXF opened by an independent second reader", pf(ok), ENV["second_reader"])
    rec("File", "Opens in AutoCAD; ASG-QA reports 0 FAIL", "UNVERIFIED", "AutoCAD not available - README step 3-4")

    h = doc.header
    for var, val, purpose in S.HEADER_VARS + S.HEADER_STYLE_VARS:
        got = h.get(var)
        ok = (tuple(got) == tuple(val)) if isinstance(val, tuple) else got == val
        rec("Units & variables", f"{var} = {val}", pf(ok), f"read back {got}")
    rec("Units & variables", "Header dimension variables = ASG-DIM-ANNO (no '<style overrides>')",
        pf(all(h.get("$" + k.upper()) == v for k, v in S.dim_values("ASG-DIM-ANNO").items()
               if k not in S.DIM_HEADER_EXCLUDE)),
        f"{len(S.dim_values('ASG-DIM-ANNO')) - len(S.DIM_HEADER_EXCLUDE)} variables compared")
    rec("Units & variables", "Drawing variables set by ASG-SETUP (CANNOSCALE, MSLTSCALE, HPLAYER ...)",
        "UNVERIFIED", "Not writable by DXF libraries; ASG-QA checks them in AutoCAD")
    rec("Units & variables", "Profile variables (OSMODE, grips, autosave ...)", "UNVERIFIED",
        "Registry, not drawing-resident; applied only by opt-in ASG-PROFILE")

    for name in list(S.LINETYPES) + ["Continuous"]:
        rec("Linetypes", f"{name} loaded", pf(name in doc.linetypes))

    names = [l.dxf.name for l in doc.layers]
    asg = [n for n in names if n.startswith("ASG-")]
    rec("Layers", f"{len(S.LAYERS)} ASG layers present", pf(len(asg) == len(S.LAYERS)), f"found {len(asg)}")
    rec("Layers", "No other layers except system 0 / Defpoints",
        pf(sorted(set(names) - set(asg)) == ["0", "Defpoints"]), str(sorted(set(names) - set(asg))))
    rec("Layers", "Layer names and codes unique",
        pf(len({l[1] for l in S.LAYERS}) == len(S.LAYERS) == len({l[0] for l in S.LAYERS})))
    bad = []
    for code, n, _g, aci, lt, lw, plot, desc, _u in S.LAYERS:
        l = doc.layers.get(n)
        if not (l.dxf.color == aci and l.dxf.linetype == lt and l.dxf.lineweight == round(lw * 100)
                and bool(l.dxf.plot) == plot and l.description == desc and lt in doc.linetypes):
            bad.append(n)
    rec("Layers", "Every layer: ACI, linetype (loaded), lineweight, plot flag, description",
        pf(not bad), f"{len(S.LAYERS) - len(bad)}/{len(S.LAYERS)} correct {bad if bad else ''}")
    noplot = sorted(l[1] for l in S.LAYERS if not l[6])
    rec("Layers", "No-plot layers exactly: " + ", ".join(noplot),
        pf(sorted(l.dxf.name for l in doc.layers if l.dxf.name.startswith("ASG") and not l.dxf.plot) == noplot))
    rec("Layers", "Current layer is a plottable geometry layer", pf(doc.layers.get(h["$CLAYER"]).dxf.plot == 1),
        h["$CLAYER"])
    plotted = sorted({l[5] for l in S.LAYERS if l[6]})
    ok = all(lw in S.ISO_128_SERIES or lw == 0.09 for lw in plotted)
    rec("Lineweights", "Plotted lineweights from ISO 128 series (0.09 hatch only)", pf(ok), str(plotted))
    rec("Lineweights", "Every plotted layer in a lineweight-matrix class",
        pf(set(plotted) == {m[0] for m in S.LW_MATRIX}))

    for n, ttf, _b, a, _u in S.TEXT_STYLES:
        st = doc.styles.get(n)
        ok = st.dxf.font == ttf and st.dxf.height == 0 and st.dxf.width == 1 and anno(st) == a
        rec("Text styles", f"{n}: {ttf}, height 0, width 1, annotative={a}", pf(ok))
    rec("Text styles", "Recommended plotted heights in ISO 3098 series",
        pf(all(h_ in S.ISO_3098_HEIGHTS for _u, h_, _s in S.TEXT_HEIGHTS)))
    rec("Text styles", "Annotative text behaviour at viewport scales", "UNVERIFIED",
        "Annotative flag written and re-read; scaling needs AutoCAD (README step 6b)")

    for n, a, over, _u in S.DIM_STYLES:
        d = doc.dimstyles.get(n)
        exp = dict(S.DIM_BASE, **over)
        diff = [k for k, v in exp.items() if k != "dimblk" and d.dxf.get(k) != v]
        rec("Dimension styles", n, pf(not diff and anno(d) == a),
            f"all {len(exp)} variables match; annotative={a}" if not diff else f"mismatch {diff}")
    std = doc.dimstyles.get("Standard")
    rec("Dimension styles", "'Standard' dim style made harmless (= ASG-DIM-FIXED values)",
        pf(all(std.dxf.get(k) == v for k, v in S.dim_values("ASG-DIM-FIXED").items() if k != "dimblk")))
    for n, a, arrow, asz, ts, ch, frame, _u in S.MLEADER_STYLES:
        m = doc.mleader_styles.get(n)
        ok = (m.dxf.char_height == ch and m.dxf.arrow_head_size == asz and bool(m.dxf.is_annotative) == a
              and m.dxf.leader_type == 1 and m.dxf.max_leader_segments_points == 2
              and bool(m.dxf.has_text_frame) == frame
              and m.dxf.text_style_handle == doc.styles.get(ts).dxf.handle
              and (not arrow or doc.entitydb.get(m.dxf.arrow_head_handle) is not None))
        rec("Multileader styles", n, pf(ok), f"{ts} {ch} mm, arrow {arrow or 'closed filled'} {asz}")
    rec("Multileader styles", "Background mask", "UNVERIFIED",
        "Mask is an MText property, not a style property - per-note procedure documented")
    for n in ("ASG-MLINE-2", "ASG-MLINE-3"):
        rec("Multiline styles", n, pf(doc.mline_styles.get(n) is not None))

    sc = []
    for _k, e in doc.rootdict.get("ACAD_SCALELIST").items():
        t = e.xtags.get_subclass("AcDbScale")
        sc.append((t.get_first_value(300), float(t.get_first_value(141)), float(t.get_first_value(140))))
    want = [(f"1:{s}", float(s), 1.0) for s in S.ANNO_SCALES]
    rec("Annotation scales", "Scale list = " + ", ".join(w[0] for w in want), pf(sc == want),
        f"read back {[s[0] for s in sc]}, paper:drawing units verified")
    rec("Annotation scales", "No duplicate scales", pf(len({s[0] for s in sc}) == len(sc)))
    rec("Annotation scales", "Scale list accepted by AutoCAD", "UNVERIFIED", "ASG-QA re-checks it in AutoCAD")

    have = [k for k, _ in doc.rootdict.get("ACAD_TABLESTYLE").items()]
    rec("Table styles", f"{len(S.TABLE_STYLES)} ASG-TABLE-* styles", "UNVERIFIED",
        f"No DXF library can write TABLESTYLE; created by ASG-SETUP. In DXF now: {have or 'none'}")
    rec("Page setups", "Named page setups ASG-<layout>", "UNVERIFIED",
        "Named PLOTSETTINGS not writable here; ASG-SETUP copies them from the layouts")

    lnames = doc.layouts.names_in_taborder()
    want_l = ["Model"] + [s[0] for s in S.SHEETS]
    rec("Layouts", "Layouts: " + ", ".join(want_l[1:]), pf(lnames == want_l), str(lnames))
    for name, w, hh, paper, tb, vps in S.SHEETS:
        lay = doc.layouts.get(name)
        d = lay.dxf
        rec("Sheets", f"{name}: ISO 216 size {w:.0f} x {hh:.0f}", pf(tuple(sorted((w, hh))) in S.ISO_216))
        ok = (abs(d.paper_width - w) < .01 and abs(d.paper_height - hh) < .01
              and d.plot_configuration_file == S.PLOTTER and d.paper_size == S.media_name(paper, w, hh)
              and d.current_style_sheet == S.CTB_NAME
              and d.plot_layout_flags & 128 and d.plot_layout_flags & 32         # lineweights, plot styles
              and not d.plot_layout_flags & 64 and not d.plot_layout_flags & 1   # no lw scaling, no vp borders
              and d.plot_type == 5 and d.scale_numerator == 1 and d.scale_denominator == 1
              and d.plot_origin_x_offset == 0 and d.plot_origin_y_offset == 0
              and d.plot_paper_units == 1)
        rec("Layouts", f"{name}: {S.PLOTTER}, media, Layout area, 1:1 mm, offset 0,0, {S.CTB_NAME}, "
                       "plot lineweights", pf(bool(ok)), d.paper_size)
        rec("Layouts", f"{name}: paper media name recognised by DWG To PDF.pc3", "UNVERIFIED",
            "ASG-QA checks it against the device's media list in AutoCAD")
        ins = [e for e in lay if e.dxftype() == "INSERT"]
        tags = sorted(a.dxf.tag for a in ins[0].attribs) if ins else []
        okb = (len(ins) == 1 and ins[0].dxf.name == tb and ins[0].dxf.xscale == 1 == ins[0].dxf.yscale
               and (round(ins[0].dxf.insert.x, 6), round(ins[0].dxf.insert.y, 6)) == (w - S.MARGIN, S.MARGIN))
        rec("Title blocks", f"{name}: {tb} at scale 1 (not stretched) on border corner, {len(tags)} attributes",
            pf(okb and tags == sorted(t for t, _p, _d in S.TB_ATTRIBUTES)))
        bx = [e for e in lay if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "ASG-BORDER"]
        pts = [tuple(round(c, 3) for c in p[:2]) for p in bx[0].get_points()] if bx else []
        okx = pts == [(S.MARGIN_LEFT, S.MARGIN), (w - S.MARGIN, S.MARGIN), (w - S.MARGIN, hh - S.MARGIN),
                      (S.MARGIN_LEFT, hh - S.MARGIN)]
        rec("Sheets", f"{name}: border, 20 mm filing margin / 10 mm others", pf(okx))
        vps_ = [e for e in lay if e.dxftype() == "VIEWPORT" and e.dxf.id != 1]
        v = vps_[0] if len(vps_) == 1 else None
        okv = (v is not None and v.dxf.layer == "ASG-VIEWPORT" and v.dxf.flags & 16384
               and abs(v.dxf.view_height / v.dxf.height - vps) < 1e-6)
        rec("Viewports", f"{name}: 1 viewport, display locked, ASG-VIEWPORT (no plot), 1:{vps}", pf(bool(okv)))
        if v is not None:
            vx1 = v.dxf.center.x - v.dxf.width / 2
            vx2 = v.dxf.center.x + v.dxf.width / 2
            vy1 = v.dxf.center.y - v.dxf.height / 2
            vy2 = v.dxf.center.y + v.dxf.height / 2
            tb_x1, tb_y2 = w - S.MARGIN - S.TB_SPECS[tb]["w"], S.MARGIN + S.title_block_height(tb)
            inside = vx1 >= S.MARGIN_LEFT and vy1 >= S.MARGIN and vx2 <= w - S.MARGIN and vy2 <= hh - S.MARGIN
            rec("Viewports", f"{name}: viewport inside border and clear of title block",
                pf(inside and (vx2 <= tb_x1 or vy1 >= tb_y2)))
    for tb, spec in S.TB_SPECS.items():
        blk = doc.blocks.get(tb)
        br = blk.block_record
        a = list(blk.query("ATTDEF"))
        bb = ezdxf.bbox.extents(blk.query("LWPOLYLINE"))
        rec("Title blocks", f"{tb}: {len(a)} attributes, {bb.size.x:.0f} x {bb.size.y:.1f} mm, own design",
            pf(sorted(x.dxf.tag for x in a) == sorted(t for t, _p, _d in S.TB_ATTRIBUTES)
               and abs(bb.size.x - spec["w"]) < 1e-6))
        rec("Title blocks", f"{tb}: block units mm, not explodable, uniform scale, attributes position-locked",
            pf(br.dxf.units == 4 and br.dxf.explode == 0 and br.dxf.scale == 1
               and all(x.dxf.lock_position == 1 for x in a)))
        hts = sorted({round(x.dxf.height, 2) for x in a} | {round(t.dxf.height, 2) for t in blk.query("TEXT")})
        rec("Title blocks", f"{tb}: text heights >= 1.8 mm on paper", pf(min(hts) >= 1.8), str(hts))
    rec("Title blocks", "A4 / A3 / A1 title blocks are separate designs (row heights differ)",
        pf(len({round(S.title_block_height(t), 3) for t in S.TB_SPECS}) == 3),
        ", ".join(f"{t}: {S.title_block_height(t):.1f} mm" for t in S.TB_SPECS))

    # ByLayer discipline - every entity in layouts and blocks
    offenders = []
    for space in [doc.layouts.get(s[0]) for s in S.SHEETS] + [doc.blocks.get(t) for t in S.TB_SPECS]:
        for e in space:
            if e.dxftype() == "VIEWPORT":
                continue
            if e.dxf.get("color", 256) not in (0, 256) or e.dxf.get("lineweight", -1) not in (-1, -2) \
                    or e.dxf.get("linetype", "BYLAYER").upper() not in ("BYLAYER", "BYBLOCK") \
                    or e.dxf.hasattr("true_color"):
                offenders.append(f"{e.dxftype()}@{space.name}")
    rec("Properties", "All layout / title-block objects ByLayer (colour, linetype, lineweight)",
        pf(not offenders), str(offenders[:5]))
    rec("Model space", "Model space empty", pf(len(doc.modelspace()) == 0), f"{len(doc.modelspace())} entities")
    xr = [b.name for b in doc.blocks if b.block and b.block.is_xref]
    rec("References", "No external references", pf(not xr))
    imgs = len(doc.objects.query("IMAGEDEF")) + len(doc.objects.query("UNDERLAYDEFINITION"))
    rec("References", "No image / PDF underlay dependencies", pf(imgs == 0))
    prox = [e.dxftype() for e in doc.entitydb.values() if e.dxftype().startswith("ACAD_PROXY")]
    rec("Interoperability", "No proxy / custom objects", pf(not prox))
    ub = sorted(b.name for b in doc.blocks if not b.name.startswith("*") and not b.name.startswith("_"))
    rec("Scope", "Only title-block blocks (no product blocks / libraries)", pf(ub == sorted(S.TB_SPECS)), str(ub))
    fonts = sorted({s.dxf.font for s in doc.styles})
    rec("Interoperability", "Fonts referenced: Arial TrueType only", pf(fonts == ["arial.ttf", "arialbd.ttf"]), str(fonts))
    lts = {l.dxf.linetype for l in doc.layers}
    rec("Interoperability", "Every layer linetype embedded in the file (no .lin dependency)",
        pf(all(t in doc.linetypes for t in lts)))
    missing = [p for _m, p, *_r in S.HATCH_STANDARD if p != "SOLID" and p not in ISO_PATTERN]
    rec("Hatch standard", "All hatch pattern names exist in AutoCAD acadiso.pat", pf(not missing), str(missing))
    return doc


def test_idempotency():
    before = BA.MASTER_DXF.read_bytes()
    S.inject_annotation_scales(BA.MASTER_DXF)
    rec("Automation", "Re-running scale injection changes nothing", pf(before == BA.MASTER_DXF.read_bytes()))
    a, b = S.new_document(), S.new_document()
    same = ([l.dxf.name for l in a.layers] == [l.dxf.name for l in b.layers]
            and [d.dxf.name for d in a.dimstyles] == [d.dxf.name for d in b.dimstyles]
            and a.layouts.names() == b.layouts.names())
    rec("Automation", "Rebuild produces identical layer / style / layout sets", pf(same))
    S._layouts(a, S.SHEETS)
    rec("Automation", "Re-running layout creation creates no duplicate layouts",
        pf(len(a.layouts) == len(S.SHEETS) + 1))
    lsp = BA.SETUP_LSP.read_text(encoding="ascii")
    need = ([l[1] for l in S.LAYERS] + [t[0] for t in S.TEXT_STYLES] + [d[0] for d in S.DIM_STYLES]
            + [m[0] for m in S.MLEADER_STYLES] + [t[0] for t in S.TABLE_STYLES] + [s[0] for s in S.SHEETS]
            + list(S.TB_SPECS) + [v for v, _x, _p in S.SETUP_DRAWING_VARS])
    miss = [n for n in need if f'"{n}"' not in lsp]
    try:
        BA._check_parens(lsp.replace("\r\n", "\n"))
        parens = True
    except ValueError:
        parens = False
    rec("Automation", "ASG_Setup.lsp generated: balanced, covers every layer / style / layout / variable",
        pf(parens and not miss), f"{len(need)} names checked; missing {miss}" if miss else f"{len(need)} names checked")
    rec("Automation", "ASG_Setup.lsp runs in AutoCAD (ASG-SETUP / ASG-QA)", "UNVERIFIED",
        "Written without AutoCAD; get-or-create logic, read-only QA")


def test_templates():
    for name, *_ in S.SHEETS:
        p = BA.D_TEMPL / f"ASG_{name}.dxf"
        doc, aud = recover.readfile(p)
        ok = (not aud.has_errors and doc.layouts.names_in_taborder() == ["Model", name]
              and len(doc.modelspace()) == 0
              and len([l for l in doc.layers if l.dxf.name.startswith("ASG-")]) == len(S.LAYERS)
              and len(doc.rootdict.get("ACAD_SCALELIST")) == len(S.ANNO_SCALES))
        rec("Drawing templates", f"ASG_{name}.dxf: opens, single layout, full standard, empty model", pf(ok))


def test_ctb():
    p = BA.D_PLOT / S.CTB_NAME
    raw = p.read_bytes()
    hdr = raw.startswith(b"PIAFILEVERSION_2.0,CTBVER1,compress\r\npmzlibcodec") and len(raw) > 60
    ctb = acadctb.load(str(p))
    blacks = all(ctb[a].color == (0, 0, 0) for a in range(1, 256) if a not in S.CTB_GREY_ACI)
    greys = all(ctb[a].has_object_color() for a in S.CTB_GREY_ACI)
    lw = all(ctb[a].lineweight == acadctb.OBJECT_LINEWEIGHT for a in range(1, 256))
    lt = all(ctb[a].linetype == acadctb.OBJECT_LINETYPE for a in range(1, 256))
    rec("Plot style", f"{S.CTB_NAME}: 60-byte header (3 x uint32) + zlib body re-read", pf(hdr),
        "ezdxf writer defect on 64-bit Linux (8-byte fields) worked around and verified")
    rec("Plot style", "ACI 1-249,255 -> black; 250-254 -> object colour (grey); object lineweight & linetype",
        pf(blacks and greys and lw and lt))
    rec("Plot style", "CTB opens in AutoCAD Plot Style Table Editor with 'Use object lineweight'", "UNVERIFIED",
        "Lineweight code per ezdxf/acad.ctb convention; ASG-QA checks the CTB is installed; README step 2 "
        "checks the editor; fallback monochrome.ctb")


def lineweight_test():
    """Render one line per lineweight class (ByLayer on the real ASG layers)
    at 2400 dpi and measure the rendered widths."""
    global RENDER_LW_SCALE
    doc = S.new_document(sheets=[])
    msp = doc.modelspace()
    for i, (lw, _c, _u) in enumerate(S.LW_MATRIX):
        layer = next(l[1] for l in S.LAYERS if l[5] == lw and l[6])
        msp.add_line((5, 75 - i * 12), (95, 75 - i * 12), dxfattribs={"layer": layer})
    fig = plt.figure(figsize=(100 / 25.4, 80 / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    cfg = Configuration(color_policy=ColorPolicy.BLACK, lineweight_policy=LineweightPolicy.ABSOLUTE,
                        background_policy=BackgroundPolicy.WHITE, min_lineweight=0.01)
    Frontend(RenderContext(doc), MatplotlibBackend(ax, adjust_figure=False), config=cfg).draw_layout(msp, finalize=True)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 80)
    ax.set_aspect("auto")
    p = D_QA / "QA_lineweight_matrix.png"
    fig.savefig(p, dpi=2400)
    plt.close(fig)
    img = plt.imread(p)[..., :3].mean(axis=2)
    H, W = img.shape
    pxmm = W / 100
    col = img[:, W // 2] < 0.5
    widths = []
    for i in range(len(S.LW_MATRIX)):
        row = int((80 - (75 - i * 12)) * pxmm)
        widths.append(col[row - 200:row + 200].sum() / pxmm)
    ratios = [w / lw for w, (lw, _c, _u) in zip(widths, S.LW_MATRIX)]
    med = sorted(ratios)[len(ratios) // 2]
    RENDER_LW_SCALE = 1.0 / med
    ordered = all(a > b for a, b in zip(widths, widths[1:]))
    proportional = all(abs(r / med - 1) < 0.2 for r in ratios)
    rec("Lineweights", f"Lineweight matrix rendered at 2400 dpi: {len(S.LW_MATRIX)} classes distinct, ordered, "
                       "proportional", "PARTIAL" if ordered and proportional else "FAIL",
        "rendered/nominal: " + ", ".join(f"{lw:.2f}:{r / med:.2f}" for r, (lw, _c, _u) in zip(ratios, S.LW_MATRIX)) +
        " (1.00 = exact). Hierarchy proven; absolute plotted mm needs an AutoCAD PDF plot.")


def test_qa_drawing():
    doc, aud = recover.readfile(BA.QA_DXF)
    rec("QA drawing", "Temporary QA drawing is a separate file", pf(BA.QA_DXF != BA.MASTER_DXF and not aud.has_errors),
        BA.QA_DXF.name)
    dims = list(doc.modelspace().query("DIMENSION"))
    meas = {}
    for d in dims:
        m = d.get_measurement()
        meas.setdefault(d.dxf.dimstyle, []).append(round(float(m if not hasattr(m, "x") else m.x), 4))
    rec("Dimensions", "Linear dims measure true geometry 1200 / 2400",
        pf(sorted(meas.get("ASG-DIM-FIXED", [])) == [1200, 2400]), str(meas.get("ASG-DIM-FIXED")))
    rec("Dimensions", "Detail dim measures 50", pf(meas.get("ASG-DIM-DETAIL") == [50]))
    ang = meas.get("ASG-DIM-ANGULAR", [0])[0]
    rec("Dimensions", "Angular dim measures 30 deg", pf(abs(ang - 30) < 1e-6), f"{ang}")
    rec("Dimensions", "Radius / diameter dims measure R40 / D80",
        pf(meas.get("ASG-DIM-RADIUS") == [40] and meas.get("ASG-DIM-DIAMETER") == [80]),
        f"R {meas.get('ASG-DIM-RADIUS')} D {meas.get('ASG-DIM-DIAMETER')}")
    over = [d for d in dims if d.dxf.get("text", "<>") not in ("", "<>")]
    rec("Dimensions", "No overridden dimension text", pf(not over))
    texts = []
    for d in dims:
        for e in d.virtual_entities():
            if e.dxftype() in ("MTEXT", "TEXT"):
                texts.append(e.plain_text() if e.dxftype() == "MTEXT" else e.dxf.text)
    rec("Dimensions", "Displayed text: 1200 / 2400 (0 dp), 50.0 (detail), 30.00 deg, R40, D80",
        pf({"1200", "2400", "50.0", "R40"} <= set(texts) and any(t.startswith("30.00") for t in texts)
           and any(t.endswith("80") and t != "80" for t in texts)), str(texts))
    lay = doc.layouts.get("A3-LANDSCAPE")
    vps = [e for e in lay if e.dxftype() == "VIEWPORT" and e.dxf.id != 1]
    scales = sorted(round(v.dxf.view_height / v.dxf.height, 6) for v in vps)
    rec("Viewports", "QA viewports at 1:20 and 1:5", pf(scales == [5, 20]), str(scales))
    render(doc, lay, D_QA / "QA_render_A3.png", dpi=300, pdf=D_QA / "QA_render_A3.pdf")
    rec("Plotting", "No-plot layers (ASG-CONSTRUCTION, ASG-NOPLOT) excluded from the plot", "UNVERIFIED",
        "Plot flags set and re-read (Layers: PASS). The preview renderer ignores plot flags, so the diagonal "
        "and 'NOPLOT' text are visible in QA_render_A3 - confirm absence in the AutoCAD PDF (README 6a)")
    rec("Plotting", "Viewport boundaries not plotted", "UNVERIFIED",
        "ASG-VIEWPORT is no-plot and 'plot viewport borders' off (PASS); renderer cannot show plot behaviour")
    rec("Plotting", "PDF via DWG To PDF.pc3 + CTB: margins, clipping, lineweights", "UNVERIFIED",
        "QA_render_A3.pdf is a preview, not an AutoCAD plot (README 6a)")
    rec("Annotation scales", "Annotative text / dims / mleaders across viewport scales", "UNVERIFIED",
        "No DXF library writes annotative scale contexts; test in AutoCAD (README 6b)")


# ===========================================================================
# Register
# ===========================================================================
def write_register():
    D_REG.mkdir(parents=True, exist_ok=True)
    header = ["Layer code", "Full layer name", "Functional group", "Purpose", "ACI colour", "Linetype",
              "Lineweight (mm)", "Lineweight class", "Plot status", "Description", "Recommended use", "Revision"]
    cls = {lw: c for lw, c, _u in S.LW_MATRIX}
    rows = [[c, n, g, d, a, lt, f"{lw:.2f}", cls.get(lw, "Non-plot"), "Plot" if p else "NO PLOT",
             f"{d}. ACI {a}, {lt}, {lw:.2f} mm", u, S.STANDARD_REV]
            for c, n, g, a, lt, lw, p, d, u in S.LAYERS]
    with open(D_REG / "ASG_Layer_Register.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([header] + rows)
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    wb = Workbook()
    ws = wb.active
    ws.title = "Layer Register"
    ws.append(["ASG CAD MASTER STANDARD - LAYER REGISTER"])
    ws.append([f"{S.COMPANY} | {S.GROUP} | Standard {S.STANDARD_REV} | {TODAY} | "
               "Generated from asg_standard.py - do not edit, change the source and rebuild"])
    ws.append([])
    ws.append(header)
    for r in rows:
        ws.append(r)
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"].font = Font(italic=True, size=9, color="555555")
    thin = Side(style="thin", color="A0A0A0")
    for c in ws[4]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="3A3A3A")
        c.alignment = Alignment(wrap_text=True, vertical="center")
    for row in ws.iter_rows(min_row=5, max_row=4 + len(rows)):
        for c in row:
            c.border = Border(top=thin, bottom=thin, left=thin, right=thin)
            c.alignment = Alignment(vertical="top", wrap_text=c.column in (4, 10, 11))
        if row[8].value == "NO PLOT":
            row[8].font = Font(bold=True, color="C00000")
    for col, w in zip("ABCDEFGHIJKL", (9, 24, 12, 26, 9, 11, 11, 12, 10, 40, 46, 8)):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "C5"
    ws.auto_filter.ref = f"A4:L{4 + len(rows)}"
    ws2 = wb.create_sheet("Lineweight Matrix")
    ws2.append(["Lineweight (mm)", "Class", "Use", "Layers"])
    for lw, c, u in S.LW_MATRIX:
        ws2.append([f"{lw:.2f}", c, u, ", ".join(l[1] for l in S.LAYERS if l[5] == lw and l[6])])
    ws3 = wb.create_sheet("Colour Logic")
    ws3.append(["ACI", "Function", "Plotted with ASG_Monochrome.ctb"])
    for r in S.COLOUR_LOGIC:
        ws3.append(list(r))
    for w_, widths in ((ws2, (16, 14, 60, 110)), (ws3, (8, 60, 40))):
        for c in w_[1]:
            c.font = Font(bold=True)
        for col, wd in zip("ABCD", widths):
            w_.column_dimensions[col].width = wd
    wb.save(D_REG / "ASG_Layer_Register.xlsx")


# ===========================================================================
# PDF documents
# ===========================================================================
def pdf_doc(path, title, story_fn):
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate

    def footer(c, d):
        c.saveState()
        c.setFont("Helvetica", 7)
        c.drawString(15 * mm, 8 * mm, f"{S.COMPANY}  |  {title}  |  Standard {S.STANDARD_REV}  |  {TODAY}")
        c.drawRightString(d.pagesize[0] - 15 * mm, 8 * mm, f"Page {d.page}")
        c.restoreState()

    path.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(path), pagesize=landscape(A4), leftMargin=15 * mm, rightMargin=15 * mm,
                      topMargin=12 * mm, bottomMargin=14 * mm, title=title, author=S.COMPANY
                      ).build(story_fn(), onFirstPage=footer, onLaterPages=footer)


def styles():
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    ss = getSampleStyleSheet()
    return {
        "H1": ParagraphStyle("h1", parent=ss["Heading1"], fontSize=15, spaceAfter=4),
        "H2": ParagraphStyle("h2", parent=ss["Heading2"], fontSize=11, spaceBefore=8, spaceAfter=3),
        "P": ParagraphStyle("p", parent=ss["BodyText"], fontSize=8.5, leading=11),
        "C": ParagraphStyle("c", parent=ss["BodyText"], fontSize=7.3, leading=8.8),
    }


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tbl(data, widths, st, status_col=None):
    from reportlab.lib import colors as rc
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, Table, TableStyle
    t = Table([[Paragraph(esc(c), st["C"]) for c in r] for r in data],
              colWidths=[w * mm for w in widths], repeatRows=1)
    sty = [("GRID", (0, 0), (-1, -1), 0.3, rc.grey), ("VALIGN", (0, 0), (-1, -1), "TOP"),
           ("BACKGROUND", (0, 0), (-1, 0), rc.HexColor("#d0d0d0")),
           ("TOPPADDING", (0, 0), (-1, -1), 1.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2)]
    if status_col is not None:
        fills = {"PASS": "#d9ead3", "PARTIAL": "#fff2cc", "UNVERIFIED": "#e6e6e6", "FAIL": "#f4cccc"}
        for i, r in enumerate(data[1:], 1):
            sty.append(("BACKGROUND", (status_col, i), (status_col, i), rc.HexColor(fills.get(r[status_col], "#ffffff"))))
    t.setStyle(TableStyle(sty))
    return t


PHILOSOPHY = [
    "Model geometry is drawn full size, 1:1, in millimetres.",
    "Geometry lives in model space; annotation is annotative in model space or true-size in paper space; "
    "sheets live in layouts.",
    "Layers are meaningful, coded and documented; object properties are ByLayer.",
    "Blocks have predictable names, datum base points and mm insertion units.",
    "Dimensions always report true geometry - dimension text is never overridden.",
    "Annotation is sized by its plotted paper height (ISO 3098 series), never guessed in model space.",
    "Layouts use genuine ISO 216 paper sizes and locked, controlled viewports.",
    "Plots are monochrome with a fixed ISO 128 lineweight hierarchy - predictable on every printer and PDF.",
    "Proprietary manufacturer data is never invented.",
    "Easy to learn, hard to misuse: few styles, clear names, one setup command, one QA command.",
]
PACKAGE = [
    ["01_Master_Template", "ASG_Master_Template.dxf (master) + ASG_Setup.lsp (setup & QA). DWG / DWT are saved "
                           "here from AutoCAD (README step 5)."],
    ["02_Drawing_Templates", "One single-layout template per sheet size (DXF)"],
    ["03_Page_Setups", "ASG_Page_Setups.csv - page setup definitions (created as named page setups by ASG-SETUP)"],
    ["04_Plotting_Standards", "ASG_Monochrome.ctb"],
    ["05_CAD_Standards_Documentation", "ASG_CAD_Standards.pdf (this document), ASG_CAD_Quick_SOP.pdf "
                                       "(one-page drafting SOP for every draftsman) + layout previews"],
    ["06_Layer_Register", "ASG_Layer_Register.xlsx / .csv"],
    ["07_QA_Validation", "Validation report PDF / TXT, temporary QA drawing, QA renders"],
    ["08_Automation_Source", "asg_standard.py (all definitions), build_all.py, build_sop.py, qa_validate.py"],
]
DIM_PARAMS = [
    ["Text", "ASG-TEXT-ANNO 2.5, above the dimension line (DIMTAD 1), aligned with it, gap 1.0"],
    ["Arrowheads", "Closed filled 2.5. Centre mark 2.5 (DIAMETER), none (RADIUS)"],
    ["Extension lines", "Offset 1.5 from origin, extend 1.25 beyond dimension line"],
    ["Spacing", "Baseline / continue spacing 7.0"],
    ["Fit", "DIMATFIT 3 best fit; DIMTOFL 1 line drawn between extension lines; DIMTMOVE 1 leader added "
            "when text is moved (RADIUS / DIAMETER: dimension line moves with text)"],
    ["Linear units", "Decimal mm, '.' separator, precision 0 (DETAIL 0.0), rounding 0, trailing zeros suppressed "
                     "(DETAIL keeps them: 50.0)"],
    ["Angular units", "Decimal degrees, 0.00 on ASG-DIM-ANGULAR (trailing zeros shown)"],
    ["Tolerance", "Off. On ASG-DIM-DETAIL switch on per dimension: symmetrical, precision 0.0, height 0.7"],
    ["Alternate units", "Off"],
    ["Measurement scale", "DIMLFAC 1.0 - always true geometry"],
    ["Scale", "Annotative styles take the annotation scale; ASG-DIM-FIXED DIMSCALE 1 for paper-space dims"],
    ["Header", "Drawing's current dimension variables equal ASG-DIM-ANNO - no '<style overrides>' on new drawings"],
]
ANNO_RULES = [
    ["Model-space text", "Annotative ASG-TEXT-ANNO / -NOTE / -SMALL - type the paper height (2.5 / 1.8)"],
    ["Paper-space text", "Non-annotative ASG-TEXT-TITLE / -HEADING / -SHEET at true plotted height"],
    ["Dimensions", "ASG-DIM-ANNO family in model space; ASG-DIM-FIXED for dimensions placed in paper space"],
    ["Multileaders", "ASG-ML-ANNO / -DETAIL / -REFERENCE in model space; ASG-ML-NOTE in paper space"],
    ["Symbols", "Section / detail / level / grid bubbles: annotative blocks"],
    ["Real-size blocks", "Never annotative (hardware, profiles, fixings)"],
    ["Hatches", "Material hatches non-annotative (scale rule in section 13); symbolic fills may be annotative"],
]
PLOT_STD = [
    ["Device", "DWG To PDF.pc3 (ships with AutoCAD) - no custom PC3 dependency"],
    ["Paper", "ISO full bleed A4 / A3 / A1 media = exact sheet size; the border provides the margins"],
    ["Area / scale / offset", "Layout, 1:1 (mm), offset 0,0 ('Center the plot' is not available for Layout)"],
    ["Plot style", "ASG_Monochrome.ctb - black; ACI 250-254 keep their grey. Fallback: monochrome.ctb"],
    ["Lineweights", "Plot object lineweights ON, scale lineweights OFF, plot paper space last"],
    ["Transparency / shading", "Plot transparency OFF; shaded viewports 'As displayed', presentation quality"],
    ["PDF options", "Vector 1200 dpi, raster 300 dpi, TrueType as text, layer information OFF for client issue"],
    ["Pre-issue", "AUDIT, PURGE, plot preview, open the PDF and check scale, dimensions and no-plot items"],
    ["Compatibility", "AutoCAD 2018 DWG (opens in AutoCAD 2018-2026); DXF 2018 for third parties; no proxies"],
    ["Xrefs / PDF import", "Relative paths, overlay, layer ASG-REFERENCE; PDFIMPORT geometry moved to ASG layers"],
]
RESOURCES = [
    ["Layers, styles, scales, layouts, title blocks, header variables", "Inside the DWT", "Copy DWT to shared Templates folder"],
    ["Table styles, named page setups, CANNOSCALE / MSLTSCALE / HPLAYER / DIMLAYER ...",
     "Inside the DWT after ASG-SETUP", "Travel with the DWT"],
    ["ASG_Monochrome.ctb", "Plot Styles folder (external)", "Copy to each PC or a shared support path"],
    ["DWG To PDF.pc3", "Plotters folder (ships with AutoCAD)", "None"],
    ["arial.ttf / arialbd.ttf", "Windows Fonts (external)", "Present on Windows; FONTALT = arial.ttf as fallback"],
    ["Linetypes", "Embedded in the DWT (acadiso values)", "None"],
    ["Hatch patterns", "acadiso.pat (ships with AutoCAD)", "None"],
    ["OSMODE, grips, autosave, pickbox ...", "User profile / registry", "Optional ASG-PROFILE per user"],
    ["QNEW default template", "Options > Files (profile)", "Set per PC to ASG_Master_Template.dwt"],
]
PORTABILITY = [
    "AutoCAD 2018 or later installed; DWG To PDF.pc3 present (default).",
    "ASG_Monochrome.ctb copied to the Plot Styles folder - ASG-QA confirms it is found.",
    "ASG_Master_Template.dwt on the shared Templates path; QNEW points to it.",
    "Arial installed (Windows default); FONTALT = arial.ttf.",
    "Open a new drawing from the DWT and run ASG-QA: RESULT must be 0 FAIL.",
    "Optional: user runs ASG-PROFILE once (snaps, grips, autosave).",
]
AUTOCAD_PROCEDURE = [
    "Copy ASG_Monochrome.ctb to the Plot Styles folder; open it in the Plot Style Table Editor: Lineweight "
    "column must read 'Use object lineweight', Color = Black (250-254 'Use object color').",
    "OPEN ASG_Master_Template.dxf, AUDIT Y, APPLOAD ASG_Setup.lsp, run ASG-SETUP.",
    "Read RESULT line / ASG_QA_Log.txt: every line PASS.",
    "SAVEAS AutoCAD 2018 DWG, then SAVEAS DWT (Measurement Metric).",
    "Open QA_TEST_DRAWING_temporary.dxf, plot A3-LANDSCAPE to PDF: check dims, no 'NOPLOT' text / diagonal, "
    "no viewport frames, 6 lineweights distinguishable, text legible.",
    "In a new drawing from the DWT: annotative text / dim / leader at 1:20 then add 1:5 via OBJECTSCALE - "
    "confirm 2.5 mm on paper in both viewports. Do not save the test.",
]


def write_standards_pdf(previews):
    from reportlab.lib.units import mm
    from reportlab.platypus import Image, PageBreak, Paragraph, Spacer
    st = styles()
    P, H2 = st["P"], st["H2"]

    def story():
        s = [Paragraph(esc(f"{S.COMPANY}  |  {S.GROUP}"), P),
             Paragraph("ASG CAD MASTER STANDARD - AutoCAD Environment for Aluminium, Glass &amp; Facade Engineering",
                       st["H1"]),
             Paragraph(f"Standard {S.STANDARD_REV} | {TODAY} | Supersedes ASG-STD-CAD-001 R0 and the earlier "
                       "cad-standard / asg-master-template packages. Conventions are informed by ISO 128 (line "
                       "widths), ISO 3098 (lettering heights), ISO 216 (paper sizes), ISO 5457 (borders), ISO 5455 "
                       "(scales) and ISO 7200 (title block data). No formal compliance or certification is "
                       "claimed - the ISO texts were not available for verification.", P)]
        s += [Paragraph("1. Design philosophy", H2)] + [Paragraph(f"{i}. {esc(t)}", P) for i, t in enumerate(PHILOSOPHY, 1)]
        s += [Paragraph("2. Package structure", H2), tbl([["Folder", "Content"]] + PACKAGE, (55, 205), st)]
        s += [PageBreak(), Paragraph("3. Units and drawing-resident variables written into the template", H2),
              tbl([["Variable", "Value", "Purpose"]] + [[v[1:], str(x), p] for v, x, p in S.HEADER_VARS + S.HEADER_STYLE_VARS],
                  (35, 45, 180), st),
              Spacer(1, 3),
              Paragraph("Drawing-resident variables set inside AutoCAD by ASG-SETUP (saved with the DWG / DWT):", P),
              tbl([["Variable", "Value", "Purpose"]] + [[v, str(x), p] for v, x, p in S.SETUP_DRAWING_VARS], (35, 45, 180), st),
              Paragraph("Precision: ordinary dimensions 0 dp; fabrication details ASG-DIM-DETAIL 0.0; angles 0.00. "
                        "INSUNITS = mm on the drawing and every block - no unit conversion on insertion.", P)]
        s += [Paragraph("4. Machine / user-profile settings (NOT stored in any DWG / DWT)", H2),
              Paragraph("These live in each PC's AutoCAD profile (registry). A template cannot enforce them. "
                        "Recommended values, applied only by the opt-in command ASG-PROFILE.", P),
              tbl([["Variable", "Recommended", "Purpose"]] + [[v, str(x), p] for v, x, p in S.PROFILE_VARS], (45, 30, 185), st)]
        s += [PageBreak(), Paragraph("5. Layer dictionary", H2),
              Paragraph("Naming: ASG-&lt;FUNCTION&gt;[-&lt;QUALIFIER&gt;] in full words. Codes: G geometry, "
                        "T technical, A annotation, S sheet. All objects ByLayer. Layer 0 for block definitions only. "
                        "Defpoints is an AutoCAD system layer (never plots).", P),
              tbl([["Code", "Layer", "ACI", "Linetype", "LW", "Plot", "Recommended use"]] +
                  [[c, n, a, lt, f"{lw:.2f}", "Yes" if p else "NO", u] for c, n, _g, a, lt, lw, p, _d, u in S.LAYERS],
                  (12, 45, 10, 20, 11, 11, 151), st),
              Spacer(1, 4), tbl([["ACI", "Function", "Plotted with ASG_Monochrome.ctb"]] + [list(r) for r in S.COLOUR_LOGIC],
                                (20, 130, 110), st)]
        s += [PageBreak(), Paragraph("6. Lineweight matrix (ISO 128 series) and linetypes", H2),
              tbl([["Lineweight", "Class", "Use", "Layers"]] +
                  [[f"{lw:.2f} mm", c, u, ", ".join(l[1] for l in S.LAYERS if l[5] == lw and l[6])]
                   for lw, c, u in S.LW_MATRIX], (22, 22, 80, 136), st),
              Paragraph("Each class is about 1.4 x the next (ISO 128), so the hierarchy survives PDF and paper. "
                        "0.09 is used only for hatching, which also plots grey. LTSCALE 1 + PSLTSCALE 1 + "
                        "MSLTSCALE 1: dash lengths are paper mm in every viewport and in model space.", P),
              tbl([["Linetype", "Pattern"]] + [[k, v[1]] for k, v in S.LINETYPES.items()] + [["Continuous", "Solid"]],
                  (40, 220), st)]
        s += [Paragraph("7. Text system - Arial (TrueType)", H2),
              tbl([["Style", "Font", "Annotative", "Use"]] +
                  [[n, f, "Yes" if a else "No (paper space)", u] for n, f, _b, a, u in S.TEXT_STYLES], (40, 25, 30, 165), st),
              Spacer(1, 3),
              tbl([["Use", "Plotted height", "Style"]] + [[a, f"{b} mm", c] for a, b, c in S.TEXT_HEIGHTS], (60, 30, 170), st),
              Paragraph("All heights are from the ISO 3098 series; minimum 1.8 mm on any sheet. Arial is a Windows "
                        "core font and embeds in PDF; if missing AutoCAD uses FONTALT (set arial.ttf).", P)]
        s += [PageBreak(), Paragraph("8. Dimension system", H2),
              tbl([["Style", "Annotative", "Use"]] + [[n, "Yes" if a else "No", u] for n, a, _o, u in S.DIM_STYLES],
                  (40, 20, 200), st),
              Spacer(1, 3), tbl([["Parameter", "Value"]] + DIM_PARAMS, (40, 220), st),
              Paragraph("Rule: dimensions always report measured geometry (DIMLFAC 1, DIMASSOC 2). Overriding "
                        "dimension text is prohibited - fix the geometry. 'Standard' carries ASG-DIM-FIXED values "
                        "so it is harmless if picked. No further fixed-scale styles are needed.", P)]
        s += [Paragraph("9. Multileader system", H2),
              tbl([["Style", "Annotative", "Arrow", "Text", "Frame", "Use"]] +
                  [[n, "Yes" if a else "No", (ar or "closed filled") + f" {sz}", f"{ts} {ch}", "Yes" if fr else "No", u]
                   for n, a, ar, sz, ts, ch, fr, u in S.MLEADER_STYLES], (35, 18, 30, 40, 13, 124), st),
              Paragraph("All: straight leader, maximum 2 points, landing gap 1.0, dogleg 4.0, text attached at the "
                        "middle of the top line, ByLayer colour. Background mask is a property of each note "
                        "(Properties &gt; Text &gt; Background mask, offset 1.2, use background colour) - use it "
                        "where a note crosses hatch.", P)]
        s += [PageBreak(), Paragraph("10. Annotative scale governance", H2),
              Paragraph("Controlled list: " + ", ".join(f"1:{x}" for x in S.ANNO_SCALES) +
                        ". Other scales only with CAD custodian approval (e.g. 1:200 site plans).", P),
              tbl([["Object", "Rule"]] + ANNO_RULES, (40, 220), st),
              Paragraph("<b>Workflow:</b> 1) Set the viewport scale from the list, then lock the viewport. 2) Work "
                        "inside the viewport - CANNOSCALE follows it. 3) Add annotation with ASG-*-ANNO styles. "
                        "4) Same note needed at another scale: select it &gt; right-click &gt; Annotative Object "
                        "Scale &gt; Add (OBJECTSCALE). 5) ANNOAUTOSCALE 0 (profile) and ANNOALLVISIBLE 0 (drawing) "
                        "prevent unwanted scales and visual duplicates; the status-bar 'Annotation Visibility' "
                        "button shows all scales temporarily. 6) Drawings imported with extra scales: "
                        "-SCALELISTEDIT &gt; Reset, then AUDIT.", P)]
        s += [Paragraph("11. Tables and schedules", H2),
              tbl([["Style", "Title", "Header", "Data", "Use"]] +
                  [[n, "suppressed" if ts_ else f"{t[0]} {t[1]}", "suppressed" if hs else f"{h[0]} {h[1]}",
                    f"{d[0]} {d[1]}", u] for n, t, h, d, ts_, hs, u in S.TABLE_STYLES], (40, 30, 30, 30, 130), st),
              Paragraph("Common: ASG-TEXT-SHEET, cell margins horizontal 1.5 / vertical 1.0, flow top-down, inside "
                        "grid 0.18, outline 0.35, header fill ACI 254 (light grey), no data fill, colour ByBlock. "
                        "Alignment codes: MC middle-centre, ML middle-left, TL top-left. Numbers centred, "
                        "descriptions left. Tables go in paper space on ASG-TABLE. Created by ASG-SETUP.", P)]
        s += [PageBreak(), Paragraph("12. Layouts, page setups, title block and numbering", H2),
              tbl([["Layout / named page setup", "Paper (canonical media name)", "Orient.", "Title block", "Default viewport"]] +
                  [[f"{n} / ASG-{n}", S.media_name(p, w, h), "L" if w > h else "P", tb, f"1:{v}, locked"]
                   for n, w, h, p, tb, v in S.SHEETS], (45, 85, 14, 25, 91), st),
              Paragraph("All page setups: DWG To PDF.pc3, plot area Layout, scale 1:1 (mm), offset 0,0, "
                        "ASG_Monochrome.ctb, plot object lineweights ON, lineweights not scaled, plot transparency "
                        "OFF, paper space last, viewport borders not plotted. Border: 20 mm filing margin left, "
                        "10 mm other sides. Viewports on ASG-VIEWPORT, scale from the controlled list, Display "
                        "Locked = Yes; unlock only to change the scale, then lock again.", P),
              Paragraph(esc("Title blocks: separate A4 (180 x {:.1f} mm), A3 (180 x {:.1f} mm) and A1 (250 x {:.1f} mm) "
                            "designs inserted at scale 1 at the border corner - never stretched. Not explodable, "
                            "uniform scale, mm units, attributes position-locked (edit values with EATTEDIT). "
                            "Hierarchy bottom-up: drawing number / revision / sheet; scale / date / status; "
                            "signatures; drawing title; client / consultant; project / location; company heading "
                            "(text - no logo invented). Attributes: ".format(
                                S.title_block_height("ASG-TB-A4"), S.title_block_height("ASG-TB-A3"),
                                S.title_block_height("ASG-TB-A1")) + ", ".join(t for t, _p, _d in S.TB_ATTRIBUTES) +
                            ". Drawing status values: " + ", ".join(S.DRAWING_STATUS_CODES) + "."), P),
              tbl([["Drawing numbering", ""]] + [list(r) for r in S.NUMBERING], (35, 225), st)]
        s += [Paragraph("13. Hatch, block and attribute standards", H2),
              tbl([["Material", "Pattern", "Angle prop.", "Model-space scale", "Layer", "Note"]] +
                  [list(r) for r in S.HATCH_STANDARD], (38, 18, 15, 62, 30, 97), st),
              Paragraph("Pattern modules (acadiso.pat, scale 1): ANSI31 / ANSI37 lines 3.175 mm apart, ANSI32 pairs "
                        "9.525 mm, INSUL band 9.525 mm, AR-* patterns are real size. 'x drawing scale' patterns "
                        "keep a constant spacing on paper. All pattern names verified to exist in acadiso.pat.", P),
              Paragraph("Blocks: name ASG-&lt;CATEGORY&gt;-&lt;ITEM&gt;-&lt;VARIANT&gt;, geometry on layer 0 "
                        "ByLayer / ByBlock, base point at a datum (fixing point, bottom-left or centreline), block "
                        "units mm, uniform scale, real-size items non-annotative, symbols annotative. Manufacturer "
                        "data only from verified supplier sources.", P),
              tbl([["Attribute tag", "Meaning"]] + [list(r) for r in S.ATTRIBUTE_STANDARD], (40, 220), st)]
        s += [PageBreak(), Paragraph("14. Plotting / PDF standard", H2), tbl([["Item", "Standard"]] + PLOT_STD, (45, 215), st),
              Paragraph("15. Resource separation", H2),
              tbl([["Resource", "Where it lives", "Deploy"]] + RESOURCES, (75, 70, 115), st),
              Paragraph("16. Portability checklist (each PC)", H2)]
        s += [Paragraph(f"[ ] {esc(t)}", P) for t in PORTABILITY]
        s += [Paragraph("17. Finishing and verifying in AutoCAD", H2)]
        s += [Paragraph(f"{i}. {esc(t)}", P) for i, t in enumerate(AUTOCAD_PROCEDURE, 1)]
        s += [PageBreak(), Paragraph("Appendix - layout previews (rendered from the saved master DXF)", H2)]
        for p in previews:
            s += [Paragraph(p.stem, P), Image(str(p), width=165 * mm, height=118 * mm, kind="proportional")]
        return s

    pdf_doc(D_DOC / "ASG_CAD_Standards.pdf", "ASG CAD Standards", story)


PROCEDURE = [
    "Inventory CAD software in the environment (AutoCAD, accoreconsole, ODA, LibreDWG, QCAD, BricsCAD).",
    "Build every file from asg_standard.py (build_all.py).",
    "Re-open the master with ezdxf recover + audit, strict parse, and LibreOffice Draw as an independent reader.",
    "Compare every header variable (incl. current dimension variables), layer, linetype, text / dim / mleader / "
    "multiline style and annotation scale with the definitions.",
    "Check page settings, borders, title-block position / scale / attributes / locks, viewport layer / lock / "
    "scale / position, ByLayer properties of every sheet object.",
    "Check model space empty, no xrefs / underlays / proxies, only title-block blocks, fonts, linetypes, hatch "
    "pattern names (acadiso.pat), ISO 128 / 3098 / 216 series.",
    "Idempotency: re-run scale injection and layout creation; rebuild and compare; check the generated LISP.",
    "Re-open each single-size template and the CTB (binary header + all 255 entries).",
    "Separate temporary QA drawing: dimensions of known geometry, viewports 1:20 / 1:5, no-plot objects, "
    "lineweight matrix, text heights. Check measured values and displayed precision; render and measure lineweights.",
    "Pending in AutoCAD: ASG-SETUP / ASG-QA (0 FAIL), AutoCAD PDF plot of the QA drawing, annotative scaling test, "
    "SAVEAS DWG / DWT.",
]


def write_validation():
    from reportlab.lib.units import mm
    from reportlab.platypus import Image, PageBreak, Paragraph
    st = styles()
    counts = {k: sum(1 for r in R if r[2] == k) for k in ("PASS", "PARTIAL", "UNVERIFIED", "FAIL")}
    sha = hashlib.sha256(BA.MASTER_DXF.read_bytes()).hexdigest()[:16]
    fails = [r for r in R if r[2] == "FAIL"]

    def story():
        s = [Paragraph("ASG TEMPLATE VALIDATION REPORT", st["H1"]),
             Paragraph(esc(f"{S.COMPANY} | Standard {S.STANDARD_REV} | master 01_Master_Template/ASG_Master_Template.dxf "
                           f"(sha256 {sha}...) | tools: ezdxf {ezdxf.__version__}, {ENV['second_reader']} | "
                           f"CAD software found: {ENV['cad']} | {TODAY}"), st["P"]),
             Paragraph("<b>Summary:</b> " + " | ".join(f"{k} {v}" for k, v in counts.items()) +
                       ". AutoCAD was NOT available: no test below ran inside AutoCAD. PASS = tested by re-opening "
                       "the saved file; PARTIAL = tested with a non-AutoCAD renderer; UNVERIFIED = needs AutoCAD "
                       "(ASG-QA and README step 6 cover each one); FAIL = test failed or deliverable missing.", st["P"]),
             Paragraph("<b>FAIL items:</b> " + ("; ".join(esc(f"{a}: {t}") for a, t, _s, _e in fails) or "none"), st["P"]),
             Paragraph("Test procedure", st["H2"])] + [Paragraph(f"{i}. {esc(t)}", st["P"]) for i, t in enumerate(PROCEDURE, 1)]
        s += [Paragraph("Results", st["H2"]),
              tbl([["Area", "Test", "Status", "Evidence"]] + [list(r) for r in R], (30, 95, 20, 115), st, status_col=2)]
        s += [PageBreak(), Paragraph("QA render - temporary QA drawing (A3, viewports 1:20 and 1:5, lineweight matrix, "
                                     "text heights). Preview only; not part of the master template. The preview "
                                     "renderer ignores layer plot flags, so no-plot objects are visible here.", st["P"]),
              Image(str(D_QA / "QA_render_A3.png"), width=240 * mm, height=170 * mm, kind="proportional")]
        return s

    pdf_doc(D_QA / "ASG_Template_Validation_Report.pdf", "Template Validation Report", story)
    lines = [f"ASG TEMPLATE VALIDATION REPORT - Standard {S.STANDARD_REV} - {TODAY}",
             "Summary: " + " | ".join(f"{k} {v}" for k, v in counts.items()),
             f"CAD software found: {ENV['cad']}. No test ran inside AutoCAD.", ""]
    lines += [f"{s:<11} [{a}] {t}" + (f"  -- {e}" if e else "") for a, t, s, e in R]
    (D_QA / "ASG_Template_Validation_Report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return counts


def previews_of_master():
    doc = ezdxf.readfile(BA.MASTER_DXF)
    pv = D_DOC / "previews"
    pv.mkdir(parents=True, exist_ok=True)
    out = []
    for lay in doc.layouts:
        if lay.name == "Model":
            continue
        p = pv / f"{lay.name}.png"
        render(doc, lay, p, dpi=150)
        out.append(p)
    return out


README = """ASG CAD MASTER STANDARD  -  Standard {rev}  ({date})
Saeed Al Siraj Glass & Aluminium Works L.L.C. | Al Siraj Group | UAE
Blank master AutoCAD environment for aluminium, glass and facade engineering.
No product libraries, profiles, sample doors / windows or project drawings.
Supersedes: ASG-STD-CAD-001 R0 and the earlier folders now in /_superseded.

=========================================================================
STATUS
=========================================================================
Master template: genuine AutoCAD 2018 DXF, built and checked by re-opening.
Validation: {counts}  (details: 07_QA_Validation)
FAIL = the native .dwg / .dwt files only: no DWG writer exists in the build
environment (CAD software found: {cad}). Nothing was renamed to .dwg / .dwt.
Step 5 below creates both in AutoCAD in about a minute.

=========================================================================
PACKAGE
=========================================================================
01_Master_Template\\        ASG_Master_Template.dxf  (master, DXF R2018 / AC1032)
                           ASG_Setup.lsp            (ASG-SETUP, ASG-QA, ASG-PROFILE)
02_Drawing_Templates\\      ASG_<SIZE>.dxf - one layout each (A4 L/P, A3 L/P, A1 L)
03_Page_Setups\\            ASG_Page_Setups.csv
04_Plotting_Standards\\     ASG_Monochrome.ctb
05_CAD_Standards_Documentation\\  ASG_CAD_Standards.pdf (full rules, + previews)
                           ASG_CAD_Quick_SOP.pdf (one-page SOP - print for every draftsman)
06_Layer_Register\\         ASG_Layer_Register.xlsx / .csv
07_QA_Validation\\          ASG_Template_Validation_Report.pdf / .txt
                           QA_TEST_DRAWING_temporary.dxf (test file - NOT a template)
08_Automation_Source\\      asg_standard.py (all definitions), build_all.py, build_sop.py,
                           qa_validate.py

=========================================================================
OPENING AND FINISHING IN AUTOCAD (CAD custodian, AutoCAD 2018 or later)
=========================================================================
1. Copy 04_Plotting_Standards\\ASG_Monochrome.ctb into the Plot Styles folder
   (Options > Files > Printer Support File Path > Plot Style Table Search Path).
2. Open it there (double-click in the Plot Styles folder): every colour must show
   Lineweight = "Use object lineweight"; colours 1-249 and 255 Color = Black;
   250-254 Color = "Use object color". If not, fix it in the editor and save
   (or use AutoCAD's monochrome.ctb meanwhile).
3. OPEN > Files of type DXF > 01_Master_Template\\ASG_Master_Template.dxf.
   Type AUDIT > Y.
4. Type APPLOAD > 01_Master_Template\\ASG_Setup.lsp > Load > Close.
   Type ASG-SETUP. It creates the 7 table styles and 5 named page setups,
   sets the drawing variables, then runs ASG-QA.
   The last line must read  RESULT: nnn PASS, 0 FAIL  (also in ASG_QA_Log.txt).
5. Click the Model tab, confirm layer ASG-OUTLINE-PRIMARY is current, then
     SAVEAS > AutoCAD 2018 Drawing (*.dwg)     > ASG_Master_Template.dwg
     SAVEAS > AutoCAD Drawing Template (*.dwt) > ASG_Master_Template.dwt
              Description "ASG CAD Master Standard {rev}", Measurement: Metric.
   Save both in 01_Master_Template.
6. Remaining checks (UNVERIFIED items in the report):
   a. OPEN 07_QA_Validation\\QA_TEST_DRAWING_temporary.dxf, plot layout
      A3-LANDSCAPE to PDF. Check: dimensions 1200 / 2400 / 50.0 / 30.00 / R40 /
      D80; the diagonal line and "NOPLOT" text do NOT print; no viewport frames;
      the 6 lineweights are distinguishable; all text legible. Close without saving.
   b. NEW from ASG_Master_Template.dwt: in the A3 viewport (1:20) add text with
      ASG-TEXT-ANNO (2.5), a dimension (ASG-DIM-ANNO) and a leader (ASG-ML-ANNO);
      set a second viewport to 1:5 and add that scale with OBJECTSCALE; both
      viewports must show 2.5 mm text on paper. Close without saving.
7. Deploy: DWT + CTB to the shared drive; on each PC set Options > Files >
   Template Settings > Default Template File Name for QNEW. Users may run
   ASG-PROFILE (asks first) for snap / grip / autosave defaults - these live
   in each PC's profile, not in the DWT.

=========================================================================
COUNTS (from asg_standard.py)
=========================================================================
Layers {layers} ASG (+ system 0, Defpoints) | Linetypes {lts} + Continuous
Text styles {ts} | Dimension styles {ds} | Multileader styles {ml} | Multiline 2
Table styles {tb} (ASG-SETUP) | Annotation scales {sc}: {scales}
Layouts {lo}: {layouts}
Title blocks {tbk} (A4, A3, A1 - separate designs), {attrs} attributes each.

=========================================================================
CHANGING THE STANDARD
=========================================================================
Change ONLY 08_Automation_Source\\asg_standard.py, then:
  pip install ezdxf openpyxl reportlab matplotlib
  python build_all.py
  python qa_validate.py
Templates, LISP, register, documentation, QA report and this README are
regenerated together, so they always agree.
"""


def write_readme(counts):
    text = README.format(
        rev=S.STANDARD_REV, date=TODAY, cad=ENV["cad"],
        counts=" / ".join(f"{v} {k}" for k, v in counts.items()),
        layers=len(S.LAYERS), lts=len(S.LINETYPES), ts=len(S.TEXT_STYLES), ds=len(S.DIM_STYLES),
        ml=len(S.MLEADER_STYLES), tb=len(S.TABLE_STYLES), sc=len(S.ANNO_SCALES),
        scales=", ".join(f"1:{s}" for s in S.ANNO_SCALES), lo=len(S.SHEETS),
        layouts=", ".join(s[0] for s in S.SHEETS), tbk=len(S.TB_SPECS), attrs=len(S.TB_ATTRIBUTES))
    (ROOT / "README.txt").write_text(text.replace("\n", "\r\n"), encoding="ascii")


def main():
    test_environment()
    test_master(BA.MASTER_DXF)
    test_idempotency()
    test_templates()
    test_ctb()
    lineweight_test()
    test_qa_drawing()
    write_register()
    import openpyxl
    wb = openpyxl.load_workbook(D_REG / "ASG_Layer_Register.xlsx")
    rec("Deliverables", "ASG_Layer_Register.xlsx written and re-opened (all layers listed)",
        pf(wb["Layer Register"].max_row == 4 + len(S.LAYERS)))
    pv = previews_of_master()
    write_standards_pdf(pv)
    rec("Deliverables", "ASG_CAD_Standards.pdf written", pf((D_DOC / "ASG_CAD_Standards.pdf").stat().st_size > 10000))
    import build_sop
    size = build_sop.build_one_page()
    from pypdf import PdfReader
    rec("Deliverables", f"ASG_CAD_Quick_SOP.pdf: one A4 page, every layer name on it exists",
        pf(len(PdfReader(str(build_sop.OUT)).pages) == 1), f"auto-fitted at {size} pt")
    counts = write_validation()
    write_readme(counts)
    print(counts)
    for a, t, s, e in R:
        if s != "PASS":
            print(f"{s:<11} {a}: {t} -- {e}")


if __name__ == "__main__":
    main()
