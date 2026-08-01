# 2차 재감사 결과

종합 판정은 **승인 보류**입니다.

보고된 12개 수정 중:

- **완전 확인: 6건** — 1, 4, 5, 8, 9, 11
- **부분 확인: 6건** — 2, 3, 6, 7, 10, 12
- **전혀 미반영: 0건**

즉, 수정 문구나 코드가 아예 빠진 항목은 없지만, 일부는 구현이 불완전하거나 다른 파일과 충돌합니다. 특히 다음 네 건은 시행·배포 전에 반드시 고쳐야 합니다.

1. 이름이 `valid`인 예시가 스킬 자체의 성취기준 정렬 규칙을 위반함.
2. 조판 전 검증 프롬프트가 아직 존재하지 않는 HWPX를 요구하고, 워크플로는 에이전트 실패를 묵살할 수 있음.
3. 필수 그림이 없거나 PNG 변환이 실패해도 최종 구조 검사가 PASS할 수 있음.
4. 오개념 교정 활동에서 `3.95배`를 `4배 확인`에 사용할 수 있다고 한 문서와 사용할 수 없다고 한 문서가 충돌함.

감사는 폴더의 35개 파일 전체를 대상으로 읽기 전용으로 수행했습니다. 파일은 변경하지 않았습니다.

검사 결과:

- Python 6개 전부 `ast.parse` 문법 검사 통과:
  `build_tpl2.py`, `check_tpl2.py`, `figlib.py`, `img_embed.py`, `metrics.py`, `restyle.py`
- JavaScript 2개 전부 `node --check` 통과:
  `develop-draft.js`, `verify-rubric.js`
- `valid-similarity-20pt.json` JSON 파싱 통과
- HWPX 패키지의 XML·HPF·RDF 전부 파싱 통과
- `ref_parapr_84/96/97.xml`은 독립 XML이 아닌 네임스페이스 조각이므로 래퍼로 감싸 파싱했으며 전부 통과
- PNG/BMP 헤더와 크기 확인 통과
- 읽기 전용 환경이므로 실제 `build → restyle → check` 쓰기 파이프라인은 실행하지 않았습니다. 코드 경로, 템플릿 구조, 실제 예시 데이터에 대한 정적·인메모리 검증으로 판단했습니다.

## ① 수정 검증 표

| # | 항목 | 실재 여부 | 직접 확인 및 부작용 |
|---:|---|---|---|
| 1 | `build_tpl2.py` 표 밖 여러 줄 문단 커서 전진 | **완전 확인** | [build_tpl2.py:874](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:874>)에서 일반 문단은 `n_lines = len(segs)`, [876행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:876>)에서 `body = n_lines * (vs + sp)`로 계산합니다. 현 템플릿의 해당 2줄 문단은 두 lineseg의 `vertsize=1500`, `spacing=692`가 같으므로 종전 한 줄분 2,192가 아니라 전체 4,384만큼 전진하여 보고된 겹침 원인은 해소됩니다. 다만 [877~887행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:877>)은 `paraPr.next`를 커서에 더하지 않아 문단 뒤 간격이 압축되는 별도 B급 결함이 남습니다. |
| 2 | `check_tpl2.py` 종료 코드·신규 검사·허용 목록·JSON 오류 | **부분 확인** | PASS/FAIL과 종료 코드는 [277~279행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:277>), 콘텐츠 JSON 미발견 오류 승격은 [193~195행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:193>), 표내 charPr 검사는 [197~226행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:197>), 표 밖 세로 겹침 검사는 [228~275행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:228>)에 실제 존재합니다. 그러나 “정확 문자열 허용 목록”은 미실현입니다. [150~155행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:150>)은 잘린 접두사와 `startswith()`를 사용합니다. charPr 검사 실패가 WARN으로 끝나는 점, 세로 겹침 검사 false negative, ZIP 손상 미집계도 남습니다. |
| 3 | `figlib.py` 옛 PNG 삭제·returncode 검사 | **부분 확인** | 기존 PNG 삭제는 [figlib.py:56](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/figlib.py:56>), 변환 returncode 확인은 [59~62행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/figlib.py:59>)에 있습니다. 하지만 실패를 출력만 하고 예외나 실패 종료로 전파하지 않습니다. 비정상 종료가 부분 PNG를 남기면 크기만 1바이트 이상이어도 성공 처리할 수 있고, PNG가 없으면 `(svg, None)`을 정상 반환합니다. 빌더도 그림 대신 자리표시 텍스트를 남기므로 필수 도해가 없는 HWPX가 PASS할 수 있습니다. |
| 4 | 예시 개명·익명화·도달 가능 구간 | **완전 확인** | [valid-similarity-20pt.json:2](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:2>)에 `○○중학교`, `홍길동`이 있고, [249행 이후](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:249>)의 구간은 `18~20 / 16~17 / 10~15 / 8~9 / 0~7`입니다. 옛 파일과 옛 파일명 참조는 0건입니다. 20개 데이터 행, 6개 요소, 최고 배점 `4/4/4/3/3/2`, 최저 총점 6점이며 가능한 총점은 6~20 전체입니다. 모든 A~E 구간에 도달 가능한 점수가 있습니다. 다만 파일 내용 자체에는 아래의 A급 성취기준 정렬 결함이 남아 있어 이름처럼 완전히 `valid`하지는 않습니다. |
| 5 | `tools/out2/` 삭제 | **완전 확인** | 전체 폴더에서 `out2` 디렉터리는 0건입니다. [build_tpl2.py:22](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:22>)가 실행 시 작업 사본에 `out2`를 다시 만드는 것은 정상 동작이며, [hwpx-build.md:19](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:19>)도 스킬 원본이 아닌 복사한 작업 디렉터리에서 실행하라고 경고합니다. |
| 6 | `SKILL.md` 수정 일괄 | **부분 확인** | `verify-rubric.js` 연결은 [SKILL.md:76](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:76>), OUT 정의는 [80~85행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:80>), 교육과정 연도·학교 정책·4문항 제한은 [45~47행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:45>), 전체 슬롯 조립 책임은 [72행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:72>), 사용자 확정 정책 단서는 [13·15행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:13>)에 실제 존재합니다. 추출본 범위 `3903~3938`, `4615~4680`도 실제 표 섹션을 가리킵니다. 그러나 72행이 실제 키 `item_questions`·`item_cond` 대신 존재하지 않는 `questions`·`cond`를 적습니다. 또한 학교 정책과 전이성 조정을 허용한다는 단서가 후속 워크플로·검사 코드에는 전달되지 않습니다. |
| 7 | `hwpx-build.md` 경로·PASS/FAIL·개명 반영 | **부분 확인** | 그림 기준은 [hwpx-build.md:21](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:21>)과 실제 빌더의 [build_tpl2.py:710~712](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:710>)에서 모두 슬롯 JSON 폴더 기준입니다. 새 예시명은 [17행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:17>) 등에 반영되었고, PASS/FAIL·종료 코드 계약도 [508행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:508>)에 있습니다. 그러나 [115·506행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:115>)은 JSON 미발견 시 검사를 건너뛴다는 구동작을 유지하고, [311행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:311>)은 여전히 경기 자료를 0점 없음의 근거처럼 씁니다. |
| 8 | `rubric-rules.md` 0점 정책 정직화·코드 문자열 대조 | **파일 본체는 완전 확인** | [rubric-rules.md:67~69](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:67>)에 “사용자 확정 기본 정책”, 경기 원문에는 0점 표와 비0점 표가 혼재, 학교 규정 우선이 명시되어 있습니다. 성취기준 코드는 [506~514행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:506>)에서 `CODES`와 문자열 일치로 검사합니다. 다만 `hwpx-build.md:311`과 충돌하고, [rubric-rules.md:416~443](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:416>)의 검사 코드는 여전히 0점 정책을 무조건 FAIL시켜 학교 정책 예외를 실행할 수 없습니다. |
| 9 | `standards.md` 미응시·연도·과제 수행수준 | **완전 확인** | 적용 연도는 [standards.md:71~73](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:71>), 제출 백지와 미응시·미제출의 구분은 [197~209행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:197>), 과제 수행수준 구간이라는 성격은 [236행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:236>)에 실제 반영되었습니다. 이 판정은 해당 문구의 존재와 내부 논리를 확인한 것이며 NCIC 외부 원문을 재검증한 판정은 아닙니다. |
| 10 | `transfer-and-numbers.md` 정책·어댑터·화이트리스트·반올림 | **부분 확인** | 사용자 확정 정책 단서는 [3행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:3>), 닮음 어댑터 한정은 [185~189행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:185>), 광역 `range(0,21)` 제거와 위치 기반 제외는 [428~435행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:428>), `ROUND_HALF_UP`은 [396~399행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:396>)에 있습니다. 그러나 `extra_ok` 숫자 허용 목록이 함수·예시·설명에 여전히 남아 있어 “화이트리스트 전체 제거”는 아닙니다. 반올림도 `Fraction → float → str → Decimal` 경로라 정확 검산을 훼손할 수 있습니다. |
| 11 | `codex-review.md` mktemp·50키 입력 | **완전 확인** | [codex-review.md:10](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:10>)에서 `S=$(mktemp -d)`가 정의되고, [25~56행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:25>)의 인라인 Python은 구문 정상입니다. `order`는 실제로 정확히 50키입니다. 다만 프롬프트는 [64·76행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:64>)에서 중학교로 고정되고, [73행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:73>)에서 학교 정책과 무관하게 0점 없음으로 고정됩니다. |
| 12 | `failure-modes.md` 실제 슬롯 JSON 입력 | **부분 확인** | [failure-modes.md:368~374](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:368>)가 `item_intro`, `item_questions`, `item_cond`, `answer1~4`, `rubric_rows` 등 실제 키를 사용합니다. 그러나 `std1_text`, `item1_element~item4_element`, 조건부 `std2_*`가 매핑에서 빠졌고, `partial`을 부분 인정 기준, `caution`을 채점 시 유의점으로 잘못 해석합니다. 실제로는 [hwpx-build.md:224~225](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:224>)에서 `partial=채점 시 유의점`, `caution=피드백 제공 시 유의점`입니다. 프롬프트가 HWPX까지 요구하지만 SKILL은 HWPX 생성 전에 이 프롬프트를 실행하도록 배치한 순서 모순도 있습니다. |

## ② 새로 발견한 결함

### A급 — 시행·배포 전 필수 수정

| 결함 | 직접 근거와 영향 | 필요한 수정 |
|---|---|---|
| **A-1. `valid` 예시가 내부 성취기준 정렬 규칙을 위반** | 예시는 [valid-similarity-20pt.json:48](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:48>)에서 `[9수03-12]` 하나를 평가한다고 선언하면서, [51~60행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:51>)과 [311~428행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/valid-similarity-20pt.json:311>)에서 부피비 산출, 단위량당 비교, 공지문 조직 등을 득점 요소로 둡니다. 그런데 [standards.md:126~130](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:126>)은 바로 이 문항에서 닮은 입체의 부피비 등을 성취기준 밖 요소로 규정합니다. 더 직접적으로 [failure-modes.md:206~218](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:206>)은 이 피자 사례를 “실제 득점 기능이 선언된 성취기준에 포함되지 않는” 결함으로 기록합니다. 이름과 점수 구간만 `valid`가 되었고 핵심 정렬 결함은 남았습니다. | `[9수03-12]`를 “중심 성취기준”으로 정직하게 한정하고 선수학습·문제해결 과정의 역할을 분리하거나, 실제 배점 요소를 포괄하는 성취기준·평가 요소 체계를 다시 확정해야 합니다. 수정 전까지 이 JSON을 valid few-shot으로 사용하면 안 됩니다. |
| **A-2. 필수 검증의 실행 순서가 불가능하고 워크플로가 실패 개방형** | [SKILL.md:74~78](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:74>)은 조판 전 4단계에서 `failure-modes.md` 프롬프트를 쓰라고 하지만, 그 프롬프트는 [368행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:368>)과 [458~467행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:458>)에서 아직 생성되지 않은 HWPX와 `check_tpl2.py` 결과까지 필수로 요구합니다. 동시에 [develop-draft.js:91~94](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:91>)와 [verify-rubric.js:79~97](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:79>)은 실패한 에이전트를 `filter(Boolean)`으로 제거하고 최소 결과 수나 최종 `pass`를 확인하지 않습니다. 필수 검사가 실패해도 “지적 0건”처럼 보일 수 있습니다. | 프롬프트를 조판 전 F01~F21과 조판 후 F22로 분리하고, 후자를 6단계 뒤에 둬야 합니다. 초안 3개·검증 2개·재검증 동일 개수를 assert하고, 누락 시 즉시 FAIL해야 합니다. 최종적으로 `pass = 모든 필수 검사 완료 && 실제 blocking 결함 0`을 명시적으로 반환해야 합니다. |
| **A-3. 필수 그림 누락·변환 실패가 최종 PASS 가능** | [figlib.py:59~68](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/figlib.py:59>)은 변환 실패를 예외로 전파하지 않습니다. [build_tpl2.py:279~283](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:279>)은 그림 파일이 없으면 자리표시를 일반 텍스트로 남깁니다. `check_tpl2.py`는 `_figs` 선언, `binaryItemIDRef`, `content.hpf`, ZIP 엔트리, PNG 유효성을 연결해 검사하지 않습니다. 가격표·치수도처럼 그림 자체가 문항 내용인 경우 학생이 문제를 풀 수 없는데도 구조 검사는 PASS할 수 있습니다. | `rsvg-convert` 실패 시 생성된 부분 PNG를 삭제하고 빌드를 실패시켜야 합니다. 성공은 `returncode==0`과 PNG 헤더·치수 파싱 성공을 모두 요구해야 합니다. `_figs` 또는 `[그림 N]`이 있으면 선언 수=삽입 수, 자리표시 잔존 0, manifest/ZIP/PNG 유효성 전부를 `check_tpl2.py`에서 차단 검사해야 합니다. |
| **A-4. 피드백 활동의 수학 규칙이 정면 충돌** | [transfer-and-numbers.md:174~183](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:174>)은 반지름 5칸·10칸의 `80:316=3.95`를 `✔`로 표시하고 “4칸 이상”이면 사용할 수 있다고 합니다. 반면 [examples-pizza.md:347~348](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:347>)은 같은 규약에서 5칸·10칸은 정확히 4배가 아니므로 사용할 수 없고 4·8 또는 6·12만 가능하다고 합니다. ‘길이 2배 → 넓이 4배’를 확인하는 교정 활동에서 3.95배를 통과시키면 문서가 세운 정확성 기준을 스스로 위반합니다. | 5칸 행을 `✗`로 바꾸고 “4칸 이상”을 검산된 허용 쌍 목록으로 교체해야 합니다. 근삿값 체험으로 허용하려면 목적과 허용 오차를 별도 명시해야 합니다. |

### B급 — 실질적인 신뢰성·정합성 결함

| 결함 | 근거와 영향 |
|---|---|
| **B-1. 학교·사용자 정책 조정이 선언만 되고 실행되지 않음** | 조정 허용은 [SKILL.md:13·15·46](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:13>)에 있으나, 0점은 [rubric-rules.md:416~443](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:416>), [verify-rubric.js:47~65](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:47>), [codex-review.md:73](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:73>)에서 고정됩니다. 전이성도 [develop-draft.js:39~44](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:39>)가 T1~T5를 무조건 강제합니다. 학교 규정과 충돌하는 실제 작업에서는 A급으로 승격됩니다. `zero_policy`, `min_score`, `absence_policy`, `transfer_profile`을 0단계 결과로 구조화해 전 워크플로와 검사식에 전달해야 합니다. |
| **B-2. 0점 정책의 인과 설명이 반대로 쓰임** | [rubric-rules.md:67](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:67>)은 “0점 급간을 두면” 저득점 구간이 미응시 전용이 된다고 설명합니다. 실제로는 [standards.md:197~209](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:197>)가 설명하듯 요소 최저점을 1점으로 하여 **0점 급간을 없앴을 때** `0..n-1`이 제출 답안에 도달 불가능해집니다. 0점 없음은 사용자 정책으로 유지할 수 있지만 이 논거는 제거하거나 바로잡아야 합니다. |
| **B-3. 슬롯 전체 조립 지시의 키가 틀림** | [SKILL.md:72](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:72>)의 `questions`·`cond`는 실제 키가 아닙니다. 빌더는 [build_tpl2.py:730~746](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:730>)에서 `item_cond`, `item_questions`만 처리하고, [hwpx-build.md:125](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:125>)도 미등록 키를 조용히 버린다고 경고합니다. 최종 내용 보존 검사에서 잡힐 수는 있지만, 조립 단계의 공식 지시 자체가 잘못되어 있습니다. |
| **B-4. `failure-modes.md`의 스키마 매핑이 불완전하고 슬롯 의미가 뒤바뀜** | [failure-modes.md:369~374](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:369>)에 `std1_text`, `item1_element~item4_element`, 조건부 `std2_*`가 없습니다. `partial`·`caution`의 의미도 반대로 설명하여 피드백 문장을 채점 규칙으로 오인할 수 있습니다. F12~F14의 성취기준 삼각 대조와 F01~F03의 급간 충돌 검사가 왜곡됩니다. |
| **B-5. ‘정확 문자열 허용 목록’ 미구현** | [check_tpl2.py:151~154](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:151>)은 실제 전체 문장 `※ 평가 유형…따라 자율적으로 선정하여 작성`이 아니라 중간에서 잘린 접두사를 저장하고 `startswith()`로 허용합니다. 같은 접두사 뒤에 임의의 오류 문구가 붙거나 여러 번 반복되어도 모두 경고로 강등됩니다. 전체 문자열 equality, 표 밖 위치, 발생 횟수 정확히 1건을 함께 검사해야 합니다. |
| **B-6. 표내 charPr 검사가 실패 개방형** | [check_tpl2.py:199~226](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:199>)은 header의 마지막 두 ID를 통일 스타일로 가정할 뿐 실제 fontRef·11pt·ratio·spacing·bold를 검사하지 않습니다. 검사 자체가 예외를 내면 ERR가 아니라 WARN이어서 최종 PASS가 가능합니다. 핵심 서식 검사의 예외는 FAIL이어야 하며 ID가 아니라 실제 속성을 확인해야 합니다. |
| **B-7. 표 밖 세로 겹침 검사가 완전하지 않음** | [check_tpl2.py:253~275](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:253>)은 다음 시작점이 2,000 미만이면 실제 겹침도 새 페이지로 간주할 수 있고, 표 문단을 만나면 이전 끝점을 초기화하며, 마지막 lineseg의 `spacing`과 paraPr의 `next`를 점유 높이에 포함하지 않습니다. 같은 문단 내부 lineseg 역전도 검사하지 않습니다. 목표였던 현재 템플릿의 2줄 문단 겹침은 잡을 수 있지만 일반적인 “세로 겹침 검사” 계약에는 미달합니다. |
| **B-8. 표 격자 검사가 중첩 셀에서 자식 주소·span을 읽음** | [check_tpl2.py:70~75](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:70>)은 직접 셀 문자열에서 첫 `cellAddr`·`cellSpan`을 `re.search()`로 읽습니다. HWPX 셀은 `subList`의 중첩 표가 부모 자신의 주소보다 먼저 나오므로 자식 값을 읽을 수 있습니다. 실제 템플릿 인메모리 대조에서 T5·T6 부모 셀의 첫 span과 부모 자신의 마지막 span이 달랐습니다. 빌더의 `own()`/`last()` 방식처럼 중첩 표를 제거한 뒤 부모 속성을 읽어야 합니다. |
| **B-9. ZIP 손상 결과가 오류로 집계되지 않음** | [check_tpl2.py:53~54](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:53>)은 `z.testzip()` 결과를 출력만 합니다. 손상 엔트리가 XML이 아닌 BinData면 XML 파싱에도 잡히지 않아 PASS가 가능합니다. 문서의 통과 기준은 `testzip=None`이므로 반환값이 있으면 ERR로 집계해야 합니다. |
| **B-10. 표 밖 커서 재계산이 `paraPr.next`를 버림** | 수정 블록은 [build_tpl2.py:877~887](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:877>)에서 `prev`만 더하고 `next`를 더하지 않습니다. 같은 파일의 `make_paras()`와 `para_height()`는 둘 다 `next`를 포함합니다. 현 템플릿 최상위 문단 53개 중 36개가 `next>0`이며 대상 2줄 문단도 `next=200`입니다. 이번 n_lines 수정은 유효하지만 문단 간격·페이지 적재가 계속 원본보다 압축됩니다. |
| **B-11. `hwpx-build.md`의 0점 근거와 3단 급간 규칙이 권위 문서와 충돌** | [hwpx-build.md:311](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:311>)은 경기 자료를 0점 없음의 근거처럼 쓰지만 실제 추출본 3912·4637·4645행에 0점 급간이 있습니다. [315행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:315>)은 “3단은 이접”으로 단정하지만 바로 아래 320행은 연접 예시이고, 권위 문서인 `rubric-rules.md`는 바로 위 급간이 포괄하는 수행에 따라 접속을 정하라고 합니다. 기계적으로 이접을 적용하면 급간 겹침이 생길 수 있습니다. |
| **B-12. 결함 있는 few-shot을 ‘완성·검증’ 사례로 제시** | [examples-pizza.md:1](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:1>)은 두 사례를 완성·검증된 복제 대상으로 부르지만, [13~15행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:13>)은 사례 A의 구간 결함을 인정하고 [275행](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:275>)은 사례 B의 세 요소에서 2점·1점 급간 중복을 인정합니다. 결함 사례는 anti-pattern 문서로 격리하고 few-shot에는 전 항목 통과 정본만 남겨야 합니다. |
| **B-13. `valid` 예시의 NCIC 출처 추적성이 없음** | [standards.md:381~383](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:381>)은 성취수준 출처 각주 1줄을 필수로 요구하지만 예시의 `std1_A~E`에는 NCIC·성취기준별/영역별 출처가 없습니다. 외부 원문과 일치하지 않는다고 단정한 것은 아니지만, 예시가 자체 최종 점검표를 통과했다는 증거가 없습니다. |
| **B-14. 고교 지원과 검증 프롬프트 학교급 고정이 충돌** | SKILL은 중·고교를 받지만 [codex-review.md:64·76](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:64>)은 “한국 중학교”, “중학교 `<학년>`”으로 고정되고 [failure-modes.md:386](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:386>)은 모든 대상에 실제 중2 답안을 요구합니다. 고교 또는 중1·중3에서는 수준 판정이 왜곡될 수 있습니다. |

### C급 — 국소적인 정확성·문서 정밀도 문제

| 결함 | 근거 |
|---|---|
| **C-1. `ROUND_HALF_UP` 전에 float로 정확도를 잃음** | [transfer-and-numbers.md:396~399](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:396>)의 `Decimal(str(float(x)))`는 정확한 `Fraction`을 먼저 이진 부동소수점으로 바꿉니다. 경계값에서는 사사오입 방향이 달라질 수 있습니다. `Decimal(x.numerator) / Decimal(x.denominator)`로 직접 변환해야 합니다. |
| **C-2. `standards.md`의 R7 상호참조가 낡음** | [standards.md:242~245](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:242>)은 현재도 `hwpx-build.md` R7이 나쁜 구간을 담는다고 하지만, 현 [hwpx-build.md:214~218](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:214>)은 올바른 구간과 과거 결함을 구분합니다. |
| **C-3. 콘텐츠 JSON 미발견 문서가 구동작을 설명** | [hwpx-build.md:115·506](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:115>)은 JSON이 없으면 검사를 건너뛰고 `(content2.json 없음)`이 찍힌다고 설명하지만 실제 [check_tpl2.py:193~195](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:193>)은 `[ERR]`와 FAIL입니다. |
| **C-4. PASS 예시가 실제 출력과 다름** | `hwpx-build.md`는 단독 `PASS`를 보이지만 실제 출력은 `PASS — 오류 0건 / 경고 N건`입니다. 판정 의미에는 영향이 없지만 자동 로그 검색 문구는 맞춰야 합니다. |
| **C-5. 경기 추출본 범위 기준이 비대칭** | `3903~3938`은 표 본체만 포함하고 유의점을 제외하지만, `4615~4680`은 표·유의점·페이지 번호까지 포함합니다. 대상 구간 자체는 맞지만 설명을 “채점기준표 및 유의점 섹션”으로 바꾸거나 동일한 경계 기준을 적용하는 편이 정확합니다. |
| **C-6. 일부 예외 경로에서는 PASS/FAIL footer 없이 traceback** | 잘못된 ZIP, 잘못된 JSON, 필수 엔트리 누락 등은 최종 footer 전에 예외가 전파됩니다. 프로세스는 비정상 종료되어 자동화 차단은 되지만 “항상 PASS/FAIL 출력” 계약은 충족하지 않습니다. 최상위 예외를 `FAIL — …`로 변환해야 합니다. |

## ③ 이번 라운드 미수정 잔여 항목의 우선순위

아래는 수정 목록에 일부 관련 문구가 추가되었더라도, 1차 감사에서 요구한 본질적 개선은 아직 이루어지지 않은 항목입니다.

| 우선순위 | 잔여 항목 | 현재 상태 | 다음 라운드 완료 기준 |
|---:|---|---|---|
| **P0-1** | **채점 요소 원자화** | **이번 라운드 미수정.** `rubric-rules.md`는 오히려 인지적으로 이어지는 수행을 합치라고 하고, 실제 valid 예시는 “개수 산출+오류 반박+촘촘함 설명”, “여러 값 산출+두 단계 판단”을 한 요소에 묶습니다. 검증 프롬프트가 사후에 원자 명제로 분해할 뿐, 작성 스키마 자체는 원자적이지 않습니다. | 각 채점 요소가 하나의 관찰 가능한 술어만 갖도록 구조화합니다. `requirement_id → 발문 요구 → 예시답안 근거 → 정확히 한 채점 요소 → 급간 판정` 매핑을 필수 산출물로 만들고, 중복 귀속·고아 요건·한 요소의 복수 독립 수행을 자동 차단해야 합니다. |
| **P0-2** | **접근성** | **이번 라운드 미수정.** 흑백 인쇄 구분 정도만 있고, [img_embed.py:53](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/img_embed.py:53>)의 shapeComment는 모든 그림에 의미 없는 `그림`으로 고정됩니다. | 의미 동등 대체텍스트, 이미지 속 정보의 텍스트 버전, 색각·명도 대비, 확대 시 가독성, 표·그림 읽기 순서, 이미지 없이도 풀 수 있는 대체 자료를 정의하고 검사해야 합니다. |
| **P0-3** | **실제 렌더링 검수** | **이번 라운드 미수정.** 현재 최종 검사는 ZIP/XML·표 격자·스타일 참조·캐시 좌표 등 구조 검사입니다. `Read로 열기`는 개별 그림에만 적용됩니다. | 실제 HWPX 호환 엔진으로 PDF 또는 페이지 PNG를 생성하고 전 페이지를 검수해야 합니다. 잘림·겹침·셀 넘침·페이지 분할·표 헤더 반복·글꼴 대체·빈 페이지·그림 비율·답안 공간을 차단 게이트로 둬야 합니다. |
| **P0-4** | **예비 시행 게이트** | **이번 라운드 미수정.** 예시 JSON에 “표본 학생 예비 실시로 확인”이라는 한 문장이 있을 뿐, SKILL 절차에는 결과 기록·통과 기준·교사 승인·미실시 차단이 없습니다. | 접근성·렌더링·원자화 수정 후 실제 소요 시간 분포, 학생 인지 인터뷰, 문항별 무응답·오답 경로, 채점자 간 일치도, 수정 전후 버전, 담당 교사 승인을 기록해야 합니다. 미실시 상태에서는 “배포용 확정본”을 만들지 못하게 해야 합니다. |
| **P1** | **전이성 요건 재정의** | **부분 문구 수정만 있고 본질은 미수정.** 사용자 정책·닮음 어댑터 단서는 추가됐지만 `transfer-and-numbers.md:9~17`과 `develop-draft.js`는 오류 2개, 경로 2개, 역방향 1개 등 T1~T5를 고정 강제합니다. | 이를 전이의 필요충분조건이 아니라 선택 가능한 평가 프로파일로 바꿔야 합니다. 개념 도출형·증명형·모델링형·통계 추론형·작도형별 요건을 만들고, 0단계에서 확정한 프로파일만 워크플로와 심사기에 전달해야 합니다. |
| **P2** | **4문항 전용 구조 일반화** | **이번 라운드 미수정.** [SKILL.md:47](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:47>)이 제한을 정직하게 고지했을 뿐, 빌더·워크플로·검토 입력·배점표는 여전히 `item1~item4` 고정입니다. | `item_count`와 문항 배열을 기반으로 문항 정보·답안·채점표·배점·표 행을 동적으로 생성하는 스키마로 바꿔야 합니다. 현재는 제한이 명시되어 있으므로 조용히 잘못된 결과를 내는 P0 항목보다 후순위입니다. |

## 최종 권고

이번 2차 수정은 문구 정직화와 일부 코드 버그 수정에는 분명한 진전이 있습니다. 특히 다중 줄 커서 계산, 명시적 종료 코드, 예시 구간, 추출본 행 범위, 50키 Codex 입력은 실제로 반영되었습니다.

그러나 현재 상태에서 스킬을 “검증 완료”로 분류해서는 안 됩니다. 다음 재감사 전에 최소한 아래 순서로 정리하는 것이 적절합니다.

1. `valid-similarity-20pt.json`의 성취기준 정렬을 바로잡거나 `valid` 지위를 철회.
2. 조판 전/후 검증을 분리하고 워크플로 실패를 fail-closed로 변경.
3. 그림 생성·삽입·manifest·PNG 유효성을 최종 PASS 게이트에 추가.
4. `SKILL.md`의 잘못된 슬롯 키와 `failure-modes.md`의 슬롯 의미를 수정.
5. 학교 0점 정책과 전이성 프로파일을 실제 워크플로·검사 코드로 전달.
6. `check_tpl2.py`의 정확 문자열, charPr, 세로 겹침, 중첩 셀, ZIP 손상 검사를 보강.
7. 그 뒤 원자화·접근성·렌더링·예비 시행을 P0 게이트로 추가.

따라서 최종 판정은 **“수정 실재는 상당 부분 확인되나, A급 4건 때문에 2차 감사 통과 보류”**입니다.
