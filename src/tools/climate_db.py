"""
Simple Climate DB PoC for Phase3.

Provides `get_climate_info(location, month)` which returns a small sample of
avg temps and descriptions. This is used when weather forecasts beyond 2 weeks
are requested.
"""
from typing import Optional, Dict, Any


_CLIMATE_SAMPLE = {
    'Paris': {
        12: {'avg_temp': (3, 8), 'precipitation_mm': 50, 'description': '추운 겨울, 비/눈 가능성'}
    },
    'Seoul': {
        12: {'avg_temp': (-3, 3), 'precipitation_mm': 30, 'description': '추운 겨울, 눈 가능성'}
    }
}


def get_climate_info(location: str, month: int) -> Optional[Dict[str, Any]]:
    loc = (location or '').strip()
    if not loc or not isinstance(month, int):
        return None
    data = _CLIMATE_SAMPLE.get(loc)
    if not data:
        return None
    return data.get(month)
