# 실행 기록

experiments.jsonl은 실행 목록이다. 한 줄이 한 실행이며 정제된 정보만 저장한다.
단계 0 검증은 모델 성능 실험이 아니다. 검색·생성 점수를 만들어 넣지 않는다.

1. 실행 전에 고유 run_id 폴더를 만든다. 같은 폴더를 덮어쓰지 않는다.
2. config.json에 question, hypothesis, variable, fixed_conditions, primary_metric, success_criteria를 기록한다.
3. 코드 commit·dirty diff 해시, 원본 노트북 해시, corpus/dataset 버전·해시, 모델 revision·양자화·프롬프트·환경·seed를 기록한다.
4. 실행 후 metrics.json, 정제된 cases.jsonl, review.md를 저장한다. 미실행/실패 지표는 null이다.
5. 목록에 run_id, stage, kind, status, artifact_dir, decision, code_commit, notebook_sha256를 추가한다.
6. decisions.md와 progress.md에서 run_id를 참조한다. commit/PR 승인 후 주소를 추가하되 실행 당시 상태는 보존한다.

status: running / completed / failed / interrupted. decision: pending / keep / discard.
사람 검토 전 점수는 null이다. 실행 로그·답변을 무조건 Git에 넣지 않는다.
holdout 정답·사용자 원문·인증키가 든 API URL·대형 자료는 Git 밖에 보관하고 정제 요약·해시·복구 방법만 기록한다.
review.md에는 개선·회귀·미해결 사례, 모든 심각한 오류, 누수·baseline 공정성·복잡도 검토를 작성한다.
시간·비용·호출 한도는 유료 실행 전에 승인된 값만 사용한다.
