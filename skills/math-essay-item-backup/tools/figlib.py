#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""문항 도해 작도 라이브러리.

글자가 곧 문항 내용인 도해(가격표·대화방·쪽지·실측 도해·크기 비교)는
AI 이미지 모델이 한글을 뭉개므로 여기서 좌표로 직접 그린다.
글자가 없는 분위기 삽화만 gpt-image-2에 맡긴다. references/figures.md 참조.

사용:
    import figlib as F
    F.OUT = "/작업/폴더/figs"          # 저장 위치. 없으면 자동 생성
    F.menu_board("fig1_menu", "○○피자 가격 안내",
                 ["크기","지름","가격"],
                 [["미디엄","24 cm","16,000원"], ["라지","30 cm","26,000원"]],
                 note="★ 이번 주 행사 : 미디엄 2판 30,000원")

모든 함수는 SVG를 쓰고 rsvg-convert로 2배 해상도 PNG를 만든 뒤 (svg경로, png경로)를 반환한다.
rsvg-convert가 없으면 SVG만 남기고 경고한다.
"""
import os
import shutil
import subprocess

# 기본 출력 폴더. 호출부에서 figlib.OUT을 덮어쓰거나 FIGLIB_OUT으로 지정한다.
OUT = os.environ.get("FIGLIB_OUT") or os.path.join(os.getcwd(), "figs")
FONT = "Malgun Gothic, AppleGothic, NanumGothic, sans-serif"

# 색 — 인쇄를 전제로 채도를 낮춘다
INK = "#111111"
SUB = "#555555"
LINE = "#d7dde3"
ACCENT = "#8a1c1c"      # 강조(오개념·핵심 조건)
WARM = "#8a5a2b"        # 안내판 테두리
WARM_BG = "#fffdf5"
PAPER = "#fffef7"
CHAT_BG = "#f4f6f8"


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def txt(x, y, s, size=14, weight="normal", fill=INK, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{_esc(s)}</text>')


def save(name, w, h, body, bg="#ffffff"):
    """SVG를 쓰고 PNG로 변환한다. (svg, png) 경로를 반환."""
    os.makedirs(OUT, exist_ok=True)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}">\n<rect width="100%" height="100%" fill="{bg}"/>\n'
           + body + '\n</svg>')
    sp = os.path.join(OUT, name + ".svg")
    pp = os.path.join(OUT, name + ".png")
    open(sp, "w", encoding="utf-8").write(svg)
    if os.path.exists(pp):
        os.remove(pp)          # 옛 PNG를 새 결과로 오인하지 않도록 먼저 지운다
    converter = shutil.which("rsvg-convert")
    if not converter:
        print(
            f"  {name}  {w}x{h} → SVG만 생성(rsvg-convert 없음). "
            f"`brew install librsvg` 후 다시 실행하면 PNG가 만들어진다."
        )
        return sp, None

    try:
        r = subprocess.run(
            [converter, "-w", str(w * 2), "-h", str(h * 2), sp, "-o", pp],
            capture_output=True,
        )

        if r.returncode != 0:
            detail = r.stderr.decode(errors='replace')[:200]
            raise RuntimeError(f"rsvg-convert 실패({name}): {detail}")

        if not os.path.exists(pp) or os.path.getsize(pp) <= 8:
            raise RuntimeError(f"rsvg-convert가 PNG를 만들지 못함({name})")

        with open(pp, 'rb') as f:
            signature = f.read(8)
        if signature != b'\x89PNG\r\n\x1a\n':
            raise RuntimeError(f"rsvg-convert 결과가 정상 PNG가 아님({name})")

    except Exception:
        if os.path.exists(pp):
            try:
                os.remove(pp)
            except OSError:
                pass
        raise

    print(f"  {name}  {w}x{h} → {pp}")
    return sp, pp


# ────────────────────────────────────────────────────────── 안내판·가격표
def menu_board(name, title, headers, rows, note=None, width=660, col_x=None):
    """가격표·안내판. rows의 '?'는 붉게 표시해 학생이 채울 자리임을 드러낸다."""
    n = len(rows)
    head_h, row_h = 52, 34
    body_h = 34 + head_h + 40 + n * row_h + (44 if note else 10)
    h = body_h + 28
    b = [f'<rect x="14" y="14" width="{width-28}" height="{body_h}" rx="14" '
         f'fill="{WARM_BG}" stroke="{WARM}" stroke-width="3"/>',
         f'<rect x="14" y="14" width="{width-28}" height="{head_h}" rx="14" fill="{WARM}"/>',
         f'<rect x="14" y="{14+head_h-14}" width="{width-28}" height="14" fill="{WARM}"/>',
         txt(width / 2, 48, title, 22, "bold", WARM_BG, "middle")]
    if col_x is None:
        inner = width - 116
        col_x = [56 + int(inner * i / len(headers)) for i in range(len(headers))]
    ys = 14 + head_h + 34
    b.append(f'<line x1="44" y1="{ys+8}" x2="{width-44}" y2="{ys+8}" stroke="{WARM}" stroke-width="1.5"/>')
    for x, s in zip(col_x, headers):
        b.append(txt(x, ys, s, 15, "bold", WARM))
    for i, r in enumerate(rows):
        y = ys + 40 + i * row_h
        for j, (x, s) in enumerate(zip(col_x, r)):
            b.append(txt(x, y, s, 16, "bold" if j == 0 else "normal",
                         ACCENT if str(s).strip() == "?" else INK))
        b.append(f'<line x1="44" y1="{y+11}" x2="{width-44}" y2="{y+11}" stroke="#e0d6c2" stroke-width="1"/>')
    if note:
        ny = ys + 40 + n * row_h + 6
        b.append(f'<rect x="44" y="{ny}" width="{width-88}" height="30" rx="6" fill="#fdf1d6" stroke="#d9b45a"/>')
        b.append(txt(width / 2, ny + 20, note, 14, "bold", WARM, "middle"))
    return save(name, width, h, "\n".join(b))


# ────────────────────────────────────────────────────────── 단체 대화방
def chat(name, title, messages, footnote=None, width=680):
    """오개념을 심는 대화방. messages = [(이름, [(문장, 밑줄여부), ...]), ...]

    밑줄 친 구간이 ㉠·㉡ 같은 오개념 표시 대상이 된다."""
    palette = ["#3b6ea5", "#b0563a", "#4a7d4a", "#7a5aa0", "#a0722f"]
    line_h, pad_t, pad_b, gap, header = 21, 12, 12, 16, 46
    y = header + 12
    b = [f'<rect x="0" y="0" width="{width}" height="{header}" fill="#2f4a63"/>',
         txt(width / 2, 30, title, 17, "bold", "#ffffff", "middle")]
    for k, (who, lines) in enumerate(messages):
        col = palette[k % len(palette)]
        box_h = pad_t + pad_b + line_h * len(lines)
        b.append(f'<circle cx="36" cy="{y+18}" r="15" fill="{col}"/>')
        b.append(txt(36, y + 23, who[0], 13, "bold", "#ffffff", "middle"))
        b.append(txt(62, y + 12, who, 12, "normal", SUB))
        b.append(f'<rect x="62" y="{y+18}" width="{width-86}" height="{box_h}" rx="10" '
                 f'fill="#ffffff" stroke="{LINE}" stroke-width="1"/>')
        for i, item in enumerate(lines):
            s, ul = item if isinstance(item, (tuple, list)) else (item, 0)
            ty = y + 18 + pad_t + line_h * i + 14
            b.append(txt(76, ty, s, 13.5, "normal", INK))
            if ul:
                b.append(f'<line x1="76" y1="{ty+4}" x2="{width-40}" y2="{ty+4}" '
                         f'stroke="{ACCENT}" stroke-width="1.2"/>')
        y += 18 + box_h + gap
    if footnote:
        b.append(txt(width / 2, y + 8, footnote, 12, "normal", "#444444", "middle"))
        y += 26
    return save(name, width, y, "\n".join(b), bg=CHAT_BG)


# ────────────────────────────────────────────────────────── 쪽지·메모
def memo(name, title, lines, signer=None, width=660):
    """의뢰인의 쪽지. lines = [(문장, 굵게여부, 색), ...] 또는 문자열 목록."""
    norm = [(x, "normal", INK) if isinstance(x, str) else x for x in lines]
    lh, top = 27, 70
    body_h = 46 + len(norm) * lh + 40
    h = body_h + 38
    b = [f'<rect x="20" y="24" width="{width-40}" height="{body_h}" rx="6" '
         f'fill="{PAPER}" stroke="#c9bfa4" stroke-width="2"/>']
    for i in range(len(norm) + 1):
        yy = top + 4 + i * lh
        b.append(f'<line x1="44" y1="{yy}" x2="{width-44}" y2="{yy}" stroke="#e8e2d0" stroke-width="1"/>')
    b.append(f'<rect x="20" y="24" width="{width-40}" height="30" fill="#f6efdc"/>')
    b.append(txt(40, 45, title, 15, "bold", "#7a6a45"))
    for i, (s, w, c) in enumerate(norm):
        b.append(txt(48, top + i * lh, s, 14, w, c))
    if signer:
        b.append(txt(width - 44, 24 + body_h - 14, signer, 13, "normal", "#7a6a45", "end"))
    return save(name, width, h, "\n".join(b))


# ────────────────────────────────────────────────────────── 크기 비교(원)
def circles_row(name, title, items, scale=3.0, width=None):
    """지름이 다른 원을 실제 비율로 나란히. items = [(라벨, 지름, 아래설명), ...]"""
    pad, gap = 40, 40
    ds = [it[1] for it in items]
    ws = [d * scale for d in ds]
    W = width or int(pad * 2 + sum(ws) + gap * (len(items) - 1))
    H = int(max(ws) + 130)
    base = H - 56
    b = [txt(W / 2, 28, title, 15, "bold", INK, "middle")]
    x = pad
    for (label, d, sub), w in zip(items, ws):
        r = w / 2
        cx, cy = x + r, base - r
        b.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#f6e0c0" stroke="{WARM}" stroke-width="2"/>')
        # 지름 표시선은 글자 자리를 비우고 좌우로 나눠 그린다
        half = max(len(f"{d} cm") * 4.2, 20)
        b.append(f'<line x1="{cx-r}" y1="{cy}" x2="{cx-half}" y2="{cy}" stroke="{SUB}" '
                 f'stroke-width="1" stroke-dasharray="4 3"/>')
        b.append(f'<line x1="{cx+half}" y1="{cy}" x2="{cx+r}" y2="{cy}" stroke="{SUB}" '
                 f'stroke-width="1" stroke-dasharray="4 3"/>')
        b.append(txt(cx, cy + 4.5, f"{d} cm", 13, "normal", SUB, "middle"))
        b.append(txt(cx, base + 22, label, 15, "bold", WARM, "middle"))
        if sub:
            b.append(txt(cx, base + 42, sub, 12.5, "normal", SUB, "middle"))
        x += w + gap
    return save(name, W, H, "\n".join(b))


# ────────────────────────────────────────────────────────── 실측 도해(직육면체)
def boxes_row(name, title, items, scale=3.4, width=None):
    """아이소메트릭 직육면체를 나란히 놓고 치수를 적는다.
    items = [(라벨, 가로, 세로, 높이, 비고), ...] — 학생이 비를 직접 재는 자료."""
    def one(x0, y0, w_cm, d_cm, h_cm, label, sub):
        W = w_cm * scale
        D = d_cm * scale * 0.5
        H = max(h_cm * scale, 10)
        dx, dy = D * 0.85, D * 0.5
        p = [f'<polygon points="{x0},{y0} {x0+W},{y0} {x0+W},{y0-H} {x0},{y0-H}" '
             f'fill="#f3dbc0" stroke="{WARM}" stroke-width="1.6"/>',
             f'<polygon points="{x0},{y0-H} {x0+W},{y0-H} {x0+W+dx},{y0-H-dy} {x0+dx},{y0-H-dy}" '
             f'fill="#fbeedd" stroke="{WARM}" stroke-width="1.6"/>',
             f'<polygon points="{x0+W},{y0} {x0+W+dx},{y0-dy} {x0+W+dx},{y0-H-dy} {x0+W},{y0-H}" '
             f'fill="#e6c49a" stroke="{WARM}" stroke-width="1.6"/>',
             txt(x0 + W / 2, y0 + 18, f"가로 {w_cm} cm", 12.5, "normal", INK, "middle"),
             txt(x0 + W / 2 + dx + 8, y0 - H - dy - 6, f"세로 {d_cm} cm", 12.5, "normal", INK, "start"),
             txt(x0 + W + dx + 8, y0 - dy / 2 - 2, f"높이 {h_cm} cm", 12.5, "normal", INK, "start"),
             txt(x0 + (W + dx) / 2, y0 - H - dy - 26, label, 14.5, "bold", "#7a4a12", "middle")]
        if sub:
            p.append(txt(x0 + (W + dx) / 2, y0 + 36, sub, 11.5, "normal", SUB, "middle"))
        return "\n".join(p), W + dx + 96

    W = width or int(60 + sum(it[1] * scale + it[2] * scale * 0.425 + 96 for it in items))
    H = int(max(it[3] * scale for it in items) + max(it[2] for it in items) * scale * 0.25 + 190)
    b = [txt(W / 2, 28, title, 15, "bold", INK, "middle")]
    x, base = 30, H - 70
    for (label, w_cm, d_cm, h_cm, sub) in items:
        frag, used = one(x, base, w_cm, d_cm, h_cm, label, sub)
        b.append(frag)
        x += used
    return save(name, W, H, "\n".join(b))


# ────────────────────────────────────────────────────────── 모눈 + 도형
def grid_shape(name, title, cells=14, cell=22, shapes=(), caption=None):
    """모눈 위에 원·정사각형을 올려 칸 수를 세게 하는 탐구용 도해.
    shapes = [("circle", cx, cy, r, 색), ("rect", x, y, w, h, 색)] — 단위는 칸."""
    pad = 34
    W = pad * 2 + cells * cell
    H = pad + cells * cell + (52 if caption else 24) + 24
    b = [txt(W / 2, 24, title, 15, "bold", INK, "middle")]
    g0 = pad
    for i in range(cells + 1):
        b.append(f'<line x1="{g0+i*cell}" y1="{pad+10}" x2="{g0+i*cell}" y2="{pad+10+cells*cell}" '
                 f'stroke="#dfe4ea" stroke-width="1"/>')
        b.append(f'<line x1="{g0}" y1="{pad+10+i*cell}" x2="{g0+cells*cell}" y2="{pad+10+i*cell}" '
                 f'stroke="#dfe4ea" stroke-width="1"/>')
    for s in shapes:
        if s[0] == "circle":
            _, cx, cy, r, col = s
            b.append(f'<circle cx="{g0+cx*cell}" cy="{pad+10+cy*cell}" r="{r*cell}" '
                     f'fill="none" stroke="{col}" stroke-width="2.2"/>')
        elif s[0] == "rect":
            _, x, y, w, h, col = s
            b.append(f'<rect x="{g0+x*cell}" y="{pad+10+y*cell}" width="{w*cell}" height="{h*cell}" '
                     f'fill="none" stroke="{col}" stroke-width="2.2"/>')
    if caption:
        b.append(txt(W / 2, pad + 10 + cells * cell + 30, caption, 12.5, "normal", SUB, "middle"))
    return save(name, W, H, "\n".join(b))


if __name__ == "__main__":
    # 데모 산출물을 스킬 폴더에 쓰지 않는다. 기본은 현재 작업 디렉터리다.
    OUT = os.environ.get("FIGLIB_OUT") or os.path.join(os.getcwd(), "figs_demo")
    print("데모 생성:")
    menu_board("demo_menu", "○○가게 가격 안내", ["크기", "치수", "가격", "개수"],
               [["작은 것", "24 cm", "16,000원", "16개"],
                ["큰 것", "36 cm", "32,000원", "?"]],
               note="★ 행사 : 작은 것 2개 묶음 30,000원")
    chat("demo_chat", "단체 대화방 (어젯밤)",
         [("민재", [("행사 봤어? 두 개 묶음이 더 싸.", 0)]),
          ("서연", [("지름이 1.5배니까 양도 1.5배야.", 1)])],
         footnote="※ 밑줄 친 부분이 ㉠이다.")
    memo("demo_memo", "✉ 사장님의 쪽지",
         ["여쭙고 싶은 것이 두 가지 있습니다.",
          ("① 큰 것에는 몇 개를 올려야 할까요?", "bold", ACCENT)],
         signer="— ○○가게")
    circles_row("demo_circles", "세 가지 크기 (실제 지름 비율)",
                [("미디엄", 24, "두께 2 cm"), ("라지", 30, "두께 2.5 cm"), ("자이언트", 36, "두께 3 cm")])
    boxes_row("demo_boxes", "실측 기록",
              [("스몰", 21, 21, 3, ""), ("빅", 35, 35, 5, ""), ("라지팩", 45, 30, 5, "(옛 상자)")])
    grid_shape("demo_grid", "모눈 위의 원", cells=18, shapes=[
        ("circle", 5, 5, 4, ACCENT), ("circle", 12, 9, 8, "#3b6ea5")],
        caption="칸의 중심이 원 안에 있는 칸을 센다.")
