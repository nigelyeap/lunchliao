# Lunch Liao HD: improvements review

Reviewed 2026-11-16. Read-only pass on play/chope.html plus five bot matches in headless Chrome at 1600x900, DPR 1, on an M4.

- Line numbers refer to a snapshot of chope.html taken at 13:55 that day. Another agent was editing the file, so lines may have moved. Search for the quoted code if a line does not match.
- Screenshots are in the session scratchpad: `/tmp/lunchliao-scratch/shots/review/`. Paths below are short names in that folder. The scratchpad is temporary, so copy anything worth keeping.
- Matches played: Ah Ma on hawker, carpark and classroom. Siao on voiddeck. Rascal on wetmarket. Each ran about 30 s of autopilot play.
- Skipped on purpose: ability animations and first-person weapon models (being reworked).
- Effort: S under an hour, M a few hours, L a day or more. Impact: 1 to 5.
- Items marked DECISION are Nigel's call. They list options only.

## Top 10 (impact over effort)

| # | Item | Effort | Impact |
|---|------|--------|--------|
| 1 | HP bar shows mostly red when HP is high (ghost bar never drains under chip damage) | S | 5 |
| 2 | Centre screen callouts sit on the crosshair and the target | S | 4 |
| 3 | Death screen: title overlaps "Killed by", crosshair stays up, death cam goes inside props | S | 4 |
| 4 | Allies clip into the player's camera at spawn and in fights | S | 4 |
| 5 | Floating damage number lands on the scoreboard portraits | S | 3 |
| 6 | Objective waypoint text is covered by the world table marker | S | 3 |
| 7 | Carpark haze and a grey disc block the view | S | 3 |
| 8 | Auto quality drops to Low for the whole session after one slow match start | M | 4 |
| 9 | Onboarding is one 2.2 s subtitle | M | 4 |
| 10 | Early fights snowball into 0 to 9 stomps | M | 4 |

## Readability and HUD

### 1. HP bar ghost freezes under chip damage
- Wrong: in ahma_carpark_a.jpg the label says 110/570 and in ahma_carpark_b.jpg 78/570, but about 70 percent of the bar is red. It reads as "nearly full but hurt" when the player is nearly dead.
- Cause: setHP (around line 6125) sets `S.ghostHold = .4` on every hit. The tick (around lines 6207 to 6208) only drains the ghost when ghostHold reaches 0. DJ notes (9 per s), Ice Cream Uncle ticks (10 per s) and Stink clouds (every .5 s) keep resetting it, so the ghost stays at the pre-fight HP for the whole fight.
- Also the ghost colour (--signred #C8221B) is close to the low HP fill (--hp-low #FF3B2F). The two reds merge into one block.
- Fix: only set ghostHold when the ghost was already caught up (`if (S.ghost <= S.hp) S.ghostHold = .4`), or cap total hold at .4 s per fight. Make the ghost a pale colour (cream or white at 60 percent).
- Effort S. Impact 5.

### 2. Callouts cover the crosshair
- Wrong: "WAH LAU!" and "+1 ELIM +25 XP" sit right on the crosshair and the enemy (rascal_wetmarket_b.jpg, ahma_carpark_a.jpg). "MORE DAMAGE!" covers the top third of the screen and the enemy head (ahma_classroom_b.jpg).
- Fix: move big callouts to the upper third, above the scoreboard line, and shrink them by half. Keep "+1 ELIM" small and offset below-right of the crosshair. Fade them in 0.6 s.
- Effort S. Impact 4.

### 3. Death screen overlaps
- Wrong: the giant "Kena chope'd!" overlaps the "Killed by" line. The crosshair stays visible while dead. The death cam sat inside an umbrella mesh in ahma_hawker_c.jpg, so the player saw a flat colour.
- Fix: stack the two lines with a gap. Hide the crosshair when `#death` is shown. Raycast from the corpse to the death cam position and pull the camera in front of the first hit.
- Effort S. Impact 4.

### 4. Allies inside the camera
- Wrong: at countdown the NSF ally blocks the view and another ally head clips at the right edge (ahma_hawker_cd.jpg). In siao_voiddeck_a.jpg an allied Ah Ma head fills the right quarter of the screen during play.
- Fix: fade ally meshes to 30 percent or hide them when closer than about 1.5 m to the camera. Spread spawn points so allies do not start inside each other.
- Effort S. Impact 4.

### 5. Damage number over the scoreboard
- Wrong: "408" draws on top of the team portraits (rascal_wetmarket_b.jpg). It happens when the target is high in the view.
- Fix: clamp damage numbers below the scoreboard band, or draw the scoreboard above them.
- Effort S. Impact 3.

### 6. Waypoint text under the world marker
- Wrong: "Go chope table B · 6m" is covered by the big "B" marker when the table is ahead (ahma_hawker_a.jpg, siao_voiddeck_a.jpg).
- Fix: put the waypoint line above the scoreboard timer, or hide it when the marker is on screen and within 15 m.
- Effort S. Impact 3.

### 7. Countdown digit on the crosshair
- Wrong: the countdown number sits exactly on the crosshair (ahma_hawker_cd.jpg).
- Fix: move it up by about 15 percent of screen height.
- Effort S. Impact 2.

### 8. Team colour only by rim and outline
- Wrong: there is no colourblind option (zero matches for colorblind in the file). Enemy outline is chilli red 0xff2f5e (line 2285). On red-heavy scenes like the hawker canopy (ahma_classroom_a.jpg shows a large red sheet) enemies lose contrast.
- Fix: add an option to pick the enemy outline colour, with yellow or magenta presets.
- Effort M. Impact 3.

### 9. No killcam or "who hit me" direction
- Wrong: the only info after death is the killer name. There is no replay or damage direction summary.
- Fix: a simple death recap card (killer hero, damage taken by source in the last 5 s) is cheaper than a killcam.
- Effort M for the recap, L for a killcam. Impact 3.

## Game feel and match flow

### 10. Early snowball
- Wrong: on hawker after about 37 s the player team had 0 elims and 10 deaths. Lens, Gym Hunk and Siao on the other team were each 3 to 0. Score 10 vs 28. Four of five allies were dead at 4:44.
- Other matches were close (carpark 36 vs 28, classroom 10 vs 12, voiddeck 11 vs 15, wetmarket 11 vs 10), so this is a variance problem rather than a constant one.
- Fix options: respawn waves so allies return together, a short respawn time for the losing team, or bots that wait for a regroup when 3 or more allies are down.
- Effort M. Impact 4.

### 11. Classroom fights are slow to start
- Wrong: classroom scored 10 vs 12 after 28 s, the lowest action of the five maps. The table ring and desks slow movement.
- Fix: check lanes from spawn to table B. Remove a desk row or two to open one direct route.
- Effort M. Impact 2.

### 12. Turret numbers do not match the comment
- Wrong: the turret block (lines 5058 to 5072) has a comment saying 9 dmg, .4 s acquire, 40 m/s. The code does 12 dmg, .15 s acquire, 75 m/s. The code version is much stronger.
- Fix: decide which is intended and make the comment match. Changing the numbers is a DECISION (see below).
- Effort S. Impact 2.

### 13. Ah Ma melee data is dead
- Wrong: meleeStrike (lines 4173 to 4182) uses hard-coded 50 and 82 for Ah Ma. `HEROES.ahma.melee.dmg` is 65 and is never read.
- Fix: read the value from HEROES, or delete the field so nobody tunes it by mistake.
- Effort S. Impact 2.

## Bots

### 14. Stuck bots
- Wrong: `__chope.stuck` was 1 on carpark and on classroom. Voiddeck, wetmarket and hawker were 0.
- Fix: log the stuck position per map (the hook already counts it), then patch the nav mesh or add a jump-out nudge after 2 s stuck.
- Effort M. Impact 2.

## Performance

### 15. Auto tier drops and stays down
- Measured: hawker on Medium tier gave median 16.7 ms, p95 50 ms, max 100 ms, 447 main draw calls and 815 total. autoTier then dropped to Low and stayed there for the session. Carpark on Low still had p95 33 ms (566 calls). Classroom on Low was clean (602 calls). After a page reload, voiddeck and wetmarket on Medium were clean (p95 16.8 ms, 810 and 858 calls).
- Reading: the spikes cluster at match start. They look like shader compiles and first-use uploads. One bad start costs the player Medium quality for the whole session.
- Fix: call `renderer.compile` on the scene, and play one frame of each hero FX offscreen, during the countdown. Ignore the first 5 s of a match in autoTier. Let the tier climb back up after 3 good windows.
- Effort M. Impact 4.

### 16. Draw calls
- Measured: 815 to 858 total draw calls on Medium. Not a problem on the M4. It will be on integrated GPUs.
- Fix: merge static map props per material at load. Instance repeated stools and tables.
- Effort L. Impact 3.

## Onboarding and menus

### 17. Onboarding is one subtitle
- Wrong: the only tutorial is a 2.2 s delayed `sub()` line for the first two games (line 5146). Abilities, ult charge, table capture and the challenge card are never explained.
- Fix: a 3-step first-match overlay: move and shoot, stand in a ring, press 4 for ult when the dial is full. Show each once and save it to the profile.
- Effort M. Impact 4.

### 18. Hero select layout
- Wrong: the card grid fills the top half and the bottom half is empty. Start is far from the detail panel. HEALTH and SPEED bars have no numbers. The "M0" mastery badge is unexplained. There is no role filter (02_herosel.jpg).
- Fix: put Start under the detail panel. Add the number next to each bar. Add a tooltip for mastery. Add role tabs (damage, tank, support).
- Effort M. Impact 3.

### 19. Main menu nav is cramped
- Wrong: "FULL SCREEN" and "CREDITS" nearly touch (01_menu.jpg).
- Fix: add a gap or a separator dot.
- Effort S. Impact 1.

### 20. Console 404s
- Wrong: `assets/logo_lunchliao_preview.png` returns 404 on every load. `maps/carpark_ao.json` and `maps/classroom_ao.json` also 404. The AO ones fall back fine but still show as errors.
- Fix: add the logo or remove the reference. Check for the AO file with a HEAD request first, or list available AO files in the map manifest.
- Effort S. Impact 1.

## Audio

### 21. No findings from play
- Headless Chrome had no audio output, so the mix was not heard. Code review only: samples load from `sfx/` through decodeAudioData (line 1112). The AudioContext waits for the first input (line 1351). Six volume sliders exist (line 5173).
- Next step: a 10-minute listen on a real machine for loudness balance between ults, footsteps and callouts.

## Settings

### 22. No FOV slider
- Wrong: the settings panel has sensitivity, volume and key rebind (lines 703, 5173, 5197). FOV is fixed at 78 (line 6464). Some players get motion sick at 78.
- Fix: add a 70 to 100 slider and use it as the base value in that line.
- Effort S. Impact 2.

## DECISION items

### D1. Hero balance numbers
VISION.md says hitboxes and gameplay numbers come from ref/chope.html and changing them is Nigel's call. These are smells from the HEROES table (lines 818 to 875). They are not verified with a large sample.
- Siao: about 95 DPS (44 per .465 s), 340 HP, speed 8.2, 120 degree cleave, plus Predator invisibility. Went 3 to 0 on hawker.
- Gym Hunk: tank with 575 HP and about 81 DPS. Speed 7.6 is faster than several damage heroes.
- Ice Cream Uncle: support with 375 HP, 70 DPS cone, slow, 2 s freeze, Cold Snap freeze and a 1 s stun cart.
- Rascal: size .75 (smallest hitbox), speed 8.6 (fastest), about 69 DPS on 285 HP.
- DJ: 21 HPS passive aura.
- Engineer: about 40 DPS. Head Prefect: 34 to 68 DPS. Both look low next to the above.
- Options: keep the ref numbers. Run a bot-only sim with `__chope.step` and fxOff over 100 matches and tune from that data. Tune by hand from player feedback.

### D2. Turret strength
- Options: keep the code values (12 dmg, .15 s, 75 m/s). Go back to the comment values (9 dmg, .4 s, 40 m/s). Pick a middle point after the sim in D1.

### D3. Match length and score target
- SCORE_TARGET is 150 and MATCH_LEN is 300 s (around line 899). In five matches scores were 10 to 36 after about 30 s.
- Options: keep. Shorten to 180 s for mobile-length sessions. Raise the target so matches more often go to time.

### D4. Hitbox sizes
- Rascal at .75 is the main outlier.
- Options: keep the ref sizes. Normalise hitboxes and keep visual size different. Scale HP to hitbox size.

## How these were measured
- Driver: a copy of play/tools/cdp.mjs in the scratchpad, using the `?q` test hooks (`__chope.start`, `setMap`, `autopilot`, `ents`, `score`, `drawCallsAll`, `tier`, `stuck`).
- Frame times: 180 rAF samples per match, about 9 s in.
- Note for future runs: `__chope.comp` cannot change the player hero. profile.hero is read once at boot, so set `chope-profile` in localStorage and reload, or pick through the hero select UI.
