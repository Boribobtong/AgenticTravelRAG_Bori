"""
Unit Tests for A/B Testing Framework

A/B 테스팅 프레임워크의 핵심 기능을 테스트합니다.
"""

import pytest
import os
import tempfile
from datetime import datetime

from src.tools.ab_testing import (
    ABTestingManager,
    Experiment,
    Variant,
    ExperimentStatus,
    ABTestDatabase
)
from src.tools.ab_testing_stats import (
    calculate_mean,
    calculate_std_dev,
    t_test,
    calculate_confidence_interval
)


class TestABTestingManager:
    """ABTestingManager 테스트"""
    
    @pytest.fixture
    def temp_db(self):
        """임시 데이터베이스"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.fixture
    def ab_manager(self, temp_db):
        """ABTestingManager 인스턴스"""
        return ABTestingManager(db_path=temp_db)
    
    def test_create_experiment(self, ab_manager):
        """실험 생성 테스트"""
        experiment = ab_manager.create_experiment(
            name="test_experiment",
            description="Test experiment",
            variants=[
                {"name": "control", "config": {"alpha": 0.5}},
                {"name": "treatment", "config": {"alpha": 0.7}}
            ],
            traffic_split=[0.5, 0.5]
        )
        
        assert experiment.name == "test_experiment"
        assert len(experiment.variants) == 2
        assert experiment.status == ExperimentStatus.DRAFT
    
    def test_traffic_split_validation(self, ab_manager):
        """트래픽 분할 검증 테스트"""
        with pytest.raises(ValueError):
            ab_manager.create_experiment(
                name="invalid_experiment",
                description="Invalid traffic split",
                variants=[
                    {"name": "v1", "config": {}},
                    {"name": "v2", "config": {}}
                ],
                traffic_split=[0.3, 0.3]  # 합이 1.0이 아님
            )
    
    def test_assign_variant_consistency(self, ab_manager):
        """변형 할당 일관성 테스트"""
        # 실험 생성 및 시작
        ab_manager.create_experiment(
            name="consistency_test",
            description="Test consistency",
            variants=[
                {"name": "v1", "config": {"alpha": 0.3}},
                {"name": "v2", "config": {"alpha": 0.7}}
            ]
        )
        ab_manager.start_experiment("consistency_test")
        
        # 같은 사용자는 항상 같은 변형을 받아야 함
        user_id = "user_123"
        variant1 = ab_manager.assign_variant("consistency_test", user_id)
        variant2 = ab_manager.assign_variant("consistency_test", user_id)
        variant3 = ab_manager.assign_variant("consistency_test", user_id)
        
        assert variant1['variant_name'] == variant2['variant_name']
        assert variant2['variant_name'] == variant3['variant_name']
    
    def test_traffic_distribution(self, ab_manager):
        """트래픽 분할 비율 테스트"""
        ab_manager.create_experiment(
            name="distribution_test",
            description="Test traffic distribution",
            variants=[
                {"name": "v1", "config": {}},
                {"name": "v2", "config": {}}
            ],
            traffic_split=[0.5, 0.5]
        )
        ab_manager.start_experiment("distribution_test")
        
        # 1000명의 사용자에게 변형 할당
        assignments = {}
        for i in range(1000):
            user_id = f"user_{i}"
            variant = ab_manager.assign_variant("distribution_test", user_id)
            variant_name = variant['variant_name']
            assignments[variant_name] = assignments.get(variant_name, 0) + 1
        
        # 각 변형이 대략 50%씩 할당되어야 함 (±10% 허용)
        for variant_name, count in assignments.items():
            ratio = count / 1000
            assert 0.4 <= ratio <= 0.6, f"Variant {variant_name} ratio {ratio} out of range"
    
    def test_record_and_analyze_results(self, ab_manager):
        """결과 기록 및 분석 테스트"""
        ab_manager.create_experiment(
            name="results_test",
            description="Test results",
            variants=[
                {"name": "control", "config": {}},
                {"name": "treatment", "config": {}}
            ]
        )
        ab_manager.start_experiment("results_test")
        
        # 결과 기록
        for i in range(10):
            user_id = f"user_{i}"
            variant = ab_manager.assign_variant("results_test", user_id)
            
            # 모의 메트릭
            metrics = {
                'satisfaction_score': 80 + i,
                'response_time': 2.0 + i * 0.1
            }
            ab_manager.record_result("results_test", user_id, metrics)
        
        # 결과 분석
        analysis = ab_manager.analyze_results("results_test")
        
        assert 'variants' in analysis
        assert analysis['total_samples'] == 10


class TestStatisticalFunctions:
    """통계 함수 테스트"""
    
    def test_calculate_mean(self):
        """평균 계산 테스트"""
        values = [1, 2, 3, 4, 5]
        assert calculate_mean(values) == 3.0
        
        assert calculate_mean([]) == 0.0
        assert calculate_mean([10]) == 10.0
    
    def test_calculate_std_dev(self):
        """표준편차 계산 테스트"""
        values = [2, 4, 4, 4, 5, 5, 7, 9]
        std_dev = calculate_std_dev(values)
        assert 1.5 < std_dev < 2.5  # 근사값 확인
    
    def test_t_test(self):
        """t-검정 테스트"""
        group_a = [85, 87, 86, 88, 90, 89, 87, 86]
        group_b = [75, 77, 76, 78, 74, 76, 75, 77]
        
        result = t_test(group_a, group_b)
        
        assert 't_statistic' in result
        assert 't_statistic' in result
        assert 'p_value' in result
        assert 'significant' in result
        
        # group_a가 group_b보다 명확히 높으므로 유의해야 함
        assert result['significant'] is True
    
    def test_confidence_interval(self):
        """신뢰구간 계산 테스트"""
        values = [85, 87, 86, 88, 90, 89, 87, 86]
        ci = calculate_confidence_interval(values, confidence_level=0.95)
        
        assert 'mean' in ci
        assert 'lower' in ci
        assert 'upper' in ci
        
        mean = calculate_mean(values)
        assert ci['lower'] < mean < ci['upper']


class TestABTestDatabase:
    """ABTestDatabase 테스트"""
    
    @pytest.fixture
    def temp_db(self):
        """임시 데이터베이스"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.fixture
    def db(self, temp_db):
        """ABTestDatabase 인스턴스"""
        return ABTestDatabase(db_path=temp_db)
    
    def test_save_and_get_experiment(self, db):
        """실험 저장 및 조회 테스트"""
        experiment = Experiment(
            name="test_exp",
            description="Test",
            variants=[
                Variant(name="v1", config={}, traffic_weight=0.5),
                Variant(name="v2", config={}, traffic_weight=0.5)
            ],
            status=ExperimentStatus.ACTIVE,
            created_at=datetime.now()
        )
        
        db.save_experiment(experiment)
        retrieved = db.get_experiment("test_exp")
        
        assert retrieved is not None
        assert retrieved.name == "test_exp"
        assert len(retrieved.variants) == 2
    
    def test_assignment_persistence(self, db):
        """할당 영속성 테스트"""
        db.save_assignment("exp1", "user1", "variant_a")
        
        assignment = db.get_assignment("exp1", "user1")
        assert assignment == "variant_a"
        
        # 존재하지 않는 할당
        assert db.get_assignment("exp1", "user2") is None
