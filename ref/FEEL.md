# FEEL.md - WP23 game feel (game feel designer)

Everything here adds to the current feel code. Nothing is replaced except the white-noise shake (F5, optional).
Hit spheres, move speeds and the 9 kits are untouched. No new screen text. No voicelines.

## Files
- `proto-feel/build_feel.py` applies 26 anchored patches. Each anchor is asserted to match once.
  - `python3 proto-feel/build_feel.py` builds `proto-feel/chope.feel.html` from `proto-feel/base.html` (frozen copy of proto-port/chope.demo.html).
  - `python3 proto-feel/build_feel.py chope.html` builds `proto-feel/chope.wp23.html` from the live game. All 26 anchors match the current chope.html once.
- Every change is gated by `FEEL`. `?feel=0` on the same file is the before build.
- `proto-feel/feel-cdp.mjs shots|fov|perf`, `proto-feel/bench.mjs`, `proto-feel/smoke.mjs`: headless drivers (CDP on 9396, server on 8796). `PAGE=chope.wp23` points them at the live-game build.
- Shots in `proto-feel/shots/` (taken on chope.wp23.html): `before_*` and `after_*` for headshot_stack, hit_from_behind_left, death, respawn_0s, end_1s, end.
- `proto-feel/kaykit` is a symlink to `../kaykit` so the copy loads the same assets.

## Cost (all builds, headless Chrome, M-series, 1920x1080)
- Draw calls added: 0. Everything is DOM/CSS in the existing HUD root or camera math.
- Frame time over a 25 s autopilot fight: p50 16.7 ms, p95 16.7 ms, p99 16.8 ms in both builds (vsync bound).
- Per-event costs are inside run-to-run noise (other agents share the machine). Ranges over 4 runs each:
  - enemy hit by player: 77 to 117 us before, 78 to 130 us after. The existing dmgNum reflow dominates.
  - player hurt: 38 to 69 us before, 42 to 75 us after.
  - hud.tick: +0.4 us (diTick loop over 4 pooled arcs).
  - player shot (rider): 50 to 108 us before, 64 to 94 us after. One Web Animation, previous one cancelled.
- 30 s autopilot smoke on chope.wp23.html: 0 uncaught errors, 0 console errors, both builds.

## Ranked changes
1. **F2 Damage numbers stack per target.** Hits on the same target inside a live number add into it. The number pops (scale 1.35 to 1), holds, then rises. Kind keeps the strongest (body < head < crit < kill). Before: three overlapping "18"s. After: one "54". Feels like Apex and OW2, and it lowers clutter. Risk: low. Uses the same 12-slot pool.
2. **F1 Headshot and crit hitmarker, plus head-kill ding.** Head or crit hits show kaya-yellow, thicker slashes with a .2 s scale pop. A head kill layers the existing `ui_head` under the kill sound. Before, `hitmarker()` mapped head to plain hit. Risk: low.
3. **F3 Damage direction arc.** A red arc on a 190 px ring around the crosshair points at the attacker. It follows your turning for .9 s, one arc per attacker, 4 pooled. It skips DoT and self damage and clears when you die. Every modern shooter has this. You can now tell where a flank comes from. Risk: low. Watch for clutter in 3v3 focus fire (max 4 arcs).
4. **F8 MVP shot at match end.** The receipt waits 2.2 s while the camera frames the MVP from the first open side (wall-ray tested) with a slow push-in. The in-game HUD and the MVP's HP bar are hidden. The MVP cheers even on the losing team. A downed MVP is respawned on its mat for the shot. Any click or key skips. Without it, the camera orbit sits behind an opaque receipt and is never seen. Risk: medium. It changes end pacing. **Needs the user** (see below).
5. **F6 Ult cast two-phase FOV + F7 ult meter gain pop.** Cast zooms in 6 deg for .2 s, then kicks out toward +8 for .25 s and settles. The camera lerp makes the measured peak +2.8 (old: in 6 deg for .3 s). Timeline 78, 74.9, 73.0, 74.8, 78.8, 80.8, 79.4, 78.2, 78. The ult plate pops (scale 1.2, brighter) on any 5%+ gain, so big plays visibly charge it. This covers the payoff that the removed ult name text used to carry. Risk: low.
6. **F4 Respawn drop-in + killer HP left.** On respawn the FOV snaps to 100 and the existing lerp pulls it to 78 in about .4 s (96, 89, 84, 82, 80, 79, 78). The death card adds "· N HP left" in kaya after the killer name. Short, factual, and it tells you if the fight was close. Risk: low. Off under reduced motion (FOV part).
7. **R3 Crosshair kick on fire.** The crosshair scales open by 22% of the vkick strength and settles in 110 ms. It hangs off `vkick()`, so every ranged primary and kick ability gets it, and melee does not. Uses the CSS `scale` property, so it stacks with the head pop. Risk: low.
8. **F5 Smooth shake.** Same amplitude and decay. Two sines per axis at 7 to 15 Hz replace per-frame `rand()`. Shake reads as a thump instead of jitter at high fps. Risk: low, optional. Skip it if anyone prefers the current rattle.

## Critique rounds (short)
- Round 1 (F1 to F8): numbers and markers good. The MVP cam was invisible behind the opaque receipt. The arc stayed on the death screen. A dead MVP got no shot.
- Round 2: receipt hold 2.2 s with skip, HUD hidden, arc clears on death, MVP respawn for the shot, HP bar hidden.
- Round 3: no fire feedback on the crosshair compared with Valorant, OW2 and Apex. Added R3 and cancel-before-animate so animations never pile up. Remaining gaps vs modern shooters, not built: play-of-the-match replay (needs a ring buffer of entity transforms, real cost), kill-cam replay, hit-confirm haptics.

## WP23 feel steps (for B, one at a time. Patch numbers are list indices in build_feel.py)
Keep `const FEEL=!/[?&]feel=0/.test(location.search)` as a test flag, like `?q&weapons=current`. Or drop the `FEEL&&` guards when landing. Snapshot before each step.

- **Step 0: gate + CSS** (patches 0, 1). The CSS block goes before `<script type="importmap">`.
  - A check: `?feel=0` and plain URL both boot with 0 console errors.
- **Step 1: F2 stacking** (5, 6, 7).
  - A check: call `damage(e,18,player,{})` 3 times, 80 ms apart, on one live enemy. Exactly one `.dn.on` exists and its text is `54`. With `?feel=0` there are 3.
- **Step 2: F1 head marker + ding** (2, 3, 4).
  - A check: after `damage(e,18,player,{head:true})` on a live enemy, `.xh` has class `head`, and gets `xh` back after .2 s of hud.tick. A head kill calls `AU.play('ui_head')` (spy on AU.play).
- **Step 3: F3 direction arc** (8, 9, 10).
  - A check: enemy 6 m behind and 4 m left. After `damage(player,12,e,{})` one `.f23-di.on` exists. Its rotation is within 0.05 rad of `atan2(-4,-6)` = -2.55. It is gone after 1 s, and on player death right away.
- **Step 4: F6 + F7 ult** (14, 15, 16, 17).
  - A check: set `player.ult` to the cost, call `ult()`, and sample `camera.fov` every 50 ms. The minimum is below 75, the maximum above 80, and it is back to 78 within 1 s. Raising `player.ult` by 10% adds class `gain` to `#ab4`.
- **Step 5: F4 respawn + HP left** (11, 12).
  - A check: kill the player with an enemy at 40% HP. `#deathBy` contains `HP left`. On respawn the first fov sample is above 90 and reaches 78 within .6 s.
- **Step 6: R3 crosshair kick** (25).
  - A check: as a ranged hero, after `fire()`, `.chud .xh` has exactly 1 running animation. With 20 fires in a row it is still 1.
- **Step 7: F8 MVP shot** (18 to 24). Land this only after the user answers.
  - A check: set `score[1]=100`. At 1.2 s, `#end` is hidden, `.chud` is hidden, and the camera is within 4 m of the MVP. At 3.5 s `#end` is visible. A pointerdown at .5 s shows `#end` at once.
- **Step 8: F5 smooth shake** (13), optional.
  - A check: `shake(.35)` and sample camera.position.x offsets over 10 frames. Mean absolute frame-to-frame change is lower than with `?feel=0`, and the peak offset is within 20%.

## Needs the user
- F8: is a 2.2 s MVP hold before the receipt OK? Skippable with any click or key.
- The kill streak callout and killConfirm text are on screen today. They could be clutter candidates for WP22.2, A's list. I did not touch them.
- Unrelated, pre-existing: clicking Play before the boot finishes throws in `startMatch` (`map` is null). Only seen when a script clicks early.
