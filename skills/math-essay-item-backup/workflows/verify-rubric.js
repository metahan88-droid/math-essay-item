// 4단계 — 검증 두 겹(급간 게이트 + 어긋남 리뷰어). Codex 적대적 검증은 Bash로 따로 실행한다.
// Workflow 도구로 실행한다. @@ 자리를 실제 값으로 바꿔 쓴다.
//
// 반환값 — pass / confirmedBlocking / precision / rerunAdvised / checks.
//  · pass: 재검증에서 확정된 차단성 결함이 0건일 때만 true. 반증률은 pass를 바꾸지 않는다.
//  · precision: 겹마다 raisedBlocking·confirmed·rebutted·handledAt·missedExistingClause.
//  · rerunAdvised: "이미 처리하는 조항이 있는데 못 찾아서 올린" 겹의 이름. 비어 있지 않으면
//    5단계(수선)는 그 겹을 반증 기록과 함께 한 번 더 돌린다 — 그 겹의 나머지 지적도 같은
//    이유로 부풀었을 가능성이 높기 때문이다. pass=true여도 rerunAdvised를 무시하지 않는다.
export const meta = {
  name: 'essay-item-verify',
  description: '채점기준 급간 게이트와 문서 정합성 리뷰',
  phases: [
    { title: '검증', detail: '급간 게이트 · 어긋남 리뷰어' },
    { title: '판정', detail: '지적의 적대적 재검증' },
  ],
}

// 이 스킬이 설치된 절대경로. 에이전트가 python3·Read로 직접 여는 경로라 ~ 는 쓰지 않는다.
// 보통 <홈>/.claude/skills/math-essay-item 이고, 셸에서 `echo "$HOME/.claude/skills/math-essay-item"`으로 확인한다.
const K = '@@스킬 루트 절대경로@@'
const TARGET = '@@검토 대상 슬롯 JSON 경로@@'   // rubric_rows·발문·조건·답안·유의점·성취수준이 든 파일
const FACTS = `@@평가 유형 프로파일(수행평가|지필평가)과 확정 수치 목록·배점 체계(예: 수행평가 — 문항별 4/4/7/5, 총 20점, 0점 급간 없음 / 지필평가 — 요소마다 0점 급간, 총 20점). 학교 학업성적관리규정 오버라이드가 있으면 그 확정값(최저 급간·0점 문구·요소 최소 배점)을 함께 적고 검사 기준으로 삼는다@@`

// ── 응답 런타임 검증 ───────────────────────────────────────────────
// fail-closed: 스키마 required가 강제되지 않아도 truthy 불완전 객체({}·필드 누락·빈 문자열)를
// 통과시키지 않는다. keys 원소는 'name'(비어 있지 않은 문자열) 또는 'name:boolean'으로 쓴다.
function need(o, keys, who) {
  if (!o || typeof o !== 'object' || Array.isArray(o))
    throw new Error(`${who} 실패 — 응답 없음 또는 객체가 아님(fail-closed)`)
  const bad = keys
    .map(spec => spec.split(':'))
    .filter(([k, kind]) => (kind === 'boolean' ? typeof o[k] !== 'boolean' : typeof o[k] !== 'string' || !o[k].trim()))
    .map(([k]) => k)
  if (bad.length)
    throw new Error(`${who} 실패 — 필수 필드 누락·빈 값: ${bad.join(', ')}(fail-closed)`)
  return o
}

// rebuttals: 자기 반증 기록. 실사용에서 차단성 지적의 절반가량이 수선 단계에서 반증돼 기각됐고,
// 반증 근거의 다수가 "문서의 다른 조항이 이미 처리하고 있다"였다 — 검증자가 그 조항을 못 찾은 것이다.
// 반증 시도를 스키마 필수 필드로 두어 (1) 건너뛴 에이전트가 fail-closed로 걸리고,
// (2) 재검증이 "이미 훑었다"는 주장을 표본으로 확인할 수 있게 한다.
const V_KEYS = ['blocking:boolean', 'issues', 'fixes', 'rebuttals']
const V = {
  type: 'object', required: V_KEYS.map(k => k.split(':')[0]),
  properties: {
    blocking: { type: 'boolean', description: '아래 blocking 문턱 셋을 모두 만족하는 결함이 있으면 true' },
    issues: { type: 'string', description: '위치와 근거. 시나리오로 시험한 결과를 포함. 지적마다 자기 반증에서 어디를 찾았는데 없었는지 한 줄로 붙인다. 결함이 없어도 시험한 시나리오와 그 결과를 적는다(빈 문자열 금지 — 빈 값이면 실패로 처리한다)' },
    fixes: { type: 'string', description: '그대로 붙여 쓸 수 있는 수정 문장. 고칠 것이 없으면 "없음"이라고 적는다(빈 문자열 금지)' },
    rebuttals: { type: 'string', description: '자기 반증 기록. 올리려다 스스로 기각한 지적마다 `[기각] 지적 요지 / 이미 처리하는 조항의 슬롯·원문`을 적는다. 기각한 것이 없으면 검색 기록을 적는다 — `기각 0건 · 검색어 …, 슬롯 …, 적중 0건`(빈 문자열 금지)' },
  },
}

// 두 검증 겹이 공유하는 자기 반증 절차. 재검증 단계에만 있던 요구를 지적을 올리는 단계로 앞당긴다.
const REBUT = `[자기 반증 — 지적을 올리기 전에 반드시 수행한다]
결함 하나를 올리기로 마음먹었으면, 올리기 전에 **그 문제를 이미 처리하고 있는 조항이 문서에 있는지 먼저 찾아라.**
전수로 훑을 자리는 다음 전부다 — 학생 지면 〈조 건〉(item_cond)·발문(item_questions),
〈채점 시 유의점〉과 부분 인정 기준(partial), 〈피드백 제공 시 유의점〉(caution),
원자 정의(_rubric_atoms_note), 급간 진술 전체(rubric_rows[].desc),
성취수준 진술(std1_A~std1_E·std2_A~std2_E·level_A_desc~level_E_desc), 평가 요소(item1_element~item4_element).
눈으로 훑지 말고 python3로 훑어라 — 지적의 핵심 술어를 2~3개 검색어로 뽑아 위 슬롯 전문에서 찾고, 검색어와 적중 문장을 그대로 남긴다.
· 처리하는 조항을 **찾았으면 그 지적은 올리지 않는다.** issues가 아니라 rebuttals에 그 위치와 원문을 적어라.
· 못 찾았을 때만 issues에 올리고, 지적마다 "어느 슬롯을 어떤 검색어로 찾았는데 0건이었다"를 한 줄 붙여라.
· 두 조항이 **둘 다 있고 서로 다른 점수를 지시**하는 경우는 반증이 아니라 확정이다(F03·F07).
  이때는 두 조항의 위치를 모두 인용하고 어느 쪽이 권위인지까지 적어라 — 학생 지면 〈조 건〉이 당사자이면 조건이 권위다(F07 「조건 우선 규칙」).

[blocking 문턱] blocking=true는 다음 셋을 **모두** 만족할 때만 쓴다.
 (1) 그 결함이 실현되는 **구체적 학생 답안 또는 계산**을 실제로 써 보였다.
 (2) 위 자기 반증을 수행했고, 그 문제를 처리하는 조항을 문서 어디에서도 찾지 못했다.
 (3) 고치지 않고 시행하면 **같은 답안이 채점자에 따라 다른 점수**를 받거나, **산술 항등식·평가 유형 프로파일 규칙이 실제로 깨진다**.
셋 중 하나라도 미달이면 blocking=false로 두고 issues에 권고로 적어라. 확신이 서지 않으면 blocking=false다.
문체·표현 취향, 더 나은 대안의 제시, "명확히 하면 좋겠다"는 blocking이 아니다.`

const BASE = `당신은 회의적인 검증자다. 작성자의 자기 보고를 믿지 않는다.

[검토 대상] "${TARGET}" — python3로 직접 읽어라.
[확정 사실] ${FACTS}

[반드시 읽을 것]
· "${K}/references/failure-modes.md" — 실제로 발생했던 결함 카탈로그. 이 목록을 탐색 기준으로 쓴다.
· "${K}/references/rubric-rules.md" — 급간 설계 규칙과 기계 검사 체크리스트.
· "${K}/references/standards.md" — 성취수준 점수 구간과 평가 유형별 floor 계산.

python3로 직접 계산·대조하라. 눈으로 훑고 판단하지 말 것.`

phase('검증')

const checks = await parallel([
  // (a) 급간 게이트 — 적대적
  () => agent(`${BASE}

[급간 게이트]
채점 요소마다 급간이 **배타적이고 포괄적인지** 시험하라. 추상적으로 판단하지 말고 **답안 시나리오를 직접 구성해서** 시험한다.

1. 각 요소마다 **두 급간에 동시에 걸리는 답안**을 만들어 보라. 만들어지면 그 급간 진술은 배타적이지 않다.
2. 각 요소마다 **어느 급간에도 걸리지 않는 답안**을 만들어 보라. 특히 다음을 반드시 시험하라.
   · 백지 답안 — 0단계에서 정한 평가 유형 프로파일에 따라 검사한다. 수행평가면 0점 급간 0건에 최저 1점 급간이 백지를 포괄해야 한다("…하려 하였으나"처럼 시도를 전제로 건 진술이 있으면 백지가 빠진다). 지필평가면 요소마다 0점 급간 1건이 있고 진술이 "무응답 또는 그 외의 오답."으로 고정되며, 급간이 배점 s부터 0까지 연속이어야 한다.
   · 요구된 것 중 하나만 수행한 답안
   · 원리와 식은 옳고 마지막 계산만 틀린 답안
   · 앞 문항의 틀린 값을 이어받아 이후 절차를 옳게 수행한 답안
   · 발문이 요구한 하위 과제 하나를 통째로 빠뜨린 답안
3. 급간 진술과 〈채점 시 유의점〉·공통 원칙이 **서로 다른 점수를 지시**하는 곳이 있는지 대조하라.
4. 기계 검사: 요소별 배점 합 = 문항 배점, 총합 일치, 급간 문장 50자 이하·한 문장, 금지 표기(⑴⑵⑶·[채점 요소 N]·마크다운) 0건. 급간 구조는 평가 유형 프로파일로 가른다 — 수행평가: 급간이 배점부터 1까지 1씩 하강·0점 급간 0건, 지필평가: 배점부터 0까지 1씩 하강·요소마다 0점 급간 1건(데이터 행 수 = Σ(요소 배점 + 1)). 수행평가의 요소 최고 배점은 2~4점, 지필평가는 1~4점이어야 한다. 수행평가의 1점 요소와 두 프로파일 모두의 5점 이상 요소를 차단하라.

${REBUT}

fixes에는 **그대로 붙여 쓸 수 있는 교체 문장**을 글자 수와 함께 적어라.`,
    { label: '급간 게이트', phase: '검증', schema: V, effort: 'max' })
    .then(r => ({ ...need(r, V_KEYS, '급간 게이트 에이전트'), label: '급간 게이트' })),

  // (b) 어긋남 리뷰어 — 정합성
  () => agent(`${BASE}

[어긋남 리뷰어]
문서 전체의 상호 참조와 표기가 어긋나지 않는지 **전수 대조**하라.

1. **배점 표기 일치** — 채점기준표의 요소 배점 합, 발문 끝의 (n점) 표기, 도입부 총점, 과제 개요, 차시 평가란, 합계 행이 모두 같은 체계인가. 총점을 바꿨다면 이 다섯 곳이 **모두** 바뀌었는지 확인하라.
2. **성취수준 구간** — A~E가 0점부터 총점까지를 겹침 없이 빠짐없이 덮는가. 수행평가는 실제 요소별 최저 급간의 합 floor를 계산하고, 도달 가능 범위 floor~총점의 각 점수를 A~E로 재분할하여 다섯 수준이 모두 도달 가능 점수를 최소 1개 포함하는지 확인하라. 0~floor−1은 E의 하한을 0으로 확장하여 흡수하되, E의 상한은 반드시 floor 이상이어야 한다. 지필평가는 기본 floor=0이므로 0~총점을 다섯 수준으로 분할하고 각 수준이 최소 1점을 포함하는지 확인하라.
3. **참조 무결** — 발문·조건·예시답안·채점기준·유의점이 서로를 가리키는 번호와 이름이 실제 정의처와 일치하는가. 삭제된 규정을 가리키는 죽은 참조가 있는가.
4. **성취기준 정렬** — 선언한 성취기준을 실제로 가르치고(차시) 평가하는가(문항·채점기준). 평가 요소와 무관한 성취기준·차시 내용이 남아 있는가.
5. **평가 요소 ↔ 채점 요소** — 상위 평가 요소에 없는 수행이 채점 요소로 배점을 갖고 있는가. 발문이 요구한 하위 과제가 최고 급간에서 빠졌는가.
6. **중복 인쇄** — 같은 문장이 두 곳에 들어가 있는가.
7. **문체** — 발문 "…시오", 조건 "~할 것", 교사용 "~함/한다"가 지켜지는가. 학생 지면에 채점자 문체가 노출되는가.
8. **조건의 채점 권위**(F07) — 〈조 건〉의 의무 조항을 \`C①\`처럼 번호 붙여 뽑고(의무 표지는 \`[가-힣] 것[.\\s]\`·\`하시오\`·\`반드시\` 무늬로 잡는다 — \`나타낼 것\`을 낱말 목록으로 적으면 빠뜨린다), 조항이 규율하는 대상을 유의점·원자 정의·급간·성취수준 진술 전수에서 검색해 **조항마다 처리 절의 개수와 방향**을 세어라. 방향은 문장이 아니라 **절 단위**로 판정한다("A는 인정하되 B는 보지 않으며"가 한 문장이다). 면제 표지(\`가르지 않\`·\`채점 요소가 아니\`·\`감점하지 않\`)나 경계 없는 술어(\`사소한\`·\`달라지지 않는 한\`)가 규율 대상과 같은 절에 있으면 결함이다. **조항을 어겨야만 나오는 값을 python3로 계산해** 그 값이 인정 절에 인쇄되어 있는지 문자열로 찾아라. 수정은 「조건 우선 규칙」에 따라 조건을 권위로 삼는다 — 유의점으로 조건을 면제하는 안은 내지 마라.

${REBUT}

fixes에는 교체 문장을 그대로 쓸 수 있게 적어라.`,
    { label: '어긋남 리뷰어', phase: '검증', schema: V, effort: 'max' })
    .then(r => ({ ...need(r, V_KEYS, '어긋남 리뷰어 에이전트'), label: '어긋남 리뷰어' })),
])

phase('판정')

// fail-closed(A-2): 실패한 검증 에이전트를 조용히 걸러내고 통과시키지 않는다.
const done = checks.filter(Boolean)
if (done.length < 2)
  throw new Error(`검증 에이전트 ${2 - done.length}개 실패 — 두 겹이 모두 끝나기 전에는 판정하지 않는다`)

const RV_KEYS = ['real:boolean', 'blocking:boolean', 'reason', 'handledAt']
const RV = {
  type: 'object', required: RV_KEYS.map(k => k.split(':')[0]),
  properties: {
    real: { type: 'boolean', description: '반증에 실패해 실제 결함으로 확정되면 true' },
    blocking: { type: 'boolean', description: '실제 결함이며 위 blocking 문턱 셋을 모두 만족하면 true' },
    reason: { type: 'string', description: '반증 시도와 그 결과. 빈 문자열 금지 — 빈 값이면 실패로 처리한다' },
    handledAt: { type: 'string', description: '그 문제를 이미 처리하고 있던 조항의 위치(슬롯·문장)와 원문. 그런 조항이 없으면 정확히 "없음"이라고 적는다(빈 문자열 금지)' },
  },
}

// 지적을 적대적으로 재검증한다 — 그럴듯하지만 틀린 지적을 걸러 낸다
const verdicts = await parallel(done.map((c, i) => () =>
  agent(`${BASE}

[재검증] 아래 지적이 실제 결함인지 판정하라. **반증을 먼저 시도하고**, 확신이 서지 않으면 real=false로 한다.
문서의 다른 조항이 이미 그 문제를 처리하고 있지는 않은지 반드시 확인하라(폴백 규칙, 공통 원칙, 유의점, 원자 정의, 성취수준 진술).
이미 처리하는 조항을 찾았으면 real=false로 하고 handledAt에 그 위치와 원문을 적어라. 못 찾았으면 handledAt은 "없음"이다.
두 조항이 **둘 다 있고 서로 다른 점수를 지시**하면 그것은 반증이 아니라 확정이다(F03·F07) — real=true로 하고 handledAt에 두 위치를 모두 적어라.
real=true이면서 blocking=true로 하려면 위 blocking 문턱 셋을 모두 만족해야 한다.

지적:
${c.issues}

제안된 수정:
${c.fixes}

이 지적을 올린 검증자가 스스로 훑었다고 보고한 반증 기록(그대로 믿지 말고 두 곳 이상 표본으로 다시 확인하라):
${c.rebuttals}`,
    { label: `재검증:${c.label || i}`, phase: '판정', schema: RV, effort: 'high' })
    .then(v => ({ ...c, verdict: need(v, RV_KEYS, `재검증 에이전트 ${c.label || i}`) }))
))

// fail-closed(A-2): 재검증이 죽은 지적은 버리지도 통과시키지도 않는다.
if (verdicts.some(v => !v || !v.verdict))
  throw new Error('재검증 에이전트 실패 — 재검증 없는 지적이 남아 있어 판정하지 않는다')

// 명시적 승인 게이트: 두 겹 완료 + 재검증에서 확정된 차단성 결함 0건일 때만 pass.
// 최초 에이전트의 blocking 자기 분류는 신뢰하지 않는다 — 재검증의 real·blocking만 본다.
const confirmed = verdicts.filter(v => v.verdict.real && v.verdict.blocking)

// 반증률 계측. 기각된 지적의 근거가 "이미 처리하는 조항이 있었다"이면 그 겹은 자기 반증을
// 실제로는 수행하지 않은 것이다 — 실사용에서 차단성 지적의 절반가량이 이 사유로 기각됐다.
const precision = verdicts.map(v => ({
  label: v.label || '(무명)',
  raisedBlocking: v.blocking,
  confirmed: v.verdict.real && v.verdict.blocking,
  rebutted: !v.verdict.real,
  handledAt: v.verdict.handledAt,
  missedExistingClause: !v.verdict.real && v.verdict.handledAt.trim() !== '없음',
}))
// pass 판정은 반증률로 바꾸지 않는다 — 반증률로 막으면 검증자가 지적을 덜 올리는 역유인이 생긴다.
// 대신 다시 돌릴 겹을 지목해 5단계(수선)가 판단하게 한다.
const rerunAdvised = precision.filter(p => p.missedExistingClause).map(p => p.label)

return {
  pass: confirmed.length === 0,
  confirmedBlocking: confirmed,
  precision,
  rerunAdvised,      // 비어 있지 않으면 그 겹을 반증 기록을 붙여 한 번 더 돌린다
  checks: verdicts,
}
