"""
Response Generator Agent: 최종 응답 생성 에이전트 (Powered by Gemini)
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

class ResponseGeneratorAgent:
    def __init__(self):
        # [수정] 모델 변경: gemini-2.5-pro (최신 고성능 모델 사용)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            temperature=0.7,
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 전문 여행 컨설턴트입니다. 수집된 정보를 바탕으로 여행 일정을 작성해주세요."),
            ("human", """
목적지: {destination}
여행 날짜: {dates}
여행 인원: {traveler_count}명
선호사항: {preferences}
호텔 검색 결과: {hotel_results}
날씨 예보:
{weather_forecast}
구글 검색 정보: {google_info}

위 정보를 바탕으로 맞춤형 여행 계획을 작성해주세요.
날씨 예보가 테이블 형식으로 제공된 경우, 응답에 그대로 포함시켜 주세요.""")
        ])
        logger.info("ResponseGeneratorAgent(Gemini) 초기화 완료")
    
    async def generate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            destination = state.get('destination', '목적지 미정')
            dates = state.get('travel_dates', ['날짜 미정'])
            
            # 날씨 정보 포맷팅
            weather_info = self._format_weather_forecast(state.get('weather_forecast', []))
            
            messages = self.prompt.format_messages(
                destination=destination,
                dates=' ~ '.join(dates) if isinstance(dates, list) else dates,
                traveler_count=state.get('traveler_count', 1),
                preferences=str(state.get('preferences', {})),
                hotel_results=self._format_hotel_results(state.get('hotel_options', [])),
                weather_forecast=weather_info,
                google_info=str(state.get('google_search_results', []))
            )
            
            response = await self.llm.ainvoke(messages)
            
            return {
                'destination': destination,
                'dates': dates,
                'summary': response.content,
                'hotels': [{'name': h.name, 'rating': h.rating, 'price': h.price_range, 'highlights': h.review_highlights} for h in state.get('hotel_options', [])[:3]],
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"응답 생성 실패: {str(e)}")
            return {'summary': f"오류 발생: {str(e)}", 'hotels': []}

    def _format_hotel_results(self, hotels: List) -> str:
        if not hotels: return "검색된 호텔 없음"
        return "\n".join([f"- {h.name} (평점: {h.rating}, 가격: {h.price_range})" for h in hotels[:3]])
    
    def _format_weather_forecast(self, forecasts: List) -> str:
        """
        날씨 예보를 Markdown 테이블 형식으로 포맷팅
        """
        if not forecasts:
            return "날씨 정보 없음 (날짜가 2주 이후이거나 조회 실패)"
        
        table = "| 날짜 | 날씨 | 최저기온 | 최고기온 | 강수량 |\n"
        table += "|------|------|----------|----------|--------|\n"
        
        for forecast in forecasts:
            table += f"| {forecast.date} | {forecast.description} | {forecast.temperature_min}°C | {forecast.temperature_max}°C | {forecast.precipitation}mm |\n"
        
        return table
