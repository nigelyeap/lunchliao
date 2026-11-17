# Hold-to-aim patch for play/chope.html

Made against the pre-classroom chope.html. Each block is an exact find/replace. Every FIND string occurs once in that base file.
Apply them in order, as plain string replacement (not regex). If a FIND no longer matches after the classroom changes, the edit is small enough to redo by hand next to the same anchor.

Inside each fence the text starts on the line after the opening fence and ends right before the newline that precedes the closing fence. The same blocks sit as exact JSON in the last section, and this applies them from the repo root:

~~~~
python3 - <<'PY'
import json;p='play/chope.html';s=open(p).read()
for f,r in json.loads(open('play/AIM_PATCH.md').read().split('~~~~json\n')[-1].rsplit('\n~~~~',1)[0]):
    assert s.count(f)==1,f[:80];s=s.replace(f,r)
open(p,'w').write(s)
PY
~~~~

What it does: hold 1 to 4 on the converted abilities shows an aim preview (dotted arc, landing ring, ghost). Release casts. RMB or Esc cancels for free. The Folding Table ghost turns 90 degrees with R or the wheel. The table is restyled with a toon folding-table mesh and pops in with a squash. Settings gains a Quick cast toggle (profile.quick, off by default).

## Block 1

FIND:

~~~~
bel><div class="klist"></div><di
~~~~

REPLACE:

~~~~
bel><div class="srow"><span>Quick cast (abilities fire on key press, no aim preview)</span><button class="ghost qcbtn">Off</button></div><div class="klist"></div><di
~~~~

## Block 2

FIND:

~~~~
ast(e,.3,e=>{const f=fwd(e.yaw,0,tmpA).setY(0).normalize();deploy('wall',e.team,e.pos.x+f.x*3,e.pos.z+f.z*3,e);fxe('auE',e,'h_eng_wall')},'',0xffd200)},
~~~~

REPLACE:

~~~~
onst W=e.aimW;cast(e,.3,e=>{const f=fwd(e.yaw,0,tmpA).setY(0).normalize();if(W)e.wallAZ=W.az;deploy('wall',e.team,W?W.x:e.pos.x+f.x*3,W?W.z:e.pos.z+f.z*3,e);e.wallAZ=undefined;fxe('auE',e,'h_eng_wall')},'',0xffd200)}, // W: hold-to-aim spot and turn, taken at release
~~~~

## Block 3

FIND:

~~~~
3 in obstacles.
const DEP={turre
~~~~

REPLACE:

~~~~
3 in obstacles.
// Folding Table on its side: yellow top in a dark rim, hazard band on both faces, toy plastic legs and orange feet on the back. Same 4.5 x 2.2 x .4 footprint as the hitbox.
function wallGeo(){const C=new THREE.Color(),parts=[],add=(g,c)=>{C.setHex(c);const n=g.attributes.position.count,a=new Float32Array(n*3);for(let i=0;i<n;i++)C.toArray(a,i*3);g.setAttribute('color',new THREE.BufferAttribute(a,3));parts.push(g)};
  add(new THREE.BoxGeometry(4.5,2.2,.12).translate(0,0,-.1),0x2b2e35); // rim
  add(new THREE.BoxGeometry(4.24,1.94,.2).translate(0,0,-.1),0xffd200); // top
  for(const z of [-.205,.005])for(let i=0;i<8;i++){const g=new THREE.BoxGeometry(.24,.5,.02),p=g.attributes.position;for(let j=0;j<p.count;j++)p.setX(j,p.getX(j)+p.getY(j)*.6);add(g.translate(-1.75+i*.5,0,z),0x1d1f24)} // hazard stripes
  for(const x of [-1.55,1.55]){for(const y of [-.7,.7]){add(new THREE.CylinderGeometry(.075,.075,.14,10).rotateX(Math.PI/2).translate(x,y,.07),0xf4f4f0);add(new THREE.SphereGeometry(.085,10,6).translate(x,y,.13),0xff7a2e)}
    add(new THREE.CylinderGeometry(.05,.05,1.4,8).translate(x,0,.1),0xf4f4f0)}
  add(new THREE.CylinderGeometry(.04,.04,3.1,8).rotateZ(Math.PI/2).translate(0,0,.1),0xb8bcc4); // hinge brace
  return mergeGeometries(parts)}
const WALLM=toon({vertexColors:true});
const DEP={turre
~~~~

## Block 4

FIND:

~~~~
new THREE.BoxGeometry(4.5,2.2,.4
~~~~

REPLACE:

~~~~
wallGeo(
~~~~

## Block 5

FIND:

~~~~
=[],depPool={};
function deploy(
~~~~

REPLACE:

~~~~
=[],depPool={};
const depY=(kind,x,z)=>{let gy=0;if(kind!=='wall')for(const b of obstacles)if(b.max.y<1.5&&b.max.y>gy&&x>=b.min.x&&x<=b.max.x&&z>=b.min.z&&z<=b.max.z)gy=b.max.y;return gy}; // sits on a table or stool top
const wallZ=o=>!o.pos||Math.abs(Math.sin(o.yaw))>=Math.abs(Math.cos(o.yaw)); // Folding Table long side across the owner's aim
function deploy(
~~~~

## Block 6

FIND:

~~~~
let gy=y??0;if(y==null&&kind!=='wall')for(const b of obstacles)if(b.max.y<1.5&&b.max.y>gy&&x>=b.min.x&&x<=b.max.x&&z>=b.min.z&&z<=b.max.z)gy=b.max.y; // sits on a table or stool top
~~~~

REPLACE:

~~~~
const gy=y??depY(kind,x,z);
~~~~

## Block 7

FIND:

~~~~
Mesh(DEPG[kind],M(DEPC[kind])))}
~~~~

REPLACE:

~~~~
Mesh(DEPG[kind],kind==='wall'?WALLM:M(DEPC[kind])))}
~~~~

## Block 8

FIND:

~~~~
  body.material=M(DEPC[kind]);bo
~~~~

REPLACE:

~~~~
  body.material=kind==='wall'?WALLM:M(DEPC[kind]);bo
~~~~

## Block 9

FIND:

~~~~
!owner.pos||Math.abs(Math.sin(owner.yaw))>=Math.abs(Math.cos(owner.yaw)
~~~~

REPLACE:

~~~~
owner.wallAZ??wallZ(owner
~~~~

## Block 10

FIND:

~~~~
function updateDeployables(dt){if(player)tpTick(player);
~~~~

REPLACE:

~~~~
// Hold to aim (player only): hold the key to see where it lands, release to cast. RMB or Esc cancels and spends nothing. Settings > Quick cast skips it. Bots cast as before.
const _av=new THREE.Vector3(),_ao=new THREE.Vector3(),_ap=new THREE.Vector3(),_ad=new THREE.Vector3();
const AIM={uncle2:{r:1,g:'gum',pt:e=>aimPt(e,8)},uncle4:{r:5,lob:e=>aimDir(e,_av).multiplyScalar(17).add(tmpA.set(0,4.5,0))},rider3:{r:3.5,lob:e=>{aimDir(e,_av).multiplyScalar(18);_av.y+=4;return _av}},
  engineer1:{wall:1},engineer3:{r:1.2,g:'vest',fly:8,pt:e=>aimPt(e,12)},lens1:{r:1,g:'claw',pt:e=>aimPt(e,10)},debater1:{r:6,g:'bell',fly:20,pt:e=>aimPt(e,30)},debater4:{r:8.5,pt:e=>ultPt(e,40)},dj2:{r:DJ.micR,g:'mic',pt:e=>aimPt(e,12)}}; // r: the real trigger or splash radius
const aimOk=(e,s)=>e.alive&&!(e.stunT>0)&&!(e.castT>0)&&!(e.chT>0)&&!qBusy(e)&&!(e.birdT>0)&&(s<4?!(e['cd'+s]>0):e.ult>=e.H.ultCost);
function aimStart(e,s){const A=AIM[e.hk+s];if(!A||profile.quick||autoPilot||!aimOk(e,s)||s===4&&e.wpn.kick&&clock<e.wpn.kick.t)return false;e.aim={s,A,rot:0,wt:0,w:{x:0,z:0,az:false}};aimTick(e);return true} // the durian kick stays instant
let aimO=null;const _am=new THREE.Matrix4().makeScale(.07,.07,.07),_ap2=new THREE.Vector3(),aimDot=(i,x,y,z)=>{if(camera.position.distanceToSquared(_ap2.set(x,y,z))<6.25)return 0;aimO.L.setMatrixAt(i,_am.setPosition(x,y,z));return 1}; // dots inside 2.5 m of the eye would fill the screen // pooled: one dotted arc (instanced), one ring, one ghost (geometry swapped per kind)
function aimTick(e){const a=e.aim;if(!a)return;if(!e.alive||AIM[e.hk+a.s]!==a.A||autoPilot||state!=='playing'||paused){aimEnd(e);return}
  if(!aimO){const L=new THREE.InstancedMesh(sphGeo,B(0xffffff),82);L.layers.set(1);L.frustumCulled=false;
    aimO={L,R:fxM(ringGeo,B(0xffffff)),G:fxM(DEPG.wall,B(0xffffff))};aimO.R.rotation.x=-Math.PI/2;for(const o of [L,aimO.R,aimO.G])o.material.userData.keep=true}
  const {L,R,G}=aimO,A=a.A,pu=Math.sin(clock*6);if(!L.parent)scene.add(L,R,G);let n=0,x,y,z;
  if(A.wall){const f=fwd(e.yaw,0,_ap).setY(0).normalize();x=e.pos.x+f.x*3;z=e.pos.z+f.z*3;y=0;const az=wallZ(e)!==!!a.rot;a.w.x=x;a.w.z=z;a.w.az=az;
    G.geometry=DEPG.wall;G.position.set(x,1.1,z);G.rotation.y=az?Math.PI/2:0;G.scale.set(1,1,1)}
  else if(A.lob){const v=_av.copy(A.lob(e)),p=muzzle(e,_ao);n+=aimDot(n,p.x,p.y,p.z); // same march as updateProjs: gravity, then the step, stopped by a wall or the y .05 floor
    for(let i=0;i<80;i++){v.y-=GRAV*.05;_ap.copy(p).addScaledVector(v,.05);_ad.subVectors(_ap,p);const len=_ad.length();let k=Math.min(1,wallDist(p,_ad.divideScalar(len),len)/len);
      if(_ap.y<.05)k=Math.min(k,clamp((p.y-.05)/(p.y-_ap.y),0,1));p.addScaledVector(_ad,len*k);n+=aimDot(n,p.x,p.y,p.z);if(k<1)break}
    x=p.x;y=Math.max(0,p.y-.05);z=p.z}
  else{const q=A.pt(e);x=q.x;z=q.z;y=depY(A.g||'closing',x,z);
    if(A.fly){const o=muzzle(e,_ao);for(let i=0;i<=24;i++){const k=i/24;n+=aimDot(n,o.x+(x-o.x)*k,o.y*(1-k)+y*k+Math.sin(k*Math.PI)*1.2,o.z+(z-o.z)*k)}} // the deployable's own fly path
    if(A.g){G.geometry=DEPG[A.g];G.rotation.y=0;G.position.set(x,y+(A.g==='gum'?.1+y:.06),z);G.scale.set(1,A.g==='gum'?.25:1,1)}}
  const ok=aimOk(e,a.s),col=ok?TEAM_COL[e.team]:0x9a9a9a;
  L.visible=n>1;L.count=n;L.instanceMatrix.needsUpdate=true;L.material.color.setHex(col);L.material.opacity=.7+.2*pu;
  R.visible=!A.wall;R.position.set(x,y+.05,z);R.scale.setScalar(A.r||1);R.material.color.setHex(col);R.material.opacity=.45+.15*pu;
  G.visible=!!(A.wall||A.g);G.material.color.setHex(col);G.material.opacity=(A.wall?.22:.35)+.1*pu}
function aimEnd(e){if(e)e.aim=null;if(aimO)aimO.L.visible=aimO.R.visible=aimO.G.visible=false}
function aimRelease(e){const a=e.aim;if(!a)return;aimEnd(e);if(!e.alive||e.stunT>0||state!=='playing'||paused)return;e.aimW=a.A.wall?a.w:null;try{a.s<4?tryAbility(e,a.s):tryUlt(e)}finally{e.aimW=null}}
function aimRot(){const a=player&&player.aim;if(a&&a.A.wall&&clock-a.wt>.15){a.rot^=1;a.wt=clock}}
function updateDeployables(dt){if(player){tpTick(player);aimTick(player)}
~~~~

## Block 11

FIND:

~~~~
d.owner.alive);
    if(d.kind===
~~~~

REPLACE:

~~~~
d.owner.alive);
    if(d.kind==='wall'){const t=DEP.wall.life-d.life,b=d.body;if(t<.9){const sy=1-Math.exp(-7*t)*Math.cos(13*t),sx=1+(1-sy)*.25;b.scale.set(sx,Math.max(.01,sy),sx);b.position.y=1.1*sy}else if(b.scale.y!==1){b.scale.set(1,1,1);b.position.y=1.1}} // pops up from the floor, overshoots, squashes, settles
    if(d.kind===
~~~~

## Block 12

FIND:

~~~~
(player)tpEnd(player);if(id)sb
~~~~

REPLACE:

~~~~
(player){tpEnd(player);aimEnd(player)}if(id)sb
~~~~

## Block 13

FIND:

~~~~
&player)tpEnd(player);
  if(c=
~~~~

REPLACE:

~~~~
&player){tpEnd(player);aimEnd(player)}
  if(c=
~~~~

## Block 14

FIND:

~~~~
SLOTKEY[c];if(sl)sl<4?tryAbility
~~~~

REPLACE:

~~~~
SLOTKEY[c];if(sl&&!aimStart(player,sl))sl<4?tryAbility
~~~~

## Block 15

FIND:

~~~~
 if(c==='KeyR'&&BND[player.hk]&&
~~~~

REPLACE:

~~~~
 if(c==='KeyR'&&player.aim&&player.aim.A.wall)aimRot();else if(c==='KeyR'&&BND[player.hk]&&
~~~~

## Block 16

FIND:

~~~~
ease(player);if(SLOTKEY[c]===3&&
~~~~

REPLACE:

~~~~
ease(player);if(player&&player.aim&&SLOTKEY[c]===player.aim.s)aimRelease(player);if(SLOTKEY[c]===3&&
~~~~

## Block 17

FIND:

~~~~
se;tpEnd(player)}});
canvas.addEvent
~~~~

REPLACE:

~~~~
se;tpEnd(player);aimEnd(player)}});
addEventListener('wheel',()=>{if(state==='playing'&&!paused)aimRot()},{passive:true}); // wheel turns the Folding Table ghost
canvas.addEvent
~~~~

## Block 18

FIND:

~~~~
if(e.button===2)rmb=true
});
addEventLis
~~~~

REPLACE:

~~~~
if(e.button===2){if(player&&player.aim)aimEnd(player);else rmb=true} // RMB cancels a held aim
});
addEventLis
~~~~

## Block 19

FIND:

~~~~
rget.blur()}));
// WP8a: map pic
~~~~

REPLACE:

~~~~
rget.blur()}));
document.querySelectorAll('.qcbtn').forEach(b=>{b.textContent=profile.quick?'On':'Off';b.addEventListener('click',e=>{profile.quick=!profile.quick;saveProfile();e.currentTarget.textContent=profile.quick?'On':'Off';e.currentTarget.blur()})}); // Quick cast: off = hold to aim
// WP8a: map pic
~~~~

## Machine-readable blocks

~~~~json
[
[
"bel><div class=\"klist\"></div><di",
"bel><div class=\"srow\"><span>Quick cast (abilities fire on key press, no aim preview)</span><button class=\"ghost qcbtn\">Off</button></div><div class=\"klist\"></div><di"
],
[
"ast(e,.3,e=>{const f=fwd(e.yaw,0,tmpA).setY(0).normalize();deploy('wall',e.team,e.pos.x+f.x*3,e.pos.z+f.z*3,e);fxe('auE',e,'h_eng_wall')},'',0xffd200)},",
"onst W=e.aimW;cast(e,.3,e=>{const f=fwd(e.yaw,0,tmpA).setY(0).normalize();if(W)e.wallAZ=W.az;deploy('wall',e.team,W?W.x:e.pos.x+f.x*3,W?W.z:e.pos.z+f.z*3,e);e.wallAZ=undefined;fxe('auE',e,'h_eng_wall')},'',0xffd200)}, // W: hold-to-aim spot and turn, taken at release"
],
[
"3 in obstacles.\nconst DEP={turre",
"3 in obstacles.\n// Folding Table on its side: yellow top in a dark rim, hazard band on both faces, toy plastic legs and orange feet on the back. Same 4.5 x 2.2 x .4 footprint as the hitbox.\nfunction wallGeo(){const C=new THREE.Color(),parts=[],add=(g,c)=>{C.setHex(c);const n=g.attributes.position.count,a=new Float32Array(n*3);for(let i=0;i<n;i++)C.toArray(a,i*3);g.setAttribute('color',new THREE.BufferAttribute(a,3));parts.push(g)};\n  add(new THREE.BoxGeometry(4.5,2.2,.12).translate(0,0,-.1),0x2b2e35); // rim\n  add(new THREE.BoxGeometry(4.24,1.94,.2).translate(0,0,-.1),0xffd200); // top\n  for(const z of [-.205,.005])for(let i=0;i<8;i++){const g=new THREE.BoxGeometry(.24,.5,.02),p=g.attributes.position;for(let j=0;j<p.count;j++)p.setX(j,p.getX(j)+p.getY(j)*.6);add(g.translate(-1.75+i*.5,0,z),0x1d1f24)} // hazard stripes\n  for(const x of [-1.55,1.55]){for(const y of [-.7,.7]){add(new THREE.CylinderGeometry(.075,.075,.14,10).rotateX(Math.PI/2).translate(x,y,.07),0xf4f4f0);add(new THREE.SphereGeometry(.085,10,6).translate(x,y,.13),0xff7a2e)}\n    add(new THREE.CylinderGeometry(.05,.05,1.4,8).translate(x,0,.1),0xf4f4f0)}\n  add(new THREE.CylinderGeometry(.04,.04,3.1,8).rotateZ(Math.PI/2).translate(0,0,.1),0xb8bcc4); // hinge brace\n  return mergeGeometries(parts)}\nconst WALLM=toon({vertexColors:true});\nconst DEP={turre"
],
[
"new THREE.BoxGeometry(4.5,2.2,.4",
"wallGeo("
],
[
"=[],depPool={};\nfunction deploy(",
"=[],depPool={};\nconst depY=(kind,x,z)=>{let gy=0;if(kind!=='wall')for(const b of obstacles)if(b.max.y<1.5&&b.max.y>gy&&x>=b.min.x&&x<=b.max.x&&z>=b.min.z&&z<=b.max.z)gy=b.max.y;return gy}; // sits on a table or stool top\nconst wallZ=o=>!o.pos||Math.abs(Math.sin(o.yaw))>=Math.abs(Math.cos(o.yaw)); // Folding Table long side across the owner's aim\nfunction deploy("
],
[
"let gy=y??0;if(y==null&&kind!=='wall')for(const b of obstacles)if(b.max.y<1.5&&b.max.y>gy&&x>=b.min.x&&x<=b.max.x&&z>=b.min.z&&z<=b.max.z)gy=b.max.y; // sits on a table or stool top",
"const gy=y??depY(kind,x,z);"
],
[
"Mesh(DEPG[kind],M(DEPC[kind])))}",
"Mesh(DEPG[kind],kind==='wall'?WALLM:M(DEPC[kind])))}"
],
[
"  body.material=M(DEPC[kind]);bo",
"  body.material=kind==='wall'?WALLM:M(DEPC[kind]);bo"
],
[
"!owner.pos||Math.abs(Math.sin(owner.yaw))>=Math.abs(Math.cos(owner.yaw)",
"owner.wallAZ??wallZ(owner"
],
[
"function updateDeployables(dt){if(player)tpTick(player);",
"// Hold to aim (player only): hold the key to see where it lands, release to cast. RMB or Esc cancels and spends nothing. Settings > Quick cast skips it. Bots cast as before.\nconst _av=new THREE.Vector3(),_ao=new THREE.Vector3(),_ap=new THREE.Vector3(),_ad=new THREE.Vector3();\nconst AIM={uncle2:{r:1,g:'gum',pt:e=>aimPt(e,8)},uncle4:{r:5,lob:e=>aimDir(e,_av).multiplyScalar(17).add(tmpA.set(0,4.5,0))},rider3:{r:3.5,lob:e=>{aimDir(e,_av).multiplyScalar(18);_av.y+=4;return _av}},\n  engineer1:{wall:1},engineer3:{r:1.2,g:'vest',fly:8,pt:e=>aimPt(e,12)},lens1:{r:1,g:'claw',pt:e=>aimPt(e,10)},debater1:{r:6,g:'bell',fly:20,pt:e=>aimPt(e,30)},debater4:{r:8.5,pt:e=>ultPt(e,40)},dj2:{r:DJ.micR,g:'mic',pt:e=>aimPt(e,12)}}; // r: the real trigger or splash radius\nconst aimOk=(e,s)=>e.alive&&!(e.stunT>0)&&!(e.castT>0)&&!(e.chT>0)&&!qBusy(e)&&!(e.birdT>0)&&(s<4?!(e['cd'+s]>0):e.ult>=e.H.ultCost);\nfunction aimStart(e,s){const A=AIM[e.hk+s];if(!A||profile.quick||autoPilot||!aimOk(e,s)||s===4&&e.wpn.kick&&clock<e.wpn.kick.t)return false;e.aim={s,A,rot:0,wt:0,w:{x:0,z:0,az:false}};aimTick(e);return true} // the durian kick stays instant\nlet aimO=null;const _am=new THREE.Matrix4().makeScale(.07,.07,.07),_ap2=new THREE.Vector3(),aimDot=(i,x,y,z)=>{if(camera.position.distanceToSquared(_ap2.set(x,y,z))<6.25)return 0;aimO.L.setMatrixAt(i,_am.setPosition(x,y,z));return 1}; // dots inside 2.5 m of the eye would fill the screen // pooled: one dotted arc (instanced), one ring, one ghost (geometry swapped per kind)\nfunction aimTick(e){const a=e.aim;if(!a)return;if(!e.alive||AIM[e.hk+a.s]!==a.A||autoPilot||state!=='playing'||paused){aimEnd(e);return}\n  if(!aimO){const L=new THREE.InstancedMesh(sphGeo,B(0xffffff),82);L.layers.set(1);L.frustumCulled=false;\n    aimO={L,R:fxM(ringGeo,B(0xffffff)),G:fxM(DEPG.wall,B(0xffffff))};aimO.R.rotation.x=-Math.PI/2;for(const o of [L,aimO.R,aimO.G])o.material.userData.keep=true}\n  const {L,R,G}=aimO,A=a.A,pu=Math.sin(clock*6);if(!L.parent)scene.add(L,R,G);let n=0,x,y,z;\n  if(A.wall){const f=fwd(e.yaw,0,_ap).setY(0).normalize();x=e.pos.x+f.x*3;z=e.pos.z+f.z*3;y=0;const az=wallZ(e)!==!!a.rot;a.w.x=x;a.w.z=z;a.w.az=az;\n    G.geometry=DEPG.wall;G.position.set(x,1.1,z);G.rotation.y=az?Math.PI/2:0;G.scale.set(1,1,1)}\n  else if(A.lob){const v=_av.copy(A.lob(e)),p=muzzle(e,_ao);n+=aimDot(n,p.x,p.y,p.z); // same march as updateProjs: gravity, then the step, stopped by a wall or the y .05 floor\n    for(let i=0;i<80;i++){v.y-=GRAV*.05;_ap.copy(p).addScaledVector(v,.05);_ad.subVectors(_ap,p);const len=_ad.length();let k=Math.min(1,wallDist(p,_ad.divideScalar(len),len)/len);\n      if(_ap.y<.05)k=Math.min(k,clamp((p.y-.05)/(p.y-_ap.y),0,1));p.addScaledVector(_ad,len*k);n+=aimDot(n,p.x,p.y,p.z);if(k<1)break}\n    x=p.x;y=Math.max(0,p.y-.05);z=p.z}\n  else{const q=A.pt(e);x=q.x;z=q.z;y=depY(A.g||'closing',x,z);\n    if(A.fly){const o=muzzle(e,_ao);for(let i=0;i<=24;i++){const k=i/24;n+=aimDot(n,o.x+(x-o.x)*k,o.y*(1-k)+y*k+Math.sin(k*Math.PI)*1.2,o.z+(z-o.z)*k)}} // the deployable's own fly path\n    if(A.g){G.geometry=DEPG[A.g];G.rotation.y=0;G.position.set(x,y+(A.g==='gum'?.1+y:.06),z);G.scale.set(1,A.g==='gum'?.25:1,1)}}\n  const ok=aimOk(e,a.s),col=ok?TEAM_COL[e.team]:0x9a9a9a;\n  L.visible=n>1;L.count=n;L.instanceMatrix.needsUpdate=true;L.material.color.setHex(col);L.material.opacity=.7+.2*pu;\n  R.visible=!A.wall;R.position.set(x,y+.05,z);R.scale.setScalar(A.r||1);R.material.color.setHex(col);R.material.opacity=.45+.15*pu;\n  G.visible=!!(A.wall||A.g);G.material.color.setHex(col);G.material.opacity=(A.wall?.22:.35)+.1*pu}\nfunction aimEnd(e){if(e)e.aim=null;if(aimO)aimO.L.visible=aimO.R.visible=aimO.G.visible=false}\nfunction aimRelease(e){const a=e.aim;if(!a)return;aimEnd(e);if(!e.alive||e.stunT>0||state!=='playing'||paused)return;e.aimW=a.A.wall?a.w:null;try{a.s<4?tryAbility(e,a.s):tryUlt(e)}finally{e.aimW=null}}\nfunction aimRot(){const a=player&&player.aim;if(a&&a.A.wall&&clock-a.wt>.15){a.rot^=1;a.wt=clock}}\nfunction updateDeployables(dt){if(player){tpTick(player);aimTick(player)}"
],
[
"d.owner.alive);\n    if(d.kind===",
"d.owner.alive);\n    if(d.kind==='wall'){const t=DEP.wall.life-d.life,b=d.body;if(t<.9){const sy=1-Math.exp(-7*t)*Math.cos(13*t),sx=1+(1-sy)*.25;b.scale.set(sx,Math.max(.01,sy),sx);b.position.y=1.1*sy}else if(b.scale.y!==1){b.scale.set(1,1,1);b.position.y=1.1}} // pops up from the floor, overshoots, squashes, settles\n    if(d.kind==="
],
[
"(player)tpEnd(player);if(id)sb",
"(player){tpEnd(player);aimEnd(player)}if(id)sb"
],
[
"&player)tpEnd(player);\n  if(c=",
"&player){tpEnd(player);aimEnd(player)}\n  if(c="
],
[
"SLOTKEY[c];if(sl)sl<4?tryAbility",
"SLOTKEY[c];if(sl&&!aimStart(player,sl))sl<4?tryAbility"
],
[
" if(c==='KeyR'&&BND[player.hk]&&",
" if(c==='KeyR'&&player.aim&&player.aim.A.wall)aimRot();else if(c==='KeyR'&&BND[player.hk]&&"
],
[
"ease(player);if(SLOTKEY[c]===3&&",
"ease(player);if(player&&player.aim&&SLOTKEY[c]===player.aim.s)aimRelease(player);if(SLOTKEY[c]===3&&"
],
[
"se;tpEnd(player)}});\ncanvas.addEvent",
"se;tpEnd(player);aimEnd(player)}});\naddEventListener('wheel',()=>{if(state==='playing'&&!paused)aimRot()},{passive:true}); // wheel turns the Folding Table ghost\ncanvas.addEvent"
],
[
"if(e.button===2)rmb=true\n});\naddEventLis",
"if(e.button===2){if(player&&player.aim)aimEnd(player);else rmb=true} // RMB cancels a held aim\n});\naddEventLis"
],
[
"rget.blur()}));\n// WP8a: map pic",
"rget.blur()}));\ndocument.querySelectorAll('.qcbtn').forEach(b=>{b.textContent=profile.quick?'On':'Off';b.addEventListener('click',e=>{profile.quick=!profile.quick;saveProfile();e.currentTarget.textContent=profile.quick?'On':'Off';e.currentTarget.blur()})}); // Quick cast: off = hold to aim\n// WP8a: map pic"
]
]
~~~~
