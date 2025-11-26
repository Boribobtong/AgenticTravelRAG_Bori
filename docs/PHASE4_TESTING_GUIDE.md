# Phase 4 기능 테스트 가이드

이 가이드는 구현된 Phase 4 기능들을 테스트하는 방법을 안내합니다.

## 🚀 빠른 시작

### 1. 통합 테스트 스크립트 실행

```bash
cd /Users/hyeonseong/workspace/AgenticTravelRAG
python examples/test_phase4_features.py
```

이 스크립트는 다음을 테스트합니다:
- ✅ A/B 테스팅 프레임워크
- ✅ 만족도 추적 시스템
- ✅ 메트릭 수집 시스템
- ✅ 자동 재학습 파이프라인

---

## 📋 개별 기능 테스트

### 1. A/B 테스팅 프레임워크

```bash
# 단위 테스트 실행
pytest tests/unit/test_ab_testing.py -v

# 예상 출력:
# ✓ 11 passed
```

**수동 테스트:**
```python
from src.tools.ab_testing import ABTestingManager

ab_manager = ABTestingManager()

# 실험 생성
ab_manager.create_experiment(
    name="my_experiment",
    description="내 실험",
    variants=[
        {"name": "control", "config": {"alpha": 0.5}},
        {"name": "treatment", "config": {"alpha": 0.7}}
    ]
)

# 실험 시작
ab_manager.start_experiment("my_experiment")

# 사용자에게 변형 할당
variant = ab_manager.assign_variant("my_experiment", "user_123")
print(f"할당된 변형: {variant}")
```

---

### 2. 만족도 추적 시스템

```bash
# 단위 테스트 실행
pytest tests/unit/test_satisfaction_tracker.py -v

# 예상 출력:
# ✓ 12 passed
```

**수동 테스트:**
```python
from src.tools.satisfaction_tracker import SatisfactionTracker

tracker = SatisfactionTracker()

# 명시적 피드백 기록
tracker.record_explicit_feedback(
    session_id="session_123",
    feedback_type="thumbs_up"
)

# 암묵적 신호 기록
tracker.record_implicit_signals(
    session_id="session_123",
    signals={
        'conversation_turns': 4,
        'search_refinements': 0,
        'hotels_viewed': 3,
        'weather_available': True,
        'time_to_completion': 5.0
    }
)

# 만족도 점수 계산
score = tracker.calculate_satisfaction_score("session_123")
print(f"만족도 점수: {score}/100")
```

---

### 3. 성능 모니터링 대시보드

```bash
# Prometheus + Grafana 시작
docker-compose -f docker-compose.monitoring.yml up -d

# Streamlit 대시보드 실행
streamlit run src/tools/monitoring_dashboard.py
```

**접속:**
- Streamlit 대시보드: http://localhost:8501
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

**단위 테스트:**
```bash
pytest tests/unit/test_metrics_collector.py -v

# 예상 출력:
# ✓ 8 passed
```

---

### 4. 자동 재학습 파이프라인

```bash
# 단위 테스트 실행
pytest tests/unit/test_retraining_pipeline.py -v

# 예상 출력:
# ✓ 8 passed
```

**수동 테스트:**
```python
from src.tools.retraining_pipeline import RetrainingPipeline

pipeline = RetrainingPipeline()

# 재학습 트리거 확인
triggers = pipeline.check_retraining_triggers()
print(f"트리거 상태: {triggers}")

# 재학습 필요 여부
if pipeline.should_retrain():
    print("재학습이 필요합니다!")
    result = await pipeline.execute_retraining()
    print(f"재학습 결과: {result}")
```

---

## 🧪 전체 테스트 실행

```bash
# Phase 4 전체 테스트
pytest tests/unit/test_ab_testing.py \
       tests/unit/test_satisfaction_tracker.py \
       tests/unit/test_metrics_collector.py \
       tests/unit/test_retraining_pipeline.py \
       -v

# 예상 출력:
# ✓ 39 passed (11 + 12 + 8 + 8)
```

---

## 📊 모니터링 대시보드 사용법

### 1. Docker 스택 시작

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2. 대시보드 접속

**Streamlit 대시보드:**
```bash
streamlit run src/tools/monitoring_dashboard.py
```
- URL: http://localhost:8501
- 실시간 메트릭 시각화
- 응답 시간, 검색 품질, 에러율, 만족도 차트

**Prometheus:**
- URL: http://localhost:9090
- PromQL 쿼리 실행
- 메트릭 원시 데이터 확인

**Grafana:**
- URL: http://localhost:3000
- 로그인: admin / admin
- 대시보드 생성 및 커스터마이징

### 3. 종료

```bash
docker-compose -f docker-compose.monitoring.yml down
```

---

## 🔍 데이터 확인

### A/B 테스트 데이터

```bash
# SQLite 데이터베이스 확인
sqlite3 data/ab_tests.db

# 실험 목록
SELECT * FROM experiments;

# 변형 할당 현황
SELECT variant_name, COUNT(*) as count 
FROM assignments 
GROUP BY variant_name;
```

### 만족도 데이터

```bash
# SQLite 데이터베이스 확인
sqlite3 data/satisfaction.db

# 만족도 점수
SELECT session_id, score, calculated_at 
FROM satisfaction_scores 
ORDER BY calculated_at DESC 
LIMIT 10;
```

### 재학습 데이터

```bash
# SQLite 데이터베이스 확인
sqlite3 data/quality_monitor.db

# 최근 쿼리
SELECT destination, COUNT(*) as count 
FROM query_stats 
GROUP BY destination 
ORDER BY count DESC;
```

---

## 🐛 문제 해결

### 1. 모듈 import 오류

```bash
# PYTHONPATH 설정
export PYTHONPATH=/Users/hyeonseong/workspace/AgenticTravelRAG:$PYTHONPATH
```

### 2. Docker 포트 충돌

```bash
# 사용 중인 포트 확인
lsof -i :9090  # Prometheus
lsof -i :3000  # Grafana
lsof -i :8501  # Streamlit

# 프로세스 종료
kill -9 <PID>
```

### 3. 데이터베이스 초기화

```bash
# 기존 데이터 삭제 (주의!)
rm -f data/ab_tests.db
rm -f data/satisfaction.db
rm -f data/quality_monitor.db
```

---

## 📝 다음 단계

1. **실제 워크플로우와 통합 테스트**
   ```bash
   # 전체 시스템 테스트
   pytest tests/integration/test_workflow.py -v
   ```

2. **프로덕션 배포 준비**
   - API 서버에 `/metrics` 엔드포인트 추가
   - Prometheus 스크래핑 설정
   - Grafana 대시보드 구성

3. **실제 데이터 수집**
   - 사용자 피드백 수집 시작
   - A/B 테스트 실험 실행
   - 성능 메트릭 모니터링

---

**작성일:** 2025-11-27  
**버전:** 1.0
