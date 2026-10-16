> 통합 전 초안입니다. 현재 PR 초안은 ../stage1-20261016-02/pr_draft.md를 사용합니다.

# feat(eval): 평가 v2 지표와 검토용 질문 초안 추가

기존 평가의 Hit/Recall 혼동과 같은 상황의 split 누수를 방지하기 위해 노트북 원본의 평가 함수를 추가합니다. dev 40 / holdout 20은 합성 질문 초안이며 정답과 사람 점수는 미검토 상태입니다.

## 변경
- 01_eval_v2.ipynb → harness/evaluation.py, tests/unit/test_evaluation.py 추출.
- Hit/Recall/Precision/MRR/nDCG@5, 검토 비율·분모, P50/P95, 상황별 paired bootstrap, split·라벨 완결도 검사, 익명 검토표.
- 사용자 검토 안내·평가 규약·실험 기록 갱신, private 라벨 경로 Git 제외.
- 기존 서비스·v1 하네스·01/02 노트북·기존 평가셋 보존.

## 검증
- 새 커널 순차 실행, 노트북/Python 일치.
- 평가·추출·SSE: 22 passed, 12 subtests passed (11.37s).
- 미판정·빈 분모·중복·다른 판본·split 누수·변형 과대 가중 fixture.

## 남은 작업
- 사용자 정답·의미 중복 검토, 실제 Before 답변으로 dev 10개 채점표 보정.
- 실제 RAG 품질·비용·전체 API 통합은 미측정. 단계 1 전체 완료를 의미하지 않음.
- PR #5 병합 여부와 최신 fork main을 Git 반영 승인 후 확인하고 이번 변경만 별도 브랜치에 반영.

## 자체 검토
- [x] 서비스와 과거 자산 보존
- [x] 미검토 점수·정답을 만들어 넣지 않음
- [x] 노트북 원본과 추출본 일치
- [x] 사용자 검토 대기와 구현 완료 구분
- [ ] 이번 변경의 commit·push·PR 승인
- [ ] merge 별도 승인
