"""
WordNet 동의어 생성 테스트
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.rag.elasticsearch_rag import ElasticSearchRAG

def test_wordnet_synonyms():
    """WordNet 동의어 생성 테스트"""
    
    print("=" * 80)
    print("WordNet 기반 동의어 생성 테스트")
    print("=" * 80)
    
    # 동의어 생성
    synonyms = ElasticSearchRAG._generate_hotel_synonyms()
    
    print(f"\n✅ 총 {len(synonyms)}개의 동의어 그룹 생성됨\n")
    
    # 카테고리별로 분류하여 출력
    categories = {
        '분위기/환경': ['quiet', 'romantic', 'luxury', 'budget'],
        '청결': ['clean', 'dirty'],
        '서비스': ['friendly', 'rude', 'professional'],
        '위치': ['central', 'nearby', 'remote'],
        '시설': ['breakfast', 'wifi', 'pool', 'gym', 'spa', 'parking', 'restaurant', 'bar'],
        '객실': ['room', 'spacious', 'tiny', 'comfortable', 'view', 'balcony'],
        '가격': ['expensive', 'reasonable'],
        '음식': ['delicious'],
        '상태': ['modern', 'old', 'new'],
        '소음': ['noisy'],
        '여행 타입': ['family', 'business', 'pet'],
        '품질': ['excellent', 'poor', 'good', 'average', 'beautiful', 'amazing', 'perfect', 'wonderful', 'helpful', 'convenient']
    }
    
    for category, keywords in categories.items():
        print(f"\n📌 {category}")
        print("-" * 80)
        
        found = []
        for synonym_group in synonyms:
            for keyword in keywords:
                if synonym_group.lower().startswith(keyword.lower() + ',') or \
                   ',' + keyword.lower() + ',' in ',' + synonym_group.lower() + ',':
                    found.append(synonym_group)
                    break
        
        for item in found:
            words = item.split(',')
            print(f"  • {words[0]} → {', '.join(words[1:])}")
    
    # WordNet 동의어 확인
    print("\n" + "=" * 80)
    print("WordNet에서 추가된 동의어 (예시)")
    print("=" * 80)
    
    wordnet_examples = [s for s in synonyms if any(word in s for word in ['beautiful', 'comfortable', 'excellent', 'amazing', 'perfect'])]
    
    for example in wordnet_examples:
        words = example.split(',')
        if len(words) > 1:
            print(f"  ✨ {words[0]} → {', '.join(words[1:])}")
    
    print("\n" + "=" * 80)
    
    return synonyms


def test_individual_wordnet_lookup():
    """개별 단어에 대한 WordNet 조회 테스트"""
    
    print("\n" + "=" * 80)
    print("개별 단어 WordNet 조회 테스트")
    print("=" * 80)
    
    test_words = [
        ('beautiful', 'adj'),
        ('comfortable', 'adj'),
        ('excellent', 'adj'),
        ('clean', 'adj'),
        ('spacious', 'adj'),
        ('convenient', 'adj'),
        ('amazing', 'adj'),
        ('perfect', 'adj'),
        ('wonderful', 'adj'),
        ('helpful', 'adj'),
    ]
    
    for word, pos in test_words:
        synonyms = ElasticSearchRAG._get_wordnet_synonyms(word, pos)
        if synonyms:
            print(f"\n'{word}' ({pos}):")
            print(f"  → {', '.join(synonyms[:10])}")  # 최대 10개만 표시
        else:
            print(f"\n'{word}' ({pos}): (동의어 없음)")


if __name__ == "__main__":
    try:
        # 동의어 생성 테스트
        synonyms = test_wordnet_synonyms()
        
        # 개별 조회 테스트
        test_individual_wordnet_lookup()
        
        print("\n✅ 테스트 완료!")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
