# 진행 상태 — 기존 질문 기반 01 노트북 통합 완료

## 현재 구성
- 사용자 승인으로 Q03을 dispute/clarify로 변경했다. 기존 세부 평가 필드도 추가 질문·불확실성 표시와 일치시켰다. Q08 및 나머지 질문은 보존했다. 현재 category 개수는 dispute 6, special_terms 2, time 2, term/policy/procedure/out_of_scope 각 1이다. 유형별 표본이 작으므로 전체 평균만으로 일반화하지 않는다.
- 후속 요청: Q10은 policy / answer_with_external을 유지한다. answer_method=external_search, support_status=pending_tool로 주제·답변 방법·현재 지원 상태를 분리했다. 검색 도구 구현은 이번 변경에 포함하지 않았다.
- 최신 파일에는 변형 없이 원문 14개가 있다. 이 상태를 보존했다. 최초 검증은 과거 Q10 변형 수(3개)를 가정해 실패했고, 실제 데이터에서 개수를 읽도록 수정한 후 새 커널과 평가 테스트 12개가 통과했다. 아래 45개·이전 테스트 수는 통합 당시 기록이다.
- 후속 사용자 요청으로 eval_set.json의 persona 14개를 삭제했다. JSON 파싱 및 삭제 전후 비교로 다른 필드가 동일함을 확인했다. 참조 코드가 없어 노트북/서비스 수정은 불필요하다. 아래 통합 실행의 데이터 해시는 삭제 전 기록이다.
- 사용자 요청에 따라 01_eval_set.ipynb 하나에 질문 확인·근거 후보·평가 코드·테스트를 통합했다.
- eval/eval_set.json의 원문 14개·변형 31개를 직접 사용한다. 기존 질문·근거 캐시는 변경하지 않았다.
- 별도 01_eval_v2.ipynb와 합성 60개 질문 파일은 제거했다.
- 과거 법령 API 코드·출력·보고서는 01 부록에 당시 비실행 기록으로 보존했다. 전체 원본은 Git 이력에 있다.
- 현재 45개는 개발용이다. holdout·40/20 개수는 현재 준비 작업의 실행 조건이 아니다.
- 평가 Python/테스트의 원본 경로를 01_eval_set.ipynb로 변경하고 재추출했다.

## 검증
- 통합 노트북 새 커널 순차 실행 통과. 기존 질문·근거 후보 보존 검사 통과.
- 00/01 export 일치 통과.
- pytest tests/unit/test_evaluation.py tests/unit/test_notebook_tools.py tests/unit/test_sse.py -q -p no:cacheprovider: 22 passed, 12 subtests passed (11.25s).
- 통합 검증 당시 기존 서비스·v1 하네스·eval_set.json·gold_texts.json은 diff 없었으며, 이후 persona 필드만 삭제했다.
- 이번에는 API 재조회·모델 호출을 하지 않았다. 실제 품질 점수는 없다.
- 최신 기록: results/stage1-20261016-02/. 이전 stage1-20261016-01은 통합 전 판단·검증 이력이며 현재 파일 구조를 나타내지 않는다.

## 다음 행동·승인
- 사용자 “평가셋 관련부터 커밋 및 PR을 올리자”로 commit/push/PR 승인.
- PR #5가 병합된 것을 확인했다. 최신 개인 fork main(d21f2b6)에서 feat/eval-v2를 생성했다.
- 최종 검사: 23 passed, 12 subtests passed (11.52s), 00/01 export 일치.
- 현재 14개 원문을 읽는다. paraphrases/related_queries와 세부 evaluation 조건은 보존하지만 모두 자동 채점에 연결된 것은 아니다.
- 최신 검증·PR 본문: results/stage1-20261016-03/. 이전 실행의 45개·테스트 수는 역사적 기록이다.
- 정답 사용자 검토와 실제 Before 측정이 남았다. 이번 반영에서 법률 정답을 재검증하지 않았다.
- merge는 별도 승인 대기.

---

# 단계 0 이력 — 2026-10-16

## 현재 상태

- 단계 0 로컬 구현·검증 완료. 사용자 승인 후 commit·push·PR #5 생성을 완료했다. merge는 미승인이다.
- 시작 승인: 사용자의 전체 계획 구현 요청 중 첫 변경 묶음(하네스·감사·설명·평가 규약).
- 작업 시작 HEAD: 08d686b31904b90e9aa5d84e8803e03f51567cc2, 기존 브랜치 feat/data-survey.
- 서비스·v1 하네스·기존 01/02 노트북·평가셋은 변경하지 않았다.
- 평가 함수·새 60항목 데이터·모델 실험은 아직 구현/실행하지 않았다. 단계 1 이후 승인 대상이다.

## 완료 내용

- 후속 사용자 요청으로 네 행동 원칙과 프로젝트 규칙을 AGENTS.md에 통합하고 별도 CLAUDE.md는 제거했다. 구체적인 작업 절차는 harness/WORKFLOW.md로 이름을 바꿨다. 문서만 변경했으며 이후 사용자가 Git 반영을 승인했다.
- 이 후속 문서 변경은 stage0-20261016-01 실행 이후의 변경이다. 해당 실행의 소스 해시와 테스트 결과는 당시 기록으로 보존한다.
- AGENTS.md → harness/WORKFLOW.md를 통해 다음 세션의 작업 재개 경로를 연결했다.
- 기존 02 노트북의 주석과 과거 실행 config.json의 program.md 표기는 당시 기록으로 보존한다. 현재 작업 절차는 WORKFLOW.md를 참조한다.
- plan/decisions/evaluation_protocol/results 기록 규약을 작성했다.
- 00 노트북에서 추출 도구와 테스트를 작성하고 Python 파일로 추출했다.
- 그래프 상태 전달·인용·유사도 게이트·토큰 계측·SSE 위험을 정적 감사했다. 라이브러리 버그로 단정하지 않는다.
- 한글 설명·주석을 UTF-8로 복구한 후 깨끗한 커널에서 전체 실행했다.

## 검증

- nbformat 검증 및 NotebookClient 새 커널 전체 실행 성공.
- `.venv/Scripts/python.exe harness/notebook_tools.py --check`: 일치.
- `.venv/Scripts/python.exe -m pytest tests/unit/test_notebook_tools.py tests/unit/test_sse.py -q -p no:cacheprovider`: 11 passed, 4 subtests passed (52.05s).
- `git diff --check`: 통과. 서비스·Before 자료의 diff 없음.
- Python 실행에 로컬 sandbox 권한 제한이 있어 승인된 실행 권한으로 기존 가상환경을 사용했다. 새 패키지 설치 없음.
- Windows Jupyter의 event-loop/로컬 TCP 경고가 있었으나 실행은 성공했다.
- 기록: results/stage0-20261016-01/. RAG 품질 측정이 아닌 하네스 검증이다.

## Critical Review와 한계

- 코드 추출은 표준 라이브러리 함수 3개로 제한했다. 프레임워크나 실험 플랫폼을 추가하지 않았다.
- check는 쓰지 않으며 전체 문법·목적지 검증 후 write한다. OS 쓰기 중 실패의 원자적 복구는 제공하지 않는다.
- 미실행 RAG 품질·사람 점수·모델 비용을 만들어 넣지 않았다.
- 현재 회귀 범위는 하네스와 SSE 포맷이다. 전체 서비스 통합·GPU·원격 DB는 실행하지 않았다.
- 참고 문서와 AIGO 자체 지표 정의를 구분했다. 특히 Context Precision (AIGO)는 Ragas 순위 가중 지표와 다르다.

## Git 반영

- 사용자 승인: “이제 commit 및 PR을 올려주세요”. merge와 단계 1 시작은 포함하지 않는다.
- commit 제목: `chore(harness): 노트북 기반 실험 기록과 검증 체계 정비`
- 개인 fork: bigmooon/aigo-ai, base main, head chore/rag-harness.
- origin fetch 후 선행 10개 commit이 PR #4로 병합된 것을 확인했다: https://github.com/bigmooon/aigo-ai/pull/4
- 최신 origin/main: b54e0c4. 기존 HEAD와 파일 내용이 같음을 확인하고 여기서 새 브랜치를 만들었다.
- 선행 작업은 이번 PR에 포함되지 않는다. 팀 upstream에는 push/PR하지 않는다.
- 구현 commit: 7ecee7b25858f962187cda3e2c22f1112bbd3a0e. PR: https://github.com/bigmooon/aigo-ai/pull/5 (OPEN).
- PR 본문: results/stage0-20261016-01/pr_draft.md. 이 기록 연결은 후속 문서 commit으로 반영한다. CI 최신 상태는 PR에서 확인한다.

## 다음 행동

1. PR #5의 리뷰·CI 결과를 확인한다. 단계 0 구현과 원격 반영은 완료했다.
2. PR 체크 결과를 확인해 보고한다. merge는 별도 승인 전 수행하지 않는다.
3. 단계 1 시작 승인 후 01 노트북의 v2 평가 규약·fixture·evaluation.py 구현과 dev/holdout 라벨 검토를 진행한다.
