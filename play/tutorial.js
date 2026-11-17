// Lunch Liao tutorial. Loaded after the game module. It talks to the game only through window.__tut (the hook is in TUTORIAL.md).
// It runs a real match on the wet market with the bots swapped for range dummies, then polls game state once a frame.
(()=>{'use strict';
const LS='chope-tut',$=s=>document.querySelector(s),clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const load=()=>{try{return JSON.parse(localStorage.getItem(LS))||{}}catch(e){return{}}},save=o=>{try{localStorage.setItem(LS,JSON.stringify(o))}catch(e){}};
let G=null,mem=load(),R=null,ui=null,pickHk='nsboy',raf=0;
const MAPID='wetmarket',EASY='nsboy';
// wet market spots (metres). The west plaza is the classroom, table A is the objective.
const P0=[-36,11.5],GO=[-32,11.5],E_HOME=[-27,10.6],A_HOME=[-32.5,15.5],TIN=[-14.65,5.5],TIN_ROUTE=[[-19,10.5],[-19,5.8],TIN];
const CHEER=['Steady!','Shiok!','Nice one!','Can lah!','Solid!','Power!','Swee!'];

/* ---------- style ---------- */
const CSS=`
#tutBtn{grid-column:1/-1;max-width:none!important;display:flex;align-items:center;justify-content:center;gap:8px}
#tutBtn i{font-style:normal;font-size:11px;background:var(--kaya);color:var(--ink);border-radius:999px;padding:2px 8px;box-shadow:inset 0 0 0 2px var(--ink)}
#tutOffer{position:fixed;left:36px;bottom:250px;z-index:6;width:min(400px,calc(100vw - 72px));background:var(--tissue);color:var(--ink);border-radius:14px;box-shadow:inset 0 0 0 2px var(--ink),0 5px 0 var(--ink);padding:10px 12px;font-family:var(--ui);font-weight:700;font-size:16px;line-height:1.25}
#tutOffer b{font-family:var(--slab);font-weight:400;font-size:17px;display:block;margin-bottom:2px}
#tutOffer div{display:flex;gap:8px;margin-top:8px}
#tutOffer button,.tutBtn{font-family:var(--ui);font-weight:800;font-size:14px;letter-spacing:.06em;text-transform:uppercase;border-radius:10px;padding:8px 14px;background:var(--kaya);color:var(--ink);box-shadow:inset 0 0 0 2px var(--ink)}
#tutOffer button+button,.tutBtn.alt{background:transparent}
.tutOv{position:fixed;inset:0;z-index:30;display:grid;place-items:center;background:rgba(28,21,18,.82);padding:20px;overflow:auto;font-family:var(--ui);color:var(--ink)}
.tutOv[hidden]{display:none}
.tutCard{background:var(--enamel);border-radius:22px;box-shadow:inset 0 0 0 3px var(--ink),0 9px 0 var(--ink);padding:22px 26px;max-width:min(940px,96vw);width:100%;box-sizing:border-box}
.tutCard h2{font-family:var(--slab);font-weight:400;font-size:clamp(26px,3.4vw,42px);margin:0 0 4px;color:var(--kopi)}
.tutCard>p{font-size:19px;font-weight:600;margin:0 0 14px;line-height:1.3}
#tutHeroes{display:grid;grid-template-columns:repeat(auto-fill,minmax(118px,1fr));gap:9px}
#tutHeroes button{background:var(--tissue);border-radius:14px;box-shadow:inset 0 0 0 2px var(--ink);padding:6px 6px 8px;display:flex;flex-direction:column;align-items:center;gap:2px;font-family:var(--ui);color:var(--ink);position:relative}
#tutHeroes button img{width:72px;height:72px;object-fit:cover;border-radius:10px}
#tutHeroes button b{font-family:var(--slab);font-weight:400;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}
#tutHeroes button small{font-size:13px;font-weight:700;opacity:.7;text-transform:uppercase;letter-spacing:.05em}
#tutHeroes button em{position:absolute;top:-6px;right:-4px;font-style:normal;font-weight:800;font-size:11px;letter-spacing:.05em;text-transform:uppercase;background:var(--tile,#1d6f6a);color:var(--tissue);border-radius:999px;padding:2px 7px}
#tutHeroes button.sel{background:var(--kaya);box-shadow:inset 0 0 0 3px var(--ink),0 4px 0 var(--ink);transform:translateY(-2px)}
#tutHeroes button:focus-visible,.tutBtn:focus-visible{outline:3px solid var(--tile,#1d6f6a);outline-offset:2px}
.tutRow{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px;align-items:center}
.tutRow .big{font-family:var(--slab);font-size:22px;text-transform:none;letter-spacing:0;padding:12px 26px;border-radius:14px;box-shadow:inset 0 0 0 3px var(--ink),0 5px 0 var(--ink)}
.tutRow span{font-size:16px;font-weight:600;opacity:.75}
#tutEnd ul{margin:0 0 4px;padding:0;list-style:none;display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:4px 18px;font-size:17px;font-weight:600}
#tutEnd li::before{content:"";display:inline-block;width:.5em;height:.9em;border:solid var(--tile,#1d6f6a);border-width:0 3px 3px 0;transform:rotate(45deg);margin:0 10px 0 4px}
#tutEnd li kbd,#tutPanel kbd{font-family:var(--slab);font-size:.82em;background:var(--ink);color:var(--enamel);border-radius:5px;padding:1px 7px;box-shadow:none;white-space:nowrap}
#tutUI{position:fixed;inset:0;z-index:9;pointer-events:none;font-family:var(--ui);color:var(--ink)}
#tutUI[hidden]{display:none}
#tutPanel{position:absolute;z-index:2;left:14px;top:clamp(120px,19vh,190px);width:min(350px,30vw);background:var(--enamel);border-radius:16px;box-shadow:inset 0 0 0 3px var(--ink),0 6px 0 var(--ink);padding:10px 14px 9px}
#tutPanel .th{display:flex;align-items:baseline;gap:8px;font-weight:800;font-size:13px;letter-spacing:.08em;text-transform:uppercase}
#tutPanel .th b{background:var(--ink);color:var(--kaya);border-radius:6px;padding:1px 7px}
#tutPanel .th .n{margin-left:auto;font-family:var(--slab);font-weight:400;letter-spacing:0}
#tutPanel .bar{height:7px;border-radius:99px;background:rgba(28,21,18,.16);margin:6px 0 8px;overflow:hidden}
#tutPanel .bar i{display:block;height:100%;width:0;background:var(--tile,#1d6f6a);border-radius:99px;transition:width .35s}
#tutPanel h3{font-family:var(--slab);font-weight:400;font-size:clamp(20px,1.75vw,27px);line-height:1.08;margin:0 0 5px;color:var(--kopi)}
#tutPanel .tx{font-size:clamp(16px,1.25vw,19px);font-weight:600;line-height:1.28;margin:0}
#tutPanel ul{list-style:none;margin:7px 0 0;padding:0;display:grid;gap:4px}
#tutPanel li{display:flex;align-items:center;gap:8px;font-size:clamp(15px,1.15vw,18px);font-weight:700;line-height:1.15}
#tutPanel li::before{content:"";flex:none;width:17px;height:17px;border-radius:6px;box-shadow:inset 0 0 0 2px var(--ink);background:var(--tissue)}
#tutPanel li.ok{opacity:.6}
#tutPanel li.ok::before{background:var(--tile,#1d6f6a) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Cpath d='M3 8.5l3.2 3.2L13 4.8' fill='none' stroke='%23FBF8F0' stroke-width='2.6' stroke-linecap='round'/%3E%3C/svg%3E") center/13px no-repeat;animation:tutPop .3s}
#tutPanel .hint{font-size:clamp(14px,1.05vw,16px);font-weight:600;line-height:1.25;margin:7px 0 0;padding:6px 9px;border-radius:9px;background:rgba(227,169,43,.3);color:var(--ink);display:block}
#tutPanel .hint:empty{display:none}
#tutPanel .ft{display:flex;justify-content:space-between;gap:8px;margin-top:8px;padding-top:6px;border-top:2px dashed rgba(28,21,18,.25);font-size:13px;font-weight:700;opacity:.85}
#tutPanel.done{animation:tutBump .35s}
#tutOk{position:absolute;left:50%;top:27%;transform:translate(-50%,-50%);font-family:var(--slab);font-size:clamp(34px,4.6vw,62px);color:var(--kaya);-webkit-text-stroke:2px var(--kopi);paint-order:stroke fill;text-shadow:0 4px 0 var(--kopi);white-space:nowrap;opacity:0;display:flex;align-items:center;gap:14px}
#tutOk svg{width:.9em;height:.9em;background:var(--tile,#1d6f6a);border-radius:50%;box-shadow:0 0 0 3px var(--kopi)}
#tutOk.on{animation:tutOk 1s ease-out}
#tutOk small{position:absolute;top:100%;left:50%;transform:translateX(-50%);margin-top:6px;font-family:var(--ui);font-weight:700;font-size:17px;-webkit-text-stroke:0;text-shadow:none;color:var(--tissue);background:rgba(28,21,18,.8);padding:5px 14px;border-radius:12px;white-space:normal;width:max-content;max-width:min(620px,70vw);text-align:center;line-height:1.25}
#tutOk small:empty{display:none}
#tutMk{position:absolute;left:0;top:0;width:0;height:0;display:none}
#tutMk i{position:absolute;left:-13px;top:-34px;width:26px;height:26px;background:var(--kaya);box-shadow:inset 0 0 0 3px var(--ink);transform:rotate(45deg);border-radius:5px;animation:tutBob .8s ease-in-out infinite alternate}
#tutMk.edge i{top:-13px;border-radius:50% 50% 50% 4px;animation:none}
#tutMk span{position:absolute;left:50%;top:6px;transform:translateX(-50%);white-space:nowrap;font-weight:800;font-size:14px;background:var(--ink);color:var(--tissue);border-radius:8px;padding:2px 8px}
#tutMk.edge span{top:18px}
#tutHl{position:absolute;display:none;border-radius:12px;box-shadow:0 0 0 4px var(--kaya),0 0 0 7px var(--ink);animation:tutPulse .7s ease-in-out infinite alternate}
#tutHl span{position:absolute;left:50%;transform:translateX(-50%);white-space:nowrap;font-weight:800;font-size:15px;background:var(--kaya);color:var(--ink);border-radius:9px;padding:3px 10px;box-shadow:inset 0 0 0 2px var(--ink)}
#tutHl span.up{bottom:calc(100% + 14px)}#tutHl span.dn{top:calc(100% + 14px)}
#tutHl span::after{content:"";position:absolute;left:50%;margin-left:-7px;border:7px solid transparent}
#tutHl span.up::after{top:100%;border-top-color:var(--ink)}#tutHl span.dn::after{bottom:100%;border-bottom-color:var(--ink)}
#tutRestart[hidden]{display:none}
@keyframes tutPop{0%{transform:scale(.3)}70%{transform:scale(1.35)}100%{transform:scale(1)}}
@keyframes tutBump{0%{transform:scale(1)}40%{transform:scale(1.04)}100%{transform:scale(1)}}
@keyframes tutOk{0%{opacity:0;transform:translate(-50%,-50%) scale(.5)}14%{opacity:1;transform:translate(-50%,-50%) scale(1.12)}24%{transform:translate(-50%,-50%) scale(1)}80%{opacity:1}100%{opacity:0;transform:translate(-50%,-62%) scale(1)}}
@keyframes tutBob{to{transform:translateY(-9px) rotate(45deg)}}
@keyframes tutPulse{to{box-shadow:0 0 0 7px var(--kaya),0 0 0 10px var(--ink)}}
@media (prefers-reduced-motion:reduce){#tutMk i,#tutHl,#tutPanel.done,#tutPanel li.ok::before{animation:none}#tutOk.on{animation-duration:.01s;animation-fill-mode:none}}
`;
const TICK='<svg viewBox="0 0 16 16"><path d="M3.5 8.5l3 3 6-6.4" fill="none" stroke="#FBF8F0" stroke-width="2.4" stroke-linecap="round"/></svg>';

/* ---------- small helpers ---------- */
const def=id=>G.BINDS.find(b=>b[0]===id)[2],held=id=>!!G.keys[def(id)];
const K=id=>`<kbd>${G.kn(G.bindOf(id))}</kbd>`,LMB='<kbd>Left click</kbd>';
const P=()=>G.player,zoneA=()=>G.zones.find(z=>z.id==='A')||G.zones[0];
const dist=(e,x,z)=>Math.hypot(e.pos.x-x,e.pos.z-z);
const tin=()=>G.pickups.reduce((a,k)=>!a||Math.hypot(k.p.x-TIN[0],k.p.z-TIN[1])<Math.hypot(a.p.x-TIN[0],a.p.z-TIN[1])?k:a,null);
const wet=()=>G.HAZ.filter(h=>h.k==='wet').sort((a,b)=>Math.hypot(a.x-E_HOME[0],a.z-E_HOME[1])-Math.hypot(b.x-E_HOME[0],b.z-E_HOME[1]))[0];
const canHead=hk=>!!G.BND[hk]||((G.HEROES[hk].shot||{}).head||1)>1;
function skipCode(){const used=new Set(G.BINDS.map(b=>G.bindOf(b[0])));return['Enter','Backslash','F2','F4'].find(c=>!used.has(c))||'F4'}
function addDummy(hk,team,name,at){const e=G.makeEnt(hk,team,false,name);e.dummy=true;e.home=at;e.post={x:at[0],z:at[1]};e.pos.set(at[0],0,at[1]);e.spInv=0;G.ents.push(e);return e}
function drop(e){const i=G.ents.indexOf(e);if(i>=0){G.ents.splice(i,1);G.freeEnt(e)}}
function park(e,at){e.post={x:at[0],z:at[1]};if(e.alive)e.pos.set(at[0],0,at[1])}

/* ---------- the course ---------- */
// A step: {id, sec, h, tx, tasks:[[label, test(d,dt)]], hint, live, mk, hl, read, enter, exit}. Tasks latch. A step with no tasks is a reading step.
function course(hk){
  const H=G.HEROES[hk],kit=H.kit,row=k=>kit.find(r=>r&&r[0]===k),band=(G.MAG||G.BND)[hk],S=[]; // band: any hero with a mag
  const add=s=>S.push(s);
  add({id:'look',sec:'Moving',h:'Look around',tx:'Move the mouse to look. Have a look at the market.',
    hint:'If the cursor is free, click the game once. No mouse capture? Hold the left button and drag.',
    enter(d){d.y=P().yaw;d.p=P().pitch;d.a=0},
    tasks:[['Look left and right',d=>{const p=P();d.a+=Math.abs(p.yaw-d.y)+Math.abs(p.pitch-d.p);d.y=p.yaw;d.p=p.pitch;return d.a>1.6}]]});
  add({id:'move',sec:'Moving',h:'Walk',tx:'Four keys move you. Try each one.',
    tasks:[['fwd','Forward'],['left','Left'],['back','Back'],['right','Right']].map(([id,n])=>[`${n} ${K(id)}`,(d,dt)=>{if(held(id)&&Math.hypot(P().vel.x,P().vel.z)>1)d[id]=(d[id]||0)+dt;return d[id]>.25}])});
  add({id:'jump',sec:'Moving',h:'Jump',tx:`Press ${K('jump')} to jump. Good for hopping on tables and crates.`,
    tasks:[['Jump once',()=>!P().onGround&&P().vel.y>1]]});
  add({id:'crouch',sec:'Moving',h:'Crouch',tx:`Stand still and hold ${K('crouch')}. You duck behind low cover and get harder to hit.`,
    tasks:[['Hold a crouch for a moment',(d,dt)=>{d.t=P().stance==='crouch'?(d.t||0)+dt:0;return d.t>.6}]]});
  add({id:'slide',sec:'Moving',h:'Slide (this is your sprint)',tx:`There is no sprint key. You always run at full speed. The slide is your burst. Run forward with ${K('fwd')}, then tap ${K('crouch')}.`,
    hint:`Your hero slides as: ${G.SL[hk]&&G.SL[hk].name||'a slide'}. You need to be running first.`,
    enter(d){d.n=0;d.was=!!P().sl},
    tasks:[['Slide while running',d=>{const on=!!P().sl;if(on&&!d.was)d.n++;d.was=on;return d.n>=1}]]});
  add({id:'slidejump',sec:'Moving',h:'Slide, then jump',tx:`Jump out of a slide to keep the speed. Run, hold ${K('crouch')}, then hit ${K('jump')} while you are still sliding.`,
    enter(d){d.was=!!P().sl;P().slEnd=null},
    tasks:[['Start a slide',d=>{const on=!!P().sl;if(on&&!d.was){d.s=1;P().slEnd=null}d.was=on;return!!d.s}],['Jump before it ends',d=>!!d.s&&P().slEnd==='jump']]});
  add({id:'goto',sec:'Moving',h:'Follow the marker',tx:'The yellow marker shows where to go. When it sits at the edge of the screen, turn that way.',
    mk:()=>({p:GO,l:'Go here'}),tasks:[['Walk to the marker',()=>dist(P(),GO[0],GO[1])<2]]});

  const foe=()=>R.foe,tgt=l=>()=>({e:foe(),l});
  add({id:'shoot',sec:'Fighting',h:kit[0][1],tx:`${LMB} to attack. ${kit[0][2]}`,hint:'The dummy does not fight back. Take your time.',
    enter(d){d.n=R.hits;foe().hp=foe().maxHp},mk:tgt('Hit me'),tasks:[['Hit the dummy 3 times',d=>R.hits-d.n>=3]]});
  if(canHead(hk))add({id:'head',sec:'Fighting',h:'Headshots',tx:'Aim at the head. Headshots hit a lot harder, and you hear a different sound.',hint:kit[0][3]||'',
    enter(d){d.n=R.heads;foe().hp=foe().maxHp},mk:tgt('Aim for the head'),tasks:[['Land a headshot',d=>R.heads>d.n]]});
  add({id:'ko',sec:'Fighting',h:'Knock it out',tx:'The dummy is nearly done. Finish it. Then look top right: the feed shows who knocked out who.',
    enter(d){d.n=P().stats.elims;const f=foe();if(f.alive)f.hp=Math.min(f.hp,Math.max(60,f.maxHp*.2))},mk:tgt('Finish it'),hl:()=>R.okT>0?['.chud .feed','Kill feed','dn']:null,
    tasks:[['Knock out the dummy',d=>P().stats.elims>d.n]]});
  if(band)add({id:'reload',sec:'Fighting',h:'Reload',tx:`Your ammo counter sits bottom right${band&&(band.mag>10||band.tank)?'':', one icon per round'}. You are nearly out. Press ${K('extra')} to reload. It also reloads by itself when empty.`,hint:'You cannot fire until the counter is full again, so pick a safe moment.',hl:()=>['.chud .ammo','Ammo','up'],
    enter(){P().wpn.mag=Math.min(P().wpn.mag,2)},
    tasks:[[`Press ${K('extra')} to reload`,d=>{if(P().wpn.rlT>=0)d.s=1;return!!d.s}],['Wait for the full reload',d=>!!d.s&&!(P().wpn.rlT>=0)&&P().wpn.mag>=band.mag]]});
  add({id:'melee',sec:'Fighting',h:'Quick melee',tx:`Press ${K('melee')} for a fast whack. Handy when someone is right in your face${band?', or when you are reloading':''}.`,
    enter(d){d.n=P().casts.q},mk:tgt('Whack me'),tasks:[['Quick melee once',d=>P().casts.q>d.n]]});

  for(const n of[1,2,3]){const r=row(String(n));if(!r)continue;const pas=/^Passive/i.test(r[2]),hold=/^Hold/i.test(r[2]),id='a'+['','1','2','3'][n];
    add({id:'ab'+n,sec:'Abilities',h:`${n}. ${r[1]}`,tx:pas?r[2]:`Press ${K(id)}. ${r[2]}`,
      hint:pas?'Nothing to press for this one. It is always on.':hold?'This one is hold, aim, release.':'Abilities have cooldowns. Watch the slot fill back up.',
      hl:()=>['#ab'+n,r[1],'up'],mk:()=>R.ally&&/ally|allies|teammate/i.test(r[2])?{e:R.ally,l:'Hurt teammate'}:{e:foe(),l:'Target'},
      enter(d){const p=P();d.n=p.casts[n];p.cd1=p.cd2=p.cd3=0;if(R.ally)R.ally.hp=R.ally.maxHp*.45;if(foe().alive)foe().hp=foe().maxHp;p.hp=Math.min(p.hp,p.maxHp*.7)},
      // ponytail: some abilities refuse without a target or height (plunge, ally heals). Pressing the key and 5 s of trying also passes
      tasks:pas?[]:[[`Use ${r[1]}`,(d,dt)=>{if(held(id))d.k=1;if(d.k)d.t=(d.t||0)+dt;return P().casts[n]>d.n||d.t>5}]],
      said:r[3]||''})}
  const u=row('4');
  add({id:'ultc',sec:'Ultimate',h:'Charge your ult',tx:'Your ult charges when you deal damage or heal. Hit the dummy until the big dial is full.',hint:'It charges extra fast here. In a match it takes a good fight or two.',
    hl:()=>['#ab4','Ult charge','up'],mk:tgt('Hit me'),enter(){foe().hp=foe().maxHp},live:()=>`Ult: ${Math.round(100*P().ult/P().H.ultCost)}%`,
    tasks:[['Fill the ult dial',()=>P().ult>=P().H.ultCost]]});
  add({id:'ult',sec:'Ultimate',h:`${u[1]}!`,tx:`Ult ready. Press ${K('ult')}. ${u[2]}`,hl:()=>['#ab4',u[1],'up'],mk:tgt('Target'),
    enter(d){const p=P();G.gainUlt(p,1e4);d.n=p.casts[4];foe().hp=foe().maxHp},tasks:[[`Use ${u[1]}`,d=>P().casts[4]>d.n]],said:u[3]||''});

  add({id:'wet',sec:'The floor',h:'Wet floor',tx:'See the shiny patch with the yellow sign? Wet floor has less grip. You skid, and slides go further. Run across it.',
    mk:()=>{const w=wet();return w?{p:[w.x,w.z],l:'Wet floor'}:null},
    tasks:[['Cross the wet patch',()=>{const w=wet(),p=P();return!w||Math.abs(p.pos.x-w.x)<w.w/2&&Math.abs(p.pos.z-w.z)<w.d/2}]]});

  add({id:'hud',sec:'Tables',h:'Score and tables',tx:'Top middle is the score, Blue (you) against Red. The three pips are tables A, B and C. A pip turns your colour when your team holds that table.',
    hl:()=>['.chud .score','Score and table pips','dn'],read:1});
  add({id:'cap',sec:'Tables',h:'Chope table A',tx:'Stand inside the glowing ring to chope the table. Stay in until the ring turns blue.',
    mk:()=>({p:[zoneA().p.x,zoneA().p.z],l:'Table A'}),hl:()=>['.chud .capture','Capture progress','up'],
    enter(){const z=zoneA();z.prog=0;z.owner=0;R.lockA=false},live:()=>`Table A: ${Math.max(0,Math.round(zoneA().prog))}%`,
    tasks:[['Step into the ring',()=>dist(P(),zoneA().p.x,zoneA().p.z)<zoneA().r],['Hold it until it is yours',()=>zoneA().owner===1]]});
  add({id:'points',sec:'Tables',h:'Tables make points',tx:'Every table your team holds adds points each second. More tables, faster points. First team to 150 wins, or the higher score when the 5 minute timer runs out.',
    hint:'The timer is frozen for this tutorial.',hl:()=>['.chud .timer','Match timer','dn'],live:()=>`Blue ${Math.floor(G.score[1])} : ${Math.floor(G.score[2])} Red`,read:1});
  add({id:'contest',sec:'Tables',h:'Contested!',tx:'Aiyo, Red took table A back and left someone on it. While both teams stand on a table the ring goes yellow and nobody gains. Clear them off.',
    mk:()=>foe().alive&&foe().post.x!==E_HOME[0]?{e:foe(),l:'On your table'}:{p:[zoneA().p.x,zoneA().p.z],l:'Table A'},
    enter(d){const z=zoneA(),f=foe();R.lockA=false;z.prog=-55;z.owner=2;d.n=f.stats.deaths;f.hp=Math.min(f.maxHp,170);park(f,[z.p.x+.8,z.p.z-.4])},
    exit(){park(foe(),E_HOME)},live:()=>zoneA().contested?'Contested. Nobody gains.':`Table A: ${Math.round(zoneA().prog)}%`,
    tasks:[['Step on the table with Red there',d=>zoneA().contested||foe().stats.deaths>d.n],['Knock out the enemy',d=>{if(foe().stats.deaths>d.n&&foe().post.x!==E_HOME[0])park(foe(),E_HOME);return foe().stats.deaths>d.n}],['Chope table A back',()=>zoneA().owner===1]]});

  add({id:'heal',sec:'Staying alive',h:'Find a pickup',tx:'You took a whack. Bottom left is your HP. Healing pickups sit around the map with a light beam on them. Walk over one to heal. They come back after 15 seconds.',
    hl:()=>['.chud .vitals .hpwrap','Your HP','up'],
    mk(d){const p=P();while(d.i<TIN_ROUTE.length-1&&dist(p,TIN_ROUTE[d.i][0],TIN_ROUTE[d.i][1])<2.2)d.i++;return{p:TIN_ROUTE[d.i],l:d.i<TIN_ROUTE.length-1?'This way':'Pickup'}},
    enter(d){const p=P(),k=tin();d.i=0;p.hp=Math.round(p.maxHp*.35);G.SFX.hurt();if(k)k.t=0;d.h=p.hp},
    tasks:[['Grab the pickup',d=>{const k=tin();return!k||k.t>0||P().hp>=P().maxHp}]]});
  add({id:'status',sec:'Staying alive',h:'Status effects',tx:'You just got slowed. Effects on you show up above your HP: slow, stink, stun, buffs. Most wear off in seconds. A teh tarik cup pickup washes off slow and stink.',
    hl:()=>['.chud .status','Effects on you','up'],enter(){G.applyStatus(P(),'slow',{m:.45,t:4.5})},
    tasks:[['Feel the slow, then wait it out',(d,dt)=>{d.t=(d.t||0)+dt;return d.t>1&&!P().st.slow.length}]]});
  add({id:'board',sec:'Staying alive',h:'Scoreboard',tx:'Hold <kbd>Tab</kbd> to see both teams, who is alive and whose ult is ready.',
    tasks:[['Hold Tab for a look',(d,dt)=>{if(R.tab)d.t=(d.t||0)+dt;return d.t>.5}]]});

  add({id:'fight',sec:'Showtime',h:'Practice round',tx:'Real thing now, small size. 3 against 3 with easy bots. Chope tables, fight on them, use everything. First team to 25 points.',
    hint:`Knocked out? You respawn in a few seconds. ${K('pause')} pauses.`,live:()=>`Blue ${Math.floor(G.score[1])} : ${Math.floor(G.score[2])} Red`,
    mk:()=>{const p=P(),z=G.zones.filter(z=>z.owner!==1).sort((a,b)=>dist(p,a.p.x,a.p.z)-dist(p,b.p.x,b.p.z))[0];return z?{p:[z.p.x,z.p.z],l:'Table '+z.id}:null},
    enter(){startFight()},tasks:[['First to 25 points',()=>G.score[1]>=25||G.score[2]>=25]]});
  return S;
}
function startFight(){
  for(const e of[R.foe,R.ally])if(e)drop(e);R.foe=R.ally=null;R.lockA=false;R.fight=true;
  const pool=Object.keys(G.HEROES).filter(h=>h!==R.hk),pick=(want,n)=>[...want.filter(h=>pool.includes(h)),...pool].filter((h,i,a)=>a.indexOf(h)===i).slice(0,n);
  const al=pick(['tarik','gym'],2),fo=pick(['uncle','rascal','dj'],3);
  al.forEach((h,i)=>G.ents.push(G.makeEnt(h,1,false,['Mei Ling','Ah Seng'][i])));fo.forEach((h,i)=>G.ents.push(G.makeEnt(h,2,false,['Beng','Lian','Kor Kor'][i])));
  G.AU.loadHeroes(G.ents.map(e=>e.hk));G.botSkill[2]=.7;G.score[1]=G.score[2]=0;G.tbBuild();
}

/* ---------- run control ---------- */
function start(hk){
  if(R||!G||G.state==='playing')return;
  const pr=G.profile;
  R={hk,i:-1,cur:null,d:{},okT:0,skips:0,hits:0,heads:0,tab:0,lockA:true,fight:false,t0:performance.now(),lt:performance.now(),skip:skipCode(),
     keep:{hero:pr.hero,map:pr.map,keys14:pr.keys14,onDamage:G.onDamage,bots:G.botSkill[2]}};
  pr.hero=hk;pr.keys14=true;G.RANGE=false;G.comp=null; // keys14: stops startMatch saving the profile with the tutorial hero in it
  G.startMatch(MAPID);
  if(G.state!=='playing'){restore();R=null;return}
  G.cdT=0;
  for(const e of G.ents.filter(e=>!e.isPlayer))G.freeEnt(e);G.ents.length=1;
  const p=P();p.pos.set(P0[0],0,P0[1]);p.yaw=-Math.PI/2;p.pitch=0;p.spInv=0;
  R.foe=addDummy(hk==='gym'?'ahma':'gym',2,'Dummy',E_HOME);R.ally=addDummy(hk==='tarik'?'dj':'tarik',1,'Kaki',A_HOME);
  G.AU.loadHeroes(G.ents.map(e=>e.hk));G.tbBuild();
  G.onDamage=(t,tot,src,opt)=>{if(!R||src!==P()||t.team===src.team)return;R.hits++;if(opt&&opt.head)R.heads++;if(R.cur&&R.cur.id==='ultc')G.gainUlt(src,src.H.ultCost*.22)};
  R.steps=course(hk);ui.root.hidden=false;$('#tutRestart').hidden=false;
  go(0);raf=requestAnimationFrame(tick);
}
function restore(){if(!R||!R.keep)return;const k=R.keep,pr=G.profile;R.keep=null;pr.hero=k.hero;pr.map=k.map;pr.keys14=k.keys14;G.onDamage=k.onDamage;G.botSkill[2]=k.bots}
// the game has left the match (quit button, or our own exit). Put everything back.
function teardown(){
  if(!R)return;cancelAnimationFrame(raf);const map=R.keep?R.keep.map:G.profile.map;restore();R=null;
  ui.root.hidden=true;$('#tutRestart').hidden=true;G.saveProfile();
  if(G.map&&G.map.id!==map&&G.state!=='playing')G.applyMap(map);
}
function quit(){restore();$('#quitBtn').click();if(document.pointerLockElement)document.exitPointerLock();teardown()}
function go(i){
  const s0=R.cur;if(s0&&s0.exit)s0.exit(R.d);
  if(i>=R.steps.length)return finish();
  R.i=i;R.cur=R.steps[i];R.d={};R.okT=0;R.ok=[];R.liveS=null;
  if(R.cur.enter)R.cur.enter(R.d);
  draw();
}
function draw(){
  const s=R.cur,n=R.steps.length,read=!s.tasks||!s.tasks.length,key=`<kbd>${G.kn(R.skip)}</kbd>`;
  ui.sec.textContent=s.sec;ui.n.textContent=`${R.i+1} / ${n}`;ui.bar.style.width=(100*R.i/n)+'%';
  ui.h.textContent=s.h;ui.tx.innerHTML=s.tx;ui.hint.innerHTML=s.hint||'';
  ui.tk.innerHTML=(s.tasks||[]).map(t=>`<li>${t[0]}</li>`).join('');
  ui.ft.innerHTML=`<span>${key} ${read?'got it, next':'skip this step'}</span><span>${K('pause')} pause, restart, quit</span>`;
}
function cheer(s,skipped){
  R.okT=skipped?.01:s.said?2.4:1.05;if(skipped)return;
  G.SFX.chal();ui.ok.innerHTML=TICK+CHEER[R.i%CHEER.length]+`<small>${s.said?'What it did: '+s.said:''}</small>`;ui.ok.style.animationDuration=s.said?'2.4s':'';
  ui.ok.classList.remove('on');void ui.ok.offsetWidth;ui.ok.classList.add('on');ui.panel.classList.remove('done');void ui.panel.offsetWidth;ui.panel.classList.add('done');
  const p=P();try{G.confetti(p.pos.clone().setY(p.pos.y+2.4),0xE3A92B,18);G.ringFx(p.pos,0xE3A92B,2.2,.5)}catch(e){}
}
function skip(){if(!R||R.okT>0||G.paused)return;const s=R.cur,read=!s.tasks||!s.tasks.length;if(!read)R.skips++;G.SFX.point();cheer(s,true)}
function finish(){
  const secs=Math.round((performance.now()-R.t0)/1000),won=G.score[1]>=G.score[2],skips=R.skips,hk=R.hk,fought=R.fight;
  mem.done=1;mem.n=(mem.n||0)+1;save(mem);quit();G.SFX.win();
  const k=id=>K(id);
  $('#tutEnd .sum').textContent=`${fought?(won?'You won the practice round. ':'Red took the practice round. No shame, they camp one. '):''}Done in ${Math.floor(secs/60)} min ${secs%60} s${skips?`, ${skips} step${skips>1?'s':''} skipped`:', nothing skipped'}.`;
  $('#tutEnd ul').innerHTML=[`Slide: run, then ${k('crouch')}. Jump out to keep speed`,`Abilities ${k('a1')} ${k('a2')} ${k('a3')}, ult ${k('ult')}`,`Quick melee ${k('melee')}, crouch ${k('crouch')}, jump ${k('jump')}`,
    'Stand in a ring to chope a table','Both teams on a table: nobody gains','More tables, faster points. First to 150','Pickups heal. Teh tarik cups also cleanse','Hold <kbd>Tab</kbd> for the scoreboard',
    'Pick a different hero on the hero screen before each match','Change keys, sensitivity and bot level in Settings'].map(t=>`<li>${t}</li>`).join('');
  $('#tutBtn').innerHTML='Tutorial';pickHk=hk;$('#tutEnd').hidden=false;$('#tutEnd .big').focus();
}

/* ---------- per frame ---------- */
const v3=()=>P().pos.clone();
function tick(now){
  if(!R)return;
  if(G.state!=='playing')return teardown();
  raf=requestAnimationFrame(tick);
  const dt=Math.min(.05,(now-R.lt)/1000);R.lt=now;
  const dead=!P().alive;ui.root.hidden=G.paused;if(G.paused)return;
  // hold the match open: frozen clock, score well under the target
  G.matchT=299;if(!R.fight)for(const t of[1,2])G.score[t]=Math.min(G.score[t],120);
  if(R.lockA){const z=zoneA();z.prog=0;z.owner=0}
  for(const e of[R.foe,R.ally])if(e){if(e.alive&&!e.wasAlive){e.pos.set(e.post.x,0,e.post.z);e.spInv=0}e.wasAlive=e.alive}
  const s=R.cur;
  if(R.okT>0){R.okT-=dt;if(R.okT<=0)return go(R.i+1)}
  else if(s.tasks&&s.tasks.length&&!dead){
    let all=true;s.tasks.forEach((t,j)=>{if(!R.ok[j]){if(t[1](R.d,dt)){R.ok[j]=1;ui.tk.children[j].classList.add('ok');if(R.ok.filter(Boolean).length<s.tasks.length)G.SFX.point()}else all=false}});
    if(all)cheer(s);
  }
  if(s.live){const l=s.live();if(l!==R.liveS){R.liveS=l;ui.hint.innerHTML=`<b>${l}</b>${s.hint?'<br>'+s.hint:''}`}}
  marker(s.mk?s.mk(R.d):null);highlight(s.hl?s.hl():null);
}
function marker(m){
  const el=ui.mk;if(!m||(m.e&&!m.e.alive)){el.style.display='none';return}
  const w=m.e?m.e.pos.clone().setY(m.e.pos.y+2.5):v3().set(m.p[0],1.4,m.p[1]),d=Math.round(Math.hypot(w.x-P().pos.x,w.z-P().pos.z));
  if(!m.e&&d<1.5){el.style.display='none';return}
  const c=w.clone().applyMatrix4(G.camera.matrixWorldInverse),n=w.project(G.camera),W=innerWidth,Hh=innerHeight;
  let x=(n.x*.5+.5)*W,y=(-n.y*.5+.5)*Hh,edge=c.z>0||Math.abs(n.x)>.92||Math.abs(n.y)>.88;
  if(edge){let dx=c.x,dy=c.z>0?-Math.abs(c.y)-1:c.y;const l=Math.hypot(dx,dy)||1;dx/=l;dy/=l;x=W/2+dx*W*.42;y=Hh/2-dy*Hh*.38;ui.mkI.style.transform=`rotate(${Math.atan2(dx,dy)*180/Math.PI+135}deg)`}else ui.mkI.style.transform='';
  el.className=edge?'edge':'';el.style.display='block';el.style.transform=`translate(${x|0}px,${y|0}px)`;ui.mkS.textContent=`${m.l} ${d} m`;
}
function highlight(h){
  const el=ui.hl,t=h&&document.querySelector(h[0]),r=t&&t.getBoundingClientRect();
  if(!r||r.width<2){el.style.display='none';return}
  el.style.cssText=`display:block;left:${r.left-6}px;top:${r.top-6}px;width:${r.width+12}px;height:${r.height+12}px`;ui.hlS.textContent=h[1];ui.hlS.className=h[2];
}

/* ---------- DOM ---------- */
function openPick(){
  $('#tutOffer')&&$('#tutOffer').remove();mem.offered=1;save(mem);
  const box=$('#tutHeroes');
  if(!box.children.length){box.innerHTML=Object.keys(G.HEROES).map(k=>{const h=G.HEROES[k];return`<button data-h="${k}" aria-label="${h.name}, ${h.role}"><img alt="" src="${G.portrait(k)||''}"><b>${h.name}</b><small>${h.role}</small>${k===EASY?'<em>Start here</em>':''}</button>`}).join('');
    box.addEventListener('click',e=>{const b=e.target.closest('button');if(b){pickHk=b.dataset.h;sel()}});box.addEventListener('dblclick',e=>{if(e.target.closest('button'))$('#tutGo').click()})}
  sel();$('#tutPick').hidden=false;$('#tutGo').focus();
}
function sel(){for(const b of $('#tutHeroes').children)b.classList.toggle('sel',b.dataset.h===pickHk);const h=G.HEROES[pickHk];$('#tutPick .who').textContent=`${h.name}: ${h.kit[0][2]}`}
function build(){
  document.head.insertAdjacentHTML('beforeend',`<style id="tutCss">${CSS}</style>`);
  $('#rangeBtn').insertAdjacentHTML('afterend',`<button class="range" id="tutBtn">Tutorial${mem.done?'':' <i>New</i>'}</button>`);
  $('#quitBtn').insertAdjacentHTML('beforebegin','<button class="ghost" id="tutRestart" hidden>Restart tutorial</button>');
  document.body.insertAdjacentHTML('beforeend',`
<div id="tutUI" hidden><div id="tutPanel" role="status" aria-live="polite"><div class="th"><b>Tutorial</b><span class="sec"></span><span class="n"></span></div><div class="bar"><i></i></div><h3></h3><p class="tx"></p><ul></ul><p class="hint"></p><div class="ft"></div></div>
<div id="tutOk"></div><div id="tutMk"><i></i><span></span></div><div id="tutHl"><span></span></div></div>
<div id="tutPick" class="tutOv" hidden role="dialog" aria-label="Tutorial hero"><div class="tutCard"><h2>Tutorial</h2><p>About 5 minutes. You learn to move, slide, fight, use your kit and chope tables, then play a small practice round. Pick who to learn with. You can redo it with anyone.</p>
<div id="tutHeroes"></div><div class="tutRow"><button class="tutBtn big" id="tutGo">Start tutorial</button><button class="tutBtn alt" id="tutBack">Back</button><span class="who"></span></div></div></div>
<div id="tutEnd" class="tutOv" hidden role="dialog" aria-label="Tutorial complete"><div class="tutCard"><h2>Tutorial done. Steady lah!</h2><p class="sum"></p><ul></ul>
<div class="tutRow"><button class="tutBtn big" data-a="play">Chope a seat</button><button class="tutBtn alt" data-a="range">Practice range</button><button class="tutBtn alt" data-a="again">Run it again</button><button class="tutBtn alt" data-a="menu">Menu</button></div></div></div>`);
  const q=s=>$('#tutPanel '+s);
  ui={root:$('#tutUI'),panel:$('#tutPanel'),sec:q('.sec'),n:q('.n'),bar:q('.bar i'),h:q('h3'),tx:q('.tx'),tk:q('ul'),hint:q('.hint'),ft:q('.ft'),ok:$('#tutOk'),mk:$('#tutMk'),mkI:$('#tutMk i'),mkS:$('#tutMk span'),hl:$('#tutHl'),hlS:$('#tutHl span')};
  $('#tutBtn').addEventListener('click',openPick);
  $('#tutGo').addEventListener('click',()=>{$('#tutPick').hidden=true;start(pickHk)});
  $('#tutBack').addEventListener('click',()=>{$('#tutPick').hidden=true;$('#tutBtn').focus()});
  $('#tutRestart').addEventListener('click',()=>{const hk=R&&R.hk;if(!hk)return;quit();start(hk)});
  $('#tutEnd').addEventListener('click',e=>{const a=e.target.dataset&&e.target.dataset.a;if(!a)return;$('#tutEnd').hidden=true;
    if(a==='play')$('#goBtn').click();else if(a==='range')$('#rangeBtn').click();else if(a==='again')openPick();else $('#tutBtn').focus()});
  // quit from the pause screen: put the real hero and map back before the game redraws its menu
  document.addEventListener('click',e=>{if(R&&e.target.closest&&e.target.closest('#quitBtn'))restore()},true);
  addEventListener('keydown',e=>{
    if(e.code==='Escape'){for(const id of['#tutPick','#tutEnd'])if(!$(id).hidden){$(id).hidden=true;e.stopPropagation();$('#tutBtn').focus()}}
    if(!R||G.paused||e.repeat)return;
    if(e.code==='Tab')R.tab=1;
    if(e.code===R.skip){e.preventDefault();skip()}
  },true);
  addEventListener('keyup',e=>{if(R&&e.code==='Tab')R.tab=0},true);
  // offer it once on a first visit. Never in test runs (?q), so other harnesses see the plain menu
  if(!mem.done&&!mem.offered&&!new URLSearchParams(location.search).has('q')&&!(G.profile.games>0)){
    $('#menu').insertAdjacentHTML('beforeend','<div id="tutOffer" role="note"><b>First time here?</b>The tutorial takes about 5 minutes and teaches moving, sliding, abilities and choping tables.<div><button data-o="1">Show me</button><button>No thanks</button></div></div>');
    $('#tutOffer').addEventListener('click',e=>{if(e.target.tagName!=='BUTTON')return;mem.offered=1;save(mem);if(e.target.dataset.o)openPick();else $('#tutOffer').remove()});
  }
}
const wait=setInterval(()=>{if(window.__tut&&window.chopeBooted&&$('#rangeBtn')){clearInterval(wait);G=window.__tut;build()}},100);
// test handle: state for the headless run in tools/tutorial_test.mjs
window.__tutorial={start:hk=>start(hk||EASY),get run(){return R},skip,quit};
})();
