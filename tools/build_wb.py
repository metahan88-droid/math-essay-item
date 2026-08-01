#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""깊이있는 수업설계 워크북(1~6차시) 채움 빌더.

원칙: 원본 레이아웃 보존을 위해 라벨 뒤 '빈 문단'들에 답안을 줄 단위로 분배한다
(빈 문단 1개 = 렌더 줄 1개, lineseg 캐시 불변).  빈 문단 수를 넘치면 마지막
빈 문단에 잔여 줄을 몰아넣고 그 문단의 lineseg만 재계산한다(개수 정확 원칙).
표 안 빈 셀은 셀 내부 문단 교체 + 셀/행 높이 확장.
"""
import re, sys, os, json, zipfile

S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S)
import metrics as MT
MT.use_profile('conservative')
MT.HANGABLE = frozenset()

SRC = ("/Volumes/ssdmacmini 1/han ex/.claude/uploads/"
       "6981ac5c-4498-45c0-98bf-f487552987cc/85c97102-_________1___.hwpx")


def spans(s, tag):
    out, d, st = [], 0, None
    for m in re.finditer(r'<%s[ >]|</%s>' % (tag, tag), s):
        if m.group(0).startswith('</'):
            d -= 1
            if d == 0:
                out.append((st, m.end()))
        else:
            if d == 0:
                st = m.start()
            d += 1
    return out


def all_tbl(s):
    opens = [m.start() for m in re.finditer(r'<hp:tbl[ >]', s)]
    res = []
    for o in opens:
        d = 0
        for m in re.finditer(r'<hp:tbl[ >]|</hp:tbl>', s[o:]):
            if m.group(0).startswith('</'):
                d -= 1
                if d == 0:
                    res.append((o, o + m.end()))
                    break
            else:
                d += 1
    return res


def p_text(p):
    body = re.sub(r'<hp:tbl.*</hp:tbl>', '', p, flags=re.S) if '<hp:tbl' in p else p
    return ''.join(re.findall(r'<hp:t>([^<]*)</hp:t>', body))


def esc(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace('"', '&quot;'))


def thin_borders(hdr_txt):
    """모든 테두리를 얇은 실선(0.1 mm)으로 통일한다."""
    n = [0]

    def fix(m):
        s = m.group(0)
        t2 = re.search(r'type="([^"]+)"', s).group(1)
        if t2 == 'NONE':
            return s
        s2 = re.sub(r'width="[^"]+"', 'width="0.1 mm"', s)
        s2 = re.sub(r'type="[^"]+"', 'type="SOLID"', s2)
        if s2 != s:
            n[0] += 1
        return s2
    out = re.sub(r'<hh:(?:left|right|top|bottom)Border [^/]*/>', fix, hdr_txt)
    print(f"테두리 얇게: {n[0]}건")
    return out


class WB:
    def __init__(self, xml, hdr):
        self.xml = xml
        self.char_h = {}
        for m in re.finditer(r'<hh:charPr id="(\d+)" height="(\d+)"', hdr):
            self.char_h[m.group(1)] = int(m.group(2))
        self.warn = []
        self.pending = []            # 높이 재계산이 필요한 컨테이너 (start,end)

    def em(self, cid):
        return max(self.char_h.get(cid, 1000), 100)

    # ---- 라벨 뒤 빈 문단 채움 -------------------------------------------
    def _container(self, pos):
        """pos를 감싸는 가장 안쪽 hp:subList의 (start,end). 없으면 문서 전체."""
        best = None
        for m in re.finditer(r'<hp:subList[ >]', self.xml):
            a = m.start()
            d, end = 0, None
            for mm in re.finditer(r'<hp:subList[ >]|</hp:subList>', self.xml[a:]):
                if mm.group(0).startswith('</'):
                    d -= 1
                    if d == 0:
                        end = a + mm.end()
                        break
                else:
                    d += 1
            if end and a < pos < end:
                if best is None or (end - a) < (best[1] - best[0]):
                    best = (a, end)
        return best or (0, len(self.xml))

    def fill_after(self, label, value, nth=0):
        text_join = value if isinstance(value, str) else ' '.join(value)
        found = -1
        ps = list(re.finditer(r'<hp:p [^>]*>.*?</hp:p>', self.xml, re.S))
        for i, m in enumerate(ps):
            if label in p_text(m.group(0)):
                found += 1
                if found == nth:
                    return self._fill_gap(ps, i, text_join, label)
        self.warn.append(f"라벨 없음: {label}")
        return False

    def _fill_gap(self, ps, li, text, label):
        # 라벨 문단과 같은 컨테이너(셀 subList 또는 본문) 안에서만 빈 문단을 모은다.
        ca, cb = self._container(ps[li].start())
        gaps = []
        j = li + 1
        skipped = 0
        while j < len(ps):
            if not (ca <= ps[j].start() and ps[j].end() <= cb):
                break                      # 컨테이너 밖으로 넘어가지 않는다
            t = p_text(ps[j].group(0)).strip()
            if not t:
                gaps.append(j)
            elif (t.startswith('(예') or t.startswith('(작성 예시')) and not gaps and skipped < 1:
                skipped += 1
            else:
                break
            j += 1
        if not gaps:
            self.warn.append(f"빈 문단 없음: {label}")
            return False
        # 폭·서체는 첫 빈 문단 기준
        g0 = ps[gaps[0]].group(0)
        hz_m = re.search(r'horzsize="(\d+)"', g0)
        hz = int(hz_m.group(1)) if hz_m else 40000
        cid_m = re.search(r'charPrIDRef="(\d+)"', g0)
        cid = cid_m.group(1) if cid_m else '0'
        em = self.em(cid)
        starts = MT.wrap(text, hz, em=em, word_unit=True)
        n = len(gaps)
        # 빈 문단별 담을 (부분 텍스트, 줄 시작 오프셋들) — 넘치면 마지막 칸에 잔여 전부
        pieces = []
        if len(starts) <= n:
            for k, a0 in enumerate(starts):
                b0 = starts[k + 1] if k + 1 < len(starts) else len(text)
                pieces.append((text[a0:b0].strip(), [0]))
        else:
            for k in range(n - 1):
                pieces.append((text[starts[k]:starts[k + 1]].strip(), [0]))
            tail = text[starts[n - 1]:].strip()
            tail_starts = MT.wrap(tail, hz, em=em, word_unit=True)
            pieces.append((tail, tail_starts))
            self.warn.append(f"넘침 {label}: {len(starts)}줄/{n}칸 — 마지막 칸 {len(tail_starts)}줄")
        edits = []
        extra = 0                       # 늘어난 렌더 줄 수
        for gi, (ptext, pstarts) in zip(gaps, pieces):
            p = ps[gi].group(0)
            extra += len(pstarts) - 1
            newp = self._set_p_text(p, ptext, pstarts, cid, hz)
            edits.append((ps[gi].start(), ps[gi].end(), newp))
        last_end = ps[gaps[-1]].end()
        for a, b, np_ in sorted(edits, reverse=True):
            self.xml = self.xml[:a] + np_ + self.xml[b:]
        if extra:
            seg0 = re.search(r'<hp:lineseg ([^/]*)/>', ps[gaps[0]].group(0))
            d = dict(re.findall(r'(\w+)="([^"]*)"', seg0.group(1)))
            shift = extra * (int(d.get('vertsize', 1000)) + int(d.get('spacing', 0)))
            self._shift_after(last_end, cb, shift)
            self.pending.append((ca, cb))
        return True

    def _shift_after(self, pos, limit, shift):
        """pos 이후 limit 이내 문단들의 vertpos를 shift만큼 내린다."""
        seg_re = re.compile(r'<hp:lineseg ([^/]*)/>')
        out, prev = [], 0
        for m in re.finditer(r'<hp:p [^>]*>.*?</hp:p>', self.xml, re.S):
            if m.start() < pos or m.end() > limit:
                continue
            p = m.group(0)
            def bump(sm):
                dd = dict(re.findall(r'(\w+)="([^"]*)"', sm.group(1)))
                dd['vertpos'] = str(int(dd.get('vertpos', 0)) + shift)
                return '<hp:lineseg ' + ' '.join(f'{k}="{v}"' for k, v in dd.items()) + '/>'
            np_ = seg_re.sub(bump, p)
            if np_ != p:
                out.append((m.start(), m.end(), np_))
        for a, b, np_ in sorted(out, reverse=True):
            self.xml = self.xml[:a] + np_ + self.xml[b:]

    def _set_p_text(self, p, text, starts, cid, hz):
        """빈 문단 p에 text를 넣고 lineseg를 starts 줄 수만큼 만든다."""
        body_open = p[:p.index('>') + 1]
        lsa = p.rfind('<hp:linesegarray>')
        seg0 = re.search(r'<hp:lineseg ([^/]*)/>', p[lsa:])
        d = dict(re.findall(r'(\w+)="([^"]*)"', seg0.group(1)))
        vp0 = int(d.get('vertpos', 0))
        sp = int(d.get('spacing', 0))
        vs = int(d.get('vertsize', 1000))
        segs = ''.join(
            f'<hp:lineseg textpos="{tp}" vertpos="{vp0 + i * (vs + sp)}" vertsize="{vs}" '
            f'textheight="{vs}" baseline="{int(round(vs * 0.85))}" spacing="{sp}" '
            f'horzpos="0" horzsize="{hz}" flags="393216"/>'
            for i, tp in enumerate(starts))
        return (body_open + f'<hp:run charPrIDRef="{cid}"><hp:t>{esc(text)}</hp:t></hp:run>'
                + '<hp:linesegarray>' + segs + '</hp:linesegarray></hp:p>')

    # ---- 라벨 문단에 텍스트 이어붙임 -------------------------------------
    def append_inline(self, label, value):
        m = re.search(r'<hp:p [^>]*>(?:(?!</hp:p>).)*?' + re.escape(label) + r'(?:(?!</hp:p>).)*?</hp:p>',
                      self.xml, re.S)
        if not m:
            self.warn.append(f"append 라벨 없음: {label}")
            return False
        p = m.group(0)
        i = p.index(label) + len(label)
        # 라벨 다음 </hp:t> 위치에 텍스트 삽입
        j = p.index('</hp:t>', i)
        newp = p[:j] + ' ' + esc(value if isinstance(value, str) else ' '.join(value)) + p[j:]
        self.xml = self.xml[:m.start()] + newp + self.xml[m.end():]
        return True

    # ---- 표 안 빈 셀 채움 ------------------------------------------------
    def fill_cell(self, ti, col, row, value):
        texts = [value] if isinstance(value, str) else list(value)
        a, b = all_tbl(self.xml)[ti]
        tbl = self.xml[a:b]
        off = tbl.index('>') + 1
        inner = tbl[off:tbl.rindex('</hp:tbl>')]
        for ca, cb in spans(inner, 'hp:tc'):
            c = inner[ca:cb]
            am = re.search(r'<hp:cellAddr colAddr="(%d)" rowAddr="(%d)"/>' % (col, row), c)
            if not am:
                continue
            sl = spans(c, 'hp:subList')[0]
            body = c[sl[0]:sl[1]]
            open_tag = body[:body.index('>') + 1].replace('lineWrap="SQUEEZE"', 'lineWrap="BREAK"')
            pin = body[body.index('>') + 1:body.rindex('</hp:subList>')]
            pspans = spans(pin, 'hp:p')
            ref = pin[pspans[0][0]:pspans[0][1]]
            pid = re.search(r'paraPrIDRef="(\d+)"', ref).group(1)
            cid_m = re.search(r'charPrIDRef="(\d+)"', ref)
            cid = cid_m.group(1) if cid_m else '0'
            em = self.em(cid)
            hz_m = re.search(r'horzsize="(\d+)"', ref)
            hz = int(hz_m.group(1)) if hz_m else 8000
            seg0 = re.search(r'<hp:lineseg ([^/]*)/>', ref)
            d0 = dict(re.findall(r'(\w+)="([^"]*)"', seg0.group(1))) if seg0 else {}
            sp = int(d0.get('spacing', 0))
            cursor, paras, nlines = 0, [], 0
            for t in texts:
                starts = MT.wrap(t, hz, em=em, word_unit=True) if t else [0]
                nlines += len(starts)
                segs = ''.join(
                    f'<hp:lineseg textpos="{tp}" vertpos="{cursor + i * (em + sp)}" '
                    f'vertsize="{em}" textheight="{em}" baseline="{int(round(em * 0.85))}" '
                    f'spacing="{sp}" horzpos="0" horzsize="{hz}" flags="393216"/>'
                    for i, tp in enumerate(starts))
                cursor += len(starts) * (em + sp)
                runs = (f'<hp:run charPrIDRef="{cid}"><hp:t>{esc(t)}</hp:t></hp:run>'
                        if t else f'<hp:run charPrIDRef="{cid}"/>')
                paras.append(f'<hp:p id="0" paraPrIDRef="{pid}" styleIDRef="0" pageBreak="0" '
                             f'columnBreak="0" merged="0">{runs}'
                             f'<hp:linesegarray>{segs}</hp:linesegarray></hp:p>')
            newc = c[:sl[0]] + open_tag + ''.join(paras) + '</hp:subList>' + c[sl[1]:]
            # 셀 높이 확장
            zm = list(re.finditer(r'<hp:cellSz width="(\d+)" height="(\d+)"/>', newc))[-1]
            mg = list(re.finditer(r'<hp:cellMargin left="(\d+)" right="(\d+)" top="(\d+)" bottom="(\d+)"/>', newc))
            pad = (int(mg[-1].group(3)) + int(mg[-1].group(4))) if mg else 566
            need = cursor + pad
            if need > int(zm.group(2)):
                newc = (newc[:zm.start()] +
                        f'<hp:cellSz width="{zm.group(1)}" height="{need}"/>' + newc[zm.end():])
            inner = inner[:ca] + newc + inner[cb:]
            new_tbl = tbl[:off] + inner + '</hp:tbl>'
            self.xml = self.xml[:a] + new_tbl + self.xml[b:]
            return True
        self.warn.append(f"셀 없음 T{ti}({col},{row})")
        return False

    # ---- fill_after로 늘어난 셀의 높이 확장 -----------------------------
    def grow_cells(self):
        """모든 셀을 훑어 내부 문단 높이 합보다 작은 cellSz를 확장한다."""
        n = 0
        changed = True
        while changed:
            changed = False
            for ca, cb in spans(self.xml, 'hp:tc'):
                c = self.xml[ca:cb]
                sl = spans(c, 'hp:subList')
                if not sl:
                    continue
                body = c[sl[0][0]:sl[0][1]]
                inner = body[body.index('>') + 1:body.rindex('</hp:subList>')]
                need = 0
                for pa, pb in spans(inner, 'hp:p'):
                    p = inner[pa:pb]
                    if spans(p, 'hp:tbl'):
                        continue
                    for sm in re.finditer(r'<hp:lineseg ([^/]*)/>', p):
                        d = dict(re.findall(r'(\w+)="([^"]*)"', sm.group(1)))
                        need += int(d.get('vertsize', 0)) + int(d.get('spacing', 0))
                zms = list(re.finditer(r'<hp:cellSz width="(\d+)" height="(\d+)"/>', c))
                mgs = list(re.finditer(r'<hp:cellMargin left="(\d+)" right="(\d+)" top="(\d+)" bottom="(\d+)"/>', c))
                if not zms:
                    continue
                pad = (int(mgs[-1].group(3)) + int(mgs[-1].group(4))) if mgs else 566
                want = need + pad
                zm = zms[-1]
                if want > int(zm.group(2)):
                    newc = (c[:zm.start()] +
                            f'<hp:cellSz width="{zm.group(1)}" height="{want}"/>' + c[zm.end():])
                    self.xml = self.xml[:ca] + newc + self.xml[cb:]
                    n += 1
                    changed = True
                    break
        if n:
            print(f"셀 높이 확장 {n}건")

    # ---- 표 행/표 높이 동기화 (전 표) -----------------------------------
    def sync_tables(self):
        for ti in range(len(all_tbl(self.xml)) - 1, -1, -1):
            a, b = all_tbl(self.xml)[ti]
            tbl = self.xml[a:b]
            off = tbl.index('>') + 1
            inner = tbl[off:tbl.rindex('</hp:tbl>')]
            rows = {}
            for ca, cb in spans(inner, 'hp:tc'):
                c = inner[ca:cb]
                ams = re.findall(r'<hp:cellAddr colAddr="(\d+)" rowAddr="(\d+)"/>', c)
                sps = re.findall(r'<hp:cellSpan colSpan="(\d+)" rowSpan="(\d+)"/>', c)
                zms = re.findall(r'<hp:cellSz width="(\d+)" height="(\d+)"/>', c)
                if not (ams and sps and zms):
                    continue
                if int(sps[-1][1]) == 1:
                    r = int(ams[-1][1])
                    rows[r] = max(rows.get(r, 0), int(zms[-1][1]))
            total = sum(rows.values())
            szm = re.search(r'(<hp:sz [^>]*height=")(\d+)(")', tbl)
            if szm and total > int(szm.group(2)):
                tbl = tbl[:szm.start()] + szm.group(1) + str(total) + szm.group(3) + tbl[szm.end():]
                self.xml = self.xml[:a] + tbl + self.xml[b:]


def main(out_path):
    slots = json.load(open(os.path.join(S, 'wb_slots.json'), encoding='utf-8'))
    z = zipfile.ZipFile(SRC)
    xml = z.read('Contents/section0.xml').decode('utf-8')
    hdr = z.read('Contents/header.xml').decode('utf-8')
    others = {n: z.read(n) for n in z.namelist() if n != 'Contents/section0.xml'}
    z.close()
    wb = WB(xml, hdr)

    # 표 안 빈칸
    for key, ti, col, row in [
        ('wb_d1_worry1', 4, 0, 1), ('wb_d1_worry2', 4, 1, 1), ('wb_d1_worry3', 4, 2, 1),
        ('wb_d3_human_sel', 9, 1, 1), ('wb_d3_comp_sel', 9, 1, 2),
        ('wb_d4_std_text', 12, 0, 1), ('wb_d4_std_k', 12, 1, 1),
        ('wb_d4_std_p', 12, 2, 1), ('wb_d4_std_v', 12, 3, 1),
        ('wb_d4_check1', 13, 1, 1), ('wb_d4_check2', 13, 1, 2), ('wb_d4_check3', 13, 1, 3),
        ('wb_d5_goal_k', 16, 1, 1), ('wb_d5_goal_p', 16, 1, 2), ('wb_d5_goal_v', 16, 1, 3),
    ]:
        if key in slots:
            wb.fill_cell(ti, col, row, slots[key])

    # 라벨 이어붙임
    for key, label in [('wb_d3_subject', '교과:'), ('wb_d3_grade', '학년:'),
                       ('wb_d3_unit', '단원(주제):')]:
        if key in slots:
            wb.append_inline(label, slots[key])

    # 라벨 뒤 빈 문단
    AFTERS = [
        ('wb_d1_keyword', '[선택한 키워드]', 0), ('wb_d1_connect', '[나의 고민과 연결하기]', 0),
        ('wb_d1_insight', '[새롭게 깨달은 점]', 0), ('wb_d1_change', '[가장 먼저 바꾸고 싶은 한 가지]', 0),
        ('wb_d2_diff', '[내가 발견한 두 설계안의 가장 큰 차이점]', 0),
        ('wb_d2_impact', '[학생의 배움에 미칠 영향]', 0),
        ('wb_d2_trip1', '1단계 (바라는 결과 확인):', 0), ('wb_d2_trip2', '2단계 (수용 가능한 증거 결정):', 0),
        ('wb_d2_trip3', '3단계 (학습 경험 및 활동 계획):', 0),
        ('wb_d2_question', '[나의 새로운 첫 번째 질문]', 0),
        ('wb_d3_human_why', '[선정 근거]', 0), ('wb_d3_comp_why', '[선정 근거]', 1),
        ('wb_d3_comp_action', '[단원에서의 구체적인 수행 모습 (조작적 정의)]', 0),
        ('wb_d3_reflect', '[나의 생각 정리]', 0),
        ('wb_d4_strategy', '[선택한 전략]', 0), ('wb_d4_bigidea', '[나의 핵심 아이디어 (초안)]', 0),
        ('wb_d4_reflect', '[나의 생각 정리]', 1),
        ('wb_d5_reflect', '[나의 생각 정리]', 2),
        ('wb_d6_intent_bg', '(배경 및 필요성)', 0), ('wb_d6_intent_dir', '(방향성 제시)', 0),
        ('wb_d6_intent_goal', '(핵심 목표 명시)', 0), ('wb_d6_intent_exp', '(핵심 경험 예고', 0),
        ('wb_d6_unitname', '[나의 단원명]', 0),
        ('wb_d6_reflect', '[나의 생각 정리]', 3),
    ]
    for key, label, nth in AFTERS:
        if key in slots:
            wb.fill_after(label, slots[key], nth)

    # 5차시 핵심 아이디어 재확인 표: '다시 확인하는' 라벨 다음 표의 (0,?) 빈 셀
    if 'wb_d5_bigidea' in slots:
        i = wb.xml.find('다시 확인하는 나의 핵심 아이디어')
        tb = next(((a, b) for a, b in all_tbl(wb.xml) if a > i), None)
        if tb:
            ti = all_tbl(wb.xml).index(tb)
            t = wb.xml[tb[0]:tb[1]]
            am = re.search(r'<hp:cellAddr colAddr="(\d+)" rowAddr="(\d+)"/>', t)
            wb.fill_cell(ti, int(am.group(1)), int(am.group(2)), slots['wb_d5_bigidea'])

    wb.grow_cells()
    wb.sync_tables()

    import xml.etree.ElementTree as ET
    ET.fromstring(wb.xml)
    others['Contents/header.xml'] = thin_borders(hdr).encode('utf-8')
    zo = zipfile.ZipFile(out_path, 'w')
    zo.writestr('mimetype', others.pop('mimetype'), zipfile.ZIP_STORED)
    zo.writestr('Contents/section0.xml', wb.xml, zipfile.ZIP_DEFLATED)
    for n, d in others.items():
        zo.writestr(n, d, zipfile.ZIP_DEFLATED)
    zo.close()
    print("경고:", wb.warn if wb.warn else "없음")
    print("wrote", out_path)


if __name__ == '__main__':
    main(sys.argv[1])
