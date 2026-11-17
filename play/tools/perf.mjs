// frame time in a real 5v5 match (autopilot player + 9 bots). env MAPS, TIERS (e.g. "1,2"). Run with FAST=1 so rAF is not capped at 60.
const MAPS=(process.env.MAPS||'hawker,wetmarket').split(','),TI=(process.env.TIERS||'1,2').split(',').map(Number);
export default async({ev,sleep})=>{
 for(const id of MAPS)for(const ti of TI){
  await ev(`(()=>{const C=__chope;C.camFix=null;C.autopilot=true;C.start('${id}');C.tier=${ti}})()`);
  await sleep(6000);
  const r=await ev(`new Promise(r=>{const t=[];function f(n){t.push(n);if(n-t[0]<6000)requestAnimationFrame(f);else r(t)}requestAnimationFrame(f)}).then(t=>{const d=t.slice(1).map((x,i)=>x-t[i]).sort((a,b)=>a-b);const C=__chope;return{avg:+(d.reduce((a,b)=>a+b)/d.length).toFixed(2),p95:+d[Math.floor(d.length*.95)].toFixed(2),n:d.length,tier:C.tier,pr:C.renderer.getPixelRatio(),buf:C.renderer.domElement.width+'x'+C.renderer.domElement.height,alive:C.ents.filter(e=>e.alive).length,ents:C.ents.length,calls:C.drawCalls,state:C.state}})`);
  console.log(id,'tier',ti,JSON.stringify(r));
 }}
