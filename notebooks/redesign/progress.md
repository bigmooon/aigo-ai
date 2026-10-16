# 진행 상태 — 2026-10-16

## 현재 상태

- 단계 0 로컬 구현·검증 완료. 사용자가 commit·push·PR 생성을 승인했으며 반영 진행 중이다. merge는 미승인이다.
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
- PR 본문: results/stage0-20261016-01/pr_draft.md. 생성된 PR 번호는 GitHub의 이 브랜치 PR에서 확인한다.

## 다음 행동

1. 승인된 단계 0 변경을 commit·push하고 개인 fork main 대상 PR을 생성한다.
2. PR 체크 결과를 확인해 보고한다. merge는 별도 승인 전 수행하지 않는다.
3. 단계 1 시작 승인 후 01 노트북의 v2 평가 규약·fixture·evaluation.py 구현과 dev/holdout 라벨 검토를 진행한다.
