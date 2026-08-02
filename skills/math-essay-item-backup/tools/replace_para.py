#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HWPX 고정 문안 교체기 — 줄 수를 지키며 문단 텍스트를 갈아 끼운다.

왜 줄 수인가
------------
HWPX는 문단마다 줄바꿈 결과를 `<hp:linesegarray>` 캐시로 들고 있다.  줄 하나가
`<hp:lineseg vertpos=… vertsize=… horzsize=…/>` 한 개다.  텍스트만 바꾸고 캐시를
그대로 두면 글자가 한 줄에 겹치고, 캐시를 늘리면 그 문단 뒤의 모든 vertpos·셀
높이·표 높이·페이지 경계가 한꺼번에 어긋난다.  그래서 이 도구의 기본은
**새 문안의 줄 수가 원본 줄 수와 같을 때만 교체**하는 `preserve-lines`다.
줄 수가 같으면 lineseg의 세로 기하(vertpos·vertsize·spacing·flags)를 손대지
않고 `textpos`만 다시 계산하면 되므로 뒤 문단을 밀 일이 없다.

사용
----
    python3 replace_para.py 입력.hwpx 출력.hwpx --spec 교체.json
    python3 replace_para.py 입력.hwpx 출력.hwpx --find "원문 앞머리" --text "새 문안"
    python3 replace_para.py 입력.hwpx --list

종료 코드
---------
    0  전 항목 교체·검증 성공
    2  인자·스펙·선택자 오류(대상 없음/중복, run 구성 불일치, 지원하지 않는 문단)
    3  같은 줄 수를 만들 수 없음 — preserve-lines가 거부했다(출력 파일 없음)
    4  --allow-reflow가 지원하지 않는 구조(표 안 문단 등)
    5  ZIP/XML/출력 실패

표준 라이브러리만 쓴다.  자원(metrics.py)은 이 파일이 있는 폴더에서 찾고,
산출물은 사용자가 준 출력 경로에만 만든다.  스킬 폴더에는 아무것도 쓰지 않는다.
"""
import argparse
import json
import os
import re
import sys
import tempfile
import unicodedata
import zipfile
import xml.etree.ElementTree as ET

S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S)
import metrics as MT                                     # noqa: E402

# metrics.py가 이번 라운드의 run별 확장(G8)을 받았는지 본다.
EXT_METRICS = hasattr(MT, 'StyledRun') and hasattr(MT, 'measure_advances')

EX_OK, EX_ARG, EX_LINES, EX_REFLOW, EX_IO = 0, 2, 3, 4, 5

SCRIPT_KEYS = ('hangul', 'latin', 'hanja', 'japanese', 'other', 'symbol', 'user')


class Refuse(Exception):
    """사람이 읽을 이유와 종료 코드를 함께 들고 다니는 거부."""

    def __init__(self, code, msg):
        super().__init__(msg)
        self.code = code
        self.msg = msg


def die(code, msg):
    raise Refuse(code, msg)


# --------------------------------------------------------------------------
# 1. XML 훑기
# --------------------------------------------------------------------------
def _tag_iter(xml, tag):
    """`<tag …>` / `<tag …/>` / `</tag>` 를 순서대로 돌려준다."""
    pat = re.compile(r'<%s(?:\s[^>]*)?/>|<%s(?:\s[^>]*)?>|</%s>' % (tag, tag, tag))
    for m in pat.finditer(xml):
        s = m.group(0)
        if s.startswith('</'):
            kind = 'close'
        elif s.endswith('/>'):
            kind = 'self'
        else:
            kind = 'open'
        yield kind, m.start(), m.end()


def _spans(text, tag, base=0, top_only=False):
    """text 안 tag 요소의 (시작, 끝, 깊이) 목록.  좌표에 base를 더해 돌려준다."""
    out, stack = [], []
    for kind, a, b in _tag_iter(text, tag):
        if kind == 'self':
            if not top_only or not stack:
                out.append((base + a, base + b, len(stack)))
        elif kind == 'open':
            stack.append(a)
        else:
            if not stack:
                continue
            st = stack.pop()
            if not top_only or not stack:
                out.append((base + st, base + b, len(stack)))
    out.sort()
    return out


def unescape(t):
    return (t.replace('&lt;', '<').replace('&gt;', '>')
             .replace('&quot;', '"').replace('&apos;', "'")
             .replace('&amp;', '&'))


def escape(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _attrs(s):
    return dict(re.findall(r'([\w:]+)="([^"]*)"', s))


RUN_OPEN = re.compile(r'<hp:run(?:\s[^>]*)?>|<hp:run(?:\s[^>]*)?/>')
T_ONLY = re.compile(r'^<hp:t>([^<]*)</hp:t>$')


def scan_paragraphs(xml):
    """`<hp:p>` 전부를 문서 순서로 훑는다(표 안 문단 포함).

    각 문단에서 **자기 것**만 본다 — 중첩 표 안의 run과 linesegarray는 뺀다.
    """
    paras = []
    for a, b, depth in _spans(xml, 'hp:p'):
        body = xml[a:b]
        head_end = body.index('>') + 1
        pattr = _attrs(body[:head_end])
        # 이 문단이 직접 품은 표(중첩 표는 그 안에 딸려 온다)
        tbl = [(x, y) for x, y, _ in _spans(body, 'hp:tbl', a, top_only=True)]
        masked = lambda pos: any(x <= pos < y for x, y in tbl)   # noqa: E731

        runs, unsupported = [], []
        for ra, rb, _ in _spans(body, 'hp:run', a):
            if masked(ra):
                continue
            rs = xml[ra:rb]
            rhead = rs[:rs.index('>') + 1]
            inner = '' if rhead.endswith('/>') else rs[len(rhead):-len('</hp:run>')]
            cid = _attrs(rhead).get('charPrIDRef', '')
            m = T_ONLY.match(inner)
            if m:
                off = ra + len(rhead) + len('<hp:t>')
                runs.append({'cid': cid, 'raw': m.group(1),
                             'span': (off, off + len(m.group(1)))})
            elif inner.strip() == '':
                pass                                     # 빈 run: 폭 0, 무시한다
            else:
                unsupported.append(inner[:40])

        lsa = [(x, y) for x, y, _ in _spans(body, 'hp:linesegarray', a)
               if not masked(x)]
        segs = []
        if lsa:
            for sm in re.finditer(r'<hp:lineseg\s([^/>]*)/>', xml[lsa[0][0]:lsa[0][1]]):
                segs.append({'span': (lsa[0][0] + sm.start(), lsa[0][0] + sm.end()),
                             'attr': _attrs(sm.group(1)), 'raw': sm.group(0)})
        paras.append({
            'start': a, 'end': b, 'depth': depth,
            'para_pr': pattr.get('paraPrIDRef', ''),
            'page_break': pattr.get('pageBreak', '0') == '1',
            'in_table': depth > 0,
            'has_table': bool(tbl),
            'runs': runs, 'unsupported': unsupported,
            'lsa_span': lsa[0] if lsa else None, 'segs': segs,
            'text': unescape(''.join(r['raw'] for r in runs)),
        })
    return paras


# --------------------------------------------------------------------------
# 2. header.xml에서 글자·문단 모양 읽기
# --------------------------------------------------------------------------
def _script_map(s, name, default):
    m = re.search(r'<hh:%s\s([^/>]*)/>' % name, s)
    if not m:
        return {k: default for k in SCRIPT_KEYS}
    d = _attrs(m.group(1))
    return {k: float(d.get(k, default)) for k in SCRIPT_KEYS}


def load_char_pr(hdr):
    out = {}
    for m in re.finditer(r'<hh:charPr id="(\d+)".*?</hh:charPr>', hdr, re.S):
        s, cid = m.group(0), m.group(1)
        h = re.search(r'height="(-?\d+)"', s)
        out[cid] = {
            'height': max(int(h.group(1)) if h else 1000, 100),
            'ratio': _script_map(s, 'ratio', 100),
            'spacing': _script_map(s, 'spacing', 0),
            'relSz': _script_map(s, 'relSz', 100),
        }
    return out


def load_para_pr(hdr):
    out = {}
    for m in re.finditer(r'<hh:paraPr id="(\d+)".*?</hh:paraPr>', hdr, re.S):
        b = re.search(r'breakNonLatinWord="(\w+)"', m.group(0))
        out[m.group(1)] = b.group(1) if b else 'BREAK_WORD'
    return out


# --------------------------------------------------------------------------
# 3. 글자 폭과 줄바꿈
# --------------------------------------------------------------------------
def apply_metrics_cfg(cfg):
    """스펙의 metrics 블록을 metrics.py 전역에 반영하고 실효값을 돌려준다."""
    MT.use_profile(cfg.get('profile', 'conservative'))
    for key, attr in (('f_full', 'F_FULL'), ('f_ambig', 'F_AMBIG'),
                      ('f_latin', 'F_LATIN'), ('f_narrow', 'F_NARROW'),
                      ('f_space', 'F_SPACE')):
        if key in cfg:
            setattr(MT, attr, float(cfg[key]))
    if 'ambiguous_full_width' in cfg:
        MT.AMBIGUOUS_FULL_WIDTH = bool(cfg['ambiguous_full_width'])
    hang = cfg.get('hangable', 'no_line_start')
    if hang == 'none':
        MT.HANGABLE = frozenset()
    elif hang == 'no_line_start':
        MT.HANGABLE = MT.NO_LINE_START
    else:
        die(EX_ARG, f"metrics.hangable 값이 이상하다: {hang!r} "
                    "(no_line_start 또는 none)")
    return {'profile': cfg.get('profile', 'conservative'),
            'f_full': MT.F_FULL, 'f_ambig': MT.F_AMBIG, 'f_latin': MT.F_LATIN,
            'f_narrow': MT.F_NARROW, 'f_space': MT.F_SPACE,
            'ambiguous_full_width': MT.AMBIGUOUS_FULL_WIDTH, 'hangable': hang}


def _slot(ch):
    o = ord(ch)
    if 0xAC00 <= o <= 0xD7A3 or 0x1100 <= o <= 0x11FF or 0x3130 <= o <= 0x318F:
        return 'hangul'
    if 0x3400 <= o <= 0x4DBF or 0x4E00 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF:
        return 'hanja'
    if 0x3040 <= o <= 0x30FF:
        return 'japanese'
    return 'latin' if (ch == ' ' or ch.isascii()) else 'other'


def char_advances(run_texts, cps, per_script):
    """[(charPr, 텍스트)] -> (전체 텍스트, 문자별 advance 폭)

    per_script=False면 예전 인터페이스대로 hangul 값 하나만 쓴다.
    """
    if EXT_METRICS:
        styled = [MT.StyledRun(text=t, em=cp['height'], ratio=cp['ratio'],
                               spacing=cp['spacing'], rel_sz=cp['relSz'])
                  for cp, t in zip(cps, run_texts)]
        text = ''.join(run_texts)
        return text, list(MT.measure_advances(text, runs=styled))
    text, w = '', []
    for cp, t in zip(cps, run_texts):
        for ch in t:
            k = _slot(ch) if per_script else 'hangul'
            em = cp['height'] * cp['relSz'][k] / 100.0
            w.append(MT.width(ch, em=em, ratio=cp['ratio'][k],
                              spacing=cp['spacing'][k]))
        text += t
    return text, w


def greedy_wrap(text, adv, widths, word_unit, latin_word_unit=True, kinsoku=True):
    """metrics.wrap과 같은 그리디 규칙.  폭 배열만 밖에서 받는다.

    widths는 줄별 사용 가능 폭(HWPUNIT) 목록이고, 목록보다 줄이 많아지면
    마지막 값을 이어 쓴다.
    """
    lim = lambda i: float(widths[min(i, len(widths) - 1)])   # noqa: E731
    starts, n = [0], len(text)
    i = start = line = 0
    cur = 0.0
    while i < n:
        ch = text[i]
        if ch == MT.FORCED_BREAK:
            i += 1
            if i < n:
                starts.append(i); line += 1; start = i; cur = 0.0
            continue
        limit = lim(line)
        over = cur + adv[i] > limit + 1e-9
        if over and (ch in MT.SPACES or (ch in MT.HANGABLE and cur <= limit + 1e-9)):
            over = False
        if over:
            brk = None
            for j in range(i, start, -1):
                if MT.break_allowed(text, j, word_unit, latin_word_unit, kinsoku):
                    brk = j; break
            if brk is None:
                brk = i if i > start else start + 1
            starts.append(brk); line += 1
            start = i = brk
            cur = 0.0
            continue
        cur += adv[i]
        i += 1
    return starts


def wrap_lines(text, adv, widths, word_unit):
    """확장 metrics가 있으면 그쪽을 쓰고, 없으면 도구 안의 같은 그리디를 쓴다."""
    if EXT_METRICS:
        return list(MT.wrap(text, list(widths), char_advances=list(adv),
                            word_unit=word_unit))
    return greedy_wrap(text, adv, widths, word_unit)


def exact_line_starts(text, adv, widths, target, word_unit):
    """정확히 target줄이 되는 합법적 줄바꿈 경로를 동적 계획법으로 찾는다.

    그리디는 줄 수 최소해다.  그리디가 target보다 많으면 어떤 경로도 target줄을
    만들 수 없다(일찍 끊으면 줄이 늘어날 뿐이다).  그래서 이 함수는 그리디가
    target보다 **적을 때만** 쓸모가 있고, 그때 나오는 경로는 한글이 다시 조판할
    때의 경로와 다르다 — 그래서 기본이 아니라 --exact-fit 전용이다.
    """
    n = len(text)
    pre = [0.0]
    for v in adv:
        pre.append(pre[-1] + float(v))
    lim = lambda i: float(widths[min(i, len(widths) - 1)])   # noqa: E731

    def used(start, end, li):
        if end <= start:
            return None
        f = text.find(MT.FORCED_BREAK, start, end)
        if f >= 0 and f != end - 1:
            return None
        if end < n and text[end] == MT.FORCED_BREAK:
            return None
        if end < n and not MT.break_allowed(text, end, word_unit, True, True):
            return None
        ve = end
        while ve > start and text[ve - 1] in MT.SPACES:
            ve -= 1
        u = pre[ve] - pre[start]
        limit = lim(li)
        if u <= limit + 1e-9:
            return u
        if ve > start and text[ve - 1] in MT.HANGABLE and \
                pre[ve - 1] - pre[start] <= limit + 1e-9:
            return u
        return None

    memo = {}

    def solve(li, start):
        key = (li, start)
        if key in memo:
            return memo[key]
        if li == target - 1:
            u = used(start, n, li)
            r = None if u is None else (max(lim(li) - min(u, lim(li)), 0.0) ** 2, (n,))
            memo[key] = r
            return r
        best = None
        for end in range(start + 1, n):
            u = used(start, end, li)
            if u is None:
                continue
            tail = solve(li + 1, end)
            if tail is None:
                continue
            cost = max(lim(li) - min(u, lim(li)), 0.0) ** 2 + tail[0]
            if best is None or cost < best[0]:
                best = (cost, (end,) + tail[1])
        memo[key] = best
        return best

    sol = solve(0, 0) if n else ((0.0, (0,)) if target == 1 else None)
    if sol is None:
        return None
    return [0, *sol[1][:-1]]


def utf16_pos(text, i):
    """파이썬 문자 인덱스 -> UTF-16 code unit 인덱스(= HWPX textpos)."""
    return len(text[:i].encode('utf-16-le')) // 2


# --------------------------------------------------------------------------
# 4. 선택자
# --------------------------------------------------------------------------
def pick(paras, item, n):
    idx = item.get('para_index')
    if idx is not None:
        if not isinstance(idx, int) or not (0 <= idx < len(paras)):
            die(EX_ARG, f"[{n}] para_index {idx}가 범위 밖이다 "
                        f"(0~{len(paras) - 1}).  --list로 확인해라.")
        return idx
    find = item.get('find')
    if not find:
        die(EX_ARG, f"[{n}] find 또는 para_index 가운데 하나는 있어야 한다.")
    how = item.get('match', 'startswith')
    if how not in ('startswith', 'exact', 'contains'):
        die(EX_ARG, f"[{n}] match는 startswith/exact/contains 가운데 하나다: {how!r}")
    test = {'startswith': lambda t: t.startswith(find),
            'exact': lambda t: t == find,
            'contains': lambda t: find in t}[how]
    hits = [i for i, p in enumerate(paras) if p['runs'] and test(p['text'])]
    want = item.get('expected_occurrences', 1)
    if len(hits) != want:
        die(EX_ARG, f"[{n}] find={find[:40]!r} ({how})에 걸린 문단이 "
                    f"{len(hits)}개다.  {want}개를 기대했다.  "
                    f"걸린 인덱스: {hits[:8]}")
    occ = item.get('occurrence', 0)
    if not (0 <= occ < len(hits)):
        die(EX_ARG, f"[{n}] occurrence {occ}가 범위 밖이다(0~{len(hits) - 1}).")
    return hits[occ]


def new_run_texts(item, para, n):
    """스펙의 text/runs -> [새 텍스트], 그리고 charPrIDRef 선행조건 검사."""
    have = [r['cid'] for r in para['runs']]
    if 'text' in item and 'runs' in item:
        die(EX_ARG, f"[{n}] text와 runs를 함께 줄 수 없다.")
    if 'text' in item:
        if len(have) != 1:
            die(EX_ARG, f"[{n}] 이 문단은 텍스트 run이 {len(have)}개다"
                        f"(charPrIDRef {have}).  text 대신 runs로 "
                        f"{len(have)}개를 순서대로 줘라 — 굵은 글씨 같은 "
                        "run 구성을 보존해야 한다.")
        out = [item['text']]
    elif 'runs' in item:
        rs = item['runs']
        if not isinstance(rs, list) or len(rs) != len(have):
            die(EX_ARG, f"[{n}] runs가 {len(rs) if isinstance(rs, list) else '?'}개인데 "
                        f"문단의 텍스트 run은 {len(have)}개다(charPrIDRef {have}).")
        out = []
        for k, r in enumerate(rs):
            if isinstance(r, str):
                out.append(r)
            elif isinstance(r, dict):
                cid = str(r.get('charPrIDRef', have[k]))
                if cid != have[k]:
                    die(EX_ARG, f"[{n}] run {k}의 charPrIDRef가 다르다: "
                                f"스펙 {cid}, 문단 {have[k]}")
                out.append(r.get('text', ''))
            else:
                die(EX_ARG, f"[{n}] runs[{k}]는 문자열이나 객체여야 한다.")
    else:
        die(EX_ARG, f"[{n}] text 또는 runs가 있어야 한다.")
    for t in out:
        bad = [c for c in t if unicodedata.category(c) == 'Cc']
        if bad:
            die(EX_ARG, f"[{n}] 새 문안에 제어문자 {bad[0]!r}가 있다.  "
                        "줄바꿈은 lineseg 캐시와 어긋난다 — 한 줄 문자열로 줘라.")
    return out


# --------------------------------------------------------------------------
# 5. 한 항목 계획
# --------------------------------------------------------------------------
def plan_one(item, paras, cps, pps, n, allow_reflow, exact_fit):
    i = pick(paras, item, n)
    p = paras[i]
    if not p['runs']:
        die(EX_ARG, f"[{n}] 문단 {i}에 바꿀 텍스트 run이 없다.")
    if p['unsupported']:
        die(EX_ARG, f"[{n}] 문단 {i}에 단순 텍스트가 아닌 run이 있다"
                    f"(예: {p['unsupported'][0]!r}).  이 도구는 "
                    "<hp:run><hp:t>글자</hp:t></hp:run> 형태만 바꾼다.")
    if p['has_table']:
        die(EX_ARG, f"[{n}] 문단 {i}는 표를 품고 있다.  표를 품은 문단의 "
                    "줄 수 계산은 이 도구의 범위 밖이다.")
    if not p['segs']:
        die(EX_ARG, f"[{n}] 문단 {i}에 linesegarray가 없다.  줄 수를 지킬 수 없다.")

    exp_sha = item.get('expected_text_sha256')
    if exp_sha:
        import hashlib
        got = hashlib.sha256(p['text'].encode('utf-8')).hexdigest()
        if got != exp_sha:
            die(EX_ARG, f"[{n}] 문단 {i} 원문 해시 불일치: 기대 {exp_sha[:12]}…, "
                        f"실제 {got[:12]}…  서식이 바뀌었다.")

    old_lines = len(p['segs'])
    exp = item.get('expected_lines')
    if exp is not None and exp != old_lines:
        die(EX_ARG, f"[{n}] 문단 {i}의 원본 줄 수가 {old_lines}줄인데 스펙은 "
                    f"{exp}줄을 기대했다.  서식이 바뀌었거나 다른 문단을 골랐다.")

    texts = new_run_texts(item, p, n)
    missing = [r['cid'] for r in p['runs'] if r['cid'] not in cps]
    if missing:
        die(EX_ARG, f"[{n}] header.xml에 charPr {missing[0]}이 없다.")
    cps_of = [cps[r['cid']] for r in p['runs']]
    text, adv = char_advances(texts, cps_of, item.get('per_script_metrics', False))
    widths = [float(s['attr'].get('horzsize', 0)) for s in p['segs']]
    if not all(widths):
        die(EX_ARG, f"[{n}] 문단 {i}의 lineseg에 horzsize가 없다.")
    # breakNonLatinWord -> word_unit 대응은 뒤집혀 있다(BREAK_WORD == 어절 단위).
    # metrics.py가 그 대응을 갖고 있으면 거기에 맡긴다 — 두 군데서 뒤집지 않는다.
    bnl = pps.get(p['para_pr'], 'BREAK_WORD')
    wu = (MT.resolve_word_unit(True, bnl) if hasattr(MT, 'resolve_word_unit')
          else bnl == 'BREAK_WORD')

    starts = wrap_lines(text, adv, widths, wu)
    natural = len(starts)
    mode = 'preserve'
    if len(starts) != old_lines:
        if exact_fit and len(starts) < old_lines:
            forced = exact_line_starts(text, adv, widths, old_lines, wu)
            if forced is None:
                die(EX_LINES, f"[{n}] 문단 {i}: 새 문안을 {old_lines}줄로 나눌 "
                              "합법적인 방법이 없다.")
            starts, mode = forced, 'exact-fit'
        elif allow_reflow:
            mode = 'reflow'
        else:
            die(EX_LINES,
                f"[{n}] 문단 {i}: 원본은 {old_lines}줄인데 새 문안은 "
                f"{len(starts)}줄이 된다.  줄 수가 같아야 교체한다.\n"
                f"       원본: {p['text'][:60]!r}\n"
                f"       새 문안: {text[:60]!r}\n"
                f"       {'글자를 줄여라' if len(starts) > old_lines else '글자를 늘려라'}"
                f" — 마지막 줄에 들어간 글자 수를 보고 다듬으면 된다.")
    return {'n': n, 'para': i, 'p': p, 'texts': texts, 'text': text,
            'starts': starts, 'old_lines': old_lines, 'new_lines': len(starts),
            'natural_lines': natural, 'mode': mode, 'old_text': p['text'],
            'widths': widths}


# --------------------------------------------------------------------------
# 6. 편집 만들기
# --------------------------------------------------------------------------
def edits_preserve(job):
    """텍스트 run 내용과 lineseg textpos만 바꾼다.  세로 기하는 그대로 둔다."""
    out = []
    for r, t in zip(job['p']['runs'], job['texts']):
        out.append((r['span'][0], r['span'][1], escape(t)))
    for seg, st in zip(job['p']['segs'], job['starts']):
        a, b = seg['span']
        new = re.sub(r'textpos="\d+"', 'textpos="%d"' % utf16_pos(job['text'], st),
                     seg['raw'], count=1)
        out.append((a, b, new))
    return out


def edits_reflow(job, paras, warn):
    """줄 수가 달라진 경우: linesegarray를 다시 만들고 뒤 문단을 민다."""
    p, segs = job['p'], job['p']['segs']
    if p['in_table']:
        die(EX_REFLOW, f"[{job['n']}] 문단 {job['para']}은 표 안에 있다.  "
                       "셀·행·표 높이를 함께 고쳐야 하므로 --allow-reflow가 "
                       "지원하지 않는다.  문안을 줄 수에 맞게 고쳐 써라.")
    a0 = segs[0]['attr']
    if len(segs) >= 2:
        pitch = int(segs[1]['attr']['vertpos']) - int(a0['vertpos'])
    else:
        pitch = int(a0.get('vertsize', 1000)) + int(a0.get('spacing', 0))
    if pitch <= 0:
        die(EX_REFLOW, f"[{job['n']}] 줄 간격을 읽을 수 없다(pitch={pitch}).")
    if len(segs) == 1 and job['new_lines'] > 1 and int(a0.get('horzpos', 0)) != 0:
        die(EX_REFLOW, f"[{job['n']}] 문단 {job['para']}은 원본이 1줄이고 첫 줄에 "
                       f"들여쓰기(horzpos={a0['horzpos']})가 있다.  둘째 줄부터의 "
                       "가로 기하를 알 수 없으므로 늘리지 않는다.")
    base_v = int(a0['vertpos'])
    out = []
    for r, t in zip(p['runs'], job['texts']):
        out.append((r['span'][0], r['span'][1], escape(t)))
    new_segs = []
    for k, st in enumerate(job['starts']):
        src = segs[min(k, len(segs) - 1)]     # 없는 줄은 마지막 줄의 기하를 따른다
        d = dict(src['attr'])
        d['textpos'] = str(utf16_pos(job['text'], st))
        d['vertpos'] = str(base_v + k * pitch)
        new_segs.append('<hp:lineseg ' +
                        ' '.join('%s="%s"' % (k2, d[k2]) for k2 in src['attr']) + '/>')
    # 속성 순서는 원본 첫 lineseg를 따른다(위 zip). 새로 만든 줄도 같은 순서다.
    out.append((p['lsa_span'][0], p['lsa_span'][1],
                '<hp:linesegarray>' + ''.join(new_segs) + '</hp:linesegarray>'))

    delta = (job['new_lines'] - job['old_lines']) * pitch
    moved, stopped = 0, None
    last_v = int(segs[-1]['attr']['vertpos'])
    for q in paras:
        if q['start'] <= p['start'] or q['depth'] != 0 or not q['segs']:
            continue
        v0 = int(q['segs'][0]['attr'].get('vertpos', 0))
        if q['page_break'] or v0 < last_v:
            stopped = q['start']
            break
        last_v = int(q['segs'][-1]['attr'].get('vertpos', 0))
        for seg in q['segs']:
            nv = int(seg['attr'].get('vertpos', 0)) + delta
            out.append((seg['span'][0], seg['span'][1],
                        re.sub(r'vertpos="-?\d+"', 'vertpos="%d"' % nv,
                               seg['raw'], count=1)))
        moved += 1
    warn.append(f"[{job['n']}] reflow: {job['old_lines']}줄 -> {job['new_lines']}줄, "
                f"뒤 문단 {moved}개를 {delta:+d} HWPUNIT 밀었다"
                + (" (다음 페이지부터는 밀지 않았다 — 페이지 경계는 다시 계산되지 "
                   "않는다)" if stopped is not None else ""))
    return out


# --------------------------------------------------------------------------
# 7. ZIP 쓰기
# --------------------------------------------------------------------------
def read_hwpx(path, section):
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            if section not in names:
                die(EX_ARG, f"{path}에 {section}이 없다.  들어 있는 것: {names[:6]}")
            if 'Contents/header.xml' not in names:
                die(EX_ARG, f"{path}에 Contents/header.xml이 없다.")
            items = [(i, z.read(i.filename)) for i in z.infolist()]
    except zipfile.BadZipFile as e:
        die(EX_IO, f"{path}를 ZIP으로 열 수 없다: {e}")
    except OSError as e:
        die(EX_IO, f"{path}를 읽을 수 없다: {e}")
    return items


def write_hwpx(items, section, xml, out_path):
    """mimetype 첫 엔트리·무압축, 나머지는 원본 순서·원본 메타데이터 유지.

    임시 파일에 다 쓰고 os.replace로 자리를 바꾼다 — 반쯤 쓰인 파일이 남지 않는다.
    """
    data = xml.encode('utf-8')
    d = os.path.dirname(os.path.abspath(out_path)) or '.'
    try:
        os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=d, suffix='.hwpx.part')
        os.close(fd)
        order = sorted(items, key=lambda it: it[0].filename != 'mimetype')
        with zipfile.ZipFile(tmp, 'w') as zo:
            for info, raw in order:
                ni = zipfile.ZipInfo(info.filename, date_time=info.date_time)
                ni.compress_type = (zipfile.ZIP_STORED
                                    if info.filename == 'mimetype'
                                    else zipfile.ZIP_DEFLATED)
                ni.external_attr = info.external_attr
                ni.create_system = info.create_system
                zo.writestr(ni, data if info.filename == section else raw)
        os.replace(tmp, out_path)
    except OSError as e:
        die(EX_IO, f"{out_path}를 쓸 수 없다: {e}")


# --------------------------------------------------------------------------
# 8. CLI
# --------------------------------------------------------------------------
EPILOG = """\
스펙(JSON) 보기:
  {
    "section": "Contents/section0.xml",
    "metrics": {"profile": "conservative", "f_latin": 0.55},
    "replacements": [
      {"id": "goal-01", "find": "• 함수의 개념을 안다.", "match": "exact",
       "expected_lines": 1, "text": "• 닮음비를 안다."},
      {"id": "goal-02", "para_index": 391,
       "runs": [{"charPrIDRef": "10", "text": "• 닮음비와 넓이의 비의 차이를 "},
                {"charPrIDRef": "13", "text": "설명할 수 있다."}]}
    ]
  }

--allow-reflow가 기본이 아닌 이유:
  줄 수가 달라지면 그 문단 뒤의 모든 세로 좌표가 어긋난다.  이 도구는 같은
  페이지의 뒤 문단 vertpos만 밀어 준다.  셀 높이(hp:cellSz), 행 높이, 표 높이,
  페이지 넘김 위치, 떠 있는 개체의 anchor는 **다시 계산하지 않는다**.  그래서
  표 안 문단은 아예 거부하고(종료 코드 4), 본문 문단이라도 페이지 경계를 넘는
  순간 미는 것을 멈춘다.  결과 파일은 한글로 열어 눈으로 확인해야 한다.
  정상 경로는 언제나 "문안을 원본 줄 수에 맞게 고쳐 쓰기"다.
"""


def main(argv):
    ap = argparse.ArgumentParser(
        prog='replace_para.py',
        description='HWPX 문단 텍스트를 줄 수를 지키며 교체한다(기본 preserve-lines).',
        epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('input', help='입력 .hwpx')
    ap.add_argument('output', nargs='?', help='출력 .hwpx (--list/--dry-run이면 생략 가능)')
    ap.add_argument('--spec', help='교체 지시 JSON')
    ap.add_argument('--find', help='단건: 찾을 문자열')
    ap.add_argument('--para-index', type=int, help='단건: 문단 인덱스(--list로 확인)')
    ap.add_argument('--match', default='startswith',
                    choices=('startswith', 'exact', 'contains'), help='단건: 일치 방식')
    ap.add_argument('--text', help='단건: 새 문안')
    ap.add_argument('--expected-lines', type=int, help='단건: 원본 줄 수 선행조건')
    ap.add_argument('--section', default='Contents/section0.xml')
    ap.add_argument('--dry-run', action='store_true',
                    help='무엇이 몇 줄로 바뀌는지만 보이고 파일을 쓰지 않는다')
    ap.add_argument('--allow-reflow', action='store_true',
                    help='줄 수가 달라도 교체하고 뒤 문단을 민다(기본 아님, 위험)')
    ap.add_argument('--exact-fit', action='store_true',
                    help='자연 줄 수가 원본보다 적을 때 일찍 끊어 줄 수를 맞춘다'
                         ' (한글이 다시 조판하면 이 경로를 재현하지 않는다)')
    ap.add_argument('--list', action='store_true', help='문단 목록만 찍는다')
    ap.add_argument('--report', help='결과 JSON을 쓸 경로')
    a = ap.parse_args(argv)

    items = read_hwpx(a.input, a.section)
    blob = {i.filename: raw for i, raw in items}
    xml = blob[a.section].decode('utf-8')
    hdr = blob['Contents/header.xml'].decode('utf-8')
    paras = scan_paragraphs(xml)

    if a.list:
        print(f"# {a.input}\n# {a.section}: 문단 {len(paras)}개 "
              "(표 안 문단 포함, 문서 순서)")
        for i, p in enumerate(paras):
            if not p['runs']:
                continue
            print(f"{i:5d}  줄{len(p['segs']):2d}  run{len(p['runs']):2d}  "
                  f"{'표안' if p['in_table'] else '본문'}  {p['text'][:56]}")
        return EX_OK

    if a.spec:
        try:
            with open(a.spec, encoding='utf-8') as f:
                spec = json.load(f)
        except OSError as e:
            die(EX_ARG, f"스펙을 읽을 수 없다: {e}")
        except json.JSONDecodeError as e:
            die(EX_ARG, f"스펙이 JSON이 아니다: {e}")
        reps = spec.get('replacements')
        if not isinstance(reps, list) or not reps:
            die(EX_ARG, "스펙에 replacements 배열이 없다.")
        cfg = spec.get('metrics', {})
        if spec.get('section') and spec['section'] != a.section:
            a.section = spec['section']
            if a.section not in blob:
                die(EX_ARG, f"{a.input}에 {a.section}이 없다.")
            xml = blob[a.section].decode('utf-8')
            paras = scan_paragraphs(xml)
    elif a.find or a.para_index is not None:
        one = {'id': 'cli'}
        if a.find:
            one['find'] = a.find
            one['match'] = a.match
        else:
            one['para_index'] = a.para_index
        if a.text is None:
            die(EX_ARG, "--find/--para-index에는 --text가 함께 있어야 한다.")
        one['text'] = a.text
        if a.expected_lines is not None:
            one['expected_lines'] = a.expected_lines
        reps, cfg = [one], {}
    else:
        die(EX_ARG, "--spec 또는 --find/--para-index 가운데 하나가 있어야 한다.")

    if not a.dry_run and not a.output:
        die(EX_ARG, "출력 경로가 없다.  파일을 쓰지 않으려면 --dry-run을 줘라.")
    if a.output and os.path.exists(a.output) and os.path.samefile(a.input, a.output):
        die(EX_ARG, "입력과 출력이 같은 파일이다.  원본을 덮어쓰지 않는다 — "
                    "다른 이름으로 내보내라.")

    eff = apply_metrics_cfg(cfg)
    if not EXT_METRICS:
        print("[알림] metrics.py에 run별 폭 API(StyledRun/measure_advances)가 없다."
              "  기존 width() 인터페이스로 run별 자간을 도구 안에서 반영한다.")
    print(f"[metrics] {eff['profile']}  latin={eff['f_latin']} narrow={eff['f_narrow']} "
          f"space={eff['f_space']} ambig={eff['f_ambig']} hangable={eff['hangable']}")

    cps, pps = load_char_pr(hdr), load_para_pr(hdr)

    # --- 1) 전 항목을 먼저 계획한다.  하나라도 거부되면 아무것도 쓰지 않는다.
    jobs, seen = [], {}
    for k, item in enumerate(reps):
        n = item.get('id', f'#{k}')
        job = plan_one(item, paras, cps, pps, n, a.allow_reflow, a.exact_fit)
        if job['para'] in seen:
            die(EX_ARG, f"[{n}] 문단 {job['para']}을 [{seen[job['para']]}]가 "
                        "이미 잡았다.  같은 문단을 두 번 바꿀 수 없다.")
        seen[job['para']] = n
        jobs.append(job)

    if sum(j['mode'] == 'reflow' for j in jobs) > 1:
        die(EX_REFLOW, "한 번에 두 문단 이상을 reflow할 수 없다.  뒤 문단을 미는 "
                       "양이 서로 겹친다.  한 건씩 나눠 돌리고 그때마다 눈으로 "
                       "확인해라.")

    for j in jobs:
        tag = {'preserve': '유지', 'exact-fit': '강제맞춤', 'reflow': '재배치'}[j['mode']]
        print(f"  [{j['n']}] 문단 {j['para']}: {j['old_lines']}줄 -> "
              f"{j['new_lines']}줄 {tag}  {j['text'][:44]!r}")
        if j['mode'] == 'exact-fit':
            print(f"  [경고] [{j['n']}] 자연 줄바꿈은 {j['natural_lines']}줄인데 "
                  f"{j['old_lines']}줄로 억지로 나눴다.  한글이 다시 조판하면 이 "
                  "줄바꿈을 재현하지 않는다 — 문안을 고쳐 쓰는 편이 낫다.")

    if a.dry_run:
        print(f"--dry-run: {len(jobs)}건 계획만 확인했다.  파일을 쓰지 않았다.")
        if a.report:
            _report(a.report, a, jobs, eff, [])
        return EX_OK

    # --- 2) 편집 적용
    warn, edits = [], []
    for j in jobs:
        edits += (edits_reflow(j, paras, warn) if j['mode'] == 'reflow'
                  else edits_preserve(j))
    edits.sort(key=lambda e: e[0])
    for (a1, b1, _), (a2, _, _) in zip(edits, edits[1:]):
        if b1 > a2:
            die(EX_IO, f"편집 구간이 겹친다({a1}-{b1} vs {a2}).  중단한다.")
    new_xml = xml
    for s, e, rep in reversed(edits):
        new_xml = new_xml[:s] + rep + new_xml[e:]

    try:
        ET.fromstring(new_xml)
    except ET.ParseError as e:
        die(EX_IO, f"교체한 XML이 깨졌다: {e}")

    write_hwpx(items, a.section, new_xml, a.output)
    for w in warn:
        print("  [경고] " + w)
    print(f"교체 {len(jobs)}건 -> {a.output}")
    if a.report:
        _report(a.report, a, jobs, eff, warn)
    return EX_OK


def _report(path, args, jobs, eff, warn):
    doc = {'input': args.input, 'output': args.output, 'section': args.section,
           'dry_run': bool(args.dry_run), 'metrics': eff,
           'extended_metrics': EXT_METRICS, 'warnings': warn,
           'replacements': [{'id': j['n'], 'para_index': j['para'],
                             'mode': j['mode'], 'old_lines': j['old_lines'],
                             'new_lines': j['new_lines'],
                             'old_text': j['old_text'], 'new_text': j['text'],
                             'textpos': [utf16_pos(j['text'], s) for s in j['starts']]}
                            for j in jobs]}
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
    except OSError as e:
        die(EX_IO, f"보고서를 쓸 수 없다: {e}")
    print(f"보고서 -> {path}")


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except Refuse as r:
        sys.stdout.flush()
        print(r.msg, file=sys.stderr)
        sys.exit(r.code)
