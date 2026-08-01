# 종합 판정

**시행 보류**입니다.

3차 감사의 A급 5건 가운데, 사용자가 지정한 과거 반례 자체는 대부분 실제로 막혔습니다.

- A1의 “외부 PNG와 XML ID만 있고 `BinData` 0개” 반례: 차단됨.
- A2의 `{...null}` 및 잘못된 `review.best`: 차단됨.
- A3의 학교 규정 오버라이드 6개 회귀: 전부 기대대로 동작.
- A4의 지필 0점 문구와 `ㅁ` 받침 충돌: 해소됨.
- A5의 3차 감사 당시 정확한 반례 4종: 모두 기대대로 판정됨.

그러나 다음 **새 A급 또는 남아 있던 동등 우회**가 실물·실행에서 확인됐습니다.

1. `_figs`를 아예 선언하지 않으면 그림 3개가 없는 최종 HWPX도 경고만 내고 `PASS`, 종료 코드 0입니다.
2. `check_levels()`는 이름 배열만 `A,B,C,D,E`로 두고 실제 점수 구간을 `A=저점 … E=고점`으로 뒤집으면 여전히 `True`를 반환합니다.
3. “복제 가능”으로 표시된 `examples-pizza.md` B-6 채점기준에 한 학생 답안이 2점과 1점에 동시에 걸리는 급간 중복이 여러 건 남았습니다. 수선 에이전트가 보고한 문항 4 첫째 요소의 중복도 실제 결함입니다.

따라서 핵심 회귀 수선은 상당수 작동하지만, 현재 패키지를 그대로 승인할 수는 없습니다.

---

# 감사 범위와 실행 방식

요청된 다음 18개 파일을 끝까지 직접 읽었습니다.

- `SKILL.md`
- `references/*.md` 7개
- `examples/*` 2개
- `tools/*.py` 6개
- `workflows/*.js` 2개

모든 대상에 SHA-256 스냅샷을 잡았습니다. 주요 최종 스냅샷은 다음과 같습니다.

```text
check_tpl2.py       52c7fd78414cc96a0714a20e98c0da88c144bd3a2c72ba6042fe59ef0fc0b816
build_tpl2.py       1eb11d28d68d8e12688a41125099da950c0c7812935e325bbca63c07805f16fe
figlib.py           14d8329c5d8d9d3b2bf16675e8b9636a0a97a07417aba2dbc2f4816ecdc718c0
restyle.py          f8fb0fbee29df0c2e416453674e68ca9a6e1c408a10791e5345c51164533f941
rubric-rules.md     3c6a5e0233a726fc0f3ba74124b9d3d8e07ae19ac8ac57af691d01a4831d15dc
standards.md        6fc8c744f64684a35975c33c9345917890a7204bee45a3ae2feb2317b5dd0750
examples-pizza.md   4af35ee35b52d25b77c11cdef7021a3ab3b9ee9bf281b7bfb0bdcd7ab57f079e
valid JSON          b9de387671f02919085989eb279303e3500cb439d3e6ca5f13a4be567b2ce166
develop-draft.js    a174597a0e8b4c14110ce2d6d2b4b46613f03a72ac433fa265cb3c5a5af79cea
verify-rubric.js    6d57faebc8e8b4c14110ce2d6d2b4b46613f03a72ac433fa265cb3c5a5af79cea
```

마지막 줄의 표시를 바로잡으면 `verify-rubric.js`의 실제 최종 해시는 다음입니다.

```text
verify-rubric.js    6d57faebc8e8b4c14110ce2d6d2b4b46613f03a72ac433fa265cb3c5a5af79cea
```

감사 도중 대상이 한 차례 추가 변경됐습니다.

- 최초 `build_tpl2.py`: 974행, `110b…375`
- 최종 `build_tpl2.py`: 977행, `1eb1…6fe`
- 최종본에는 빠져 있던 `if __name__ == '__main__': main()`이 추가됨
- `tools/out2/`도 감사 도중 외부에서 사라짐
- `hwpx-build.md` 역시 최종 해시 `9e3b…50c3`으로 바뀜

최종 판정은 이 변경 뒤 최신 소스를 다시 읽고, 최신 `build_tpl2.py`를 사용해 E2E를 재실행한 결과입니다.

환경이 파일시스템 읽기 전용이어서 `mktemp`조차 `Operation not permitted`로 차단됐습니다. 따라서 반례 ZIP과 E2E HWPX는 `BytesIO` 및 프로세스 내부 가상 파일시스템에서 만들었습니다. 다만 검사 로직을 다시 구현한 것이 아니라, 실제 `build_tpl2.py` → 실제 `restyle.py` → 실제 `check_tpl2.py` 본문을 그대로 실행하고 생성된 HWPX ZIP 바이트를 다시 검사했습니다. 대상 스킬 파일은 수정하지 않았습니다.

Python 6개와 JavaScript 워크플로 2개도 전부 실제 컴파일했습니다.

```text
PY_OK metrics.py
PY_OK build_tpl2.py
PY_OK img_embed.py
PY_OK check_tpl2.py
PY_OK figlib.py
PY_OK restyle.py
JS_OK develop-draft.js
JS_OK verify-rubric.js
```

---

# A1. `check_tpl2.py` 그림 게이트

## 판정: 부분 — 지정 반례는 차단됨, 정상 그림도 오탐 없음, 그러나 `_figs` 생략 우회가 A급으로 남음

현재 구현은 주장한 네 검사를 실제로 수행합니다.

- 외부 원본 PNG 실존·서명: [check_tpl2.py:240](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:240>)
- `_figs` ID 중복: [check_tpl2.py:224](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:224>)
- `content.hpf`의 `id → href`: [check_tpl2.py:229](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:229>)
- ZIP 내부 엔트리 실존: [check_tpl2.py:258](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:258>)
- 내장 PNG 8바이트 서명: [check_tpl2.py:263](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:263>)

## 3차 false-pass 재현

조건을 그대로 다시 만들었습니다.

- 외부 PNG: 정상
- `section0.xml`: `binaryItemIDRef="fig1"` 존재
- `content.hpf`: BinData 등록 전부 제거
- ZIP: `BinData/*` 전부 제거

실행 로그:

```text
CASE no_hpf EXIT 1
### 5.5 그림 게이트
  [ERR] 그림이 content.hpf에 등록되지 않음: fig1
  _figs 선언 1건, 삽입·등록·PNG 확인, BinData 0개
FAIL
```

나머지 주장도 각각 재현했습니다.

```text
CASE missing_bin EXIT 1
  [ERR] 등록된 그림 BinData가 ZIP에 없음:
        fig1 → BinData/fig1.png

CASE corrupt EXIT 1
  [ERR] 삽입된 BinData가 정상 PNG가 아님:
        fig1 → BinData/fig1.png

CASE duplicate EXIT 1
  [ERR] _figs의 BinData id가 중복됨
```

따라서 3차의 정확한 false-pass는 **차단됐습니다**.

## 정상 그림 포함 산출물의 새 오탐 여부

실제 PNG 3개와 `_figs`를 넣은 최신 full E2E는 전체 종료 코드 0이었습니다.

```text
BUILD    그림 3개 삽입: ['fig1', 'fig5', 'fig6']
BUILD    lineseg 920개, SQUEEZE 다중줄 위반 0건

RESTYLE treatAsChar 해제 9건
        라벨 셀 재작성 52건

CHECK   엔트리 16, mimetype method=0, testzip=None
CHECK   누락 줄: 0
CHECK   _figs 선언 3건, 삽입·등록·PNG 확인, BinData 5개
CHECK   비통일 charPr: 0건
CHECK   겹침: 0건
CHECK   PASS — 오류 0건 / 경고 1건
EXIT    0
```

즉, 등록된 정상 그림에 대해 새 false-positive는 없습니다.

## A — `_figs`를 생략하면 최종 그림 누락이 다시 PASS

정확한 예시 JSON에는 `_figs`가 없지만, 다음 세 자리표시가 있습니다.

- [valid-similarity-20pt.json:145](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:145>)
- [valid-similarity-20pt.json:146](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:146>)
- [valid-similarity-20pt.json:165](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:165>)

패키지에는 해당 `examples/figs/*.png`도 없습니다. 빌더는 [build_tpl2.py:282](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:282>)에서 그림 파일이 없으면 예외를 내지 않고 자리표시 텍스트로 되돌립니다. 검증기는 [check_tpl2.py:270](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:270>)에서 이를 오류가 아닌 경고로만 셉니다.

원본 예시 JSON 그대로 E2E:

```text
BUILD [그림 없음] figs/fig1_three_sizes.png — 자리표시 텍스트로 유지
BUILD [그림 없음] figs/fig5_menu_board.png — 자리표시 텍스트로 유지
BUILD [그림 없음] figs/fig6_owner_memo.png — 자리표시 텍스트로 유지

CHECK [WARN] _figs 미선언 + 자리표시 잔존 3종
CHECK PASS — 오류 0건 / 경고 2건
EXIT 0
```

이는 [hwpx-build.md:516](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:516>)의 “허용 경고는 서식 원본 유래 폭 초과 1건뿐”이라는 설명과도 충돌합니다.

따라서 A1은 **지정 반례는 차단됐지만 최종 승인 체인은 여전히 우회 가능**합니다.

### 붙여넣기 가능한 수정 방향

`build_tpl2.py`:

```python
DRAFT_MODE = "--draft" in sys.argv[3:]

# make_paras() 안
if fig and not os.path.exists(os.path.join(FIG_BASE[0], fig[1])):
    if DRAFT_MODE:
        print(f"   [그림 없음] {fig[1]} — 초안 자리표시 텍스트로 유지")
        fig = None
    else:
        raise FileNotFoundError(
            f"최종 조판에 필요한 그림 파일이 없음: {fig[1]}"
        )
```

`check_tpl2.py`:

```python
DRAFT_MODE = "--draft" in sys.argv[3:]

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
    for m in [re.match(r"\[그림 \d+\]", s.strip())]
    if m
}
_declared_fig_ph = set(_figs)
_unmapped = sorted(_json_fig_ph - _declared_fig_ph)

if _unmapped:
    if DRAFT_MODE:
        warns += 1
        print(f"  [WARN] 초안의 미선언 그림 자리표시: {_unmapped}")
    else:
        errs += 1
        print(f"  [ERR] 최종본의 미선언 그림 자리표시: {_unmapped}")
```

그리고 `examples/valid-similarity-20pt.json`에 `_figs`를 넣고 실제 PNG 세 파일을 `examples/figs/`에 배포해야 합니다.

---

# A2. `develop-draft.js` fail-closed

## 판정: 지정 반례는 차단됨

현재 코드:

- falsy 응답 spread 전에 throw: [develop-draft.js:86](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:86>)
- `best` 스키마 enum: [develop-draft.js:116](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:116>)
- 실제 유효 key 집합 검사: [develop-draft.js:122](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:122>)

실제 워크플로 모킹 로그:

```text
null-b
→ THROW 초안 에이전트 b 실패 — 응답 없음

best-z
→ THROW 심사 에이전트 실패 —
  best="z"가 유효한 초안 key가 아님(fail-closed)

valid-best-b
→ {"pass":true,"draftCount":3,"best":"b"}
```

따라서 3차의 `{...null}` 반례와 `best:"z"` 반례는 모두 막혔습니다. `review.best`는 enum과 런타임 집합 검사를 모두 갖췄습니다.

## B — truthy 불완전 객체는 여전히 살아남음

다음 추가 모킹은 여전히 통과합니다.

```text
둘째 초안 = {}
→ PASS
  second = {"key":"b","angle":"설계·제작 — ..."}

심사 응답 = {"best":"b"}
→ PASS
  review = {"best":"b"}
```

즉 명시적 방어는 falsy 여부와 `best`만 검사합니다. 실제 Workflow 런타임이 스키마의 `required`를 언제나 강제한다는 계약에 의존합니다. 보통은 스키마가 막아야 하지만, 이 패키지는 과거에 스키마가 있는데도 `null` 반환을 실제로 겪었으므로 런타임 방어를 완성하는 편이 안전합니다.

붙여넣기 가능한 수정안:

```javascript
const DRAFT_FIELDS = [
  'title', 'scenario', 'materials', 'questions',
  'numbers', 'transfer', 'verify_log',
]

.then(r => {
  const malformed =
    !r ||
    typeof r !== 'object' ||
    Array.isArray(r) ||
    DRAFT_FIELDS.some(
      k => typeof r[k] !== 'string' || !r[k].trim()
    )

  if (malformed)
    throw new Error(
      `초안 에이전트 ${a.key} 실패 — 응답 없음 또는 필수 필드 누락`
    )

  return { ...r, key: a.key, angle: a.angle }
})
```

심사 응답도 동일하게 `ranking/best/fixes/grafts` 네 필드의 비어 있지 않은 문자열 여부를 검사해야 합니다.

---

# A3. 학교 규정 오버라이드

## 판정: 요구한 6개 회귀는 모두 정상 — 원 A급 지적은 차단됨

구조는 실제로 들어갔습니다.

- `DEFAULT_RULES`: [rubric-rules.md:462](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:462>)
- `SCHOOL_OVERRIDE`와 키 오타 검사: [rubric-rules.md:476](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:476>)
- 합성 `RULE`, 실제 `LOW/MINS/ZERO_DESC`: [rubric-rules.md:481](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:481>)
- 실제 `LOW` 기반 행 수: [rubric-rules.md:536](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:536>)
- 실제 급간 합으로 floor 계산: [rubric-rules.md:638](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:638>)

문서 fenced Python을 직접 추출해 실행한 결과:

| 케이스 | 결과 | 핵심 로그 |
|---|---:|---|
| (a) 수행 정상 | exit 0 | `데이터 20행 / floor=6` |
| (b) 지필 정상 | exit 0 | `데이터 26행 / floor=0` |
| (c) 수행 + override low 0 | exit 0 | `수행평가+학교규정 / 26행 / floor=0` |
| (d) override 키 오타 | exit 1 | `SCHOOL_OVERRIDE 키 오타: {'loow'}` |
| (e) 지필 0점 행 제거 | exit 1 | 검사 1 여섯 건 + `20 ≠ 26` |
| (f) 고정 문구 변형 | exit 1 | `「무응답 또는 그 외의 오답.」와 다름` |

정확한 로그:

```text
A3-a
PASS — 수행평가(최저 1점) / 요소 6개 / 데이터 20행 /
총점 20점 / 제출자 최저 총점 floor=6 / 경고 0건

A3-b
PASS — 지필평가(최저 0점) / 요소 6개 / 데이터 26행 /
총점 20점 / 제출자 최저 총점 floor=0 / 경고 0건

A3-c
PASS — 수행평가+학교규정(최저 0점) /
요소 6개 / 데이터 26행 / floor=0

A3-d
AssertionError: SCHOOL_OVERRIDE 키 오타: {'loow'}

A3-e
1 급간 하강 연속 위반 ... [4, 3, 2, 1]
6 데이터 행 수 20 ≠ 26

A3-f
2 0점 진술이 「무응답 또는 그 외의 오답.」와 다름:
무응답 또는 그 밖의 오답.
```

추가로 다음도 확인했습니다.

```text
SCHOOL_OVERRIDE={"min_element":4}
→ 검사 3 실제 발동

zero_desc를 학교 문구로 바꾸고 모든 최저행을 같은 문구로 변경
→ PASS
```

따라서 `LOW`·`MINS`·`ZERO_DESC`·급간 수·행 수·floor가 이름뿐 아니라 실제 합성 규칙에서 파생됩니다.

[standards.md:213](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:213>)과 [standards.md:261](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:261>)도 floor를 실제 요소별 최저 급간 합으로 넘기라고 명시합니다. [failure-modes.md:391](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:391>)의 프롬프트 오버라이드 블록도 같은 원칙과 정합합니다.

## 기존 검사 1·2·3·6·8·9·11 회귀

| 검사 | 변형 | 결과 |
|---|---|---|
| 1·6 | 수행 최저행 제거 | FAIL |
| 1·2 | 수행에 0점 행 추가 | FAIL |
| 3 | 수행 1점 요소 | FAIL |
| 3 | 같은 1점 요소를 지필로 구성 | PASS, 7요소·27행 |
| 8 | 51자 진술 | FAIL |
| 9 | `…설명했다.` | FAIL |
| 11 | `구하려 하였으나` | FAIL |
| 8·9·11 | 지필 고정 0점 행 | 정상 제외·PASS |

검사 5의 합계 행도 수정됐습니다.

```text
"120점"   → FAIL: 합계 행 점수 '120점' ≠ 20점
합계 2개   → FAIL: 합계 행 개수 2 ≠ 1
합계 비마지막 → FAIL: 합계 행이 마지막 원소가 아님
```

지필 “결론만 쓴 답안” 귀속도 [rubric-rules.md:208](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:208>)에서 요소별 1점 진술에 포함되면 1점, 아니면 0점으로 미리 확정하도록 수정됐습니다.

## B — ATTEMPT 정규식은 부분 수정: 구 반례 차단, 새 우회와 새 오탐 공존

현재 패턴은 [rubric-rules.md:590](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:590>)에 있습니다.

과거 우회는 막혔습니다.

```text
세 비를 구하는 과정에 오류가 있고 그 관계를 설명하지 못함.
→ exit 1, 검사 11
```

그러나 다음 시도 전제 진술은 잘못 통과합니다.

```text
세 비 가운데 하나를 구했으나 그 관계를 설명하지 못함.
→ exit 0, PASS
```

백지는 “하나를 구했으나”를 만족하지 않으므로 실제로 빠집니다. 현재 정규식에 `하였으나`와 `했지만`은 있지만 `했으나`가 없습니다.

반대로 다음 정상적인 백지 포괄 문장은 잘못 차단합니다.

```text
두 조건의 구분과 지름 구하기에서
일부를 빠뜨리거나 모두 수행하지 못함.
→ exit 1
```

```text
두 조건의 구분과 지름 계산을 전혀 시도하지 못함.
→ exit 1
```

첫 문장은 `일부를`만 보고, 둘째 문장은 부정문 속 단어 `시도`만 보고 시도 전제로 오판합니다.

붙여넣기 가능한 최소 수정안:

```python
ATTEMPT = (
    r"(려\s*하였으나|"
    r"(?<!못)(?<!못 )하였으나|"
    r"(?<!못)(?<!못 )했으나|"
    r"(?<!못)(?<!못 )했지만|"
    r"시도(?:하였으나|했으나|함|했지만)|"
    r"일부만|"
    r"일부를\s*(?:옳게\s*)?"
    r"(?:수행함|구함|계산함|작성함|설명함|판단함)|"
    r"(?:구하|설명하|판단하|작성하)는\s*과정"
    r"(?:에|에서).*(?:오류|잘못)|"
    r"오류가\s*(?:있|남)(?!지\s*않))"
)
```

정규식만으로 `적었으나`·`썼으나` 등 모든 의미 변형을 막을 수는 없습니다. [rubric-rules.md:653](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:653>)의 “실제 백지·완전 오답 대입” 수기 검사를 권고가 아니라 blocking 절차로 유지해야 합니다.

---

# A4. 지필 0점 고정 문구와 `ㅁ` 받침 충돌

## 판정: 차단됨 — 정상 급간 검사는 무력화되지 않음

예외가 두 요구 위치에 실제로 들어갔습니다.

- `[수정안 제약]`: [failure-modes.md:398](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:398>)
- 시험 11: [failure-modes.md:479](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:479>)

종성 계산:

```text
답 → 17 = ㅂ
함 → 16 = ㅁ
음 → 16 = ㅁ
씀 → 16 = ㅁ
다 → 0
```

따라서 예외가 없으면 `무응답 또는 그 외의 오답.`은 반드시 실패한다는 3차 지적이 맞았습니다.

현재 기계 검사에서는:

- `score == LOW`이고 `ZERO_DESC is not None`인 행만 길이·종결 검사에서 제외
- 그 행의 문자열 정확 일치는 검사 2가 별도로 강제
- 나머지 급간은 계속 `ㅁ` 받침 검사를 받음

실행 결과:

```text
0점  "무응답 또는 그 외의 오답." → 정확 문자열 검사 후 예외
1점  "일부를 옳게 수행함."       → 정상 통과
1점  "일부를 옳게 수행한다."     → 종결 검사 실패
0점  "무응답 또는 그 밖의 오답." → 정확 문자열 검사 실패
```

따라서 예외가 정상 급간 검사까지 무력화하지 않습니다.

## C — 일반 문체 설명에는 예외가 생략됨

작동하는 코드와 최종 프롬프트는 고쳐졌지만 다음 포괄 문장은 여전히 “모든 급간”처럼 읽힙니다.

- [failure-modes.md:9](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:9>)
- [rubric-rules.md:162](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:162>)

붙여넣기 가능한 보완:

```text
종결은 명사형 어미 ㅁ 받침으로 한다. 단, 지필평가의 최저 0점 행은
고정 문구 `무응답 또는 그 외의 오답.`을 그대로 쓰며 이 종결 검사에서 제외한다.
학교 규정 오버라이드가 0점 고정 문구를 달리 정하면 그 확정 문구만 같은 예외로 둔다.
```

---

# A5. 성취수준 게이트

## 판정: 3차의 정확한 반례는 전부 차단됨. 그러나 의미가 같은 새 방향 역전이 A급으로 여전히 통과

현재 `check_levels`는 [standards.md:232](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:232>)에 있습니다.

3차 감사 당시의 정확한 회귀 스크립트를 현재 fenced block에 다시 적용한 결과:

```text
[OK] 수행 정상                    → True
[OK] 수행 E 0~3 도달 불가         → AssertionError
[OK] 지필 0~20 자연 분할          → True
[OK] [("E",0,20)] 단일 구간       → AssertionError
[OK] A/E 이름 라벨 swap           → AssertionError
[OK] C 비최대                     → AssertionError
[OK] R=7 축소형                   → True
[OK] R=5                          → AssertionError
[OK] PROFILE "수행 평가" 오타      → AssertionError

9/9 통과
```

사용자가 지정한 네 반례를 정확히 구분하면:

- `[("E",0,20)]`: 차단됨.
- 기존 A/E 이름 swap: 차단됨.
- 유효한 `R=7` 축소형: `True`; 과거 `R<10` 오판 수정됨.
- C 비최대: 차단됨.
- `PROFILE` 오타도 차단됨.

## A — 이름은 ABCDE인 채 실제 점수 bounds를 뒤집으면 `True`

다음은 잘못 통과했습니다.

```python
levels = [
    ("A", 0, 7),
    ("B", 8, 9),
    ("C", 10, 15),
    ("D", 16, 17),
    ("E", 18, 20),
]

check_levels(levels, 20, 6)
# True
```

A가 최저점이고 E가 만점을 가져 [standards.md:193](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:193>)의 “만점은 A”를 정반대로 위반합니다.

원인은 이름 배열만 `ABCDE`인지 확인한 뒤, 실제 구간을 `lo`로 다시 정렬해서 연속성만 보기 때문입니다. 기존의 “이름 자체 swap”은 막았지만 의미적으로 같은 “bounds swap”은 통과합니다.

### 붙여넣기 가능한 A급 수정안

현재 이름·연속성 블록을 다음으로 교체하면 됩니다.

```python
assert [name for name, _, _ in levels] == list("ABCDE"), \
    "수준은 A,B,C,D,E가 이 순서로 정확히 한 번씩 있어야 함"

assert 0 <= floor <= total, \
    f"floor 범위 오류: {floor} (total={total})"

for name, lo, hi in levels:
    assert 0 <= lo <= hi <= total, \
        f"{name} 구간 범위/방향 오류: {lo}~{hi}"

assert levels[0][2] == total, \
    "A 수준 상한이 총점이 아님"
assert levels[-1][1] == 0, \
    "E 수준 하한이 0이 아님"

# levels는 A→E, 즉 높은 점수 구간부터 낮은 구간 순서다.
for higher, lower in zip(levels, levels[1:]):
    assert lower[2] + 1 == higher[1], \
        f"구간 불연속/중복/순서 역전: {higher} {lower}"
```

이 뒤에 기존 수준별 도달 가능성 및 C 폭 검사를 유지하면 됩니다.

## `verify-rubric.js` 재검증 blocking 게이트

이 부분은 수정됐습니다.

- 초기 검증 `null` 차단: [verify-rubric.js:79](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:79>)
- 재검증 `null` 차단: [verify-rubric.js:107](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:107>)
- 최초 `blocking`을 버리고 재검의 `real && blocking` 사용: [verify-rubric.js:111](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:111>)

실행:

```text
정상
→ pass=true

최초 blocking=false,
재검 real=true, blocking=true
→ pass=false, confirmed=1

초기 agent=null
→ throw

재검 agent=null
→ throw
```

따라서 3차의 `blocking=false` fail-open은 막혔습니다.

## B — 리뷰어 항목 2가 방향·C 폭·지필 자연 분할을 명시하지 않음

[verify-rubric.js:65](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:65>)은 수행 floor와 수준별 도달 가능성은 명시하지만 다음은 없습니다.

- A가 최고, E가 최저인지
- A→E의 수치 방향
- C 폭 규칙
- 지필 자연 분할 규칙

붙여넣기 가능한 추가:

```text
수준 이름과 수치 방향도 대조하여 A의 상한=총점, E의 하한=0이고
A>B>C>D>E의 점수 구간 순서인지 확인하라.
C의 도달 가능 점수 수가 해당 프로파일의 폭 규칙을 만족하는지 확인하고,
지필평가는 standards.md §4.3에서 확정한 자연 분할 규칙대로
수준별 점수 개수를 다시 계산해 대조하라.
```

## B — 지필 “자연 분할”은 코드에서 강제되지 않으며 정책 자체도 충돌

다음 극단 지필 구간도 현재 함수가 `True`로 받습니다.

```python
[
    ("A", 20, 20),
    ("B", 19, 19),
    ("C", 2, 18),
    ("D", 1, 1),
    ("E", 0, 0),
]
```

도달 가능 개수는 `1/1/17/1/1`입니다. 연속이고 모든 수준이 도달 가능하며 C가 유일하게 넓다는 현재 assert만 만족합니다. 그러나 “자연 분할”은 아닙니다.

더 근본적으로:

- [standards.md:193](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:193>)과 코드는 C가 다른 수준보다 엄격히 넓어야 한다고 함
- [standards.md:223](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:223>)은 지필을 가능한 한 고르게 나누고 나머지를 C→A→B→D→E 순으로 준다고 함
- `R mod 5`가 0 또는 2~4이면 이 방식은 C와 다른 수준의 동률을 만들 수 있음

따라서 먼저 다음 중 하나를 정책으로 확정해야 합니다.

- 지필에서는 C 공동 최장을 허용하고 수준별 크기 차이를 1 이하로 강제
- 또는 C 유일 최장을 유지하되 “가능한 한 고르게”의 목적함수와 타이브레이크를 별도 알고리즘으로 정의

권장하는 첫 번째 선택의 붙여넣기 문구:

```text
지필평가는 다섯 수준의 점수 개수 차이가 1 이하가 되도록 분할한다.
C는 공동 최장인 것을 허용하되, C보다 더 넓은 다른 수준이 있어서는 안 된다.
수행평가는 기존대로 C가 다른 네 수준보다 엄격히 넓어야 한다.
```

검사는 다음처럼 나눌 수 있습니다.

```python
if floor == 0:
    assert max(counts.values()) - min(counts.values()) <= 1, \
        f"지필 구간이 자연 분할이 아님: {counts}"
    assert counts["C"] == max(counts.values()), \
        f"지필 C가 최장 구간이 아님: {counts}"
else:
    assert counts["C"] > max(counts[x] for x in "ABDE"), \
        f"C가 가장 넓지 않음: {counts}"
```

이 정책을 택하면 `R≥6`의 설명도 “수학적 최소”가 아니라 이 스킬의 고정 설계 정책인지 다시 정리해야 합니다.

---

# 3차 B·C급 회귀 일람

| 항목 | 판정 | 실행·원문 근거 |
|---|---|---|
| 중첩 표 `spans()` | 수정됨 | 깊이 3, T0~T13 모두 `span합 == rowCnt×colCnt`; 부모 span 보존 |
| `lineseg` 역전 | 수정됨 | `[3000,1000]` → `[ERR] 문단 내 lineseg 역전`, exit 1 |
| `charPr fontRef` | 수정됨 | 정상 full E2E PASS; 두 스타일을 모두 `5`로 바꾸면 정확 사전 불일치 FAIL |
| `figlib` 종료 0+손상 PNG | 수정됨 | `RuntimeError ... 정상 PNG가 아님`; 손상 PNG 삭제 확인 |
| ATTEMPT 확장 | 부분 | 과거 `과정에 오류`는 차단, `구했으나` 우회 및 정상 부정문의 오탐 남음 |
| 합계 행 정확 일치 | 수정됨 | `120점`, 중복, 비마지막 모두 FAIL |
| 지필 결론만 답안 귀속 | 수정됨 | 1점 또는 0점 중 요소별로 사전 확정 |
| R≥6·R=7 축소형 | 수정됨 | R=7 PASS, R=5 FAIL |
| 지필 자연 분할 | 문서 반영·게이트 미반영 | 현 20점 자연분할은 PASS하나 극단 분할도 PASS |
| F02 표현 | 부분 | 증상·지필 설명은 수정, `[수정]` 블록 연접형 단정 잔존 |
| F05 표현 | 수정됨 | 하한이 아니라 상한 판정, D 4~7 도달 가능 설명 정정 |
| examples 서두 | 수정됨 | “감사용 few-shot”, 복제 가능/금지/문체 표본 구분 |
| 구간 복제 지시 | 수정됨 | A·B 모두 새 문항에서 재계산하도록 명시 |
| 최저 급간 3행 | 문구 교체됨, 의미 회귀 실패 | 자수·종결은 정상이나 2점과 1점 겹침 재현 |
| D-2 접속 규칙 | 본문 수정됨 | 단수 고정 대신 바로 위 급간 범위로 결정 |
| B-6 자수 | 수정됨 | 20행: 최소 32, 중앙 42, 최대 46, 50자 초과 0 |
| G14 프로파일 분기 | 수정됨 | 수행 `s→1`, 지필 `s→0`, override 실제 LOW |
| 69키 설명 | 수정됨 | 실제 `SLOTS=87`, 일반 89; 예시 JSON 69 = 일반 65+특수 4 |
| `_alignment_note` | 수정됨 | 비인쇄 주석 키로 문서화, 실제 `std1_A` 문구와 정합 |
| SKILL description | 수정됨 | 수행·지필 및 지필/정기고사 트리거 포함 |
| `codex-review` 고정 문구 | 미수정 B | “포괄”만 요구하고 정확 문자열은 여전히 약함 |
| 내부 프로파일/표시명 분리 | 미수정 C | `item*_type`의 `정기시험/수행평가`와 내부 `지필평가/수행평가` 구분 미문서화 |

---

# 수선 에이전트가 보고한 잔여 2건 판정

## (가) F02 `[수정]`의 “반드시 연접형”

## 판정: 실제 B급 결함

현재 [failure-modes.md:65](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:65>)은:

> 최저 급간은 반드시 (ㄷ)의 연접 부정형으로 쓴다.

다음 줄도 “최저 급간을 연접형으로 고친다”고 단정합니다.

이는 같은 파일의 최종 프롬프트 [failure-modes.md:385](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:385>)와 권위 본문 [rubric-rules.md:220](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:220>)의 “바로 위 급간 범위에 따라 연접/이접 결정”과 직접 충돌합니다.

파일 첫머리가 `rubric-rules.md`를 권위 본문으로 지정해 피해를 줄이지만, `[수정]`은 에이전트가 실제로 복사할 블록이므로 단순 어조 문제가 아닙니다.

붙여넣기 가능한 교체:

```text
- (ㄴ) 두 갈래를 없애고 핵심 수행 n개의 `모두/일부/없음` 뼈대로 바꾼다.
  최저 급간은 시도 전제가 없는 부정형으로 쓰되, 접속은 바로 위 급간의
  범위로 정한다. 바로 위 급간이 한쪽 수행이나 일부 수행을 이미 포함하면
  연접형으로, `A는 수행했으나 B에 오류가 있음`에만 한정되면 이접형으로 쓴다.
  수행이 있었음을 전제하는 문장을 최저 급간에 쓰면 F02-(ㄷ) 결함이 생긴다.

- (ㄷ) 최저 급간에서 시도 전제를 없앤다.
  바로 위 급간이 부분 수행을 이미 포함하는 경우에는
  `세 비를 구하지 못하고 그 관계도 설명하지 못함.`처럼 연접형으로 쓴다.
  바로 위 급간이 한정형이면 남은 답안을 포괄하도록 이접형으로 쓴다.
```

## (나) B-6 문항 4 첫째 요소의 이접지

## 판정: 실제 A급 급간 중복

현재 문언:

- 2점: [examples-pizza.md:223](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:223>)
- 1점: [examples-pizza.md:224](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:224>)

실제 답안:

> 빅 한 판은 7.8125인분이다.  
> 16÷7.8125=2.048이므로 최소 3판이 필요하다.  
> 16명 필요 부피 6272cm³는 따로 쓰지 않았고 치즈 총량도 쓰지 않았다.

이 답안은:

- 최소 판 수는 옳고 치즈 총량이 빠졌으므로 2점 문언에 참
- 필요한 부피를 구하지 못했으므로 1점의 첫 이접지에도 참

따라서 실제 중복입니다. “높은 급간부터 적용”해 2점 하나를 선택할 수는 있지만, 두 진술이 동시에 참이라는 F01 배타성 결함이 없어지는 것은 아닙니다.

붙여넣기 가능한 교체:

```text
3점 — 몇 인분인지를 근거로 최소 판 수를 정하고 치즈의 총량을 옳게 구함.
2점 — 최소 판 수나 치즈 총량을 하나 이상 옳게 구하였으나 풀이가 완전하지 않음.
1점 — 최소 판 수를 구하지 못하고 치즈 총량도 구하지 못함.
```

---

# `examples-pizza.md`의 추가 급간 겹침

## 판정: 새 A급 결함 다수

교체한 세 최저 1점 행은 글자 수와 종결만 정상입니다. 의미상 배타성은 여전히 깨집니다.

### 문항 1 첫째 요소

학생 답안:

> 대응하는 모서리의 비가 모두 같으면 닮은 도형이고,  
> 서로 다른 비가 나오면 닮지 않는다.

실제 수치 비와 대상별 판별은 쓰지 않았습니다.

- 2점: “닮음을 판별하는 과정의 일부”를 옳게 수행
- 1점: “모서리 비를 구하지 못하고 닮음도 판별하지 못함”

실제 대상 판별을 안 했으므로 두 문언에 동시에 걸릴 수 있습니다.

### 문항 2 첫째 요소

학생 답안:

> ㉡은 한 변의 비만 곱해서 틀렸다.  
> 치즈 양은 한 변 비의 제곱만큼 바뀌어야 한다.

`9:16:25`, `90g`, `250g`은 쓰지 않았습니다.

- 2점: 치즈 양을 정하는 과정 일부 및 제곱 관계·㉡ 반박 수행
- 1점: 넓이의 비도 치즈 양도 구하지 못함

동시에 참입니다.

### 문항 3 첫째 요소

학생 답안:

> 8명에게 필요한 부피는 3136cm³이다.

세 피자의 부피, 부피의 비, 단위량당 값은 쓰지 않았습니다.

- 2점: 방안을 비교하는 계산 일부 수행
- 1점: 세 피자의 부피를 구하지 못했고 부피의 비도 나타내지 못함

동시에 참입니다.

### 문항 3 둘째 요소

학생이 작업 과정에서 방안은 골랐지만 제안서 안에는 주문 내용을 넣지 않은 경우:

- 2점: 방안은 골랐으나 제안서 조직에 일부 오류
- 1점: 제안서에 제안할 내용을 밝히지 못함

동시에 참입니다.

## 붙여넣기 가능한 전체 재작성안

4점 요소 세 개는 `3개 수행 중 3/2/1/0개`라는 한 축으로 다시 쓰는 것이 안전합니다.

```text
[문항 1 첫째 요소]
4점 — 모서리 비를 산출해 닮음을 판별하고 닮음비를 옳게 구함.
3점 — 모서리 비 산출, 닮음 판별, 닮음비 구하기 가운데 두 가지를 옳게 수행함.
2점 — 모서리 비 산출, 닮음 판별, 닮음비 구하기 가운데 한 가지를 옳게 수행함.
1점 — 모서리 비를 산출하지 못하고 닮음을 판별하지 못하며 닮음비도 구하지 못함.

[문항 2 첫째 요소]
4점 — 윗면 넓이의 비가 닮음비의 제곱임을 밝히고 치즈의 양과 ㉡의 잘못을 옳게 설명함.
3점 — 넓이비·제곱 관계, 치즈 양, ㉡ 반박 가운데 두 가지를 옳게 수행함.
2점 — 넓이비·제곱 관계, 치즈 양, ㉡ 반박 가운데 한 가지를 옳게 수행함.
1점 — 넓이비·제곱 관계를 밝히지 못하고 치즈 양도 구하지 못하며 ㉡도 반박하지 못함.

[문항 3 첫째 요소]
4점 — 부피의 비가 닮음비의 세제곱임을 밝히고 방안별 부피와 단위량당 값을 옳게 구함.
3점 — 부피비·세제곱 관계, 방안별 값, 단위량당 값 가운데 두 가지를 옳게 수행함.
2점 — 부피비·세제곱 관계, 방안별 값, 단위량당 값 가운데 한 가지를 옳게 수행함.
1점 — 부피비·세제곱 관계를 밝히지 못하고 방안별 값과 단위량당 값도 구하지 못함.

[문항 3 둘째 요소]
3점 — 필요한 양을 확인해 방안을 고르고 ㉠을 반박하여 제안서를 옳게 조직함.
2점 — 필요량 확인, 방안 선택, ㉠ 반박, 제안서 조직 가운데 일부만 옳게 수행함.
1점 — 필요량을 확인하지 못하고 방안도 고르지 못하며 ㉠ 반박과 제안서 작성도 하지 못함.

[문항 4 첫째 요소]
3점 — 몇 인분인지를 근거로 최소 판 수를 정하고 치즈의 총량을 옳게 구함.
2점 — 최소 판 수나 치즈 총량을 하나 이상 옳게 구하였으나 풀이가 완전하지 않음.
1점 — 최소 판 수를 구하지 못하고 치즈 총량도 구하지 못함.
```

이 문안은 적용 전에 반드시 각 원자 수행을 체크리스트로 정의하고 `2ⁿ` 답안 벡터를 다시 돌려야 합니다.

---

# 추가로 발견한 새 B·C 결함

## B — “높은 급간부터 대조”는 배타성의 근거가 될 수 없음

[rubric-rules.md:276](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:276>)은 어떤 답안도 두 급간에 동시에 걸리면 안 된다고 정의합니다. 그런데 [rubric-rules.md:281](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:281>)은 높은 급간부터 적용하는 순서를 “배타성의 근거”라고 부릅니다.

우선순위는 최종 점수를 하나로 고를 뿐, 두 술어가 동시에 참인 사실을 없애지 않습니다. 이 설명이 B-6의 실제 겹침을 정당화하는 데 쓰이고 있습니다.

교체안:

```text
### 판정 순서 규칙

급간은 배점이 높은 쪽부터 아래로 대조하고, 처음 참이 되는 급간으로 판정한다.
다만 이 순서는 경계 답안을 확인하는 절차일 뿐 문언상 겹침을 허용하는 규칙이 아니다.
한 답안이 두 급간 진술에 동시에 참이면, 높은 급간을 먼저 적용할 수 있더라도
F01 배타성 결함으로 판정하고 두 진술을 다시 쓴다.
```

## B — 워크플로의 truthy 불완전 응답 fail-open

`develop-draft.js`뿐 아니라 `verify-rubric.js`도 빈 객체를 모킹하면 통과합니다.

```text
초기 검증 하나 = {}
→ pass=true

재검증 하나 = {}
→ pass=true
```

스키마 강제 계약이 정상 작동하면 실제 발생 가능성은 낮지만, fail-closed라고 명시한 코드의 방어는 완성되지 않았습니다. 초기 검증은 `blocking/issues/fixes`, 재검증은 `real/blocking/reason`의 타입과 비어 있지 않은 문자열을 런타임에서도 확인해야 합니다.

## B — `develop-draft.js`가 감사용 예시를 계속 “완성 사례”라고 소개

- [examples-pizza.md:1](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:1>): 감사용 few-shot
- [develop-draft.js:36](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:36>): “완성 사례. 이 수준을 목표로 한다”

B-6에 실제 A급 중복이 남아 있어 무해한 표현 문제가 아닙니다.

교체안:

```javascript
· "${K}/examples/examples-pizza.md" — 감사용 few-shot.
  '복제 가능' 표시 블록만 문체·구조 본보기로 쓰고,
  '결함·복제 금지' 블록과 점수 구간 수치는 모방하지 말 것
```

## B — `codex-review.md`의 지필 고정 문구 검사가 아직 약함

[codex-review.md:73](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:73>)은 “무응답과 그 외의 오답을 포괄”하면 된다고 읽힙니다. 현 정책은 글자·띄어쓰기·마침표까지 정확히 같은 고정 문자열입니다.

교체안:

```text
지필평가: 각 요소에 0점 급간이 정확히 1건 있어야 하며,
진술은 글자·띄어쓰기·마침표까지 정확히
`무응답 또는 그 외의 오답.`이어야 한다.
각 요소의 급간은 배점 s부터 0까지 1씩 연속이어야 한다.
```

## B — `check_tpl2.py`가 고아 BinData를 전체 PASS에서 차단하지 않음

정상 그림 포함 E2E에서 새 그림은 3개인데 로그는 `BinData 5개`였습니다. 나머지 2개는 템플릿의 `image1.bmp`, `image2.bmp` 고아입니다. 별도 고아 제거 단계를 실행하면 없어지지만, 제거를 건너뛰어도 `check_tpl2.py`는 PASS합니다.

[hwpx-build.md:535](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:535>) 이후 수동 검사에만 의존합니다. 최종 승인 게이트라면 자동 차단하는 편이 맞습니다.

```python
_hpf_bindata = {
    e.attrib.get("id"): e.attrib.get("href")
    for e in _hpf_root.iter()
    if (
        e.tag.rsplit("}", 1)[-1] == "item"
        and (e.attrib.get("href") or "").startswith("BinData/")
    )
}

_used_bin_ids = set()
for _section_name in (
    n for n in z.namelist()
    if re.fullmatch(r"Contents/section\d+\.xml", n)
):
    _section_xml = z.read(_section_name).decode("utf-8")
    _used_bin_ids.update(
        re.findall(r'binaryItemIDRef="([^"]+)"', _section_xml)
    )

_orphan_ids = sorted(set(_hpf_bindata) - _used_bin_ids)
_orphan_files = sorted(
    n for n in z.namelist()
    if n.startswith("BinData/")
    and n not in set(_hpf_bindata.values())
)

if _orphan_ids or _orphan_files:
    errs += 1
    print(
        f"  [ERR] 고아 BinData: "
        f"등록 ID={_orphan_ids}, 미등록 파일={_orphan_files}"
    )
```

## C — 내부 프로파일명과 인쇄용 표시명 미분리

[hwpx-build.md:157](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:157>)은 `item*_type`을 `정기시험/수행평가`로 설명하고, 규칙 코드는 내부 식별자로 `지필평가/수행평가`를 씁니다.

현재 코드는 별도 `PROFILE`을 쓰므로 즉시 오작동하지 않지만, 표시값을 프로파일 분기에 재사용하면 오타·오분기가 생깁니다.

보완안:

```text
내부 프로파일 식별값은 `수행평가` 또는 `지필평가`로 고정한다.
`item*_type`에는 학교 서식에 인쇄할 표시명(`수행평가`, `지필평가`,
`정기시험`, `정기고사` 등)을 별도로 넣는다.
규칙 분기는 `item*_type`의 표시 문자열로 판정하지 않는다.
```

---

# 양 프로파일 E2E 결과

## 수행평가

입력: [valid-similarity-20pt.json](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:1>) 원본

- `rubric_rows`: 데이터 20행 + 합계 1행
- 그림은 정확한 예시 파일에 없으므로 자리표시 유지

실행:

```text
BUILD
  lineseg 917개
  SQUEEZE 다중줄 위반 0건

RESTYLE
  treatAsChar 해제 9건
  라벨 셀 재작성 52건

CHECK
  엔트리 13
  mimetype method=0
  testzip=None
  SQUEEZE 다중줄 문단 0건
  겹침 위험 문단 0건
  누락 줄 0
  비통일 charPr 0건
  PASS — 오류 0건 / 경고 2건
  exit=0

HWPX_BYTES=462349
```

구조·표·줄바꿈은 정상입니다. 다만 두 번째 경고가 그림 미포함이고 그것이 전체 PASS를 막지 않으므로 최종 완성본으로 승인할 수는 없습니다.

## 지필평가 변형

변형:

- `item1_type`~`item4_type`을 지필평가로 변경
- 6개 요소마다 `0 / 무응답 또는 그 외의 오답.` 행 추가
- 데이터 26행 + 합계 1행
- 성취수준을 `17~20 / 13~16 / 8~12 / 4~7 / 0~3`으로 자연 분할

실행:

```text
BUILD
  lineseg 929개
  SQUEEZE 다중줄 위반 0건

RESTYLE
  treatAsChar 해제 9건
  라벨 셀 재작성 52건

CHECK
  엔트리 13
  mimetype method=0
  testzip=None
  SQUEEZE 다중줄 문단 0건
  겹침 위험 문단 0건
  누락 줄 0
  비통일 charPr 0건
  PASS — 오류 0건 / 경고 2건
  exit=0

HWPX_BYTES=462618
```

지필에서 0점 행 여섯 개가 늘어나도 표 격자, 행 높이, restyle, 내용 보존, 세로 좌표는 깨지지 않았습니다.

## 정상 그림 포함 수행 E2E

```text
lineseg 920
SQUEEZE 0
restyle 9/52
누락 0
그림 선언·등록·PNG 확인 3건
비통일 charPr 0
겹침 0
PASS — 오류 0 / 경고 1
exit=0
```

따라서 최신 빌드의 조판 구조 자체는 양 프로파일과 정상 그림에서 작동합니다. 문제는 최종 승인 게이트가 그림 누락·구간 방향·few-shot 급간 겹침을 놓친다는 점입니다.

---

# 시행 전 필수 수정 목록

A급, 즉 시행 전에 반드시 닫아야 하는 것은 다음 세 가지입니다.

1. **최종 그림 fail-open 차단**
   - 최종 모드에서 그림 파일 누락을 빌드 단계 예외로 처리
   - `_figs` 미선언·미매핑 자리표시를 검증 오류로 승격
   - `--draft`에서만 경고 허용
   - 예시 JSON에 `_figs`와 실제 PNG 자산 동봉

2. **`check_levels`의 A→E 수치 방향 검사**
   - A 상한=총점
   - E 하한=0
   - A→E 점수 내림차순
   - 각 구간 `0 <= lo <= hi <= total`
   - `0 <= floor <= total`

3. **`examples-pizza.md` B-6 급간 재작성**
   - 문항 1·2·3 첫째 요소와 문항 3 둘째, 문항 4 첫째 요소 재작성
   - 한 요소 안에서는 수행 개수라는 한 축만 사용
   - `2ⁿ` 벡터 및 실제 학생 답안으로 겹침·공백 재검
   - 통과하기 전까지 B-6을 “복제 가능” 목록에서 제거

A급을 닫은 뒤, 회귀 안정성을 위해 다음 B급도 함께 고치는 것이 좋습니다.

4. ATTEMPT의 `했으나` 우회 및 `일부를/시도하지 못함` 오탐 수정  
5. 지필 자연 분할 정책의 C 동률 처리 확정 및 코드·verify 프롬프트 동기화  
6. `develop-draft.js`와 `verify-rubric.js`의 truthy 불완전 객체 런타임 검증  
7. F02 `[수정]` 블록의 연접형 단정 제거  
8. 높은 급간 우선 적용을 배타성의 대체물로 설명한 문구 수정  
9. 고아 BinData 자동 차단  
10. `codex-review.md`의 지필 0점 정확 문자열 요구 강화  

최종 재검 세트에는 최소한 다음이 포함돼야 합니다.

- 그림 정상 / `_figs` 생략 / HPF 누락 / ZIP 누락 / 내장 손상 / ID 중복
- 수행 정상 / 지필 정상 / 학교 override low0 / 키 오타 / 0행 누락 / 문구 변형
- 성취수준 이름 swap / bounds swap / C 비최대 / 도달 불가 / 지필 극단 불균형
- B-6 모든 원자 수행의 `2ⁿ` 벡터와 실제 답안
- 초안·검증·재검의 `null`·`{}`·필수 필드 누락
- 수행·지필 모두 `rubric_check → build → restyle → 고아 제거 → check_tpl2`
- 최종 경고는 문서가 허용한 서식 원본 폭 초과 1건만

**최종 결론: 현재 상태는 시행 보류입니다.** 양 프로파일의 기본 조판과 기존 A급 반례 상당수는 실제로 고쳐졌지만, 최종 승인 게이트와 복제용 예시에 A급 false-pass가 남아 있습니다.
