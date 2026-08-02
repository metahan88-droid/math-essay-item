#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NCIC 공시 자료(성취기준·성취수준) 확보 도구.

스킬 원칙 6과 `references/standards.md` §1은 "NCIC 공시 자료만 근거로 삼고
지어내지 않는다"고 정한다. 이 도구는 그 근거를 **실제로 손에 넣는** 경로다.

하는 일 셋
  1) 내려받기 — 게시글 번호로 첨부 목록을 얻어 .hwp/.pdf를 작업 폴더에 받는다.
  2) 본문 추출 — 받은 .hwp에서 텍스트를 뽑아 같은 이름의 .txt로 저장한다.
  3) 성취기준 찾기 — `--find "[9수04-18]"`로 그 코드의 성취기준 문구와
     수준별 진술을 표 구조 그대로 뽑고, **수준체계(2015 상·중·하 3단계 /
     2022 A~E 5단계)를 판정해 함께 알린다.**

HWP 5.x 읽는 법 (실사용에서 검증된 경로)
  · HWP 5.x는 OLE 복합문서다. `olefile`로 열고 BodyText/Section* 스트림을 읽는다.
  · FileHeader의 37번째 바이트(인덱스 36) 최하위 비트가 1이면 압축이므로
    `zlib.decompress(data, -15)`로 푼다.
  · 레코드 헤더 4바이트를 리틀엔디언 uint32로 읽어
    tag = h & 0x3FF, level = (h >> 10) & 0x3FF, size = (h >> 20) & 0xFFF.
    size가 0xFFF면 이어지는 4바이트가 실제 크기다.
  · tag 67(HWPTAG_PARA_TEXT)의 데이터를 utf-16-le로 디코드하면 문단 텍스트다.
  · 표는 tag 77(HWPTAG_TABLE)로 열리고 각 칸은 같은 level의 tag 72
    (HWPTAG_LIST_HEADER)다. 칸 머리에 col/row/colSpan/rowSpan이 들어 있어
    **세로 병합된 성취수준 칸을 원문 그대로 복원**할 수 있다(R1-10).

의존
  표준 라이브러리 + `olefile`. olefile이 없으면 설치 안내를 찍고 종료 코드 3.
  네트워크 없이 이미 받아 둔 .hwp만 다루는 것도 된다(`extract`/`find <파일>`).

종료 코드
  0 성공 / 2 사용법·인자 오류 / 3 olefile 없음 / 4 네트워크 실패 /
  5 게시글 없음 / 6 첨부 없음 / 7 HWP 파싱 실패 / 8 성취기준 코드 못 찾음
"""

import argparse
import io
import json
import os
import re
import ssl
import struct
import sys
import urllib.error
import urllib.parse
import urllib.request

# ── 종료 코드 ───────────────────────────────────────────────────────────────
EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NO_OLEFILE = 3
EXIT_NETWORK = 4
EXIT_NO_ARTICLE = 5
EXIT_NO_ATTACH = 6
EXIT_HWP_PARSE = 7
EXIT_NOT_FOUND = 8

BASE = "https://ncic.re.kr"
VIEW_URL = BASE + "/bbs/standard/view/{idx}.do"
DOWNLOAD_URL = BASE + "/bbs/download.do?articleIdx={idx}&fileName={name}"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"

# standards.md §1.1의 게시글 번호. 문서를 읽어 덮어쓰고, 못 읽으면 이 값을 쓴다.
FALLBACK_ARTICLES = {
    "중2022": 772,
    "고2022": 780,
    "중2015": 735,
    "고2015": 753,
}

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(TOOLS_DIR)
STANDARDS_MD = os.path.join(SKILL_ROOT, "references", "standards.md")

LV_2015 = ["상", "중", "하"]
LV_2022 = ["A", "B", "C", "D", "E"]
LV_ALL = set(LV_2015) | set(LV_2022)

# 성취기준 코드: [9수04-18], [10공수1-01-03], [12미적II-01-02] 등
CODE_RE = re.compile(r"\[\d{1,2}[가-힣A-Za-z]+\d*(?:[IVXⅠ-Ⅹ]+)?(?:-\d{2})?-\d{2}\]")
SUB_STD_RE = re.compile(r"^\[평가준거\s*성취기준")


def say(*args):
    print(*args, file=sys.stderr, flush=True)


def die(code, *lines):
    """사람 말로 무엇이 왜 실패했는지 찍고 종료 코드로 알린다."""
    sys.stdout.flush()          # 표준출력 뒤에 실패 이유가 오도록 순서를 맞춘다
    say("")
    say("[실패] " + str(lines[0]))
    for extra in lines[1:]:
        say("       " + str(extra))
    say("       종료 코드 %d" % code)
    sys.exit(code)


# ── olefile ────────────────────────────────────────────────────────────────
def require_olefile():
    try:
        import olefile  # noqa: F401
        return olefile
    except ImportError:
        die(
            EXIT_NO_OLEFILE,
            "olefile 패키지가 없어 HWP(OLE 복합문서)를 열 수 없다.",
            "설치:  pip3 install olefile",
            "설치가 막힌 환경이면 대체 경로 둘 중 하나를 쓴다.",
            "  (1) `python3 ncic_fetch.py fetch <번호> --ext pdf`로 PDF만 받아 사람이 읽고,",
            "      성취기준·성취수준 문구를 0단계 입력으로 직접 넘긴다(standards.md R1-1).",
            "  (2) 한글/한컴오피스에서 .hwp를 열어 '다른 이름으로 저장 → 텍스트 문서(.txt)'로 저장한 뒤",
            "      `python3 ncic_fetch.py find <그 .txt> --find \"[9수04-18]\"`로 검색한다.",
            "      (.txt 경로는 표 구조를 잃으므로 병합된 수준 칸은 사람이 원문과 대조해야 한다.)",
        )


# ── 게시글 번호 표 ──────────────────────────────────────────────────────────
def load_articles():
    """standards.md §1.1에서 게시글 번호 표를 읽는다. 못 읽으면 내장 표로 되돌린다."""
    try:
        with io.open(STANDARDS_MD, encoding="utf-8") as f:
            text = f.read()
    except OSError as ex:
        say("[알림] %s 를 읽지 못해 내장 게시글 번호 표를 쓴다 (%s)." % (STANDARDS_MD, ex))
        return dict(FALLBACK_ARTICLES), "내장"
    table = {}
    for m in re.finditer(r"(중|고)(2015|2022)\s*(?:→|->)\s*(\d+)", text):
        table[m.group(1) + m.group(2)] = int(m.group(3))
    if len(table) < 4:
        say("[알림] standards.md §1.1에서 게시글 번호 표를 4개 다 찾지 못해(%d개) 내장 표를 쓴다."
            % len(table))
        say("       standards.md §1.1의 `(중2022 → 772, 고2022 → 780, 중2015 → 735, 고2015 → 753)`"
            " 표기가 바뀌었는지 확인하라.")
        return dict(FALLBACK_ARTICLES), "내장"
    return table, STANDARDS_MD


def resolve_article(token, table):
    """'735' 또는 '중2015' 같은 별칭을 게시글 번호로 바꾼다."""
    token = str(token).strip()
    if token.isdigit():
        return int(token)
    key = token.replace(" ", "")
    if key in table:
        return table[key]
    die(EXIT_USAGE,
        "게시글 번호를 알 수 없다: %r" % token,
        "숫자를 주거나 별칭을 쓴다: " + ", ".join("%s=%d" % (k, v) for k, v in sorted(table.items())))


# ── 네트워크 ────────────────────────────────────────────────────────────────
def http_get(url, timeout, insecure=False, referer=None):
    headers = {"User-Agent": UA, "Accept-Language": "ko,en;q=0.8"}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    ctx = None
    if insecure:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            if resp.status != 200:
                die(EXIT_NETWORK,
                    "NCIC가 HTTP %d로 응답했다: %s" % (resp.status, url))
            return resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as ex:
        die(EXIT_NETWORK,
            "NCIC가 HTTP %d로 응답했다: %s" % (ex.code, url),
            "게시글 번호가 맞는지, 사이트가 점검 중인지 확인하라.")
    except urllib.error.URLError as ex:
        die(EXIT_NETWORK,
            "NCIC에 접속하지 못했다: %s" % url,
            "원인: %s" % (ex.reason,),
            "망이 막혀 있으면 사람이 브라우저로 받은 .hwp를 주고",
            "  python3 ncic_fetch.py extract <그 파일.hwp> --find \"[9수04-18]\"",
            "로 이어서 쓸 수 있다.",
            "사설 인증서 때문이면 --insecure를 붙여 다시 시도한다(검증을 끄므로 신뢰망에서만).")
    except (ssl.SSLError, OSError) as ex:
        die(EXIT_NETWORK,
            "NCIC 접속 중 통신 오류: %s" % url,
            "원인: %s: %s" % (type(ex).__name__, ex))


# ── 게시글 페이지 파싱 ──────────────────────────────────────────────────────
ATTACH_RE = re.compile(
    r'<p class="tit">(?P<title>.*?)</p>.*?'
    r'href="(?P<href>/bbs/download\.do\?articleIdx=\d+&(?:amp;)?fileName=[^"]+)"',
    re.S)
TITLE_RE = re.compile(r'community-page-title">\s*<h3 class="tit">(.*?)</h3>', re.S)


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def article_page(idx, timeout, insecure):
    url = VIEW_URL.format(idx=idx)
    raw, _ = http_get(url, timeout, insecure)
    html = raw.decode("utf-8", "replace")
    subject = TITLE_RE.search(html)
    if not subject:
        die(EXIT_NO_ARTICLE,
            "게시글 %s이(가) 없다: %s" % (idx, url),
            "NCIC가 오류 화면을 돌려주었다(게시글 제목 영역이 없다).",
            "standards.md §1.1의 번호를 확인하라 — 중2022 772 / 고2022 780 / 중2015 735 / 고2015 753.")
    return url, strip_tags(subject.group(1)), html


def parse_attachments(idx, html):
    """게시글 HTML에서 첨부 목록을 긁는다. fileName 타임스탬프는 다운로드 링크에 그대로 들어 있다."""
    out = []
    for m in ATTACH_RE.finditer(html):
        href = m.group("href").replace("&amp;", "&")
        q = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
        name = (q.get("fileName") or [""])[0]
        if not name:
            continue
        art = (q.get("articleIdx") or [str(idx)])[0]
        title = strip_tags(m.group("title"))
        # "이름.hwp [hwp, 507KB]" 꼬리표를 떼어 낸다
        size_tag = ""
        mm = re.search(r"\s*\[([^\[\]]*)\]\s*$", title)
        if mm:
            size_tag = mm.group(1)
            title = title[:mm.start()].strip()
        ext = os.path.splitext(name)[1].lower().lstrip(".")
        out.append({
            "title": title,
            "file_name": name,
            "ext": ext,
            "size_tag": size_tag,
            "url": DOWNLOAD_URL.format(idx=art, name=name),
        })
    return out


def safe_name(idx, att):
    stem = att["title"] or att["file_name"]
    stem = os.path.splitext(os.path.basename(stem))[0]
    stem = re.sub(r"[\\/:*?\"<>|\r\n\t]", "_", stem)
    stem = re.sub(r"\s+", "_", stem).strip("._")
    stem = stem[:80] or att["file_name"].split(".")[0]
    return "ncic%s_%s.%s" % (idx, stem, att["ext"] or "bin")


# ── HWP 레코드 ──────────────────────────────────────────────────────────────
TAG_PARA_HEADER = 66
TAG_PARA_TEXT = 67
TAG_LIST_HEADER = 72
TAG_TABLE = 77

# HWP 제어 문자: 8 wchar를 차지하는 것과 1 wchar를 차지하는 것
CTRL_8WCHAR = {1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23}


def decode_para(body):
    """HWPTAG_PARA_TEXT 데이터 → 문단 텍스트. 확장/인라인 제어문자를 폭만큼 건너뛴다.

    제어문자를 한 글자씩 지우면 8 wchar 제어의 나머지 6 wchar가 한자 쓰레기
    (예: 氠瑢)로 남는다. 폭을 지켜야 원문만 남는다.
    """
    s = body.decode("utf-16-le", "replace")
    out = []
    i = 0
    n = len(s)
    while i < n:
        c = ord(s[i])
        if c in CTRL_8WCHAR:
            if c == 9:
                out.append("\t")
            i += 8
        elif c < 32:
            if c == 10:
                out.append("\n")
            i += 1
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def read_records(path):
    """.hwp → [(tag, level, body), ...]  (BodyText/Section* 순서대로)"""
    olefile = require_olefile()
    if not os.path.exists(path):
        die(EXIT_USAGE, "파일이 없다: %s" % path)
    try:
        if not olefile.isOleFile(path):
            die(EXIT_HWP_PARSE,
                "OLE 복합문서가 아니다: %s" % path,
                "HWP 5.x(.hwp)만 읽는다. .hwpx(zip)나 .pdf는 이 명령의 대상이 아니다.",
                "PDF만 받았다면 사람이 읽고 문구를 0단계 입력으로 넘긴다(standards.md R1-1).")
        ole = olefile.OleFileIO(path)
    except OSError as ex:
        die(EXIT_HWP_PARSE, "파일을 열지 못했다: %s" % path, "원인: %s" % ex)

    try:
        header = ole.openstream("FileHeader").read()
    except OSError:
        die(EXIT_HWP_PARSE,
            "FileHeader 스트림이 없다: %s" % path,
            "HWP 5.x 파일이 아니거나 내려받기가 잘렸다. 파일 크기를 확인하고 다시 받아라.")
    if len(header) < 40:
        die(EXIT_HWP_PARSE, "FileHeader가 %d바이트뿐이다: %s" % (len(header), path))
    props = struct.unpack("<I", header[36:40])[0]
    compressed = bool(props & 0x01)
    encrypted = bool(props & 0x02)
    distributed = bool(props & 0x04)
    if encrypted:
        die(EXIT_HWP_PARSE,
            "암호가 걸린 HWP다: %s" % path,
            "한글에서 암호를 풀어 저장한 뒤 다시 시도하라.")
    if distributed:
        say("[알림] 배포용 문서 플래그가 켜져 있다. BodyText가 따로 암호화되어 추출이 실패할 수 있다.")

    names = ["/".join(p) for p in ole.listdir() if p and p[0] == "BodyText"]
    if not names:
        die(EXIT_HWP_PARSE,
            "BodyText 스트림이 없다: %s" % path,
            "본문이 없는 파일이거나 HWP 5.x가 아니다.")

    def secnum(name):
        m = re.search(r"(\d+)$", name)
        return int(m.group(1)) if m else 0

    records = []
    for name in sorted(names, key=secnum):
        data = ole.openstream(name).read()
        if compressed:
            try:
                data = zlib_decompress(data)
            except Exception as ex:
                die(EXIT_HWP_PARSE,
                    "%s 스트림의 압축을 풀지 못했다: %s" % (name, path),
                    "원인: %s: %s" % (type(ex).__name__, ex),
                    "FileHeader는 압축(플래그 0x%X)이라고 말한다. 파일이 손상됐을 수 있다." % props)
        pos, n = 0, len(data)
        while pos + 4 <= n:
            (h,) = struct.unpack("<I", data[pos:pos + 4])
            pos += 4
            tag = h & 0x3FF
            level = (h >> 10) & 0x3FF
            size = (h >> 20) & 0xFFF
            if size == 0xFFF:
                if pos + 4 > n:
                    break
                (size,) = struct.unpack("<I", data[pos:pos + 4])
                pos += 4
            body = data[pos:pos + size]
            if len(body) < size:
                say("[알림] %s 스트림이 레코드 중간에서 끊겼다(tag %d, %d/%d바이트). 거기까지만 읽는다."
                    % (name, tag, len(body), size))
                records.append((tag, level, body))
                break
            pos += size
            records.append((tag, level, body))
    if not records:
        die(EXIT_HWP_PARSE, "레코드를 하나도 읽지 못했다: %s" % path)
    return records


def zlib_decompress(data):
    import zlib
    return zlib.decompress(data, -15)


def records_to_text(records):
    """문단 텍스트를 읽은 순서대로 이어 붙인다(사람이 읽는 .txt)."""
    return "\n".join(decode_para(b) for (t, _l, b) in records if t == TAG_PARA_TEXT)


def records_to_tables(records):
    """표를 (row, col, rowspan, colspan, text) 칸 목록으로 복원한다.

    tag 77(HWPTAG_TABLE)이 표를 열고, **같은 level의** tag 72가 그 표의 칸이다.
    칸 머리 8바이트 뒤에 col/row/colSpan/rowSpan(UINT16 ×4)이 온다.
    칸의 문단은 그 다음 level의 tag 67이다.
    """
    tables = []
    open_tables = {}     # level -> table dict
    cur_cell = None
    cur_level = None
    for tag, level, body in records:
        if tag == TAG_TABLE:
            if len(body) >= 8:
                rows, cols = struct.unpack("<HH", body[4:8])
            else:
                rows = cols = 0
            tbl = {"rows": rows, "cols": cols, "cells": []}
            tables.append(tbl)
            for lv in [k for k in open_tables if k > level]:
                del open_tables[lv]
            open_tables[level] = tbl
            cur_cell, cur_level = None, None
            continue
        if tag == TAG_LIST_HEADER:
            tbl = open_tables.get(level)
            cur_cell, cur_level = None, None
            if tbl is not None and len(body) >= 16:
                col, row, cspan, rspan = struct.unpack("<HHHH", body[8:16])
                if row < 4096 and col < 512 and 1 <= rspan <= 512 and 1 <= cspan <= 512:
                    cur_cell = {"row": row, "col": col,
                                "rowspan": rspan, "colspan": cspan, "paras": []}
                    tbl["cells"].append(cur_cell)
                    cur_level = level + 1
            continue
        if tag == TAG_PARA_TEXT and cur_cell is not None and level == cur_level:
            cur_cell["paras"].append(decode_para(body))
            continue
        if tag == TAG_PARA_HEADER and cur_cell is not None and level != cur_level - 1:
            # 칸을 벗어나 본문(또는 다른 깊이)으로 돌아왔다. 칸 문맥을 닫는다.
            cur_cell, cur_level = None, None
            continue
    for tbl in tables:
        for c in tbl["cells"]:
            c["text"] = "\n".join(c["paras"]).strip()
    return tables


# ── 성취기준 찾기 ───────────────────────────────────────────────────────────
def norm_code(code):
    code = code.strip()
    if not code.startswith("["):
        code = "[" + code
    if not code.endswith("]"):
        code = code + "]"
    return code


def scheme_of(labels):
    if any(l in LV_2015 for l in labels):
        return "2015-3"
    if any(l in LV_2022 for l in labels):
        return "2022-5"
    return "미판정"


SCHEME_NOTE = {
    "2015-3": "2015 개정 평가기준 — 상·중·하 3단계. "
              "서식의 성취수준란이 A~E 5칸이므로 그대로 넣을 수 없다. "
              "standards.md §1.6(적용 교육과정 판정)으로 이 자료가 맞는지 확인하고, "
              "§1.7(3단계 자료를 5칸 서식에 옮긴다)대로 배치한다. "
              "근거를 못 채우는 칸은 R1-5대로 비운다.",
    "2022-5": "2022 개정 성취수준 — A~E 5단계. 서식의 성취수준란 5칸과 그대로 맞는다.",
    "미판정": "수준 라벨(상·중·하 / A~E)을 찾지 못했다. 원문 표 구조가 다르다. "
              "사람이 원문을 확인해야 한다.",
}


def _split_sub_standard(text):
    """'[평가준거 성취기준 ①]\\n방정식과 …' → ('[평가준거 성취기준 ①]', '방정식과 …')"""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return "", ""
    m = re.match(r"^(\[평가준거[^\]]*\])\s*(.*)$", lines[0])
    if m:
        rest = [m.group(2)] + lines[1:]
        return m.group(1), " ".join(x for x in rest if x).strip()
    return lines[0], " ".join(lines[1:]).strip()


def _close_groups(groups, warnings, where):
    """그룹마다 병합을 표시하고 수준 라벨이 온전한지 본다."""
    scheme = "미판정"
    for g in groups:
        bykey = {}
        for lv in g["levels"]:
            bykey.setdefault(lv["_key"], []).append(lv["label"])
        for lv in g["levels"]:
            lv["merged"] = bykey.get(lv["_key"], [lv["label"]])
            lv.pop("_key", None)
        labels = [lv["label"] for lv in g["levels"]]
        sch = scheme_of(labels)
        if scheme == "미판정":
            scheme = sch
        elif sch != "미판정" and sch != scheme:
            warnings.append("한 성취기준 안에서 수준체계가 섞여 있다(%s / %s). 원문을 확인하라."
                            % (scheme, sch))
        expect = LV_2015 if sch == "2015-3" else (LV_2022 if sch == "2022-5" else [])
        tail = (" — %s" % g["sub_standard"]) if g["sub_standard"] else ""
        if expect and labels != expect:
            warnings.append("수준 라벨이 %s여야 하는데 원문에서 읽은 것은 %s다%s. 원문과 대조하라."
                            % ("·".join(expect), "·".join(labels) or "(없음)", tail))
        for lv in g["levels"]:
            if not lv["statement"]:
                warnings.append("수준 %s의 진술 칸이 비었다(%s)%s. R1-5대로 비워 두고 원문을 확인하라."
                                % (lv["label"], where, tail))
    return scheme


def find_in_tables(tables, code):
    """표 구조로 코드 블록을 찾는다. 세로 병합을 원문 그대로 복원한다(R1-10).

    2015 자료는 한 성취기준 아래에 [평가준거 성취기준 ①/②]가 있고 그 각각에
    상·중·하가 따로 붙는다. 그 묶음을 groups로 갈라서 돌려준다.
    """
    results = []
    for ti, tbl in enumerate(tables):
        for cell in tbl["cells"]:
            if code not in cell["text"]:
                continue
            r0, rs, c0 = cell["row"], cell["rowspan"], cell["col"]
            lines = [l.strip() for l in cell["text"].split("\n") if l.strip()]
            head = " ".join(lines)
            stmt = head.split(code, 1)[1].strip() if code in head else ""
            stmt = stmt.lstrip(":： ").strip()

            warnings = []
            groups = []
            by_sub = {}
            for r in range(r0, r0 + rs):
                row_cells = sorted(
                    [c for c in tbl["cells"]
                     if c["col"] > c0 and c["row"] <= r < c["row"] + c["rowspan"]],
                    key=lambda c: c["col"])
                sub_key = None
                sub_head = sub_body = ""
                label = text = key = None
                for c in row_cells:
                    t = c["text"].strip()
                    if label is None and SUB_STD_RE.match(t):
                        sub_key = (c["row"], c["col"])
                        sub_head, sub_body = _split_sub_standard(c["text"])
                        continue
                    if label is None and t in LV_ALL:
                        label = t
                        continue
                    if label is not None and text is None:
                        text = t
                        key = (c["row"], c["col"])
                if label is None:
                    continue
                if sub_key not in by_sub:
                    g = {"sub_standard": sub_head or None,
                         "sub_standard_text": sub_body or None,
                         "levels": []}
                    by_sub[sub_key] = g
                    groups.append(g)
                by_sub[sub_key]["levels"].append(
                    {"label": label, "statement": text or "", "_key": key, "row": r})

            scheme = _close_groups(groups, warnings, "표 %d, 행 %d~%d" % (ti, r0, r0 + rs - 1))
            flat = [lv for g in groups for lv in g["levels"]]
            if not flat:
                warnings.append("이 칸에는 수준 진술이 붙어 있지 않다(목차·머리말·부록일 수 있다). "
                                "성취수준 표에서 다시 확인하라.")
            results.append({
                "table": ti, "row": r0, "col": c0, "rowspan": rs,
                "curriculum_standard": stmt,
                "cell_text": cell["text"],
                "level_scheme": scheme,
                "groups": groups,
                "levels": flat,
                "warnings": warnings,
                "method": "표 구조(HWPTAG_TABLE/LIST_HEADER)",
            })
    # 수준을 실제로 찾은 블록을 앞으로
    results.sort(key=lambda r: (0 if r["levels"] else 1, r["table"], r["row"]))
    return results


STRUCT_LINE = re.compile(r"^(?:\d+\)|\(\d+\)|[가-힣]\.|[ⅠⅡⅢⅣⅤ]+\.|\d+\.)\s")
HEAD_LINES = {"교육과정 성취기준", "평가기준", "성취수준", "설 명", "설명", "영역",
              "영역별 성취수준", "내용 영역", "성취기준별 성취수준"}


def find_in_text(text, code):
    """표 구조가 없을 때(.txt 입력) 줄 단위로 찾는 되돌림 경로."""
    lines = text.split("\n")
    results = []
    for i, line in enumerate(lines):
        if code not in line:
            continue
        head = line.strip()
        tail = head.split(code, 1)[1].strip()
        stmt_parts = [tail] if tail else []
        cur = {"sub_standard": None, "sub_standard_text": None, "levels": []}
        groups = [cur]
        pending = []
        seq = 0
        j = i + 1
        while j < len(lines):
            s = lines[j].strip()
            if not s:
                j += 1
                continue
            if CODE_RE.search(s) or s in HEAD_LINES or STRUCT_LINE.match(s) \
                    or "영역별 성취수준" in s:
                break
            if SUB_STD_RE.match(s):
                sub_head, sub_body = _split_sub_standard(s)
                cur = {"sub_standard": sub_head, "sub_standard_text": sub_body or None,
                       "levels": []}
                groups.append(cur)
                pending = []
                j += 1
                continue
            if s in LV_ALL:
                pending.append(s)
                j += 1
                continue
            if pending:
                seq += 1
                for p in pending:
                    cur["levels"].append({"label": p, "statement": s, "_key": seq})
                pending = []
            elif cur["levels"]:
                prev = cur["levels"][-1]["statement"]
                if prev.rstrip().endswith((".", "다", "음", "임", "함")):
                    break
                for lv in cur["levels"]:
                    if lv["statement"] == prev:
                        lv["statement"] = prev + " " + s
            elif not cur["sub_standard"]:
                stmt_parts.append(s)
            else:
                cur["sub_standard_text"] = ((cur["sub_standard_text"] or "") + " " + s).strip()
            j += 1
        for p in pending:
            seq += 1
            cur["levels"].append({"label": p, "statement": "", "_key": seq})
        groups = [g for g in groups if g["levels"]] or groups[:1]
        warnings = ["표 구조 없이 줄 단위로 읽었다. 세로 병합된 수준 칸이 어긋날 수 있으니 "
                    "원문(.hwp/PDF)과 대조하라."]
        sch = _close_groups(groups, warnings, "줄 %d" % i)
        flat = [lv for g in groups for lv in g["levels"]]
        results.append({
            "table": None, "row": i, "col": None, "rowspan": None,
            "curriculum_standard": " ".join(stmt_parts).strip(),
            "cell_text": line.strip(),
            "level_scheme": sch,
            "groups": groups,
            "levels": flat,
            "warnings": warnings,
            "method": "줄 단위(되돌림 경로)",
        })
    results.sort(key=lambda r: (0 if r["levels"] else 1, r["row"]))
    return results


def find_sub_standards(text, code):
    """2015 자료의 [평가준거 성취기준 ①/②] 하위 블록을 알려 준다(있을 때만)."""
    lines = text.split("\n")
    out = []
    for i, line in enumerate(lines):
        if code not in line:
            continue
        j = i + 1
        while j < len(lines) and j < i + 60:
            s = lines[j].strip()
            if CODE_RE.search(s):
                break
            if SUB_STD_RE.match(s):
                out.append(s)
            j += 1
        break
    return out


# ── 출력 ────────────────────────────────────────────────────────────────────
def print_find(code, source, hits, sub_standards):
    print("")
    print("── 성취기준 %s ──────────────────────────────" % code)
    print("자료      : %s" % source)
    if not hits:
        print("결과      : 이 자료에서 찾지 못했다.")
        return
    for k, h in enumerate(hits, 1):
        if len(hits) > 1:
            print("")
            print("[일치 %d/%d]  읽은 방법: %s" % (k, len(hits), h["method"]))
        else:
            print("읽은 방법 : %s" % h["method"])
        print("수준체계  : %s" % h["level_scheme"])
        print("            %s" % SCHEME_NOTE.get(h["level_scheme"], ""))
        print("성취기준  : %s" % (h["curriculum_standard"] or "(코드와 같은 칸에 문구가 없다)"))
        groups = [g for g in h.get("groups", []) if g["levels"]]
        if not groups:
            print("수준 진술 : (없음)")
        for g in groups:
            if g["sub_standard"]:
                print("")
                print("  %s %s" % (g["sub_standard"], g["sub_standard_text"] or ""))
                print("  ※ 2015 자료는 평가준거 성취기준마다 상·중·하가 따로 붙는다. "
                      "어느 평가준거를 채점 대상으로 삼을지 R1-3대로 사용자에게 확정받는다.")
            else:
                print("수준 진술 :")
            shown = set()
            for lv in g["levels"]:
                tag = "·".join(lv["merged"])
                if len(lv["merged"]) > 1:
                    if tag in shown:
                        continue
                    shown.add(tag)
                    print("  %-5s %s" % (tag, lv["statement"]))
                    print("        ※ 원문에서 %s가 한 칸으로 병합되어 있다. 병합 그대로 옮긴다(R1-10)."
                          % tag)
                else:
                    print("  %-5s %s" % (lv["label"], lv["statement"]))
        if sub_standards and not any(g["sub_standard"] for g in groups):
            print("평가준거  : %s" % " / ".join(sub_standards))
            print("            ※ 원문에 평가준거 성취기준이 있는데 수준 묶음에 붙이지 못했다.")
            print("               위 진술이 어느 평가준거의 것인지 원문에서 확인하라.")
        if h["warnings"]:
            print("경고      :")
            for w in h["warnings"]:
                print("  · %s" % w)
        else:
            print("경고      : 없음")
    print("")
    print("R1-4 — 위 문구를 문서에 넣을 때 줄이거나 다듬지 않는다. 글자 단위로 그대로 옮긴다.")
    print("R1-5 — 여기서 확보하지 못한 칸은 비운다. 그럴듯한 문장을 지어 넣지 않는다.")


# ── 명령 ────────────────────────────────────────────────────────────────────
def cmd_list(args, table):
    idx = resolve_article(args.article, table)
    url, subject, html = article_page(idx, args.timeout, args.insecure)
    atts = parse_attachments(idx, html)
    if not atts:
        die(EXIT_NO_ATTACH,
            "게시글 %d에 첨부가 없다: %s" % (idx, url),
            "제목: %s" % subject)
    if args.json:
        print(json.dumps({"article": idx, "url": url, "subject": subject,
                          "attachments": atts}, ensure_ascii=False, indent=2))
        return EXIT_OK
    print("게시글 %d — %s" % (idx, subject))
    print("  %s" % url)
    for i, a in enumerate(atts, 1):
        print("  [%d] %s  (%s)" % (i, a["title"], a["size_tag"] or a["ext"]))
        print("      %s" % a["url"])
    return EXIT_OK


def do_fetch(idx, args):
    url, subject, html = article_page(idx, args.timeout, args.insecure)
    atts = parse_attachments(idx, html)
    if not atts:
        die(EXIT_NO_ATTACH,
            "게시글 %d에 첨부가 없다: %s" % (idx, url),
            "제목: %s" % subject)
    want = [a for a in atts if args.ext == "all" or a["ext"] == args.ext]
    if args.index:
        pick = []
        for n in args.index:
            if not (1 <= n <= len(atts)):
                die(EXIT_USAGE, "--index %d 는 첨부 범위(1~%d) 밖이다." % (n, len(atts)))
            pick.append(atts[n - 1])
        want = pick
    if not want:
        die(EXIT_NO_ATTACH,
            "게시글 %d에 .%s 첨부가 없다." % (idx, args.ext),
            "있는 첨부: " + " / ".join("%s(.%s)" % (a["title"], a["ext"]) for a in atts),
            "`--ext all` 또는 `--ext pdf`로 다시 시도하라.")
    os.makedirs(args.out, exist_ok=True)
    saved = []
    for a in want:
        dst = os.path.join(args.out, safe_name(idx, a))
        if os.path.exists(dst) and not args.force:
            say("[재사용] 이미 있다: %s  (--force로 다시 받는다)" % dst)
        else:
            say("[받는 중] %s" % a["url"])
            data, headers = http_get(a["url"], args.timeout, args.insecure, referer=url)
            if len(data) < 1024:
                die(EXIT_NETWORK,
                    "첨부를 받았으나 %d바이트뿐이다: %s" % (len(data), a["url"]),
                    "로그인 요구나 오류 페이지일 수 있다. 브라우저에서 직접 받아 extract를 쓰라.")
            with open(dst, "wb") as f:
                f.write(data)
            say("[저장] %s  (%d바이트)" % (dst, len(data)))
        saved.append((dst, a))
    return url, subject, saved


def extract_to_txt(hwp_path, out_dir, write_cells=False):
    records = read_records(hwp_path)
    text = records_to_text(records)
    tables = records_to_tables(records)
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(hwp_path))[0]
    txt_path = os.path.join(out_dir, stem + ".txt")
    with io.open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)
    n_cells = sum(len(t["cells"]) for t in tables)
    say("[추출] %s  (문단 %d개, %d자, 표 %d개 / 칸 %d개)"
        % (txt_path, text.count("\n") + 1, len(text), len(tables), n_cells))
    if len(text.strip()) < 200:
        die(EXIT_HWP_PARSE,
            "본문에서 %d자만 나왔다: %s" % (len(text.strip()), hwp_path),
            "배포용 문서이거나 본문이 그림뿐일 수 있다. PDF 첨부를 받아 사람이 읽어라.")
    if write_cells:
        cells_path = os.path.join(out_dir, stem + ".cells.tsv")
        with io.open(cells_path, "w", encoding="utf-8") as f:
            f.write("table\trow\tcol\trowspan\tcolspan\ttext\n")
            for ti, t in enumerate(tables):
                for c in sorted(t["cells"], key=lambda c: (c["row"], c["col"])):
                    f.write("%d\t%d\t%d\t%d\t%d\t%s\n"
                            % (ti, c["row"], c["col"], c["rowspan"], c["colspan"],
                               c["text"].replace("\t", " ").replace("\n", " ⏎ ")))
        say("[추출] %s  (표 칸 좌표 — 병합 확인용)" % cells_path)
    return text, tables, txt_path


def run_find(code, text, tables, source, args):
    code = norm_code(code)
    hits = find_in_tables(tables, code) if tables else []
    if not hits:
        hits = find_in_text(text, code)
    subs = find_sub_standards(text, code)
    if args.json:
        print(json.dumps({
            "code": code,
            "source": source,
            "found": bool(hits),
            "level_scheme": hits[0]["level_scheme"] if hits else None,
            "matches": hits,
            "sub_standards": subs,
        }, ensure_ascii=False, indent=2))
    else:
        print_find(code, source, hits, subs)
    if not hits:
        die(EXIT_NOT_FOUND,
            "성취기준 코드 %s를 이 자료에서 찾지 못했다." % code,
            "출처: %s" % source,
            "코드 표기를 확인하라(예: [9수04-18]). 학교급·개정 연도가 맞는 게시글인지도 본다 —",
            "중2022 772 / 고2022 780 / 중2015 735 / 고2015 753.")
    return EXIT_OK


def cmd_fetch(args, table):
    idx = resolve_article(args.article, table)
    url, subject, saved = do_fetch(idx, args)
    print("게시글 %d — %s" % (idx, subject))
    print("  %s" % url)
    for dst, a in saved:
        print("  받음: %s" % dst)
    if args.no_extract:
        return EXIT_OK
    text = tables = None
    src = None
    for dst, a in saved:
        if a["ext"] != "hwp":
            continue
        text, tables, txt_path = extract_to_txt(dst, args.out, args.cells)
        src = "%s (게시글 %d)" % (os.path.basename(dst), idx)
        print("  추출: %s" % txt_path)
    if args.find:
        if text is None:
            die(EXIT_USAGE,
                "--find는 .hwp 첨부가 있어야 쓸 수 있다.",
                "`--ext hwp`(기본)로 받았는지 확인하라. PDF만 있으면 사람이 읽어야 한다.")
        return run_find(args.find, text, tables, src, args)
    return EXIT_OK


def cmd_extract(args, table):
    text, tables, txt_path = extract_to_txt(args.path, args.out, args.cells)
    print("추출: %s" % txt_path)
    if args.find:
        return run_find(args.find, text, tables, os.path.basename(args.path), args)
    return EXIT_OK


def cmd_find(args, table):
    target = args.target
    if target.isdigit() or target.replace(" ", "") in table:
        idx = resolve_article(target, table)
        args.ext = "hwp"
        args.no_extract = False
        url, subject, saved = do_fetch(idx, args)
        hwp = [d for d, a in saved if a["ext"] == "hwp"]
        if not hwp:
            die(EXIT_NO_ATTACH, "게시글 %d에서 .hwp를 받지 못했다." % idx)
        text, tables, _ = extract_to_txt(hwp[0], args.out, args.cells)
        src = "%s (게시글 %d)" % (os.path.basename(hwp[0]), idx)
        return run_find(args.find, text, tables, src, args)
    if not os.path.exists(target):
        die(EXIT_USAGE,
            "게시글 번호도 아니고 있는 파일도 아니다: %r" % target,
            "번호(735) · 별칭(중2015) · .hwp 경로 · .txt 경로 중 하나를 준다.")
    if target.lower().endswith(".txt"):
        with io.open(target, encoding="utf-8") as f:
            text = f.read()
        say("[알림] .txt는 표 구조가 없어 줄 단위로 읽는다. 병합된 수준 칸은 원문과 대조하라.")
        return run_find(args.find, text, None, os.path.basename(target), args)
    records = read_records(target)
    text = records_to_text(records)
    tables = records_to_tables(records)
    return run_find(args.find, text, tables, os.path.basename(target), args)


GLOBAL_DEFAULTS = {
    "out": None,          # main()에서 os.getcwd()로 채운다
    "timeout": 60.0,
    "insecure": False,
    "json": False,
    "cells": False,
    "force": False,
}


def add_global_options(p):
    """공통 옵션. 기본값을 SUPPRESS로 두어 하위 명령이 상위 값을 덮어쓰지 않게 한다.

    argparse의 하위 파서는 자기 기본값으로 이미 정해진 값을 덮어쓴다. 그래서
    `--json`을 하위 명령 앞에 써도 뒤에 써도 같게 하려면 기본값을 두지 말고
    파싱이 끝난 뒤 GLOBAL_DEFAULTS로 채워야 한다.
    """
    p.add_argument("-o", "--out", default=argparse.SUPPRESS,
                   help="산출물 폴더 (기본: 현재 작업 폴더)")
    p.add_argument("--timeout", type=float, default=argparse.SUPPRESS,
                   help="통신 제한 시간(초, 기본 60)")
    p.add_argument("--insecure", action="store_true", default=argparse.SUPPRESS,
                   help="TLS 인증서 검증을 끈다(사설 인증서 환경에서만)")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                   help="기계가 읽는 JSON으로 출력")
    p.add_argument("--cells", action="store_true", default=argparse.SUPPRESS,
                   help="표 칸 좌표를 <이름>.cells.tsv로 함께 저장(병합 확인용)")
    p.add_argument("--force", action="store_true", default=argparse.SUPPRESS,
                   help="이미 받은 파일도 다시 받는다")
    return p


def build_parser(table):
    alias = ", ".join("%s=%d" % (k, v) for k, v in sorted(table.items()))
    p = argparse.ArgumentParser(
        prog="ncic_fetch.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="NCIC 공시 자료(성취기준·성취수준)를 내려받아 본문을 뽑고 성취기준을 찾는다.",
        epilog="""
게시글 별칭: %s   (standards.md §1.1)

보기
  python3 ncic_fetch.py list 735
  python3 ncic_fetch.py fetch 중2015 --find "[9수04-18]"
  python3 ncic_fetch.py fetch 772 --ext all
  python3 ncic_fetch.py extract ./ncic735_....hwp --find "[9수04-18]"
  python3 ncic_fetch.py find 772 --find "[9수03-13]" --json

종료 코드
  0 성공 / 2 사용법 오류 / 3 olefile 없음 / 4 네트워크 실패 /
  5 게시글 없음 / 6 첨부 없음 / 7 HWP 파싱 실패 / 8 성취기준 코드 못 찾음
""" % alias)
    add_global_options(p)

    sub = p.add_subparsers(dest="cmd")

    q = add_global_options(sub.add_parser("list", help="첨부 목록만 보여 준다"))
    q.add_argument("article", help="게시글 번호 또는 별칭")

    q = add_global_options(sub.add_parser("fetch", help="첨부를 내려받고 .hwp는 .txt로 추출한다"))
    q.add_argument("article", help="게시글 번호 또는 별칭")
    q.add_argument("--ext", default="hwp", choices=["hwp", "pdf", "all"],
                   help="내려받을 확장자 (기본 hwp)")
    q.add_argument("--index", type=int, nargs="+", help="첨부 번호로 직접 고른다(list 참고)")
    q.add_argument("--no-extract", action="store_true", help="내려받기만 한다")
    q.add_argument("--find", help='성취기준 코드. 예: "[9수04-18]"')

    q = add_global_options(sub.add_parser("extract", help="이미 받은 .hwp에서 본문을 뽑는다"))
    q.add_argument("path", help=".hwp 경로")
    q.add_argument("--find", help='성취기준 코드. 예: "[9수04-18]"')

    q = add_global_options(
        sub.add_parser("find", help="성취기준 코드를 찾아 수준 진술을 구조화해 출력한다"))
    q.add_argument("target", help="게시글 번호·별칭 또는 .hwp/.txt 경로")
    q.add_argument("--find", required=True, help='성취기준 코드. 예: "[9수04-18]"')
    return p


def main(argv):
    table, src = load_articles()
    parser = build_parser(table)
    args = parser.parse_args(argv)
    if not args.cmd:
        parser.print_help()
        return EXIT_USAGE
    for name, default in GLOBAL_DEFAULTS.items():
        if not hasattr(args, name):
            setattr(args, name, default)
    for name in ("ext", "index", "no_extract", "find"):
        if not hasattr(args, name):
            setattr(args, name, False if name == "no_extract" else None)
    if args.insecure:
        say("[경고] --insecure: TLS 인증서 검증을 껐다. 신뢰할 수 있는 망에서만 쓴다.")
    args.out = os.path.abspath(args.out or os.getcwd())
    if args.cmd == "list":
        return cmd_list(args, table)
    if args.cmd == "fetch":
        return cmd_fetch(args, table)
    if args.cmd == "extract":
        return cmd_extract(args, table)
    if args.cmd == "find":
        return cmd_find(args, table)
    parser.print_help()
    return EXIT_USAGE


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        say("[중단] 사용자가 멈췄다.")
        sys.exit(130)
