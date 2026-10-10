ASG CAD MASTER STANDARD  -  Standard R1  (10.10.2026)
Saeed Al Siraj Glass & Aluminium Works L.L.C. | Al Siraj Group | UAE

=========================================================================
START HERE  ->  open 00_START_HERE.pdf  (2 pages, with pictures)
=========================================================================

INSTALL - CAD IN-CHARGE (once, 2 minutes)
  1. Extract this zip (right-click > Extract All). Do not run it from inside the zip.
  2. Double-click  01_Master_Template\ASG_Master_Template.dxf  (opens in AutoCAD).
  3. Drag  01_Master_Template\ASG_Install.lsp  into the AutoCAD window.
     If AutoCAD asks, click "Load Once".
  -> A window says  ASG INSTALL COMPLETE.  Done:
     - print setting installed, template saved, Ctrl+N uses it,
     - folder 09_Team_Kit is ready to share with your team.
  If a step says NOT DONE, the window tells you exactly what to do by hand.

INSTALL - EACH TEAM MEMBER (once per PC, 1 minute)
  1. Copy the folder 09_Team_Kit to the PC (or open it on the shared drive).
  2. Open AutoCAD and drag  ASG_Install.lsp  from the kit into the window.
  3. Select  ASG_Master_Template.dwt  from the kit when asked.
  -> ASG INSTALL COMPLETE. Press Ctrl+N.

EVERY NEW DRAWING
  Ctrl+N - draw 1:1 in mm on ASG layers - pick a sheet tab - set the viewport
  scale and lock it - double-click the title strip and fill it - Ctrl+P.
  Rules on one page: 05_CAD_Standards_Documentation\ASG_CAD_Quick_SOP.pdf

=========================================================================
WHAT IS IN THE PACKAGE
=========================================================================
00_START_HERE.pdf              picture guide (install + daily use)
01_Master_Template\           ASG_Master_Template.dxf + ASG_Install.lsp
02_Drawing_Templates\         one-sheet templates (A4 L/P, A3 L/P, A1 L)
03_Page_Setups\               page setup list
04_Plotting_Standards\        ASG_Monochrome.ctb (print setting)
05_CAD_Standards_Documentation\  full rules (PDF) + one-page SOP
06_Layer_Register\            all layers (Excel)
07_QA_Validation\             test report (167 PASS / 1 PARTIAL / 19 UNVERIFIED / 2 FAIL)
08_Automation_Source\         source - change the standard here only
09_Team_Kit\                  share this folder with the team

Template: 34 layers, 6 text styles, 6 dimension styles, 4 leader
styles, 7 table styles, 8 annotation scales, 5 sheets (A4-LANDSCAPE, A4-PORTRAIT, A3-LANDSCAPE, A3-PORTRAIT, A1-LANDSCAPE),
5 professional title blocks with 35 fields (key plan, approval stamp,
notes, 5-row revision table, project data, signatures, drawing number).

=========================================================================
GOOD TO KNOW
=========================================================================
- The .dwg / .dwt files are made by the installer inside AutoCAD (this
  package was built without AutoCAD; nothing was renamed to look like DWG).
- Problems: send ASG_QA_Log.txt (next to the template) to the CAD in-charge.
- To change the standard: edit 08_Automation_Source\asg_standard.py, then
  run  python build_all.py  and  python qa_validate.py  - every file,
  document and test is regenerated together.
