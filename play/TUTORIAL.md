# Tutorial

An interactive course that teaches the game inside a real match. It lives in `play/tutorial.js` (logic and CSS in one file). The game file needs a three line hook, listed below.

Status: built and tested against `play/chope_tut.html`, a copy of `chope.html` with the hook applied. The hook is not in `chope.html` yet.

## How to try it

```
cd ~/Documents/lunchliao-hd && python3 play/serve.py 5310
open http://localhost:5310/chope_tut.html
```

Click **Tutorial** under Practice Range in the main menu. Pick a hero (NSF is the default) and press Start tutorial. A first time visitor also gets a small offer card on the menu. It can be dismissed and never shows again.

During the course:

- The panel on the left shows the step, the tasks and the keys. Keys are read from the live bindings, so rebinding works.
- `Enter` skips the current step. If Enter is bound to something, the skip key falls back to `\`, then F2, then F4.
- `P` pauses. The pause screen has Restart tutorial and Quit to menu.
- Completion is stored in localStorage under `chope-tut`. The menu button shows a "New" tag until then.

## Steps

The game has no sprint key. You always run at full speed, and the slide is the burst move. The slide step says so.

| # | Step | What the player does |
|---|------|----------------------|
| 1 | Look around | Move the mouse left, right and up |
| 2 | Walk | Press each of the four move keys |
| 3 | Jump | Jump once |
| 4 | Crouch | Hold crouch while standing still |
| 5 | Slide | Run, then tap crouch |
| 6 | Slide, then jump | Hold crouch to slide, jump before it ends |
| 7 | Go to the marker | Follow the world marker to the target |
| 8 | Shoot | Hit the target three times |
| 9 | Headshots | Land a headshot (heroes that can headshot only) |
| 10 | Knock out | Finish the target, see the kill feed |
| 11 | Reload | Reload the band (NSF and Birdwatcher only) |
| 12 | Quick melee | Melee the target |
| 13 to 15 | Abilities 1, 2, 3 | Use each one. The panel says what it did. A passive slot becomes a reading step |
| 16 | Charge the ult | Deal damage until the meter is full |
| 17 | Use the ult | Fire it |
| 18 | Wet floor | Walk over the wet patch |
| 19 | Score and tables | Reading step on the HUD |
| 20 | Chope table A | Stand in the ring until it is yours |
| 21 | Tables make points | Reading step |
| 22 | Contested | An enemy sits on table A. Clear it and take the table back |
| 23 | Find a pickup | HP drops to 35 percent. Walk to the healing pickup |
| 24 | Status effects | You get slowed. Watch the chip until it ends |
| 25 | Scoreboard | Hold Tab |
| 26 | Practice round | 3 versus 3 against easy bots, first to 25 points |

Then a finish screen with a recap and buttons for a real match, the practice range, another run or the menu.

## Hook patch for chope.html

Landed in `chope.html` on 16 Nov 2026 at 21:44. The file before the hook is `play/chope.html.bak_tut`. The line numbers below are from that backup.

Line numbers are for the `chope.html` of 16 Nov 2026 (8839 lines, as of 21:44). The script `play/tools/apply_tutorial_hook.py` finds the anchors by text, so it still works after the file moves.

```
cd play && python3 tools/apply_tutorial_hook.py chope.html chope_tut.html   # build the test copy
cd play && python3 tools/apply_tutorial_hook.py chope.html chope.html       # land it for real
```

It stops with an assert if an anchor is missing or appears twice.

### 1. Line 6678, inside the entity loop of the frame step

Old:

```js
RANGE&&e.team===2?rangeDummy(e,dt):updateBot(e,dt)
```

New:

```js
(RANGE&&e.team===2)||e.dummy?rangeDummy(e,dt):updateBot(e,dt)
```

Tutorial targets carry `e.dummy=true` and use the practice range dummy brain. Nothing else sets `dummy`, so normal matches run the same code as before.

### 2. Line 8838, a new line just before `if(TESTQ)window.__chope={`

```js
window.__tut={THREE,scene,camera,HEROES,HUD,hud,SFX,AU,zones,pickups,keys,profile,BINDS,BND,SL,bindOf,kn,saveProfile,startMatch,applyMap,makeEnt,freeEnt,tbBuild,gainUlt,applyStatus,ringFx,confetti,portrait:k=>heroPortrait(k),get ents(){return ents},get player(){return player},get state(){return state},get paused(){return paused},get HAZ(){return HAZ},get map(){return map},get matchT(){return matchT},set matchT(v){matchT=v},get score(){return score},set cdT(v){cdT=v},set RANGE(v){RANGE=!!v},set comp(v){compOverride=v},get botSkill(){return botSkill},get onDamage(){return onDamage},set onDamage(f){onDamage=f}}; // tutorial.js hook
```

The game is one ES module, so its internals are out of reach from another file. This object hands over the ones the tutorial uses.

### 3. Line 8839, after the closing `</script>` of the module

```html
<script src="tutorial.js" defer></script>
```

If a name in the `__tut` line gets renamed in `chope.html`, the page throws a ReferenceError at boot. Fix the name in the hook line and in `tutorial.js`.

## How it works

- `start(hero)` remembers the profile hero, map and bot settings, starts a normal match on Wet Market, removes the bots and adds two dummies (one enemy target, one ally).
- Its own `requestAnimationFrame` loop checks the tasks of the current step each frame. It pins the match timer, keeps table A neutral until the capture step and puts respawned dummies back on their spot.
- Leaving by any route (finish, Quit to menu, Restart) restores the profile and the `onDamage` callback.
- No balance numbers, hitboxes or hero kits are touched. The tutorial does grant ult charge in the ult step and sets HP to 35 percent in the pickup step.

## Test

`play/tools/tutorial_test.mjs` drives headless Chrome with real key and mouse events over CDP. It needs a CDP driver that loads `chope_tut.html` (or `chope.html` once the hook lands). `play/tools/cdp.mjs` loads `chope.html`.

```
MODE=play node play/tools/cdp.mjs $PWD/play/tools/tutorial_test.mjs q   # play every step for real, then check the finish screen and restored profile
MODE=skip node play/tools/cdp.mjs $PWD/play/tools/tutorial_test.mjs q   # every hero: skip every step. Then pause, Restart, Quit, and a normal match
```

Other env: `HERO=engineer` picks the hero for the play run. `SHOTS=/some/dir` saves JPEGs of key steps. The last line is `TUTORIAL TEST: all passed` or a failure count. Any console error other than the known 404 for `assets/logo_lunchliao_preview.png` is a failure.
