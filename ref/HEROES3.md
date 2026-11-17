# Chope! Hero Spec wave 3

Status: READY for B. Owner: wave 3 hero designer. Prototype: proto-heroes3/build3.py writes proto-heroes3/chope.h3.html from the current chope.html. chope.html is untouched.

Two new Damage heroes:

- Long Lens Lim (key `lens`). A retired uncle bird photographer with a huge white telephoto lens. Sniper.
- The Siaolang (key `siao`). A kampung boy in a white singlet and red headband. Melee assassin. "Siaolang" here means a reckless daredevil. No mental illness imagery, props or lines.

New shared system: RMB scope. Lim gets 4x. NS Boy gets 1.75x with a small retune.

## 1. Kit numbers

### 1.1 Long Lens Lim

HP 150, speed 7.4, size 1, ult cost 210, bot range 45. Q is Lens Cap Bonk (NS Boy melee numbers).

| Slot | Name | Numbers |
|---|---|---|
| LMB | Telephoto Shot | Hold to charge. 1.2 s to full, .8 s when scoped. Tap 30, full 80. Full head x2.25 = 180. Part charge head x1.5. 6 shots, .5 s between shots, reload 1.8 s, active reload window .9 to 1.1 s. Weapon name "telephoto shot" |
| RMB | Scope | 4x zoom (fov 78 to 22.9). Moves 40% slower. Charge time drops to .8 s. Mouse sensitivity divides by the zoom. Off during Bird Escape |
| 1 | Claw Trap | cd 12, cast .3 s. Drops at the aim point up to 10 m away. One at a time, 40 hp, lasts 30 s, arms in .8 s. Triggers within 1 m: 15 damage and a 2 s snare (75% slow, no jump). Enemies only see it within 8 m |
| 2 | Bird Escape | cd 14, cast .15 s. Turns into a hornbill for 2.5 s. See 1.3 |
| 3 | Burst Mode | cd 8. 3 hitscan shots .12 s apart, 30 each, head x1.5. Full damage to 8 m, falls to 40% at 16 m and beyond. .36 s cast lock |
| 4 | Golden Ratio | 5 s. Every shot is a full shot: 80, head x2.25, .75 s apart, no charge, no ammo use. Hit area grows (head radius +.14, body +.35). Each shot pierces one target. Mag refills on cast |

### 1.2 The Siaolang

HP 160, speed 8.2, size 1, ult cost 190, bot range 3. Q is Elbow Jab (Gym Hunk melee, no lunge).

| Slot | Name | Numbers |
|---|---|---|
| LMB | Bare Arms | Melee. 32 a swing, range 2.3 m, 50 degree arc, .1 s windup, .38 s cycle. First swing within .5 s of leaving Predator deals +20 |
| 1 | Predator | cd 12. 5 s invisible to enemies, 25% faster. Any attack, ability, ult or Q ends it. Taking damage makes him flicker for .6 s. A soft pop plays every 1.5 s so he can be heard |
| 2 | Stim Siol | Passive. On a KO: heal 60 and 50% faster for 5 s. This is on top of the 25 heal everyone gets on a KO. The HUD slot shows the 5 s buff timer and cannot be pressed |
| 3 | Stun | cd 10, cast .1 s. 3.5 m cone (35 degrees), 20 damage, 1 s stun (no moving, no shots, no casts). Knocks Lim out of Bird Escape. Runner's High blocks it |
| 4 | Wild Leap | Big forward leap: 10 m/s, 7 m/s up. Take-off hits 50 in radius 3. Landing hits 80 inside 2 m, 50 at the 4 m edge, and slows 50% for 2 s. Ends on landing after .15 s or at 3 s |

How he differs from Recess Rascal: Rascal throws shurikens, dashes and blocks. The Siaolang has no ranged attack at all. He gets in unseen, wins fights with a stun and big swings, and chains kills through Stim Siol.

### 1.3 How Bird Escape works

- On cast Lim becomes a black and yellow hornbill for 2.5 s. His body hides and a flapping bird mesh takes his place.
- He flies forward at 12 m/s along his aim. A player steers with the mouse. A bot flies away from the nearest enemy within 12 m.
- Space climbs at 6 m/s and crouch drops. He cannot rise more than 4.5 m above his take-off height. Bots climb at .6 of that.
- He takes 35% less damage. He cannot shoot, melee, cast or ult. The charge and scope drop.
- The camera goes third person: 3.2 m back (clamped by walls) and .8 m up, capped at 6.9 m so it stays under the 7.2 m hawker roof.
- It ends early on a stun, a snare or death. Gravity then takes over. Flying off a ledge is a real risk.
- Use: escape a diver, reach a high perch, or reposition across a lane.

### 1.4 NS Boy scope retune

- RMB gives NS Boy a 1.75x zoom with a light vignette.
- Scoped he moves 25% slower.
- Full head is x2 scoped (116, the old number) and x1.75 unscoped (102, was 116). Tap and full body damage are unchanged.
- Bots scope when the target is over 15 m away.
- Scope is off during Live Firing.
- Kit text: 'hold .6 s: tap 26, full 58, full head 102, 116 scoped. RMB 1.75x zoom. 8 bands'.

## 2. Kit text (all lines 90 characters or less, build3.py asserts this)

Lim:
- LMB Telephoto Shot: hold 1.2 s, .8 s scoped: tap 30, full 80, full head 180. 6 shots
- 1 Claw Trap: drop a trap up to 10 m away. Snaps for 15, snares 2 s. Enemies see it within 8 m
- 2 Bird Escape: turn into a hornbill for 2.5 s: fly 12 m/s, 35% less damage, no shots
- 3 Burst Mode: 3 quick shots, 30 each, head x1.5. Drops to 40% from 8 to 16 m
- 4 Golden Ratio: 5 s: every shot is full, 80, head x2.25, bigger hit area, pierces
- P Scope: RMB: 4x zoom, 40% slower moves, full charge in .8 s

Siaolang:
- LMB Bare Arms: 32 a swing, fast. First hit out of Predator +20
- 1 Predator: 5 s invisible, 25% faster. Attacking ends it. Hits make you flicker
- 2 Stim Siol: passive. On a KO: heal 60 and 50% faster for 5 s
- 3 Stun: 3.5 m swipe for 20. Stuns 1 s: no moving, no shots
- 4 Wild Leap: big leap. 50 r3 on take-off, 80 r4 and a slow on landing

Blurbs:
- Lim: Retired uncle with a huge lens. He waits all day for one shot.
- Siaolang: Kampung boy in a singlet. Fast hands, no fear, no plan.

## 3. Voice lines (text only, HEROES.lines order: pick, 1, 2, 3, 4, KO)

| Slot | Lim | Siaolang |
|---|---|---|
| pick | Wah, got good light today. | Who want to fight? |
| 1 | Shh, the bird is nearby. | Now you see me... |
| 2 | Fly away first! | (none, passive) |
| 3 | Burst mode! | Stand still lah! |
| 4 | Golden hour, everybody smile! | Wild leap! |
| KO | Got the shot. | Too easy, bro. |

## 4. Models and weapons (KayKit)

- Lim: Barbarian.glb body retextured khaki (#b8a878, #8f8259), Knight head with grey hair, white brows, glasses, a bucket hat (two cylinders) and two vest pockets. Third person: black camera body, white telephoto, red ring, team band. First person: camera and white lens in the right hand, khaki sleeves. USES Barbarian, Knight.
- Siaolang: Rogue.glb with cape and weapons hidden, white singlet, bare tan arms, black shorts, red headband torus. Third person: team wristbands on both hands. First person: two bare arms, team cuffs from arm(). USES Rogue.
- Bird: one hornbill group per Lim (sphere body, yellow cone bill and casque, white tail, two flapping wings), toon M() materials, 6 meshes.
- Old-model fallbacks: lens uses buildNsBoy, siao uses buildGym, with NS Boy size, budget and height tables.
- PCAM: no entry needed. The default portrait framing puts both heads and feet inside the disc (shots/h3-lineup.jpg).

## 5. HUD.KITS entries

```
lens: {name: 'Long Lens Lim', han: '摄', field: '--hdb-khaki', hp: 150, basic: 'band', ab: [['Claw Trap', 'gum'], ['Bird Escape', 'dash'], ['Burst Mode', 'band'], ['Golden Ratio', 'ot']]},
siao: {name: 'The Siaolang', han: '野', field: '--hdb-rose', hp: 160, basic: 'walker', ab: [['Predator', 'dash'], ['Stim Siol', 'pb'], ['Stun', 'megaphone'], ['Wild Leap', 'scoot']]}
```

- Han: 摄 (to shoot a photo) for Lim, 野 (wild) for the Siaolang.
- New fields: `--hdb-khaki:#D9C9A0` and `--hdb-rose:#E8A3A8`.
- Icons reuse existing keys. New art can replace them later.

## 6. Bot rules

Lim (HOLD_ROLE sniper):
- Scopes when it has a target over 15 m away. Holds to full charge 60% of the time, like NS Boy.
- Claw Trap: if a melee enemy is within 12 m, drops it 30% of the way from that enemy to himself. With no target and standing in a zone, drops it 2 m on the enemy side of the zone centre.
- Bird Escape: below 35% hp with an enemy within 10 m, or 2 or more enemies within 5 m. Flies away from the nearest enemy.
- Burst Mode: target under 10 m with line of sight.
- Golden Ratio: target 12 to 45 m away with line of sight.

Siaolang (HOLD_ROLE assassin):
- Predator: target 6 to 25 m away and not already invisible.
- Stun: target under 3.2 m.
- Wild Leap: target 4 to 9 m away with line of sight. Turns to face it first.

All bots vs Predator: an invisible Siaolang is ignored beyond 6 m unless he is flickering. Reaction time against him is +.3 s.

## 7. Counter web

Pair win% from BAL.duels(10), both orders pooled, draws out.

| Hero | Counters | Countered by |
|---|---|---|
| Long Lens Lim | JC Debater (90%) | The Siaolang (11%) |
| The Siaolang | Long Lens Lim (89%) | Ah Ma and Gym Hunk (0%) |

The loop: Lim outranges Debater. The Siaolang closes on Lim unseen and stuns him out of Bird Escape. Tanks with big melee and hp stop the Siaolang.

## 8. Balance results

Gate (acceptance.js, baselineDraw 125) on the proto, after the bird camera fix: PASS 8, FAIL 0.
- G6 scene draws avg 61.9, max 94. All passes avg 79.2, max 116. Limits 130 and 180.
- G7 step 0.1138 ms. Baseline chope.html was 0.1207 ms.

Draws with the new heroes in the match (autopilot, 3600 steps):
- Lim comp: avg 60.6, max 87, step 0.133 ms.
- Siaolang comp: avg 60.9, max 88, step 0.135 ms.

Duels (n=10 per ordered pair), win% of the row hero:

| | ahma | debater | engineer | gym | nsboy | rascal | rider | tarik | uncle | lens | siao | overall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lens | 30 | 90 | 25 | 15 | 25 | 50 | 50 | 100 | 65 | | 11 | 46 |
| siao | 0 | 53 | 50 | 0 | 55 | 20 | 40 | 100 | 50 | 89 | | 45 |
| nsboy | 75 | 95 | 35 | 25 | | 55 | 80 | 100 | 85 | 75 | 45 | 67 |

Before tuning, Lim was 41% and the Siaolang 36%. The tuning: Siaolang melee 28 to 32, Predator speed .15 to .25, Lim shot cd .6 to .5.

TTK (BAL.ttk, median s, cells 5/10/20 m):

| att | ahma | gym | uncle | nsboy | engineer | debater | tarik | rider | rascal | lens | siao |
|---|---|---|---|---|---|---|---|---|---|---|---|
| lens | 4.1/6.7/inf | 6.5/5.2/8.3 | 1.7/2.9/4.7 | 2.2/2.6/2.3 | 2.4/4.8/5.4 | 5.4/3.7/3.6 | 2.3/inf/5.3 | 2.3/2.3/5.7 | 4.2/4.8/8.4 | 3.1/1.9/3.0 | 1.0/3.0/4.8 |
| siao | 3.0/3.4/4.5 | 2.6/3.2/4.6 | 1.9/2.5/4.0 | 1.9/2.6/3.2 | 1.9/2.5/3.5 | 1.9/2.6/3.2 | 2.3/2.5/3.8 | 1.9/2.8/3.3 | 1.5/2.1/3.1 | 2.0/2.2/3.1 | 1.8/2.6/3.5 |

Notes:
- tests/balance.js has no TTK bands for wave 2 or wave 3 heroes. proto-heroes3/bal.js adds them to the back-line band at run time. The tests file is not edited.
- 232 of 363 cells are out of band across the whole roster, so the existing heroes are out of band too. The bands need a separate pass.
- Lim's 20 m bot TTK is noisy (3 trials per cell, 60% full-charge holds). Read it as a rough guide only.
- NS Boy sits at 67% and Gym Hunk at 86%. Both were high before wave 3.

## 9. Skipped, add later

- Scope glint for enemies. Add if Lim feels unfair at range.
- Player-side invisibility tint. The player sees himself normally in first person.
- Kopi Can Turret still targets an invisible Siaolang.
- The bird mesh is never freed. One per Lim, fine for a 6v6 match.
- The Predator "giggle" is the existing pop sound. A real voice clip can replace it.
- Claw Trap is a snare (75% slow, no jump), not a full root.
- Icons reuse existing keys.

## 10. Requests

To MAPS3 (classroom block):
- Lim wants at least one 40 m clear lane per side, ideally the corridor or bridge.
- Bird Escape plus map.fall: a Lim whose bird ends over the open gap falls and dies. That is fine as a risk. Please keep the fall a y threshold so Bird Escape over the gap still works while airborne.
- Any roof or ceiling: please make it a collide obstacle, so wallDist can clamp the bird camera. Today the camera is capped at 6.9 m by a constant, the same way Peak Hour Rush caps at 6 m.

To art:
- Icons for Claw Trap, Bird Escape, Burst Mode, Golden Ratio, Predator, Stim Siol, Stun and Wild Leap. Current ones are placeholders from existing keys.

To B: the landing checklist below.

## 11. Landing checklist (READY for B)

1. Snapshot chope.html as chope.pre-heroes3.html.
2. Apply the splices in build3.py order. Each anchor must match exactly once in chope.html. build3.py asserts this and passed against chope.html as of 2026-11-04. The easiest path is to run `python3 proto-heroes3/build3.py` and diff proto-heroes3/chope.h3.html against chope.html, then copy the diff by hand without the last rep (the test hook).
3. Check `node --check` on the extracted module and that the file is ASCII only (the han characters are \u escapes).
4. Run the gate: `node proto-heroes3/run.mjs "http://127.0.0.1:8801/chope.h3.html?q" proto-heroes3/gate.js`. Point it at chope.html after landing. Expect PASS 8, G6 avg about 62, max about 94, G7 about 0.11 ms.
5. Smoke: `node proto-heroes3/run.mjs URL proto-heroes3/smoke.js`. It needs the rmb hook, so run it on the proto build or add the hook to the TESTQ __chope object.
6. Balance: `node proto-heroes3/run.mjs URL proto-heroes3/bal.js > out.json`, then `python3 -I proto-heroes3/duelsum.py out.json lens siao`.
7. Shots for review: proto-heroes3/shot_lineup.js and proto-heroes3/shot_game.js (set window.__MODE to 'scope' or 'bird').
8. Add a CHANGELOG line and bump the version.

Splice points (section numbers match the comments in build3.py):

| # | Section | Anchor (start, `\n` is a newline) |
|---|---|---|
| 1 | 1 | `KO while charging: half ult back']]},\n};\nconst SKINS=[` |
| 2 | 1 | `'hold .6 s to stretch: tap 26, full 58, full head 116. 8 bands'` |
| 3 | 2 | `if(e.cdP>0\|\|e.castT>0\|\|!e.alive\|\|e.mw>0\|\|e.chT>0\|\|e.q)return...` |
| 4 | 2 | the NS Boy band block, from `  else if(e.hk==='nsboy'){ // Rubber Band Rifle` up to, not including, `  }else if(e.hk==='rider'){ // Chopstick Fan` |
| 5 | 2 | `function bandReload(e){const W=e.wpn;if(W.rlT>=0\|\|W.mag>=8)return;` |
| 6 | 2 | `if(W.rlT>=.6&&W.rlT<=.8){W.rlT=-1;W.mag=8;W.pre=true;` |
| 7 | 2 | `const ready=p.cdP<=0&&p.castT<=0&&p.alive&&!(W.rlT>=0)&&!p.q;` |
| 8 | 2 | `W.st=Math.min(.6,was+dt);if(was<.6&&W.st>=.6&&p.isPlayer)SFX.clink()` |
| 9 | 3 | `if(e.hk==='nsboy')Object.assign(e.wpn,{mag:8,rlT:-1,pre:false,st:0,hol...` |
| 10 | 3 | `if(e.hk==='nsboy'){const W=e.wpn;if(W.rlT>=0){W.rlT+=dt;if(W.arOk&&W.r...` |
| 11 | 3 | `if(c==='KeyR'&&player.hk==='nsboy'&&player.alive)bandActive(player);` |
| 12 | 3 | `  if(p.hk==='nsboy')bandInput(p,dt);else if(p.hk==='tarik')` |
| 13 | 3 | `a.head=isE&&(e.hk==='nsboy'\|\|e.hk==='engineer')` |
| 14 | 3 | `    if(e.hk==='nsboy'){\n      if(W.hold&&!(W.rlT>=0))chg(CHG.nsboy,Mat...` |
| 15 | 3 | `(p.hk==='nsboy'&&p.wpn.hold?.02*Math.min(1,(p.wpn.st\|\|0)/.6):0)` |
| 16 | 4 | `function hitscan(e,dir,dmg,hm=1.75,pierce=false){\n  const o=eyeOf(e,ne...` |
| 17 | 4 | `damage(e2,dmg*(h2?hm:1),e,{head:h2,weapon:'rubber band'})` |
| 18 | 4 | `{head,crit:hm===2,knock:tmpB.copy(dir).setY(0).normalize().multiplySca...` |
| 19 | 4 | `let best=Math.min(wallDist(o,dir,max),hazDist(o,dir,max));rhE=null;rhH...` |
| 20 | 4 | `hr=HR*z;sph.center.set(` |
| 21 | 4 | `sph.radius=(i?.42:.56)*z;` |
| 22 | 5 | `  if(e.button===0){mouseDown=true;if(player)player.wpn.pr=true}\n` |
| 23 | 5 | `addEventListener('mouseup',e=>{if(e.button===0)mouseDown=false});` |
| 24 | 5 | `for(const k in keys)keys[k]=false;mouseDown=false;` |
| 25 | 5 | `const s=.0022*profile.sens*(player.wpn.steer>clock?.4:1);` |
| 26 | 6 | `if(e.qPress){e.qPress=false;tryMelee(e)}` |
| 27 | 6 | `*(e.stumble>0?MV.stumbleMul:1);\n  let wx=` |
| 28 | 6 | `  if(e.chT>0)return charge(e,dt);\n` |
| 29 | 6 | `else if(e.hk==='rider'&&e.ultT>0){e.vel.y=(e.fly\|\|0)*8.5;e.carry=fal...` |
| 30 | 6 | `// Peak Hour Rush ceiling\n` |
| 31 | 7 | `if(!f\|\|!e.alive\|\|e.castT>0\|\|e.chT>0\|\|e['cd'+slot]>0\|\|qBusy(e...` |
| 32 | 7 | `if(f(e)===false)return false;fxr(` |
| 33 | 7 | `if(!e.H.kit[4]\|\|e.ult<e.H.ultCost\|\|!e.alive\|\|e.castT>0\|\|e.chT>...` |
| 34 | 7 | `  fxr(e.H.kit[4][1].toLowerCase(),'tele',e.pos);e.ult=0;` |
| 35 | 7 | `  const un=ULTS[e.hk];\n` |
| 36 | 8 | `  auE(e,e.hk==='ahma'?'w_walker':e.hk==='gym'?'w_medball':'q_whoosh');...` |
| 37 | 8 | `fl?84:m.dmg;let landed=false;` |
| 38 | 9 | `if(SHOT&&!SHOT.hit&&t.team!==SHOT.e.team){SHOT.hit=1;SHOT.e.stats.hits...` |
| 39 | 9 | `  t.alive=false;t.hp=0;t.mw=t.pendT=t.chT=t.stunT=0;if(t.dec)` |
| 40 | 9 | `  gainUlt(src,10);if(src.alive)heal(src,25,src);` |
| 41 | 10 | `closing:{cap:1,hp:0,life:4.5,r:0,y:.1}};` |
| 42 | 10 | `ring:new THREE.RingGeometry(.5,.62,20)};` |
| 43 | 10 | `closing:0x7b2436};` |
| 44 | 10 | `    if(d.kind==='gum'){\n` |
| 45 | 11 | `};\nABIL.engineer={` |
| 46 | 11 | `  if(e.hk==='tarik')tarikTick(e,dt);` |
| 47 | 12 | `for(const t of ents){if(!t.alive\|\|t.team===e.team)continue;const d=t...` |
| 48 | 12 | `if(T&&T!==a.lastT){a.lastT=T;a.react=rand(.15,.25)/sk(e)}` |
| 49 | 12 | `  }else if(e.hk==='nsboy'){\n    if(e.cd1<=0&&r(2)){const f=` |
| 50 | 12 | `  }else if(e.hk==='tarik'){` |
| 51 | 13 | `{const cd=p['cd'+s];if(cd<=0)cdTop[s]=0;` |
| 52 | 13 | `['PSLE Slash', 'slash']]}\n};` |
| 53 | 13 | `--hdb-blush:#EBC1C9;` |
| 54 | 13 | `  <div id="death" hidden>` |
| 55 | 14 | `if(camQ>.01&&cq[2])camera.position.addScaledVector(fwd(p.yaw,0,tmpA),c...` |
| 56 | 14 | `vm.rotation.set(ks*K[3],ks*K[4],ks*K[5]);vm.visible=true}` |
| 57 | 14 | `    const fv=REDUCED?78:` |
| 58 | 14 | `:6:0);if(Math.abs(fv-camera.fov)>.01){` |
| 59 | 14 | `  }else{\n    if(vm)vm.visible=false;` |
| 60 | 14 | `if(vm)vm.visible=false;if(state==='end'&&mvpCam)` |
| 61 | 15 | `const VIEWMODELS = {make, arm, add3, aim, ahma: buildAhMa,` |
| 62 | 16 | `const BUILDERS = {ahma: buildAhMa,` |
| 63 | 16 | `\n};\n\n/* ---- third person, CURRENT game weapons` |
| 64 | 17 | `const BUILD={ahma,uncle,nsboy,engineer:encik,gym,rascal,tarik:auntie,r...` |
| 65 | 17 | `const USES={ahma:['Rogue'],` |
| 66 | 18 | `fontReady.catch(()=>{}).then(` |
| 67 | test | `get autopilot(){return autoPilot},` SKIP. Proto-only rmb hook for tests |

Section key: 1 HEROES and BND, 2 tryPrimary, 3 spawn reload input bots anim, 4 hitscan and rayHit, 5 mouse, 6 physics, 7 tryAbility and tryUlt, 8 melee, 9 damage and kill, 10 Claw Trap deployable, 11 ABIL and h3Tick, 12 bots, 13 HUD, 14 camera, 15 viewmodels, 16 fallbacks and TP weapons, 17 KayKit, 18 alias tables.

## 12. Siaolang v2 (READY for B)

User request: a salivating middle-aged uncle with glasses and animal body language, a visible invisibility, Predator ends on any hit, and a stun telegraph. Built by `python3 proto-heroes3/siao2.py`, which reads chope.html and writes proto-heroes3/chope.s2.html plus a root copy chope.s2.html. It prints "18 reps ok" against chope.html as of 2026-11-05 (after ART3 landed). Never writes chope.html.

### 12.1 What changed
- Model (proto-heroes3/siao2_model.js, replaces `function siao()`): an original uncle on the Rogue rig. Bald dome with messy side tufts and a few strands on top. Thick round black glasses with a glint, heavy brows, open grin with two teeth, sweat beads and a drool strand. Round gut under a stained cream singlet, maroon shorts, red slippers. No real person's face, name, catchphrase or outfit.
- Body language: a bone tick on top of the mixer. Spine lean 12 degrees idle, 18 running, 20 in Wild Leap, with the face kept level. Arms sweep back on the run and reach forward on the pounce. Idle has a head tilt and a sniff twitch. Measured with proto-heroes3/s2pose.js.
- Voice: lines are now growls and snorts. New sounds b_siao_growl (Predator), b_siao_snort (Stun), b_siao_sniff (idle bots), b_siao_roar (Wild Leap) and a_siao_break (Predator pop). Blurb: "Feral uncle in a stained singlet. Sniffs you out, then pounces."
- Predator, own view: the first-person arms go see-through (opacity about .5) with a wobble and a pale rim, the screen edge gets a cool pulsing haze, and "INVISIBLE 4.7 s" counts down above the HUD. Reduced motion drops the wobble and the haze animation.
- Predator, enemy view: hidden, with a 0.2 s glimpse on each 1.5 s pop sound.
- Predator break: any damage ends it at once (was a 0.6 s flicker). The break plays a pale burst, a ring, a glassy crack sound, and "Spotted!" for the player. Counted in stats.pb.
- Stun telegraph: the player holds 3 to aim. A yellow floor wedge follows him. Release, or 2 s, swipes. On cast a red wedge flashes for 0.35 s for the caster and any player within 7.9 m. Bots cast instantly and still show the flash.
- Stun shape: one wedge, 3.9 m radius, 35 degrees each side, frozen at cast. The decal uses the same geometry. The hit test `inStun` is the same shape (centre inside, 2 m height band, line of sight). Damage, stun and Bird Escape cancel are unchanged. Range went from 3.5 m to 3.9 m so the shown area is generous to read.
- Kit text: "5 s invisible, 25% faster. Attacking or taking any damage ends it" and "hold to aim, release: 3.9 m wedge for 20. Stuns 1 s: no moving, no shots". Both under 90 characters.

### 12.2 Bot rules
- Predator only when `e.calm>2` (no damage for 2 s), since a hit would pop it. Other gates unchanged: cd ready, not invisible, target 6 to 25 m.
- Stun at `dist<3.6` (was 3.2), inside the 3.9 m wedge.
- Bots skip the aim hold and cast at once.

### 12.3 Costs
Measured against chope.html on hawker with the Siaolang as the player (proto-heroes3/s2cost.js and s2cost3.js):
- Scene objects: idle and invisible the same as chope.html. Aiming or flashing adds 1 mesh (the wedge). Both wedges share one geometry. Only one is visible at a time in practice.
- Programs: +1 at load ('rim1s', the shimmer arms), +1 the first time a wedge draws (MeshBasic transparent). 31 to 33.
- Textures: +1 (57 to 58). Geometries +2 at load, +2 once the wedges exist.
- Draws: +1 while a wedge shows, 0 otherwise. The HUD overlay is DOM.

### 12.4 Tests (2026-11-05)
- Gate on chope.s2.html: PASS 8, FAIL 0. G6 avg 60.9, max 96. G7 0.1128 ms per step at load 4.3 to 3.9 (logged, right at the limit).
- node --check on the module passes. The file is ASCII only.
- Smoke (proto-heroes3/s2smoke.js, output s2smoke.out.json):
  - shimmer on: overlay shown, "INVISIBLE 4.7 s", wobble .006, opacity .45, rim 1.23, program 'rim1s'.
  - break on hit: invisT 0, pb 1, overlay hidden, arms opaque.
  - enemy Siaolang: visible 3 of 90 frames while invisible, then visible after one hit.
  - aim decal visible while held. The flash sits at the same position and yaw, the aim hides, and the flash is gone 0.5 s later.
  - shape match: 1200 grid samples, 724 inside, 724 hit, 0 mismatches between hits and `inStun`, 0 mismatches between the decal polygon and `inStun`.
- 2 bot matches, Siaolang on both teams (proto-heroes3/s2bots.js, output s2bots.out.json). Elims, deaths, Predator casts, pops, stuns and leaps:
  - gym, ahma vs rider, rascal: 100-60, 3862 steps. Team 1 6/10, 5 Predator, 1 pop, 8 stuns, 1 leap. Team 2 9/11, 6 Predator, 1 pop, 9 stuns, 2 leaps.
  - lens, tarik vs nsboy, gym: 64-100, 4265 steps. Team 1 8/16, 3 Predator, 1 pop, 9 stuns, 2 leaps. Team 2 14/8, 6 Predator, 1 pop, 10 stuns, 2 leaps.
- Shots in shots/siao2/: front34.jpg, run.jpg, fp_shimmer.jpg, stun_telegraph.jpg. Files that start with an underscore are scratch.

### 12.5 Splice points (siao2.py order, each matches exactly once)

| # | Anchor (start, `\n` is a newline) |
|---|---|
| 1 | `blurb:'Kampung boy in a singlet. Fast hands, no fear, no plan.'` |
| 2 | `lines:['Who want to fight?','Now you see me...','','Stand still lah!',...` |
| 3 | `'5 s invisible, 25% faster. Attacking ends it. Hits make you flicker'` |
| 4 | `'3.5 m swipe for 20. Stuns 1 s: no moving, no shots'` |
| 5 | `b_ras_ult:{bus:'vox',pv:.3,cap:1,pri:0,L:bark(460,[['o','o',220,1.1]])...` |
| 6 | `auE(e,'a_ns_dash',{pitch:-3})},` |
| 7 | `  3(e){e.cd3=10;say(e,3);cast(e,.1,e=>{coneHit(e,3.5,35,t=>{damage(t,2...` |
| 8 | `function invisEnd(e){e.invisT=0;e.flkT=0;stOff(e.st.buff,'pred');if(!e...` |
| 9 | `function h3Tick(e,dt){` |
| 10 | `if((e.gigT-=dt)<=0){e.gigT=1.5;sfxAt('pop',e.pos)}}}` |
| 11 | `if(t.invisT>0)t.flkT=.6;` |
| 12 | `if(SLOTKEY[c]===3&&player)rulerRelease(player)}` |
| 13 | `if(t&&e.cd1<=0&&!(e.invisT>0)&&r(1.5)&&dist>6&&dist<25)tryAbility(e,1)...` |
| 14 | `else if(e.hk==='siao'){const f=fwd(e.yaw,0,new THREE.Vector3());e.leap...` |
| 15 | `vmo=demoVM()[hk]({team:TEAM_COL[1]});vm=vmo.g;camera.add(vm);` |
| 16 | `st.tarik=e.hk==='tarik'&&!!(e.wpn&&e.wpn.on);` |
| 17 | the whole `function siao(){\n const g=load(C+'Rogue.glb')` block up to and including ` return [o,g,1]}`, replaced by siao2_model.js |
| 18 | `get vicT(){return vicT}};` TEST ONLY, skip. It adds the `s2` hook the smoke needs |

Landing path: snapshot chope.html, run siao2.py, diff proto-heroes3/chope.s2.html against chope.html, copy the diff without rep 18. Then gate, smoke on the proto build (it needs the s2 hook), bump the version.

### 12.6 Known limits
- An enemy within 6 m still finds an invisible Siaolang, as before.
- The flash shows for any player within 7.9 m, even behind a wall. It is a floor decal, so walls hide most of it.
- The 'Spotted!' text fires for any invisible player. Only the Siaolang uses invisT today.
