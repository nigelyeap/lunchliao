# Chope! improvement log

Each agent turn appends a section: what changed, how it was tested, open bugs, and challenges for the other agents.

## Pass 1 - Gameplay

### What changed
- Pacing: points per held table per second cut from 1.1 to 0.45 (`PTS`). A full sweep now takes about 74s from zero instead of 30s. Bot-vs-bot matches now run 110-175s and are often within 10 points.
- Comeback: a team behind by 15 or more caps tables 30% faster and respawns 1.5s sooner (`trailing()`).
- Overtime: when the clock hits 0 and the trailing team has someone on a table, play continues. It ends 3s after they leave, capped at 30s (`OT_MAX`, `otGrace`). The timer reads OVERTIME and an OVERTIME! callout fires.
- Assists: anyone on the killer's team who hit the victim in the last 6s gets an assist, +8 ult, and a hitmarker plus "Assist on X" for the player. Assists column on the scoreboard. Assists count toward MVP rank.
- Elim reward: +12 ult and +25 HP on every elim. Killing someone on a 3+ streak gives a SHUTDOWN! callout and XP.
- Sustain: out-of-combat regen (8% max HP per second after 4s without damage). Two teh peng pickups on the flank lanes at (0, +-13) heal 80 and respawn after 15s. Bots go for them below 45% HP.
- Objective feedback: a readout under the crosshair while you stand on a table: "Choping A 73%", "Breaking A 40%", "CONTESTED A", "Holding A". HUD pips pulse while contested.
- Progression: per-hero mastery (M0-M5, shown on hero cards), first win of the day (+200 XP), XP lines for assists, best streak and shutdowns. End screen reward lines reveal one by one with a tick sound.
- Balance (bot-driven sims): Ah Ma slipper flies out 0.5s (was 0.42), 38 dmg (was 34), 0.55s cooldown (was 0.62), hit radius 0.78. Ah Ma HP 250 (was 230), speed 6.5. Ah Ma bot only throws inside 13m (it threw at 22m with a 13m weapon) and uses spin and ult at better ranges. NS Boy bot headshot aim 22% (was 35%) and spread 0.075 (was 0.05).
- Test hook `window.__chope` gained: `autopilot` (get/set, the player is driven by bot AI), `matchT` (get/set), `pickups`, `mem` (renderer.info.memory).

### Bugs fixed
- Ragdoll velocity aliased the shared `tmpA` vector in `kill()`, so any later use of tmpA bent the corpse's flight. Now cloned.
- Every slipper throw and every Slipper Storm slipper created two new BoxGeometries that were never disposed. Now shared `slipGeo`/`strapGeo`. Durian material shared too.
- `updateFx` never disposed the per-effect transparent materials from `B()` (rings, spheres, tracers). Now disposed.
- Character meshes (geometries and materials) were only removed from the scene on rematch or quit, never disposed. New `freeEnt()`.
- Quit to menu left live projectiles hanging in the scene. Now cleared.
- Clicking Play Again during the XP count-up threw away the rest of the XP. The remainder is now granted with level-ups. XP is stored as an integer (was drifting floats like 1465.0000000000057).
- Zone tissue-packet bob used `orbitT`, which is frozen during play. Now uses the match clock.
- A stale `profile.hero` key would crash `makeEnt`. Now validated on load.
- "1 tables chope'd" plural.

### How I tested
- Local server on 127.0.0.1:8771, built-in browser, `__chope.step()` with the new `autopilot` flag so the player slot plays like a bot.
- Baseline (original numbers, 9 matches): matches ended in 51-76s. Damage per hero summed over both teams: Ah Ma 8.3k, Auntie 15.7k, NS Boy 24.7k.
- Final (12 matches, 4 per player hero): lengths 139-174s, losing side scored 69-94. Elims per hero slot 107-151, damage 28-35k, deaths 117-142. Ah Ma K/D is about 1.0 (was about 0.6).
- Then 4 more full matches (NS Boy, Auntie, Ah Ma, NS Boy) through Play Again and Change Hero: 110-168s, no console errors.
- Idle player (Auntie): loses 5-100 in 93s. That is a 2v3 and losing is correct.
- Overtime: player forced onto B at 2s left while trailing. OT ran, readout went Choping B 8% to Holding B. Leaving ended it 3s later.
- Pickup healed 50 to 130 and set its 15s timer. Regen took 60 to 95 HP in 6s.
- Screenshots: in-match on table A (readout visible) and the end screen with reward lines.
- File is pure ASCII. Test profile in the 127.0.0.1 origin was cleared afterwards.

### Known issues
- `__chope.mem` reads 0 when the pane is in the background because nothing renders. I could not confirm the leak fixes by GPU counters. They are confirmed by code reading only.
- Autopilot matches are bot-vs-bot. Real human NS Boy has no spread and a 0.72s cooldown, so a good human NS Boy will out-damage the other heroes. Not tuned.
- Mastery is a plain XP counter and has no rewards beyond the M-level badge.
- The teh peng pickup is a plain brown cylinder with a ring. It needs a proper look.
- Projectiles move up to 1.9 m per frame at the 0.05 dt cap (tissue at 38 m/s). With a 0.62 hit radius they can tunnel past a target at low fps.

### Challenges for the other agents
- VISUALS: at 800px wide the "TANJONG KOPI" label runs into the Match Challenge box, and the hero name in the bottom-left vitals is near invisible against the bright floor. Fix the HUD contrast and the top-bar collision before adding any new effects.
- VISUALS: kills, assists, shutdowns and pickups all reuse the same few SFX (`SFX.cap`, `SFX.xp`). A shutdown or a 3-streak should sound different from a table capture. Also give the teh peng pickup a real model and a respawn tell. Keep it to shared geometries, because I just removed two per-throw leaks.
- PHYSICS: projectile hit tests are a single point check per step with no sweep. Tissue at 38 m/s can skip a 0.62 radius body at low fps. Add a swept segment test in `updateProjs` before tuning feel.
- PHYSICS: the bot unstuck logic jumps and sidesteps in a random direction with no wall check. Every zone table has four stools around it. Measure how long bots sit stuck there (I did not). NS Boy's dash also ignores walls (24 m/s straight line, then `collide` pushes out), and the Rotan Spin knockback of 14 can launch people onto table tops. Check these before adding new movement tech.

## Pass 1 - Visuals and Audio

### What changed
- Arena: warm sky gradient background, warmer hemisphere and sun, pushed-back fog. Stalls got awnings, light strips, lamps and counter clutter. Pillars got cuffs. 28 fluorescent tubes, bins and tray racks on the end walls (no colliders). Tables got condiments, trays, cups, bowls and chope tissue packets on stools.
- All static props are baked into one vertex-coloured merged mesh, plus one merged glow mesh and one merged blob-shadow mesh. Fans share one merged geometry. Scene mesh count mid-match fell from about 400 to about 315 with more detail on screen.
- Characters: a `body` sub-group carries squash and stretch, run bob, forward lean, leg and hand swing, air stretch, landing squash and a hurt squash (`animEnt`, called after `physics`). Hit flash is white for 60ms, then red. Team collar ring for readability from above. Ah Ma holds a slipper, NS Boy wears a field pack, Auntie carries a market bag. Shoes on everyone.
- Death: team-colour burst and a white pop on kill, then a poof and ring when the ragdoll shrinks away.
- Teh peng: clear cup, milky tea, foam, ice, straw, raffia loop and a light beam. While it is away the ring dims. In the last 3s it pulses. Respawn plays a ring, burst and pop. Pickup plays a slurp.
- VFX: projectile trails (cached per-colour materials, shrink instead of fade), thicker and longer tracers, a hit pop sphere on every hit, team-colour confetti on every table capture, beam flare on capture.
- Kill confirm: bigger rotated kill hitmarker, a mint assist hitmarker, and a "+1 ELIM / +25 XP" popup next to the crosshair ("x2" and up on streaks, gold "SHUTDOWN / +55 XP", mint "ASSIST / +10 XP").
- Ult ready: one edge flash plus a three-note formant "voice" jingle and an "Ultimate ready! Press Q" line, once per charge.
- HUD: challenge and killfeed drop to 84px under 1000px wide so they clear the score bar. Vitals sit on a dark panel. Team names hide under 640px.
- End screen: title slam, score count-up, staggered board rows, highlighted MVP row, win confetti, win or sad jingle, then music after 2.4s.
- Audio: distinct SFX for kill (pitched up per streak), shutdown, assist, capture, table lost, under attack, pickup slurp, respawn pop, low-HP heartbeat (below 35%), challenge done, win and lose. A hawker ambience bed (looped noise through two LFO-swept bands plus random cup clinks) plays during matches. A procedural I-vi-IV-V loop plays on menu and end screens. Mute on M or the top-right button, saved in localStorage (`chope-mute`).
- `__chope` gained `drawCalls`, `render()` (renders and returns draw calls) and `muted`. All old fields kept.

### Bugs fixed
- Sounds fired while the AudioContext was still suspended were queued and all played at once on resume. Nodes are now only built while the context is running (`live()`).
- `sphereFx`, `ringFx` and `tracer` built a new geometry on every call. They now share tagged geometries, and `updateFx` skips anything tagged `userData.keep`.
- Assists reused the kill hitmarker and the XP tick. They now have their own marker, sound and popup.
- At 759-800px the killfeed ran under the score bar (score bar bottom is 71px, killfeed top was 66px). Moved to 84px.

### Answers to challenges
- HUD at 800px and hero name contrast: fixed (see HUD above). Checked at 800x600.
- Same few SFX for everything: every event in that list now has its own sound. Shutdown and streak kills sound different from a capture.
- Teh peng model and respawn tell: done, all geometry and materials are shared module-level objects, created once.

### Disagreements with the gameplay pass
- Sustain stacks a lot: 8%/s regen after 4s, +25 HP per elim and 80 HP pickups. In autopilot matches players rarely stay low for long, which blunts the heartbeat and the pickup's value. Suggest dropping one of the three.
- `updateZones` writes pip styles and runs `$()` lookups every frame. Cheap at 3 zones, but it is DOM churn in the hot loop. Cache the elements and only write on change.

### Testing
- Served on 127.0.0.1:8772, driven with `__chope.step` and autopilot. Four full matches (one started by a real click so the AudioContext ran), zero console errors.
- Screenshots: menu, mid-match with the kill popup, ult-ready at 800x600, end screen.
- Draw calls mid-match: 94 to 269 depending on view and live FX. Geometries 165-171 and textures 26 stayed flat across matches, so no leak.
- M key toggles mute and writes `chope-mute`. Output ASCII only, JS passes `node --check`.

### Known issues
- Characters are 22-28 meshes each. They are the largest draw-call cost now. Instancing them is a bigger job.
- Confetti is one mesh per piece (up to 60 at once on the end screen). Fine in testing, but an InstancedMesh would be cheaper.
- Reduced-motion paths were checked in code only, not with an emulated preference.
- I could not listen to the audio. Mix levels are set by reading, not by ear.

### Challenges for the other agents
- PHYSICS: `animEnt` reads `e.onGround` and `e.vel` for the landing squash. If you change ground detection, keep `onGround` true while standing on table tops, or bots will squash every frame up there.
- PHYSICS: the ragdoll in `physics()` clamps `rotation.x` to +-90 degrees but spins `rotation.z` without limit, so bodies can end up lying through the floor. Give the ragdoll a floor-aware rest pose.
- GAMEPLAY: pick one sustain source to cut (see Disagreements) and say which in the log.
- GAMEPLAY: the end-screen XP shows "+55 XP" on a shutdown popup because a shutdown elim earns 25 plus 30. If you change those values, update the `killConfirm` strings in `kill()` too.

## Pass 1 - Physics and Feel

### What changed
- Projectiles use a swept test. Each step casts the travel segment against walls and the floor with `wallDist`, then finds the closest approach to each body inside that range. Slippers pierce and hit every body on the path. Other projectiles take the earliest hit and stop at the wall face.
- New `moveEnt` helper moves an entity in substeps of at most 0.3m (up to 8). Dash, knockback and ragdolls all use it, so nothing tunnels through stalls or pillars at low fps. `unwall` removes the velocity going into a wall.
- Ground feel: 0.13s jump buffer, 0.1s coyote time, lower air control, a short landing slide after hard falls, and step-up smoothing so stools no longer snap the camera up.
- Ragdolls bounce off walls and the floor. `rotation.z` is clamped to +-0.6 and the pivot lifts as the body tips, so corpses stay out of the floor.
- Bots probe four headings ahead every 0.15s and keep turning one way to stop dithering. When stuck they score 8 headings over 4m, prefer the goal side, and hop. `__chope.stuck` counts stuck events per match.
- Camera: landing dip, strafe tilt, recoil punch, viewmodel sway from mouse motion, dash FOV kick. Under reduced motion the tilt, punch and FOV kick are off and FOV stays at 78.
- Aim: hitscan gains a leg sphere below the chest sphere.
- Mouse sensitivity slider (0.3 to 2.5) on the menu and pause screens, saved as `profile.sens`. `__chope` gained `stuck`, `sens`, `fire()` and `ability()`. All old fields kept.

### Bugs fixed
- Tissue at 15fps passed through a body 10m away every time (0/20 hits). Now 20/20.
- NS Boy dash at dt 0.05 went through the pillar and ended at z -14.58. It now stops at -8.1 at every frame rate tested.
- Rotan Spin knockback could push targets into stall walls. It is now wall-clamped.
- `updateBot` built a new Vector3 each frame for movement and lob aim. `updateDmgs` did the same. Both use scratch vectors now.
- `collide` built and sorted an array per obstacle overlap. Replaced with a min of four values.
- Zone pips: elements are cached and styles are written only when the state changes. This answers the visuals agent's disagreement.

### Answers to challenges
- GAMEPLAY, swept projectiles: done, see above.
- GAMEPLAY, bot unstuck and stool traps: measured before and after (table below). Random sidesteps are gone. Every escape heading is ray-checked.
- GAMEPLAY, dash and Rotan Spin ignoring walls: both go through `moveEnt` now. I kept the Spin numbers (14 out, 7 up). Landing people on tables is fun and reads well.
- VISUALS, onGround on tables: stable. Player and an ally bot on table B for 90 steps showed 0 frames off the ground, and walking off lands at y 0.
- VISUALS, ragdoll `rotation.z`: clamped, see above.

### Disagreements
- No spatial grid. `step()` averages about 0.06ms with 160 boxes, so a broadphase buys nothing yet.
- No fixed timestep. Substeps plus `1-exp(-k*dt)` smoothing already give the same results at 15, 20 and 30fps in the tests. A fixed step would add interpolation code for no measured gain.
- VISUALS: `projTrails` creates a new Mesh every 0.035s per projectile. That is allocation churn in the hot loop. It should pool.

### Measurements (dt 1/30 autopilot, one match per hero)
| Build | Hero | Stuck samples | avg step | p99 | max | Stuck over 3s |
|---|---|---|---|---|---|---|
| before | Ah Ma | 42/749 (5.6%) | .059ms | .4 | 3.9 | 0 |
| before | NS Boy | 55/798 (6.9%) | .051ms | .4 | 1.4 | 0 |
| before | Auntie | 40/712 (5.6%) | .053ms | .4 | 1.0 | 0 |
| after | Ah Ma | 34/753 (4.5%) | .059ms | .3 | 2.4 | 0 |
| after | NS Boy | 28/720 (3.9%) | .055ms | .3 | 1.5 | 0 |
| after | Auntie | 37/706 (5.2%) | .057ms | .3 | 1.1 | 0 |

Totals: 137/2259 (6.1%) stuck before, 99/2179 (4.5%) after. Other checks on the new build: tissue at 15fps 20/20 at 10m and 16/20 at 25m (the misses come from spread), tissue through a pillar 0/10, buffered jump peak 1.61m, coyote jump off a table peak 2.41m, ragdoll flung at a pillar at 20fps stayed in front with mesh y never below 0.42. No console errors. Sensitivity 1.7 saved to the profile and read back.

### Known issues
- A stuck sample still happens about 1 in 22 checks, mostly bots sliding along stool clusters. They escape in under 3s every time.
- Reduced motion was checked in code, not with an emulated preference.
- Ragdolls do not collide with each other or with live characters.

### Challenges for pass 2
- VISUALS: pool the `projTrails` meshes. One new Mesh per projectile every 0.035s is the largest per-frame allocation left.
- GAMEPLAY or VISUALS: `updateHud` runs `$()` lookups and writes `textContent` every frame even when nothing changed. Cache the elements and write on change, like the zone pips.
- GAMEPLAY: the leg hit sphere makes NS Boy more forgiving at close range. Check his time-to-kill against Ah Ma and Auntie and retune if he now wins every duel.
- GAMEPLAY: bots get stuck most near the four-stool tables. If you move zones or add props, keep at least a 1.2m gap between stools so the probes find a way out.

## Pass 2 - Gameplay

### Changes
- Map symmetry fix: the table layout skipped tables by `(i+j)%3`, which is not symmetric through the centre. Team 1 (the player's side) had a different set of lanes to A than team 2 had to C. The right half now mirrors the left half. Only table and stool positions changed. Props, stalls and zones are untouched.
- Sustain: regen nerfed from 8% max HP per second after 4s calm to 5% per second after 6s. Elim heal (+25) and teh peng (80) stay.
- XP values live in one `XP` table. The `killConfirm` popups (+25, +55 shutdown, +10 assist), the challenge text (+100) and the end-screen lines all read from it.
- `updateHud` caches its elements and writes text, styles and classes only when the value changes (`txt`, `sty`, `cls` helpers). The vignette opacity is rounded to 2 decimals so it stops writing every frame.
- Auntie tissue damage 15 to 13. Her blurb said "Grabs tables 50% faster", but capture uses `sqrt(weight)`, so a solo Auntie is 22% faster. The blurb now says 20%.
- First 60 seconds: `#obj` shows "Go chope table X - 14m" toward the nearest table your team does not hold. It shows for the first 15s of every match, and all the time in a player's first 3 games. It stays hidden while you stand in a zone, because the capture readout uses that slot. In the first 2 games a one-line tip explains the goal 2s after the opening callout.
- Reason to press Play again: the end screen gets a `#nextUp` line after the XP count-up, for example "Next match: Get 4 eliminations - Peranakan Teal skin in 485 XP - NS Boy M2 in 135 XP". The next match uses the challenge it names.

### Fixes found in review
- The team 1 win rate was low. Before the symmetry fix, team 1 won 4 of 18 autopilot games. After it, team 1 won 30 of 90 with the player slot on autopilot, and 40 of 90 with the player slot turned into a plain bot (`player.isPlayer=false`). The extra 0.5s player respawn does not explain the rest: cutting it gave 11 of 30. This only affects autopilot runs, so I logged it and left it. Candidates are the Auntie durian lob, which uses the human formula under autopilot, and update order (team 1 ents tick first).
- Nothing broken was found in the visuals or physics changes. There were no console errors across 120+ autopilot matches and a rendered match.

### Challenge answers
- Sustain stacking: I nerfed regen, which was the largest source. Elim heal stays because it is the reward for winning a fight. The pickup stays because it is map play. With the nerf, pickup grabs went from 3.1 to 3.6 per minute (12 to 30 games). The share of alive time below 50% HP went from 21.4% to 22.6%. Bots fight almost nonstop, so regen rarely kicks in for them. A human who backs off will see the bigger change: a full heal from 0 now takes 26s instead of 16.5s.
- Hardcoded XP strings: done, see the `XP` table.
- NS Boy TTK with legs: measured with `__chope.fire()` at 12m with perfect aim. Legs and chest both take 3 shots (1.44s) on NS Boy and Auntie, and 5 shots (2.88s) on Ah Ma. Headshots take 2 shots (0.72s), or 3 on Ah Ma. Perfect-aim TTK for the other heroes: Ah Ma 1.65s on NS Boy, 2.2s on Auntie and 3.3s on Ah Ma (not counting return hits). Auntie, after the nerf, 1.5s on NS Boy, 1.8s on Auntie and 2.85s on Ah Ma. Every matchup sits between 1.4s and 3.3s, and NS Boy has the lowest body DPS (76). The leg sphere only makes his damage consistent. No NS Boy change.
- Stool spacing: stools sit 1.25m from the table centre at 45 degrees, so adjacent stool boxes are 1.29m apart. Stools on neighbouring tables are at least 3.25m apart. Both are above 1.2m. The symmetry fix moved no table closer to a pillar, zone or pickup.
- updateHud churn: done (gameplay took it).

### Measurements (autopilot, 30 games, 10 per hero, after all changes)
- Match length 111-174s. No overtime in this batch. The losing side scored 32-99. Elims are 27.8 per minute across 6 players.
- Elims and damage per hero (both teams): Ah Ma 695 / 147k, NS Boy 654 / 165k, Auntie 711 / 176k. Before the tissue nerf it was 632 / 134k, 671 / 164k and 789 / 195k.
- Draw calls 151 in a match. `stuck` was 36 over 30 games. Sim cost is about 75us per 1/30s step without rendering.

### Disagreements
- Visuals suggested cutting one sustain source outright. I nerfed regen and kept all three, because each one rewards a different action (disengage, win a fight, take the flank). The numbers are above.

### Challenges for pass 3
- VISUALS: the waypoint text and the capture readout share `#obj` under the crosshair. Check that it does not cover targets at 1366x768. If it does, move both a little lower or style the waypoint lighter.
- VISUALS: the end screen now has a `#nextUp` line under the level bar. Give it a style that reads as a teaser without crowding the Play again button on short screens.
- PHYSICS: under autopilot the player slot still loses more (30 of 90 against 40 of 90 as a plain bot). Check whether anything in the movement path differs for `isPlayer` (update order, `updatePlayer` running before `updateBot`, jump buffer). If nothing does, say so and I will chase the durian lob.
- PHYSICS: the table layout changed on the right half (mirrored). Re-run your stuck measurement on the new layout.

## Pass 2 - Visuals and Audio

### Review of physics and gameplay changes
- Camera feel is fine. I left it alone. Landing dip tops out at 0.2m and decays at 9/s. Strafe tilt is about 1 degree at full strafe. Recoil punch is 2 degrees on NS Boy only. Sway is clamped to 0.04. None of it reads as nauseating in play. Reduced motion turns off dip, tilt, punch and FOV kick (code review: `REDUCED` gates in physics() and updateCamera()).
- Objective readout (`#obj`) did cover target legs. At 1366x768 a bot at 15m is about 57px tall, so a dark pill 34px under the crosshair sat on its legs, and legs are hittable since physics pass 1. Moved it to 92px under the crosshair and dropped the box for outlined text. Checked at 1366x768: it now sits under the feet of a mid-range target.
- HUD clutter: OK as is. The only overlap I found was my own mute button sitting on the end-screen TABLES header at 800px wide. Moved it to the bottom right.
- Mirrored layout: overview and lineup screenshots look clean. No table, blob or prop overlaps found.
- No new bugs found in the swept projectiles or substeps from a visual angle. Trails and debris land in the right places.

### Changes
- Characters: each one is now 5 meshes (merged body, 2 legs with shoes, 2 hands with held props) plus ring, shadow and hp bar. Was 22-28. One vertex-coloured Lambert per character, so the hit flash still works through emissive. The flash now covers the whole body, eyes included.
- Hero silhouettes for 30m: Ah Ma gets a bigger white bun and a rotan cane in her left hand. NS Boy gets a taller pack with a bedroll on top. Auntie gets a wider visor and a second market bag, so she is wide on both sides.
- Particle pools: confetti, debris bits (burst, kopi splash) and projectile trails are each one InstancedMesh with per-instance colour. No mesh is created or disposed per particle. Pools are 400 / 500 / 160 and drop the oldest piece when full. Hidden when empty.
- Kill moment (your kills only, so bot fights stay clean): small team-coloured confetti pop at the chest (30 on a shutdown) and a floor shockwave ring.
- Table capture: floor shockwave ring the size of the zone, on top of the confetti and beam flash.
- `#nextUp` styled as a teaser: butter text, left rule, hidden when empty, smaller on screens under 700px tall. At 800x600 it sits clear of Play again.
- Renamed real brands: skin "Bata Blue" is now "Slipper Blue" (id stays `classic`, so saves keep working). Bot "Milo Dino" is now "Chendol Champ".
- Removed the now unused `CM` and `TM` material caches.

### Challenge answers
- Pool projTrails: done, see particle pools.
- Pointer readability: done, lower and boxless.
- Style "Next match": done.
- Cache updateHud writes: gameplay already did it. Checked, no change needed.

### Draw calls (autopilot, sampled every 5s of a full match, `__chope.render()`)
- Before (chope.p2a.html): avg 171, min 79, max 276. Geometries 173.
- After, 4 matches: avg 79-90, min 38-56, max 110-119. Geometries 74-115, no upward trend across 3 back-to-back matches.
- 6 full matches run, no errors. File is pure ASCII and passes `node --check`.

### Not done
- Reduced motion checked by code review only. The browser pane cannot emulate prefers-reduced-motion. The new floor rings still expand under reduced motion. They are slow and do not flash, so I left them.
- No audio changes this pass. The kill and capture sounds already layer well. Visual spectacle was the bigger gap.

### Challenges for pass 3
- PHYSICS: the slipper storm still spawns a full slipper Group per falling slipper (4 every 0.25s for 3.6s). It could move into an instanced pool like the debris. Your call, since `fall` bounces through updateFx.
- PHYSICS: `info.memory.geometries` swings between 74 and 115 at match end. I think that is culling, not a leak, because there is no upward trend. Please confirm with a long soak if you have one.
- GAMEPLAY: the waypoint now sits 92px under the crosshair. Check that new players still notice it in the first 15s. If not, a one-time pulse on first show would help more than moving it back up.
- GAMEPLAY: "Kopitiam Gold" is also the name of a food court chain. Consider a generic name like "Kopi Gold".

## Pass 2 - Physics and Feel

### Fixes
- Geometry leak. buildViewmodel removed the old viewmodel from the camera but never disposed its geometries. Every match left 3-5 behind. It now disposes them.
- Player hand position. muzzle() used camera.localToWorld, so it read last frame's camera. Under __chope.step the camera never moves, so test shots spawned wherever the camera was left. It now builds the same camera-space offset from yaw and pitch. Checked against a YXZ Object3D over 50 random angles: max error 5e-16.

### Changes
- Slipper storm uses a pool. Falling storm slippers are a 4th InstancedMesh pool (PL.slip, 96 max, kind 3). They fall, spin and puff on landing. No mesh is created or disposed per slipper. One storm peaks near 32 alive, two at once near 64.
- rayHit(e,o,dir,max) holds the wall plus head, chest and leg sphere test. hitscan and the new convergence share it.
- Projectile convergence for the human player. Ah Ma and Auntie shots leave the hand but fly to the point under the crosshair (rayHit to 60m, minimum 2m). If a wall sits between eye and hand, the shot starts at the eye. Bots and autopilot are unchanged.

### Review of gameplay pass 2 and visuals pass 2
- Character merge: hit spheres are position based, so the merge cannot move them. Leg sphere, ragdoll (rotates g), squash and stretch (scales body) and the hit flash (emissive on the one material) all still work. freeEnt disposes the merged geometry and material.
- Auntie's outer market bags reach x +-.81. The chest sphere is r .56. A shot that only clips the outer bag misses. Left as is, see challenges.
- Pools: emit drops the oldest item when full, and updatePool sets im.count to the live count, so nothing overflows and no stale instance draws. Each particle still allocates one object and one Vector3. That is GC churn, not a leak.
- Mirrored layout: the skip rule is a correct point mirror. The table test still passes.

### Challenge answers
- Player slot asymmetry. Two samples on p2b. First: autopilot slot 28/90 team wins, same slot as a plain bot 44/90. Second: 12/30 against 11/30. Total 40/120 against 55/120. I listed every isPlayer branch and switched off each one with a sim effect in a test copy: respawn 5s, human Auntie lob, NS Boy .72s cooldown, hitStop, hidden player mesh. With all of them off the slot won 20/60, still low. The remaining branches only touch DOM, sound and camera. No rule I can find explains the gap, and the second sample shows none. At 90 games one standard error is about 7 wins. I am calling it noise until a 300 game run says otherwise.
- Stuck test on the mirrored layout. p2b: 82 stuck samples of 2080 (3.9%). Now: 86 of 1954 (4.4%). No 3s stalls in either. Step time avg .044-.052ms, p99 .3-.4ms.
- Geometry swing. It was a leak. p2b over 40 matches: geometries climbed 34 to 163, about 3.2 per match. Now over 22 matches: 113-126 with no trend. Textures flat at 27 across 3 more matches.

### Disagreements
- Visuals said the 74-115 geometry swing was culling. renderer.info.memory.geometries counts uploaded geometries until they are disposed. Culling does not lower it. The climb came from the viewmodel leak above. The per-match swing that remains comes from projectiles and effects created and freed during play.

### Measurements (chope.html after this pass)
- projTest at 15fps, 20 shots each: Ah Ma 10m 20/20, Auntie 10m 20/20, Auntie 20m 20/20. At 60fps: Ah Ma 4m 20/20, Auntie 3m 20/20.
- Ah Ma at 20m: 0/20. This is correct. The slipper turns home at .5s, so its reach is about 13m. p2b scored 20/20 there only because its stale camera muzzle put the slipper somewhere else.
- Hand inside a pillar (eye clear, target 8m ahead): 10/10 hits for both Ah Ma and Auntie.
- Dash through a wall at dt .05: no pass through. Table test: player and bot get up and off, end at y 0.
- No console errors. Script passes node --check. File is ASCII. Title is on line 1.

### Not done
- No new movement, dash or nav tuning. Stuck time is about 4% with no long stalls. A step costs about .05ms. I did not find a change worth the risk in this pass.
- The test tab crashes when one call runs more than about 30 full matches. Long runs need chunks of 30 or fewer.

### Challenges for pass 3
- Visuals: Auntie's outer bags sit outside her chest sphere. Shrink them inside r .56, or ask physics to add a wider chest sphere for her only.
- Gameplay: if you still see the player slot losing more, run 300 games in chunks of 30 and send the per-hero split. I could not find a cause in code.
- Visuals: the pools still allocate per particle. If a long session shows GC hitches, switch emit to a free list of reused objects.
- Gameplay: Ah Ma's slipper reach is about 13m and bots only throw inside 13m. Check that new players understand the short reach, since the crosshair now converges on targets far beyond it.

## Engine proto (tech art)
- Decision: move from Three.js r128 to r170 (0.170.0) ES modules. Details, look spec, budgets and migration steps in ENGINE.md.
- Added proto-engine/index.html: hawker slice with toon shading, screen-space ink outlines, enemy team-b outline, AO, light shafts, 3 quality tiers. Screenshots in proto-engine/.
- chope.html not touched.

## WP0 - Integrator
Snapshots: chope.pre-wp0.html (r128), chope.wp0.html.
What changed:
- Three.js r128 cdnjs tag replaced by an importmap for three@0.170.0 on jsdelivr and one `<script type="module">`. IIFE wrapper removed. No strict-mode errors surfaced.
- canvasTex() sets SRGBColorSpace (covers signage, sky, floor, HDB, zone label sprite).
- Lights: hemi 0xfff0d2/0x8a6650 at 1.0, sun 0xffe2b8 at 3.4.
- Every MeshLambertMaterial is now MeshToonMaterial with the shared 4-step ramp (M(), VC, floor, HDB, characters, debris pools, durian, teh peng). Hit flash via emissive still works. Durian lost flatShading (toon has no such flag, the icosahedron normals are already flat).
- B() and the teh peng cup set forceSinglePass. r170 otherwise draws transparent DoubleSide meshes twice (+30 calls).
- Layer 1: B() meshes (via fxM()), blob shadows, zone label sprite, all particle pools, transparent teh peng parts. Layer 2: team 2 character meshes, with the nMat enemy flag in onBeforeRender.
- Post module ported from proto-engine: HalfFloat scene RT with depth texture, normal prepass, composite (ink, AO, grade, Chilli enemy outline), FXAA. Tiers Low/Medium/High with pr 1/1/1.5, MSAA 4 on High, shadows on High with the sun camera covering the arena. Shadow map renders in its own pass so drawCalls stays the scene pass.
- Auto tier: starts Medium, drops to Low once if the 120-frame average is over 18 ms (frames over 100 ms and hidden tabs ignored), saved as profile.q. Quality button (Auto/Low/Medium/High) in the menu row and the pause row. `?q=0|1|2` forces a tier for tests and disables the auto drop. No number keys.
- Render targets and resize clamp to at least 1 px (a 0x0 hidden pane gave framebuffer warnings).
- __chope: drawCalls (scene pass only), drawCallsAll, shadowCalls, rev, programs, tier get/set, q, render() runs the full post and returns scene calls, plus renderer/scene/camera refs.
Tests (built-in browser, 127.0.0.1:8792):
- node --check on the module passes. 0 non-ASCII bytes. Zero console messages on load and through matches.
- 15 full autopilot matches across the turn (6 + 3 Low-by-accident + 3 Medium + 2 High + 1 High), all ended with a winner. Same seed gives identical scores and lengths to r128 (48-100, 100-80, 100-79).
- Draw calls, bot match, one sample per simulated second: r128 baseline 43.3 avg / 75 max. WP0 Medium 43.3 / 75 scene, 75 avg / 125 max all passes. High scene 44 / 71, all passes 149 avg.
- Programs after 30 s fresh: Low 16, Medium 16, High 17.
- Step cost 0.085 ms (600 steps). Memory across 4 quit/start cycles: geometries 33-36, textures 19.
- projTest ahma 20/20, auntie 20/20 at 10 m. dashTest no pass-through. tableTest gets off the table. Mute, quality button, end screen and Play again checked.
Known gaps:
- Medium drawCallsAll - drawCalls is about 32, over the WP0 acceptance band of 3-20 (B note in INTEGRATION.md).
- Harness loops that block the main thread for many frames can trip the auto drop. Tests should use ?q=1.
- Switching tiers live leaves stale programs (29 after cycling all three). A fresh load stays at 16-17.

## WP1a - Integrator
Snapshots: chope.pre-wp1a.html, chope.wp1a.html.
What changed:
- HEROES: size, ultCost 200, kit as 5 slots (0 basic, 1-3, 4 ult). Ah Ma Tank, HP 300, speed 6.0, size 1.2. NS Boy HP 150. Existing kits mapped: Ah Ma spin on 2 and storm on 4, NS Boy dash on 1 and Live Firing on 4, Auntie Kopi-O on 2 and Durian on 4.
- Size scaling: radius .45*size, collide height, separate (sum of radii), rayHit spheres, projectile body band and headshot line, eyeOf, chestOf, camera eye height, mesh scale, ragdoll shrink.
- rayHit picks the nearest sphere (head or body) per target. Head-first order called a flat shot at a size 1.2 chin a headshot.
- Status module: slow, buff, dmg, dr, lifesteal, resist, hot as timed lists {m,t,src} (same source refreshes). Snare with 3 s immunity after it ends, no jump while snared. Poison 3 stacks, 3 s timer, 3 per stack every 0.5 s. Shield (cap 150, replace if larger), armour (cap 75), deflect, cleanse. Cleared on spawn and death. Teh peng cleanses.
- Speed formula per HEROES 1.5 with snare x0.25. Knockback clamped to 18 m/s in damage() and again before the move.
- damage(): 7-step pipeline. Buffs cap +25%, DR product floored at 0.5, armour flat cut min(5, 50%), shield then armour then HP. Lifesteal on melee only. DoT ticks that round below 1 are skipped. Ult points 0.12 per point dealt, elim +10, assist +5, 1/s alive, +1/s in a zone the team does not own, none while own ult is active.
- Input: Digit1-3 and Numpad1-3 call tryAbility, Digit4 and Numpad4 call tryUlt (points vs cost). Q and C are stubs that count e.casts.q and e.casts.c (C also sets crouchHeld). Old E and Q handlers removed. Key repeat ignored. Basics locked while castT > 0.
- HUD: #ab1-#ab4 plates with keycaps 1-4, empty slots dimmed, ult plate shows round(points/cost*100)% and READY. Menu hint and hero-select keys updated. One-time "new keys" sub line for returning players (profile.keys14).
- D0.4 stool fix in collide: `top - Math.max(e.pos.y,0) <= .46`.
- __chope hooks per the acceptance.js header: heroes, ability, ult, applyStatus, speedMul, ray, dmg, key, obstacles. Ent fields casts {1,2,3,4,q,c}, poison {stacks,t}, hero. render() now calls updateCamera(0) first (see B note on the draw-call method).
- harness.js: dashTest presses Digit1. H.start turns autopilot off.
Tests (built-in browser, 127.0.0.1:8792, ?q=1):
- node --check passes. 0 non-ASCII bytes. Zero console errors.
- ACC wp1a: PASS 12 FAIL 1 SKIP 0. The FAIL is Numpad1 on Ah Ma, who has no slot 1 in WP1a (runner issue, B note). Numpad1 on NS Boy casts the dash.
- ACC gate with prevDraw 69: PASS 7 FAIL 1. G6 avg 70.2 max 123. G7 0.086 ms/step. G8 proj 20/20, no dash pass-through, table afterWalkY 0. The FAIL is G5 mid-match sampling (86-119 from in-flight FX). Quit plus 2.5 s gives 51-52 geometries flat over 5 cycles.
- Draw calls, seeds 1-3, live camera: pre-wp1a 69.2 / 121, WP1a 70.1 / 126.
- 5 more autopilot matches (ahma, nsboy, auntie, ahma, nsboy) all ended: 83-100, 100-87, 77-100, 95-100, 100-79. Scene 67-70 avg. Earlier in the turn: 6 seeded matches ended, step cost 0.05 ms, stuck 1.3-2.9%.
- Stools stepped onto 8/8 for ahma and nsboy at dt 1/60, 1/30 and 1/20.
- projTest ahma 20/20 at 10 and 13 m, auntie 20/20. dashTest at dt .05 and 1/15 no pass-through.
Known gaps:
- No status VFX, HUD status chips, or shield and armour bar segments (WP6).
- castT is always 0 for the current abilities. No windup cancel yet, there are no basic windups until WP1b melee.
- Pools hold fractions, HP is rounded.
- Auntie 1.5 capture weight still in place (WP1b sets 1.0).
- WP1b not started this turn.

## WP1b - Integrator
Snapshots: chope.pre-wp1b.html, chope.wp1b.html. Edit script: wp1b_edit.py (applied to pre-wp1b).
What changed:
- Roster of 6: ahma, gym, uncle, nsboy, engineer, rascal. Body colours from ART_STYLE, botRange per hero, melee or shot tables per HEROES. Uncle keeps Kopi-O on 2 and Durian on 4. New heroes have empty slots 1-4 until WP2.
- Profile migration: migrate(p) maps auntie to uncle (selected hero and mastery) at load. Skin 'Kopitiam Gold' renamed 'Kopi Gold'. The word auntie is left only inside migrate.
- Melee per HEROES 1.3: windup e.mw, hit check at windup end (arc, edge distance, |dy| < 1.6, wall check chest to chest), cleave, lunge .8 m toward the nearest target in the arc when it sits within range+1.5, move x0.8 during windup. Ah Ma Walker Whack 65, Gym Bro 46. Melee hits deployables.
- Shooters use a generic shot table (tissue, dart, shuriken) with projectile radius p.r and head multiplier p.head. NS Boy hitscan unchanged.
- Deployables per HEROES 1.8: wall 4.5 x 2.2 x 0.4 perpendicular to aim, gum, vest, turret. HP, life, per-owner cap (oldest replaced), dormant flag, vest pickup (+50 armour to 75, enemy within 1.2 m destroys it). Blocks movement, rays, projectiles and explosions. Cleared on start, end and quit.
- Random comps (R12) each match. __chope.comp sets a one-shot override.
- Bots: melee bots close in under 6 m and orbit at 1.8 m. Lead uses shot speed. Fire range from botRange. Zone capture weight 1 for everyone.
- Hooks: comp (get/set), deploy(kind,team,x,z), deployables, migrate.
Tests (built-in browser, 127.0.0.1:8792, ?q=1):
- node --check passes. 0 non-ASCII bytes. Zero console errors.
- ACC wp1b: PASS 6, FAIL 0, MANUAL 2. Migration ok, 50 comps 0 bad, all 6 heroes seen, override ok, melee ahead 65, 60 deg 0, cleave 65/65, lunge 0.80, deployables all true, 2/2 bot matches ended.
- ACC gate (prevDraw 69): PASS 7, FAIL 1. G5 flat at 75/32 over 3 cycles. G6 62.5 avg, 111 max. G7 0.030 ms/step. G8 FAIL is projTest('ahma') 0/20 because Ah Ma is melee now (B note).
- ACC wp1a: 13/13 PASS. wp0: all pass except the same projTest('ahma').
- projTest: uncle 19-20/20, engineer 20/20, rascal 20/20, nsboy 20/20.
- 6 autopilot matches, one per hero, all ended: 100-89, 92-100, 100-54, 90-100, 76-100, 81-100. Stuck 1.25-2.5 percent, long3 0 (pre-wp1b 1.69-3.17 percent).
- Melee test logic repeated by hand: 19/20 exact. The miss came from live enemy bots (B note).
- Deployed wall stops the player 0.45 m from its face. Melee does not reach a target behind a wall.
Known gaps:
- Gum trap effects, turret firing and vest throw (WP2).
- Abilities and ults for gym, engineer, rascal. Uncle Booger Bomb (WP2).
- Placeholder markers for new hero models (WP4). Enemy rim and TEAM_COL per C1 not done.
- Old slipper projectile code is still in updateProjs, unused.
- WP2a not started this turn.

## WP2a - Integrator
Snapshots: chope.pre-wp2a.html (= chope.wp1b.html), chope.wp2a.html.

Changes
- Ah Ma: Excuse Me Charge (1): .6 s windup with a 9 m plum arrow decal, then 13 m/s for .7 s, turns 90 deg/s toward aim, ignores slows and knockback. First enemy within 1 m takes 90 and knockback 10 out, 4 up. A wall gives a .6 s stumble with no damage. A snare in the windup or the run ends it.
- Ah Ma: Rotan Spin to cd 8, 40 dmg, knockback 8/5, 30% slow 1.5 s. Medicated Oil (3): cd 15, .4 s cast, hot 20 for 5 s. Passive: 20% DR from attackers within 5 m (inside the .5 DR floor), 15% melee lifesteal.
- Uncle: tissue and Kopi-O removed. Booger Bomb LMB (22 m/s + 3 up, gravity, .8 s cycle, 2 m splash 32 to 19.2, 1 poison stack, 20% slow 1.5 s). Kopi Gao (1), Gum Trap (2, aim point up to 8 m, arms .8 s, 10 dmg, snare 1.25 s then 30% slow 1.5 s, consumed, enemy player sees it within 12 m). Singlet Flap (3, 6.5 m cone, 50 deg half angle, 25 dmg, knockback 9/3, 30% slow 2 s, 1 poison stack). Durian shows a landing circle while in flight.
- NS Boy: dash cd 5. Water Parade (2): cd 14, hot 20 for 3 s, +15% speed 4 s. Matador Strike (3): cd 10, .35 s windup, 3 rockets in a 6 deg fan at 24 m/s, 2 m splash 30 to 15, knockback 5, no self damage.
- Shared splash(): distance to the body segment, walls block, linear falloff. Durian, booger and rocket use it through a p.boom callback. Slipper and tissue projectile code removed. Projectile meshes pooled per type (shared geometry, free list).
- Pending casts: cast(e,t,fn) locks basics and fires fn when castT runs out. Windups of .3 s or more show a floor decal (ring, or an arrow for the charge). The .35 s melee windup shows the ring too.
- Voice lines in HEROES.lines, shown as subtitles on player casts, ults and kills.
- Bot kit rules per HEROES 2.1 to 2.3 in botKit(): charge with a clear path at 5-9 m, spin, oil, Kopi, gum at the zone or on a melee diver, flap, Water Parade, Matador at 6-25 m, NS Boy ult only within 30 m. Booger bots aim with a lob solved at 22 m/s across.
- D1b.1: bot unstick hop now fires only with a wall ahead or after 2 checks in a row with no progress, and never while casting, stunned, in a melee windup or slowed below 50%.

Tests (127.0.0.1:8792, ?q=1, zero console errors, ASCII clean, node --check ok)
- ACC wp2a: PASS 2, MANUAL 1. DR 4 m 80, 6 m 100. Cast coverage per match: ahma 7.5/9/7/2, uncle 5.5/6/10/2, nsboy 9.5/5.5/11.5/1.
- Manual (wp2a_manual run): charge at 5 m 90. Charge into a wall 3 m ahead: .6 s stumble, 0 dmg, stops at x -23.74. Snare mid-run ends it. Lifesteal 9.75 on 65. Booger 3 hits give stacks 1/2/3 and 18 poison dps. Gum: snare 1.25, speed x.25 while snared, x.7 after, 1.0 at the end. Gum hidden at 13 m, visible at 11 m. Durian 101 near centre (the lob meets the body side, about .4 m out), 45 at 4.9 m. Matador 53 on a target at 10 m, 0 self damage at a wall.
- ACC gate 8/8. wp1a 13/13. wp0 5 PASS, 1 MANUAL. wp1b 7/8: the cleave test fails when an enemy is an Ah Ma (B note).
- Autopilot matches, 15 in total over three runs, all ended. Last run of 9: unstick hops 0-3 per match (WP1b: 12-27). Harness stuck 1.6-4.0 percent, long3 0-1. Step cost .03-.04 ms. Max draw calls 118-122 during matches.

Known gaps
- Bots do not sidestep enemy windup decals yet (WP3). Status VFX on bodies come in WP6.
- Ah Ma Slipper Storm keeps its WP1 radius. The 7.5 m storm ring visual is not added.
- Durian landing circle ignores walls and tables (lands on the floor plane).
- Gum visibility is per local player only. Bots always know where gum is.

## WP2b - Integrator

Engineer Encik kit, deployable pooling (D1b.2), restart fix.

- Engineer slots. 1 Road Closed! wall (cd 13, .3 s cast, 3 m ahead, 4.5 x 2.2 x .4, 350 HP). 2 Ping Pong Turret (cd 7, .5 s cast, aimed up to 6 m, cap 3, refused within 4 m of his other turrets). 3 Safety Vest throw (cd 10, .2 s cast, aimed up to 12 m, arcs at 8 m/s, +50 armour to cap 75, an enemy walking over it denies it). 4 Claim OT! (7 s).
- Turret: builds 1.5 s from 50 HP, range 16 m with chest line of sight, .4 s acquire, 9 dmg ball every .6 s at 40 m/s. Balls live R/40 s, so nothing lands past range. A ball on an armoured target removes 4.5 armour. Dormant while the owner is dead.
- Deployables placed on a table or stool sit on its top. The turret muzzle is .8 m above that.
- Claim OT!: every turret goes to full HP and finishes building. With no turret, one drops at his feet. While active: fire every .2 s, range 24 m, turrets take 25% less damage, overdrive balls give no ult charge. Body turns lime in overdrive, red with a target, grey idle.
- D1b.2: deployables come from a per-kind pool of Groups. Team rings are one InstancedMesh per team, so each deployable costs one draw call.
- Fix: restart and quit freed live projectiles back to the pool. WP2a removed pooled meshes from the scene, which leaked them.
- Bots: turret near the contested zone edge (2/s out of combat, .5/s in), wall below half HP against a ranged enemy past 8 m or against a charge, run or Gym ult within 10 m, vest for a 0 armour calm ally in 10 m or self under 25 armour, ult with 2 turrets near an enemy or a turret by a contested zone.

Tests (127.0.0.1:8792, ?q=1, zero console errors, ASCII clean)
- ACC wp2b: PASS 3, MANUAL 1. Turret 13.5 dps at 15 m, 0 at 17 m. Cast coverage per match: 4/12.5/14.5/2.
- Manual: vest 0 to 50, 40 to 75, enemy deny leaves armour 0 and removes the vest. Ball armour 36.5 to 32, 0 HP. OT: ult true, turret 10 to 100 HP, 11 hits in 3 s at 20 m, .2 s gaps, owner ult stays 0, 20 dmg on turret reads 15. After OT: 0 hits at 20 m, 20 dmg reads 20. Booger at a wall with the target .7 m behind: 0 dmg (38 without the wall).
- Draw calls with 3 turrets, 2 vests and a wall: main pass +7 (38 to 45), all passes +13. Before the ring instancing it was +12.
- Bot turret rate: 4 matches, 2 engineers each, 16 lives over 20 s, 16 placed a turret.
- ACC gate 8/8, wp0 5 PASS 1 MANUAL, wp1a 13/13, wp1b 8/8, wp2a 2 PASS 1 MANUAL.
- 5 bot matches with an engineer per team: all ended, unstick 0-4, max draw calls 126-143, no errors.

Known gaps
- Turret has no turn rate, LED, siren, exhaust or rim yet (WP4 art).
- D1b.3 vest walk-over left as is until A rules.

## WP2b follow-ups (A review R34 to R37)
- R35: Durian splash has a 0.75 m full-damage radius. Direct hits read 110 at 6 m and 10 m. Body-segment distance still applies outside it.
- R37 vest walk-over checked. An ally at 75 armour leaves the vest. An enemy destroys it and gains 0 armour and no ult beyond the passive per-frame gain (+0.10). A dead enemy does not trigger it.
- R36: added `__chope.stuckLog` (hero, x, y, z, match time, check count per unstick hop). Diagnostic only.

## WP2c - Integrator
Gym Kor Kor and Recess Rascal kits, lines and bot rules.

Acceptance (fresh tests/acceptance.js)
- gate PASS 6. wp0 PASS 5, MANUAL 1. wp1a PASS 13. wp1b PASS 8. wp2a PASS 2, MANUAL 1. wp2b PASS 3, MANUAL 1. wp2c PASS 2, MANUAL 1. Console errors 0. node --check OK.
- Casts per 2 matches: gym 28/20/26/4, rascal 37/24/26/5.

Manual checks
- Sandbag Brace: 120 hit on 250 HP leaves 230. Shield 100 at 2.97 s, 0 at 3.0 s.
- Personal Best: speed 1.20 under a 0.5 slow, snare refused, Med Ball 46 to 58, model scale 1.155.
- Battle Rope Slam: 80 at 7.5 m, 0 at 90 deg, 0 at 8.8 m. Sector decal shows during the 0.7 s windup.
- Run the 1K: speed 1.5, 1.20 under a 0.5 slow, heal 50.6 over 3 s.
- Exercise Book Block: frontal hitscan returns to the shooter (NS Boy took 55, Rascal 0). From behind Rascal takes 55. Durian into the front is destroyed. Med Ball, rope slam and Engineer dart into the front deal 0, the dart returns 50 to the Engineer.
- Recess Dash: 8.76 m, 40 to the first enemy only. KO resets cd1 to 0. A second KO 1 s later does not (4.09). Ally KO resets at 1.5 s after Rascal's hit, not at 2.5 s.
- PSLE: rooted during the 1 s charge, dash ends 12 m out, 160 at 1.3 m lateral, 0 at 1.6 m. KO during the charge refunds 50% (ult 120.33).

R36 unstick hops (bot matches, 3v3 with gym and rascal)
- 18 matches in three runs: 2,2,6,4,1,2 then 0,2,2,6 then 4,1,4,5,1,3,2,2. 8 of 18 read 3 or more. The last run had a trial rule that ignored hops with another body within 1.4 m. It did not help and was reverted.
- Hot spots: the two pillar and table clusters near (-11..-13, 7.5..10) and the mirror (10.5..12.5, -7.5..-12), every hero type. A few hops in open floor near the centre come from two bots body-blocking each other in melee.
- Not fixed in WP2c. Stools are 0.44 m solid boxes and bots catch on them next to the pillar. Logged for A per R36.

Known gaps
- Visual props not built: exercise book mesh, ropes, sandbag, sweat, PSLE whistle (WP4 art).

## WPM - Integrator
Quick melee on Q, crouch and slide on C, ported from proto-move. Also R38 feet-relative step-up and the `__chope.onDamage` hook.

What changed
- QM, SL and MV tables from MOVEMENT.md. Q is one nearest target, checked once at the end of windup, through the melee pipeline (book deflect blocks it). Q cancels a basic windup and adds 0.25 s to the basic cycle. Abilities and the ult wait out Q windup and active, and cancel recovery.
- C held while slow gives crouch (0.5 speed, eye 1.10 x size). C pressed at 0.75 x base speed or more on the ground gives a slide. Slide ends on time, release after 0.25 s, jump (keeps speed as air carry), ledge, wall bonk (0.25 s stumble), snare, dash, charge or any cast.
- Eye height is stored per metre of size (eyeR), so `e.eye` follows size changes. Head, chest and leg spheres, projectile bands and splash tops scale with it.
- Third person: crouch hip drop and leg split, slide lean with the lead leg out, Q poses from MOVEMENT 8.1 mapped onto the hands. First person: VMK viewmodel keys, CAMQ camera punch, slide roll and FOV kick, crouch bob. All camera motion is off under reduced motion.
- New SFX: whoosh, slide, bonk and six Q hit sounds. Slide dust is one pooled InstancedMesh (PL.dust).
- Hooks: key(code,down), hitSpheres, slideDist, melee(), QM, SL, MV, onDamage (get and set).
- R38: step-up is measured from the feet (top minus feet 0.46 m or less).

Tests (private tab, ?q=1)
- ACC wpm PASS 5, MANUAL 1, five runs in a row. gate PASS 8 (G6 avg 68.3, G7 0.044 ms). wp0 to wp2c: no FAIL. Console errors 0. node --check OK. ASCII only.
- Proto runTests ported as a scratch script (scratch/wpm_proto.js, outside tests/): 66 of 66 pass. It covers crouch eye and head sphere per hero, crouch walk, slide entry speed, time and distance per hero, NS Boy slide at 15, 30 and 120 fps, cooldown, tap, slow 30/20, snare, jump carry, wall bonk, stool 0.85, NS Boy reach and arc, wall block, each hero Q damage, Uncle Q cooldown, Gym lunge, Ah Ma knockback and the basic tax.
- R38: walking at 15 fps over a 0.44 m stool, and from that stool onto a box 0.44 m higher, both pass.
- BAL 30 bot matches: stuck 0.43 per match (max 3 in one match), step cost 0.054 ms. Hot spots (3 m cells): (-12, 9) 5 hops, the rest 1 each.

## WP3 - Integrator
Bot aim, bot movement and goal pick (INTEGRATION.md WP3, MOVEMENT.md section 7).
- botAim: reaction delay rand(.15,.25)/skill on each new target, error disc R=(.6+.017d)/skill re-rolled every .35 s, 25% head aim for NS Boy and Engineer, projectile lead at .9, lob solvers aim at the aim point. Fire gate uses the miss distance.
- Removed the old NS Boy bot spread. Per-band shot and hit counters (stats.shots, stats.hits) through SHOT in hitscan, projectiles and melee.
- threat(): decal dodge on arrow, ring and rope telegraphs, sideways toward the open side, 50% as a slide.
- botMoves: delayed decision queue, Q checks, crouch at range, escape, gap-close and travel slides, jump-out of a held crouch.
- Goal pick in one function (pickZone) with a pickup override when low. Target hysteresis 2 m. Deployable targets (turret, gum, blocking wall).
- Ult fallback after 6 s held ready. __chope.botSkill hook for skill sweeps.
Tests (private tab, ?q=2)
- ACC runAll: gate to wp3 no FAIL (wp3 stuck 0.00, step 0.044 ms). FAILs only in wp4 and wp6, not started. Console errors 0. node --check OK. ASCII only.
- BAL 60 matches: hit rate <8 m 54.3, 8-20 m 40.9, >20 m 32. Melee swing hit 75.3%, melee median 2.33 m. Decal dodge 41.2%. Stuck 0.6 per match. Slides blocked 0 of 5354.
- Marginal: elims per minute 21.9 (target 22), median length 167.4 s (target 165). Ults per life: Ah Ma 1.95, Gym 1.98 (target 2), others 2.07 to 2.53.
- Skill sweep 1.3 vs 0.7: team 1 wins 73.3% of 60.
- duels(10): about 20 cells outside 15-85%. Pre-WP3 file gives 20 such cells too, so this is hero balance for WP7.

## WP4a - Integrator
Hero models from proto-models/models.js (INTEGRATION.md WP4, ART_STYLE 7).
- models.js ported as is inside a MODELS closure. Exports stripped, its own ramp dropped for the chope ramp. mergeGeometries imported from three/addons r170.
- makeMesh calls MODELS.BUILDERS[hk]({team}). All six heroes are wired, since the port came prebuilt. Default skins. Uncle's cloud on layer 1.
- Ring, shadow and HP bar moved to 4 shared InstancedMeshes (R2), filled each frame by syncEntFx with a camera frustum test. Old per-ent bar code removed.
- animEnt drives h.update with idle, walk or attack. Squash, hip drop, lean, crouch and slide legs and Q-pose arm deltas go on top of the model rig. Faces: 2 hurt, 3 ult, 4 down, restored when the override ends.
- buildViewmodel is unchanged (WP4b).
Tests (private tab, ?q=1)
- ACC runAll: wp4 meshes, tris and one material PASS for all six. Heights PASS (ahma 2.34, nsboy 1.90, gym 2.02, uncle 1.82, rascal 1.52). Colour rule: only TEAM itself is near a team hue.
- FAILs: wp6 (not started), plus three flakes that also show on chope.wp3.html: G8 projectile, wp1b Ah Ma lunge (0.52 or 0.80), wp2b turret dps at 15 m (3 to 13.5).
- Console errors 0 (in-page counter over a full runAll). node --check OK. ASCII only.
- Draw calls, 3v3 match ?q=1: WP3 about 66.6, WP4a about 62.2. Five heroes in view: 45 calls before, 33 after.

## WP4b - Integrator
Viewmodels from proto-models/viewmodels.js, plus an audio guard.
- viewmodels.js ported as is inside a VIEWMODELS closure, using MODELS.KIT, TEAM and SKINS. Its QM, VMK and qBlend stay local.
- buildViewmodel builds VIEWMODELS[hk] and adds its group to the camera. The proto rig does bob, crouch, slide, Q and basic anims. The game adds only mouse sway and landing dip on the group.
- Basic attacks call fire(), Q start calls melee(). The old kick offset on the viewmodel is gone. vmKick still drives the NS Boy camera kick.
- Audio: tone, noise and voice return early on any non-finite value. sfxAt skips a NaN distance.
Tests (private tab, ?q=1)
- Viewmodels: ahma 1 mesh 1112 tris, uncle 3/920, nsboy 3/936, engineer 3/928, gym 2/1092, rascal 3/864, one material each. Geometry count steady across 6 restarts.
- ACC runAll: 52 PASS, FAIL only wp6. G6 avg 62.1. Console errors 0. node --check OK. ASCII only.

## WP5 - Integrator
- Ported proto-env/env.js into chope.html as the ENV closure. The scene now uses env.group for all static hawker visuals.
- The old arena code is collider-only now: obstacles, addBox, zones, spawn mats, table colliders, zone visuals. Removed the old floor, grass, HDB blocks, stall meshes, signs, trays, tubes, fans, glow and blob meshes.
- Frame loop calls env.update(dt) in place of the old fan spin.
- Fonts: Alfa Slab One and Barlow Condensed in one link, Noto Serif SC in a separate link with the HAN_TEXT subset. The env build waits for both stylesheets (2 s cap) so its canvas text draws in the right fonts.
- Background colour is 0xf3dcc2 to match the env sky.
Tests (private tab, ?q=1)
- Colliders 148, zero diff against proto-env/obstacles.json.
- env group 13 draw calls, 44082 tris. Renderer memory 18 textures, 57 geometries, 21 programs. Scene pass about 63k tris.
- Fonts: all five families report loaded.
- ACC runAll: 52 PASS, FAIL only wp6. G6 avg 53.3 max 93 (was 62.1). wp7 sample draw 57.6. Errors 0.
- BAL.sweep(20): stuck per match 0.4, max 1. H.tableTest: off-ground 0 for player and bot.
- Screenshots at 2 points: trusses, fans, pillars, stalls and shafts show, no crease flicker. Frame time not measured (MANUAL).
- node --check OK. ASCII only.

## WP6 - Integrator
- Ported hud.js as the HUD closure and appended hud.css as-is (scoped under .chud). The old HUD, damage numbers, XP bar and end screen are gone.
- Team colours are Stool Blue 0x1aa3e8 and Chilli Padi 0xff5a1f. Menu and hero select restyled with the hud.css tokens and fonts (Alfa Slab One, Barlow, Noto Sans SC for han).
- Hero cards show the HDB field colour, the han character and a line naming Q and C. New menu tagline. Controls legend reads 1 2 3 abilities, 4 ult, Q quick melee, C crouch/slide (R9d).
- Bot skill button (Easy 0.7, Normal 1, Hard 1.3) on menu and pause. Stored in profile.bots. Enemy team only.
- Status badges by edge detection, cooldown totals, Engineer counts, ult meter, challenge chit, kill feed with weapon names, capture ring and pips, end receipt with kopi card stamps (10 per level).
- Hidden #changeBtn kept as a harness hook. Compact feed width override under 900x640.
- ACC runAll at 800x600: 54 PASS, 0 FAIL, 10 MANUAL. At 1366x768: wp7 sample failed once on variance (203 s), passed on rerun (174, 164). Errors 0.
- BAL.sweep(12): length avg 152.9 (123-178), step cost 0.059 ms. HUD on vs off about 0.01 ms.
- Screenshots checked: HUD, menu, hero select, end screen at 1366x768 and 800x600. No horizontal scroll.
- node --check OK. ASCII only.

## WP7 - Integrator
A's T1 to T11 applied in order, one number per pass. Each pass: BAL.sweep(30) x4 (120 matches) plus BAL.weave. Final: 300 matches, BAL.duels(50), BAL.slide.

| Pass | Change | Median s | Elims/min | Ah Ma | Gym | Uncle | NS Boy | Eng | Rascal |
|---|---|---|---|---|---|---|---|---|---|
| P0 | baseline | 165.7 | 22.2 | 36.2 | 38.3 | 46.2 | 66.7 | 73.3 | 39.3 |
| T1 | PTS .45 to .495 | 148.4 | 22.3 | 43.9 | 28.8 | 38.9 | 68.7 | 77.6 | 34.4 |
| T2 | dart cd .95 to 1.05 | 150.1 | 21.8 | 38.3 | 28.8 | 49.2 | 69.5 | 75 | 34.7 |
| T3 | NS Boy cdP .72/1.05 to .79/1.15 | 148.7 | 21.4 | 33.9 | 42.4 | 46.2 | 66.1 | 68.7 | 40.9 |
| T4 | turret fire .6 to .54 | 148.2 | 21.5 | 42.2 | 44.6 | 33.9 | 56.8 | 78.5 | 40.6 |
| T5 | Ah Ma cd2 8 to 7.2 | 152.7 | 21.5 | 45.6 | 42.4 | 40 | 62.3 | 68.8 | 39.3 |
| T6a | Rascal block cd 8 to 7.2 | 151.9 | 21.4 | 46.9 | 40.9 | 43.1 | 62.1 | 70.8 | 35.7 |
| T6b | Rascal hp 125 to 137 | 152.9 | 21.1 | 46.3 | 36.4 | 40.7 | 58 | 73.6 | 47.4 |
| T7 | Uncle cd1 12 to 10.8 | 155.1 | 21.3 | 40 | 38.1 | 44.6 | 59.7 | 67.9 | 48.2 |
| T8a | ult cost -10%, all six | 151.6 | 21.5 | 50.9 | 40.7 | 35.4 | 63.2 | 70.5 | 36.9 |
| T8b | passive ult gain x1.1 | 152.6 | 21.5 | 43.3 | 40.7 | 40.4 | 62.7 | 75.9 | 39.1 |
| T9a | Stock Poke 30 to 27 | 151.4 | 21.4 | 41.1 | 32.8 | 41.4 | 65.5 | 81.3 | 35.8 |
| T9b | Stock Poke 27 to 24.5 | 156.3 | 21.5 | 41.8 | 35.4 | 47.5 | 65.3 | 77.8 | 27.6 |
| T10 | Rascal block botKit | 151.2 | 21.4 | 47 | 39.7 | 47.3 | 55.1 | 75.9 | 38.7 |
| T11 | basic cds -5% | 150.5 | 21.6 | 25.4 | 45.2 | 55.4 | 67.8 | 75 | 31.1 |
| Final | 300 matches | 153.1 | 21.8 | 34.7 | 42.5 | 49.3 | 64.4 | 68.5 | 41.1 |

- Win% per hero at 120 matches carries about +-6 points of noise (about 60 appearances each).
- Final ults per match: 1.89 2.03 2.89 2.46 1.93 2.32. Turret share 12.4% (R43 band 10 to 30, in). Rascal returned 53.4 (band 100 to 400, OUT). Ah Ma close 49% (ok). Stuck 0.4 per match.
- Weave: NS Boy +18.9% at T3, +14.7% at T9a, +11.9% at T9b, +3.9% after T11 (ok). Gym -16.6% (ok).
- Duels(50), R43 split. Melee is Ah Ma and Gym. Like-vs-like OUT: ahma>gym 95.8. Ranged OUT: uncle>nsboy 18, uncle>engineer 18.4, nsboy>uncle 78, nsboy>engineer 16.3, engineer mirror 20.7, rascal>nsboy 10, rascal>engineer 12.2. Gate fails.
- Slide R24 ok. Elims 21.8 stays under the 22 floor. Avg length 152.1 is in band, median 153.1 in band.
- Step cost 0.156 in the final run, 0.105 to 0.112 in the per-pass runs. The final run was polled while hidden. Treat as noise until a visible-pane read.
- The 600-match run (x20 plus duels in one load) crashed the tab. Done as 300 sweep plus a separate duels load.
- ACC runAll (fresh acceptance.js) at 1366x768: 51 PASS, 3 FAIL, 10 MANUAL, errors 0.
  - R20 pass overhead: tier 0 diff 14.1. Same fail on chope.wp6.html (diff 14.7) in this pane. Pre-existing, not WP7.
  - G3 autopilot: feed 0 once (score 9-62). Rerun PASS (feed 3).
  - wp1a ult points: idle 11.04, want 10. Caused by T8 step two (passive gain x1.1), which A ruled. The test needs A's update.
- First ACC run at the hidden pane size (421x311) also failed wp6 HUD overlap. It passes at 1366x768.

## WP7b - Integrator
- Q hit cue: 0.04 s hit stop and a 4 deg FOV dip on a landed quick melee.
- Ult camera moment (player): shake .35, 6 deg FOV dip for .3 s, vignette in the hero body colour for .4 s. Rascal PSLE fires the banner and SFX on the dash, not on the key press.
- Stat-only ult cues: NS Boy live tracers in 0xffe600. Gym ult ring pulse every .6 s. Engineer ult ring and burst on each turret.
- Rascal block: voice line plus clink SFX.
- Spawn clip: up to 8 rerolls to keep 1.6 m from live teammates.
- End screen: keyboard focus moves to Play again.
- Bug found while testing: a pointer-lock rejection that arrived after the match ended called resume() and hid the end screen. resume() now runs from that path only while playing.
- D5.1: floor, zinc, pillars, tiles, tabletops, signs and menus get white vertex colours and vertexColors, so they share the hdb toon program. Tier 2 fresh load: 19 programs. Six heroes in one page: 23 to 25.
- D6.1: Play row sticky at the bottom. Hero grid 2 columns under 900 px, 1 under 520 px. Play at y 638 (1366x768) and y 412 (800x600). No horizontal scroll.
- D6.2: `.chud table{color:inherit;font:inherit}`. End table digits rgb(28,21,18) on cream in quirks mode and with a doctype (checked with a temp doctype copy).
- D6.3: logo padding-top .3em. The .08em in the brief still clipped the rotated glyphs.
- D6.4: names stay on one line (33 px), role chip does not shrink.
- D4b.1: Engineer tool rifle in navy and lime boxes. Rest moved from [.20,-.22,-.42] to [.24,-.28,-.48] so it no longer fills the lower right.
- D4b.2: Gym ball radius .17 to .12, rest [0,-.37,-.58].
- D4b.3: NS Boy rest [.22,-.27,-.46] to [.25,-.32,-.50].
- ACC runAll at 1366x768: 52 PASS, 2 FAIL (R20 tier 0 and wp1a idle ult, both known from WP7), 10 MANUAL, errors 0.
- BAL.sweep(30) x2: median 153.9, elims 21.6, stuck .47, step .094. In line with WP7.
- Screenshots: menu at 1366x768 and 800x600, end screen at 800x600, Engineer, NS Boy and Gym viewmodels at 800x600.
- node --check OK. ASCII only.

## WP7c - Integrator
T12 to T17 and T8c in one build (chope.pre-wp7c.html to chope.wp7c.html), plus D7b.1. Measured once: BAL.sweep(30) x10, BAL.duels(50), BAL.weave, BAL.slide. T18: only the Engineer condition held, then BAL.sweep(30) x4.

| Pass | Change | Median s | Elims/min | Ah Ma | Gym | Uncle | NS Boy | Eng | Rascal |
|---|---|---|---|---|---|---|---|---|---|
| Start | WP7 final, 300 matches | 153.1 | 21.8 | 34.7 | 42.5 | 49.3 | 64.4 | 68.5 | 41.1 |
| T12-T17 + T8c | one build, 300 matches | 155.4 | 22.8 | 42.9 | 35.2 | 50.3 | 55.8 | 66.7 | 49.3 |
| T18 | dart cd 1.0 to 1.1, 120 matches | 158.5 | 22.7 | 48.5 | 35.7 | 51.8 | 50.9 | 67.3 | 46.7 |

- Changes: dart dmg 50 to 44. Rifle 55 to 49. Ah Ma speed 6.6, Charge cd1 8.5. Med Ball 54. Respawn 4.0 bots, 4.5 player. Ult cost 145, 150, 180, 170, 170, 185 (Ah Ma, Gym, Uncle, NS Boy, Eng, Rascal).
- T16: the deflect branch in damage() returns the blocked hit to a live hero at full amount, weapon 'deflect', with no melee flag. Rascal botKit raises Block on an enemy within 3.5 m facing him with mw above 0, or a rope cast within 8 m.
- T18 checks on the 300 run: Rascal 49.3 (not under 45, no change). Engineer 66.7 (over 60, applied). Elims 22.8 (not under 22, no change).
- Ults per match (300 run): 2.44 2.55 2.9 2.63 2.16 3.0. After T18: 2.5 2.62 3.03 2.63 2.08 3.02. Engineer stays under 2.5. Charge 38.6 to 51 s.
- Rascal returned 246.6 per match (band 100 to 400, ok). Turret share 15.2%, 16.6% after T18. Both are just over the 15% R43 fallback line, so the 20 to 40 band applies and it reads OUT. Ah Ma close 51.3% ok. Stuck 0.36 per match.
- Match length median 155.4 and 158.5, over the 140 to 155 band. Avg 153 and 156.2. Respawn cuts and Ah Ma reach lengthened matches by 2 to 5 s.
- Pairs out (300 run): Engineer with Rascal, Uncle or NS Boy at 63 to 65%. Ah Ma plus Gym 32.3%.
- Duels(50), R44 pooled: like-vs-like OUT only Ah Ma over Gym 90% (was 96%). NS Boy over Uncle is back in band. Mirrors: Engineer 17.9% side bias, report only.
- Weave R23: NS Boy +7.9% (OUT, limit 5). The rifle cut made Stock Poke a bigger share. Gym -22.9% ok. Slide R24 ok.
- Step cost 0.136 and 0.120 ms.
- D7b.1: the controls legend moved out of the sticky row. Under 700 px tall the row stays on one line with a smaller Play button and chips. At 800x600 the row is 59 px tall (one line), and the first card names end at y 422 against a row top of 514.
- ACC runAll (fresh acceptance.js) at 1366x768: PASS 54, FAIL 0, SKIP 0, MANUAL 10. At 800x600: PASS 54, FAIL 0, SKIP 0, MANUAL 10. G4 errors 0 at both sizes.

## WP7d - Integrator
Coordinator round, no further tuning after the measure. chope.pre-wp7d.html (same as chope.wp7c.html) to chope.wp7d.html.
- Turret fire interval .54 back to .6 (T4 reverted). Turret ball dmg 9 to 7.65 (minus 15%). Dart cd stays 1.1.
- Gym hp 250 to 275. Stock Poke 24.5 to 22.
- Measured: BAL.sweep(30) x10 over two loads, merged for the summary. BAL.duels(50), weave and slide ran on separate loads. One load with 300 matches plus duels crashed the tab.

| Pass | Change | Median s | Elims/min | Ah Ma | Gym | Uncle | NS Boy | Eng | Rascal |
|---|---|---|---|---|---|---|---|---|---|
| WP7c T18 | 120 matches | 158.5 | 22.7 | 48.5 | 35.7 | 51.8 | 50.9 | 67.3 | 46.7 |
| WP7d | 300 matches | 157.8 | 22.5 | 39.5 | 41.3 | 50.3 | 67.7 | 53.8 | 47.5 |

- Ults per match: 2.54 2.71 2.99 2.58 2.1 3.1. Engineer is under 2.5 (charge 54.1 s).
- Turret share 13.6%, under 15%, so the R43 fallback band 10 to 30 applies (ok). Rascal returned 246.9 (ok). Ah Ma close 54.1% (ok). Stuck 0.36, 3 matches with 3+ hops. Step 0.126 ms. Median 157.8 is in the R46 band of 140 to 160. Avg 156.5.
- Pairs out: Engineer plus NS Boy 71.4%, NS Boy plus Rascal 62.1%, Ah Ma plus Gym 32.3%, Gym plus Rascal 39.5%.
- Duels(50) pooled: like-vs-like OUT only Ah Ma over Gym 89%. Engineer mirror 4.3% side bias (report only).
- Weave R23: NS Boy +3.5% ok, Gym -22.9% ok. Slide R24 ok.
- Weave harness note: on a fresh load the first canvas mousedown asks for pointer lock and does not fire, so weave reads basic 0. chope.wp7c.html reads the same. Primed with one mousedown in a started match, then weave measured as above.
- ACC runAll at 1366x768 and 800x600: PASS 53, FAIL 1, SKIP 0, MANUAL 10. G4 errors 0. The fail is wp2b turret 15 dps at 15 m, which reads 12.0. That follows from the ruled turret cut. A needs to update the test.

## WP8a - Integrator
Map loader. chope.pre-wp8a.html (same as chope.wp7d.html) to chope.wp8a.html.
- gen_hawker.py follows the live build (R40). Stall colours, names, Han text, menus and food colours now come from the live STALLS and SIGN. Zone table A added. Bins are drawn only. Bounds match the live clamp. Roof collider added. Node A moved to (-13,9.4) so link A-n2 clears the zone table. hawker.json regenerated: viewer 0 warnings, static tris 17770.
- chope.html carries MAPS (raw JSON per id) plus expandMap and mapSolids, ported from the viewer. The game builds 148 colliders from hawker.json. proto-env/obstacles.json also has 148. Worst gap 0.00012 m.
- The hand-built arena (addTable, addBox, ZONE_R) is gone. loadMap(id) fills obstacles, zones (each with its own r), spawns, pickups, bounds and the shadow camera. applyMap(id) rebuilds arena visuals, pickups and the env group and drops a stale build.
- STALLS and SIGN are filled from map.signs.rows. HAN_TEXT covers the rows of every map.
- Menu chip "Map: Hawker Centre". profile.map defaults to hawker and is saved in the profile (try/catch as before).
- Hooks: __chope.maps, __chope.map (raw JSON), __chope.setMap(id).
- Side by side at two fixed cameras: draw calls 51 and 51, no visible change.
- ACC wp8-hawker over 10 matches: all PASS except one match at 207 s. Lengths 140,159,176,132,131,149,165,133,137,207, and 198 in the runAll pass. Stuck 0 or 1. Slow max 2.1 s. Draw avg 55 to 63, max 99. Programs 20. Step 0.061 to 0.065 ms. nav.path SKIP until WP8b.
- Baseline for the length tail: chope.pre-wp8a.html with the same loop gave 118,167,136,148,166,147,148,185,146,173,165,183,140 (2 of 13 over 180, mean 155). The tail predates WP8a.
- ACC runAll at 1366x768: PASS 59, FAIL 1 (the 198 s match above), SKIP 4, MANUAL 10. At 800x600: PASS 59, FAIL 1 (G3 feed 0), SKIP 4, MANUAL 10. G3 is a 60 s window with no kill: 2 of 8 on chope.html and 1 of 8 on chope.pre-wp8a.html. Gate rerun at 800x600: PASS 8. Console errors 0.

## WP8b - Integrator
Bot nav graph (R41). chope.pre-wp8b.html to chope.wp8b.html.
- buildNav() runs in loadMap. Nodes and links come from the expanded map, mirror included. A k link is never used (bots do not crouch). An s link is used only after the earliest shutter openAt.
- segClear(a,b,w) casts a knee-height ray plus two shoulder rays. navNear picks the nearest node on the same level with a clear walk. For the goal end it falls back to the nearest node (a zone centre sits inside a table).
- navPath is A* over the nodes. Each point carries the flag of the link into it. A j link makes a grounded bot hop when the next point is higher.
- navStep sets ai.goal. It walks straight when the spot is in clear view. Else it follows the path, skips points it can already see, and re-plans when the next point goes out of view. With no visible node it walks 3 m toward the most open of 8 headings.
- Melee bots chase a target they cannot see within 14 m along the path. While on a path a bot drops fight strafe, the far-target pull and the Newspaper Boy back-off. A melee bot only stands and swings when the target is within 1.2 m of its height.
- Strafe flips when the strafe side is blocked within 0.9 m, and stops when both sides are.
- Holds by role: defending an owned zone, half the time a bot takes a hold of its role within 14 m (HOLD_ROLE maps role to tank, sniper, builder or assassin).
- carpark.json nav: added door approach nodes dNi (-26.4,2.1) and dSi (-26.4,-2.1) between spawn and the doors. The spawn to door links grazed the 1.8 m door jambs.
- Hooks: __chope.nav.path([x,z] or [x,y,z], same, size) returns points or null. __chope.nav.nodes.

## WP8c - Integrator
Map hazards (wet, shutter, smoke, fog, alarm). chope.pre-wp8c.html to chope.wp8c.html.
- makeHazards builds HAZ from the map JSON in loadMap. updateHazards runs each step and only writes h.on when the schedule changes, so a test can set it by hand. resetHazards runs in startMatch.
- wet: ground accel and friction scale by wetK(e) inside a wet rect. Bots walk at 0.6 speed on wet so they do not slide into the ice stall.
- shutter: a solid box in obstacles until openAt, then removed. Plays e_shutter when it opens.
- smoke (sphere, on a repeating schedule from offset) and fog (box, from at for dur): hazDist blocks a line once 3 m of it is inside (SEE=3). los and rayHit both use it, so they agree.
- alarm: a hitscan end or a damage point inside r triggers it for 8 s. It plays e_alarm and sets ai.heard on live bots inside r. A bot with no target turns toward the heard point.
- Meshes: wet plane, shutter box, smoke sphere and fog box. Smoke and fog are hidden while off.
- Bot nav: navNear skips a node whose links are all shut (the shutter gap before openAt). The probe loop checks both shoulders with segClear. This fixed bots stuck in the wetmarket counter pockets and on the centre-aisle crates.
- Hooks: __chope.hazards, __chope.los(a,b).

## WP8d - Integrator
Blk 404 Void Deck ships in MAPS. chope.pre-wp8d.html to chope.wp8d.html.
- MAPS.voiddeck holds proto-maps/maps/voiddeck.json. It sits on the line after MAPS, so hawker stays first in the map cycle.
- ENV.buildMapEnv({map,X,ramp}) renders any map that has no hawker menu rows. It is a render-only port of the viewer build(): floors (terrazzo, tile, concrete), wall textures (walltile, pillar, hdb, shutter, zinc), boxes, stairs, the prop library, sign atlas, outside blocks and trees. Colliders still come from loadMap. hawker keeps ENV.buildEnv.
- applyMap applies map.look before the build: fog colour and range, background (fog colour), hemi colours and intensity, sun colour and intensity. The hemi light is now a named const.
- hp pickup: a cream first-aid tin with a green lid and green crosses. Same heal and cleanse as the teh. Subtitle "First aid! +80 HP".
- R38 bots on the tower deck. Bots never reached the deck before this package (0 bot samples above 1.9 m in 3 matches). Three fixes:
  - climbing(a,e): while a bot follows a path point more than .3 m above or below it, the wall probe does not steer and a lost knee ray does not re-plan. The knee ray hits the next riser on a stair, which turned bots off the side. A periodic re-plan still runs every 8 checks in place of 4.
  - navPath: a link with more than .3 m of height change costs 3 times its length. High ground costs something to reach (MAPS.md), so bots stop using the deck as a crossing between halves. Those crossings put wide bots on the 1.4 m stair and logged stucks there.
  - voiddeck.json and MAPS.voiddeck nav: new node stairT (-0.9, -1.5, y 2.45) on the deck past the stair top. stairW to deck becomes stairW to stairT to deck. A bot now turns for the deck centre only once it is clear of the rail end at z -0.8.

## WP8e - Integrator
Pasar Lorong Tiga ships in MAPS. chope.pre-wp8e.html to chope.wp8e.html.
- MAPS.wetmarket holds proto-maps/maps/wetmarket.json, on the line after MAPS.voiddeck. The harness no longer injects it.
- Stuck detection: the 0.6 m progress bar scales by wetK. On a wet patch a bot speeds up and turns at the friction rate, so a bot easing off a counter beside a wet patch logged as stuck. A bot with no progress at all still logs.
- wetmarket nav: cut1 moves from z 4.5 to 4.1, the centre of the 1.55 m pocket. The straight line from pkS to cut1 passed .44 m from the wall end at x -14.4, under Ah Ma's radius, so wide bots ground on it. The chokes list keeps its label point.

## WP8f - Integrator
Multi-storey carpark ships in MAPS. chope.pre-wp8f.html to chope.wp8f.html.
- MAPS.carpark holds proto-maps/maps/carpark.json, on the line after MAPS.wetmarket (// WP8f).
- carpark nav: two stair-top nodes, stSt (-13,10.2,y 2.4) and stWt (-21,11.25,y 2.4). Links stS-dk and stW-dk now go through them. Bots took the stair to deck link on a diagonal, walked off the stair side and ended under the deck. Nodes 21 to 23, links 28 to 30. The JSON has the same change.
- wetmarket chokes label for cut1 now reads z 4.1, matching the nav node (A's small item).

## WP17 AB0 - Integrator
Shared weapon state, marks and the pip row. chope.pre-wp17-ab0.html to chope.wp17-ab0.html. No behaviour change.
- makeEnt: e.wpn {charge, stage, spent}, reset on spawn. e.marks {stink, cut, tag}. stink is a getter on the poison stack (6 dps, cap 3). cut and tag hold seconds left and a src, tick in tickStatus, clear in clearStatus.
- applyStatus: new kinds 'cut' and 'tag', 3 s by default, no stat effect. 'poison' also reads o.stacks.
- R50 hooks: e.anim {shotT, castT, cast}. shotT counts up in tickEnt and is set to 0 on a ranged shot in tryPrimary and on the melee strike in tickMelee. castT 0 and cast = slot on an ability, 'ult' on an ult.
- Pips: a DOM overlay in #hud (#pips), one row per marked entity, placed by projecting the head top. 0 draw calls. Green Stink per stack, white Paper Cut, yellow Tag. Placeholder look.
- __chope.pips(e) returns the pip count. __chope.pipKinds(e) returns the kinds.

## WP17 AB1 - Integrator
- Ah Ma kit per ABILITIES.md 9 AB1: Walker Combo 50, 50, Hook 82 (Hook tugs the target toward her, kb 9.3, measured 1.38 m). The string resets after 1.2 s idle, held while Tiger Balm is on.
- Kopitiam Charge 65, plus 25 and a primed Hook when it pins the target within 2.5 m of a wall.
- Walker Twirl pulls in (kb 5, none inside 1 m) and cuts .8 s off its cooldown per hit.
- Tiger Balm: a landed Hook adds 1 s to her oil heal-over-time.
- Seen It All DR .8 to .9. Slipper Storm ramps 60/70/80/90 per s per target, cost 135.
- freeEnt removes the pip row (A's AB0 fix).
- Snapshots: chope.pre-wp17-ab1.html, chope.wp17-ab1.html.

## WP17 AB2 - Integrator (reverted)
- Built Gym per ABILITIES.md 9 AB2: Med Ball Reps, Finish Line bonk, Spotter rep gain, Battle Ropes scaling, Personal Best rep lock, no PB damage buff. All 5 wp17-ab2 rows PASS.
- It breaks the AB1 duel band: Ah Ma over Gym 19.9% (n396, band 40-60). With the Rep cycle speedup turned off, the same duel reads 45.5%. Reverted to chope.pre-wp17-ab2.html per the band rule.
- The AB2 build is kept as chope.wp17-ab2-held.html for A. chope.html is the AB1 build again.

## WP17 AB2 re-apply - Integrator
- Re-applied chope.wp17-ab2-held.html with A's ruling: Med Ball 50 per hit, cycle cut 3% of .62 per Rep (.62 to .546). The kit text now says 3%.
- Snapshot: chope.wp17-ab2.html.

## WP17 AB3 - Integrator (reverted)
- Built Uncle to ABILITIES.md AB3: Booger Flick direct 38 + 2 Stink and splash 20 + 1 Stink with no slow, Kopi Break, Chewing Gum blob, Air Out, Durian 3 Stink and kick, ult 170.
- One row failed: two directs then Air Out leave a 175 HP target on 7 HP. Reverted to chope.wp17-ab2.html. The build is held as chope.wp17-ab3-held.html and wp8/edit_ab3.py rebuilds it.

## WP17 AB3 re-apply - Integrator
- Re-applied the held Uncle build with A's ruling: Air Out base 30 plus 22 per Stink (max 96). Kit text matches.
- Snapshot: chope.wp17-ab3.html.

## WP17 AB4 - Integrator (reverted)
- Built NS Boy to the AB4 spec: Rubber Band Rifle (stretch, 8 bands, 1.5 s reload, active reload .6 to .8 s), Fall In pre-stretch, Water Parade pierce, one guided Matador, Live Firing 5 s at .35.
- NS Boy won 41% over 90 sweep matches (band 50 to 56). Reverted to chope.wp17-ab3.html. The build is held as chope.wp17-ab4-held.html and wp8/edit_ab4.py rebuilds it.


## WP17 AB4 re-apply - Integrator (held again)
- Bot full-stretch share 80% per A, then the tap 30 fallback. NS Boy 38.6% and 35.3% over 90 sweep matches, under the 45 guard. Held as chope.wp17-ab4-held.html, chope.html stays without AB4.

## WP17 AB5 - Integrator
- Engineer Encik kit: Foam Dart Ricochet (one bounce, 55 after, Tag 3 s, repairs his own turret 30), Folding Table (soaked damage charges ult at half rate), Kopi Can Turret (cap 2, 120 HP, 9 per shot, prefers Tagged, +20% to Tagged), Hi-Vis Vest (+50 armour, +20% speed 2 s), Claim OT (140, 7 s, .2 s fire, +50% max HP).
- AB4 NS Boy applied on top at spec numbers per A ruling 2.
- AB5 fix per A review: the dart bounces off walls and props only. A dart that hits the floor stops.

## WP17 AB6 - Integrator
- Recess Rascal kit: Paper Shuriken 21, one wall or prop bounce for 14 (no floor bounce). Every 3rd star in a row on one target applies Paper Cut 3 s (streak resets after 1 s or on a new target).
- Recess Dash 30. Exercise Book Block 1 s deflect, Perfect Copy in the first .25 s: -3 s cooldown once per Book, the returned shot applies Paper Cut (projectiles and hitscan).
- Ruler Slice windup .15, 65, +25 and -2 s cooldown on a Paper Cut target. PSLE Slash +40 on Paper Cut targets and does not shove them. Kit text updated.

## WP17 AB7 - Integrator
- Built on the repdash build (P pause, Gym Rep counter, Dash radius 1.5).
- Turret HP 100, shot 8. Dart repair 20. Uncle gum trap snare 1.0 s, slow 2.2 s. Uncle ult cost 195.
- Bots: Rascal Ruler whenever up and in reach, Ah Ma Charge also at 4 to 8 m, Twirl under half HP with a foe near, Gym Ropes at 2 Reps. Air Out 26 plus 22 per stack.
- Saved as chope.wp17-ab7.html. Accepted by A with known issues under 1 point on Uncle win, the Engineer+Uncle pair and Rascal charge.

## WP17 AB8 - Integrator
- Wave 1 checkpoint, functional only. No code change. Snapshot chope.wp17-ab8.html.

## WP17 AB9 - Integrator
- One heal() path for every heal. Sticky status, cleanse, ally-heal ult charge (.12 per HP), heal assists inside 3 s.
- Support HUD: ally low HP bar flash and ping, heal-target ring.

## WP17 AB10 - Integrator
- JC Debater (Zoner, 150 HP, 7.0 speed, size .9, ult 220). Model and face atlas page 2 from proto-heroes2/models2.js. First person megaphone and bell viewmodel.
- Cue Card Plane: 30 m/s, light drop, lofted onto the crosshair point. 24 up to 10 m of flight, +1.2 per m, 48 from 30 m. Strafe banks the plane.
- Order, Order! bell zone r5, 6 ticks of 12, 15% slow, planes +10% inside. Rebuttal 7 m cone, 20 and a knock to about 10 m, ends charges and dashes.
- Rostrum podium 1.2 x 1.2 x 1.0, 150 HP, 12 s, solid and standable, +5 m of flight from on top. Closing Statement: 7 m circle within 40 m, no LOS, 6 waves of 22 from 1.2 s.
- Cue Card Slap quick melee 25, Blazer Slide 6.04 m. Bot rules from HEROES2 section 5. HUD kit card with new icons.

## WP17 AB11 - Integrator
- Teh Tarik Auntie (Support, 175 HP, 7.0 speed, size .95, ult 200). Model from proto-heroes2/models2.js. First person steel jug and mug viewmodel.
- Pour: hold a 10 m stream. 4/s then 6/s on an enemy, 6/s then 9/s on an ally after 1.5 s on one target. Release after 1.5 s and press within .3 s for the Toss, 40 in r2.
- Pull to Table: 15 m 8 deg ally cone, travel to 1.2 m short and heal 20. No ally means a 6 m dash. Ice Kosong: cleanse, 25, +20% speed 2 s, on an ally or self. Milk Spill: lobbed r4.8 zone, slow and sticky 1.5 s.
- Drinks On Me: 6 s aura, 35/s, 210 cap per ally, she moves at 85%. Self Service: calm regen from 4 s. R33: at most one Tarik per team.
- Pull now zeroes velocity on arrival and abort, so she stops at 1.2 m.

## WP17 AB12 - Integrator
- Makan Rider added without ult (Peak Hour Rush is AB13). HEROES.rider, model ported from proto-heroes2 (budget 4400, height 2.13, skin 1), viewmodel with a three-stick fan and a wrist phone, HUD kit with new icons and field --hdb-lime, quick melee Cube Bag Swing, slide Scooter Coast.
- Chopstick Fan: three sticks 2.5 deg apart at 45 m/s, centre 12, sides 5. Stars on the centre stick only, +4% each to 5, a centre miss clears them. x1.25 when fired from 2 m above the target's feet. No head multiplier (ABILITIES.md lists none).
- Kick-Scoot Launch (cd 8): 12.5 up, 9 along aim, keeps slide speed if higher, keeps Stars. Special Delivery (cd 9): plunge at 20 m/s with a red landing ring, r2.5 for 50 +5 per m fallen (cap 70), +20 on a Tracked target. On the ground a 4 m hop for 50. Order Tracking (cd 12): sticker for 15, Tracked 6 s, +10% damage from the Rider (the plunge uses its own +20 instead).
- Umbrella Glide: Space held while falling caps the fall at 2.5 m/s. Awnings are a 'rider' collider at 3.35 m: only he stands on them, nothing else collides with them, shots and sight pass through. 4 s on an awning, then 3 s locked out.
- Ceiling rule in collide: an airborne body whose head enters a box from below stops under it. The hawker roof (7.2 m) was shoving the Rider sideways by up to 10 m after an awning launch.
- Bots: perch on a counter that sees the most enemies within 15 m, launch up to the awning, leave at 3.5 s, glide, plunge when an enemy is within 2 m below, escape launch under 40% HP, track rascal or gym or far targets. A perched bot's goal is where he stands.

## WP17 AB13 - Integrator
- Rider ult Peak Hour Rush: 7 s flight at 8.5 m/s, Space rises and C sinks, 6 m ceiling. Fan cycle x0.75 and Special Delivery cooldown 2 s while flying. No slide while flying.
- Kit: kit[4] is now the ult row. The Umbrella Glide passive moves to kit[5].
- Bot Rider ults on a target 6 to 20 m away, then holds about 4 m up and 12 m out and circles. It plunges when within 2.5 m.
- Reveal: Tracked enemies show a see-through capsule silhouette to the Rider's team only. One draw call each.
- Verified: runWP wp17-ab13 flight row PASS (max y 5.49). runAll 131 pass, 0 fail, EC 0 at 1366x768 and 800x600.

## WP17 AB14 - Integrator
- Face atlas (R33): one 1024x1024 8x8 page. Wave 1 in cells 0 to 29, wave 2 in rows 4 and 5 (cells 32 to 46). The second atlas page is gone, so all 9 heroes share one texture.
- Engineer turret: a nozzle merged into the can geometry (same draw call). The turret snaps to face its target.
- Already in place and checked: Tarik head 1.47, 9 heroes live in HEROES, 9 hero cards in the menu, scooter has no collider, wave 2 bot rules, Toss gate.
- Verified: runWP wp17-ab14 2 PASS, 1 SKIP (balance), 3 MANUAL staged. ttk3.py prints "bands ok". runAll 131 pass, 0 fail, EC 0 at 1366x768. At 800x600 the only fail is carpark match length 104 (balance noise).

## WP17 close gate - Integrator
- Functional close gate only, per the user's ruling (no balance checks).
- Fixed the stale HUD.KITS hp: Gym 250 to 275, Rascal 125 to 137. Bars already used maxHp.
- runWP wp17-close: 5 SKIP (balance, and R30 needs the AB8 base), 2 MANUAL.
- R28 restaged: slide, launch and glide cover 22.1 to 23.1 m (26 or less).
- Programs stay flat from match to match: hawker 21/21/21/21/20, across maps 18 to 19.
- Lineup look check at 10 m and 30 m: enemies keep the red outline and red bars, allies blue. Rider green, Debater white, Rascal yellow and NS Boy olive all read apart.
- runAll 1366: 131/0, EC 0. 800: 129/2, both fails are match length (voiddeck 107, carpark 100 and 105), a balance band. Stuck, draw and errors pass.
- Snapshot chope.wp17-close.html.

## WP16a.0 - Integrator
- Program headroom (R51). No look change: every added colour is white.
- Fans get a white instanceColor. The bit and slip particle pools get white vertex colours. Both now share one toon program (instancing, instanceColor, vertexColors).
- Every EFX instanced mesh gets a white instanceColor, so shadow and barbg share the ring and barfg basic program.
- High, fresh load, 30 s, hawker: 25 to 23. Four maps in one page: 22 to 24.
- runAll 1366: 130/1 (voiddeck length 215). 800: 128/3 (length on three maps, one hawker match stuck 3). EC 0 both.
- Snapshot chope.wp16a0.html. Backup chope.pre-wp16a0.html.

## WP16a.1 - Integrator
- G1 tone map and grade in the comp pass, ported from the proto NEW path. Khronos PBR Neutral at exposure 1.05, then sRGB. Saturation 1.08, plum shadow lift, warm highlights on L squared, vignette .35, grain .02. renderer.toneMapping stays NoToneMapping.
- Hawker Medium: pixels at 254 or more on all channels 0% at spawn and over 10 samples of 30 s autopilot (0% before too). Lower third luma .54, upper third .26 (was .31).
- Programs, draw calls and passes unchanged.
- runAll 1366: 130/1 (hawker length 207). 800: 129/2 (length only). EC 0.
- Snapshot chope.wp16a1.html. Backup chope.pre-wp16a1.html.

## WP16a.2 - Integrator
- G17 look rows in all 4 map look blocks: bg, hemi, sun, fogExp, gloom (stored for 16a.3, carpark null), floorTint.
- applyMap picks FogExp2 when look.fogExp is set, else the linear fog. Scene starts on FogExp2 so load-time programs match the maps (fog type is a program key).
- Floor material colour set from look.floorTint after the env swap. Toon ramp [78,140,205,255]. Shaft k .35.
- Tuned from the starting rows: voiddeck floorTint #ffffff, carpark floorTint #ffffff and bg #8fa9b4.
- New hook __chope.camFix=[x,y,z,tx,ty,tz] pins the camera (null clears).
- Harness fix: wp8/harness.js no longer swaps in proto-maps/maps/carpark.json. That stale copy had the old look and no fogExp, so it put carpark on linear fog and doubled programs (29) in runAll.
- Luma, Medium, preset cam (lower/upper): hawker .507/.231 ok, wetmarket .449/.220 ok, voiddeck .524/.464 OUT, carpark .549/.576 OUT.
- drawCalls at the preset cam match chope.wp16a1.html: 49, 74, 70, 70. Console errors 0 across all maps on all tiers.
- runAll 1366: PASS 129, FAIL 2 (wp3 stuck 2.5 avg, wetmarket length 99). 800: PASS 131, FAIL 0. EC 0, programs 19.
- Snapshot chope.wp16a2.html. Backup chope.pre-wp16a2.html.

## WP16a.3 - Integrator
- G4 ceiling gloom in comp: camW (camera matrixWorld, set each frame) and gloom uniforms. World y from depth, smoothstep(gloom.x, gloom.y, wy) darkens toward gloom.z*(1,1.04,1.14). Roof ink drops 60% under full gloom. applyMap loads look.gloom, or (99,100,1) when null.
- G6 ink: silhouette fades 30 to 55 m, crease 14 to 40 m. Ink colour 50% near-black, 50% local colour times .3.
- G7 AO: strength .8, plum tint (.46,.36,.52), skipped under 1.5 m linear depth. Low keeps ao 0.
- Low pass overhead (R20) diff 13.9 at 1366, 13.8 at 800. Unchanged. Programs 19 after runAll, same as WP16a.2.
- Gloom k=1 vs WP16a.2 mean luma shift (0-255): hawker +3.1, wetmarket +1.3, voiddeck +1.9. The shift comes from the lighter ink and weaker AO in this same step. Gloom on: hawker -3.6, wetmarket -6.8, voiddeck -9.1, mostly in the upper third.
- Luma at preset cam: hawker .508/.186, wetmarket .451/.151, voiddeck .525/.391 (now passes), carpark .552/.576 (accepted known issue).
- runAll 1366: PASS 131, FAIL 0. 800: PASS 130, FAIL 1 (wetmarket stuck 3, the carried item). EC 0.
- Snapshot chope.wp16a3.html. Backup chope.pre-wp16a3.html.

## WP16a.4 - Integrator
- G8: static toon materials (hawker VCM, generic VC) use shadowSide BackSide. Zinc sheets (hawker 'zinc', generic 'tex:zinc...') do not cast. Rafters still cast.
- New shadowFlags(o) helper used by setTier and after every env swap. Before this, a map swap left the new env with no shadow flags until the next setTier. The swap also sets shadowMap.needsUpdate.
- Hawker floor luma at the preset cam, High vs Medium (x .2 to .8): lower half .459 vs .519 (diff .060), lower third .446 vs .512 (diff .066). WP16a.3 High was .308 and .291.
- shadowCalls on High hawker at load: 24 before, 23 after. After map swaps on High: wetmarket 9, voiddeck 9, carpark 7, hawker 12. No console errors.
- runAll 1366: PASS 129, FAIL 2 (wetmarket and carpark match length). 800: PASS 129, FAIL 2 (hawker stuck 3 plus length, carpark length). EC 0, programs 19.
- Snapshot chope.wp16a4.html. Backup chope.pre-wp16a4.html.

## WP16a.5 - Integrator
- G9 rim light: new module-scope rimify(mat,col,amt). It injects the rim term before opaque_fragment and sets customProgramCacheKey to 'rim1'. Uniforms rimCol and rimAmt live per material.
- Heroes: ally 0xfff1dc at .9, enemy 0xff7a3d at 1.3, set in makeMesh. Viewmodel material uses the same key at .5.
- G11: character blob opacity .25 to .45.
- Armband scaled [1.05,1.05,1.6] (1.6x tall). Collar ring scaled [1.25,1.25,1.8] so it shows past the head. Both stay merged in existing meshes.
- G10 enemy outline colour unchanged.

## WP16a.6 - Integrator
- G12: 512x256 VFX atlas (8 cells) and a 256 billboard InstancedMesh pool. G13: 64 floor decal pool, ring buffer, 6 s life, 1 s fade.
- Both pools share one ShaderMaterial program. Billboard or decal mode is a uniform, so the source is identical (R51).
- burst() and sphereFx() keep their signatures and write into the sprite pool. The toon cube pool (PL.bit) is gone. The air-out cone uses the pool too.
- splash() drops a splat decal when the blast is near the floor.
- Zone labels are a camera-facing basic quad. The THREE.Sprite path is gone.
- __chope.vfx exposes spr, decal, VFX and VCELL for tests.

## WP16a.7 - Integrator
- G14 hit feedback: new hitFx(c,frac,head) replaces the sphere puff on non-player hits. One star sprite sized .6 + .6 x sqrt(damage fraction), cream on body, white on head. A head hit adds a gold ring. Six streaks on body, eight on head, in the camera plane, .18 s.
- Hit flash is now a .05 s near-white tint, then red emissive fading to 0 over .2 s, peak .45. Driven by a new e.hitT. The old .9 squash is gone. The rig pops 7% for .12 s.
- Tracers last .1 s and use cream 0xfff1dc (ult stays 0xffe600). Still a box mesh.
- R21: shadowFlags drops fan (zinc), glow and instanced meshes from casting, and unmapped casters use shadowSide BackSide. High programs after 30 s: 26 to 22, depth variants 5 to 1. shadowCalls 67 to 51.
- runAll 1366: PASS 127, FAIL 4 (wp7 and wp8 match length only). 800: PASS 129, FAIL 2 (match length only). EC 0, programs 20.
- Snapshot chope.wp16a7.html. Backup chope.pre-wp16a7.html.

## WP16a.8 - Integrator
- Ability VFX recipes: RECIPES table (tele, shot, trail, imp, decal, lin phases) and fxr(id,ph,p,k). Covers all 20 ABILITIES section 5 ids plus aliases.
- Telegraph on ability and ult start. Shot flash at the muzzle or chest. Projectile and charge trails. Impact and decal on hit for recipe weapons. Linger effects on wall bonk, turret repair, dart bounce, Perfect Copy, shuriken 3rd hit, Tarik Toss and Tarik heal.
- Status VFX in tickStatus: slow drops, buff ring, Finish Line trail, 3-Stink drip.
- Crit damage numbers: gold, 34px, class crit. Payoff hits flag crit (walker hook, Finish Line bonk, Paper Cut, full rubber band, battle ropes, plane at 30 m or more).
- Checks: syntax ok, ASCII 0. Spec test: 69 colours outside team hue bands, all 59 phases fired for +2 draw calls, EC 0.
- runAll 1366x768: PASS 130 FAIL 1 (carpark length). 800x600: PASS 129 FAIL 2 (wp7 length, wp8 length 101 with stuck 2). EC 0, programs 20.

## WP16a.9 - Integrator
- Zone telegraph (G16): beam cylinder removed. Ring and fill are cream 0xfff6e6 at .35 when neutral and take the team colour when captured. Contested ring stays gold.
- 4 chevrons per zone in the shared sprite pool, on the ring, pointing in on screen, bobbing .1 m at 1 Hz. They are re-added if the pool drops them.
- Rubber band full headshot ring is now white (A, 16a.8 review).
- Checks: syntax ok, ASCII 0. Beams cost 3 calls on hawker with all zones in view (51 to 48). Chevrons share the sprite pool call. Capture turns ring, fill and chevrons to the team colour.
- runAll 1366x768: PASS 129 FAIL 2. 800x600: PASS 127 FAIL 4. All fails are length bands except one wetmarket stuck 3 at 1366, which passed on 3 reruns (stuck 0 to 1). EC 0, programs 20.

## Skill designer
- SKILLS.md: new kit text for all 9 heroes, checked against code. Mismatches fixed in text: Chewing Gum (trap, no projectile), Live Firing (42, head x1.5), Claim OT (+50% HP is on turrets). New P rows for Ah Ma, NS Boy and Tarik.
- Fun pass: 8 small feedback changes, player only, no balance numbers changed. Hook and Ruler hit-stop, Air Out payoff, Durian kick prompt, full-stretch click, Rep 4 ding, Twirl ring 4.2 to 3.8, pause kit panel.
- Packages SK1 (kit text), SK2 (feedback), SK3 (pause kit). Patch in proto-skills/skills.diff.
- Checks in proto: ACC.errs empty, bot matches end for all 9 heroes, stuck 2 or less (one Tarik run hit 4, reruns 1, 1, 0).
- Rework round SK4 to SK10, built by proto-skills/sk4.py on top of current chope.html. Renames: Gym Hunk, MRT Seat Rush, Runner's High!. NS Boy ult is a 3 rocket volley. Turret locks on in .15 s and hits for 14. Debater Stay Back! replaces Rostrum. Rider launches higher and glides slower. Food Parcel replaces Order Tracking. Ruler Slice is a hold to charge dash-stab with a meter and aim line.
- Checks in proto: bot matches end for all 9 heroes, ACC.errs empty, stuck 2 or less. Numbers in SKILLS.md section 4. Tests SK1.5, AB4, AB6 and AB10 need updates.
- SK11 Teh Tarik Auntie rework, built by proto-skills/sk11.py on current chope.html. Tea Stream locks on, Cup Toss bounces, Steam Off, Have a Cup!, Teh Tarik Rain. Old milk, ice, pull and table code removed. Checks: ACC.errs empty, bot matches end for all 9 heroes, stuck 1 or less. Numbers and dead code list in SKILLS.md SK11.

## SK1 - Integrator
- Kit text for all 9 heroes from SKILLS.md section 2, applied with proto-skills/kit_sk1.py. Kit names unchanged. New P rows for Ah Ma, NS Boy and Tarik.
- Menu fix: no period after a skill name that ends in ! or ? ("Fall In!", "Personal Best!").
- Checks: syntax ok, ASCII 0. 9 cards, 49 rows, max 86 characters, no quotes or angle brackets, no card overflow at 1366 or 800.
- runAll 1366x768: PASS 129 FAIL 2 (hawker and carpark length, one hawker match stuck 3). wp8-hawker rerun 3 times, stuck 0. 800x600: SK1 rows all PASS, wp8 all PASS. SK2 and SK3 rows fail until those packages land. EC 0, programs 20.

## SK2 - Integrator
- Skill feedback, player only: Hook thud (F1), Ruler on Cut hit-stop and sound (F2), Air Out shake by stacks and full-stink payoff (F3), Durian kick prompt (F5), NS Boy full-stretch clink (F6), Gym Rep 4 bell and burst (F7). Twirl ring radius 3.8 to match the hitbox (F8).
- Fix to the SKILLS.md patch: F6 used e.isPlayer inside bandInput, where the entity is p. It threw "e is not defined" (AB4). Now p.isPlayer.
- Checks: syntax ok, ASCII 0. runAll 1366x768: PASS 138 FAIL 9. 800x600: PASS 139 FAIL 8. Fails are SK3 and WP19 rows waiting for their packages, plus length bands. EC 0, programs 20.

## SK3 - Integrator
- Pause screen lists the current hero kit in a new #pkit list under the tag line. showScreen fills it on each #pause open, so a hero switch shows the new kit.
- Same row format as the menu cards, with the Fall In fix (no period after a name ending in ! or ?).
- Snapshot chope.sk3.html. Backup chope.pre-sk3.html.
- runAll 800x600: PASS 142 FAIL 5. SK3.1 to SK3.3 PASS. Fails: wp19 x4 (not built yet), wp8 voiddeck length band.
- runAll 1366x768: PASS 140 FAIL 7. SK3.1 to SK3.3 PASS. Fails: wp19 x4, wp8 voiddeck and carpark length band, SK2.8 stuck 3 (rider, rascal). SK2.8 reran clean (max stuck 1, errors 0).

## SK4 to SK10 - Integrator
- Merged the rework round from proto-skills/sk4.py (SK3 part skipped, already in). Script: wp8/edit_sk4.py.
- SK4 renames: Gym Hunk, MRT Seat Rush (Ah Ma slot 1, the code owner of Kopitiam Charge), Runner's High!.
- SK5 Live Firing volley, SK6 turret lock-on, SK7 Stay Back!, SK8 Rider airtime, SK9 Food Parcel, SK10 Ruler charge dash-stab.
- Coordinator rulings: kit rows kept at 90 chars max. Food Parcel row is now 75 chars, Ruler Slice row 82. Shared Matador and Live Firing icon kept.
- Dead code removed: NS Boy live band path in tryPrimary, Debater rost method, the rostrum deploy kind (DEP, DEPG, DEPC, deploy branch), the plane rost flight bonus, the old ruler Cut path and rulerRf in meleeStrike.

## WP16b.1 - Integrator
- Shared stance-locked stride from proto-anim (legAng, strideEnt, SR rows for the six wave 1 heroes). Leg rotation order YXZ (R1). Legs cancel body lean and twist. Run lean per hero from SR.
- Tarik, Debater and Rider keep the old walk until 16b.9.
- __chope.animEnt exposed for the slip test.

## WP16b.2 - Integrator
- Action layer: ACT basic clips for Gym, Rascal, Ah Ma (poke and Hook), Uncle, NS Boy and Engineer. Twelve additive channels per ANIMATION 3.3, eases from proto-anim, kfA port.
- Melee clips map the windup onto 0..r, then play on from the release key at the strike. Ranged clips start at the release key on the shot. Gym and Ah Ma pokes mirror on alternate swings.
- Planted feet: hips keep their pre-clip spot, legs cancel the clip lean and twist, the stretch goes on the body mesh, lean is damped with speed. Loco damping uses run fraction.
- withUpdate takes an atk flag for the face. Clip heroes no longer get the model attack state. Tarik, Debater and Rider keep it until their clips land.
- tests/slip.js holds SLIP2 and SLIPRUN for A to rerun.

## WP16b.3 - Integrator
- Springs (ANIMATION 3.4): squash, accel lean, flinch x and z. sprg() sub-steps at 120 Hz. The name spr was taken by the VFX sprite pool.
- Squash spring replaces the old air stretch, land term and slide sqT/popT scale. The timers stay for other readers.
- Jump and land (3.6): takeoff stretch, rising tuck, falling reach on stride heroes, land squash with rig dip and leg splay. First person gets a .5 deg pitch dip on land when landV > 8.
- Hit react (3.7): damage() writes e.anim.hx, hz, hn and big. The flinch pushes away from the attacker, with a squash and an arm flare. Big hits (over 60 or a knockback) add .25 lean back and arms out for .15 s.
- REDUCED: no squash, flinch at half.
- Skipped: prop springs and the head look-away. Heads are part of the body mesh and props are posed per model. Both are left for 16b.8.

## WP16b.4 - Integrator
- Viewmodel kick is now a per-hero spring (ANIMATION 3.10 and section 4 rows): VKS table with pos, rot, f, zeta and camera pitch. The impulse is scaled so each kick peaks at 1.
- NS Boy kick and pitch scale with band stretch c (pitch .3 + .5 c deg). Ah Ma's Hook has its own kick (yaw .12, x -.06).
- Camera pitch kick on every hero. REDUCED: kicks at 50 percent, pitch 0.
- Melee basics kick at the strike, not the windup. The second vmo.fire() at the strike is gone, it replayed the windup keys on contact.
- Gym and Ah Ma BASIC keys: windup out3, strike in2, .03 contact hold, recovery backOut. keyed() takes an optional ease per key.
- Local hit-stop (3.5): the target's flinch spring freezes for .04 s after a hit. Global hitStop is unchanged.
- __chope gains vk and cam(dt) for tests. vmKick is removed.

## WP16b.5 - Integrator
- Quick melee stops a slide (ANIMATION user ruling). tryMelee calls endSlide(e,'q'). Slide time and speed curve are untouched otherwise.
- Slide pose runs on a weight spring (f 7.1, zeta .48): lean back .45 peaks at .067 s with a .14 overshoot. Arms blend on the same weight. Slide buzz .006 on rig y above 3 m/s, off under REDUCED.
- A slide stopped by Q holds the body hip for .06 s, then blends out at k 28.
- Q clips for all 9 heroes: contact hold (.04, Rascal .02) and backOut settle in qBlend. New channels: drop, leg swing, smear on body.scale.z, windup squash. Gym and Rascal from 4.1 and 4.2, the rest at 70 percent of Gym. REDUCED: no smear, half squash.
- Slide entry and exit squash stay as set in 16b.3 (R53).

## WP16b.7 - Integrator
- Death flail (ANIMATION 3.8). animEnt now runs 4 limb springs on the dead (R2). Arms f 2.6 zeta .28, legs f 2.2 zeta .3. The start impulse uses the side part of the kill direction (rag.sd). Each floor impact over 1 m/s adds .6 times the impact speed. After 1 s the targets go to a starfish: arms out 1.3, legs out .4.
- Toy pop. At 2.2 s the scale swells to 1.15 in .08 s, then shrinks to .001 by 2.4 s. The 2.4 s puff is unchanged.
- Victory clips (3.9 and 4). vicTick runs on the end screen. Winners play a 3 s clip, then hold. On a draw both teams cheer. Losers idle. The dead finish their ragdoll and pop. The player model shows for the orbit camera.
- Clips for gym, rascal, ahma, uncle, nsboy and engineer. Debater, tarik and rider share a generic arms-wide clip until 16b.9.
- Test hooks: __chope.vic(dt) and __chope.vicT.

## WP16b.8 - Integrator
- Cast templates from ANIMATION section 5 on the WP17 kits. New featEnt(e,h,dt) runs after actEnt. apC adds a 12-channel pose with a weight.
- Charge: NS Boy band stretch (c from the stretch timer) and Gym Battle Ropes (fixed .7 s). Pose by out2(c), tremble .004 c^2 at 25 to 38 Hz past c .7, a .04 squash pulse at full. The NS Boy viewmodel pushes in .02 c.
- Reload: NS Boy clip over 1.5 s with the hand-at-mag key at .6 s. A good press plays the rest at 2x with a .04 pulse. A missed press fumbles (aRx +.2 wobble for .3 s).
- Combo: Ah Ma tracks the combo stage. Only stage 2 mirrors. The Hook finisher gets a .06 hold and a 1.5x kick.
- Channel: Matador steer, Rascal Homework Book (1 s), Tarik pour (lean grows with pour time). Sway .03 at 2 Hz.
- Payoff, pay(e,a,hold): hold freezes the clip and flinch springs, .06 squash pulse, 1.2x on the impact key for .25 s, kick 1.3x and 1 deg pitch for the player. Fires on 4 Reps, Finish Line bonk, Battle Ropes landing (1 + .05 per Rep), MRT Seat Rush wall pin, Air Out with stacks (arms flap once per stack), every 3rd shuriken and a Perfect Copy.
- Dash: forward lean .2, smear up to .35 (off in reduced motion), squash when the dash ends.
- Tarik Toss alt clip. Rider squash of .01 per Star on each shot. Debater body roll up to .1 rad from the strafe for .4 s after a shot.
- Prop lag springs: Gym f 3, Rascal f 4.5, Engineer clipboard f 6, zeta .28.

## WP16b.9 - Integrator
- Stride rows for Tarik [.9,1.1,0,0,.08,0] and Debater [.30,.45,0,.025,.06,.04].
- Victory clips for Tarik (pour arm high), Rider (hop with fist up), Debater (arms wide).
- Removed the unused TOSS clip. Tarik Toss uses the model attack lob. Pour channel scales with pour time.
- Swing clearance gets a minimum lift so short legs clear the ground.
- Rider keeps no stride row. She kick-pushes a scooter and the deck foot rides the deck.

## SK11 - Integrator
- Merged the Skill designer SK11 Teh Tarik Auntie rework with proto-skills/sk11.py. The kit is Tea Stream, Cup Toss, Steam Off, Have a Cup! and Teh Tarik Rain.
- Removed the old milk puddle, Ice Kosong, Pull to Table, Toss and the old ult, all inside sk11.py.
- wp8/edit_sk11.py removes the sticky status (nothing applies it now) and adds a __chope.damage test hook.
- cleanse() stays because the pickups call it. SFX.qtarik stays because quick melee calls it by hero key.
- Ult cost stays at 200 until the user rules on 170.

## WP16c.1 - Integrator
- Ported the proto-audio engine and all 157 recipes into chope.html as one AU module. Prototype board fields (cat, label, old) are stripped.
- No AudioContext exists before the first click or key press.
- Stored volumes are sanitised. Only finite numbers survive, clamped to 0..1. A broken chope-audio-v1 key loads defaults.
- The old SFX object is now a key map (O2N) onto the new recipes. Every old call site keeps working. Wave 2 quick melee keys reuse wave 1 hits with a pitch offset.
- Old music and ambience feed the new mus and amb buses. Mute drives the new master bus.
- play() refuses loop recipes and loopStart() refuses one-shots or unknown names. Before this, play('k_charge') threw halfway and left sources running.

## WP16c.2 - Integrator
- sfxAt() now turns a world position into listener space from the player yaw and passes it to play(). The recipe range, distance gain, air lowpass, behind cue and pan do the rest. The old flat 24 m cut is gone.
- Occlusion uses one cached ray per source every 150 ms, with the same wall and smoke checks as bot line of sight. Sources past 70 m skip the ray.
- The ray saves and restores wdBox so a sound never changes what a caller just read from wallDist.
- Test hooks: __chope.sfxAt and AU.lastStrip.

## WP16c.3 - Integrator
- Weapon fire sounds per hero. Each primary plays its own recipe: w_walker, w_medball, w_booger, w_band, w_dart, w_shuriken, w2_chopstick, w2_plane. Other melee plays q_whoosh.
- New helpers au(name,pos,o) and auE(e,name,o). The player's own shots play flat. Others play in listener space.
- Hit confirm: ui_head, ui_hit_shield, ui_hit_armour or ui_hit. A hit within 1 s of the last raises pitch by .5, capped at 4. DoT ticks do not build the combo.
- ui_hurt is panned toward the damage source. Weapon impact recipes play at the target for Ah Ma, Engineer, Gym and Rascal.
- Enemy projectiles play w_flyby once when they pass within 2.5 m of the player.
- The panOnly branch of strip now records lastStrip.
- Tarik Tea Stream sound waits for 16c.10.

## WP16c.4 - Integrator
- Ability sounds for the six wave 1 heroes. Each of the 18 abilities plays its own a_* recipe. Bark b_* recipes chain through `with`.
- Extra events: charge body hit, storm slippers, Matador and Live Firing bursts, gum place and snare, durian landing and kick, turret acquire, vest pickup, wall and turret break, shield break, Rascal dash reset, PSLE charge and release.
- Ult cast: the caster plays a_<hero>_ult. A bot ult also plays ui_ult_enemy or ui_ult_ally panned to the caster at any range. The 40 m "incoming" subtitle stays.
- Added `__chope.tryUlt(e)` as a test hook.
- Debater, Tarik and Rider abilities keep the old sounds until 16c.10.

## WP16c.5 - Integrator
- Footsteps: a stride timer per entity in stepAudio(), called from stanceTick. One `st_<surface>` every 0.38 s while standing and moving over 1.2 m/s. None when crouched, sliding or airborne. The game has no sprint, so the 0.30 s sprint stride from AUDIO.md is not used.
- Surface comes from STEPSURF per map (hawker tile, voiddeck and carpark concrete, wetmarket wet). There is no per-region floor data.
- AU.HEROSTEP gain and pitch per hero. Ah Ma adds st_walker every second step.
- mv_jump on takeoff, mv_land with gain clamp(fall speed / 12, .3, 1), mv_crouch on stand to crouch.
- New mv_slide_loop recipe. It starts with mv_slide, its param is speed over slide speed, and it stops when the slide ends or in ambStop().
- Bots play at their position and skip everything beyond 22 m. The player hears their own steps flat at gain .5.

## WP16c.6 - Integrator
- Low HP: AU.setLowHP follows the player below 35 percent HP and alive. It clears in ambStop() at match end and quit. The heartbeat now repeats every 0.6 s (was 0.8).
- ui_ult90 once when ult charge crosses 90 percent. It re-arms when charge drops back under 90.
- ui_tick once per second for the last 10 s of regular time. ui_go plays with the CHOPE YOUR TABLES! callout.
- ui_death on player KO, ui_respawn on player respawn.
- Menu: ui_hover on button mouseover, ui_click on button click, ui_back for Quit, Change hero and the end screen Change hero plate. Active in menus and the pause screen, silent during play.
- Status: st_slow, st_speed (buff), st_dr, st_heal (hot), st_poison (stink, poison) play at the target when the status goes on fresh. Refreshes are silent.
- Already wired through the SFX map since 16c.1: ui_cap, ui_attacked, ui_lost, ui_overtime, ui_ult_ready, ui_xp, ui_lvl, ui_chal.
- ui_count is not wired. The game has no pre-match countdown. 16c.8 adds the countdown.

## WP16c.7 - Integrator
- Map ambience moves into AU: AMAP holds the proto beds, event rates and IR length per map (hawker 1.1 s, voiddeck .7, wetmarket 1.5, carpark .35). AU.ambOn(map, verb) builds the beds on the amb bus with a 1.5 s fade in, and builds the IR for that map. AU.ambOff stops them.
- Events: AU.ambEv(dt) from step, each event at its per second rate, at a random point 6 to 30 m around the listener. All e_ ambience recipes are priority 5.
- Low tier (tierIdx 0): verb buffer null, so spatial() builds no reverb sends. setTier calls AU.setVerb, so an auto drop to Low mid-match drops the convolver too.
- The old hand-built hawker bed in ambStart and the flat 1.3 per second e_cup in step are removed.

## WP16c.8 - Integrator
- Menu and end screen music is now the kopitiam lounge from proto-audio: 98 bpm, C Am F G, 15 percent swing, seeded pluck walk. It is built from mu_bass, mu_pluck, mu_wood and mu_shaker through AU.play, so it obeys the voice cap.
- Final 30 s groove: 110 bpm, bass and woodblock only, at gain 0.35. It starts when the clock reaches 30 s and stops at the end of the match, so the sting plays alone.
- Countdown: ui_count three times, 0.25 s apart, then ui_go with the CHOPE YOUR TABLES! callout at 1.0 s. Play is not frozen during it.
- Win and lose stings were already wired through SFX.win and SFX.sad. They are unchanged.
- Removed the old tone, noise and voice synths and their globals. Only the old menu loop used them.

## WP16c.9 - Integrator
- Six volume sliders (Master, SFX, UI, Voice, Ambience, Music) in a Volume panel above the mute button. It shows on the menu, pause and end screens, like the mute button.
- Each slider calls AU.setVol. Values persist through the existing chope-audio-v1 key. M and the mute button stay the master mute.

## Hero porter (WP21 prep) - round 1
- proto-port/heroes-port.js: drop-in module that builds the 9 proto-look KayKit heroes (encik is engineer, auntie is tarik). Rendered through the WP16a toon, rim, outline and team-flag pipeline. Driven by the WP16b procedural animation, with the KayKit Idle clip as a base layer.
- proto-port/chope.port-test.html: playable demo, chope.html plus the module. Pick any hero, match against bots.
- Old models stay as the load-failure fallback. Draw calls 79 to 82 avg, 110 to 117 max. No texture leak across matches.
- Screenshots of all 9 heroes in proto-port/. Merge steps, perf, risks and requests in PORT.md. chope.html not changed.

## Hero porter (WP21 prep) - round 2
- CRITIQUE1.md items 1 to 10 and part of 12 done in kk-tail.js and build_port.py. Team band and collar back, tarik 18.2k to 9.7k tris, 5 to 10 draws per hero, dark colour lift, knee bend, KO idle fade, measured HP bar height.
- Item 11 left for the user. Rascal cap gap still open. Perf, scale and requests in PORT.md round 2. chope.html not changed.

## WP16c.10 - Integrator
- Wave 2 ability sounds wired. Each ability now has its own cast recipe.
- Debater: Order, Order! w2_ding (bell ticks stay w2_bell), Rebuttal w2_megaphone, Stay Back! w2_rostrum, Closing Statement w2_flutter.
- Tarik: Cup Toss w2_teh_splash (ally cup hit w2_teh_heal), Steam Off w2_steam (new), Have a Cup! w2_teh_heal (the dash follow-up is q_whoosh), Teh Tarik Rain w2_teh_ult then w2_teh_splash.
- Tea Stream: new w2_pour loop for the player, louder as the hold builds. Stops when the pour stops and in ambStop. Bots pour silently.
- Rider: Kick-Scoot Launch w2_scoot, Special Delivery w2_plunge (whistle) with the new w2_plunge_hit on landing, Food Parcel w2_parcel (new), Peak Hour Rush w2_rush (new).
- ULTS gains tarik, rider and debater.

## Weapon designer (WP21 prep) - round 1
- proto-weapons2/: viewer for held weapons on the 9 KayKit heroes, rendered through the WP16a pipeline sliced from chope.html. 3P and FP, blue and orange team, fire, emit and muzzle markers.
- One toggle switches between the current chope weapon models and a restyled KayKit set close to the current shapes and colours. The new FP view models are offered as an option. The current FP stays the default.
- Same draw calls as the current models. Gameplay muzzles are unchanged.
- Screenshots per hero in both modes and contact sheets are in proto-weapons2/. Design, sockets, emit points, perf, toggle and landing steps are in WEAPONS2.md. chope.html is not changed.

## WP20 - Integrator
- Bot stuck spikes on hawker (Rider). Three small changes in the bot code.
- A stuck hop drops the Rider perch, so he stops pressing on the same counter (A's fix A).
- Stuck checks skip a Rider holding on an awning. He holds still there on purpose and riderBot zeroes his move after the check, so those hops were false.
- On the ground within launch range with Kick-Scoot on cooldown, Rider gives up the perch instead of walking into the counter front.
- A's fix B (awnLock on leave) was tried and dropped. It did not lower the awning hops in 30 matches.

## Map redesigner (WP21 prep)
- New KayKit map viewer at proto-maps2/index.html. It builds all 4 maps through the WP16a pipeline with the current palette.
- 20 KayKit pieces used (19 Restaurant Bits, 1 Furniture Bits). Knight.glb is the scale reference.
- Gameplay boxes, spawns, zones, pickups and nav are unchanged. Colliders still come from mapSolids.
- Eye and top screenshots for all 4 maps in proto-maps2/. Per-piece layouts in proto-maps2/<id>.layout.json.
- MAPS2.md holds the layouts, perf notes, the single zip plan, 11 conflicts and 4 requests. Round 1 of 3, ready for the art critic.

## Weapon designer (WP21 prep) - round 2
- Worked through proto-weapons2/CRITIQUE1.md in rank order. Debater megaphone trimmed to .62 and moved to the collar, with the handle in her fist. The nsboy shooter now sits in the hand by its grip. Rascal star 1.4x, newspaper longer, off-hand props turned outward.
- rb() defaults to 1 segment. The restyle is now 0.4k to 1.65k tris per hero in 3P (round 1 was up to 3.3k). Draw calls are the same as the current models.
- One weapon material per hero so the hit flash stays per hero. Team accents wrap the part. Lifted darks, 16-sided rims, no shadows on small off-hand props.
- Both toggle options still work. New 3/4 front shots per hero, refreshed sheets, and a round 2 section in WEAPONS2.md. chope.html is not changed.

## Weapon designer (WP21 prep) - round 3
- Worked through proto-weapons2/CRITIQUE2.md. FP rider chopstick tips now sit on the sticks. The nsboy and rider team bands show past the stock and the fist. nsboy slide set to dz -.12.
- Walking_A and shoot-clip shots for all nine heroes in both options. The debater megaphone now rides her right hand, so the handle stays in her fist when she shoots.
- Rascal ruler wider and turned to show its ticks. Rider phone in a team case. Newsprint grey newspaper with a red masthead. Desk bell stands upright. Tarik at 16 sides, rider sticks cheaper (624 tris).
- WEAPONS2.md now opens with a landing checklist for chope.demo.html. chope.html and the porter files are not changed.

## WP20b - Integrator
- Ah Ma walker redesign (zimmer frame). Third person: four round legs, two side frames with a brace, a front crossbar, dark rubber hand grips at hip height, rubber feet on the back legs, two small wheels with forks on the front legs. Red basket kept on the front crossbar. The walking stick and the lime tennis-ball feet are gone.
- First person: round side rails and crossbar, dark grips under the hands. Basket unchanged.
- Walker is still the one merged 'prop' mesh at origin 0, 0, -.70, so it can carry over to another Ah Ma model. Animation, hitbox, range and damage unchanged.
- Walker 668 tris. Ah Ma total 4448 (want 4800, inside 15%). Mesh count 6, draw calls unchanged.

## Map redesigner (WP21 prep) - round 2
- Hawker now uses the legacy buildEnv look with KayKit tables, stools and counter clutter only. Clutter hides on Low.
- Wet market rebuilt as tiled slab stalls with drains, plastic crates, fish on ice and a bluer wet floor.
- kfit stretch clamp at 1.35 with a primitive fallback. Full-height sliced pillars. Ceiling underside lift.
- Carpark bays, lot numbers, stoppers, kerbs, plates and signs. Void deck pillar bands, letterboxes, RC board and drains.
- Knight at 0.895. New zone B eye view. 12 screenshots and 4 layouts reshot. Gameplay data unchanged. Details in MAPS2.md, Round 2.

## Hero porter (WP21 prep) - round 3
- CRITIQUE2.md fixes 1 to 10 done in kk-tail.js, build_port.py and the shots harness. KO limb drift fixed, and the KO flail now matches the old model (Idle freezes on KO, limbs aim along the old rig). Knee bend on crouch and slide only.
- Props bake into the body skin: 3 to 6 draws per hero, fewer main, prepass and shadow draws than the old models at Medium and High. Shader warm-up on the menu, castShadow kept across tier changes, dark lift 0.045, team bands on both arms, rascal cap raised.
- Fixed-camera and SwiftShader perf tables, budget and requests in PORT.md round 3. chope.html not changed.

## Map redesigner (WP21 prep) - round 3
- CRITIQUE2.md worked in rank order. Coral mat and car gone. The rendered hue check at 6 degrees finds no orange cluster over 2 m2 on any map.
- Void deck pillar band covers the mid ring. Wet market slabs carry goods, tiled wainscot walls, two-faced blade signs over the aisles. Lighter ceilings through new look.ceil. Grey blue car cabins, white bays, yellow DON'T ANYHOW plate.
- Noto Serif SC loads in the proto from fontsource on jsdelivr. Missing glyphs for the game HAN_TEXT listed in MAPS2.md Requests.
- Rascal and Ah Ma hero shots, head clip log, tree canopies and void deck shelter raised (art only).
- Landing checklist for chope.demo.html at the top of MAPS2.md. scratch/maps2/solids_check.mjs confirms colliders match the game's mapSolids on all four maps. chope.html not changed.

## Hero porter (WP21 prep) - round 4
- New proto-port/chope.demo.html (built by build_port.py from the test copy and demo-addon.js): WEAPONS2 props in third person, the fp toggle, MAPS2 art with game colliders, an all-bot match. Toggles by URL, buttons and F7, F8, F9.
- Solids check against the demo prints same for all 4 maps (164, 137, 72, 102).
- Bot match per map: 60 fps, 87 to 110 max draws, 0 console errors.
- Demo gate PASS 7 FAIL 1 (G7 step cost 0.159 ms, same on the test copy). wpm PASS 5.
- Recolour cache: KK play click 29 to 50 ms, was 95 to 151 ms.
- chope.html not changed. How to open the demo is at the top of PORT.md.


## WP21a - Integrator
- KayKit heroes landed from proto-port/heroes-port.js (PORT.md READY round 5): GLTFLoader, SkeletonUtils and RoundedBoxGeometry imports, module before the boot line, KK.preload() in boot, KK.warm() before the first frame, HP bar at e.mesh.barY.
- WEAPONS2 held weapons landed in the same step, because they attach to the KayKit hand bones. weapons.js is inlined as the WPN closure, so chope.html stays one file. demoWeapons() runs in mesh(), castShadow keep for userData.wpn, VIEWMODELS exposes make, arm, add3, aim.
- Defaults: new 3P weapons, current FP viewmodels. ?q&weapons=current and ?q&fp=new are test flags only. No F7 to F9, no spectator, no demo buttons.
- Edit script wp8/edit_wp21a.py builds from chope.pre-wp21.html, so a rerun pulls the latest proto files. Snapshot chope.wp21a.html.

## WP21b - Integrator
- MAPS2 art landed for hawker, voiddeck and wetmarket: the ENV2 closure from proto-maps2/index.html (KayKit pieces, kitTools, buildMapEnv, buildHawkerLegacy), the map JSON from proto-maps2/maps, demoMapsReady after KK.preload. Game colliders unchanged (solids check same on all three).
- FONT_ZH is now "Noto Serif SC", "PingFang SC", "Microsoft YaHei", serif. HAN_TEXT gains the four glyphs of the do not feed the birds sign as \u escapes.
- maps=current is a test flag only with ?q. Snapshot chope.wp21b.html.

## WP21c - Integrator
- Carpark landed last with the 0.8 m deck raise (MAPS2.md landing step 4). In game the carpark has 110 obstacles, deck slab y0 3.0. Same script with WP21c=1. Snapshot chope.wp21c.html.

## WP21d - Integrator
- WEAPONS2 post-landing items 1 to 7 pulled (weapons.js). Hand props on the r and l sockets now take the TP entry scale (w.scale.setScalar(scale) before attach, K is 1 in chope).
- R59: KayKit recolour canvases capped at 512 (the atlas is 1024). Applied in wp8/edit_wp21a.py on top of heroes-port.js until the porter folds it into build_port.py.
- Snapshot chope.wp21d.html.

## WP22 - Integrator
- WP22.1: the player ult name callout, the player ult quote line (say(e,4)) and the enemy "Name: ULT incoming!" sub are gone. #callout and #sub stay, other messages use them. No CSS was popup only.
- New acceptance row wp22: all 9 heroes, abilities 1 to 3 and the ult, player and an enemy bot. It fails on chope.pre-wp22.html and passes now.
- Snapshot chope.wp22.html.

## WP21e - Integrator
- Porter polish round 2: the WP21 block is now proto-port/heroes-port.js as of p2. The demoWeapons and castShadow splices are redone. The R59 512 cap is an EDITS entry.
- Step cost A/B at 800x600, 6 samples per run, runs interleaved, load 3.4 to 3.8: with p2 0.104 to 0.114 ms min, without p2 0.109 to 0.110 ms min. Same cost. p2 stays. Log: logs/wp21e_ab.txt.
- Snapshot chope.wp21e.html.

## WP19 - Integrator
- Head: doctype, charset, viewport, a longer title, a 130 character description meta and a data: favicon. WP19.12 no longer fails on favicon.ico.
- Menu: Credits button, Full screen button (hidden when fullscreen is not enabled), version chip v0.9.0.
- #credits screen: Nigel Yeap, three.js with the MIT text, the three fonts under SIL OFL, KayKit by Kay Lousberg under CC0, a Back button.
- Load fallback: a classic script before the module shows #loadFail when the module fails to load or boot throws. Message from DEPLOY.md.
- Play (#goBtn) starts disabled and turns on at the end of boot. startMatch returns before boot. This fixes the map null throw.
- Touch-only devices keep Play disabled and show #touchWarn.
- Low-end hint: on the lowest tier, 5 s of play averaging under 30 fps shows one line about a smaller window. Once per page.
- window.__chope and #changeBtn exist only when the URL has a q param.
- Built chope-itch.zip locally: index.html at the root, the 46 KayKit files the page loads at the same paths, licenses/ with the three KayKit LICENSE.txt files. Not uploaded.
- Snapshot chope.wp19.html.

## WP18 - Integrator
- New #heroSel screen. Menu Play (#goBtn) opens it. Cards, Back and Start (#playBtn, calls startMatch). Change hero and #changeBtn open it with the last hero selected and focused.
- #heroes left the menu. The skin row stays. Compact cards: headshot, name, role, one line. #heroDet shows the full kit.
- Keys: arrows move focus, Enter or Space selects, Enter on the selected card starts, Escape goes back. No number keys.
- heroShot: each KayKit hero renders once after boot on layer 7 into a linear target, so no new programs. 9 shots in about 90 to 200 ms. The target is freed after. Data URLs stay in memory only.
- Hooks: __chope.heroShots, __chope.screen, __chope.heroShotMs, __chope.reshoot().
- Menu bar at 800 px wraps instead of clipping Map and Sound.
- Snapshot chope.wp18.html.

## Map redesigner (WP21 prep) - round 4
- Carpark deck raised 0.8 m: underside 2.2 to 3.0, deck top 3.2, perch 4.0, stairs 7 steps of 0.4. Ah Ma (2.68 m) fits under with 0.32 m to spare. Collider change as planned, 102 to 110. Full list in MAPS2.md landing step 4. Land it last.
- Void deck playground deck: probed with the game collide. Ah Ma cannot get stuck. She can walk under it today, so it is not off limits. No blocker added. A trial blocker and its costs are in MAPS2.md Requests (round 4).
- READY for B written at the top of the landing checklist.
- Polish: yellow box junction at carpark zone B, HEIGHT LIMIT 2.9M plate on the carpark deck. Art only. Perf numbers logged. No art cuts needed.


## Weapon designer, post-landing rounds 1 and 2 (2026-11-04)
- FP new: fire punch and reload pop on R.scale (free), forearm capsule to cylinder and thin bars to boxes. New FP tris now 800 to 1236, close to current. Same draws.
- 3P: r and l hand props honour the entry scale. Fight-distance scale bumps on seven primaries, brighter gym ball, cooler uncle newspaper.
- Viewer: d10 and d25 modes, kick shots, src=ck frozen source, no-store server. List for B at the top of WEAPONS2.md.

## Game feel designer (WP23) - rounds 1 to 3
- FEEL.md: 8 ranked feel changes and step list for B. Stacked damage numbers, head marker and ding, damage direction arc, MVP end shot, ult FOV punch and meter pop, respawn drop-in and killer HP, crosshair fire kick, smooth shake.
- proto-feel/build_feel.py: 26 anchored patches, all match the current chope.html once. Gated by FEEL, ?feel=0 is the before build.
- Cost: 0 draw calls, frame p95 16.7 ms both builds, per-event cost inside noise. 30 s smoke 0 errors.
- chope.html not changed. MVP end hold needs the user's call.

## Hero porter (WP21) - round 5 (2026-11-04)
- Step cost: rot() works from local quaternions, h.kk lost both full matrix passes, the Idle mixer has a distance and behind-camera LOD, three proto ticks lost their own matrix pass. Demo G7 0.093 and 0.106 ms, wp3 0.109 ms.
- PORT.md: READY for B section with the files and splices. B has landed it.
- Post-landing p1: blue ally rim, thicker team bands, chest kick on fire, head snap on hit. Fixed a pose tick that stacked the kick on uncle.
- Post-landing p2: melee heroes lunge forward on the strike, the head snap follows the hit direction.
- New test page proto-port/chope.post.html (landed game plus this module) and the recoil check mode in shots.js. Gate PASS 8 after p1. After p2 the Mac was under heavy load from other agents and the step cost read high on the unchanged landed copy too.

## Graphics quality director (WP23) - rounds 1 to 3 (2026-11-04)
- GFX2.md: ranked list and step list for B. Baked Medium sun shadows, painted sky in comp, quarter-res bloom with HDR glow, bird flock. Rim skipped.
- proto-gfx2/patches.py: 23 anchored edits on the demo copy, gated by ?g=. ?g=none is the before build.
- Cost: q=1 draws max 111, all maps 60 fps, 0 errors. GPU +1.2 to 2.6 ms at 4 MP. Low has no bloom.
- chope.html not changed. Sun direction per map needs the user call.

## WP18b - Integrator
- Hero screen at short heights: one `@media (max-height:620px)` rule trims padding, gaps and the detail panel text size. The panel max height is the viewport minus 100 px.
- At 800x600, 1024x600 and 1280x720 the page and the detail panel have 0 px overflow for all 9 heroes. The passive and the Q and C hints are in view.
- Applied on top of WP23 feel step 3. Gate 8/0, G7 0.1275 at load 1.4.
- Snapshot chope.wp18b.html.
- Debater headshot: the Rogue hair under the bob cap is now scaled to 0.9 in x and z (`crop(-.25,.9)`, was 1). The spiky hair tips no longer poke through the cap as dark bits. Same geometry count. Gate 8/0, G7 0.1197.

## WP23 feel - Integrator
- Landed the 26 patches from proto-feel/build_feel.py in the FEEL.md step order, one step at a time. All are gated by `FEEL` so `?feel=0` is the before build. Snapshots chope.wp23-0.html to chope.wp23-8.html, backups chope.pre-wp23-N.html.
- Step 0 (0, 1): FEEL flag and CSS. Both URLs boot with 0 errors.
- Step 1 (5, 6, 7): damage numbers stack per target. 3 hits of 18 give one `.dn.on` reading 54. With feel=0 there are 3.
- Step 2 (2, 3, 4): head hitmarker and head-kill ding. `.xh` reads `xh head`, then `xh`. `ui_head` plays on a head kill.
- Step 3 (8, 9, 10): damage direction arc. Rotation -2.554 for an enemy 6 m behind and 4 m left. Gone 1.1 s after the last hit.
- Step 4 (14 to 17): ult FOV. Min 72.7, max 80.8, back to 78 in 1 s. `#ab4` gets `gain`.
- Step 5 (11, 12): respawn FOV starts at 96.3 and settles to 78 in about .55 s. The death card shows "HP left".
- Step 6 (25): crosshair kick. NS Boy fire gives 1 running animation, still 1 after 20 fires. Melee heroes (Ah Ma) get none, as designed.
- Step 7 (18 to 24): MVP shot. At 1.2 s `#end` and the HUD are hidden and the camera is 3.3 m from the MVP. `#end` shows at 3.5 s, or at once on a pointerdown at .5 s.
- Step 7 integrator fix: `endGo` now removes its pointerdown and keydown listeners before the state check. A match left during the hold no longer leaves a stale listener that could show an old receipt later.
- Step 7 test fix: tests/acceptance.js G4 waits up to 3 s for `#end` after runMatch. The check itself is unchanged.
- Step 8 (13): smooth shake. Mean frame-to-frame camera x change 0.011 vs 0.0161 with feel=0 (8 runs each). Peak 0.0308 vs 0.0316.
- Gate 8/0 after every step (steps 3, 5 and 7 needed a rerun for the "no hero ahma" flake). G7 0.112 to 0.133.

## WP23 graphics - Integrator
- Landed GFX2 steps 0, 1, 2 and 5 from proto-gfx2/patches.py, one at a time, gate 8/0 after each.
- Step 0: test hook only under ?q, g= flag read only under ?q. P1 (__kk hook) skipped.
- Step 1: baked shadow (sm, st, rcv knobs dropped). shadowCalls 0, draws avg 73.5.
- Step 2: sky. skyK 1, draws avg 83.4, programs 32.
- Step 5: birds. Gate 8/0, G7 0.128 ms/step. wp5 textures 68, 68, 65, 72 against TEXN 72.
- Held: steps 3 and 4 (bloom and bloom sources). Bloom adds 2 render targets and wp5 read textures 70 to 75, over TEXN 72 about half the time. Budget kept, bloom held for a ruling.
- Per-map sun direction left alone (GFX2.md, needs the user).
- Final runAll: 1366 160/1, 800 160/1 (both the known match length band noise). wp19 9/0. Zip rebuilt locally, not uploaded.

## WP24 bloom toggle - Integrator
- Landed GFX2 steps 3 and 4 (bloom, bloom sources) from chope.gfx-3.html behind a Bloom button next to Quality in the menu and pause rows.
- Default off. Saved in the profile (bloom:false, existing try/catch save). Off on Low regardless of the setting. The button reads "Off on Low" there.
- Bloom off: no bloom render targets exist, bloomK 0, glow 1.5, VFX boost 0. Bloom on: two quarter-res half-float targets, glow 2.4, additive VFX x1.6 through a shared uniform, so the toggle needs no shader rebuild.
- New wp24 rows (3/3): off has no targets and textures within TEXN 72. On has targets, textures within 74 and 0 errors. 8 flips mid-match give exactly +2/-2 textures each, no reload, Low forces off. wp24 runs last because it flips tiers.
- Gate 8/0, G7 0.1243 ms. runAll 1366 162/2, 800 162/2. wp19 9/0.
- The 1366 fails are wp5 textures 75 (bloom off) and wp24 row 2 at 76/74. The default build was already over TEXN before WP24: chope.gfx-5.html read 74, 70, 70, 75, 71 against 76, 68, 75, 72, 70 for chope.html. Scene textures are steady at 37 to 39. The rest sits outside the scene and moves by about 7 between loads. Root cause not found. TEXN not changed.
- Per-map sun left alone. Zip rebuilt locally (67 entries, boot probe clean). Not uploaded.

## R63 shared Skeleton per rig - Integrator
- A's fix for the wp5 texture spread. In KK mesh(), after mergeSkinned, skinned meshes with the same bones and bone inverses now share one Skeleton. three makes one bone texture per Skeleton, so one texture per rig instead of one per clone.
- TEXN stays 72. wp5 textures over 5 fresh loads: 62, 63, 60, 59, 57 (was 68 to 76). Programs 32 to 34.
- Gate 8/0. Draws avg 70.3, max 108. G7 0.1403 ms/step at load about 3.5.
- wp24 3/0 (bloom on 64/74, flips still exactly +2/-2). runAll 1366 163/1, the one fail is the known wp8 length band noise. Console errors 0.
- Snapshot chope.r63.html, backup chope.pre-r63.html.

## WP26 step 1 multi-kill chop marks - Integrator
- Landed IDEAS.md step 1 from proto-ideas/build_ideas.py (built on the chope.r63.html base). Adds the IDEAS gate (?q&ideas=0 turns it off), i25el and i25multi.
- Gate 8/0. Draws avg 65.4, max 103. G7 0.1407 ms at load about 4.0. Console errors 0.
- Shot shots/wp26_1.png: three red seals under the crosshair after a triple kill. With ?q&ideas=0, #i25mk does not exist.
- wp5: programs 32, textures 64 (TEXN 72).
- Snapshot chope.wp26-1.html, backup chope.pre-wp26-1.html.

## WP26 step 2 nemesis chevron and revenge sting - Integrator
- Landed IDEAS.md step 2 (build_ideas.py 2 on the chope.r63.html base).
- Gate 8/0. Draws avg 64.0, max 96. G7 0.1442 ms at load about 2.4. wp5 programs 32, textures 60. Console errors 0.
- After death and respawn, player.nem is the killer and the chevron shows. It clears after the living-time window. With ?q&ideas=0 there is no nem and no #i25nem.
- Shot shots/wp26_2.png: gold chevron over the killer.
- Snapshot chope.wp26-2.html, backup chope.pre-wp26-2.html.

## WP26 step 3 receipt accolade stamps - Integrator
- Landed IDEAS.md step 3 (build_ideas.py 3 on the chope.r63.html base).
- Gate 8/0. Draws avg 66.8, max 98. G7 0.1278 ms at load about 4.4. wp5 programs 34, textures 62. Console errors 0.
- Player with 9 elims and 3 caps gets TABLE HOG and TOP CHOPE beside MVP. With ?q&ideas=0 the receipt has no .i25a.
- Shot shots/wp26_3.png. The stamps read TABLE HOG then TOP CHOPE, since each one is inserted right after the name.
- Snapshot chope.wp26-3.html, backup chope.pre-wp26-3.html.

## WP26 step 4 killable HP-bar flash, plus R64 - Integrator
- Landed IDEAS.md step 4 (build_ideas.py 4 on the chope.r63.html base) and A's R64: accolade stamps now insert after the last stamp, so they read in category order (TOP CHOPE, TABLE HOG).
- Gate 8/0. Draws avg 67.4, max 102. wp5 programs 32, textures 65. Console errors 0.
- G7 on chope.html: 0.1165 ms at load 3.2 and 0.1477 at load 4.15. On the step 3 build: 0.1265 at load 3.4. A pair at load 3.4 to 5.5 failed both builds (0.1868 and 0.1663), which is load noise. No clear cost from the flash.
- A 60 hit sets player.i25last to 60. An enemy on 50 hp shows a white bar (shots/wp26_4.png). With ?q&ideas=0 i25last is never set.
- Snapshot chope.wp26-4.html, backup chope.pre-wp26-4.html.

## Zip rebuild after WP26 - Integrator
- A passed WP26 steps 1 to 4 and R64. chope-itch.zip rebuilt locally per DEPLOY.md Zip layout from chope.wp26-4.html.
- unzip -l: 67 entries, index.html at the root, the 46 WP19.13 files (same list as the wp19 row), 3 KayKit LICENSE.txt under licenses/. Size 5,150,015 bytes (15,742,035 unpacked).
- Boot probe on build/index.html?q=2: no failed requests, match starts, 0 console errors. Not uploaded.

## WP27 S1 inert range code and test hook - Integrator
- proto-range/build_range.py rebuilt against chope.wp26-4.html: all 15 anchors found once. A copy in w27/pr applies a chosen patch list, so each step lands only its own patches.
- S1 = P3 (range block before startMatch) and P14 (__chope.range get and set).
- Gate 8/0. Draws avg 70.9, max 101. G7 0.1430 ms at load about 5.4 (passes, but read on a busy machine). __chope.range is false. Console errors 0.
- No shot. Nothing on screen changes.
- Snapshot chope.wp27-1.html, backup chope.pre-wp27-1.html.

## WP27 S2 menu entry and routes - Integrator
- S2 = P1 (Practice range chip), P2 (hidden Change hero in pause), P12 (three listeners), P13 (chip disabled on touch-only), on top of S1.
- Gate 8/0. Draws avg 63.7, max 93. G7 0.1273 ms at load about 3.6. Console errors 0.
- "Chope a seat" then Start gives a normal match: 6 ents, range false.
- Shots shots/wp27_2_1366.png and shots/wp27_2_800.png. No page overflow at either size (scroll size equals the window). The chip sits beside "Chope a seat" in the button row, not under it.
- Snapshot chope.wp27-2.html, backup chope.pre-wp27-2.html.

## WP27 S3 the range - Integrator
- S3 adds P0 (CSS), P4 (no allies), P5 (rangeStart), P9 (dummy brain), P10 (rangeTick), P11 (respawn at post).
- Range on hawker: 4 ents, 0 allies. Challenge, score and objective hidden. Zone meshes hidden. Dummies at 7.5, 16.9 and 26.5 m, all in sight. A KO dummy is back at its post (distance 0) after 2.6 s. Score 0:0, timer 300, ult full. Range draws 62, programs 32, textures 56. Console errors 0.
- Gate 8/0. Draws avg 68.5, max 103. G7 0.1332 ms at load about 4.1 to 5.9.
- Shot shots/wp27_3_range_hawker.png: three dummies in view, no score bar, ult READY.
- Snapshot chope.wp27-3.html, backup chope.pre-wp27-3.html.

## WP27 S4 quiet start, plus challenge guard - Integrator
- S4 adds P6, P7 and P8 (all 15 build_range.py patches now in). It also adds the coordinator-required guard `if(RANGE)return;` at the top of progressChallenge.
- First 5 s, four fresh iframes per profile: the range (fresh and played profile) shows no "CHOPE YOUR TABLES!" and no hint. A normal match shows the callout and the hint for both profiles (the games<2 ring hint and the keys14 new-keys hint).
- Challenge: range kills give no "Challenge complete". In a normal match with a fresh profile the challenge bar moved after kills. The played-profile match rolled a non-elims challenge, so kills did not move it there.
- Open: the range still shows "Ultimate ready! Press 4" once at start, because rangeTick fills the ult. Flagged to A.
- Gate 8/0 in a fresh page. Draws avg 72.2, max 104. G7 0.1357 ms at load about 4.5 to 5.2.
- Shot shots/wp27_4_start2s.png: clean screen at 2 s.
- Snapshot chope.wp27-4.html, backup chope.pre-wp27-4.html.

## WP27 S5 checks, plus R66 ult-ready guard - Integrator
- R66 (coordinator ruling): the ult-ready cue skips flash, sound and "Ultimate ready! Press 4" when RANGE is set. The ult icon still shows READY 100% in the range.
- Ult cue: in the range, no sub-title in the 12 s after an ult, through the refill at 3.3 s. A normal match still shows "Ultimate ready! Press 4" when the ult fills.
- Range per map (draws avg/max): hawker 62, voiddeck 70, wetmarket 76.4/81, carpark 82.7/83. Programs 32 to 33, textures 51 to 53. KO then back at the post on all 4 maps.
- Dummies in sight on all maps. One voiddeck run read the strafer at 24.1 m NOLOS. Three reruns read it in sight at 17.2 to 20.3 m. The strafe walks it past cover for a moment.
- Normal match: draws avg 93.9, max 96, ran to the end, games +1. Range draws stay under match draws. Peaks well under 180.
- Change hero from pause: hero select shows, state is menu between, ahma to gym, back in the range with 4 ents.
- Profile diff after a range session with change hero: hero only.
- Gate 8/0 in a fresh page. G6 avg 68.6, max 105. G7 0.1200 ms at load about 3.8. wp5 programs 32, textures 66. 0 console errors.
- Shots: shots/wp27_5_range_{hawker,voiddeck,wetmarket,carpark,ult,pause}.png and shots/wp27_5_normal_hawker.png.
- Snapshot chope.wp27-5.html, backup chope.pre-wp27-5.html.

## Zip rebuild after WP27 - Integrator
- A passed WP27 S5 (R66 is the coordinator's ruling). chope-itch.zip rebuilt locally per DEPLOY.md Zip layout from chope.wp27-5.html.
- unzip -l: 67 entries, index.html at the root, 3 licenses under licenses/. Size 5,150,933 bytes (15,744,752 unpacked).
- Boot probe on build/index.html?q=2: no failed requests, match starts, 0 console errors. Not uploaded.

## Rebindable keys - Coordinator
- Keys chip in the menu and pause rows opens a panel. 14 actions. Click, press a key, Esc cancels, a key in use swaps. Saved in profile.binds.
- Input layer only: REMAP turns the pressed code into the default code, so game logic is unchanged. Hint row, HUD slot keys, hero card and pause kit show the bound keys.
- Snapshot chope.pre-keys.html, result chope.keys.html. Zip rebuilt (67 entries, 5,152,862 bytes), copied to ~/Downloads. Not uploaded.

## Settings, gfx3 and minified build - Coordinator
- Keys panel is now Settings with 3 tabs: Controls (the 14 binds), Graphics, Sound (6 sliders). Same chip in the menu and pause rows.
- Bloom on by default. One-time migration sets profile.bloom=true for old saves (profile.bl2 flag).
- gfx3: per-map sun direction. Carpark sun now sits at (-30,14,12) to match its painted sky glow. Others about the same.
- gfx3: slow cloud shadows on voiddeck (.26) and carpark (.32), inside the existing comp pass. Weaker in shade, fade out from 40 to 80 m. No new programs.
- Gate on source 8/0. G6 avg 69.2 max 105. G7 0.1445 ms. Programs 35, textures 58, tris 198k.
- build/index.html is now minified with esbuild (module 640 KB to 489 KB). chope.html stays readable. Re-run the minify step after any chope.html change. Do not copy chope.html over build/index.html.
- Minified build: gate 8/0, G6 avg 63.4 max 99, G7 0.1057 ms, 0 errors. Plain load (no ?q) boots 9 heroes with no test hooks.
- Snapshots chope.pre-settings.html, chope.pre-gfx3.html. Zip rebuilt (67 entries, 5,107,598 bytes), copied to ~/Downloads. Not uploaded.

## NS Boy swap, headshot package, HUD bust, zip - Coordinator
- NS Boy: Live Firing is the ult again (5 s of bands, 42 each, head x1.5, no reload). The old ult rocket barrage is now Matador Strike (ability 3), toned down: 3 rockets, 45 centre to 15 edge, smaller FX. Snapshot chope.pre-nsult.html.
- Headshots (snapshot chope.pre-hsmerge.html), applied hs1 then hs3 then hs2:
  - hs1: head sphere follows the head bone (crouch, run, air, slide), r .43 x size, chest leans, neck tie rule, projectiles test the head. Head rate on the visible face is now 97 to 100% in every stance. See HITBOX.md.
  - hs3: head multipliers per weapon, +50% ult charge on head hits, head kill takes 1 s off cd1 to cd3, bot head chance scaled to head size. See HEADREWARD.md.
  - hs2: head tink pitch chain, short hitStop, kaya pop, kill X, kill feed head mark, ability icon flash on the cooldown cut. Off with ?hs2=0. See HEADFEEL.md.
  - tests/acceptance.js wpm crouch test: standing ray moved from 1.55 to 1.70 x size, since 1.55 now hits the crouched head for real.
- HUD medal shows the hero bust (SHOTS) instead of the han character. Scoreboard still uses han.
- Checks: gate 8/0 on source (G7 .134 ms) and on the minified build (G7 .116 ms, draw calls avg 67.5). wpm 5/0. 10 autopilot matches: bot dps on player 15.7 (was about 18).
- Minified module 643 KB to 491 KB. chope-itch.zip rebuilt, 67 entries, copied to ~/Downloads.

## 2026-11-04 itch build: domain lock and copyright
- Menu version tag and Credits now carry "© 2026 Nigel Yeap. All rights reserved."
- itch build only: tmp/lock.js is injected into the minified module. Off itch hosts (itch.zone, hwcdn.net, itch.io, localhost) it shows a card linking to https://glyphys.itch.io/chope. chope.html and the artifact stay unlocked.
- Build with tmp/build_itch.sh. Verified boot on 127.0.0.1 with 0 errors and the lock card on [::1].

## 2026-11-04 Main menu redesign (MENU.md) - menu builder
- Step 1, grid and top bar. #menu is now a CSS grid. New header.mtop holds the tab bar (Play, Practice range, Settings, Credits), the player card (#pLvl, #pXp, #pXpT, #pWins) and the Full screen .ubtn. The old blurb, skins and play row sit in a temporary .mside. All new rules are scoped to #menu.
- Checks: Settings opens #keysDlg and all 3 tabs switch. Credits Back returns focus to #creditsBtn. Practice range opens hero select. PLAY starts a match. Gate 8/0 (G7 .135 ms), node --check ok, 0 console errors. Snapshots chope.pre-menu-1.html and chope.menu-1.html.
- Test note: in the hidden browser pane the boot can stall on Image.decode until a screenshot is taken. Not a game bug. Take one screenshot after load.
- Step 2, left column. New .mbrand (logo, tag) and .mmatch (Next match label, .mopts with the map and bots .opt cards, #touchWarn, #goBtn with a label span and an ink .go play disc). The old .playrow is gone from the menu. .playrow CSS stays for hero select. Ver, skins and key hints sit in a temporary .mtmp.
- Checks: Map cycles through 4 arenas and back. Bots cycles and the pause copy matches. #goBtn is disabled in the markup and enabled at boot. Back and Escape from hero select return focus to #goBtn. Gate 8/0 (G7 .136 ms, one noisy run at .152), 0 errors. Snapshots chope.pre-menu-2.html and chope.menu-2.html.
- Step 3, footer. #keyHint and .ver now sit in footer.mfoot, key hints left and version right, with 150px clear for #muteBtn.
- Checks: rebinding Jump to Z in Settings updates the hint, Reset keys puts it back. Version line reads "Chope! v0.9.0 · © 2026 Nigel Yeap". Gate 8/0 (G7 .127 ms), 0 errors. Snapshots chope.pre-menu-3.html and chope.menu-3.html.
- Step 4, hero stage. New section#menuHero: faint han characters, pastel enamel plate, hidden #menuHeroImg, red signboard with name and role. Gear skin label and #skins moved into .mgear under the hero. New syncMenuHero() fills name, role, han and --field from profile.hero. renderMenu and showScreen('#menu') call it.
- Checks: picking Stinky Uncle then Back shows his name, role, han and sage plate. Makan Rider then Escape shows lime. Skins still select. Gate 8/0 (G7 .132 ms), 0 errors. Snapshots chope.pre-menu-4.html and chope.menu-4.html.
- Step 5, hero portrait. heroShot(hk,P) takes optional portrait settings and renders into its own 512px target, then frees it. Without P it works as before. New heroPortrait(k) caches one data URL per hero, and syncMenuHero shows it in #menuHeroImg. PCAM holds per-hero camera tweaks (uncle and rider sit a little higher). HEROES size is left out because the shot rig does not scale the model. __chope gains portrait, PORTRAIT and PCAM for tuning.
- Checks: all 9 heroes rendered in a test grid. Heads and feet sit inside the disc. Rendering all 9 took 130 ms. Programs stay at 33 and textures at 50 after all 9. Smoke check passes. Gate 8/0 (G7 .107 ms), 0 errors. Snapshots chope.pre-menu-5.html and chope.menu-5.html.
- Step 6, arrow-key focus. menuNav from the mock moves focus to the nearest enabled menu button in the arrow direction. It listens on document and returns early when #menu is hidden or a dialog is open, so focus can also recover from body to #goBtn. #goBtn takes focus at boot once it is enabled, except on touch-only devices. The Map and Bots buttons now blur only on pointer clicks (e.detail), so Enter and Space keep keyboard focus on them.
- Checks: from PLAY, Up reaches Map and Up again reaches Practice range. Right walks Settings, Credits and ends on Full screen. Real Enter cycles the map and real Space cycles bots with focus kept. Arrows inside Settings and during a match do nothing to the menu. Smoke check passes. Gate 8/0 (G7 .130 ms, one noisy run at .158), 0 errors. Snapshots chope.pre-menu-6.html and chope.menu-6.html.
- Step 7, responsive rules. The mock's max-height:640px and max-width:760px rules landed with #menu prefixes. On phones the menu stacks top bar, brand, hero, gear and match, then the footer. Key hints hide on phones and short windows. The plate disc now sizes with container units (min(78cqh,92cqw)) so it stays round when the hero column is narrow. It went oval at 800x600 before.
- Checks at 1280x720, 1280x600, 800x600, 390x844 and 375x667: no horizontal scroll, all 4 tabs in view, PLAY fully visible, #muteBtn clear of PLAY and the version line. 375x667 has 7px of vertical scroll inside #menu. Smoke check passes. Gate 8/0 (G7 .136 ms), 0 errors. Snapshots chope.pre-menu-7.html and chope.menu-7.html.
- Build. Rebuilt build/index.html (551,917 bytes) and chope-itch.zip (5,111,855 bytes, 67 files) with tmp/build_itch.sh. build/index.html boots with 0 errors, shows the portrait, and PLAY has focus. Copied the zip to ~/Downloads/chope-itch.zip.
- Shots in shots/: menu-1280x720.jpg, menu-390x844.jpg, menu-hero-uncle.jpg, menu-hero-rider.jpg and menu-hero-rascal.jpg. JPEG quality 70, taken with local headless Chrome through tmp/cdpshot.mjs. tmp/shot.html seeds the profile hero first.

## 2026-11-04 Rascal menu portrait
- PCAM.rascal {z:8,ly:.6}: camera pulled back and figure raised, so his feet clear the name plate and the cap sits like Ah Ma's bun. Snapshot chope.pre-rascalcam.html.

## Four roles
- Roles are now Support (green), Tank (yellow), Damage (red), Utility (blue). Gym Hunk is Tank. Uncle, Engineer and Debater are Utility. NS Boy, Rider and Rascal are Damage.
- The role pill and a strip under the hero card are coloured on hero select only. The menu plate is unchanged.
- Bot hold spots now key on the hero (HOLD_ROLE by hk), so bot behaviour is the same as before. Snapshot chope.pre-roles.html.

## 2026-11-04 Classroom block map - maps3 designer
- New fifth map, Classroom Block Level 5, in proto only. chope.html is untouched. MAPS3.md is READY for B with the landing checklist and splice points.
- proto-maps3/gen.py writes maps/classroom.json. Size 50x36, mirror "z", 150 solids, 53 nodes, 16 holds. Zones in classroom 3 of each wing and mid bridge.
- proto-maps3/patch.py builds chope.classroom.html: mirror "z" in expandMap, map.fall death volume with push credit, open gap floor, instanced desks (one draw call).
- Checks: the four shipped maps expand the same (mirror_check ALL OK). Gate 8/0 on classroom and hawker. 3 bot matches, 0 unstick hops, 0 errors. Mean spawn to zone walk 7.3 s against 4.6 to 5.6 s on the others.
- Shots: shots/classroom-overview.jpg, shots/classroom-classroom.jpg, shots/classroom-bridge.jpg.

## 2026-11-04 Wave 3 heroes - heroes3 designer
- Two new Damage heroes in proto only: Long Lens Lim (lens, sniper) and The Siaolang (siao, melee assassin). chope.html is untouched. HEROES3.md is READY for B with the spec, bot rules, HUD.KITS entries and 66 splice points.
- New shared RMB scope. Lim 4x, NS Boy 1.75x. NS Boy full head is now 102 unscoped and 116 scoped, and he moves 25% slower while scoped.
- proto-heroes3/build3.py builds proto-heroes3/chope.h3.html. KayKit models (Barbarian plus Knight head for Lim, Rogue for the Siaolang), first and third person weapons, a hornbill mesh for Bird Escape.
- Checks: gate 8/0, G6 avg 61.9 max 94, G7 0.1138 ms. Duels: Lim 46%, Siaolang 45%. Lim counters Debater (90%), the Siaolang counters Lim (89%), Ah Ma and Gym Hunk counter the Siaolang.
- Shots: shots/h3-lineup.jpg, shots/h3-scope.jpg, shots/h3-bird.jpg.

## 2026-11-05 Classroom block v2 - maps3 designer
- Proto only, chope.html untouched. MAPS3.md "v2 revision" section is READY for B.
- 40 single desks per room in pairs, 5 rows facing the whiteboard, teacher desk in the front corner, a bag on every chair. 280 desks, still one instanced draw call. Window lane and centre aisle are 1.5 m, checked at r .54.
- New solid flag `m`: collide uses it, wallDist skips it unless the caller passes mv=1 (8 bot movement sites). Each window bay has a full height `im` blocker. Shots and sight pass, walking and jumping do not.
- Bridge planters shortened to 1.6 m to cut bot hops at zone B.
- Checks: mirror_check ALL OK. win.js and desk.js probes pass. Gate classroom G1 to G5 and G8 PASS, G6 68.3 and 75.8 over two runs (limit 74, fixed views equal to v1), G7 fails under load on every map including the v1 control. Bot matches 0,0,0 and 0,0,1 hops.
- Shots: shots/classroom-v2-front.jpg, shots/classroom-v2-back.jpg, shots/classroom-v2-window.jpg.

## 2026-11-05 Classroom v1, assist fix, wave 3 heroes landed - Orchestrator B
- Classroom Block Level 5 (v1) is in chope.html, from MAPS3.md and proto-maps3/patch.py. No base tag. The four older maps expand the same.
- kill(): a player who falls to their own death no longer gives a heal assist to teammates who healed them.
- Long Lens Lim (lens) and The Siaolang (siao) are in chope.html, from HEROES3.md. All 66 splices, the proto rmb test hook left out.
- Version v0.10.0.
- Checks: classroom 8/0 at q=1. G6 61 to 68 avg on every run. G7 fails only under machine load 5 to 25, and the old page reads the same under the same load. 0 console errors. Bot matches end normally with 0 or 1 unstick hops. Details in INTEGRATION.md "Classroom v1, assist fix, HEROES3 - B notes".
- Open: G7 at load under 4. smoke.js and bal.js not run on the landed page.

## 2026-11-05 Classroom v2 landed - Orchestrator B
- Classroom v2 is in chope.html from MAPS3.md "v2 revision": 280 paired desks with school bags, a teacher desk, window bays you can shoot and see through but not walk or jump through (solid flag m), shorter bridge planters, moved nav nodes.
- The four older maps expand the same. win.js and desk.js pass.
- Checks: classroom gate 8/0 once and 7/1 twice on G7 under load 8 to 16. G6 avg 63.7 to 70.3. 9 bot matches end by score with 0 falls and 0 errors.
- G7 at load 3.5 to 3.8: classroom 0.1317 and 0.1353, hawker 0.1180 and 0.1360. PASS.
- Open: bot stuck count about 1.6 a match against 0.8 on v1, none at the windows. wp5 textures hit 74 once (TEXN 72), on hawker, which v2 does not touch.

## 2026-11-05 Long Lens Lim headshot buff - Orchestrator B
- User request. Lim full-charge headshot multiplier is now x2.25 (was x1.75), so a full head does 180 (was 140). Golden Ratio heads also use x2.25, 180. Part charge head stays x1.5. Burst Mode stays x1.5. NS Boy is unchanged.
- Kit text and HEROES3.md now say full head 180 and Golden Ratio head x2.25. Snapshot chope.pre-lenshead.html.
- Frozen-target probe (wp8/lenshead.js, 6 m): Lim full head 180, full body 80, tap head 45, Golden Ratio head 180. Before: 140, 80, 45, 140. NS Boy 102, 58, 39 on both pages.
- A full-charge headshot now kills every hero at 180 HP or less in one shot: NS Boy, Debater, Rider, Rascal, Lim, the Siaolang, Uncle, Engineer and Teh Tarik Auntie. Ah Ma (300) and Gym Hunk (275) survive one.
- 2 bot matches with Lim on hawker: 12 elims 6 deaths (100-34), 18 elims 8 deaths (100-75). 13 one-shot kills from 180 hits. Same probe before the change: 16/7 and 24/9, with 2 one-shots (both on Rascal, 137 HP).
- node --check passes, ASCII only. Standard gate 7/1, G6 avg 69.4. G7 0.3555 at load about 10, the same load fail seen all session.

## 2026-11-05 Classroom block v3 stuck fixes - maps3 designer
- Proto only. MAPS3.md "v3 follow-up" is READY for B: a classroom literal swap, plus an optional `,1` on the Ah Ma seat rush slam check so window bays count as walls.
- Corridor columns are now 0.3 m deep and the plants sit against the railing. The tank hold, sniper hold, assassin hold and teh pickup moved out of corners. Desks and lanes unchanged.
- Bot stuck moments 0.75 a match over 16 matches, down from 1.38 on landed v2. Gate classroom and hawker G1 to G6 and G8 PASS, classroom G7 .162 once, .115 to .124 on repeats.

## 2026-11-05 Classroom v3 landed, zip rebuilt - Orchestrator B
- Classroom v3 from MAPS3.md "v3 follow-up": the new classroom literal (thinner railing columns, plants on the railing, moved tank, sniper and assassin holds and teh pickup) and the Ah Ma seat rush slam now counts window bays as walls (wallDist mv=1). proto-maps3/dbg.py not landed. Snapshots chope.pre-classroom-v3.html and chope.classroom-v3.html.
- mirror_check ALL OK, older maps the same. node --check passes, ASCII only. Standard gate 7/1, G6 avg 58.4, G7 0.4043 at load about 9. g7 pairs (classroom, hawker) 0.1780/0.1535 at load 4.2 and 0.1568/0.1712 at load 10. Load did not hold under 4, so G7 stays owed.
- 9 classroom bot matches: stuck 1,1,1,0,2,0,1,1,0, mean 0.78 (v2 was 1.6). Falls 0, pushes 0, 0 errors.
- chope-itch.zip rebuilt with tmp/build_itch.sh: 67 files, 5,120,751 bytes, 15,651,773 unpacked. build/index.html boots and the window probe passes on it.

## 2026-11-05 ART3 landed (toon, golden hour grade, new Ah Ma) - Orchestrator B
- User approved the new Ah Ma. proto-art3/build.py --land on the classroom v3 chope.html: land.diff 28 added, 4 removed, 6 hunks, ASCII. heroes/ahma.glb is proto-art3/ahma_v2.glb (3,144,644 bytes). Snapshots chope.pre-art3.html and chope.art3.html.
- Flags: no param is all on. ?a3=none is the old game. ?a3=toon,grade keeps the old Ah Ma.
- In game (wp8/a3m.js, both teams Ah Ma): the new model loads (a3kit), piping takes the team colour (388 blue verts on team 1, 520 orange on team 2), no magenta key left, no torus bands. The mixer plays Idle. Run and attack are the procedural rig copied onto the bones, as for every KayKit hero: arm moves up to 1.25 rad, leg up to 0.88 rad, no T-pose. The glb carries Idle, Running_A, Walking_A, 1H_Melee_Attack_Chop and Death_A.
- Enemy outline uniform is #ff2f5e with the grade on and #ff5a1f with ?a3=none. Old Ah Ma comes back with ?a3=none (bands present, old look). The enemy rim tint is 0xff4d6d, a separate thing from the outline.
- Programs 34 on, 33 with ?a3=none (+1, in budget). Draws 84 against 85 on hawker.
- 90 s Ah Ma bot match on each map, 0 console errors: hawker 6-75, voiddeck 27-79, wetmarket 41-49, carpark 47-44, classroom 43-66.
- node --check passes. Standard gate 7/1, G6 avg 58.6, max 91. G7 0.3340 at load about 16 to 20.
- G7 pairs (classroom, hawker) at q=1: none 0.199/0.240 (load 15), on 0.304/0.230 (load 11), none 0.261/0.290 (load 18), on 0.473/0.408 (load 18). Too noisy to read. The art agent's own paired run had on and none level. G7 stays owed until load holds under 4.
- chope-itch.zip rebuilt with tmp/build_itch.sh (run with zsh). build/heroes/ahma.glb added, so the zip now has 69 files, 6,106,863 bytes, 18,799,736 unpacked. build/index.html (592,231 bytes) boots, loads the new Ah Ma, and runs a 30 s hawker match with 0 errors.

## 2026-11-05 Siaolang v2 - wave 3 hero designer
- Proto only. HEROES3.md section 12 is READY for B: 18 exact-once reps in proto-heroes3/siao2.py (rep 18 is test only). New feral uncle model with glasses, gut, drool and a hunched run. Predator shows shimmer arms, an edge haze and a timer to its owner, and any damage pops it. Stun is hold to aim with a floor wedge that matches the hit test.
- Smoke: 1200 samples, 0 mismatches between hits, wedge and decal. Gate PASS 8, G6 avg 60.9, G7 0.1128 at load about 4. 2 Siaolang bot matches ended 100-60 and 64-100 with 0 errors. Cost +2 programs, +1 texture, +1 draw only while a wedge shows.

## 2026-11-05 Siaolang v2 landed, v0.11.0 - Orchestrator B
- User request. HEROES3.md section 12 by proto-heroes3/siao2.py against the ART3 chope.html (md5 a74c41f753d267eec87fe235da580ee3, the same bytes as chope.art3.html). "18 reps ok". Rep 18 (the s2 test hook) is left out. Version v0.11.0. Snapshots chope.pre-siao2.html and chope.siao2.html.
- Programs were the risk. As built, wp5 hit 37 (limit 36). Two program keys were new: 'rim1s' for the shimmer arms, and a one-sided MeshBasic for the stun wedge. Fixes, both in this landing:
  - The wedge material is DoubleSide with forceSinglePass, so it shares the existing double-sided transparent MeshBasic program. No extra draw.
  - rimify now carries the shimmer for every rim1 material: wob and wt (vertex wobble) and rimOp (a screen stipple fade that discards pixels while rimOp is under 1). Defaults 0, 0, 1 leave every other hero unchanged. shimmerVM is gone, the Siaolang arms stay opaque rim1, and predHud drives rimOp where it set opacity. The arms read see-through as a fine stipple.
- Programs after the fix, same scene on both pages: hawker Siaolang mirror 34/34, siao+tarik+engineer vs siao+ahma+lens 36/36, two more comps 35/35 and 36/36. wp5 on the landed page 36, 34, 36 (base 34 to 36). Textures up to 69, +1 at most (TEXN 72).
- Designer smoke (proto-heroes3/s2smoke.js on a copy with the s2 hook, reading rimOp for opacity): shimmer overlay, "INVISIBLE 4.7 s", wob .006, op .45, rim 1.23, arms on rim1. Break on hit, enemy glimpse 3/90 frames, aim and flash decal, 1200 shape samples with 0 mismatches.
- node --check passes, ASCII only. Standard gate 7/1, G6 avg 66.6 max 106, G7 0.2723 at load about 12 to 15.
- 2 bot matches, Siaolang on both teams (proto-heroes3/s2bots.js on chope.html): 79-100 (Predator 7 and 13, stuns 13 and 13, leaps 2 and 2), 40-100 (Predator 4 and 8, stuns 9 and 8). 0 console errors.
- G7 (q=1, 1280x720): at load 3.46 chope.html scored classroom 0.1217, hawker 0.1193. That passes 0.15. The earlier pairs at load 3.66 to 6.96 spread from 0.11 to 0.42 on both pages, the old page included, so they were logged as noise (wp8/s2g7.out, wp8/s2g7b.out).
- A review: PASS. Watch item: wp5 is at 36 programs, so there is no headroom for the next hero. wp5 tris 251,471 is just over 250k. Sniff subtitle shows quotes around asterisk lines (cosmetic).
- Zip rebuilt: 69 files, md5 0b779b8ea412ab8172497c6c0555154c, copied to ~/Downloads/chope-itch.zip. Not published.

## 2026-11-05 Sniff subtitle quotes fix - Orchestrator B
- say() no longer wraps lines that start with an asterisk in quotes. Siaolang shows *sniff sniff* bare. Spoken lines keep their quotes. One line in the shared say().
- Snapshots: chope.pre-sniffq.html and chope.sniffq.html. md5 0362e0c8acc3dbbb6d0ee49dae8991be. Probe: wp8/sayq.js.
- Gate 7/1. G6 avg 59.7, max 92. G7 0.4445 at load 13.85, logged and not counted. Boot 0 errors. Zip not rebuilt.

## 2026-11-05 Ability icons v2 landed (44 icons, greyscale cooldown) - Orchestrator B
- Source proto-icons/icons2.js, pasted as the IC2 block before esc in the HUD IIFE. icons2_before.js was not landed.
- sprite() appends IC2.sprite(), which emits 44 chud-x-KEY symbols. The 47 old symbols stay.
- AB2 map comes from proto-icons/keymap.js (11 heroes x 4). The ic2 helper emits svg.ic.x2.
- Only setHero uses the new icons, for the 3 slots and the ult. The kill feed and status chips keep the old line icons. KITS ab keys are unchanged.
- Cooldown: .chud .slot.cool svg.ic.x2{opacity:1;filter:grayscale(1) contrast(.75) brightness(1.08)}. The ult has no filter.
- Probe wp8/ic2.js: all 11 heroes show 4 of 4 x2 icons, every symbol resolves, the cooldown slot computes the grayscale filter at opacity 1, the ult filter is none, 0 errors.
- Page grew 11.7 KB (760266 to 771951 bytes). The icons are DOM SVG and add no GL programs. wp5 programs 34 to 35 and textures 60 to 65, against the old page at 36 and 65 on the same runs.
- Gate 7/1. G6 avg 63.1, max 92. G7 0.2995 at load 13.08, logged and not counted. Boot 0 errors. ASCII clean.
- md5 c5b06f1f483e5231fa9f4fb50bfc17ef. Snapshots chope.pre-icons2.html and chope.icons2.html. Shots shots/icons/landed_ahma.jpg, landed_siao.jpg, landed_rider.jpg. Zip not rebuilt.
- A review: PASS (INTEGRATION.md line 616). A's own wp5 run: programs 34, textures 56, tris 200,685, all within the caps.
- G7 rerun on md5 c5b06f1f (q=1, 1280x720, wp8/icg7.out). Under load 4: 0.1678/0.1642 at 3.26 (fail), then 0.1330/0.1408 at 3.55 (pass). The pre-icons page at 3.44 gave 0.1550/0.1350. Runs at load 4.6 to 5.6 all passed at 0.11 to 0.15. The spread matches the old page, so it is noise, not the icons.

## 2026-11-05 Perf step 1: shadow camera copy without children - Orchestrator B
- postRender line 1374: shCam.copy(camera) is now shCam.copy(camera,false). Per PERF.md root cause 1, the old call cloned the viewmodel under shCam every High frame.
- md5 1bea70b4bcca14e6a513b45231902377. Snapshots chope.pre-perf1.html and chope.perf1.html.
- High hawker soak, 2 matches (proto-perf/b_soak.mjs on a test-only copy with the PERF-PROBE lines, proto-perf/b_p1probe.html, not landed). Heap after GC 36.2, 36.4, 36.5, 36.7 in match 1, then 38.6 to 38.8 in match 2. The old page in the same harness: 41.9, 48.5, 54.8, 60.9 within match 1. Programs 36, textures 65, 0 errors. A no-probe soak (shots/perf/b_p1soak.json) also ran with 0 errors, programs 36, tier 2.
- Canvas-only seeded shots (proto-perf/b_shot.mjs) at 6, 20, 45 and 90 s: 0 pixels changed against the old page (shots/perf/bp0_c*.png vs bp1_c*.png).
- Gate 7/1. G6 avg 65.8, max 98. G7 0.1792 at load 3.77 while the soak ran on the same machine, so it does not count. Boot 0 errors. ASCII clean.
- A review: PASS.

## 2026-11-05 Perf step 2: autoTier needs 3 slow windows and never saves - Orchestrator B
- tierS has a bad counter. The guard skips the first 4 s of a match. A drop now needs 3 slow 120-frame windows in a row and no longer writes profile.q. The header comment was updated. Players with a saved q=0 are not migrated (the user's call).
- md5 b3736244d1e6b55280aab7a411887aba. Snapshots chope.pre-perf2.html and chope.perf2.html. Applied by wp8/perf/step2.py, byte identical to the tested copy proto-perf/b_p2.html.
- Forced drop test (REAL=1 SPIKE=1 proto-perf/b_soak.mjs, Auto quality, hawker): stayed on Medium through the 2.5 s spike at 20 s. Dropped to Low at matchT 243.4, about 11.6 s into the sustained load. localStorage profile.q stayed 'auto' the whole run. 0 errors. Programs went 35 to 59 on the drop, as the tier change recompiles. shots/perf/b_p2spike.json.
- Gate 8/0. G6 avg 63.0, max 94. G7 0.1310 at load 2.37 (counts). Boot 0 errors. ASCII clean.
- A review: PASS. A noted (optional) that tierS is not reset at match start, so a match that ends with bad=2 can drop after 1 slow window next match. Not folded in. Left for the coordinator to decide.

## 2026-11-05 Perf step 3: small leaks - Orchestrator B
- Steam Off cloud material disposed on expiry (fresh B() material per cast, safe). Hornbill bird removed and its geometry disposed in freeEnt (fresh geometry per birdMesh, shared M materials kept). Audio: strip() records its chain on ig._ch, play() disconnects the chain once the last source ends. Tracer pool skipped, as asked.
- md5 baa40212a3de9c9b11ce6cc2eb9903d6. Snapshots chope.pre-perf3.html and chope.perf3.html. Applied by wp8/perf/step3.py, byte identical to the tested copy proto-perf/b_p3.html.
- Smoke wp8/perf/s3.js (hawker, Tarik and Lim on both teams, 2 bot matches plus a restart, Steam Off used each match). Old page: 4 birds live after match 2 and after restart, 0 audio disconnects. New page: 2 birds per match, 0 after restart, 8587 disconnects, 0 errors.
- Gate 8/0. G6 avg 62.9, max 99. G7 0.1168 at load 2.12 (counts). Boot 0 errors. ASCII clean. No PERF-PROBE lines.
- A review: PASS.

## 2026-11-05 Perf step 4: tierS reset at match start - Orchestrator B
- startMatch now clears tierS.n, tierS.sum and tierS.bad next to matchT=MATCH_LEN. A slow streak from the last match no longer carries over. Requested by the coordinator after A's step 2 note.
- md5 94b6790dedbcebc9e7f8814fac4e31d6. Snapshots chope.pre-perf4.html and chope.perf4.html. Applied by wp8/perf/step4.py, byte identical to proto-perf/b_p4.html.
- Spike test rerun (shots/perf/b_p4spike.json): held through the spike, dropped at 243.8, profile.q stayed 'auto', 0 errors. Same as step 2.
- Gate 8/0. G6 avg 62.4, max 98. G7 0.1143 at load 2.12 (counts). Boot 0 errors. ASCII clean.
- A review: PASS.
- Zip rebuilt with zsh tmp/build_itch.sh after the heroes check: 69 files, chope-itch.zip md5 29096176225dbccef3f3c31cff3f4bc2, build/index.html md5 11844c5b33ad0ea7b703db421c362e2f. All 4 fixes present in the minified build. Boot 0 errors. Not copied anywhere.

## 2026-11-05 Tab scoreboard - Orchestrator B
- Holding Tab in a match shows K/D/A for both teams. DOM only. preventDefault only while playing. Hides on blur, when a screen opens and at match end. Rebuilds on open and on each kill. The 6 s assist rule is kept.
- md5 fc54b4c7, then the board score refresh (sbTime) at md5 a2da1c24. A review: PASS for both.

## 2026-11-05 GPU F1: High shadow map drawn in the main render - Orchestrator B
- High uses shadowMap.needsUpdate inside the main render, so there is no separate shadow render. Saves 6 to 10 draw calls a frame. Shadow calls are counted apart, so G6 is unchanged. 0 px against a second base run.
- md5 f2f71b81557d86db542938ff13f16c5b. Snapshot chope.pre-gpuf1.html. A review: PASS. Report PERF2_GPU.md.

## 2026-11-05 CPU Fix B: per-kind normal materials - Orchestrator B
- A renderBufferDirect wrapper gives plain, skinned and instanced meshes their own nMat clone with shared uniforms, plus a shared skinned customDepthMaterial in the shadow pass. Stops about 28 program key rebuilds a frame. Allocation 234 to 118 KB per frame.
- md5 d226ca4b71f3f77944363156c0605b78. Snapshot chope.pre-cpuB.html. wp8/cpu/fixB.diff.
- Gate 8/0 twice, G7 0.121 and 0.098 (counts). Pixel diffs on 3 maps equal a third base shot in all 24 cases (base boot variance). 37 programs was a 5-map running total, a fresh load gives 36. A review: PASS.

## 2026-11-05 CPU Fix A: repeat renders reuse the frame counter - Orchestrator B
- The normal prepass, and the main pass on bake frames, reuse info.render.frame and skip the matrix pass. The counter is restored afterwards. Optional idea from A, not applied: use fr1 for the prepass on High.
- md5 9b6458af393500c74c197d23b9a78aeb. Snapshot chope.pre-cpuA.html. wp8/cpu/fixA.diff.
- Gate 8/0, G7 0.122 (counts). Pixel diffs on 4 maps equal a third base shot in all 32 cases. A review: PASS, checked against the three r170 source.
- Both fixes together, paced 60 Hz, 5 maps: High p50/p95 2.2/2.86 to 1.92/2.46 ms. Medium 1.94/2.48 to 1.72/2.24 ms. Report PERF2_CPU.md.
- Zip rebuilt, 69 files, md5 6a9e003ce2e6fd3560aeda364be5422f, build/heroes matches heroes/. Copied to ~/Downloads/chope-itch.zip.

## 2026-11-05 Respawn timers up 3 s - Orchestrator B
- kill() base respawn is now 7.5 s for the player and 7 s for bots (was 4.5 and 4). The 1.5 s trailing-team discount stays. The practice range dummy clamp (1.5 s) is unchanged.
- md5 c4cae38eb619235474daca0bb1ccf454. Snapshot chope.pre-respawn.html.
- Probe wp8/resp/probe.js, one bot match on autopilot: two player deaths, each with respawnT 7.5 and a death screen reading Back in 8 down to Back in 1, then hidden on respawn. Six bot deaths, all at 7.
- Boot 0 errors. Gate 8/0, G7 0.139 at load 3.8. An earlier run at load 20 to 76 failed only G7 (0.342), which does not count above load 4.
- A review: PASS. Trailing discount checked: enemy ahead gives player 6, teammate 5.5, enemy 7. Own team ahead gives player 7.5, teammate 7, enemy 5.5 (shots/wp21a/resp_trail.json). Matches will run longer. If the wp8 match-length band drifts, log it as a known issue.

## 2026-11-05 Wave 9: Engineer turret ghost and raised placement - Orchestrator B
- Hold 2 to aim a ghost turret (green valid, red invalid, 16 m range ring), release to build. A tap still builds. Escape, stun, death and screen changes cancel. Turrets now sit on flat tops: tables, counters, cars, planters. Walls, stool tops, spots out of bounds and spots more than 3 m up or down are rejected with a reason. The bot turretSpot uses the same fit rules and may use table tops. Claim OT drops the turret on what he stands on. collide() is untouched.
- md5 2bc751faeca8842bbfbf457099baae44. Snapshot chope.pre-turret9.html. Patch proto-turret9/patch.py (no --proto).
- Probe 17/17 (wp8/turret9/probe.js). Programs 35 with the ghost shown, plus 3 draw calls only while the key is held. Boot 0 errors. Gate 8/0, G7 0.130 at load 3.9.
- Pixel diff with no Engineer in the comp (new COMP env in wp8/cpu/shot.mjs): all 40 cases equal a base shot at 0 px. With a bot Engineer the seeded matches diverge from t45 or t90 on purpose, because turretSpot changed.
- Do not trust proto-turret9/probe.js as shipped. Line 39 has its closing brace inside a comment ("// rebinding is tested in run.js}"), so it does not parse. The fixed copy is wp8/turret9/probe.js.
- A review: PASS. wp2b 3/0 and wp17-ab5 pass on the patched page. Known issue: a keyup lost on window blur leaves the ghost up until 2 is pressed again. The wp1b "6 to 9 heroes" row fails on the base page too (the roster is 11).

## 2026-11-05 Wave 9: roofs collide - Orchestrator B
- mapSolids(X,R) makes r and rx roof boxes solid when R is set. loadMap passes it for every map but hawker, which keeps its own ix twin. The collide() ceiling test now reaches .1 past the slab edge, so the camera near plane stays out of the slab side. Wet market gets 5 invisible canopy colliders (10 after mirror). Other mapSolids callers pass no R, so visuals are unchanged.
- md5 6b98a6a8d9ea544bfb2191da83af5a06. Snapshot chope.pre-roof9.html. Patch proto-world9/patch_roof.py.
- Boot 0 errors. Gate 8/0, G7 0.120 at load 3.8. Roof audit (proto-world9/audit.js) matches the agent's after-audit on every row of voiddeck, wet market, carpark and classroom.
- Hawker audit: 3 Rider fly rows give y 5.49 with a clip on the 6.8 rim here, and 5.09 in the agent's runner. Every build back to chope.pre-turret9.html gives 5.49, and so does the agent's own before-audit. Hawker has R off, so this predates the landing.
- Pixel diff with no Engineer: hawker 0 px on all 8 shots. Carpark matches fresh base shots at 0 px on all 8 (the first base set caught the q1 shadow bake in its other state). Voiddeck, wet market and classroom diverge on purpose. Per-hero traces (wp8/cpu/trace.mjs, wp8/roof9/firstdiv.py) tie each first divergence to the patch. Voiddeck at 7.85 s: the Debater meets the existing 2.25 m deck one substep sooner because of the .1 margin. Wet market at 8.05 s and classroom at 5.35 s: a projectile stops on a roof that it used to pass through.
- A review: PASS. wp1b 8/0, stuck 0. wp8 functional rows pass. The wp8 length band fails (voiddeck 91), and the base page fails it on wet market and carpark too (known balance issue).
- Items for the user, from proto-world9/REPORT.md:
  - New perches. Rascal and Siao can stand on the carpark lobby roofs (top 3.25), right over the spawns at x = +-28, and Rascal can jump from there to 4.7. Rascal can stand on the voiddeck bike shelter roofs (top 2.9). Rider ult and Bird Escape can land on every roof. Options: accept, move the ledges that reach them, or add roof fatigue like the Rider awning.
  - Roofs now block projectiles.
  - Wet market: the gap between the stall walls and the canopies can no longer be stood in (it was a clipping perch).
  - Classroom: the gym indoor jump is capped at feet 1.18, so the head no longer goes through the 3.2 m ceiling.
  - Known issue: on Rider ult fly at the playground roof edge, the head goes .65 into the slab. The eye stays clear, so the camera does not clip.

## 2026-11-05 Wave 9: shadow fit v1 reverted - Orchestrator B
- patch_shadow.py v1 fit the sun shadow box to the map bounds plus 2 m. It landed as 6438efd6 and was reverted to 6b98a6a8 after A's review.
- Reason: the old square box reached 33 to 40 m from the centre. The fitted box dropped off-map trees just past the fence, at voiddeck (-34,26) and carpark (-36,20) and (-40,-26), so their grass went fully lit. In-bounds shadows were the same or crisper. Gate 8/0 and G7 0.1225.
- The rejected build is kept as chope.shadow9-rejected.html. v2 covers off-map casters and lands separately.
- Note: near chope.html line 1202, sun.shadow.bias=-.0005 and sun.shadow.normalBias=.03 sit inside a comment and are never applied. Left as is.

## 2026-11-05 Wave 9: turret ghost cancels on window blur - Orchestrator B
- The window blur handler now calls tpEnd(player). Before, an Engineer who held 2 and switched windows kept the ghost on screen, and a later keyup placed a turret.
- md5 ce91ade0d4837968b81d116a3fafd0f3. Snapshot chope.pre-blur9.html. One line in the blur handler.
- Probe wp8/blur9/probe.js: the base page reproduces the stale placement. The new page hides the ghost, ignores the stale keyup, and still places on a normal hold and release. The turret regression probe (wp8/turret9/probe.js) passes on both pages.
- Boot 0 errors. Gate 8/0, G7 0.1195 at load 2.2. Pixel diff: hawker and classroom 0 px. On voiddeck, wet market and carpark, a third base run matches new at 0 px on all 24 shots, so the first diffs were run-to-run state.
- A review: PASS.

## 2026-11-05 Wave 9: shadow fit v2 - Orchestrator B
- fitShadow(map) runs in applyMap. It fits the sun shadow box to the map bounds plus 2 m, and to every off-map building and tree plus 4 m, so it never drops a caster the old square covered. The sun moves back until every corner clears the near plane, and far is at least 120. The map size grows in steps of 256 to hold texels at or below 80 m/2048, capped at maxTextureSize. The five real maps stay at 2048.
- md5 f1e2b7eab3195786fddd84275a15a40b. Snapshot chope.pre-shadow9b.html (ce91ade0). Patch proto-world9/patch_shadow.py (v2).
- Boot 0 errors. Gate 8/0, G7 0.0945 at load 2.8. Coverage (wp8/shadow9/cover.js): floor 100% on all maps. Carpark caster tops outside the box go from 4 to 0. Voiddeck keeps 1, the tall HDB block, which predates this.
- Per map: hawker and voiddeck keep the same box, sun and near/far as before. Wet market box bottom moves from -39 to -36.3. Classroom shrinks from 66x66 to 62x55, so shadows are crisper (3.22 to 3.03 cm per texel). Carpark box shrinks and the sun moves back from 35.2 m to 42.7 m.
- Look change on carpark: the tall HDB block and an off-map tree now cast shadows on the west edge of the deck. The old near plane clipped them. More correct, no loss, but visible. Shots: proto-world9/shots/off_carpark_aerial_sbs.jpg.
- The patch comment says the sun distance and near/far stay as before. That is wrong for carpark. Fix the comment in the next landing.
- The bias note from the v1 entry still holds: sun.shadow.bias and normalBias near line 1202 sit in a comment and are not applied.
- A review: PASS. Off-map props the old box shaded are all inside the new box on all five maps.

## 2026-11-05 Wave 9: hawker full stretch - Orchestrator B
- Hawker grows to the full 90x60 stretch from proto-maps4/hawker/patch.py. The fitShadow comment now says the sun distance and near/far can change, with carpark 35.2 to 42.7 m as the example.
- md5 f87c4a72246bb662a5c1507c0d8a1cd8. Snapshot chope.pre-hawker9.html (f1e2b7ea). The patch adds a base href tag. The first landing kept it and A reverted that. It is stripped now and `grep -c '<base'` prints 0.
- Boot 0 errors. mirror_check ALL OK. wp8-hawker functional rows pass, stuck 0 to 1 over 3 bot matches.
- Gate 8/0, G7 0.1468 at load 3.99 and 0.1437 at load 2.98. Paired G7 under load 4: base 0.123, new 0.120.
- Perf: draw calls 36.4 avg, 50 max on q1 and q2. Frame tris 227.8k on q1, 336.1k on q2. Programs 33/32, textures 50/49. Shadow box 114x114, map 3072, 3.71 cm per texel.
- Watch: High frame tris 336k, up from the 251k known issue. Hawker now renders a 3072 shadow map each frame on High. Add it to the Safari look check.
- Known issue: the wp8 match-length band (110 to 200) fails. Balance, not this landing.
- A review: PASS.

## 2026-11-05 Wave 9: voiddeck full stretch - Orchestrator B
- Voiddeck grows from 62x42 to 90x60 from proto-maps4/voiddeck/patch.py (full, not lite). Adds signs, the letterbox bank, the RC notice board, deck drains and the new map entry. The redundant i twins are kept.
- md5 6a9b7017e7b7c25da4f520ba5d72f35b. Snapshot chope.pre-voiddeck9.html (f87c4a72). Patched to chope.html, so no base tag. `grep -c '<base'` prints 0.
- Boot 0 errors. mirror_check ALL OK. wp8-voiddeck functional rows pass, stuck 0 over 3 bot matches, EC 0.
- Gate 8/0, G7 0.1338. Paired G7 under load 4: base mean 0.112, new 0.124. Spreads overlap. G7 margin is now about 0.016.
- Perf on High: draw calls 50.2 avg, 82 max. Frame tris about 151k (was 70k). Programs 30, textures 51.
- Shadow box 114x114, map 3072, 3.71 cm per texel, sun 47.9 m. The second caster top outside the box is the invisible i twin and casts nothing. The tall HDB block top still clips the near plane, a known ceiling.
- Watch: voiddeck joins hawker on a 3072 shadow map.
- Known issue: the wp8 match-length band fails. Balance, not this landing.
- A review: PASS.

## 2026-11-05 Wave 9: wetmarket full stretch - Orchestrator B
- Wet market grows from 62x37 to 90x56 from proto-maps4/wetmarket/patch.py. Four signs move to the new layout, the map entry is new, and the aisle drain-side list changes. That list only places drains and goods.
- md5 d008472bf0c60c42d16903aaf2fa04e8. Snapshot chope.pre-wetmarket9.html (6a9b7017). Patched to chope.html, so no base tag. `grep -c '<base'` prints 0.
- Boot 0 errors. mirror_check ALL OK. wp8-wetmarket 9 pass, stuck 0, 1, 1 over 3 bot matches, EC 0. Wet slide and shutter rows pass.
- Gate 8/0 at load 3.91, G7 0.1402. Paired G7 under load 4: base mean 0.112, new 0.114.
- Perf on High: draw calls 63.8 avg, 91 max. Programs 32, textures 51. Shadow box 110x100, map 2816, 3.91 cm per texel, no casters outside.
- Watch: frame tris on High go from 229k to 420k, the biggest jump so far. Tris have no gate. Add it to the Safari look check.
- Known issue: the wp8 match-length band fails. Balance, not this landing.
- A review: PASS.

## 2026-11-05 Wave 9: carpark full stretch - Orchestrator B
- Carpark grows from 62x43 to 90x62 from proto-maps4/carpark/patch.py. The signs move to the new layout and the map entry is new. Every anchor matched on d008472b.
- md5 0830995236bdab96d76cad8ff32167ab. Snapshot chope.pre-carpark9.html (d008472b). Landed from the patch's unbased .raw.html output. `grep -c '<base'` prints 0.
- Boot 0 errors. mirror_check ALL OK. wp8-carpark stuck 0 over 3 bot matches, EC 0. Wet slide, smoke, alarm and hazard draw rows pass. The hazard draw row is tight, 119 to 124 against 130.
- The wp8 JSON row first failed against the old carpark JSON (3 pickups, 3 hazards). A fixed tests/acceptance.js to read proto-maps4/<id>/maps first. The rerun passes.
- Gate 8/0 at load 3.96, G7 0.1283. Paired G7 under load 4: base mean 0.111, new 0.113.
- Perf on High: draw calls 59.8 avg, 98 max. Frame tris 43k to 171k. Programs 31, textures 47. Shadow box 114x92, map 3072, 3.71 cm per texel, sun 57.8 m, no casters outside.
- Watch: carpark is the third map on a 3072 shadow map.
- Known issue: the wp8 match-length band fails. Balance, not this landing.
- A review: PASS.

## 2026-11-05 Wave 9: map stretches final gate - Orchestrator B
- All four stretches are in. chope.html 0830995236bdab96d76cad8ff32167ab. No base tag, ASCII 0.
- Gate 8/0 at load 3.96, G7 0.1438, G6 avg 62.6 max 88.
- Watch for the Safari look check: 3072 shadow maps on hawker, voiddeck and carpark. Wetmarket frame tris 420k on High.
- Known issue, predates this wave: the wp8 bot-match row also checks programs <= 36 after 3 matches in one page. It reads 37 on every map and on the pre-stretch base f1e2b7ea. The fresh-load programs checks in the gate pass.

## 2026-11-06 Strong Words: JC Debater shoots debate words - Orchestrator B
- The LMB shot is now a flying word in bold block letters with team colour fill and a dark outline. Words cycle per shooter: OBJECTION!, SOURCE?, REBUTTAL!, WRONG!, POINT OF ORDER, ACTUALLY..., NO LAH. From proto-words/patch.py.
- Visual only. The internal type stays 'plane', so speed, damage, cooldown, life, radius, head multiplier, falloff, strafe bank, hit spark and despawn are unchanged. Hitbox and hero stats unchanged.
- One 1024x512 canvas atlas holds 7 words x 2 teams. Pooled meshes swap a prebuilt quad per shot. The material is a basic map material on layer 1 with the faceCam billboard, the same program type as the zone labels. The per-step lookAt for this shot is gone, so step work went down.
- Kit entry renamed Cue Card Plane to Strong Words with a new description. Blurb and bell text no longer say planes. The 'strong words' trail recipe keeps the old puff and streak. Sound stays w2_plane.
- The paper plane in the megaphone is removed from the third person prop, the viewmodel and the KayKit pin.
- md5 001dc5804b63416538f9dedcf177ba62 after the re-land (first land 9f849abc failed SK1.3, LMB kit text 103 chars, now 84). Snapshot chope.pre-words.html (08309952). `grep -c '<base'` prints 0, ASCII 0, boot 0 errors.
- Gate 8/0 at load 3.94, G7 0.1308, G6 avg 59.0 max 93. Paired G7 on hawker under load 4: base mean 0.112, new 0.116. Noise range.
- Fresh load on hawker, debater match: programs 35 base and new at q1 and q2. Textures 63 to 64 at q1, 62 to 63 at q2. Shots in shots/words/.
- A review: PASS on the re-land.

## 2026-11-06 Test fix: two stale debater-area rows - Orchestrator B
- tests/acceptance.js only. Backup tests/acceptance.pre-lanefix.js. Diff in proto-words/tests-lanefix.diff. No chope.html change.
- New helper onLane: on hawker it moves the pair to z=-19.5, a lane clear from x=-30 to 22 with nothing nudging the dummy. The old z=0 lane is blocked past about 22 m on the 90x60 hawker. It also aims at the chest, since a flat ray from the eye is a head shot.
- AB10 plane damage by distance: now 24, 24, 36, 48, 48. PASS. It read 30, 30, 45 with 30 and 40 m missing.
- SK5.1: Live Firing is bands again (42 each, head x1.5), and the 3 rocket volley moved to Matador Strike. The row now fires through the ult and wants 2 body bands of 42 at 8, 12 and 20 m. PASS with 7 bands at each range. SKILLS.md SK5.1 still describes the rockets and needs A to update it.
- Same results on chope.html and chope.pre-words.html.

## 2026-11-06 Hero models landing 1: loader path and Gym Hunk - Orchestrator B
- New flag `heroes`, on by default in the A3 string (`toon,grade,ahma,heroes`). A3_HEROES maps a hero to a stripped GLB and its head offset. BUILD for that hero returns the new scene with the Idle of the KayKit file it already uses (Barbarian for gym). A failed file keeps the old model. From proto-heroes-land/patch1.py on chope.pre-heroes1.html.
- heroes/gym.glb (291,992 bytes) is proto-art3/demos/gym.glb (3,108,300) with its 76 clips dropped and the RGBA vertex colours stored as RGB. proto-heroes-land/strip.py. Rig rest pose matches KayKit, so the shared clips drive it.
- Hitbox, stats, SIZE and HEIGHT unchanged. FIT still puts the head mesh centre at 1.55 x size. Model top 1.912 against HEIGHT 2.02 (the old KayKit gym reached 2.145).
- HDL.gym is set to [.269,.013] only when the new file loads. That is the new face mesh centre in head bone space. Live play: head sphere centre 1.47 to 1.60 m (old 1.48 to 1.63) and within 0.013 m of the head mesh centre (old 0.04 to 0.10).
- Kept: team tint, outline, rim, hit flash, death, menu and card portrait, medicine ball in hand. Gear skins never touched the 3P models. KayKit heroes have no face expressions, so none to keep.
- Addendum: engineer kit line 2 is 89 chars. SKILLS.md SK5.1 says Live Firing is rapid 42 bands and the rockets are Matador Strike (backup SKILLS.pre-heroes1.md).
- Tris on High, 6 gym in a frozen match: hawker 405,916 to 464,774, wetmarket 489,446 to 545,840. Calls 153 to 128 and 169 to 144. Gym model 7,770 tris plus 464 weapon against BUDGET 4,200 (old 4,428).
- Programs 36 (base 35, cap 36). Cause: three r170 copies material.map onto the shared shadow depth material, and the new model has no map, so its shadow pass compiles a no-map skinned variant. Later models share it. Textures 58 (base 63).
- Gate 7/1 at load 3.83: G6 avg 58.6 max 91, G7 0.1723 FAIL. Paired G7 on hawker under load 4, 6 samples each: base 0.164, new 0.174. The base is over 0.15 on this machine today too.
- SK1.3 passes. Boot 0 console errors. ASCII 0, no base tag.
- Zip: chope-itch.zip 6,142,839 (older index.html). Rebuilt in proto-heroes-land/zipt with today's chope.html: 6,194,673 without gym.glb, 6,282,407 with it (+87,734). Not copied to Downloads.
- Shots in shots/heroes-land/: gym-shot-hawker, gym-foe-hawker, gym-menu, gym-sel.

## 2026-11-06 Shadow depth program fix (hero landing 1b) - Orchestrator B
- Programs back to 35 (was 36 after landing 1). In the renderBufferDirect hook, a shadow pass (s null) on a skinned mesh whose depth material has no map and no alphaTest now gets the KayKit Rogue atlas as its map. Map-less hero models then share the KayKit skinned depth program. From proto-heroes-land/patch-sd.py on chope.pre-heroes2.html.
- KK now also returns CACHE so the hook can read the atlas. The atlas is looked up once.
- Visual-neutral by construction: the depth shader writes depth only, and the map only matters with alphaTest, which this path excludes. Hero crop diff of gym-shot-hawker before and after (sd-old, sd-new) is inside the run-to-run noise.
- count.js: match [35,58] to [35,62] over 4 runs. 0 console errors.
- Gate 8/0 at load under 4, G7 0.1272. Paired G7 on hawker, base chope.pre-heroes2.html: base 0.117 0.121 0.102 0.125, new 0.110 0.119 0.124 0.109.
- Boot 0 console errors. ASCII 0, no base tag. md5 48532238.

## 2026-11-06 Hero models landing 2: Siaolang, NS Boy, Long Lens Lim - Orchestrator B
- heroes/siao.glb (242,064), heroes/nsboy.glb (307,388), heroes/lens.glb (280,128). From the simplified proto-heroes-simp/v/<k>-90.glb through strip.py. Siao is the 90% version.
- Three A3_HEROES entries from proto-heroes-land/patch2.py on chope.pre-hland2.html. 1 line diff. md5 32c5fa25.
- HDL from the new face mesh centre in head bone space: siao [.286,.131] (its own, no longer rascal's), nsboy [.283,-.012], lens [.401,.001]. Live head sphere stays within 0.07, 0.065 and 0.023 m of the head mesh.
- Model tris: siao 6,160 (old 6,779), nsboy 6,402 (old 5,328), lens 7,238 (old 5,320).
- Tris on High, 6 of one hero, new vs base. Hawker: siao 432,904 vs 429,609, nsboy 446,326 vs 422,616, lens 457,694 vs 419,144. Wetmarket: siao 515,378 vs 516,095, nsboy 530,708 vs 509,806, lens 537,148 vs 502,462. Draw calls fall (siao hawker 152 to 142, nsboy wetmarket 229 to 146).
- Programs and textures, comp debater,siao,nsboy,lens,gym,engineer: menu [32,39] (base [32,45]), match [35,49] (base [35,59]).
- Gate 8/0, G7 0.1332. Paired G7 on hawker: base 0.1317 0.1117 0.1073 0.1138, new 0.1273 0.1203 0.1117 0.1058. Both means about 0.116.
- Boot 0 console errors. The three heroes build from Siao_Body, NsBoy_Body and Lens_Body. ASCII 0, no base tag.
- Shots in shots/heroes-land/: siao, nsboy and lens menu-hawker and shot-hawker. One cold run gave blank menu shots for nsboy and lens. Reruns are fine.

## 2026-11-06 Hero models landing 3: JC Debater, Engineer Encik, Makan Rider - Orchestrator B
- heroes/debater.glb (214,068, 90%), heroes/engineer.glb (220,872, 75%), heroes/rider.glb (203,348, 75%). From proto-heroes-simp/v/ through strip.py.
- Three A3_HEROES entries from proto-heroes-land/patch2.py on chope.pre-hland3.html. md5 d9087656.
- HDL: debater [.237,-.047], engineer [.462,.001], rider [.444,.036]. Live head sphere to head mesh: engineer under 0.01 m, rider under 0.02 m, debater 0.04 to 0.06 m. The debater gap is sideways (x), which HDL does not set. Its y and z match.
- Model tris: debater 5,510 (old 5,415), engineer 5,364 (old 5,328), rider 4,696 (old 6,168). Model top: engineer 1.84 (old 2.09), rider 1.78 (old 2.19).
- Tris on High, 6 of one hero, new vs base. Hawker: debater 436,368 vs 424,841, engineer 434,896 vs 432,470, rider 416,516 vs 433,919. Wetmarket: debater 514,266 vs 508,815, engineer 518,120 vs 511,694, rider 501,602 vs 512,309. Draw calls fall (engineer wetmarket 264 to 166).
- Programs and textures, comp debater,engineer,rider,siao,nsboy,lens: match [35,35] in 4 of 4 runs (base [35,51]). Menu [34 to 35, 27 to 34] (base [32,39]).
- Gate under load 4.5 to 6: 7/1 on both pages, G7 only. Paired full gates: base 0.340 0.336, new 0.306 0.363. Paired G7 on hawker: base 0.1878 0.1927 0.2307 0.2223, new 0.1862 0.2035 0.2047 0.1745. Another session's python job held 160 to 240% CPU during these runs.
- Boot 0 console errors. All six heroes build from their _Body meshes. ASCII 0, no base tag.
- Shots in shots/heroes-land/: debater, engineer and rider menu-hawker and shot-hawker. Two menu shots came out blank on the first try and fine on retake. The base page does the same.

## 2026-11-06 Hero models landing 4: Teh Tarik Auntie, Ah Ma, Recess Rascal - Orchestrator B
- heroes/tarik.glb (279,212, 90%), heroes/ahma.glb (355,780, 75%), heroes/rascal.glb (217,572, 90%). From proto-heroes-simp/v/ through strip.py.
- Three A3_HEROES entries from proto-heroes-land/patch2.py on chope.pre-hland4.html. md5 7ee178d6. patch2.py also skips the ahma3 preload when A3_HEROES.ahma is set.
- The old v3 ahma (9,842 tris, 76 clips) is kept at proto-heroes-land/ahma-v3.glb. The base page for ahma is chope.base4v3.html, which points A3_AHMA at that file.
- HDL: tarik [.422,-.036], ahma [.404,-.049], rascal [.467,-.008]. Live head sphere to head mesh: rascal under 0.01 m, ahma 0.004 to 0.041 m, tarik about 0.01 m standing and 0.05 to 0.09 m in crouch frames.
- Model tris: tarik 7,208 (old 10,767), ahma 8,104 (v3 9,842), rascal 5,696 (old 5,751). Model top: tarik 1.78 (old 2.2), rascal 1.39 (old 1.61), ahma 2.27 to 2.34 (v3 2.25 to 2.33).
- Tris on High, 6 of one hero, new vs base. Hawker: tarik 452,054 vs 459,663, ahma 484,886 vs 516,236, rascal 430,800 vs 423,833. Wetmarket: tarik 523,853 vs 555,588, ahma 570,878 vs 594,272, rascal 512,834 vs 509,739.
- Programs and textures, comp tarik,ahma,rascal,debater,engineer,rider: menu [29,25] (base [32,29]), match [32,31] (base [35,36]).
- Gate 8/0 at load 3.1, G7 0.1217. Paired G7 on hawker, base chope.base4v3.html: base 0.1200 0.1147 0.1285 0.1207, new 0.1080 0.0978 0.1293 0.1155.
- Boot 0 console errors. All six heroes build from their _Body meshes. ASCII 0, no base tag.
- Shots in shots/heroes-land/: tarik, ahma and rascal menu-hawker and shot-hawker, plus menu-base for each. The new ahma keeps walker and basket. It loses the v3 hunched spine and head pose, which reads fine.
- Test harness fix: the 9341 Chrome served the old heroes/ahma.glb from HTTP cache. proto-heroes-land/cdp.mjs now enables Network, clears the browser cache and disables caching on every run. Numbers above are from runs after the fix.

## score150 - win target 150, draw result, filler text cut (B, 2026-11-07)

### What changed
- SCORE_TARGET 100 to 150. The tutorial line reads the target from the constant.
- Draw. New `fsc(t)`: the floored score, capped at the target. endMatch, the overtime check and the end-screen cheer all use it. Root cause: endMatch compared raw floats, so 150.7 vs 150.1 showed "150 vs 150" as a win and 87.9 vs 87.1 at time out as a win.
- Draw end screen: title DRAW LAH (was SEOW ONG), blue title. No Win counted, no first-win bonus, no confetti, neutral bell sound. XP line "Draw" gives 90 (loss 40, win 150).
- Overtime on a tie now runs while either team is on a table. Before, only team 2 on a table kept a tie going.
- Filler cut: menu blurb, hero card tagline, detail panel italic line (blurb field removed from all 11 heroes), pause joke, receipt "TABLE NO. 07" and "PLEASE RETURN YOUR TRAY". Inventory in FILLER.md.

### How I tested
- tests/acceptance.js package score150 (6 rows): 6/0. The same rows on chope.pre-score150.html: 2/4 (150.7-150.1 showed SHIOK! and +1 Win).
- Bot match log, 12 matches (gym, tarik, debater x 4 maps), q=1. Target 100: length avg 138 s (107 to 160), loser avg 64.6. Target 150: avg 202 s (118 to 253), loser avg 93.8. No overtime. All ended before the 300 s clock.
- Gate 8/0 (G7 0.112 ms). Boot 0 errors. Shots in shots/score150/.

## menulive - live 3D hero on the main menu, no prop clipping (B, 2026-11-07)

### What changed
- Main menu shows the picked hero live in the map (option A, proto-menuhero/patch_live.py). Hero select cards, score and draw code untouched.
- No clipping, general for every hero and map. `mhHide()` takes the hero box from his visible meshes over the idle sway, pads it 15 cm, and hides what it touches above his feet. Small meshes (tissue packet, sign) go invisible. Fan instances get a zero matrix, re-applied each frame since fans spin. Merged batches lose only the touching triangles (the hawker sauce pots). Floor and the table he stands on stay.
- `mhShow()` puts back exactly those props. It runs on every hero swap, map rebuild and when the hero is freed for a match. The Medium shadow bake restores them and hides the hero, then re-hides them.
- Stage spot needs about 2.6 m headroom (voiddeck zone B sits under a slab, so it moves to another zone). Tight maps try camera distances 9, 7, 5, 4 and 3 m and widen the lens when close.
- Bug fixed: classroom had no spot that passed the 5 m ray check, so it fell back to zone A with the camera inside a wall (empty wall on screen). It now stands at zone B with the camera 3.7 m out down the corridor.

### How I tested
- proto-menulive/probe.js: 11 heroes x 5 menu maps, scene triangles above the feet inside the hero box. 55/55 print 0, two runs.
- Match after the menu (hawker): __mh.hid() 0, every zone packet and label visible, scene geometry checksum equals chope.pre-menulive.html.
- Medium q=1 bake: hero hidden, table B packet visible during the bake. Hidden again after.
- In-match programs 31 and textures 30, same program keys as the pre build at q=1 and q=2.
- Gate 8/0 (G7 0.135 ms). Boot 0 errors. ASCII clean. Shots in shots/menuhero-land/.

## menulive2 (B) - menu hero framing

### What changed
- The menu camera frames each hero on his measured visible box (`mhBox`). The box covers every visible mesh over 8 s of idle and the yaw sway. Skinned meshes refresh their skeleton first. Instanced meshes are boxed over their instances. Uncle's fumes run on the wall clock, so `mhBox` steps `performance.now` with the sample and puts it back after.
- Fixed 30 deg lens on every map. The distance comes from the box so each hero fills about 0.8 of the stage height (`mhFit`). `mhSpot(need)` looks for a spot with that much clear distance: zones first, then a 2 m floor grid near table B, then shorter distances. Classroom now uses a grid spot with full distance and no ceiling beam behind the head.
- A wide hero (Ah Ma's walker) slides left until his box clears the right edge by 48 px.
- `mhHide` reuses the measured box.
- The name plate moved to the top left of the stage (left 3%, top 4%, max width 24%). The narrow layout rule gained `top:auto` so it keeps its bottom placement.
- Siao's tick clamps a negative dt to 0, since the stepped clock can run ahead of the next real frame.
- Hook: `__mh.fit()` returns the box, the spot and the fit.

### How I tested
- Framing at 1280x720, 11 heroes x 5 maps: fill 0.69 to 0.83, top margin 0.087 to 0.182, lens 30 everywhere, right edge at most 1240, plate overlap 0 vertices. Uncle's box top is 2.64 to 2.66 on every map.
- Clip probe 55 cells, sum 0. Gate menulive2-B 8 PASS, 0 FAIL, 0 console errors.
- Match programs (31) and textures (30) match pre-menulive at q=1 and q=2. Match geometry checksum unchanged. The hero is hidden in every bake. Boot ok at q=1 and q=2.
- Shots: shots/menuhero-land2/ (23 frames and sheet.jpg).

## menulive3 (B) - menu hero fit by screen size

### What changed
- `mhSolve` fits the projected hero box inside the real stage rect, read from the DOM: below the top bar, above the skin row and bottom bar, right of the left panel. The margin is max(12 px, 2 percent of the short side). The fixed 0.84 factor is gone.
- When the name plate overlaps the stage, the box goes beside it or under it, whichever leaves the hero bigger. The solver iterates distance and screen offsets (10 steps at most).
- `mhCam` solves only when the layout, plate, spot or box changes, then just aims (`mhAim`).
- `mhMeasure` takes one box per mesh at yaw 0 over the idle sample. It is cached per hero and skin in `MH.bc`. `mhBox` turns those boxes to the spot yaw at five sway samples (-0.4 to 0.4).
- `mhHide` caches its hide list per map, spot and box, so a repeat swap skips the triangle scan.
- Narrow layout: the plate sits at the top left of the stage (`top:0`, max width 60%). The fit puts the hero under it.

### How I tested
- Framing, 11 heroes x 5 maps at each size. Plate overlap 0, edge overlap 0, skin row overlap 0 at every size.
  - 1280x720: fill 0.67 to 0.76, top 0.098, bottom 0.86.
  - 1920x1080 DPR 2: fill 0.73 to 0.81, top 0.092, bottom 0.90.
  - 390x844: fill 0.32 to 0.36, left edge at least 48 px, right edge at most 357.
- Clip probe 55 cells, sum 0 at all three sizes.
- Match programs (31) and textures (30) equal pre-menulive at q=1 and q=2. All program keys equal menulive2. Geometry checksum equals menulive2. Hero hidden in every bake. Boot ok at q=1 and q=2.
- Swap: first visit 59 to 79 ms (makeMesh 9 to 18 ms). Repeat visit 9 to 19 ms, which is makeMesh alone.
- Shots: shots/menuhero-land3/ (23 frames and sheet.jpg).
- Gate menulive3-B: 7 PASS, 1 FAIL (G7 0.154 to 0.193 ms), 0 console errors. The pre-menulive3 build (4dd5a381) fails G7 on the same machine at the same time (0.153 to 0.180 ms). G7-only runs, alternated: pre 0.131 to 0.181, menulive3 0.148 to 0.167. G7 needs a rerun on a quieter machine before this ships.

## lineup (B) - hero select cards and 4 renames (2026-11-07)

### What changed
- Hero select: proto-cards/patch_lineup.py landed as written. Full-body figures in 6 columns, condensed caps name over the role pill, 256 px round busts in the HUD medal, Tab board, receipt, death card and detail panel.
- Renames, display names only (ids unchanged): NS Boy to NSF, JC Debater to Debate Team Captain, Long Lens Lim to Birdwatcher, Makan Rider to Delivery Driver. HEROES and HUD.KITS plus the code comments. Docs and test labels keep the old names as history.
- Card name: one line, nowrap, font capped at 10.6cqi of the card, letter spacing .01em. No wraps or overflow at 1280 or 1920.
- Menu plate: a long name steps its font down (fitPlate, ResizeObserver on the stage) until it fits in two lines. Plate width is unchanged, so the hero framing is unchanged. Debate Team Captain is 26px at 1280, 29px at 1366, 38px at 1920.
- Build: patch_lineup.py then proto-lineupB/rename.py on 7b64faf9.

### How I tested
- Hero select: 0 wraps, 0 overflow, cards end at 562 (Start bar 576) at 1280 and 745 (759) at 1920. Bust render 159 to 168 ms.
- In-match: kill feed and death card show player names, the HUD hero name is hidden by CSS. Tab shows the new names with no overflow.
- fit3: probe hits 0, edge 0, skin 0 at 1280, 1920x2 and 390. Fill 0.62 to 0.73, 0.73 to 0.81, 0.32 to 0.39. Rascal fill swings 0.50 to 0.68 between runs on both builds, so the 1280 low end is noise.
- Match programs (31) and textures (30) equal pre-lineup at q=1 and q=2, program keys equal. Boot ok at q=1 and q=2.
- Shots: shots/lineup-land/.
- Gate lineup-B: 8 PASS, 0 FAIL, 0 console errors, G7 0.1255 ms (load 3.83). G7-only, 3 interleaved pairs of 3 runs: pre-lineup median 0.1153 ms (0.098 to 0.170), lineup median 0.1160 ms (0.108 to 0.163). Load rose from 3.2 to 5.8 during the pairs.

### Open
- Under load some runs log "heroes/<x>.glb failed, old model kept" on both builds. A loader timeout under load, not this change.

## lineup2 (B) - card portraits, plate width, card fit, load retry (2026-11-07)

### What changed
- Card portraits: the card scene now renders into a HalfFloat target. A pass then applies the game tone map and exposure, srgb(neutral(c*expo)) with expo from the comp pass, into an 8-bit target before readback. The CPU sRGB table is gone from cardRender. All three targets, the material and the quad are freed after the 11 heroes.
- Menu plate: fitPlate also steps the font down while the name is wider than the plate (scrollWidth over clientWidth).
- Hero cards: .shot is now aspect-ratio .64 (the render aspect) with the old clamp as max-height, so the image never gets wider than the card.
- Loading: once() retries a failed KayKit, hero GLB or map piece load once after 300 ms. No loop.
- Build: proto-lineup2B/patch.py on a732fb24.

### How I tested
- Portraits, share of opaque pixels with a channel at 254 or above, before to after: Uncle 27.6% to 0%, Ah Ma 13.9% to 0%, Birdwatcher 9.9% to 0%, Gym 6.0% to 0%. Mean brightness is about the same. PNG and JPEG for each are in shots/lineup-land2/.
- Bust render 157 to 169 ms for 11 heroes on an idle machine (pre-lineup2 177 ms).
- Hero select at 1280, 1366 and 1920: image 118 px in a 118 px card, no side clipping, no name wraps or overflow. Cards end at 562 and the Start bar is at 576.
- Plate at 1280, 1366, 1920 and 390: every hero fits in 2 lines or fewer, and scrollWidth equals clientWidth. Birdwatcher is 27px at 1280 and 30px at 1366.
- fit3 at 1280, 1920x2 and 390: probe hits 0, edge 0, skin 0. Fill is the same as lineup.
- Match programs (31) and textures (30) equal pre-lineup at q=1 and q=2, keys equal. Boot ok at q=1 and q=2. once() checked in node: it retries once and then gives up.
- Gate lineup2-B: 8 PASS, 0 FAIL, 0 console errors, G7 0.1307 ms (load 1.60). G7-only, 3 interleaved pairs of 3 runs: pre-lineup median 0.1093 ms, lineup2 median 0.1095 ms (load about 2).

## dock (B) - menu direction C, 1920 zoom, no hero han glyphs in the UI (2026-11-07)

### What changed
- Menu: proto-menu2/patch_dock.py on 21a7ab5a (gives 179c5f13). Ink top bar, ink dock below, the live hero big and centred between them.
- 1920 zoom from proto-menu2/wip/c_base.css: #menu and the mute button get zoom 1.3 at 1600x860 or larger, and 1.6 at 2200x1200 or larger.
- No hero han glyphs in the UI. The dock plate badge (#menuHan, now #menuBust) shows the hero bust and refreshes when the busts finish. The card, detail panel, HUD medal and receipt fallbacks show nothing, so the field colour shows. The han field is gone from KITS and from the Noto Serif SC text= list. The .hn, .chud .han, #sb .hi .hn rules and the --han var are removed.
- Map signage is unchanged (zh rows, TRAY_ZH, HALL_ZH).
- Build: patch_dock.py, then proto-dockB/nohan.py.

### How I tested
- Plate at 1280, 1920x2 and 390: every hero fits in 2 lines or fewer, scrollWidth equals clientWidth, and the badge has a bust. Debate Team Captain is 2 lines and Birdwatcher is 1.
- CJK scan of all DOM text, alt and aria-label: none on the menu, hero select, HUD or Tab board at all three sizes. The source has CJK escapes only in map signage.
- fit3 and the clip probe: hits 0, edge 0, skin 0 at 1280, 1920x2 and 390. Fill 0.57 to 0.60, 0.61 to 0.65, 0.36 to 0.48.
- Match programs (31), menu programs (31) and textures (30) equal the base at q=1 and q=2, and the keys are equal. Boot is ok.
- Gate dock-B: 8 PASS, 0 FAIL, 0 console errors, G7 0.1332 ms (load 2.54). G6 scene avg 53.1 (base 48.2), under the limit of 74.
- Shots: shots/dock-land/.

## kits3 (B) - Ah Ma hook, Siaolang assist stim, Rascal book shield, Downwards Slam, Birdwatcher scoped auto-charge (2026-11-07)

### What changed
- Siaolang, Stim Siol: also fires on an assist (hitBy and healBy assist loops) while Siaolang is alive. Same effect as on a KO: heal 60, buff .5 for 5 s. Kit text: "On a KO or assist".
- Ah Ma, ability 2: Walker Twirl is replaced by Kaypoh Hook (weapon key 'kaypoh hook'). A hook projectile at 36 m/s with .5 s life (18 m). On hit: 30 damage, slow 30% for 1.5 s, and a pull to 2 m in front of her through the generic dash (speed 26). No pull on a target that is dead, charging or plunging. Charge cd -0.8 s on hit is kept. Cooldown 7.2 s. Bots use it at 3.5 to 17 m with line of sight. The Twirl code is gone. The AB2 icon key stays 'twirl' until the icon landing.
- Rascal, Exercise Book Block: lasts 2 s, the .25 s perfect window is unchanged. A book shield (two hinged halves, shared toon materials, one unit box) pops up .95 m in front, under the eye line, scale .3 to 1.15 to 1 over .2 s while the covers open.
- Delivery Driver: "Special Delivery" is now "Downwards Slam" in the kit, KITS ab, the weapon name and the Order Tracking check. "Delivery cd" is now "Slam cd". Icon keys and behaviour are unchanged.
- Birdwatcher: scoped, the charge fills on its own over .8 s and a click fires what is built. A shot, reload, unscope, Bird Escape or death resets it. Unscoped is still hold to charge over 1.2 s. Scoped bots fire at full, or early when the shot already KOs. The player gets a charge ring around the scope crosshair (flashes at full) with the k_charge loop and k_charge_full. Others see a lens glint at the muzzle that grows with charge and pops at full. The glint uses the FX pool material (fxM and B) and is disposed in freeEnt.
- Build: proto-kits3B/patch.py on fabf616f, then the glint material and dispose fix.

### How I tested
- Ah Ma: target at 13 m, hook hit for 30 ('kaypoh hook'), slow on, cd1 -0.8, pulled from 13 m to about 1.6 m in .4 s.
- Siaolang: assist counted, stim heal 60 and buff on. The KO path still works.
- Rascal: deflectT 2 on cast, book visible at scale 1 after .25 s, still visible at 1.85 s, hidden after 2.15 s.
- Birdwatcher: scoped charge climbs at 1 per s to .8 after the shot cooldown, a click fires one shot and resets it, unscope resets it and the ring. Unscoped hold reaches 1.2 and fires. A scoped bot charges with the glint growing (.07 to .15), fires at full for 80 and the glint pops.
- Match programs (31) and textures (30) equal the base at q=1 and q=2, with the book and glint forced on screen. The first build had 32 programs at q=2 from a plain glint material. It now uses the FX one.
- Boot ok, 0 console errors. ASCII only, node --check passes.
- Gate kits3-B: 8 PASS, 0 FAIL, 0 console errors, G7 0.1322 ms (load 2.81). G6 scene avg 53.9. G7-only, 3 interleaved pairs of 3 runs on hawker: base median 0.1072 ms, kits3 median 0.1165 ms (load about 3).
- Shots: shots/kits3/.

### Open
- The book adds a few box tris while it is up. These are FX, not the hero model.
- A hook that Rascal reflects pulls toward Rascal.

## icons-e (B) - style E ability icons, hook visibility, reflected hook naming (2026-11-07)

- Snapshot: chope.pre-icons-e.html (md5 c7bd6d37). New page md5 91a0db86. Build: proto-iconsB/patch.py.
- Icons: IC2 block replaced by ICE (proto-icons3/icons_e.js), ICE.sprite() in the HUD. AB2 ahma slot 2 is now 'hook'. Greyscale cooldown CSS unchanged and still applies (slot.cool svg.ic.x2 filter grayscale(1) contrast(.75) brightness(1.08)).
- Hook head: thicker shaft (r .075, 0.8 m) with a vertical J crook, colour 0xff4fc8, on a kept FX material (hookM).
- Rope: ropeTick draws a cream line from Ah Ma's hand to the hook in flight, then to the target while it is pulled. It hides when the pull ends. Uses the FX tracer geometry and B(), so no new program. freeEnt disposes it.
- Reflected hook: hookHit passes p.weapon to damage, so a deflected hook logs 'deflect' like other reflected shots.
- Gate icons-e-B2: 8 PASS, 0 FAIL, 0 console errors, G7 0.1468 ms (load 3.16), G6 avg 55.5. First run read G7 0.1583 at load 3.18. G7 pairs on hawker: base 0.1408 0.1308 0.1250 0.1265, new 0.1458 0.1260 0.1240 0.1312, so flat.
- Programs: forcing the hook and rope on screen adds 0 program keys at q=1 and q=2. Match program totals read 31 to 33 on both base and new pages from match FX variance. Textures 29 to 31 on both.
- Shots: shots/icons-land/.

## hookfix (B) - hook tip colour, hook cancel on KO, pulled flag, twirl icon removed (2026-11-07)

- Snapshot: chope.pre-hookfix.html (md5 91a0db86). New page md5 ef183324. Build: proto-iconsB/patch2.py.
- Hook: magenta shaft (PROJ.hook is now the cylinder only) with a cream crook child (hookTipG, hookTipM=B(CRM), kept). FX layer, no new program.
- kill(): a hook Ah Ma owns in flight gets life -1, and hookHit returns early when the owner is dead, so it cannot land or drag. A pull on or by the dead entity stops (pulled, dashT, dashSpd cleared).
- ICE sprite: 'twirl' symbol removed (44 symbols). proto-icons3 untouched.
- Tests (h1-dbg, q=2): KO with hook in flight gives no hook damage, no pull, rope hidden. Victim KO mid-pull and Ah Ma KO mid-pull both clear pulled and dashT. Programs 31.
- Gate hookfix-B2 at load 2.45: 7/1, G7 0.1808 only, 0 console errors. G7 pairs on hawker under load 2.5 read new about 10 percent higher (base median 0.153, new 0.168). With Math.random seeded per run, 6 G7 runs per page: base 0.1635 to 0.1837, new 0.1575 to 0.1847, medians 0.174 and 0.173, so the gap is sim divergence, not step code. G7 owed under clean load.
- Programs and textures with the hook and rope on screen: 31 and 29 to 30 at q=1 and q=2, same as the base.
- Zip: chope-itch.zip in the scratchpad, 5977348 bytes, 78 files, md5 66f6b9b00f50a460504907f833f3d567. Not copied or published. The build boots to playing with 0 errors.

## canehook (B) - Kaypoh Hook renamed Cane Hook, root while throwing, bigger hook, stun, hit feel (2026-11-07)

- Snapshot: chope.pre-canehook.html (md5 ef183324). New page md5 2c96ca36. Build: proto-iconsB/patch3.py. ASCII only, no "kaypoh" left in the page.
- Rename: kit, HEROES ab, voice recipe key, weapon string and comments now say Cane Hook.
- Root: casting ability 2 sets rootT .45 and zeroes ground velocity. rootT zeroes move speed like a stun. Cleared on respawn and KO. Bots use the same code, so they get the same root.
- Throw: cast goes from .12 s to .25 s. New third person clip ACT.cane (arm cocked back and up, lean back, then an overhand fling). First person view model lifts and tips back, then pushes forward. Release adds shake .16 and a low whoosh.
- Hook size: hit radius .5 to 1.35. Mesh 2x (shaft .15 x 1.6, crook torus .4/.17). Rope width .035 to .07, with a 1.7x tug pulse for .18 s when the pull starts.
- Stun: hit target gets stunT max(.6, pull time + .2) and the same castT, unless a plunge or block is on. Bird form ends. The pull still moves under stun.
- Hit feel: cream burst and ring, impact sound, Ah Ma "ke-na" bark (b_ahma_kena). Thrower player gets hit-stop .07, bonk, shake .22, head hitmarker and a "KENA!" pop over the target. Victim player gets shake .3.
- Stun icons: star pip over stunned bots, star badge (--st-snare) in the player HUD while stunned.
- Tests (c1-dbg vs base, q=2): player stopped .45 s (27 frames), release at .25 s, then speed 6.6 again. Base: never stopped, release .133 s. Lateral sweep at 10 m vs rascal: base hits to .6 m offset, new hits to 1.2 m and misses from 1.3 m. Hook at 13 m: stunned .717 s, pulled .517 s. Reflected hook stuns Ah Ma .6 s and pulls .233 s, and all state clears after. HUD star shows while stunned and clears after.
- Gate canehook-B at load 3.98: 7/1, G7 0.1517 only, 0 console errors, G6 avg 60.5. G7 pairs on hawker under load 2.5: base 0.1168 0.1182 0.1148 0.1037, new 0.1247 0.1013 0.0975 0.1095, means 0.113 and 0.108, so flat.
- Programs and textures with the hook and rope on screen: 31 and 30 at q=1 and q=2. The hook adds 0 program keys.
- Shots: shots/canehook/.
- Zip: chope-itch.zip in the scratchpad, 5978120 bytes, 78 files, md5 722995c1db633f24142f1cdf3ff10161. Not copied or published. build/index.html boots to playing with 0 errors.

## kenafix (B) - Ah Ma bark only when Ah Ma threw the hook (2026-11-08)

- Snapshot: chope.pre-kenafix.html (md5 2c96ca36). New page md5 ad065219.
- hookHit: b_ahma_kena now plays only when the hook owner e.hk is 'ahma'. A reflected hook (owner Rascal) keeps the burst, ring, impact sound, hit-stop, bonk, shake, hitmarker and KENA! pop.
- Test proto-iconsB/t_kena2.js (player Rascal reflects a bot Ah Ma hook, q=2): base plays b_ahma_kena 1 time, new 0. Impact 1, bonk 1 and KENA! pop on both. t_kena.js: player Ah Ma plain hook plays b_ahma_kena 1 time on the new page.
- Gate kenafix-B at load 3.94: G7 0.1870 FAIL. Rerun kenafix-B2 at load 3.76: G7 0.1170 PASS, G6 avg 55.8, 0 console errors. G8 failed both runs with "Unexpected token '<'": /harness.js in the scratchpad root was deleted around 00:00 (proto-cards and proto-world9 harness.js are symlinks to it, now dangling, and several proto-* folders were emptied at the same time). Not caused by this change. G8 owed once harness.js is back.
- Zip: chope-itch.zip in the scratchpad, 5978121 bytes, 78 files, md5 6606dcaacdc04cffedd58cacaf204ff6. Not copied or published. build/index.html boots to playing with 0 errors and carries the guard.
