"""
Optional cross-encoder re-ranker.

This module attempts to load a CrossEncoder (from sentence-transformers) only
when requested (via environment variable). If the heavy dependency is not
installed or loading fails, functions return None so callers can fall back to
the lightweight `simple_rerank`.

The design keeps imports lazy and fails gracefully for CI/local runs where
heavy ML packages are intentionally not installed.
"""
import os
from typing import List, Dict, Any, Optional


def try_cross_rerank(results: List[Dict[str, Any]], query: str) -> Optional[List[Dict[str, Any]]]:
    """
    Try to rerank using a CrossEncoder. Returns a new ranked list on success,
    or None if the cross-encoder isn't available or fails to load.
    """
    use_flag = os.getenv('USE_CROSS_ENCODER', '').lower() in ('1', 'true', 'yes')
    if not use_flag:
        return None

    try:
        # Lazy import to avoid heavy dependency unless explicitly requested
        from sentence_transformers import CrossEncoder
    except Exception:
        return None

    model_name = os.getenv('CROSS_ENCODER_MODEL', 'cross-encoder/ms-marco-MiniLM-L-6-v2')
    try:
        model = CrossEncoder(model_name)
    except Exception:
        return None

    # Prepare pairs for scoring: (query, passage)
    texts = []
    for r in results:
        src = r.get('_source', {})
        text = src.get('review_text') or src.get('review_snippet') or ''
        texts.append(text)

    if not texts:
        return results

    try:
        scores = model.predict([[query, t] for t in texts])
    except Exception:
        return None

    # Attach rerank_score and sort
    scored = []
    for r, s in zip(results, scores):
        new = dict(r)
        new['rerank_score'] = float(s)
        scored.append(new)

    scored_sorted = sorted(scored, key=lambda x: x['rerank_score'], reverse=True)
    return scored_sorted
