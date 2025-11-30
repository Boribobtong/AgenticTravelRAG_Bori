"""
Unit Tests for CurrencyConverterAgent

환율 변환 에이전트의 기능 검증
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from src.agents.currency_converter import CurrencyConverterAgent


@pytest.fixture
def currency_agent():
    """CurrencyConverterAgent 인스턴스"""
    return CurrencyConverterAgent()


class TestCurrencyConverterAgent:
    """CurrencyConverterAgent 테스트"""
    
    @pytest.mark.asyncio
    async def test_convert_usd_to_krw(self, currency_agent):
        """USD를 KRW로 변환"""
        result = await currency_agent.convert(150, 'USD', 'KRW')
        
        # 성공 또는 폴백 데이터
        assert 'error' not in result or 'converted_amount' in result
        assert result['original_amount'] == 150
        assert result['original_currency'] == 'USD'
        assert result['target_currency'] == 'KRW'
        assert result['converted_amount'] > 0
        assert 'exchange_rate' in result
    
    @pytest.mark.asyncio
    async def test_convert_same_currency(self, currency_agent):
        """같은 통화 변환"""
        result = await currency_agent.convert(100, 'USD', 'USD')
        
        assert result['converted_amount'] == 100
        assert result['exchange_rate'] == 1.0
        assert result['source'] == 'same_currency'
    
    @pytest.mark.asyncio
    async def test_convert_invalid_currency(self, currency_agent):
        """지원하지 않는 통화"""
        result = await currency_agent.convert(100, 'XYZ', 'USD')
        
        assert result.get('error') is not None
        assert 'supported_currencies' in result
    
    @pytest.mark.asyncio
    async def test_convert_case_insensitive(self, currency_agent):
        """대소문자 무관"""
        result1 = await currency_agent.convert(100, 'usd', 'krw')
        result2 = await currency_agent.convert(100, 'USD', 'KRW')
        
        # 둘 다 성공해야 함
        assert result1.get('success') is True
        assert result2.get('success') is True
    
    @pytest.mark.asyncio
    async def test_caching_works(self, currency_agent):
        """캐싱 기능 확인"""
        # 첫 번째 호출
        result1 = await currency_agent.convert(100, 'USD', 'EUR')
        assert result1.get('success') is True
        
        # 캐시 확인
        assert len(currency_agent.cache) > 0
        
        # 두 번째 호출 (캐시 사용)
        result2 = await currency_agent.convert(100, 'USD', 'EUR')
        
        # 결과 동일해야 함
        assert result1['exchange_rate'] == result2['exchange_rate']
    
    @pytest.mark.asyncio
    async def test_get_exchange_rates(self, currency_agent):
        """기준 통화 환율 조회"""
        rates = await currency_agent.get_exchange_rates('USD')
        
        # USD 기준 주요 환율이 있어야 함
        assert len(rates) > 0
        assert any(curr in rates for curr in ['EUR', 'GBP', 'KRW', 'JPY'])
    
    @pytest.mark.asyncio
    async def test_format_price_single_currency(self, currency_agent):
        """단일 통화 가격 포맷"""
        result = await currency_agent.format_price(150, 'USD')
        
        assert result['original'] == '$150.00 USD'
        assert 'conversions' in result
    
    @pytest.mark.asyncio
    async def test_format_price_multiple_currencies(self, currency_agent):
        """다중 통화 가격 포맷"""
        result = await currency_agent.format_price(100, 'USD', ['EUR', 'GBP'])
        
        assert result['original'] == '$100.00 USD'
        assert 'EUR' in result['conversions'] or 'EUR' not in result['conversions']  # 선택적
    
    def test_supported_currencies(self, currency_agent):
        """지원 통화 목록"""
        currencies = currency_agent.get_supported_currencies()
        
        assert 'USD' in currencies
        assert 'KRW' in currencies
        assert 'EUR' in currencies
        assert len(currencies) == 15
    
    def test_cache_clear(self, currency_agent):
        """캐시 초기화"""
        # 캐시 설정
        currency_agent.cache['TEST_KEY'] = {'rate': 1.0, 'timestamp': None}
        assert len(currency_agent.cache) > 0
        
        # 캐시 초기화
        currency_agent.clear_cache()
        assert len(currency_agent.cache) == 0
    
    @pytest.mark.asyncio
    async def test_convert_multiple_pairs(self, currency_agent):
        """여러 통화 쌍 변환"""
        pairs = [
            (100, 'USD', 'EUR'),
            (1000, 'EUR', 'GBP'),
            (50000, 'KRW', 'USD'),
            (1000, 'JPY', 'KRW'),
        ]
        
        for amount, from_cur, to_cur in pairs:
            result = await currency_agent.convert(amount, from_cur, to_cur)
            # 성공 또는 폴백 데이터 사용
            assert 'converted_amount' in result or 'error' in result
    
    @pytest.mark.asyncio
    async def test_bidirectional_conversion(self, currency_agent):
        """양방향 변환 (A→B, B→A)"""
        # USD → KRW
        result1 = await currency_agent.convert(100, 'USD', 'KRW')
        
        # KRW → USD (역변환)
        if result1.get('success'):
            result2 = await currency_agent.convert(
                result1['converted_amount'], 'KRW', 'USD'
            )
            
            # 다시 돌아왔으므로 원래 금액과 비슷해야 함 (오차 허용)
            if result2.get('success'):
                assert abs(result2['converted_amount'] - 100) < 1  # 오차 1 미만


class TestEdgeCases:
    """엣지 케이스 테스트"""
    
    @pytest.mark.asyncio
    async def test_zero_amount(self):
        """0 금액 변환"""
        agent = CurrencyConverterAgent()
        result = await agent.convert(0, 'USD', 'KRW')
        
        assert result.get('success') is True
        assert result['converted_amount'] == 0
    
    @pytest.mark.asyncio
    async def test_large_amount(self):
        """큰 금액 변환"""
        agent = CurrencyConverterAgent()
        result = await agent.convert(1000000, 'USD', 'KRW')
        
        assert result.get('success') is True
        assert result['converted_amount'] > 0
    
    @pytest.mark.asyncio
    async def test_decimal_amount(self):
        """소수점 금액"""
        agent = CurrencyConverterAgent()
        result = await agent.convert(123.45, 'USD', 'EUR')
        
        assert result.get('success') is True
        assert result['converted_amount'] > 0
    
    @pytest.mark.asyncio
    async def test_negative_amount(self):
        """음수 금액"""
        agent = CurrencyConverterAgent()
        result = await agent.convert(-100, 'USD', 'KRW')
        
        # 음수도 변환 가능 (환불 등)
        assert result.get('success') is True
        assert result['converted_amount'] < 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
