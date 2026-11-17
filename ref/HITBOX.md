# HITBOX (hs1)

Owner: hs1. Patch: `python3 -I tmp/hs1.py chope.html` (8 exact replaces, each asserted once). Test copy: chope-hs1.html.
Damage numbers and hit effects are untouched. hs2 and hs3 own those.

## What was wonky

The old hitboxes were three spheres stacked on e.pos: head at 1.55 x size x k, r .33 x size. Chest at .85, r .56. Legs at .38, r .42.
k is eye/1.55, so crouch and slide only moved the head down. The animation rig moves the head a lot more than that.

Audit: visible head = vertices skinned to the head bone, plus meshes under it. Offsets are in the hero's yaw frame (f = forward, metres).

| stance | visible head vs old sphere | worst cases |
|---|---|---|
| stand | within 0.02 m | gym 1.727 vs 1.705, rascal 1.187 vs 1.163 |
| crouch | f +0.17 to +0.59, y +0.10 to +0.22 above | ahma f .588, uncle .498, tarik y 1.275 vs 1.05, rider 1.241 vs 1.045 |
| run | f up to +0.73 | ahma .73, rascal .57 |
| air | f up to +0.69 | |
| slide | f -0.40 to -0.80 (head behind the body) | tarik -.80, rider -.776, nsboy -.718 |

Size: the visible face is about .43 to .53 x size across, so r .33 was small.
The chin sits about 1.0 to 1.1 x size. The old chest sphere reached 1.41 x size, so the lower face always counted as body.
KayKit heads are big. nsboy standing head mesh spans 1.06 to 2.17 m including hair.

## Fix

- headTick(e) runs once per step after animEnt. It reads the head bone world matrix and stores the face centre offset in e.hdo.
  HDL holds the face centre in head bone space per hero. Hidden or dead meshes (first person player) fall back to the old formula.
- Head sphere: centre on e.hdo, r = .43 x size (1.3x).
- Chest sphere follows half the head lean in x and z. Legs stay on the feet.
- Neck tie rule in rayHit: head wins if the ray reaches the head within one head radius of the body entry and the body entry is above the head sphere bottom.
- Projectiles: old body cylinder plus a head sphere test (r + .08 for projectile size). The head flag comes from the sphere, not the 1.25 x size height line.
- Bot head aim uses headAt(T,c), so bots aim at the real head.
- hitSpheres() still returns the head first, so `hitSpheres(T)[0].r` (hs3) keeps working. It now also gives x and z.
- headAt(e,out) gives the world head centre. hs2 can use it for head FX instead of pos.y+1.55*size*kOf.

## Scripted aim test

tmp/hs1/run.js plus aim.js. 9 heroes x 5 stances, front and side, 150 rays per case, 0.12 m disc error from 6 m.
Head rate for rays aimed at the visible face centre (front and side pooled):

| stance | before | after |
|---|---|---|
| stand | 100% | 100% |
| crouch | 58% (27% miss) | 100% |
| run | 62% (22% miss) | 100% |
| air | 58% (16% miss) | 100% |
| slide | 21% (46% miss) | 97% |

Rays aimed at the visible chin: before 0% head in every stance. After 34 to 47% (slide front 6%, the chin tucks behind the chest).
Rays aimed at the chest: 0% head before and after, so the bigger head does not steal body shots.

## Checks

- Gate on chope-hs1.html: PASS 8 FAIL 0. G6 avg 67.8 max 101. G7 0.1037 ms/step. Shader programs 35.
- node --check on the module: OK.
- wp2c "Rascal head at 1.55*0.75": PASS.
- wpm "crouched head: standing ray misses" now FAILS. The test ray at 1.55 x size goes through the crouched nsboy head mesh (0.66 to 1.81 m), so it is a real head hit now.
  Suggested test change in tests/acceptance.js line 239: use 1.70 x size for the "standing" ray. Checked: crouch 1.70 miss, crouch 1.10 head, stand 1.70 head.
