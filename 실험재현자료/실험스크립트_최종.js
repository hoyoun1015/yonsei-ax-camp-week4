export const meta = {
  name: 'chem-lab-demo-transcripts',
  description: 'Generate real multi-agent (7-call team) vs single-LLM chemistry design transcripts for the Virtual-Lab-style demo UI, plus blind judge scoring',
  phases: [
    { title: 'ConditionA', detail: 'single-LLM one-shot response per task' },
    { title: 'ConditionB', detail: 'real separate-agent team: draft->critic->improve->critic->improve->critic->PI synthesis' },
    { title: 'Judge', detail: 'blind rubric scoring + deliberation guess' },
  ],
}

const FORMAT_INSTR = "답변은 반드시 다음 5개 항목 형식으로 작성하시오: (1) 시약, (2) 용매, (3) 온도/시간, (4) work-up 절차, (5) 핵심 근거(2~3문장). 전체 200~300단어 내외, 한국어로 작성하시오. 서론이나 자기소개 없이 바로 항목 답변만 쓰시오."

const TASKS = [
  {
    id: 'T1',
    k: 1,
    title: '표준 환원적 아민화',
    prompt: '벤즈알데하이드와 메틸아민으로부터 N-메틸벤질아민을 얻기 위한 환원적 아민화 조건(시약/용매/온도/work-up)을 제안하시오.',
  },
  {
    id: 'T4',
    k: 1,
    title: '표준 피셔 에스터화',
    prompt: '아세트산과 이소프로판올로부터 아세트산이소프로필을 얻는 표준 피셔 에스터화 조건(시약/용매/온도/work-up)을 제안하시오.',
  },
  {
    id: 'T5',
    k: 1,
    title: '표준 그리냐르 부가',
    prompt: '페닐마그네슘브로마이드를 아세톤에 부가하여 2-페닐-2-프로판올을 얻는 표준 그리냐르 부가 조건을 제안하시오.',
  },
  {
    id: 'T6',
    k: 1,
    title: '표준 윌리엄슨 에터화',
    prompt: '페놀과 브로모에탄으로부터 페네톨(에틸페닐에터)을 합성하는 표준 윌리엄슨 에터화 조건을 제안하시오.',
  },
  {
    id: 'T7',
    k: 2,
    title: '선택적 모노-Boc 보호',
    prompt: '1,3-다이아미노프로판에서 모노-Boc 보호체만 선택적으로 얻기 위한 조건(과량 다이아민 사용, Boc2O 당량, 온도)을 제안하시오. 비스-Boc 부반응을 최소화해야 한다.',
  },
  {
    id: 'T8',
    k: 2,
    title: '선택적 모노아세틸화',
    prompt: '1,4-부탄다이올에서 모노아세틸화 생성물만 선택적으로 얻기 위한 Ac2O 당량 및 반응 조건을 제안하시오.',
  },
  {
    id: 'T9',
    k: 2,
    title: '케톤 선택적 환원',
    prompt: '메틸 4-옥소펜타노에이트(케톤과 에스터가 공존하는 기질)에서 케톤만 선택적으로 환원하고 에스터는 보존하는 환원 조건을 제안하시오.',
  },
  {
    id: 'T10',
    k: 2,
    title: '모노브롬화 선택성 제어',
    prompt: '활성화된 방향족 기질(아니솔)에서 NBS를 이용해 모노브롬화만 선택적으로 얻고 다이브롬화를 최소화하는 당량 및 조건을 제안하시오.',
  },
  {
    id: 'T2',
    k: 3,
    title: '화학선택적 환원',
    prompt: '동일 기질에 알데하이드와 니트릴이 공존할 때, 알데하이드만 선택적으로 환원하고 니트릴은 보존하는 환원 조건을 제안하시오.',
  },
  {
    id: 'T11',
    k: 3,
    title: '선택적 에스터 가수분해',
    prompt: '메틸에스터와 tert-부틸에스터가 공존하는 기질에서 메틸에스터만 선택적으로 가수분해하고 tert-부틸에스터는 보존하는 조건을 제안하시오.',
  },
  {
    id: 'T12',
    k: 3,
    title: '에폭사이드 개환 위치선택성',
    prompt: '비대칭 에폭사이드의 염기성 조건(SN2, 덜 hindered 탄소 공격) 개환 조건을 제안하고, 산성 조건에서는 위치선택성이 어떻게 달라지는지 설명하시오.',
  },
  {
    id: 'T13',
    k: 3,
    title: 'E-선택적 비티히 반응',
    prompt: '안정화 일리드를 사용해 E-선택적 비티히 반응을 수행하는 조건을 제안하고, 비안정화 일리드 사용 시 Z-선택성으로 어떻게 바뀌는지 설명하시오.',
  },
  {
    id: 'T14',
    k: 4,
    title: '프리델-크래프츠 파라선택성',
    prompt: '아니솔의 프리델-크래프츠 아실화에서 파라 선택성을 극대화하고 다이아실화를 최소화하는 촉매 당량과 온도 조건을 제안하시오.',
  },
  {
    id: 'T15',
    k: 4,
    title: '반마르코브니코프 하이드로보레이션',
    prompt: '알켄에 대해 반마르코브니코프 위치선택성으로 알코올을 얻는 하이드로보레이션-산화 조건을 제안하고, 마르코브니코프 조건(옥시수은화)과의 위치화학 차이를 설명하시오.',
  },
  {
    id: 'T16',
    k: 4,
    title: 'SN1 vs SN2 용매 제어',
    prompt: '2차 알킬할라이드에서 극성 양성자성 용매(SN1 우세, 라세미화) 조건을 제안하고, 극성 비양성자성 용매(SN2 우세, 반전) 조건과의 입체화학적 결과 차이를 설명하시오.',
  },
  {
    id: 'T17',
    k: 4,
    title: 'Directed ortho-metalation 위치제어',
    prompt: '방향족 기질의 directed ortho-metalation에서 지향기와 온도에 따라 리튬화 위치가 어떻게 달라지는지 조건과 함께 제안하시오.',
  },
  {
    id: 'T3',
    k: 5,
    title: '경쟁 반응 제어 (분자내 딜스-알더 vs 이량화)',
    prompt: '퓨란이 텐더된 다이엔-다이에노필 기질에서 분자내 딜스-알더 반응이 분자간 이량화 및 레트로-DA 분해와 경쟁하지 않도록 하는 조건(농도/온도/촉매)을 제안하시오.',
  },
  {
    id: 'T18',
    k: 5,
    title: '나자로프 고리화 torquoselectivity',
    prompt: '나자로프 고리화의 컨로테이토리 폐환 입체특이성이 루이스산 세기에 따라 어떻게 torquoselectivity가 달라지는지 조건과 함께 제안하시오.',
  },
  {
    id: 'T19',
    k: 5,
    title: '도미노 마이클-알돌 부분입체선택성',
    prompt: '도미노 마이클-알돌 반응 순서에서 염기 세기와 온도에 따라 부분입체선택성이 어떻게 달라지는지 조건과 함께 제안하시오.',
  },
  {
    id: 'T20',
    k: 5,
    title: '옥시-코프 vs 레트로-엔 경쟁 제어',
    prompt: '음이온성 옥시-코프 재배열이 레트로-엔 경쟁 경로와 맞서는 기질에서 짝이온(K+ vs Na+)과 용매(THF vs DMSO)에 따른 최적 조건을 제안하시오.',
  },
]

const AGENTS = {
  synthetic_chemist: { title: '합성화학자', expertise: '반응 경로와 시약 선택' },
  mechanistic_chemist: { title: '반응메커니즘 전문가', expertise: '전자이동과 전이상태 분석' },
  safety_specialist: { title: '공정안전 전문가', expertise: '실험실 안전성 및 스케일업 위험성 평가' },
  critic: { title: 'Scientific Critic', expertise: '과학적 추론에 대한 비판적 평가' },
  pi: { title: 'PI', expertise: 'AI 보조 화학 연구 설계 총괄' },
}

const JUDGE_SCHEMA = {
  type: 'object',
  properties: {
    scores_first: {
      type: 'object',
      properties: {
        reagent: { type: 'number' },
        condition: { type: 'number' },
        mechanism: { type: 'number' },
        safety: { type: 'number' },
      },
      required: ['reagent', 'condition', 'mechanism', 'safety'],
    },
    scores_second: {
      type: 'object',
      properties: {
        reagent: { type: 'number' },
        condition: { type: 'number' },
        mechanism: { type: 'number' },
        safety: { type: 'number' },
      },
      required: ['reagent', 'condition', 'mechanism', 'safety'],
    },
    more_deliberated: { type: 'string', enum: ['제안1', '제안2'] },
  },
  required: ['scores_first', 'scores_second', 'more_deliberated'],
}

function assertOk(text, label) {
  if (!text) throw new Error(`agent call ${label} returned null/empty — aborting this task instead of propagating corrupted input`)
  return text
}

async function runConditionA(task) {
  const prompt = `당신은 화학 설계를 담당하는 단일 전문가입니다. 토론이나 검토 없이 혼자 최종 답을 제시하시오.\n\n과제: ${task.prompt}\n\n${FORMAT_INSTR}`
  const response = assertOk(await agent(prompt, { label: `A:${task.id}`, phase: 'ConditionA' }), `A:${task.id}`)
  return { task, conditionA: response }
}

async function runConditionB(prev) {
  const { task, conditionA } = prev

  const draft = assertOk(await agent(
    `당신은 "${AGENTS.synthetic_chemist.title}"입니다(전문성: ${AGENTS.synthetic_chemist.expertise}). 다음 화학 설계 과제에 대한 초안을 제시하시오.\n\n과제: ${task.prompt}`,
    { label: `B1-draft:${task.id}`, phase: 'ConditionB' }
  ), `B1-draft:${task.id}`)
  const critic1 = assertOk(await agent(
    `당신은 "Scientific Critic"입니다(전문성: ${AGENTS.critic.expertise}). 아래 초안을 비판적으로 검토해 오류, 누락, 위험을 구체적으로 지적하시오.\n\n초안:\n${draft}`,
    { label: `B2-critic1:${task.id}`, phase: 'ConditionB' }
  ), `B2-critic1:${task.id}`)
  const improve1 = assertOk(await agent(
    `당신은 "${AGENTS.mechanistic_chemist.title}"입니다(전문성: ${AGENTS.mechanistic_chemist.expertise}). 아래 초안과 비판을 반영해 메커니즘 관점에서 개선안을 제시하시오.\n\n초안:\n${draft}\n\n비판:\n${critic1}`,
    { label: `B3-improve1:${task.id}`, phase: 'ConditionB' }
  ), `B3-improve1:${task.id}`)
  const critic2 = assertOk(await agent(
    `당신은 "Scientific Critic"입니다. 아래 개선안을 다시 비판적으로 검토하시오. 남아있는 문제가 있다면 지적하시오.\n\n개선안:\n${improve1}`,
    { label: `B4-critic2:${task.id}`, phase: 'ConditionB' }
  ), `B4-critic2:${task.id}`)
  const improve2 = assertOk(await agent(
    `당신은 "${AGENTS.safety_specialist.title}"입니다(전문성: ${AGENTS.safety_specialist.expertise}). 아래 개선안과 비판을 반영해 안전성을 포함한 최종 개선안을 제시하시오.\n\n개선안:\n${improve1}\n\n비판:\n${critic2}`,
    { label: `B5-improve2:${task.id}`, phase: 'ConditionB' }
  ), `B5-improve2:${task.id}`)
  const critic3 = assertOk(await agent(
    `당신은 "Scientific Critic"입니다. 아래 최종 개선안에 남은 문제가 있는지 마지막으로 검토하시오. 큰 문제가 없다면 그렇게 명시하시오.\n\n최종개선안:\n${improve2}`,
    { label: `B6-critic3:${task.id}`, phase: 'ConditionB' }
  ), `B6-critic3:${task.id}`)
  const finalAnswer = assertOk(await agent(
    `당신은 "PI"입니다(전문성: ${AGENTS.pi.expertise}). 아래 팀 논의 전체를 종합해 최종 답변을 작성하시오.\n\n초안:\n${draft}\n\n1차비판:\n${critic1}\n\n1차개선안:\n${improve1}\n\n2차비판:\n${critic2}\n\n2차개선안(최종개선안):\n${improve2}\n\n3차비판:\n${critic3}\n\n${FORMAT_INSTR}`,
    { label: `B7-final:${task.id}`, phase: 'ConditionB' }
  ), `B7-final:${task.id}`)

  const rounds = [
    { round: 1, speaker: 'synthetic_chemist', label: '초안 제안', text: draft },
    { round: 1, speaker: 'critic', label: '1차 비판', text: critic1 },
    { round: 2, speaker: 'mechanistic_chemist', label: '메커니즘 개선안', text: improve1 },
    { round: 2, speaker: 'critic', label: '2차 비판', text: critic2 },
    { round: 3, speaker: 'safety_specialist', label: '안전성 반영 최종개선안', text: improve2 },
    { round: 3, speaker: 'critic', label: '3차 비판(최종)', text: critic3 },
    { round: 4, speaker: 'pi', label: 'PI 최종 통합', text: finalAnswer },
  ]

  return { task, conditionA, conditionB: { rounds, finalResponse: finalAnswer } }
}

async function runJudge(prev, originalItem, index) {
  const { task, conditionA, conditionB } = prev
  const bIsFirst = index % 2 === 0
  const first = bIsFirst ? conditionB.finalResponse : conditionA
  const second = bIsFirst ? conditionA : conditionB.finalResponse

  const rubric = '각 항목을 1~5점으로 채점하시오: reagent(시약 적절성), condition(조건 현실성), mechanism(메커니즘 타당성), safety(안전성).'
  const prompt = `다음은 화학 설계 과제와 그에 대한 두 익명의 제안입니다. ${rubric}\n또한 어느 제안이 더 숙고를 거친 것처럼 보이는지 more_deliberated 필드에 "제안1" 또는 "제안2"로 답하시오.\n\n과제: ${task.prompt}\n\n제안1:\n${first}\n\n제안2:\n${second}`

  const judged = await agent(prompt, { label: `J:${task.id}`, phase: 'Judge', schema: JUDGE_SCHEMA })

  const scoresB = bIsFirst ? judged.scores_first : judged.scores_second
  const scoresA = bIsFirst ? judged.scores_second : judged.scores_first
  const avg = s => (s.reagent + s.condition + s.mechanism + s.safety) / 4
  const avgA = avg(scoresA)
  const avgB = avg(scoresB)
  const gap = avgB - avgA
  const guessedB = bIsFirst ? judged.more_deliberated === '제안1' : judged.more_deliberated === '제안2'

  return {
    task,
    conditionA,
    conditionB,
    judge: { scoresA, scoresB, avgA, avgB, gap, guessedB, order: bIsFirst ? 'B_first' : 'A_first' },
  }
}

let ids = args
if (typeof ids === 'string') {
  try { ids = JSON.parse(ids) } catch (e) { ids = [ids] }
}
const BATCH = Array.isArray(ids) && ids.length ? TASKS.filter(t => ids.includes(t.id)) : TASKS
log(`batch filter: args=${JSON.stringify(args)} -> resolved ids=${JSON.stringify(ids)} -> BATCH=${BATCH.map(t => t.id).join(',')} (${BATCH.length} tasks)`)
const results = await pipeline(BATCH, runConditionA, runConditionB, runJudge)
return results
