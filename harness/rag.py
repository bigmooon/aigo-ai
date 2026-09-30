r"""
aigo 하네스 — RAG 검색 구성. **에이전트가 수정하는 유일한 파일.**

karpathy/autoresearch 의 train.py 역할. 청킹, 토큰화, 검색 방식, 시점(as_of) 처리,
재순위화 등 무엇이든 바꿔도 되지만 prepare.py 의 평가 규칙과 코퍼스는 건드리지 않는다.

실행:  uv run harness/rag.py > run.log 2>&1
결과:  grep "^recall@5:\|^mrr@5:\|^asof_acc:" run.log

기준선: 조문=1청크, 판례·해석례=요약 1청크 + 본문 창 청크, 한글 문자 bigram BM25,
        질문에서 'YYYY년 M월'을 뽑아 그 시점에 시행 중인 조문 판본만 검색.
"""

from __future__ import annotations

import math
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare import CORPUS_VERSION, K, TIME_BUDGET, evaluate, load_corpus  # noqa: E402

# ── 실험 변수 ─────────────────────────────────────────────
BODY_WINDOW = 800      # 판례·해석례 본문 창 크기(문자)
BODY_STRIDE = 600
BM25_K1 = 1.5
BM25_B = 0.75
TOP_N = 50             # evaluate 에 넘길 후보 수 (중복 문서 제거 전)


# ── 청킹 ──────────────────────────────────────────────────
def chunk(doc: dict) -> list[dict]:
  base = {k: doc[k] for k in ("key", "version_key", "url", "valid_from", "valid_to", "doc_type")}
  if doc["doc_type"] == "law":
    return [{**base, "text": f"{doc['title']}\n{doc['text']}"}]

  f = doc["fields"]
  if doc["doc_type"] == "prec":
    head = "\n".join(filter(None, [doc["title"], f["판시사항"], f["판결요지"], f["참조조문"]]))
    body = re.split(r"【이\s*유】", f["판례내용"])[-1]
  else:
    head = "\n".join(filter(None, [doc["title"], f["질의요지"], f["회답"]]))
    body = f["이유"]

  chunks = [{**base, "text": head}]
  for i in range(0, max(len(body) - BODY_WINDOW, 0) + 1, BODY_STRIDE):
    piece = body[i:i + BODY_WINDOW]
    if piece.strip():
      chunks.append({**base, "text": f"{doc['title']}\n{piece}"})
  return chunks


# ── 토큰화 · BM25 ─────────────────────────────────────────
def tokenize(text: str) -> list[str]:
  tokens = []
  for word in re.findall(r"[가-힣]+|[a-zA-Z]+|\d+", text):
    if re.match(r"[가-힣]", word) and len(word) > 1:
      tokens += [word[i:i + 2] for i in range(len(word) - 1)]
    else:
      tokens.append(word.lower())
  return tokens


class BM25:
  def __init__(self, docs: list[list[str]]):
    self.n = len(docs)
    self.len = [len(d) for d in docs]
    self.avg = sum(self.len) / self.n
    self.postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for i, d in enumerate(docs):
      for t, c in Counter(d).items():
        self.postings[t].append((i, c))

  def scores(self, query: list[str]) -> dict[int, float]:
    out: dict[int, float] = defaultdict(float)
    for t in set(query):
      plist = self.postings.get(t)
      if not plist:
        continue
      idf = math.log(1 + (self.n - len(plist) + 0.5) / (len(plist) + 0.5))
      for i, c in plist:
        denom = c + BM25_K1 * (1 - BM25_B + BM25_B * self.len[i] / self.avg)
        out[i] += idf * c * (BM25_K1 + 1) / denom
    return out


# ── 시점 처리 ─────────────────────────────────────────────
def extract_as_of(query: str) -> str | None:
  """질문의 첫 'YYYY년 (M월)' 을 기준 시점으로 본다. 없으면 None(= 오늘)."""
  m = re.search(r"(19|20)(\d{2})년\s*(?:(\d{1,2})월)?", query)
  if not m:
    return None
  return f"{m.group(1)}{m.group(2)}-{int(m.group(3) or 1):02d}-01"


def in_force(chunk: dict, day: str) -> bool:
  return (chunk["valid_from"] or "0000") <= day and (chunk["valid_to"] is None or day <= chunk["valid_to"])


# ── 색인 · 검색 ───────────────────────────────────────────
t0 = time.time()
CHUNKS = [c for d in load_corpus() for c in chunk(d)]
INDEX = BM25([tokenize(c["text"]) for c in CHUNKS])
print(f"corpus {CORPUS_VERSION}: {len(CHUNKS)} chunks indexed in {time.time() - t0:.1f}s")

TODAY = date.today().isoformat()


def retrieve(query: str) -> list[dict]:
  day = extract_as_of(query) or TODAY
  scored = INDEX.scores(tokenize(query))
  ranked = sorted(scored.items(), key=lambda x: -x[1])
  hits = []
  for i, _ in ranked:
    c = CHUNKS[i]
    if c["doc_type"] == "law" and not in_force(c, day):
      continue
    hits.append(c)
    if len(hits) >= TOP_N:
      break
  return hits


if __name__ == "__main__":
  metrics = evaluate(retrieve, split="dev")
  elapsed = time.time() - t0
  print("---")
  for name, value in metrics.items():
    print(f"{name}: {value:.6f}")
  print(f"total_seconds: {elapsed:.1f}")
  print(f"k: {K}")
  if elapsed > TIME_BUDGET:
    print(f"WARNING: time budget {TIME_BUDGET}s exceeded")
