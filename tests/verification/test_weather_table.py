import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.agents.weather_tool import WeatherToolAgent
from src.core.state import WeatherForecast


def test_format_weather_table():
    agent = WeatherToolAgent()

    forecasts = [
        WeatherForecast(
            date="2025-11-26",
            temperature_min=3,
            temperature_max=12,
            precipitation=0,
            weather_code=0,
            description="맑음",
            recommendations=[],
            advice=""
        )
    ]

    table = agent.format_weather_table(forecasts)

    assert "| 날짜 | 날씨 | 최저기온 | 최고기온 | 강수량 |" in table
    # Temperatures may appear as integers or floats (3 or 3.0), so check for key parts
    assert "| 2025-11-26 | 맑음 |" in table
    assert "°C" in table
    assert "mm" in table
