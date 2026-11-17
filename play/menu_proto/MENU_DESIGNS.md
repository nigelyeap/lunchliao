# Lunch Liao! main menu redesigns

Preview mockups only. Nothing here is wired into the game and `chope.html` is untouched. Each file is a standalone page on a fixed 1600x900 stage. Open one in a browser. Click the map chip to open the map picker.

Round 5 (Backdrop with a real menu list) is the current work. Round 3 answered the feedback that round 2 was too busy, too wordy and looked like a website. All earlier designs are still on disk.

Player numbers in the mockups (Level 4, 12 wins) are sample values.

## Research: game main menus

Limits first. Game UI Database returned a 403 to my fetch, so I could not read it. Interface In Game loaded as an index only. The sources below describe layouts in words. I found nothing specific on Deep Rock Galactic, Lethal Company, Valorant, Rocket League, Stumble Guys, Mario Kart or Apex.

- Interface In Game catalogues 406 game interfaces, including Apex Legends, Valorant, Overwatch, Hades and Sifu. Worth browsing by eye for the main menu and start screen entries. https://interfaceingame.com/games/ and https://interfaceingame.com/games/sifu/
- Brawl Stars lobby. The chosen brawler stands in the centre. Player stats sit top left, settings top right. The mode chooser and a large Play button sit at the bottom. https://samurai-gamers.com/brawl-stars/main-menu-guide/
- A Pratt critique of the same lobby says Play works because it is large, bold and bright yellow. It also says the many side buttons and promos confuse new players. https://ixd.prattsi.org/2025/02/design-critique-brawl-stars/
- Overwatch 2. Critiques say the options are stacked down the left, promos take too much room, and players could not find settings because it left the main list. https://eyween.artstation.com/blog/PyAa/independent-ux-case-study-overwatch-overwatch2-ui and https://medium.com/@joelsgrobinson/overwatch-ui-redesign-b32e8fa32685 and https://us.forums.blizzard.com/en/overwatch/t/the-menu-ui-is-a-mess-everything-is-buried-in-sub-menus/711968
- Apple WWDC 2017 session on game UI. Menus get crowded over time. Keep the play button the most dominant element. https://developer.apple.com/videos/play/wwdc2017/811
- Packt on mobile game design says to make Play large and distinctive. https://www.packtpub.com/en-id/learning/how-to-tutorials/mobile-game-design-best-practices
- Abratabia on game menus says the root options are Play, Settings and Credits, and depth should stay shallow. https://www.abratabia.com/game-ui-design/game-menus.php
- A developer write-up on game UI says a main menu should get the player into the game as fast as possible. https://medium.com/@a_kill_/video-game-ui-the-design-process-explained-14c23fa70d37
- A fan redesign thread praises the Fall Guys menu as clean, with one top bar. https://forums.pixeltailgames.com/t/main-menu-redesign-concept-long-thread-warning/39302
- Fortnite. A lobby redesign drew complaints from players. A Game Developer piece says its menu text and icons are too small to read from a sofa. https://www.wepc.com/news/fortnite-players-disgusted-layout-change/ and https://www.gamedeveloper.com/business/two-drunks-stepped-in-a-health-bar-the-jui-joke-user-interface-epic-made-in-fortnite

Patterns taken from this:

- One Play button, bigger and brighter than anything else on screen.
- The character or the scene is the picture. The UI sits around it.
- Secondary items are a short list or a corner cluster. Settings is an icon.
- Almost no body text.
- Mode or map is a small chip next to Play that opens its own screen.

## Round 6: View Characters (v6)

Mockup only. Nothing is wired into the game.

- `v6_roster.html`: all 13 heroes in four role groups (Tank 2, Damage 5, Support 3, Utility 3). Opens from the View Characters row in `v5_backdrop.html`.
- `v6_hero.html?h=<id>`: one page per hero. Numbers, tabs and abilities on the left, the spinning model on the right. The top bar has back to roster and the prev and next arrows.
- `v6_other.html`: a one-page sketch of three more screens.
- `v6_data.js`: hero data copied out of chope.html by a script (HEROES, MAG, BND, plus the HUD icon paths and the ability to icon table). Regenerate it when the game numbers change.
- `v6.css`: styles for all three pages, on top of v5.css.

The model needs the page to be served over http (for example the existing `play/serve.py`). Opened by double click, Chrome blocks the module and the page shows the hero portrait instead. All 13 GLBs in `assets/heroes/` loaded in testing, so no hero fell back.

### Where the numbers come from

- Health, move speed, ult charge, ammo and reload are read from `HEROES` and `MAG` in chope.html.
- Ability text and numbers are the game's own kit strings, unchanged.
- Ability icons use the HUD icon table. The game has no icon for passives, so passives show a star.
- The HUD `KITS` table lists different HP for two heroes (Ah Ma 600, Siaolang 310). The page uses `HEROES`, which is what the match uses (570 and 340).

### Stat bars

Each bar has five segments.

- Health: HP divided by the highest HP (575), times 5.
- Speed: 6.6 m/s maps to 1 and 8.6 m/s maps to 5, straight line in between.
- Damage: steady damage a second from the main attack on body shots, divided by the highest (125), times 5. No reload time, no headshots, no abilities.
- Utility and difficulty: my drafts, 1 to 5. Change them in the `DRAFT` table at the top of the script in `v6_hero.html`.

| Hero | HP | Speed | Damage a second, and how | Utility (draft) | Difficulty (draft) |
|---|---|---|---|---|---|
| Ah Ma | 570 | 6.6 | 71. Combo 50, 50, 82 over three 0.855 s swings | 3 | 2 |
| Gym Hunk | 575 | 7.6 | 81. 50 every 0.62 s, no Reps | 2 | 1 |
| Stinky Uncle | 300 | 7.0 | 66. 50 every 0.76 s, direct hits, no Stink | 4 | 3 |
| NSF | 300 | 7.8 | 121. Full stretch 72.5 every 0.6 s | 2 | 3 |
| Engineer Encik | 275 | 6.8 | 50. 55 every 1.1 s | 5 | 4 |
| Head Prefect | 275 | 7.0 | 34. 27 every 0.8 s, under 10 m | 5 | 4 |
| Teh Tarik Auntie | 300 | 7.0 | 40. Stream on one enemy after 1 s | 5 | 2 |
| Delivery Driver | 300 | 7.6 | 45. Centre stick 17 every 0.38 s, no side sticks or blasts | 2 | 4 |
| Recess Rascal | 285 | 8.6 | 85. 26 every 0.305 s | 2 | 4 |
| Birdwatcher | 300 | 7.8 | 125. Scoped full charge 100 every 0.8 s | 2 | 5 |
| The Siaolang | 340 | 8.2 | 95. 44 every 0.465 s | 2 | 3 |
| Nightclub DJ | 300 | 7.2 | 56. From the kit text | 5 | 2 |
| Ice Cream Uncle | 375 | 7.0 | 88. From the kit text | 5 | 3 |

The damage column is the weakest part. Delivery Driver reads low because side sticks and blasts are left out. Charge heroes read high because every shot is assumed fully charged and on target. A hand-set 1 to 5 rating may be more honest than this formula.

### Other screens that would fit

1. Settings, from the gear icon. One page: sensitivity, volume, field of view, graphics, reduced motion, key bindings, crosshair.
2. Profile, from the level badge. Level and XP, matches, wins, knockouts, most played hero, best streak.
3. How to Play, beside the Tutorial row. Four short cards and a button to replay the tutorial.

All values in `v6_other.html` are sample text.

### Still weak

- The DJ booth and the Ice Cream cart are wide, so those models sit small and close to the right edge.
- The Overview panel is half empty under the bars. A short "how to play this hero" blurb could go there.
- Delivery Driver has six long abilities, so that list scrolls.
- The roster leaves the right third of the screen empty, and the busts are crops of the portraits.
- Skins and Weapons are placeholder slots only.
- The model uses plain studio lighting, so it looks glossier than in a match.

## Round 5: Backdrop with a real menu list

The user meant menu content when they asked for more life. The effects from round 4 were too much. `v5_backdrop.html` drops the disc, rays, light shafts, motes, sway, hop, glow, shine and pulse. It keeps the warmer grade (less hazy), the slow drift, the map cross-fade, the entrance stagger and the Play hover and press states.

The left column now starts under the logo. Chope a Seat sits at the top inside one panel with the map and bots chips, so the chips read as setup for that match. Below it is a list of rows: Practice Range, View Characters, Custom Match (disabled, tagged Soon), Tutorial (tagged New). Rows turn cream and slide right on hover. The hero name and Change hero button are gone because View Characters covers them.

`v5_backdrop_alt.html` is the same with the chips above Chope a Seat. Shots, a hover sheet and an MP4 are in `../shots/menu_redesign/v5/`. It reuses `v4.css` and `v4.js` with `v5.css` on top.

My pick is the main one. The button the user asked to be on top is on top, and the chips under it read as its options.

## Round 4: Backdrop with more life

The user picked Backdrop and asked for more life. Three variants of the same page. The layout, the labels and the picker are identical. Only motion, light and colour differ. The body class (`lv-a`, `lv-b`, `lv-c`) picks the level. Shared code is in `v4.css` and `v4.js`.

All three have a warmer, brighter grade, a slow drift on the backdrop, a cross-fade when the map changes, a staggered entrance, a shine sweep on Play with hover and press states, and a breathing loop on the hero.

- A subtle (`v4_backdrop_a.html`): only the list above, plus a soft warm glow behind the hero.
- B medium (`v4_backdrop_b.html`): adds a kaya disc behind the hero, two slow light shafts, a few light motes, a gentle hero sway, a pulse on Play, a red drop on the logo and a kopitiam tile strip under it.
- C lively (`v4_backdrop_c.html`): adds slow rotating rays behind the disc, more motes, a faster and wider camera drift, a small hop from the hero every 7 seconds, a ring pulse around Play, and a ceiling fan shadow on the two indoor maps.

The hero motion is faked with CSS on the flat sticker. It breathes, sways and hops. It cannot blink or move an arm. The real game should play the 3D model's idle animation.

Shots, strips and MP4s are in `../shots/menu_redesign/v4/`. Each `v4_backdrop_<x>_strip.jpg` shows the entrance, the idle loop and a map change. `v4_picker_strip.jpg` shows the picker opening. `v4_play_states.jpg` shows Play at rest, hover and press.

My pick is B. A fixes the dull colour but still sits quite still. C adds little over B and the ring and hop start to nag.

## Round 3 designs

Shared rules. Main screen labels are Chope a seat, Practice, Tutorial, Change hero, the map chip and the bots chip. Level and wins are one small badge. Settings, Controls and Credits are three icons top right. All five share one map picker layout from `v3.css`, based on the round 2 notice board picker with the pins and paper removed: five large previews in a 3 over 2 grid, name plus one tag each, a ring and tick on the chosen one, and a sixth cell with the chosen name and a confirm button.

Shots are in `../shots/menu_redesign/v3/` as `v3_<name>.png` and `v3_<name>_maps.png`.

### 1. Plate (`v3_plate.html`)
Layout: hero on the left standing on a white disc with a blue rim, like an enamel plate. Menu column on the right with the two chips, the red Play button, then Practice and Tutorial as text. Palette: cream, kopi brown, sign red, rim blue. Fonts: Fredoka, Nunito. Strengths: the calmest of the set, and the eye goes hero then Play. The plate is the only local motif. Weaknesses: the right column is small against a lot of empty cream, and it shows no map art on the main screen.

### 2. Backdrop (`v3_backdrop.html`)
Layout: the chosen map fills the screen, blurred a little and darkened on the left. Hero stands large on the right. Logo top left. Chips, a kaya yellow Play button, Practice and Tutorial sit bottom left. Palette: map colours, kopi shade, kaya yellow. Fonts: Alfa Slab One, Barlow Condensed (the game's current fonts). Strengths: reads as a game lobby faster than the others, and changing the map changes the whole screen. Weaknesses: busier than the flat designs because the map has detail. In the real game this wants a live or slowly panning 3D scene, which is more work than a flat menu.

### 3. Block (`v3_block.html`)
Layout: hero in the centre in front of a painted wall band in mint, butter and peach, like an HDB block stripe. One bottom bar holds everything: Practice, map chip, Play in the middle, bots chip, Tutorial. Palette: pale mint, slate ink, sign red. Fonts: Titan One, Nunito. Strengths: closest to the Brawl Stars and Fall Guys pattern, with the hero dead centre and Play under it. Weaknesses: Practice and Tutorial sit at the far ends of the bar and are easy to miss. The bots chip is wider than it needs to be.

### 4. Bold (`v3_bold.html`)
Layout: one kaya yellow field. The logo runs across the top in very large cream slab type. Hero stands in the centre below it. A slightly tilted cluster bottom right holds the chips, a red Play button, Practice and Tutorial. Hero name bottom left. Palette: kaya yellow, cream, sign red, kopi. Fonts: Alfa Slab One, Barlow Condensed. Strengths: the most character with the fewest parts. Weaknesses: the loudest of the five, so it sits closest to the "too stimulating" complaint. Play is in the corner, so it is a little less obvious than in Plate or Block.

### 5. Window (`v3_window.html`)
Layout: the left 60 percent is a rounded window with a blue rim showing the chosen map. The hero stands in front and steps over its bottom edge. The map chip sits in the window's top corner. A quiet cream column on the right holds the logo, Play, the bots chip, Practice and Tutorial. Palette: cream, rim blue, sign red. Fonts: Baloo 2, Nunito. Strengths: shows the map and the hero together and still keeps a calm column for the buttons. The chip sits on the thing it changes. Weaknesses: the map shot is sharp and detailed behind the hero, so the left side is busy. The hero name in white on the map is the least readable label in the set.

## My read of round 3

Strongest: Backdrop and Plate. Backdrop looks most like a real game lobby. Plate is the calmest and the easiest to build. Window is a fair middle if the map should be visible without filling the screen. Block is solid but plain. Bold is the riskiest given the feedback.

Rough spots in all five. The hero art is a 410x640 sticker scaled up, so it is a little soft at this size. The real game would use the 3D model. The Wet Market card shows "Wet Market" as both name and tag because that is the tag in the shared data.

## Earlier rounds (kept on disk)

Round 2 was seven busier, themed designs. The user found them too stimulating and too wordy. Only the map picker of design 6 was liked, and it is the base of the round 3 picker. Shots are in `../shots/menu_redesign/`.

### Round 2 designs

#### 1. Kopitiam stall signs (`kopitiam.html`)
A red signboard header with a blue rim holds the logo, the three small buttons and the player card. The five maps sit under it as a row of stall signs with unit numbers, a photo and the flavour line. The chosen one gets a red frame and a "CHOPED" tissue tag. Below, Ah Ma stands on an enamel plate next to an order chit that lists place, hero and bots, with the play button on the right. Palette is the game's own enamel cream, sign red, rim blue and HDB pastels. Fonts are Alfa Slab One, Barlow Condensed and Courier Prime. Strengths: closest to the current game, all five maps visible at once, easy to build. Weaknesses: the safest of the set, and the terrazzo background is plain.

#### 2. Lightbox menu board (`lightbox.html`)
The screen is a stall front. A glowing yellow lightbox carries the logo in red with a unit plate. The maps are five numbered dish panels on a menu board, and the pick gets a "TODAY SPECIAL" sticker and a red tick. Ah Ma stands at the counter under a hygiene grade "A" certificate that doubles as the player card. Bots are a spice level with chillies. The play button is a big red block with a service bell and a queue ticket. Palette is lightbox yellow, sign red and teal tile. Fonts are Bowlby One, Sofia Sans Condensed and Permanent Marker. The `#maps` frame enlarges the board. Strengths: the loudest and most hawker of the set, strong hierarchy, the spice level joke lands. Weaknesses: busy, the yellow band has empty space beside the logo, and the Chinese line 午餐了 needs checking by a reader.

#### 3. School jotter book (`jotter.html`)
An open exercise book on a wooden desk. The left page has the logo in marker, Ah Ma as a sticker with a red arrow and a pasted report book strip for level, XP and wins. The right page has the five maps as taped photos with handwritten captions. The pick is looped in red pen with a tick. Bots are a multiple choice question with shaded ovals. The play button is a red rubber stamp block. Practice range and Tutorial are index tabs, and Settings, Controls and Credits sit on a ruler. Palette is paper cream, ink navy and red pen. Fonts are Permanent Marker, Kalam and Archivo. The `#maps` frame is a scrapbook spread. Strengths: the most personal and handmade, very different from any other shooter. Weaknesses: school is only one of five maps so the theme is a step away from food, handwriting is slower to read, and the scrapbook frame has loose empty areas.

#### 4. Lunch Line (`mrt.html`)
A dark green platform sign across the top with exit boxes A, B and C for Settings, Controls and Credits. The five maps are stations LL1 to LL5 on a peach line, each with a photo, code lozenge and flavour line. The pick is marked "YOU ARE HERE". Ah Ma waits behind the yellow line with a stored value "Liao Card". A departure board shows the next stop, bots are a crowd level, and Practice range and Tutorial are taped A4 paper signs with red arrows. Palette is cream tile, sign green, peach and yellow. Fonts are Fredoka and Nunito with Arial on the paper signs. The `#maps` frame is the full line with five large cards. Strengths: the clearest and tidiest layout, maps read as a journey, the paper signs add the human touch. Weaknesses: the least food-related, the dark board has spare space, and it could drift corporate if the paper signs were removed.

#### 5. Mama shop toy box (`toybox.html`)
Ah Ma sits in a blister pack on a sunburst backing card with the logo, a Series 1 badge, a $2.50 price sticker and a barcode. The five maps hang on a peg rail as collectible playset cards. The pick lifts, tilts and gets a "PICKED" sticker. Bots are capsule tokens, the play button is a big glossy red arcade button, and the player card is a collectors club card. Palette is butter yellow, red, blue and peach pegboard. Fonts are Titan One, Nunito and Gochi Hand. The `#maps` frame is a sticker album page with an empty sixth slot. Strengths: matches the vinyl toy look of the characters better than anything else, the play button is the most pressable, and it gives hero and map collecting a natural home. Weaknesses: some small labels are under 13px, the bubble has empty space above Ah Ma, and it says toy shop more than food court.

#### 6. Void deck notice board (`noticeboard.html`)
A cream HDB wall with a peach band and the logo painted like a block number. A green felt board holds a "Have you seen her?" poster for Ah Ma and five pinned map notices. The pick straightens, grows and gets a "THIS WEEK" banner. On the wall to the right are the red play poster, a tear-off strip for bots, two flyers and three letterboxes for Settings, Controls and Credits. The player card is a resident card. Palette is wall cream, peach, rim blue, felt green. Fonts are Anton, Patrick Hand and DM Sans. The `#maps` frame zooms into the board. Strengths: funny and very local, lots of room for seasonal notices and events later. Weaknesses: the hero is small, the play poster is weaker than in the other designs, and the board is the busiest composition.

#### 7. Hawker table and tray (`tray.html`)
A mint terrazzo table seen from above with red stools at the edges. A yellow canteen tray holds five plates, each showing a map as the dish. The pick moves to the centre on a large blue-rim enamel plate with a "CHOPED" flag. The play button is a tissue packet with "put here to chope" written beside it. Bots are three sambal dishes, Practice range is a coaster, Tutorial is a table tent, and the table number disc shows the level. Palette is mint, tray yellow, red and blue. Fonts are Titan One, Fredoka and Gochi Hand. The `#maps` frame is a lazy susan. Strengths: the idea comes straight from the game's name and its play button, it is the most charming, and the big centre plate shows the map well. Weaknesses: the tissue packet is smaller than the centre plate so the main action is less dominant, Ah Ma is front-facing art on a top-down scene, and round crops hide the edges of each map.

### My read of round 2

Strongest: 7 (table and tray), 2 (lightbox) and 5 (toy box). Each has one clear idea that only this game could use. Design 1 is the low-risk option. Design 4 is the cleanest to use. Designs 3 and 6 have the most personality but need the most tidying.
