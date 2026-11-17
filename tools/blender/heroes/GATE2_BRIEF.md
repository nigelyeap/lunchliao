# Gate 2 brief: Gym Hunk, Teh Tarik Auntie, Siaolang

Read first: /Users/nigelyeap/Documents/lunchliao-hd/VISION.md, ARCHITECTURE.md, tools/blender/heroes/SCALE.md and the Ah Ma section of STATUS.md. Then read tools/blender/heroes/ahma.py, hero_lib.py and render_lib.py. Ah Ma is the working example. Copy her pipeline: build, rig, bake, anim, export, verify, shots.

## What Nigel said about Ah Ma (apply to every hero)
- The first version "looks like an eldritch horror". Go less realistic and more oil-painty, "something beautiful". Then: "arcane would be beautiful. try that."
- "make her face less lumpy man, and slightly less realistic and more arcane"
- "she doesnt look very chinese or singaporean or anything". Each hero must read as a real Singaporean at a glance: the face, hair, clothes and props of people you see at a hawker centre. Do it with respect. Caricature the body shape and the attitude, never the ethnicity. No slit eyes, buck teeth or skin-colour jokes.

## Lessons from Ah Ma (do these from the start)
- The head is a few big clean forms (cranium, cheek mass, jaw, chin, wedge nose), smoothed. Never sculpt jowls, bags, folds or wrinkles. Age and detail are painted, with a few strokes at most.
- Painted albedo: a warm light band and a cool violet or teal shadow band from a designed radial normal (`MB.radial`, `MB.paint_light`), fine brush strokes, saturated colour. Use the designed normal only on the head. The real-normal blend streaked on low-poly triangles.
- AO is flat white on every material, with no baked occlusion. It left black patches.
- Hair and cloth are a few designed clumps with crisp edges and painted strands. Don't use a remeshed blob.
- Eyes are painted (iris, pupil, lid line, one highlight), set into shallow sockets. Mouth: a painted lip shape, and the basis carries a slight smile so it never reads as a dark slit.
- Check the expressions sheet and turnaround yourself as JPEGs before calling it done. Ask: does this look like a hand-painted animated film character and a real Singaporean? Iterate until yes.

## Contract (same as Ah Ma)
- Output: assets/heroes/<key>.glb. Target heights from SCALE.md: gym 1.81, tarik 1.88 (shorter, per Nigel), siao 1.96. Keep props inside about x +-0.8.
- Faces -Z in glTF, Y up, 1 unit = 1 m. Bone names, shape keys (blink, mouth_open, smile, angry, grin, ult) and clips (idle 60f loop, run 24f loop, attack 18f, ult 2f pose, 30 fps) exactly as in SCALE.md.
- About 25k tris. Head and body 2048 baseColor, others 1024.
- The kit, silhouette and props follow the current hero in ref/chope.html and ref/HEROES3.md (its build function, blurb and abilities). Keep each hero's look and role. Drop the KayKit look entirely.
- Shots go in shots/heroes/<key>/: turnaround.png, expressions.png, anim_sheet.png, side_by_side_old_vs_new.png (old ref/heroes/<key>.glb next to the new one at the same scale; see shoot_old.py). Write JPEG previews to the scratchpad as <key>_expr.jpg and <key>_turn.jpg.

## Parallel work rules
- Three agents build at the same time. You write only tools/blender/heroes/<key>.py (plus <key>_*.py helpers), assets/heroes/<key>.glb and shots/heroes/<key>/.
- hero_lib.py, render_lib.py, ahma.py and SCALE.md are read only for you. If you need a change in a lib, copy the function into your own file.
- Run one Blender process at a time per agent. Use the session scratchpad for temp files.
- When done, append your section to STATUS.md with one shell append (`cat >> STATUS.md <<'EOF'`). Put your heights and tris in your report, and the orchestrator adds them to SCALE.md.
- Never publish, push, upload or download anything.
