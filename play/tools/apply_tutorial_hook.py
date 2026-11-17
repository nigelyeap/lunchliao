#!/usr/bin/env python3
"""Apply the tutorial hook to a copy of chope.html. usage: apply_tutorial_hook.py SRC DST
Three edits, each must match exactly once or the script stops. See play/TUTORIAL.md."""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
assert 'src="tutorial.js"' not in s, "hook already applied"
EXPOSE = ("window.__tut={THREE,scene,camera,HEROES,HUD,hud,SFX,AU,zones,pickups,keys,profile,BINDS,BND,SL,bindOf,kn,saveProfile,startMatch,applyMap,makeEnt,freeEnt,tbBuild,"
          "gainUlt,applyStatus,ringFx,confetti,portrait:k=>heroPortrait(k),get ents(){return ents},get player(){return player},get state(){return state},get paused(){return paused},"
          "get HAZ(){return HAZ},get map(){return map},get matchT(){return matchT},set matchT(v){matchT=v},get score(){return score},set cdT(v){cdT=v},set RANGE(v){RANGE=!!v},"
          "set comp(v){compOverride=v},get botSkill(){return botSkill},get onDamage(){return onDamage},set onDamage(f){onDamage=f}}; // tutorial.js hook\n")
EDITS = [
    # 1. tutorial dummies reuse the range dummy brain in a normal match
    ("RANGE&&e.team===2?rangeDummy(e,dt):updateBot(e,dt)", "(RANGE&&e.team===2)||e.dummy?rangeDummy(e,dt):updateBot(e,dt)"),
    # 2. one line that hands the module internals to tutorial.js
    ("if(TESTQ)window.__chope={", EXPOSE + "if(TESTQ)window.__chope={"),
]
for old, new in EDITS:
    assert s.count(old) == 1, f"anchor not found exactly once: {old[:60]}"
    s = s.replace(old, new)
# 3. load tutorial.js after the game module
i = s.rindex("</script>") + len("</script>")
s = s[:i] + '\n<script src="tutorial.js" defer></script>' + s[i:]
open(dst, 'w', encoding='utf-8').write(s)
print("hook applied to", dst)
