import sys
import os
from datetime import datetime, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.agents.weather_tool import WeatherToolAgent


def test_parse_dates_two_week_limit():
    agent = WeatherToolAgent()

    future_start = (datetime.now() + timedelta(days=20)).strftime("%Y-%m-%d")
    future_end = (datetime.now() + timedelta(days=25)).strftime("%Y-%m-%d")

    # 시작일이 20일 후면 None (시작일이 제한을 넘음)
    assert agent._parse_dates([future_start, future_end]) is None

    # 종료일만 초과할 경우 종료일이 최대값으로 조정되어 튜플 반환
    start = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=20)).strftime("%Y-%m-%d")
    parsed = agent._parse_dates([start, end])
    assert parsed is not None
