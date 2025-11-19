# 🚀 AgenticTravelRAG Quick Start Guide

## 📋 프로젝트 개요
**AgenticTravelRAG**는 TripAdvisor 리뷰 데이터를 기반으로 사용자가 자연어로 여행 요구사항을 질문하면 관련 호텔과 액티비티를 찾아주고 맞춤형 여행 일정을 제안하는 Agentic RAG 기반 지능형 여행 플래너입니다.

## 🎯 팀원별 작업 가이드

### 1️⃣ 프로젝트 시작하기

```bash
# 저장소 클론
git clone https://github.com/YOUR_TEAM/AgenticTravelRAG.git
cd AgenticTravelRAG

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp config/.env.example .env
# .env 파일을 열어 필요한 API 키 입력
```

### 2️⃣ 역할별 작업 폴더

#### 🔧 **백엔드 개발자**
- **작업 폴더**: `src/core/`, `src/api/`
- **주요 파일**:
  - `src/core/workflow.py` - LangGraph 워크플로우
  - `src/core/state.py` - 상태 관리
- **할 일**:
  - FastAPI 엔드포인트 구현 (`src/api/main.py`)
  - 워크플로우 최적화

#### 🤖 **AI/ML 엔지니어**
- **작업 폴더**: `src/agents/`, `src/rag/`
- **주요 파일**:
  - `src/agents/*.py` - 각종 에이전트
  - `src/rag/elasticsearch_rag.py` - RAG 파이프라인
- **할 일**:
  - 에이전트 성능 개선
  - 임베딩 모델 최적화
  - 프롬프트 엔지니어링

#### 📊 **데이터 엔지니어**
- **작업 폴더**: `data/scripts/`
- **할 일**:
  - TripAdvisor 데이터 ETL 파이프라인 구축
  - ElasticSearch 인덱싱 스크립트 작성
  - 데이터 전처리 최적화

#### 🎨 **프론트엔드 개발자**
- **작업 폴더**: `src/ui/`
- **할 일**:
  - Streamlit UI 개발 (`src/ui/app.py`)
  - 사용자 인터페이스 개선
  - 대화형 챗봇 UI 구현

### 3️⃣ 개발 워크플로우

```bash
# 1. 최신 코드 가져오기
git checkout develop
git pull origin develop

# 2. 기능 브랜치 생성
git checkout -b feature/기능명

# 3. 개발 작업
# ... 코드 작성 ...

# 4. 테스트 실행
pytest tests/

# 5. 커밋
git add .
git commit -m "feat: 기능 설명"

# 6. 푸시 및 PR 생성
git push origin feature/기능명
# GitHub에서 PR 생성 → develop 브랜치로
```

### 4️⃣ ElasticSearch 설정

```bash
# Docker로 ElasticSearch 실행
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  docker.elastic.co/elasticsearch/elasticsearch:8.11.0

# 연결 확인
curl http://localhost:9200
```

### 5️⃣ 데이터 준비

```python
# data/scripts/download_data.py 생성
from datasets import load_dataset

# TripAdvisor 데이터셋 로드
dataset = load_dataset("jniimi/tripadvisor-review-rating")
dataset.save_to_disk("data/raw/tripadvisor")
```

### 6️⃣ 애플리케이션 실행

```bash
# API 서버 실행 (터미널 1)
cd src/api
uvicorn main:app --reload --port 8000

# Streamlit UI 실행 (터미널 2)
streamlit run src/ui/app.py

# 접속
# API: http://localhost:8000/docs
# UI: http://localhost:8501
```

## 📁 핵심 파일 설명

| 파일 | 설명 | 담당자 |
|------|------|--------|
| `src/core/workflow.py` | LangGraph 메인 워크플로우 | 백엔드 |
| `src/core/state.py` | AppState 정의 및 관리 | 백엔드 |
| `src/agents/query_parser.py` | 사용자 쿼리 파싱 | AI/ML |
| `src/agents/hotel_rag.py` | 호텔 RAG 검색 | AI/ML |
| `src/agents/weather_tool.py` | 날씨 정보 조회 | AI/ML |
| `src/agents/google_search.py` | 구글 검색 | AI/ML |
| `src/agents/response_generator.py` | 최종 응답 생성 | AI/ML |
| `src/rag/elasticsearch_rag.py` | ElasticSearch RAG | 데이터 |
| `data/scripts/index_to_elastic.py` | ES 인덱싱 (생성 필요) | 데이터 |
| `src/api/main.py` | FastAPI 서버 (생성 필요) | 백엔드 |
| `src/ui/app.py` | Streamlit UI (생성 필요) | 프론트 |

## 🧪 테스트 가이드

```bash
# 전체 테스트
pytest tests/

# 특정 모듈 테스트
pytest tests/unit/test_agents.py

# 커버리지 확인
pytest --cov=src tests/
```

## 📝 커밋 메시지 규칙

```
feat: 새로운 기능
fix: 버그 수정
docs: 문서 수정
style: 코드 스타일 변경
refactor: 리팩토링
test: 테스트 추가/수정
chore: 빌드/설정 변경
```

## 🔑 필요한 API 키

| API | 용도 | 발급처 | 환경변수 |
|-----|------|--------|----------|
| OpenAI | LLM | https://platform.openai.com | `OPENAI_API_KEY` |
| SerpApi | 구글 검색 | https://serpapi.com | `SERP_API_KEY` |

## 🐛 문제 해결

### ElasticSearch 연결 오류
```bash
# ElasticSearch 상태 확인
curl http://localhost:9200/_cluster/health

# Docker 로그 확인
docker logs elasticsearch
```

### 임포트 오류
```bash
# PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:${PWD}"
```

### API 키 오류
```bash
# .env 파일 확인
cat .env

# 환경변수 로드 확인
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"
```

## 📞 팀 소통

- **코드 리뷰**: GitHub PR
- **이슈 트래킹**: GitHub Issues  
- **일반 토론**: GitHub Discussions
- **실시간 소통**: Slack/Discord (팀 채널)

## 🚀 다음 단계

1. [ ] ElasticSearch에 TripAdvisor 데이터 인덱싱
2. [ ] FastAPI 엔드포인트 구현
3. [ ] Streamlit UI 개발
4. [ ] 통합 테스트 작성
5. [ ] Docker 컨테이너화
6. [ ] CI/CD 파이프라인 구축

---

**문의사항이 있으면 GitHub Issues에 등록해주세요!** 🙏
