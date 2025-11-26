"""
Unit Tests for Metrics Collector

메트릭 수집 시스템의 핵심 기능을 테스트합니다.
"""

import pytest
from prometheus_client import CollectorRegistry

from src.tools.metrics_collector import MetricsCollector


class TestMetricsCollector:
    """MetricsCollector 테스트"""
    
    @pytest.fixture
    def collector(self):
        """독립적인 레지스트리를 사용하는 MetricsCollector"""
        registry = CollectorRegistry()
        return MetricsCollector(registry=registry)
    
    def test_track_node_execution_success(self, collector):
        """노드 실행 시간 추적 테스트 - 성공"""
        with collector.track_node_execution('test_node'):
            # 노드 실행 시뮬레이션
            pass
        
        # 메트릭이 기록되었는지 확인
        metrics = collector.get_metrics().decode('utf-8')
        assert 'art_requests_total{endpoint="test_node",status="success"}' in metrics
        assert 'art_response_time_seconds' in metrics
    
    def test_track_node_execution_error(self, collector):
        """노드 실행 시간 추적 테스트 - 에러"""
        with pytest.raises(ValueError):
            with collector.track_node_execution('test_node'):
                raise ValueError("Test error")
        
        # 에러 메트릭이 기록되었는지 확인
        metrics = collector.get_metrics().decode('utf-8')
        assert 'art_requests_total{endpoint="test_node",status="error"}' in metrics
        assert 'art_errors_total{error_type="ValueError",node_name="test_node"}' in metrics
    
    def test_record_search_quality(self, collector):
        """검색 품질 메트릭 기록 테스트"""
        collector.record_search_quality(
            search_type='hotel',
            result_count=5,
            avg_score=0.85
        )
        
        metrics = collector.get_metrics().decode('utf-8')
        assert 'art_search_results_count' in metrics
        assert 'art_search_score' in metrics
    
    def test_record_satisfaction(self, collector):
        """만족도 점수 기록 테스트"""
        collector.record_satisfaction(85.0)
        
        metrics = collector.get_metrics().decode('utf-8')
        assert 'art_satisfaction_score' in metrics
    
    def test_record_ab_assignment(self, collector):
        """A/B 테스트 변형 할당 기록 테스트"""
        collector.record_ab_assignment(
            experiment_name='test_experiment',
            variant_name='variant_a'
        )
        
        metrics = collector.get_metrics().decode('utf-8')
        assert 'art_ab_variant_assignments_total' in metrics
        assert 'experiment_name="test_experiment"' in metrics
        assert 'variant_name="variant_a"' in metrics
    
    def test_active_sessions(self, collector):
        """활성 세션 카운터 테스트"""
        # 세션 증가
        collector.increment_active_sessions()
        collector.increment_active_sessions()
        
        metrics = collector.get_metrics().decode('utf-8')
        assert 'art_active_sessions 2' in metrics
        
        # 세션 감소
        collector.decrement_active_sessions()
        
        metrics = collector.get_metrics().decode('utf-8')
        assert 'art_active_sessions 1' in metrics
    
    def test_multiple_node_executions(self, collector):
        """여러 노드 실행 추적 테스트"""
        nodes = ['query_parser', 'hotel_rag', 'weather_tool']
        
        for node in nodes:
            with collector.track_node_execution(node):
                pass
        
        metrics = collector.get_metrics().decode('utf-8')
        
        for node in nodes:
            assert f'endpoint="{node}"' in metrics
    
    def test_prometheus_format(self, collector):
        """Prometheus 형식 검증"""
        collector.record_satisfaction(90.0)
        
        metrics = collector.get_metrics()
        
        # bytes 타입인지 확인
        assert isinstance(metrics, bytes)
        
        # Prometheus 텍스트 형식인지 확인
        metrics_str = metrics.decode('utf-8')
        assert '# HELP' in metrics_str
        assert '# TYPE' in metrics_str
