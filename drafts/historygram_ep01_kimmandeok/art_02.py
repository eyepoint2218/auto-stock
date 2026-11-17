"""2장 실루엣 삽화(SVG) 생성 → Chromium으로 PNG 렌더."""
import subprocess, json
from pathlib import Path

W, H = 1080, 1350
HERE = Path(__file__).resolve().parent
SIL = "#120c09"   # 실루엣 색
RIM = "#d89a4a"   # 역광 테두리


def official(x, y, s, face=1):
    """단령·사모 차림 신하 실루엣. (x,y)=발 위치, s=배율, face=±1 바라보는 방향."""
    return f'''<g transform="translate({x},{y}) scale({s * face},{s})">
      <path d="M-34 0 L-30 -70 Q-38 -95 -26 -120 Q-14 -140 0 -140 Q14 -140 26 -120 Q38 -95 30 -70 L34 0 Z"/>
      <path d="M-26 -118 Q-46 -100 -42 -70 Q-30 -66 -24 -80 Z"/>
      <path d="M22 -118 Q46 -96 40 -66 Q22 -62 18 -84 Z"/>
      <ellipse cx="0" cy="-156" rx="13" ry="15"/>
      <path d="M-13 -164 L-13 -174 Q-13 -178 -8 -178 L8 -178 Q13 -178 13 -174 L13 -164 Z"/>
      <path d="M-9 -177 Q-9 -190 0 -190 Q9 -190 9 -177 Z"/>
      <ellipse cx="-20" cy="-178" rx="10" ry="5" transform="rotate(-15 -20 -178)"/>
      <ellipse cx="20" cy="-178" rx="10" ry="5" transform="rotate(15 20 -178)"/>
    </g>'''


def king(x, y, s):
    """곤룡포·익선관 차림으로 어좌에 앉은 임금(정면, 작게)."""
    return f'''<g transform="translate({x},{y}) scale({s})">
      <path d="M-46 0 Q-50 -40 -40 -70 Q-30 -98 0 -100 Q30 -98 40 -70 Q50 -40 46 0 Z" fill="#3a0f0c"/>
      <circle cx="0" cy="-74" r="11" fill="#8a6a2a" opacity=".8"/>
      <ellipse cx="0" cy="-116" rx="14" ry="16" fill="{SIL}"/>
      <path d="M-15 -124 Q-15 -146 0 -148 Q15 -146 15 -124 Z" fill="{SIL}"/>
      <path d="M-10 -146 Q-10 -158 0 -158 Q10 -158 10 -146 Z" fill="{SIL}"/>
      <ellipse cx="-9" cy="-156" rx="5" ry="7" fill="{SIL}"/><ellipse cx="9" cy="-156" rx="5" ry="7" fill="{SIL}"/>
    </g>'''


def screen():
    """일월오봉도 병풍 (단순화). 해=오른쪽 붉은 원, 달=왼쪽 흰 원."""
    peaks = "M330 470 L330 330 L380 250 L420 300 L470 215 L540 160 L610 215 L660 300 L700 250 L750 330 L750 470 Z"
    return f'''<g>
      <rect x="320" y="120" width="440" height="360" fill="#2d4a52"/>
      <path d="{peaks}" fill="#3f6f62"/>
      <path d="M330 470 L330 380 L420 330 L540 260 L660 330 L750 380 L750 470 Z" fill="#2f5a4f"/>
      <path d="M330 470 Q400 430 470 455 Q540 480 610 452 Q680 428 750 460 L750 480 L330 480 Z" fill="#3c6a8a"/>
      <circle cx="385" cy="185" r="26" fill="#e8e2cc"/>
      <circle cx="695" cy="185" r="26" fill="#c8402c"/>
      <g stroke="#1b2a2c" stroke-width="3">
        <line x1="408" y1="120" x2="408" y2="480"/><line x1="496" y1="120" x2="496" y2="480"/>
        <line x1="584" y1="120" x2="584" y2="480"/><line x1="672" y1="120" x2="672" y2="480"/>
      </g>
      <rect x="320" y="120" width="440" height="360" fill="none" stroke="#5a3a1c" stroke-width="10"/>
    </g>'''


def woman(x, y, s):
    """무릎 꿇고 엎드린 여인의 뒷모습(가리마·치마)."""
    return f'''<g transform="translate({x},{y}) scale({s})" fill="{SIL}" stroke="{RIM}" stroke-width="2.2" stroke-linejoin="round">
      <path d="M-150 0 Q-160 -40 -110 -62 Q-60 -80 0 -80 Q60 -80 110 -62 Q160 -40 150 0 Z"/>
      <path d="M-78 -66 Q-86 -120 -50 -150 Q-20 -170 0 -170 Q20 -170 50 -150 Q86 -120 78 -66 Z"/>
      <path d="M-40 -150 Q-44 -186 0 -192 Q44 -186 40 -150 Q20 -158 0 -158 Q-20 -158 -40 -150 Z"/>
      <path d="M-46 -176 Q-50 -196 0 -200 Q50 -196 46 -176 L52 -128 Q40 -122 36 -134 L30 -166 Q0 -172 -30 -166 L-36 -134 Q-40 -122 -52 -128 Z"/>
    </g>'''


officials = []
for i, (x, y, s) in enumerate([(250, 560, .62), (175, 650, .78), (85, 765, .98)]):
    officials.append(official(x, y, s, 1))
    officials.append(official(W - x, y, s, -1))

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <radialGradient id="glow" cx="50%" cy="27%" r="60%">
    <stop offset="0" stop-color="#b8763a"/><stop offset=".45" stop-color="#5a2e18"/><stop offset="1" stop-color="#140b07"/>
  </radialGradient>
  <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#4a2c18"/><stop offset="1" stop-color="#0d0805"/>
  </linearGradient>
  <linearGradient id="path" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#e0a25a" stop-opacity=".45"/><stop offset="1" stop-color="#e0a25a" stop-opacity="0"/>
  </linearGradient>
  <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="7"/>
    <feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 .10 0"/><feComposite in2="SourceGraphic" operator="in"/></filter>
  <filter id="soft"><feGaussianBlur stdDeviation="14"/></filter>
</defs>
<rect width="{W}" height="{H}" fill="url(#glow)"/>
<!-- 천장 들보 -->
<path d="M0 0 H{W} V70 Q540 110 0 70 Z" fill="#1c100a"/>
<path d="M0 70 Q540 110 {W} 70 V92 Q540 132 0 92 Z" fill="#6a2a1c"/>
{screen()}
<!-- 바닥 -->
<path d="M0 520 H{W} V{H} H0 Z" fill="url(#floor)"/>
<g stroke="#2a180e" stroke-width="2" opacity=".8">
  {''.join(f'<line x1="{540 + (i - 8) * 30}" y1="520" x2="{540 + (i - 8) * 260}" y2="{H}"/>' for i in range(17))}
</g>
<path d="M470 520 L610 520 L760 {H} L320 {H} Z" fill="url(#path)" filter="url(#soft)"/>
<!-- 어탑(계단) -->
<rect x="380" y="470" width="320" height="22" fill="#2a1409"/>
<rect x="400" y="492" width="280" height="18" fill="#3a1d0e"/>
<rect x="420" y="510" width="240" height="16" fill="#2a1409"/>
<!-- 어좌 -->
<path d="M470 470 L470 330 Q540 300 610 330 L610 470 Z" fill="#5a1e14"/>
<path d="M480 470 L480 340 Q540 314 600 340 L600 470 Z" fill="#3a120c"/>
{king(540, 462, 1.0)}
<!-- 기둥 -->
<rect x="0" y="0" width="70" height="{H}" fill="#2a0e09"/><rect x="62" y="0" width="10" height="{H}" fill="#4a1a10"/>
<rect x="{W - 70}" y="0" width="70" height="{H}" fill="#2a0e09"/><rect x="{W - 72}" y="0" width="10" height="{H}" fill="#4a1a10"/>
<g fill="{SIL}" stroke="{RIM}" stroke-width="1.6" stroke-opacity=".7">{''.join(officials)}</g>
<!-- 바닥 그림자 -->
<ellipse cx="540" cy="752" rx="190" ry="26" fill="#000" opacity=".6" filter="url(#soft)"/>
{woman(540, 750, 0.95)}
<rect width="{W}" height="{H}" filter="url(#grain)"/>
</svg>'''

svg_path = HERE / "art_02.svg"
svg_path.write_text(svg, encoding="utf-8")
out = HERE / "art_02.png"
js = f"""
const {{chromium}} = require('playwright');
(async () => {{
  const b = await chromium.launch();
  const p = await b.newPage({{viewport: {{width: {W}, height: {H}}}, deviceScaleFactor: 1}});
  await p.goto('file://{svg_path}');
  await p.screenshot({{path: {json.dumps(str(out))}}});
  await b.close();
}})();
"""
subprocess.run(["node", "-e", js], check=True)
print(out)
