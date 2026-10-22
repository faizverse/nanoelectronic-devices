/* Tunnelling helpers for the Lecture 3 animations: exact 1-D transmission through piecewise-constant
   potentials (transfer matrices). Energies in eV, lengths in nm, mass in units of the free-electron mass. */
const TUN = (() => {
  const HB2M = 0.0380998;      // ħ²/2m0 in eV·nm²
  const HBAR = 0.6582119;      // ħ in eV·fs
  const kT300 = 0.025852;
  // complex helpers on [re, im]
  const cm = (a, b) => [a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]];
  const cadd = (a, b) => [a[0] + b[0], a[1] + b[1]];
  const cdiv = (a, b) => { const d = b[0] * b[0] + b[1] * b[1]; return [(a[0] * b[0] + a[1] * b[1]) / d, (a[1] * b[0] - a[0] * b[1]) / d]; };
  const cexp = z => { const e = Math.exp(z[0]); return [e * Math.cos(z[1]), e * Math.sin(z[1])]; };
  // wave number k = sqrt((E-V) m / HB2M): real above the step, imaginary (decay) below it
  function kOf(E, V, m) { const s = (E - V) * m / HB2M; return s >= 0 ? [Math.sqrt(Math.max(s, 1e-12)), 0] : [0, Math.sqrt(-s)]; }
  // P(k, x) = [[e^{ikx}, e^{-ikx}], [ik e^{ikx}, -ik e^{-ikx}]]
  function P(k, x) {
    const ik = [-k[1], k[0]], ep = cexp([-k[1] * x, k[0] * x]), em = cexp([k[1] * x, -k[0] * x]);
    return [[ep, em], [cm(ik, ep), cm([-ik[0], -ik[1]], em)]];
  }
  function inv(M) {
    const det = cadd(cm(M[0][0], M[1][1]), cm([-M[0][1][0], -M[0][1][1]], M[1][0]));
    return [[cdiv(M[1][1], det), cdiv([-M[0][1][0], -M[0][1][1]], det)], [cdiv([-M[1][0][0], -M[1][0][1]], det), cdiv(M[0][0], det)]];
  }
  function mul(A, B) {
    return [[cadd(cm(A[0][0], B[0][0]), cm(A[0][1], B[1][0])), cadd(cm(A[0][0], B[0][1]), cm(A[0][1], B[1][1]))],
            [cadd(cm(A[1][0], B[0][0]), cm(A[1][1], B[1][0])), cadd(cm(A[1][0], B[0][1]), cm(A[1][1], B[1][1]))]];
  }
  const mv = (M, v) => [cadd(cm(M[0][0], v[0]), cm(M[0][1], v[1])), cadd(cm(M[1][0], v[0]), cm(M[1][1], v[1]))];
  /* edges: interface positions (ascending); Vs: potential in each of edges.length+1 regions.
     Returns { T, R, c: [[A,B] per region], ks } for an electron arriving from the left with amplitude 1. */
  function solve(E, edges, Vs, m = 1) {
    const ks = Vs.map(V => kOf(E, V, m)); let M = [[[1, 0], [0, 0]], [[0, 0], [1, 0]]]; const Ms = [];
    for (let j = 0; j < edges.length; j++) { const Mj = mul(inv(P(ks[j + 1], edges[j])), P(ks[j], edges[j])); Ms.push(Mj); M = mul(Mj, M); }
    const B0 = cdiv([-M[1][0][0], -M[1][0][1]], M[1][1]);
    const c = [[[1, 0], B0]]; for (const Mj of Ms) c.push(mv(Mj, c[c.length - 1]));
    const kL = ks[0][0], kR = ks[ks.length - 1][0], A = c[c.length - 1][0];
    const T = kR > 0 && kL > 0 ? (A[0] * A[0] + A[1] * A[1]) * kR / kL : 0;
    return { T, R: B0[0] * B0[0] + B0[1] * B0[1], c, ks };
  }
  // the stationary wave at positions xs (array), for the same arguments
  function psi(xs, E, edges, Vs, m = 1) {
    const s = solve(E, edges, Vs, m), re = new Float64Array(xs.length), im = new Float64Array(xs.length);
    for (let i = 0; i < xs.length; i++) {
      const x = xs[i]; let j = 0; while (j < edges.length && x > edges[j]) j++;
      const k = s.ks[j], [A, B] = s.c[j];
      const ep = cexp([-k[1] * x, k[0] * x]), em = cexp([k[1] * x, -k[0] * x]);
      const v = cadd(cm(A, ep), cm(B, em)); re[i] = v[0]; im[i] = v[1];
    }
    return { re, im, T: s.T };
  }
  // single rectangular barrier, analytic and overflow-safe
  function Trect(E, V0, d, m = 1) {
    if (d <= 0) return 1;
    if (E >= V0) return solve(E, [0, d], [0, V0, 0], m).T;
    const ka = Math.sqrt((V0 - E) * m / HB2M) * d;
    if (ka > 30) return 16 * E * (V0 - E) / (V0 * V0) * Math.exp(-2 * ka);
    const s = Math.sinh(ka); return 1 / (1 + V0 * V0 * s * s / (4 * E * (V0 - E)));
  }
  const kappa = (dV, m = 1) => Math.sqrt(Math.max(dV, 0) * m / HB2M);
  // "1 in N" style text for a probability
  function odds(p) {
    if (!(p > 0)) return "essentially never";
    if (p >= 0.995) return "almost 100%";
    if (p >= 0.01) return (100 * p).toFixed(p >= 0.1 ? 0 : 1) + "%";
    const n = 1 / p;
    if (n < 1e6) { const f = Math.pow(10, Math.max(0, Math.floor(Math.log10(n)) - 1)); return "1 in " + (Math.round(n / f) * f).toLocaleString("en-GB"); }
    return "1 in " + NX.fmt(n, 1);
  }
  return { HB2M, HBAR, kT300, kOf, solve, psi, Trect, kappa, odds };
})();
