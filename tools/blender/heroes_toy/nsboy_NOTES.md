# nsboy (NSF) toy build notes

Script: tools/blender/heroes_toy/nsboy.py. Run with `-- build rig anim export verify shots`.

## Identity sources
- ref/chope.html: NSF, Damage role, body colour 0x5d7a3a.
- Rubber Band Rifle spec: black plank stock, darker front block, red bands with two loops at the front, peg sight. About 0.8 long.
- heroes10 NOTES: No. 4 pixel camo colours, mandarin collar, rolled sleeves, angled chest pockets, blank name tape, webbing belt and bottle, trousers bloused into high black boots, botak cut with ears out, keen grin, beret flopping to his right with a plain gold disc badge over the left eye, team colour rank slip and laces.
- ART3: silhouette is the beret plus the long rifle line, a square backpack and a slim build.
- Old look: ~/Documents/chope-src/heroes/nsboy.glb (renders in _tmp_nsboy/old_*.png).

No web sources were used.

## Choices
- Camo is a packed 512 px texture made in code (tileable noise, four colours, Closest filter). No image files on disk.
- Beret, rank slip and boot laces are magenta (#E0218A) so he pops on green maps. Bands on the rifle are red.
- Badge is a plain gold disc. No crest, no text, no real insignia.
- Rifle is held at port arms across the body. It is weighted to handslot.r. Attack and ult move both arms with a two-bone IK so both hands stay on the rifle.

## Fix round 1
- Rifle rebuilt as a chunky toy rifle held side-on: stock, receiver with carry handle and rear sight, pistol grip with trigger guard, curved magazine, fat handguard, barrel, front sight, two red band loops. No markings.
- Attack and ult yaw the whole body 65 degrees left so the rifle lies across the shot camera.
- Face skin ring welded to the head hole, and the skin gets custom normals from the exact jaw-ellipsoid surface.
- Hair: smooth cosine hairline (rounded nape), thin faded lowest band. Head lowered 0.045 for a shorter neck. Head trimmed from 10.1k to 7.8k tris.
