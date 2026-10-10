# Chakwal Photo Studio – Logo Identity

Logo system for Chakwal Photo Studio, Pindi Road, Minhas Book Place, Chakwal.

- `brand-presentation.html` – concepts, final logo, colours, type and mockups (signboard, album, watermark, WhatsApp, cards).
- `logo/` – final artwork. All lettering in the SVGs is outlined, so they open in CorelDRAW / Illustrator without fonts.
- `source/` – generator scripts. To rebuild, put Marcellus, Jost Medium and Noto Nastaliq Urdu (SemiBold) TTFs in `source/fonts/`
  (`Marcellus.ttf`, `Jost500.ttf`, `Nastaliq600.ttf`), then run `pip install fonttools uharfbuzz && python3 brand.py ../logo`.

| Colour | HEX | Use |
|---|---|---|
| Surma (charcoal) | #26231F | Main colour, signboard, text |
| Malai (ivory) | #F4EDE0 | Backgrounds |
| Sona (muted gold) | #B08D57 | The sun only; gold foil in print |
| Mehndi (maroon) | #6E2B2A | Wedding albums only |
