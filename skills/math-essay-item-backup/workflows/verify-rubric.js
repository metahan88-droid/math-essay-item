// 4단계 — 검증 두 겹(급간 게이트 + 어긋남 리뷰어). Codex 적대적 검증은 Bash로 따로 실행한다.
// Workflow 도구로 실행한다. @@ 자리를 실제 값으로 바꿔 쓴다.
export const meta = {
  name: 'essay-item-verify',
  description: '채점기준 급간 게이트와 문서 정합성 리뷰',
  phases: [
    { title: '검증', detail: '급간 게이트 · 어긋남 리뷰어' },
    { title: '판정', detail: '지적의 적대적 재검증' },
  ],
}

const K = '/Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item'
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

const V_KEYS = ['blocking:boolean', 'issues', 'fixes']
const V = {
  type: 'object', required: V_KEYS.map(k => k.split(':')[0]),
  properties: {
    blocking: { type: 'boolean', description: '시행 전 반드시 고쳐야 하는 결함이 있으면 true' },
    issues: { type: 'string', description: '위치와 근거. 시나리오로 시험한 결과를 포함. 결함이 없어도 시험한 시나리오와 그 결과를 적는다(빈 문자열 금지 — 빈 값이면 실패로 처리한다)' },
    fixes: { type: 'string', description: '그대로 붙여 쓸 수 있는 수정 문장. 고칠 것이 없으면 "없음"이라고 적는다(빈 문자열 금지)' },
  },
}

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

차단성 결함만 blocking=true로 하고, fixes에는 **그대로 붙여 쓸 수 있는 교체 문장**을 글자 수와 함께 적어라.`,
    { label: '급간 게이트', phase: '검증', schema: V, effort: 'max' })
    .then(r => need(r, V_KEYS, '급간 게이트 에이전트')),

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

차단성 결함만 blocking=true. fixes에는 교체 문장을 그대로 쓸 수 있게 적어라.`,
    { label: '어긋남 리뷰어', phase: '검증', schema: V, effort: 'max' })
    .then(r => need(r, V_KEYS, '어긋남 리뷰어 에이전트')),
])

phase('판정')

// fail-closed(A-2): 실패한 검증 에이전트를 조용히 걸러내고 통과시키지 않는다.
const done = checks.filter(Boolean)
if (done.length < 2)
  throw new Error(`검증 에이전트 ${2 - done.length}개 실패 — 두 겹이 모두 끝나기 전에는 판정하지 않는다`)

const RV_KEYS = ['real:boolean', 'blocking:boolean', 'reason']
const RV = {
  type: 'object', required: RV_KEYS.map(k => k.split(':')[0]),
  properties: {
    real: { type: 'boolean', description: '반증에 실패해 실제 결함으로 확정되면 true' },
    blocking: { type: 'boolean', description: '실제 결함이며 시행 전 필수 수정이면 true' },
    reason: { type: 'string', description: '반증 시도와 그 결과. 빈 문자열 금지 — 빈 값이면 실패로 처리한다' },
  },
}

// 지적을 적대적으로 재검증한다 — 그럴듯하지만 틀린 지적을 걸러 낸다
const verdicts = await parallel(done.map((c, i) => () =>
  agent(`${BASE}

[재검증] 아래 지적이 실제 결함인지 판정하라. **반증을 먼저 시도하고**, 확신이 서지 않으면 real=false로 한다.
문서의 다른 조항이 이미 그 문제를 처리하고 있지는 않은지 반드시 확인하라(폴백 규칙, 공통 원칙, 유의점).

지적:
${c.issues}

제안된 수정:
${c.fixes}`,
    { label: `재검증:${i}`, phase: '판정', schema: RV, effort: 'high' })
    .then(v => ({ ...c, verdict: need(v, RV_KEYS, `재검증 에이전트 ${i}`) }))
))

// fail-closed(A-2): 재검증이 죽은 지적은 버리지도 통과시키지도 않는다.
if (verdicts.some(v => !v || !v.verdict))
  throw new Error('재검증 에이전트 실패 — 재검증 없는 지적이 남아 있어 판정하지 않는다')

// 명시적 승인 게이트: 두 겹 완료 + 재검증에서 확정된 차단성 결함 0건일 때만 pass.
// 최초 에이전트의 blocking 자기 분류는 신뢰하지 않는다 — 재검증의 real·blocking만 본다.
const confirmed = verdicts.filter(v => v.verdict.real && v.verdict.blocking)
return { pass: confirmed.length === 0, confirmedBlocking: confirmed, checks: verdicts }
