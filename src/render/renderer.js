// Lunch Liao! HD renderer: WebGL2, physical sun + sky through PMREM, tight-fit
// soft shadows, GTAO + humid height fog, bloom, AgX warm grade, SMAA.
import * as THREE from 'three';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js';
import { GTAOPass } from 'three/examples/jsm/postprocessing/GTAOPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { SMAAPass } from 'three/examples/jsm/postprocessing/SMAAPass.js';
import { FXAAPass } from 'three/examples/jsm/postprocessing/FXAAPass.js';
import { Sky } from 'three/examples/jsm/objects/Sky.js';
import { FogAOShader, GradeShader, PaintShader } from './post.js';
import { shared } from './materials.js';

export const PRESETS = {
  default: { shadow: 2048, shadowType: THREE.PCFShadowMap, ao: true, aoScale: 0.5, aoRadius: 24, aoSamples: 8, aoDenoise: 1, bloomScale: 0.25, aa: 'fxaa', scale: 0.85, shafts: 10, steam: 160, paintScale: 0.5, paintRadius: 3, paintMix: 0.5 },
  high:    { shadow: 4096, shadowType: THREE.PCFSoftShadowMap, ao: true, aoScale: 0.75, aoRadius: 36, aoSamples: 16, aoDenoise: 2, bloomScale: 0.5, aa: 'smaa', scale: 1, shafts: 18, steam: 320, paintScale: 0.75, paintRadius: 4, paintMix: 0.5 },
  // ponytail: full-res 32-sample GTAO at 1.25x cost 54 ms alone, so ultra keeps AO at high's settings and spends on VSM, 4K shadows and full-res bloom
  ultra:   { shadow: 4096, shadowType: THREE.VSMShadowMap, ao: true, aoScale: 0.75, aoRadius: 40, aoSamples: 16, aoDenoise: 2, bloomScale: 1.0, aa: 'smaa', scale: 1.0, shafts: 28, steam: 480, paintScale: 1.0, paintRadius: 5, paintMix: 0.5 },
};

export function createRenderer({ canvas, preset = 'default', width, height }) {
  const P = PRESETS[preset] || PRESETS.default;
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance', stencil: false, preserveDrawingBuffer: true });
  renderer.setPixelRatio(1);
  renderer.setSize(width, height, false);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = P.shadowType;
  renderer.toneMapping = THREE.NoToneMapping; // the grade pass tonemaps
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  const W = Math.round(width * P.scale), H = Math.round(height * P.scale);

  // ---- sky, sun, environment
  const sky = new Sky();
  sky.scale.setScalar(4000);
  const su = sky.material.uniforms;
  su.turbidity.value = 12;
  su.rayleigh.value = 2.2;
  su.mieCoefficient.value = 0.012;
  su.mieDirectionalG.value = 0.86;
  const sunDir = new THREE.Vector3(-0.86, 0.24, -0.2).normalize(); // golden hour, in over the open side, raking the stall from the left, shallow enough to spare the shutters
  su.sunPosition.value.copy(sunDir);

  const sun = new THREE.DirectionalLight(0xffc38a, 7.0);
  sun.position.copy(sunDir).multiplyScalar(40);
  sun.castShadow = true;
  sun.shadow.mapSize.set(P.shadow, P.shadow);
  sun.shadow.bias = -0.0004;
  sun.shadow.normalBias = 0.03;
  sun.shadow.radius = P.shadowType === THREE.VSMShadowMap ? 6 : 1;
  sun.shadow.blurSamples = 12;

  const pmrem = new THREE.PMREMGenerator(renderer);
  pmrem.compileEquirectangularShader();
  const skyScene = new THREE.Scene();
  skyScene.add(sky);
  const envRT = pmrem.fromScene(skyScene, 0.02);
  skyScene.remove(sky);

  function fitShadow(box) {
    // tight-fit the ortho shadow frustum to a world box
    const c = box.getCenter(new THREE.Vector3());
    const r = box.getSize(new THREE.Vector3()).length() * 0.5;
    sun.target.position.copy(c);
    sun.position.copy(c).addScaledVector(sunDir, r * 2);
    const cam = sun.shadow.camera;
    cam.left = cam.bottom = -r; cam.right = cam.top = r;
    cam.near = r * 0.5; cam.far = r * 3.5;
    cam.updateProjectionMatrix();
    sun.target.updateMatrixWorld();
  }

  function attachLighting(scene) {
    scene.add(sun, sun.target, sky);
    scene.environment = envRT.texture;
    scene.environmentIntensity = 0.15; // cool sky ambient against the warm sun
    scene.background = null; // sky mesh is the background
  }

  // ---- post stack
  const sceneRT = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, depthTexture: new THREE.DepthTexture(W, H, THREE.FloatType), samples: 0 });
  const composerRT = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, depthBuffer: false });
  const composer = new EffectComposer(renderer, composerRT);
  composer.setSize(W, H);

  let gtao = null;
  if (P.ao) {
    gtao = new GTAOPass(new THREE.Scene(), new THREE.PerspectiveCamera(), Math.round(W * P.aoScale), Math.round(H * P.aoScale));
    gtao.setGBuffer(sceneRT.depthTexture, undefined);
    gtao.output = GTAOPass.OUTPUT.Off;
    gtao.updateGtaoMaterial({ radius: P.aoRadius, distanceExponent: 1, thickness: 1, scale: 1.2, samples: P.aoSamples, distanceFallOff: 1, screenSpaceRadius: true }); // px radius: a world radius explodes in screen space near the camera
    gtao.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 4, radiusExponent: 1, rings: P.aoDenoise, samples: 12 });
    gtao.setSize(Math.round(W * P.aoScale), Math.round(H * P.aoScale));
    composer.addPass(gtao);
  }

  // painterly: Kuwahara into its own RT, composited by the fog pass
  const PW = Math.round(W * P.paintScale), PH = Math.round(H * P.paintScale);
  const paintRT = new THREE.WebGLRenderTarget(PW, PH, { type: THREE.HalfFloatType, depthBuffer: false });
  const paintPass = new ShaderPass(PaintShader, 'tScene');
  paintPass.uniforms.tDepth.value = sceneRT.depthTexture;
  paintPass.uniforms.uTexel.value.set(1 / PW, 1 / PH);
  paintPass.uniforms.uRadius.value = P.paintRadius;

  const fogPass = new ShaderPass(FogAOShader, 'tNone');
  fogPass.uniforms.tScene.value = sceneRT.texture;
  fogPass.uniforms.tDepth.value = sceneRT.depthTexture;
  fogPass.uniforms.tPaint.value = paintRT.texture;
  fogPass.uniforms.uPaintMix.value = P.paintMix;
  fogPass.uniforms.uTexelP.value.set(1 / PW, 1 / PH);
  fogPass.uniforms.uRes.value.set(W, H);
  fogPass.uniforms.uTexelS.value.set(1 / W, 1 / H);
  fogPass.uniforms.tAO.value = gtao ? gtao.pdRenderTarget.texture : null;
  fogPass.uniforms.uUseAO.value = gtao ? 1 : 0;
  fogPass.uniforms.uSunDir.value.copy(sunDir);
  composer.addPass(fogPass);

  const bloom = new UnrealBloomPass(new THREE.Vector2(Math.round(W * P.bloomScale), Math.round(H * P.bloomScale)), 0.25, 0.7, 1.0);
  composer.addPass(bloom);

  const grade = new ShaderPass(GradeShader);
  grade.uniforms.toneMappingExposure.value = 1.0;
  composer.addPass(grade);

  const aa = P.aa === 'smaa' ? new SMAAPass() : new FXAAPass();
  composer.addPass(aa);
  composer.setSize(W, H);
  if (gtao) gtao.setSize(Math.round(W * P.aoScale), Math.round(H * P.aoScale));

  // ---- frame
  const camDir = new THREE.Vector3();
  const stats = { frames: [], last: 0, post: true, scene: true };
  const _v = new THREE.Vector3();
  function render(scene, camera) {
    // sun direction in view space for the rim
    shared.uRimDir.value.copy(sunDir).transformDirection(camera.matrixWorldInverse);
    if (gtao) { gtao.camera = camera; gtao.scene = scene; }
    const fu = fogPass.uniforms;
    fu.uProjInv.value.copy(camera.projectionMatrixInverse);
    fu.uCamWorld.value.copy(camera.matrixWorld);
    fu.uCamPos.value.copy(camera.getWorldPosition(_v));
    sky.position.copy(camera.position);
    renderer.setRenderTarget(sceneRT);
    renderer.clear();
    if (stats.scene) renderer.render(scene, camera);
    stats.calls = renderer.info.render.calls; stats.triangles = renderer.info.render.triangles;
    renderer.setRenderTarget(null);
    if (stats.post) {
      paintPass.uniforms.uNF.value.set(camera.near, camera.far);
      fu.uNF.value.set(camera.near, camera.far);
      if (stats.paint !== false) paintPass.render(renderer, paintRT, sceneRT);
      composer.render();
    }
  }

  // Pipelined throughput bench: n frames queued back to back, one GPU sync at
  // the end, ms per frame. This is what a 60 fps budget is measured against.
  function bench(scene, camera, n = 60) {
    const gl = renderer.getContext();
    const px = new Uint8Array(4);
    render(scene, camera);
    gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
    // min of 3 batches: the desktop shares the GPU, so the min is the honest number
    let best = Infinity;
    for (let b = 0; b < 3; b++) {
      const t0 = performance.now();
      for (let i = 0; i < n; i++) render(scene, camera);
      gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
      best = Math.min(best, (performance.now() - t0) / n);
    }
    return best;
  }

  async function prewarm(scene, camera) {
    await renderer.compileAsync(scene, camera);
    render(scene, camera);
  }

  return { renderer, composer, sun, sunDir, sky, envRT, fitShadow, attachLighting, render, bench, prewarm, preset: P, presetName: preset, passes: { gtao, fogPass, bloom, grade, aa, paintPass }, stats, info: renderer.info };
}
