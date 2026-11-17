// Asset discovery. Other agents drop files into assets/. We load what exists
// and fall back to the blockout for the rest. import.meta.glob is resolved by
// vite at transform time, so a page reload after a file lands picks it up.
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

const FILES = import.meta.glob('/assets/**/*.{glb,png,jpg,jpeg,webp}', { query: '?url', import: 'default', eager: true });

export const paths = Object.keys(FILES).sort();
export const url = (p) => FILES[p];
export const has = (p) => p in FILES;
export const list = (dir, ext) => paths.filter((p) => p.startsWith(dir) && (!ext || p.endsWith(ext)));

const gltf = new GLTFLoader();
const tex = new THREE.TextureLoader();

export function loadGlb(p) {
  if (!has(p)) return Promise.resolve(null);
  return gltf.loadAsync(url(p)).catch((e) => { console.warn('glb failed', p, e); return null; });
}

export function loadTex(p, { srgb = true, repeat = 1 } = {}) {
  if (!has(p)) return null;
  const t = tex.load(url(p));
  t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeat, repeat);
  t.anisotropy = 8;
  return t;
}

// Find a texture for a material set by loose name matching.
// set: 'tile' | 'formica' | 'steel' | 'concrete' | 'wood' | 'plastic'
// kind: 'color' | 'normal' | 'orm' | 'rough'
const KIND = {
  color: ['basecolor', 'base_color', 'albedo', 'color', 'diffuse', 'col'],
  normal: ['normal', 'nrm', 'nor'],
  orm: ['orm', 'arm', 'occlusionroughnessmetallic'],
  rough: ['rough', 'rgh'],
};
export function findTex(set, kind) {
  const alts = set === 'steel' ? ['steel', 'stainless', 'metal'] : [set];
  for (const p of list('/assets/tex/')) {
    const n = p.toLowerCase().split('/').pop();
    if (!alts.some((a) => n.includes(a))) continue;
    if (KIND[kind].some((k) => n.includes(k))) return p;
  }
  return null;
}
