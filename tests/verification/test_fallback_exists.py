import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.agents.hotel_rag import HotelRAGAgent
from src.core.state import HotelOption


def test_fallback_and_field():
    agent = HotelRAGAgent()
    assert hasattr(agent, 'search_with_fallback')
    # Use model_fields if available (pydantic v2), else fallback to __fields__ (v1).
    fields = getattr(HotelOption, 'model_fields', None)
    if fields is None:
        fields = getattr(HotelOption, '__fields__', {})

    # fields may be mapping-like; ensure key presence check works
    assert 'search_note' in fields
