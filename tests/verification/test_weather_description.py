import sys
import os

# Ensure repository root is on sys.path so `src` package can be imported when running tests.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.agents.weather_tool import WeatherToolAgent


def test_get_weather_description():
    agent = WeatherToolAgent()

    # These expectations follow the project's verification plan mapping.
    assert agent._get_weather_description(0) == "맑음"
    assert agent._get_weather_description(3) == "흐림"
    assert agent._get_weather_description(63) == "비"
    assert agent._get_weather_description(73) == "눈"
