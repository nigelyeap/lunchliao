# voiddeck reference: Toa Payoh Lorong 6 (late 1970s HDB estate)

Research notes. Sources are read-only web pages. Items marked (common knowledge) had no
page that confirmed them in this pass, so treat as soft. No Chinese/Malay/Tamil text is
proposed. Existing sign text in the layout JSON already carries translations, leave it.

## 1. Chosen place and why

Primary: Toa Payoh Lorong 6, the Dragon Playground and the slab blocks around it.
- It is the one site almost every Singaporean of any age recognises. The dragon is a
  heritage-listed icon, and it is the only dragon still standing in a sand pit.
  https://en.wikipedia.org/wiki/Toa_Payoh_Dragon_Playground
  https://www.littledayout.com/dragon-playgrounds-of-singapore-icons-of-childhood/
- It reads in toy/vinyl style: one chunky coloured silhouette, big and readable from far.
- A dragon is a natural low-cover body that is also a landmark for zone B.

Secondary (props only): MacPherson Weave, for twin dragons plus a watermelon dome and
jackfruit pods. Justifies a twin dragon (needed for point symmetry) and fruit domes as cover.
https://thesmartlocal.com/read/old-school-playgrounds/
Tiong Bahru SIT flats: one visual borrow only (curved block corner, green window panes).
https://www.roots.gov.sg/places/places-landing/Places/landmarks/tiong-bahru-heritage-trail/the-architecture-of-tiong-bahru

## 2. Visual details to copy

1. Dragon: winding body, multicoloured steel rings along the back to climb through, slide
   in the head, clad in mosaic tile so it never needs repainting.
   https://en.wikipedia.org/wiki/Toa_Payoh_Dragon_Playground
2. Sand pit under the dragon, roughly 10 x 10 m for the original design. Baby dragons were
   scaled down for estates. https://wiki.sg/p/Dragon_Playground_(Toa_Payoh_Lorong_6)
3. Other mosaic shapes to reuse as cover: watermelon with merry-go-round, jackfruit with two
   domes and leaf canopies, three-pod fruit, clock, sampan with eyes. Baby dragon in pale
   blue and peach. https://thesmartlocal.com/read/old-school-playgrounds/
4. Void deck basics from the 1970s: lifts, letter boxes, bicycle racks, plain cement floor.
   https://roots.gov.sg/-/media//Roots/Images/resources/e-books/nhb_ebook_void_decks
5. 1980s void deck extras: ping pong table, Chinese chess or checker tables with stools and
   benches. Same NHB e-book as above. Concrete chess tables dot older estates:
   https://www.99.co/blog/singapore/uniquely-singaporean-growing-hdb-estate/
6. Tiled chess tables in the middle of the deck, birdcages hung in corners, small mama
   shops tucked under the deck. https://uchify.com/nostalgic-hdb-features/
7. Provision shops were introduced by HDB in the 1970s, peaking near 560 in the 80s and 90s.
   https://borneobulletin.com.bn/859712-2
   Photo of a Chinese provision shop: https://www.roots.gov.sg/Collection-Landing/listing/1212149
8. Terrazzo speckled floors, and older blocks with a rubbish chute per flat. Use speckle
   on the sand-pit border and lift lobby floor. https://uchify.com/nostalgic-hdb-features/
9. Tiong Bahru: curved streamlined corners, concrete sunshade over green-tinted window panes.
   https://www.roots.gov.sg/places/places-landing/Places/landmarks/tiong-bahru-heritage-trail/the-architecture-of-tiong-bahru
10. Pillar paint band: dark lower band about 1.2 m, cream above, so pillars read as chunky
    toys. (common knowledge, no source found)
11. Laundry on bamboo poles slotted out from corridor parapets, bright mixed colours,
    drain grate strips along walkways, notice board by the lift lobby. (common knowledge)
12. Pastel repaint scheme on tall block faces. Layout JSON already uses #f4c7c3 pink,
    #cfe8d8 mint, #f7e3a1 yellow, #e8d1ef lilac, keep them. (matches existing)

## 3. Layout proposal (game coords, x right, z down; every move mirrors via (x,z) -> (-x,-z))

Keep unchanged: both blocks and pillar grids, spawns, zones A and C, the north and south
walls, the zinc linkway strip, fog volumes, stair at (-3.7,-1.5), pickups, all nodes and holds.

Moves (C = changes colliders, V = visual only):
M1 (C, small). B becomes a twin dragon playground. Keep the existing 4.4 square raised
   deck at origin as the shared dragon head platform (collider unchanged, so deckH and the
   stairs still work). Re-skin it as a mosaic dragon head, slide at the stair side, eyes on
   the top face. Add two body humps, each 5.0 x 1.2 x 1.1 m, mosaic coloured:
   hump 1 centred (-6.0, 2.6), hump 2 centred (6.0, -2.6). Rings as V arches only above
   them (y 1.1 to 1.9, not colliders). These break the straight line spawn to spawn.
M2 (V). Sand pit: 14 x 9 m, y 0.03, centred at origin, over the existing 18 x 18 green
   pad. Terrazzo kerb strip 0.3 wide around it. No collider and no slow, so movement and
   bots are untouched.
M3 (C). Two watermelon domes, 2.6 m dia x 1.2 m high, at (-9.0,-13.0) and (9.0, 13.0).
   Fills the 12 m gap between the springs and the north linkway on each side of mid.
M4 (C). Bicycle racks: low rack run 3.0 x 0.6 x 1.0 at (-17.0,-1.0) and (17.0, 1.0),
   beside zone A and C approaches, giving cover at the block mouth.
M5 (V). Mama shop: reuse the shop box at (-29,-1.2). Add striped awning, cardboard drink
   crates, hanging snack strips. Also give the block's pillars the dark-lower, cream-upper
   band. Reuse the 0.9 x 2.6 box at (-13.8,-0.7) as the notice board. Letter box bank
   (V, 0.1 deep) on the lift core walls at (-30,26.5) and its mirror.
M6 (V). Kopitiam corner: round marble tables and red plastic stools (props, not colliders)
   at (-24.5,-6.0), mirrored. Reuse existing blue-striped tent at (-31,-14) as the funeral
   or wedding tent. Add bamboo laundry poles on block corridor parapets at the roofline
   y 4.2 along the street faces.
M7 (V). Tiong Bahru borrow: round the NE corner of each block with a curved sunshade, green
   panes on the upper windows. Skip if costly.

Cover spacing check: mid now has springs, humps, domes and the deck every 6 to 9 m along
x, so no uncovered line longer than about 12 m. Zone A and C keep pillar grids.

## 4. Sketch (not to scale, left half only, right half is the 180 degree rotation)

```
 z-30 |=== zinc linkway =========|
      |        (dome)           |   <- M3 at (-9,-13)
      |  [bike]  tent  (shop)   |
 z 0  |   notice   +--head--+   |   B at origin
      | (spawn)    ~ sand pit ~ |   hump1 at (-6, 2.6)
      |  A[pillar grid]  [bike] |
 z+30 |=== block + lift core ===|
```

## 5. Research notes (reading only) and Update 5 palette

Real place findings:
- Toa Payoh Lorong 6 dragon, built 1979: orange mosaic and terrazzo head, steel-ribbed spine, terrazzo slide, sand pit, blue inside the head, tyre swings and ropes. Sources: https://www.littledayout.com/dragon-playgrounds-of-singapore-icons-of-childhood , https://remembersingapore.org/toa-payoh-dragon-playground , https://www.roots.gov.sg (Toa Payoh Dragon Playground, Mosaic Playgrounds pages), https://en.wikipedia.org/wiki/Toa_Payoh_Dragon_Playground
- MacPherson twin dragons, tiled maze, watermelon dome. Pipit Road baby dragon in blue and peach. Source: https://thesmartlocal.com/read/old-school-playgrounds/
- Void deck fittings: letter boxes, bike racks, vending machines, stone tables, no ball games sign. Sources: NHB void deck e-book, stackedhomes.com, mustsharenews.com
- Soft (no source confirmed): block paint colours, pillar band height, dragon eye shape, block number plate style.

Update 5 palette (saturated, as built):
- Blocks 404 `#d9796b`, 405 `#5fb89a`. Skyline `#d9b23f`, `#a585c8` (REF 12 hues, stronger)
- Bands `#c0453a`, `#1f8a70`, stripe `#f2b632` (REF 10)
- Walls and pillars `#d9bd84`, ceiling `#6fb4d8`, floor tile `#c4906a` (REF 4), terrazzo `#6fb3a3` (REF 8)
- Dragon mosaic `#f08a2c`, `#2f7fc4`, `#f2c230` (REF 1). Baby dragon `#5fb6e0`, `#f29a6b` (REF 3)
- Linkway roof `#3f8fb0`, posts `#e0a92e`, letter boxes `#2f6fb0` with `#f2b632` doors, shutters `#3f78b8`
- Render: AgX Punchy, sun 3.6 warm, sky `#7fbfe6` at 0.8

## 6. Update 6: dragon dropped, neighbourhood park, shop rows, grey palette

The dragon theme is removed (head, spine, mosaics, watermelon dome). Sections 1 to 3 and the dragon notes in section 5 no longer drive the build.

What replaced it, on the same colliders:
- Raised B deck: a modern HDB playground tower. Blue steel posts, grey deck, lime HDPE panels, yellow fascia, red hipped roof, teal steps, blue rubber safety floor.
- Humps: raised concrete planter beds with a clipped hedge. Domes: rubber climbing mounds with holds.
- Striped tent: a park pavilion with a hipped tile roof and concrete tables. Green shelter: a grey steel bicycle shelter. Zinc roof: the covered linkway, now grey.

Park research (read only):
- Toa Payoh Town Park: pavilions, gazebo, shade trees and a looping path. https://roots.gov.sg/places/places-landing/Places/landmarks/Toa-Payoh-Heritage-Trail----Of-Public-Housing-and-Shared-Spaces/Toa-Payoh-Town-Park and https://en.wikipedia.org/wiki/Toa_Payoh_Town_Park
- Ang Mo Kio fitness corners: chest press, pull-up and dip stations. https://www.amktc.org.sg/stay-fit-rain-or-shine
- HDB precinct facilities (pavilions, fitness corners, playgrounds, covered linkways): https://www.hdb.gov.sg/residential/living-in-an-hdb-flat/my-neighbourhood/facilities
- Soft: no source confirmed rain trees or angsana at these exact parks. They are the common Singapore shade trees, used on that basis.

Shop research (read only):
- Provision shops in HDB blocks since the 1970s: https://www.scmp.com/week-asia/lifestyle-culture/article/3363838/singapores-provision-shops-struggle-keep-shutters-open-hdb-heartlands
- Barbers and coffee shops as void deck hangouts: https://www.99.co/singapore/insider/3-ways-can-revive-dying-void-deck-culture/ , https://remembersingapore.org/tag/void-deck , https://en.wikipedia.org/wiki/Void_deck
- Soft: signboard and shutter styling is generic. Shop names are English plus a pictogram only (COFFEE SHOP, MEDICAL HALL, BARBER, BAKERY) because no other wording is on file.

Palette (concrete grey on structure, colour on accents):
- Structure: walls and pillars #c9c4b8, ceiling #ddd6c6, beams #bcb5a6, floor #cfc6b3, paths #bdb7aa, terrazzo base #b9b5aa, steel #8f979c.
- Accents: block bands #b8544a and #2f8a74, stripe #f2b632, shutters #4a7fb0, play blue #2f6fb0, lime #9ac83a, teal #2f9f95, red #d3262b, yellow #f2c230, rubber #3f95b8 and #c8704f, pavilion roof #a85a44.
- Blocks #d6988c (404) and #7fb5a3 (405).

Colliders added for the park and shops live in voiddeck_park.py (west half list, east half is the point mirror).
