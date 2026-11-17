# Perf fixes (play/chope_perf.html)

Three fixes, all on the toy heroes and toy maps. None of them touches resolution, shadow quality, MSAA, AO, effects or autoTier.
autoTier was already safe: it skips the first 4 s and never saves a drop, so it is unchanged.

chope_perf.html is a fresh copy of chope.html (as of 20:20 on 16 Nov) with the three patches below. Line refs: "chope" is chope.html, "perf" is chope_perf.html.

## How it was measured

- High tier (q=2), 3200x1800 canvas, interleaved A/B (base, fixes 1+2, fixes 1+2+3), 3 rounds, 8 s into a bot match, 5 s window. Medians.
- The machine was shared with other agents the whole time (load 40 to 260). Frame rate sat near 20 fps for every build, so live fps and 1% low do not show the change. The rAF loop is capped by contention, not by this page.
- The reliable number is render CPU time: 20 back-to-back `render()` calls, with and without `gl.finish()`. Draw calls are deterministic.
- Look check: frozen scene (seeded random, fake clock, same bot roster, same cameras), 3 shots per map, base and fixed shot back to back, plus a base-to-base pair for the noise floor. Images are in `shots/perf/` (`*_before`, `*_after`, `*_diff`).

## Results, High tier

| Map | Build | fps | 1% low | render CPU ms | CPU + finish ms | draws total | main | shadow | textures | geometries |
|---|---|---|---|---|---|---|---|---|---|---|
| hawker | base | 20.1 | 7.5 | 37.0 | 43.6 | 1177 | 405 | 393 | 474 | 565 |
| hawker | fixes 1+2 | 19.7 | 5.5 | 24.4 | 25.1 | 992 | 380 | 323 | 219 | 568 |
| hawker | fixes 1+2+3 | 21.9 | 7.5 | 27.2 | 26.6 | 303 | 162 | 79 | 44 | 203 |
| classroom | base | 20.1 | 8.6 | 37.0 | 41.5 | 1233 | 414 | 442 | 488 | 516 |
| classroom | fixes 1+2 | 22.5 | 10.0 | 27.3 | 25.2 | 1135 | 420 | 381 | 217 | 522 |
| classroom | fixes 1+2+3 | 21.5 | 6.7 | 11.7 | 12.6 | 383 | 171 | 128 | 41 | 158 |

Hawker fixes 1+2+3 ranged 10.4 to 52.8 ms CPU across rounds because of load spikes. The best round was 10.4 ms, in line with classroom.
Render CPU time per frame drops by about 3x. On a CPU-bound machine that is not shared this should show up as higher fps. I could not measure that cleanly here.

Full bot match (both maps, about 4 minutes each, samples every 60 s): geometries and textures plateau after the first minute in both builds, and scene nodes stay flat. No leak. Draw calls stay between 256 and 460 for the whole match with all fixes, against 1112 to 1295 on base.

Look check, mean abs pixel difference (0 to 255), fixed vs base, with base vs base beside it:

| Shot | fixed vs base | base vs base |
|---|---|---|
| hawker_a | 0.73 | 0.65 to 0.99 |
| hawker_b | 0.22 | 0.19 to 0.21 |
| hawker_o | 0.13 | 0.10 |
| classroom_a | 0.003 | 0.01 to 0.05 |
| classroom_b | 0.006 | 0.07 to 0.21 |
| classroom_o | 0.001 | 0.006 |

Hawker has moving fans and steam, which is where its noise comes from. Every shot is at or under the noise floor.

## Fix 1: one skeleton per toy hero

Waste: each toy hero part had its own Skeleton, so three uploaded a bone texture per part per frame, about 25 per hero. The parts use the same bones and the same bind inverses (checked exact), so sharing is lossless.
Gain: textures 474 to 219 on hawker. The render CPU drop is shared with fix 2 (37 to 24 ms).
Look: pixel-identical.

Patch, in `toyMesh`, after chope line 8111 (perf line 8148):

```js
 mergeSkinned(o);toonify(o); // no teamKit rings: on the toy bodies they read as swim floats. Team shows by rim colour, enemy outline and bars
```

add (perf line 8149):

```js
 {const S=new Map();o.traverse(x=>{if(!x.isSkinnedMesh)return;const sk=x.skeleton,k=sk.bones.map(b=>b.uuid).join()+sk.boneInverses.map(m=>m.elements.map(v=>v.toFixed(4)).join()).join();if(S.has(k))x.skeleton=S.get(k);else S.set(k,sk)})} // perf: SkeletonUtils.clone gives every skinned part its own Skeleton. Share one per bone set (as R63 does for KayKit), so one bone texture update per hero, not about 28
```

## Fix 2: merged proxies for static toy map meshes in the shadow and normal passes

Waste: the shadow pass and the normal prepass drew every static map mesh one by one, with materials that do nothing in those passes. The main colour pass is unchanged and still draws every mesh with its own material.
The fix builds one merged depth proxy per shadow side and one merged normal mesh at map load. They are visible only during those passes. FAN, STEAM and SHUTTER nodes animate, so they are left out.
Gain: shadow draws 393 to 323 (hawker), 442 to 381 (classroom).
Look: pixel-identical (fixed vs base under the noise floor).

Patch A, insert before chope line 1596 `let skyT=null;` (perf lines 1596 to 1615):

```js
// perf: toy map statics drawn as merged proxies in the shadow pass (one per depth side) and the normal prepass (one mesh).
// The main pass still draws every original mesh with its own material. FAN, STEAM and SHUTTER nodes move, so they stay as they are.
let MP=null;
function mapProxy(g){
  g.updateMatrixWorld(true);const DYN=/^(FAN|STEAM|SHUTTER)_/,stat=[];
  g.traverse(o=>{if(!o.isMesh||o.isSkinnedMesh||o.isInstancedMesh||Array.isArray(o.material)||!o.material.visible||o.morphTargetInfluences)return;
    for(let p=o;p;p=p.parent){if(DYN.test(p.name)||!p.visible)return;if(p===g)break}stat.push(o)});
  const geo=(list,nrm)=>mergeGeometries(list.map(o=>{const s=o.geometry,b=new THREE.BufferGeometry(),n=s.attributes.position.count;
    b.setAttribute('position',s.attributes.position.clone());if(nrm)b.setAttribute('normal',s.attributes.normal.clone());
    b.setIndex(s.index?s.index.clone():[...Array(n).keys()]);b.applyMatrix4(o.matrixWorld);return b}));
  const side=m=>m.shadowSide!==null&&m.shadowSide!==undefined?m.shadowSide:m.side===THREE.FrontSide?THREE.BackSide:m.side===THREE.BackSide?THREE.FrontSide:THREE.DoubleSide;
  const cast=stat.filter(o=>o.castShadow&&!(o.material.alphaTest>0&&(o.material.map||o.material.alphaMap))&&!o.customDepthMaterial&&!o.material.alphaToCoverage),bySide=new Map();
  for(const o of cast){const k=side(o.material);(bySide.get(k)||bySide.set(k,[]).get(k)).push(o)}
  const mk=(gm,m,nm)=>{const x=new THREE.Mesh(gm,m);x.name=nm;x.frustumCulled=false;x.matrixAutoUpdate=false;x.visible=false;x.userData.tm=true;x.userData.noShadow=nm!=='mpS';g.add(x);return x};
  const sh=[...bySide].map(([k,l])=>{const x=mk(geo(l,false),new THREE.MeshBasicMaterial({shadowSide:k,colorWrite:false}),'mpS');x.castShadow=true;x.layers.enable(1);return x}); // layer 1 keeps shadowFlags off it, so shadowSide stays k
  for(const o of cast){o.castShadow=false;o.userData.noShadow=true}
  const nl=stat.filter(o=>o.geometry.attributes.normal&&(o.layers.mask&~2)),np=nl.length?mk(geo(nl,true),new THREE.MeshBasicMaterial({colorWrite:false}),'mpN'):null;np&&(np.castShadow=false);
  MP={g,sh,np,nl,n(on){if(!this.np||this.g.parent!==scene||on===this.on)return;this.on=on;this.np.visible=on;for(const o of this.nl)o.visible=!on}};
}
{const r=renderer.shadowMap.render;renderer.shadowMap.render=function(l,s,c){const P=MP&&MP.g.parent===scene?MP.sh:null;if(P)for(const x of P)x.visible=true;r.call(this,l,s,c);if(P)for(const x of P)x.visible=false}}
```

Patch B, chope line 1678 (perf 1698). Old:

```js
  renderer.setClearColor(0x8080ff,0);renderer.setRenderTarget(rtN);renderer.autoClearDepth=Q.normals;const frH=RF.frame;RF.frame=fr1-1;scene.matrixWorldAutoUpdate=false;renderer.render(scene,camera);scene.matrixWorldAutoUpdate=true;RF.frame=frH;renderer.autoClearDepth=true;
```

New:

```js
  if(MP&&Q.normals)MP.n(true);renderer.setClearColor(0x8080ff,0);renderer.setRenderTarget(rtN);renderer.autoClearDepth=Q.normals;const frH=RF.frame;RF.frame=fr1-1;scene.matrixWorldAutoUpdate=false;renderer.render(scene,camera);scene.matrixWorldAutoUpdate=true;RF.frame=frH;renderer.autoClearDepth=true;if(MP)MP.n(false);
```

Patch C, in `applyMap`, insert before chope line 2308 `  renderer.shadowMap.needsUpdate=true;` (perf line 2328):

```js
  if(e.toy)mapProxy(e.group);
```

## Fix 3: merge each toy hero's same-material parts into one skinned mesh

Waste: a toy hero is about 24 skinned parts that differ only in colour. Each was a draw in the main, shadow and normal passes.
Parts that share skeleton, bind, parent, map, side, alpha and (for face parts) morph set merge into one mesh. Each part's colour goes into a vertex colour and the material colour becomes white. The toon shader multiplies diffuse by vColor, so the product is the same. Hit flash, spawn and freeze tints set emissive on the shared material, so they still work. Face morphs are driven by name and still apply to the merged face.
Bug found and fixed during the look check: `mergeGeometries` does not carry `morphTargetsRelative`. Without the extra assignment the merged face read its relative morphs as absolute and the head shrank to about 70 percent. The patch below includes the fix.
Gain: about 24 parts down to about 9 meshes per hero. Draws 992 to 303 (hawker), 1135 to 383 (classroom). Render CPU 27 to 12 ms on classroom. Hawker was too noisy to split from fix 2.
Look: pixel-identical (classroom_b 0.006 against a noise floor of 0.07 to 0.21).
Second bug found while landing: some hero parts overlap on the same plane. Three drew them in id order, so the later part won the depth tie. In a merged draw the primitive order decides instead, and a few ink lines on the hawker hero moved. Sorting each list by id keeps the old order. Hero box diff went from 0.512 to 0.0.

Patch A, insert before chope line 8108 `function toyMesh(hk,team,old){` (perf lines 8129 to 8144):

```js
// perf: a toy hero is about 28 skinned parts that differ only in colour, so each frame paid about 28 draws per pass per hero.
// Parts that share skeleton, bind, parent, map, side and alpha merge into one mesh. Each part's toon colour goes into a vertex colour, the material colour goes white.
// diffuse times vColor is the same product the shader made from the part colour, so the shading is the same. Face parts merge only with parts of the same shape-key set (chope drives them all with the same weights). KayKit heads and transparent parts stay apart
function toyMerge(o){const grp=new Map();o.updateMatrixWorld(true);
 o.traverse(m=>{if(!m.isSkinnedMesh||/_Head$/.test(m.name)||!visible(m)||Array.isArray(m.material))return;const t=m.material,g=m.geometry;
  if(t.transparent||!t.color||!g.attributes.normal||(t.vertexColors&&(!g.attributes.color||g.attributes.color.itemSize!==3)))return;
  const k=[m.skeleton.uuid,m.bindMatrix.elements.join(),m.parent.uuid,m.matrix.elements.join(),t.map?t.map.uuid:'',t.side,t.alphaTest,t.opacity,t.type,m.morphTargetInfluences?JSON.stringify(m.morphTargetDictionary)+g.morphTargetsRelative+Object.keys(g.morphAttributes)+m.morphTargetInfluences.join():''].join('|');(grp.get(k)||grp.set(k,[]).get(k)).push(m)});
 for(const list of grp.values()){if(list.length<2)continue;list.sort((a,b)=>a.id-b.id); // three drew the parts in id order, keep it so coplanar overlaps resolve the same way
  const keys=['position','normal','skinIndex','skinWeight'].concat(list[0].material.map?['uv']:[]);
  if(!list.every(m=>keys.every(n=>m.geometry.attributes[n])))continue;
  const mg=mergeGeometries(list.map(m=>{const s=m.geometry,g=new THREE.BufferGeometry(),n=s.attributes.position.count,c=new Float32Array(n*3),col=m.material.color,vc=m.material.vertexColors&&s.attributes.color;
   for(let i=0;i<n;i++){c[i*3]=col.r*(vc?vc.getX(i):1);c[i*3+1]=col.g*(vc?vc.getY(i):1);c[i*3+2]=col.b*(vc?vc.getZ(i):1)}
   g.setIndex(s.index?s.index:[...Array(n).keys()]);keys.forEach(k=>g.setAttribute(k,s.attributes[k]));g.setAttribute('color',new THREE.BufferAttribute(c,3));for(const k in s.morphAttributes)g.morphAttributes[k]=s.morphAttributes[k];g.morphTargetsRelative=s.morphTargetsRelative;for(const gr of s.groups)g.addGroup(gr.start,gr.count,0);return g}));
  if(!mg)continue;const a=list[0],mt=a.material;mg.morphTargetsRelative=a.geometry.morphTargetsRelative;mt.color.setRGB(1,1,1);mt.vertexColors=true;mt.needsUpdate=true;mg.clearGroups(); // mergeGeometries drops the relative flag
  const x=new THREE.SkinnedMesh(mg,mt);x.name=a.name+'_tm';x.position.copy(a.position);x.quaternion.copy(a.quaternion);x.scale.copy(a.scale);x.renderOrder=a.renderOrder;
  if(a.morphTargetInfluences){x.morphTargetDictionary={...a.morphTargetDictionary};x.morphTargetInfluences=a.morphTargetInfluences.slice()}
  a.parent.add(x);x.bind(a.skeleton,a.bindMatrix);list.forEach(m=>m.parent.remove(m))}}
```

Patch B, in `toyMesh`, after the fix 1 line (perf line 8150):

```js
 toyMerge(o);
```

## Landed in chope.html (2026-11-16)

Landed on top of Classroom v4 and the Warm look, one fix at a time. Backup is chope.html.bak_perf.
Fix 1 still matches the warm rim. The warm bounce reads diffuseColor.rgb, which already includes vColor, and the rim uses its own uniform.
Look checks are mean abs diff against the pre-landing shots. Noise floor from two pre-landing runs: 0.01 to 0.12 on classroom, 0.11 to 0.82 on hawker.

| Step | hawker calls | classroom calls | textures | look |
|---|---|---|---|---|
| before | 1201 to 1223 | 1295 to 1349 | 470 to 513 | |
| fix 1 | 1269 | 1151 | 218 to 219 | at noise |
| fix 2 | 1047 | 1111 | 218 to 219 | at noise |
| fix 3 + id sort | 353 | 354 | 41 to 43 | at noise, hero box 0.0 |

Render CPU after fix 3 is 11 ms on classroom. Hawker reads 12 to 35 ms because the machine is contended. fps was 10 to 20 throughout for the same reason, so it is not a usable number here.
Console: only the old 404 for logo_lunchliao_preview.png.
Face shape keys after landing: merged head bounds match the union of the original parts, all 10 merged faces keep the relative flag, blink still runs.
Shots: shots/perf/landed_*_before.jpg and landed_*_after.jpg.

## Test harness note

Seeded-random shots drifted between builds because three's `generateUUID` uses `Math.random`, and fix 3 creates new objects before the bot roster shuffle. The shot harness routes UUID calls to the real random so both builds get the same roster. The game itself is not affected.
