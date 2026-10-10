ASG CAD MASTER STANDARD  -  Standard R1  (10.10.2026)
Saeed Al Siraj Glass & Aluminium Works L.L.C. | Al Siraj Group | UAE
Blank master AutoCAD environment for aluminium, glass and facade engineering.
No product libraries, profiles, sample doors / windows or project drawings.
Supersedes: ASG-STD-CAD-001 R0 and the earlier folders now in /_superseded.

=========================================================================
STATUS
=========================================================================
Master template: genuine AutoCAD 2018 DXF, built and checked by re-opening.
Validation: 150 PASS / 1 PARTIAL / 19 UNVERIFIED / 2 FAIL  (details: 07_QA_Validation)
FAIL = the native .dwg / .dwt files only: no DWG writer exists in the build
environment (CAD software found: none). Nothing was renamed to .dwg / .dwt.
Step 5 below creates both in AutoCAD in about a minute.

=========================================================================
PACKAGE
=========================================================================
01_Master_Template\        ASG_Master_Template.dxf  (master, DXF R2018 / AC1032)
                           ASG_Setup.lsp            (ASG-SETUP, ASG-QA, ASG-PROFILE)
02_Drawing_Templates\      ASG_<SIZE>.dxf - one layout each (A4 L/P, A3 L/P, A1 L)
03_Page_Setups\            ASG_Page_Setups.csv
04_Plotting_Standards\     ASG_Monochrome.ctb
05_CAD_Standards_Documentation\  ASG_CAD_Standards.pdf (+ previews)
06_Layer_Register\         ASG_Layer_Register.xlsx / .csv
07_QA_Validation\          ASG_Template_Validation_Report.pdf / .txt
                           QA_TEST_DRAWING_temporary.dxf (test file - NOT a template)
08_Automation_Source\      asg_standard.py (all definitions), build_all.py, qa_validate.py

=========================================================================
OPENING AND FINISHING IN AUTOCAD (CAD custodian, AutoCAD 2018 or later)
=========================================================================
1. Copy 04_Plotting_Standards\ASG_Monochrome.ctb into the Plot Styles folder
   (Options > Files > Printer Support File Path > Plot Style Table Search Path).
2. Open it there (double-click in the Plot Styles folder): every colour must show
   Lineweight = "Use object lineweight"; colours 1-249 and 255 Color = Black;
   250-254 Color = "Use object color". If not, fix it in the editor and save
   (or use AutoCAD's monochrome.ctb meanwhile).
3. OPEN > Files of type DXF > 01_Master_Template\ASG_Master_Template.dxf.
   Type AUDIT > Y.
4. Type APPLOAD > 01_Master_Template\ASG_Setup.lsp > Load > Close.
   Type ASG-SETUP. It creates the 7 table styles and 5 named page setups,
   sets the drawing variables, then runs ASG-QA.
   The last line must read  RESULT: nnn PASS, 0 FAIL  (also in ASG_QA_Log.txt).
5. Click the Model tab, confirm layer ASG-OUTLINE-PRIMARY is current, then
     SAVEAS > AutoCAD 2018 Drawing (*.dwg)     > ASG_Master_Template.dwg
     SAVEAS > AutoCAD Drawing Template (*.dwt) > ASG_Master_Template.dwt
              Description "ASG CAD Master Standard R1", Measurement: Metric.
   Save both in 01_Master_Template.
6. Remaining checks (UNVERIFIED items in the report):
   a. OPEN 07_QA_Validation\QA_TEST_DRAWING_temporary.dxf, plot layout
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
Layers 34 ASG (+ system 0, Defpoints) | Linetypes 11 + Continuous
Text styles 6 | Dimension styles 6 | Multileader styles 4 | Multiline 2
Table styles 7 (ASG-SETUP) | Annotation scales 8: 1:1, 1:2, 1:5, 1:10, 1:20, 1:25, 1:50, 1:100
Layouts 5: A4-LANDSCAPE, A4-PORTRAIT, A3-LANDSCAPE, A3-PORTRAIT, A1-LANDSCAPE
Title blocks 3 (A4, A3, A1 - separate designs), 15 attributes each.

=========================================================================
CHANGING THE STANDARD
=========================================================================
Change ONLY 08_Automation_Source\asg_standard.py, then:
  pip install ezdxf openpyxl reportlab matplotlib
  python build_all.py
  python qa_validate.py
Templates, LISP, register, documentation, QA report and this README are
regenerated together, so they always agree.
