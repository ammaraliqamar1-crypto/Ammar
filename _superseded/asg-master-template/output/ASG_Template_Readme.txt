ASG MASTER AUTOCAD TEMPLATE - README
Saeed Al Siraj Glass & Aluminium Works L.L.C. | Al Siraj Group | UAE | Rev 0

-------------------------------------------------------------------------
1. FILES IN THIS FOLDER
-------------------------------------------------------------------------
ASG_Master_Template.dxf    Master blank template, AutoCAD 2018 DXF. All settings below.
ASG_Monochrome.ctb         Plot style table (ACI 1-249,255 black; 250-254 grey; object lineweight).
ASG_Template_Setup.lsp     ASG-TABLESTYLES (table styles) + optional ASG-PROFILE (user settings).
ASG_CAD_Standards.pdf      Settings & standards reference (with layout previews).
ASG_Layer_Standards.xlsx   Layer register (+ lineweight hierarchy sheet).
ASG_Layer_Standards.csv    Same register, CSV.
ASG_Validation_Report.txt  Check-by-check results.
preview\*.png              Monochrome render of every layout.

NOT INCLUDED: ASG_Master_Template.dwg and ASG_Master_Template.dwt.
Reason: the generation environment has no DWG writer (no AutoCAD, ODA File
Converter or RealDWG). Renaming a DXF to .dwg/.dwt is not done - make them in
AutoCAD as in section 2 (about 1 minute).

-------------------------------------------------------------------------
2. ONE-TIME SETUP (CAD custodian)
-------------------------------------------------------------------------
 1. Copy ASG_Monochrome.ctb into the Plot Styles folder
    (Options > Files > Printer Support File Path > Plot Style Table Search Path).
 2. Open ASG_Master_Template.dxf in AutoCAD 2018 or later.
 3. AUDIT  > Y
 4. APPLOAD > ASG_Template_Setup.lsp > Load.  Type  ASG-TABLESTYLES
 5. Check: LAYER, STYLE, DIMSTYLE, MLEADERSTYLE, TABLESTYLE, SCALELISTEDIT,
    each layout's Page Setup (tick items marked PASS* / UNVERIFIED in the report).
 6. Make sure Model tab is active, layer ASG-OBJECT current, ZOOM Extents.
 7. SAVEAS > AutoCAD 2018 Drawing (*.dwg)       > ASG_Master_Template.dwg
 8. SAVEAS > AutoCAD Drawing Template (*.dwt)   > ASG_Master_Template.dwt
    Description: ASG master template | Measurement: Metric
 9. Put the DWT + CTB on the shared drive; set Options > Files > Template
    Settings > Default Template File Name for QNEW = ASG_Master_Template.dwt.
10. (Optional, per user) type ASG-PROFILE to apply snap/grip/autosave defaults.

-------------------------------------------------------------------------
3. WHAT IS IN THE TEMPLATE
-------------------------------------------------------------------------
Units          mm, decimal, 0 dp; angles decimal degrees 0.00; INSUNITS mm; metric.
Layers         33 ASG layers (+ system 0, Defpoints). Current = ASG-OBJECT.
               No-plot: ASG-CONSTRUCTION, ASG-VIEWPORT, ASG-NOPLOT.
Linetypes      Continuous, HIDDEN, HIDDEN2, CENTER, CENTER2, DASHED, DASHED2,
               DASHDOT, DASHDOT2, PHANTOM, PHANTOM2, DOT. LTSCALE 1, PSLTSCALE 1.
Text styles    ASG-TEXT, ASG-TEXT-NOTE, ASG-TEXT-SMALL (annotative),
               ASG-TEXT-TITLE, ASG-TEXT-SHEET (paper space). Font Arial.
Dim styles     ASG-DIM-ANNOTATIVE, ASG-DIM-1-1, -1-2, -1-5, -1-10, -1-20, -1-50.
MLeader        ASG-ML-ANNOTATIVE, ASG-ML-NOTE, ASG-ML-DETAIL.
Multiline      ASG-MLINE-2, ASG-MLINE-3.
Anno. scales   1:1 1:2 1:5 1:10 1:20 1:25 1:50 1:100.
Table styles   via ASG-TABLESTYLES (see step 4).
Layouts        A4-LANDSCAPE, A4-PORTRAIT, A3-LANDSCAPE, A3-PORTRAIT, A1-LANDSCAPE.
               DWG To PDF.pc3, full-bleed ISO paper, 1:1, centred, CTB,
               plot lineweights on, one locked viewport on ASG-VIEWPORT.
Title blocks   ASG-TB-A4, ASG-TB-A3, ASG-TB-A1 (separate designs), 16 attributes:
               PROJECT LOCATION CLIENT CONSULTANT DWG_TITLE DWG_TITLE_2 DWG_NO REV
               DATE DRAWN_BY CHECKED_BY APPROVED_BY SCALE SHEET_NO DWG_STATUS REMARKS
Model space    Empty. No xrefs. No product blocks, no hatches, no schedules.

-------------------------------------------------------------------------
4. DAILY USE
-------------------------------------------------------------------------
- NEW > ASG_Master_Template.dwt. Draw 1:1 in mm on ASG layers, never on 0.
- Model-space notes/dims/leaders: annotative styles; set viewport scale first.
- Fixed-scale dims only when the whole drawing is one scale (ASG-DIM-1-x).
- Delete layouts you do not need; keep one layout per sheet size used.
- Edit title block: double-click it (EATTEDIT).
- Change viewport scale: unlock viewport > set scale > lock.
- Before issue: AUDIT > PURGE > check PDF.
Full details: ASG_CAD_Standards.pdf.

-------------------------------------------------------------------------
5. REGENERATE (developers)
-------------------------------------------------------------------------
pip install ezdxf openpyxl reportlab matplotlib
python build_master_template.py
python validate_and_document.py
