// Sign definitions. Each sign: {name, w, h, glow, html(body markup), css}.
// All wording is listed in WORDING.md. Keep both in sync.

const INK = '#3a2a20';

// ---------- flat illustrations (viewBox 0 0 200 200) ----------
const S = `stroke="${INK}" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"`;
const slices = (fill, edge) =>
  [[-14, 62, 96], [4, 96, 88], [18, 128, 98]]
    .map(([r, x, y]) => `<g transform="rotate(${r} ${x} ${y})"><rect x="${x - 26}" y="${y - 15}" width="52" height="30" rx="13" fill="${fill}" ${S}/><path d="M${x - 18} ${y - 6} Q${x} ${y - 11} ${x + 18} ${y - 6}" fill="none" stroke="${edge}" stroke-width="4" stroke-linecap="round"/></g>`).join('');
const plate = (bg, kind) => `<svg viewBox="0 0 200 200"><rect width="200" height="200" rx="20" fill="${bg}"/>
<ellipse cx="100" cy="136" rx="84" ry="40" fill="#efe6d2" ${S}/><ellipse cx="100" cy="132" rx="62" ry="27" fill="#d8ccb2"/>
<path d="M44 128 Q54 70 100 66 Q146 70 156 128 Q100 150 44 128Z" fill="#fbf5e4" ${S}/>
<g fill="#e7dcc0"><circle cx="78" cy="94" r="3"/><circle cx="108" cy="82" r="3"/><circle cx="126" cy="108" r="3"/><circle cx="90" cy="116" r="3"/></g>
${kind === 'steamed' ? slices('#f3dfa8', '#fff3cc') : ''}${kind === 'roast' ? slices('#c9782f', '#e8a24c') : ''}
${kind === 'pork' ? `<g>${[[-8, 62, 96], [6, 100, 90], [14, 136, 100]].map(([r, x, y]) => `<g transform="rotate(${r} ${x} ${y})"><rect x="${x - 25}" y="${y - 14}" width="50" height="28" rx="8" fill="#9a4a2c" ${S}/><rect x="${x - 21}" y="${y - 3}" width="42" height="7" rx="3" fill="#f0d9b0"/><path d="M${x - 20} ${y - 9} h40" stroke="#d9923f" stroke-width="4" stroke-linecap="round"/></g>`).join('')}</g>` : ''}
${kind === 'leg' ? `<g transform="rotate(-18 100 90)"><path d="M52 98 Q50 62 96 64 Q128 66 128 92 Q126 118 90 116 Q58 116 52 98Z" fill="#c9782f" ${S}/><rect x="120" y="82" width="38" height="14" rx="7" fill="#f6ecd2" ${S}/><circle cx="162" cy="86" r="9" fill="#f6ecd2" ${S}/></g>` : ''}
<g><circle cx="38" cy="150" r="13" fill="#b6c98a" ${S}/><circle cx="38" cy="150" r="6" fill="#d8e6b4"/><circle cx="62" cy="160" r="13" fill="#b6c98a" ${S}/><circle cx="62" cy="160" r="6" fill="#d8e6b4"/></g>
<g><path d="M150 148 h34 a4 4 0 0 1 4 4 q-2 16 -21 16 q-19 0 -21 -16 a4 4 0 0 1 4 -4Z" fill="#e4e0d4" ${S}/><ellipse cx="167" cy="150" rx="15" ry="5" fill="#c4391f"/></g></svg>`;

const soup = bg => `<svg viewBox="0 0 200 200"><rect width="200" height="200" rx="20" fill="${bg}"/>
<path d="M30 100 H170 Q166 170 100 172 Q34 170 30 100Z" fill="#efe6d2" ${S}/><path d="M40 118 H160" stroke="#3f8a78" stroke-width="7" stroke-linecap="round"/>
<ellipse cx="100" cy="100" rx="70" ry="16" fill="#e8c46a" ${S}/><ellipse cx="100" cy="100" rx="52" ry="9" fill="#f3d98f"/>
<g fill="#7fae5a" stroke="${INK}" stroke-width="3"><circle cx="78" cy="98" r="6"/><circle cx="112" cy="102" r="6"/><circle cx="96" cy="94" r="5"/></g>
<g stroke="#e9e3d3" stroke-width="5" stroke-linecap="round" fill="none" opacity=".85"><path d="M80 78 q-10 -14 0 -26 q10 -12 0 -22"/><path d="M110 76 q-10 -14 0 -26 q10 -12 0 -22"/></g></svg>`;

const wrap = (svg, label, zh) => `<div class="tile">${svg}<div class="cap"><b class="zh">${zh}</b><span>${label}</span></div></div>`;

// ---------- sign_main ----------
const main = {
  name: 'sign_main', w: 2048, h: 1024, glow: true,
  css: `
  .frame{position:absolute;inset:0;background:linear-gradient(#4a6f69,#33504b);border-radius:26px}
  .frame i{position:absolute;width:20px;height:20px;border-radius:50%;background:radial-gradient(#9fb3a8,#52665f)}
  .panel{position:absolute;left:44px;top:44px;right:44px;bottom:44px;border-radius:10px;background:linear-gradient(#f2d476,#e6bd58);overflow:hidden}
  .band{position:absolute;left:0;right:0;top:0;height:470px;background:linear-gradient(#b8432f,#9e3626)}
  .band:after{content:"";position:absolute;left:0;right:0;bottom:-14px;height:14px;background:#7d2a1d}
  .plate{position:absolute;left:34px;top:30px;width:330px;height:140px;border-radius:18px;background:#2f4a46;border:6px solid #e9dcb4;display:flex;align-items:center;justify-content:center;font:900 74px/1 'Disp';color:#f3e6bd;white-space:nowrap}
  .zhname{position:absolute;left:360px;right:360px;top:30px;white-space:nowrap;text-align:center;font:900 180px/1.05 'SerifSC';color:#f7e9bd;text-shadow:7px 7px 0 #5d1b10,-3px -3px 0 #5d1b10,3px -3px 0 #5d1b10,-3px 3px 0 #5d1b10}
  .enname{position:absolute;left:0;right:0;top:262px;white-space:nowrap;text-align:center;font:900 92px/1 'Disp';color:#ffffff;letter-spacing:3px;text-shadow:5px 5px 0 #5d1b10}
  .sub{position:absolute;left:0;right:0;top:392px;text-align:center;font:700 46px/1 'SansSC';color:#f3d98f;letter-spacing:6px}
  .badge{position:absolute;right:34px;top:28px;width:210px;height:210px;border-radius:50%;background:#f3e6bd;border:8px solid #2f4a46;text-align:center;color:#9e3626;font:900 30px/1.1 'Disp';padding-top:34px;box-sizing:border-box}
  .badge b{display:block;font:900 60px/1 'Disp'} .badge span{display:block;font:900 30px/1.2 'SansSC';color:#2f4a46}
  .tiles{position:absolute;left:34px;right:34px;top:520px;bottom:24px;display:flex;gap:30px}
  .tile{flex:1;background:#fdf4d6;border:7px solid #5d1b10;border-radius:22px;padding:12px;display:flex;flex-direction:column}
  .tile svg{width:100%;flex:1;min-height:0;border-radius:14px}
  .cap{text-align:center;color:#5d1b10;margin-top:6px;font:700 30px/1.1 'SansSC'} .cap b{display:block;font-size:50px;font-weight:900} .cap span{letter-spacing:1px}
  `,
  html: () => `
  <div class="frame dark">${[[14, 14], [1994, 14], [14, 990], [1994, 990], [1014, 14], [1014, 990]].map(([x, y]) => `<i style="left:${x}px;top:${y}px"></i>`).join('')}</div>
  <div class="panel"><div class="band"></div>
   <div class="plate dark">#01-23</div>
   <div class="zhname">金成海南鸡饭</div>
   <div class="enname">KIM SENG HAINANESE CHICKEN RICE</div>
   <div class="sub">白鸡 · 烧鸡 · 烧肉</div>
   <div class="badge">SINCE<b>1987</b><span>创立于1987</span></div>
   <div class="tiles">
    ${wrap(plate('#cf6b4a', 'steamed'), 'Steamed Chicken', '白鸡')}
    ${wrap(plate('#4f8f86', 'roast'), 'Roast Chicken', '烧鸡')}
    ${wrap(plate('#d9a441', 'pork'), 'Roast Pork', '烧肉')}
    ${wrap(plate('#7a9bb0', 'leg'), 'Chicken Leg Rice', '鸡腿饭')}
    ${wrap(soup('#c98f53'), 'Soup of the Day', '例汤')}
   </div>
  </div>`,
};

// ---------- menu boards ----------
const boardCss = `
  .wood{position:absolute;inset:0;background:linear-gradient(135deg,#7a5738,#5c3f27);border-radius:22px}
  .board{position:absolute;left:38px;top:38px;right:38px;bottom:38px;background:#27382f;border-radius:10px;box-shadow:inset 0 0 0 6px #3b5146;overflow:hidden}
  .head{height:150px;background:#a8402e;display:flex;align-items:center;justify-content:space-between;padding:0 44px;color:#f4e6bd;border-bottom:8px solid #e3b04b}
  .head .t{font:900 64px/1 'Disp';letter-spacing:3px;white-space:nowrap} .head .z{font:900 92px/1 'SerifSC';white-space:nowrap}
  .rows{position:absolute;left:44px;right:44px;top:176px;bottom:84px;display:flex;flex-direction:column}
  .row{flex:1;display:flex;align-items:center;justify-content:space-between;border-bottom:4px dashed #6c8478;color:#f1e6c6}
  .row:last-child{border:0}
  .row .n b{display:block;font:900 64px/1.05 'SansSC'} .row .n span{display:block;font:700 34px/1.1 'SansSC';color:#d8c99f;letter-spacing:1px}
  .row .p{font:900 76px/1 'Disp';color:#f0bd4f;white-space:nowrap} .row .p i{font-style:normal;font-size:46px;color:#e9805f;margin-right:4px}
  .foot{position:absolute;left:0;right:0;bottom:0;height:70px;background:#1d2a23;color:#cdbf94;display:flex;align-items:center;justify-content:center;font:700 32px/1 'SansSC';letter-spacing:2px}
`;
const menu = (name, en, zh, rows, foot) => ({
  name, w: 1024, h: 1024, glow: false, css: boardCss,
  html: () => `<div class="wood dark"></div><div class="board"><div class="head"><span class="t">${en}</span><span class="z">${zh}</span></div>
  <div class="rows">${rows.map(([z, e, p]) => `<div class="row"><div class="n"><b>${z}</b><span>${e}</span></div><div class="p">${p === 'FREE' ? '<i></i>FREE' : `<i>$</i>${p}`}</div></div>`).join('')}</div>
  <div class="foot">${foot}</div></div>`,
});
const menus = [
  menu('sign_menu_1', 'CHICKEN RICE', '鸡饭', [
    ['白鸡饭', 'Steamed Chicken Rice', '4.50'], ['烧鸡饭', 'Roast Chicken Rice', '4.50'],
    ['鸡腿饭', 'Chicken Leg Rice', '5.50'], ['烧肉饭', 'Roast Pork Rice', '5.00'], ['套餐', 'Set Meal: rice, chicken, veg, soup', '6.50']],
    'Chilli and ginger sauce free 辣椒姜蓉免费'),
  menu('sign_menu_2', 'SIDES', '配菜', [
    ['蚝油菜心', 'Choy Sum in Oyster Sauce', '4.00'], ['卤蛋', 'Braised Egg', '1.00'], ['卤豆腐', 'Braised Tofu', '1.50'],
    ['黄瓜', 'Cucumber Slices', '1.00'], ['例汤', 'Soup of the Day', '1.50'], ['加饭', 'Extra Rice', '0.80']],
    'Prices in Singapore dollars'),
  menu('sign_menu_3', 'WHOLE BIRD', '整鸡', [
    ['整只鸡', 'Whole Chicken', '34.00'], ['半只鸡', 'Half Chicken', '18.00'], ['四分之一只鸡', 'Quarter Chicken', '9.50'],
    ['烧肉', 'Roast Pork (200g)', '9.00'], ['打包', 'Takeaway Box 打包盒', '0.30']],
    'Orders 30 minutes ahead 请提前预订'),
];

// ---------- grade sticker ----------
const grade = {
  name: 'sign_grade', w: 512, h: 512, glow: false,
  css: `
  .st{position:absolute;inset:14px;background:#f0e5c5;border:10px solid #2f7a68;border-radius:34px}
  .hd{position:absolute;left:0;right:0;top:0;height:92px;background:#2f7a68;color:#f6ecc9;text-align:center;font:900 38px/1 'Disp';padding-top:18px;box-sizing:border-box;letter-spacing:2px}
  .hd span{display:block;font:700 22px/1.3 'SansSC';letter-spacing:2px}
  .disc{position:absolute;left:112px;top:104px;width:260px;height:260px;border-radius:50%;background:#2f7a68;border:12px solid #dca93c;display:flex;align-items:center;justify-content:center;color:#f6ecc9;font:900 210px/1 'Disp'}
  .ft{position:absolute;left:0;right:0;bottom:16px;text-align:center;color:#2f4a40}
  .ft b{display:block;font:900 40px/1.1 'SansSC'} .ft span{display:block;font:700 24px/1.3 'SansSC';letter-spacing:1px}
  .star{position:absolute;font:900 40px 'Disp';color:#dca93c}
  `,
  html: () => `<div class="st"><div class="hd">FOOD HYGIENE<span>GRADE</span></div><div class="disc">A</div>
  <div class="ft"><b>食品卫生等级</b><span>Gred Kebersihan Makanan</span></div></div>`,
};

// ---------- tray return ----------
const trayIcon = `<svg viewBox="0 -4 220 180" width="230"><g ${S} transform="translate(0 36)"><path d="M14 92 H206 L190 130 H30Z" fill="#c9782f"/><path d="M52 92 Q54 54 110 54 Q166 54 168 92Z" fill="#efe6d2"/><ellipse cx="110" cy="54" rx="24" ry="7" fill="#e8c46a"/></g>
<g stroke="${INK}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" fill="#f6ecc9"><path d="M110 0 v34 M110 34 l-16 -16 M110 34 l16 -16" fill="none" transform="translate(0 0)"/></g></svg>`;
const lang = (cls, color, text, tag) => `<div class="ln" style="background:${color}"><span class="tg">${tag}</span><div class="${cls}">${text}</div></div>`;
const tray = {
  name: 'sign_tray', w: 1024, h: 1024, glow: false,
  css: `
  .post{position:absolute;inset:0;background:#efe3c2;border-radius:18px}
  .top{position:absolute;left:0;right:0;top:0;height:230px;background:#2f7a68;display:flex;align-items:center;justify-content:center;gap:34px;color:#f6ecc9}
  .top b{font:900 78px/1.02 'Disp';letter-spacing:2px}
  .ls{position:absolute;left:34px;right:34px;top:256px;bottom:130px;display:flex;flex-direction:column;gap:14px}
  .ln{flex:1;border-radius:18px;display:flex;align-items:center;padding:0 28px;position:relative;color:#fff}
  .ln .tg{position:absolute;right:16px;top:8px;font:700 20px 'SansSC';opacity:.85;letter-spacing:2px}
  .e{font:900 54px/1.1 'Disp'} .z{font:900 74px/1.1 'SansSC'} .m{font:900 50px/1.15 'SansSC'} .t{font:700 52px/1.3 'TamilSans';font-weight:700}
  .ty{position:absolute;left:0;right:0;bottom:0;height:112px;display:flex;align-items:center;justify-content:center;gap:26px;color:#2f4a40;font:900 38px/1 'SansSC'}
  .ty .tm{font:700 36px/1 'TamilSans'} .ty em{font-style:normal;color:#b8432f}
  `,
  html: () => `<div class="post"><div class="top dark">${trayIcon}<b>TRAY<br>RETURN</b></div>
  <div class="ls">
   ${lang('e', '#b8432f', 'Please return your tray here.', 'EN')}
   ${lang('z', '#2f4a40', '请将托盘归还此处。', '中文')}
   ${lang('m', '#c98a2b', 'Sila pulangkan dulang anda di sini.', 'BM')}
   ${lang('t', '#3d6f8c', 'தயவுசெய்து உங்கள் தட்டை இங்கே திருப்பி வைக்கவும்.', 'தமிழ்')}
  </div>
  <div class="ty">Thank you <em>·</em> 谢谢 <em>·</em> Terima kasih <em>·</em> <span class="tm">நன்றி</span></div></div>`,
};

// ---------- no smoking ----------
const nosmoke = {
  name: 'sign_nosmoke', w: 1024, h: 1024, glow: false,
  css: `
  .post{position:absolute;inset:0;background:#f0e5c8;border:22px solid #b8432f;border-radius:30px;box-sizing:border-box}
  .ic{position:absolute;left:0;right:0;top:44px;text-align:center}
  .tx{position:absolute;left:30px;right:30px;top:410px;bottom:30px;display:flex;flex-direction:column;justify-content:space-around;text-align:center;color:#2a1d17}
  .a{font:900 110px/1 'Disp';color:#b8432f;letter-spacing:3px} .b{font:900 100px/1.05 'SansSC'} .c{font:900 70px/1.1 'SansSC';letter-spacing:2px} .d{font:700 66px/1.3 'TamilSans'}
  `,
  html: () => `<div class="post"><div class="ic"><svg viewBox="0 0 300 300" width="340"><circle cx="150" cy="150" r="128" fill="#f6ecd2" stroke="#b8432f" stroke-width="30"/>
   <g transform="rotate(-20 150 150)"><rect x="60" y="130" width="130" height="34" rx="6" fill="#efe6d2" stroke="${INK}" stroke-width="6"/><rect x="190" y="130" width="52" height="34" rx="6" fill="#c9782f" stroke="${INK}" stroke-width="6"/></g>
   <g fill="none" stroke="#6a5a4e" stroke-width="9" stroke-linecap="round" opacity=".85"><path d="M96 110 q-14 -18 0 -34 q14 -16 0 -32"/><path d="M130 110 q-14 -18 0 -34 q14 -16 0 -32"/></g>
   <path d="M62 238 L238 62" stroke="#b8432f" stroke-width="30" stroke-linecap="round"/></svg></div>
   <div class="tx"><div class="a">NO SMOKING</div><div class="b">禁止吸烟</div><div class="c">DILARANG MEROKOK</div><div class="d">புகைபிடிக்கக் கூடாது</div></div></div>`,
};

// ---------- table plates ----------
const tables = [1, 2, 3, 4, 5, 6].map(n => ({
  name: `sign_table_0${n}`, w: 256, h: 256, glow: false,
  css: `
  .pl{position:absolute;inset:10px;border-radius:34px;background:linear-gradient(#e8dcb8,#d5c698);border:10px solid #2f7a68}
  .pl small{position:absolute;left:0;right:0;top:14px;text-align:center;font:900 24px/1 'Disp';letter-spacing:6px;color:#2f7a68}
  .pl b{position:absolute;left:0;right:0;top:36px;text-align:center;font:900 170px/1.1 'Disp';color:#a8402e}
  .pl i{position:absolute;width:14px;height:14px;border-radius:50%;background:radial-gradient(#b9c0b0,#667066)}
  `,
  html: () => `<div class="pl"><small>TABLE</small><b>${n}</b><i style="left:14px;top:14px"></i><i style="right:14px;top:14px"></i><i style="left:14px;bottom:14px"></i><i style="right:14px;bottom:14px"></i></div>`,
}));

// ---------- drinks ----------
const drinkRows = [
  ['Kopi', '咖啡', '1.60', '2.10'], ['Kopi O', '咖啡乌', '1.40', '1.90'], ['Teh', '茶', '1.60', '2.10'], ['Teh O', '茶乌', '1.40', '1.90'],
  ['Teh Tarik', '拉茶', '1.90', '2.40'], ['Teh Halia', '姜茶', '2.00', '2.50'], ['Milo', '美禄', '2.20', '2.70'], ['Milo Dinosaur', '美禄恐龙', '', '4.00'],
  ['Horlicks', '好立克', '2.20', '2.70'], ['Soya Bean', '豆浆', '1.60', '1.80'], ['Sugarcane', '甘蔗水', '', '2.50'], ['Lime Juice', '酸柑汁', '', '2.20'],
  ['Barley', '薏米水', '', '1.80'], ['Air Bandung', 'Rose syrup milk', '', '2.20'],
];
const drinks = {
  name: 'sign_drinks', w: 2048, h: 1024, glow: true,
  css: `
  .frame{position:absolute;inset:0;background:linear-gradient(#4a6f69,#33504b);border-radius:26px}
  .panel{position:absolute;left:40px;top:40px;right:40px;bottom:40px;border-radius:10px;background:linear-gradient(#f2dc8a,#e8c564);overflow:hidden}
  .hd{height:150px;background:#b8432f;display:flex;align-items:center;justify-content:space-between;padding:0 50px;color:#f7e9bd;border-bottom:10px solid #7d2a1d}
  .hd .t{font:900 118px/1 'Disp';letter-spacing:6px;text-shadow:5px 5px 0 #5d1b10} .hd .z{font:900 120px/1 'SerifSC';text-shadow:5px 5px 0 #5d1b10}
  .cols{position:absolute;left:40px;right:40px;top:176px;bottom:100px;display:flex;gap:56px}
  .col{flex:1;display:flex;flex-direction:column}
  .ch{display:flex;justify-content:flex-end;gap:0;font:900 34px/1 'SansSC';color:#7d2a1d;height:46px;align-items:center}
  .ch span{width:136px;text-align:right}
  .r{flex:1;display:flex;align-items:center;border-bottom:4px dashed #b8923a;color:#3a1c10}
  .r .n{flex:1} .r .n b{display:block;font:900 42px/1.05 'Disp'} .r .n span{display:block;font:900 30px/1.1 'SansSC';color:#7d2a1d}
  .r .pr{width:136px;text-align:right;font:900 44px/1 'Disp';color:#9e3626} .r .pr.no{color:#b8923a}
  .ft{position:absolute;left:0;right:0;bottom:0;height:84px;background:#33504b;color:#f3e6bd;display:flex;align-items:center;justify-content:center;gap:34px;font:700 34px/1 'SansSC';letter-spacing:1px}
  `,
  html: () => {
    const col = rs => `<div class="col"><div class="ch"><span>热 HOT</span><span>冰 ICED</span></div>${rs.map(([e, z, h, c]) => `<div class="r"><div class="n"><b>${e}</b><span>${z}</span></div><div class="pr ${h ? '' : 'no'}">${h ? '$' + h : '-'}</div><div class="pr">$${c}</div></div>`).join('')}</div>`;
    return `<div class="frame dark"></div><div class="panel"><div class="hd"><span class="t">DRINKS</span><span class="z">饮料</span></div>
    <div class="cols">${col(drinkRows.slice(0, 7))}${col(drinkRows.slice(7))}</div>
    <div class="ft"><span>Kosong 无糖</span><span>Siew Dai 少甜</span><span>Gao 浓</span><span>Tapau 打包 +$0.20</span><span>Air Kosong 白开水 FREE</span></div></div>`;
  },
};

export const SIGNS = [main, ...menus, grade, tray, nosmoke, ...tables, drinks];
