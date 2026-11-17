// Entry: ?shot=stall|ahma  &preset=default|high|ultra  &seed=1  &t=12.5
// &stats shows a frame-time readout. &freeze holds time at t for screenshots.
import * as THREE from 'three';
import { createRenderer, PRESETS } from '../render/renderer.js';
import { buildStyleFrame, SHOTS } from './styleframe.js';

const q = new URLSearchParams(location.search);
const shot = q.get('shot') || 'stall';
const preset = q.get('preset') || 'default';
const seed = Number(q.get('seed') || 1);
const t0 = Number(q.get('t') || 7.3);
const freeze = q.has('freeze');
const showStats = q.has('stats');
// &p.aoSamples=4 style overrides for tuning a preset from the URL
for (const [k, v] of q) if (k.startsWith('p.') && PRESETS[preset]) PRESETS[preset][k.slice(2)] = isNaN(v) ? v : Number(v);

const canvas = document.getElementById('c');
const W = Number(q.get('w') || 1920), H = Number(q.get('h') || 1080);
const R = createRenderer({ canvas, preset, width: W, height: H });

const camera = new THREE.PerspectiveCamera(38, W / H, 0.1, 120);
function applyShot(name) {
  const s = SHOTS[name] || SHOTS.stall;
  camera.position.fromArray(s.pos);
  camera.lookAt(new THREE.Vector3().fromArray(s.look));
  camera.fov = s.fov;
  camera.updateProjectionMatrix();
  camera.updateMatrixWorld();
}

const statsEl = document.getElementById('stats');
if (showStats) statsEl.style.display = 'block';
const frameTimes = [];

const state = { ready: false, used: null, scene: null };
window.__shot = {
  state, R, THREE,
  stats: () => summary(),
  bench: (n = 60) => R.bench(state.scene, camera, n),
  info: () => ({ calls: R.stats.calls, triangles: R.stats.triangles, preset: R.presetName }),
  setShot: (n) => { applyShot(n); state.sf.setShot(n); },
};

function summary() {
  const a = frameTimes.slice(-240).sort((x, y) => x - y);
  if (!a.length) return null;
  const p = (f) => a[Math.min(a.length - 1, Math.floor(a.length * f))];
  return { avg: a.reduce((s, v) => s + v, 0) / a.length, p50: p(0.5), p95: p(0.95), max: a[a.length - 1], n: a.length };
}

(async () => {
  const sf = await buildStyleFrame(R, { seed, preset });
  state.sf = sf;
  state.scene = sf.scene;
  state.used = sf.used;
  applyShot(shot);
  sf.setShot(shot);
  sf.update(t0, 0);
  await R.prewarm(sf.scene, camera);
  // a second render so every pass has a warm history, then flag ready
  R.render(sf.scene, camera);
  state.ready = true;
  console.log('[styleframe] ready', JSON.stringify(sf.used), R.info.render);

  let last = performance.now(), elapsed = 0;
  function loop(now) {
    const dt = Math.min(0.1, (now - last) / 1000);
    last = now;
    if (!freeze) elapsed += dt;
    sf.update(t0 + elapsed, dt);
    const s = performance.now();
    R.render(sf.scene, camera);
    frameTimes.push(performance.now() - s);
    if (frameTimes.length > 600) frameTimes.splice(0, frameTimes.length - 600);
    if (showStats && frameTimes.length % 10 === 0) {
      const m = summary();
      statsEl.textContent = `${R.presetName}  ${W}x${H}\ncpu ms  avg ${m.avg.toFixed(2)}  p95 ${m.p95.toFixed(2)}\ncalls ${R.stats.calls}  tris ${R.stats.triangles}`;
    }
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
})().catch((e) => { console.error(e); state.error = String(e.stack || e); });
