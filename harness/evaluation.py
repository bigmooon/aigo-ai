# Generated from notebooks/redesign/01_eval_set.ipynb; edit the notebook, not this file.
import math
import random
from collections import defaultdict
from statistics import mean


def retrieval_metrics(retrieved, judgments, *, answerable=True):
    """근거 ID 순위와 관련도 dict를 받아 중복 제거 후 @5 지표·분모를 반환합니다."""
    if any(type(v) is not int or v not in (0, 1, 2) for v in judgments.values()):
        raise ValueError("관련도는 검토된 정수 0, 1, 2여야 합니다.")
    ranked = list(dict.fromkeys(retrieved))[:5]
    if set(ranked) - judgments.keys():
        raise ValueError("검색된 미판정 근거를 먼저 검토하세요.")
    relevant = {key for key, value in judgments.items() if value > 0}
    if answerable and not relevant:
        raise ValueError("정상 질문에는 검토된 정답 근거가 필요합니다.")
    grades = [judgments[key] for key in ranked]
    hits = sum(value > 0 for value in grades)
    dcg = sum((2**value - 1) / math.log2(rank + 1)
              for rank, value in enumerate(grades, 1))
    ideal = sorted(judgments.values(), reverse=True)[:5]
    idcg = sum((2**value - 1) / math.log2(rank + 1)
               for rank, value in enumerate(ideal, 1))
    return {
        "hit@5": int(hits > 0),
        "recall@5": hits / len(relevant) if answerable else None,
        "precision@5": hits / 5,
        "mrr@5": next((1 / rank for rank, value in enumerate(grades, 1) if value), 0),
        "ndcg@5": dcg / idcg if idcg else None,
        "retrieved_units": len(ranked), "relevant_units": len(relevant), "hits": hits,
    }


def reviewed_rate(labels):
    """bool/None 판정 목록에서 비율·분모를 반환합니다. 미검토가 있으면 값은 None입니다."""
    # 일부만 검토한 평균을 전체 점수로 오해하지 않도록 완결 전 계산을 막습니다.
    if any(value is not None and type(value) is not bool for value in labels):
        raise ValueError("판정은 True/False/None만 사용하세요.")
    reviewed = sum(value is not None for value in labels)
    return {"value": sum(value is True for value in labels) / len(labels)
            if labels and reviewed == len(labels) else None,
            "numerator": sum(value is True for value in labels),
            "denominator": len(labels), "reviewed": reviewed}


def percentile(values, probability):
    """유한한 숫자 목록에서 선형 보간 분위수를 반환합니다. 빈 목록은 None입니다."""
    if not 0 <= probability <= 1 or any(not math.isfinite(x) for x in values):
        raise ValueError("유한한 값과 0~1 확률이 필요합니다.")
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def paired_comparison(rows, *, seed=42, repeats=2000):
    """id/scenario_id/before/after 행을 받아 상황별 동등 가중 평균·차이·95% 구간을 반환합니다."""
    if type(repeats) is not int or repeats < 1:
        raise ValueError("bootstrap 반복 수는 양의 정수여야 합니다.")
    groups, seen, differences = defaultdict(list), set(), []
    for row in rows:
        if row["id"] in seen:
            raise ValueError("중복 질문 ID입니다.")
        seen.add(row["id"])
        before, after = row["before"], row["after"]
        if before is None or after is None:
            continue
        if not all(math.isfinite(value) for value in (before, after)):
            raise ValueError("NaN/무한 점수는 비교할 수 없습니다.")
        groups[row["scenario_id"]].append((before, after))
        differences.append({"id": row["id"], "delta": after - before})
    averages = [(mean(x[0] for x in values), mean(x[1] for x in values))
                for _, values in sorted(groups.items())]
    deltas = [after - before for before, after in averages]
    interval = None
    # 한 상황만으로 만든 0폭 구간은 확실성을 과장하므로 보고하지 않습니다.
    if len(deltas) >= 2:
        rng = random.Random(seed)
        samples = [mean(rng.choices(deltas, k=len(deltas))) for _ in range(repeats)]
        interval = [percentile(samples, .025), percentile(samples, .975)]
    return {"before": mean(x[0] for x in averages) if averages else None,
            "after": mean(x[1] for x in averages) if averages else None,
            "delta": mean(deltas) if deltas else None, "ci95": interval,
            "n_items": len(differences), "n_groups": len(groups),
            "excluded_pairs": len(rows) - len(differences),
            "item_differences": differences, "seed": seed, "repeats": repeats}

def validate_eval_set(items, *, ready=False):
    """질문 목록의 ID·상황 split 누수를 검사하고, ready이면 사람 라벨 완결도도 확인합니다."""
    ids, scenarios, queries = set(), {}, {}
    counts = {"dev": 0, "holdout": 0}
    for item in items:
        if item["id"] in ids:
            raise ValueError("질문 ID가 중복됩니다.")
        ids.add(item["id"])
        split, scenario = item["split"], item["scenario_id"]
        if split not in counts or not scenario or not item["query"].strip():
            raise ValueError("split/상황/질문을 확인하세요.")
        normalized = "".join(item["query"].lower().split())
        if scenarios.setdefault(scenario, split) != split:
            raise ValueError("같은 상황이 두 split에 있습니다.")
        if queries.setdefault(normalized, split) != split:
            raise ValueError("같은 질문이 두 split에 있습니다.")
        counts[split] += 1
        if ready:
            if item.get("review_status") != "approved" or not item.get("reviewer"):
                raise ValueError("사용자 정답 검토가 필요합니다.")
            for field in ("expected_behavior", "reference_answer", "must_include", "must_not_include"):
                if item.get(field) is None:
                    raise ValueError(f"미검토 필드: {field}")
            if item["expected_behavior"] not in ("answer", "answer_with_external", "clarify", "abstain", "out_of_scope"):
                raise ValueError("기대 행동을 확인하세요.")
            if item.get("expected_sources") is None:
                raise ValueError("근거 검토가 필요합니다.")
            if item["expected_behavior"] in ("answer", "answer_with_external") and (
                    not item["expected_sources"] or not item["must_include"]):
                raise ValueError("정상 질문의 근거·핵심 조건이 비어 있습니다.")
    return counts


def blind_review(answers, *, seed=42):
    """id/model/answer 행을 섞어 익명 검토표와 별도 복원 키를 반환합니다."""
    shuffled = list(answers)
    random.Random(seed).shuffle(shuffled)
    sheet, key = [], {}
    for index, row in enumerate(shuffled, 1):
        review_id = f"R{index:03d}"
        sheet.append({"review_id": review_id, "question_id": row["id"],
                      "answer": row["answer"],
                      "answer_relevance": None, "easy_terms": None,
                      "clear_sentences": None, "actionability": None,
                      "severe_error": None, "reason": None,
                      "llm_disagreement": None})
        key[review_id] = {"question_id": row["id"], "model": row["model"]}
    return sheet, key
