# aigo harness — program.md

> 에이전트 운영 매뉴얼. [karpathy/autoresearch](https://github.com/karpathy/autoresearch)의 `program.md` 구조를 이 프로젝트(임대차 법령 RAG)에 맞춘 것이다.
> 사람은 이 문서와 평가셋을 관리하고, 에이전트는 `rag.py`만 고치면서 지표를 올린다.

## 구조

| 파일 | 역할 | 수정 |
|---|---|---|
| `prepare.py` | 코퍼스 스냅샷(법령 시점별 판본 포함), 고정 평가(dev/test 분할, 정답 키, 지표), 근거 링크 규칙 | **금지** |
| `rag.py` | 청킹 · 토큰화 · 검색 · 시점 처리 · 재순위화 | **이 파일만 수정** |
| `program.md` | 이 매뉴얼 | 사람만 |
| `results.tsv` | 실험 기록 (커밋하지 않음) | 에이전트가 추가 |
| `../notebooks/redesign/eval/eval_set.json` | 평가셋 | **금지** (사람이 버전을 올려 관리) |

autoresearch와 달라진 점:

- **지표**: `val_bpb` 대신 dev 질의의 **`recall@5`**(높을수록 좋음). 동점이면 `mrr@5`.
- **보호 지표**: `asof_acc`(시점 질문 정확도)와 `link_ok`(근거 링크 형식)는 **떨어지면 안 된다**. 주 지표가 올라도 보호 지표가 떨어지면 discard.
- **dev/test 분리**: 평가셋이 작아서(수십 개 질의) 반복 최적화하면 과적합된다. 에이전트는 **dev(변형 질문)만** 돌린다. test(원문 질문)는 사람이 마일스톤에서만 실행한다.
- **비용**: GPU(RunPod)를 쓰는 실험은 시간당 비용이 든다. 사람이 정한 최대 실험 횟수(기본 20회)에서 멈춘다.

## 준비 (Setup)

1. **실행 태그를 정한다.** 날짜 기반(예: `oct1`). `harness/<tag>` 브랜치가 없어야 한다.
2. **브랜치를 만든다.** `git checkout -b harness/<tag>`
3. **범위 안의 파일을 읽는다.** `harness/program.md`, `harness/prepare.py`, `harness/rag.py`, 평가셋.
4. **코퍼스를 확인한다.** `~/.cache/aigo-harness/corpus_<CORPUS_VERSION>.jsonl`이 있어야 한다. 없으면 사람에게 `uv run harness/prepare.py` 실행을 요청한다(법령 API 인증키 필요).
5. **`results.tsv`를 만든다.** 헤더 한 줄만 둔다.
6. **기준선을 먼저 돌린다.** 수정 없이 한 번 실행해 `baseline`으로 기록한다.

## 실험 루프

반복한다.

1. git 상태를 확인한다.
2. `rag.py`에 아이디어 하나를 적용한다. **한 번에 한 가지만** 바꾼다.
3. 커밋한다 (`exp: <설명>`).
4. 실행: `uv run harness/rag.py > run.log 2>&1`
5. 결과 추출: `grep "^recall@5:\|^mrr@5:\|^asof_acc:\|^link_ok:\|^total_seconds:" run.log`
6. 실패하면 `tail -n 50 run.log`로 원인을 본다. 쉽게 고칠 수 있으면 고치고, 아니면 `crash`로 기록하고 넘어간다.
7. `results.tsv`에 기록한다.
8. 판정:
   - `recall@5`가 올랐고 보호 지표가 유지되면 → **keep** (커밋 유지)
   - 같거나 나빠졌거나 보호 지표가 떨어지면 → **discard** (`git reset --hard HEAD~1`)

## results.tsv 형식

탭으로 구분한다. 쉼표는 설명에 쓸 수 있으므로 CSV를 쓰지 않는다.

```
commit	recall@5	mrr@5	asof_acc	link_ok	status	description
a1b2c3d	0.512821	0.401282	0.500000	1.000000	keep	baseline
```

- `commit`: 7자리 해시
- 지표: 소수점 6자리. crash는 `0.000000`
- `status`: `keep` / `discard` / `crash`
- `description`: 무엇을 바꿨는지 한 줄

## 제약

- **시간 예산**: 1회 실행(색인 + 평가) `TIME_BUDGET`=600초. 넘으면 그 실험은 discard.
- **패키지 설치 금지**: `pyproject.toml`에 있는 것만 쓴다. 새 모델(임베딩 등)이 필요하면 사람에게 제안만 한다.
- **평가 우회 금지**: 평가셋 문구나 정답 키를 `rag.py`에 하드코딩하지 않는다(예: 특정 질문이면 특정 조문 반환). 발견되면 그 실험 전체를 무효로 한다.
- **근거 링크**: 모든 hit는 코퍼스 문서의 `url`을 그대로 전달한다. API(DRF) 주소나 인증키(OC)를 만들어 넣지 않는다.
- **시점**: 질문에 시점이 없으면 오늘 기준 현행 판본을 쓴다. 시점이 있으면 그 시점에 시행 중인 판본을 쓰고, 아직 시행 전이면 가장 먼저 시행되는 판본을 정답으로 본다(`prepare.gold_keys` 참고).

## git 규칙

팀 규칙([`docs/git_strategy.md`](../docs/git_strategy.md))을 따르고, 하네스 전용 규칙을 더한다.

| 대상 | 규칙 |
|---|---|
| 실험 브랜치 | `harness/<tag>` (예: `harness/oct1`). 현재 작업 브랜치에서 만들고, **로컬 전용**이라 push하지 않는다 |
| 실험 커밋 | `exp: <무엇을 바꿨는지>` 한 줄 (예: `exp: 판례 본문 청크 제외`). discard되면 `git reset`으로 사라진다 |
| 결과 반영 | 실험이 끝나면 keep된 변경만 모아 `feat/…` 브랜치에 Conventional Commits로 커밋하고, PR 본문에 `results.tsv` 요약을 붙인다 |
| push | **fork(origin)에만** push한다. upstream에 직접 push하거나 force push하지 않는다 |
| 보안 | 코퍼스 캐시·API 응답에는 인증키가 들어 있으므로 저장소 밖(`~/.cache/aigo-harness`)에 둔다. 저장소에 넣을 때는 인증키를 제거한다 |

## 단순성 기준

다른 조건이 같다면 단순한 쪽이 낫다. 지표가 조금 오르는데 코드가 크게 복잡해지면 가치가 없다. 반대로 코드를 지웠는데 지표가 같거나 오르면 keep한다.

## 아이디어 예시 (막히면 여기서 고른다)

- 토큰화: 문자 bigram → 형태소, trigram 혼합, 법령명·조문번호 보존
- 청킹: 판례 요약 청크 구성(판시사항·참조조문 비중), 본문 창 크기, 조문 항 단위 분할
- 검색: BM25 파라미터, 필드 가중치, 법령명 매칭 보너스, 조문↔판례 참조 확장
- 시점: 날짜 표현 추출 개선("작년", "2020년 가을"), 시행 전 판본 포함 규칙
- (사람 승인 후) dense 임베딩 · 하이브리드 · 리랭커 — RunPod GPU 필요

막히면 코드를 고치기 전에 방법론부터 조사한다(관련 논문, 공식 문서).

## 멈추지 않는다

실험 루프를 시작한 뒤에는 계속할지 사람에게 묻지 않는다. 멈추는 조건은 다음 셋뿐이다.

- 사람이 중단한다.
- 사람이 정한 최대 실험 횟수에 도달한다.
- 코퍼스나 평가셋에 문제가 있다고 판단된다. 이때는 **고치지 말고** 멈춘 뒤 보고한다.
