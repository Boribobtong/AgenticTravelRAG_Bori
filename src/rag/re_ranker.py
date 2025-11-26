"""
Light-weight re-ranker PoC for ElasticSearchRAG.

This module implements a low-dependency reranker used as a safe PoC in CI and
local runs. It prefers a simple lexical overlap score but provides a hook for
future cross-encoder integration.
"""
from typing import List, Dict, Any
import math


def _token_overlap_score(query: str, text: str) -> float:
    """Return a simple overlap score between query and text (0..1).

    This is intentionally cheap and deterministic for CI/unit tests.
    """
    if not query or not text:
        return 0.0

    q_tokens = set(q.strip().lower() for q in query.split())
    t_tokens = set(t.strip().lower() for t in text.split())
    if not q_tokens or not t_tokens:
        return 0.0

    overlap = q_tokens.intersection(t_tokens)
    return len(overlap) / float(len(q_tokens))


def simple_rerank(results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """Re-rank results by simple lexical similarity to query.

    Expects each result to contain a '_source' with 'review_text' or 'review_snippet'.
    Adds/updates a 'rerank_score' field and returns results sorted by it (desc).
    """
    scored = []
    for r in results:
        src = r.get('_source', {})
        text = src.get('review_text') or src.get('review_snippet') or ''
        score = _token_overlap_score(query, text)
        # combine with existing combined_score if present to prefer already-high scoring docs
        combined = score * 0.6 + float(r.get('combined_score', 0)) * 0.4
        new = dict(r)
        new['rerank_score'] = combined
        scored.append(new)

    scored_sorted = sorted(scored, key=lambda x: x['rerank_score'], reverse=True)
    return scored_sorted
