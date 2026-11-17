# Reload for the ranged cast: plan

Status: approved by Nigel 2026-11-16 with the changes below. Being built.

Nigel's changes: DJ and Ice Cream Uncle get bigger mags. Teh Tarik Auntie is left out. Every hero that gains a reload gets +25% damage, Delivery Driver +40%. NSF and Birdwatcher also get +25%. Birdwatcher's reload becomes a camera battery swap. Each hero gets its own stylised reload animation.

## Who gets it

NSF and Birdwatcher already reload (BND table, chope.html:940). Head Prefect is left out, as asked. Ah Ma, Gym Hunk and The Siaolang are melee, so they're out too.

| Hero | Fire rate now | Draft mag | Reload | One mag lasts |
|---|---|---|---|---|
| Stinky Uncle (Booger Flick) | 0.76 s | 6 boogers | 1.6 s | about 4.6 s |
| Engineer Encik (Foam Dart) | 1.1 s | 5 darts | 1.5 s | about 5.5 s |
| Delivery Driver (Chopstick Fan) | 0.38 s | 12 fans | 1.6 s | about 4.6 s |
| Recess Rascal (Paper Shuriken) | 0.305 s | 15 shuriken | 1.4 s | about 4.6 s |
| DJ (Glow Notes) | 0.111 s | 60 notes | 1.8 s | about 6.7 s |
| Ice Cream Uncle (Brain Freeze) | 0.1 s ticks | 6 s of mist (60 ticks) | 1.8 s | 6 s |

Ice Cream Uncle fires a stream, so he gets a tank that drains while held instead of a count. It uses the same reload rule.

## How it works (same for everyone)
- Reload starts on its own at empty. R reloads early when the mag isn't full.
- You can't fire while reloading. Moving and abilities still work.
- Ult rule: an ult refills the mag and pauses reload for its length, like NSF's Live Firing does now. Each hero's ult gets checked one by one, and any that already fire freely stay that way.
- Death and respawn refill the mag.
- Bots reload at empty. They also reload early when no enemy has been in sight for about 2 s.

## Build steps (one landing each, by the single writer, gate and shots every time)
1. Generalise the code. Turn BND's mag and reload fields into one `MAG` table for all heroes, and split `bandReload` into a shared `magReload`. NSF and Birdwatcher must behave exactly the same afterwards (headless check: same shots, same reload timing).
2. Add the count heroes: Uncle, Engineer, Driver, Rascal, DJ. Each one decrements in its branch of the fire code (chope.html:4235 to 4258).
3. Add the tank hero: Ice Cream Uncle (the ice branch).
3b. Damage: +25% on the primary fire of Uncle, Engineer, Rascal, DJ and Ice Cream Uncle. +40% for Delivery Driver. Update the kit text numbers to match.
4. Counter UI. The new option 1 counter (big number plus pips) gets used for all of them. At 12 to 40 rounds pips get cramped, so above 10 rounds it shows a thin fill bar instead. Tank heroes always use the bar.
5. Reload animations. Add a short first person clip per hero to the RLV table (chope.html:4266), plus a reload sound. Keep each under about 1 s of motion so it fits inside the reload time.
6. Bots: hook the bot logic into the reload rule above.
7. Shots of each hero full, low and reloading go to shots/reload_all/. One rebuild of chope-itch.zip at the end.

## Still open for Nigel
- Engineer's turrets: the draft says they don't reload, only his gun does.
- Mag sizes and reload times are still drafts.
