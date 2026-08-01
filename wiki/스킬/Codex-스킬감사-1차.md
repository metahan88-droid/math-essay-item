최종 판정은 **시행·범용 배포 보류**다. 현재 폴더는 “한국 중등 수학 전 단원용 서·논술형 문항 개발 스킬”이라기보다, **중2 닮음·피자 문항을 여러 차례 수정한 개발 기록과 특정 HWPX 템플릿용 조판 코드**에 가깝다.

요청한 `SKILL.md`, `references/*.md`, `examples/examples-pizza.md`, `workflows/*.js`, `tools/*.py`를 모두 직접 읽었고, 추가로 실행 계약 확인에 필요한 `examples/sample-slots-15pt-to-20pt.json`, `gyeonggi-2025-extract.txt` 지정 구간, `tpl2/`, 동봉 산출물 `out2/`도 대조했다. 파일은 수정하지 않았다.

심각도는 다음과 같이 적용했다.

- A: 정상 절차를 따라도 실행이 막히거나, 틀린 평가·깨진 HWPX가 “통과”할 수 있어 시행 전 필수 수정
- B: 수동 우회는 가능하지만 신뢰도·일반화·공정성·유지보수성을 크게 낮춤
- C: 사소한 정리·명료성·구성 문제

집중 관점 1~5 모두에서 문제가 발견되었으므로, 관점 단위의 “이상 없음”은 없다.

## (A) 오작동·시행 전 필수 수정

### A-1. 빌더가 실제로 두 줄 문단과 다음 문단을 겹치게 만든다

위치: [build_tpl2.py:854](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:854>), [build_tpl2.py:876](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:876>), [build_tpl2.py:884](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:884>), [build_tpl2.py:886](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:886>), [out2/Contents/section0.xml:1](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/out2/Contents/section0.xml:1>)

표 바깥 문단 재배치 루프는 `segs`가 여러 개인지 알면서도 페이지 적합성과 다음 문단의 `cursor`를 `vs + sp` 한 줄분만큼만 전진시킨다. 그러나 실제 줄들은 `top + i × (vs + sp)`에 배치한다.

동봉된 `out2`에서 이를 직접 재현했다.

- 두 줄 문단의 줄 시작: `8420`, `10612`
- 두 번째 줄 높이: `1500`
- 바로 다음 문단 시작: `11012`

따라서 두 번째 줄은 최소 `10612~12112`를 차지하는데 다음 문단이 `11012`에서 시작한다. 실제 겹침이다.

구체 수정안:

- 문단 본문 높이를 `body_span = (len(segs)-1) * (vs+sp) + vs`로 계산한다.
- 페이지 넘김 판정도 `top + body_span`으로 한다.
- 다음 문단의 `cursor`는 `top + body_span + para_next_margin`으로 갱신한다.
- `check_tpl2.py`에 표 바깥 인접 문단의 세로 구간을 계산하여 `previous_end > next_start`를 차단하는 검사를 추가한다.
- 수정 후 동봉 템플릿과 긴 2·3·4줄 문단 회귀 테스트를 만든다.

### A-2. 검증기들이 오류를 세기만 하고 실패 종료하지 않는다

위치: [check_tpl2.py:12](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:12>), [check_tpl2.py:150](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:150>), [check_tpl2.py:161](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:161>), [check_tpl2.py:187](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:187>), [check_tpl2.py:190](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:190>), [build_tpl2.py:948](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:948>), [build_tpl2.py:965](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:965>), [hwpx-build.md:496](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:496>)

`check_tpl2.py`는 `errs`를 증가시키지만 마지막에 `sys.exit(1)`을 호출하지 않는다. XML 파손, 내용 누락, 셀 주소 중복이 있어도 프로세스 종료 코드는 0이다. `build_tpl2.py`의 자체 검사도 `SQUEEZE` 위반 수를 출력할 뿐 실패하지 않는다.

또한 다음 검증 계약이 구현되지 않았다.

- [SKILL.md:97](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:97>)이 요구하는 “표내 비통일 `charPr` 0”은 `check_tpl2.py`가 검사하지 않는다. 검사하는 것은 미정의 `charPr`뿐이다.
- 그림 누락, 체크박스 선택 수, 고아 BinData, 셀 높이 부족, 문단 세로 위치 역전은 최종 검사에 통합되어 있지 않다.
- 콘텐츠 JSON을 못 찾는 경우 [check_tpl2.py:187](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:187>)은 오류로 세지 않고 안내문만 출력한다.
- [hwpx-build.md:508](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:508>)은 “오류 1건”을 통과로 간주한다. 정상 안내문 대신 전혀 다른 위험 문장 한 건이 생겨도 같은 모양이 된다.
- 필수라는 `rubric_check.py`는 실제 `tools/`에 없고 [rubric-rules.md:388](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:388>)의 코드블록을 매번 복사하고 `ITEM`까지 수동 수정해야 한다.
- 수치 검산 뼈대도 [transfer-and-numbers.md:367](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:367>)에서 G13은 주석 상태이고 G14는 없다고 스스로 밝힌다. 마지막에도 실패를 출력할 뿐 비정상 종료하지 않는다.

구체 수정안:

- `tools/validate_slots.py`, `tools/rubric_check.py`, `tools/check_tpl2.py`를 실제 실행 파일로 제공하고 공통 검증 모듈을 공유한다.
- 모든 검사기는 명시적인 `PASS`/`FAIL`과 종료 코드 0/1을 반환한다.
- 예상되는 안내문 위험은 `allowed_warning`으로 정확한 문자열까지 비교하고 오류 수에 넣지 않는다.
- `build_tpl2.py`가 슬롯 의미 검증을 먼저 호출하고 실패 시 조판을 시작하지 않게 한다.
- 최종 검증은 슬롯 의미, 그림, HWPX 구조, 내용, 세로 겹침, 스타일, BinData를 한 번에 차단해야 한다.

### A-3. 7단계 사이에 “완성 슬롯 JSON을 만드는 단계”가 없다

위치: [SKILL.md:37](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:37>), [SKILL.md:48](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:48>), [SKILL.md:60](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:60>), [SKILL.md:69](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:69>), [SKILL.md:95](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:95>), [develop-draft.js:62](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:62>), [hwpx-build.md:119](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:119>), [build_tpl2.py:740](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:740>), [check_tpl2.py:174](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/check_tpl2.py:174>)

초안 워크플로의 산출은 `title`, `scenario`, `materials`, `questions`, `numbers`, `transfer`, `verify_log` 7필드다. 3단계는 `rubric_rows`, 예시 답안, 유의점, 성취수준을 만든다고만 한다.

그러나 HWPX에는 다음과 같은 별도 내용이 필요하다.

- `affiliation`, `name`, `_check_class`
- `task`, `purpose`
- `std1_text`, `std1_A`~`std1_E`, 필요하면 `std2_*`
- `item1_type/form/element`~`item4_*`
- `lesson1_act/eval`~`lesson5_act/eval`
- `item_intro`, `item_questions`, `item_cond`
- `answer_n*`, `answer*`
- `partial`, `caution`
- `level_A_score/desc`~`level_E_score/desc`
- `rubric_rows`, `_figs`

이 필드들을 누가, 언제, 어떤 스키마로 생성하는지가 없다. 4단계 검증은 완성 슬롯 JSON 경로를 요구하지만, SKILL은 슬롯 JSON 작성을 6단계에 둔다. 실행 순서도 순환한다.

더 심각하게 `build_tpl2.py`는 존재하는 키만 치환하고, `check_tpl2.py`도 입력 JSON에 있던 값만 보존 여부를 검사한다. 필수 키가 빠지면 템플릿의 예시 문구가 그대로 남아도 통과할 수 있다.

구체 수정안:

- 2단계 뒤에 “2.5단계 — 정규 콘텐츠 모델 조립”을 추가한다.
- `content.schema.json`을 제공해 필수/선택 키, 자료형, 문항 수, 빈 문자열 허용 여부, 줄 배열 규칙을 강제한다.
- 초안 7필드에서 `item_intro`·`item_questions` 등으로 옮기는 mapper를 제공한다.
- 템플릿의 원본 예시 텍스트가 최종 파일에 남아 있지 않은지 sentinel 목록으로 검사한다.
- 4단계는 이 정규화된 슬롯 JSON만 검증하게 하고, 5단계에서 `_figs`를 추가한 뒤 전체 검증을 다시 실행한다.

### A-4. 워크플로 파일은 실행 런타임과 호출법이 정의되지 않았고 검증 워크플로는 절차에서 발견되지 않는다

위치: [develop-draft.js:2](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:2>), [develop-draft.js:12](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:12>), [develop-draft.js:54](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:54>), [develop-draft.js:116](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:116>), [verify-rubric.js:2](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:2>), [verify-rubric.js:78](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:78>), [verify-rubric.js:97](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:97>)

`phase`, `parallel`, `agent`는 import도 정의도 없다. 전용 “Workflow 도구”가 이를 주입하는 것으로 보이지만, 도구 이름, 버전, 실행 명령, 입력 방법, 결과 파일 위치가 없다. 표준 Node로 두 파일을 실행하면 마지막의 top-level `return`에서 `SyntaxError: Illegal return statement`가 발생한다.

또한:

- SKILL 1단계는 `develop-draft.js`만 언급한다.
- 4단계는 `verify-rubric.js`를 전혀 가리키지 않는다.
- 검증 워크플로는 두 검증 중 하나가 실패해도 남은 결과만 반환한다.
- 재검증 결과의 `verdict.real`을 이용해 승인 여부를 집계하지 않는다.
- `blocking=false`인지, 검증 에이전트가 모두 실제로 응답했는지, 수정 후 재실행했는지를 나타내는 최종 `approved` 게이트가 없다.

구체 수정안:

- 전용 런타임을 유지한다면 정확한 실행 예와 요구 버전을 SKILL에 넣고, 파일을 해당 런타임이 요구하는 export 형식으로 만든다.
- 범용성을 원한다면 명시적인 import와 `export default async function main(input)`을 가진 실행 가능한 JS 또는 Python 오케스트레이터로 바꾼다.
- `verify-rubric.js`를 SKILL 4단계에 직접 연결한다.
- `approved = 두 검증 모두 존재 ∧ 실재 blocking 결함 0 ∧ rubric_check 통과 ∧ Codex 검토 성공`으로 집계하고, 거짓이면 다음 단계로 진행하지 않는다.
- 모든 `@@...@@` 자리표시가 남아 있으면 실행 전 실패하도록 한다.

### A-5. 문항 수를 받는다고 하지만 전체 구현은 사실상 정확히 4문항 전용이다

위치: [SKILL.md:43](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:43>), [develop-draft.js:69](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:69>), [develop-draft.js:82](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:82>), [build_tpl2.py:54](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:54>), [build_tpl2.py:446](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:446>), [hwpx-build.md:454](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:454>)

0단계는 사용자가 문항 수를 고를 수 있다고 한다. 그러나 워크플로는 항상 문항 1~4를 만들고, 슬롯은 `item4`까지만 있으며, 표 수술도 정확히 4문항 전용이다. 5문항 이상은 표현할 수 없고, 3문항은 원본 답안 행과 수술 조건의 지원 경로가 명확하지 않다.

구체 수정안:

- 단기적으로는 0단계에 “현재 HWPX·워크플로는 4문항만 지원”을 명시하고 다른 입력을 거부한다.
- 장기적으로는 `item_count`, `item_scores`, `items[]`, `answers[]` 배열을 도입하고 개요·답안·채점표 행을 임의 개수로 생성하도록 수술 코드를 일반화한다.

### A-6. 필수 Codex 검토 명령과 입력 생성 코드가 자립 실행되지 않고, 검토 자료도 불완전하다

위치: [SKILL.md:75](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:75>), [SKILL.md:77](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:77>), [codex-review.md:9](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:9>), [codex-review.md:20](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:20>), [codex-review.md:24](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:24>), [codex-review.md:25](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/codex-review.md:25>)

직접 실행 문제:

- SKILL 명령의 `$OUT`이 정의되지 않았다. 빈 값이면 출력 경로가 `/codex_review.md`가 된다.
- `codex-review.md`는 `S="$SCRATCH"`라고 하지만 `$SCRATCH`가 정의되지 않았다.
- 검토 자료 준비 Python 조각은 `S`와 `slots`가 정의되어 있다고 가정하며 JSON 로드와 `import json`도 없다.
- 백그라운드 실행 후 어떻게 기다리고 종료 코드를 확인하는지 없다.

내용 누락 문제:

- `order`에는 `level_A_desc`, `level_E_desc`만 있고 B·C·D 설명이 없다.
- `level_A_score`~`level_E_score`가 전부 없다.
- `std1_text`, `std1_A`~`std1_E`, `std2_*`가 없다.
- 차시 계획은 `lesson3_eval` 하나뿐이다.
- `item*_type`, `item*_form`도 없다.

그런데 프롬프트는 “자료 전체”라 부르며 성취수준 구간과 성취기준-차시-채점요소 정렬을 검토하라고 한다. 필요한 입력을 주지 않은 필수 검증이므로 false-pass가 발생한다.

구체 수정안:

- `tools/make_review_input.py slots.json review_input.txt`를 실제 파일로 제공한다.
- 특수 메타를 제외한 모든 일반 슬롯을 안정된 순서로 내보내고 “원본 키 수/출력 키 수/누락 키”를 검증한다.
- `mktemp -d` 또는 명시적 작업 폴더를 만들고 경로를 명령행 인자로 넘긴다.
- Codex 실행 래퍼는 사전 인증 확인, 제한시간, 종료 코드, 빈 출력, stderr를 검사한다.
- 리뷰 입력에는 모든 `std*`, `lesson*`, `item*`, `answer*`, `rubric_rows`, `partial`, `caution`, `level_*`을 포함한다.

### A-7. 샘플 JSON은 그림 세 개를 요구하지만 실제 그림이 없고, 빌더는 이를 정상 완료한다

위치: [sample-slots-15pt-to-20pt.json:135](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/sample-slots-15pt-to-20pt.json:135>), [sample-slots-15pt-to-20pt.json:144](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/sample-slots-15pt-to-20pt.json:144>), [sample-slots-15pt-to-20pt.json:164](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/sample-slots-15pt-to-20pt.json:164>), [build_tpl2.py:30](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:30>), [build_tpl2.py:279](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:279>), [figures.md:132](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/figures.md:132>)

샘플은 `[그림 1]`~`[그림 3]`을 사용하지만 `_figs`가 없다. 기본 매핑이 기대하는 다음 파일도 폴더에 없다.

- `examples/figs/fig1_three_sizes.png`
- `examples/figs/fig5_menu_board.png`
- `examples/figs/fig6_owner_memo.png`

빌더는 그림 누락을 경고만 하고 자리표시 문장을 텍스트로 남긴다. 내용 보존 검사는 바로 그 문장이 남아 있으므로 오히려 통과한다. 가격표·실측도가 정보 자료라면 시행 불가능한 문항이 된다.

구체 수정안:

- 유효 샘플에는 실제 PNG와 `_figs`를 함께 번들한다.
- 최종 빌드에서는 `_figs`에 선언된 파일 누락, 잘못된 PNG, BinData ID 중복, 기대 `binaryItemIDRef` 미삽입을 모두 실패 처리한다.
- 자리표시 허용은 `_allow_missing_figs: true`인 명시적 초안 프로파일에서만 허용한다.

### A-8. 적용 교육과정을 2022 개정으로 고정하여 2026년 중3·고3 문항에 잘못된 기준을 적용한다

위치: [standards.md:5](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:5>), [standards.md:7](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:7>), [SKILL.md:44](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:44>)

문서는 모든 학년에 2022 개정 NCIC 자료만 사용하도록 한다. 그러나 2022 개정 교육과정은 중1·고1에 2025년, 중2·고2에 2026년, 중3·고3에 2027년부터 순차 적용된다. 따라서 현재 2026년의 중3·고3은 여전히 2015 개정 적용 대상이다. [교육부 고시 제2022-33호](https://www.moe.go.kr/boardCnts/viewRenew.do?boardID=141&boardSeq=93458&lev=0&searchType=null)

구체 수정안:

- 0단계 입력에 `평가 실시 연도`, `적용 교육과정`, `학년`, `학기/평가 시점`, `이미 학습한 단원`을 추가한다.
- 실시 연도·학년에 따라 2015/2022 자료를 선택한다.
- 목표 성취기준에 포함된 개념을 정적 금지 목록이 차단하지 못하게 한다.

### A-9. “전이성 5요건”은 전이의 필요조건도 충분조건도 아니며 실제 샘플을 전이로 오판한다

위치: [SKILL.md:15](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:15>), [transfer-and-numbers.md:5](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:5>), [transfer-and-numbers.md:9](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:9>), [sample-slots-15pt-to-20pt.json:74](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/sample-slots-15pt-to-20pt.json:74>), [sample-slots-15pt-to-20pt.json:83](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/sample-slots-15pt-to-20pt.json:83>), [sample-slots-15pt-to-20pt.json:175](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/sample-slots-15pt-to-20pt.json:175>)

개념적으로:

- T1의 소재어 0회는 표면 맥락만 측정하며 심층 구조의 새로움을 증명하지 않는다.
- T2의 “결론 관계식 인쇄 0건”은 학생이 관계를 도출했다는 증거가 아니다. 바로 전 차시에 배운 관계를 회상할 수 있다.
- T3 오개념 진단은 진단 설계 특성이지 전이의 구성요건이 아니다.
- T4 정답 유일성과 복수 경로는 해 공간의 성질이다. 정당화된 복수 결론이 가능한 모델링·통계·증명 과제를 부당하게 탈락시킨다.
- T5 역방향 추론은 유용한 인지 요구지만 모든 성취기준의 전이 조건은 아니다.

실제 샘플도 평가 전 차시에 다음을 거의 그대로 연습시킨다.

- “지름이 1.5배면 양도 1.5배”라는 평가 오개념을 같은 수치로 사전 진단
- “넓이 4배 → 지름 2배” 역방향을 예비 훈련
- 닮음비의 제곱·세제곱 관계를 일반식으로 이미 진술

그런데 ‘피자’라는 소재어가 차시에 없다는 이유로 새 맥락 게이트를 통과한다.

구체 수정안:

- 명칭을 “전이 문항 설계 점검표”로 낮춘다.
- 필수 핵심은 `수업과 평가가 같은 심층 구조를 요구함`, `표현·목표·자료·단서·비계 중 둘 이상 변화`, `평가에서 비계 감소`, `학생 답안에서 구조 연결 이유를 관찰 가능`으로 바꾼다.
- 오개념 반박, 복수 경로, 역방향은 성취기준과 청사진에 따라 선택하는 확장 특성으로 둔다.
- 소재어 세기 대신 `목표/주어진 정보/표현/핵심 관계/추론/비계` 대조표와 학생 예비 시행을 사용한다.

### A-10. 수치 규칙과 워크플로가 닮음·피자 구조를 중등 수학 전체의 규칙으로 강제한다

위치: [transfer-and-numbers.md:106](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:106>), [transfer-and-numbers.md:187](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:187>), [transfer-and-numbers.md:219](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:219>), [transfer-and-numbers.md:270](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:270>), [transfer-and-numbers.md:295](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:295>), [develop-draft.js:39](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:39>), [develop-draft.js:46](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:46>), [develop-draft.js:56](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:56>), [examples-pizza.md:352](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:352>)

다음이 일반 규칙처럼 강제된다.

- `k/k²/k³` 오개념 층위
- 기초값은 모두 정수·유한소수
- 역방향 해는 완전제곱에서 나오는 정수
- 단가 최유리 방안과 정답 방안을 다르게 설계
- 세 규격과 여러 선택지
- 오개념 발언 두 개
- 구매·설계·검수 세 소재 각도

이 구조는 순환소수, 무리수, 제곱근, 방정식, 함수, 확률·통계, 기하 증명, 작도, 자료 해석처럼 핵심 대상 자체가 정수·유한소수나 유일 수치 결론이 아닌 단원을 정상적으로 처리하지 못한다. 중3의 목표 개념인 무리수·이차방정식도 정적 금지 토큰으로 걸린다.

구체 수정안:

- 일반 코어와 영역별 어댑터를 분리한다.
- 일반 코어에는 성취기준 정렬, 인지 요구, 수학적 정확성, 발문-채점 대조, 공정성, 채점 신뢰도만 둔다.
- `k²/k³`, 두께 고정, 단위가격, 판 수는 `similarity-volume` 어댑터로 옮긴다.
- 수와 연산, 문자와 식, 함수, 도형과 측정, 자료와 가능성용 어댑터와 각각의 유효 예시를 추가한다.
- 수 체계 게이트는 “해당 교육과정·성취기준·평가 목적에 적합한 표현인가”로 동적으로 생성한다.

### A-11. 0점 금지와 백지 요소별 1점은 근거 없는 보편 정책이며 내부 논리도 모순된다

위치: [SKILL.md:13](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:13>), [rubric-rules.md:65](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:65>), [rubric-rules.md:110](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:110>), [rubric-rules.md:215](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:215>), [standards.md:191](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:191>), [standards.md:248](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:248>), [gyeonggi-2025-extract.txt:3912](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/gyeonggi-2025-extract.txt:3912>), [gyeonggi-2025-extract.txt:4637](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/gyeonggi-2025-extract.txt:4637>)

문제는 다음과 같다.

- 백지·완전 오답에도 요소마다 1점을 주면 관찰된 성취 증거가 없는 학생에게 학업 점수를 준다.
- 같은 20점 평가라도 요소가 4개면 최저 4점, 8개면 최저 8점이다. 최저점이 내용 성취가 아니라 요소 분할 수에 의해 바뀐다.
- `rubric-rules.md`는 백지가 모든 요소의 1점 급간에 들어간다고 하는데, `standards.md`는 `0~floor-1`을 “미응시·백지” 구간이라고 한다. 6요소 전체 백지는 현 규칙상 6점이지 0~5점이 아니다.
- “0점 급간을 두면 저득점 구간이 도달 불가가 된다”는 설명도 반대다. 0점 급간을 두지 않기 때문에 `floor=n`이 생긴다.
- 경기 원문은 0점 급간이 있는 표와 없는 표가 섞여 있다. 스킬의 0점 금지는 외부 자료의 보편 규칙이 아니다.

구체 수정안:

- 0단계에서 학교 학업성적관리규정의 `0점 허용`, `참여 기본점수`, `백지`, `미응시`, `미제출` 처리 정책을 받는다.
- 내용 척도는 원칙적으로 `0 = 해당 수행 증거 없음`을 허용한다.
- 참여 기본점수가 필요하면 각 요소의 성취 점수와 섞지 말고 평가 전체 후처리로 분리한다.
- 미응시는 A~E 밖의 `NE/미평가`로 분리한다.
- 요소 최저 1점 체제는 선택 가능한 로컬 프로파일로만 둔다.

### A-12. 1점 요소 금지와 연속 급간 강제가 분석적 채점의 관찰 가능성을 깨뜨린다

위치: [rubric-rules.md:73](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:73>), [rubric-rules.md:78](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:78>), [rubric-rules.md:88](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:88>), [rubric-rules.md:135](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:135>), [rubric-rules.md:224](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:224>), [failure-modes.md:84](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:84>), [examples-pizza.md:94](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:94>)

`0/1` 이분 기준은 명확한 원자 수행을 판정하는 정상적인 분석적 채점 방식이다. “한 단뿐이라 척도가 아니다”라는 이유로 이를 금지하고 계산과 설명을 합치면 서로 독립적인 수행이 한 급간에 억지로 들어간다.

실제 사례 A 문항 1에 다음 답안을 넣으면 어느 급간에도 걸리지 않는다.

> 세 비는 계산하지 못했지만, 길이가 \(k\)배이면 넓이는 \(k^2\)배이고 부피는 \(k^3\)배이다.

- 4·3점은 비 계산을 요구한다.
- 2점은 “비 일부 수행 또는 관계 미설명”이므로 해당하지 않는다.
- 1점은 “비도 못 구하고 관계도 설명하지 못함”이라는 연접형이므로 해당하지 않는다.

또한 2점 요소의 1점 급간은 “A/B 중 하나만 수행”과 “백지”를 같은 점수로 묶어 부분점수 기능을 잃는다. “최고점부터 처음 참인 급간”은 채점 우선순위일 뿐 논리적 배타성을 만들지 않는다.

구체 수정안:

- 채점 수행을 원자화한다. 예: `산출 정확성 0~2`, `관계 설명 0~2`.
- 총점이 2점이어야 하면 결과와 근거를 각각 0/1로 합산한다.
- 급간 수와 요소 최대점이 같아야 한다는 조판 항등식을 폐기한다.
- 인쇄용 짧은 진술과 교사용 상세 의사결정표를 분리한다.
- 모든 수행 조합에 대해 정확히 한 점수가 나오게 한 뒤 문장으로 압축한다.

### A-13. 성취수준 A~E 구간 알고리즘은 도달 가능성만 맞출 뿐 준거 타당성이 없다

위치: [standards.md:183](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:183>), [standards.md:207](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:207>), [standards.md:211](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:211>), [standards.md:212](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:212>), [rubric-rules.md:94](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:94>)

“C가 가장 넓다”, “A 2~3점 폭, B 2점, D 2점, E 1~2점”, `R ≥ 10`은 조합론적 편의일 뿐 성취수준 경계의 교육적 근거가 아니다. 18점이 왜 A이고 17점이 왜 B인지는 경계 답안이나 성취기준 내용으로 정해지지 않는다.

동일한 18점도 핵심 개념을 틀리고 형식·계산 점수를 얻은 학생과 핵심 개념은 정확하지만 사칙연산을 한 번 틀린 학생이 같게 분류될 수 있다. 그런데 A 진술은 모든 핵심 수행을 할 수 있다고 단정한다.

내부 충돌도 있다. [rubric-rules.md:100](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:100>)의 10점·12점 권장 배분은 `floor=4`일 때 각각 `R=7`, `R=9`여서 `standards.md`의 필수 `R≥10`을 만족하지 못한다.

구체 수정안:

- A~E 경계는 교사 패널이 경계 답안·앵커 답안을 검토하여 내용 기반으로 설정한다.
- 핵심 개념 요소에 최소 충족 조건을 두는 비보상 규칙을 검토한다.
- 미응시는 수준 구간 밖으로 분리한다.
- 이 점수 구간은 “과제 수행수준”으로 부르고 학기 성취수준과 구별한다.
- 자동 검사는 겹침·공백·도달 가능성만 검사하고 컷 점수 자체를 자동 결정하지 않는다.

### A-14. positive few-shot이 스스로 인정한 치명 결함을 포함한다

위치: [examples-pizza.md:1](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:1>), [examples-pizza.md:13](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:13>), [examples-pizza.md:195](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:195>), [examples-pizza.md:275](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:275>), [sample-slots-15pt-to-20pt.json:249](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/sample-slots-15pt-to-20pt.json:249>), [transfer-and-numbers.md:309](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:309>), [develop-draft.js:34](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:34>)

파일 첫 줄은 두 사례를 “완성·검증”이라고 부르고 그대로 복제하라고 한다. 그러나:

- 사례 A의 `E 0~3`은 도달 불가 결함이다.
- 샘플 JSON에 잘못된 A~E 구간이 실제 값으로 남아 있다.
- 사례 B의 4단 세 요소는 1점 이접형 때문에 2점과 1점에 동시에 걸린다고 파일 자체가 인정한다.
- 사례 B 가격 `9,000:16,000:25,000`은 넓이비 오개념 경로에서 세 방안의 단가를 모두 `500/49`로 만들어 후속 판단이 동률이 된다.
- 사례 A의 일부 급간도 위 A-12와 같은 공백을 갖는다.

후반부의 “복제 금지” 경고보다 positive few-shot과 실제 JSON이 생성 모델에 더 강한 신호를 준다.

구체 수정안:

- positive example에는 전 검증을 통과한 정본만 둔다.
- 결함 원문은 `anti-examples/INVALID_*.md`로 물리적으로 분리한다.
- 예시마다 `status`, `validated_against`, `known_issues` 메타데이터를 둔다.
- 사례 A 구간, 사례 B 최저 급간, 사례 B 오개념 동률 처리 또는 가격을 실제로 고친 뒤에만 “완성 사례”라고 부른다.
- CI에서 `status=valid` 예시의 알려진 오류가 0인지 검사한다.

## (B) 품질 저하·중요 개선 권고

### B-1. 같은 규칙의 권위 문서가 갈리거나 문서와 코드가 다르게 동작한다

주요 충돌은 다음과 같다.

- **급간 길이** — [SKILL.md:12](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:12>)와 [hwpx-build.md:322](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:322>)는 25~45자로 “쓴다”고 하지만, [rubric-rules.md:452](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:452>)의 검사는 46~50자를 경고로 통과시키며 사례 B의 최대 46자도 완성 사례다.  
  수정: “25~45자 권장, 46~50자 수동 검토, 51자 이상 차단” 또는 “25~45 절대” 중 하나로 통일한다.

- **3점 요소 최저 급간 접속** — [rubric-rules.md:163](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:163>)은 바로 위 급간의 범위로 연접/이접을 결정하라고 하지만, [hwpx-build.md:313](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:313>)와 [examples-pizza.md:269](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/examples-pizza.md:269>)은 3단=이접으로 고정한다.  
  수정: 단수별 접속표를 삭제하고 권위 규칙 하나만 참조한다.

- **그림 상대경로** — [hwpx-build.md:19](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:19>)은 CWD 기준이라고 하지만 [figures.md:132](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/figures.md:132>)와 실제 [build_tpl2.py:710](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:710>)은 슬롯 JSON 디렉터리 기준이다.  
  수정: “콘텐츠 JSON의 디렉터리 기준”으로 통일한다.

- **유한소수** — [develop-draft.js:46](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:46>)은 모든 값이 정수·유한소수여야 한다고 하지만 [transfer-and-numbers.md:219](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:219>)은 단위량당 값 하나를 순환소수 예외로 둔다.  
  수정: 예외를 워크플로 프롬프트에도 인라인한다.

- **교사용 문체** — 급간과 `partial`은 `~함/~있음`, `level_*_desc`는 `~할 수 있습니다/~기 바랍니다`인데 [verify-rubric.js:70](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:70>)은 “교사용 `~함/한다`”로 뭉뚱그린다.  
  수정: 슬롯별 문체표를 만들고 검사도 슬롯별로 한다.

- **경기 자료의 0점 급간** — [hwpx-build.md:311](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:311>)은 경기 자료가 0점 없는 척도인 것처럼 쓰지만 [rubric-rules.md:67](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:67>)과 실제 추출본은 혼재한다고 밝힌다.  
  수정: “0점 없음은 이 스킬의 선택 정책이며 경기 원문 근거가 아님”으로 정정한다.

- **부분 인정 기준의 산출물 위치** — [failure-modes.md:368](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:368>)은 “부분 인정 기준”과 “채점 시 유의점”을 별개로 검증하지만 [hwpx-build.md:220](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:220>)의 슬롯은 `partial=채점 시 유의점`, `caution=피드백 유의점`뿐이다.  
  수정: `partial`을 부분 인정·동등 경로를 포함한 유일한 채점 유의점으로 정의하거나 별도 슬롯을 실제로 추가한다.

### B-2. 성취기준 정렬을 문자열 출현으로 판정한다

위치: [standards.md:145](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:145>), [standards.md:151](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:151>), [failure-modes.md:218](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:218>), [failure-modes.md:230](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:230>)

차시에 `닮음`, `닮음비` 두 낱말이 있으면 가르친 것으로 보는 것은 단순 언급과 실제 학습을 구별하지 못한다. 반대로 동의어·수학적으로 동치인 표현은 문자열 불일치로 실패한다.

구체 수정안:

- 각 요소를 `내용 개념 / 인지 과정 / 증거 산출물 / 복잡성 / 비계`로 매핑한다.
- 문자열 검사는 누락 후보를 찾는 경고로만 사용한다.
- 최종 정렬은 “그 개념으로 무엇을 설명·정당화·적용하는가”를 의미 단위로 판정한다.

### B-3. 고교 성취기준 코드가 문서에는 유효 예로 나오지만 검사 정규식은 거부한다

위치: [standards.md:61](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:61>), [rubric-rules.md:505](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:505>), [rubric-rules.md:510](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:510>), [hwpx-build.md:140](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:140>)

정규식 `\[\d+[가-힣]\d{2}-\d{2}\]`은 문서가 유효 예로 쓰는 `[10공수1-01-03]`을 거부한다. HWPX는 `중`과 `고`를 모두 허용한다.

구체 수정안:

- 코드 형식을 임의 정규식으로 재구성하지 말고 0단계에서 확인한 NCIC 코드 집합과 정확히 대조한다.
- 최소 회귀 테스트에 `[9수03-12]`, `[10공수1-01-03]`을 모두 넣는다.
- 스킬이 중학교만 지원한다면 description·HWPX 입력·고교 예시를 모두 중학교로 좁힌다.

### B-4. 수치 검산 코드가 작은 정답과 부분 동률을 조용히 통과시킨다

위치: [transfer-and-numbers.md:418](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:418>), [transfer-and-numbers.md:424](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:424>), [transfer-and-numbers.md:491](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:491>), [transfer-and-numbers.md:498](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:498>), [transfer-and-numbers.md:458](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:458>)

- G13의 `range(0, 21)` 화이트리스트는 배점뿐 아니라 16개·20개 같은 실제 답안값도 검산된 것으로 위장한다.
- G9는 세 선택지가 전부 같은 경우만 실패한다. 둘만 동률이어도 최적 선택의 유일성이 깨질 수 있다.
- `round(float(x), 1)`은 Python의 ties-to-even 방식이므로 학교 수학의 통상적인 사사오입과 `.05` 경계에서 달라질 수 있다.
- 반올림 후 순위가 원값 순위와 같은지도 검사하지 않는다.

구체 수정안:

- 수치값 범위 화이트리스트를 제거하고, 배점·문항 번호는 필드 위치로 제외한다.
- 정답 후보 집합의 크기가 1인지 검사하고, 공동정답이면 발문·채점안에 명시한다.
- `Decimal.quantize(..., ROUND_HALF_UP)`을 사용한다.
- 원값과 학생에게 요구한 반올림값에서 결론이 모두 같은지 검사한다.
- 모든 수치에 `source → expression → exact value → displayed value` provenance를 저장한다.

### B-5. 목표 성취기준보다 단위가격 계산·장문 읽기·공지문 형식이 점수 변량을 크게 만든다

위치: [sample-slots-15pt-to-20pt.json:175](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/sample-slots-15pt-to-20pt.json:175>), [sample-slots-15pt-to-20pt.json:189](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/sample-slots-15pt-to-20pt.json:189>), [sample-slots-15pt-to-20pt.json:359](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/sample-slots-15pt-to-20pt.json:359>), [standards.md:122](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:122>)

선언한 `[9수03-12]`보다 다음이 상당한 득점·실점을 만든다.

- 단위가격과 경제적 의사결정
- 긴 상황·조건문 읽기
- 지정 공식 사용
- 지정 용어의 문자 그대로의 출현
- 공지문 세 문단과 문단별 배치

“조건에 명시했다”는 사실만으로 그 요구가 성취기준에 정렬되는 것은 아니다. 특히 “반드시 지정 공식으로 계산”은 동치 풀이를 막아 다중 경로 원칙과도 충돌한다.

구체 수정안:

- 모든 점수를 `목표 성취기준 / 선수 기능 / 의사소통 역량 / 형식 준수`로 분류하는 청사진을 만든다.
- 목표 외 기능의 배점 상한을 정한다.
- 단위율이 목표가 아니면 계산값을 제공하고 학생은 닮음 관계의 선택·정당화에 집중하게 한다.
- 문단 구조는 작성 도움으로 제공하되 별도 의사소통 기준이 없으면 수학 점수에서 제외한다.
- 공식·용어는 수학적으로 동치인 표현을 인정한다.

### B-6. 평가 청사진과 다중 성취기준 처리 규칙이 없다

위치: [SKILL.md:41](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:41>), [SKILL.md:42](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:42>), [SKILL.md:64](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:64>), [standards.md:73](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:73>)

0단계는 평가 요소 하나를 받지만 완성본은 문항별 평가 요소 네 개를 요구한다. 이들을 어떻게 분해하고 중요도·인지 요구·시간에 따라 배점하는지 없다. 여러 성취기준이 있으면 하나만 고르도록 하므로 정상적인 통합 문항도 배제한다.

구체 수정안:

- `primary_standard`, `secondary_standards`, `set_goal`, `items[]`로 구분한다.
- 청사진에 `문항 | 성취기준 | 내용 요소 | 인지 과정 | 증거 | 예상 시간 | 배점 | 선수 기능`을 둔다.
- 각 채점 요소는 정확히 하나의 성취기준에 귀속시키되 통합 과제 자체는 여러 기준을 지원한다.
- 코드를 무조건 삭제하기 전에 수업·문항을 보완할지, 범위를 줄일지 판단하게 한다.

### B-7. 실제 학생 예비 시행과 인간 채점 신뢰도 절차가 필수 게이트가 아니다

위치: [SKILL.md:69](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:69>), [failure-modes.md:360](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:360>), [sample-slots-15pt-to-20pt.json:89](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/sample-slots-15pt-to-20pt.json:89>), [develop-draft.js:96](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:96>)

LLM 심사자가 시간 적정성을 판단할 뿐이다. 샘플에는 “시행 전 표본 학생 예비 실시로 확인”이라는 미래 계획만 있으며 실제 표본 수·완료율·시간 분포·수정 기준이 없다. 채점자 훈련, 앵커 답안, 독립 이중채점, 불일치 해결 절차도 없다.

구체 수정안:

- 파일럿 전 산출물은 “시행 전 검증 필요”로 표시한다.
- 다양한 성취수준과 읽기 지원 필요 학생을 포함한 소규모 파일럿을 필수 게이트로 둔다.
- 완료시간 중앙값과 하위 25%, 무응답 위치, 읽기 시간, 계산기 영향을 기록한다.
- 만점·경계·비정형 정답·대표 오답 앵커를 마련한다.
- 두 채점자가 표본을 독립 채점하고 일치율·인접 일치율 또는 가중 카파를 확인하며, 제3채점·협의 절차를 둔다.

### B-8. 공정성·접근성 지침이 사실상 없다

위치: [figures.md:72](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/figures.md:72>), [SKILL.md:37](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:37>)

흑백 인쇄는 고려하지만 다음은 없다.

- 정보성 그림의 대체 텍스트와 기계 판독 가능한 중복 자료
- 큰글자·고대비·화면낭독 순서
- 색만으로 구분하지 않기
- 읽기 부담·한국어 학습자·저시력·난독 지원
- 소재의 문화·경제적 편향과 불필요한 배경지식 검토
- 필요한 평가 조정과 계산기 사용 정책

구체 수정안:

- 0단계에 접근성·평가 조정 조건을 받는다.
- 정보성 그림의 모든 수치와 문장을 본문 또는 실제 표로도 제공한다.
- 큰글자·회색조·화면낭독·색각 검사를 최종 체크리스트에 추가한다.
- 성취기준과 무관한 언어·문화·경제 지식이 정답을 좌우하는지 민감도 검토를 한다.

### B-9. 최종 HWPX를 실제 페이지로 렌더링해 보는 절차가 없다

위치: [SKILL.md:95](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/SKILL.md:95>), [failure-modes.md:326](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:326>), [hwpx-build.md:496](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:496>)

XML 검사는 글자 겹침·잘린 표·페이지 분할·글꼴 대체·그림 해상도를 완전히 보지 못한다. 실제 A-1의 겹침도 현재 검사에서 빠졌다.

구체 수정안:

- 최종 HWPX를 한글 또는 신뢰할 수 있는 변환기로 PDF/페이지 이미지로 렌더링한다.
- 모든 페이지를 시각적으로 확인하고 페이지 수, 잘림, 빈 페이지, 표 행 분할, 캡션, 그림, 글꼴을 점검한다.
- 렌더링할 수 없는 환경에서는 최종 산출물을 “구조 검증만 완료, 시각 검수 필요”로 명시한다.

### B-10. `figlib.py`는 긴 한글을 줄바꿈하지 않고 변환 실패 시 오래된 PNG를 성공으로 오인할 수 있다

위치: [figlib.py:47](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/figlib.py:47>), [figlib.py:55](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/figlib.py:55>), [figlib.py:57](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/figlib.py:57>), [figlib.py:68](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/figlib.py:68>), [figlib.py:100](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/figlib.py:100>), [figlib.py:132](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/figlib.py:132>)

메뉴·대화방·쪽지는 고정 폭에 텍스트를 한 줄로 넣으며 줄바꿈과 경계 검사가 없다. `rsvg-convert`는 `check=False`이고, 이전 PNG가 이미 존재하면 새 변환이 실패해도 그 오래된 파일을 성공으로 반환한다.

구체 수정안:

- 생성 전에 같은 이름의 PNG를 지운다.
- `subprocess.run(..., check=True)`와 stderr 검사를 사용한다.
- 변환 후 PNG 서명·크기·수정시각을 확인한다.
- 폰트 존재 여부와 한글 글리프를 점검한다.
- 텍스트 폭 측정·자동 줄바꿈·최소 글자 크기·캔버스 경계 검사를 구현한다.

### B-11. 줄바꿈 폭 모형의 대상 글꼴과 실제 출력 글꼴이 다르다

위치: [metrics.py:3](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/metrics.py:3>), [metrics.py:230](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/metrics.py:230>), [build_tpl2.py:194](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/build_tpl2.py:194>), [hwpx-build.md:12](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:12>)

`metrics.py`는 맑은 고딕을 역산했다고 쓰지만 빌더는 함초롬바탕 11pt로 출력한다. 동봉 회귀 테스트는 보수 프로파일에서 10건 중 8건만 정확하며 나머지는 조기 줄바꿈이다. 늦게 나누지 않는 안전성은 있으나 불필요한 줄 증가·표 높이·페이지 증가를 만들 수 있다. `check_tpl2.py`는 또 다른 간이 폭 모형을 사용한다.

구체 수정안:

- 실제 함초롬바탕 11pt HWPX 표본으로 폭 모형을 다시 교정한다.
- 빌더와 검증기가 동일한 `metrics` 모듈을 사용하게 한다.
- 한국어, 숫자, 수학기호, 괄호, 영문 혼합의 실제 템플릿 회귀 코퍼스를 번들한다.
- 조기/정확/지연 줄바꿈률을 테스트 결과로 기록한다.

### B-12. 2ⁿ 이진 벡터 검사는 실제 부분 수행 상태를 전수하지 못한다

위치: [failure-modes.md:39](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:39>), [failure-modes.md:49](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:49>), [failure-modes.md:377](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:377>)

실제 답안은 충족/미충족만이 아니다.

- 개념은 정확하지만 산술 오류
- 근거 일부 누락
- 동치 표현
- 잘못된 전제에서 일관된 후속 절차
- 정답만 제시
- 표현은 불완전하지만 수학은 타당
- 핵심 오류와 사소한 오류의 혼합

이들을 이진화하면 “일부 오류” 경계를 검증하지 못하면서도 전수 검사라는 과신을 준다.

구체 수정안:

- 원자 기준을 최소 `정확 / 부분 / 개념 오류 / 무응답`으로 모델링한다.
- 전체 조합이 너무 크면 pairwise 조합과 위험 기반 시나리오를 사용한다.
- 실제 학생 답안에서 새 상태를 발견할 때마다 회귀 테스트에 추가한다.

### B-13. 채점 시 유의점을 2~4문장으로 제한하면서 모호한 포괄 문구를 허용한다

위치: [rubric-rules.md:348](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:348>), [rubric-rules.md:366](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:366>), [sample-slots-15pt-to-20pt.json:236](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/sample-slots-15pt-to-20pt.json:236>)

“사소한 수치 오차”, “반올림 자리의 차이”, “수학적으로 논리적”, “적절한 설명과 수학적 용어”는 채점자마다 다르게 적용할 수 있다. 여섯 요소, 다중 경로, 연쇄 오류, 핵심 개념 오류를 2~4문장에 모두 넣기는 어렵다.

구체 수정안:

- 인쇄용 공통 유의점과 별도 교사용 상세 채점안을 분리한다.
- 허용 오차, 반올림 구간, 산술 오류의 영향 범위, 개념 오류와 계산 오류의 우선순위를 수치·예시로 명시한다.
- 경계 답안과 대체 경로를 상세안에 둔다.
- “적절한 용어”처럼 조작적 정의가 없는 문구를 삭제한다.

### B-14. 외부 의존성과 절대경로가 선언되지 않아 다른 설치 위치에서 깨진다

위치: [hwpx-build.md:5](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:5>), [hwpx-build.md:35](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:35>), [develop-draft.js:12](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/develop-draft.js:12>), [verify-rubric.js:12](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/workflows/verify-rubric.js:12>), [figures.md:77](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/figures.md:77>), [figures.md:81](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/figures.md:81>)

스킬 루트, 외부 `gpt-image-2`, Codex CLI, `rsvg-convert`, 특정 폰트가 모두 환경에 암묵적으로 의존한다. 현재 기계에는 외부 브리지가 존재하지만 스킬 자체에는 dependency manifest나 대체 경로가 없다.

구체 수정안:

- 스크립트 경로에서 스킬 루트를 동적으로 계산한다.
- `tools/preflight.py`로 Python 버전, Codex CLI 인증, `rsvg-convert`, 폰트, 템플릿 파일, 외부 이미지 스킬을 검사한다.
- 선택 의존성이 없으면 어떤 기능을 건너뛰고 무엇을 수동 처리해야 하는지 명시한다.
- 외부 스킬 경로를 `$HOME/.claude/...`로 직접 조립하지 말고 설정값 또는 도구 인터페이스로 받는다.

## (C) 사소한 문제

### C-1. 재사용 샘플에 실제처럼 보이는 소속·이름이 들어 있다

위치: [sample-slots-15pt-to-20pt.json:2](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/sample-slots-15pt-to-20pt.json:2>)

`○○중학교`, `홍길동`이 샘플 기본값으로 들어 있다. 실제 정보인지 여부와 무관하게 재사용 시 그대로 출력될 위험이 있다.

구체 수정안: `○○중학교`, `홍길동` 또는 빈 필수 자리표시로 익명화하고, 미교체 시 스키마 검증이 실패하게 한다.

### C-2. 생성 산출물 `tools/out2/`가 스킬에 포함되어 템플릿과 중복되고 이미 깨진 결과를 기준처럼 보이게 한다

위치: [tools/out2](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/tools/out2>), [hwpx-build.md:19](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:19>)

`tpl2/`와 대형 BMP·XML이 중복되고, A-1의 겹침이 있는 산출물이 동봉되어 있다. `tools/` 전체 복사 시 불필요하게 함께 복사된 뒤 다시 삭제된다.

구체 수정안: `out2/`를 제거하고 유효한 작은 golden fixture가 필요하면 `tests/fixtures/`에 명확한 이름과 검증 기대값으로 둔다.

### C-3. 샘플 파일명과 실제 내용이 어긋난다

위치: [sample-slots-15pt-to-20pt.json](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/examples/sample-slots-15pt-to-20pt.json>)

파일명은 `15pt-to-20pt`인데 현재 내용은 20점판이며, 알려진 결함까지 남아 있다.

구체 수정안: 검증 후 `valid-similarity-20pt.json`으로 바꾸고 변환 이력은 산출물 이름에서 제거한다.

### C-4. 긴 참조 문서에 목차가 없고 같은 규칙이 여러 파일에 반복된다

위치: [failure-modes.md:1](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/failure-modes.md:1>), [rubric-rules.md:1](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/rubric-rules.md:1>), [standards.md:1](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:1>), [transfer-and-numbers.md:1](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/transfer-and-numbers.md:1>), [hwpx-build.md:1](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/hwpx-build.md:1>)

500줄 안팎의 문서에 목차가 없고, 0점·문장 길이·급간 접속·배점 규칙이 여러 곳에 복사되어 이미 충돌했다.

구체 수정안:

- 각 규칙에 고유 ID와 권위 파일 하나를 둔다.
- 다른 문서는 규칙 본문을 복사하지 말고 ID와 링크만 사용한다.
- 100줄 이상 참조 문서에는 목차를 추가한다.
- 과거 실패 문안은 현행 규칙과 분리한다.

### C-5. 공식 원문의 알려진 오식까지 아무 표식 없이 복사하라는 규칙은 최종 문서의 오식처럼 보일 수 있다

위치: [standards.md:57](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:57>), [standards.md:69](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/standards.md:69>)

구체 수정안: 공식 인용 칸은 그대로 유지하되 `※ 원문 표기` 또는 `[원문 오식]` 각주를 붙이고, 설명문에서는 교정 여부와 근거를 기록한다.

### C-6. 정확 비율 그림이 의도하지 않은 측정 지름길을 줄 수 있다

위치: [figures.md:72](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/figures.md:72>), [figures.md:75](</Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item/references/figures.md:75>)

“눈대중으로도 확인”할 수 있는 정확 비율 그림은 계산·추론을 평가하는 문항에서 답을 측정으로 추정하게 할 수 있다.

구체 수정안: 시각 추정이 의도한 다중표현 경로라면 인정 기준에 넣고, 의도하지 않았다면 관계는 전달하되 정답 수치를 정밀하게 측정할 수 없는 도해로 만든다.

## 부분 검증에서 이상 없음

집중 관점 전체가 문제없는 것은 아니지만, 다음 개별 사항은 독립 재계산·검토에서 이상이 없었다.

- 사례 A의 핵심 산술은 맞다: 넓이 `452.16/706.5/1017.36`, 부피 `904.32/1766.25/3052.08`, 8명 필요량 `1808.64`, 자이언트 `13.5인분`, 16명 최소 `2판`, 패밀리 지름 `48 cm`.
- 사례 B의 원수치도 맞다: 넓이 `441/784/1225`, 부피 `661.5/1568/3062.5`, 필요량 `3136/6272`, 빅 최소 `3판`, 치즈 `750 g`, 파티팩 넓이 `3969 cm²`, 한 변 `63 cm`.
- 반지름 4·8칸에서 칸 중심 규약으로 `52:208`, 반지름 6·12칸에서 `112:448`이 나오는 계산은 맞다.
- 반지름 \(2r\)인 원 안에 반지름 \(r\)인 원을 겹치지 않게 최대 2개 넣을 수 있다는 지적은 타당하다.
- “치즈가 이미 윗면 넓이를 알려 주는 사례 B에서는 두께가 한 변 산출과 무관하다”는 인과 수정은 정확하다.
- `aπ = 소수`라고 쓰지 않고 “원주율을 3.14로 보아 계산하면”으로 구분한 표기 규칙은 타당하다.
- Python 6개 파일은 구문 파싱에 성공했다. `metrics.py`의 보수 프로파일은 동봉 10개 회귀 사례에서 늦게 줄을 나눈 사례가 0건이었다. 다만 실제 출력 글꼴과의 불일치는 B-11로 남는다.
- 발문↔채점요건 양방향 대조, 동치 표현 인정, 연쇄 오류를 중복 감점하지 않으려는 의도, 필체·맞춤법·태도를 수학 점수로 독립 배점하지 않는 방향은 적절하다.

우선 수정 순서는 **A-1 조판 겹침 → A-2 검증기 종료 코드·통합 검증 → A-3 슬롯 스키마·조립 단계 → A-4~A-7 실행 파이프라인 → A-8 교육과정 선택 → A-9~A-14 평가론·few-shot 재설계**가 가장 안전하다.
