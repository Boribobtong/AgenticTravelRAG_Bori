import os
import sys
import asyncio
from datetime import datetime, timedelta
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.agents.weather_tool import WeatherToolAgent, _AIOHTTP_AVAILABLE


@pytest.mark.integration
@pytest.mark.asyncio
async def test_weather_get_forecast_live():
    """Integration test: call Open-Meteo via WeatherToolAgent and verify parsing."""
    if not _AIOHTTP_AVAILABLE:
        pytest.skip("aiohttp not available; skip integration test")

    agent = WeatherToolAgent()

    start = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    forecasts = await agent.get_forecast("Seoul", [start, end])

    # Basic assertions about returned structure
    assert isinstance(forecasts, list)
    assert len(forecasts) >= 1
    f = forecasts[0]
    assert hasattr(f, 'date') and hasattr(f, 'temperature_min')
    assert '°' not in f.description  # description should be short Korean word
"""
Integration Tests for Weather Agent: 실제 API 호출 테스트

실제 Open-Meteo API와 Google Gemini API를 호출하여
Weather Agent의 전체 동작을 검증합니다.

주의: 이 테스트는 실제 API를 호출하므로:
- 네트워크 연결 필요
- API 키 필요 (.env 파일)
- 실행 시간이 느림
- CI/CD에서는 선택적으로 실행 권장
"""

import pytest
import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv("config/.env")

from src.agents.weather_tool import WeatherToolAgent
from src.core.state import WeatherForecast


@pytest.mark.integration
@pytest.mark.asyncio
async def test_weather_agent_real_api():
    """실제 API를 사용한 Weather Agent 전체 플로우 테스트"""
    
    # API 키 확인
    assert os.getenv("GOOGLE_API_KEY"), "GOOGLE_API_KEY가 설정되지 않았습니다"
    
    agent = WeatherToolAgent()
    
    # 테스트 파라미터
    location = "Paris"
    start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    dates = [start_date, end_date]
    
    # 실제 API 호출
    forecasts = await agent.get_forecast(location, dates)
    
    # 검증
    assert isinstance(forecasts, list), "예보 결과는 리스트여야 합니다"
    assert len(forecasts) > 0, "최소 1일 이상의 예보가 있어야 합니다"
    
    # 첫 번째 예보 상세 검증
    first_forecast = forecasts[0]
    assert isinstance(first_forecast, WeatherForecast), "예보는 WeatherForecast 타입이어야 합니다"
    assert first_forecast.date is not None, "날짜가 있어야 합니다"
    assert isinstance(first_forecast.temperature_min, (int, float)), "최저 기온은 숫자여야 합니다"
    assert isinstance(first_forecast.temperature_max, (int, float)), "최고 기온은 숫자여야 합니다"
    assert first_forecast.description != "", "날씨 설명이 있어야 합니다"
    
    # LLM 조언 검증
    assert first_forecast.advice != "", "LLM 조언이 생성되어야 합니다"
    assert len(first_forecast.advice) > 10, "조언은 충분한 길이여야 합니다"
    
    print(f"\n✅ 테스트 성공: {location}의 {len(forecasts)}일 예보 수신")
    print(f"📅 첫 날짜: {first_forecast.date}")
    print(f"🌡️ 기온: {first_forecast.temperature_min}°C ~ {first_forecast.temperature_max}°C")
    print(f"🤖 조언: {first_forecast.advice[:100]}...")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_weather_agent_multiple_locations():
    """여러 도시의 날씨 조회 테스트"""
    
    agent = WeatherToolAgent()
    locations = ["Tokyo", "London", "New York"]
    start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    
    results = {}
    for location in locations:
        forecasts = await agent.get_forecast(location, [start_date, end_date])
        results[location] = forecasts
        
        # 각 도시별 검증
        assert len(forecasts) > 0, f"{location}의 예보가 없습니다"
        assert forecasts[0].advice != "", f"{location}의 조언이 생성되지 않았습니다"
    
    print(f"\n✅ {len(locations)}개 도시 날씨 조회 성공: {', '.join(locations)}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_weather_agent_far_future_fallback():
    """먼 미래 날짜에 대한 폴백 로직 테스트"""
    
    agent = WeatherToolAgent()
    
    # 30일 후 (API 제한 초과)
    far_future = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    far_future_end = (datetime.now() + timedelta(days=32)).strftime("%Y-%m-%d")
    
    forecasts = await agent.get_forecast("Paris", [far_future, far_future_end])
    
    # 폴백 데이터 검증
    assert isinstance(forecasts, list), "폴백 데이터도 리스트여야 합니다"
    if len(forecasts) > 0:
        assert forecasts[0].description != "", "폴백 데이터에도 설명이 있어야 합니다"
        print(f"\n✅ 폴백 로직 작동: {forecasts[0].description}")


if __name__ == "__main__":
    # 개발 중 빠른 실행용
    asyncio.run(test_weather_agent_real_api())
