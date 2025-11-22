"""
LangGraph Workflow: A.R.T 시스템의 메인 오케스트레이터

사용자 쿼리를 받아 여러 에이전트를 조율하여 
최종 여행 계획을 생성하는 워크플로우를 정의합니다.
"""

from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
# [수정] 미사용 임포트 제거 (ToolNode 제거)
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
        """쿼리 파싱 노드"""
        logger.info(f"[QueryParser] 쿼리 파싱 시작: {state['user_query'][:50]}...")
        
        state = self.state_manager.log_execution_path(state, "query_parser")
        state = self.state_manager.update_state(state, {
            'conversation_state': ConversationState.PARSING
        })
        
        try:
            parsed_info = await self.query_parser.parse(state['user_query'])
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
        """호텔 RAG 검색 노드"""
        logger.info("[HotelRAG] 호텔 검색 시작")
        state = self.state_manager.log_execution_path(state, "hotel_rag")
        state = self.state_manager.update_state(state, {
            'conversation_state': ConversationState.SEARCHING
        })
        
        try:
            search_params = {
                'destination': state.get('destination'),
                'preferences': state.get('preferences'),
                'budget': state.get('preferences', {}).get('budget_range') if state.get('preferences') else None
            }
            hotel_results = await self.hotel_rag.search(search_params)
            state = self.state_manager.update_state(state, {
                'hotel_options': hotel_results
            })
            logger.info(f"[HotelRAG] {len(hotel_results)}개 호텔 검색 완료")
            
        except Exception as e:
            logger.error(f"[HotelRAG] 검색 실패: {str(e)}")
            state['error_messages'].append(f"호텔 검색 오류: {str(e)}")
        
        return state
    
    async def weather_tool_node(self, state: AppState) -> AppState:
        """날씨 조회 노드"""
        logger.info("[Weather] 날씨 정보 조회 시작")
        state = self.state_manager.log_execution_path(state, "weather_tool")
        
        if not state.get('destination') or not state.get('travel_dates'):
            return state
        
        try:
            weather_data = await self.weather_tool.get_forecast(
                location=state['destination'],
                dates=state['travel_dates']
            )
            state = self.state_manager.update_state(state, {
                'weather_forecast': weather_data
            })
            logger.info(f"[Weather] {len(weather_data)}일 날씨 예보 조회 완료")
            
        except Exception as e:
            logger.error(f"[Weather] 조회 실패: {str(e)}")
            state['error_messages'].append(f"날씨 조회 오류: {str(e)}")
        
        return state
    
    async def google_search_node(self, state: AppState) -> AppState:
        """구글 검색 노드"""
        logger.info("[GoogleSearch] 구글 검색 시작")
        state = self.state_manager.log_execution_path(state, "google_search")
        
        if not state.get('hotel_options'):
            return state
        
        try:
            search_results = []
            for hotel in state['hotel_options'][:3]:
                result = await self.google_search.search_hotel_info(
                    hotel_name=hotel.name,
                    location=hotel.location
                )
                search_results.append(result)
            
            state = self.state_manager.update_state(state, {
                'google_search_results': search_results
            })
            logger.info(f"[GoogleSearch] {len(search_results)}개 호텔 정보 검색 완료")
            
        except Exception as e:
            logger.error(f"[GoogleSearch] 검색 실패: {str(e)}")
        
        return state
    
    async def response_generator_node(self, state: AppState) -> AppState:
        """응답 생성 노드"""
        logger.info("[ResponseGenerator] 최종 응답 생성 시작")
        
        state = self.state_manager.log_execution_path(state, "response_generator")
        state = self.state_manager.update_state(state, {
            'conversation_state': ConversationState.GENERATING
        })
        
        try:
            final_response = await self.response_generator.generate(state)
            
            state = self.state_manager.update_state(state, {
                'final_itinerary': final_response,
                'conversation_state': ConversationState.COMPLETED,
                'user_feedback': None
            })
            
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
        """피드백 처리 노드"""
        logger.info("[FeedbackHandler] 피드백 처리 시작")
        
        state = self.state_manager.log_execution_path(state, "feedback_handler")
        state = self.state_manager.update_state(state, {
            'conversation_state': ConversationState.REFINING
        })
        
        feedback = state.get('user_feedback', '')
        
        if "다른 호텔" in feedback or "호텔 변경" in feedback:
            state['context_memory']['retry_type'] = 'hotel'
        elif "처음부터" in feedback or "다시 시작" in feedback:
            state['context_memory']['retry_type'] = 'all'
        else:
            state['context_memory']['retry_type'] = 'complete'
        
        logger.info(f"[FeedbackHandler] 피드백 타입: {state['context_memory'].get('retry_type')}")
        return state
    
    # ==================== 라우팅 함수들 ====================
    
    def route_after_parsing(self, state: AppState) -> str:
        if state.get('conversation_state') == ConversationState.ERROR:
            return "error"
        if state.get('user_feedback'):
            return "feedback"
        
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
        return "both"
    
    def check_completion(self, state: AppState) -> str:
        if state.get('conversation_state') == ConversationState.COMPLETED:
            if state.get('user_feedback'):
                return "feedback"
            return "complete"
        return "feedback"
    
    def route_after_feedback(self, state: AppState) -> str:
        retry_type = state.get('context_memory', {}).get('retry_type', 'complete')
        if retry_type == 'hotel':
            return "retry_hotel"
        elif retry_type == 'all':
            return "retry_all"
        else:
            return "complete"
    
    # ==================== 실행 메서드 ====================
    
    async def run(self, user_query: str, session_id: str = None) -> Dict[str, Any]:
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        initial_state = self.state_manager.create_initial_state(
            session_id=session_id,
            user_query=user_query
        )
        return await self.run_from_state(initial_state)
    
    async def continue_conversation(self, user_input: str, session_id: str, previous_state: AppState) -> Dict[str, Any]:
        updated_state = self.state_manager.update_state(previous_state, {
            'user_feedback': user_input,
            'user_query': user_input
        })
        updated_state = self.state_manager.add_to_chat_history(
            updated_state,
            ChatMessage(role="user", content=user_input)
        )
        return await self.run_from_state(updated_state)
    
    async def run_from_state(self, state: AppState) -> Dict[str, Any]:
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

_workflow_instance = None

def get_workflow() -> ARTWorkflow:
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = ARTWorkflow()
    return _workflow_instance
