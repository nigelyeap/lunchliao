# Wetmarket "Pasar Lorong Tiga" reference

Research caveat: web sources give layout, history and materials but almost no stall-level visuals (hooks, lamps, scales). Items marked (common knowledge) are not backed by a fetched page. Verify against photos before final art.

## 1. Chosen places

Primary: Tiong Bahru Market (old Seng Poh Road Market, 1950/51). Rows of stalls by type (fish and pork, fruit and veg, cooked food), white mosaic floor, zinc pitched roof, hot and crowded, hanging meat. The best match for "nostalgic" and for a rows-and-aisles floor plan.
- https://mothership.sg/2017/02/tiong-bahru-market-looked-like-this-in-the-1980s
- https://biblioasia.nlb.gov.sg/vol-18/issue-1/apr-to-jun-2022/singapore-changing-wet-markets

Secondary (flavour only): Chinatown Complex basement wet market (400+ stalls, live seafood, cut-to-order butchers, busiest early morning), Geylang Serai (ground floor grouped by product: seafood, poultry, veg, spices, dry goods; Malay-house roof style), Tekka (Kandang Kerbau cattle/meat origin, Indian + Chinese stalls).
- https://www.roots.gov.sg/stories-landing/stories/Hawker-Centres/Chinatown-Complex-Market-Food-Centre
- https://honeykidsasia.com/guide-to-wet-markets-in-singapore-where-to-shop-for-fruit-vegetables-meat-and-seafood/
- https://www.roots.gov.sg/stories-landing/stories/Hawker-Centres/Geylang-Serai-Market-Food-Centre
- https://www.roots.gov.sg/stories-landing/stories/hawker-centres/tekka-market

## 2. Visual details to copy

1. White mosaic / small-tile floor, hosed wet. Tiny white tile read with grey grout lines, shine on wet zones. https://mothership.sg/2017/02/tiong-bahru-market-looked-like-this-in-the-1980s
2. Stalls grouped by product in separate rows or zones (fish+pork, veg+fruit). Colour-code zones: A fish, B meat, C veg. https://mothership.sg/2017/02/tiong-bahru-market-looked-like-this-in-the-1980s ; https://honeykidsasia.com/guide-to-wet-markets-in-singapore-where-to-shop-for-fruit-vegetables-meat-and-seafood/
3. Simple pitched zinc roof on exposed frame, hot and stuffy, so ceiling fans and open sides. https://mothership.sg/2017/02/tiong-bahru-market-looked-like-this-in-the-1980s
4. Meat hung openly, no fridge: hooks and rails over the counter. https://mothership.sg/2017/02/tiong-bahru-market-looked-like-this-in-the-1980s
5. Fish shown on ice, "live fish in tubs of water", ice melt makes the floor wet (the reason for the name). https://biblioasia.nlb.gov.sg/vol-18/issue-1/apr-to-jun-2022/singapore-changing-wet-markets
6. Poultry in baskets, customer picks a bird (historic, banned 1993). Use as woven baskets stacked at a poultry stall, no live animals. https://biblioasia.nlb.gov.sg/vol-18/issue-1/apr-to-jun-2022/singapore-changing-wet-markets
7. Fruit piled high, watermelons in string bags, plus eggs, flowers, dried goods, joss sticks on edge stalls. https://mothership.sg/2017/02/tiong-bahru-market-looked-like-this-in-the-1980s
8. Spice and dried-goods stalls with numbered units (example unit "#01-166" style). Use stall number plates on every block. https://honeykidsasia.com/guide-to-wet-markets-in-singapore-where-to-shop-for-fruit-vegetables-meat-and-seafood/
9. Names mix Chinese (ba sha) and Malay (Pasar). Signs: use only the English word MARKET and "PASAR" plus numbers. https://biblioasia.nlb.gov.sg/vol-18/issue-1/apr-to-jun-2022/singapore-changing-wet-markets
10. Courtyard or well in the middle, airy and brightly lit (newer Tiong Bahru). Use for zone B skylight. https://biblioasia.nlb.gov.sg/vol-18/issue-1/apr-to-jun-2022/singapore-changing-wet-markets
11. (common knowledge) Green/white wall tiles on stall counters, red lamps over pork, polystyrene boxes, hand scales, roller shutters, trolleys. Already in current JSON, keep.
12. Busy early, many stalls shut by lunch: justifies shutters that are down at start and open at 60 s. https://www.roots.gov.sg/stories-landing/stories/Hawker-Centres/Chinatown-Complex-Market-Food-Centre

## 3. Layout proposal (game x right, z down; apply every move and its point-mirror (-x,-z))

Current problem: 6 counter rows (z about -9.5, -7, -4.4, 4, 6.8, 9.4) run 8 to 25 m with only small gaps, so the x-axis lanes between them are 40 m+ sightlines.

Real-place logic: Tiong Bahru blocks are short island rows separated by cross aisles, with a central open court. Do that.

Moves:
1. [COLLIDER] Cut each long counter row into blocks of 9 m or less with 3 m cross aisles. North-half rows (z -10..-4): gaps at x = -30, -12, +6, +24. South-half rows get the mirror: gaps at x = +30, +12, -6, -24. Staggered, so no gap lines up across the centre lane.
2. [COLLIDER] Two tall blockers per lane to kill the long line: closed stall units with rolled-down shutters (2.6 m high, 4 x 1.2 m) at (-15, -2.4) and (15, 2.4), plus (-33, 2.4) and (33, -2.4). Reuse shutter art. Opens at 60 s? Keep them static, not the existing shutter.
3. [COLLIDER] Zone B court: open a 9 x 9 m clear court at (0,0), remove the counter blocks that overlap it, ring with 4 existing pillars. Skylight beam, drain grate, wet floor hazard in the court. Cover: one ice-box stack 1.2 m at (-3.5, 2.5) and mirror (3.5, -2.5).
4. [COLLIDER] Cover every 6-10 m in aisles: ice-box stacks and trolleys (1.1 m high) at x = +-9, +-21, +-33 on z = 0. Break lines at eye height with hanging-meat racks (see 7) over some.
5. [COLLIDER] Zones A and C: each gets an island block pair with a 3 m aisle through: A at (-19.2, 13), C at (19.2, -13). Mid-height counter 1.1 m, shop-front behind. Keep the existing shop units along z = +-22.6 as the "wall stalls" with shutters.
6. [NO COLLIDER] Spawn rooms stay. Add roller shutter art to the spawn wall, a "LOADING" bay look: crate pallets and a pushcart outside at x = +-36.
7. [NO COLLIDER] Props: red lamps and hook rails over every second block (z = -9.5 and +9.4 rows), hook rails at 2.4 m so they do not block aim. Polystyrene boxes and fish ice on A zone counters. Weighing scale and plastic baskets on C zone counters. Stall number plates on each block end. Ceiling fans every 12 m (already), add skylight strips above the B court.
8. [NO COLLIDER] Floor: white small tile with grey grout everywhere, darker wet patches near fish blocks, drain gutters along the cross aisles (keep wet hazard patches at the existing places).
9. [NO COLLIDER] Marketing trolley aunties as static toys parked at (-8, -12) and (8, 12), plus bicycle at (-40, -22) and mirror.

Minimum to read as real: short back-to-back blocks, white tile floor, red lamps + hooks, fish on ice boxes, number plates, fans and skylight. Everything else is optional.

## 4. Sketch (top view, half arena x -45..45, z -28..28, "=" counter block, "S" shutter unit, "+" pillar, "B" court)

```
z-28 ##################################################
     |  shop units / shutters (north wall)            |
z-12 |      == ==    ==  ==    ==         == ==       |
z -9 |  ==  ==== ==  ==== ===  ==== ==  ====  ==      |
     |   sp  ==  S         ...      ==   sp            |
z  0 |SP         +  [  B court  ]  +           SP     |
     |   sp  ==      ...  S      ==  ==    sp          |
z  9 |  ==  ==== ==  ==== ===  ==== ==  ====  ==      |
z 12 |      == ==    ==  ==    ==         == ==       |
     |  shop units / shutters (south wall)            |
z+28 ##################################################
     x-45                    0                    x+45
```
Gaps in row z=-9 sit at x -30,-12,+6,+24. Row z=+9 gaps at +30,+12,-6,-24 (point mirror).

## 3. Web research, 2026-11-16 (text only, nothing downloaded)

- https://www.roots.gov.sg/stories-landing/stories/hawker-centres/tiong-bahru-market-food-centre : current building dates from 2004 to 2006. Two storeys on a triangular site around a central garden courtyard. Art Deco style parts. Wet and provision stalls on level 1, provision shops along the outer edge.
- https://johorkaki.blogspot.com/2020/07/history-of-tiong-bahru-market-food.html : wet market on the ground floor. Unit numbers use the "#02-xx" form upstairs, so "#01-xx" downstairs. Small number plates. Meat hung on hooks in the old market.
- https://mothership.sg/2025/07/tiong-bahru-market-reopens-3-months-after/ and https://www.timeout.com/singapore/news/tiong-bahru-market-food-centre-welcomes-customers-back-after-a-three-month-renovation-072125 : 2025 works gave fresh paint, new floor tiles and larger fans. Earlier works (2017) replaced floor tiles, fans and ceiling lights and added a sink at each stall.
- https://commons.wikimedia.org/wiki/Category:Tiong_Bahru_Market : confirms the courtyard garden.

Not confirmed by any page I could read: exact paint colour of walls and pillars, colour of the number plates, signboard design. The build uses white paint, a green tile dado, blue "#01-xxx" plates and cream stall boards as a best guess from sections 2.1 to 2.11 above.

Used in the build: white small floor tile, white tiled counters with steel tops, unit number plate on each counter end, hook rails with hanging chicken and meat over the |z| 9 counters, large ceiling fans, styrofoam fish box stacks, four-language no-smoking plates (wording from tools/signs/WORDING.md).

## 4. Update 5 recolour, 2026-11-16

Nigel asked for saturated colour, so the build no longer uses the white guesses above. Floor terracotta tile #c98f62, stall tiles blue #3f93c4, dado green #2fa37e, walls and pillars yellow #d9b35a, shutters and trim red #d9583a, beams blue #2c5f9e, zinc roof teal #5fa89c, boards yellow #f6c544, number plates red #d8362f. These are game choices, not confirmed colours of the real market.

Follow-up, same day: Nigel wanted more grey. Walls and pillars now concrete grey #a8a59b, beams #9a9890, concrete #b0aca2, floor #b8927a, zinc roof #71a89f. Stall tiles, shutters, signs, lamps and canopies keep the colours above.
