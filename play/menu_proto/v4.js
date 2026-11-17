// v4_backdrop life: cross-fading map layers and seeded light motes. Loads after proto.js.
(()=>{const B=document.body;
// a .bgs in the main frame waits until the picker closes, so the cross-fade is seen
const sync=()=>document.querySelectorAll('.bgs').forEach(c=>{const id=B.dataset.map;
 if(!id||c.dataset.cur===id||(c.closest('.f1')&&B.classList.contains('maps')))return;
 c.dataset.cur=id;[...c.children].slice(0,-1).forEach(x=>x.remove());
 const d=document.createElement('div');d.style.backgroundImage=`url(assets/maps/${id}.jpg)`;c.append(d)});
new MutationObserver(sync).observe(B,{attributes:true});sync();
let s=11;const r=()=>(s=s*16807%2147483647)/2147483647; // seeded so screenshots repeat
document.querySelectorAll('.motes').forEach(m=>{for(let i=0;i<30;i++){const e=document.createElement('span'),z=3+r()*7,t=7+r()*9;
 e.style.cssText=`left:${r()*1600}px;top:${200+r()*700}px;width:${z}px;height:${z}px;--t:${t}s;--dl:${-r()*t}s;--o:${.25+r()*.5};--dx:${r()*120-40}px`;m.append(e)}})})();
