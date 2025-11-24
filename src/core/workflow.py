"""
LangGraph Workflow: A.R.T 시스템의 메인 오케스트레이터

사용자 쿼리를 받아 여러 에이전트를 조율하여 
최종 여행 계획을 생성하는 워크플로우를 정의합니다.
"""

from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
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
    """
    
    def __init__(self):
        self.state_manager = StateManager()
        self.query_parser = QueryParserAgent()
        self.hotel_rag = HotelRAGAgent()
        self.weather_tool = WeatherToolAgent()
        self.google_search = GoogleSearchAgent()
        self.response_generator = ResponseGeneratorAgent()
        
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
        
        logger.info("A.R.T Workflow 초기화 완료")
    
    def _build_workflow(self) -> StateGraph:
        workflow = StateGraph(AppState)
        
        workflow.add_node("query_parser", self.parse_query_node)
        workflow.add_node("hotel_rag", self.hotel_rag_node)
        workflow.add_node("weather_tool", self.weather_tool_node)
        workflow.add_node("google_search", self.google_search_node)
        workflow.add_node("response_generator", self.response_generator_node)
        workflow.add_node("feedback_handler", self.feedback_handler_node)
        
        workflow.set_entry_point("query_parser")
        
        workflow.add_conditional_edges(
            "query_parser",
            self.route_after_parsing,
            {
                "search": "hotel_rag",     # 검색 실행
                "feedback": "feedback_handler", # 단순 피드백 처리
                "error": END
            }
        )
        
        workflow.add_edge("hotel_rag", "weather_tool")
        workflow.add_edge("weather_tool", "google_search")
        workflow.add_edge("google_search", "response_generator")
        
        workflow.add_conditional_edges(
            "response_generator",
            self.check_completion,
            {
                "complete": END,
                "feedback": "feedback_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "feedback_handler",
            self.route_after_feedback,
            {
                "retry_search": "hotel_rag",
                "retry_parsing": "query_parser",
                "complete": END
            }
        )
        
        return workflow
    
    # ==================== 노드 함수들 ====================
    
    async def parse_query_node(self, state: AppState) -> AppState:
            """쿼리 파싱 및 컨텍스트 업데이트"""
            logger.info(f"[QueryParser] 시작: {state['user_query'][:50]}...")
            
            state = self.state_manager.log_execution_path(state, "query_parser")
            
            try:
                # [수정] state 전체를 넘겨주어 컨텍스트를 인식하게 함
                parsed_info = await self.query_parser.parse(state['user_query'], state)
                
                logger.info(f"[QueryParser] 파싱 결과: {parsed_info}")
                
                updates = {}
                if parsed_info.get('destination'):
                    updates['destination'] = parsed_info['destination']
                    logger.info(f"[QueryParser] 목적지 업데이트: {parsed_info['destination']}")
                else:
                    logger.warning(f"[QueryParser] 목적지 정보 없음. 파싱 결과: {parsed_info}")
                
                if parsed_info.get('dates'):
                    updates['travel_dates'] = parsed_info['dates']
                    
                # traveler_count가 None이 아닐 때만 업데이트 (기존 인원 유지)
                if parsed_info.get('traveler_count') is not None:
                    updates['traveler_count'] = parsed_info['traveler_count']
                    
                if parsed_info.get('preferences'):
                    current_prefs = state.get('preferences', {}) or {}
                    # 단순 덮어쓰기가 아니라 병합하는 것이 더 좋음 (여기서는 일단 유지)
                    updates['preferences'] = parsed_info['preferences']

                state = self.state_manager.update_state(state, updates)
                logger.info(f"[QueryParser] 완료: 목적지={state.get('destination')}, 날짜={state.get('travel_dates')}")
                
            except Exception as e:
                logger.error(f"[QueryParser] 실패: {str(e)}")
                state['error_messages'].append(str(e))
                state['conversation_state'] = ConversationState.ERROR
            
            return state
    
    async def hotel_rag_node(self, state: AppState) -> AppState:
        """호텔 검색"""
        logger.info("[HotelRAG] 검색 시작")
        state = self.state_manager.log_execution_path(state, "hotel_rag")
        
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
            logger.info(f"[HotelRAG] {len(hotel_results)}개 호텔 발견")
            
        except Exception as e:
            logger.error(f"[HotelRAG] 실패: {str(e)}")
        
        return state
    
    async def weather_tool_node(self, state: AppState) -> AppState:
        """[수정] 날씨 조회 (목적지와 날짜가 변경되었을 때만 재실행)"""
        state = self.state_manager.log_execution_path(state, "weather_tool")
        
        # 목적지나 날짜 정보가 없으면 스킵
        if not state.get('destination') or not state.get('travel_dates'):
            logger.info("[Weather] 목적지 또는 날짜 정보 없음 - 스킵")
            return state
        
        # 이미 같은 목적지/날짜로 날씨를 조회했으면 스킵
        existing_forecast = state.get('weather_forecast', [])
        if existing_forecast:
            # 컨텍스트 메모리에서 이전 조회 정보 확인
            prev_dest = state.get('context_memory', {}).get('weather_destination')
            prev_dates = state.get('context_memory', {}).get('weather_dates')
            
            if prev_dest == state['destination'] and prev_dates == state['travel_dates']:
                logger.info(f"[Weather] 이미 조회됨 ({state['destination']}) - 스킵")
                return state
            
        try:
            logger.info(f"[Weather] 날씨 조회: {state['destination']}, {state['travel_dates']}")
            weather_data = await self.weather_tool.get_forecast(
                location=state['destination'],
                dates=state['travel_dates']
            )
            
            # 날씨 정보와 함께 조회 이력 저장
            updates = {
                'weather_forecast': weather_data,
                'context_memory': {
                    **state.get('context_memory', {}),
                    'weather_destination': state['destination'],
                    'weather_dates': state['travel_dates']
                }
            }
            state = self.state_manager.update_state(state, updates)
            logger.info(f"[Weather] 조회 완료: {len(weather_data)}개 예보")
            
        except Exception as e:
            logger.error(f"[Weather] 실패: {str(e)}")
        
        return state
    
    async def google_search_node(self, state: AppState) -> AppState:
        """구글 검색"""
        state = self.state_manager.log_execution_path(state, "google_search")
        if not state.get('hotel_options'):
            return state
            
        try:
            search_results = []
            for hotel in state['hotel_options'][:3]:
                result = await self.google_search.search_hotel_info(hotel.name, hotel.location)
                search_results.append(result)
            state = self.state_manager.update_state(state, {'google_search_results': search_results})
        except Exception:
            pass # 구글 검색 실패는 무시
        
        return state
    
    async def response_generator_node(self, state: AppState) -> AppState:
        """응답 생성"""
        logger.info("[ResponseGenerator] 생성 시작")
        state = self.state_manager.log_execution_path(state, "response_generator")
        
        try:
            final_response = await self.response_generator.generate(state)
            
            state = self.state_manager.update_state(state, {
                'final_itinerary': final_response,
                'conversation_state': ConversationState.COMPLETED,
                'user_feedback': None # [중요] 피드백 루프 방지
            })
            
            # 히스토리에 저장
            state = self.state_manager.add_to_chat_history(
                state,
                ChatMessage(role="assistant", content=final_response.get('summary', ''))
            )
            
        except Exception as e:
            logger.error(f"[ResponseGenerator] 실패: {str(e)}")
            state['conversation_state'] = ConversationState.ERROR
        
        return state
    
    async def feedback_handler_node(self, state: AppState) -> AppState:
        """피드백 처리 (수동 개입이 필요한 경우만)"""
        logger.info("[FeedbackHandler] 처리")
        state = self.state_manager.log_execution_path(state, "feedback_handler")
        
        # [수정] 목적지 정보가 없는 경우 안내 메시지 생성
        if not state.get('destination'):
            feedback_message = (
                "목적지를 알려주시면 여행 계획을 도와드리겠습니다! 😊\n\n"
            )
            state = self.state_manager.update_state(state, {
                'final_itinerary': {
                    'summary': feedback_message,
                    'type': 'feedback'
                },
                'conversation_state': ConversationState.COMPLETED
            })
            return state
        
        # 기타 피드백 처리
        state['context_memory']['retry_type'] = 'complete'
        return state
    
    # ==================== 라우팅 함수들 ====================
    
    def route_after_parsing(self, state: AppState) -> str:
        """파싱 후 경로 결정"""
        if state.get('conversation_state') == ConversationState.ERROR:
            return "error"
            
        # [핵심 수정] 목적지가 있으면 무조건 검색 수행 (새로운 질문 or 수정된 질문)
        if state.get('destination'):
            return "search"
            
        # 목적지가 없는데 피드백만 있는 경우 (예: "안녕", "고마워")
        return "feedback"
    
    def check_completion(self, state: AppState) -> str:
        if state.get('user_feedback'):
            return "feedback"
        return "complete"
    
    def route_after_feedback(self, state: AppState) -> str:
        return "complete"
    
    # ==================== 실행 메서드 ====================
    
    async def run(self, user_query: str, session_id: str = None) -> Dict[str, Any]:
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        initial_state = self.state_manager.create_initial_state(session_id, user_query)
        return await self.run_from_state(initial_state)
    
    async def continue_conversation(self, user_input: str, session_id: str, previous_state: AppState) -> Dict[str, Any]:
        # 이전 상태 유지하며 새 쿼리 업데이트
        updated_state = self.state_manager.update_state(previous_state, {
            'user_query': user_input,
            'user_feedback': user_input,
            'conversation_state': ConversationState.PARSING # 상태 초기화
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
                'state': final_state, # 다음 턴을 위해 필수
                'itinerary': final_state.get('final_itinerary'),
                'hotels': final_state.get('hotel_options'),
                'weather': final_state.get('weather_forecast'),
                'execution_path': final_state.get('execution_path', [])  # 테스트용 실행 경로
            }
        except Exception as e:
            logger.error(f"워크플로우 실행 실패: {str(e)}")
            return {'success': False, 'error': str(e)}

_workflow_instance = None
def get_workflow() -> ARTWorkflow:
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = ARTWorkflow()
    return _workflow_instance