# Chakwal Photo Studio – Logo Identity

Logo system for Chakwal Photo Studio, Minhas Book Palace, Pindi Road, Chakwal. Contact: Zaigham Ali, 0316-5549338 / 0336-9145512.

- `brand-presentation.html` – concepts, final logo, colours, type and mockups (signboard, album, watermark, WhatsApp, cards).
- `app/Chakwal-Studio-Designer.html` – **Studio Designer app** (single file, works offline). Open it in Chrome/Edge on a
  computer or phone: pick a design, add your own photos (drag to position, zoom), edit names/text in English or Urdu,
  then export PNG / JPG / print-size PDF, print, export everything as a ZIP, or save/open a project file.
  Work is also kept automatically in that browser. Rebuild: `python3 studio_app.py templates && node app_thumbs.js && python3 studio_app.py html OUT`.
- `app/Studio-Designer-Guide-Urdu.pdf` – Urdu user guide for the app (A4, 5 pages); `app/guide/` has the same pages as images for WhatsApp.
- `Chakwal-Photo-Studio-Brand-Kit.zip` – everything below in one file, for sending on WhatsApp / to the printer.
- `dp/` – round profile pictures: badges (charcoal, ivory, mehndi), WhatsApp icon, stamp.
- `illustrations/` – six service illustrations (wedding, baby, family, passport, prints/frames/crystals, drone).
- `social/` – six service posts 1080×1350, seven story-highlight covers, Facebook cover 1640×624.
- `album-covers/` – wedding, baby, family covers, 12×12 in print PDF (sample names; edit `ALBUMS` in `source/kit.py`).
- `signboard/` – 12×3 ft panaflex, vector PDF.
- `stationery/` – A5 bilingual order slip / receipt PDF.
- `logo/` – final artwork. All lettering in the SVGs is outlined, so they open in CorelDRAW / Illustrator without fonts.
- `ads/` – advertisement: feed post 1080×1350, WhatsApp status 1080×1920, A4 flyer (PDF for print).
- `cards/` – business card front/back, 3.5×2 in + 0.125 in bleed (PDF for print, PNG at 300 dpi).
- `source/` – generator scripts. Real photos go in `source/photos/` (see README there); `python3 kit.py ..` then `node kitrender.js ../social` rebuilds the posts. Ads/cards: `python3 ad.py ../ads [--photo wedding.jpg]` then `node render.js ../ads`
  (puts a real photo in the arch window). To rebuild, put Marcellus, Jost Medium and Noto Nastaliq Urdu (SemiBold) TTFs in `source/fonts/`
  (`Marcellus.ttf`, `Jost500.ttf`, `Nastaliq600.ttf`), then run `pip install fonttools uharfbuzz && python3 brand.py ../logo`.

| Colour | HEX | Use |
|---|---|---|
| Surma (charcoal) | #26231F | Main colour, signboard, text |
| Malai (ivory) | #F4EDE0 | Backgrounds |
| Sona (muted gold) | #B08D57 | The sun only; gold foil in print |
| Mehndi (maroon) | #6E2B2A | Wedding albums only |
