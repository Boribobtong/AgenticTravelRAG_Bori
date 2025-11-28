import asyncio
import os
import sys
import json
from dotenv import load_dotenv
import aiohttp

# 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 환경 변수 로드
load_dotenv("config/.env")

async def debug_search():
    api_key = os.getenv("SERP_API_KEY")
    if not api_key:
        print("❌ API Key가 없습니다.")
        return

    # 테스트 설정: 날짜를 2024년(또는 가까운 미래)으로 변경
    hotel_name = "Ritz Paris"
    check_in = "2025-12-02"  # 가까운 날짜
    check_out = "2025-12-04"
    
    print(f"🔍 검색 대상: {hotel_name}")
    print(f"📅 날짜: {check_in} ~ {check_out}")
    
    url = "https://serpapi.com/search.json"
    params = {
        'q': hotel_name,
        'api_key': api_key,
        'engine': 'google_hotels',
        'check_in_date': check_in,
        'check_out_date': check_out,
        'currency': 'USD',
        'hl': 'en'
    }
    
    print("\n🚀 API 호출 중...")
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            print(f"📡 상태 코드: {response.status}")
            
            if response.status == 200:
                data = await response.json()
                
                # 원본 데이터의 핵심 키 확인
                print(f"\n📦 응답 데이터 키 목록: {list(data.keys())}")
                
                # 에러 메시지가 있는지 확인
                if 'error' in data:
                    print(f"⚠️ API 에러 메시지: {data['error']}")
                
                # properties 키 확인
                if 'properties' in data:
                    props = data['properties']
                    print(f"✅ 발견된 호텔 옵션 수: {len(props)}")
                    if props:
                        print(f"   첫 번째 옵션 가격: {props[0].get('rate_per_night', {}).get('lowest')}")
                else:
                    print("❌ 'properties' 키가 응답에 없습니다. (검색 결과 없음)")
                    # 디버깅을 위해 전체 응답의 일부 출력
                    print("\n[응답 내용 일부 (Top 500 chars)]")
                    print(json.dumps(data, indent=2)[:500])
            else:
                print(f"❌ 호출 실패: {await response.text()}")

if __name__ == "__main__":
    asyncio.run(debug_search())