"""
Agent Unit Tests: 
QueryParserAgent, HotelRAGAgent, WeatherToolAgent에 대한 단위 테스트.
실제 API 호출 대신 Mock 객체를 사용하여 환경 변수나 네트워크 문제 없이 로직을 검증합니다.
"""

import pytest
import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dotenv import load_dotenv
from unittest.mock import MagicMock, patch, AsyncMock

# [1] .env 파일 로드
load_dotenv("config/.env")

# [2] 프록시 환경 변수 제거
proxy_keys = ["http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "OPENAI_PROXY"]
for key in proxy_keys:
    if key in os.environ:
        del os.environ[key]

from src.agents.query_parser import QueryParserAgent
from src.agents.weather_tool import WeatherToolAgent
from src.agents.hotel_rag import HotelRAGAgent 
from src.core.state import WeatherForecast

# Mocking ElasticSearchRAG
class MockElasticSearchRAG:
    def __init__(self): pass
    def hybrid_search(self, query, location=None, min_rating=None, tags=None, top_k=10, alpha=0.5):
        if "romantic" in query:
            return [{
                "hotel_name": "Romantic Stay Paris",
                "location": "Paris",
                "rating": 4.8,
                "review_snippet": "Perfect for couples. Very quiet and intimate.",
                "tags": ["romantic", "quiet"],
                "combined_score": 0.95,
                "semantic_score": 0.9,
                "bm25_score": 0.8
            }]
        # [수정됨] f-string 내부 따옴표 충돌 해결 (" -> ')
        return [{
            "hotel_name": f"City Hotel {location or 'Unknown'}",
            "location": location,
            "rating": 4.0,
            "review_snippet": "Clean and centrally located.",
            "tags": tags or ["clean", "central"],
            "combined_score": 0.75,
            "semantic_score": 0.7,
            "bm25_score": 0.6
        }]

@pytest.mark.asyncio
async def test_query_parser_basic():
    """기본 쿼리 파싱 테스트 - LLM 호출 Mocking"""
    
    with patch('src.agents.query_parser.ChatOpenAI') as MockChatOpenAI:
        mock_llm = MagicMock()
        # special_requirements 필드 추가
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "destination": "뉴욕",
            "check_in_date": "2024-12-01",
            "check_out_date": "2024-12-06",
            "traveler_count": 4,
            "budget_min": 100.0,
            "budget_max": 500.0,
            "accommodation_type": "hotel",
            "amenity_requirements": ["wifi", "breakfast"],
            "special_requirements": null
        }
        '''
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        MockChatOpenAI.return_value = mock_llm

        parser = QueryParserAgent(llm_model="gpt-3.5-turbo")
        
        query = "뉴욕으로 4명 여행 가요."
        result = await parser.parse(query)
        
        assert result['destination'] == "뉴욕"
        assert result['traveler_count'] == 4
        assert result['dates'][0] == "2024-12-01"

@pytest.mark.asyncio
async def test_query_parser_fallback():
    """규칙 기반 폴백 파싱 테스트 - LLM 실패 시나리오"""
    
    with patch('src.agents.query_parser.ChatOpenAI') as MockChatOpenAI:
        mock_llm = MagicMock()
        mock_llm.ainvoke.side_effect = Exception("API Error")
        MockChatOpenAI.return_value = mock_llm
        
        parser = QueryParserAgent()
        
        # 영어 쿼리로 테스트
        query = "Trip to Paris for 2 people budget hotel"
        result = parser._fallback_parse(query)
        
        assert result['destination'] == "Paris"
        assert result['traveler_count'] == 2

@pytest.mark.asyncio
async def test_weather_tool_basic():
    """날씨 조회 도구 기본 테스트"""
    agent = WeatherToolAgent()
    start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    
    forecasts = await agent.get_forecast(location="Tokyo", dates=[start_date, end_date])
    
    assert isinstance(forecasts, list)

@pytest.mark.asyncio
async def test_hotel_rag_search(monkeypatch):
    """HotelRAGAgent 검색 테스트"""
    def mock_get_rag_instance(): return MockElasticSearchRAG()
    monkeypatch.setattr("src.agents.hotel_rag.get_rag_instance", mock_get_rag_instance)
    
    agent = HotelRAGAgent()
    params = {"destination": "Paris", "preferences": {"atmosphere": ["romantic"]}}
    hotels = await agent.search(params)
    
    assert len(hotels) == 1
    assert hotels[0].name == "Romantic Stay Paris"
