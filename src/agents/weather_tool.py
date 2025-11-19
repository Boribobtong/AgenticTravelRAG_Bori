"""
Weather Tool Agent: 날씨 정보 조회 에이전트

Open-Meteo API를 사용하여 무료로 날씨 정보를 조회합니다.
"""

import logging
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from src.core.state import WeatherForecast

logger = logging.getLogger(__name__)


class WeatherToolAgent:
    """
    Open-Meteo API를 통한 날씨 정보 조회 에이전트
    """
    
    def __init__(self):
        """초기화"""
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        logger.info("WeatherToolAgent 초기화 완료 (Open-Meteo API)")
    
    async def get_forecast(self, location: str, dates: List[str]) -> List[WeatherForecast]:
        """
        날씨 예보 조회
        
        Args:
            location: 위치 (도시명)
            dates: [체크인, 체크아웃] 날짜
            
        Returns:
            WeatherForecast 리스트
        """
        
        try:
            # 1. 지오코딩으로 좌표 얻기
            coordinates = await self._get_coordinates(location)
            if not coordinates:
                logger.warning(f"좌표를 찾을 수 없음: {location}")
                return []
            
            lat, lon = coordinates
            
            # 2. 날짜 범위 계산
            start_date, end_date = self._parse_dates(dates)
            
            # 3. 날씨 API 호출
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
                        return self._parse_weather_data(data)
                    else:
                        logger.error(f"날씨 API 오류: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"날씨 조회 실패: {str(e)}")
            return []
    
    async def _get_coordinates(self, location: str) -> Optional[tuple]:
        """
        지오코딩으로 좌표 얻기
        
        Args:
            location: 위치명
            
        Returns:
            (위도, 경도) 튜플 또는 None
        """
        
        params = {
            'name': location,
            'count': 1,
            'language': 'en',
            'format': 'json'
        }
        
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
    
    def _parse_dates(self, dates: List[str]) -> tuple:
        """
        날짜 파싱 및 검증
        
        Args:
            dates: 날짜 리스트
            
        Returns:
            (시작일, 종료일) 튜플
        """
        
        if not dates or len(dates) < 2:
            # 기본값: 오늘부터 5일
            start = datetime.now()
            end = start + timedelta(days=5)
        else:
            try:
                start = datetime.strptime(dates[0], "%Y-%m-%d")
                end = datetime.strptime(dates[1], "%Y-%m-%d")
            except ValueError:
                start = datetime.now()
                end = start + timedelta(days=5)
        
        # Open-Meteo는 최대 16일까지 지원
        max_date = datetime.now() + timedelta(days=16)
        if end > max_date:
            end = max_date
        
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    
    def _parse_weather_data(self, data: Dict) -> List[WeatherForecast]:
        """
        API 응답 파싱
        
        Args:
            data: Open-Meteo API 응답
            
        Returns:
            WeatherForecast 리스트
        """
        
        forecasts = []
        
        daily_data = data.get('daily', {})
        times = daily_data.get('time', [])
        max_temps = daily_data.get('temperature_2m_max', [])
        min_temps = daily_data.get('temperature_2m_min', [])
        precipitations = daily_data.get('precipitation_sum', [])
        weather_codes = daily_data.get('weathercode', [])
        
        for i in range(len(times)):
            forecast = WeatherForecast(
                date=times[i],
                temperature_min=min_temps[i] if i < len(min_temps) else 0,
                temperature_max=max_temps[i] if i < len(max_temps) else 0,
                precipitation=precipitations[i] if i < len(precipitations) else 0,
                weather_code=weather_codes[i] if i < len(weather_codes) else 0,
                description=self._get_weather_description(weather_codes[i] if i < len(weather_codes) else 0),
                recommendations=self._get_activity_recommendations(
                    weather_codes[i] if i < len(weather_codes) else 0,
                    max_temps[i] if i < len(max_temps) else 20,
                    precipitations[i] if i < len(precipitations) else 0
                )
            )
            forecasts.append(forecast)
        
        return forecasts
    
    def _get_weather_description(self, code: int) -> str:
        """
        날씨 코드를 설명으로 변환
        
        Args:
            code: WMO 날씨 코드
            
        Returns:
            날씨 설명
        """
        
        # WMO Weather interpretation codes
        weather_codes = {
            0: "맑음",
            1: "대체로 맑음",
            2: "부분적으로 흐림",
            3: "흐림",
            45: "안개",
            48: "서리 안개",
            51: "가벼운 이슬비",
            53: "중간 이슬비",
            55: "강한 이슬비",
            61: "약한 비",
            63: "중간 비",
            65: "강한 비",
            71: "약한 눈",
            73: "중간 눈",
            75: "강한 눈",
            77: "진눈깨비",
            80: "약한 소나기",
            81: "중간 소나기",
            82: "강한 소나기",
            85: "약한 눈 소나기",
            86: "강한 눈 소나기",
            95: "뇌우",
            96: "우박을 동반한 뇌우",
            99: "심한 우박을 동반한 뇌우"
        }
        
        return weather_codes.get(code, "알 수 없음")
    
    def _get_activity_recommendations(self, weather_code: int, 
                                     temperature: float, 
                                     precipitation: float) -> List[str]:
        """
        날씨 기반 활동 추천
        
        Args:
            weather_code: 날씨 코드
            temperature: 온도
            precipitation: 강수량
            
        Returns:
            추천 활동 리스트
        """
        
        recommendations = []
        
        # 맑은 날씨 (0-3)
        if weather_code <= 3:
            recommendations.extend([
                "야외 관광 추천",
                "피크닉 적합",
                "사진 촬영 좋은 날"
            ])
            if temperature > 25:
                recommendations.append("수영장/해변 활동 추천")
            elif temperature > 15:
                recommendations.append("하이킹/트레킹 추천")
        
        # 비 오는 날씨 (51-82)
        elif 51 <= weather_code <= 82:
            recommendations.extend([
                "실내 활동 추천 (박물관, 미술관)",
                "쇼핑몰 방문",
                "카페/레스토랑 투어"
            ])
            if precipitation < 5:
                recommendations.append("우산 준비하면 외출 가능")
        
        # 눈 오는 날씨 (71-77, 85-86)
        elif weather_code in [71, 73, 75, 77, 85, 86]:
            recommendations.extend([
                "겨울 스포츠 가능",
                "눈 구경 및 사진 촬영",
                "따뜻한 실내 활동"
            ])
        
        # 흐린 날씨 (45-48)
        elif 45 <= weather_code <= 48:
            recommendations.extend([
                "도시 투어 적합",
                "박물관/갤러리 방문",
                "로컬 마켓 탐방"
            ])
        
        # 온도 기반 추가 추천
        if temperature < 10:
            recommendations.append("따뜻한 옷 필수")
        elif temperature > 30:
            recommendations.append("자외선 차단제 필수")
            recommendations.append("수분 보충 중요")
        
        return recommendations[:3]  # 최대 3개 추천
    
    async def get_climate_info(self, location: str, month: int) -> Dict[str, Any]:
        """
        특정 월의 기후 정보 조회 (과거 데이터 기반)
        
        Args:
            location: 위치
            month: 월 (1-12)
            
        Returns:
            기후 정보
        """
        
        # 실제로는 과거 데이터를 분석해야 하지만, 
        # 여기서는 간단한 추정값 반환
        climate_data = {
            1: {"avg_temp": 5, "rainfall": 50, "description": "추운 겨울"},
            2: {"avg_temp": 7, "rainfall": 45, "description": "늦겨울"},
            3: {"avg_temp": 12, "rainfall": 60, "description": "초봄"},
            4: {"avg_temp": 18, "rainfall": 70, "description": "봄"},
            5: {"avg_temp": 23, "rainfall": 80, "description": "늦봄"},
            6: {"avg_temp": 27, "rainfall": 100, "description": "초여름"},
            7: {"avg_temp": 30, "rainfall": 120, "description": "한여름"},
            8: {"avg_temp": 29, "rainfall": 110, "description": "늦여름"},
            9: {"avg_temp": 25, "rainfall": 90, "description": "초가을"},
            10: {"avg_temp": 19, "rainfall": 70, "description": "가을"},
            11: {"avg_temp": 13, "rainfall": 60, "description": "늦가을"},
            12: {"avg_temp": 7, "rainfall": 55, "description": "초겨울"}
        }
        
        return climate_data.get(month, climate_data[1])
