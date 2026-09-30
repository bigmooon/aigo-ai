r"""
aigo 하네스 — 고정 평가 하네스. **에이전트는 이 파일을 수정하지 않는다.**

karpathy/autoresearch 의 prepare.py 역할을 이 프로젝트에 맞춘 것:
  - 코퍼스 스냅샷 준비 (국가법령정보 공동활용 API → 로컬 캐시, 시점별 법령 판본 포함)
  - 고정 평가 (평가셋 dev/test 분할, 정답 근거 키, Recall@K · MRR@K · 시점 정확도 · 링크 형식)
  - 근거 링크 생성 규칙 (사용자에게 노출되는 law.go.kr 퍼머링크, 인증키 미포함)

사용법:
  uv run harness/prepare.py                 # 코퍼스 스냅샷 준비 (최초 1회, 이후 캐시 사용)
  uv run harness/prepare.py --check-links   # 코퍼스 링크 표본을 실제로 열어 제목 검증

rag.py 에서:
  from prepare import K, TIME_BUDGET, CORPUS_VERSION, load_corpus, evaluate
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote

import requests
from dotenv import dotenv_values

# ── 고정 상수 ─────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = ROOT / "notebooks" / "redesign" / "eval" / "eval_set.json"
CACHE_DIR = Path(os.environ.get("AIGO_HARNESS_CACHE") or Path.home() / ".cache" / "aigo-harness")

CORPUS_VERSION = "v1-seed"  # 소스 목록(SOURCES)이 바뀌면 올린다. 버전이 다른 결과끼리는 비교하지 않는다.
TIME_BUDGET = 600           # rag.py 1회 실행(색인 + 평가) 제한 시간(초)
K = 5                       # Recall@K, MRR@K 의 K

# 2단계(데이터 소스 조사) 전까지 쓰는 시드 소스. history=True 인 법령은 HISTORY_SINCE 이후 모든 시행 판본을 받는다.
SOURCES: dict[str, Any] = {
  "laws": [
    {"name": "주택임대차보호법", "history": True},
    {"name": "주택임대차보호법 시행령", "history": True},
    {"name": "부동산 거래신고 등에 관한 법률", "history": True},
    {"name": "부동산 거래신고 등에 관한 법률 시행령", "history": True},
    {"name": "민법", "history": False},
    {"name": "형법", "history": False},
    {"name": "공동주택관리법", "history": False},
    {"name": "공동주택 층간소음의 범위와 기준에 관한 규칙", "history": False},
  ],
  "prec_queries": ["임대차", "임차보증금", "전세", "가계약금", "계약갱신"],
  "expc_queries": ["임대차", "주택임대차", "임차인"],
}
HISTORY_SINCE = "20000101"
MAX_PER_QUERY = 500

LAW_SITE = "https://www.law.go.kr"
_SEARCH_URL = f"{LAW_SITE}/DRF/lawSearch.do"
_SERVICE_URL = f"{LAW_SITE}/DRF/lawService.do"


# ── 법령 API (디스크 캐시) ────────────────────────────────
_session = requests.Session()


def _oc() -> str:
  oc = os.environ.get("OC") or dotenv_values(ROOT / ".env").get("OC")
  if not oc:
    sys.exit("법령 API 인증키 OC 가 필요합니다 (.env 또는 환경변수).")
  return oc


def _api(url: str, **params) -> dict:
  """캐시가 있으면 캐시를, 없으면 API 를 호출한다. 캐시 키에는 인증키를 넣지 않는다."""
  key = hashlib.sha1(json.dumps([url, params], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
  path = CACHE_DIR / "api" / f"{key}.json"
  if path.exists():
    return json.loads(path.read_text(encoding="utf-8"))
  for attempt in range(4):
    try:
      resp = _session.get(url, params={"OC": _oc(), "type": "JSON", **params}, timeout=60)
      resp.raise_for_status()
      data = resp.json()
      break
    except (requests.RequestException, ValueError):
      if attempt == 3:
        raise
      time.sleep(2 ** attempt)
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
  time.sleep(0.2)
  return data


def _as_list(x) -> list:
  if x is None:
    return []
  return x if isinstance(x, list) else [x]


def _join(x) -> str:
  if isinstance(x, list):
    return "\n".join(_join(v) for v in x)
  return str(x or "").strip()


def _clean(s: str) -> str:
  s = re.sub(r"<br\s*/?>", "\n", s or "")
  s = re.sub(r"<[^>]+>", "", s)
  return re.sub(r"[ \t]+", " ", s).strip()


def _iso(yyyymmdd: str | None) -> str | None:
  s = re.sub(r"\D", "", yyyymmdd or "")
  return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if len(s) == 8 else None


# ── 근거 링크 규칙 (사용자 노출용, 인증키 없음) ────────────
def article_label(jo_no: str | int, branch: str | int | None = None) -> str:
  label = f"제{int(jo_no)}조"
  if branch and int(branch):
    label += f"의{int(branch)}"
  return label


def jo_to_label(jo: str) -> str:
  """평가셋의 6자리 JO('000602') → '제6조의2'."""
  return article_label(jo[:4], jo[4:])


def law_url(law_name: str, label: str | None = None, promulgation: tuple[str, str] | None = None) -> str:
  """현행: /법령/{법령명}/제N조 · 특정 판본: /법령/{법령명}/({공포번호},{공포일자})/제N조"""
  parts = [LAW_SITE, quote("법령"), quote(law_name)]
  if promulgation:
    parts.append(f"({promulgation[0]},{promulgation[1]})")
  if label:
    parts.append(quote(label))
  return "/".join(parts)


def prec_url(prec_seq: str) -> str:
  return f"{LAW_SITE}/LSW/precInfoP.do?precSeq={prec_seq}"


def expc_url(expc_seq: str) -> str:
  return f"{LAW_SITE}/LSW/expcInfoP.do?expcSeq={expc_seq}"


_URL_PATTERNS = [
  re.compile(r"^https://www\.law\.go\.kr/%EB%B2%95%EB%A0%B9/[^?#]+$"),  # /법령/...
  re.compile(r"^https://www\.law\.go\.kr/LSW/(prec|expc)InfoP\.do\?(prec|expc)Seq=\d+$"),
]


def link_format_ok(url: str | None) -> bool:
  """퍼머링크 형식이고 인증키(OC)가 섞이지 않았는가."""
  if not url or "OC=" in url or "/DRF/" in url:
    return False
  return any(p.match(url) for p in _URL_PATTERNS)


# ── 코퍼스 스냅샷 ─────────────────────────────────────────
def _find_law(name: str) -> dict:
  res = _api(_SEARCH_URL, target="law", query=name, display=100)["LawSearch"]
  for row in _as_list(res.get("law")):
    if row["법령명한글"] == name:
      return row
  raise ValueError(f"법령을 찾지 못함: {name}")


def _law_versions(name: str) -> list[dict]:
  """시행일 기준 판본 목록(오래된 순). 시행예정 판본 포함."""
  res = _api(_SEARCH_URL, target="eflaw", query=name, display=100)["LawSearch"]
  rows = [r for r in _as_list(res.get("law")) if r["법령명한글"] == name and r["시행일자"] >= HISTORY_SINCE]
  return sorted(rows, key=lambda r: (r["시행일자"], r["공포일자"]))


def _article_units(body: dict) -> list[dict]:
  return [u for u in _as_list(body.get("조문", {}).get("조문단위")) if u.get("조문여부") == "조문"]


def _article_text(u: dict) -> str:
  lines = [_join(u.get("조문내용"))]
  for hang in _as_list(u.get("항")):
    lines.append(_join(hang.get("항내용")))
    for ho in _as_list(hang.get("호")):
      lines.append("  " + _join(ho.get("호내용")))
      for mok in _as_list(ho.get("목")):
        lines.append("    " + _join(mok.get("목내용")))
  return "\n".join(line for line in lines if line)


def _law_docs(spec: dict) -> list[dict]:
  """법령 → 조문 문서. history=True 면 조문 텍스트가 바뀐 지점마다 판본 문서를 만들고 유효기간을 붙인다."""
  name = spec["name"]
  if spec["history"]:
    versions = [
      (v["시행일자"], v["공포일자"], v["공포번호"],
       _api(_SERVICE_URL, target="eflaw", MST=v["법령일련번호"], efYd=v["시행일자"])["법령"])
      for v in _law_versions(name)
    ]
  else:
    cur = _find_law(name)
    body = _api(_SERVICE_URL, target="law", ID=cur["법령ID"])["법령"]
    info = body["기본정보"]
    versions = [(info["시행일자"], info["공포일자"], info["공포번호"], body)]

  docs: list[dict] = []
  open_docs: dict[str, dict] = {}  # 조문 라벨 → 현재 열려 있는 판본 문서
  for ef_date, pub_date, pub_no, body in versions:
    seen = set()
    for u in _article_units(body):
      label = article_label(u["조문번호"], u.get("조문가지번호"))
      seen.add(label)
      text = _article_text(u)
      valid_from = _iso(u.get("조문시행일자")) or _iso(ef_date)
      prev = open_docs.get(label)
      if prev and prev["text"] == text:
        continue
      if prev:
        prev["valid_to"] = (date.fromisoformat(valid_from) - timedelta(days=1)).isoformat()
      doc = {
        "doc_type": "law",
        "key": f"{name}|{label}",
        "version_key": f"{name}|{label}@{valid_from}",
        "title": f"{name} {label}({_join(u.get('조문제목'))})",
        "text": text,
        "law_name": name,
        "article": label,
        "valid_from": valid_from,
        "valid_to": None,
        "history": spec["history"],  # False 면 현행 판본만 있으므로 과거 시점 질문에는 근거가 불완전하다
        "공포일자": _iso(pub_date),
        "url": law_url(name, label, (pub_no, pub_date) if spec["history"] else None),
      }
      open_docs[label] = doc
      docs.append(doc)
    # 이 판본에서 사라진 조문은 직전 날짜로 닫는다
    for label, prev in list(open_docs.items()):
      if label not in seen and prev["valid_to"] is None:
        prev["valid_to"] = (date.fromisoformat(_iso(ef_date)) - timedelta(days=1)).isoformat()
        del open_docs[label]
  return docs


def _search_ids(target: str, root: str, query: str, id_field: str) -> list[str]:
  ids: list[str] = []
  page = 1
  while len(ids) < MAX_PER_QUERY:
    res = _api(_SEARCH_URL, target=target, query=query, display=100, page=page)[root]
    rows = _as_list(res.get(target))
    ids += [r[id_field] for r in rows]
    if len(rows) < 100:
      break
    page += 1
  return ids[:MAX_PER_QUERY]


def _prec_docs(queries: list[str]) -> list[dict]:
  ids = dict.fromkeys(i for q in queries for i in _search_ids("prec", "PrecSearch", q, "판례일련번호"))
  docs = []
  for seq in ids:
    d = _api(_SERVICE_URL, target="prec", ID=seq).get("PrecService")
    if not d:
      continue
    docs.append({
      "doc_type": "prec",
      "key": f"판례|{d.get('사건번호')}",
      "version_key": f"판례|{d.get('사건번호')}",
      "title": f"{d.get('법원명', '')} {d.get('사건번호')} {d.get('사건명', '')}".strip(),
      "fields": {k: _clean(d.get(k, "")) for k in ("판시사항", "판결요지", "참조조문", "참조판례", "판례내용")},
      "선고일자": _iso(d.get("선고일자")),
      "valid_from": _iso(d.get("선고일자")),
      "valid_to": None,
      "url": prec_url(seq),
    })
  return docs


def _expc_docs(queries: list[str]) -> list[dict]:
  ids = dict.fromkeys(i for q in queries for i in _search_ids("expc", "Expc", q, "법령해석례일련번호"))
  docs = []
  for seq in ids:
    d = _api(_SERVICE_URL, target="expc", ID=seq).get("ExpcService")
    if not d:
      continue
    docs.append({
      "doc_type": "expc",
      "key": f"해석례|{d.get('안건번호')}",
      "version_key": f"해석례|{d.get('안건번호')}",
      "title": f"법령해석례 {d.get('안건번호')} {d.get('안건명', '')}".strip(),
      "fields": {k: _clean(d.get(k, "")) for k in ("질의요지", "회답", "이유")},
      "valid_from": _iso(d.get("회신일자")),
      "valid_to": None,
      "url": expc_url(seq),
    })
  return docs


def _corpus_path() -> Path:
  return CACHE_DIR / f"corpus_{CORPUS_VERSION}.jsonl"


def build_corpus() -> Path:
  docs: list[dict] = []
  for spec in SOURCES["laws"]:
    law = _law_docs(spec)
    print(f"  법령 {spec['name']}: {len(law)} 조문 판본")
    docs += law
  prec = _prec_docs(SOURCES["prec_queries"])
  print(f"  판례: {len(prec)}")
  expc = _expc_docs(SOURCES["expc_queries"])
  print(f"  해석례: {len(expc)}")
  docs += prec + expc
  path = _corpus_path()
  path.parent.mkdir(parents=True, exist_ok=True)
  with path.open("w", encoding="utf-8") as f:
    for d in docs:
      f.write(json.dumps(d, ensure_ascii=False) + "\n")
  manifest = {
    "corpus_version": CORPUS_VERSION,
    "built": date.today().isoformat(),
    "sources": SOURCES,
    "history_since": HISTORY_SINCE,
    "n_docs": len(docs),
    "sha1": hashlib.sha1(path.read_bytes()).hexdigest(),
  }
  (CACHE_DIR / f"manifest_{CORPUS_VERSION}.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
  return path


def load_corpus() -> list[dict]:
  path = _corpus_path()
  if not path.exists():
    sys.exit(f"코퍼스가 없습니다. 먼저 `uv run harness/prepare.py` 를 실행하세요. ({path})")
  with path.open(encoding="utf-8") as f:
    return [json.loads(line) for line in f]


# ── 평가 ──────────────────────────────────────────────────
def load_eval() -> list[dict]:
  return json.loads(EVAL_PATH.read_text(encoding="utf-8"))["items"]


def _in_force(doc: dict, day: str) -> bool:
  return (doc["valid_from"] or "0000") <= day and (doc["valid_to"] is None or day <= doc["valid_to"])


def gold_keys(item: dict, corpus_index: dict[str, list[dict]]) -> set[str]:
  """정답 근거 키. 시점 질문(as_of)은 그 시점에 시행 중인 판본의 version_key,
  시행 중인 판본이 없으면(아직 시행 전) 가장 먼저 시행되는 판본의 version_key 를 정답으로 한다."""
  keys: set[str] = set()
  for src in item["gold_sources"]:
    if src["type"] == "prec" and src.get("case_no"):
      keys.add(f"판례|{src['case_no']}")
    elif src["type"] == "law":
      jos = [a["jo"] for a in src.get("articles", [])] or ([src["jo"]] if src.get("jo") else [])
      for jo in jos:
        base = f"{src['law_name']}|{jo_to_label(jo)}"
        if not item.get("as_of"):
          keys.add(base)
          continue
        versions = sorted(corpus_index.get(base, []), key=lambda d: d["valid_from"] or "")
        hit = next((d for d in versions if _in_force(d, item["as_of"])), None)
        hit = hit or next((d for d in versions if (d["valid_from"] or "") > item["as_of"]), None)
        keys.add(hit["version_key"] if hit else base + "@?")
  return keys


def queries_for(item: dict, split: str) -> list[str]:
  """dev = 변형 질문(에이전트가 반복 최적화), test = 원문 질문(사람이 마일스톤에서만 실행)."""
  return item["variants"] if split == "dev" else [item["question"]]


def evaluate(retrieve: Callable[[str], list[dict]], split: str = "dev") -> dict[str, float]:
  """retrieve(query) → 순위순 hit 리스트. 각 hit 는 코퍼스 문서의 key, version_key, url 을 가져야 한다."""
  assert split in ("dev", "test")
  corpus_index: dict[str, list[dict]] = {}
  for d in load_corpus():
    corpus_index.setdefault(d["key"], []).append(d)

  recall, rr, asof, links = [], [], [], []
  for item in load_eval():
    gold = gold_keys(item, corpus_index)
    if not gold:
      continue  # 범위 밖·외부 소스·용어 사전 전용 항목은 검색 평가에서 제외
    time_item = bool(item.get("as_of"))
    for q in queries_for(item, split):
      hits = retrieve(q)
      ranked, seen = [], set()
      for h in hits:  # 같은 문서의 여러 청크는 한 번만 센다
        k = h["version_key"] if time_item else h["key"]
        if k not in seen:
          seen.add(k)
          ranked.append((k, h))
      top = ranked[:K]
      rank = next((i + 1 for i, (k, _) in enumerate(top) if k in gold), None)
      recall.append(1.0 if rank else 0.0)
      rr.append(1.0 / rank if rank else 0.0)
      links += [1.0 if link_format_ok(h.get("url")) else 0.0 for _, h in top]
      if time_item:
        asof.append(1.0 if rank else 0.0)

  mean = lambda xs: sum(xs) / len(xs) if xs else float("nan")
  return {
    f"recall@{K}": mean(recall),
    f"mrr@{K}": mean(rr),
    "asof_acc": mean(asof),
    "link_ok": mean(links),
    "n_queries": float(len(recall)),
  }


# ── 링크 실검증 ───────────────────────────────────────────
def check_links(n: int = 30, seed: int = 0) -> None:
  """코퍼스에서 표본을 뽑아 실제 페이지 제목을 확인한다.
  주의: law.go.kr 은 없는 페이지도 HTTP 200 '오류페이지'로 응답하므로 상태 코드가 아닌 <title> 로 판정한다."""
  docs = load_corpus()
  random.Random(seed).shuffle(docs)
  bad = 0
  for d in docs[:n]:
    html = _session.get(d["url"], timeout=30).text
    m = re.search(r"<title>([^<]*)", html)
    title = m.group(1) if m else ""
    ok = bool(title) and "오류" not in title
    bad += not ok
    print(f"{'OK ' if ok else 'BAD'} {d['version_key'][:40]:40s} {title[:40]}")
  print(f"링크 {n}개 중 실패 {bad}개")


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--check-links", action="store_true")
  args = ap.parse_args()
  if args.check_links:
    check_links()
  else:
    t0 = time.time()
    print(f"코퍼스 {CORPUS_VERSION} 준비 → {CACHE_DIR}")
    path = build_corpus()
    print(f"완료: {path} ({time.time() - t0:.0f}s)")
