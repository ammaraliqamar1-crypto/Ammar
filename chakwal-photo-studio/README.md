# Chakwal Photo Studio – Logo Identity

Logo system for Chakwal Photo Studio, Minhas Book Palace, Pindi Road, Chakwal. Contact: Zaigham Ali, 0316-5549338 / 0336-9145512.

- `brand-presentation.html` – concepts, final logo, colours, type and mockups (signboard, album, watermark, WhatsApp, cards).
- `logo/` – final artwork. All lettering in the SVGs is outlined, so they open in CorelDRAW / Illustrator without fonts.
- `ads/` – advertisement: feed post 1080×1350, WhatsApp status 1080×1920, A4 flyer (PDF for print).
- `cards/` – business card front/back, 3.5×2 in + 0.125 in bleed (PDF for print, PNG at 300 dpi).
- `source/` – generator scripts. Ads/cards: `python3 ad.py ../ads [--photo wedding.jpg]` then `node render.js ../ads`
  (puts a real photo in the arch window). To rebuild, put Marcellus, Jost Medium and Noto Nastaliq Urdu (SemiBold) TTFs in `source/fonts/`
  (`Marcellus.ttf`, `Jost500.ttf`, `Nastaliq600.ttf`), then run `pip install fonttools uharfbuzz && python3 brand.py ../logo`.

| Colour | HEX | Use |
|---|---|---|
| Surma (charcoal) | #26231F | Main colour, signboard, text |
| Malai (ivory) | #F4EDE0 | Backgrounds |
| Sona (muted gold) | #B08D57 | The sun only; gold foil in print |
| Mehndi (maroon) | #6E2B2A | Wedding albums only |
