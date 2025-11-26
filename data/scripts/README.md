# Data Scripts

이 디렉토리에는 TripAdvisor 리뷰 데이터를 다운로드하고 ElasticSearch에 인덱싱하는 Python 스크립트가 포함되어 있습니다.

## 📁 파일 구조

```
data/scripts/
├── download_data.py          # 데이터 다운로드 스크립트
├── index_to_elastic.py        # ElasticSearch 인덱싱 스크립트
└── README.md                  # 이 파일
```

## 🚀 사용 방법

### 1단계: 데이터 다운로드

**방법 1: Python 모듈로 실행 (권장)**
```bash
python -m data.scripts.download_data
```

**방법 2: 직접 실행**
```bash
python data/scripts/download_data.py
```

### 2단계: ElasticSearch 인덱싱

**사전 요구사항:** ElasticSearch가 실행 중이어야 합니다.
```bash
docker-compose -f docker/docker-compose.yml up -d elasticsearch
```

**방법 1: Python 모듈로 실행 (권장)**
```bash
python -m data.scripts.index_to_elastic
```

**방법 2: 직접 실행**
```bash
python data/scripts/index_to_elastic.py
```

## ✨ 주요 기능

### download_data.py
- 🎨 사용자 친화적인 출력 (이모지 + 진행 상황)
- 📦 HuggingFace에서 자동 다운로드
- 💾 JSONL 형식으로 저장
- ✅ 기존 파일 감지 및 건너뛰기

### index_to_elastic.py
- 🔍 ElasticSearch 연결 자동 확인
- 🗑️ 기존 인덱스 자동 재생성
- 🏷️ 메타데이터 자동 보강 (도시, 호텔명)
- 📊 실시간 진행 상황 표시
- ✅ 인덱싱 완료 후 통계 출력

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
스크립트가 자동으로 연결을 확인하고 실패 시 해결 방법을 안내합니다.

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

## 💡 Windows/Mac/Linux 모두 호환

Python 스크립트이므로 **모든 플랫폼에서 동일하게 실행**됩니다. 별도의 `.sh`나 `.bat` 파일이 필요하지 않습니다!

