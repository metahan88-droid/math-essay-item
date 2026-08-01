# 감사 결론

**시행 보류**다. 문서 체계에 최소 **A급 2건**이 남아 있다.

1. 현행 `[수정]` 지시가 급간을 원자 개수축이 아니라 특정 위반의 “1점 귀속”으로 되돌린다.
2. 1단계에서 반드시 복사·실행하라는 수치 검산 스크립트가 실제로 `NameError`로 중단된다.

그 밖에도 최종/초안 모드, 종료 코드 2, 고유 임시 작업 트리, 그림 자리표시 검증, 즉시 BinData 검사, Codex 리뷰 입력 생성, 성취수준 절차 사이에 다수의 B급 불일치가 있다.

감사 대상 7개 문서는 전부 확인했다. `rubric-rules.md`는 권위 기준인 §3만 참고했고, `valid-similarity-20pt.json`은 허용된 사실 대조용으로만 읽었다. 도구 소스는 열어 읽지 않고 실행만 했다. 스킬 폴더를 포함해 **생성·수정한 파일은 0개**다.

다만 지정 작업 폴더 `.../scratchpad/cx6c/`가 존재하지 않았고 읽기 전용 샌드박스가 생성을 거부했다. 따라서 새 HWPX를 만드는 빌드–restyle–고아 제거–check 전 과정을 완주하지는 못했다. 지정 폴더 밖의 기존 HWPX 표본은 최종 판정 근거로 사용하지 않았다.

---

# 실행 검증 로그

## 1. 지정 작업 폴더

```text
$ ls -ld .../scratchpad/cx6c
ls: .../scratchpad/cx6c: No such file or directory
exit 1

$ mkdir -p .../scratchpad/cx6c
mkdir: .../scratchpad/cx6c: Operation not permitted
exit 1
```

최종 빌드도 출력 부모 폴더 생성 단계에서 막혔다.

```text
$ python3 build_tpl2.py .../cx6c/final-missing.hwpx valid-similarity-20pt.json
PermissionError: [Errno 1] Operation not permitted: '.../scratchpad/cx6c'
FINAL_BUILD_EXIT=1
```

따라서 이 로그는 “그림 누락으로 중단”을 확인한 것이 아니다. **출력 폴더 권한에서 먼저 중단된 환경 실패**다.

## 2. 실제 CLI 인터페이스

```text
$ python3 build_tpl2.py --help
사용법: python3 build_tpl2.py <출력.hwpx> <content.json> [--draft]
  위치 인자 1번에 플래그가 왔다: --help
BUILD_HELP_EXIT=1

$ python3 check_tpl2.py --help
사용법: python3 check_tpl2.py <산출.hwpx> <content.json> [--draft]
  위치 인자 1번에 플래그가 왔다: --help
CHECK_HELP_EXIT=1
```

두 도구 모두 실제로 `--draft`를 받으며, 플래그는 두 위치 인자 뒤에 와야 한다. 현재 문서 흐름은 `build_tpl2.py`에만 `--draft`를 붙이고 `check_tpl2.py`에는 붙이지 않는다.

위 명령의 `--help`는 정상 도움말 기능이 아니라 사용법 오류를 내고 종료 코드 1을 반환한다.

## 3. `check_tpl2.py --draft` 인자 위치

```text
$ python3 check_tpl2.py .../cx6c/nonexistent.hwpx valid-similarity-20pt.json --draft
FAIL — 예외로 중단: FileNotFoundError ...
CHECK_DRAFT_MISSING_EXIT=1
```

입력 HWPX가 없어서 의미 검증은 못 했지만, 플래그 위치는 받아들였다.

```text
$ python3 check_tpl2.py --draft .../cx6c/nonexistent.hwpx valid-similarity-20pt.json
사용법: python3 check_tpl2.py <산출.hwpx> <content.json> [--draft]
  위치 인자 1번에 플래그가 왔다: --draft
CHECK_DRAFT_WRONGPOS_EXIT=1
```

## 4. figlib 출력 폴더

파일을 만들지 않고 모듈을 불러 `OUT`만 출력했다.

```text
$ python3 -c '... import figlib; print(figlib.OUT)'
FIGLIB_LIBRARY_OUT=/Volumes/ssdmacmini 1/han ex/projects/123/figs
FIGLIB_IMPORT_EXIT=0
```

```text
$ FIGLIB_OUT=".../cx6c/figs" python3 -c '... import figlib; print(figlib.OUT)'
FIGLIB_LIBRARY_OUT=.../scratchpad/cx6c/figs
FIGLIB_ENV_IMPORT_EXIT=0
```

따라서 [SKILL.md:101](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:101>)과 [figures.md:34](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/figures.md:34>)의 “`FIGLIB_OUT`, 없으면 현재 작업 디렉터리 기준 `./figs`”는 실물과 맞는다.

데모 실행은 지정 폴더 생성 권한 때문에 실패했다.

```text
데모 생성:
PermissionError: [Errno 1] Operation not permitted: '.../scratchpad/cx6c'
FIGLIB_EXPLICIT_EXIT=1
```

## 5. 복붙용 수치 검산 게이트

문서 코드블록을 파일로 만들지 않고 그대로 파이프로 실행했다.

```text
$ sed -n '376,536p' transfer-and-numbers.md | python3 -
── 기초 산출값 ──
...
빅 최소 판 수(16명) = 3
Traceback (most recent call last):
  File "<stdin>", line 94, in <module>
  File "<stdin>", line 24, in rq
NameError: name 'Fraction' is not defined
TRANSFER_GATE_EXIT=1
```

`Fraction`만 `F`로 바꾼 스트림은 끝까지 실행됐다.

```text
── 실패 목록 ──
[동률] 오답 경로 안에서 세 방안의 단가가 완전 동률 → 채점 불능
TRANSFER_GATE_ONE_LINE_FIX_EXIT=0
```

두 번째 로그는 또 다른 문제를 보여 준다. 실패 목록이 남아 있는데도 스크립트가 종료 코드 0을 반환한다.

## 6. 워크플로 파일

내용을 열지 않고 구문 검사만 했다.

```text
DEVELOP_DRAFT_NODE_CHECK_EXIT=0
VERIFY_RUBRIC_NODE_CHECK_EXIT=0
```

`develop-draft.js`와 `verify-rubric.js`는 모두 존재하고 JavaScript 구문은 유효하다.

## 7. 실제 예시 JSON

```text
최상위 키          71개
일반 키            65개
특수 키             6개
rubric_rows         21행
  데이터 행         20행
  합계 행            1행
채점 요소            6개
최고점 합           20점
성취수준 구간       18~20 / 16~17 / 10~15 / 8~9 / 0~7
```

따라서 [hwpx-build.md:17](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:17>)과 [hwpx-build.md:151](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:151>)의 “71키 = 일반 65 + 특수 6” 주장은 정확하다.

Codex 리뷰 변환기를 실제 예시에 적용하면 다음처럼 합계가 훼손된다.

```text
문항 4 | 조건 구분하고 지름 구하기 | 1점 | ...
합계 | — | 20점점 | 문항 1부터 문항 4까지의 점수를 합하여 20점 만점으로 함.
```

---

# 검증 1 — 구 급간 뼈대와 좋은 예

## 문서별 판정

| 문서 | 판정 |
|---|---|
| `SKILL.md` | 구 뼈대 지시 없음. [66~69행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:66>)이 현행 §3을 그대로 따르라고 올바르게 지시 |
| `failure-modes.md` | 구 뼈대 문자열 대부분은 결함 사례·“쓰지 않는다” 대비문으로 적절히 격리됨. 단, 활성 `[수정]` 한 곳이 개수축을 직접 위반 |
| `hwpx-build.md` | [353~359행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:353>)은 접속 선택 폐기와 구 뼈대 금지를 올바르게 설명. 하지만 “좋음” 최고 급간이 현행 문안 규칙을 어김 |
| `standards.md` | 연접·이접 구 뼈대는 없지만, [366행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:366>)의 활성 규칙이 “요소의 유무” 축을 지시 |
| `figures.md` | 급간 관련 구 뼈대 없음 |
| `codex-review.md` | 구 뼈대를 직접 지시하지는 않지만 필수 리뷰 프롬프트에 새 개수축 검사가 빠져 있음 |
| `transfer-and-numbers.md` | `k→k²→k³ 세 층위`는 오개념 층위이지 채점 급간 구 뼈대가 아님. 연접·이접 지시 없음 |

구 뼈대가 결함 사례로 올바르게 남은 대표 위치는 [failure-modes.md:46](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:46>), [64행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:64>), [328행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:328>), [hwpx-build.md:359](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:359>)이다. 모두 “옛 문안”, “나쁨”, “쓰지 않는다”로 표시되어 있어 그 출현 자체는 결함이 아니다.

## A-1 — 활성 `[수정]`이 특정 오류를 무조건 1점으로 보냄

[failure-modes.md:72](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:72>):

> “그 요건만 미충족, 1점 급간”을 명시한다.

이것은 결함 사례가 아니라 F02의 현행 `[수정]` 지시다.

- `옳게 수행한 원자의 개수`를 세지 않는다.
- `미충족`이라는 별도 축을 쓴다.
- 배점·원자 수와 관계없이 1점으로 고정한다.
- 3점·원자 3개 요소에서 해당 요건 하나만 틀리고 나머지 둘이 옳다면 새 축의 판정은 2점이지 1점이 아니다.
- [failure-modes.md:11](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:11>)의 “이 문서의 `[수정]` 급간 문안은 모두 개수축으로 옮겼다”는 사실 주장도 이 행 때문에 거짓이다.

붙여넣기 수정안:

```md
- (ㄹ) 원주율 3.14 사용을 채점하려면 이를 독립 원자 수행(`원주율 규칙 지키기`)으로 정의하고, 다른 원자 수행과 함께 옳게 수행한 개수로 판정한다. 특정 위반 답안을 1점 급간에 고정 귀속시키지 않는다. 원주율 선택 자체를 채점하지 않을 의도라면 해당 요구를 〈조 건〉에서 삭제하고 인정 범위를 〈채점 시 유의점〉에 적는다.
```

## B-1 — 현행 “좋은 예”에 정답 수치가 들어감

[failure-modes.md:69](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:69>):

> 한 변 63 cm와 두께 조건에 따른 부피 배수를 모두 옳게 구함.

`모두`는 들어 있어 개수축 자체는 맞지만, 급간 안에 `63 cm`라는 정답 수치가 남았다. 권위 §3은 수치 예시를 유의점으로 보내도록 한다.

교체안:

```md
"**2점** — 한 변 구하기와 부피 배수 구분하기를 모두 옳게 수행함."(31자) / "**1점** — 한 변 구하기와 부피 배수 구분하기 가운데 한 가지 이상을 옳게 수행하지 못함."(44자)
```

`63 cm`, `27배`, `9배`는 예시 답안이나 채점 시 유의점으로 옮기면 된다.

## B-2 — 수행평가에 복사할 수 있는 `[0~2점]`이 여전히 `[수정]`에 남음

[failure-modes.md:97](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:97>)은 `[수정]`으로 `산출 요소 [0~2점]`, `관계 설명 요소 [0~1점]`을 제시한다. [98행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:98>)은 `[0~1점]`만 그대로 쓰지 말라고 강조한다.

수행평가 기본 프로파일에서는 `[0~2점]` 역시 0점 급간 때문에 그대로 쓸 수 없다.

교체안:

```md
**위 `[0~2점]`과 `[0~1점]`은 모두 당시 권고의 표기이며 수행평가 프로파일에 그대로 복제하지 않는다.** 현행 수행평가에서는 독립 요소를 각각 2점 이상으로 두고 최저 급간을 1점으로 하거나, 한 요소 안에서 `산출`·`관계 설명`을 독립 원자로 정의하여 옳게 수행한 개수로 판정한다. 지필평가에서만 요소마다 고정 0점 급간을 둔다.
```

## B-3 — 일반 뼈대 요약에서 2단 특례가 빠짐

[failure-modes.md:332](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:332>)은 현행 뼈대를 다음처럼 요약한다.

> 모두 / 세 가지만 / 한두 가지만 / 한 가지도 … 못함

2단 최저 급간의 필수 문안인 `한 가지 이상을 옳게 수행하지 못함`이 빠졌다. 이 요약을 2단에 복사하면 원자 하나를 옳게 한 답안이 공백으로 남는다.

교체안:

```md
**[수정]** 급간 뼈대를 **옳게 수행한 원자 개수**로 고정한다. 2단은 `모두 옳게 수행함 / 한 가지 이상을 옳게 수행하지 못함`, 3·4단은 `모두 옳게 수행함 / N가지만 옳게 수행함 / 한 가지도 옳게 수행하지 못함`으로 쓴다. 인정 범위·동등 경로·용어 요건은 〈채점 시 유의점〉과 〈부분 인정 기준〉으로 옮긴다.
```

## B-4 — 각 이접지·연접지의 `옳게` 누락을 검사가 놓침

[failure-modes.md:337](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:337>)은 “각 이접지·연접지마다 `옳게`가 있어야 한다”고 설명하지만 실제 검사는 문장 전체의 `옳게`가 0건인지만 본다. 최종 프롬프트 [507~508행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:507>)도 동일하다.

따라서 다음 오류가 통과한다.

```text
A를 옳게 수행하지 못하거나 B를 수행하지 못함.
```

수정안:

```md
- (c) 부정형 각 절에 `옳게` 누락 — 문장 전체에서 `옳게`가 0건인지만 보지 않는다. `못하거나`·`못하고`로 이접지·연접지를 분리한 뒤 각 절에 `옳게`가 1건 이상 있는지 검사한다. 어느 한 절이라도 `옳게`가 없으면 착수 축 위반으로 차단한다.
```

최종 프롬프트도 다음으로 맞춘다.

```md
(c) 부정형 급간은 `못하거나`·`못하고`로 절을 분리하고 각 이접지·연접지마다 `옳게`가 있는지 확인하라. 문장 전체에 `옳게`가 한 번 있다는 이유로 통과시키지 마라.
```

## B-5 — 상세 검사와 최종 필수 프롬프트가 서로 다름

- [failure-modes.md:335](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:335>)는 `다섯`까지 검사하지만 [506행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:506>)은 `네`까지만 검사한다.
- [338행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:338>)의 `려 하였으나`, `일부를 옳게`, 모호어 6종이 [508행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:508>)에서 빠졌다.
- [334행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:334>)의 `~로 본다`가 [505행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:505>)에서 빠졌다.
- [320행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:320>)의 학생 지면 금칙어 `배점 요소`가 [502행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:502>)에서 빠졌다.

최종 프롬프트 교체안:

```md
  개수 축 위반도 함께 검사하라 —
  (a) `가운데 (한두|한|두|세|네|다섯|여섯|일곱|여덟|아홉|열|\d+) 가지` 뒤에 `만`·`도`가 없고 `이상`도 아닌 급간,
  (b) 2단 요소인데 최저 급간이 `한 가지도 … 못함`인 요소,
  (c) 부정형 각 이접지·연접지 가운데 `옳게`가 없는 절,
  (d) `하였으나·했지만·려 하였으나·시도·일부만·일부를 옳게·일부 오류·오류가 있음·하나만 하거나`가 있는 급간,
  (e) `미흡·부족·다소·대체로·적절히·충분히`가 있는 급간.
  `가운데 한 가지`는 개수 축의 표준 어구이므로 그 자체를 결함 표지로 삼지 마라.
```

## B-6 — `hwpx-build.md`의 최고 급간 “좋음”이 `모두`를 빠뜨림

두 곳이다.

- 예시 `rubric_rows`: [hwpx-build.md:313](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:313>)
- “좋음(v6)” 예: [hwpx-build.md:364](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:364>)

현재 문안:

> 세 피자의 지름·넓이·부피의 비를 옳게 구하고 그 관계를 옳게 설명함.

문법상 여러 수행의 정오를 말하고 있지만, 현행 §3의 최고 급간 고정 규칙인 “원자 전부를 나열하고 `모두 옳게`로 한정”을 따르지 않는다. 실제 `valid` JSON은 이미 이를 올바르게 고쳤다.

교체안:

```text
지름의 비·넓이의 비·부피의 비·관계 설명을 모두 옳게 수행함.
```

JSON 예시도 다음으로 교체한다.

```json
"desc": "지름의 비·넓이의 비·부피의 비·관계 설명을 모두 옳게 수행함."
```

## B-7 — `standards.md`가 활성 규칙으로 “요소의 유무” 축을 지시

[standards.md:366](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:366>):

> 급간은 관찰 가능한 요소의 유무로만 가른다.

“답안에 요소가 있는가”는 착수·출현 축으로 읽힐 수 있다. 현행 축은 **옳게 수행한 원자의 개수**다.

교체안:

```md
위계 조절 어휘는 성취수준 진술에만 쓴다. 채점기준표 급간은 요소마다 미리 확정한 원자 수행 가운데 **옳게 수행한 원자의 개수**로만 가른다. 원자의 단순 출현·착수·완성도는 급간 축으로 쓰지 않는다.
```

## B-8 — 필수 Codex 프롬프트가 새 축을 검사하지 않음

[codex-review.md:71](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:71>)~[74](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:74>)은 배타성·포괄성과 최저 급간은 검사하지만 다음을 요구하지 않는다.

- 원자 수행을 먼저 확정
- 옳게 수행한 원자 개수만을 단일 축으로 사용
- `만`·`도`
- 최고 급간의 `모두`
- 2단 최저의 `한 가지 이상`

추가안:

```md
각 요소의 원자 수행을 먼저 열거하고, 모든 급간이 `옳게 수행한 원자의 개수`만을 축으로 쓰는지 검사하라. 최고 급간은 원자 전부를 `모두 옳게`로 한정하고, 중간 급간의 개수는 `N가지만`, 3·4단 최저 급간은 `한 가지도 옳게 수행하지 못함`, 2단 최저 급간은 `한 가지 이상을 옳게 수행하지 못함`으로 쓰였는지 확인하라. `하였으나·일부만·시도` 등 착수·완성도 축이 들어간 문안은 배타성 전수 열거가 우연히 통과하더라도 결함으로 보고하라.
```

## B-9 — 모호어 목록이 문서마다 다름

- [failure-modes.md:74](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:74>), [338행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:338>): `미흡·부족·다소·대체로·적절히·충분히`
- [hwpx-build.md:366](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:366>): 위 6개에 `적절하게·어느 정도·나름대로`를 추가하고 “같은 목록”이라고 주장

붙여넣기 수정안:

```md
모호어 차단 목록의 단일 권위는 `references/rubric-rules.md` §3 「형식 규칙」으로 한다. 이 문서에서 별도 목록을 복제하지 말고 그 목록을 그대로 적용한다. 추가 탐지어를 운영하려면 권위 목록과 구분하여 `권고 경고 목록`으로 명시한다.
```

---

# 검증 2 — 도구 동작 서술

## B-10 — `_figs` 설명이 폐기된 동작을 사실처럼 적음

[hwpx-build.md:289](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:289>)은 현재도 다음처럼 동작한다고 말한다.

- `_figs` 생략 시 기본 `FIGS`로 조용히 대체
- 그림 게이트는 `_figs`가 있을 때만 실행
- 그림이 빠진 산출물이 `PASS`

이는 사용자께서 제시한 현행 동작, 즉 “최종 기본 모드에서 미매핑 자리표시는 검증 오류”와 정면 충돌한다. 같은 문서의 최신 §5.5·최종/초안 개념과도 맞지 않는다.

교체안:

```md
`{자리표시 문자열: [BinData id, PNG 경로]}`. 그림을 하나라도 쓰면 사용하는 그림 전부를 `_figs`에 명시한다. 최종 모드에서는 본문의 그림 자리표시가 `_figs` 및 실제 PNG와 완전히 대응해야 한다. 선언한 PNG가 없으면 `build_tpl2.py`가 빌드를 중단하고, 산출물에 미매핑 자리표시가 남으면 `check_tpl2.py` §5.5가 `[ERR]`로 집계한다. 그림 미완성을 허용하는 것은 `--draft`뿐이며, 완화가 발생한 초안은 `DRAFT-ONLY`와 종료 코드 2를 반환하므로 제출본으로 취급하지 않는다.
```

## B-11 — 초안 모드 문서 흐름이 `check_tpl2.py --draft`를 빠뜨림

- [SKILL.md:102](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:102>), [113행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:113>)은 빌더에만 `--draft`를 붙인다.
- [SKILL.md:116](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:116>)의 checker에는 `--draft`가 없다.
- [hwpx-build.md:48](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:48>), [140행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:140>)은 초안 명령 자체를 설명하지 않는다.
- [figures.md:160](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/figures.md:160>)~[172](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/figures.md:172>)은 빌드만 설명한다.
- 실제 CLI는 builder와 checker 모두 `[--draft]`를 받는다.

[hwpx-build.md:548](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:548>)의 “종료 코드 0/1”도 초안 완화 코드 2를 누락한다.

붙여넣기용 실행 설명:

```md
플래그를 생략하면 최종 모드다. 최종 제출에서는 `build_tpl2.py`와 `check_tpl2.py` 모두 플래그 없이 실행하고 종료 코드 0만 성공으로 인정한다.

그림 미완성 상태의 반복 작업에서만 두 명령 모두 끝에 `--draft`를 붙인다. 초안 모드에서 완화가 실제 발생하면 `DRAFT-ONLY`와 종료 코드 2를 반환한다. 코드 2는 초안 산출물이 만들어졌다는 뜻이지 최종 제출 성공이 아니다. 초안에서도 일반 오류는 종료 코드 1이다.
```

붙여넣기용 셸 예:

```bash
if python3 "$S/tools/build_tpl2.py" "$WORK/out.hwpx" "$WORK/content.json" --draft; then
  draft_build_rc=0
else
  draft_build_rc=$?
fi
case "$draft_build_rc" in
  0|2) ;;
  *) exit "$draft_build_rc" ;;
esac

python3 "$S/tools/restyle.py" "$WORK/out.hwpx"

if python3 "$S/tools/check_tpl2.py" "$WORK/out.hwpx" "$WORK/content.json" --draft; then
  draft_check_rc=0
else
  draft_check_rc=$?
fi
case "$draft_check_rc" in
  0|2) ;;
  *) exit "$draft_check_rc" ;;
esac
```

제출본은 반드시 두 명령 모두 `--draft` 없이 다시 실행해야 한다.

## B-12 — 고정 `out2/` 설명이 현행 고유 임시 작업 트리와 불일치

[hwpx-build.md:19](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:19>)은 고정 이름 `out2/`를 만들고 사용자가 지워도 된다고 설명한다. 현행은 산출물 폴더 옆의 **빌드별 고유 임시 폴더**다.

교체안:

```md
**R1.** `build_tpl2.py`는 스크립트 파일이 있는 폴더를 기준으로 `tpl2/`와 `ref_parapr_*.xml` 읽기 전용 원본을 찾는다. 빌드 작업 트리는 산출 `.hwpx`의 부모 폴더 아래에 빌드마다 고유한 임시 폴더로 만들고 종료 시 정리한다. 고정 이름 `out2/`를 가정하거나 사용자가 직접 삭제하지 않는다. 따라서 스킬 폴더의 도구를 그대로 실행하되 산출물 경로만 작업 폴더 안으로 지정한다.
```

[hwpx-build.md:34](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:34>)~[38](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:38>)의 고정 `/private/tmp/hwpx-build`와 `rm -rf`도 작업 간 충돌과 오삭제 위험이 있다.

교체안:

```bash
OUTPUT_DIR=<산출물 폴더>
WORK="$(mktemp -d "$OUTPUT_DIR/.hwpx-work.XXXXXX")"
SKILL="/Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item"
```

## B-13 — 즉시 BinData 확인기가 §5.6과 동등하지 않음

[hwpx-build.md:109](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:109>)은 즉시 검사와 §5.6이 “같은 것”을 본다고 주장한다. 그러나 [112~122행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:112>)과 [574~584행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:574>)의 코드는 다음 둘만 본다.

- 고아
- XML에서 참조하지만 매니페스트에 없는 ID

§5.6이 새로 보는 세 번째 오류, 즉 **매니페스트에는 있으나 ZIP에 실제 파일이 없는 경우**를 검사하지 않는다. 또한 실패 문자열을 인쇄해도 `sys.exit`가 없어 셸 종료 코드는 0이다.

반면 [546행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:546>), [550행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:550>), [572행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:572>)의 **실제 §5.6 본문 설명 자체는 현행 변경 명세와 맞는다.** 결함은 즉시 확인기를 동등한 검사라고 부르는 데 있다.

교체 코드:

```python
import zipfile, re, sys

z = zipfile.ZipFile(sys.argv[1])
names = set(z.namelist())
x = z.read("Contents/section0.xml").decode()
h = z.read("Contents/content.hpf").decode()

used = set(re.findall(r'binaryItemIDRef="([^"]+)"', x))
items = dict(re.findall(
    r'<opf:item id="([^"]+)" href="(BinData/[^"]+)"',
    h
))

orphan = {k: v for k, v in items.items() if k not in used}
manifest_missing = used - set(items)
zip_missing = {k: v for k, v in items.items() if v not in names}

print("고아", orphan)
print("참조되나 매니페스트에 없음", manifest_missing)
print("매니페스트에 있으나 ZIP에 없음", zip_missing)

ok = not orphan and not manifest_missing and not zip_missing
print("BinData 검사:", "OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

## B-14 — `content.json`을 선택 인자처럼 표기

- [failure-modes.md:368](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:368>)
- [failure-modes.md:518](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:518>)

두 곳 모두 `[content.json]`으로 표기한다. 반면 [hwpx-build.md:143](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:143>)은 필수라고 명시하며, 실제 CLI 사용법도 `<content.json>`이다.

교체안:

```text
python3 <스킬 루트>/tools/check_tpl2.py <산출.hwpx> <content.json> [--draft]
```

## 그림 출력 위치 판정

다음은 통과했다.

- [SKILL.md:101](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:101>)
- [figures.md:34](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/figures.md:34>)~[42](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/figures.md:42>)
- [figures.md:82](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/figures.md:82>)~[90](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/figures.md:90>)

실행으로 `FIGLIB_OUT` 우선, 미설정 시 cwd 기준을 확인했다. 슬롯 그림 경로를 콘텐츠 JSON 폴더 기준으로 잡는 설명도 [hwpx-build.md:21](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:21>)과 [figures.md:42](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/figures.md:42>)에서 일치한다.

---

# 검증 3 — 문서 간 모순, 수치, 죽은 참조

## A-2 — 복붙용 수치 검산 스크립트가 실행되지 않음

[transfer-and-numbers.md:378](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:378>)은 다음만 가져온다.

```python
from fractions import Fraction as F
```

그런데 [399행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:399>)은 정의되지 않은 `Fraction`을 사용한다.

```python
isinstance(x, Fraction)
```

문서는 [369행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:369>)에서 그대로 복사하라고 하고 [371행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:371>)에서 이 함수 정의부를 손대지 말라고 한다. 실제 실행은 첫 단위량당 값 계산에서 `NameError`, 종료 코드 1이었다.

수정:

```python
def rq(x, q="0.1"):
    return (
        Decimal(x.numerator) / Decimal(x.denominator)
        if isinstance(x, F)
        else Decimal(str(x))
    ).quantize(Decimal(q), rounding=ROUND_HALF_UP)
```

또 [535~536행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:535>)은 실패를 출력만 하고 종료 코드를 바꾸지 않는다. 실제로 `[동률]`이 남았는데 종료 코드 0이었다.

마지막을 다음처럼 고쳐야 자동 게이트가 된다.

```python
print("\n── 실패 목록 ──")
print("\n".join(FAIL) if FAIL else "없음")
raise SystemExit(1 if FAIL else 0)
```

## B-15 — G9 동률 처리 지시가 서로 모순

- [transfer-and-numbers.md:323](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:323>)~[325](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:325>): 수치를 안 바꾸고 유의점으로 처리해도 된다고 허용
- [329행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:329>): 실패가 하나라도 있으면 수치를 고치라고 지시
- [508~510행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:508>): 동률이면 조건 없이 `fail`
- [552행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:552>): 다시 유의점 처리를 허용
- [553행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:553>): 실패 목록이 없을 때만 제출

유의점만 넣으면 코드의 `[동률]` 실패는 영원히 없어지지 않는다.

교체안:

```md
→ **검사 항목**: 각 오답 경로에서도 선택지별 단위량당 값을 계산한다. 세 값이 모두 같으면 가격 수열이나 부피 수열을 반드시 바꾼다. 유의점만 추가한 채 동률 수치를 유지하는 것은 허용하지 않는다. G9 실패가 남아 있으면 초안을 제출하지 않는다.
```

## B-16 — 학교 규정 오버라이드 뒤에 `floor = 0`을 다시 고정

[standards.md:213](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:213>)과 [219행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:219>)은 프로파일 이름으로 추정하지 말고 학교 규정의 실제 최저 급간을 합산하라고 한다.

그러나 [223행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:223>)과 [232행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:232>)은 다시 지필평가를 무조건 `floor = 0`으로 단정한다.

교체안:

```md
5. 기본 지필평가 프로파일은 각 요소의 최저 급간이 0점이므로 `floor = 0`이다. 학교 규정이 다르면 실제 요소별 최저 급간의 합으로 `floor`를 계산한다. 지필평가는 도달 가능 범위 `[floor, 총점]`의 `R = 총점 − floor + 1`개 점수에 아래 자연 분할 절차를 적용한다.

6. `floor > 0`이면 E의 하한만 0으로 늘려 미응시·미제출 구간을 흡수한다. `floor = 0`이면 프로파일 이름과 관계없이 이 단계를 건너뛴다.
```

작업 노트도 단일 `min_grade`보다 요소별 값이 안전하다.

```json
"interval_basis": {
  "profile": "수행평가",
  "total": 20,
  "n_elements": 6,
  "element_min_grades": [1, 1, 1, 1, 1, 1],
  "floor": 6,
  "reachable": "6..20",
  "R": 15
}
```

## B-17 — 필수 성취수준 각주를 조판할 슬롯이 없음

[standards.md:334](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:334>)은 성취수준 표 바로 아래에 총점·요소 수·floor를 적은 한 줄 각주를 필수로 한다. 최종 점검도 [454행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:454>)에서 이를 요구한다.

그런데 `hwpx-build.md`의 성취수준 표 키는 [237~243행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:237>)의 `level_A~E_score/desc`뿐이다. 각주용 슬롯이나 행이 없다. 실제 `valid` JSON에도 해당 각주가 없다.

즉 앞 단계가 요구한 인쇄물을 뒤 단계가 표현할 수 없다.

문서만으로 즉시 정리하려면 다음처럼 바꿀 수 있다.

```md
R4-5. 성취수준 구간 산출 근거는 작업 노트의 `interval_basis`에 구조화하여 남긴다. 사용하는 HWPX 서식에 전용 각주 행이 있으면 성취수준 표 바로 아래에 인쇄하고, 전용 행이 없으면 `partial`의 마지막 문장으로 총점·요소 수·floor·도달 가능 범위를 적는다.
```

장기적으로는 builder에 `level_basis` 슬롯과 표 행을 추가하는 편이 낫다.

## B-18 — `valid` 예시가 필수 “우연히 정답” 규칙과 충돌

[transfer-and-numbers.md:142](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:142>)~[145](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:145>)은 잘못된 `24개 × 3판 = 72개`를 총 개수 원자로 인정하지 말라고 한다.

실제 예시는 다음을 모두 포함한다.

- 잘못된 경로가 3판: [valid JSON:43](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:43>)
- 오답 24개: [237행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:237>)
- 정답 72개: [304행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:304>)
- 원자 정의는 단순히 “72개를 구함”: [321행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:321>)
- `partial`과 `caution`에는 우연 일치 처리 문장이 없음: [242~253행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:242>)

원자 수정안:

```text
총 개수(윗면 넓이의 비로 자이언트 1판당 36개를 구하고, 옳게 구한 최소 판 수 2를 곱하여 72개를 구함)
```

`partial` 추가안:

```text
잘못 구한 자이언트 1판당 페퍼로니 수 24개와 잘못 구한 판 수 3을 곱하여 우연히 72개가 나온 경우에는 ‘총 개수’ 원자를 옳게 수행한 것으로 인정하지 않음.
```

## B-19 — `valid` 예시가 `standards.md`의 필수 조건을 모두 충족하지 않음

### 한 평가만으로 성취수준 확정 금지 문장

필수 규칙은 [standards.md:375](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:375>)~[379](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:379>)과 최종 점검 [459행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:459>)이다.

예시의 마지막 차시에는 취지가 있지만 `partial/caution`에는 없다.

추가안:

```text
본 평가는 [9수03-12]의 일부를 평가 요소로 설정한 것이므로, 이 수행평가 결과만으로 모든 성취수준을 확정하지 않음. 문항 1부터 문항 4까지의 결과와 형성평가 기록을 함께 고려하여 학기 단위 성취수준을 판정함.
```

### A수준 문장 구조

[standards.md:365](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:365>)은 A·B 모두 `도달 → 도달 → 한계`를 요구한다. 예시 A의 [257~259행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:257>)은 세 문장 모두 도달·확장 서술이다.

A수준에 억지 한계를 붙이기보다 규칙을 다음처럼 고치는 편이 자연스럽다.

```md
R4-9. 구조는 A는 `도달한 것 → 도달한 것 → 확장 과제`, B는 `도달한 것 → 도달한 것 → 한계`, C·D·E는 `도달한 것 → 한계 → 처방`이다. 하위 세 수준(C·D·E)에는 처방 문장을 반드시 1개 넣는다.
```

### “사소한 수치 오차”가 정의되지 않음

예시 [244행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:244>)은 “사소한 수치 오차나 반올림 자리의 차이”를 옳고 그름에 반영하지 않는다고 한다. `사소한`의 수치 범위가 없어 이진 원자 판정이 채점자마다 달라진다.

교체안:

```text
넓이와 부피는 aπ 꼴 또는 원주율을 3.14로 보아 계산한 값을 인정함. 문항 3의 단위량당 값은 소수 첫째 자리 반올림값 또는 세 방안의 대소 관계를 보존하여 같은 결론에 이르게 하는 근삿값만 인정함. 그 밖의 수치 오류는 해당 원자 수행을 옳게 수행하지 못한 것으로 판정함.
```

## B-20 — Codex 리뷰 입력 생성 절차가 그대로는 실행되지 않음

### `make_review_input.py`가 없음

[codex-review.md:25](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:25>)은 다음을 실행하라고 한다.

```text
python3 make_review_input.py <슬롯.json> <출력 디렉터리>
```

다음 세 위치에 파일이 없었다.

```text
MISSING <skill>/make_review_input.py
MISSING <skill>/tools/make_review_input.py
MISSING <skill>/references/make_review_input.py
```

코드블록을 저장하라는 단계도 없다.

수정안:

```md
아래 코드블록을 `$S/make_review_input.py`로 저장한 뒤 다음과 같이 실행한다.

```bash
python3 "$S/make_review_input.py" "<슬롯.json>" "$S"
```

또는 이 코드를 실제 `tools/make_review_input.py`로 제공하고 그 절대경로를 사용한다.
```

### 합계가 `20점점`으로 바뀜

[codex-review.md:52](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:52>)는 모든 `score`에 `점`을 덧붙인다. 합계 행은 [hwpx-build.md:375](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:375>) 규칙상 이미 `"20점"`이다.

수정안:

```python
def with_point_unit(value):
    value = str(value)
    return value if value.endswith("점") else value + "점"

if k == "rubric_rows" and v:
    v = "\n".join(
        f"{r['item'].splitlines()[0]} | {r['elem']} | "
        f"{with_point_unit(r['score'])} | {r['desc']}"
        for r in v
    )
```

### 둘째 성취기준이 코드에서 빠짐

[codex-review.md:32](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:32>)~[34](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:34>)은 필요하면 `std2_*`를 추가하라고 하지만 실제 `order`에는 없다.

추가안:

```python
"std2_text", "std2_A", "std2_B", "std2_C", "std2_D", "std2_E",
```

빈 값은 무해하므로 항상 넣는 것이 안전하다.

### 완료·종료 코드·빈 결과 게이트가 없음

[codex-review.md:9](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:9>)~[18](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:18>)은 백그라운드 실행을 지시하지만 완료 대기, 종료 코드, 비어 있지 않은 결과 검사가 없다.

추가안:

```bash
# 백그라운드 실행이면 먼저 완료될 때까지 wait/poll한다.
codex_rc=$?
if [ "$codex_rc" -ne 0 ]; then
  echo "Codex 검토 실패(exit $codex_rc). $S/codex.err 확인" >&2
  exit "$codex_rc"
fi

test -s "$S/codex_review.md" || {
  echo "Codex 검토 결과가 비어 있음" >&2
  exit 1
}
```

## B-21 — 죽은·비해결 상호참조

### 이름 없는 “운영 지침”

- [transfer-and-numbers.md:58](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:58>): `운영 지침 9`
- [transfer-and-numbers.md:106](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:106>): `운영 지침 5-⑵`

감사 문서 체계 안에 파일명·표제·절 경로가 없다.

58행 교체안:

```md
도해에도 `references/figures.md` §2 「작도 원칙」의 ‘정답을 그림에 흘리지 말 것’을 적용한다. 페퍼로니 배치, 부피 비교, 패밀리 설계처럼 정답을 드러내는 도해는 학생용 지면에 넣지 않고 피드백 자료로만 쓴다.
```

106행 교체안:

```md
역방향 실패가 독립 진단 신호로 쓰이게 배치했는지 확인한다. 정방향 수행만으로 만점이 되는 구조라면 역방향 원자를 별도 채점 대상으로 다시 설계한다.
```

### 역사 파일명이 경로 없이 남음

[standards.md:301](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:301>)의 `content2_v6.json`, [313행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:313>)의 `content_b_v6.json`은 스킬 루트와 `examples/` 아래에서 찾지 못했다. 역사 사례라면 “현재 배포 파일”처럼 읽히지 않도록 경로를 제거하거나 `valid-similarity-20pt.json`으로 사실 대조 대상을 통일하는 편이 낫다.

## 수치·공식 중 통과한 항목

- 급간 길이: 한 문장 25~45자 권장, 50자 초과 차단이 `SKILL`, `failure-modes`, `hwpx-build`에서 일치한다.
- 현재 좋은 예로 분류된 `failure-modes` 급간 16개는 표기 자수와 실제 `len()`이 모두 일치했다.
- 채점 요소 6~16자와 문항 열 평가 요소 10~17자는 서로 다른 대상이며, 실제 JSON은 각각 13~15자와 15~17자로 통과했다.
- 실제 예시 키 수 71은 `hwpx-build.md`의 주장과 일치한다.
- 행 수 공식은 기본 프로파일에서 일치한다.
  - 수행평가: 데이터 행 수 = 총점
  - 지필평가: 데이터 행 수 = 총점 + 요소 수
  - 실제 수행평가 예시: 총점 20, 데이터 행 20, 합계 행 별도 1
- 최저 급간 기본 규칙은 문서 사이에 일치한다.
  - 수행평가: 1점, 요소 배점 2점 이상
  - 지필평가: 고정 0점 행, 1점 요소 허용
- 실제 성취수준 구간은 `floor=6`, `R=15`, 도달 개수 `3/2/6/2/2`이고, 공백·겹침 없이 C가 유일 최대다.

---

# 검증 4 — SKILL 0~6단계 실행 가능성

| 단계 | 확인 결과 |
|---|---|
| 0 입력 | 핵심 평가 정책은 대부분 묻는다. 문항 수를 두 번 묻고, HWPX의 소속기관·성명·분반, 산출 폴더·파일 기본명은 받지 않는다 |
| 1 초안·검산 | `develop-draft.js` 존재·구문 정상. 그러나 필수 수치 게이트가 A-2 `NameError`로 중단 |
| 2 사용자 선택 | 앞 단계의 세 초안을 전제로 하며 선후관계 정상 |
| 3 슬롯 JSON | 예시 JSON 존재, 71키·20데이터행 사실 확인. 다만 standards의 인쇄용 각주를 표현할 슬롯이 없음 |
| 4 세 겹 검증 | `verify-rubric.js` 존재·구문 정상. Codex 입력 생성 파일 부재, `20점점`, 새 급간 축 누락, 완료 게이트 부재 |
| 5 그림 | figlib 경로와 출력 기준 정상. gpt-image 브리지 파일도 존재. 단, 의미 검증 뒤에 그림을 만들어 그림 속 수치가 세 겹 검증을 우회 |
| 6 조판 | build/restyle/check 도구 존재. 초안 checker 플래그·코드 2·고유 임시 폴더·즉시 BinData 검사가 문서와 불일치. 지정 폴더 권한 때문에 완주 실행은 미검증 |

## B-22 — 의미를 담은 그림이 세 겹 의미 검증 뒤에 생성됨

- 세 겹 검증: [SKILL.md:75](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:75>)~[90](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:90>)
- 가격표·치수·대화문 그림 생성: [92~102행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:92>)
- 조판 뒤 재검은 F22 구조 검사만: [123행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:123>)

그림 속 가격·치수·문구는 발문과 동등한 평가 입력이다. 제작 중 숫자가 달라져도 어긋남 리뷰와 Codex 수학 검증을 다시 받지 않는다.

추가안:

```md
문항 내용을 담는 그림과 `_figs` 매핑을 완성한 뒤 4단계의 (b) 어긋남 리뷰와 (c) Codex 적대적 검증을 다시 실행한다. 그림 속 수치·문구·기호를 발문·조건·예시답안·채점기준과 전수 대조하고, 하나라도 달라지면 수정 후 재검한다. 분위기 삽화처럼 문항 정보가 전혀 없는 그림만 이 재검 대상에서 제외한다.
```

## B-23 — 공유 스킬의 워크플로 원본을 “고쳐 쓴다”고 지시

- [SKILL.md:54](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:54>)
- [SKILL.md:77](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:77>)
- [SKILL.md:79](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:79>)

문언대로면 공유 설치본이 작업별 수치·경로로 오염된다.

교체안:

```md
스킬 폴더의 워크플로 원본은 수정하지 않는다. 작업 시작 시 `workflows/develop-draft.js`와 `workflows/verify-rubric.js`를 현재 작업의 스크래치 폴더로 복사하고, 작업별 사본만 상황에 맞게 고쳐 실행한다.
```

## B-24 — `WORK`·파일명·HWPX 필수 인쇄 정보가 0단계에서 정해지지 않음

`hwpx-build.md` 슬롯에는 `affiliation`, `name`, `_check_class`가 있지만 [SKILL.md:37](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:37>)~[48](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:48>)은 이를 받지 않는다. [109행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:109>)은 갑자기 `WORK`를 요구하고, [130행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:130>)은 버전 접미사를 요구하지만 실행 예는 고정 `out.hwpx`다.

0단계 추가안:

```md
- **소속기관·성명·분반(교과)** — HWPX 첫 페이지에 인쇄할 값과 `_check_class` 값을 확정한다.
- **산출물 폴더와 파일 기본명** — 기본 산출물 폴더는 현재 사용자 프로젝트 폴더로 한다. 같은 이름이 있으면 덮어쓰지 않고 `_v2`, `_v3` 접미사를 붙인다. 이 확정 경로를 이후 단계의 `WORK`와 `OUT_HWPX`로 계속 사용한다.
```

## B-25 — SKILL의 조판 코드블록은 고아 제거를 실제로 실행하지 않음

[SKILL.md:106](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:106>)은 고아 제거를 순서에 넣지만 [115행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:115>)에는 주석만 있고 [116행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:116>)에서 곧바로 checker를 실행한다.

최소 수정안:

```md
# 주의: 다음은 설명 주석이 아니라 필수 실행 단계다.
# references/hwpx-build.md §1의 4단계 고아 BinData 제거 스크립트 전체를
# 이 위치에서 실행한 뒤에만 check_tpl2.py로 넘어간다.
```

가장 안전한 해결은 제거 스크립트를 코드블록 안에 직접 인라인하는 것이다.

## C급 명료화

### C-1 — 문항 수를 두 번 묻음

[SKILL.md:43](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:43>)과 [48행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:48>)을 합친다.

```md
- **총점·문항 수·문항별 배점** — 현재 서식·도구는 4문항 전용이다. 기본값은 20점 4문항(4/4/7/5)이고, 15점이면 4문항(3/3/5/4)이다. 4문항이 아닌 경우에는 조판 없이 텍스트 산출까지만 지원한다.
```

### C-2 — “백그라운드”와 실제 동기 명령이 어긋남

[SKILL.md:81](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:81>)은 백그라운드라 하지만 제시 명령에는 `&`, 작업 ID, `wait`가 없다.

```md
**(c) Codex 적대적 검증** — 필수. 별도 프로세스로 실행하고 종료까지 기다린 뒤 결과 파일과 종료 코드를 확인한다.
```

### C-3 — `PROFILE`을 설정하지만 검사 함수가 사용하지 않음

[standards.md:236](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:236>)에서 `PROFILE`을 설정하고 최종 점검 [451행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:451>)도 맞추라고 하지만 `check_levels()`는 `PROFILE`을 인자로 받지도, 전역값으로 읽지도 않는다. 실제 판정은 `floor`에 의존한다.

수정 방향은 둘 중 하나다.

```md
`PROFILE` 변수는 설명용이며 `check_levels()` 판정에는 사용되지 않는다. 검사는 채점기준표에서 계산한 실제 `floor`를 기준으로 한다.
```

또는 함수에 `profile`을 인자로 넣어 지필 자연 분할 검산까지 실제 구현한다.

### C-4 — “6칸 전부 상이”와 실제 코드가 다름

[transfer-and-numbers.md:140](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:140>)과 [342행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:342>)은 6칸 모두가 달라야 한다고 하지만 실제 코드 [492~494행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:492>)은 단위가 같은 각 열 안의 세 값만 비교한다. 코드 쪽이 합리적이다.

```md
**M5. 각 자리 안에서 세 지수 경로의 값이 서로 다른지 확인한다.** 단위가 같은 한 자리 안에서 k·k²·k³ 값이 겹치면 답안에서 경로를 복원할 수 없다. 단위가 다른 두 자리 사이의 수치는 서로 비교하지 않는다.
```

### C-5 — “단위량당 값 하나”의 뜻이 불분명

[transfer-and-numbers.md:225](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:225>)은 예외를 “단위량당 값 하나”라고 하지만 실제로는 선택지별 값 세 개를 계산한다.

```md
예외는 조건에서 학생이 선택하는 **한 종류의 단위량당 값**뿐이다. 선택지별로 계산하는 여러 수치는 이 한 종류에 포함한다.
```

---

# 최종 시행 가능 여부

**현재 문서 체계는 시행 불가, 정확히는 “시행 전 필수 수정 및 재검” 상태다.**

도구 구현 자체가 전부 고장 났다는 판정은 아니다. 오히려 `build_tpl2.py`와 `check_tpl2.py`가 모두 `--draft`를 받는 것, figlib 출력 기준, 워크플로 파일 존재·구문 등 일부 현행 동작은 확인됐다. 문제는 문서가 그 구현을 일관되게 설명하지 못하고, 필수 수치 게이트와 필수 리뷰 준비 절차가 문서대로는 실행되지 않는다는 점이다.

시행 승인 전 최소 조건은 다음과 같다.

1. `failure-modes.md:72`의 고정 1점 귀속을 원자 개수축으로 교체한다.
2. `transfer-and-numbers.md:399`의 `Fraction` 오류와 마지막 종료 코드를 고친다.
3. `hwpx-build.md:289`, `548`과 SKILL/figures의 초안 절차를 최종·초안·종료 코드 `0/1/2` 계약으로 통일한다.
4. draft에서는 `build_tpl2.py`와 `check_tpl2.py` 모두 `--draft`를 사용하도록 한다.
5. 고정 `out2/` 설명을 고유 임시 작업 트리로 교체한다.
6. 즉시 BinData 검사에 ZIP 누락과 실패 종료 코드를 추가한다.
7. Codex 리뷰 입력 생성 파일 또는 저장 단계를 제공하고 `20점점`, `std2_*`, 종료 코드 게이트를 고친다.
8. 의미를 담은 그림을 만든 뒤 어긋남·Codex 의미 검증을 다시 돌린다.
9. `valid` 예시의 우연히 맞은 72개 판정, 수치 오차 범위, 성취수준 필수 문장을 정리한다.
10. 쓰기 가능한 지정 `cx6c/`에서 다음을 실제 재현한다.

```text
최종 정상 build/check                         → 0
최종 모드의 매핑된 PNG 누락 build            → 중단, 비정상
최종 모드의 미매핑 자리표시 check             → 1
초안 완화 build/check                         → 2
고아 BinData                                  → 1
참조되나 매니페스트에 없음                    → 1
매니페스트에 있으나 ZIP에 없음                → 1
고아 제거 후 §5.6 clean                       → 0
restyle 후 표내 charPr·SQUEEZE·셀 주소 검사   → PASS
Codex 리뷰                                    → 종료 0 + 비어 있지 않은 결과
수치 검산 게이트                              → 실패 목록 없음 + 종료 0
```

A급 두 건 중 하나라도 남아 있으면 문항 수치가 검산되지 않거나 급간이 잘못 귀속될 수 있으므로, **현재 상태에서 실제 평가 문항을 생성·조판해 시행하는 것은 승인할 수 없다.**
