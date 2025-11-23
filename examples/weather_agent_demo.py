"""
Weather Agent Demo: Weather Agent 사용 예제

실제 Open-Meteo API와 Google Gemini API를 호출하여
Weather Agent의 동작을 시연합니다.

사용법:
    python examples/weather_agent_demo.py
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.weather_tool import WeatherToolAgent
from dotenv import load_dotenv

# 환경 변수 로드 (API 키 등)
load_dotenv(os.path.join(os.path.dirname(__file__), '../config/.env'))

async def demo_weather_agent():
    print("🌤️ Weather Agent Demo 시작...")
    print("=" * 50)
    
    agent = WeatherToolAgent()
    
    # 다양한 테스트 시나리오 정의
    scenarios = [
        {"location": "Paris", "days": 3, "desc": "유럽 도시, 짧은 기간 (3일)"},
        {"location": "Tokyo", "days": 5, "desc": "아시아 도시, 중간 기간 (5일)"},
        {"location": "New York", "days": 1, "desc": "미국 도시, 하루 (1일)"},
    ]

    for scenario in scenarios:
        location = scenario["location"]
        days = scenario["days"]
        desc = scenario["desc"]

        print(f"\n{'='*60}")
        print(f"🧪 테스트 시나리오: {desc}")
        print(f"{'='*60}")

        start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        dates = [start_date, end_date]
        
        print(f"\n📍 위치: {location}")
        print(f"📅 날짜: {dates}")
        
        print("\n🔄 날씨 정보 조회 및 분석 중...")
        results = await agent.get_forecast(location, dates)
        
        if not results:
            print("❌ 날씨 정보를 가져오지 못했습니다.")
            continue

        print(f"\n✅ 총 {len(results)}일치 예보 수신 완료!")
        
        for forecast in results:
            print("-" * 50)
            print(f"📅 날짜: {forecast.date}")
            print(f"🌡️ 기온: {forecast.temperature_min}°C ~ {forecast.temperature_max}°C")
            print(f"🌧️ 강수량: {forecast.precipitation}mm")
            print(f"📝 날씨: {forecast.description}")
            print(f"🤖 [LLM 조언]:\n{forecast.advice}")
            print("-" * 50)
        
        # API 호출 간 잠시 대기 (Rate Limit 방지)
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(demo_weather_agent())
