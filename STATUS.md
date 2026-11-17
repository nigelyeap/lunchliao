# Status

## 2026-11-13: project created
- The project is set up with three 0.180.0, vite 6.3.5 and esbuild 0.24.0, installed locally with exact versions.
- ref/ holds chope.html, the changelog, hitbox and hero notes, and the current Ah Ma, Gym, Tarik and Siao glbs for scale. All read only.
- public/sfx is copied from chope-src.
- Current gate: 1 (style frames). Ah Ma, plus one hawker stall corner.

Each agent appends one short section here when it finishes: what it built, where the files are, and what is still open.

## Prop and texture builder (Gate 1)
- Textures: `node tools/forge/forge.mjs` writes 8 sets (floor_tile, wall_tile, steel_brushed, formica, concrete_painted, plywood, plastic_blue, plastic_red) to assets/tex/ as `<name>_basecolor|orm|normal.png`, 1024 px, tileable. ORM = R occlusion, G roughness, B metal. Normals are +Y (glTF).
- Props: one script each in tools/blender/props/ (`blender -b -P <name>.py`, shared `_common.py`). Glb in assets/props/, manifest in assets/props/manifest.json. Front faces glTF +Z, floor origin unless noted. Meshes are merged per material. Box-projected UVs, scale per texture set in `_common.py` TEXSLOTS table.
- Hanging props (ceiling_fan, fluorescent_tube) have the origin at the ceiling attach point. FAN_rotor pivot is the hub, spin about its local Y. TUBE_emit is the glowing tube. stockpot_wok has empties STEAM_pot and STEAM_wok. Glass materials are alphaMode BLEND.
- Sheets: `blender -b -P tools/blender/props/_sheet.py -- props|tex` renders shots/props/sheet.png and tex.png.

| file | tris | texture slots |
|---|---|---|
| bin.glb | 1162 | steel_brushed |
| bowls_plates.glb | 3632 | - |
| ceiling_fan.glb | 1024 | plywood, steel_brushed |
| chope_tissue.glb | 288 | - |
| fluorescent_tube.glb | 536 | steel_brushed |
| hawker_table.glb | 2988 | formica, plastic_red, steel_brushed |
| stall_front.glb | 2926 | steel_brushed, wall_tile |
| stockpot_wok.glb | 3604 | steel_brushed |
| stool_plastic_blue.glb | 1056 | plastic_blue |
| stool_plastic_red.glb | 1056 | plastic_red |
| teh_tarik.glb | 1912 | steel_brushed |
| tray_return_rack.glb | 1434 | plastic_blue, plastic_red, steel_brushed |
- Sign quads: SIGN_main, SIGN_menu_1..3, SIGN_grade (stall_front), SIGN_tray (tray_return_rack), SIGN_bin (bin). UV 0..1, plain cream material for the sign builder to replace.
- Open: glb files embed their PNGs (0.1 to 1.8 MB each), so the renderer may want to share textures by name. Textures are hand-tuned procedural, not yet seen in the real engine.

## 2026-11-13: sign builder
- Fonts (OFL, Noto only) are in assets/fonts with SOURCES.md and licence texts. About 29.8 MB total.
- tools/signs/: signs.mjs (definitions), bake.mjs (headless Chrome on port 9404, own profile, `node tools/signs/bake.mjs [name]`), check.py (glyph coverage, passes), sheet.py (contact sheet), WORDING.md (every CJK/Malay/Tamil line with gloss and confidence).
- assets/signs/: sign_main, sign_menu_1..3, sign_grade, sign_tray, sign_nosmoke, sign_table_01..06, sign_drinks. sign_main_n.png and sign_drinks_n.png are emissive maps (lit panels only, wear removed). No normal maps made.
- Sheet: shots/signs/sheet.png.
- Open: Tamil tray line needs a native check. Prices not surveyed.

## 2026-11-13: renderer and Gate 1 style frames
- src/render/renderer.js: WebGL2 three 0.180.0. Physical low warm sun (0xffc38a, dir -0.82,0.22,-0.34), Sky through PMREM as environment, tight-fit PCFSoft shadows (VSM on ultra), own HalfFloat scene pass with a float depth texture, then composer: GTAO (OUTPUT.Off, screen-space px radius), FogAO (humid height fog + AO composite + light shafts), UnrealBloom, Grade (AgX, warm code LUT, vignette, sRGB), FXAA or SMAA. Presets default/high/ultra differ in shadow size, AO scale/samples/denoise, bloom scale, AA, render scale, shaft and steam counts. `?p.<key>=<value>` overrides any preset field.
- src/render/materials.js: hand-painted PBR library by mesh/material name (`applyByName`), with an onBeforeCompile injection for gradient, 3-octave mottle, curvature edge wear and a sun-facing rim. Signs get flipY=false and the `_n` emissive map. The hero glb keeps its authored PBR and only gets the rim.
- src/scene/styleframe.js: stall corner with real props, textures, signs and assets/heroes/ahma.glb when present, blockout otherwise. Cameras `stall` and `ahma` are fixed in SHOTS. Steam sprites, tubes, exhaust duct, roof cartons, light shaft strips.
- Run: `npx vite --port 5301` then `/?shot=stall|ahma&preset=default|high|ultra&stats&freeze`. Shots: `node tools/shoot.mjs [shot...] [--preset=a,b] [--seed=1] [--t=7.3] [--bench] [--profile] [--p.key=v] [--out=dir]` (headless Chrome on port 9401, own profile in the scratchpad, kills only its own pid). Output shots/gate1/<shot>_<preset>.png and last_run.json (calls, tris, assets used, ms).
- Frame times, 1920x1080 on the M4 with the desktop busy (min of 3 batches of 60 pipelined frames): default 10.8 / 11.2 ms at scale 0.85 (7.4 ms in a quiet run), high 21.6 / 23.1 ms, ultra 31.6 / 32.8 ms. Default cost split: GTAO 1.3 ms, paint shader 1.3, bloom 0.6, AA 0.5, shadows 0.4. An M1 Air has not been measured, expect roughly 2x.
- Real assets in frame: every glb in assets/props except the stools (hero shot hides them), all five texture sets, all signs, ahma.glb (skinned, idle clip). Still blockout: stall interior back wall and shelf, hall walls, pillars, neighbour stall shutters, ceiling, exhaust duct and cartons.
- Fixed while iterating: mirrored sign text (flipY), grey steam blob over the fascia, invisible shafts, muddy hero from the paint pass, hero overflowing the frame, page-reload race in the bench, ultra GTAO at 54 ms on its own.
- Open: ceiling is a flat plane, right shutter bleaches under the shafts, hero face is on the shadow side so it reads flat at default, tube hotspot on the back tiles, neighbour drinks sign at far left is cropped and ambiguous. No M1 Air numbers yet.

## 2026-11-13: painterly Arcane pass (renderer)
- Look: stepped toon ramp (three soft bands, wrap 0.5, diffuse only, `shared.uToon` 0 to 1) injected into every painted material through `lights_physical_pars_fragment`; bold golden rim; warm sun key against teal hemisphere ambient and a cool shadow tint in the grade; teal haze that only turns gold toward the sun.
- Post (src/render/post.js): generalised Kuwahara `PaintShader` (8 sectors, 49 taps, depth guarded) rendered at `paintScale` into paintRT, composited in FogAO with silhouettes kept crisp, 4-tap colour bleed, canvas weave and diagonal brush grain, thin tinted ink lines from depth steps (silhouettes) and depth bends (creases). Knobs: `paintMix`, `uInk`, `uInkColor`, `uCanvas`, `uBrush`, `uBleed`, `uQ`.
- Scene (src/scene/styleframe.js): ceiling joists and six fans, stall interior (back tiles, green band, menu board, roast bird rail, sauce bottles, bowl stacks, chopping board), painted shutters, teal fill, hemisphere light, warm tube glow, shafts with bristle bands, steam as 20 tumbling painted puff sprites (`T.puffSprite`).
- Default preset moved to plain PCF shadows, half-res paint, radius 3. Profile toggle `kuwahara` in tools/shoot.mjs turns the pass off for A/B.
- Frame times on the M4 with the hero agent busy on the GPU (shots/gate1, min of 3 batches): default 6.8 / 7.9 ms, high 11.4 / 11.7 ms, ultra 18.8 / 19.9 ms (ahma / stall). The 60 fps budget on an M1 Air is not measured on that machine. If it misses, drop `paintScale` to 0.4 or `scale` to 0.75 first.
- Open: Kuwahara at half res leaves blocky patches in sign text at default (high and ultra are clean), far right shutter still washes a little under the shafts, hero face depends on the new ahma.glb.

## 2026-11-13: Ah Ma hero (Gate 1)
- tools/blender/heroes/ahma.py builds, rigs, bakes, animates and exports her headless (`blender -b -P tools/blender/heroes/ahma.py -- build rig bake anim export verify shots exprfinal`, about 8 min). hero_lib.py and render_lib.py are shared helpers. SCALE.md has the ref heights, the target heights for the other three heroes, bone names, shape keys, head sphere centre and the look rules.
- assets/heroes/ahma.glb: 4.2 MB, 24592 tris (head 5064, headgear 5028, eyes 720, body 10980, walker 2800), height 2.127 (old 2.117), faces -Z, Y up. One glTF material per mesh: baseColor 2048 JPEG for head and body with 1024 ORM and normal PNG, 1024 set for headgear and walker, 256 for eyes.
- Rig: root, hips, spine, chest, neck, head, eye.l/r, upperarm/lowerarm/hand/handslot .l/.r, upperleg/lowerleg/foot/toes .l/.r, prop (walker). Morphs on ahma_head: blink, mouth_open, smile, angry, grin, ult. Clips: idle (60 f), run (24), attack (18), ult (2, pose). 30 fps.
- Head and hair redo (Nigel: less lumpy, more Arcane). Head is three ellipsoid masses (cranium, cheek mass, jaw) plus a small chin sphere and one wedge nose, remeshed and smoothed, no sculpted jowls, folds, bags or cheek balls. Age is painted: one smile line per side and soft cheek blush (crow's feet were cut, they read as an X on the temple). Eyes 0.066 radius set back into shallow sockets, painted iris, pupil, lid line, lash stroke and one highlight. Thin wire glasses with flat lenses. Brows are thin clean wedges. Mouth at rest is a thin cut covered by a painted lip shape with a slight smile baked into the basis (0.3 smile). mouth_open and grin show a flat dark cavity box with a teeth hint, both tucked inside the curved cheeks.
- Hair: scalp cap plus 9 designed ellipsoid curl masses (HAIR_CLUMPS, mirrored) joined without remesh so the edges stay crisp. Albedo paints strands (stroke bands plus thin dark strand lines), cream in light, lavender mid, violet shadow band and teal in the deepest shadow, light taken 70 percent from each clump's own normal.
- Skin: warm peach light band, mauve violet shadow band from a designed radial normal only (the real normal streaked the jaw across sliver triangles), fine stroke texture, roughness 0.62. Hair roughness 0.88 so the clumps do not read glossy.
- AO: the ORM red channel is flat white on every material. A baked AO left black patches where the glasses arms and hair occluded the bake, and the paint already carries the shading.
- Shots: shots/heroes/ahma/turnaround.png, expressions.png (and expr_*.png), anim_sheet.png, side_by_side_old_vs_new.png. Flat and textured check shots: look_*.png, tex_*.png, exprtex_*.png.
- Open: the EEVEE check lights throw a hard lit strip on the shadow side of the jaw (rim light between hair and ear), it is not in the albedo. Hands rest near the walker grips without wrapping the fingers. The painted age lines are subtle at game distance. Not yet seen in the real engine.

## 2026-11-13: art director review fixes (renderer)
- Signs: every sign material (styleframe `signMat` and the SIGN_ branch in `applyByName`) is painted with `sign: true`, which writes alpha 0 at the end of the fragment. FogAO reads sceneRT alpha and skips the paint composite where it is below 0.5, so text stays crisp at every preset. No MRT or stencil needed.
- Paint: `paintMix` 1.0 to 0.5 on all three presets. World-space triplanar brush strokes in `paint()` (`ll_strokes`, about 3 strokes per metre, 4:1 long, shared `uStroke` 0.2, per-material `stroke` option, 0 on signs and the hero). Tile grout reads again.
- Lighting: sun 8 to 7, environment 0.22 to 0.15, hemisphere 0.7 to 0.4 with deeper teal and warm bounce, shadow tint toward teal violet, saturation 1.3, fog density 0.012 to 0.004, sun glow 0.6 to 0.15, shaft strength 0.22 to 0.14, tube point light 5 to 1.6 and moved to the lintel. The stall is the one lit focal point.
- Stall interior: stall_front.glb is only 0.9 m deep and its steel side panel hides everything left of local x -0.7, so the props were behind its back wall. The shelf (jars with red lids, sauce bottles), two hanging roast birds, the stockpot with puff steam and the chopping board now sit in the visible 0.4 m band in front of the glb back tiles. Display case birds enlarged. Steam: size 1.1, opacity 0.85, rise 0.2, brightness lifted past AgX mid grey.
- Far right shutter: it is in full sun, so any mid albedo clipped to cream. Shutter base is now a saturated 0x2f4a58 so it stays blue grey when lit. Still the palest surface in frame, see open items.
- Hero hooks (ready, not shot): per-material `toon` (uToonMul) and `rimColor` options. ahma.glb gets toon 0.45, teal rim 0x4fd6dc, rim 1.3, no strokes, eyes and headgear meshes flagged `sign: true` so the paint pass leaves them crisp, smile morph held at 0.25 (idle has no weight tracks).
- Frame times (stall, M4, hero agent busy on the GPU, min of 3 batches): default 2.0 ms, high 6.0 ms, ultra 10.6 ms. Ahma shot held until the coordinator confirms the glb.
- Open items: the far right shutter still reads pale under direct sun (sun angle or a sun-facing darker slat colour would finish it). The back kitchen hatch behind the counter shows the tan backTiles and the steam puffs are large and white in front of it. Shadows on the left shutter went very dark with the sun cut.

## 2026-11-13: stall polish pass (renderer)

- Shadows: fill light 0.5 to 0.8, hemisphere 0.4 to 0.5 with a bluer sky (0x3a6a94), Grade shadow tint lifted to (0.014, 0.024, 0.058). Left shutter and pillar base now read deep teal with visible slats.
- Camera: stall shot moved to pos (2.1, 1.55, -5.4) look (-1.6, 1.3, 1.4). The foreground pillar is a thin left edge, the stall sits near centre.
- Steam: size 0.55, opacity 0.5, spread 0.28, grow 1.3, sprite brightness 1.3. Puffs are broken up and the roast birds show through.
- DRINKS shutter: sun swung to (-0.86, 0.24, -0.2), shutter base 0x22384a roughness 0.9, wear colour 0x44606c. Reads as a dark slatted shutter in sun rather than cream.
- Counter life: tray rack beside the stall at (0.75, 1.3), bowl stack on the counter at (-2.1, 1.9, y 0.95), tissue chope and bowls added to the right-hand table at (-3.6, -2.7). All via the existing slot() places, no new props.
- Shots: shots/gate1/stall_{default,high,ultra}.png (23:33).
- Bench (polluted, Blender from the hero agent at 60 percent CPU plus GPU during the run): default 7.7 ms/frame, high 13.0, ultra 22.2. A repeat default run gave 6.9. The previous clean run was 2.0 / 6.0 / 10.6, and nothing in this pass adds meaningful GPU work, so re-bench once Blender is idle before judging the 60 fps target.
- Ahma shot on hold until the coordinator's go. Hero hooks unchanged.

## 2026-11-13: ahma shot with the head and hair redo (renderer)

- Finding: the glb's baked occlusion (ORM red channel, all five materials) has hard black patches on the cheeks, chin and under the hair, which rendered as grey blotches on her face. Not the toon ramp (toon 0 looked the same) and not the paint pass (paintMix 0 looked the same). Fix in engine: aoMap set to null on every hero material in styleframe.js. The hero designer should rebake or drop the AO so this hack can go.
- Head toon lowered to 0.3 (body, hair bun, walker stay at 0.45). Face lit, rosy, friendly mouth from smile 0.25, glasses crisp, no light and shadow split down the middle.
- Shots: shots/gate1/ahma_{default,high,ultra}.png (23:54) and a stall re-shoot stall_{default,high,ultra}.png (23:55).
- Bench, Blender idle but the machine is noisy (WindowServer at 30 to 50 percent). Back-to-back runs of stall default gave 5.7, 3.3 and 6.5 ms/frame. Ranges over three runs: stall default 3.3 to 6.5, high 10.7 to 10.8, ultra 18.9 to 20.8. ahma default 7.1 to 8.2, high 10.9 to 12.1, ultra 17.4 to 21.0. CPU per frame roughly 7 to 15 ms default, 30 to 34 high, 41 to 47 ultra. The earlier quiet run was 2.0 / 6.0 / 10.6, so re-bench on a quiet machine before judging the M1 Air 60 fps target.
- 2026-11-14 00:05: hero designer rebaked ahma.glb with flat AO. aoMap = null workaround removed, ahma re-shot at all presets (shots/gate1/ahma_*.png). Face clean. Small remaining marks: a dark smudge at the right temple where the glasses arm meets the hair, and a lighter vertical strip down the centre of the neck inside the jaw shadow band.

## The Siaolang (siao), Gate 2 build, 2026-11-14

- Script: tools/blender/heroes/siao.py (stages build look rig expr bake anim export verify shots exprfinal, work dir SIAO_WORK). Generic helpers imported from ahma.py unchanged.
- Output: assets/heroes/siao.glb, 2.9 MB, 24,084 tris (head 5156, headgear 5344, eyes 720, body 12864), height 1.976 (strands add 1.6 cm over the 1.96 dome), faces -Z. All contract bones, morphs blink/mouth_open/smile/angry/grin/ult, clips idle 60f, run 24f, attack 18f, ult 2f.
- Look: bald dome with three thin comb-over strands and crisp side tufts, round black rims with a painted glint strip, heavy brows, open grin with two teeth baked into the Basis, five sweat beads, one short drool strand with a drop. Stained cream singlet with a crisp boolean hem, maroon shorts, red slippers, claw hands. Skin paint: warm light, mauve shadow, painted stubble on the jaw, bags under the eyes, blush. AO flat white in ORM.
- Body language: idle is crouched 22 degrees at the knees with a 17 degree hunch, slow head tilt and a quick sniff twitch. Run leans 24 degrees, arms swept back and wide. Attack is a right haymaker (coil, swing, follow through). Ult is the pounce: legs tucked, arms reaching.
- Gotchas: shape_key_add leaves new keys at value 1.0, so zero them or the bake runs on the fully mixed face. The glTF importer leaves objects in quaternion mode, so set rotation_mode before touching rotation_euler. Old ref siao.glb faces -Y after import (turn it pi for side by side).
- Weak points: brows and hair tufts are plain dark capsules and could use the hair sheen paint more strongly. Glint strips still read as small white sticks. Shorts have no pocket or fly detail. The angry and grin keys are close to each other. Legs are short and hidden by the shorts, so the crouch reads mainly in the hunch rather than the knees.

## Gym Hunk (Gate 2) - 2026-11-14

Built by `tools/blender/heroes/gym.py` (same stage pipeline as ahma.py, shares its MB node builder, bake and pose helpers by import).
Command (about 6 min): `GYM_WORK=<scratch>/gym_work blender -b -P tools/blender/heroes/gym.py -- build rig bake anim export verify shots exprfinal`

- glb: `assets/heroes/gym.glb` (2.8 MB). 24918 tris. Height 1.810. X extent -0.76..0.77. Faces -Z glTF, Y up.
- Meshes: gym_head 5104 (2048 baseColor), gym_body 16536 (2048), gym_headgear 1598 (1024), gym_ball 960 (1024, the medicine ball, rigid to handslot.r), gym_eyes 720 (256).
- Bones, morphs (blink, mouth_open, smile, angry, grin, ult) and clips (idle 60f, run 24f, attack 18f, ult 2f, 30 fps) as SCALE.md. `prop` bone exists at the back with no mesh.
- Look: chunky local gym bro. Short boxy crop with painted fade, thick straight brows, square jaw with light painted stubble, bull neck, huge delts and arms on short legs, black tank with violet chest bar and side flash, black shorts, chunky trainers, violet wrist straps, protein shaker on the hip, 20KG rubber med ball cupped in the right hand. AO flat white everywhere.
- Shots: `shots/heroes/gym/turnaround.png`, `expressions.png`, `anim_sheet.png`, `side_by_side_old_vs_new.png`.
- Known weak points: socket rim shows a faint dark line under the eyes; hair strands read mostly as flat colour; ult pose is a plain double biceps and the left hand is open; shoe and shorts paint is simple.

### Siaolang review pass 2 (2026-11-14)
Fixed: back of skull plain (lid/lip paint masked to the front), hair as flat swept clumps with grey-black strands and a warm sheen (brows share it), three small temple beads, one curved drool strand, painted soft lens glints (boxes removed), warm rounded teeth seated in the lip and excluded from mouth morphs, jowl plus thicker neck so the jaw blends into the neck, softer shoulder shade. Height 1.960, 24,084 tris.

### Ah Ma Singaporean redo + cane behind (2026-11-14)
Nigel: "doesn't look very chinese or singaporean, and the cane should be behind her."
- Face: rounder and broader, lower nose bridge with a small round tip, fuller cheeks, almond eyes with a single lid line and a low soft crease, small dark brown iris with a painted highlight, warm light tan skin (no pink-white).
- Hair: tight short black perm (250 small curls, seg 8, decimated to 2900) over a grey scalp cap that shows between the curls, grey at the temples, a few grey strands. Violet and teal shadow bands kept.
- Clothes: samfu blouse with a mandarin stand collar (cream band, violet piping along the top edge, shows at the sides and nape), three violet frog knots ray-cast onto the cloth, small floral print on cream, jade bangle on the left wrist, gold ear studs.
- Cane: out of the walker basket. Slung diagonally across her back, crook over the left shoulder, tip at the right hip. Rigid to `chest`. Checked from behind at 4 frames of idle, run, attack and ult: no clipping.
- Engine marks: neck seam gone (neck has its own cylinder radial), temple smudge gone (lid/lash strokes masked to the front with a 3D near-eye blob, lash wing shortened).
- Walker rubber feet sat 3 cm below the floor; raised so the bottom is at z 0. Height 2.127 again.
- Verify: 24,288 tris (head 5064, headgear 4712, eyes 720, body 11592, walker 2200), height 2.127, bones and morphs unchanged, clips attack/idle/run/ult. glb 4.5 MB.
- Shots: `shots/heroes/ahma/turnaround.png`, `expressions.png`, `anim_sheet.png`.
- Known weak points: curls are faceted up close (tri budget), collar is hidden under the chin from the front, the run clip's raised leg pokes through the blouse hem (pre-existing, not the cane).
Pass 3: nape is one thin band hugging the skull with tapered ends, the lower lip drops as one block with the slit interior painted mouth-dark (no lip smear on the chin), teeth enlarged and seated so they read in grin and ult. 25,932 tris, height 1.960.

### Ah Ma perm and mouth fixes (2026-11-14)
- Perm rebuilt: 64 big curl clumps (r 0.10 to 0.12) plus the scalp cap in one Soup, voxel remeshed into a single smooth shell so the clumps touch and no scalp shows. Painted voronoi curl seams and a warm sheen ring on top, black base, grey temples and streaks kept.
- Grin: smile corner and cheek domes widened and smoothed, lower lip tucked back, grin mouth_open 0.35 to 0.1. Shape-key deltas get a 3-pass edge relax so the coarse head triangulation never shows as lumps.
- Ult: mouth_open lower ramp tightened so the lip paint rides down with the jaw. The dark interior stays inside the opening, chin stays skin.
- Tri room: arms 1500 to 1300 each, walker 2200 to 1800. Export 23526 tris, 4161 KB, height 2.128 (1 mm over from the voxel remesh of the top curl), bones, morphs and clips unchanged.

### Gym Hunk, review pass (2026-11-14, later)
Addressed the coordinator review in tools/blender/heroes/gym.py and re-ran rig, bake, anim, export, verify, shots, exprfinal, jpeg.
- Face: head is now cranium, cheek planes, one wide two-lobe jaw, chin and wedge nose, smoothed harder. Lid ring, lash, sock and dotted stubble paint removed. Stubble is one soft tone. Lips painted with a smirk. Smile and grin keys move the mouth corners only.
- Hair: black crop with three flat swept wedges on top, painted skin fade at the sides and back, warm brown-black strands, no blue.
- Ball reads 20KG from the front.
- Torso: squared pec shelf, narrower waist, trap wedges on the core, painted fold and pec highlight on the tank, bolder violet bar and thin hem trim.
- Left hand is a loose fist, so idle reads relaxed and the ult flex reads as a fist.
- Sandbag: the old in-browser kit had one on `prop`, so a 500-tri canvas block with painted straps is rigid to `prop` (gym_prop, 512 atlas).
Result: 25172 tris, height 1.810, X -0.761..0.770. Same shot paths as before. Old ref in the side-by-side has no face, so it reads as a back view either way.

### Gym Hunk, round 3 (2026-11-14, later still)
Hair near-black (#1A1614) with a warm brown highlight and a cool violet shadow, no teal. Skin stroke texture removed (it read as scratches), chin merged into the jaw mass, smirk ticks shortened. Mouth cavity kept still under the jaw keys and made taller, teeth box lowered a touch, so ult is a wide dark shout with a hint of teeth. Ball close-up confirms 20KG reads left to right. The jpeg stage now forces the image buffer to load before saving (previews were stale before) and takes GYM_TAG for a version suffix. 25172 tris, height 1.810.

### Teh Tarik Auntie, round 2 (2026-11-14)
Face notes folded in: smile lines, eye socket shade, lashes and the under-chin blob removed, lid ring lightened. The dark patch below the nose was the skin shader switching to the mirrored arm radial at the jaw, so the head radial now runs down through the neck. The chin triangle was the mouth cavity box poking through the shrunken chin, so cavity and teeth moved back. Lip line now curves up (soft idle smile), grin opens with teeth, angry turns down, ult is a wide shout. Hair rebuilt as 7 large smooth clumps (seg 12, no decimation) over a tucked scalp cap, grey crown tint dropped, a few thin grey streaks only.
Result: 22758 tris (head 5344, hair 1728), height 1.881, X -0.694..0.694, Y -0.475..0.578. Head bone (0, 0.01, 1.14), HEAD_C z 1.42. spout_jug on handslot.r, spout_mug on handslot.l. Shots in shots/heroes/tarik/. Weak points: apron is a stiff single-sided cone, bib strap hidden under the collar, faint stroke marks still on the cheeks, hair crown is one big dome.

### Teh Tarik Auntie, round 3 (2026-11-14, later)
Back of the head showed lips and a mouth line because ring, seg and the lip ellipse are flat in xz, so all face paint is now masked to y > 0.04 and a nape clump covers the neck. The mouth boolean left a dent, so the lower face dropped under a skin band and ult never opened: the cutter faces are deleted so the mouth is a hole, the hinge sits at the lip line, the cavity is wider and taller and the teeth hang below the upper lip. Head decimate is symmetric on X (midline chin crease). Skin strokes, nose shade blob and the heavier lid ring are gone. Hair shells at seg 24 (crown) and 16, bands follow the designed normal at 0.75, roughness 0.94. Apron rim verts snap to the hem, bib and shoulder lines. Stray mouth-rim verts are weighted to the head bone.
Result: 24177 tris (head 5091, hair 3400, body 12962), height 1.881, X -0.694..0.694. JPEG previews are made with sips from the PNGs on disk, no Blender image buffer involved.

## Gym Hunk round 4 (lower face only)
- Lower head: 5 Laplacian passes on verts below the cheekbones (mouth zone excluded), then the head is mirrored across X so the keys pull both corners the same way. Square jaw kept.
- Mouth keys: jaw drop gated by vertex normal (decimation had merged the slot edges, which kept the shout small), smile lifts the lip band on a parabola (no centre kink), new upper-lip lift key. grin = smile + lip lift + small open (teeth sliver), ult = full open + lip lift. Cavity split into two stepped blocks so it stays inside the chin.
- Hair, ball, body untouched. gym.glb re-exported: 25490 tris, height 1.810, |x| <= 0.770.
Apron addendum: the stepped bib kept a ledge and torn corners, so the apron now has one straight hem at the chest (z 0.95) with the straps starting at the hem. Snapping the rim made zero-area faces that broke the bone heat solve (every body vert unweighted, the body rode on the arm bones), fixed with dissolve_degenerate after the snap. Final: 24177 tris, height 1.881, 0 unweighted verts.

## Teh Tarik Auntie, round 4
- Apron, straps, bow and pen are weighted to hips, spine and chest only (arm, hand, handslot and prop groups removed, normalised), and skipped by the sleeve blend. Attack and ult rows: the apron stays on the torso, nothing covers her face.
- Midline split was the mirrored arm radial (SIGN(x) centre) blending into the chin and neck. The arm centre now ramps from the body axis to the arm axis over |x| 0.15..0.40, and the head radial owns everything above z 1.02. The front face is one soft warm-to-cool gradient.
- Squint, smile and frown deltas are relaxed over the mesh (3 neighbour-average passes) so the cheeks move as a plane. Some lower-lid faceting is still visible in grin and ult.
- Crown hair: grey streak paint was a hard noise contour (read as a plastic highlight). Softened to step 0.66..0.80 at 0.22, hair roughness 0.98.
- 24177 tris, height 1.881, 0 unweighted verts. Previews from the PNGs on disk via sips.
