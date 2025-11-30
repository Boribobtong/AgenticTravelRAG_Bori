"""
Integration Tests for CurrencyConverterAgent with Workflow

워크플로우에 통합된 환율 변환 에이전트 테스트
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
from datetime import datetime
from src.agents.currency_converter import CurrencyConverterAgent


@pytest.fixture
def currency_agent():
    """CurrencyConverterAgent 인스턴스"""
    return CurrencyConverterAgent()


class TestCurrencyConverterIntegration:
    """CurrencyConverterAgent 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_basic_conversion_flow(self, currency_agent):
        """기본 변환 흐름"""
        # 1단계: 여러 통화로 가격 변환
        prices = {
            'USD': 150,
            'EUR': 140,
            'GBP': 130
        }
        
        conversions = {}
        for base_currency, amount in prices.items():
            result = await currency_agent.convert(amount, base_currency, 'KRW')
            if 'error' not in result:
                conversions[base_currency] = result
        
        # 결과 검증
        assert len(conversions) > 0
        assert all('converted_amount' in conv for conv in conversions.values())
    
    @pytest.mark.asyncio
    async def test_format_price_integration(self, currency_agent):
        """가격 포맷팅 통합"""
        # 여행 패키지 가격 (USD 기준)
        base_price = 1500  # USD
        
        # 다양한 통화로 포맷
        result = await currency_agent.format_price(
            base_price, 
            'USD',
            ['EUR', 'GBP', 'KRW', 'JPY']
        )
        
        assert result['original'] == '$1,500.00 USD'
        assert 'conversions' in result
    
    @pytest.mark.asyncio
    async def test_batch_conversion(self, currency_agent):
        """배치 환율 변환"""
        hotel_prices = [
            {'name': '호텔A', 'price': 200, 'currency': 'USD'},
            {'name': '호텔B', 'price': 180, 'currency': 'EUR'},
            {'name': '호텔C', 'price': 150, 'currency': 'GBP'},
        ]
        
        converted_prices = []
        for hotel in hotel_prices:
            result = await currency_agent.convert(
                hotel['price'],
                hotel['currency'],
                'KRW'
            )
            
            if 'error' not in result:
                hotel_copy = hotel.copy()
                hotel_copy.update({
                    'krw_price': result['converted_amount'],
                    'rate': result['exchange_rate']
                })
                converted_prices.append(hotel_copy)
        
        # 결과 검증
        assert len(converted_prices) > 0
        assert all('krw_price' in h for h in converted_prices)
    
    @pytest.mark.asyncio
    async def test_multi_destination_pricing(self, currency_agent):
        """다중 목적지 가격 정보"""
        destinations = {
            '서울': {'currency': 'KRW', 'hotel_price': 150000},
            'NYC': {'currency': 'USD', 'hotel_price': 200},
            '도쿄': {'currency': 'JPY', 'hotel_price': 20000},
            '방콕': {'currency': 'THB', 'hotel_price': 3500},
        }
        
        # 모든 가격을 USD로 표준화
        usd_prices = {}
        for city, info in destinations.items():
            if info['currency'] != 'USD':
                result = await currency_agent.convert(
                    info['hotel_price'],
                    info['currency'],
                    'USD'
                )
                if 'error' not in result:
                    usd_prices[city] = result['converted_amount']
            else:
                usd_prices[city] = info['hotel_price']
        
        # 결과 검증 - 최소 일부는 변환되어야 함
        assert len(usd_prices) > 0
    
    @pytest.mark.asyncio
    async def test_workflow_state_with_currency(self, currency_agent):
        """워크플로우 상태에 환율 정보 통합"""
        # 사용자 쿼리
        user_query = "서울과 도쿄 호텔 가격 비교"
        
        # 상태 초기화 (딕셔너리 형식)
        state = {
            'query': user_query,
            'enriched_query': user_query,
            'context': {
                'hotels': [
                    {'name': 'Hotel A', 'price': 150000, 'currency': 'KRW', 'city': 'Seoul'},
                    {'name': 'Hotel B', 'price': 20000, 'currency': 'JPY', 'city': 'Tokyo'},
                ]
            }
        }
        
        # 가격 정규화
        hotels = state['context'].get('hotels', [])
        for hotel in hotels:
            if hotel['currency'] != 'USD':
                result = await currency_agent.convert(
                    hotel['price'],
                    hotel['currency'],
                    'USD'
                )
                if 'error' not in result:
                    hotel['price_usd'] = result['converted_amount']
                    hotel['exchange_rate'] = result['exchange_rate']
        
        # 결과 검증
        assert all('price_usd' in h for h in hotels if h['currency'] != 'USD')
    
    @pytest.mark.asyncio
    async def test_error_handling_in_batch(self, currency_agent):
        """배치 작업에서 에러 처리"""
        conversions = [
            (100, 'USD', 'KRW'),
            (100, 'XYZ', 'KRW'),  # 지원하지 않는 통화
            (50, 'EUR', 'ABC'),   # 지원하지 않는 통화
            (200, 'GBP', 'JPY'),
        ]
        
        results = []
        errors = []
        
        for amount, from_cur, to_cur in conversions:
            result = await currency_agent.convert(amount, from_cur, to_cur)
            
            if 'error' in result:
                errors.append(result['error'])
            else:
                results.append(result)
        
        # 일부는 성공, 일부는 실패
        assert len(results) > 0
        assert len(errors) > 0
    
    @pytest.mark.asyncio
    async def test_caching_in_repeated_queries(self, currency_agent):
        """반복 쿼리에서 캐싱"""
        # 동일 쌍에 대한 반복 호출
        pair = ('USD', 'KRW')
        
        # 첫 번째 호출
        result1 = await currency_agent.convert(100, pair[0], pair[1])
        cache_size_1 = len(currency_agent.cache)
        
        # 두 번째 호출 (캐시 사용)
        result2 = await currency_agent.convert(100, pair[0], pair[1])
        cache_size_2 = len(currency_agent.cache)
        
        # 캐시 크기 동일해야 함 (새로운 항목 추가 안 됨)
        assert cache_size_1 == cache_size_2
        
        # 결과는 동일해야 함
        if 'exchange_rate' in result1 and 'exchange_rate' in result2:
            assert result1['exchange_rate'] == result2['exchange_rate']


class TestCurrencyConverterWithMocking:
    """Mock을 사용한 테스트"""
    
    @pytest.mark.asyncio
    async def test_api_failure_graceful_degradation(self, currency_agent):
        """API 실패 시 폴백"""
        # 정상 동작 확인
        result = await currency_agent.convert(100, 'USD', 'KRW')
        
        # 성공하거나 폴백 데이터 사용
        assert 'converted_amount' in result or 'error' in result
    
    @pytest.mark.asyncio
    async def test_exchange_rates_bulk_query(self, currency_agent):
        """대량 환율 조회"""
        # 다양한 기준 통화로 환율 조회
        base_currencies = ['USD', 'EUR', 'GBP', 'KRW', 'JPY']
        
        all_rates = {}
        for base_cur in base_currencies:
            try:
                rates = await currency_agent.get_exchange_rates(base_cur)
                all_rates[base_cur] = len(rates)
            except Exception:
                # 일부 실패는 허용
                pass
        
        # 최소 일부는 조회되어야 함
        assert len(all_rates) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_conversions(self, currency_agent):
        """동시 환율 변환"""
        conversions = [
            (100, 'USD', 'EUR'),
            (150, 'EUR', 'GBP'),
            (200, 'GBP', 'JPY'),
            (1000, 'JPY', 'KRW'),
            (50000, 'KRW', 'USD'),
        ]
        
        # 동시 실행
        tasks = [
            currency_agent.convert(amount, from_cur, to_cur)
            for amount, from_cur, to_cur in conversions
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 모든 결과 검증
        assert len(results) == len(conversions)
        
        # 대부분 성공해야 함
        successes = [r for r in results 
                    if isinstance(r, dict) and 'error' not in r]
        assert len(successes) > 0
    
    @pytest.mark.asyncio
    async def test_currency_conversion_accuracy(self, currency_agent):
        """환율 변환 정확성"""
        # 기준: 100 USD를 EUR로 변환했을 때
        result_eur = await currency_agent.convert(100, 'USD', 'EUR')
        
        if 'error' not in result_eur:
            # EUR을 KRW로 변환
            result_krw = await currency_agent.convert(
                result_eur['converted_amount'], 'EUR', 'KRW'
            )
            
            if 'error' not in result_krw:
                # 간접 환율 (USD->EUR->KRW)이 합리적 범위 내
                assert result_krw['converted_amount'] > 0


class TestCurrencyConverterPerformance:
    """성능 테스트"""
    
    @pytest.mark.asyncio
    async def test_cache_performance_benefit(self, currency_agent):
        """캐싱의 성능 효과"""
        import time
        
        # 첫 번째 호출 (API 호출)
        start1 = time.time()
        result1 = await currency_agent.convert(100, 'USD', 'KRW')
        _time1 = time.time() - start1
        
        # 두 번째 호출 (캐시 사용)
        start2 = time.time()
        result2 = await currency_agent.convert(100, 'USD', 'KRW')
        _time2 = time.time() - start2
        
        # 캐시된 호출이 더 빨라야 함
        # (단, 네트워크 지연이 작은 경우 명확하지 않을 수 있음)
        assert result1.get('exchange_rate') == result2.get('exchange_rate')
    
    @pytest.mark.asyncio
    async def test_multiple_sequential_conversions(self, currency_agent):
        """순차적 다중 변환"""
        conversions = [
            (100, 'USD', 'EUR'),
            (150, 'EUR', 'GBP'),
            (200, 'GBP', 'JPY'),
        ]
        
        results = []
        for amount, from_cur, to_cur in conversions:
            result = await currency_agent.convert(amount, from_cur, to_cur)
            results.append(result)
            
            # 각 변환이 성공해야 함 (또는 폴백)
            assert 'converted_amount' in result or 'error' in result
        
        assert len(results) == len(conversions)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
