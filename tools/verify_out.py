import zipfile, re, json, sys
import xml.etree.ElementTree as ET

S = "/private/tmp/claude-501/-Volumes-ssdmacmini-1-han-ex-projects-123/6981ac5c-4498-45c0-98bf-f487552987cc/scratchpad"
OUT = sys.argv[1]

z = zipfile.ZipFile(OUT)
print("entries:", len(z.namelist()))
xml = z.read('Contents/section0.xml').decode('utf-8')
ET.fromstring(xml)
print("XML well-formed: OK")

texts = re.findall(r'<hp:t>([^<]*)</hp:t>', xml)
print("텍스트 런 수:", len(texts))

import html
joined = html.unescape("".join(texts))
s = json.load(open(S + "/slots_final.json", encoding='utf-8'))
missing = []
for k, v in s.items():
    for ln in (v if isinstance(v, list) else [v]):
        if ln.strip() and ln not in joined:
            missing.append((k, ln[:70]))
print("누락 줄:", len(missing))
for m in missing[:15]:
    print("  ", m)

# table geometry
starts = [m.start() for m in re.finditer(r'<hp:tbl ', xml)]
ends = [m.end() for m in re.finditer(r'</hp:tbl>', xml)]
print("\n표 구조:")
for i, (a, b) in enumerate(zip(starts, ends)):
    t = xml[a:b]
    sz = re.search(r'<hp:sz [^>]*height="(\d+)"', t)
    rows = {}
    for cm in re.finditer(r'<hp:tc[ >].*?</hp:tc>', t, re.S):
        c = cm.group(0)
        am = re.search(r'colAddr="(\d+)" rowAddr="(\d+)"', c)
        sm = re.search(r'colSpan="(\d+)" rowSpan="(\d+)"', c)
        zm = re.search(r'width="(\d+)" height="(\d+)"', c)
        if am and sm and zm and int(sm.group(2)) == 1:
            r = int(am.group(2))
            rows[r] = max(rows.get(r, 0), int(zm.group(2)))
    total = sum(rows.values())
    print(f"  T{i}: 표높이={sz.group(1) if sz else '?'} 행합={total} 행별={[rows[k] for k in sorted(rows)]}")
