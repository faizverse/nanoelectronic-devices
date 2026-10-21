# KKKC6353 Nanoelectronic Devices — interactive animations

Teaching animations for the postgraduate course KKKC6353 Nanoelectronic Devices, published at
**https://faizverse.github.io/nanoelectronic-devices/**.

## Lecture 1

| # | Animation | Notes section |
|---|---|---|
| 1 | [MOSFET basics](https://faizverse.github.io/nanoelectronic-devices/L1/mosfet-basics.html) | Doc 2, §3 |
| 2 | [Natural length and threshold roll-off](https://faizverse.github.io/nanoelectronic-devices/L1/vt-rolloff.html) | Doc 3, §1.1, 2.1 |
| 3 | [Drain-induced barrier lowering](https://faizverse.github.io/nanoelectronic-devices/L1/dibl.html) | Doc 3, §2.2 |
| 4 | [Punchthrough](https://faizverse.github.io/nanoelectronic-devices/L1/punchthrough.html) | Doc 3, §2.3 |
| 5 | [Subthreshold swing degradation](https://faizverse.github.io/nanoelectronic-devices/L1/subthreshold-swing.html) | Doc 3, §2.4 |
| 6 | [Channel-length modulation](https://faizverse.github.io/nanoelectronic-devices/L1/channel-length-modulation.html) | Doc 3, §2.5 |
| 7 | [Carrier velocity saturation](https://faizverse.github.io/nanoelectronic-devices/L1/velocity-saturation.html) | Doc 3, §3.1 |
| 8 | [Hot carriers and impact ionisation](https://faizverse.github.io/nanoelectronic-devices/L1/hot-carriers.html) | Doc 3, §3.3–3.4 |
| 9 | [Oxide breakdown (TDDB)](https://faizverse.github.io/nanoelectronic-devices/L1/oxide-breakdown.html) | Doc 3, §3.4 |
| 10 | [Gate-induced drain leakage](https://faizverse.github.io/nanoelectronic-devices/L1/gidl.html) | Doc 3, §4 |
| 11 | [Variability: random dopants](https://faizverse.github.io/nanoelectronic-devices/L1/variability.html) | Doc 3, §5 |

## Lecture 2

| # | Animation | Notes section |
|---|---|---|
| 1 | [Particle in a box](https://faizverse.github.io/nanoelectronic-devices/L2/particle-in-a-box.html) | Doc 1, §4–6 |
| 2 | [Density of states, 3D to 0D](https://faizverse.github.io/nanoelectronic-devices/L2/density-of-states.html) | Doc 2, §2 |
| 3 | [Quantum-well emission](https://faizverse.github.io/nanoelectronic-devices/L2/quantum-well-emission.html) | Doc 3, §6.1 |
| 4 | [Quantum cascade laser](https://faizverse.github.io/nanoelectronic-devices/L2/quantum-cascade-laser.html) | Doc 3, §6.4 |
| 5 | [Quantum-dot colour](https://faizverse.github.io/nanoelectronic-devices/L2/quantum-dot-colour.html) | Doc 2, §6 |
| 6 | [Carbon nanotubes: roll your own](https://faizverse.github.io/nanoelectronic-devices/L2/carbon-nanotubes.html) | Doc 2, §5 |
| 7 | [Growing quantum dots](https://faizverse.github.io/nanoelectronic-devices/L2/quantum-dot-growth.html) | Doc 3, §3–4 |

Each page is a single self-contained HTML file (no external dependencies; it works offline).

## Editing

The published pages are generated. Edit the files in `source/src/` and run `python3 build.py`
from `source/`; it inlines the shared CSS/JS into each page and writes them to `source/site/`.
Copy `source/site/index.html`, `source/site/L1/` and `source/site/L2/` to the repository root to publish.
