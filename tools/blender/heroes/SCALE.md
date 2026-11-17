# Hero scale and rig conventions

Measured from ref/heroes/*.glb with tools/blender/heroes/measure_ref.py (glTF units = metres, Y up).

## Reference heights (old models, keep the ratios)

| hero  | old height | old head bone (y) | notes |
|-------|-----------:|------------------:|-------|
| ahma  | 2.117      | 1.241             | widest: x -1.03..1.03 with the walker; head mesh y 1.22..2.07 |
| gym   | 1.774      | 1.241             | shortest |
| tarik | 2.047      | 1.241             | |
| siao  | 1.917      | 1.241             | |

All four old rigs put the head bone at y 1.241. The game does not scale glb heroes by `e.size`, so the glb is shipped at final size.

Target heights (Nigel, 2026-11-16 after the toy line-up: gym larger, tarik and siao slightly smaller): ahma 2.16, gym 2.05, tarik 1.80, siao 1.88. Keep the walker and other props inside about x +-0.8.

Built (2026-11-14): gym 1.810, 25,490 tris, |x| 0.77. siao 1.960, 25,932 tris. tarik 1.881, 24,177 tris (round 4), |x| 0.69. Ah Ma below.

## Ah Ma (new, assets/heroes/ahma.glb)

- Height 2.160 in toy style (2.127 in Gate 2). Feet on y 0, top of the permed hair. Bounds x -0.79..0.77, z -1.15..0.51 (walker in front at -z). Old model 2.117.
- Faces -Z in glTF. In the Blender scripts the hero faces +Y with Z up; the exporter (export_yup) does the conversion.
  The old ref glbs face +Z, so the side-by-side shot turns them 180 degrees.
- Head bone head at Blender (0, 0.01, 1.33) = glTF (0, 1.33, -0.01). Head mesh centre HEAD_C = Blender (0, 0, 1.60).
  For the hitbox head sphere (HDL in ref/chope.html about line 3943): the centre sits 0.27 up the head bone, 0.01 behind it. Radius about 0.42.
- Walker prop bone `prop` at Blender (0, 0.70, 0) = glTF (0, 0, -0.70), parent `root`. The old walker pivot was [0, 0, -0.70] too.
- Tri budget 25k. Current: head 5064, headgear 4752, eyes 720, body 11192, walker 1798 (23526).

## Bone names (humanoid, use these for every hero)

root, hips, spine, chest, neck, head, eye.l, eye.r,
upperarm.l, lowerarm.l, hand.l, handslot.l, upperarm.r, lowerarm.r, hand.r, handslot.r,
upperleg.l, lowerleg.l, foot.l, toes.l, upperleg.r, lowerleg.r, foot.r, toes.r, prop

`handslot.*` is a child of `hand.*` for held items. `prop` is the hero's big prop (walker for Ah Ma).

## Face

Shape keys on the head mesh: blink, mouth_open, smile, angry, grin, ult.
`angry`, `grin` and `ult` are the finished expression mixes. `blink`, `mouth_open` and `smile` are the components for the engine to blend.

## Animations (glTF actions)

idle (60 frames, loop), run (24, loop), attack (18), ult (2, pose). 30 fps.

## Look rules (from VISION.md, 2026-11-13)

Painted albedo: warm light band and cool violet shadow band baked into the base colour from a designed radial normal (see `MB.radial` and `MB.paint_light` in ahma.py), soft brush-stroke bands, no pores, wrinkle maps, grime or AO on faces. Keep AO off the head atlas (it shows triangle patches on low-poly smooth meshes).
