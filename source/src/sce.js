/* Quasi-2-D natural-length model of a short-channel MOSFET (used by roll-off, DIBL and swing pages).
   Surface potential along the channel (x from source, 0..L):
     psi(x) = psiL + (Vbi-psiL) sinh((L-x)/lam)/sinh(L/lam) + (Vbi+VD-psiL) sinh(x/lam)/sinh(L/lam)
   psiL = long-channel surface potential set by the gate. Potentials in volts, lengths in nm. */
const SCE = (() => {
  const P = { Vbi: 1.10, psiTh: 0.90, VTlong: 0.30, mu: 250e-4 /* m2/Vs */, W: 1e-6 };
  const ARCH = {
    bulk: { name: "Planar bulk", N: 1, tSi: 20, tag: "depletion depth" },
    fin:  { name: "FinFET / double gate", N: 2, tSi: 6, tag: "fin width" },
    gaa:  { name: "GAA nanosheet", N: 4, tSi: 5, tag: "sheet thickness" }
  };
  const lambda = (tSi, eot, N) => Math.sqrt((11.7 / 3.9) * tSi * eot / N);
  // body factor m = 1 + Cdep/Cox for bulk; fully depleted multi-gate bodies are close to ideal
  const mFac = (N, tSi, eot) => N === 1 ? 1 + (11.7 / tSi) / (3.9 / eot) : 1.03;
  function psi(x, psiL, L, VD, lam) {
    const r = L / lam;
    if (r > 600) return psiL;
    const s = Math.sinh(r);
    return psiL + (P.Vbi - psiL) * Math.sinh((L - x) / lam) / s + (P.Vbi + VD - psiL) * Math.sinh(x / lam) / s;
  }
  function minimum(psiL, L, VD, lam) {
    // golden-section search for the potential minimum (the top of the electron barrier)
    let a = 0, b = L; const g = 0.381966;
    let c = a + g * (b - a), d = b - g * (b - a), fc = psi(c, psiL, L, VD, lam), fd = psi(d, psiL, L, VD, lam);
    for (let i = 0; i < 46; i++) {
      if (fc < fd) { b = d; d = c; fd = fc; c = a + g * (b - a); fc = psi(c, psiL, L, VD, lam); }
      else { a = c; c = d; fc = fd; d = b - g * (b - a); fd = psi(d, psiL, L, VD, lam); }
    }
    const x = (a + b) / 2, r = L / lam;
    const eta = r > 600 ? 1 : 1 - (Math.sinh((L - x) / lam) + Math.sinh(x / lam)) / Math.sinh(r);
    return { x, psi: psi(x, psiL, L, VD, lam), eta: Math.max(eta, 0.02) };
  }
  // Device: {L, VD, tSi, eot, N}. Threshold = gate voltage at which the barrier top reaches psiTh.
  function device(o) {
    const lam = lambda(o.tSi, o.eot, o.N), m = mFac(o.N, o.tSi, o.eot);
    let lo = P.psiTh - 3, hi = P.psiTh + 0.5;
    for (let i = 0; i < 40; i++) { const mid = (lo + hi) / 2; (minimum(mid, o.L, o.VD, lam).psi < P.psiTh) ? lo = mid : hi = mid; }
    const psiL = (lo + hi) / 2, mn = minimum(psiL, o.L, o.VD, lam);
    const VT = P.VTlong + m * (psiL - P.psiTh);
    const n = m / mn.eta;                         // effective swing factor
    const SS = n * NX.C.Vt * Math.log(10) * 1000; // mV/decade
    const Cox = NX.C.epsOx / (o.eot * 1e-9);
    const Ispec = 2 * n * P.mu * Cox * (P.W / (o.L * 1e-9)) * NX.C.Vt ** 2; // A per um of width
    // EKV-style interpolation (exponential below VT, square law above) in series with a
    // velocity-saturation limit W*Cox*vsat*Vov, which only matters well above threshold
    const Id = VG => {
      const u = (VG - VT) / (2 * n * NX.C.Vt); const s = u > 30 ? u : Math.log1p(Math.exp(u));
      const Iekv = Ispec * s * s, Ivs = P.W * Cox * 1e5 * 2 * n * NX.C.Vt * s;
      return 1 / (1 / Iekv + 1 / Ivs);
    };
    return { lam, m, n, VT, SS, Id, xBar: mn.x, eta: mn.eta, psiLofVG: VG => P.psiTh + (VG - P.VTlong) / m };
  }
  // barrier for electrons (eV), measured from the source conduction-band edge, at gate voltage VG
  function barrier(o, VG) {
    const lam = lambda(o.tSi, o.eot, o.N), m = mFac(o.N, o.tSi, o.eot);
    const psiL = P.psiTh + (VG - P.VTlong) / m;
    const mn = minimum(psiL, o.L, o.VD, lam);
    return { Eb: P.Vbi - mn.psi, x: mn.x, psiL, lam };
  }
  return { P, ARCH, lambda, mFac, psi, minimum, device, barrier };
})();
