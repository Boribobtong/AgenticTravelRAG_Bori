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
        """
        호텔 정보 검색
        
        Args:
            hotel_name: 호텔 이름
            location: 위치
            
        Returns:
            검색 결과
        """
        
        query = f"{hotel_name} {location} hotel prices reviews"
        
        if not self.api_key:
            # API 키가 없으면 모의 데이터 반환
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
        """
        호텔 가격 검색 (Google Hotels)
        
        Args:
            hotel_name: 호텔 이름
            check_in: 체크인 날짜
            check_out: 체크아웃 날짜
            
        Returns:
            가격 정보
        """
        
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
        """
        관광지 검색
        
        Args:
            location: 위치
            
        Returns:
            관광지 리스트
        """
        
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
        """
        검색 결과 파싱
        
        Args:
            query: 검색 쿼리
            data: SerpApi 응답
            
        Returns:
            GoogleSearchResult
        """
        
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
            results.insert(0, {
                'title': kg.get('title', ''),
                'description': kg.get('description', ''),
                'rating': kg.get('rating', {}).get('rating', None),
                'reviews': kg.get('rating', {}).get('reviews', None),
                'type': 'knowledge_panel'
            })
        
        return GoogleSearchResult(
            query=query,
            results=results,
            timestamp=datetime.now()
        )
    
    def _parse_hotel_prices(self, data: Dict) -> Dict[str, Any]:
        """
        호텔 가격 정보 파싱
        
        Args:
            data: Google Hotels API 응답
            
        Returns:
            가격 정보
        """
        
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
                # $ 기호와 쉼표 제거
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
            # 제목에 관광지 키워드가 있는 경우만
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
        """모의 검색 결과 (API 키 없을 때)"""
        
        mock_results = [
            {
                'title': f"{hotel_name} - Official Website",
                'link': f"https://www.{hotel_name.lower().replace(' ', '')}.com",
                'snippet': f"Book directly at {hotel_name} in {location} for the best rates. Luxury accommodation with excellent amenities.",
                'source': 'Official Site'
            },
            {
                'title': f"{hotel_name} Reviews - TripAdvisor",
                'link': "https://www.tripadvisor.com",
                'snippet': f"Read {hotel_name} reviews from real guests. Rated 4.5/5 based on 500+ reviews. 'Excellent location and service'",
                'source': 'TripAdvisor'
            },
            {
                'title': f"{hotel_name} Booking.com",
                'link': "https://www.booking.com",
                'snippet': f"Book {hotel_name} with free cancellation. Prices from $150/night. Located in the heart of {location}.",
                'source': 'Booking.com'
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
                {'provider': 'Hotels.com', 'price': f"${base_price + 10}", 'total_price': f"${(base_price + 10) * 3}"},
                {'provider': 'Expedia', 'price': f"${base_price - 5}", 'total_price': f"${(base_price - 5) * 3}"}
            ],
            'avg_price': base_price
        }
    
    def _get_mock_attractions(self, location: str) -> List[Dict[str, Any]]:
        """모의 관광지 데이터"""
        
        mock_attractions = {
            'default': [
                {'name': 'City Museum', 'description': 'Historic museum with local artifacts', 'link': '#'},
                {'name': 'Central Park', 'description': 'Beautiful park in the city center', 'link': '#'},
                {'name': 'Old Town Market', 'description': 'Traditional market with local goods', 'link': '#'},
                {'name': 'Royal Palace', 'description': 'Historic palace with guided tours', 'link': '#'},
                {'name': 'Art Gallery', 'description': 'Modern and contemporary art', 'link': '#'}
            ],
            'Bangkok': [
                {'name': 'Grand Palace', 'description': 'Historic royal palace complex', 'link': '#'},
                {'name': 'Wat Pho Temple', 'description': 'Temple of the Reclining Buddha', 'link': '#'},
                {'name': 'Chatuchak Market', 'description': 'Massive weekend market', 'link': '#'},
                {'name': 'Wat Arun', 'description': 'Temple of Dawn by the river', 'link': '#'},
                {'name': 'Jim Thompson House', 'description': 'Traditional Thai house museum', 'link': '#'}
            ],
            'Paris': [
                {'name': 'Eiffel Tower', 'description': 'Iconic iron lattice tower', 'link': '#'},
                {'name': 'Louvre Museum', 'description': "World's largest art museum", 'link': '#'},
                {'name': 'Notre-Dame Cathedral', 'description': 'Gothic cathedral', 'link': '#'},
                {'name': 'Arc de Triomphe', 'description': 'Triumphal arch monument', 'link': '#'},
                {'name': 'Sacré-Cœur', 'description': 'Basilica on Montmartre hill', 'link': '#'}
            ]
        }
        
        # 위치에 따른 관광지 반환
        for key in mock_attractions:
            if key.lower() in location.lower():
                return mock_attractions[key]
        
        return mock_attractions['default']
