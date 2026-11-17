# play/chope.html changes (for reviewer A)

Base: copy of ref/chope.html. All edits are in play/chope.html unless noted.

## Serving
- serve.py: threaded static server, no-store cache, glb mime type. Run `python3 play/serve.py 5302` from the repo root and open http://localhost:5302/chope.html. Add `?q` for test hooks.
- Symlinks in play/: heroes, maps, layouts (tools/blender/maps_toy/layouts), kaykit, sfx, three, assets. The importmap points at the three symlink.

## Heroes
- All 13 heroes load from heroes/<key>.glb (toyMesh). Each uses its own clips.
- Shape keys are driven through the existing expression hooks (TOY_EX table).
- HDL (head height, bar height) is recomputed per hero from the glb bounds (TOY_HDL). Scale is 1/size.
- Hitboxes are unchanged. Head spheres were moved onto the toy heads because the toy heads are large. Body and leg spheres are the old ones.
- Team rings are removed on toys. Team reads from rim colour, outline and bars.

## Maps
- Each map loads maps/<id>.glb in place of the procedural dressing (toyMapEnv).
- Solids come from layouts/<map>_solids_vN.json (SOL_FILE table) in place of mapSolids(). Loaded before boot (solReady).
- A RoomEnvironment PMREM is set as scene.environment at intensity .55 on toy maps. The glb materials are PBR and look flat without it.
- FAN_* nodes spin. STEAM_* nodes rise, scale and fade on a loop.
- Wet market shutter hazards drive the glb SHUTTER_* nodes. The procedural shutter meshes are removed.
- All toy map meshes receive shadows. Graphics tiers and autoTier are untouched.

## Bot nav
- genNav(): 1 m grid, one node per standing level per cell, nudged inside the cell to dodge furniture. Links are walked in .15 m steps with the same step rule as collide() (.46 m). Shutter links get the 's' flag. Only nodes reachable from the spawns are kept.
- The generated nodes and links replace MAP.nodes and MAP.links before buildNav. Spawns, zones, holds and chokes still come from the old map JSON.
- Classroom stairs and the bridge to L2 (y 3.5) are in the graph. Tested by sending bots to L2 goals.

## Test hooks
- __chope.navg and __chope.sol expose the generated nav and loaded solids.

## maplook (2026-11-16): toy maps closer to the Blender renders
- Toy map meshes carry userData.tm and write alpha .25 in the normal prepass. The comp shader reads that tag: no normal or depth ink on map pixels, neutral SSAO there (strength TOYL ao), AgX Punchy tone map (agxP) instead of neutral plus grade. Heroes keep ink, rim, grade and the enemy outline (alpha 1).
- Toy maps turn off ceiling gloom and cloud shadows, vignette .2, per-map fog from TOYL.
- TOYL table: hemi, sun, fog, env, expoA, sat, ao, aoB, shI per map, tuned against shots/maps_toy. Shadows are PCFSoft on Medium (baked) and High.
- Fixes: sun.shadow bias line and setTier shadowMap.enabled line were swallowed by comments. setTier no longer strips receiveShadow from toy map meshes on Medium.
- Resolution: Medium pr 1.5 (was 1), High pr 2 with MSAA 4 (was 1.5). autoTier first drops Medium to pr 1, then to Low. Never saved.
- Baked AO: maps/<id>_ao.json switches to <id>_lit.glb plus the AO PNG (flipY false, linear, uv channel 1) on the listed meshes. Shared materials are cloned. SSAO drops to aoB. Missing or bad files fall back to <id>.glb. Tested on hawker (51 of 74 materials take the map).
- Tools: play/tools/maplook.mjs (Blender camera, fp, tp shots), montage.py, perf.mjs, cost.mjs. cdp.mjs captures JPEG and converts with sips, since PNG capture hangs headless Chrome mid-match.

## Abilities feel (2026-11-16): every hero ability shows anticipation, release and follow-through
- Backup: play/chope.html.bak_abilities (before this pass), play/chope.html.bak_ui (before the UI items below).
- Viewmodel make(): additive ability layer (vm.ab(S), abS, abT). R and G offsets add to the hand groups, L now has its own offset and rotation, hA hides A for a window. Clips end by themselves.
- AB table (one entry per ability, 13 heroes): w is the wind-up that lands on the real cast (pendF), rd delays the release for ults, d is the clip length. R, L, G or RK, LK, GK give the first person poses. c is [pitch deg, roll deg, fov] for the camera punch, s is shake, hs is hit stop, f(e,P) is the world VFX from the existing helpers (burst, ringFx, confetti, spr, decal through abX), tp gives the third person cast pose through apC.
- abGo runs on tryAbility success, at the end of tryUlt, from stunGo (Siao Stun) and from rulerRelease (Rascal Ruler Slice release). abRel fires at the pendF landing, after rd, or at once. Gameplay numbers, timings, cooldowns and hitboxes are unchanged. The release never delays the cast.
- Camera punch (abC) decays at exp(-8 dt). It is skipped under REDUCED or with FEEL off. FX_OFF skips the VFX. autoTier is untouched.
- Test hook: __chope.fxe exposes FXE.
- Verified: scratchpad cast_all.mjs casts all 52 slots in first person. Every castable one returns true and no console errors were logged. Siao 2 is passive. Shots are in shots/abilities, sheet is shots/abilities/contact_sheet.jpg.
- Perf, tier 2, FAST=1. Match (perf.mjs): hawker 40.98 ms avg before, 32.0 to 43.0 after over three runs. Wet market 37.56 before, 32.3 to 38.7 after. Ability spam (uncle, ahma, dj, gym): 53 to 58 ms avg before, 37 to 40 after. Geometry and texture counts are flat.

## UI (2026-11-16)
- Callout: clamp(16px,2.2vw,26px), sits under the score bar where the objective line was, 1.5px stroke, 2px shadow, no tilt, 1 s fade. Streak scale capped at 1.2. The hot colour stays and the glow is gone. The reduced motion rule is unchanged.
- Waypoint hints removed: #obj, objTxt and lastObj are gone, along with the callout code that hid #obj. Zone markers, pips and the capture bar stay. The range mode rule no longer names #obj.
- HP ghost: setHP starts the 0.4 s hold only when the ghost had caught up, so chip damage keeps draining it. The trail colour is now pale cream at 60 percent. Checked with 20 ticks of 5 HP: the gap stays under 10 HP. Before the fix it grew to 100.
- Shots: shots/ui/callout_before_after.jpg, shots/ui/hp_before_after.jpg.
- Known test issue: headless Chrome sometimes stops answering CDP mid-run (no JS runs while stalled). The pre-change backup stalls the same way, so the cause is the headless setup and not this pass. Rerun the affected heroes with HEROES=... when it happens.

## Reload for ranged heroes (2026-11-17)
- Backups: play/chope.html.bak_reload_all and play/tutorial.js.bak_reload_all (before this pass). Design and landed differences: play/RELOAD_BUILD.md.
- MAG table: uncle 6 / 1.6 s, engineer 5 / 1.5, rider 12 / 1.6, rascal 15 / 1.4, dj 60 / 1.8, ice 60 ticks / 1.8 (tank). nsboy and lens keep their bands. Tarik and Head Prefect have no reload.
- Primary damage up 25 percent for uncle, engineer, rascal, dj, ice, nsboy and lens. Rider up 40 percent. Kit text matches.
- RLV clips: one first person reload per hero with prop meshes (PROP table) and sound cues. Lens has a battery swap. NSF keeps the band clip. Props are dropped and hand moves shrink under REDUCED.
- RL3 table: third person reload pose for the six new heroes, played through apC.
- Ammo counter: mags over 10 and the ice tank show a bar. The tank reads in percent. Infinity shows only while the ult makes shots free.
- Bots reload after 2 s with no target.
- Tutorial: the reload lesson reads MAG, so it runs for every hero with a mag.
- Verified: scratchpad rl_test.mjs (mag drains, reload refills, counter text) and tools/tutorial_test.mjs with MODE=skip pass for all heroes. Shots are in shots/reload_all.

## Reload clip fixes, Scaffolding Wall, Longkang Juice (2026-11-17)
- Backups: play/chope.html.bak_reload_anim (before the clip fixes), play/chope.html.bak_uncle_goo and play/tutorial.js.bak_uncle_goo (before the Stinky Uncle rework). tutorial.js did not need a change.
- Reload clips (RLV, PROP). DJ, Recess Rascal and NSF are untouched. Birdwatcher: the camera tilts to show the battery door, the old battery drops from the slot and out of view, the hand brings the new one up from below and pushes it into the same slot. Stinky Uncle: a first person nose dig, the off hand comes back with the booger (new boog prop). Delivery Driver: the hand dips below the view and comes back up with the chopsticks. Engineer and Ice Cream Uncle: retimed for an empty off hand.
- Off hand items are hidden in first person for Engineer, Stinky Uncle, Delivery Driver and Ice Cream Uncle (KK.vm), in play and during reload. Mag sizes, reload times, damage and bot reload logic are unchanged.
- Engineer ability 2 is now called Scaffolding Wall (kit entry and ability list). The internal kind is still wall.
- wallGeo(): the wall is a scaffolding panel. Three pipe uprights on orange feet, three ledgers, an X brace on the back, green netting with a grid, two planks and a yellow and black hazard strip. Same 4.5 x 2.2 x .4 footprint, so the hitbox, HP, aim ghost and rotation are unchanged. Still one merged vertex colour mesh on WALLM, about 560 tris. The HUD icon is still the old wall art.
- Stinky Uncle ability 3: Air Out is removed. Longkang Juice replaces it. Cast .35 s, cooldown 10 s. A strip 14 m long and 3 m wide lands on the floor in the aim direction and lasts 4 s. It stops at walls. Enemies inside get a 35 percent slow, 12 damage a second (6 per half second) and 1 Stink stack per full second. No knockback, allies are not affected. Numbers live in the GOO constant.
- Goo code: gooThrow, gooTick (called from updateDeployables), gooMesh (one canvas texture and one material, pooled quads). clearDeps clears the strips. The strip is flat at the caster's floor height and does not follow stairs (ponytail comment in the code).
- Stink pop: at 3 stacks the stacks pop for STINK_POP (40) damage with a green puff, ring and the stink sound, then reset to 0. Side effects: a Durian Drop hit and a Kopi boosted direct booger give 3 stacks, so they pop at once for 40 more.
- Chewing Gum: stuck for 1 s as before, then a 60 percent slow for 3 s. Before it was 30 percent for 1.2 s. The slow cap in speedFactor moved from 50 to 60 percent to allow it. Damage and charges are unchanged.
- Kit text, the ability list, FX recipe, AB.uncle3 (first person fling and third person throw pose) and the bot line are updated. Bots cast when the target is on the same level within 12 m, or within 19 m and closing fast. They back off at 2 stacks now. The Air Out flap code is removed. The h_uncle_flap sound alias is left unused.
- Icons: the ability list reuses the stink icon. The HUD slot uses a placeholder (longkang) made from the old Air Out lines over a green puddle.
- Verified: scratchpad gate.sh (syntax, rl_test.mjs, tools/tutorial_test.mjs). A live match check measured the goo damage, the stacks at 1, 2 and 3 s and the pop of 40. Shots are in shots/reload_anim, shots/scaffold_wall and shots/uncle_goo.

## Fix pass 2: hands, goo, scaffolding icon (2026-11-17)
- Backup: play/chope.html.bak_fix2. No balance numbers changed.
- Rule for this pass: show as little arm as the move needs. Hands peek in from the bottom or the side edge.
- Birdwatcher reload: the battery door is bigger and tilts further toward the camera. The hand wraps its fingers round the battery. Only the fingertips and the battery show.
- Stinky Uncle reload: the off hand has a pointing pose (index out, other fingers curled). The hand and a bit of wrist rise at bottom centre, dig, and come back with the booger.
- Delivery Driver reload: the hand drops fully below the frame. The chopsticks hide only while the hand is off screen (S.hide) and come back up in the hand.
- Props can now sit in view space (on:'V') and take a skin colour (propGeo(n,sk)).
- Longkang Juice first person: the fling arm is shorter and stays low on the left, clear of the crosshair.
- Longkang Juice third person: bigger swing from behind to the front with a lean, held to .8 of the cast. Toy bodies ignore arm channels, so the toy pose code now swings the upper arms for clips marked arm:1 and for the RL3 reload keys.
- Goo strip: 28 rows sample floorAt along the strip, so it follows steps and ramps. A row stops the strip when the floor jumps more than .45 m. The wall check is still one flat ray 1.3 m above the caster, so the strip ends where a staircase passes about 1.3 m (ponytail comment in the code).
- Scaffolding Wall HUD icon: pipe frame, diagonal brace, plank and green netting replace the brick wall.
- Fallback hero builders: off hand items removed for Engineer, Stinky Uncle, Delivery Driver and Ice Cream Uncle.
- Reload check: for all eight reload heroes the mag refills and every sound cue in RLV fires at its time (logged through AU.play). Third person reload poses were shot at 25, 50 and 75 percent.
- Test hook: floorAt and wallDist added to window.__chope.
- Known weak spots: the nose dig is foreshortened. The battery grip hand is blobby. The toy arm swing uses only the upper arm x rotation, so reload poses are rough. Lens and NSF have no third person reload arm pose. The stairs shot is on voiddeck because hawker, wetmarket and carpark have no step runs.
- Shots are in shots/fix2.

## Reload fix pass 3

- Stinky Uncle nose dig (first person). The pointing hand comes in from the lower left, the finger goes into the nostril, wiggles for a beat, then pulls out with the booger on the tip. Sound cues moved to match (0.5, 0.6, 0.78, 1.2 s). Reload time is unchanged.
- Lens battery swap (first person). The camera is held closer and tipped further, the batteries are 1.25 times bigger, and the fresh battery has a green label. The gripping hand has a thumb with a nail and three fingers.
- Longkang Juice (first person). The off arm is hidden while it is out of view. Only a hand on a small red pail shows at the lower left.
- Third person reloads. The elbow now bends with the arm swing. Lens and NSF play the generic reload arm keys. Ability throws keep a straight arm.
- Fix: a first person prop slot is rebuilt when another clip of the same hero needs a different prop there (uncle reload, then the pail).
- No balance numbers changed. Shots are in shots/reload_all/pass3/.

## Fix pass 4

- Longkang Juice range is up 40 percent. The strip is now 20 m long (was 14). The mesh, the aim arrow, the hit test, the wall stop and the bot check all read the same value. Kit text updated.
- Stinky Uncle reload: the nose and nostrils from pass 3 are removed. The finger motion is unchanged.
- Boot screen: the logo is text now. It stays hidden until the slab font has loaded, so it does not flash in Georgia. The old 404 for the missing logo image is gone.
