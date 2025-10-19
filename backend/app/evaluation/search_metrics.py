"""Evaluation harness for search quality metrics.

This module computes nDCG@k and Recall@k and can run side-by-side
comparisons for BM25-only, weighted fusion, and RRF strategies.

Usage:
    python -m app.evaluation.search_metrics --k 10 --strategy all \
        --queries-file backend/app/evaluation/queries.json

If no queries file is provided, it will run a small built-in demo and
print top IDs to help you curate ground truth.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from app.core.config import settings
from app.services.elasticsearch_service import (
    ElasticsearchService,
    get_elasticsearch_service,
)
from app.services.vertex_ai_service import get_vertex_ai_service

logger = logging.getLogger(__name__)


# -----------------------------
# Metric computations
# -----------------------------

def calculate_ndcg_at_k(
    ranked_ids: Sequence[str], relevant_ids: Set[str], k: int = 10
) -> float:
    """Compute nDCG@k for binary relevance.

    DCG@k = sum_{i=1..k} (rel_i / log2(i+1)) where rel_i in {0,1}.
    nDCG@k = DCG@k / IDCG@k. If IDCG is 0 (no relevant), returns 0.0.
    """
    if k <= 0:
        return 0.0

    # DCG
    dcg = 0.0
    for i, doc_id in enumerate(ranked_ids[:k], start=1):
        rel = 1.0 if doc_id in relevant_ids else 0.0
        if rel:
            dcg += rel / math.log2(i + 1)

    # IDCG: best possible ranking puts all relevant items first
    ideal_hits = min(len(relevant_ids), k)
    if ideal_hits == 0:
        return 0.0
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
    return dcg / idcg if idcg > 0 else 0.0


def calculate_recall_at_k(
    ranked_ids: Sequence[str], relevant_ids: Set[str], k: int = 10
) -> float:
    """Compute Recall@k for binary relevance.

    Recall@k = |retrieved ∩ relevant| / |relevant|
    If |relevant| == 0, returns 0.0 to avoid overclaiming.
    """
    if k <= 0:
        return 0.0
    if not relevant_ids:
        return 0.0
    retrieved_k: Set[str] = set(ranked_ids[:k])
    return len(retrieved_k & relevant_ids) / float(len(relevant_ids))


# -----------------------------
# Running evaluations
# -----------------------------

@dataclass
class EvalCase:
    query: str
    index: str  # one of settings.ELASTICSEARCH_INDEX_* values
    relevant_ids: Set[str]


async def _search_top_ids(
    es: ElasticsearchService,
    query: str,
    index_name: str,
    strategy: str,
    query_embedding: Optional[List[float]] = None,
    size: int = 10,
    keyword_weight: float = 0.3,
    semantic_weight: float = 0.7,
) -> List[str]:
    """Run a search and return the ranked _id list for the chosen strategy."""
    # Generate embedding if not provided
    if query_embedding is None:
        vertex = get_vertex_ai_service()
        query_embedding = await vertex.generate_embedding(query, task_type="RETRIEVAL_QUERY")

    # Choose fusion behavior
    fusion_strategy = None
    kw_w, sem_w = keyword_weight, semantic_weight
    if strategy == "bm25":
        kw_w, sem_w = 1.0, 0.0
        fusion_strategy = "weighted"
    elif strategy == "weighted":
        fusion_strategy = "weighted"
    elif strategy == "rrf":
        fusion_strategy = "rrf"
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    results = await es.hybrid_search(
        index_name=index_name,
        query_text=query,
        query_embedding=query_embedding,
        size=size,
        keyword_weight=kw_w,
        semantic_weight=sem_w,
        fusion_strategy=fusion_strategy,
    )
    return [r.get("_id") for r in results if r.get("_id")]


async def evaluate_cases(
    cases: Sequence[EvalCase],
    strategies: Sequence[str] = ("bm25", "weighted", "rrf"),
    k: int = 10,
    size: int = 10,
    keyword_weight: float = 0.3,
    semantic_weight: float = 0.7,
) -> Dict[str, Dict[str, float]]:
    """Run evaluation across strategies and return averaged metrics per strategy.

    Returns a dict like:
    {
      "bm25": {"nDCG@10": 0.42, "Recall@10": 0.36},
      "weighted": {...},
      "rrf": {...}
    }
    """
    es = await get_elasticsearch_service()

    # Per-strategy accumulators
    totals: Dict[str, Tuple[float, float, int]] = {s: (0.0, 0.0, 0) for s in strategies}

    for case in cases:
        for strategy in strategies:
            try:
                ids = await _search_top_ids(
                    es,
                    query=case.query,
                    index_name=case.index,
                    strategy=strategy,
                    size=size,
                    keyword_weight=keyword_weight,
                    semantic_weight=semantic_weight,
                )
                ndcg = calculate_ndcg_at_k(ids, case.relevant_ids, k=k)
                recall = calculate_recall_at_k(ids, case.relevant_ids, k=k)
                s_ndcg, s_recall, n = totals[strategy]
                totals[strategy] = (s_ndcg + ndcg, s_recall + recall, n + 1)
            except Exception as e:
                logger.error("Evaluation failed for strategy=%s query=%.40s: %s", strategy, case.query, e)

    # Compute averages
    results: Dict[str, Dict[str, float]] = {}
    for strategy in strategies:
        s_ndcg, s_recall, n = totals[strategy]
        if n > 0:
            results[strategy] = {f"nDCG@{k}": s_ndcg / n, f"Recall@{k}": s_recall / n}
        else:
            results[strategy] = {f"nDCG@{k}": 0.0, f"Recall@{k}": 0.0}
    return results


# -----------------------------
# CLI helpers
# -----------------------------

def _load_cases_from_file(path: Path) -> List[EvalCase]:
    data = json.loads(path.read_text())
    cases: List[EvalCase] = []
    for item in data:
        cases.append(
            EvalCase(
                query=item["query"],
                index=item["index"],
                relevant_ids=set(item.get("relevant_ids", [])),
            )
        )
    return cases


def _demo_cases() -> List[EvalCase]:
    """Small built-in set to exercise the pipeline. Replace with curated gold."""
    return [
        EvalCase(query="metformin for type 2 diabetes", index=settings.ELASTICSEARCH_INDEX_PUBMED, relevant_ids=set()),
        EvalCase(query="myocardial infarction treatment", index=settings.ELASTICSEARCH_INDEX_PUBMED, relevant_ids=set()),
        EvalCase(query="hypertension guidelines", index=settings.ELASTICSEARCH_INDEX_PUBMED, relevant_ids=set()),
    ]


async def _dump_top_ids(cases: Sequence[EvalCase], strategy: str, size: int = 10) -> None:
    es = await get_elasticsearch_service()
    for case in cases:
        ids = await _search_top_ids(es, case.query, case.index, strategy=strategy, size=size)
        print(f"Query: {case.query}\nTop-{size} ({strategy}): {ids}\n")


async def _main_async(args: argparse.Namespace) -> None:
    # Load cases
    if args.queries_file:
        cases = _load_cases_from_file(Path(args.queries_file))
    else:
        cases = _demo_cases()

    strategies: List[str] = []
    if args.strategy == "all":
        strategies = ["bm25", "weighted", "rrf"]
    else:
        strategies = [args.strategy]

    if args.dump_top:
        await _dump_top_ids(cases, strategy=strategies[0], size=args.size)
        return

    results = await evaluate_cases(
        cases,
        strategies=strategies,
        k=args.k,
        size=args.size,
        keyword_weight=args.keyword_weight,
        semantic_weight=args.semantic_weight,
    )

    # Pretty print
    print(json.dumps(results, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run search evaluation metrics")
    parser.add_argument("--k", type=int, default=10, help="Cutoff k for metrics (default 10)")
    parser.add_argument("--size", type=int, default=10, help="Search depth per query (default 10)")
    parser.add_argument(
        "--strategy",
        choices=["bm25", "weighted", "rrf", "all"],
        default="all",
        help="Which strategy to evaluate (default all)",
    )
    parser.add_argument("--queries-file", type=str, default="", help="Path to JSON with eval cases")
    parser.add_argument("--keyword-weight", type=float, default=0.3, help="Weight for BM25 in weighted fusion")
    parser.add_argument("--semantic-weight", type=float, default=0.7, help="Weight for semantic in weighted fusion")
    parser.add_argument("--dump-top", action="store_true", help="Only dump top IDs for curation")

    args = parser.parse_args()
    try:
        asyncio.run(_main_async(args))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

