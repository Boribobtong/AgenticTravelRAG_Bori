"""
Memory Management System: Short-term & Long-term Memory

다중 턴 대화에서 컨텍스트를 유지하고, 사용자 선호도를 학습하는 메모리 시스템
- Short-term: 현재 세션 내 임시 정보 (최대 N개 대화 유지)
- Long-term: 사용자 프로필, 선호도, 과거 여행 기록
"""

import logging
from typing import Dict, Any, List, Optional, Deque
from collections import deque
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
import json

logger = logging.getLogger(__name__)


@dataclass
class ShortTermMemory:
    """
    세션 내 임시 메모리 (Single Session)
    
    최근 N개의 대화와 컨텍스트를 유지합니다.
    """
    session_id: str
    max_messages: int = 10
    conversation_history: Deque[Dict[str, Any]] = field(default_factory=lambda: deque(maxlen=10))
    context_stack: List[Dict[str, Any]] = field(default_factory=list)  # 대화 컨텍스트 스택
    current_destination: Optional[str] = None
    current_dates: Optional[List[str]] = None
    current_preferences: Optional[Dict[str, Any]] = None
    last_query_time: Optional[datetime] = None
    query_count: int = 0
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """메시지 추가"""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self.conversation_history.append(message)
        self.query_count += 1
        self.last_query_time = datetime.now()
        logger.debug(f"[STM] 메시지 추가: {role} ({self.query_count}번째)")
    
    def push_context(self, context: Dict[str, Any]):
        """컨텍스트 스택에 푸시"""
        self.context_stack.append({
            'timestamp': datetime.now().isoformat(),
            'context': context
        })
        logger.debug(f"[STM] 컨텍스트 푸시 ({len(self.context_stack)}개)")
    
    def pop_context(self) -> Optional[Dict[str, Any]]:
        """컨텍스트 스택에서 팝"""
        if self.context_stack:
            popped = self.context_stack.pop()
            logger.debug(f"[STM] 컨텍스트 팝 ({len(self.context_stack)}개 남음)")
            return popped.get('context')
        return None
    
    def get_recent_context(self, num_messages: int = 3) -> str:
        """최근 대화 컨텍스트 요약"""
        recent = list(self.conversation_history)[-num_messages:]
        context_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content'][:100]}"
            for msg in recent
        ])
        return context_text if context_text else "대화 기록 없음"
    
    def clear(self):
        """메모리 초기화"""
        self.conversation_history.clear()
        self.context_stack.clear()
        self.query_count = 0
        logger.info(f"[STM] 세션 {self.session_id} 메모리 초기화")


@dataclass
class UserProfile:
    """사용자 프로필 (Long-term Memory)"""
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    # 기본 정보
    name: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    # 여행 특성
    favorite_destinations: List[str] = field(default_factory=list)
    avoided_destinations: List[str] = field(default_factory=list)
    
    # 여행 스타일
    travel_style: Optional[str] = None  # "adventure", "relaxation", "cultural", "luxury"
    budget_preference: Optional[str] = None  # "budget", "mid-range", "luxury"
    activity_preferences: List[str] = field(default_factory=list)  # ["hiking", "museum", ...]
    dietary_restrictions: List[str] = field(default_factory=list)
    
    # 통계
    total_trips: int = 0
    average_trip_duration: Optional[float] = None
    total_trips_cost: float = 0.0
    
    def update_preferences(self, new_prefs: Dict[str, Any]):
        """선호도 업데이트"""
        self.preferences.update(new_prefs)
        self.last_updated = datetime.now()
        logger.debug(f"[LTM] 사용자 {self.user_id} 선호도 업데이트")
    
    def add_trip_record(self, destination: str, duration: int, cost: float):
        """여행 기록 추가"""
        self.total_trips += 1
        self.total_trips_cost += cost
        if self.average_trip_duration:
            self.average_trip_duration = (
                (self.average_trip_duration * (self.total_trips - 1) + duration) / 
                self.total_trips
            )
        else:
            self.average_trip_duration = duration
        
        if destination not in self.favorite_destinations:
            self.favorite_destinations.append(destination)
        
        self.last_updated = datetime.now()
        logger.debug(f"[LTM] 여행 기록 추가: {destination} ({duration}일, ${cost})")


@dataclass
class LongTermMemory:
    """
    사용자 프로필 및 선호도 저장소
    
    사용자별 여행 패턴, 선호도, 과거 기록을 유지합니다.
    """
    storage: Dict[str, UserProfile] = field(default_factory=dict)
    
    def get_or_create_profile(self, user_id: str) -> UserProfile:
        """사용자 프로필 조회 또는 생성"""
        if user_id not in self.storage:
            self.storage[user_id] = UserProfile(user_id=user_id)
            logger.info(f"[LTM] 새 사용자 프로필 생성: {user_id}")
        return self.storage[user_id]
    
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """사용자 프로필 조회"""
        return self.storage.get(user_id)
    
    def get_user_preferences_summary(self, user_id: str) -> str:
        """사용자 선호도 요약"""
        profile = self.get_profile(user_id)
        if not profile:
            return "프로필 정보 없음"
        
        summary = f"""
**사용자 프로필 요약**
- 선호 여행지: {', '.join(profile.favorite_destinations[:3]) if profile.favorite_destinations else '없음'}
- 여행 스타일: {profile.travel_style or '미정'}
- 예산 선호: {profile.budget_preference or '미정'}
- 활동 선호: {', '.join(profile.activity_preferences[:3]) if profile.activity_preferences else '없음'}
- 총 여행 횟수: {profile.total_trips}회
        """.strip()
        
        return summary


class MemoryManager:
    """
    통합 메모리 관리자
    
    Short-term & Long-term 메모리를 통합 관리합니다.
    """
    
    def __init__(self):
        self.short_term_memories: Dict[str, ShortTermMemory] = {}
        self.long_term_memory = LongTermMemory()
        logger.info("MemoryManager 초기화 완료")
    
    def get_session_memory(self, session_id: str, user_id: Optional[str] = None) -> ShortTermMemory:
        """세션 메모리 조회 또는 생성"""
        if session_id not in self.short_term_memories:
            self.short_term_memories[session_id] = ShortTermMemory(session_id=session_id)
            logger.debug(f"[Memory] 새 세션 메모리 생성: {session_id}")
        return self.short_term_memories[session_id]
    
    def add_user_memory(self, user_id: str, session_id: str, role: str, content: str):
        """사용자 메시지를 메모리에 추가"""
        # Short-term 메모리에 추가
        session_mem = self.get_session_memory(session_id, user_id)
        session_mem.add_message(role, content)
        
        # Long-term 메모리 업데이트 (사용자 프로필 정보 추출)
        if user_id:
            profile = self.long_term_memory.get_or_create_profile(user_id)
            # 프로필 정보는 별도 분석 에이전트에서 추출
    
    def get_conversation_context(self, session_id: str, num_messages: int = 3) -> str:
        """대화 컨텍스트 조회"""
        session_mem = self.get_session_memory(session_id)
        return session_mem.get_recent_context(num_messages)
    
    def get_user_context(self, user_id: str) -> str:
        """사용자 기반 컨텍스트 조회 (Long-term)"""
        return self.long_term_memory.get_user_preferences_summary(user_id)
    
    def record_trip(self, user_id: str, destination: str, duration: int, cost: float):
        """여행 기록 저장"""
        profile = self.long_term_memory.get_or_create_profile(user_id)
        profile.add_trip_record(destination, duration, cost)
    
    def clear_session(self, session_id: str):
        """세션 메모리 정리"""
        if session_id in self.short_term_memories:
            self.short_term_memories[session_id].clear()
            del self.short_term_memories[session_id]
            logger.info(f"[Memory] 세션 {session_id} 메모리 정리")
    
    def export_long_term_memory(self, user_id: str) -> Dict[str, Any]:
        """Long-term 메모리 내보내기"""
        profile = self.long_term_memory.get_profile(user_id)
        if not profile:
            return {}
        return asdict(profile, dict_factory=self._serialize_factory)
    
    @staticmethod
    def _serialize_factory(fields):
        """Datetime 직렬화"""
        result = {}
        for key, value in fields:
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result


# Global instance
_memory_manager_instance: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Global MemoryManager 인스턴스 조회"""
    global _memory_manager_instance
    if _memory_manager_instance is None:
        _memory_manager_instance = MemoryManager()
    return _memory_manager_instance
