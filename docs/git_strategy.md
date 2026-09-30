# Git 협업 전략 문서

## 브랜치 전략

### 브랜치 구조

- `main`: 프로덕션 배포 브랜치 (직접 수정 금지)
- `{type}/{feature}`: 개인 작업 브랜치

### 브랜치 명명 규칙

```
{type}/{feature}
```

- 소문자로 작성
- feature에는 현재 자신이 하고 있는 작업을 간단하게 작성
- feature는 kebab-case(단어를 `-`로 연결), 브랜치명 전체 **25자 이내**
- 예: `feat/rag-redesign`, `fix/oc-leak`, `ci/pr-check`

---

## Fork 작업 흐름 (개인 fork 전용)

팀 저장소(`aigo-youth/aigo-ai`)에는 push하지도, PR을 올리지도 않습니다. 모든 작업은 **개인 fork 안에서** 브랜치 → PR → fork `main` 머지로 끝냅니다.
팀 저장소는 최신 코드를 받아오는 용도(fetch)로만 씁니다.

```bash
# 최초 1회: 팀 저장소를 upstream으로 등록하고 push를 막는다
git remote add upstream https://github.com/aigo-youth/aigo-ai.git
git remote set-url --push upstream no_push
gh repo set-default <github-id>/aigo-ai      # gh 명령의 기본 대상을 fork로

# 작업 시작: fork main 기준으로 브랜치 생성
git checkout main && git pull origin main
git checkout -b fix/oc-leak

# 작업 후: fork에 push하고, fork main으로 PR
git push -u origin fix/oc-leak
gh pr create --base main

# (필요할 때만) 팀 저장소의 변경을 fork main에 반영
git fetch upstream && git checkout main && git merge upstream/main && git push origin main
```

---

## 작업 흐름 (처음부터 끝까지)

> 처음 Git을 사용하는 분들을 위해 전체 흐름을 순서대로 정리했습니다.

### 1단계: 작업 시작 전 — main 최신화

새 작업을 시작하기 전에 항상 main 브랜치를 최신 상태로 가져옵니다.

```bash
git checkout main
git pull origin main
```

### 2단계: 작업 브랜치 생성

main에서 새 브랜치를 만들고 이동합니다.

```bash
git checkout -b feat/login
```

### 3단계: 작업 및 커밋

파일을 수정한 후 커밋합니다.

```bash
git add 파일명
git commit -m "feat: 로그인 기능 구현"
```

### 4단계: push 전 충돌 예방 — main 변경사항 반영

push하기 전에 다른 팀원이 main에 올린 변경사항을 내 브랜치에 반영합니다.

```bash
git checkout main
git pull origin main
git checkout feat/login
git merge main
```

### 5단계: push 전 보안 체크 (필수)

push 전에 아래 항목을 반드시 확인하세요.

#### `.env` 파일 확인

#### `.env.example` 업데이트

`.env`에 새로운 키를 추가했다면 `.env.example`도 함께 업데이트합니다.

### 6단계: 원격 브랜치에 push

```bash
git push origin feat/login
```

### 7단계: Pull Request 생성

GitHub에서 PR을 생성합니다.

- base: `main` ← compare: `feat/login`
- PR 템플릿에 맞게 내용 작성
- Reviewers에 팀원 최소 1명 지정 (1인 작업 시 생략 가능, 아래 PR 규칙 참고)

### 8단계: 리뷰 반영 및 Merge

- 리뷰 요청사항을 반영해 커밋 후 push
- 승인 후 Merge

### 9단계: 브랜치 삭제 (Merge 직후 바로)

Merge 완료 후 작업 브랜치는 바로 삭제합니다. 브랜치를 오래 두면 충돌 가능성이 높아집니다.

GitHub에서 PR 완료 후 "Delete branch" 버튼 클릭, 또는:

```bash
# 원격 브랜치 삭제
git push origin --delete feat/login

# 로컬 브랜치 삭제
git checkout main
git branch -d feat/login
```

### 10단계: 다음 작업 전 main 재최신화

```bash
git checkout main
git pull origin main
```

---

## 커밋 컨벤션

### type 목록

| 타입     | 상황                          |
| -------- | ----------------------------- |
| feat     | 새로운 기능 추가              |
| fix      | 버그 수정                     |
| docs     | README, 주석 등 문서 수정     |
| refactor | 기능 변경 없이 코드 구조 개선 |
| chore    | 패키지 설치, 설정 파일 수정   |
| style    | 코드 포맷, 린트 수정          |
| perf     | 성능 개선                     |
| test     | 테스트 추가·수정              |
| ci       | CI 워크플로 수정              |

### 커밋 메시지 작성 예시

```
feat: 사용자 로그인 API 구현
fix: 회원가입 유효성 검증 오류 수정
chore: Prettier 설정 추가
docs: README에 설치 가이드 추가
```

- 커밋 메시지는 말머리(type) 제외 한글로 작성
- 제목은 50자 이내로 간결하게
- 영향 범위를 밝히고 싶으면 scope를 붙입니다: `fix(chat): ...`, `feat(rag): ...` ([Conventional Commits](https://www.conventionalcommits.org/ko/v1.0.0/))
- 본문이 필요하면 한 줄을 비우고 "무엇을, 왜" 바꿨는지 적습니다

---

## Pull Request 프로세스

### PR 생성 규칙

1. **제목 형식**: 커밋 컨벤션과 동일 (`feat:`, `fix(chat):` 등, 설명 50자 이내)
2. **Reviewers**: 팀원 최소 1명 이상의 리뷰 필수
3. **Merge 조건**: 최소 1명 이상의 Approve 필요
4. **1인 작업 예외**: 혼자 진행하는 작업은 리뷰어 없이 셀프 머지할 수 있습니다. 단, 아래를 지킵니다.
   - PR 체크(`PR check`)가 모두 통과한 뒤 머지
   - PR 본문의 체크리스트로 자체 검토를 대신함
   - 여러 사람에게 영향을 주는 변경(환경 변수·인증키, 공용 설정, 이 문서)은 PR 본문에 명시

### 자동 검사 (`.github/workflows/pr-check.yml`)

PR을 열거나 수정하면 아래 규칙을 자동으로 확인하고, 어기면 PR 체크가 실패합니다.

| 검사 | 규칙 |
|---|---|
| 브랜치명 | `{type}/{kebab-case}`, 25자 이내 |
| PR 제목 | `{type}(scope): 설명`, 설명 50자 이내 |
| `.env` | `.env.example` 외의 `.env*` 파일이 커밋되지 않음 |
| 인증키 | PR에서 추가된 줄에 법령 API 인증키(`OC=값`)가 없음 |

### Merge 후 할 일

- [ ] GitHub에서 "Delete branch" 클릭
- [ ] 로컬에서 브랜치 삭제 (`git branch -d 브랜치명`)
- [ ] `git checkout main && git pull origin main`으로 최신화

---

## 금지 사항

```
❌ main 브랜치에 직접 push
❌ 타인의 브랜치 직접 수정
❌ force push (git push -f) 사용
❌ 대용량 파일 커밋 (100MB 이상)
❌ .env 파일 커밋
❌ API 키, 비밀번호 하드코딩 (API 응답의 상세링크에도 인증키가 들어 있으니 저장 전에 제거)
❌ Merge 후 브랜치 방치
```

이 문서는 팀 상황에 맞춰 지속적으로 업데이트됩니다.
