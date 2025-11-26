"""
Weather Tool Agent: 날씨 정보 조회 에이전트
"""

import logging
try:
    import aiohttp
    _AIOHTTP_AVAILABLE = True
except Exception:
    aiohttp = None
    _AIOHTTP_AVAILABLE = False
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from src.core.state import WeatherForecast

# LLM 및 프롬프트 라이브러리는 선택적 의존성으로 처리합니다.
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import ChatPromptTemplate
    _LLM_AVAILABLE = True
except Exception:
    ChatGoogleGenerativeAI = None
    ChatPromptTemplate = None
    _LLM_AVAILABLE = False

logger = logging.getLogger(__name__)


class WeatherToolAgent:
    """
    Open-Meteo API를 통한 날씨 정보 조회 및 LLM 기반 분석 에이전트
    """
    
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        
        # LLM 초기화 (선택적)
        if _LLM_AVAILABLE and ChatGoogleGenerativeAI is not None:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    temperature=0.5,
                )
                logger.info("WeatherToolAgent LLM 초기화 완료 (Gemini)")
            except Exception as e:
                logger.warning(f"LLM 초기화 실패, 대체 동작 사용: {e}")
                self.llm = None
        else:
            logger.warning("LLM 라이브러리 미설치: 날씨 조언 생성은 기본 문자열로 대체됩니다.")
            self.llm = None

        logger.info("WeatherToolAgent 초기화 완료 (Open-Meteo API)")
    
    async def get_forecast(self, location: str, dates: List[str], user_context: str = "") -> List[WeatherForecast]:
        """날씨 예보 조회 및 분석"""
        try:
            # 1. 지오코딩
            coordinates = await self._get_coordinates(location)
            if not coordinates:
                logger.warning(f"좌표를 찾을 수 없음: {location}")
                return []
            
            lat, lon = coordinates
            
            # 2. 날짜 범위 계산
            date_range = self._parse_dates(dates)
            if not date_range:
                logger.warning("날짜가 예보 가능 범위(2주)를 벗어남")
                return []  # 2주 이후는 데이터 제공 안 함
                
            start_date, end_date = date_range
            
            # 3. API 호출
            params = {
                'latitude': lat,
                'longitude': lon,
                'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode',
                'timezone': 'auto',
                'start_date': start_date,
                'end_date': end_date
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        forecasts = self._parse_weather_data(data)
                        
                        # 4. LLM을 통한 날씨 분석 및 조언 생성 (비동기 병렬 처리)
                        tasks = [self._generate_weather_advice(f, user_context) for f in forecasts]
                        advices = await asyncio.gather(*tasks)

                        for i, forecast in enumerate(forecasts):
                            forecast.advice = advices[i]
                            
                        return forecasts
                    else:
                        logger.error(f"날씨 API 오류: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"날씨 조회 실패: {str(e)}")
            return []
    
    async def _generate_weather_advice(self, forecast: WeatherForecast, context: str = "") -> str:
        """
        LLM을 사용하여 날씨 조언 생성 (사용자 컨텍스트 반영)
        """
        try:
            # LLM이 없으면 간단한 로컬 요약 반환
            if not self.llm or ChatPromptTemplate is None:
                # 안전한 기본 메시지 (의견/주관적 표현 배제)
                return (
                    f"{forecast.date}: {forecast.description}. "
                    f"기온 {forecast.temperature_min}°C~{forecast.temperature_max}°C, "
                    f"강수량 {forecast.precipitation}mm."
                )

            # 프롬프트에 여행 컨텍스트 추가
            system_msg = "당신은 여행 날씨 전문가입니다."
            if context:
                system_msg += f" 여행자의 성향/목적은 다음과 같습니다: {context}"

            custom_prompt = ChatPromptTemplate.from_messages([
                ("system", system_msg),
                ("human", """
                날짜: {date} ({description})
                기온: {min_temp}°C ~ {max_temp}°C
                강수량: {precipitation}mm

                위 데이터에 기반하여 여행자 성향에 맞춘 3줄 요약 조언을 주세요.
                (옷차림, 주의사항, 맞춤 활동)
                """)
            ])

            messages = custom_prompt.format_messages(
                date=forecast.date,
                description=forecast.description,
                min_temp=forecast.temperature_min,
                max_temp=forecast.temperature_max,
                precipitation=forecast.precipitation
            )
            # ainvoke 사용
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.warning(f"조언 생성 실패: {e}")
            return "날씨 정보를 확인하세요."

    async def _get_coordinates(self, location: str) -> Optional[tuple]:
        params = {'name': location, 'count': 1, 'language': 'en', 'format': 'json'}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.geocoding_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('results'):
                            result = data['results'][0]
                            return (result['latitude'], result['longitude'])
        except Exception as e:
            logger.error(f"지오코딩 실패: {str(e)}")
        return None
    
    def _parse_dates(self, dates: List[str]) -> Optional[tuple]:
        """날짜 파싱 및 유효성 검사 (14일 제한)"""
        if not dates or len(dates) < 2:
            start = datetime.now()
            end = start + timedelta(days=5)
        else:
            try:
                start = datetime.strptime(dates[0], "%Y-%m-%d")
                end = datetime.strptime(dates[1], "%Y-%m-%d")
            except ValueError:
                start = datetime.now()
                end = start + timedelta(days=5)
        
        # Open-Meteo 무료판 한계: 오늘부터 약 14일 후까지만 가능
        max_date = datetime.now() + timedelta(days=14)
        
        # 시작일이 이미 제한을 넘어선 경우 -> API 호출 불가
        if start > max_date:
            return None
            
        # 종료일만 넘어선 경우 -> 종료일을 제한일에 맞춤
        if end > max_date:
            end = max_date
        
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

    def _parse_weather_data(self, data: Dict) -> List[WeatherForecast]:
        forecasts = []
        daily = data.get('daily', {})
        times = daily.get('time', [])
        max_temps = daily.get('temperature_2m_max', [])
        min_temps = daily.get('temperature_2m_min', [])
        precipitations = daily.get('precipitation_sum', [])
        weather_codes = daily.get('weathercode', [])
        
        for i in range(len(times)):
            forecasts.append(WeatherForecast(
                date=times[i],
                temperature_min=min_temps[i] if i < len(min_temps) else 0,
                temperature_max=max_temps[i] if i < len(max_temps) else 0,
                precipitation=precipitations[i] if i < len(precipitations) else 0,
                weather_code=weather_codes[i] if i < len(weather_codes) else 0,
                description=self._get_weather_description(weather_codes[i] if i < len(weather_codes) else 0),
                recommendations=["날씨에 따른 활동 추천"],
                advice="" # 초기값
            ))
        return forecasts
    
    def _get_weather_description(self, code: int) -> str:
        """
        WMO Weather Code를 명확한 한국어 날씨 상태로 매핑
        
        WMO Code 0-99 표준:
        - 0: Clear sky (맑음)
        - 1-3: Mainly clear, partly cloudy, overcast (구름)
        - 45-48: Fog (안개)
        - 51-67: Rain (비)
        - 71-77: Snow (눈)
        - 80-99: Showers/Thunderstorm (소나기/뇌우)
        """
        weather_map = {
            0: "맑음",
            1: "대체로 맑음",
            2: "부분적으로 흐림",
            3: "흐림",
            45: "안개",
            48: "짙은 안개",
            51: "약한 이슬비",
            53: "이슬비",
            55: "강한 이슬비",
            56: "약한 freezing drizzle",
            57: "강한 freezing drizzle",
            61: "약한 비",
            63: "비",
            65: "강한 비",
            66: "약한 freezing rain",
            67: "강한 freezing rain",
            71: "약한 눈",
            73: "눈",
            75: "강한 눈",
            77: "진눈깨비",
            80: "약한 소나기",
            81: "소나기",
            82: "강한 소나기",
            85: "약한 눈 소나기",
            86: "강한 눈 소나기",
            95: "뇌우",
            96: "약한 우박을 동반한 뇌우",
            99: "강한 우박을 동반한 뇌우"
        }
        
        return weather_map.get(code, "알 수 없음")
    
    def format_weather_table(self, forecasts: List[WeatherForecast]) -> str:
        """
        날씨 데이터를 Markdown 테이블 형식으로 포맷팅
        """
        if not forecasts:
            return ""
        
        table = "| 날짜 | 날씨 | 최저기온 | 최고기온 | 강수량 |\n"
        table += "|------|------|----------|----------|--------|\n"
        
        for forecast in forecasts:
            table += f"| {forecast.date} | {forecast.description} | {forecast.temperature_min}°C | {forecast.temperature_max}°C | {forecast.precipitation}mm |\n"
        
        return table
