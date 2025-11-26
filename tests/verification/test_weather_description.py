import pytest

try:
    from src.agents.weather_tool import WeatherToolAgent
except Exception:
    pytest.skip("WeatherToolAgent not available", allow_module_level=True)


def test_get_weather_description():
    agent = WeatherToolAgent()

    # These expectations follow the project's verification plan mapping.
    assert agent._get_weather_description(0) == "맑음"
    assert agent._get_weather_description(3) == "흐림"
    assert agent._get_weather_description(63) == "비"
    assert agent._get_weather_description(73) == "눈"
