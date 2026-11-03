/* KKKC6353 self-test quiz: one question at a time, instant feedback, score, review, reshuffle.
   Reads QUIZ (questions) and QMETA (links) defined inline by build.py. Nothing leaves the browser. */
(() => {
  const $ = (s, el = document) => el.querySelector(s);
  const app = $("#quiz"), KEY = "kkkc6353-quiz-" + QMETA.id;
  const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  // escape, then turn V_T, I_D, V_GS … into subscripts
  const fmt = s => esc(s).replace(/([A-Za-zμσ])_([A-Za-z0-9]+)/g, "$1<sub>$2</sub>");
  let order, i, score, missed, answered;

  function best() { try { return JSON.parse(localStorage.getItem(KEY) || "null"); } catch (e) { return null; } }
  function saveBest(s) { try { const b = best(); if (!b || s > b.score) localStorage.setItem(KEY, JSON.stringify({ score: s, of: QUIZ.length })); } catch (e) {} }
  function slideRef(q) {
    if (!q.slide) return "";
    return QMETA.slides ? `<a href="${QMETA.slides}#page=${q.slide}" target="_blank" rel="noopener">Slide ${q.slide}</a>` : `Slide ${q.slide}`;
  }
  function animRef(q) { return q.anim ? ` · <a href="${QMETA.root}${q.anim}">Try the animation</a>` : ""; }

  function start(reshuffle) {
    // first round keeps the order of the slides; "Try again" reshuffles the questions as well as the options
    order = (reshuffle ? shuffle(QUIZ.map((_, k) => k)) : QUIZ.map((_, k) => k)).map(k => {
      const q = QUIZ[k], idx = q.options.map((_, j) => j);
      return { k, opts: q.type === "tf" ? idx : shuffle(idx) };
    });
    i = 0; score = 0; missed = []; show();
  }

  function show() {
    answered = false;
    const { k, opts } = order[i], q = QUIZ[k];
    app.innerHTML = `
      <div class="qhead"><span>Question ${i + 1} of ${order.length}</span><span>Score ${score}</span></div>
      <div class="qbar" aria-hidden="true"><i style="width:${100 * i / order.length}%"></i></div>
      <h2 class="qtext" id="qtext" tabindex="-1">${fmt(q.q)}</h2>
      ${q.img ? `<figure class="qimg"><button type="button" class="qzoom" title="Enlarge the picture"><img src="${q.img}" alt="${esc(q.alt || "")}"></button><figcaption>Click or tap the picture to enlarge it.</figcaption></figure>` : ""}
      <div class="qopts" role="group" aria-labelledby="qtext">
        ${opts.map((j, n) => `<button type="button" class="qopt" data-j="${j}"><span class="qkey">${q.type === "tf" ? "" : "ABCD"[n]}</span><span>${fmt(q.options[j])}</span></button>`).join("")}
      </div>
      <div class="qfb" aria-live="polite"></div>
      <div class="qnext"></div>`;
    app.querySelectorAll(".qopt").forEach(b => b.onclick = () => pick(+b.dataset.j));
    const z = $(".qzoom"); if (z) z.onclick = () => zoom(q.img, q.alt);
    $("#qtext").focus({ preventScroll: true });
  }

  function zoom(src, alt) {
    const o = document.createElement("div"); o.className = "qlight"; o.setAttribute("role", "dialog"); o.setAttribute("aria-label", "Enlarged picture");
    o.innerHTML = `<div class="qlbox"><img src="${src}" alt="${esc(alt || "")}"></div><p class="qlhint">Scroll sideways to see the whole picture.</p><button type="button" class="btn">Close</button>`;
    const close = () => { o.remove(); document.removeEventListener("keydown", key, true); const z = $(".qzoom"); z && z.focus(); };
    const key = e => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); close(); } };
    o.onclick = e => { if (!e.target.closest(".qlbox")) close(); }; document.addEventListener("keydown", key, true);
    document.body.appendChild(o); o.querySelector("button").focus();
  }

  function pick(j) {
    if (answered) return; answered = true;
    const { k } = order[i], q = QUIZ[k], ok = j === q.answer;
    if (ok) score++; else missed.push(k);
    app.querySelectorAll(".qopt").forEach(b => {
      const jj = +b.dataset.j; b.disabled = true;
      if (jj === q.answer) b.classList.add("right");
      else if (jj === j) b.classList.add("wrong");
    });
    $(".qfb").innerHTML = `<div class="fb ${ok ? "good" : "bad"}"><b>${ok ? "Correct." : "Not quite."}</b> ${fmt(q.explain)}
      <div class="fbref">${slideRef(q)}${animRef(q)}</div></div>`;
    $(".qhead span:last-child").textContent = "Score " + score;
    const last = i === order.length - 1;
    $(".qnext").innerHTML = `<button type="button" class="btn" id="qgo">${last ? "See your score" : "Next question →"}</button>`;
    $("#qgo").onclick = () => { if (last) finish(); else { i++; show(); } };
    $("#qgo").focus({ preventScroll: true });
  }

  function finish() {
    saveBest(score);
    const n = order.length, b = best(), pct = score / n;
    const msg = pct === 1 ? "Full marks: you have the key ideas of this part." : pct >= .75 ? "Well done. Look over the questions you missed below." :
      pct >= .5 ? "A good start. Revisit the slides for the questions you missed, then try again." : "Go back through the slides and animations for these ideas, then try again.";
    app.innerHTML = `
      <div class="qdone"><p class="kicker">Your score</p><p class="big">${score} <span>/ ${n}</span></p><p>${msg}</p>
      ${b ? `<p class="best">Your best on this device: ${b.score} / ${b.of}</p>` : ""}</div>
      ${missed.length ? `<h2 class="qrev">Questions to review</h2>` + missed.map(k => { const q = QUIZ[k]; return `<div class="card qmiss"><p class="qmq">${fmt(q.q)}</p>
        <p><b>Answer:</b> ${fmt(q.options[q.answer])}</p><p class="qme">${fmt(q.explain)}</p><div class="fbref">${slideRef(q)}${animRef(q)}</div></div>`; }).join("") : ""}
      <div class="btnrow qend"><button type="button" class="btn" id="qagain">Try again (new order)</button>
      <a class="btn ghost" href="index.html">All quizzes</a></div>`;
    $("#qagain").onclick = () => start(true);
    window.scrollTo({ top: app.offsetTop - 20, behavior: "smooth" });
  }

  document.addEventListener("keydown", e => {
    if (e.target.closest && e.target.closest("input,textarea")) return;
    if (document.querySelector(".qlight")) return;
    const opts = [...app.querySelectorAll(".qopt")];
    if (!answered && opts.length) {
      const n = "abcd".indexOf(e.key.toLowerCase()), d = "1234".indexOf(e.key), t = e.key.toLowerCase() === "t" ? 0 : e.key.toLowerCase() === "f" ? 1 : -1;
      const m = n >= 0 ? n : d >= 0 ? d : t;
      if (m >= 0 && opts[m]) { e.preventDefault(); opts[m].click(); }
    }
  });
  start(false);
})();
