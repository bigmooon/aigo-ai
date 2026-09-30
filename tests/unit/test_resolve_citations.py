from app.graph.nodes.resolve_citations import _build_url, resolve_citations


def test_prec_url_is_permalink_without_api_key():
    """판례 링크는 퍼머링크이며 API 주소·인증키를 포함하지 않는다."""
    url = _build_url({"doc_type": "판례", "source_id": "235603"})
    assert url == "https://www.law.go.kr/LSW/precInfoP.do?precSeq=235603"
    assert "OC=" not in url and "/DRF/" not in url


def test_expc_url_is_permalink():
    url = _build_url({"doc_type": "법령해석례", "source_id": "313107"})
    assert url == "https://www.law.go.kr/LSW/expcInfoP.do?expcSeq=313107"


def test_law_url_uses_law_name_and_article():
    """법령ID를 lsiSeq로 쓰면 다른 법령이 열리므로 법령명·조문번호 퍼머링크를 쓴다."""
    url = _build_url({"doc_type": "법령", "source_id": "001706", "title": "민법", "조문번호": "제618조"})
    assert url == "https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EB%AF%BC%EB%B2%95/%EC%A0%9C618%EC%A1%B0"
    assert "lsiSeq" not in url


def test_law_url_without_article_points_to_law():
    url = _build_url({"doc_type": "법령", "title": "민법"})
    assert url == "https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EB%AF%BC%EB%B2%95"


def test_unknown_doc_falls_back_to_site_root():
    assert _build_url({"doc_type": "기타"}) == "https://www.law.go.kr"


def test_resolve_citations_never_exposes_api_key():
    docs = [
        {"doc_type": "판례", "source_id": "1", "title": "t", "사건번호": "2022다1"},
        {"doc_type": "법령해석례", "source_id": "2", "title": "t", "chunk_id": "21-0001"},
        {"doc_type": "법령", "source_id": "001706", "title": "민법", "조문번호": "제636조"},
    ]
    citations = resolve_citations({"retrieved_docs": docs})["citations"]
    assert len(citations) == 3
    assert all("OC=" not in c["url"] for c in citations)
