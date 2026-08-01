# 종합 판정

**시행 보류**입니다.

4차 감사의 A급 3건은 핵심 반례 기준으로 상당 부분 고쳐졌습니다.

- `_figs` 생략·부분 매핑은 기본 최종 모드에서 차단됩니다.
- `check_levels()`의 bounds swap·이름 swap·C 비최대·도달 불가·범위 오류는 차단됩니다.
- B-6의 실제 44개 충족 벡터는 겹침 0·공백 0입니다.
- 수행·지필 E2E는 둘 다 최종 오류 0·허용 경고 1건으로 통과합니다.

그러나 다음 새 A급 4건 때문에 승인할 수 없습니다.

| 등급 | 새 결함 | 실행 판정 |
|---|---|---|
| **A** | `rubric-rules.md` §3의 4단 표준 뼈대 | 백지가 2점·1점에 동시 해당, `A 전무+B 부분/완전`은 무급간 |
| **A** | PNG 검사가 서명만 확인 | IDAT·CRC·IEND가 없는 26바이트 파일도 build·최종 check 모두 `PASS` |
| **A** | `check_tpl2.py --draft`가 최종 승인 우회 | 그림 3개가 모두 없는 산출물이 `PASS`, 종료 코드 0 |
| **A** | 새 `out2` 위치가 기존 사용자 폴더를 재귀 삭제 | 산출 폴더의 임의 `out2/`를 무조건 `shutil.rmtree()`하며 병렬 빌드도 충돌 |

기술 조판 파이프라인은 정상 동작하지만, 채점기준 원형과 최종 승인 게이트 및 데이터 안전성에 시행 전 차단 결함이 남아 있습니다.

---

# 감사 범위와 실행 방식

먼저 이전 감사 전문 1,119행인 [codex_skill_review4.md](</private/tmp/claude-501/-Volumes-ssdmacmini-1-han-ex-projects-123/6981ac5c-4498-45c0-98bf-f487552987cc/scratchpad/codex_skill_review4.md:1>)를 읽었습니다. 이어서 대상의 다음 파일을 끝까지 직접 읽었습니다.

- `SKILL.md`
- `references/*.md` 7개
- `examples/examples-pizza.md`
- `examples/valid-similarity-20pt.json`
- `examples/figs/`의 PNG 3개와 SVG 3개
- `tools/*.py` 6개
- `workflows/*.js` 2개

주요 현재 스냅샷은 다음과 같습니다.

```text
build_tpl2.py       f95b25a0b38cadd7141c2f675e4ca52fd8c6ca2ceaa4f76eb7c050201e1d78
check_tpl2.py       9fae9802c2f675e4ca52fd8c6ca2ceaa4f76eb7c050201e1d78cd4f9a91344cd
figlib.py           79ff1c3052162f95ee570c42da88f009f085b43218580757fd45cd30b470370f
rubric-rules.md     ad35e669eac19c32af0b1f3ebd84bd117ef8910b35ce3cf698b97adf7d14f8de
standards.md        5fbb1b7e8664e2b37f0c37dd2168d04764bece79b79d1a7dc53d3440c3acd639
examples-pizza.md   1374b4ace972edd58eb381dd16f961992cff8bb7153a1f44704dcfcdeac518d4
valid JSON          0a03191ee0fdba5d6aa63e6d4b17dbabe027ed7ec8205eeaccae967d5cef6a8f
develop-draft.js    24ac3b945d92888b958e507ad1c5812bebb7ae3ca133ca8b49ec1d0d79c4ae59
verify-rubric.js    9eb753ac030e96caba1fd05a41a4d0a8be37fc44a0312a3728facd78472ff2ec
```

Python 6개는 모두 실제 `compile()`을 통과했습니다.

```text
PY_OK build_tpl2.py
PY_OK check_tpl2.py
PY_OK figlib.py
PY_OK img_embed.py
PY_OK metrics.py
PY_OK restyle.py
```

파일시스템이 읽기 전용이어서 새 임시 폴더 생성도 `Operation not permitted`였습니다. 따라서 변조 ZIP과 fresh E2E는 `open`·`os`·`shutil`·`zipfile`만 메모리 VFS와 `BytesIO`에 연결하고 **실제 소스 본문을 그대로 `compile`/`exec`**했습니다. 검사 로직을 다시 구현하지 않았습니다. 공유 스크래치에 현재 `build_tpl2.py`로 생성된 수행·지필 실물도 있어, 최신 `check_tpl2.py`로 양쪽을 다시 직접 검사했습니다. 대상 스킬은 수정하지 않았습니다.

---

# A1. 그림 최종 모드

## 항목별 결과

| 시험 | 결과 | 실행 근거 |
|---|---|---|
| 정상 `_figs` 3개 + 정상 PNG 3개 | **차단 오탐 없음** | `PASS — 오류 0 / 경고 1` |
| `_figs` 생략, 최종 검사 | **차단됨** | `EXIT 1`, 미선언 자리표시 3개 ERR |
| `_figs` 부분 매핑 | **부분** | 빌더 단독은 미매핑 줄을 텍스트로 유지하지만 최종 검사는 `EXIT 1` |
| 매핑된 외부 PNG 누락, 최종 build | **차단됨** | `FileNotFoundError` |
| 외부 PNG 서명 손상 | **차단됨** | `그림 원본 파일 없음/손상` |
| 내장 PNG 서명 손상 | **차단됨** | `삽입된 BinData가 정상 PNG가 아님` |
| `content.hpf` 그림 항목 누락 | **차단됨** | 미등록·참조 누락 ERR |
| ZIP의 등록된 그림 파일 누락 | **차단됨** | 5.5·5.6 ERR |
| `_figs` ID 중복 | **차단됨** | `_figs의 BinData id가 중복됨` |
| 선언했으나 section XML에 미삽입 | **차단됨** | `선언한 그림이 문서에 삽입되지 않음` |
| PNG 서명과 크기 필드만 남긴 26바이트 파일 | **여전히 통과 — 새 A** | build 0, check 0, 최종 `PASS` |
| 그림 전체 누락 + `check --draft` | **여전히 통과 — 새 A** | `PASS — 오류 0 / 경고 2`, 종료 코드 0 |

관련 구현은 [build_tpl2.py의 최종·초안 분기](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:299>)와 [check_tpl2.py 그림 게이트](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:236>)입니다.

## 정상 예시 자산

예시 JSON에는 실제로 `_figs` 3개가 들어 있습니다. 세 PNG를 눈으로 열어 확인했고, Pillow `verify()`와 실제 디코딩 `load()`도 통과했습니다.

```text
fig1_three_sizes.png  PNG 1220×620  verify+load OK
fig5_menu_board.png   PNG 1480×600  verify+load OK
fig6_owner_memo.png   PNG 1520×788  verify+load OK
```

정상 최종 검사:

```text
_figs 선언 3건, 삽입·등록·PNG 확인, BinData 3개
고아 0건 / 참조 누락 0건 (등록 3개, 참조 3개)
PASS — 오류 0건 / 경고 1건
```

따라서 지원되는 정상 경로에서 새 false-positive는 없습니다.

## 과거 `_figs` 생략 반례

최종 모드:

```text
### 5.5 그림 게이트 (최종 모드)
[ERR] 최종본의 미선언 그림 자리표시:
      ['[그림 1]', '[그림 2]', '[그림 3]']
FAIL — 오류 1건 / 경고 1건
EXIT 1
```

부분 매핑도 최종 검사에서 나머지 자리표시를 ERR로 잡았습니다.

```text
[ERR] 최종본의 미선언 그림 자리표시:
      ['[그림 2]', '[그림 3]']
EXIT 1
```

따라서 4차 감사의 정확한 `_figs 생략 → 경고만 내고 PASS` 반례는 **기본 최종 모드에서 차단됐습니다.**

## 새 A — 실제 PNG가 아닌 26바이트 파일이 최종 PASS

[img_embed.py의 `png_size()`](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/img_embed.py:18>)는 `head[1:4] == b"PNG"`와 너비·높이만 읽습니다. [check_tpl2.py](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:262>)도 첫 8바이트 서명만 확인합니다.

다음 파일을 만들었습니다.

```python
bad = (
    b"\x89PNG\r\n\x1a\n"
    + b"\x00\x00\x00\rIHDR"
    + (1).to_bytes(4, "big")
    + (1).to_bytes(4, "big")
    + b"\x08\x02"
)
```

이 파일에는 IDAT, CRC, IEND가 전혀 없습니다.

```text
길이 26바이트
Pillow: OSError: Truncated File Read
img_embed.png_size: (1, 1)
```

이를 정상 HWPX의 `BinData/fig1.png`로 바꾼 뒤 최신 검증기를 실행했습니다.

```text
FAKE_LEN 26
EXIT 0
_figs 선언 3건, 삽입·등록·PNG 확인, BinData 3개
PASS — 오류 0건 / 경고 1건
```

즉 “PNG 손상” 중 첫 서명이 바뀐 단순 손상만 막고, 실제로 열리지 않는 구조 손상은 승인합니다.

### 붙여넣기 가능한 수정안

Pillow는 현재 환경에 설치되어 있으며 실제 동봉 PNG 3개도 통과했습니다. 외부 파일·내장 바이트·`figlib` 변환 결과를 같은 함수로 검증해야 합니다.

```python
from io import BytesIO
from pathlib import Path
from PIL import Image


def verified_png_bytes(data, label):
    try:
        with Image.open(BytesIO(data)) as im:
            if im.format != "PNG":
                raise ValueError("PNG 형식이 아님")
            size = im.size
            im.verify()

        # verify() 뒤 다시 열어 실제 픽셀 디코딩까지 확인한다.
        with Image.open(BytesIO(data)) as im:
            im.load()
            if im.width <= 0 or im.height <= 0:
                raise ValueError("그림 크기가 0 이하임")

        return size
    except Exception as ex:
        raise ValueError(f"정상 PNG가 아님: {label}: {ex}") from ex


def verified_png_path(path):
    return verified_png_bytes(Path(path).read_bytes(), path)
```

`img_embed.py`:

```python
def png_size(path):
    return verified_png_path(path)
```

`check_tpl2.py`:

```python
try:
    verified_png_path(_png)
except ValueError as ex:
    errs += 1
    print(f"  [ERR] 그림 원본 파일 없음/손상: {_rel}: {ex}")

try:
    verified_png_bytes(z.read(_href), _href)
except ValueError as ex:
    errs += 1
    print(f"  [ERR] 삽입된 BinData가 정상 PNG가 아님: {_fid} → {_href}: {ex}")
```

`figlib.save()`에서 `rsvg-convert` 결과도 동일한 `verified_png_path(pp)`를 통과시켜야 합니다.

## 새 A — `--draft`가 최종 게이트를 우회

같은 그림 없는 산출물을 기본 최종과 `--draft`로 각각 검사했습니다.

```text
FINAL EXIT 1
[ERR] 최종본의 미선언 그림 자리표시 3건
FAIL — 오류 1건 / 경고 1건
```

```text
DRAFT EXIT 0
[WARN] 초안의 미선언 그림 자리표시 3건
PASS — 오류 0건 / 경고 2건
```

부분 매핑도 `partial_final EXIT 1`, `partial_draft EXIT 0`입니다.

초안 모드 자체는 필요할 수 있지만, 현재는 결과 문자열과 종료 코드가 최종 성공과 동일합니다. 호출자가 플래그 하나를 추가하면 과거 A급 false-pass가 복원됩니다. 별도 릴리스 오케스트레이터가 `--draft`를 금지한다는 기계 계약도 없습니다.

### 붙여넣기 가능한 수정안

가장 안전한 방법은 `check_tpl2.py`에서 `--draft`를 제거하고, 완화는 `build_tpl2.py --draft`에만 두는 것입니다. 초안 검사도 최종 기준으로 실패 위치를 보여 주면 됩니다.

초안 검증을 유지해야 한다면 적어도 완화가 사용된 실행은 `PASS`와 코드 0을 반환하지 않아야 합니다.

```python
draft_waivers = 0

if _unmapped:
    if DRAFT_MODE:
        draft_waivers += len(_unmapped)
        warns += 1
        print(f"  [WARN] 초안의 미선언 그림 자리표시: {_unmapped}")
    else:
        errs += 1
        print(f"  [ERR] 최종본의 미선언 그림 자리표시: {_unmapped}")

if DRAFT_MODE and draft_waivers:
    print(
        f"\n{'='*60}\n"
        f"DRAFT-ONLY — 최종 제출 불가 / 완화 {draft_waivers}건 / "
        f"오류 {errs}건 / 경고 {warns}건"
    )
    sys.exit(2)

_result = "PASS" if errs == 0 else "FAIL"
print(f"\n{'='*60}\n{_result} — 오류 {errs}건 / 경고 {warns}건")
sys.exit(0 if errs == 0 else 1)
```

---

# 가장 중요한 새 A — `rubric-rules.md` §3 표준 뼈대

문제 위치는 [rubric-rules.md §3 급간 뼈대](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:171>)입니다. 문서가 “배점 단수별로 아래 뼈대를 그대로 쓴다”고 지시하므로 한 예시의 결함이 아니라 스킬이 만드는 모든 채점기준의 원형 결함입니다.

## 현재 2단

A와 B를 각각 성공/실패의 이진 원자로 해석했습니다.

```text
2점 = A ∧ B
1점 = ¬(A ∧ B)
```

실행:

```text
vectors 4
overlap 0
gap 0
```

**판정: 차단 오탐 없음.**

## 현재 3단

문언:

```text
3점 = A와 B를 모두 옳게 수행함.
2점 = A는 하였으나 B에 일부 오류가 있음.
1점 = A를 하지 못하거나 B를 하지 못함.
```

`B 일부 오류`와 `B 전무`를 서로 배타적인 상태로 조작적으로 정의하면:

```text
A = 전무/완전
B = 전무/부분오류/완전
유효 상태 6
overlap 0
gap 0
```

그러나 자연어에서 “B를 하지 못함”은 “B를 옳게 완수하지 못함”으로도 읽힙니다. 이 해석에서는 `A 완전+B 부분오류`가 2점이면서 동시에 1점입니다. 현재 문서에는 “하지 못함=시도 전무”라는 조작적 정의가 없습니다.

**판정: 형식적 의도상 정상, 자연어 외연상 부분. 모호어를 금지하는 스킬의 표준 뼈대로는 부적합하므로 함께 교체해야 합니다.**

## 현재 4단

문언:

```text
4점 = A와 B를 모두 옳게 수행함.
3점 = A는 모두 옳으나 B에 일부 오류가 있음.
2점 = A의 일부만 수행하거나 B를 하지 못함.
1점 = A도 하지 못하고 B도 하지 못함.
```

A와 B를 각각 `0=전무, 1=부분·오류, 2=완전`으로 두었습니다. 이를 Boolean 원자 `A_some, A_all, B_some, B_all`로 풀어 `2⁴` 조합 중 `all ⇒ some`을 만족하는 9개 유효 벡터를 전수 검사했습니다.

```text
4단 valid vectors 9
overlap 1
gap 2
```

반례:

| 상태 | 참이 되는 급간 | 판정 |
|---|---|---|
| A 전무, B 전무 `(0,0)` | 2점, 1점 | **겹침** |
| A 전무, B 부분 `(0,1)` | 없음 | **공백** |
| A 전무, B 완전 `(0,2)` | 없음 | **공백** |

사용자가 제시한 주장은 정확합니다.

- 백지는 “B를 하지 못함” 때문에 2점이고 “A도 B도 못함” 때문에 1점입니다.
- A를 전혀 하지 않았지만 B를 일부 또는 완전히 한 답안은 어느 급간에도 없습니다.
- 높은 급간부터 대조한다는 운영 순서는 점수 하나를 골라 줄 뿐, 두 술어가 동시에 참인 사실을 제거하지 않습니다.

**판정: 새 A급 확정.**

## 모든 단수의 대체 뼈대

안전한 공통 원리는 “관찰 가능한 독립 원자의 성공 개수” 한 축만 쓰는 것입니다.

- 2단: 원자 2개를 `2개 / 0~1개`
- 3단: 원자 2개를 `2개 / 1개 / 0개`
- 4단: 원자 3개를 `3개 / 2개 / 1개 / 0개`

아래는 그대로 붙여넣을 수 있는 실물 표입니다. `세 비 구하기`, `관계 설명`, `주문 방안 판단`은 실제 요소의 구체적인 관찰 행동으로 일관되게 치환하되, 치환 후 다시 자수를 재야 합니다.

| 단수 | 점수 | 대체 뼈대 | 자수 |
|---|---:|---|---:|
| 2단 | 2 | 세 비를 옳게 구하고 세 비 사이의 관계를 식으로 빠짐없이 설명함. | 37 |
| 2단 | 1 | 세 비를 옳게 구하지 못하거나 세 비 사이의 관계를 식으로 설명하지 못함. | 41 |
| 3단 | 3 | 세 비를 옳게 구하고 세 비 사이의 관계를 식으로 빠짐없이 설명함. | 37 |
| 3단 | 2 | 세 비 구하기와 관계 설명하기 가운데 한 가지만 옳게 수행함. | 34 |
| 3단 | 1 | 세 비를 구하지 못하고 세 비 사이의 관계도 식으로 설명하지 못함. | 37 |
| 4단 | 4 | 세 비를 구하고 관계를 설명하며 주문 방안을 옳게 판단함. | 32 |
| 4단 | 3 | 세 비 구하기, 관계 설명, 주문 방안 판단 가운데 두 가지를 옳게 수행함. | 42 |
| 4단 | 2 | 세 비 구하기, 관계 설명, 주문 방안 판단 가운데 한 가지만 옳게 수행함. | 42 |
| 4단 | 1 | 세 비를 구하지 못하고 관계를 설명하지 못하며 주문 방안도 판단하지 못함. | 41 |

문체 기계 검사:

```text
자수 32~42
마침표 정확히 1개
마지막 음절 종성 = 16(ㅁ)
50자 초과 0
⑴⑵⑶ 0
내부 참조 0
금지 모호어 0
```

전수 열거:

```text
대체 2단: 2² = 4벡터, overlap 0, gap 0
대체 3단: 2² = 4벡터, overlap 0, gap 0
대체 4단: 2³ = 8벡터, overlap 0, gap 0
```

4단 요소에서 독립 원자 세 개를 정할 수 없다면 두 원자에 “부분 수행”이라는 다른 축을 억지로 섞지 말고, 요소를 3단으로 낮추거나 채점 요소를 다시 분해해야 합니다.

## 이 수정과 함께 바꿔야 할 곳

현재 [valid-similarity-20pt.json](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:330>)의 `rubric_rows`도 결함 있는 A-6 4단 구조를 담고 있습니다. 파일명이 `valid`이고 E2E 형식 견본으로 쓰이므로 표준 뼈대만 고치고 이 JSON을 그대로 두면 다음 작성자가 다시 복제할 수 있습니다.

시행 전 함께 해야 합니다.

1. `rubric-rules.md` §3의 2·3·4단 표를 위 개수축 표로 교체
2. `valid-similarity-20pt.json`의 A-6 `rubric_rows`를 개수축 문언으로 교체
3. `failure-modes.md`의 “좋은 예” 중 A-6 문언을 새 문언과 동기화
4. 각 실제 요소의 원자 목록과 `2ⁿ` 실행 결과를 JSON 인접 주석 문서 또는 예시 문서에 보존

---

# A3. `examples-pizza.md` B-6과 A-6

## B-6 — 실제 44벡터는 정상

[B-6 급간 원문](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:208>)에서 원자 수행을 직접 유도했습니다.

| 요소 | 원자 수 | 벡터 | 분할 |
|---|---:|---:|---|
| 닮음 판별과 닮음비 구하기 | 3 | 8 | 3/2/1/0개 |
| 넓이의 비 적용과 ㉡ 반박하기 | 3 | 8 | 3/2/1/0개 |
| 부피의 비와 방안별 값 구하기 | 3 | 8 | 3/2/1/0개 |
| 두 단계 판단과 제안서 쓰기 | 3 | 8 | 3/1~2/0개 |
| 빅 판 수와 치즈 총량 구하기 | 3 | 8 | 3/1~2/0개 |
| 파티팩 한 변과 조건 구분하기 | 2 | 4 | 2/0~1개 |

실행 결과:

```text
B1   8 vectors
B2   8 vectors
B3a  8 vectors
B3b  8 vectors
B4a  8 vectors
B4b  4 vectors

B6 TOTAL 44 overlap 0 gap 0
```

**판정: 차단됨. 정상 급간의 새 겹침·공백은 없습니다.**

## 새 B — 문서의 “40벡터” 보고는 여섯째 요소를 누락

문서는 [B-6 검사 결과](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:242>)를 “다섯 요소 × 8 = 40벡터”라고 씁니다. 그러나 B-6에는 여섯 요소가 있고, 마지막 2단 요소의 4벡터가 빠졌습니다.

결론은 우연히 맞지만 전수 검증 증거는 불완전합니다.

### 붙여넣기 가능한 수정안

원자 수행 표에 다음 행을 추가합니다.

```markdown
| 파티팩 한 변과 조건 구분하기 | 파티팩 한 변 구하기 / 두께 조건에 따른 부피 배수 구분하기 |
```

결과 문구를 교체합니다.

```markdown
**2ⁿ 전수 검사 결과 — 여섯 요소의 44벡터
(3원자 요소 5개 × 8벡터 + 2원자 요소 1개 × 4벡터)에서
겹침 0건·공백 0건.**
```

문서 첫머리의 “40벡터” 설명도 같은 값으로 바꿔야 합니다.

## A-6 — 결함·복제 금지 표시는 정확

다음 위치에서 명확하게 금지되어 있습니다.

- [문서 서두](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:1>): 감사용 few-shot
- [복제 가능/금지 표](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:5>): A-6은 문체·자수만 허용, 구조는 금지
- [결함·복제 금지 행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:7>): A-6 구조를 명시적으로 포함
- [D-2 설명](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:295>): 구조를 복제하지 말라고 재확인

**판정: 표시 자체는 차단됨.**

다만 `겹침 1·공백 4`라는 수치는 계수 단위가 생략되어 있습니다.

- 동형인 세 4단 요소를 하나의 구조 유형으로 합치면 `겹침 1·공백 2`
- 문항 4 첫째 요소에서 `공백 2`
- 구조 유형으로 합산하면 `겹침 1·공백 4`

반면 A-6의 모든 요소를 실제 사례별로 세면:

```text
TOTAL 48 valid states
overlap 3
gap 8
```

즉 수선자의 질적 판정은 맞지만, 숫자는 **동형 구조를 접어 센 값일 때만** 맞습니다.

### 붙여넣기 가능한 보완

```markdown
A-6의 `겹침 1·공백 4`는 동형인 세 4단 요소를 하나의
급간 구조로 묶어 센 결함 유형 수이다. 동일 구조가 적용된 각 요소를
별도 사례로 세면 겹침 3건·공백 8건이다.
```

이 항목은 질적 금지 판정을 바꾸지 않으므로 C급입니다.

---

# A2. `check_levels`와 지필 자연 분할

관련 구현은 [standards.md의 `check_levels`](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:240>)입니다.

## 지정 회귀

| 시험 | 실제 결과 |
|---|---|
| 수행 정상, total 20·floor 6 | `True` |
| 지필 정상, total 20·floor 0 | `True` |
| bounds swap `A 0~7 … E 18~20` | 차단, `A 수준 상한이 총점이 아님` |
| 이름 swap | 차단 |
| C 비최대 | 차단 |
| C 최대 동률 | 차단 |
| E 도달 불가 | 차단 |
| `lo > hi` | 차단 |
| floor `-1` | 차단 |
| floor `21 > total` | 차단 |
| R=5 | 차단 |
| 정상 축소형 R=7 | 통과 |
| 구간 공백·겹침 | 차단 |

**판정: 과거 bounds-swap A급은 차단됐고 정상 수행·지필 오탐은 없습니다.**

과거 핵심 반례는 예외를 잡지 않은 독립 프로세스에서도 종료 코드 1이었습니다.

```text
AssertionError: A 수준 상한이 총점이 아님
BOUNDS_SWAP_PROCESS_EXIT=1
```

## §4.3-5 지필 알고리즘 total 5~40 스윕

실제 적용 공식:

```python
R = total + 1
C = ceil((R + 4) / 5)
q, rem = divmod(R - C, 4)

sizes = {
    "A": q + (rem > 0),
    "B": q + (rem > 1),
    "C": C,
    "D": q + (rem > 2),
    "E": q + (rem > 3),
}
```

총점 5~40, 36개 전부에 대해 다음을 동시에 확인했습니다.

```text
check_levels == True
C 유일 최대
max(size) - min(size) <= 2
A 상한 = total
E 하한 = 0
공백 0
겹침 0

SWEEP PASS 36/36
```

대표 결과:

| total | R | A/B/C/D/E 개수 | 결과 |
|---:|---:|---|---|
| 5 | 6 | 1/1/2/1/1 | 통과 |
| 6 | 7 | 1/1/3/1/1 | 통과 |
| 10 | 11 | 2/2/3/2/2 | 통과 |
| 20 | 21 | 4/4/5/4/4 | 통과 |
| 40 | 41 | 8/8/9/8/8 | 통과 |

20점 결과는 문서 예시와 정확히 같습니다.

```text
A 17~20 / B 13~16 / C 8~12 / D 4~7 / E 0~3
```

**판정: 문서 공식·문서 예시·현재 assert에 모두 부합합니다.**

## 새 B — `python3 -O`에서 게이트 전체 소멸

모든 검사가 `assert`로만 구현되어 있습니다. `python3 -O` 또는 `PYTHONOPTIMIZE=1`에서는 assert가 컴파일 단계에서 제거됩니다.

실행:

```text
OPTIMIZE 1
bounds_swap_result True
EXIT 0
```

통상 문서 명령은 `python3`이라 기본 경로는 안전하지만, 검증 코드로서는 fail-closed가 아닙니다.

## 잔여 B — 지필 자연 분할 자체는 기계 강제가 아님

현재 함수는 C가 유일 최대인지만 봅니다. 다음 극단 분할도 `True`입니다.

```python
[
    ("A", 20, 20),
    ("B", 19, 19),
    ("C", 2, 18),
    ("D", 1, 1),
    ("E", 0, 0),
]
# counts = 1/1/17/1/1
```

실행 결과:

```text
extreme True
```

문서는 이를 수기 검산이라고 정확히 밝히므로 숨은 모순은 아니지만, 최종 기계 게이트는 여전히 자연 분할을 강제하지 않습니다.

## 새 C — 비정수 floor 허용

```text
floor=6.5 → True
```

정상 생성 경로에서는 정수지만 잘못된 외부 계산을 조용히 승인할 수 있습니다.

## 붙여넣기 가능한 통합 수정안

`profile`을 명시적으로 넘기고 `assert`를 명시적 예외로 바꾸면 `-O`, 비정수 입력, 지필 자연 분할을 한 번에 해결할 수 있습니다.

```python
from math import ceil


def check_levels(levels, total, floor, profile):
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    require(
        profile in ("수행평가", "지필평가"),
        f"평가 유형 오타: {profile!r}",
    )
    require(
        type(total) is int and type(floor) is int,
        f"total·floor는 정수여야 함: total={total!r}, floor={floor!r}",
    )
    require(
        len(levels) == 5
        and all(isinstance(x, (tuple, list)) and len(x) == 3 for x in levels),
        "수준은 (이름, 하한, 상한) 5개여야 함",
    )
    require(
        all(type(lo) is int and type(hi) is int for _, lo, hi in levels),
        "모든 구간 하한·상한은 정수여야 함",
    )
    require(
        [name for name, _, _ in levels] == list("ABCDE"),
        "수준은 A,B,C,D,E가 이 순서로 정확히 한 번씩 있어야 함",
    )
    require(
        0 <= floor <= total,
        f"floor 범위 오류: {floor} (total={total})",
    )

    R = total - floor + 1
    require(
        R >= 6,
        f"도달 가능 점수 {R}개로 C가 가장 넓은 5수준을 만들 수 없음",
    )

    for name, lo, hi in levels:
        require(
            0 <= lo <= hi <= total,
            f"{name} 구간 범위/방향 오류: {lo}~{hi}",
        )

    require(levels[0][2] == total, "A 수준 상한이 총점이 아님")
    require(levels[-1][1] == 0, "E 수준 하한이 0이 아님")

    for higher, lower in zip(levels, levels[1:]):
        require(
            lower[2] + 1 == higher[1],
            f"구간 불연속/중복/순서 역전: {higher} {lower}",
        )

    counts = {}
    for name, lo, hi in levels:
        counts[name] = sum(s >= floor for s in range(lo, hi + 1))
        require(
            counts[name] > 0,
            f"{name} 수준에 도달 가능 점수가 없음 "
            f"({lo}~{hi}, floor={floor})",
        )

    require(
        counts["C"] > max(counts[x] for x in "ABDE"),
        f"C가 유일한 최대가 아님: {counts}",
    )

    if profile == "지필평가":
        require(floor == 0, f"지필평가 floor가 0이 아님: {floor}")

        c_size = ceil((total + 1 + 4) / 5)
        q, rem = divmod(total + 1 - c_size, 4)
        expected = {
            "A": q + (rem > 0),
            "B": q + (rem > 1),
            "C": c_size,
            "D": q + (rem > 2),
            "E": q + (rem > 3),
        }
        require(
            counts == expected,
            f"지필 자연 분할과 다름: 실제 {counts}, 기대 {expected}",
        )

    return True
```

호출:

```python
check_levels(levels, total, floor, PROFILE)
```

학교 규정이 수행평가에도 0점 급간을 두는 경우에는 `profile="수행평가"`로 넘기므로 지필 전용 자연 분할을 잘못 강제하지 않습니다.

---

# 새 ①. §5.6 BinData 정합

## 고아 제거 생략

빌더가 남기는 실제 고아:

```text
image1 → BinData/image1.bmp
image2 → BinData/image2.bmp
```

고아 제거를 건너뛴 실물에 최신 검증기를 실행했습니다.

```text
### 5.6 BinData 정합
[ERR] 고아 BinData(아무도 참조하지 않음):
      {'image1': 'BinData/image1.bmp',
       'image2': 'BinData/image2.bmp'}
FAIL
```

정상 제거본:

```text
고아 0건 / 참조 누락 0건 (등록 3개, 참조 3개)
PASS
```

**판정: 주장대로 차단됨.**

## 새 B — ZIP에만 남은 미등록 BinData는 PASS

`content.hpf`에는 등록하지 않고 ZIP에만 `BinData/ghost.bin`을 추가했습니다.

```text
엔트리 15
고아 0건 / 참조 누락 0건
PASS — 오류 0건 / 경고 1건
EXIT 0
```

## 새 B — `content.hpf` 중복 ID는 PASS

`id="fig1"` 항목을 그대로 한 번 더 넣었습니다.

```text
고아 0건 / 참조 누락 0건
PASS — 오류 0건 / 경고 1건
EXIT 0
```

원인은 [check_tpl2.py의 `dict()` 축약](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:333>)이 중복을 버리기 때문입니다.

## 붙여넣기 가능한 보완

```python
from collections import Counter

_hpf_root = ET.fromstring(z.read("Contents/content.hpf"))
_pairs = [
    (e.attrib.get("id"), e.attrib.get("href"))
    for e in _hpf_root.iter()
    if (
        e.tag.rsplit("}", 1)[-1] == "item"
        and (e.attrib.get("href") or "").startswith("BinData/")
    )
]

_ids = [item_id for item_id, _ in _pairs]
_hrefs = [href for _, href in _pairs]

_dup_ids = sorted(
    item_id for item_id, n in Counter(_ids).items() if n > 1
)
_dup_hrefs = sorted(
    href for href, n in Counter(_hrefs).items() if n > 1
)

if _dup_ids:
    errs += 1
    print(f"  [ERR] content.hpf BinData id 중복: {_dup_ids}")
if _dup_hrefs:
    errs += 1
    print(f"  [ERR] content.hpf BinData href 중복: {_dup_hrefs}")

_items = dict(_pairs)

_used = set()
for _section in (
    n for n in z.namelist()
    if re.fullmatch(r"Contents/section\d+\.xml", n)
):
    _used.update(
        re.findall(
            r'binaryItemIDRef="([^"]+)"',
            z.read(_section).decode("utf-8"),
        )
    )

_zip_bins = {
    n for n in z.namelist()
    if n.startswith("BinData/") and not n.endswith("/")
}
_manifest_bins = set(_hrefs)

_orphan = {k: v for k, v in _items.items() if k not in _used}
_missing = _used - set(_items)
_zip_missing = sorted(_manifest_bins - _zip_bins)
_unregistered_zip = sorted(_zip_bins - _manifest_bins)

if _orphan:
    errs += 1
    print(f"  [ERR] 고아 BinData: {_orphan}")
if _missing:
    errs += 1
    print(f"  [ERR] 참조되나 매니페스트에 없음: {sorted(_missing)}")
if _zip_missing:
    errs += 1
    print(f"  [ERR] 매니페스트에 있으나 ZIP에 없음: {_zip_missing}")
if _unregistered_zip:
    errs += 1
    print(
        f"  [ERR] ZIP에만 있고 매니페스트에 없는 BinData: "
        f"{_unregistered_zip}"
    )
```

`Contents/content.hpf` 파일 전체가 없을 때는 §5.5가 먼저 uncaught `KeyError`로 끝나 최종 실패는 안전하지만 친절한 §5.6 진단에 도달하지 않습니다. HPF 파싱을 5.5·5.6 공통 선행 블록으로 합치면 이 B/C급 진단 문제도 함께 해소됩니다.

---

# 새 ②. `figlib.py` 출력 경로

[figlib.py 기본 OUT](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/figlib.py:27>)은 다음과 같습니다.

```python
OUT = os.environ.get("FIGLIB_OUT") or os.path.join(os.getcwd(), "figs")
```

직접 실행하는 `__main__`은:

```python
OUT = os.environ.get("FIGLIB_OUT") or os.path.join(os.getcwd(), "figs_demo")
```

임의 현재 디렉터리 `/arbitrary/run`으로 실제 소스를 메모리 VFS에서 실행한 결과:

```text
CREATED 6
PREFIX_OK True

/arbitrary/run/figs_demo/demo_boxes.svg
/arbitrary/run/figs_demo/demo_chat.svg
/arbitrary/run/figs_demo/demo_circles.svg
/arbitrary/run/figs_demo/demo_grid.svg
/arbitrary/run/figs_demo/demo_memo.svg
/arbitrary/run/figs_demo/demo_menu.svg
```

`FIGLIB_OUT=/chosen/output`:

```text
ENV_PREFIX_OK 6 True
```

스킬 폴더에는 `tools/figs`, `tools/figs_demo`, `tools/out2`가 생기지 않았습니다.

**판정: 주장대로 수정됨.**

단, [figures.md](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/figures.md:70>)는 아직 데모가 `tools/figs_demo/`에 생성된다고 쓰므로 문서가 낡았습니다.

붙여넣기 가능한 교체:

```text
`python3 figlib.py`를 실행하면 `FIGLIB_OUT`이 지정된 경우 그 폴더에,
그렇지 않으면 현재 작업 디렉터리의 `figs_demo/`에 데모를 생성한다.
스킬의 `tools/` 아래에는 데모를 쓰지 않는다.
```

같은 문서 [134행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/figures.md:134>)도 “그림 파일이 없으면 계속한다”고 일반화합니다. 다음으로 바꿔야 합니다.

```text
기본 최종 모드에서는 매핑된 그림 파일이 하나라도 없으면
`FileNotFoundError`로 빌드를 중단한다. 초안에서만 `--draft`를 붙여
자리표시 텍스트를 유지할 수 있다. 제출본은 플래그 없이 다시 빌드하고
플래그 없이 최종 검사한다.
```

---

# 새 ③. `build_tpl2.py`의 out2 위치

출력 경로 `/private/tmp/arbitrary-product/final.hwpx`로 초기화했을 때:

```text
OUT_DIR = /private/tmp/arbitrary-product/out2
```

메모리 E2E에서도:

```text
/virtual/perf/out2
/virtual/paper/out2
```

스킬 경로에는 작업 트리가 만들어지지 않았습니다.

**판정: “산출 HWPX 폴더 옆에 생성” 주장은 참입니다.**

## 새 A — 기존 `out2/` 재귀 삭제와 병렬 경합

현재 [build_tpl2.py](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:937>)는 다음을 실행합니다.

```python
if os.path.exists(OUT_DIR):
    shutil.rmtree(OUT_DIR)
shutil.copytree(TPL_DIR, OUT_DIR)
```

따라서:

- 사용자의 산출 폴더에 관련 없는 `out2/`가 있으면 통째로 삭제합니다.
- 같은 폴더에서 수행·지필 빌드를 병렬 실행하면 서로의 작업 트리를 삭제합니다.
- 출력 파일명이 달라도 작업 트리는 모두 같은 `out2`입니다.

문서의 권장 경로가 빈 `/private/tmp` 작업 폴더라 정상 예시에서는 드러나지 않지만, CLI 사용법은 임의 출력 경로를 허용하고 코드가 빈 작업 폴더를 강제하지 않습니다. 사용자 데이터 손실 가능성이 있어 시행 전 수정해야 합니다.

### 붙여넣기 가능한 수정안

```python
import atexit
import tempfile
from pathlib import Path

_out_path = Path(sys.argv[1]).resolve()
OUT_DIR = tempfile.mkdtemp(
    prefix=f".{_out_path.stem}.out2-",
    dir=str(_out_path.parent),
)
atexit.register(shutil.rmtree, OUT_DIR, ignore_errors=True)
```

기존의 선삭제 블록을 제거하고 다음으로 바꿉니다.

```python
shutil.copytree(TPL_DIR, OUT_DIR, dirs_exist_ok=True)
```

각 빌드가 자신만의 고유 작업 트리를 소유하므로 기존 사용자 폴더를 지우지 않고 병렬 빌드도 충돌하지 않습니다.

---

# 4차 B급 회귀

| 항목 | 판정 | 실행·원문 근거 |
|---|---|---|
| ATTEMPT `했으나` 우회 | **차단됨** | `구했으나`, `적었으나` 모두 탐지 |
| ATTEMPT `일부를` 오탐 | **해소됨** | `일부를 빠뜨리거나 모두 수행하지 못함` 비탐지 |
| ATTEMPT `시도하지 못함` 오탐 | **해소됨** | `전혀 시도하지 못함` 비탐지 |
| 판정 순서≠배타성 | **수정됨** | [배타성의 대체물이 아니다](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:281>)로 명시 |
| failure-modes F02 연접 단정 | **수정됨** | 바로 위 급간 범위에 따른 연접/이접으로 교체 |
| codex-review 지필 고정문구 | **수정됨** | 글자·띄어쓰기·마침표 정확 일치 요구 |
| develop-draft truthy 불완전 응답 | **차단됨** | `{}`·필드 누락 모두 throw |
| verify-rubric truthy 불완전 응답 | **차단됨** | 초기 검증·재검 `{}` 모두 throw |
| develop-draft 예시 소개 | **수정됨** | 감사용 few-shot, 복제 가능 블록만 사용하도록 명시 |
| hwpx-build 고아 절차 | **코드는 수정, 문서는 미수정** | §5.6은 차단하지만 문서는 반대로 설명 |
| 표시명/프로파일 분리 | **수정됨** | [표시명과 내부 식별값 분리](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:189>) |
| 키 수 70 | **수정됨** | JSON 70 = 일반 65 + 특수 5 |

## ATTEMPT 실행 근거

현재 [ATTEMPT 정규식](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:608>)을 문서 fenced code에서 직접 추출해 실행했습니다.

```text
"세 비 가운데 하나를 구했으나 그 관계를 설명하지 못함."
→ 탐지 True

"값을 적었으나 관계를 설명하지 못함."
→ 탐지 True

"세 비를 구하는 과정에 오류가 있고 관계를 설명하지 못함."
→ 탐지 True

"일부를 빠뜨리거나 모두 수행하지 못함."
→ 탐지 False

"전혀 시도하지 못함."
→ 탐지 False
```

**판정: 요구한 세 회귀 모두 정상입니다.**

## 워크플로 런타임 검증

두 워크플로의 실제 소스를 mock agent 응답과 함께 실행했습니다. `need()` 구현은 [develop-draft.js](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:17>)와 [verify-rubric.js](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:19>)에 있습니다.

```text
develop draft {}
→ THROW 필수 필드 누락:
  title, scenario, materials, questions, numbers, transfer, verify_log

develop review {"best":"b"}
→ THROW 필수 필드 누락:
  ranking, fixes, grafts

develop valid
→ PASS true

verify initial {}
→ THROW 필수 필드 누락:
  blocking, issues, fixes

verify verdict {"real":true}
→ THROW 필수 필드 누락:
  blocking, reason

verify valid
→ PASS true
```

**판정: 과거 truthy 불완전 객체 fail-open은 차단됐습니다.**

## `hwpx-build.md`의 낡은 고아 설명

현재 다음 문언이 새 §5.6과 정면 충돌합니다.

- [107행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:107>): 검증기는 고아를 검사하지 않는다고 함
- [131행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:131>): 다음 라운드에 검사기로 옮긴다고 함
- [546행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:546>): 고아는 검증기 밖이라고 함
- [565행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:565>): 고아가 남아도 PASS라고 함

이제 실제로는 고아가 남으면 `EXIT 1`입니다.

### 붙여넣기 가능한 일괄 교체

```text
4단계는 건너뛸 수 없다. 제거를 건너뛰면 5단계 `check_tpl2.py`의
「5.6 BinData 정합」에서 고아 BinData가 `[ERR]`로 집계되어 FAIL한다.
아래 수동 명령은 실패 원인을 세부 확인할 때 쓰는 보조 진단이며,
최종 PASS 여부는 `check_tpl2.py`의 종료 코드로 판정한다.
```

검증 통과 표에는 다음을 추가합니다.

```markdown
| 5.5 | 그림 게이트 | 최종 모드, 미매핑 자리표시 0건, 선언·삽입·HPF·ZIP·PNG 정합 |
| 5.6 | BinData 정합 | 고아 0건, 참조 누락 0건, ZIP 누락 0건, 미등록 ZIP BinData 0건, 중복 ID 0건 |
```

`_figs` 설명은 다음으로 바꿉니다.

```text
최종 검증기는 `_figs`가 없어도 콘텐츠 전체에서 줄 시작 `[그림 N]`
자리표시를 찾아 미매핑 항목을 오류로 처리한다. 그림을 쓰면 모든 매핑을
명시하고, 최종 build와 check에는 `--draft`를 붙이지 않는다.
```

---

# 수행·지필 E2E

현재 `rubric-rules.md`의 fenced `rubric_check.py`를 직접 추출해 실행한 뒤, 실제 `build_tpl2.py → restyle.py → 고아 제거 → check_tpl2.py`를 양 프로파일로 수행했습니다. 전체 실행 로그는 [step6.log](</private/tmp/claude-501/-Volumes-ssdmacmini-1-han-ex-projects-123/6981ac5c-4498-45c0-98bf-f487552987cc/scratchpad/r4reg/logs/step6.log:1>)에도 남아 있습니다.

## 수행평가

```text
rubric_check EXIT 0
PASS — 수행평가(최저 1점) /
요소 6개 / 데이터 20행 / 총점 20점 /
floor=6 / 경고 0건

build EXIT 0
모드: 최종
그림 3개 삽입
lineseg 920개
SQUEEZE 다중줄 위반 0건

restyle EXIT 0
treatAsChar 해제 9건
라벨 셀 재작성 52건

고아 제거
image1.bmp, image2.bmp 제거
고아 0 / 참조 누락 0

최신 check_tpl2 EXIT 0
엔트리 14, mimetype method=0, testzip=None
누락 줄 0
_figs 선언 3건
등록 3 / 참조 3
비통일 charPr 0
겹침 0
PASS — 오류 0건 / 경고 1건
```

## 지필평가

```text
rubric_check EXIT 0
PASS — 지필평가(최저 0점) /
요소 6개 / 데이터 26행 / 총점 20점 /
floor=0 / 경고 0건

build EXIT 0
모드: 최종
그림 3개 삽입
lineseg 932개
SQUEEZE 다중줄 위반 0건

restyle EXIT 0
treatAsChar 해제 9건
라벨 셀 재작성 52건

고아 제거
image1.bmp, image2.bmp 제거
고아 0 / 참조 누락 0

최신 check_tpl2 EXIT 0
엔트리 14, mimetype method=0, testzip=None
누락 줄 0
_figs 선언 3건
등록 3 / 참조 3
비통일 charPr 0
겹침 0
PASS — 오류 0건 / 경고 1건
```

두 프로파일의 최종 경고는 문서가 허용한 다음 1건뿐입니다.

```text
[WARN] 서식 원본 유래 폭 초과(허용):
※ 평가 유형(지필평가, 수행평가 등)은 분반(교과)별 운영 방향에 따라 자율적…
```

**E2E 판정: 수행·지필 모두 기술 조판 기준 통과. 최종 경고 정확히 1건.**

다만 E2E의 `rubric_check`는 문언 의미를 판정하지 못하므로, 결함 있는 4단 뼈대가 들어간 현재 `valid` JSON도 통과합니다. E2E 성공은 §3의 A급 의미 결함을 반증하지 않습니다.

---

# 잔여 지적 등급

## A — 시행 전 필수 수정

1. **표준 급간 뼈대 교체**
   - `rubric-rules.md` §3의 2·3·4단을 수행 개수 한 축으로 교체
   - 특히 4단은 원자 수행 3개를 `3/2/1/0개`로 분할
   - `valid-similarity-20pt.json`의 결함 급간도 함께 교체
   - 실제 요소별 `2ⁿ` 전수 결과를 보존

2. **PNG 완전성 검사**
   - `img_embed.py`, `check_tpl2.py`, `figlib.py` 모두 Pillow `verify()+load()` 사용
   - 외부 원본과 ZIP 내장 바이트를 모두 검사
   - 서명만 유지한 잘린 PNG 회귀 추가

3. **`--draft` 승인 우회 폐쇄**
   - 권장: `check_tpl2.py`에서 `--draft` 제거
   - 유지 시 완화가 쓰인 실행은 `DRAFT-ONLY`, 종료 코드 2
   - 최종 승인 계약은 플래그 없음 + 정확한 `PASS` + 코드 0으로 고정

4. **`out2` 데이터 손실·경합 제거**
   - 고정 `out2`와 선행 `rmtree` 제거
   - 출력 파일별 `TemporaryDirectory` 또는 `mkdtemp` 사용
   - 프로세스가 만든 고유 디렉터리만 정리

## B — 함께 고칠 권고

5. §5.6에서 ZIP 단독 `BinData/*`와 `content.hpf` 중복 ID·href 차단  
6. `check_levels`를 `assert` 대신 명시적 `ValueError`로 변경  
7. 지필 자연 분할 공식을 `check_levels`가 직접 강제하도록 `profile` 인자 추가  
8. B-6 문서의 `40벡터`를 실제 `44벡터`로 수정  
9. `hwpx-build.md`의 고아 검사 관련 낡은 여섯 문구 동기화  
10. `figures.md`의 `tools/figs_demo`와 그림 누락 서술 동기화  
11. `content.hpf` 파일 전체 누락 시 §5.5의 uncaught `KeyError` 대신 명시적 ERR 출력  

## C — 정밀성 보완

12. A-6의 `겹침 1·공백 4`가 구조 유형 수임을 명시하고 실제 요소별 수 `3·8` 병기  
13. `check_levels`에서 total·floor·구간 경계의 정수 타입 검사  

---

# 최종 시행 가능 여부

**현재 상태는 시행 불가, 시행 보류입니다.**

양 프로파일의 실제 조판·표 구조·그림 삽입·고아 제거·글꼴 통일·내용 보존은 정상입니다. 과거 A1/A2/A3의 지정 반례도 기본 최종 경로에서는 대부분 닫혔습니다. 그러나 스킬 전체 채점기준의 원형인 4단 표준 뼈대가 실제로 겹침·공백을 만들고, 열리지 않는 잘린 PNG가 최종 승인을 통과하며, `--draft`가 동일한 `PASS`/코드 0으로 최종 게이트를 우회하고, 새 작업 트리가 사용자 `out2/`를 재귀 삭제할 수 있습니다.

따라서 최소 필수 수정은 다음 네 가지입니다.

1. **§3의 2·3·4단 뼈대와 valid JSON을 수행 개수 축으로 교체**
2. **Pillow 기반 PNG 완전성 검사 추가**
3. **`check --draft`의 `PASS`·종료 코드 0 제거**
4. **고정 `out2` 선삭제를 고유 임시 작업 트리로 교체**

이 네 건을 고친 뒤, 잘린 PNG·draft·기존 out2 보존·동시 빌드·표준 뼈대 `2ⁿ` 회귀와 양 프로파일 E2E를 다시 모두 통과해야 시행 가능합니다.
