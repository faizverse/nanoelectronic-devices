// Screenshots of the L3 animations (simple view) for the decks and guides -> /home/claude/guide/imgL3/
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
const SET = { 'resonant-tunnelling-diode.html': [['V', 0.13]], 'tunnel-fet.html': [['Vg', 0.25]], 'single-electron-transistor.html': [['ng', 0.5]], 'tunnel-diode.html': [['V', 0.07]] };
const WAIT = { 'tunnelling.html': 4300 };
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell' });
  fs.mkdirSync('/home/claude/guide/imgL3', { recursive: true });
  const files = fs.readdirSync('site/L3').filter(f => f.endsWith('.html') && f !== 'index.html');
  for (const f of files) {
    for (const more of [false, true]) {
      const p = await b.newPage({ viewport: { width: 1180, height: 900 }, deviceScaleFactor: 2, colorScheme: 'light' });
      await p.goto('file://' + path.resolve('site/L3/' + f)); await p.waitForTimeout(400);
      for (const [id, v] of SET[f] || []) await p.evaluate(([id, v]) => { const r = document.getElementById('s_' + id); r.value = v; r.dispatchEvent(new Event('input')); }, [id, v]);
      if (more) await p.evaluate(() => document.querySelector('.more-btn').click());
      await p.evaluate(() => { document.querySelector('.lab .stage').style.alignSelf = 'start'; });
      await p.waitForTimeout(WAIT[f] || 2800);
      await p.locator('.lab .stage').screenshot({ path: '/home/claude/guide/imgL3/' + f.replace('.html', more ? '-more.png' : '.png') });
      await p.close();
    }
  }
  await b.close(); console.log('done');
})();
