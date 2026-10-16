# feat(eval): 기존 질문 중심 평가 노트북 통합

기존 eval_set.json의 원문 14개와 변형 31개를 01_eval_set.ipynb에서 직접 읽고 평가 계산·검증을 수행합니다.
별도 v2 노트북과 합성 60개 질문 대신 기존 질문·근거 후보를 중심으로 통합합니다.

- 질문·캐시 원본 보존, 과거 API 코드·출력은 비실행 부록에 보존.
- 평가 함수/테스트는 01 노트북에서 추출. 실제 서비스 변경 없음.
- Hit/Recall 구분, 미판정·중복·판본·split·상황 가중 비교 fixture.
- 독립 holdout은 후속 최종 평가 준비 사항이며 현재 45개는 개발용.
- 새 커널 실행·export 일치, 22 passed / 12 subtests passed (11.25s).
- 정답 사용자 검토와 실제 Before 품질 측정은 남음. API 재조회·GPU 실행 없음.

commit/push/PR 및 merge 승인 대기. 개인 fork 안에서만 반영합니다.
