import os
import json
import requests
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv
import sys
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm  # 진행률 표시 라이브러리 (pip install tqdm)

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.rag.elasticsearch_rag import get_rag_instance, ReviewDocument

load_dotenv("config/.env")

DATA_DIR = Path("data/raw")
INPUT_FILE = DATA_DIR / "tripadvisor_reviews.jsonl"

# ---------------------------------------------------------
# 1. 헬퍼 함수들은 그대로 유지 (병렬 처리를 위해 최상위 레벨에 위치해야 함)
# ---------------------------------------------------------
def parse_hotel_info_from_url(url):
    try:
        if 'Reviews-' not in url:
            return "Unknown Hotel", "Unknown Location"
        slug = url.split('Reviews-')[1].replace('.html', '')
        if '-' in slug:
            parts = slug.split('-', 1)
            hotel_name = parts[0].replace('_', ' ')
            location = parts[1].replace('_', ' ')
        else:
            hotel_name = slug.replace('_', ' ')
            location = "Unknown"
        return hotel_name, location
    except Exception:
        return "Unknown Hotel", "Unknown Location"

def extract_tags(property_dict, text):
    tags = []
    if property_dict:
        key_map = {
            'cleanliness': 'clean',
            'service': 'good_service',
            'location': 'good_location',
            'value': 'good_value',
            'sleep quality': 'quiet',
            'rooms': 'nice_rooms'
        }
        for key, score in property_dict.items():
            if float(score) >= 4.0 and key in key_map:
                tags.append(key_map[key])

    text_lower = text.lower()
    keywords = {
        'romantic': 'romantic', 'honeymoon': 'romantic',
        'family': 'family', 'kids': 'family', 'business': 'business',
        'solo': 'solo_travel', 'pool': 'pool', 'beach': 'beach_front',
        'breakfast': 'breakfast'
    }
    for word, tag in keywords.items():
        if word in text_lower:
            tags.append(tag)
    return list(set(tags))

# ---------------------------------------------------------
# 2. 병렬 처리를 위한 단위 작업 함수 정의
# ---------------------------------------------------------
def process_single_line(line_data):
    """
    한 줄(JSON 문자열)을 받아 ReviewDocument 객체(또는 None)를 반환하는 함수
    이 함수는 각 워커 프로세스에서 실행됩니다.
    """
    try:
        # tuple (idx, line_string) 형태로 받음
        idx, line = line_data
        item = json.loads(line)
        
        hotel_name, location = parse_hotel_info_from_url(item.get('hotel_url', ''))
        tags = extract_tags(item.get('property_dict', {}), item.get('text', ''))

        doc = ReviewDocument(
            doc_id=f"review_{idx}",
            hotel_name=hotel_name,
            location=location,
            review_text=item.get('text', ''),
            rating=float(item.get('rating', 0)),
            review_title=item.get('title', ''),
            tags=tags,
            reviewer_location=item.get('author', '')
        )
        return doc
    except Exception:
        return None

# ---------------------------------------------------------
# 3. 메인 인덱싱 로직 개선
# ---------------------------------------------------------
def index_data():
    print("\n" + "="*60)
    print("🚀 ElasticSearch 대용량 병렬 인덱싱 (Optimized)")
    print("="*60 + "\n")
    
    rag = get_rag_instance()
    
    # 인덱스 초기화
    rag.create_index(force_recreate=True)
    
    if not INPUT_FILE.exists():
        print(f"❌ 데이터 파일 없음: {INPUT_FILE}")
        return

    # 설정값 조정
    BATCH_SIZE = 5000  # 배치 크기 증가 (500 -> 5000)
    MAX_WORKERS = max(1, os.cpu_count() - 1)  # CPU 코어 수 활용 (하나 남겨둠)

    print(f"⚙️  설정: Batch Size={BATCH_SIZE}, Workers={MAX_WORKERS}")
    
    # 전체 라인 수 계산 (tqdm 진행률 표시용, 100만개면 약간 시간 걸림)
    print("📊 전체 라인 수 계산 중...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        total_lines = sum(1 for _ in f)
    
    documents_batch = []
    
    # ProcessPoolExecutor를 사용하여 병렬 처리
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        # 인덱스와 라인을 튜플로 묶어서 generator 생성
        lines_gen = ((i, line) for i, line in enumerate(f))
        
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # tqdm으로 진행상황 표시
            results = tqdm(
                executor.map(process_single_line, lines_gen), 
                total=total_lines,
                unit="docs",
                desc="Processing & Indexing"
            )
            
            for doc in results:
                if doc:
                    documents_batch.append(doc)
                
                # 배치가 차면 인덱싱 실행 (메인 프로세스에서 수행)
                if len(documents_batch) >= BATCH_SIZE:
                    # [수정] use_dummy_embedding=True 옵션 추가 (속도 최적화 모드)
                    # 실제 임베딩 모델 사용 시 use_dummy_embedding=False로 변경
                    rag.index_documents(documents_batch, batch_size=BATCH_SIZE, use_dummy_embedding=False)
                    documents_batch = [] # 비우기

    # 남은 문서 처리
    if documents_batch:
        # [수정] use_dummy_embedding=True 옵션 추가
        # 실제 임베딩 모델 사용 시 use_dummy_embedding=False로 변경
        rag.index_documents(documents_batch, batch_size=BATCH_SIZE, use_dummy_embedding=False)
    
    print(f"\n✅ 인덱싱 완료!")

if __name__ == "__main__":
    # Windows/Mac 환경의 Multiprocessing 보호를 위해 필수
    index_data()