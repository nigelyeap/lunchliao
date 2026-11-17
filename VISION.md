# Lunch Liao! HD: vision

Nigel wrote this brief on 2026-11-13. Every agent reads this file first. If another doc disagrees with it, this file wins.

## What this is
This is a full visual rebuild of Lunch Liao!, a Singapore hawker-centre hero shooter where teams fight to chope tables at lunchtime. Everything about the story, the heroes, their kits, the scoring and the choices stays the same. All the graphics are new: renderer, models, maps, HUD and effects. The players are Singaporean, so the place has to feel real to someone who eats at one every day.

The source game is in ref/chope.html (read only). Its sounds are copied to public/sfx and are reused as they are, along with the mix engine and music.

## Look
- **Painterly and beautiful (Nigel, 2026-11-13, overrides the first brief).** Nigel's verdict on the first Ah Ma: she "looks like an eldritch horror". Go less realistic and more oil-painty. Think of a living oil painting, in the spirit of Arcane or a Ghibli background, but with our own designs.
  - Every surface has visible brush strokes and soft colour shifts. Use no photoreal skin, pores, wrinkles or grime blotches.
  - The renderer adds a painterly pass, such as a Kuwahara filter, that keeps silhouettes crisp.
  - Faces are simple and appealing, with clear shapes and big readable expressions. Do not model realistic eyes behind thick lenses, gaping mouths or uncanny detail.
  - **Arcane is the target look (Nigel, 2026-11-13).** Take the techniques, never Arcane's characters, logos or designs:
    - Hand-painted textures with visible strokes. Painted detail sits over simple 3D forms.
    - Shading is stepped and graphic, with soft painted edges between light and shadow.
    - Rim and bounce light are bold and saturated. Warm key, cool teal or violet shadows.
    - Faces are stylised with painted features: shaped brows, painted eyes and lips. Expressions are acted, the way a hand-drawn character acts.
    - Fine ink lines appear only where a form needs one.
    - Effects like steam, fire, slippers and teh look painted or 2D.
  - Keep rim light, readable silhouettes and clean shape language. No mannequins, no blocky hands, no default-material grey.
- Golden hour with humid haze. A warm, low sun comes through the open sides of the hawker centre. Ceiling fans turn, steam rises off the stalls, and light shafts show in the haze.
- Heroes are chunky caricatures: bigger heads, squat bodies, lots of detail. **Keep each hero's size relative to the others the same as the current game** (reference models in ref/heroes). **Drop the KayKit look completely.** No KayKit meshes, proportions or flat-colour faces.
- Faces have full expressions. Brows, eyes and mouth are rigged, with at least these states: idle, angry while shooting, a grin after a kill, and an ult face.
- In-world signs use all four official languages: English, Chinese, Malay and Tamil. Think stall signboards, the NEA grade sticker, "no smoking" signs, tray-return posters and table-number plates. Typeset them with Noto fonts (OFL). Only the baked textures ship.
- Menus and HUD are in English only, in a kopitiam print style: warm cream, ink outlines, kaya gold, the chunky slab title, more depth and motion than the old game, and 3D hero cards.

## Vertical slice (the current target)
- One map: Hawker Centre.
- Four heroes: Ah Ma, Gym Hunk, Teh Tarik Auntie and Siaolang.
- It is playable with bots and uses the tuned gameplay from ref/chope.html.

## Hard limits
- WebGL2 through three.js 0.180.0, with vite 6.3.5 and esbuild 0.24.0. All are installed in this folder, with exact versions. Install nothing globally.
- 60 fps at default settings on an M1 MacBook Air or Iris Xe at 1080p. High and Ultra presets can go above that budget. Measure frame time, don't guess it.
- Make every asset yourself. Use headless Blender 5.2 (/opt/homebrew/bin/blender) scripted from Python, plus textures, foliage, signage and effects generated in code. The only download allowed is Noto fonts from github.com/notofonts. Never use AI image or audio generators, store assets or KayKit.
- Desktop browser only. The upload target is CrazyGames, as a folder. Never publish, upload, push or deploy anything. Nigel does that.
- Player-facing text has no em dashes and no semicolons. Chinese and Tamil appear on in-world signs only.
- Hitboxes and gameplay numbers come from ref/chope.html. Changing them is Nigel's call.

## Banned outcomes
- The KayKit look, or anything that reads as an asset-store kit.
- Mannequin bodies, blocky hands or faces with no expression.
- Flat lighting with no shadows, or a grey-blue haze that kills the warm mood.
- Fake or garbled Chinese and Tamil text. Get each sign checked against real wording.
- Generic "Asian" decor that isn't Singaporean (no lanterns everywhere, no Japanese signs).
- Shader hitches the first time an effect plays. Prewarm them.
- Effects bright enough to hide enemies. Readability comes first.

## Gates (Nigel signs off at each one)
1. **Style frames.** One hero (Ah Ma) and one hawker stall corner, rendered in the real engine. Send the shots and a short note.
2. **Hero looks.** All four heroes posed, with expressions, next to the old models at the same scale.
3. **Map greybox.** Hawker Centre layout with the lighting pass, matching the old map's lanes and tables.
4. **Playable slice.** Bots, kits, HUD, effects and sound, at 60 fps on the default preset.

Between gates the team works on its own. Stop for Nigel only at a gate, or for a big decision: budget, hitboxes, a new hero or a gameplay change.
