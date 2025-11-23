"""
Weather Agent Demo: Weather Agent 사용 예제

실제 Open-Meteo API와 Google Gemini API를 호출하여
Weather Agent의 동작을 시연합니다.

사용법:
    python examples/weather_agent_demo.py
"""

import argparse

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

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Weather Agent Demo - 실제 API 호출 테스트'
    )
    parser.add_argument(
        '--location', 
        default='Paris', 
        help='조회할 도시 이름 (예: Paris, Tokyo, Seoul)'
    )
    parser.add_argument(
        '--days', 
        type=int, 
        default=3, 
        help='예보 일수 (1-14)'
    )
    parser.add_argument(
        '--all-scenarios', 
        action='store_true',
        help='모든 시나리오 실행'
    )
    return parser.parse_args()

import logging
import traceback
import time

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def validate_forecast(forecast):
    """예보 데이터의 무결성 검증"""
    errors = []
    
    # 필수 필드 확인
    if not forecast.date:
        errors.append("날짜가 비어있음")
    
    # 기온 범위 검증 (-50°C ~ 60°C)
    if not (-50 <= forecast.temperature_min <= 60):
        errors.append(f"비정상 최저기온: {forecast.temperature_min}°C")
    
    if not (-50 <= forecast.temperature_max <= 60):
        errors.append(f"비정상 최고기온: {forecast.temperature_max}°C")
    
    # 논리적 검증
    if forecast.temperature_max < forecast.temperature_min:
        errors.append(f"최고기온({forecast.temperature_max}) < 최저기온({forecast.temperature_min})")
    
    # LLM 조언 생성 확인
    if not forecast.advice or len(forecast.advice) < 10:
        errors.append("LLM 조언이 충분하지 않음")
    
    # 강수량 음수 확인
    if forecast.precipitation < 0:
        errors.append(f"음수 강수량: {forecast.precipitation}mm")
    
    return errors

async def demo_weather_agent(args):
    print("🌤️ Weather Agent Demo 시작...")
    print("=" * 50)
    
    agent = WeatherToolAgent()
    
    # 시나리오 결정
    if args.all_scenarios:
        scenarios = [
            {"location": "Paris", "days": 3, "desc": "유럽 도시, 짧은 기간 (3일)"},
            {"location": "Tokyo", "days": 5, "desc": "아시아 도시, 중간 기간 (5일)"},
            {"location": "New York", "days": 1, "desc": "미국 도시, 하루 (1일)"},
        ]
    else:
        scenarios = [
            {"location": args.location, "days": args.days, "desc": f"사용자 지정: {args.location}, {args.days}일"}
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
        
        try:
            # 실행 시간 측정
            start_time = time.time()
            logger.info(f"날씨 조회 시작: {location}, {dates}")
            
            results = await agent.get_forecast(location, dates)
            
            elapsed = time.time() - start_time
            logger.info(f"API 호출 완료: {elapsed:.2f}초")
            
            if not results:
                logger.warning("결과가 비어있습니다")
                print("❌ 날씨 정보를 가져오지 못했습니다.")
                continue

            print(f"\n✅ 총 {len(results)}일치 예보 수신 완료! (소요시간: {elapsed:.2f}초)")
            
            for forecast in results:
                print("-" * 50)
                print(f"📅 날짜: {forecast.date}")
                print(f"🌡️ 기온: {forecast.temperature_min}°C ~ {forecast.temperature_max}°C")
                print(f"🌧️ 강수량: {forecast.precipitation}mm")
                print(f"📝 날씨: {forecast.description}")
                print(f"🤖 [LLM 조언]:\n{forecast.advice}")
                
                # 데이터 검증 수행
                errors = validate_forecast(forecast)
                if errors:
                    print(f"⚠️ [검증 실패]:")
                    for error in errors:
                        print(f"   - {error}")
                else:
                    print("✅ [검증 통과]")
                
                print("-" * 50)
                
        except Exception as e:
            logger.error(f"예상치 못한 오류 발생: {type(e).__name__}")
            logger.error(f"상세: {str(e)}")
            traceback.print_exc()
            continue
        
        # API 호출 간 잠시 대기 (Rate Limit 방지)
        if len(scenarios) > 1:
            await asyncio.sleep(1)

if __name__ == "__main__":
    args = parse_arguments()
    asyncio.run(demo_weather_agent(args))
