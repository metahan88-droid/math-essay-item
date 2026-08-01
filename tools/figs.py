#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""문항용 도형 생성 — 지름·넓이·페퍼로니 개수가 수학적으로 정확한 SVG.

AI 이미지 생성은 원의 지름 비와 페퍼로니 개수를 정확히 맞추지 못한다.
수학이 걸린 도해는 좌표를 직접 계산해 그린다.
"""
import math, os, random

OUT = os.path.dirname(os.path.abspath(__file__)) + '/figs'
os.makedirs(OUT, exist_ok=True)

FONT = "Malgun Gothic, AppleGothic, NanumGothic, sans-serif"


def pepperoni_points(R, n, seed):
    """반지름 R 원 안에 n개를 겹치지 않게 고르게 배치 (동심원 배치 + 지터)."""
    rnd = random.Random(seed)
    pts = []
    # 동심원 링에 나눠 담는다: 링 반지름에 비례해 개수 배분
    rings = []
    k = 1
    while True:
        # 링 수를 늘려가며 용량이 n을 넘으면 멈춘다
        caps = []
        for i in range(k):
            rr = R * (i + 0.55) / k
            caps.append(max(1, int(2 * math.pi * rr / (R * 0.30))))
        if sum(caps) >= n or k > 6:
            rings = [(R * (i + 0.55) / k, caps[i]) for i in range(k)]
            break
        k += 1
    left = n
    for idx, (rr, cap) in enumerate(rings):
        take = min(cap, left) if idx < len(rings) - 1 else left
        if take <= 0:
            continue
        off = rnd.uniform(0, 2 * math.pi)
        for j in range(take):
            a = off + 2 * math.pi * j / take
            jit = rnd.uniform(-0.02, 0.02) * R
            pts.append((rr * math.cos(a) + jit, rr * math.sin(a) + jit))
        left -= take
        if left <= 0:
            break
    return pts[:n]


def pizza(cx, cy, R, npep, seed, label=None, sub=None, crust=0.11, ly=None):
    """피자 하나의 SVG 조각."""
    s = []
    s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{R:.1f}" fill="#f2c14e" '
             f'stroke="#8a5a2b" stroke-width="{max(R*0.045,1.6):.1f}"/>')
    s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{R*(1-crust):.1f}" '
             f'fill="#e9564b" stroke="#c8452f" stroke-width="1"/>')
    pr = 3.7                      # 페퍼로니 한 개의 크기는 피자 크기와 무관하게 동일 (자료 규정)
    for (dx, dy) in pepperoni_points(R * (1 - crust) * 0.86, npep, seed):
        s.append(f'<circle cx="{cx+dx:.1f}" cy="{cy+dy:.1f}" r="{pr:.1f}" '
                 f'fill="#9e2b25" stroke="#7c1f1a" stroke-width="0.7"/>')
    y0 = ly if ly is not None else cy + R + 26
    if label:
        s.append(f'<text x="{cx:.1f}" y="{y0:.1f}" text-anchor="middle" '
                 f'font-family="{FONT}" font-size="16" font-weight="bold" fill="#111">{label}</text>')
    if sub:
        s.append(f'<text x="{cx:.1f}" y="{y0+20:.1f}" text-anchor="middle" '
                 f'font-family="{FONT}" font-size="13" fill="#333">{sub}</text>')
    return '\n'.join(s)


def diameter_arrow(cx, cy, R, text, dy=0):
    """지름 화살표 + 라벨."""
    y = cy + dy
    return f'''<g stroke="#1a3f6f" stroke-width="1.6" fill="#1a3f6f">
  <line x1="{cx-R:.1f}" y1="{y:.1f}" x2="{cx+R:.1f}" y2="{y:.1f}"
        marker-start="url(#ar)" marker-end="url(#ar)"/>
</g>
<text x="{cx:.1f}" y="{y-8:.1f}" text-anchor="middle" font-family="{FONT}"
      font-size="14" font-weight="bold" fill="#1a3f6f">{text}</text>'''


def txt_c(x, y, s, size=14, w='normal', fill='#111'):
    return (f'<text x="{x}" y="{y}" text-anchor="middle" font-family="{FONT}" '
            f'font-size="{size}" font-weight="{w}" fill="{fill}">{s}</text>')


HEAD = '''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6"
  orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#1a3f6f"/></marker></defs>
<rect width="100%" height="100%" fill="#ffffff"/>'''


def save(name, w, h, body):
    svg = HEAD.format(w=w, h=h) + '\n' + body + '\n</svg>'
    p = f'{OUT}/{name}.svg'
    open(p, 'w', encoding='utf-8').write(svg)
    os.system(f'rsvg-convert -w {w*2} -h {h*2} "{p}" -o "{OUT}/{name}.png" 2>/dev/null')
    print(f'  {name}.svg / .png  ({w}x{h})')


# ── 도해 1 : 세 피자 크기 비교 — 부피판 (지름 비 + 두께 비, 완전 닮음) ──────
SC = 3.6                                        # 1 cm = 3.6 px
d = {'미디엄': 24, '라지': 30, '자이언트': 36}
th = {'미디엄': 2.0, '라지': 2.5, '자이언트': 3.0}
pep = {'미디엄': 16, '라지': 25, '자이언트': 36}
price = {'미디엄': '16,000원', '라지': '26,000원', '자이언트': '32,000원'}
W, H = 700, 360
xs = [110, 300, 540]
TSC = 9.0                                        # 두께 강조 배율 (표기값이 진실)
body = [f'<text x="{W/2}" y="26" text-anchor="middle" font-family="{FONT}" font-size="16" '
        f'font-weight="bold" fill="#111">[그림 1] 세 가지 크기의 피자 — 서로 닮은 입체 (지름은 실제 비율)</text>']
for x, k in zip(xs, d):
    R = d[k] / 2 * SC
    n_show = pep[k] if k == '미디엄' else 0
    body.append(pizza(x, 135, R, n_show, seed=hash(k) & 0xffff, ly=None, label=None, sub=None))
    body.append(diameter_arrow(x, 135, R, f'{d[k]} cm', dy=-R - 14))
# 옆에서 본 단면 (두께)
side_y = 262
for x, k in zip(xs, d):
    R = d[k] / 2 * SC
    hpx = th[k] * TSC
    body.append(f'<rect x="{x-R:.1f}" y="{side_y - hpx:.1f}" width="{2*R:.1f}" height="{hpx:.1f}" '
                f'rx="{hpx/2.2:.1f}" fill="#f2c14e" stroke="#8a5a2b" stroke-width="1.6"/>')
    body.append(f'<text x="{x+R+8:.1f}" y="{side_y - hpx/2 + 4:.1f}" font-family="{FONT}" '
                f'font-size="12.5" font-weight="bold" fill="#1a3f6f">두께 {th[k]:g} cm</text>')
    body.append(txt_c(x, side_y + 24, f'{k} · 지름 {d[k]} cm', 15, 'bold'))
    body.append(txt_c(x, side_y + 43, f'{price[k]} · 페퍼로니 {"16개" if k=="미디엄" else "?개"}', 13, 'normal', '#333'))
body.append(f'<text x="{W/2}" y="{side_y - 52}" text-anchor="middle" font-family="{FONT}" '
            f'font-size="13" fill="#555">〔옆에서 본 모양〕 두께도 지름과 같은 비율(4 : 5 : 6)로 두꺼워진다 (두께는 알아보기 쉽게 확대해 그림)</text>')
save('fig1_three_sizes', W, H, '\n'.join(body))

# ── 도해 2 : 페퍼로니 밀도 — 옳은 개수 vs 오류 개수 ────────────────────────
W, H = 760, 315
body = [f'<text x="{W/2}" y="26" text-anchor="middle" font-family="{FONT}" font-size="16" '
        f'font-weight="bold" fill="#111">〔도해〕 자이언트에 페퍼로니를 몇 개 올려야 할까?</text>']
R24 = 12 * SC
R36 = 18 * SC
body.append(pizza(110, 155, R24, 16, 11, ly=250, label='미디엄 · 16개', sub='1개당 피자 넓이 28.26 cm²'))
body.append(pizza(365, 155, R36, 36, 22, ly=250, label='자이언트 · 36개  ✔', sub='1개당 피자 넓이 28.26 cm² (미디엄과 같음)'))
body.append(pizza(625, 155, R36, 24, 33, ly=250, label='자이언트 · 24개  ✘', sub='1개당 피자 넓이 42.39 cm² (듬성해짐)'))
body.append(f'<text x="{W/2}" y="303" text-anchor="middle" font-family="{FONT}" font-size="13" '
            f'fill="#8a1c1c">지름이 1.5배이면 넓이는 1.5 × 1.5 = 2.25배이므로 16 × 2.25 = 36개가 필요하다</text>')
save('fig2_pepperoni_density', W, H, '\n'.join(body))

# ── 도해 3 : 넓이 비교 — 미디엄 2판 vs 자이언트 1판 ────────────────────────
W, H = 700, 300
body = [f'<text x="{W/2}" y="26" text-anchor="middle" font-family="{FONT}" font-size="16" '
        f'font-weight="bold" fill="#111">〔도해·교사용〕 미디엄 2판 vs 자이언트 1판 — 양은 부피로 (완전 닮음: 두께도 4:5:6)</text>']
body.append(pizza(120, 150, R24, 16, 44, ly=232, label='미디엄', sub='부피 904.32 cm³'))
body.append(pizza(285, 150, R24, 16, 55, ly=232, label='미디엄', sub='부피 904.32 cm³'))
body.append(f'<text x="203" y="283" text-anchor="middle" font-family="{FONT}" font-size="14" '
            f'font-weight="bold" fill="#111">ⓐ 2판 = 1808.64 cm³ = 8인분 · 30,000원 · 32개</text>')
body.append(f'<text x="425" y="158" text-anchor="middle" font-family="{FONT}" font-size="26" fill="#555">vs</text>')
body.append(pizza(570, 150, R36, 36, 66, ly=232, label='자이언트', sub='부피 3052.08 cm³'))
body.append(f'<text x="570" y="283" text-anchor="middle" font-family="{FONT}" font-size="14" '
            f'font-weight="bold" fill="#0b5c2e">ⓒ 1판 = 3052.08 cm³ = 13.5인분 · 32,000원 · 36개</text>')
save('fig3_area_compare', W, H, '\n'.join(body))

# ── 도해 4 : 패밀리 설계 — 넓이 4배는 지름 2배 ────────────────────────────
W, H = 700, 330
body = [f'<text x="{W/2}" y="26" text-anchor="middle" font-family="{FONT}" font-size="16" '
        f'font-weight="bold" fill="#111">〔도해·교사용〕 패밀리(두께 2 cm 고정): 윗면 넓이 4배 → 지름 2배</text>']
SC2 = 1.9
body.append(pizza(105, 170, 12 * SC2, 16, 77, ly=268, label='미디엄 · 지름 24 cm', sub='윗면 452.16 cm² · 두께 2 cm'))
body.append(pizza(300, 170, 24 * SC2, 64, 88, ly=268, label='패밀리 · 지름 48 cm  ✔', sub='윗면 1808.64 cm² (4배) · 두께 2 cm'))
body.append(f'<text x="203" y="318" text-anchor="middle" font-family="{FONT}" font-size="13" '
            f'font-weight="bold" fill="#0b5c2e">두께 고정 → 부피∝윗면 넓이 → k×k=4 → 지름 2배</text>')
body.append(f'<text x="560" y="120" text-anchor="middle" font-family="{FONT}" font-size="14" '
            f'font-weight="bold" fill="#8a1c1c">완전 닮음으로 16명분을 만들면?</text>')
body.append(f'<text x="560" y="145" text-anchor="middle" font-family="{FONT}" font-size="13" fill="#8a1c1c">'
            f'k×k×k=4 → k=∛4 (무리수)</text>')
body.append(f'<text x="560" y="168" text-anchor="middle" font-family="{FONT}" font-size="13" fill="#8a1c1c">'
            f'중2 범위 밖 — 그래서 두께를 고정한다</text>')
body.append(f'<circle cx="560" cy="245" r="{48*SC2*0.62:.1f}" fill="none" stroke="#8a1c1c" '
            f'stroke-width="2" stroke-dasharray="6 4"/>')
body.append(f'<text x="560" y="250" text-anchor="middle" font-family="{FONT}" font-size="12" fill="#8a1c1c">96 cm</text>')
save('fig4_family_design', W, H, '\n'.join(body))

print('\n검증:')
for k in d:
    R = d[k] / 2
    print(f'  {k}: 반지름 {R} cm → 넓이 {3.14*R*R:.2f} cm², 페퍼로니 {pep[k]}개, '
          f'조각당 {3.14*R*R/pep[k]:.2f} cm²')
print(f'  자이언트 24개일 때 조각당 {3.14*18*18/24:.2f} cm²')
print(f'  패밀리 48 cm: {3.14*24*24:.2f} cm² = 미디엄의 {24*24/(12*12)}배, 페퍼로니 {16*4}개')
