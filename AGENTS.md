# AGENTS.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## AIGO 프로젝트 규칙

위 네 원칙을 기본 행동 지침으로 적용한다. 구체적인 작업 절차는 [harness/WORKFLOW.md](harness/WORKFLOW.md)를 따른다.

- 새 구현·테스트는 설명과 주석이 있는 노트북에서 작성하고 검증된 셀만 Python으로 추출한다.
- 기존 사용자 변경과 Before 자료를 보존한다. 성능 결과나 사람 점수를 추측해 채우지 않는다.
- 문제를 작은 사례로 재현하고 필요한 논문·공식 방법론을 조사한 뒤 정량·정성 평가로 판단한다. 사용자에게는 초보자도 이해할 수 있게 설명한다.
- 단계 시작·commit/push/PR·유료 실험·merge의 승인 경계를 유지한다. 지침 변경 요청을 Git 반영 승인으로 해석하지 않는다.
- 승인된 단계 안에서 성공 기준까지 검증한다. 다음 단계나 유료 실행은 해당 승인을 받은 뒤 시작한다.

## 작업 재개

RAG 재설계 작업을 시작하거나 이어갈 때 아래 기록을 읽는다.

1. `harness/WORKFLOW.md` — 실험·검증·승인·Git 반영 절차
2. `notebooks/redesign/plan.md` — 승인된 범위와 단계
3. `notebooks/redesign/progress.md` — 현재 상태·다음 행동·승인 대기
4. `notebooks/redesign/decisions.md`와 관련 `notebooks/redesign/results/experiments.jsonl` — 결정 이유와 실험 기록

작업 종료 시 결과·한계·다음 행동을 기록해 대화 기억 없이도 재개할 수 있게 한다.
