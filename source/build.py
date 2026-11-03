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
    ("L3", "L3pages", "Lecture 3", "Quantum tunnelling devices",
     "Six interactive models that go with the Lecture 3 notes: an electron tunnelling through a wall, the scanning tunnelling microscope, the tunnel diode, the resonant-tunnelling diode, the tunnel FET, and the single-electron transistor. Each opens in a simple view; press More detail for the numbers and graphs."),
    ("L4", "L4pages", "Lecture 4", "Beyond planar silicon: nanotubes, FinFETs, SOI and compound semiconductors",
     "Six interactive models that go with the Lecture 4 notes: the band structure of a carbon nanotube, the ballistic nanotube transistor, the Schottky-barrier nanotube transistor, FinFET and nanosheet design, partially and fully depleted SOI, and the speed and colour of compound semiconductors. Each opens in a simple view; press More detail for the numbers and graphs."),
]


QUIZDIR = SRC / "quiz"           # one JSON file of questions per slide deck, e.g. L4-D3.json
def quiz_links(LID, ref, pre="../"):
    """Links to the quizzes for the documents an animation supports (only quizzes that exist)."""
    out = []
    for n in sorted(set(re.findall(r"Document (\d)", ref))):
        f = QUIZDIR / f"{LID}-D{n}.json"
        if f.exists():
            q = json.loads(f.read_text()); out.append(f'<a href="{pre}quiz/{LID}-D{n}.html">{q["kicker"]}: {q["title"]}</a>')
    return out

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

SECTIONS = [("notes", "Notes &amp; Slides"), ("animations", "Animations"), ("quiz", "Quizzes")]
def topbar(pre, section, fs):
    nav = "".join(f'<a href="{pre}{k}/index.html"' + (' aria-current="page"' if k == section else "") + f'>{t}</a>' for k, t in SECTIONS)
    tools = ('<button id="tbig" type="button" title="Larger text for projection">A+</button>'
             '<button id="ttheme" type="button" title="Switch light/dark">Theme</button>'
             + ('<button id="tfs" type="button" title="Show the animation full screen">Full screen</button>' if fs else ''))
    return (f'<div class="top"><div class="wrap"><a class="brand" href="{pre}index.html">KKKC6353<span>Nanoelectronic Devices</span></a>'
            f'<nav class="snav" aria-label="Sections">{nav}</nav><div class="tools">{tools}</div></div></div>')

def ltabs(current, href):
    """Lecture switcher: href(LID) gives the link for each lecture."""
    return '<nav class="ltabs" aria-label="Lectures">' + "".join(
        f'<a href="{href(L[0])}"' + (' aria-current="page"' if L[0] == current else "") + f'>{L[2]}</a>' for L in LECTURES) + '</nav>'

def shell(title, desc, body, pre="", section=None, fs=False, path=""):
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
{topbar(pre, section, fs)}
{body}
</body></html>"""

tiles = []; ANIMS = {}
for LID, FOLDER, LNAME, LTITLE, LEDE in LECTURES:
    pages = load(FOLDER); N = len(pages)
    (OUT / LID).mkdir(parents=True, exist_ok=True)
    for i, (m, body) in enumerate(pages):
        prev = pages[i - 1][0] if i > 0 else None
        nxt = pages[i + 1][0] if i < N - 1 else None
        nav = '<footer class="nav wrap">' + (
            f'<a href="{prev["slug"]}.html" rel="prev"><small>← Previous</small>{prev["title"]}</a>' if prev else '<a href="index.html"><small>←</small>All animations</a>') + (
            f'<a href="{nxt["slug"]}.html" rel="next" style="text-align:right"><small>Next →</small>{nxt["title"]}</a>' if nxt else '<a href="index.html" style="text-align:right"><small>→</small>All animations</a>') + '</footer>'
        hero = f"""<div class="wrap"><nav class="bc" aria-label="Breadcrumb"><a href="../animations/index.html">Animations</a> › <a href="index.html">{LNAME}</a></nav><header class="hero">
    <p class="kicker">Animation {m['num']} of {N} · {m['ref']}</p>
    <h1>{m['title']}</h1><p class="lede">{m['blurb']}</p></header>"""
        ql = quiz_links(LID, m["ref"])
        qline = (f'<p class="quizlink">Test yourself: {" · ".join(ql)}</p>') if ql else ""
        page = hero + body.replace("</main>", "</main>", 1) + qline + nav + \
            f'<p class="wrap foot">{COURSE} · {BYLINE}.<br>Interactive teaching models: simplified physics, stated on each page. Original work; no third-party figures.</p></div>'
        (OUT / LID / f"{m['slug']}.html").write_text(shell(f"{m['title']} · KKKC6353 {LNAME}", m["blurb"], page, pre="../", section="animations", fs=True, path=f"{LID}/{m['slug']}.html"))

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
    .artnote{font-size:.78rem;color:var(--muted);margin:-.8rem 0 1rem}
    .also{margin:.6rem 0 0;font-size:.95rem}</style>"""
    idx = f"""{idx_css}<div class="wrap"><nav class="bc" aria-label="Breadcrumb"><a href="../animations/index.html">Animations</a> › {LNAME}</nav>
    {ltabs(LID, lambda k: f"../{k}/index.html")}<header class="hero"><p class="kicker">{COURSE}</p>
    <h1>{LNAME} — interactive animations</h1><p class="byline">{BYLINE}</p>
    <p class="lede">{LEDE} Each page has the animation, things to try in class, check questions with answers, and a statement of the model behind it.</p>
    <p class="also">Also for {LNAME}: <a href="../notes/index.html#{LID}">notes and slides</a> · <a href="../quiz/index.html#{LID}">quizzes</a></p></header>
    <div class="tiles">{cards}</div>
    <section class="card howto"><h2>Using these in class</h2>
    <ul><li>Use <b>A+</b> for larger text when projecting, and <b>Full screen</b> to show just the animation.</li>
    <li>Every page works offline: save it (File → Save Page As) and it runs without a network connection.</li>
    <li>The models are deliberately simple and each page says what is left out. They reproduce trends and orders of magnitude, not a specific process.</li></ul></section></div>"""
    (OUT / LID / "index.html").write_text(shell(f"{LNAME} animations · KKKC6353 Nanoelectronic Devices", f"{N} interactive animations for KKKC6353 {LNAME}: {LTITLE[0].lower() + LTITLE[1:]}.", idx, pre="../", section="animations", path=f"{LID}/"))


    ANIMS[LID] = pages
    tiles.append(f'<a class="card tile" href="../{LID}/index.html"><span class="num">{LNAME.upper()}</span><span class="t">{LTITLE}</span><span class="b">{N} interactive animations, with things to try in class and check questions.</span></a>')

# ---- notes, quizzes, animations landing and site root
import shutil
HERE = pathlib.Path(__file__).parent
PDFDIR = HERE / "pdf"            # PDFs of notes, slides and student guides (copied to notes/files/ when present)
# lecture -> [(doc id, kicker, title, file stem, has slides, note)]
DOCS = {
    "L1": [("D1", "Document 1", "CMOS Technology", "L1-D1-CMOS-Technology", True, ""),
           ("D2", "Document 2", "Device Physics", "L1-D2-Device-Physics", True, ""),
           ("D3", "Document 3", "Short-Channel Effects", "L1-D3-Short-Channel-Effects", True, "")],
    "L2": [("D1", "Document 1", "The Quantum World", "L2-D1-The-Quantum-World", True, ""),
           ("D2", "Document 2", "Wells, Wires and Dots", "L2-D2-Wells-Wires-Dots", True, ""),
           ("D3", "Document 3", "Making Dots and Nanotubes", "L2-D3-Making-Dots-and-Nanotubes", True, "")],
    "L3": [("D1", "Document 1", "Tunnelling", "L3-D1-Tunnelling", True, ""),
           ("D2", "Document 2", "Tunnel Devices", "L3-D2-Tunnel-Devices", True, ""),
           ("D3", "Document 3", "One Electron at a Time", "L3-D3-One-Electron-at-a-Time", True, "")],
    "L4": [("D1", "Document 1 · optional reading", "Carbon Nanotubes", "L4-D1-Carbon-Nanotubes", False,
            "The band theory of nanotubes, for reading on your own. The Part 1 slides open with a short recap of what you need from it."),
           ("D2", "Part 1 · Document 2", "Carbon Nanotube Transistors", "L4-D2-Nanotube-Transistors", True, ""),
           ("D3", "Part 2 · Document 3", "FinFETs, Nanosheets and Silicon-on-Insulator", "L4-D3-FinFETs-Nanosheets-SOI", True, ""),
           ("D4", "Part 3 · Document 4", "Compound Semiconductors", "L4-D4-Compound-Semiconductors", True, "")],
}
(OUT / "notes" / "files").mkdir(parents=True, exist_ok=True)
(OUT / "quiz").mkdir(parents=True, exist_ok=True)
(OUT / "animations").mkdir(parents=True, exist_ok=True)

def pdf(stem):
    """Copy a PDF into the site if it exists; return its site path relative to notes/, or None."""
    f = PDFDIR / f"{stem}.pdf"
    if not f.exists(): return None
    shutil.copy(f, OUT / "notes" / "files" / f.name); return f"files/{f.name}"

def quiz_of(LID, D):
    f = QUIZDIR / f"{LID}-{D}.json"
    return json.loads(f.read_text()) if f.exists() else None

def anims_for(LID, D):
    n = D[1:]
    return [m for m, _ in ANIMS[LID] if re.search(rf"Document {n}\b", m["ref"])]

SOON = '<span class="soon">{} · coming soon</span>'
def btn(href, text, ext=False):
    return f'<a class="btn{"" if ext else " ghost"}" href="{href}"' + (' target="_blank" rel="noopener"' if ext else "") + f'>{text}</a>'

sec_css = idx_css + """<style>
.lec{margin:1.6rem 0 2rem;scroll-margin-top:1rem}
.lec>h2{font-size:1.25rem;color:var(--navy);margin:0 0 .2rem;padding-bottom:.3rem;border-bottom:2px solid var(--rust)}
.lec>p{color:var(--muted);margin:.3rem 0 .8rem}
.docs{display:grid;gap:10px}
.doc{padding:14px 16px;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:.3rem 1.2rem;align-items:center}
.doc>*{grid-column:1}.doc .btnrow{grid-column:2;grid-row:1/span 4;justify-content:flex-end}
@media (max-width:760px){.doc{grid-template-columns:minmax(0,1fr)}.doc .btnrow{grid-column:1;grid-row:auto;justify-content:flex-start}}
a.btn{text-decoration:none;display:inline-block}
.doc .dk{margin:0;color:var(--rust);font-weight:700;font-size:.8rem;letter-spacing:.05em;text-transform:uppercase}
.doc h3{margin:0;font-size:1.08rem;color:var(--navy)}
.doc .dn{margin:0;color:var(--muted);font-size:.9rem}
.doc .rel{margin:.2rem 0 0;font-size:.88rem;color:var(--muted)}
.doc .rel a{white-space:nowrap}
.soon{display:inline-block;font-size:.84rem;padding:.38rem .65rem;border-radius:6px;border:1px dashed var(--line);color:var(--muted)}
.sections{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:14px;margin:0 0 1.6rem}
.sections .tile .t{font-size:1.25rem}
table.bylec{width:100%;border-collapse:collapse;font-size:.95rem;margin:.4rem 0 1.4rem}
table.bylec th,table.bylec td{text-align:left;padding:.55rem .6rem;border-bottom:1px solid var(--line);vertical-align:top}
table.bylec th{color:var(--muted);font-weight:600;font-size:.82rem;text-transform:uppercase;letter-spacing:.05em}
table.bylec td a{white-space:nowrap}
@media (max-width:640px){table.bylec .topic,table.bylec .ln{display:none}table.bylec th,table.bylec td{padding:.5rem .35rem}}
</style>"""

def lec_head(LID, LNAME, LTITLE):
    return f'<section class="lec" id="{LID}"><h2>{LNAME} · {LTITLE}</h2>'

# ---------- Notes & Slides
blocks = []
for LID, FOLDER, LNAME, LTITLE, LEDE in LECTURES:
    cards = []
    for D, kick, title, stem, slides, note in DOCS[LID]:
        n_pdf, s_pdf, q = pdf(stem), (pdf(stem + "-slides") if slides else None), quiz_of(LID, D)
        b = [btn(n_pdf, "Notes (PDF)", True) if n_pdf else SOON.format("Notes PDF")]
        if slides: b.append(btn(s_pdf, "Slides (PDF)", True) if s_pdf else SOON.format("Slides PDF"))
        if slides: b.append(btn(f"../quiz/{LID}-{D}.html", "Quiz") if q else SOON.format("Quiz"))
        rel = anims_for(LID, D)
        rel_html = ('<p class="rel">Animations: ' + " · ".join(f'<a href="../{LID}/{m["slug"]}.html">{m["title"]}</a>' for m in rel) + '</p>') if rel else ""
        cards.append(f'<div class="card doc"><p class="dk">{kick}</p><h3>{title}</h3>' + (f'<p class="dn">{note}</p>' if note else "")
                     + f'<div class="btnrow">{"".join(b)}</div>{rel_html}</div>')
    g = pdf(f"{LID}-Animations-Student-Guide")
    cards.append(f'<div class="card doc"><p class="dk">Animations</p><h3>Student guide to the {LNAME} animations</h3>'
                 f'<p class="dn">What each animation shows, the big idea, things to try and questions to answer.</p>'
                 f'<div class="btnrow">{btn(g, "Guide (PDF)", True) if g else SOON.format("Guide PDF")}{btn(f"../{LID}/index.html", "Open the animations")}</div></div>')
    blocks.append(lec_head(LID, LNAME, LTITLE) + f'<div class="docs">{"".join(cards)}</div></section>')
notes = f"""{sec_css}<div class="wrap"><header class="hero"><p class="kicker">{COURSE}</p><h1>Notes &amp; Slides</h1>
<p class="lede">The lecture notes and slides for each lecture, with the quiz and the animations that go with each part. The PDFs open in your browser; use its download button to keep a copy.</p></header>
{ltabs(None, lambda k: f"#{k}")}{"".join(blocks)}<p class="foot">{COURSE} · {BYLINE}</p></div>"""
(OUT / "notes" / "index.html").write_text(shell(f"Notes and slides · {COURSE}", f"Lecture notes and slides for {COURSE}.", notes, pre="../", section="notes", path="notes/"))

# ---------- Quizzes (index; the quiz pages themselves are added per deck)
blocks = []
for LID, FOLDER, LNAME, LTITLE, LEDE in LECTURES:
    cards = []
    for D, kick, title, stem, slides, note in DOCS[LID]:
        if not slides: continue
        q = quiz_of(LID, D)
        nq = f"{len(q['questions'])} questions · " if q else ""
        cards.append(f'<div class="card doc"><p class="dk">{kick}</p><h3>{title}</h3><p class="dn">{nq}Easy questions on the key ideas of this set of slides.</p>'
                     f'<div class="btnrow">{btn(f"{LID}-{D}.html", "Start the quiz", True).replace(' target="_blank" rel="noopener"', '') if q else SOON.format("Quiz")}</div></div>')
    blocks.append(lec_head(LID, LNAME, LTITLE) + f'<div class="docs">{"".join(cards)}</div></section>')
quiz = f"""{sec_css}<div class="wrap"><header class="hero"><p class="kicker">{COURSE}</p><h1>Quizzes</h1>
<p class="lede">One short quiz for each set of slides: easy multiple-choice questions on the foundations, with an explanation after every answer. Nothing is recorded: your best score is kept only in your own browser.</p></header>
{ltabs(None, lambda k: f"#{k}")}{"".join(blocks)}<p class="foot">{COURSE} · {BYLINE}</p></div>"""
(OUT / "quiz" / "index.html").write_text(shell(f"Quizzes · {COURSE}", f"Self-test quizzes for {COURSE}, one per set of slides.", quiz, pre="../", section="quiz", path="quiz/"))

# ---------- Quiz pages, one per slide deck with a JSON file
qjs = (SRC / "quiz.js").read_text()
qcss = """<style>
.qwrap{max-width:820px;margin:0 auto}
#quiz{padding:18px 20px 20px}
.qhead{display:flex;justify-content:space-between;color:var(--muted);font-size:.88rem;font-variant-numeric:tabular-nums}
.qbar{height:5px;background:var(--grid);border-radius:3px;margin:.4rem 0 1rem;overflow:hidden}.qbar i{display:block;height:100%;background:var(--rust)}
.qtext{font-size:1.15rem;line-height:1.4;color:var(--ink);margin:0 0 .9rem;outline:none}
.qimg{margin:0 0 1rem;text-align:center}.qimg img{max-width:100%;max-height:340px;border-radius:8px;border:1px solid var(--line);background:#fff}
.qopts{display:grid;gap:8px}
.qopt{display:flex;gap:.7rem;align-items:flex-start;text-align:left;font:inherit;padding:.7rem .85rem;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--ink);cursor:pointer}
.qopt:hover:not(:disabled){border-color:var(--blue)}
.qopt:disabled{cursor:default}
.qkey{flex:0 0 1.5rem;height:1.5rem;border-radius:50%;background:var(--chip);color:var(--muted);font-weight:700;font-size:.8rem;display:grid;place-items:center}
.qkey:empty{display:none}
.qopt.right{border-color:var(--green);background:color-mix(in srgb,var(--green) 12%,var(--panel))}
.qopt.right .qkey{background:var(--green);color:#fff}
.qopt.wrong{border-color:var(--rust);background:color-mix(in srgb,var(--rust) 12%,var(--panel))}
.qopt.wrong .qkey{background:var(--rust);color:#fff}
.fb{margin-top:1rem;padding:.75rem .9rem;border-radius:8px;background:var(--chip);border-left:4px solid var(--blue)}
.fb.good{border-left-color:var(--green)}.fb.bad{border-left-color:var(--rust)}
.fbref{margin-top:.4rem;font-size:.88rem;color:var(--muted)}
.qnext{margin-top:1rem;display:flex;justify-content:flex-end}
.qdone{text-align:center;padding:.5rem 0 1rem}.qdone .big{font-size:3rem;font-weight:700;color:var(--navy);margin:.2rem 0}.qdone .big span{font-size:1.5rem;color:var(--muted)}
.qdone .best{color:var(--muted);font-size:.9rem}
.qrev{font-size:1.05rem;color:var(--navy);margin:1rem 0 .5rem}
.qmiss{padding:12px 14px;margin:0 0 10px}.qmiss p{margin:.2rem 0}.qmq{font-weight:600}.qme{color:var(--muted)}
.qend{justify-content:center;margin-top:1rem}
.qnote{color:var(--muted);font-size:.85rem;text-align:center;margin:.8rem 0 0}
.also{margin:.6rem 0 0;font-size:.95rem}
</style>"""
qfiles = sorted(QUIZDIR.glob("*.json")) if QUIZDIR.exists() else []
if (QUIZDIR / "img").exists():
    (OUT / "quiz" / "img").mkdir(parents=True, exist_ok=True)
    for f in (QUIZDIR / "img").iterdir(): shutil.copy(f, OUT / "quiz" / "img" / f.name)
for f in qfiles:
    Q = json.loads(f.read_text()); qid = f.stem; LID = Q["lecture"]
    sp = pdf(Q["slides"])
    meta = {"id": qid, "root": "../", "slides": ("../notes/" + sp) if sp else None}
    rel = [m for m in anims_for(LID, Q["doc"])]
    rel_html = " · ".join(f'<a href="../{LID}/{m["slug"]}.html">{m["title"]}</a>' for m in rel)
    body = f"""{qcss}<div class="wrap qwrap"><nav class="bc" aria-label="Breadcrumb"><a href="index.html">Quizzes</a> › {Q["kicker"]}</nav>
<header class="hero"><p class="kicker">Quiz · {Q["kicker"]}</p><h1>{Q["title"]}</h1>
<p class="lede">{len(Q["questions"])} easy questions on the key ideas of these slides. Pick an answer to see whether it is right, and why. Keys: A–D (or 1–4) to answer, Enter for the next question.</p>
<p class="also">{'<a href="../notes/' + sp + '" target="_blank" rel="noopener">Slides (PDF)</a> · ' if sp else ''}<a href="../notes/index.html#{LID}">Notes &amp; slides</a>{' · Animations: ' + rel_html if rel_html else ''}</p></header>
<section class="card" id="quiz"><noscript>This quiz needs JavaScript.</noscript></section>
<p class="qnote">Nothing is recorded or sent anywhere. Your best score is kept only in this browser.</p>
<p class="foot">{COURSE} · {BYLINE}</p></div>
<script>const QUIZ = {json.dumps(Q["questions"], ensure_ascii=False)};
const QMETA = {json.dumps(meta)};
{qjs}</script>"""
    (OUT / "quiz" / f"{qid}.html").write_text(shell(f"Quiz: {Q['title']} · {COURSE}", f"Self-test quiz for {COURSE}, {Q['kicker']}: {Q['title']}.", body, pre="../", section="quiz", path=f"quiz/{qid}.html"))

# ---------- Animations landing
total = sum(len(v) for v in ANIMS.values())
anim = f"""{sec_css}<div class="wrap"><header class="hero"><p class="kicker">{COURSE}</p><h1>Animations</h1>
<p class="lede">{total} interactive models, by lecture. Each page has the animation, things to try, check questions with answers, and a statement of the model behind it. Every page also works offline once saved.</p></header>
<div class="tiles">{"".join(tiles)}</div><p class="foot">{COURSE} · {BYLINE}</p></div>"""
(OUT / "animations" / "index.html").write_text(shell(f"Animations · {COURSE}", f"{total} interactive animations for {COURSE}, by lecture.", anim, pre="../", section="animations", path="animations/"))

# ---------- Site root
rows = "".join(f'<tr><td><b><span class="ln">Lecture </span>{LNAME.split()[-1]}</b></td><td class="topic">{LTITLE}</td><td><a href="notes/index.html#{LID}">Notes &amp; slides</a></td>'
               f'<td><a href="{LID}/index.html">{len(ANIMS[LID])}<span class="ln"> animations</span></a></td><td><a href="quiz/index.html#{LID}">Quizzes</a></td></tr>'
               for LID, FOLDER, LNAME, LTITLE, LEDE in LECTURES)
root = f"""{sec_css}<div class="wrap">
<section class="banner" aria-label="{COURSE}"><div class="in"><p class="k">KKKC6353</p><h1>Nanoelectronic Devices</h1>
<p class="sub">Lecture notes, slides, interactive animations and quizzes</p>
<div class="who"><b>{AUTHOR}</b><span>{UNI} · 2026</span></div></div></section>
<p class="artnote">Banner: original artwork made for this course, chip wiring giving way to a quantum interference pattern.</p>
<div class="sections">
<a class="card tile" href="notes/index.html"><span class="num">READ</span><span class="t">Notes &amp; Slides</span><span class="b">The lecture notes and slides for every lecture, as PDFs.</span></a>
<a class="card tile" href="animations/index.html"><span class="num">EXPLORE</span><span class="t">Animations</span><span class="b">{total} interactive models: change the device and watch the physics respond.</span></a>
<a class="card tile" href="quiz/index.html"><span class="num">TEST YOURSELF</span><span class="t">Quizzes</span><span class="b">A short quiz for each set of slides, with an explanation after every answer.</span></a>
</div>
<h2 style="color:var(--navy);font-size:1.15rem;margin:0">By lecture</h2>
<table class="bylec"><thead><tr><th>Lecture</th><th class="topic">Topic</th><th>Notes</th><th>Animations</th><th>Quizzes</th></tr></thead><tbody>{rows}</tbody></table>
<p class="foot" style="padding:0">{COURSE} · {BYLINE}</p></div>"""
(OUT / "index.html").write_text(shell(COURSE, "Lecture notes, slides, interactive animations and quizzes for " + COURSE + ".", root, pre="", section=None, path=""))
for img in ("hero.jpg", "og-image.jpg"): shutil.copy(pathlib.Path(__file__).parent / "art" / img, OUT / img)
(OUT / ".nojekyll").write_text("")
print("built", total, "animation pages + notes, quizzes and home")
