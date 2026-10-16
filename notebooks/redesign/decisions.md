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
