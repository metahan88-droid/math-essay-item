#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HWPX line-metrics model for 맑은 고딕 (Malgun Gothic), reverse-engineered from
Hangul-generated HWPX files.

Deliverables
------------
    width(ch, em=1200, ...)     -> advance width of one character, in HWPUNIT
    measure_advances(text, ...) -> per-character advance array for one paragraph
    wrap(text, horzsize, ...)   -> list of line-start character indices
                                   (== the textpos values of <hp:lineseg>)
    linesegarray(text, ...)     -> the <hp:linesegarray> XML for one paragraph

Units
-----
    1 HWPUNIT = 1/7200 inch.   12 pt = 12/72 inch = 1200 HWPUNIT = 1 em.

Two ways to describe a paragraph
--------------------------------
1. **One style for the whole paragraph** (the original API, unchanged)::

       wrap(text, horzsize, em=1100, word_unit=True, ratio=100, spacing=0)

2. **Per-run styles**, because a real HWPX paragraph is a sequence of
   `<hp:run>`s and every run carries its own `charPr` (height, 장평, 자간,
   relSz).  Mixing 자간 inside one paragraph is normal in authored documents,
   and a single paragraph-wide value cannot reproduce the line cache::

       runs = [MT.StyledRun(text='표 1. ', em=1000, spacing=-5),
               MT.StyledRun(text='닮음비 구하기', em=1000, spacing=-1)]
       wrap(''.join(r.text for r in runs), horzsize,
            runs=runs, break_non_latin_word='KEEP_WORD')

   A run may also be given as a plain dict with the same keys, which is what
   an HWPX header parser naturally produces.

   If you already measured the text with a real font engine, hand the widths
   over directly and no style is consulted at all::

       wrap(text, horzsize, char_advances=[...])   # len == len(text)

The new arguments (`runs`, `char_advances`, `break_non_latin_word`,
`break_latin_word`, `rel_sz`) are keyword-only, so every existing positional
call keeps its old meaning and its old result.

Line-break policy comes from paraPr/breakSetting.  The enum names are
counter-intuitive, so the mapping lives here and nowhere else::

    breakNonLatinWord = BREAK_WORD -> 어절 단위 -> word_unit=True
    breakNonLatinWord = KEEP_WORD  -> 글자 단위 -> word_unit=False
    breakLatinWord    = KEEP_WORD  -> 라틴 낱말 안 쪼갬 -> latin_word_unit=True
    breakLatinWord    = BREAK_WORD -> 라틴 낱말 쪼갬   -> latin_word_unit=False

Evidence for that inversion: on 127 two-or-more-line paragraphs pulled out of
two real documents, KEEP_WORD -> 글자 단위 reproduced the line count 117 times
against 115 for the inverted reading, and in tpl2 it never broke later than
Hangul (0 vs 3 late lines).  The breakLatinWord row is read off the same enum
by symmetry — both sample documents only ever use KEEP_WORD, so no measurement
separates it from its opposite yet.  Keep that in mind before trusting it.

Run this file directly to execute the ground-truth regression tests, or
`python3 metrics.py wrap-runs --input paragraph.json` to wrap one paragraph
described in JSON.
"""
import math
import unicodedata as ud
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

# --------------------------------------------------------------------------
# 1. character advance widths
# --------------------------------------------------------------------------
# Fractions of one em.  Derived from Hangul-authored HWPX line caches; see the
# module test-suite at the bottom for the evidence each value rests on.
F_FULL    = 1.00     # East-Asian W / F  : Hangul, Hanja, 〔〕〈〉【】㉮①…, U+3000
F_AMBIG   = 1.00     # East-Asian A      : conservative choice, see NOTE below
F_LATIN   = 0.70     # ASCII letters     : upper bound for proportional Malgun
F_NARROW  = 0.60     # digits / ASCII punctuation
F_SPACE   = 0.50     # U+0020
F_ZERO    = 0.00     # combining marks, U+200B, the forced-break character
#
# NOTE on the ambiguous class (·, —, →, ÷, …, ※, ×, ○, ①-⑤, ⓐ, ³, Ⅰ, ⑴…):
#   the corpus does not settle these to a single value; a best-fit search
#   slightly prefers 0.50 em while several individual characters (※, ○, —)
#   fit better at 1.00 em.  1.00 em is chosen because it can only ever make a
#   line SHORTER than Hangul would, which is the safe direction: a short cached
#   line renders fine, an over-long cached line overflows the cell.
#   Set AMBIGUOUS_FULL_WIDTH = False to switch to the best-fit 0.50 em.
AMBIGUOUS_FULL_WIDTH = True

FORCED_BREAK = '\n'          # how <hp:lineBreak/> is represented in the text
SPACES = ' 　\t'         # characters allowed to hang past the right margin

# characters that may not begin a line (closing kinsoku)
NO_LINE_START = set(
    '!%),.:;?]}¢°’”‰′″、。〉》」』】〕〞ㆍ！％），．：；？］｝'
    '·‧･…〙〗»›'
)
# characters that may not end a line (opening kinsoku)
NO_LINE_END = set('$([\\{£¥‘“〈《「『【〔＄（［｛￥￦«‹〘〖#')

# closing punctuation that HWP lets hang past the right margin (문장부호 매달기),
# exactly like a trailing space.  Without this rule the model breaks one
# character too early whenever a line ends in , . ) ] 」 etc.
HANGABLE = NO_LINE_START


# --------------------------------------------------------------------------
# 1b. per-run styles
# --------------------------------------------------------------------------
# charPr/ratio, charPr/spacing and charPr/relSz carry one value per script in
# HWPX.  A plain number means "same value for every script".
SCRIPT_SLOTS = ('hangul', 'latin', 'hanja', 'japanese', 'other',
                'symbol', 'user')

_RUN_KEYS = {'text', 'em', 'ratio', 'spacing', 'rel_sz'}
# an HWPX parser usually keeps the attribute spelling; accept it too
_RUN_ALIASES = {'relSz': 'rel_sz', 'height': 'em'}


@dataclass(frozen=True)
class StyledRun:
    """One `<hp:run>`, reduced to what line breaking needs.

    text    : the run's characters (a `<hp:lineBreak/>` is '\\n')
    em      : charPr/@height, raw (1200 == 12 pt).  relSz is applied on top,
              unlike the paragraph-wide `wrap(em=...)` argument, which callers
              have always had to pre-multiply themselves.
    ratio   : charPr/ratio   (장평, percent)      number or per-script dict
    spacing : charPr/spacing (자간, percent of em) number or per-script dict
    rel_sz  : charPr/relSz   (상대 크기, percent)  number or per-script dict
    """
    text: str
    em: float = 1200
    ratio: Any = 100
    spacing: Any = 0
    rel_sz: Any = 100


def as_run(obj):
    """StyledRun 그대로 두고, dict은 StyledRun으로 바꾼다."""
    if isinstance(obj, StyledRun):
        return obj
    if not isinstance(obj, Mapping):
        raise TypeError(
            f'run은 StyledRun이나 dict여야 한다: {type(obj).__name__} 이(가) 왔다')
    kw = {}
    for key, value in obj.items():
        name = _RUN_ALIASES.get(key, key)
        if name not in _RUN_KEYS:
            raise ValueError(
                f'run에 모르는 항목이 있다: {key!r}. '
                f'쓸 수 있는 항목은 {sorted(_RUN_KEYS)} 이다. '
                '조용히 무시하면 줄 수가 틀리므로 여기서 멈춘다.')
        if name in kw:
            raise ValueError(f'run에 {name!r} 이(가) 두 번 들어 있다: {sorted(obj)}')
        kw[name] = value
    if 'text' not in kw:
        raise ValueError("run에 'text'가 없다.")
    if not isinstance(kw['text'], str):
        raise TypeError("run의 'text'는 문자열이어야 한다.")
    return StyledRun(**kw)


_SLOT_CACHE = {}


def _script_slot(ch):
    """문자를 charPr의 스크립트 칸(hangul/latin/…)에 대응시킨다."""
    slot = _SLOT_CACHE.get(ch)
    if slot is not None:
        return slot
    o = ord(ch)
    if (0xAC00 <= o <= 0xD7A3) or (0x1100 <= o <= 0x11FF) \
       or (0x3130 <= o <= 0x318F):
        slot = 'hangul'
    elif (0x3400 <= o <= 0x4DBF) or (0x4E00 <= o <= 0x9FFF) \
            or (0xF900 <= o <= 0xFAFF):
        slot = 'hanja'
    elif 0x3040 <= o <= 0x30FF:
        slot = 'japanese'
    elif 0xE000 <= o <= 0xF8FF:
        slot = 'user'
    elif ch == ' ' or ch.isdigit():
        slot = 'latin'
    elif ch.isalpha() and (ch.isascii() or 'LATIN' in ud.name(ch, '')):
        slot = 'latin'
    elif ud.category(ch)[0] in 'PS':
        slot = 'symbol'
    else:
        slot = 'other'
    _SLOT_CACHE[ch] = slot
    return slot


def _metric_value(value, slot, default):
    if not isinstance(value, Mapping):
        return float(value)
    for key in (slot, 'other', 'hangul'):
        if key in value:
            return float(value[key])
    return float(default)


def width(ch, em=1200, ratio=100, spacing=0, *, rel_sz=100):
    """Advance width of `ch` in HWPUNIT.

    em       : charPr/@height (1200 == 12 pt); when `rel_sz` is left at 100 the
               caller is expected to have folded relSz in already, as before
    ratio    : charPr/ratio   (장평, percent)      number or per-script dict
    spacing  : charPr/spacing (자간, percent of em, may be negative)
    rel_sz   : charPr/relSz   (percent)            number or per-script dict
    """
    f = _factor(ch)
    if f == 0.0:
        return 0.0
    if not (isinstance(ratio, Mapping) or isinstance(spacing, Mapping)
            or isinstance(rel_sz, Mapping)):
        if rel_sz != 100:
            em = em * rel_sz / 100.0
        return em * f * ratio / 100.0 + em * spacing / 100.0
    slot = _script_slot(ch)
    em = em * _metric_value(rel_sz, slot, 100) / 100.0
    return (em * f * _metric_value(ratio, slot, 100) / 100.0
            + em * _metric_value(spacing, slot, 0) / 100.0)


def _factor(ch):
    if ch == FORCED_BREAK or ud.combining(ch) or ch == '​':
        return F_ZERO
    eaw = ud.east_asian_width(ch)
    if eaw in ('W', 'F'):
        return F_FULL
    if eaw == 'A':
        return F_AMBIG if AMBIGUOUS_FULL_WIDTH else 0.50
    if ch == ' ':
        return F_SPACE
    if eaw in ('Na', 'H'):
        return F_LATIN if ch.isalpha() else F_NARROW
    return F_AMBIG if AMBIGUOUS_FULL_WIDTH else 0.50   # 'N', e.g. U+2212 −


def measure_advances(text, em=1200, ratio=100, spacing=0, *,
                     rel_sz=100, runs=None):
    """문단 하나의 문자별 advance 배열 (HWPUNIT).

    runs가 있으면 문자마다 그 문자가 속한 run의 charPr로 폭을 잰다.
    runs의 텍스트를 이으면 text와 정확히 같아야 한다 — 다르면 예외다.
    """
    if runs is None:
        return [width(c, em, ratio, spacing, rel_sz=rel_sz) for c in text]

    runs = [as_run(r) for r in runs]
    joined = ''.join(r.text for r in runs)
    if joined != text:
        i = next((k for k, (a, b) in enumerate(zip(joined, text)) if a != b),
                 min(len(joined), len(text)))
        raise ValueError(
            'runs의 텍스트를 이은 결과가 wrap()에 넘긴 text와 다르다. '
            f'text {len(text)}자, runs {len(joined)}자, {i}번째 문자부터 어긋난다: '
            f'text={text[i:i + 12]!r} runs={joined[i:i + 12]!r}. '
            'run을 나누거나 합칠 때 글자를 빠뜨렸는지 확인해라.')

    out = []
    for r in runs:
        out.extend(width(c, r.em, r.ratio, r.spacing, rel_sz=r.rel_sz)
                   for c in r.text)
    return out


# --------------------------------------------------------------------------
# 2. line breaking
# --------------------------------------------------------------------------
def _cls(ch):
    if ch in SPACES:      return 'SP'
    if ch == FORCED_BREAK: return 'BR'
    o = ord(ch)
    if (0xAC00 <= o <= 0xD7A3) or (0x1100 <= o <= 0x11FF) or (0x3130 <= o <= 0x318F) \
       or (0x4E00 <= o <= 0x9FFF) or (0x3400 <= o <= 0x4DBF) or (0xF900 <= o <= 0xFAFF) \
       or (0x3040 <= o <= 0x30FF):
        return 'CJK'
    if ch.isalnum():
        return 'LAT'
    return 'PUN'


def break_allowed(text, i, word_unit=True, latin_word_unit=True, kinsoku=True):
    """May a line break be placed immediately BEFORE text[i]?

    word_unit       True  -> 어절 단위: Hangul only breaks at spaces
                    False -> 글자 단위: Hangul breaks between any two syllables
    latin_word_unit True  -> Latin words are never split
    """
    if i <= 0 or i >= len(text):
        return False
    a, b = text[i-1], text[i]
    if a == FORCED_BREAK:
        return True
    if b in SPACES:
        return False                      # a line never starts with a space
    if a in SPACES:
        return True                       # after a space is always legal
    if word_unit:
        # 어절 단위: the only legal break is after a space (handled above).
        # '2층)', 'y=ax+b의' etc. are single 어절 and are never split.
        return False
    if kinsoku and (b in NO_LINE_START or a in NO_LINE_END):
        return False
    ca, cb = _cls(a), _cls(b)
    if ca == 'LAT' and cb == 'LAT':
        return not latin_word_unit
    if ca == 'PUN' and cb == 'PUN':
        return not latin_word_unit
    if 'LAT' in (ca, cb) and 'PUN' in (ca, cb):
        return not latin_word_unit
    return True                            # CJK involved -> 글자 단위 break


# paraPr/breakSetting 의 enum -> 이 모듈의 boolean.
# 이름만 보면 거꾸로 읽기 쉬우므로 매핑은 여기 한 곳에만 둔다.
_NON_LATIN_WORD_UNIT = {'BREAK_WORD': True,    # 어절 단위
                        'KEEP_WORD': False}    # 글자 단위
_LATIN_WORD_UNIT = {'KEEP_WORD': True,         # 낱말을 통째로 유지
                    'BREAK_WORD': False}       # 낱말 중간에서도 끊음


def _resolve(table, fallback, value, attr):
    if value is None:
        return bool(fallback)
    name = str(getattr(value, 'value', value)).strip().upper()
    try:
        return table[name]
    except KeyError:
        raise ValueError(
            f'{attr} 값을 알 수 없다: {value!r}. '
            f'BREAK_WORD 아니면 KEEP_WORD여야 한다.') from None


def resolve_word_unit(word_unit=True, break_non_latin_word=None):
    """paraPr/breakSetting/@breakNonLatinWord -> word_unit."""
    return _resolve(_NON_LATIN_WORD_UNIT, word_unit,
                    break_non_latin_word, 'breakNonLatinWord')


def resolve_latin_word_unit(latin_word_unit=True, break_latin_word=None):
    """paraPr/breakSetting/@breakLatinWord -> latin_word_unit."""
    return _resolve(_LATIN_WORD_UNIT, latin_word_unit,
                    break_latin_word, 'breakLatinWord')


def _limit_getter(horzsize):
    if callable(horzsize):
        return lambda i: float(horzsize(i))
    if isinstance(horzsize, (list, tuple)):
        if not horzsize:
            raise ValueError('horzsize 목록이 비었다.')
        return lambda i: float(horzsize[min(i, len(horzsize) - 1)])
    return lambda i: float(horzsize)


def _advances_for(text, em, ratio, spacing, rel_sz, runs, char_advances):
    if runs is not None and char_advances is not None:
        raise ValueError('runs와 char_advances는 같이 줄 수 없다. 하나만 골라라.')
    if char_advances is None:
        return measure_advances(text, em, ratio, spacing,
                                rel_sz=rel_sz, runs=runs)
    if isinstance(char_advances, (str, bytes)):
        raise TypeError('char_advances는 숫자 목록이어야 한다. 문자열이 왔다.')
    try:
        w = [float(v) for v in char_advances]
    except TypeError as e:
        raise TypeError(f'char_advances를 숫자 목록으로 읽지 못했다: {e}') from None
    if len(w) != len(text):
        raise ValueError(
            f'char_advances 길이가 text 길이와 다르다: {len(w)} != {len(text)}. '
            '문자 하나에 폭 하나씩 넣어라.')
    for i, v in enumerate(w):
        if not math.isfinite(v):
            raise ValueError(f'char_advances[{i}]가 유한한 수가 아니다: {v!r}')
    return w


def wrap(text, horzsize, em=1200, word_unit=True, ratio=100, spacing=0,
         latin_word_unit=True, kinsoku=True, safety=0, *,
         runs=None, char_advances=None, break_non_latin_word=None,
         break_latin_word=None, rel_sz=100):
    """Greedy line breaking.  Returns the list of line-start indices,
    i.e. exactly the `textpos` attributes of the <hp:lineseg> elements.

    horzsize : available width in HWPUNIT (may be an int, or a list/callable
               giving a per-line width).
    safety   : HWPUNIT shaved off every line's limit; use a positive value to
               bias towards breaking early.

    Keyword-only, all optional — omit them and the result is the old one:
    runs                 : StyledRun/dict 목록. 문자 폭을 run별 charPr로 잰다.
    char_advances        : 문자별 폭을 직접 준다 (len == len(text)).
    break_non_latin_word : 'BREAK_WORD'/'KEEP_WORD'. 주면 word_unit을 덮는다.
    break_latin_word     : 'BREAK_WORD'/'KEEP_WORD'. 주면 latin_word_unit을 덮는다.
    rel_sz               : charPr/relSz. runs를 쓰면 run마다 따로 준다.
    """
    limit_of = _limit_getter(horzsize)
    word_unit = resolve_word_unit(word_unit, break_non_latin_word)
    latin_word_unit = resolve_latin_word_unit(latin_word_unit,
                                              break_latin_word)
    w = _advances_for(text, em, ratio, spacing, rel_sz, runs, char_advances)

    starts = [0]
    n = len(text)
    i = start = line = 0
    cur = 0.0
    while i < n:
        ch = text[i]
        if ch == FORCED_BREAK:            # <hp:lineBreak/> : hard break
            i += 1
            if i < n:
                starts.append(i); line += 1; start = i; cur = 0.0
            continue
        limit = limit_of(line) - safety
        if limit <= 0:
            raise ValueError(
                f'{line}번 줄의 쓸 수 있는 폭이 0 이하다: {limit}. '
                f'horzsize({horzsize!r})와 safety({safety})를 확인해라 — '
                '들여쓰기를 빼다가 폭이 음수가 된 경우가 많다.')
        over = cur + w[i] > limit + 1e-9
        if over and (ch in SPACES or (ch in HANGABLE and cur <= limit + 1e-9)):
            over = False                  # trailing space / one punctuation hangs
        if over:
            brk = None
            for j in range(i, start, -1):
                if break_allowed(text, j, word_unit, latin_word_unit, kinsoku):
                    brk = j; break
            if brk is None:               # nothing fits: emergency mid-unit break
                brk = i if i > start else start + 1
            starts.append(brk); line += 1
            start = i = brk
            cur = 0.0
            continue
        cur += w[i]
        i += 1
    return starts


def line_width(text, em=1200, ratio=100, spacing=0, *,
               rel_sz=100, runs=None, char_advances=None):
    """Rendered width of one line, ignoring hanging trailing spaces."""
    w = _advances_for(text, em, ratio, spacing, rel_sz, runs, char_advances)
    return sum(w[:len(text.rstrip(SPACES))])


def use_profile(name):
    """'conservative' (default, never breaks later than Hangul) or 'bestfit'
    (reproduces Hangul's own break positions most often)."""
    global AMBIGUOUS_FULL_WIDTH, F_AMBIG, F_LATIN, F_NARROW
    if name == 'bestfit':
        AMBIGUOUS_FULL_WIDTH, F_AMBIG, F_LATIN, F_NARROW = False, 0.50, 0.50, 0.50
    elif name == 'conservative':
        AMBIGUOUS_FULL_WIDTH, F_AMBIG, F_LATIN, F_NARROW = True, 1.00, 0.70, 0.60
    else:
        raise ValueError(name)


# --------------------------------------------------------------------------
# 2b. emitting <hp:linesegarray>
# --------------------------------------------------------------------------
def _run_em(r):
    """run 하나가 요구하는 줄 높이 (height x relSz)."""
    rel = r.rel_sz
    if isinstance(rel, Mapping):
        rel = max(float(v) for v in rel.values()) if rel else 100.0
    return float(r.em) * float(rel) / 100.0


def _line_heights(text, starts, runs, char_height):
    """줄마다 vertsize. runs가 없으면 전부 char_height."""
    if runs is None:
        return [float(char_height)] * len(starts)
    runs = [as_run(r) for r in runs]
    per_char = []
    for r in runs:
        per_char.extend([_run_em(r)] * len(r.text))
    bounds = list(starts) + [len(text)]
    out = []
    for i in range(len(starts)):
        chunk = per_char[bounds[i]:bounds[i + 1]]
        out.append(max(chunk) if chunk else float(char_height))
    return out


def linesegarray(text, horzsize, char_height=1200, line_spacing_pct=120,
                 word_unit=True, ratio=100, spacing=0, indent=0, *,
                 runs=None, char_advances=None, break_non_latin_word=None,
                 break_latin_word=None, rel_sz=100):
    """Build the <hp:linesegarray> XML for one paragraph.

    char_height      : charPr/@height of the run (1200 == 12 pt)
    line_spacing_pct : paraPr/lineSpacing/@value when type="PERCENT"
    Verified against the template: vertsize == textheight == char_height,
    baseline == round(vertsize*0.85), spacing == char_height*(pct-100)/100,
    vertpos == line_index * (vertsize + spacing), horzpos == 0, flags == 393216.

    With `runs`, each line's vertsize is the tallest run on that line
    (height x relSz), which is how Hangul caches mixed-size paragraphs:
    tpl2 서식의 크기 섞인 문단 5개 중 4개가 정확히 max(run em)이었다.
    남은 1개는 가장 큰 run이 HY그래픽이라 한글이 1100 대신 1177(x1.07)로
    잡았다 — 자기 줄 높이가 em보다 큰 글꼴을 쓰면 캐시를 직접 확인해라.
    같은 서식에서 크기가 하나뿐인 순수 텍스트 문단 195개는 전부 vertsize == em
    이었다.
    """
    starts = wrap(text, horzsize, em=char_height, word_unit=word_unit,
                  ratio=ratio, spacing=spacing, runs=runs,
                  char_advances=char_advances, rel_sz=rel_sz,
                  break_non_latin_word=break_non_latin_word,
                  break_latin_word=break_latin_word)
    heights = _line_heights(text, starts, runs, char_height)
    hz = int(horzsize if not isinstance(horzsize, (list, tuple)) else horzsize[0])
    segs = []
    vertpos = 0
    for i, tp in enumerate(starts):
        vs = int(round(heights[i]))
        sp = int(round(vs * (line_spacing_pct - 100) / 100.0))
        segs.append(
            f'<hp:lineseg textpos="{tp}" vertpos="{vertpos}" vertsize="{vs}" '
            f'textheight="{vs}" baseline="{int(round(vs * 0.85))}" spacing="{sp}" '
            f'horzpos="{indent if i == 0 else 0}" horzsize="{hz}" flags="393216"/>')
        vertpos += vs + sp
    return '<hp:linesegarray>' + ''.join(segs) + '</hp:linesegarray>', len(starts)


# --------------------------------------------------------------------------
# 3. ground-truth regression tests
# --------------------------------------------------------------------------
# (label, text, horzsize, char_height, word_unit, expected textpos list)
# word_unit is derived from paraPr/breakSetting/@breakNonLatinWord:
#     BREAK_WORD -> 어절 단위 -> word_unit=True
#     KEEP_WORD  -> 글자 단위 -> word_unit=False        (yes, inverted; see report)
TEMPLATE_CASES = [
    # straight out of [사전과제 서식] ... .hwpx (맑은 고딕 12pt, charPr 56/58)
    ('tpl paraPr68 CENTER 120% BREAK_WORD hz=9388',
     '서·논술형 평가 문항 재구성', 9388, 1200, True,  [0, 9]),
    ('tpl paraPr74 CENTER 160% BREAK_WORD hz=4184',
     '채점 기준 초안',              4184, 1200, True,  [0, 3, 6]),
]

EXTRA_CASES = [
    ('세안 paraPr39 KEEP_WORD(글자) hz=26412 em=1300',
     '▸ 학생의 다양한 표현(올라간 칸·올라간 높이·비율)을 미리 예상·메모',
     26412, 1300, False, [0, 24]),
    ('어울림 BREAK_WORD(어절) hz=9460 em=1100  [hanging comma]',
     '캠프파이어(고구마, 마시멜로우)', 9460, 1100, True, [0, 11]),
    ('mel-001 forced <hp:lineBreak/> hz=10940',
     '·중장년 맞춤형\n패키지 확대(1월)', 10940, 1200, True, [0, 9]),
    ('mel-001 forced <hp:lineBreak/> hz=10868',
     '·온라인 훈련 \n확대(5월)', 10868, 1200, True, [0, 9]),
    ('mel-001 BREAK_WORD(어절) hz=10940 em=1200',
     '·맞돌봄 확산 제도시행(9월)', 10940, 1200, True, [0, 8]),
    ('mel-001 BREAK_WORD(어절) hz=10868 em=1200',
     '·엔지니어 훈련 과정 개시(6월)', 10868, 1200, True, [0, 9]),
    ('해설지 KEEP_WORD(글자) hz=24708 em=1000',
     '평행사변형에서 두 대각선은 서로 다른 것을 이등분하므로,', 24708, 1000, False, [0, 27]),
    ('1222222 KEEP_WORD(글자) hz=6516 em=1000 (굴림체)',
     '청소년 SNS 사용', 6516, 1000, False, [0, 9]),
]

# --------------------------------------------------------------------------
# 3b. mixed-run ground truth
# --------------------------------------------------------------------------
# 한 문단 안에서 run마다 charPr가 다른 실제 문단들.  옛 API(문단 하나에 자간
# 하나)로는 만들 수 없는 입력이라, 여기서만 새 인자를 검증한다.
# 네 건 모두 "옛 방식은 줄 수를 틀리고 run별 charPr로는 맞는" 실제 문단이다.
# (label, runs, horzsize, breakNonLatinWord, expected textpos list)
MIXED_RUN_CASES = [
    # <스킬 루트>/tools/tpl2/Contents/section0.xml — 문항 지시문.
    # 12pt/자간-12 로 시작해 11pt/장평95/자간-8 로 이어진다.  첫 run만 보면
    # 두 줄로 잡혀 셀이 한 줄만큼 높아진다.
    ('tpl2 [논술형 1] 지시문 (12pt+11pt, 자간 -12/-10/-8)',
     [StyledRun('[논술형 1] ', 1200, 100, -12),
      StyledRun('교내 ', 1100, 95, -10),
      StyledRun('카페에서는 다음과 같은 안내문을 게시했다. 두 학생의 대화를 읽고 물음에 ',
                1100, 95, -8),
      StyledRun('답하시오.', 1100, 95, -10)],
     47056, 'KEEP_WORD', [0]),
    # 실제 워크북 문서(수업설계 워크북, 굴림 10pt)의 문단들.
    # run을 dict으로 준 경우 — HWPX 헤더 파서가 내놓는 모양 그대로다.
    ('워크북 성찰 질문 (자간 +1/-5/-1, dict run)',
     [{'text': ' ', 'em': 1000, 'spacing': 1},
      {'text': "위에서 확인한 교육과정의 핵심 요구 사항('깊이있는 학습', '학생 참여',"
               " '과정 평가', '일관성' 등) 중,", 'em': 1000, 'spacing': -5},
      {'text': ' 나의 고민을 해결하는 데 가장 큰 실마리를 줄 것이라고 생각하는 '
               '키워드는 무엇인가요? ', 'em': 1000, 'spacing': -1}],
     45358, 'KEEP_WORD', [0, 65]),
    # 워크북 — 크기만 섞인 문단 (13pt 공백 + 12pt 본문)
    ('워크북 탐구 질문 (13pt 공백 + 12pt 본문)',
     [StyledRun(' ', 1300),
      StyledRun("이 단원을 통해 학생의 어떤 '궁극적 성장'을 이끌어 낼 것인가?", 1200)],
     36976, 'KEEP_WORD', [0]),
    # 워크북 — 자간을 스크립트별 dict으로 준 경우
    ('워크북 가치·태도 (자간 -2/-8, 스크립트별 dict)',
     [StyledRun('가치·태도: ', 1000,
                spacing={k: -2 for k in SCRIPT_SLOTS}),
      StyledRun("학생이 어떤 마음을 '느끼고 내면화해야 하는가'에 대한 영역. "
                '(협력, 존중, 학습 동기 등)', 1000,
                spacing={k: -8 for k in SCRIPT_SLOTS})],
     44858, 'KEEP_WORD', [0]),
]


def _run(cases, profile):
    use_profile(profile)
    ok = never_late = 0
    for label, text, hz, em, wu, want in cases:
        got = wrap(text, hz, em=em, word_unit=wu)
        exact = got == want
        late = any(a > b for a, b in zip(got, want))
        ok += exact
        never_late += not late
        tag = 'PASS' if exact else ('early' if not late else 'LATE!')
        print(f'  [{tag:5s}] {label}')
        if not exact:
            print(f'          text={text!r}')
            print(f'          want={want}  got={got}')
    print(f'  -> exact {ok}/{len(cases)},  never-breaks-late {never_late}/{len(cases)}')
    return ok, never_late, len(cases)


def _run_mixed(cases, profile):
    """새 run 인자 회귀시험.  옛 방식(첫 run의 charPr 하나)과 나란히 찍는다.

    줄 수(len)가 셀 높이를 정하므로 exact 와 별도로 줄 수 일치를 센다.
    """
    use_profile(profile)
    ok = lines = old_ok = old_lines = 0
    for label, runs, hz, bnlw, want in cases:
        runs = [as_run(r) for r in runs]
        text = ''.join(r.text for r in runs)
        got = wrap(text, hz, runs=runs, break_non_latin_word=bnlw)
        first = runs[0]
        old = wrap(text, hz, em=first.em, ratio=first.ratio,
                   spacing=first.spacing,
                   word_unit=_NON_LATIN_WORD_UNIT[bnlw])
        ok += got == want
        lines += len(got) == len(want)
        old_ok += old == want
        old_lines += len(old) == len(want)
        tag = ('PASS' if got == want else
               'lines' if len(got) == len(want) else 'FAIL')
        print(f'  [{tag:5s}] {label}')
        print(f'          want={want}  runs={got}  옛 단일 charPr={old}')
        if len(got) != len(want):
            print(f'          text={text!r}')
    print(f'  -> runs 인자   exact {ok}/{len(cases)}, 줄 수 {lines}/{len(cases)}')
    print(f'  -> 옛 단일 charPr exact {old_ok}/{len(cases)}, '
          f'줄 수 {old_lines}/{len(cases)}')
    return ok, lines, len(cases)


def _corpus_test(profile):
    import json, os, unicodedata
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, 'corpus.json')
    if not os.path.exists(path):
        print('  (corpus.json absent - skipping bulk regression)'); return
    import model2, sanity
    use_profile(profile)
    cs = model2.dedupe([x for x in json.load(open(path))
                        if x['clean'] and len(x['charPrIds']) == 1])
    cs = [x for x in cs if sanity.sane(x) and x['file'] != 'tac-img-02.hwpx']
    subsets = {
        'ALL Hangul-authored, sanity-checked': cs,
        'Hangul 13 subset': [x for x in cs if x['appv'].startswith('13')],
        '맑은 고딕 (ratio100 spacing0)':
            [x for x in cs if model2.sig(x)[0] == '맑은 고딕'
             and (model2.sig(x)[2], model2.sig(x)[3], model2.sig(x)[4]) == ('100','0','100')],
        'CJK + space only (break-rule only)':
            [x for x in cs if all(unicodedata.east_asian_width(c) in ('W','F')
                                  or c in SPACES for c in x['text'])],
    }
    for name, ds in subsets.items():
        if not ds: continue
        ok = late = 0
        for x in ds:
            cp = list(x['charPrs'].values())[0] or {}
            em = model2.em_of(cp)
            ratio = float((cp.get('ratio') or {}).get('hangul', 100) or 100)
            sp = float((cp.get('spacing') or {}).get('hangul', 0) or 0)
            bs = (x['paraPr'] or {}).get('breakSetting', {}) or {}
            wu = bs.get('breakNonLatinWord', 'KEEP_WORD') == 'BREAK_WORD'
            hz = [float(s['horzsize']) for s in x['segs']]
            want = [int(s['textpos']) for s in x['segs']]
            got = wrap(x['text'], hz, em=em, word_unit=wu, ratio=ratio, spacing=sp)
            if got == want: ok += 1
            elif any(a > b for a, b in zip(got, want)): late += 1
        print(f'  {name:36s} exact {ok:5d}/{len(ds):5d} = {ok/len(ds)*100:5.1f}%'
              f'   breaks-late {late:4d} ({late/len(ds)*100:.1f}%)')


# --------------------------------------------------------------------------
# 4. command line
# --------------------------------------------------------------------------
CLI_USAGE = """사용법:
  python3 metrics.py                      회귀시험을 돌린다
  python3 metrics.py wrap-runs --input paragraph.json [--output out.json]
                                          [--expect-lines N]
                                          문단 하나를 줄바꿈한다

paragraph.json:
  {"runs": [{"text": "...", "em": 1000, "ratio": 100, "spacing": -5,
             "rel_sz": 100}, ...],
   "paragraph": {"horzsize": 41508,
                 "break_non_latin_word": "KEEP_WORD",
                 "break_latin_word": "KEEP_WORD",
                 "safety": 0, "kinsoku": true,
                 "profile": "conservative", "hanging": true}}
  horzsize는 숫자 하나이거나 줄별 숫자 목록이다.

종료 코드: 0 성공  2 입력 스키마 오류  3 미지원 속성  4 기대 줄 수 불일치
           5 파일 입출력 실패"""

_PARA_KEYS = {'horzsize', 'break_non_latin_word', 'break_latin_word',
              'safety', 'kinsoku', 'profile', 'hanging'}


def _cli_wrap_runs(argv):
    import json
    global HANGABLE
    args = {}
    it = iter(argv)
    for a in it:
        if a in ('--input', '--output', '--expect-lines'):
            args[a] = next(it, None)
            if args[a] is None:
                print(f'{a} 뒤에 값이 없다.'); return 2
        else:
            print(f'모르는 인자다: {a}\n\n{CLI_USAGE}'); return 2
    if '--input' not in args:
        print(f'--input 이 없다.\n\n{CLI_USAGE}'); return 2
    try:
        with open(args['--input'], encoding='utf-8') as f:
            doc = json.load(f)
    except OSError as e:
        print(f'입력 파일을 읽지 못했다: {e}'); return 5
    except ValueError as e:
        print(f'입력이 올바른 JSON이 아니다: {e}'); return 2

    if not isinstance(doc, Mapping) or 'runs' not in doc:
        print("입력에 'runs'가 없다."); return 2
    para = doc.get('paragraph') or {}
    unsupported = sorted(set(para) - _PARA_KEYS)
    if unsupported:
        print('문단 속성 중 이 모형이 다루지 못하는 것이 있다: '
              f'{unsupported}. 조용히 무시하지 않고 멈춘다.')
        return 3
    if 'horzsize' not in para:
        print("paragraph에 'horzsize'가 없다."); return 2
    try:
        runs = [as_run(r) for r in doc['runs']]
    except (TypeError, ValueError) as e:
        print(f'run을 읽지 못했다: {e}'); return 3

    use_profile(para.get('profile', 'conservative'))
    if not para.get('hanging', True):
        HANGABLE = frozenset()
    text = ''.join(r.text for r in runs)
    try:
        starts = wrap(text, para['horzsize'], runs=runs,
                      kinsoku=bool(para.get('kinsoku', True)),
                      safety=float(para.get('safety', 0)),
                      break_non_latin_word=para.get('break_non_latin_word'),
                      break_latin_word=para.get('break_latin_word'))
    except (TypeError, ValueError) as e:
        print(f'줄바꿈에 실패했다: {e}'); return 2

    limit_of = _limit_getter(para['horzsize'])
    adv = measure_advances(text, runs=runs)
    bounds = starts + [len(text)]
    lines = []
    for i, tp in enumerate(starts):
        seg = text[tp:bounds[i + 1]]
        keep = len(seg.rstrip(SPACES))
        lines.append({'index': i, 'start': tp, 'end': bounds[i + 1],
                      'text': seg,
                      'measured_width': round(sum(adv[tp:tp + keep]), 3),
                      'limit': limit_of(i)})
    result = {'line_count': len(starts), 'textpos': starts, 'lines': lines,
              'unsupported_properties': [],
              'overflow': [ln['index'] for ln in lines
                           if ln['measured_width'] > ln['limit'] + 1e-9]}
    out = json.dumps(result, ensure_ascii=False, indent=1)
    if args.get('--output'):
        try:
            with open(args['--output'], 'w', encoding='utf-8') as f:
                f.write(out + '\n')
        except OSError as e:
            print(f'결과 파일을 쓰지 못했다: {e}'); return 5
    else:
        print(out)
    if args.get('--expect-lines') is not None:
        try:
            want = int(args['--expect-lines'])
        except ValueError:
            print('--expect-lines 는 정수여야 한다.'); return 2
        if want != len(starts):
            print(f'줄 수가 기대와 다르다: 기대 {want}, 계산 {len(starts)}')
            return 4
    return 0


def _selftest():
    """회귀시험.  종료 코드 0 = 안전, 1 = 못 봐줄 회귀.

    한 글자 일찍 끊는 것(early)은 캐시가 짧아질 뿐이라 인쇄가 깨지지 않으므로
    실패로 치지 않는다.  한글보다 **늦게** 끊거나(칸 밖으로 넘친다) mixed-run
    문단의 **줄 수**가 틀리면(칸 높이가 어긋나 글자가 겹친다) 실패다.
    """
    bad = []
    for prof in ('bestfit', 'conservative'):
        print(f'############ profile = {prof} ############')
        print('=== template reference cases ===')
        a1, b1, n1 = _run(TEMPLATE_CASES, prof)
        print('=== additional ground-truth cases ===')
        a2, b2, n2 = _run(EXTRA_CASES, prof)
        print(f'=== curated total: exact {a1+a2}/{n1+n2}, '
              f'never-late {b1+b2}/{n1+n2} ===')
        if b1 + b2 != n1 + n2:
            bad.append(f'{prof}: 한글보다 늦게 끊은 문단 '
                       f'{n1 + n2 - b1 - b2}건 — 칸 밖으로 넘친다')
        print('=== mixed-run ground truth (runs= 인자) ===')
        if MIXED_RUN_CASES:
            _, lines, nm = _run_mixed(MIXED_RUN_CASES, prof)
            if lines != nm:
                bad.append(f'{prof}: run별 charPr로도 줄 수를 못 맞춘 문단 '
                           f'{nm - lines}건 — 칸 높이가 어긋난다')
        else:
            print('  (없음)')
        print('=== bulk corpus regression ===')
        _corpus_test(prof)
        print()
    use_profile('conservative')
    if bad:
        print('회귀시험 실패:')
        for line in bad:
            print(f'  - {line}')
        return 1
    return 0


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'wrap-runs':
        raise SystemExit(_cli_wrap_runs(sys.argv[2:]))
    if len(sys.argv) > 1:
        print(CLI_USAGE)
        raise SystemExit(2 if sys.argv[1] not in ('-h', '--help') else 0)
    raise SystemExit(_selftest())
