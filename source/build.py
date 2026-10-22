#!/usr/bin/env python3
"""Assemble standalone HTML pages: inline common.css/common.js and shared models into each page."""
import json, re, pathlib, html

SRC = pathlib.Path(__file__).parent / "src"
OUT = pathlib.Path(__file__).parent / "site"
COURSE = "KKKC6353 Nanoelectronic Devices"
AUTHOR, UNI = "Dr Muhammad Faiz Bukhori", "Universiti Kebangsaan Malaysia"
BASE = "https://faizverse.github.io/nanoelectronic-devices/"
BYLINE = f"{AUTHOR} · {UNI} · 2026"
css = (SRC / "common.css").read_text()
js = (SRC / "common.js").read_text()

# lecture id -> (source folder, short name, tile title, index lede)
LECTURES = [
    ("L1", "pages", "Lecture 1", "CMOS technology, device physics and short-channel effects",
     "Eleven interactive models that go with the Lecture 1 notes: how a MOSFET works, how it fails as it shrinks, and why the industry changed the device."),
    ("L2", "L2pages", "Lecture 2", "Quantum wells, wires and dots",
     "Seven interactive models that go with the Lecture 2 notes: an electron in a box, how trapping electrons shares out their energies, quantum-well and cascade lasers, carbon nanotubes, quantum-dot colour, and how dots are grown. Each opens in a simple view; press More detail for the numbers and graphs."),
]


def load(folder):
    out = []
    for f in sorted((SRC / folder).glob("*.html")):
        raw = f.read_text()
        m = re.match(r"\s*<!--META\s*(\{.*?\})\s*-->", raw, re.S)
        meta = json.loads(m.group(1)); body = raw[m.end():]
        body = re.sub(r"/\*INCLUDE (\S+)\*/", lambda k: (SRC / k.group(1)).read_text(), body)
        out.append((meta, body))
    out.sort(key=lambda p: p[0]["num"])
    return out

TOP = """<div class="top"><div class="wrap">
<a class="crumb" href="{home}">{crumb}</a>
<div class="tools"><button id="tbig" type="button" title="Larger text for projection">A+</button>
<button id="ttheme" type="button" title="Switch light/dark">Theme</button>{fs}</div></div></div>"""

def shell(title, desc, body, home, fs=True, crumb=COURSE + ' · Lecture 1 animations', path=""):
    e = html.escape; d = f"{desc} {AUTHOR}, {UNI}."
    og = f"""<meta name="author" content="{AUTHOR}, {UNI}">
<link rel="canonical" href="{BASE}{path}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{COURSE} · {UNI}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(d)}">
<meta property="og:url" content="{BASE}{path}">
<meta property="og:image" content="{BASE}og-image.jpg">
<meta property="og:image:secure_url" content="{BASE}og-image.jpg">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{COURSE}: {AUTHOR}, {UNI}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(d)}">
<meta name="twitter:image" content="{BASE}og-image.jpg">"""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(d)}">
{og}
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%231f3a5f'/%3E%3Crect x='6' y='9' width='20' height='4' fill='%23b4451f'/%3E%3Crect x='6' y='15' width='20' height='9' fill='%23dfe7ef'/%3E%3C/svg%3E">
<style>{css}</style>
<script>{js}</script></head>
<body>
{TOP.format(home=home, crumb=crumb, fs='<button id="tfs" type="button" title="Show the animation full screen">Full screen</button>' if fs else '')}
{body}
</body></html>"""

tiles = []
for LID, FOLDER, LNAME, LTITLE, LEDE in LECTURES:
    pages = load(FOLDER); N = len(pages)
    (OUT / LID).mkdir(parents=True, exist_ok=True)
    for i, (m, body) in enumerate(pages):
        prev = pages[i - 1][0] if i > 0 else None
        nxt = pages[i + 1][0] if i < N - 1 else None
        nav = '<footer class="nav wrap">' + (
            f'<a href="{prev["slug"]}.html" rel="prev"><small>← Previous</small>{prev["title"]}</a>' if prev else '<a href="index.html"><small>←</small>All animations</a>') + (
            f'<a href="{nxt["slug"]}.html" rel="next" style="text-align:right"><small>Next →</small>{nxt["title"]}</a>' if nxt else '<a href="index.html" style="text-align:right"><small>→</small>All animations</a>') + '</footer>'
        hero = f"""<div class="wrap"><header class="hero">
    <p class="kicker">Animation {m['num']} of {N} · {m['ref']}</p>
    <h1>{m['title']}</h1><p class="lede">{m['blurb']}</p></header>"""
        page = hero + body.replace("</main>", "</main>", 1) + nav + \
            f'<p class="wrap foot">{COURSE} · {BYLINE}.<br>Interactive teaching models: simplified physics, stated on each page. Original work; no third-party figures.</p></div>'
        (OUT / LID / f"{m['slug']}.html").write_text(shell(f"{m['title']} · KKKC6353 {LNAME}", m["blurb"], page, "index.html", crumb=f"{COURSE} · {LNAME} animations", path=f"{LID}/{m['slug']}.html"))

    # ---- L1 index
    cards = "".join(f"""<a class="card tile" href="{m['slug']}.html">
    <span class="num">{m['num']:02d}</span><span class="t">{m['title']}</span>
    <span class="b">{m['blurb']}</span><span class="pills"><span class="pill">{m['ref']}</span>{'<span class="pill new">New</span>' if m.get('new') else ''}</span></a>"""
                    for m, _ in pages)
    idx_css = """<style>.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr));gap:14px;margin:1rem 0 2rem}
    .tile{display:flex;flex-direction:column;gap:.35rem;padding:16px;text-decoration:none;color:var(--ink);transition:border-color .15s,transform .15s}
    .tile:hover{border-color:var(--rust);transform:translateY(-2px)}
    .tile .num{font-weight:700;color:var(--rust);font-size:.85rem;letter-spacing:.06em}
    .tile .t{font-weight:650;font-size:1.08rem;color:var(--navy)}
    .tile .b{color:var(--muted);font-size:.92rem;flex:1}
    .tile .pills{display:flex;flex-wrap:wrap;gap:6px}.tile .pill.new{color:var(--green);border-color:var(--green)}
    .howto{padding:16px 18px;margin-bottom:1rem}.howto h2{font-size:1.05rem;color:var(--navy);margin:0 0 .4rem}
    .byline{margin:.1rem 0 .6rem;font-weight:600;color:var(--ink)}
    .banner{position:relative;margin:1rem 0 1.4rem;border-radius:14px;overflow:hidden;color:#fff;min-height:clamp(260px,34vw,400px);display:flex;align-items:center;
     background:linear-gradient(90deg,rgba(12,22,40,.94) 0%,rgba(12,22,40,.82) 40%,rgba(12,22,40,.15) 78%),url(hero.jpg) 62% center/cover no-repeat #0e1a2e}
    .banner .in{padding:clamp(20px,4vw,48px);max-width:640px}
    .banner .k{color:#ecb85c;font-weight:700;letter-spacing:.08em;font-size:.85rem;margin:0}
    .banner h1{color:#fff;font-size:clamp(2rem,5vw,3.2rem);line-height:1.05;margin:.3rem 0 .6rem}
    .banner .sub{color:#d6e2f0;margin:0 0 1.1rem;font-size:1.05rem}
    .banner .who{border-top:3px solid #d6683e;padding-top:.8rem;display:inline-block}
    .banner .who b{display:block;font-size:1.15rem}.banner .who span{color:#d6e2f0}
    .artnote{font-size:.78rem;color:var(--muted);margin:-.8rem 0 1rem}</style>"""
    idx = f"""{idx_css}<div class="wrap"><header class="hero"><p class="kicker">{COURSE}</p>
    <h1>{LNAME} — interactive animations</h1><p class="byline">{BYLINE}</p>
    <p class="lede">{LEDE} Each page has the animation, things to try in class, check questions with answers, and a statement of the model behind it.</p></header>
    <div class="tiles">{cards}</div>
    <section class="card howto"><h2>Using these in class</h2>
    <ul><li>Use <b>A+</b> for larger text when projecting, and <b>Full screen</b> to show just the animation.</li>
    <li>Every page works offline: save it (File → Save Page As) and it runs without a network connection.</li>
    <li>The models are deliberately simple and each page says what is left out. They reproduce trends and orders of magnitude, not a specific process.</li></ul></section></div>"""
    (OUT / LID / "index.html").write_text(shell(f"{LNAME} animations · KKKC6353 Nanoelectronic Devices", f"{N} interactive animations for KKKC6353 {LNAME}: {LTITLE[0].lower() + LTITLE[1:]}.", idx, "index.html", fs=False, crumb=f"{COURSE} · {LNAME} animations", path=f"{LID}/"))


    tiles.append(f'<a class="card tile" href="{LID}/index.html"><span class="num">{LNAME.upper()}</span><span class="t">{LTITLE}</span><span class="b">{N} interactive animations, with things to try in class and check questions.</span></a>')

# ---- site root
root = f"""{idx_css}<div class="wrap">
<section class="banner" aria-label="{COURSE}"><div class="in"><p class="k">KKKC6353</p><h1>Nanoelectronic Devices</h1>
<p class="sub">Interactive animations and course materials</p>
<div class="who"><b>{AUTHOR}</b><span>{UNI} · 2026</span></div></div></section>
<p class="artnote">Banner: original artwork made for this course, chip wiring giving way to a quantum interference pattern.</p>
<div class="tiles">{"".join(tiles)}</div>
<p class="wrap foot" style="padding:0">{COURSE} · {BYLINE}</p></div>"""
(OUT / "index.html").write_text(shell(COURSE, "Interactive animations and course materials for " + COURSE + ".", root, "index.html", fs=False, crumb=COURSE))
import shutil
for img in ("hero.jpg", "og-image.jpg"): shutil.copy(pathlib.Path(__file__).parent / "art" / img, OUT / img)
(OUT / ".nojekyll").write_text("")
print("built", N, "pages")
