// headless Chrome driver for play/. Own profile, kill by pid. usage: [PORT=5302 DPR=2 FAST=1] node play/tools/cdp.mjs scenario.mjs [query]
import { spawn, execSync } from 'node:child_process';
import { mkdirSync, writeFileSync, readFileSync, existsSync, unlinkSync } from 'node:fs';
const SCRATCH='/tmp/lunchliao-scratch';
const PROFILE=`${SCRATCH}/chrome-profile-play2`,PIDFILE=`${SCRATCH}/chrome-play2.pid`;
const CHROME='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',CDP=+(process.env.CDP||9403),PORT=+(process.env.PORT||5302),DPR=+(process.env.DPR||2);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function up(u){try{await fetch(u);return true}catch{return false}}
mkdirSync(PROFILE,{recursive:true});
if(existsSync(PIDFILE)){const old=+readFileSync(PIDFILE,'utf8');try{if(execSync(`ps -o command= -p ${old}`).toString().includes(PROFILE))process.kill(old,'SIGKILL')}catch{}unlinkSync(PIDFILE)}
const chrome=spawn(CHROME,['--headless=new',`--remote-debugging-port=${CDP}`,`--user-data-dir=${PROFILE}`,'--window-size=1600,900','--hide-scrollbars','--no-first-run','--no-default-browser-check','--use-angle=metal','--enable-gpu-rasterization','--ignore-gpu-blocklist','--autoplay-policy=no-user-gesture-required',...(process.env.FAST?['--disable-gpu-vsync','--disable-frame-rate-limit']:[]),'about:blank'],{stdio:'ignore'});
writeFileSync(PIDFILE,String(chrome.pid));
const cleanup=()=>{try{process.kill(chrome.pid,'SIGKILL')}catch{}try{unlinkSync(PIDFILE)}catch{}};
process.on('exit',cleanup);process.on('SIGINT',()=>process.exit(1));
for(let i=0;i<100&&!(await up(`http://localhost:${CDP}/json/version`));i++)await sleep(100);
const r=await fetch(`http://localhost:${CDP}/json/new?about:blank`,{method:'PUT'});const page=await r.json();
const ws=new WebSocket(page.webSocketDebuggerUrl);await new Promise((a,b)=>{ws.onopen=a;ws.onerror=b});
let id=0;const pend=new Map(),logs=[];
ws.onmessage=ev=>{const m=JSON.parse(ev.data);if(m.id&&pend.has(m.id)){pend.get(m.id)(m);pend.delete(m.id)}
 else if(m.method==='Runtime.consoleAPICalled'){const t=m.params.type;if(t==='error'||t==='warning'||t==='warn')logs.push(t+': '+m.params.args.map(a=>a.value??a.description??'').join(' ').slice(0,400))}
 else if(m.method==='Runtime.exceptionThrown'){const d=m.params.exceptionDetails;logs.push('EXC: '+(d.exception?.description||d.text).slice(0,600))}
 else if(m.method==='Log.entryAdded'){const e=m.params.entry;if(e.level==='error')logs.push('LOG: '+e.text+' '+(e.url||''))}};
const send=(method,params={})=>new Promise((res,rej)=>{const i=++id;pend.set(i,res);ws.send(JSON.stringify({id:i,method,params}));setTimeout(()=>{if(pend.delete(i))rej(new Error('timeout '+method))},120000)});
const ev=async e=>{const m=await send('Runtime.evaluate',{expression:e,returnByValue:true,awaitPromise:true});if(m.result?.exceptionDetails)throw new Error(JSON.stringify(m.result.exceptionDetails).slice(0,800));return m.result?.result?.value};
await send('Runtime.enable');await send('Log.enable');await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride',{width:1600,height:900,deviceScaleFactor:DPR,mobile:false});
// PNG capture of a busy WebGL page hangs headless Chrome, so capture JPEG q95 and convert .png targets with sips
const shot=async(f)=>{const s=await send('Page.captureScreenshot',{format:'jpeg',quality:95}),png=f.endsWith('.png'),j=png?f.slice(0,-4)+'.cap.jpg':f;writeFileSync(j,Buffer.from(s.result.data,'base64'));
 if(png){execSync(`sips -s format png "${j}" --out "${f}" >/dev/null`);unlinkSync(j)}console.log('shot',f)};
const q=process.argv[3]||'q';
await send('Page.navigate',{url:`http://localhost:${PORT}/chope.html?${q}`});
let ok=false;for(let i=0;i<600&&!ok;i++){await sleep(100);ok=await ev('!!window.chopeBooted').catch(()=>false)}
console.log('booted',ok);
const sc=await import(process.argv[2]);
try{await sc.default({ev,shot,sleep,send,logs})}catch(e){console.log('SCENARIO ERR',e.message)}
console.log('--- console errors/warnings ('+logs.length+')');for(const l of [...new Set(logs)])console.log(l);
process.exit(0);
