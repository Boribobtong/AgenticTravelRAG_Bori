"""
SafetyInfoAgent 테스트
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.safety_info import SafetyInfoAgent


async def test_safety_info():
    """SafetyInfoAgent 테스트"""
    agent = SafetyInfoAgent()
    
    # 테스트 도시들
    test_locations = ["Paris", "Tokyo", "London", "Seoul"]
    
    for location in test_locations:
        print(f"\n{'='*60}")
        print(f"🔍 {location} 안전 정보 조회 중...")
        print(f"{'='*60}\n")
        
        safety_info = await agent.get_safety_info(location)
        
        if safety_info:
            formatted = agent.format_safety_info(safety_info)
            print(formatted)
        else:
            print(f"❌ {location}의 안전 정보를 조회할 수 없습니다.\n")


if __name__ == "__main__":
    asyncio.run(test_safety_info())
