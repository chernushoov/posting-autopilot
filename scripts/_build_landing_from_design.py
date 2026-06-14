import re, pathlib

SRC = pathlib.Path.home() / "Desktop" / "posting-autopilot.logo"
DST = pathlib.Path("/Users/alexey/Desktop/pa-design-work/app/templates")

# (source design file, output template, og:locale)
JOBS = [
    ("index.html", "landing.html",    "he"),  # Hebrew = default
    ("en.html",    "landing_en.html", "en"),
    ("ru.html",    "landing_ru.html", "ru"),
]

def transform(html: str) -> str:
    # 1. Drop the client-side auto language redirect (Flask controls language now)
    html = re.sub(r"<script>\s*/\* Auto language.*?</script>\s*", "", html, flags=re.S)

    # 2. assets/ -> Flask static
    html = html.replace('="assets/', '="/static/')

    # 3. plain nav "Sign in" link (no class) -> /login   (do BEFORE generic app.html)
    html = html.replace(
        '<a href="app.html" target="_blank" rel="noopener">',
        '<a href="/login">',
    )

    # 4. all other CTAs (Start Free / pricing / final) -> /register
    html = html.replace(
        'href="app.html" target="_blank" rel="noopener"',
        'href="/register"',
    )

    # 5. language switcher -> Flask /set-lang (keeps session lang consistent w/ app)
    html = html.replace('href="en.html" data-lang',   'href="/set-lang/en" data-lang')
    html = html.replace('href="ru.html" data-lang',   'href="/set-lang/ru" data-lang')
    html = html.replace('href="index.html" data-lang', 'href="/set-lang/he" data-lang')

    # 6. brand logo link -> home
    html = html.replace('href="index.html" class="brand"', 'href="/" class="brand"')

    # safety: any leftover bare *.html landing links -> home
    for f in ("index.html", "en.html", "ru.html", "app.html"):
        html = html.replace(f'href="{f}"', 'href="/register"' if f == "app.html" else 'href="/"')

    return html

def add_og_image(html: str) -> str:
    if "og:image" in html:
        return html
    tag = '<meta property="og:image" content="https://posting-autopilot.com/static/icon-512.png">\n'
    return html.replace('<meta property="og:type"', tag + '<meta property="og:type"', 1)

for src, out, loc in JOBS:
    raw = (SRC / src).read_text(encoding="utf-8")
    res = add_og_image(transform(raw))
    (DST / out).write_text(res, encoding="utf-8")
    # report residual risky refs
    leftover = re.findall(r'(?:src|href)="(?:assets/|app\.html|en\.html|ru\.html|index\.html)[^"]*"', res)
    assets_marker = '="assets/'
    print(f"{out}: {len(res)} bytes | app.html_left={res.count('app.html')} assets_left={res.count(assets_marker)} leftover={leftover[:3]}")
