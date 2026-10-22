/* Shared models for the KKKC6353 Lecture 4 animations (made for this course).
   1. Graphene nearest-neighbour tight binding and nanotube zone folding (Saito-Dresselhaus).
   2. Top-of-the-barrier ballistic CNTFET (after Rahman, Guo, Datta and Lundstrom, IEEE TED 2003).
   3. Schottky-barrier CNTFET: Landauer current with WKB tunnelling through the tube's band gap.
   Units: nm, eV, V, A. */
const L4 = (() => {
  const ACC = 0.142, A = Math.sqrt(3) * ACC, HBARVF0 = 1.5 * ACC; // hbar*vF = 1.5*acc*gamma0 (eV nm)
  const a1 = [A * Math.sqrt(3) / 2, A / 2], a2 = [A * Math.sqrt(3) / 2, -A / 2];
  const b1 = [2 * Math.PI / A / Math.sqrt(3), 2 * Math.PI / A], b2 = [2 * Math.PI / A / Math.sqrt(3), -2 * Math.PI / A];
  const gcd = (x, y) => { x = Math.abs(x); y = Math.abs(y); while (y) [x, y] = [y, x % y]; return x; };
  function eg(kx, ky, g0) {            // |E| of the graphene pi bands
    const p1 = kx * a1[0] + ky * a1[1], p2 = kx * a2[0] + ky * a2[1];
    const re = 1 + Math.cos(p1) + Math.cos(p2), im = Math.sin(p1) + Math.sin(p2);
    return g0 * Math.sqrt(re * re + im * im);
  }
  function tube(n, m) {
    const Ch = [n * a1[0] + m * a2[0], n * a1[1] + m * a2[1]], L = Math.hypot(Ch[0], Ch[1]);
    const dR = gcd(2 * n + m, 2 * m + n), t1 = (2 * m + n) / dR, t2 = -(2 * n + m) / dR, N = 2 * (n * n + m * m + n * m) / dR;
    const T = [t1 * a1[0] + t2 * a2[0], t1 * a1[1] + t2 * a2[1]], Tl = Math.hypot(T[0], T[1]);
    const K1 = [(-t2 * b1[0] + t1 * b2[0]) / N, (-t2 * b1[1] + t1 * b2[1]) / N];
    const K2 = [(m * b1[0] - n * b2[0]) / N, (m * b1[1] - n * b2[1]) / N], K2l = Math.hypot(K2[0], K2[1]);
    return { n, m, Ch, d: L / Math.PI, theta: Math.atan2(Math.sqrt(3) * m, 2 * n + m) * 180 / Math.PI, N, T, Tl, K1, K2u: [K2[0] / K2l, K2[1] / K2l],
      metallic: ((n - m) % 3 + 3) % 3 === 0, atoms: 2 * N };
  }
  // subband energies E_mu(k), k in (-pi/T, pi/T); returns {k:[], E:[[...] per mu]}
  function subbands(t, g0, nk = 161) {
    const k = [], E = [];
    for (let i = 0; i < nk; i++) k.push(-Math.PI / t.Tl + 2 * Math.PI / t.Tl * i / (nk - 1));
    for (let mu = 0; mu < t.N; mu++) {
      const row = new Float64Array(nk);
      for (let i = 0; i < nk; i++) row[i] = eg(mu * t.K1[0] + t.K2u[0] * k[i], mu * t.K1[1] + t.K2u[1] * k[i], g0);
      E.push(row);
    }
    return { k, E };
  }
  // subband minima (sorted) from a fine 1D minimisation along each line
  function edges(t, g0) {
    const out = [];
    for (let mu = 0; mu < t.N; mu++) {
      let best = 1e9, nk = 400;
      for (let i = 0; i < nk; i++) { const k = -Math.PI / t.Tl + 2 * Math.PI / t.Tl * i / nk; const e = eg(mu * t.K1[0] + t.K2u[0] * k, mu * t.K1[1] + t.K2u[1] * k, g0); if (e < best) best = e; }
      out.push(best);
    }
    return out.sort((x, y) => x - y);
  }
  // DOS per unit length (states / eV / nm), both signs of E, histogram + smoothing
  function dos(t, g0, emax = 3, nb = 300, nk = 2400) {
    const H = new Float64Array(nb), dE = 2 * emax / nb, dk = 2 * Math.PI / t.Tl / nk;
    for (let mu = 0; mu < t.N; mu++) for (let i = 0; i < nk; i++) {
      const k = -Math.PI / t.Tl + dk * (i + 0.5), e = eg(mu * t.K1[0] + t.K2u[0] * k, mu * t.K1[1] + t.K2u[1] * k, g0);
      for (const s of [e, -e]) { const j = Math.floor((s + emax) / dE); if (j >= 0 && j < nb) H[j] += dk / (2 * Math.PI) * 2 / dE; }
    }
    const S = new Float64Array(nb); for (let j = 0; j < nb; j++) { let a = 0, w = 0; for (let q = -2; q <= 2; q++) { const jj = j + q; if (jj >= 0 && jj < nb) { const c = 3 - Math.abs(q); a += H[jj] * c; w += c; } } S[j] = a / w; }
    const e = []; for (let j = 0; j < nb; j++) e.push(-emax + dE * (j + 0.5));
    return { e, D: S };
  }

  /* ---------- ballistic top-of-the-barrier CNTFET ---------- */
  const q = 1.602e-19, h = 6.626e-34, EPS0 = 8.854e-12;
  const cins = (d, tox, kappa) => 2 * Math.PI * EPS0 * kappa / Math.log((2 * tox + d) / d); // F/m
  const lse = x => x > 30 ? x : Math.log1p(Math.exp(x));
  function ballistic(VG, VD, o) {      // o: {d, tox, kappa, T, VT0, nsub, aG, aD} -> {I, U, n, Cq}
    const kT = 8.617e-5 * o.T, Eg = 2 * ACC * o.g0 / o.d, D1 = Eg / 2, Cins = cins(o.d, o.tox, o.kappa);
    const aG = o.aG ?? 0.97, aD = o.aD ?? 0.03, Csig = Cins / aG, D0 = 4 / (Math.PI * HBARVF0 * o.g0 / 1); // states/(eV nm) for gamma0
    const edgesE = [1, 2, 4, 5].slice(0, o.nsub || 2).map(f => D1 * f);
    const NE = 220, Emax = 1.2;
    const charge = U => {             // electrons per m at the top of the barrier
      let n = 0;
      for (const De of edgesE) {
        const Ei = (De - D1) + o.VT0 + U;
        if (Ei > 1.0) continue;
        let s = 0; const dE = Emax / NE;
        for (let i = 0; i < NE; i++) {
          const ek = (i + 0.5) * dE, Ee = ek + De, dosv = D0 * Ee / Math.sqrt(Ee * Ee - De * De);
          const fS = 1 / (1 + Math.exp(Math.min(200, (ek + Ei) / kT))), fD = 1 / (1 + Math.exp(Math.min(200, (ek + Ei + VD) / kT)));
          s += dosv * 0.5 * (fS + fD) * dE;
        }
        n += s;
      }
      return n * 1e9;
    };
    let lo = -3, hi = 3, U = 0;
    for (let it = 0; it < 46; it++) { U = (lo + hi) / 2; const rhs = -(aG * VG + aD * VD) + q * charge(U) / Csig; if (U > rhs) hi = U; else lo = U; }
    U = (lo + hi) / 2;
    let I = 0;
    for (const De of edgesE) { const Ei = (De - D1) + o.VT0 + U; I += (4 * q / h) * kT * q * (lse(-Ei / kT) - lse((-Ei - VD) / kT)); }
    return { I, U, n: charge(U), Cins, Eg };
  }

  /* ---------- Schottky-barrier CNTFET ---------- */
  // midgap energy along the tube (eV, electron energy; source metal Fermi level = 0, drain = -VD)
  function sbProfile(x, VG, VD, o) {   // o: {L, lam, phiB, Eg}
    const Emid_S = o.phiB - o.Eg / 2, Emid_D = o.phiB - o.Eg / 2 - VD, Emid_ch = -VG + (o.VFB || 0);
    return Emid_ch + (Emid_S - Emid_ch) * Math.exp(-x / o.lam) + (Emid_D - Emid_ch) * Math.exp(-(o.L - x) / o.lam);
  }
  function sbSplit(VG, VD, o) {        // o: {L, lam, phiB, Eg, T, g0, VFB}; returns {I, Ie, Ih}
    const kT = 8.617e-5 * o.T, D1 = o.Eg / 2, nx = 160, dx = o.L / nx, xs = [];
    for (let i = 0; i <= nx; i++) xs.push(sbProfile(i * dx, VG, VD, o));
    const mid = xs[nx >> 1];
    let Ie = 0, Ih = 0; const nE = 260, E0 = -1.6, E1 = 1.6, dE = (E1 - E0) / nE;
    for (let j = 0; j < nE; j++) {
      const E = E0 + (j + 0.5) * dE, fS = 1 / (1 + Math.exp(E / kT)), fD = 1 / (1 + Math.exp((E + VD) / kT));
      if (Math.abs(fS - fD) < 1e-14) continue;
      let s = 0; for (let i = 0; i <= nx; i++) { const a = D1 * D1 - (E - xs[i]) ** 2; if (a > 0) s += Math.sqrt(a) / (HBARVF0 * o.g0); }
      const c = Math.exp(-2 * s * dx) * (fS - fD) * dE;
      if (E > mid) Ie += c; else Ih += c;
    }
    const k = (4 * q / h) * q;
    return { I: k * (Ie + Ih), Ie: k * Ie, Ih: k * Ih };
  }
  const sbCurrent = (VG, VD, o) => sbSplit(VG, VD, o).I;
  // doped-contact (MOSFET-like) comparison: thermionic over the channel barrier, same channel electrostatics
  function mosCurrent(VG, VD, o) {
    const kT = 8.617e-5 * o.T, Ec = (o.Vth ?? 0.25) - VG;   // channel band edge relative to the source (n+) Fermi level, ideal gate
    return (4 * q / h) * kT * q * (lse(-Ec / kT) - lse((-Ec - VD) / kT));
  }
  return { ACC, A, a1, a2, b1, b2, eg, tube, subbands, edges, dos, cins, ballistic, sbProfile, sbCurrent, sbSplit, mosCurrent, HBARVF0 };
})();
