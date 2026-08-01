"""중첩 표를 인식하는 HWPX 구조·레이아웃 검증기.

사용:
    python3 check_tpl2.py <산출.hwpx> <content.json> [--draft]

    기본은 **최종 모드**다. 콘텐츠 JSON에 남은 `[그림 N]` 자리표시 중 `_figs`에
    매핑되지 않은 것이 하나라도 있으면 오류로 세어 FAIL한다.
    `--draft`를 주면 **초안 모드**로, 같은 상황을 경고로만 센다.
    플래그는 두 위치 인자 뒤에만 온다.
"""
import os
import zipfile, re, sys, json, unicodedata
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import img_embed as IE                                  # noqa: E402  PNG 구조 검증기를 공유한다

USAGE = "사용법: python3 check_tpl2.py <산출.hwpx> <content.json> [--draft]"

# 위치 인자 자리에 플래그가 오면 산출물·콘텐츠 경로를 조용히 잘못 잡는다. 먼저 막는다.
for _i, _a in enumerate(sys.argv[1:3], 1):
    if _a.startswith('-'):
        sys.exit(f"{USAGE}\n  위치 인자 {_i}번에 플래그가 왔다: {_a}")

# 초안 모드. 최종 모드(기본값)에서는 미매핑 그림 자리표시가 오류다.
DRAFT_MODE = "--draft" in sys.argv[3:]
for _a in sys.argv[3:]:
    if _a != "--draft":
        sys.exit(f"{USAGE}\n  모르는 인자: {_a}")

def _fail_hook(tp, val, tb):
    # 예외로 중단돼도 PASS/FAIL footer 계약을 지킨다(C-6). excepthook 뒤 파이썬은 코드 1로 종료한다.
    import traceback
    traceback.print_exception(tp, val, tb)
    print(f"\n{'='*60}\nFAIL — 예외로 중단: {tp.__name__}: {val}")
sys.excepthook = _fail_hook

OUT = sys.argv[1]
S = os.path.dirname(os.path.abspath(__file__))
z = zipfile.ZipFile(OUT)
xml = z.read('Contents/section0.xml').decode('utf-8')
hdr = z.read('Contents/header.xml').decode('utf-8')

errs = warns = 0
_draft_waivers = 0          # 초안 모드에서 눈감아 준 건수. 0이 아니면 최종 제출 불가다.


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
    res = []
    for o in [m.start() for m in re.finditer(r'<hp:tbl[ >]', s)]:
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


print("### 1. XML / ZIP")
for n in z.namelist():
    if n.endswith('.xml') or n.endswith('.hpf') or n.endswith('.rdf'):
        try:
            ET.fromstring(z.read(n))
        except Exception as ex:
            errs += 1
            print(f"  [ERR] {n}: {ex}")
info = z.infolist()
_bad_entry = z.testzip()
print(f"  엔트리 {len(info)}, 첫 엔트리 {info[0].filename} "
      f"method={info[0].compress_type}, testzip={_bad_entry}")
if _bad_entry is not None:
    errs += 1
    print(f"  [ERR] ZIP 손상 엔트리: {_bad_entry}")
if info[0].filename != 'mimetype' or info[0].compress_type != 0:
    errs += 1
    print("  [ERR] mimetype이 첫 엔트리(STORED)가 아님")

print("\n### 2. 표 격자 (깊이 인식)")
tbls = all_tbl(xml)
for ti, (a, b) in enumerate(tbls):
    t = xml[a:b]
    off = t.index('>') + 1
    inner = t[off:t.rindex('</hp:tbl>')]
    cells = spans(inner, 'hp:tc')
    rc = re.search(r'rowCnt="(\d+)" colCnt="(\d+)"', t[:off])
    exp = int(rc.group(1)) * int(rc.group(2))
    got = 0
    addrs = set()
    for ca, cb in cells:
        c = inner[ca:cb]
        # 겹치지 않는 최상위 중첩 표 범위만 제거한다(B-8).
        # all_tbl은 손자 범위까지 돌려주므로 깊이 3에서 부모 자신의 addr/span까지 잘린다.
        for na, nb in reversed(spans(c, 'hp:tbl')):
            c = c[:na] + c[nb:]
        sm = re.search(r'colSpan="(\d+)" rowSpan="(\d+)"/>', c)
        am = re.search(r'colAddr="(\d+)" rowAddr="(\d+)"/>', c)
        if sm:
            got += int(sm.group(1)) * int(sm.group(2))
        if am:
            key = am.groups()
            if key in addrs:
                errs += 1
                print(f"  [ERR] T{ti} cellAddr 중복 {key}")
            addrs.add(key)
    ok = 'OK' if got == exp else 'MISMATCH'
    if got != exp:
        errs += 1
    print(f"  T{ti}: 직속셀 {len(cells)}, span합 {got}, rowCnt×colCnt {exp} {ok}")

print("\n### 3. 스타일 참조")
for kind, pat in (('paraPr', r'paraPrIDRef="(\d+)"'), ('charPr', r'charPrIDRef="(\d+)"'),
                  ('borderFill', r'borderFillIDRef="(\d+)"')):
    defined = set(re.findall(r'<hh:%s id="(\d+)"' % kind, hdr))
    used = set(re.findall(pat, xml))
    miss = sorted(used - defined, key=int)
    if miss:
        errs += 1
    print(f"  미정의 {kind}: {miss}")

print("\n### 4. lineWrap / 겹침 위험")
squeeze_bad = 0
for a, b in tbls:
    t = xml[a:b]
    off = t.index('>') + 1
    inner = t[off:t.rindex('</hp:tbl>')]
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
                squeeze_bad += 1
if squeeze_bad:
    errs += 1
print(f"  SQUEEZE 칸 다중줄 문단: {squeeze_bad}건")


def w(ch, em):
    if unicodedata.combining(ch):
        return 0
    e = unicodedata.east_asian_width(ch)
    if e in ('W', 'F', 'A', 'N'):
        return em
    return em * 0.5 if ch == ' ' else em * 0.62


CH = {}
for m in re.finditer(r'<hh:charPr id="(\d+)"[^>]*>.*?</hh:charPr>', hdr, re.S):
    b2, cid = m.group(0), m.group(1)
    h = int(re.search(r'height="(\d+)"', b2).group(1))
    r = re.search(r'<hh:ratio hangul="(-?\d+)"', b2)
    sp = re.search(r'<hh:spacing hangul="(-?\d+)"', b2)
    CH[cid] = int(round(h * ((int(r.group(1)) if r else 100) + (int(sp.group(1)) if sp else 0)) / 100.0))

risk = 0
for pm in re.finditer(r'<hp:p [^>]*>((?:(?!<hp:p[ >]).)*?)</hp:p>', xml, re.S):
    body = pm.group(1)
    t = ''.join(re.findall(r'<hp:t>([^<]*)</hp:t>', body))
    segs = re.findall(r'<hp:lineseg ([^/]*)/>', body)
    cid = re.findall(r'charPrIDRef="(\d+)"', body)
    if not t or not segs or not cid:
        continue
    em = CH.get(cid[0], 1000)
    d0 = dict(re.findall(r'(\w+)="([^"]*)"', segs[0]))
    hz = int(d0['horzsize'])
    if hz == 0:
        continue
    # 서식 원본에서 물려받은 안내 문단 — 폭 초과 캐시가 원본 상태이며 HWP가 열 때 재배치한다.
    # 정확한 전체 문자열이 문서에서 1회만 나올 때에만 허용한다(B-5).
    _ALLOWED_RISK_EXACT = ("※ 평가 유형(지필평가, 수행평가 등)은 분반(교과)별 운영 방향에 따라 자율적으로 선정하여 작성",)
    if len(segs) == 1 and sum(w(c, em) for c in t) > hz:
        _joined_all = ''.join(re.findall(r'<hp:t>([^<]*)</hp:t>', xml))
        if t in _ALLOWED_RISK_EXACT and _joined_all.count(t) == 1:
            warns += 1
            print(f"  [WARN] 서식 원본 유래 폭 초과(허용): {t[:44]!r}")
        else:
            risk += 1
            print(f"  [RISK] 1줄 캐시인데 폭 초과: {t[:44]!r}")
    tps = [int(dict(re.findall(r'(\w+)="([^"]*)"', s))['textpos']) for s in segs]
    if tps != sorted(tps) or tps[0] != 0 or tps[-1] >= len(t) and len(t) > 0:
        errs += 1
        print(f"  [ERR] textpos 이상 {tps} len={len(t)} {t[:34]!r}")
if risk:
    errs += 1
print(f"  겹침 위험 문단: {risk}건")

print("\n### 5. 내용 보존")
try:
    content = json.load(open(sys.argv[2] if len(sys.argv) > 2 else S + "/content2.json", encoding='utf-8'))
    if isinstance(content.get('rubric_rows'), list):
        flat = []
        for r in content['rubric_rows']:
            for x in (r.get('item',''), r.get('elem',''), r.get('score',''), r.get('desc','')):
                flat += str(x).split('\n')
        content['rubric_rows'] = flat
    joined = ''.join(re.findall(r'<hp:t>([^<]*)</hp:t>', xml))
    joined = (joined.replace('&amp;', '&').replace('&lt;', '<')
              .replace('&gt;', '>').replace('&quot;', '"'))
    miss = []
    for k, v in content.items():
        if k.startswith('_') or isinstance(v, bool):
            continue
        for ln in ([v] if isinstance(v, str) else v):
            if isinstance(ln, dict):
                ln = ' '.join(str(x) for x in ln.values())
            if ln.strip() and ln not in joined:
                miss.append((k, ln[:50]))
    if miss:
        errs += 1
        for m2 in miss[:10]:
            print(f"  [ERR] 누락 {m2}")
    print(f"  누락 줄: {len(miss)}")
except FileNotFoundError:
    errs += 1
    print("  [ERR] 콘텐츠 JSON을 찾지 못함 — 내용 보존을 검사하지 못했다")

print(f"\n### 5.5 그림 게이트 ({'초안' if DRAFT_MODE else '최종'} 모드)")
try:
    _content_path = sys.argv[2] if len(sys.argv) > 2 else S + "/content2.json"
    _c = json.load(open(_content_path, encoding='utf-8'))
    _figs = _c.get('_figs') or {}
    if _figs:
        _base = os.path.dirname(os.path.abspath(_content_path))
        _sec_ids = set(re.findall(r'binaryItemIDRef="([^"]+)"', xml))
        _names = set(z.namelist())

        _ids = [str(v[0]) for v in _figs.values()]
        if len(_ids) != len(set(_ids)):
            errs += 1
            print("  [ERR] _figs의 BinData id가 중복됨")

        _hpf_root = ET.fromstring(z.read('Contents/content.hpf'))
        _hpf_items = {
            e.attrib.get('id'): e.attrib.get('href')
            for e in _hpf_root.iter()
            if e.tag.rsplit('}', 1)[-1] == 'item'
        }

        for _ph, (_fid, _rel) in _figs.items():
            _fid = str(_fid)
            _png = os.path.join(_base, _rel)

            try:
                IE.verified_png_path(_png)
            except ValueError as _ex:
                errs += 1
                print(f"  [ERR] 그림 원본 파일 없음/손상: {_rel}: {_ex}")

            if _fid not in _sec_ids:
                errs += 1
                print(f"  [ERR] 선언한 그림이 문서에 삽입되지 않음: {_ph} → {_fid}")

            _href = _hpf_items.get(_fid)
            if not _href:
                errs += 1
                print(f"  [ERR] 그림이 content.hpf에 등록되지 않음: {_fid}")
                continue

            if _href not in _names:
                errs += 1
                print(f"  [ERR] 등록된 그림 BinData가 ZIP에 없음: {_fid} → {_href}")
                continue

            try:
                IE.verified_png_bytes(z.read(_href), _href)
            except ValueError as _ex:
                errs += 1
                print(f"  [ERR] 삽입된 BinData가 정상 PNG가 아님: {_fid} → {_href}: {_ex}")

        _bin = [n for n in z.namelist() if n.startswith('BinData/')]
        print(f"  _figs 선언 {len(_figs)}건, 삽입·등록·PNG 확인, BinData {len(_bin)}개")

    # 콘텐츠 JSON에 남은 [그림 N] 자리표시 중 _figs에 매핑되지 않은 것.
    # 빌더는 자리표시로 **시작하는** 줄만 그림 문단으로 바꾸므로 같은 기준으로 센다.
    # _figs 자체가 없는 경우까지 포함해 검사한다(_figs 생략으로 게이트를 비우지 못하게).
    def _walk_strings(v):
        if isinstance(v, str):
            yield v
        elif isinstance(v, list):
            for x in v:
                yield from _walk_strings(x)
        elif isinstance(v, dict):
            for k, x in v.items():
                if not str(k).startswith("_"):
                    yield from _walk_strings(x)

    _json_fig_ph = {
        m.group(0)
        for s in _walk_strings(_c)
        for m in re.finditer(r"\[그림 \d+\]", s)
        }
    _declared_fig_ph = set(_figs)
    _unmapped = sorted(_json_fig_ph - _declared_fig_ph)

    if _unmapped:
        if DRAFT_MODE:
            warns += 1
            _draft_waivers += len(_unmapped)
            print(f"  [WARN] 초안의 미선언 그림 자리표시: {_unmapped}")
        else:
            errs += 1
            print(f"  [ERR] 최종본의 미선언 그림 자리표시: {_unmapped}"
                  f" — _figs에 매핑하고 PNG를 넣거나, 초안이면 --draft로 검증할 것")
    elif not _figs:
        print("  그림 없음(자리표시도 없음)")
except FileNotFoundError:
    pass          # 콘텐츠 JSON 미발견은 5절에서 이미 오류로 집계됨

print("\n### 5.6 BinData 정합")
try:
    _hpf = z.read('Contents/content.hpf').decode('utf-8')
    _used = set(re.findall(r'binaryItemIDRef="([^"]+)"', xml))
    _items = dict(re.findall(r'<opf:item id="([^"]+)" href="(BinData/[^"]+)"', _hpf))
    _orphan = {k: v for k, v in _items.items() if k not in _used}
    _missing = _used - set(_items)
    if _orphan:
        errs += 1
        print(f"  [ERR] 고아 BinData(아무도 참조하지 않음): {_orphan}")
    if _missing:
        errs += 1
        print(f"  [ERR] 참조되나 매니페스트에 없음: {sorted(_missing)}")
    _names = set(z.namelist())
    _zip_missing = sorted(h for h in _items.values() if h not in _names)
    if _zip_missing:
        errs += 1
        print(f"  [ERR] 매니페스트에 있으나 ZIP에 없음: {_zip_missing}")
    # ZIP에만 있고 아무도 등록하지 않은 파일 — 문서에 실리지 않는 군더더기다.
    _unlisted = sorted(n for n in _names
                       if n.startswith('BinData/') and n not in set(_items.values()))
    if _unlisted:
        errs += 1
        print(f"  [ERR] ZIP에 있으나 매니페스트에 없음: {_unlisted}")
    # id·href 중복 등록
    _ids = re.findall(r'<opf:item id="([^"]+)" href="BinData/', _hpf)
    _dup_id = sorted({i for i in _ids if _ids.count(i) > 1})
    _hrefs = list(_items.values())
    _dup_href = sorted({h for h in _hrefs if _hrefs.count(h) > 1})
    if _dup_id or _dup_href:
        errs += 1
        print(f"  [ERR] 매니페스트 중복 — id {_dup_id} / href {_dup_href}")
    # _figs 밖의 그림도 실제로 열리는지 본다(등록된 PNG 전부).
    _bad_payload = []
    for _h in sorted(set(_items.values()) & _names):
        if _h.lower().endswith('.png'):
            try:
                IE.verified_png_bytes(z.read(_h), _h)
            except ValueError as _ex:
                _bad_payload.append(f"{_h}: {_ex}")
    if _bad_payload:
        errs += 1
        for _b in _bad_payload:
            print(f"  [ERR] 등록된 그림이 정상 PNG가 아님: {_b}")
    if not (_orphan or _missing or _zip_missing or _unlisted
            or _dup_id or _dup_href or _bad_payload):
        print(f"  고아 0건 / 참조 누락 0건 (등록 {len(_items)}개, 참조 {len(_used)}개)")
except KeyError:
    errs += 1
    print("  [ERR] Contents/content.hpf를 찾지 못함")

print("\n### 6. 표 안 글꼴 통일")
try:
    _hdr = z.read('Contents/header.xml').decode('utf-8')
    _cids = sorted(int(m) for m in re.findall(r'<hh:charPr id="(\d+)"', _hdr))
    _N, _B = str(_cids[-2]), str(_cids[-1])
    def _top_tbls(s):
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
    _EXPECTED_FONTREF = {
        'hangul': '11',
        'latin': '12',
        'hanja': '10',
        'japanese': '10',
        'other': '10',
        'symbol': '8',
        'user': '10',
    }

    def _attr(cid):
        m = re.search(r'<hh:charPr id="%s".*?</hh:charPr>' % cid, _hdr, re.S)
        if not m:
            raise ValueError(f'charPr {cid} 정의를 찾지 못함')

        b = m.group(0)
        hm = re.search(r'height="(\d+)"', b)
        fr = re.search(r'<hh:fontRef ([^/]*)/>', b)
        if not hm:
            raise ValueError(f'charPr {cid}에 height가 없음')
        if not fr:
            raise ValueError(f'charPr {cid}에 fontRef가 없음')

        return (
            hm.group(1),
            bool(re.search(r'<hh:bold\s*/>', b)),
            dict(re.findall(r'(\w+)="([^"]*)"', fr.group(1))),
        )

    _hN, _bN, _fN = _attr(_N)
    _hB, _bB, _fB = _attr(_B)

    if (
        _hN != '1100'
        or _hB != '1100'
        or _bN
        or not _bB
        or _fN != _EXPECTED_FONTREF
        or _fB != _EXPECTED_FONTREF
    ):
        errs += 1
        print(
            f"  [ERR] 통일 스타일 속성 이상: "
            f"본문(h={_hN},bold={_bN},fontRef={_fN}) "
            f"굵게(h={_hB},bold={_bB},fontRef={_fB})"
        )
    _tt = _top_tbls(xml)
    _inner = ''.join(xml[a:b] for a, b in _tt[1:])         # T0 제목 표 제외
    import collections as _co
    _other = {k: v for k, v in _co.Counter(re.findall(r'charPrIDRef="(\d+)"', _inner)).items()
              if k not in (_N, _B)}
    if _other:
        errs += 1
        print(f"  [ERR] 표내 비통일 charPr: {_other}")
    else:
        print("  비통일 charPr: 0건")
except Exception as _e:
    errs += 1
    print(f"  [ERR] 통일 검사 자체가 실패 — 통과로 간주하지 않는다: {_e}")

print("\n### 7. 표 밖 문단 세로 겹침")
def _top_p(s):
    out, d, st = [], 0, None
    for m in re.finditer(r'<hp:p[ >]|</hp:p>', s):
        if m.group(0).startswith('</'):
            d -= 1
            if d == 0:
                out.append((st, m.end()))
        else:
            if d == 0:
                st = m.start()
            d += 1
    return out
def _tbl_spans(s):
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
_overlap = 0
_prev_end = None
for _a, _b in _top_p(xml):
    _p = xml[_a:_b]
    if _tbl_spans(_p):
        _prev_end = None
        continue
    _segs = re.findall(r'<hp:lineseg ([^/]*)/>', _p)
    if not _segs:
        continue
    _ds = [dict(re.findall(r'(\w+)="([^"]*)"', s)) for s in _segs]
    _vps = [int(d.get('vertpos', 0)) for d in _ds]
    # 같은 문단 안에서 줄 세로좌표가 역전되면 겹침(B-7).
    # 문단 내부에는 페이지 넘김 휴리스틱(vertpos 하한)을 적용하지 않고 모든 역전을 잡는다.
    if any(b2 < a2 for a2, b2 in zip(_vps, _vps[1:])):
        _overlap += 1
        print(f"  [ERR] 문단 내 lineseg 역전: {_vps[:6]}")
    _st = int(_ds[0].get('vertpos', 0))
    _en = int(_ds[-1].get('vertpos', 0)) + int(_ds[-1].get('vertsize', 0))
    # 세로좌표가 크게 줄면 새 페이지로 본다(위쪽 여백 이내 시작)
    if _prev_end is not None and _st < _prev_end and _st >= 2000:
        _overlap += 1
        _txt = ''.join(re.findall(r'<hp:t>([^<]*)</hp:t>', _p))[:40]
        print(f"  [ERR] 겹침: 이전 끝 {_prev_end} > 시작 {_st} '{_txt}'")
    _prev_end = _en
if _overlap:
    errs += _overlap
else:
    print("  겹침: 0건")

if DRAFT_MODE and _draft_waivers:
    # 초안 완화를 쓴 실행은 최종 성공과 같은 신호를 내지 않는다(플래그 하나로 최종 게이트를 우회하지 못하게).
    print(f"\n{'='*60}\nDRAFT-ONLY — 최종 제출 불가 / 완화 {_draft_waivers}건 / "
          f"오류 {errs}건 / 경고 {warns}건")
    sys.exit(2)

_result = "PASS" if errs == 0 else "FAIL"
print(f"\n{'='*60}\n{_result} — 오류 {errs}건 / 경고 {warns}건")
sys.exit(0 if errs == 0 else 1)
