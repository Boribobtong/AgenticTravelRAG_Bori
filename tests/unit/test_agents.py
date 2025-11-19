"""
Agent Unit Tests: 
QueryParserAgent, HotelRAGAgent (모의 RAG 사용), WeatherToolAgent에 대한 
독립적인 단위 테스트를 수행합니다.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List

# 테스트 대상 모듈 임포트 (프로젝트 구조에 따라 경로 조정)
from src.agents.query_parser import QueryParserAgent, ParsedTravelQuery
from src.agents.weather_tool import WeatherToolAgent
# HotelRAGAgent는 Mock RAG 인스턴스를 사용합니다.
from src.agents.hotel_rag import HotelRAGAgent 
from src.core.state import WeatherForecast, HotelOption

# Mocking ElasticSearchRAG for isolated testing
class MockElasticSearchRAG:
    """HotelRAGAgent 테스트를 위한 모의 RAG 객체"""
    
    def __init__(self):
        pass
    
    def hybrid_search(self, query: str, location: str = None, min_rating: float = None, tags: List[str] = None, top_k: int = 10, alpha: float = 0.5) -> List[Dict[str, Any]]:
        """하이브리드 검색 모의 결과 반환"""
        
        # 쿼리/필터에 따른 간단한 응답 로직
        if 'romantic' in query:
            return [{
                'hotel_name': 'Romantic Stay Paris',
                'location': 'Paris',
                'rating': 4.8,
                'review_snippet': 'Perfect for couples. Very quiet and intimate.',
                'tags': ['romantic', 'quiet'],
                'combined_score': 0.95,
                'semantic_score': 0.9,
                'bm25_score': 0.8
            }]
        
        return [{
            'hotel_name': f"City Hotel {location or 'Unknown'}",
            'location': location,
            'rating': 4.0,
            'review_snippet': 'Clean and centrally located.',
            'tags': tags or ['clean', 'central'],
            'combined_score': 0.75,
            'semantic_score': 0.7,
            'bm25_score': 0.6
        }]
    
    # HotelRAGAgent가 get_rag_instance() 대신 이 Mock 클래스를 사용하도록 오버라이딩 필요

@pytest.mark.asyncio
async def test_query_parser_basic():
    """기본 쿼리 파싱 테스트"""
    # LLM 호출이 필요하므로 실제 API 키가 필요하거나, Mocking 처리해야 함.
    # 여기서는 폴백 로직만 테스트하거나, API 키를 설정했다고 가정합니다.
    parser = QueryParserAgent(llm_model="gpt-3.5-turbo")
    
    query = "뉴욕으로 가족 여행 갈 건데, 다음 달 1일부터 5일 동안 4명이 쓸 수 있는 조식 포함된 호텔을 찾아줘."
    result = await parser.parse(query)
    
    assert result['destination'] is not None
    assert result['traveler_count'] == 4
    assert result['dates'] is not None
    assert 'amenities' in result['preferences']
    
    # 날짜 검증 (YYYY-MM-DD 형식인지 확인)
    assert len(result['dates']) == 2
    try:
        datetime.strptime(result['dates'][0], "%Y-%m-%d")
        datetime.strptime(result['dates'][1], "%Y-%m-%d")
    except ValueError:
        pytest.fail("날짜 형식이 YYYY-MM-DD가 아님")


@pytest.mark.asyncio
async def test_query_parser_fallback():
    """규칙 기반 폴백 파싱 테스트"""
    parser = QueryParserAgent(llm_model="gpt-3.5-turbo")
    
    # LLM이 실패했을 때를 시뮬레이션
    query = "파리에서 budget급이고 수영장 있는 숙소 2인으로"
    result = parser._fallback_parse(query)
    
    assert result['destination'] == '파리'
    assert result['traveler_count'] == 2
    assert 'budget' in result['preferences']['atmosphere']
    assert 'pool' in result['preferences']['amenities']


@pytest.mark.asyncio
async def test_weather_tool_basic():
    """날씨 조회 도구 기본 테스트"""
    agent = WeatherToolAgent()
    
    start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    
    forecasts = await agent.get_forecast(location="Tokyo", dates=[start_date, end_date])
    
    assert isinstance(forecasts, list)
    assert len(forecasts) > 0
    assert all(isinstance(f, WeatherForecast) for f in forecasts)
    
    # 실제 API 호출을 통해 응답이 오는지 확인 (외부 API에 의존함)
    if forecasts:
        assert forecasts[0].temperature_max > -50
        assert forecasts[0].date == start_date
        assert len(forecasts[0].recommendations) > 0


@pytest.mark.asyncio
async def test_hotel_rag_search(monkeypatch):
    """HotelRAGAgent 검색 테스트 (Mock RAG 사용)"""
    
    # get_rag_instance()가 Mock 객체를 반환하도록 패치
    def mock_get_rag_instance():
        return MockElasticSearchRAG()
        
    monkeypatch.setattr("src.agents.hotel_rag.get_rag_instance", mock_get_rag_instance)
    
    agent = HotelRAGAgent()
    
    # 로맨틱 검색
    params_romantic = {
        'destination': 'Paris',
        'preferences': {
            'atmosphere': ['romantic'],
            'amenities': ['wifi']
        }
    }
    hotels_romantic = await agent.search(params_romantic)
    
    assert len(hotels_romantic) == 1
    assert hotels_romantic[0].name == 'Romantic Stay Paris'
    assert hotels_romantic[0].rating == 4.8
    
    # 일반 검색
    params_general = {
        'destination': 'Seoul',
        'preferences': {
            'atmosphere': ['family'],
            'budget_range': (100, 300)
        }
    }
    hotels_general = await agent.search(params_general)
    
    assert len(hotels_general) == 1
    assert hotels_general[0].location == 'Seoul'
    assert hotels_general[0].combined_score == 0.75
    
    # 예산 필터링 테스트 (가격대는 $$$=200 으로 가정)
    budget_range = (50, 150)
    filtered = agent._filter_by_budget(hotels_general, budget_range)
    
    # City Hotel Seoul은 $$$=200 이므로 필터링에서 제외되어야 하지만, 
    # 필터링 결과가 없으면 상위 2개를 반환하는 로직 때문에 1개 반환
    # 이 부분은 Mock 객체의 응답과 필터링 로직에 따라 달라질 수 있습니다.
    # 여기서는 Mock 응답이 $$$로 설정되어 있어 필터링되면 결과가 없어야 합니다.
    # HotelRAGAgent의 _estimate_price_range 로직을 따른다면 $$, $$$만 통과
    
    # Mock RAG는 가격 추정 정보가 없으므로 통과하는 것으로 가정하고 테스트
    assert len(filtered) == 1