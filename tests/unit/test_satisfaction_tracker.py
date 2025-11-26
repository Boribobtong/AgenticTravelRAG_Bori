"""
Unit Tests for Satisfaction Tracking System

만족도 추적 시스템의 핵심 기능을 테스트합니다.
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta

from src.tools.satisfaction_tracker import (
    SatisfactionTracker,
    SatisfactionDatabase,
    ExplicitFeedback,
    ImplicitSignals,
    FeedbackType
)


class TestSatisfactionTracker:
    """SatisfactionTracker 테스트"""
    
    @pytest.fixture
    def temp_db(self):
        """임시 데이터베이스"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.fixture
    def tracker(self, temp_db):
        """SatisfactionTracker 인스턴스"""
        return SatisfactionTracker(db_path=temp_db)
    
    def test_record_explicit_feedback_thumbs_up(self, tracker):
        """명시적 피드백 기록 테스트 - Thumbs Up"""
        tracker.record_explicit_feedback(
            session_id="session_1",
            feedback_type="thumbs_up"
        )
        
        # 만족도 점수 계산
        score = tracker.calculate_satisfaction_score("session_1")
        
        # Thumbs up은 100점이므로, 명시적 피드백만 있으면 60점 (가중치 0.6)
        assert score >= 50.0  # 암묵적 신호가 없어도 최소 50점
    
    def test_record_explicit_feedback_rating(self, tracker):
        """명시적 피드백 기록 테스트 - 별점"""
        tracker.record_explicit_feedback(
            session_id="session_2",
            feedback_type="rating",
            value=4.0  # 5점 만점에 4점
        )
        
        score = tracker.calculate_satisfaction_score("session_2")
        
        # 4/5 * 100 = 80점, 가중치 0.6 적용하면 48점
        assert score >= 40.0
    
    def test_record_implicit_signals(self, tracker):
        """암묵적 신호 기록 테스트"""
        tracker.record_implicit_signals(
            session_id="session_3",
            signals={
                'conversation_turns': 4,  # 이상적 범위 (3-5)
                'search_refinements': 0,  # 재검색 없음
                'hotels_viewed': 3,  # 적절한 수
                'weather_available': True,
                'time_to_completion': 5.0  # 이상적 범위 (3-10초)
            }
        )
        
        score = tracker.calculate_satisfaction_score("session_3")
        
        # 모든 암묵적 신호가 이상적이므로 높은 점수 예상
        assert score >= 80.0
    
    def test_combined_feedback_and_signals(self, tracker):
        """명시적 피드백 + 암묵적 신호 조합 테스트"""
        session_id = "session_4"
        
        # 명시적 피드백: Thumbs up (100점)
        tracker.record_explicit_feedback(
            session_id=session_id,
            feedback_type="thumbs_up"
        )
        
        # 암묵적 신호: 이상적 조건
        tracker.record_implicit_signals(
            session_id=session_id,
            signals={
                'conversation_turns': 4,
                'search_refinements': 0,
                'hotels_viewed': 4,
                'weather_available': True,
                'time_to_completion': 6.0
            }
        )
        
        score = tracker.calculate_satisfaction_score(session_id)
        
        # 0.6 * 100 + 0.4 * ~100 = ~100점
        assert score >= 90.0
    
    def test_poor_satisfaction_signals(self, tracker):
        """낮은 만족도 신호 테스트"""
        session_id = "session_5"
        
        # 명시적 피드백: Thumbs down (0점)
        tracker.record_explicit_feedback(
            session_id=session_id,
            feedback_type="thumbs_down"
        )
        
        # 암묵적 신호: 좋지 않은 조건
        tracker.record_implicit_signals(
            session_id=session_id,
            signals={
                'conversation_turns': 15,  # 너무 많음
                'search_refinements': 5,  # 재검색 많음
                'hotels_viewed': 1,  # 선택지 부족
                'weather_available': False,
                'time_to_completion': 25.0  # 너무 느림
            }
        )
        
        score = tracker.calculate_satisfaction_score(session_id)
        
        # 낮은 점수 예상
        assert score <= 50.0
    
    def test_get_avg_satisfaction(self, tracker):
        """평균 만족도 조회 테스트"""
        # 여러 세션의 피드백 기록
        for i in range(5):
            session_id = f"session_{i}"
            tracker.record_explicit_feedback(
                session_id=session_id,
                feedback_type="rating",
                value=4.0
            )
            tracker.calculate_satisfaction_score(session_id)
        
        # 최근 7일 평균 만족도
        avg_score = tracker.get_avg_satisfaction(days=7)
        
        # 모두 4/5 별점이므로 평균 약 80점 (가중치 고려)
        assert avg_score >= 40.0


class TestSatisfactionDatabase:
    """SatisfactionDatabase 테스트"""
    
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
        """SatisfactionDatabase 인스턴스"""
        return SatisfactionDatabase(db_path=temp_db)
    
    def test_save_and_get_explicit_feedback(self, db):
        """명시적 피드백 저장 및 조회 테스트"""
        feedback = ExplicitFeedback(
            session_id="test_session",
            feedback_type=FeedbackType.THUMBS_UP,
            value=None,
            timestamp=datetime.now(),
            comment="Great service!"
        )
        
        db.save_explicit_feedback(feedback)
        retrieved = db.get_explicit_feedback("test_session")
        
        assert retrieved is not None
        assert retrieved.session_id == "test_session"
        assert retrieved.feedback_type == FeedbackType.THUMBS_UP
        assert retrieved.comment == "Great service!"
    
    def test_save_and_get_implicit_signals(self, db):
        """암묵적 신호 저장 및 조회 테스트"""
        signals = ImplicitSignals(
            session_id="test_session",
            conversation_turns=5,
            search_refinements=1,
            hotels_viewed=3,
            weather_available=True,
            time_to_completion=7.5,
            timestamp=datetime.now()
        )
        
        db.save_implicit_signals(signals)
        retrieved = db.get_implicit_signals("test_session")
        
        assert retrieved is not None
        assert retrieved.session_id == "test_session"
        assert retrieved.conversation_turns == 5
        assert retrieved.search_refinements == 1
        assert retrieved.weather_available is True
    
    def test_satisfaction_trends(self, db):
        """만족도 추세 테스트"""
        # 여러 날짜에 걸쳐 만족도 점수 저장
        for i in range(5):
            db.save_satisfaction_score(
                session_id=f"session_{i}",
                score=80.0 + i,
                explicit_component=100.0,
                implicit_component=60.0 + i
            )
        
        # 추세 조회
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now() + timedelta(days=1)
        
        trends = db.get_satisfaction_trends(start_date, end_date)
        
        assert len(trends) > 0
        assert 'avg_score' in trends[0]
        assert 'count' in trends[0]


class TestSatisfactionScoreCalculation:
    """만족도 점수 계산 로직 테스트"""
    
    @pytest.fixture
    def temp_db(self):
        """임시 데이터베이스"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.fixture
    def tracker(self, temp_db):
        """SatisfactionTracker 인스턴스"""
        return SatisfactionTracker(db_path=temp_db)
    
    def test_ideal_conversation_turns(self, tracker):
        """이상적 대화 턴 수 테스트"""
        tracker.record_implicit_signals(
            session_id="ideal_turns",
            signals={
                'conversation_turns': 4,  # 이상적 (3-5)
                'search_refinements': 0,
                'hotels_viewed': 3,
                'weather_available': True,
                'time_to_completion': 5.0
            }
        )
        
        score = tracker.calculate_satisfaction_score("ideal_turns")
        assert score >= 80.0
    
    def test_too_many_turns(self, tracker):
        """너무 많은 대화 턴 테스트"""
        tracker.record_implicit_signals(
            session_id="many_turns",
            signals={
                'conversation_turns': 15,  # 너무 많음
                'search_refinements': 0,
                'hotels_viewed': 3,
                'weather_available': True,
                'time_to_completion': 5.0
            }
        )
        
        score = tracker.calculate_satisfaction_score("many_turns")
        # 대화 턴이 많으면 점수 감소 (하지만 다른 신호가 좋으면 여전히 높을 수 있음)
        assert score < 90.0
    
    def test_multiple_refinements(self, tracker):
        """여러 번의 재검색 테스트"""
        tracker.record_implicit_signals(
            session_id="refinements",
            signals={
                'conversation_turns': 4,
                'search_refinements': 4,  # 많은 재검색
                'hotels_viewed': 3,
                'weather_available': True,
                'time_to_completion': 5.0
            }
        )
        
        score = tracker.calculate_satisfaction_score("refinements")
        # 재검색이 많으면 점수 감소
        assert score < 80.0
