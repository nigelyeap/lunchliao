// Procedural canvas textures for the blockout. Used only when assets/tex/
// has nothing for a given set. Seeded, so shots are reproducible.
import * as THREE from 'three';

export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function canvas(size) {
  const c = document.createElement('canvas');
  c.width = c.height = size;
  return [c, c.getContext('2d')];
}

function toTexture(c, { srgb = true, repeat = 1 } = {}) {
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeat, repeat);
  t.anisotropy = 8;
  return t;
}

// Smooth value noise on a canvas-sized grid, tileable.
function noiseField(size, cells, r) {
  const g = new Float32Array(cells * cells);
  for (let i = 0; i < g.length; i++) g[i] = r();
  const out = new Float32Array(size * size);
  const s = cells / size;
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const fx = x * s, fy = y * s;
      const x0 = Math.floor(fx), y0 = Math.floor(fy);
      const tx = fx - x0, ty = fy - y0;
      const sx = tx * tx * (3 - 2 * tx), sy = ty * ty * (3 - 2 * ty);
      const x1 = (x0 + 1) % cells, y1 = (y0 + 1) % cells;
      const a = g[y0 * cells + x0], b = g[y0 * cells + x1], c = g[y1 * cells + x0], d = g[y1 * cells + x1];
      out[y * size + x] = (a + (b - a) * sx) * (1 - sy) + (c + (d - c) * sx) * sy;
    }
  }
  return out;
}

function fbm(size, r, octaves = 4, base = 4) {
  const out = new Float32Array(size * size);
  let amp = 0.5, total = 0;
  for (let o = 0; o < octaves; o++) {
    const f = noiseField(size, base << o, r);
    for (let i = 0; i < out.length; i++) out[i] += f[i] * amp;
    total += amp;
    amp *= 0.5;
  }
  for (let i = 0; i < out.length; i++) out[i] /= total;
  return out;
}

// Height field (0..1) to a tangent-space normal map texture.
function normalFromHeight(h, size, strength = 2) {
  const [c, ctx] = canvas(size);
  const img = ctx.createImageData(size, size);
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const l = h[y * size + ((x - 1 + size) % size)], rr = h[y * size + ((x + 1) % size)];
      const u = h[((y - 1 + size) % size) * size + x], d = h[((y + 1) % size) * size + x];
      let nx = (l - rr) * strength, ny = (u - d) * strength, nz = 1;
      const len = Math.hypot(nx, ny, nz);
      const i = (y * size + x) * 4;
      img.data[i] = (nx / len * 0.5 + 0.5) * 255;
      img.data[i + 1] = (ny / len * 0.5 + 0.5) * 255;
      img.data[i + 2] = (nz / len * 0.5 + 0.5) * 255;
      img.data[i + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  return toTexture(c, { srgb: false });
}

function pack(size, fn) {
  // fn(x, y) -> [r,g,b] in 0..255. Returns canvas.
  const [c, ctx] = canvas(size);
  const img = ctx.createImageData(size, size);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const [r, g, b] = fn(x, y);
    const i = (y * size + x) * 4;
    img.data[i] = r; img.data[i + 1] = g; img.data[i + 2] = b; img.data[i + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
  return c;
}

const clamp = (v, a = 0, b = 255) => Math.max(a, Math.min(b, v));
const mix = (a, b, t) => a + (b - a) * t;

// Hawker floor: 30 cm tiles, cream with terracotta accents, grout, grime.
// Texture covers 2.4 m (8 x 8 tiles).
export function tileSet(seed = 1, size = 1024) {
  const r = rng(seed);
  const grime = fbm(size, r, 5, 3);
  const fine = fbm(size, r, 3, 32);
  const tiles = 8, tw = size / tiles, grout = 5;
  const tileCol = [];
  for (let i = 0; i < tiles * tiles; i++) {
    const v = r();
    // mostly cream, some terracotta, a few dark green (hawker centre checker)
    const t = v < 0.72 ? [226, 212, 186] : v < 0.9 ? [178, 96, 62] : [78, 112, 90];
    const j = (r() - 0.5) * 18;
    tileCol.push([t[0] + j, t[1] + j, t[2] + j]);
  }
  const height = new Float32Array(size * size);
  const col = pack(size, (x, y) => {
    const tx = Math.floor(x / tw), ty = Math.floor(y / tw);
    const ix = x % tw, iy = y % tw;
    const inGrout = ix < grout || iy < grout;
    const i = y * size + x;
    const g = grime[i], f = fine[i];
    height[i] = inGrout ? 0.3 : 1.0 - (f - 0.5) * 0.08;
    if (inGrout) {
      const v = mix(92, 128, g);
      return [v, v - 4, v - 10];
    }
    const c = tileCol[ty * tiles + tx];
    // painted gradient inside each tile: lighter centre, dirt toward edges
    const ex = Math.min(ix - grout, tw - ix) / tw, ey = Math.min(iy - grout, tw - iy) / tw;
    const edge = Math.min(ex, ey) * 2;
    const dirt = (1 - g * 0.5) * (0.85 + 0.15 * Math.min(1, edge * 3));
    const spec = 1 + (f - 0.5) * 0.12;
    return [clamp(c[0] * dirt * spec), clamp(c[1] * dirt * spec), clamp(c[2] * dirt * spec)];
  });
  const rough = pack(size, (x, y) => {
    const ix = x % tw, iy = y % tw;
    const inGrout = ix < grout || iy < grout;
    const i = y * size + x;
    const v = inGrout ? 230 : clamp(mix(110, 185, grime[i]) + (fine[i] - 0.5) * 40);
    return [255, v, 0]; // ORM: R=AO (1), G=roughness, B=metal (0)
  });
  return { map: toTexture(col), orm: toTexture(rough, { srgb: false }), normal: normalFromHeight(height, size, 3.5), metres: 2.4 };
}

// Light green formica with a soft speckle, the classic kopitiam table top.
export function formicaSet(seed = 2, size = 512) {
  const r = rng(seed);
  const n = fbm(size, r, 4, 6);
  const speck = fbm(size, r, 2, 64);
  const col = pack(size, (x, y) => {
    const i = y * size + x;
    const base = [176, 196, 170];
    const v = (n[i] - 0.5) * 20 + (speck[i] > 0.62 ? -22 : 0);
    return [clamp(base[0] + v), clamp(base[1] + v), clamp(base[2] + v)];
  });
  const rough = pack(size, (x, y) => [255, clamp(80 + (n[y * size + x] - 0.5) * 50), 0]);
  return { map: toTexture(col), orm: toTexture(rough, { srgb: false }), normal: null, metres: 1.2 };
}

// Brushed stainless steel, a roughness streak map and a tiny normal grain.
export function steelSet(seed = 3, size = 512) {
  const r = rng(seed);
  const n = fbm(size, r, 3, 4);
  const streak = noiseField(size, 2, r);
  const h = new Float32Array(size * size);
  const col = pack(size, (x, y) => {
    const i = y * size + x;
    h[i] = 0.5 + (r() - 0.5) * 0.02;
    const v = 200 + (n[i] - 0.5) * 16;
    return [v, v, v + 2];
  });
  const rough = pack(size, (x, y) => {
    const i = y * size + x;
    const line = (Math.sin(y * 1.7 + n[i] * 9) * 0.5 + 0.5) * 30;
    return [255, clamp(70 + line + (streak[i] - 0.5) * 60 + (n[i] - 0.5) * 40), 255];
  });
  return { map: toTexture(col), orm: toTexture(rough, { srgb: false }), normal: normalFromHeight(h, size, 0.6), metres: 1 };
}

// Painted concrete pillar and wall: cream above, dark green dado below is done in geometry.
export function concreteSet(seed = 4, size = 512) {
  const r = rng(seed);
  const n = fbm(size, r, 5, 3);
  const stain = fbm(size, r, 3, 2);
  const h = new Float32Array(size * size);
  const col = pack(size, (x, y) => {
    const i = y * size + x;
    h[i] = n[i];
    const v = 196 + (n[i] - 0.5) * 34 - Math.max(0, stain[i] - 0.6) * 90;
    return [clamp(v + 6), clamp(v), clamp(v - 14)];
  });
  const rough = pack(size, (x, y) => [255, clamp(190 + (n[y * size + x] - 0.5) * 60), 0]);
  return { map: toTexture(col), orm: toTexture(rough, { srgb: false }), normal: normalFromHeight(h, size, 1.2), metres: 2 };
}

// Oiled wood planks for counters and the stall frame.
export function woodSet(seed = 5, size = 512) {
  const r = rng(seed);
  const grain = fbm(size, r, 4, 2);
  const planks = 4, pw = size / planks;
  const h = new Float32Array(size * size);
  const col = pack(size, (x, y) => {
    const i = y * size + x;
    const p = Math.floor(x / pw);
    const seam = x % pw < 3 ? 0.55 : 1;
    const ring = Math.sin((y + grain[i] * 140 + p * 37) * 0.08) * 0.5 + 0.5;
    h[i] = seam * (0.8 + ring * 0.2);
    const v = (120 + ring * 36 + (grain[i] - 0.5) * 30) * seam;
    return [clamp(v + 24), clamp(v - 4), clamp(v - 40)];
  });
  const rough = pack(size, (x, y) => [255, clamp(130 + (grain[y * size + x] - 0.5) * 70), 0]);
  return { map: toTexture(col), orm: toTexture(rough, { srgb: false }), normal: normalFromHeight(h, size, 2), metres: 1.5 };
}

// A soft round sprite for steam and dust.
export function softSprite(size = 128) {
  const [c, ctx] = canvas(size);
  const g = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  g.addColorStop(0, 'rgba(255,255,255,1)');
  g.addColorStop(0.35, 'rgba(255,255,255,0.55)');
  g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, size, size);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

// A painted steam puff: a lumpy cloud of overlapping discs, lit from the top
// left, hard-ish edge so it reads as a brush shape and not a blur.
export function puffSprite(size = 128) {
  const [c, ctx] = canvas(size);
  const r = rng(7);
  const lobes = [[0.5, 0.52, 0.3]];
  for (let i = 0; i < 7; i++) { const a = i * 0.9 + r(); lobes.push([0.5 + Math.cos(a) * 0.2, 0.5 + Math.sin(a) * 0.17, 0.16 + r() * 0.08]); }
  for (const [x, y, rad] of lobes) {
    const g = ctx.createRadialGradient((x - 0.06) * size, (y - 0.06) * size, 0, x * size, y * size, rad * size);
    g.addColorStop(0, 'rgba(255,255,255,1)');
    g.addColorStop(0.75, 'rgba(225,215,235,0.95)');
    g.addColorStop(1, 'rgba(200,190,220,0)');
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(x * size, y * size, rad * size, 0, Math.PI * 2); ctx.fill();
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

// Fallback signboard (English only, the sign builder owns the four languages).
export function signTex({ title, sub, bg = '#c8102e', fg = '#fff3d6', accent = '#f3c23a', w = 1024, h = 320 }) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const ctx = c.getContext('2d');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = accent;
  ctx.lineWidth = 14;
  ctx.strokeRect(22, 22, w - 44, h - 44);
  ctx.fillStyle = fg;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.font = `900 ${Math.floor(h * 0.36)}px "Arial Black", "Helvetica Neue", Arial, sans-serif`;
  ctx.fillText(title, w / 2, h * 0.42);
  if (sub) {
    ctx.fillStyle = accent;
    ctx.font = `700 ${Math.floor(h * 0.16)}px "Helvetica Neue", Arial, sans-serif`;
    ctx.fillText(sub, w / 2, h * 0.76);
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}
