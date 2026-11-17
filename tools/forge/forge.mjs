// Procedural, tileable, hand-painted-style PBR sets. Usage: node tools/forge/forge.mjs
// Writes assets/tex/<name>_{basecolor,orm,normal}.png at 1024 px. Node stdlib only.
import { deflateSync, crc32 } from 'node:zlib';
import { writeFileSync, mkdirSync } from 'node:fs';
const N = 1024, OUT = new URL('../../assets/tex/', import.meta.url).pathname;
mkdirSync(OUT, { recursive: true });

// ---- periodic noise ----
const hash = (x, y, s) => { let h = (x * 374761393 + y * 668265263 + s * 1274126177) | 0; h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };
const sm = t => t * t * (3 - 2 * t);
const vn = (u, v, p, s) => { // u,v in 0..1 tile, p lattice cells
  const x = u * p, y = v * p, ix = Math.floor(x), iy = Math.floor(y), fx = sm(x - ix), fy = sm(y - iy);
  const w = a => ((a % p) + p) % p, a = hash(w(ix), w(iy), s), b = hash(w(ix + 1), w(iy), s), c = hash(w(ix), w(iy + 1), s), d = hash(w(ix + 1), w(iy + 1), s);
  return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy;
};
const fbm = (u, v, p, o, s) => { let a = 0, m = 0.5, t = 0; for (let i = 0; i < o; i++) { a += m * vn(u, v, p << i, s + i); t += m; m /= 2; } return a / t; };
const vor = (u, v, p, s) => { // returns [F1, F2-F1 edge, id]
  const x = u * p, y = v * p, ix = Math.floor(x), iy = Math.floor(y); let f1 = 9, f2 = 9, id = 0;
  for (let j = -1; j <= 1; j++) for (let i = -1; i <= 1; i++) {
    const cx = ix + i, cy = iy + j, wx = ((cx % p) + p) % p, wy = ((cy % p) + p) % p;
    const px = cx + hash(wx, wy, s), py = cy + hash(wx, wy, s + 7), d = Math.hypot(px - x, py - y);
    if (d < f1) { f2 = f1; f1 = d; id = hash(wx, wy, s + 3); } else if (d < f2) f2 = d;
  } return [f1, f2 - f1, id];
};
const clamp = (x, a = 0, b = 1) => x < a ? a : x > b ? b : x;
const mix = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
const hex = h => [h >> 16 & 255, h >> 8 & 255, h & 255].map(v => v / 255);
const ss = (a, b, x) => sm(clamp((x - a) / (b - a)));
const post = c => c.map(v => Math.round(Math.pow(clamp(v), 1 / 2.2) * 255)); // lin->srgb for baseColor

// ---- PNG ----
function png(path, w, h, ch, data) {
  const raw = Buffer.alloc((w * ch + 1) * h);
  for (let y = 0; y < h; y++) { raw[y * (w * ch + 1)] = 0; data.copy(raw, y * (w * ch + 1) + 1, y * w * ch, (y + 1) * w * ch); }
  const chunk = (t, d) => { const b = Buffer.alloc(12 + d.length); b.writeUInt32BE(d.length); b.write(t, 4); d.copy(b, 8); b.writeUInt32BE(crc32(b.subarray(4, 8 + d.length)), 8 + d.length); return b; };
  const ih = Buffer.alloc(13); ih.writeUInt32BE(w); ih.writeUInt32BE(h, 4); ih[8] = 8; ih[9] = ch === 4 ? 6 : 2;
  writeFileSync(path, Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ih), chunk('IDAT', deflateSync(raw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]));
}

// ---- material builder: f(u,v) -> {c:[r,g,b] linear, h, r, m, ao}; normalStrength ----
function build(name, f, ns = 3) {
  const H = new Float32Array(N * N), bc = Buffer.alloc(N * N * 3), orm = Buffer.alloc(N * N * 3), nm = Buffer.alloc(N * N * 3);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const o = f(x / N, y / N), i = y * N + x; H[i] = o.h;
    bc.set(post(o.c), i * 3); orm.set([clamp(o.ao) * 255, clamp(o.r) * 255, clamp(o.m) * 255].map(Math.round), i * 3);
  }
  const g = (x, y) => H[((y + N) % N) * N + ((x + N) % N)];
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const dx = (g(x - 1, y) - g(x + 1, y)) * ns * 8, dy = (g(x, y - 1) - g(x, y + 1)) * ns * 8, l = Math.hypot(dx, dy, 1), i = (y * N + x) * 3; // +Y up (glTF), image y down
    nm.set([dx / l, -dy / l, 1 / l].map(v => Math.round((v * 0.5 + 0.5) * 255)), i);
  }
  png(OUT + name + '_basecolor.png', N, N, 3, bc); png(OUT + name + '_orm.png', N, N, 3, orm); png(OUT + name + '_normal.png', N, N, 3, nm);
  console.log('wrote', name);
}

// painterly helpers: soft posterize toward flat paint bands, keeps it stylised
const paint = (c, k = 0.18) => c.map(v => { const q = Math.round(v * 6) / 6; return v + (q - v) * k; });
const brush = (u, v, s, ax = 1, ay = 1) => fbm(u * ax % 1, v * ay % 1, 4, 3, s); // low-freq blotches
const blotch = (u, v, s) => fbm(u, v, 3, 3, s);

// ---- 1. floor tiles: red-brown quarry w/ cream terrazzo flecks ----
const TF = 8;
build('floor_tile', (u, v) => {
  const tu = (u * TF) % 1, tv = (v * TF) % 1, ti = Math.floor(u * TF), tj = Math.floor(v * TF);
  const e = Math.min(tu, 1 - tu, tv, 1 - tv), gr = 0.035; // grout half width in tile units
  const inT = ss(gr, gr + 0.02, e), id = hash(ti, tj, 11);
  let base = mix(hex(0x8a3a24), hex(0xa4482c), id); base = mix(base, hex(0x7a3321), blotch(u, v, 5) * 0.6);
  const [f1, , cid] = vor(u, v, 16, 4), fleck = ss(0.2, 0.16, f1) * (cid > 0.7 ? 1 : 0); // cream chips
  base = mix(base, hex(cid > 0.8 ? 0xe9d3a8 : 0xc9a074), fleck * 0.85);
  const corner = Math.pow(1 - Math.min(1, Math.hypot(Math.min(tu, 1 - tu), Math.min(tv, 1 - tv)) * 2.2), 3);
  base = mix(base, hex(0x3d1c14), corner * 0.45 * inT);        // grime in corners
  base = mix(base, hex(0xd08a60), ss(0.1, 0.03, e - gr) * 0.4 * (blotch(u, v, 9) > 0.45 ? 1 : 0)); // worn edges
  const grout = mix(hex(0x6f6256), hex(0x3a322b), blotch(u, v, 2));
  const c = paint(mix(grout, base, inT), 0.15);
  return { c, h: inT * 0.7 + 0.3 * ss(gr + 0.04, gr + 0.01, e) * 0 + (1 - fleck) * 0.0 + fleck * 0.05, r: 0.55 + 0.25 * (1 - inT) + 0.1 * blotch(u, v, 6) - fleck * 0.2, m: 0, ao: 0.55 + 0.45 * inT * (1 - corner * 0.3) };
}, 2);

// ---- 2. wall tiles: pastel mint small squares, glossy ----
const TW = 16;
build('wall_tile', (u, v) => {
  const tu = (u * TW) % 1, tv = (v * TW) % 1, ti = Math.floor(u * TW), tj = Math.floor(v * TW);
  const e = Math.min(tu, 1 - tu, tv, 1 - tv), gr = 0.04, inT = ss(gr, gr + 0.05, e), id = hash(ti, tj, 21);
  let base = mix(hex(0xbfe3cc), hex(0xdcefe0), id); base = mix(base, hex(0xb7d4c4), blotch(u, v, 8) * 0.6);
  const bev = ss(gr + 0.2, gr + 0.05, e); base = mix(base, hex(0xf6fbf0), (1 - bev) * 0.0 + (tu < 0.5 && tv < 0.5 ? 0 : 0)); // flat paint
  base = mix(base, hex(0xffffff), ss(0.4, 0.0, Math.hypot(tu - 0.28, tv - 0.28)) * 0.18); // painted highlight
  const drip = Math.pow(1 - v, 2) * 0, grime = ss(0.55, 0.9, fbm(u, v, 3, 3, 33)) * 0.35 + Math.pow(1 - Math.min(1, Math.hypot(Math.min(tu, 1 - tu), Math.min(tv, 1 - tv)) * 2.4), 3) * 0.25;
  base = mix(base, hex(0x6d7a5c), grime * inT);
  const c = paint(mix(mix(hex(0x8f948a), hex(0x4a4b44), blotch(u, v, 3)), base, inT), 0.12);
  return { c, h: inT * 0.6 + bev * 0.15, r: 0.22 + 0.35 * (1 - inT) + grime * 0.3, m: 0, ao: 0.5 + 0.5 * inT };
}, 2);

// ---- 3. brushed stainless ----
build('steel_brushed', (u, v) => {
  const streak = fbm((u * 1) % 1, v, 2, 1, 41) * 0, s1 = vn(u, v, 1, 1) * 0;
  // anisotropic: few cells along x, many along y
  const aniso = (s, px, py) => { const x = u * px, y = v * py, ix = Math.floor(x), iy = Math.floor(y), fx = sm(x - ix), fy = sm(y - iy), w = (a, p) => ((a % p) + p) % p; const a = hash(w(ix, px), w(iy, py), s), b = hash(w(ix + 1, px), w(iy, py), s), c = hash(w(ix, px), w(iy + 1, py), s), d = hash(w(ix + 1, px), w(iy + 1, py), s); return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy; };
  const br = (aniso(5, 4, 256) + aniso(6, 8, 512) * 0.6) / 1.6;
  let t = 0.5 + (br - 0.5) * 0.9 + (blotch(u, v, 2) - 0.5) * 0.5;
  let c = mix(hex(0x6d747a), hex(0xc4cbd0), clamp(t)).map(x => x);
  const smudge = ss(0.55, 0.85, fbm(u, v, 3, 3, 47));
  c = mix(c, hex(0x4a4a40), smudge * 0.4);
  c = mix(c, hex(0xeef4f6), ss(0.75, 0.9, aniso(9, 2, 90)) * 0.5); // painted glints
  return { c: paint(c, 0.1), h: br * 0.25, r: 0.3 + 0.2 * smudge + 0.1 * br, m: 1.0 - smudge * 0.15, ao: 1 };
}, 1.2);

// ---- 4. formica tabletop, cream with green marbling ----
build('formica', (u, v) => {
  const wu = fbm(u, v, 3, 3, 51), wv = fbm(u, v, 3, 3, 52);
  const m = fbm(u + (wu - 0.5) * 0.35, v + (wv - 0.5) * 0.35, 4, 3, 53), vein = 1 - Math.abs(Math.sin((m * 4.5 + wu * 1.5) * Math.PI)), veinMask = ss(0.8, 0.97, vein);
  let c = mix(hex(0xe9e1c4), hex(0xd5d9b0), blotch(u, v, 6));
  c = mix(c, hex(0x6c9a74), ss(0.5, 0.75, fbm(u, v, 3, 3, 55)) * 0.45);
  c = mix(c, hex(0x2f6a4b), veinMask * 0.75);
  const scuff = ss(0.62, 0.9, fbm(u, v, 6, 2, 57)) * 0.5, ring = ss(0.01, 0.0, Math.abs(Math.hypot(((u + 0.2) % 1) - 0.5, v - 0.5) - 0.16)) * 0.0;
  c = mix(c, hex(0x8a7a56), scuff * 0.35);
  return { c: paint(c, 0.12), h: veinMask * 0.03 + scuff * -0.05, r: 0.28 + scuff * 0.45, m: 0, ao: 1 };
}, 0.4);

// ---- 5. painted concrete pillar ----
build('concrete_painted', (u, v) => {
  let c = mix(hex(0xe2d3a8), hex(0xd2c291), blotch(u, v, 3)); // faded cream-yellow paint
  const [f1, f2] = vor(u, v, 6, 61), chip = ss(0.1, 0.0, f2) * 0 + ss(0.62, 0.8, fbm(u, v, 5, 4, 62)) * ss(0.5, 0.2, f1 + 0.0);
  const rust = ss(0.7, 0.9, fbm(u, v, 3, 3, 63));
  const grimeY = Math.pow(Math.abs(v - 0.5) * 2, 3) * 0.55 + ss(0.55, 0.85, fbm(u, v, 4, 3, 64)) * 0.4; // dirt at bottom/top seams, tiles vertically
  c = mix(c, hex(0x5b4e38), grimeY * 0.75);
  c = mix(c, hex(0x8d8a82), chip * 0.9);      // exposed concrete
  c = mix(c, hex(0x9a5a2e), rust * 0.35);
  const pit = ss(0.1, 0.0, vor(u, v, 40, 65)[0] - 0.12) * 0.5;
  return { c: paint(c, 0.14), h: chip * -0.2 + 0.4 + fbm(u, v, 8, 2, 66) * 0.15 - pit * 0.02, r: 0.8 - chip * 0.0 + 0.15 * chip, m: 0, ao: 1 - grimeY * 0.35 - pit * 0.1 };
}, 2.5);

// ---- 6. weathered plywood ----
build('plywood', (u, v) => {
  const wy = fbm(u, v, 2, 2, 71), grainP = v * 22 + wy * 1.6 + fbm(u, v, 3, 2, 72) * 0.8;
  const ring = Math.abs(Math.sin(grainP * Math.PI)), stripe = 0.5 + 0.5 * Math.sin(v * 70 * Math.PI + fbm(u, v, 4, 2, 73) * 8) * 0.0;
  const longn = vn(u, v * 1, 2, 74) * 0 + (vn(u, v, 1, 75) * 0);
  const an = (px, py, s) => { const x = u * px, y = v * py, ix = Math.floor(x), iy = Math.floor(y), fx = sm(x - ix), fy = sm(y - iy), w = (a, p) => ((a % p) + p) % p; const a = hash(w(ix, px), w(iy, py), s), b = hash(w(ix + 1, px), w(iy, py), s), c = hash(w(ix, px), w(iy + 1, py), s), d = hash(w(ix + 1, px), w(iy + 1, py), s); return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy; };
  const fib = (an(3, 90, 76) + an(6, 40, 77)) / 2;
  let c = mix(hex(0xb88a58), hex(0x8c5f38), ring * 0.55 + (fib - 0.5) * 0.6);
  c = mix(c, hex(0x9a9486), ss(0.45, 0.8, fbm(u, v, 3, 3, 78)) * 0.55);   // sun-bleached grey
  const knot = vor(u, v, 4, 79), kn = ss(0.18, 0.07, knot[0]) * (knot[2] > 0.82 ? 1 : 0);
  c = mix(c, hex(0x4a2c18), kn * 0.8);
  c = mix(c, hex(0x3b2a1c), ss(0.7, 0.92, fbm(u, v, 4, 3, 81)) * 0.4);   // water stains
  return { c: paint(c, 0.12), h: ring * 0.12 + fib * 0.1 - kn * 0.15, r: 0.7 + 0.15 * fib, m: 0, ao: 1 - kn * 0.4 };
}, 1.5);

// ---- 7/8. plastic (stools, baskets) ----
function plastic(name, light, dark, scuffCol) {
  build(name, (u, v) => {
    let c = mix(dark, light, 0.35 + 0.65 * blotch(u, v, 3));
    const sc = ss(0.7, 0.92, fbm(u, v, 5, 3, 91)) * 0.6, mold = ss(0.5, 0.52, Math.abs(Math.sin(u * 6 * Math.PI))) * 0.0;
    c = mix(c, scuffCol, sc * 0.5);
    c = mix(c, hex(0x2a2018), ss(0.72, 0.95, fbm(u, v, 3, 3, 92)) * 0.35); // grime
    const pit = ss(0.22, 0.12, vor(u, v, 30, 93)[0]);                       // soft moulded dimples
    return { c: paint(c, 0.15), h: pit * 0.02 - sc * 0.03, r: 0.42 + sc * 0.35, m: 0, ao: 1 - pit * 0.05 };
  }, 0.8);
}
plastic('plastic_blue', hex(0x2f6fd0), hex(0x1b3f93), hex(0x8fb2e8));
plastic('plastic_red', hex(0xdc3a2e), hex(0x9a1f1c), hex(0xf0a08a));
