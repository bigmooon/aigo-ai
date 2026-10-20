# Generated from notebooks/redesign/03_metadata_and_ingest.ipynb; edit the notebook, not this file.
import asyncio
import json
import hashlib
import re
import time
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit


def sha256(data):
    """bytes를 받아 재현 확인용 SHA-256 문자열을 반환합니다."""
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    """JSON 값을 키 순서와 공백이 고정된 UTF-8 bytes로 반환합니다."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def valid_source(url):
    """캐시 URL이 인증정보 없는 국가법령정보 원문 주소 형식인지 반환합니다."""
    parts = urlsplit(url or "")
    if parts.scheme != "https" or parts.netloc not in {"law.go.kr", "www.law.go.kr"}:
        return False
    if parts.fragment or parts.username or parts.password:
        return False
    query = parse_qs(parts.query, keep_blank_values=True)
    if unquote(parts.path).startswith("/법령/"):
        return not query
    names = {"/LSW/precInfoP.do": "precSeq", "/LSW/expcInfoP.do": "expcSeq"}
    key = names.get(parts.path)
    return bool(key and set(query) == {key} and len(query[key]) == 1 and query[key][0].isdigit())


def normalize_document(row):
    """캐시 한 행을 본문·판본·날짜·출처가 분리된 준비 문서로 반환합니다."""
    kind = row["doc_type"]
    if kind not in {"law", "prec", "expc"}:
        raise ValueError("unsupported_document_type")
    text = row.get("text") or "\n\n".join(f"{k}\n{v}" for k, v in row.get("fields", {}).items() if v)
    if not text.strip():
        raise ValueError("empty_document")
    if not valid_source(row.get("url")):
        raise ValueError("invalid_source_url")
    for key in ("valid_from", "valid_to"):
        if row.get(key):
            date.fromisoformat(row[key])
    if row.get("valid_from") and row.get("valid_to") and row["valid_from"] > row["valid_to"]:
        raise ValueError("reversed_validity")
    version = row.get("version_key") or None
    identity = [kind, row.get("key"), version, row["url"]]
    return {
        "document_id": sha256(json_bytes(identity)), "body_sha256": sha256(text.encode("utf-8")),
        "doc_type": kind, "source_key": row.get("key"), "version": version,
        "title": row.get("title"), "article": row.get("article"), "law_name": row.get("law_name"),
        "law_source_id": row.get("law_source_id"),
        "effective_from": row.get("valid_from") if kind == "law" else None,
        "effective_to": row.get("valid_to") if kind == "law" else None,
        "decision_date": row.get("valid_from") if kind != "law" else None,
        "url": row["url"], "text": text,
        "date_provenance": "inherited_cache_not_reverified",
    }


def prepare_corpus(rows):
    """캐시 행 목록에서 결정론적 문서 목록과 누락·중복 통계를 반환합니다."""
    docs = [normalize_document(row) for row in rows]
    docs.sort(key=lambda d: (d["document_id"], d["body_sha256"]))
    pairs = Counter((d["document_id"], d["body_sha256"]) for d in docs)
    ids = Counter(d["document_id"] for d in docs)
    return docs, {
        "documents": len(docs), "types": dict(sorted(Counter(d["doc_type"] for d in docs).items())),
        "duplicate_source_version_keys": sum(n - 1 for n in Counter(r.get("version_key") for r in rows).values() if n > 1),
        "exact_duplicate_rows": sum(n - 1 for n in pairs.values() if n > 1),
        "identity_conflicts": sum(len({d["body_sha256"] for d in docs if d["document_id"] == key}) > 1 for key, n in ids.items() if n > 1),
        "missing_version": sum(d["version"] is None for d in docs),
        "missing_applicable_date": sum(not (d["effective_from"] or d["decision_date"]) for d in docs),
        "law_alias_urls": sum(d["doc_type"] == "law" and "/(" not in unquote(d["url"]) for d in docs),
    }


def write_once(path, content):
    """동일한 파일은 재사용하고 다른 내용은 덮어쓰지 않습니다."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError("snapshot_content_changed")
    else:
        with path.open("xb") as handle:
            handle.write(content)


def service_payload(doc):
    """준비 문서를 기존 서비스의 한국어 payload 필드로 변환합니다."""
    kind = doc["doc_type"]
    query = parse_qs(urlsplit(doc["url"]).query)
    source_id = (query.get("precSeq") or query.get("expcSeq") or [None])[0]
    # 법령ID는 기존 검색 API 캐시에서 확인한 값만 사용합니다.
    if kind == "law":
        source_id = doc.get("law_source_id")
        if not source_id:
            raise ValueError("law_source_id_required_for_ingest")
    return {
        "doc_type": {"law": "법령", "prec": "판례", "expc": "법령해석례"}[kind],
        "title": doc["law_name"] if kind == "law" else doc["title"],
        "source_id": source_id, "chunk_id": doc["source_key"].removeprefix("해석례|") if kind == "expc" else doc["document_id"], "text": doc["text"],
        "조문번호": doc["article"], "사건번호": doc["source_key"].removeprefix("판례|") if kind == "prec" else None,
        "document_id": doc["document_id"], "version": doc["version"], "body_sha256": doc["body_sha256"],
        "effective_from": doc["effective_from"], "effective_to": doc["effective_to"],
        "decision_date": doc["decision_date"], "source_url": doc["url"],
    }

async def collect_answer(question, stream, trace):
    """질문과 SSE 함수·관찰 dict에서 답변/인용/실패/지연 기록을 반환합니다."""
    started = time.perf_counter()
    result = {"id": question["id"], "question": question["question"], "status": "failed",
              "answer": "", "citations": [], "events": [], "error": None,
              "ttft_ms": None, "total_ms": None, "usage": "unknown", "cost": "unknown"}
    ended = False
    try:
        async for event in stream(question["question"]):
            elapsed = (time.perf_counter() - started) * 1000
            result["events"].append({"elapsed_ms": elapsed, **event})
            kind, data = event["event"], event["data"]
            if kind == "token" and data.get("delta"):
                if result["ttft_ms"] is None:
                    result["ttft_ms"] = elapsed
                result["answer"] += data["delta"]
            elif kind == "citation":
                result["citations"].append(data)
            elif kind == "error":
                result["error"] = data.get("code", "SERVICE_ERROR")
            elif kind == "message_end":
                ended = True
    except asyncio.CancelledError:
        # 호출자가 취소한 경우 성공으로 저장하지 않으며 배치도 중단시킵니다.
        raise
    except Exception as exc:
        # 예외 본문에 URL 인증키가 섞일 수 있어 타입만 기록합니다.
        result["error"] = type(exc).__name__
    result["total_ms"] = (time.perf_counter() - started) * 1000
    if not result["error"]:
        result["error"] = None if ended and result["answer"].strip() else ("EMPTY_RESPONSE" if ended else "INCOMPLETE_STREAM")
    result["status"] = "ok" if result["error"] is None else "failed"
    result["trace"] = dict(trace)
    return result


def save_trace(path, record):
    """한 질문 결과를 새 JSON 파일로 저장합니다. 기존 결과 덮어쓰기는 금지합니다."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)


async def run_current_service(question):
    """승인된 실행 환경에서 기존 stream_chat을 관찰하여 한 질문 결과를 반환합니다."""
    from unittest.mock import patch
    from app.services import chat_service
    from app.graph.nodes.generator import _build_messages
    trace = {"retrieved_docs": None, "generation_messages": None, "preformat_ms": None}
    original_preformat = chat_service.run_preformat
    original_formatter = chat_service.stream_formatter

    def observe_preformat(query):
        started = time.perf_counter()
        try:
            state = original_preformat(query)
            trace["retrieved_docs"] = state.get("retrieved_docs", [])
            trace["retrieval_passed"] = state.get("retrieval_passed")
            trace["user_query"] = state.get("user_query")
            return state
        finally:
            trace["preformat_ms"] = (time.perf_counter() - started) * 1000

    def observe_formatter(state):
        trace["generation_messages"] = [{"type": m.type, "content": m.content} for m in _build_messages(state)]
        yield from original_formatter(state)

    # 전역 계측 충돌을 피하도록 이 노트북은 질문을 병렬 실행하지 않습니다.
    with patch.object(chat_service, "run_preformat", observe_preformat), patch.object(chat_service, "stream_formatter", observe_formatter):
        return await collect_answer(question, chat_service.stream_chat, trace)

def stop_runpod_at(pod_id, stop_at):
    """지정한 Unix 시각에 해당 Pod만 중지 요청하고 API의 기대 상태를 반환합니다."""
    import os
    import requests
    if not re.fullmatch(r"[A-Za-z0-9_-]+", pod_id):
        raise ValueError("invalid_pod_id")
    if not 0 < stop_at < float("inf"):
        raise ValueError("invalid_deadline")
    headers = {"Authorization": "Bearer " + os.environ["RUNPOD_API_KEY"]}
    url = "https://rest.runpod.io/v1/pods/" + pod_id
    # 노트북 커널과 독립된 프로세스에서 대기하도록 함수 전체를 분리합니다.
    while time.time() < stop_at:
        time.sleep(min(30, max(0, stop_at - time.time())))
    for attempt in range(3):
        try:
            response = requests.post(url + "/stop", headers=headers, timeout=15)
            response.raise_for_status()
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            if response.json().get("desiredStatus") == "EXITED":
                return "stop_requested"
        except (requests.RequestException, ValueError):
            pass  # 응답 본문·예외 객체에는 비밀정보가 있을 수 있어 출력하지 않습니다.
        if attempt < 2:
            time.sleep(5)
    raise RuntimeError("Pod 중지 확인 실패: RunPod 콘솔에서 즉시 확인하세요")
