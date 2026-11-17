# Hero polish pass (Nigel, 2026-11-16)

Nigel signed off Gym Hunk after several rounds ("ok gym guy is good now. start working on the other characters as well."). Bring Ah Ma, Teh Tarik Auntie and Siaolang up to the same finish. One agent per hero.

## Read first
- STYLE_TOY.md in this folder (the locked look, the five fixes, the contract).
- gym.py in this folder: the quality bar. Read how it builds clothes as one closed mesh with real thickness, the collar and armhole cuts, piping, shoes, hands gripping the prop, and the muscle forms.
- shots/heroes_toy/gym/*.png and your own hero's current shots in shots/heroes_toy/<key>/. Make JPEGs and look at both before you start.
- Your hero's current file: <key>.py (ahma, tarik, siao). Keep what works, rebuild what does not.

## What to do
1. Self-review first. Put your hero's current beauty, turnaround, expressions and anim_sheet next to gym's. Write down every place where your hero looks cheaper: lumpy or faceted forms, patch seams on the face or body (gym had a visible lower-face patch, check for the same), clothes that read as shells or tube tops, print smear, floating props, hands that do not grip, flat or unreadable expressions, skin poking through clothes in run or attack frames.
2. Fix them all. Clothes must read as the real garment from front, side and back. The character must stay recognisable: same outfit idea, same props, same personality, same colours unless they clash with the new saturated maps.
3. The maps are now bold and saturated (terracotta floors, green and blue tiles, yellow walls). Your hero must still pop against them. If a colour blends in, propose a change in the report rather than repainting the whole outfit.
4. Expressions: angry, grin and ult must read from 10 m. Check expressions.png at 25% size.

## Contract (unchanged, see STYLE_TOY.md)
- Heights: ahma 2.16, tarik 1.80, siao 1.88. Faces +Y. Bones, shape keys and clips as SCALE.md.
- About 25k tris, 30k ceiling.
- Export assets/heroes/<key>.glb with the same settings as before.

## Shots
Rerender shots/heroes_toy/<key>/beauty.png, turnaround.png, expressions.png, anim_sheet.png. Make JPEGs with
`sips -s format jpeg -s formatOptions 75 -Z 1600 in.png --out <scratchpad>/r5_<key>_<shot>.jpg`
and look at every one, zoomed in on the face, the neckline, the hands and the hem. Never judge from a Blender buffer.

## Rules
- Write only tools/blender/heroes_toy/<key>.py (plus <key>_*.py helpers and _tmp_<key>/), shots/heroes_toy/<key>/ and assets/heroes/<key>.glb.
- One Blender process at a time per agent. Seven at most on this machine.
- Scratchpad: /tmp/lunchliao-scratch
- Never publish, push, upload or download anything. No installs.
- Do not touch ref/chope.html or other heroes' files.
- Report in under 200 words: what you changed, tris, height, the four JPEG paths, any colour change you propose, and your honest weakest points.
