"""
Performance Metrics Collector

Prometheus 기반 성능 메트릭 수집 시스템입니다.
"""

import logging
import time
from typing import Dict, Any, Optional
from contextlib import contextmanager
from prometheus_client import Counter, Histogram, Gauge, Summary, Info
from prometheus_client import generate_latest, REGISTRY
from prometheus_client.core import CollectorRegistry

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Prometheus 메트릭 수집기"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        Args:
            registry: Prometheus registry (기본값: REGISTRY)
        """
        self.registry = registry or REGISTRY
        
        # 요청 카운터
        self.request_count = Counter(
            'art_requests_total',
            'Total number of requests',
            ['endpoint', 'status'],
            registry=self.registry
        )
        
        # 응답 시간 히스토그램
        self.response_time = Histogram(
            'art_response_time_seconds',
            'Response time in seconds',
            ['node_name'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry
        )
        
        # 활성 세션 게이지
        self.active_sessions = Gauge(
            'art_active_sessions',
            'Number of active sessions',
            registry=self.registry
        )
        
        # 검색 결과 수 히스토그램
        self.search_results_count = Histogram(
            'art_search_results_count',
            'Number of search results returned',
            ['search_type'],
            buckets=[0, 1, 3, 5, 10, 20, 50],
            registry=self.registry
        )
        
        # 검색 점수 요약
        self.search_score = Summary(
            'art_search_score',
            'Search result scores',
            ['search_type'],
            registry=self.registry
        )
        
        # 에러 카운터
        self.error_count = Counter(
            'art_errors_total',
            'Total number of errors',
            ['node_name', 'error_type'],
            registry=self.registry
        )
        
        # 만족도 점수 히스토그램
        self.satisfaction_score = Histogram(
            'art_satisfaction_score',
            'User satisfaction scores',
            buckets=[0, 20, 40, 60, 80, 100],
            registry=self.registry
        )
        
        # A/B 테스트 변형 카운터
        self.ab_variant_count = Counter(
            'art_ab_variant_assignments_total',
            'A/B test variant assignments',
            ['experiment_name', 'variant_name'],
            registry=self.registry
        )
        
        # 시스템 정보
        self.system_info = Info(
            'art_system',
            'System information',
            registry=self.registry
        )
        
        # 시스템 정보 설정
        self.system_info.info({
            'version': '1.0.0',
            'environment': 'production'
        })
        
        logger.info("MetricsCollector initialized")
    
    @contextmanager
    def track_node_execution(self, node_name: str):
        """
        노드 실행 시간 추적 (컨텍스트 매니저)
        
        Usage:
            with metrics.track_node_execution('hotel_rag'):
                # 노드 실행 코드
                pass
        """
        start_time = time.time()
        try:
            yield
            # 성공
            self.request_count.labels(endpoint=node_name, status='success').inc()
        except Exception as e:
            # 실패
            self.request_count.labels(endpoint=node_name, status='error').inc()
            self.error_count.labels(
                node_name=node_name,
                error_type=type(e).__name__
            ).inc()
            raise
        finally:
            # 실행 시간 기록
            duration = time.time() - start_time
            self.response_time.labels(node_name=node_name).observe(duration)
    
    def record_search_quality(
        self,
        search_type: str,
        result_count: int,
        avg_score: float
    ):
        """
        검색 품질 메트릭 기록
        
        Args:
            search_type: 검색 유형 (예: 'hotel', 'weather')
            result_count: 검색 결과 수
            avg_score: 평균 검색 점수
        """
        self.search_results_count.labels(search_type=search_type).observe(result_count)
        self.search_score.labels(search_type=search_type).observe(avg_score)
    
    def record_satisfaction(self, score: float):
        """
        만족도 점수 기록
        
        Args:
            score: 만족도 점수 (0-100)
        """
        self.satisfaction_score.observe(score)
    
    def record_ab_assignment(self, experiment_name: str, variant_name: str):
        """
        A/B 테스트 변형 할당 기록
        
        Args:
            experiment_name: 실험 이름
            variant_name: 변형 이름
        """
        self.ab_variant_count.labels(
            experiment_name=experiment_name,
            variant_name=variant_name
        ).inc()
    
    def increment_active_sessions(self):
        """활성 세션 수 증가"""
        self.active_sessions.inc()
    
    def decrement_active_sessions(self):
        """활성 세션 수 감소"""
        self.active_sessions.dec()
    
    def get_metrics(self) -> bytes:
        """
        Prometheus 형식의 메트릭 반환
        
        Returns:
            Prometheus 텍스트 형식의 메트릭
        """
        return generate_latest(self.registry)


# 전역 메트릭 수집기 인스턴스
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    """전역 메트릭 수집기 반환"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
