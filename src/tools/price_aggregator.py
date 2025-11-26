"""
PriceAggregator: lightweight interface and mock adapters for Phase3 PoC.

This module provides a small abstraction over multiple price providers. It
contains a MockProvider that returns deterministic, test-friendly prices so
we can unit-test integration without external API calls.
"""
from typing import Dict, Any, List


class PriceProvider:
    """Abstract provider interface."""
    async def get_price(self, hotel_name: str, dates: List[str]) -> Dict[str, Any]:
        raise NotImplementedError()


class MockPriceProvider(PriceProvider):
    """Return deterministic mock price data for testing and local dev."""
    async def get_price(self, hotel_name: str, dates: List[str]) -> Dict[str, Any]:
        nights = max(1, len(dates) - 1) if dates else 1
        base = 100
        price = base + (len(hotel_name) % 5) * 20 + nights * 10
        return {
            'hotel_name': hotel_name,
            'dates': dates,
            'price': float(price),
            'currency': 'USD',
            'source': 'mock'
        }


class PriceAggregator:
    """Aggregate prices from multiple providers and return the best price.

    For Phase3 PoC this is intentionally simple: it queries providers in
    sequence and returns the minimum price result.
    """
    def __init__(self, providers: List[PriceProvider] = None):
        self.providers = providers or [MockPriceProvider()]

    async def get_best_price(self, hotel_name: str, dates: List[str]) -> Dict[str, Any]:
        best = None
        for p in self.providers:
            try:
                r = await p.get_price(hotel_name, dates)
            except Exception:
                continue
            if not best or r.get('price', float('inf')) < best.get('price', float('inf')):
                best = r
        return best or {'hotel_name': hotel_name, 'dates': dates, 'price': None}
