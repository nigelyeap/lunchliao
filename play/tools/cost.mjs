// split frame cost: sim step (CPU) vs render with glFinish (CPU submit + GPU), per tier. env MAPS, TIERS
const MAPS=(process.env.MAPS||'hawker').split(','),TI=(process.env.TIERS||'0,1,2').split(',').map(Number);
export default async({ev,sleep})=>{
 for(const id of MAPS){
  await ev(`(()=>{const C=__chope;C.camFix=null;C.autopilot=true;C.start('${id}')})()`);await sleep(5000);
  for(const ti of TI){
   await ev(`__chope.tier=${ti}`);await sleep(2500);
   const r=await ev(`(()=>{const C=__chope,gl=C.renderer.getContext();for(let i=0;i<5;i++){C.render();gl.finish()}
    let t=performance.now();for(let i=0;i<30;i++)C.step(1/60);const st=(performance.now()-t)/30;
    t=performance.now();for(let i=0;i<30;i++){C.render();gl.finish()}const rt=(performance.now()-t)/30;
    return{step:+st.toFixed(2),render:+rt.toFixed(2),pr:C.renderer.getPixelRatio(),buf:C.renderer.domElement.width+'x'+C.renderer.domElement.height}})()`);
   console.log(id,'tier',ti,JSON.stringify(r));
  }}}
