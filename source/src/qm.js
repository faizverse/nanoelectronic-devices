/* Quantum-mechanics helpers for the Lecture 2 animations (all energies in eV, lengths in nm). */
const QM = (() => {
  const HB2_2M0 = 0.0380998;            // ħ²/2m0 in eV·nm²
  const h_c = 1239.84;                  // hc in eV·nm
  const kT300 = 0.025852;

  // ground and excited levels of an infinite well of width L (nm), effective mass m (in m0)
  const Einf = (n, L, m) => HB2_2M0 * Math.PI * Math.PI * n * n / (m * L * L);

  // bound states of a symmetric finite square well (same mass inside and out), by bisection on
  // the even/odd matching conditions.  Returns [{E, parity, k, kap}], E measured from the well bottom.
  function finiteWell(L, V0, m) {
    const out = [], a = L / 2;
    const k = E => Math.sqrt(m * E / HB2_2M0), kap = E => Math.sqrt(m * (V0 - E) / HB2_2M0);
    const fe = E => k(E) * Math.tan(k(E) * a) - kap(E);          // even
    const fo = E => -k(E) / Math.tan(k(E) * a) - kap(E);         // odd
    // search between successive poles of tan / cot
    const u0 = a * Math.sqrt(m * V0 / HB2_2M0), nmax = Math.floor(2 * u0 / Math.PI) + 1;
    for (let n = 0; n < nmax; n++) {
      const parity = n % 2 === 0 ? "even" : "odd", f = parity === "even" ? fe : fo;
      // k·a lies in (nπ/2, (n+1)π/2)
      const kaLo = n * Math.PI / 2 + 1e-9, kaHi = Math.min((n + 1) * Math.PI / 2 - 1e-9, u0 - 1e-12);
      if (kaHi <= kaLo) break;
      const E = ka => HB2_2M0 * (ka / a) * (ka / a) / m;
      let lo = E(kaLo), hi = E(kaHi), flo = f(lo), fhi = f(hi);
      if (!(flo * fhi <= 0)) continue;
      for (let i = 0; i < 80; i++) { const mid = (lo + hi) / 2, fm = f(mid); if (fm * flo <= 0) { hi = mid; fhi = fm; } else { lo = mid; flo = fm; } }
      const Es = (lo + hi) / 2; out.push({ E: Es, parity, k: k(Es), kap: kap(Es) });
    }
    return out;
  }
  // normalised wavefunction of a finite-well state at position x (nm, centred on the well)
  function psiFinite(st, L, x) {
    const a = L / 2, { k, kap, parity } = st;
    const inside = parity === "even" ? Math.cos(k * x) : Math.sin(k * x);
    if (Math.abs(x) <= a) return inside / norm(st, L);
    const edge = parity === "even" ? Math.cos(k * a) : Math.sin(k * a) * Math.sign(x);
    return edge * Math.exp(-kap * (Math.abs(x) - a)) / norm(st, L);
  }
  function norm(st, L) {
    if (st._n) return st._n;
    const a = L / 2, { k, kap, parity } = st;
    const inside = parity === "even" ? a + Math.sin(2 * k * a) / (2 * k) : a - Math.sin(2 * k * a) / (2 * k);
    const edge = parity === "even" ? Math.cos(k * a) : Math.sin(k * a);
    const outside = 2 * edge * edge / (2 * kap);
    return (st._n = Math.sqrt(inside + outside));
  }

  // eigenstates of an arbitrary 1-D potential V[i] on a uniform grid dx (nm), effective mass m:
  // Sturm-sequence bisection for eigenvalues below Emax, inverse iteration for vectors.
  function solve1D(V, dx, m, Emax, nmax = 8) {
    const N = V.length, t = HB2_2M0 / (m * dx * dx);
    const d = V.map(v => v + 2 * t), e = -t;
    const count = x => { let c = 0, q = d[0] - x; if (q < 0) c++; for (let i = 1; i < N; i++) { q = d[i] - x - e * e / (q === 0 ? 1e-300 : q); if (q < 0) c++; } return c; };
    const Vmin = Math.min(...V), nb = Math.min(nmax, count(Emax)), res = [];
    for (let j = 0; j < nb; j++) {
      let lo = Vmin, hi = Emax;
      for (let it = 0; it < 60; it++) { const mid = (lo + hi) / 2; if (count(mid) > j) hi = mid; else lo = mid; }
      const E = (lo + hi) / 2 + 1e-12;
      let v = new Float64Array(N).fill(1);
      for (let rep = 0; rep < 3; rep++) {            // solve (H - E) y = v with the Thomas algorithm
        const c = new Float64Array(N), y = new Float64Array(N); let b = d[0] - E;
        c[0] = e / b; y[0] = v[0] / b;
        for (let i = 1; i < N; i++) { b = d[i] - E - e * c[i - 1]; c[i] = e / b; y[i] = (v[i] - e * y[i - 1]) / b; }
        for (let i = N - 2; i >= 0; i--) y[i] -= c[i] * y[i + 1];
        let s = 0; for (let i = 0; i < N; i++) s += y[i] * y[i]; s = Math.sqrt(s * dx);
        for (let i = 0; i < N; i++) v[i] = y[i] / s;
      }
      let mx = 0, im = 0; for (let i = 0; i < N; i++) if (Math.abs(v[i]) > mx) { mx = Math.abs(v[i]); im = i; }
      if (v[im] < 0) for (let i = 0; i < N; i++) v[i] = -v[i];
      res.push({ E, psi: v });
    }
    return res;
  }

  // approximate sRGB colour of a wavelength in nm; infrared and ultraviolet shown dimmed
  function wlColor(wl, alpha = 1) {
    const w = Math.max(380, Math.min(780, wl)); let r, g, b;
    if (w < 440) { r = -(w - 440) / 60; g = 0; b = 1; } else if (w < 490) { r = 0; g = (w - 440) / 50; b = 1; }
    else if (w < 510) { r = 0; g = 1; b = -(w - 510) / 20; } else if (w < 580) { r = (w - 510) / 70; g = 1; b = 0; }
    else if (w < 645) { r = 1; g = -(w - 645) / 65; b = 0; } else { r = 1; g = 0; b = 0; }
    let f = w < 420 ? 0.3 + 0.7 * (w - 380) / 40 : w > 700 ? 0.3 + 0.7 * (780 - w) / 80 : 1;
    if (wl > 780) f = 0.28; if (wl < 380) f = 0.3;
    const c = v => Math.round(255 * Math.pow(Math.max(0, v * f), 0.8));
    return `rgba(${c(r)},${c(g)},${c(b)},${alpha})`;
  }
  const band = wl => wl < 380 ? "ultraviolet" : wl < 450 ? "violet" : wl < 490 ? "blue" : wl < 520 ? "cyan" : wl < 565 ? "green" : wl < 590 ? "yellow" : wl < 625 ? "orange" : wl <= 750 ? "red" : wl < 1400 ? "near-infrared" : wl < 3000 ? "short-wave infrared" : "mid-infrared";

  return { HB2_2M0, h_c, kT300, Einf, finiteWell, psiFinite, solve1D, wlColor, band };
})();
