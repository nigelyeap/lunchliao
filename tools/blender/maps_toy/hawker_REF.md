# Hawker map reference (Lunch Liao HD)

Research limits: web search only returned history and layout text. Floor material, stall-number format and chope tissue are NOT backed by a source I could open, so they are marked "unverified, common knowledge" below. Check against your own photos before copying.

## 1. Chosen places

1. Old Airport Road Food Centre (Blk 51). Main pick. Built 1972 on the former Kallang Airport runway, 176 ground-floor food stalls, flat roof, shops and a post office upstairs, upgraded 2006-07 (seating 1,904). Loved for the food queues and the 70s-block feel.
   - https://www.roots.gov.sg/stories-landing/stories/Hawker-Centres/Blk-51-Old-Airport-Road
   - https://en.wikipedia.org/wiki/Old_Airport_Road,_Singapore
2. Tiong Bahru Market and Food Centre. Secondary pick for the courtyard idea. The original 1951 Seng Poh Road Market was a wooden structure with a zinc pitched roof, and the old food centre ringed stalls around a central courtyard. The 2004-06 rebuild has a central garden courtyard and an Art Deco style facade.
   - https://www.roots.gov.sg/stories-landing/stories/Hawker-Centres/Tiong-Bahru-Market-Food-Centre
3. Era context (1970s open-air designs: Changi Village, East Coast Lagoon, Adam Road, Tampines Round, Geylang Serai).
   - https://www.roots.gov.sg/stories-landing/stories/our-hawker-culture-built-for-great-taste

## 2. Visual details to copy

1. Dense continuous rows of small stalls along the walls, many more than 8 per side, each narrow (about 3 m). Source: Old Airport Road, 176 stalls. https://www.roots.gov.sg/stories-landing/stories/Hawker-Centres/Blk-51-Old-Airport-Road
2. Flat concrete roof slab with a visible grid of beams, as in 1960s-70s new-town centres (Woodlands, Commonwealth Ave). Not a pitched roof. Same URL as 1.
3. Open, well-ventilated sides with generous roof overhangs (Changi Village, East Coast Lagoon). Perimeter reads as open air, with a low parapet, not solid walls. https://www.roots.gov.sg/stories-landing/stories/our-hawker-culture-built-for-great-taste
4. Raised ceiling or central void for airflow, with daylight from above (Geylang Serai ceiling raised to about twice its height, Hong Lim light tubes, Adam Road higher roof). Use a skylight or clerestory over the mid. Same URL as 3.
5. Central courtyard with planting, stalls and seating ringing it. Source: Tiong Bahru. https://www.roots.gov.sg/stories-landing/stories/Hawker-Centres/Tiong-Bahru-Market-Food-Centre
6. Woven baskets hung from the ceiling as decor (Geylang Serai). Cheap toy-style prop. Same URL as 3.
7. Bright façade colours: green, yellow, orange and blue (Tekka), canvas sail fixtures (Commonwealth Crescent). Use as stall awning palette. Same URL as 3.
8. Umbrella-covered tables outside the main hall (Adam Road). Use for the spawn-side open areas. Same URL as 3.
9. Seating in clear ranks with about 1.2 m between tables (Tiong Bahru), stall rows evenly spaced so diners see the queues (Geylang Serai). So tables go on a grid, not scattered. Same URL as 3.
10. Grade stickers on every stall front. NEA graded stalls A to D and required the grade to be displayed. Now being replaced by SFA's SAFE framework (Phase 1 from 19 Jan 2026), so a letter-grade sticker is period-correct for a nostalgic map. https://www.ichefpos.com/en-sg/blog/sfa-is-the-new-nea and https://www.sfa.gov.sg/news-publications/newsroom/new-safety-assurance-for-food-establishment--safe--framework--to-strengthen-food-safety
11. Tray return stations from 1 Sep 2021, with posters showing which crockery to return. https://www.nea.gov.sg/media/news/advisories/index/cleaner-tables-in-hawker-centres-and-coffeeshops
12. Unverified, common knowledge: stall numbers like #01-23 on a small sign, roller shutters, menu boards with food photos, tissue packets on tables, red or grey terrazzo floor, round fixed tables with 4 stools, HDB blocks visible past the open sides. Source it before relying on it.

## 3. Layout proposal (game coords, x right, z down, arena x +-45, z +-30)

Principle: keep the existing zones, spawns, perimeter stall rows and corner blocks. Change only what makes it read as a real centre. Every move below has its point mirror (x,z) -> (-x,-z).

Does not change colliders (visual only):
- V1. Stall rows at z about +-21: narrow each stall front into 3 m units with a shutter, a number sign, a grade sticker and a photo menu board. Same footprint.
- V2. Flat slab ceiling with beam grid at about 5 m, a skylight strip over x -6..6, z -3..3. Hang baskets and fans from the beams.
- V3. Corner blocks keep their colliders. Dress them as TOILET and TRAY RETURN with a sign each. Paint stall awnings in the Tekka palette.
- V4. Open perimeter feel: replace solid north and south outer wall faces above 1.2 m with railings and a view of an HDB block (backdrop only). Wall collider stays.

Changes colliders:
- C1. Island stall block (back-to-back stalls, Old Airport Road pattern), 12x4 at (-9,-10) and mirror at (9,10). Keeps z=0 lane open and stays 10 m or more from zones A and C. Replaces the nearest scattered tables and short partitions within 3 m.
- C2. Courtyard planter ring at B: four low planter walls (1.0 m high, 4 m long, gaps of 2 m at the diagonals) on a ring of radius 5.5 m around (0,0). Gives close-range cover for zone B. Remove the 4 pillars currently around B.
- C3. Replace the scattered tables with ranked grids: pitch 4 m in x, 3 m in z, in two bands, z about +-14 to +-17, x -33..-13 and 13..33. Table collider size unchanged. About 14 tables per band, keep total count about the same.
- C4. Tray return stands 2x1.5, 1.1 m high, at (-24,0) and (24,0). They are the mid-lane cover for the x axis.
- C5. Keep the side stalls near each spawn at x about +-36 to +-38. Add 2 umbrella tables (round, low collider) each side at (+-35,+-6).
- C6. Delete the long partition walls at x about +-39. They block the spawn exits. Leave one short wall per side.

Checks:
- Longest open line is z=0, from the spawn (41,0) to B. The tray return at (+-24,0) and the planters at B break it into runs under 25 m.
- Diagonal A to C passes z = -0.55 x. The islands at (-9,-10) and (9,10) sit off it, so A and C keep a fight line of about 22 m past B with planter cover.
- Cover spacing: islands every about 18 m in x, tables every 4 m, planters at B, tray returns at 24 m. All within 6-10 m of something solid.

## 4. ASCII sketch (not to scale, N at top, z down)

```
+----------------------------------------------------------+
|TOI| s s s s s s s s s s s s s s s s s s s s s s s s |TRY |
|LET|                                                  |RET |
|   |  o o o o o o        [ISLAND]        o o o o o o  |    |
|   |  o o o o o o        (-9,-10)        o o o o o o  |    |
| S |                    _  _                          | S  |
| P |  u            T   |      |   T            u      | P  |
| A |  u            R   | ( B )|   R            u      | A  |
| W | (-35,+-6)     N   |_    _|   N         (35,+-6)  | W  |
| N |                      A->C diagonal               | N  |
|   |  o o o o o o        [ISLAND]        o o o o o o  |    |
|TRY|  o o o o o o        (9,10)          o o o o o o  |TOI |
|RET| s s s s s s s s s s s s s s s s s s s s s s s s | LET|
+----------------------------------------------------------+
s=stall  o=table grid  TRN=tray return  ( B )=planter ring  u=umbrella table
```
(A at (-19,10.5) and C at (19,-10.5) sit on the diagonal inside the table bands. Zone positions do not move.)

## Real place findings (web reading, 2026-11-16)

Old Airport Road Food Centre, Blk 51. Text sources only. No images were saved.

- Two-storey block. Food stalls are on level 1 and shops are upstairs (136 units in 1972, 54 after 2007). https://johorkaki.blogspot.com/2020/07/history-10-best-hawker-stalls-old.html and https://allwickedlife.blogspot.com/2007/07/new-old-airport-takes-off.html
- 2007 upgrade: new floor and wall tiles, new tables and stools, a mechanical exhaust system, an alfresco plaza with 30 umbrella tables, 168 stalls. https://allwickedlife.blogspot.com/2007/07/new-old-airport-takes-off.html
- 2024 repairs (closed 1 Jun to 30 Sep, reopened 1 Oct): fresh colourful exterior paint, common areas repainted, first-storey floor retiled, all indoor and outdoor tables and stools replaced, 21 high volume low speed fans along the walkway aisle, more light fittings, bird spikes and netting, exhaust ducting cleaned, toilets upgraded. https://mustsharenews.com/old-airport-hawker-reopening/ and https://mothership.sg/2024/09/old-airport-road-food-centre-reopen and https://sethlui.com/old-airport-road-food-centre-mountbatten-reopening-singapore-sep-2024/
- Stall numbers are written like #01-116 and #01-35. https://www.treksplorer.com/old-airport-road-food-centre-singapore/
- A front name sign and a garden exist (file names in the Commons category). https://commons.wikimedia.org/wiki/Category:Old_Airport_Road_Food_Centre

Not sourced: the exact paint, floor tile, table, stool and signboard colours. The text pages name no colours. The HDB block numbers on the skyline are placeholders.

How the build uses this:
- Upper shop storey above the stall rows, steel exhaust ducts above every stall, large slow fans, tube lights, umbrella tables, tiled dados, a front name sign in English, stall numbers in the #01-xx form.
- Colours come from the REF 7 accent set, pushed bold for BRIEF Update 5. See the palette in hawker.py.

## Seating density and greenery (Nigel feedback, 2026-11-16: "way more tables, and less greenery")

Text sources only, no images saved.

- Seating is fixed communal tables and stools in long rows between the stall aisles. https://jetsetter-magazine.com/inspiration/hawker-centres-singapore/
- Maxwell is one hall with stalls round the edge and in inner rows, all facing a central block of communal seating. https://www.treksplorer.com/maxwell-food-centre-singapore/
- Old Airport Road splits its seating into zones you can tell apart by table colour. https://fooddrinkdestinations.com/?p=11041
- Round tables were the norm in estate hawker centres so strangers could share a table. https://www.kitchenaid.com/stories/travel-and-culture/on-hawker-centres.html
- Seating is packed tight. Diners at the renovated Jurong West centre complained of gaps below the usual 8 inches between seats. https://www.theonlinecitizen.com/2024/12/12/complaints-of-cramped-seating-and-poor-planning-arise-after-jurong-west-hawker-centre-renovation
- NEA plans "better spacing of aisles and tables" to cut crowding, so the real thing is denser than a game can allow. https://www.mse.gov.sg/latest-news/oral-reply-to-pq-on-hawker-centre-infrastructure/
- Seating ranks about 1.2 m apart at Tiong Bahru (see section 2 item 9).

How the build uses this:
- v3 (hawker_tables.py) swaps the scattered tables for rows at a 3.8 m pitch: table edges 2.3 m apart, stool to stool 1.56 m. That is the tightest spacing that keeps every lane at 1.5 m or more for the heroes. Tables went from 29 to 59.
- Table and stool colour follows the hall quarter, as at Old Airport Road: blue in two halls, yellow and green in the other two. Zone tables stay orange.
- Greenery is cut back. The halls are indoors under a slab and the sources describe no indoor planting. The B planter ring is now a low tiled ledge with a concrete cap and no plants. The court floor is terracotta tile, the outer grass is paving and only two street trees remain. The four potted-plant colliders keep small pots with a low tuft.
