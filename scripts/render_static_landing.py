#!/usr/bin/env python3
"""Render the Jinja landing.html (and pricing.html) into static HTML per language.

Lets the polished landing live on Cloudflare Pages without the Flask backend.
Design is unchanged — we only resolve the {% if ui_lang %} branches per language
and inline /static/app.css so the page is fully self-contained.

Output:
  site/index.html        -> Hebrew (default, RTL)
  site/ru/index.html     -> Russian
  site/en/index.html     -> English
"""
import os
import re
from jinja2 import Environment, FileSystemLoader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL_DIR = os.path.join(ROOT, "app", "templates")
CSS_PATH = os.path.join(ROOT, "app", "static", "app.css")
OUT_DIR = os.path.join(ROOT, "site")

SUPPORTED = ["en", "ru", "he"]
RTL = {"he"}


def is_rtl(lang):
    return lang in RTL


def render(template, lang):
    env = Environment(loader=FileSystemLoader(TPL_DIR), autoescape=False)
    env.globals["ui"] = lambda key, **kw: key  # safety no-op; landing doesn't use it
    tpl = env.get_template(template)
    return tpl.render(
        ui_lang=lang,
        is_rtl=is_rtl(lang),
        supported_langs=SUPPORTED,
    )


def inline_css(html, css):
    """Replace the external app.css link with an inline <style> block."""
    style = "<style>\n" + css + "\n</style>"
    html = re.sub(r'<link[^>]+/static/app\.css[^>]*>', style, html)
    return html


REVEAL_FAILSAFE = """
<noscript><style>.reveal,.reveal-left,.reveal-right,.reveal-scale{opacity:1!important;transform:none!important}</style></noscript>
<script>/* static-site failsafe: guarantee content is visible even if scroll-observer never fires */
setTimeout(function(){document.querySelectorAll('.reveal,.reveal-left,.reveal-right,.reveal-scale').forEach(function(e){e.classList.add('visible')});},2200);</script>
"""


def add_reveal_failsafe(html):
    """Static hosting safety net: never let JS-reveal hide content permanently."""
    if "</body>" in html:
        html = html.replace("</body>", REVEAL_FAILSAFE + "\n</body>", 1)
    else:
        html += REVEAL_FAILSAFE
    return html


from urllib.parse import quote

# Lead-capture contacts (coming-soon: no backend yet, so CTAs collect leads)
WA_PHONE = "972509051065"     # WhatsApp / phone
TG_USER = "TerrazzoTLV"       # Telegram username

# Prefilled WhatsApp message per page language
WA_MSG = {
    "he": "היי! ראיתי את Posting Autopilot ואשמח לגישה מוקדמת ולהדגמה.",
    "ru": "Привет! Видел Posting Autopilot — хочу ранний доступ и демо.",
    "en": "Hi! Saw Posting Autopilot — I'd like early access and a demo.",
}


def fix_links(html, lang):
    """Rewrite app routes for the backend-less coming-soon site.

    Language switch:
      /set-lang/he -> /   ·  /set-lang/ru -> /ru/  ·  /set-lang/en -> /en/
    CTAs (no backend yet) collect leads instead of dead-ending:
      /register, /user-login, /login, /pricing -> WhatsApp with a prefilled,
      language-matched message. Swap back to app routes once the VPS is live.
    """
    # Flat top-level files (no subfolders) so a single drag-drop never loses pages.
    html = html.replace('href="/set-lang/he"', 'href="/"')
    html = html.replace('href="/set-lang/ru"', 'href="/ru.html"')
    html = html.replace('href="/set-lang/en"', 'href="/en.html"')

    msg = WA_MSG.get(lang, WA_MSG["en"])
    wa = "https://wa.me/%s?text=%s" % (WA_PHONE, quote(msg))
    tg = "https://t.me/%s" % TG_USER
    # register / pricing = primary intent -> WhatsApp; sign-in -> Telegram
    for route in ("/register", "/pricing"):
        html = html.replace(
            'href="%s"' % route,
            'href="%s" target="_blank" rel="noopener"' % wa,
        )
    for route in ("/user-login", "/login"):
        html = html.replace(
            'href="%s"' % route,
            'href="%s" target="_blank" rel="noopener"' % tg,
        )
    return html


def main():
    css = open(CSS_PATH, encoding="utf-8").read() if os.path.exists(CSS_PATH) else ""
    os.makedirs(OUT_DIR, exist_ok=True)
    targets = {"he": "index.html", "ru": "ru.html", "en": "en.html"}
    for lang, rel in targets.items():
        html = render("landing.html", lang)
        html = inline_css(html, css)
        html = fix_links(html, lang)
        html = add_reveal_failsafe(html)
        out = os.path.join(OUT_DIR, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print("wrote %s (%d bytes, lang=%s)" % (rel, len(html), lang))


if __name__ == "__main__":
    main()
