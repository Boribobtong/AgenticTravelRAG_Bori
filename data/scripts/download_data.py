"""
데이터 다운로드 스크립트

HuggingFace datasets 라이브러리를 사용하여 
TripAdvisor 리뷰 데이터를 다운로드하고 로컬에 저장합니다.

사용법:
    python -m data.scripts.download_data
    또는
    python data/scripts/download_data.py
"""

import os
import json
import yaml
from pathlib import Path
from datasets import load_dataset
from loguru import logger
from dotenv import load_dotenv
from pandas import Timestamp 

# 환경 변수 및 설정 로드
load_dotenv()
try:
    with open("config/config.yaml", 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    logger.error("config/config.yaml 파일을 찾을 수 없습니다. 설정을 확인하세요.")
    exit(1)

DATA_CONFIG = config.get('data', {})
DATASET_NAME = DATA_CONFIG.get('huggingface_dataset')
RAW_DIR = Path(DATA_CONFIG.get('raw_dir'))
MAX_DOCS = DATA_CONFIG.get('max_docs_for_dev')

def _jsonable(value):
    if isinstance(value, Timestamp):
        return value.isoformat()
    return value

def download_data():
    """데이터셋을 다운로드하고 JSONL 형식으로 raw 디렉토리에 저장"""
    
    print("\n" + "="*60)
    print("🔽 TripAdvisor 리뷰 데이터 다운로드")
    print("="*60 + "\n")
    
    if not DATASET_NAME:
        logger.error("HuggingFace 데이터셋 이름이 설정되지 않았습니다.")
        print("❌ 설정 오류: config/config.yaml을 확인하세요.\n")
        return

    os.makedirs(RAW_DIR, exist_ok=True)
    output_file = RAW_DIR / "tripadvisor_reviews.jsonl"

    if output_file.exists():
        logger.info(f"데이터 파일이 이미 존재합니다: {output_file}. 다운로드를 건너뜁니다.")
        print(f"ℹ️  데이터 파일이 이미 존재합니다: {output_file}")
        print("   재다운로드하려면 파일을 삭제하세요.\n")
        return

    logger.info(f"데이터셋 다운로드 시작: {DATASET_NAME}")
    print(f"📦 데이터셋: {DATASET_NAME}")
    
    try:
        # 데이터셋 로드 (train split 사용)
        print("⏳ HuggingFace에서 데이터 로드 중...")
        dataset = load_dataset(DATASET_NAME, split="train")
        
        # 개발 환경을 위해 문서 수 제한
        if MAX_DOCS and len(dataset) > MAX_DOCS:
            dataset = dataset.select(range(MAX_DOCS))
            print(f"📊 개발 모드: {MAX_DOCS}개 문서로 제한")

        # JSONL 형식으로 저장
        print(f"💾 저장 중: {output_file}")
        with open(output_file, "w", encoding="utf-8") as f:
            for item in dataset:
                clean_item = {k: _jsonable(v) for k, v in item.items()}
                f.write(json.dumps(clean_item, ensure_ascii=False) + "\n")

        logger.success(f"데이터 다운로드 및 저장 완료: {output_file} ({len(dataset)}개 문서)")
        print(f"\n✅ 다운로드 완료!")
        print(f"   파일: {output_file}")
        print(f"   문서 수: {len(dataset):,}개\n")
        print("="*60 + "\n")

    except Exception as e:
        logger.error(f"데이터 다운로드 실패: {str(e)}")
        print(f"\n❌ 다운로드 실패: {str(e)}\n")
        print("="*60 + "\n")

if __name__ == "__main__":
    download_data()