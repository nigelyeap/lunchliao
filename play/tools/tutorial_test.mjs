// Headless check for play/tutorial.js. Plays every step with real key and mouse events sent over CDP, then tests skip, restart, quit and a normal match.
// usage: node play/tools/cdp.mjs play/tools/tutorial_test.mjs   (the page must have the tutorial hook, see play/TUTORIAL.md)
// env: MODE=play|skip|all (default all), HERO=nsboy, SHOTS=/dir for JPEG captures of key steps
const MODE=process.env.MODE||'all',HERO=process.env.HERO||'nsboy',FROM=process.env.FROM,SHOTS=process.env.SHOTS;
export default async({ev,shot,send,logs})=>{
  // game time, not wall time: a busy machine drops frames and the game clamps dt, so waits count clamped frame time
  const sleep=ms=>ev(`new Promise(r=>{let t=0,l=performance.now();const f=n=>{t+=Math.min(n-l,50);l=n;t>=${ms}?r():requestAnimationFrame(f)};requestAnimationFrame(f)})`);
  const fails=[],ok=(c,m)=>{if(!c){fails.push(m);console.log('FAIL',m)}};
  const VK={Enter:13,Tab:9,Space:32,Escape:27};
  const key=(code,down=true)=>send('Input.dispatchKeyEvent',{type:down?'rawKeyDown':'keyUp',code,key:code.replace(/^(Key|Digit)/,''),windowsVirtualKeyCode:VK[code]||(code.startsWith('Key')?code.charCodeAt(3):code.startsWith('Digit')?code.charCodeAt(5):0)});
  const tap=async(code,ms=60)=>{await key(code);await sleep(ms);await key(code,false)};
  let mx=800,my=450,btn=false;
  const mouse=(type,o={})=>send('Input.dispatchMouseEvent',{type,x:mx,y:my,button:btn||type!=='mouseMoved'?'left':'none',buttons:btn?1:0,clickCount:1,...o});
  const press=async()=>{if(!btn){btn=true;await mouse('mousePressed')}},release=async()=>{if(btn){await mouse('mouseReleased');btn=false}};
  const moveTo=async(x,y)=>{mx=x;my=y;await mouse('mouseMoved')};
  // drag with the button held: this is how the game looks around when the browser gives no pointer lock (headless)
  const drag=async(dx,dy)=>{while(Math.abs(dx)>.5||Math.abs(dy)>.5){
    if(mx<200||mx>1400||my<150||my>750){await release();await moveTo(800,450)}
    await press();const sx=Math.max(-120,Math.min(120,dx)),sy=Math.max(-120,Math.min(120,dy));await moveTo(mx+sx,my+sy);dx-=sx;dy-=sy}};
  const S=()=>ev(`(()=>{const R=__tutorial.run,G=__tut,p=G.player;if(!R)return{run:false,state:G.state};const f=R.foe,z=G.zones.find(z=>z.id==='A');
    return{run:true,i:R.i,n:R.steps.length,id:R.cur.id,okT:R.okT,ok:R.ok.filter(Boolean).length,state:G.state,paused:G.paused,sens:G.profile.sens,slEnd:p.slEnd,vy:p.vel.y,air:p.airT,x:p.pos.x,y:p.pos.y,z:p.pos.z,yaw:p.yaw,pitch:p.pitch,hp:p.hp,alive:p.alive,
      eye:G.camera.position.toArray(),foe:f&&{x:f.pos.x,y:f.pos.y,z:f.pos.z,alive:f.alive,hp:f.hp},A:{x:z.p.x,z:z.p.z,prog:z.prog,owner:z.owner},score:[G.score[1],G.score[2]]}})()`);
  const wrap=a=>Math.atan2(Math.sin(a),Math.cos(a));
  const look=async(yaw,pitch=0)=>{for(let k=0;k<14;k++){const s=await S(),dy=wrap(yaw-s.yaw),dp=pitch-s.pitch;if(Math.abs(dy)<.012&&Math.abs(dp)<.012)break;const c=.0022*s.sens;await drag(-dy/c,-dp/c);await sleep(60)}};
  const aim=async(x,y,z)=>{const s=await S(),dx=x-s.eye[0],dy=y-s.eye[1],dz=z-s.eye[2];await look(Math.atan2(-dx,-dz),Math.atan2(dy,Math.hypot(dx,dz)))};
  const fire=async(hold=700)=>{await press();await sleep(hold);await release();await sleep(120)};
  // turn first, then walk: W only goes down while the heading is close, so a slow machine cannot overshoot far. Stuck for a while: hop and sidestep.
  const walk=async(x,z,r=1,max=30000)=>{let id0,w=false,lx,lz,still=0;const W=async d=>{if(w!==d){w=d;await key('KeyW',d)}};
    try{for(let t=0;t<max;t+=120){const s=await S(),d=Math.hypot(x-s.x,z-s.z);id0??=s.id;if(!s.run||s.id!==id0||d<r)break;
      const yaw=Math.atan2(-(x-s.x),-(z-s.z));if(process.env.TRACE)console.log('  walk',s.id,s.x.toFixed(2),s.z.toFixed(2),'yaw',s.yaw.toFixed(2),'want',yaw.toFixed(2),'to',x,z);if(Math.abs(wrap(yaw-s.yaw))>.3)await W(false);await look(yaw,0);await release();await W(true);
      still=lx!==undefined&&Math.hypot(s.x-lx,s.z-lz)<.05?still+1:0;lx=s.x;lz=s.z;if(still>6){still=0;await key('KeyA');await tap('Space');await sleep(500);await key('KeyA',false)}
      await sleep(Math.min(300,Math.max(50,d*50)));if(d<6)await W(false)}}finally{await W(false);await release()}}; // short bursts near the goal
  const until=async(f,max=15000)=>{for(let t=0;;t+=100){const s=await S();if(f(s))return s;if(t>max)return null;await sleep(100)}};
  const snap=async n=>{if(SHOTS){await release();await sleep(250);await shot(`${SHOTS}/${n}.jpg`)}};
  const head=()=>ev(`(()=>{const f=__tutorial.run.foe;const h=window.__chope&&__chope.hitSpheres?__chope.hitSpheres(f):null;const s=h&&(h.find(s=>s.head)||h[h.length-1]);const c=s&&(s.c||s.p||s.pos);return c?[c.x,c.y,c.z]:[f.pos.x,f.pos.y+1.75,f.pos.z]})()`);
  const chest=async()=>{const s=await S();return[s.foe.x,s.foe.y+1.15,s.foe.z]};
  const shoot=async(at,hold)=>{const c=await at();await aim(...c);await fire(hold)};

  // how each step gets done. Anything missing here just waits (and fails on timeout).
  const DO={
    look:async()=>{await drag(500,0);await drag(-500,60);await release()},
    move:async()=>{for(const k of['KeyW','KeyA','KeyS','KeyD'])await tap(k,500)},
    jump:()=>tap('Space'),
    crouch:()=>tap('KeyC',1100),
    slide:async()=>{await look(-Math.PI/2);await release();await key('KeyW');await sleep(700);await tap('KeyC');await sleep(900);await key('KeyW',false)},
    slidejump:async()=>{await look(Math.PI/2);await release();await sleep(900);await key('KeyW');await sleep(800);await key('KeyC');await sleep(250);await tap('Space');await key('KeyC',false);await sleep(500);await key('KeyW',false)},
    goto:()=>walk(-32,11.5,1.2),
    shoot:async()=>{for(let k=0;k<6&&(await S()).id==='shoot'&&!(await S()).okT;k++)await shoot(chest,700)},
    head:async()=>{for(let k=0;k<8&&(await S()).id==='head'&&!(await S()).okT;k++){const c=await head();await aim(...c);await fire(750)}},
    ko:async()=>{for(let k=0;k<12&&(await S()).id==='ko'&&!(await S()).okT;k++)await shoot(chest,700)},
    reload:async()=>{await tap('KeyR');await sleep(2200)},
    melee:()=>tap('KeyQ'),
    ab1:async()=>{await key('KeyW');await sleep(300);await tap('Digit1');await sleep(300);await key('KeyW',false)},
    ab2:()=>tap('Digit2',250),
    ab3:async()=>{await aim(...await chest());await release();await tap('Digit3',250)},
    ultc:async()=>{for(let k=0;k<12&&(await S()).id==='ultc'&&!(await S()).okT;k++)await shoot(chest,650)},
    ult:async()=>{await tap('Digit4');await sleep(300);await aim(...await chest());await press();await sleep(1500);await release()},
    wet:async()=>{const w=await ev(`(()=>{const w=__tut.HAZ.filter(h=>h.k==='wet').sort((a,b)=>Math.hypot(a.x+27,a.z-10.6)-Math.hypot(b.x+27,b.z-10.6))[0];return[w.x,w.z]})()`);await walk(w[0],w[1],.5)},
    hud:()=>tap('Enter'),points:()=>tap('Enter'),
    cap:async()=>{const s=await S();await walk(s.A.x,s.A.z,1)},
    contest:async()=>{const s=await S();await walk(s.A.x-1,s.A.z+.6,1.2);for(let k=0;k<14;k++){const t=await S();if(t.id!=='contest'||!t.foe.alive||Math.hypot(t.foe.x-t.A.x,t.foe.z-t.A.z)>4)break;await shoot(chest,650)}},
    heal:async()=>{for(const[x,z]of[[-19,10.5],[-19,5.8],[-14.65,5.5]])await walk(x,z,.7)},
    status:()=>sleep(500),
    board:()=>tap('Tab',900),
    fight:async()=>{const s=await S();await walk(s.A.x,s.A.z,1.5,12000)},
  };
  const LATE=['slide','cap','fight']; // these look better captured after the action
  const SNAP={slide:'02_slide',head:'03_headshot',shoot:'03_shoot',ab2:'04_ability',ult:'05_ult',cap:'06_capture',contest:'07_contest',heal:'08_pickup',fight:'09_practice_round'};
  const startVia=async hk=>{ // menu button, hero card, Start: all real clicks
    const c=async sel=>{const r=await ev(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(!e)return null;e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect();return[r.left+r.width/2,r.top+r.height/2]})()`);if(!r)return false;await moveTo(r[0],r[1]);btn=true;await mouse('mousePressed');await mouse('mouseReleased');btn=false;await sleep(250);return true};
    ok(await c('#tutBtn'),'menu has #tutBtn');ok(await ev(`!document.querySelector('#tutPick').hidden`),'hero picker opens');
    ok(await c(`#tutHeroes [data-h="${hk}"]`),'hero card '+hk);ok(await c('#tutGo'),'start button');
    const s=await until(s=>s.run,6000);ok(s,'tutorial started');await moveTo(800,450);return c};

  await ev(`localStorage.removeItem('chope-tut')`);
  if(MODE==='all'||MODE==='play'){
    if(SHOTS){await sleep(600);await shot(`${SHOTS}/00_menu.jpg`)}
    const before=await ev(`JSON.stringify([__tut.profile.hero,__tut.profile.map])`);
    const click=await startVia(HERO);
    if(SHOTS){await ev(`__tutorial.quit()`);await click('#tutBtn');await shot(`${SHOTS}/01_hero_picker.jpg`);await click('#tutGo');await until(s=>s.run,6000);await moveTo(800,450)}
    await press();await sleep(150);await release(); // first click: the game asks for pointer lock, headless falls back to drag look
    let s=await S();const n=s.n,seen=[];
    while(s&&s.run){
      const i=s.i,id=s.id;seen.push(id);console.log(`step ${i+1}/${n} ${id}`);
      if(FROM&&id!==FROM&&!seen.includes(FROM)){await ev(`__tutorial.skip()`);s=await until(s=>!s.run||s.i>i,5000);continue} // FROM=step: jump ahead when debugging one step
      if(SNAP[id]&&!LATE.includes(id))await snap(SNAP[id]);
      if(DO[id])await DO[id]();
      if(LATE.includes(id))await snap(SNAP[id]);
      s=await until(s=>!s.run||s.i>i,id==='fight'?150000:id==='cap'||id==='contest'?25000:12000);
      if(!s){ok(false,`step ${id} did not complete `+JSON.stringify(await S()));await release();await tap('Enter');await sleep(300);s=await until(s=>!s.run||s.i>i,3000);if(!s)break}
    }
    await release();
    ok(FROM||seen.length===n,`saw ${seen.length} of ${n} steps`);
    await sleep(500);
    ok(await ev(`!document.querySelector('#tutEnd').hidden`),'finish screen shows');
    ok(await ev(`__tut.state`)==='menu','back on the menu after the finish');
    ok(await ev(`JSON.stringify([__tut.profile.hero,__tut.profile.map])`)===before,'profile hero and map restored');
    ok(await ev(`JSON.parse(localStorage.getItem('chope-tut')).done`)===1,'completion saved');
    ok(await ev(`__tut.onDamage`)===null,'onDamage handed back');
    if(SHOTS)await shot(`${SHOTS}/10_finish.jpg`);
    await ev(`document.querySelector('#tutEnd [data-a=menu]').click()`);
  }
  if(MODE==='all'||MODE==='skip'){
    // every hero: skip through every step with the skip key. Each step must enter cleanly and leave on one key press.
    const heroes=await ev(`Object.keys(__tut.HEROES)`);
    for(const hk of heroes){
      await ev(`__tutorial.start(${JSON.stringify(hk)})`);let s=await until(s=>s.run,6000);if(!s){ok(false,'start '+hk);continue}
      const n=s.n;let steps=0;
      while(s&&s.run){const i=s.i;await tap('Enter',30);s=await until(s=>!s.run||s.i>i,2500);steps++;if(!s){ok(false,`${hk}: skip stuck at step ${i+1}`);await ev(`__tutorial.quit()`);break}}
      ok(steps===n,`${hk}: skipped ${steps} of ${n}`);
      ok(await ev(`!document.querySelector('#tutEnd').hidden&&__tut.state==='menu'`),hk+': finish after skipping');
      await ev(`document.querySelector('#tutEnd').hidden=true`);
      console.log('skip run',hk,n,'steps');
    }
    // restart and quit from the pause screen
    await ev(`__tutorial.start('nsboy')`);await until(s=>s.run,6000);await tap('Enter',30);await tap('Enter',30);await sleep(400);await tap('Enter',30);await sleep(300);
    await tap('KeyP');await sleep(300);
    ok(await ev(`!document.querySelector('#pause').hidden&&!document.querySelector('#tutRestart').hidden&&document.querySelector('#tutUI').hidden`),'pause shows Restart and hides the panel');
    await ev(`document.querySelector('#tutRestart').click()`);const r=await until(s=>s.run&&s.i===0&&!s.paused,6000);ok(r,'restart goes back to step 1');
    await tap('KeyP');await sleep(300);await ev(`document.querySelector('#quitBtn').click()`);await sleep(400);
    ok(await ev(`__tut.state==='menu'&&!__tutorial.run&&document.querySelector('#tutUI').hidden&&document.querySelector('#tutRestart').hidden`),'quit leaves the tutorial');
    // a normal match is untouched
    const hero=await ev(`__tut.profile.hero`);
    await ev(`__tut.RANGE=false;__tut.startMatch('hawker')`);await sleep(4500);
    ok(await ev(`__tut.state==='playing'&&__tut.ents.length===10&&!__tut.ents.some(e=>e.dummy)&&__tut.player.hk===${JSON.stringify(hero)}&&__tut.map.id==='hawker'&&document.querySelector('#tutUI').hidden&&__tut.matchT<300&&__tut.botSkill[2]===__tut.profile.bots`),'normal 5v5 match after the tutorial');
    await ev(`document.querySelector('#quitBtn').click()`);
  }
  const bad=logs.filter(l=>!/logo_lunchliao_preview|404/.test(l));ok(!bad.length,'console errors: '+bad.slice(0,3).join(' | '));
  console.log(fails.length?`TUTORIAL TEST: ${fails.length} FAILED`:'TUTORIAL TEST: all passed');
};
