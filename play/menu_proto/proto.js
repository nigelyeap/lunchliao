// shared by every menu mockup. Real names from chope.html. Flavour lines and player numbers are sample copy.
const MAPS=[
 {id:'hawker',name:'Hawker Centre',short:'Hawker Centre',code:'HC',tag:'Food centre',line:'Blk 51 at lunch hour. Long rows of tables and tight corners at the stalls.'},
 {id:'carpark',name:'Changkat Food Centre Roof Carpark',short:'Roof Carpark',code:'RC',tag:'Rooftop',line:'Open rooftop at golden hour. Parked cars and planters are the only cover.'},
 {id:'classroom',name:'Level 5 Classroom Block',short:'Classroom Block',code:'CB',tag:'School',line:'Corridors, railings and a long drop to the courtyard. Mind the stairwells.'},
 {id:'voiddeck',name:'Blk 404 Void Deck',short:'Void Deck',code:'VD',tag:'HDB estate',line:'Pillars, a playground and the coffee shop downstairs. A proper neighbourhood scrap.'},
 {id:'wetmarket',name:'Pasar Lorong Tiga',short:'Wet Market',code:'PL',tag:'Wet market',line:'Fish stalls, veg crates and narrow lanes. Everything happens up close.'}];
const fill=(t,m,i)=>t.replace(/\{(\w+)\}/g,(_,k)=>k==='n'?String(i+1).padStart(2,'0'):k==='i'?i+1:m[k]??'');
// <template data-maps> ... {id} {name} {short} {code} {tag} {line} {n} {i} ... </template> is stamped once per map
document.querySelectorAll('template[data-maps]').forEach(t=>{t.insertAdjacentHTML('beforebegin',MAPS.map((m,i)=>fill(t.innerHTML,m,i)).join(''));t.remove()});
function pick(id){const i=MAPS.findIndex(x=>x.id===id),m=MAPS[i];if(!m)return;document.body.dataset.map=id;
 document.querySelectorAll('[data-map]').forEach(e=>e.classList.toggle('on',e.dataset.map===id));
 document.querySelectorAll('[data-f]').forEach(e=>{const k=e.dataset.f,src=`assets/maps/${id}.jpg`;
  if(k==='img')e.src=src;else if(k==='bg')e.style.backgroundImage=`url(${src})`;else e.textContent=fill('{'+k+'}',m,i)})}
document.addEventListener('click',e=>{const m=e.target.closest('[data-map]'),g=e.target.closest('[data-go]'),b=e.target.closest('[data-bots]');
 if(m)pick(m.dataset.map);
 if(b){b.parentNode.querySelectorAll('[data-bots]').forEach(x=>x.classList.toggle('on',x===b));document.querySelectorAll('[data-f-bots]').forEach(x=>x.textContent=b.dataset.bots)}
 if(g)location.hash=g.dataset.go});
const sync=()=>document.body.classList.toggle('maps',location.hash==='#maps');addEventListener('hashchange',sync);sync();
pick(new URLSearchParams(location.search).get('map')||'hawker');
const fit=()=>{const s=Math.min(innerWidth/1600,innerHeight/900);document.querySelector('.stage').style.transform=`scale(${s})`};addEventListener('resize',fit);fit();
