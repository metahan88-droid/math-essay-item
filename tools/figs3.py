#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""자료 2 — 동아리 단체 대화방 도해 (v3 확정 대사)."""
import os

OUT = os.path.dirname(os.path.abspath(__file__)) + '/figs'
FONT = "Malgun Gothic, AppleGothic, NanumGothic, sans-serif"
HEAD = ('<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        'viewBox="0 0 {w} {h}">\n<rect width="100%" height="100%" fill="#f4f6f8"/>')


def save(name, w, h, body):
    open(f'{OUT}/{name}.svg', 'w', encoding='utf-8').write(
        HEAD.format(w=w, h=h) + '\n' + body + '\n</svg>')
    os.system(f'rsvg-convert -w {w*2} -h {h*2} "{OUT}/{name}.svg" -o "{OUT}/{name}.png" 2>/dev/null')
    print(f'  {name}  ({w}x{h})')


PAL = {'민재': '#3b6ea5', '서연': '#b0563a', '하윤': '#4a7d4a', '지호': '#7a5aa0'}

# v3 확정 대사. ㉠·㉡ 밑줄 구간은 뒤 검은 밑줄로 표시
MSGS = [
    ('민재', [('행사 봤어? 미디엄 2판이 30,000원인데 자이언트 1판은 32,000원이야.', 0),
              ('2,000원 더 싼데 피자도 2판이잖아. 미디엄 2판으로 하자!', 0)]),
    ('서연', [('나도 계산해 봤어. ㉠ 자이언트가 36 cm이고 미디엄이 24 cm니까', 1),
              ('36 ÷ 24 = 1.5야. 그러니까 자이언트 1판은 미디엄 1.5판만큼이지.', 1),
              ('미디엄 2판이 1.5판보다 많으니까 민재 말이 맞네.', 0)]),
    ('하윤', [('그런데 라지 1판이면 26,000원이라 예산도 남잖아.', 0),
              ('그냥 라지 시키면 안 돼?', 0)]),
    ('지호', [('페퍼로니 개수는 내가 계산할게. ㉡ 라지는 미디엄보다 지름이', 1),
              ('1.25배니까 16 × 1.25 = 20개, 자이언트는 미디엄보다 지름이', 1),
              ('1.5배니까 16 × 1.5 = 24개야. 그렇게 올려 달라고 하면 되겠다.', 1)]),
]

W = 680
LINE_H = 21
PAD_TOP, PAD_BOT = 12, 12
GAP = 16
HEADER = 46

y = HEADER + 12
parts = []
parts.append(f'<rect x="0" y="0" width="{W}" height="{HEADER}" fill="#2f4a63"/>')
parts.append(f'<text x="{W/2}" y="30" font-family="{FONT}" font-size="17" font-weight="bold" '
             f'fill="#fff" text-anchor="middle">수학동아리 단체 대화방 (어젯밤)</text>')

for name, lines in MSGS:
    box_h = PAD_TOP + PAD_BOT + LINE_H * len(lines)
    col = PAL[name]
    # 아바타 + 이름
    parts.append(f'<circle cx="36" cy="{y+18}" r="15" fill="{col}"/>')
    parts.append(f'<text x="36" y="{y+23}" font-family="{FONT}" font-size="13" font-weight="bold" '
                 f'fill="#fff" text-anchor="middle">{name[0]}</text>')
    parts.append(f'<text x="62" y="{y+12}" font-family="{FONT}" font-size="12" fill="#555">{name}</text>')
    # 말풍선
    parts.append(f'<rect x="62" y="{y+18}" width="{W-62-24}" height="{box_h}" rx="10" '
                 f'fill="#ffffff" stroke="#d7dde3" stroke-width="1"/>')
    for i, (s, ul) in enumerate(lines):
        ty = y + 18 + PAD_TOP + LINE_H * i + 14
        parts.append(f'<text x="76" y="{ty}" font-family="{FONT}" font-size="13.5" '
                     f'fill="#1b1b1b">{s}</text>')
        if ul:
            parts.append(f'<line x1="76" y1="{ty+4}" x2="{W-40}" y2="{ty+4}" '
                         f'stroke="#8a1c1c" stroke-width="1.2"/>')
    y += 18 + box_h + GAP

foot = ('※ ㉠은 서연의 발언에서 밑줄 친 부분 전체를, ㉡은 지호의 발언에서 밑줄 친 부분 전체를 가리킨다.')
parts.append(f'<text x="{W/2}" y="{y+8}" font-family="{FONT}" font-size="12" '
             f'fill="#444" text-anchor="middle">{foot}</text>')
H = y + 26
save('fig7_chat', W, H, '\n'.join(parts))
