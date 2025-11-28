# tests/manual_google_search.py
import asyncio
import os
import sys
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.google_search import GoogleSearchAgent

load_dotenv("config/.env")

async def test_search():
    print("🔍 Google Search Agent 테스트 (수정 버전 확인)...\n")
    agent = GoogleSearchAgent()
    
    # 2025년 날짜로 테스트 (실제 API 호출)
    hotel_name = "Ritz Paris"
    check_in = "2025-12-02"
    check_out = "2025-12-04"
    
    print(f"Target: {hotel_name} ({check_in} ~ {check_out})")
    
    try:
        price_result = await agent.search_hotel_prices(hotel_name, check_in, check_out)
        
        print("\n✅ [파싱 성공!]")
        print(f"호텔명: {price_result.get('hotel_name')}")
        print(f"평균 가격: ${price_result.get('avg_price'):.2f}")
        print(f"가격 옵션 수: {len(price_result.get('prices', []))}")
        
        print("\n📝 상세 옵션:")
        for price in price_result.get('prices', []):
            print(f"  - {price.get('provider')}: {price.get('price')}")
            
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    asyncio.run(test_search())