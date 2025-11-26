"""
User Satisfaction Tracking System

사용자 만족도를 추적하고 분석하는 시스템입니다.
명시적 피드백(thumbs up/down, 별점)과 암묵적 신호(대화 길이, 재검색 횟수)를 수집합니다.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """피드백 유형"""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    RATING = "rating"  # 1-5 별점


@dataclass
class ExplicitFeedback:
    """명시적 피드백"""
    session_id: str
    feedback_type: FeedbackType
    value: Optional[float]  # 별점의 경우 1-5
    timestamp: datetime
    comment: Optional[str] = None


@dataclass
class ImplicitSignals:
    """암묵적 신호"""
    session_id: str
    conversation_turns: int
    search_refinements: int
    hotels_viewed: int
    weather_available: bool
    time_to_completion: float  # 초 단위
    timestamp: datetime


class SatisfactionDatabase:
    """만족도 데이터베이스"""
    
    def __init__(self, db_path: str = "data/satisfaction.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """데이터베이스 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS explicit_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    feedback_type TEXT,
                    value REAL,
                    comment TEXT,
                    timestamp TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS implicit_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    conversation_turns INTEGER,
                    search_refinements INTEGER,
                    hotels_viewed INTEGER,
                    weather_available INTEGER,
                    time_to_completion REAL,
                    timestamp TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS satisfaction_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE,
                    score REAL,
                    explicit_component REAL,
                    implicit_component REAL,
                    calculated_at TEXT
                )
            """)
            
            conn.commit()
    
    def save_explicit_feedback(self, feedback: ExplicitFeedback):
        """명시적 피드백 저장"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO explicit_feedback 
                (session_id, feedback_type, value, comment, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                feedback.session_id,
                feedback.feedback_type.value,
                feedback.value,
                feedback.comment,
                feedback.timestamp.isoformat()
            ))
            conn.commit()
    
    def save_implicit_signals(self, signals: ImplicitSignals):
        """암묵적 신호 저장"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO implicit_signals 
                (session_id, conversation_turns, search_refinements, 
                 hotels_viewed, weather_available, time_to_completion, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                signals.session_id,
                signals.conversation_turns,
                signals.search_refinements,
                signals.hotels_viewed,
                1 if signals.weather_available else 0,
                signals.time_to_completion,
                signals.timestamp.isoformat()
            ))
            conn.commit()
    
    def save_satisfaction_score(
        self,
        session_id: str,
        score: float,
        explicit_component: float,
        implicit_component: float
    ):
        """만족도 점수 저장"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO satisfaction_scores 
                (session_id, score, explicit_component, implicit_component, calculated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                score,
                explicit_component,
                implicit_component,
                datetime.now().isoformat()
            ))
            conn.commit()
    
    def get_explicit_feedback(self, session_id: str) -> Optional[ExplicitFeedback]:
        """명시적 피드백 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT session_id, feedback_type, value, comment, timestamp
                FROM explicit_feedback
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (session_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return ExplicitFeedback(
                session_id=row[0],
                feedback_type=FeedbackType(row[1]),
                value=row[2],
                comment=row[3],
                timestamp=datetime.fromisoformat(row[4])
            )
    
    def get_implicit_signals(self, session_id: str) -> Optional[ImplicitSignals]:
        """암묵적 신호 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT session_id, conversation_turns, search_refinements,
                       hotels_viewed, weather_available, time_to_completion, timestamp
                FROM implicit_signals
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (session_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return ImplicitSignals(
                session_id=row[0],
                conversation_turns=row[1],
                search_refinements=row[2],
                hotels_viewed=row[3],
                weather_available=bool(row[4]),
                time_to_completion=row[5],
                timestamp=datetime.fromisoformat(row[6])
            )
    
    def get_satisfaction_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "daily"
    ) -> List[Dict[str, Any]]:
        """만족도 추세 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DATE(calculated_at) as date, AVG(score) as avg_score, COUNT(*) as count
                FROM satisfaction_scores
                WHERE calculated_at BETWEEN ? AND ?
                GROUP BY DATE(calculated_at)
                ORDER BY date
            """, (start_date.isoformat(), end_date.isoformat()))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'date': row[0],
                    'avg_score': row[1],
                    'count': row[2]
                })
            
            return results
    
    def get_avg_satisfaction(self, days: int) -> float:
        """최근 N일 평균 만족도"""
        start_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT AVG(score)
                FROM satisfaction_scores
                WHERE calculated_at >= ?
            """, (start_date.isoformat(),))
            row = cursor.fetchone()
            
            return row[0] if row[0] is not None else 0.0


class SatisfactionTracker:
    """사용자 만족도 추적 시스템"""
    
    def __init__(self, db_path: str = "data/satisfaction.db"):
        self.db = SatisfactionDatabase(db_path)
    
    def record_explicit_feedback(
        self,
        session_id: str,
        feedback_type: str,
        value: Optional[float] = None,
        comment: Optional[str] = None
    ):
        """
        명시적 피드백 기록
        
        Args:
            session_id: 세션 ID
            feedback_type: "thumbs_up", "thumbs_down", "rating"
            value: 별점 (1-5, rating 타입인 경우만)
            comment: 추가 코멘트
        """
        try:
            feedback_enum = FeedbackType(feedback_type)
        except ValueError:
            logger.error(f"Invalid feedback type: {feedback_type}")
            return
        
        feedback = ExplicitFeedback(
            session_id=session_id,
            feedback_type=feedback_enum,
            value=value,
            timestamp=datetime.now(),
            comment=comment
        )
        
        self.db.save_explicit_feedback(feedback)
        logger.info(f"Recorded explicit feedback: {session_id} - {feedback_type}")
    
    def record_implicit_signals(
        self,
        session_id: str,
        signals: Dict[str, Any]
    ):
        """
        암묵적 신호 기록
        
        Args:
            session_id: 세션 ID
            signals: {
                'conversation_turns': int,
                'search_refinements': int,
                'hotels_viewed': int,
                'weather_available': bool,
                'time_to_completion': float
            }
        """
        implicit_signals = ImplicitSignals(
            session_id=session_id,
            conversation_turns=signals.get('conversation_turns', 0),
            search_refinements=signals.get('search_refinements', 0),
            hotels_viewed=signals.get('hotels_viewed', 0),
            weather_available=signals.get('weather_available', False),
            time_to_completion=signals.get('time_to_completion', 0.0),
            timestamp=datetime.now()
        )
        
        self.db.save_implicit_signals(implicit_signals)
        logger.info(f"Recorded implicit signals: {session_id}")
    
    def calculate_satisfaction_score(self, session_id: str) -> float:
        """
        종합 만족도 점수 계산 (0-100)
        
        만족도 점수 = 0.6 * 명시적_피드백 + 0.4 * 암묵적_신호
        
        명시적 피드백:
        - 👍: 100점
        - 👎: 0점
        - 별점: (rating / 5) * 100
        
        암묵적 신호:
        - 대화 턴 수: 3-5턴 = 100점, 10턴+ = 50점
        - 재검색 횟수: 0-1회 = 100점, 3회+ = 30점
        - 완료 시간: 적정 시간 내 = 100점
        """
        # 명시적 피드백 점수
        explicit_score = self._calculate_explicit_score(session_id)
        
        # 암묵적 신호 점수
        implicit_score = self._calculate_implicit_score(session_id)
        
        # 가중 평균
        if explicit_score is not None and implicit_score is not None:
            total_score = 0.6 * explicit_score + 0.4 * implicit_score
        elif explicit_score is not None:
            total_score = explicit_score
        elif implicit_score is not None:
            total_score = implicit_score
        else:
            total_score = 50.0  # 기본값
        
        # 저장
        self.db.save_satisfaction_score(
            session_id=session_id,
            score=total_score,
            explicit_component=explicit_score or 0.0,
            implicit_component=implicit_score or 0.0
        )
        
        return total_score
    
    def _calculate_explicit_score(self, session_id: str) -> Optional[float]:
        """명시적 피드백 점수 계산"""
        feedback = self.db.get_explicit_feedback(session_id)
        
        if not feedback:
            return None
        
        if feedback.feedback_type == FeedbackType.THUMBS_UP:
            return 100.0
        elif feedback.feedback_type == FeedbackType.THUMBS_DOWN:
            return 0.0
        elif feedback.feedback_type == FeedbackType.RATING:
            if feedback.value:
                return (feedback.value / 5.0) * 100.0
        
        return None
    
    def _calculate_implicit_score(self, session_id: str) -> Optional[float]:
        """암묵적 신호 점수 계산"""
        signals = self.db.get_implicit_signals(session_id)
        
        if not signals:
            return None
        
        # 대화 턴 수 점수 (3-5턴이 이상적)
        turns = signals.conversation_turns
        if 3 <= turns <= 5:
            turn_score = 100.0
        elif turns < 3:
            turn_score = 70.0  # 너무 짧음
        elif turns <= 7:
            turn_score = 85.0
        elif turns <= 10:
            turn_score = 70.0
        else:
            turn_score = 50.0  # 너무 많음 (불만족)
        
        # 재검색 횟수 점수 (적을수록 좋음)
        refinements = signals.search_refinements
        if refinements == 0:
            refinement_score = 100.0
        elif refinements == 1:
            refinement_score = 85.0
        elif refinements == 2:
            refinement_score = 60.0
        else:
            refinement_score = 30.0
        
        # 호텔 조회 수 점수 (적절한 수가 좋음)
        hotels = signals.hotels_viewed
        if 3 <= hotels <= 5:
            hotel_score = 100.0
        elif hotels < 3:
            hotel_score = 60.0  # 선택지 부족
        else:
            hotel_score = 80.0  # 많은 선택지
        
        # 날씨 정보 가용성 (있으면 보너스)
        weather_score = 100.0 if signals.weather_available else 80.0
        
        # 완료 시간 점수 (3-10초가 이상적)
        time = signals.time_to_completion
        if 3 <= time <= 10:
            time_score = 100.0
        elif time < 3:
            time_score = 90.0  # 빠름
        elif time <= 15:
            time_score = 80.0
        else:
            time_score = 60.0  # 느림
        
        # 가중 평균
        implicit_score = (
            turn_score * 0.3 +
            refinement_score * 0.3 +
            hotel_score * 0.2 +
            weather_score * 0.1 +
            time_score * 0.1
        )
        
        return implicit_score
    
    def get_satisfaction_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "daily"
    ) -> List[Dict[str, Any]]:
        """만족도 추세 분석"""
        return self.db.get_satisfaction_trends(start_date, end_date, granularity)
    
    def get_avg_satisfaction(self, days: int = 7) -> float:
        """최근 N일 평균 만족도"""
        return self.db.get_avg_satisfaction(days)
