// 방구석 물가 ISSUE 003 — 고구마 1kg 캐러셀 4장 렌더러 (1080×1350 PNG)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const DIR = __dirname;
const OUT = process.argv[2] || path.join(DIR, 'out');
fs.mkdirSync(OUT, { recursive: true });
const img = (n) => 'data:image/png;base64,' + fs.readFileSync(path.join(DIR, n + '.png')).toString('base64');

const D = {
  date: '2026.11.11',
  spec: '밤고구마(상품) 1kg',
  nat: 4270, seoul: 4954, andong: 2490,
};
D.diffNat = D.seoul - D.nat;      // 684
D.diffReg = D.seoul - D.andong;   // 2,464
if (D.diffNat !== 684 || D.diffReg !== 2464) throw new Error('차액 계산 불일치');
const won = (n) => n.toLocaleString('ko-KR');

const SOURCE = `자료: 한국농수산식품유통공사(aT) KAMIS 농산물 소매가격 · 조사 기준일 ${D.date} · ${D.spec}`;

const CSS = `
:root{--paper:#F4EEE4;--ink:#141414;--sub:#4a4a4a;--muted:#6b6b6b;--rule:#aaa59e;--green:#1E4E34;--olive:#8AA95A;--logo:#56703C;--badge:#E7E5C8}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1350px}
body{font-family:'Noto Sans CJK KR',sans-serif;color:var(--ink);background:var(--paper);position:relative;overflow:hidden;word-break:keep-all;-webkit-font-smoothing:antialiased}
.paper{position:absolute;inset:0;pointer-events:none;opacity:.55;mix-blend-mode:multiply}
.page{position:absolute;inset:0;padding:0 70px}
.hd{position:absolute;left:70px;right:70px;top:30px;height:88px;display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid var(--rule)}
.brand{display:flex;align-items:center;gap:20px;padding-bottom:12px}
.brand .ko{font-size:42px;font-weight:900;color:var(--green);line-height:1;letter-spacing:-1px}
.brand .en{font-size:18px;font-weight:700;letter-spacing:.3px;margin-top:8px;color:#222}
.issue{font-size:30px;font-weight:400;letter-spacing:.5px;padding-bottom:12px}
.ft{position:absolute;left:70px;right:70px;top:1252px;border-top:2px solid var(--rule);display:flex;justify-content:space-between;align-items:center;height:68px}
.ft span{font-size:26px;font-weight:500;letter-spacing:.3px}
.src{position:absolute;left:70px;right:70px;top:1210px;font-size:17px;color:var(--muted);letter-spacing:-.2px}
h1{position:absolute;left:70px;right:70px;font-weight:900;letter-spacing:-2px;line-height:1.16}
.subt{position:absolute;left:70px;right:70px;font-size:30px;color:var(--sub);font-weight:400;letter-spacing:-.6px;line-height:1.45}
.ph{position:absolute;overflow:hidden;background:#ddd}
.ph img{width:100%;height:100%;object-fit:cover;display:block}
.green{color:var(--green)}
.price{font-weight:900;color:var(--green);letter-spacing:-2px;line-height:1}
.price small{font-size:.62em;letter-spacing:0;margin-left:4px}
`;

const LOGO = `<svg width="86" height="74" viewBox="0 0 86 74"><path d="M43 2 L84 30 V72 H2 V30 Z" fill="var(--logo)"/><circle cx="43" cy="45" r="15" fill="#fff"/><rect x="42" y="52" width="2" height="9" fill="var(--logo)"/></svg>`;

const PAPER = `<svg class="paper" width="1080" height="1350"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="3" seed="7"/><feColorMatrix values="0 0 0 0 .55  0 0 0 0 .5  0 0 0 0 .43  0 0 0 .22 0"/></filter><filter id="f"><feTurbulence type="fractalNoise" baseFrequency=".012 .02" numOctaves="2" seed="3"/><feColorMatrix values="0 0 0 0 .6  0 0 0 0 .55  0 0 0 0 .48  0 0 0 .10 0"/></filter><rect width="100%" height="100%" filter="url(#f)"/><rect width="100%" height="100%" filter="url(#n)"/></svg>`;

const shell = (n, body, src = true) => `<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>${CSS}</style></head><body>${PAPER}
<div class="hd"><div class="brand">${LOGO}<div><div class="ko">방구석 물가</div><div class="en">BANGGUSEOK PRICE</div></div></div><div class="issue">ISSUE 003</div></div>
${body}
${src ? `<div class="src">${SOURCE}</div>` : ''}
<div class="ft"><span>LIVING PRICE JOURNAL</span><span>${n}-4</span></div></body></html>`;

const pages = [];

// 1-4 표지
pages.push(shell(1, `
<h1 style="top:150px;font-size:96px">고구마 1kg,<br>요즘 얼마일까?</h1>
<div class="subt" style="top:384px">겨울 간식으로 즐겨 먹는 고구마, 지금 가격을 살펴봤습니다.</div>
<div class="ph" style="left:70px;top:458px;width:940px;height:535px"><img src="${img('p1')}"></div>
<div style="position:absolute;left:70px;top:1018px;font-size:30px;font-weight:500">전국 22개 조사 도시 평균</div>
<div class="price" style="position:absolute;left:66px;top:1066px;font-size:112px">${won(D.nat)}<small>원</small></div>
<div style="position:absolute;right:70px;top:1150px;text-align:right;font-size:26px;color:var(--sub)">조사 기준일 <b style="color:var(--ink);font-weight:500">${D.date}</b></div>
`));

// 2-4 가격 현황
const row = (k, v, strong) => `<div style="display:flex;justify-content:space-between;align-items:center;height:58px;border-bottom:1.5px solid #cfc9bf;font-size:26px"><span>${k}</span><span style="font-weight:${strong ? 900 : 500}">${v}</span></div>`;
pages.push(shell(2, `
<h1 style="top:146px;font-size:76px">고구마 1kg, 얼마일까?</h1>
<div class="subt" style="top:254px">전국 22개 조사 도시 평균과 서울 가격을 비교했습니다.</div>
<div class="ph" style="left:70px;top:340px;width:460px;height:430px"><img src="${img('p2')}"></div>
<div style="position:absolute;left:570px;right:70px;top:336px">
  <div style="font-size:28px;font-weight:500">전국 평균 · 22개 조사 도시</div>
  <div class="price" style="font-size:100px;margin:18px 0 22px -4px">${won(D.nat)}<small>원</small></div>
  <div style="border-top:1.5px solid #cfc9bf">
  ${row('조사 기준일', D.date)}${row('규격', D.spec)}${row('서울 평균', won(D.seoul) + '원', 1)}${row('전국 평균', won(D.nat) + '원', 1)}
  </div>
</div>
<div style="position:absolute;left:70px;right:70px;top:808px;border-top:1.5px solid #cfc9bf"></div>
<div style="position:absolute;left:540px;top:836px;width:1.5px;height:340px;background:#cfc9bf"></div>
<div style="position:absolute;left:70px;top:840px;width:440px">
  <div style="font-size:40px;font-weight:900;letter-spacing:-1px">서울은 얼마?</div>
  <div style="font-size:30px;line-height:1.5;margin-top:14px;color:#222">서울 평균 가격은<br>${won(D.seoul)}원입니다.</div>
  <div style="margin-top:26px;background:var(--badge);border-radius:10px;padding:18px 26px;display:flex;align-items:baseline;gap:12px;font-size:28px;font-weight:500;white-space:nowrap">전국보다 <span class="price" style="font-size:60px">${won(D.diffNat)}<small>원</small></span> 높음</div>
</div>
<div style="position:absolute;left:580px;right:70px;top:840px">
  <div style="font-size:40px;font-weight:900;letter-spacing:-1px">전국 평균과 차이는?</div>
  <div style="font-size:30px;line-height:1.5;margin-top:14px;color:#222">서울은 전국 22개 조사 도시<br>평균보다 ${won(D.diffNat)}원 높은<br>가격입니다.</div>
</div>
`));

// 3-4 지역별 가격 비교 (축 0원 기준, 막대 높이 실측 비례)
const cx0 = 210, cx1 = 1010, cy0 = 380, cy1 = 790, ymax = 6000;
const y = (v) => cy1 - (v / ymax) * (cy1 - cy0);
let grid = '';
for (let v = 0; v <= ymax; v += 1000) {
  grid += `<line x1="${cx0}" x2="${cx1}" y1="${y(v)}" y2="${y(v)}" stroke="${v ? '#bdb6ab' : '#555'}" stroke-width="${v ? 1.5 : 2}" ${v ? 'stroke-dasharray="6 6"' : ''}/>`;
  grid += `<text x="${cx0 - 18}" y="${y(v) + 9}" text-anchor="end" font-size="26" fill="#222">${won(v)}</text>`;
}
const bw = 280, b1 = 300, b2 = 680;
const bar = (x, v, c, label) => `<rect x="${x}" y="${y(v)}" width="${bw}" height="${cy1 - y(v)}" fill="${c}"/>
<text x="${x + bw / 2}" y="${y(v) - 20}" text-anchor="middle" font-size="46" font-weight="900" fill="#141414">${won(v)}원</text>
<text x="${x + bw / 2}" y="${cy1 + 46}" text-anchor="middle" font-size="34" font-weight="500" fill="#141414">${label}</text>`;
pages.push(shell(3, `
<h1 style="top:146px;font-size:76px">서울·안동 가격 비교</h1>
<div class="subt" style="top:254px">같은 밤고구마 1kg 기준, 지역별 조사 가격을 비교했습니다.</div>
<svg style="position:absolute;left:0;top:0" width="1080" height="900" font-family="Noto Sans CJK KR">
<text x="${cx0 - 18}" y="${cy0 - 28}" text-anchor="end" font-size="24" fill="#222">(원)</text>
${grid}<line x1="${cx0}" x2="${cx0}" y1="${cy0 - 6}" y2="${cy1}" stroke="#555" stroke-width="2"/>
${bar(b1, D.seoul, 'var(--green)', '서울')}${bar(b2, D.andong, 'var(--olive)', '안동')}
</svg>
<div style="position:absolute;left:70px;right:70px;top:880px;border-top:1.5px solid #cfc9bf"></div>
<div class="ph" style="left:70px;top:908px;width:450px;height:274px"><img src="${img('p3')}"></div>
<div style="position:absolute;left:566px;right:70px;top:916px">
  <div style="font-size:28px;color:var(--sub)">밤고구마 1kg 기준</div>
  <div style="font-size:38px;font-weight:900;letter-spacing:-1px;margin-top:8px">서울·안동 가격 차이</div>
  <div class="price" style="font-size:112px;margin-top:20px;margin-left:-4px">${won(D.diffReg)}<small>원</small></div>
</div>
`));

// 4-4 가격 차이 분석
const items = [
  ['품종과 등급', '밤고구마, 호박고구마 등 품종과 품질 등급에 따라 가격이 달라질 수 있습니다.'],
  ['크기와 선별', '고구마 크기와 선별 기준에 따라 판매가격이 달라질 수 있습니다.'],
  ['유통과 판매처', '전통시장, 대형마트, 온라인 등 판매처별 조건을 확인하세요.'],
  ['행사와 할인', '묶음 판매, 카드 할인, 배송비 등에 따라 최종 구매가격이 달라질 수 있습니다.'],
];
pages.push(shell(4, `
<h1 style="top:146px;font-size:76px">고구마값이 다른 이유</h1>
<div class="subt" style="top:254px;font-size:29px">품종, 등급, 유통경로 등에 따라 가격은 달라질 수 있습니다.</div>
<div class="ph" style="left:70px;top:340px;width:440px;height:754px"><img src="${img('p4')}"></div>
<div style="position:absolute;left:546px;right:70px;top:340px;height:754px;display:flex;flex-direction:column">
${items.map(([h, t], i) => `<div style="flex:1;display:flex;flex-direction:column;justify-content:center;${i ? 'border-top:1.5px solid #cfc9bf;' : ''}">
  <div class="green" style="font-size:40px;font-weight:900;letter-spacing:-1px">${h}</div>
  <div style="font-size:27px;line-height:1.5;margin-top:10px;color:#222;letter-spacing:-.6px">${t}</div></div>`).join('')}
</div>
<div style="position:absolute;left:70px;right:70px;top:1122px;font-size:21px;line-height:1.5;color:var(--sub);letter-spacing:-.4px">※ 위 항목은 일반적인 가격 비교 요소이며, 이번 지역별 가격 차이의 원인으로 확정된 것은 아닙니다.</div>
`));

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
  const names = ['01_cover', '02_price', '03_compare', '04_reasons'];
  for (let i = 0; i < 4; i++) {
    fs.writeFileSync(path.join(DIR, `p${i + 1}.html`), pages[i]);
    await page.setContent(pages[i], { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    // 글자 잘림 검사: 넘침 요소 보고
    const over = await page.evaluate(() => [...document.querySelectorAll('div,h1,span')].filter(e => e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflow !== 'hidden').map(e => e.textContent.trim().slice(0, 30)));
    if (over.length) console.log(`page ${i + 1} overflow:`, over);
    await page.screenshot({ path: path.join(OUT, `issue003_sweet-potato_${names[i]}_${i + 1}-4.png`) });
  }
  await browser.close();
  console.log('done');
})();
