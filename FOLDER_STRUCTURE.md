# 📁 AgenticTravelRAG 프로젝트 폴더 구조 및 파일 배치 가이드

## 🗂️ 전체 폴더 구조

```
AgenticTravelRAG/
│
├── 📄 README.md                           # ✅ 생성됨 - 프로젝트 메인 문서
├── 📄 setup_dirs.sh                       # ✅ 생성됨 - 폴더 생성 스크립트
│
├── 📁 src/                                # 소스 코드 메인 폴더
│   │
│   ├── 📁 core/                          # 핵심 로직
│   │   ├── 📄 __init__.py                # (생성 필요)
│   │   ├── 📄 state.py                   # ✅ 생성됨 - AppState 정의
│   │   └── 📄 workflow.py                # ✅ 생성됨 - LangGraph 워크플로우
│   │
│   ├── 📁 agents/                        # 에이전트 모듈
│   │   ├── 📄 __init__.py                # (생성 필요)
│   │   ├── 📄 query_parser.py            # ✅ 생성됨 - 쿼리 파싱 에이전트
│   │   ├── 📄 hotel_rag.py               # ✅ 생성됨 - 호텔 RAG 에이전트
│   │   ├── 📄 weather_tool.py            # ✅ 생성됨 - 날씨 도구 에이전트
│   │   ├── 📄 google_search.py           # ✅ 생성됨 - 구글 검색 에이전트
│   │   └── 📄 response_generator.py      # ✅ 생성됨 - 응답 생성 에이전트
│   │
│   ├── 📁 rag/                           # RAG 파이프라인
│   │   ├── 📄 __init__.py                # (생성 필요)
│   │   └── 📄 elasticsearch_rag.py       # ✅ 생성됨 - ElasticSearch RAG
│   │
│   ├── 📁 tools/                         # 외부 API 도구 (추가 도구용)
│   │   ├── 📄 __init__.py                # (생성 필요)
│   │   └── 📄 (추가 도구들)
│   │
│   ├── 📁 api/                           # FastAPI 엔드포인트
│   │   ├── 📄 __init__.py                # (생성 필요)
│   │   ├── 📄 main.py                    # (생성 필요) - FastAPI 메인
│   │   └── 📄 routes.py                  # (생성 필요) - API 라우트
│   │
│   └── 📁 ui/                            # Streamlit UI
│       ├── 📄 __init__.py                # (생성 필요)
│       └── 📄 app.py                      # (생성 필요) - Streamlit 앱
│
├── 📁 data/                               # 데이터 관련
│   ├── 📁 raw/                           # 원본 TripAdvisor 데이터
│   ├── 📁 processed/                     # 전처리된 데이터
│   ├── 📁 embeddings/                    # 임베딩 벡터
│   └── 📁 scripts/                       # ETL 스크립트
│       ├── 📄 __init__.py                # (생성 필요)
│       ├── 📄 download_data.py           # (생성 필요) - 데이터 다운로드
│       ├── 📄 preprocess.py              # (생성 필요) - 전처리
│       └── 📄 index_to_elastic.py        # (생성 필요) - ES 인덱싱
│
├── 📁 config/                             # 설정 파일
│   ├── 📄 config.yaml                    # (생성 필요) - 메인 설정
│   ├── 📄 .env.example                   # (생성 필요) - 환경변수 예시
│   └── 📄 logging.yaml                   # (생성 필요) - 로깅 설정
│
├── 📁 tests/                              # 테스트 코드
│   ├── 📁 unit/                          # 단위 테스트
│   │   ├── 📄 test_agents.py             # (생성 필요)
│   │   └── 📄 test_rag.py                # (생성 필요)
│   ├── 📁 integration/                   # 통합 테스트
│   │   └── 📄 test_workflow.py           # (생성 필요)
│   └── 📁 e2e/                           # End-to-End 테스트
│       └── 📄 test_complete_flow.py      # (생성 필요)
│
├── 📁 docs/                               # 문서
│   ├── 📁 api/                           # API 문서
│   │   └── 📄 openapi.json               # (생성 필요)
│   ├── 📁 guides/                        # 가이드 문서
│   │   ├── 📄 SETUP.md                   # (생성 필요) - 설치 가이드
│   │   └── 📄 USAGE.md                   # (생성 필요) - 사용 가이드
│   └── 📁 architecture/                  # 아키텍처 문서
│       └── 📄 DESIGN.md                  # (생성 필요) - 설계 문서
│
├── 📁 docker/                             # Docker 설정
│   ├── 📁 elasticsearch/                 # ElasticSearch 설정
│   │   └── 📄 Dockerfile                 # (생성 필요)
│   ├── 📁 app/                           # 애플리케이션 설정
│   │   └── 📄 Dockerfile                 # (생성 필요)
│   └── 📄 docker-compose.yml             # (생성 필요)
│
├── 📁 notebooks/                          # Jupyter 노트북
│   ├── 📄 01_data_exploration.ipynb      # (생성 필요) - 데이터 탐색
│   ├── 📄 02_rag_testing.ipynb           # (생성 필요) - RAG 테스트
│   └── 📄 03_agent_demo.ipynb            # (생성 필요) - 에이전트 데모
│
├── 📁 logs/                               # 로그 파일 (자동 생성)
│
├── 📁 .github/                            # GitHub 설정
│   ├── 📁 workflows/                     # GitHub Actions
│   │   ├── 📄 ci.yml                     # (생성 필요) - CI 파이프라인
│   │   └── 📄 cd.yml                     # (생성 필요) - CD 파이프라인
│   └── 📄 PULL_REQUEST_TEMPLATE.md       # (생성 필요) - PR 템플릿
│
├── 📄 .gitignore                          # (생성 필요) - Git 제외 파일
├── 📄 requirements.txt                    # (생성 필요) - Python 패키지
├── 📄 Makefile                           # (생성 필요) - 빌드 자동화
├── 📄 CONTRIBUTING.md                    # (생성 필요) - 기여 가이드
└── 📄 LICENSE                            # (생성 필요) - 라이센스
```

## 🚀 폴더 생성 명령어

```bash
# 1. 프로젝트 루트로 이동
cd ART-project

# 2. 폴더 생성 스크립트 실행
chmod +x setup_dirs.sh
./setup_dirs.sh

# 3. __init__.py 파일 생성
touch src/__init__.py
touch src/core/__init__.py
touch src/agents/__init__.py
touch src/rag/__init__.py
touch src/tools/__init__.py
touch src/api/__init__.py
touch src/ui/__init__.py
touch data/scripts/__init__.py
```

## 📝 생성된 파일 이동 명령어

```bash
# 이미 생성된 파일들은 올바른 위치에 있습니다:
# ✅ /ART-project/README.md
# ✅ /ART-project/setup_dirs.sh
# ✅ /ART-project/src/core/state.py
# ✅ /ART-project/src/core/workflow.py
# ✅ /ART-project/src/agents/query_parser.py
# ✅ /ART-project/src/agents/hotel_rag.py
# ✅ /ART-project/src/agents/weather_tool.py
# ✅ /ART-project/src/agents/google_search.py
# ✅ /ART-project/src/agents/response_generator.py
# ✅ /ART-project/src/rag/elasticsearch_rag.py
```

## 🔧 추가로 생성해야 할 핵심 파일들

### 1. requirements.txt
```bash
cat > requirements.txt << 'EOF'
# Core
python-dotenv==1.0.0
pyyaml==6.0.1

# LangChain & LangGraph
langchain==0.1.0
langchain-openai==0.0.5
langgraph==0.2.0

# ElasticSearch
elasticsearch==8.11.0
sentence-transformers==2.2.2

# Data
datasets==2.14.0
pandas==2.0.3
numpy==1.24.3

# API
fastapi==0.104.1
uvicorn==0.24.0
aiohttp==3.9.0

# UI
streamlit==1.28.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1

# Logging
loguru==0.7.2
EOF
```

### 2. .env.example
```bash
cat > config/.env.example << 'EOF'
# OpenAI
OPENAI_API_KEY=your_openai_key_here

# SerpApi (Google Search)
SERP_API_KEY=your_serpapi_key_here

# ElasticSearch
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200

# Logging
LOG_LEVEL=INFO
EOF
```

### 3. docker-compose.yml
```bash
cat > docker/docker-compose.yml << 'EOF'
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  app:
    build: ./app
    ports:
      - "8000:8000"
      - "8501:8501"
    environment:
      - ELASTICSEARCH_HOST=elasticsearch
    depends_on:
      - elasticsearch
    volumes:
      - ../src:/app/src
      - ../data:/app/data

volumes:
  es_data:
EOF
```

### 4. Makefile
```bash
cat > Makefile << 'EOF'
.PHONY: help setup run test clean

help:
	@echo "Available commands:"
	@echo "  make setup    - Install dependencies and setup environment"
	@echo "  make run      - Run the application"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean cache files"

setup:
	pip install -r requirements.txt
	./setup_dirs.sh
	cp config/.env.example .env

run:
	docker-compose -f docker/docker-compose.yml up -d
	streamlit run src/ui/app.py

test:
	pytest tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
EOF
```

## 📌 팀원들을 위한 시작 가이드

```bash
# 1. 저장소 클론
git clone https://github.com/your-team/AgenticTravelRAG.git
cd AgenticTravelRAG

# 2. 환경 설정
make setup

# 3. 환경변수 설정
cp config/.env.example .env
# .env 파일 편집하여 API 키 입력

# 4. ElasticSearch 시작
docker-compose -f docker/docker-compose.yml up -d elasticsearch

# 5. 데이터 인덱싱
python data/scripts/index_to_elastic.py

# 6. 애플리케이션 실행
python src/api/main.py  # API 서버
streamlit run src/ui/app.py  # UI
```

## 🎯 각 팀원 역할별 작업 폴더

- **백엔드 개발자**: `src/core/`, `src/api/`
- **AI/ML 엔지니어**: `src/agents/`, `src/rag/`
- **데이터 엔지니어**: `data/scripts/`, ElasticSearch 설정
- **프론트엔드 개발자**: `src/ui/`
- **DevOps**: `docker/`, `.github/workflows/`
- **QA**: `tests/`
