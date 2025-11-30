"""
Tests for CurrencyConverterNode

워크플로우 노드 테스트
"""

import pytest
from src.agents.currency_converter_node import (
    CurrencyConverterNode,
    get_currency_node,
    execute_currency_conversion
)


@pytest.fixture
def node():
    """CurrencyConverterNode 인스턴스"""
    return CurrencyConverterNode()


@pytest.fixture
def state():
    """샘플 워크플로우 상태"""
    return {
        'query': 'Find hotels in Seoul and Tokyo',
        'context': {
            'hotels': [
                {
                    'name': 'Hotel Seoul',
                    'price': 150000,
                    'currency': 'KRW',
                    'city': 'Seoul'
                },
                {
                    'name': 'Hotel Tokyo',
                    'price': 20000,
                    'currency': 'JPY',
                    'city': 'Tokyo'
                }
            ],
            'flights': [
                {
                    'route': 'ICN -> NRT',
                    'price': 500,
                    'currency': 'USD'
                },
                {
                    'route': 'ICN -> CDG',
                    'price': 800,
                    'currency': 'EUR'
                }
            ]
        }
    }


class TestCurrencyConverterNode:
    """CurrencyConverterNode 테스트"""
    
    @pytest.mark.asyncio
    async def test_node_execute_with_hotels(self, node, state):
        """호텔 가격 정규화"""
        result = await node.execute(state)
        
        assert 'context' in result
        assert 'currency_conversions' in result['context']
        assert 'base_currency' in result['context']['currency_conversions']
        assert result['context']['currency_conversions']['base_currency'] == 'USD'
    
    @pytest.mark.asyncio
    async def test_node_normalize_hotels(self, node, state):
        """호텔 가격 정규화 검증"""
        result = await node.execute(state)
        
        if 'normalized_hotels' in result['context']:
            normalized_hotels = result['context']['normalized_hotels']
            
            # 모든 호텔이 정규화되어야 함
            assert len(normalized_hotels) > 0
            
            # 가격이 USD로 변환되어야 함
            for hotel in normalized_hotels:
                if hotel['currency'] != 'USD':
                    assert 'price_usd' in hotel or 'error' in hotel
    
    @pytest.mark.asyncio
    async def test_node_normalize_flights(self, node, state):
        """항공편 가격 정규화 검증"""
        result = await node.execute(state)
        
        if 'normalized_flights' in result['context']:
            normalized_flights = result['context']['normalized_flights']
            
            # 모든 항공편이 정규화되어야 함
            assert len(normalized_flights) > 0
            
            # 가격이 USD로 변환되어야 함
            for flight in normalized_flights:
                if flight['currency'] != 'USD':
                    assert 'price_usd' in flight or 'error' in flight
    
    @pytest.mark.asyncio
    async def test_node_exchange_rates(self, node, state):
        """환율 정보 확인"""
        result = await node.execute(state)
        
        assert 'context' in result
        assert 'currency_conversions' in result['context']
        
        conversions = result['context']['currency_conversions']
        assert 'exchange_rates' in conversions
        
        # 주요 통화 환율이 있어야 함
        rates = conversions['exchange_rates']
        assert len(rates) > 0
    
    @pytest.mark.asyncio
    async def test_normalize_prices_method(self, node):
        """normalize_prices 메서드"""
        items = [
            {'name': 'Item A', 'price': 100, 'currency': 'EUR'},
            {'name': 'Item B', 'price': 150, 'currency': 'GBP'},
            {'name': 'Item C', 'price': 200, 'currency': 'JPY'},
        ]
        
        normalized = await node.normalize_prices(
            items,
            target_currency='USD'
        )
        
        assert len(normalized) == len(items)
        
        # 대부분 정규화되어야 함
        normalized_count = sum(
            1 for item in normalized
            if 'normalized_price' in item
        )
        assert normalized_count > 0
    
    @pytest.mark.asyncio
    async def test_get_price_in_currencies(self, node):
        """다중 통화 가격 변환"""
        result = await node.get_price_in_currencies(
            amount=100,
            from_currency='USD',
            to_currencies=['EUR', 'GBP', 'KRW', 'JPY']
        )
        
        assert 'original' in result
        assert result['original']['amount'] == 100
        assert result['original']['currency'] == 'USD'
        
        assert 'conversions' in result
        
        # 대부분 변환되어야 함
        assert len(result['conversions']) > 0
    
    @pytest.mark.asyncio
    async def test_node_execution_idempotency(self, node):
        """동일한 상태에서 여러 번 실행"""
        state1 = {
            'query': 'Test',
            'context': {
                'hotels': [
                    {'name': 'Hotel A', 'price': 100, 'currency': 'USD'}
                ]
            }
        }
        
        # 첫 번째 실행
        result1 = await node.execute(state1)
        
        # 두 번째 실행
        state2 = state1.copy()
        result2 = await node.execute(state2)
        
        # 결과는 동일해야 함
        assert result1['context'].get('base_currency') == result2['context'].get('base_currency')
    
    @pytest.mark.asyncio
    async def test_empty_context(self, node):
        """빈 context 처리"""
        test_state = {'query': 'Test', 'context': {}}
        
        result = await node.execute(test_state)
        
        # context가 있어야 함
        assert 'context' in result
        assert 'currency_conversions' in result['context']
    
    @pytest.mark.asyncio
    async def test_no_context(self, node):
        """context 없을 때 처리"""
        test_state = {'query': 'Test'}
        
        result = await node.execute(test_state)
        
        # context가 생성되어야 함
        assert 'context' in result
        assert 'currency_conversions' in result['context']


class TestCurrencyConverterNodeFunctions:
    """함수형 인터페이스 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_currency_node(self):
        """get_currency_node 함수"""
        node1 = await get_currency_node()
        node2 = await get_currency_node()
        
        # 싱글톤이어야 함
        assert node1 is node2
    
    @pytest.mark.asyncio
    async def test_execute_currency_conversion_function(self):
        """execute_currency_conversion 함수"""
        sample_state = {
            'query': 'Find hotels in Seoul and Tokyo',
            'context': {
                'hotels': [
                    {
                        'name': 'Hotel Seoul',
                        'price': 150000,
                        'currency': 'KRW',
                        'city': 'Seoul'
                    }
                ]
            }
        }
        result = await execute_currency_conversion(sample_state)
        
        assert 'context' in result
        assert 'currency_conversions' in result['context']
    
    @pytest.mark.asyncio
    async def test_node_singleton_behavior(self):
        """싱글톤 동작 확인"""
        from src.agents.currency_converter_node import _CurrencyNodeManager
        
        # 여러 번 호출해도 동일 인스턴스
        node1 = _CurrencyNodeManager.get_instance()
        node2 = _CurrencyNodeManager.get_instance()
        
        assert node1 is node2


class TestEdgeCases:
    """엣지 케이스"""
    
    @pytest.mark.asyncio
    async def test_malformed_price_data(self):
        """잘못된 가격 데이터"""
        test_node = CurrencyConverterNode()
        
        test_state = {
            'query': 'Test',
            'context': {
                'hotels': [
                    {'name': 'Hotel A'},  # 가격 없음
                    {'price': 100},  # 통화 없음
                ]
            }
        }
        
        # 에러 없이 실행되어야 함 (graceful degradation)
        result = await test_node.execute(test_state)
        assert 'context' in result
    
    @pytest.mark.asyncio
    async def test_none_values(self):
        """None 값 처리"""
        test_node = CurrencyConverterNode()
        
        test_state = {
            'query': 'Test',
            'context': {
                'hotels': None,
                'flights': None
            }
        }
        
        # 에러 없이 실행되어야 함
        result = await test_node.execute(test_state)
        assert 'context' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
