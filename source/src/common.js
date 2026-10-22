/* Shared helpers for the KKKC6353 animations: theme tokens, controls, plots, animation loop. */
const NX = (() => {
  const root = document.documentElement;
  let tok = {};
  function readTokens() {
    const cs = getComputedStyle(root);
    ["bg","panel","ink","muted","line","grid","navy","blue","rust","green","gold","violet","electron","hole",
     "oxide","si","nplus","pbody","metal","depl","chip"].forEach(k => tok[k] = cs.getPropertyValue("--" + k).trim());
    return tok;
  }
  readTokens();
  const redrawers = new Set();
  function onRedraw(fn) { redrawers.add(fn); }
  function redrawAll() { readTokens(); redrawers.forEach(f => { try { f(); } catch (e) { console.error(e); } }); }
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", redrawAll);
  let rT; addEventListener("resize", () => { clearTimeout(rT); rT = setTimeout(redrawAll, 80); });

  /* ---------- number formatting ---------- */
  function fmt(v, d = 2) {
    if (!isFinite(v)) return "—";
    const a = Math.abs(v);
    if (a !== 0 && (a < 1e-2 || a >= 1e4)) {
      const e = Math.floor(Math.log10(a)), m = v / Math.pow(10, e);
      return m.toFixed(1) + "×10" + sup(e);
    }
    return v.toFixed(d);
  }
  function sup(n) { const s = "⁰¹²³⁴⁵⁶⁷⁸⁹"; return String(n).replace("-", "⁻").replace(/\d/g, c => s[c]); }
  function si(v, unit, d = 3) {
    if (!isFinite(v) || v === 0) return (v === 0 ? "0 " : "— ") + unit;
    if (Math.abs(v) < 1e-15) return "< 1 f" + unit;
    const p = ["f","p","n","µ","m","","k","M","G"]; let e = Math.floor(Math.log10(Math.abs(v)) / 3);
    e = Math.max(-5, Math.min(3, e));
    const m = v / Math.pow(1000, e);
    return (+m.toPrecision(d)) + " " + p[e + 5] + unit;
  }

  /* ---------- controls ---------- */
  function slider(host, o) {
    const id = "s_" + o.id;
    const w = document.createElement("div"); w.className = "ctl";
    w.innerHTML = `<label for="${id}"><b>${o.label}</b><output id="${id}_o"></output></label>
      <input type="range" id="${id}" min="${o.min}" max="${o.max}" step="${o.step}" value="${o.value}">
      ${o.hint ? `<div class="hint">${o.hint}</div>` : ""}`;
    host.appendChild(w);
    const inp = w.querySelector("input"), out = w.querySelector("output");
    const show = () => { out.textContent = (o.fmt ? o.fmt(+inp.value) : (+inp.value).toFixed(o.dp ?? 2) + (o.unit ? " " + o.unit : "")); };
    inp.addEventListener("input", () => { show(); o.on && o.on(+inp.value); });
    show();
    return { get value() { return +inp.value; }, set value(v) { inp.value = v; show(); }, input: inp, el: w };
  }
  function seg(host, o) {
    const w = document.createElement("div"); w.className = "ctl";
    w.innerHTML = `<label><b>${o.label}</b></label><div class="seg" role="group" aria-label="${o.label}"></div>${o.hint ? `<div class="hint">${o.hint}</div>` : ""}`;
    const g = w.querySelector(".seg"); let val = o.value;
    const btns = o.options.map(([v, t]) => {
      const b = document.createElement("button"); b.type = "button"; b.textContent = t;
      b.setAttribute("aria-pressed", v === val); b.onclick = () => { set(v); o.on && o.on(v); };
      g.appendChild(b); return [v, b];
    });
    function set(v) { val = v; btns.forEach(([k, b]) => b.setAttribute("aria-pressed", k === v)); }
    host.appendChild(w);
    return { get value() { return val; }, set value(v) { set(v); }, el: w };
  }

  /* ---------- "More detail" toggle: shows every element marked .adv ---------- */
  function more(host, o = {}) {
    const b = document.createElement("button"); b.type = "button"; b.className = "more-btn";
    const set = on => { document.body.classList.toggle("more", on); b.setAttribute("aria-expanded", on); b.textContent = on ? "Show less detail" : "More detail: numbers and graphs"; };
    b.onclick = () => { set(!document.body.classList.contains("more")); redrawAll(); o.on && o.on(); };
    set(false); host.appendChild(b); return b;
  }

  /* ---------- canvas with DPR handling ---------- */
  function fitCanvas(cv, aspect) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
    const w = Math.max(200, cv.clientWidth || cv.parentElement.clientWidth);
    const h = Math.round(w / aspect);
    if (cv.width !== Math.round(w * dpr) || cv.height !== Math.round(h * dpr)) {
      cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); cv.style.height = h + "px";
    }
    const g = cv.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { g, w, h };
  }

  /* ---------- 2-D plot ---------- */
  function niceTicks(a, b, n = 5) {
    const span = b - a, step0 = span / n, mag = Math.pow(10, Math.floor(Math.log10(step0)));
    const r = step0 / mag, step = (r < 1.5 ? 1 : r < 3.5 ? 2 : r < 7.5 ? 5 : 10) * mag;
    const t = []; for (let v = Math.ceil(a / step - 1e-9) * step; v <= b + step * 1e-6; v += step) t.push(+v.toFixed(12));
    return t;
  }
  class Plot {
    constructor(cv, o) { this.cv = cv; this.o = Object.assign({ aspect: 1.45, m: [14, 16, 44, 58] }, o); }
    setX(a, b) { this.o.x = [a, b]; } setY(a, b) { this.o.y = [a, b]; }
    begin() {
      const { g, w, h } = fitCanvas(this.cv, this.o.aspect); this.g = g; this.w = w; this.h = h;
      const [mt, mr, mb, ml] = this.o.m; this.L = ml; this.R = w - mr; this.T = mt; this.B = h - mb;
      g.clearRect(0, 0, w, h); g.fillStyle = tok.panel; g.fillRect(0, 0, w, h);
      return this;
    }
    tx(v) { const [a, b] = this.o.x; const f = this.o.xlog ? (Math.log10(v) - Math.log10(a)) / (Math.log10(b) - Math.log10(a)) : (v - a) / (b - a); return this.L + f * (this.R - this.L); }
    ty(v) { const [a, b] = this.o.y; const f = this.o.ylog ? (Math.log10(Math.max(v, 1e-300)) - Math.log10(a)) / (Math.log10(b) - Math.log10(a)) : (v - a) / (b - a); return this.B - f * (this.B - this.T); }
    axes() {
      const g = this.g, o = this.o; g.save();
      g.font = "12px system-ui,sans-serif"; g.lineWidth = 1;
      const ticks = (lo, hi, log) => log ? (() => { const t = []; for (let e = Math.ceil(Math.log10(lo) - 1e-9); e <= Math.floor(Math.log10(hi) + 1e-9); e++) t.push(Math.pow(10, e)); return t; })() : niceTicks(lo, hi, o.nt || 5);
      const xt = ticks(o.x[0], o.x[1], o.xlog), yt0 = ticks(o.y[0], o.y[1], o.ylog);
      const yt = o.ylog && yt0.length > 8 ? yt0.filter((v, i) => i % 2 === (yt0.length % 2 ? 0 : 1)) : yt0;
      g.strokeStyle = tok.grid;
      xt.forEach(v => { const X = this.tx(v); g.beginPath(); g.moveTo(X, this.T); g.lineTo(X, this.B); g.stroke(); });
      yt.forEach(v => { const Y = this.ty(v); g.beginPath(); g.moveTo(this.L, Y); g.lineTo(this.R, Y); g.stroke(); });
      g.strokeStyle = tok.muted; g.beginPath(); g.moveTo(this.L, this.T); g.lineTo(this.L, this.B); g.lineTo(this.R, this.B); g.stroke();
      g.fillStyle = tok.muted; g.textAlign = "center"; g.textBaseline = "top";
      const lab = (v, log) => log ? "10" + sup(Math.round(Math.log10(v))) : (o.tickfmt ? o.tickfmt(v) : (+v.toPrecision(6)).toString());
      if (!o.noxt) xt.forEach(v => g.fillText(lab(v, o.xlog), this.tx(v), this.B + 5));
      g.textAlign = "right"; g.textBaseline = "middle";
      yt.forEach(v => g.fillText(lab(v, o.ylog), this.L - 6, this.ty(v)));
      g.fillStyle = tok.ink; g.font = "12.5px system-ui,sans-serif";
      if (o.xlabel) { g.textAlign = "center"; g.textBaseline = "bottom"; g.fillText(o.xlabel, (this.L + this.R) / 2, this.h - 4); }
      if (o.ylabel) { g.save(); g.translate(13, (this.T + this.B) / 2); g.rotate(-Math.PI / 2); g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(o.ylabel, 0, 0); g.restore(); }
      g.restore(); return this;
    }
    clip(fn) { const g = this.g; g.save(); g.beginPath(); g.rect(this.L, this.T, this.R - this.L, this.B - this.T); g.clip(); fn(g); g.restore(); return this; }
    line(xs, ys, s = {}) {
      return this.clip(g => {
        g.strokeStyle = s.color || tok.ink; g.lineWidth = s.width || 2; g.setLineDash(s.dash || []); g.lineJoin = "round";
        g.beginPath(); let pen = false;
        for (let i = 0; i < xs.length; i++) {
          const y = ys[i]; if (!isFinite(y) || (this.o.ylog && y <= 0)) { pen = false; continue; }
          const X = this.tx(xs[i]), Y = Math.max(-1e4, Math.min(1e4, this.ty(y)));
          pen ? g.lineTo(X, Y) : g.moveTo(X, Y); pen = true;
        }
        g.stroke();
      });
    }
    fn(f, s = {}, n = 240) {
      const [a, b] = this.o.x, xs = [], ys = [];
      for (let i = 0; i <= n; i++) { const x = this.o.xlog ? a * Math.pow(b / a, i / n) : a + (b - a) * i / n; xs.push(x); ys.push(f(x)); }
      return this.line(xs, ys, s);
    }
    point(x, y, s = {}) { return this.clip(g => { g.fillStyle = s.color || tok.rust; g.strokeStyle = tok.panel; g.lineWidth = 2; g.beginPath(); g.arc(this.tx(x), this.ty(y), s.r || 5, 0, 7); g.fill(); g.stroke(); }); }
    vline(x, s = {}) { return this.clip(g => { g.strokeStyle = s.color || tok.muted; g.lineWidth = s.width || 1.2; g.setLineDash(s.dash || [4, 4]); const X = this.tx(x); g.beginPath(); g.moveTo(X, this.T); g.lineTo(X, this.B); g.stroke(); if (s.label) { g.setLineDash([]); g.fillStyle = s.color || tok.muted; g.font = "11.5px system-ui"; g.textAlign = s.align || "left"; g.textBaseline = "top"; g.fillText(s.label, X + (s.align === "right" ? -4 : 4), this.T + 4 + (s.dy || 0)); } }); }
    hline(y, s = {}) { return this.clip(g => { g.strokeStyle = s.color || tok.muted; g.lineWidth = s.width || 1.2; g.setLineDash(s.dash || [4, 4]); const Y = this.ty(y); g.beginPath(); g.moveTo(this.L, Y); g.lineTo(this.R, Y); g.stroke(); if (s.label) { g.setLineDash([]); g.fillStyle = s.color || tok.muted; g.font = "11.5px system-ui"; g.textAlign = s.align || "right"; g.textBaseline = "bottom"; g.fillText(s.label, s.align === "left" ? this.L + 4 : this.R - 4, Y - 3); } }); }
    band(x0, x1, color, alpha = .12) { return this.clip(g => { g.globalAlpha = alpha; g.fillStyle = color; g.fillRect(this.tx(x0), this.T, this.tx(x1) - this.tx(x0), this.B - this.T); }); }
    text(x, y, t, s = {}) { const g = this.g; g.save(); g.font = (s.bold ? "600 " : "") + (s.size || 12) + "px system-ui,sans-serif"; g.fillStyle = s.color || tok.ink; g.textAlign = s.align || "left"; g.textBaseline = s.base || "middle"; g.fillText(t, this.tx(x) + (s.dx || 0), this.ty(y) + (s.dy || 0)); g.restore(); return this; }
  }

  /* ---------- drawing utilities for device pictures ---------- */
  function rect(g, x, y, w, h, fill, stroke) { g.fillStyle = fill; g.fillRect(x, y, w, h); if (stroke) { g.strokeStyle = stroke; g.lineWidth = 1; g.strokeRect(x + .5, y + .5, w - 1, h - 1); } }
  function label(g, t, x, y, o = {}) { g.save(); g.font = (o.bold ? "600 " : "") + (o.size || 13) + "px system-ui,sans-serif"; g.fillStyle = o.color || tok.ink; g.textAlign = o.align || "center"; g.textBaseline = o.base || "middle"; g.fillText(t, x, y); g.restore(); }
  function arrow(g, x0, y0, x1, y1, color, w = 2, head = 8) {
    g.save(); g.strokeStyle = color; g.fillStyle = color; g.lineWidth = w; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
    const a = Math.atan2(y1 - y0, x1 - x0); g.beginPath(); g.moveTo(x1, y1);
    g.lineTo(x1 - head * Math.cos(a - .4), y1 - head * Math.sin(a - .4)); g.lineTo(x1 - head * Math.cos(a + .4), y1 - head * Math.sin(a + .4)); g.closePath(); g.fill(); g.restore();
  }
  function dot(g, x, y, r, fill, sign) { g.fillStyle = fill; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); if (sign && r >= 4) { g.strokeStyle = "#fff"; g.lineWidth = 1.3; g.beginPath(); g.moveTo(x - r * .55, y); g.lineTo(x + r * .55, y); if (sign === "+") { g.moveTo(x, y - r * .55); g.lineTo(x, y + r * .55); } g.stroke(); } }

  /* ---------- animation loop that pauses off-screen / when paused ---------- */
  function loop(step) {
    let last = 0, running = true, visible = true;
    const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const st = { get running() { return running; }, set running(v) { running = v; } };
    if (reduce) running = false;
    function f(t) { const dt = Math.min(0.05, (t - last) / 1000 || 0); last = t; if (running && visible && !document.hidden) step(dt); requestAnimationFrame(f); }
    requestAnimationFrame(f);
    return st;
  }

  /* ---------- page chrome: text size, theme, full screen ---------- */
  function chrome() {
    const big = document.getElementById("tbig"), th = document.getElementById("ttheme"), fs = document.getElementById("tfs");
    try { if (localStorage.getItem("nx-big") === "1") document.body.classList.add("big"); const t = localStorage.getItem("nx-theme"); if (t) root.dataset.theme = t; } catch (e) {}
    big && (big.onclick = () => { const on = document.body.classList.toggle("big"); try { localStorage.setItem("nx-big", on ? "1" : "0"); } catch (e) {} redrawAll(); });
    th && (th.onclick = () => { const dark = getComputedStyle(root).getPropertyValue("color-scheme").trim() === "dark"; root.dataset.theme = dark ? "light" : "dark"; try { localStorage.setItem("nx-theme", root.dataset.theme); } catch (e) {} redrawAll(); });
    const lab = document.querySelector(".lab");
    fs && lab && lab.requestFullscreen ? (fs.onclick = () => document.fullscreenElement ? document.exitFullscreen() : lab.requestFullscreen()) : fs && (fs.hidden = true);
    document.addEventListener("fullscreenchange", () => setTimeout(redrawAll, 60));
    readTokens();
  }
  document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", chrome) : chrome();

  /* ---------- physical constants (SI unless stated) ---------- */
  const C = { q: 1.602e-19, k: 1.381e-23, eps0: 8.854e-12, epsSi: 11.7 * 8.854e-12, epsOx: 3.9 * 8.854e-12, T: 300 };
  C.Vt = C.k * C.T / C.q;

  return { tok, readTokens, onRedraw, redrawAll, fmt, si, sup, slider, seg, more, fitCanvas, Plot, rect, label, arrow, dot, loop, C };
})();
