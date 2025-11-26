"""
Unit Tests for Retraining Pipeline

재학습 파이프라인의 핵심 기능을 테스트합니다.
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta

from src.tools.retraining_pipeline import RetrainingPipeline, ModelRegistry
from src.tools.data_quality_monitor import DataQualityMonitor


class TestRetrainingPipeline:
    """RetrainingPipeline 테스트"""
    
    @pytest.fixture
    def pipeline(self):
        """RetrainingPipeline 인스턴스"""
        return RetrainingPipeline()
    
    def test_check_retraining_triggers(self, pipeline):
        """재학습 트리거 확인 테스트"""
        triggers = pipeline.check_retraining_triggers()
        
        assert isinstance(triggers, dict)
        assert 'data_drift' in triggers
        assert 'performance_degradation' in triggers
        assert 'new_data_threshold' in triggers
        assert 'scheduled_time' in triggers
    
    def test_should_retrain(self, pipeline):
        """재학습 필요 여부 판단 테스트"""
        should_retrain = pipeline.should_retrain()
        
        assert isinstance(should_retrain, bool)
    
    @pytest.mark.asyncio
    async def test_execute_retraining(self, pipeline):
        """재학습 실행 테스트"""
        result = await pipeline.execute_retraining()
        
        assert 'status' in result
        assert 'timestamp' in result


class TestModelRegistry:
    """ModelRegistry 테스트"""
    
    @pytest.fixture
    def registry(self):
        """ModelRegistry 인스턴스"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield ModelRegistry(registry_path=tmpdir)
    
    def test_register_model(self, registry):
        """모델 등록 테스트"""
        model_info = registry.register_model(
            version='1.0.1',
            metrics={'accuracy': 0.95, 'f1_score': 0.93}
        )
        
        assert model_info['version'] == '1.0.1'
        assert 'timestamp' in model_info
        assert model_info['status'] == 'active'
    
    def test_get_active_model(self, registry):
        """활성 모델 조회 테스트"""
        active_model = registry.get_active_model()
        
        assert active_model is not None
        assert 'version' in active_model
        assert 'status' in active_model


class TestDataQualityMonitor:
    """DataQualityMonitor 테스트"""
    
    @pytest.fixture
    def temp_db(self):
        """임시 데이터베이스"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.fixture
    def monitor(self, temp_db):
        """DataQualityMonitor 인스턴스"""
        return DataQualityMonitor(db_path=temp_db)
    
    def test_record_query(self, monitor):
        """쿼리 기록 테스트"""
        monitor.record_query(
            query_text="파리 호텔 추천",
            destination="Paris",
            result_count=5,
            avg_score=0.85
        )
        
        # 쿼리가 기록되었는지 확인
        recent_queries = monitor.get_recent_queries(days=1)
        assert len(recent_queries) > 0
    
    def test_calculate_drift(self, monitor):
        """드리프트 계산 테스트"""
        # 샘플 쿼리 기록
        for i in range(10):
            monitor.record_query(
                query_text=f"Query {i}",
                destination="Paris" if i < 5 else "Seoul",
                result_count=3,
                avg_score=0.8
            )
        
        recent_queries = monitor.get_recent_queries(days=7)
        drift_score = monitor.calculate_drift(recent_queries)
        
        assert isinstance(drift_score, float)
        assert 0.0 <= drift_score <= 1.0
    
    def test_prepare_training_data(self, monitor):
        """학습 데이터 준비 테스트"""
        # 샘플 쿼리 기록
        monitor.record_query(
            query_text="Test query",
            destination="Paris",
            result_count=3,
            avg_score=0.85
        )
        
        training_data = monitor.prepare_training_data()
        
        assert 'query_count' in training_data
        assert 'unique_destinations' in training_data
        assert 'timestamp' in training_data
