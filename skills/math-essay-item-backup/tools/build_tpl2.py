#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""[실습과제] 서·논술형 평가 문항 개발 서식(안) HWPX 채우기.

앞선 겹침 사고에서 확정한 규칙을 그대로 따른다.
1. 채우는 칸의 lineWrap SQUEEZE -> BREAK  (SQUEEZE는 자동 줄바꿈을 하지 않는다)
2. linesegarray에 실제 줄 수만큼 lineseg
3. vertpos는 셀 전체에서 누적
4. horzsize는 그 칸에 한글이 써 둔 값을 재사용
5. 문자 폭은 보수적으로(넓게). 장평/자간을 em에 반영
6. 셀/행/표 높이 = 위아래 여백 + Σ(줄수 x 줄피치)

이 서식은 문항 본문 칸(TBL#5 r0c0) 안에 자료 상자(TBL#6/7)와 조건 상자(TBL#8)가
중첩되어 있다. 따라서 모든 탐색을 깊이 인식으로 하고, 중첩 표를 담은 문단은 보존한다.

사용:
    python3 build_tpl2.py <출력.hwpx> <content.json> [--draft]

    기본은 **최종 모드**다. `_figs`가 가리키는 PNG가 하나라도 없으면
    FileNotFoundError로 즉시 중단한다 — 그림이 빠진 채 최종본이 나가는 것을 막는다.
    `--draft`를 주면 **초안 모드**로, 없는 그림은 자리표시 텍스트로 남기고 계속한다.
    플래그는 두 위치 인자 뒤에만 온다.
"""
import atexit, json, os, re, shutil, sys, tempfile, zipfile
import xml.etree.ElementTree as ET

USAGE = "사용법: python3 build_tpl2.py <출력.hwpx> <content.json> [--draft]"

# 위치 인자 자리에 플래그가 오면 OUT_DIR·콘텐츠 경로를 조용히 잘못 잡는다. 먼저 막는다.
for _i, _a in enumerate(sys.argv[1:3], 1):
    if _a.startswith('-'):
        sys.exit(f"{USAGE}\n  위치 인자 {_i}번에 플래그가 왔다: {_a}")

# 초안 모드. 최종 모드(기본값)에서는 그림 파일 누락이 오류다.
DRAFT_MODE = "--draft" in sys.argv[3:]
for _a in sys.argv[3:]:
    if _a != "--draft":
        sys.exit(f"{USAGE}\n  모르는 인자: {_a}")

SCRATCH = os.path.dirname(os.path.abspath(__file__))
FIG_BASE = [SCRATCH]          # 그림 상대경로의 기준. 슬롯 JSON이 있는 폴더로 바뀐다
TPL_DIR = os.path.join(SCRATCH, 'tpl2')
# 작업 트리는 산출물 옆에 **고유 이름으로** 만들고 끝나면 지운다.
#   · 스크립트 옆(설치된 스킬 안)에 만들면 스킬 폴더가 오염된다.
#   · 고정 이름 out2/를 선삭제하면 사용자의 같은 이름 폴더를 지우고, 같은 폴더의 병렬 빌드끼리 서로를 지운다.
_out_parent = (os.path.dirname(os.path.abspath(sys.argv[1]))
               if len(sys.argv) > 1 else SCRATCH)
_out_stem = os.path.splitext(os.path.basename(sys.argv[1]))[0] if len(sys.argv) > 1 else 'build'
os.makedirs(_out_parent, exist_ok=True)
OUT_DIR = tempfile.mkdtemp(prefix=f'.{_out_stem}.out2-', dir=_out_parent)
atexit.register(shutil.rmtree, OUT_DIR, ignore_errors=True)
SECTION = os.path.join(TPL_DIR, 'Contents', 'section0.xml')
HEADER = os.path.join(TPL_DIR, 'Contents', 'header.xml')

sys.path.insert(0, SCRATCH)
import metrics as MT                                  # noqa: E402
import img_embed as IE                                # noqa: E402

# [그림 N] 자리표시 → PNG. 캡션은 자리표시 줄 자체를 그대로 쓴다.
FIGS = {
    '[그림 1]': ('fig1', 'figs/fig1_three_sizes.png'),
    '[그림 2]': ('fig5', 'figs/fig5_menu_board.png'),
    '[그림 3]': ('fig6', 'figs/fig6_owner_memo.png'),
}
USED_FIGS = {}
MT.use_profile('conservative')
MT.HANGABLE = frozenset()

ITEM_CELL = (5, 0, 0)          # 문항 본문 칸 (중첩 표 포함)

SLOTS = {
    'affiliation':   (1, 1, 0), 'name': (1, 3, 0),
    'school_level':  (2, 1, 0), 'subject': (2, 5, 0),
    'grade':         (2, 1, 1), 'unit': (2, 5, 1),
    'task':          (2, 1, 2),
    'std1_text':     (2, 1, 3),
    'std1_A': (2, 4, 3), 'std1_B': (2, 4, 4), 'std1_C': (2, 4, 5),
    'std1_D': (2, 4, 6), 'std1_E': (2, 4, 7),
    'std2_text':     (2, 1, 8),
    'std2_A': (2, 4, 8), 'std2_B': (2, 4, 9), 'std2_C': (2, 4, 10),
    'std2_D': (2, 4, 11), 'std2_E': (2, 4, 12),
    'purpose':       (2, 1, 13),
    'item1_type': (3, 1, 1), 'item1_form': (3, 2, 1), 'item1_element': (3, 3, 1),
    'item2_type': (3, 1, 2), 'item2_form': (3, 2, 2), 'item2_element': (3, 3, 2),
    'item3_type': (3, 1, 3), 'item3_form': (3, 2, 3), 'item3_element': (3, 3, 3),
    'item4_type': (3, 1, 4), 'item4_form': (3, 2, 4), 'item4_element': (3, 3, 4),
    'lesson1_act': (4, 1, 1), 'lesson1_eval': (4, 2, 1),
    'lesson2_act': (4, 1, 2), 'lesson2_eval': (4, 2, 2),
    'lesson3_act': (4, 1, 3), 'lesson3_eval': (4, 2, 3),
    'lesson4_act': (4, 1, 4), 'lesson4_eval': (4, 2, 4),
    'lesson5_act': (4, 1, 5), 'lesson5_eval': (4, 2, 5),
    # 조건 상자 (TBL#8).  자료 상자(TBL#6/7)는 예시(집합)용 말풍선 이미지이므로 제거한다.
    'item_cond':    (8, 1, 2),
    # 예시 답안
    'answer_n1': (9, 0, 1), 'answer_n2': (9, 0, 2),
    'answer_n3': (9, 0, 3), 'answer_n4': (9, 0, 4),
    'answer1': (9, 1, 1), 'answer2': (9, 1, 2),
    'answer3': (9, 1, 3), 'answer4': (9, 1, 4),
    # 채점기준표
    'rubric_n1': (10, 0, 1), 'rubric_n2': (10, 0, 2), 'rubric_n3': (10, 0, 3),
    'rubric_n4': (10, 0, 4), 'rubric_n5': (10, 0, 5), 'rubric_n6': (10, 0, 6),
    'rubric_e1': (10, 1, 1), 'rubric_e2': (10, 1, 2), 'rubric_e3': (10, 1, 3),
    'rubric_e4': (10, 1, 4), 'rubric_e5': (10, 1, 5), 'rubric_e6': (10, 1, 6),
    'rubric_p1': (10, 2, 1), 'rubric_c1': (10, 3, 1),
    'rubric_p2': (10, 2, 2), 'rubric_c2': (10, 3, 2),
    'rubric_p3': (10, 2, 3), 'rubric_c3': (10, 3, 3),
    'rubric_p4': (10, 2, 4), 'rubric_c4': (10, 3, 4),
    'rubric_p5': (10, 2, 5), 'rubric_c5': (10, 3, 5),
    'rubric_p6': (10, 2, 6), 'rubric_c6': (10, 3, 6),
    # 성취수준
    'level_A_score': (11, 1, 1), 'level_A_desc': (11, 2, 1),
    'level_B_score': (11, 1, 2), 'level_B_desc': (11, 2, 2),
    'level_C_score': (11, 1, 3), 'level_C_desc': (11, 2, 3),
    'level_D_score': (11, 1, 4), 'level_D_desc': (11, 2, 4),
    'level_E_score': (11, 1, 5), 'level_E_desc': (11, 2, 5),
    'partial': (12, 0, 0), 'caution': (13, 0, 0),
}


def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace('"', '&quot;'))


def own(cell):
    """중첩 표를 걷어낸 셀 문자열.

    <hp:tc> 자식 순서는 subList -> cellAddr -> cellSpan -> cellSz -> cellMargin 이다.
    중첩 표는 subList 안에 있으므로, 중첩 셀의 cellAddr/cellSz 가 이 셀 자신의 것보다
    **먼저** 나온다.  따라서 re.search(첫 매치)를 쓰면 남의 값을 읽는다.
    """
    out, depth, st = cell, 0, None
    cuts = []
    for m in re.finditer(r'<hp:tbl[ >]|</hp:tbl>', cell):
        if m.group(0).startswith('</'):
            depth -= 1
            if depth == 0:
                cuts.append((st, m.end()))
        else:
            if depth == 0:
                st = m.start()
            depth += 1
    for a, b in reversed(cuts):
        out = out[:a] + out[b:]
    return out


def last(pattern, cell):
    """셀 자신의 속성(마지막 매치)."""
    ms = list(re.finditer(pattern, own(cell)))
    return ms[-1] if ms else None


def set_own_cellsz(cell, w, h_old, h_new):
    """이 셀 자신의 cellSz 만 바꾼다 (마지막 occurrence)."""
    target = f'<hp:cellSz width="{w}" height="{h_old}"/>'
    i = cell.rfind(target)
    if i < 0:
        return cell
    return cell[:i] + f'<hp:cellSz width="{w}" height="{h_new}"/>' + cell[i + len(target):]


def spans(s, tag):
    """s 안에서 깊이 0인 <tag> 요소들의 (start, end)."""
    out, depth, st = [], 0, None
    for m in re.finditer(r'<%s[ >]|</%s>' % (tag, tag), s):
        if m.group(0).startswith('</'):
            depth -= 1
            if depth == 0:
                out.append((st, m.end()))
        else:
            if depth == 0:
                st = m.start()
            depth += 1
    return out


def all_tbl_spans(s):
    """중첩 포함, 문서 순서대로 모든 표의 (start, end)."""
    opens = [m.start() for m in re.finditer(r'<hp:tbl[ >]', s)]
    res = []
    for o in opens:
        depth = 0
        for m in re.finditer(r'<hp:tbl[ >]|</hp:tbl>', s[o:]):
            if m.group(0).startswith('</'):
                depth -= 1
                if depth == 0:
                    res.append((o, o + m.end()))
                    break
            else:
                depth += 1
    return res


# ---------------------------------------------------------------- header.xml
def parse_header():
    txt = open(HEADER, encoding='utf-8').read()
    paras, chars = {}, {}
    for m in re.finditer(r'<hh:paraPr id="(\d+)".*?</hh:paraPr>', txt, re.S):
        blk, pid = m.group(0), m.group(1)
        case = re.search(r'<hp:case\b.*?</hp:case>', blk, re.S)
        seg = case.group(0) if case else blk
        ls = re.search(r'<hh:lineSpacing type="(\w+)" value="(-?\d+)"', seg)
        pv = re.search(r'<hc:prev value="(-?\d+)"', seg)
        nx = re.search(r'<hc:next value="(-?\d+)"', seg)
        paras[pid] = {'ls_type': ls.group(1) if ls else 'PERCENT',
                      'ls_value': int(ls.group(2)) if ls else 100,
                      'prev': int(pv.group(1)) if pv else 0,
                      'next': int(nx.group(1)) if nx else 0}
    for m in re.finditer(r'<hh:charPr id="(\d+)"[^>]*>.*?</hh:charPr>', txt, re.S):
        b, cid = m.group(0), m.group(1)
        r = re.search(r'<hh:ratio hangul="(-?\d+)"', b)
        sp = re.search(r'<hh:spacing hangul="(-?\d+)"', b)
        chars[cid] = {'h': int(re.search(r'height="(\d+)"', b).group(1)),
                      'ratio': int(r.group(1)) if r else 100,
                      'sp': int(sp.group(1)) if sp else 0,
                      'bold': '<hh:bold' in b}
    return paras, chars


PARAPR, CHARPR = parse_header()

# 표 안 글자 통일용: 함초롬바탕 11pt (일반/굵게).  header 주입은 main()에서.
HAM_FONT = 'hangul="11" latin="12" hanja="10" japanese="10" other="10" symbol="8" user="10"'
_max_cid = max(int(k) for k in CHARPR)
CID_N, CID_B = str(_max_cid + 1), str(_max_cid + 2)
CHARPR[CID_N] = {'h': 1100, 'ratio': 100, 'sp': 0, 'bold': False}
CHARPR[CID_B] = {'h': 1100, 'ratio': 100, 'sp': 0, 'bold': True}


def ham_charpr_xml():
    base = ('<hh:charPr id="{cid}" height="1100" textColor="#000000" shadeColor="none" '
            'useFontSpace="0" useKerning="0" symMark="NONE" borderFillIDRef="2">'
            '<hh:fontRef ' + HAM_FONT + '/>'
            '<hh:ratio hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>'
            '<hh:spacing hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>'
            '<hh:relSz hangul="100" latin="100" hanja="100" japanese="100" other="100" symbol="100" user="100"/>'
            '<hh:offset hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/>'
            '{bold}</hh:charPr>')
    return base.format(cid=CID_N, bold='') + base.format(cid=CID_B, bold='<hh:bold/>')


_max_pid = max(int(k) for k in PARAPR)
PID_J, PID_Q, PID_C = str(_max_pid + 1), str(_max_pid + 2), str(_max_pid + 3)
PARAPR[PID_J] = {'ls_type': 'PERCENT', 'ls_value': 120, 'prev': 300, 'next': 200}
PARAPR[PID_Q] = {'ls_type': 'PERCENT', 'ls_value': 120, 'prev': 300, 'next': 200}
PARAPR[PID_C] = {'ls_type': 'PERCENT', 'ls_value': 140, 'prev': 0, 'next': 100}
HANG = {PID_Q: 1308, PID_C: 2100}


def ref_parapr_xml():
    out = []
    for pid, ref in ((PID_J, 'ref_parapr_84.xml'), (PID_Q, 'ref_parapr_97.xml'),
                     (PID_C, 'ref_parapr_96.xml')):
        blk = open(os.path.join(SCRATCH, ref), encoding='utf-8').read()
        blk = re.sub(r'(<hh:paraPr id=")\d+(")', lambda m: m.group(1) + pid + m.group(2), blk, count=1)
        # 문단 테두리 제거: 조건 문단마다 상자가 그려지는 것을 막는다(테두리 없는 7번 사용)
        blk = re.sub(r'(<hh:border borderFillIDRef=")\d+(")', lambda m: m.group(1) + '7' + m.group(2), blk)
        out.append(blk)
    return ''.join(out)


def hang_style(t):
    """발문·조건 문단의 내어쓰기 스타일: (paraPr id, 내어쓰기 폭)."""
    s = t.lstrip('\u3000 ')
    if re.match(r'^문항 \d+[\.．]', t) or re.match(r'^\(\d\)', t):
        return PID_Q, HANG[PID_Q]
    if s[:1] in '㉮㉯㉰㉱':
        return PID_Q, HANG[PID_Q]
    if s[:1] in '①②③④⑤⑥⑦⑧':
        return PID_C, HANG[PID_C]
    if re.match(r'^\((ㄱ|ㄴ|ㄷ|ㄹ)\)', s) or s[:1] in '·•':
        return PID_C, HANG[PID_C]
    return None, 0


def em_of(cid):
    c = CHARPR[cid]
    return max(int(round(c['h'] * (c['ratio'] + c['sp']) / 100.0)), 100)


def pitch_of(pid, em):
    pp = PARAPR[pid]
    if pp['ls_type'] != 'PERCENT':
        return em, 0
    spacing = int(round(em * (pp['ls_value'] - 100) / 100.0))
    return em + spacing, spacing


_pid = [4000]


def make_paras(texts, pid, cid, horzsize, start_cursor=0, auto_style=False):
    em = em_of(cid)
    baseline = int(round(em * 0.85))
    out, total, cursor = [], 0, start_cursor
    for t in texts:
        _pid[0] += 1
        p_pid, indent = pid, 0
        if auto_style and t.strip():
            st, ind = hang_style(t)
            if st:
                p_pid, indent = st, ind
            else:
                p_pid = PID_J
        pitch, spacing = pitch_of(p_pid, em)
        prev, nxt = PARAPR[p_pid]['prev'], PARAPR[p_pid]['next']
        fig = next((v for k, v in FIGS.items() if t.strip().startswith(k)), None)
        if fig and not os.path.exists(os.path.join(FIG_BASE[0], fig[1])):
            if DRAFT_MODE:
                # 초안 모드에서만 자리표시 문장을 남기고 텍스트로 처리한다
                print(f"   [그림 없음] {fig[1]} — 초안 자리표시 텍스트로 유지")
                fig = None
            else:
                raise FileNotFoundError(
                    f"최종 조판에 필요한 그림 파일이 없음: {fig[1]} "
                    f"(기준 폴더 {FIG_BASE[0]}). "
                    f"그림을 만들어 두거나, 초안이면 --draft를 붙여라.")
        if fig:
            bin_id, rel = fig
            path = os.path.join(FIG_BASE[0], rel)
            pw, ph = IE.png_size(path)
            disp_w = min(horzsize - 400, int((horzsize - 400)))
            # 그림 문단 (가운데 정렬 유지: pid 그대로)
            pxml, disp_h = IE.pic_paragraph(bin_id, disp_w, pw, ph, pid, horzsize, cursor + prev)
            cursor += prev + disp_h + nxt
            total += 1                        # 높이 계산에서 그림은 lineseg 1개로 취급
            out.append(pxml)
            USED_FIGS[bin_id] = path
            # 캡션 문단 (자리표시 텍스트 그대로)
            _pid[0] += 1
            starts_c = MT.wrap(t, horzsize, em=em, word_unit=True)
            total += len(starts_c)
            runs_c = f'<hp:run charPrIDRef="{cid}"><hp:t>{esc(t)}</hp:t></hp:run>'
            cursor += prev
            segs_c = ''.join(
                f'<hp:lineseg textpos="{tp}" vertpos="{cursor + i * pitch}" vertsize="{em}" '
                f'textheight="{em}" baseline="{baseline}" spacing="{spacing}" '
                f'horzpos="0" horzsize="{horzsize}" flags="393216"/>'
                for i, tp in enumerate(starts_c))
            cursor += len(starts_c) * pitch + nxt
            out.append(f'<hp:p id="{_pid[0]}" paraPrIDRef="{pid}" styleIDRef="0" '
                       f'pageBreak="0" columnBreak="0" merged="0">{runs_c}'
                       f'<hp:linesegarray>{segs_c}</hp:linesegarray></hp:p>')
            continue
        starts = MT.wrap(t, horzsize, em=em, word_unit=True) if t else [0]
        if indent and len(starts) > 1:
            cont = starts[1]
            rest = MT.wrap(t[cont:], horzsize - indent, em=em, word_unit=True)
            starts = [0] + [cont + s for s in rest]
        total += len(starts)
        runs = (f'<hp:run charPrIDRef="{cid}"><hp:t>{esc(t)}</hp:t></hp:run>'
                if t else f'<hp:run charPrIDRef="{cid}"/>')
        cursor += prev
        segs = ''.join(
            f'<hp:lineseg textpos="{tp}" vertpos="{cursor + i * pitch}" vertsize="{em}" '
            f'textheight="{em}" baseline="{baseline}" spacing="{spacing}" '
            f'horzpos="0" horzsize="{horzsize}" '
            f'flags="{1441792 if (indent and i) else 393216}"/>'
            for i, tp in enumerate(starts))
        cursor += len(starts) * pitch + nxt
        out.append(f'<hp:p id="{_pid[0]}" paraPrIDRef="{p_pid}" styleIDRef="0" '
                   f'pageBreak="0" columnBreak="0" merged="0">{runs}'
                   f'<hp:linesegarray>{segs}</hp:linesegarray></hp:p>')
    return ''.join(out), total, cursor


def para_height(p):
    """문단 하나가 차지하는 세로 높이 (표를 담은 문단은 표 높이)."""
    lsa = p.rfind('<hp:linesegarray>')
    if lsa < 0:
        return 0
    segs = re.findall(r'<hp:lineseg ([^/]*)/>', p[lsa:])
    if not segs:
        return 0
    h = 0
    for s in segs:
        d = dict(re.findall(r'(\w+)="([^"]*)"', s))
        h += int(d['vertsize']) + int(d['spacing'])
    pid = re.search(r'paraPrIDRef="(\d+)"', p)
    if pid and pid.group(1) in PARAPR:
        h += PARAPR[pid.group(1)]['prev'] + PARAPR[pid.group(1)]['next']
    return h


def cell_needed_height(cell):
    """셀 안 직속 문단들의 높이 합 + 위아래 여백."""
    sl = spans(cell, 'hp:subList')
    if not sl:
        return 0
    a, b = sl[0]
    body = cell[a:b]
    inner = body[body.index('>') + 1:body.rindex('</hp:subList>')]
    total = sum(para_height(inner[x:y]) for x, y in spans(inner, 'hp:p'))
    mg = last(r'<hp:cellMargin left="(\d+)" right="(\d+)" top="(\d+)" bottom="(\d+)"/>', cell)
    if mg:
        total += int(mg.group(3)) + int(mg.group(4))
    return total


def fill_cell(cell, texts, key):
    """일반 셀(중첩 표 없음)의 내용을 통째로 교체."""
    hz = re.search(r'<hp:lineseg [^>]*horzsize="(\d+)"', own(cell))
    szm = last(r'<hp:cellSz width="(\d+)" height="(\d+)"/>', cell)
    mgm = last(r'<hp:cellMargin left="(\d+)" right="(\d+)" top="(\d+)" bottom="(\d+)"/>', cell)
    cw, chh = int(szm.group(1)), int(szm.group(2))
    horz = int(hz.group(1)) if hz else cw - int(mgm.group(1)) - int(mgm.group(2))
    pids = re.findall(r'paraPrIDRef="(\d+)"', cell)
    cids = re.findall(r'charPrIDRef="(\d+)"', cell)
    pid = pids[0] if pids else '0'
    cid = CID_N                                     # 표 안 글자: 함초롬바탕 11pt 통일
    paras, nlines, _ = make_paras(texts, pid, cid, horz,
                                  auto_style=(key == 'item_cond'))
    sl = spans(cell, 'hp:subList')[0]
    body = cell[sl[0]:sl[1]]
    open_tag = body[:body.index('>') + 1].replace('lineWrap="SQUEEZE"', 'lineWrap="BREAK"')
    new_body = open_tag + paras + '</hp:subList>'
    out = cell[:sl[0]] + new_body + cell[sl[1]:]
    need = cell_needed_height(out)
    if need > chh:
        out = set_own_cellsz(out, cw, chh, need)
    print(f"   {key:16} 문단 {len(texts):3} 줄 {nlines:4} pPr {pid:>3} cPr {cid:>3} "
          f"em {em_of(cid):5} hz {horz:6} h {chh}->{max(need, chh)}")
    return out


def fill_item_cell(cell, intro, questions):
    """문항 본문 칸: 중첩 표를 담은 문단은 보존하고 텍스트 문단만 교체."""
    sl = spans(cell, 'hp:subList')[0]
    body = cell[sl[0]:sl[1]]
    open_tag = body[:body.index('>') + 1].replace('lineWrap="SQUEEZE"', 'lineWrap="BREAK"')
    inner = body[body.index('>') + 1:body.rindex('</hp:subList>')]
    kids = [inner[a:b] for a, b in spans(inner, 'hp:p')]
    tbl_paras = [p for p in kids if spans(p, 'hp:tbl')]
    text_paras = [p for p in kids if not spans(p, 'hp:tbl')]
    ref = text_paras[0]
    hz = int(re.search(r'horzsize="(\d+)"', ref).group(1))
    pid = re.search(r'paraPrIDRef="(\d+)"', ref).group(1)
    cid = CID_N                                     # 통일 charPr

    # 자료 상자(첫 중첩 표)는 예시용 말풍선 이미지라 버리고, 조건 상자(마지막)만 남긴다.
    keep = tbl_paras[-1:] if tbl_paras else []
    intro_x, n1, cur = make_paras(intro, pid, cid, hz, 0)
    q_x, n2, cur = make_paras(questions, pid, cid, hz, cur, auto_style=True)
    parts = [intro_x, q_x] + keep
    new_body = open_tag + ''.join(parts) + '</hp:subList>'
    out = cell[:sl[0]] + new_body + cell[sl[1]:]
    szm = last(r'<hp:cellSz width="(\d+)" height="(\d+)"/>', out)
    cw, chh = int(szm.group(1)), int(szm.group(2))
    need = cell_needed_height(out)
    if need > chh:
        out = set_own_cellsz(out, cw, chh, need)
    print(f"   item_body        도입 {n1}줄 + 발문 {n2}줄, 중첩표 {len(tbl_paras)}개 보존, "
          f"h {chh}->{max(need, chh)}")
    return out


def _dup_row(xml, ti, src_row, new_rows, text_map=None):
    """표 ti의 src_row 행을 복제해 new_rows(rowAddr 목록)로 뒤에 삽입."""
    a, b = all_tbl_spans(xml)[ti]
    tbl = xml[a:b]
    off = tbl.index('>') + 1
    inner = tbl[off:tbl.rindex('</hp:tbl>')]
    trs = spans(inner, 'hp:tr')
    src = inner[trs[src_row][0]:trs[src_row][1]]
    add = ''
    for nr in new_rows:
        row = src.replace(f'rowAddr="{src_row}"', f'rowAddr="{nr}"')
        if text_map:
            for old, new in text_map.items():
                row = row.replace(old, new)
        add += row
    new_inner = inner[:trs[-1][1]] + add + inner[trs[-1][1]:]
    new_tbl = tbl[:off] + new_inner + '</hp:tbl>'
    rc = re.search(r'rowCnt="(\d+)"', new_tbl)
    new_tbl = (new_tbl[:rc.start()] + f'rowCnt="{int(rc.group(1)) + len(new_rows)}"'
               + new_tbl[rc.end():])
    return xml[:a] + new_tbl + xml[b:]


def surgery_4items(xml):
    """문항 1~4 체제: T3 문항4 행 추가, T9 답안 행 2개 추가, T10 rowspan 해제."""
    # T3: 문항4 행 (문항3 행 복제)
    xml = _dup_row(xml, 3, 3, [4], {'<hp:t>문항3</hp:t>': '<hp:t>문항4</hp:t>'})
    # T9: 답안 행 r3·r4 (r2 복제)
    xml = _dup_row(xml, 9, 2, [3, 4], {'<hp:t>1-2</hp:t>': '<hp:t></hp:t>'})
    # T10: 열0·열1 rowspan(3) 해제 → 행마다 독립 셀
    a, b = all_tbl_spans(xml)[10]
    tbl = xml[a:b]
    off = tbl.index('>') + 1
    inner = tbl[off:tbl.rindex('</hp:tbl>')]
    trs = spans(inner, 'hp:tr')
    rows = [inner[x:y] for x, y in trs]
    protos = {}
    for base in (1, 4):
        row = rows[base]
        tcs = spans(row, 'hp:tc')
        new_row = row
        for ca, cb in reversed(tcs):
            c = row[ca:cb]
            am = last(r'colAddr="(\d+)" rowAddr="(\d+)"/>', c)
            if int(am.group(1)) > 1:
                continue
            c2 = c.replace('rowSpan="3"', 'rowSpan="1"')
            new_row = new_row[:ca] + c2 + new_row[cb:]
            zm = last(r'<hp:cellSz width="(\d+)" height="(\d+)"/>', c2)
            proto = c2.replace(f'rowAddr="{base}"', 'rowAddr="@R@"')
            proto = re.sub(r'<hp:t>[^<]*</hp:t>', '<hp:t></hp:t>', proto)
            if int(zm.group(2)) > 1000:
                proto = set_own_cellsz(proto, int(zm.group(1)), int(zm.group(2)), 1000)
            protos[int(am.group(1))] = proto
        rows[base] = new_row
    for r in (2, 3, 5, 6):
        ins = (protos[0] + protos[1]).replace('rowAddr="@R@"', f'rowAddr="{r}"')
        row = rows[r]
        first_tc = spans(row, 'hp:tc')[0][0]
        rows[r] = row[:first_tc] + ins + row[first_tc:]
    new_inner = ''
    prev = 0
    for (x, y), row in zip(trs, rows):
        new_inner += inner[prev:x] + row
        prev = y
    new_inner += inner[prev:]
    xml = xml[:a] + tbl[:off] + new_inner + '</hp:tbl>' + xml[b:]
    return xml


# ---------------------------------------------------------------- 채점기준표 v2
RUB_TBL = 10                      # all_tbl_spans 기준 채점기준표 인덱스
RUB_W = (7000, 8200, 2900, 30258)
RUB_HZ = (5980, 7180, 1880, 29238)
RUB_PID = ('68', '74', '74', '93')
RUB_BF_DATA = '31'                # 네 변 SOLID 0.1mm

CELL_TPL = ('<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" '
            'borderFillIDRef="{bf}"><hp:subList id="" textDirection="HORIZONTAL" '
            'lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" '
            'textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">{paras}</hp:subList>'
            '<hp:cellAddr colAddr="{col}" rowAddr="{row}"/>'
            '<hp:cellSpan colSpan="1" rowSpan="{rs}"/>'
            '<hp:cellSz width="{w}" height="{h}"/>'
            '<hp:cellMargin left="510" right="510" top="141" bottom="141"/></hp:tc>')


def _cell_paras(text, col):
    """셀 문단 XML과 필요 높이를 만든다."""
    lines = [x for x in str(text).split('\n')]
    paras, n, cur = make_paras(lines, RUB_PID[col], CID_N, RUB_HZ[col])
    need = cur + 141 * 2
    return paras, max(need, 1000)


def check_class_box(xml, label):
    """분반(교과) 칸의 체크박스 가운데 label(예: '3분반')에 해당하는 것을 CHECKED로 바꾼다."""
    tc = None
    for a, b in spans(xml, 'hp:tc'):
        c = xml[a:b]
        if '1분반' in c and '<hp:checkBtn' in c and len(c) < 12000:
            tc = (a, b)
            break
    if tc is None:
        print("   분반 칸을 찾지 못해 체크박스를 건너뜀")
        return xml
    a, b = tc
    cell = xml[a:b]
    i = cell.find(label)
    if i < 0:
        print(f"   '{label}' 항목을 찾지 못함")
        return xml
    # 그 항목 바로 앞의 checkBtn을 켠다
    j = cell.rfind('<hp:checkBtn', 0, i)
    if j < 0:
        print("   해당 체크박스를 찾지 못함")
        return xml
    end = cell.index('>', j)
    head = cell[j:end + 1]
    if 'value="UNCHECKED"' not in head:
        print("   이미 선택되어 있음")
        return xml
    new_head = head.replace('value="UNCHECKED"', 'value="CHECKED"')
    name = re.search(r'name="([^"]*)"', head)
    print(f"   체크박스 선택: {label} ({name.group(1) if name else '?'})")
    cell = cell[:j] + new_head + cell[end + 1:]
    return xml[:a] + cell + xml[b:]


def build_cond_v4(xml, lines):
    """조건 상자의 장식용 빈 셀을 없애고 1행 1열 표에 텍스트만 이어 넣는다."""
    target = None
    for a, b in all_tbl_spans(xml):
        txt = ''.join(re.findall(r'<hp:t>([^<]*)</hp:t>', xml[a:b]))
        if '조건' in txt and 'colCnt="5"' in xml[a:a + 400]:
            target = (a, b)
            break
    if target is None:
        print("   조건 상자를 찾지 못해 건너뜀")
        return xml
    a, b = target
    tbl = xml[a:b]
    off = tbl.index('>') + 1
    inner = tbl[off:tbl.rindex('</hp:tbl>')]
    prefix = inner[:inner.index('<hp:tr')]
    # 표 전체 폭 = 원래 셀 폭 합
    total_w = 0
    first_tr = inner[inner.index('<hp:tr'):]
    for m in re.finditer(r'<hp:cellAddr colAddr="(\d+)" rowAddr="0"/><hp:cellSpan colSpan="(\d+)"[^/]*/>'
                         r'<hp:cellSz width="(\d+)"', first_tr):
        total_w += int(m.group(3))
    if total_w == 0:
        total_w = 47051
    hz = total_w - 1020
    body = ['〈조 건〉', ''] + list(lines)
    paras, n, cur = make_paras(body, PID_C, CID_N, hz)
    h = cur + 141 * 2
    cell = CELL_TPL.format(bf='31', paras=paras, col=0, row=0, rs=1, w=total_w, h=h)
    new_tbl = tbl[:off] + prefix + '<hp:tr>' + cell + '</hp:tr>' + '</hp:tbl>'
    for pat, rep_ in ((r'rowCnt="\d+"', 'rowCnt="1"'), (r'colCnt="\d+"', 'colCnt="1"')):
        new_tbl = re.sub(pat, rep_, new_tbl, count=1)
    szm = re.search(r'(<hp:sz [^>]*height=")(\d+)(")', new_tbl)
    if szm:
        new_tbl = new_tbl[:szm.start()] + szm.group(1) + str(h) + szm.group(3) + new_tbl[szm.end():]
    print(f"   조건 상자 평문화: 1행 1열, {n}줄")
    return xml[:a] + new_tbl + xml[b:]


def find_rubric_tbl(xml):
    """헤더에 '수행 특성'이 있는 4열 표를 찾는다(인덱스는 편집으로 바뀔 수 있다)."""
    for a, b in all_tbl_spans(xml):
        head = xml[a:a + 400]
        if 'colCnt="4"' not in head:
            continue
        txt = ''.join(re.findall(r'<hp:t>([^<]*)</hp:t>', xml[a:b]))
        if '수행 특성' in txt and '평가요소' in txt:
            return a, b
    raise SystemExit('채점기준표를 찾지 못했습니다')


def build_rubric_v2(xml, rows):
    """채점기준표를 '급간 1개 = 표 1행' 구조로 다시 만든다(문항·요소는 세로 병합)."""
    a, b = find_rubric_tbl(xml)
    tbl = xml[a:b]
    off = tbl.index('>') + 1
    inner = tbl[off:tbl.rindex('</hp:tbl>')]
    header_row = inner[spans(inner, 'hp:tr')[0][0]:spans(inner, 'hp:tr')[0][1]]

    # 연속 동일값 구간 → rowSpan
    def runs(key):
        out, i = [], 0
        while i < len(rows):
            j = i
            while j + 1 < len(rows) and rows[j + 1][key] == rows[i][key]:
                j += 1
            out.append((i, j - i + 1))
            i = j + 1
        return out
    item_runs = {s: n for s, n in runs('item')}
    elem_runs = {s: n for s, n in runs('elem')}

    cells = []            # (row, col, rowspan, text)
    for r, row in enumerate(rows):
        if r in item_runs:
            cells.append((r, 0, item_runs[r], row['item']))
        if r in elem_runs:
            cells.append((r, 1, elem_runs[r], row['elem']))
        cells.append((r, 2, 1, row['score']))
        cells.append((r, 3, 1, row['desc']))

    built = {}
    for r, c, rs, txt in cells:
        paras, need = _cell_paras(txt, c)
        built[(r, c)] = (rs, paras, need)

    # 행 높이: rowSpan 1 셀들의 최대 필요 높이
    hrow = [1000] * len(rows)
    for (r, c), (rs, _, need) in built.items():
        if rs == 1:
            hrow[r] = max(hrow[r], need)
    # rowSpan>1 셀이 더 크면 마지막 행에 부족분을 더한다
    for (r, c), (rs, _, need) in built.items():
        if rs > 1:
            have = sum(hrow[r:r + rs])
            if need > have:
                hrow[r + rs - 1] += need - have

    out_rows = [header_row]
    for r in range(len(rows)):
        cxml = ''
        for c in range(4):
            if (r, c) not in built:
                continue
            rs, paras, _ = built[(r, c)]
            cxml += CELL_TPL.format(bf=RUB_BF_DATA, paras=paras, col=c, row=r + 1, rs=rs,
                                    w=RUB_W[c], h=sum(hrow[r:r + rs]))
        out_rows.append('<hp:tr>' + cxml + '</hp:tr>')

    prefix = inner[:inner.index('<hp:tr')]      # hp:sz·hp:pos·여백 등 보존
    new_inner = prefix + ''.join(out_rows)
    new_tbl = tbl[:off] + new_inner + '</hp:tbl>'
    rc = re.search(r'rowCnt="(\d+)"', new_tbl)
    new_tbl = new_tbl[:rc.start()] + f'rowCnt="{len(rows) + 1}"' + new_tbl[rc.end():]
    szm = re.search(r'(<hp:sz [^>]*height=")(\d+)(")', new_tbl)
    hdr_h = int(re.search(r'height="(\d+)"', header_row).group(1))
    total = hdr_h + sum(hrow)
    if szm:
        new_tbl = new_tbl[:szm.start()] + szm.group(1) + str(total) + szm.group(3) + new_tbl[szm.end():]
    print(f"   채점기준표 v2: {len(rows)}행 (헤더 제외), 표높이 {total}")
    return xml[:a] + new_tbl + xml[b:]


def thin_borders(hdr_txt):
    """모든 테두리를 얇은 실선(0.1 mm)으로 통일한다."""
    n = [0]

    def fix(m):
        s = m.group(0)
        t2 = re.search(r'type="([^"]+)"', s).group(1)
        w = re.search(r'width="([^"]+)"', s).group(1)
        if t2 == 'NONE':
            return s
        s2 = re.sub(r'width="[^"]+"', 'width="0.1 mm"', s)
        s2 = re.sub(r'type="[^"]+"', 'type="SOLID"', s2)
        if s2 != s:
            n[0] += 1
        return s2
    hdr_txt = re.sub(r'<hh:(?:left|right|top|bottom)Border [^/]*/>', fix, hdr_txt)
    print(f"   테두리 얇게: {n[0]}건")
    return hdr_txt


def get_cell(xml, ti, col, row):
    """표 ti의 직속 셀 (col,row)의 (start,end) — xml 전체 기준 절대 좌표."""
    a, b = all_tbl_spans(xml)[ti]
    tbl = xml[a:b]
    off = tbl.index('>') + 1
    inner = tbl[off:tbl.rindex('</hp:tbl>')]
    for ca, cb in spans(inner, 'hp:tc'):
        c = inner[ca:cb]
        am = last(r'<hp:cellAddr colAddr="(\d+)" rowAddr="(\d+)"/>', c)
        if am and (int(am.group(1)), int(am.group(2))) == (col, row):
            return a + off + ca, a + off + cb
    return None


def main():
    print(f"모드: {'초안(--draft) — 없는 그림은 자리표시 텍스트로 유지' if DRAFT_MODE else '최종 — 그림 파일이 없으면 중단'}")
    cpath = sys.argv[2] if len(sys.argv) > 2 else os.path.join(SCRATCH, 'content2.json')
    content = json.load(open(cpath, encoding='utf-8'))
    FIG_BASE[0] = os.path.dirname(os.path.abspath(cpath))
    if '_figs' in content:                      # 콘텐츠별 그림 매핑 오버라이드
        FIGS.clear()
        FIGS.update({k: tuple(v) for k, v in content.pop('_figs').items()})
    xml = open(SECTION, encoding='utf-8').read()
    rub_rows = content.pop('rubric_rows', None)
    if 'item4_type' in content:
        xml = surgery_4items(xml)
        print("표 수술: T3 문항4 행 / T9 답안 4행 / T10 채점기준 rowspan 해제")
    if rub_rows:
        for k in list(content):
            if k.startswith('rubric_'):
                content.pop(k)
        xml = build_rubric_v2(xml, rub_rows)
    cbox = content.pop('_check_class', None)
    if cbox:
        xml = check_class_box(xml, cbox)
    if content.pop('_flat_cond', None):
        cond_lines = content.pop('item_cond', [])
        xml = build_cond_v4(xml, cond_lines if isinstance(cond_lines, list) else [cond_lines])

    pp = re.search(r'<hp:pagePr [^>]*height="(\d+)"', xml)
    mg = re.search(r'<hp:margin ([^/]*)/>', xml)
    md = dict(re.findall(r'(\w+)="(\d+)"', mg.group(1)))
    page_usable = (int(pp.group(1)) - int(md['top']) - int(md['bottom'])
                   - int(md['header']) - int(md['footer']))
    print(f"한 쪽 가용 높이 {page_usable}\n== 칸 채우기 ==")

    # 문서 뒤에서부터 채워야 앞의 좌표가 유지된다
    jobs = []
    for key, addr in SLOTS.items():
        if key in content:
            jobs.append((key, addr, content[key]))
    if 'item_intro' in content or 'item_questions' in content:
        jobs.append(('__item__', ITEM_CELL, None))

    # 문서 뒤쪽 칸부터 채운다.  중첩 셀(자식)이 부모보다 뒤에 있으므로 자식이 먼저 처리되고,
    # 부모 칸은 채우기 직전에 좌표를 다시 구해 최신 내용을 반영한다.
    order = []
    for key, (ti, col, row), val in jobs:
        loc = get_cell(xml, ti, col, row)
        if loc is None:
            sys.exit(f'slot {key}: cell T{ti}({col},{row}) not found')
        order.append((loc[0], key, (ti, col, row), val))

    for _pos, key, (ti, col, row), val in sorted(order, key=lambda r: -r[0]):
        s, e = get_cell(xml, ti, col, row)
        cell = xml[s:e]
        if key == '__item__':
            new_c = fill_item_cell(cell,
                                   content.get('item_intro', []),
                                   content.get('item_questions', []))
        else:
            texts = [val] if isinstance(val, str) else list(val)
            new_c = fill_cell(cell, texts, key)
        xml = xml[:s] + new_c + xml[e:]

    # ---- 표 높이: 깊은 것부터 (문서 순서 역순 = 자식이 먼저)
    print("\n== 표/행 높이 =")
    for ti in range(len(all_tbl_spans(xml)) - 1, -1, -1):
        a, b = all_tbl_spans(xml)[ti]
        tbl = xml[a:b]
        off = tbl.index('>') + 1
        inner = tbl[off:tbl.rindex('</hp:tbl>')]
        cells = spans(inner, 'hp:tc')
        rows = {}
        for ca, cb in cells:
            c = inner[ca:cb]
            am = last(r'colAddr="(\d+)" rowAddr="(\d+)"/>', c)
            sm = last(r'colSpan="(\d+)" rowSpan="(\d+)"/>', c)
            zm = last(r'<hp:cellSz width="(\d+)" height="(\d+)"/>', c)
            if not (am and sm and zm):
                continue
            if int(sm.group(2)) == 1:
                r = int(am.group(2))
                rows[r] = max(rows.get(r, 0), int(zm.group(2)), cell_needed_height(c))
        # 셀 높이 동기화
        def fix(cm):
            c = cm.group(0)
            am = last(r'colAddr="(\d+)" rowAddr="(\d+)"/>', c)
            sm = last(r'colSpan="(\d+)" rowSpan="(\d+)"/>', c)
            zm = last(r'<hp:cellSz width="(\d+)" height="(\d+)"/>', c)
            if not (am and sm and zm):
                return c
            r, rs = int(am.group(2)), int(sm.group(2))
            w, h = int(zm.group(1)), int(zm.group(2))
            want = sum(rows.get(r + k, 0) for k in range(rs))
            if want > h:
                return set_own_cellsz(c, w, h, want)
            return c
        new_inner = ''
        prev = 0
        for ca, cb in cells:
            new_inner += inner[prev:ca] + fix(re.match(r'.*', inner[ca:cb], re.S))
            prev = cb
        new_inner += inner[prev:]
        total = sum(rows.values())
        # <hp:sz>는 여는 태그 밖(자식)에 있다.  중첩 표가 있어도 첫 번째 hp:sz가 이 표의 것이다.
        new_tbl = tbl[:off] + new_inner + '</hp:tbl>'
        szm = re.search(r'(<hp:sz [^>]*height=")(\d+)(")', new_tbl)
        if szm and total > int(szm.group(2)):
            new_tbl = (new_tbl[:szm.start()] + szm.group(1) + str(total)
                       + szm.group(3) + new_tbl[szm.end():])
        xml = xml[:a] + new_tbl + xml[b:]

        # 부모 셀 안에서 이 표를 담은 문단의 lineseg vertsize 갱신
        na, nb = all_tbl_spans(xml)[ti]
        h_now = int(re.search(r'height="(\d+)"', xml[na:na + 400]).group(1))
        pstart = xml.rfind('<hp:p ', 0, na)
        pend = xml.find('</hp:p>', nb)
        if pstart >= 0 and pend > 0:
            para = xml[pstart:pend + 7]
            lsa = para.rfind('<hp:linesegarray>')
            if lsa >= 0 and '<hp:tbl' in para:
                seg = re.search(r'<hp:lineseg ([^/]*)/>', para[lsa:])
                if seg:
                    d = dict(re.findall(r'(\w+)="([^"]*)"', seg.group(1)))
                    if d.get('vertsize') != str(h_now):
                        d['vertsize'] = d['textheight'] = str(h_now)
                        d['baseline'] = str(int(round(h_now * 0.85)))
                        newseg = '<hp:lineseg ' + ' '.join(f'{k}="{v}"' for k, v in d.items()) + '/>'
                        old = para[lsa:]
                        newpara = para[:lsa] + re.sub(r'<hp:lineseg [^/]*/>', newseg, old, count=1)
                        xml = xml[:pstart] + newpara + xml[pend + 7:]
        print(f"   T{ti}: 표높이 {total}")

    # ---- 표 바깥 문단 재계산
    print("\n== 표 바깥 문단 재계산 ==")

    def top_spans(s_xml):
        out, depth, st = [], 0, None
        for m in re.finditer(r'<hp:p[ >]|</hp:p>', s_xml):
            if m.group(0).startswith('</'):
                depth -= 1
                if depth == 0:
                    out.append((st, m.end()))
            else:
                if depth == 0:
                    st = m.start()
                depth += 1
        return out

    cursor, page = 0, 1
    res, at = [], 0
    for s, e in top_spans(xml):
        para = xml[s:e]
        pm = re.search(r'paraPrIDRef="(\d+)"', para)
        lsa = para.rfind('<hp:linesegarray>')
        if not pm or lsa < 0:
            continue
        pid = pm.group(1)
        lsa_end = para.index('</hp:linesegarray>', lsa) + len('</hp:linesegarray>')
        segs = re.findall(r'<hp:lineseg [^>]*/>', para[lsa:lsa_end])
        if not segs:
            continue
        a0 = dict(re.findall(r'(\w+)="([^"]*)"', segs[0]))
        tb = spans(para, 'hp:tbl')
        if tb:
            vs = int(re.search(r'height="(\d+)"', para[tb[0][0]:tb[0][0] + 400]).group(1))
        else:
            vs = int(a0['vertsize'])
        sp = int(a0['spacing'])
        # 문단 전체 높이 — 표 문단은 lineseg 1개(표 높이), 일반 문단은 줄 수 × 줄 높이.
        n_lines = 1 if tb else len(segs)
        nxt = PARAPR[pid]['next'] if pid in PARAPR else 0
        body = n_lines * (vs + sp) + nxt
        prev = PARAPR[pid]['prev'] if pid in PARAPR else 0
        top = cursor + prev
        if top + body > page_usable:
            top = 0 if body > page_usable else prev
            page += 1
        if top + body > page_usable:
            span = top + body
            page += span // page_usable
            cursor = span % page_usable
        else:
            cursor = top + body
        newsegs = []
        for i, seg in enumerate(segs):
            d = dict(re.findall(r'(\w+)="([^"]*)"', seg))
            d['vertsize'] = d['textheight'] = str(vs)
            d['baseline'] = str(int(round(vs * 0.85)))
            d['vertpos'] = str(top + i * (vs + sp))
            newsegs.append('<hp:lineseg ' + ' '.join(f'{k}="{v}"' for k, v in d.items()) + '/>')
        t = ''.join(re.findall(r'<hp:t>([^<]*)</hp:t>', para if not tb else para[:tb[0][0]]))[:20]
        print(f"   pPr {pid:>3} vs {vs:7d} -> vertpos {top:6d} (p{page}) "
              f"{'[표]' if tb else repr(t)}")
        res.append(xml[at:s + lsa])
        res.append('<hp:linesegarray>' + ''.join(newsegs) + '</hp:linesegarray>')
        at = s + lsa_end
    res.append(xml[at:])
    xml = ''.join(res)

    # ---- 출력
    shutil.copytree(TPL_DIR, OUT_DIR, dirs_exist_ok=True)
    hdr_txt = open(os.path.join(OUT_DIR, 'Contents', 'header.xml'), encoding='utf-8').read()
    hdr_txt = thin_borders(hdr_txt)
    if f'<hh:paraPr id="{PID_J}"' not in hdr_txt:
        hdr_txt = hdr_txt.replace('</hh:paraProperties>', ref_parapr_xml() + '</hh:paraProperties>')
        mp = re.search(r'(<hh:paraProperties itemCnt=")(\d+)(")', hdr_txt)
        hdr_txt = (hdr_txt[:mp.start()] + mp.group(1) + str(int(mp.group(2)) + 3)
                   + mp.group(3) + hdr_txt[mp.end():])
    if f'id="{CID_N}"' not in hdr_txt:
        hdr_txt = hdr_txt.replace('</hh:charProperties>', ham_charpr_xml() + '</hh:charProperties>')
        m9 = re.search(r'(<hh:charProperties itemCnt=")(\d+)(")', hdr_txt)
        hdr_txt = hdr_txt[:m9.start()] + m9.group(1) + str(int(m9.group(2)) + 2) + m9.group(3) + hdr_txt[m9.end():]
        open(os.path.join(OUT_DIR, 'Contents', 'header.xml'), 'w', encoding='utf-8').write(hdr_txt)
    open(os.path.join(OUT_DIR, 'Contents', 'section0.xml'), 'w', encoding='utf-8').write(xml)
    ET.parse(os.path.join(OUT_DIR, 'Contents', 'section0.xml'))
    if USED_FIGS:
        IE.register_images(OUT_DIR, USED_FIGS)
        print(f"   그림 {len(USED_FIGS)}개 삽입: {sorted(USED_FIGS)}")

    # 미리보기: 가장 안쪽 문단 단위로 묶는다 (문단 하나 = 한 줄)
    prv = []
    for pm in re.finditer(r'<hp:p [^>]*>((?:(?!<hp:p[ >]).)*?)</hp:p>', xml, re.S):
        t = ''.join(re.findall(r'<hp:t>([^<]*)</hp:t>', pm.group(1)))
        t = (t.replace('&amp;', '&').replace('&lt;', '<')
              .replace('&gt;', '>').replace('&quot;', '"'))
        if t.strip():
            prv.append(t)
    open(os.path.join(OUT_DIR, 'Preview', 'PrvText.txt'), 'w',
         encoding='utf-8').write('\n'.join(prv))

    # 서식이 갖고 있던 미참조 BinData(예시용 말풍선 이미지)를 산출물에 넣지 않는다.
    # 넣어 두면 조판 뒤 별도 제거 단계를 거쳐야 하고, 그 단계를 빠뜨리면 검증이 FAIL한다.
    _hpf_path = os.path.join(OUT_DIR, 'Contents', 'content.hpf')
    _hpf = open(_hpf_path, encoding='utf-8').read()
    _used = set(re.findall(r'binaryItemIDRef="([^"]+)"', xml))
    _dropped = []
    for _id, _href in re.findall(r'<opf:item id="([^"]+)" href="(BinData/[^"]+)"', _hpf):
        if _id not in _used:
            _hpf = re.sub(r'<opf:item id="%s"[^>]*/>' % re.escape(_id), '', _hpf)
            _dead = os.path.join(OUT_DIR, *_href.split('/'))
            if os.path.exists(_dead):
                os.remove(_dead)
            _dropped.append(_href)
    if _dropped:
        open(_hpf_path, 'w', encoding='utf-8').write(_hpf)
        print(f"   미참조 BinData 제외: {_dropped}")

    # 원자적 공개 — 같은 이름으로 동시에 쓰더라도 반쯤 쓰인 zip이 남지 않는다.
    out_path = os.path.abspath(sys.argv[1])
    _tmp_fd, _tmp_out = tempfile.mkstemp(
        prefix='.' + os.path.basename(out_path) + '.', suffix='.part',
        dir=os.path.dirname(out_path))
    os.close(_tmp_fd)
    zf = zipfile.ZipFile(_tmp_out, 'w')
    zf.write(os.path.join(OUT_DIR, 'mimetype'), 'mimetype', compress_type=zipfile.ZIP_STORED)
    for root, _d, files in os.walk(OUT_DIR):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, OUT_DIR)
            if rel != 'mimetype':
                zf.write(full, rel, compress_type=zipfile.ZIP_DEFLATED)
    zf.close()
    os.replace(_tmp_out, out_path)      # 같은 이름으로 동시에 써도 반쯤 쓰인 파일이 남지 않는다
    print(f"\nwrote {out_path}")

    errs = 0
    for a, b in all_tbl_spans(xml):
        tbl = xml[a:b]
        off = tbl.index('>') + 1
        inner = tbl[off:tbl.rindex('</hp:tbl>')]
        for ca, cb in spans(inner, 'hp:tc'):
            c = inner[ca:cb]
            lw = re.search(r'lineWrap="(\w+)"', c)
            sl = spans(c, 'hp:subList')
            if not sl:
                continue
            bd = c[sl[0][0]:sl[0][1]]
            ib = bd[bd.index('>') + 1:bd.rindex('</hp:subList>')]
            for pa, pb in spans(ib, 'hp:p'):
                n = len(re.findall(r'<hp:lineseg ', ib[pa:pb]))
                if lw and lw.group(1) == 'SQUEEZE' and n > 1:
                    errs += 1
    print(f"\n== 자체 점검 ==\n   lineseg {len(re.findall(r'<hp:lineseg ', xml))}개, "
          f"SQUEEZE 다중줄 위반 {errs}건")


if __name__ == '__main__':
    main()
