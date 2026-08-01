#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""빌드 후처리 (플랜 B — 단순·안전):
1. 모든 표의 '글자처럼 취급' 해제 — <hp:tbl…><hp:sz…/><hp:pos…> 패턴만 치환(그림 pos는 불변)
2. 빌더가 채우지 않은 원본 라벨 셀만 함초롬바탕 11pt로 재작성
   (빌더 채움 칸은 이미 통일 charPr 사용. 라벨 셀은 전부 중첩 없는 단순 셀)
   ※ T0 문서 제목 표는 제외.
"""
import re, sys, zipfile, os

S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S)
import metrics as MT
MT.use_profile('conservative')
MT.HANGABLE = frozenset()

EM = 1100


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


def top_tbls(s):
    out, d, st = [], 0, None
    for m in re.finditer(r'<hp:tbl[ >]|</hp:tbl>', s):
        if m.group(0).startswith('</'):
            d -= 1
            if d == 0:
                out.append((st, m.end()))
        else:
            if d == 0:
                st = m.start()
            d += 1
    return out


def main(path):
    z = zipfile.ZipFile(path)
    xml = z.read('Contents/section0.xml').decode('utf-8')
    hdr = z.read('Contents/header.xml').decode('utf-8')
    others = {n: z.read(n) for n in z.namelist()
              if n not in ('Contents/section0.xml',)}
    z.close()

    # 통일 charPr id (빌더가 주입해 둠 — 마지막 2개)
    ids = sorted(int(m) for m in re.findall(r'<hh:charPr id="(\d+)"', hdr))
    CID_N, CID_B = str(ids[-2]), str(ids[-1])
    bold_ids = {m.group(1) for m in re.finditer(r'<hh:charPr id="(\d+)"[^>]*>.*?</hh:charPr>', hdr, re.S)
                if '<hh:bold' in m.group(0)}
    para_ls = {}
    for m in re.finditer(r'<hh:paraPr id="(\d+)".*?</hh:paraPr>', hdr, re.S):
        blk, pid = m.group(0), m.group(1)
        case = re.search(r'<hp:case\b.*?</hp:case>', blk, re.S)
        seg = case.group(0) if case else blk
        ls = re.search(r'<hh:lineSpacing type="PERCENT" value="(-?\d+)"', seg)
        pv = re.search(r'<hc:prev value="(-?\d+)"', seg)
        nx = re.search(r'<hc:next value="(-?\d+)"', seg)
        para_ls[pid] = (int(ls.group(1)) if ls else 100,
                        int(pv.group(1)) if pv else 0,
                        int(nx.group(1)) if nx else 0)

    # ── 1) 표 글자취급 해제 ────────────────────────────────────────────
    n_pos = [0]

    def flip(m):
        head, pos = m.group(1), m.group(2)
        if 'treatAsChar="1"' in pos:
            n_pos[0] += 1
            pos = pos.replace('treatAsChar="1"', 'treatAsChar="0"')
        return head + pos
    xml = re.sub(r'(<hp:tbl\b[^>]*><hp:sz[^/]*/>)(<hp:pos [^/]*/>)', flip, xml)

    # ── 2) 라벨 셀 재작성 (통일 charPr 미사용 셀만) ─────────────────────
    def restyle_label_cell(cell):
        if '<hp:tbl' in cell[cell.index('>'):]:
            # 중첩 표 보유 셀은 빌더 채움 칸이므로 여기 올 일 없음 — 안전상 스킵
            return cell, False
        cids = set(re.findall(r'charPrIDRef="(\d+)"', cell))
        if not cids or cids <= {CID_N, CID_B}:
            return cell, False
        sl = spans(cell, 'hp:subList')
        if not sl:
            return cell, False
        a0, b0 = sl[0]
        body = cell[a0:b0]
        open_tag = body[:body.index('>') + 1]
        inner = body[body.index('>') + 1:body.rindex('</hp:subList>')]
        hz = re.search(r'horzsize="(\d+)"', cell)
        horz = int(hz.group(1)) if hz else 4000
        cursor = 0
        new_paras = []
        for pa, pb in spans(inner, 'hp:p'):
            p = inner[pa:pb]
            pid_m = re.search(r'paraPrIDRef="(\d+)"', p)
            pid = pid_m.group(1) if pid_m else '0'
            # run들: 원 charPr의 bold 여부에 따라 CID_N/CID_B
            def sub_c(mm):
                return f'charPrIDRef="{CID_B if mm.group(1) in bold_ids else CID_N}"'
            p2 = re.sub(r'charPrIDRef="(\d+)"', sub_c, p)
            text = ''.join(re.findall(r'<hp:t>([^<]*)</hp:t>', p2))
            text = (text.replace('&amp;', '&').replace('&lt;', '<')
                        .replace('&gt;', '>').replace('&quot;', '"'))
            pct, prev_m, next_m = para_ls.get(pid, (100, 0, 0))
            spacing = int(round(EM * (pct - 100) / 100.0))
            pitch = EM + spacing
            starts = MT.wrap(text, horz, em=EM, word_unit=True) if text else [0]
            cursor += prev_m
            segs = ''.join(
                f'<hp:lineseg textpos="{tp}" vertpos="{cursor + i * pitch}" vertsize="{EM}" '
                f'textheight="{EM}" baseline="{int(round(EM * 0.85))}" spacing="{spacing}" '
                f'horzpos="0" horzsize="{horz}" flags="393216"/>'
                for i, tp in enumerate(starts))
            cursor += len(starts) * pitch + next_m
            lsa = p2.rfind('<hp:linesegarray>')
            if lsa >= 0:
                lse = p2.index('</hp:linesegarray>', lsa) + len('</hp:linesegarray>')
                p2 = p2[:lsa] + '<hp:linesegarray>' + segs + '</hp:linesegarray>' + p2[lse:]
            new_paras.append((pa, pb, p2))
        out = ''
        pv = 0
        for pa, pb, p2 in new_paras:
            out += inner[pv:pa] + p2
            pv = pb
        out += inner[pv:]
        return cell[:a0] + open_tag + out + '</hp:subList>' + cell[b0:], True

    n_cells = 0
    parts, prev = [], 0
    for ti, (a, b) in enumerate(top_tbls(xml)):
        t = xml[a:b]
        if ti == 0:                                  # 문서 제목 표 제외
            parts.append(xml[prev:b]); prev = b
            continue
        # 중첩 표 포함 전체 셀 순회: 깊이 인식으로 최하위 셀부터
        def walk_tbl(tb):
            nonlocal n_cells
            off = tb.index('>') + 1
            inner = tb[off:tb.rindex('</hp:tbl>')]
            new_inner, pv2 = '', 0
            for ca, cb in spans(inner, 'hp:tc'):
                c = inner[ca:cb]
                subs = spans(c, 'hp:tbl')
                if subs:
                    # 셀 안 중첩 표를 먼저 재귀 처리하고, 셀 자신은 라벨 아님(채움 칸)
                    for na, nb in reversed(subs):
                        c = c[:na] + walk_tbl(c[na:nb]) + c[nb:]
                else:
                    c2, changed = restyle_label_cell(c)
                    if changed:
                        n_cells += 1
                    c = c2
                new_inner += inner[pv2:ca] + c
                pv2 = cb
            new_inner += inner[pv2:]
            return tb[:off] + new_inner + '</hp:tbl>'
        parts.append(xml[prev:a])
        parts.append(walk_tbl(t))
        prev = b
    parts.append(xml[prev:])
    xml = ''.join(parts)

    # ── 3) 마무리: 표 내부(T0 제외) 잔여 charPrIDRef 일괄 치환 (빈 run·그림 run 포함) ──
    tt = top_tbls(xml)
    parts2, prev2 = [], 0
    for ti, (a, b) in enumerate(tt):
        if ti == 0:
            parts2.append(xml[prev2:b]); prev2 = b
            continue
        seg = xml[a:b]
        seg = re.sub(r'charPrIDRef="(\d+)"',
                     lambda mm: f'charPrIDRef="{CID_B if mm.group(1) in bold_ids else CID_N}"'
                     if mm.group(1) not in (CID_N, CID_B) else mm.group(0), seg)
        parts2.append(xml[prev2:a]); parts2.append(seg); prev2 = b
    parts2.append(xml[prev2:])
    xml = ''.join(parts2)

    import xml.etree.ElementTree as ET
    ET.fromstring(xml)
    tmp = path + '.tmp'
    zo = zipfile.ZipFile(tmp, 'w')
    zo.writestr('mimetype', others.pop('mimetype'), zipfile.ZIP_STORED)
    zo.writestr('Contents/section0.xml', xml, zipfile.ZIP_DEFLATED)
    for n, dta in others.items():
        zo.writestr(n, dta, zipfile.ZIP_DEFLATED)
    zo.close()
    os.replace(tmp, path)
    print(f"treatAsChar 해제 {n_pos[0]}건 / 라벨 셀 재작성 {n_cells}건 (함초롬바탕 11pt, T0 제외)")


if __name__ == '__main__':
    main(sys.argv[1])
