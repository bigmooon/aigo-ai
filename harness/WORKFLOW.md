# AIGO 실험 작업 안내

## 작업 재개
기본 행동 지침은 [AGENTS.md](../AGENTS.md)다. 이 문서는 노트북·실험 기록·승인에 관한 프로젝트별 보완 규칙이다.

1. notebooks/redesign/plan.md: 승인된 목표·범위·종료 조건.
2. notebooks/redesign/progress.md: 현재 단계·마지막 결과·다음 행동·승인 상태.
3. notebooks/redesign/decisions.md와 해당 단계 노트북: 관련 결정·실패 기록.
4. Git 상태를 확인하고 사용자 변경과 현재 브랜치를 보존한다.

## 승인
- 2026-10-16 구현 요청은 단계 0(기록 체계·감사 노트북·설명 및 평가 규약) 시작 승인이다.
- 정답·채점표 검토자는 사용자다. 이 변경의 Git 반영은 별도 승인 대기다.
- 단계별 시작 승인 → 로컬 작업·검증 → Critical Review → diff·결과·commit 메시지·PR 초안 → 승인 후 commit/push/PR.
- merge는 별도 승인. 유료 실행도 GPU·모델·양자화·비용·최대 시간 승인을 먼저 받는다.
- docs/git_strategy.md를 따른다. 개인 fork만 push/PR하고 upstream은 fetch 전용이다. 실제 remote를 먼저 확인한다.
- PR 작성·수정 전 [.github/PULL_REQUEST_TEMPLATE.md](../.github/PULL_REQUEST_TEMPLATE.md)를 읽고, 제목별 섹션과 체크리스트를 유지해 본문을 작성한다. 임의 양식으로 대체하지 않는다.
- 체크는 실제 수행·검증한 항목에만 표시한다. 해당 없음이나 다른 방식으로 충족한 항목은 사유와 수행 방법을 명시하며, 실행하지 않은 pull/merge/노트북 실행을 했다고 표시하지 않는다.
- PR 범위가 바뀌면 템플릿에 맞춰 제목·본문·검증 결과를 최종 diff 기준으로 갱신한다. 승인된 파일만 포함하고 로컬 작업 전체를 함께 올리지 않는다.
- 자동 실험 루프와 reset --hard 폐기를 사용하지 않는다. 실패·중단·기각 증거도 보존한다.

## 코드
- 새 구현·테스트 원본은 redesign 노트북이다. 설명 → 작은 함수 → 예제 → 검증 순서.
- 함수는 한 가지 일을 하고 목적·입출력 docstring을 쓴다. 비자명한 처리에는 이유를 주석으로 설명한다.
- export 태그와 export_to 메타데이터가 있는 셀만 Python으로 추출한다. 추출 파일을 직접 편집하지 않는다.
- 처음에는 00_harness_and_audit.ipynb를 실행해 추출 도구를 만든다.
- 이후 python harness/notebook_tools.py --check로 일치 여부를 확인한다. 승인된 수정에만 --write를 사용한다.
- 단계 1까지 전체 확인: `python harness/notebook_tools.py --check notebooks/redesign/00_harness_and_audit.ipynb notebooks/redesign/01_eval_set.ipynb`. 인자를 생략하면 기존 00만 검사한다.
- 기존 수동 작성 파일의 전환은 별도 검토한다. 도구로 강제 덮어쓰지 않는다.
- prepare.py, rag.py, 기존 평가셋·서비스는 Before 자료로 보존한다. evaluation.py는 단계 1에서 작성한다.

## 방법론·기록
재현 → 원인 분류 → 논문/공식 문서 조사 → 한 변수 비교 → 정량·정성 평가 → 결정 → Critical Review.
외부 벤치마크를 AIGO 성능처럼 쓰지 않는다. 더 단순한 해결책을 먼저 비교한다.
일반 수정·테스트는 해당 노트북에 명령·결과·실패·한계를 기록하고 progress.md에 현재 상태만 갱신한다. 실행마다 config/metrics/review/PR 초안 파일을 만들지 않는다.
실제 모델·검색 비교 실험에만 실행 전 가설·변수·고정 조건·성공 기준을 고정하고 필요한 설정·원시 결과를 별도로 보관한다. 결과 기록은 results/README.md를 따른다.
실패는 failed, 중단은 interrupted, 미측정은 null이다. 기본 점수나 가짜 수치를 채우지 않는다.
holdout 정답·개인정보·인증키·대형 데이터·모델을 Git이나 기억 파일에 복사하지 않는다.

## 종료
progress.md에 완료 작업·검증 명령·한계·다음 행동·승인 대기를 갱신한다.
사용자에게 문제 → 쉬운 설명 → 비교 방법 → 결과 → 결정 → 다음 작업 순서로 보고한다.
현재 승인 단계가 끝나면 다음 단계 승인을 기다린다. 다음 세션은 파일 기록을 읽고 재개한다.
