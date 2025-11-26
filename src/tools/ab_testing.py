"""
A/B Testing Framework for AgenticTravelRAG

실험 설정, 트래픽 분할, 결과 수집 및 통계 분석을 제공하는 A/B 테스팅 프레임워크입니다.
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """실험 상태"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class Variant:
    """실험 변형"""
    name: str
    config: Dict[str, Any]
    traffic_weight: float
    description: str = ""


@dataclass
class Experiment:
    """A/B 테스트 실험"""
    name: str
    description: str
    variants: List[Variant]
    status: ExperimentStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        
        # 트래픽 가중치 합이 1.0인지 검증
        total_weight = sum(v.traffic_weight for v in self.variants)
        if not (0.99 <= total_weight <= 1.01):  # 부동소수점 오차 허용
            raise ValueError(f"Traffic weights must sum to 1.0, got {total_weight}")


class ABTestDatabase:
    """A/B 테스트 데이터베이스"""
    
    def __init__(self, db_path: str = "data/ab_tests.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """데이터베이스 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    name TEXT PRIMARY KEY,
                    description TEXT,
                    variants TEXT,
                    status TEXT,
                    created_at TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_name TEXT,
                    user_id TEXT,
                    variant_name TEXT,
                    assigned_at TEXT,
                    UNIQUE(experiment_name, user_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_name TEXT,
                    user_id TEXT,
                    variant_name TEXT,
                    metrics TEXT,
                    recorded_at TEXT
                )
            """)
            
            conn.commit()
    
    def save_experiment(self, experiment: Experiment):
        """실험 저장"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO experiments 
                (name, description, variants, status, created_at, started_at, completed_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                experiment.name,
                experiment.description,
                json.dumps([asdict(v) for v in experiment.variants]),
                experiment.status.value,
                experiment.created_at.isoformat(),
                experiment.started_at.isoformat() if experiment.started_at else None,
                experiment.completed_at.isoformat() if experiment.completed_at else None,
                json.dumps(experiment.metadata)
            ))
            conn.commit()
    
    def get_experiment(self, name: str) -> Optional[Experiment]:
        """실험 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM experiments WHERE name = ?",
                (name,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            variants_data = json.loads(row[2])
            variants = [Variant(**v) for v in variants_data]
            
            return Experiment(
                name=row[0],
                description=row[1],
                variants=variants,
                status=ExperimentStatus(row[3]),
                created_at=datetime.fromisoformat(row[4]),
                started_at=datetime.fromisoformat(row[5]) if row[5] else None,
                completed_at=datetime.fromisoformat(row[6]) if row[6] else None,
                metadata=json.loads(row[7]) if row[7] else {}
            )
    
    def save_assignment(self, experiment_name: str, user_id: str, variant_name: str):
        """사용자 변형 할당 저장"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO assignments 
                (experiment_name, user_id, variant_name, assigned_at)
                VALUES (?, ?, ?, ?)
            """, (experiment_name, user_id, variant_name, datetime.now().isoformat()))
            conn.commit()
    
    def get_assignment(self, experiment_name: str, user_id: str) -> Optional[str]:
        """사용자 변형 할당 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT variant_name FROM assignments 
                WHERE experiment_name = ? AND user_id = ?
            """, (experiment_name, user_id))
            row = cursor.fetchone()
            return row[0] if row else None
    
    def save_result(self, experiment_name: str, user_id: str, variant_name: str, metrics: Dict[str, Any]):
        """실험 결과 저장"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO results 
                (experiment_name, user_id, variant_name, metrics, recorded_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                experiment_name,
                user_id,
                variant_name,
                json.dumps(metrics),
                datetime.now().isoformat()
            ))
            conn.commit()
    
    def get_results(self, experiment_name: str) -> List[Dict[str, Any]]:
        """실험 결과 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT user_id, variant_name, metrics, recorded_at 
                FROM results 
                WHERE experiment_name = ?
            """, (experiment_name,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'user_id': row[0],
                    'variant_name': row[1],
                    'metrics': json.loads(row[2]),
                    'recorded_at': row[3]
                })
            
            return results


class ABTestingManager:
    """A/B 테스팅 관리자"""
    
    def __init__(self, db_path: str = "data/ab_tests.db"):
        self.db = ABTestDatabase(db_path)
        self.experiments: Dict[str, Experiment] = {}
        self._load_active_experiments()
    
    def _load_active_experiments(self):
        """활성 실험 로드"""
        # 실제 구현에서는 DB에서 활성 실험 목록을 가져와야 함
        pass
    
    def create_experiment(
        self,
        name: str,
        description: str,
        variants: List[Dict[str, Any]],
        traffic_split: Optional[List[float]] = None
    ) -> Experiment:
        """
        새로운 실험 생성
        
        Args:
            name: 실험 이름
            description: 실험 설명
            variants: 변형 목록 [{"name": "control", "config": {...}}, ...]
            traffic_split: 트래픽 분할 비율 (None이면 균등 분할)
        
        Returns:
            생성된 Experiment 객체
        """
        if not variants:
            raise ValueError("At least one variant is required")
        
        # 트래픽 분할 비율 설정
        if traffic_split is None:
            traffic_split = [1.0 / len(variants)] * len(variants)
        
        if len(traffic_split) != len(variants):
            raise ValueError("Traffic split length must match variants length")
        
        # Variant 객체 생성
        variant_objects = []
        for i, variant_config in enumerate(variants):
            variant_objects.append(Variant(
                name=variant_config.get('name', f'variant_{i}'),
                config=variant_config.get('config', {}),
                traffic_weight=traffic_split[i],
                description=variant_config.get('description', '')
            ))
        
        # Experiment 생성
        experiment = Experiment(
            name=name,
            description=description,
            variants=variant_objects,
            status=ExperimentStatus.DRAFT,
            created_at=datetime.now()
        )
        
        # 저장
        self.db.save_experiment(experiment)
        self.experiments[name] = experiment
        
        logger.info(f"Created experiment: {name} with {len(variants)} variants")
        return experiment
    
    def start_experiment(self, experiment_name: str):
        """실험 시작"""
        experiment = self.db.get_experiment(experiment_name)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_name}")
        
        experiment.status = ExperimentStatus.ACTIVE
        experiment.started_at = datetime.now()
        self.db.save_experiment(experiment)
        self.experiments[experiment_name] = experiment
        
        logger.info(f"Started experiment: {experiment_name}")
    
    def assign_variant(
        self,
        experiment_name: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        사용자에게 변형 할당 (일관성 유지)
        
        Args:
            experiment_name: 실험 이름
            user_id: 사용자 ID (session_id 등)
        
        Returns:
            할당된 변형의 config
        """
        # 기존 할당 확인
        existing_assignment = self.db.get_assignment(experiment_name, user_id)
        if existing_assignment:
            experiment = self.db.get_experiment(experiment_name)
            variant = next(v for v in experiment.variants if v.name == existing_assignment)
            return {
                'variant_name': variant.name,
                'config': variant.config
            }
        
        # 새로운 할당
        experiment = self.db.get_experiment(experiment_name)
        if not experiment or experiment.status != ExperimentStatus.ACTIVE:
            # 실험이 없거나 비활성이면 기본값 반환
            return {'variant_name': 'default', 'config': {}}
        
        # 해시 기반 일관된 할당
        variant = self._hash_based_assignment(user_id, experiment.variants)
        
        # 할당 저장
        self.db.save_assignment(experiment_name, user_id, variant.name)
        
        logger.info(f"Assigned user {user_id} to variant {variant.name} in experiment {experiment_name}")
        
        return {
            'variant_name': variant.name,
            'config': variant.config
        }
    
    def _hash_based_assignment(self, user_id: str, variants: List[Variant]) -> Variant:
        """해시 기반 일관된 변형 할당"""
        # user_id를 해시하여 0-1 사이 값으로 변환
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        normalized_hash = (hash_value % 10000) / 10000.0
        
        # 누적 가중치로 변형 선택
        cumulative_weight = 0.0
        for variant in variants:
            cumulative_weight += variant.traffic_weight
            if normalized_hash <= cumulative_weight:
                return variant
        
        # 부동소수점 오차로 인한 fallback
        return variants[-1]
    
    def record_result(
        self,
        experiment_name: str,
        user_id: str,
        metrics: Dict[str, float]
    ):
        """
        실험 결과 기록
        
        Args:
            experiment_name: 실험 이름
            user_id: 사용자 ID
            metrics: 측정 메트릭 (예: {'satisfaction_score': 85, 'response_time': 2.3})
        """
        # 할당된 변형 확인
        variant_name = self.db.get_assignment(experiment_name, user_id)
        if not variant_name:
            logger.warning(f"No assignment found for user {user_id} in experiment {experiment_name}")
            return
        
        # 결과 저장
        self.db.save_result(experiment_name, user_id, variant_name, metrics)
        logger.info(f"Recorded result for user {user_id} in experiment {experiment_name}")
    
    def analyze_results(self, experiment_name: str) -> Dict[str, Any]:
        """
        통계적 유의성 분석
        
        Returns:
            분석 결과 (변형별 평균, 표준편차, p-value 등)
        """
        results = self.db.get_results(experiment_name)
        
        if not results:
            return {'error': 'No results found'}
        
        # 변형별 메트릭 집계
        variant_metrics = {}
        for result in results:
            variant_name = result['variant_name']
            if variant_name not in variant_metrics:
                variant_metrics[variant_name] = []
            
            variant_metrics[variant_name].append(result['metrics'])
        
        # 기본 통계 계산
        analysis = {}
        for variant_name, metrics_list in variant_metrics.items():
            # 각 메트릭별 평균 계산
            metric_names = metrics_list[0].keys()
            variant_stats = {
                'sample_size': len(metrics_list)
            }
            
            for metric_name in metric_names:
                values = [m[metric_name] for m in metrics_list]
                variant_stats[metric_name] = {
                    'mean': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }
            
            analysis[variant_name] = variant_stats
        
        return {
            'experiment_name': experiment_name,
            'variants': analysis,
            'total_samples': len(results)
        }
    
    def complete_experiment(self, experiment_name: str):
        """실험 완료"""
        experiment = self.db.get_experiment(experiment_name)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_name}")
        
        experiment.status = ExperimentStatus.COMPLETED
        experiment.completed_at = datetime.now()
        self.db.save_experiment(experiment)
        
        logger.info(f"Completed experiment: {experiment_name}")
