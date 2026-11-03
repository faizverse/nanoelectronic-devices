#!/usr/bin/env python3
"""Check quiz JSON files: structure, one correct answer, unique options, slide numbers within the deck, images and animation links exist.
Usage: python3 quizcheck.py [deck_dir] ; with --show prints each question next to the text of its slide."""
import json, sys, pathlib, re
SRC = pathlib.Path(__file__).parent / "src"; SITE = pathlib.Path(__file__).parent / "site"
DECKS = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else None
show = "--show" in sys.argv
bad = 0
def err(f, n, m):
    global bad; bad += 1; print(f"  {f}: Q{n}: {m}")
for f in sorted((SRC / "quiz").glob("*.json")):
    Q = json.loads(f.read_text()); qs = Q["questions"]
    for k in ("lecture", "doc", "kicker", "title", "slides", "questions"):
        if k not in Q: err(f.name, 0, f"missing {k}")
    nslides, texts = None, {}
    if DECKS:
        from pptx import Presentation
        p = DECKS / f"{Q['slides']}.pptx"
        if p.exists():
            pr = Presentation(p); nslides = len(pr.slides)
            for i, sl in enumerate(pr.slides, 1):
                texts[i] = " | ".join(sh.text_frame.text.replace("\n", " / ") for sh in sl.shapes if sh.has_text_frame and sh.text_frame.text.strip())
                if sl.has_notes_slide: texts[i] += "  [NOTES] " + sl.notes_slide.notes_text_frame.text
        else: err(f.name, 0, f"deck not found: {p}")
    if not 10 <= len(qs) <= 15: err(f.name, 0, f"{len(qs)} questions (want 10-15)")
    for n, q in enumerate(qs, 1):
        o = q.get("options", [])
        if q.get("type") == "tf":
            if o != ["True", "False"]: err(f.name, n, "true/false options must be ['True','False']")
        elif not 3 <= len(o) <= 4: err(f.name, n, f"{len(o)} options")
        if len(set(o)) != len(o): err(f.name, n, "duplicate options")
        if not isinstance(q.get("answer"), int) or not 0 <= q["answer"] < len(o): err(f.name, n, "answer index out of range")
        if not q.get("explain"): err(f.name, n, "no explanation")
        if not q.get("q"): err(f.name, n, "no question text")
        s = q.get("slide")
        if not isinstance(s, int) or s < 1 or (nslides and s > nslides): err(f.name, n, f"bad slide {s}")
        if q.get("img"):
            if not (SRC / "quiz" / q["img"]).exists(): err(f.name, n, f"missing image {q['img']}")
            if not q.get("alt"): err(f.name, n, "image without alt text")
        if q.get("anim") and not (SITE / q["anim"]).exists(): err(f.name, n, f"missing animation {q['anim']}")
        if show:
            print(f"\n[{f.stem} Q{n}] slide {s}: {q['q']}\n  ANSWER: {o[q['answer']]}\n  SLIDE: {texts.get(s, '')[:700]}")
    print(f"{f.name}: {len(qs)} questions checked")
print("problems:", bad); sys.exit(1 if bad else 0)
