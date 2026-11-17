# uncle (Stinky Uncle) toy build notes

Run: `blender -b -P uncle.py -- build rig anim export verify shots`

- Built on gym.py: same toy helpers, rig, weights, OG animation and export call.
- GS is computed in the build stage as HEIGHT / top z and saved to `_tmp_uncle/gs.json`. Later stages read it.
- Identity comes from chope.html (cream body, Utility role) and the old proto-art3 uncle demo. Kept: pear body, comb-over, grey back fringe, big ears, red bulb nose, eye bags, toothpick, singlet with green stink dots, kopi shorts, blue slippers, rolled newspaper (right) and kopi bag on a red string (left).
- The singlet texture needs its UVMap to survive the join. stage_rig puts `singlet` first in the body list for that reason.
- No towel or scarf. ztop() is one smooth symmetric U front and back. spt() makes the singlet hang straight from the belly widest point down to a hem at z .355, over the shorts waistband. Shorts hem is at z .25.
- handslot.l is counter-rotated against hand.l every frame, so the kopi bag always hangs down. Shorts are one remeshed shell bisected at z .30 with a tan torus cuff per leg.
- No web sources used.
- Neckline: ztop is a parabola U across the straps (front 8.5 cm deep, back 6.5 cm). atop() re-solves the angle from a monotonic table so x follows the analytic curve, mirrored in X. Piping uses the same curve.
- Back hair: none. Nigel asked for a bald back of the skull, only the comb-over strands and brows remain.
