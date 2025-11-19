"""
Response Generator Agent: 최종 응답 생성 에이전트

수집된 모든 정보를 종합하여 사용자에게 제공할 
최종 여행 계획을 생성합니다.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


class ResponseGeneratorAgent:
    """
    최종 여행 계획 응답을 생성하는 에이전트
    """
    
    def __init__(self, llm_model: str = "gpt-3.5-turbo"):
        """
        초기화
        
        Args:
            llm_model: 사용할 LLM 모델
        """
        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=0.7,
            max_tokens=2000
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 전문 여행 컨설턴트입니다.
수집된 정보를 바탕으로 개인 맞춤형 여행 일정을 작성해주세요.

다음 정보가 제공됩니다:
1. 호텔 검색 결과 (리뷰 기반 추천)
2. 날씨 예보
3. 구글 검색 결과 (실시간 가격 등)

작성 지침:
- 친근하고 전문적인 톤 유지
- 구체적이고 실용적인 정보 제공
- 날씨를 고려한 일정 제안
- 호텔 선택의 장단점 명시
- 예산 고려사항 포함
- 팁과 주의사항 추가

응답 형식:
1. 여행 개요
2. 추천 호텔 (TOP 3)
3. 일별 추천 일정
4. 날씨 정보 및 준비물
5. 예산 가이드
6. 현지 팁
"""),
            ("human", """
목적지: {destination}
여행 날짜: {dates}
여행 인원: {traveler_count}명
선호사항: {preferences}

호텔 검색 결과:
{hotel_results}

날씨 예보:
{weather_forecast}

구글 검색 정보:
{google_info}

위 정보를 바탕으로 맞춤형 여행 계획을 작성해주세요.
""")
        ])
        
        logger.info("ResponseGeneratorAgent 초기화 완료")
    
    async def generate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        최종 여행 계획 생성
        
        Args:
            state: 현재 상태 (모든 수집된 정보 포함)
            
        Returns:
            최종 여행 계획
        """
        
        try:
            # 상태에서 정보 추출
            destination = state.get('destination', '목적지 미정')
            dates = state.get('travel_dates', ['날짜 미정'])
            traveler_count = state.get('traveler_count', 1)
            preferences = state.get('preferences', {})
            hotel_options = state.get('hotel_options', [])
            weather_forecast = state.get('weather_forecast', [])
            google_results = state.get('google_search_results', [])
            
            # 프롬프트 구성
            messages = self.prompt.format_messages(
                destination=destination,
                dates=' ~ '.join(dates) if isinstance(dates, list) else dates,
                traveler_count=traveler_count,
                preferences=self._format_preferences(preferences),
                hotel_results=self._format_hotel_results(hotel_options),
                weather_forecast=self._format_weather(weather_forecast),
                google_info=self._format_google_info(google_results)
            )
            
            # LLM 호출
            response = await self.llm.ainvoke(messages)
            
            # 구조화된 결과 생성
            itinerary = self._structure_itinerary(
                response.content,
                destination,
                dates,
                hotel_options,
                weather_forecast
            )
            
            logger.info("여행 계획 생성 완료")
            return itinerary
            
        except Exception as e:
            logger.error(f"응답 생성 실패: {str(e)}")
            return self._get_fallback_response(state)
    
    def _format_preferences(self, preferences: Dict) -> str:
        """선호도 포맷팅"""
        if not preferences:
            return "특별한 선호사항 없음"
        
        lines = []
        if preferences.get('budget_range'):
            min_b, max_b = preferences['budget_range']
            lines.append(f"예산: ${min_b} - ${max_b}")
        
        if preferences.get('atmosphere'):
            lines.append(f"분위기: {', '.join(preferences['atmosphere'])}")
        
        if preferences.get('amenities'):
            lines.append(f"편의시설: {', '.join(preferences['amenities'])}")
        
        if preferences.get('activities'):
            lines.append(f"관심 활동: {', '.join(preferences['activities'])}")
        
        return '\n'.join(lines) if lines else "일반적인 선호"
    
    def _format_hotel_results(self, hotels: List) -> str:
        """호텔 결과 포맷팅"""
        if not hotels:
            return "호텔 검색 결과 없음"
        
        lines = []
        for i, hotel in enumerate(hotels[:3], 1):
            lines.append(f"\n{i}. {hotel.name}")
            lines.append(f"   위치: {hotel.location}")
            lines.append(f"   평점: {hotel.rating}/5.0")
            lines.append(f"   가격대: {hotel.price_range}")
            lines.append(f"   특징: {', '.join(hotel.review_highlights[:2])}")
            lines.append(f"   매칭 점수: {hotel.combined_score:.2f}")
        
        return '\n'.join(lines)
    
    def _format_weather(self, forecasts: List) -> str:
        """날씨 정보 포맷팅"""
        if not forecasts:
            return "날씨 정보 없음"
        
        lines = []
        for forecast in forecasts[:5]:  # 5일치만
            lines.append(f"\n{forecast.date}:")
            lines.append(f"  {forecast.description}")
            lines.append(f"  온도: {forecast.temperature_min}°C ~ {forecast.temperature_max}°C")
            if forecast.precipitation > 0:
                lines.append(f"  강수량: {forecast.precipitation}mm")
            if forecast.recommendations:
                lines.append(f"  추천: {forecast.recommendations[0]}")
        
        return '\n'.join(lines)
    
    def _format_google_info(self, results: List) -> str:
        """구글 검색 정보 포맷팅"""
        if not results:
            return "추가 정보 없음"
        
        lines = []
        for result in results[:2]:  # 상위 2개만
            if hasattr(result, 'results') and result.results:
                for item in result.results[:2]:
                    lines.append(f"- {item.get('title', '')}")
                    lines.append(f"  {item.get('snippet', '')[:100]}...")
        
        return '\n'.join(lines) if lines else "검색 정보 없음"
    
    def _structure_itinerary(self, llm_response: str, 
                            destination: str,
                            dates: List[str],
                            hotels: List,
                            weather: List) -> Dict[str, Any]:
        """
        LLM 응답을 구조화된 일정으로 변환
        
        Args:
            llm_response: LLM 생성 텍스트
            destination: 목적지
            dates: 여행 날짜
            hotels: 호텔 옵션
            weather: 날씨 정보
            
        Returns:
            구조화된 일정
        """
        
        return {
            'destination': destination,
            'dates': dates,
            'summary': llm_response,
            'hotels': [
                {
                    'name': h.name,
                    'rating': h.rating,
                    'price': h.price_range,
                    'highlights': h.review_highlights
                } for h in hotels[:3]
            ] if hotels else [],
            'weather_summary': self._create_weather_summary(weather),
            'generated_at': datetime.now().isoformat(),
            'version': '1.0'
        }
    
    def _create_weather_summary(self, forecasts: List) -> str:
        """날씨 요약 생성"""
        if not forecasts:
            return "날씨 정보를 확인할 수 없습니다."
        
        # 평균 온도 계산
        temps = [f.temperature_max for f in forecasts if hasattr(f, 'temperature_max')]
        avg_temp = sum(temps) / len(temps) if temps else 20
        
        # 비 오는 날 계산
        rainy_days = sum(1 for f in forecasts 
                        if hasattr(f, 'precipitation') and f.precipitation > 0)
        
        summary = f"평균 기온 {avg_temp:.1f}°C"
        if rainy_days > 0:
            summary += f", {rainy_days}일 강수 예상"
        else:
            summary += ", 대체로 맑음"
        
        return summary
    
    def _get_fallback_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        폴백 응답 (오류 시)
        
        Args:
            state: 현재 상태
            
        Returns:
            기본 응답
        """
        
        destination = state.get('destination', '목적지')
        dates = state.get('travel_dates', ['날짜 미정'])
        
        fallback_text = f"""
        # {destination} 여행 계획
        
        여행 날짜: {' ~ '.join(dates) if isinstance(dates, list) else dates}
        
        죄송합니다. 일시적인 오류로 상세한 여행 계획을 생성할 수 없습니다.
        
        다음 정보를 확인해 보세요:
        1. 호텔: TripAdvisor나 Booking.com에서 {destination} 호텔을 검색해보세요
        2. 날씨: 여행 전 날씨 예보를 확인하세요
        3. 관광지: {destination}의 주요 관광지를 검색해보세요
        
        더 나은 서비스를 위해 잠시 후 다시 시도해 주세요.
        """
        
        return {
            'destination': destination,
            'dates': dates,
            'summary': fallback_text,
            'hotels': [],
            'weather_summary': '날씨 정보 없음',
            'generated_at': datetime.now().isoformat(),
            'version': '1.0',
            'status': 'fallback'
        }
