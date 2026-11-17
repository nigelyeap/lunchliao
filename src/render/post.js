// Post shaders: combined AO + humid height fog, and the AgX warm grade.
import * as THREE from 'three';

// Reads the scene colour and depth, multiplies GTAO, adds exponential height
// fog whose colour warms toward the sun. Runs as the first composer pass.
export const FogAOShader = {
  name: 'FogAOShader',
  uniforms: {
    tScene: { value: null },
    tDepth: { value: null },
    tAO: { value: null },
    uUseAO: { value: 0 },
    uAOIntensity: { value: 1.0 },
    uProjInv: { value: new THREE.Matrix4() },
    uCamWorld: { value: new THREE.Matrix4() },
    uCamPos: { value: new THREE.Vector3() },
    uSunDir: { value: new THREE.Vector3(0, 1, 0) },
    uFogColor: { value: new THREE.Color(0.30, 0.40, 0.47) }, // teal haze, gold only toward the sun
    uSunColor: { value: new THREE.Color(1.0, 0.62, 0.30) },
    uFogDensity: { value: 0.004 },
    uFogFalloff: { value: 0.4 },
    uFogStart: { value: 2.0 },
    uSunPower: { value: 14.0 },
    uSunGlow: { value: 0.15 },
    tPaint: { value: null },
    uPaintMix: { value: 1.0 },
    uBleed: { value: 0.25 },
    uCanvas: { value: 0.07 },
    uBrush: { value: 0.06 },
    uTexelP: { value: new THREE.Vector2(1 / 960, 1 / 540) },
    uTexelS: { value: new THREE.Vector2(1 / 1920, 1 / 1080) },
    uInk: { value: 0.75 },
    uInkColor: { value: new THREE.Color(0.2, 0.17, 0.3) },
    uRes: { value: new THREE.Vector2(1920, 1080) },
    uNF: { value: new THREE.Vector2(0.1, 120) },
  },
  vertexShader: /* glsl */ `
    varying vec2 vUv;
    void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,
  fragmentShader: /* glsl */ `
    precision highp float;
    uniform sampler2D tScene, tDepth, tAO, tPaint;
    uniform int uUseAO;
    uniform float uAOIntensity, uFogDensity, uFogFalloff, uFogStart, uSunPower, uSunGlow, uPaintMix, uBleed, uCanvas, uBrush;
    uniform vec2 uTexelP, uTexelS, uRes, uNF;
    uniform float uInk;
    uniform vec3 uInkColor;
    uniform mat4 uProjInv, uCamWorld;
    uniform vec3 uCamPos, uSunDir, uFogColor, uSunColor;
    varying vec2 vUv;
    float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
    float vn(vec2 x) { vec2 i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f);
      return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y); }
    float lin(float d) { return uNF.x * uNF.y / (uNF.y - d * (uNF.y - uNF.x)); }
    void main() {
      vec4 sc = texture2D(tScene, vUv);
      vec3 col = sc.rgb;
      float keep = step(sc.a, 0.5); // signs write alpha 0: crisp text, no paint
      float d = texture2D(tDepth, vUv).x;
      float zc = lin(d);
      {
        // painterly composite: Kuwahara colour everywhere except across silhouettes
        float edge = smoothstep(0.015, 0.06, fwidth(zc) / zc);
        vec3 pc = texture2D(tPaint, vUv).rgb;
        // soft colour bleed: a wide 4-tap chroma, luminance kept from the paint
        vec2 o = uTexelP * 3.0;
        vec3 bl = (texture2D(tPaint, vUv + vec2(o.x, 0.0)).rgb + texture2D(tPaint, vUv - vec2(o.x, 0.0)).rgb
                 + texture2D(tPaint, vUv + vec2(0.0, o.y)).rgb + texture2D(tPaint, vUv - vec2(0.0, o.y)).rgb) * 0.25;
        float lp = dot(pc, vec3(0.2126, 0.7152, 0.0722)), lb = dot(bl, vec3(0.2126, 0.7152, 0.0722));
        pc = mix(pc, bl * (lp / max(lb, 1e-4)), uBleed);
        col = mix(col, pc, uPaintMix * (1.0 - edge) * (1.0 - keep));
      }
      {
        // ink: thin tinted lines on silhouettes (depth step) and creases (depth bend)
        float zl = lin(texture2D(tDepth, vUv - vec2(uTexelS.x, 0.0)).x), zr = lin(texture2D(tDepth, vUv + vec2(uTexelS.x, 0.0)).x);
        float zu = lin(texture2D(tDepth, vUv + vec2(0.0, uTexelS.y)).x), zd = lin(texture2D(tDepth, vUv - vec2(0.0, uTexelS.y)).x);
        float sil = max(abs(zl - zr), abs(zu - zd)) / zc;
        float crease = (abs(zl + zr - 2.0 * zc) + abs(zu + zd - 2.0 * zc)) / zc;
        float ink = clamp(smoothstep(0.02, 0.08, sil) + smoothstep(0.006, 0.02, crease) * 0.3, 0.0, 1.0) * uInk;
        col = mix(col, col * uInkColor, ink);
      }
      if (uUseAO == 1) {
        float ao = texture2D(tAO, vUv).r;
        col *= mix(1.0, ao, uAOIntensity);
      }
      vec4 clip = vec4(vUv * 2.0 - 1.0, d * 2.0 - 1.0, 1.0);
      vec4 view = uProjInv * clip; view /= view.w;
      vec3 world = (uCamWorld * view).xyz;
      vec3 ray = world - uCamPos;
      float dist = length(ray);
      if (d >= 0.99999) { dist = 80.0; ray = normalize(ray) * dist; world = uCamPos + ray; }
      vec3 dir = ray / dist;
      // exponential height fog integrated along the ray
      float f = uFogFalloff;
      float t = max(dist - uFogStart, 0.0);
      float dy = dir.y * t;
      float integral = abs(dir.y) > 1e-3
        ? (exp(-uCamPos.y * f) * (1.0 - exp(-dy * f)) / (dir.y * f))
        : exp(-uCamPos.y * f) * t;
      float fog = 1.0 - exp(-uFogDensity * max(integral, 0.0));
      fog = clamp(fog, 0.0, 0.92);
      float sunAmt = pow(max(dot(dir, uSunDir), 0.0), uSunPower);
      vec3 fogCol = uFogColor + uSunColor * sunAmt * uSunGlow;
      col = mix(col, fogCol, fog);
      // canvas weave and diagonal brush grain over everything, fog included
      vec2 px = vUv * uRes;
      float weave = vn(px * vec2(0.9, 0.22)) * 0.5 + vn(px * vec2(0.22, 0.9)) * 0.5;
      vec2 rp = mat2(0.94, 0.34, -0.34, 0.94) * px;
      float brush = vn(rp * vec2(0.05, 0.6)) * 0.6 + vn(rp * vec2(0.11, 1.3)) * 0.4;
      float lum = dot(col, vec3(0.2126, 0.7152, 0.0722));
      col *= 1.0 + (weave - 0.5) * uCanvas + (brush - 0.5) * uBrush * smoothstep(0.02, 0.4, lum);
      gl_FragColor = vec4(col, 1.0);
    }`,
};

// AgX tonemap, then a warm grade done in code: lifted umber shadows, kaya gold
// highlights, a gentle S curve, saturation, vignette. Writes sRGB.
export const GradeShader = {
  name: 'GradeShader',
  uniforms: {
    tDiffuse: { value: null },
    toneMappingExposure: { value: 1.0 },
    uShadowTint: { value: new THREE.Color(0.014, 0.024, 0.058) }, // teal violet shadows, no voids
    uHighTint: { value: new THREE.Color(1.08, 1.0, 0.86) }, // warm light
    uContrast: { value: 1.18 },
    uSaturation: { value: 1.3 },
    uVignette: { value: 0.28 },
    uToneMap: { value: 1 }, // 1 AgX, 0 ACES
  },
  vertexShader: /* glsl */ `
    varying vec2 vUv;
    void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,
  fragmentShader: /* glsl */ `
    precision highp float;
    #include <tonemapping_pars_fragment>
    uniform sampler2D tDiffuse;
    uniform vec3 uShadowTint, uHighTint;
    uniform float uContrast, uSaturation, uVignette;
    uniform int uToneMap;
    varying vec2 vUv;
    vec3 oetf(vec3 c) { return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }
    void main() {
      vec3 c = texture2D(tDiffuse, vUv).rgb;
      c = uToneMap == 1 ? AgXToneMapping(c) : ACESFilmicToneMapping(c);
      // code LUT: lift, gain, curve, saturation
      float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
      c = c + uShadowTint * (1.0 - smoothstep(0.0, 0.35, l));
      c *= mix(vec3(1.0), uHighTint, smoothstep(0.35, 1.0, l));
      c = mix(vec3(0.5), c, uContrast);
      c = clamp(c, 0.0, 1.0);
      c = pow(c, vec3(1.0)) ;
      float l2 = dot(c, vec3(0.2126, 0.7152, 0.0722));
      c = mix(vec3(l2), c, uSaturation);
      vec2 q = vUv - 0.5;
      float vig = 1.0 - uVignette * smoothstep(0.25, 0.85, dot(q, q) * 2.2);
      c *= vig;
      gl_FragColor = vec4(oetf(clamp(c, 0.0, 1.0)), 1.0);
    }`,
};

// Painterly pass: generalised Kuwahara (8 sectors, radius in paint-RT px) with
// a depth guard so strokes never cross a silhouette. Reads the scene colour
// and depth, writes the flattened "oil" colour. Runs at P.paintScale.
// ponytail: isotropic. Anisotropic (stroke follows edges) needs a structure
// tensor pass and a blur, add when the flat look is not enough.
export const PaintShader = {
  name: 'PaintShader',
  uniforms: {
    tScene: { value: null },
    tDepth: { value: null },
    uTexel: { value: new THREE.Vector2(1 / 960, 1 / 540) },
    uRadius: { value: 3.0 },
    uQ: { value: 6.0 },
    uDepthK: { value: 30.0 },
    uNF: { value: new THREE.Vector2(0.1, 120) },
  },
  vertexShader: /* glsl */ `
    varying vec2 vUv;
    void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,
  fragmentShader: /* glsl */ `
    precision highp float;
    uniform sampler2D tScene, tDepth;
    uniform vec2 uTexel, uNF;
    uniform float uRadius, uQ, uDepthK;
    varying vec2 vUv;
    float lin(float d) { return uNF.x * uNF.y / (uNF.y - d * (uNF.y - uNF.x)); }
    void main() {
      const int R = 3;
      vec3 m[8]; vec3 s[8]; float w[8];
      for (int k = 0; k < 8; k++) { m[k] = vec3(0.0); s[k] = vec3(0.0); w[k] = 0.0; }
      float zc = lin(texture2D(tDepth, vUv).x);
      float st = uRadius / float(R);
      for (int j = -R; j <= R; j++) for (int i = -R; i <= R; i++) {
        vec2 o = vec2(float(i), float(j));
        float r2 = dot(o, o) / float(R * R);
        if (r2 > 1.0001) continue;
        vec2 uv = vUv + o * st * uTexel;
        vec3 c = texture2D(tScene, uv).rgb;
        float z = lin(texture2D(tDepth, uv).x);
        float g = exp(-r2 * 2.0) * exp(-abs(z - zc) / max(zc, 0.5) * uDepthK);
        int k = int(mod(floor((atan(o.y, o.x) + 3.14159265) / 0.78539816 + 0.5), 8.0));
        m[k] += c * g; s[k] += c * c * g; w[k] += g;
      }
      vec3 outc = vec3(0.0); float tw = 0.0;
      for (int k = 0; k < 8; k++) {
        if (w[k] < 1e-4) continue;
        vec3 mean = m[k] / w[k];
        vec3 var = abs(s[k] / w[k] - mean * mean);
        float sig = sqrt(dot(var, vec3(1.0 / 3.0))) / (dot(mean, vec3(0.333)) + 0.05);
        float wk = 1.0 / (1.0 + pow(sig * 60.0, uQ)); // the flattest sector wins, that is the brush
        outc += mean * wk; tw += wk;
      }
      gl_FragColor = vec4(tw > 0.0 ? outc / tw : texture2D(tScene, vUv).rgb, 1.0);
    }`,
};
