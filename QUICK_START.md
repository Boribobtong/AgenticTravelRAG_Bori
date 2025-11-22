# 🚀 AgenticTravelRAG Quick Start Guide

> **Google Gemini**와 **LangGraph**를 활용한 TripAdvisor 리뷰 기반 여행 플래너를 빠르게 시작하는 가이드입니다.

## 📋 프로젝트 개요

\*\*AgenticTravelRAG (A.R.T)\*\*는 사용자의 복잡한 여행 요구사항(예: "파리에서 12월에 묵을 낭만적인 호텔")을 이해하고, TripAdvisor 리뷰 데이터와 실시간 정보(날씨, 검색)를 결합하여 최적의 여행 일정을 제안하는 지능형 에이전트 시스템입니다.

-----

## 🏁 10분 안에 시작하기 (For Developers)

### 1️⃣ 환경 설정

**1. 저장소 클론**

```bash
git clone https://github.com/YOUR_TEAM/AgenticTravelRAG.git
cd AgenticTravelRAG
```

**2. 가상환경 생성 및 활성화**

```bash
# 가상환경 생성
python -m venv venv

# 활성화 (Mac/Linux)
source venv/bin/activate
# 활성화 (Windows)
venv\Scripts\activate
```

**3. 의존성 설치**

```bash
pip install -r requirements.txt
```

**4. 환경변수 설정**
`.env` 파일을 생성하고 API 키를 입력합니다.

```bash
cp config/.env.example config/.env
```

`config/.env` 파일을 열어 다음 키를 입력하세요:

  * `GOOGLE_API_KEY`: Google AI Studio에서 발급받은 Gemini API 키
  * `SERP_API_KEY` (선택): Google 검색을 위한 SerpApi 키 (없으면 모의 데이터 사용)

-----

### 2️⃣ 데이터베이스 및 데이터 준비

A.R.T는 **ElasticSearch**를 벡터 데이터베이스로 사용합니다.

**1. ElasticSearch 실행 (Docker)**

```bash
docker-compose -f docker/docker-compose.yml up -d elasticsearch
```

  * 실행 확인: 브라우저에서 `http://localhost:9200` 접속

**2. 데이터 다운로드 및 인덱싱**
TripAdvisor 리뷰 데이터를 다운로드하고, 가상의 메타데이터(도시, 호텔명)를 주입하여 인덱싱합니다.

```bash
# 데이터 다운로드
python -m data.scripts.download_data

# 데이터 인덱싱 (Embedding 생성 포함)
python -m data.scripts.index_to_elastic
```

  * 완료 시 로그: `인덱싱 완료! 총 문서 수: 5000`

-----

### 3️⃣ 서비스 실행

두 개의 터미널 창을 열어 각각 실행합니다.

**터미널 1: Backend API 서버**

```bash
uvicorn src.api.main:app --reload --port 8000
```

  * API 문서: `http://localhost:8000/docs`

**터미널 2: Frontend UI**

```bash
streamlit run src/ui/app.py
```

  * 접속 주소: `http://localhost:8501`

-----

## 🎯 팀원별 역할 가이드

### 🔧 **백엔드 개발자**

  * **주요 관심사**: LangGraph 워크플로우, 상태 관리, API 최적화
  * **핵심 파일**:
      * `src/core/workflow.py`: 에이전트 간 흐름 제어 및 라우팅 로직
      * `src/core/state.py`: AppState 데이터 구조 정의
      * `src/api/main.py`: FastAPI 엔드포인트 및 비동기 처리

### 🤖 **AI/ML 엔지니어**

  * **주요 관심사**: 프롬프트 엔지니어링, RAG 성능 개선, 모델 튜닝
  * **핵심 파일**:
      * `src/agents/query_parser.py`: 사용자 의도 파악 및 JSON 추출 (Gemini 2.5 Flash)
      * `src/agents/response_generator.py`: 최종 응답 생성 및 페르소나 설정 (Gemini 2.5 Pro)
      * `src/rag/elasticsearch_rag.py`: 하이브리드 검색(BM25 + Vector) 로직

### 📊 **데이터 엔지니어**

  * **주요 관심사**: 데이터 파이프라인, 벡터 DB 관리, 인덱싱 효율화
  * **핵심 파일**:
      * `data/scripts/index_to_elastic.py`: 데이터 전처리 및 메타데이터 주입 로직
      * `docker/docker-compose.yml`: ElasticSearch 컨테이너 설정

### 🎨 **프론트엔드 개발자**

  * **주요 관심사**: 사용자 경험(UX), Streamlit UI 커스터마이징
  * **핵심 파일**:
      * `src/ui/app.py`: Streamlit 대시보드 구성 및 API 연동

-----

## 🧪 테스트 실행 방법

안정적인 개발을 위해 테스트 코드가 준비되어 있습니다.

**단위 테스트 (Unit Test)**
개별 에이전트의 동작을 Mock 객체로 검증합니다.

```bash
python -m pytest tests/unit/test_agents.py
```

**통합 테스트 (Integration Test)**
전체 워크플로우의 흐름과 상태 전이를 검증합니다.

```bash
python -m pytest tests/integration/test_workflow.py
```

-----

## 🐛 자주 발생하는 문제 (Troubleshooting)

### Q1. ElasticSearch 연결 오류 (`ConnectionRefused` 등)

  * **해결**: `.env` 파일의 `ES_HOST`가 `localhost`로 설정되어 있는지 확인하세요. (Docker 내부 통신용 `elasticsearch`로 설정되어 있으면 로컬 실행 시 실패합니다.)
  * **확인**: `curl http://localhost:9200` 명령어로 응답이 오는지 확인하세요.

### Q2. Gemini API 오류 (`404 Not Found`)

  * **해결**: 사용 중인 Gemini 모델(`gemini-1.5-pro` 등)이 만료되었을 수 있습니다. `src/agents/*.py` 파일에서 모델명을 최신 버전(`gemini-2.5-flash` 등)으로 변경하세요.

### Q3. 날씨 정보가 안 나와요

  * **해결**: 날짜 정보가 없으면 날씨 조회를 건너뜁니다. 질문에 구체적인 날짜(예: "12월 25일부터")를 포함해 보세요. 또한, 너무 먼 미래(14일 이후)의 날씨는 조회되지 않습니다.

-----

**Happy Coding\!** ✈️