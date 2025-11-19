"""
ElasticSearch 인덱싱 스크립트

1. ElasticSearchRAG 인스턴스를 사용하여 인덱스 생성.
2. raw 데이터를 로드하고 전처리 (Embedding 생성 포함).
3. ElasticSearch에 문서들을 인덱싱.
"""

import os
import json
import yaml
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# 프로젝트 루트를 Python Path에 추가 (모듈 임포트용)
import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.rag.elasticsearch_rag import get_rag_instance, ReviewDocument

# 환경 변수 및 설정 로드
load_dotenv()
try:
    with open("config/config.yaml", 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    logger.error("config/config.yaml 파일을 찾을 수 없습니다. 설정을 확인하세요.")
    exit(1)

ES_CONFIG = config.get('elasticsearch', {})
DATA_CONFIG = config.get('data', {})
RAW_DIR = Path(DATA_CONFIG.get('raw_dir'))
INPUT_FILE = RAW_DIR / "tripadvisor_reviews.jsonl"


def load_raw_data() -> list[dict]:
    """저장된 raw JSONL 데이터를 로드"""
    if not INPUT_FILE.exists():
        logger.error(f"원본 데이터 파일이 없습니다: {INPUT_FILE}. download_data.py를 먼저 실행하세요.")
        return []

    data = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.warning(f"JSON 디코딩 오류: {e} in line: {line.strip()[:50]}...")
    
    return data

def index_data():
    """데이터를 로드하고 ElasticSearch에 인덱싱"""
    
    logger.info("데이터 인덱싱 시작...")
    
    # 1. RAG 인스턴스 초기화 및 인덱스 생성
    # get_rag_instance()는 환경변수를 읽어 ES에 연결합니다.
    rag = get_rag_instance()
    rag.create_index(force_recreate=True)
    
    # 2. 데이터 로드
    raw_data = load_raw_data()
    if not raw_data:
        logger.error("로드할 데이터가 없습니다. 인덱싱 중단.")
        return
        
    logger.info(f"로드된 문서 수: {len(raw_data)}")
    
    # 3. 문서 형식으로 변환 (Embedding 생성 준비)
    documents = []
    for idx, item in enumerate(raw_data):
        try:
            # elasticsearch_rag.py의 ReviewDocument 스키마에 맞게 조정
            doc = ReviewDocument(
                doc_id=f"tripadvisor_{idx}",
                hotel_name=item.get('hotel_name', f"Hotel_{idx}"),
                location=item.get('location', 'Unknown'),
                review_text=item.get('text', item.get('review', '')),
                rating=float(item.get('rating', 0)),
                review_title=item.get('title', None),
                # tags 추출은 ElasticSearchRAG._extract_tags에서 하거나,
                # 여기서는 간단히 스킵하고 인덱싱 메소드에 맡깁니다.
                tags=[] # 태그는 RAG 클래스 내부에서 추출하는 것으로 가정
            )
            documents.append(doc)
        except Exception as e:
            logger.warning(f"문서 변환 실패 (idx={idx}): {str(e)}")
            continue

    # 4. 인덱싱 실행
    rag.index_documents(documents)
    
    # 5. 상태 확인
    doc_count = rag.es.count(index=rag.index_name)['count']
    logger.success(f"인덱싱 완료! 총 인덱스된 문서 수: {doc_count}")

if __name__ == "__main__":
    index_data()