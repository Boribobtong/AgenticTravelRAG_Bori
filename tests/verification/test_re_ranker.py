from src.rag.re_ranker import simple_rerank


def test_simple_rerank_prefers_overlap():
    query = "quiet romantic hotel with breakfast"

    # create three fake results: one with strong overlap, others weak
    results = [
        {'_id': '1', '_source': {'review_text': 'loud noisy crowd and cheap food'}, 'combined_score': 0.9},
        {'_id': '2', '_source': {'review_text': 'quiet romantic atmosphere; great breakfast'}, 'combined_score': 0.2},
        {'_id': '3', '_source': {'review_text': 'average stay, friendly staff'}, 'combined_score': 0.3}
    ]

    reranked = simple_rerank(results, query)

    # top result should be the one with romantic/quiet/breakfast
    assert len(reranked) == 3
    assert reranked[0]['_id'] == '2'
