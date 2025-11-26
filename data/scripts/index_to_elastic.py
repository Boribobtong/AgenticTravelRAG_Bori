"""
ElasticSearch 인덱싱 스크립트 (메타데이터 보강 버전)

문제 해결: 원본 데이터에 호텔 위치/이름이 없으므로, 
각 hotel_id에 랜덤하게 인기 도시와 가상의 호텔 이름을 부여하여 인덱싱합니다.

사용법:
    python -m data.scripts.index_to_elastic
    또는
    python data/scripts/index_to_elastic.py
"""

import os
import json
import random
import requests
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# 프로젝트 루트를 Python Path에 추가
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.rag.elasticsearch_rag import get_rag_instance, ReviewDocument

# 환경 변수 로드
load_dotenv("config/.env")

DATA_DIR = Path("data/raw")
INPUT_FILE = DATA_DIR / "tripadvisor_reviews.jsonl"

# ==========================================
# 🌍 가상 메타데이터 생성기
# ==========================================
CITIES = ["Paris", "New York", "Seoul", "Bangkok", "London", "Tokyo", "Barcelona", "Rome"]
HOTEL_TYPES = ["Grand Hotel", "Resort & Spa", "Boutique Stay", "Guesthouse", "Plaza", "Inn"]
ADJECTIVES = ["Luxury", "Cozy", "Modern", "Historic", "Royal", "City"]

class MetadataGenerator:
    def __init__(self):
        self.hotel_map = {}  # hotel_id -> (name, location) 매핑

    def get_metadata(self, hotel_id: int):
        """호텔 ID별로 일관된 가상 이름/위치 반환"""
        if hotel_id not in self.hotel_map:
            city = random.choice(CITIES)
            name = f"{random.choice(ADJECTIVES)} {city} {random.choice(HOTEL_TYPES)}"
            self.hotel_map[hotel_id] = {"name": name, "location": city}
        return self.hotel_map[hotel_id]

# ==========================================

def check_elasticsearch_connection():
    """ElasticSearch 연결 상태 확인"""
    es_host = os.getenv("ES_HOST", "localhost")
    es_port = os.getenv("ES_PORT", "9200")
    es_url = f"http://{es_host}:{es_port}"
    
    try:
        response = requests.get(es_url, timeout=5)
        if response.status_code == 200:
            return True, es_url
        return False, es_url
    except requests.exceptions.RequestException:
        return False, es_url

def load_raw_data():
    if not INPUT_FILE.exists():
        logger.error(f"데이터 파일이 없습니다: {INPUT_FILE}")
        return []
    
    data = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except:
                continue
    return data

def index_data():
    print("\n" + "="*60)
    print("📊 ElasticSearch 인덱싱 시작")
    print("="*60 + "\n")
    
    # ElasticSearch 연결 확인
    print("🔍 ElasticSearch 연결 확인 중...")
    is_connected, es_url = check_elasticsearch_connection()
    
    if not is_connected:
        print(f"❌ ElasticSearch에 연결할 수 없습니다: {es_url}")
        print("\n다음 명령어로 ElasticSearch를 시작하세요:")
        print("  docker-compose -f docker/docker-compose.yml up -d elasticsearch")
        print("\n연결 확인:")
        print(f"  curl {es_url}\n")
        print("="*60 + "\n")
        return
    
    print(f"✅ ElasticSearch 연결 성공: {es_url}\n")
    
    logger.info("데이터 인덱싱 시작 (메타데이터 보강 포함)...")
    
    rag = get_rag_instance()
    print("🗑️  기존 인덱스 삭제 및 재생성 중...")
    rag.create_index(force_recreate=True)
    
    raw_data = load_raw_data()
    if not raw_data:
        print("❌ 데이터 파일이 없거나 비어있습니다.")
        print(f"   먼저 데이터를 다운로드하세요:")
        print(f"   python -m data.scripts.download_data\n")
        print("="*60 + "\n")
        return

    # 메타데이터 생성기 초기화
    meta_gen = MetadataGenerator()
    documents = []
    
    logger.info(f"총 {len(raw_data)}개 리뷰 처리 중...")
    print(f"📦 총 {len(raw_data):,}개 리뷰 처리 중...")

    for idx, item in enumerate(raw_data):
        try:
            # 호텔 ID 기반으로 가상 정보 생성
            hotel_id = item.get('hotel_id')
            meta = meta_gen.get_metadata(hotel_id)
            
            # 텍스트에서 태그 추출 (간단한 키워드 매칭)
            text = item.get('text', '').lower()
            tags = []
            if 'wifi' in text: tags.append('wifi')
            if 'breakfast' in text: tags.append('breakfast')
            if 'pool' in text: tags.append('pool')
            if 'quiet' in text: tags.append('quiet')
            if 'family' in text: tags.append('family')
            if 'romantic' in text: tags.append('romantic')

            doc = ReviewDocument(
                doc_id=f"review_{idx}",
                hotel_name=meta['name'],      # 가상 호텔 이름
                location=meta['location'],    # 가상 위치 (Paris, Seoul 등)
                review_text=item.get('text', ''),
                rating=float(item.get('overall', item.get('rating', 0))),
                review_title=item.get('title', ''),
                tags=tags
            )
            documents.append(doc)
            
        except Exception as e:
            continue

    # 인덱싱 실행 (배치 처리)
    print("💾 ElasticSearch에 인덱싱 중...")
    rag.index_documents(documents, batch_size=500)
    
    doc_count = rag.es.count(index=rag.index_name)['count']
    logger.success(f"인덱싱 완료! 총 문서 수: {doc_count}")
    
    print(f"\n✅ 인덱싱 완료!")
    print(f"   인덱스: {rag.index_name}")
    print(f"   문서 수: {doc_count:,}개")
    print(f"\n💡 이제 'Paris', 'Seoul' 등으로 검색이 가능합니다.\n")
    print("="*60 + "\n")

if __name__ == "__main__":
    index_data()