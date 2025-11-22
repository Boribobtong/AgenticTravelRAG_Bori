"""
Google Search Agent: 구글 검색 도구 에이전트

SerpApi를 사용하여 호텔 정보와 실시간 가격을 검색합니다.
"""

import os
import logging
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
from src.core.state import GoogleSearchResult

logger = logging.getLogger(__name__)


class GoogleSearchAgent:
    """
    SerpApi를 통한 구글 검색 에이전트
    무료 플랜: 월 100회 검색
    """
    
    def __init__(self):
        """초기화"""
        self.api_key = os.getenv('SERP_API_KEY', '')
        self.base_url = "https://serpapi.com/search.json"
        
        if not self.api_key:
            logger.warning("SERP_API_KEY 환경변수가 설정되지 않음 - 모의 데이터 사용")
        
        logger.info("GoogleSearchAgent 초기화 완료")
    
    async def search_hotel_info(self, hotel_name: str, location: str) -> GoogleSearchResult:
        """호텔 정보 검색"""
        query = f"{hotel_name} {location} hotel prices reviews"
        
        if not self.api_key:
            return self._get_mock_results(hotel_name, location)
        
        try:
            params = {
                'q': query,
                'api_key': self.api_key,
                'engine': 'google',
                'num': 5,
                'hl': 'en'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_search_results(query, data)
                    else:
                        logger.error(f"SerpApi 오류: {response.status}")
                        return self._get_mock_results(hotel_name, location)
                        
        except Exception as e:
            logger.error(f"구글 검색 실패: {str(e)}")
            return self._get_mock_results(hotel_name, location)
    
    async def search_hotel_prices(self, hotel_name: str, 
                                 check_in: str, 
                                 check_out: str) -> Dict[str, Any]:
        """호텔 가격 검색 (Google Hotels)"""
        if not self.api_key:
            return self._get_mock_price_data(hotel_name)
        
        try:
            params = {
                'q': hotel_name,
                'api_key': self.api_key,
                'engine': 'google_hotels',
                'check_in_date': check_in,
                'check_out_date': check_out,
                'currency': 'USD',
                'hl': 'en'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_hotel_prices(data)
                    else:
                        return self._get_mock_price_data(hotel_name)
                        
        except Exception as e:
            logger.error(f"가격 검색 실패: {str(e)}")
            return self._get_mock_price_data(hotel_name)
    
    async def search_attractions(self, location: str) -> List[Dict[str, Any]]:
        """관광지 검색"""
        query = f"top tourist attractions {location} things to do"
        
        if not self.api_key:
            return self._get_mock_attractions(location)
        
        try:
            params = {
                'q': query,
                'api_key': self.api_key,
                'engine': 'google',
                'num': 10,
                'hl': 'en'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_attractions(data)
                    else:
                        return self._get_mock_attractions(location)
                        
        except Exception as e:
            logger.error(f"관광지 검색 실패: {str(e)}")
            return self._get_mock_attractions(location)
    
    def _parse_search_results(self, query: str, data: Dict) -> GoogleSearchResult:
        """검색 결과 파싱 (안전한 타입 체크 추가)"""
        results = []
        
        # 일반 검색 결과
        for item in data.get('organic_results', [])[:5]:
            results.append({
                'title': item.get('title', ''),
                'link': item.get('link', ''),
                'snippet': item.get('snippet', ''),
                'source': item.get('source', '')
            })
        
        # 지식 패널 (있는 경우)
        if 'knowledge_graph' in data:
            kg = data['knowledge_graph']
            
            # [핵심 수정] rating 필드가 딕셔너리가 아닌 float일 수 있음을 처리
            rating_data = kg.get('rating')
            rating_val = None
            reviews_val = None
            
            if isinstance(rating_data, dict):
                rating_val = rating_data.get('rating')
                reviews_val = rating_data.get('reviews')
            elif isinstance(rating_data, (float, int)):
                rating_val = rating_data
            
            results.insert(0, {
                'title': kg.get('title', ''),
                'description': kg.get('description', ''),
                'rating': rating_val,
                'reviews': reviews_val,
                'type': 'knowledge_panel'
            })
        
        return GoogleSearchResult(
            query=query,
            results=results,
            timestamp=datetime.now()
        )
    
    def _parse_hotel_prices(self, data: Dict) -> Dict[str, Any]:
        """호텔 가격 정보 파싱"""
        prices = []
        for property in data.get('properties', [])[:5]:
            prices.append({
                'provider': property.get('provider', 'Unknown'),
                'price': property.get('rate_per_night', {}).get('lowest', 'N/A'),
                'total_price': property.get('total_rate', {}).get('lowest', 'N/A'),
                'link': property.get('link', '')
            })
        
        return {
            'hotel_name': data.get('search_information', {}).get('query', ''),
            'check_in': data.get('search_parameters', {}).get('check_in_date', ''),
            'check_out': data.get('search_parameters', {}).get('check_out_date', ''),
            'prices': prices,
            'avg_price': self._calculate_avg_price(prices)
        }
    
    def _calculate_avg_price(self, prices: List[Dict]) -> float:
        """평균 가격 계산"""
        valid_prices = []
        for p in prices:
            try:
                price_str = str(p.get('price', ''))
                price_clean = price_str.replace('$', '').replace(',', '')
                if price_clean and price_clean != 'N/A':
                    valid_prices.append(float(price_clean))
            except:
                continue
        return sum(valid_prices) / len(valid_prices) if valid_prices else 0
    
    def _parse_attractions(self, data: Dict) -> List[Dict[str, Any]]:
        """관광지 정보 파싱"""
        attractions = []
        for item in data.get('organic_results', []):
            title = item.get('title', '').lower()
            if any(word in title for word in ['museum', 'park', 'temple', 'palace', 
                                              'beach', 'market', 'tower', 'bridge']):
                attractions.append({
                    'name': item.get('title', ''),
                    'description': item.get('snippet', ''),
                    'link': item.get('link', '')
                })
        return attractions[:10]
    
    def _get_mock_results(self, hotel_name: str, location: str) -> GoogleSearchResult:
        """모의 검색 결과"""
        mock_results = [
            {
                'title': f"{hotel_name} - Official Website",
                'link': "#",
                'snippet': f"Book directly at {hotel_name} in {location}. Best rates guaranteed.",
                'source': 'Official Site'
            },
            {
                'title': f"{hotel_name} Reviews - TripAdvisor",
                'link': "#",
                'snippet': f"Rated 4.5/5. See reviews for {hotel_name}.",
                'source': 'TripAdvisor'
            }
        ]
        return GoogleSearchResult(
            query=f"{hotel_name} {location}",
            results=mock_results,
            timestamp=datetime.now()
        )
    
    def _get_mock_price_data(self, hotel_name: str) -> Dict[str, Any]:
        """모의 가격 데이터"""
        import random
        base_price = random.randint(100, 300)
        return {
            'hotel_name': hotel_name,
            'prices': [
                {'provider': 'Booking.com', 'price': f"${base_price}", 'total_price': f"${base_price * 3}"},
                {'provider': 'Hotels.com', 'price': f"${base_price + 10}", 'total_price': f"${(base_price + 10) * 3}"}
            ],
            'avg_price': base_price
        }
    
    def _get_mock_attractions(self, location: str) -> List[Dict[str, Any]]:
        """모의 관광지 데이터"""
        return [{'name': 'City Center', 'description': 'Main attraction', 'link': '#'}]