# Map redesign proposal (2026-11-16)

Plans: scratchpad td/prop_<map>.jpg (grey = unchanged collider, red X = removed, magenta = new, teal = level 2).
Every collider move is applied with its mirror, so both teams keep the same map. Zones and spawns do not move.
Collider changes need matching nav nodes and collider edits in chope.html (orchestrator B lands, A reviews).

## Hawker: Old Airport Road Food Centre
Look: 3 m stall units with shutters, stall numbers, NEA grade stickers and menu boards. Flat slab ceiling with a beam grid and a skylight over B. Corner blocks dressed as TOILET and TRAY RETURN. HDB blocks behind the railings.
Layout:
- B: the 4 tall pillars and 2 low walls go. A planter ring (four 4 m walls, 1.0 m high) with diagonal gaps takes their place.
- Two 10x4 m island stall blocks at (-10,-10) and (10,10) break the long diagonal lines.
- Tray return stations (1.1 m) at (-24,0) and (24,0).
- The 20 m wall in front of each spawn becomes an 8 m wall. Umbrella tables cover the exits.
- Tables re-gridded into rows at the same count (not drawn).
Nav: B ring, island blocks, spawn exits.

## Void deck: Toa Payoh Dragon Playground
Look: the raised B deck becomes the dragon head on a sand pit with a terrazzo kerb. Mama shop, kopitiam corner, notice board and letter boxes, pastel pillar bands, laundry poles on the blocks.
Layout (adds only):
- Two dragon body humps (5 m long, 1.1 m) beside B.
- Two watermelon domes (2.6 m, 1.2 m) on the open flanks.
- Two bike racks (3 m, 1.0 m) on the side lanes.
Nav: small, six new obstacles.

## Wet market: Tiong Bahru Market
Look: white small-tile floor with wet patches, red lamps and hook rails over the pork blocks, fish on ice, stall number plates, zinc roof with fans, a skylight court at B.
Layout:
- Counter rows cut into short blocks with 3 m cross aisles. North gaps at x -30, -12, 6, 24, south gaps mirrored, so no gap lines up across the centre lane.
- A 9x9 m open court at B.
- Four closed shutter units (2.6 m) and ice-box stacks (1.1 m) on the centre lane, so it is no longer a 40 m sightline.
Nav: largest rework of the flat maps. The aisles change.

## Carpark: HDB rooftop carpark over a food centre (People's Park, Chinatown Complex)
Look: white lot lines and lot numbers, red season lots, coupon parking signs and coupons on dashboards, a yellow dashed spine on z=0, estate colour icon and level number on each stair core, an ochre HDB block behind.
Layout:
- The 24 scattered cars become ordered lot banks, still 24 cars.
- The far-edge car rows go. A 1 m planter and mural wall replaces them on each edge.
- A clear 6 m drive aisle along z=0 through B, framed by 3-car rows at z ±8.5.
- Raised decks and ramps unchanged.
Nav: car positions move, so the nodes near them move.

## Classroom: 1980s-90s neighbourhood school (approved two storeys)
Look: green louvre windows, painted parapet rails, class plates (3E1 style), noticeboards, green boards with flag and crest, water cooler, mop and pail, court lines on the courtyard drop.
Layout:
- Level 2 at +3.5 over both blocks, with corridor parapets and four rooms upstairs. Desks are split between floors, same total.
- West stair in each spawn room, east stair in place of the solid east core.
- A roofed level 2 bridge over the B landing. B stays on level 1, so the upper bridge is a flank route. Falling into the courtyard still kills.
- Locker banks (1.4 m) at x -5.5 and 2.5 so the corridor has cover every 4 to 8 m.
Nav: needs a second nav layer with stair links. The biggest code change of the five.
