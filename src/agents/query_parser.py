"""
Query Parser Agent: 사용자 쿼리 파싱 에이전트 (Powered by Gemini)
"""
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ParsedTravelQuery(BaseModel):
    destination: Optional[str] = Field(description="여행 목적지 (반드시 영어로 번역)")
    check_in_date: Optional[str] = Field(description="체크인 날짜 (YYYY-MM-DD)")
    check_out_date: Optional[str] = Field(description="체크아웃 날짜 (YYYY-MM-DD)")
    traveler_count: Optional[int] = Field(description="여행자 수")
    budget_min: Optional[float] = Field(description="최소 예산")
    budget_max: Optional[float] = Field(description="최대 예산")
    accommodation_type: Optional[str] = Field(description="숙박 유형 (영어로 번역)")
    atmosphere_keywords: List[str] = Field(default_factory=list, description="분위기 키워드 (영어로 번역)")
    amenity_requirements: List[str] = Field(default_factory=list, description="필수 편의시설 (영어로 번역)")
    activity_interests: List[str] = Field(default_factory=list, description="관심 활동 (영어로 번역)")
    special_requirements: Optional[str] = Field(description="특별 요구사항")

class QueryParserAgent:
    def __init__(self):
        # 모델: gemini-2.5-flash (속도 최적화)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.1,
        )
        
        self.output_parser = PydanticOutputParser(pydantic_object=ParsedTravelQuery)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 여행 계획 전문가입니다. 사용자의 자연어 질문에서 여행 관련 정보를 JSON 형식으로 정확하게 추출하세요.

[중요] 검색 정확도를 위해 다음 필드는 반드시 **영어(English)**로 번역해서 추출해야 합니다:
- destination (예: '파리' -> 'Paris', '방콕' -> 'Bangkok')
- atmosphere_keywords (예: '조용한' -> 'quiet', '낭만적인' -> 'romantic')
- amenity_requirements (예: '조식' -> 'breakfast')
- accommodation_type (예: '호텔' -> 'hotel')

날짜가 상대적으로 표현된 경우(예: "다음 주") 오늘({current_date}) 기준으로 계산하세요.
{format_instructions}"""),
            ("human", "{query}")
        ])
        logger.info("QueryParserAgent(Gemini) 초기화 완료")
    
    async def parse(self, user_query: str) -> Dict[str, Any]:
        try:
            messages = self.prompt.format_messages(
                query=user_query,
                current_date=datetime.now().strftime("%Y-%m-%d"),
                format_instructions=self.output_parser.get_format_instructions()
            )
            
            response = await self.llm.ainvoke(messages)
            parsed_result = self.output_parser.parse(response.content)
            return self._post_process(parsed_result, user_query)
            
        except Exception as e:
            logger.error(f"쿼리 파싱 실패: {str(e)}")
            return self._fallback_parse(user_query)
    
    def _post_process(self, parsed: ParsedTravelQuery, original_query: str) -> Dict[str, Any]:
        result = {
            'destination': parsed.destination,
            'dates': None,
            'traveler_count': parsed.traveler_count or 1,
            'preferences': {}
        }
        if parsed.check_in_date:
            try:
                check_in = datetime.strptime(parsed.check_in_date, "%Y-%m-%d")
                check_out = check_in + timedelta(days=3)
                if parsed.check_out_date:
                    check_out = datetime.strptime(parsed.check_out_date, "%Y-%m-%d")
                result['dates'] = [parsed.check_in_date, check_out.strftime("%Y-%m-%d")]
            except: pass
            
        if parsed.budget_min or parsed.budget_max:
            result['preferences']['budget_range'] = (parsed.budget_min or 0, parsed.budget_max or float('inf'))
        if parsed.atmosphere_keywords: result['preferences']['atmosphere'] = parsed.atmosphere_keywords
        if parsed.amenity_requirements: result['preferences']['amenities'] = parsed.amenity_requirements
        if parsed.accommodation_type: result['preferences']['accommodation_type'] = parsed.accommodation_type
        return result

    def _fallback_parse(self, user_query: str) -> Dict[str, Any]:
        logger.warning("LLM 파싱 실패, 규칙 기반 파싱 시도")
        return {'destination': None, 'dates': None, 'traveler_count': 1, 'preferences': {}}
