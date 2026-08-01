# 종합 판정

**시행 보류**입니다.

두 기본 프로파일의 핵심 분기 자체는 실제로 반영되어 있고, `rubric-rules.md`의 검사 코드는 수행평가와 지필평가 양쪽 정상 입력에서 실제로 통과했습니다. 그러나 다음 A급 결함 때문에 현재 패키지를 그대로 “검증 완료·시행 가능”으로 승인할 수 없습니다.

- `check_tpl2.py`가 `section0.xml`에 그림 ID 문자열만 있으면, 실제 `content.hpf` 등록과 `BinData`가 전혀 없어도 **PASS**합니다.
- `develop-draft.js`는 실패 초안이 `null`이어도 `{key, angle}` 객체로 살아나 **`pass:true`**가 됩니다.
- 학교 규정 우선 원칙을 선언했지만, 검사기는 수행/지필 두 고정 프로파일만 허용하여 규정이 다를 때 규정을 지키면서 검사를 통과할 방법이 없습니다.
- `failure-modes.md` 최종 프롬프트는 지필 필수 0점 문구를 요구하는 동시에 모든 급간을 `ㅁ` 받침으로 검사하여, 올바른 지필표도 문자 그대로는 반드시 실패합니다.
- `verify-rubric.js`가 수행평가 성취수준의 “각 A~E 수준에 도달 가능 점수가 최소 1개” 조건을 명확히 강제하지 않고, 최초 에이전트의 `blocking` 오분류를 재검하지 않아 실제 A급 결함도 통과할 수 있습니다.

감사 중 파일은 수정하지 않았습니다.

## 감사 범위와 실행 증거

요청하신 범위인 `SKILL.md`, `references/*.md` 7개, `examples/*` 2개, `tools/*.py` 6개, `workflows/*.js` 2개, 총 18개 파일을 모두 원문 끝까지 직접 읽고 SHA-256으로 스냅샷을 고정했습니다.

실행한 핵심 반증은 다음과 같습니다.

- `rubric-rules.md` §7 코드를 문서에서 직접 추출:
  - 수행평가, 원본 예시: `PASS — 요소 6개 / 데이터 20행 / 총점 20점`
  - 지필평가, 요소마다 고정 0점 행 추가: `PASS — 요소 6개 / 데이터 26행 / 총점 20점`
  - 지필평가, 1점 요소 포함: `PASS — 요소 7개 / 데이터 27행 / 총점 20점`
  - 지필 데이터를 0점 행 없이 실행: 종료 코드 1
- `standards.md`의 `check_levels` 직접 추출:
  - 수행 도달 가능형 구간: `True`
  - 지필 0~20 자연 분할: `True`
  - 수행 결함 구간 `E 0~3`, floor=6: `AssertionError`
  - A~E가 아닌 단일 구간, `R<10`, A/E 라벨 역전은 모두 잘못 `True`
- 두 JS 파일을 `AsyncFunction` 본문으로 파싱: 둘 다 구문 통과
- `develop-draft.js`에서 둘째 초안 에이전트를 `null`로 모킹: `drafts[1]={key,angle}`, 최종 `pass:true`
- `verify-rubric.js`에서 검증 에이전트 하나를 `null`로 모킹: 정상적으로 `throw`
- `verify-rubric.js`에서 `issues="A 시행 전 필수 결함"`, `blocking=false`, 재검 `real=true`: 잘못 `pass:true`
- `check_tpl2.py`:
  - `testzip()`이 손상 엔트리를 반환하면 FAIL/종료 1
  - 존재하지 않는 HWPX로 비처리 예외 발생 시 FAIL footer/종료 1
  - 외부 PNG와 XML의 그림 ID만 있고 내부 `BinData`가 없는 반례는 잘못 PASS
  - `vertpos=[3000,1000]`인 문단 내부 역전은 잘못 PASS
  - 실제 `tpl2`의 깊이 3 중첩 표에서 부모 `addr/span`을 잃는 반례 재현
- `py_compile.compile(..., doraise=True)`:
  - `check_tpl2.py`, `build_tpl2.py`, `figlib.py`, `img_embed.py`, `metrics.py`, `restyle.py` 모두 구문 통과
  - 읽기 전용 환경이므로 `.pyc` 쓰기 함수만 무출력으로 대체했습니다. 컴파일러의 파싱·바이트코드 생성 단계 자체는 실제 실행했습니다.

---

# 갈래 1 — 평가 유형 프로파일 분기

## 1. `SKILL.md` 원칙 2·0단계·3단계

**확인 결과: 반영됨. 단, 학교 규정 우선의 실행 경로는 미반영.**

정상 반영 근거:

- [SKILL.md:13](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:13>)은 수행평가의 `0점 없음·최저 1점·백지 포괄·요소 2점 이상`과 지필평가의 `0점·고정 진술·1점 요소 허용`을 모두 정확히 구분합니다.
- [SKILL.md:46](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:46>)은 0단계에서 평가 유형을 받습니다.
- [SKILL.md:47](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:47>)은 학교 규정이 다르면 규정이 우선한다고 명시합니다.
- [SKILL.md:66](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:66>)과 [SKILL.md:69](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:69>)은 3단계 급간 작성도 프로파일별로 구분합니다.

### A — 학교 규정 우선 원칙이 검사 코드에서는 실행 불가능

상위 정책은 규정 우선을 선언하지만:

- [rubric-rules.md:449](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:449>)은 `PROFILE`을 수행/지필 두 값으로만 제한합니다.
- [rubric-rules.md:450](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:450>)은 `LOW`, `MINS`, `ZERO_DESC`를 프로파일 이름에서 고정 파생합니다.
- [standards.md:232](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:232>)도 수행이 아니면 모두 floor=0으로 처리합니다.
- [verify-rubric.js:14](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:14>)과 [failure-modes.md:383](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:383>)도 둘 중 하나만 선택하게 합니다.

예를 들어 학교 규정이 “수행평가에도 요소별 0점 급간을 둔다”고 하면, 규정을 지키면 수행 프로파일 검사에서 실패하고, 지필로 거짓 지정해야 통과합니다.

붙여넣기 가능한 공통 정책·검사 수정안:

```python
DEFAULT_RULES = {
    "수행평가": {
        "low": 1,
        "min_element": 2,
        "zero_desc": None,
    },
    "지필평가": {
        "low": 0,
        "min_element": 1,
        "zero_desc": "무응답 또는 그 외의 오답.",
    },
}

PROFILE = "수행평가"       # 문서에 표시할 평가 유형
SCHOOL_OVERRIDE = {}       # 학교 규정이 다를 때만 채움
# 예: {"low": 0, "min_element": 1,
#      "zero_desc": "무응답 또는 그 외의 오답."}

assert PROFILE in DEFAULT_RULES
RULE = {**DEFAULT_RULES[PROFILE], **SCHOOL_OVERRIDE}

LOW = int(RULE["low"])
MINS = int(RULE["min_element"])
ZERO_DESC = RULE.get("zero_desc")

# 프로파일 이름이 아니라 실제 적용 급간으로 행 수를 계산한다.
need = sum(v[0] - LOW + 1 for v in el.values())

# 성취수준 floor도 프로파일 이름이 아니라 실제 요소별 최저 급간의 합으로 계산한다.
submitted_floor = sum(min(v) for v in el.values())
```

검증 프롬프트에는 다음을 추가해야 합니다.

```text
[학교 학업성적관리규정 오버라이드]
<없음 | 최저 급간·0점 문구·요소 최소 배점·미응시 점수·성취수준 처리의 확정값>

오버라이드가 없을 때만 수행평가·지필평가 기본 프로파일을 적용한다.
오버라이드가 있으면 먼저
`항목 | 기본 프로파일 | 학교 규정 | 실제 적용값`
표를 작성하고, 모든 급간 수·행 수·최저 총점·성취수준 검사를 실제 적용값으로 수행한다.
```

### C — 스킬 메타데이터는 여전히 수행평가만 설명

[SKILL.md:3](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:3>)은 `서·논술형(수행평가)`만 기술하여 지필 요청의 라우팅 가능성을 약화합니다.

붙여넣기 가능한 수정안:

```yaml
description: 중등 수학 서·논술형(수행평가·지필평가) 문항과 채점기준표를 개발한다. 성취기준·평가요소를 입력받아 전이가 높은 문항 초안을 여러 개 제안하고, 고른 초안을 평가 유형별 채점 요소·급간별 수행 수준까지 완성해 HWPX 서식으로 조판한다. 트리거 — "서논술형 문항 만들어줘", "수행평가 문항 개발", "지필평가 서논술형 문항", "정기고사 서술형 문항", "채점기준표 만들어줘", "논술형 평가 도구", "성취기준으로 문항 개발".
```

---

## 2. `references/rubric-rules.md` §1~§7

**확인 결과: 핵심 분기는 반영됨. 검사 코드에는 잔여 우회가 있음.**

정상 반영 근거:

- [rubric-rules.md:24](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:24>)∼32: 수행 데이터 행=총점, 지필 데이터 행=총점+요소 수.
- [rubric-rules.md:68](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:68>)∼76: 두 프로파일의 최저 급간·요소 최소 배점·행 수·floor·성취수준 분기.
- [rubric-rules.md:80](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:80>): 요구한 인과인 “0점 급간을 없앴기 때문에 floor=n, 0~n−1 미응시 전용”이 정확히 들어갔습니다.
- [rubric-rules.md:101](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:101>)∼118: 지필 0점 고정 문구, 1점 요소 허용, 행 수 공식.
- 실제 실행에서도 수행 20행, 지필 26행, 지필 1점 요소 포함 27행이 모두 통과했습니다.

### B — 수행 최저 급간의 “시도 전제” 검사가 우회됨

[rubric-rules.md:550](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:550>)의 정규식은 다음 반례를 잡지 못합니다.

```text
세 비를 구하는 과정에 오류가 있고 그 관계를 설명하지 못함.
```

백지는 “구하는 과정”도 그 “과정의 오류”도 없으므로 이 진술에 해당하지 않지만, `못함`이 하나 있다는 이유로 검사 11을 통과했습니다.

붙여넣기 가능한 수정안:

```python
ATTEMPT = (
    r"(려\s*하였으나|하였으나|했지만|"
    r"시도(?:하였으나|했으나)?|"
    r"일부(?:를|만)|"
    r"(?:구하|설명하|판단하|작성하)는\s*과정(?:에|에서).*(?:오류|잘못)|"
    r"오류가\s*(?:있|남))"
)
```

정규식만으로 의미 포괄성을 완전 검증할 수 없으므로 수기 체크에는 다음도 추가해야 합니다.

```text
□ 수행평가의 각 1점 진술에 실제 백지·완전 오답을 대입했을 때 진술이 참인가.
  단순히 부정 술어가 있다는 이유만으로 통과시키지 않는다.
```

### B — 합계 행 검사가 부분 문자열과 중복을 허용

[rubric-rules.md:495](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:495>)은 `str(TOTAL) in score`만 확인합니다. 따라서 총점 20에서 `"120점"`도 통과하고 합계 행이 두 개여도 첫 행만 검사합니다.

붙여넣기 가능한 수정안:

```python
if len(tot) != 1:
    fail.append(f"5 합계 행 개수 {len(tot)} ≠ 1")
elif rows[-1] is not tot[0]:
    fail.append("5 합계 행이 마지막 원소가 아님")
elif tot[0]["score"] != f"{TOTAL}점":
    fail.append(f"5 합계 행 점수 {tot[0]['score']!r} ≠ {TOTAL}점")
```

### B — 지필 “결론만 쓴 답안”을 일괄 0점으로 지정

[rubric-rules.md:279](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:279>)∼285는 지필에서 백지와 “결론만 쓰고 근거 없음”을 모두 0점이라고 읽히게 합니다. 그러나 [rubric-rules.md:199](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:199>)∼206의 지필 1점 급간은 시도·부분 수행을 허용하므로, 결론만 쓴 답안이 요소에 따라 1점일 수 있습니다.

붙여넣기 가능한 수정안:

```text
수행평가에서는 백지·전무 답안이 최저 1점에 걸려야 한다.
지필평가에서는 백지만 고정 0점 급간에 걸려야 한다.
결론만 쓴 답안은 해당 요소의 1점 진술이 이를 포함하는지 먼저 판정한다.
포함하면 1점, 포함하지 않으면 높은 급간부터 대조한 뒤 0점으로 가되,
어느 쪽인지 요소별로 명시하여 채점자 해석에 맡기지 않는다.
```

[rubric-rules.md:603](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:603>)의 수기 체크도 다음으로 교체해야 합니다.

```text
□ 결론만 쓰고 근거가 없는 답안의 귀속이 프로파일과 요소별 1점 진술에 따라 하나로 확정되는가
  (수행: 최저 1점 포괄, 지필: 1점 또는 0점 중 하나로 명시)
```

---

## 3. `references/standards.md` §4.2·§4.3와 `check_levels`

**확인 결과: 프로파일 본문은 반영됨. 검사 코드와 저총점 절차는 부분 반영.**

정상 반영 근거:

- [standards.md:197](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:197>)∼209: 수행 floor=n, 0~n−1 미응시·미제출 전용.
- [standards.md:211](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:211>): 지필 floor=0, 0~총점 분할.
- [standards.md:213](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:213>): 각 A~E 수준이 도달 가능 점수를 최소 하나 포함.
- 대표 수행 결함 구간은 실제 `check_levels`가 거부했습니다.

### B — `R ≥ 10`이 10점·12점 권장표와 충돌

[standards.md:219](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:219>)은 `R<10`이면 C를 가장 넓게 한 5수준 구간을 만들 수 없다고 단정합니다. 그러나:

- 수행 10점·요소 4개면 floor=4, R=7입니다.
- A 10 / B 9 / C 6~8 / D 5 / E 0~4로 나누면 도달 가능 개수는 1/1/3/1/1이고 모든 수준이 도달 가능하며 C가 가장 넓습니다.
- [rubric-rules.md:132](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:132>)∼136은 10점·12점 수행평가 배분을 권장합니다.

즉 `R≥10`은 “권장 폭 A≥2/B=2/D=2”에서 나온 선택값이지 수학적 필요조건이 아닙니다.

붙여넣기 가능한 수정안:

```text
3. `R ≥ 6`인지 확인한다. 다섯 수준에 도달 가능 점수를 하나씩 두고 C를 다른 수준보다 넓게 하려면 최소 배분은 A 1 / B 1 / C 2 / D 1 / E 1이므로 최소 R은 6이다.
4. R이 6~9이면 A 1 / B 1 / C 나머지 / D 1 / E 1의 축소형을 사용한다. R이 10 이상이면 A 2~3 / B 2 / C 나머지 / D 2 / E 1~2를 권장형으로 사용한다.
```

### B — 지필 “자연 분할”과 §4.3의 수행형 권장 폭이 구분되지 않음

[standards.md:211](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:211>)은 지필을 0~총점 자연 분할한다고 하지만, [standards.md:220](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:220>)의 `A 2~3 / B 2 / C 나머지 / D 2 / E 1~2`는 수행 전용이라고 표시되지 않았습니다. 20점 지필에 그대로 적용하면 C가 과도하게 넓은 구간이 되어 “자연 분할”과 어긋납니다.

붙여넣기 가능한 수정안:

```text
4. 수행평가는 도달 가능 범위 floor~총점에 위 권장 폭을 적용한다.
   지필평가는 floor=0이므로 0~총점의 점수 개수를 다섯 수준에 가능한 한 고르게 배분하되,
   나머지 점수는 먼저 C에 주어 C가 가장 넓도록 하고, 이후 A·B·D·E 순으로 배분한다.
```

### B — `check_levels`가 A~E의 존재·프로파일 오타·C 폭을 검사하지 않음

[standards.md:225](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:225>)∼241의 코드에 다음 우회가 있습니다.

- `[("E",0,20)]` 한 구간만 주어도 `True`
- `PROFILE="수행 평가"`처럼 오타가 나면 지필로 간주
- A와 E 라벨을 뒤집어도 `True`
- 본문이 요구하는 R 최소값과 C 최장 조건을 검사하지 않음

붙여넣기 가능한 교체안:

```python
PROFILE = "수행평가"
assert PROFILE in ("수행평가", "지필평가")

def check_levels(levels, total, floor):
    # levels: [("A", lo, hi), ..., ("E", lo, hi)]
    assert [name for name, _, _ in levels] == list("ABCDE"), \
        "수준은 A,B,C,D,E가 이 순서로 정확히 한 번씩 있어야 함"

    R = total - floor + 1
    assert R >= 6, \
        f"도달 가능 점수 {R}개로 C가 가장 넓은 5수준을 만들 수 없음"

    xs = sorted(levels, key=lambda t: t[1])
    assert xs[0][1] == 0, "최저 수준의 하한이 0이 아님"
    assert xs[-1][2] == total, "최고 수준의 상한이 총점이 아님"

    for a, b in zip(xs, xs[1:]):
        assert a[2] + 1 == b[1], f"구간 불연속/중복: {a} {b}"

    counts = {}
    for name, lo, hi in levels:
        counts[name] = sum(s >= floor for s in range(lo, hi + 1))
        assert counts[name] > 0, \
            f"{name} 수준에 도달 가능 점수가 없음 ({lo}~{hi}, floor={floor})"

    assert counts["C"] > max(counts[x] for x in "ABDE"), \
        f"C가 가장 넓지 않음: {counts}"

    return True
```

호출 시에는 프로파일 이름에서 floor를 다시 추정하지 말고 실제 급간으로 계산한 값을 넘겨야 합니다.

```python
floor = sum(min(scores) for scores in element_score_sequences)
check_levels(levels, total, floor)
```

---

## 4. `references/failure-modes.md` F02·F05·검증 프롬프트

**확인 결과: 부분 반영, 새 모순 있음.**

### F02 프로파일 분기

[failure-modes.md:53](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:53>)은 수행 백지→1점, 지필 백지→0점을 올바르게 구분합니다.

그러나 잔여 문제가 있습니다.

### B — 수행평가에서 F02-(ㄷ)이 “반드시 발생”한다고 단정

[failure-modes.md:61](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:61>)은 다음처럼 씁니다.

> 0점 급간을 제거한 수행평가 프로파일에서는 (ㄷ)이 반드시 발생한다.

시도 전제가 있는 최저 급간에서만 발생하며, 올바른 부정형이 백지까지 포괄하면 발생하지 않습니다.

붙여넣기 가능한 수정안:

```text
0점 급간을 제거한 수행평가 프로파일에서 최저 1점 진술이 시도·부분 수행을 전제하면 (ㄷ)이 반드시 발생한다. 시도를 전제하지 않는 부정형 진술이 백지·완전 오답을 포괄하면 (ㄷ)은 발생하지 않는다.
```

### B — 지필에서 1점 급간을 0점 급간으로 “대신”한다는 표현

[failure-modes.md:66](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:66>)은 “연접형 최저 1점 급간 대신 0점 급간을 둔다”고 씁니다. 문자 그대로 1점 행을 없애면 지필의 `s→…→1→0` 연속 수열과 충돌합니다.

붙여넣기 가능한 수정안:

```text
지필평가 프로파일에서는 1점 급간을 시도·부분 수행 답안의 급간으로 유지하고, 그 아래에 0점 급간을 추가한다. 0점 진술은 "무응답 또는 그 외의 오답."으로 고정한다.
```

### B — F05 증상 정의의 하한/상한 역전

- [failure-modes.md:98](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:98>)은 “구간 하한이 floor보다 낮으면 결함”이라고 씁니다.
- [failure-modes.md:106](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:106>)은 올바르게 “판정 기준은 상한이며 하한이 낮은 것만으로는 결함이 아니다”라고 씁니다.
- [failure-modes.md:102](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:102>)은 최저 제출 학생이 C라고 하지만 floor=6이면 D 4~7의 6·7점에 들어가므로 최저 제출자는 D입니다.

붙여넣기 가능한 교체문:

```text
**[증상]** 성취수준 A~E 가운데 어떤 구간의 상한이, 답안을 제출한 학생이 실제로 받을 수 있는 최저 총점보다 낮아 도달 가능한 점수를 하나도 포함하지 못한다. 최하위 E의 하한을 0으로 두는 것 자체는 결함이 아니다.

**[실제 사례 문장]** 요소 6개·최저 급간 1점이면 제출자의 최저 총점은 6점이다. 따라서 E 0~3점은 구간 전체가 도달 불가능했다. D 4~7점의 4·5점도 나올 수 없지만 D 자체는 6·7점을 포함하므로 도달 가능한 수준이었다.

**[왜 위험한가]** E가 제출 답안을 진단하는 기능을 잃는다. 가장 낮은 제출 점수 6점의 학생은 D에 배치되고 E에는 어떤 제출자도 배정되지 않는다.
```

### B — 검증 프롬프트가 모든 수행 최저 급간을 “연접형”으로 강제

[failure-modes.md:385](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:385>)∼386은 1점 급간이 “연접 부정형”인지 확인하라고 합니다. 그러나 권위 본문인 [rubric-rules.md:208](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:208>)∼215는 바로 위 급간의 범위에 따라 연접/이접을 정하라고 합니다.

붙여넣기 가능한 수정안:

```text
· 수행평가: 0점 급간 0건, 요소마다 최저 급간 1점. 각 요소의 1점 급간이 시도를 전제하지 않는 부정형이며 백지·완전 오답을 포괄하는지 확인하라. 접속은 일률적으로 연접형을 요구하지 말고, 바로 위 급간이 한쪽 수행·부분 수행을 이미 포함하면 연접형, 바로 위 급간이 A 수행+B 오류에만 한정되면 이접형으로 정한다.
```

### A — 지필 고정 0점 문구와 시험 11의 `ㅁ` 받침 검사가 충돌

- [failure-modes.md:387](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:387>)은 `무응답 또는 그 외의 오답.`을 요구합니다.
- [failure-modes.md:471](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:471>)은 모든 급간 종결을 `ㅁ` 받침으로 검사합니다.
- `답`의 종성은 `ㅂ`이므로 올바른 지필 0점 행이 반드시 실패합니다.

붙여넣기 가능한 수정안:

```text
지필평가의 0점 행은 진술이 정확히 "무응답 또는 그 외의 오답."인지 검사하고, 글자 수 권장 범위와 명사형 어미 ㅁ 받침 검사에서는 제외하라. 나머지 급간 진술만 마지막 음절의 받침이 ㅁ인지 확인하라.
```

---

## 5. `references/hwpx-build.md` R11~R13

**확인 결과: 반영됨 — 이상 없음.**

- [hwpx-build.md:308](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:308>): 수행은 1점, 지필은 0점까지 1씩 하강.
- [hwpx-build.md:311](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:311>): 수행 0점 없음·1점 요소 통합, 지필 0점 고정·1점 요소 허용·총점+요소 수.
- [hwpx-build.md:313](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:313>): 수행 최저 급간만 시도 전제 금지.
- [hwpx-build.md:315](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:315>): 접속은 급간 단수가 아니라 바로 위 급간 내용으로 결정.

### C — 내부 프로파일 명칭과 인쇄용 평가 유형 명칭이 다름

[hwpx-build.md:157](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:157>)은 `정기시험/수행평가`, 다른 파일은 `지필평가(정기고사)`를 씁니다.

붙여넣기 가능한 수정안:

```text
내부 프로파일 식별값은 `수행평가` 또는 `지필평가`로 고정한다. `item*_type`에는 학교 서식이 요구하는 인쇄용 명칭(`수행평가`, `지필평가`, `정기시험`, `정기고사` 등)을 별도로 넣는다. 내부 프로파일 분기는 `item*_type`의 표시 문자열로 판정하지 않는다.
```

---

## 6. `examples/examples-pizza.md`

**확인 결과: 프로파일 설명은 반영됐으나, few-shot 내부에 새 모순이 남음.**

- [examples-pizza.md:11](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:11>)과 [examples-pizza.md:367](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:367>)은 수행/지필 분기를 올바르게 설명합니다.

### B — “완성·검증된 사례”와 실제 결함 사례가 공존

[examples-pizza.md:1](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:1>)은 두 사례가 “완성·검증을 마쳤고 그대로 복제”할 수 있다고 합니다. 그러나:

- [examples-pizza.md:13](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:13>)∼15는 사례 A 성취수준이 결함이라고 명시합니다.
- [examples-pizza.md:275](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:275>)는 사례 B의 4점 요소 세 개에 급간 겹침이 있다고 스스로 인정합니다.

붙여넣기 가능한 서두 수정안:

```text
이 문서는 확정 수치와 문체 예시, 그리고 개발 중 발견된 결함 실물을 함께 싣는 감사용 few-shot이다. ‘복제 가능’이라고 표시한 블록만 새 문항의 본보기로 사용하고, ‘결함·복제 금지·문체 표본’ 블록은 채점 구조와 성취수준 구간의 본보기로 사용하지 않는다.
```

명백한 세 최저 급간은 최소한 다음처럼 바꿔야 합니다.

```text
대응하는 모서리의 비를 구하지 못하고 닮음도 판별하지 못함.
윗면 넓이의 비를 구하지 못하고 치즈의 양도 구하지 못함.
세 피자의 부피를 구하지 못하고 부피의 비도 나타내지 못함.
```

교체 후에는 모든 3점 요소까지 F01의 `2ⁿ` 벡터 검사를 다시 돌려야 합니다.

### B — 접속을 급간 단수로 고정

[examples-pizza.md:267](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:267>)∼273은 4단=연접, 3단=이접으로 가르칩니다. 이는 `rubric-rules.md` §3과 정면충돌하며, 같은 파일의 A-6에도 연접형 3단 요소가 있습니다.

붙여넣기 가능한 교체안:

```text
접속은 급간 단수로 고정하지 않는다. 바로 위 급간이 A만 수행하거나 일부 수행한 답안을 이미 포함하면 최저 급간은 `A도 하지 못하고 B도 하지 못함`의 연접형으로 쓴다. 바로 위 급간이 `A는 수행했으나 B에 오류가 있음`에만 한정되면 최저 급간은 나머지를 포괄하는 이접형으로 쓴다. 모든 요소는 바로 위 급간과 최저 급간을 한 쌍으로 놓고 겹침·공백 답안을 직접 시험한다.
```

### B — 사례 B의 점수 구간을 복제하라는 지시

[examples-pizza.md:15](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:15>)은 사례 B 구간을 복제하라고 하지만, [standards.md:250](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:250>)은 예시에서 복사하지 말고 재계산하라고 합니다.

붙여넣기 가능한 수정안:

```text
사례 A의 구간은 복제하지 않는다. 사례 B의 구간도 총점 20점·요소 6개·최저 급간 1점이 모두 같은 경우의 검산값일 뿐이다. 새 사례에서는 총점·요소 수·요소별 최저 급간으로 floor를 다시 계산하여 standards.md §4.3에 따라 A~E를 재분할한다.
```

---

## 7. `workflows/verify-rubric.js`

**확인 결과: 프로파일 급간 구조는 반영됐으나, 검증 프롬프트는 부분 반영.**

정상 반영:

- [verify-rubric.js:47](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:47>)은 수행 백지→1점, 지필 고정 0점을 구분합니다.
- [verify-rubric.js:53](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:53>)은 수행 s→1, 지필 s→0과 지필 행 수를 구분합니다.

### A — 수행 성취수준 재분할 조건이 약함

[verify-rubric.js:65](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:65>)은 하단이 미응시 전용이라는 점이 “처리”됐는지만 묻습니다. 결함인 `E 0~3, floor=6`도 “미응시 전용으로 설명했다”고 통과시킬 여지가 있습니다. 또한 필독 목록에 `standards.md`가 없습니다.

붙여넣기 가능한 추가:

```javascript
· "${K}/references/standards.md" — 성취수준 점수 구간과 평가 유형별 floor 계산.
```

성취수준 문구 교체안:

```text
2. 성취수준 구간 — A~E가 0점부터 총점까지 겹침 없이 빠짐없이 덮는가. 수행평가는 실제 요소별 최저 급간의 합 floor를 계산하고, 도달 가능 범위 floor~총점의 각 점수를 A~E로 재분할하여 다섯 수준이 모두 도달 가능 점수를 최소 1개 포함하는지 확인하라. 0~floor−1은 E의 하한을 0으로 확장하여 흡수하되, E의 상한은 반드시 floor 이상이어야 한다. 지필평가는 기본 floor=0이므로 0~총점을 다섯 수준으로 분할하고 각 수준이 최소 1점을 포함하는지 확인하라.
```

### B — 요소 최소 배점이 프롬프트에 명시되지 않음

붙여넣기 가능한 추가:

```text
수행평가의 요소 최고 배점은 2~4점, 지필평가는 1~4점이어야 한다. 수행평가의 1점 요소와 두 프로파일 모두의 5점 이상 요소를 차단하라.
```

### B — 최초 에이전트의 `blocking` 오분류를 그대로 신뢰

[verify-rubric.js:107](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:107>)은 최초 `blocking`과 재검 `real`이 모두 참일 때만 차단합니다. 실제로 `issues="A 시행 전 필수 결함"`, `blocking=false`, `real=true`를 넣었더니 `pass:true`였습니다.

붙여넣기 가능한 수정안:

```js
// 재검증 스키마
required: ['real', 'blocking', 'reason'],
properties: {
  real: { type: 'boolean' },
  blocking: {
    type: 'boolean',
    description: '실제 결함이며 시행 전 필수 수정이면 true',
  },
  reason: { type: 'string' },
}
```

```js
const confirmed = verdicts.filter(
  v => v.verdict.real && v.verdict.blocking
)
```

가장 안전한 형태는 `issues`를 문자열이 아니라 이슈 배열로 만들고 각 이슈의 `severity: A|B|C`를 따로 재검하는 것입니다.

---

## 8. `references/codex-review.md`

**확인 결과: 부분 반영.**

[codex-review.md:73](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:73>)은 두 프로파일을 구분하지만, 지필 0점 문구를 “무응답과 그 외의 오답까지 포괄”한다고만 씁니다. 이는 고정 문자열 정책보다 약합니다.

### B — 지필 고정 문자열 요구 약화

붙여넣기 가능한 수정안:

```text
지필평가: "이 평가는 지필평가이므로 각 요소에 0점 급간이 정확히 1건 있어야 하며, 진술은 글자·띄어쓰기·마침표까지 정확히 `무응답 또는 그 외의 오답.`이어야 한다. 각 요소의 급간은 배점 s부터 0까지 1씩 연속이어야 하고, 데이터 행 수는 총점+요소 수여야 하며, 1점 요소를 허용한다."
```

---

## 9. 범위 전체의 추가 프로파일 모순

### B — `transfer-and-numbers.md` G14가 수행평가로 고정

[transfer-and-numbers.md:348](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:348>)은 다음처럼 프로파일 구분 없이 씁니다.

> 요소별 급간이 배점부터 1까지 1씩 하강

붙여넣기 가능한 수정안:

```text
| G14 | 배점 합계·급간 수 | 문항 배점 합 = 총점. 수행평가는 요소별 급간이 배점부터 1까지, 지필평가는 배점부터 0까지 1씩 하강하며, 학교 규정 오버라이드가 있으면 실제 적용 최저 급간까지 하강 |
```

---

# 갈래 2 — 2차 감사 반영 확인

## 1. `tools/check_tpl2.py`

### 1-a. B-9 `testzip()` 오류 집계

**확인 결과: 반영됨 — 이상 없음.**

[check_tpl2.py:60](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:60>)∼65에서 `testzip()` 반환값이 `None`이 아니면 `errs += 1` 합니다.

실제 인메모리 손상 Zip 반례 결과:

```text
[ERR] ZIP 손상 엔트리: BinData/bad.png
FAIL — 오류 1건
종료 코드 1
```

### 1-b. A-3 그림 게이트

**확인 결과: 부분 반영 + A급 false-pass.**

반영된 부분:

- [check_tpl2.py:216](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:216>)∼228:
  - `_figs` 원본 파일 존재·8바이트 PNG 서명 확인
  - `_fid`가 `section0.xml`에 있는지 확인
- [check_tpl2.py:232](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:232>)∼237:
  - `_figs` 미선언과 자리표시 잔존 경고

### A — 실제 HWPX 내부 PNG가 없어도 PASS

현재는 외부 PNG와 XML의 `binaryItemIDRef`만 봅니다. `content.hpf` 등록, 실제 ZIP 엔트리, 내장 PNG 서명은 전혀 확인하지 않습니다. [check_tpl2.py:229](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:229>)의 BinData 개수는 출력만 합니다.

실제 반례:

```text
_figs 선언 1건, 삽입 확인, BinData 0개
PASS — 오류 0건 / 경고 0건
```

붙여넣기 가능한 교체안:

```python
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

            _src_ok = False
            if os.path.exists(_png) and os.path.getsize(_png) > 8:
                with open(_png, 'rb') as _f:
                    _src_ok = _f.read(8) == b'\x89PNG\r\n\x1a\n'
            if not _src_ok:
                errs += 1
                print(f"  [ERR] 그림 원본 파일 없음/손상: {_rel}")

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

            _embedded = z.read(_href)
            if len(_embedded) <= 8 or _embedded[:8] != b'\x89PNG\r\n\x1a\n':
                errs += 1
                print(f"  [ERR] 삽입된 BinData가 정상 PNG가 아님: {_fid} → {_href}")

        _bin = [n for n in z.namelist() if n.startswith('BinData/')]
        print(f"  _figs 선언 {len(_figs)}건, 삽입·등록·PNG 확인, BinData {len(_bin)}개")
```

추가 모순:

- `examples/valid-similarity-20pt.json`에는 `_figs`가 없습니다.
- `build_tpl2.py`의 기본 그림 세 파일은 `examples/figs/`와 `tools/figs/` 어느 쪽에도 없습니다.
- 빌더는 정상 그림도 자리표시 문자열을 캡션으로 남기므로 `[그림 N]` 문자열 존재만으로 미삽입을 판정할 수 없습니다.
- [hwpx-build.md:515](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:515>)∼521은 허용 경고가 원본 폭 초과 1건뿐이라고 하지만, 그림 경고도 최종 PASS에 남습니다.

최종본에서는 `_figs`를 필수로 하거나 `--draft/--final` 모드를 나눠 최종 모드에서 미선언 그림을 오류로 올려야 합니다.

### 1-c. B-8 중첩 표 제거 후 부모 `addr/span`

**확인 결과: 부분 반영.**

[check_tpl2.py:83](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:83>)은 `reversed(all_tbl(c))`로 모든 중첩 표를 삭제합니다. 한 단계 중첩에서는 작동하지만, 실제 `tpl2`에는 최대 깊이 3 표가 있습니다. 부모·손자 범위가 겹치기 때문에 손자를 먼저 삭제한 후 원래 부모 오프셋을 쓰면 부모 셀 자신의 `addr/span`까지 잘립니다.

실제 템플릿 T5 반례에서 `parent_span_found=False`, `got=0`, `expected=1`을 재현했습니다.

붙여넣기 가능한 수정안:

```python
        # 겹치지 않는 최상위 중첩 표 범위만 제거한다.
        for na, nb in reversed(spans(c, 'hp:tbl')):
            c = c[:na] + c[nb:]
```

### 1-d. B-6 표 안 `charPr` 실제 속성·예외 처리

**확인 결과: 부분 반영.**

반영된 부분:

- [check_tpl2.py:260](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:260>)∼270에서 11pt, 일반/굵게, 두 fontRef의 일치를 봅니다.
- [check_tpl2.py:281](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:281>)∼283은 예외를 ERR로 처리합니다.

### B — fontRef가 둘 다 없거나 둘 다 잘못된 같은 글꼴이어도 PASS

`fontRef`가 없으면 둘 다 `''`가 되어 같다고 판정됩니다. 또한 두 스타일 모두 `hangul="5"` 같은 잘못된 글꼴이면 서로 같다는 이유로 통과합니다. 실제 목표는 [build_tpl2.py:195](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:195>)의 `HAM_FONT`입니다.

붙여넣기 가능한 수정안:

```python
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
```

### 1-e. B-7 문단 내 `lineseg` 역전

**확인 결과: 부분 반영.**

[check_tpl2.py:323](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:323>)은 뒤 좌표가 2000 이상인 역전만 잡습니다.

```python
if any(b2 < a2 for a2, b2 in zip(_vps, _vps[1:]) if b2 >= 2000):
```

따라서 `[3000,1000]`과 `[1000,500]`은 통과합니다. 같은 줄의 주석은 문단 내부에 페이지 휴리스틱을 적용하지 않는다고 하므로 코드와 주석도 모순됩니다.

붙여넣기 가능한 수정안:

```python
    if any(b2 < a2 for a2, b2 in zip(_vps, _vps[1:])):
        _overlap += 1
        print(f"  [ERR] 문단 내 lineseg 역전: {_vps[:6]}")
```

### 1-f. C-6 예외 FAIL footer·종료 1

**확인 결과: 반영됨 — 이상 없음.**

[check_tpl2.py:6](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:6>)∼11의 `sys.excepthook`이 작동했습니다. 존재하지 않는 파일로 `FileNotFoundError`를 발생시켰을 때 traceback, `FAIL — 예외로 중단`, 종료 코드 1을 확인했습니다.

### 1-g. `py_compile`

**확인 결과: 반영됨 — 이상 없음.**

요청된 세 파일을 포함하여 `tools/*.py` 6개 모두 실제 Python 컴파일 단계에 성공했습니다.

---

## 2. `tools/build_tpl2.py` B-10

**확인 결과: 반영됨 — 이상 없음.**

근거:

- [build_tpl2.py:875](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:875>): 일반 문단 `n_lines=len(segs)`
- [build_tpl2.py:876](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:876>): `paraPr.next`
- [build_tpl2.py:877](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:877>):

```python
body = n_lines * (vs + sp) + nxt
```

- [build_tpl2.py:888](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:888>)과 [build_tpl2.py:894](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:894>)에서 커서와 각 줄 위치에 같은 피치를 적용합니다.

---

## 3. `tools/figlib.py` A-3

**확인 결과: 부분 반영.**

반영된 부분:

- [figlib.py:56](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/figlib.py:56>)∼57: 이전 PNG 선삭제
- [figlib.py:61](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/figlib.py:61>)∼64: 비정상 종료 시 부분 파일 삭제·`RuntimeError`
- [figlib.py:65](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/figlib.py:65>)∼66: 8바이트 PNG 서명 검사

### B — 종료 코드 0이지만 손상 PNG를 만든 경우 fail-open

이 경우 손상 파일을 남기고 `(svg, None)`을 반환하며, 변환기를 실제 실행했는데도 “rsvg-convert 없음”이라고 출력합니다.

붙여넣기 가능한 교체안:

```python
    converter = shutil.which("rsvg-convert")
    if not converter:
        print(
            f"  {name}  {w}x{h} → SVG만 생성(rsvg-convert 없음). "
            f"`brew install librsvg` 후 다시 실행하면 PNG가 만들어진다."
        )
        return sp, None

    try:
        r = subprocess.run(
            [converter, "-w", str(w * 2), "-h", str(h * 2), sp, "-o", pp],
            capture_output=True,
        )

        if r.returncode != 0:
            detail = r.stderr.decode(errors='replace')[:200]
            raise RuntimeError(f"rsvg-convert 실패({name}): {detail}")

        if not os.path.exists(pp) or os.path.getsize(pp) <= 8:
            raise RuntimeError(f"rsvg-convert가 PNG를 만들지 못함({name})")

        with open(pp, 'rb') as f:
            signature = f.read(8)
        if signature != b'\x89PNG\r\n\x1a\n':
            raise RuntimeError(f"rsvg-convert 결과가 정상 PNG가 아님({name})")

    except Exception:
        if os.path.exists(pp):
            try:
                os.remove(pp)
            except OSError:
                pass
        raise

    print(f"  {name}  {w}x{h} → {pp}")
    return sp, pp
```

---

## 4. `workflows/develop-draft.js`·`verify-rubric.js`

**확인 결과: 부분 반영. 두 파일 모두 구문 유효하지만 `develop-draft.js`는 fail-closed가 실제로 깨짐.**

### async 함수 본문 파싱

**반영됨 — 이상 없음.**

`export const meta`를 메타 선언으로 분리해 `const meta`로 바꾼 뒤 두 파일 전체를 `AsyncFunction` 본문으로 파싱했고 둘 다 통과했습니다.

### A — `develop-draft.js`의 실패 초안이 truthy 객체로 변환됨

[develop-draft.js:86](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:86>)은 다음과 같습니다.

```js
.then(r => ({ ...r, key: a.key, angle: a.angle }))
```

JavaScript의 `{...null}`과 `{...undefined}`는 오류가 아니므로 실패 결과가 `{key,angle}`로 바뀝니다. 이후 [develop-draft.js:92](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:92>)의 `filter(Boolean)`을 통과합니다.

실제 반례:

```json
{
  "pass": true,
  "draftCount": 3,
  "second": {
    "key": "b",
    "angle": "설계·제작 — 조건을 만족하는 새 규격을 거꾸로 설계하는 상황"
  }
}
```

붙여넣기 가능한 수정안:

```js
.then(r => {
  if (!r)
    throw new Error(`초안 에이전트 ${a.key} 실패 — 응답 없음`)
  return { ...r, key: a.key, angle: a.angle }
})
```

### B — 심사 `best="z"`도 통과

[develop-draft.js:119](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:119>)은 `review.best`가 비어 있는지만 봅니다. 실제로 `best:"z"`, `fixes:"채택 가능한 초안 없음"`을 줘도 `pass:true`였습니다.

붙여넣기 가능한 수정안:

```js
const validKeys = new Set(valid.map(d => d.key))
if (!review || !validKeys.has(review.best))
  throw new Error(
    `심사 에이전트 실패 — best=${JSON.stringify(review?.best)}가 유효한 초안 key가 아님`
  )
```

스키마에도 다음을 권장합니다.

```js
best: {
  type: 'string',
  enum: ANGLES.map(a => a.key),
  description: '1위 초안의 key',
}
```

### `verify-rubric.js` 실패 에이전트 throw

**반영됨 — 이상 없음.**

- [verify-rubric.js:78](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:78>)∼81: 두 초기 검증 중 하나라도 없으면 throw
- [verify-rubric.js:102](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:102>)∼104: 재검증 누락도 throw

초기 검증 하나를 `null`로 주었을 때 실제로 실패했습니다.

### `verify-rubric.js` 명시적 pass 게이트

**반영됐으나 B급 fail-open 경로 있음.**

명시적 `pass` 계산은 [verify-rubric.js:106](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:106>)∼108에 있습니다. 다만 최초 에이전트의 `blocking` 분류를 그대로 신뢰하는 문제는 갈래 1에서 지적한 수정안이 필요합니다.

---

## 5. `references/failure-modes.md` 검증 프롬프트·슬롯 매핑

**확인 결과: 요구된 수정은 반영됨. 단, 지필 종결 검사는 새 모순.**

정상 반영:

- [failure-modes.md:7](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:7>)과 [failure-modes.md:368](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:368>)∼370:
  - 조판 전 시험 1~11
  - 조판 후 시험 12
- [failure-modes.md:373](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:373>)∼380:
  - `item_intro`, `item_questions`, `item_cond`
  - `std1_text`
  - `item1_element`~`item4_element`
  - 조건부 `std2_text`, `std2_A`~`std2_E`
  - `partial`=채점 시 유의점
  - `caution`=피드백 제공 시 유의점
- 실제 예시도 [valid-similarity-20pt.json:237](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:237>)∼248에서 같은 의미로 사용합니다.

잔여 A는 앞서 지적한 “지필 0점 행을 `ㅁ` 종결 검사에서 제외하지 않음”입니다.

---

## 6. `references/rubric-rules.md` 수행 프로파일 인과

**확인 결과: 반영됨 — 이상 없음.**

[rubric-rules.md:80](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:80>)은 정확히 다음 인과를 씁니다.

> 0점 급간을 없앴기 때문에 제출 답안의 최저 총점이 요소 수 n이 되고, 0~n−1점은 미응시·미제출 전용이 된다.

반대 인과는 검색되지 않았습니다.

---

## 7. `SKILL.md` 슬롯 키·4단계·6단계

**확인 결과: 반영됨 — 이상 없음.**

- [SKILL.md:73](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:73>)은 `item_intro`·`item_questions`·`item_cond`를 정확히 사용합니다.
- [SKILL.md:77](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:77>)은 4단계를 조판 전 시험 1~11로 둡니다.
- [SKILL.md:104](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:104>)은 6단계에서 시험 12(F22)를 조판 후 모드로 실행합니다.

메타데이터의 수행평가 한정 표현은 앞서 C급으로 별도 지적했습니다.

---

## 8. `references/standards.md` §4.4의 R7 상호참조

**확인 결과: 반영됨 — 이상 없음.**

- [standards.md:250](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:250>)은 R7이 올바른 값과 결함 사례를 구분해 싣는다고 명시합니다.
- 실제 [hwpx-build.md:214](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:214>)∼218도:
  - 올바른 값: `18~20 / 16~17 / 10~15 / 8~9 / 0~7`
  - 결함 값: `19~20 / 16~18 / 8~15 / 4~7 / 0~3`
  을 명확히 분리합니다.

---

## 9. `examples/valid-similarity-20pt.json` `_alignment_note`

**확인 결과: 반영됨 — 이상 없음.**

- `_alignment_note`: [valid-similarity-20pt.json:9](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:9>)
- 실제 `std1_A`: [valid-similarity-20pt.json:17](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:17>)

프로그램 대조 결과 다음 세 문구가 `std1_A`와 `_alignment_note` 양쪽에 모두 실제로 존재했습니다.

- `부피의 비를 추론할 수 있으며`
- `이를 실생활 문제 해결에 활용하고`
- `그 과정을 논리적으로 정당화하여 설명할 수 있다`

따라서 다음 귀속은 실제 `std1_A`와 일치합니다.

- 부피비 산출 → 부피의 비 추론
- 단위량당 가격 비교 → 실생활 문제 해결 활용
- 공지문 작성·반박 → 과정의 논리적 정당화·설명

---

# 최종 시행 가능 여부

현재 상태는 **시행 보류**입니다. “두 기본 프로파일의 설계가 전혀 안 들어갔다”는 상태는 아닙니다. 오히려 기본 수행·지필 분기와 핵심 산술 검사는 상당 부분 정확히 들어갔습니다. 문제는 최종 승인 체인에 실제 fail-open과 자기모순이 남았다는 점입니다.

시행 전 최소 필수 수정 순서는 다음과 같습니다.

1. **A — `check_tpl2.py` 그림 게이트**
   - `section0.xml ↔ content.hpf ↔ ZIP BinData ↔ 내장 PNG 서명`을 모두 대조
   - 최종 모드에서 그림 미선언·미삽입을 오류 처리

2. **A — `develop-draft.js`**
   - falsy 결과를 object spread하기 전에 즉시 throw
   - `review.best`를 실제 초안 key로 제한

3. **A — 학교 규정 오버라이드**
   - 프로파일 이름과 실제 채점 규칙을 분리
   - `LOW/MINS/ZERO_DESC/floor`를 규정의 실제 값에서 계산

4. **A — 지필 검증 프롬프트**
   - 고정 0점 행을 `ㅁ` 받침·일반 길이 검사에서 제외

5. **A — 수행 성취수준 게이트**
   - `verify-rubric.js`가 A~E 각각의 도달 가능 점수를 명시적으로 검사
   - `check_levels`가 A~E 개수·순서·PROFILE·C 폭을 검증

6. **B — 조판 검증 견고성**
   - 깊이 3 중첩 표 삭제 방식 수정
   - fontRef의 실제 목표값 검사
   - 모든 문단 내부 `lineseg` 역전 검사
   - `figlib.py`의 종료 코드 0+손상 출력도 삭제 후 예외 전파

7. **B — 문서·few-shot 정합성**
   - F02/F05 표현 수정
   - examples-pizza의 단수 기반 접속 규칙 제거
   - 결함 예시를 복제 가능한 few-shot과 명시적으로 분리
   - 합계 행 정확 일치·단일·마지막 행 검사

위 수정 후에는 최소한 다음 회귀 세트를 다시 실행해야 승인할 수 있습니다.

- 수행 정상 / 수행 1점 요소 / 수행 0점 행 / 수행 백지 공백 반례
- 지필 정상 / 지필 1점 요소 / 지필 0점 누락 / 지필 고정문구 변형
- 학교 규정 오버라이드 2종 이상
- 수행·지필 성취수준 정상 및 A~E 누락·라벨 역전·도달 불가 반례
- 실제 깊이 3 템플릿으로 `check_tpl2.py`
- 그림 정상 / XML ID만 존재 / manifest만 존재 / BinData 누락 / 내장 PNG 손상
- 워크플로 초안 `null`·검증 `null`·재검증 `null`·심각도 오분류 반례

이 회귀가 모두 기대대로 PASS/FAIL을 가를 때 비로소 시행 가능 판정을 내릴 수 있습니다.
