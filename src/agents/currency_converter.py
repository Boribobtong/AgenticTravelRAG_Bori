"""
Currency Converter Agent: 환율 변환 에이전트

실시간 환율 정보를 제공하고 통화 변환을 수행합니다.
- ExchangeRate API 통합
- 캐싱으로 API 호출 최소화
- 주요 통화 지원
"""

import logging
import os
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import aiohttp

logger = logging.getLogger(__name__)


class CurrencyConverterAgent:
    """환율 변환 에이전트
    
    Features:
    - 실시간 환율 조회
    - 다중 통화 변환
    - 환율 캐싱 (1시간)
    - 기록 및 통계
    """
    
    def __init__(self):
        """초기화"""
        # 주요 통화 (여행자 중심)
        self.supported_currencies = {
            'USD': '미국 달러',
            'EUR': '유로',
            'GBP': '영국 파운드',
            'JPY': '일본 엔',
            'KRW': '한국 원',
            'CNY': '중국 위안',
            'AUD': '호주 달러',
            'CAD': '캐나다 달러',
            'SGD': '싱가포르 달러',
            'HKD': '홍콩 달러',
            'THB': '태국 바트',
            'MXN': '멕시코 페소',
            'BRL': '브라질 레알',
            'INR': '인도 루피',
            'IDR': '인도네시아 루피아',
        }
        
        # API 설정
        self.api_url = "https://api.exchangerate-api.com/v4/latest"
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_duration = 3600  # 1시간
        
        logger.info("CurrencyConverterAgent 초기화 완료 (%d개 통화 지원)", 
                   len(self.supported_currencies))
    
    async def convert(self, amount: float, from_currency: str, 
                     to_currency: str, date: Optional[str] = None) -> Dict[str, Any]:
        """통화 변환
        
        Args:
            amount: 변환할 금액
            from_currency: 원본 통화 코드 (예: USD)
            to_currency: 목표 통화 코드 (예: KRW)
            date: 날짜 (기본: 오늘)
        
        Returns:
            {
                'original_amount': 150.0,
                'original_currency': 'USD',
                'converted_amount': 200000.0,
                'target_currency': 'KRW',
                'exchange_rate': 1333.33,
                'timestamp': '2025-11-30T10:00:00',
                'source': 'exchangerate-api'
            }
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # 검증
        if from_currency not in self.supported_currencies:
            logger.warning(f"[CurrencyConverter] 지원하지 않는 통화: {from_currency}")
            return {
                'error': f'지원하지 않는 통화: {from_currency}',
                'supported_currencies': list(self.supported_currencies.keys())
            }
        
        if to_currency not in self.supported_currencies:
            logger.warning(f"[CurrencyConverter] 지원하지 않는 통화: {to_currency}")
            return {
                'error': f'지원하지 않는 통화: {to_currency}',
                'supported_currencies': list(self.supported_currencies.keys())
            }
        
        # 동일 통화 변환
        if from_currency == to_currency:
            return {
                'original_amount': amount,
                'original_currency': from_currency,
                'converted_amount': amount,
                'target_currency': to_currency,
                'exchange_rate': 1.0,
                'timestamp': datetime.now().isoformat(),
                'source': 'same_currency'
            }
        
        try:
            # 환율 조회
            exchange_rate = await self._get_exchange_rate(from_currency, to_currency)
            
            if exchange_rate is None:
                return {
                    'error': f'{from_currency}에서 {to_currency}로 변환할 수 없습니다',
                    'details': '환율 정보를 가져올 수 없습니다'
                }
            
            # 변환
            converted_amount = amount * exchange_rate
            
            logger.info(
                "[CurrencyConverter] 변환 완료: %.2f %s → %.2f %s (환율: %.4f)",
                amount, from_currency, converted_amount, to_currency, exchange_rate
            )
            
            return {
                'success': True,
                'original_amount': amount,
                'original_currency': from_currency,
                'converted_amount': round(converted_amount, 2),
                'target_currency': to_currency,
                'exchange_rate': round(exchange_rate, 4),
                'timestamp': datetime.now().isoformat(),
                'source': 'exchangerate-api'
            }
        
        except Exception as e:
            logger.error(f"[CurrencyConverter] 변환 실패: {str(e)}")
            return {
                'error': str(e),
                'details': '환율 변환 중 오류가 발생했습니다'
            }
    
    async def _get_exchange_rate(self, from_currency: str, 
                                to_currency: str) -> Optional[float]:
        """환율 조회 (캐싱 포함)
        
        Args:
            from_currency: 원본 통화
            to_currency: 목표 통화
        
        Returns:
            환율 (예: 1333.33)
        """
        cache_key = f"{from_currency}_{to_currency}"
        
        # 캐시 확인
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached['timestamp'] < timedelta(seconds=self.cache_duration):
                logger.debug(f"[CurrencyConverter] 캐시 사용: {cache_key}")
                return cached['rate']
            else:
                # 캐시 만료
                del self.cache[cache_key]
        
        try:
            # API 호출
            rate = await self._fetch_exchange_rate(from_currency, to_currency)
            
            if rate is not None:
                # 캐시 저장
                self.cache[cache_key] = {
                    'rate': rate,
                    'timestamp': datetime.now()
                }
                logger.debug(f"[CurrencyConverter] API 호출: {cache_key} = {rate}")
            
            return rate
        
        except Exception as e:
            logger.error(f"[CurrencyConverter] 환율 조회 실패: {str(e)}")
            # 폴백: 모의 데이터 (개발용)
            return self._get_fallback_rate(from_currency, to_currency)
    
    async def _fetch_exchange_rate(self, from_currency: str, 
                                   to_currency: str) -> Optional[float]:
        """ExchangeRate API에서 환율 조회"""
        try:
            url = f"{self.api_url}/{from_currency}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        rates = data.get('rates', {})
                        rate = rates.get(to_currency)
                        
                        if rate:
                            logger.info(
                                f"[CurrencyConverter] API 성공: "
                                f"1 {from_currency} = {rate} {to_currency}"
                            )
                            return float(rate)
                    else:
                        logger.warning(f"[CurrencyConverter] API 오류: {response.status}")
                        return None
        
        except asyncio.TimeoutError:
            logger.warning(f"[CurrencyConverter] API 타임아웃")
            return None
        except Exception as e:
            logger.error(f"[CurrencyConverter] API 호출 실패: {str(e)}")
            return None
    
    def _get_fallback_rate(self, from_currency: str, 
                          to_currency: str) -> Optional[float]:
        """폴백 환율 데이터 (개발/테스트용)"""
        fallback_rates = {
            ('USD', 'KRW'): 1333.33,
            ('USD', 'EUR'): 0.92,
            ('USD', 'GBP'): 0.79,
            ('USD', 'JPY'): 149.50,
            ('USD', 'CNY'): 7.24,
            ('EUR', 'KRW'): 1450.00,
            ('EUR', 'GBP'): 0.86,
            ('GBP', 'KRW'): 1690.00,
            ('JPY', 'KRW'): 8.92,
            ('KRW', 'USD'): 0.00075,
            ('KRW', 'EUR'): 0.00069,
        }
        
        # 역방향 계산
        if (from_currency, to_currency) in fallback_rates:
            return fallback_rates[(from_currency, to_currency)]
        elif (to_currency, from_currency) in fallback_rates:
            return 1 / fallback_rates[(to_currency, from_currency)]
        
        logger.warning(f"[CurrencyConverter] 폴백 데이터 없음: {from_currency}-{to_currency}")
        return None
    
    async def get_exchange_rates(self, base_currency: str) -> Dict[str, float]:
        """기본 통화 기준 모든 환율 조회
        
        Args:
            base_currency: 기준 통화 (예: USD)
        
        Returns:
            {
                'EUR': 0.92,
                'GBP': 0.79,
                'JPY': 149.50,
                ...
            }
        """
        base_currency = base_currency.upper()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/{base_currency}",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        rates = data.get('rates', {})
                        
                        # 지원 통화만 필터링
                        filtered_rates = {
                            curr: rates.get(curr)
                            for curr in self.supported_currencies
                            if curr in rates
                        }
                        
                        logger.info(f"[CurrencyConverter] 환율 조회 완료: {base_currency} 기준")
                        return filtered_rates
        
        except Exception as e:
            logger.error(f"[CurrencyConverter] 환율 조회 실패: {str(e)}")
        
        return {}
    
    async def format_price(self, amount: float, currency: str, 
                          target_currencies: List[str] = None) -> Dict[str, Any]:
        """가격을 다양한 통화로 포맷팅
        
        Args:
            amount: 금액
            currency: 원본 통화
            target_currencies: 변환할 통화 목록
        
        Returns:
            {
                'original': '$150.00 USD',
                'conversions': {
                    'KRW': '₩200,000',
                    'EUR': '€138.00',
                    'JPY': '¥22,425'
                }
            }
        """
        if target_currencies is None:
            target_currencies = ['KRW', 'EUR', 'GBP', 'JPY']
        
        currency = currency.upper()
        
        # 심볼 매핑
        symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': '¥',
            'KRW': '₩',
            'CNY': '¥',
            'AUD': 'A$',
            'CAD': 'C$',
            'SGD': 'S$',
            'HKD': 'HK$',
            'THB': '฿',
            'MXN': '$',
            'BRL': 'R$',
            'INR': '₹',
            'IDR': 'Rp',
        }
        
        symbol = symbols.get(currency, currency)
        
        # 원본 포맷
        original_formatted = f"{symbol}{amount:,.2f} {currency}"
        
        # 변환
        conversions = {}
        for target in target_currencies:
            if target != currency:
                result = await self.convert(amount, currency, target)
                if result.get('success'):
                    target_symbol = symbols.get(target, target)
                    converted_amount = result['converted_amount']
                    
                    # JPY는 소수점 없음
                    if target == 'JPY':
                        conversions[target] = f"{target_symbol}{int(converted_amount):,}"
                    else:
                        conversions[target] = f"{target_symbol}{converted_amount:,.2f}"
        
        return {
            'original': original_formatted,
            'conversions': conversions,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_supported_currencies(self) -> Dict[str, str]:
        """지원하는 통화 목록 반환"""
        return self.supported_currencies.copy()
    
    def clear_cache(self):
        """캐시 초기화"""
        self.cache.clear()
        logger.info("[CurrencyConverter] 캐시 초기화 완료")
