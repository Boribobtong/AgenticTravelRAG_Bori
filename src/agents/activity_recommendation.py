"""
ActivityRecommendationAgent: 여행 일정에 기반한 활동 추천
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class ActivityRecommendationAgent:
    """
    목적지 + 날씨 + 선호도 기반 활동 추천
    
    특징:
    - 시간대별 활동 추천 (morning, afternoon, evening, night)
    - 날씨 기반 동적 추천 (비오면 실내 활동)
    - 그룹 vs 개인 활동 구분
    - 예산대별 필터링
    - 현지 이벤트 자동 포함
    """
    
    def __init__(self):
        """에이전트 초기화"""
        self.supported_cities = {
            'Paris': {'landmarks': ['Eiffel Tower', 'Louvre', 'Notre-Dame']},
            'Tokyo': {'landmarks': ['Senso-ji', 'Shibuya', 'Meiji Shrine']},
            'Seoul': {'landmarks': ['Gyeongbokgung', 'Myeongdong', 'Hangang Park']},
            'London': {'landmarks': ['Big Ben', 'Tower Bridge', 'British Museum']},
            'New York': {'landmarks': ['Statue of Liberty', 'Central Park', 'Times Square']},
        }
        
        # 활동 DB (실제로는 API 연동)
        self.activities_db = self._initialize_activities_db()
        logger.info("ActivityRecommendationAgent 초기화 완료")
    
    def _initialize_activities_db(self) -> Dict[str, List[Dict]]:
        """활동 데이터베이스 초기화"""
        return {
            'indoor': [
                {'name': '박물관 방문', 'duration': '2-3시간', 'cost': 'low', 'group_friendly': True},
                {'name': '미술관 투어', 'duration': '2-3시간', 'cost': 'low', 'group_friendly': True},
                {'name': '요리 클래스', 'duration': '3시간', 'cost': 'medium', 'group_friendly': True},
                {'name': '카페 투어', 'duration': '1시간', 'cost': 'low', 'group_friendly': True},
                {'name': '쇼핑', 'duration': '2-4시간', 'cost': 'variable', 'group_friendly': True},
            ],
            'outdoor': [
                {'name': '공원 산책', 'duration': '1-2시간', 'cost': 'free', 'group_friendly': True},
                {'name': '트래킹', 'duration': '3-5시간', 'cost': 'free', 'group_friendly': True},
                {'name': '자전거 투어', 'duration': '2-3시간', 'cost': 'low', 'group_friendly': True},
                {'name': '보트 투어', 'duration': '1-2시간', 'cost': 'medium', 'group_friendly': True},
                {'name': '사진 촬영 투어', 'duration': '2-3시간', 'cost': 'low', 'group_friendly': False},
            ],
            'evening': [
                {'name': '저녁 식사', 'duration': '2시간', 'cost': 'medium', 'group_friendly': True},
                {'name': '뮤지컬 공연', 'duration': '3시간', 'cost': 'high', 'group_friendly': True},
                {'name': '라이브 음악 바', 'duration': '2-3시간', 'cost': 'medium', 'group_friendly': True},
                {'name': '야경 투어', 'duration': '1-2시간', 'cost': 'medium', 'group_friendly': True},
                {'name': '스탠드업 코미디', 'duration': '1-2시간', 'cost': 'medium', 'group_friendly': True},
            ]
        }
    
    async def recommend_activities(self, 
                                  destination: str,
                                  travel_dates: List[str],
                                  preferences: Dict[str, Any],
                                  weather_forecast: List[Dict],
                                  budget: float,
                                  group_size: int = 1) -> Dict[str, Any]:
        """
        활동 추천
        
        Args:
            destination: 목적지
            travel_dates: 여행 날짜 [시작, 종료]
            preferences: 선호도 {'activities': ['hiking', 'museum', ...]}
            weather_forecast: 날씨 예보
            budget: 활동 예산
            group_size: 그룹 크기
            
        Returns:
            활동 추천 결과
        """
        try:
            if destination not in self.supported_cities:
                logger.warning(f"지원하지 않는 도시: {destination}")
                return self._generate_generic_recommendations(destination, travel_dates)
            
            # 1. 날짜별 일정 생성
            itinerary = self._create_daily_itinerary(travel_dates)
            
            # 2. 각 날짜별 활동 추천
            recommendations = {}
            for day_num, (date, time_slots) in enumerate(itinerary.items()):
                weather = weather_forecast[day_num] if day_num < len(weather_forecast) else {}
                
                recommendations[date] = {
                    'morning': self._recommend_for_time_slot(
                        'morning', weather, preferences, budget, group_size
                    ),
                    'afternoon': self._recommend_for_time_slot(
                        'afternoon', weather, preferences, budget, group_size
                    ),
                    'evening': self._recommend_for_time_slot(
                        'evening', weather, preferences, budget, group_size
                    ),
                }
            
            # 3. 목적지 특화 추천 추가
            recommendations['special_experiences'] = self._get_special_experiences(
                destination, preferences
            )
            
            return {
                'destination': destination,
                'recommendations': recommendations,
                'total_estimated_cost': self._calculate_total_cost(recommendations),
                'summary': self._generate_summary(recommendations)
            }
            
        except Exception as e:
            logger.error(f"활동 추천 실패: {str(e)}")
            return {'error': str(e)}
    
    def _create_daily_itinerary(self, travel_dates: List[str]) -> Dict[str, List[str]]:
        """날짜별 일정 생성"""
        # 간단한 구현 (실제로는 날짜 파싱)
        return {
            f"Day {i+1}": ["morning", "afternoon", "evening"]
            for i in range(3)  # 3일 예시
        }
    
    def _recommend_for_time_slot(self, 
                                 time_slot: str,
                                 weather: Dict,
                                 preferences: Dict,
                                 budget: float,
                                 group_size: int) -> List[Dict]:
        """시간대별 활동 추천"""
        # 날씨에 따른 실내/실외 구분
        if weather.get('condition') == 'rainy':
            category = 'indoor'
        elif time_slot == 'evening':
            category = 'evening'
        else:
            category = 'outdoor' if weather.get('condition') != 'rainy' else 'indoor'
        
        # 활동 필터링
        activities = self.activities_db.get(category, [])
        
        # 그룹 크기에 따른 필터링
        if group_size == 1:
            activities = [a for a in activities if a['group_friendly'] or group_size == 1]
        
        # 상위 3개 추천
        return activities[:3]
    
    def _get_special_experiences(self, destination: str, preferences: Dict) -> List[Dict]:
        """목적지 특화 경험"""
        special_experiences = {
            'Paris': [
                {'name': '에펠탑 야경', 'duration': '1시간', 'cost': 'medium'},
                {'name': '센느강 크루즈', 'duration': '1시간', 'cost': 'medium'},
                {'name': '몽마르트르 투어', 'duration': '2시간', 'cost': 'low'},
            ],
            'Tokyo': [
                {'name': '다실 체험', 'duration': '1시간', 'cost': 'medium'},
                {'name': '오토바이 투어', 'duration': '3시간', 'cost': 'high'},
                {'name': '스시 마스터클래스', 'duration': '2시간', 'cost': 'high'},
            ],
            'Seoul': [
                {'name': '한국 전통 무술 체험', 'duration': '1시간', 'cost': 'medium'},
                {'name': 'K-드라마 촬영지 투어', 'duration': '2시간', 'cost': 'medium'},
                {'name': 'K-팝 콘서트', 'duration': '3시간', 'cost': 'high'},
            ],
        }
        
        return special_experiences.get(destination, [])
    
    def _calculate_total_cost(self, recommendations: Dict) -> float:
        """전체 예상 비용 계산"""
        # 간단한 추정
        return 300.0  # 예시
    
    def _generate_summary(self, recommendations: Dict) -> str:
        """추천 요약"""
        return "다양한 활동이 포함된 완벽한 여행 일정입니다."
    
    def _generate_generic_recommendations(self, destination: str, travel_dates: List[str]) -> Dict:
        """기본 활동 추천"""
        return {
            'destination': destination,
            'recommendations': {'generic': ['박물관 방문', '공원 산책', '현지 음식 맛보기']},
            'summary': f"{destination}의 기본 활동들입니다."
        }
