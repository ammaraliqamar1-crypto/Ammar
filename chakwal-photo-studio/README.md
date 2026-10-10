# Chakwal Photo Studio – Brand System

Minhas Book Palace, Pindi Road, Chakwal. Contact: Zaigham Ali, 0316-5549338 / 0336-9145512.

**Logo: the "Darwaza camera"** – a clear camera whose top is the arched doorway of a Punjabi home, with the sun
rising over the Potohar ridge inside the lens. Gold is used only for the sun.

| Colour | HEX | Use |
|---|---|---|
| Surma (charcoal) | #26231F | Main colour, signboard, text |
| Malai (ivory) | #F4EDE0 | Backgrounds |
| Sona (muted gold) | #B08D57 | The sun only; gold foil in print |
| Mehndi (maroon) | #6E2B2A | Wedding albums and wedding posts |

## What is here

| Path | Contents |
|---|---|
| `Chakwal-Photo-Studio-Brand-Kit.zip` | Everything below in one file, for WhatsApp or the printer |
| `brand-presentation.html` | Logo, idea, versions, colours, mockups, ads, social kit, print kit |
| `app/Chakwal-Studio-Designer.html` | **Studio Designer app** – one offline file. Open in Chrome/Edge, add your own photos (drag, zoom), edit English/Urdu text, export PNG / JPG / print-size PDF, print, export all as ZIP, save/open projects. Urdu help button inside. |
| `app/Studio-Designer-Guide-Urdu.pdf` | Urdu user guide (A4, 5 pages); `app/guide/` has the pages as images |
| `logo/` | Primary, stacked, bilingual signboard, black, white, mark only, WhatsApp icon, watermarks (SVG + PNG) |
| `dp/` | Round profile badges (charcoal, ivory, mehndi), round WhatsApp icon, stamp |
| `illustrations/` | Six service illustrations, dark and light |
| `social/` | Six service posts 1080×1350, seven highlight covers, Facebook cover 1640×624 |
| `ads/` | Feed post 1080×1350, WhatsApp status 1080×1920, A4 flyer (PDF) |
| `cards/` | Business card front/back, 3.5×2 in + 0.125 in bleed (PDF) |
| `album-covers/` | Wedding, baby, family covers, 12×12 in PDF (sample names – change them in the app) |
| `signboard/` | 12×3 ft panaflex, vector PDF |
| `stationery/` | A5 bilingual order slip / receipt PDF |
| `source/` | Generators and checks (see below) |

All lettering in the SVG and PDF files is converted to outlines, so they open in CorelDRAW / Illustrator without fonts.

## Rebuilding and checking

Put `Marcellus.ttf`, `Jost500.ttf` (Jost Medium) and `Nastaliq600.ttf` (Noto Nastaliq Urdu SemiBold) in
`source/fonts/`, then from `source/`:

```
pip install fonttools uharfbuzz      # plus Node with Playwright for rendering
./build_all.sh                       # rebuilds every file into source/stage, the app, the guide and the presentation
node qa.js stage                     # nothing painted outside any canvas (73 designs)
python3 qa_text.py                   # every text line inside its canvas, no two lines' ink overlapping
```

Real photos for the default posts go in `source/photos/` (see the README there). Day to day, use the app instead.
