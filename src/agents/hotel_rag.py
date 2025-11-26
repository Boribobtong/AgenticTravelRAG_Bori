"""
Hotel RAG Agent: 호텔 검색 에이전트

ElasticSearch RAG 파이프라인을 사용하여 
사용자 요구사항에 맞는 호텔을 검색합니다.
"""

import logging
from typing import Dict, Any, List, Optional
try:
    from src.rag.elasticsearch_rag import get_rag_instance, ElasticSearchRAG
    _RAG_AVAILABLE = True
except Exception:
    get_rag_instance = None
    ElasticSearchRAG = None
    _RAG_AVAILABLE = False
from src.core.state import HotelOption

logger = logging.getLogger(__name__)


class HotelRAGAgent:
    """
    ElasticSearch 하이브리드 검색을 통한 호텔 추천 에이전트
    """
    
    def __init__(self):
        """초기화"""
        if _RAG_AVAILABLE and get_rag_instance is not None:
            try:
                self.rag = get_rag_instance()
            except Exception as e:
                logger.warning("RAG 인스턴스 생성 실패: %s", e)
                self.rag = None
        else:
            logger.warning("ElasticSearch RAG 라이브러리 미설치: 검색 기능은 제한됩니다.")
            self.rag = None

        logger.info("HotelRAGAgent 초기화 완료")
    
    async def search(self, search_params: Dict[str, Any]) -> List[HotelOption]:
        """
        호텔 검색 실행
        
        Args:
            search_params: 검색 파라미터
                - destination: 목적지
                - preferences: 선호도 정보
                - budget: 예산 범위
                
        Returns:
            HotelOption 리스트
        """
        
        try:
            # 검색 쿼리 구성
            query = self._build_search_query(search_params)
            
            # 필터 설정
            location = search_params.get('destination')
            min_rating = 3.5  # 기본 최소 평점
            tags = []
            
            # 선호도에서 태그 추출
            if search_params.get('preferences'):
                prefs = search_params['preferences']
                
                # 편의시설 태그
                if prefs.get('amenities'):
                    tags.extend(prefs['amenities'])
                
                # 분위기 태그
                if prefs.get('atmosphere'):
                    for atm in prefs['atmosphere']:
                        if atm == 'family':
                            tags.append('family')
                        elif atm == 'romantic':
                            tags.append('romantic')
                        elif atm == 'business':
                            tags.append('business')
            
            # ElasticSearch 하이브리드 검색 실행
            if not self.rag:
                logger.warning("RAG 인스턴스가 없어 빈 결과 반환")
                return []

            results = self.rag.hybrid_search(
                query=query,
                location=location,
                min_rating=min_rating,
                tags=tags if tags else None,
                top_k=10,
                alpha=0.6  # 시맨틱 검색 가중치를 높게
            )
            
            # 결과를 HotelOption으로 변환
            hotel_options = []
            for result in results:
                hotel_option = HotelOption(
                    hotel_id=f"hotel_{len(hotel_options)}",
                    name=result['hotel_name'],
                    location=result['location'],
                    rating=result['rating'],
                    review_count=len(result.get('review_snippet', '')) // 50,  # 임시
                    price_range=self._estimate_price_range(result),
                    amenities=result.get('tags', []),
                    review_highlights=self._extract_highlights(result['review_snippet']),
                    semantic_score=result.get('semantic_score', 0),
                    bm25_score=result.get('bm25_score', 0),
                    combined_score=result['combined_score']
                )
                hotel_options.append(hotel_option)
            
            # 예산 필터링
            if search_params.get('budget'):
                hotel_options = self._filter_by_budget(hotel_options, search_params['budget'])
            
            # 점수 기준 정렬
            hotel_options.sort(key=lambda x: x.combined_score, reverse=True)
            
            logger.info(f"호텔 검색 완료: {len(hotel_options)}개 결과")
            return hotel_options[:5]  # 상위 5개만 반환
            
        except Exception as e:
            logger.error(f"호텔 검색 실패: {str(e)}")
            return []
    
    async def search_with_fallback(self, search_params: Dict[str, Any]) -> List[HotelOption]:
        """
        Fallback 로직이 포함된 호텔 검색
        
        1차: 모든 조건으로 검색
        2차: 필수 조건만 (목적지 + 최소 평점)
        3차: 빈 결과 반환 (workflow에서 처리)
        
        Args:
            search_params: 검색 파라미터
            
        Returns:
            HotelOption 리스트
        """
        # 1차 검색: 모든 조건
        results = await self.search(search_params)
        
        if len(results) >= 3:
            logger.info(f"[Fallback] 1차 검색 성공: {len(results)}개 결과")
            return results
        
        # 2차 검색: 조건 완화 (필수 조건만)
        logger.warning(f"[Fallback] 1차 검색 결과 부족 ({len(results)}개), 조건 완화 시도")
        
        relaxed_params = {
            'destination': search_params.get('destination'),
            'preferences': {
                # 분위기, 편의시설 제거, 최소 평점만 유지
            }
        }
        
        relaxed_results = await self.search(relaxed_params)
        
        if len(relaxed_results) >= 3:
            logger.info(f"[Fallback] 2차 검색 성공: {len(relaxed_results)}개 결과")
            # 완화 메시지 추가
            for hotel in relaxed_results:
                hotel.search_note = "조건을 일부 완화하여 검색했습니다."
            return relaxed_results
        
        # 3차: 빈 결과 반환 (workflow에서 안내 메시지 처리)
        logger.warning(f"[Fallback] 2차 검색도 결과 부족, 빈 결과 반환")
        return []
    
    def _build_search_query(self, search_params: Dict[str, Any]) -> str:
        """
        검색 쿼리 구성
        
        Args:
            search_params: 검색 파라미터
            
        Returns:
            검색 쿼리 문자열
        """
        
        query_parts = []
        
        # 목적지
        if search_params.get('destination'):
            query_parts.append(search_params['destination'])
        
        # 선호도
        if search_params.get('preferences'):
            prefs = search_params['preferences']
            
            # 분위기 키워드
            if prefs.get('atmosphere'):
                query_parts.extend(prefs['atmosphere'])
            
            # 숙박 유형
            if prefs.get('accommodation_type'):
                query_parts.append(prefs['accommodation_type'])
            
            # 특별 요구사항
            if prefs.get('special_requirements'):
                query_parts.append(prefs['special_requirements'])
        
        # 쿼리가 비어있으면 기본값
        if not query_parts:
            query_parts = ['good hotel', 'comfortable', 'clean']
        
        return ' '.join(query_parts)
    
    def _estimate_price_range(self, result: Dict) -> str:
        """
        가격 범위 추정 (리뷰 텍스트 기반)
        
        Args:
            result: 검색 결과
            
        Returns:
            가격 범위 문자열
        """
        
        review_text = result.get('review_snippet', '').lower()
        
        # 가격 관련 키워드 분석
        if any(word in review_text for word in ['luxury', 'expensive', 'premium', 'high-end']):
            return "$$$$$"
        elif any(word in review_text for word in ['upscale', 'pricey']):
            return "$$$$"
        elif any(word in review_text for word in ['reasonable', 'moderate', 'fair price']):
            return "$$$"
        elif any(word in review_text for word in ['budget', 'cheap', 'affordable']):
            return "$$"
        else:
            return "$$$"  # 기본값
    
    def _extract_highlights(self, review_snippet: str) -> List[str]:
        """
        리뷰에서 하이라이트 추출
        
        Args:
            review_snippet: 리뷰 텍스트 일부
            
        Returns:
            하이라이트 리스트
        """
        
        highlights = []
        snippet_lower = review_snippet.lower()
        
        # 긍정적 키워드 체크
        positive_keywords = {
            'excellent': '훌륭한 서비스',
            'amazing': '놀라운 경험',
            'clean': '깨끗한 시설',
            'friendly': '친절한 직원',
            'comfortable': '편안한 객실',
            'great location': '좋은 위치',
            'good breakfast': '만족스러운 조식',
            'spacious': '넓은 공간',
            'quiet': '조용한 환경',
            'modern': '현대적인 시설'
        }
        
        for keyword, highlight in positive_keywords.items():
            if keyword in snippet_lower:
                highlights.append(highlight)
        
        # 최대 3개까지만
        return highlights[:3] if highlights else ['고객 만족도 높음']
    
    def _filter_by_budget(self, hotels: List[HotelOption], budget_range: tuple) -> List[HotelOption]:
        """
        예산으로 호텔 필터링
        
        Args:
            hotels: 호텔 리스트
            budget_range: (min, max) 예산 범위
            
        Returns:
            필터링된 호텔 리스트
        """
        
        if not budget_range:
            return hotels
        
        min_budget, max_budget = budget_range
        
        # 가격 범위를 숫자로 매핑
        price_map = {
            "$": 50,
            "$$": 100,
            "$$$": 200,
            "$$$$": 400,
            "$$$$$": 800
        }
        
        filtered = []
        for hotel in hotels:
            estimated_price = price_map.get(hotel.price_range, 200)
            if min_budget <= estimated_price <= max_budget:
                filtered.append(hotel)
        
        return filtered if filtered else hotels[:2]  # 결과가 없으면 상위 2개 반환
    
    async def get_hotel_details(self, hotel_name: str) -> Dict[str, Any]:
        """
        특정 호텔의 상세 정보 조회
        
        Args:
            hotel_name: 호텔 이름
            
        Returns:
            호텔 상세 정보
        """
        
        try:
            # 호텔 리뷰 분석
            analysis = self.rag.analyze_hotel_reviews(hotel_name)
            
            # 유사 호텔 찾기
            similar_hotels = self.rag.get_similar_hotels(hotel_name, top_k=3)
            
            return {
                'hotel_name': hotel_name,
                'analysis': analysis,
                'similar_hotels': similar_hotels
            }
            
        except Exception as e:
            logger.error(f"호텔 상세 정보 조회 실패: {str(e)}")
            return {}
    
    async def refine_search(self, previous_results: List[HotelOption], 
                           feedback: str) -> List[HotelOption]:
        """
        사용자 피드백 기반 검색 개선
        
        Args:
            previous_results: 이전 검색 결과
            feedback: 사용자 피드백
            
        Returns:
            개선된 검색 결과
        """
        
        # 피드백 분석
        feedback_lower = feedback.lower()
        
        # 제외할 호텔
        exclude_hotels = [h.name for h in previous_results]
        
        # 새로운 검색 쿼리 구성
        new_query_parts = []
        
        if '더 저렴' in feedback or 'cheaper' in feedback_lower:
            new_query_parts.append('budget affordable')
        elif '더 고급' in feedback or 'luxury' in feedback_lower:
            new_query_parts.append('luxury premium')
        
        if '조용' in feedback or 'quiet' in feedback_lower:
            new_query_parts.append('quiet peaceful')
        
        if '중심' in feedback or 'center' in feedback_lower:
            new_query_parts.append('city center central location')
        
        # 새로운 검색 실행
        new_query = ' '.join(new_query_parts) if new_query_parts else 'alternative hotel options'
        
        results = self.rag.hybrid_search(
            query=new_query,
            location=previous_results[0].location if previous_results else None,
            min_rating=3.0,  # 기준 완화
            top_k=15,
            alpha=0.7  # 시맨틱 가중치 증가
        )
        
        # 이전 결과 제외
        filtered_results = []
        for result in results:
            if result['hotel_name'] not in exclude_hotels:
                hotel_option = HotelOption(
                    hotel_id=f"refined_{len(filtered_results)}",
                    name=result['hotel_name'],
                    location=result['location'],
                    rating=result['rating'],
                    review_count=10,  # 임시
                    price_range=self._estimate_price_range(result),
                    amenities=result.get('tags', []),
                    review_highlights=self._extract_highlights(result['review_snippet']),
                    semantic_score=result.get('semantic_score', 0),
                    bm25_score=result.get('bm25_score', 0),
                    combined_score=result['combined_score']
                )
                filtered_results.append(hotel_option)
        
        return filtered_results[:5]
