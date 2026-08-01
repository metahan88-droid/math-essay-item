"""완성 HWPX를 표/칸 단위로 덤프한다 (깊이 인식)."""
import zipfile, re, sys

OUT = sys.argv[1]
only = sys.argv[2] if len(sys.argv) > 2 else None
z = zipfile.ZipFile(OUT)
xml = z.read('Contents/section0.xml').decode('utf-8')


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


def unesc(t):
    return (t.replace('&amp;', '&').replace('&lt;', '<')
             .replace('&gt;', '>').replace('&quot;', '"'))


def cell_paras(cell):
    """셀 직속 문단들의 (텍스트, 줄수, 표포함) — 중첩 표 안 텍스트 제외."""
    sl = spans(cell, 'hp:subList')
    if not sl:
        return []
    b = cell[sl[0][0]:sl[0][1]]
    inner = b[b.index('>') + 1:b.rindex('</hp:subList>')]
    out = []
    for a, e in spans(inner, 'hp:p'):
        p = inner[a:e]
        has = bool(spans(p, 'hp:tbl'))
        body = p
        for na, nb in reversed(spans(p, 'hp:tbl')):
            body = body[:na] + body[nb:]
        t = unesc(''.join(re.findall(r'<hp:t>([^<]*)</hp:t>', body)))
        lsa = body.rfind('<hp:linesegarray>')
        n = len(re.findall(r'<hp:lineseg ', body[lsa:])) if lsa >= 0 else 0
        out.append((t, n, has))
    return out


for ti, (a, b) in enumerate(all_tbl(xml)):
    if only and str(ti) != only:
        continue
    t = xml[a:b]
    off = t.index('>') + 1
    inner = t[off:t.rindex('</hp:tbl>')]
    print(f"\n{'='*78}\n### T{ti}")
    for ca, cb in spans(inner, 'hp:tc'):
        c = inner[ca:cb]
        am = re.search(r'colAddr="(\d+)" rowAddr="(\d+)"', c)
        ps = cell_paras(c)
        if not any(p[0].strip() or p[2] for p in ps):
            continue
        print(f"\n-- r{am.group(2)}c{am.group(1)} ({len(ps)}문단)")
        for txt, n, has in ps:
            if has:
                print(f"     [중첩표]")
            elif txt.strip():
                print(f"   {n:2}줄| {txt}")
            else:
                print(f"     | (빈 줄)")
