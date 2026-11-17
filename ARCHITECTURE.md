# Architecture and ownership

Each directory has one owner. Only that owner writes there. Everyone else reads it or asks the owner. Work on coupled render code goes in sequence, one owner at a time. Parallel agents only work on separate directories.

| Path | Owner | What |
|---|---|---|
| src/render/ | Renderer lead (Fable) | Renderer, post stack (AgX, bloom, LUT, AO, AA), sky and sun, haze and light shafts, shadows, material library, presets, shader prewarm |
| src/scene/ | Renderer lead | Scene assembly: map loading, lighting rigs, style-frame scenes |
| tools/forge/ | Texture builder (Sonnet) | Code-generated textures: tiles, formica, steel, stainless, plastic stools, concrete, wood. Output goes to assets/tex/ |
| tools/blender/heroes/, assets/heroes/ | Hero designer (Fable) | Hero models, rig, face rig, expressions and animations as .glb |
| tools/blender/props/, assets/props/ | Prop builder (Sonnet) | Stalls, tables, stools, fans, trays, kettles, woks, bins and other props as .glb |
| tools/signs/, assets/signs/, assets/fonts/ | Sign builder (Sonnet) | Four-language signage baked to textures, with Noto fonts |
| src/game/ | Gameplay porter (later gate) | Gameplay ported from ref/chope.html: kits, bots, scoring, netcode plan |
| src/ui/ | UI builder (later gate) | Kopitiam print menus, HUD and 3D hero cards |
| shots/, tools/shoot.mjs | Shared (write only your own subfolder) | Screenshots from headless Chrome |
| STATUS.md | Orchestrator, with a short append from each agent at the end of its run | Memory between runs |
| ref/ | Nobody (read only) | The source game and reference models |

## Contracts
- **Units and axes.** 1 unit = 1 m, Y up. Heroes face -Z in their rest pose. Glb is the asset format, with Draco or meshopt off for now.
- **Materials.** Props and heroes export glTF PBR (baseColor, ORM, normal). The renderer may swap in its own materials by name prefix, set in src/render/materials.js.
- **Budgets at default.** About 1.2 M triangles on screen, at most 250 draw calls, and textures at most 1024 px per prop atlas, 2048 px per hero. High and Ultra raise these.
- **Screenshots.** Use tools/shoot.mjs with a fixed seed, fixed time of day and a fixed camera from a named shot list. That makes before and after comparisons reproducible.
- **Running it.** `npx vite` serves the project. Each agent uses its own port and its own temp Chrome profile in the scratchpad. Run at most one Chrome per agent, and kill only your own pid.
