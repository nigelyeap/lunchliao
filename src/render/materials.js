// Stylised hand-painted PBR material library.
// paint(material) injects: rim light from the sun, edge wear from screen-space
// curvature, a painted mottle and a world-height gradient. applyByName()
// swaps glb materials by mesh name prefix and paints whatever is left.
import * as THREE from 'three';

// Shared uniforms, one object so every painted material updates together.
export const shared = {
  uRimDir: { value: new THREE.Vector3(0, 0, 1) }, // sun dir in view space
  uRimColor: { value: new THREE.Color(1.0, 0.6, 0.22) }, // bold golden rim
  uRimPower: { value: 2.4 },
  uRimStrength: { value: 0.95 },
  uToon: { value: 0.85 }, // 0 smooth PBR, 1 stepped three-band ramp
  uStroke: { value: 0.2 }, // world-space brush strokes on albedo
  uGradY: { value: new THREE.Vector2(0.0, 2.6) }, // world height band for the painted gradient
  uGradLow: { value: new THREE.Color(0.80, 0.74, 0.70) },
  uGradHigh: { value: new THREE.Color(1.0, 1.01, 1.06) },
  uMottle: { value: 0.13 },
  uWear: { value: 0.0 },
  uWearColor: { value: new THREE.Color(0.9, 0.86, 0.78) },
};

const GLSL_NOISE = /* glsl */ `
float ll_hash(vec3 p) { p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
float ll_vnoise(vec3 x) {
  vec3 i = floor(x); vec3 f = fract(x); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(ll_hash(i + vec3(0,0,0)), ll_hash(i + vec3(1,0,0)), f.x),
                 mix(ll_hash(i + vec3(0,1,0)), ll_hash(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(ll_hash(i + vec3(0,0,1)), ll_hash(i + vec3(1,0,1)), f.x),
                 mix(ll_hash(i + vec3(0,1,1)), ll_hash(i + vec3(1,1,1)), f.x), f.y), f.z);
}
float ll_fbm(vec3 p) { return ll_vnoise(p) * 0.6 + ll_vnoise(p * 2.3) * 0.3 + ll_vnoise(p * 5.1) * 0.1; }
`;

export function paint(mat, opts = {}) {
  if (mat.userData.painted) return mat;
  mat.userData.painted = true;
  const o = {
    wear: 0.0, wearColor: null, wearRough: 0.15, metalWear: 0.0,
    mottle: null, rim: 1.0, gradient: 1.0, stroke: 1.0, sign: false, toon: 1.0, rimColor: null, ...opts,
  };
  mat.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, shared, {
      uWearLocal: { value: o.wear },
      uWearColLocal: { value: o.wearColor ? new THREE.Color(o.wearColor) : shared.uWearColor.value },
      uWearRough: { value: o.wearRough },
      uMetalWear: { value: o.metalWear },
      uMottleLocal: { value: o.mottle ?? -1 },
      uRimMul: { value: o.rim },
      uGradMul: { value: o.gradient },
      uStrokeMul: { value: o.stroke },
      uToonMul: { value: o.toon },
    });
    if (o.rimColor) shader.uniforms.uRimColor = { value: new THREE.Color(o.rimColor) };
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vLLWorld;')
      .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvLLWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>
varying vec3 vLLWorld;
uniform vec3 uRimDir, uRimColor, uGradLow, uGradHigh, uWearColLocal;
uniform vec2 uGradY;
uniform float uRimPower, uRimStrength, uMottle, uWearLocal, uWearRough, uMetalWear, uMottleLocal, uRimMul, uGradMul, uToon, uStroke, uStrokeMul, uToonMul;
${GLSL_NOISE}
// stretched value noise, tilted: reads as brush strokes about 3 per metre across, 4:1 long
float ll_strokes(vec2 p) { vec2 q = mat2(0.87, 0.5, -0.5, 0.87) * p; return ll_vnoise(vec3(q.x * 0.8, q.y * 3.2, 0.0)) * 0.6 + ll_vnoise(vec3(q.x * 1.6 + 7.0, q.y * 6.0, 3.0)) * 0.4; }
// three soft-edged bands: shadow, half tone, light
float ll_ramp(float x) { float r = smoothstep(0.06, 0.16, x) * 0.42 + smoothstep(0.42, 0.56, x) * 0.58; return mix(x, r, uToon * uToonMul); }`)
      .replace('#include <lights_physical_pars_fragment>', THREE.ShaderChunk.lights_physical_pars_fragment.replace('reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );', 'reflectedLight.directDiffuse += ll_ramp(saturate((dot(geometryNormal, directLight.direction) + 0.5) / 1.5)) * directLight.color * BRDF_Lambert( material.diffuseColor );')) // diffuse only: ramped and wrapped so the key creeps round the form, specular keeps the real dotNL
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
{
  // painted gradient: darker and warmer toward the floor
  float gy = smoothstep(uGradY.x, uGradY.y, vLLWorld.y);
  diffuseColor.rgb *= mix(vec3(1.0), mix(uGradLow, uGradHigh, gy), uGradMul);
  // hand-painted mottle: low frequency albedo and roughness wobble
  float m = uMottleLocal < 0.0 ? uMottle : uMottleLocal;
  float n = ll_fbm(vLLWorld * 1.7) - 0.5;
  diffuseColor.rgb *= 1.0 + n * 2.0 * m * vec3(1.3, 1.0, 0.7); // warm where it lifts, cool where it drops
  // triplanar brush strokes that follow the surface
  vec3 wn = abs(normalize(cross(dFdx(vLLWorld), dFdy(vLLWorld)))); wn = pow(wn, vec3(4.0)); wn /= wn.x + wn.y + wn.z;
  float st = ll_strokes(vLLWorld.zy) * wn.x + ll_strokes(vLLWorld.xz) * wn.y + ll_strokes(vLLWorld.xy) * wn.z - 0.5;
  diffuseColor.rgb *= 1.0 + st * uStroke * uStrokeMul * vec3(1.15, 1.0, 0.85);
  roughnessFactor = clamp(roughnessFactor + n * 0.25, 0.04, 1.0);
  // edge wear: screen-space curvature, masked by noise so it is patchy
  if (uWearLocal > 0.0) {
    float curv = length(fwidth(normal)) / max(fwidth(vLLWorld.x) + fwidth(vLLWorld.y) + fwidth(vLLWorld.z), 1e-4);
    float mask = smoothstep(0.4, 0.7, ll_vnoise(vLLWorld * 6.0) * 0.7 + ll_vnoise(vLLWorld * 13.0) * 0.3);
    float wear = smoothstep(0.6, 2.2, curv) * mask * uWearLocal;
    diffuseColor.rgb = mix(diffuseColor.rgb, uWearColLocal, wear);
    roughnessFactor = mix(roughnessFactor, uWearRough, wear);
    metalnessFactor = mix(metalnessFactor, max(metalnessFactor, uMetalWear), wear);
  }
}`)
      .replace('#include <lights_fragment_end>', `#include <lights_fragment_end>
{
  // sun rim: fresnel weighted toward the surface facing the sun
  float fres = pow(1.0 - saturate(dot(normal, geometryViewDir)), uRimPower);
  float toSun = saturate(dot(normal, uRimDir) * 0.6 + 0.4);
  reflectedLight.directSpecular += fres * toSun * uRimColor * uRimStrength * uRimMul;
}`);
    if (o.sign) shader.fragmentShader = shader.fragmentShader.replace('#include <dithering_fragment>', '#include <dithering_fragment>\ngl_FragColor.a = 0.0; // sign mask: the paint pass leaves alpha 0 pixels alone');
    mat.userData.shader = shader;
  };
  mat.customProgramCacheKey = () => 'll_paint_' + JSON.stringify(o);
  return mat;
}

// Library by name prefix. Textures sets are injected by the scene (assets or procedural).
const sets = {};
export function setTextureSet(name, set) { sets[name] = set; }

function std(name, props, paintOpts) {
  const set = sets[name];
  const m = new THREE.MeshStandardMaterial(props);
  if (set) {
    if (set.map) m.map = set.map;
    if (set.normal) { m.normalMap = set.normal; m.normalScale = new THREE.Vector2(0.2, 0.2); } // painted: fewer fine details
    if (set.orm) { m.roughnessMap = set.orm; m.metalnessMap = set.orm; m.aoMap = set.orm; }
    m.color.set(props.color ?? 0xffffff);
  }
  return paint(m, paintOpts);
}

export const LIB = {};
export function buildLibrary() {
  LIB.tile = std('tile', { color: 0xffffff, roughness: 0.6, metalness: 0 }, { wear: 0, mottle: 0.16 });
  LIB.formica = std('formica', { color: 0xffffff, roughness: 0.35, metalness: 0 }, { wear: 0.45, wearColor: 0x8c8a7a, wearRough: 0.5 });
  LIB.steel = std('steel', { color: 0xffffff, roughness: 0.35, metalness: 1.0 }, { wear: 0.30, wearColor: 0xe8e8ec, wearRough: 0.2, metalWear: 1, mottle: 0.03 });
  LIB.concrete = std('concrete', { color: 0xffffff, roughness: 0.9, metalness: 0 }, { wear: 0.20, wearColor: 0xb8b2a4 });
  LIB.wood = std('wood', { color: 0xffffff, roughness: 0.55, metalness: 0 }, { wear: 0.35, wearColor: 0xd9b98a, wearRough: 0.35 });
  LIB.plastic = paint(new THREE.MeshStandardMaterial({ color: 0xc8352a, roughness: 0.45, metalness: 0 }), { wear: 0.40, wearColor: 0xe9b0a0, wearRough: 0.3, mottle: 0.05 });
  LIB.plastic_green = paint(new THREE.MeshStandardMaterial({ color: 0x2f7a4e, roughness: 0.45, metalness: 0 }), { wear: 0.40, wearColor: 0x9fd0ad, wearRough: 0.3, mottle: 0.05 });
  LIB.paint_cream = paint(new THREE.MeshStandardMaterial({ color: 0xe9dcc0, roughness: 0.8 }), { wear: 0.25, wearColor: 0xb9ad94 });
  LIB.paint_green = paint(new THREE.MeshStandardMaterial({ color: 0x3f6b4a, roughness: 0.75 }), { wear: 0.30, wearColor: 0x8fb08f });
  LIB.paint_red = paint(new THREE.MeshStandardMaterial({ color: 0xb42a1e, roughness: 0.6 }), { wear: 0.35, wearColor: 0xe5a28a });
  LIB.chrome = paint(new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.18, metalness: 1 }), { wear: 0.15, wearColor: 0xd0d0d6, wearRough: 0.4, metalWear: 1 });
  LIB.glass = new THREE.MeshPhysicalMaterial({ color: 0xdfe9e4, roughness: 0.08, metalness: 0, transmission: 0, transparent: true, opacity: 0.22, depthWrite: false, side: THREE.DoubleSide });
  LIB.paint_white = paint(new THREE.MeshStandardMaterial({ color: 0xf0ebe0, roughness: 0.7 }), { wear: 0.25, wearColor: 0xbdb5a4 });
  LIB.paint_gold = paint(new THREE.MeshStandardMaterial({ color: 0xc98a1e, roughness: 0.45, metalness: 0.15 }), { wear: 0.30, wearColor: 0xf0d28a, wearRough: 0.3 });
  LIB.paint_maroon = paint(new THREE.MeshStandardMaterial({ color: 0x5a1612, roughness: 0.6 }), { wear: 0.30, wearColor: 0xa8604f });
  LIB.iron = paint(new THREE.MeshStandardMaterial({ color: 0x1f1d1c, roughness: 0.5, metalness: 0.8 }), { wear: 0.25, wearColor: 0x8a8a90, metalWear: 1, wearRough: 0.3 });
  LIB.ceramic_rim = paint(new THREE.MeshStandardMaterial({ color: 0xb09c80, roughness: 0.3 }), { wear: 0.10 });
  LIB.ceramic_blue = paint(new THREE.MeshStandardMaterial({ color: 0x1e3f8a, roughness: 0.25 }), { wear: 0.10, wearColor: 0x8aa0d0 });
  LIB.rubber = paint(new THREE.MeshStandardMaterial({ color: 0x2a2622, roughness: 0.9 }), { wear: 0.15, wearColor: 0x6a655c });
  LIB.ceramic = paint(new THREE.MeshStandardMaterial({ color: 0xf1ece0, roughness: 0.25 }), { wear: 0.10, wearColor: 0xcfc6b2 });
  // hero skin and cloth: softer rim, no wear
  LIB.skin = paint(new THREE.MeshStandardMaterial({ color: 0xe6b48f, roughness: 0.55 }), { wear: 0, mottle: 0.03, rim: 0.8 });
  LIB.cloth = paint(new THREE.MeshStandardMaterial({ color: 0x8a3c6b, roughness: 0.85 }), { wear: 0, mottle: 0.06, rim: 0.6 });
  LIB.hair = paint(new THREE.MeshStandardMaterial({ color: 0xd9d6cf, roughness: 0.6 }), { wear: 0, mottle: 0.05, rim: 1.2 });
  return LIB;
}

// Prefix table for glb meshes: "tile_floor" -> LIB.tile and so on.
const PREFIX = [
  ['tile', 'tile'], ['formica', 'formica'], ['steel', 'steel'], ['stainless', 'steel'], ['chrome', 'chrome'],
  ['concrete', 'concrete'], ['wood', 'wood'], ['plastic_green', 'plastic_green'], ['plastic', 'plastic'],
  ['glass', 'glass'], ['rubber', 'rubber'], ['ceramic', 'ceramic'], ['skin', 'skin'], ['cloth', 'cloth'], ['hair', 'hair'],
  ['paint_cream', 'paint_cream'], ['paint_green', 'paint_green'], ['paint_red', 'paint_red'],
];

// glb material names from the prop builder: tex_slots keep their embedded
// maps and get painted, flat mats map to the library by name.
const MAT_BY_NAME = {
  steel_brushed: 'steel', stainless: 'steel', chrome: 'chrome', formica: 'formica', wall_tile: 'ceramic', floor_tile: 'tile',
  plastic_red: 'plastic', plastic_blue: 'plastic_blue', plywood: 'wood', wood: 'wood', concrete_painted: 'concrete',
  paint_cream: 'paint_cream', paint_green: 'paint_green', paint_red: 'paint_red', paint_white: 'paint_white', paint_gold: 'paint_gold', paint_maroon: 'paint_maroon',
  rubber_black: 'rubber', iron_dark: 'iron', glass: 'glass', ceramic_white: 'ceramic', ceramic_rim: 'ceramic_rim', ceramic_blue: 'ceramic_blue',
};

// root: Object3D. opts.sign(name) -> Texture|null for SIGN_* meshes.
// opts.signEmit(name) -> Texture|null, the lit-panels emissive map.
export function applyByName(root, opts = {}) {
  root.traverse((obj) => {
    if (!obj.isMesh) return;
    obj.castShadow = true;
    obj.receiveShadow = true;
    const name = (obj.name || '').toLowerCase();
    if (/^sign_/i.test(obj.name) && opts.sign) {
      const key = obj.name.replace(/\.\d+$/, '');
      const tex = opts.sign(key);
      if (tex) {
        const e = opts.signEmit && opts.signEmit(key);
        const m = new THREE.MeshStandardMaterial({ map: tex, roughness: 0.6, emissive: 0xffffff, emissiveMap: e || tex, emissiveIntensity: e ? 1.6 : 0.18 });
        obj.material = paint(m, { wear: 0.25, wearColor: 0xd8cfbd, mottle: 0.02, gradient: 0, stroke: 0, sign: true });
        obj.castShadow = false;
        return;
      }
    }
    if (/^tube_emit/i.test(obj.name)) {
      obj.material = new THREE.MeshStandardMaterial({ color: 0xfff4de, emissive: 0xfff0d2, emissiveIntensity: 5 });
      obj.castShadow = false;
      return;
    }
    const hit = PREFIX.find(([p]) => name.startsWith(p));
    const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
    const painted = mats.map((m) => {
      if (!m) return m;
      const mname = (m.name || '').toLowerCase();
      const hasMaps = !!(m.map || m.normalMap);
      if (hit && !hasMaps) return LIB[hit[1]];
      const lib = MAT_BY_NAME[mname];
      if (lib && LIB[lib] && !hasMaps) return LIB[lib];
      if (mname === 'glass') return LIB.glass;
      if (m.isMeshStandardMaterial) return paint(m, { wear: hasMaps ? 0.22 : 0.15, wearColor: 0xd8cfbd, mottle: 0.08 });
      const s = new THREE.MeshStandardMaterial({ color: m.color ?? 0xffffff, map: m.map ?? null, roughness: 0.7 });
      return paint(s, { wear: 0.3, wearColor: 0xd8cfbd });
    });
    obj.material = Array.isArray(obj.material) ? painted : painted[0];
  });
}
