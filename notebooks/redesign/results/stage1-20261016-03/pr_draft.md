# feat(eval): 기존 질문 중심 평가셋과 노트북 정비

기존 14개 질문을 평가 준비의 출발점으로 사용하도록 01_eval_set.ipynb에 지표·검증 코드를 통합합니다. 질문의 주제와 필요한 답변 행동을 구분해 Q03은 추가 질문, Q10은 외부 검색 연결 대기로 처리합니다.

## 변경
- eval_set.json v0.4.0: persona 삭제, paraphrases/related_queries 및 reasoning/factuality/retrieval/response 평가 조건 보존, Q03 dispute/clarify, Q10 policy/answer_with_external과 도구 연결 대기 표시.
- 노트북에서 기존 질문·근거 후보를 읽고 검색 지표, 사람 판정 집계, 상황별 비교, 검토표를 설명·검증합니다. 평가 함수와 테스트는 export 셀에서 추출합니다.
- 이전 API 조회 코드는 비실행 부록에 보존합니다. 별도 합성 60문항은 사용하지 않습니다.
- 평가 규약·검토 안내·작업 기록 갱신, private 라벨 경로 Git 제외.

## 검증
- 통합 노트북 새 커널 실행 및 Q03/Q10 표시 확인.
- 노트북/Python 일치 확인.
- 평가·추출·SSE: 23 passed, 12 subtests passed (11.52s).
- 서비스 app, 기존 prepare.py/rag.py, gold_texts.json 변경 없음.

## 한계
- 현재 실행 목록은 원문 14개입니다. paraphrases/related_queries는 보존하지만 자동 확장하지 않습니다.
- 세부 evaluation 필드를 전부 자동 채점하는 연결은 아직 없습니다.
- 정답 후보의 법률적 정확성을 이번 커밋에서 재검증하지 않았습니다. 사람 검토와 실제 Before 성능 측정이 남았습니다.
- 독립 holdout과 외부 검색 도구는 아직 준비/구현하지 않았습니다. 지원 대기를 범위 밖 거절의 정답으로 간주하지 않습니다.
- 과거 실행 기록은 당시 상태로 보존하며 최신 코드·데이터 해시는 stage1-20261016-03/metrics.json에 있습니다.

## 승인과 자체 검토
- [x] 사용자 commit/push/PR 승인
- [x] 개인 fork main 기준, 선행 PR #5는 이미 병합됨
- [x] 노트북/추출본 일치 및 회귀 테스트
- [x] 실측하지 않은 성능·법률 검증을 주장하지 않음
- [ ] merge 별도 승인
