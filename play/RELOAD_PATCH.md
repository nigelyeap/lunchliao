# Reload patch: ammo counter, plain reload, reload animations

This patch removes the NS Boy and Lens quick reload timing. R is now a plain reload when the mag is not full. Auto reload at empty stays. It also adds the kopi receipt ammo counter and the first person reload clips.

It has 11 hunks. Each anchor must appear exactly once in play/chope.html. The apply script below asserts that, then checks that no quick reload names are left.

Landed in play/chope.html on 2026-11-16. The backup is play/chope.html.bak_reload. The same script is saved as play/tools/reload_hunks.py.

The counter uses the class amu during an ult. The plain name ult would pick up the existing .chud .ult button rule.

## Apply

```sh
python3 play/tools/reload_hunks.py play/chope.html
```

## Hunk 1: BND drops the active reload window

Anchor:

```
// HEROES3: hold-to-charge rifles. mag, reload s, active reload window, charge s, tap damage, extra at full, shot cd, weapon name
const BND={nsboy:{mag:8,rl:1.5,ar:[.6,.8],ch:.6,t:26,f:32,cd:.45,w:'rubber band'},lens:{mag:6,rl:1.8,ar:[.9,1.1],ch:1.2,t:30,f:50,cd:.5,w:'telephoto shot'}};
```

Replacement:

```
// HEROES3: hold-to-charge rifles. mag, reload s, charge s, tap damage, extra at full, shot cd, weapon name
const BND={nsboy:{mag:8,rl:1.5,ch:.6,t:26,f:32,cd:.45,w:'rubber band'},lens:{mag:6,rl:1.8,ch:1.2,t:30,f:50,cd:.5,w:'telephoto shot'}};
```

## Hunk 2: NSF kit loses the Quick Reload passive row

Anchor:

```
,['P','Quick Reload','Press R again at the right moment in a reload to finish it early and stretch your next band.','The window is 0.6 to 0.8 seconds into the reload. One try per reload.']
```

Replacement:

```

```

## Hunk 3: quick reload sound key gone

Anchor:

```
h_ns_quickreload:'a_eng_turret',
```

Replacement:

```

```

## Hunk 4: third person reload pose comment

Anchor:

```
[1.5,Z12,'backOut']], // .6 key: hand at the mag, the active window opens
```

Replacement:

```
[1.5,Z12,'backOut']], // .6 key: hand at the mag
```

## Hunk 5: third person reload: no 2x finish, no fumble

Anchor:

```
      if(W.rlT>=0)apC(h,kfA(RL,W.rlT,_aa),1);
      else if(n.rl>=0&&n.rl<=.85){n.rf=n.rl;n.rs=0;n.sq.v-=1.5} // good active press: play the rest at 2x
      if(n.rf>=0){const t=n.rf+2*n.rs;n.rs+=dt;if(t<1.5)apC(h,kfA(RL,t,_aa),1);else n.rf=-1}
      if(W.arTry&&W.rlT>=0&&!n.ar)n.fm=.3;n.ar=!!W.arTry;n.rl=W.rlT??-1; // a missed press fumbles
      if(n.fm>0){n.fm-=dt;h.armR.rotation.x+=.2*S(P2*8*(.3-n.fm))}
```

Replacement:

```
      if(W.rlT>=0)apC(h,kfA(RL,W.rlT,_aa),1);
```

## Hunk 6: bandReload plain, bandActive removed, first person reload clips

Anchor:

```
function bandReload(e){const W=e.wpn;if(W.rlT>=0||W.mag>=BND[e.hk].mag)return;W.rlT=0;W.arTry=false;W.arOk=!(e.isPlayer&&!autoPilot)&&Math.random()<.5} // bots hit the active reload half the time
function bandActive(e){const W=e.wpn;if(!(W.rlT>=0)){bandReload(e);return}
  if(W.arTry)return;W.arTry=true;const B=BND[e.hk];if(W.rlT>=B.ar[0]&&W.rlT<=B.ar[1]){W.rlT=-1;W.mag=B.mag;W.pre=true;fxe('burst',chestOf(e,tmpA),0xffe600,8,3,.3);fxe('auE',e,'h_ns_quickreload')}} // active reload: one try per reload
```

Replacement:

```
// first person reload clips for vmo.ab: G both hands, L off hand, R gun hand, keys [t,[dx,dy,dz,rx,ry,rz],ease], hA hides the loaded band. Reduced motion keeps 30% of the moves
const RLV=(()=>{const k=REDUCED?.3:1,v=a=>a.map(x=>x*k),Z=[0,0,0,0,0,0];return{
  nsboy:{d:1.5,hA:[.1,1.02], // tilt the rifle, off hand dips for a fresh band, hooks it on the nose, snap
    G:[[0,Z],[.16,v([-.04,.05,.03,.34,.22,.5]),'out3'],[1.12,v([-.04,.045,.03,.3,.2,.46])],[1.5,Z,'backOut']],
    L:[[0,Z],[.14,v([-.05,-.36,.14,-.6,0,.3]),'in2'],[.5,v([-.04,-.32,.12,-.5,0,.3])],[.8,v([.07,.07,-.03,.2,0,-.2]),'out3'],[.98,v([.09,.09,-.14,.3,0,-.2]),'in2'],[1.08,v([.05,.05,.02,0,0,0]),'out2'],[1.4,Z,'backOut']],
    R:[[0,Z],[.98,Z],[1.03,v([0,-.015,.06,-.18,0,0]),'in2'],[1.26,Z,'backOut']]},
  lens:{d:1.8, // tip the camera, off hand dips for a fresh roll, twists the lens twice, click
    G:[[0,Z],[.2,v([.03,.05,.04,.3,-.14,-.44]),'out3'],[1.42,v([.03,.05,.04,.28,-.12,-.4])],[1.8,Z,'backOut']],
    L:[[0,Z],[.16,v([-.04,-.32,.12,-.5,0,.3]),'in2'],[.55,v([-.03,-.3,.1,-.4,0,.3])],[.8,v([.04,.02,-.04,.1,0,0]),'out3'],[.98,v([.04,.02,-.04,.1,0,.9])],[1.13,v([.04,.02,-.04,.1,0,-.2])],[1.28,v([.04,.02,-.04,.1,0,.9])],[1.4,v([.04,.02,-.04,.1,0,0])],[1.62,Z,'backOut']],
    R:[[0,Z],[1.38,Z],[1.44,v([0,-.01,.05,-.12,0,0]),'in2'],[1.66,Z,'backOut']]}}})();
function bandReload(e){const W=e.wpn;if(W.rlT>=0||W.mag>=BND[e.hk].mag)return;W.rlT=0;if(e===player&&!autoPilot){if(vmo)vmo.ab(RLV[e.hk]);AU.play('ui_tick',{pitch:-7,gain:.7})}} // plain reload: auto at empty, R when not full
```

## Hunk 7: R key reloads (aim wall rotate keeps R first)

Anchor:

```
else if(c==='KeyR'&&BND[player.hk]&&player.alive)bandActive(player);
```

Replacement:

```
else if(c==='KeyR'&&BND[player.hk]&&player.alive)bandReload(player);
```

## Hunk 8: reload tick: no bot window hits

Anchor:

```
if(BND[e.hk]){const W=e.wpn,A=BND[e.hk],am=(A.ar[0]+A.ar[1])/2;if(W.rlT>=0){W.rlT+=dt;if(W.arOk&&W.rlT>=am){W.arOk=false;W.arTry=false;W.rlT=am;bandActive(e)}else if(W.rlT>=A.rl){W.rlT=-1;W.mag=A.mag}}}
```

Replacement:

```
if(BND[e.hk]){const W=e.wpn,A=BND[e.hk];if(W.rlT>=0&&(W.rlT+=dt)>=A.rl){W.rlT=-1;W.mag=A.mag}}
```

## Hunk 9: ammo counter CSS

Anchor:

```
.chud .reps b{display:block;height:3px;width:0;background:var(--tissue);box-shadow:0 0 0 1px var(--ink);align-self:flex-start}
```

Replacement:

```
.chud .reps b{display:block;height:3px;width:0;background:var(--tissue);box-shadow:0 0 0 1px var(--ink);align-self:flex-start}
/* ammo counter for the band heroes: receipt chit over the ability row, one icon per round. .ammo carries the drop shadow, the masked .am can't */
.chud .ammo{position:absolute;right:calc(6*var(--p));bottom:calc(168*var(--p));filter:drop-shadow(3px 3px 0 var(--kopi));transform:rotate(-2deg);transform-origin:100% 100%}
.chud .ammo[hidden],.chud .amxh[hidden]{display:none}
.chud .ammo .am{position:relative;padding:calc(6*var(--p)) calc(12*var(--p)) calc(15*var(--p));min-width:calc(150*var(--p))}
.chud .ammo .amh{display:flex;align-items:baseline;justify-content:space-between;gap:calc(12*var(--p));border-bottom:1.5px dashed var(--kopi-2);padding-bottom:calc(3*var(--p));margin-bottom:calc(7*var(--p))}
.chud .ammo .aml{color:var(--kopi-2);white-space:nowrap}
.chud .ammo .amq{white-space:nowrap;font-variant-numeric:tabular-nums}
.chud .ammo .amn{display:inline-block;font:400 calc(30*var(--p))/1 var(--slab);color:var(--ink);transform-origin:50% 80%}
.chud .ammo .amm{font:800 calc(15*var(--p)) var(--ui);color:var(--kopi-2);margin-left:2px}
.chud .ammo .amr{position:relative;display:flex;gap:calc(5*var(--p));justify-content:flex-end;align-items:center;height:calc(24*var(--p))}
.chud .ammo .amr i,.chud .ammo .amg{flex:none;display:block;position:relative;transition:opacity .12s,transform .12s}
/* NSF: a red rubber band loop */
.chud .ammo.nsboy .amr i,.chud .ammo.nsboy .amg{width:calc(18*var(--p));height:calc(12*var(--p));border-radius:50%;border:calc(3.5*var(--p)) solid #E8312A;box-shadow:0 0 0 1.5px var(--ink),inset 0 0 0 1.5px var(--ink);transform:rotate(-14deg)}
.chud .ammo.nsboy .amr i:nth-child(even){transform:rotate(10deg) translateY(1px)}
.chud .ammo.nsboy .amr i:not(.on){border-color:var(--terrazzo);opacity:.45;transform:rotate(-14deg) scale(.78)}
/* Birdwatcher: a film frame with sprocket holes */
.chud .ammo.lens .amr i,.chud .ammo.lens .amg{width:calc(17*var(--p));height:calc(22*var(--p));border-radius:2px;box-shadow:0 0 0 1.5px var(--ink);
  background:linear-gradient(#FFD877,#E3A92B) 50% 50%/56% 56% no-repeat,repeating-linear-gradient(0deg,var(--tissue) 0 2px,transparent 2px 4px) 1.5px 0/2px 100% no-repeat,repeating-linear-gradient(0deg,var(--tissue) 0 2px,transparent 2px 4px) calc(100% - 1.5px) 0/2px 100% no-repeat,#2A1D17}
.chud .ammo.lens .amr i:not(.on){background:linear-gradient(#5A3A26,#3A2417) 50% 50%/56% 56% no-repeat,#6b5a50;opacity:.5;transform:scale(.82)}
/* reload bar under the rounds */
.chud .ammo .amb{height:calc(7*var(--p));margin-top:calc(6*var(--p));border:1.5px solid var(--ink);border-radius:3px;background:var(--enamel-2);overflow:hidden;opacity:0;transition:opacity .1s}
.chud .ammo .amb i{display:block;height:100%;transform-origin:0 50%;transform:scaleX(0);background:repeating-linear-gradient(-45deg,var(--kaya) 0 5px,#d29a20 5px 8px);background-size:11px 11px;animation:chud-stripe .6s linear infinite}
.chud .ammo.rl .amb{opacity:1}
.chud .ammo.rl .aml{color:#B07A10}
.chud .ammo .ams{position:absolute;right:calc(-8*var(--p));top:calc(-20*var(--p));padding:1px calc(8*var(--p));font-size:calc(15*var(--p));opacity:0;pointer-events:none}
.chud .ammo .ams.on{animation:am-stamp 1.1s ease-out both}
/* low: rounds glow red and breathe, the count goes red */
.chud .ammo.low .amn{color:var(--signred)}
.chud .ammo.low.nsboy .amr i.on{animation:am-low .55s ease-in-out infinite alternate}
.chud .ammo.low.lens .amr i.on{animation:am-lowl .55s ease-in-out infinite alternate}
/* ult: no reload, rounds go gold */
.chud .ammo.amu .amn{color:#B07A10}
.chud .ammo.amu.nsboy .amr i.on{border-color:#FFD23F;box-shadow:0 0 0 1.5px var(--ink),inset 0 0 0 1.5px var(--ink),0 0 8px #FFD23F;animation:am-gold .5s ease-in-out infinite alternate calc(var(--i)*-60ms)}
.chud .ammo.amu.lens .amr i.on{box-shadow:0 0 0 1.5px var(--ink),0 0 8px #FFD23F;animation:am-gold .5s ease-in-out infinite alternate calc(var(--i)*-60ms)}
/* beats: spent round flies off, row recoils, count pops, refilled round bounces in, full flashes a wave and pops the chit */
.chud .ammo .amg{position:absolute;margin:0;animation:am-fly .42s cubic-bezier(.2,.6,.4,1) forwards}
.chud .ammo .amr.kick{animation:am-kick .14s ease-out}
.chud .ammo .amn.pop{animation:am-pop .2s cubic-bezier(.3,1.8,.5,1)}
.chud .ammo .amr i.in{animation:am-in .28s cubic-bezier(.3,1.7,.5,1) both}
.chud .ammo.full{animation:am-full .34s cubic-bezier(.3,1.8,.5,1)}
.chud .ammo.full .amr i{animation:am-wave .36s ease-out both calc(var(--i)*28ms)}
.chud .ammo .amk{position:absolute;left:50%;top:50%;width:10px;height:10px;margin:-5px;border-radius:50%;pointer-events:none;opacity:0}
.chud .ammo.full .amk{animation:am-ring .45s ease-out}
@keyframes am-fly{0%{opacity:1;transform:rotate(-14deg)}18%{opacity:1;transform:scale(1.35,.65) rotate(-14deg)}100%{opacity:0;transform:translate(var(--dx),calc(-38*var(--p))) rotate(var(--r)) scale(.55)}}
@keyframes am-kick{40%{transform:translate(2px,2px)}}
@keyframes am-pop{0%{transform:scale(1.4) rotate(-6deg)}}
@keyframes am-in{0%{opacity:0;transform:translateY(-9px) scale(0) rotate(-40deg)}}
@keyframes am-full{40%{transform:rotate(-2deg) scale(1.09)}}
@keyframes am-wave{40%{filter:brightness(1.7) saturate(1.3);translate:0 -4px}}
@keyframes am-ring{0%{opacity:.9;box-shadow:0 0 0 0 #FFD23F,0 0 0 0 var(--tissue)}100%{opacity:0;box-shadow:0 0 0 calc(70*var(--p)) #FFD23F00,0 0 0 calc(40*var(--p)) #FBF8F000}}
@keyframes am-low{to{border-color:var(--led);scale:1.12}}
@keyframes am-lowl{to{filter:hue-rotate(-40deg) saturate(1.8) brightness(1.05);scale:1.1}}
@keyframes am-gold{to{filter:brightness(1.35);translate:0 -2px}}
@keyframes am-stamp{0%{opacity:0;transform:scale(1.6) rotate(-14deg)}14%{opacity:1;transform:scale(1) rotate(-8deg)}22%{transform:translate(2px,0) rotate(-8deg)}30%{transform:translate(-2px,0) rotate(-8deg)}75%{opacity:1;transform:rotate(-8deg)}100%{opacity:0;transform:translateY(-8px) rotate(-8deg)}}
/* crosshair: a thin reload ring while reloading, an R chip when low */
.chud .amxh{position:absolute;left:50%;top:50%;width:0;height:0}
.chud .amxh .ring{position:absolute;left:-23px;top:-23px;width:46px;height:46px;border-radius:50%;opacity:0;transition:opacity .1s;
  background:conic-gradient(var(--kaya) var(--rp,0deg),rgba(28,21,18,.35) 0);-webkit-mask:radial-gradient(circle,#0000 18px,#000 18.5px 22px,#0000 22.5px);mask:radial-gradient(circle,#0000 18px,#000 18.5px 22px,#0000 22.5px)}
.chud .amxh.rl .ring{opacity:1}
.chud .amxh .lo{position:absolute;left:0;top:calc(34*var(--p));transform:translateX(-50%);white-space:nowrap;display:none;align-items:center;gap:5px;font:800 calc(13*var(--p)) var(--ui);text-transform:uppercase;letter-spacing:.08em;color:var(--tissue);text-shadow:1px 1px 0 var(--ink)}
.chud .amxh.low .lo{display:flex;animation:chud-pulse .9s ease-in-out infinite}
@media (prefers-reduced-motion:reduce){.chud .ammo,.chud .ammo *,.chud .amxh *{animation:none!important}.chud .ammo .amg{display:none}}
```

## Hunk 10: ammo counter element and tick

Anchor:

```
hud.root.appendChild(repEl); // Gym Rep counter
```

Replacement:

```
hud.root.appendChild(repEl); // Gym Rep counter
// ammo counter (NSF bands, Birdwatcher film). Spent rounds fly off, the reload refills them one by one from .3 to .92 of the reload with a tick each, full pops
const AMN={nsboy:'Rubber bands',lens:'Film rolls'},AMS={hk:'',n:-1,rl:false,k:''};
const amEl=document.createElement('div');amEl.className='ammo';amEl.hidden=true;amEl.innerHTML='<div class="am chit zz-b"><div class="amh"><span class="micro aml"></span><span class="amq"><b class="amn"></b><small class="amm"></small></span></div><div class="amr"></div><div class="amb"><i></i></div></div><i class="amk"></i><span class="ams sign">Kosong!</span>';hud.root.appendChild(amEl);
const amX=document.createElement('div');amX.className='amxh';amX.hidden=true;amX.innerHTML='<i class="ring"></i><span class="lo"><b class="key">R</b>Reload</span>';hud.root.appendChild(amX);
const amQ=s=>amEl.querySelector(s),amR=amQ('.amr'),amN=amQ('.amn'),amL=amQ('.aml'),amB=amQ('.amb i'),amS=amQ('.ams');
const reAnim=(el,c)=>{el.classList.remove(c);void el.offsetWidth;el.classList.add(c)};
function amFly(pip){if(REDUCED)return;const g=document.createElement('span');g.className='amg';g.style.left=pip.offsetLeft+'px';g.style.top=pip.offsetTop+'px';
  g.style.setProperty('--dx',(Math.random()*26-8).toFixed(1)+'px');g.style.setProperty('--r',((Math.random()<.5?-1:1)*(150+Math.random()*130)).toFixed(0)+'deg');amR.appendChild(g);g.addEventListener('animationend',()=>g.remove())}
function ammoTick(p){const B=BND[p.hk],on=!!B&&p.alive&&!(p.birdT>0)&&state==='playing';amEl.hidden=amX.hidden=!on;if(!on){AMS.n=-1;return}
  const W=p.wpn,S=AMS;
  if(S.hk!==p.hk){S.hk=p.hk;amEl.className='ammo '+p.hk;amR.innerHTML=Array.from({length:B.mag},(_,i)=>`<i class="on" style="--i:${i}"></i>`).join('');amQ('.amm').textContent='/'+B.mag;S.n=-1;S.k=''}
  const mag=W.mag??B.mag,rl=W.rlT>=0,u=rl?Math.min(1,W.rlT/B.rl):0,ult=p.ultT>0,
    n=rl?mag+Math.floor((B.mag-mag)*Math.max(0,Math.min(1,(u-.3)/.62))):mag;
  if(S.n<0){S.n=n;[...amR.children].forEach((c,i)=>c.classList.toggle('on',i<n))}
  if(n!==S.n){const P=amR.children;
    if(n<S.n){for(let i=n;i<S.n;i++){P[i].classList.remove('on','in');amFly(P[i])}reAnim(amR,'kick')}
    else{for(let i=S.n;i<n;i++){P[i].classList.add('on');reAnim(P[i],'in')}if(rl)AU.play('ui_click',{pitch:n*1.5-4,gain:.55})}
    reAnim(amN,'pop');S.n=n}
  if(rl&&!S.rl&&mag===0)reAnim(amS,'on');
  if(S.rl&&!rl&&!ult&&mag>=B.mag){reAnim(amEl,'full');AU.play('k_charge_full',{gain:.45})}
  if(!rl&&vmo&&vmo.abS===RLV[p.hk])vmo.abS=null; // ult or death cut the reload: stop the clip
  S.rl=rl;
  const low=!rl&&!ult&&mag<=Math.ceil(B.mag/4),k=(ult?'u':rl?'r':low?'l':'n')+n;
  if(k!==S.k){S.k=k;amEl.classList.toggle('rl',rl);amEl.classList.toggle('low',low);amEl.classList.toggle('amu',ult);amX.classList.toggle('rl',rl);amX.classList.toggle('low',low);
    amN.textContent=ult?'∞':n;amL.textContent=ult?p.H.kit[4][1]:rl?'Reloading':AMN[p.hk]}
  if(rl){amB.style.transform=`scaleX(${u.toFixed(3)})`;amX.style.setProperty('--rp',(u*360).toFixed(1)+'deg')}
}
```

## Hunk 11: ammo counter runs with the HUD

Anchor:

```
  {const on=p.hk==='gym'&&p.alive;repEl.hidden=!on;
```

Replacement:

```
  ammoTick(p);
  {const on=p.hk==='gym'&&p.alive;repEl.hidden=!on;
```

## Apply script

```python
# Reload patch hunks for play/chope.html: (name, anchor, replacement). Each anchor must occur exactly once.
H = []
def h(name, a, b): H.append((name, a, b))

h('BND drops the active reload window',
"""// HEROES3: hold-to-charge rifles. mag, reload s, active reload window, charge s, tap damage, extra at full, shot cd, weapon name
const BND={nsboy:{mag:8,rl:1.5,ar:[.6,.8],ch:.6,t:26,f:32,cd:.45,w:'rubber band'},lens:{mag:6,rl:1.8,ar:[.9,1.1],ch:1.2,t:30,f:50,cd:.5,w:'telephoto shot'}};""",
"""// HEROES3: hold-to-charge rifles. mag, reload s, charge s, tap damage, extra at full, shot cd, weapon name
const BND={nsboy:{mag:8,rl:1.5,ch:.6,t:26,f:32,cd:.45,w:'rubber band'},lens:{mag:6,rl:1.8,ch:1.2,t:30,f:50,cd:.5,w:'telephoto shot'}};""")

h('NSF kit loses the Quick Reload passive row',
",['P','Quick Reload','Press R again at the right moment in a reload to finish it early and stretch your next band.','The window is 0.6 to 0.8 seconds into the reload. One try per reload.']",
"")

h('quick reload sound key gone',
"h_ns_quickreload:'a_eng_turret',", "")

h('third person reload pose comment',
"[1.5,Z12,'backOut']], // .6 key: hand at the mag, the active window opens",
"[1.5,Z12,'backOut']], // .6 key: hand at the mag")

h('third person reload: no 2x finish, no fumble',
"""      if(W.rlT>=0)apC(h,kfA(RL,W.rlT,_aa),1);
      else if(n.rl>=0&&n.rl<=.85){n.rf=n.rl;n.rs=0;n.sq.v-=1.5} // good active press: play the rest at 2x
      if(n.rf>=0){const t=n.rf+2*n.rs;n.rs+=dt;if(t<1.5)apC(h,kfA(RL,t,_aa),1);else n.rf=-1}
      if(W.arTry&&W.rlT>=0&&!n.ar)n.fm=.3;n.ar=!!W.arTry;n.rl=W.rlT??-1; // a missed press fumbles
      if(n.fm>0){n.fm-=dt;h.armR.rotation.x+=.2*S(P2*8*(.3-n.fm))}
""",
"""      if(W.rlT>=0)apC(h,kfA(RL,W.rlT,_aa),1);
""")

h('bandReload plain, bandActive removed, first person reload clips',
"""function bandReload(e){const W=e.wpn;if(W.rlT>=0||W.mag>=BND[e.hk].mag)return;W.rlT=0;W.arTry=false;W.arOk=!(e.isPlayer&&!autoPilot)&&Math.random()<.5} // bots hit the active reload half the time
function bandActive(e){const W=e.wpn;if(!(W.rlT>=0)){bandReload(e);return}
  if(W.arTry)return;W.arTry=true;const B=BND[e.hk];if(W.rlT>=B.ar[0]&&W.rlT<=B.ar[1]){W.rlT=-1;W.mag=B.mag;W.pre=true;fxe('burst',chestOf(e,tmpA),0xffe600,8,3,.3);fxe('auE',e,'h_ns_quickreload')}} // active reload: one try per reload
""",
"""// first person reload clips for vmo.ab: G both hands, L off hand, R gun hand, keys [t,[dx,dy,dz,rx,ry,rz],ease], hA hides the loaded band. Reduced motion keeps 30% of the moves
const RLV=(()=>{const k=REDUCED?.3:1,v=a=>a.map(x=>x*k),Z=[0,0,0,0,0,0];return{
  nsboy:{d:1.5,hA:[.1,1.02], // tilt the rifle, off hand dips for a fresh band, hooks it on the nose, snap
    G:[[0,Z],[.16,v([-.04,.05,.03,.34,.22,.5]),'out3'],[1.12,v([-.04,.045,.03,.3,.2,.46])],[1.5,Z,'backOut']],
    L:[[0,Z],[.14,v([-.05,-.36,.14,-.6,0,.3]),'in2'],[.5,v([-.04,-.32,.12,-.5,0,.3])],[.8,v([.07,.07,-.03,.2,0,-.2]),'out3'],[.98,v([.09,.09,-.14,.3,0,-.2]),'in2'],[1.08,v([.05,.05,.02,0,0,0]),'out2'],[1.4,Z,'backOut']],
    R:[[0,Z],[.98,Z],[1.03,v([0,-.015,.06,-.18,0,0]),'in2'],[1.26,Z,'backOut']]},
  lens:{d:1.8, // tip the camera, off hand dips for a fresh roll, twists the lens twice, click
    G:[[0,Z],[.2,v([.03,.05,.04,.3,-.14,-.44]),'out3'],[1.42,v([.03,.05,.04,.28,-.12,-.4])],[1.8,Z,'backOut']],
    L:[[0,Z],[.16,v([-.04,-.32,.12,-.5,0,.3]),'in2'],[.55,v([-.03,-.3,.1,-.4,0,.3])],[.8,v([.04,.02,-.04,.1,0,0]),'out3'],[.98,v([.04,.02,-.04,.1,0,.9])],[1.13,v([.04,.02,-.04,.1,0,-.2])],[1.28,v([.04,.02,-.04,.1,0,.9])],[1.4,v([.04,.02,-.04,.1,0,0])],[1.62,Z,'backOut']],
    R:[[0,Z],[1.38,Z],[1.44,v([0,-.01,.05,-.12,0,0]),'in2'],[1.66,Z,'backOut']]}}})();
function bandReload(e){const W=e.wpn;if(W.rlT>=0||W.mag>=BND[e.hk].mag)return;W.rlT=0;if(e===player&&!autoPilot){if(vmo)vmo.ab(RLV[e.hk]);AU.play('ui_tick',{pitch:-7,gain:.7})}} // plain reload: auto at empty, R when not full
""")

h('R key reloads (aim wall rotate keeps R first)',
"else if(c==='KeyR'&&BND[player.hk]&&player.alive)bandActive(player);",
"else if(c==='KeyR'&&BND[player.hk]&&player.alive)bandReload(player);")

h('reload tick: no bot window hits',
"if(BND[e.hk]){const W=e.wpn,A=BND[e.hk],am=(A.ar[0]+A.ar[1])/2;if(W.rlT>=0){W.rlT+=dt;if(W.arOk&&W.rlT>=am){W.arOk=false;W.arTry=false;W.rlT=am;bandActive(e)}else if(W.rlT>=A.rl){W.rlT=-1;W.mag=A.mag}}}",
"if(BND[e.hk]){const W=e.wpn,A=BND[e.hk];if(W.rlT>=0&&(W.rlT+=dt)>=A.rl){W.rlT=-1;W.mag=A.mag}}")

CSS = r"""
/* ammo counter for the band heroes: receipt chit over the ability row, one icon per round. .ammo carries the drop shadow, the masked .am can't */
.chud .ammo{position:absolute;right:calc(6*var(--p));bottom:calc(168*var(--p));filter:drop-shadow(3px 3px 0 var(--kopi));transform:rotate(-2deg);transform-origin:100% 100%}
.chud .ammo[hidden],.chud .amxh[hidden]{display:none}
.chud .ammo .am{position:relative;padding:calc(6*var(--p)) calc(12*var(--p)) calc(15*var(--p));min-width:calc(150*var(--p))}
.chud .ammo .amh{display:flex;align-items:baseline;justify-content:space-between;gap:calc(12*var(--p));border-bottom:1.5px dashed var(--kopi-2);padding-bottom:calc(3*var(--p));margin-bottom:calc(7*var(--p))}
.chud .ammo .aml{color:var(--kopi-2);white-space:nowrap}
.chud .ammo .amq{white-space:nowrap;font-variant-numeric:tabular-nums}
.chud .ammo .amn{display:inline-block;font:400 calc(30*var(--p))/1 var(--slab);color:var(--ink);transform-origin:50% 80%}
.chud .ammo .amm{font:800 calc(15*var(--p)) var(--ui);color:var(--kopi-2);margin-left:2px}
.chud .ammo .amr{position:relative;display:flex;gap:calc(5*var(--p));justify-content:flex-end;align-items:center;height:calc(24*var(--p))}
.chud .ammo .amr i,.chud .ammo .amg{flex:none;display:block;position:relative;transition:opacity .12s,transform .12s}
/* NSF: a red rubber band loop */
.chud .ammo.nsboy .amr i,.chud .ammo.nsboy .amg{width:calc(18*var(--p));height:calc(12*var(--p));border-radius:50%;border:calc(3.5*var(--p)) solid #E8312A;box-shadow:0 0 0 1.5px var(--ink),inset 0 0 0 1.5px var(--ink);transform:rotate(-14deg)}
.chud .ammo.nsboy .amr i:nth-child(even){transform:rotate(10deg) translateY(1px)}
.chud .ammo.nsboy .amr i:not(.on){border-color:var(--terrazzo);opacity:.45;transform:rotate(-14deg) scale(.78)}
/* Birdwatcher: a film frame with sprocket holes */
.chud .ammo.lens .amr i,.chud .ammo.lens .amg{width:calc(17*var(--p));height:calc(22*var(--p));border-radius:2px;box-shadow:0 0 0 1.5px var(--ink);
  background:linear-gradient(#FFD877,#E3A92B) 50% 50%/56% 56% no-repeat,repeating-linear-gradient(0deg,var(--tissue) 0 2px,transparent 2px 4px) 1.5px 0/2px 100% no-repeat,repeating-linear-gradient(0deg,var(--tissue) 0 2px,transparent 2px 4px) calc(100% - 1.5px) 0/2px 100% no-repeat,#2A1D17}
.chud .ammo.lens .amr i:not(.on){background:linear-gradient(#5A3A26,#3A2417) 50% 50%/56% 56% no-repeat,#6b5a50;opacity:.5;transform:scale(.82)}
/* reload bar under the rounds */
.chud .ammo .amb{height:calc(7*var(--p));margin-top:calc(6*var(--p));border:1.5px solid var(--ink);border-radius:3px;background:var(--enamel-2);overflow:hidden;opacity:0;transition:opacity .1s}
.chud .ammo .amb i{display:block;height:100%;transform-origin:0 50%;transform:scaleX(0);background:repeating-linear-gradient(-45deg,var(--kaya) 0 5px,#d29a20 5px 8px);background-size:11px 11px;animation:chud-stripe .6s linear infinite}
.chud .ammo.rl .amb{opacity:1}
.chud .ammo.rl .aml{color:#B07A10}
.chud .ammo .ams{position:absolute;right:calc(-8*var(--p));top:calc(-20*var(--p));padding:1px calc(8*var(--p));font-size:calc(15*var(--p));opacity:0;pointer-events:none}
.chud .ammo .ams.on{animation:am-stamp 1.1s ease-out both}
/* low: rounds glow red and breathe, the count goes red */
.chud .ammo.low .amn{color:var(--signred)}
.chud .ammo.low.nsboy .amr i.on{animation:am-low .55s ease-in-out infinite alternate}
.chud .ammo.low.lens .amr i.on{animation:am-lowl .55s ease-in-out infinite alternate}
/* ult: no reload, rounds go gold */
.chud .ammo.amu .amn{color:#B07A10}
.chud .ammo.amu.nsboy .amr i.on{border-color:#FFD23F;box-shadow:0 0 0 1.5px var(--ink),inset 0 0 0 1.5px var(--ink),0 0 8px #FFD23F;animation:am-gold .5s ease-in-out infinite alternate calc(var(--i)*-60ms)}
.chud .ammo.amu.lens .amr i.on{box-shadow:0 0 0 1.5px var(--ink),0 0 8px #FFD23F;animation:am-gold .5s ease-in-out infinite alternate calc(var(--i)*-60ms)}
/* beats: spent round flies off, row recoils, count pops, refilled round bounces in, full flashes a wave and pops the chit */
.chud .ammo .amg{position:absolute;margin:0;animation:am-fly .42s cubic-bezier(.2,.6,.4,1) forwards}
.chud .ammo .amr.kick{animation:am-kick .14s ease-out}
.chud .ammo .amn.pop{animation:am-pop .2s cubic-bezier(.3,1.8,.5,1)}
.chud .ammo .amr i.in{animation:am-in .28s cubic-bezier(.3,1.7,.5,1) both}
.chud .ammo.full{animation:am-full .34s cubic-bezier(.3,1.8,.5,1)}
.chud .ammo.full .amr i{animation:am-wave .36s ease-out both calc(var(--i)*28ms)}
.chud .ammo .amk{position:absolute;left:50%;top:50%;width:10px;height:10px;margin:-5px;border-radius:50%;pointer-events:none;opacity:0}
.chud .ammo.full .amk{animation:am-ring .45s ease-out}
@keyframes am-fly{0%{opacity:1;transform:rotate(-14deg)}18%{opacity:1;transform:scale(1.35,.65) rotate(-14deg)}100%{opacity:0;transform:translate(var(--dx),calc(-38*var(--p))) rotate(var(--r)) scale(.55)}}
@keyframes am-kick{40%{transform:translate(2px,2px)}}
@keyframes am-pop{0%{transform:scale(1.4) rotate(-6deg)}}
@keyframes am-in{0%{opacity:0;transform:translateY(-9px) scale(0) rotate(-40deg)}}
@keyframes am-full{40%{transform:rotate(-2deg) scale(1.09)}}
@keyframes am-wave{40%{filter:brightness(1.7) saturate(1.3);translate:0 -4px}}
@keyframes am-ring{0%{opacity:.9;box-shadow:0 0 0 0 #FFD23F,0 0 0 0 var(--tissue)}100%{opacity:0;box-shadow:0 0 0 calc(70*var(--p)) #FFD23F00,0 0 0 calc(40*var(--p)) #FBF8F000}}
@keyframes am-low{to{border-color:var(--led);scale:1.12}}
@keyframes am-lowl{to{filter:hue-rotate(-40deg) saturate(1.8) brightness(1.05);scale:1.1}}
@keyframes am-gold{to{filter:brightness(1.35);translate:0 -2px}}
@keyframes am-stamp{0%{opacity:0;transform:scale(1.6) rotate(-14deg)}14%{opacity:1;transform:scale(1) rotate(-8deg)}22%{transform:translate(2px,0) rotate(-8deg)}30%{transform:translate(-2px,0) rotate(-8deg)}75%{opacity:1;transform:rotate(-8deg)}100%{opacity:0;transform:translateY(-8px) rotate(-8deg)}}
/* crosshair: a thin reload ring while reloading, an R chip when low */
.chud .amxh{position:absolute;left:50%;top:50%;width:0;height:0}
.chud .amxh .ring{position:absolute;left:-23px;top:-23px;width:46px;height:46px;border-radius:50%;opacity:0;transition:opacity .1s;
  background:conic-gradient(var(--kaya) var(--rp,0deg),rgba(28,21,18,.35) 0);-webkit-mask:radial-gradient(circle,#0000 18px,#000 18.5px 22px,#0000 22.5px);mask:radial-gradient(circle,#0000 18px,#000 18.5px 22px,#0000 22.5px)}
.chud .amxh.rl .ring{opacity:1}
.chud .amxh .lo{position:absolute;left:0;top:calc(34*var(--p));transform:translateX(-50%);white-space:nowrap;display:none;align-items:center;gap:5px;font:800 calc(13*var(--p)) var(--ui);text-transform:uppercase;letter-spacing:.08em;color:var(--tissue);text-shadow:1px 1px 0 var(--ink)}
.chud .amxh.low .lo{display:flex;animation:chud-pulse .9s ease-in-out infinite}
@media (prefers-reduced-motion:reduce){.chud .ammo,.chud .ammo *,.chud .amxh *{animation:none!important}.chud .ammo .amg{display:none}}"""

h('ammo counter CSS',
".chud .reps b{display:block;height:3px;width:0;background:var(--tissue);box-shadow:0 0 0 1px var(--ink);align-self:flex-start}",
".chud .reps b{display:block;height:3px;width:0;background:var(--tissue);box-shadow:0 0 0 1px var(--ink);align-self:flex-start}" + CSS)

JS = r"""
// ammo counter (NSF bands, Birdwatcher film). Spent rounds fly off, the reload refills them one by one from .3 to .92 of the reload with a tick each, full pops
const AMN={nsboy:'Rubber bands',lens:'Film rolls'},AMS={hk:'',n:-1,rl:false,k:''};
const amEl=document.createElement('div');amEl.className='ammo';amEl.hidden=true;amEl.innerHTML='<div class="am chit zz-b"><div class="amh"><span class="micro aml"></span><span class="amq"><b class="amn"></b><small class="amm"></small></span></div><div class="amr"></div><div class="amb"><i></i></div></div><i class="amk"></i><span class="ams sign">Kosong!</span>';hud.root.appendChild(amEl);
const amX=document.createElement('div');amX.className='amxh';amX.hidden=true;amX.innerHTML='<i class="ring"></i><span class="lo"><b class="key">R</b>Reload</span>';hud.root.appendChild(amX);
const amQ=s=>amEl.querySelector(s),amR=amQ('.amr'),amN=amQ('.amn'),amL=amQ('.aml'),amB=amQ('.amb i'),amS=amQ('.ams');
const reAnim=(el,c)=>{el.classList.remove(c);void el.offsetWidth;el.classList.add(c)};
function amFly(pip){if(REDUCED)return;const g=document.createElement('span');g.className='amg';g.style.left=pip.offsetLeft+'px';g.style.top=pip.offsetTop+'px';
  g.style.setProperty('--dx',(Math.random()*26-8).toFixed(1)+'px');g.style.setProperty('--r',((Math.random()<.5?-1:1)*(150+Math.random()*130)).toFixed(0)+'deg');amR.appendChild(g);g.addEventListener('animationend',()=>g.remove())}
function ammoTick(p){const B=BND[p.hk],on=!!B&&p.alive&&!(p.birdT>0)&&state==='playing';amEl.hidden=amX.hidden=!on;if(!on){AMS.n=-1;return}
  const W=p.wpn,S=AMS;
  if(S.hk!==p.hk){S.hk=p.hk;amEl.className='ammo '+p.hk;amR.innerHTML=Array.from({length:B.mag},(_,i)=>`<i class="on" style="--i:${i}"></i>`).join('');amQ('.amm').textContent='/'+B.mag;S.n=-1;S.k=''}
  const mag=W.mag??B.mag,rl=W.rlT>=0,u=rl?Math.min(1,W.rlT/B.rl):0,ult=p.ultT>0,
    n=rl?mag+Math.floor((B.mag-mag)*Math.max(0,Math.min(1,(u-.3)/.62))):mag;
  if(S.n<0){S.n=n;[...amR.children].forEach((c,i)=>c.classList.toggle('on',i<n))}
  if(n!==S.n){const P=amR.children;
    if(n<S.n){for(let i=n;i<S.n;i++){P[i].classList.remove('on','in');amFly(P[i])}reAnim(amR,'kick')}
    else{for(let i=S.n;i<n;i++){P[i].classList.add('on');reAnim(P[i],'in')}if(rl)AU.play('ui_click',{pitch:n*1.5-4,gain:.55})}
    reAnim(amN,'pop');S.n=n}
  if(rl&&!S.rl&&mag===0)reAnim(amS,'on');
  if(S.rl&&!rl&&!ult&&mag>=B.mag){reAnim(amEl,'full');AU.play('k_charge_full',{gain:.45})}
  if(!rl&&vmo&&vmo.abS===RLV[p.hk])vmo.abS=null; // ult or death cut the reload: stop the clip
  S.rl=rl;
  const low=!rl&&!ult&&mag<=Math.ceil(B.mag/4),k=(ult?'u':rl?'r':low?'l':'n')+n;
  if(k!==S.k){S.k=k;amEl.classList.toggle('rl',rl);amEl.classList.toggle('low',low);amEl.classList.toggle('amu',ult);amX.classList.toggle('rl',rl);amX.classList.toggle('low',low);
    amN.textContent=ult?'∞':n;amL.textContent=ult?p.H.kit[4][1]:rl?'Reloading':AMN[p.hk]}
  if(rl){amB.style.transform=`scaleX(${u.toFixed(3)})`;amX.style.setProperty('--rp',(u*360).toFixed(1)+'deg')}
}"""

h('ammo counter element and tick',
"hud.root.appendChild(repEl); // Gym Rep counter",
"hud.root.appendChild(repEl); // Gym Rep counter" + JS)

h('ammo counter runs with the HUD',
"  {const on=p.hk==='gym'&&p.alive;repEl.hidden=!on;",
"  ammoTick(p);\n  {const on=p.hk==='gym'&&p.alive;repEl.hidden=!on;")

def apply(path):
    s = open(path, encoding='utf-8').read()
    for name, a, b in H:
        c = s.count(a)
        assert c == 1, f'{name}: anchor found {c} times'
        s = s.replace(a, b)
    for bad in ('bandActive', 'arOk', 'arTry', 'h_ns_quickreload', 'Quick Reload'):
        assert bad not in s, bad + ' still present'
    open(path, 'w', encoding='utf-8').write(s)
    print('applied', len(H), 'hunks to', path)

if __name__ == '__main__':
    import sys
    apply(sys.argv[1])
```
