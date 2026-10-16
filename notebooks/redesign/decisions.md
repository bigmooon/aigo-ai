# 결정 기록

## D001 — 폴더 유지·노트북 원본 (2026-10-16)
- Context: 사용자 요청은 기존 자산을 보존하는 최소 변경과 이해하기 쉬운 코드다.
- Options: 최상위 폴더 재편 / redesign 유지.
- Evidence: 사용자 계획 승인. 성능 실험에 따른 결정은 아니다.
- Decision: redesign 유지, export 셀만 Python으로 추출한다.
- Trade-off: 원본과 추출본을 함께 관리하므로 일치 검증이 필요하다.

## D002 — 평가 v1 보존, v2 별도 정의
- Context: 기존 recall은 Hit이며 dev/test는 동일 상황의 변형/원문이다.
- Decision: 기존 코드·평가셋·결과 보존. 평가 규약과 독립 split은 단계 1에서 구현한다.
- Trade-off: 과거 점수와 v2 점수를 직접 비교할 수 없다. Before도 v2로 다시 측정해야 한다.

## D003 — 승인과 증거 보존
- Decision: 자동 실험 루프·hard reset을 중단한다. 실패·중단·기각도 기록한다.
- Evidence: 사용자 요청. 단계 시작, Git 반영, 유료 실행, merge의 승인 경계를 구분한다.
- Trade-off: 검토 대기 시간이 있지만 변경·비용의 범위가 명확하다.

## D004 — 정량·정성 별도 제시
- Decision: 임의 종합점수·미검토 기본값 금지. 근거 왜곡은 평균 점수와 관계없이 채택을 차단한다.
- Evidence: evaluation_protocol.md와 사용자 요청. 향후 실험 결정에는 실제 run_id를 연결한다.

## D005 — 평가 v2 코드와 사람 검토를 분리
- 현재 상태: 아래 별도 노트북·60개 합성 질문 결정은 사용자 요청으로 D006에서 대체했다. 이 절은 당시 판단의 이력이다.
- Context: 사용자가 다음 단계 실행을 요청하고 정답·채점표 검토자로 자신을 지정했다.
- Decision: 기존 API 검증 기록인 01_eval_set.ipynb는 보존하고 01_eval_v2.ipynb에 새 계산·테스트를 작성한다. 추출본은 harness/evaluation.py와 tests/unit/test_evaluation.py다.
- Evidence: stage1-20261016-01의 합성 fixture. Hit와 Recall 차이·중복·미판정·split 누수·상황 가중 비교를 검증한다.
- Decision: dev 40 / holdout 20 초안은 정답과 점수를 null로 두고 사용자 검토를 기다린다. ready 검사는 라벨 완결도만 보며 의미·법률 정확성을 보증하지 않는다.
- Trade-off: 60개는 실제 사용자 분포를 대표하지 않는 합성 초안이다. 공개된 holdout 질문으로 튜닝하면 사용자 작성 독립 질문으로 교체해야 한다.
- Pending: 정답 판본 라벨, 의미 중복 검토, 실제 Before 답변 확보 후 dev 10개 채점표 보정. 코드 구현 완료와 단계 전체 완료를 구분한다.

## D006 — 기존 질문 중심으로 01 노트북 통합
- Context: 사용자는 기존 eval_set 질문을 사용하고 01 노트북 하나로 합치도록 요청했다.
- Decision: 01_eval_set.ipynb가 단일 작성 원본이다. 원문 14개·변형 31개와 근거 후보를 직접 읽는다. 별도 01_eval_v2.ipynb와 합성 질문 60개 파일은 제거했다.
- Preservation: eval_set.json·gold_texts.json은 변경하지 않았다. 과거 API 코드·저장 출력·보고서는 통합 노트북 부록에 비실행 기록으로 보존했다. 전체 원본은 Git 이력에 있다.
- Evaluation: 현재 45개는 개발용이다. 독립 holdout과 40/20 개수는 현재 준비 작업의 필수 조건이 아니다. 최종 평가 전 독립 질문을 준비한다.
- Evidence: stage1-20261016-02. 새 커널에서 기존 질문·근거 보존과 export 일치를 검증한다. 실제 서비스 품질 실험은 아니다.
- Limit: 근거 후보의 현재 판본·정답 적합성은 사용자 검토가 남았다. API 재조회는 이번 통합에서 수행하지 않았다.

## D007 — 정책 주제와 지원 상태 구분
- 사용자 요청에 따라 Q10의 policy와 answer_with_external을 유지한다. 외부 검색이 필요한 것과 서비스 범위 밖인 것을 구분한다.
- answer_method=external_search, support_status=pending_tool을 기록한다. 검색 도구 연결 전 정책 답변 품질은 미측정으로 둔다. 이번에는 도구를 구현하지 않는다.
- 노트북의 policy → out_of_scope 변환을 제거했다. 외부 답변도 정답 근거가 필요한 기대 행동으로 검증한다.
