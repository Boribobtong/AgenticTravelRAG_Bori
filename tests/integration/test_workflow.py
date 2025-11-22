"""
Workflow Integration Tests: 
LangGraph 워크플로우의 노드 간 연결 및 상태 전파를 테스트합니다.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from typing import Dict, Any

# 테스트 대상 모듈 임포트
from src.core.workflow import ARTWorkflow
from src.core.state import AppState, ConversationState, HotelOption, WeatherForecast
from src.agents.query_parser import ParsedTravelQuery

# 모의 데이터 설정
MOCK_HOTEL = HotelOption(
    hotel_id="test1",
    name="Test Hotel",
    location="Paris",
    rating=4.5,
    review_count=100,
    price_range="$$$",
    amenities=['wifi', 'pool'],
    review_highlights=['clean', 'friendly'],
    semantic_score=0.9,
    bm25_score=0.8,
    combined_score=0.85
)

MOCK_WEATHER = WeatherForecast(
    date="2025-12-15",
    temperature_min=5.0,
    temperature_max=10.0,
    precipitation=0.0,
    weather_code=1,
    description="맑음",
    recommendations=['야외 활동']
)

# ==================== 에이전트 Mocking ====================

@pytest.fixture
def mock_agents():
    """모든 에이전트를 비동기 모의 객체(AsyncMock)로 설정하는 픽스처"""
    
    # 1. QueryParserAgent Mock
    mock_parser = MagicMock()
    mock_parser.parse = AsyncMock(return_value={
        'destination': 'Paris',
        'dates': ['2025-12-15', '2025-12-18'],
        'traveler_count': 2,
        'preferences': {
            'atmosphere': ['romantic'],
            'amenities': ['wifi']
        }
    })
    
    # 2. HotelRAGAgent Mock
    mock_hotel_rag = MagicMock()
    mock_hotel_rag.search = AsyncMock(return_value=[MOCK_HOTEL])
    
    # 3. WeatherToolAgent Mock
    mock_weather_tool = MagicMock()
    mock_weather_tool.get_forecast = AsyncMock(return_value=[MOCK_WEATHER])
    
    # 4. GoogleSearchAgent Mock
    mock_google_search = MagicMock()
    mock_google_search.search_hotel_info = AsyncMock(return_value=[]) 
    
    # 5. ResponseGeneratorAgent Mock
    mock_generator = MagicMock()
    mock_generator.generate = AsyncMock(return_value={
        'destination': 'Paris',
        'summary': 'Final generated itinerary for Paris.',
        'hotels': [{'name': 'Test Hotel'}],
        'weather_summary': 'Clear skies.'
    })
    
    return {
        'parser': mock_parser,
        'hotel_rag': mock_hotel_rag,
        'weather_tool': mock_weather_tool,
        'google_search': mock_google_search,
        'generator': mock_generator
    }

@pytest.mark.asyncio
async def test_full_workflow_execution(mock_agents, monkeypatch):
    """전체 워크플로우가 성공적으로 실행되는지 테스트 (Mock 사용)"""
    
    # 에이전트 클래스 자체를 Mock으로 대체
    monkeypatch.setattr("src.core.workflow.QueryParserAgent", lambda: mock_agents['parser'])
    monkeypatch.setattr("src.core.workflow.HotelRAGAgent", lambda: mock_agents['hotel_rag'])
    monkeypatch.setattr("src.core.workflow.WeatherToolAgent", lambda: mock_agents['weather_tool'])
    monkeypatch.setattr("src.core.workflow.GoogleSearchAgent", lambda: mock_agents['google_search'])
    monkeypatch.setattr("src.core.workflow.ResponseGeneratorAgent", lambda: mock_agents['generator'])
    
    # 워크플로우 인스턴스 생성
    workflow = ARTWorkflow()
    
    initial_query = "파리 여행 계획 좀 짜줘. 12월 15일부터 3일간."
    result = await workflow.run(user_query=initial_query, session_id="test_session_1")
    
    # 1. 결과 검증
    assert result['success'] is True
    assert result['session_id'] == "test_session_1"
    assert result['itinerary']['destination'] == 'Paris'
    assert "Final generated itinerary" in result['itinerary']['summary']
    assert len(result['hotels']) == 1
    assert len(result['weather']) == 1
    
    # 2. 실행 경로 검증 (모든 노드가 순서대로 실행되었는지)
    expected_path = [
        'query_parser', 
        'hotel_rag',     # 'both' 라우팅으로 인해 호텔/날씨 둘 다 실행
        'weather_tool', 
        'google_search',
        'response_generator'
    ]
    assert result['execution_path'] == expected_path
    
    # 3. 에이전트 호출 확인
    mock_agents['parser'].parse.assert_called_once_with(initial_query)
    mock_agents['hotel_rag'].search.assert_called_once()
    mock_agents['weather_tool'].get_forecast.assert_called_once()
    mock_agents['google_search'].search_hotel_info.assert_called_once()
    mock_agents['generator'].generate.assert_called_once()


@pytest.mark.asyncio
async def test_feedback_handling(mock_agents, monkeypatch):
    """피드백 기반 재실행 로직 테스트"""
    
    # 에이전트 Mocking (이전 테스트와 동일)
    monkeypatch.setattr("src.core.workflow.QueryParserAgent", lambda: mock_agents['parser'])
    monkeypatch.setattr("src.core.workflow.HotelRAGAgent", lambda: mock_agents['hotel_rag'])
    monkeypatch.setattr("src.core.workflow.WeatherToolAgent", lambda: mock_agents['weather_tool'])
    monkeypatch.setattr("src.core.workflow.GoogleSearchAgent", lambda: mock_agents['google_search'])
    monkeypatch.setattr("src.core.workflow.ResponseGeneratorAgent", lambda: mock_agents['generator'])
    
    workflow = ARTWorkflow()
    session_id = "test_session_2"
    
    # 1. 초기 상태 생성
    initial_state = workflow.state_manager.create_initial_state(session_id, "파리 여행 계획")
    initial_state['destination'] = 'Paris'
    initial_state['hotel_options'] = [MOCK_HOTEL]
    initial_state['conversation_state'] = ConversationState.COMPLETED
    
    # 2. 피드백 입력: 재검색 트리거 단어("다른 호텔") 포함
    feedback = "호텔이 너무 비싸. 다른 호텔을 찾아줘."
    
    # 3. Multi-turn 대화 계속
    result = await workflow.continue_conversation(feedback, session_id, initial_state)
    
    # 4. 실행 경로 검증
    assert 'feedback_handler' in result['execution_path']
    assert 'hotel_rag' in result['execution_path']
    
    # hotel_rag가 호출되었는지 확인
    mock_agents['hotel_rag'].search.assert_called()
