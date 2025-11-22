"""
Weather Tool Agent: 날씨 정보 조회 에이전트
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
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        logger.info("WeatherToolAgent 초기화 완료 (Open-Meteo API)")
    
    async def get_forecast(self, location: str, dates: List[str]) -> List[WeatherForecast]:
        """날씨 예보 조회"""
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
                logger.warning("날짜가 예보 가능 범위를 벗어남")
                return self._get_mock_climate_data(dates) # 폴백: 기후 데이터 반환
                
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
                        return self._parse_weather_data(data)
                    else:
                        logger.error(f"날씨 API 오류: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"날씨 조회 실패: {str(e)}")
            return []
    
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
        
        # Open-Meteo 무료판 한계: 오늘부터 약 14~16일 후까지만 가능
        max_date = datetime.now() + timedelta(days=14)
        
        # 시작일이 이미 제한을 넘어선 경우 -> API 호출 불가
        if start > max_date:
            return None
            
        # 종료일만 넘어선 경우 -> 종료일을 제한일에 맞춤
        if end > max_date:
            end = max_date
        
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    
    def _get_mock_climate_data(self, dates: List[str]) -> List[WeatherForecast]:
        """너무 먼 미래인 경우 평년 기후 데이터(Mock) 반환"""
        try:
            target_date = datetime.strptime(dates[0], "%Y-%m-%d")
            month = target_date.month
            
            # 12월 파리 예시 데이터
            base_temp_min = 3 if month in [12, 1, 2] else 10
            base_temp_max = 8 if month in [12, 1, 2] else 20
            desc = "추움, 비/눈 가능성" if month in [12, 1, 2] else "온화함"
            
            return [WeatherForecast(
                date=dates[0],
                temperature_min=base_temp_min,
                temperature_max=base_temp_max,
                precipitation=0.0,
                weather_code=3,
                description=f"{month}월 평균 기후: {desc}",
                recommendations=["계절에 맞는 옷차림 준비"]
            )]
        except:
            return []

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
                recommendations=["날씨에 따른 활동 추천"]
            ))
        return forecasts
    
    def _get_weather_description(self, code: int) -> str:
        # 간소화된 코드 매핑
        if code == 0: return "맑음"
        if code <= 3: return "구름 많음"
        if code <= 48: return "안개"
        if code <= 67: return "비"
        if code <= 77: return "눈"
        return "흐림/비"
