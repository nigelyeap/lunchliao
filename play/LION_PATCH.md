# Lion Dancer patch for play/chope.html

Adds the new Tank hero Lion Dancer (key `lion`) with every row of play/LION_DANCER.md. Each block is an exact find/replace. Every FIND string occurs once in chope.html as of 16 Nov 2026, with or without AIM_PATCH.md and CHAR_LOOK.md applied.
Apply them in order, as plain string replacement (not regex). The working copy with all blocks applied is play/chope_lion.html.

Inside each fence the text starts on the line after the opening fence and ends right before the newline that precedes the closing fence. The same blocks sit as exact JSON in the last section, and this applies them from the repo root:

~~~~
python3 - <<'PY'
import json;p='play/chope.html';s=open(p).read()
for f,r in json.loads(open('play/LION_PATCH.md').read().split('~~~~json\n')[-1].rsplit('\n~~~~',1)[0]):
    assert s.count(f)==1,f[:80];s=s.replace(f,r)
open(p,'w').write(s)
PY
~~~~

What it does: a HEROES entry with Singlish lines and kit rows, the Belly system (fill, drain, Digest heal, size, full Belly damage and knockback cuts), Chomp on the shared melee, Feed and Spit on RMB, Swallow, Pounce, Firecracker Shake, the King of the Jungle ult, a bot brain, four comic icons, a Belly meter above the ult wheel and HUD kit text. It reuses HEROES, ABIL, splash, applyStatus, startDash and the leap mover. Projectiles and hitscan check the Feed cone and a pouncing body before they hit. Firecracker Shake wobbles the aim of anyone it hits for 1.5 seconds through aimDir.

Model: heroes/lion.glb loads as a toy hero like the others. Its feed, pounce and shake clips and the belly shape key are optional and guarded. Missing clips become empty clips. With no lion.glb the Gym Hunk body, viewmodel, quick melee and tables stand in. There is no viewmodels/lion.glb, so first person uses the Gym Hunk arms.

## Block 1: HEROES entry

FIND:

~~~~
  siao:{name:'The Siaolang'
~~~~

REPLACE:

~~~~
  lion:{name:'Lion Dancer',role:'Tank',hp:800,speed:6.4,size:1.35,ultCost:160,body:0xe8312a,botRange:2.4,
    melee:{dmg:55,range:2.6,arc:25,windup:.2,cycle:.7,kb:2},
    lines:['Ptui! Eat this lah!','Come, come, go inside first!','Wah, pounce liao!','Firecracker! Cover ears ah!','King of the jungle lah!','Huat ah! Gong xi gong xi!'],
    kit:[['LMB','Chomp','Bite everything in front of you. Each bite that lands fills your Belly a little.','2.6 m reach, 50 degree arc. 55 damage a bite, one bite every 0.7 seconds. 5 Belly per bite that lands.'],
      ['1','Swallow','Gulp a teammate next to you to carry and heal them. Press again to spit them out forward.','3 m grab range. Holds them up to 4 seconds. They heal 30 HP a second and cannot be hit. 6 Belly a second. No Chomp or Feed while full. Spits them about 6 m forward. Every 14 seconds.'],
      ['2','Pounce','Leap at where you aim. Your stretched body blocks shots on the way. The landing knocks enemies back and shields you.','Up to 14 m in about 0.6 seconds. 50 damage and knockback within 4 m. A 150 shield and 1.3x size for 3 seconds. With 50 Belly it spends it for 18 m and a 250 shield. Every 10 seconds.'],
      ['3','Firecracker Shake','Shake out a ring of firecrackers. Enemies get knocked back and their aim shakes.','5 m radius, 40 damage, big knockback. Enemy aim shakes for 1.5 seconds. With 30 Belly it spends it for a second burst 1 second later. Every 12 seconds.'],
      ['4','King of the Jungle','Grow huge and hungry. Your Belly fills, Feed has no cooldown and Spit becomes a cannonball.','8 seconds. Belly to 100, 1.6x size, a 300 shield. Feed has no cooldown and a 12 m cone. Spit deals 180 in a 6 m splash. Pounce cooldown halved.'],
      ['RMB','Feed','Hold to open wide and eat enemy shots in front of you. Let go to spit it all back.','Hold up to 3.5 seconds. An 8 m, 60 degree cone eats projectiles and hitscan and pulls in enemy gum and bells. 40% slower while held. 1 Belly per 4 damage eaten. Spit: 20 damage plus 1 per Belly in a 4 m splash, spends all Belly. Cooldown 3 seconds plus 1.5 per second held.'],
      ['P','Digest','Belly drains when you stop eating and you heal what drains. A full Belly makes you tougher.','Drains 2 a second after 4 seconds without gaining. Heals 1 HP per Belly drained. At 100 Belly: 20% less damage, 50% less knockback.']]},
  siao:{name:'The Siaolang'
~~~~

## Block 2: Mesh fallback tables (SIZE, BUDGET, HEIGHT, BUILDERS)

FIND:

~~~~
dj: buildTarik, ice: buildTarik};
~~~~

REPLACE:

~~~~
dj: buildTarik, ice: buildTarik};
for (const T of [SIZE, BUDGET, HEIGHT]) T.lion = T.gym; BUILDERS.lion = buildGym; // Lion Dancer: Gym Hunk body when lion.glb is missing
~~~~

## Block 3: Quick melee and camera tables

FIND:

~~~~
T.dj = T.rider; T.ice = T.rider; }
~~~~

REPLACE:

~~~~
T.dj = T.rider; T.ice = T.rider; }
for (const T of [QM, VMK, CAMQ, BASIC]) if (!T.lion) T.lion = T.gym; // Lion Dancer
~~~~

## Block 4: Viewmodel

FIND:

~~~~
dj: buildDj, ice: buildIce};
~~~~

REPLACE:

~~~~
dj: buildDj, ice: buildIce};
VIEWMODELS.lion = buildGym; // Lion Dancer first person arms
~~~~

## Block 5: Shield cap

FIND:

~~~~
e.shield=Math.min(150,o.v)
~~~~

REPLACE:

~~~~
e.shield=Math.min(o.cap||150,o.v)
~~~~

## Block 6: Spawn reset

FIND:

~~~~
e.leap=null;e.scoped=false;if(e.bird)e.bird.visible=false;
~~~~

REPLACE:

~~~~
e.leap=null;e.scoped=false;if(e.bird)e.bird.visible=false;e.inLion=null;if(e.hk==='lion')lionReset(e);
~~~~

## Block 7: Projectiles: Feed eats, Pounce blocks

FIND:

~~~~
const p=projs[i];p.t+=dt;let dead=p.t>p.life;
~~~~

REPLACE:

~~~~
const p=projs[i];p.t+=dt;let dead=p.t>p.life;if(!dead&&lionEat(p))dead=true; // Lion Dancer Feed and Pounce
~~~~

## Block 8: Hitscan: Feed eats, Pounce blocks

FIND:

~~~~
  if(pierce&&bestE&&!bestE.kind&&!(bestE.deflectT>0)){bestE.alive=false;
~~~~

REPLACE:

~~~~
  {const fr=feedRay(e,o,dir,best,dmg);if(fr>=0){fxe('tracer',muzzle(e,new THREE.Vector3()),o.clone().addScaledVector(dir,fr),0xfff1dc);return}} // Lion Dancer Feed and Pounce
  if(pierce&&bestE&&!bestE.kind&&!(bestE.deflectT>0)){bestE.alive=false;
~~~~

## Block 9: Aim shake

FIND:

~~~~
  if(e.isPlayer)return fwd(e.yaw,e.pitch,out);
  return out.copy(e.ai.aim);
}
~~~~

REPLACE:

~~~~
  if(e.isPlayer)fwd(e.yaw,e.pitch,out);else out.copy(e.ai.aim);
  if(e.shakeT>0){const k=clock;out.x+=.08*Math.sin(k*29);out.y+=.06*Math.sin(k*37);out.z+=.08*Math.cos(k*31);out.normalize()} // Firecracker Shake
  return out;
}
~~~~

## Block 10: No Chomp while feeding, full or pouncing

FIND:

~~~~
  if(e.hk==='tarik')return; // Tarik Pour runs in pourInput and pourTick
~~~~

REPLACE:

~~~~
  if(e.hk==='tarik')return; // Tarik Pour runs in pourInput and pourTick
  if(e.hk==='lion'&&(e.gulp||e.feedT>0||e.leap))return; // Lion Dancer
~~~~

## Block 11: Chomp fills Belly

FIND:

~~~~
  if(e.hk==='gym'&&landed){const W=e.wpn,r0=W.reps||0;
~~~~

REPLACE:

~~~~
  if(e.hk==='lion'&&landed)bellyAdd(e,LN.gChomp);
  if(e.hk==='gym'&&landed){const W=e.wpn,r0=W.reps||0;
~~~~

## Block 12: Lion functions and ABIL.lion

FIND:

~~~~
const stOff=(l,src)=>{
~~~~

REPLACE:

~~~~
// Lion Dancer (lion), numbers from LION_DANCER.md. Belly 0 to 100 fills from Feed, Swallow and Chomp, drains 2/s after 4 s with no gain, and Digest heals what drains
const LN={b0:1.35,b1:1.5,sp0:6.4,sp1:5.6,dr:.2,kr:.5,drainW:4,drain:2,gFeed:.25,gGulp:6,gChomp:5,gDep:10,fR:8,fA:30,fT:3.5,fSlow:.4,fCd0:3,fCd1:1.5,spD:20,spR:4,spK:6,uSpD:180,uSpR:6,uFR:12,
  gR:3,gT:4,gH:30,gCd:14,gOut:20,pR:14,pR2:18,pT:.6,pD:50,pRad:4,pK:8,pSh:150,pSh2:250,pCost:50,pCd:10,pBig:1.3,pBigT:3,pBlock:1.4,sR:5,sD:40,sK:9,sT:1.5,sCost:30,sCd:12,uT:8,uSh:300,uBig:1.6};
PROJ.spit=[new THREE.SphereGeometry(.22,8,6),0xffb547];PROJ.cannon=[new THREE.SphereGeometry(.5,10,8),0x8a2a1a];
const _ln=new THREE.Vector3(),_ln2=new THREE.Vector3(),_ln3=new THREE.Vector3();
function bellyAdd(e,v){if(!(v>0)||e.hk!=='lion'||!e.alive)return;e.belly=Math.min(100,(e.belly||0)+v);e.bellyG=clock}
function lionReset(e){if(e.gulp)lionEject(e,true);e.belly=0;e.bellyG=clock;e.feedT=0;e.feedH=false;e.feedLock=false;e.cdF=0;e.gulp=null;e.gulpT=0;e.bigT=0;e.shk2=0;e.shkFx=0;e.lnTo=null}
function lionSpd(e){return (LN.sp0+(LN.sp1-LN.sp0)*(e.belly||0)/100)/e.H.speed*(e.feedT>0?1-LN.fSlow:1)}
const feedR=L=>L.ultT>0?LN.uFR:LN.fR,lnPounce=L=>L.leap&&L.leap.lion;
function feedIn(L,q,R){const dx=q.x-L.pos.x,dz=q.z-L.pos.z,dy=q.y-L.pos.y,d=Math.hypot(dx,dz);if(d>R||dy<-.6||dy>2.2*L.size)return false;if(d<.3)return true;
  const f=fwd(L.yaw,0,_ln2);return (dx*f.x+dz*f.z)/d>=Math.cos(LN.fA*Math.PI/180)} // 8 m, 60 degree cone (30 each side), about body height
function lionEat(p){if(!p.owner||!p.owner.team)return false; // a projectile in a feeding enemy lion's cone is eaten. A pouncing lion's stretched body blocks shots near its chest
  for(const L of ents){if(L.hk!=='lion'||!L.alive||L.team===p.owner.team)continue;
    if(L.feedT>0&&feedIn(L,p.pos,feedR(L))){bellyAdd(L,(p.dmg||25)*LN.gFeed);L.lnAte=(L.lnAte||0)+1;fxe('burst',p.pos,0xffd23f,5,3,.3);return true}
    if(lnPounce(L)&&chestOf(L,_ln3).distanceTo(p.pos)<LN.pBlock*L.size){fxe('burst',p.pos,0xffffff,4,3,.3);return true}}
  return false}
function feedRay(e,o,dir,best,dmg){let r=-1,W=null; // hitscan: the first point along the shot inside a feeding cone, or the closest pass by a pouncing lion. -1 when no lion takes it
  for(const L of ents){if(L.hk!=='lion'||!L.alive||L.team===e.team)continue;let s0=-1;
    if(L.feedT>0){const R=feedR(L);for(let s=0;s<best+.4;s+=.4){const q=Math.min(s,best);if(feedIn(L,_ln3.copy(o).addScaledVector(dir,q),R)){s0=q;break}}}
    else if(lnPounce(L)){const c=chestOf(L,_ln3).sub(o),s=clamp(c.dot(dir),0,best);if(c.addScaledVector(dir,-s).length()<LN.pBlock*L.size)s0=s}
    if(s0>=0&&(r<0||s0<r)){r=s0;W=L}}
  if(W&&W.feedT>0){bellyAdd(W,(dmg||10)*LN.gFeed);W.lnAte=(W.lnAte||0)+1;fxe('burst',_ln3.copy(o).addScaledVector(dir,r),0xffd23f,5,3,.3)}
  return r}
function lionSpit(e){const u=e.ultT>0,dm=u?LN.uSpD:LN.spD+Math.round(e.belly||0),R=u?LN.uSpR:LN.spR,o=eyeOf(e,new THREE.Vector3()),d=aimDir(e,new THREE.Vector3());
  o.addScaledVector(d,.7*e.size);if(!u){e.belly=0} // Spit spends all Belly. The ult cannonball spends none
  spawnProj({type:u?'cannon':'spit',owner:e,pos:o,vel:d.multiplyScalar(u?26:32),dmg:dm,life:2,r:u?.6:.35,g:6,weapon:u?'lion cannonball':'lion spit',
    boom:p=>{const c=splash(p,R,R,dm,dm,u?LN.spK*1.5:LN.spK,3,p.weapon);fxe('burst',c,u?0xff5a1f:0xffb547,u?22:12,u?8:5,.5);ringFx(c,u?0xff5a1f:0xffb547,R,.4);if(u&&e.isPlayer)shake(.3)}});
  fxe('sfxAt','pop',e.pos);say(e,0)}
function lionEject(e,quiet){const A=e.gulp;e.gulp=null;e.gulpT=0;e.cd1=Math.max(e.cd1,LN.gCd);if(!A)return;A.inLion=null;A.steamT=0;A.rootT=0;A.castT=0;if(A.mesh&&A.mesh.g)A.mesh.g.visible=A.lnVis!==false;
  if(quiet||!A.alive)return;const f=fwd(e.yaw,0,new THREE.Vector3()),dd=Math.min(1.2*e.size+.4,Math.max(0,wallDist(_ln3.set(e.pos.x,e.pos.y+.8,e.pos.z),f,3)-.5));
  A.pos.set(e.pos.x+f.x*dd,e.pos.y+.1,e.pos.z+f.z*dd);A.mesh.g.position.copy(A.pos);startDash(A,f,LN.gOut,.3,0,0,'');A.dashHit=null;A.vel.y=4;A.onGround=false; // about 6 m forward
  fxe('burst',chestOf(A,_ln3),0xffd23f,10,5,.4);fxe('sfxAt','pop',A.pos)}
function lionShake(e){const c=splash({pos:chestOf(e,new THREE.Vector3()),owner:e},LN.sR,LN.sR,LN.sD,LN.sD,LN.sK,3,'firecracker shake',t=>{t.shakeT=LN.sT;if(t.isPlayer)shake(.3)});
  e.shkFx=.6;ringFx(e.pos,0xff3b1f,LN.sR,.45);fxe('burst',c,0xffd23f,18,7,.5);fxe('burst',c,0xff3b1f,12,6,.4);fxe('sfxAt','pop',e.pos);if(e.isPlayer)shake(.2)}
function lionLand(e,big){const c=e.pos.clone();splash({pos:c,owner:e},LN.pRad,LN.pRad,LN.pD,LN.pD,LN.pK,4,'lion pounce');
  applyStatus(e,'shield',{v:big?LN.pSh2:LN.pSh,t:3,cap:LN.uSh});e.bigT=LN.pBigT;ringFx(c,0xe8312a,LN.pRad,.45);fxe('burst',c,0xffd23f,16,6,.5);fxe('sfxAt','pop',c);if(e.isPlayer)shake(.3)}
function lionUlt(e){e.ultT=LN.uT;e.belly=100;e.bellyG=clock;e.cdF=0;e.cd2*=.5;applyStatus(e,'shield',{v:LN.uSh,t:LN.uT,cap:LN.uSh});say(e,4);ringFx(e.pos,0xffd23f,3,.5);fxe('burst',chestOf(e,_ln3),0xe8312a,24,8,.6)}
function lionTick(e,dt){
  if(e.belly==null)lionReset(e);
  // Feed: hold RMB (bots set feedH). Release, or 3.5 s, spits. Cooldown 3 s + 1.5 s per second held, none in the ult
  const want=e.feedH&&e.alive&&!e.gulp&&!lnPounce(e)&&!(e.stunT>0)&&!(e.castT>0);
  if(!e.feedH)e.feedLock=false;if(e.cdF>0)e.cdF=Math.max(0,e.cdF-dt);
  if(e.feedT>0){e.feedT+=dt;
    if(!want||e.feedT>=LN.fT){const held=Math.min(LN.fT,e.feedT);e.feedT=0;e.cdF=e.ultT>0?0:LN.fCd0+LN.fCd1*held;if(e.feedH)e.feedLock=true;if(e.alive&&!(e.stunT>0))lionSpit(e)}
    else for(const d of [...deployables]){if(d.team===e.team||!(d.hp>0)||d.kind!=='gum'&&d.kind!=='bell')continue;if(!feedIn(e,_ln.set(d.pos.x,d.y??e.pos.y,d.pos.z),feedR(e)))continue; // sucks in enemy gum and bells
      const dx=e.pos.x-d.pos.x,dz=e.pos.z-d.pos.z,L=Math.hypot(dx,dz);if(L<1.2+e.radius){freeDep(d);bellyAdd(e,LN.gDep);fxe('burst',_ln,0xffd23f,8,4,.4);continue}
      const k=Math.min(L,6*dt)/L;d.pos.x+=dx*k;d.pos.z+=dz*k;if(d.g){d.g.position.x+=dx*k;d.g.position.z+=dz*k}}}
  else if(want&&!e.feedLock&&e.cdF<=0&&!(e.mw>0)){e.feedT=1e-3;fxe('sfxAt','pop',e.pos)}
  // Belly drain and Digest
  if(e.alive&&e.belly>0&&clock-e.bellyG>LN.drainW){const l=Math.min(e.belly,LN.drain*dt);e.belly-=l;heal(e,l,e)}
  // size: hitbox follows Belly. Pounce and the ult grow the model only
  const k=clamp((e.belly||0)/100,0,1);e.size=LN.b0+(LN.b1-LN.b0)*k;e.radius=.45*e.size;if(e.bigT>0)e.bigT-=dt;
  if(e.alive&&e.mesh&&e.mesh.g){const g=e.size*(e.ultT>0?LN.uBig:e.bigT>0?LN.pBig:1),w=e.mesh.h&&e.mesh.h.bellyMorph?1:1+.15*k;e.mesh.g.scale.set(g*w,g,g*w)}
  if(e.shkFx>0)e.shkFx-=dt;if(e.shk2>0&&(e.shk2-=dt)<=0){e.shk2=0;if(e.alive)lionShake(e)}
  if(lnPounce(e)){e.leap.t+=dt;if(!e.alive)e.leap=null;else if(e.onGround&&e.leap.t>.15||e.leap.t>2.5){const big=e.leap.big;e.leap=null;e.vel.x=e.vel.z=0;lionLand(e,big)}}
  // Swallow: the ally rides inside, untargetable, heals 30/s. Out at 4 s, on recast or when either dies
  const A=e.gulp;if(A){e.gulpT+=dt;
    if(!e.alive||!A.alive||e.gulpT>=LN.gT)lionEject(e,!e.alive);
    else{A.steamT=Math.max(A.steamT||0,.2);A.rootT=Math.max(A.rootT||0,.1);A.castT=Math.max(A.castT||0,.1);A.pos.set(e.pos.x,e.pos.y+.3,e.pos.z);A.vel.set(0,0,0);A.kb.set(0,0,0);A.dashT=0;A.leap=null;
      if(A.mesh&&A.mesh.g){A.mesh.g.visible=false;A.mesh.g.position.copy(A.pos)}heal(A,LN.gH*dt,e);bellyAdd(e,LN.gGulp*dt)}}
}
function lionBot(e,dt,a,t,dist,hp,K,r,near){
  const hot=e.calm<1||e.hurtT>0;
  if(e.feedT>0){if(t&&dist<14&&(e.belly>=60||e.feedT>2.6)&&los(e,t)||!hot&&e.feedT>1.5)e.feedH=false} // Spit once full enough and something is in reach
  else{e.feedH=false;if(hot&&e.cdF<=0&&!e.gulp&&!lnPounce(e)&&r(3))e.feedH=true} // Feed under fire
  if(e.gulp){const A=e.gulp;if(e.gulpT>3||A.hp>=.9*A.maxHp)tryAbility(e,1)}
  else if(e.cd1<=0&&r(2)){for(const o of ents)if(o!==e&&o.alive&&o.team===e.team&&!o.inLion&&o.hp<.4*o.maxHp&&o.pos.distanceTo(e.pos)<LN.gR+e.radius){tryAbility(e,1);break}} // Swallow a low teammate
  if(e.cd2<=0&&!lnPounce(e)&&r(1)){let to=null;const R=(e.belly||0)>=LN.pCost?LN.pR2:LN.pR;
    for(const z of zones){const d=Math.hypot(z.p.x-e.pos.x,z.p.z-e.pos.z);if(d>Math.max(6,z.r)&&d<R+z.r*.5&&(z.pres===3||z.owner!==e.team)){to=z.p;break}} // Pounce onto the objective
    if(!to&&t&&dist>6&&dist<R&&los(e,t))to=t.pos;if(to){e.lnTo=_ln.copy(to);tryAbility(e,2)}}
  if(e.cd3<=0&&near(LN.sR)>=1&&r(3))tryAbility(e,3);
  if(K&&(near(8)>=2||hp<.35&&t&&dist<6)&&r(1.5))tryUlt(e);
}
ABIL.lion={
  1(e){if(e.gulp){lionEject(e);say(e,1);return} // Swallow, recast spits the ally out
    let b=null,bd=LN.gR+e.radius;for(const o of ents){if(o===e||!o.alive||o.team!==e.team||o.inLion||o.gulp)continue;const d=o.pos.distanceTo(e.pos);if(d<bd){bd=d;b=o}}
    if(!b)return false;if(e.feedT>0)e.feedH=false;e.gulp=b;e.gulpT=0;b.inLion=e;b.lnVis=b.mesh&&b.mesh.g?b.mesh.g.visible:true;b.dashT=0;b.leap=null;e.cd1=.4;say(e,1);fxe('burst',chestOf(e,_ln3),0xe8312a,12,5,.4)},
  2(e){const big=(e.belly||0)>=LN.pCost;if(big)e.belly-=LN.pCost;const R=big?LN.pR2:LN.pR; // Pounce, spends 50 Belly when it has it
    const to=(!e.isPlayer||autoPilot)&&e.lnTo?e.lnTo:aimPt(e,R),f=_ln2.copy(to).sub(e.pos).setY(0);e.lnTo=null;let d=f.length();if(d<.1){fwd(e.yaw,0,f);d=R}else f.divideScalar(d);d=clamp(d,4,R);
    if(e.feedT>0)e.feedH=false;e.leap={d:f.clone(),t:0,k:1,v:d/LN.pT,lion:1,big};if(e.sl)endSlide(e,'jump');e.onGround=false;e.vel.y=GRAV*LN.pT/2;e.cd2=e.ultT>0?LN.pCd/2:LN.pCd;say(e,2);fxe('burst',e.pos,0xe8312a,10,4,.4)},
  3(e){e.cd3=LN.sCd;lionShake(e);if((e.belly||0)>=LN.sCost){e.belly-=LN.sCost;e.shk2=1}say(e,3)}, // Firecracker Shake, 30 Belly buys a second burst 1 s later
};
const stOff=(l,src)=>{
~~~~

## Block 13: Ult

FIND:

~~~~
  else if(e.hk==='gym'){e.ultT=8;e.snareT=0;
~~~~

REPLACE:

~~~~
  else if(e.hk==='lion')lionUlt(e); // King of the Jungle
  else if(e.hk==='gym'){e.ultT=8;e.snareT=0;
~~~~

## Block 14: Full Belly damage reduction

FIND:

~~~~
for(const o of t.st.dr)k*=1-o.m;amt*=Math.max(.5,k)}
~~~~

REPLACE:

~~~~
for(const o of t.st.dr)k*=1-o.m;if(t.hk==='lion'&&t.belly>=100)k*=1-LN.dr;amt*=Math.max(.5,k)}
~~~~

## Block 15: Full Belly knockback reduction

FIND:

~~~~
if(opt.knock&&!(t.chT>0)){t.kb.add(opt.knock);
~~~~

REPLACE:

~~~~
if(opt.knock&&!(t.chT>0)){if(t.hk==='lion'&&t.belly>=100)opt.knock.multiplyScalar(1-LN.kr);t.kb.add(opt.knock);
~~~~

## Block 16: Move speed from Belly and Feed

FIND:

~~~~
*(e.scoped?(e.hk==='lens'?.6:.75):1);
~~~~

REPLACE:

~~~~
*(e.scoped?(e.hk==='lens'?.6:.75):1)*(e.hk==='lion'?lionSpd(e):1);
~~~~

## Block 17: Bots do not steer a Pounce

FIND:

~~~~
if(e.leap&&!(e.stunT>0))leapSteer(e,dt);
~~~~

REPLACE:

~~~~
if(e.leap&&!(e.stunT>0)&&!(e.leap.lion&&(!e.isPlayer||autoPilot)))leapSteer(e,dt);
~~~~

## Block 18: Pounce speed

FIND:

~~~~
v=e.leap?12*e.leap.k:12
~~~~

REPLACE:

~~~~
v=e.leap?(e.leap.v||12)*e.leap.k:12
~~~~

## Block 19: Swallowed ally skips body push

FIND:

~~~~
if(psleThru(a,c)||psleThru(c,a))continue;
~~~~

REPLACE:

~~~~
if(psleThru(a,c)||psleThru(c,a)||a.inLion||c.inLion)continue;
~~~~

## Block 20: Player Feed input

FIND:

~~~~
  p.scoped=rmb&&!!BND[p.hk]
~~~~

REPLACE:

~~~~
  if(p.hk==='lion'&&!autoPilot)p.feedH=!!rmb||!!p.feedTest; // Lion Dancer Feed (feedTest: test hook)
  p.scoped=rmb&&!!BND[p.hk]
~~~~

## Block 21: Bot kit

FIND:

~~~~
  }else if(e.hk==='siao'){
~~~~

REPLACE:

~~~~
  }else if(e.hk==='lion'){lionBot(e,dt,a,t,dist,hp,K,r,near);
  }else if(e.hk==='siao'){
~~~~

## Block 22: Per frame tick

FIND:

~~~~
  if(e.hk==='rascal')bookTick(e);
~~~~

REPLACE:

~~~~
  if(e.hk==='rascal')bookTick(e);
  if(e.hk==='lion')lionTick(e,dt);if(e.shakeT>0)e.shakeT-=dt; // Lion Dancer, Firecracker Shake aim
~~~~

## Block 23: HUD kit

FIND:

~~~~
  ice: {name: 'Ice Cream Uncle', field: '--hdb-ice'
~~~~

REPLACE:

~~~~
  lion: {name: 'Lion Dancer', field: '--hdb-peach', hp: 800, basic: 'walker', ab: [['Swallow', 'pb'], ['Pounce', 'scoot'], ['Firecracker Shake', 'megaphone'], ['King of the Jungle', 'star']]},
  ice: {name: 'Ice Cream Uncle', field: '--hdb-ice'
~~~~

## Block 24: Comic icons

FIND:

~~~~
const AB2={
~~~~

REPLACE:

~~~~
Object.assign(ICE.I,{swallow:[[0,'e8312a','M6 22a18 15 0 1 0 36 0a18 15 0 1 0 -36 0z'],[0,'ffd23f','M7 16Q10 4 24 5Q38 4 41 16Q33 10 24 11Q15 10 7 16Z'],[0,'3a2417','M10 25Q24 46 38 25Q24 31 10 25Z'],[4,'fff','M12 27L14.5 31L17 28L19.5 32L22 28.5L24.5 32.5L27 28.5L29.5 32L32 28L34.5 31L36 27Z'],[0,'fff','M13.4 17a3.6 3.6 0 1 0 7.2 0a3.6 3.6 0 1 0 -7.2 0z'],[0,'fff','M27.4 17a3.6 3.6 0 1 0 7.2 0a3.6 3.6 0 1 0 -7.2 0z'],[0,'3a2417','M16.2 17.6a1.6 1.6 0 1 0 3.2 0a1.6 1.6 0 1 0 -3.2 0zM30.2 17.6a1.6 1.6 0 1 0 3.2 0a1.6 1.6 0 1 0 -3.2 0z'],[0,'5b7','M38.6 2h4.8v3.6h3.6v4.8h-3.6v3.6h-4.8v-3.6h-3.6v-4.8h3.6z']],pounce:[[2,'f52',2.6,'M3 33h7M2 40h8M5 26h6'],[2,'ffd23f',3,'M9 41Q20 6 37 24'],[0,'e8312a','M26 28a9 9 0 1 0 18 0a9 9 0 1 0 -18 0z'],[0,'ffd23f','M27 22Q30 15 37 17Q44 18 44 26Q40 21 35 21Q30 21 27 22Z'],[0,'fff','M29.6 27a2.4 2.4 0 1 0 4.8 0a2.4 2.4 0 1 0 -4.8 0z'],[0,'fff','M36.6 27a2.4 2.4 0 1 0 4.8 0a2.4 2.4 0 1 0 -4.8 0z'],[0,'3a2417','M31.5 27.4a1 1 0 1 0 2 0a1 1 0 1 0 -2 0zM38.5 27.4a1 1 0 1 0 2 0a1 1 0 1 0 -2 0z'],[2,'3a2417',2,'M31 33Q35 36 40 33']],firecracker:[[2,'3a2417',1.8,'M18 15Q18 8 24 6Q30 8 30 15'],[0,'e8312a','M15 15h5a2 2 0 0 1 2 2v21a2 2 0 0 1 -2 2h-5a2 2 0 0 1 -2 -2v-21a2 2 0 0 1 2 -2z'],[0,'e8312a','M28 15h5a2 2 0 0 1 2 2v21a2 2 0 0 1 -2 2h-5a2 2 0 0 1 -2 -2v-21a2 2 0 0 1 2 -2z'],[1,'ffd23f','M13 20H22V22.5H13ZM26 20H35V22.5H26ZM13 33H22V35.5H13ZM26 33H35V35.5H26Z'],[0,'ffd23f','M24.0 0.0L25.6 3.8L29.7 4.1L26.6 6.8L27.5 10.9L24.0 8.7L20.5 10.9L21.4 6.8L18.3 4.1L22.4 3.8Z'],[2,'f52',2.4,'M9 9l-4-3M39 9l4-3M7 18H2M41 18h5']],kingjungle:[[0,'e8312a','M8 29a16 13 0 1 0 32 0a16 13 0 1 0 -32 0z'],[0,'ffd23f','M11 16L15 4L20.5 11L24 2L27.5 11L33 4L37 16Z'],[4,'fff','M22.4 10.5a1.6 1.6 0 1 0 3.2 0a1.6 1.6 0 1 0 -3.2 0z'],[0,'fff','M14.6 27a3.4 3.4 0 1 0 6.8 0a3.4 3.4 0 1 0 -6.8 0z'],[0,'fff','M26.6 27a3.4 3.4 0 1 0 6.8 0a3.4 3.4 0 1 0 -6.8 0z'],[0,'3a2417','M17.200000000000003 27.5a1.4 1.4 0 1 0 2.8 0a1.4 1.4 0 1 0 -2.8 0zM29.200000000000003 27.5a1.4 1.4 0 1 0 2.8 0a1.4 1.4 0 1 0 -2.8 0z'],[2,'3a2417',2.2,'M17 35Q24 40 31 35'],[0,'ffd23f','M6 30Q4 22 9 18Q8 25 11 29ZM42 30Q44 22 39 18Q40 25 37 29Z']]}); // Lion Dancer comic icons, literal paths
const AB2={
~~~~

## Block 25: Icon keys

FIND:

~~~~
ice:['coldsnap','freescoops','cartcharge','triplespin']};
~~~~

REPLACE:

~~~~
ice:['coldsnap','freescoops','cartcharge','triplespin']};AB2.lion=['swallow','pounce','firecracker','kingjungle'];
~~~~

## Block 26: Belly meter element

FIND:

~~~~
hud.root.appendChild(repEl); // Gym Rep counter

~~~~

REPLACE:

~~~~
hud.root.appendChild(repEl); // Gym Rep counter
const bellyEl=document.createElement('div');bellyEl.className='belly';bellyEl.hidden=true;bellyEl.style.cssText='position:absolute;left:50%;bottom:calc(100% + 12px);transform:translateX(-50%);width:120px;font:800 11px/1 var(--ui,sans-serif);letter-spacing:.04em;color:#fff1dc;text-shadow:1px 1px 0 #3a2417;text-align:center;white-space:nowrap;pointer-events:none;z-index:4';bellyEl.innerHTML='<div style="height:11px;border:2px solid #3a2417;border-radius:6px;background:#5a3a2a;overflow:hidden;box-shadow:2px 2px 0 #3a2417"><i style="display:block;height:100%;width:0;background:#ffb547"></i></div><b style="display:block;margin-top:4px">BELLY 0</b>'; // Lion Dancer Belly meter, sits on the ult meter

~~~~

## Block 27: Belly meter update

FIND:

~~~~
  {const on=p.hk==='gym'&&p.alive;repEl.hidden=!on;
~~~~

REPLACE:

~~~~
  {const on=p.hk==='lion'&&p.alive;bellyEl.hidden=!on;if(on){const u=hud.root.querySelector('.ultwrap')||document.querySelector('.chud .ultwrap');if(u&&bellyEl.parentNode!==u)u.appendChild(bellyEl);else if(!u&&!bellyEl.parentNode)hud.root.appendChild(bellyEl);
    const b=Math.round(p.belly||0),f=bellyEl.firstChild.firstChild;f.style.width=b+'%';f.style.background=b>=100?'#ff3b1f':'#ffb547';bellyEl.lastChild.textContent='BELLY '+b+(p.feedT>0?' . FEED '+p.feedT.toFixed(1):p.cdF>0?' . FEED '+Math.ceil(p.cdF)+'s':'')}} // Lion Dancer Belly and Feed
  {const on=p.hk==='gym'&&p.alive;repEl.hidden=!on;
~~~~

## Block 28: Toy model: missing clips are harmless

FIND:

~~~~
const clip=n=>THREE.AnimationClip.findByName(G.animations,n),
~~~~

REPLACE:

~~~~
const clip=n=>THREE.AnimationClip.findByName(G.animations,n)||new THREE.AnimationClip(n,1,[]),
~~~~

## Block 29: Toy model: lion extras

FIND:

~~~~
I[j]=i?W[i]:bw}}};
 h.kk({alive:true,hk},0);
~~~~

REPLACE:

~~~~
I[j]=i?W[i]:bw}}};
 if(hk==='lion'){const has=n=>!!THREE.AnimationClip.findByName(G.animations,n),bm=[],X={};o.traverse(x=>{if(x.morphTargetDictionary&&x.morphTargetDictionary.belly!==undefined)bm.push(x)});h.bellyMorph=bm.length>0; // Lion Dancer: optional feed, pounce, shake clips and the belly shape key
  if(has('feed')){X.feed=mx.clipAction(upper(clip('feed')));X.feed.play().setEffectiveWeight(0)}for(const n of ['pounce','shake'])if(has(n)){X[n]=mx.clipAction(clip(n));X[n].play().setEffectiveWeight(0)}
  const k0=h.kk;h.kk=(e,dt)=>{const w=(n,v)=>{if(X[n])X[n].setEffectiveWeight(v)};w('feed',e.feedT>0?1:0);w('pounce',e.leap?1:0);w('shake',e.shkFx>0?1:0);k0(e,dt);
   const v=clamp((e.belly||0)/100,0,1);for(const f of bm)f.morphTargetInfluences[f.morphTargetDictionary.belly]=v}}
 h.kk({alive:true,hk},0);
~~~~

## Block 30: Toy hand offsets

FIND:

~~~~
'dj','ice'],TOY_HDL={
~~~~

REPLACE:

~~~~
'dj','ice'],TOY_HDL={lion:[.526,.016],
~~~~

## Block 31: Toy list: lion.glb loads as a hero model only, no viewmodel

FIND:

~~~~
await Promise.all(TOY.map(k=>once(()=>L.loadAsync('heroes/'+k+'.glb'))
~~~~

REPLACE:

~~~~
await Promise.all([...TOY,'lion'].map(k=>once(()=>L.loadAsync('heroes/'+k+'.glb'))
~~~~

## Block 32: Aliases: voice, poses, sounds, role, skin

FIND:

~~~~
al(T,'ice','tarik')}
~~~~

REPLACE:

~~~~
al(T,'ice','tarik');al(T,'lion','gym')}if(!QM.lion)QM.lion={...QM.gym,name:'Lion Headbutt'};
~~~~

## Block 33: Aliases: sounds and tables

FIND:

~~~~
SFX.qice=SFX.qtarik;}
~~~~

REPLACE:

~~~~
SFX.qice=SFX.qtarik;SFX.qlion=SFX.qgym;if(typeof HOLD_ROLE!=='undefined')HOLD_ROLE.lion='tank';if(typeof SKIN_DEFAULT!=='undefined'&&SKIN_DEFAULT.lion===undefined)SKIN_DEFAULT.lion=1;}
~~~~

## JSON

~~~~json
[
[
"  siao:{name:'The Siaolang'",
"  lion:{name:'Lion Dancer',role:'Tank',hp:800,speed:6.4,size:1.35,ultCost:160,body:0xe8312a,botRange:2.4,\n    melee:{dmg:55,range:2.6,arc:25,windup:.2,cycle:.7,kb:2},\n    lines:['Ptui! Eat this lah!','Come, come, go inside first!','Wah, pounce liao!','Firecracker! Cover ears ah!','King of the jungle lah!','Huat ah! Gong xi gong xi!'],\n    kit:[['LMB','Chomp','Bite everything in front of you. Each bite that lands fills your Belly a little.','2.6 m reach, 50 degree arc. 55 damage a bite, one bite every 0.7 seconds. 5 Belly per bite that lands.'],\n      ['1','Swallow','Gulp a teammate next to you to carry and heal them. Press again to spit them out forward.','3 m grab range. Holds them up to 4 seconds. They heal 30 HP a second and cannot be hit. 6 Belly a second. No Chomp or Feed while full. Spits them about 6 m forward. Every 14 seconds.'],\n      ['2','Pounce','Leap at where you aim. Your stretched body blocks shots on the way. The landing knocks enemies back and shields you.','Up to 14 m in about 0.6 seconds. 50 damage and knockback within 4 m. A 150 shield and 1.3x size for 3 seconds. With 50 Belly it spends it for 18 m and a 250 shield. Every 10 seconds.'],\n      ['3','Firecracker Shake','Shake out a ring of firecrackers. Enemies get knocked back and their aim shakes.','5 m radius, 40 damage, big knockback. Enemy aim shakes for 1.5 seconds. With 30 Belly it spends it for a second burst 1 second later. Every 12 seconds.'],\n      ['4','King of the Jungle','Grow huge and hungry. Your Belly fills, Feed has no cooldown and Spit becomes a cannonball.','8 seconds. Belly to 100, 1.6x size, a 300 shield. Feed has no cooldown and a 12 m cone. Spit deals 180 in a 6 m splash. Pounce cooldown halved.'],\n      ['RMB','Feed','Hold to open wide and eat enemy shots in front of you. Let go to spit it all back.','Hold up to 3.5 seconds. An 8 m, 60 degree cone eats projectiles and hitscan and pulls in enemy gum and bells. 40% slower while held. 1 Belly per 4 damage eaten. Spit: 20 damage plus 1 per Belly in a 4 m splash, spends all Belly. Cooldown 3 seconds plus 1.5 per second held.'],\n      ['P','Digest','Belly drains when you stop eating and you heal what drains. A full Belly makes you tougher.','Drains 2 a second after 4 seconds without gaining. Heals 1 HP per Belly drained. At 100 Belly: 20% less damage, 50% less knockback.']]},\n  siao:{name:'The Siaolang'"
],
[
"dj: buildTarik, ice: buildTarik};",
"dj: buildTarik, ice: buildTarik};\nfor (const T of [SIZE, BUDGET, HEIGHT]) T.lion = T.gym; BUILDERS.lion = buildGym; // Lion Dancer: Gym Hunk body when lion.glb is missing"
],
[
"T.dj = T.rider; T.ice = T.rider; }",
"T.dj = T.rider; T.ice = T.rider; }\nfor (const T of [QM, VMK, CAMQ, BASIC]) if (!T.lion) T.lion = T.gym; // Lion Dancer"
],
[
"dj: buildDj, ice: buildIce};",
"dj: buildDj, ice: buildIce};\nVIEWMODELS.lion = buildGym; // Lion Dancer first person arms"
],
[
"e.shield=Math.min(150,o.v)",
"e.shield=Math.min(o.cap||150,o.v)"
],
[
"e.leap=null;e.scoped=false;if(e.bird)e.bird.visible=false;",
"e.leap=null;e.scoped=false;if(e.bird)e.bird.visible=false;e.inLion=null;if(e.hk==='lion')lionReset(e);"
],
[
"const p=projs[i];p.t+=dt;let dead=p.t>p.life;",
"const p=projs[i];p.t+=dt;let dead=p.t>p.life;if(!dead&&lionEat(p))dead=true; // Lion Dancer Feed and Pounce"
],
[
"  if(pierce&&bestE&&!bestE.kind&&!(bestE.deflectT>0)){bestE.alive=false;",
"  {const fr=feedRay(e,o,dir,best,dmg);if(fr>=0){fxe('tracer',muzzle(e,new THREE.Vector3()),o.clone().addScaledVector(dir,fr),0xfff1dc);return}} // Lion Dancer Feed and Pounce\n  if(pierce&&bestE&&!bestE.kind&&!(bestE.deflectT>0)){bestE.alive=false;"
],
[
"  if(e.isPlayer)return fwd(e.yaw,e.pitch,out);\n  return out.copy(e.ai.aim);\n}",
"  if(e.isPlayer)fwd(e.yaw,e.pitch,out);else out.copy(e.ai.aim);\n  if(e.shakeT>0){const k=clock;out.x+=.08*Math.sin(k*29);out.y+=.06*Math.sin(k*37);out.z+=.08*Math.cos(k*31);out.normalize()} // Firecracker Shake\n  return out;\n}"
],
[
"  if(e.hk==='tarik')return; // Tarik Pour runs in pourInput and pourTick",
"  if(e.hk==='tarik')return; // Tarik Pour runs in pourInput and pourTick\n  if(e.hk==='lion'&&(e.gulp||e.feedT>0||e.leap))return; // Lion Dancer"
],
[
"  if(e.hk==='gym'&&landed){const W=e.wpn,r0=W.reps||0;",
"  if(e.hk==='lion'&&landed)bellyAdd(e,LN.gChomp);\n  if(e.hk==='gym'&&landed){const W=e.wpn,r0=W.reps||0;"
],
[
"const stOff=(l,src)=>{",
"// Lion Dancer (lion), numbers from LION_DANCER.md. Belly 0 to 100 fills from Feed, Swallow and Chomp, drains 2/s after 4 s with no gain, and Digest heals what drains\nconst LN={b0:1.35,b1:1.5,sp0:6.4,sp1:5.6,dr:.2,kr:.5,drainW:4,drain:2,gFeed:.25,gGulp:6,gChomp:5,gDep:10,fR:8,fA:30,fT:3.5,fSlow:.4,fCd0:3,fCd1:1.5,spD:20,spR:4,spK:6,uSpD:180,uSpR:6,uFR:12,\n  gR:3,gT:4,gH:30,gCd:14,gOut:20,pR:14,pR2:18,pT:.6,pD:50,pRad:4,pK:8,pSh:150,pSh2:250,pCost:50,pCd:10,pBig:1.3,pBigT:3,pBlock:1.4,sR:5,sD:40,sK:9,sT:1.5,sCost:30,sCd:12,uT:8,uSh:300,uBig:1.6};\nPROJ.spit=[new THREE.SphereGeometry(.22,8,6),0xffb547];PROJ.cannon=[new THREE.SphereGeometry(.5,10,8),0x8a2a1a];\nconst _ln=new THREE.Vector3(),_ln2=new THREE.Vector3(),_ln3=new THREE.Vector3();\nfunction bellyAdd(e,v){if(!(v>0)||e.hk!=='lion'||!e.alive)return;e.belly=Math.min(100,(e.belly||0)+v);e.bellyG=clock}\nfunction lionReset(e){if(e.gulp)lionEject(e,true);e.belly=0;e.bellyG=clock;e.feedT=0;e.feedH=false;e.feedLock=false;e.cdF=0;e.gulp=null;e.gulpT=0;e.bigT=0;e.shk2=0;e.shkFx=0;e.lnTo=null}\nfunction lionSpd(e){return (LN.sp0+(LN.sp1-LN.sp0)*(e.belly||0)/100)/e.H.speed*(e.feedT>0?1-LN.fSlow:1)}\nconst feedR=L=>L.ultT>0?LN.uFR:LN.fR,lnPounce=L=>L.leap&&L.leap.lion;\nfunction feedIn(L,q,R){const dx=q.x-L.pos.x,dz=q.z-L.pos.z,dy=q.y-L.pos.y,d=Math.hypot(dx,dz);if(d>R||dy<-.6||dy>2.2*L.size)return false;if(d<.3)return true;\n  const f=fwd(L.yaw,0,_ln2);return (dx*f.x+dz*f.z)/d>=Math.cos(LN.fA*Math.PI/180)} // 8 m, 60 degree cone (30 each side), about body height\nfunction lionEat(p){if(!p.owner||!p.owner.team)return false; // a projectile in a feeding enemy lion's cone is eaten. A pouncing lion's stretched body blocks shots near its chest\n  for(const L of ents){if(L.hk!=='lion'||!L.alive||L.team===p.owner.team)continue;\n    if(L.feedT>0&&feedIn(L,p.pos,feedR(L))){bellyAdd(L,(p.dmg||25)*LN.gFeed);L.lnAte=(L.lnAte||0)+1;fxe('burst',p.pos,0xffd23f,5,3,.3);return true}\n    if(lnPounce(L)&&chestOf(L,_ln3).distanceTo(p.pos)<LN.pBlock*L.size){fxe('burst',p.pos,0xffffff,4,3,.3);return true}}\n  return false}\nfunction feedRay(e,o,dir,best,dmg){let r=-1,W=null; // hitscan: the first point along the shot inside a feeding cone, or the closest pass by a pouncing lion. -1 when no lion takes it\n  for(const L of ents){if(L.hk!=='lion'||!L.alive||L.team===e.team)continue;let s0=-1;\n    if(L.feedT>0){const R=feedR(L);for(let s=0;s<best+.4;s+=.4){const q=Math.min(s,best);if(feedIn(L,_ln3.copy(o).addScaledVector(dir,q),R)){s0=q;break}}}\n    else if(lnPounce(L)){const c=chestOf(L,_ln3).sub(o),s=clamp(c.dot(dir),0,best);if(c.addScaledVector(dir,-s).length()<LN.pBlock*L.size)s0=s}\n    if(s0>=0&&(r<0||s0<r)){r=s0;W=L}}\n  if(W&&W.feedT>0){bellyAdd(W,(dmg||10)*LN.gFeed);W.lnAte=(W.lnAte||0)+1;fxe('burst',_ln3.copy(o).addScaledVector(dir,r),0xffd23f,5,3,.3)}\n  return r}\nfunction lionSpit(e){const u=e.ultT>0,dm=u?LN.uSpD:LN.spD+Math.round(e.belly||0),R=u?LN.uSpR:LN.spR,o=eyeOf(e,new THREE.Vector3()),d=aimDir(e,new THREE.Vector3());\n  o.addScaledVector(d,.7*e.size);if(!u){e.belly=0} // Spit spends all Belly. The ult cannonball spends none\n  spawnProj({type:u?'cannon':'spit',owner:e,pos:o,vel:d.multiplyScalar(u?26:32),dmg:dm,life:2,r:u?.6:.35,g:6,weapon:u?'lion cannonball':'lion spit',\n    boom:p=>{const c=splash(p,R,R,dm,dm,u?LN.spK*1.5:LN.spK,3,p.weapon);fxe('burst',c,u?0xff5a1f:0xffb547,u?22:12,u?8:5,.5);ringFx(c,u?0xff5a1f:0xffb547,R,.4);if(u&&e.isPlayer)shake(.3)}});\n  fxe('sfxAt','pop',e.pos);say(e,0)}\nfunction lionEject(e,quiet){const A=e.gulp;e.gulp=null;e.gulpT=0;e.cd1=Math.max(e.cd1,LN.gCd);if(!A)return;A.inLion=null;A.steamT=0;A.rootT=0;A.castT=0;if(A.mesh&&A.mesh.g)A.mesh.g.visible=A.lnVis!==false;\n  if(quiet||!A.alive)return;const f=fwd(e.yaw,0,new THREE.Vector3()),dd=Math.min(1.2*e.size+.4,Math.max(0,wallDist(_ln3.set(e.pos.x,e.pos.y+.8,e.pos.z),f,3)-.5));\n  A.pos.set(e.pos.x+f.x*dd,e.pos.y+.1,e.pos.z+f.z*dd);A.mesh.g.position.copy(A.pos);startDash(A,f,LN.gOut,.3,0,0,'');A.dashHit=null;A.vel.y=4;A.onGround=false; // about 6 m forward\n  fxe('burst',chestOf(A,_ln3),0xffd23f,10,5,.4);fxe('sfxAt','pop',A.pos)}\nfunction lionShake(e){const c=splash({pos:chestOf(e,new THREE.Vector3()),owner:e},LN.sR,LN.sR,LN.sD,LN.sD,LN.sK,3,'firecracker shake',t=>{t.shakeT=LN.sT;if(t.isPlayer)shake(.3)});\n  e.shkFx=.6;ringFx(e.pos,0xff3b1f,LN.sR,.45);fxe('burst',c,0xffd23f,18,7,.5);fxe('burst',c,0xff3b1f,12,6,.4);fxe('sfxAt','pop',e.pos);if(e.isPlayer)shake(.2)}\nfunction lionLand(e,big){const c=e.pos.clone();splash({pos:c,owner:e},LN.pRad,LN.pRad,LN.pD,LN.pD,LN.pK,4,'lion pounce');\n  applyStatus(e,'shield',{v:big?LN.pSh2:LN.pSh,t:3,cap:LN.uSh});e.bigT=LN.pBigT;ringFx(c,0xe8312a,LN.pRad,.45);fxe('burst',c,0xffd23f,16,6,.5);fxe('sfxAt','pop',c);if(e.isPlayer)shake(.3)}\nfunction lionUlt(e){e.ultT=LN.uT;e.belly=100;e.bellyG=clock;e.cdF=0;e.cd2*=.5;applyStatus(e,'shield',{v:LN.uSh,t:LN.uT,cap:LN.uSh});say(e,4);ringFx(e.pos,0xffd23f,3,.5);fxe('burst',chestOf(e,_ln3),0xe8312a,24,8,.6)}\nfunction lionTick(e,dt){\n  if(e.belly==null)lionReset(e);\n  // Feed: hold RMB (bots set feedH). Release, or 3.5 s, spits. Cooldown 3 s + 1.5 s per second held, none in the ult\n  const want=e.feedH&&e.alive&&!e.gulp&&!lnPounce(e)&&!(e.stunT>0)&&!(e.castT>0);\n  if(!e.feedH)e.feedLock=false;if(e.cdF>0)e.cdF=Math.max(0,e.cdF-dt);\n  if(e.feedT>0){e.feedT+=dt;\n    if(!want||e.feedT>=LN.fT){const held=Math.min(LN.fT,e.feedT);e.feedT=0;e.cdF=e.ultT>0?0:LN.fCd0+LN.fCd1*held;if(e.feedH)e.feedLock=true;if(e.alive&&!(e.stunT>0))lionSpit(e)}\n    else for(const d of [...deployables]){if(d.team===e.team||!(d.hp>0)||d.kind!=='gum'&&d.kind!=='bell')continue;if(!feedIn(e,_ln.set(d.pos.x,d.y??e.pos.y,d.pos.z),feedR(e)))continue; // sucks in enemy gum and bells\n      const dx=e.pos.x-d.pos.x,dz=e.pos.z-d.pos.z,L=Math.hypot(dx,dz);if(L<1.2+e.radius){freeDep(d);bellyAdd(e,LN.gDep);fxe('burst',_ln,0xffd23f,8,4,.4);continue}\n      const k=Math.min(L,6*dt)/L;d.pos.x+=dx*k;d.pos.z+=dz*k;if(d.g){d.g.position.x+=dx*k;d.g.position.z+=dz*k}}}\n  else if(want&&!e.feedLock&&e.cdF<=0&&!(e.mw>0)){e.feedT=1e-3;fxe('sfxAt','pop',e.pos)}\n  // Belly drain and Digest\n  if(e.alive&&e.belly>0&&clock-e.bellyG>LN.drainW){const l=Math.min(e.belly,LN.drain*dt);e.belly-=l;heal(e,l,e)}\n  // size: hitbox follows Belly. Pounce and the ult grow the model only\n  const k=clamp((e.belly||0)/100,0,1);e.size=LN.b0+(LN.b1-LN.b0)*k;e.radius=.45*e.size;if(e.bigT>0)e.bigT-=dt;\n  if(e.alive&&e.mesh&&e.mesh.g){const g=e.size*(e.ultT>0?LN.uBig:e.bigT>0?LN.pBig:1),w=e.mesh.h&&e.mesh.h.bellyMorph?1:1+.15*k;e.mesh.g.scale.set(g*w,g,g*w)}\n  if(e.shkFx>0)e.shkFx-=dt;if(e.shk2>0&&(e.shk2-=dt)<=0){e.shk2=0;if(e.alive)lionShake(e)}\n  if(lnPounce(e)){e.leap.t+=dt;if(!e.alive)e.leap=null;else if(e.onGround&&e.leap.t>.15||e.leap.t>2.5){const big=e.leap.big;e.leap=null;e.vel.x=e.vel.z=0;lionLand(e,big)}}\n  // Swallow: the ally rides inside, untargetable, heals 30/s. Out at 4 s, on recast or when either dies\n  const A=e.gulp;if(A){e.gulpT+=dt;\n    if(!e.alive||!A.alive||e.gulpT>=LN.gT)lionEject(e,!e.alive);\n    else{A.steamT=Math.max(A.steamT||0,.2);A.rootT=Math.max(A.rootT||0,.1);A.castT=Math.max(A.castT||0,.1);A.pos.set(e.pos.x,e.pos.y+.3,e.pos.z);A.vel.set(0,0,0);A.kb.set(0,0,0);A.dashT=0;A.leap=null;\n      if(A.mesh&&A.mesh.g){A.mesh.g.visible=false;A.mesh.g.position.copy(A.pos)}heal(A,LN.gH*dt,e);bellyAdd(e,LN.gGulp*dt)}}\n}\nfunction lionBot(e,dt,a,t,dist,hp,K,r,near){\n  const hot=e.calm<1||e.hurtT>0;\n  if(e.feedT>0){if(t&&dist<14&&(e.belly>=60||e.feedT>2.6)&&los(e,t)||!hot&&e.feedT>1.5)e.feedH=false} // Spit once full enough and something is in reach\n  else{e.feedH=false;if(hot&&e.cdF<=0&&!e.gulp&&!lnPounce(e)&&r(3))e.feedH=true} // Feed under fire\n  if(e.gulp){const A=e.gulp;if(e.gulpT>3||A.hp>=.9*A.maxHp)tryAbility(e,1)}\n  else if(e.cd1<=0&&r(2)){for(const o of ents)if(o!==e&&o.alive&&o.team===e.team&&!o.inLion&&o.hp<.4*o.maxHp&&o.pos.distanceTo(e.pos)<LN.gR+e.radius){tryAbility(e,1);break}} // Swallow a low teammate\n  if(e.cd2<=0&&!lnPounce(e)&&r(1)){let to=null;const R=(e.belly||0)>=LN.pCost?LN.pR2:LN.pR;\n    for(const z of zones){const d=Math.hypot(z.p.x-e.pos.x,z.p.z-e.pos.z);if(d>Math.max(6,z.r)&&d<R+z.r*.5&&(z.pres===3||z.owner!==e.team)){to=z.p;break}} // Pounce onto the objective\n    if(!to&&t&&dist>6&&dist<R&&los(e,t))to=t.pos;if(to){e.lnTo=_ln.copy(to);tryAbility(e,2)}}\n  if(e.cd3<=0&&near(LN.sR)>=1&&r(3))tryAbility(e,3);\n  if(K&&(near(8)>=2||hp<.35&&t&&dist<6)&&r(1.5))tryUlt(e);\n}\nABIL.lion={\n  1(e){if(e.gulp){lionEject(e);say(e,1);return} // Swallow, recast spits the ally out\n    let b=null,bd=LN.gR+e.radius;for(const o of ents){if(o===e||!o.alive||o.team!==e.team||o.inLion||o.gulp)continue;const d=o.pos.distanceTo(e.pos);if(d<bd){bd=d;b=o}}\n    if(!b)return false;if(e.feedT>0)e.feedH=false;e.gulp=b;e.gulpT=0;b.inLion=e;b.lnVis=b.mesh&&b.mesh.g?b.mesh.g.visible:true;b.dashT=0;b.leap=null;e.cd1=.4;say(e,1);fxe('burst',chestOf(e,_ln3),0xe8312a,12,5,.4)},\n  2(e){const big=(e.belly||0)>=LN.pCost;if(big)e.belly-=LN.pCost;const R=big?LN.pR2:LN.pR; // Pounce, spends 50 Belly when it has it\n    const to=(!e.isPlayer||autoPilot)&&e.lnTo?e.lnTo:aimPt(e,R),f=_ln2.copy(to).sub(e.pos).setY(0);e.lnTo=null;let d=f.length();if(d<.1){fwd(e.yaw,0,f);d=R}else f.divideScalar(d);d=clamp(d,4,R);\n    if(e.feedT>0)e.feedH=false;e.leap={d:f.clone(),t:0,k:1,v:d/LN.pT,lion:1,big};if(e.sl)endSlide(e,'jump');e.onGround=false;e.vel.y=GRAV*LN.pT/2;e.cd2=e.ultT>0?LN.pCd/2:LN.pCd;say(e,2);fxe('burst',e.pos,0xe8312a,10,4,.4)},\n  3(e){e.cd3=LN.sCd;lionShake(e);if((e.belly||0)>=LN.sCost){e.belly-=LN.sCost;e.shk2=1}say(e,3)}, // Firecracker Shake, 30 Belly buys a second burst 1 s later\n};\nconst stOff=(l,src)=>{"
],
[
"  else if(e.hk==='gym'){e.ultT=8;e.snareT=0;",
"  else if(e.hk==='lion')lionUlt(e); // King of the Jungle\n  else if(e.hk==='gym'){e.ultT=8;e.snareT=0;"
],
[
"for(const o of t.st.dr)k*=1-o.m;amt*=Math.max(.5,k)}",
"for(const o of t.st.dr)k*=1-o.m;if(t.hk==='lion'&&t.belly>=100)k*=1-LN.dr;amt*=Math.max(.5,k)}"
],
[
"if(opt.knock&&!(t.chT>0)){t.kb.add(opt.knock);",
"if(opt.knock&&!(t.chT>0)){if(t.hk==='lion'&&t.belly>=100)opt.knock.multiplyScalar(1-LN.kr);t.kb.add(opt.knock);"
],
[
"*(e.scoped?(e.hk==='lens'?.6:.75):1);",
"*(e.scoped?(e.hk==='lens'?.6:.75):1)*(e.hk==='lion'?lionSpd(e):1);"
],
[
"if(e.leap&&!(e.stunT>0))leapSteer(e,dt);",
"if(e.leap&&!(e.stunT>0)&&!(e.leap.lion&&(!e.isPlayer||autoPilot)))leapSteer(e,dt);"
],
[
"v=e.leap?12*e.leap.k:12",
"v=e.leap?(e.leap.v||12)*e.leap.k:12"
],
[
"if(psleThru(a,c)||psleThru(c,a))continue;",
"if(psleThru(a,c)||psleThru(c,a)||a.inLion||c.inLion)continue;"
],
[
"  p.scoped=rmb&&!!BND[p.hk]",
"  if(p.hk==='lion'&&!autoPilot)p.feedH=!!rmb||!!p.feedTest; // Lion Dancer Feed (feedTest: test hook)\n  p.scoped=rmb&&!!BND[p.hk]"
],
[
"  }else if(e.hk==='siao'){",
"  }else if(e.hk==='lion'){lionBot(e,dt,a,t,dist,hp,K,r,near);\n  }else if(e.hk==='siao'){"
],
[
"  if(e.hk==='rascal')bookTick(e);",
"  if(e.hk==='rascal')bookTick(e);\n  if(e.hk==='lion')lionTick(e,dt);if(e.shakeT>0)e.shakeT-=dt; // Lion Dancer, Firecracker Shake aim"
],
[
"  ice: {name: 'Ice Cream Uncle', field: '--hdb-ice'",
"  lion: {name: 'Lion Dancer', field: '--hdb-peach', hp: 800, basic: 'walker', ab: [['Swallow', 'pb'], ['Pounce', 'scoot'], ['Firecracker Shake', 'megaphone'], ['King of the Jungle', 'star']]},\n  ice: {name: 'Ice Cream Uncle', field: '--hdb-ice'"
],
[
"const AB2={",
"Object.assign(ICE.I,{swallow:[[0,'e8312a','M6 22a18 15 0 1 0 36 0a18 15 0 1 0 -36 0z'],[0,'ffd23f','M7 16Q10 4 24 5Q38 4 41 16Q33 10 24 11Q15 10 7 16Z'],[0,'3a2417','M10 25Q24 46 38 25Q24 31 10 25Z'],[4,'fff','M12 27L14.5 31L17 28L19.5 32L22 28.5L24.5 32.5L27 28.5L29.5 32L32 28L34.5 31L36 27Z'],[0,'fff','M13.4 17a3.6 3.6 0 1 0 7.2 0a3.6 3.6 0 1 0 -7.2 0z'],[0,'fff','M27.4 17a3.6 3.6 0 1 0 7.2 0a3.6 3.6 0 1 0 -7.2 0z'],[0,'3a2417','M16.2 17.6a1.6 1.6 0 1 0 3.2 0a1.6 1.6 0 1 0 -3.2 0zM30.2 17.6a1.6 1.6 0 1 0 3.2 0a1.6 1.6 0 1 0 -3.2 0z'],[0,'5b7','M38.6 2h4.8v3.6h3.6v4.8h-3.6v3.6h-4.8v-3.6h-3.6v-4.8h3.6z']],pounce:[[2,'f52',2.6,'M3 33h7M2 40h8M5 26h6'],[2,'ffd23f',3,'M9 41Q20 6 37 24'],[0,'e8312a','M26 28a9 9 0 1 0 18 0a9 9 0 1 0 -18 0z'],[0,'ffd23f','M27 22Q30 15 37 17Q44 18 44 26Q40 21 35 21Q30 21 27 22Z'],[0,'fff','M29.6 27a2.4 2.4 0 1 0 4.8 0a2.4 2.4 0 1 0 -4.8 0z'],[0,'fff','M36.6 27a2.4 2.4 0 1 0 4.8 0a2.4 2.4 0 1 0 -4.8 0z'],[0,'3a2417','M31.5 27.4a1 1 0 1 0 2 0a1 1 0 1 0 -2 0zM38.5 27.4a1 1 0 1 0 2 0a1 1 0 1 0 -2 0z'],[2,'3a2417',2,'M31 33Q35 36 40 33']],firecracker:[[2,'3a2417',1.8,'M18 15Q18 8 24 6Q30 8 30 15'],[0,'e8312a','M15 15h5a2 2 0 0 1 2 2v21a2 2 0 0 1 -2 2h-5a2 2 0 0 1 -2 -2v-21a2 2 0 0 1 2 -2z'],[0,'e8312a','M28 15h5a2 2 0 0 1 2 2v21a2 2 0 0 1 -2 2h-5a2 2 0 0 1 -2 -2v-21a2 2 0 0 1 2 -2z'],[1,'ffd23f','M13 20H22V22.5H13ZM26 20H35V22.5H26ZM13 33H22V35.5H13ZM26 33H35V35.5H26Z'],[0,'ffd23f','M24.0 0.0L25.6 3.8L29.7 4.1L26.6 6.8L27.5 10.9L24.0 8.7L20.5 10.9L21.4 6.8L18.3 4.1L22.4 3.8Z'],[2,'f52',2.4,'M9 9l-4-3M39 9l4-3M7 18H2M41 18h5']],kingjungle:[[0,'e8312a','M8 29a16 13 0 1 0 32 0a16 13 0 1 0 -32 0z'],[0,'ffd23f','M11 16L15 4L20.5 11L24 2L27.5 11L33 4L37 16Z'],[4,'fff','M22.4 10.5a1.6 1.6 0 1 0 3.2 0a1.6 1.6 0 1 0 -3.2 0z'],[0,'fff','M14.6 27a3.4 3.4 0 1 0 6.8 0a3.4 3.4 0 1 0 -6.8 0z'],[0,'fff','M26.6 27a3.4 3.4 0 1 0 6.8 0a3.4 3.4 0 1 0 -6.8 0z'],[0,'3a2417','M17.200000000000003 27.5a1.4 1.4 0 1 0 2.8 0a1.4 1.4 0 1 0 -2.8 0zM29.200000000000003 27.5a1.4 1.4 0 1 0 2.8 0a1.4 1.4 0 1 0 -2.8 0z'],[2,'3a2417',2.2,'M17 35Q24 40 31 35'],[0,'ffd23f','M6 30Q4 22 9 18Q8 25 11 29ZM42 30Q44 22 39 18Q40 25 37 29Z']]}); // Lion Dancer comic icons, literal paths\nconst AB2={"
],
[
"ice:['coldsnap','freescoops','cartcharge','triplespin']};",
"ice:['coldsnap','freescoops','cartcharge','triplespin']};AB2.lion=['swallow','pounce','firecracker','kingjungle'];"
],
[
"hud.root.appendChild(repEl); // Gym Rep counter\n",
"hud.root.appendChild(repEl); // Gym Rep counter\nconst bellyEl=document.createElement('div');bellyEl.className='belly';bellyEl.hidden=true;bellyEl.style.cssText='position:absolute;left:50%;bottom:calc(100% + 12px);transform:translateX(-50%);width:120px;font:800 11px/1 var(--ui,sans-serif);letter-spacing:.04em;color:#fff1dc;text-shadow:1px 1px 0 #3a2417;text-align:center;white-space:nowrap;pointer-events:none;z-index:4';bellyEl.innerHTML='<div style=\"height:11px;border:2px solid #3a2417;border-radius:6px;background:#5a3a2a;overflow:hidden;box-shadow:2px 2px 0 #3a2417\"><i style=\"display:block;height:100%;width:0;background:#ffb547\"></i></div><b style=\"display:block;margin-top:4px\">BELLY 0</b>'; // Lion Dancer Belly meter, sits on the ult meter\n"
],
[
"  {const on=p.hk==='gym'&&p.alive;repEl.hidden=!on;",
"  {const on=p.hk==='lion'&&p.alive;bellyEl.hidden=!on;if(on){const u=hud.root.querySelector('.ultwrap')||document.querySelector('.chud .ultwrap');if(u&&bellyEl.parentNode!==u)u.appendChild(bellyEl);else if(!u&&!bellyEl.parentNode)hud.root.appendChild(bellyEl);\n    const b=Math.round(p.belly||0),f=bellyEl.firstChild.firstChild;f.style.width=b+'%';f.style.background=b>=100?'#ff3b1f':'#ffb547';bellyEl.lastChild.textContent='BELLY '+b+(p.feedT>0?' . FEED '+p.feedT.toFixed(1):p.cdF>0?' . FEED '+Math.ceil(p.cdF)+'s':'')}} // Lion Dancer Belly and Feed\n  {const on=p.hk==='gym'&&p.alive;repEl.hidden=!on;"
],
[
"const clip=n=>THREE.AnimationClip.findByName(G.animations,n),",
"const clip=n=>THREE.AnimationClip.findByName(G.animations,n)||new THREE.AnimationClip(n,1,[]),"
],
[
"I[j]=i?W[i]:bw}}};\n h.kk({alive:true,hk},0);",
"I[j]=i?W[i]:bw}}};\n if(hk==='lion'){const has=n=>!!THREE.AnimationClip.findByName(G.animations,n),bm=[],X={};o.traverse(x=>{if(x.morphTargetDictionary&&x.morphTargetDictionary.belly!==undefined)bm.push(x)});h.bellyMorph=bm.length>0; // Lion Dancer: optional feed, pounce, shake clips and the belly shape key\n  if(has('feed')){X.feed=mx.clipAction(upper(clip('feed')));X.feed.play().setEffectiveWeight(0)}for(const n of ['pounce','shake'])if(has(n)){X[n]=mx.clipAction(clip(n));X[n].play().setEffectiveWeight(0)}\n  const k0=h.kk;h.kk=(e,dt)=>{const w=(n,v)=>{if(X[n])X[n].setEffectiveWeight(v)};w('feed',e.feedT>0?1:0);w('pounce',e.leap?1:0);w('shake',e.shkFx>0?1:0);k0(e,dt);\n   const v=clamp((e.belly||0)/100,0,1);for(const f of bm)f.morphTargetInfluences[f.morphTargetDictionary.belly]=v}}\n h.kk({alive:true,hk},0);"
],
[
"'dj','ice'],TOY_HDL={",
"'dj','ice'],TOY_HDL={lion:[.526,.016],"
],
[
"await Promise.all(TOY.map(k=>once(()=>L.loadAsync('heroes/'+k+'.glb'))",
"await Promise.all([...TOY,'lion'].map(k=>once(()=>L.loadAsync('heroes/'+k+'.glb'))"
],
[
"al(T,'ice','tarik')}",
"al(T,'ice','tarik');al(T,'lion','gym')}if(!QM.lion)QM.lion={...QM.gym,name:'Lion Headbutt'};"
],
[
"SFX.qice=SFX.qtarik;}",
"SFX.qice=SFX.qtarik;SFX.qlion=SFX.qgym;if(typeof HOLD_ROLE!=='undefined')HOLD_ROLE.lion='tank';if(typeof SKIN_DEFAULT!=='undefined'&&SKIN_DEFAULT.lion===undefined)SKIN_DEFAULT.lion=1;}"
]
]
~~~~
