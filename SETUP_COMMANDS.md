# 🚀 AgenticTravelRAG - 실제 사용 명령어

## 🔧 로컬에서 프로젝트 시작하기

### 방법 1: 파일 다운로드 후 시작
```bash
# 1. 파일 다운로드 (Claude에서 다운로드 링크 제공된 경우)
# 또는 수동으로 파일 복사

# 2. 프로젝트 폴더로 이동
cd AgenticTravelRAG

# 3. 실행 권한 부여 (macOS/Linux)
chmod +x init_git.sh setup_dirs.sh

# 4. 폴더 구조 생성
./setup_dirs.sh

# 5. Git 초기화
./init_git.sh
```

### 방법 2: 수동으로 Git 초기화
```bash
# 1. 프로젝트 폴더 이동
cd AgenticTravelRAG

# 2. 폴더 구조 생성
bash setup_dirs.sh
# 또는 직접 생성
mkdir -p src/{agents,tools,rag,core,api,ui}
mkdir -p data/{raw,processed,scripts,embeddings}
mkdir -p config tests/{unit,integration,e2e}
mkdir -p docs/{api,guides,architecture}
mkdir -p docker/{elasticsearch,app}
mkdir -p notebooks logs

# 3. Git 초기화
git init
git branch -M main
git add .
git commit -m "feat: Initial project structure with core agents"

# 4. GitHub 연결
git remote add origin https://github.com/b8goal/AgenticTravelRAG.git
git push -u origin main
```

### 방법 3: GitHub에서 바로 시작
```bash
# 1. GitHub에서 새 레포지토리 생성 (AgenticTravelRAG)

# 2. 로컬에 클론
git clone https://github.com/b8goal/AgenticTravelRAG.git
cd AgenticTravelRAG

# 3. 파일 복사
# 생성된 모든 파일을 이 폴더에 복사

# 4. 커밋 및 푸시
git add .
git commit -m "feat: Initial project structure"
git push origin main
```

## 📂 필수 __init__.py 파일 생성
```bash
# 모든 Python 패키지 폴더에 __init__.py 생성
touch src/__init__.py
touch src/core/__init__.py
touch src/agents/__init__.py
touch src/rag/__init__.py
touch src/tools/__init__.py
touch src/api/__init__.py
touch src/ui/__init__.py
touch data/scripts/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch tests/e2e/__init__.py
```

## 🐍 Python 환경 설정
```bash
# 가상환경 생성
python -m venv venv

# 활성화 (macOS/Linux)
source venv/bin/activate

# 활성화 (Windows)
venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

## 🔑 환경변수 설정
```bash
# .env 파일 생성
cat > .env << EOF
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

## 🐳 ElasticSearch 실행
```bash
# Docker로 실행
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  docker.elastic.co/elasticsearch/elasticsearch:8.11.0

# 확인
curl http://localhost:9200
```

## 🧪 테스트 실행
```bash
# 전체 테스트
pytest tests/

# 특정 테스트
pytest tests/unit/test_agents.py -v
```

## 🎯 애플리케이션 실행
```bash
# API 서버 (개발 필요)
cd src/api
python main.py

# Streamlit UI (개발 필요)
streamlit run src/ui/app.py
```

## ⚠️ 주의사항
1. Windows에서는 `./` 대신 `bash` 명령어 사용
2. 권한 오류 시 `sudo` 사용 (Linux/macOS)
3. Python 3.9+ 필요

## 📞 문제 해결
- 파일이 없다는 오류: 전체 경로 확인
- 권한 오류: `chmod +x` 또는 `bash` 사용
- 임포트 오류: `export PYTHONPATH=$PWD:$PYTHONPATH`
