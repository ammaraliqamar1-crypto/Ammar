# Al Siraj CAD Shop Drawing Standard – CAD Files

Built from **ASG-STD-CAD-001 Rev 0** (CAD Shop Drawing Standard).

## Files (`output/`)

| File | Use |
|---|---|
| `AlSiraj_ShopDrawing_Template.dxf` | Master template. Open in AutoCAD → **Save As → AutoCAD Drawing Template (.dwt)** → name `AlSiraj_ShopDrawing.dwt`. |
| `AlSiraj_ShopDrawing.ctb` | Plot style table – all 255 colours plot **black**, lineweight/linetype = object, screening 100. Copy to the Plot Styles folder. |
| `AS-2026-000-ALU-SD-001-R0_Sample-W01.dxf` | Worked example: sliding window W-01 – elevation 1:20 + jamb section A-A 1:5, plus `STD-LEGEND` layout (layers, hatches, text, dims). |
| `preview/*.pdf` | Monochrome previews of every layout (as they will plot with the CTB). |

## What is inside the template

- **Units** mm, decimal; LWDISPLAY 1, LTSCALE 1, PSLTSCALE 1, OSMODE End/Mid/Cen/Int/Perp, PDMODE 34 / PDSIZE 2.5.
- **31 layers** exactly as Section 3 (colour, lineweight, linetype, description); `A-CONST` and `A-VPORT` set to **No Plot**.
- **Linetypes** CENTER, CENTER2, HIDDEN, HIDDEN2, DASHED, PHANTOM2 (acadiso values).
- **Text styles** STD-TITLE (Arial Bold), STD-SUBTITLE, STD-NOTES, STD-DIM, STD-LABEL – height 0, width 1.0.
- **Dimension styles** (closed filled 2.5, ext. offset 1.5, extend 1.25, gap 1.0, text above/aligned, colours ByLayer, no zero suppression):

  | Style | DIMSCALE | Precision |
  |---|---|---|
  | `AlSiraj-Dim` | 1 (paper space / 1:1) | 0.0 |
  | `AlSiraj-Dim-1-2`, `-1-5`, `-1-10` | 2 / 5 / 10 | 0.0 |
  | `AlSiraj-Dim-1-20`, `-1-50`, `-1-100` | 20 / 50 / 100 | 0 |
  | `AlSiraj-Dim-TOL`, `-TOL-1-2` | 1 / 2 | ±0.5, height 0.7 |

- **Multileader styles** `AlSiraj-MLeader` (+ `-1-2 … -1-100`): straight, max 2 points, closed filled 2.5, landing gap 2 / length 6, MText STD-LABEL 2.0, ByLayer.
- **Layouts / page setups** `AlSiraj-A3-Plot` and `AlSiraj-A1-Plot`: DWG To PDF.pc3, ISO full-bleed sheet, plot scale 1:1, CTB attached, plot object lineweights ON, centred. Border 20 mm left (binding), 10 mm others; general-notes column; one viewport (1:10 on A3, 1:50 on A1) on `A-VPORT`.
- **Blocks**
  - `ASG-TITLEBLOCK` (180 × 111 mm) – all Section 10.1 fields as attributes: company/logo, project, client, title (2 lines), drawing no., rev, scale, date, sheet, size, drawn/checked/approved, 4-row revision table. Edit with `EATTEDIT`.
  - `ASG-SECTION-MARK`, `ASG-REV-DELTA`, `ASG-ITEM-TAG`, `ASG-SEALANT` (sealant symbol, Section 9).

## How to use (daily)

1. `NEW` → choose `AlSiraj_ShopDrawing.dwt`.
2. Draw in Model space 1:1 on the correct layer (never Layer 0).
3. Set dim / mleader style to match the viewport scale (e.g. 1:20 view → `AlSiraj-Dim-1-20` + `AlSiraj-MLeader-1-20`).
4. Text height in model space = plotted height × scale (2.5 mm notes at 1:20 = 50).
5. Hatch scale in model space = Section 9 scale × drawing scale (glass at 1:5 → 0.5 × 5 = 2.5).
6. Fill title block attributes, file name = drawing number + short project name.
7. Plot from the layout with `AlSiraj_ShopDrawing.ctb` → check the PDF before issue (Section 13).

## Notes on interpretation

- Section 3 lists ANSI32 / ANSI31 / ANSI37 as linetypes for MS-HATCH, SS-HATCH, MISC-INSULATION. These are hatch patterns, not linetypes – the layers use **Continuous** and the pattern is set on the hatch.
- Section 9 angles are taken as the **visual** line angle on paper. ANSI patterns are already drawn at 45°, so the AutoCAD hatch angle property is: Glass/MS/Insulation = **0°**, SS = **90°** (lines read 135°).
- Annotative styles are not used in the file; the standard's alternative (DIMSCALE per scale) is applied with one style per scale. Annotative can be switched on later by the CAD custodian if preferred.
- Sample profile geometry is indicative only.

## Regenerate

```bash
pip install ezdxf
python generate_cad_standard.py
```
