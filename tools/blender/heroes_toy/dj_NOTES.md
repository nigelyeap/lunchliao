# dj (Nightclub DJ), toy style

Built by dj.py from the gym.py template (same helpers, face, rig, weights, export and shot cameras).

## Identity sources
- ref/chope.html HEROES.dj: Support, size .95, body colour 0xe040c0 (magenta). Kit names (Glow Notes, Drop the Beat, Main Stage) drove the poses.
- ref/chope.html buildDj viewmodel: dark sleeves #1B1A24 with pink trim, a launchpad in the right hand (#1E1A22 with #FF3FB4, #33E6FF and #B44CFF pads plus a pink strip), a mic in the left (black handle, #9AA0AA grille, #33E6FF ring).
- ~/Documents/chope-src/proto-dj (dj.diff, shots/model): high dark brown ponytail, black over-ear headphones with a pink ring, gold hoops and neck chain, winged liner, high-waisted wide-leg pants, chunky platform soles.
- No web sources used.

## Decisions
- The DJ booth is back on Nigel's call, which overrides the +-0.8 prop rule. It is 1.80 m wide, 0.50 deep and 0.63 tall, standing on the floor in front of her with the top at mid torso (z .66). The proto booth was 1.85 x 0.85 x 0.55 but hung below her hover height, so the height is cut to sit on the ground. Body #1F1C26, dark front panel, emissive pink LED strips, 13 EQ bars, two platters with pink labels and tonearms, a mixer between them.
- The booth is weighted to the prop bone, which is parented to hips, so it moves with her body and never with the hands.
- The launchpad and the handheld mic are dropped. Both hands rest flat on the platters in every clip.
- Magenta goes on the crop top and wide pants so the hero keeps the HEROES body colour. The black cropped bomber, pink piping and white platform soles break it up.
- idle nods and scratches the right platter. run keeps the gym legs with the torso steady over the booth. attack (Glow Notes) winds the right hand up and slams the platter. ult (Main Stage) throws the chest back with both hands pressed on the decks.
- Respect: caricature only, no real DJ likeness, no brand marks on the booth or cans.
