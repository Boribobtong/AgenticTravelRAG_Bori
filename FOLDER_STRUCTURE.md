# 📁 AgenticTravelRAG 프로젝트 폴더 구조 및 파일 배치 가이드

이 문서는 프로젝트의 현재 파일 구조 현황과 배치를 설명합니다.

## 🗂️ 전체 폴더 구조 현황

범례:

  - ✅ : **현재 존재하는 파일** (구현 완료)
  - 🚧 : **생성이 필요한 파일** (초기화 또는 설정 필요)

<!-- end list -->

```text
AgenticTravelRAG/
│
├── 📄 README.md                           # ✅ 프로젝트 메인 문서
├── 📄 setup_dirs.sh                       # ✅ 폴더 생성 스크립트
├── 📄 init_git.sh                         # ✅ Git 초기화 스크립트
├── 📄 Makefile                            # ✅ 빌드 및 실행 자동화
├── 📄 requirements.txt                    # ✅ Python 의존성 패키지 목록
├── 📄 .gitignore                          # ✅ Git 제외 파일 설정
│
├── 📁 src/                                # 소스 코드 메인 폴더
│   ├── 📄 __init__.py                     # 🚧 (패키지 초기화)
│   │
│   ├── 📁 core/                           # 핵심 로직
│   │   ├── 📄 __init__.py                 # ✅ 패키지 노출 설정
│   │   ├── 📄 state.py                    # ✅ AppState 및 데이터 모델 정의
│   │   └── 📄 workflow.py                 # ✅ LangGraph 메인 워크플로우
│   │
│   ├── 📁 agents/                         # 에이전트 모듈
│   │   ├── 📄 __init__.py                 # 🚧 (패키지 초기화)
│   │   ├── 📄 query_parser.py             # ✅ 사용자 쿼리 파싱 및 구조화
│   │   ├── 📄 hotel_rag.py                # ✅ ElasticSearch 기반 호텔 검색
│   │   ├── 📄 weather_tool.py             # ✅ Open-Meteo 날씨 조회 도구
│   │   ├── 📄 google_search.py            # ✅ SerpApi 기반 구글 검색 도구
│   │   └── 📄 response_generator.py       # ✅ 최종 답변 생성 에이전트
│   │
│   ├── 📁 rag/                            # RAG 파이프라인
│   │   ├── 📄 __init__.py                 # 🚧 (패키지 초기화)
│   │   └── 📄 elasticsearch_rag.py        # ✅ ElasticSearch 하이브리드 검색 구현
│   │
│   ├── 📁 api/                            # FastAPI 서버
│   │   ├── 📄 __init__.py                 # 🚧 (패키지 초기화)
│   │   ├── 📄 main.py                     # ✅ FastAPI 메인 엔드포인트
│   │   └── 📄 routes.py                   # ✅ 추가 API 라우트 (유틸리티 등)
│   │
│   ├── 📁 ui/                             # 사용자 인터페이스
│   │   ├── 📄 __init__.py                 # 🚧 (패키지 초기화)
│   │   └── 📄 app.py                      # ✅ Streamlit 웹 애플리케이션
│   │
│   └── 📁 tools/                          # (확장용) 추가 외부 도구 폴더
│       └── 📄 __init__.py                 # 🚧 (패키지 초기화)
│
├── 📁 data/                               # 데이터 관련
│   ├── 📁 raw/                            # 원본 데이터 저장소 (Git 제외됨)
│   ├── 📁 processed/                      # 전처리된 데이터 (Git 제외됨)
│   ├── 📁 embeddings/                     # 벡터 임베딩 캐시 (Git 제외됨)
│   └── 📁 scripts/                        # ETL 및 유틸리티 스크립트
│       ├── 📄 __init__.py                 # 🚧 (패키지 초기화)
│       ├── 📄 download_data.py            # ✅ HuggingFace 데이터 다운로드
│       └── 📄 index_to_elastic.py         # ✅ ElasticSearch 데이터 인덱싱
│
├── 📁 config/                             # 설정 파일
│   ├── 📄 config.yaml                     # ✅ 애플리케이션 메인 설정
│   └── 📄 .env                            # 🚧 API 키 설정 (로컬 생성 필요)
│
├── 📁 tests/                              # 테스트 코드
│   ├── 📄 __init__.py                     # 🚧
│   ├── 📁 unit/                           # 단위 테스트
│   │   ├── 📄 test_agents.py              # ✅ 에이전트 단위 테스트
│   │   └── 📄 test_rag.py                 # ✅ RAG 파이프라인 단위 테스트
│   ├── 📁 integration/                    # 통합 테스트
│   │   └── 📄 test_workflow.py            # ✅ 워크플로우 통합 테스트
│   └── 📁 e2e/                            # End-to-End 테스트
│       └── 📄 test_complete_flow.py       # ✅ 전체 시스템 E2E 테스트
│
├── 📁 docs/                               # 문서
│   ├── 📄 QUICK_START.md                  # ✅ 빠른 시작 가이드
│   ├── 📄 SETUP_COMMANDS.md               # ✅ 설치 명령어 모음
│   ├── 📄 API_DATA_SOURCES_GUIDE.md       # ✅ 외부 API 가이드
│   ├── 📄 FOLDER_STRUCTURE.md             # ✅ 폴더 구조 설명 (본 파일)
│   ├── 📄 CONTRIBUTING.md                 # ✅ 기여 가이드
│   └── 📁 architecture/                   # 아키텍처 문서 등
│
├── 📁 docker/                             # Docker 설정
│   ├── 📄 docker-compose.yml              # ✅ Docker Compose 설정
│   └── 📁 app/                            # App 컨테이너 설정
│       └── 📄 Dockerfile                  # 🚧 (Makefile 참조 시 필요)
│
└── 📁 .github/                            # GitHub 설정
    ├── 📄 PULL_REQUEST_TEMPLATE.md        # ✅ PR 템플릿
    └── 📁 workflows/
        └── 📄 ci.yml                      # ✅ CI 파이프라인 설정
```

-----

## 🚀 초기 설정 명령어 (누락 파일 생성)

이미 핵심 로직 파일들은 구현되어 있으므로, Python 패키지 인식을 위한 `__init__.py` 파일들과 환경 변수 파일만 생성하면 됩니다.

```bash
# 1. 패키지 초기화 파일 생성
touch src/__init__.py
touch src/agents/__init__.py
touch src/rag/__init__.py
touch src/tools/__init__.py
touch src/api/__init__.py
touch src/ui/__init__.py
touch data/__init__.py
touch data/scripts/__init__.py
touch tests/__init__.py

# 2. 환경 변수 파일 생성 (config.yaml 참고하여 값 입력 필요)
cat > config/.env << 'EOF'
# OpenAI
OPENAI_API_KEY=your_openai_key_here

# SerpApi (Google Search)
SERP_API_KEY=your_serpapi_key_here

# ElasticSearch
ES_HOST=localhost
ES_PORT=9200
ES_USER=elastic
ES_PASSWORD=changeme
EOF
```

## 🐳 Docker 관련 파일 확인

`docker-compose.yml`은 존재하지만, 빌드를 위한 `Dockerfile`이 명시적으로 업로드되지 않았습니다. (Makefile 참조 시 `docker/app/Dockerfile` 경로 사용). 아래 내용으로 생성하는 것을 권장합니다.

**docker/app/Dockerfile**

```dockerfile
# Python 3.11 사용
FROM python:3.11-slim

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    APP_HOME=/app

WORKDIR $APP_HOME

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 실행 권한 설정 (스크립트용)
RUN chmod +x data/scripts/*.py

# 실행 포트
EXPOSE 8000

# 기본 실행 명령 (docker-compose에서 덮어씌움)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
