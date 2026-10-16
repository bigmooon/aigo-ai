# 기존 질문 기반 평가 검토 안내

질문 원본은 eval_set.json입니다. 현재 원문 14개를 01_eval_set.ipynb에서 직접 읽습니다. paraphrases와 related_queries는 데이터에 보존하지만 현재 실행 목록에는 확장하지 않습니다.
기존 gold_sources·must_include·must_not은 검토 후보로 보존합니다. 별도 합성 질문 초안은 사용하지 않습니다.

## 먼저 확인할 것

1. 노트북의 질문 목록과 기존 근거 후보를 읽고 원하는 질문이 맞는지 확인합니다.
2. 기존 verified는 과거 조회 기록입니다. 현재 판본과 질문 조건에 적합한 정답인지 검토합니다.
3. Q10은 policy를 유지합니다. answer_with_external은 외부 정보를 찾아 답하는 기대 행동, answer_method=external_search는 답변 방법, support_status=pending_tool은 도구 연결 대기 상태입니다. 서비스 범위 밖으로 거절할 질문이 아닙니다. 검색 도구 연결 전에는 정책 답변 성능을 미측정으로 두고, 연결 후 최신 공식 자료와 기존 근거 후보·조건을 검토해 평가합니다.
4. 현재 원문 14개는 개발용입니다. 질문을 읽고 현재 성능을 살펴보는 데 독립 holdout은 필수가 아닙니다.
5. 이후 개선 성과를 최종 확인할 때 새 독립 holdout을 준비합니다. 원문과 변형은 같은 상황으로 묶습니다.
## 정답 작성

기존 질문 원본과 과거 근거 캐시를 보존하고 `private/labels_v2.json`에 검토본을 저장합니다. 이 폴더는 Git에서 제외됩니다. 별도의 사용자 관리 백업에 보관하고 복구 위치·파일 해시만 작업 기록에 남깁니다. 저장소 ignore는 접근 통제가 아니므로 agent에게 holdout 정답 읽기를 지시하지 마세요. 일상 개발에서는 dev 라벨만 별도 파일로 제공합니다.

각 질문에서 다음 항목을 채웁니다.

| 필드 | 검토 내용 |
|---|---|
| as_of | 판단 기준일(YYYY-MM-DD). 과거 사례는 그 당시 날짜 |
| expected_behavior | 답변/외부 정보로 답변/추가 질문/근거 부족 유보/범위 밖 중 하나 |
| answer_method / support_status | 필요한 답변 방법과 현재 구현 상태. 주제 category와 구분 |
| expected_sources | 문서 판본·조문·절별 근거 목록. 청크 ID 사용 금지 |
| reference_answer | 공식 근거를 확인한 정답 또는 적절한 유보·추가 질문 |
| must_include | 답변에서 반드시 충족해야 하는 조건 목록 |
| must_not_include | 잘못된 단정·예외 누락 등 금지 내용 목록 |
| reviewer / review_status | 검토자 식별자 / 검토 후에만 approved |

expected_sources의 각 원소에는 `unit_id`, `document_id`, `version`, `article`, `section`, `relevance`(0/1/2), `url`, `effective_from`, `effective_to`(종료일 미정이면 null), `checked_at`을 기록합니다. unit_id 형식은 `document_id|version|article|section`입니다. URL에는 인증키를 넣지 않습니다. 현행 페이지가 과거 판본의 근거를 대신하지 않도록 본문과 부칙을 확인합니다.

`null`은 미검토, `[]`는 검토 결과 해당 항목 없음입니다. 답변 불가라서 정답 근거가 없더라도 기대 행동과 금지할 단정은 기록합니다. `validate_eval_set(..., ready=True)`는 필수 필드 완결도만 검사하며 법률 판단·판본·URL 내용의 정확성을 보증하지 않습니다.

## 사람 채점표

[평가 규약](../evaluation_protocol.md)의 1·3·5점 기준을 사용합니다. 실제 Before 답변이 확보되면 dev 원문 질문 중 최대 10개부터 보정합니다. 답변이 아직 없으므로 현재 보정 완료 수는 0입니다. 순위나 모델명은 보지 않고 답변을 읽은 뒤 이유를 한 문장으로 적습니다.

`blind_review`의 반환값 중 첫 번째는 검토표, 두 번째는 관리자만 보는 복원 키입니다. 검토자는 키를 열지 않습니다. 사용자 혼자 관리와 채점을 함께 하면 완전한 블라인드를 보장하지 못한다는 한계를 보고합니다. 모든 사람 점수는 null에서 시작합니다.

| 별도 판정 목록 | True의 의미 | 집계 |
|---|---|---|
| context_useful | 전달된 문맥 단위가 질문에 유용함 | Context Precision |
| required_evidence_covered | 필수 근거 단위가 문맥에 있음 | Context Recall |
| claims_supported | 검증 가능한 주장이 제공 문맥에 지지됨 | Faithfulness |
| requirements_met | 검토된 정답 조건을 충족함 | Correctness |
| citation_links_supported | 해당 인용이 연결된 주장을 지지함 | Citation Correctness |
| claims_with_valid_citation | 근거 필요 주장에 지지되는 인용이 있음 | Citation Coverage |
| inappropriate_certainty | 답변 불가 항목을 부적절하게 단정함 | 답변 불가 항목만의 오류율 |
| unnecessary_refusal | 정상 질문을 불필요하게 거절함 | 정상 항목만의 오류율 |

각 목록을 `reviewed_rate`에 따로 넣습니다. 판정 중 하나라도 미검토면 점수는 null입니다. 분모·검토 수를 함께 보고합니다. 인용 없음은 인용 정확성의 분모 0이지만, 출처가 필요한 주장이 있으면 그 주장의 coverage 판정은 False입니다. 문맥에 충실하더라도 오래된 법령을 쓰면 correctness가 낮을 수 있습니다.

심각한 오류, 판본 정확성, 기준일 유효성, 링크 형식, 실제 내용 지지, 예외 누락, 필요한 추가 질문, Before 대비 회귀를 별도 기록합니다. 심각한 오류는 평균 점수와 관계없이 전부 검토합니다. LLM 평가를 나중에 사용하면 사람과의 불일치·이유·최종 판정을 남깁니다.

## 고정과 사용

- dev 10개 채점 보정 후 규약 버전을 고정합니다. holdout 20개는 최종 모델 선택 후 한 번 평가하고 전부 사람이 검토합니다.
- 공개 질문을 보고 튜닝했다면 해당 holdout을 사용자 작성 독립 질문으로 교체합니다. 기존 질문은 이미 개발 중 확인한 자료이므로 독립 holdout으로 주장하지 않습니다.
- 비교 입력은 같은 질문 ID의 Before/After를 한 행에 넣습니다. 누락된 쪽을 0점으로 바꾸지 말고 null로 남깁니다. 실패 요청은 실패율에도 별도로 집계합니다.
- paired_comparison은 질문 차이·유효 질문 수·상황 수·제외 수와 상황별 동등 가중 평균을 반환합니다. 95% 구간은 상황을 복원 추출하는 percentile bootstrap(2,000회, seed=42)입니다. 상황 1개는 구간을 만들지 않습니다. 이는 작은 표본의 대표성을 보장하지 않습니다.
- 단계 1의 종료에는 사용자 정답 검토가 필요합니다. 현재는 기존 질문 연결·계산 검증까지 완료했으며 RAG 점수는 없습니다.

현재 evaluation.reasoning/factuality/retrieval/response의 세부 조건은 검토용 데이터입니다. evaluation.py가 이 구조 전체를 자동 채점하는 것은 아닙니다. 데이터의 정답 수정 내용을 이번 Git 반영에서 법률적으로 재검증하지 않았습니다.
