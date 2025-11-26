import os
import sys
import asyncio
from datetime import datetime, timedelta
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.agents.weather_tool import WeatherToolAgent, _AIOHTTP_AVAILABLE


@pytest.mark.integration
@pytest.mark.asyncio
async def test_weather_get_forecast_live():
    """Integration test: call Open-Meteo via WeatherToolAgent and verify parsing."""
    if not _AIOHTTP_AVAILABLE:
        pytest.skip("aiohttp not available; skip integration test")

    agent = WeatherToolAgent()

    start = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    forecasts = await agent.get_forecast("Seoul", [start, end])

    # Basic assertions about returned structure
    assert isinstance(forecasts, list)
    assert len(forecasts) >= 1
    f = forecasts[0]
    assert hasattr(f, 'date') and hasattr(f, 'temperature_min')
    # description should be a short Korean label (no degree symbol)
    assert '°' not in f.description
