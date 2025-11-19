"""
Query Parser Agent: 사용자 쿼리 파싱 에이전트

사용자의 자연어 입력에서 여행 관련 정보를 추출합니다.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ParsedTravelQuery(BaseModel):
    """파싱된 여행 쿼리 모델"""
    destination: Optional[str] = Field(description="여행 목적지")
    check_in_date: Optional[str] = Field(description="체크인 날짜 (YYYY-MM-DD)")
    check_out_date: Optional[str] = Field(description="체크아웃 날짜 (YYYY-MM-DD)")
    traveler_count: Optional[int] = Field(description="여행자 수")
    budget_min: Optional[float] = Field(description="최소 예산")
    budget_max: Optional[float] = Field(description="최대 예산")
    accommodation_type: Optional[str] = Field(description="숙박 유형 (hotel/hostel/resort/etc)")
    atmosphere_keywords: List[str] = Field(default_factory=list, description="분위기 키워드 (quiet/romantic/etc)")
    amenity_requirements: List[str] = Field(default_factory=list, description="필수 편의시설")
    activity_interests: List[str] = Field(default_factory=list, description="관심 활동")
    special_requirements: Optional[str] = Field(description="특별 요구사항")


class QueryParserAgent:
    """
    사용자 쿼리를 파싱하여 구조화된 여행 정보를 추출하는 에이전트
    """
    
    def __init__(self, llm_model: str = "gpt-3.5-turbo"):
        """
        초기화
        
        Args:
            llm_model: 사용할 LLM 모델
        """
        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=0.1,  # 파싱은 정확해야 하므로 낮은 temperature
            max_tokens=500
        )
        
        self.output_parser = PydanticOutputParser(pydantic_object=ParsedTravelQuery)
        
        # 프롬프트 템플릿
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 여행 계획 전문가입니다. 
사용자의 자연어 질문에서 여행 관련 정보를 정확하게 추출해야 합니다.

다음 정보를 추출하세요:
1. 목적지 (도시, 국가)
2. 여행 날짜 (체크인/체크아웃)
3. 여행 인원
4. 예산 범위
5. 숙박 유형 선호
6. 분위기/스타일 키워드 (예: 조용한, 낭만적인, 모던한)
7. 필수 편의시설 (예: 무료 WiFi, 조식 포함, 주차)
8. 관심 활동 (예: 관광, 쇼핑, 맛집)

날짜가 상대적으로 표현된 경우(예: "다음 주", "이번 달 말") 현재 날짜 기준으로 계산하세요.
오늘 날짜: {current_date}

{format_instructions}
"""),
            ("human", "{query}")
        ])
        
        logger.info("QueryParserAgent 초기화 완료")
    
    async def parse(self, user_query: str) -> Dict[str, Any]:
        """
        사용자 쿼리 파싱
        
        Args:
            user_query: 사용자 입력
            
        Returns:
            파싱된 정보 딕셔너리
        """
        
        try:
            # 프롬프트 구성
            messages = self.prompt.format_messages(
                query=user_query,
                current_date=datetime.now().strftime("%Y-%m-%d"),
                format_instructions=self.output_parser.get_format_instructions()
            )
            
            # LLM 호출
            response = await self.llm.ainvoke(messages)
            
            # 응답 파싱
            parsed_result = self.output_parser.parse(response.content)
            
            # 후처리
            processed_result = self._post_process(parsed_result, user_query)
            
            logger.info(f"쿼리 파싱 성공: {processed_result}")
            return processed_result
            
        except Exception as e:
            logger.error(f"쿼리 파싱 실패: {str(e)}")
            # 폴백: 규칙 기반 파싱 시도
            return self._fallback_parse(user_query)
    
    def _post_process(self, parsed: ParsedTravelQuery, original_query: str) -> Dict[str, Any]:
        """
        파싱 결과 후처리
        
        Args:
            parsed: 파싱된 결과
            original_query: 원본 쿼리
            
        Returns:
            후처리된 결과
        """
        
        result = {
            'destination': parsed.destination,
            'dates': None,
            'traveler_count': parsed.traveler_count or 1,
            'preferences': {}
        }
        
        # 날짜 처리
        if parsed.check_in_date and parsed.check_out_date:
            result['dates'] = [parsed.check_in_date, parsed.check_out_date]
        elif parsed.check_in_date:
            # 체크아웃 날짜가 없으면 3일 후로 설정
            check_in = datetime.strptime(parsed.check_in_date, "%Y-%m-%d")
            check_out = check_in + timedelta(days=3)
            result['dates'] = [parsed.check_in_date, check_out.strftime("%Y-%m-%d")]
        
        # 예산 처리
        if parsed.budget_min or parsed.budget_max:
            result['preferences']['budget_range'] = (
                parsed.budget_min or 0,
                parsed.budget_max or float('inf')
            )
        
        # 선호도 처리
        if parsed.accommodation_type:
            result['preferences']['accommodation_type'] = parsed.accommodation_type
        
        if parsed.atmosphere_keywords:
            result['preferences']['atmosphere'] = parsed.atmosphere_keywords
        
        if parsed.amenity_requirements:
            result['preferences']['amenities'] = parsed.amenity_requirements
        
        if parsed.activity_interests:
            result['preferences']['activities'] = parsed.activity_interests
        
        if parsed.special_requirements:
            result['preferences']['special_requirements'] = parsed.special_requirements
        
        return result
    
    def _fallback_parse(self, user_query: str) -> Dict[str, Any]:
        """
        규칙 기반 폴백 파싱
        
        Args:
            user_query: 사용자 쿼리
            
        Returns:
            파싱된 정보
        """
        
        logger.warning("LLM 파싱 실패, 규칙 기반 파싱 시도")
        
        result = {
            'destination': None,
            'dates': None,
            'traveler_count': 1,
            'preferences': {}
        }
        
        query_lower = user_query.lower()
        
        # 목적지 추출 (도시 이름 패턴)
        city_patterns = [
            r'(?:in|to|at|visit)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:hotel|trip|travel)'
        ]
        
        for pattern in city_patterns:
            match = re.search(pattern, user_query)
            if match:
                result['destination'] = match.group(1)
                break
        
        # 날짜 추출
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(next week|this weekend|next month)'
        ]
        
        dates_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, query_lower)
            dates_found.extend(matches)
        
        if dates_found:
            # 상대 날짜 변환
            processed_dates = []
            for date_str in dates_found:
                if date_str == 'next week':
                    base_date = datetime.now() + timedelta(weeks=1)
                    processed_dates.append(base_date.strftime("%Y-%m-%d"))
                elif date_str == 'this weekend':
                    # 다음 토요일
                    days_ahead = 5 - datetime.now().weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    base_date = datetime.now() + timedelta(days=days_ahead)
                    processed_dates.append(base_date.strftime("%Y-%m-%d"))
                elif date_str == 'next month':
                    base_date = datetime.now() + timedelta(days=30)
                    processed_dates.append(base_date.strftime("%Y-%m-%d"))
                else:
                    processed_dates.append(date_str)
            
            if len(processed_dates) >= 2:
                result['dates'] = processed_dates[:2]
            elif len(processed_dates) == 1:
                # 체크아웃 날짜 자동 생성
                check_in = datetime.strptime(processed_dates[0], "%Y-%m-%d")
                check_out = check_in + timedelta(days=3)
                result['dates'] = [processed_dates[0], check_out.strftime("%Y-%m-%d")]
        
        # 인원수 추출
        people_match = re.search(r'(\d+)\s*(?:people|persons?|travelers?|guests?)', query_lower)
        if people_match:
            result['traveler_count'] = int(people_match.group(1))
        
        # 예산 추출
        budget_match = re.search(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', user_query)
        if budget_match:
            budget_str = budget_match.group(1).replace(',', '')
            budget = float(budget_str)
            result['preferences']['budget_range'] = (budget * 0.8, budget * 1.2)
        
        # 키워드 추출
        atmosphere_keywords = []
        keyword_map = {
            'quiet': ['quiet', 'peaceful', 'calm', 'tranquil'],
            'romantic': ['romantic', 'intimate', 'couples', 'honeymoon'],
            'luxury': ['luxury', 'luxurious', 'premium', 'upscale'],
            'budget': ['budget', 'cheap', 'affordable', 'economical'],
            'family': ['family', 'kids', 'children', 'family-friendly']
        }
        
        for key, keywords in keyword_map.items():
            if any(word in query_lower for word in keywords):
                atmosphere_keywords.append(key)
        
        if atmosphere_keywords:
            result['preferences']['atmosphere'] = atmosphere_keywords
        
        # 편의시설 추출
        amenities = []
        amenity_keywords = {
            'wifi': ['wifi', 'internet', 'wi-fi'],
            'breakfast': ['breakfast', 'morning meal'],
            'parking': ['parking', 'car park'],
            'pool': ['pool', 'swimming'],
            'gym': ['gym', 'fitness'],
            'spa': ['spa', 'massage']
        }
        
        for amenity, keywords in amenity_keywords.items():
            if any(word in query_lower for word in keywords):
                amenities.append(amenity)
        
        if amenities:
            result['preferences']['amenities'] = amenities
        
        return result
    
    def validate_parsed_data(self, parsed_data: Dict[str, Any]) -> bool:
        """
        파싱된 데이터 검증
        
        Args:
            parsed_data: 파싱된 데이터
            
        Returns:
            유효성 여부
        """
        
        # 최소 요구사항: 목적지
        if not parsed_data.get('destination'):
            logger.warning("목적지 정보 누락")
            return False
        
        # 날짜 검증
        if parsed_data.get('dates'):
            try:
                check_in = datetime.strptime(parsed_data['dates'][0], "%Y-%m-%d")
                check_out = datetime.strptime(parsed_data['dates'][1], "%Y-%m-%d")
                
                # 체크인이 체크아웃보다 늦으면 안됨
                if check_in >= check_out:
                    logger.warning("체크인 날짜가 체크아웃 날짜보다 늦음")
                    return False
                
                # 과거 날짜 체크
                if check_in < datetime.now():
                    logger.warning("체크인 날짜가 과거")
                    return False
                    
            except (ValueError, IndexError):
                logger.warning("날짜 형식 오류")
                return False
        
        return True
