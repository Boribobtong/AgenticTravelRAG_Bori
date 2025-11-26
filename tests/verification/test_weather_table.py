import pytest

try:
    from src.agents.weather_tool import WeatherToolAgent
    from src.core.state import WeatherForecast
except Exception:
    pytest.skip("Required modules not available", allow_module_level=True)


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
    assert "| 2025-11-26 | 맑음 | 3°C | 12°C | 0mm |" in table
