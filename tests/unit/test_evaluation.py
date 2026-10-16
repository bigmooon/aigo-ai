# Generated from notebooks/redesign/01_eval_set.ipynb; edit the notebook, not this file.
"""법률 정답이 아닌 합성 fixture로 평가 계산과 누수 방지를 검증합니다."""

import unittest

from harness.evaluation import (
    blind_review, paired_comparison, percentile, retrieval_metrics,
    reviewed_rate, validate_eval_set,
)


class EvaluationTests(unittest.TestCase):
    """손계산 결과와 평가를 중단해야 하는 입력을 확인합니다."""

    def test_hit_is_not_recall(self):
        result = retrieval_metrics(["X", "B", "B"], {"A": 2, "B": 1, "X": 0})
        self.assertEqual([result[k] for k in ("hit@5", "recall@5", "precision@5", "mrr@5")],
                         [1, .5, .2, .5])
        self.assertAlmostEqual(result["ndcg@5"], .6309297536 / 3.6309297536)
        self.assertEqual(result["retrieved_units"], 2)

    def test_dedup_before_cutoff_and_ideal(self):
        gold = {"A": 2, "B": 1, "X": 0, "Y": 0, "Z": 0}
        self.assertEqual(retrieval_metrics(["A", "A", "B"], gold)["ndcg@5"], 1)
        self.assertEqual(retrieval_metrics(["X", "X", "Y", "Z", "A", "B"], gold)["recall@5"], 1)

    def test_empty_and_no_answer(self):
        self.assertEqual(retrieval_metrics([], {"A": 2})["recall@5"], 0)
        result = retrieval_metrics([], {}, answerable=False)
        self.assertIsNone(result["recall@5"])
        self.assertIsNone(result["ndcg@5"])
        self.assertEqual(result["precision@5"], 0)

    def test_unjudged_invalid_and_missing_gold(self):
        for retrieved, gold in [(["U"], {"A": 2}), ([], {}), ([], {"A": None}),
                                ([], {"A": 3}), ([], {"A": True})]:
            with self.subTest(gold=gold), self.assertRaises(ValueError):
                retrieval_metrics(retrieved, gold)

    def test_rates_preserve_missing_and_denominators(self):
        self.assertIsNone(reviewed_rate([])["value"])
        self.assertEqual(reviewed_rate([True, False])["value"], .5)
        self.assertEqual(reviewed_rate([True, None]),
                         {"value": None, "numerator": 1, "denominator": 2, "reviewed": 1})
        with self.assertRaises(ValueError):
            reviewed_rate([1])

    def test_percentiles(self):
        self.assertEqual(percentile([5, 1, 4, 2, 3], .5), 3)
        self.assertAlmostEqual(percentile([1, 2, 3, 4, 5], .95), 4.8)
        self.assertIsNone(percentile([], .95))
        for values, p in [([float("nan")], .5), ([1], 2)]:
            with self.assertRaises(ValueError):
                percentile(values, p)

    def test_group_weighted_pairs_and_reproducibility(self):
        rows = [{"id": str(i), "scenario_id": group, "before": 0, "after": value}
                for i, (group, value) in enumerate([("A", 1), ("A", 1), ("B", 0)])]
        rows.append({"id": "missing", "scenario_id": "C", "before": None, "after": 1})
        result = paired_comparison(rows)
        self.assertEqual(result["delta"], .5)  # 2/3이 아니라 상황 두 개에 동일 가중
        self.assertEqual((result["n_items"], result["n_groups"], result["excluded_pairs"]), (3, 2, 1))
        self.assertEqual(result, paired_comparison(rows))
        self.assertEqual(result["ci95"], [0, 1])
        self.assertIsNone(paired_comparison(rows[:1])["ci95"])
        self.assertIsNone(paired_comparison([])["delta"])
        with self.assertRaises(ValueError):
            paired_comparison(rows + rows[:1])

    def test_split_leak_and_draft_gate(self):
        items = [{"id": "1", "scenario_id": "A", "split": "dev", "query": "질문"},
                 {"id": "2", "scenario_id": "B", "split": "holdout", "query": "다른 질문"}]
        self.assertEqual(validate_eval_set(items), {"dev": 1, "holdout": 1})
        with self.assertRaises(ValueError):
            validate_eval_set(items, ready=True)
        for change in ({"scenario_id": "A"}, {"query": "질 문"}, {"id": "1"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_eval_set([items[0], {**items[1], **change}])

    def test_blind_review_has_no_model_or_default_score(self):
        answers = [{"id": "D01", "model": m, "answer": f"응답 {i}"}
                   for i, m in enumerate(["before", "after"])]
        sheet, key = blind_review(answers)
        self.assertEqual(len(key), 2)
        self.assertTrue(all("model" not in row and row["answer_relevance"] is None for row in sheet))
        self.assertEqual({row["model"] for row in key.values()}, {"before", "after"})
        self.assertEqual((sheet, key), blind_review(answers))
    def test_document_version_is_part_of_evidence_id(self):
        old = "law|2020-01-01|article6|paragraph1"
        current = "law|2026-01-01|article6|paragraph1"
        result = retrieval_metrics([old], {old: 0, current: 2})
        self.assertEqual(result["recall@5"], 0)
        self.assertEqual(result["hit@5"], 0)

    def test_ready_requires_reviewed_answer_evidence(self):
        item = {"id": "D01", "scenario_id": "A", "split": "dev", "query": "합성 질문",
                "review_status": "approved", "reviewer": "fixture_reviewer",
                "expected_behavior": "answer", "reference_answer": "합성 답",
                "expected_sources": ["synthetic|v1|section1"],
                "must_include": ["핵심 조건"], "must_not_include": []}
        self.assertEqual(validate_eval_set([item], ready=True), {"dev": 1, "holdout": 0})
        with self.assertRaises(ValueError):
            validate_eval_set([{**item, "expected_sources": []}], ready=True)
        with self.assertRaises(ValueError):
            validate_eval_set([{**item, "must_include": None}], ready=True)
    def test_external_answer_is_valid_behavior_and_needs_evidence(self):
        item = {"id": "Q10", "scenario_id": "Q10", "split": "dev", "query": "합성 정책 질문",
                "review_status": "approved", "reviewer": "fixture_reviewer",
                "expected_behavior": "answer_with_external", "reference_answer": "합성 답",
                "expected_sources": ["synthetic|v1|section1"],
                "must_include": ["핵심 조건"], "must_not_include": []}
        self.assertEqual(validate_eval_set([item], ready=True), {"dev": 1, "holdout": 0})
        with self.assertRaises(ValueError):
            validate_eval_set([{**item, "expected_sources": []}], ready=True)
