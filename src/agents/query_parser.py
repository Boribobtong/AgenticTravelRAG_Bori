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
        
        # [수정] 프롬프트에 Context 섹션 추가
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 여행 계획 전문가입니다. 사용자의 자연어 질문에서 여행 관련 정보를 JSON 형식으로 정확하게 추출하세요.

[현재 계획된 여행 정보]
목적지: {current_destination}
날짜: {current_dates}
인원: {current_traveler_count}

[지시사항]
1. 사용자의 질문이 '새로운 여행' 요청이면 위 [현재 계획된 여행 정보]를 무시하고 새로 추출하세요.
2. 사용자의 질문이 '기존 계획 수정'(예: "이틀 더", "인원 추가")이면, [현재 계획된 여행 정보]를 기준으로 새로운 값을 계산하여 추출하세요.
   - 예: 현재 날짜가 2025-12-01 ~ 2025-12-03이고 사용자가 "이틀 더 묵을래"라고 하면, check_out_date는 2025-12-05가 되어야 합니다.

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
    
    # [수정] current_state 인자 추가
    async def parse(self, user_query: str, current_state: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            # 현재 상태에서 정보 추출 (없으면 기본값)
            current_dest = "없음"
            current_dates = "없음"
            current_count = "1"
            
            if current_state:
                current_dest = current_state.get('destination') or "없음"
                dates = current_state.get('travel_dates')
                if dates:
                    current_dates = f"{dates[0]} ~ {dates[1]}"
                current_count = str(current_state.get('traveler_count') or 1)

            messages = self.prompt.format_messages(
                query=user_query,
                current_date=datetime.now().strftime("%Y-%m-%d"),
                current_destination=current_dest,
                current_dates=current_dates,
                current_traveler_count=current_count,
                format_instructions=self.output_parser.get_format_instructions()
            )
            
            response = await self.llm.ainvoke(messages)
            parsed_result = self.output_parser.parse(response.content)
            return self._post_process(parsed_result, user_query)
            
        except Exception as e:
            logger.error(f"쿼리 파싱 실패: {str(e)}")
            return self._fallback_parse(user_query)
    
    def _post_process(self, parsed: ParsedTravelQuery, original_query: str) -> Dict[str, Any]:
        # 기존 로직 동일
        result = {
            'destination': parsed.destination,
            'dates': None,
            'traveler_count': parsed.traveler_count, # [수정] None일 경우 workflow에서 처리하도록 변경
            'preferences': {}
        }
        if parsed.check_in_date:
            try:
                check_in = datetime.strptime(parsed.check_in_date, "%Y-%m-%d")
                # 체크아웃 날짜가 없으면 기본 3박으로 설정하던 로직 유지하되, 
                # 멀티턴에서는 LLM이 체크아웃 날짜를 계산해서 줄 것이므로 그대로 사용
                if parsed.check_out_date:
                    check_out = datetime.strptime(parsed.check_out_date, "%Y-%m-%d")
                else:
                    check_out = check_in + timedelta(days=3)
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
        return {'destination': None, 'dates': None, 'traveler_count': None, 'preferences': {}}