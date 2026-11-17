#!/usr/bin/env node
// Headless Chrome screenshots of named shots.
//   node tools/shoot.mjs [shot...] [--preset=default|high|ultra] [--seed=1] [--t=7.3] [--out=shots/gate1] [--bench]
// Starts vite on 5301 if nothing answers there. One Chrome, own profile in the
// scratchpad, CDP on 9401, killed by pid at the end. No npm deps.
import { spawn, execSync } from 'node:child_process';
import { mkdirSync, writeFileSync, readFileSync, existsSync, unlinkSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SCRATCH = '/tmp/lunchliao-scratch';
const PROFILE = `${SCRATCH}/chrome-profile`;
const PIDFILE = `${SCRATCH}/chrome.pid`;
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PORT = 5301, CDP = 9401;

const args = process.argv.slice(2);
const opt = Object.fromEntries(args.filter((a) => a.startsWith('--')).map((a) => { const [k, v] = a.slice(2).split('='); return [k, v ?? true]; }));
const shots = args.filter((a) => !a.startsWith('--'));
if (!shots.length) shots.push('stall', 'ahma');
const presets = String(opt.preset || 'high').split(',');
const seed = opt.seed || 1, t = opt.t || 7.3;
const out = resolve(ROOT, opt.out || 'shots/gate1');
mkdirSync(out, { recursive: true });
mkdirSync(PROFILE, { recursive: true });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function up(url) { try { await fetch(url); return true; } catch { return false; } }

// ---- vite
let vite = null;
if (!(await up(`http://localhost:${PORT}/`))) {
  vite = spawn('npx', ['vite', '--port', String(PORT), '--strictPort'], { cwd: ROOT, stdio: 'ignore' });
  for (let i = 0; i < 100 && !(await up(`http://localhost:${PORT}/`)); i++) await sleep(100);
}

// ---- chrome: kill a stale one of ours by pid, then start fresh
if (existsSync(PIDFILE)) {
  const old = Number(readFileSync(PIDFILE, 'utf8'));
  try {
    const cmd = execSync(`ps -o command= -p ${old}`).toString();
    if (cmd.includes(PROFILE)) process.kill(old, 'SIGKILL');
  } catch { /* gone */ }
  unlinkSync(PIDFILE);
}
const chrome = spawn(CHROME, [
  '--headless=new', `--remote-debugging-port=${CDP}`, `--user-data-dir=${PROFILE}`,
  '--window-size=1920,1080', '--hide-scrollbars', '--no-first-run', '--no-default-browser-check',
  '--use-angle=metal', '--enable-gpu-rasterization', '--ignore-gpu-blocklist', '--disable-gpu-vsync', '--disable-frame-rate-limit',
  'about:blank',
], { stdio: 'ignore' });
writeFileSync(PIDFILE, String(chrome.pid));
const cleanup = () => { try { process.kill(chrome.pid, 'SIGKILL'); } catch {} try { unlinkSync(PIDFILE); } catch {} if (vite) vite.kill(); };
process.on('exit', cleanup);
process.on('SIGINT', () => process.exit(1));

for (let i = 0; i < 100 && !(await up(`http://localhost:${CDP}/json/version`)); i++) await sleep(100);

// ---- minimal CDP client
async function connect(url) {
  const r = await fetch(`http://localhost:${CDP}/json/new?about:blank`, { method: 'PUT' });
  const page = await r.json();
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let id = 0; const pending = new Map();
  ws.onmessage = (ev) => { const m = JSON.parse(ev.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } };
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); setTimeout(() => { if (pending.delete(i)) rej(new Error('CDP timeout: ' + method)); }, 60000); });
  const evalJs = async (expr) => { const m = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true }); if (m.result?.exceptionDetails) throw new Error(JSON.stringify(m.result.exceptionDetails)); return m.result?.result?.value; };
  await send('Page.navigate', { url });
  return { send, evalJs, close: () => ws.close(), id: page.id };
}

const results = [];
for (const preset of presets) {
  for (const shot of shots) {
    const url = `http://localhost:${PORT}/?shot=${shot}&preset=${preset}&seed=${seed}&t=${t}&freeze${Object.keys(opt).filter((k) => k.startsWith('p.')).map((k) => `&${k}=${opt[k]}`).join('')}`;
    const c = await connect(url);
    await c.send('Page.enable');
    await c.send('Emulation.setDeviceMetricsOverride', { width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false });
    let ready = false;
    for (let i = 0; i < 600 && !ready; i++) {
      await sleep(100);
      const s = await c.evalJs('window.__shot ? { ready: window.__shot.state.ready, error: window.__shot.state.error } : null');
      if (s?.error) throw new Error(s.error);
      ready = !!s?.ready;
    }
    if (!ready) throw new Error('page never became ready: ' + url);
    await sleep(600);
    const shotRes = await c.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
    const file = resolve(out, `${shot}_${preset}.png`);
    writeFileSync(file, Buffer.from(shotRes.result.data, 'base64'));
    const info = await c.evalJs('JSON.stringify({ info: window.__shot.info(), cpu: window.__shot.stats(), used: window.__shot.state.used })');
    let bench = null;
    // another agent writing into the project can make vite reload the page mid-run: wait for ready again
    const waitReady = async () => { for (let i = 0; i < 600; i++) { if (await c.evalJs('!!(window.__shot && window.__shot.state.ready)')) return; await sleep(100); } throw new Error('page lost: ' + url); };
    if (opt.bench) { await waitReady(); bench = await c.evalJs('window.__shot.bench(60)'); }
    if (opt.profile) {
      await waitReady();
      // bench again with one thing switched off at a time
      const prof = await c.evalJs(`(() => {
        const S = window.__shot, R = S.R, out = {};
        const tog = { gtao: (v) => { if (R.passes.gtao) { R.passes.gtao.enabled = v; R.passes.fogPass.uniforms.uUseAO.value = v ? 1 : 0; } },
          bloom: (v) => R.passes.bloom.enabled = v, aa: (v) => R.passes.aa.enabled = v,
          shadows: (v) => R.renderer.shadowMap.enabled = v, sky: (v) => R.sky.visible = v,
          fx: (v) => S.state.scene.traverse((o) => { if (o.userData.fx) o.visible = v; }),
          paint: (v) => S.state.scene.overrideMaterial = v ? null : new S.THREE.MeshStandardMaterial({ color: 0x888888 }),
          post: (v) => R.stats.post = v, scene: (v) => R.stats.scene = v,
          kuwahara: (v) => { R.stats.paint = v; R.passes.fogPass.uniforms.uPaintMix.value = v ? R.preset.paintMix : 0; } };
        R.composer.passes.forEach((p, i) => { tog['pass' + i + '_' + p.constructor.name] = (v) => p.enabled = v; });
        for (const k in tog) { tog[k](false); out[k] = S.bench(20); tog[k](true); }
        return out; })()`);
      results.push({ shot, preset, profile: prof });
      console.log('  profile ms with X off:', JSON.stringify(prof));
    }
    const gpu = await c.evalJs(`(() => { const gl = document.getElementById('c').getContext('webgl2'); const d = gl.getExtension('WEBGL_debug_renderer_info'); return (d ? gl.getParameter(d.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER)) + (gl.getExtension('EXT_disjoint_timer_query_webgl2') ? ' +timerquery' : ''); })()`);
    results.push({ shot, preset, file, ...JSON.parse(info), benchMs: bench, gpu });
    console.log(`${shot} ${preset} -> ${file}${bench != null ? `  ${bench.toFixed(2)} ms/frame` : ''}  cpu ${JSON.parse(info).cpu?.avg.toFixed(2)} ms`);
    c.close();
    await fetch(`http://localhost:${CDP}/json/close/${c.id}`);
  }
}
writeFileSync(resolve(out, 'last_run.json'), JSON.stringify(results, null, 2));
cleanup();
process.exit(0);
