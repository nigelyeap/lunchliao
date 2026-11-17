# Lion Dancer (lion), toy style

Build: `blender -b -P lion.py -- build rig anim export verify shots`. Add `look` after `build` for quick check renders in `_tmp_lion/`.

## Research: what a Singapore southern lion looks like (v2)
Reading only. Each point lists where it came from.

What Singapore people remember: the Fut San (Foshan) or Fut-Hok hybrid lion at CNY, shop openings and void decks. Drums, gongs and cymbals, two dancers, a lettuce and ang pow (cai qing) hung over a door. [1][2][3]

Head
- Huge compared to the dancer. Papier-mache and rice paper on a bamboo frame (over 100 strips), painted bright. The front dancer wears it over his head and shoulders and looks out through the mouth. When excited he lifts it high above his head with his arms. [1][4][5][6]
- Foshan face: long head, large round high forehead, fierce look. The mouth is curved and wide, with visible upper teeth. Heshan is flatter with a duck-bill mouth. Singapore mixes the two (Fut-Hok). [1][2][7]
- Big round convex mirror in the middle of the forehead. It wards off evil spirits. [8][9]
- One horn on top, pointed on Fut San. [1][7]
- Big eyes in gold-rimmed sockets. The eyelids move and blink. The lids carry fur and long lashes, with rabbit fur also used as lower lashes. [1][9][10]
- Movable ears that flap. [7][10]
- Lots of coloured pom-poms on the head. [10]
- Fur everywhere: rabbit fur or wool trims the head rim and mouth. Gold trim sits between fur and paint. The lips are big and fluffy. White beard under the chin on Liu Bei style lions. Fur eyebrows. [1][9][10][11]
- Painted all over with swirls and scroll patterns in many colours. Gold foil rims. A gilded collar where the troupe name may be written. [1][4]

Body and tail
- Long layered cloth (about 3 m in the 1960s) trimmed with rows of fur, multicolour, with scale or diamond patterns down the back. [1][2][7]
- Fut San tail is long with a white underside and sometimes bells. Hok San tail is short. [1][7]

Dancers
- Pants match the lion, made of fur or silk with golden fur, loose and gathered at the ankle with a fur cuff. Black kung fu shoes. [12][13]
- The tail dancer bends forward under the cloth and carries the weight. [5]

Colours
- Traditional are yellow, red and black, with green and blue added later. Liu Bei lion is yellow with white fur and a multicolour tail. Guan Gong is red with black fur. [1][2]

Sources
1. Wikipedia, Lion dance: https://en.wikipedia.org/wiki/Lion_dance
2. SCCC Culturepaedia, southern lion: https://culturepaedia.singaporeccc.org.sg/?p=3374
3. NLB Infopedia, lion dance: https://eresources.nlb.gov.sg/infopedia/articles/SIP_57_2004-12-27.html
4. Homo Faber, Henry Ng lion heads, Singapore: https://www.homofaber.com/en/artisans/henry-ng-hong-kiang-mask-making-singapore
5. ANZA, the head of the lion: https://anza.org.sg/2023/01/17/stars-of-cny-the-head-of-the-lion/
6. Asia News Network, lion head makers: https://asianews.network/?p=245548
7. Lim's Lion Dance, types of southern lion: https://sites.google.com/view/limsliondance/types-of-southern-lion
8. The World of Chinese, lion heads: https://www.theworldofchinese.com/2023/06/how-chinas-dancing-lions-get-their-heads/
9. Neocities lion dance shrine: https://bluuhcknotch.neocities.org/shrines/lion%20dance/newyearslions.html
10. China-cart, lion dance costumes: https://www.china-cart.com/lion-dance-costumes.html
11. Wukong Wushu, lion head notes: https://wukongwushu.com/?p=184
12. National Costume, Hok San fur lion dance pants listings: https://national-costume.com/
13. Roots.sg, lion dance: https://www.roots.gov.sg/ich-landing/ich/lion-dance

## What v1 got wrong
- Head read as a smooth red ball, too narrow, plain sides, no pom-poms, thin fur.
- Lower half was one red mass. Jaw rested too open.
- Body cloth was a narrow red tent with one print.

## v2 plan from the research
- Wider head with a high domed forehead, a big mirror, painted gold and colour scrolls on the sides, one horn.
- Many coloured pom-poms over the top, round the horn and on the ears.
- Fur-lashed eyelids, fur brows, a thick fur rim round the face, fluffy fur lips on the jaw, big white beard.
- Gilded collar band at the back rim.
- Wide body with crosswise fur rows down the back, scale print, a green and blue layered hem with fringe.
- Gold fur pants with white fur cuffs to break the red. Broad shoulders on the front dancer.
- Jaw rests nearly closed.

## Contract
- Height 2.54 m (size 1.35). Faces +Y in Blender, -Z in the glb.
- Bones: all SCALE.md names. Extras: `rear`, `rthigh/rshin/rfoot .l/.r`, `tail`.
- `prop` is the jaw hinge. Shape keys on `lion_head`: blink, mouth_open, smile, angry, grin, ult. `belly` on `lion_body`.
- Clips at 30 fps: idle 60, run 24, attack 18, ult 2. Extras: feed 30, pounce 20, shake 18.

## Verified v2 (glb re-import)
- 34,885 tris (head 20,196, body 14,689). Height 2.545.
- Footprint X -1.010..1.005, Y -1.632..0.858 (Blender axes, +Y front).
- Head mesh bbox centre in head bone space: y 0.306, z -0.065 (TOY_HDL). Head size about 1.73 x 1.19 x 1.62.
- Jaw rests 10 degrees open so the upper and lower teeth show.
- Known gaps: open-mouth keys show a dark mouth floor behind the tongue. Front dancer torso reads as a dark lump under the beard.

## v3 Hok San head (Singapore style)
- Reference: user photo (_tmp_lion/ref1.png). Style notes from Lim's Lion Dance types page: Hok San has few balls, fur brows, a forehead mirror.
- Only the head was rebuilt. GS frozen at GS_BODY so body, cloth, tail, dancers and stance stay as v2.
- Head built at v2 size then shrunk with HS(p) = HPV + (p - HPV) * HK + HOFF, HK .78. Rig eye bones, prop bone and jaw-key pivot use HS too.
- Features: red fur rim, fur brows and big fur lower lip. Gold face panels with black swirl lines (procedural texture). Orange cheek balls with swirls. Black fur puffs under eyes. Mirror in a red fur ring with a red flower on top. Simple flat eyes: white dome, bronze iris, fur lids, no highlights.
- Removed: horn, crest, pastel pom-poms, ears, white beard.
- Front dancer torso and shoulders moved back and down so nothing shows inside the open jaw. Mouth interior is pink. Cloth front top lowered to 2.10 to tuck under the smaller head.
- 30,987 tris (head 16,348, body 14,639). Height 2.204. Footprint X -1.008..1.005, Y -1.632..0.734.
- Head bbox centre in head bone space y 0.250, z -0.064. Size 1.423 x 0.939 x 1.047.
- Known gaps: red reads slightly coral under toy lights. Head is shallow from the side. v2 backup in _tmp_lion/lion_v2.py.

## v4 Hok San frame (2026-11-16)
- Head rebuilt as a rigid frame: boxy superellipsoid shell (HX 4/5/3.5), sheared back by LEAN so the forehead leans, tapered, flat mouth roof. Square shovel jaw (superellipse revolve, JE 3.2).
- Fur is directional clumps (clump_vf): lip hangs down in three rows, brows and rim sweep back, big lobes on the top corners. No round puffs.
- Mirror high on the forehead in a gold frame with a red clump ring. Eyes are bronze balls with a gold rim and cream socket ring, thick red lids, neutral lu 68 tilt 20.
- Red is #C8102E. Cape green and blue hem bands removed. Red bib with white fur hem fills the gap under the head (weighted chest to head).
- Tris 34,577. 33 bones, 7 actions, 6 face keys plus belly. Backups in _tmp_lion/lion_v3.py and lion_r13.py.
- Limits: smooth toy clumps, no fur texture, so it never gets the shaggy look of the photo. Shell is still one smooth superellipsoid, not separate bevelled panels.

## v5 mouth (2026-11-16)
- Rest jaw opened to 22 deg. Dark mouth (#4A0810), pink tongue, gold lower lip bar matching the upper one, 2 bold fangs top and bottom.
- Removed the 18 small teeth and all hanging lip clumps. Lower jaw fur is one clean roll below the gold lip.
- Jaw keys relative to rest: mouth_open 20, smile 4, angry 8, grin 12, ult 18.
- Bib widened (rx .56, wraps -30 to 210 deg), made shallower (ry .25) and shorter (top 1.38) so it hides the dancer and does not clip the open jaw.
- Tris 32,273. New 'far' shot (8 m, raised) writes _tmp_lion/far.png. v4 backup in _tmp_lion/lion_v4.py.

## v6 mouth sheet, tiered cape, simple eyes (2026-11-16)
- Mouth: all 4 fangs removed. The jaw bowl is now a flat crimson sheet (mouth_sheet #D8344A) across the opening, with a flat pink tongue pad (TONGUE flag). Jaw keys unchanged.
- Eyes: white ball, one black socket ring, one big black pupil aimed forward, plain red lids. Gold rim and bronze iris removed. Lids opened up (neutral lu 56, ll 34).
- Cape: three lengthwise tiers a side, shingled from spine to hem (TB, TF, TA, TR, TS, TK, TP). Each tier flares out, ripples and scallops, more towards the back. Gold strip and a white fur rope on each upper tier edge. Rump pinches closed (cloth_dims rump term). NS 30, NP 25.
- Print: tone on tone scales with a small gold dot per scale. UV u is taken from one row so the print does not shear.
- Bug fixed: H.join left the UV layer not render-active, so the cape print sampled texel 0 and rendered flat in every rigged shot since v2. Now set after join.
- Face panel: two wavy crimson bands and a dot row low on the panel, small red dots between swirls (panel_curves, panel_dots).
- Tris 33,115 (head 15,918, body 17,197). 33 bones, 7 actions, 6 face keys plus belly. Height 2.318. Footprint X -1.120..1.122 (v5 was about 1.01), Y -1.632..0.647.
- Limits: the print fans out and stretches on the rump. Cape is rigid, the folds are modelled and do not move. No ringed rosettes, the forehead mirror stands in. v5 backup in _tmp_lion/lion_v5.py.

## v7 cape from the hinge, plain lion face, matte eyes (2026-11-16)
- Cape: starts inside the head at the jaw hinge (Y0 -.08) and comes out under the mane. Front edge is narrow (.50) with no tier flare (ss(0, .18, s)), so there is no gap from any turnaround angle. Dancer shoulders narrowed to rx .42 to stay under it.
- Face: all black print gone except one big crimson swirl per temple (panel_curves). Removed the plate, gold upper lip, mirror fur ring, petals, flower, socket rings, black fringe, gold collar and swirl cheek balls. The mirror stays as a plain disc. No horn, no new ornaments.
- Lion forms: rounder dome (HR .70/.46/.56, HX 2.8/3.2/2.6), heavy rolled brow ridges (tube_vf, in the keyed face), two white muzzle pads, wide dark red nose with nostrils, thick red lip roll round the mouth (h_lip), gold cheek pads, three row mane (h_rimfur), white fur beard in two rows under the jaw (j_beard).
- Eyes: ER .21, sunk .07 into the head. Off-white ball (#DCD2BC), dull amber iris, dark brown pupil, all matte (rough .85 to .9, no coat). Upper lid cuts across the top of the ball (neutral lu 68). Blink closes fully (lu 101, ll 80).
- Mouth sheet unchanged, no teeth. Cape print tile .30 (smaller), cloth rough .62, coat .08.
- Tris 32,441 (head 15,252, body 17,189). 33 bones, 7 actions, 6 face keys plus belly. Height 2.289. Footprint X -1.121..1.126, Y -1.632..0.760 (the muzzle and nose add .11 at the front).
- Limits: head outline is still squarish from the front and back. The white beard sits right above the white bib trim and can read as a tooth row from the front. Print still fans on the rump. Cape still shows a soft sheen in side light. v6 backup in _tmp_lion/lion_v6.py.

## v8 back to the costume head (2026-11-17)
- v7 was rejected: it read as a real lion. v8 starts from the v6 head (boxy Hok San shell, mirror with fur ring, fur brows, pom balls, black whisker band, top flower). v7 is in _tmp_lion/lion_v7.py.
- Shared ref features used as the build list: blocky head, wide mouth under a broad lip band, big fur brows over the eyes, large blank eyes in a rim, raised forehead mirror, two pom balls above the lip, plain gold face panel, dark fur under the eyes. No animal nose in either ref.
- Removed: nose, nostrils, muzzle pads, beard, cheek pads, iris and pupil (and the keyed pupil mesh).
- Upper lip: broad red fur band round the mouth edge, fattest at the front (h_lipfur), with the gold lip edge under it.
- Eyes: blank matte off-white ball (#D9D0BC, rough .95) in a matte black rim. No iris, pupil or highlight. v6 lids and keys unchanged, blink closes.
- Face panel is plain gold, no print. Pom balls are bigger (.13) with one swirl each.
- Kept from v7: cape from the jaw hinge (Y0 -.08, front width .50), print tile .30, cloth rough .62, narrow shoulders, no teeth, no horn.
- Tris 33,687 (head 16,498, body 17,189). 33 bones, 7 actions, 6 face keys plus belly. Height 2.318. Footprint X -1.121..1.126, Y -1.632..0.643.
- Differs from the refs: smooth toy clumps, no shaggy fur. No patterned gold panel (the photo has swirls all over it). Eyes are blank balls, the photo has a white ring with a bronze ball. Lip is red fur as in the photo, the pastel ref has a cream beak plate. No beard fringe under the jaw. Print still fans on the rump.

## v9 beard, eye rings, one red costume (2026-11-17)

Backup of v8: `_tmp_lion/lion_v8.py`. Variant B (face panel rings) was cancelled.

- Beard: two rows of red fur clumps under the lower jaw, object `j_beard`. It lives in the head mesh on the `prop` (jaw) bone, so it follows both the jaw bone and the jaw swing baked into the six face keys. The build undoes the `j_` rest swing and head shrink on it so the specs stay in body coordinates.
- No white under the jaw. The white bib trim is gone and the bib itself is red fur.
- Eyes: black socket, then two black tori on the blank eyeball (radii .112 and .062). No iris, pupil or highlight. Blink lids still close over the rings.
- Front dancer: hips, torso, shoulders and all four trouser legs use the cape cloth material with the scale print (`cyl_uv` wraps the print round each tube). White fur trims at knee and ankle. Yellow trousers and leg stripes removed. Sash is a thin gold band.
- Contract: 34,423 tris (head 17,802, body 16,621), 33 bones, 7 clips, morphs unchanged. Footprint X -1.121..1.126, height 2.318, depth Y -1.632..0.643.

Still off against the refs:
- The trousers have straight fur cuffs. The cape's scalloped wave trim with gold piping is not repeated on the legs.
- In feed and ult the jaw swings far and the plain red bib shows as a smooth panel with no fur on it.
- The beard is chunky toy clumps. The photo has long fine fur.
- The side view still shows a step between the back of the head and the cape collar.

## v10 cape hugs the body, scalloped cuffs, bib fur (2026-11-17)

Backup of v9: `_tmp_lion/lion_v9.py`.

- Cape: half width cut from about .90 to .68 and the tier flare from (.05, .075, .10) to (.03, .045, .06). Footprint X is now -0.876..0.876 (was -1.121..1.126). The collar top is raised at s .1 and .3 so the side line from head to cape is smoother.
- Cuffs: knee and ankle trims are scalloped fur rings (3 waves) with a gold piping ring above each.
- Bib: two rows of static fur clumps (`bibfur`, weighted like the bib). They show when the jaw and beard swing open in feed, ult and attack. The gold sash is removed, which was the pale band in ult.
- Beard: 33 clumps (was 25), narrower (.088) and longer (.32 and .36), rows start at z 1.36 and 1.20 (was 1.42 and 1.25).
- Contract: 34,469 tris (head 17,792, body 16,677), 33 bones, 7 clips, morphs unchanged. Height 2.318, depth Y -1.632..0.643.

Still off:
- Cuff rings are low poly (4 sided) and look a bit angular up close.
- In ult a few beard clump tips poke through the top of the lower jaw roll.
- In run the front knee passes through the beard tips, and a rear shoe shows under the hem on the lift.
- Beard and bib fur are still chunky clumps next to the long fine fur in the photo.

## v11 no beard, cape cloth round the front (2026-11-17)

Backup of v10: `_tmp_lion/lion_v10.py`. Log: `_tmp_lion/run48.log`. Shots: r15_*.

- Removed every j_beard clump and the bib fur clumps.
- The front is now cape cloth. `bib` is a flared skirt in the scale print with the scalloped white fur edge and gold piping. It runs from the hips (z .88) up to z 1.16, where it closes onto the torso cloth. It is weighted like the torso (hips, spine, chest).
- An apron reaching up to the jaw (z 1.38) was tried first (run43 to run45). The open jaw swings down through that space, so the cloth showed inside the mouth in ult and attack. Hanging it from the jaw bone did not help.
- To keep the mouth clean the chest moved back: torso centre y .06 to -.04 and rz .30 to .26, shoulders y -.06 to -.10, f_hips (0, .20, .89) radii (.44, .24, .14).
- Clip changes for jaw clearance. attack: jaw peak 40 to 37 degrees, head tips up 1.6 x lean on the rear back. feed: head +14 (was -10), jaw 30 (was 44). The body still bows.
- Leg cuff sweeps: seg 4 to 6, gold 3 to 4.
- New check: `blender -b -P lion_poke_check.py -- ../../../assets/heroes/lion.glb` counts body verts sitting above the jaw sheet or lip for every clip frame and face key. v11 prints POKE_TOTAL 0. Run45 printed several thousand.
- Contract: 34,155 tris (body 17,353, head 16,802), 33 bones, same 7 clips and frame counts, same morphs, X -0.876..0.876, height 2.318, depth -1.632..0.643.

Still off:
- The front cloth is a low skirt. Between it and the jaw the chest is the narrow torso shape in the same print, mostly in shadow. From the side there is open space under the jaw in front of the cape edge.
- The scale print pinches toward the top centre of the front skirt.
- The skirt hem corners show as small white tips beside the front legs in the front view.
- Feed and attack poses differ a little from v10 (see above). Check them in game.
- Tri count is the same as v10, not lower.

## v12 one gown round the front, trunk under it (2026-11-17)
- The v11 bib skirt, its trim ring and the set-back torso tube are gone. The cape itself now carries on round the front performer (`gown` in build_cloth, `gown_pt`). Its end columns sit on the cape front edge, rows match the lowest tier, the hem roll, gold strip and fringe run as one closed loop at the cape hem height. The top tucks under the jaw and climbs behind the jaw corners.
- Print: u repeat is rounded to a whole count from hem to hem (`TU`), so the gown matches both cape sides and mirrors at the front centre.
- Under the gown: hips, chest, shoulders and short sleeves going up into the jaw (`torso`, `shoulders`, `arm`). Hidden in normal views.
- Jaw clearance by deform, no jaw swing cut. `front_w`: the gown top and the trunk top are skinned to `prop`, the hem to hips and thighs (skirt swing in run). The body mesh also gets the head's key names (blink, mouth_open, smile, angry, grin, ult) holding the same jaw swing for prop-weighted verts. chope.html already drives those keys on any mesh that has `blink`, so no game change is needed.
- lion_poke_check.py now sets same-named body keys too. Result POKE_TOTAL 0.
- Contract (run54): 33,769 tris, 33 bones, 7 clips, footprint unchanged (X -0.875..0.873, height 2.318, depth -1.632..0.643), glb 1741 KB (was 1667). Body morphs are now belly plus the six face key names.
- Backup of v11: _tmp_lion/lion_v11.py.
