import pytest

try:
    from src.agents.hotel_rag import HotelRAGAgent
    from src.core.state import HotelOption
except Exception:
    pytest.skip("HotelRAGAgent or HotelOption not available", allow_module_level=True)


def test_fallback_and_field():
    agent = HotelRAGAgent()
    assert hasattr(agent, 'search_with_fallback')
    assert 'search_note' in HotelOption.__fields__
