# 호텔 가격 정보 개선 계획

## 📋 문제 분석

### 🔍 현재 상황 (`paris_log5.md` 피드백 기반)

**주요 문제**: 호텔 추천 결과에 **가격 정보가 제대로 표시되지 않음**

---

## 🐛 근본 원인 분석

### 1. **가격 추정 방식의 한계**

**현재 구현** (`src/agents/hotel_rag.py:_estimate_price_range`):
```python
def _estimate_price_range(self, result: Dict) -> str:
    review_text = result.get('review_snippet', '').lower()
    
    # 키워드 기반 추정
    if any(word in review_text for word in ['luxury', 'expensive', ...]):
        return "$$$$$"
    elif any(word in review_text for word in ['budget', 'cheap', ...]):
        return "$$"
    else:
        return "$$$"  # 기본값
```

**문제점**:
- ❌ **리뷰 텍스트에 가격 키워드가 없으면 항상 `$$$` 반환**
- ❌ **실제 가격이 아닌 추정치**
- ❌ **정확도 낮음** (리뷰에 가격 언급이 드문 경우)
- ❌ **사용자에게 오해 유발** (실제 가격과 다를 수 있음)

### 2. **Google Search API 가격 정보 미활용**

**현재 구현** (`src/agents/google_search.py`):
```python
async def search_hotel_prices(self, hotel_name: str, check_in: str, check_out: str):
    # SerpAPI를 통한 Google Hotels 가격 검색
    # ✓ 구현되어 있음
    # ❌ 하지만 결과가 호텔 객체에 제대로 반영되지 않음
```

**문제점**:
- ⚠️ API 호출은 하지만 **결과가 `HotelOption.price_range`에 업데이트되지 않음**
- ⚠️ `GoogleSearchResult`에만 저장되고 **최종 응답에 포함 안 됨**

### 3. **가격 정보 표시 포맷 문제**

**현재 표시 방식**:
```
가격: $$$
```

**문제점**:
- ❌ **구체적인 금액 없음**
- ❌ **`$` 기호의 의미 불명확** (1개 = $50? $100?)
- ❌ **통화 단위 없음** (USD? EUR? KRW?)

---

## ✅ 개선 방안

### 🎯 Phase 1: 즉시 개선 (Quick Fix) - **30분**

#### 1.1 가격 표시 포맷 개선

**Before**:
```
가격: $$$
```

**After**:
```
가격: $$$ (약 $150-250/박)
💡 예상 가격대입니다. 정확한 가격은 예약 사이트에서 확인하세요.
```

**구현**:
```python
# src/agents/hotel_rag.py
PRICE_RANGE_GUIDE = {
    "$": "약 $50-100/박 (저렴)",
    "$$": "약 $100-150/박 (합리적)",
    "$$$": "약 $150-250/박 (중급)",
    "$$$$": "약 $250-400/박 (고급)",
    "$$$$$": "약 $400+/박 (럭셔리)"
}

def _estimate_price_range(self, result: Dict) -> str:
    # 기존 로직...
    price_symbol = "$$$"  # 예시
    return f"{price_symbol} {PRICE_RANGE_GUIDE[price_symbol]}"
```

#### 1.2 가격 정보 부재 시 명확한 안내

```python
if not hotel.price_range or hotel.price_range == "$$$":
    hotel.price_info = "가격 정보 없음 - 예약 사이트에서 확인하세요"
```

---

### 🚀 Phase 2: 중기 개선 (API 통합) - **2-3시간**

#### 2.1 Google Hotels API 가격 정보 활용

**목표**: 이미 호출하고 있는 `search_hotel_prices` 결과를 호텔 객체에 반영

**구현 위치**: `src/core/workflow.py:google_search_node`

**Before**:
```python
# 가격 정보를 검색하지만 hotel 객체에 반영 안 함
price_info = await self.google_search.search_hotel_prices(...)
search_results.append(GoogleSearchResult(..., price_info=price_info))
```

**After**:
```python
# 가격 정보를 hotel 객체에 직접 업데이트
price_info = await self.google_search.search_hotel_prices(...)

# HotelOption 객체 업데이트
if price_info and price_info.get('avg_price'):
    hotel.actual_price = price_info['avg_price']
    hotel.price_range = self._convert_price_to_symbol(price_info['avg_price'])
    hotel.price_currency = price_info.get('currency', 'USD')
```

#### 2.2 HotelOption 데이터 클래스 확장

```python
@dataclass
class HotelOption:
    name: str
    rating: float
    price_range: str  # 기존: "$$$"
    actual_price: Optional[float] = None  # 신규: 실제 가격
    price_currency: str = "USD"  # 신규: 통화
    price_source: str = "estimated"  # 신규: "estimated" | "google_hotels" | "booking"
```

#### 2.3 응답 생성 시 실제 가격 우선 표시

```python
# src/agents/response_generator.py
def _format_hotel_results(self, hotels: List) -> str:
    for h in hotels[:3]:
        if h.actual_price:
            price_str = f"${h.actual_price:.0f}/{h.price_currency} (실시간 가격)"
        else:
            price_str = f"{h.price_range} (예상)"
```

---

### 🌟 Phase 3: 장기 개선 (실시간 가격 비교) - **1-2일**

#### 3.1 다중 가격 소스 통합

**목표**: Booking.com, Hotels.com, Expedia 등 여러 사이트 가격 비교

**구현**:
```python
# src/tools/price_aggregator.py 확장
class RealPriceProvider(PriceProvider):
    async def get_price(self, hotel_name: str, dates: List[str]):
        # Booking.com API 호출
        # Hotels.com API 호출
        # 최저가 반환
```

#### 3.2 가격 캐싱

**목표**: 동일한 호텔/날짜 조합에 대한 반복 API 호출 방지

```python
# Redis 또는 메모리 캐시 사용
@cached(ttl=3600)  # 1시간 캐시
async def get_hotel_price(hotel_name, check_in, check_out):
    ...
```

#### 3.3 가격 변동 알림

```python
# 가격이 일정 % 이상 변동 시 사용자에게 알림
if price_change > 10%:
    notify_user(f"{hotel_name} 가격이 {price_change}% 변동했습니다!")
```

---

## 🎨 기타 개선 사항

### 1. **호텔 정보 표시 개선**

#### 문제
- 호텔 이름만 표시되고 **주소/위치 정보 부족**
- **예약 링크 없음**

#### 개선안
```markdown
## 🏨 추천 숙소

### Hôtel Plaza Athénée ⭐ 4.8
- 📍 **위치**: 25 Avenue Montaigne, 8th arr., 75008 Paris
- 💰 **가격**: $450/박 (USD) - 실시간 가격
- 🔗 **예약**: [Booking.com](링크) | [Hotels.com](링크)
- 🔍 [구글에서 검색](링크)

**✨ 리뷰 하이라이트**:
- "Luxurious rooms with Eiffel Tower view"
- "Exceptional service and breakfast"
```

### 2. **날씨 정보 시각화**

#### 문제
- 테이블은 있지만 **시각적 요소 부족**

#### 개선안
```markdown
## 🌤️ 파리 날씨 예보

| 날짜 | 날씨 | 기온 | 강수 | 복장 |
|------|------|------|------|------|
| 12/01 | ☀️ 맑음 | 4-9°C | 0mm | 🧥 코트 필수 |
| 12/02 | 🌧️ 비 | 5-10°C | 4mm | ☂️ 우산 챙기세요 |
```

### 3. **일정 시간 구체화**

#### 문제
- "오전", "점심", "저녁"만 표시

#### 개선안
```markdown
### 📅 1일차: 몽마르뜨 예술 탐방

- **09:00-11:00** 🌅 사랑해 벽 & 몽마르뜨 언덕
- **11:30-13:00** 🎨 테르트르 광장 (화가들의 거리)
- **13:00-14:30** 🍽️ 점심 - 현지 비스트로
- **15:00-17:00** 🏛️ 사크레쾨르 대성당
- **19:00-21:00** 🌆 저녁 - 센 강변 산책
```

### 4. **예산 정보 추가**

```markdown
## 💰 예상 여행 경비 (1인 기준, 3박 4일)

| 항목 | 금액 | 비고 |
|------|------|------|
| 숙박 | $450 x 3박 = $1,350 | Hôtel Plaza Athénée |
| 식사 | $50 x 4일 = $200 | 1일 평균 |
| 교통 | $50 | 메트로 패스 |
| 관광 | $100 | 입장료 |
| **총계** | **$1,700** | 약 230만원 (환율 1,350원) |
```

### 5. **Google Search 결과 활용 개선**

#### 현재 문제
- Google Search 결과를 가져오지만 **활용도 낮음**

#### 개선안
```markdown
## 🔍 현지 정보

### 🍴 추천 레스토랑 (Google 검색 기반)
- **Le Jules Verne** - 에펠탑 내 미슐랭 레스토랑
- **L'Ami Jean** - 현지인 추천 비스트로

### 🎫 인기 관광지
- **루브르 박물관** - 온라인 예약 필수 (€17)
- **에펠탑** - 저녁 시간 방문 추천
```

---

## 📊 우선순위

| 순위 | 작업 | 예상 시간 | 영향도 | 난이도 |
|------|------|----------|--------|--------|
| 🥇 **1** | 가격 표시 포맷 개선 | 30분 | ⭐⭐⭐⭐⭐ | ⚡ 쉬움 |
| 🥈 **2** | Google Hotels API 통합 | 2-3시간 | ⭐⭐⭐⭐ | ⚡⚡ 중간 |
| 🥉 **3** | 호텔 정보 표시 개선 | 1시간 | ⭐⭐⭐⭐ | ⚡ 쉬움 |
| 4 | 일정 시간 구체화 | 1시간 | ⭐⭐⭐ | ⚡ 쉬움 |
| 5 | 예산 정보 추가 | 2시간 | ⭐⭐⭐ | ⚡⚡ 중간 |
| 6 | 실시간 가격 비교 | 1-2일 | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ 어려움 |

---

## 🚀 실행 계획

### Week 1: 즉시 개선
- [x] 문제 분석 완료
- [ ] Phase 1 구현 (가격 표시 포맷)
- [ ] Phase 1 테스트 및 배포

### Week 2: API 통합
- [ ] Phase 2 구현 (Google Hotels API)
- [ ] HotelOption 데이터 구조 확장
- [ ] 통합 테스트

### Week 3-4: 고도화
- [ ] Phase 3 설계 (다중 소스 통합)
- [ ] 캐싱 시스템 구현
- [ ] 성능 최적화

---

## 📝 참고 사항

### API 사용 현황
- **SerpAPI**: 월 100회 무료 (현재 사용 중)
- **Google Hotels API**: 가격 정보 제공
- **Booking.com API**: 파트너 프로그램 필요

### 데이터 소스
1. **ElasticSearch RAG**: 리뷰 기반 가격 추정 (현재)
2. **Google Hotels**: 실시간 가격 (구현 필요)
3. **Booking.com**: 예약 링크 + 가격 (향후)

---

**작성일**: 2025-11-30  
**작성자**: AI Agent  
**기반 피드백**: `logs/paris_log5.md`
