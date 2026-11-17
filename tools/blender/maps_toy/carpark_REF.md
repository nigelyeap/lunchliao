# Carpark reference: Changkat Food Centre Roof Carpark

Research caveat: web search returned thin, listicle-grade sources. Only items with a URL below were
confirmed online. Items marked (general knowledge) are common HDB/SG conventions from memory and
should be eyeballed against a real photo before they go in as "facts". No Chinese/Malay/Tamil text
is proposed. Use English signs only, plus pictograms.

## 1. Chosen place

Primary: a generic HDB multi-storey carpark (MSCP) rooftop sitting on or beside a hawker/food
centre, in the style of People's Park Complex roof carpark (Chinatown) and Chinatown Complex roof.
Why: People's Park Complex has the strongest "rooftop carpark hangout" nostalgia (views, photo
spot, 1973 modernist podium, tall yellow residential block behind). Chinatown Complex is the
hawker-centre-with-roof angle. An HDB MSCP roof gives the lot rows, stair/lift cores, parapet
and ramp vocabulary.
- People's Park carpark on levels 4-6, rooftop is the "hidden gem", yellow 31-storey block as
  backdrop, built 1973 (now closed per captions): https://olafallen.blogspot.com/2021/09/chinatown-complex-carpark.html
- Time Out / TheSmartLocal list Chinatown Complex and People's Park roofs as free viewpoints:
  https://thesmartlocal.com/read/hypebeast-backdrops/amp/ (listing only, page not opened)
- HDB MSCP history and roof uses (gardens, mural, sports ideas):
  https://thesmartlocal.com/read/singapore-hdb-then-vs-now/amp/ and https://hypeandstuff.com/hdb-rooftop-gardens-singapore/ (search snippets only)

## 2. Visual details to copy

1. Coupon era: coupons were colour-coded by value (50c to $4), shaded for date/time/place, left
   on the dashboard, with tear-off tabs. Prop: a small coloured paper coupon on 2-3 car dashboards,
   and a "coupon parking" sign. https://www.tech.gov.sg/technews/history-of-parking/
2. Coupon carparks had no electronic gantry, so the entrance is just a ramp with a plain
   sign and perhaps a kerb, no barrier arm. Same source as 1. Use as: no gate on the ramp.
3. Red season-parking lots: about 30% of MSCPs have designated red-lot decks. Paint 2-3 lots per
   bank with a red outline or red "S" lot marking. https://www.mnd.gov.sg/newsroom/speeches/view/written-answer-by-ministry-of-national-development-on-the-number-of-multi-storey-carparks-(mscps)-in-all-hdb-estates-and-those-with-at-least-one-or-two-decks-of-exclusively-or-a-majority-of-red-season-parking-lots
4. Estate wayfinding by colour and icon (pineapple, fish, tree, sunflower, palm tree) painted
   on stair/lift areas and block sides, with big numbers on solid backgrounds. Put one icon
   (e.g. a sunflower) on each spawn core wall plus a big level number. https://uchify.com/colour-coded-hdb-blocks/
5. Rooftop greening: carpark roofs host allotment gardens and murals. Add a raised planter
   strip with a mural-painted wall as low cover. https://hypeandstuff.com/hdb-rooftop-gardens-singapore/ (snippet), https://www.homeanddecor.com.sg/property/hdb-rooftop-farming (snippet)
6. Roof uses: HDB design material imagines sports facilities on MSCP roofs. A half-court or
   fitness corner is a safe flavour pick. https://www.hdb.gov.sg/about-us/news-and-publications/publications/dwellings/Designing-for-Life (snippet)
7. Hawker-centre-below feel: the roof is the top of a podium with a yellow/ochre residential
   block as backdrop. Skyline cards in ochre/yellow behind the north wall. olafallen link above.
8. (general knowledge) Lot markings: white painted bays about 2.4 x 4.8 m, lot numbers stencilled at
   the bay nose, yellow line at drive-aisle edges, white arrows on aisles.
9. (general knowledge) Red/white or yellow/black painted kerb stripes at ramp mouths and
   column bases, plus low concrete wheel stops per bay.
10. (general knowledge) Stair core: painted level number (big, one colour per estate), steel-pipe handrail,
    louvred lift lobby window, blue/grey metal door.
11. (general knowledge) Parapet: waist-high concrete wall with a steel pipe rail above, tall
    green or grey mesh at the top edge, convex mirror on a pole at the ramp corner.
12. (general knowledge) Ramp: yellow chevrons or "SLOW" in paint, two speed humps with
    yellow/black stripes, a headroom bar sign at the entrance.

## 3. Layout proposal (game coords, x right, z down, point-mirror (x,z) -> (-x,-z))

Principle: turn the random scatter into lot banks (double rows of cars nose-to-nose along x),
separated by 6 m drive aisles, with 2-lot gaps (5 m) every 4 cars as cross lanes. Every move
below lists its mirror. Cars keep current size (about 4.4 long on z, 1.8 wide on x, so rows
step 2.5 m in x).

Existing things to KEEP untouched: spawn rooms at x=+-42, zones A(-22,-9) B(0,0) C(22,9), both
raised decks (x 17..31, z -23..-14 and mirror) with their ramps, perimeter walls.

M1. Aisle spine [colliders: none, paint only]. Paint a yellow dashed centreline plus white
    arrows along z=0 from x=-36 to x=36, and a 6 m wide aisle band z -3..3 kept clear. B stays
    open at origin. Cross aisles at x=-8..-2 and x=2..8 north of z=-5 and south of z=5 are
    open lanes between the lot banks.
M2. Bank NW [colliders: MOVE 4 cars]. Four cars at x=-33.5,-31,-28.5,-26, z=-17 (centre). Row
    runs left to right with 0.7 m gaps. Wheel stops painted at car noses. This sits just north
    of zone A (z=-9), giving 8 m of open aisle between cover and the zone. Mirror bank SE:
    x=33.5,31,28.5,26 at z=17.
M3. Bank NC [colliders: MOVE 4 cars]. Pair of back-to-back rows at x=-14..-6, z=-17 and z=-12.5
    (two cars per row, nose-to-nose gap 0.4 m). Mirror bank SC at x=6..14, z=12.5 and 17.
    Gives centre-north cover 8 m from B and 14 m from A.
M4. Bank around B [colliders: MOVE 3 cars]. Single-row of 3 cars at x=-4,-1.5,1, z=-8.5 (north
    of aisle), mirrored at x=4,1.5,-1, z=8.5. This frames B and gives the 6-10 m cover rhythm
    between M2/M3 and the spawns. Leave 5 m gap at x=-9..-5 and 5..9 as cross lanes.
M5. Spawn-side lots [colliders: MOVE 2 cars]. One car at (-34, 8) and one at (34, -8): these
    sit between the spawn core and the aisle so exits have cover. Replaces the three random cars
    near the spawn rooms in the current layout.
    Car budget for 14: M2 as 3+3 (drop the x=-26 / x=26 car), M3 as 2+2 (outer rows only),
    M4 as 2+2 (x=-4,-1.5 and x=4,1.5), M5 as 1+1. Total 6+4+4+2 = 16, so also drop M3's
    inner row entirely if 14 is a hard cap (then 3+3, 2+2, 2+2 = 14 with M5 removed).
M6. Painted flavour [colliders: none]. White lot lines, lot numbers, red season lots (2 per
    bank), yellow kerb at deck ramp mouths and at stair core doors, speed-hump stripes on both
    ramps, chevrons.
M7. Red/white barrier rails on parapet (visual only). Convex mirror pole at the foot of each
    deck ramp [collider: thin pole, optional].
M8. Planter strip + mural wall [colliders: ADD 2, low 1.0 m]. One at (-10,-26) length 8 m,
    mirror at (10,26). Doubles as cover on the north and south edges where the layout is sparse.
M9. Half-court corner (optional) [colliders: none, decal]. Painted court lines on open floor at
    x=-36..-28, z=20..26 and mirror, with a low rail. Flavour only.

Competitive checks: bank edges are 8-10 m apart in z and about 5 m cross lanes in x, so no sightline
longer than about 12 m is uncovered. The raised decks remain the only high ground.

## 4. ASCII sketch (x -45..45 left to right, z -31..31 top to bottom; not to scale)

```
+-----------------------------------------------------------+
| S1                 [planter]                        deckB |
|                  NN NN        ## ##                 ####  |
|   .  [car][car][car]     [car][car]   A            ####  |
|  /\                          (o)                          |
| [] <-- spawn          - - - -  -  - - - - ->    spawn []  |
|                 [c][c][c]        B                        |
|                        (o)      [c][c][c]                 |
|   ####                        (o) C                       |
|   ####   [car][car]     [car][car][car]       [planter]   |
+-----------------------------------------------------------+
```
(deck top-right and bottom-left are the two raised decks. Lot banks run parallel to the aisle.)

## What is still unverified

No photo-grade source was fetched. Before modelling, check: (a) exact HDB lot sizes and colours,
(b) whether the stair-core level numbers are typically red or blue, (c) signage fonts.

## 5. Real-place research (Update 4) and palette used

Read on 2026-11-15 and 16. Reading only, nothing downloaded. Several pages failed to load (HDB pages 404, Time Out 403), so the list is short.

Confirmed from sources:
- R1. People's Park Complex is a 31 storey slab of flats on a shopping podium. It was raw concrete at first and was later painted green and maroon. The flat block has round portholes near the top and tall roof fins. https://en.wikipedia.org/wiki/People%27s_Park_Complex
- R2. The carpark sits on podium levels 4 to 6 and the roof is the top deck. A visitor calls the backdrop a "31 storey old school yellow building". https://olafallen.blogspot.com/2021/09/chinatown-complex-carpark.html
- R3. The roof deck is about 4,000 sq m, reached by car or by lift then stairs. https://www.edgeprop.sg/property-news/why-investors-may-want-park-42-mil-peoples-park-complex
- R4. Chinatown Complex carpark is Blk 335 on Smith Street, 361 lots. Same blog as R2.
- R5. Lot lines: white for visitor lots, red for season parking, red and white for season at night, yellow for restricted zones. https://www.motorist.sg/article/8/types-of-parking-lots-and-coupons-in-singapore
- R6. HDB carpark roof gardens have planters, benches, trellises and fitness corners. Parapet or railing at least 1.2 m high. https://skyrisegreenery.nparks.gov.sg/explore/showcase-projects-folder/garden-by-the-roof---boon-lay-zone-4/
- R7. Coupon parking: a main signboard lists the scheme and hours, and coupons sit on the dashboard. https://www.tech.gov.sg/technews/history-of-parking/

From general knowledge, not checked against a photo (U): blue P boards, green way-out boards, lot number stencils at the bay mouth, grey bare deck, steel pipe rail on the parapet, cream HDB wall paint.

Palette in carpark.py:

| Use | Hex | From |
|---|---|---|
| Deck floor | #b5b1a8 | U, bare concrete deck |
| Kerbs, concrete | #c2bcb0 | R1, raw concrete |
| Parapets, walls | #e9e1cf | U, HDB cream |
| Wall caps, sign text | #f6f0e0 | U |
| Stair and lift cores | #f1ece0 | U |
| Dado band, tower bands | #5d8f6a | R1, People's Park green |
| Canopy, name board, tower bands | #8c3b3b | R1, People's Park maroon |
| Tower face, loading bay board, level panel | #e2b84e | R2, old school yellow |
| Lot lines, arrows, numbers | #f6f1e4 | R5, white visitor lots |
| Season lot lines, no parking board | #c8221b | R5, red season lots |
| Spine dashes, hatch box, SLOW | #e8bf3f | R5, yellow restricted zone |
| Parking and coupon boards | #1f5fae | R7 for content, colour U |
| Way-out, lift, refuse boards | #2f7d4f | U |
| Hedge and trees | #5aa04a, #3f8a3a | R6, roof planters |
| Soil | #7a5538 | R6 |
| Far block glass | #6f8796 | U |
| Car pastels | #f4c7c3 #cfe8d8 #f7e3a1 #c7b5d9 #9ec9df #f6f0e0 #f2b8a0 #b9d8a8 #ffd9b0 #a6d6be, taxi #8fc3e8 | toy finish (STYLE_TOY), not from the place |

Kept from the old layout because they are colliders: gantry booth and barrier arm. A real coupon carpark has no gantry.

Second pass, 2026-11-16 (search results only, pages not opened):
- R8. HDB roof garden barriers: parapet or railing at least 1.2 m, solid part at least 0.5 m, gaps under 100 mm, nothing easy to climb. Each multi-storey carpark gets two lit block signs and two plain plates. At least two accessible lots. https://www.hdb.gov.sg/cs/infoweb/-/media/doc/BQG/hdb-arch-technical-requirements.pdf
- R9. People's Park carpark runs from level 3 to level 6 with 648 car lots and 56 motorcycle lots. The roof is level 6. This backs the level 6 panel and the scooter row. https://www.edgeprop.sg/property-news/feo%E2%80%99s-lucky-pinnacle-pays-3933-mil-people%E2%80%99s-park-complex-carpark
- No source describes lamp posts, lot number style or deck paint at either place. Those stay unverified. The pipe rail on the parapet is horizontal, which R8 would not allow on a new roof garden. It is kept as an older-carpark detail and is unverified.

Layout fix 2026-11-16: v2 now has 24 cars and 232 boxes. Cars are built straight from the collider file, so the four removed cars are gone and the bank now sits at x -31 to -23.5 (mirror 23.5 to 31).

## 6. Update 5 palette (saturated). This table replaces the one in section 5.

Sun strength cut from 6.5 to 5.4 and sky from 1.7 to 1.2, AgX Punchy kept. Lot lines widened from 10 cm to 16 cm.

| Use | Hex | From |
|---|---|---|
| Deck floor, warm dark concrete | #a68b66 | U |
| Kerbs, platform | #a88a63 | R1, raw concrete, warmed |
| Parapets, pillars, podium, planters | #d98866 | U, repainted HDB terracotta |
| Stair and lift cores | #63a886 | R1, People's Park green, pastel |
| Core dado, podium fascia | #2c7a58 | R1, green |
| Vent shafts, screen walls | #6f9cc4 | U, HDB pastel blue |
| Canopy, name board, tower accents | #9c2f33 | R1, maroon |
| People's Park tower face | #e39a1f | R2, old school yellow, pushed |
| Tower bands | #3f8f63 | R1, green |
| Base bands, loading board, level panel | #e3a224 | R2 |
| Trims and caps only | #f3e3bf, #f0dcae | U, warm white |
| Lot lines, arrows, numbers | #f6f1e4 | R5 |
| Season lines, no parking | #c8221b | R5 |
| Spine, hatch box, SLOW | #f4b31c | R5 |
| Parking boards | #1f5fae | R7 content, colour U |
| Way-out boards | #2f7d4f | U |
| Hedge, trees, grass | #4fa53c, #3f8a3a, #6a9f55 | R6 |
| Far HDB blocks | #e58f7a #6fb39a #e6b455 #7aa6d0 #dd8fa3 | U, repainted HDB pastels |
| Cars | #e8746a #4fb58a #f0b93a #e0709c #3f9bd0 #f1e2bd #ee8a4a #7dbb4e #f29b7a #35b0a6, taxi #2f86d6 | toy finish |

## 7. Real carpark layout (v3 revamp research, 2026-11-16)

Read from public pages only. Used to plan `carpark_layout.py`.

1. A car lot is 2.4 m by 4.8 m. A parallel lot is 5.4 m long. v3 bays are 2.4 by 4.8. Source: LTA Code of Practice on Vehicle Parking Provision, 2019. https://www.lta.gov.sg/content/dam/ltagov/industry_innovations/industry_matters/development_construction_resources/Vehicle_Parking_Proposals/COP_on_Vehicle_Parking_Provision_in_Development_Proposals-2019_Edition.pdf (The lot size came from a secondary summary of this code. The aisle width was not confirmed, so the 6.4 m aisles are a game choice.)
2. A lot beside a wall or column widens to 2.7 m on one side, or 3.0 m with obstructions on both sides. Headroom is 2.2 m. The aisle runs at least one lot length past the last lot. Curved ramp lanes are 3.6 m inner and 3.3 m outer. v3 carport roofs sit at 3.0 m and the dead-end aisles run past the last bay. https://www.lta.gov.sg/content/dam/ltagov/who_we_are/statistics_and_publications/quick_guide_for_development_proposals/quick_guide_8.pdf
3. End lots of a dead-end aisle widen to 3.0 m. https://www.lta.gov.sg/content/dam/ltagov/who_we_are/statistics_and_publications/quick_guide_for_development_proposals/quick_guide_17.pdf
4. Short-span parking structures put columns about 7.6 to 9.1 m apart, standing in the bay rows. Roof parking over a shopping centre has lifts down into the centre. v3 columns stand at bay lines every 7.2 m (three bays) and the lift and stair cores sit at each end. https://en.wikipedia.org/wiki/Multistorey_car_park
5. Red lots are season parking. Red and white lots are season parking at set hours, with the times painted at the lot. v3 paints the outer rows red. https://www.hdb.gov.sg/cs/infoweb/car-parks/shortterm-parking/free-parking and https://www.mnd.gov.sg/newsroom/speeches/view/written-answer-by-ministry-of-national-development-on-clarifying-use-of-bi-coloured-parking-lots-for-overnight-and-daytime-season-parking
6. HDB carpark roofs carry gardens, reached by the carpark lift. Some have community gardens and farms. This is why v3 uses kerbed planters with hedges and small trees as row ends and medians. https://www.nparks.gov.sg/-/media/cuge/ebook/citygreen/cg7/cg7_18.pdf and https://www.mnd.gov.sg/newsroom/speeches/view/oral-answer-by-ministry-of-national-development-on-number-of-community-gardens-and-urban-farms-that-have-been-set-up-on-unutilised-hdb-multi-storey-carparks-to-date
7. HDB lift and stair lobbies are open and cross ventilated. Covered links join the carpark to the blocks. v3 spawns are open lobbies under a canopy between a lift core and a stair core. https://www.hdb.gov.sg/cs/infoweb/-/media/doc/BQG/hdb-arch-technical-requirements.pdf

Not found: an HDB column grid figure and a ramp gradient figure.
