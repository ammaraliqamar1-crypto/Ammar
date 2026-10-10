ASG CAD MASTER STANDARD  -  Standard R0
Saeed Al Siraj Glass & Aluminium Works L.L.C. | Al Siraj Group | UAE
Blank master AutoCAD environment for aluminium, glass and facade engineering.
No product libraries, profiles, sample doors/windows or project drawings.

=========================================================================
STATUS IN ONE LINE
=========================================================================
Master template exists as a genuine AutoCAD 2018 DXF and passed initial QA
(130 PASS / 1 PARTIAL / 13 UNVERIFIED / 3 FAIL). The 3 FAILs are the missing
native DWG/DWT files: no DWG writer exists in the build environment (no
AutoCAD, accoreconsole, ODA File Converter, LibreDWG, QCAD or BricsCAD).
Nothing was renamed to .dwg/.dwt. Step 4 below creates them in about a minute.

=========================================================================
PACKAGE
=========================================================================
01_Master_Template\      ASG_Master_Template.dxf  (master - DXF R2018/AC1032)
                         ASG_Setup.lsp            (finishing + QA commands)
02_Drawing_Templates\    ASG_A4-LANDSCAPE.dxf ... ASG_A1-LANDSCAPE.dxf (one layout each)
03_Page_Setups\          ASG_Page_Setups.csv      (page setup definitions)
04_Plotting_Standards\   ASG_Monochrome.ctb
05_CAD_Standards_Documentation\  ASG_CAD_Standards.pdf (+ layout previews)
06_Layer_Register\       ASG_Layer_Register.xlsx / .csv
07_QA_Validation\        ASG_Template_Validation_Report.pdf / .txt
                         QA_TEST_DRAWING_temporary.dxf  (separate test file - NOT a template)
                         QA_render_A3.pdf/.png, QA_lineweight_matrix.png
08_Automation_Source\    asg_standard.py (single source of truth), build_all.py,
                         qa_validate.py, ASG_Setup.lsp

=========================================================================
EXACT OPENING / FINISHING PROCEDURE (CAD custodian, AutoCAD 2018 or later)
=========================================================================
1. Copy 04_Plotting_Standards\ASG_Monochrome.ctb to the Plot Styles folder
   (Options > Files > Printer Support File Path > Plot Style Table Search Path).
2. AutoCAD > OPEN > Files of type: DXF (*.dxf) >
   01_Master_Template\ASG_Master_Template.dxf.   Then: AUDIT > Y.
3. APPLOAD > 01_Master_Template\ASG_Setup.lsp > Load. Type:  ASG-SETUP
   - creates 7 table styles and named page setups ASG-<layout>
   - runs ASG-QA: every line must read PASS.
4. Click the Model tab, ZOOM > Extents, confirm layer ASG-OUTLINE-PRIMARY current, then
     SAVEAS > AutoCAD 2018 Drawing (*.dwg)          > ASG_Master_Template.dwg
     SAVEAS > AutoCAD Drawing Template (*.dwt)      > ASG_Master_Template.dwt
              Description "ASG CAD Master Standard R0", Measurement: Metric.
5. Pending AutoCAD tests (validation report, UNVERIFIED items):
   a. OPEN 07_QA_Validation\QA_TEST_DRAWING_temporary.dxf, plot layout A3-LANDSCAPE
      to PDF with ASG_Monochrome.ctb; check: dims 1200/2400/50.0/30.00/R40/D80,
      the diagonal line and "NOPLOT" text do NOT print, no viewport frames,
      lineweights 0.09-0.50 distinguishable, text heights legible.
   b. In ASG_Master_Template.dwt: draw a test line, set viewport 1:20, add text with
      ASG-TEXT-ANNO (2.5), a dim with ASG-DIM-ANNO and a leader with ASG-ML-ANNO;
      change viewport to 1:5 > add scale via OBJECTSCALE; confirm 2.5 mm on paper.
      Then UNDO back to the blank state (do not save test objects in the template).
6. Deploy: DWT to the shared Templates folder; Options > Files > Template Settings >
   Default Template File Name for QNEW = ASG_Master_Template.dwt on each PC.
7. Optional per user: type ASG-PROFILE (asks before changing that user's
   OSMODE, grips, autosave, etc. - these are NOT stored in DWG/DWT).

=========================================================================
COUNTS
=========================================================================
Layers 34 ASG (+ system 0, Defpoints) | Linetypes 11 + Continuous
Text styles 6 | Dimension styles 6 | Multileader styles 4 | Multiline styles 2
Table styles 7 (created by ASG-SETUP) | Annotation scales 8 (1:1 ... 1:100)
Layouts 5: A4-LANDSCAPE, A4-PORTRAIT, A3-LANDSCAPE, A3-PORTRAIT, A1-LANDSCAPE
Title blocks 3 (ASG-TB-A4, -A3, -A1), 15 attributes each.

=========================================================================
REBUILD (idempotent)
=========================================================================
pip install ezdxf openpyxl reportlab matplotlib
cd 08_Automation_Source
python build_all.py
python qa_validate.py
Change the standard ONLY in asg_standard.py, then rebuild - documentation,
register, templates and QA all follow from it.
