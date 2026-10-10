;;; ASG_Template_Setup.lsp
;;; Saeed Al Siraj Glass & Aluminium Works L.L.C. - ASG Master Template
;;;
;;; Commands:
;;;   ASG-TABLESTYLES  creates / updates ASG-TABLE-STANDARD, -MATERIAL,
;;;                    -REVISION, -NOTES in the current drawing (run once in
;;;                    ASG_Master_Template before saving the DWT).
;;;   ASG-PROFILE      OPTIONAL. Sets recommended machine/profile variables
;;;                    for the current user. Changes the user's AutoCAD
;;;                    profile - run only if you want these settings.
;;;
;;; STATUS: UNVERIFIED - written without access to AutoCAD. Check the result
;;; in TABLESTYLE after running.

(vl-load-com)

(defun asg:color (aci / c)
  (setq c (vla-GetInterfaceObject (vlax-get-acad-object)
            (strcat "AutoCAD.AcCmColor." (substr (getvar "ACADVER") 1 2))))
  (vla-put-ColorIndex c aci)
  c)

;; title header data : (height align) ; align 1=TopLeft 4=MiddleLeft 5=MiddleCenter
(defun asg:tablestyle (name desc tH tA tSup hH hA hSup dH dA / doc dict ts)
  (setq doc  (vla-get-ActiveDocument (vlax-get-acad-object))
        dict (vla-Item (vla-get-Dictionaries doc) "ACAD_TABLESTYLE"))
  (setq ts (vl-catch-all-apply 'vla-Item (list dict name)))
  (if (vl-catch-all-error-p ts)
    (setq ts (vla-AddObject dict name "AcDbTableStyle")))
  (vla-put-Description ts desc)
  (vla-put-FlowDirection ts 0)            ; top to bottom
  (vla-put-HorzCellMargin ts 1.5)
  (vla-put-VertCellMargin ts 1.0)
  (vla-put-TitleSuppressed ts (if tSup :vlax-true :vlax-false))
  (vla-put-HeaderSuppressed ts (if hSup :vlax-true :vlax-false))
  (vla-SetTextStyle ts 7 "ASG-TEXT")      ; 7 = title+header+data
  (vla-SetTextHeight ts 2 tH)             ; title
  (vla-SetTextHeight ts 4 hH)             ; header
  (vla-SetTextHeight ts 1 dH)             ; data
  (vla-SetAlignment ts 2 tA)
  (vla-SetAlignment ts 4 hA)
  (vla-SetAlignment ts 1 dA)
  (vla-SetColor ts 7 (asg:color 0))       ; ByBlock
  (vla-SetBackgroundColorNone ts 3 :vlax-true)  ; title + data: no fill
  (vla-SetBackgroundColorNone ts 4 :vlax-false)
  (vla-SetBackgroundColor ts 4 (asg:color 254)) ; header light grey
  (vla-SetGridLineWeight ts 18 7 18)      ; inside grid 0.18 (horz+vert inside)
  (vla-SetGridLineWeight ts 45 7 35)      ; outline 0.35 (top bottom left right)
  (princ (strcat "\n  " name " ok"))
  ts)

(defun c:ASG-TABLESTYLES ()
  (asg:tablestyle "ASG-TABLE-STANDARD" "General tables / drawing register"
                  3.5 5 nil 2.5 5 nil 2.5 4)
  (asg:tablestyle "ASG-TABLE-MATERIAL" "Material / glass / hardware schedules"
                  3.5 5 nil 2.0 5 nil 2.0 4)
  (asg:tablestyle "ASG-TABLE-REVISION" "Revision history: Rev, Date, Description, By"
                  3.5 5 T 2.0 5 nil 2.0 4)
  (asg:tablestyle "ASG-TABLE-NOTES" "General notes"
                  3.5 4 nil 2.5 4 T 2.5 1)
  (setvar "CTABLESTYLE" "ASG-TABLE-STANDARD")
  (princ "\nASG table styles created. Save the drawing.")
  (princ))

(defun c:ASG-PROFILE ()
  (initget "Yes No")
  (if (= (getkword "\nChange YOUR AutoCAD profile settings to ASG defaults? [Yes/No] <No>: ") "Yes")
    (progn
      (foreach p '(("OSMODE" 2223) ("AUTOSNAP" 63) ("POLARANG" 45.0) ("DYNMODE" 3)
                   ("DYNPROMPT" 1) ("SELECTIONCYCLING" 2) ("GRIPS" 1) ("GRIPSIZE" 5)
                   ("PICKBOX" 4) ("APERTURE" 8) ("PICKFIRST" 1) ("PICKADD" 2)
                   ("MSLTSCALE" 1) ("ANNOAUTOSCALE" 0) ("SAVETIME" 10) ("ISAVEBAK" 1)
                   ("LAYOUTREGENCTL" 2) ("REFPATHTYPE" 1))
        (vl-catch-all-apply 'setvar p))
      (vl-catch-all-apply 'setvar '("HPLAYER" "ASG-HATCH"))
      (vl-catch-all-apply 'setvar '("DIMLAYER" "ASG-DIMENSION"))
      (princ "\nASG profile settings applied."))
    (princ "\nNo changes made."))
  (princ))

(princ "\nASG_Template_Setup loaded: ASG-TABLESTYLES, ASG-PROFILE (optional).")
(princ)
