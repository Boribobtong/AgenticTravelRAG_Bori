"""
Safety Info Agent: 여행지 안전 정보 제공 에이전트
"""

import logging
try:
    import aiohttp
    _AIOHTTP_AVAILABLE = True
except Exception:
    aiohttp = None
    _AIOHTTP_AVAILABLE = False

from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SafetyInfo:
    """안전 정보 데이터 클래스"""
    country: str
    country_code: str
    capital: str
    languages: List[str]
    currency: str
    emergency_numbers: Dict[str, str]  # {"police": "17", "ambulance": "15"}
    timezone: str
    visa_info: str  # 간단한 비자 정보
    safety_tips: List[str]
    last_updated: str


class SafetyInfoAgent:
    """
    REST Countries API를 통한 여행지 안전 정보 제공 에이전트
    """
    
    def __init__(self):
        self.countries_api = "https://restcountries.com/v3.1"
        logger.info("SafetyInfoAgent 초기화 완료 (REST Countries API)")
    
    async def get_safety_info(self, location: str) -> Optional[SafetyInfo]:
        """
        여행지의 안전 정보 조회
        
        Args:
            location: 도시명 또는 국가명 (예: "Paris", "France")
            
        Returns:
            SafetyInfo 객체 또는 None
        """
        try:
            # 1. 국가 정보 조회
            country_data = await self._get_country_info(location)
            if not country_data:
                logger.warning(f"국가 정보를 찾을 수 없음: {location}")
                return None
            
            # 2. 데이터 파싱
            safety_info = self._parse_country_data(country_data)
            
            # 3. 안전 팁 생성
            safety_info.safety_tips = self._generate_safety_tips(country_data)
            
            logger.info(f"안전 정보 조회 완료: {safety_info.country}")
            return safety_info
            
        except Exception as e:
            logger.error(f"안전 정보 조회 실패: {str(e)}")
            return None
    
    async def _get_country_info(self, location: str) -> Optional[Dict]:
        """REST Countries API로 국가 정보 조회"""
        if not _AIOHTTP_AVAILABLE:
            logger.error("aiohttp가 설치되지 않았습니다")
            return None
        
        # 도시명인 경우 국가명으로 매핑 (간단한 매핑)
        city_to_country = {
            "paris": "france",
            "london": "united kingdom",
            "tokyo": "japan",
            "seoul": "south korea",
            "new york": "united states",
            "rome": "italy",
            "barcelona": "spain",
            "berlin": "germany",
            "amsterdam": "netherlands",
            "prague": "czech republic",
            "vienna": "austria",
            "budapest": "hungary",
            "bangkok": "thailand",
            "singapore": "singapore",
            "dubai": "united arab emirates",
            "sydney": "australia",
            "toronto": "canada",
            "mexico city": "mexico",
            "rio de janeiro": "brazil",
            "buenos aires": "argentina"
        }
        
        search_term = city_to_country.get(location.lower(), location)
        
        try:
            url = f"{self.countries_api}/name/{search_term}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        # 첫 번째 결과 반환
                        return data[0] if data else None
                    else:
                        logger.warning(f"국가 정보 API 오류: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"국가 정보 조회 실패: {str(e)}")
            return None
    
    def _parse_country_data(self, data: Dict) -> SafetyInfo:
        """API 응답 데이터 파싱"""
        from datetime import datetime
        
        # 국가명
        country = data.get('name', {}).get('common', 'Unknown')
        country_code = data.get('cca2', 'XX')
        
        # 수도
        capital = data.get('capital', ['Unknown'])[0] if data.get('capital') else 'Unknown'
        
        # 언어
        languages_dict = data.get('languages', {})
        languages = list(languages_dict.values()) if languages_dict else ['Unknown']
        
        # 통화
        currencies_dict = data.get('currencies', {})
        currency = list(currencies_dict.keys())[0] if currencies_dict else 'Unknown'
        if currencies_dict and currency != 'Unknown':
            currency_name = currencies_dict[currency].get('name', currency)
            currency = f"{currency} ({currency_name})"
        
        # 긴급 연락처 (일부 국가만 제공)
        emergency_numbers = {}
        
        # 국가별 긴급 연락처 (하드코딩 - REST Countries API에서 제공 안 함)
        emergency_db = {
            "FR": {"police": "17", "ambulance": "15", "fire": "18", "emergency": "112"},
            "GB": {"police": "999", "ambulance": "999", "fire": "999", "emergency": "112"},
            "US": {"police": "911", "ambulance": "911", "fire": "911"},
            "KR": {"police": "112", "ambulance": "119", "fire": "119"},
            "JP": {"police": "110", "ambulance": "119", "fire": "119"},
            "IT": {"police": "113", "ambulance": "118", "fire": "115", "emergency": "112"},
            "ES": {"police": "091", "ambulance": "061", "fire": "080", "emergency": "112"},
            "DE": {"police": "110", "ambulance": "112", "fire": "112", "emergency": "112"},
        }
        
        emergency_numbers = emergency_db.get(country_code, {"emergency": "112 (유럽 공통)"})
        
        # 시간대
        timezones = data.get('timezones', ['Unknown'])
        timezone = timezones[0] if timezones else 'Unknown'
        
        # 비자 정보 (간단한 안내)
        visa_info = "여행 전 외교부 또는 대사관에서 비자 요구사항을 확인하세요."
        
        return SafetyInfo(
            country=country,
            country_code=country_code,
            capital=capital,
            languages=languages,
            currency=currency,
            emergency_numbers=emergency_numbers,
            timezone=timezone,
            visa_info=visa_info,
            safety_tips=[],  # 나중에 채움
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def _generate_safety_tips(self, country_data: Dict) -> List[str]:
        """국가별 안전 팁 생성"""
        tips = [
            "여권과 중요 서류는 복사본을 별도로 보관하세요.",
            "여행자 보험 가입을 권장합니다.",
            "현지 긴급 연락처를 휴대폰에 저장하세요.",
        ]
        
        # 지역별 추가 팁
        region = country_data.get('region', '')
        
        if region == 'Europe':
            tips.append("유럽 내 이동 시 소매치기에 주의하세요.")
            tips.append("대중교통 이용 시 가방을 앞으로 메세요.")
        elif region == 'Asia':
            tips.append("음식물과 물은 위생 상태를 확인하세요.")
            tips.append("현지 문화와 관습을 존중하세요.")
        elif region == 'Americas':
            tips.append("밤늦은 시간 외출 시 택시를 이용하세요.")
        
        return tips
    
    def format_safety_info(self, safety_info: SafetyInfo) -> str:
        """안전 정보를 Markdown 형식으로 포맷팅"""
        if not safety_info:
            return "안전 정보를 조회할 수 없습니다."
        
        output = f"## 🛡️ {safety_info.country} 안전 정보\n\n"
        output += f"**수도**: {safety_info.capital}\n"
        output += f"**언어**: {', '.join(safety_info.languages)}\n"
        output += f"**통화**: {safety_info.currency}\n"
        output += f"**시간대**: {safety_info.timezone}\n\n"
        
        output += "### 🚨 긴급 연락처\n"
        for service, number in safety_info.emergency_numbers.items():
            service_emoji = {
                "police": "👮",
                "ambulance": "🚑",
                "fire": "🚒",
                "emergency": "🆘"
            }.get(service, "📞")
            output += f"- {service_emoji} **{service.title()}**: {number}\n"
        
        output += f"\n### 💡 안전 팁\n"
        for tip in safety_info.safety_tips:
            output += f"- {tip}\n"
        
        output += f"\n**비자**: {safety_info.visa_info}\n"
        output += f"\n*정보 업데이트: {safety_info.last_updated}*\n"
        
        return output
