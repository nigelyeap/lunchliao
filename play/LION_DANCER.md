# Lion Dancer (third tank): design draft

Status: design only. Nothing is built. Every number below is a first draft for Nigel to adjust.

## Identity
- Role: Tank, hp 800 (Ah Ma 570, Gym Hunk 575).
- A two-person cloth lion. Protects teammates more than it kills.
- Speed 6.4 at an empty Belly, down to 5.6 at full (Ah Ma 6.6, Gym 7.6).
- Size 1.35 empty, 1.5 full (Ah Ma 1.2). The hitbox size is Nigel's call.
- Ult cost 160 (both other tanks are 150. It's a little higher because the ult also refills the Belly).

## Meter: Belly (0 to 100)
How it fills:
- Feed the Lion: 1 Belly per 4 damage eaten.
- Swallow: 6 a second while a teammate is inside.
- Chomp: 5 a hit.
- It drains 2 a second after 4 seconds without gaining any.

What a full Belly does (it scales smoothly from empty to full):
- Damage taken: 0% to 20% less.
- Knockback taken: 0% to 50% less.
- Move speed: 6.4 to 5.6.
- The body visibly rounds out.

## Kit

| Slot | Name | Draft numbers | Compare |
|---|---|---|---|
| LMB | Chomp | 55 damage, 2.6 m range, 50 degree arc, 0.7 s cycle, +5 Belly | Ah Ma 65 at 0.855 s, Gym 50 at 0.62 s |
| RMB | Feed the Lion | Hold up to 3.5 s. 8 m cone, 60 degrees. Projectiles and instant hits inside the cone are eaten. Gum traps and bells in the cone get sucked in. Move 40% slower while holding. Cooldown starts on release: 3 s plus 1.5 s per second held, so a 1 s Feed comes back in 4.5 s and a full 3.5 s hold in about 8 s | No tank has this |
| RMB release | Spit | Spends all Belly. 20 damage plus 1 per Belly spent, so 120 at full. 4 m splash, 3 m knockback | Gym Battle Ropes 70 to 90 |
| 1 | Swallow | 3 m grab range. Holds a teammate up to 4 s. They heal 30 a second and can't be targeted. Recast to spit them out with a forward boost of about 6 m. No Chomp or Feed while full. 14 s cooldown | Gym Spotter shield 100 |
| 2 | Pounce | Up to 14 m, about 0.6 s of travel. The stretched body blocks shots during the travel. On landing: 50 damage and a knockback within 4 m, a 150 shield for 3 s, size 1.3x for 3 s. Spending 50 Belly gives 18 m and a 250 shield. 10 s cooldown | Ah Ma Seat Rush 9 m at 8.5 s |
| 3 | Firecracker Shake | 5 m radius around the lion. 40 damage, 5 m knockback, enemy aim shakes for 1.5 s. Spending 30 Belly adds a second burst 1 s later. 12 s cooldown | Ah Ma Tiger Balm 15 s |
| Ult | King of the Jungle | Belly to 100 at once. Size 1.6x, a 300 shield, lasts 8 s. Feed has no cooldown and a 12 m cone. Spit becomes a cannonball doing 180 in a 6 m splash. Pounce cooldown halved | Gym Runner's High 8 s, 20% less damage taken |
| P | Digest | When the Belly drains after 4 s without eating, heal 1 HP per Belly point lost (up to 100 HP from a full Belly over about 50 s) | Ah Ma Seen It All, 10% from close range |

## Calls for Nigel
- HP 800 and the Belly damage reduction stack. At a full Belly he effectively has about 1000 HP. Cut the reduction to 10% if that feels too much.
- Feed eating instant hits makes him a hard counter to the NSF and Lens snipers. That might be the fun of it, or it might be frustrating to play against.
- Swallow heals 120 over 4 s. That's close to Ah Ma's Tiger Balm, but it goes on a teammate.
- The Pounce shot block and the ult size make the hitbox big. The model needs a hitbox and polygon budget before it gets built.
- Bots need new logic: Feed when under fire, Swallow a low teammate, Pounce onto the objective.
