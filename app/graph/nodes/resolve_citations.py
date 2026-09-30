"""검색 문서의 출처 URL을 결정론적으로 구성하는 노드.

사용자에게 노출되는 링크이므로 API(DRF) 주소나 인증키(OC)를 쓰지 않고
국가법령정보센터 퍼머링크만 사용한다:
- 판례: /LSW/precInfoP.do?precSeq={판례일련번호}
- 법령해석례: /LSW/expcInfoP.do?expcSeq={법령해석례일련번호}
- 법령: /법령/{법령명}/{조문번호}  (예: /법령/민법/제618조)
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from app.graph.state import Citation, State

_BASE_URL = "https://www.law.go.kr"


def _build_url(doc: dict[str, Any]) -> str:
    """doc_type과 source_id로 법령정보센터 상세 페이지 URL을 구성한다."""
    doc_type = doc.get("doc_type", "")
    source_id = str(doc.get("source_id", ""))

    if doc_type == "판례" and source_id:
        return f"{_BASE_URL}/LSW/precInfoP.do?precSeq={source_id}"

    if doc_type == "법령해석례" and source_id:
        return f"{_BASE_URL}/LSW/expcInfoP.do?expcSeq={source_id}"

    # 법령ID는 lsiSeq(법령일련번호)가 아니므로 lsInfoP.do에 넣으면 엉뚱한 법령이 열린다.
    law_name = doc.get("title", "")
    if doc_type == "법령" and law_name:
        parts = [_BASE_URL, quote("법령"), quote(law_name)]
        if doc.get("조문번호"):
            parts.append(quote(doc["조문번호"]))
        return "/".join(parts)

    return _BASE_URL


def _extract_detail(doc: dict[str, Any]) -> str:
    """doc_type별 부가 정보 문자열을 생성한다."""
    doc_type = doc.get("doc_type", "")

    if doc_type == "법령":
        parts = [doc.get("조문번호", ""), doc.get("조문제목", "")]
        return " ".join(p for p in parts if p)

    if doc_type == "판례":
        return doc.get("사건번호", "")

    if doc_type == "법령해석례":
        return doc.get("chunk_id", "")  # 안건번호

    return ""


def _deduplicate(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """source_id 기준으로 중복을 제거한다."""
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for doc in docs:
        sid = str(doc.get("source_id", ""))
        if sid and sid in seen:
            continue
        seen.add(sid)
        unique.append(doc)
    return unique


def resolve_citations(state: State) -> dict:
    """retrieved_docs에서 출처를 추출하고 URL을 확보한다."""
    retrieved_docs = state.get("retrieved_docs", [])
    if not retrieved_docs:
        return {"citations": []}

    unique_docs = _deduplicate(retrieved_docs)

    citations: list[Citation] = []
    for doc in unique_docs:
        citations.append(
            Citation(
                doc_type=doc.get("doc_type", ""),
                title=doc.get("title", ""),
                source_id=str(doc.get("source_id", "")),
                detail=_extract_detail(doc),
                url=_build_url(doc),
            )
        )

    return {"citations": citations}
