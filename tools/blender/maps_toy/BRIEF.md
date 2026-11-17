# Toy map rebuild brief (Nigel, 2026-11-16)

Nigel picked the toy look for the heroes and asked to "redo all the maps following this style". There are five maps. Each agent rebuilds one map in the toy style. Gameplay layout stays exactly as it is in the current game.

The toy look overrides the painterly and Arcane rules in VISION.md. Everything else in VISION.md still holds: the Singapore setting, four-language signs, the hard limits and the banned outcomes.

## Read first
- VISION.md (setting, hard limits, banned outcomes)
- tools/blender/heroes_toy/STYLE_TOY.md and tools/blender/styles/toy/ahma_toy.py (the `mat()` helper and `stage()` lighting)
- shots/heroes_toy/lineup_new_34.png (the heroes that will stand in your map)
- Your map's files in tools/blender/maps_toy/layouts/:
  - `<id>.json`: the raw map from ref/chope.html (MAPS2, the current maps). Half of it is mirrored.
  - `<id>_expanded.json`: after expandMap (mirror and repeats applied). This is what you build from.
  - `<id>_solids.json`: the gameplay colliders from mapSolids, as [minx,miny,minz,maxx,maxy,maxz,flags] in game units (metres, y up).
- ref/chope.html around line 1678 (expandMap, mapSolids, the box flags) and the ENV builder after it (how the old game dressed each box and prop). Read only.

## The look: a toy playset
- The map is a designer vinyl playset that the toy heroes live in. Chunky, clean, bevelled primitives with rounded edges. Flat colours from `mat()`, soft gloss, a light coat on plastic parts, real metal on steel.
- Clean prints and signs as textures. No grime, no noise, no painted strokes, no AO baked into albedo.
- Still clearly Singaporean and specific to the place: HDB pastel palettes, green or blue tiles, terrazzo, tray-return racks, NEA grade stickers, ceiling fans, kopitiam stools and tables, plants in pots, etc. Use the old map's colours from the `look` block as the starting palette.
- Golden-hour light as in `stage()`, with the sun direction from the map's `look.sun`.
- Readability first. Cover must read as cover. Heroes must pop against the floor and walls. Keep large surfaces calmer and less saturated than the heroes.
- Signs use all four languages. Copy every Chinese, Malay and Tamil line from the map JSON `signs` block or tools/signs/WORDING.md. Never invent non-English text. Fonts are in assets/fonts (Noto). Existing sign PNGs in assets/signs can be reused.

## Gameplay must not change
- Coordinates: game x is Blender X, game z is Blender -Y, game y is Blender Z. The glb export is Y-up, so it lands back in game coordinates.
- Every collider in `<id>_solids.json` must have visual geometry with the same footprint and height, within 5 cm. Nothing solid-looking may stand where there is no collider in a walkable area (low floor decals, thin rails above head height and roof parts the colliders allow are fine).
- Respect the flags: `v` and `g` boxes are visual only, `r` is a roof, `i` is an invisible wall (do not dress it as a wall unless the old game did), stairs and ramps keep their rise.
- Do not change hitboxes, sizes, spawns, zones or lanes. If the toy look seems to need a layout change, list it in your report. That is Nigel's call.

## Budget (defaults, report what you used)
- About 300k tris for the whole map, 400k hard ceiling. Merge by material, aim under 120 materials and draw calls.
- Textures: atlas where you can, 2048 px max per texture.
- Doors, fans, steam and other moving bits as separate named objects (FAN_*, STEAM_*), so the engine can animate them.

## Deliverables (your files only)
- tools/blender/maps_toy/<id>.py, plus any helpers named tools/blender/maps_toy/<id>_*.py. Runs headless: `/opt/homebrew/bin/blender -b -P tools/blender/maps_toy/<id>.py`.
- assets/maps/<id>.glb (visual only) and assets/maps/<id>_tex/ if you need loose textures.
- shots/maps_toy/<id>/:
  - overview.png: high three-quarter aerial of the whole map.
  - topdown_check.png: orthographic top view with every collider outlined in red over the map. Use it to prove the layout matches.
  - ground_a.png and ground_b.png: eye height 1.6 m down two main lanes, with two or three toy heroes from assets/heroes/*.glb standing in for scale. Other agents are rebuilding gym and siao right now, so import whatever glb is there.
  - detail.png: a close shot of the best corner (a stall, a stairwell, a desk row).
- Make your own JPEGs with sips from the PNGs on disk and look at every one: `sips -s format jpeg -s formatOptions 75 -Z 1600 in.png --out <scratchpad>/<id>_x.jpg`. Never judge from a Blender image buffer.

## Quality bar
Would a Singaporean who eats there every day recognise the place, and does it look like the same toy line as the heroes? Iterate until yes. Clean and simple beats busy with artefacts (z-fighting, floating props, stretched textures, garbled text).

## Rules
- Write only your own files listed above. Everything else is read only, including ref/, the layouts folder, assets/heroes and other maps.
- Up to seven Blender processes may be running on this machine at once. Keep renders at 1600 px, EEVEE, modest samples.
- Use the session scratchpad for temp files: /tmp/lunchliao-scratch
- Never publish, push, upload or download anything. No new installs.
- Report in under 200 words: tris, materials, the five shot paths, whether the collider check passes, any layout changes you would suggest, and your honest weakest points.

## Update 2 (Nigel, 2026-11-16): go real, go nostalgic, go detailed
Nigel: "dont be afraid to improve the map design to make it look more like an actual in-singapore area. take more research, of places singaporeans will find nostalgic, and make the necessary changes."
This is the go-ahead to detail. Before more modelling:
- Research your place with WebSearch and WebFetch (reading only, no downloads, no images saved). Pick one or two real, well-loved Singapore spots as the model, for example Old Airport Road or Tiong Bahru hawker centres, 1970s-80s HDB void decks (Dragon playground, mosaic, kopitiam stools, letter boxes, Ah Gong chess tables), Tekka or Geylang Serai wet markets, rooftop HDB carparks with coupon signs, and older government school blocks (green louvre windows, canteen, assembly area). Write 5 to 10 concrete details you will copy into tools/blender/maps_toy/<id>_REF.md, each with its source URL.
- Free to redesign everything that is not a collider: building facades, rooflines, colours, signage, set dressing, skyline, ground textures, lighting, landmarks outside the play area. Make the facades read as a specific real era and place, not generic window grids.
- Colliders and layout stay as the game has them. If a real-place feature needs a collider change, list it in the report with a sketch of the change. Nigel decides.
- Quality: this is the final pass. Higher bevel and texture detail on what the player sees up close, real HDB facade details (corridor parapets, window frames, block numbers, laundry poles), warm golden-hour light everywhere (no cold grey ceilings), and calm large surfaces so the heroes still pop. Budget stays about 300k tris, 400k ceiling.
- Then do the full deliverable list above, including the collider check.

## Update 3 (Nigel approved, 2026-11-16): new layouts
Nigel approved the layout changes in REDESIGN_PROPOSAL.md ("Approve all five"). This replaces "Gameplay must not change" and "Colliders and layout stay" above for the moves listed there. Nothing else in the layout changes.
- Build from `layouts/<id>_solids_v2.json`, not `<id>_solids.json`. It is the old set minus the removed boxes plus the new ones (flag `s`, all mirrored already). The plan is the scratchpad file td/prop_<id>.jpg (red X = removed, magenta = new).
- The `_expanded.json` props and zones still apply, except where a prop sits inside a removed collider (drop it) or a new one (move it clear and list it).
- Hawker: tables stay where they are for now. The planter ring, island stalls, tray returns, 8 m spawn walls and umbrella tables are in v2.
- Classroom: v2 has only the ground-floor moves (east core gone, east stair box, lockers). You design level 2 to the proposal: slab top at +3.5 over both blocks with the west stair void, parapets copied from level 1 at +3.5, four rooms upstairs with walls, switchback stairs (0.4 m rise per step) in each spawn room and in the old east core, a roofed L2 bridge over x 14.5..24.5, z -6..6 with 1 m parapets, all mirrored in z. Write the full collider set to `layouts/classroom_solids_v3.json` (same format) and build to it. Keep the courtyard open so a fall still kills. Stairs must be climbable with a step of 0.4 m or less.
- Collider check (topdown_check.png) runs against the v2 file (classroom: v3). Your report lists any extra collider you think is needed. Do not add it yourself.
- The game code (ref/chope.html colliders and nav) is updated later by orchestrator B. You do not touch it.
- Previous outputs of stopped agents may exist for your map. Reuse what still fits, rebuild what does not.

## Update 4 (Nigel, 2026-11-16): new look, not the old one
Nigel: "make sure to replicate the design choices of wall colors, signs, colors, etc into the map creation and dont stick to the old one".
- Wall colours, floor colours, signs, trims and props come from your `<id>_REF.md` and your section of REDESIGN_PROPOSAL.md. The old map `look` block is no longer the starting palette. Use it only for the sun direction.
- Do not reuse old sign PNGs or old map textures unless they match the REF. Make new sign textures in the REF style (wording rules above still apply).
- Old outputs from stopped agents: keep geometry that fits, repaint it to the REF palette.
- Report lists the palette you used (hex values) next to the REF line it came from.
- Nigel clarified: "by replicate i mean learn from the actual in real life map". The real place is the reference, not the old game. Before you pick a colour or a sign, look up how the real place looks today (WebSearch and WebFetch, reading only, no downloads): actual wall and pillar paint, floor tiles, ceiling, signboard layout and colours, stall fronts, railings, roof. Copy those choices in toy form. Add what you learn to `<id>_REF.md` with source URLs.
- Nigel again: "not just wall floor sign and trim colors, everything else". Every visual choice follows the real place: materials, shapes and proportions of buildings and fixtures, props and furniture and where they sit, lighting fixtures, plants, skyline, clutter, wear-free versions of real details. If the real place has it and it fits inside the colliders, model it. Only the collider layout and the toy finish stay from the brief.

## Update 5 (Nigel, 2026-11-16): saturate it
Nigel: "the overall look is very white. i need you to saturate it with colours."
- No near-white large surfaces. Walls, pillars, floors, ceilings and roofs get real colour. Pick the boldest version the real place has, such as repainted HDB blocks in strong pastels and bold accent bands, coloured floor tiles, painted beams, and coloured stall fronts and shutters. Where the real place is white, use a warm tinted version and add the colour through bands, dados, signs, awnings, plants and props.
- Target: large surfaces at HSV saturation 0.30 or more and value 0.85 or less. Accents and props 0.55 or more. White and off-white only on trims, lot lines, ceiling lights and small details, under about 15% of any ground shot.
- Check the render chain too. AgX washes out bright surfaces. Lower the exposure or sun strength until no large surface clips toward white, and try the AgX Punchy look. The golden-hour warmth stays.
- Heroes must still pop. Keep floors and walls in hues that differ from the heroes' black and purple and from the floral samfu, and keep them a step calmer than the heroes.
- Update the palette table in the report with the new hex values. Redo all shots and the collider check, and look at the JPEGs.
