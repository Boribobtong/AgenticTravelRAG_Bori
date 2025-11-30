"""
Currency Converter Node for Parallel Workflow

환율 변환 에이전트를 워크플로우에 통합하는 노드
"""

import logging
from typing import Dict, Any
from src.agents.currency_converter import CurrencyConverterAgent

logger = logging.getLogger(__name__)


class CurrencyConverterNode:
    """환율 변환 워크플로우 노드"""
    
    def __init__(self):
        """초기화"""
        self.agent = CurrencyConverterAgent()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        환율 변환 노드 실행
        
        Args:
            state: 현재 워크플로우 상태
                {
                    'query': str,
                    'context': {
                        'hotels': [...],
                        'flights': [...],
                        ...
                    }
                }
        
        Returns:
            업데이트된 상태
                {
                    'context': {
                        'currency_conversions': {...},
                        ...
                    }
                }
        """
        try:
            self.logger.info("[CurrencyConverter] 환율 변환 처리 시작")
            
            # 기본 통화 (기본값: USD)
            base_currency = 'USD'
            
            # 변환 대상 통화 목록
            target_currencies = ['KRW', 'EUR', 'GBP', 'JPY', 'CNY']
            
            # 환율 조회
            exchange_rates = await self.agent.get_exchange_rates(base_currency)
            
            # 필터링된 환율
            filtered_rates = {
                curr: exchange_rates.get(curr)
                for curr in target_currencies
                if curr in exchange_rates
            }
            
            # Context에 환율 정보 추가
            if 'context' not in state:
                state['context'] = {}
            
            state['context']['currency_conversions'] = {
                'base_currency': base_currency,
                'exchange_rates': filtered_rates,
                'timestamp': self._get_timestamp()
            }
            
            # 호텔 가격 정규화
            hotels = state.get('context', {}).get('hotels', [])
            normalized_hotels = []
            
            for hotel in hotels:
                if isinstance(hotel, dict):
                    hotel_copy = hotel.copy()
                    
                    # 가격 정규화 (USD 기준)
                    if 'price' in hotel_copy and 'currency' in hotel_copy:
                        result = await self.agent.convert(
                            hotel_copy['price'],
                            hotel_copy['currency'],
                            base_currency
                        )
                        
                        if 'error' not in result:
                            hotel_copy['price_usd'] = result['converted_amount']
                            hotel_copy['exchange_rate'] = result['exchange_rate']
                    
                    normalized_hotels.append(hotel_copy)
            
            if normalized_hotels:
                state['context']['normalized_hotels'] = normalized_hotels
            
            # 항공편 가격 정규화
            flights = state.get('context', {}).get('flights', [])
            normalized_flights = []
            
            for flight in flights:
                if isinstance(flight, dict):
                    flight_copy = flight.copy()
                    
                    # 가격 정규화
                    if 'price' in flight_copy and 'currency' in flight_copy:
                        result = await self.agent.convert(
                            flight_copy['price'],
                            flight_copy['currency'],
                            base_currency
                        )
                        
                        if 'error' not in result:
                            flight_copy['price_usd'] = result['converted_amount']
                            flight_copy['exchange_rate'] = result['exchange_rate']
                    
                    normalized_flights.append(flight_copy)
            
            if normalized_flights:
                state['context']['normalized_flights'] = normalized_flights
            
            self.logger.info(
                "[CurrencyConverter] 환율 변환 완료: %s개 환율, %s개 호텔, %s개 항공편",
                len(exchange_rates), len(normalized_hotels), len(normalized_flights)
            )
            
        except Exception:  # pylint: disable=broad-except
            self.logger.error("[CurrencyConverter] 에러 발생", exc_info=True)
            
            # 에러 발생 시 기본값 반환 (graceful degradation)
            if 'context' not in state:
                state['context'] = {}
            
            state['context']['currency_error'] = 'Currency conversion failed'
        
        return state
    
    async def normalize_prices(
        self,
        items: list,
        source_currency: str = None,
        target_currency: str = 'USD'
    ) -> list:
        """
        항목들의 가격 정규화
        
        Args:
            items: 가격을 포함한 항목 리스트
            source_currency: 원본 통화 (None이면 항목의 currency 필드 사용)
            target_currency: 목표 통화
        
        Returns:
            정규화된 항목 리스트
        """
        normalized = []
        
        for item in items:
            item_copy = item.copy() if isinstance(item, dict) else item
            
            if isinstance(item_copy, dict):
                currency = source_currency or item_copy.get('currency')
                price = item_copy.get('price')
                
                if currency and price and currency != target_currency:
                    result = await self.agent.convert(
                        price,
                        currency,
                        target_currency
                    )
                    
                    if 'error' not in result:
                        item_copy['normalized_price'] = result['converted_amount']
                        item_copy['normalized_currency'] = target_currency
            
            normalized.append(item_copy)
        
        return normalized
    
    async def get_price_in_currencies(
        self,
        amount: float,
        from_currency: str,
        to_currencies: list = None
    ) -> Dict[str, Any]:
        """
        다양한 통화로 가격 변환
        
        Args:
            amount: 금액
            from_currency: 원본 통화
            to_currencies: 목표 통화 목록 (None이면 주요 통화)
        
        Returns:
            다양한 통화로의 변환 결과
        """
        if to_currencies is None:
            to_currencies = ['KRW', 'EUR', 'GBP', 'JPY', 'CNY', 'AUD', 'CAD']
        
        results = {
            'original': {
                'amount': amount,
                'currency': from_currency
            },
            'conversions': {}
        }
        
        for target_currency in to_currencies:
            try:
                result = await self.agent.convert(
                    amount,
                    from_currency,
                    target_currency
                )
                
                if 'error' not in result:
                    results['conversions'][target_currency] = {
                        'amount': result['converted_amount'],
                        'rate': result['exchange_rate']
                    }
            except Exception:  # pylint: disable=broad-except
                self.logger.debug(
                    "[CurrencyConverter] %s → %s 변환 실패",
                    from_currency, target_currency
                )
        
        return results
    
    @staticmethod
    def _get_timestamp() -> str:
        """현재 타임스탬프 반환"""
        from datetime import datetime
        return datetime.now().isoformat()


# 전역 노드 인스턴스 관리
class _CurrencyNodeManager:
    """CurrencyConverterNode 싱글톤 관리"""
    _instance = None
    
    @classmethod
    def get_instance(cls) -> CurrencyConverterNode:
        """인스턴스 획득"""
        if cls._instance is None:
            cls._instance = CurrencyConverterNode()
        return cls._instance


async def get_currency_node() -> CurrencyConverterNode:
    """CurrencyConverterNode 인스턴스 획득"""
    return _CurrencyNodeManager.get_instance()


async def execute_currency_conversion(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    워크플로우 노드 실행 함수
    
    Args:
        state: 워크플로우 상태
    
    Returns:
        업데이트된 상태
    """
    node = await get_currency_node()
    return await node.execute(state)
