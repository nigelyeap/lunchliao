# Classroom map reference: Level 5 Classroom Block (two storeys)

Source quality note: web search found little about the exact visual details (no photo captions on louvres, plates, stripes). Items marked (memory) are common Singapore school knowledge, not backed by a fetched page. Verify with Nigel's own photos or recollection before modelling hard.

## 1. Reference type and why

Chosen: a 1980s-90s neighbourhood school with two facing 3-4 storey open-corridor blocks, pre-PRIME, the kind that got extension blocks and link bridges added later. Think a closed or merged secondary school that still looks lived in.

Why: it matches the existing plan. Classrooms face the courtyard through an open corridor, spawn and staff rooms sit at the ends, and PRIME-era add-ons explain the bridge at B.

- MOE school building heritage: standard multi-storey designs from 1947, primary schools often 4-storey, then 12 varied plans in the 1980s. https://moehc.moe.edu.sg/explore/5
- PRIME (1999) upgraded pre-1997 schools by adding extension blocks and altering existing ones. https://en.wikipedia.org/wiki/Programme_for_Rebuilding_and_Improving_Existing_Schools
- Closed-school nostalgia (Upper Thomson Sec closed 1997, main block, assembly hall, lab block). https://remembersingapore.org/upper-thomson-secondary-school/
- Closed-school photo set (Changkat Changi). https://mustsharenews.com/changkat-changi-ex-students/
- Separate blocks linked by covered walkways (1969 Singapore school note). https://hkintexts.histsyn.com/page/1157423
- Open-air circulation facing a shared inner space (Nanyang Primary extension). https://archilovers.com/projects/184751/nanyang-primary-school.html

## 2. Visual details to copy

1. Open corridor with a half-height parapet and a painted rail on top, blue-grey with a pale cap, posts every 1 m. Already in the JSON (#2f6f9f rail). Keep. (memory)
2. Louvre windows high on the classroom wall, blue-green frames, glass slats stacked every 0.25 m. Already built. Keep and make the frame colour match the rail. (memory)
3. Whiteboard writing left on a board in an empty room. Add chalk-style scribble decals (shapes only, no readable text) on 2 boards. https://mustsharenews.com/changkat-changi-ex-students/
4. Office cabinets still labelled, rusted key bunches. Staff room gets grey filing cabinets and a key board prop. https://mustsharenews.com/changkat-changi-ex-students/
5. Shuttered canteen stalls. Put a roll-down shutter set at the B bridge landing end or in the east block so it reads as the canteen edge. https://mustsharenews.com/changkat-changi-ex-students/
6. Desks pushed together for play wrestling. Cluster 4 desks in one room as a pushed-together ring. https://www.timeout.com/singapore/things-to-do/the-ultimate-guide-to-retro-singapore
7. Retro green tiles plus a wall-length blackboard as the visual shorthand for school. Use green board, not black, and a green dado tile strip low on the corridor wall. https://guide.michelin.com/en/article/dining-out/taste-the-past-6-retro-cafes-to-take-you-back-in-time
8. Class plates above doors, e.g. 3E1 style codes (digits and letters only), plus a noticeboard beside each door. Plates are flat coloured boxes with block letters. (memory)
9. Staircase with painted edge stripes and a handrail, one coloured wall panel per landing. Existing spawn-room steps alternate #bdb3a3 and #cbc2b2, add a yellow nosing strip. (memory)
10. Assembly area and canteen below, seen over the parapet. The fall floor at the courtyard gap gets painted court lines (white lines, a flagpole, faint circle) so the drop reads as parade square. (memory)
11. Water cooler, mop and pail, bin in the corridor. Cooler and bin already exist at x -9.5 and x 6.5. Add a pail and mop leaning on the parapet near x -1.5. (memory)
12. Ceiling fans, wooden desks with metal frames and attached chair, class crest and flag above the board. Fans, desks exist. Add a red-white flag and a crest disc on each board wall. (memory)

## 3. Layout proposal (game coordinates, x right, z down, mirrored in z)

Existing: block z -17.9..-6, corridor z -9.6..-6 (3.5 m), rooms x -17.5..14.5 in 8 m bays, spawn room x -24.75..-17.5, east core x 14.5..24.5, bridge/landing B at x 14.5..24.5, z -6..6. Corridor pillars already at x -17.5, -9.5, -1.5, 6.5, 14.5 (8 m).
Level 2 floor top = +3.5. Level 1 ceiling stays 3.2. Slab is 0.3 thick.

Moves, in priority order:

M1. Upper floor slab over both blocks. Z-mirrored.
  - Slab x -24.75..24.75, z -17.9..-6 (and mirror), top at y 3.5. COLLIDER.
  - Open the slab over the corridor at the stair void only (M2). Rest of corridor slab stays so level 1 corridor is covered (the linkway feel). COLLIDER.
  - Level 2 repeats the same 4 rooms, spawn room is empty (storage), corridor, parapet at y 3.5..4.6. Copy parapet boxes with y offset 3.5. COLLIDER for parapet, rooms and walls.
  - Level 2 rooms get roughly half the desks (about 30 per room) so the 140 desk total is only moved, not raised. Visual only.

M2. Stairwells at each end, both ends of both blocks (4 stairs total, 2 per block, mirrored).
  - West: reuse the spawn-room steps (x -24.5..-21.5, z -17.0 side) as a switchback up to +3.5. Cut the slab hole x -24.5..-20.5, z -17.4..-10. COLLIDER (stairs as stepped boxes, 0.4 rise, matches existing).
  - East: put a stair at the corridor east end, x 12..14.5 ... use the east core x 14.5..24.5, z -17.9..-9.6 (currently solid walltile) as the stairwell: steps along x 15..23 at z -15, rising east, landing at +3.5 at x 23.5. COLLIDER, replaces a solid block.
  - Stair cores break the 50 m sightline at both ends and give a vertical route to the bridge.

M3. Bridges between blocks across the kill gap, at both levels. This is the biggest change.
  - Level 1 bridge: the current B landing (x 14.5..24.5, z -6..6, y 0). Keep. Add 4 more parapet posts. No collider change.
  - Level 2 bridge: same footprint at y 3.5, with a 1 m parapet both sides and a 2 m roof panel (covered linkway) at y 6.6..6.9. COLLIDER (floor, parapet, roof). Zone B at (19.5, 0) stays on level 1. Keep B ground, level 2 is the flank route.
  - Optional second link, small: a covered walkway slab at y 3.5 from x -6 to x -2, z -6..6 is NOT proposed. Only one bridge pair keeps the kill gap readable.
  - Open sides toward the courtyard fall floor. Falling from either bridge still kills.

M4. Break the 50 m corridor sightline every 8-12 m.
  - Pillars: widen existing 8 m pillars (0.45 x 0.3) to 0.6 x 0.5 at x -9.5, -1.5, 6.5 on level 1 and level 2. COLLIDER.
  - Water cooler x -9.5, bin x 6.5 exist. Add a stacked-stool / locker bank 1.2 x 0.5 at x -5.5 and x 2.5, hugging the parapet side (z -6.5). COLLIDER.
  - Mop and pail props at x -1.5 are decoration only, no collider.
  - Result: something at x -17.5, -13.5, -9.5, -5.5, -1.5, 2.5, 6.5, 10.5, 14.5 which is every 4-8 m.

M5. Zones.
  - A (2.5, -14.35) and C (2.5, 14.35): stay on level 1 in the third classroom. Open the room's corridor wall door a bit wider (1.4 to 2.0 m) so level 2 can overlook through the stair void at x 2.5 only if wanted. Not needed. No change.
  - B stays on the level 1 bridge. Level 2 bridge is the high-ground flank.

M6. Spawns (-21, -13.25) and (-21, 13.25) stay on level 1 inside the spawn rooms. Door onto the corridor stays. Stairs sit inside the room, so a spawn can climb in 2 s. Add a spawn-protection wall at the west end of the corridor if needed (already walled).

Colliders changed: M1 slabs/walls/parapets level 2, M2 stairs and slab hole and east core, M3 level 2 bridge, M4 pillars and locker banks. Visual only: signs, flags, boards, mops, tiles, plates, crest, court lines.

## 4. ASCII sketches (x right, z down, not to scale, top half only, bottom mirrors)

Level 1 (y 0):
```
z-17.9 +----------+---+---+---+---+----------+
       | spawn    | R1| R2| R3| R4|  EAST    |
       | stair W  |   |   | A |   | CORE     |
z-9.6  +--door-----+---+---+---+---+  stair E |
       corridor  |  |   |   |   |  |  |       |
z-6    =pillars=cooler=lockers=bin=pillars===+
              (kill gap: courtyard, court lines)
z-6..6                               [B bridge L1]
                (mirror below)
```
Level 2 (y +3.5):
```
z-17.9 +----------+---+---+---+---+----------+
       | storage  | R5| R6| R7| R8|  stair E |
       | stair W  |   |   |   |   |  landing |
z-9.6  +--door-----+---+---+---+---+----------+
       corridor, parapet, pillars, lockers
z-6    ====================================+
                                   [B bridge L2, roofed]
               (mirror below)
```
Legend: = parapet, | pillar or wall, A zone, R room.

## 5. Update 4 research: the real place (1980s-90s neighbourhood school block)

Pages read (reading only):
- https://thesmartlocal.com (Upper Thomson Secondary and Old Swiss Cottage Secondary articles): open corridors facing a courtyard, parade square, old furniture left in rooms.
- https://road-less-travelled-by.blogspot.com/2016/03 (Braddell-Westlake Secondary): chalkboards on the front wall, wash basins along the corridor, stairs opening to the courtyard.
- https://www.roots.gov.sg (Old School Daze): blackboard, chalk, duster, wooden desks.
- https://moehc.moe.edu.sg/explore/5 (MOE Heritage Centre): standard-plan school blocks of the period.

The pages say little about colour or fittings. Lines marked (memory) are from common knowledge of these schools, not from a source.

Palette used in classroom.py and classroom_signs.py:
- 5.1 Walls, pillars, beams: cream emulsion `#f2ead6` (memory)
- 5.2 Dado to 1 m: gloss pale green `#a9c4b0` (memory)
- 5.3 Louvre window frames, railings, bins: school green `#1f6b4f`. Glass slats `#bfe0d8` (memory)
- 5.4 Corridor and bridge floor: cement screed `#b9b3a6`. Classroom floor tile `#c9cbbf` (memory)
- 5.5 Stairs and planters: terrazzo `#c2bcae`, yellow nosing `#e9b82c` (memory)
- 5.6 Chalkboard `#2f5b47` in a wood frame `#c9995c` on the front wall (blogspot, roots.gov.sg)
- 5.7 Desks: wood top `#c9995c`, chair `#a8743f`, steel frame `#7f8c95` (roots.gov.sg, memory for colour)
- 5.8 Noticeboard felt `#3f7a55`, paper `#fbf8ee` (memory)
- 5.9 Pitched roof: clay red `#a4553f` (memory)
- 5.10 Courtyard: tarmac `#6a716c`, court lines `#f1eee4`, three flagpoles (thesmartlocal for the parade square, memory for colour)
- 5.11 Signs: class plate cream `#fbf8ee` with green `#1f5a43` text, red `#c8221b` no-running sign, amber `#e3a92b` keep left. English and pictograms only.
- 5.12 Lockers `#8f9ca3`, water cooler stainless `#c9ced2` (memory)

Not built: corridor wash basins (blogspot). They would need a collider.

## 6. Update 5 palette (saturated, replaces the hex values in section 5)

Bold repainted-school version of the same parts. All (memory) unless section 5 names a source.
- 6.1 Walls: cream-yellow `#d9b45a`
- 6.2 Dado to 1 m: deep green `#226b4c`
- 6.3 Pillars and beams: painted blue `#3d7fae`. Slab soffits: sky blue `#8fbcd4`
- 6.4 Corridor and bridge floor: red screed `#b9604a`. Classroom floor: green tile `#6aa884`
- 6.5 Roof: red tile `#c2452d`
- 6.6 Lockers: orange `#d07a34`, doors `#e79a4a`
- 6.7 Noticeboard paper: `#f2c230`, `#e8574a`, `#4aa3df`, `#f08a3c`, `#e86a9a`, `#8fd06a`
- 6.8 Bridge: blue glazed planters `#2f6fa8` with flowers, yellow edge stripes `#e9b82c`, bunting, red fascia `#e8344a`
- 6.9 Court: sports blue `#5a7f9c`. Skyline block body `#e3c594`
- Unchanged: school green `#1f6b4f`, terrazzo stairs `#c2bcae`, signs.
- Render: sun 4.2 (was 6.0), sky 1.1 (was 1.6), AgX Punchy.

## 7. Layout changes, 2026-11-16 (Nigel)
- Corridor cooler and parapet lockers removed. Low locker banks (0.95 m) sit under each louvre window on the corridor side.
- Toilet beside the east stair on both floors. Boys in the north block, girls in the mirrored south block. Blue or pink wall tiles, brown chequer floor, steel cooler outside.
- Bridge planters and floor markings removed. One wooden picnic set at the centre of the level 1 bridge.
- Desks: 2 x 4 units per room, 1.65 m gaps in x and 1.16 m in z. Hero radius is 0.45 (ref/chope.html), so the minimum gap is 1.1 m. classroom_layout3.py asserts it.
