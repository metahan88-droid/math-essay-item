#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""슬롯 JSON을 Codex 적대적 검증용 평문(review_input.txt)으로 펼친다.

    python3 <스킬 루트>/tools/make_review_input.py <슬롯.json> [출력경로|출력폴더]

Codex는 이 대화를 모르고 JSON을 읽기 어려워한다. 그래서 슬롯을 `===== [키] =====`
구분자를 넣은 평문으로 펼쳐 준다. 표준 라이브러리만 쓴다(외부 패키지 없음).

## 설계 두 가지 — 실사용에서 난 결함을 막는다

1. **키 목록을 하드코딩하지 않는다.** 실을 키는 슬롯 JSON에 실제로 있는 키 전부다.
   아래 GROUPS는 *순서표*일 뿐 *허용 목록*이 아니다. 규칙은 이름 하나가 아니라
   패턴이라서 `std3_A`·`lesson6_act`·`item5_element`처럼 번호만 늘어난 키는 저절로
   제자리에 들어가고, 패턴에도 안 걸리는 낯선 키는 마지막 「그 밖의 키」 묶음에
   실린 뒤 자체 점검에서 이름이 불린다. 어떤 키도 조용히 빠지지 않는다.
   (문서에 order 배열을 박아 두었더니 새로 생긴 `_rubric_atoms_note`가 통째로
    빠진 채 검토가 돌았다. 그 사고를 구조로 막는다.)

2. **값에 단위를 덧붙이지 않는다.** 특히 `rubric_rows`의 `score`는 원문 그대로 쓴다.
   예전 생성기가 `f"{score}점"`으로 찍는 바람에 합계 행의 `"20점"`이 `"20점점"`이
   되었고, Codex가 이것을 오탈자 결함으로 보고했다 — 생성기 버그가 가짜 지적을
   만들었다. 자체 점검이 배점 열을 다시 읽어 원문과 글자까지 같은지 대조한다.

## 자체 점검 (실패하면 종료 코드 1)

· 슬롯 JSON의 키 수 == 출력에 실린 `===== [키] =====` 수, 빠진 키는 이름을 댄다
· `rubric_rows`의 행 수와 배점 값이 출력에서 왜곡 없이 살아 있는지 왕복 대조
· 낯선 키(그 밖의 키)는 이름을 보고해 순서표를 넓힐 단서를 남긴다

종료 코드: 0 정상 / 1 생성·점검 실패 / 2 사용법 오류
"""

import json
import os
import re
import sys
import unicodedata

# 이 파일 위치에서 스킬 루트를 되짚는다(<스킬 루트>/tools/make_review_input.py).
# SKILL.md가 실제로 거기 있을 때만 스킬 루트로 인정한다 — tools/를 다른 곳에
# 복사해 쓰는 경우에 애먼 폴더를 잠그지 않으려고.
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN_SKILL = os.path.isfile(os.path.join(SKILL_ROOT, "SKILL.md"))

SEP_OPEN = "===== ["
SEP_CLOSE = "] ====="
COL_SEP = " | "
PAD_MAX = 60          # 표 열을 이 폭까지만 맞춘다(더 길면 맞추지 않는다)

# ── 순서표 ────────────────────────────────────────────────────────────────
# (묶음 이름, 번호 우선 정렬 여부, [규칙…]). 규칙은 정규식이며 `n`(숫자)·`a`(글자)를
# 이름 붙은 그룹으로 잡으면 그 값이 정렬 색인이 된다. 규칙에 걸리지 않은 키는
# 마지막 「그 밖의 키」로 간다 — 목록이 아니라 순서표라는 뜻이다.
GROUPS = [
    ("1. 과제 개요", False, [
        r"^affiliation$", r"^name$", r"^_check_class$",
        r"^school_level$", r"^grade$", r"^subject$", r"^unit$",
        r"^task$", r"^purpose$",
    ]),
    ("2. 성취기준·성취수준", True, [
        r"^std(?P<n>\d+)_text$",
        r"^std(?P<n>\d+)_(?P<a>[A-E])$",
        r"^_alignment_note$",
    ]),
    ("3. 문항 정보", True, [
        r"^item(?P<n>\d+)_type$",
        r"^item(?P<n>\d+)_form$",
        r"^item(?P<n>\d+)_element$",
    ]),
    ("4. 학생 지면", False, [
        r"^item_intro$", r"^item_questions$", r"^item_cond$",
        r"^_flat_cond$", r"^_figs$", r"^_figs_spec$",
    ]),
    ("5. 예시답안", True, [
        r"^answer_n(?P<n>\d+)$",
        r"^answer(?P<n>\d+)$",
    ]),
    ("6. 채점기준", True, [
        r"^rubric_rows$",
        r"^_rubric_atoms_note$",
        r"^rubric_n(?P<n>\d+)$",
        r"^rubric_e(?P<n>\d+)$",
        r"^rubric_p(?P<n>\d+)$",
        r"^rubric_c(?P<n>\d+)$",
    ]),
    ("7. 유의점", False, [
        r"^partial$", r"^caution$",
    ]),
    ("8. 성취수준 점수 구간", True, [
        r"^level_(?P<a>[A-E])_score$",
        r"^level_(?P<a>[A-E])_desc$",
    ]),
    ("9. 차시 계획", True, [
        r"^lesson(?P<n>\d+)_act$",
        r"^lesson(?P<n>\d+)_eval$",
    ]),
]
OTHER_GROUP = "10. 그 밖의 키 (순서표에 없는 키 — 빠뜨리지 않으려고 여기 싣는다)"

def _compile(title, num_first, pats):
    rules = [re.compile(p) for p in pats]
    # 번호 우선 묶음에서 색인 없는 규칙(rubric_rows·_alignment_note 등)이 색인 있는
    # 규칙 앞에 적혔으면 앞에, 뒤에 적혔으면 뒤에 오게 한다.
    idx_ranks = [i for i, r in enumerate(rules)
                 if "n" in r.groupindex or "a" in r.groupindex]
    return (title, num_first, rules, min(idx_ranks) if idx_ranks else None)


_COMPILED = [_compile(*g) for g in GROUPS]

# rubric_rows 열 이름을 사람 말로. 모르는 열은 키 이름을 그대로 쓴다.
RUBRIC_COL_LABEL = {"item": "문항", "elem": "평가요소(채점요소)",
                    "score": "배점", "desc": "수행 특성(채점 기준)"}


def die(msg, code=1):
    sys.stderr.write("오류: %s\n" % msg)
    sys.exit(code)


def under(path, root):
    """path가 root 안에 있는가. 드라이브가 달라 비교가 안 되면 아니라고 본다."""
    try:
        rp, rr = os.path.realpath(path), os.path.realpath(root)
        return rp == rr or os.path.commonpath([rp, rr]) == rr
    except ValueError:
        return False


def disp_width(s):
    """동아시아 전각을 2칸으로 세는 표시 폭."""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in s)


def pad(s, width):
    gap = width - disp_width(s)
    return s + " " * gap if gap > 0 else s


def sort_key(key):
    """키 하나의 정렬 자리를 정한다. 걸리는 규칙이 없으면 None."""
    for gi, (title, num_first, pats, first_idx) in enumerate(_COMPILED):
        for ri, pat in enumerate(pats):
            m = pat.match(key)
            if not m:
                continue
            gd = m.groupdict()
            n, a = gd.get("n"), gd.get("a")
            if n or a:
                # 형이 섞여도 비교가 깨지지 않게 삼중항으로 만든다.
                idx = (1, int(n) if n else 0, a or "")
            else:
                idx = (0 if (first_idx is None or ri < first_idx) else 2, 0, "")
            rank = (idx, ri) if num_first else (ri, idx)
            return (gi, rank, key)
    return None


def render_scalar(x):
    if isinstance(x, str):
        return x
    if isinstance(x, bool):
        return "true" if x else "false"
    if x is None:
        return "null"
    if isinstance(x, (int, float)):
        return str(x)
    return json.dumps(x, ensure_ascii=False)


def render_rubric(rows):
    """rubric_rows를 사람이 읽을 표로 편다.

    값은 **그대로** 옮긴다. 배점에 '점'을 붙이지 않는다 — 합계 행은 이미 "20점"이다.
    돌려주는 scores는 자체 점검이 출력에서 다시 읽어 대조할 원문 배점이다.
    """
    plain = [r for r in rows if not isinstance(r, dict)]
    if plain:
        # 형식이 다르면 표로 펴지 말고 원문 그대로 넘긴다(조용히 버리지 않는다).
        return "\n".join(render_scalar(r) for r in rows), None, None

    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    if not cols:
        return "(빈 배열)", None, None

    cells = []
    for r in rows:
        # 셀 안 줄바꿈은 ' / '로 이어 붙인다. 한 줄도 버리지 않는다(item은 세 줄).
        cells.append([render_scalar(r.get(k, "")).replace("\n", " / ") for k in cols])

    widths = []
    for ci, k in enumerate(cols):
        w = max([disp_width(RUBRIC_COL_LABEL.get(k, k))] +
                [disp_width(row[ci]) for row in cells])
        widths.append(min(w, PAD_MAX))

    def line(vals):
        # 마지막 열은 채우지 않는다(줄 끝 공백을 만들지 않으려고).
        return COL_SEP.join(pad(v, widths[i]) if i < len(vals) - 1 else v
                            for i, v in enumerate(vals))

    out = [line([RUBRIC_COL_LABEL.get(k, k) for k in cols]),
           line(["-" * min(widths[i], 12) for i in range(len(cols))])]
    out.extend(line(row) for row in cells)

    score_i = cols.index("score") if "score" in cols else None
    scores = [row[score_i] for row in cells] if score_i is not None else None
    return "\n".join(out), score_i, scores


def render_value(key, val):
    if key == "rubric_rows" and isinstance(val, list) and val:
        return render_rubric(val)
    if isinstance(val, str):
        return (val if val != "" else "(빈 값)"), None, None
    if isinstance(val, list):
        if not val:
            return "(빈 배열)", None, None
        return "\n".join(render_scalar(x) for x in val), None, None
    if isinstance(val, dict):
        if not val:
            return "(빈 객체)", None, None
        return "\n".join("%s: %s" % (k, render_scalar(v))
                         for k, v in val.items()), None, None
    return render_scalar(val), None, None


def build(slots, src_name):
    """(본문, 실린 키 순서, 배점 왕복 대조용 정보)"""
    ordered, unknown = [], []
    for i, key in enumerate(slots):
        sk = sort_key(key)
        if sk is None:
            unknown.append((i, key))
        else:
            ordered.append((sk, key))
    ordered.sort()

    buckets = {}                      # 묶음 이름 → [키…]
    for (gi, _, _), key in ordered:
        buckets.setdefault(_COMPILED[gi][0], []).append(key)
    if unknown:
        buckets[OTHER_GROUP] = [k for _, k in sorted(unknown)]

    titles = [g[0] for g in _COMPILED] + [OTHER_GROUP]

    lines = [
        "# 검토 자료 — %s (슬롯 키 %d개)" % (src_name, len(slots)),
        "# 섹션 구분자: %s슬롯 키%s   묶음 구분자: ########## 묶음 이름 ##########" % (SEP_OPEN, SEP_CLOSE),
        "# 값은 슬롯 JSON 원문 그대로다. 배열은 한 줄에 한 원소, 표는 ' | '로 나눈 열이다.",
        "# `_`로 시작하는 키는 조판 지면에 인쇄되지 않는 내부 주석·지시다(검토에는 필요).",
        "# 채점기준표 셀 안의 줄바꿈은 ' / '로 이어 붙였다.",
    ]
    emitted, rubric_info = [], None
    for title in titles:
        keys = buckets.get(title)
        if not keys:
            continue
        lines.append("")
        lines.append("########## %s ##########" % title)
        for key in keys:
            text, score_i, scores = render_value(key, slots[key])
            if key == "rubric_rows" and scores is not None:
                rubric_info = (score_i, scores)
            mark = "  (내부 주석 — 지면 밖)" if key.startswith("_") else ""
            lines.append("")
            lines.append("%s%s%s%s" % (SEP_OPEN, key, SEP_CLOSE, mark))
            lines.append(text)
            emitted.append(key)
    return "\n".join(lines) + "\n", emitted, rubric_info, buckets.get(OTHER_GROUP, [])


def verify(path, slots, emitted, rubric_info):
    """쓴 파일을 되읽어 점검한다. 문제 목록을 돌려준다(빈 목록이면 통과)."""
    problems = []
    with open(path, encoding="utf-8") as f:
        text = f.read()

    found = re.findall(r"(?m)^%s(.+?)%s" % (re.escape(SEP_OPEN), re.escape(SEP_CLOSE)), text)
    missing = [k for k in slots if k not in found]
    extra = [k for k in found if k not in slots]
    dup = sorted({k for k in found if found.count(k) > 1})
    print("슬롯 JSON 키 %d개 / 출력에 실린 키 %d개" % (len(slots), len(found)))
    if missing:
        problems.append("출력에 빠진 키 %d개: %s" % (len(missing), ", ".join(missing)))
    if extra:
        problems.append("슬롯에 없는 키가 출력에 있음: %s" % ", ".join(extra))
    if dup:
        problems.append("같은 키가 두 번 실림: %s" % ", ".join(dup))
    if set(emitted) != set(found):
        problems.append("생성 기록과 파일 내용이 다름(생성 %d · 파일 %d)" % (len(emitted), len(found)))
    if not missing and not extra and not dup:
        print("  누락 0건 · 잉여 0건 · 중복 0건")

    # 배점 왕복 대조 — 원문 그대로인가(단위가 덧붙지 않았는가).
    if rubric_info and rubric_info[0] is not None:
        score_i, src_scores = rubric_info
        block = text.split(SEP_OPEN + "rubric_rows" + SEP_CLOSE, 1)
        if len(block) < 2:
            problems.append("rubric_rows 절을 되읽지 못했다")
        else:
            body = block[1].split("\n" + SEP_OPEN, 1)[0].strip("\n").split("\n")
            data = body[2:2 + len(src_scores)]           # 머리글·구분선 두 줄 건너뛴다
            got = [ln.split(COL_SEP, score_i + 1)[score_i].strip()
                   if len(ln.split(COL_SEP, score_i + 1)) > score_i else "(파싱 실패)"
                   for ln in data]
            if len(data) != len(src_scores):
                problems.append("채점기준표 행 수가 다름: 원문 %d행 · 출력 %d행"
                                % (len(src_scores), len(data)))
            bad = [(i, s, g) for i, (s, g) in enumerate(zip(src_scores, got)) if s != g]
            if bad:
                for i, s, g in bad[:5]:
                    problems.append("채점기준표 %d행 배점이 왜곡됨: 원문 %r → 출력 %r" % (i + 1, s, g))
            else:
                print("채점기준표 %d행 · 배점 값 원문 그대로(단위 덧붙임 없음)" % len(data))
    return problems


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        sys.stderr.write(
            "사용법: python3 make_review_input.py <슬롯.json> [출력경로|출력폴더]\n"
            "  출력경로를 생략하면 슬롯 JSON 옆에 review_input.txt를 만든다.\n"
            "  폴더를 주면 그 폴더 안에 review_input.txt를 만든다.\n")
        return 2
    if len(argv) > 3:
        sys.stderr.write("오류: 인자가 너무 많다(최대 2개). 사용법은 --help.\n")
        return 2

    src = os.path.abspath(argv[1])
    if not os.path.isfile(src):
        die("슬롯 JSON을 찾을 수 없다: %s" % src)
    try:
        with open(src, encoding="utf-8") as f:
            slots = json.load(f)
    except (OSError, ValueError) as ex:
        die("슬롯 JSON을 읽지 못했다: %s: %s" % (src, ex))
    if not isinstance(slots, dict):
        die("슬롯 JSON의 최상위가 객체가 아니다(%s를 받았다): %s"
            % (type(slots).__name__, src))
    if not slots:
        die("슬롯 JSON이 비었다: %s" % src)

    if len(argv) == 3:
        out = os.path.abspath(argv[2])
        if os.path.isdir(out):
            out = os.path.join(out, "review_input.txt")
    else:
        out = os.path.join(os.path.dirname(src), "review_input.txt")

    # 산출물은 작업 폴더에 만든다. 스킬 폴더 안에는 쓰지 않는다
    # (스킬 동봉 예시로 돌릴 때 examples/ 안에 파일이 쌓이는 것을 막는다).
    if IN_SKILL and under(out, SKILL_ROOT):
        die("스킬 폴더 안에는 쓰지 않는다: %s\n"
            "      작업 폴더 경로를 둘째 인자로 줘라. 예:\n"
            "      python3 %s %s <작업폴더>/review_input.txt"
            % (out, os.path.abspath(argv[0]), src), 2)

    body, emitted, rubric_info, unknown = build(slots, os.path.basename(src))
    d = os.path.dirname(out)
    if d and not os.path.isdir(d):
        try:
            os.makedirs(d, exist_ok=True)
        except OSError as ex:
            die("출력 폴더를 만들지 못했다: %s: %s" % (d, ex))
    try:
        with open(out, "w", encoding="utf-8") as f:
            f.write(body)
    except OSError as ex:
        die("출력 파일을 쓰지 못했다: %s: %s" % (out, ex))

    print("씀: %s (%d바이트)" % (out, os.path.getsize(out)))
    problems = verify(out, slots, emitted, rubric_info)
    if unknown:
        print("순서표에 없어 「그 밖의 키」로 실린 키 %d개: %s"
              % (len(unknown), ", ".join(unknown)))
        print("  → 빠지지는 않았다. 자주 쓰는 키면 GROUPS에 규칙을 넣어 제자리로 보내라.")
    if problems:
        sys.stderr.write("\n자체 점검 실패 — 이 파일로 검토를 돌리지 마라.\n")
        for p in problems:
            sys.stderr.write("  · %s\n" % p)
        return 1
    print("자체 점검 통과.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
