# Data Scripts

이 디렉토리에는 TripAdvisor 리뷰 데이터를 다운로드하고 ElasticSearch에 인덱싱하는 스크립트가 포함되어 있습니다.

## 📁 파일 구조

```
data/scripts/
├── download_data.py          # Python 다운로드 모듈
├── download_data.sh           # Mac/Linux 실행 스크립트
├── download_data.bat          # Windows 실행 스크립트
├── index_to_elastic.py        # Python 인덱싱 모듈
├── index_to_elastic.sh        # Mac/Linux 실행 스크립트
├── index_to_elastic.bat       # Windows 실행 스크립트
└── README.md                  # 이 파일
```

## 🚀 사용 방법

### 1단계: 데이터 다운로드

**Mac/Linux:**
```bash
./data/scripts/download_data.sh
```

**Windows:**
```cmd
data\scripts\download_data.bat
```

**또는 Python 직접 실행:**
```bash
python -m data.scripts.download_data
```

### 2단계: ElasticSearch 인덱싱

**사전 요구사항:** ElasticSearch가 실행 중이어야 합니다.
```bash
docker-compose -f docker/docker-compose.yml up -d elasticsearch
```

**Mac/Linux:**
```bash
./data/scripts/index_to_elastic.sh
```

**Windows:**
```cmd
data\scripts\index_to_elastic.bat
```

**또는 Python 직접 실행:**
```bash
python -m data.scripts.index_to_elastic
```

## ⚙️ 설정

스크립트는 `config/config.yaml`의 설정을 사용합니다:
- `huggingface_dataset`: 다운로드할 데이터셋 이름
- `raw_dir`: 원본 데이터 저장 경로
- `max_docs_for_dev`: 개발 환경에서 사용할 최대 문서 수

## 📊 출력

- **다운로드**: `data/raw/tripadvisor_reviews.jsonl`
- **인덱싱**: ElasticSearch `hotel_reviews` 인덱스에 저장

## 🔍 문제 해결

### ElasticSearch 연결 실패
```bash
# ElasticSearch 상태 확인
curl http://localhost:9200

# ElasticSearch 재시작
docker-compose -f docker/docker-compose.yml restart elasticsearch
```

### 데이터 파일이 이미 존재
다운로드 스크립트는 기존 파일이 있으면 건너뜁니다. 재다운로드하려면:
```bash
rm data/raw/tripadvisor_reviews.jsonl
```

### 인덱스 재생성
인덱싱 스크립트는 기본적으로 기존 인덱스를 삭제하고 재생성합니다.
