import zipfile, re, sys, collections

OUT = sys.argv[1]
z = zipfile.ZipFile(OUT)
xml = z.read('Contents/section0.xml').decode('utf-8')
hdr = z.read('Contents/header.xml').decode('utf-8')

# 1. paragraph id uniqueness
ids = re.findall(r'<hp:p id="(\d+)"', xml)
dup = [k for k, v in collections.Counter(ids).items() if v > 1]
print(f"문단 수 {len(ids)}, 중복 id {len(dup)}개", dup[:5])

# 2. style refs exist
para_ids = set(re.findall(r'<hh:paraPr id="(\d+)"', hdr))
char_ids = set(re.findall(r'<hh:charPr id="(\d+)"', hdr))
used_p = set(re.findall(r'paraPrIDRef="(\d+)"', xml))
used_c = set(re.findall(r'charPrIDRef="(\d+)"', xml))
print("미정의 paraPr:", sorted(used_p - para_ids))
print("미정의 charPr:", sorted(used_c - char_ids))

# 3. borderFill refs
bf_ids = set(re.findall(r'<hh:borderFill id="(\d+)"', hdr))
used_bf = set(re.findall(r'borderFillIDRef="(\d+)"', xml))
print("미정의 borderFill:", sorted(used_bf - bf_ids))

# 4. table pageBreak / cell counts
for i, m in enumerate(re.finditer(r'<hp:tbl ([^>]*)>', xml)):
    a = m.group(1)
    pb = re.search(r'pageBreak="(\w+)"', a)
    rc = re.search(r'rowCnt="(\d+)" colCnt="(\d+)"', a)
    print(f"  T{i}: pageBreak={pb.group(1) if pb else '?'} rows/cols={rc.groups() if rc else '?'}")

# 5. cell count per table matches rowCnt*colCnt accounting spans
starts = [x.start() for x in re.finditer(r'<hp:tbl ', xml)]
ends = [x.end() for x in re.finditer(r'</hp:tbl>', xml)]
for i, (s, e) in enumerate(zip(starts, ends)):
    t = xml[s:e]
    cells = re.findall(r'<hp:tc[ >]', t)
    rc = re.search(r'rowCnt="(\d+)" colCnt="(\d+)"', t)
    spans = sum(int(a) * int(b) for a, b in re.findall(r'colSpan="(\d+)" rowSpan="(\d+)"', t))
    exp = int(rc.group(1)) * int(rc.group(2))
    print(f"  T{i}: 셀 {len(cells)}개, span합 {spans}, rowCnt*colCnt {exp} {'OK' if spans == exp else 'MISMATCH'}")

# 6. control chars / illegal XML chars in text
bad = []
for t in re.findall(r'<hp:t>([^<]*)</hp:t>', xml):
    for ch in t:
        if ord(ch) < 0x20 and ch not in '\t':
            bad.append((repr(ch), t[:40]))
print("제어문자 포함 런:", len(bad))

# 7. mimetype stored first & uncompressed
info = z.infolist()
print("첫 엔트리:", info[0].filename, "compress_type:", info[0].compress_type, "(0=STORED)")
print("mimetype 내용:", z.read('mimetype').decode())
