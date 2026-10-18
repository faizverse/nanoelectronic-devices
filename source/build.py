#!/usr/bin/env python3
"""Assemble standalone HTML pages: inline common.css/common.js and shared models into each page."""
import json, re, pathlib, html

SRC = pathlib.Path(__file__).parent / "src"
OUT = pathlib.Path(__file__).parent / "site"
COURSE = "KKKC6353 Nanoelectronic Devices"
css = (SRC / "common.css").read_text()
js = (SRC / "common.js").read_text()

pages = []
for f in sorted((SRC / "pages").glob("*.html")):
    raw = f.read_text()
    m = re.match(r"\s*<!--META\s*(\{.*?\})\s*-->", raw, re.S)
    meta = json.loads(m.group(1)); body = raw[m.end():]
    body = re.sub(r"/\*INCLUDE (\S+)\*/", lambda k: (SRC / k.group(1)).read_text(), body)
    pages.append((meta, body))
pages.sort(key=lambda p: p[0]["num"])
N = len(pages)

TOP = """<div class="top"><div class="wrap">
<a class="crumb" href="{home}">{crumb}</a>
<div class="tools"><button id="tbig" type="button" title="Larger text for projection">A+</button>
<button id="ttheme" type="button" title="Switch light/dark">Theme</button>{fs}</div></div></div>"""

def shell(title, desc, body, home, fs=True, crumb=COURSE + ' · Lecture 1 animations'):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%231f3a5f'/%3E%3Crect x='6' y='9' width='20' height='4' fill='%23b4451f'/%3E%3Crect x='6' y='15' width='20' height='9' fill='%23dfe7ef'/%3E%3C/svg%3E">
<style>{css}</style>
<script>{js}</script></head>
<body>
{TOP.format(home=home, crumb=crumb, fs='<button id="tfs" type="button" title="Show the animation full screen">Full screen</button>' if fs else '')}
{body}
</body></html>"""

(OUT / "L1").mkdir(parents=True, exist_ok=True)
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
        f'<p class="wrap foot">{COURSE}. Interactive teaching models: simplified physics, stated on each page. Original work; no third-party figures.</p></div>'
    (OUT / "L1" / f"{m['slug']}.html").write_text(shell(f"{m['title']} · L1 animation", m["blurb"], page, "index.html"))

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
.howto{padding:16px 18px;margin-bottom:1rem}.howto h2{font-size:1.05rem;color:var(--navy);margin:0 0 .4rem}</style>"""
idx = f"""{idx_css}<div class="wrap"><header class="hero"><p class="kicker">{COURSE}</p>
<h1>Lecture 1 — interactive animations</h1>
<p class="lede">Eleven interactive models that go with the Lecture 1 notes: how a MOSFET works, how it fails as it shrinks, and why the industry changed the device. Each page has the animation, things to try in class, check questions with answers, and a statement of the model behind it.</p></header>
<div class="tiles">{cards}</div>
<section class="card howto"><h2>Using these in class</h2>
<ul><li>Use <b>A+</b> for larger text when projecting, and <b>Full screen</b> to show just the animation.</li>
<li>Every page works offline: save it (File → Save Page As) and it runs without a network connection.</li>
<li>The models are deliberately simple and each page says what is left out. They reproduce trends and orders of magnitude, not a specific process.</li></ul></section></div>"""
(OUT / "L1" / "index.html").write_text(shell("Lecture 1 animations · KKKC6353", "Interactive animations for KKKC6353 Lecture 1.", idx, "index.html", fs=False))

# ---- site root
root = f"""{idx_css}<div class="wrap"><header class="hero"><p class="kicker">Course materials</p>
<h1>{COURSE}</h1><p class="lede">Interactive animations for the course, by lecture.</p></header>
<div class="tiles"><a class="card tile" href="L1/index.html"><span class="num">L1</span><span class="t">CMOS technology, device physics and short-channel effects</span><span class="b">{N} animations</span></a></div></div>"""
(OUT / "index.html").write_text(shell(COURSE, "Interactive animations for " + COURSE, root, "index.html", fs=False, crumb=COURSE))
(OUT / ".nojekyll").write_text("")
print("built", N, "pages")
