from src.rag.elasticsearch_rag import ElasticSearchRAG


def test_adaptive_alpha_semantic_preference():
    # call the unbound method without instantiating heavy dependencies
    alpha = ElasticSearchRAG.adaptive_alpha(None, "romantic quiet scenic stay")
    assert alpha >= 0.6


def test_adaptive_alpha_keyword_preference():
    alpha = ElasticSearchRAG.adaptive_alpha(None, "near center close to parking and breakfast")
    assert alpha <= 0.5
