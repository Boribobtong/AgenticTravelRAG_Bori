# 🛠️ AgenticTravelRAG - 명령어 치트시트 (Cheat Sheet)

이 문서는 개발 중 자주 사용하는 명령어들을 빠르게 찾아 복사/붙여넣기 할 수 있도록 모아둔 **치트시트**입니다. 상세한 설치 과정과 설명은 [QUICK_START.md](https://www.google.com/search?q=QUICK_START.md)를 참고하세요.

## ⚡️ 빠른 실행 (Quick Run)

### 1. 초기 설정 (First Setup)

```
# 가상환경 생성 및 활성화
python -m venv venv
# Mac/Linux
source venv/bin/activate
# Windows
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정 (.env 파일 수정 필요)
cp config/.env.example config/.env

# 데이터베이스 실행
docker-compose -f docker/docker-compose.yml up -d elasticsearch

# 데이터 준비 (순서 준수)
python -m data.scripts.download_data
python -m data.scripts.index_to_elastic

```

### 2. 서비스 실행 (Run Services)

각각 다른 터미널에서 실행하세요.

**Terminal 1: API Server**

```
uvicorn src.api.main:app --reload --port 8000

```

**Terminal 2: UI App**

```
streamlit run src/ui/app.py

```

## 🧪 테스트 및 검증 (Test & Verify)

### 테스트 코드 실행

```
# 단위 테스트 (API 호출 없이 로직 검증)
python -m pytest tests/unit/test_agents.py -v

# 통합 테스트 (전체 워크플로우 흐름 검증)
python -m pytest tests/integration/test_workflow.py -v

```

### 데이터베이스 상태 확인

```
# ElasticSearch 연결 확인
curl http://localhost:9200

# 인덱스 목록 및 상태 확인
curl http://localhost:9200/_cat/indices?v

```

### Docker 관리

```
# 실행 중인 컨테이너 확인
docker ps

# DB 초기화 (데이터 삭제 후 재시작 - 주의!)
docker-compose -f docker/docker-compose.yml down -v
docker-compose -f docker/docker-compose.yml up -d elasticsearch

```

## 📂 유틸리티 (Utilities)

### 프로젝트 구조 생성

`setup_dirs.sh` 스크립트를 사용하여 초기 폴더 구조를 생성할 수 있습니다.

```
chmod +x setup_dirs.sh
./setup_dirs.sh

```

## ⚠️ 트러블슈팅 팁 (Troubleshooting Tips)

1. **Python 실행 경로**: 모든 `python -m ...` 명령어는 반드시 프로젝트 **루트 폴더**(`AgenticTravelRAG/`)에서 실행해야 합니다.
2. **환경 변수 오류**: 로컬 실행 시 `.env` 파일의 `ES_HOST`는 반드시 `localhost`여야 합니다. (`elasticsearch`는 Docker 내부 통신용)
3. **API 키 오류**: Gemini API 호출 실패 시 `config/.env` 파일의 `GOOGLE_API_KEY`가 올바른지 확인하세요.
4. **의존성 충돌**: 패키지 에러 발생 시 `pip install -r requirements.txt`를 다시 실행하여 버전을 맞추세요.