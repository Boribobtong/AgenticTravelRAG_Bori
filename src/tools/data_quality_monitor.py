"""
Data Quality Monitor

데이터 품질을 모니터링하고 드리프트를 감지하는 시스템입니다.
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class DataQualityMonitor:
    """데이터 품질 모니터링"""
    
    def __init__(self, db_path: str = "data/quality_monitor.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """데이터베이스 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS query_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_text TEXT,
                    destination TEXT,
                    timestamp TEXT,
                    result_count INTEGER,
                    avg_score REAL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS drift_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT,
                    value REAL,
                    timestamp TEXT
                )
            """)
            
            conn.commit()
    
    def record_query(
        self,
        query_text: str,
        destination: str,
        result_count: int,
        avg_score: float
    ):
        """쿼리 통계 기록"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO query_stats 
                (query_text, destination, timestamp, result_count, avg_score)
                VALUES (?, ?, ?, ?, ?)
            """, (
                query_text,
                destination,
                datetime.now().isoformat(),
                result_count,
                avg_score
            ))
            conn.commit()
    
    def get_recent_queries(self, days: int = 7) -> List[str]:
        """최근 N일 쿼리 조회"""
        start_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT query_text FROM query_stats
                WHERE timestamp >= ?
            """, (start_date.isoformat(),))
            
            return [row[0] for row in cursor.fetchall()]
    
    def calculate_drift(self, recent_queries: List[str]) -> float:
        """
        데이터 드리프트 점수 계산
        
        간단한 구현: 최근 쿼리의 고유 목적지 비율 변화
        실제로는 임베딩 기반 분포 비교 필요
        
        Returns:
            드리프트 점수 (0-1, 높을수록 드리프트 심함)
        """
        if not recent_queries:
            return 0.0
        
        # 최근 7일 vs 이전 30일 목적지 분포 비교
        recent_7d = self.get_destination_distribution(days=7)
        baseline_30d = self.get_destination_distribution(days=30)
        
        # 간단한 KL divergence 근사
        drift_score = 0.0
        all_destinations = set(recent_7d.keys()) | set(baseline_30d.keys())
        
        for dest in all_destinations:
            p = recent_7d.get(dest, 0.001)  # 스무딩
            q = baseline_30d.get(dest, 0.001)
            drift_score += p * (p / q if q > 0 else 1.0)
        
        # 정규화 (0-1 범위)
        drift_score = min(drift_score / len(all_destinations), 1.0)
        
        # 드리프트 메트릭 기록
        self.record_drift_metric('destination_drift', drift_score)
        
        return drift_score
    
    def get_destination_distribution(self, days: int) -> Dict[str, float]:
        """목적지 분포 조회"""
        start_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT destination, COUNT(*) as count
                FROM query_stats
                WHERE timestamp >= ?
                GROUP BY destination
            """, (start_date.isoformat(),))
            
            results = cursor.fetchall()
            total = sum(count for _, count in results)
            
            if total == 0:
                return {}
            
            return {dest: count / total for dest, count in results}
    
    def record_drift_metric(self, metric_name: str, value: float):
        """드리프트 메트릭 기록"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO drift_metrics (metric_name, value, timestamp)
                VALUES (?, ?, ?)
            """, (metric_name, value, datetime.now().isoformat()))
            conn.commit()
    
    def get_avg_satisfaction(self, days: int) -> float:
        """
        평균 만족도 조회 (SatisfactionTracker에서 가져옴)
        
        실제 구현에서는 SatisfactionTracker와 통합 필요
        """
        # 임시 구현
        return 85.0
    
    def count_new_feedback(self) -> int:
        """
        마지막 학습 이후 신규 피드백 수
        
        실제 구현에서는 모델 레지스트리와 통합 필요
        """
        # 임시 구현
        return 1500
    
    def prepare_training_data(self) -> Dict[str, Any]:
        """
        재학습용 데이터 준비
        
        Returns:
            학습 데이터 메타데이터
        """
        recent_queries = self.get_recent_queries(days=30)
        
        return {
            'query_count': len(recent_queries),
            'unique_destinations': len(set(self.get_destination_distribution(30).keys())),
            'timestamp': datetime.now().isoformat()
        }
