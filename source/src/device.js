/* Shared n-MOSFET cross-section drawing. All geometry in canvas pixels, derived from w and h. */
const DEV = (() => {
  // o: {VG, VD, qn(f) -> channel thickness 0..1 along f = 0..1 (source->drain), pinch (0..1 position where channel ends),
  //     dep(f) -> depletion depth 0..1 under the gate, dDrain (0..1 extra drain depletion), labels}
  function geom(w, h) {
    const y0 = Math.round(h * 0.36), x0 = w * 0.05, x1 = w * 0.95;
    const sE = w * 0.27, dS = w * 0.73;             // source edge, drain edge (channel = sE..dS)
    const jd = h * 0.2;                              // junction depth
    return { w, h, y0, x0, x1, sE, dS, jd, tox: Math.max(6, h * 0.025), tg: h * 0.1, L: dS - sE, fx: f => sE + f * (dS - sE) };
  }
  function draw(g, w, h, o) {
    const t = NX.tok, G = geom(w, h), { y0, sE, dS, jd, tox, tg } = G;
    g.clearRect(0, 0, w, h); g.fillStyle = t.panel; g.fillRect(0, 0, w, h);
    // body
    NX.rect(g, G.x0, y0, G.x1 - G.x0, h * 0.9 - y0, t.pbody);
    // depletion under the gate and around the junctions
    const dmax = h * 0.3;
    g.fillStyle = t.depl; g.beginPath(); g.moveTo(sE - jd * 0.5, y0);
    for (let i = 0; i <= 60; i++) { const f = i / 60; g.lineTo(G.fx(f), y0 + dmax * (o.dep ? o.dep(f) : 0.5)); }
    g.lineTo(dS + jd * 0.5, y0); g.closePath(); g.fill();
    const dd = (o.dDrain ?? 0.3) * h * 0.22, ds = (o.dSource ?? 0.25) * h * 0.22;
    g.beginPath(); g.ellipse(dS + (G.x1 - dS) / 2, y0, (G.x1 - dS) / 2 + dd * .9 + 2, jd + dd, 0, 0, Math.PI); g.fill();
    g.beginPath(); g.ellipse(G.x0 + (sE - G.x0) / 2, y0, (sE - G.x0) / 2 + ds * .9 + 2, jd + ds, 0, 0, Math.PI); g.fill();
    // n+ source and drain (rounded wells)
    g.fillStyle = t.nplus;
    g.beginPath(); g.ellipse(G.x0 + (sE - G.x0) / 2, y0, (sE - G.x0) / 2 + 2, jd, 0, 0, Math.PI); g.fill();
    g.beginPath(); g.ellipse(dS + (G.x1 - dS) / 2, y0, (G.x1 - dS) / 2 + 2, jd, 0, 0, Math.PI); g.fill();
    g.fillRect(G.x0, y0 - 1, G.x1 - G.x0, 1);
    // oxide and gate
    NX.rect(g, sE - 6, y0 - tox, dS - sE + 12, tox, t.oxide);
    NX.rect(g, sE - 6, y0 - tox - tg, dS - sE + 12, tg, t.metal);
    // inversion channel
    if (o.qn) {
      const pin = o.pinch ?? 1, th = Math.max(5, h * 0.03);
      g.fillStyle = t.electron; g.globalAlpha = .55; g.beginPath(); g.moveTo(sE - 2, y0);
      for (let i = 0; i <= 80; i++) { const f = pin * i / 80; g.lineTo(G.fx(f), y0 + th * o.qn(f)); }
      g.lineTo(G.fx(pin), y0); g.closePath(); g.fill(); g.globalAlpha = 1;
    }
    // contacts and labels
    const lab = (txt, x, y, col) => NX.label(g, txt, x, y, { bold: true, size: Math.max(12, h * 0.045), color: col || t.ink });
    NX.rect(g, G.x0 + 10, y0 - 10, sE - G.x0 - 28, 10, t.metal); NX.rect(g, dS + 18, y0 - 10, G.x1 - dS - 28, 10, t.metal);
    lab("n⁺ source", G.x0 + (sE - G.x0) / 2, y0 + jd * 0.5); lab("n⁺ drain", dS + (G.x1 - dS) / 2, y0 + jd * 0.5);
    lab("p-type body", (sE + dS) / 2, h * 0.84, t.muted);
    NX.label(g, "gate", (sE + dS) / 2, y0 - tox - tg / 2, { color: "#fff", bold: true, size: Math.max(12, h * 0.042) });
    if (o.vlabels !== false) {
      const s = Math.max(12, h * 0.042);
      NX.label(g, `S  0 V`, G.x0 + (sE - G.x0) / 2 - 8, y0 - 22, { size: s, color: t.muted });
      NX.label(g, `D  ${o.VD.toFixed(2)} V`, dS + (G.x1 - dS) / 2 + 8, y0 - 22, { size: s, color: t.rust, bold: true });
      NX.label(g, `G  ${o.VG.toFixed(2)} V`, (sE + dS) / 2, y0 - tox - tg - 14, { size: s, color: t.rust, bold: true });
    }
    return G;
  }
  return { geom, draw };
})();
