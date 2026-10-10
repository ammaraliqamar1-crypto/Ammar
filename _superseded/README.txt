SUPERSEDED - DO NOT USE FOR NEW DRAWINGS
=========================================
These two earlier packages are kept only for history:

  cad-standard/          built to ASG-STD-CAD-001 R0 (layer names ALU-*, GLZ-*, MS-* ...)
  asg-master-template/   first blank master template (layer names ASG-OBJECT ...)

Both are replaced by ../ASG_CAD_MASTER_STANDARD (Standard R1), which has
one consistent layer dictionary, ISO-series lineweights, synchronised
dimension variables, generated AutoCAD setup/QA commands and a full
validation report. Use only ASG_CAD_MASTER_STANDARD.

Known defects in these old packages (fixed in R1, not back-ported):
- current dimension variables in the file header did not match the
  current dimension style (AutoCAD shows "<style overrides>");
- title blocks were explodable and attributes could be dragged;
- lineweight classes 0.30 / 0.35 / 0.40 too close to tell apart on paper.
