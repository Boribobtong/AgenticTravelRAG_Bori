"""
Query Parser Agent: 사용자 쿼리 파싱 에이전트 (Powered by Gemini)
"""
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# [수정] Google Gemini 임포트
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ParsedTravelQuery(BaseModel):
    destination: Optional[str] = Field(description="여행 목적지")
    check_in_date: Optional[str] = Field(description="체크인 날짜 (YYYY-MM-DD)")
    check_out_date: Optional[str] = Field(description="체크아웃 날짜 (YYYY-MM-DD)")
    traveler_count: Optional[int] = Field(description="여행자 수")
    budget_min: Optional[float] = Field(description="최소 예산")
    budget_max: Optional[float] = Field(description="최대 예산")
    accommodation_type: Optional[str] = Field(description="숙박 유형")
    atmosphere_keywords: List[str] = Field(default_factory=list, description="분위기 키워드")
    amenity_requirements: List[str] = Field(default_factory=list, description="필수 편의시설")
    activity_interests: List[str] = Field(default_factory=list, description="관심 활동")
    special_requirements: Optional[str] = Field(description="특별 요구사항")

class QueryParserAgent:
    def __init__(self):
        # [수정] ChatGoogleGenerativeAI 사용 (Gemini 1.5 Flash 모델 추천 - 빠르고 저렴함)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.1,
        )
        
        self.output_parser = PydanticOutputParser(pydantic_object=ParsedTravelQuery)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 여행 계획 전문가입니다. 사용자의 자연어 질문에서 여행 관련 정보를 JSON 형식으로 정확하게 추출하세요.
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
            
            # Gemini 호출
            response = await self.llm.ainvoke(messages)
            
            # 파싱
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
        return result

    def _fallback_parse(self, user_query: str) -> Dict[str, Any]:
        logger.warning("LLM 파싱 실패, 규칙 기반 파싱 시도")
        return {'destination': None, 'dates': None, 'traveler_count': 1, 'preferences': {}}
