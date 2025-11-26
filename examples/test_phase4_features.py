"""
Phase 4 기능 테스트 스크립트

구현된 Phase 4 기능들을 간단히 테스트할 수 있는 스크립트입니다.
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.tools.ab_testing import ABTestingManager
from src.tools.satisfaction_tracker import SatisfactionTracker
from src.tools.metrics_collector import get_metrics_collector
from src.tools.retraining_pipeline import RetrainingPipeline


def test_ab_testing():
    """A/B 테스팅 프레임워크 테스트"""
    print("\n" + "="*60)
    print("1. A/B 테스팅 프레임워크 테스트")
    print("="*60)
    
    ab_manager = ABTestingManager()
    
    # 실험 생성
    try:
        experiment = ab_manager.create_experiment(
            name="test_experiment",
            description="테스트 실험",
            variants=[
                {"name": "variant_a", "config": {"alpha": 0.3}},
                {"name": "variant_b", "config": {"alpha": 0.7}}
            ]
        )
        print(f"✓ 실험 생성 성공: {experiment.name}")
        
        # 실험 시작
        ab_manager.start_experiment("test_experiment")
        print(f"✓ 실험 시작됨")
        
        # 사용자에게 변형 할당
        for i in range(5):
            user_id = f"user_{i}"
            variant = ab_manager.assign_variant("test_experiment", user_id)
            print(f"  - {user_id}: {variant['variant_name']} (alpha={variant['config']['alpha']})")
        
        # 결과 기록
        for i in range(5):
            user_id = f"user_{i}"
            ab_manager.record_result(
                "test_experiment",
                user_id,
                {"satisfaction": 80 + i * 2}
            )
        print(f"✓ 결과 기록 완료")
        
        # 결과 분석
        analysis = ab_manager.analyze_results("test_experiment")
        print(f"✓ 분석 결과:")
        for variant_name, stats in analysis['variants'].items():
            print(f"  - {variant_name}: {stats['sample_size']}개 샘플")
        
    except Exception as e:
        print(f"✗ 오류 발생: {e}")


def test_satisfaction_tracking():
    """만족도 추적 시스템 테스트"""
    print("\n" + "="*60)
    print("2. 만족도 추적 시스템 테스트")
    print("="*60)
    
    tracker = SatisfactionTracker()
    
    try:
        # 명시적 피드백 기록
        tracker.record_explicit_feedback(
            session_id="test_session_1",
            feedback_type="thumbs_up"
        )
        print("✓ 명시적 피드백 기록 (thumbs_up)")
        
        # 암묵적 신호 기록
        tracker.record_implicit_signals(
            session_id="test_session_1",
            signals={
                'conversation_turns': 4,
                'search_refinements': 1,
                'hotels_viewed': 3,
                'weather_available': True,
                'time_to_completion': 5.5
            }
        )
        print("✓ 암묵적 신호 기록")
        
        # 만족도 점수 계산
        score = tracker.calculate_satisfaction_score("test_session_1")
        print(f"✓ 만족도 점수: {score:.1f}/100")
        
        # 평균 만족도
        avg_score = tracker.get_avg_satisfaction(days=7)
        print(f"✓ 최근 7일 평균 만족도: {avg_score:.1f}/100")
        
    except Exception as e:
        print(f"✗ 오류 발생: {e}")


def test_metrics_collector():
    """메트릭 수집 시스템 테스트"""
    print("\n" + "="*60)
    print("3. 메트릭 수집 시스템 테스트")
    print("="*60)
    
    metrics = get_metrics_collector()
    
    try:
        # 노드 실행 시간 추적
        with metrics.track_node_execution('test_node'):
            import time
            time.sleep(0.1)  # 0.1초 대기
        print("✓ 노드 실행 시간 추적 완료")
        
        # 검색 품질 기록
        metrics.record_search_quality(
            search_type='hotel',
            result_count=5,
            avg_score=0.85
        )
        print("✓ 검색 품질 메트릭 기록")
        
        # 만족도 점수 기록
        metrics.record_satisfaction(87.5)
        print("✓ 만족도 점수 기록")
        
        # A/B 변형 할당 기록
        metrics.record_ab_assignment('test_experiment', 'variant_a')
        print("✓ A/B 변형 할당 기록")
        
        # 메트릭 출력
        metrics_output = metrics.get_metrics().decode('utf-8')
        print(f"✓ Prometheus 메트릭 생성 ({len(metrics_output)} bytes)")
        
        # 일부 메트릭 출력
        print("\n메트릭 샘플:")
        for line in metrics_output.split('\n')[:10]:
            if line and not line.startswith('#'):
                print(f"  {line}")
        
    except Exception as e:
        print(f"✗ 오류 발생: {e}")


async def test_retraining_pipeline():
    """재학습 파이프라인 테스트"""
    print("\n" + "="*60)
    print("4. 자동 재학습 파이프라인 테스트")
    print("="*60)
    
    pipeline = RetrainingPipeline()
    
    try:
        # 재학습 트리거 확인
        triggers = pipeline.check_retraining_triggers()
        print("✓ 재학습 트리거 확인:")
        for trigger_name, is_active in triggers.items():
            status = "🔴 활성" if is_active else "⚪ 비활성"
            print(f"  - {trigger_name}: {status}")
        
        # 재학습 필요 여부
        should_retrain = pipeline.should_retrain()
        print(f"\n✓ 재학습 필요: {'예' if should_retrain else '아니오'}")
        
        # 재학습 실행 (테스트)
        if should_retrain:
            result = await pipeline.execute_retraining()
            print(f"✓ 재학습 실행 결과: {result['status']}")
        
    except Exception as e:
        print(f"✗ 오류 발생: {e}")


def main():
    """메인 함수"""
    print("\n" + "="*60)
    print("Phase 4 Production Ready 기능 테스트")
    print("="*60)
    
    # 1. A/B 테스팅
    test_ab_testing()
    
    # 2. 만족도 추적
    test_satisfaction_tracking()
    
    # 3. 메트릭 수집
    test_metrics_collector()
    
    # 4. 재학습 파이프라인
    asyncio.run(test_retraining_pipeline())
    
    print("\n" + "="*60)
    print("테스트 완료!")
    print("="*60)
    print("\n다음 단계:")
    print("1. 모니터링 대시보드 실행:")
    print("   docker-compose -f docker-compose.monitoring.yml up -d")
    print("   streamlit run src/tools/monitoring_dashboard.py")
    print("\n2. 전체 단위 테스트 실행:")
    print("   pytest tests/unit/test_ab_testing.py -v")
    print("   pytest tests/unit/test_satisfaction_tracker.py -v")
    print("   pytest tests/unit/test_metrics_collector.py -v")
    print("   pytest tests/unit/test_retraining_pipeline.py -v")
    print()


if __name__ == "__main__":
    main()
