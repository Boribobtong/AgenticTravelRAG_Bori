"""
RAG Unit Tests: 
ElasticSearchRAG 클래스의 주요 기능 (인덱스 생성, 하이브리드 검색 등)을
모의 ElasticSearch 인스턴스를 사용하여 테스트합니다.
"""

import pytest
from typing import List, Dict, Any
from datetime import datetime
from unittest.mock import MagicMock, patch

# 테스트 대상 모듈 임포트
from src.rag.elasticsearch_rag import ElasticSearchRAG, ReviewDocument

# 모의 데이터
MOCK_DOCUMENTS = [
    ReviewDocument(doc_id="1", hotel_name="Luxury Resort", location="Maldives", review_text="The most romantic and quiet place I've ever been. Excellent service.", rating=5.0),
    ReviewDocument(doc_id="2", hotel_name="Budget Inn", location="Tokyo", review_text="Cheap and cheerful. Great for backpackers.", rating=3.5),
    ReviewDocument(doc_id="3", hotel_name="Family Hotel", location="Seoul", review_text="Kid-friendly and spacious rooms. The breakfast was good.", rating=4.2),
]

@pytest.fixture
def mock_es_client():
    """ElasticSearch 클라이언트 모킹 픽스처"""
    mock_client = MagicMock()
    # ping() 메소드가 항상 True를 반환하도록 설정
    mock_client.ping.return_value = True
    # indices.exists()가 기본적으로 False를 반환하도록 설정
    mock_client.indices.exists.return_value = False
    return mock_client

@pytest.fixture
def mock_embedding_model():
    """SentenceTransformer 모델 모킹 픽스처"""
    mock_model = MagicMock()
    # 임베딩 차원 설정
    mock_model.get_sentence_embedding_dimension.return_value = 384
    # encode() 메소드가 더미 벡터를 반환하도록 설정
    mock_model.encode.return_value = [
        [0.1] * 384, [0.2] * 384, [0.3] * 384
    ]
    return mock_model

@patch('src.rag.elasticsearch_rag.Elasticsearch')
@patch('src.rag.elasticsearch_rag.SentenceTransformer')
def test_rag_initialization(MockST, MockES, mock_embedding_model, mock_es_client):
    """RAG 인스턴스 초기화 테스트"""
    MockES.return_value = mock_es_client
    MockST.return_value = mock_embedding_model
    
    rag = ElasticSearchRAG(es_host="test_host", es_port=9201)
    
    assert rag.es.ping() is True
    assert rag.embedding_model == mock_embedding_model
    assert rag.embedding_dim == 384
    
    # Elasticsearch 초기화 호출 확인
    MockES.assert_called_once()

@patch('src.rag.elasticsearch_rag.Elasticsearch')
@patch('src.rag.elasticsearch_rag.SentenceTransformer')
def test_create_index(MockST, MockES, mock_embedding_model, mock_es_client):
    """인덱스 생성 테스트"""
    MockES.return_value = mock_es_client
    MockST.return_value = mock_embedding_model
    
    rag = ElasticSearchRAG()
    
    # 인덱스 존재하지 않음 -> 생성 호출
    rag.create_index()
    mock_es_client.indices.create.assert_called_once()
    
    # force_recreate=True, 인덱스 존재 -> 삭제 후 생성 호출
    mock_es_client.indices.exists.return_value = True
    rag.create_index(force_recreate=True)
    mock_es_client.indices.delete.assert_called_once()
    # create는 두 번째 호출되어야 함
    assert mock_es_client.indices.create.call_count == 2

@patch('src.rag.elasticsearch_rag.Elasticsearch')
@patch('src.rag.elasticsearch_rag.SentenceTransformer')
@patch('src.rag.elasticsearch_rag.helpers.bulk')
def test_index_documents(MockBulk, MockST, MockES, mock_embedding_model, mock_es_client):
    """문서 인덱싱 테스트"""
    MockES.return_value = mock_es_client
    MockST.return_value = mock_embedding_model
    
    # bulk 작업 성공으로 모의 설정
    MockBulk.return_value = (len(MOCK_DOCUMENTS), []) 
    
    rag = ElasticSearchRAG()
    rag.index_documents(MOCK_DOCUMENTS, batch_size=2)
    
    # bulk 호출 확인 (3개 문서, 배치 크기 2이므로 2번 호출)
    assert MockBulk.call_count == 2
    
    # 인덱스 새로고침 확인
    mock_es_client.indices.refresh.assert_called_once()

# 하이브리드 검색은 Mocking이 복잡하므로, 가장 중요한 결과 융합 로직만 테스트합니다.
def test_result_fusion():
    """결과 융합 (RRF) 로직 테스트"""
    
    rag = ElasticSearchRAG() # 실제 RAG 인스턴스지만, 메소드만 사용
    
    # 모의 검색 결과
    bm25_results = [
        {'_id': 'doc1', '_score': 10.0, '_source': {'hotel_name': 'A'}},
        {'_id': 'doc2', '_score': 5.0, '_source': {'hotel_name': 'B'}},
    ]
    
    semantic_results = [
        {'_id': 'doc2', '_score': 0.8, '_source': {'hotel_name': 'B'}},
        {'_id': 'doc3', '_score': 0.6, '_source': {'hotel_name': 'C'}},
    ]
    
    # 1. 융합 실행 (alpha=0.5)
    fused = rag._fuse_results(bm25_results, semantic_results, alpha=0.5)
    
    # 정규화된 점수 계산 예상:
    # Max BM25 = 10.0, Max Semantic = 0.8
    # Doc1: (1 - 0.5) * (10.0/10.0) + 0.5 * (0/0.8) = 0.5 * 1.0 + 0 = 0.5
    # Doc2: (1 - 0.5) * (5.0/10.0) + 0.5 * (0.8/0.8) = 0.5 * 0.5 + 0.5 * 1.0 = 0.25 + 0.5 = 0.75
    # Doc3: (1 - 0.5) * (0/10.0) + 0.5 * (0.6/0.8) = 0 + 0.5 * 0.75 = 0.375
    
    # 예상 정렬 순서: Doc2 (0.75) > Doc1 (0.5) > Doc3 (0.375)
    
    assert len(fused) == 3
    assert fused[0]['_id'] == 'doc2'
    assert fused[1]['_id'] == 'doc1'
    # combined_score의 정확한 계산값 비교
    assert fused[0]['combined_score'] == pytest.approx(0.75) 
    assert fused[1]['combined_score'] == pytest.approx(0.50)
    assert fused[2]['combined_score'] == pytest.approx(0.375)