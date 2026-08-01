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
"""
import json, os, re, shutil, sys, zipfile
import xml.etree.ElementTree as ET

SCRATCH = os.path.dirname(os.path.abspath(__file__))
TPL_DIR = os.path.join(SCRATCH, 'tpl3')
OUT_DIR = os.path.join(SCRATCH, 'out3')
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
    'lesson1_act': (4, 1, 1), 'lesson1_eval': (4, 2, 1),
    'lesson2_act': (4, 1, 2), 'lesson2_eval': (4, 2, 2),
    'lesson3_act': (4, 1, 3), 'lesson3_eval': (4, 2, 3),
    'lesson4_act': (4, 1, 4), 'lesson4_eval': (4, 2, 4),
    'lesson5_act': (4, 1, 5), 'lesson5_eval': (4, 2, 5),
    # 조건 상자 (TBL#8).  자료 상자(TBL#6/7)는 예시(집합)용 말풍선 이미지이므로 제거한다.
    'item_cond':    (6, 1, 2),
    # 예시 답안
    'answer_n1': (7, 0, 1), 'answer_n2': (7, 0, 2),
    'answer1': (7, 1, 1), 'answer2': (7, 1, 2),
    # 채점기준표
    'rubric_n1': (8, 0, 1), 'rubric_n2': (8, 0, 4),
    'rubric_e1': (8, 1, 1),
    'rubric_p1': (8, 2, 1), 'rubric_c1': (8, 3, 1),
    'rubric_p2': (8, 2, 2), 'rubric_c2': (8, 3, 2),
    'rubric_p3': (8, 2, 3), 'rubric_c3': (8, 3, 3),
    'rubric_e2': (8, 1, 4),
    'rubric_p4': (8, 2, 4), 'rubric_c4': (8, 3, 4),
    'rubric_p5': (8, 2, 5), 'rubric_c5': (8, 3, 5),
    'rubric_p6': (8, 2, 6), 'rubric_c6': (8, 3, 6),
    # 성취수준
    'level_A_score': (9, 1, 1), 'level_A_desc': (9, 2, 1),
    'level_B_score': (9, 1, 2), 'level_B_desc': (9, 2, 2),
    'level_C_score': (9, 1, 3), 'level_C_desc': (9, 2, 3),
    'level_D_score': (9, 1, 4), 'level_D_desc': (9, 2, 4),
    'level_E_score': (9, 1, 5), 'level_E_desc': (9, 2, 5),
    'partial': (10, 0, 0), 'caution': (11, 0, 0),
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


def make_paras(texts, pid, cid, horzsize, start_cursor=0):
    em = em_of(cid)
    pitch, spacing = pitch_of(pid, em)
    baseline = int(round(em * 0.85))
    prev, nxt = PARAPR[pid]['prev'], PARAPR[pid]['next']
    out, total, cursor = [], 0, start_cursor
    for t in texts:
        _pid[0] += 1
        fig = next((v for k, v in FIGS.items() if t.strip().startswith(k)), None)
        if fig:
            bin_id, rel = fig
            path = os.path.join(SCRATCH, rel)
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
        total += len(starts)
        runs = (f'<hp:run charPrIDRef="{cid}"><hp:t>{esc(t)}</hp:t></hp:run>'
                if t else f'<hp:run charPrIDRef="{cid}"/>')
        cursor += prev
        segs = ''.join(
            f'<hp:lineseg textpos="{tp}" vertpos="{cursor + i * pitch}" vertsize="{em}" '
            f'textheight="{em}" baseline="{baseline}" spacing="{spacing}" '
            f'horzpos="0" horzsize="{horzsize}" flags="393216"/>'
            for i, tp in enumerate(starts))
        cursor += len(starts) * pitch + nxt
        out.append(f'<hp:p id="{_pid[0]}" paraPrIDRef="{pid}" styleIDRef="0" '
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
    cid = cids[0] if cids else '1'
    if CHARPR.get(cid, {}).get('bold'):
        for alt in cids:
            if not CHARPR[alt]['bold']:
                cid = alt
                break
    paras, nlines, _ = make_paras(texts, pid, cid, horz)
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
    cids = [c for c in re.findall(r'charPrIDRef="(\d+)"', ref) if not CHARPR[c]['bold']]
    cid = cids[0] if cids else re.findall(r'charPrIDRef="(\d+)"', ref)[0]

    # 자료 상자(첫 중첩 표)는 예시용 말풍선 이미지라 버리고, 조건 상자(마지막)만 남긴다.
    keep = tbl_paras[-1:] if tbl_paras else []
    intro_x, n1, cur = make_paras(intro, pid, cid, hz, 0)
    q_x, n2, cur = make_paras(questions, pid, cid, hz, cur)
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
    content = json.load(open(os.path.join(SCRATCH, 'content3.json'), encoding='utf-8'))
    xml = open(SECTION, encoding='utf-8').read()

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
        prev = PARAPR[pid]['prev'] if pid in PARAPR else 0
        top = cursor + prev
        if top + vs + sp > page_usable:
            top = 0 if vs + sp > page_usable else prev
            page += 1
        if top + vs + sp > page_usable:
            span = top + vs + sp
            page += span // page_usable
            cursor = span % page_usable
        else:
            cursor = top + vs + sp
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
    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    shutil.copytree(TPL_DIR, OUT_DIR)
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

    out_path = sys.argv[1]
    if os.path.exists(out_path):
        os.remove(out_path)
    zf = zipfile.ZipFile(out_path, 'w')
    zf.write(os.path.join(OUT_DIR, 'mimetype'), 'mimetype', compress_type=zipfile.ZIP_STORED)
    for root, _d, files in os.walk(OUT_DIR):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, OUT_DIR)
            if rel != 'mimetype':
                zf.write(full, rel, compress_type=zipfile.ZIP_DEFLATED)
    zf.close()
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
