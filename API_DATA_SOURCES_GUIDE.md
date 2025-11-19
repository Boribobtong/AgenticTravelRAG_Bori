# 📊 여행 계획 RAG 시스템 - API 데이터 소스 상세 가이드

## 🌟 추천 API 조합

### 기본 구성 (무료/저비용)
1. **OpenWeatherMap** - 날씨 (무료 1,000 calls/일)
2. **Amadeus Self-Service** - 항공/호텔 (무료 테스트)
3. **Google Places** - 장소 정보 ($200 무료 크레딧/월)
4. **OpenAI GPT-3.5** - LLM (저렴한 가격)

### 프리미엄 구성 (상용)
1. **Tomorrow.io** - 고급 날씨 예측
2. **Amadeus Enterprise** - 실시간 예약
3. **TripAdvisor API** - 리뷰/평점
4. **OpenAI GPT-4** - 고급 LLM

---

## 🌤️ 날씨 API 상세

### 1. OpenWeatherMap ⭐ 추천
```python
# API 엔드포인트
BASE_URL = "https://api.openweathermap.org/data/2.5"

# 주요 엔드포인트
- /weather - 현재 날씨
- /forecast - 5일 예보 (3시간 간격)
- /onecall - 종합 날씨 정보 (유료)

# 무료 플랜 제한
- 60 calls/minute
- 1,000,000 calls/month

# 예제 코드
import requests

def get_weather(city, api_key):
    url = f"{BASE_URL}/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
        "lang": "ko"  # 한국어 지원
    }
    response = requests.get(url, params=params)
    return response.json()
```

### 2. Tomorrow.io (구 ClimaCell)
```python
# 특징
- 하이퍼로컬 예보 (1km 격자)
- AI 기반 예측
- 실시간 날씨 알림

# API 엔드포인트
BASE_URL = "https://api.tomorrow.io/v4"

# 주요 기능
- /timelines - 시간대별 예보
- /realtime - 실시간 날씨
- /insights - AI 기반 인사이트

# 가격
- Core: $0/월 (500 calls/일)
- Advanced: $475/월 (10,000 calls/일)
```

### 3. Visual Crossing
```python
# 특징
- 50년 과거 날씨 데이터
- 배치 처리 지원
- CSV/JSON 포맷

# 무료 플랜
- 1,000 records/일
- 과거 데이터 접근

# 유료 플랜
- $35/월부터
- 100,000 records/월
```

---

## ✈️ 항공/호텔 API 상세

### 1. Amadeus API ⭐ 추천
```python
# 인증 과정
from amadeus import Client

amadeus = Client(
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_CLIENT_SECRET'
)

# 주요 API
# 1. Flight Offers Search
response = amadeus.shopping.flight_offers_search.get(
    originLocationCode='ICN',
    destinationLocationCode='BKK',
    departureDate='2024-05-15',
    adults=2
)

# 2. Hotel Search
response = amadeus.shopping.hotel_offers.get(
    cityCode='BKK',
    checkInDate='2024-05-15',
    checkOutDate='2024-05-20'
)

# 3. AI 기반 추천
response = amadeus.shopping.flight_destinations.get(
    origin='ICN',
    departureDate='2024-05-15',
    oneWay=False,
    viewBy='DESTINATION'
)

# 무료 테스트 환경
- 모든 API 접근 가능
- 실제 예약 불가
- 데이터 제한적

# 프로덕션 환경
- 실시간 데이터
- 실제 예약 가능
- 사용량 기반 과금
```

### 2. Skyscanner API
```python
# 특징
- 메타서치 엔진
- 전 세계 항공사 커버
- 가격 알림 기능

# 주요 엔드포인트
- /flights/search - 항공편 검색
- /hotels/search - 호텔 검색
- /carhire/search - 렌터카 검색

# 파트너십 필요
- B2B 전용
- 승인 프로세스 필요
```

### 3. Booking.com API
```python
# 접근 방법
- Affiliate Partner Program 가입 필요
- 승인까지 2-4주 소요

# 주요 기능
- 실시간 가용성
- 동적 가격
- 2,800,000+ 숙소

# Commission
- 예약당 3-5% 수수료
```

---

## 🗺️ 장소/지도 API 상세

### 1. Google Places API ⭐ 추천
```python
import googlemaps

gmaps = googlemaps.Client(key='YOUR_API_KEY')

# 장소 검색
places = gmaps.places_nearby(
    location=(13.7563, 100.5018),  # Bangkok coordinates
    radius=5000,
    type='tourist_attraction'
)

# 장소 상세 정보
place_details = gmaps.place(
    place_id='ChIJ82ENKDJgHTERIEjiXbIAAQE'
)

# 사진 가져오기
photo_reference = places['results'][0]['photos'][0]['photo_reference']
photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={API_KEY}"

# 가격
- $200 무료 크레딧/월
- Places API: $17/1000 requests
- Geocoding: $5/1000 requests
```

### 2. TripAdvisor Content API
```python
# 특징
- 7억개+ 리뷰
- 8백만+ 숙소/레스토랑/관광지
- 평점 및 순위

# 제한사항
- 소비자 대면 여행 웹사이트만
- 상업적 사용 제한
- 승인 프로세스 필요

# 주요 API
- Location Search
- Location Details
- Reviews
- Photos
```

### 3. Foursquare Places API
```python
# 특징
- 1억+ POI 데이터
- 실시간 인기도
- 체크인 데이터

# 무료 플랜
- 99,500 calls/월
- Rate limit: 500/시간

# 예제
import requests

url = "https://api.foursquare.com/v3/places/search"
headers = {
    "Accept": "application/json",
    "Authorization": API_KEY
}
params = {
    "near": "Bangkok,TH",
    "categories": "13065",  # Restaurants
    "limit": 10
}
response = requests.get(url, params=params, headers=headers)
```

---

## 💱 보조 API

### 1. 환율 API
```python
# ExchangeRate-API
url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD"
response = requests.get(url)
rates = response.json()['conversion_rates']
```

### 2. 번역 API
```python
# Google Translate
from googletrans import Translator

translator = Translator()
result = translator.translate('Hello', dest='ko')
print(result.text)  # 안녕하세요
```

### 3. 시간대 API
```python
# WorldTimeAPI (무료, API 키 불필요)
url = "http://worldtimeapi.org/api/timezone/Asia/Bangkok"
response = requests.get(url)
time_info = response.json()
```

---

## 🔧 통합 예제

### 완전한 여행 정보 수집 예제
```python
import os
from datetime import datetime
import requests
from amadeus import Client

class TravelDataCollector:
    def __init__(self):
        self.weather_key = os.getenv('OPENWEATHER_API_KEY')
        self.google_key = os.getenv('GOOGLE_API_KEY')
        self.amadeus = Client(
            client_id=os.getenv('AMADEUS_CLIENT_ID'),
            client_secret=os.getenv('AMADEUS_CLIENT_SECRET')
        )
    
    def get_complete_travel_info(self, destination, dates):
        """통합 여행 정보 수집"""
        
        # 1. 날씨 정보
        weather = self.get_weather(destination)
        
        # 2. 항공편 정보
        flights = self.search_flights(
            origin="ICN",
            destination=destination,
            date=dates['departure']
        )
        
        # 3. 호텔 정보
        hotels = self.search_hotels(
            city=destination,
            checkin=dates['checkin'],
            checkout=dates['checkout']
        )
        
        # 4. 관광지 정보
        attractions = self.find_attractions(destination)
        
        # 5. 레스토랑 정보
        restaurants = self.find_restaurants(destination)
        
        return {
            'weather': weather,
            'flights': flights,
            'hotels': hotels,
            'attractions': attractions,
            'restaurants': restaurants,
            'generated_at': datetime.now().isoformat()
        }
    
    def get_weather(self, city):
        """OpenWeatherMap API"""
        url = f"https://api.openweathermap.org/data/2.5/forecast"
        params = {
            'q': city,
            'appid': self.weather_key,
            'units': 'metric'
        }
        response = requests.get(url, params=params)
        return response.json()
    
    def search_flights(self, origin, destination, date):
        """Amadeus Flight API"""
        try:
            response = self.amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=date,
                adults=2,
                max=5
            )
            return response.data
        except Exception as e:
            return {'error': str(e)}
    
    def search_hotels(self, city, checkin, checkout):
        """Amadeus Hotel API"""
        try:
            # Get city code first
            city_search = self.amadeus.reference_data.locations.get(
                keyword=city,
                subType='CITY'
            )
            
            if city_search.data:
                city_code = city_search.data[0]['iataCode']
                
                # Search hotels
                response = self.amadeus.shopping.hotel_offers.get(
                    cityCode=city_code,
                    checkInDate=checkin,
                    checkOutDate=checkout,
                    adults=2,
                    radius=5,
                    radiusUnit='KM',
                    bestRateOnly=True
                )
                return response.data
        except Exception as e:
            return {'error': str(e)}
    
    def find_attractions(self, city):
        """Google Places API"""
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            'query': f'tourist attractions in {city}',
            'key': self.google_key
        }
        response = requests.get(url, params=params)
        return response.json()
    
    def find_restaurants(self, city):
        """Google Places API"""
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            'query': f'best restaurants in {city}',
            'key': self.google_key
        }
        response = requests.get(url, params=params)
        return response.json()

# 사용 예제
if __name__ == "__main__":
    collector = TravelDataCollector()
    
    travel_info = collector.get_complete_travel_info(
        destination="BKK",  # Bangkok
        dates={
            'departure': '2024-05-15',
            'checkin': '2024-05-15',
            'checkout': '2024-05-20'
        }
    )
    
    print("수집된 여행 정보:")
    print(f"- 날씨 예보: {len(travel_info['weather'].get('list', []))} 시간대")
    print(f"- 항공편: {len(travel_info['flights'])} 개 옵션")
    print(f"- 호텔: {len(travel_info['hotels'])} 개 추천")
    print(f"- 관광지: {len(travel_info['attractions'].get('results', []))} 개")
    print(f"- 레스토랑: {len(travel_info['restaurants'].get('results', []))} 개")
```

---

## 📈 API 선택 가이드

### 프로젝트 규모별 추천

#### 개인/학습 프로젝트
- **날씨**: OpenWeatherMap (무료)
- **장소**: Google Places ($200 크레딧)
- **LLM**: GPT-3.5-turbo
- **예상 비용**: $0-10/월

#### 스타트업/MVP
- **날씨**: Tomorrow.io (Core)
- **항공/호텔**: Amadeus Self-Service
- **장소**: Google Places + Foursquare
- **LLM**: GPT-4 + Claude
- **예상 비용**: $50-200/월

#### 기업/프로덕션
- **날씨**: Tomorrow.io (Enterprise)
- **항공/호텔**: Amadeus Enterprise + 직접 계약
- **장소**: Google Places + TripAdvisor
- **LLM**: OpenAI Enterprise + Fine-tuning
- **예상 비용**: $500+/월

---

## 🚀 Quick Start 체크리스트

### 1단계: 기본 API 등록 (30분)
- [ ] OpenWeatherMap 가입 및 API 키 발급
- [ ] OpenAI API 키 발급
- [ ] Google Cloud Console 계정 생성

### 2단계: 개발 환경 설정 (20분)
- [ ] Python 가상환경 생성
- [ ] requirements.txt 설치
- [ ] .env 파일 설정

### 3단계: 테스트 (10분)
- [ ] 날씨 API 테스트
- [ ] LLM 연결 테스트
- [ ] 기본 에이전트 실행

### 4단계: 확장 (선택사항)
- [ ] Amadeus 테스트 환경 설정
- [ ] 벡터 DB 구축
- [ ] UI 개발

---

## 📞 지원 및 문의

각 API 제공자별 지원 채널:

- **OpenWeatherMap**: support@openweathermap.org
- **Amadeus**: developers@amadeus.com
- **Google**: https://cloud.google.com/support
- **OpenAI**: https://help.openai.com

---

마지막 업데이트: 2024년 11월
