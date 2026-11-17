# ice (Ice Cream Uncle), toy build notes

Sources used. No web sources.
- ref/chope.html: HEROES `ice` entry (Support, size .95, body colour 0x8fd0ef), the ICE flavour list, and buildIce (white right sleeve, blue frost nozzle in #7FB8E0, #DDE8F0 and #2C7FB8, wafer #D9A35B and yam #9B6FC4 sandwich in the left hand).
- ~/Documents/chope-src/proto-ice/NOTES.md: red freezer box with dark base and white trim, steel lid with two hatches, wafer stack, rainbow bread and brass bell on the lid, blue frame, 8 panel red and yellow umbrella above head height. Uncle in a cream bucket hat with belt and green waist pouch.

Decisions (cart revision, Nigel's call overrides the x 0.8 prop rule).
- Outfit is a white singlet with a scooped neck, narrow straps and deep armholes, sky blue piping at neck and hem as the HEROES body colour nod. Khaki shorts, belt, green waist pouch, cream bucket hat, blue flip flops.
- Pot belly is a front only bulge. Soft jowls. Short grey hair under a tilted back bucket hat so the brows stay clear.
- He pushes the cart in front, as in the old game (both hands on the bar there). Here the left fist grips the push bar and the right hand keeps the frost nozzle. The left arm is locked to the bar in every clip.
- Cart layout and sizes come from iceCart in proto-ice/ice.diff, shrunk to 0.62 of old size so the push bar meets his toy hands at 0.57 m. Umbrella kept big: 2.4 m canopy, rim at 2.05 m. Freezer box sidecar on his right front, step-through scooter on his left front, umbrella pole at the box front outer corner.
- Cart is one mesh named CART, all weighted to the `prop` bone, which is parented to root. Hide CART in game to drop it.
- Height is set by measuring the hero without the cart and scaling to 1.80 (gs.txt in _tmp_ice).
- attack is a one arm nozzle sweep. ult thrusts the nozzle up over the cart.
