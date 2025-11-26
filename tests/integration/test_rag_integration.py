import os
import sys
import time
import asyncio
import subprocess
import socket
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from elasticsearch import Elasticsearch
from src.agents.hotel_rag import HotelRAGAgent


def wait_for_es(host='localhost', port=9200, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except Exception:
            time.sleep(1)
    return False


@pytest.mark.integration
def test_rag_end_to_end(tmp_path):
    """Start ES via docker-compose, index a doc, and run HotelRAGAgent.search_with_fallback."""
    # Start ES container
    subprocess.run(["docker-compose", "up", "-d", "elasticsearch"], check=True)

    try:
        assert wait_for_es(), "Elasticsearch did not become ready in time"

        es = Elasticsearch([{"host": "localhost", "port": 9200, "scheme": "http"}])

        index_name = "art_hotel_reviews"
        # index a simple document
        doc = {
            "hotel_name": "Integration Test Hotel",
            "location": "Seoul",
            "rating": 4.6,
            "review_text": "Excellent, clean and friendly staff",
            "tags": ["clean", "friendly"]
        }
        es.index(index=index_name, id="int1", document=doc)
        es.indices.refresh(index=index_name)

        # Create a lightweight RAG stub and inject into a HotelRAGAgent instance
        class SimpleRAGStub:
            def __init__(self, es_client, index_name):
                self.es = es_client
                self.index_name = index_name

            def hybrid_search(self, query, location=None, min_rating=None, tags=None, top_k=10, alpha=0.5):
                body = {"query": {"multi_match": {"query": query, "fields": ["review_text", "hotel_name"]}}, "size": top_k}
                res = self.es.search(index=self.index_name, body=body)
                formatted = []
                for hit in res['hits']['hits']:
                    src = hit['_source']
                    formatted.append({
                        'hotel_name': src.get('hotel_name'),
                        'location': src.get('location'),
                        'rating': src.get('rating', 0),
                        'review_snippet': src.get('review_text', '')[:200],
                        'tags': src.get('tags', []),
                        'combined_score': hit.get('_score', 0),
                        'bm25_score': hit.get('_score', 0),
                        'semantic_score': 0
                    })
                return formatted

        # instantiate agent without running its __init__ to avoid heavy model loads
        agent = HotelRAGAgent.__new__(HotelRAGAgent)
        agent.rag = SimpleRAGStub(es, index_name)

        # run the fallback search (async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(agent.search_with_fallback({"destination": "Seoul", "preferences": {}}))
        loop.close()

        assert isinstance(results, list)
        assert len(results) >= 1
    finally:
        # Tear down ES container
        subprocess.run(["docker-compose", "down", "-v"], check=False)
