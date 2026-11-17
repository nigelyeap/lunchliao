// Bake sign PNGs with headless Chrome (HTML/CSS + @font-face, so Tamil shapes correctly).
// Usage: node tools/signs/bake.mjs [name ...]   (no names = all)
// Own Chrome: temp profile in the scratchpad, debug port 9404, one process, killed by pid at the end.
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { SIGNS } from './signs.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const FONTS = pathToFileURL(path.join(ROOT, 'assets/fonts')).href;
const OUT = path.join(ROOT, 'assets/signs');
const HTML = path.join(ROOT, 'tools/signs/_html');
const PROFILE = '/tmp/lunchliao-scratch/chrome-signs';
const PORT = 9404;
fs.mkdirSync(OUT, { recursive: true }); fs.mkdirSync(HTML, { recursive: true });

const face = (fam, file, wt) => `@font-face{font-family:'${fam}';src:url('${FONTS}/${file}');font-weight:${wt}}`;
const FONTCSS = [
  face('SansSC', 'NotoSansSC-Bold.otf', 700), face('SansSC', 'NotoSansSC-Black.otf', 900),
  face('SerifSC', 'NotoSerifSC-Black.otf', 900), face('Disp', 'NotoSerifDisplay-Black.ttf', 900),
  face('TamilSans', 'NotoSansTamil-Bold.ttf', 700), face('TamilSans', 'NotoSansTamil-Black.ttf', 900),
].join('\n');

const BASE = `*{box-sizing:border-box;margin:0;padding:0}html,body{overflow:hidden;background:transparent}
body{position:relative;font-family:'SansSC';-webkit-font-smoothing:antialiased}
.art{position:absolute;inset:0;filter:url(#wob) saturate(.86) contrast(.97)}
.wear{position:absolute;inset:0;pointer-events:none}
.wear div{position:absolute;inset:0;background:#000}
.chips{filter:url(#chips)} .dirt{filter:url(#dirt);mix-blend-mode:multiply} .streak{filter:url(#streak);mix-blend-mode:multiply}
.edge{background:transparent!important;box-shadow:inset 0 0 90px 12px rgba(48,30,14,.42);mix-blend-mode:multiply}
.sun{background:linear-gradient(125deg,rgba(255,236,190,.14),rgba(255,236,190,0) 55%)!important;mix-blend-mode:screen}
body.em{background:#000}.em .dark{visibility:hidden}.em .wear{display:none}.em .art{filter:none}`;

const FILTERS = `<svg width="0" height="0" style="position:absolute"><defs>
<filter id="wob" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".022" numOctaves="2" seed="4" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="4.5"/></filter>
<filter id="chips" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".55" numOctaves="3" seed="11"/><feColorMatrix type="matrix" values="0 0 0 0 .96  0 0 0 0 .91  0 0 0 0 .78  26 0 0 0 -19.6"/></filter>
<filter id="dirt" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".007" numOctaves="4" seed="7"/><feColorMatrix type="matrix" values="0 0 0 0 .42  0 0 0 0 .3  0 0 0 0 .18  2.2 0 0 0 -1.04"/></filter>
<filter id="streak" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".04 .0025" numOctaves="2" seed="21"/><feColorMatrix type="matrix" values="0 0 0 0 .35  0 0 0 0 .24  0 0 0 0 .14  1.1 0 0 0 -.52"/></filter>
</defs></svg>`;

function page(s, em) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>${FONTCSS}\n${BASE}\n${s.css}</style></head>
<body class="${em ? 'em' : ''}" style="width:${s.w}px;height:${s.h}px">${FILTERS}
<div class="art">${s.html()}</div>
<div class="wear"><div class="chips"></div><div class="dirt"></div><div class="streak"></div><div class="edge"></div><div class="sun"></div></div></body></html>`;
}

// --- minimal CDP client (Node has global WebSocket) ---
async function connect() {
  for (let i = 0; i < 50; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
      const t = list.find(x => x.type === 'page');
      if (t) return t.webSocketDebuggerUrl;
    } catch {}
    await new Promise(r => setTimeout(r, 200));
  }
  throw new Error('chrome did not start');
}

const want = process.argv.slice(2);
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
  '--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${PROFILE}`, '--no-first-run',
  '--hide-scrollbars', '--allow-file-access-from-files', '--force-device-scale-factor=1', 'about:blank'], { stdio: 'ignore' });
let id = 0; const pend = new Map();
try {
  const ws = new WebSocket(await connect());
  await new Promise(r => ws.addEventListener('open', r));
  ws.addEventListener('message', e => { const m = JSON.parse(e.data); pend.get(m.id)?.(m); });
  const send = (method, params = {}) => new Promise(res => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
  await send('Page.enable');
  for (const s of SIGNS) {
    if (want.length && !want.includes(s.name)) continue;
    for (const em of s.glow ? [false, true] : [false]) {
      const f = path.join(HTML, `${s.name}${em ? '_n' : ''}.html`);
      fs.writeFileSync(f, page(s, em));
      await send('Emulation.setDeviceMetricsOverride', { width: s.w, height: s.h, deviceScaleFactor: 1, mobile: false });
      await send('Page.navigate', { url: pathToFileURL(f).href });
      await new Promise(r => setTimeout(r, 400));
      await send('Runtime.evaluate', { expression: 'document.fonts.ready.then(()=>1)', awaitPromise: true });
      await new Promise(r => setTimeout(r, 300));
      const r = await send('Page.captureScreenshot', { format: 'png', clip: { x: 0, y: 0, width: s.w, height: s.h, scale: 1 } });
      fs.writeFileSync(path.join(OUT, `${s.name}${em ? '_n' : ''}.png`), Buffer.from(r.result.data, 'base64'));
      console.log('baked', s.name + (em ? '_n' : ''));
    }
  }
  ws.close();
} finally { chrome.kill(); }
