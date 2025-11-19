"""
LangGraph Workflow: A.R.T 시스템의 메인 오케스트레이터

사용자 쿼리를 받아 여러 에이전트를 조율하여 
최종 여행 계획을 생성하는 워크플로우를 정의합니다.
"""

from typing import Dict, Any, List, Optional
from langgraph.graph import Graph, StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import logging
import asyncio

from src.core.state import AppState, StateManager, ConversationState, ChatMessage
from src.agents.query_parser import QueryParserAgent
from src.agents.hotel_rag import HotelRAGAgent  
from src.agents.weather_tool import WeatherToolAgent
from src.agents.google_search import GoogleSearchAgent
from src.agents.response_generator import ResponseGeneratorAgent

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ARTWorkflow:
    """
    A.R.T 시스템의 메인 워크플로우 클래스
    LangGraph를 사용하여 Multi-Agent 오케스트레이션을 구현합니다.
    """
    
    def __init__(self):
        """워크플로우 초기화"""
        self.state_manager = StateManager()
        
        # 에이전트 초기화
        self.query_parser = QueryParserAgent()
        self.hotel_rag = HotelRAGAgent()
        self.weather_tool = WeatherToolAgent()
        self.google_search = GoogleSearchAgent()
        self.response_generator = ResponseGeneratorAgent()
        
        # 워크플로우 그래프 구성
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
        
        logger.info("A.R.T Workflow 초기화 완료")
    
    def _build_workflow(self) -> StateGraph:
        """
        LangGraph 워크플로우 구성
        
        노드(Node): 개별 에이전트 함수
        엣지(Edge): 상태 기반 조건부 라우팅
        """
        
        # StateGraph 생성
        workflow = StateGraph(AppState)
        
        # 노드 추가
        workflow.add_node("query_parser", self.parse_query_node)
        workflow.add_node("hotel_rag", self.hotel_rag_node)
        workflow.add_node("weather_tool", self.weather_tool_node)
        workflow.add_node("google_search", self.google_search_node)
        workflow.add_node("response_generator", self.response_generator_node)
        workflow.add_node("feedback_handler", self.feedback_handler_node)
        
        # 시작점 설정
        workflow.set_entry_point("query_parser")
        
        # 조건부 엣지 추가
        workflow.add_conditional_edges(
            "query_parser",
            self.route_after_parsing,
            {
                "hotel": "hotel_rag",
                "weather": "weather_tool",
                "both": "hotel_rag",
                "feedback": "feedback_handler",
                "error": END
            }
        )
        
        # 일반 엣지 추가
        workflow.add_edge("hotel_rag", "weather_tool")
        workflow.add_edge("weather_tool", "google_search")
        workflow.add_edge("google_search", "response_generator")
        
        # 응답 생성 후 라우팅
        workflow.add_conditional_edges(
            "response_generator",
            self.check_completion,
            {
                "complete": END,
                "feedback": "feedback_handler"
            }
        )
        
        # 피드백 처리 후 라우팅
        workflow.add_conditional_edges(
            "feedback_handler",
            self.route_after_feedback,
            {
                "retry_hotel": "hotel_rag",
                "retry_all": "query_parser",
                "complete": END
            }
        )
        
        return workflow
    
    # ==================== 노드 함수들 ====================
    
    async def parse_query_node(self, state: AppState) -> AppState:
        """
        쿼리 파싱 노드
        사용자 입력에서 여행 정보를 추출합니다.
        """
        logger.info(f"[QueryParser] 쿼리 파싱 시작: {state['user_query'][:50]}...")
        
        state = self.state_manager.log_execution_path(state, "query_parser")
        state = self.state_manager.update_state(state, {
            'conversation_state': ConversationState.PARSING
        })
        
        try:
            # QueryParserAgent 실행
            parsed_info = await self.query_parser.parse(state['user_query'])
            
            # 상태 업데이트
            state = self.state_manager.update_state(state, {
                'destination': parsed_info.get('destination'),
                'travel_dates': parsed_info.get('dates'),
                'traveler_count': parsed_info.get('traveler_count'),
                'preferences': parsed_info.get('preferences')
            })
            
            logger.info(f"[QueryParser] 파싱 완료: 목적지={state['destination']}")
            
        except Exception as e:
            logger.error(f"[QueryParser] 파싱 실패: {str(e)}")
            state['error_messages'].append(f"쿼리 파싱 오류: {str(e)}")
            state['conversation_state'] = ConversationState.ERROR
        
        return state
    
    async def hotel_rag_node(self, state: AppState) -> AppState:
        """
        호텔 RAG 검색 노드
        ElasticSearch를 통해 호텔을 검색합니다.
        """
        logger.info("[HotelRAG] 호텔 검색 시작")
        
        state = self.state_manager.log_execution_path(state, "hotel_rag")
        state = self.state_manager.update_state(state, {
            'conversation_state': ConversationState.SEARCHING
        })
        
        try:
            # 검색 쿼리 구성
            search_params = {
                'destination': state.get('destination'),
                'preferences': state.get('preferences'),
                'budget': state.get('preferences', {}).get('budget_range') if state.get('preferences') else None
            }
            
            # HotelRAGAgent 실행
            hotel_results = await self.hotel_rag.search(search_params)
            
            # 상태 업데이트
            state = self.state_manager.update_state(state, {
                'hotel_options': hotel_results
            })
            
            logger.info(f"[HotelRAG] {len(hotel_results)}개 호텔 검색 완료")
            
        except Exception as e:
            logger.error(f"[HotelRAG] 검색 실패: {str(e)}")
            state['error_messages'].append(f"호텔 검색 오류: {str(e)}")
        
        return state
    
    async def weather_tool_node(self, state: AppState) -> AppState:
        """
        날씨 조회 노드
        Open-Meteo API를 통해 날씨를 조회합니다.
        """
        logger.info("[Weather] 날씨 정보 조회 시작")
        
        state = self.state_manager.log_execution_path(state, "weather_tool")
        
        if not state.get('destination') or not state.get('travel_dates'):
            logger.warning("[Weather] 목적지 또는 날짜 정보 없음 - 스킵")
            return state
        
        try:
            # WeatherToolAgent 실행
            weather_data = await self.weather_tool.get_forecast(
                location=state['destination'],
                dates=state['travel_dates']
            )
            
            # 상태 업데이트
            state = self.state_manager.update_state(state, {
                'weather_forecast': weather_data
            })
            
            logger.info(f"[Weather] {len(weather_data)}일 날씨 예보 조회 완료")
            
        except Exception as e:
            logger.error(f"[Weather] 조회 실패: {str(e)}")
            state['error_messages'].append(f"날씨 조회 오류: {str(e)}")
        
        return state
    
    async def google_search_node(self, state: AppState) -> AppState:
        """
        구글 검색 노드
        호텔 가격 및 추가 정보를 검색합니다.
        """
        logger.info("[GoogleSearch] 구글 검색 시작")
        
        state = self.state_manager.log_execution_path(state, "google_search")
        
        if not state.get('hotel_options'):
            logger.warning("[GoogleSearch] 호텔 옵션 없음 - 스킵")
            return state
        
        try:
            # 상위 3개 호텔에 대해 검색
            search_results = []
            for hotel in state['hotel_options'][:3]:
                result = await self.google_search.search_hotel_info(
                    hotel_name=hotel.name,
                    location=hotel.location
                )
                search_results.append(result)
            
            # 상태 업데이트
            state = self.state_manager.update_state(state, {
                'google_search_results': search_results
            })
            
            logger.info(f"[GoogleSearch] {len(search_results)}개 호텔 정보 검색 완료")
            
        except Exception as e:
            logger.error(f"[GoogleSearch] 검색 실패: {str(e)}")
            # 구글 검색 실패는 치명적이지 않으므로 계속 진행
        
        return state
    
    async def response_generator_node(self, state: AppState) -> AppState:
        """
        응답 생성 노드
        수집된 정보를 종합하여 최종 응답을 생성합니다.
        """
        logger.info("[ResponseGenerator] 최종 응답 생성 시작")
        
        state = self.state_manager.log_execution_path(state, "response_generator")
        state = self.state_manager.update_state(state, {
            'conversation_state': ConversationState.GENERATING
        })
        
        try:
            # ResponseGeneratorAgent 실행
            final_response = await self.response_generator.generate(state)
            
            # 상태 업데이트
            state = self.state_manager.update_state(state, {
                'final_itinerary': final_response,
                'conversation_state': ConversationState.COMPLETED
            })
            
            # 대화 히스토리 추가
            state = self.state_manager.add_to_chat_history(
                state,
                ChatMessage(
                    role="assistant",
                    content=final_response.get('summary', '')
                )
            )
            
            logger.info("[ResponseGenerator] 응답 생성 완료")
            
        except Exception as e:
            logger.error(f"[ResponseGenerator] 생성 실패: {str(e)}")
            state['error_messages'].append(f"응답 생성 오류: {str(e)}")
            state['conversation_state'] = ConversationState.ERROR
        
        return state
    
    async def feedback_handler_node(self, state: AppState) -> AppState:
        """
        피드백 처리 노드
        사용자 피드백을 처리하고 재검색 여부를 결정합니다.
        """
        logger.info("[FeedbackHandler] 피드백 처리 시작")
        
        state = self.state_manager.log_execution_path(state, "feedback_handler")
        state = self.state_manager.update_state(state, {
            'conversation_state': ConversationState.REFINING
        })
        
        # 피드백 분석 및 다음 액션 결정
        feedback = state.get('user_feedback', '')
        
        if "다른 호텔" in feedback or "호텔 변경" in feedback:
            # 호텔 재검색 필요
            state['context_memory']['retry_type'] = 'hotel'
        elif "처음부터" in feedback or "다시 시작" in feedback:
            # 전체 재시작
            state['context_memory']['retry_type'] = 'all'
        else:
            # 완료
            state['context_memory']['retry_type'] = 'complete'
        
        logger.info(f"[FeedbackHandler] 피드백 타입: {state['context_memory'].get('retry_type')}")
        
        return state
    
    # ==================== 라우팅 함수들 ====================
    
    def route_after_parsing(self, state: AppState) -> str:
        """쿼리 파싱 후 라우팅 결정"""
        
        if state.get('conversation_state') == ConversationState.ERROR:
            return "error"
        
        # 사용자 피드백이 있으면 피드백 처리로
        if state.get('user_feedback'):
            return "feedback"
        
        # 선호도 기반 라우팅
        preferences = state.get('preferences', {})
        if preferences:
            has_hotel = any(keyword in str(preferences) for keyword in ['호텔', '숙박', '숙소'])
            has_weather = any(keyword in str(preferences) for keyword in ['날씨', '기후'])
            
            if has_hotel and has_weather:
                return "both"
            elif has_hotel:
                return "hotel"
            elif has_weather:
                return "weather"
        
        # 기본값: 둘 다 실행
        return "both"
    
    def check_completion(self, state: AppState) -> str:
        """응답 생성 후 완료 여부 확인"""
        
        if state.get('conversation_state') == ConversationState.COMPLETED:
            # 사용자 피드백 대기 (실제로는 별도 입력 필요)
            if state.get('user_feedback'):
                return "feedback"
            return "complete"
        
        return "feedback"
    
    def route_after_feedback(self, state: AppState) -> str:
        """피드백 처리 후 라우팅"""
        
        retry_type = state.get('context_memory', {}).get('retry_type', 'complete')
        
        if retry_type == 'hotel':
            return "retry_hotel"
        elif retry_type == 'all':
            return "retry_all"
        else:
            return "complete"
    
    # ==================== 실행 메서드 ====================
    
    async def run(self, user_query: str, session_id: str = None) -> Dict[str, Any]:
        """
        워크플로우 실행
        
        Args:
            user_query: 사용자 질문
            session_id: 세션 ID (Multi-turn 대화용)
            
        Returns:
            최종 결과 딕셔너리
        """
        
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        # 초기 상태 생성
        initial_state = self.state_manager.create_initial_state(
            session_id=session_id,
            user_query=user_query
        )
        
        try:
            # 워크플로우 실행
            logger.info(f"워크플로우 시작: session_id={session_id}")
            final_state = await self.app.ainvoke(initial_state)
            
            # 결과 반환
            return {
                'success': not self.state_manager.has_error(final_state),
                'session_id': session_id,
                'itinerary': final_state.get('final_itinerary'),
                'hotels': final_state.get('hotel_options'),
                'weather': final_state.get('weather_forecast'),
                'execution_path': final_state.get('execution_path'),
                'errors': final_state.get('error_messages')
            }
            
        except Exception as e:
            logger.error(f"워크플로우 실행 실패: {str(e)}")
            return {
                'success': False,
                'session_id': session_id,
                'error': str(e)
            }
    
    async def continue_conversation(self, user_input: str, session_id: str, previous_state: AppState) -> Dict[str, Any]:
        """
        Multi-turn 대화 계속하기
        
        Args:
            user_input: 새로운 사용자 입력
            session_id: 기존 세션 ID
            previous_state: 이전 상태
            
        Returns:
            업데이트된 결과
        """
        
        # 사용자 피드백 추가
        updated_state = self.state_manager.update_state(previous_state, {
            'user_feedback': user_input,
            'user_query': user_input  # 새 쿼리로 업데이트
        })
        
        # 대화 히스토리 추가
        updated_state = self.state_manager.add_to_chat_history(
            updated_state,
            ChatMessage(role="user", content=user_input)
        )
        
        # 워크플로우 재실행
        return await self.run_from_state(updated_state)
    
    async def run_from_state(self, state: AppState) -> Dict[str, Any]:
        """기존 상태에서 워크플로우 계속 실행"""
        
        try:
            final_state = await self.app.ainvoke(state)
            
            return {
                'success': not self.state_manager.has_error(final_state),
                'session_id': final_state['session_id'],
                'itinerary': final_state.get('final_itinerary'),
                'hotels': final_state.get('hotel_options'),
                'weather': final_state.get('weather_forecast'),
                'execution_path': final_state.get('execution_path'),
                'errors': final_state.get('error_messages')
            }
            
        except Exception as e:
            logger.error(f"상태 기반 실행 실패: {str(e)}")
            return {
                'success': False,
                'session_id': state['session_id'],
                'error': str(e)
            }


# 싱글톤 인스턴스
_workflow_instance = None

def get_workflow() -> ARTWorkflow:
    """워크플로우 싱글톤 인스턴스 반환"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = ARTWorkflow()
    return _workflow_instance
