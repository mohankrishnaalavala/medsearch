"""Unit tests for evaluation metrics functions.

These tests do not hit external services.
"""
from app.evaluation.search_metrics import calculate_ndcg_at_k, calculate_recall_at_k


def test_ndcg_at_k_basic_binary():
    # Relevant set contains two items; ideal DCG at k=3 is 1 + 1/log2(3)
    ranked = ["a", "b", "c", "d"]
    rel = {"a", "c"}
    ndcg3 = calculate_ndcg_at_k(ranked, rel, k=3)
    # Compute expected
    import math

    dcg = 1.0 / math.log2(1 + 1) + 1.0 / math.log2(3 + 1)  # a at 1, c at 3
    idcg = 1.0 / math.log2(1 + 1) + 1.0 / math.log2(2 + 1)
    expected = dcg / idcg
    assert abs(ndcg3 - expected) < 1e-9


def test_ndcg_no_relevant_returns_zero():
    ranked = ["a", "b", "c"]
    rel = set()
    assert calculate_ndcg_at_k(ranked, rel, k=3) == 0.0


def test_recall_at_k_basic():
    ranked = ["a", "b", "c", "d"]
    rel = {"b", "e"}  # only b is retrieved in top-3
    recall3 = calculate_recall_at_k(ranked, rel, k=3)
    assert recall3 == 0.5


def test_recall_no_relevant_returns_zero():
    assert calculate_recall_at_k(["a"], set(), k=1) == 0.0

