// Gate 1 style frame: a hawker stall corner at golden hour, plus Ah Ma.
// Blockout first, real assets swapped in by file name when they exist.
import * as THREE from 'three';
import * as A from './assets.js';
import * as T from './proctex.js';
import { LIB, buildLibrary, setTextureSet, applyByName, paint } from '../render/materials.js';

export const SHOTS = {
  stall: { pos: [2.1, 1.55, -5.4], look: [-1.6, 1.3, 1.4], fov: 38, hero: false }, // pillar as a thin left edge, stall near centre
  ahma: { pos: [0.5, 1.3, -5.7], look: [-0.55, 1.05, -1.35], fov: 34, hero: true },
};

export const SCENE_BOX = new THREE.Box3(new THREE.Vector3(-10.5, -0.2, -9), new THREE.Vector3(6, 4.6, 4.6));

const box = (w, h, d, mat, x = 0, y = 0, z = 0) => {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.position.set(x, y, z);
  m.castShadow = m.receiveShadow = true;
  return m;
};
const cyl = (rt, rb, h, mat, x = 0, y = 0, z = 0, seg = 18) => {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(rt, rb, h, seg), mat);
  m.position.set(x, y, z);
  m.castShadow = m.receiveShadow = true;
  return m;
};
const sph = (r, mat, x = 0, y = 0, z = 0, ws = 20, hs = 14) => {
  const m = new THREE.Mesh(new THREE.SphereGeometry(r, ws, hs), mat);
  m.position.set(x, y, z);
  m.castShadow = m.receiveShadow = true;
  return m;
};
const plane = (w, h, mat, x, y, z, ry = 0) => {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat);
  m.position.set(x, y, z);
  m.rotation.y = ry;
  m.receiveShadow = true;
  return m;
};

function uvScale(geo, metresU, metresV, setMetres) {
  const uv = geo.attributes.uv;
  for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) * metresU / setMetres, uv.getY(i) * metresV / setMetres);
  return geo;
}

function texSetFor(name, fallback, metres = 2) {
  const c = A.findTex(name, 'color');
  if (!c) return fallback();
  const set = { map: A.loadTex(c), normal: null, orm: null, metres };
  const n = A.findTex(name, 'normal');
  const o = A.findTex(name, 'orm');
  if (n) set.normal = A.loadTex(n, { srgb: false });
  if (o) set.orm = A.loadTex(o, { srgb: false });
  return set;
}

export async function buildStyleFrame(R, { seed = 1, preset }) {
  const used = { assets: [], blockout: [] };
  const rnd = T.rng(seed);
  const scene = new THREE.Scene();
  R.attachLighting(scene);

  // ---- textures: assets/tex if present, else procedural
  const sets = {
    tile: texSetFor('tile', () => T.tileSet(seed)),
    formica: texSetFor('formica', () => T.formicaSet(seed + 1)),
    steel: texSetFor('steel', () => T.steelSet(seed + 2)),
    concrete: texSetFor('concrete', () => T.concreteSet(seed + 3), 1.3),
    wood: texSetFor('wood', () => T.woodSet(seed + 4)),
  };
  for (const k in sets) {
    setTextureSet(k, sets[k]);
    (A.findTex(k, 'color') ? used.assets : used.blockout).push('tex:' + k);
  }
  buildLibrary();

  // ---- architecture
  const floor = new THREE.Mesh(uvScale(new THREE.PlaneGeometry(24, 22), 24, 22, sets.tile.metres), LIB.tile);
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(-2.5, 0, -2.5);
  floor.receiveShadow = true;
  scene.add(floor);

  const wallMat = LIB.concrete;
  const backWall = new THREE.Mesh(uvScale(new THREE.BoxGeometry(22, 4.4, 0.3), 22, 4.4, sets.concrete.metres), wallMat);
  backWall.position.set(-2.5, 2.2, 4.35);
  backWall.receiveShadow = true;
  scene.add(backWall);
  // right wall (camera right), closes the corner
  scene.add(box(0.3, 4.4, 14, wallMat, 5.5, 2.2, -2.5));
  // green dado band along the walls, hawker centre paint
  scene.add(box(22, 1.15, 0.05, LIB.paint_green, -2.5, 0.575, 4.17));
  scene.add(box(0.05, 1.15, 14, LIB.paint_green, 5.32, 0.575, -2.5));
  // ceiling slab and beams
  const ceilMat = paint(new THREE.MeshStandardMaterial({ color: 0xcdb997, roughness: 0.92 }), { mottle: 0.2, gradient: 0, wear: 0 });
  scene.add(box(24, 0.3, 22, ceilMat, -2.5, 4.55, -2.5));
  for (const z of [-8, -4, 0, 3.8]) scene.add(box(24, 0.5, 0.35, LIB.paint_cream, -2.5, 4.15, z));
  // joists across the beams, so the ceiling reads as a grid instead of a plane
  for (const x of [-8.2, -5.6, -3.0, -0.4, 2.2, 4.8]) scene.add(box(0.22, 0.36, 22, LIB.paint_cream, x, 4.22, -2.5));
  // pillars with green dado, a table number plate on each
  for (const [x, z] of [[-4.6, -1.0], [2.4, -1.0], [-4.6, -7.0], [2.4, -7.0]]) {
    scene.add(box(0.5, 4.4, 0.5, wallMat, x, 2.2, z));
    scene.add(box(0.54, 1.15, 0.54, LIB.paint_green, x, 0.575, z));
  }
  // open side (camera left): half wall with a railing, sun comes over it
  scene.add(box(0.25, 1.0, 22, wallMat, -10.0, 0.5, -2.5));
  for (let z = -9; z <= 4; z += 1.6) scene.add(cyl(0.025, 0.025, 1.0, LIB.chrome, -10.0, 1.5, z, 8));
  scene.add(box(0.05, 0.05, 22, LIB.chrome, -10.0, 2.0, -2.5));
  // outside: a couple of rain trees in the haze
  const leaf = paint(new THREE.MeshStandardMaterial({ color: 0x4f7a3c, roughness: 0.9 }), { mottle: 0.12, rim: 1.5 });
  const bark = paint(new THREE.MeshStandardMaterial({ color: 0x5a4634, roughness: 0.95 }), { mottle: 0.08 });
  for (const [x, z, s] of [[-17, -6, 1.3], [-21, 3, 1.6], [-15, 6, 1.0]]) {
    scene.add(cyl(0.18 * s, 0.26 * s, 4 * s, bark, x, 2 * s, z, 10));
    scene.add(sph(2.4 * s, leaf, x, 5.2 * s, z, 14, 10));
    scene.add(sph(1.6 * s, leaf, x + 1.6 * s, 4.6 * s, z - 0.8 * s, 12, 8));
  }

  // ---- stall slot
  const stallAt = { x: -1.6, zFront: 1.6, zBack: 4.2, w: 3.6 };
  const signs = A.list('/assets/signs/', '.png');
  const pickSign = (keys) => signs.find((p) => keys.some((k) => p.toLowerCase().includes(k)));
  const signMat = (p, fallback) => {
    const tex = p ? A.loadTex(p) : fallback;
    (p ? used.assets : used.blockout).push('sign:' + (p ? p.split('/').pop() : fallback.userData.name));
    const ep = p && signs.find((f) => f === p.replace(/\.png$/, '_n.png'));
    const e = ep ? A.loadTex(ep) : null;
    return paint(new THREE.MeshStandardMaterial({ map: tex, roughness: 0.55, emissive: 0xffffff, emissiveMap: e || tex, emissiveIntensity: e ? 1.6 : 0.25 }), { mottle: 0, gradient: 0, stroke: 0, sign: true });
  };
  const fb = (o) => { const t = T.signTex(o); t.userData.name = o.title; return t; };

  const signOpts = {
    sign: (k) => { const p = signs.find((f) => f.toLowerCase().endsWith('/' + k.toLowerCase() + '.png')); if (!p) return null; used.assets.push('sign:' + k); const t = A.loadTex(p); glbUv(t); return t; },
    signEmit: (k) => { const p = signs.find((f) => f.toLowerCase().endsWith('/' + k.toLowerCase() + '_n.png')); if (!p) return null; const t = A.loadTex(p, { srgb: false }); glbUv(t); return t; },
  };
  // the builder's SIGN quads read upside down and mirrored with default texture orientation
  function glbUv(t) { t.flipY = false; }
  const apply = (o) => applyByName(o, signOpts);

  const stallGlb = await A.loadGlb(A.list('/assets/props/', '.glb').find((p) => /stall/i.test(p)) || '');
  const g = new THREE.Group();
  g.position.set(stallAt.x, 0, 0);
  const glaze = paint(new THREE.MeshStandardMaterial({ color: 0xb5581c, roughness: 0.32 }), { mottle: 0.1, rim: 1.3 });

  const d = stallAt.zBack - stallAt.zFront, zc = (stallAt.zBack + stallAt.zFront) / 2;
  if (stallGlb) {
    // builder's stall front faces +Z: turn it to face the hall, front edge on zFront
    const s = stallGlb.scene;
    apply(s);
    s.rotation.y = Math.PI;
    s.position.set(0, 0, stallAt.zFront + 0.54);
    g.add(s);
    used.assets.push('prop:stall_front.glb');
  } else {
    used.blockout.push('prop:stall');
    // tiled front and counter
    const front = new THREE.Mesh(uvScale(new THREE.BoxGeometry(stallAt.w, 0.92, 0.62), 3.6, 0.92, 0.6), LIB.tile);
    front.position.set(0, 0.46, stallAt.zFront + 0.31); front.castShadow = front.receiveShadow = true; g.add(front);
    g.add(box(stallAt.w + 0.06, 0.05, 0.7, LIB.steel, 0, 0.945, stallAt.zFront + 0.33));
    // fascia with the signboard and a fluorescent tube under it
    g.add(box(stallAt.w + 0.24, 0.8, 0.3, LIB.paint_red, 0, 2.55, stallAt.zFront + 0.15));
    const signTex = pickSign(['sign_main']);
    g.add(plane(stallAt.w, 0.68, signMat(signTex, fb({ title: 'AH MA CHICKEN RICE', sub: '#01-23  since 1978', bg: '#b8231a' })), 0, 2.55, stallAt.zFront - 0.001, Math.PI));
    const tube = new THREE.Mesh(new THREE.BoxGeometry(stallAt.w - 0.4, 0.04, 0.08), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xfff2d0, emissiveIntensity: 3.5 }));
    tube.position.set(0, 2.12, stallAt.zFront + 0.2); g.add(tube);
    // glass display: chrome frame, panes, hanging roast chickens
    const gx = 1.0, gz = stallAt.zFront + 0.33;
    g.add(box(2.0, 0.04, 0.6, LIB.steel, gx, 1.72, gz));
    for (const dx of [-1, 1]) for (const dz of [-0.29, 0.29]) g.add(box(0.04, 0.78, 0.04, LIB.chrome, gx + dx, 1.35, gz + dz));
    g.add(plane(2.0, 0.74, LIB.glass, gx, 1.35, gz - 0.29));
    g.add(plane(2.0, 0.74, LIB.glass, gx, 1.35, gz + 0.29));
    for (let i = 0; i < 3; i++) {
      const cx = gx - 0.6 + i * 0.6;
      g.add(cyl(0.006, 0.006, 0.22, LIB.chrome, cx, 1.62, gz, 6));
      const bird = new THREE.Mesh(new THREE.SphereGeometry(0.17, 16, 12), glaze);
      bird.scale.set(0.8, 1.3, 0.75); bird.position.set(cx, 1.3, gz); bird.castShadow = true; g.add(bird);
      g.add(sph(0.07, glaze, cx + 0.04, 1.5, gz, 10, 8));
    }
    g.add(plane(0.22, 0.22, signMat(pickSign(['grade']), fb({ title: 'A', sub: 'NEA', bg: '#2a7a3b', w: 256, h: 256 })), stallAt.w / 2 - 0.3, 1.5, stallAt.zFront + 0.005, Math.PI));
  }
  // back of stall (always blockout): side walls, back tiles, wok station, shelves
  const tubeLight = new THREE.PointLight(0xffd9a0, 1.6, 9, 2); // warm interior glow against the cool hall
  tubeLight.position.set(0, 2.0, stallAt.zFront + 0.25); g.add(tubeLight);
  g.add(box(0.12, 2.9, d, LIB.paint_cream, -stallAt.w / 2 - 0.06, 1.45, zc));
  g.add(box(0.12, 2.9, d, LIB.paint_cream, stallAt.w / 2 + 0.06, 1.45, zc));
  const backMat = paint(new THREE.MeshStandardMaterial({ color: 0x9a8f78, roughness: 0.85 }), { mottle: 0.14, wear: 0.1 }); // matte tan so the back kitchen hatch does not read white
  const backTiles = new THREE.Mesh(uvScale(new THREE.BoxGeometry(stallAt.w, 2.9, 0.08), 3.6, 2.9, 2.4), backMat);
  backTiles.position.set(0, 1.45, stallAt.zBack - 0.1); backTiles.receiveShadow = true; g.add(backTiles);
  // green tile band on the back wall, a menu board above the shelves
  g.add(box(stallAt.w, 1.2, 0.06, LIB.paint_green, 0, 0.6, stallAt.zBack - 0.16));
  g.add(plane(1.6, 0.5, signMat(pickSign(['sign_menu_1']), fb({ title: 'CHICKEN RICE $4', sub: 'set $6', bg: '#2d2a26' })), -0.6, 2.75, stallAt.zBack - 0.15, Math.PI));
  // a rail of roast birds hanging over the prep counter
  // the stall_front glb is only 0.9 m deep (back tiles at zFront + 0.94), so everything lives in that band
  const zr = stallAt.zFront + 0.68;
  // the glb's steel side panel hides anything left of x -0.7 from the hall, so the birds hang over the visible counter
  g.add(box(1.0, 0.03, 0.03, LIB.chrome, -0.35, 1.95, zr));
  for (const cx of [-0.6, -0.15]) {
    g.add(cyl(0.006, 0.006, 0.2, LIB.chrome, cx, 1.86, zr, 6));
    const bird = new THREE.Mesh(new THREE.SphereGeometry(0.19, 16, 12), glaze);
    bird.scale.set(0.85, 1.4, 0.8); bird.position.set(cx, 1.52, zr); bird.castShadow = true; g.add(bird);
    g.add(sph(0.08, glaze, cx + 0.04, 1.76, zr, 10, 8));
  }
  // chopping board and cleaver on the counter
  g.add(box(0.45, 0.05, 0.3, LIB.wood, 0.0, 0.97, stallAt.zFront + 0.55));
  g.add(box(0.2, 0.01, 0.1, LIB.steel, 0.05, 1.0, stallAt.zFront + 0.55));
  const wz = stallAt.zFront + 0.7;
  g.add(box(0.9, 0.85, 0.5, LIB.steel, -1.3, 0.425, wz));
  const steamAt = [];
  const wokGlb = await A.loadGlb(A.list('/assets/props/', '.glb').find((p) => /stockpot|wok/i.test(p)) || '');
  if (wokGlb) {
    const w = wokGlb.scene; apply(w); w.position.set(-1.3, 0.85, wz); g.add(w);
    used.assets.push('prop:stockpot_wok.glb');
    g.updateMatrixWorld(true);
    w.traverse((o) => { if (/^steam_/i.test(o.name)) steamAt.push(o.getWorldPosition(new THREE.Vector3())); });
  } else {
    const wok = new THREE.Mesh(new THREE.SphereGeometry(0.34, 20, 10, 0, Math.PI * 2, 0, Math.PI * 0.45), LIB.rubber);
    wok.rotation.x = Math.PI; wok.position.set(-1.3, 1.08, wz); wok.castShadow = true; g.add(wok);
    steamAt.push(new THREE.Vector3(stallAt.x - 1.3, 1.15, wz));
  }
  const flame = new THREE.PointLight(0xff9a3a, 2.5, 2.5, 2); flame.position.set(-1.3, 0.95, wz); g.add(flame);
  const pz = stallAt.zFront + 0.75;
  g.add(cyl(0.22, 0.2, 0.3, LIB.steel, -0.4, 1.1, pz, 20));
  g.add(cyl(0.23, 0.23, 0.05, LIB.plastic, -0.4, 1.275, pz, 20));
  // one shelf low enough to show under the lintel, bowls stacked up top out of sight
  const sz = stallAt.zFront + 0.74;
  g.add(box(3.2, 0.04, 0.22, LIB.steel, 0, 1.5, sz));
  // sauce bottles in broad painted colours, bowl stacks on the top shelf
  const sauces = [0x7a1d12, 0xd23a1a, 0xe0a020, 0x2f7a4e, 0x3a2a1a].map((c) => paint(new THREE.MeshStandardMaterial({ color: c, roughness: 0.3 }), { mottle: 0.12 }));
  for (let i = 0; i < 7; i++) {
    const x = -1.4 + i * 0.3, m = sauces[i % sauces.length];
    g.add(cyl(0.07, 0.08, 0.4, m, x, 1.72, sz + 0.03, 10));
    g.add(cyl(0.03, 0.04, 0.09, m, x, 1.96, sz + 0.03, 8));
  }
  // jars on the lower shelf: wide, cream and brown, painted lids
  for (const [x, c] of [[0.75, 0xe8d8b0], [1.1, 0x7a4a22], [1.45, 0xe8d8b0], [0.4, 0x9a6a30]]) {
    const jm = paint(new THREE.MeshStandardMaterial({ color: c, roughness: 0.5 }), { mottle: 0.12 });
    g.add(cyl(0.13, 0.12, 0.26, jm, x, 1.65, sz - 0.02, 14));
    g.add(cyl(0.11, 0.13, 0.04, LIB.paint_red, x, 1.8, sz - 0.02, 14));
  }
  // kitchen exhaust: hood duct up from the stall roof to a run along the ceiling, boxes stored on top
  const duct = paint(new THREE.MeshStandardMaterial({ color: 0x9a9ea0, roughness: 0.5, metalness: 0.8 }), { wear: 0.5, wearColor: 0xc8ccce, metalWear: 1, mottle: 0.05 });
  g.add(box(0.55, 1.5, 0.55, duct, -1.2, 3.65, stallAt.zBack - 0.6));
  g.add(box(0.55, 0.45, 5.0, duct, -1.2, 4.1, stallAt.zBack - 3.0));
  const carton = paint(new THREE.MeshStandardMaterial({ color: 0xb08a5a, roughness: 0.95 }), { wear: 0.35, wearColor: 0xd8c09a, mottle: 0.08 });
  for (const [x, z, w, h] of [[0.4, stallAt.zBack - 0.9, 0.6, 0.4], [1.05, stallAt.zBack - 1.0, 0.5, 0.35], [0.5, stallAt.zBack - 0.9, 0.45, 0.3]]) g.add(box(w, h, 0.5, carton, x, 2.95 + h / 2 + (w < 0.5 ? 0.4 : 0), z));
  scene.add(g);
  steamAt.push(new THREE.Vector3(stallAt.x - 0.4, 1.3, pz));
  scene.userData.steamAt = steamAt;
  // neighbour stalls: roller shutters down, closed for the afternoon
  const shutter = paint(new THREE.MeshStandardMaterial({ color: 0x22384a, roughness: 0.9, metalness: 0.1 }), { wear: 0.3, wearColor: 0x44606c, mottle: 0.1 }); // saturated enough to stay blue in full sun
  for (const [x, w] of [[-6.8, 3.6], [2.6, 3.6]]) {
    const s = new THREE.Group();
    s.position.set(x, 0, 0);
    const sh = box(w, 2.2, 0.06, shutter, 0, 1.1, stallAt.zFront + 0.5);
    s.add(sh);
    for (let y = 0.15; y < 2.2; y += 0.12) s.add(box(w, 0.02, 0.08, LIB.rubber, 0, y, stallAt.zFront + 0.5));
    s.add(box(w + 0.24, 0.8, 0.3, LIB.paint_cream, 0, 2.55, stallAt.zFront + 0.15));
    s.add(plane(w - 0.3, 0.6, signMat(pickSign(['sign_drinks']), fb({ title: 'KOPI  TEH  MILO', sub: 'drinks stall', bg: '#2d6a8a' })), 0, 2.55, stallAt.zFront - 0.001, Math.PI));
    scene.add(s);
  }
  // wall signs: no smoking and tray return
  scene.add(plane(0.6, 0.42, signMat(pickSign(['nosmoke']), fb({ title: 'NO SMOKING', sub: 'fine $1000', bg: '#f1ede2', fg: '#b8231a', accent: '#b8231a', w: 512, h: 360 })), 2.4, 2.4, -0.74, Math.PI));
  scene.add(plane(0.7, 0.5, signMat(pickSign(['sign_tray']), fb({ title: 'RETURN YOUR TRAY', sub: 'keep the tables clean', bg: '#2a7a3b' })), -4.6, 2.3, -0.74, Math.PI));

  // ---- furniture slots: tables with fixed stools, from glb if present
  const propGlbs = A.list('/assets/props/', '.glb');
  const find = (re) => propGlbs.find((p) => re.test(p.split('/').pop()));
  async function slot(name, re, places, blockoutFn) {
    const p = find(re);
    const g = p ? await A.loadGlb(p) : null;
    if (g) {
      used.assets.push('prop:' + p.split('/').pop());
      apply(g.scene);
      for (const [x, z, ry, y] of places) {
        const c = g.scene.clone();
        c.position.set(x, y || 0, z); c.rotation.y = ry || 0;
        scene.add(c);
      }
    } else {
      used.blockout.push('prop:' + name);
      for (const [x, z, ry] of places) {
        const c = blockoutFn();
        c.position.set(x, 0, z); c.rotation.y = ry || 0;
        scene.add(c);
      }
    }
  }
  const tableTop = new THREE.Mesh(uvScale(new THREE.BoxGeometry(0.78, 0.04, 0.78), 0.78, 0.78, sets.formica.metres), LIB.formica);
  tableTop.castShadow = tableTop.receiveShadow = true;
  function blockTable() {
    const g = new THREE.Group();
    const top = tableTop.clone(); top.position.y = 0.74; g.add(top);
    g.add(box(0.8, 0.04, 0.8, LIB.chrome, 0, 0.735, 0));
    g.add(cyl(0.04, 0.04, 0.7, LIB.steel, 0, 0.36, 0, 12));
    g.add(cyl(0.28, 0.32, 0.03, LIB.steel, 0, 0.015, 0, 20));
    for (let i = 0; i < 4; i++) {
      const a = i * Math.PI / 2 + Math.PI / 4, r = 0.62;
      const sx = Math.cos(a) * r, sz = Math.sin(a) * r;
      g.add(cyl(0.035, 0.035, 0.42, LIB.steel, sx, 0.21, sz, 10));
      const bar = box(r, 0.03, 0.03, LIB.steel, sx / 2, 0.06, sz / 2); bar.rotation.y = -a; g.add(bar);
      const seat = cyl(0.17, 0.15, 0.06, i % 2 ? LIB.plastic_green : LIB.plastic, sx, 0.45, sz, 22);
      g.add(seat);
    }
    return g;
  }
  await slot('table', /table/i, [[-1.5, -2.7, 0.08], [-3.6, -2.7, -0.05], [-1.5, -4.9, 0.12], [1.2, -4.6, -0.1], [-3.6, -4.9, 0.02], [-6.3, -3.0, 0.1]], blockTable);

  // tray return rack, a bin, a kettle on the floor, a tissue packet chope
  function blockRack() {
    const g = new THREE.Group();
    for (const dx of [-0.45, 0.45]) for (const dz of [-0.25, 0.25]) g.add(cyl(0.02, 0.02, 1.5, LIB.steel, dx, 0.75, dz, 8));
    for (const y of [0.35, 0.8, 1.25]) g.add(box(0.96, 0.03, 0.56, LIB.steel, 0, y, 0));
    const trayMat = paint(new THREE.MeshStandardMaterial({ color: 0x8c2e22, roughness: 0.5 }), { wear: 0.6, wearColor: 0xd08c7c });
    for (let i = 0; i < 5; i++) g.add(box(0.44, 0.02, 0.32, trayMat, -0.22 + (i % 2) * 0.44, 0.82 + Math.floor(i / 2) * 0.03, 0));
    return g;
  }
  await slot('rack', /rack|tray/i, [[-4.6, -1.9, 0], [0.75, 1.3, 0.2]], blockRack);
  function blockBin() {
    const g = new THREE.Group();
    g.add(box(0.55, 0.95, 0.5, LIB.plastic_green, 0, 0.48, 0));
    g.add(box(0.58, 0.06, 0.53, LIB.plastic_green, 0, 0.98, 0));
    return g;
  }
  await slot('bin', /bin/i, [[-3.0, -2.3, 0.2]], blockBin);
  function blockTissue() {
    const g = new THREE.Group();
    g.add(box(0.1, 0.03, 0.06, paint(new THREE.MeshStandardMaterial({ color: 0xf4f6ff, roughness: 0.5 }), { mottle: 0.02 }), 0, 0.775, 0));
    g.add(box(0.1, 0.031, 0.02, LIB.plastic_green, 0, 0.776, 0));
    return g;
  }
  await slot('tissue', /tissue/i, [[-1.35, -2.55, 0.5], [1.05, -4.4, -0.3], [-3.45, -2.6, 0.8]], blockTissue);
  function blockPlate() {
    const g = new THREE.Group();
    g.add(cyl(0.12, 0.09, 0.02, LIB.ceramic, 0, 0.77, 0, 20));
    const rice = paint(new THREE.MeshStandardMaterial({ color: 0xf0e6c8, roughness: 0.8 }), { mottle: 0.1 });
    g.add(sph(0.06, rice, 0.03, 0.79, 0, 12, 8));
    g.add(cyl(0.035, 0.03, 0.09, LIB.glass, -0.22, 0.805, 0.12, 12));
    return g;
  }
  await slot('teh', /teh|tarik/i, [[-1.2, -2.55, 0.4], [1.4, -4.35, -0.2], [-3.8, -4.7, 0.9]], () => new THREE.Group());
  await slot('tubes', /fluorescent|tube/i, [[-2.6, -5.6, 0, 4.4], [1.2, -5.6, 0, 4.4], [-6.5, -5.6, 0, 4.4], [-1.6, -1.3, 0, 4.4], [-6.1, -1.3, 0, 4.4], [2.6, -1.3, 0, 4.4], [-1.6, 3.0, 0, 4.4], [-6.1, 3.0, 0, 4.4], [2.6, 3.0, 0, 4.4]], () => new THREE.Group());
  await slot('plate', /plate|bowl/i, [[-1.7, -2.85, 0.3], [-1.3, -4.75, 1.2], [-3.75, -2.85, 0.6], [-2.1, 1.9, 0.4, 0.95]], blockPlate);

  // ---- ceiling fans
  const fans = [];
  function blockFan() {
    const g = new THREE.Group();
    g.add(cyl(0.02, 0.02, 0.8, LIB.rubber, 0, 3.75, 0, 8));
    g.add(cyl(0.12, 0.14, 0.2, LIB.paint_cream, 0, 3.3, 0, 16));
    const blades = new THREE.Group();
    blades.position.y = 3.25;
    for (let i = 0; i < 3; i++) {
      const b = box(0.62, 0.012, 0.11, LIB.paint_cream, 0.42, 0, 0);
      const arm = new THREE.Group(); arm.rotation.y = i * Math.PI * 2 / 3; arm.add(b);
      b.rotation.x = 0.2; blades.add(arm);
    }
    g.add(blades);
    g.userData.blades = blades;
    return g;
  }
  const fanGlb = find(/fan/i) ? await A.loadGlb(find(/fan/i)) : null;
  for (const [x, z] of [[-2.6, -3.2], [1.2, -3.2], [-6.5, -3.2], [-2.6, 0.6], [1.2, 0.6], [-6.5, 0.6]]) {
    let f;
    if (fanGlb) { f = fanGlb.scene.clone(); apply(f); f.position.set(x, 4.4, z); f.traverse((o) => { if (/blade|rotor/i.test(o.name)) f.userData.blades = o; }); }
    else { f = blockFan(); f.position.set(x, 0, z); }
    scene.add(f); fans.push(f);
  }
  (fanGlb ? used.assets : used.blockout).push('prop:fan');

  // ---- Ah Ma
  const fill = new THREE.DirectionalLight(0x8fc0d4, 0.8); // teal bounce from the hall
  scene.add(new THREE.HemisphereLight(0x3a6a94, 0x8a4a28, 0.5)); // deep teal down, warm floor bounce up
  fill.position.set(4, 3, -9);
  scene.add(fill);
  const heroGroup = new THREE.Group();
  heroGroup.position.set(-0.55, 0, -1.35);
  heroGroup.rotation.y = -0.45;
  scene.add(heroGroup);
  let mixer = null;
  const heroGlb = await A.loadGlb('/assets/heroes/ahma.glb');
  if (heroGlb) {
    // authored PBR: only the sun rim from the paint library, no wear, mottle or gradient
    // her albedo carries painted light bands already, so the toon ramp is softened on her, teal rim, eyes and glasses kept crisp
    heroGlb.scene.traverse((o) => {
      if (!o.isMesh) return;
      o.castShadow = o.receiveShadow = true;
      const crisp = /eyes|headgear/i.test(o.name);
      paint(o.material, { wear: 0, mottle: 0, gradient: 0, rim: 1.3, rimColor: 0x4fd6dc, toon: /head/i.test(o.name) ? 0.3 : 0.45, stroke: 0, sign: crisp });
      const si = o.morphTargetDictionary?.smile;
      if (si != null) o.morphTargetInfluences[si] = 0.25; // idle has no weight tracks, so this holds
    });
    heroGroup.add(heroGlb.scene);
    if (heroGlb.animations.length) {
      mixer = new THREE.AnimationMixer(heroGlb.scene);
      const clip = heroGlb.animations.find((c) => /idle/i.test(c.name)) || heroGlb.animations[0];
      mixer.clipAction(clip).play();
    }
    used.assets.push('hero:ahma.glb');
  } else {
    used.blockout.push('hero:ahma');
    heroGroup.add(blockAhMa());
  }

  // ---- steam, dust and light shafts
  const sprite = T.softSprite();
  // steam as a few painted puffs that tumble, not a soft particle haze
  const steam = makeParticles({ count: Math.max(12, R.preset.steam >> 3), sprite: T.puffSprite(), emitters: scene.userData.steamAt, rnd, life: 2.6, rise: 0.22, spread: 0.28, size: 0.55, grow: 1.3, color: 0xfff6ea, opacity: 0.5, spin: 1 });
  steam.userData.fx = true; scene.add(steam);
  const dust = makeParticles({ count: R.preset.steam, sprite, emitters: [new THREE.Vector3(-5, 1.8, -2.5)], rnd, life: 12, rise: 0.04, spread: 4.5, size: 0.025, grow: 1.0, color: 0xffd9a0, opacity: 0.9, drift: 0.12 });
  dust.userData.fx = true; scene.add(dust);
  const shafts = makeShafts(R, { count: R.preset.shafts, rnd });
  shafts.userData.fx = true; scene.add(shafts);

  R.fitShadow(SCENE_BOX);
  if (R.passes.gtao) R.passes.gtao.setSceneClipBox(SCENE_BOX);

  function update(t, dt) {
    for (const f of fans) if (f.userData.blades) f.userData.blades.rotation.y = t * Math.PI * 2 * 1.1;
    steam.material.uniforms.uTime.value = t;
    dust.material.uniforms.uTime.value = t;
    shafts.material.uniforms.uTime.value = t;
    if (mixer) mixer.setTime(t % 10);
  }
  function setShot(name) {
    heroGroup.visible = !!SHOTS[name]?.hero;
  }
  return { scene, update, setShot, used };
}

// Blockout Ah Ma: a squat caricature stand-in with a walker. The hero
// designer's glb replaces it as soon as assets/heroes/ahma.glb lands.
function blockAhMa() {
  const g = new THREE.Group();
  const skin = LIB.skin, cloth = LIB.cloth, hair = LIB.hair;
  const pants = paint(new THREE.MeshStandardMaterial({ color: 0x2a2a30, roughness: 0.9 }), { mottle: 0.05, rim: 0.6 });
  // legs and slippers
  for (const dx of [-0.11, 0.11]) {
    g.add(cyl(0.085, 0.1, 0.42, pants, dx, 0.27, 0, 12));
    const s = box(0.11, 0.035, 0.22, LIB.rubber, dx, 0.02, -0.03); g.add(s);
  }
  // body: wide samfu top, slight hunch
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.26, 0.28, 6, 18), cloth);
  body.scale.set(1.0, 1.0, 0.85); body.position.set(0, 0.68, 0.02); body.rotation.x = 0.12; body.castShadow = body.receiveShadow = true; g.add(body);
  // floral: a few dots painted on as small discs
  const floral = paint(new THREE.MeshStandardMaterial({ color: 0xe9c7a8, roughness: 0.85 }), { mottle: 0.05, rim: 0.6 });
  for (let i = 0; i < 10; i++) {
    const a = i * 1.7, r = 0.27, y = 0.55 + (i % 4) * 0.09;
    const d = cyl(0.025, 0.025, 0.01, floral, Math.cos(a) * r, y, Math.sin(a) * r * 0.85 + 0.02, 8);
    d.lookAt(d.position.x * 2, y, d.position.z * 2); d.rotateX(Math.PI / 2); g.add(d);
  }
  // arms gripping the walker
  for (const dx of [-0.3, 0.3]) {
    const up = new THREE.Mesh(new THREE.CapsuleGeometry(0.06, 0.22, 4, 10), cloth);
    up.position.set(dx, 0.72, -0.06); up.rotation.x = -1.0; up.rotation.z = dx > 0 ? -0.15 : 0.15; up.castShadow = true; g.add(up);
    const hand = sph(0.062, skin, dx * 0.95, 0.72, -0.3, 12, 10); g.add(hand);
  }
  // head: big, with a bun, glasses, brows, a mouth set in a scowl
  const head = sph(0.2, skin, 0, 1.13, -0.02, 24, 18); head.scale.set(1, 1.08, 1); g.add(head);
  const cap = sph(0.21, hair, 0, 1.22, 0.05, 20, 14); cap.scale.set(1, 0.7, 1); g.add(cap);
  g.add(sph(0.09, hair, 0, 1.3, 0.14, 14, 10));
  const dark = paint(new THREE.MeshStandardMaterial({ color: 0x1a1412, roughness: 0.4 }), { rim: 0.3 });
  for (const dx of [-0.075, 0.075]) {
    g.add(sph(0.032, dark, dx, 1.14, -0.19, 10, 8));
    const brow = box(0.075, 0.018, 0.02, dark, dx, 1.19, -0.2); brow.rotation.z = dx > 0 ? 0.35 : -0.35; g.add(brow);
    const lens = new THREE.Mesh(new THREE.TorusGeometry(0.05, 0.006, 6, 18), LIB.chrome); lens.position.set(dx, 1.14, -0.2); g.add(lens);
  }
  const mouth = box(0.07, 0.014, 0.02, dark, 0, 1.03, -0.195); mouth.rotation.z = 0.1; g.add(mouth);
  // walker
  const w = new THREE.Group(); w.position.set(0, 0, -0.42);
  for (const dx of [-0.27, 0.27]) {
    w.add(cyl(0.013, 0.013, 0.75, LIB.chrome, dx, 0.375, 0.1, 8));
    w.add(cyl(0.013, 0.013, 0.75, LIB.chrome, dx, 0.375, -0.15, 8));
    const top = box(0.03, 0.03, 0.3, LIB.chrome, dx, 0.75, -0.02); w.add(top);
    const grip = box(0.04, 0.04, 0.14, LIB.rubber, dx, 0.76, 0.05); w.add(grip);
    for (const dz of [0.1, -0.15]) w.add(cyl(0.025, 0.03, 0.03, LIB.rubber, dx, 0.015, dz, 8));
  }
  w.add(box(0.56, 0.025, 0.025, LIB.chrome, 0, 0.35, -0.15));
  g.add(w);
  return g;
}

// Deterministic particles: position is a pure function of seed and time.
function makeParticles({ count, sprite, emitters, rnd, life, rise, spread, size, grow, color, opacity, drift = 0.3, spin = 0 }) {
  const n = count;
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(n * 3), rand = new Float32Array(n * 4);
  for (let i = 0; i < n; i++) {
    const e = emitters[i % emitters.length];
    pos.set([e.x, e.y, e.z], i * 3);
    rand.set([rnd(), rnd(), rnd(), rnd()], i * 4);
  }
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('aRand', new THREE.BufferAttribute(rand, 4));
  const mat = new THREE.ShaderMaterial({
    uniforms: { uTime: { value: 0 }, uMap: { value: sprite }, uLife: { value: life }, uRise: { value: rise }, uSpread: { value: spread }, uSize: { value: size }, uGrow: { value: grow }, uColor: { value: new THREE.Color(color) }, uOpacity: { value: opacity }, uDrift: { value: drift }, uScale: { value: 1080 }, uSpin: { value: spin } },
    vertexShader: /* glsl */ `
      attribute vec4 aRand; uniform float uTime, uLife, uRise, uSpread, uSize, uGrow, uDrift, uScale, uSpin;
      varying float vA, vRot;
      void main() {
        float age = mod(uTime + aRand.x * uLife, uLife);
        float k = age / uLife;
        float ang = aRand.y * 6.2832 + age * (0.6 + aRand.w);
        vec3 p = position;
        p.x += (aRand.y - 0.5) * uSpread * 0.25 + cos(ang) * uDrift * k + sin(age * 0.7 + aRand.z * 9.0) * 0.05;
        p.z += (aRand.z - 0.5) * uSpread * 0.25 + sin(ang) * uDrift * k;
        p.y += age * uRise + (aRand.w - 0.5) * uSpread * 0.08;
        if (uSpread > 1.0) { p.x += (aRand.y - 0.5) * uSpread * 2.0; p.z += (aRand.z - 0.5) * uSpread * 2.0; p.y += (aRand.w - 0.5) * 2.0; }
        vec4 mv = modelViewMatrix * vec4(p, 1.0);
        gl_Position = projectionMatrix * mv;
        float s = uSize * (1.0 + k * uGrow);
        gl_PointSize = s * uScale / max(-mv.z, 0.1);
        vA = sin(k * 3.1416) * (0.6 + 0.4 * aRand.x);
        vRot = uSpin * (aRand.y * 6.2832 + age * (aRand.z - 0.5) * 1.2);
      }`,
    fragmentShader: /* glsl */ `
      uniform sampler2D uMap; uniform vec3 uColor; uniform float uOpacity; varying float vA, vRot;
      void main() {
        vec2 c = gl_PointCoord - 0.5; float cs = cos(vRot), sn = sin(vRot);
        vec4 t = texture2D(uMap, vec2(c.x * cs - c.y * sn, c.x * sn + c.y * cs) + 0.5);
        gl_FragColor = vec4(uColor * t.rgb * 1.3, t.a * vA * uOpacity); }`, // lifted past AgX mid grey so the puffs read white
    transparent: true, depthWrite: false, blending: THREE.NormalBlending,
  });
  const pts = new THREE.Points(geo, mat);
  pts.frustumCulled = false;
  return pts;
}

// Light shafts: one draw call of cylinder-billboarded strips along the sun
// direction, additive, soft edged and fading along their length.
function makeShafts(R, { count, rnd }) {
  const axis = R.sunDir.clone().negate(); // direction the light travels
  const geo = new THREE.BufferGeometry();
  const verts = count * 4;
  const center = new Float32Array(verts * 3), corner = new Float32Array(verts * 2), param = new Float32Array(verts * 3);
  const idx = [];
  for (let i = 0; i < count; i++) {
    // start high at the open side, travel along the sun into the room
    const z = -9 + rnd() * 12, y = 3.0 + rnd() * 1.2, x = -9.8;
    const len = 8 + rnd() * 6, w = 0.12 + rnd() * 0.45, seed = rnd();
    const cx = x + axis.x * len * 0.5, cy = y + axis.y * len * 0.5, cz = z + axis.z * len * 0.5;
    const cs = [[-1, -1], [1, -1], [1, 1], [-1, 1]];
    for (let k = 0; k < 4; k++) {
      const v = i * 4 + k;
      center.set([cx, cy, cz], v * 3);
      corner.set(cs[k], v * 2);
      param.set([len, w, seed], v * 3);
    }
    idx.push(i * 4, i * 4 + 1, i * 4 + 2, i * 4, i * 4 + 2, i * 4 + 3);
  }
  geo.setAttribute('position', new THREE.BufferAttribute(center, 3));
  geo.setAttribute('aCorner', new THREE.BufferAttribute(corner, 2));
  geo.setAttribute('aParam', new THREE.BufferAttribute(param, 3));
  geo.setIndex(idx);
  const mat = new THREE.ShaderMaterial({
    uniforms: { uAxis: { value: axis }, uTime: { value: 0 }, uColor: { value: new THREE.Color(1.0, 0.72, 0.42) }, uStrength: { value: 0.14 } },
    vertexShader: /* glsl */ `
      attribute vec2 aCorner; attribute vec3 aParam; uniform vec3 uAxis;
      varying vec2 vC; varying float vSeed; varying float vDepth;
      void main() {
        vec3 toCam = cameraPosition - position;
        vec3 side = normalize(cross(uAxis, normalize(toCam)));
        vec3 p = position + uAxis * aCorner.x * aParam.x * 0.5 + side * aCorner.y * aParam.y * 0.5;
        vC = aCorner; vSeed = aParam.z;
        vec4 mv = modelViewMatrix * vec4(p, 1.0);
        vDepth = -mv.z;
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: /* glsl */ `
      uniform vec3 uColor; uniform float uTime, uStrength; varying vec2 vC; varying float vSeed, vDepth;
      void main() {
        float across = 1.0 - vC.y * vC.y;
        across = across * across;
        float along = smoothstep(-1.0, -0.4, vC.x) * (1.0 - smoothstep(0.1, 1.0, vC.x));
        float flick = 0.75 + 0.25 * sin(uTime * 0.6 + vSeed * 40.0 + vC.x * 3.0);
        float near = smoothstep(0.5, 3.0, vDepth);
        float stroke = 0.7 + 0.3 * sin(vC.y * 11.0 + vSeed * 30.0) * sin(vC.x * 5.0 + vSeed * 7.0); // bristle bands, reads as a painted stroke
        gl_FragColor = vec4(uColor * across * along * flick * near * stroke * uStrength, 1.0);
      }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.frustumCulled = false;
  return mesh;
}
