# Reload for the ranged cast: build design

Companion to RELOAD_PLAN.md. Written 2026-11-16 from a read of chope.html. Nothing in chope.html has been changed yet.

Line numbers in chope.html move while the other writer is in the file (they shifted by about 35 lines during this read). Every change below is located by an anchor string. Each anchor must match exactly once before the edit is applied, same rule as tools/reload_hunks.py.

Includes the two later additions: NSF and Birdwatcher get +25% too, and Birdwatcher gets a battery swap reload.

## 0. Landing rules

- Backup first: `cp chope.html chope.html.bak_reload_all`.
- One step per landing. Gate after each one:
  1. Pull the inline scripts out and run `node --check` on them.
  2. `node tools/cdp.mjs <scenario>` with `?q`: page loads, a match starts for each of the 8 reload heroes, zero console errors.
  3. `node tools/tutorial_test.mjs` still passes (the tutorial has a reload lesson that reads `BND.mag` and `wpn.rlT`).
- Shots: JPEG capture, then `sips` to compress, into `shots/reload_all/`. Per hero: `<hk>_full.jpg`, `<hk>_low.jpg`, `<hk>_reload.jpg` (taken at the clip's most readable beat, listed per hero in section 6).
- No push, no publish, no zip upload. `chope-itch.zip` is rebuilt once at the end, locally.

## 1. Step 1: one MAG table, shared magReload

Goal: no behaviour change for NSF and Birdwatcher.

### 1a. MAG table
Anchor: `const bch=e=>e.hk==='lens'` (the line after BND). Add after BND:

```js
// mag heroes: mag size, reload s. free: the ult fires without using the mag. tank: counter shows a bar and a percent
const MAG={nsboy:BND.nsboy,lens:BND.lens};MAG.nsboy.free=MAG.lens.free=1;
```

BND keeps `mag` and `rl`. MAG points at the same objects, so there is one source of truth and tutorial.js (`band.mag`) is untouched. Step 2 adds the other rows.

### 1b. magReload
Anchor: `function bandReload(e){`. Replace the function with:

```js
function magReload(e){const W=e.wpn,M=MAG[e.hk];if(!M||W.rlT>=0||W.mag>=M.mag)return;W.rlT=0;if(e===player&&!autoPilot&&vmo&&RLV[e.hk])vmo.ab(RLV[e.hk])} // auto at empty, R when not full
```

The old `AU.play('ui_tick',{pitch:-7,gain:.7})` start sound moves into the clip's sound list (1e), as the `t=0` cue for nsboy and lens, so they sound the same.

Rename the three call sites: `bandReload(e)` in tryPrimary, `bandReload(player)` on KeyR, and the definition.

### 1c. Other BND checks that become MAG checks
| Anchor | Change |
|---|---|
| `if(BND[e.hk])Object.assign(e.wpn,{mag:BND[e.hk].mag,rlT:-1` (respawn) | `if(MAG[e.hk])Object.assign(e.wpn,{mag:MAG[e.hk].mag,rlT:-1,...` same fields |
| `if(BND[e.hk]){const W=e.wpn,A=BND[e.hk];if(W.rlT>=0&&(W.rlT+=dt)>=A.rl)` (tick) | see 1e |
| `else if(c==='KeyR'&&BND[player.hk]&&player.alive)bandReload(player)` | `MAG[player.hk]`, `magReload` |
| `function ammoTick(p){const B=BND[p.hk]` | `MAG[p.hk]` (full counter work is step 4) |
| nsboy and lens rows in tryUlt (`e.wpn.mag=8`, `e.wpn.mag=6`) | leave as they are in step 1. Step 2 adds the shared refill line |

Everything else that reads BND (charge, scope, bot head aim, third person stretch) stays BND.

### 1d. Viewmodel clip system: props and ammo keys
Inside `make()` in VIEWMODELS. Needed from step 5 on, landed in step 1 so the engine work is in one place. Three small additions:

1. `keyed()`: loop `k < a.length` in place of `k < 6`, and make the `ok` scratch array 7 long. Lets a key carry a 7th value.
2. `S.A` keys on the ammo mesh: `[t,[dx,dy,dz,rx,ry,rz,ds]]`. Scale is `1+ds`, so `ds:-1` hides it and `ds:.3` is a 30% overshoot. When no clip with `S.A` is running, A goes back to position 0, rotation 0, scale 1 (flag `vm.aD`).
3. `S.P` props: a list of `{m:'name',on:'R'|'L',k:[[t,[x,y,z,rx,ry,rz,s]],...]}`. `s` is the absolute scale, 0 hides. Meshes come from a `PROP` table of builders inside the closure (uses the existing `prep`, `box`, `cyl`, `sph`, `tor` helpers), built on first use, cached on the vm as `vm.pr[i]`, parented to R or L. One shared vertex colour toon material with the rim, same as the fallback builder. When `vm.abS` is not the clip that owns the visible props, hide them (covers the ammoTick cancel path that sets `vmo.abS=null`). `dispose()` frees them.

Props are always parented to a hand, never to the rig. That way reduced motion (which scales hand moves to 30%) keeps props attached.

No material hiding on the glb weapons. Where a weapon part should look swapped, the hand drops below the frame for the swap or the prop seats on top of the part it replaces.

### 1e. Tick and reload sounds
Anchor: `if(BND[e.hk]){const W=e.wpn,A=BND[e.hk];if(W.rlT>=0&&(W.rlT+=dt)>=A.rl){W.rlT=-1;W.mag=A.mag}}`. Replace with:

```js
{const M=MAG[e.hk],W=e.wpn;if(M&&W.rlT>=0){const t0=W.rlT,t1=W.rlT+=dt,C=RLV[e.hk];
  if(e===player&&!autoPilot&&C&&C.sn)for(const s of C.sn)if(s[0]>=t0-(t0?0:1)&&s[0]<t1&&(t0||s[0]===0?true:true))AU.play(s[1],s[2]);
  if(t1>=M.rl){W.rlT=-1;W.mag=M.mag}}}
```

Write the cue test plainly at landing: fire cue `s` when `t0<=s[0]&&s[0]<t1`, with `t0` taken as 0 on the first frame. Each clip has `sn:[[t,key,opts],...]`. nsboy and lens get `sn:[[0,'ui_tick',{pitch:-7,gain:.7}]]` in step 1, so they sound as before. The end of reload chime (`k_charge_full`) already comes from ammoTick for everyone.

Bots make no reload sound. Add one later if it is missed.

### 1f. Parity check for NSF and Birdwatcher
Scenario script run against `chope.html.bak_reload_all` and the new file, same seed, `FAST=1`:
- Spawn as nsboy. Log `(frame, wpn.mag, wpn.rlT.toFixed(3), cdP.toFixed(3))` every frame while firing 8 taps, through the auto reload, then 3 taps, R, reload, then ult.
- Same for lens, scoped and unscoped.
- The two logs must be identical. One shot of each mid-reload must match the old shot by eye.

## 2. Step 2: count heroes

### 2a. MAG rows
```js
Object.assign(MAG,{uncle:{mag:6,rl:1.6},engineer:{mag:5,rl:1.5},rider:{mag:12,rl:1.6,free:1},rascal:{mag:15,rl:1.4},dj:{mag:60,rl:1.8}});
```

| Hero | key | Mag | Reload | Fire cd | One mag lasts | Counter |
|---|---|---|---|---|---|---|
| NSF | nsboy | 8 | 1.5 s | .45 s + charge | unchanged | pips |
| Birdwatcher | lens | 6 | 1.8 s | .5 s + charge | unchanged | pips |
| Stinky Uncle | uncle | 6 | 1.6 s | .76 s | 4.6 s | pips |
| Engineer Encik | engineer | 5 | 1.5 s | 1.1 s | 5.5 s | pips |
| Delivery Driver | rider | 12 | 1.6 s | .38 s | 4.6 s | bar |
| Recess Rascal | rascal | 15 | 1.4 s | .305 s | 4.6 s | bar |
| Nightclub DJ | dj | 60 | 1.8 s | .111 s | 6.7 s | bar |
| Ice Cream Uncle | ice | 60 ticks, tank | 1.8 s | .1 s | 6.0 s | bar, percent |

### 2b. Fire code: one guard, one decrement
The plan says each hero decrements in its own branch. One guard at the top and one decrement at the bottom of tryPrimary does the same job with two lines, and covers rider, the generic branch (uncle, engineer, rascal, dj) and ice. BND heroes keep their own code inside their branch.

Anchor: `const dir=aimDir(e,new THREE.Vector3());` in tryPrimary. Add before it:

```js
const M=!BND[e.hk]&&MAG[e.hk],W0=e.wpn;if(M){if(W0.mag==null){W0.mag=M.mag;W0.rlT=-1}if(W0.rlT>=0)return}
```

Anchor: `if(!e.H.melee){e.anim.shotT=0;fxe('fxr',e.H.kit[0][1].toLowerCase(),'shot'`. Add before it:

```js
if(M&&!(M.free&&e.ultT>0)&&--W0.mag<=0)magReload(e);
```

The guard sits after the existing `e.cdP>0||e.castT>0...` return, so a blocked shot never costs a round.

### 2c. Ult rule
Anchor: `const [un,uo]=[].concat(ULTS[e.hk]);` in tryUlt. Add before it:

```js
if(MAG[e.hk]){e.wpn.mag=MAG[e.hk].mag;e.wpn.rlT=-1} // every ult refills the mag and cancels a reload
```

Then drop the now duplicate `e.wpn.rlT=-1;e.wpn.mag=8;` and `e.wpn.rlT=-1;e.wpn.mag=6;` from the nsboy and lens rows (rerun the 1f parity log after this).

Ult by ult:
| Hero | Ult | Rule |
|---|---|---|
| NSF | Live Firing, ultT 5 | refill, free fire for 5 s (as now) |
| Birdwatcher | Golden Ratio, ultT 5 | refill, free fire for 5 s (as now) |
| Delivery Driver | Peak Hour Rush, ultT 7 | refill at cast, free fire for 7 s (`free:1`). It is a weapon mode, same as the two above |
| Engineer | Claim OT, ultT 7 | refill only. The ult is about turrets, his gun keeps its mag. Turrets never reload |
| Stinky Uncle | Durian Drop | refill only. The durian and the kick use no rounds |
| Recess Rascal | PSLE Slash | refill at the press (start of the 1 s charge) |
| Nightclub DJ | Main Stage | refill only. The fire rate buff (x1.5) empties a mag in 4.4 s |
| Ice Cream Uncle | Triple Scoop Spin | refill only |

The rider refill runs at the press, .3 s before `ultT` is set by the cast. That is fine: the mag is full either way.

### 2d. Other rules, already covered
- R reloads early: KeyR change in 1c.
- Death and respawn refill: respawn line in 1c.
- Moving and abilities work while reloading: the guard is only in tryPrimary.
- Kopi Break's "next 3 boogers", Stars, Paper Cut counting: untouched.

## 3. Step 3: Ice Cream Uncle tank

A tank that drains while held is the same thing as 60 ticks at one tick per .1 s. So it is one row and the step 2 code handles it:

```js
MAG.ice={mag:60,rl:1.8,tank:1};
```

- Drain: 1 unit per Brain Freeze tick (`ICE.cd` .1 s), only when a tick fires. Not firing does not drain and does not refill. 6.0 s of mist per tank.
- Empty: auto reload, 1.8 s. R refills early.
- Free Scoops "25% faster shots" and the DJ fire rate buff make ticks come faster, so the tank drains faster in time but holds the same 60 ticks of damage.
- Freeze build: a 1.8 s reload gap resets the 1.5 s of steady hits. A full tank is 4 freeze builds, so this only bites when the tank runs out mid build.
- UI: `tank:1` shows a bar and a percent (step 4).

## 3b. Damage

Rounding: whole numbers where the kit text shows a whole number. DJ and Ice are small per hit, so they keep decimals in code and the text gives the per second figure.

| Hero | What | Before | After | Where in code |
|---|---|---|---|---|
| Stinky Uncle | direct | 40 | 50 | `shot.dmg`, and the literal `damage(te,40,` in boogerBurst |
| | splash | 21 | 26 | `splash(p,2,2,21,21,` in boogerBurst |
| | Stink ticks | 3 per half second | unchanged | status, not the shot |
| Engineer | dart | 44 | 55 | `shot.dmg` |
| | headshot 1.5x | 66 | 82.5 | follows |
| | after a bounce | 55 | 69 | `p.dmg=p.type==='dart'?55:14` |
| | turret, repair | 12, 20 | unchanged | |
| Delivery Driver (+40%) | centre stick | 12 | 17 | `dmg:(a?5:12)` in the rider branch, and `shot.dmg` |
| | side sticks | 5 | 7 | same |
| | centre pop | 9 to 3 | 13 to 4 | `(s?9:5)*m,(s?3:2)*m` in stickBurst |
| | side pop | 5 to 2 | 7 to 3 | same |
| | Star bonus, 2 m height bonus, Rush x1.2 | unchanged multipliers | | |
| Recess Rascal | shuriken | 21 | 26 | `shot.dmg` |
| | after a bounce | 14 | 18 | `:14` in the bounce line |
| | deflected shots | unchanged | | |
| Nightclub DJ | note | 5 | 6.25 | `shot.dmg` |
| | per second | 45 | 56 | |
| | Drop the Beat | 30 | unchanged | ability |
| Ice Cream Uncle | tick | 7 | 8.75 | `ICE.d1` (also the deployable tick) |
| | per second | 70 | 87.5 | |
| | Cold Snap, Cart Charge | unchanged | | abilities |
| NSF | tap | 26 | 32.5 | `BND.nsboy.t` |
| | full | 58 | 72.5 | `BND.nsboy.f` 32 to 40 |
| | full headshot 1.75x | 102 | 127 | follows |
| | full headshot zoomed 2x | 116 | 145 | follows |
| | Live Firing band | 42 | 42, kept | see below |
| Birdwatcher | tap | 30 | 37.5 | `BND.lens.t` |
| | full | 80 | 100 | `BND.lens.f` 50 to 62.5 |
| | full headshot 2.6x + 20 | 228 | 280 | follows |
| | flat headshot bonus | 20 | 20, kept | `hb` in hitscan |
| | Golden Ratio shot | 80 | 100 | change `hitscan(e,dir,80,2.6,true,'golden ratio')` to `B.t+B.f` |
| | Golden Ratio headshot | 228 | 280 | follows |
| | Burst Mode | 30 | unchanged | ability |

Ult shot choice:
- Birdwatcher's Golden Ratio is scaled to 100. Its kit text says every shot is fully charged, and a full charge is now 100. Left at 80, the ult shot would be weaker than a normal full charge. Coding it as `B.t+B.f` keeps the two tied.
- NSF's Live Firing stays at 42. The text never calls those bands full, 42 is still above the new tap (32.5), and at one band every .35 s it is 120 a second against about 69 for full charge fire. It does not need more.

### Kit text after the change (stat lines only)
- Booger Flick: `50 damage on a direct hit, 26 splash. Each Stink stack deals 3 damage every half second. 6 boogers.`
- Foam Dart Ricochet: `55 damage, 1.5x on headshots, 69 after one wall bounce. Tag lasts 3 seconds. A dart on your own turret repairs 20. 5 darts.`
- Chopstick Fan: `Centre stick 17 damage, 1.25x on headshots. Side sticks 7. Every stick explodes on the floor, walls and enemies: centre 13 to 4 within 2.4 m, sides 7 to 3 within 1.8 m. Each Star adds 4% centre damage, up to 5. 1.25x damage from 2 m above the target. 12 fans.`
- Peak Hour Rush: add `No reloading.` after `hit 20% harder and explode 25% wider.`
- Paper Shuriken: `26 damage, 1.25x on headshots, 18 after a bounce. Hits must land under 1 second apart. Paper Cut lasts 3 seconds. 15 shuriken.`
- Glow Notes: `9 notes a second for about 56 damage a second. Reaches about 15 m. 60 notes.`
- Brain Freeze: `8 m cone, about 88 damage a second. Slows by up to 40%. After 1.5 seconds of steady hits the target freezes for 2 seconds. A target that just thawed cannot freeze again for 4 seconds. The tank holds 6 seconds of mist.`
- Rubber Band Rifle: `Full stretch takes 0.6 seconds. Tap 33, full 73, full headshot 127, or 145 zoomed. 1.75x zoom, moves 25% slower. 8 bands.`
- Telephoto Shot: `Unscoped, hold for 1.2 seconds. Scoped, it charges itself in 0.8 seconds, then click. Tap 38, full 100, full headshot 280. Every headshot also adds 20. 6 shots.`
- Golden Ratio: `Lasts 5 seconds. 100 damage a shot, 2.6x plus 20 on headshots, one every 0.75 seconds. Pierces one target. Refills your shots.`
- Live Firing: unchanged.

Also check the code comments that quote old numbers (boogerBurst, stickBurst, the BND comment) and the tutorial text for any quoted damage.

### What the buff does to damage over time
Direct hits only, firing nonstop, reload included.

| Hero | Before | Burst after | Sustained after |
|---|---|---|---|
| Stinky Uncle | 53 /s | 66 | 49 |
| Engineer | 40 | 50 | 39 |
| Delivery Driver (all 3 sticks) | 58 | 82 | 60 |
| Recess Rascal | 69 | 86 | 66 |
| Nightclub DJ | 45 | 56 | 44 |
| Ice Cream Uncle | 70 | 88 | 67 |
| NSF (full charge) | 46 | 58 | 58 |
| Birdwatcher (scoped full) | 46 | 58 | 58 |

The six new reload heroes come out about even over a long fight and stronger in a burst. NSF and Birdwatcher already paid for their reload, so they get a straight 25%.

## 4. Step 4: counter

Reuse the other agent's counter (`amEl`, `.amn` number, `.amr` pips, `.amb` bar, `amX` crosshair ring and R prompt). Changes in ammoTick:

- `const B=MAG[p.hk]`, `bar=B.mag>10||!!B.tank`.
- On hero change: if `bar`, `amR.innerHTML=''` and add class `bar`. Else build pips as now. `.amm` text is `'/ '+B.mag`, or `'%'` for a tank.
- Number: `n`, or `Math.round(100*n/B.mag)` for a tank. `∞` during a free ult only (`B.free&&p.ultT>0`). Today it is any `ultT>0`, which would wrongly show ∞ for the Engineer's 7 s ult.
- Bar fill: reload progress `u` while reloading (as now), else `n/B.mag`.
- When `bar`: no per round pop animation and no per pip tick sound (DJ fires 9 a second). Keep the pop and tick for pip heroes.
- `low` stays `mag<=Math.ceil(B.mag/4)`.

CSS, next to the existing `.chud .ammo .amb` rules:

```css
.chud .ammo.bar .amr{display:none}
.chud .ammo.bar .amb{opacity:1;height:calc(5*var(--p))}
.chud .ammo.bar.low .amb i{background:#FF5A4E}
```

`amEl.className='ammo '+p.hk` on hero change wipes the state classes. Add `bar` there in the same assignment.

## 5. Step 5: reload animations

All clips go in the RLV table (anchor: `const RLV=(()=>{`). Format as today: `d` length, `G` both hands, `L` off hand, `R` weapon hand, keys `[t,[dx,dy,dz,rx,ry,rz],ease]`, plus the new `A`, `P` and `sn`. `v()` scales hand moves to 30% under REDUCED, as RLV does now. Prop and ammo keys are not scaled, since they ride on the hands.

Shared shape for every clip: a short anticipation move the wrong way (about .1 s), a fast main action, a hard contact beat with a 1 frame style overshoot, and a `backOut` settle that ends by the reload time. Each clip's `d` equals the hero's reload time. The plan says to keep motion under about 1 s. These run the full reload, like the two existing clips do, with the busy part in the middle and the last .3 s only a settle.

The numbers below are the starting values. They get tuned against the mid-reload shots at landing. Seat positions on the glb weapons need one look each.

Sounds use keys that already exist. At landing, assert every key in every `sn` resolves in the audio table.

### 5.1 Stinky Uncle: roll a fresh one (1.6 s)
Idea: the flick hand goes up to his nose, digs twice, comes down palm up and rolls a new booger between the fingers. It grows with a spin and a wobble.
- Hands: R is the flick hand with the booger (A). L holds the kopi bag and sags out of the way.
- Props: none. The booger is the A mesh.

```js
uncle:{d:1.6,
  R:[[0,Z],[.12,v([.02,-.03,.03,.2,0,.1]),'out3'],           // dip, anticipation
     [.38,v([-.14,.2,.16,-.7,.3,-.3]),'backOut'],            // up to the nose, top centre
     [.5,v([-.13,.21,.17,-.6,.45,-.3])],[.62,v([-.15,.19,.16,-.75,.2,-.3])],[.74,v([-.13,.21,.17,-.6,.45,-.3])], // two digs
     [.95,v([-.04,.05,.02,-.25,0,.25]),'out3'],               // down, palm up
     [1.05,v([-.03,.06,.02,-.25,.25,.25])],[1.15,v([-.05,.05,.02,-.25,-.25,.25])],[1.25,v([-.03,.06,.02,-.25,.25,.25])], // rolling circles
     [1.6,Z,'backOut']],
  L:[[0,Z],[.3,v([0,-.05,.02,-.15,0,.1]),'out2'],[1.2,v([0,-.04,.02,-.1,0,.1])],[1.5,Z,'backOut']],
  A:[[0,[0,0,0,0,0,0,-1]],[.92,[0,0,0,0,0,0,-1]],[1.3,[0,0,0,0,0,6.28,.3],'out3'],[1.45,[0,0,0,0,0,6.28,0],'out2']], // hidden, grows past full size while spinning, settles
  sn:[[.38,'w_booger',{pitch:7,gain:.3}],[.62,'ui_tick',{pitch:3,gain:.5}],[.74,'ui_click',{pitch:6,gain:.5}],[1.05,'ui_tick',{pitch:-2,gain:.4}],[1.25,'ui_tick',{pitch:1,gain:.4}]]}
```
Shot beat: .62 (hand at the nose).

### 5.2 Engineer Encik: dart clip, knocked home with the spanner (1.5 s)
Idea: blaster rolls onto its side, the old clip drops out, the spanner hand brings a fresh lime clip up from the tool belt, pauses, then knocks it in. The blaster jumps, then he racks it and the dart shows at the muzzle.
- Hands: R holds the blaster. L holds the spanner and carries the clip.
- Props: `clip` (lime box .045 x .1 x .05 with three white dart tips). Two uses: old one on R, new one on R too, with L timed to sit under it. Seat is the blaster's own lime mag at about `[0,-.05,-.2]`, so the prop vanishing at the end cannot be seen.

```js
engineer:{d:1.5,hA:[.05,1.2],
  G:[[0,Z],[.16,v([-.03,.05,.03,.3,.25,.55]),'out3'],[1.1,v([-.03,.045,.03,.27,.22,.5])],[1.5,Z,'backOut']],
  L:[[0,Z],[.14,v([-.04,-.36,.12,-.5,0,.3]),'in2'],[.6,v([-.03,-.34,.1,-.4,0,.3])],
     [.84,v([.36,-.1,-.14,.2,0,-.3]),'out3'],[.9,v([.36,-.11,-.14,.2,0,-.3])],   // under the gun, small pull back
     [.98,v([.38,-.03,-.16,.3,0,-.3]),'in2'],[1.08,v([.3,-.08,-.1,.1,0,-.1]),'out2'],[1.4,Z,'backOut']], // knock, bounce off
  R:[[0,Z],[.97,Z],[1.02,v([0,.02,0,.1,0,0]),'in2'],[1.15,Z,'out2'],[1.2,v([0,0,.05,-.1,0,0]),'in2'],[1.4,Z,'backOut']], // jump from the knock, then rack
  P:[{m:'clip',on:'R',k:[[0,[0,-.05,-.2,0,0,0,0]],[.18,[0,-.05,-.2,0,0,0,1]],[.22,[0,-.07,-.2,0,0,0,1]],[.5,[.02,-.6,-.15,.8,0,.6,1],'in2'],[.52,[.02,-.6,-.15,.8,0,.6,0]]]},
     {m:'clip',on:'R',k:[[0,[-.1,-.5,-.1,0,0,.4,0]],[.6,[-.1,-.5,-.1,0,0,.4,1]],[.84,[0,-.12,-.2,0,0,0,1],'out3'],[.9,[0,-.13,-.2,0,0,0,1]],[.98,[0,-.03,-.2,0,0,0,1],'in2'],[1.06,[0,-.05,-.2,0,0,0,1],'out2'],[1.3,[0,-.05,-.2,0,0,0,1]],[1.32,[0,-.05,-.2,0,0,0,0]]]}],
  sn:[[.18,'ui_back',{pitch:4,gain:.6}],[.98,'ui_click',{pitch:-4,gain:.9}],[1.2,'w_dart_hit',{pitch:6,gain:.35}]]}
```
Shot beat: .9 (clip under the gun, spanner hand ready).

### 5.3 Delivery Driver: fresh bundle from the bag (1.6 s)
Idea: the stick hand drops out of view, the phone hand comes up with a paper wrapped bundle of chopsticks, pulls back and slaps it into the other hand. The fan snaps open with two flicks.
- Hands: R holds the fan. L holds the phone and carries the bundle on top of it.
- Props: `bundle` (three pale sticks in a white paper sleeve with a green band), on L.

```js
rider:{d:1.6,
  R:[[0,Z],[.1,v([0,.03,0,.15,0,0]),'out2'],[.3,v([.04,-.4,.1,-.5,0,-.2]),'in2'],[.7,v([.04,-.38,.1,-.5,0,-.2])],
     [.95,v([-.06,.02,0,0,.2,.1]),'out3'],[1.02,v([-.03,.03,.03,.05,.1,.05])],            // up to meet, takes the slap
     [1.15,v([-.05,.04,-.02,0,.55,.15]),'out3'],[1.3,v([-.04,.03,-.02,0,-.3,-.1]),'out2'],[1.6,Z,'backOut']], // fan open, flick back
  L:[[0,Z],[.2,v([-.02,-.36,.1,-.4,0,.2]),'in2'],[.5,v([-.02,-.34,.1,-.4,0,.2])],
     [.82,v([.2,.04,-.06,.1,0,-.3]),'backOut'],[.92,v([.17,.04,-.06,.1,0,-.3])],[1.0,v([.3,.05,-.08,.1,0,-.5]),'in2'],
     [1.12,v([.22,.02,-.04,0,0,-.2]),'out2'],[1.5,Z,'backOut']],
  P:[{m:'bundle',on:'L',k:[[0,[0,.1,-.06,-.3,0,0,0]],[.45,[0,.1,-.06,-.3,0,0,0]],[.5,[0,.1,-.06,-.3,0,0,1]],[.99,[0,.1,-.06,-.3,0,0,1]],[1.03,[.05,.1,-.08,-.3,0,0,0],'out2']]}],
  sn:[[.3,'mv_crouch',{gain:.5}],[.82,'w2_chopstick',{pitch:-5,gain:.35}],[1.0,'ui_click',{pitch:2,gain:.9}],[1.15,'ui_tick',{pitch:5,gain:.6}],[1.3,'ui_tick',{pitch:9,gain:.6}]]}
```
Shot beat: .9 (bundle held up, just before the slap).

### 5.4 Recess Rascal: fold one over the ruler (1.4 s)
Idea: a sheet of exercise book paper appears on the ruler. Three quick folds, each a pinch of both hands with the sheet turning a quarter and shrinking. On the third it becomes a shuriken that spins up in the throwing hand.
- Hands: R is the throwing hand with the shuriken (A). L holds the ruler, used as the folding edge.
- Props: `sheet` (thin cream square .12 wide with two blue rule lines), on L.

```js
rascal:{d:1.4,
  L:[[0,Z],[.12,v([0,-.04,.02,-.2,0,.1]),'out2'],[.3,v([.2,.05,-.04,.15,0,-.35]),'backOut'],[.44,v([.2,.035,-.04,.15,0,-.35])],
     [.5,v([.21,.06,-.04,.15,0,-.5]),'in2'],[.62,v([.2,.035,-.04,.15,0,-.35])],[.68,v([.21,.06,-.04,.15,0,-.5]),'in2'],[.8,v([.2,.035,-.04,.15,0,-.35])],
     [.86,v([.22,.07,-.05,.15,0,-.6]),'in2'],[1.0,v([.12,.02,-.02,.05,0,-.2]),'out2'],[1.3,Z,'backOut']],
  R:[[0,Z],[.3,v([-.1,.04,-.02,0,.3,.3]),'backOut'],[.44,v([-.1,.05,-.02,0,.3,.3])],
     [.5,v([-.12,.03,-.02,.3,.3,.5]),'in2'],[.62,v([-.1,.05,-.02,0,.3,.3])],[.68,v([-.12,.03,-.02,.3,.3,.5]),'in2'],[.8,v([-.1,.05,-.02,0,.3,.3])],
     [.86,v([-.13,.02,-.02,.4,.3,.6]),'in2'],[1.0,v([-.02,.06,.03,0,-.4,-.2]),'out3'],[1.4,Z,'backOut']], // third fold, then the flick up with the new star
  A:[[0,[0,0,0,0,0,0,-1]],[.92,[0,0,0,0,0,0,-1]],[1.08,[0,.02,0,0,0,-6.28,.35],'out3'],[1.22,[0,0,0,0,0,-6.28,0],'out2']],
  P:[{m:'sheet',on:'L',k:[[0,[.02,.07,-.1,0,0,0,0]],[.14,[.02,.07,-.1,0,0,0,0]],[.3,[.02,.07,-.1,0,0,0,1],'backOut'],[.44,[.02,.07,-.1,0,0,0,1]],
     [.5,[.02,.075,-.1,0,0,1.57,.75],'in2'],[.62,[.02,.075,-.1,0,0,1.57,.75]],[.68,[.02,.08,-.1,0,0,3.14,.55],'in2'],[.8,[.02,.08,-.1,0,0,3.14,.55]],
     [.86,[.02,.085,-.1,0,0,4.71,.4],'in2'],[.92,[.02,.085,-.1,0,0,4.71,0]]]}],
  sn:[[.5,'ui_tick',{pitch:0,gain:.6}],[.68,'ui_tick',{pitch:4,gain:.6}],[.86,'ui_tick',{pitch:7,gain:.6}],[1.0,'w_shuriken',{pitch:5,gain:.3}]]}
```
Shot beat: .62 (sheet half folded between the hands).

### 5.5 Nightclub DJ: swap the record (1.8 s)
Idea: the launchpad tips up to face her. The spent record on it slows, she flicks it away like a frisbee, reaches down, holds a fresh one over the pad, lifts and drops it. The pad dips, the record spins up fast and sinks into the deck.
- Hands: R holds the launchpad. L holds the mic and does the flick and the drop.
- Props: `rec` (black disc r .07 with a pink label and a cyan ring). Three uses: old one on R, fresh one on L while carried, fresh one on R after the drop. The hand off between L and R happens at the contact frame.

```js
dj:{d:1.8,
  G:[[0,Z],[.18,v([-.05,.06,.04,.55,.1,-.1]),'out3'],[1.35,v([-.05,.055,.04,.5,.1,-.1])],[1.8,Z,'backOut']],
  L:[[0,Z],[.3,v([.3,.1,-.03,0,0,-.2]),'out3'],[.45,v([.32,.12,-.03,0,0,-.1])],[.6,v([.05,.2,-.1,0,0,.6]),'in2'],   // reach, lift, flick away
     [.75,v([-.04,-.36,.1,-.4,0,.3]),'in2'],[.95,v([-.03,-.34,.1,-.4,0,.3])],                                      // down for the fresh one
     [1.2,v([.3,.16,-.03,0,0,-.2]),'backOut'],[1.27,v([.3,.18,-.03,0,0,-.2])],[1.35,v([.31,.1,-.03,0,0,-.2]),'in2'], // hold over the pad, lift, drop
     [1.5,v([.2,.08,0,0,0,0]),'out2'],[1.75,Z,'backOut']],
  R:[[0,Z],[1.34,Z],[1.39,v([0,-.02,0,.08,0,0]),'in2'],[1.55,Z,'backOut']],
  P:[{m:'rec',on:'R',k:[[0,[-.02,.085,-.06,0,0,0,0]],[.16,[-.02,.085,-.06,0,0,0,0]],[.2,[-.02,.085,-.06,0,0,0,1],'backOut'],[.32,[-.02,.085,-.06,0,-2,0,1],'out2'],
        [.45,[-.02,.1,-.06,0,-2.3,0,1]],[.7,[-.5,.3,-.2,1.5,-6,1,1],'in2'],[.72,[-.5,.3,-.2,1.5,-6,1,0]]]},
     {m:'rec',on:'L',k:[[0,[0,.02,-.04,0,0,0,0]],[.9,[0,.02,-.04,0,0,0,0]],[.95,[0,.02,-.04,0,0,0,1]],[1.34,[0,.02,-.04,0,0,0,1]],[1.35,[0,.02,-.04,0,0,0,0]]]},
     {m:'rec',on:'R',k:[[0,[-.02,.085,-.06,0,0,0,0]],[1.34,[-.02,.085,-.06,0,0,0,0]],[1.35,[-.02,.085,-.06,0,0,0,1]],[1.41,[-.02,.08,-.06,0,.3,0,1.12],'out2'],
        [1.5,[-.02,.085,-.06,0,1.5,0,1]],[1.62,[-.02,.085,-.06,0,7,0,1],'in2'],[1.74,[-.02,.07,-.06,0,14,0,0],'in2']]}],
  sn:[[.2,'ui_back',{pitch:-5,gain:.5}],[.6,'q_whoosh',{pitch:8,gain:.3}],[1.35,'ui_click',{pitch:-2,gain:.9}],[1.45,'h_dj_turnup',{pitch:5,gain:.25}]]}
```
Shot beat: 1.25 (fresh record held over the tilted pad).

### 5.6 Ice Cream Uncle: fresh canister from the cart (1.8 s)
Idea: the nozzle rolls over. He unscrews the empty frost canister off the top and tosses it, scoops a full one up from the cart below the frame, plants it, twists it tight and pushes it down. Frost hiss.
- Hands: R holds the nozzle. L holds the wafer sandwich and works the canister.
- Props: `can` (pale blue cylinder r .04 h .1 with a pink scoop dome). Three uses, same hand off trick as the DJ. Seat is on top of the nozzle body at about `[-.02,.14,-.08]`.

```js
ice:{d:1.8,
  G:[[0,Z],[.2,v([-.04,.03,.05,.25,.2,.35]),'out3'],[1.4,v([-.04,.03,.05,.22,.18,.32])],[1.8,Z,'backOut']],
  L:[[0,Z],[.22,v([.34,.14,-.08,0,0,-.3]),'out3'],[.4,v([.34,.17,-.08,0,-.6,-.3])],[.55,v([.4,.1,0,0,0,-.6]),'in2'],  // grab, unscrew, toss
     [.7,v([-.02,-.36,.1,-.4,0,.3]),'in2'],[.95,v([-.02,-.34,.1,-.4,0,.3])],                                        // scoop from the cart
     [1.15,v([.34,.22,-.08,0,0,-.3]),'backOut'],[1.22,v([.34,.24,-.08,0,0,-.3])],[1.3,v([.34,.15,-.08,0,0,-.3]),'in2'], // over the seat, lift, plant
     [1.5,v([.34,.14,-.08,0,.8,-.3])],[1.75,Z,'backOut']],                                                           // twist tight
  R:[[0,Z],[1.29,Z],[1.34,v([0,-.025,0,.1,0,0]),'in2'],[1.5,Z,'backOut']],
  P:[{m:'can',on:'R',k:[[0,[-.02,.14,-.08,0,0,0,0]],[.18,[-.02,.14,-.08,0,0,0,0]],[.22,[-.02,.14,-.08,0,0,0,1]],[.4,[-.02,.17,-.08,0,-3.14,0,1],'out2'],
        [.48,[-.02,.19,-.08,0,-3.5,0,1]],[.75,[.25,-.5,0,2,-4,1,1],'in2'],[.77,[.25,-.5,0,2,-4,1,0]]]},
     {m:'can',on:'L',k:[[0,[0,.06,-.02,0,0,0,0]],[.9,[0,.06,-.02,0,0,0,0]],[.95,[0,.06,-.02,0,0,0,1]],[1.29,[0,.06,-.02,0,0,0,1]],[1.3,[0,.06,-.02,0,0,0,0]]]},
     {m:'can',on:'R',k:[[0,[-.02,.14,-.08,0,0,0,0]],[1.29,[-.02,.14,-.08,0,0,0,0]],[1.3,[-.02,.14,-.08,0,0,0,1]],[1.36,[-.02,.125,-.08,0,0,0,1.1],'out2'],
        [1.5,[-.02,.13,-.08,0,3.14,0,1]],[1.62,[-.02,.1,-.08,0,3.14,0,0],'in2']]}],
  sn:[[.22,'ui_back',{pitch:2,gain:.5}],[.95,'mv_crouch',{pitch:4,gain:.5}],[1.3,'ui_click',{pitch:-5,gain:.9}],[1.5,'h_ice_snap',{pitch:6,gain:.25}]]}
```
Shot beat: 1.2 (full canister held over the nozzle).

### 5.7 Birdwatcher: battery swap (1.8 s, replaces his current clip)
Idea: the camera tips up so its base faces him. The battery door pops open, the old battery slides out of the grip and tumbles away, and the camera lifts a little as the weight leaves. The off hand comes up with a fresh one, pulls back, pushes it in, then palms the door shut with a snap.
- Hands: R holds the camera. L does the battery and the door.
- Props: `door` (small dark flap .05 x .008 x .04, hinged at its back edge) on R. `batt` (dark grey block .035 x .06 x .025 with a yellow stripe and a gold contact). Two uses: old one on R, fresh one on L. Seat is the base of the grip. Call it `S=[sx,sy,sz]` and find it on the glb at landing. Start from `[.02,-.02,.02]`.

```js
lens:{d:1.8,
  G:[[0,Z],[.2,v([.03,.06,.05,.5,-.14,-.5]),'out3'],[1.38,v([.03,.055,.05,.46,-.12,-.46])],[1.8,Z,'backOut']],
  R:[[0,Z],[.3,Z],[.42,v([0,.015,0,.05,0,0]),'out2'],[.6,Z],                          // lifts as the old battery leaves
     [1.01,Z],[1.06,v([0,.02,0,.08,0,0]),'in2'],[1.2,Z,'out2'],                       // pushed up by the new one
     [1.24,Z],[1.28,v([0,.012,.02,-.08,0,0]),'in2'],[1.5,Z,'backOut']],               // door slap
  L:[[0,Z],[.16,v([-.04,-.32,.12,-.5,0,.3]),'in2'],[.55,v([-.03,-.3,.1,-.4,0,.3])],
     [.82,v([.3,-.14,.02,.2,0,-.2]),'out3'],[.9,v([.3,-.17,.03,.2,0,-.2])],            // under the grip, pull back
     [1.02,v([.31,-.08,.01,.3,0,-.2]),'in2'],[1.1,v([.3,-.12,.02,.2,0,-.2]),'out2'],   // push in, release
     [1.18,v([.3,-.15,.05,0,0,-.4])],[1.26,v([.31,-.09,.01,.2,0,-.2]),'in2'],          // wind up, palm the door shut
     [1.4,v([.2,-.1,.02,0,0,0]),'out2'],[1.66,Z,'backOut']],
  P:[{m:'door',on:'R',k:[[0,[S,0,0,0,0]],[.2,[S,0,0,0,0]],[.22,[S,0,0,0,1]],[.32,[S,1.9,0,0,1],'backOut'],   // pops past open, settles at 1.7
        [.4,[S,1.7,0,0,1]],[1.18,[S,1.7,0,0,1]],[1.26,[S,-.1,0,0,1],'in2'],[1.32,[S,0,0,0,1],'out2'],[1.34,[S,0,0,0,0]]]},
     {m:'batt',on:'R',k:[[0,[S,0,0,0,0]],[.3,[S,0,0,0,0]],[.32,[S,0,0,0,1]],[.42,[sx,sy-.05,sz,0,0,0,1],'out2'],[.7,[sx+.04,sy-.6,sz+.05,1.2,0,2.5,1],'in2'],[.72,[sx+.04,sy-.6,sz+.05,1.2,0,2.5,0]]]},
     {m:'batt',on:'L',k:[[0,[0,.07,-.02,0,0,0,0]],[.5,[0,.07,-.02,0,0,0,0]],[.55,[0,.07,-.02,0,0,0,1]],[1.02,[0,.07,-.02,0,0,0,1]],[1.06,[0,.1,-.02,0,0,0,0],'out2']]}],
  sn:[[.22,'ui_click',{pitch:5,gain:.7}],[.42,'ui_back',{pitch:-6,gain:.5}],[1.02,'ui_click',{pitch:-3,gain:.9}],[1.26,'ui_tick',{pitch:2,gain:.9}]]}
```
`[S,rx,ry,rz,s]` above means `[sx,sy,sz,rx,ry,rz,s]`. Shot beat: .9 (door open, fresh battery under the grip).

His old `ui_tick` start cue is dropped with the old clip. The third person RL pose for him stays.

### 5.8 NSF
Clip unchanged. Only gains `sn:[[0,'ui_tick',{pitch:-7,gain:.7}]]` from step 1.

### 5.9 Third person cue
Cheap, so it is in. A table next to `RL` (anchor: `RL=[[0,Z12],[.3,AV({1:.06,4:-.3,6:.6,7:-.2})`), same 12 channels (0 rigY, 1 rigRX, 4 aRx, 5 aRz, 6 aLx, 7 aLz, 11 squash):

```js
RL3={uncle:[[0,Z12],[.38,AV({1:-.06,4:2.4,5:-.4}),'backOut'],[.56,AV({1:-.04,4:2.3,5:-.3})],[.74,AV({1:-.06,4:2.4,5:-.4})],[1.0,AV({4:.9,5:.2}),'out3'],[1.6,Z12,'backOut']], // hand to the nose, two digs, roll
  engineer:[[0,Z12],[.16,AV({1:.05,4:-.25,3:.06}),'out3'],[.84,AV({1:.06,4:-.3,6:.9,7:-.3}),'out3'],[.98,AV({0:.02,4:-.2,6:1.2,7:-.3}),'in2'],[1.5,Z12,'backOut']], // off hand knocks up under the gun
  rider:[[0,Z12],[.3,AV({1:.1,4:-.6}),'in2'],[.82,AV({1:.04,4:.5,6:.9,7:-.4}),'backOut'],[1.0,AV({4:.6,6:1.0,7:-.6,11:.04}),'in2'],[1.6,Z12,'backOut']], // hand to the bag, slap together
  rascal:[[0,Z12],[.3,AV({1:.12,4:.8,5:.4,6:.8,7:.4}),'backOut'],[.5,AV({1:.14,4:.9,5:.5,6:.9,7:.5,11:.03}),'in2'],[.68,AV({1:.12,4:.8,5:.4,6:.8,7:.4})],[.86,AV({1:.14,4:.9,5:.5,6:.9,7:.5,11:.03}),'in2'],[1.4,Z12,'backOut']], // hunched over the fold
  dj:[[0,Z12],[.3,AV({1:.06,6:1.0,7:-.4}),'out3'],[.6,AV({6:1.6,7:.6}),'in2'],[1.27,AV({1:.04,6:1.4,7:-.3}),'backOut'],[1.35,AV({0:-.02,6:.9,7:-.3,11:.04}),'in2'],[1.8,Z12,'backOut']], // flick away, drop the new record
  ice:[[0,Z12],[.22,AV({1:.06,6:1.1,7:-.3}),'out3'],[.7,AV({1:.14,0:-.04,6:-.4}),'in2'],[1.22,AV({1:.04,6:1.3,7:-.3}),'backOut'],[1.3,AV({0:-.02,6:1.0,7:-.3,11:.04}),'in2'],[1.8,Z12,'backOut']]}; // bend to the cart, plant the canister
```

Applied in featEnt, inside `if(!e.q){`, as its own statement after the hero chain (not inside the `if(BND[e.hk])` block, which keeps `RL`):

```js
if(RL3[e.hk]&&W.rlT>=0)apC(h,kfA(RL3[e.hk],W.rlT,_aa),1);
```

Arm signs follow the existing rows (`4` positive raises the right arm, as in the uncle's flick). Check each in a third person shot. Under REDUCED apply at weight .5, like the other body motion.

## 6. Step 6: bots

Bots already reload at empty, because they go through tryPrimary.

Early reload: in the bot tick, next to the fire decision (anchor: `if(T&&a.react<=0){const m=e.H.melee;`). Add before it:

```js
if(MAG[e.hk]){if(a.target)a.rlI=0;else if((a.rlI=(a.rlI||0)+dt)>2)magReload(e)}
```

`magReload` returns at once when the mag is full or a reload is running. This also covers the autopilot player. NSF and Birdwatcher bots gain the early reload too, which is the one planned behaviour change for them and comes after the step 1 parity check.

## 7. Step 7: shots and wrap up

- 8 heroes x 3 shots (`full`, `low`, `reload` at the beat listed in section 5) into `shots/reload_all/` as JPEG. One third person contact sheet of the six RL3 poses.
- Low state: set `wpn.mag` to 1 (or 10 for the DJ, 12 for Ice) through the test hook.
- Reload state: set `wpn.rlT` and `vmo.abT` to the beat time, render one frame.
- Final: rebuild `chope-itch.zip` once, locally. Add a short entry to CHANGES.md.

## 8. Things in the plan I would change or check with Nigel

1. Birdwatcher one shot kills. A full charge headshot goes from 228 to 280. That now knocks out Engineer and Head Prefect (275 HP) in one shot, and leaves Recess Rascal on 5. Before, nobody below 228 HP existed, so no one died to one shot. If that is not wanted, cap his full value at 97 (full headshot 272) or lower the flat +20.
2. NSF and Birdwatcher get a straight 25% while the six new reload heroes come out about even over a long fight (table in 3b). The two snipers end up further ahead than the plan's "buff to pay for the reload" idea suggests.
3. Delivery Driver in Peak Hour Rush: +40%, then x1.2, 33% faster, and no reload for 7 s is about 130 direct damage a second before pops. The plan's ult rule gives this. The softer option is refill only, with reloads still happening in the air.
4. Rounding makes some buffs a little more than stated: side pop edge 2 to 3 is +50%, rascal bounce 14 to 18 is +29%. DJ and Ice keep decimals (6.25 and 8.75) so they are exact, and their kit text gives damage per second. Say if you would rather have whole numbers (DJ 6, Ice 9).
5. The plan says each hero decrements in its own fire branch. One guard and one decrement in tryPrimary covers all of them with less code. Same behaviour.
6. The plan gives the tank its own step. It is the same as a 60 round mag at one round per tick, so step 3 is one table row plus the UI flag.
7. The plan says under about 1 s of motion per clip. The clips here run the full reload time, like the two existing ones, with the action in the middle. Easy to shorten if they feel long.
8. ∞ on the counter currently shows for any `ultT>0`. With more heroes that would show ∞ during the Engineer's ult while his mag still drains. Step 4 limits it to free fire ults.
9. Rider, DJ and Ice have no ammo mesh in their viewmodel glb, so there is no visible "empty hand" state for them. Their reloads read through props and hand motion only. A proper empty state would need new glb parts.
10. The DJ record and the Ice canister shrink into the weapon at the end of the clip, since the weapon model has no slot for them. It reads as "pushed in" at toy scale. Worth a look in the shots.
11. Stink ticks, turret damage and all abilities are left alone. The buff is on the shot and its own splash only.
12. Still open from the plan: mag sizes and reload times are drafts, and turrets do not reload.

## 9. What landed differently from this design

Checked against screenshots of the real glb viewmodels, which differ from the fallback builders this design assumed.

- Third person squash uses channel 10. `apC` only reads 0 to 10, so the 11 in section 5 was wrong.
- Props are dropped under REDUCED (`pp=a=>REDUCED?null:a`). Hand moves still scale to 30%.
- Ammo keys (`A`) only scale. No spin.
- Rider has no prop. The glb off hand already holds a spare chopstick bundle, so the clip uses that.
- Engineer rolls the gun the other way (`rz -.8`, `rx .5`) so the mag well faces the off hand. The off hand holds the toolbox on the glb, so it dips to the toolbox for the fresh clip.
- Rascal's ruler is upright on the glb. The paper sheet is larger and folds upright beside it.
- DJ record seat moved onto the pad of the glb deck.
- Lens tips the camera nose down (`rx -1`) so the base faces the player. Door and both batteries ride on the camera hand. The off hand comes up from below with an open palm.
- Bots reload after 2 s with no target (step 6), as designed.
