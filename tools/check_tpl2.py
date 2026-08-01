"""중첩 표를 인식하는 HWPX 구조·레이아웃 검증기."""
import zipfile, re, sys, json, unicodedata
import xml.etree.ElementTree as ET

OUT = sys.argv[1]
S = "/private/tmp/claude-501/-Volumes-ssdmacmini-1-han-ex-projects-123/6981ac5c-4498-45c0-98bf-f487552987cc/scratchpad"
z = zipfile.ZipFile(OUT)
xml = z.read('Contents/section0.xml').decode('utf-8')
hdr = z.read('Contents/header.xml').decode('utf-8')

errs = warns = 0


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
print(f"  엔트리 {len(info)}, 첫 엔트리 {info[0].filename} "
      f"method={info[0].compress_type}, testzip={z.testzip()}")
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
    if len(segs) == 1 and sum(w(c, em) for c in t) > hz:
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
    print("  (content2.json 없음)")

print(f"\n{'='*60}\n오류 {errs}건 / 경고 {warns}건")
