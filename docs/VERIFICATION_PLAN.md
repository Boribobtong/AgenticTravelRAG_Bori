# Weather Agent 고도화 및 Phase 1 검증 계획

> **검증 대상:** Weather Agent 고도화 + Phase 1 Quick Wins  
> **검증자:** Agent Verification 전문가  
> **작성일:** 2025-11-26

---

## 📋 검증 개요

### 검증 목표
PR에 포함된 모든 변경사항이 의도대로 동작하고, 기존 기능을 손상시키지 않으며, 사용자 경험을 개선하는지 확인합니다.

### 검증 범위
1. Weather Agent 고도화 (날씨 설명, 테이블 형식, 2주 제한)
2. CLI 스크립트 기능
3. 검색 Fallback 로직
4. 문서 품질 및 정확성

---

## 검증 브랜치

검증 작업은 `verification/phase1` 브랜치에서 수행됩니다. 이 브랜치는 `feature/weather-agent-enhancement` 브랜치에서 분기하여 검증 관련 테스트 및 CI 구성을 포함합니다.


## 🎯 검증 단계

### Phase 1: 환경 설정 및 사전 점검

#### 1.1 의존성 확인
- [ ] Python 패키지 설치 확인
- [ ] ElasticSearch 실행 확인
- [ ] 환경 변수 설정 확인 (`config/.env`)

**검증 방법:**
```bash
# 의존성 확인
pip list | grep -E "langchain|elasticsearch|sentence-transformers"

# ElasticSearch 확인
curl -u elastic:changeme http://localhost:9200

# 환경 변수 확인
cat config/.env | grep -E "GOOGLE_API_KEY|SERP_API_KEY"
```

**예상 결과:**
- 모든 필수 패키지 설치됨
- ElasticSearch 정상 응답 (200 OK)
- API 키 설정됨

---

### Phase 2: Weather Agent 기능 검증

#### 2.1 날씨 설명 개선 검증

**테스트 케이스:**
1. 다양한 WMO Weather Code에 대한 한국어 매핑 확인
2. 주관적 표현 제거 확인
3. 객관적 상태 표시 확인

**검증 방법:**
```python
# tests/verification/test_weather_description.py
from src.agents.weather_tool import WeatherToolAgent

agent = WeatherToolAgent()

# 테스트: 맑음
assert agent._get_weather_description(0) == "맑음"

# 테스트: 흐림
assert agent._get_weather_description(3) == "흐림"

# 테스트: 비
assert agent._get_weather_description(63) == "비"

# 테스트: 눈
assert agent._get_weather_description(73) == "눈"
```

**예상 결과:**
- 모든 WMO 코드가 명확한 한국어로 매핑됨
- "기분 좋은 날씨" 같은 표현 없음

#### 2.2 테이블 형식 출력 검증

**테스트 케이스:**
1. 날씨 데이터가 Markdown 테이블로 포맷팅되는지 확인
2. 테이블에 필수 컬럼(날짜, 날씨, 기온, 강수량) 포함 확인

**검증 방법:**
```python
# tests/verification/test_weather_table.py
from src.agents.weather_tool import WeatherToolAgent
from src.core.state import WeatherForecast

agent = WeatherToolAgent()

# Mock 데이터
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

# 검증
assert "| 날짜 | 날씨 | 최저기온 | 최고기온 | 강수량 |" in table
assert "| 2025-11-26 | 맑음 | 3°C | 12°C | 0mm |" in table
```

**예상 결과:**
- 테이블 헤더와 데이터가 올바르게 포맷팅됨

#### 2.3 2주 제한 안내 검증

**테스트 케이스:**
1. 2주 이후 날짜 요청 시 빈 배열 반환 확인
2. context_memory에 제한 메시지 저장 확인

**검증 방법:**
```python
# tests/verification/test_weather_limitation.py
from src.agents.weather_tool import WeatherToolAgent
from datetime import datetime, timedelta

agent = WeatherToolAgent()

# 2주 이후 날짜
future_date = (datetime.now() + timedelta(days=20)).strftime("%Y-%m-%d")
dates = [future_date, future_date]

# 검증
forecasts = await agent.get_forecast("Paris", dates)
assert forecasts == []  # 빈 배열 반환
```

**예상 결과:**
- 2주 이후 날짜는 빈 배열 반환
- Workflow에서 안내 메시지 처리

---

### Phase 3: CLI 스크립트 검증

#### 3.1 기본 실행 검증

**테스트 케이스:**
1. `--help` 옵션 동작 확인
2. `--interactive` 모드 실행 확인
3. `--query` 단일 쿼리 모드 확인

**검증 방법:**
```bash
# Help 확인
python scripts/run_agent.py --help

# Interactive 모드 (수동 테스트)
python scripts/run_agent.py --interactive

# Single query 모드
python scripts/run_agent.py --query "파리 호텔 추천해줘"
```

**예상 결과:**
- Help 메시지 정상 출력
- Interactive 모드 정상 실행
- Single query 모드 응답 생성

#### 3.2 환경 변수 로드 검증

**테스트 케이스:**
1. `config/.env` 파일 자동 로드 확인
2. API 키 정상 로드 확인

**검증 방법:**
```bash
# 환경 변수 없이 실행 (실패해야 함)
unset GOOGLE_API_KEY
python scripts/run_agent.py --query "test"

# .env 파일 있을 때 실행 (성공해야 함)
python scripts/run_agent.py --query "test"
```

**예상 결과:**
- `.env` 파일에서 API 키 자동 로드
- "✅ 환경 변수 로드 완료" 메시지 출력

---

### Phase 4: 검색 Fallback 로직 검증

#### 4.1 Fallback 메서드 존재 확인

**테스트 케이스:**
1. `search_with_fallback()` 메서드 존재 확인
2. `HotelOption.search_note` 필드 존재 확인

**검증 방법:**
```python
# tests/verification/test_fallback_exists.py
from src.agents.hotel_rag import HotelRAGAgent
from src.core.state import HotelOption

# 메서드 존재 확인
agent = HotelRAGAgent()
assert hasattr(agent, 'search_with_fallback')

# 필드 존재 확인
from pydantic import BaseModel
assert 'search_note' in HotelOption.__fields__
```

**예상 결과:**
- 메서드와 필드 모두 존재

#### 4.2 Fallback 로직 동작 검증

**테스트 케이스:**
1. 1차 검색 성공 시 결과 반환
2. 1차 실패, 2차 성공 시 완화 메시지 포함
3. 모두 실패 시 빈 배열 반환

**검증 방법:**
```python
# tests/verification/test_fallback_logic.py
from src.agents.hotel_rag import HotelRAGAgent

agent = HotelRAGAgent()

# 테스트 1: 정상 검색
params = {
    'destination': 'Paris',
    'preferences': {'atmosphere': ['romantic']}
}
results = await agent.search_with_fallback(params)
assert len(results) > 0

# 테스트 2: 조건 완화 (Mock 필요)
# 실제 구현 시 ElasticSearch Mock 사용
```

**예상 결과:**
- Fallback 로직이 단계별로 동작

---

### Phase 5: 통합 테스트

#### 5.1 End-to-End 테스트

**테스트 케이스:**
1. 전체 워크플로우 실행
2. 날씨 정보 포함 응답 생성
3. 검색 결과 포함 응답 생성

**검증 방법:**
```bash
# E2E 테스트
python scripts/run_agent.py --query "파리에서 12월 15일부터 3박 4일 묵을 낭만적인 호텔 추천해줘"
```

**예상 결과:**
- 호텔 추천 포함
- 날씨 테이블 포함
- 여행 일정 포함

#### 5.2 성능 테스트

**테스트 케이스:**
1. 응답 시간 측정 (목표: 10초 이내)
2. 메모리 사용량 확인

**검증 방법:**
```python
# tests/verification/test_performance.py
import time
from src.core.workflow import ARTWorkflow

workflow = ARTWorkflow()

start = time.time()
result = await workflow.run("파리 호텔 추천")
end = time.time()

response_time = end - start
assert response_time < 10.0, f"응답 시간 초과: {response_time}초"
```

**예상 결과:**
- 응답 시간 10초 이내

---

### Phase 6: 문서 검증

#### 6.1 문서 정확성 확인

**테스트 케이스:**
1. README.md CLI 사용법 정확성
2. QUICK_START.md 가이드 정확성
3. SYSTEM_ANALYSIS_AND_IMPROVEMENTS.md 내용 검토

**검증 방법:**
- 수동 검토
- 문서에 명시된 명령어 실제 실행

**예상 결과:**
- 모든 명령어 정상 실행
- 설명과 실제 동작 일치

#### 6.2 코드 주석 및 Docstring 확인

**테스트 케이스:**
1. 새로 추가된 메서드에 Docstring 존재
2. 복잡한 로직에 주석 존재

**검증 방법:**
```bash
# Docstring 확인
grep -r "def search_with_fallback" src/agents/hotel_rag.py -A 10
```

**예상 결과:**
- 모든 public 메서드에 Docstring 존재

---

## 📊 검증 결과 기록

### 검증 체크리스트

#### Phase 1: 환경 설정
- [ ] 의존성 확인
- [ ] ElasticSearch 실행 확인
- [ ] 환경 변수 설정 확인

#### Phase 2: Weather Agent
- [ ] 날씨 설명 개선 검증
- [ ] 테이블 형식 출력 검증
- [ ] 2주 제한 안내 검증

#### Phase 3: CLI 스크립트
- [ ] 기본 실행 검증
- [ ] 환경 변수 로드 검증

#### Phase 4: 검색 Fallback
- [ ] Fallback 메서드 존재 확인
- [ ] Fallback 로직 동작 검증

#### Phase 5: 통합 테스트
- [ ] End-to-End 테스트
- [ ] 성능 테스트

#### Phase 6: 문서 검증
- [ ] 문서 정확성 확인
- [ ] 코드 주석 확인

---

## 🐛 발견된 이슈

### Critical Issues
_검증 중 발견된 치명적 이슈 기록_

### Minor Issues
_검증 중 발견된 경미한 이슈 기록_

### Suggestions
_개선 제안 사항 기록_

---

## ✅ 검증 완료 기준

다음 조건을 모두 만족해야 검증 완료:
1. 모든 Phase의 테스트 케이스 통과
2. Critical Issue 0건
3. 문서와 실제 동작 일치
4. 성능 기준 충족 (응답 시간 10초 이내)

---

**검증 시작일:** 2025-11-26  
**검증 완료일:** TBD  
**검증자:** Agent Verification 전문가

## Todo
Proceed with Option B: Update the CI workflow to run weather integration tests in cassette mode and separate the heavy ES tests.

Please modify `.github/workflows/verification.yml` (or create a new one) to implement a split testing strategy:

1. **Job 1: Fast Tests (Required)**
   - Installs dependencies (including `pytest-vcr`).
   - Runs standard Unit Tests AND the Weather Integration Test (using the recorded cassette).
   - Does NOT require Docker/Elasticsearch.
   - Command: `pytest -m "not integration or vcr"` (adjust markers so VCR tests run here).

2. **Job 2: Heavy Integration Tests (Optional/Conditional)**
   - Spins up the Elasticsearch service container.
   - Runs the heavy RAG integration tests (Docker-dependent).
   - This job should trigger on PRs or Manual Dispatch, but shouldn't block the "Fast Tests" from giving quick feedback.

Goal: Ensure that I get quick feedback on logic and API parsing (via VCR) without waiting for Docker spin-up every time.