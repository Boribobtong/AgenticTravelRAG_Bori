import asyncio

from src.tools.price_aggregator import PriceAggregator, MockPriceProvider


def test_price_aggregator_mock():
    agg = PriceAggregator(providers=[MockPriceProvider()])

    async def run():
        res = await agg.get_best_price('Hotel Test', ['2025-12-15', '2025-12-17'])
        assert res is not None
        assert res['hotel_name'] == 'Hotel Test'
        assert 'price' in res and res['price'] is not None

    asyncio.get_event_loop().run_until_complete(run())
