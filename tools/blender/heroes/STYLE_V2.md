# Hero style v2: Pixar / Fortnite (Nigel, 2026-11-15)

Nigel rejected the Gate 2 heroes: "looks way too unnatural. can we stick to the cartoon plan, but just with much higher quality and detail?" He picked Pixar / Fortnite style over the old toy look and over cel shading.
This replaces the Arcane painted-skin rules in SCALE.md "Look rules" and GATE2_BRIEF.md. Everything else in the contract stays (bones, morphs, clips, heights, facing, about 25k tris, file paths).

## What went wrong
- Painted light bands, brush strokes and wrinkle marks on low-poly skin read as dirt, seams and scars.
- Small sunken eyes and thin lips on big heads look uncanny. Faces were lumpy or flat, not appealing.
- Clothes were shells with ragged edges. Props floated.

## The target look
- Appeal first. Clean, smooth, rounded forms with clear big shapes. Think Pixar's Up or Coco, or Fortnite skins.
- Head: big and rounded, soft cheeks, small simple nose, a clear chin. Age shows in the shape (soft jowls as one smooth form, a few large smooth smile lines as geometry), never in painted lines.
- Eyes: large, real geometry. White eyeball sphere, iris and pupil as a slightly domed disc, a glossy clearcoat so it catches a highlight, eyelids as real lids that close for blink. Eyebrows as thick smooth shapes.
- Mouth: real lip shapes with a mouth cavity, tongue and a single clean tooth row (upper visible in grin and ult). Grin and ult must read from 10 m away.
- Skin: one flat base colour per hero with soft subsurface (Subsurface Weight about 0.15, warm radius), roughness about 0.5, a gentle hue shift toward red on cheeks, nose and ears (painted as soft blurry blobs only). No strokes, no light bands baked into albedo, no AO on skin.
- Hair: big sculpted clumps that merge into one silhouette, smooth surfaces, a soft colour gradient root to tip, roughness 0.4 to 0.5 for a soft sheen. No noise contours.
- Cloth: thick, soft volumes with a few big rounded folds, real thickness (solidify), clean rounded hems. Simple prints are fine as clean texture (a samfu floral, a tank top logo).
- Hands: four fingers plus thumb, chunky and rounded, posed to actually grip their props.
- Props: clean bevelled hard-surface, metal with real metallic and smooth reflections.
- Use subdivision at build time and then decimate or retopo to budget, with smooth shading and weighted normals so silhouettes stay round. Bake a normal map from the high-res to keep the smoothness if needed.
- Keep the Singaporean read from the old brief: real hawker-centre people, caricature body and attitude, never ethnicity.

## Review shots (same as before)
turnaround.png, expressions.png (idle, angry, grin, ult), anim_sheet.png, side_by_side_old_vs_new.png in shots/heroes/<key>/. Plus a close beauty shot, beauty.png, at three-quarter, golden-hour key light and a cool rim. Check your own JPEGs made with sips from the PNGs on disk.
Ask of every shot: would this pass as a still from a Pixar short or a Fortnite skin preview? Iterate until yes.
