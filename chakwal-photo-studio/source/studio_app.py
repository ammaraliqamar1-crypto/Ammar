"""Builds the Chakwal Studio Designer app.

Step 1: python3 studio_app.py templates   -> build/templates.json (live-text SVG templates)
Step 2: node app_thumbs.js                -> build/thumbs/*.jpg
Step 3: python3 studio_app.py html OUT_DIR -> OUT_DIR/studio-designer.html (standalone)
                                             OUT_DIR/studio-designer-artifact.html (claude.ai page body)
"""
import base64, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")

import ad
ad.LIVE = True
import kit
from brand import SURMA, MALAI, SONA, MEHNDI, BLACK


def strip_size(s):
    return re.sub(r'^<svg([^>]*?) width="[^"]*" height="[^"]*"', r"<svg\1", s, count=1)


def templates():
    T = []

    def add(tid, group, name, ur, svgstr, pdf=None, scale=1):
        vb = svgstr.split('viewBox="0 0 ')[1].split('"')[0].split()
        T.append(dict(id=tid, group=group, name=name, ur=ur, w=float(vb[0]), h=float(vb[1]),
                      pdf=pdf, scale=scale, svg=strip_size(svgstr)))

    names = {"wedding": ("Wedding", "شادی"), "baby": ("Baby shoot", "بچوں کا فوٹو شوٹ"),
             "family": ("Family portrait", "فیملی پورٹریٹ"), "passport": ("Passport & ID", "پاسپورٹ فوٹو"),
             "prints": ("Prints, frames & crystals", "پرنٹ، فریم، کرسٹل"), "drone": ("Drone & movies", "ڈرون کوریج")}
    for p in kit.POSTS:
        n, u = names[p["key"]]
        add(f"post-{p['key']}", "Social posts", n, u, kit.service_post(p))
    add("facebook-cover", "Social posts", "Facebook cover", "فیس بک کور", kit.fb_cover())
    add("ad-post", "Ads", "Ad · feed post", "اشتہار · پوسٹ", ad.ad_post())
    add("ad-status", "Ads", "Ad · WhatsApp status", "اشتہار · اسٹیٹس", ad.ad_tall(1920, None, "s"))
    add("ad-flyer", "Ads", "Ad · A4 flyer", "اشتہار · اے فور فلائر", ad.ad_tall(1527, None, "a"),
        pdf=[210, 297], scale=2.3)
    for name, kind, title, ur, date in kit.ALBUMS:
        lab = {"wedding": ("Wedding album", "شادی البم"), "baby": ("Baby album", "بے بی البم"),
               "family": ("Family album", "فیملی البم")}[kind]
        add(name, "Album covers", lab[0], lab[1], kit.album(kind, title, ur, date), pdf=[305, 305], scale=3)
    add("card-front", "Business card", "Card · front", "کارڈ · سامنے", ad.card_front(), pdf=[95.25, 57.15], scale=1)
    add("card-back", "Business card", "Card · back", "کارڈ · پیچھے", ad.card_back(), pdf=[95.25, 57.15], scale=1)
    add("dp-badge", "Profile picture", "Round badge · charcoal", "گول لوگو", kit.badge(SURMA, MALAI, SONA, MALAI))
    add("dp-badge-light", "Profile picture", "Round badge · ivory", "گول لوگو", kit.badge(MALAI, SURMA, SONA, SURMA))
    add("dp-badge-mehndi", "Profile picture", "Round badge · mehndi", "گول لوگو", kit.badge(MEHNDI, MALAI, "#D9B77C", MALAI))
    add("dp-icon", "Profile picture", "WhatsApp icon", "واٹس ایپ ڈی پی", kit.dp_icon(SURMA, MALAI, SONA))
    add("signboard", "Print", "Signboard flex 12×3 ft", "سائن بورڈ", kit.signboard(), pdf=[3657.6, 914.4], scale=3)
    add("order-slip", "Print", "Order slip A5", "آرڈر سلپ", kit.order_slip(), pdf=[148, 210], scale=3)
    return T


def b64(path):
    return base64.b64encode(open(path, "rb").read()).decode()


def build_html(out):
    T = json.load(open(os.path.join(BUILD, "templates.json")))
    for tp in T:
        p = os.path.join(BUILD, "thumbs", tp["id"] + ".jpg")
        tp["thumb"] = "data:image/jpeg;base64," + b64(p) if os.path.exists(p) else ""
    fonts = {"CPS Display": b64(os.path.join(HERE, "fonts/Marcellus.ttf")),
             "CPS Sans": b64(os.path.join(HERE, "fonts/Jost500.ttf")),
             "CPS Urdu": b64(os.path.join(HERE, "fonts/Nastaliq600.ttf"))}
    from brand import horizontal
    ad.LIVE = False
    logo = strip_size(horizontal(MALAI, SONA, MALAI, MALAI, SONA)).replace("<svg ", '<svg class="logo" aria-hidden="true" ', 1)
    body = open(os.path.join(HERE, "app_template.html")).read()
    data = json.dumps({"templates": T, "fonts": fonts}).replace("</", "<\\/")
    body = body.replace("{{DATA}}", data).replace("{{LOGO}}", logo)
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "studio-designer-artifact.html"), "w").write(body)
    standalone = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                  '<meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'
                  + body + "</body></html>")
    open(os.path.join(out, "studio-designer.html"), "w").write(standalone)
    print("wrote", out, len(standalone) // 1024, "KB")


if __name__ == "__main__":
    if sys.argv[1] == "templates":
        os.makedirs(BUILD, exist_ok=True)
        T = templates()
        json.dump(T, open(os.path.join(BUILD, "templates.json"), "w"))
        print(len(T), "templates,", sum(len(x["svg"]) for x in T) // 1024, "KB")
    else:
        build_html(sys.argv[2])
