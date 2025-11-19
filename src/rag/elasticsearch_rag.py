"""
ElasticSearch RAG Pipeline: TripAdvisor 리뷰 기반 하이브리드 검색 시스템

BM25(키워드) + 시맨틱(임베딩) 하이브리드 검색을 통해
사용자의 추상적인 요구사항을 이해하고 호텔을 추천합니다.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from dataclasses import dataclass, asdict

from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer
import pandas as pd
from datasets import load_dataset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ReviewDocument:
    """리뷰 문서 스키마"""
    doc_id: str
    hotel_name: str
    location: str
    review_text: str
    rating: float
    review_title: Optional[str] = None
    reviewer_location: Optional[str] = None
    review_date: Optional[str] = None
    helpful_votes: int = 0
    total_votes: int = 0
    tags: List[str] = None
    
    def to_dict(self) -> Dict:
        """딕셔너리 변환"""
        return {k: v for k, v in asdict(self).items() if v is not None}


class ElasticSearchRAG:
    """
    ElasticSearch 기반 RAG 시스템
    TripAdvisor 리뷰 데이터를 인덱싱하고 하이브리드 검색을 제공합니다.
    """
    
    def __init__(
        self,
        es_host: str = "localhost",
        es_port: int = 9200,
        index_name: str = "art_hotel_reviews",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        초기화
        
        Args:
            es_host: ElasticSearch 호스트
            es_port: ElasticSearch 포트
            index_name: 인덱스 이름
            embedding_model: 임베딩 모델 이름
        """
        
        # ElasticSearch 연결
        self.es = Elasticsearch(
            [{'host': es_host, 'port': es_port, 'scheme': 'http'}],
            timeout=30,
            max_retries=3,
            retry_on_timeout=True
        )
        
        self.index_name = index_name
        
        # 임베딩 모델 로드
        logger.info(f"임베딩 모델 로딩: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        
        logger.info(f"ElasticSearch RAG 초기화 완료: {es_host}:{es_port}")
    
    def create_index(self, force_recreate: bool = False):
        """
        ElasticSearch 인덱스 생성
        
        Args:
            force_recreate: True면 기존 인덱스 삭제 후 재생성
        """
        
        if force_recreate and self.es.indices.exists(index=self.index_name):
            logger.warning(f"기존 인덱스 삭제: {self.index_name}")
            self.es.indices.delete(index=self.index_name)
        
        if not self.es.indices.exists(index=self.index_name):
            # 인덱스 매핑 정의
            mapping = {
                "mappings": {
                    "properties": {
                        # 기본 필드
                        "doc_id": {"type": "keyword"},
                        "hotel_name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                        "location": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                        
                        # 리뷰 텍스트 (BM25 검색용)
                        "review_text": {
                            "type": "text",
                            "analyzer": "standard",  # 또는 custom analyzer
                            "fields": {
                                "english": {"type": "text", "analyzer": "english"}
                            }
                        },
                        "review_title": {"type": "text"},
                        
                        # 메타데이터
                        "rating": {"type": "float"},
                        "review_date": {"type": "date", "format": "yyyy-MM-dd||epoch_millis", "ignore_malformed": True},
                        "reviewer_location": {"type": "keyword"},
                        "helpful_votes": {"type": "integer"},
                        "total_votes": {"type": "integer"},
                        "tags": {"type": "keyword"},
                        
                        # 임베딩 벡터 (시맨틱 검색용)
                        "review_vector": {
                            "type": "dense_vector",
                            "dims": self.embedding_dim,
                            "index": True,
                            "similarity": "cosine"
                        },
                        
                        # 집계된 호텔 정보
                        "hotel_avg_rating": {"type": "float"},
                        "hotel_review_count": {"type": "integer"},
                        
                        # 인덱싱 타임스탬프
                        "indexed_at": {"type": "date"}
                    }
                },
                "settings": {
                    "number_of_shards": 2,
                    "number_of_replicas": 1,
                    "analysis": {
                        "analyzer": {
                            "review_analyzer": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase", "stop", "synonym_filter", "stemmer"]
                            }
                        },
                        "filter": {
                            "synonym_filter": {
                                "type": "synonym",
                                "synonyms": [
                                    "quiet,peaceful,calm,tranquil",
                                    "romantic,intimate,cozy",
                                    "luxury,luxurious,premium,upscale",
                                    "budget,cheap,affordable,economical",
                                    "clean,tidy,spotless,pristine",
                                    "friendly,hospitable,welcoming",
                                    "breakfast,morning meal",
                                    "wifi,internet,wireless"
                                ]
                            }
                        }
                    }
                }
            }
            
            # 인덱스 생성
            self.es.indices.create(index=self.index_name, body=mapping)
            logger.info(f"인덱스 생성 완료: {self.index_name}")
        else:
            logger.info(f"인덱스 이미 존재: {self.index_name}")
    
    def load_and_process_tripadvisor_data(self, max_docs: int = None) -> List[ReviewDocument]:
        """
        HuggingFace에서 TripAdvisor 데이터셋 로드 및 전처리
        
        Args:
            max_docs: 로드할 최대 문서 수 (테스트용)
            
        Returns:
            ReviewDocument 리스트
        """
        
        logger.info("TripAdvisor 데이터셋 로딩 시작...")
        
        # HuggingFace 데이터셋 로드
        dataset = load_dataset("jniimi/tripadvisor-review-rating", split="train")
        
        if max_docs:
            dataset = dataset.select(range(min(max_docs, len(dataset))))
        
        documents = []
        
        for idx, item in enumerate(dataset):
            try:
                # 필드 매핑 (실제 데이터셋 구조에 맞게 조정 필요)
                doc = ReviewDocument(
                    doc_id=f"tripadvisor_{idx}",
                    hotel_name=item.get('hotel_name', f"Hotel_{idx}"),  # 실제 필드명 확인 필요
                    location=item.get('location', 'Unknown'),
                    review_text=item.get('text', item.get('review', '')),  # 리뷰 텍스트 필드
                    rating=float(item.get('rating', 0)),
                    review_title=item.get('title', None),
                    tags=self._extract_tags(item.get('text', ''))
                )
                
                documents.append(doc)
                
                if idx % 1000 == 0:
                    logger.info(f"처리 진행: {idx}/{len(dataset)}")
                    
            except Exception as e:
                logger.warning(f"문서 처리 실패 (idx={idx}): {str(e)}")
                continue
        
        logger.info(f"데이터 로드 완료: {len(documents)}개 문서")
        return documents
    
    def _extract_tags(self, text: str) -> List[str]:
        """리뷰 텍스트에서 태그 추출"""
        tags = []
        
        # 키워드 매칭 기반 태그 추출
        keyword_tags = {
            'wifi': ['wifi', 'internet', 'wireless'],
            'breakfast': ['breakfast', 'morning meal'],
            'parking': ['parking', 'car park'],
            'pool': ['pool', 'swimming'],
            'gym': ['gym', 'fitness', 'workout'],
            'spa': ['spa', 'massage', 'wellness'],
            'pet_friendly': ['pet', 'dog', 'cat'],
            'business': ['business', 'conference', 'meeting room'],
            'family': ['family', 'kids', 'children'],
            'romantic': ['romantic', 'honeymoon', 'couples']
        }
        
        text_lower = text.lower()
        for tag, keywords in keyword_tags.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(tag)
        
        return tags
    
    def index_documents(self, documents: List[ReviewDocument], batch_size: int = 100):
        """
        문서 인덱싱 (벡터 임베딩 포함)
        
        Args:
            documents: ReviewDocument 리스트
            batch_size: 배치 크기
        """
        
        logger.info(f"인덱싱 시작: {len(documents)}개 문서")
        
        # 배치 단위로 처리
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            
            # 리뷰 텍스트 임베딩
            texts = [doc.review_text for doc in batch]
            embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
            
            # ElasticSearch bulk 작업 준비
            actions = []
            for doc, embedding in zip(batch, embeddings):
                action = {
                    "_index": self.index_name,
                    "_id": doc.doc_id,
                    "_source": {
                        **doc.to_dict(),
                        "review_vector": embedding.tolist(),
                        "indexed_at": datetime.now().isoformat()
                    }
                }
                actions.append(action)
            
            # Bulk 인덱싱
            success, failed = helpers.bulk(
                self.es,
                actions,
                stats_only=True,
                raise_on_error=False
            )
            
            logger.info(f"배치 인덱싱: 성공={success}, 실패={failed}")
        
        # 인덱스 새로고침
        self.es.indices.refresh(index=self.index_name)
        logger.info("인덱싱 완료")
    
    def hybrid_search(
        self,
        query: str,
        location: Optional[str] = None,
        min_rating: Optional[float] = None,
        tags: Optional[List[str]] = None,
        top_k: int = 10,
        alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        하이브리드 검색 (BM25 + 시맨틱)
        
        Args:
            query: 검색 쿼리
            location: 위치 필터
            min_rating: 최소 평점
            tags: 태그 필터
            top_k: 반환할 결과 수
            alpha: 하이브리드 가중치 (0=BM25만, 1=시맨틱만)
            
        Returns:
            검색 결과 리스트
        """
        
        # 필터 구성
        filters = []
        if location:
            filters.append({"match": {"location": location}})
        if min_rating:
            filters.append({"range": {"rating": {"gte": min_rating}}})
        if tags:
            filters.append({"terms": {"tags": tags}})
        
        # 1. BM25 검색
        bm25_query = {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["review_text^2", "review_title", "hotel_name"],
                            "type": "best_fields"
                        }
                    }
                ],
                "filter": filters
            }
        }
        
        bm25_results = self.es.search(
            index=self.index_name,
            body={
                "query": bm25_query,
                "size": top_k * 2  # 더 많이 검색해서 나중에 융합
            }
        )
        
        # 2. 시맨틱 검색
        query_embedding = self.embedding_model.encode(query, show_progress_bar=False)
        
        semantic_query = {
            "script_score": {
                "query": {
                    "bool": {
                        "filter": filters
                    }
                },
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'review_vector') + 1.0",
                    "params": {"query_vector": query_embedding.tolist()}
                }
            }
        }
        
        semantic_results = self.es.search(
            index=self.index_name,
            body={
                "query": semantic_query,
                "size": top_k * 2
            }
        )
        
        # 3. 결과 융합
        combined_results = self._fuse_results(
            bm25_results['hits']['hits'],
            semantic_results['hits']['hits'],
            alpha=alpha
        )
        
        # 4. 결과 포맷팅
        formatted_results = []
        for result in combined_results[:top_k]:
            source = result['_source']
            formatted_results.append({
                'hotel_name': source['hotel_name'],
                'location': source['location'],
                'rating': source['rating'],
                'review_snippet': source['review_text'][:200] + '...',
                'tags': source.get('tags', []),
                'combined_score': result['combined_score'],
                'bm25_score': result.get('bm25_score', 0),
                'semantic_score': result.get('semantic_score', 0)
            })
        
        return formatted_results
    
    def _fuse_results(
        self,
        bm25_results: List[Dict],
        semantic_results: List[Dict],
        alpha: float = 0.5
    ) -> List[Dict]:
        """
        BM25와 시맨틱 검색 결과 융합
        
        Args:
            bm25_results: BM25 검색 결과
            semantic_results: 시맨틱 검색 결과
            alpha: 가중치 (0=BM25만, 1=시맨틱만)
            
        Returns:
            융합된 결과
        """
        
        # 점수 정규화
        max_bm25 = max([r['_score'] for r in bm25_results]) if bm25_results else 1
        max_semantic = max([r['_score'] for r in semantic_results]) if semantic_results else 1
        
        # 결과 맵 생성
        result_map = {}
        
        # BM25 결과 처리
        for r in bm25_results:
            doc_id = r['_id']
            result_map[doc_id] = {
                **r,
                'bm25_score': r['_score'] / max_bm25,
                'semantic_score': 0
            }
        
        # 시맨틱 결과 처리
        for r in semantic_results:
            doc_id = r['_id']
            if doc_id in result_map:
                result_map[doc_id]['semantic_score'] = r['_score'] / max_semantic
            else:
                result_map[doc_id] = {
                    **r,
                    'bm25_score': 0,
                    'semantic_score': r['_score'] / max_semantic
                }
        
        # 하이브리드 점수 계산
        for doc_id in result_map:
            result_map[doc_id]['combined_score'] = (
                (1 - alpha) * result_map[doc_id]['bm25_score'] +
                alpha * result_map[doc_id]['semantic_score']
            )
        
        # 정렬
        sorted_results = sorted(
            result_map.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )
        
        return sorted_results
    
    def get_similar_hotels(self, hotel_name: str, top_k: int = 5) -> List[Dict]:
        """
        유사한 호텔 찾기 (벡터 유사도 기반)
        
        Args:
            hotel_name: 기준 호텔 이름
            top_k: 반환할 호텔 수
            
        Returns:
            유사 호텔 리스트
        """
        
        # 기준 호텔 검색
        base_query = {
            "match": {"hotel_name.keyword": hotel_name}
        }
        
        base_result = self.es.search(
            index=self.index_name,
            body={"query": base_query, "size": 1}
        )
        
        if not base_result['hits']['hits']:
            logger.warning(f"호텔을 찾을 수 없음: {hotel_name}")
            return []
        
        # 기준 벡터 추출
        base_vector = base_result['hits']['hits'][0]['_source']['review_vector']
        
        # 유사 호텔 검색
        similar_query = {
            "script_score": {
                "query": {
                    "bool": {
                        "must_not": [
                            {"match": {"hotel_name.keyword": hotel_name}}
                        ]
                    }
                },
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'review_vector') + 1.0",
                    "params": {"query_vector": base_vector}
                }
            }
        }
        
        similar_results = self.es.search(
            index=self.index_name,
            body={
                "query": similar_query,
                "size": top_k,
                "aggs": {
                    "unique_hotels": {
                        "terms": {
                            "field": "hotel_name.keyword",
                            "size": top_k
                        }
                    }
                }
            }
        )
        
        # 결과 포맷팅
        hotels = []
        seen_hotels = set()
        
        for hit in similar_results['hits']['hits']:
            hotel = hit['_source']['hotel_name']
            if hotel not in seen_hotels:
                hotels.append({
                    'hotel_name': hotel,
                    'location': hit['_source']['location'],
                    'rating': hit['_source']['rating'],
                    'similarity_score': hit['_score']
                })
                seen_hotels.add(hotel)
        
        return hotels
    
    def analyze_hotel_reviews(self, hotel_name: str) -> Dict[str, Any]:
        """
        특정 호텔의 리뷰 분석
        
        Args:
            hotel_name: 호텔 이름
            
        Returns:
            분석 결과
        """
        
        # 호텔 리뷰 검색
        query = {
            "match": {"hotel_name": hotel_name}
        }
        
        results = self.es.search(
            index=self.index_name,
            body={
                "query": query,
                "size": 100,
                "aggs": {
                    "avg_rating": {"avg": {"field": "rating"}},
                    "rating_distribution": {
                        "histogram": {
                            "field": "rating",
                            "interval": 1
                        }
                    },
                    "common_tags": {
                        "terms": {
                            "field": "tags",
                            "size": 10
                        }
                    }
                }
            }
        )
        
        # 분석 결과 구성
        analysis = {
            'hotel_name': hotel_name,
            'total_reviews': results['hits']['total']['value'],
            'avg_rating': results['aggregations']['avg_rating']['value'],
            'rating_distribution': [
                {'rating': b['key'], 'count': b['doc_count']}
                for b in results['aggregations']['rating_distribution']['buckets']
            ],
            'common_tags': [
                {'tag': b['key'], 'count': b['doc_count']}
                for b in results['aggregations']['common_tags']['buckets']
            ],
            'sample_reviews': [
                {
                    'rating': hit['_source']['rating'],
                    'text': hit['_source']['review_text'][:200] + '...'
                }
                for hit in results['hits']['hits'][:3]
            ]
        }
        
        return analysis


# 싱글톤 인스턴스
_rag_instance = None

def get_rag_instance() -> ElasticSearchRAG:
    """RAG 싱글톤 인스턴스 반환"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = ElasticSearchRAG()
    return _rag_instance
