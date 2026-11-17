# New toy heroes (Nigel, 2026-11-16)

Nigel: "there are 9 other characters for you to work on as well." Build the nine heroes that have no toy model yet, one agent per hero:
uncle, nsboy, engineer, debater, rider, rascal, lens, dj, ice.

## Read first
- STYLE_TOY.md in this folder (locked look, five fixes, contract) and SCALE.md (bones, shape keys, clips).
- gym.py in this folder is the quality bar: clothes as one closed mesh with real thickness, collar and armhole cuts, piping, shoes, hands gripping the prop, muscle forms. ahma.py shows a prop held with both hands.
- shots/heroes_toy/gym/*.png and shots/heroes_toy/lineup_new_34.png. Make JPEGs and look at them.

## Who your hero is (identity sources, read all that exist)
- ref/chope.html, `const HEROES` (line ~817): name, role, size, body colour, kit names, voice lines. Also the hero's weapon and ability blocks (grep the key) and its first-person viewmodel `build<Key>` (grep `const build`), which shows the prop and sleeve colours.
- ref/HEROES3.md (lens, siao), ~/Documents/chope-src/ART3.md, ~/Documents/chope-src/heroes10/BRIEF.md.
- Old models: ~/Documents/chope-src/heroes/<key>.glb (all but uncle, dj, ice). ~/Documents/chope-src/proto-art3/demos/{uncle,rascal}_blender.py and .glb. ~/Documents/chope-src/proto-ice/NOTES.md and proto-dj/ for the two newest heroes.
- Keep the old identity: same outfit idea, prop and colours. The HEROES `body` colour is the main outfit colour. Make it the toy version, at gym's finish.
- Respect: caricature body and attitude, never ethnicity. No brand logos, no real-person likeness.
- You may WebSearch and WebFetch real Singapore references (reading only, no downloads). Note sources in <key>_NOTES.md.

## Contract
- Height by size (about 1.88 x size): rascal 1.41 (.75), debater 1.69 (.9), rider, dj, ice 1.80 (.95), uncle, nsboy, engineer, lens 1.88 (1.0). Shipped glb at that height.
- Faces +Y. Bones, shape keys (blink, mouth_open, smile, angry, grin, ult) and clips (idle 60, run 24, attack 18, ult 2, at 30 fps) exactly as SCALE.md. Reuse the rig, weights, anim and export code from gym.py.
- About 25k tris, 30k ceiling. Props inside about x +-0.8 (lens telephoto may reach forward).
- Export assets/heroes/<key>.glb with the same settings as gym.
- Heroes must pop on bold saturated maps (terracotta floors, green and blue tiles, yellow walls). If the body colour blends in, say so in the report.

## Shots
Render shots/heroes_toy/<key>/beauty.png, turnaround.png, expressions.png, anim_sheet.png with gym's stage and cameras. Make JPEGs with
`sips -s format jpeg -s formatOptions 75 -Z 1600 in.png --out <scratchpad>/r5_<key>_<shot>.jpg`
and look at every one, zoomed on face, neckline, hands and hem. Angry, grin and ult must read at 25% size. Iterate until it stands next to gym. Never judge from a Blender buffer.

## Rules
- Write only tools/blender/heroes_toy/<key>.py (plus <key>_*.py, <key>_NOTES.md, _tmp_<key>/), shots/heroes_toy/<key>/ and assets/heroes/<key>.glb.
- Blender: /opt/homebrew/bin/blender -b -P. One process at a time per agent, seven at most on this machine. Before every run: `until [ $(pgrep -f /opt/homebrew/bin/blender | wc -l) -lt 7 ]; do sleep 20; done`.
- Scratchpad: /tmp/lunchliao-scratch
- Never publish, push, upload or download anything. No installs. Do not touch ref/, other heroes or maps.
- Report in under 200 words: look summary, tris, height, the four JPEG paths, any colour concern, honest weakest points.
