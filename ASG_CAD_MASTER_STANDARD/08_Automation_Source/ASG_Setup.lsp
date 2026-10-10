;;; ASG_Setup.lsp - ASG CAD Master Standard R0
;;; Saeed Al Siraj Glass & Aluminium Works L.L.C.
;;;
;;; Completes, inside AutoCAD, the parts of the template a DXF library cannot
;;; write, and checks the result. Every command is idempotent (re-running
;;; updates, never duplicates). Nothing outside the current drawing is
;;; changed except by ASG-PROFILE, which asks first.
;;;
;;;   ASG-SETUP     = ASG-TABLESTYLES + ASG-PAGESETUPS, then ASG-QA
;;;   ASG-TABLESTYLES   7 table styles
;;;   ASG-PAGESETUPS    named page setups ASG-<layout> copied from each layout
;;;   ASG-QA        in-AutoCAD checks written to the command line
;;;   ASG-PROFILE   OPTIONAL user-profile settings (asks for confirmation)
;;;
;;; STATUS: UNVERIFIED - written without access to AutoCAD.

(vl-load-com)
(setq asg:doc (vla-get-ActiveDocument (vlax-get-acad-object)))

(defun asg:item (coll name / r)
  (setq r (vl-catch-all-apply 'vla-Item (list coll name)))
  (if (vl-catch-all-error-p r) nil r))

(defun asg:color (aci / c)
  (setq c (vla-GetInterfaceObject (vlax-get-acad-object)
            (strcat "AutoCAD.AcCmColor." (substr (getvar "ACADVER") 1 2))))
  (vla-put-ColorIndex c aci)
  c)

;; row types: 1 data, 2 title, 4 header ; align: 1 TL, 4 ML, 5 MC
(defun asg:ts (name desc tH tA hH hA dH dA tSup hSup / dict ts)
  (setq dict (vla-Item (vla-get-Dictionaries asg:doc) "ACAD_TABLESTYLE"))
  (or (setq ts (asg:item dict name))
      (setq ts (vla-AddObject dict name "AcDbTableStyle")))
  (vla-put-Description ts desc)
  (vla-put-FlowDirection ts 0)
  (vla-put-HorzCellMargin ts 1.5)
  (vla-put-VertCellMargin ts 1.0)
  (vla-put-TitleSuppressed ts (if tSup :vlax-true :vlax-false))
  (vla-put-HeaderSuppressed ts (if hSup :vlax-true :vlax-false))
  (vla-SetTextStyle ts 7 "ASG-TEXT-SHEET")
  (vla-SetTextHeight ts 2 tH) (vla-SetAlignment ts 2 tA)
  (vla-SetTextHeight ts 4 hH) (vla-SetAlignment ts 4 hA)
  (vla-SetTextHeight ts 1 dH) (vla-SetAlignment ts 1 dA)
  (vla-SetColor ts 7 (asg:color 0))
  (vla-SetBackgroundColorNone ts 3 :vlax-true)
  (vla-SetBackgroundColorNone ts 4 :vlax-false)
  (vla-SetBackgroundColor ts 4 (asg:color 254))
  (vla-SetGridLineWeight ts 18 7 18)   ; inside grid 0.18
  (vla-SetGridLineWeight ts 45 7 35)   ; outline 0.35
  (princ (strcat "\n  table style " name " ok"))
  ts)

(defun c:ASG-TABLESTYLES ()
  (asg:ts "ASG-TABLE-STANDARD" "Standard technical tables" 3.5 5 2.5 5 2.5 4 nil nil)
  (asg:ts "ASG-TABLE-MATERIAL" "Material schedules"        3.5 5 2.0 5 2.0 4 nil nil)
  (asg:ts "ASG-TABLE-GLASS"    "Glass schedules"           3.5 5 2.0 5 2.0 4 nil nil)
  (asg:ts "ASG-TABLE-HARDWARE" "Hardware schedules"        3.5 5 2.0 5 2.0 4 nil nil)
  (asg:ts "ASG-TABLE-REVISION" "Revision registers"        3.5 5 2.0 5 2.0 4 T   nil)
  (asg:ts "ASG-TABLE-REGISTER" "Drawing registers"         3.5 5 2.5 5 2.5 4 nil nil)
  (asg:ts "ASG-TABLE-NOTES"    "General notes"             3.5 4 2.5 4 2.5 1 nil T)
  (setvar "CTABLESTYLE" "ASG-TABLE-STANDARD")
  (princ))

(defun c:ASG-PAGESETUPS (/ pcs name pc)
  (setq pcs (vla-get-PlotConfigurations asg:doc))
  (vlax-for lay (vla-get-Layouts asg:doc)
    (if (= (vla-get-ModelType lay) :vlax-false)
      (progn
        (setq name (strcat "ASG-" (vla-get-Name lay)))
        (or (setq pc (asg:item pcs name))
            (setq pc (vla-Add pcs name :vlax-false)))
        (vla-CopyFrom pc lay)
        (princ (strcat "\n  page setup " name " ok")))))
  (princ))

(defun asg:chk (label ok)
  (princ (strcat "\n  " (if ok "PASS  " "FAIL  ") label)) ok)

(defun c:ASG-QA (/ lays n tsd)
  (princ "\nASG-QA ----------------------------------------------")
  (asg:chk "INSUNITS = 4 (mm)" (= (getvar "INSUNITS") 4))
  (asg:chk "LUNITS = 2, LUPREC = 0" (and (= (getvar "LUNITS") 2) (= (getvar "LUPREC") 0)))
  (asg:chk "AUNITS = 0, AUPREC = 2" (and (= (getvar "AUNITS") 0) (= (getvar "AUPREC") 2)))
  (asg:chk "MEASUREMENT = 1" (= (getvar "MEASUREMENT") 1))
  (asg:chk "CLAYER = ASG-OUTLINE-PRIMARY" (= (getvar "CLAYER") "ASG-OUTLINE-PRIMARY"))
  (setq n 0)
  (vlax-for l (vla-get-Layers asg:doc) (if (wcmatch (vla-get-Name l) "ASG-*") (setq n (1+ n))))
  (asg:chk (strcat "ASG layers = 34 (found " (itoa n) ")") (= n 34))
  (foreach s '("ASG-TEXT-ANNO" "ASG-TEXT-NOTE" "ASG-TEXT-SMALL" "ASG-TEXT-TITLE"
               "ASG-TEXT-HEADING" "ASG-TEXT-SHEET")
    (asg:chk (strcat "text style " s) (tblsearch "STYLE" s)))
  (foreach s '("ASG-DIM-ANNO" "ASG-DIM-FIXED" "ASG-DIM-DETAIL" "ASG-DIM-ANGULAR"
               "ASG-DIM-RADIUS" "ASG-DIM-DIAMETER")
    (asg:chk (strcat "dim style " s) (tblsearch "DIMSTYLE" s)))
  (foreach s '("ASG-ML-ANNO" "ASG-ML-NOTE" "ASG-ML-DETAIL" "ASG-ML-REFERENCE")
    (asg:chk (strcat "mleader style " s) (dictsearch (cdr (assoc -1 (dictsearch (namedobjdict) "ACAD_MLEADERSTYLE"))) s)))
  (setq tsd (cdr (assoc -1 (dictsearch (namedobjdict) "ACAD_TABLESTYLE"))))
  (foreach s '("ASG-TABLE-STANDARD" "ASG-TABLE-MATERIAL" "ASG-TABLE-GLASS" "ASG-TABLE-HARDWARE"
               "ASG-TABLE-REVISION" "ASG-TABLE-REGISTER" "ASG-TABLE-NOTES")
    (asg:chk (strcat "table style " s) (dictsearch tsd s)))
  (foreach s '("1:1" "1:2" "1:5" "1:10" "1:20" "1:25" "1:50" "1:100")
    (asg:chk (strcat "annotation scale " s)
             (vl-some '(lambda (e) (= (cdr (assoc 300 (entget (cdr e)))) s))
                      (vl-remove-if-not '(lambda (x) (= (car x) 350))
                        (dictsearch (namedobjdict) "ACAD_SCALELIST")))))
  (setq lays (layoutlist))
  (foreach s '("A4-LANDSCAPE" "A4-PORTRAIT" "A3-LANDSCAPE" "A3-PORTRAIT" "A1-LANDSCAPE")
    (asg:chk (strcat "layout " s) (member s lays)))
  (asg:chk "model space empty" (null (ssget "_X" '((410 . "Model")))))
  (princ "\n------------------------------------------------------")
  (princ))

(defun c:ASG-SETUP ()
  (c:ASG-TABLESTYLES)
  (c:ASG-PAGESETUPS)
  (c:ASG-QA)
  (princ "\nASG-SETUP complete - review FAIL lines, then SAVEAS DWG / DWT.")
  (princ))

(defun c:ASG-PROFILE ()
  (initget "Yes No")
  (if (= (getkword "\nChange YOUR AutoCAD profile settings to ASG defaults? [Yes/No] <No>: ") "Yes")
    (progn
      (foreach p '(("OSMODE" 2223) ("AUTOSNAP" 63) ("POLARANG" 45.0) ("DYNMODE" 3)
                   ("DYNPROMPT" 1) ("SELECTIONCYCLING" 2) ("GRIPS" 1) ("GRIPSIZE" 5)
                   ("PICKBOX" 4) ("APERTURE" 8) ("PICKFIRST" 1) ("PICKADD" 2)
                   ("MSLTSCALE" 1) ("ANNOAUTOSCALE" 0) ("ANNOALLVISIBLE" 0)
                   ("SAVETIME" 10) ("ISAVEBAK" 1) ("LAYOUTREGENCTL" 2) ("REFPATHTYPE" 1)
                   ("UCSFOLLOW" 0) ("HPLAYER" "ASG-HATCH") ("DIMLAYER" "ASG-DIMENSION"))
        (vl-catch-all-apply 'setvar p))
      (princ "\nASG profile settings applied."))
    (princ "\nNo changes made."))
  (princ))

(princ "\nASG_Setup loaded: ASG-SETUP, ASG-TABLESTYLES, ASG-PAGESETUPS, ASG-QA, ASG-PROFILE.")
(princ)
