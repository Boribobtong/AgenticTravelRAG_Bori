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
import json
import logging
import traceback
import time
from datetime import datetime, timedelta
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.weather_tool import WeatherToolAgent
from dotenv import load_dotenv

# 환경 변수 로드 (API 키 등)
load_dotenv(os.path.join(os.path.dirname(__file__), '../config/.env'))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def save_results(location, results, output_dir="examples/demo_results"):
    """결과를 JSON 파일로 저장"""
    Path(output_dir).mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/weather_{location}_{timestamp}.json"
    
    output = {
        "metadata": {
            "location": location,
            "query_time": datetime.now().isoformat(),
            "forecast_count": len(results)
        },
        "forecasts": [
            {
                "date": f.date,
                "temperature": {
                    "min": f.temperature_min,
                    "max": f.temperature_max,
                    "unit": "celsius"
                },
                "precipitation": {
                    "amount": f.precipitation,
                    "unit": "mm"
                },
                "weather_code": f.weather_code,
                "description": f.description,
                "llm_advice": f.advice,
                "recommendations": f.recommendations
            }
            for f in results
        ]
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"💾 결과 저장: {filename}")
    return filename

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

from src.core.state import WeatherForecast

def generate_mock_weather(location, dates):
    """테스트용 Mock 날씨 데이터 생성"""
    mock_forecasts = []
    start = datetime.strptime(dates[0], "%Y-%m-%d")
    end = datetime.strptime(dates[1], "%Y-%m-%d")
    delta = (end - start).days + 1
    
    for i in range(delta):
        current_date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        mock_forecasts.append(WeatherForecast(
            date=current_date,
            temperature_min=10.0,
            temperature_max=20.0,
            precipitation=0.0,
            weather_code=0,
            description="Mock Clear Sky",
            recommendations=["Mock Recommendation"],
            advice="This is a mock advice for testing purposes."
        ))
    return mock_forecasts

async def compare_mock_vs_real(agent, location, dates):
    """Mock 데이터와 실제 API 결과 비교"""
    print("\n📊 Mock vs Real 비교 모드")
    print("="*60)
    
    # Mock 데이터 생성 (빠른 검증)
    mock_results = generate_mock_weather(location, dates)
    print(f"Mock 결과: {len(mock_results)}일 생성됨")
    
    # 실제 API 호출
    print("실제 API 호출 중...")
    real_results = await agent.get_forecast(location, dates)
    print(f"Real 결과: {len(real_results)}일 수신됨")
    
    # 구조 비교
    if len(mock_results) == len(real_results):
        print("✅ 결과 개수 일치")
    else:
        print(f"⚠️ 결과 개수 불일치: Mock({len(mock_results)}) vs Real({len(real_results)})")
    
    # 필드 존재 여부 비교
    for i, (mock, real) in enumerate(zip(mock_results, real_results)):
        print(f"\n날짜 {real.date}:")
        print(f"  Mock advice 길이: {len(mock.advice)}")
        print(f"  Real advice 길이: {len(real.advice)}")
        
        if len(real.advice) > 0:
             print("  ✅ Real advice 생성 성공")
        else:
             print("  ❌ Real advice 생성 실패")

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
    parser.add_argument(
        '--save', 
        action='store_true',
        help='결과를 JSON 파일로 저장'
    )
    parser.add_argument(
        '--compare', 
        action='store_true',
        help='Mock 데이터와 실제 결과 비교'
    )
    parser.add_argument(
        '--korea-cities', 
        action='store_true',
        help='한국 10대 도시 테스트 실행'
    )
    return parser.parse_args()

async def demo_weather_agent(args):
    print("🌤️ Weather Agent Demo 시작...")
    print("=" * 50)
    
    agent = WeatherToolAgent()
    
    # 비교 모드 실행
    if args.compare:
        start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=args.days)).strftime("%Y-%m-%d")
        dates = [start_date, end_date]
        await compare_mock_vs_real(agent, args.location, dates)
        return

    # 시나리오 결정
    if args.all_scenarios:
        scenarios = [
            {"location": "Paris", "days": 3, "desc": "유럽 도시, 짧은 기간 (3일)"},
            {"location": "Tokyo", "days": 5, "desc": "아시아 도시, 중간 기간 (5일)"},
            {"location": "New York", "days": 1, "desc": "미국 도시, 하루 (1일)"},
        ]
    elif args.korea_cities:
        korea_cities = [
            "Seoul", "Busan", "Incheon", "Daegu", "Daejeon", 
            "Gwangju", "Ulsan", "Suwon", "Changwon", "Jeju"
        ]
        scenarios = [
            {"location": city, "days": 3, "desc": f"한국 주요 도시: {city} (3일)"}
            for city in korea_cities
        ]
    else:
        scenarios = [
            {"location": args.location, "days": args.days, "desc": f"사용자 지정: {args.location}, {args.days}일"}
        ]

    # tqdm 라이브러리 시도
    try:
        from tqdm import tqdm
        iterator = tqdm(scenarios, desc="전체 시나리오 진행")
    except ImportError:
        iterator = scenarios
        print("ℹ️ tqdm 라이브러리가 없어 일반 진행 표시를 사용합니다.")

    for scenario in iterator:
        location = scenario["location"]
        days = scenario["days"]
        desc = scenario["desc"]
        
        # tqdm 사용 시 print 대신 tqdm.write 사용 권장
        printer = tqdm.write if 'tqdm' in locals() else print

        printer(f"\n{'='*60}")
        printer(f"🧪 테스트 시나리오: {desc}")
        printer(f"{'='*60}")

        start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        dates = [start_date, end_date]
        
        printer(f"\n📍 위치: {location}")
        printer(f"📅 날짜: {dates}")
        
        printer("\n🔄 날씨 정보 조회 및 분석 중...")
        
        try:
            # 실행 시간 측정
            start_time = time.time()
            logger.info(f"날씨 조회 시작: {location}, {dates}")
            
            results = await agent.get_forecast(location, dates)
            
            elapsed = time.time() - start_time
            logger.info(f"API 호출 완료: {elapsed:.2f}초")
            
            if not results:
                logger.warning("결과가 비어있습니다")
                printer("❌ 날씨 정보를 가져오지 못했습니다.")
                continue

            printer(f"\n✅ 총 {len(results)}일치 예보 수신 완료! (소요시간: {elapsed:.2f}초)")
            
            for forecast in results:
                printer("-" * 50)
                printer(f"📅 날짜: {forecast.date}")
                printer(f"🌡️ 기온: {forecast.temperature_min}°C ~ {forecast.temperature_max}°C")
                printer(f"🌧️ 강수량: {forecast.precipitation}mm")
                printer(f"📝 날씨: {forecast.description}")
                printer(f"🤖 [LLM 조언]:\n{forecast.advice}")
                
                # 데이터 검증 수행
                errors = validate_forecast(forecast)
                if errors:
                    printer(f"⚠️ [검증 실패]:")
                    for error in errors:
                        printer(f"   - {error}")
                else:
                    printer("✅ [검증 통과]")
                
                printer("-" * 50)
            
            # 결과 저장
            if args.save:
                save_results(location, results)
                
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
