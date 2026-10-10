"""
Builds every generated file of the ASG CAD Master Standard package.
Idempotent: output files are rebuilt from the definitions in asg_standard.py;
nothing outside ASG_CAD_MASTER_STANDARD/ is touched.

    python build_all.py && python qa_validate.py
"""

import csv
import shutil
from pathlib import Path

from ezdxf.math import Vec2

import asg_standard as S

ROOT = Path(__file__).resolve().parent.parent
D_MASTER = ROOT / "01_Master_Template"
D_TEMPL = ROOT / "02_Drawing_Templates"
D_PSETUP = ROOT / "03_Page_Setups"
D_PLOT = ROOT / "04_Plotting_Standards"
D_QA = ROOT / "07_QA_Validation"
SRC = Path(__file__).resolve().parent

MASTER_DXF = D_MASTER / "ASG_Master_Template.dxf"
QA_DXF = D_QA / "QA_TEST_DRAWING_temporary.dxf"


def build_master():
    S.save_dxf(S.new_document(), MASTER_DXF)
    shutil.copy(SRC / "ASG_Setup.lsp", D_MASTER / "ASG_Setup.lsp")


def build_size_templates():
    for sheet in S.SHEETS:
        S.TB_HEIGHTS.clear()
        S.save_dxf(S.new_document(sheets=[sheet]), D_TEMPL / f"ASG_{sheet[0]}.dxf")


def build_page_setup_register():
    D_PSETUP.mkdir(parents=True, exist_ok=True)
    with open(D_PSETUP / "ASG_Page_Setups.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["Page setup / layout", "Plot device", "Paper size (canonical media name)",
                     "Orientation", "Plot area", "Plot scale", "Plot offset", "Plot style table",
                     "Plot lineweights", "Title block", "Default viewport"])
        for name, w, h, paper, tb, vps in S.SHEETS:
            wr.writerow([f"ASG-{name}", S.PLOTTER, f"{paper}_({w:.2f}_x_{h:.2f}_MM)",
                         "Landscape" if w > h else "Portrait", "Layout", "1:1", "Centred",
                         S.CTB_NAME, "Yes (not scaled)", tb, f"1:{vps}, locked, ASG-VIEWPORT"])


def build_ctb():
    S.build_ctb(D_PLOT / S.CTB_NAME)


# ---------------------------------------------------------------------------
# Temporary QA drawing - SEPARATE from the master (never delivered as template)
# ---------------------------------------------------------------------------
QA_LW_Y0 = 250.0  # paper y of first lineweight sample on QA layout
QA_LW_STEP = 9.0
QA_LW_X = (230.0, 300.0)


def build_qa_drawing():
    S.TB_HEIGHTS.clear()
    a3 = [s for s in S.SHEETS if s[0] == "A3-LANDSCAPE"]
    doc = S.new_document(sheets=a3)
    msp = doc.modelspace()
    # 1:20 test geometry - a 1200 x 2400 opening
    msp.add_lwpolyline([(0, 0), (1200, 0), (1200, 2400), (0, 2400)], close=True,
                       dxfattribs={"layer": "ASG-OUTLINE-PRIMARY"})
    d = msp.add_linear_dim(base=(0, -300), p1=(0, 0), p2=(1200, 0), dimstyle="ASG-DIM-FIXED",
                           override={"dimscale": 20}, dxfattribs={"layer": "ASG-DIMENSION"})
    d.render()
    d = msp.add_linear_dim(base=(-300, 0), p1=(0, 0), p2=(0, 2400), angle=90, dimstyle="ASG-DIM-FIXED",
                           override={"dimscale": 20}, dxfattribs={"layer": "ASG-DIMENSION"})
    d.render()
    t = msp.add_text("TEXT 2.5 @1:20", height=2.5 * 20,
                     dxfattribs={"style": "ASG-TEXT-NOTE", "layer": "ASG-TEXT-NOTE"})
    t.set_placement((0, 2550))
    # 1:5 detail geometry at x=5000
    ox = 5000
    msp.add_lwpolyline([(ox, 0), (ox + 50, 0), (ox + 50, 100), (ox, 100)], close=True,
                       dxfattribs={"layer": "ASG-SECTION-CUT"})
    hatch = msp.add_hatch(dxfattribs={"layer": "ASG-HATCH-FILL"})
    hatch.set_solid_fill(color=256)
    hatch.paths.add_polyline_path([(ox, 0), (ox + 50, 0), (ox + 50, 100), (ox, 100)], is_closed=True)
    d = msp.add_linear_dim(base=(ox, -25), p1=(ox, 0), p2=(ox + 50, 0), dimstyle="ASG-DIM-DETAIL",
                           override={"dimscale": 5}, dxfattribs={"layer": "ASG-DIMENSION"})
    d.render()
    # angular 30 deg
    c = Vec2(ox + 150, 0)
    msp.add_line(c, c + Vec2(120, 0), dxfattribs={"layer": "ASG-OUTLINE-SECONDARY"})
    msp.add_line(c, c + Vec2.from_deg_angle(30, 120), dxfattribs={"layer": "ASG-OUTLINE-SECONDARY"})
    d = msp.add_angular_dim_cra(center=c, radius=90, start_angle=0, end_angle=30, distance=0,
                                dimstyle="ASG-DIM-ANGULAR", override={"dimscale": 5},
                                dxfattribs={"layer": "ASG-DIMENSION"})
    d.render()
    # radius / diameter on R40 circle
    cc = (ox + 100, 200)
    msp.add_circle(cc, 40, dxfattribs={"layer": "ASG-OUTLINE-SECONDARY"})
    msp.add_radius_dim(center=cc, radius=40, angle=45, dimstyle="ASG-DIM-RADIUS",
                       override={"dimscale": 5}, dxfattribs={"layer": "ASG-DIMENSION"}).render()
    msp.add_diameter_dim(center=cc, radius=40, angle=200, dimstyle="ASG-DIM-DIAMETER",
                         override={"dimscale": 5}, dxfattribs={"layer": "ASG-DIMENSION"}).render()
    # non-plot objects that must NOT appear in output
    msp.add_line((0, 0), (1200, 2400), dxfattribs={"layer": "ASG-CONSTRUCTION"})
    msp.add_text("NOPLOT", height=100, dxfattribs={"layer": "ASG-NOPLOT"}).set_placement((300, 1200))

    lay = doc.layouts.get("A3-LANDSCAPE")
    # replace default viewport with two test viewports
    for e in list(lay):
        if e.dxftype() == "VIEWPORT" and e.dxf.id != 1:
            lay.delete_entity(e)
    for (x1, y1, x2, y2), scale, ctr in (((25, 15, 125, 282), 20, (450, 1100)),
                                         ((130, 15, 225, 140), 5, (ox + 120, 120))):
        vp = lay.add_viewport(center=((x1 + x2) / 2, (y1 + y2) / 2), size=(x2 - x1, y2 - y1),
                              view_center_point=ctr, view_height=(y2 - y1) * scale,
                              dxfattribs={"layer": "ASG-VIEWPORT"})
        vp.dxf.flags |= 16384
    # lineweight matrix (paper space)
    x1, x2 = QA_LW_X
    for i, (lw, label) in enumerate(S.LW_MATRIX):
        y = QA_LW_Y0 - i * QA_LW_STEP
        layer = next(l[1] for l in S.LAYERS if l[5] == lw and l[6])
        lay.add_line((x1, y), (x2, y), dxfattribs={"layer": layer})
        S._text(lay, f"{lw:.2f}  {layer}", x2 + 3, y - 1, 1.8, "ASG-TEXT-SHEET", "ASG-TEXT")
    # paper text heights
    y = 175
    for use, h, style in S.TEXT_HEIGHTS:
        y -= h + 2.5
        st = style.split(" ")[0]
        S._text(lay, f"{h} mm {use}", 230, y, h, st, "ASG-TEXT")
    QA_DXF.parent.mkdir(parents=True, exist_ok=True)
    S.save_dxf(doc, QA_DXF)


def main():
    build_master()
    build_size_templates()
    build_page_setup_register()
    build_ctb()
    build_qa_drawing()
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and p.suffix in (".dxf", ".ctb", ".csv", ".lsp"):
            print("written", p.relative_to(ROOT))


if __name__ == "__main__":
    main()
