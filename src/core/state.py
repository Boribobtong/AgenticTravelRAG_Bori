"""
AppState: A.R.T 시스템의 중앙 상태 관리 모듈

사용자와의 Multi-turn 대화를 관리하고, 모든 에이전트가 공유하는 
상태 정보를 저장하는 핵심 데이터 구조입니다.
"""

from typing import TypedDict, List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ConversationState(str, Enum):
    """대화 상태 열거형"""
    INITIAL = "initial"
    PARSING = "parsing"
    SEARCHING = "searching"
    REFINING = "refining"
    GENERATING = "generating"
    COMPLETED = "completed"
    ERROR = "error"


class TravelPreference(BaseModel):
    """사용자 여행 선호도 모델"""
    budget_range: Optional[tuple] = Field(default=None, description="예산 범위 (min, max)")
    accommodation_type: Optional[str] = Field(default=None, description="숙박 유형")
    amenities: List[str] = Field(default_factory=list, description="필수 편의시설")
    atmosphere: List[str] = Field(default_factory=list, description="분위기/스타일 키워드")
    activities: List[str] = Field(default_factory=list, description="선호 활동")
    dietary: Optional[str] = Field(default=None, description="식단 제한사항")


class HotelOption(BaseModel):
    """호텔 검색 결과 모델"""
    hotel_id: str
    name: str
    location: str
    rating: float
    review_count: int
    price_range: str
    amenities: List[str]
    review_highlights: List[str] = Field(description="리뷰에서 추출한 주요 특징")
    semantic_score: float = Field(description="시맨틱 검색 점수")
    bm25_score: float = Field(description="BM25 검색 점수")
    combined_score: float = Field(description="하이브리드 검색 최종 점수")
    source_reviews: List[Dict[str, Any]] = Field(default_factory=list, description="원본 리뷰 샘플")


class WeatherForecast(BaseModel):
    """날씨 예보 모델"""
    date: str
    temperature_min: float
    temperature_max: float
    precipitation: float
    weather_code: int
    description: str
    advice: str = Field(default="", description="LLM이 생성한 날씨 기반 여행 조언")
    recommendations: List[str] = Field(default_factory=list, description="날씨 기반 활동 추천")


class GoogleSearchResult(BaseModel):
    """구글 검색 결과 모델"""
    query: str
    results: List[Dict[str, Any]]
    timestamp: datetime
    

class ChatMessage(BaseModel):
    """대화 메시지 모델"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None


class AppState(TypedDict):
    """
    LangGraph 워크플로우의 중앙 상태 객체
    
    모든 노드(에이전트)가 이 상태를 읽고 업데이트하며,
    Multi-turn 대화의 컨텍스트를 유지합니다.
    """
    
    # 기본 대화 정보
    session_id: str                          # 세션 고유 ID
    user_query: str                          # 현재 사용자 쿼리
    conversation_state: ConversationState    # 현재 대화 상태
    
    # 추출된 여행 정보
    destination: Optional[str]               # 목적지
    travel_dates: Optional[List[str]]        # 여행 날짜 [시작, 종료]
    traveler_count: Optional[int]            # 여행자 수
    preferences: Optional[TravelPreference]   # 여행 선호도
    
    # 검색 및 조회 결과
    hotel_options: List[HotelOption]         # RAG 호텔 검색 결과
    weather_forecast: List[WeatherForecast]  # 날씨 예보
    google_search_results: List[GoogleSearchResult]  # 구글 검색 결과
    
    # 대화 히스토리 및 메모리
    chat_history: List[ChatMessage]          # 전체 대화 기록
    context_memory: Dict[str, Any]           # 컨텍스트 메모리 (임시 정보)
    
    # 실행 메타데이터
    current_agent: Optional[str]             # 현재 실행 중인 에이전트
    execution_path: List[str]                # 실행된 노드 경로
    error_messages: List[str]                # 에러 메시지
    
    # 최종 결과
    final_itinerary: Optional[Dict[str, Any]]  # 생성된 최종 여행 일정
    user_feedback: Optional[str]               # 사용자 피드백
    satisfaction_score: Optional[float]        # 만족도 점수


class StateManager:
    """
    AppState를 관리하는 헬퍼 클래스
    상태 업데이트, 검증, 직렬화 등을 담당합니다.
    """
    
    @staticmethod
    def create_initial_state(session_id: str, user_query: str) -> AppState:
        """초기 상태 생성"""
        return AppState(
            session_id=session_id,
            user_query=user_query,
            conversation_state=ConversationState.INITIAL,
            destination=None,
            travel_dates=None,
            traveler_count=None,
            preferences=None,
            hotel_options=[],
            weather_forecast=[],
            google_search_results=[],
            chat_history=[
                ChatMessage(
                    role="user",
                    content=user_query
                )
            ],
            context_memory={},
            current_agent=None,
            execution_path=[],
            error_messages=[],
            final_itinerary=None,
            user_feedback=None,
            satisfaction_score=None
        )
    
    @staticmethod
    def update_state(state: AppState, updates: Dict[str, Any]) -> AppState:
        """상태 업데이트 (불변성 유지)"""
        new_state = state.copy()
        for key, value in updates.items():
            if key in new_state:
                new_state[key] = value
        return new_state
    
    @staticmethod
    def add_to_chat_history(state: AppState, message: ChatMessage) -> AppState:
        """대화 히스토리에 메시지 추가"""
        new_state = state.copy()
        new_state['chat_history'] = state['chat_history'] + [message]
        return new_state
    
    @staticmethod
    def log_execution_path(state: AppState, node_name: str) -> AppState:
        """실행 경로 로깅"""
        new_state = state.copy()
        new_state['execution_path'] = state['execution_path'] + [node_name]
        new_state['current_agent'] = node_name
        return new_state
    
    @staticmethod
    def is_complete(state: AppState) -> bool:
        """워크플로우 완료 여부 확인"""
        return state['conversation_state'] == ConversationState.COMPLETED
    
    @staticmethod
    def has_error(state: AppState) -> bool:
        """에러 발생 여부 확인"""
        return state['conversation_state'] == ConversationState.ERROR or len(state['error_messages']) > 0
    
    @staticmethod
    def get_context_summary(state: AppState) -> str:
        """현재 컨텍스트 요약 생성"""
        summary = f"""
        목적지: {state.get('destination', '미정')}
        날짜: {state.get('travel_dates', '미정')}
        인원: {state.get('traveler_count', '미정')}명
        호텔 옵션: {len(state.get('hotel_options', []))}개
        날씨 정보: {'있음' if state.get('weather_forecast') else '없음'}
        """
        return summary.strip()
