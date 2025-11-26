import pytest
from datetime import datetime, timedelta
import asyncio

try:
    from src.agents.weather_tool import WeatherToolAgent
except Exception:
    pytest.skip("WeatherToolAgent not available", allow_module_level=True)


@pytest.mark.asyncio
async def test_two_week_limit():
    agent = WeatherToolAgent()

    future_date = (datetime.now() + timedelta(days=20)).strftime("%Y-%m-%d")
    dates = [future_date, future_date]

    forecasts = await agent.get_forecast("Paris", dates)
    assert forecasts == []
