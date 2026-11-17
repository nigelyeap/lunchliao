# Engineer Encik, toy build notes

Script: engineer.py (stages: build rig anim export verify shots). Work files in _tmp_engineer/.

## Identity sources
- ref/chope.html, HEROES entry: body colour 0x23395b (navy), kit Foam Dart Ricochet, Folding Table, Kopi Can Turret, Hi-Vis Vest, Claim OT (ult). Voice lines about drawings, road closures, safety and OT claims.
- ref/chope.html buildEngineer and the viewmodel: lime #D4F03C vest with steel reflective bands, white hard hat with a ridge, brown belt and boots, dark kneepads, red-brown toolbox on the left arm, lime dart blaster with white barrel and drum and a green dart tip, steel spanner.
- ~/Documents/chope-src/ART3.md: barrel body, hard hat brim, hi-vis vest, tool belt, toolbox, spanner. Signature is the brim plus the boxy toolbox.
- ~/Documents/chope-src/heroes/engineer.glb (old model, rendered for reference): white hat with ridge, vest with silver bands, moustache, belly, tool belt with pouch and tape, lanyard and ID card, clipboard on the back.
- No web references used.

## Design decisions
- Navy work shirt and trousers carry the main colour. Lime vest with two silver bands, a navy zip line and a deep front V that shows the lanyard and ID card.
- Barrel torso with a soft front belly. Belt with steel buckle, pouch, tape measure and a spanner on the left hip.
- White glossy hard hat with a crest and a small lime badge (no logo). Short dark hair band under the brim. Moustache rides the upper lip and follows each expression.
- Right fist wraps the blaster grip. Left fist hooks the toolbox handle. Clipboard sits on the back on the prop bone.
- Caricature only: no ethnicity cues, no logos, no real-person likeness.
- GS (final uniform scale) is measured in build so the hero is exactly 1.88 tall and stored in _tmp_engineer/gs.json for the later stages.

## Round 2 fixes
- Kneepads are curved rounded-rect plates in navy_dark with a thin navy_dark strap round the knee.
- Hair is a parametric band on the head surface (sides and back, under the hat) with a soft scallop nape line. Roughness raised and clearcoat lowered so it does not read as a visor. Hair colour unchanged.
- Sleeves: 32 segments and a 7-ring shoulder dome built in the sweep points (the helper cap has only 3 rings).
- Ult tear came from the nearest-segment weight lookup pulling outer sleeve and cuff verts onto the forearm when the elbow bent. Sleeve and cuff are now rigid on the upper arm, the arm skin is rigid on its chain (no chest blend) and slimmer at the shoulder so it stays inside the sleeve.
- Attack recoil: spine and chest lean back about 8 degrees at the shot, hand and forearm kick up, longer kick window. Thumb is a separate arc that lies over the index finger.
- Head grid kept at 48x24. 60x30 cost 900 tris and made a visible seam at the face patch edge.

## Round 3 and Malay update
- Nigel asked for the engineer to be Malay. Skin is now #B07650 (warm medium brown), nose #A66C48, blush #B0625A, lip #A85A52. Face shape, moustache, black hair, hat, outfit and props unchanged. No feature exaggeration.
- Back hair band: scalloped edge replaced by a straight nape curve with a rounded lip (rider style).
- Head and face patch get smooth custom normals from the analytic jaw surface, so no facets and no seam. No extra tris.
- Boot capsule and collar pulled in so no brown notches poke through the trouser sides.
