# Style bake-off brief (2026-11-15)

Nigel rejected the Gate 2 heroes as "way too unnatural" and wants "much higher quality and detail" in a cartoon style. He wants to see candidates in several styles and pick one.
Five agents each build Ah Ma in one style. Same subject, same lighting, same cameras, so the only difference is the style.

## Read first
- /Users/nigelyeap/Documents/lunchliao-hd/VISION.md (setting, golden-hour hawker centre, Singaporean audience)
- tools/blender/heroes/STYLE_V2.md (what went wrong last time, and the Pixar/Fortnite notes)
- tools/blender/heroes/ahma.py, hero_lib.py, render_lib.py (the old pipeline: copy what helps, ignore the painted-skin look)
- ref/heroes/ahma.glb and shots/heroes/ahma/*.png (old and Gate 2 Ah Ma, for the character)

## The character: Ah Ma
A Singaporean Chinese grandmother at a hawker centre. Short permed hair (dark grey to black curls, or white curls), round glasses, jade bangle, gold stud earrings, a loose floral samfu blouse, dark slacks, red rubber slippers, an aluminium walking frame (walker) with a red basket in front of her. Chunky caricature: big head, round body, short legs. Height about 2.13 m (game scale) with the walker in front, the cane-like walker never behind her face. Warm, cheeky, feisty. Do it with respect: caricature body and attitude, never ethnicity (no slit eyes, no buck teeth, no skin-colour jokes).

## Scope (style frame only, no rig or animation)
- Build the full body and the walker, posed standing, hands gripping the walker.
- Make four facial expressions as shape keys: neutral smile, angry, big grin, ult shout. They can be quick but must read clearly.
- Budget: aim for about 25-40k tris for the game mesh. Say what you used. High-res with a baked normal map is fine.
- No glb export needed. Save the .blend.

## Shots (all must exist)
Use headless Blender 5.2: /opt/homebrew/bin/blender -b -P your_script.py. EEVEE, AgX, 1600 px wide.
Same lighting for all: golden-hour warm key from front-left about 45 degrees up, cool blue sky fill, a warm rim from back-right, a soft neutral floor. Copy RL.setup_render and studio_light from render_lib.py if they help, then add the rim.
- shots/styles/<id>/hero.png: full body, three-quarter front, camera at chest height.
- shots/styles/<id>/face.png: head and shoulders close-up, three-quarter.
- shots/styles/<id>/expressions.png: four head close-ups in a row (smile, angry, grin, ult), front view.
- shots/styles/<id>/turn.png: front, side, back in a row, full body.
Hero faces +Y in Blender, so the front camera sits at +Y.
Make your own JPEG previews with sips from the PNGs on disk and look at them: sips -s format jpeg -s formatOptions 75 -Z 1600 in.png --out <scratchpad>/<id>_hero.jpg. Never judge from a Blender image buffer.

## Quality bar
Ask of every shot: would this pass as a still from a real game or film in your named style? Is Ah Ma appealing, clearly Singaporean, clearly old, and fun? Iterate until yes. A smaller amount of very clean work beats lots of detail with artefacts (seams, facets, floating props, torn cloth, eyes poking through lids).

## Rules
- Write only tools/blender/styles/<id>/ and shots/styles/<id>/. Everything else is read only.
- One Blender process at a time. Use the session scratchpad for temp files: /tmp/lunchliao-scratch
- Never publish, push, upload or download anything. No new installs.
- Report: your style id, tris, the four shot paths, your honest weakest points, in under 200 words.
