# rider (Delivery Driver) toy build notes

Script: `rider.py`, built on `gym.py` (same head, face, shape keys, rig, weights pattern, export settings). Run stages with
`blender -b -P rider.py -- build rig anim export verify shots`.

## Look
- Green half-shell helmet (HEROES body colour 0x2ebd59) with four dark vent slots, dark rim, a short dark visor and a chin strap in front of the ears. Short hair shows under the rim at the sides and back. One dark earbud.
- Green zip jacket with a stand collar, white piping, a silver reflective chest band, dark green hem and cuffs, and silver sleeve bands. Dark sun sleeves on the forearms and a grey neck gaiter.
- Navy shorts with a green hem, white socks with green cuffs, and dark shoes with a white sole and green tongue and heel.
- Cube delivery bag on the back. Green with a dark green lid, a reflective band, a top handle and a plain white disc badge with a generic fork and spoon. Dark straps over the shoulders with a chest clip. It is skinned to the `prop` bone.
- He stands on a delivery kick scooter (old buildRider): dark deck with a green top, two wheels with white hubs and fenders, a silver stem, a white fairing with a pale yellow headlamp, a dark handlebar with grips. The scooter is skinned to `root`, so it moves with him. The deck lifts the body by 0.156 m, and the body itself is 1.80 m.
- Both fists grip the handlebar. The right fist also clutches three giant wooden chopsticks (the Chopstick Fan) in a paper wrap, fanned out forward and up, with dark green tips. The phone is strapped on top of the left forearm with the teal screen up, as in the old game. It is skinned to `lowerarm.l`.
- Umbrella hat on a short pole above the helmet, eight green and white wedges with a green knob (skinned to `head`). Whip flag up the back left corner of the bag with a green pennant and white inner triangle (skinned to `prop`). Both rise above the 1.80 body height.
- Palette comes from ref/chope.html buildRider. The magenta stripe on the old glb was dropped. There are no brand marks and no real delivery company colour scheme beyond the body green.

## Old items restored
Nigel asked for the scooter, umbrella hat and flag back, overriding the x 0.8 prop rule. Body height stays 1.80. The umbrella and flag take the total to about 2.44.

## Face and hands
The head grid is 56 by 28 and the face skin ring is welded onto the head rim after the join (gym's fix), so the jaw and mouth area shade as one surface. The wrist capsule of each hand is thinner than the sleeve end, so no skin and sleeve surfaces sit on top of each other at the cuff.

## Animation
All four clips are rider poses. A small two-bone reach keeps the fists on the grips while the body moves. Idle: breathe, bob, look around and glance down at the wrist phone. Run: kick-push, right foot swings back off the deck while the left knee gives. Attack: the right fist leaves the bar for the fan flick and returns. Ult (Peak Hour Rush): the scooter pops a wheelie on the back wheel (root rotated and lifted), the fan punched high, left fist still on the bar. The ult face is a battle shout with wide eyes and hard brows, unlike the happy grin.

## Process note
The brief's `pgrep -f /opt/homebrew/bin/blender` wait also counts waiting shells whose command line holds that path. With many agents waiting, the count never fell below 7. Runs were gated instead on the number of real Blender executables (`ps -axo comm= | grep -c 'MacOS/Blender$'`), with the same limit of 7.

## Sources
No web sources were used.
