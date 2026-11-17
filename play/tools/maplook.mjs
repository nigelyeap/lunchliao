// maplook shots per map: <id>_a (Blender ground_a camera, matched fov, bots where the Blender heroes stand), <id>_fp (first person from the
// ground_a eye), <id>_tp (third person behind the ground_b eye). Out: shots/play/. env MAPS, TIER (default 1), TAG (file suffix)
const OUT='/Users/nigelyeap/Documents/lunchliao-hd/shots/play/',TIER=+(process.env.TIER??1),TAG=process.env.TAG||'';
const MAPS=(process.env.MAPS||'hawker,voiddeck,wetmarket,carpark,classroom').split(',');
// [eye, target, lens, heroes [x,z]] from tools/blender/maps_toy/<id>.py
const CAM={hawker:{a:[[-27.2,1.6,-18],[-10,1.9,-19.6],20,[[-20.6,-18.6],[-17.6,-19.3],[-22.4,-19.2]]],b:[[-22,1.6,1.6],[0,1.5,0],20,[[-15.8,1.2],[-12.6,-2.6]]]},
 voiddeck:{a:[[-41,1.6,7.6],[-14,1.5,7.8],20,[[-31.5,6.2],[-27.5,8.6],[-34,9]]],b:[[-20.2,1.6,.9],[0,3,.9],22,[[-12,2.4],[-6.2,-.4]]]},
 wetmarket:{a:[[-35.6,1.6,-.7],[-8,1.7,-.2],22,[[-30,-1],[-25.2,1.5],[-18.5,-.6]]],b:[[-30.5,1.6,12.6],[-6,1.6,12.2],22,[[-22,13],[-15.5,11.4]]]},
 carpark:{a:[[-7.5,1.6,-3.6],[3,1.2,-1],24,[[-1.6,-1.4],[1.6,-2.4]]],b:[[-32.5,1.6,-7.6],[-20,1.2,-10.4],24,[[-24.3,-8.2],[-21.2,-10.2]]]},
 classroom:{a:[[-12.5,1.6,-7.6],[6,1.3,-7.9],20,[[-6.5,-8.4],[-3.2,-7.2],[1,-8.6]]],b:[[19.3,1.6,-8.6],[19.8,1.2,6],20,[[17,-2.6],[22.2,2.8],[22,-8]],.6]}};
const fov=l=>2*Math.atan(36*9/16/2/l)*180/Math.PI;
export default async({ev,sleep,shot})=>{
 for(const id of MAPS){const C=CAM[id];
  await ev(`(()=>{const C=__chope;C.camFix=null;C.autopilot=false;C.start('${id}');C.tier=${TIER}})()`);
  await sleep(4000);await ev(`__chope.step(2.5)`);
  const put=(cam,pts)=>`(()=>{const C=__chope,E=C.ents.filter(e=>!e.isPlayer&&e.alive),P=${JSON.stringify(pts)},e0=${JSON.stringify(cam[0])};
    P.forEach((p,i)=>{const b=E[i];if(!b)return;b.pos.set(p[0],0,p[1]);b.vel.set(0,0,0);b.yaw=Math.atan2(e0[0]-p[0],e0[2]-p[1])});
    for(const b of E.slice(P.length))b.pos.set(b.pos.x,-50,b.pos.z)})()`;
  // a: Blender camera
  const A=C.a;await ev(put(A,A[3]));
  await ev(`(()=>{const C=__chope;C.camFix=${JSON.stringify([...A[0],...A[1]])};C.camera.fov=${fov(A[2])};C.camera.updateProjectionMatrix();if(C.vm)C.vm.visible=false})()`);
  await sleep(400);await ev(put(A,A[3]));await sleep(150);await shot(OUT+id+'_a'+TAG+'.png');
  // fp: player at the ground_a eye (kept inside the map bounds), looking at the target
  await ev(`(()=>{const C=__chope,p=C.player,B=C.map.bounds,e=${JSON.stringify(A[0])},t=${JSON.stringify(A[1])};C.camFix=null;C.camera.fov=78;C.camera.updateProjectionMatrix();
    const x=Math.max(B[0]+1.5,Math.min(B[1]-1.5,e[0])),z=Math.max(B[2]+1.5,Math.min(B[3]-1.5,e[2]));p.pos.set(x,0,z);p.vel.set(0,0,0);p.yaw=Math.atan2(-(t[0]-x),-(t[2]-z));p.pitch=-.05})()`);
  await ev(put([[A[0][0],0,A[0][2]]],A[3]));await sleep(500);await ev(put(A,A[3]));await sleep(150);await shot(OUT+id+'_fp'+TAG+'.png');
  // tp: behind and above the ground_b eye
  const Bc=C.b,e=Bc[0],t=Bc[1],dx=t[0]-e[0],dz=t[2]-e[2],L=Math.hypot(dx,dz),bk=Bc[4]??2.5,cam=[e[0]-dx/L*bk,e[1]+(bk<1?.9:1.6),e[2]-dz/L*bk];
  await ev(`(()=>{const C=__chope,p=C.player;p.pos.set(${e[0]+dx/L*1.2},0,${e[2]+dz/L*1.2});p.yaw=${Math.atan2(-dx,-dz)};C.camFix=${JSON.stringify([...cam,...t])};C.camera.fov=60;C.camera.updateProjectionMatrix();if(C.vm)C.vm.visible=false})()`);
  await ev(put(Bc,Bc[3]));await sleep(400);await ev(put(Bc,Bc[3]));await sleep(150);await shot(OUT+id+'_tp'+TAG+'.png');
  await ev(`(()=>{const C=__chope;C.camFix=null;C.camera.fov=78;C.camera.updateProjectionMatrix()})()`);
 }}
