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
from src.agents.safety_info import SafetyInfoAgent
from src.agents.currency_converter_node import execute_currency_conversion
from src.tools.ab_testing import ABTestingManager
from src.tools.satisfaction_tracker import SatisfactionTracker
from src.tools.metrics_collector import get_metrics_collector
from src.tools.wiki_tool import WikipediaCustomTool
import time

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
        self.safety_info = SafetyInfoAgent()
        # Wikipedia tool (Phase 4)
        try:
            self.wiki_tool = WikipediaCustomTool()
        except Exception:
            self.wiki_tool = None
        
        # Phase 4: A/B Testing
        self.ab_testing = ABTestingManager()
        self._init_ab_experiments()
        
        # Phase 4: Satisfaction Tracking
        self.satisfaction_tracker = SatisfactionTracker()
        self.session_start_times = {}  # 세션별 시작 시간 추적
        
        # Phase 4: Metrics Collection
        self.metrics = get_metrics_collector()
        
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
        
        logger.info("A.R.T Workflow 초기화 완료")
    
    def _init_ab_experiments(self):
        """A/B 테스팅 실험 초기화"""
        try:
            # 하이브리드 검색 alpha 값 실험
            experiment = self.ab_testing.create_experiment(
                name="hybrid_search_alpha",
                description="하이브리드 검색의 최적 alpha 값 찾기",
                variants=[
                    {"name": "bm25_heavy", "config": {"alpha": 0.3}, "description": "BM25 강화"},
                    {"name": "balanced", "config": {"alpha": 0.5}, "description": "균형"},
                    {"name": "vector_heavy", "config": {"alpha": 0.7}, "description": "Vector 강화"}
                ],
                traffic_split=[0.33, 0.34, 0.33]
            )
            # 실험 시작
            self.ab_testing.start_experiment("hybrid_search_alpha")
            logger.info("A/B 테스팅 실험 초기화 완료")
        except Exception as e:
            logger.warning(f"A/B 테스팅 실험 초기화 실패 (기존 실험 존재 가능): {e}")
    
    def _build_workflow(self) -> StateGraph:
        workflow = StateGraph(AppState)
        
        workflow.add_node("query_parser", self.parse_query_node)
        workflow.add_node("hotel_rag", self.hotel_rag_node)
        workflow.add_node("weather_tool", self.weather_tool_node)
        workflow.add_node("safety_info", self.safety_info_node)
        workflow.add_node("google_search", self.google_search_node)
        workflow.add_node("currency_conversion", self.currency_conversion_node)
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
        workflow.add_edge("weather_tool", "safety_info")
        workflow.add_edge("safety_info", "google_search")
        workflow.add_edge("google_search", "currency_conversion")
        workflow.add_edge("currency_conversion", "response_generator")
        
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
            # 기존 호환성 유지: 대부분의 QueryParser.parse는 user_query만 받음
            parsed_info = await self.query_parser.parse(state['user_query'])

            logger.info(f"[QueryParser] 파싱 결과: {parsed_info}")

            updates = {}
            if parsed_info.get('destination'):
                updates['destination'] = parsed_info['destination']
                logger.info("[QueryParser] 목적지 업데이트: %s", parsed_info['destination'])
            else:
                logger.warning("[QueryParser] 목적지 정보 없음. 파싱 결과: %s", parsed_info)

            if parsed_info.get('dates'):
                updates['travel_dates'] = parsed_info['dates']

            # traveler_count가 None이 아닐 때만 업데이트 (기존 인원 유지)
            if parsed_info.get('traveler_count') is not None:
                updates['traveler_count'] = parsed_info['traveler_count']

            if parsed_info.get('preferences'):
                # 단순 덮어쓰기가 아니라 병합하는 것이 더 좋음 (여기서는 일단 유지)
                updates['preferences'] = parsed_info['preferences']

            state = self.state_manager.update_state(state, updates)
            logger.info("[QueryParser] 완료: 목적지=%s, 날짜=%s", state.get('destination'), state.get('travel_dates'))

        except Exception as e:
            logger.error("[QueryParser] 실패: %s", str(e))
            state['error_messages'].append(str(e))
            state['conversation_state'] = ConversationState.ERROR

        return state
    
    async def hotel_rag_node(self, state: AppState) -> AppState:
        """호텔 검색 (A/B 테스팅 + 메트릭 수집)"""
        logger.info("[HotelRAG] 검색 시작")
        state = self.state_manager.log_execution_path(state, "hotel_rag")
        
        # Phase 4: 메트릭 - 실행 시간 추적
        with self.metrics.track_node_execution('hotel_rag'):
            try:
                # A/B 테스팅: alpha 값 실험
                variant = self.ab_testing.assign_variant(
                    "hybrid_search_alpha",
                    state['session_id']
                )
                
                # 실험 변형 정보 저장
                state = self.state_manager.update_state(state, {
                    'ab_experiment_id': 'hybrid_search_alpha',
                    'ab_variant': variant
                })
                
                alpha = variant.get('config', {}).get('alpha', 0.5)
                logger.info(f"[HotelRAG] A/B 테스팅 변형: {variant.get('variant_name')}, alpha={alpha}")
                
                # Phase 4: 메트릭 - A/B 변형 할당 기록
                self.metrics.record_ab_assignment(
                    "hybrid_search_alpha",
                    variant.get('variant_name', 'unknown')
                )
                
                search_params = {
                    'destination': state.get('destination'),
                    'preferences': state.get('preferences'),
                    'budget': state.get('preferences', {}).get('budget_range') if state.get('preferences') else None,
                    'alpha': alpha  # A/B 테스팅 파라미터
                }
                hotel_results = await self.hotel_rag.search(search_params)
                state = self.state_manager.update_state(state, {
                    'hotel_options': hotel_results
                })
                logger.info(f"[HotelRAG] {len(hotel_results)}개 호텔 발견")
                
                # Phase 4: 메트릭 - 검색 품질 기록
                if hotel_results:
                    avg_score = sum(h.combined_score for h in hotel_results) / len(hotel_results)
                    self.metrics.record_search_quality(
                        search_type='hotel',
                        result_count=len(hotel_results),
                        avg_score=avg_score
                    )
                
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
            if weather_data:
                # 정상적으로 날씨 데이터를 받은 경우
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
            else:
                # 2주 제한으로 데이터를 받지 못한 경우
                logger.warning(f"[Weather] 날씨 데이터 없음 (2주 제한 초과 가능)")
                updates = {
                    'weather_forecast': [],
                    'context_memory': {
                        **state.get('context_memory', {}),
                        'weather_limitation_message': '날씨 정보는 오늘부터 2주 이내의 날짜만 제공됩니다. 여행 날짜를 2주 이내로 조정해 주세요.'
                    }
                }
                state = self.state_manager.update_state(state, updates)
            
        except Exception as e:
            logger.error(f"[Weather] 실패: {str(e)}")
        
        return state
    
    async def safety_info_node(self, state: AppState) -> AppState:
        """안전 정보 조회 노드"""
        logger.info("[SafetyInfo] 안전 정보 조회 시작")
        state = self.state_manager.log_execution_path(state, "safety_info")
        
        destination = state.get('destination')
        if not destination:
            logger.warning("[SafetyInfo] 목적지 정보 없음 - 안전 정보 조회 스킵")
            return state
        
        try:
            safety_info = await self.safety_info.get_safety_info(destination)
            
            if safety_info:
                logger.info(f"[SafetyInfo] 안전 정보 조회 성공: {safety_info.country}")
                state = self.state_manager.update_state(state, {
                    'safety_info': safety_info
                })
            else:
                logger.warning(f"[SafetyInfo] 안전 정보 조회 실패: {destination}")
                
        except Exception as e:
            logger.error(f"[SafetyInfo] 조회 중 오류: {str(e)}")
        
        return state
    
    async def google_search_node(self, state: AppState) -> AppState:
        """구글 검색 및 실시간 가격 정보 병합"""
        logger.info(f"[GoogleSearch] 호텔 {len(state.get('hotel_options', [])[:3])}곳 정보 검색 시작")
        
        state = self.state_manager.log_execution_path(state, "google_search")
        if not state.get('hotel_options'):
            return state
            
        # 1. 여행 날짜 추출
        dates = state.get('travel_dates')
        check_in, check_out = None, None
        if dates and len(dates) >= 2:
            check_in, check_out = dates[0], dates[1]
            
        try:
            search_results = []
            updated_hotel_options = [] # 업데이트된 호텔 정보를 담을 리스트
            
            # 상위 3개 호텔에 대해 검색 수행
            for i, hotel in enumerate(state['hotel_options']):
                # 상위 3개만 실제 검색 수행
                if i < 3:
                    # A. 기본 정보 검색
                    search_result_obj = await self.google_search.search_hotel_info(hotel.name, hotel.location)
                    
                    # B. 실시간 가격 검색
                    if check_in and check_out:
                        try:
                            # [수정] 1차 시도: 호텔 이름 + 도시 (정확도 높음)
                            search_query = f"{hotel.name} {hotel.location}"
                            price_data = await self.google_search.search_hotel_prices(
                                search_query, check_in, check_out
                            )
                            
                            # [추가] 1차 실패 시 2차 시도: 호텔 이름만 사용 (검색 범위 확장)
                            if not price_data.get('prices'):
                                logger.info(f"[GoogleSearch] 재검색 시도 (이름만): {hotel.name}")
                                price_data = await self.google_search.search_hotel_prices(
                                    hotel.name, check_in, check_out # 도시명 제외
                                )

                            # 검색된 가격 정보를 HotelOption 객체에 직접 업데이트
                            if price_data and price_data.get('prices'):
                                lowest_price = price_data['prices'][0].get('price')
                                # 기존 가격 범위를 실시간 가격으로 교체
                                hotel.price_range = f"{lowest_price} (실시간)"
                                
                                # 상세 정보를 하이라이트에 추가 (LLM이 참고하도록)
                                price_info = f"실시간 최저가: {lowest_price} ({price_data['prices'][0]['provider']})"
                                hotel.review_highlights.insert(0, price_info)
                                
                                # 구글 결과 리스트에도 추가
                                price_data['type'] = 'price_comparison'
                                search_result_obj.results.insert(0, price_data)
                                
                        except Exception as e:
                            logger.warning(f"[GoogleSearch] 가격 검색 실패 ({hotel.name}): {e}")

                    search_results.append(search_result_obj)
                
                updated_hotel_options.append(hotel)
                
            # 업데이트된 호텔 정보를 상태에 반영
            state = self.state_manager.update_state(state, {
                'google_search_results': search_results,
                'hotel_options': updated_hotel_options 
            })
            
        except Exception as e:
            logger.error(f"[GoogleSearch] 전체 프로세스 실패: {e}")
            pass 
        
        return state
    
    async def currency_conversion_node(self, state: AppState) -> AppState:
        """환율 변환 및 가격 정규화"""
        logger.info("[CurrencyConversion] 호텔 및 항공편 가격 정규화 시작")
        
        state = self.state_manager.log_execution_path(state, "currency_conversion")
        
        try:
            # CurrencyConverterNode 실행
            updated_state = await execute_currency_conversion(state)
            
            # 정규화된 정보 로깅
            if 'normalized_hotels' in updated_state.get('context', {}):
                num_hotels = len(updated_state['context']['normalized_hotels'])
                logger.info("[CurrencyConversion] %s개 호텔 USD 기준 정규화 완료", num_hotels)
            
            if 'normalized_flights' in updated_state.get('context', {}):
                num_flights = len(updated_state['context']['normalized_flights'])
                logger.info("[CurrencyConversion] %s개 항공편 USD 기준 정규화 완료", num_flights)
            
            # 환율 정보 추가
            if 'currency_conversions' in updated_state.get('context', {}):
                conversion_info = updated_state['context']['currency_conversions']
                logger.info("[CurrencyConversion] 기준 통화: %s", conversion_info.get('base_currency'))
            
            return updated_state
            
        except Exception:  # pylint: disable=broad-except
            logger.error("[CurrencyConversion] 환율 변환 실패", exc_info=True)
            # 에러 발생해도 워크플로우 계속 진행
            return state
    
    async def response_generator_node(self, state: AppState) -> AppState:
        """응답 생성 (만족도 추적 포함)"""
        logger.info("[ResponseGenerator] 생성 시작")
        state = self.state_manager.log_execution_path(state, "response_generator")
        
        try:
            # Enrich state with wiki entries for destination (best-effort)
            try:
                wiki_entries = []
                if getattr(self, 'wiki_tool', None) is not None:
                    destination = state.get('destination')
                    if destination:
                        # Query destination and a history-focused query
                        res1 = self.wiki_tool.run(destination)
                        if res1 and not res1.get('error'):
                            wiki_entries.append(res1)
                        res2 = self.wiki_tool.run(f"{destination} 역사")
                        if res2 and not res2.get('error'):
                            wiki_entries.append(res2)
                if wiki_entries:
                    state = self.state_manager.update_state(state, {'wiki_entries': wiki_entries})
            except Exception:
                # non-fatal: continue without wiki entries
                pass

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
            
            # Phase 4: 암묵적 신호 기록
            session_id = state['session_id']
            start_time = self.session_start_times.get(session_id, time.time())
            completion_time = time.time() - start_time
            
            self.satisfaction_tracker.record_implicit_signals(
                session_id=session_id,
                signals={
                    'conversation_turns': len(state['chat_history']),
                    'search_refinements': state['context_memory'].get('search_count', 0),
                    'hotels_viewed': len(state['hotel_options']),
                    'weather_available': bool(state['weather_forecast']),
                    'time_to_completion': completion_time
                }
            )
            
            # 만족도 점수 계산
            satisfaction_score = self.satisfaction_tracker.calculate_satisfaction_score(session_id)
            state = self.state_manager.update_state(state, {
                'satisfaction_score': satisfaction_score
            })
            
            # Phase 4: 메트릭 - 만족도 점수 기록
            self.metrics.record_satisfaction(satisfaction_score)
            
            logger.info(f"[ResponseGenerator] 만족도 점수: {satisfaction_score:.1f}/100")
            
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
        
        # 기타 피드백 처리: 재검색 트리거 단어가 있으면 retry_search로 라우팅
        user_fb = state.get('user_feedback') or state.get('user_query')
        if user_fb and isinstance(user_fb, str) and any(k in user_fb for k in ['다른 호텔', '다른', '다시', '다른 옵션', '다른 추천']):
            state['context_memory']['retry_type'] = 'retry_search'
        else:
            state['context_memory']['retry_type'] = 'complete'
        return state
    
    # ==================== 라우팅 함수들 ====================
    
    def route_after_parsing(self, state: AppState) -> str:
        """파싱 후 경로 결정"""
        if state.get('conversation_state') == ConversationState.ERROR:
            return "error"
        # 만약 사용자의 입력(또는 user_feedback)에 재검색/다른 옵션 요청 키워드가 포함되어 있으면
        # feedback 흐름으로 보낸다 (예: '다른 호텔', '다시 찾아', '다른 옵션')
        user_fb = state.get('user_feedback') or state.get('user_query')
        if user_fb and isinstance(user_fb, str):
            lowered = user_fb.lower()
            if any(k in lowered for k in ['다른 호텔', '다른', '다시', '다른 옵션', '다른 추천']):
                return 'feedback'

        # 목적지가 있으면 검색 수행
        if state.get('destination'):
            return "search"
            
        # 목적지가 없는데 피드백만 있는 경우 (예: "안녕", "고마워")
        return "feedback"
    
    def check_completion(self, state: AppState) -> str:
        if state.get('user_feedback'):
            return "feedback"
        return "complete"
    
    def route_after_feedback(self, state: AppState) -> str:
        rt = state.get('context_memory', {}).get('retry_type')
        if rt == 'retry_search':
            return 'retry_search'
        return 'complete'
    
    # ==================== 실행 메서드 ====================
    
    async def run(self, user_query: str, session_id: str = None) -> Dict[str, Any]:
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        # Phase 4: 세션 시작 시간 기록
        self.session_start_times[session_id] = time.time()
        
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
