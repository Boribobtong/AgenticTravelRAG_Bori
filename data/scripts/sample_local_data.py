import os
import random
from pathlib import Path
from tqdm import tqdm

# ==========================================
# ⚙️ 설정 (환경에 맞게 수정하세요)
# ==========================================
SOURCE_FILE = Path("data/raw/HotelRec.txt")  # 실제 파일 경로
OUTPUT_FILE = Path("data/raw/tripadvisor_reviews.jsonl")

# 전체 데이터 크기 대비 샘플링 비율 설정
# 50GB 중 1GB 샘플링 비율 1/50 = 0.02 (2%)
TOTAL_SIZE_GB_ESTIMATE = 50.0 
TARGET_SIZE_GB = 1.0
SAMPLING_RATIO = TARGET_SIZE_GB / TOTAL_SIZE_GB_ESTIMATE  # 0.02

def sample_large_dataset_randomly():
    if not SOURCE_FILE.exists():
        print(f"❌ 원본 파일을 찾을 수 없습니다: {SOURCE_FILE}")
        return

    print(f"🔄 랜덤 샘플링 시작: {SOURCE_FILE} -> {OUTPUT_FILE}")
    print(f"📊 예상 샘플링 비율: {SAMPLING_RATIO*100:.2f}% (목표: 약 {TARGET_SIZE_GB}GB)")

    # 출력 디렉토리 생성
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    current_size = 0
    line_count = 0
    processed_lines = 0
    
    # 파일 전체 크기 확인 (진행률 표시용)
    total_file_size = os.path.getsize(SOURCE_FILE)

    with open(SOURCE_FILE, 'r', encoding='utf-8') as f_in, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        
        # tqdm으로 전체 진행상황 표시
        with tqdm(total=total_file_size, unit='B', unit_scale=True, desc="Processing") as pbar:
            for line in f_in:
                line_size = len(line.encode('utf-8'))
                pbar.update(line_size)
                processed_lines += 1

                # 🎲 랜덤 확률로 선택 (0.0 ~ 1.0 사이 난수 생성)
                if random.random() < SAMPLING_RATIO:
                    f_out.write(line)
                    current_size += line_size
                    line_count += 1
                
    print(f"\n✅ 샘플링 완료!")
    print(f"   총 읽은 라인: {processed_lines:,}개")
    print(f"   저장된 라인: {line_count:,}개")
    print(f"   최종 파일 크기: {current_size / (1024*1024*1024):.2f} GB")

if __name__ == "__main__":
    sample_large_dataset_randomly()