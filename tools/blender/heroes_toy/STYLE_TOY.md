# Locked hero style: toy (Nigel, 2026-11-15)

Nigel picked `toy` from the five-style bake-off: "i like toy. thats my final choice".
This replaces STYLE_V2.md and the "Look rules" in SCALE.md. Everything else in SCALE.md stays: bone names, shape keys, clips, heights, facing, file paths.

Reference: tools/blender/styles/toy/ahma_toy.py and shots/styles/toy/*.png.
The other bake-off candidates are in shots/styles/ for comparison only. Do not copy their looks.

## The look
- A designer vinyl collectible. Clean primitives, sweeps and lathes. No sculpt noise, no painted strokes, no AO on skin.
- Big round head (about 40% of height), short round body, stubby legs.
- Eyes: glossy black domes with a white catchlight, coat 1.0. Brows as thick smooth shapes. Pink blush discs on cheeks.
- Materials: flat colours from the `mat()` helper in ahma_toy.py, light SSS on skin, coat on glossy parts, real metal on props.
- Prints: clean texture images, like the samfu floral.
- Same golden-hour lighting and stage as the bake-off (`stage()` in ahma_toy.py).

## Fix these (weak points found in the bake-off, apply to every hero)
1. Neck: a short visible neck or collar transition. The head must not sit straight on the shoulders.
2. Mouth: real geometry, not a decal. A mouth cavity, tongue and one clean upper tooth row, so `mouth_open`, `grin` and `ult` open properly.
3. Hands: chunky but with a thumb and four fingers (fingers can be partly merged). Posed to grip props.
4. No print smear at seams or sleeve edges. Check the UVs where prints wrap.
5. `angry` must read from 10 m away: strong brow drop, a frown, eyes narrowed.

## Contract (from SCALE.md)
- Heights (2026-11-16): ahma 2.16, gym 2.05, tarik 1.80, siao 1.88. Props inside about x +-0.8.
- Faces +Y in Blender. Export glTF Y-up, faces -Z.
- Bones, shape keys (blink, mouth_open, smile, angry, grin, ult) and clips (idle 60, run 24, attack 18, ult 2, 30 fps) exactly as SCALE.md.
- About 25k tris. 30k is the hard ceiling.
- Rig, weights, anims and export: reuse make_armature, the weights, rest_mat, the anim and export code from tools/blender/heroes/ahma.py and hero_lib.py. Copy into your own file if you need changes.
