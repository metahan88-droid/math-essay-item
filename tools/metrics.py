#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HWPX line-metrics model for 맑은 고딕 (Malgun Gothic), reverse-engineered from
Hangul-generated HWPX files.

Deliverables
------------
    width(ch, em=1200)          -> advance width of one character, in HWPUNIT
    wrap(text, horzsize, ...)   -> list of line-start character indices
                                   (== the textpos values of <hp:lineseg>)

Units
-----
    1 HWPUNIT = 1/7200 inch.   12 pt = 12/72 inch = 1200 HWPUNIT = 1 em.

Run this file directly to execute the ground-truth regression tests.
"""
import unicodedata as ud

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


def width(ch, em=1200, ratio=100, spacing=0):
    """Advance width of `ch` in HWPUNIT.

    em       : charPr/@height (1200 == 12 pt) times relSz/100
    ratio    : charPr/ratio/@hangul  (장평, percent)
    spacing  : charPr/spacing/@hangul (자간, percent of em, may be negative)
    """
    f = _factor(ch)
    if f == 0.0:
        return 0.0
    return em * f * ratio / 100.0 + em * spacing / 100.0


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


def wrap(text, horzsize, em=1200, word_unit=True, ratio=100, spacing=0,
         latin_word_unit=True, kinsoku=True, safety=0):
    """Greedy line breaking.  Returns the list of line-start indices,
    i.e. exactly the `textpos` attributes of the <hp:lineseg> elements.

    horzsize : available width in HWPUNIT (may be an int, or a list/callable
               giving a per-line width).
    safety   : HWPUNIT shaved off every line's limit; use a positive value to
               bias towards breaking early.
    """
    if callable(horzsize):
        limit_of = horzsize
    elif isinstance(horzsize, (list, tuple)):
        limit_of = lambda i: float(horzsize[min(i, len(horzsize)-1)])
    else:
        limit_of = lambda i: float(horzsize)

    w = [width(c, em, ratio, spacing) for c in text]
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


def line_width(text, em=1200, ratio=100, spacing=0):
    """Rendered width of one line, ignoring hanging trailing spaces."""
    return sum(width(c, em, ratio, spacing) for c in text.rstrip(SPACES))


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
def linesegarray(text, horzsize, char_height=1200, line_spacing_pct=120,
                 word_unit=True, ratio=100, spacing=0, indent=0):
    """Build the <hp:linesegarray> XML for one paragraph.

    char_height      : charPr/@height of the run (1200 == 12 pt)
    line_spacing_pct : paraPr/lineSpacing/@value when type="PERCENT"
    Verified against the template: vertsize == textheight == char_height,
    baseline == round(vertsize*0.85), spacing == char_height*(pct-100)/100,
    vertpos == line_index * (vertsize + spacing), horzpos == 0, flags == 393216.
    """
    starts = wrap(text, horzsize, em=char_height, word_unit=word_unit,
                  ratio=ratio, spacing=spacing)
    vs = int(char_height)
    sp = int(round(char_height * (line_spacing_pct - 100) / 100.0))
    base = int(round(vs * 0.85))
    pitch = vs + sp
    hz = int(horzsize if not isinstance(horzsize, (list, tuple)) else horzsize[0])
    segs = []
    for i, tp in enumerate(starts):
        segs.append(
            f'<hp:lineseg textpos="{tp}" vertpos="{i*pitch}" vertsize="{vs}" '
            f'textheight="{vs}" baseline="{base}" spacing="{sp}" '
            f'horzpos="{indent if i == 0 else 0}" horzsize="{hz}" flags="393216"/>')
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


if __name__ == '__main__':
    for prof in ('bestfit', 'conservative'):
        print(f'############ profile = {prof} ############')
        print('=== template reference cases ===')
        a1, b1, n1 = _run(TEMPLATE_CASES, prof)
        print('=== additional ground-truth cases ===')
        a2, b2, n2 = _run(EXTRA_CASES, prof)
        print(f'=== curated total: exact {a1+a2}/{n1+n2}, '
              f'never-late {b1+b2}/{n1+n2} ===')
        print('=== bulk corpus regression ===')
        _corpus_test(prof)
        print()
    use_profile('conservative')
