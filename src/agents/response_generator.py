"""
Response Generator Agent: 최종 응답 생성 에이전트 (Powered by Gemini)
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

import os
try:
    # Optional LLM binding (only loaded when ENABLE_LLM=1)
    from langchain_google_genai import ChatGoogleGenerativeAI
except Exception:
    ChatGoogleGenerativeAI = None


logger = logging.getLogger(__name__)

class ResponseGeneratorAgent:
    def __init__(self):
        # LLM initialization is optional and gated by environment to keep tests
        # and CI lightweight. Set ENABLE_LLM=1 to attempt to use Google Gemini.
        self.llm = None
        self.enable_llm = os.getenv('ENABLE_LLM', '').lower() in ('1', 'true', 'yes') and ChatGoogleGenerativeAI is not None
        if self.enable_llm:
            try:
                self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.7)
            except Exception:
                self.llm = None

        # Use a simple string template for prompt formatting to avoid hard
        # dependency on langchain prompt classes in tests.
        self.prompt_template = (
            "당신은 전문 여행 컨설턴트입니다. 수집된 정보를 바탕으로 맞춤형 여행 계획을 작성해주세요.\n\n"
            "**중요: 각 섹션 헤더에 관련 이모지를 추가하세요:**\n"
            "- 숙소/호텔: 🏨\n"
            "- 날씨/기후: 🌤️ 또는 ☀️, 🌧️, ❄️ (날씨에 따라)\n"
            "- 일정/스케줄: 📅\n"
            "- 아침 활동: 🌅\n"
            "- 점심 시간: 🍽️\n"
            "- 저녁 활동: 🌆\n"
            "- 교통/이동: 🚇, 🚌, 🚶\n"
            "- 음식/레스토랑: 🍴, 🥐, 🍷\n"
            "- 관광지/명소: 🗼, 🏛️, ⛪\n"
            "- 문화/예술: 🎨, 🎭\n"
            "- 쇼핑: 🛍️\n"
            "- 자연/공원: 🌳, 🏞️\n"
            "- 팁/조언: 💡\n\n"
            "목적지: {destination}\n"
            "여행 날짜: {dates}\n"
            "여행 인원: {traveler_count}명\n"
            "선호사항: {preferences}\n"
            "호텔 검색 결과: {hotel_results}\n"
            "날씨 예보:\n{weather_forecast}\n"
            "구글 검색 정보: {google_info}\n\n"
            "위 정보를 바탕으로 이모지가 포함된 맞춤형 여행 계획을 작성해주세요."
        )
        logger.info("ResponseGeneratorAgent(Gemini) 초기화 완료")
    
    async def generate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            destination = state.get('destination', '목적지 미정')
            dates = state.get('travel_dates', ['날짜 미정'])
            
            # 날씨 정보 포맷팅
            weather_info = self._format_weather_forecast(
                state.get('weather_forecast', []),
                state.get('context_memory', {}).get('weather_limitation_message')
            )
            
            prompt_text = self.prompt_template.format(
                destination=destination,
                dates=' ~ '.join(dates) if isinstance(dates, list) else dates,
                traveler_count=state.get('traveler_count', 1),
                preferences=str(state.get('preferences', {})),
                hotel_results=self._format_hotel_results(state.get('hotel_options', [])),
                weather_forecast=weather_info,
                google_info=str(state.get('google_search_results', []))
            )

            if self.llm:
                try:
                    response = await self.llm.ainvoke(prompt_text)
                    content = getattr(response, 'content', str(response))
                except Exception:
                    content = "요약을 생성할 수 없습니다."
            else:
                # Lightweight fallback summary (non-LLM)
                content = f"{destination}에 대한 간단한 일정입니다. 호텔 {len(state.get('hotel_options', []))}곳 추천." 

            return {
                'destination': destination,
                'dates': dates,
                'summary': content,
                'hotels': [{'name': h.name, 'rating': h.rating, 'price': h.price_range, 'highlights': h.review_highlights} for h in state.get('hotel_options', [])[:3]],
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"응답 생성 실패: {str(e)}")
            return {'summary': f"오류 발생: {str(e)}", 'hotels': []}

    def _format_hotel_results(self, hotels: List) -> str:
        if not hotels: return "검색된 호텔 없음"
        return "\n".join([f"- {h.name} (평점: {h.rating}, 가격: {h.price_range})" for h in hotels[:3]])
    
    def _format_weather_forecast(self, forecasts: List, limitation_message: str = None) -> str:
        """
        날씨 예보를 Markdown 테이블 형식으로 포맷팅
        """
        if not forecasts:
            if limitation_message:
                return f"⚠️ {limitation_message}"
            return "날씨 정보 없음 (날짜가 2주 이후이거나 조회 실패)"
        
        table = "| 날짜 | 날씨 | 최저기온 | 최고기온 | 강수량 |\n"
        table += "|------|------|----------|----------|--------|\n"
        
        for forecast in forecasts:
            table += f"| {forecast.date} | {forecast.description} | {forecast.temperature_min}°C | {forecast.temperature_max}°C | {forecast.precipitation}mm |\n"
        
        return table

    async def stream_response(self, state: Dict[str, Any]):
        """Async generator that yields parts of the response incrementally.

        This is a lightweight PoC for streaming responses without invoking the
        LLM for every partial update. It yields three steps:
        1) hotels list
        2) weather table or message
        3) final summary (placeholder if LLM not available)
        """
        # 1) hotels
        hotels = [{'name': h.name, 'rating': h.rating, 'price': h.price_range, 'highlights': h.review_highlights} for h in state.get('hotel_options', [])[:3]]
        yield {'step': 'hotels', 'hotels': hotels}

        # 2) weather
        weather_info = self._format_weather_forecast(
            state.get('weather_forecast', []),
            state.get('context_memory', {}).get('weather_limitation_message')
        )
        yield {'step': 'weather', 'weather': weather_info}

        # 3) final summary — try LLM generate, but fall back to a simple placeholder
        try:
            final = await self.generate(state)
            yield {'step': 'final', 'itinerary': final}
        except Exception:
            # Non-fatal fallback
            yield {'step': 'final', 'itinerary': {'summary': '요약을 생성할 수 없습니다. 나중에 다시 시도해 주세요.'}}
