# debater (Head Prefect), toy style

Run: `/opt/homebrew/bin/blender -b -P debater.py -- build rig anim export verify shots`
(add `beauty`, `turn`, `expr`, `sheet` or `hands` after `shots` to render only some shots)

## Identity sources
- ref/chope.html: HEROES entry (Head Prefect, Utility, body 0x7b2436), voice lines
  (Point of information, Silence, No running, Stay back, Detention) and the kit
  (Strong Words shout, Silence bell, No Running megaphone, Detention area ult, arms-wide hold).
- ART3.md: tall hair or mortar board, blazer, tie, lectern card.
- Old glb ~/Documents/chope-src/heroes/debater.glb: maroon blazer with gold piping, white shirt
  and collar, striped tie, badge, gold buttons, slate pleated skirt, white socks, black shoes,
  round black glasses, short black hair with a high ponytail.
- No web sources used.

## Build notes
- Built on gym.py: same toy helpers, face system, weights, Pose code and export settings.
- Megaphone in the right fist (pistol grip), desk bell on the left palm.
- GS (unit to metre scale) is measured in the build stage and stored in _tmp_debater/gs.txt.
- Colour: maroon blazer is close to terracotta map floors. Gold piping, white shirt, collar
  and socks carry the silhouette there.
