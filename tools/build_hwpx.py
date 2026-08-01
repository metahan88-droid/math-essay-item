#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fill the 사전과제 HWPX template with content from content.json.

content.json maps slot keys to text (str = single para, list[str] = multiple paras).
Slots are addressed by (table_index, colAddr, rowAddr).

v3 changes (line-layout cache rebuilt from scratch)
--------------------------------------------------
1.  <hp:linesegarray> now carries ONE <hp:lineseg> per rendered line, produced by
    metrics.wrap() (conservative Malgun-Gothic width model, 어절 단위 줄바꿈).
2.  vertpos / spacing / pitch are derived from the paraPr's lineSpacing read out
    of header.xml -- no more hard-coded spacing="720".
3.  horzsize is taken from the lineseg Hangul itself wrote into that cell
    (cellW - marginL - marginR is off by 1..3 HWPUNIT in 5 of 9 cell widths).
4.  subList/@lineWrap SQUEEZE -> BREAK on every filled cell.  SQUEEZE means
    "자간을 조종하여 한 줄을 유지" -- a SQUEEZE cell never auto-wraps, which is the
    real reason long paragraphs render as one overlapping black bar.  Evidence:
    across 342 Hangul-authored *.hwpx (14,766 SQUEEZE paragraphs) not one
    SQUEEZE paragraph wraps automatically; all 26 multi-line ones are explicit
    <hp:lineBreak/>.  Both auto-wrapping paragraphs in this very template are
    lineWrap="BREAK".
5.  charPrIDRef 58 -> 59 (58 is the same style + <hh:bold/>).
6.  left-aligned body cells use paraPr 14 (JUSTIFY 130%, prev=next=0) instead of
    73 (prev=700 injected between every paragraph, and 120% != the 720 spacing
    the old builder wrote).
7.  cell / row / table heights follow  h = marginTop+marginBottom + sum(lines*pitch).
8.  body-level (outside-table) linesegs are re-flowed: anchor vertsize := new
    table height, vertpos re-accumulated with a page reset at PAGE_USABLE.
"""
import json, os, re, shutil, sys, zipfile
import xml.etree.ElementTree as ET

SCRATCH = os.path.dirname(os.path.abspath(__file__))
TPL_DIR = os.path.join(SCRATCH, 'template')
OUT_DIR = os.path.join(SCRATCH, 'out')
SECTION = os.path.join(TPL_DIR, 'Contents', 'section0.xml')
HEADER = os.path.join(TPL_DIR, 'Contents', 'header.xml')

sys.path.insert(0, SCRATCH)
import metrics as MT                      # noqa: E402

# conservative profile: every glyph width is an UPPER bound, so a cached line can
# only ever be shorter than what Hangul would lay out -> ragged, never overflowing.
MT.use_profile('conservative')
# no 문장부호 매달기: a hanging 1200-wide punctuation would stick 690 HWPUNIT past
# the 510 right cell margin.  Disabling it only ever breaks earlier.
MT.HANGABLE = frozenset()

P = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'

LEFT_PARAPR = '14'      # JUSTIFY 130%, breakLatin/NonLatin KEEP_WORD, prev=next=0
CENTER_PARAPR = '74'    # CENTER 160%, prev=next=0
CHARPR = '59'           # == charPr 58 minus <hh:bold/>
FLAGS = '393216'        # 54/54 linesegs in the template

# slot -> (table_idx, colAddr, rowAddr, style)  style: 'center' | 'left'
SLOTS = {
    'subject':        (1, 1, 0, 'center'),
    'school_level':   (1, 3, 0, 'center'),
    'affiliation':    (1, 1, 1, 'center'),
    'name':           (1, 3, 1, 'center'),
    'eval_type':      (2, 1, 0, 'left'),
    'unit':           (2, 1, 1, 'left'),
    'standards':      (2, 1, 2, 'left'),
    'old_item':       (2, 1, 3, 'left'),
    'link_analysis':  (3, 1, 1, 'left'),
    'thinking_level': (3, 1, 2, 'left'),
    'response_char':  (3, 1, 3, 'left'),
    'improve_needs':  (3, 1, 4, 'left'),
    'improve_dir':    (4, 2, 0, 'left'),
    'new_item':       (4, 2, 1, 'left'),
    'rubric_elements': (4, 2, 2, 'left'),
    'rubric_criteria': (4, 2, 3, 'left'),
    'training_wish':  (5, 0, 0, 'left'),
}


def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace('"', '&quot;'))


# ---------------------------------------------------------------- header.xml
def parse_header():
    txt = open(HEADER, encoding='utf-8').read()
    paras, chars = {}, {}
    for m in re.finditer(r'<hh:paraPr id="(\d+)".*?</hh:paraPr>', txt, re.S):
        blk, pid = m.group(0), m.group(1)
        case = re.search(r'<hp:case\b.*?</hp:case>', blk, re.S)
        seg = case.group(0) if case else blk          # hp:case is what Hangul typesets with
        ls = re.search(r'<hh:lineSpacing type="(\w+)" value="(-?\d+)"', seg)
        bs = re.search(r'<hh:breakSetting\b[^>]*>', blk).group(0)
        al = re.search(r'<hh:align horizontal="(\w+)"', blk)
        paras[pid] = {
            'ls_type': ls.group(1), 'ls_value': int(ls.group(2)),
            'prev': int(re.search(r'<hc:prev value="(-?\d+)"', seg).group(1)),
            'next': int(re.search(r'<hc:next value="(-?\d+)"', seg).group(1)),
            'intent': int(re.search(r'<hc:intent value="(-?\d+)"', seg).group(1)),
            'breakNonLatinWord': re.search(r'breakNonLatinWord="(\w+)"', bs).group(1),
            'breakLatinWord': re.search(r'breakLatinWord="(\w+)"', bs).group(1),
            'align': al.group(1) if al else '?',
        }
    for m in re.finditer(r'<hh:charPr id="(\d+)"[^>]*height="(\d+)"', txt):
        chars[m.group(1)] = int(m.group(2))
    return paras, chars


PARAPR, CHARPR_H = parse_header()


def pitch_of(parapr_id, char_h):
    """(pitch, spacing) in HWPUNIT.  spacing = char_h*(pct-100)/100, pitch = char_h+spacing
    -- verified on all 6 paraPr/charPr combinations present in the template."""
    pp = PARAPR[parapr_id]
    assert pp['ls_type'] == 'PERCENT', (parapr_id, pp['ls_type'])
    spacing = int(round(char_h * (pp['ls_value'] - 100) / 100.0))
    return char_h + spacing, spacing


def word_unit_of(parapr_id):
    """어절 단위(True) vs 글자 단위(False).

    The two diagnoses disagree on the direction of the breakNonLatinWord mapping.
    어절 단위 breaks at or BEFORE every 글자 단위 break, so its lines are always a
    prefix of the character-wise ones and can never be wider.  Under an unresolved
    mapping the safe answer is therefore 어절 단위 for both.
    """
    return True


# ------------------------------------------------------------ paragraph build
_pid = [1000]


def make_paras(texts, style, horzsize):
    """-> (xml, [line_count per paragraph], pitch)

    vertpos accumulates over the whole cell, it does NOT restart per paragraph.
    Template evidence: the two-paragraph cells of table 4 (paraPr 71, pitch 1560)
    carry vertpos 0 and 1560.
    """
    parapr = CENTER_PARAPR if style == 'center' else LEFT_PARAPR
    char_h = CHARPR_H[CHARPR]
    pitch, spacing = pitch_of(parapr, char_h)
    baseline = int(round(char_h * 0.85))
    wu = word_unit_of(parapr)
    prev, nxt = PARAPR[parapr]['prev'], PARAPR[parapr]['next']
    out, counts, cursor = [], [], 0
    for t in texts:
        _pid[0] += 1
        starts = MT.wrap(t, horzsize, em=char_h, word_unit=wu) if t else [0]
        counts.append(len(starts))
        runs = (f'<hp:run charPrIDRef="{CHARPR}"><hp:t>{esc(t)}</hp:t></hp:run>'
                if t else f'<hp:run charPrIDRef="{CHARPR}"/>')
        cursor += prev
        segs = ''.join(
            f'<hp:lineseg textpos="{tp}" vertpos="{cursor + i * pitch}" vertsize="{char_h}" '
            f'textheight="{char_h}" baseline="{baseline}" spacing="{spacing}" '
            f'horzpos="0" horzsize="{horzsize}" flags="{FLAGS}"/>'
            for i, tp in enumerate(starts))
        cursor += len(starts) * pitch + nxt
        out.append(
            f'<hp:p id="{_pid[0]}" paraPrIDRef="{parapr}" styleIDRef="0" '
            f'pageBreak="0" columnBreak="0" merged="0">{runs}'
            f'<hp:linesegarray>{segs}</hp:linesegarray></hp:p>')
    return ''.join(out), counts, pitch


# ------------------------------------------------------------- ground truth
def selftest():
    """Regression gate: must pass before anything is written."""
    print('== ground-truth 대조 (conservative, 어절 단위, 매달기 없음) ==')
    ok = late = 0
    for label, text, hz, em, wu, want in MT.TEMPLATE_CASES:
        got = MT.wrap(text, hz, em=em, word_unit=wu)
        print(f'   [{"PASS" if got == want else "FAIL"}] {label}  want={want} got={got}')
        if got != want:
            sys.exit('ground-truth 대조 실패 - 빌드 중단')
    for label, text, hz, em, wu, want in MT.EXTRA_CASES:
        got = MT.wrap(text, hz, em=em, word_unit=wu)
        exact = got == want
        is_late = any(a > b for a, b in zip(got, want))
        ok += exact
        late += is_late
        print(f'   [{"PASS " if exact else ("LATE!" if is_late else "early")}] {label}'
              f'  want={want} got={got}')
    print(f'   -> 템플릿 2/2 정확, 추가 사례 {ok}/{len(MT.EXTRA_CASES)} 정확, '
          f'늦게 끊음 {late}/{len(MT.EXTRA_CASES)}')
    if late:
        sys.exit('일부 사례에서 한글보다 늦게 끊음 - 셀 넘침 위험, 빌드 중단')
    # vertical parameters, checked against every lineseg in the template
    tpl = open(SECTION, encoding='utf-8').read()
    root = ET.fromstring(tpl)
    bad = 0
    for seg in root.iter(P + 'lineseg'):
        vs = int(seg.get('vertsize'))
        if int(seg.get('baseline')) != int(round(vs * 0.85)):
            bad += 1
        if seg.get('flags') != FLAGS or seg.get('horzpos') != '0':
            bad += 1
    print(f'   템플릿 lineseg 세로 파라미터 위반: {bad}건')
    if bad:
        sys.exit('세로 파라미터 모델 불일치 - 빌드 중단')


# ------------------------------------------------------------------- helpers
def cells_of(tbl):
    return [(m.start(), m.end(), m.group(0))
            for m in re.finditer(r'<hp:tc[ >].*?</hp:tc>', tbl, re.S)]


def cell_meta(c):
    a = re.search(r'<hp:cellAddr colAddr="(\d+)" rowAddr="(\d+)"/>', c)
    s = re.search(r'<hp:cellSpan colSpan="(\d+)" rowSpan="(\d+)"/>', c)
    z = re.search(r'<hp:cellSz width="(\d+)" height="(\d+)"/>', c)
    if not (a and s and z):
        return None
    m = re.search(r'<hp:cellMargin[^>]*left="(\d+)" right="(\d+)" top="(\d+)" bottom="(\d+)"', c)
    return {'col': int(a.group(1)), 'row': int(a.group(2)),
            'colspan': int(s.group(1)), 'rowspan': int(s.group(2)),
            'w': int(z.group(1)), 'h': int(z.group(2)),
            'ml': int(m.group(1)) if m else 510, 'mr': int(m.group(2)) if m else 510,
            'mt': int(m.group(3)) if m else 141, 'mb': int(m.group(4)) if m else 141}


def set_cell_h(c, w, old_h, new_h):
    return c.replace(f'<hp:cellSz width="{w}" height="{old_h}"/>',
                     f'<hp:cellSz width="{w}" height="{new_h}"/>', 1)


# ---------------------------------------------------------------------- main
def main():
    selftest()
    content = json.load(open(os.path.join(SCRATCH, 'content.json'), encoding='utf-8'))
    xml = open(SECTION, encoding='utf-8').read()

    pg = re.search(r'<hp:pagePr[^>]*height="(\d+)"', xml)
    mg = re.search(r'<hp:margin header="(\d+)" footer="(\d+)" gutter="\d+" '
                   r'left="\d+" right="\d+" top="(\d+)" bottom="(\d+)"', xml)
    page_usable = (int(pg.group(1)) - int(mg.group(3)) - int(mg.group(4))
                   - int(mg.group(1)) - int(mg.group(2)))
    print(f'\n== 페이지 가용 높이 {page_usable} ==')

    slots_by_tbl = {}
    for key, (ti, col, row, style) in SLOTS.items():
        slots_by_tbl.setdefault(ti, {})[(col, row)] = (key, style)

    starts = [m.start() for m in re.finditer(r'<hp:tbl ', xml)]
    ends = [m.end() for m in re.finditer(r'</hp:tbl>', xml)]
    assert len(starts) == len(ends) == 6, (len(starts), len(ends))

    report, tbl_heights, filled = [], {}, set()
    pieces, prev_end = [], 0
    for ti in range(len(starts)):
        tbl = xml[starts[ti]:ends[ti]]
        cl = cells_of(tbl)
        metas = [cell_meta(c) for _, _, c in cl]
        new_cells = [c for _, _, c in cl]

        # --- pass 1: fill the slot cells -------------------------------------
        for idx, (cs, ce, c) in enumerate(cl):
            md = metas[idx]
            if md is None:
                continue
            hit = slots_by_tbl.get(ti, {}).get((md['col'], md['row']))
            if not hit:
                continue
            key, style = hit
            if key not in content:
                continue
            filled.add(key)
            val = content[key]
            texts = [val] if isinstance(val, str) else list(val)

            hzm = re.search(r'<hp:lineseg [^>]*horzsize="(\d+)"', c)
            if hzm:                                   # reuse Hangul's own value
                horzsize = int(hzm.group(1))
            else:                                     # quantised fallback
                horzsize = ((md['w'] - md['ml'] - md['mr']) // 4) * 4

            slm = re.search(r'(<hp:subList [^>]*>)(.*?)(</hp:subList>)', c, re.S)
            pre, _, post = slm.groups()
            if style == 'left':
                pre = pre.replace('vertAlign="CENTER"', 'vertAlign="TOP"')
            # SQUEEZE cells never auto-wrap (see module docstring)
            pre = pre.replace('lineWrap="SQUEEZE"', 'lineWrap="BREAK"')

            paras, counts, pitch = make_paras(texts, style, horzsize)
            c2 = c[:slm.start()] + pre + paras + post + c[slm.end():]

            need = md['mt'] + md['mb'] + sum(counts) * pitch
            if need > md['h']:
                c2 = set_cell_h(c2, md['w'], md['h'], need)
                md['h'] = need
            new_cells[idx] = c2
            report.append((key, len(texts), sum(counts), pitch, horzsize, md['h']))

        # --- pass 2: row heights ---------------------------------------------
        rowh = {}
        for idx, md in enumerate(metas):
            if md and md['rowspan'] == 1:
                rowh[md['row']] = max(rowh.get(md['row'], 0), md['h'])
        for idx, md in enumerate(metas):
            if md is None:
                continue
            want = sum(rowh.get(md['row'] + k, 0) for k in range(md['rowspan']))
            want = max(want, md['h'] if md['rowspan'] > 1 else 0)
            if want != md['h']:
                new_cells[idx] = set_cell_h(new_cells[idx], md['w'], md['h'], want)
                md['h'] = want

        # --- pass 3: table container height ----------------------------------
        tbl2, at = [], 0
        for idx, (cs, ce, _) in enumerate(cl):
            tbl2.append(tbl[at:cs]); tbl2.append(new_cells[idx]); at = ce
        tbl2.append(tbl[at:])
        tbl2 = ''.join(tbl2)
        total = sum(rowh.values())
        szm = re.search(r'(<hp:sz [^>]*height=")(\d+)(")', tbl2)
        if szm:
            tbl2 = tbl2[:szm.start()] + szm.group(1) + str(total) + szm.group(3) + tbl2[szm.end():]
        tbl_heights[ti] = total
        print(f'   T{ti}: 표높이 {szm.group(2) if szm else "?"} -> {total}'
              f'   행높이 {[rowh[k] for k in sorted(rowh)]}')

        pieces.append(xml[prev_end:starts[ti]]); pieces.append(tbl2); prev_end = ends[ti]
    pieces.append(xml[prev_end:])
    xml = ''.join(pieces)

    missing = set(k for k in SLOTS if k in content) - filled
    if missing:
        sys.exit(f'슬롯 셀을 찾지 못함: {sorted(missing)}')

    print('\n== 칸별 결과 ==')
    for key, np_, nl, pitch, hz, h in report:
        print(f'   {key:16s} 문단 {np_:3d}  줄 {nl:4d}  pitch {pitch}  '
              f'horzsize {hz:5d}  cell height {h}')

    # ---- body-level (outside-table) lineseg re-flow -------------------------
    xml = reflow_body(xml, tbl_heights, page_usable)

    # ---- emit ---------------------------------------------------------------
    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    shutil.copytree(TPL_DIR, OUT_DIR)
    open(os.path.join(OUT_DIR, 'Contents', 'section0.xml'), 'w', encoding='utf-8').write(xml)
    ET.parse(os.path.join(OUT_DIR, 'Contents', 'section0.xml'))

    prv = []
    for m in re.finditer(r'<hp:tbl .*?</hp:tbl>|<hp:p [^>]*>.*?</hp:p>', xml, re.S):
        t = ''.join(re.findall(r'<hp:t>([^<]*)</hp:t>', m.group(0)))
        t = (t.replace('&amp;', '&').replace('&lt;', '<')
              .replace('&gt;', '>').replace('&quot;', '"'))
        if t.strip():
            prv.append(t)
    open(os.path.join(OUT_DIR, 'Preview', 'PrvText.txt'), 'w', encoding='utf-8').write('\n'.join(prv))

    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SCRATCH, 'output.hwpx')
    if os.path.exists(out_path):
        os.remove(out_path)
    zf = zipfile.ZipFile(out_path, 'w')
    zf.write(os.path.join(OUT_DIR, 'mimetype'), 'mimetype', compress_type=zipfile.ZIP_STORED)
    for root_, _dirs, files in os.walk(OUT_DIR):
        for f in files:
            full = os.path.join(root_, f)
            rel = os.path.relpath(full, OUT_DIR)
            if rel == 'mimetype':
                continue
            zf.write(full, rel, compress_type=zipfile.ZIP_DEFLATED)
    zf.close()
    print('\nwrote', out_path)
    selfcheck(out_path, page_usable)


# ------------------------------------------- body paragraphs (outside tables)
def body_paragraph_spans(xml):
    spans, depth, start = [], 0, None
    for m in re.finditer(r'<hp:p[ >]|</hp:p>', xml):
        if m.group(0).startswith('</'):
            depth -= 1
            if depth == 0:
                spans.append((start, m.end()))
        else:
            if depth == 0:
                start = m.start()
            depth += 1
    return spans


def reflow_body(xml, tbl_heights, page_usable):
    """Body linesegs are page-relative (a Hangul-saved 15-page file resets vertpos
    to 0 fourteen times).  Anchor paragraphs carry the table height as vertsize, so
    every one of them is stale after the tables grow."""
    print('\n== 표 바깥 문단 lineseg 재계산 ==')
    spans = body_paragraph_spans(xml)
    out, at, cursor, ntbl, page = [], 0, 0, 0, 1
    for s, e in spans:
        para = xml[s:e]
        pid = re.search(r'paraPrIDRef="(\d+)"', para).group(1)
        lsa = para.rfind('<hp:linesegarray>')
        if lsa < 0:
            out.append(xml[at:e]); at = e
            continue
        lsa_end = para.index('</hp:linesegarray>', lsa) + len('</hp:linesegarray>')
        segs = re.findall(r'<hp:lineseg [^>]*/>', para[lsa:lsa_end])
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', segs[0]))
        has_tbl = '<hp:tbl ' in para
        vs = int(attrs['vertsize'])
        if has_tbl:
            vs = tbl_heights[ntbl]
            ntbl += 1
        sp = int(attrs['spacing'])
        prev = PARAPR[pid]['prev']
        top = cursor + prev
        if top + vs + sp > page_usable:            # does not fit -> next page
            top = 0 if vs + sp > page_usable else prev
            page += 1
        if top + vs + sp > page_usable:            # spans several pages (a tall table)
            # the split object still occupies (total mod usable) on its LAST page --
            # resetting to 0 would let the next paragraph sit on top of the table tail
            span = top + vs + sp
            page += span // page_usable
            cursor = span % page_usable
        else:
            cursor = top + vs + sp
        newsegs = []
        for i, seg in enumerate(segs):
            a = dict(re.findall(r'(\w+)="([^"]*)"', seg))
            a['vertsize'] = a['textheight'] = str(vs)
            a['baseline'] = str(int(round(vs * 0.85)))
            a['vertpos'] = str(top + i * (vs + sp))
            newsegs.append('<hp:lineseg ' + ' '.join(f'{k}="{v}"' for k, v in a.items()) + '/>')
        txt = ''.join(re.findall(r'<hp:t>([^<]*)</hp:t>', para))[:24]
        print(f'   paraPr {pid:>3s} prev {prev:4d} vertsize {vs:7d} -> vertpos {top:6d} '
              f'(page {page}) {"[표]" if has_tbl else txt!r}')
        out.append(xml[at:s + lsa])
        out.append('<hp:linesegarray>' + ''.join(newsegs) + '</hp:linesegarray>')
        at = s + lsa_end
    out.append(xml[at:])
    return ''.join(out)


# ------------------------------------------------------------- post-build QA
def selfcheck(out_path, page_usable):
    print('\n== 자체 점검 ==')
    z = zipfile.ZipFile(out_path)
    root = ET.fromstring(z.read('Contents/section0.xml').decode('utf-8'))
    errs, warns = [], []
    nseg = ncell_p = 0

    def para_text(p):
        s = []
        for node in p.iter():
            if node.tag == P + 't':
                s.append(node.text or '')
            elif node.tag == P + 'lineBreak':
                s.append('\n')
            elif node.tag == P + 'tbl':
                return None                       # anchor paragraph: not our text
        return ''.join(s)

    def own_char_h(p):
        """max charPr height over the paragraph's OWN runs (never descends into a
        nested table).  Template check: paraPr 70 anchor keeps spacing 520 = 1300*0.4
        even though the table it contains holds 1800-high runs."""
        hs = [CHARPR_H.get(r.get('charPrIDRef'), 1200) for r in p.findall(P + 'run')]
        return max(hs) if hs else 1200

    def check_paras(container, in_cell, horzsize=None):
        """returns the accumulated cell height consumed by these paragraphs"""
        nonlocal nseg, ncell_p
        cursor = 0
        for p in container.findall(P + 'p'):
            mine = 1000 < int(p.get('id') or 0) < 1000000      # generated by us
            kids = list(p)
            lsas = p.findall(P + 'linesegarray')
            if len(lsas) != 1:
                errs.append(f'문단 linesegarray {len(lsas)}개'); continue
            if kids[-1] is not lsas[0]:
                errs.append('linesegarray가 마지막 자식이 아님')
            segs = lsas[0].findall(P + 'lineseg')
            nseg += len(segs)
            if not segs:
                errs.append('lineseg 0개'); continue
            tps = [int(s.get('textpos')) for s in segs]
            if tps[0] != 0:
                errs.append(f'첫 textpos {tps[0]} != 0')
            if any(b <= a for a, b in zip(tps, tps[1:])):
                errs.append(f'textpos 비단조 {tps}')
            t = para_text(p)
            if t is not None and t != '' and tps[-1] >= len(t):
                errs.append(f'마지막 textpos {tps[-1]} >= 길이 {len(t)}: {t[:30]!r}')
            for s in segs:
                if s.get('flags') != FLAGS or s.get('horzpos') != '0':
                    errs.append('flags/horzpos 이상')
                vs = int(s.get('vertsize'))
                if int(s.get('baseline')) != int(round(vs * 0.85)):
                    errs.append('baseline != vertsize*0.85')
            if not in_cell:
                for s in segs:
                    if int(s.get('vertpos')) > page_usable:
                        errs.append(f'본문 vertpos {s.get("vertpos")} > {page_usable}')
                continue
            ncell_p += 1
            pp = p.get('paraPrIDRef')
            char_h = own_char_h(p)
            pitch, spacing = pitch_of(pp, char_h)
            cursor += PARAPR[pp]['prev']
            for i, s in enumerate(segs):
                if int(s.get('vertpos')) != cursor + i * pitch:
                    errs.append(f'vertpos {s.get("vertpos")} != {cursor}+{i}*{pitch} (paraPr {pp})')
                if int(s.get('spacing')) != spacing:
                    errs.append(f'spacing {s.get("spacing")} != {spacing} (paraPr {pp})')
                if mine and horzsize is not None and int(s.get('horzsize')) != horzsize:
                    errs.append(f'horzsize {s.get("horzsize")} != {horzsize}')
            cursor += len(segs) * pitch + PARAPR[pp]['next']
            if mine and t:
                lim = int(segs[0].get('horzsize'))
                for i, a in enumerate(tps):
                    b = tps[i + 1] if i + 1 < len(tps) else len(t)
                    w = MT.line_width(t[a:b].rstrip('\n'), em=char_h)
                    if w > lim:
                        errs.append(f'줄 폭 {w:.0f} > horzsize {lim}: {t[a:b][:30]!r}')
        return cursor

    check_paras(root, in_cell=False)
    for tbl in root.iter(P + 'tbl'):
        for tr in tbl.findall(P + 'tr'):
            for tc in tr.findall(P + 'tc'):
                ca, cs = tc.find(P + 'cellAddr'), tc.find(P + 'cellSpan')
                cz, cm = tc.find(P + 'cellSz'), tc.find(P + 'cellMargin')
                md = {'row': int(ca.get('rowAddr')), 'col': int(ca.get('colAddr')),
                      'rowspan': int(cs.get('rowSpan')), 'colspan': int(cs.get('colSpan')),
                      'w': int(cz.get('width')), 'h': int(cz.get('height')),
                      'mt': int(cm.get('top')) if cm is not None else 141,
                      'mb': int(cm.get('bottom')) if cm is not None else 141}
                sl = tc.find(P + 'subList')
                hz0 = None
                seg0 = sl.find('.//' + P + 'lineseg')
                if seg0 is not None:
                    hz0 = int(seg0.get('horzsize'))
                used = check_paras(sl, in_cell=True, horzsize=hz0)
                generated = any(1000 < int(p.get('id') or 0) < 1000000
                                for p in sl.findall(P + 'p'))
                need = md['mt'] + md['mb'] + used
                if generated:
                    if sl.get('lineWrap') != 'BREAK':
                        errs.append(f'채운 셀 lineWrap={sl.get("lineWrap")} (BREAK 필요)')
                    if md['rowspan'] == 1 and md['h'] < need:
                        errs.append(f'cellSz height {md["h"]} < 필요 {need}')
                if md['h'] > page_usable:
                    warns.append(f'셀 높이 {md["h"]} > 한 쪽 가용 {page_usable}')
    print(f'   lineseg 총 {nseg}개, 셀 안 문단 {ncell_p}개')
    for e in errs[:20]:
        print('   [ERR]', e)
    for w in sorted(set(warns)):
        print('   [WARN]', w)
    print(f'   오류 {len(errs)}건 / 경고 {len(set(warns))}건')
    if errs:
        sys.exit(1)


if __name__ == '__main__':
    main()
