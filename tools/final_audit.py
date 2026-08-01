"""최종 자체 감사 — 겹침 재발 가능성이 남았는지 직접 확인."""
import zipfile, re, sys, unicodedata, collections

OUT = sys.argv[1]
z = zipfile.ZipFile(OUT)
xml = z.read('Contents/section0.xml').decode('utf-8')
hdr = z.read('Contents/header.xml').decode('utf-8')

print("### 1. lineWrap — SQUEEZE 셀에 다중 줄 문단이 남아 있는가 (겹침의 직접 원인)")
bad = 0
for cm in re.finditer(r'<hp:tc[ >].*?</hp:tc>', xml, re.S):
    c = cm.group(0)
    lw = re.search(r'<hp:subList [^>]*lineWrap="(\w+)"', c)
    if not lw:
        continue
    for pm in re.finditer(r'<hp:p [^>]*>(.*?)</hp:p>', c, re.S):
        n = len(re.findall(r'<hp:lineseg ', pm.group(1)))
        t = ''.join(re.findall(r'<hp:t>([^<]*)</hp:t>', pm.group(1)))
        if lw.group(1) == 'SQUEEZE' and n > 1:
            bad += 1
            print(f"  [ERR] SQUEEZE 셀에 {n}줄 문단: {t[:40]!r}")
cnt = collections.Counter(re.findall(r'<hp:subList [^>]*lineWrap="(\w+)"', xml))
print(f"  lineWrap 분포: {dict(cnt)}  / SQUEEZE 다중줄 위반: {bad}")

print("\n### 2. 굵게(bold) — 본문이 굵은 글꼴을 쓰는가")
bolds = set()
for m in re.finditer(r'<hh:charPr id="(\d+)".*?</hh:charPr>', hdr, re.S):
    if '<hh:bold' in m.group(0):
        bolds.add(m.group(1))
used = collections.Counter(re.findall(r'charPrIDRef="(\d+)"', xml))
print(f"  bold charPr: {sorted(bolds)}")
print(f"  사용 charPr: {dict(used)}")
print(f"  본문에 쓰인 bold charPr: {sorted(set(used) & bolds)}")

print("\n### 3. 긴 문단 표본 — lineseg가 텍스트를 실제로 분할하는가")
shown = 0
for cm in re.finditer(r'<hp:tc[ >].*?</hp:tc>', xml, re.S):
    c = cm.group(0)
    for pm in re.finditer(r'<hp:p [^>]*>(.*?)</hp:p>', c, re.S):
        body = pm.group(1)
        t = ''.join(re.findall(r'<hp:t>([^<]*)</hp:t>', body))
        t = t.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
        segs = [dict(re.findall(r'(\w+)="([^"]*)"', s))
                for s in re.findall(r'<hp:lineseg ([^/]*)/>', body)]
        if len(t) > 120 and shown < 2:
            shown += 1
            print(f"\n  문단 {len(t)}자 → {len(segs)}줄, horzsize={segs[0]['horzsize']}, "
                  f"spacing={segs[0]['spacing']}, vertpos={[s['vertpos'] for s in segs[:4]]}...")
            tp = [int(s['textpos']) for s in segs] + [len(t)]
            for i in range(min(4, len(segs))):
                print(f"     줄{i}: [{tp[i]:4}:{tp[i+1]:4}] {t[tp[i]:tp[i+1]]!r}")

print("\n### 4. 모든 문단: lineseg 개수가 1인데 텍스트가 한 줄을 넘는가 (겹침 위험)")
def w(ch):
    if unicodedata.combining(ch):
        return 0
    e = unicodedata.east_asian_width(ch)
    if e in ('W', 'F', 'A', 'N'):
        return 1200
    return 600 if ch == ' ' else 700

risk = 0
for cm in re.finditer(r'<hp:tc[ >].*?</hp:tc>', xml, re.S):
    for pm in re.finditer(r'<hp:p [^>]*>(.*?)</hp:p>', cm.group(0), re.S):
        body = pm.group(1)
        t = ''.join(re.findall(r'<hp:t>([^<]*)</hp:t>', body))
        segs = re.findall(r'<hp:lineseg ([^/]*)/>', body)
        if len(segs) == 1 and t:
            hz = int(dict(re.findall(r'(\w+)="([^"]*)"', segs[0]))['horzsize'])
            tot = sum(w(c) for c in t)
            if tot > hz:
                risk += 1
                print(f"  [RISK] 1줄 캐시인데 폭 {tot} > {hz}: {t[:45]!r}")
print(f"  위험 문단: {risk}건")
