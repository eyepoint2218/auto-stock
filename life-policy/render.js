// LIFE POLICY 카드뉴스 렌더러 — ISSUE 001 원본 레이아웃을 좌표로 고정한 템플릿
// 사용법: node render.js issues/issue-00N.json [출력폴더]   (새 호는 issues/_template.json 복사)
// 텍스트에서 [대괄호]로 감싼 부분은 파란색 강조.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const cfgPath = path.resolve(process.argv[2] || 'issues/issue-002.json');
const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));

// 시리즈 고정값(series.json): 푸터 문구, 5장 순서, 마지막 팔로우 장을 모든 호에 강제 적용
const series = JSON.parse(fs.readFileSync(path.join(__dirname, 'series.json'), 'utf8'));
cfg.footer = series.footer;
cfg.slides = cfg.slides.filter((s) => s.type !== 'follow').concat([series.follow]);
const order = cfg.slides.map((s) => s.type).join(',');
if (order !== series.order.join(',')) { console.error(`장 구성이 고정 순서와 다릅니다: ${order} (고정: ${series.order.join(',')})`); process.exit(1); }
// 후킹 규칙: 표지 큰 글씨에 2·3장의 결과 숫자를 쓰지 않는다
{
  const cover = cfg.slides[0], cmp = cfg.slides[1];
  const reveal = [cmp.rows[1].value, cmp.banner].map((v) => v.replace(/[^0-9.,%p]/g, '')).filter((v) => /\d/.test(v));
  if (reveal.some((v) => cover.big.includes(v))) { console.error(`표지에 결과가 노출됩니다: "${cover.big}" — 질문형으로 바꾸세요 (예: "인상? 동결?", "얼마나?")`); process.exit(1); }
}
const OUT = path.resolve(process.argv[3] || path.join(__dirname, 'out', path.basename(cfgPath, '.json')));
fs.mkdirSync(OUT, { recursive: true });

// 계산 검증(있을 때만)
if (cfg.check) {
  const c = cfg.check;
  const a = Math.round(c.income * c.rate2026 / 100 * c.employeeShare);
  const b = Math.round(c.income * c.rate2027 / 100 * c.employeeShare);
  const fmt = (n) => n.toLocaleString('ko-KR') + '원';
  const s3 = cfg.slides.find((s) => s.type === 'calc');
  const s2 = cfg.slides.find((s) => s.type === 'compare');
  const errs = [];
  if (s3) {
    if (s3.rows[0].value !== fmt(a)) errs.push(`2026 월 보험료 ${s3.rows[0].value} ≠ ${fmt(a)}`);
    if (s3.rows[1].value !== fmt(b)) errs.push(`2027 월 보험료 ${s3.rows[1].value} ≠ ${fmt(b)}`);
    if (b === a ? !s3.banner.includes('0원') : s3.banner !== '+' + fmt(b - a)) errs.push(`차액 배너 ${s3.banner} 확인 (계산값 ${fmt(b - a)})`);
  }
  if (s2 && c.rate2027 !== c.rate2026 && !s2.banner.includes(String(+(c.rate2027 - c.rate2026).toFixed(2)))) errs.push(`인상폭 배너 확인: ${s2.banner}`);
  if (errs.length) { console.error('계산 불일치:\n' + errs.join('\n')); process.exit(1); }
  console.log(`계산 확인: ${fmt(a)} → ${fmt(b)} (+${fmt(b - a)})`);
}

const FONT = (w, f) => `@font-face{font-family:P;font-weight:${w};src:url(data:font/otf;base64,${fs.readFileSync(path.join(__dirname, 'fonts', f)).toString('base64')})}`;
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const hl = (s) => esc(s).replace(/\[(.+?)\]/g, '<b class="bl">$1</b>');

const CSS = `
${FONT(500, 'Pretendard-Medium.otf')}${FONT(600, 'Pretendard-SemiBold.otf')}${FONT(700, 'Pretendard-Bold.otf')}${FONT(800, 'Pretendard-ExtraBold.otf')}${FONT(900, 'Pretendard-Black.otf')}
:root{--navy:#0A1230;--blue:#0A3EC2;--rule:#2A2C48;--gray:#C9C9CD;--box1:#ECECEE;--box2:#DCE8FD}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1350px;background:#fff}
body{font-family:P,sans-serif;color:var(--navy);position:relative;overflow:hidden;word-break:keep-all;letter-spacing:-0.02em}
b{font-weight:inherit}.bl{color:var(--blue)}
.a{position:absolute;white-space:nowrap}
.fit{display:inline-block;transform-origin:left center}
.h{font-weight:900;letter-spacing:-0.045em}
`;

const frame = (n, total, body) => `<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>${CSS}</style></head><body>
<div class="a" style="left:92px;top:52px;width:11px;height:46px;background:var(--blue)"></div>
<div class="a" style="left:128px;top:46px;font-size:46px;font-weight:800;line-height:56px;letter-spacing:-0.01em">LIFE POLICY</div>
<div class="a" style="right:80px;top:54px;font-size:38px;font-weight:800;line-height:48px;letter-spacing:-0.01em">${esc(cfg.issue)}</div>
<div class="a" style="left:92px;top:122px;width:908px;height:3px;background:var(--rule)"></div>
${body}
<div class="a" style="left:92px;top:1193px;width:908px;height:3px;background:var(--rule)"></div>
<div class="a" style="left:92px;top:1220px;font-size:43px;font-weight:700;letter-spacing:-0.03em;line-height:50px">${esc(cfg.footer)}</div>
<div class="a" style="right:80px;top:1220px;font-size:43px;font-weight:800;line-height:50px;letter-spacing:0">${String(n).padStart(2, '0')} / ${String(total).padStart(2, '0')}</div>
</body></html>`;

// 지정 폭을 넘으면 글자 크기를 줄임(원본 크기가 상한)
const fitText = (html, size, maxW, style = '', grow = 0) => `<span class="fit" data-maxw="${maxW}" data-grow="${grow}" style="font-size:${size}px;${style}">${html}</span>`;

const rows = (r, y1, y2, h, boxW, labelSizes, numSize, divX, sepY) => {
  const one = (row, y, bg, numColor) => `
<div class="a" style="left:92px;top:${y}px;width:${boxW}px;height:${h}px;background:${bg};display:flex;flex-direction:column;justify-content:center;align-items:center;white-space:normal">
  <div style="font-size:${labelSizes[0]}px;font-weight:900;letter-spacing:-0.03em;line-height:1.2">${esc(row.label[0])}</div>
  <div style="font-size:${labelSizes[1]}px;font-weight:${labelSizes[1] < labelSizes[0] ? 800 : 900};letter-spacing:-0.03em;line-height:1.25">${esc(row.label[1])}</div>
</div>
<div class="a" style="left:${divX}px;top:${y + 28}px;width:2px;height:${h - 56}px;background:var(--rule)"></div>
<div class="a h" style="left:${divX + 40}px;top:${y}px;height:${h}px;display:flex;align-items:center;color:${numColor}">${fitText(esc(row.value), numSize, 1000 - divX - 50, '', Math.round(numSize * 1.4))}</div>`;
  return one(r[0], y1, 'var(--box1)', 'var(--navy)') +
    `<div class="a" style="left:${divX - 2}px;top:${sepY}px;width:${1000 - divX + 2}px;height:2px;background:var(--gray)"></div>` +
    one(r[1], y2, 'var(--box2)', 'var(--blue)');
};

const banner = (text, y, h, size) => `<div class="a h" style="left:92px;top:${y}px;width:908px;height:${h}px;background:var(--blue);display:flex;align-items:center;justify-content:center;color:#fff">${fitText(esc(text), size, 820, 'transform-origin:center')}</div>`;

const title = (t, top, size, lh) => `<div class="a h" style="left:88px;top:${top}px;height:${lh}px;display:flex;align-items:center">${fitText(hl(t), size, 914, '', size * 1.08)}</div>`;

const LAYOUT = {
  cover: (s) => `
${s.lines.map((l, i) => `<div class="a h" style="left:88px;top:${178 + i * 158}px;line-height:160px">${fitText(hl(l), 134, 914)}</div>`).join('')}
<div class="a" style="left:100px;top:715px;height:117px;padding:0 36px;min-width:790px;background:var(--blue);display:flex;align-items:center;justify-content:center;color:#fff;font-size:62px;font-weight:800;letter-spacing:-0.03em">${esc(s.label)}</div>
<div class="a h" style="left:86px;top:846px;height:330px;display:flex;align-items:center;color:var(--blue);line-height:1">${fitText(esc(s.big), 262, 900, 'letter-spacing:-0.05em', 360)}</div>`,
  compare: (s) => title(s.title, 186, 132, 140) + rows(s.rows, 390, 622, 183, 280, [54, 54], 120, 411, 596) + banner(s.banner, 893, 170, 136),
  calc: (s) => title(s.title, 190, 112, 124) + rows(s.rows, 352, 574, 175, 286, [50, 40], 104, 418, 549) + banner(s.banner, 810, 162, 134) +
    `<div class="a" style="left:124px;top:1012px;font-weight:800;letter-spacing:-0.03em;line-height:60px">${fitText(esc(s.note), 52, 876)}</div>`,
  when: (s) => title(s.title, 184, 110, 124) +
    `<div class="a h" style="left:88px;top:326px;color:var(--blue);line-height:124px">${fitText(esc(s.period), 116, 914)}</div>
<div class="a" style="left:92px;top:474px;width:908px;height:2px;background:var(--gray)"></div>
${s.scope.map((l, i) => `<div class="a h" style="left:90px;top:${512 + i * 92}px;line-height:96px">${fitText(esc(l), 88, 910)}</div>`).join('')}
<div class="a" style="left:92px;top:736px;width:908px;height:2px;background:var(--gray)"></div>
<div class="a" style="left:96px;top:766px;font-weight:800;letter-spacing:-0.035em;line-height:84px">${fitText(esc(s.basis), 68, 900)}</div>
<div class="a" style="left:92px;top:908px;width:908px;height:190px;background:var(--box2);padding:0 36px;display:flex;flex-direction:column;justify-content:center;white-space:nowrap">
${s.box.map((l) => `<div style="font-weight:700;letter-spacing:-0.03em;line-height:64px">${fitText(esc(l), 54, 836)}</div>`).join('')}</div>`,
  // 팔로우 유도(마지막 장): 제목 2줄 + 번호 목록 3개 + 계정 배너 + 안내 문구
  follow: (s) => s.lines.map((l, i) => title(l, 184 + i * 128, 110, 124)).join('') +
    `<div class="a" style="left:92px;top:474px;width:908px;height:2px;background:var(--gray)"></div>` +
    s.items.map((t, i) => `
<div class="a h" style="left:92px;top:${492 + i * 108}px;height:108px;display:flex;align-items:center;color:var(--blue);font-size:50px;letter-spacing:-0.02em">${String(i + 1).padStart(2, '0')}</div>
<div class="a" style="left:190px;top:${492 + i * 108}px;height:108px;display:flex;align-items:center;font-weight:800;letter-spacing:-0.035em">${fitText(hl(t), 58, 810)}</div>
<div class="a" style="left:92px;top:${492 + (i + 1) * 108}px;width:908px;height:2px;background:var(--gray)"></div>`).join('') +
    banner(s.banner, 880, 162, 120) +
    `<div class="a" style="left:124px;top:1078px;font-weight:800;letter-spacing:-0.03em;line-height:60px">${fitText(hl(s.note), 52, 876)}</div>`,
};

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
  const total = cfg.slides.length;
  const files = [];
  for (let i = 0; i < total; i++) {
    const s = cfg.slides[i];
    await page.setContent(frame(i + 1, total, LAYOUT[s.type](s)), { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    const shrunk = await page.evaluate(() => [...document.querySelectorAll('.fit')].map((e) => {
      const max = +e.dataset.maxw, w = e.getBoundingClientRect().width;
      const fs0 = parseFloat(e.style.fontSize), cap = +e.dataset.grow;
      if (cap && w < max) { const k = Math.min(max / w, cap / fs0); e.style.fontSize = (fs0 * k).toFixed(1) + 'px'; return; }
      if (w > max) { const k = max / w; e.style.fontSize = (fs0 * k).toFixed(1) + 'px'; return e.textContent + ` → ${Math.round(k * 100)}%`; }
    }).filter(Boolean));
    if (shrunk.length) console.log(`slide ${i + 1} 자동 축소:`, shrunk.join(' | '));
    const fonts = await page.evaluate(() => [...document.fonts].filter((f) => f.status === 'loaded').length);
    if (fonts < 2) throw new Error('Pretendard 폰트 로드 실패');
    const f = path.join(OUT, `${cfg.issue.replace(/\s+/g, '_').toLowerCase()}_${String(i + 1).padStart(2, '0')}-${String(total).padStart(2, '0')}.png`);
    await page.screenshot({ path: f });
    files.push(f);
  }
  await browser.close();
  console.log(files.join('\n'));
})();
