# Character look: soft vinyl toy shading (warm)

This is the warm-only patch for `play/chope.html`, the variant the user picked. It has not been applied
yet. To preview it, open `play/chope_look.html?look=warm` (add `&q` for the test API). Shots are in
`shots/char_look/`.

Line numbers are from `chope.html` as of 2026-11-16 (8783 lines). Another agent edits that file, so
find each spot by its old snippet. Every old snippet below is unique in the file.

## Root causes

1. **Cold rim on every silhouette.** `rimify()` adds `rimCol*rimAmt*smoothstep(.5,.56,fr)`, a hard
   additive band, at 1.3 in team colour (0x3aa8ff, 0xff4d6d or 0xff7a3d). It is applied in `mesh()` and
   `toyMesh()`.
2. **Pale gap and doubled ink.** The gap is the same rim band, just inside the dark silhouette ink.
   Normal ink fires on both sides of an occluding edge (glasses, singlet hem) and depth ink fires on
   the near side only, which makes two lines. `nMat` also had no morph target chunks, so face shape
   keys were drawn at rest in the prepass and the ink traced brows and eyes that are not on screen.
3. **Flat shading.** The A3 toon ramp has three hard bands, a cool shade tint `toonS`, no bounce and
   no sheen.

## What the patch does

- Soft wrap diffuse and a warm shade tint, applied only to `rimify` materials (heroes, viewmodels,
  menu hero, guns). The map keeps its A3 toon look.
- Warm floor bounce on down-facing normals and a broad low sheen from the key light.
- Hero rim becomes a soft top-lit warm edge, 0xffe2c4 at .45, the same for both teams. The team read
  comes from the bars and the red enemy outline, which are unchanged.
- The rim mask is skipped while `rimOp<1`, so the Siaolang Predator arms keep their full glow. The
  discard, `wob`, `wt` and the `rim1` program key are unchanged.
- One ink line per edge. Normal ink is dropped on the far side of a depth step.
- `nMat` gets morph target chunks, and morphed meshes get their own prepass program.

## Performance

Applied to `chope.html` on 2026-11-16. Backup: `chope.html.bak_look`.

Re-timed on High (3200x1800, pr 2, MSAA, AO) with no other headless Chrome load, two alternating rounds,
avg frame ms from `tools/perf.mjs`:

| Map | Before | After |
| --- | --- | --- |
| hawker | 47.26, 43.42 | 45.43, 42.83 |
| wetmarket | 44.92, 41.02 | 44.56, 44.92 |
| mean | 44.2 | 44.4 |

That is about +0.6%, inside the 5% budget and well under the run-to-run noise of about 8%.
No shader recompiles happen per frame: `renderer.info.programs` stays at 42.

## Patch

### 1. After line 1478 (`const A3RS=A3.toon?...`), insert

```js
// char look: soft vinyl shading for every rimify material (heroes, viewmodels, menu hero, guns). Soft top-lit rim, warm floor bounce, broad low sheen. The rim mask is off while the Predator stipple runs (rimOp<1)
const SOFTR=`vec3 up=normalize((viewMatrix*vec4(0.,1.,0.,0.)).xyz);float dn=dot(normal,up);
outgoingLight+=rimCol*rimAmt*rs*smoothstep(.45,1.,fr)*max(smoothstep(-.5,.3,dn),step(rimOp,.99));
outgoingLight+=diffuseColor.rgb*vec3(.5,.3,.18)*smoothstep(.1,-.8,dn)*.45;
#if NUM_DIR_LIGHTS>0
{vec3 H=normalize(directionalLights[0].direction+normalize(vViewPosition));outgoingLight+=directionalLights[0].color*pow(max(dot(normal,H),0.),18.)*.035;}
#endif
`;
// wrap diffuse instead of the hard cel bands
const SOFTF=`vec3 getGradientIrradiance(vec3 normal,vec3 lightDirection){float d=dot(normal,lightDirection)*.5+.5;return vec3(mix(.5,1.,smoothstep(.22,.78,d)));}`;
```

### 2. Line 1482, inside `rimify`

Old (end of the line):

```js
...rs='+A3RS+';\n#endif\noutgoingLight+=rimCol*rimAmt*rs*smoothstep(.5,.56,fr)*smoothstep(-.35,.15,normal.y);}\n#include <opaque_fragment>')};
```

New (everything before `rs='+A3RS+'` is unchanged):

```js
...rs='+A3RS+';\n#endif\n'+SOFTR+'}\n#include <opaque_fragment>');
  if(A3.toon)s.fragmentShader=s.fragmentShader.replace('#include <gradientmap_pars_fragment>',THREE.ShaderChunk.gradientmap_pars_fragment.replace(/vec3 getGradientIrradiance[\s\S]*$/,SOFTF)).replace('#include <lights_toon_pars_fragment>',THREE.ShaderChunk.lights_toon_pars_fragment.replace('toonS.rgb','vec3(1.,.93,.9)'))};
```

### 3. Comp shader, line 1534

Old:

```glsl
  float dd=max(max(lin(vUv+ox),lin(vUv-ox)),max(lin(vUv+oy),lin(vUv-oy)))-lc;
```

New:

```glsl
  vec4 l4=vec4(lin(vUv+ox),lin(vUv-ox),lin(vUv+oy),lin(vUv-oy));
  float dd=max(max(l4.x,l4.y),max(l4.z,l4.w))-lc;
```

### 4. Comp shader, after line 1539 (`inkN=smoothstep(.6,.3,nd)*geo*(1.-tm);`), insert

```glsl
  inkN*=1.-smoothstep(.015,.04,(lc-min(min(l4.x,l4.y),min(l4.z,l4.w)))/lc); // one line per edge: the far side leaves it to the depth ink
```

### 5. `mesh()`, line 8073

Old:

```js
 m.mats=[...mats];m.mats.forEach(t=>rimify(t,team===2?(A3.grade?0xff4d6d:0xff7a3d):0x3aa8ff,hk==='ice'&&t.side===THREE.DoubleSide?.2:1.3));
```

New:

```js
 m.mats=[...mats];m.mats.forEach(t=>rimify(t,0xffe2c4,hk==='ice'&&t.side===THREE.DoubleSide?.07:.45));
```

### 6. `toyMesh()`, line 8123

Old:

```js
 m.mats=[...mats];m.mats.forEach(t=>rimify(t,team===2?(A3.grade?0xff4d6d:0xff7a3d):0x3aa8ff,1.3));
```

New:

```js
 m.mats=[...mats];m.mats.forEach(t=>rimify(t,0xffe2c4,.45));
```

### 7. `nMat` morph support, line 8172

Old:

```js
 .replace('#include <project_vertex>','#include <skinning_vertex>\n#include <project_vertex>');nMat.needsUpdate=true;
```

New:

```js
 .replace('#include <project_vertex>','#include <skinning_vertex>\n#include <project_vertex>')
 .replace('#include <skinning_pars_vertex>','#include <skinning_pars_vertex>\n#include <morphtarget_pars_vertex>')
 .replace('#include <skinbase_vertex>','#include <morphinstance_vertex>\n#include <morphnormal_vertex>\n#include <skinbase_vertex>')
 .replace('#include <skinning_vertex>','#include <morphtarget_vertex>\n#include <skinning_vertex>');nMat.needsUpdate=true;
```

### 8. Prepass program per morphed mesh, line 8177

Old (start of the line):

```js
  if(m===nMat){const k=(o.isSkinnedMesh?1:o.isInstancedMesh?o.instanceColor?3:2:0)+(o.userData.tm?4:0);if(k){m=nV[k]||(nV[k]=k>3?
```

New (`+8` for morphed meshes. The toy-map test becomes a bit test so a morphed mesh is not mistaken for a toy-map one. The rest of the line is unchanged):

```js
  if(m===nMat){const k=(o.isSkinnedMesh?1:o.isInstancedMesh?o.instanceColor?3:2:0)+(o.userData.tm?4:0)+(o.morphTargetInfluences?8:0);if(k){m=nV[k]||(nV[k]=k&4?
```

## Left out on purpose

- The `look` URL switch and `window.__abSoft` timing hook from `chope_look.html`. The backup
  `chope.html.bak_look` covers before and after comparisons.
- The subtle and teamink variants: the `HRIM` table, `allyOn`, the `ALLYINK` define and the enemy
  outline threshold change. Warm needs none of them, so the enemy outline code stays exactly as it is.
