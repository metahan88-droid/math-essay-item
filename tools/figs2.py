#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""자료 삽화 — 안내판·대화방·쪽지.

AI 이미지 모델은 한글을 뭉갠다. 자료의 글자가 곧 문항 내용인 이 문항에서는
좌표와 텍스트를 직접 배치해 그리는 것이 정확하고 인쇄 품질도 낫다.
"""
import os

OUT = os.path.dirname(os.path.abspath(__file__)) + '/figs'
os.makedirs(OUT, exist_ok=True)
FONT = "Malgun Gothic, AppleGothic, NanumGothic, sans-serif"

HEAD = ('<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        'viewBox="0 0 {w} {h}">\n<rect width="100%" height="100%" fill="#ffffff"/>')


def save(name, w, h, body):
    open(f'{OUT}/{name}.svg', 'w', encoding='utf-8').write(
        HEAD.format(w=w, h=h) + '\n' + body + '\n</svg>')
    os.system(f'rsvg-convert -w {w*2} -h {h*2} "{OUT}/{name}.svg" -o "{OUT}/{name}.png" 2>/dev/null')
    print(f'  {name}  ({w}x{h})')


def txt(x, y, s, size=14, w='normal', fill='#111', anchor='start', fam=FONT):
    return (f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" '
            f'font-weight="{w}" fill="{fill}" text-anchor="{anchor}">{s}</text>')


# ── 자료 1 : 피자 가게 안내판 ────────────────────────────────────────────
W, H = 660, 300
b = []
b.append('<rect x="14" y="14" width="632" height="272" rx="14" fill="#fffdf5" '
         'stroke="#8a5a2b" stroke-width="3"/>')
b.append('<rect x="14" y="14" width="632" height="52" rx="14" fill="#8a5a2b"/>')
b.append('<rect x="14" y="52" width="632" height="14" fill="#8a5a2b"/>')
b.append(txt(330, 48, '○○피자  가격 안내', 22, 'bold', '#fffdf5', 'middle'))
# 표 헤더
ys = 100
b.append(f'<line x1="44" y1="{ys+8}" x2="616" y2="{ys+8}" stroke="#8a5a2b" stroke-width="1.5"/>')
for x, s in ((56, '크기'), (170, '지름'), (285, '두께'), (395, '한 판 가격'), (540, '페퍼로니')):
    b.append(txt(x, ys, s, 15, 'bold', '#8a5a2b'))
rows = [('미디엄', '24 cm', '2 cm', '16,000원', '16개'),
        ('라지', '30 cm', '2.5 cm', '26,000원', '?'),
        ('자이언트', '36 cm', '3 cm', '32,000원', '?')]
for i, r in enumerate(rows):
    y = ys + 40 + i * 34
    for x, s in zip((56, 170, 285, 395, 540), r):
        bold = 'bold' if x == 56 else 'normal'
        col = '#9e2b25' if s == '?' else '#111'
        b.append(txt(x, y, s, 16, bold, col))
    b.append(f'<line x1="44" y1="{y+11}" x2="616" y2="{y+11}" stroke="#e0d6c2" stroke-width="1"/>')
# 안내 문구
b.append('<rect x="44" y="243" width="572" height="30" rx="6" fill="#fdf1d6" stroke="#d9b45a"/>')
b.append(txt(330, 263, '★ 이번 주 행사 : 미디엄 2판 묶음 30,000원 (정가 32,000원에서 2,000원 할인)',
             14, 'bold', '#8a5a2b', 'middle'))
save('fig5_menu_board', W, H, '\n'.join(b))


# ── 자료 3 : 사장님 쪽지 ────────────────────────────────────────────────
W, H = 660, 268
b = []
b.append('<rect x="20" y="24" width="620" height="206" rx="6" fill="#fffef7" '
         'stroke="#c9bfa4" stroke-width="2"/>')
for i in range(7):
    y = 74 + i * 27
    b.append(f'<line x1="44" y1="{y}" x2="616" y2="{y}" stroke="#e8e2d0" stroke-width="1"/>')
b.append('<rect x="20" y="24" width="620" height="30" fill="#f6efdc"/>')
b.append(txt(40, 45, '✉ 가게 사장님의 쪽지', 15, 'bold', '#7a6a45'))
lines = [('라지와 자이언트를 새로 판매하는데, 두 가지만 여쭙겠습니다.', 'normal', '#111'),
         ('① 어느 크기에서나 페퍼로니 1개당 윗면 넓이가 미디엄과 같아야 같은 정도로', 'normal', '#111'),
         ('   촘촘합니다. 라지와 자이언트에는 각각 몇 개씩 올려야 할까요?', 'normal', '#111'),
         ('② 다음 학기에 부원이 16명이 되면, 자이언트만 주문할 때 몇 판과 페퍼로니 몇 개가', 'normal', '#111'),
         ('   필요할까요? 또 16명분을 한 판에 담는 「패밀리」를 만들려고 하는데, 굽는 기계의', 'normal', '#111'),
         ('   높이 때문에 두께는 미디엄과 같은 2 cm입니다. 지름은 몇 cm여야 할까요?', 'bold', '#8a1c1c')]
for i, (s, w, c) in enumerate(lines):
    b.append(txt(48, 70 + i * 27, s, 14, w, c))
b.append(txt(616, 248, '— ○○피자 사장', 13, 'normal', '#7a6a45', 'end'))
save('fig6_owner_memo', W, H, '\n'.join(b))
print('\n안내판·쪽지 완료. 대화방 도해는 개선된 대사가 확정된 뒤 생성한다.')
