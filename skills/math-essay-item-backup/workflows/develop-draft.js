// 1단계 — 문항 초안 3개 병렬 생성 + 수치 검산 + 심사
// Workflow 도구로 실행한다. @@ 자리를 실제 값으로 바꿔 쓴다.
export const meta = {
  name: 'essay-item-draft',
  description: '서논술형 문항 초안 3개 생성 후 심사',
  phases: [
    { title: '초안', detail: '소재 각도별 병렬 생성 + 자체 수치 검산' },
    { title: '심사', detail: '전이성·수치·채점 가능성 평가' },
  ],
}

const K = '/Volumes/ssdmacmini 1/han ex/.claude/skills/math-essay-item'

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

// ── 0단계에서 받은 입력 ────────────────────────────────────────────
const INPUT = {
  standard: '@@성취기준 코드와 문구@@',
  element: '@@평가 요소@@',
  grade: '@@학교급·학년@@',
  total: '@@총점@@',            // 예: '20점 4문항(4/4/7/5)'
  minutes: '@@평가 시간@@',
  hint: '@@사용자가 제시한 초안 느낌. 없으면 "지정 없음"@@',
}

const BASE = `당신은 한국 중등 수학 서·논술형 평가 문항 개발 전문가다.

[개발 조건]
· 성취기준: ${INPUT.standard}
· 평가 요소: ${INPUT.element}
· 대상: ${INPUT.grade}
· 배점: ${INPUT.total}
· 평가 시간: ${INPUT.minutes}
· 사용자가 제시한 방향: ${INPUT.hint}

[반드시 읽을 것 — python3로 직접 읽어라]
· "${K}/references/transfer-and-numbers.md" — 전이성 5요건과 수치 설계 원칙, 검산 게이트
· "${K}/examples/examples-pizza.md" — 감사용 few-shot. 확정 사례와 개발 중 발견된 결함 실물이 섞여 있다. '복제 가능' 표시 블록만 문체·구조 본보기로 쓰고, '결함·복제 금지' 블록과 성취수준 구간·급간 점수 수치는 모방하지 말 것
· "${K}/references/standards.md" — 성취기준·평가요소·채점요소의 정렬 규칙

[전이성 5요건 — 모두 갖출 것]
⑴ 학습 맥락과 다른 새 맥락에서 같은 개념을 쓴다
⑵ 공식을 주지 않고 학생이 관계를 도출한다
⑶ 오개념을 진단하는 장치가 있다(자료 속 인물의 잘못된 계산을 반박하게 하는 구조)
⑷ 정답은 하나로 떨어지되 도달 경로가 여러 개다
⑸ 역방향 추론이 있다(결과에서 조건을 되짚기)

[수치 검산 — 반드시 python3로 수행하고 결과를 함께 낼 것]
· 문항에 등장하는 모든 값과 정답을 전수 재계산한다.
· 학년 범위 위반을 검사한다: 무리수, 세제곱근, 미학습 개념이 필요해지면 조건을 바꿔 제곱으로 환원하거나 값을 다시 고른다.
· 값이 정수나 유한소수로 떨어지는지 확인한다. 떨어지지 않으면 소재나 수치를 바꾼다.
· 오답 경로(오개념대로 계산했을 때의 값)도 계산해 둔다.
· 선택지가 있다면 변별이 생기는지 확인한다(모든 선택지가 같은 결론이면 실패).
검산에 실패하면 **스스로 수치를 고쳐 다시 계산**한 뒤 최종본만 낸다.`

phase('초안')

const ANGLES = [
  { key: 'a', angle: '구매·의사결정 — 예산 안에서 여러 방안을 비교해 고르는 상황' },
  { key: 'b', angle: '설계·제작 — 조건을 만족하는 새 규격을 거꾸로 설계하는 상황' },
  { key: 'c', angle: '검수·판별 — 주어진 측정값에서 성질을 판별하고 반례를 가려내는 상황' },
]

const DRAFT = {
  type: 'object',
  required: ['title', 'scenario', 'materials', 'questions', 'numbers', 'transfer', 'verify_log'],
  properties: {
    title: { type: 'string', description: '문항 제목' },
    scenario: { type: 'string', description: '〔상 황〕 본문' },
    materials: { type: 'string', description: '자료 1~3(가격표·대화방·쪽지 등). 줄바꿈 구분' },
    questions: { type: 'string', description: '문항 1~4 발문. 배점 표기 포함' },
    numbers: { type: 'string', description: '확정 수치 설계표. 값과 그 값을 고른 이유' },
    transfer: { type: 'string', description: '전이성 5요건이 각각 어디에서 충족되는지' },
    verify_log: { type: 'string', description: 'python3 검산 결과. 재계산한 항목과 값, 학년 범위 검사 결과' },
  },
}

const drafts = await parallel(ANGLES.map(a => () =>
  agent(`${BASE}

[이 초안의 소재 각도] ${a.angle}
이 각도로 문항 세트를 설계하라. 다른 두 각도로 동시에 개발 중이므로 **이 각도의 특성을 살려** 차별화하라.

[산출]
상황·자료·발문 4문항을 완성하고, 수치 설계표와 전이성 5요건 충족 근거, python3 검산 로그를 함께 내라.
발문은 "…시오." 종결, 조건은 "~할 것", 배점은 문항 끝에 (4점) 형태로 표기한다.`,
    { label: `초안:${a.key}`, phase: '초안', schema: DRAFT, effort: 'max' })
    .then(r => {
      // fail-closed: null·{}·필수 필드 누락·빈 문자열을 모두 차단한 뒤에만 spread한다.
      need(r, DRAFT.required, `초안 에이전트 ${a.key}`)
      return { ...r, key: a.key, angle: a.angle }
    })
))

phase('심사')

// fail-closed(A-2): 실패한 초안 에이전트를 조용히 걸러내고 진행하지 않는다.
const valid = drafts.filter(Boolean)
if (valid.length < ANGLES.length)
  throw new Error(`초안 에이전트 ${ANGLES.length - valid.length}개 실패 — ${valid.length}/${ANGLES.length}건으로 심사를 진행하지 않는다`)
const REVIEW = {
  type: 'object', required: ['ranking', 'best', 'fixes', 'grafts'],
  properties: {
    ranking: { type: 'string', description: '순위와 근거' },
    best: { type: 'string', enum: ANGLES.map(a => a.key), description: '1위 초안의 key' },
    fixes: { type: 'string', description: '1위 초안에서 반드시 고칠 점. 없으면 "없음"이라고 적는다(빈 문자열 금지)' },
    grafts: { type: 'string', description: '다른 초안에서 옮겨 올 아이디어. 없으면 "없음"이라고 적는다(빈 문자열 금지)' },
  },
}

const review = await agent(`${BASE}

[심사] 아래 초안 ${valid.length}개를 평가하라.

각 초안에 대해 python3로 **수치를 독립 재계산**하고, 다음을 판정하라.
(i) 전이성 5요건 — 각 요건을 실제로 충족하는가. 형식적으로 붙인 것과 구조에 녹아 있는 것을 구분하라.
(ii) 수치 견고성 — 값이 떨어지는가, 학년 범위를 벗어나지 않는가, 변별이 생기는가, 오답 경로가 의미 있게 갈리는가.
(iii) 채점 가능성 — 이 발문으로 관찰 가능한 수행을 몇 개나 뽑을 수 있는가. 배점 배분이 가능한가.
(iv) 시간 적정성 — 주어진 평가 시간 안에 마칠 분량인가.

순위를 매기고, 1위 초안에 대해 **반드시 고쳐야 할 점**을 구체적으로 적어라. 2·3위에서 1위로 옮겨 올 만한 좋은 아이디어가 있으면 그것도 적어라.

초안:
${JSON.stringify(valid, null, 1)}`,
  { label: '심사', phase: '심사', schema: REVIEW, effort: 'max' })

// fail-closed: 먼저 필수 필드(존재·문자열·비어 있지 않음)를 확인하고, 그다음 best의 유효성을 본다.
need(review, REVIEW.required, '심사 에이전트')
const validKeys = new Set(valid.map(d => d.key))
if (!validKeys.has(review.best))
  throw new Error(`심사 에이전트 실패 — best=${JSON.stringify(review.best)}가 유효한 초안 key가 아님(fail-closed)`)

return { pass: true, drafts: valid, review }
